#!/bin/bash
# Roteiro do fim de semana na RTX 4090 (uso liberado pela faculdade).
# Etapa principal: treinar um detector de layout nas 9 classes do Diamond e compara-lo,
# no MESMO criterio da segmentacao atual, contra o extrator de hoje.
#
# Antes de rodar:
#   - anote o que puder no Diamond (mais ouro = melhor);
#   - se tiver um lote desenhado do zero (sem a pre-marcacao), passe-o em TESTE abaixo:
#     ele nao entra no treino e vira a medicao honesta.
#   - confirme a GPU:  venv/Scripts/python.exe -c "import torch;print(torch.cuda.get_device_name(0))"
#
# Uso:  bash orquestracao/fim_de_semana_4090.sh
set -u
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/fim_de_semana_4090
mkdir -p "$LOGS"

OURO="diamond_piloto diamond_treino"     # lotes com anotacao humana
PRATA="rose_treino"                       # pseudo-rotulo do VLM (paginas que ja sao ouro sao descartadas)
TESTE=""                                  # ex.: diamond_teste_zero  (lote desenhado do zero)
MODELO_BASE="yolov8s.pt"                  # leve; troque pelos pesos do DocLayout-YOLO se quiser
EPOCAS=100; IMGSZ=1024; BATCH=16; DISPOSITIVO=0

passo() {
  local nome=$1; shift
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  echo "    -> codigo $? ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOGS/roteiro.log"
}

# 0. dependencia (idempotente)
$PY -c "import ultralytics" 2>/dev/null || passo instalar_ultralytics venv/Scripts/pip install ultralytics

# 1. exporta o dataset YOLO a partir do Diamond
passo exportar $PY src/data/exportar_deteccao.py --ouro $OURO --prata $PRATA ${TESTE:+--teste $TESTE}

# 2. treina o detector
passo treinar $PY src/models/detector_layout.py treinar \
  --dados data/deteccao/diamond_yolo/data.yaml --modelo "$MODELO_BASE" \
  --epocas $EPOCAS --imgsz $IMGSZ --batch $BATCH --dispositivo $DISPOSITIVO --nome diamond

PESOS="runs/detect/diamond/weights/best.pt"

# 3. preve nos lotes de ouro e mede contra o gabarito humano, junto dos sistemas atuais
for LOTE in $OURO $TESTE; do
  passo prever_$LOTE $PY src/models/detector_layout.py prever \
    --pesos "$PESOS" --lote "$LOTE" --saida "resultados/deteccao/pred_yolo_$LOTE.jsonl" \
    --imgsz $IMGSZ --dispositivo $DISPOSITIVO
  passo avaliar_$LOTE $PY src/eval/avaliar_diamond.py --lote "$LOTE" \
    --rose rose_treino --pred "resultados/deteccao/pred_yolo_$LOTE.jsonl"
done

echo "=== $(date '+%Y-%m-%d %H:%M') FIM. Tabela em resultados/diamond/<lote>/avaliacao.md" | tee -a "$LOGS/roteiro.log"
