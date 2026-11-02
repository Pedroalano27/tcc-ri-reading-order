#!/bin/bash
# Re-treino limpo do detector apos corrigir a duplicacao de paginas re-anotadas (sem vazamento
# treino/validacao). Dataset ja re-exportado. Treina, preve e mede contra o ouro.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/retreino_detector
mkdir -p "$LOGS"
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(2*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo() {
  local nome=$1; shift
  echo "=== $(date '+%H:%M:%S') $nome" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  echo "    -> codigo $? ($(date '+%H:%M:%S'))" | tee -a "$LOGS/roteiro.log"
}

passo treinar $PY src/models/detector_layout.py treinar \
  --modelo yolov8s.pt --epocas 200 --imgsz 1024 --batch 4 --paciencia 40 --nome diamond
PESOS=$(ls -t runs/detect/diamond*/weights/best.pt 2>/dev/null | head -1)
echo "    pesos: ${PESOS:-NAO}" | tee -a "$LOGS/roteiro.log"
if [ -n "$PESOS" ]; then
  for LOTE in diamond_piloto diamond_treino; do
    passo prever_$LOTE $PY src/models/detector_layout.py prever \
      --pesos "$PESOS" --lote "$LOTE" --saida "resultados/deteccao/pred_yolo_$LOTE.jsonl"
    passo avaliar_$LOTE $PY src/eval/avaliar_diamond.py --lote "$LOTE" \
      --rose rose_treino --pred "resultados/deteccao/pred_yolo_$LOTE.jsonl"
  done
fi
echo "=== $(date '+%H:%M') FIM" | tee -a "$LOGS/roteiro.log"
