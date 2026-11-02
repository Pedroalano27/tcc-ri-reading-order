## Contexto

Na segmentação v3, o LayoutLM com predição de sucessor vai bem no teste silver (89 páginas: τ 0,878,
71% de sucessor correto; `resultados/comparacao.md`). No Golden, contra a leitura humana (47
páginas, `resultados/golden/_avaliacao/golden_v3/avaliacao.md`), ele cai para τ 0,699 (p10 0,275),
enquanto o LayoutLM pontual fica em 0,846 e o XY-cut em 0,851. Queremos saber em que páginas e por
quê.

## Escopo

Crie somente `resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md` (e, se quiser, um
script de apoio em `orquestracao/analises/diagnostico_sucessor.py`). Não altere nenhum outro arquivo,
não use GPU e não rode treino nem avaliação: o treino da noite está rodando. Só leia arquivos.

## Dados

- Referência: `data/golden/_avaliacao/golden_v3/referencia.jsonl` (campo `ordem`) e
  `tarefas.jsonl` (`bounding_boxes`, `grupo`, `uf`, `stats.n_colunas`, `stats.n_tabelas`), com
  os flags e notas do anotador em `referencia.jsonl`.
- Predições no Golden: `resultados/golden/_avaliacao/golden_v3/pred_*.jsonl`
  (`page_id`, `ordem_pred`). Para `xycut`, `naive` e `fluxo_pdf`, as ordens estão em
  `tarefas.jsonl` (`ordens.xycut`, `ordens.naive`, `ordens.stream`).
- Métricas: use `src.eval.metrics.avaliar(pred, ref, textos)` e `kendall_tau`, como em
  `src/eval/avaliar_golden.py`.

## O que o relatório deve ter

1. Tabela por página: page_id curto, grupo, uf, blocos, colunas, tabelas, flags do anotador, τ e
   sucessor correto de `layoutlm_sucessor`, `layoutlm` e `xycut`. Ordene pela diferença de τ entre
   `layoutlm_sucessor` e `xycut`, pior primeiro.
2. As 8 páginas em que o sucessor mais perde para o XY-cut. Para cada uma, compare as duas ordens
   bloco a bloco: onde o sucessor começa a errar (posição, texto dos blocos envolvidos, com 40
   caracteres cada) e o padrão do erro. Exemplos: cadeias locais certas coladas na ordem global
   errada; tabela ou cabeçalho posicionado errado; troca de colunas.
3. Médias de τ do sucessor por grupo (`silver`/`incerto`), por número de colunas e com/sem tabela,
   com o n de cada célula.
4. Três hipóteses, em frases curtas, sustentadas pelos números acima. Sem conclusões além deles.

Todo número deve vir do cálculo, com o comando usado registrado no fim do arquivo.

## Resposta final

Em FEITO: o caminho do relatório e as três hipóteses.
