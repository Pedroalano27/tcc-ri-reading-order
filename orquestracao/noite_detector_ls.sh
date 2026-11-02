#!/bin/bash
# Noite 01->02/10: detector de layout treinado no dataset do Label Studio (2.118 paginas, split por fonte).
#   ls3  = plano "grosso" do professor: texto / tabela / imagem
#   ls16 = as 16 classes do guia de anotacao
# Para cada um: treina (YOLOv8s, 1024 px), mede mAP no TESTE do Label Studio (fontes nao vistas) e
# preve no diamond_teste (11 paginas anotadas do zero) para comparar com o extrator de regras.
# Um job de GPU por vez. Retomavel: pula o treino se o best.pt ja existe.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/noite_detector_ls
mkdir -p "$LOGS" resultados/deteccao
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(10*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

passo(){ local n=$1; shift; echo "=== $(date '+%H:%M:%S') $n" | tee -a "$LOGS/roteiro.log"; "$@" > "$LOGS/$n.log" 2>&1; echo "    -> $? ($(date '+%H:%M:%S'))" | tee -a "$LOGS/roteiro.log"; }

for DS in ls3 ls16; do
  PESOS=runs/detect/$DS/weights/best.pt
  FEITO=runs/detect/$DS/treino_ok        # best.pt existe desde a 1a epoca; o que marca o fim e este arquivo
  if [ ! -f "$FEITO" ]; then
    # --retomar: se o treino foi interrompido, continua da ultima epoca salva (weights/last.pt)
    passo treinar_$DS $PY src/models/detector_layout.py treinar --dados data/deteccao/$DS/data.yaml \
      --modelo yolov8s.pt --epocas 60 --imgsz 1024 --batch 4 --paciencia 15 --fliplr 0 --workers 1 --nome $DS --retomar \
      && touch "$FEITO"
  fi
  [ -f "$FEITO" ] || { echo "    treino de $DS incompleto; paro aqui" | tee -a "$LOGS/roteiro.log"; exit 1; }

  # mAP no teste do Label Studio (fontes que o modelo nao viu)
  passo map_teste_$DS $PY -c "
import json
from ultralytics import YOLO
m = YOLO('$PESOS')
r = m.val(data='data/deteccao/$DS/data.yaml', split='test', imgsz=1024, batch=4, device=0, verbose=False,
          project='runs/detect', name='${DS}_teste', exist_ok=True)
saida = {'mAP50': float(r.box.map50), 'mAP50_95': float(r.box.map), 'precisao': float(r.box.mp), 'revocacao': float(r.box.mr),
         'por_classe': {m.names[int(c)]: {'AP50': float(r.box.ap50[i]), 'AP50_95': float(r.box.ap[i])}
                        for i, c in enumerate(r.box.ap_class_index)}}
json.dump(saida, open('resultados/deteccao/${DS}_map_teste.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(saida, ensure_ascii=False, indent=1))
"
  passo prever_$DS $PY src/models/detector_layout.py prever --pesos "$PESOS" --lote diamond_teste \
    --saida resultados/deteccao/pred_${DS}_diamond_teste.jsonl
done

ARGS=""
for DS in ls3 ls16; do
  [ -f resultados/deteccao/pred_${DS}_diamond_teste.jsonl ] && ARGS="$ARGS --pred $DS=resultados/deteccao/pred_${DS}_diamond_teste.jsonl"
done
passo comparar $PY orquestracao/analises/avaliar_detector_ls.py $ARGS
cp "$LOGS/comparar.log" resultados/deteccao/comparacao_detector_ls.txt 2>/dev/null
echo "=== $(date '+%F %H:%M') FIM. Ver resultados/deteccao/comparacao_detector_ls.txt e *_map_teste.json" | tee -a "$LOGS/roteiro.log"
