set -e
venv/Scripts/python.exe -c "import lightgbm; print('lightgbm', lightgbm.__version__)"
venv/Scripts/python.exe -B orquestracao/analises/e004_grafo.py
head -8 resultados/e004_grafo/RELATORIO.md
venv/Scripts/python.exe -B orquestracao/analises/e005_seletor.py
head -8 resultados/e005_seletor/RELATORIO.md
