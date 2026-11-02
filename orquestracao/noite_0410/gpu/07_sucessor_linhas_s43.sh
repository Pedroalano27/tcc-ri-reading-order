#!/bin/bash
# Segunda semente (43) do roteiro 01, para medir a variacao entre treinos.
# Noite de 04->05/10 (escrito pelo orquestrador depois que o Codex bateu no limite de uso as 02:20).
# Treina sucessor/linhas na GPU nas 873 paginas congeladas (resultados/unidades_sem_caixas/treino_noite.json),
# um token por unidade (so layout), ate 75 min; depois ordena as tres bancadas em CPU e avalia na bancada.
cd "$(dirname "$0")/../../.." || exit 1
export PYTHONIOENCODING=utf-8
N=sucessor_linhas_s43; O=resultados/ordenadores_treinados_sem_caixas/$N
venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas.py treinar --modelo sucessor --representacao linhas --device cuda   --max-minutos 75 --epocas 8 --batch 8 --micro-batch 1 --seed 43 --nome $N --dir-saida $O || exit 1
venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas.py --checkpoint $O/melhor.pt --avaliar || exit 2
