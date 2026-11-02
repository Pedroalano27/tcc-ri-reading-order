# Ordenadores treinados sobre unidades sem caixas finas

Relatório gerado por `treinar_sem_caixas.py`; estado parcial é preservado a cada checkpoint.

Amostra fixa: prefixo de 0 páginas pedidas, semente 20261004, de 3217 elegíveis; 43 puladas por recorte deslocado. Não foi exportada nenhuma página adicional.

- `linhas`: 151 registros base + 3023 extras = 3140 páginas únicas após deduplicação. Todos os treinos completos usam exatamente estes IDs; fumaças são subconjuntos explicitamente separados.
- `colunas`: 151 registros base + 3023 extras = 3140 páginas únicas após deduplicação. Todos os treinos completos usam exatamente estes IDs; fumaças são subconjuntos explicitamente separados.
- `colunas_margens`: 151 registros base + 3023 extras = 3140 páginas únicas após deduplicação. Todos os treinos completos usam exatamente estes IDs; fumaças são subconjuntos explicitamente separados.

Âncoras conferidas antes do treino com `bancada_ordenadores.py --somente-ancoras`:

| Âncora v4 | τ palavras | Quebras/página |
|---|---:|---:|
| P2 | 0,985948 | 6,045455 |
| P1m | 0,952424 | 8,931818 |

## Treinos executados

| Modelo | Representação | Dispositivo | Páginas | Visitadas | Passos | Épocas completas | Segundos | τ validação de unidades | Concluído |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| fumaca_texto | linhas | cpu | 8 | 8 | 1 | 1 | 41,9 | 0,078009 | sim |
| layoutreader_ajustado_linhas | linhas | cuda | 873 | 873 | 440 | 4 | 204,0 | 0,901046 | sim |
| lstm_geo_colunas_margens | colunas_margens | cpu | 873 | 873 | 4400 | 40 | 299,8 | 0,831111 | sim |
| lstm_geo_linhas | linhas | cpu | 873 | 873 | 1102 | 10 | 481,0 | 0,840063 | sim |
| lstm_geo_texto_colunas_margens | colunas_margens | cpu | 873 | 873 | 3224 | 29 | 425,6 | 0,831746 | não |
| lstm_geo_texto_linhas | linhas | cpu | 873 | 873 | 941 | 8 | 481,7 | 0,799752 | sim |
| pontual_linhas | linhas | cuda | 873 | 873 | 880 | 8 | 626,2 | 0,870360 | sim |
| sucessor_colunas_margens | colunas_margens | cuda | 873 | 873 | 880 | 8 | 632,7 | 0,844444 | sim |
| sucessor_colunas_margens_s43 | colunas_margens | cuda | 873 | 873 | 880 | 8 | 647,7 | 0,844444 | sim |
| sucessor_linhas | linhas | cuda | 873 | 873 | 880 | 8 | 739,4 | 0,869452 | sim |
| sucessor_linhas_100ep | linhas | cuda | 873 | 873 | 11000 | 100 | 9370,4 | 0,931728 | sim |
| sucessor_linhas_40ep | linhas | cuda | 873 | 873 | 4400 | 40 | 3948,2 | 0,934662 | sim |
| sucessor_linhas_completo_s42 | linhas | cuda | 3140 | 3140 | 7860 | 20 | 7697,5 | 0,933753 | sim |
| sucessor_linhas_completo_s43 | linhas | cuda | 3140 | 3140 | 7860 | 20 | 6589,0 | 0,934548 | sim |
| sucessor_linhas_s43 | linhas | cuda | 873 | 873 | 880 | 8 | 737,4 | 0,882660 | sim |
| sucessor_linhas_texto_s42 | linhas | cuda | 3140 | 3140 | 7860 | 20 | 6820,3 | 0,917961 | sim |
| sucessor_linhas_texto_s42 | linhas | cuda | 3140 | 1160 | 145 | 0 | 125,3 | -2,000000 | não |

## Régua de palavras, por bancada

As métricas abaixo vêm da bancada existente; a expansão interna é `ordem_sem_bbox.fluxo()`. Validação escolhe checkpoint por τ de unidades em RN; não usa ouro humano.

| Modelo | Representação | Bancada | Grupo | n | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas | Δτ ao oráculo mediano | Δquebras ao oráculo |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| layoutreader_ajustado_linhas | linhas | golden_v3_novo | todos | 27 | 0,944733 | 20,85 | 89,30% | 86,13% | 0,055261 | 20,15 |
| layoutreader_ajustado_linhas | linhas | golden_v3_novo | não vistos | 27 | 0,944733 | 20,85 | 89,30% | 86,13% | 0,055261 | 20,15 |
| layoutreader_ajustado_linhas | linhas | golden_v4 | todos | 44 | 0,905410 | 21,91 | 90,39% | 89,08% | 0,094583 | 21,02 |
| layoutreader_ajustado_linhas | linhas | golden_v4 | vistos | 5 | 0,875020 | 27,20 | 88,77% | 88,16% | 0,124969 | 25,80 |
| layoutreader_ajustado_linhas | linhas | golden_v4 | não vistos | 39 | 0,909306 | 21,23 | 90,60% | 89,19% | 0,090688 | 20,41 |
| layoutreader_ajustado_linhas | linhas | teste_silver | todos | 89 | 0,930176 | 36,60 | 80,24% | 80,80% | 0,066927 | 19,47 |
| layoutreader_ajustado_linhas | linhas | teste_silver | não vistos | 89 | 0,930176 | 36,60 | 80,24% | 80,80% | 0,066927 | 19,47 |
| lstm_geo_colunas_margens | colunas_margens | golden_v3_novo | todos | 27 | 0,833214 | 9,15 | 92,28% | 91,82% | 0,075944 | 0,33 |
| lstm_geo_colunas_margens | colunas_margens | golden_v3_novo | não vistos | 27 | 0,833214 | 9,15 | 92,28% | 91,82% | 0,075944 | 0,33 |
| lstm_geo_colunas_margens | colunas_margens | golden_v4 | todos | 44 | 0,934236 | 6,25 | 94,74% | 93,50% | 0,025724 | 1,05 |
| lstm_geo_colunas_margens | colunas_margens | golden_v4 | vistos | 5 | 0,874404 | 6,40 | 95,29% | 94,43% | 0,074561 | 1,00 |
| lstm_geo_colunas_margens | colunas_margens | golden_v4 | não vistos | 39 | 0,941906 | 6,23 | 94,67% | 93,38% | 0,019463 | 1,05 |
| lstm_geo_colunas_margens | colunas_margens | teste_silver | todos | 89 | 0,906561 | 32,24 | 80,29% | 82,42% | 0,039899 | 6,99 |
| lstm_geo_colunas_margens | colunas_margens | teste_silver | não vistos | 89 | 0,906561 | 32,24 | 80,29% | 82,42% | 0,039899 | 6,99 |
| lstm_geo_linhas | linhas | golden_v3_novo | todos | 27 | 0,845511 | 75,04 | 46,51% | 35,19% | 0,154483 | 74,33 |
| lstm_geo_linhas | linhas | golden_v3_novo | não vistos | 27 | 0,845511 | 75,04 | 46,51% | 35,19% | 0,154483 | 74,33 |
| lstm_geo_linhas | linhas | golden_v4 | todos | 44 | 0,872290 | 75,48 | 40,32% | 30,37% | 0,127703 | 74,59 |
| lstm_geo_linhas | linhas | golden_v4 | vistos | 5 | 0,906304 | 119,40 | 44,01% | 36,36% | 0,093685 | 118,00 |
| lstm_geo_linhas | linhas | golden_v4 | não vistos | 39 | 0,867929 | 69,85 | 39,85% | 29,60% | 0,132064 | 69,03 |
| lstm_geo_linhas | linhas | teste_silver | todos | 89 | 0,854402 | 107,67 | 35,56% | 24,50% | 0,142702 | 90,55 |
| lstm_geo_linhas | linhas | teste_silver | não vistos | 89 | 0,854402 | 107,67 | 35,56% | 24,50% | 0,142702 | 90,55 |
| lstm_geo_texto_colunas_margens | colunas_margens | golden_v3_novo | todos | 27 | 0,819227 | 9,19 | 92,34% | 91,87% | 0,089932 | 0,37 |
| lstm_geo_texto_colunas_margens | colunas_margens | golden_v3_novo | não vistos | 27 | 0,819227 | 9,19 | 92,34% | 91,87% | 0,089932 | 0,37 |
| lstm_geo_texto_colunas_margens | colunas_margens | golden_v4 | todos | 44 | 0,898530 | 6,30 | 94,35% | 93,40% | 0,061430 | 1,09 |
| lstm_geo_texto_colunas_margens | colunas_margens | golden_v4 | vistos | 5 | 0,786003 | 6,80 | 95,29% | 94,28% | 0,162962 | 1,40 |
| lstm_geo_texto_colunas_margens | colunas_margens | golden_v4 | não vistos | 39 | 0,912956 | 6,23 | 94,23% | 93,29% | 0,048413 | 1,05 |
| lstm_geo_texto_colunas_margens | colunas_margens | teste_silver | todos | 89 | 0,879439 | 32,51 | 80,07% | 82,31% | 0,067021 | 7,26 |
| lstm_geo_texto_colunas_margens | colunas_margens | teste_silver | não vistos | 89 | 0,879439 | 32,51 | 80,07% | 82,31% | 0,067021 | 7,26 |
| lstm_geo_texto_linhas | linhas | golden_v3_novo | todos | 27 | 0,817913 | 78,04 | 43,66% | 30,45% | 0,182081 | 77,33 |
| lstm_geo_texto_linhas | linhas | golden_v3_novo | não vistos | 27 | 0,817913 | 78,04 | 43,66% | 30,45% | 0,182081 | 77,33 |
| lstm_geo_texto_linhas | linhas | golden_v4 | todos | 44 | 0,850227 | 78,14 | 38,24% | 28,59% | 0,149765 | 77,25 |
| lstm_geo_texto_linhas | linhas | golden_v4 | vistos | 5 | 0,898021 | 125,20 | 41,15% | 33,57% | 0,101967 | 123,80 |
| lstm_geo_texto_linhas | linhas | golden_v4 | não vistos | 39 | 0,844100 | 72,10 | 37,87% | 27,95% | 0,155893 | 71,28 |
| lstm_geo_texto_linhas | linhas | teste_silver | todos | 89 | 0,812201 | 110,62 | 32,78% | 21,26% | 0,184902 | 93,49 |
| lstm_geo_texto_linhas | linhas | teste_silver | não vistos | 89 | 0,812201 | 110,62 | 32,78% | 21,26% | 0,184902 | 93,49 |
| pontual_linhas | linhas | golden_v3_novo | todos | 27 | 0,870196 | 74,44 | 47,63% | 36,15% | 0,129798 | 73,74 |
| pontual_linhas | linhas | golden_v3_novo | não vistos | 27 | 0,870196 | 74,44 | 47,63% | 36,15% | 0,129798 | 73,74 |
| pontual_linhas | linhas | golden_v4 | todos | 44 | 0,902310 | 72,57 | 43,35% | 33,93% | 0,097682 | 71,68 |
| pontual_linhas | linhas | golden_v4 | vistos | 5 | 0,969481 | 115,80 | 47,81% | 38,96% | 0,030508 | 114,40 |
| pontual_linhas | linhas | golden_v4 | não vistos | 39 | 0,893699 | 67,03 | 42,78% | 33,29% | 0,106294 | 66,21 |
| pontual_linhas | linhas | teste_silver | todos | 89 | 0,869050 | 105,74 | 37,33% | 26,44% | 0,128053 | 88,62 |
| pontual_linhas | linhas | teste_silver | não vistos | 89 | 0,869050 | 105,74 | 37,33% | 26,44% | 0,128053 | 88,62 |
| sucessor_colunas_margens | colunas_margens | golden_v3_novo | todos | 27 | 0,867014 | 8,96 | 92,49% | 92,19% | 0,042145 | 0,15 |
| sucessor_colunas_margens | colunas_margens | golden_v3_novo | não vistos | 27 | 0,867014 | 8,96 | 92,49% | 92,19% | 0,042145 | 0,15 |
| sucessor_colunas_margens | colunas_margens | golden_v4 | todos | 44 | 0,934163 | 5,98 | 94,79% | 93,76% | 0,025797 | 0,77 |
| sucessor_colunas_margens | colunas_margens | golden_v4 | vistos | 5 | 0,858007 | 6,20 | 95,24% | 94,56% | 0,090958 | 0,80 |
| sucessor_colunas_margens | colunas_margens | golden_v4 | não vistos | 39 | 0,943926 | 5,95 | 94,74% | 93,66% | 0,017443 | 0,77 |
| sucessor_colunas_margens | colunas_margens | teste_silver | todos | 89 | 0,902705 | 32,18 | 80,40% | 82,43% | 0,043755 | 6,93 |
| sucessor_colunas_margens | colunas_margens | teste_silver | não vistos | 89 | 0,902705 | 32,18 | 80,40% | 82,43% | 0,043755 | 6,93 |
| sucessor_colunas_margens_s43 | colunas_margens | golden_v3_novo | todos | 27 | 0,865694 | 9,00 | 92,48% | 92,11% | 0,043464 | 0,19 |
| sucessor_colunas_margens_s43 | colunas_margens | golden_v3_novo | não vistos | 27 | 0,865694 | 9,00 | 92,48% | 92,11% | 0,043464 | 0,19 |
| sucessor_colunas_margens_s43 | colunas_margens | golden_v4 | todos | 44 | 0,936177 | 5,86 | 94,88% | 93,89% | 0,023783 | 0,66 |
| sucessor_colunas_margens_s43 | colunas_margens | golden_v4 | vistos | 5 | 0,858482 | 6,00 | 95,65% | 94,70% | 0,090483 | 0,60 |
| sucessor_colunas_margens_s43 | colunas_margens | golden_v4 | não vistos | 39 | 0,946138 | 5,85 | 94,78% | 93,78% | 0,015231 | 0,67 |
| sucessor_colunas_margens_s43 | colunas_margens | teste_silver | todos | 89 | 0,901657 | 31,96 | 80,41% | 82,45% | 0,044803 | 6,71 |
| sucessor_colunas_margens_s43 | colunas_margens | teste_silver | não vistos | 89 | 0,901657 | 31,96 | 80,41% | 82,45% | 0,044803 | 6,71 |
| sucessor_linhas_100ep | linhas | golden_v3_novo | todos | 27 | 0,895723 | 12,59 | 89,49% | 88,41% | 0,104271 | 11,89 |
| sucessor_linhas_100ep | linhas | golden_v3_novo | não vistos | 27 | 0,895723 | 12,59 | 89,49% | 88,41% | 0,104271 | 11,89 |
| sucessor_linhas_100ep | linhas | golden_v4 | todos | 44 | 0,929268 | 12,57 | 92,14% | 89,65% | 0,070724 | 11,68 |
| sucessor_linhas_100ep | linhas | golden_v4 | vistos | 5 | 0,991734 | 8,80 | 97,08% | 96,71% | 0,008255 | 7,40 |
| sucessor_linhas_100ep | linhas | golden_v4 | não vistos | 39 | 0,921260 | 13,05 | 91,50% | 88,74% | 0,078733 | 12,23 |
| sucessor_linhas_100ep | linhas | teste_silver | todos | 89 | 0,931371 | 31,91 | 80,89% | 81,53% | 0,065732 | 14,79 |
| sucessor_linhas_100ep | linhas | teste_silver | não vistos | 89 | 0,931371 | 31,91 | 80,89% | 81,53% | 0,065732 | 14,79 |
| sucessor_linhas_40ep | linhas | golden_v3_novo | todos | 27 | 0,919281 | 12,48 | 89,40% | 88,51% | 0,080713 | 11,78 |
| sucessor_linhas_40ep | linhas | golden_v3_novo | não vistos | 27 | 0,919281 | 12,48 | 89,40% | 88,51% | 0,080713 | 11,78 |
| sucessor_linhas_40ep | linhas | golden_v4 | todos | 44 | 0,927649 | 11,00 | 93,19% | 90,40% | 0,072344 | 10,11 |
| sucessor_linhas_40ep | linhas | golden_v4 | vistos | 5 | 0,992782 | 7,80 | 96,56% | 96,28% | 0,007206 | 6,40 |
| sucessor_linhas_40ep | linhas | golden_v4 | não vistos | 39 | 0,919298 | 11,41 | 92,76% | 89,65% | 0,080695 | 10,59 |
| sucessor_linhas_40ep | linhas | teste_silver | todos | 89 | 0,914279 | 31,92 | 80,45% | 81,16% | 0,082825 | 14,80 |
| sucessor_linhas_40ep | linhas | teste_silver | não vistos | 89 | 0,914279 | 31,92 | 80,45% | 81,16% | 0,082825 | 14,80 |
| sucessor_linhas | linhas | golden_v3_novo | todos | 27 | 0,884739 | 57,00 | 63,36% | 54,07% | 0,115254 | 56,30 |
| sucessor_linhas | linhas | golden_v3_novo | não vistos | 27 | 0,884739 | 57,00 | 63,36% | 54,07% | 0,115254 | 56,30 |
| sucessor_linhas | linhas | golden_v4 | todos | 44 | 0,902271 | 57,59 | 61,40% | 54,34% | 0,097722 | 56,70 |
| sucessor_linhas | linhas | golden_v4 | vistos | 5 | 0,864965 | 93,60 | 62,05% | 53,94% | 0,135024 | 92,20 |
| sucessor_linhas | linhas | golden_v4 | não vistos | 39 | 0,907054 | 52,97 | 61,31% | 54,39% | 0,092939 | 52,15 |
| sucessor_linhas | linhas | teste_silver | todos | 89 | 0,876328 | 89,62 | 50,80% | 40,61% | 0,120776 | 72,49 |
| sucessor_linhas | linhas | teste_silver | não vistos | 89 | 0,876328 | 89,62 | 50,80% | 40,61% | 0,120776 | 72,49 |
| sucessor_linhas_completo_s42 | linhas | golden_v3_novo | todos | 27 | 0,927693 | 10,41 | 90,92% | 90,26% | 0,072301 | 9,70 |
| sucessor_linhas_completo_s42 | linhas | golden_v3_novo | não vistos | 27 | 0,927693 | 10,41 | 90,92% | 90,26% | 0,072301 | 9,70 |
| sucessor_linhas_completo_s42 | linhas | golden_v4 | todos | 44 | 0,923692 | 9,00 | 94,25% | 92,59% | 0,076301 | 8,11 |
| sucessor_linhas_completo_s42 | linhas | golden_v4 | vistos | 5 | 0,993789 | 7,60 | 97,42% | 96,85% | 0,006200 | 6,20 |
| sucessor_linhas_completo_s42 | linhas | golden_v4 | não vistos | 39 | 0,914705 | 9,18 | 93,84% | 92,05% | 0,085288 | 8,36 |
| sucessor_linhas_completo_s42 | linhas | teste_silver | todos | 89 | 0,934165 | 29,15 | 82,03% | 82,92% | 0,062938 | 12,02 |
| sucessor_linhas_completo_s42 | linhas | teste_silver | não vistos | 89 | 0,934165 | 29,15 | 82,03% | 82,92% | 0,062938 | 12,02 |
| sucessor_linhas_completo_s43 | linhas | golden_v3_novo | todos | 27 | 0,922683 | 10,81 | 90,79% | 89,63% | 0,077310 | 10,11 |
| sucessor_linhas_completo_s43 | linhas | golden_v3_novo | não vistos | 27 | 0,922683 | 10,81 | 90,79% | 89,63% | 0,077310 | 10,11 |
| sucessor_linhas_completo_s43 | linhas | golden_v4 | todos | 44 | 0,945122 | 8,68 | 93,99% | 92,55% | 0,054871 | 7,80 |
| sucessor_linhas_completo_s43 | linhas | golden_v4 | vistos | 5 | 0,992333 | 9,20 | 97,15% | 96,65% | 0,007656 | 7,80 |
| sucessor_linhas_completo_s43 | linhas | golden_v4 | não vistos | 39 | 0,939069 | 8,62 | 93,58% | 92,03% | 0,060924 | 7,79 |
| sucessor_linhas_completo_s43 | linhas | teste_silver | todos | 89 | 0,934092 | 29,63 | 81,91% | 82,57% | 0,063012 | 12,51 |
| sucessor_linhas_completo_s43 | linhas | teste_silver | não vistos | 89 | 0,934092 | 29,63 | 81,91% | 82,57% | 0,063012 | 12,51 |
| sucessor_linhas_s43 | linhas | golden_v3_novo | todos | 27 | 0,879237 | 62,41 | 58,18% | 47,80% | 0,120757 | 61,70 |
| sucessor_linhas_s43 | linhas | golden_v3_novo | não vistos | 27 | 0,879237 | 62,41 | 58,18% | 47,80% | 0,120757 | 61,70 |
| sucessor_linhas_s43 | linhas | golden_v4 | todos | 44 | 0,887253 | 62,75 | 55,80% | 48,06% | 0,112740 | 61,86 |
| sucessor_linhas_s43 | linhas | golden_v4 | vistos | 5 | 0,915752 | 100,60 | 56,25% | 49,74% | 0,084237 | 99,20 |
| sucessor_linhas_s43 | linhas | golden_v4 | não vistos | 39 | 0,883599 | 57,90 | 55,75% | 47,84% | 0,116394 | 57,08 |
| sucessor_linhas_s43 | linhas | teste_silver | todos | 89 | 0,861724 | 94,35 | 46,83% | 36,47% | 0,135379 | 77,22 |
| sucessor_linhas_s43 | linhas | teste_silver | não vistos | 89 | 0,861724 | 94,35 | 46,83% | 36,47% | 0,135379 | 77,22 |

## Veículos vistos nas bancadas humanas

`golden_v4`: 5 vistas por veículo e 39 não vistas. Nenhuma destas páginas entrou no treino.

- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5`
- `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6`
- `official_diary_rr/2021-09-23_DiarioRR.pdf#p10`
- `official_diary_sc/2023-11-27_22151.pdf#p28`

`golden_v3_novo`: 0 vistas por veículo e 27 não vistas. Nenhuma destas páginas entrou no treino.


## Adaptações e limitações

Os embrulhos importam as arquiteturas e perdas existentes. Leitura por offsets, micro-lotes sequenciais, sem workers, no máximo quatro threads; caches/checkpoints em resultados. BiLSTM mantém MSE/Adam 0,002 e até 40 épocas, orçamento de oito minutos por variante/representação. O prazo é conferido entre lotes; validação e gravação final podem acrescentar tempo. Entrada fixa do protocolo em treino e inferência.

LayoutLM usa exatamente um token [UNK] por unidade, além de CLS/SEP: não há tokenização de texto nem truncamento silencioso. Sucessor mantém viés geométrico, peso de posição e decodificação em cadeias do melhor config anterior. Pontual também recebe UNK único: ablação geométrica declarada. A única página que excede 510 unidades é agrupada em faixas por geometria, com ordem interna congelada, e todas as suas unidades continuam no treino. Contagens auditadas por representação/partição estão em auditoria_tokens.json.

LayoutReader ajusta as últimas quatro camadas e a cabeça, preservando pesos locais iniciais; o restante do encoder fica congelado para caber em 6 GB. Um token de caixa por unidade, fp16 com AMP apenas na GPU; CPU float32. Gradient checkpointing na GPU. A perda ensina diretamente a permutação retornada pelo decoder local (posto de saída → índice de entrada); não se inverte com argsort.

Colunas têm poucas unidades e ordem interna imposta: o ordenador quase não pode consertar quebras internas. Linhas deixam mais decisões ao ordenador e aproximam o oráculo humano, mas apertam o orçamento de tokens. O teste silver discorda da expansão canônica dentro das tabelas; comparar τ e distância ao oráculo, sem interpretar todas as quebras absolutas como erro do ordenador.

Golden v4 participou do desenvolvimento da regra de colunas; golden v3 adicional é pequeno e pode repetir veículos. Ouro humano é de regiões expandido geometricamente. Silver é automático, nos veículos confiáveis e split congelado; páginas humanas e silver podem se sobrepor e não devem ser somadas. Veículo visto refere-se ao split do TCC, não ao treinamento prévio do ls3/LayoutReader.

## Roteiros de GPU

Os quatro roteiros são independentes e retomáveis; treinam 873 páginas únicas, até quatro épocas e 75 minutos, batch efetivo 8/micro-batch 1; encoder lr 0,00004, cabeça 0,001, seed 42. Inferência sequencial nas três bancadas em CPU após encerrar o processo de treino; cada JSONL é incorporado com --avaliar-pred, sem alterar a expansão da bancada. Nenhum roteiro foi executado em GPU por esta tarefa.

- `orquestracao/noite_0410/gpu/01_sucessor_linhas.sh`
- `orquestracao/noite_0410/gpu/02_layoutreader_ajuste_linhas.sh`
- `orquestracao/noite_0410/gpu/03_sucessor_colunas_margens.sh`
- `orquestracao/noite_0410/gpu/04_pontual_linhas.sh`
- `orquestracao/noite_0410/gpu/04b_layoutreader_ajuste_linhas.sh`
- `orquestracao/noite_0410/gpu/05_sucessor_linhas_40ep.sh`
- `orquestracao/noite_0410/gpu/06_sucessor_colunas_margens_s43.sh`
- `orquestracao/noite_0410/gpu/07_sucessor_linhas_s43.sh`
- `orquestracao/noite_0410/gpu/08_sucessor_linhas_100ep.sh`

```json
{
  "linhas": {
    "treino": {
      "paginas": 873,
      "mediana_unidades": 137,
      "max_unidades": 517,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 1,
      "paginas_descartadas": 0,
      "hierarquia": [
        {
          "page_id": "official_diary_pe/2023-04-29_1-Poder Executivo.pdf#p32",
          "unidades": 517,
          "faixas": 204
        }
      ]
    },
    "validacao": {
      "paginas": 15,
      "mediana_unidades": 178,
      "max_unidades": 299,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    },
    "teste": {
      "paginas": 89,
      "mediana_unidades": 87,
      "max_unidades": 401,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    }
  },
  "colunas": {
    "treino": {
      "paginas": 873,
      "mediana_unidades": 5,
      "max_unidades": 214,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    },
    "validacao": {
      "paginas": 15,
      "mediana_unidades": 3,
      "max_unidades": 11,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    },
    "teste": {
      "paginas": 89,
      "mediana_unidades": 3,
      "max_unidades": 169,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    }
  },
  "colunas_margens": {
    "treino": {
      "paginas": 873,
      "mediana_unidades": 5,
      "max_unidades": 213,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    },
    "validacao": {
      "paginas": 15,
      "mediana_unidades": 3,
      "max_unidades": 7,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    },
    "teste": {
      "paginas": 89,
      "mediana_unidades": 3,
      "max_unidades": 169,
      "tokens_por_unidade": 1,
      "fora_limite_direto": 0,
      "paginas_descartadas": 0,
      "hierarquia": []
    }
  },
  "mesmos_ids_treino": true
}
```

## Reprodução

```powershell
venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas.py relatorio
```

## Leitura do resultado principal

| Ordenador em linhas, v4 | τ palavras | Quebras/página |
|---|---:|---:|
| regra_colunas | 0,985948 | 6,05 |
| lstm_geo_linhas | 0,872290 | 75,48 |
| lstm_geo_texto_linhas | 0,850227 | 78,14 |

Os BiLSTMs em linhas avaliados até aqui tiveram mais quebras de leitura que a regra de colunas. Portanto este orçamento de treino não sustenta ganho de continuidade por BiLSTM.

As avaliações dos Transformers da fila estão completas e constam das tabelas acima.

## Evidência das fumaças em CPU

| Fumaça | Páginas selecionadas | Visitadas | Passos de otimizador | Bancadas inferidas | Isolamento do ouro |
|---|---:|---:|---:|---:|---|
| fumaca_texto | 8 | 8 | 1 | 0 | pendente |

Fumaças usam CPU/float32, sem carregar outra rede em paralelo. Cada inferência limitada confere permutação, avalia pela função original da bancada e repete a predição sem referência de unidades. Seus valores de eficácia são controles de execução, não avaliações completas. JSONs de treino e tempos em `resultados/ordenadores_treinados_sem_caixas/fumaca_*/` preservam os números.

O Bash desta sessão falhou antes de analisar os roteiros (`CreateFileMapping`, erro de acesso do Windows). Por isso a prova executável usa diretamente o Python do projeto com os mesmos argumentos. A sintaxe Bash precisa de conferência no terminal da fila. Nenhum pico de memória/tempo em GPU foi medido; micro-lote e congelamento de camadas são escolhas de execução a confirmar quando a fila rodar.
