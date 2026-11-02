#!/bin/bash
# GPU local da noite: espera a placa ficar livre (o Pedro pode estar usando) e so entao roda o roteiro
# dos detectores, que e retomavel (ls3 continua da ultima epoca salva; depois ls16, mAP e comparacao).
cd "$(dirname "$0")/../.." || exit 1
D=orquestracao/noite_0210
log(){ echo "$(date '+%d/%m %H:%M:%S') [gpu] $*" >> "$D/fila.log"; }
if [ -f runs/detect/ls16/treino_ok ] && [ -f resultados/deteccao/comparacao_detector_ls.txt ]; then
  log "detectores e comparacao ja prontos; nada a fazer"; exit 0; fi
livres=0; avisou=0
until [ $livres -ge 3 ]; do
  [ -f "$D/STOP" ] && exit 0
  read -r mem util < <(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr -d ',')
  # so a memoria decide: com a tela ligada o uso fica em 25-50% mesmo sem nada rodando (medido em 03/10),
  # e um jogo ou outro treino aparece como memoria acima de ~1,1 GB (o desktop sozinho usa 0,3-0,8 GB)
  if [ "${mem:-9999}" -lt 1100 ]; then livres=$((livres+1))
  else livres=0; [ $avisou -eq 0 ] && { log "GPU em uso (${mem} MiB, ${util}%); espero liberar"; avisou=1; }; fi
  sleep 20
done
log "GPU livre; iniciando orquestracao/noite_detector_ls.sh"
mkdir -p orquestracao/logs/noite_detector_ls
bash orquestracao/noite_detector_ls.sh >> orquestracao/logs/noite_detector_ls/saida_gpu.log 2>&1
log "noite_detector_ls.sh terminou (rc=$?)"
