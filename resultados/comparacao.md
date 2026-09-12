# Resultados da comparacao

Referencia: ordem `stream` (rotulo silver). Teste: 95 paginas de 3 veiculos nunca vistos no treino: official_diary_ce, official_diary_ma, official_diary_rj.

Setas: tau e BLEU quanto maior melhor; ARD quanto menor melhor. tau p10 = percentil 10, o desempenho nas 10% piores paginas.

### Todas as paginas de teste

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD | ARD norm. | BLEU | Acerto exato | Latencia (ms/pag.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 95 | **-0.005** (-0.056-0.043) | -0.200 | 4.8% | 16.29 | 0.330 | 94.2 | 1.1% | 0.001 |
| Ingênua (topo→base, esq.→dir.) | 95 | **0.753** (0.704-0.804) | 0.347 | 52.5% | 5.84 | 0.106 | 96.9 | 1.1% | 0.015 |
| XY-cut (heurística de colunas) | 95 | **0.837** (0.788-0.880) | 0.496 | 64.2% | 3.46 | 0.067 | 96.8 | 18.9% | 0.141 |
| BiLSTM: só texto | 95 | **0.066** (0.024-0.111) | -0.195 | 5.5% | 16.21 | 0.309 | 94.2 | 1.1% | 6.8 |
| BiLSTM: só geometria | 95 | **0.731** (0.691-0.769) | 0.459 | 27.1% | 5.85 | 0.105 | 94.7 | 7.4% | 7.1 |
| BiLSTM: texto + geometria | 95 | **0.628** (0.588-0.666) | 0.334 | 15.5% | 7.09 | 0.136 | 94.3 | 2.1% | 8.3 |
| LayoutLM sem layout (ablação) | 95 | **0.122** (0.084-0.160) | -0.099 | 5.5% | 15.64 | 0.294 | 94.1 | 0.0% | 13.8 |
| LayoutLM: texto + layout 2D | 95 | **0.671** (0.636-0.707) | 0.345 | 13.4% | 6.25 | 0.123 | 94.6 | 3.2% | 18.0 |

### Subconjunto avaliado pela LLM

Subconjunto de 15 paginas comum aos metodos avaliados em parte do teste (a LLM llava:7b rodou so em paginas pequenas). Todos os metodos nas MESMAS paginas.

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD | ARD norm. | BLEU | Acerto exato | Latencia (ms/pag.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 15 | **0.040** (-0.173-0.257) | -0.410 | 11.4% | 4.82 | 0.309 | 98.0 | 6.7% | 0.001 |
| Ingênua (topo→base, esq.→dir.) | 15 | **0.817** (0.724-0.905) | 0.562 | 69.0% | 1.07 | 0.073 | 99.4 | 6.7% | 0.006 |
| XY-cut (heurística de colunas) | 15 | **0.680** (0.492-0.843) | 0.429 | 63.3% | 1.74 | 0.126 | 98.5 | 26.7% | 0.043 |
| BiLSTM: só texto | 15 | **0.174** (0.029-0.340) | -0.209 | 15.8% | 4.51 | 0.272 | 98.0 | 6.7% | 2.6 |
| BiLSTM: só geometria | 15 | **0.732** (0.630-0.827) | 0.419 | 39.8% | 1.64 | 0.104 | 97.2 | 6.7% | 2.6 |
| BiLSTM: texto + geometria | 15 | **0.667** (0.569-0.765) | 0.381 | 28.7% | 1.99 | 0.125 | 97.1 | 6.7% | 3.3 |
| LayoutLM sem layout (ablação) | 15 | **0.233** (0.120-0.344) | -0.099 | 8.5% | 4.09 | 0.261 | 96.9 | 0.0% | 12.5 |
| LayoutLM: texto + layout 2D | 15 | **0.658** (0.549-0.768) | 0.333 | 19.5% | 2.08 | 0.131 | 98.0 | 6.7% | 17.6 |
| LLM llava:7b (zero-shot) | 15 | **0.099** (-0.027-0.224) | -0.333 | 8.5% | 4.64 | 0.306 | 96.8 | 0.0% | 8,414.7 |

Permutacoes validas devolvidas por LLM llava:7b (zero-shot): **80%** (as invalidas foram reparadas antes de medir).

### Tau medio por numero de colunas da pagina

| Metodo | 1 coluna | 2 colunas | 3+ colunas |
|---|---:|---:|---:|
| Ordem do detector (sem ordenar) | -0.026 (n=39) | 0.021 (n=39) | -0.017 (n=17) |
| Ingênua (topo→base, esq.→dir.) | 0.793 (n=39) | 0.731 (n=39) | 0.709 (n=17) |
| XY-cut (heurística de colunas) | 0.896 (n=39) | 0.821 (n=39) | 0.737 (n=17) |
| BiLSTM: só texto | 0.086 (n=39) | 0.057 (n=39) | 0.038 (n=17) |
| BiLSTM: só geometria | 0.713 (n=39) | 0.758 (n=39) | 0.709 (n=17) |
| BiLSTM: texto + geometria | 0.610 (n=39) | 0.653 (n=39) | 0.613 (n=17) |
| LayoutLM sem layout (ablação) | 0.168 (n=39) | 0.100 (n=39) | 0.068 (n=17) |
| LayoutLM: texto + layout 2D | 0.627 (n=39) | 0.725 (n=39) | 0.649 (n=17) |

### Testes de Wilcoxon pareados (tau por pagina)

| A | B | n | media A | media B | p-valor |
|---|---|---:|---:|---:|---:|
| LayoutLM: texto + layout 2D | Ordem do detector (sem ordenar) | 95 | 0.671 | -0.005 | 8.4e-17 |
| LayoutLM: texto + layout 2D | Ingênua (topo→base, esq.→dir.) | 95 | 0.671 | 0.753 | 0.013 |
| LayoutLM: texto + layout 2D | XY-cut (heurística de colunas) | 95 | 0.671 | 0.837 | 2.6e-11 |
| LayoutLM: texto + layout 2D | BiLSTM: só texto | 95 | 0.671 | 0.066 | 2.6e-16 |
| LayoutLM: texto + layout 2D | BiLSTM: só geometria | 95 | 0.671 | 0.731 | 8.2e-09 |
| LayoutLM: texto + layout 2D | BiLSTM: texto + geometria | 95 | 0.671 | 0.628 | 4.6e-05 |
| LayoutLM: texto + layout 2D | LayoutLM sem layout (ablação) | 95 | 0.671 | 0.122 | 2.6e-16 |
| LayoutLM: texto + layout 2D | LLM llava:7b (zero-shot) | 15 | 0.658 | 0.099 | 6.1e-05 |
| XY-cut (heurística de colunas) | LLM llava:7b (zero-shot) | 15 | 0.680 | 0.099 | 0.0012 |
