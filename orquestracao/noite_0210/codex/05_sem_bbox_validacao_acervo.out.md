O ganho médio de τ aparece nas páginas humanas novas, sobretudo em multicoluna detectada, mas **não comprova superioridade geral**: Wilcoxon p = 0,289 e continuidade pior. Nas 27 novas, o sucessor cai de 99,1% para 98,1%, com 3,1% de regiões fragmentadas.

Régua principal: **τ da sequência real de palavras**.

| Conjunto | n | Congelado | XY-cut + margens | XY-cut pura | Ingênua | Sem margens¹ |
|---|---:|---:|---:|---:|---:|---:|
| Humanas novas | 27 | 0,971 | 0,918 | 0,913 | 0,800 | 0,948 |
| Humanas repetidas | 20 | 0,983 | 0,950 | 0,845 | 0,771 | 0,940 |
| Silver novas | 86 | 0,968 | 0,948 | 0,942 | 0,780 | 0,961 |
| Silver completo | 89 | 0,965 | 0,939 | 0,934 | 0,771 | 0,958 |

¹ Sensibilidade. Todos os veículos já apareciam no `golden_v4`; o silver favorece a XY-cut.

A execução do zero reproduziu os resultados; relatório e 95 hashes conferidos. O relatório inclui IC agrupados por veículo, estratos e oito perdas inspecionadas.

- [Relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox_validacao_acervo.md)
- [Script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox_validacao_acervo.py)
- [Resultados completos e caches](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox_cache/validacao_acervo.json)