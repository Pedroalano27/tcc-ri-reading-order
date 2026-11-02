**FEITO**

54 combinações concluídas em CPU. Âncoras aprovadas: **0,985948 / 6,045455** e **0,952424 / 8,931818** (τ / quebras por página). `ancora_ok.json` publicado.

**ARQUIVOS**

[Bancada](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/bancada_ordenadores.py), [relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordenadores_sem_caixas.md), [resultados JSON](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordenadores_sem_caixas.json) e [sinal aprovado](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordenadores_sem_caixas/ancora_ok.json).

**EVIDÊNCIA**

Menores médias de quebras por página:

| Representação | Golden v4 | V3 adicional | Silver |
|---|---|---|---|
| Linhas | Regra: 6,05 | Regra: 9,22 | Regra: 27,45 |
| Colunas | XY-cut: 5,57 | LayoutReader: 8,81 | XY-cut ± margens: 25,48 |
| Colunas com margens | LayoutReader/ingênuo: 5,30 | LayoutReader: 8,81 | XY-cut ± margens: 25,53 |

Conferidas **2.951 avaliações**. `--avaliar-pred` preservou as demais linhas e predições. O relatório contém ICs, Wilcoxon, teto, piso interno e diagnóstico de `ks` cru.

**PENDÊNCIAS**

Nenhuma da tarefa 02b. Limitações de desenvolvimento, silver e amostra pequena estão declaradas no relatório.