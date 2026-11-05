set -e
S=orquestracao/fase_nov/spark.sh
bash $S sincronizar
bash $S enviar e003_rn -- --partition=hpc-spark-45 --time=06:00:00 cluster/job_pontuar.sh Qwen/Qwen3-8B
bash $S esperar e003_rn
bash $S trazer '~/tcc/ordem_lm/escores' resultados/ordem_lm/escores
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B
