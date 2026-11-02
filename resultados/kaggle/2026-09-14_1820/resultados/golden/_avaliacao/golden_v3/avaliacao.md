# Avaliação contra anotação humana: lote `_avaliacao/golden_v3`

Referência: ordem anotada por **Pedro alano** em 47 de 47 páginas (0 puladas). Grupos: incerto, silver.

## Todas as páginas anotadas

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 47 | **0.714** (0.594-0.822) | 0.143 | 78% | 0.109 | 21% |
| Ordem do detector (sem ordenar) | 47 | **-0.007** (-0.050-0.038) | -0.143 | 7% | 0.336 | 0% |
| Ingênua (topo→base, esq.→dir.) | 47 | **0.781** (0.722-0.842) | 0.510 | 60% | 0.098 | 32% |
| XY-cut (heurística de colunas) | 47 | **0.851** (0.796-0.901) | 0.556 | 74% | 0.068 | 23% |

## Grupo `incerto`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 26 | **0.544** (0.349-0.708) | -0.333 | 68% | 0.169 | 8% |
| Ordem do detector (sem ordenar) | 26 | **-0.024** (-0.094-0.044) | -0.222 | 7% | 0.341 | 0% |
| Ingênua (topo→base, esq.→dir.) | 26 | **0.795** (0.706-0.882) | 0.502 | 61% | 0.092 | 27% |
| XY-cut (heurística de colunas) | 26 | **0.834** (0.758-0.909) | 0.505 | 72% | 0.077 | 27% |

## Grupo `silver`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 21 | **0.925** (0.844-0.984) | 0.814 | 89% | 0.034 | 38% |
| Ordem do detector (sem ordenar) | 21 | **0.014** (-0.027-0.062) | -0.098 | 6% | 0.331 | 0% |
| Ingênua (topo→base, esq.→dir.) | 21 | **0.765** (0.683-0.852) | 0.524 | 59% | 0.107 | 38% |
| XY-cut (heurística de colunas) | 21 | **0.873** (0.805-0.936) | 0.616 | 76% | 0.056 | 19% |

## Referência vinda de `golden_v1 projetada (v3)`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 20 | **0.684** (0.478-0.849) | 0.378 | 77% | 0.118 | 20% |
| Ordem do detector (sem ordenar) | 20 | **0.021** (-0.034-0.079) | -0.088 | 5% | 0.333 | 0% |
| Ingênua (topo→base, esq.→dir.) | 20 | **0.779** (0.673-0.878) | 0.510 | 64% | 0.099 | 35% |
| XY-cut (heurística de colunas) | 20 | **0.867** (0.786-0.936) | 0.567 | 71% | 0.061 | 15% |

## Referência vinda de `golden_v2`

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 27 | **0.736** (0.579-0.872) | 0.143 | 78% | 0.101 | 22% |
| Ordem do detector (sem ordenar) | 27 | **-0.028** (-0.092-0.029) | -0.205 | 7% | 0.339 | 0% |
| Ingênua (topo→base, esq.→dir.) | 27 | **0.783** (0.704-0.856) | 0.524 | 57% | 0.098 | 30% |
| XY-cut (heurística de colunas) | 27 | **0.840** (0.761-0.905) | 0.505 | 76% | 0.073 | 30% |

## A referência automática se sustenta?

- Grupo `incerto`: o fluxo do PDF concorda com o humano com tau médio **0.544** (pior caso p10 -0.333, 8% das páginas idênticas).
- Grupo `silver`: o fluxo do PDF concorda com o humano com tau médio **0.925** (pior caso p10 0.814, 38% das páginas idênticas).

## Wilcoxon pareado contra a XY-cut

| A | B | n | p-valor |
|---|---|---:|---:|
| XY-cut (heurística de colunas) | Fluxo do PDF (referência silver) | 47 | 0.23 |
| XY-cut (heurística de colunas) | Ordem do detector (sem ordenar) | 47 | 2.4e-09 |
| XY-cut (heurística de colunas) | Ingênua (topo→base, esq.→dir.) | 47 | 0.037 |

## Custo da anotação

45 min de trabalho ativo: 57 s por página, 2.2 s por bloco.
