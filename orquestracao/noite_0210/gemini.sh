#!/bin/bash
# Gemini (API, sem GPU) da noite. So paginas do acervo do orientador: NADA de data/labelstudio aqui.
#   1) ordem de leitura por VLM nas 89 paginas de TESTE (veiculos CE, MA, RJ, fora do guia e de qualquer treino)
#      -> resultados/pred_vlm_gemini_3_1_flash_lite.jsonl   (item de acao da reuniao: reavaliar o Gemini)
#   2) terminar a massa de anotacao de prata (data/diamond/massa1_gemini, 273 de 383)
# A cota diaria do Gemini renova as 04:00 de Brasilia: se acabar antes, espera e continua. Retomavel.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
D=orquestracao/noite_0210
L=orquestracao/logs/noite_gemini; mkdir -p "$L"
log(){ echo "$(date '+%d/%m %H:%M:%S') [gemini] $*" >> "$D/fila.log"; }
PRED=resultados/pred_vlm_gemini_3_1_flash_lite.jsonl
FIM=$(( $(date +%s) + 9*3600 ))

for volta in 1 2 3 4; do
  [ -f "$D/STOP" ] && exit 0
  if [ ! -f "$PRED" ]; then
    log "ordem VLM na particao de teste (volta $volta)"
    $PY src/eval/vlm_ordem.py --particao teste --retomar > "$L/vlm_teste_v$volta.log" 2>&1
    log "vlm_ordem rc=$? | parcial: $( [ -f "$PRED.parcial" ] && grep -c . "$PRED.parcial" || echo 0 ) | final: $( [ -f "$PRED" ] && grep -c . "$PRED" || echo nao )"
  fi
  if [ -f "$PRED" ]; then
    FEITAS=$(grep -c . data/diamond/massa1_gemini/anotacoes.jsonl 2>/dev/null || echo 0)
    if [ "$FEITAS" -lt 383 ]; then
      log "massa de anotacao: $FEITAS/383; retomando"
      bash orquestracao/madrugada_rose_massa.sh > "$L/massa_v$volta.log" 2>&1
      log "massa: $(grep -c . data/diamond/massa1_gemini/anotacoes.jsonl)/383"
    fi
  fi
  [ -f "$PRED" ] && [ "$(grep -c . data/diamond/massa1_gemini/anotacoes.jsonl)" -ge 383 ] && { log "tudo pronto"; exit 0; }
  [ $(date +%s) -gt $FIM ] && break
  log "pendente (cota ou congestao); nova volta em 40 min"
  sleep 2400
done
log "gemini encerrado"
