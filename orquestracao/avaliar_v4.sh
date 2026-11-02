#!/bin/bash
# Rodada local sobre o golden_v4 (13/09/2026): espera o VLM terminar o golden_v4, avalia todos os metodos
# locais nos dois conjuntos (golden_v4 e _avaliacao/golden_v3), roda a ablacao do VLM sem marcas e
# despacha o Antigravity para o relatorio (T37). GPU: LayoutLM na avaliacao.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/avaliar_v4
mkdir -p "$LOGS"
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(4 * 3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo() {
  local nome=$1; shift
  local ini=$(date '+%Y-%m-%d %H:%M:%S')
  echo "=== $ini $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  local cod=$?
  echo "    -> codigo $cod ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOGS/roteiro.log"
}

until grep -q "^\[OK\] .* paginas\|Cota diaria\|\[ERRO\]" orquestracao/logs/vlm_ordem_golden_v4.log 2>/dev/null; do sleep 30; done

LAYOUTLM="--layoutlm layoutlm pontual_seed1 pontual_seed2 layoutlm_sem_layout"
SUCESSOR="--sucessor layoutlm_sucessor sucessor_seed1 sucessor_seed2 ablacao_suc_sem_vies_geo ablacao_suc_sem_posicao ablacao_suc_sem_layout ablacao_suc_sem_texto"
passo golden_v4 $PY src/eval/avaliar_golden.py --lote golden_v4 $LAYOUTLM $SUCESSOR
passo golden_v3 $PY src/eval/avaliar_golden.py --lote _avaliacao/golden_v3 $LAYOUTLM $SUCESSOR
passo vlm_sem_marcas $PY src/eval/vlm_ordem.py --particao golden:golden_v4 --sem-marcas
passo golden_v4_final $PY src/eval/avaliar_golden.py --lote golden_v4 $LAYOUTLM $SUCESSOR
passo relatorio_antigravity $PY orquestracao/despachar.py --agente antigravity --tarefa T37 \
  --prompt orquestracao/prompts/T37_relatorio_v4.md --timeout-min 75 \
  --escopo src/eval/relatorio_v4.py notebooks/relatorio_ordem_v4.ipynb docs/RELATORIO_V4.md
echo "=== $(date '+%Y-%m-%d %H:%M') FIM" | tee -a "$LOGS/roteiro.log"
