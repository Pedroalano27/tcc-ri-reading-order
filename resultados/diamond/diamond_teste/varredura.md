# Varredura do extrator em `diamond_teste` (11 paginas, SEM ancoragem)

Ordenado por F1@0,5 com classe. `d` = diferenca vs extrator atual.

| Configuracao | F1@0,5 | F1@0,9 | F1 c/ classe | d classe | Classe % | regioes |
|---|---:|---:|---:|---:|---:|---:|
| hibrido classe [assinatura_cabecalho] | 0.838 | 0.737 | **0.695** | +0.009 | 77.1% | 383/328 |
| v3 score_min=0.55 | 0.840 | 0.738 | **0.687** | +0.001 | 77.0% | 379/328 |
| extrator v3 (atual) **<** | 0.838 | 0.737 | **0.686** | +0.000 | 76.9% | 383/328 |
| v3 sem local_e_data **<** | 0.838 | 0.737 | **0.686** | +0.000 | 76.9% | 383/328 |
| v3 score_min=0.35 **<** | 0.838 | 0.737 | **0.686** | +0.000 | 76.9% | 383/328 |
| hibrido gapfill (caixas) **<** | 0.838 | 0.737 | **0.686** | +0.000 | 76.9% | 383/328 |
| hibrido classe [todas] | 0.838 | 0.737 | **0.675** | -0.011 | 64.8% | 383/328 |
| v3 sem rotulo_com_valor | 0.820 | 0.707 | **0.671** | -0.015 | 76.9% | 396/328 |
| v3 sem assinatura | 0.826 | 0.718 | **0.665** | -0.021 | 76.5% | 391/328 |
| v3 sem dividir_campos | 0.814 | 0.696 | **0.664** | -0.022 | 77.2% | 365/328 |
| v3 score_min=0.65 | 0.817 | 0.717 | **0.659** | -0.027 | 72.7% | 397/328 |
| regras v2 | 0.841 | 0.745 | **0.657** | -0.029 | 76.7% | 381/328 |
| v3 sem outro_marcacao | 0.841 | 0.745 | **0.657** | -0.029 | 76.7% | 381/328 |
| hibrido classe [lista,assinatura,cabecalho,figura] | 0.838 | 0.737 | **0.653** | -0.033 | 66.1% | 383/328 |
| hibrido classe [tabela,figura,assinatura,cabecalho,rodape,lista] | 0.838 | 0.737 | **0.653** | -0.033 | 66.1% | 383/328 |
| so outro_marcacao | 0.784 | 0.647 | **0.627** | -0.059 | 76.8% | 386/328 |
| so dividir_campos | 0.811 | 0.696 | **0.622** | -0.064 | 76.3% | 402/328 |
| so assinatura | 0.798 | 0.673 | **0.619** | -0.067 | 77.0% | 376/328 |
| so rotulo_com_valor | 0.804 | 0.684 | **0.612** | -0.074 | 76.6% | 371/328 |
| sem regras | 0.787 | 0.654 | **0.598** | -0.088 | 76.6% | 384/328 |
| so local_e_data | 0.787 | 0.654 | **0.598** | -0.088 | 76.6% | 384/328 |
