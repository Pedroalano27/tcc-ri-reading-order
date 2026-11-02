#!/bin/bash
# Noite de 14->15/09: enquanto o Pedro dorme.
#   1. treina o PRIMEIRO detector de layout (extrator da imagem) no ouro+prata do Diamond
#      -- baseline local na RTX 4050, para de-riscar o fim de semana na 4090 (um job de GPU por vez);
#   2. preve e mede o detector contra o gabarito humano (regenera a segmentacao com as 64 paginas novas);
#   3. Gemini SO TEXTO no golden_v4 (API, sem GPU): isola imagem x modelo -- a pergunta aberta do relatorio.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/noite_detector
mkdir -p "$LOGS"

# nao deixa o Windows dormir por ~8h
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(8*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo() {
  local nome=$1; shift
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  echo "    -> codigo $? ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOGS/roteiro.log"
}

# 1. dataset atualizado (pega as 64 concluidas) + treino do detector (GPU)
passo exportar $PY src/data/exportar_deteccao.py --ouro diamond_piloto diamond_treino --prata rose_treino
passo treinar_detector $PY src/models/detector_layout.py treinar \
  --modelo yolov8s.pt --epocas 200 --imgsz 1024 --batch 4 --paciencia 40 --nome diamond

PESOS=$(ls -t runs/detect/diamond*/weights/best.pt 2>/dev/null | head -1)
echo "    pesos: ${PESOS:-NAO ENCONTRADO}" | tee -a "$LOGS/roteiro.log"

# 2. preve e mede contra o ouro (regenera a avaliacao da segmentacao com as paginas novas)
if [ -n "$PESOS" ]; then
  for LOTE in diamond_piloto diamond_treino; do
    passo prever_$LOTE $PY src/models/detector_layout.py prever \
      --pesos "$PESOS" --lote "$LOTE" --saida "resultados/deteccao/pred_yolo_$LOTE.jsonl"
    passo avaliar_$LOTE $PY src/eval/avaliar_diamond.py --lote "$LOTE" \
      --rose rose_treino --pred "resultados/deteccao/pred_yolo_$LOTE.jsonl"
  done
fi

# 3. Gemini so-texto no golden_v4 (API; roda depois do detector para nao competir)
passo gemini_so_texto $PY src/eval/vlm_ordem.py --particao golden:golden_v4 --sem-imagem --retomar \
  --saida resultados/golden/golden_v4/pred_vlm_gemini_3_1_flash_lite_sem_imagem.jsonl
passo avaliar_golden_v4 $PY src/eval/avaliar_golden.py --lote golden_v4

echo "=== $(date '+%Y-%m-%d %H:%M') FIM DA NOITE" | tee -a "$LOGS/roteiro.log"
