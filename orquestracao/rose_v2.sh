#!/bin/bash
# Rose v2 (13/09/2026): VLM (gemini-3.1-flash-lite, plano gratuito: 15 req/min, 500 req/dia) classifica,
# une e quebra as regioes da proposta v2 (src/data/regioes.py). Primeiro o piloto (20 paginas com
# anotacao humana, para medir), depois as 199 paginas do diamond_treino. Paginas que falham vao para
# erros.jsonl; cota diaria esgotada para o lote de forma limpa (retomar com --retomar).
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/rose_v2
mkdir -p "$LOGS"
ENTRADA_PILOTO="$1"
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
  return $cod
}

passo piloto $PY src/data/gerar_rose.py --colecao "$ENTRADA_PILOTO" --saida data/diamond/rose_piloto_v2 \
  --modo regioes --rpm 14 --pular-erros --retomar
passo avaliar_piloto $PY src/eval/avaliar_diamond.py --lote diamond_piloto --rose rose_piloto --rose rose_piloto_v2
passo treino $PY src/data/gerar_rose.py --colecao data/diamond/diamond_treino/tarefas.jsonl \
  --saida data/diamond/rose_treino --modo regioes --rpm 14 --pular-erros --retomar
echo "=== $(date '+%Y-%m-%d %H:%M') FIM" | tee -a "$LOGS/roteiro.log"
