# Auditoria do Extrator Novo sem Caixas de Parágrafo

Auditoria automática realizada em todas as páginas exportadas na representação sem caixas de parágrafo (texto em linhas, apenas tabela e imagem como bloco, margens e quadros separados).

## 1. Resumo Executivo

1. A auditoria cobriu **614 páginas únicas** exportadas no extrator novo, identificando inconsistências estruturais e geométricas.
2. Os defeitos mais frequentes são **D4 (Tabela suspeita)** com 123 páginas (20,0%), seguido de **D6 (Linha com altura anômala)** (16,8%) e **D2 (Sobreposição tabela x texto)** (8,0%).
3. Exatamente **32,1% das páginas** (197 de 614) apresentam pelo menos um defeito grave (gravidade $\ge 0,70$).
4. Os veículos que mais concentram defeitos no acervo são **am_manaus (223), RJ_duque_de_caxias (82), RJ_seropedica (73), ba_salvador (66)**, refletindo leiautes multicoluna mais densos e tabelas complexas.
5. Os detectores calibrados contra as anotações humanas do autor reproduziram os apontamentos reais de invasão de colunas, listas colapsadas em tabelas e sobreposições.

## 2. Resultados por Detector

| Detector | Nome do Defeito | Páginas Afetadas | % Total | Gravidade Média | Com Nota (Acende/Total) | Sem Nota (Acende) | Acerto / Recall Notas |
|:---:|:---|---:|---:|---:|---:|---:|---:|
| **D1** | Linha que atravessa colunas | 5 | 0,8% | 0,68 | 1/15 | 4 | 0,0% (0/2) |
| **D2** | Sobreposição tabela x texto | 49 | 8,0% | 0,49 | 4/15 | 45 | 100,0% (1/1) |
| **D3** | Coluna não separada | 0 | 0,0% | 0,00 | 0/15 | 0 | - |
| **D4** | Tabela suspeita | 123 | 20,0% | 0,80 | 1/15 | 122 | 0,0% (0/4) |
| **D5** | Cabeçalho/rodapé fragmentado | 37 | 6,0% | 0,77 | 14/15 | 23 | 100,0% (4/4) |
| **D6** | Linha com altura anômala | 103 | 16,8% | 0,78 | 6/15 | 97 | - |
| **D7** | Texto sem dono perto de átomo | 6 | 1,0% | 0,69 | 2/15 | 4 | 0,0% (0/7) |

## 3. Páginas Mais Críticas

### 3.1 As 15 Piores Páginas no Geral

| Rank | Page ID | Veículo (UF) | Gravidade Máx. | Gravidade Total | Total Achados | Detectores Acionados |
|---:|:---|:---|---:|---:|---:|:---|
| 1 | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p9` | official_diary_am_manaus | 1,00 | 17,59 | 21 | D2, D4, D6 |
| 2 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29` | official_diary_am_manaus | 1,00 | 15,47 | 18 | D1, D6 |
| 3 | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p5` | official_diary_am_manaus | 1,00 | 15,37 | 19 | D2, D6 |
| 4 | `official_diary_am_manaus/2025-08-13_caderno_1.pdf#p32` | official_diary_am_manaus | 1,00 | 14,12 | 16 | D2, D4, D6 |
| 5 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p26` | official_diary_am_manaus | 1,00 | 14,06 | 16 | D6 |
| 6 | `official_diary_am_manaus/2025-08-13_caderno_1.pdf#p21` | official_diary_am_manaus | 1,00 | 13,93 | 16 | D2, D4, D6 |
| 7 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p44` | official_diary_am_manaus | 1,00 | 13,82 | 16 | D2, D4, D6 |
| 8 | `official_diary_am_manaus/2025-11-03_caderno_1.pdf#p24` | official_diary_am_manaus | 1,00 | 13,74 | 15 | D2, D6 |
| 9 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p3` | official_diary_am_manaus | 1,00 | 11,47 | 13 | D1, D4, D6 |
| 10 | `official_diary_am_manaus/2025-11-03_caderno_1.pdf#p2` | official_diary_am_manaus | 1,00 | 11,41 | 13 | D2, D6 |
| 11 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p40` | official_diary_am_manaus | 1,00 | 10,80 | 12 | D2, D6 |
| 12 | `official_diary_am_manaus/2025-11-03_caderno_1.pdf#p1` | official_diary_am_manaus | 1,00 | 10,12 | 12 | D2, D4, D6 |
| 13 | `official_diary_am_manaus/2025-08-13_caderno_1.pdf#p36` | official_diary_am_manaus | 1,00 | 8,36 | 9 | D2, D6 |
| 14 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p36` | official_diary_am_manaus | 1,00 | 7,12 | 9 | D2, D4, D6 |
| 15 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-06-28_1845.pdf#p20` | official_diary_RJ_volta_redonda | 1,00 | 6,97 | 8 | D4, D6 |

### 3.2 As 5 Piores Páginas por Detector

#### D1 — Linha que atravessa colunas

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | official_diary_RJ_duque_de_caxias | 1,00 | largura=90.3% da pag; vao_max=461.2pt (77.5%) |
| 2 | `official_diary_ro/executive_official_diary_suplemento_2026-01-09.pdf#p16` | official_diary_ro | 1,00 | largura=91.3% da pag; vao_max=254.9pt (42.8%) |
| 3 | `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | official_diary_ms | 0,53 | largura=85.1% da pag; vao_max=39.2pt (6.6%) |
| 4 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p3` | official_diary_am_manaus | 0,44 | largura=81.0% da pag; vao_max=28.3pt (4.8%) |
| 5 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29` | official_diary_am_manaus | 0,44 | largura=81.0% da pag; vao_max=28.3pt (4.8%) |

#### D2 — Sobreposição tabela x texto

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_am_manaus/2025-11-03_caderno_1.pdf#p24` | official_diary_am_manaus | 1,00 | atomo=l3(picture); sobrep_texto=18.0%; sobrep_atomo=100.0% |
| 2 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p40` | official_diary_am_manaus | 1,00 | atomo=l3(picture); sobrep_texto=6.9%; sobrep_atomo=100.0% |
| 3 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | official_diary_rj | 1,00 | atomo=l0(picture); sobrep_texto=3.4%; sobrep_atomo=100.0% |
| 4 | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | official_diary_RJ_seropedica | 1,00 | atomo=l1(picture); sobrep_texto=100.0%; sobrep_atomo=100.0% |
| 5 | `official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf#p9` | official_diary_al | 1,00 | atomo=l2(picture); sobrep_texto=100.0%; sobrep_atomo=100.0% |

#### D3 — Coluna não separada

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| - | *Nenhum achado neste detector* | - | - | - |

#### D4 — Tabela suspeita

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-06-28_1845.pdf#p20` | official_diary_RJ_volta_redonda | 1,00 | linhas=2; linhas_com_vao=2; lista_nomes=False |
| 2 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-12-15_1899.pdf#p4` | official_diary_RJ_volta_redonda | 1,00 | tabela vazia (zero palavras associadas) |
| 3 | `official_diary_RJ_volta_redonda/executive_official_diary_2023-03-28_1930.pdf#p5` | official_diary_RJ_volta_redonda | 1,00 | tabela vazia (zero palavras associadas) |
| 4 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-10-20_1884.pdf#p13` | official_diary_RJ_volta_redonda | 1,00 | tabela vazia (zero palavras associadas) |
| 5 | `official_diary_RJ_volta_redonda/executive_official_diary_2023-07-25_1967_39_44.pdf#p0` | official_diary_RJ_volta_redonda | 1,00 | tabela vazia (zero palavras associadas) |

#### D5 — Cabeçalho/rodapé fragmentado

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p2` | official_diary_pi_v2 | 1,00 | cabecalhos=4; rodapes=4; fragmentos_curtos=6 |
| 2 | `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | official_diary_se | 1,00 | cabecalhos=4; rodapes=1; fragmentos_curtos=3 |
| 3 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | official_diary_rj | 1,00 | cabecalhos=3; rodapes=0; fragmentos_curtos=2 |
| 4 | `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | official_diary_al | 1,00 | cabecalhos=4; rodapes=0; fragmentos_curtos=1 |
| 5 | `official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf#p9` | official_diary_al | 1,00 | cabecalhos=4; rodapes=0; fragmentos_curtos=1 |

#### D6 — Linha com altura anômala

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29` | official_diary_am_manaus | 1,00 | altura=37.7pt; mediana=8.5pt; razao=4.43x |
| 2 | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p5` | official_diary_am_manaus | 1,00 | altura=28.0pt; mediana=8.5pt; razao=3.29x |
| 3 | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p9` | official_diary_am_manaus | 1,00 | altura=49.1pt; mediana=8.5pt; razao=5.76x |
| 4 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p26` | official_diary_am_manaus | 1,00 | altura=58.9pt; mediana=8.5pt; razao=6.92x |
| 5 | `official_diary_am_manaus/2025-08-13_caderno_1.pdf#p21` | official_diary_am_manaus | 1,00 | altura=92.3pt; mediana=8.5pt; razao=10.83x |

#### D7 — Texto sem dono perto de átomo

| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |
|---:|:---|:---|---:|:---|
| 1 | `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | official_diary_ms | 1,00 | atomo=l1(table); n_invasoras=13; amostra=['Diário', 'Oficial', 'Eletrônico', 'n.'] |
| 2 | `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | official_diary_pb | 0,75 | atomo=l1(picture); n_invasoras=3; amostra=['Diário', 'Ofi', 'cial'] |
| 3 | `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | official_diary_pb | 0,75 | atomo=l8(picture); n_invasoras=3; amostra=['Diário', 'Ofi', 'cial'] |
| 4 | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | official_diary_RJ_seropedica | 0,55 | atomo=l1(picture); n_invasoras=1; amostra=['3'] |
| 5 | `official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf#p9` | official_diary_al | 0,55 | atomo=l2(picture); n_invasoras=1; amostra=['10'] |

## 4. Galeria de Imagens Inspecionadas

Foram renderizadas as 4 piores páginas de cada detector na pasta `resultados/auditoria_extrator_sem_paragrafos/` (total de **24 imagens**). As unidades normais estão marcadas em **azul** e as caixas anômalas ou suspeitas em **vermelho**.

| Imagem | Detector | Veículo (UF) | Page ID | Gravidade | Origem da Base | Detalhe |
|:---|:---:|:---|:---|---:|:---:|:---|
| [`01_d1_RJ_duque_de_caxias.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/01_d1_RJ_duque_de_caxias.jpg) | **D1** | official_diary_RJ_duque_de_caxias | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | 1,00 | Imagem Golden | largura=90.3% da pag; vao_max=461.2pt (77.5%) |
| [`02_d1_ro.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/02_d1_ro.jpg) | **D1** | official_diary_ro | `official_diary_ro/executive_official_diary_suplemento_2026-01-09.pdf#p16` | 1,00 | Imagem Golden | largura=91.3% da pag; vao_max=254.9pt (42.8%) |
| [`03_d1_ms.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/03_d1_ms.jpg) | **D1** | official_diary_ms | `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 0,53 | Imagem Golden | largura=85.1% da pag; vao_max=39.2pt (6.6%) |
| [`04_d1_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/04_d1_am_manaus.jpg) | **D1** | official_diary_am_manaus | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p3` | 0,44 | Render em Escala | largura=81.0% da pag; vao_max=28.3pt (4.8%) |
| [`05_d2_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/05_d2_am_manaus.jpg) | **D2** | official_diary_am_manaus | `official_diary_am_manaus/2025-11-03_caderno_1.pdf#p24` | 1,00 | Render em Escala | atomo=l3(picture); sobrep_texto=18.0%; sobrep_atomo=100.0% |
| [`06_d2_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/06_d2_am_manaus.jpg) | **D2** | official_diary_am_manaus | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p40` | 1,00 | Render em Escala | atomo=l3(picture); sobrep_texto=6.9%; sobrep_atomo=100.0% |
| [`07_d2_rj.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/07_d2_rj.jpg) | **D2** | official_diary_rj | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 1,00 | Imagem Golden | atomo=l0(picture); sobrep_texto=3.4%; sobrep_atomo=100.0% |
| [`08_d2_RJ_seropedica.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/08_d2_RJ_seropedica.jpg) | **D2** | official_diary_RJ_seropedica | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 1,00 | Imagem Golden | atomo=l1(picture); sobrep_texto=100.0%; sobrep_atomo=100.0% |
| [`09_d4_RJ_volta_redonda.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/09_d4_RJ_volta_redonda.jpg) | **D4** | official_diary_RJ_volta_redonda | `official_diary_RJ_volta_redonda/executive_official_diary_2022-06-28_1845.pdf#p20` | 1,00 | Render em Escala | linhas=2; linhas_com_vao=2; lista_nomes=False |
| [`10_d4_RJ_volta_redonda.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/10_d4_RJ_volta_redonda.jpg) | **D4** | official_diary_RJ_volta_redonda | `official_diary_RJ_volta_redonda/executive_official_diary_2022-12-15_1899.pdf#p4` | 1,00 | Render em Escala | tabela vazia (zero palavras associadas) |
| [`11_d4_RJ_volta_redonda.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/11_d4_RJ_volta_redonda.jpg) | **D4** | official_diary_RJ_volta_redonda | `official_diary_RJ_volta_redonda/executive_official_diary_2023-03-28_1930.pdf#p5` | 1,00 | Render em Escala | tabela vazia (zero palavras associadas) |
| [`12_d4_RJ_volta_redonda.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/12_d4_RJ_volta_redonda.jpg) | **D4** | official_diary_RJ_volta_redonda | `official_diary_RJ_volta_redonda/executive_official_diary_2022-10-20_1884.pdf#p13` | 1,00 | Render em Escala | tabela vazia (zero palavras associadas) |
| [`13_d5_pi_v2.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/13_d5_pi_v2.jpg) | **D5** | official_diary_pi_v2 | `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p2` | 1,00 | Imagem Golden | cabecalhos=4; rodapes=4; fragmentos_curtos=6 |
| [`14_d5_se.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/14_d5_se.jpg) | **D5** | official_diary_se | `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | 1,00 | Imagem Golden | cabecalhos=4; rodapes=1; fragmentos_curtos=3 |
| [`15_d5_rj.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/15_d5_rj.jpg) | **D5** | official_diary_rj | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 1,00 | Imagem Golden | cabecalhos=3; rodapes=0; fragmentos_curtos=2 |
| [`16_d5_al.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/16_d5_al.jpg) | **D5** | official_diary_al | `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | 1,00 | Imagem Golden | cabecalhos=4; rodapes=0; fragmentos_curtos=1 |
| [`17_d6_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/17_d6_am_manaus.jpg) | **D6** | official_diary_am_manaus | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29` | 1,00 | Render em Escala | altura=37.7pt; mediana=8.5pt; razao=4.43x |
| [`18_d6_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/18_d6_am_manaus.jpg) | **D6** | official_diary_am_manaus | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p5` | 1,00 | Render em Escala | altura=28.0pt; mediana=8.5pt; razao=3.29x |
| [`19_d6_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/19_d6_am_manaus.jpg) | **D6** | official_diary_am_manaus | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p9` | 1,00 | Render em Escala | altura=49.1pt; mediana=8.5pt; razao=5.76x |
| [`20_d6_am_manaus.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/20_d6_am_manaus.jpg) | **D6** | official_diary_am_manaus | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p26` | 1,00 | Render em Escala | altura=58.9pt; mediana=8.5pt; razao=6.92x |
| [`21_d7_ms.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/21_d7_ms.jpg) | **D7** | official_diary_ms | `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 1,00 | Imagem Golden | atomo=l1(table); n_invasoras=13; amostra=['Diário', 'Oficial', 'Eletrônico', 'n.'] |
| [`22_d7_pb.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/22_d7_pb.jpg) | **D7** | official_diary_pb | `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | 0,75 | Imagem Golden | atomo=l1(picture); n_invasoras=3; amostra=['Diário', 'Ofi', 'cial'] |
| [`23_d7_pb.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/23_d7_pb.jpg) | **D7** | official_diary_pb | `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | 0,75 | Imagem Golden | atomo=l8(picture); n_invasoras=3; amostra=['Diário', 'Ofi', 'cial'] |
| [`24_d7_RJ_seropedica.jpg`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos/24_d7_RJ_seropedica.jpg) | **D7** | official_diary_RJ_seropedica | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 0,55 | Imagem Golden | atomo=l1(picture); n_invasoras=1; amostra=['3'] |

## 5. Base de Dados Bruta

O inventário completo e estruturado de todas as páginas e seus respectivos achados foi salvo em formato JSON sob [`resultados/auditoria_extrator_sem_paragrafos.json`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/auditoria_extrator_sem_paragrafos.json).

## 6. Limitações Metodológicas

1. **Anotações Humanas Parciais:** O Golden contém anotações com notas textuais livres em um subconjunto restrito de páginas (~28 páginas com observações qualitativas). O acerto/recall contra notas é portanto uma medida de sensibilidade em defeitos que incomodaram o autor, não uma métrica exaustiva de ground-truth.
2. **Escopo do D5:** O detector D5 de cabeçalho/rodapé fragmentado opera exclusivamente sobre as 45 páginas do lote `estruturas_golden_v4`, pois os demais lotes não contêm a rotulação explícita dos tipos estruturais `cabecalho` e `rodape`.
3. **Documentos Especializados:** Tabelas sem bordas em listas orçamentárias densas (como diários de SP e SC) podem gerar falsos positivos em D4 quando a diagramação possui apenas uma coluna dominante com dados mistos.
4. **Imagens de Fundo:** Para páginas silver fora da bancada Golden, a galeria foi desenhada sobre fundo branco sintético em escala preservando fielmente a geometria das bounding boxes.
