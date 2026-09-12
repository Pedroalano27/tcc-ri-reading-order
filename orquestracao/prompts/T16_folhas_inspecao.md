## Objetivo

Gerar imagens das quatro páginas-problema com as caixas de cada versão do segmentador
desenhadas por cima, para inspeção visual. Elas vão ser usadas para decidir qual versão da
segmentação fica (tarefa T03). É um trabalho mecânico: nenhuma decisão de método, só desenhar
e contar.

## Escopo

Pode **criar**:
- `src/data/inspecionar_segmentacao.py`
- a pasta `resultados/inspecao_segmentacao/` e o que houver dentro dela

Pode **ler** qualquer arquivo. **Não altere nenhum arquivo existente.** Não escreva em `data/`.

## As quatro páginas

Os PDFs estão em `data/raw/<veiculo>/` (procure recursivamente pelo nome do arquivo). A página
é numerada a partir de **0**, e o `page_id` de cada uma é `<veiculo>/<arquivo>#p<pagina>`.

| Rótulo | Veículo | Arquivo | Página |
|---|---|---|---:|
| `MA_negrito` | `official_diary_ma` | `executive_official_diary_2024-01-18_22_36.pdf` | 0 |
| `SE_justificado` | `official_diary_se` | `DOE-SE_2023-03-10_5100.pdf` | 14 |
| `RJ_tres_colunas` | `official_diary_rj` | `Parte II (Poder Legislativo)_2024-02-06.pdf` | 1 |
| `CE_texto_corrido` | `official_diary_ce` | `do20250314p03.pdf` | 45 |

## As três versões

Para cada página, obtenha os blocos de três fontes:

| Versão | De onde vêm os blocos |
|---|---|
| `v1` | procure a linha com o `page_id` em `data/processed/blocos_v1/<veiculo>.jsonl`; campo `bounding_boxes`, cada um com `bbox` = `[x0, top, x1, bottom]` |
| `B` | a mesma busca em `data/processed/blocos/<veiculo>.jsonl` |
| `C` | rode o código atual: abra o PDF com `pdfplumber`, pegue a página, e chame `palavras_da_pagina(pagina)` e depois `segmentar(palavras)`, ambas de `src/data/extrator.py`; cada bloco devolvido é um dicionário com `x0`, `top`, `x1`, `bottom` e `texto` |

Se a página não existir numa das pastas, **não invente**: gere o painel com o aviso "página
ausente nesta coleta".

## O que desenhar

Para cada página e versão, uma imagem PNG da página inteira a 110 dpi (use
`pagina.to_image(resolution=110)` do `pdfplumber`, que já converte coordenadas do PDF), com:

- o contorno de cada bloco: **vermelho** se o bloco tem mais de 250 palavras; **laranja** se a
  caixa se sobrepõe a outra (use a função `qualidade` de `src/data/reextrair.py` como
  referência da regra: interseção de pelo menos 25% da área da menor caixa); **cinza** se tem
  uma palavra só; **azul** nos demais;
- no topo da imagem, uma faixa com: rótulo da página, versão, número de blocos, % de blocos
  sobrepostos, número de blocos acima de 250 palavras e de blocos de uma palavra.

Depois, para cada página, junte as três imagens lado a lado num PNG só
(`<rotulo>_comparativo.png`), com `PIL`.

## Saídas

Em `resultados/inspecao_segmentacao/`:
- `<rotulo>_v1.png`, `<rotulo>_B.png`, `<rotulo>_C.png` e `<rotulo>_comparativo.png`, para as quatro páginas;
- `contagens.json` com, por página e versão: `n_blocos`, `pct_sobrepostos`,
  `n_acima_250_palavras`, `n_uma_palavra`, `maior_bloco_palavras` e se a página estava ausente.

## Pronto quando

1. `venv\Scripts\python.exe src\data\inspecionar_segmentacao.py` gera os 16 PNGs e o JSON do
   zero, sem erro.
2. Os números de blocos batem com estes, medidos pelo orquestrador (confira e diga se algum
   não bater): MA — v1 54, B 36, C 85; SE — v1 39, B 30, C 48; RJ — v1 74, B 53, C 159;
   CE — C 15 (a página foi rejeitada na B e pode estar ausente na v1).
3. O script tem docstring no topo no padrão do projeto (o que faz, por quê, como usar;
   português sem acento nos `.py`).
4. A resposta final lista os arquivos gerados e a tabela de contagens.
