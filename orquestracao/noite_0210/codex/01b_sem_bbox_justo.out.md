**Veredito:** a política de margens recupera **90,1% do ganho original** em τ de regiões. A projeção também contribui na ablação, mas não demonstra superioridade sobre a comparação justa: Δτ de palavras = **0,008**, IC 95% **[−0,056; 0,040]**, permutação por veículo **p = 0,590**.

| Método | τ palavras — principal | τ regiões |
|---|---:|---:|
| XY-cut ouro, pura | 0,853 | 0,825 |
| XY-cut ouro + margens geométricas | 0,972 | 0,908 |
| XY-cut ouro + classes humanas | 0,979 | 0,918 |
| XY-cut automática, pura | 0,819 | 0,798 |
| XY-cut automática + margens geométricas | 0,952 | 0,899 |
| XY-cut automática + classes previstas | 0,940 | 0,889 |
| Ingênua ouro, pura | 0,756 | 0,713 |
| Ingênua ouro + margens | 0,755 | 0,707 |
| Ingênua automática, pura | 0,750 | 0,726 |
| Ingênua automática + margens | 0,749 | 0,715 |
| Plano original LOPO | 0,946 | 0,917 |
| Plano original LOVO | 0,947 | 0,917 |
| Plano LOVO selecionado por palavras | 0,980 | 0,937 |

Recomendo retirar a alegação de superioridade geral e priorizar a validação da política no pipeline de regiões. O relatório responde aos nove itens, apresenta ablação, estratos, testes e as **18 páginas com fragmentação**.

Executado do zero e conferido: **nenhuma divergência** na reprodução do LOPO ou da grade original.

Arquivos: [script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox_justo.py) · [relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox_justo.md).