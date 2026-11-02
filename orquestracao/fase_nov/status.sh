#!/bin/bash
# Estado compacto das filas da fase de novembro (para o orquestrador ler gastando pouco). So le, nao muda nada.
cd "$(dirname "$0")/../.." || exit 1
D=orquestracao/fase_nov
echo "== $(date '+%d/%m %H:%M') | GPU $(nvidia-smi --query-gpu=memory.used,utilization.gpu,temperature.gpu --format=csv,noheader 2>/dev/null)"
[ -f $D/STOP ] && echo "== STOP presente"
echo "== filas:"
for f in $D/codex/*.txt $D/agy/*.txt $D/cmd/*.txt; do
  [ -e "$f" ] || continue
  b=${f%.txt}; e=espera
  for alvo in $(grep "^#ESPERA:" "$f" | sed 's/^#ESPERA:[[:space:]]*//' | tr -d '\r'); do [ -e "$alvo" ] || e="dep:$(basename "$alvo")"; done
  [ -f $b.rodando ] && e=RODANDO; [ -f $b.done ] && e=ok; [ -f $b.falhou ] && e=FALHOU
  printf "   %-14s %s\n" "$e" "$(basename $(dirname $f))/$(basename $f .txt)"
done
echo "== ultimas linhas do log: $(tail -3 $D/fila.log 2>/dev/null | tr '\n' ' ')"
echo "== spark: $(tail -3 $D/spark.log 2>/dev/null | tr '\n' ' ')"
