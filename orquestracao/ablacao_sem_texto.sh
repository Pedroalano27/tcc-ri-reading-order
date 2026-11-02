#!/bin/bash
# Ablacao do LayoutLM sucessor SEM TEXTO (13/09/2026): todo token de palavra vira [UNK], com as
# mesmas caixas, o mesmo numero de tokens por bloco e o vies geometrico. Mesmo treino da semente 42
# do roteiro principal (3.189 paginas, 4 epocas, 45 min). Se o tau quase nao cair, o texto ajuda
# pouco e um pre-treino em portugues tem pouco a ganhar; se cair muito, vale investir nele.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/ablacao_sem_texto
mkdir -p "$LOGS"
STATUS="$LOGS/status.jsonl"
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(3 * 3600)" &
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
passo treinar $PY src/models/layoutlm_sucessor.py treinar --nome ablacao_suc_sem_texto --sem-texto $EXTRA \
  && passo avaliar $PY src/models/layoutlm_sucessor.py avaliar --nome ablacao_suc_sem_texto --sem-texto \
  && passo golden $PY src/eval/avaliar_golden.py --lote _avaliacao/golden_v3 \
       --layoutlm layoutlm pontual_seed1 pontual_seed2 layoutlm_sem_layout \
       --sucessor layoutlm_sucessor sucessor_seed1 sucessor_seed2 ablacao_suc_sem_vies_geo ablacao_suc_sem_posicao \
                  ablacao_suc_sem_layout ablacao_suc_sem_texto \
  && passo comparar $PY src/eval/comparar.py
echo "=== $(date '+%Y-%m-%d %H:%M') FIM" | tee -a "$LOGS/roteiro.log"
