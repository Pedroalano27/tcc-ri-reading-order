## Objetivo

Converter as saídas do **Google Document AI** que estão no acervo para o formato de páginas do
protocolo do projeto. Isso permite rodar a comparação de métodos sobre blocos produzidos por
um detector de layout **de produção**, e não pela nossa heurística — é a validação externa da
análise de sensibilidade à segmentação (T11).

## Escopo

Pode **criar**:
- `src/data/converter_docai.py`
- a pasta `data/processed/blocos_docai_japeri/` e o que houver dentro dela

Pode **ler** qualquer arquivo do repositório. **Não altere** nenhum arquivo existente:
`src/data/extrator.py`, `src/eval/protocolo.py` e os demais são usados por outros agentes
agora mesmo.

## Entradas

Pasta `data/raw/official_diary_rj_japeri/diarios_avaliados_apis_pagas/`:

| JSON do Document AI | PDF correspondente | Observação |
|---|---|---|
| `executive_official_diary_2025-08-04_Boletim_7621_processado_completo.json` (34 MB) | `executive_official_diary_2025-08-04_Boletim_7621.pdf` | 14 páginas; também tem `chunkedDocument` (ignore) |
| `Google Doc AI Tests/document (1).json` (6 MB) | `Google Doc AI Tests/Parte I (Poder Executivo)_2021-06-10.pdf` | 2 páginas; é o Diário Oficial do **Estado** do RJ, não de Japeri — confirme pelo texto e pelo número de páginas |

Formato conhecido: `documentLayout.blocks[]`, cada bloco com `blockId`, `pageSpan`
(`pageStart`/`pageEnd`, **base 1**), `boundingBox.normalizedVertices` (quatro vértices com
`x`,`y` em 0–1; use mínimo e máximo, não suponha a ordem dos vértices) e um de `textBlock`
(`text`, `type`, e às vezes `blocks` filhos — **a estrutura é aninhada**) ou `tableBlock`.
Inspecione os dois arquivos antes de decidir; eles podem diferir.

## Formato de saída

Um `.jsonl` por veículo, `data/processed/blocos_docai_japeri/official_diary_rj_japeri.jsonl`,
uma página por linha, **idêntico ao das outras coleções** (confira em
`data/processed/blocos_v1/official_diary_rj_japeri.jsonl` e em
`src/data/extrator.py:processar_pagina`):

- `page_id` = `official_diary_rj_japeri/<caminho do PDF relativo a data/raw/official_diary_rj_japeri, com />#p<página base 0>`
- `uf`, `arquivo`, `pagina` (base 0), `dimensions` (`width`, `height` do PDF em pontos, lidos com `pdfplumber`)
- `bounding_boxes`: `id`, `text`, `bbox` = `[x0, top, x1, bottom]` **em pontos do PDF**
  (vértice normalizado × dimensão da página), arredondado a 0,1; pode acrescentar `tipo`
  (o `type` do Document AI, ou `table`)
- `ordens`: `stream` = ordem em que o Document AI emite os blocos (percurso em profundidade);
  `naive` = por `(top, x0)`; `xycut` = função `xycut` de `src/data/extrator.py`
- `stats`: `n_blocos`, `n_palavras`, `n_colunas` (função `estimar_colunas` de `extrator.py`)
- identificadores `b<k>` sorteados por permutação semeada com o `page_id`, exatamente como em
  `processar_pagina`, para que o nome do bloco não carregue ordem

## Decisões que você toma e registra na resposta

1. **Unidade de bloco:** use os blocos de texto **folha** (sem filhos com texto). Se um bloco
   pai tem texto próprio além dos filhos, explique como tratou.
2. **Tabelas:** cada `tableBlock` vira **um** bloco, com o texto das células concatenado linha
   a linha, `tipo` = `table`. Conte quantas páginas têm tabela.
3. **Bloco em mais de uma página** (`pageStart` ≠ `pageEnd`) ou **sem caixa:** não descarte em
   silêncio — conte e liste.
4. **Filtro de 3 a 200 blocos** do extrator: aplique o mesmo, e liste as páginas que ficaram fora.

## Comparação com o nosso extrator

Nas mesmas páginas, rode o nosso segmentador ao vivo (`palavras_da_pagina` + `segmentar` de
`src/data/extrator.py` — é a versão **C**, não validada; diga isso no relatório) e grave em
`data/processed/blocos_docai_japeri/_comparacao_extrator.json`, para as duas fontes: páginas,
blocos por página (média e mediana), palavras por bloco (mediana, p95, máximo), % de blocos de
uma palavra, % com até três palavras e % de blocos sobrepostos — use
`src/data/reextrair.py:qualidade` para a sobreposição, que é a definição do projeto.

## Pronto quando

1. `venv\Scripts\python.exe src\data\converter_docai.py` gera a pasta do zero, sem erro.
2. As páginas carregam com
   `iterar_paginas(["official_diary_rj_japeri"], "data/processed/blocos_docai_japeri")` de
   `src/eval/protocolo.py`.
3. Em cada página, as três ordens são permutações exatas dos identificadores e toda caixa
   cabe dentro de `dimensions`.
4. O script tem docstring no topo no padrão do projeto (o que faz, por quê, como usar;
   português sem acento nos `.py`).
5. A resposta final traz a tabela de comparação com os números.
