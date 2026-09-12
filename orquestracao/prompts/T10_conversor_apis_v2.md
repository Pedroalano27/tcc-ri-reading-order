## Contexto: por que esta é a segunda versão

Na primeira execução da T10 você parou pela regra 5, e acertou: o JSON do Boletim 7621 não tem
nenhuma caixa (e é de Duque de Caxias), e o `document (1).json` cobre só 2 das 22 páginas do
PDF. O orquestrador achou uma fonte melhor, o **Azure Document Intelligence**, e reespecificou
a tarefa. **Ignore o Boletim 7621.**

## Objetivo

Converter as saídas de **dois detectores de layout comerciais** (Azure e Google) para o formato
de páginas do protocolo, para comparar a nossa segmentação com a de sistemas de produção e,
mais adiante, usar a ordem de leitura do Azure como referência comercial.

## Escopo

Pode **criar**:
- `src/data/converter_apis.py`
- as pastas `data/processed/blocos_api_azure/` e `data/processed/blocos_api_docai/` e o que houver dentro delas

Pode **ler** qualquer arquivo. **Não altere nenhum arquivo existente.**

## Entrada 1: Azure Document Intelligence, `prebuilt-layout` (API 2024-11-30)

Arquivos `data/raw/official_diary_rj_japeri/json_atos_japeri/resultado_azure_lote_layout.jsonl` e
`resultado_azure_lote_layout.txt`. **Apesar da extensão, nenhum dos dois é JSONL.** Cada um é uma
sequência de blocos assim:

```
NOME DO ARQUIVO: <nome do pdf>
{ ...JSON do Azure, com várias linhas... }
==================================================
```

Separe pelos cabeçalhos `NOME DO ARQUIVO:` e leia cada JSON com `json.JSONDecoder().raw_decode`
(sobra a linha de `=` depois do objeto). Um dos blocos não é JSON: começa com
`Erro na consulta de JAPERI-5174-26-DE-JULHO-2022.pdf (429)` — pule e relate.

O orquestrador conferiu o conteúdo (confirme):

| PDF | Onde está | Páginas analisadas | Parágrafos |
|---|---|---:|---:|
| `Parte I (Poder Executivo)_2021-06-10.pdf` | `data/raw/official_diary_rj/` | 2 | 228 |
| `JAPERI-6003-30-DE-DEZEMBRO-DE-2025.pdf` | `data/raw/official_diary_rj_japeri/diarios_avaliados_apis_pagas/TEMP/` | 2 | 147 |
| `JAPERI-5203-05-DE-SETEMBRO-2022.pdf` | idem | 2 | 125 |
| `JAPERI-5192-19-DE-AGOSTO-2022.pdf` | idem | 2 | 136 |
| `JAPERI-5339-30-DE-MARcO-2023.pdf` | idem | 2 | 135 |
| `JAPERI-5290-16-DE-JANEIRO-2023.pdf` | idem | 2 | 180 |

Em `analyzeResult`: `pages[]` (`pageNumber` base 1, `width`, `height`, `unit` = `inch`) e
`paragraphs[]`, cada um com `content`, `role` opcional (`title`, `sectionHeading`, `pageHeader`,
`pageFooter`, `pageNumber`) e `boundingRegions[]` com `pageNumber` e `polygon` (8 números
x1,y1…x4,y4, **em polegadas**). Caixa em pontos do PDF = mínimo e máximo do polígono × 72.
**Confira** a conversão contra as dimensões do PDF lidas com `pdfplumber` (a razão deve bater
com 72 pontos por polegada). A ordem do array `paragraphs` é a ordem de leitura do Azure.

## Entrada 2: Google Document AI, só as páginas com caixas

`data/raw/official_diary_rj_japeri/diarios_avaliados_apis_pagas/Google Doc AI Tests/document (1).json`:
2 páginas do mesmo `Parte I (Poder Executivo)_2021-06-10.pdf`. Você já mapeou a estrutura (286
nós com caixa normalizada, estrutura aninhada, uma tabela). Descubra **quais** páginas do PDF de
22 páginas são essas duas comparando o texto do JSON com o de cada página do PDF, e registre
como decidiu. Use as folhas de texto e trate cada tabela como um bloco, como você propôs.

## Formato de saída

Um `.jsonl` por veículo em cada pasta (`data/processed/blocos_api_azure/official_diary_rj.jsonl`,
`.../official_diary_rj_japeri.jsonl`, e o mesmo para `blocos_api_docai`), **no formato das outras
coleções** (confira `data/processed/blocos_v1/*.jsonl` e `src/data/extrator.py:processar_pagina`):

- `page_id` = `<veiculo>/<caminho do PDF relativo a data/raw/<veiculo>, com />#p<página base 0>`
- `uf`, `arquivo`, `pagina` (base 0), `dimensions` em pontos (do PDF, via `pdfplumber`)
- `bounding_boxes`: `id`, `text`, `bbox` `[x0, top, x1, bottom]` em pontos, arredondado a 0,1, e
  `papel` (o `role` do Azure, o `type` do Google, ou `table`; vazio se não houver)
- `ordens`: `stream` = ordem em que a API emite os blocos; `naive` = por `(top, x0)`;
  `xycut` = `xycut` de `src/data/extrator.py`
- `stats`: `n_blocos`, `n_palavras`, `n_colunas` (`estimar_colunas` de `extrator.py`)
- identificadores `b<k>` por permutação semeada com o `page_id`, como em `processar_pagina`
- **não** aplique o filtro de 3 a 200 blocos aqui; apenas relate páginas fora dessa faixa

## Comparação de segmentação

Grave `data/processed/blocos_api_azure/_comparacao_segmentacao.json` e imprima a tabela. Para as
12 páginas do Azure, as 2 do Google e o nosso segmentador rodado ao vivo **nas mesmas páginas**
(`palavras_da_pagina` + `segmentar` de `src/data/extrator.py`; é a versão C, **não validada** —
diga isso), por fonte: páginas, blocos por página (média e mediana), palavras por bloco (mediana,
p95, máximo), % de blocos de uma palavra, % com até três palavras, % de blocos sobrepostos
(`qualidade` de `src/data/reextrair.py`) e, para as APIs, a contagem por papel. Separe a linha das
2 páginas do Estado do RJ, onde as três fontes existem.

## Pronto quando

1. `venv\Scripts\python.exe src\data\converter_apis.py` gera as duas pastas do zero, sem erro.
2. As páginas carregam com `iterar_paginas([...], "data/processed/blocos_api_azure")` e
   `iterar_paginas([...], "data/processed/blocos_api_docai")` de `src/eval/protocolo.py`.
3. Em cada página, as três ordens são permutações exatas dos identificadores e toda caixa cabe
   em `dimensions` (tolerância de 1 pt).
4. Docstring no topo no padrão do projeto (português sem acento nos `.py`).
5. A resposta final traz a tabela de comparação e as decisões tomadas (páginas do Google, polegadas → pontos, tabelas).
