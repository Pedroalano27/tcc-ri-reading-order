O v4 melhora o F1 de localização em **19,0 pontos percentuais** sobre o extrator atual, mas **não supera o detector puro** ajustado por fonte.

Resultados nas 317 páginas; CV deixa uma fonte inteira de fora:

| Sistema | Localização ≥0,50 | Localização ≥0,75 | 3 classes ≥0,50 | 16 classes ≥0,50 | CPU ms/página |
|---|---:|---:|---:|---:|---:|
| Extrator atual | 0,573 | 0,399 | 0,555 | 0,422 | 4486,8 |
| ls3 puro | 0,780 | 0,731 | 0,769 | — | 711,2 |
| ls16 puro | 0,753 | 0,705 | 0,743 | 0,622 | 277,7 |
| Detector puro com CV | **0,799** | **0,753** | **0,787** | — | 711,2 |
| v4 padrão | 0,757 | 0,571 | 0,742 | 0,582 | 3956,4 |
| v4 com CV | 0,763 | 0,582 | 0,751 | 0,437 | 3678,8 |

Os valores finos do extrator e do v4 incluem classes projetadas; os tempos reutilizam custos dos caches. ICs, testes pareados e ablações estão no relatório.

Com RT-DETR L, o v4 padrão alcançou **0,768**. No Diamond, obteve **0,750**, contra **0,851** do antigo. Nas caixas casadas com transcrição humana, **67,1%** dos textos foram idênticos.

A execução final do zero passou, e o relatório foi conferido contra a saída e o JSON.

- [Relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_v4.md)
- [Script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/extrator_v4.py)
- [Resultados verificáveis](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_v4_cache/resultados.json)
- [Conferência](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_v4_cache/conferencia.json)