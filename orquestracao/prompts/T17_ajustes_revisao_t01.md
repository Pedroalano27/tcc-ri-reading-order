## Contexto

A T01 (feita pelo Codex do app) centralizou em `montar_treino()`, de `src/eval/protocolo.py`,
a validação das páginas extras do treino ampliado, e fez o empacotador do Kaggle
(`src/kaggle/montar_pacote.py`) recusar coleções vazias. A revisão do Claude aprovou e achou
dois furos, reproduzidos com estes resultados:

| Chamada | Resultado hoje | Problema |
|---|---|---|
| `montar_treino(0, "data/processed/blocos_extra_v1")` | devolve 0 páginas, sem erro | antes da T01, 0 significava "todas"; agora vira um treino vazio silencioso |
| `montar_treino(None, pasta_com_1_dos_7_jsonl)` | devolve 515 páginas (152 + 363), sem erro | uma re-extração interrompida deixa só parte dos veículos; o treino segue com menos dados e ninguém percebe |

O empacotador tem o mesmo furo do segundo caso: aceita a coleção se houver pelo menos um JSONL.

## Escopo

Pode **alterar** somente `src/eval/protocolo.py` e `src/kaggle/montar_pacote.py`.
Não altere os chamadores (`src/models/*.py`, `src/rodar_curva_aprendizado.py`) nem crie
arquivos em `data/`. Para testar, use pastas temporárias fora do repositório (`tempfile`).

## O que fazer

1. **`n_treino ≤ 0`** em `montar_treino` → `ValueError` com mensagem que diga o valor recebido e
   que `None` significa "todas as páginas disponíveis".
2. **Extras parciais** → antes de ler as páginas extras, conferir que existe
   `<dir_extra>/<veiculo>.jsonl` para **cada um** dos veículos de treino de `splits.json`. Se
   faltar algum, `FileNotFoundError` listando os ausentes e dizendo que a re-extração parece
   incompleta. Um JSONL existente mas sem nenhuma página válida conta como ausente.
3. **Empacotador** → para cada coleção, conferir a lista esperada de veículos, não só a
   existência de um arquivo:
   - `data/processed/blocos`: todos os veículos citados em `splits.json` (treino, validação,
     teste e não confiáveis);
   - `data/processed/blocos_extra`: todos os veículos de treino;
   - `data/processed/blocos_ri_japeri`: `official_diary_rj_japeri`.

   Se faltar algo, encerrar com a lista do que falta, sem criar o zip.
4. Manter todo o comportamento já validado da T01 (mensagens, contagem impressa de páginas base
   e extras, erro para pasta ausente ou vazia, erro para pedido acima do disponível).

## Pronto quando

Mostrar na resposta a saída destes casos, rodados com `venv\Scripts\python.exe`:

| Caso | Esperado |
|---|---|
| `montar_treino(None, None)` | 152 páginas |
| `montar_treino(None, "data/processed/blocos_extra_v1")` | 3.235 páginas (152 + 3.083) |
| `montar_treino(400, "data/processed/blocos_extra_v1")` | 400 páginas |
| `montar_treino(0, "data/processed/blocos_extra_v1")` | `ValueError` |
| `montar_treino(-5, None)` | `ValueError` |
| pasta temporária com 1 dos 7 JSONL de `blocos_extra_v1` | `FileNotFoundError` listando os 6 ausentes |
| pasta temporária com os 7, um deles vazio | `FileNotFoundError` citando o vazio |
| `montar_pacote.py` com `data/processed/blocos_extra` ausente (situação atual) | sai com erro e lista a coleção, sem gerar zip |

E também: `venv\Scripts\python.exe src\eval\metrics.py` roda sem erro, e todos os `.py` de
`src/` passam por `ast.parse`.
