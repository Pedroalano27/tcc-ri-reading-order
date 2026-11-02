#!/bin/bash
# Madrugada 16->17/09: gerar MASSA de anotacao com o Gemini (Rose), modo regioes (critico do extrator).
# O modelo olha a extracao (proposta v3) e corrige classe/uniao/quebra de cada regiao -> anotacao de prata.
# Salva num lote NOVO (nunca toca no ouro humano nem no teste). Retoma de onde parou.
# RESILIENCIA A 503: o modelo as vezes responde 503 "high demand" (congestao temporaria do Google).
# Por isso rodamos em VARIAS PASSADAS com --retomar: paginas que falharam numa passada sao tentadas
# na proxima (so as ja concluidas entram no anotacoes.jsonl e sao puladas). Para limpo na cota diaria.
#   LOTE de tarefas: data/diamond/diamond_massa1  (imagens + proposta v3)
#   SAIDA:           data/diamond/massa1_gemini    (anotacoes VLM:gemini-*)
set -u
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/madrugada_rose
mkdir -p "$LOGS"
TAREFAS=data/diamond/diamond_massa1/tarefas.jsonl
SAIDA=data/diamond/massa1_gemini
MAX_PASSADAS=16

# mantem a maquina acordada durante o job (API, sem GPU)
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(9*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

TOTAL=$(grep -c . "$TAREFAS")
echo "=== $(date '+%F %H:%M') inicio da massa Rose (regioes) | $TOTAL paginas alvo" | tee -a "$LOGS/roteiro.log"

for passada in $(seq 1 $MAX_PASSADAS); do
  echo "--- passada $passada/$MAX_PASSADAS ($(date '+%H:%M'))" | tee -a "$LOGS/roteiro.log"
  $PY src/data/gerar_rose.py \
    --colecao "$TAREFAS" --saida "$SAIDA" \
    --modo regioes --provedor gemini --rpm 14 \
    --retomar --pular-erros \
    > "$LOGS/gerar_p${passada}.log" 2>&1

  FEITAS=$( [ -f "$SAIDA/anotacoes.jsonl" ] && grep -c . "$SAIDA/anotacoes.jsonl" || echo 0 )
  echo "    feitas: $FEITAS/$TOTAL" | tee -a "$LOGS/roteiro.log"
  if [ "$FEITAS" -ge "$TOTAL" ]; then
    echo "    tudo anotado; encerrando." | tee -a "$LOGS/roteiro.log"; break
  fi
  if grep -q "Cota diaria esgotada" "$LOGS/gerar_p${passada}.log"; then
    echo "    cota diaria esgotada; paro ate amanha (rode de novo com --retomar)." | tee -a "$LOGS/roteiro.log"; break
  fi
  sleep 90    # deixa a congestao (503) passar antes da proxima passada
done

# resumo do que saiu
$PY - "$SAIDA" <<'PY' 2>&1 | tee -a "$LOGS/roteiro.log"
import json, collections, os, sys
saida = sys.argv[1]
p = os.path.join(saida, "anotacoes.jsonl")
if os.path.exists(p):
    A = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    cls = collections.Counter(r["classe"] for a in A for r in a["regioes"])
    print(f"anotacoes: {len(A)} | regioes: {sum(len(a['regioes']) for a in A)} | classes: {dict(cls)}")
e = os.path.join(saida, "erros.jsonl")
if os.path.exists(e):
    ids = {json.loads(l)['page_id'] for l in open(e, encoding='utf-8') if l.strip()}
    print("paginas ainda com erro (nao concluidas):", len(ids))
PY
echo "=== $(date '+%F %H:%M') FIM" | tee -a "$LOGS/roteiro.log"
