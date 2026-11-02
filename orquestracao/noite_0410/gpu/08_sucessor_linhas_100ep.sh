#!/bin/bash
# Treino longo: com 40 epocas as quebras cairam de 57,6 para 11,0 por pagina no golden_v4 e a validacao
# ainda subia; esta versao vai a 100 epocas (ate 165 min).
# Noite de 04->05/10 (escrito pelo orquestrador depois que o Codex bateu no limite de uso as 02:20).
# Treina sucessor/linhas na GPU nas 873 paginas congeladas (resultados/unidades_sem_caixas/treino_noite.json),
# um token por unidade (so layout), ate 75 min; depois ordena as tres bancadas em CPU e avalia na bancada.
cd "$(dirname "$0")/../../.." || exit 1
export PYTHONIOENCODING=utf-8
N=sucessor_linhas_100ep; O=resultados/ordenadores_treinados_sem_caixas/$N
venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas.py treinar --modelo sucessor --representacao linhas --device cuda   --max-minutos 165 --epocas 100 --batch 8 --micro-batch 1 --nome $N --dir-saida $O || exit 1
venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas.py --checkpoint $O/melhor.pt --avaliar || exit 2
