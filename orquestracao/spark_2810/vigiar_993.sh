#!/bin/bash
# Espera o job 993 (pontuar_lm) terminar no cluster, traz os escores e roda a decodificacao local.
cd "$(dirname "$0")/../.." || exit 1
J=${1:-993}; L=orquestracao/spark_2810/vigia.log
log(){ echo "$(date '+%d/%m %H:%M:%S') $*" >> $L; }
log "vigia do job $J: inicio"
while :; do
  st=$(timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=15 dgx-spark "sacct -j $J -X -n -o State%20" 2>/dev/null | tr -d ' \r')
  case "$st" in
    PENDING|RUNNING|"") sleep 600 ;;
    *) log "job $J: $st"; break ;;
  esac
done
timeout 120 ssh -o BatchMode=yes dgx-spark "tail -40 ~/tcc/logs/pontuar_lm-$J.out" > orquestracao/spark_2810/job_$J.tail.txt 2>&1
mkdir -p resultados/ordem_lm/escores
timeout 900 ssh -o BatchMode=yes dgx-spark "tar -cf - -C ~/tcc/ordem_lm/escores ." | tar -xf - -C resultados/ordem_lm/escores
log "escores trazidos: $(ls resultados/ordem_lm/escores | tr '\n' ' ')"
if [ -d resultados/ordem_lm/escores/Qwen_Qwen3-8B ]; then
  venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B \
    > orquestracao/spark_2810/decodificar_8b.log 2>&1
  log "decodificar rc=$?"
fi
log "vigia: fim"
