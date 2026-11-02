**FEITO** — Executei e validei as três etapas em CPU. O híbrido **não mostrou ganho consistente sobre a regra**; encerrei a demonstração sem ampliar o treino.

**ARQUIVOS** — [Relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/corretor_de_transicoes.md), com resumo de cinco linhas, diagnóstico por transição, sucessor, IC por veículo e Wilcoxon. [Script validado](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/corretor_de_transicoes.py), com checkpoints e caches retomáveis.

**EVIDÊNCIA** — Âncora reproduzida: τ **0,985948**, **6,045455** quebras/página. Autoteste e conferência passaram. Treino: 24 páginas, três épocas; limiar escolhido em RN: 0,80.

| Bancada | n | Quebras: regra → híbrido |
|---|---:|---:|
| golden_v4 | 44 | 6,045 → 5,909 |
| golden_v3 novo | 27 | 9,222 → 9,444 |
| Teste silver | 68 | 29,485 → 29,471 |

τ caiu nas três bancadas. Os IC das diferenças de quebras incluem zero; no v3 novo, a queda de τ teve p=0,027670 por veículo.

**PENDÊNCIAS** — Nenhuma desta execução. O resultado é exploratório: treino pequeno e referência silver automática; não exclui ganhos de outra configuração.