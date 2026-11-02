# Avaliação contra anotação humana: lote `golden_v4`

Referência: ordem anotada por **Pedro alano** em 44 de 45 páginas (1 puladas). Grupos: blocos, blocos_extra, incerto, silver.

## Todas as páginas anotadas

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 44 | **0.632** (0.497-0.761) | 0.000 | 74% | 0.137 | 14% |
| Ordem do detector (sem ordenar) | 44 | **0.053** (0.014-0.094) | -0.143 | 5% | 0.319 | 0% |
| Ingênua (topo→base, esq.→dir.) | 44 | **0.713** (0.639-0.785) | 0.339 | 58% | 0.124 | 18% |
| XY-cut (heurística de colunas) | 44 | **0.825** (0.763-0.886) | 0.538 | 71% | 0.083 | 27% |
| LLM gemma4:31b (zero-shot) | 44 | **0.822** (0.746-0.892) | 0.401 | 80% | 0.078 | 34% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 44 | **0.848** (0.770-0.922) | 0.357 | 79% | 0.063 | 34% |
| LLM qwen3.8:27b (zero-shot) | 44 | **0.859** (0.781-0.923) | 0.569 | 80% | 0.058 | 36% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 44 | **0.876** (0.820-0.923) | 0.692 | 76% | 0.051 | 36% |

## Grupo `blocos`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 20 | **0.671** (0.519-0.813) | 0.238 | 74% | 0.131 | 5% |
| Ordem do detector (sem ordenar) | 20 | **0.069** (0.004-0.136) | -0.143 | 4% | 0.311 | 0% |
| Ingênua (topo→base, esq.→dir.) | 20 | **0.738** (0.635-0.846) | 0.429 | 62% | 0.116 | 25% |
| XY-cut (heurística de colunas) | 20 | **0.844** (0.754-0.928) | 0.538 | 73% | 0.075 | 40% |
| LLM gemma4:31b (zero-shot) | 20 | **0.860** (0.758-0.942) | 0.576 | 83% | 0.061 | 45% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 20 | **0.849** (0.725-0.949) | 0.606 | 84% | 0.067 | 40% |
| LLM qwen3.8:27b (zero-shot) | 20 | **0.921** (0.862-0.973) | 0.790 | 86% | 0.032 | 55% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 20 | **0.908** (0.832-0.967) | 0.747 | 80% | 0.035 | 55% |

## Grupo `blocos_extra`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 4 | **0.957** (0.881-0.998) | 0.844 | 94% | 0.020 | 25% |
| Ordem do detector (sem ordenar) | 4 | **0.086** (0.037-0.124) | 0.016 | 7% | 0.305 | 0% |
| Ingênua (topo→base, esq.→dir.) | 4 | **0.532** (0.294-0.818) | 0.264 | 48% | 0.193 | 0% |
| XY-cut (heurística de colunas) | 4 | **0.935** (0.911-0.959) | 0.902 | 86% | 0.030 | 0% |
| LLM gemma4:31b (zero-shot) | 4 | **0.560** (0.185-0.934) | 0.168 | 89% | 0.213 | 25% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 4 | **0.942** (0.884-1.000) | 0.854 | 83% | 0.020 | 50% |
| LLM qwen3.8:27b (zero-shot) | 4 | **0.662** (0.145-0.960) | -0.116 | 73% | 0.132 | 0% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 4 | **0.877** (0.758-0.966) | 0.703 | 76% | 0.055 | 0% |

## Grupo `incerto`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 17 | **0.480** (0.213-0.753) | -0.467 | 65% | 0.179 | 12% |
| Ordem do detector (sem ordenar) | 17 | **0.027** (-0.027-0.088) | -0.107 | 6% | 0.333 | 0% |
| Ingênua (topo→base, esq.→dir.) | 17 | **0.723** (0.617-0.839) | 0.339 | 55% | 0.118 | 18% |
| XY-cut (heurística de colunas) | 17 | **0.780** (0.678-0.881) | 0.480 | 68% | 0.103 | 18% |
| LLM gemma4:31b (zero-shot) | 17 | **0.861** (0.754-0.952) | 0.512 | 77% | 0.058 | 29% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 17 | **0.851** (0.730-0.949) | 0.357 | 74% | 0.060 | 24% |
| LLM qwen3.8:27b (zero-shot) | 17 | **0.859** (0.762-0.943) | 0.545 | 78% | 0.062 | 29% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 17 | **0.849** (0.739-0.938) | 0.357 | 74% | 0.065 | 29% |

## Grupo `silver`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 3 | **0.798** (0.394-1.000) | 0.394 | 95% | 0.094 | 67% |
| Ordem do detector (sem ordenar) | 3 | **0.047** (-0.203-0.275) | -0.203 | 6% | 0.313 | 0% |
| Ingênua (topo→base, esq.→dir.) | 3 | **0.726** (0.555-0.987) | 0.555 | 55% | 0.121 | 0% |
| XY-cut (heurística de colunas) | 3 | **0.801** (0.555-1.000) | 0.555 | 63% | 0.086 | 33% |
| LLM gemma4:31b (zero-shot) | 3 | **0.695** (0.401-0.987) | 0.401 | 62% | 0.122 | 0% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 3 | **0.689** (0.080-1.000) | 0.080 | 65% | 0.111 | 33% |
| LLM qwen3.8:27b (zero-shot) | 3 | **0.708** (0.213-0.977) | 0.213 | 65% | 0.108 | 0% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 3 | **0.822** (0.737-0.965) | 0.737 | 56% | 0.069 | 0% |

## A referência automática se sustenta?

- Grupo `blocos`: o fluxo do PDF concorda com o humano com tau médio **0.671** (pior caso p10 0.238, 5% das páginas idênticas).
- Grupo `blocos_extra`: o fluxo do PDF concorda com o humano com tau médio **0.957** (pior caso p10 0.844, 25% das páginas idênticas).
- Grupo `incerto`: o fluxo do PDF concorda com o humano com tau médio **0.480** (pior caso p10 -0.467, 12% das páginas idênticas).
- Grupo `silver`: o fluxo do PDF concorda com o humano com tau médio **0.798** (pior caso p10 0.394, 67% das páginas idênticas).

## Wilcoxon pareado contra a XY-cut

| A | B | n | p-valor |
|---|---|---:|---:|
| XY-cut (heurística de colunas) | Fluxo do PDF (referência silver) | 44 | 0.055 |
| XY-cut (heurística de colunas) | Ordem do detector (sem ordenar) | 44 | 7.6e-09 |
| XY-cut (heurística de colunas) | Ingênua (topo→base, esq.→dir.) | 44 | 0.0074 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (zero-shot) | 44 | 0.84 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (few-shot, 2 exemplos) | 44 | 0.33 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (zero-shot) | 44 | 0.18 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (few-shot, 2 exemplos) | 44 | 0.077 |

## Custo da anotação

13 min de trabalho ativo: 17 s por página, 0.5 s por bloco.
