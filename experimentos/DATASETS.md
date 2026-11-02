# Versões dos dados

Cada experimento registra os hashes (SHA-256, 16 primeiros caracteres) dos arquivos de dados
que usou (`src/exp/registro.py registrar --dados ...`). Esta tabela nomeia as versões, para
que o texto do TCC possa citar "D1", "D2" etc. Gerar os hashes atuais:
`venv/Scripts/python.exe -B src/exp/registro.py dados`.

Regra: uma versão nunca é alterada. Um conjunto novo (ex.: teste cego anotado, dados da Data
Policy convertidos) ganha versão nova, com origem, data e quem anotou.

## D1 — estado de 02/11/2026 (início da fase de novembro)

| Arquivo | Hash | Conteúdo |
|---|---|---|
| `resultados/unidades_sem_caixas/bancadas/golden_v4.jsonl` | `683c64e71e63a753` | 44 páginas humanas em linhas + átomos ls3 (ajuste) |
| `resultados/unidades_sem_caixas/bancadas/golden_v3_novo.jsonl` | `3cbf0331eb778740` | 27 páginas humanas fora do v4 (externa, já consultada) |
| `resultados/unidades_sem_caixas/treino_noite.json` | `46fc38bc27bb40d4` | lista congelada das 3.140 páginas silver de treino |
| `resultados/unidades_sem_caixas/manifesto.json` | `7b50f982104bf466` | manifesto da exportação em linhas (inclui teste silver e validação RN) |
| `data/processed/splits.json` | `f957e4c2e174600f` | divisão por veículo (treino 7, validação RN, teste CE/MA/RJ) |
| `data/golden/golden_v4/anotacoes.jsonl` | `51eccd24ae166a6e` | anotação humana do golden_v4 (somente leitura) |
| `data/golden/golden_v4/tarefas.jsonl` | `f4e151547006e0a8` | tarefas do golden_v4 |

## Planejadas

| Versão | Conteúdo | Depende de |
|---|---|---|
| D2 | + teste cego humano (60 págs do `lote_sem_paragrafos`, anotação do Pedro), **lacrado** até a avaliação final | anotação (DEPENDENCIAS item 3) |
| D3 | + anotações de ordem da Data Policy convertidas para linhas (treino/ajuste) | uso autorizado em 02/11 (DEPENDENCIAS item 2); falta a conversão auditada (E012) |
| D4 | + treino silver ampliado (meta: 10–20 mil páginas dos veículos de treino) | só computação |
