#!/bin/bash
# Exportacao do treino da noite (amostra fixa de 1.500 paginas), retomavel; tenta de novo se cair.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
D=orquestracao/noite_0410
for i in 1 2 3 4 5 6; do
  venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 1500 >> $D/saida_export.log 2>&1; rc=$?
  [ $rc -eq 0 ] && break
  echo "tentativa-$i-rc=$rc" >> $D/saida_export.log; sleep 30
done
echo "rc=$rc" > $D/export_fim.txt
