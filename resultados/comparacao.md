# Resultados da comparacao

Referencia: ordem `stream` (rotulo silver). Teste: 89 paginas de 3 veiculos nunca vistos no treino: official_diary_ce, official_diary_ma, official_diary_rj.

Setas: tau e BLEU quanto maior melhor; ARD quanto menor melhor. tau p10 = percentil 10, o desempenho nas 10% piores paginas.

### Todas as paginas de teste

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD | ARD norm. | BLEU | Acerto exato | Latencia (ms/pag.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 89 | **-0.020** (-0.070-0.027) | -0.205 | 6.3% | 10.31 | 0.335 | 96.9 | 1.1% | 0.008 |
| Ingênua (topo→base, esq.→dir.) | 89 | **0.790** (0.734-0.844) | 0.445 | 69.0% | 4.44 | 0.092 | 98.8 | 46.1% | 0.050 |
| XY-cut (heurística de colunas) | 89 | **0.891** (0.846-0.930) | 0.688 | 78.4% | 1.54 | 0.045 | 99.2 | 29.2% | 0.333 |

### Tau medio por numero de colunas da pagina

| Metodo | 1 coluna | 2 colunas | 3+ colunas |
|---|---:|---:|---:|
| Ordem do detector (sem ordenar) | -0.114 (n=34) | 0.038 (n=49) | 0.036 (n=6) |
| Ingênua (topo→base, esq.→dir.) | 0.895 (n=34) | 0.764 (n=49) | 0.412 (n=6) |
| XY-cut (heurística de colunas) | 0.896 (n=34) | 0.882 (n=49) | 0.930 (n=6) |

### Testes de Wilcoxon pareados (tau por pagina)

| A | B | n | media A | media B | p-valor |
|---|---|---:|---:|---:|---:|
