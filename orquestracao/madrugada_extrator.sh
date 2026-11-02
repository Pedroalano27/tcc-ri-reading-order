#!/bin/bash
# Madrugada 15->16/09: melhorar/medir o extrator com o Diamond novo (96 ouro) e o teste SEM viés.
#   1. re-treina o detector YOLOv8s com as 96 páginas de ouro (GPU) -- dataset já exportado;
#   2. prevê com o detector novo no diamond_teste e nos lotes de ouro;
#   3. varre configurações do extrator + híbridos no diamond_teste (11 páginas, sem ancoragem);
#   4. avalia tudo junto e escreve um resumo.
# Um job de GPU por vez: o treino/inferência é sequencial; a varredura é CPU.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/madrugada_extrator
mkdir -p "$LOGS"
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(8*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo(){ local n=$1; shift; echo "=== $(date '+%H:%M:%S') $n" | tee -a "$LOGS/roteiro.log"; "$@" > "$LOGS/$n.log" 2>&1; echo "    -> $? ($(date '+%H:%M:%S'))" | tee -a "$LOGS/roteiro.log"; }

# 1. detector novo (96 ouro)
passo treinar_s $PY src/models/detector_layout.py treinar --modelo yolov8s.pt --epocas 200 --imgsz 1024 --batch 4 --paciencia 40 --nome diamond96
PESOS=$(ls -t runs/detect/diamond96*/weights/best.pt 2>/dev/null | head -1)
echo "    pesos: ${PESOS:-NAO}" | tee -a "$LOGS/roteiro.log"

# 2. prevê com o detector novo
if [ -n "$PESOS" ]; then
  for LOTE in diamond_teste diamond_piloto diamond_treino; do
    passo prever_$LOTE $PY src/models/detector_layout.py prever --pesos "$PESOS" --lote "$LOTE" --saida "resultados/deteccao/pred96_$LOTE.jsonl"
  done
fi

# 3. varredura de configurações + híbridos no teste sem viés
passo varredura $PY orquestracao/analises/varrer_extrator.py --lote diamond_teste --pred resultados/deteccao/pred96_diamond_teste.jsonl

# 4. avaliação completa (extrator, ablação de regras, detector novo, híbrido) no teste
passo avaliar_teste $PY src/eval/avaliar_diamond.py --lote diamond_teste --ablacao \
  --pred resultados/deteccao/pred96_diamond_teste.jsonl --pred-classe resultados/deteccao/pred96_diamond_teste.jsonl

echo "=== $(date '+%H:%M') FIM. Ranking em resultados/diamond/diamond_teste/varredura.md" | tee -a "$LOGS/roteiro.log"
