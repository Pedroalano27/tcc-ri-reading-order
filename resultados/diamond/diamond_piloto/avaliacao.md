# Diamond `diamond_piloto`: segmentacao contra a anotacao humana

20 paginas. Comparacao pelas palavras de cada regiao (docstring de `src/eval/avaliar_diamond.py`). A `proposta` e a pre-anotacao que o anotador viu: o gabarito partiu dela, entao o numero dela esta inflado.

| Sistema | Paginas | Regioes (gabarito) | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (palavras) |
|---|---:|---:|---:|---:|---:|---:|---:|
| v3 | 20 | 523 (754) | 0.647 | 0.512 | 0.457 | 0.296 | 83.8% |
| proposta | 20 | 764 (754) | 0.937 | 0.870 | 0.867 | 0.788 | 90.7% |
| regioes_v2 | 20 | 763 (754) | 0.952 | 0.893 | 0.887 | 0.840 | 91.4% |
| regioes | 20 | 764 (754) | 0.951 | 0.891 | 0.885 | 0.848 | 91.5% |
| pred:pred_kaggle_limpo_diamond_piloto | 20 | 777 (754) | 0.933 | 0.869 | 0.840 | 0.879 | 93.9% |
| hibrido:pred_kaggle_limpo_diamond_piloto | 20 | 764 (754) | 0.951 | 0.891 | 0.885 | 0.884 | 96.2% |

## Revocacao por classe (Jaccard >= 0,5 e mesma classe)

| Sistema | titulo | texto | lista | tabela | assinatura | cabecalho | rodape | figura | outro |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v3 | 0.00 (152) | 0.41 (448) | 0.00 (14) | 0.88 (8) | 0.00 (49) | 0.00 (53) | 0.00 (21) | 0.00 (2) | 0.00 (7) |
| proposta | 0.85 (152) | 0.88 (448) | 0.57 (14) | 0.88 (8) | 0.00 (49) | 0.72 (53) | 0.95 (21) | 0.00 (2) | 0.00 (7) |
| regioes_v2 | 0.85 (152) | 0.90 (448) | 0.57 (14) | 0.88 (8) | 0.63 (49) | 0.72 (53) | 0.95 (21) | 0.00 (2) | 0.00 (7) |
| regioes | 0.85 (152) | 0.90 (448) | 0.57 (14) | 0.88 (8) | 0.63 (49) | 0.72 (53) | 0.95 (21) | 0.00 (2) | 1.00 (7) |
| pred:pred_kaggle_limpo_diamond_piloto | 0.83 (152) | 0.94 (448) | 0.64 (14) | 1.00 (8) | 0.90 (49) | 0.93 (53) | 0.67 (21) | 0.50 (2) | 0.14 (7) |
| hibrido:pred_kaggle_limpo_diamond_piloto | 0.85 (152) | 0.93 (448) | 0.57 (14) | 0.88 (8) | 0.82 (49) | 0.89 (53) | 0.81 (21) | 0.50 (2) | 1.00 (7) |
