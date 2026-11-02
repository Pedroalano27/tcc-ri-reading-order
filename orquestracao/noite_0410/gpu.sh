#!/bin/bash
# GPU local da noite de 04/10: roda, um de cada vez, os roteiros orquestracao/noite_0410/gpu/NN_*.sh que
# ainda nao tem .done/.falhou. Antes de CADA roteiro espera a placa ficar livre (o Pedro pode estar usando
# em outro trabalho; nunca mexer no processo dele). Retomavel; para parar: criar noite_0410/STOP.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
D=orquestracao/noite_0410
log(){ echo "$(date '+%d/%m %H:%M:%S') [gpu] $*" >> "$D/fila.log"; }
esperar_livre(){ local livres=0 avisou=0 mem util
  until [ $livres -ge 3 ]; do
    [ -f "$D/STOP" ] && exit 0
    read -r mem util < <(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr -d ',')
    # so a memoria decide (medido em 03/10: o desktop sozinho usa 0,3-0,8 GB e 25-50% de uso)
    if [ "${mem:-9999}" -lt 1100 ]; then livres=$((livres+1))
    else livres=0; [ $avisou -eq 0 ] && { log "GPU em uso (${mem} MiB, ${util}%); espero liberar"; avisou=1; }; fi
    sleep 20
  done; }
vazio=0
while [ $vazio -lt 540 ]; do            # desiste depois de 9 h sem roteiro novo
  [ -f "$D/STOP" ] && exit 0
  prox=""
  for f in $D/gpu/[0-9]*.sh; do
    [ -e "$f" ] || continue
    [ -f "${f%.sh}.done" ] || [ -f "${f%.sh}.falhou" ] || { prox=$f; break; }
  done
  if [ -z "$prox" ]; then vazio=$((vazio+1)); sleep 60; continue; fi
  vazio=0; esperar_livre
  log "GPU livre; comecando $(basename "$prox")"; touch "${prox%.sh}.rodando"; t0=$(date +%s)
  bash "$prox" > "${prox%.sh}.log" 2>&1; rc=$?
  rm -f "${prox%.sh}.rodando"
  if [ $rc -eq 0 ]; then touch "${prox%.sh}.done"; else echo "rc=$rc" > "${prox%.sh}.falhou"; fi
  log "$(basename "$prox") terminou (rc=$rc, $(( ($(date +%s)-t0)/60 )) min)"
done
log "fila da GPU encerrada"
