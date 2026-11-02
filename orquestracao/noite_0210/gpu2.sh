#!/bin/bash
# GPU, segunda parte da noite (03/10): o dataset do Label Studio ajuda na CONVENCAO DE CAIXAS DO TCC?
# No teste do zero (diamond_teste) o extrator ganhou dos detectores ls3/ls16 (0,851 x 0,765 / 0,753 de F1@0,5);
# no teste do Label Studio foi o contrario. Cada um ganha no gabarito da sua convencao. Este roteiro faz o
# ajuste fino no ouro do Diamond (data/deteccao/diamond_yolo: 200 paginas de treino, 19 de validacao, 9 classes)
# partindo de tres pontos, com os MESMOS hiperparametros:
#   coco  yolov8s.pt generico (controle)
#   ls16  detector pre-treinado em 1.590 paginas de diarios, 16 classes do guia
#   ls3   idem, 3 classes
# e mede no diamond_teste (11 paginas anotadas do zero). Retomavel (treino_ok + --retomar).
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
D=orquestracao/noite_0210
LOGS=orquestracao/logs/noite_ajuste_fino; mkdir -p "$LOGS" resultados/deteccao
log(){ echo "$(date '+%d/%m %H:%M:%S') [gpu2] $*" >> "$D/fila.log"; }
SAIDA=resultados/deteccao/comparacao_ajuste_fino_diamond.txt
[ -f runs/detect/diamond_ft_ls3/treino_ok ] && [ -f "$SAIDA" ] && grep -q "ft_ls3" "$SAIDA" && { log "ajuste fino ja pronto"; exit 0; }
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(5*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT
livres=0
until [ $livres -ge 3 ]; do          # mesma regra do gpu.sh: so a memoria decide se a placa esta livre
  [ -f "$D/STOP" ] && exit 0
  read -r mem util < <(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr -d ',')
  if [ "${mem:-9999}" -lt 1100 ]; then livres=$((livres+1)); else livres=0; fi
  sleep 20
done
ARGS="--pred ls16=resultados/deteccao/pred_ls16_diamond_teste.jsonl --pred ls3=resultados/deteccao/pred_ls3_diamond_teste.jsonl"
for PAR in "coco=yolov8s.pt" "ls16=runs/detect/ls16/weights/best.pt" "ls3=runs/detect/ls3/weights/best.pt"; do
  [ -f "$D/STOP" ] && exit 0
  INI=${PAR%%=*}; PESO=${PAR#*=}; NOME=diamond_ft_$INI
  if [ ! -f runs/detect/$NOME/treino_ok ]; then
    log "ajuste fino no Diamond a partir de $INI"
    $PY src/models/detector_layout.py treinar --dados data/deteccao/diamond_yolo/data.yaml --modelo "$PESO" \
      --epocas 120 --imgsz 1024 --batch 4 --paciencia 30 --fliplr 0 --workers 1 --nome $NOME --retomar \
      > "$LOGS/treinar_$NOME.log" 2>&1 && touch runs/detect/$NOME/treino_ok
  fi
  [ -f runs/detect/$NOME/treino_ok ] || { log "treino de $NOME falhou; sigo para o proximo"; continue; }
  $PY src/models/detector_layout.py prever --pesos runs/detect/$NOME/weights/best.pt --lote diamond_teste \
    --saida resultados/deteccao/pred_${NOME}_diamond_teste.jsonl > "$LOGS/prever_$NOME.log" 2>&1
  ARGS="$ARGS --pred ft_$INI=resultados/deteccao/pred_${NOME}_diamond_teste.jsonl"
  $PY orquestracao/analises/avaliar_detector_ls.py $ARGS > "$SAIDA" 2> "$LOGS/avaliar.log"
  log "$NOME pronto: $(grep "ft_$INI" "$SAIDA" | head -1 | tr -s ' ')"
done
log "ajuste fino terminou"
