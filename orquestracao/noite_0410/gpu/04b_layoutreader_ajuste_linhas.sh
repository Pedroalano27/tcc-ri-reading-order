#!/bin/bash
# Segunda tentativa do roteiro 02 (a primeira falhou: LayoutLMv3 sem gradient checkpointing; corrigido).
# Noite de 04->05/10 (escrito pelo orquestrador depois que o Codex bateu no limite de uso as 02:20).
# Treina layoutreader/linhas na GPU nas 873 paginas congeladas (resultados/unidades_sem_caixas/treino_noite.json),
# um token por unidade (so layout), ate 70 min; depois ordena as tres bancadas em CPU e avalia na bancada.
cd "$(dirname "$0")/../../.." || exit 1
export PYTHONIOENCODING=utf-8
N=layoutreader_ajustado_linhas; O=resultados/ordenadores_treinados_sem_caixas/$N
venv/Scripts/python.exe -B orquestracao/analises/layoutreader_ajuste.py treinar --modelo layoutreader --representacao linhas --device cuda   --max-minutos 70 --epocas 4 --batch 8 --micro-batch 1 --nome $N --dir-saida $O || exit 1
venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas.py --checkpoint $O/melhor.pt --avaliar || exit 2
