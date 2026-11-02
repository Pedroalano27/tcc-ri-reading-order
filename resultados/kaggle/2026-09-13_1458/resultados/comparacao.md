# Resultados da comparacao

Referencia: ordem `stream` (rotulo silver). Teste: 89 paginas de 3 veiculos nunca vistos no treino: official_diary_ce, official_diary_ma, official_diary_rj.

Setas: tau e BLEU quanto maior melhor; ARD quanto menor melhor. tau p10 = percentil 10, o desempenho nas 10% piores paginas.

### Todas as paginas de teste

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD | ARD norm. | BLEU | Acerto exato | Latencia (ms/pag.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 89 | **-0.020** (-0.070-0.027) | -0.205 | 6.3% | 10.31 | 0.335 | 96.9 | 1.1% | 0.008 |
| Ingênua (topo→base, esq.→dir.) | 89 | **0.790** (0.734-0.844) | 0.445 | 69.0% | 4.44 | 0.092 | 98.8 | 46.1% | 0.050 |
| XY-cut (heurística de colunas) | 89 | **0.891** (0.846-0.930) | 0.688 | 78.4% | 1.54 | 0.045 | 99.2 | 29.2% | 0.333 |
| BiLSTM: só texto | 89 | **0.102** (0.061-0.145) | -0.150 | 5.2% | 9.83 | 0.300 | 97.0 | 0.0% | 6.5 |
| BiLSTM: só geometria | 89 | **0.801** (0.762-0.836) | 0.539 | 31.4% | 2.56 | 0.080 | 97.5 | 5.6% | 5.5 |
| BiLSTM: texto + geometria | 89 | **0.711** (0.674-0.746) | 0.451 | 18.5% | 3.45 | 0.109 | 97.3 | 2.2% | 5.9 |
| LayoutLM sem layout (ablação) | 89 | **0.122** (0.071-0.173) | -0.150 | 8.8% | 9.60 | 0.294 | 97.0 | 2.2% | 13.4 |
| LayoutLM pontual: um escore por bloco | 89 | **0.800** (0.762-0.836) | 0.551 | 29.8% | 2.57 | 0.080 | 97.6 | 5.6% | 12.4 |
| LayoutLM sucessor: prevê o próximo bloco | 89 | **0.878** (0.830-0.915) | 0.666 | 71.3% | 1.96 | 0.052 | 98.9 | 21.3% | 18.5 |
| LayoutLM sucessor (decodificação em feixe) | 89 | **0.754** (0.688-0.815) | 0.281 | 71.3% | 4.30 | 0.096 | 98.9 | 15.7% | 20.8 |
| LLM gemma4:31b (zero-shot) | 89 | **0.817** (0.761-0.868) | 0.415 | 73.2% | 3.68 | 0.075 | 99.0 | 28.1% | 25,355.8 |
| LLM gemma4:31b (few-shot, 2 exemplos) | 89 | **0.835** (0.782-0.883) | 0.419 | 70.9% | 3.17 | 0.066 | 98.9 | 25.8% | 26,657.7 |
| LLM qwen3.6:35b (zero-shot) | 89 | **0.499** (0.430-0.569) | -0.010 | 34.4% | 6.52 | 0.182 | 97.9 | 6.7% | 10,761.7 |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 89 | **0.592** (0.530-0.655) | 0.097 | 36.8% | 6.08 | 0.151 | 97.8 | 5.6% | 4,904.8 |
| LLM qwen3.8:27b (zero-shot) | 89 | **0.833** (0.778-0.884) | 0.356 | 72.5% | 2.92 | 0.068 | 99.0 | 28.1% | 18,384.5 |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 89 | **0.827** (0.777-0.873) | 0.354 | 72.5% | 3.35 | 0.070 | 99.1 | 27.0% | 18,524.4 |
| ablacao_suc_sem_layout | 89 | **0.216** (0.160-0.281) | -0.075 | 30.6% | 9.29 | 0.266 | 97.5 | 4.5% | 19.2 |
| ablacao_suc_sem_posicao | 89 | **0.374** (0.290-0.456) | -0.178 | 65.5% | 9.03 | 0.246 | 98.7 | 13.5% | 19.2 |
| ablacao_suc_sem_vies_geo | 89 | **0.853** (0.795-0.900) | 0.556 | 67.1% | 1.93 | 0.057 | 98.9 | 20.2% | 18.1 |
| pontual_seed1 | 89 | **0.820** (0.781-0.855) | 0.564 | 31.6% | 2.20 | 0.072 | 97.7 | 6.7% | 15.3 |
| pontual_seed2 | 89 | **0.814** (0.776-0.849) | 0.619 | 30.0% | 2.26 | 0.074 | 97.7 | 2.2% | 13.1 |
| suc_limiar_00 | 89 | **0.756** (0.691-0.813) | 0.208 | 72.9% | 4.48 | 0.103 | 99.0 | 19.1% | 20.5 |
| suc_limiar_03 | 89 | **0.855** (0.803-0.898) | 0.600 | 71.6% | 2.12 | 0.062 | 98.9 | 19.1% | 19.1 |
| suc_limiar_07 | 89 | **0.873** (0.825-0.910) | 0.677 | 66.6% | 2.10 | 0.054 | 98.8 | 18.0% | 20.2 |
| suc_limiar_09 | 89 | **0.860** (0.820-0.893) | 0.719 | 55.8% | 2.18 | 0.058 | 98.4 | 13.5% | 19.3 |
| sucessor_seed1 | 89 | **0.849** (0.810-0.885) | 0.632 | 57.3% | 2.16 | 0.061 | 98.5 | 9.0% | 18.5 |
| sucessor_seed2 | 89 | **0.894** (0.851-0.931) | 0.725 | 73.0% | 1.77 | 0.044 | 99.0 | 29.2% | 18.0 |

Permutacoes validas devolvidas por LLM gemma4:31b (zero-shot): **87%** (as invalidas foram reparadas antes de medir).

Permutacoes validas devolvidas por LLM gemma4:31b (few-shot, 2 exemplos): **76%** (as invalidas foram reparadas antes de medir).

Permutacoes validas devolvidas por LLM qwen3.6:35b (zero-shot): **30%** (as invalidas foram reparadas antes de medir).

Permutacoes validas devolvidas por LLM qwen3.6:35b (few-shot, 2 exemplos): **37%** (as invalidas foram reparadas antes de medir).

Permutacoes validas devolvidas por LLM qwen3.8:27b (zero-shot): **80%** (as invalidas foram reparadas antes de medir).

Permutacoes validas devolvidas por LLM qwen3.8:27b (few-shot, 2 exemplos): **70%** (as invalidas foram reparadas antes de medir).

### Tau medio por numero de colunas da pagina

| Metodo | 1 coluna | 2 colunas | 3+ colunas |
|---|---:|---:|---:|
| Ordem do detector (sem ordenar) | -0.114 (n=34) | 0.038 (n=49) | 0.036 (n=6) |
| Ingênua (topo→base, esq.→dir.) | 0.895 (n=34) | 0.764 (n=49) | 0.412 (n=6) |
| XY-cut (heurística de colunas) | 0.896 (n=34) | 0.882 (n=49) | 0.930 (n=6) |
| BiLSTM: só texto | 0.141 (n=34) | 0.096 (n=49) | -0.073 (n=6) |
| BiLSTM: só geometria | 0.823 (n=34) | 0.784 (n=49) | 0.815 (n=6) |
| BiLSTM: texto + geometria | 0.727 (n=34) | 0.700 (n=49) | 0.720 (n=6) |
| LayoutLM sem layout (ablação) | 0.169 (n=34) | 0.099 (n=49) | 0.045 (n=6) |
| LayoutLM pontual: um escore por bloco | 0.806 (n=34) | 0.790 (n=49) | 0.846 (n=6) |
| LayoutLM sucessor: prevê o próximo bloco | 0.865 (n=34) | 0.890 (n=49) | 0.851 (n=6) |
| LayoutLM sucessor (decodificação em feixe) | 0.759 (n=34) | 0.796 (n=49) | 0.389 (n=6) |
| LLM gemma4:31b (zero-shot) | 0.896 (n=34) | 0.827 (n=49) | 0.288 (n=6) |
| LLM gemma4:31b (few-shot, 2 exemplos) | 0.887 (n=34) | 0.848 (n=49) | 0.429 (n=6) |
| LLM qwen3.6:35b (zero-shot) | 0.642 (n=34) | 0.433 (n=49) | 0.226 (n=6) |
| LLM qwen3.6:35b (few-shot, 2 exemplos) | 0.679 (n=34) | 0.560 (n=49) | 0.353 (n=6) |
| LLM qwen3.8:27b (zero-shot) | 0.870 (n=34) | 0.823 (n=49) | 0.708 (n=6) |
| LLM qwen3.8:27b (few-shot, 2 exemplos) | 0.877 (n=34) | 0.825 (n=49) | 0.571 (n=6) |
| ablacao_suc_sem_layout | 0.344 (n=34) | 0.160 (n=49) | -0.053 (n=6) |
| ablacao_suc_sem_posicao | 0.455 (n=34) | 0.389 (n=49) | -0.207 (n=6) |
| ablacao_suc_sem_vies_geo | 0.868 (n=34) | 0.845 (n=49) | 0.834 (n=6) |
| pontual_seed1 | 0.804 (n=34) | 0.824 (n=49) | 0.874 (n=6) |
| pontual_seed2 | 0.779 (n=34) | 0.835 (n=49) | 0.843 (n=6) |
| suc_limiar_00 | 0.759 (n=34) | 0.786 (n=49) | 0.499 (n=6) |
| suc_limiar_03 | 0.821 (n=34) | 0.878 (n=49) | 0.860 (n=6) |
| suc_limiar_07 | 0.862 (n=34) | 0.885 (n=49) | 0.827 (n=6) |
| suc_limiar_09 | 0.847 (n=34) | 0.876 (n=49) | 0.796 (n=6) |
| sucessor_seed1 | 0.837 (n=34) | 0.864 (n=49) | 0.792 (n=6) |
| sucessor_seed2 | 0.885 (n=34) | 0.907 (n=49) | 0.846 (n=6) |

### Testes de Wilcoxon pareados (tau por pagina)

| A | B | n | media A | media B | p-valor |
|---|---|---:|---:|---:|---:|
| LayoutLM pontual: um escore por bloco | Ordem do detector (sem ordenar) | 89 | 0.800 | -0.020 | 6.1e-16 |
| LayoutLM pontual: um escore por bloco | Ingênua (topo→base, esq.→dir.) | 89 | 0.800 | 0.790 | 0.75 |
| LayoutLM pontual: um escore por bloco | XY-cut (heurística de colunas) | 89 | 0.800 | 0.891 | 4.5e-10 |
| LayoutLM pontual: um escore por bloco | BiLSTM: só texto | 89 | 0.800 | 0.102 | 8e-16 |
| LayoutLM pontual: um escore por bloco | BiLSTM: só geometria | 89 | 0.800 | 0.801 | 0.94 |
| LayoutLM pontual: um escore por bloco | BiLSTM: texto + geometria | 89 | 0.800 | 0.711 | 5.8e-08 |
| LayoutLM pontual: um escore por bloco | LayoutLM sem layout (ablação) | 89 | 0.800 | 0.122 | 3.4e-15 |
| LayoutLM pontual: um escore por bloco | LayoutLM sucessor: prevê o próximo bloco | 89 | 0.800 | 0.878 | 2.4e-07 |
| LayoutLM pontual: um escore por bloco | LayoutLM sucessor (decodificação em feixe) | 89 | 0.800 | 0.754 | 0.19 |
| LayoutLM pontual: um escore por bloco | LLM gemma4:31b (zero-shot) | 89 | 0.800 | 0.817 | 0.011 |
| LayoutLM pontual: um escore por bloco | LLM gemma4:31b (few-shot, 2 exemplos) | 89 | 0.800 | 0.835 | 0.0066 |
| LayoutLM pontual: um escore por bloco | LLM qwen3.6:35b (zero-shot) | 89 | 0.800 | 0.499 | 3.4e-10 |
| LayoutLM pontual: um escore por bloco | LLM qwen3.6:35b (few-shot, 2 exemplos) | 89 | 0.800 | 0.592 | 1.5e-09 |
| LayoutLM pontual: um escore por bloco | LLM qwen3.8:27b (zero-shot) | 89 | 0.800 | 0.833 | 0.00079 |
| LayoutLM pontual: um escore por bloco | LLM qwen3.8:27b (few-shot, 2 exemplos) | 89 | 0.800 | 0.827 | 0.011 |
| LayoutLM pontual: um escore por bloco | ablacao_suc_sem_layout | 89 | 0.800 | 0.216 | 7e-15 |
| LayoutLM pontual: um escore por bloco | ablacao_suc_sem_posicao | 89 | 0.800 | 0.374 | 1.2e-11 |
| LayoutLM pontual: um escore por bloco | ablacao_suc_sem_vies_geo | 89 | 0.800 | 0.853 | 2.3e-07 |
| LayoutLM pontual: um escore por bloco | pontual_seed1 | 89 | 0.800 | 0.820 | 0.0004 |
| LayoutLM pontual: um escore por bloco | pontual_seed2 | 89 | 0.800 | 0.814 | 0.27 |
| LayoutLM pontual: um escore por bloco | suc_limiar_00 | 89 | 0.800 | 0.756 | 0.64 |
| LayoutLM pontual: um escore por bloco | suc_limiar_03 | 89 | 0.800 | 0.855 | 0.00017 |
| LayoutLM pontual: um escore por bloco | suc_limiar_07 | 89 | 0.800 | 0.873 | 1.6e-07 |
| LayoutLM pontual: um escore por bloco | suc_limiar_09 | 89 | 0.800 | 0.860 | 0.00031 |
| LayoutLM pontual: um escore por bloco | sucessor_seed1 | 89 | 0.800 | 0.849 | 0.0056 |
| LayoutLM pontual: um escore por bloco | sucessor_seed2 | 89 | 0.800 | 0.894 | 7.4e-09 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (zero-shot) | 89 | 0.891 | 0.817 | 0.011 |
| XY-cut (heurística de colunas) | LLM gemma4:31b (few-shot, 2 exemplos) | 89 | 0.891 | 0.835 | 0.036 |
| XY-cut (heurística de colunas) | LLM qwen3.6:35b (zero-shot) | 89 | 0.891 | 0.499 | 3.3e-13 |
| XY-cut (heurística de colunas) | LLM qwen3.6:35b (few-shot, 2 exemplos) | 89 | 0.891 | 0.592 | 3.5e-14 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (zero-shot) | 89 | 0.891 | 0.833 | 0.081 |
| XY-cut (heurística de colunas) | LLM qwen3.8:27b (few-shot, 2 exemplos) | 89 | 0.891 | 0.827 | 0.015 |
