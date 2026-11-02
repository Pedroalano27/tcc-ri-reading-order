#!/bin/bash
# Noite de 06->07/10: exporta o treino completo (CPU) e treina o LayoutLM sucessor em linhas com todo o
# dado, duas sementes, quando a GPU estiver livre. Retomavel. Parar: criar orquestracao/noite_0610/STOP.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
D=orquestracao/noite_0610; PY=venv/Scripts/python.exe; T=resultados/ordenadores_treinados_sem_caixas
log(){ echo "$(date '+%d/%m %H:%M:%S') $*" >> $D/log.txt; }
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(11*3600)" &
AC=$!; trap 'kill $AC 2>/dev/null' EXIT
if [ ! -f $D/export_ok ]; then
  log "exportacao completa: inicio"
  for i in 1 2 3 4 5 6; do
    [ -f $D/STOP ] && exit 0
    $PY -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 0 >> $D/export.log 2>&1; rc=$?
    [ $rc -eq 0 ] && break; log "exportacao caiu (rc=$rc), tentativa $i"; sleep 30
  done
  [ $rc -eq 0 ] || { log "exportacao FALHOU"; exit 1; }
  $PY -B $D/congelar.py >> $D/log.txt 2>&1 && touch $D/export_ok
  log "exportacao completa: fim"
fi
for S in 42 43; do
  N=sucessor_linhas_completo_s$S
  [ -f $D/$N.done ] && continue
  [ -f $D/STOP ] && exit 0
  livres=0
  until [ $livres -ge 3 ]; do
    [ -f $D/STOP ] && exit 0
    mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' \r')
    if [ "${mem:-9999}" -lt 1100 ]; then livres=$((livres+1)); else livres=0; fi; sleep 20
  done
  log "treino $N: inicio"
  $PY -B orquestracao/analises/treinar_sem_caixas.py treinar --modelo sucessor --representacao linhas --device cuda \
     --max-minutos 170 --epocas 20 --batch 8 --micro-batch 1 --seed $S --nome $N --dir-saida $T/$N >> $D/$N.log 2>&1 \
  && $PY -B orquestracao/analises/ordenar_bancadas.py --checkpoint $T/$N/melhor.pt --avaliar >> $D/$N.log 2>&1 \
  && touch $D/$N.done
  log "treino $N: fim (rc=$?)"
done
$PY -B orquestracao/analises/tabela_noite_0410.py > resultados/tabela_noite_0410.md
log "fim"; touch $D/fim
