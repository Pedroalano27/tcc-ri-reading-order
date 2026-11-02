# Diagnostico de Faixas Estreitas Indevidas e Cabecalhos Fragmentados

Relatorio analitico da representacao de texto sem caixas finas (colunas e faixas continuas).
Medicoes conduzidas em CPU sobre o conjunto consolidado de paginas unicas do acervo e na bancada Golden v4.

## Resumo Executivo

1. **Frequencia do defeito:** O defeito de faixas estreitas indevidas afeta 13 de 614 paginas (2,1%) e 69 de 3.600 faixas de texto (1,9%) do conjunto consolidado.
2. **Concentracao por veiculo:** A anomalia se concentra principalmente em official_diary_pe (6/14 pags, 21 faixas), official_diary_sc (2/22 pags, 40 faixas), official_diary_pr (2/25 pags, 4 faixas), decorrente de alinhamentos irregulares, tabelas sem bordas e notas marginais.
3. **Volume de texto atingido:** O defeito atinge 3.075 palavras (0,58% de todas as 528.001 palavras do conjunto), com impacto localizado mas de alto risco para ordenadores sequenciais.
4. **Recomendacao para a regra de calhas:** Calhas verticais locais devem exigir largura minima de faixa (suporte geometrico de pelo menos 12% da pagina ou 45% da mediana local), sob pena de fusao obrigatoria com a coluna adjacente.

## 1. Distribuicao Geral das Faixas de Texto

Estatisticas calculadas sobre todas as faixas de texto (`tipo == 'texto_coluna'`) nas paginas unicas:

| Variavel / Metrica | Media | Desvio Padrao | Min | p10 | p25 | Mediana (p50) | p75 | p90 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Largura relativa a pagina | 39,9 % | 22,6 % | 0,4 % | 11,4 % | 28,1 % | 38,1 % | 45,7 % | 81,5 % | 98,4 % |
| Numero de linhas por faixa | 15,9 | 27,6 | 1,0 | 1,0 | 1,0 | 1,0 | 18,0 | 61,0 | 359,0 |
| Numero de palavras por faixa | 121,2 | 217,6 | 1,0 | 3,0 | 8,0 | 14,0 | 105,0 | 462,1 | 1.999,0 |
| Largura relativa a mediana da pagina | 98,7 % | 42,8 % | 0,9 % | 51,4 % | 91,2 % | 100,0 % | 100,2 % | 129,4 % | 758,3 % |

## 2. Faixas Suspeitas por Veiculo

Uma faixa de texto e classificada como **suspeita** se possui pelo menos **4 linhas** e sua largura e **menor que 45% da mediana da pagina** OU **menor que 12% da largura da pagina**.

- **Total de faixas suspeitas:** 69
- **Paginas com faixas suspeitas:** 13 de 614 (2,12%)
- **Palavras em faixas suspeitas:** 3.075 de 528.001 (0,58%)

### Tabela Detalhada por Veiculo (ordenada pela fracao de paginas afetadas)

| Veiculo (UF) | Paginas Totais | Paginas Afetadas | % Pags Afetadas | Faixas Totais | Faixas Suspeitas | % Faixas Suspeitas | Palavras Totais | Palavras Afetadas | % Pals Afetadas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `official_diary_pe` | 14 | 6 | 42,9% | 445 | 21 | 4,7% | 22.149 | 1.855 | 8,38% |
| `official_diary_sc` | 22 | 2 | 9,1% | 1.010 | 40 | 4,0% | 35.136 | 915 | 2,60% |
| `official_diary_pr` | 25 | 2 | 8,0% | 334 | 4 | 1,2% | 29.263 | 219 | 0,75% |
| `official_diary_al` | 21 | 1 | 4,8% | 96 | 1 | 1,0% | 18.940 | 60 | 0,32% |
| `official_diary_RJ_volta_redonda` | 40 | 1 | 2,5% | 221 | 1 | 0,5% | 40.500 | 8 | 0,02% |
| `official_diary_ba_salvador` | 49 | 1 | 2,0% | 167 | 2 | 1,2% | 46.156 | 18 | 0,04% |
| `official_diary_ap` | 49 | 0 | 0,0% | 108 | 0 | 0,0% | 26.350 | 0 | 0,00% |
| `official_diary_am_manaus` | 43 | 0 | 0,0% | 131 | 0 | 0,0% | 41.235 | 0 | 0,00% |
| `official_diary_RJ_duque_de_caxias` | 42 | 0 | 0,0% | 232 | 0 | 0,0% | 38.287 | 0 | 0,00% |
| `official_diary_ac` | 37 | 0 | 0,0% | 49 | 0 | 0,0% | 32.396 | 0 | 0,00% |
| `official_diary_ms` | 35 | 0 | 0,0% | 35 | 0 | 0,0% | 16.289 | 0 | 0,00% |
| `official_diary_RJ_barra_do_pirai` | 33 | 0 | 0,0% | 80 | 0 | 0,0% | 14.997 | 0 | 0,00% |
| `official_diary_RJ_seropedica` | 28 | 0 | 0,0% | 176 | 0 | 0,0% | 15.669 | 0 | 0,00% |
| `official_diary_pa` | 25 | 0 | 0,0% | 221 | 0 | 0,0% | 26.480 | 0 | 0,00% |
| `official_diary_MG_congonhas` | 23 | 0 | 0,0% | 32 | 0 | 0,0% | 11.281 | 0 | 0,00% |
| `official_diary_rr` | 21 | 0 | 0,0% | 21 | 0 | 0,0% | 14.667 | 0 | 0,00% |
| `official_diary_ro` | 15 | 0 | 0,0% | 15 | 0 | 0,0% | 9.103 | 0 | 0,00% |
| `official_diary_se` | 14 | 0 | 0,0% | 54 | 0 | 0,0% | 17.488 | 0 | 0,00% |
| `official_diary_rn` | 13 | 0 | 0,0% | 44 | 0 | 0,0% | 21.854 | 0 | 0,00% |
| `official_diary_to` | 12 | 0 | 0,0% | 23 | 0 | 0,0% | 12.110 | 0 | 0,00% |
| `official_diary_pr_curitiba` | 12 | 0 | 0,0% | 12 | 0 | 0,0% | 2.772 | 0 | 0,00% |
| `official_diary_rs_porto_alegre` | 10 | 0 | 0,0% | 10 | 0 | 0,0% | 3.541 | 0 | 0,00% |
| `official_diary_pi_v2` | 10 | 0 | 0,0% | 10 | 0 | 0,0% | 3.234 | 0 | 0,00% |
| `official_diary_pb` | 8 | 0 | 0,0% | 24 | 0 | 0,0% | 11.328 | 0 | 0,00% |
| `official_diary_rj_japeri` | 8 | 0 | 0,0% | 16 | 0 | 0,0% | 6.053 | 0 | 0,00% |
| `official_diary_rj` | 1 | 0 | 0,0% | 24 | 0 | 0,0% | 2.519 | 0 | 0,00% |
| `official_diary_ce` | 1 | 0 | 0,0% | 1 | 0 | 0,0% | 1.104 | 0 | 0,00% |
| `official_diary_ma` | 1 | 0 | 0,0% | 2 | 0 | 0,0% | 796 | 0 | 0,00% |
| `official_diary_mg` | 1 | 0 | 0,0% | 6 | 0 | 0,0% | 4.080 | 0 | 0,00% |
| `official_diary_sp` | 1 | 0 | 0,0% | 1 | 0 | 0,0% | 2.224 | 0 | 0,00% |
| **TOTAL GLOBAL** | **614** | **13** | **2,1%** | **3.600** | **69** | **1,9%** | **528.001** | **3.075** | **0,58%** |

## 3. Faixas Sobrepostas na Mesma Pagina

Pares de faixas de texto (`texto_coluna`) da mesma pagina cuja **area de intersecao ultrapassa 20% da area da menor faixa**:

- **Total de pares sobrepostos identificados:** 249
- **Total de paginas afetadas por sobreposicao:** 56

### As 20 Piores Sobreposicoes

| # | Page ID | Veiculo | Faixa A (id / lin / pal) | Faixa B (id / lin / pal) | % Sobreposicao | IoU | Area Intersecao (pt²) |
|---|---|---|---|---|---:|---:|---:|
| 1 | `executive_official_diary_2022-04-28_978.pdf#p2` | `official_diary_RJ_seropedica` | `c18` (5L, 28W) | `c17` (1L, 11W) | **100,0%** | 14,6% | 3.658,3 |
| 2 | `2025-01-14_1-Poder Executivo.pdf#p1` | `official_diary_pe` | `c37` (1L, 14W) | `c36` (5L, 38W) | **100,0%** | 21,6% | 3.515,1 |
| 3 | `2025-09-11_1-Poder Executivo.pdf#p4` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,5 |
| 4 | `2026-01-09_1-Poder Executivo.pdf#p2` | `official_diary_pe` | `c1` (1L, 9W) | `c0` (2L, 13W) | **100,0%** | 38,3% | 2.820,5 |
| 5 | `2025-07-29_1-Poder Executivo.pdf#p3` | `official_diary_pe` | `c1` (1L, 9W) | `c0` (2L, 13W) | **100,0%** | 38,3% | 2.820,5 |
| 6 | `2025-05-06_1-Poder Executivo.pdf#p3` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,5 |
| 7 | `2023-02-02_1-Poder Executivo.pdf#p6` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,5 |
| 8 | `2025-09-11_1-Poder Executivo.pdf#p5` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,5 |
| 9 | `2025-07-12_1-Poder Executivo.pdf#p6` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,4 |
| 10 | `2024-02-06_1-Poder Executivo.pdf#p3` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,4 |
| 11 | `2021-08-27_1-Poder Executivo.pdf#p6` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,0 |
| 12 | `2021-08-12_1-Poder Executivo.pdf#p4` | `official_diary_pe` | `c1` (1L, 9W) | `c0` (2L, 13W) | **100,0%** | 38,3% | 2.820,0 |
| 13 | `2021-11-09_1-Poder Executivo.pdf#p2` | `official_diary_pe` | `c0` (2L, 13W) | `c1` (1L, 9W) | **100,0%** | 38,3% | 2.820,0 |
| 14 | `2025-01-14_1-Poder Executivo.pdf#p1` | `official_diary_pe` | `c6` (1L, 39W) | `c7` (1L, 10W) | **100,0%** | 13,2% | 2.267,7 |
| 15 | `2025-01-14_1-Poder Executivo.pdf#p1` | `official_diary_pe` | `c7` (1L, 10W) | `c5` (2L, 6W) | **100,0%** | 20,7% | 2.267,7 |
| 16 | `2025-01-14_1-Poder Executivo.pdf#p1` | `official_diary_pe` | `c13` (3L, 16W) | `c14` (1L, 8W) | **100,0%** | 29,8% | 2.267,5 |
| 17 | `DOE-RN_2023-08-02_Ordinaria_33_52.pdf#p0` | `official_diary_rn` | `c1` (1L, 9W) | `c0` (2L, 13W) | **100,0%** | 26,7% | 1.966,4 |
| 18 | `2022-01-14_21688.pdf#p16` | `official_diary_sc` | `c2` (2L, 11W) | `c3` (1L, 9W) | **100,0%** | 38,1% | 1.844,4 |
| 19 | `DOE-RN_2022-11-23_Ordinaria.pdf#p51` | `official_diary_rn` | `c0` (2L, 13W) | `c1` (1L, 8W) | **100,0%** | 24,9% | 1.837,8 |
| 20 | `DOE-RN_2022-11-23_Ordinaria.pdf#p5` | `official_diary_rn` | `c0` (2L, 13W) | `c1` (1L, 8W) | **100,0%** | 24,9% | 1.837,8 |

## 4. Fragmentacao de Cabecalhos e Rodapes (45 Paginas do Golden v4)

Analise conduzida sobre `resultados/estruturas_golden_v4/colunas.jsonl` (45 paginas):

### Estatisticas de Cabecalhos e Rodapes por Pagina

| Tipo Estrutural | Mediana por Pagina | Maximo por Pagina | Paginas com > 2 Unidades | % Paginas com > 2 Unidades |
|---|---:|---:|---:|---:|
| **Cabecalho** (`cabecalho`) | 2,0 | 4 | 22 de 45 | 48,9% |
| **Rodape** (`rodape`) | 1,0 | 4 | 5 de 45 | 11,1% |

### Distribuicao de Unidades por Pagina

| Qtd de Unidades | Paginas com Cabecalhos | Paginas com Rodapes |
|---|---:|---:|
| 0 unidades | 8 (17,8%) | 22 (48,9%) |
| 1 unidades | 11 (24,4%) | 10 (22,2%) |
| 2 unidades | 4 (8,9%) | 8 (17,8%) |
| 3 unidades | 15 (33,3%) | 4 (8,9%) |
| 4 unidades | 7 (15,6%) | 1 (2,2%) |

### Causa Tecnica da Fragmentacao
A presenca de multiplos cabecalhos e rodapes em uma unica pagina ocorre porque o detector de layout (`docling-layout-heron` e heuristica vetorial) detecta caixas delimitadoras locais separadas para cada elemento individual da margem (ex.: numero de pagina a direita, titulo do diario ao centro, data e brasao a esquerda). Como o exportador trata cada regiao delimitada como uma unidade isolada antes da projecao de colunas, essas caixas nao sao fundidas em uma unica faixa horizontal, gerando fragmentacao estrutural artificial nas bordas da pagina.

## 5. Galeria Visual das 12 Paginas com Mais Faixas Suspeitas (Golden v4)

As 12 paginas do Golden com maior volume de faixas suspeitas foram renderizadas com caixas coloridas:
- **Azul:** faixas de texto de largura regular (`texto_coluna`).
- **Vermelho:** faixas suspeitas (>= 4 linhas e largura < 45% da mediana ou < 12% da pagina).
- **Verde:** estruturas de cabecalho e rodape isoladas.

| # | Arquivo de Imagem | Veiculo (UF) | Faixas Texto | Faixas Suspeitas | Dimensao Renderizada | Diagnostico Visual |
|---|---|---|---:|---:|---|---|
| 01 | [`01_official_diary_pr.jpg`](resultados/faixas_estreitas/01_official_diary_pr.jpg) | `official_diary_pr` | 4 | **2** | `991x1400` | Faixa estreita indevida gerada por calha local (`executive_official_diary_2021-11-26.pdf#p66`) |
| 02 | [`02_official_diary_rs_porto_alegre.jpg`](resultados/faixas_estreitas/02_official_diary_rs_porto_alegre.jpg) | `official_diary_rs_porto_alegre` | 1 | **0** | `989x1400` | Sem faixas estreitas graves (`4689_cl_20230227_legislativo.pdf#p1`) |
| 03 | [`03_official_diary_RJ_barra_do_pirai.jpg`](resultados/faixas_estreitas/03_official_diary_RJ_barra_do_pirai.jpg) | `official_diary_RJ_barra_do_pirai` | 1 | **0** | `1209x1400` | Sem faixas estreitas graves (`executive_official_diary_2026-01-16_010.pdf#p2`) |
| 04 | [`04_official_diary_pi_v2.jpg`](resultados/faixas_estreitas/04_official_diary_pi_v2.jpg) | `official_diary_pi_v2` | 1 | **0** | `991x1400` | Sem faixas estreitas graves (`executive_official_diary_2025_11_07_216_2025.pdf#p2`) |
| 05 | [`05_official_diary_se.jpg`](resultados/faixas_estreitas/05_official_diary_se.jpg) | `official_diary_se` | 1 | **0** | `1021x1400` | Sem faixas estreitas graves (`DOE-SE_2023-03-10_5100.pdf#p14`) |
| 06 | [`06_official_diary_rj.jpg`](resultados/faixas_estreitas/06_official_diary_rj.jpg) | `official_diary_rj` | 3 | **0** | `902x1400` | Sem faixas estreitas graves (`Parte II (Poder Legislativo)_2024-02-06.pdf#p1`) |
| 07 | [`07_official_diary_al.jpg`](resultados/faixas_estreitas/07_official_diary_al.jpg) | `official_diary_al` | 1 | **0** | `991x1400` | Sem faixas estreitas graves (`DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`) |
| 08 | [`08_official_diary_ce.jpg`](resultados/faixas_estreitas/08_official_diary_ce.jpg) | `official_diary_ce` | 1 | **0** | `991x1400` | Sem faixas estreitas graves (`do20220530p02.pdf#p53`) |
| 09 | [`09_official_diary_RJ_duque_de_caxias.jpg`](resultados/faixas_estreitas/09_official_diary_RJ_duque_de_caxias.jpg) | `official_diary_RJ_duque_de_caxias` | 2 | **0** | `991x1400` | Sem faixas estreitas graves (`executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`) |
| 10 | [`10_official_diary_ac.jpg`](resultados/faixas_estreitas/10_official_diary_ac.jpg) | `official_diary_ac` | 2 | **0** | `991x1400` | Sem faixas estreitas graves (`executive_official_diary_2025-02-11.pdf#p114`) |
| 11 | [`11_official_diary_ro.jpg`](resultados/faixas_estreitas/11_official_diary_ro.jpg) | `official_diary_ro` | 1 | **0** | `990x1400` | Sem faixas estreitas graves (`executive_official_diary_suplemento_2026-01-09.pdf#p16`) |
| 12 | [`12_official_diary_ms.jpg`](resultados/faixas_estreitas/12_official_diary_ms.jpg) | `official_diary_ms` | 0 | **0** | `990x1400` | Sem faixas estreitas graves (`executive_official_diary_46741_2021-06-29.pdf#p48`) |
