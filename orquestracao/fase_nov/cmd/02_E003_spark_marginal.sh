set -e
S=orquestracao/fase_nov/spark.sh
bash $S sincronizar
ssh -o BatchMode=yes dgx-spark "mkdir -p ~/tcc/ordem_lm/pares_marginal ~/tcc/logs"
scp -q cluster/pontuar_pares_lm.py cluster/requisitos_pontuar.txt dgx-spark:~/tcc/ordem_lm/
scp -q resultados/ordem_lm/pares_marginal/*.jsonl dgx-spark:~/tcc/ordem_lm/pares_marginal/
bash $S enviar e003_marginal -- --partition=hpc-spark-45 --time=03:00:00 cluster/job_pontuar.sh Qwen/Qwen3-8B --entrada pares_marginal --saida escores_marginal
bash $S esperar e003_marginal
bash $S trazer '~/tcc/ordem_lm/escores_marginal' resultados/ordem_lm/escores_marginal
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --saida resultados/e003_lm/ablacao_8b
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --escores-marginal resultados/ordem_lm/escores_marginal/Qwen_Qwen3-8B --saida resultados/e003_lm/contrastivo_8b
ls resultados/e003_lm/contrastivo_8b
