# Avaliação contra anotação humana: lote `_avaliacao/golden_v3`

Referência: ordem anotada por **Pedro alano** em 47 de 47 páginas (0 puladas). Grupos: incerto, silver.

## Todas as páginas anotadas

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 47 | **0.714** (0.594-0.822) | 0.143 | 78% | 0.109 | 21% |
| Ordem do detector (sem ordenar) | 47 | **-0.007** (-0.050-0.038) | -0.143 | 7% | 0.336 | 0% |
| Ingênua (topo→base, esq.→dir.) | 47 | **0.781** (0.722-0.842) | 0.510 | 60% | 0.098 | 32% |
| XY-cut (heurística de colunas) | 47 | **0.851** (0.796-0.901) | 0.556 | 74% | 0.068 | 23% |
| LLM gemma4:31b (zero-shot) | 47 | **0.870** (0.813-0.923) | 0.530 | 76% | 0.057 | 40% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 47 | **0.873** (0.813-0.927) | 0.496 | 75% | 0.053 | 38% |
| LLM qwen3.6:35b (zero-shot) | 47 | **0.632** (0.561-0.700) | 0.282 | 39% | 0.140 | 9% |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 47 | **0.710** (0.639-0.777) | 0.329 | 44% | 0.108 | 15% |
| LLM qwen3.8:27b (zero-shot) | 47 | **0.853** (0.789-0.910) | 0.505 | 73% | 0.062 | 26% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 47 | **0.881** (0.825-0.928) | 0.546 | 74% | 0.048 | 28% |

## Grupo `incerto`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 26 | **0.544** (0.349-0.708) | -0.333 | 68% | 0.169 | 8% |
| Ordem do detector (sem ordenar) | 26 | **-0.024** (-0.094-0.044) | -0.222 | 7% | 0.341 | 0% |
| Ingênua (topo→base, esq.→dir.) | 26 | **0.795** (0.706-0.882) | 0.502 | 61% | 0.092 | 27% |
| XY-cut (heurística de colunas) | 26 | **0.834** (0.758-0.909) | 0.505 | 72% | 0.077 | 27% |
| LLM gemma4:31b (zero-shot) | 26 | **0.920** (0.855-0.974) | 0.667 | 81% | 0.036 | 46% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 26 | **0.924** (0.860-0.977) | 0.778 | 82% | 0.034 | 50% |
| LLM qwen3.6:35b (zero-shot) | 26 | **0.674** (0.582-0.762) | 0.282 | 42% | 0.124 | 12% |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 26 | **0.765** (0.677-0.847) | 0.333 | 47% | 0.088 | 19% |
| LLM qwen3.8:27b (zero-shot) | 26 | **0.918** (0.883-0.951) | 0.778 | 77% | 0.035 | 27% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 26 | **0.942** (0.915-0.967) | 0.833 | 78% | 0.025 | 35% |

## Grupo `silver`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 21 | **0.925** (0.844-0.984) | 0.814 | 89% | 0.034 | 38% |
| Ordem do detector (sem ordenar) | 21 | **0.014** (-0.027-0.062) | -0.098 | 6% | 0.331 | 0% |
| Ingênua (topo→base, esq.→dir.) | 21 | **0.765** (0.683-0.852) | 0.524 | 59% | 0.107 | 38% |
| XY-cut (heurística de colunas) | 21 | **0.873** (0.805-0.936) | 0.616 | 76% | 0.056 | 19% |
| LLM gemma4:31b (zero-shot) | 21 | **0.809** (0.716-0.893) | 0.462 | 71% | 0.082 | 33% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 21 | **0.810** (0.709-0.905) | 0.437 | 65% | 0.078 | 24% |
| LLM qwen3.6:35b (zero-shot) | 21 | **0.580** (0.471-0.690) | 0.369 | 36% | 0.160 | 5% |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 21 | **0.642** (0.540-0.740) | 0.319 | 41% | 0.132 | 10% |
| LLM qwen3.8:27b (zero-shot) | 21 | **0.773** (0.650-0.885) | 0.333 | 69% | 0.095 | 24% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 21 | **0.806** (0.695-0.899) | 0.421 | 70% | 0.078 | 19% |

## Referência vinda de `golden_v1 projetada (v3)`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 20 | **0.684** (0.478-0.849) | 0.378 | 77% | 0.118 | 20% |
| Ordem do detector (sem ordenar) | 20 | **0.021** (-0.034-0.079) | -0.088 | 5% | 0.333 | 0% |
| Ingênua (topo→base, esq.→dir.) | 20 | **0.779** (0.673-0.878) | 0.510 | 64% | 0.099 | 35% |
| XY-cut (heurística de colunas) | 20 | **0.867** (0.786-0.936) | 0.567 | 71% | 0.061 | 15% |
| LLM gemma4:31b (zero-shot) | 20 | **0.918** (0.847-0.974) | 0.667 | 85% | 0.038 | 50% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 20 | **0.968** (0.939-0.990) | 0.895 | 87% | 0.014 | 55% |
| LLM qwen3.6:35b (zero-shot) | 20 | **0.668** (0.552-0.774) | 0.325 | 43% | 0.125 | 10% |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 20 | **0.673** (0.562-0.780) | 0.333 | 42% | 0.119 | 15% |
| LLM qwen3.8:27b (zero-shot) | 20 | **0.901** (0.810-0.966) | 0.752 | 81% | 0.040 | 30% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 20 | **0.881** (0.790-0.953) | 0.765 | 78% | 0.048 | 25% |

## Referência vinda de `golden_v2`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 27 | **0.736** (0.579-0.872) | 0.143 | 78% | 0.101 | 22% |
| Ordem do detector (sem ordenar) | 27 | **-0.028** (-0.092-0.029) | -0.205 | 7% | 0.339 | 0% |
| Ingênua (topo→base, esq.→dir.) | 27 | **0.783** (0.704-0.856) | 0.524 | 57% | 0.098 | 30% |
| XY-cut (heurística de colunas) | 27 | **0.840** (0.761-0.905) | 0.505 | 76% | 0.073 | 30% |
| LLM gemma4:31b (zero-shot) | 27 | **0.835** (0.743-0.910) | 0.462 | 70% | 0.070 | 33% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 27 | **0.804** (0.711-0.888) | 0.354 | 66% | 0.082 | 26% |
| LLM qwen3.6:35b (zero-shot) | 27 | **0.605** (0.506-0.698) | 0.282 | 37% | 0.151 | 7% |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 27 | **0.737** (0.648-0.816) | 0.329 | 46% | 0.100 | 15% |
| LLM qwen3.8:27b (zero-shot) | 27 | **0.818** (0.728-0.893) | 0.482 | 68% | 0.078 | 22% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 27 | **0.881** (0.810-0.939) | 0.546 | 72% | 0.049 | 30% |

## A referência automática se sustenta?

- Grupo `incerto`: o fluxo do PDF concorda com o humano com tau médio **0.544** (pior caso p10 -0.333, 8% das páginas idênticas).
- Grupo `silver`: o fluxo do PDF concorda com o humano com tau médio **0.925** (pior caso p10 0.814, 38% das páginas idênticas).

## Wilcoxon pareado contra a XY-cut

| A | B | n | p-valor |
|---|---|---:|---:|
| XY-cut (heurística de colunas) | Fluxo do PDF (referência silver) | 47 | 0.23 |
| XY-cut (heurística de colunas) | Ordem do detector (sem ordenar) | 47 | 2.4e-09 |
| XY-cut (heurística de colunas) | Ingênua (topo→base, esq.→dir.) | 47 | 0.037 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (zero-shot) | 47 | 0.23 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (few-shot, 2 exemplos) | 47 | 0.35 |
| XY-cut (heurística de colunas) | LLM qwen3.6:35b (zero-shot) | 47 | 1.6e-06 |
| XY-cut (heurística de colunas) | LLM qwen3.6:35b (few-shot, 2 exemplos) | 47 | 5.3e-05 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (zero-shot) | 47 | 0.45 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (few-shot, 2 exemplos) | 47 | 0.24 |

## Custo da anotação

45 min de trabalho ativo: 57 s por página, 2.2 s por bloco.
