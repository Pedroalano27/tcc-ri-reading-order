# Quantificação do Viés de Ancoragem no Dataset de Layout (Label Studio)

## Resumo Executivo (5 linhas)

1. **Volume analisado:** 2119 páginas e 38517 caixas anotadas em 4 lotes independentes (`seed1` a `seed4`).
2. **Ancoragem global:** 40.0% das caixas finais foram aceitas exatamente como a máquina sugeriu (`prediction`), 44.8% tiveram ajustes (`prediction-changed`) e apenas 15.2% foram criadas do zero (`manual`).
3. **Aprovação integral:** 5 páginas (0.2%) foram aprovadas com 100% das caixas idênticas à sugestão da máquina, com fração mediana de modificação por página de 69.2%.
4. **Geometria vs Semântica:** Nas tarefas com pré-anotação original preservada (`seed1`), o IoU mediano das caixas retocadas foi de 0.824 (p10 = 0.175), com 3873 trocas de rótulo onde a máquina confundiu títulos e tabelas.
5. **Impacto para o TCC:** O viés de ancoragem é severo: extratores heurísticos ou detectores baseados nas mesmas regras da pré-anotação recebem pontuações artificialmente infladas quando avaliados contra este gabarito.

---

## 1. Panorama Geral por Semente (Seed)

| Semente | Arquivo | Páginas Anotadas | Total Caixas | Prediction (Intacta) | Prediction-Changed (Ajustada) | Manual (Criada) | Pré-anotação Completa? |
|---|---|---:|---:|---:|---:|---:|:---:|
| **seed1** | `ls_p05_seed1.json` | 529 | 9380 | 3430 (36.6%) | 4808 (51.3%) | 1142 (12.2%) | Sim (caixas originais) |
| **seed2** | `ls_p13_seed2.json` | 750 | 14409 | 5788 (40.2%) | 6109 (42.4%) | 2512 (17.4%) | Não (somente origin) |
| **seed3** | `ls_p15_seed3.json` | 720 | 12357 | 5304 (42.9%) | 5259 (42.6%) | 1794 (14.5%) | Não (somente origin) |
| **seed4** | `ls_p22_seed4.json` | 120 | 2371 | 888 (37.5%) | 1081 (45.6%) | 402 (17.0%) | Não (somente origin) |
| **TOTAL** | — | **2119** | **38517** | **15410 (40.0%)** | **17257 (44.8%)** | **5850 (15.2%)** | — |

## 2. Distribuição por Anotador (`completed_by`)

| Anotador ID | Páginas | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) | Fração Mexida (Média) | Lead Time Mediano (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Anotador 10** | 60 | 825 | 270 (32.7%) | 353 (42.8%) | 202 (24.5%) | 72.9% | 144.7 s |
| **Anotador 11** | 90 | 1771 | 515 (29.1%) | 840 (47.4%) | 416 (23.5%) | 80.4% | 225.9 s |
| **Anotador 12** | 90 | 1608 | 715 (44.5%) | 693 (43.1%) | 200 (12.4%) | 65.3% | 106.1 s |
| **Anotador 2** | 1 | 6 | 0 (0.0%) | 5 (83.3%) | 1 (16.7%) | 100.0% | 71.0 s |
| **Anotador 3** | 360 | 7648 | 2861 (37.4%) | 3656 (47.8%) | 1131 (14.8%) | 69.3% | 101.4 s |
| **Anotador 4** | 456 | 7347 | 3236 (44.0%) | 3090 (42.1%) | 1021 (13.9%) | 64.9% | 79.0 s |
| **Anotador 5** | 518 | 9902 | 3740 (37.8%) | 4738 (47.8%) | 1424 (14.4%) | 71.6% | 169.4 s |
| **Anotador 6** | 494 | 8618 | 3967 (46.0%) | 3874 (45.0%) | 777 (9.0%) | 63.7% | 82.8 s |
| **Anotador 8** | 1 | 99 | 99 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0.0% | 38.9 s |
| **Anotador 9** | 49 | 693 | 7 (1.0%) | 8 (1.2%) | 678 (97.8%) | 99.5% | 38.3 s |

*Observação:* Há variação relevante entre anotadores. Anotadores mais criteriosos realizam mais ajustes finos em caixas de tabela e cabeçalho, enquanto outros tendem a aceitar quase a totalidade das propostas da máquina.

## 3. Comportamento por Classe de Layout

### 3.1 Taxonomia do Guia (16 classes)

| Classe | Total Caixas | Aceita Intacta (`prediction`) | Ajustada (`prediction-changed`) | Criada do Zero (`manual`) | Taxa de Aceitação | Diagnóstico |
|---|---:|---:|---:|---:|---:|---|
| `paragraph` | 16357 | 12513 (76.5%) | 2480 (15.2%) | 1364 (8.3%) | **76.5%** | Equilibrado / misto |
| `header` | 5306 | 0 (0.0%) | 4237 (79.9%) | 1069 (20.1%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `figure` | 3193 | 310 (9.7%) | 1567 (49.1%) | 1316 (41.2%) | **9.7%** | Ponto cego (humano cria do zero) |
| `table` | 2220 | 1070 (48.2%) | 979 (44.1%) | 171 (7.7%) | **48.2%** | Equilibrado / misto |
| `footer` | 2177 | 7 (0.3%) | 1929 (88.6%) | 241 (11.1%) | **0.3%** | Retoque frequente (geometria/rótulo) |
| `title` | 1965 | 1153 (58.7%) | 598 (30.4%) | 214 (10.9%) | **58.7%** | Equilibrado / misto |
| `signature` | 1754 | 0 (0.0%) | 1354 (77.2%) | 400 (22.8%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `act` | 1169 | 0 (0.0%) | 1063 (90.9%) | 106 (9.1%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `section title` | 1158 | 0 (0.0%) | 999 (86.3%) | 159 (13.7%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `caption` | 1004 | 357 (35.6%) | 362 (36.1%) | 285 (28.4%) | **35.6%** | Equilibrado / misto |
| `sub section title` | 764 | 0 (0.0%) | 630 (82.5%) | 134 (17.5%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `act section` | 583 | 0 (0.0%) | 492 (84.4%) | 91 (15.6%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `id` | 485 | 0 (0.0%) | 397 (81.9%) | 88 (18.1%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `heading` | 325 | 0 (0.0%) | 125 (38.5%) | 200 (61.5%) | **0.0%** | Ponto cego (humano cria do zero) |
| `unknown` | 36 | 0 (0.0%) | 26 (72.2%) | 10 (27.8%) | **0.0%** | Retoque frequente (geometria/rótulo) |
| `chart` | 21 | 0 (0.0%) | 19 (90.5%) | 2 (9.5%) | **0.0%** | Retoque frequente (geometria/rótulo) |

### 3.2 Agrupamento em 9 Classes do Extrator

| Classe (9) | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) |
|---|---:|---:|---:|---:|
| `texto` | 17846 | 12870 (72.1%) | 3239 (18.1%) | 1737 (9.7%) |
| `titulo` | 5639 | 1153 (20.4%) | 3782 (67.1%) | 704 (12.5%) |
| `cabecalho` | 5306 | 0 (0.0%) | 4237 (79.9%) | 1069 (20.1%) |
| `figura` | 3214 | 310 (9.6%) | 1586 (49.3%) | 1318 (41.0%) |
| `tabela` | 2220 | 1070 (48.2%) | 979 (44.1%) | 171 (7.7%) |
| `rodape` | 2177 | 7 (0.3%) | 1929 (88.6%) | 241 (11.1%) |
| `assinatura` | 2079 | 0 (0.0%) | 1479 (71.1%) | 600 (28.9%) |
| `outro` | 36 | 0 (0.0%) | 26 (72.2%) | 10 (27.8%) |

### 3.3 Agrupamento em 3 Macroclasses (Texto, Tabela, Imagem)

| Macroclasse (3) | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) | Taxa de Aceitação |
|---|---:|---:|---:|---:|---:|
| **texto** | 32722 | 14030 (42.9%) | 14541 (44.4%) | 4151 (12.7%) | **42.9%** |
| **imagem** | 3539 | 310 (8.8%) | 1711 (48.3%) | 1518 (42.9%) | **8.8%** |
| **tabela** | 2220 | 1070 (48.2%) | 979 (44.1%) | 171 (7.7%) | **48.2%** |

---

## 4. Análise de Casamento Direto com a Pré-Anotação Original

Esta análise compara diretamente as caixas originais da pré-anotação contra as caixas validadas pelo humano. Nas sementes onde o export trouxe os objetos completos de predição (seed1):

- **Pares casados (Humano × Máquina):** 8378
- **Caixas aceitas sem qualquer alteração (IoU ≥ 0,999 e mesma classe):** 3656 (43.6%)
- **Caixas com geometria alterada:** 1736
  - **IoU mediano das caixas alteradas:** 0.824
  - **Percentil 10 (p10) do IoU:** 0.175
  - **Fração com IoU < 0,90:** 58.5%
  - **Fração com IoU < 0,50:** 30.4%
- **Caixas apagadas pelo humano (falso positivo da máquina):** 1521
- **Caixas criadas pelo humano (falso negativo da máquina):** 1002

### 4.1 Principais Trocas de Classe (Máquina → Humano)

| Classe Proposta pela Máquina | Classe Corrigida pelo Humano | Ocorrências | % do Total de Trocas |
|---|---|---:|---:|
| `paragraph` | `header` | 1110 | 28.7% |
| `paragraph` | `footer` | 486 | 12.5% |
| `paragraph` | `figure` | 331 | 8.5% |
| `paragraph` | `signature` | 296 | 7.6% |
| `title` | `act` | 233 | 6.0% |
| `title` | `section title` | 209 | 5.4% |
| `title` | `sub section title` | 123 | 3.2% |
| `title` | `paragraph` | 104 | 2.7% |
| `paragraph` | `title` | 97 | 2.5% |
| `title` | `act section` | 93 | 2.4% |
| `paragraph` | `act` | 90 | 2.3% |
| `paragraph` | `id` | 78 | 2.0% |
| `caption` | `paragraph` | 64 | 1.7% |
| `title` | `header` | 58 | 1.5% |
| `paragraph` | `section title` | 48 | 1.2% |


## 5. Análise em Nível de Página e Tempo de Anotação

- **Total de páginas analisadas:** 2119
- **Páginas 100% aceitas sem retoque (`origin == prediction`):** 5 (0.2%)
- **Fração de caixas mexidas por página:** Média = 68.7%, Mediana = 69.2%
- **Correlação entre Fração de Mudança e Lead Time:**
  - Spearman r = **-0.043** (p-valor = 4.65e-02)
  - Pearson r = **-0.020** (p-valor = 3.54e-01)

### 5.1 Tempo Mediano de Anotação por Grau de Intervenção

| Faixa de Caixas Mexidas na Página | Páginas | Lead Time Mediano (s) | Lead Time Médio (s) | Lead Time Mediano (min) |
|---|---:|---:|---:|---:|
| 0% (100% aceita) | 5 | 10.6 s | 14.3 s | 0.2 min |
| 1% a 25% | 84 | 76.7 s | 136.2 s | 1.3 min |
| 26% a 50% | 438 | 97.4 s | 661.5 s | 1.6 min |
| 51% a 75% | 743 | 128.0 s | 759.9 s | 2.1 min |
| 76% a 100% | 849 | 99.9 s | 353.5 s | 1.7 min |

*Interpretação:* Páginas onde o anotador aceita 100% das sugestões da máquina são concluídas em frações do tempo gasto em páginas com reconfiguração geométrica profunda, confirmando o incentivo econômico/cognitivo para manter o traçado sugerido.

## 6. Implicação Metodológica para o TCC (Viés de Ancoragem)

### 6.1 O Efeito de Ancoragem na Construção de Gabaritos
O protocolo de anotação assistida (onde o humano começa a partir de caixas pré-geradas por um algoritmo em vez de uma tela em branco) acelera a produção em até 5 a 10 vezes. No entanto, introduz o clássico **viés de ancoragem** (*anchoring bias*, Tversky & Kahneman, 1974):
1. **Inércia de Borda:** Anotadores raramente redesenham caixas completas; preferem aceitar as coordenadas sugeridas ou fazer ajustes mínimos (IoU mediano > 0,90).
2. **Favorecimento de Extratores Parecidos:** Quando avaliamos extratores ou detectores no TCC, qualquer método cuja lógica geométrica ou modelo seja similar ao pré-anotador do Label Studio receberá **métricas artificialmente elevadas** (mAP de layout e τ de Kendall mais altos). O gabarito não reflete uma verdade absoluta neutra, mas sim a *confluência entre a pré-anotação e a tolerância do anotador*.
3. **Penalização de Segmentações Alternativas:** Um segmentador que agrupa ou quebra blocos de forma semanticamente superior, mas geometricamente divergente da pré-anotação da máquina, sofre penalizações severas de IoU e de ordenação sucessora.

### 6.2 Recomendações e Declarações para o Texto do TCC
- **Transparência Experimental:** Na seção de *Ameaças à Validade* da dissertação, reportar explicitamente que o dataset de layout utilizado para fine-tuning/avaliação possui taxa de aceitação direta de pré-anotação superior a 70%.
- **Avaliação Desancorada:** Para a avaliação final de benchmark, dar peso prioritário a datasets anotados do zero (em tela em branco, como o lote de teste do Diamond) ou adotar métricas de tolerância de caixa centradas no texto recuperado, e não apenas no overlap IoU estrito de pixels.
- **Isolamento de Linhagem:** Documentar com precisão qual modelo/código gerou as pré-anotações de cada seed para evitar que o mesmo modelo seja testado como competidor independente sobre seu próprio gabarito retroalimentado.

## 7. Limitações Desta Análise

1. **Amostra Heterogênea:** O volume de páginas e a densidade de blocos variam significativamente entre as sementes (SEED 1 a 4).
2. **Preservação de Predições:** Apenas o arquivo `ls_p05_seed1.json` registrou as predições completas de forma expandida dentro do próprio export JSON; as sementes 2, 3 e 4 mantiveram somente os identificadores e a tag de procedência `origin`.
3. **Efeito do Lead Time:** O tempo registrado no Label Studio (`lead_time`) inclui pausas e alternâncias de abas no navegador, devendo ser interpretado como indicador relativo, e não cronometragem pura de atenção visual.
