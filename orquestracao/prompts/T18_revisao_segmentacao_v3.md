## Contexto

O Pedro anotou o Golden v1 e as notas dele apontaram seis defeitos da segmentação. O Claude
implementou a **segmentação v3** (tarefas T18, T19 e T20 do quadro; registro de 20:11 com o
diagnóstico). O código mudou desde o commit `3074213` (branch `golden-v1-e-segmentacao`):

| Arquivo | O que mudou |
|---|---|
| `src/data/extrator.py` | `_juntar_letras_espacadas` ("R E S O L V E" → "RESOLVE"); `_reatribuir_faixas` (segunda passada das faixas de linha de base, pelo centro); `_cortes_locais` (calha local, vão a vão) usada em `construir_linhas`; `segmentar(ws, tabelas)` com `_bloco_tabela` (cada região de tabela vira um bloco) e descarte de bloco sem letra nem dígito; `processar_pagina(..., tabelas, palavras)`; `processar_paginas` e `_processar_pedidos_pdf` |
| `src/data/layout.py` (novo) | detector Docling Heron (RT-DETRv2) offline, com revisão fixada; `tabelas()` com supressão de duplicadas; renderização por `pdfplumber.to_image`; cache JSONL por veículo; `garantir_cache` |
| `src/anotacao/projetar_ordem.py` (novo) | leva a ordem anotada de um lote para os blocos da segmentação atual, pela contiguidade das palavras na sequência humana |
| `src/anotacao/preparar_lote.py` | segmenta as páginas do lote na hora, com layout; `--refazer-de LOTE:ROTULO`; filtro de tamanho sobre a segmentação atual; grava `derivados/palavras_por_bloco.jsonl` |
| `src/data/avaliar_segmentacao.py` | usa as tabelas do cache de layout; `--sem-layout` |

Veja o diff com `git diff 3074213 -- src/` e os arquivos novos com `git status`.

Resultados já medidos pelo Claude:
- bancada de 44 páginas (`resultados/avaliacao_segmentacao_v3.json`): 33,3 blocos/pág,
  2,5% sobrepostos, 6,8% de blocos de 1 palavra, 0 páginas rejeitadas, maior bloco 1.748
  palavras (tabela); a versão anterior dava 48,8 / 5,9% / 21,5% / 1;
- projeção do Golden v1 (`data/golden/golden_v1/derivados/projecao_v3.jsonl`): 20 páginas
  limpas, 5 com conflito, 4 sem anotação e 1 rejeitada.

## Tarefa: REVISÃO, sem alterar nenhum arquivo

Revise o código acima procurando **defeitos reais**, com um cenário concreto de falha para cada
um. Prioridades:

1. **Correção.** Erros de lógica em `_reatribuir_faixas`, `_cortes_locais` (subida e descida
   pelas faixas, `livre`, `atravessa`, contagem), `_juntar_letras_espacadas` (falso positivo em
   texto corrido em português; siglas; números romanos; células de tabela) e
   `segmentar`/`_bloco_tabela` (palavra na borda da tabela, tabelas que se sobrepõem, tabela
   que engole a página inteira, página só com tabela).
2. **Coordenadas.** As caixas do detector saem da imagem de `page.to_image()` e são convertidas
   para pontos por `largura_pt / largura_px`. As palavras vêm de `page.extract_words()`. Confira
   se os dois sistemas coincidem em páginas com CropBox diferente da MediaBox e em páginas
   giradas (`/Rotate`). Se houver risco, diga como detectar e corrigir.
3. **Projeção.** Com `projetar_pagina`, é possível uma página sair "limpa" com uma ordem
   projetada que não é a leitura do anotador? E sair "conflito" sem necessidade? Pense em
   palavras que o extrator novo junta (letras espaçadas), em blocos descartados (separadores) e
   no casamento de palavras pelo centro, com folga de 0,6 pt.
4. **Desempenho.** A bancada mediu cerca de 18 s por página com 6 processos, contra 12 s da
   versão anterior. Aponte o gargalo provável (complexidade de `_cortes_locais` em páginas de
   tabela e listas, `_reatribuir_faixas`, `_juntar_letras_espacadas`) e uma correção que não
   mude o resultado.
5. **Reprodutibilidade.** Determinismo de ids e ordens, dependência de ordem de dicionário,
   comportamento com `spawn` no Windows, cache de layout com linha truncada.

## Como verificar

- `venv\Scripts\python.exe -m py_compile` nos arquivos.
- Trechos de Python que só LEEM: por exemplo, carregar `data/processed/layout` com
  `src.data.layout.carregar_cache()` e segmentar páginas com
  `src.data.extrator.processar_paginas(...)`, imprimindo o resultado.
- **Não rode o detector** (`Detector`, `garantir_cache` com páginas fora do cache,
  `layout.py` pela linha de comando): a GPU está reservada para o Claude. As páginas da
  bancada e do Golden v1 já estão no cache.
- **Não rode** `preparar_lote.py`, `projetar_ordem.py` nem `reextrair.py`: eles gravam em
  `data/`.

## Resposta final

Em FEITO, a lista de achados, do mais grave para o menos grave. Cada achado com: arquivo e
linha; o defeito em uma frase; o cenário concreto de falha (entrada → saída errada); a correção
sugerida; e se você **reproduziu** o defeito (com o comando) ou se é só suspeita. Diga
explicitamente o que conferiu e achou correto. Não invente achados para preencher a lista.
