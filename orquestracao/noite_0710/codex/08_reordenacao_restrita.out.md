Executei e validei o [script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/reordenacao_restrita.py) em CPU, nas 160 páginas, com âncoras reproduzidas e caches retomáveis.

Quebras por página:

| Bancada | Regra | Reordenação | Oráculo |
|---|---:|---:|---:|
| Golden v4 | 6,045 | 5,182 | 4,909 |
| Golden v3 externo | 9,222 | 7,778 | 6,963 |
| Silver externo | 27,449 | 26,449 | 24,831 |

**Melhorou a média nas três bancadas**, com τ praticamente preservado. O oráculo recuperou **42,59%** das quebras na coluna no v4. O ganho externo continua exploratório: Wilcoxon por veículo não o confirma.

O [relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/reordenacao_restrita.md) contém diagnóstico, exemplos, alertas, reparos, regressões e IC. A classe “candidato em outra coluna” teve zero casos observados.