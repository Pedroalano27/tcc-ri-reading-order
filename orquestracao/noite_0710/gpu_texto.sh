#!/usr/bin/env bash
# LayoutLM sucessor com texto. Retomavel; este arquivo nao foi executado.
# Parar a espera: criar orquestracao/noite_0710/STOP. Nao mata outro processo.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export CUDA_VISIBLE_DEVICES=0

PY=venv/Scripts/python.exe
D=orquestracao/noite_0710
ANTERIOR=orquestracao/noite_0610
N=sucessor_linhas_texto_s42
T=resultados/ordenadores_treinados_sem_caixas
RUN="$T/$N"
LOCK="$RUN/fila.lock"
mkdir -p "$RUN"
log() { printf '%s %s\n' "$(date '+%d/%m %H:%M:%S')" "$*" >> "$RUN/fila.log"; }
parar() { [ ! -f "$D/STOP" ]; }

# Trava apenas instancias DESTE roteiro. A fila antiga nao usa essa trava:
# aguardar tambem sua ultima semente impede a corrida entre as duas filas.
# mkdir e atomico; PID permite retomar depois de queda sem apagar trava viva.
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ ! -f "$LOCK/pid" ]; then
    log "trava sem PID: verificar $LOCK antes de retomar"; exit 1
  fi
  read -r dono < "$LOCK/pid"
  if ! [[ "$dono" =~ ^[0-9]+$ ]]; then
    log "PID de trava invalido: verificar $LOCK"; exit 1
  fi
  if kill -0 "$dono" 2>/dev/null; then
    log "outra instancia ativa (PID $dono)"; exit 1
  fi
  rm -- "$LOCK/pid"
  rmdir -- "$LOCK"
  mkdir "$LOCK"
fi
printf '%s\n' "$$" > "$LOCK/pid"
trap 'rm -f -- "$LOCK/pid"; rmdir -- "$LOCK" 2>/dev/null || true' EXIT

[ -f "$RUN/avaliacao.done" ] && { log "ja avaliado"; exit 0; }
log "aguardando s42 e encerramento da fila anterior (tambem tem s43)"
until [ -f "$ANTERIOR/sucessor_linhas_completo_s42.done" ] &&
      { [ -f "$ANTERIOR/sucessor_linhas_completo_s43.done" ] || [ -f "$ANTERIOR/fim" ]; }; do
  parar || { log "STOP durante espera"; exit 0; }
  sleep 20
done

if [ ! -f "$RUN/treino.done" ]; then
  log "aguardando memoria GPU abaixo de 1100 MiB em tres leituras"
  livres=0
  until [ "$livres" -ge 3 ]; do
    parar || { log "STOP durante espera GPU"; exit 0; }
    mem=$(nvidia-smi --id=0 --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' \r' || true)
    if [[ "$mem" =~ ^[0-9]+$ ]] && [ "$mem" -lt 1100 ]; then
      livres=$((livres+1))
    else
      livres=0
    fi
    [ "$livres" -ge 3 ] || sleep 20
  done
  parar || { log "STOP antes do treino"; exit 0; }
  log "treino textual: inicio"
  "$PY" -B orquestracao/analises/treinar_sem_caixas_texto.py treinar \
    --modelo sucessor --representacao linhas --device cuda \
    --nome "$N" --dir-saida "$RUN" --epocas 20 --max-minutos 170 \
    --seed 42 --micro-batch 1 --batch 8 --lr 0.00004 --lr-cabeca 0.001 \
    --peso-posicao 0.5 --limiar-cadeia 0.5 >> "$RUN/treino.log" 2>&1
  touch "$RUN/treino.done"
  log "treino textual: fim"
fi
parar || { log "STOP antes da inferencia"; exit 0; }
log "inferencia CPU e avaliacao: inicio"
"$PY" -B orquestracao/analises/ordenar_bancadas_texto.py \
  --checkpoint "$RUN/melhor.pt" --dir-saida "$RUN/pred_texto" --avaliar \
  >> "$RUN/inferencia.log" 2>&1
touch "$RUN/avaliacao.done"
log "inferencia e avaliacao: fim"
