set -e
venv/Scripts/python.exe -B orquestracao/analises/e006_residual.py --gerar-rn
head -8 resultados/e006_residual/RELATORIO.md
grep -q "PENDENTE" resultados/e006_residual/RELATORIO.md && { echo "ainda pendente"; exit 1; } || true
