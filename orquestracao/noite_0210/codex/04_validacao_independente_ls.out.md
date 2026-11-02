**O ganho não se confirma contra a XY-cut com as mesmas margens.** Na saída real de palavras, Δτ = −0,010, com IC 95% [−0,050; 0,018].

Tabela principal: 123 páginas com palavras; três páginas vazias foram contabilizadas separadamente.

| Método | τ (IC 95% por veículo) | Sucessor | ARD norm. | Fragmentação |
|---|---:|---:|---:|---:|
| Ingênua no ouro | 0,893 [0,808; 0,956] | 99,2% | 0,054 | 0,0% |
| XY-cut no ouro | 0,905 [0,822; 0,967] | 99,3% | 0,047 | 0,0% |
| XY-cut ouro + margens | **0,976 [0,954; 0,993]** | **99,3%** | **0,012** | **0,0%** |
| Sem bbox fina, átomos humanos | 0,966 [0,928; 0,991] | 98,8% | 0,017 | 4,1% |
| Sem bbox fina, ls3 CPU | 0,954 [0,915; 0,982] | 98,1% | 0,022 | 5,1% |

O ls3 agregado inclui treino. No teste separado, alcançou τ = 0,975 em 21 páginas com palavras, de apenas cinco veículos. A melhoria multicoluna permanece exploratória, com IC incluindo zero. A ausência das sugestões originais impediu identificar correções humanas comprovadas.

Execução do zero reproduzida; relatório, agregados e testes conferidos.

- [Script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox_validacao_ls.py)
- [Relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox_validacao_ls.md)
- [Resultados e auditoria](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_ls/validacao_sem_bbox/resultado.json)