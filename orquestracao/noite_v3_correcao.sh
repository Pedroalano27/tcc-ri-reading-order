#!/bin/bash
# Correcao da noite de 13/09/2026: avaliar_golden.py e piloto_japeri.py chamavam prever() do sucessor
# sem dizer o modo, e o padrao da funcao era busca em feixe (o teste usa cadeias). O padrao foi
# corrigido em src/models/layoutlm_sucessor.py; aqui se refazem os dois passos afetados e, com o
# Antigravity, o diagnostico e o relatorio da manha. Espera o roteiro principal terminar (GPU livre).
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/noite_v3
STATUS="$LOGS/status.jsonl"
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(4 * 3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo() {
  local nome=$1; shift
  local ini=$(date '+%Y-%m-%d %H:%M:%S')
  echo "=== $ini $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  local cod=$?
  local fim=$(date '+%Y-%m-%d %H:%M:%S')
  echo "{\"passo\": \"$nome\", \"inicio\": \"$ini\", \"fim\": \"$fim\", \"codigo\": $cod}" >> "$STATUS"
  echo "    -> codigo $cod ($fim)" | tee -a "$LOGS/roteiro.log"
}

until grep -q "FIM DO ROTEIRO" "$LOGS/roteiro.log" 2>/dev/null; do sleep 60; done

passo golden_v3_cadeias $PY src/eval/avaliar_golden.py --lote _avaliacao/golden_v3
passo ri_japeri_piloto_cadeias $PY src/ri/piloto_japeri.py
passo comparar_pos_correcao $PY src/eval/comparar.py
passo diagnostico_antigravity $PY orquestracao/despachar.py --agente antigravity --tarefa T25 \
  --prompt orquestracao/prompts/T25b_diagnostico_sucessor_cadeias.md --timeout-min 40 \
  --escopo resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md orquestracao/analises/diagnostico_sucessor.py
passo relatorio_antigravity_corrigido $PY orquestracao/despachar.py --agente antigravity --tarefa T13 \
  --prompt orquestracao/prompts/T13b_relatorio_noite_v3_corrigido.md --timeout-min 45 --escopo docs/RELATORIO_NOITE_V3.md
echo "=== $(date '+%Y-%m-%d %H:%M') FIM DA CORRECAO" | tee -a "$LOGS/roteiro.log"
