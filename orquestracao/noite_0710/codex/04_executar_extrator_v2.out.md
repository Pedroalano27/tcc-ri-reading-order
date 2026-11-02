**FEITO:** execução em CPU concluída, com âncoras exatas reproduzidas e duas iterações. **A v2 não cumpriu o critério de melhora.**

**EVIDÊNCIA:** na configuração final:

| Bancada | Quebras antes → depois | τ antes → depois |
|---|---:|---:|
| golden_v4 | 6,045455 → 5,931818 | 0,985948 → 0,985953 |
| golden_v3_novo | 9,222222 → 9,222222 | 0,959557 → 0,959557 |

O piso interno permaneceu igual nas duas bancadas.

**ARQUIVOS:** [relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_sem_paragrafos_v2.md) e [script validado](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/extrator_sem_paragrafos_v2.py). Incluem tabela por componente, auditoria, páginas com maiores mudanças e oito painéis conferidos.

**PENDÊNCIAS:** sem ganho confiável para aprovar a exportação final. Os caches e as unidades candidatas foram preservados.