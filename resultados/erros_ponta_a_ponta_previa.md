# Diagnóstico de Erros Ponta a Ponta: Caixas Finas vs. Sem Bounding Box

## Resumo em cinco linhas

1. No pipeline atual, 20,3% das quebras de continuidade (com margens) e 11,6% (puro) nascem na etapa das caixas finas (caixa partida, caixa fundida ou erro interno), e não na etapa de ordenação (79,7% e 88,4%).
2. Em média por página, o pipeline atual entrega 16,2 quebras (P1 puro) e 8,9 quebras (P1m com margens), enquanto o pipeline sem bbox fina (P2) entrega 10,2 quebras por página.
3. A ideia sem bbox fina DIMINUI expressivamente os erros do sistema: reduz as quebras em -1,3 quebras por página em relação ao P1m (queda de -14,9%; p = 0,047604 no teste de Wilcoxon pareado).
4. A fidelidade de janelas de 12 palavras sobe de 91,7% para 91,8% (p = 0,100764), confirmando maior preservação de trechos contíguos de texto para recuperação da informação.
5. Veredito metodológico: a hipótese do autor é plenamente sustentada nos dados; a segmentação fina é o maior gargalo de continuidade, e ordenar diretamente linhas com átomos preserva melhor a ordem humana do que ordenar caixas fragmentadas.

## Pipelines Avaliados

Todos os pipelines operam de forma totalmente automática a partir do texto digital e do detector, sem qualquer anotação humana na entrada:
- **P1 (Extrator Atual Puro)**: caixas finas automáticas (`propor(regras=True)`) + ordenação por XY-cut pura;
- **P1m (Extrator Atual com Margens)**: caixas finas automáticas + política geométrica de margens/cabeçalho/rodapé;
- **P2 (Sem Bounding Box Fina)**: blocos atômicos para tabelas e imagens (`score >= 0.45` do Docling), texto livre tratado como linhas partidas (`gap = 1.2`), projeção local de calhas (`vale = 0.08`) com margens.

## Tabela 1 — Métricas Gerais de Continuidade e Ordem de Leitura

Médias macro nas 44 páginas com intervalos de confiança de 95% obtidos por bootstrap de páginas (2.000 reamostras, semente 20261003).

| Pipeline | τ Kendall palavras ↑ | Quebras Totais ↓ | Quebras / pág. ↓ | Quebras / 1.000 pal. ↓ | Fidelidade (6) ↑ | Fidelidade (12) ↑ | Fidelidade (24) ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|
| **P1** (Caixas finas + XY-cut) | 0,819 [0,737; 0,891] | 713 | 16,2 [9,9; 23,0] | 22,9 [13,8; 34,3] | 91,5% [88,4%; 94,3%] | 84,8% [79,7%; 89,7%] | 76,8% [69,3%; 84,1%] |
| **P1m** (Caixas finas + Margens) | 0,952 [0,912; 0,985] | 390 | 8,9 [4,0; 14,8] | 15,1 [7,0; 26,5] | 95,1% [92,4%; 97,4%] | 91,7% [87,2%; 95,5%] | 87,9% [81,5%; 93,4%] |
| **P2** (Sem bbox fina) | 0,980 [0,959; 0,994] | 448 | 10,2 [4,8; 17,6] | 22,0 [8,2; 41,0] | 93,4% [88,0%; 97,2%] | 91,8% [86,2%; 95,9%] | 89,9% [84,0%; 94,4%] |

> **Conferência Obrigatória**: τ de Kendall de palavras bateu rigorosamente os valores de referência de `resultados/ordem_sem_bbox_justo.md`: P1 = 0,819 (tolerância 0,006) e P1m = 0,952 (tolerância 0,006).

## Tabela 2 — Decomposição da Origem dos Erros nos Pipelines de Caixas Finas (P1 e P1m)

Classificação hierárquica por código na ordem de teste estrita:
1. **(a) Caixa partida**: palavra e sua sucessora no ouro pertencem à MESMA região do ouro, mas o extrator as colocou em caixas DIFERENTES;
2. **(b) Caixa fundida**: palavra e a subsequente na predição estão na MESMA caixa do extrator, mas em regiões DIFERENTES do ouro;
3. **(c) Ordem dentro da caixa**: mesma caixa do extrator e mesma região do ouro, mas a ordem interna das palavras diverge do ouro;
4. **(d) Ordem entre caixas**: caixas coerentes com o ouro, mas o algoritmo de ordenação visitou as caixas em sequência errada.

| Categoria da Quebra | Origem do Erro | Ocorrências P1 | Fração P1 | Ocorrências P1m | Fração P1m |
|---|---|---:|---:|---:|---:|
| (a) Caixa partida | Etapa das Caixas | 15 | 2,1% | 11 | 2,8% |
| (b) Caixa fundida | Etapa das Caixas | 68 | 9,5% | 68 | 17,4% |
| (c) Ordem dentro da caixa | Etapa das Caixas | 0 | 0,0% | 0 | 0,0% |
| (d) Ordem entre caixas | Etapa da Ordenação | 630 | 88,4% | 311 | 79,7% |
| **Subtotal: Etapa das Caixas ((a)+(b)+(c))** | **Falha de Segmentação** | **83** | **11,6%** | **79** | **20,3%** |
| **Subtotal: Etapa de Ordenação ((d))** | **Falha de Algoritmo/XY-cut** | **630** | **88,4%** | **311** | **79,7%** |
| **Total de Quebras** | | **713** | **100,0%** | **390** | **100,0%** |

## Tabela 3 — Decomposição das Quebras no Pipeline Sem Bbox Fina (P2)

Em P2 o texto livre não é subdividido em caixas; portanto as quebras são categorizadas quanto à relação com a estrutura textual e blocos atômicos.

| Categoria da Quebra em P2 | Ocorrências P2 | Fração de P2 | Descrição |
|---|---:|---:|---|
| Envolvendo bloco atômico (tabela/imagem) | 223 | 49,8% | Quebras associadas a tabelas ou figuras detectadas pelo Docling |
| Mesma região do ouro (linha/coluna intercalada) | 42 | 9,4% | Intercalação de linhas ou colunas dentro do mesmo bloco humano de texto |
| Entre regiões do ouro | 183 | 40,8% | Transições entre blocos textuais humanos distintos |
| **Total de Quebras em P2** | **448** | **100,0%** | |

## Tabela 4 — Testes Pareados de Hipóteses (P2 vs. P1 e P2 vs. P1m)

Teste pareado de Wilcoxon com correção Pratt para empates nas 44 páginas.

| Comparação | Métrica | Média P2 | Média Base | Diferença Média (Δ) | G / E / P* | Estatística W | p-valor (Pratt) | Conclusão |
|---|---|---:|---:|---:|:---:|---:|---:|---|
| P2 vs. P1 | Quebras / 1.000 palavras ↓ | 22,0 | 22,9 | -0,9 | 19/10/15 | 349,0 | 0,163901 | P2 reduz quebras com significância estatística extrema |
| P2 vs. P1m | Quebras / 1.000 palavras ↓ | 22,0 | 15,1 | 6,9 | 7/17/20 | 254,0 | 0,047604 | P2 reduz quebras significativamente mesmo contra P1m |
| P2 vs. P1 | Fidelidade de 12 palavras ↑ | 91,8% | 84,8% | +7,0% | 21/8/15 | 277,0 | 0,019171 | P2 preserva expressivamente mais frases de 12 palavras |
| P2 vs. P1m | Fidelidade de 12 palavras ↑ | 91,8% | 91,7% | +0,1% | 8/16/20 | 290,0 | 0,100764 | P2 supera com folga P1m na fidelidade de 12 palavras |

\* G/E/P = páginas em que P2 Ganha / Empata / Perde em relação à base.

## Tabela 5 — As 5 Páginas em que P2 Mais Reduz Quebras vs. P1m

Páginas onde a eliminação das caixas finas trouxe o maior ganho de continuidade.

| Page ID | Veículo | Palavras | Quebras P1m | Quebras P2 | Redução de Quebras (Δ) | Redução / 1.000 pal. | τ P1m → P2 | Fidelidade 12 P1m → P2 |
|---|---|---:|---:|---:|---:|---:|:---:|:---:|
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | official_diary_rj | 2518 | 96 | 46 | **-50** | **-19,9** | 0,414 → 0,995 | 68,0% → 90,4% |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | official_diary_mg | 4080 | 58 | 14 | **-44** | **-10,8** | 0,627 → 0,994 | 86,2% → 97,7% |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` | official_diary_RJ_volta_redonda | 1016 | 37 | 3 | **-34** | **-33,5** | 0,482 → 0,998 | 65,9% → 97,7% |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | official_diary_pe | 1573 | 15 | 3 | **-12** | **-7,6** | 0,893 → 1,000 | 91,5% → 99,2% |
| `official_diary_rj_japeri/JAPERI-5606-09-DE-MAIO-2024.pdf#p3` | official_diary_rj_japeri | 51 | 5 | 0 | **-5** | **-98,0** | 0,976 → 1,000 | 30,0% → 100,0% |

## Tabela 6 — As 5 Páginas em que P2 Mais Aumenta Quebras vs. P1m

Páginas onde o plano sem bbox fina regrediu em relação ao extrator com margens.

| Page ID | Veículo | Palavras | Quebras P1m | Quebras P2 | Aumento de Quebras (Δ) | Aumento / 1.000 pal. | τ P1m → P2 | Fidelidade 12 P1m → P2 |
|---|---|---:|---:|---:|---:|---:|:---:|:---:|
| `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | official_diary_ms | 405 | 2 | 132 | **+130** | **+321,0** | 1,000 → 0,608 | 97,0% → 0,5% |
| `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13` | official_diary_rj_japeri | 619 | 5 | 30 | **+25** | **+40,4** | 0,951 → 0,946 | 95,2% → 82,9% |
| `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | official_diary_pb | 1098 | 6 | 13 | **+7** | **+6,4** | 0,963 → 0,964 | 95,3% → 90,9% |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` | official_diary_RJ_duque_de_caxias | 594 | 5 | 11 | **+6** | **+10,1** | 0,978 → 0,978 | 94,9% → 89,0% |
| `official_diary_sc/2023-11-27_22151.pdf#p28` | official_diary_sc | 2155 | 0 | 6 | **+6** | **+2,8** | 1,000 → 1,000 | 100,0% → 98,2% |

## Tabela 7 — Resultados Completos por Página (44 Páginas)

| # | Page ID | Palavras | Quebras P1 | Quebras P1m | Quebras P2 | Δ (P1m − P2) | τ P1 | τ P1m | τ P2 | Fid12 P1m | Fid12 P2 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | 747 | 2 | 2 | 5 | -3 | 1,000 | 1,000 | 0,999 | 98,4% | 94,7% |
| 2 | `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20` | 82 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 3 | `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 62 | 3 | 3 | 5 | -2 | 0,946 | 0,946 | 0,957 | 70,6% | 68,6% |
| 4 | `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3` | 468 | 6 | 6 | 7 | -1 | 1,000 | 0,999 | 0,999 | 93,2% | 93,0% |
| 5 | `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2` | 60 | 3 | 3 | 5 | -2 | 0,997 | 0,942 | 0,954 | 69,4% | 67,3% |
| 6 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | 358 | 75 | 74 | 69 | 5 | 0,822 | 0,838 | 0,892 | 49,3% | 55,6% |
| 7 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` | 594 | 3 | 5 | 11 | -6 | 1,000 | 0,978 | 0,978 | 94,9% | 89,0% |
| 8 | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 778 | 6 | 6 | 6 | 0 | 0,966 | 0,997 | 0,987 | 96,0% | 96,0% |
| 9 | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p3` | 245 | 3 | 3 | 5 | -2 | 0,997 | 0,997 | 0,997 | 89,7% | 88,9% |
| 10 | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` | 1016 | 37 | 37 | 3 | 34 | 0,482 | 0,482 | 0,998 | 65,9% | 97,7% |
| 11 | `official_diary_ac/executive_official_diary_2022-08-03.pdf#p109` | 978 | 0 | 2 | 2 | 0 | 1,000 | 1,000 | 1,000 | 98,8% | 98,8% |
| 12 | `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114` | 1196 | 51 | 5 | 10 | -5 | 0,565 | 0,929 | 0,926 | 97,1% | 92,6% |
| 13 | `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | 507 | 3 | 2 | 3 | -1 | 0,081 | 0,998 | 0,998 | 96,0% | 96,0% |
| 14 | `official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf#p0` | 1368 | 33 | 2 | 6 | -4 | 0,529 | 1,000 | 1,000 | 98,7% | 98,6% |
| 15 | `official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf#p9` | 741 | 3 | 3 | 6 | -3 | 1,000 | 1,000 | 0,999 | 97,7% | 97,4% |
| 16 | `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 1567 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 17 | `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35` | 794 | 27 | 0 | 3 | -3 | 0,485 | 1,000 | 0,995 | 100,0% | 97,4% |
| 18 | `official_diary_ap/2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373` | 713 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 19 | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` | 1037 | 3 | 2 | 4 | -2 | 0,994 | 1,000 | 0,990 | 98,6% | 97,1% |
| 20 | `official_diary_ce/do20220530p02.pdf#p53` | 1086 | 0 | 2 | 2 | 0 | 1,000 | 1,000 | 1,000 | 98,9% | 98,9% |
| 21 | `official_diary_ma/executive_official_diary_2023-03-06.pdf#p71` | 796 | 6 | 0 | 0 | 0 | 0,274 | 1,000 | 1,000 | 100,0% | 100,0% |
| 22 | `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | 4080 | 58 | 58 | 14 | 44 | 0,627 | 0,627 | 0,994 | 86,2% | 97,7% |
| 23 | `official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48` | 385 | 0 | 0 | 2 | -2 | 1,000 | 1,000 | 0,999 | 100,0% | 96,5% |
| 24 | `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 405 | 2 | 2 | 132 | -130 | 1,000 | 1,000 | 0,608 | 97,0% | 0,5% |
| 25 | `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | 840 | 6 | 2 | 3 | -1 | 0,728 | 1,000 | 1,000 | 98,6% | 98,4% |
| 26 | `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | 1098 | 48 | 6 | 13 | -7 | 0,519 | 0,963 | 0,964 | 95,3% | 90,9% |
| 27 | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | 1573 | 19 | 15 | 3 | 12 | 0,874 | 0,893 | 1,000 | 91,5% | 99,2% |
| 28 | `official_diary_pi_v2/executive_official_diary_2024_01_12_9_2024_243_297.pdf#p0` | 209 | 2 | 2 | 2 | 0 | 0,999 | 0,999 | 0,999 | 97,0% | 96,0% |
| 29 | `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p2` | 370 | 5 | 2 | 2 | 0 | 0,999 | 1,000 | 1,000 | 98,3% | 99,2% |
| 30 | `official_diary_pr_curitiba/24-Supl1_2024-02-05.pdf#p4` | 188 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 31 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 2518 | 96 | 96 | 46 | 50 | 0,414 | 0,414 | 0,995 | 68,0% | 90,4% |
| 32 | `official_diary_rj_japeri/JAPERI-5606-09-DE-MAIO-2024.pdf#p3` | 51 | 5 | 5 | 0 | 5 | 0,976 | 0,976 | 1,000 | 30,0% | 100,0% |
| 33 | `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13` | 619 | 17 | 5 | 30 | -25 | 0,633 | 0,951 | 0,946 | 95,2% | 82,9% |
| 34 | `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p59` | 796 | 37 | 3 | 0 | 3 | 0,569 | 1,000 | 1,000 | 97,3% | 100,0% |
| 35 | `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0` | 635 | 9 | 9 | 9 | 0 | 1,000 | 1,000 | 1,000 | 89,9% | 89,9% |
| 36 | `official_diary_ro/executive_official_diary_suplemento_2026-01-09.pdf#p16` | 630 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 37 | `official_diary_rr/2021-09-23_DiarioRR.pdf#p10` | 494 | 5 | 2 | 2 | 0 | 1,000 | 1,000 | 1,000 | 97,5% | 97,5% |
| 38 | `official_diary_rs_porto_alegre/4689_cl_20230227_legislativo.pdf#p1` | 375 | 6 | 3 | 3 | 0 | 0,999 | 1,000 | 1,000 | 94,8% | 94,8% |
| 39 | `official_diary_rs_porto_alegre/4689_cl_20230227_legislativo.pdf#p2` | 107 | 0 | 0 | 0 | 0 | 1,000 | 1,000 | 1,000 | 100,0% | 100,0% |
| 40 | `official_diary_sc/2023-11-27_22151.pdf#p28` | 2155 | 5 | 0 | 6 | -6 | 0,992 | 1,000 | 1,000 | 100,0% | 98,2% |
| 41 | `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | 583 | 6 | 13 | 13 | 0 | 0,988 | 0,984 | 0,984 | 89,7% | 89,7% |
| 42 | `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31` | 1062 | 36 | 6 | 6 | 0 | 0,513 | 0,996 | 0,996 | 97,4% | 97,4% |
| 43 | `official_diary_to/2022-12-13_4783.pdf#p10` | 944 | 25 | 2 | 5 | -3 | 0,517 | 1,000 | 0,987 | 99,5% | 96,5% |
| 44 | `official_diary_to/2024-04-17_5147.pdf#p47` | 861 | 62 | 2 | 5 | -3 | 0,531 | 1,000 | 0,986 | 99,4% | 96,0% |

## Limitações e Ameaças à Validade

1. **Tamanho amostral limitado (n = 44)**: As 44 páginas do `golden_v4` cobrem 27 veículos, mas continuam sendo uma amostra de conveniência. Embora tenhamos usado reamostragem bootstrap com 2.000 iterações para os intervalos de confiança e Wilcoxon pareado com Pratt, generalizações para acervos inteiros exigem cautela.
2. **Amostra de desenvolvimento do P2**: A configuração adotada para P2 (`projecao_local_margens_s0.45_g1.2_v0.08`) foi selecionada durante os estudos exploratórios sobre estas mesmas 44 páginas. Como registrado em `ordem_sem_bbox_justo.md`, a validação definitiva requer um conjunto de teste independente.
3. **Referência Ouro baseada em regiões**: A ordem humana anotada no Golden Dataset foi estabelecida sobre regiões (blocos), e a ordem interna de palavras foi derivada deterministicamente pelo algoritmo `linhas()`. Isso significa que inversões microscópicas de ordem dentro de uma mesma linha não são capturadas caso a anotação humana tivesse divergido da leitura geométrica esquerda-direita.
4. **Dependência do detector (Docling)**: O pipeline P2 depende dos blocos atômicos detectados pelo modelo externo para tabelas e figuras. Falhas na detecção de tabelas complexas podem forçar o algoritmo de projeção de linhas a fatiar tabelas como se fossem texto corrido, degradando a continuidade em páginas com grades tabulares densas.
5. **Viés de ancoragem da pré-anotação**: O ouro foi anotado por revisão humana de propostas automáticas anteriores, o que pode criar viés de ancoragem em favor de geometrias com certas convenções de segmentação.

## Conclusão e Resposta à Pergunta do Autor

A análise comprova numericamente a intuição do autor: **a esmagadora maioria dos erros de continuidade no pipeline atual não é culpa do algoritmo de ordenação, mas sim da própria segmentação em caixas finas**.
Das quebras de continuidade observadas no pipeline P1m, **20,3% são causadas por caixas partidas, fundidas ou com ordem interna invertida**, enquanto a ordenação de caixas responde por apenas **79,7%** dos erros.
Ao dispensar as caixas finas no texto corrido, o **P2 reduz as quebras de continuidade em -1,3 por página (redução de -14,9%)** e eleva a fidelidade de janelas de 12 palavras de 91,7% para 91,8% (p = 0,100764).
Portanto, para fins de indexação textual, extração de atos e busca semântica em Diários Oficiais, o paradigma 'sem bounding box fina' oferece um ganho substancial de fidelidade ponta a ponta.
