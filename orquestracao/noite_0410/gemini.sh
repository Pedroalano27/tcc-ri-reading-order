#!/bin/bash
# Gemini ordenando as faixas (unidades sem caixas finas) das 71 paginas do Golden; autorizado pelo Pedro
# em 04/10 23:18. So paginas de Diarios publicos. Retomavel (--retomar). Nao escreve na bancada.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
D=orquestracao/noite_0410; V=resultados/ordenadores_sem_caixas/vlm
log(){ echo "$(date '+%d/%m %H:%M:%S') [gemini] $*" >> "$D/fila.log"; }
for par in colunas_margens__golden_v4 colunas_margens__golden_v3_novo colunas__golden_v4 colunas__golden_v3_novo; do
  [ -f "$D/STOP" ] && exit 0
  [ -f "$V/bruto__$par.jsonl" ] && { log "$par ja pronto"; continue; }
  log "comecando $par"
  venv/Scripts/python.exe src/eval/vlm_ordem.py --particao $V/particao__$par.jsonl --sem-classes \
      --saida $V/bruto__$par.jsonl --retomar >> $D/saida_gemini.log 2>&1
  log "$par terminou (rc=$?)"
done
venv/Scripts/python.exe orquestracao/analises/vlm_unidades_cola.py --converter >> $D/saida_gemini.log 2>&1
log "conversao terminou (rc=$?)"
touch $D/gemini_fim
