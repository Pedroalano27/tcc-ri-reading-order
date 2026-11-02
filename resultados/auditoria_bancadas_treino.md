# Auditoria de Bancadas de Avaliação vs. Treino

*Data da auditoria*: 2026-10-04 23:44:48  
*Ambiente*: Python 3.11.9 no Windows | Validação estrita por biblioteca padrão  
*Critério de exclusão*: Todo `page_id` de treino cujo PDF (`<veiculo>/<arquivo.pdf>`) aparece nas bancadas humanas.

---

## Resumo Executivo (4 Linhas)

1. **Sobreposição exata de `page_id`**: Sim, há 6 ocorrência(s) de page_id repetido entre treino e medição (bancada A: 6).
2. **Sobreposição de PDF (mesmo documento)**: Sim, há 6 caso(s) de sobreposição de PDF entre treino e medição (bancada A: 6 PDF(s)), apresentando vazamento de template/documento intra-PDF.
3. **Páginas humanas em veículos vistos no treino**: Bancada A (golden_v4): 6 de 45 páginas (13,3%) são de veículos vistos no treino (39 em não vistos); Bancada B nova (golden_v3 fora do v4): 0 de 27 páginas (0,0%) são de veículos vistos no treino (27 em não vistos).
4. **Isolamento limpo para o treino**: O orquestrador deve excluir exatamente 36 páginas do conjunto de treino (cujos PDFs pertencem a alguma bancada humana), listadas em resultados/auditoria_excluir_do_treino.txt.

---

## 1. Visão Geral dos Conjuntos

Contagem de páginas únicas (`page_id`), documentos PDF distintos (`<veiculo>/<arquivo>`) e veículos distintos em cada partição:

| Conjunto | Páginas (`page_id`) | PDFs Distintos | Veículos Distintos | Fontes Analisadas |
|---|---:|---:|---:|---|
| **Treino Total** (base + extra) | **3.189** | **741** | **7** | `data/processed/blocos/` (7 UFs) + `data/processed/blocos_extra/` |
| └─ Treino Base | 152 | 57 | 7 | `data/processed/blocos/<veiculo>.jsonl` dos 7 veículos em `splits.json` |
| └─ Treino Extra | 3.071 | 730 | 7 | Todos os arquivos em `data/processed/blocos_extra/*.jsonl` |
| **Validação Silver** | 15 | 6 | 1 | `data/processed/blocos/<veiculo>.jsonl` (RN) |
| **Teste Silver** | 89 | 31 | 3 | `data/processed/blocos/<veiculo>.jsonl` (CE, MA, RJ) |
| **Bancada Humana A** (Golden v4) | 45 | 43 | 28 | `data/golden/golden_v4/tarefas.jsonl` (45 tarefas) |
| **Bancada Humana B Nova** (Golden v3 fora do v4) | 27 | 26 | 10 | `data/golden/_avaliacao/golden_v3/tarefas.jsonl` (excluídas as 20 do v4) |
| *Referência*: Bancada Humana B Completa (Golden v3 total) | 47 | 42 | 19 | `data/golden/_avaliacao/golden_v3/tarefas.jsonl` (47 tarefas completas) |

> [!NOTE]
> O conjunto de treino apresentou **34** repetições internas de registros entre base e extra (total de 3223 registros para 3189 páginas únicas).

---

## 2. Sobreposição Exata de `page_id` entre Treino e Medição

Uma sobreposição exata de `page_id` significa que a exata mesma página usada para avaliar um modelo também estava presente no lote de treino.

### 2.1 Treino vs. Validação Silver
✅ **0 páginas repetidas**. Separação estrita garantida por veículo (`official_diary_rn`).

### 2.2 Treino vs. Teste Silver
✅ **0 páginas repetidas**. Separação estrita garantida por veículo (`official_diary_ce`, `official_diary_ma`, `official_diary_rj`).

### 2.3 Treino vs. Bancada Humana A (Golden v4)
⚠️ **6 página(s) com page_id idêntico no treino**:
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` (Origem no treino: blocos/official_diary_RJ_volta_redonda.jsonl)
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` (Origem no treino: blocos_extra/official_diary_ba_salvador.jsonl)
- `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` (Origem no treino: blocos_extra/official_diary_pe.jsonl)
- `official_diary_pr/executive_official_diary_2021-11-26.pdf#p66` (Origem no treino: blocos_extra/official_diary_pr.jsonl)
- `official_diary_rr/2021-09-23_DiarioRR.pdf#p10` (Origem no treino: blocos_extra/official_diary_rr.jsonl)
- `official_diary_sc/2023-11-27_22151.pdf#p28` (Origem no treino: blocos_extra/official_diary_sc.jsonl)

### 2.4 Treino vs. Bancada Humana B Nova (Golden v3 fora do v4)
✅ **0 páginas repetidas**.

### 2.5 Treino vs. Bancada Humana B Total (Golden v3 completo)
✅ **0 páginas repetidas**.

---

## 3. Sobreposição de PDFs (Mesmo Veículo e Mesmo Arquivo)

Esta análise audita o vazamento em nível de documento: casos onde o treino e a bancada de teste compartilham o mesmo arquivo PDF físico, seja na mesma página ou em páginas distintas.

### 3.1 Treino vs. Validação Silver
✅ **Nenhum PDF compartilhado** entre treino e Validação Silver.

### 3.2 Treino vs. Teste Silver
✅ **Nenhum PDF compartilhado** entre treino e Teste Silver.

### 3.3 Treino vs. Bancada Humana A (Golden v4)
⚠️ Foram identificados **6 PDF(s) compartilhados** entre treino e Bancada Humana A (Golden v4):

| PDF Compartilhado (`<uf>/<arquivo>`) | Páginas no Treino | Páginas na Medição | Páginas Idênticas? | Páginas Distintas do Mesmo PDF? |
|---|---|---|---|---|
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | `#p1, #p14, #p15, #p16, #p17, #p18, #p2, #p4, #p8` | `#p16` | Sim | Sim |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | `#p16, #p18, #p26, #p27, #p5, #p7` | `#p5` | Sim | Sim |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | `#p2, #p3, #p4, #p5, #p6, #p7` | `#p6` | Sim | Sim |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf` | `#p12, #p34, #p4, #p66, #p69` | `#p66` | Sim | Sim |
| `official_diary_rr/2021-09-23_DiarioRR.pdf` | `#p10, #p13, #p30, #p5, #p61` | `#p10` | Sim | Sim |
| `official_diary_sc/2023-11-27_22151.pdf` | `#p28, #p29, #p42, #p45, #p7` | `#p28` | Sim | Sim |

### 3.4 Treino vs. Bancada Humana B Nova (Golden v3 fora do v4)
✅ **Nenhum PDF compartilhado** entre treino e Bancada Humana B Nova.

### 3.5 Treino vs. Bancada Humana B Total (Golden v3 completo)
✅ **Nenhum PDF compartilhado** entre treino e Bancada Humana B Total.

---

## 4. Distribuição por Veículo nas Bancadas Humanas

Mostra a proporção de páginas originárias de veículos que faziam parte do conjunto de treino versus veículos inéditos (zero-shot de veículo/layout).

#### Bancada Humana A (Golden v4 — 45 tarefas)

| Veículo (`uf`) | Páginas | Proporção | Papel no `splits.json` | Visto no Treino? |
|---|---:|---:|---|---|
| `official_diary_MG_congonhas` | 2 | 4,4% | não confiável | Não |
| `official_diary_RJ_barra_do_pirai` | 3 | 6,7% | não confiável | Não |
| `official_diary_RJ_duque_de_caxias` | 2 | 4,4% | não confiável | Não |
| `official_diary_RJ_seropedica` | 2 | 4,4% | não confiável | Não |
| `official_diary_RJ_volta_redonda` | 1 | 2,2% | treino | **Sim** |
| `official_diary_ac` | 2 | 4,4% | não confiável | Não |
| `official_diary_al` | 3 | 6,7% | não confiável | Não |
| `official_diary_am_manaus` | 1 | 2,2% | não confiável | Não |
| `official_diary_ap` | 2 | 4,4% | não confiável | Não |
| `official_diary_ba_salvador` | 1 | 2,2% | treino | **Sim** |
| `official_diary_ce` | 1 | 2,2% | teste | Não |
| `official_diary_ma` | 1 | 2,2% | teste | Não |
| `official_diary_mg` | 1 | 2,2% | não confiável | Não |
| `official_diary_ms` | 2 | 4,4% | não confiável | Não |
| `official_diary_pb` | 2 | 4,4% | não confiável | Não |
| `official_diary_pe` | 1 | 2,2% | treino | **Sim** |
| `official_diary_pi_v2` | 2 | 4,4% | não confiável | Não |
| `official_diary_pr` | 1 | 2,2% | treino | **Sim** |
| `official_diary_pr_curitiba` | 1 | 2,2% | não confiável | Não |
| `official_diary_rj` | 1 | 2,2% | teste | Não |
| `official_diary_rj_japeri` | 2 | 4,4% | não confiável | Não |
| `official_diary_rn` | 1 | 2,2% | validacao | Não |
| `official_diary_ro` | 2 | 4,4% | não confiável | Não |
| `official_diary_rr` | 1 | 2,2% | treino | **Sim** |
| `official_diary_rs_porto_alegre` | 2 | 4,4% | não confiável | Não |
| `official_diary_sc` | 1 | 2,2% | treino | **Sim** |
| `official_diary_se` | 2 | 4,4% | não confiável | Não |
| `official_diary_to` | 2 | 4,4% | não confiável | Não |
|---|---:|---:|---|---|
| **TOTAL EM VEÍCULOS VISTOS NO TREINO** | **6** | **13,3%** | — | **SIM** |
| **TOTAL EM VEÍCULOS NÃO VISTOS NO TREINO** | **39** | **86,7%** | — | **NÃO** |
| **TOTAL GERAL DA BANCADA** | **45** | **100,0%** | — | — |

#### Bancada Humana B Nova (Golden v3 fora do v4 — 27 tarefas)

| Veículo (`uf`) | Páginas | Proporção | Papel no `splits.json` | Visto no Treino? |
|---|---:|---:|---|---|
| `official_diary_RJ_barra_do_pirai` | 1 | 3,7% | não confiável | Não |
| `official_diary_ac` | 2 | 7,4% | não confiável | Não |
| `official_diary_ap` | 1 | 3,7% | não confiável | Não |
| `official_diary_ce` | 6 | 22,2% | teste | Não |
| `official_diary_ma` | 7 | 25,9% | teste | Não |
| `official_diary_mg` | 1 | 3,7% | não confiável | Não |
| `official_diary_pi_v2` | 2 | 7,4% | não confiável | Não |
| `official_diary_rj` | 5 | 18,5% | teste | Não |
| `official_diary_ro` | 1 | 3,7% | não confiável | Não |
| `official_diary_se` | 1 | 3,7% | não confiável | Não |
|---|---:|---:|---|---|
| **TOTAL EM VEÍCULOS VISTOS NO TREINO** | **0** | **0,0%** | — | **SIM** |
| **TOTAL EM VEÍCULOS NÃO VISTOS NO TREINO** | **27** | **100,0%** | — | **NÃO** |
| **TOTAL GERAL DA BANCADA** | **27** | **100,0%** | — | — |

#### Referência: Bancada Humana B Total (Golden v3 completo — 47 tarefas)

| Veículo (`uf`) | Páginas | Proporção | Papel no `splits.json` | Visto no Treino? |
|---|---:|---:|---|---|
| `official_diary_MG_congonhas` | 1 | 2,1% | não confiável | Não |
| `official_diary_RJ_barra_do_pirai` | 3 | 6,4% | não confiável | Não |
| `official_diary_RJ_duque_de_caxias` | 1 | 2,1% | não confiável | Não |
| `official_diary_RJ_seropedica` | 1 | 2,1% | não confiável | Não |
| `official_diary_ac` | 3 | 6,4% | não confiável | Não |
| `official_diary_al` | 1 | 2,1% | não confiável | Não |
| `official_diary_ap` | 2 | 4,3% | não confiável | Não |
| `official_diary_ce` | 7 | 14,9% | teste | Não |
| `official_diary_ma` | 8 | 17,0% | teste | Não |
| `official_diary_mg` | 2 | 4,3% | não confiável | Não |
| `official_diary_ms` | 1 | 2,1% | não confiável | Não |
| `official_diary_pb` | 1 | 2,1% | não confiável | Não |
| `official_diary_pi_v2` | 3 | 6,4% | não confiável | Não |
| `official_diary_rj` | 6 | 12,8% | teste | Não |
| `official_diary_rj_japeri` | 1 | 2,1% | não confiável | Não |
| `official_diary_ro` | 2 | 4,3% | não confiável | Não |
| `official_diary_rs_porto_alegre` | 1 | 2,1% | não confiável | Não |
| `official_diary_se` | 2 | 4,3% | não confiável | Não |
| `official_diary_to` | 1 | 2,1% | não confiável | Não |
|---|---:|---:|---|---|
| **TOTAL EM VEÍCULOS VISTOS NO TREINO** | **0** | **0,0%** | — | **SIM** |
| **TOTAL EM VEÍCULOS NÃO VISTOS NO TREINO** | **47** | **100,0%** | — | **NÃO** |
| **TOTAL GERAL DA BANCADA** | **47** | **100,0%** | — | — |

---

## 5. Instruções de Isolamento para o Orquestrador

Para que o benchmark e os testes dos ordenadores reflitam capacidades de generalização puras e sem vazamento intra-documento, recomenda-se que o orquestrador filtre o lote de treino.

Arquivo gerado: [`resultados/auditoria_excluir_do_treino.txt`](resultados/auditoria_excluir_do_treino.txt)  
Total de páginas a excluir do treino: **36**

### Detalhamento das Páginas de Treino a Excluir:

| `page_id` de Treino a Excluir | PDF Compartilhado com Bancada Humana | Presente em qual Bancada Humana? |
|---|---|---|
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p1` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p14` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p15` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p17` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p18` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p2` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p4` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p8` | `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p16` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p18` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p26` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p27` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p7` | `official_diary_ba_salvador/dom-8379-27-09-2022.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p2` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p3` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p4` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p5` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p7` | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf` | Golden v4 |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf#p12` | `official_diary_pr/executive_official_diary_2021-11-26.pdf` | Golden v4 |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf#p34` | `official_diary_pr/executive_official_diary_2021-11-26.pdf` | Golden v4 |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf#p4` | `official_diary_pr/executive_official_diary_2021-11-26.pdf` | Golden v4 |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf#p66` | `official_diary_pr/executive_official_diary_2021-11-26.pdf` | Golden v4 |
| `official_diary_pr/executive_official_diary_2021-11-26.pdf#p69` | `official_diary_pr/executive_official_diary_2021-11-26.pdf` | Golden v4 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p10` | `official_diary_rr/2021-09-23_DiarioRR.pdf` | Golden v4 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p13` | `official_diary_rr/2021-09-23_DiarioRR.pdf` | Golden v4 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p30` | `official_diary_rr/2021-09-23_DiarioRR.pdf` | Golden v4 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p5` | `official_diary_rr/2021-09-23_DiarioRR.pdf` | Golden v4 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p61` | `official_diary_rr/2021-09-23_DiarioRR.pdf` | Golden v4 |
| `official_diary_sc/2023-11-27_22151.pdf#p28` | `official_diary_sc/2023-11-27_22151.pdf` | Golden v4 |
| `official_diary_sc/2023-11-27_22151.pdf#p29` | `official_diary_sc/2023-11-27_22151.pdf` | Golden v4 |
| `official_diary_sc/2023-11-27_22151.pdf#p42` | `official_diary_sc/2023-11-27_22151.pdf` | Golden v4 |
| `official_diary_sc/2023-11-27_22151.pdf#p45` | `official_diary_sc/2023-11-27_22151.pdf` | Golden v4 |
| `official_diary_sc/2023-11-27_22151.pdf#p7` | `official_diary_sc/2023-11-27_22151.pdf` | Golden v4 |

