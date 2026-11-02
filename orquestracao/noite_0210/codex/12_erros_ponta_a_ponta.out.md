O **P2 com ls3 reduz a média observada de quebras**: 55,1% contra P1 e 26,5% contra P1m. Porém, o ganho sobre P1m permanece inconclusivo: IC 95% de −5,77 a +0,18 quebras/página.

Pela definição operacional, **19,7% das quebras do P1 estão associadas às caixas**. A hipótese de que elas causam a maioria dos erros não foi sustentada nesta régua.

Médias nas 71 páginas:

| Pipeline | Quebras/pág. ↓ | τ ↑ | Sucessor linhas ↑ | Fidelidade 6 ↑ | Fidelidade 12 ↑ | Fidelidade 24 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| P0 — ingênua | 85,46 | 0,759 | 50,8% | 73,7% | 56,2% | 46,6% |
| P1 — caixas + XY-cut | 16,14 | 0,830 | 85,7% | 93,0% | 87,5% | 79,8% |
| P1m — com margens | 9,87 | 0,947 | 91,2% | 95,1% | 92,3% | 88,5% |
| P2 — ls3 | **7,25** | 0,976 | **92,1%** | **95,9%** | **94,1%** | **91,8%** |
| P2d — Docling | 10,99 | 0,977 | 89,9% | 94,2% | 92,2% | 90,1% |

Reexecução do zero e conferência passaram. A prévia teve **1.276 verificações sem divergência numérica**, mas suas conclusões contradiziam os números. O relatório documenta isso, as demais contagens e os vieses.

Arquivos: [relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/erros_ponta_a_ponta.md), [script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/erros_ponta_a_ponta.py), [resultados completos](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/erros_ponta_a_ponta.json).