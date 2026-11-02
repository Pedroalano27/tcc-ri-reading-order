# Avaliação contra anotação humana: lote `golden_v4`

Referência: ordem anotada por **Pedro alano** em 44 de 45 páginas (1 puladas). Grupos: blocos, blocos_extra, incerto, silver.

## Todas as páginas anotadas

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 44 | **0.632** (0.497-0.761) | 0.000 | 74% | 0.137 | 14% |
| Ordem do detector (sem ordenar) | 44 | **0.053** (0.014-0.094) | -0.143 | 5% | 0.319 | 0% |
| Ingênua (topo→base, esq.→dir.) | 44 | **0.713** (0.639-0.785) | 0.339 | 58% | 0.124 | 18% |
| XY-cut (heurística de colunas) | 44 | **0.825** (0.763-0.886) | 0.538 | 71% | 0.083 | 27% |
| LayoutLM pontual: um escore por bloco | 44 | **0.847** (0.803-0.887) | 0.686 | 35% | 0.060 | 7% |
| LayoutLM sucessor: prevê o próximo bloco | 44 | **0.890** (0.845-0.932) | 0.667 | 67% | 0.043 | 9% |
| ablacao_suc_sem_layout | 44 | **0.280** (0.196-0.371) | -0.118 | 31% | 0.247 | 2% |
| ablacao_suc_sem_posicao | 44 | **0.321** (0.188-0.453) | -0.287 | 66% | 0.266 | 7% |
| ablacao_suc_sem_texto | 44 | **0.863** (0.796-0.918) | 0.670 | 73% | 0.055 | 23% |
| ablacao_suc_sem_vies_geo | 44 | **0.880** (0.820-0.928) | 0.771 | 69% | 0.049 | 9% |
| layoutlm_sem_layout | 44 | **0.124** (0.058-0.184) | -0.062 | 10% | 0.289 | 0% |
| LLM gemma4:31b (zero-shot) | 44 | **0.822** (0.746-0.892) | 0.401 | 80% | 0.078 | 34% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 44 | **0.848** (0.770-0.922) | 0.357 | 79% | 0.063 | 34% |
| LLM qwen3.8:27b (zero-shot) | 44 | **0.859** (0.781-0.923) | 0.569 | 80% | 0.058 | 36% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 44 | **0.876** (0.820-0.923) | 0.692 | 76% | 0.051 | 36% |
| pontual_seed1 | 44 | **0.852** (0.785-0.905) | 0.714 | 38% | 0.054 | 14% |
| pontual_seed2 | 44 | **0.850** (0.791-0.899) | 0.697 | 39% | 0.056 | 11% |
| sucessor_seed1 | 44 | **0.847** (0.792-0.896) | 0.667 | 54% | 0.060 | 9% |
| sucessor_seed2 | 44 | **0.873** (0.822-0.919) | 0.667 | 66% | 0.051 | 7% |
| LLM gemini-3.1-flash-lite (zero-shot) | 44 | **0.962** (0.925-0.987) | 0.889 | 94% | 0.017 | 68% |
| LLM gemini-3.1-flash-lite (zero-shot) | 44 | **0.966** (0.937-0.988) | 0.830 | 94% | 0.016 | 66% |
| LLM gemini-3.1-flash-lite (zero-shot) | 44 | **0.896** (0.849-0.935) | 0.703 | 80% | 0.044 | 30% |
| LLM gemini-3.1-flash-lite (zero-shot) | 44 | **0.942** (0.908-0.971) | 0.760 | 90% | 0.025 | 52% |

## Grupo `blocos`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 20 | **0.671** (0.519-0.813) | 0.238 | 74% | 0.131 | 5% |
| Ordem do detector (sem ordenar) | 20 | **0.069** (0.004-0.136) | -0.143 | 4% | 0.311 | 0% |
| Ingênua (topo→base, esq.→dir.) | 20 | **0.738** (0.635-0.846) | 0.429 | 62% | 0.116 | 25% |
| XY-cut (heurística de colunas) | 20 | **0.844** (0.754-0.928) | 0.538 | 73% | 0.075 | 40% |
| LayoutLM pontual: um escore por bloco | 20 | **0.814** (0.732-0.886) | 0.600 | 37% | 0.073 | 5% |
| LayoutLM sucessor: prevê o próximo bloco | 20 | **0.901** (0.828-0.955) | 0.802 | 70% | 0.041 | 10% |
| ablacao_suc_sem_layout | 20 | **0.322** (0.201-0.450) | 0.054 | 37% | 0.240 | 5% |
| ablacao_suc_sem_posicao | 20 | **0.330** (0.128-0.536) | -0.140 | 68% | 0.274 | 10% |
| ablacao_suc_sem_texto | 20 | **0.865** (0.773-0.946) | 0.581 | 78% | 0.057 | 25% |
| ablacao_suc_sem_vies_geo | 20 | **0.877** (0.779-0.955) | 0.800 | 71% | 0.049 | 10% |
| layoutlm_sem_layout | 20 | **0.096** (-0.017-0.205) | -0.143 | 11% | 0.293 | 0% |
| LLM gemma4:31b (zero-shot) | 20 | **0.860** (0.758-0.942) | 0.576 | 83% | 0.061 | 45% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 20 | **0.849** (0.725-0.949) | 0.606 | 84% | 0.067 | 40% |
| LLM qwen3.8:27b (zero-shot) | 20 | **0.921** (0.862-0.973) | 0.790 | 86% | 0.032 | 55% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 20 | **0.908** (0.832-0.967) | 0.747 | 80% | 0.035 | 55% |
| pontual_seed1 | 20 | **0.797** (0.666-0.902) | 0.697 | 34% | 0.071 | 5% |
| pontual_seed2 | 20 | **0.809** (0.697-0.899) | 0.727 | 34% | 0.068 | 5% |
| sucessor_seed1 | 20 | **0.849** (0.749-0.930) | 0.687 | 58% | 0.059 | 10% |
| sucessor_seed2 | 20 | **0.865** (0.772-0.942) | 0.692 | 68% | 0.055 | 10% |
| LLM gemini-3.1-flash-lite (zero-shot) | 20 | **0.984** (0.964-0.998) | 0.967 | 97% | 0.008 | 70% |
| LLM gemini-3.1-flash-lite (zero-shot) | 20 | **0.975** (0.946-0.997) | 0.958 | 97% | 0.012 | 75% |
| LLM gemini-3.1-flash-lite (zero-shot) | 20 | **0.892** (0.818-0.950) | 0.703 | 79% | 0.045 | 35% |
| LLM gemini-3.1-flash-lite (zero-shot) | 20 | **0.966** (0.927-0.998) | 0.850 | 95% | 0.014 | 70% |

## Grupo `blocos_extra`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 4 | **0.957** (0.881-0.998) | 0.844 | 94% | 0.020 | 25% |
| Ordem do detector (sem ordenar) | 4 | **0.086** (0.037-0.124) | 0.016 | 7% | 0.305 | 0% |
| Ingênua (topo→base, esq.→dir.) | 4 | **0.532** (0.294-0.818) | 0.264 | 48% | 0.193 | 0% |
| XY-cut (heurística de colunas) | 4 | **0.935** (0.911-0.959) | 0.902 | 86% | 0.030 | 0% |
| LayoutLM pontual: um escore por bloco | 4 | **0.916** (0.828-0.966) | 0.784 | 40% | 0.033 | 0% |
| LayoutLM sucessor: prevê o próximo bloco | 4 | **0.952** (0.868-0.993) | 0.827 | 91% | 0.023 | 0% |
| ablacao_suc_sem_layout | 4 | **0.402** (0.086-0.725) | -0.022 | 38% | 0.209 | 0% |
| ablacao_suc_sem_posicao | 4 | **0.856** (0.667-0.972) | 0.576 | 89% | 0.053 | 0% |
| ablacao_suc_sem_texto | 4 | **0.936** (0.870-0.999) | 0.827 | 91% | 0.030 | 25% |
| ablacao_suc_sem_vies_geo | 4 | **0.946** (0.868-0.993) | 0.827 | 91% | 0.026 | 0% |
| layoutlm_sem_layout | 4 | **0.171** (0.103-0.269) | 0.087 | 3% | 0.283 | 0% |
| LLM gemma4:31b (zero-shot) | 4 | **0.560** (0.185-0.934) | 0.168 | 89% | 0.213 | 25% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 4 | **0.942** (0.884-1.000) | 0.854 | 83% | 0.020 | 50% |
| LLM qwen3.8:27b (zero-shot) | 4 | **0.662** (0.145-0.960) | -0.116 | 73% | 0.132 | 0% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 4 | **0.877** (0.758-0.966) | 0.703 | 76% | 0.055 | 0% |
| pontual_seed1 | 4 | **0.908** (0.802-0.964) | 0.749 | 39% | 0.034 | 0% |
| pontual_seed2 | 4 | **0.917** (0.822-0.968) | 0.775 | 48% | 0.032 | 0% |
| sucessor_seed1 | 4 | **0.905** (0.801-0.975) | 0.749 | 72% | 0.033 | 0% |
| sucessor_seed2 | 4 | **0.952** (0.868-0.995) | 0.827 | 91% | 0.023 | 0% |
| LLM gemini-3.1-flash-lite (zero-shot) | 4 | **0.972** (0.916-1.000) | 0.889 | 94% | 0.013 | 50% |
| LLM gemini-3.1-flash-lite (zero-shot) | 4 | **0.979** (0.939-1.000) | 0.919 | 98% | 0.010 | 50% |
| LLM gemini-3.1-flash-lite (zero-shot) | 4 | **0.953** (0.893-0.993) | 0.862 | 84% | 0.016 | 25% |
| LLM gemini-3.1-flash-lite (zero-shot) | 4 | **0.956** (0.916-0.995) | 0.899 | 91% | 0.021 | 25% |

## Grupo `incerto`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 17 | **0.480** (0.213-0.753) | -0.467 | 65% | 0.179 | 12% |
| Ordem do detector (sem ordenar) | 17 | **0.027** (-0.027-0.088) | -0.107 | 6% | 0.333 | 0% |
| Ingênua (topo→base, esq.→dir.) | 17 | **0.723** (0.617-0.839) | 0.339 | 55% | 0.118 | 18% |
| XY-cut (heurística de colunas) | 17 | **0.780** (0.678-0.881) | 0.480 | 68% | 0.103 | 18% |
| LayoutLM pontual: um escore por bloco | 17 | **0.868** (0.822-0.913) | 0.733 | 35% | 0.051 | 12% |
| LayoutLM sucessor: prevê o próximo bloco | 17 | **0.860** (0.790-0.928) | 0.600 | 59% | 0.051 | 12% |
| ablacao_suc_sem_layout | 17 | **0.218** (0.080-0.363) | -0.200 | 25% | 0.261 | 0% |
| ablacao_suc_sem_posicao | 17 | **0.219** (0.000-0.431) | -0.345 | 62% | 0.293 | 6% |
| ablacao_suc_sem_texto | 17 | **0.838** (0.713-0.927) | 0.705 | 63% | 0.060 | 18% |
| ablacao_suc_sem_vies_geo | 17 | **0.860** (0.770-0.925) | 0.600 | 61% | 0.056 | 12% |
| layoutlm_sem_layout | 17 | **0.147** (0.069-0.232) | -0.062 | 10% | 0.285 | 0% |
| LLM gemma4:31b (zero-shot) | 17 | **0.861** (0.754-0.952) | 0.512 | 77% | 0.058 | 29% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 17 | **0.851** (0.730-0.949) | 0.357 | 74% | 0.060 | 24% |
| LLM qwen3.8:27b (zero-shot) | 17 | **0.859** (0.762-0.943) | 0.545 | 78% | 0.062 | 29% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 17 | **0.849** (0.739-0.938) | 0.357 | 74% | 0.065 | 29% |
| pontual_seed1 | 17 | **0.903** (0.849-0.950) | 0.714 | 46% | 0.039 | 29% |
| pontual_seed2 | 17 | **0.882** (0.823-0.934) | 0.667 | 45% | 0.046 | 24% |
| sucessor_seed1 | 17 | **0.832** (0.768-0.891) | 0.600 | 48% | 0.067 | 12% |
| sucessor_seed2 | 17 | **0.861** (0.793-0.918) | 0.600 | 59% | 0.054 | 6% |
| LLM gemini-3.1-flash-lite (zero-shot) | 17 | **0.943** (0.859-0.995) | 0.788 | 93% | 0.027 | 71% |
| LLM gemini-3.1-flash-lite (zero-shot) | 17 | **0.961** (0.900-0.999) | 0.813 | 93% | 0.018 | 65% |
| LLM gemini-3.1-flash-lite (zero-shot) | 17 | **0.894** (0.814-0.951) | 0.819 | 80% | 0.049 | 24% |
| LLM gemini-3.1-flash-lite (zero-shot) | 17 | **0.921** (0.847-0.975) | 0.668 | 87% | 0.036 | 41% |

## Grupo `silver`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 3 | **0.798** (0.394-1.000) | 0.394 | 95% | 0.094 | 67% |
| Ordem do detector (sem ordenar) | 3 | **0.047** (-0.203-0.275) | -0.203 | 6% | 0.313 | 0% |
| Ingênua (topo→base, esq.→dir.) | 3 | **0.726** (0.555-0.987) | 0.555 | 55% | 0.121 | 0% |
| XY-cut (heurística de colunas) | 3 | **0.801** (0.555-1.000) | 0.555 | 63% | 0.086 | 33% |
| LayoutLM pontual: um escore por bloco | 3 | **0.851** (0.771-0.935) | 0.771 | 23% | 0.061 | 0% |
| LayoutLM sucessor: prevê o próximo bloco | 3 | **0.905** (0.798-0.974) | 0.798 | 56% | 0.040 | 0% |
| ablacao_suc_sem_layout | 3 | **0.187** (-0.118-0.345) | -0.118 | 18% | 0.256 | 0% |
| ablacao_suc_sem_posicao | 3 | **0.129** (-0.210-0.333) | -0.210 | 55% | 0.334 | 0% |
| ablacao_suc_sem_texto | 3 | **0.893** (0.784-1.000) | 0.784 | 69% | 0.046 | 33% |
| ablacao_suc_sem_vies_geo | 3 | **0.918** (0.779-0.988) | 0.779 | 69% | 0.034 | 0% |
| layoutlm_sem_layout | 3 | **0.121** (-0.032-0.307) | -0.032 | 12% | 0.291 | 0% |
| LLM gemma4:31b (zero-shot) | 3 | **0.695** (0.401-0.987) | 0.401 | 62% | 0.122 | 0% |
| LLM gemma4:31b (few-shot, 2 exemplos) | 3 | **0.689** (0.080-1.000) | 0.080 | 65% | 0.111 | 33% |
| LLM qwen3.8:27b (zero-shot) | 3 | **0.708** (0.213-0.977) | 0.213 | 65% | 0.108 | 0% |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 3 | **0.822** (0.737-0.965) | 0.737 | 56% | 0.069 | 0% |
| pontual_seed1 | 3 | **0.859** (0.796-0.908) | 0.796 | 16% | 0.056 | 0% |
| pontual_seed2 | 3 | **0.861** (0.782-0.906) | 0.782 | 27% | 0.058 | 0% |
| sucessor_seed1 | 3 | **0.839** (0.734-0.948) | 0.734 | 40% | 0.067 | 0% |
| sucessor_seed2 | 3 | **0.902** (0.778-0.974) | 0.778 | 57% | 0.041 | 0% |
| LLM gemini-3.1-flash-lite (zero-shot) | 3 | **0.907** (0.721-1.000) | 0.721 | 86% | 0.031 | 67% |
| LLM gemini-3.1-flash-lite (zero-shot) | 3 | **0.909** (0.739-1.000) | 0.739 | 79% | 0.034 | 33% |
| LLM gemini-3.1-flash-lite (zero-shot) | 3 | **0.855** (0.579-1.000) | 0.579 | 75% | 0.045 | 33% |
| LLM gemini-3.1-flash-lite (zero-shot) | 3 | **0.886** (0.669-1.000) | 0.669 | 78% | 0.039 | 33% |

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
| XY-cut (heurística de colunas) | LayoutLM pontual: um escore por bloco | 44 | 0.68 |
| XY-cut (heurística de colunas) | LayoutLM sucessor: prevê o próximo bloco | 44 | 0.18 |
| XY-cut (heurística de colunas) | ablacao_suc_sem_layout | 44 | 2.4e-08 |
| XY-cut (heurística de colunas) | ablacao_suc_sem_posicao | 44 | 6.8e-07 |
| XY-cut (heurística de colunas) | ablacao_suc_sem_texto | 44 | 0.21 |
| XY-cut (heurística de colunas) | ablacao_suc_sem_vies_geo | 44 | 0.22 |
| XY-cut (heurística de colunas) | layoutlm_sem_layout | 44 | 8.2e-09 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (zero-shot) | 44 | 0.84 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (few-shot, 2 exemplos) | 44 | 0.33 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (zero-shot) | 44 | 0.18 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (few-shot, 2 exemplos) | 44 | 0.077 |
| XY-cut (heurística de colunas) | pontual_seed1 | 44 | 0.3 |
| XY-cut (heurística de colunas) | pontual_seed2 | 44 | 0.4 |
| XY-cut (heurística de colunas) | sucessor_seed1 | 44 | 0.71 |
| XY-cut (heurística de colunas) | sucessor_seed2 | 44 | 0.27 |
| XY-cut (heurística de colunas) | LLM gemini-3.1-flash-lite (zero-shot) | 44 | 5.4e-06 |
| XY-cut (heurística de colunas) | LLM gemini-3.1-flash-lite (zero-shot) | 44 | 9.8e-06 |
| XY-cut (heurística de colunas) | LLM gemini-3.1-flash-lite (zero-shot) | 44 | 0.073 |
| XY-cut (heurística de colunas) | LLM gemini-3.1-flash-lite (zero-shot) | 44 | 0.0002 |

## Custo da anotação

13 min de trabalho ativo: 17 s por página, 0.5 s por bloco.
