#!/bin/bash
# Envia um job a DGX Spark, espera terminar e traz uma pasta de resultados. Usado pela fila cmd.
# Uso:
#   bash orquestracao/fase_nov/spark.sh enviar  <nome> -- <args do sbatch, a partir de ~/tcc/repo>
#   bash orquestracao/fase_nov/spark.sh esperar <nome>            (bloqueia ate o job terminar; rc 0 se COMPLETED)
#   bash orquestracao/fase_nov/spark.sh trazer  <dir remoto> <dir local>
#   bash orquestracao/fase_nov/spark.sh sincronizar                (envia cluster/ src/ orquestracao/analises/ ao cluster)
# O id do job fica em orquestracao/fase_nov/spark/<nome>.jobid; reenviar o mesmo nome reaproveita o job se
# ele ainda estiver na fila ou rodando (nao duplica). Exige a VPN; sem ela, espera e tenta de novo.
cd "$(dirname "$0")/../.." || exit 1
S=orquestracao/fase_nov/spark; mkdir -p $S
L=orquestracao/fase_nov/spark.log
log(){ echo "$(date '+%d/%m %H:%M:%S') $*" >> $L; }
r(){ timeout ${T:-90} ssh -o BatchMode=yes -o ConnectTimeout=15 dgx-spark "$@"; }
estado(){ r "sacct -j $1 -X -n -o State%20" 2>/dev/null | head -1 | tr -d ' \r'; }

case "$1" in
  sincronizar)
    tar --exclude=__pycache__ -cf - cluster src orquestracao/analises | T=600 r "mkdir -p ~/tcc/repo && tar -xf - -C ~/tcc/repo" \
      && log "sincronizado" ;;
  enviar)
    nome=$2; shift 3
    if [ -f $S/$nome.jobid ]; then
      st=$(estado "$(cat $S/$nome.jobid)")
      case "$st" in PENDING|RUNNING|REQUEUED) log "$nome ja esta na fila ($st)"; exit 0;; esac
    fi
    until saida=$(r "mkdir -p ~/tcc/logs && cd ~/tcc/repo && sbatch --parsable $*" 2>&1); do
      log "$nome: envio falhou (${saida:0:120}); tento em 5 min"; sleep 300; done
    id=$(echo "$saida" | tail -1 | tr -d ' \r'); echo "$id" > $S/$nome.jobid; log "$nome enviado: job $id ($*)" ;;
  esperar)
    nome=$2; id=$(cat $S/$nome.jobid) || exit 2
    while :; do
      st=$(estado "$id")
      case "$st" in
        PENDING|RUNNING|REQUEUED|"") sleep 300 ;;
        COMPLETED) log "$nome (job $id): COMPLETED"; r "tail -30 ~/tcc/logs/*-$id.out" > $S/$nome.tail.txt 2>&1; exit 0 ;;
        *) log "$nome (job $id): $st"; r "tail -60 ~/tcc/logs/*-$id.out" > $S/$nome.tail.txt 2>&1; exit 1 ;;
      esac
    done ;;
  trazer)
    mkdir -p "$3" && T=1800 r "tar -cf - -C $2 ." | tar -xf - -C "$3" && log "trazido $2 -> $3" ;;
  *) sed -n 2,9p "$0"; exit 2 ;;
esac
