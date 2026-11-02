#!/bin/bash
# Rodada extra da noite de 13/09/2026 (GPU livre depois do roteiro principal e da correcao):
#   - variancia entre sementes: as duas formulacoes do LayoutLM no maior treino (3.189 paginas),
#     sementes 1 e 2 (a 42 e a do roteiro principal). No Golden os metodos ficaram a menos de 0,01
#     de tau um do outro; sem a variancia entre sementes nao da para dizer se a diferenca existe;
#   - ablacao sem layout 2D do LayoutLM pontual (a v1 tinha; a v3 ainda nao);
#   - avaliacao de tudo isso, e das tres ablacoes do sucessor, contra a anotacao humana (golden_v3);
#   - o Antigravity acrescenta ao relatorio da manha uma secao com esses numeros.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/noite_v3
STATUS="$LOGS/status.jsonl"
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(5 * 3600)" &
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
  return $cod
}

N=3189
EXTRA="--n-treino $N --blocos-extra data/processed/blocos_extra --epocas 4 --max-minutos 45 --micro-batch 4"

passo layoutlm_sem_layout_treinar $PY src/models/layoutlm_ordem.py treinar --nome layoutlm_sem_layout --sem-layout $EXTRA \
  && passo layoutlm_sem_layout_avaliar $PY src/models/layoutlm_ordem.py avaliar --nome layoutlm_sem_layout --sem-layout

for s in 1 2; do
  passo sucessor_seed${s}_treinar $PY src/models/layoutlm_sucessor.py treinar --nome sucessor_seed$s --seed $s $EXTRA \
    && passo sucessor_seed${s}_avaliar $PY src/models/layoutlm_sucessor.py avaliar --nome sucessor_seed$s
  passo pontual_seed${s}_treinar $PY src/models/layoutlm_ordem.py treinar --nome pontual_seed$s --seed $s $EXTRA \
    && passo pontual_seed${s}_avaliar $PY src/models/layoutlm_ordem.py avaliar --nome pontual_seed$s
done

passo golden_v3_extra $PY src/eval/avaliar_golden.py --lote _avaliacao/golden_v3 \
  --layoutlm layoutlm pontual_seed1 pontual_seed2 layoutlm_sem_layout \
  --sucessor layoutlm_sucessor sucessor_seed1 sucessor_seed2 ablacao_suc_sem_vies_geo ablacao_suc_sem_posicao ablacao_suc_sem_layout
passo comparar_extra $PY src/eval/comparar.py

passo relatorio_extra_antigravity $PY orquestracao/despachar.py --agente antigravity --tarefa T13 \
  --prompt orquestracao/prompts/T13c_relatorio_rodada_extra.md --timeout-min 40 --escopo docs/RELATORIO_NOITE_V3.md
echo "=== $(date '+%Y-%m-%d %H:%M') FIM DA RODADA EXTRA" | tee -a "$LOGS/roteiro.log"
