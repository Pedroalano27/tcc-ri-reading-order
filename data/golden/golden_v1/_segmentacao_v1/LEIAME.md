# Arquivo: golden_v1 sobre a segmentação antiga (v1)

Esta pasta guarda o lote `golden_v1` **como ele era antes da correção da segmentação**
(1.044 blocos) e a única anotação humana feita sobre ele. Nenhuma ferramenta lê esta
pasta automaticamente: o servidor de anotação, o avaliador e o pacote do Kaggle só olham
`data/golden/<lote>/`, um nível acima.

| Arquivo | Conteúdo |
|---|---|
| `tarefas.jsonl` | As 30 páginas com os blocos da segmentação v1, exatamente como foram mostradas na ferramenta |
| `anotacoes.jsonl` | Página 1 (`official_diary_ce/do20220530p02.pdf#p53`), concluída: 28 blocos ordenados, marcada com "tabela" e "segmentação", 254 s de trabalho ativo |

## Procedência

- A anotação foi feita em 2026-09-12, por volta de 14h18, no navegador embutido do app do
  Claude. O campo **Anotador** estava preenchido com `teste_claude`, resto de um teste da
  ferramenta que ficou guardado no navegador; a anotação é quase certamente do Pedro.
- Foi durante essa anotação que o problema da segmentação apareceu — daí a marcação
  "segmentação" (bloco mistura colunas ou trechos distantes).
- O arquivo original foi apagado por engano na sessão seguinte e **reconstruído** a partir
  do conteúdo impresso antes da remoção. A ordem dos 28 blocos confere exatamente com os
  identificadores de `tarefas.jsonl` desta pasta. O horário `salvo_em` é aproximado
  (14:18:57 ou 14:19:21). Um rascunho da página 2, incompleto, não foi recuperado.

## Por que não está no lote ativo

Os identificadores de bloco são sorteados sobre o conjunto de blocos da página. Quando a
segmentação muda, os blocos mudam e os identificadores deixam de corresponder: esta
anotação **não vale** para o `golden_v1` regenerado. Ela serve como registro do custo de
anotação (254 s para 28 blocos) e como evidência do defeito de segmentação encontrado.
