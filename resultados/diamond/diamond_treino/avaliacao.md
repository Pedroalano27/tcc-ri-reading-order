# Diamond `diamond_treino`: segmentacao contra a anotacao humana

39 paginas. Comparacao pelas palavras de cada regiao (docstring de `src/eval/avaliar_diamond.py`). A `proposta` e a pre-anotacao que o anotador viu: o gabarito partiu dela, entao o numero dela esta inflado.

| Sistema | Paginas | Regioes (gabarito) | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (palavras) |
|---|---:|---:|---:|---:|---:|---:|---:|
| v3 | 39 | 1054 (1338) | 0.690 | 0.583 | 0.568 | 0.337 | 84.8% |
| proposta | 39 | 1392 (1338) | 0.925 | 0.904 | 0.899 | 0.826 | 89.8% |
| regioes_v2 | 39 | 1390 (1338) | 0.924 | 0.902 | 0.897 | 0.806 | 89.3% |
| regioes | 39 | 1392 (1338) | 0.925 | 0.904 | 0.899 | 0.820 | 89.4% |
| rose:rose_treino | 39 | 1364 (1338) | 0.923 | 0.899 | 0.893 | 0.790 | 89.0% |
| pred:pred_yolo_diamond_treino | 39 | 1378 (1338) | 0.895 | 0.823 | 0.803 | 0.853 | 92.8% |
| regioes_v3+rose:todas | 39 | 1392 (1338) | 0.925 | 0.904 | 0.899 | 0.801 | 89.0% |
| regioes_v3+rose:assinatura_cabecalho | 39 | 1392 (1338) | 0.925 | 0.904 | 0.899 | 0.829 | 90.0% |
| regioes_v3+rose:assinatura_cabecalho_titulo_rodape | 39 | 1392 (1338) | 0.925 | 0.904 | 0.899 | 0.816 | 89.7% |

## Revocacao por classe (Jaccard >= 0,5 e mesma classe)

| Sistema | titulo | texto | lista | tabela | assinatura | cabecalho | rodape | figura | outro |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v3 | 0.00 (216) | 0.48 (759) | 0.00 (20) | 1.00 (38) | 0.00 (84) | 0.00 (90) | 0.00 (30) | 0.00 (11) | 0.00 (90) |
| proposta | 0.90 (216) | 0.92 (759) | 0.20 (20) | 1.00 (38) | 0.84 (84) | 0.90 (90) | 0.90 (30) | 0.00 (11) | 0.18 (90) |
| regioes_v2 | 0.90 (216) | 0.92 (759) | 0.20 (20) | 1.00 (38) | 0.76 (84) | 0.84 (90) | 0.90 (30) | 0.00 (11) | 0.00 (90) |
| regioes | 0.90 (216) | 0.92 (759) | 0.20 (20) | 1.00 (38) | 0.76 (84) | 0.84 (90) | 0.90 (30) | 0.00 (11) | 0.21 (90) |
| rose:rose_treino | 0.91 (216) | 0.81 (759) | 0.20 (20) | 1.00 (38) | 0.96 (84) | 0.92 (90) | 0.90 (30) | 0.00 (11) | 0.26 (90) |
| pred:pred_yolo_diamond_treino | 0.93 (216) | 0.93 (759) | 0.75 (20) | 0.97 (38) | 0.98 (84) | 0.91 (90) | 0.70 (30) | 0.73 (11) | 0.09 (90) |
| regioes_v3+rose:todas | 0.91 (216) | 0.83 (759) | 0.20 (20) | 1.00 (38) | 0.98 (84) | 0.94 (90) | 0.93 (30) | 0.00 (11) | 0.28 (90) |
| regioes_v3+rose:assinatura_cabecalho | 0.90 (216) | 0.90 (759) | 0.20 (20) | 1.00 (38) | 0.98 (84) | 0.96 (90) | 0.87 (30) | 0.00 (11) | 0.21 (90) |
| regioes_v3+rose:assinatura_cabecalho_titulo_rodape | 0.91 (216) | 0.87 (759) | 0.20 (20) | 1.00 (38) | 0.98 (84) | 0.94 (90) | 0.93 (30) | 0.00 (11) | 0.21 (90) |
