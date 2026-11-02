#!/bin/bash
# Madrugada de 14/09/2026: a cota gratuita do Gemini acabou depois de 12 das 45 paginas da ablacao do VLM
# sem as classes humanas no prompt. Espera a cota renovar (meia-noite do Pacifico ~ 04:00 em Brasilia),
# completa com --retomar, reavalia o golden_v4 e despacha o Antigravity para a revisao do relatorio (T37b).
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/avaliar_v4
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(9 * 3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo() {
  local nome=$1; shift
  local ini=$(date '+%Y-%m-%d %H:%M:%S')
  echo "=== $ini $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  echo "    -> codigo $? ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOGS/roteiro.log"
}

until [ "$(date '+%Y%m%d%H%M')" -ge "202609140420" ]; do sleep 120; done

for tentativa in 1 2 3; do
  passo vlm_sem_classes_$tentativa $PY src/eval/vlm_ordem.py --particao golden:golden_v4 --sem-classes --retomar \
    --saida resultados/golden/golden_v4/pred_vlm_gemini_3_1_flash_lite_sem_classes.jsonl
  n=$(grep -c . resultados/golden/golden_v4/pred_vlm_gemini_3_1_flash_lite_sem_classes.jsonl 2>/dev/null)
  [ "${n:-0}" -ge 45 ] && break
  sleep 3600
done
passo golden_v4_sem_classes $PY src/eval/avaliar_golden.py --lote golden_v4
passo relatorio_revisao_antigravity $PY orquestracao/despachar.py --agente antigravity --tarefa T37 \
  --prompt orquestracao/prompts/T37b_relatorio_v4_revisao.md --timeout-min 60 \
  --escopo src/eval/relatorio_v4.py notebooks/relatorio_ordem_v4.ipynb docs/RELATORIO_V4.md docs/figuras
echo "=== $(date '+%Y-%m-%d %H:%M') FIM DA MADRUGADA" | tee -a "$LOGS/roteiro.log"
