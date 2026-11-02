**Ainda não há vencedor comparativo:** `ls3` e `ls16` ficaram fora por ausência de `treino_ok`. O extrator foi avaliado nas **317 páginas**, em CPU.

| Sistema | F1 loc. 0,50 | F1 loc. 0,75 | F1 3 classes 0,50 | F1 9 classes 0,50 | Média ms/página |
|---|---:|---:|---:|---:|---:|
| Extrator | 0,573 | 0,399 | 0,555 | 0,480 | 4.486,8 |
| ls3 | Fora | — | — | — | — |
| ls16 | Fora | — | — | — | — |

O IC 95% do F1 em 3 classes é **[0,513; 0,595]**. Nas 11 páginas sem texto, esse F1 cai para **0,194**.

A auditoria confirmou uma página com vazamento de fonte: `pag df` no teste corresponde a `df` no treino. O relatório mantém as 317 páginas e apresenta a sensibilidade sem esse alias.

A reexecução preservou **951 arquivos de cache**, reproduziu métricas e tempos e conferiu a tabela do relatório.

- [Script retomável](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/extrator_vs_detector_ls.py)
- [Relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_vs_detector_ls_teste.md)
- [Métricas e evidências](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ls_teste_cache/metricas.json)