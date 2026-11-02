# Diamond `diamond_teste`: segmentacao contra a anotacao humana

11 paginas. Comparacao pelas palavras de cada regiao (docstring de `src/eval/avaliar_diamond.py`). A `proposta` e a pre-anotacao que o anotador viu: o gabarito partiu dela, entao o numero dela esta inflado.

| Sistema | Paginas | Regioes (gabarito) | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (palavras) |
|---|---:|---:|---:|---:|---:|---:|---:|
| v3 | 11 | 303 (328) | 0.666 | 0.567 | 0.564 | 0.317 | 72.4% |
| proposta | 11 | 0 (328) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% |
| regioes_v2 | 11 | 369 (328) | 0.844 | 0.735 | 0.723 | 0.666 | 76.7% |
| regioes | 11 | 370 (328) | 0.851 | 0.754 | 0.745 | 0.696 | 76.9% |
| regioes_sem_fundir | 11 | 383 (328) | 0.838 | 0.737 | 0.731 | 0.686 | 76.9% |

## Revocacao por classe (Jaccard >= 0,5 e mesma classe)

| Sistema | titulo | texto | lista | tabela | assinatura | cabecalho | rodape | figura | outro |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v3 | 0.00 (58) | 0.49 (172) | 0.00 (9) | 0.80 (20) | 0.00 (15) | 0.00 (23) | 0.00 (9) | 0.00 (5) | 0.00 (17) |
| proposta | 0.00 (58) | 0.00 (172) | 0.00 (9) | 0.00 (20) | 0.00 (15) | 0.00 (23) | 0.00 (9) | 0.00 (5) | 0.00 (17) |
| regioes_v2 | 0.69 (58) | 0.82 (172) | 0.11 (9) | 0.80 (20) | 0.47 (15) | 0.78 (23) | 1.00 (9) | 0.00 (5) | 0.00 (17) |
| regioes | 0.69 (58) | 0.82 (172) | 0.11 (9) | 0.80 (20) | 0.47 (15) | 0.78 (23) | 1.00 (9) | 0.00 (5) | 0.65 (17) |
| regioes_sem_fundir | 0.69 (58) | 0.83 (172) | 0.11 (9) | 0.80 (20) | 0.47 (15) | 0.78 (23) | 1.00 (9) | 0.00 (5) | 0.65 (17) |
