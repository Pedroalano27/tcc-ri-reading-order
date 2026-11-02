Recomendo **XY-cut + margens geométricas, separando as margens antes de recalcular a XY-cut no corpo**, como método adicional do TCC.

Resultados sem → com essa variante:

| Conjunto | n | τ Kendall | Sucessor correto | ARD norm. | Δτ [IC 95%] |
|---|---:|---:|---:|---:|---:|
| Teste silver | 89 | 0,891 → 0,928 | 78,4% → 83,2% | 0,045 → 0,029 | 0,037 [0,013; 0,064] |
| golden_v3 | 47 | 0,851 → 0,908 | 74,0% → 76,8% | 0,068 → 0,041 | 0,057 [0,020; 0,102] |
| golden_v4 | 44 | 0,825 → 0,908 | 71,5% → 82,0% | 0,083 → 0,034 | 0,083 [0,004; 0,163] |

Há ressalvas: o recorte piorou **6, 4 e 7 páginas**, respectivamente; topo de 5% mudou o sinal do ganho no teste. O pós-processamento isolado caiu para **τ 0,799 no v4**. Esse conjunto foi usado no desenvolvimento e tem viés de ancoragem das caixas; classes humanas são diagnóstico de oráculo.

Passaram **18 testes novos e 144 testes na suíte completa**. A execução final do zero reproduziu os resultados, e a conferência em outro processo validou hashes, métricas e relatório integral.

Criei apenas os quatro arquivos pedidos:

- [Módulo](C:/Users/pedro/dev/tcc-ri-reading-order/src/eval/politica_margens.py)
- [Testes](C:/Users/pedro/dev/tcc-ri-reading-order/tests/test_politica_margens.py)
- [Script de avaliação](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/politica_margens_avaliacao.py)
- [Relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/politica_margens.md), com ingênua, LayoutLM, variantes, Wilcoxon, quedas, sensibilidade e diff proposto.