**FEITO:** três representações exportadas em CPU: 44 páginas v4, 27 v3 novo, 15 validação, 89 teste e 60 treino. Retomada e verificações passaram.

**ARQUIVOS:** [gerador](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/unidades_sem_caixas.py) e [relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/unidades_sem_caixas.md), com datasets e caches em `resultados/unidades_sem_caixas/`.

**EVIDÊNCIA:** âncoras reproduzidas: τ 0,985948 / 6,045455 quebras e τ 0,952424 / 8,931818 quebras. Integridade das palavras e ausência de vazamento conferidas. Pico RSS: 1.064,9 MiB. O relatório detalha os cruzamentos de referência nas faixas.

**PENDÊNCIAS:** exportar as 3.157 páginas restantes; estimativa de 3,18 horas, com limitações declaradas. Nenhum ordenador foi treinado.

```powershell
venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 0
```