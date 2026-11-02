# Híbrido por densidade: LayoutReader pronto nas páginas leves, regra de colunas nas densas

Gerado por `orquestracao/analises/hibrido_regra_layoutreader.py` a partir das medições por página de
`resultados/ordenadores_sem_caixas.json` (representação `linhas`). Nenhum modelo foi rodado de novo.

Limiar escolhido **só no golden_v4**: usar o LayoutReader quando a página tem até **67 unidades**
(linhas, tabelas e imagens); acima disso, a regra de colunas. O golden_v3 novo e o teste silver não
participaram da escolha.

| Bancada | n | Páginas no LayoutReader | Regra: τ / quebras | LayoutReader: τ / quebras | Híbrido: τ / quebras | Δ quebras híbrido − regra [IC 95% por veículo] | Híbrido melhor / igual / pior |
|---|---:|---:|---:|---:|---:|---:|---:|
| golden_v4 | 44 | 25 | 0,986 / 6,05 | 0,913 / 18,39 | 0,980 / 5,14 | -0,91 [-1,78; -0,10] | 16 / 24 / 4 |
| golden_v3_novo | 27 | 13 | 0,960 / 9,22 | 0,951 / 16,22 | 0,959 / 7,89 | -1,33 [-2,63; -0,35] | 7 / 18 / 2 |
| teste_silver | 89 | 27 | 0,960 / 27,45 | 0,942 / 31,25 | 0,959 / 26,43 | -1,02 [-1,89; -0,08] | 14 / 72 / 3 |

Sensibilidade do limiar no golden_v4 (quebras por página do híbrido):

| Limiar (unidades) | 4 | 12 | 18 | 33 | 48 | 67 | 91 | 113 | 137 | 233 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Quebras | 6,05 | 6,02 | 5,80 | 5,70 | 5,50 | 5,14 | 5,68 | 6,07 | 6,48 | 7,98 |

Limitações: o limiar foi escolhido nas mesmas 44 páginas em que a regra de colunas foi desenvolvida;
o golden_v3 novo tem 27 páginas; no teste silver a referência é o fluxo do PDF e o piso de quebras é
alto por causa da ordem dentro das tabelas. É uma pista para testar, não um método validado.
