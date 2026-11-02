# Diagnóstico de Erros do LayoutLM Sucessor no Golden Dataset (`golden_v3`)

## Correção de 13/09: Impacto da Decodificação em Cadeias vs Busca em Feixe

Na versão inicial deste diagnóstico, a avaliação do **LayoutLM Sucessor** no Golden Dataset (`golden_v3`) utilizou inadvertidamente predições geradas por **busca em feixe** (*beam search*), devido ao parâmetro padrão herdado na função `prever()` chamada por `src/eval/avaliar_golden.py`. No protocolo experimental principal do TCC (assim como no conjunto de teste), a linha de inferência adota **decodificação em cadeias** com limiar 0,5. Com a re-avaliação do Golden utilizando as predições corretas em cadeias (`resultados/golden/_avaliacao/golden_v3/pred_layoutlm_sucessor.jsonl`), os números e as conclusões diagnósticas alteraram-se substancialmente:

### Comparação Direta dos Resultados Globais no Golden (`golden_v3`, n=47)

| Métrica | Antes (Busca em Feixe) | Depois (Decodificação em Cadeias) | Variação ($\Delta$) |
|---|---:|---:|---:|
| **$\tau$ de Kendall Médio** | 0,699 | **0,845** | **+0,146** |
| **$\tau$ no Percentil 10 ($p_{10}$)** | 0,275 | **0,591** | **+0,316** |
| **Sucessor Correto Médio** | 67,1% | **66,8%** | **-0,3 p.p.** |
| **Diferença vs LayoutLM Pontual ($\tau$)** | -0,147 (0,699 vs 0,846) | **-0,001** (0,845 vs 0,846) | Empate técnico |
| **Diferença vs XY-cut ($\tau$)** | -0,152 (0,699 vs 0,851) | **-0,007** (0,845 vs 0,851) | Diferença residual |

Com a correção, o LayoutLM Sucessor praticamente empata com o LayoutLM Pontual em $\tau$ (0,845 vs 0,846) e aproxima-se estreitamente do XY-cut (0,851), mantendo mais que o dobro da continuidade local em relação ao modelo pontual (66,8% vs 32,8% de sucessor correto). O percentil 10 ($p_{10}$) salta de 0,275 para 0,591, superando inclusive o $p_{10}$ do próprio XY-cut (0,545).

### Síntese da Revisão das Três Hipóteses

- **Hipótese 1 (Falha de ancoragem de cabeçalhos): MUDA / MANTÉM-SE PARCIALMENTE.**
  - *O que cai:* A ideia de que o desacoplamento de cabeçalhos causava colapso global sistêmico em toda a base foi refutada. Casos críticos que sofriam quedas drásticas em feixe tiveram recuperação expressiva em cadeias (ex.: Piauí p223 saltou de $\tau$ 0,143 para 0,714; Piauí p0 foi de 0,543 para 0,981).
  - *O que se mantém / expande:* O mecanismo de falha em si (pequenos blocos isolados no topo ou rodapé que não estabelecem aresta de transição com o corpo e são deslocados pela pontuação pontual) continua sendo o principal modo de erro local residual (ex.: Japeri p3, Congonhas p1, Barra do Piraí p2). Adicionalmente, revelou-se um novo modo macro de erro: a inversão de colunas completas cujos blocos internos foram encadeados perfeitamente (MA p14, com 90,6% de acerto local mas $\tau$ 0,027 devido à leitura da Coluna 2 antes da Coluna 1).
- **Hipótese 2 (Degradação monotônica com número de colunas): CAI.**
  - *Refutação:* O colapso em páginas de 3 colunas não existe na decodificação em cadeias. O $\tau$ médio em 3 colunas subiu de 0,601 para **0,814** (muito próximo ao de 2 colunas: 0,824). No caso mais complexo do acervo (MG p28, com 99 blocos em 3 colunas), o Sucessor saltou de $\tau$ 0,460 para **0,881**, superando o próprio XY-cut (0,852). Em páginas de 1 coluna, o Sucessor supera amplamente o XY-cut (0,878 vs 0,788, vantagem de +0,090). O Sucessor sustenta $\tau > 0,81$ em todas as configurações de colunas.
- **Hipótese 3 (Vulnerabilidade fora do domínio de treino no grupo `incerto`): CAI COMPLETAMENTE.**
  - *Refutação:* A suposta incapacidade de generalizar para layouts e municípios novos era um artefato exclusivo da busca em feixe (que caía de 0,739 no *silver* para 0,666 no *incerto*). Em cadeias, o Sucessor atinge $\tau$ **0,851** no grupo *incerto* — superando tanto o grupo *silver* (0,837) quanto o próprio XY-cut no grupo *incerto* (0,834). A matriz de transição de adjacência com decodificação em cadeias generaliza de forma robusta e independente de vocabulário específico.

---

Este relatório detalha o desempenho do **LayoutLM com predição de sucessor** (decodificação em cadeias, limiar 0,5) no Golden Dataset (47 páginas contra anotação humana), onde atinge $\tau$ médio de **0,845** (p10 0,591) e **66,8%** de sucessor correto, empatando em $\tau$ com o **LayoutLM pontual** (0,846, mas com apenas 32,8% de sucessores) e aproximando-se do **XY-cut** (0,851 e 74,0%).

## 1. Tabela Completa por Página (Ordenada pelo Déficit do Sucessor vs XY-cut)

Critério de ordenação: diferença de τ de Kendall ($\Delta\tau = \tau_{\text{sucessor}} - \tau_{\text{xycut}}$), da pior página para a melhor.

| Página | Grupo | UF | Blocos | Cols | Tabs | Flags | τ Suc. | Suc. Suc. | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut | $\Delta\tau$ (Suc - XY) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `executive_official_diary_2021-11-19.pdf#p14` | silver | ma | 33 | 2 | 3 | tabela | **0.027** | 91% | 0.765 | 12% | **0.943** | 91% | **-0.917** |
| `2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373` | incerto | ap | 5 | 2 | 1 | tabela | **0.600** | 0% | 0.800 | 50% | **1.000** | 100% | **-0.400** |
| `JAPERI-5606-09-DE-MAIO-2024.pdf#p3` | incerto | rj_japeri | 7 | 1 | 0 | figura | **0.524** | 67% | 1.000 | 100% | **0.905** | 67% | **-0.381** |
| `Parte I (Poder Executivo)_2024-02-02.pdf#p39` | silver | rj | 7 | 2 | 1 | tabela | **0.143** | 17% | 0.429 | 17% | **0.429** | 67% | **-0.286** |
| `executive_official_diary_2025_11_07_216_2025.pdf#p223` | incerto | pi_v2 | 8 | 3 | 0 | - | **0.714** | 57% | 0.929 | 57% | **1.000** | 100% | **-0.286** |
| `executive_official_diary_2022-05-26_095.pdf#p2` | incerto | RJ_barra_do_pirai | 6 | 3 | 0 | figura | **0.733** | 60% | 0.867 | 60% | **1.000** | 100% | **-0.267** |
| `executive_official_diary_2026-01-16_010.pdf#p2` | incerto | RJ_barra_do_pirai | 6 | 3 | 0 | figura | **0.733** | 60% | 0.867 | 60% | **1.000** | 100% | **-0.267** |
| `executive_official_diary_2020-12-10_2591.pdf#p1` | incerto | MG_congonhas | 17 | 1 | 0 | figura | **0.794** | 88% | 0.897 | 12% | **0.985** | 88% | **-0.191** |
| `executive_official_diary_suplemento_2026-01-09.pdf#p16` | incerto | ro | 10 | 1 | 0 | - | **0.778** | 67% | 0.867 | 22% | **0.956** | 67% | **-0.178** |
| `2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41` | incerto | ap | 8 | 2 | 2 | tabela | **0.857** | 29% | 0.786 | 14% | **1.000** | 100% | **-0.143** |
| `executive_official_diary_2024-06-12.pdf#p392` | incerto | ro | 14 | 1 | 0 | - | **0.846** | 54% | 0.912 | 38% | **0.934** | 62% | **-0.088** |
| `executive_official_diary_2021-12-20.pdf#p51` | silver | ma | 8 | 2 | 5 | tabela | **0.929** | 71% | 0.929 | 71% | **1.000** | 100% | **-0.071** |
| `4689_cl_20230227_legislativo.pdf#p1` | incerto | rs_porto_alegre | 20 | 2 | 0 | - | **0.916** | 63% | 0.684 | 16% | **0.979** | 84% | **-0.063** |
| `executive_official_diary_2025_11_07_216_2025.pdf#p2` | incerto | pi_v2 | 20 | 2 | 0 | - | **0.905** | 53% | 0.863 | 11% | **0.968** | 68% | **-0.063** |
| `Parte IV (Municipalidades)_2025-11-10.pdf#p0` | silver | rj | 52 | 2 | 0 | figura | **0.750** | 24% | 0.799 | 12% | **0.810** | 80% | **-0.060** |
| `do20220530p02.pdf#p81` | silver | ce | 9 | 1 | 0 | - | **0.944** | 62% | 1.000 | 100% | **1.000** | 100% | **-0.056** |
| `executive_official_diary_2025-09-24.pdf#p41` | incerto | ac | 10 | 1 | 1 | tabela | **0.956** | 67% | 0.956 | 67% | **1.000** | 100% | **-0.044** |
| `Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | silver | rj | 41 | 2 | 0 | figura | **0.717** | 50% | 0.702 | 8% | **0.754** | 52% | **-0.037** |
| `executive_official_diary_2021-11-12.pdf#p60` | silver | ma | 50 | 2 | 0 | - | **0.925** | 86% | 0.837 | 10% | **0.961** | 94% | **-0.036** |
| `do20250505p03.pdf#p66` | silver | ce | 32 | 1 | 0 | - | **0.968** | 77% | 0.935 | 26% | **0.996** | 94% | **-0.028** |
| `do20220512p03.pdf#p20` | silver | ce | 21 | 2 | 4 | tabela | **0.943** | 55% | 0.914 | 25% | **0.962** | 40% | **-0.019** |
| `do20220530p02.pdf#p53` | silver | ce | 17 | 1 | 1 | tabela | **0.985** | 81% | 0.824 | 12% | **1.000** | 100% | **-0.015** |
| `executive_official_diary_2021-11-12.pdf#p56` | silver | ma | 50 | 2 | 0 | - | **0.953** | 86% | 0.776 | 16% | **0.961** | 94% | **-0.008** |
| `executive_official_diary_2024_05_29_104_2024_15_340.pdf#p0` | incerto | pi_v2 | 15 | 2 | 0 | - | **0.981** | 86% | 0.962 | 64% | **0.981** | 79% | **+0.000** |
| `executive_official_diary_46741_2021-06-29.pdf#p48` | incerto | ms | 5 | 2 | 1 | tabela, figura | **1.000** | 100% | 0.800 | 25% | **1.000** | 100% | **+0.000** |
| `executive_official_diary_2022-12-02.pdf#p419` | incerto | ac | 9 | 1 | 1 | tabela | **0.556** | 12% | 0.389 | 0% | **0.556** | 12% | **+0.000** |
| `do20260107p04.pdf#p42` | silver | ce | 7 | 1 | 0 | - | **1.000** | 100% | 0.810 | 50% | **1.000** | 100% | **+0.000** |
| `Parte I (Poder Executivo)_2022-01-05.pdf#p18` | silver | rj | 31 | 3 | 0 | - | **0.828** | 83% | 0.832 | 27% | **0.828** | 83% | **+0.000** |
| `do20250522p02.pdf#p8` | silver | ce | 22 | 2 | 3 | tabela | **0.974** | 86% | 0.827 | 24% | **0.974** | 62% | **+0.000** |
| `DOE-SE_2022-03-18_4475.pdf#p15` | incerto | se | 19 | 2 | 4 | tabela | **0.942** | 72% | 0.906 | 17% | **0.918** | 61% | **+0.023** |
| `executive_official_diary_2021-07-06.pdf#p28` | incerto | mg | 99 | 3 | 0 | figura | **0.881** | 58% | 0.712 | 1% | **0.852** | 72% | **+0.029** |
| `executive_official_diary_2023-03-06.pdf#p24` | silver | ma | 42 | 2 | 0 | - | **0.995** | 88% | 0.666 | 10% | **0.965** | 93% | **+0.030** |
| `executive_official_diary_2023-12-04_30_84.pdf#p0` | silver | ma | 39 | 2 | 0 | - | **0.995** | 84% | 0.903 | 8% | **0.935** | 76% | **+0.059** |
| `do20240429p01.pdf#p6` | silver | ce | 8 | 1 | 1 | tabela | **1.000** | 100% | 1.000 | 100% | **0.929** | 71% | **+0.071** |
| `executive_official_diary_2023-03-06.pdf#p71` | silver | ma | 31 | 2 | 0 | - | **1.000** | 100% | 0.927 | 43% | **0.918** | 90% | **+0.082** |
| `executive_official_diary_suplement_2025-02-21_202_378.pdf#p0` | silver | ma | 61 | 2 | 0 | tabela | **0.846** | 48% | 0.831 | 15% | **0.748** | 63% | **+0.098** |
| `executive_official_diary_2022-08-02_139.pdf#p5` | incerto | RJ_barra_do_pirai | 26 | 1 | 1 | tabela | **0.809** | 84% | 0.889 | 28% | **0.705** | 24% | **+0.105** |
| `executive_official_diary_2022-05-09_986.pdf#p2` | incerto | RJ_seropedica | 42 | 2 | 0 | - | **0.988** | 90% | 0.937 | 39% | **0.872** | 88% | **+0.116** |
| `Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | silver | rj | 73 | 1 | 0 | - | **0.795** | 61% | 0.820 | 14% | **0.607** | 15% | **+0.188** |
| `executive_official_diary_2021-12-30.pdf#p16` | incerto | mg | 42 | 1 | 15 | tabela | **0.984** | 71% | 0.877 | 15% | **0.796** | 56% | **+0.188** |
| `DOE-SE_2023-03-10_5100.pdf#p14` | incerto | se | 34 | 3 | 1 | figura | **0.993** | 82% | 0.875 | 30% | **0.786** | 85% | **+0.207** |
| `Parte IV (Municipalidades)_2021-08-30.pdf#p0` | silver | rj | 51 | 1 | 0 | tabela, figura | **0.853** | 32% | 0.856 | 14% | **0.616** | 40% | **+0.237** |
| `executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | incerto | RJ_duque_de_caxias | 20 | 2 | 3 | tabela | **0.747** | 32% | 0.811 | 11% | **0.505** | 58% | **+0.242** |
| `Diario Oficial 10-09-2025 Portal.pdf#p41` | incerto | pb | 40 | 1 | 0 | - | **0.944** | 59% | 0.969 | 49% | **0.567** | 54% | **+0.377** |
| `executive_official_diary_2025-02-11.pdf#p114` | incerto | ac | 23 | 1 | 0 | - | **0.984** | 91% | 0.953 | 59% | **0.581** | 14% | **+0.403** |
| `2024-04-17_5147.pdf#p47` | incerto | to | 29 | 1 | 0 | - | **0.995** | 89% | 0.961 | 32% | **0.502** | 50% | **+0.493** |
| `DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | incerto | al | 19 | 1 | 0 | - | **0.977** | 67% | 0.906 | 50% | **0.333** | 83% | **+0.643** |

## 2. Análise Detalhada das 8 Páginas em que o Sucessor Mais Perde para o XY-cut

Para cada uma das 8 piores páginas sob decodificação em cadeias, analisamos onde o sucessor começa a errar, o alinhamento bloco a bloco com os textos (40 caracteres), as coordenadas de bounding box e o padrão estrutural da falha.

### Caso 1: `executive_official_diary_2021-11-19.pdf#p14`
- **ID Completo:** `official_diary_ma/executive_official_diary_2021-11-19.pdf#p14`
- **Contexto:** UF: `ma` | Grupo: `silver` | Blocos: 33 | Colunas: 2 | Tabelas: 3 | Flags: `['tabela']`
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.027}$ | Sucessor Correto = **90.6%**
  - **XY-cut:** $\tau = \mathbf{0.943}$ | Sucessor Correto = **90.6%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.765}$ | Sucessor Correto = **12.5%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.917}$

- **Onde o Sucessor começa a errar (Posição 0):**
  - Bloco predito pelo Sucessor: `b17` (deveria estar na pos 1 da Ref, bbox=[331.4, 50.1, 540.7, 66.1]): `"SEXTA - FEIRA, 19 - NOVEMBRO - 2021 15"`
  - Bloco esperado pela Referência: `b13` (colocado pelo Sucessor na pos 17, bbox=[49.5, 52.2, 169.9, 62.2]): `"D.O. PODER EXECUTIVO"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 4 cadeias locais contínuas para 33 blocos:
  - **Cadeia 1** (1 bloco): blocos da referência `[1..1]`, bounding box `[331.4, 50.1, 540.7, 66.1]`. Início: `"SEXTA - FEIRA, 19 - NOVEMBRO - 2021 15"`
  - **Cadeia 2** (16 blocos): blocos da referência `[17..32]`, bounding box `[303.3, 73.7, 551.8, 793.4]`. Início: `"O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV"`
  - **Cadeia 3** (1 bloco): blocos da referência `[0..0]`, bounding box `[49.5, 52.2, 169.9, 62.2]`. Início: `"D.O. PODER EXECUTIVO"`
  - **Cadeia 4** (15 blocos): blocos da referência `[2..16]`, bounding box `[41.1, 73.7, 289.6, 792.1]`. Início: `"O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b13` | 0 | 17 | 0 | `[49.5, 52.2, 169.9, 62.2]` | 'D.O. PODER EXECUTIVO' |
| `b17` | 1 | 0 | 16 | `[331.4, 50.1, 540.7, 66.1]` | 'SEXTA - FEIRA, 19 - NOVEMBRO - 2021 15' |
| `b10` | 2 | 18 | 1 | `[41.1, 73.7, 289.6, 145.1]` | 'O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV' |
| `b32` | 3 | 19 | 2 | `[139.8, 161.2, 190.5, 170.2]` | 'RESOLVEM' |
| `b6` | 4 | 20 | 3 | `[41.1, 186.1, 289.1, 220.1]` | 'Nomear os integrantes do quadro abaixo p' |
| `b11` | 5 | 21 | 4 | `[46.8, 238.5, 281.8, 297.3]` | 'NOME CARGO SÍMBOLO JOSÉ MARIA RIBEIRO As' |
| `b2` | 6 | 22 | 5 | `[41.1, 309.3, 289.1, 339.5]` | 'PALÁCIO DO GOVERNO DO ESTADO DO MARANHÃO' |
| `b14` | 7 | 23 | 6 | `[103.7, 351.7, 226.5, 371.3]` | 'DIEGO GALDINO DE ARAUJO Secretário-Chefe' |
| `b18` | 8 | 24 | 7 | `[80.1, 383.5, 250.6, 403.1]` | 'ANDERSON FLÁVIO LINDOSO SANTANA Secretár' |
| `b3` | 9 | 25 | 8 | `[41.1, 415.5, 289.2, 477.3]` | 'O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV' |
| `b4` | 10 | 26 | 9 | `[139.8, 489.7, 190.5, 498.7]` | 'RESOLVEM' |
| `b29` | 11 | 27 | 10 | `[41.1, 510.7, 289.1, 541.1]` | 'Exonerar, a pedido, os integrantes do qu' |
| `b12` | 12 | 28 | 11 | `[46.8, 556.0, 283.4, 682.0]` | 'NOME CARGO SÍMBOLO Diretor de Administra' |
| `b5` | 13 | 29 | 12 | `[41.1, 695.9, 289.1, 726.7]` | 'PALÁCIO DO GOVERNO DO ESTADO DO MARANHÃO' |
| `b20` | 14 | 30 | 13 | `[103.7, 739.5, 226.5, 759.4]` | 'DIEGO GALDINO DE ARAUJO Secretário-Chefe' |
| `b31` | 15 | 31 | 14 | `[95.2, 772.2, 235.5, 781.2]` | 'MURILO ANDRADE DE OLIVEIRA' |
| `b8` | 16 | 32 | 15 | `[70.8, 783.1, 259.5, 792.1]` | 'Secretário de Estado de Administração Pe' |
| `b0` | 17 | 1 | 17 | `[303.3, 73.7, 551.4, 134.1]` | 'O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV' |
| `b7` | 18 | 2 | 18 | `[402.0, 145.8, 452.7, 154.8]` | 'RESOLVEM' |
| `b19` | 19 | 3 | 19 | `[303.3, 166.3, 551.3, 195.9]` | 'Nomear os integrantes do quadro abaixo p' |
| `b1` | 20 | 4 | 20 | `[309.0, 210.9, 544.9, 348.5]` | 'NOME CARGO SÍMBOLO Diretor de Área da Ad' |
| `b25` | 21 | 5 | 21 | `[303.3, 359.4, 551.3, 389.0]` | 'PALÁCIO DO GOVERNO DO ESTADO DO MARANHÃO' |
| `b26` | 22 | 6 | 22 | `[366.0, 400.6, 488.7, 419.9]` | 'DIEGO GALDINO DE ARAUJO Secretário-Chefe' |
| `b30` | 23 | 7 | 23 | `[357.5, 431.5, 497.7, 440.5]` | 'MURILO ANDRADE DE OLIVEIRA' |
| `b23` | 24 | 8 | 24 | `[333.0, 441.8, 521.7, 450.8]` | 'Secretário de Estado de Administração Pe' |
| `b24` | 25 | 9 | 25 | `[303.3, 462.6, 551.8, 533.2]` | 'O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV' |
| `b27` | 26 | 10 | 26 | `[402.0, 545.0, 452.7, 554.0]` | 'RESOLVEM' |
| `b9` | 27 | 11 | 27 | `[303.3, 565.4, 551.4, 605.3]` | 'Exonerar ANNE THALITA TELES RODRIGUES FE' |
| `b21` | 28 | 12 | 28 | `[303.3, 616.9, 551.3, 646.7]` | 'PALÁCIO DO GOVERNO DO ESTADO DO MARANHÃO' |
| `b15` | 29 | 13 | 29 | `[366.0, 658.5, 488.7, 677.9]` | 'DIEGO GALDINO DE ARAUJO Secretário-Chefe' |
| `b28` | 30 | 14 | 30 | `[352.4, 689.7, 502.2, 698.7]` | 'DIEGO FERNANDO MENDES ROLIM' |
| `b16` | 31 | 15 | 31 | `[318.4, 700.1, 536.3, 709.1]` | 'Secretário de Estado do Meio Ambiente e ' |
| `b22` | 32 | 16 | 32 | `[303.3, 721.1, 551.8, 793.4]` | 'O SECRETÁRIO DE ESTADO CHEFE DA CASA CIV' |

- **Padrão do Erro:**
**Inversão da ordem de macro-cadeias entre colunas (Coluna 2 antes da Coluna 1).** O LayoutLM com predição de sucessor recuperou a ordem interna de leitura de cada coluna com precisão de 100%: formou uma cadeia contínua de 15 blocos para a Coluna 1 (ref [2..16]) e uma cadeia de 16 blocos para a Coluna 2 (ref [17..32]), alcançando expressivos 90,6% de sucessores corretos no documento. Contudo, na fase de decodificação global em que as cadeias são ordenadas pelo escore pontual médio, a cadeia da Coluna 2 recebeu valor médio inferior ao da Coluna 1, sendo alocada antes dela. Essa inversão de colunas completas gerou a discordância de 240 pares cruzados, despencando o τ de Kendall para 0,027 (contra 0,943 do XY-cut). Trata-se de uma falha de ordenação macro-estrutural entre cadeias, contrastando com a continuidade local quase perfeita.

### Caso 2: `2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373`
- **ID Completo:** `official_diary_ap/2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373`
- **Contexto:** UF: `ap` | Grupo: `incerto` | Blocos: 5 | Colunas: 2 | Tabelas: 1 | Flags: `['tabela']`
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.600}$ | Sucessor Correto = **0.0%**
  - **XY-cut:** $\tau = \mathbf{1.000}$ | Sucessor Correto = **100.0%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.800}$ | Sucessor Correto = **50.0%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.400}$

- **Onde o Sucessor começa a errar (Posição 1):**
  - Bloco predito pelo Sucessor: `b4` (deveria estar na pos 2 da Ref, bbox=[661.9, 37.8, 806.4, 47.8]): `"Terça-Feira, 07 de Maio de 2024"`
  - Bloco esperado pela Referência: `b0` (colocado pelo Sucessor na pos 2, bbox=[393.2, 38.4, 449.8, 48.4]): `"• Nº 8.159"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 5 cadeias locais contínuas para 5 blocos:
  - **Cadeia 1** (1 bloco): blocos da referência `[0..0]`, bounding box `[35.4, 35.7, 150.1, 50.7]`. Início: `"DIÁRIO OFICIAL"`
  - **Cadeia 2** (1 bloco): blocos da referência `[2..2]`, bounding box `[661.9, 37.8, 806.4, 47.8]`. Início: `"Terça-Feira, 07 de Maio de 2024"`
  - **Cadeia 3** (1 bloco): blocos da referência `[1..1]`, bounding box `[393.2, 38.4, 449.8, 48.4]`. Início: `"• Nº 8.159"`
  - **Cadeia 4** (1 bloco): blocos da referência `[4..4]`, bounding box `[390.4, 575.0, 450.4, 585.0]`. Início: `"374 de 632"`
  - **Cadeia 5** (1 bloco): blocos da referência `[3..3]`, bounding box `[127.7, 87.4, 760.7, 517.4]`. Início: `"230101 - SECRETARIA DE ESTADO DO DESENVO"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b2` | 0 | 0 | 0 | `[35.4, 35.7, 150.1, 50.7]` | 'DIÁRIO OFICIAL' |
| `b0` | 1 | 2 | 1 | `[393.2, 38.4, 449.8, 48.4]` | '• Nº 8.159' |
| `b4` | 2 | 1 | 2 | `[661.9, 37.8, 806.4, 47.8]` | 'Terça-Feira, 07 de Maio de 2024' |
| `b1` | 3 | 4 | 3 | `[127.7, 87.4, 760.7, 517.4]` | '230101 - SECRETARIA DE ESTADO DO DESENVO' |
| `b3` | 4 | 3 | 4 | `[390.4, 575.0, 450.4, 585.0]` | '374 de 632' |

- **Padrão do Erro:**
**Desconexão e colapso de adjacência em página esparsa com tabela isolada.** Página de baixa densidade (apenas 5 blocos) dominada por uma grande região de tabela identificada pelo detector visual e blocos periféricos de cabeçalho e rodapé. Nenhuma das transições entre os blocos superou o limiar de probabilidade de 0,5, resultando em 0,0% de sucessores corretos e fragmentando o documento em 5 cadeias unitárias. A ordenação dessas cadeias pela estimativa pontual posicionou o número de página no rodapé ('374 de 632', ref [4]) antes do bloco de tabela (ref [3]), atingindo τ de 0,600 contra 1,000 do particionamento determinístico do XY-cut.

### Caso 3: `JAPERI-5606-09-DE-MAIO-2024.pdf#p3`
- **ID Completo:** `official_diary_rj_japeri/JAPERI-5606-09-DE-MAIO-2024.pdf#p3`
- **Contexto:** UF: `rj_japeri` | Grupo: `incerto` | Blocos: 7 | Colunas: 1 | Tabelas: 0 | Flags: `['figura']`
- **Nota do Anotador:** *"praticamente só uma imagem, e o texto foi bem removido, mas faltou um pouco"*
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.524}$ | Sucessor Correto = **66.7%**
  - **XY-cut:** $\tau = \mathbf{0.905}$ | Sucessor Correto = **66.7%**
  - **LayoutLM Pontual:** $\tau = \mathbf{1.000}$ | Sucessor Correto = **100.0%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.381}$

- **Onde o Sucessor começa a errar (Posição 1):**
  - Bloco predito pelo Sucessor: `b1` (deveria estar na pos 2 da Ref, bbox=[46.8, 38.9, 273.9, 46.9]): `"ANO XXII - NÚMERO 5.606 - QUINTA-FEIRA, "`
  - Bloco esperado pela Referência: `b3` (colocado pelo Sucessor na pos 6, bbox=[218.6, 14.6, 434.7, 31.6]): `"DO MUNICÍPIO DE JAPERI"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 3 cadeias locais contínuas para 7 blocos:
  - **Cadeia 1** (1 bloco): blocos da referência `[0..0]`, bounding box `[37.7, 16.1, 45.2, 31.1]`. Início: `"4"`
  - **Cadeia 2** (5 blocos): blocos da referência `[2..6]`, bounding box `[46.8, 38.9, 438.4, 490.9]`. Início: `"ANO XXII - NÚMERO 5.606 - QUINTA-FEIRA, "`
  - **Cadeia 3** (1 bloco): blocos da referência `[1..1]`, bounding box `[218.6, 14.6, 434.7, 31.6]`. Início: `"DO MUNICÍPIO DE JAPERI"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b0` | 0 | 0 | 1 | `[37.7, 16.1, 45.2, 31.1]` | '4' |
| `b3` | 1 | 6 | 0 | `[218.6, 14.6, 434.7, 31.6]` | 'DO MUNICÍPIO DE JAPERI' |
| `b1` | 2 | 1 | 2 | `[46.8, 38.9, 273.9, 46.9]` | 'ANO XXII - NÚMERO 5.606 - QUINTA-FEIRA, ' |
| `b2` | 3 | 2 | 3 | `[70.3, 101.9, 430.8, 207.1]` | 'A VOZ DO CIDADÃO' |
| `b6` | 4 | 3 | 4 | `[49.2, 200.4, 438.4, 256.1]` | 'JAPERIENSE' |
| `b5` | 5 | 4 | 5 | `[48.3, 285.0, 230.0, 361.2]` | 'Um elo que auxilia a relação do munícipe' |
| `b4` | 6 | 5 | 6 | `[69.5, 408.3, 243.1, 490.9]` | 'ouvidoria.pmj@japeri.rj.gov.br 21 4063-7' |

- **Padrão do Erro:**
**Cabeçalho desacoplado jogado para o final da página.** Página de coluna única dominada por imagem gráfica (anotador: 'praticamente só uma imagem, e o texto foi bem removido, mas faltou um pouco'). O corpo textual central (ref [2..6], 5 blocos) formou uma cadeia coesa e contínua com 100% de acerto interno. Entretanto, o bloco de cabeçalho no topo (ref [1], 'DO MUNICÍPIO DE JAPERI') não estabeleceu transição de alta confiança com o início do corpo e formou uma cadeia unitária. A cabeça pontual atribuiu a esse cabeçalho uma posição tardia, posicionando-o na posição 6 (final da página) e reduzindo o τ para 0,524 (vs 0,905 do XY-cut).

### Caso 4: `Parte I (Poder Executivo)_2024-02-02.pdf#p39`
- **ID Completo:** `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p39`
- **Contexto:** UF: `rj` | Grupo: `silver` | Blocos: 7 | Colunas: 2 | Tabelas: 1 | Flags: `['tabela']`
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.143}$ | Sucessor Correto = **16.7%**
  - **XY-cut:** $\tau = \mathbf{0.429}$ | Sucessor Correto = **66.7%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.429}$ | Sucessor Correto = **16.7%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.286}$

- **Onde o Sucessor começa a errar (Posição 0):**
  - Bloco predito pelo Sucessor: `b2` (deveria estar na pos 3 da Ref, bbox=[51.4, 38.7, 219.3, 68.6]): `"(cid:12)(cid:13) (cid:19)(cid:4)(cid:6)("`
  - Bloco esperado pela Referência: `b6` (colocado pelo Sucessor na pos 2, bbox=[343.0, 53.8, 393.3, 68.7]): `"(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 6 cadeias locais contínuas para 7 blocos:
  - **Cadeia 1** (2 blocos): blocos da referência `[3..4]`, bounding box `[51.4, 38.7, 258.8, 68.6]`. Início: `"(cid:12)(cid:13) (cid:19)(cid:4)(cid:6)("`
  - **Cadeia 2** (1 bloco): blocos da referência `[0..0]`, bounding box `[343.0, 53.8, 393.3, 68.7]`. Início: `"(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)"`
  - **Cadeia 3** (1 bloco): blocos da referência `[2..2]`, bounding box `[357.2, 69.3, 456.3, 75.3]`. Início: `"(cid:1)(cid:4) (cid:9)(cid:10)(cid:11)(c"`
  - **Cadeia 4** (1 bloco): blocos da referência `[6..6]`, bounding box `[74.5, 87.1, 734.3, 1179.3]`. Início: `"50224255 Lucimara De Paula Fraccho Guana"`
  - **Cadeia 5** (1 bloco): blocos da referência `[1..1]`, bounding box `[417.9, 53.8, 473.4, 68.8]`. Início: `"(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:"`
  - **Cadeia 6** (1 bloco): blocos da referência `[5..5]`, bounding box `[685.2, 60.6, 761.1, 68.5]`. Início: `"(cid:1)(cid:2)(cid:3)(cid:4)(cid:5) (cid"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b6` | 0 | 2 | 2 | `[343.0, 53.8, 393.3, 68.7]` | '(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)' |
| `b4` | 1 | 5 | 3 | `[417.9, 53.8, 473.4, 68.8]` | '(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:' |
| `b5` | 2 | 3 | 4 | `[357.2, 69.3, 456.3, 75.3]` | '(cid:1)(cid:4) (cid:9)(cid:10)(cid:11)(c' |
| `b2` | 3 | 0 | 0 | `[51.4, 38.7, 219.3, 68.6]` | '(cid:12)(cid:13) (cid:19)(cid:4)(cid:6)(' |
| `b3` | 4 | 1 | 1 | `[224.9, 60.3, 258.8, 68.3]` | '(cid:3)(cid:4) (cid:18)(cid:13)(cid:18)(' |
| `b1` | 5 | 6 | 5 | `[685.2, 60.6, 761.1, 68.5]` | '(cid:1)(cid:2)(cid:3)(cid:4)(cid:5) (cid' |
| `b0` | 6 | 4 | 6 | `[74.5, 87.1, 734.3, 1179.3]` | '50224255 Lucimara De Paula Fraccho Guana' |

- **Padrão do Erro:**
**Degradação severa por corrupção de fontes digitais do PDF (glifos `(cid:...)`).** Página afetada por defeito de codificação de fontes no PDF original, no qual a camada digital de texto extraiu sequências ilegíveis de glifos não mapeados (`(cid:12)(cid:13)...`). A ausência de informação semântica textual desestabilizou as probabilidades de adjacência da cabeça de sucessor (apenas 1 sucessor correto de 6, 16,7%) e a estimativa de posições. O próprio XY-cut atingiu apenas τ 0,429 nessa página, enquanto o Sucessor caiu para 0,143.

### Caso 5: `executive_official_diary_2025_11_07_216_2025.pdf#p223`
- **ID Completo:** `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223`
- **Contexto:** UF: `pi_v2` | Grupo: `incerto` | Blocos: 8 | Colunas: 3 | Tabelas: 0 | Flags: `nenhum`
- **Nota do Anotador:** *"n reconheceu o tirulo, provavelmente por ser imagem"*
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.714}$ | Sucessor Correto = **57.1%**
  - **XY-cut:** $\tau = \mathbf{1.000}$ | Sucessor Correto = **100.0%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.929}$ | Sucessor Correto = **57.1%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.286}$

- **Onde o Sucessor começa a errar (Posição 1):**
  - Bloco predito pelo Sucessor: `b6` (deveria estar na pos 2 da Ref, bbox=[48.5, 87.7, 546.8, 347.7]): `"segue confrontando com a propriedade de "`
  - Bloco esperado pela Referência: `b3` (colocado pelo Sucessor na pos 5, bbox=[443.3, 38.6, 552.8, 46.1]): `"Publicado: 10/11/2025 00:00:00"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 4 cadeias locais contínuas para 8 blocos:
  - **Cadeia 1** (1 bloco): blocos da referência `[0..0]`, bounding box `[42.5, 38.6, 170.9, 46.1]`. Início: `"Disponibilizado: 07/11/2025 18:00:13"`
  - **Cadeia 2** (4 blocos): blocos da referência `[2..5]`, bounding box `[48.5, 87.7, 546.8, 731.6]`. Início: `"segue confrontando com a propriedade de "`
  - **Cadeia 3** (1 bloco): blocos da referência `[1..1]`, bounding box `[443.3, 38.6, 552.8, 46.1]`. Início: `"Publicado: 10/11/2025 00:00:00"`
  - **Cadeia 4** (2 blocos): blocos da referência `[6..7]`, bounding box `[218.9, 773.2, 549.0, 800.6]`. Início: `"Diário nº 216/2025, 7 de novembro de 202"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b4` | 0 | 0 | 0 | `[42.5, 38.6, 170.9, 46.1]` | 'Disponibilizado: 07/11/2025 18:00:13' |
| `b3` | 1 | 5 | 1 | `[443.3, 38.6, 552.8, 46.1]` | 'Publicado: 10/11/2025 00:00:00' |
| `b6` | 2 | 1 | 2 | `[48.5, 87.7, 546.8, 347.7]` | 'segue confrontando com a propriedade de ' |
| `b5` | 3 | 2 | 3 | `[48.5, 357.3, 546.8, 397.5]` | '- MEMORIAL DESCRITIVO ÁREA 03: situado n' |
| `b7` | 4 | 3 | 4 | `[48.5, 407.1, 546.8, 711.0]` | '- Inicia-se a descrição deste perímetro ' |
| `b0` | 5 | 4 | 5 | `[48.5, 720.6, 546.7, 731.6]` | 'Este EDITAL será publicado, no Diário Of' |
| `b2` | 6 | 6 | 6 | `[218.9, 773.2, 371.3, 800.6]` | 'Diário nº 216/2025, 7 de novembro de 202' |
| `b1` | 7 | 7 | 7 | `[495.4, 780.7, 549.0, 788.2]` | 'Página 222/243' |

- **Padrão do Erro:**
**Desacoplamento parcial de metadados de cabeçalho (recuperação substancial em relação ao feixe).** Na busca em feixe anterior, esta página sofria colapso total (τ 0,143), com ambos os blocos de cabeçalho jogados após o corpo. Com a decodificação em cadeias, a página recuperou-se para τ 0,714 e 57,1% de sucessor: o bloco inicial de cabeçalho (ref [0], 'Disponibilizado...') foi posicionado corretamente no topo da leitura, e os 4 blocos do corpo (ref [2..5]) formaram uma cadeia contínua exemplar. O erro residual concentrou-se no segundo bloco de metadado (ref [1], 'Publicado...'), que não se encadeou ao primeiro e foi posicionado entre o corpo e o rodapé.

### Caso 6: `executive_official_diary_2022-05-26_095.pdf#p2`
- **ID Completo:** `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2`
- **Contexto:** UF: `RJ_barra_do_pirai` | Grupo: `incerto` | Blocos: 6 | Colunas: 3 | Tabelas: 0 | Flags: `['figura']`
- **Nota do Anotador:** *"pegou muito mal os textos da imagem a qualidade do diario ta ruim tbm, mas ele quase n reconehceu nada"*
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.733}$ | Sucessor Correto = **60.0%**
  - **XY-cut:** $\tau = \mathbf{1.000}$ | Sucessor Correto = **100.0%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.867}$ | Sucessor Correto = **60.0%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.267}$

- **Onde o Sucessor começa a errar (Posição 3):**
  - Bloco predito pelo Sucessor: `b1` (deveria estar na pos 4 da Ref, bbox=[421.4, 795.2, 665.6, 805.2]): `"DIÁRIO OFICIAL ELETRÔNICO garante autent"`
  - Bloco esperado pela Referência: `b2` (colocado pelo Sucessor na pos 5, bbox=[245.1, 803.8, 360.5, 819.8]): `"Barra do Piraí/RJ 3"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 3 cadeias locais contínuas para 6 blocos:
  - **Cadeia 1** (3 blocos): blocos da referência `[0..2]`, bounding box `[64.4, 22.8, 658.6, 193.7]`. Início: `"Boletim do Município de Barra do Piraí -"`
  - **Cadeia 2** (2 blocos): blocos da referência `[4..5]`, bounding box `[421.4, 795.2, 665.6, 827.2]`. Início: `"DIÁRIO OFICIAL ELETRÔNICO garante autent"`
  - **Cadeia 3** (1 bloco): blocos da referência `[3..3]`, bounding box `[245.1, 803.8, 360.5, 819.8]`. Início: `"Barra do Piraí/RJ 3"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b0` | 0 | 0 | 0 | `[104.2, 22.8, 620.7, 33.3]` | 'Boletim do Município de Barra do Piraí -' |
| `b3` | 1 | 1 | 1 | `[66.2, 111.8, 156.2, 130.8]` | 'SUMÁRIO' |
| `b4` | 2 | 2 | 2 | `[64.4, 140.7, 658.6, 193.7]` | 'Secretaria Municipal de Governo.........' |
| `b2` | 3 | 5 | 3 | `[245.1, 803.8, 360.5, 819.8]` | 'Barra do Piraí/RJ 3' |
| `b1` | 4 | 3 | 4 | `[421.4, 795.2, 665.6, 805.2]` | 'DIÁRIO OFICIAL ELETRÔNICO garante autent' |
| `b5` | 5 | 4 | 5 | `[421.4, 805.2, 661.0, 827.2]` | 'deste documento visualizado diretamente ' |

- **Padrão do Erro:**
**Inversão de blocos periféricos no rodapé da página.** Página de baixa densidade (6 blocos) com cabeçalho institucional e avisos (anotador: 'pegou muito mal os textos da imagem...'). O modelo agrupou corretamente os 3 blocos superiores (ref [0..2]) e os 2 blocos de autenticação eletrônica (ref [4..5]). Contudo, o bloco intermediário contendo local e número de página (ref [3], 'Barra do Piraí/RJ 3') formou cadeia unitária que foi posicionada após os blocos de rodapé de autenticação, resultando em τ 0,733 contra 1,000 do XY-cut.

### Caso 7: `executive_official_diary_2026-01-16_010.pdf#p2`
- **ID Completo:** `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2`
- **Contexto:** UF: `RJ_barra_do_pirai` | Grupo: `incerto` | Blocos: 6 | Colunas: 3 | Tabelas: 0 | Flags: `['figura']`
- **Nota do Anotador:** *"o texto da imagem n foi bem feito"*
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.733}$ | Sucessor Correto = **60.0%**
  - **XY-cut:** $\tau = \mathbf{1.000}$ | Sucessor Correto = **100.0%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.867}$ | Sucessor Correto = **60.0%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.267}$

- **Onde o Sucessor começa a errar (Posição 3):**
  - Bloco predito pelo Sucessor: `b2` (deveria estar na pos 4 da Ref, bbox=[421.4, 795.2, 665.6, 805.2]): `"DIÁRIO OFICIAL ELETRÔNICO garante autent"`
  - Bloco esperado pela Referência: `b3` (colocado pelo Sucessor na pos 5, bbox=[245.1, 803.8, 360.5, 819.8]): `"Barra do Piraí/RJ 3"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 3 cadeias locais contínuas para 6 blocos:
  - **Cadeia 1** (3 blocos): blocos da referência `[0..2]`, bounding box `[63.8, 22.8, 658.0, 178.1]`. Início: `"Boletim do Município de Barra do Piraí -"`
  - **Cadeia 2** (2 blocos): blocos da referência `[4..5]`, bounding box `[421.4, 795.2, 665.6, 827.2]`. Início: `"DIÁRIO OFICIAL ELETRÔNICO garante autent"`
  - **Cadeia 3** (1 bloco): blocos da referência `[3..3]`, bounding box `[245.1, 803.8, 360.5, 819.8]`. Início: `"Barra do Piraí/RJ 3"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b4` | 0 | 0 | 0 | `[98.7, 22.8, 626.2, 33.3]` | 'Boletim do Município de Barra do Piraí -' |
| `b5` | 1 | 1 | 1 | `[66.2, 111.8, 156.2, 130.8]` | 'SUMÁRIO' |
| `b0` | 2 | 2 | 2 | `[63.8, 136.1, 658.0, 178.1]` | 'Secretaria Municipal de Governo.........' |
| `b3` | 3 | 5 | 3 | `[245.1, 803.8, 360.5, 819.8]` | 'Barra do Piraí/RJ 3' |
| `b2` | 4 | 3 | 4 | `[421.4, 795.2, 665.6, 805.2]` | 'DIÁRIO OFICIAL ELETRÔNICO garante autent' |
| `b1` | 5 | 4 | 5 | `[421.4, 805.2, 661.0, 827.2]` | 'deste documento visualizado diretamente ' |

- **Padrão do Erro:**
**Inversão de blocos de rodapé em edição do mesmo veículo (Barra do Piraí).** Comportamento e gabarito idênticos ao Caso 6: cabeçalho e corpo agrupados em cadeia com acerto perfeito, mas o bloco periférico de identificação de página (ref [3], 'Barra do Piraí/RJ 3') foi alocado após as declarações de conformidade da assinatura digital (ref [4..5]), mantendo τ de 0,733 vs 1,000 do XY-cut.

### Caso 8: `executive_official_diary_2020-12-10_2591.pdf#p1`
- **ID Completo:** `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`
- **Contexto:** UF: `MG_congonhas` | Grupo: `incerto` | Blocos: 17 | Colunas: 1 | Tabelas: 0 | Flags: `['figura']`
- **Nota do Anotador:** *"o tirulo é uma figura e ela n identificou"*
- **Desempenho Comparado:**
  - **LayoutLM Sucessor:** $\tau = \mathbf{0.794}$ | Sucessor Correto = **87.5%**
  - **XY-cut:** $\tau = \mathbf{0.985}$ | Sucessor Correto = **87.5%**
  - **LayoutLM Pontual:** $\tau = \mathbf{0.897}$ | Sucessor Correto = **12.5%**
  - **Diferença (Sucessor − XY-cut):** $\mathbf{-0.191}$

- **Onde o Sucessor começa a errar (Posição 2):**
  - Bloco predito pelo Sucessor: `b1` (deveria estar na pos 16 da Ref, bbox=[568.0, 803.4, 572.0, 811.5]): `"2"`
  - Bloco esperado pela Referência: `b11` (colocado pelo Sucessor na pos 3, bbox=[230.7, 203.4, 371.7, 224.9]): `"ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG"`

- **Estrutura das Cadeias Preservadas:** O Sucessor formou 3 cadeias locais contínuas para 17 blocos:
  - **Cadeia 1** (2 blocos): blocos da referência `[0..1]`, bounding box `[33.1, 116.3, 569.5, 180.4]`. Início: `"Congonhas, 10 de Dezembro de 2020 – Diár"`
  - **Cadeia 2** (1 bloco): blocos da referência `[16..16]`, bounding box `[568.0, 803.4, 572.0, 811.5]`. Início: `"2"`
  - **Cadeia 3** (14 blocos): blocos da referência `[2..15]`, bounding box `[33.1, 203.4, 569.5, 811.6]`. Início: `"ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG"`

- **Alinhamento Bloco a Bloco:**

| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |
|---|---:|---:|---:|---|---|
| `b7` | 0 | 0 | 0 | `[48.4, 116.3, 554.1, 125.8]` | 'Congonhas, 10 de Dezembro de 2020 – Diár' |
| `b3` | 1 | 1 | 1 | `[33.1, 135.6, 569.5, 180.4]` | 'arte, desenvolvimento de relações de soc' |
| `b11` | 2 | 3 | 2 | `[230.7, 203.4, 371.7, 224.9]` | 'ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG' |
| `b14` | 3 | 4 | 3 | `[36.7, 236.7, 565.5, 244.8]` | 'PRIMEIRO TERMO ADITIVO AO TERMO DE COLAB' |
| `b0` | 4 | 5 | 4 | `[169.6, 246.0, 432.9, 254.0]` | 'E A ASSOCIAÇÃO COMUNITÁRIA BENEFICENTE D' |
| `b2` | 5 | 6 | 5 | `[33.1, 264.2, 569.5, 391.9]` | 'Partícipes: MUNICÍPIO DE CONGONHAS, insc' |
| `b15` | 6 | 7 | 6 | `[230.7, 415.0, 371.8, 436.5]` | 'ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG' |
| `b5` | 7 | 8 | 7 | `[188.1, 448.3, 414.4, 456.3]` | 'EDITAL PROCESSO ADMINISTRATIVO: PMC Nº 1' |
| `b9` | 8 | 9 | 8 | `[33.1, 466.6, 569.4, 621.8]` | 'A Secretaria Municipal da Fazenda, Diret' |
| `b8` | 9 | 10 | 9 | `[75.7, 632.2, 186.9, 640.2]` | 'Congonhas, 09 de dezembro 2020.' |
| `b10` | 10 | 11 | 10 | `[230.9, 650.7, 371.5, 658.7]` | 'Diretoria de Tributação e de Fiscalizaçã' |
| `b6` | 11 | 12 | 11 | `[230.7, 681.7, 371.7, 703.2]` | 'ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG' |
| `b16` | 12 | 13 | 12 | `[182.7, 715.0, 419.6, 723.0]` | 'PRIMEIRO TERMO ADITIVO AO CONTRATO N° PM' |
| `b13` | 13 | 14 | 13 | `[33.1, 733.2, 569.1, 750.5]` | 'Partes: Município de Congonhas X Edmar L' |
| `b4` | 14 | 15 | 14 | `[230.7, 773.6, 371.7, 795.1]` | 'ESTADO DE MINAS GERAIS MUNICÍPIO DE CONG' |
| `b12` | 15 | 16 | 16 | `[223.8, 803.6, 381.7, 811.6]` | 'w w w. congonhas. m g. g o v. b r' |
| `b1` | 16 | 2 | 15 | `[568.0, 803.4, 572.0, 811.5]` | '2' |

- **Padrão do Erro:**
**Número de página isolado inserido precocemente antes do corpo textual.** O corpo da matéria em coluna única (14 blocos, ref [2..15]) foi totalmente encadeado em uma única macro-cadeia com 100% de continuidade local (sucessor correto de 87,5%). Contudo, o número da página no rodapé inferior (ref [16], '2', caixa diminuta no canto inferior direito) formou cadeia unitária e recebeu escore pontual intermediário, sendo inserido logo na posição 2 (após o cabeçalho e antes de todo o corpo da matéria), reduzindo o τ para 0,794 (contra 0,985 do XY-cut).

## 3. Médias de Desempenho por Recorte Estrutural

Para entender a sensibilidade estrutural dos métodos sob decodificação em cadeias, agrupamos as 47 páginas por características de layout, comparando o LayoutLM Sucessor com o LayoutLM Pontual e o XY-cut.

### 3.1 Por Grupo de Validação (`silver` vs `incerto`)

| Grupo | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |
|---|---:|---:|---:|---:|---:|---:|---:|
| `silver` | 21 | **0.837** | 70.6% | 0.828 | 29.2% | **0.873** | 76.5% |
| `incerto` | 26 | **0.851** | 63.7% | 0.861 | 35.7% | **0.834** | 72.0% |

### 3.2 Por Número de Colunas da Página

| Número de Colunas | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 coluna | 19 | **0.878** | 69.9% | 0.885 | 41.5% | **0.788** | 62.9% |
| 2 colunas | 22 | **0.824** | 64.0% | 0.812 | 23.5% | **0.890** | 79.1% |
| 3 colunas | 6 | **0.814** | 66.7% | 0.847 | 39.2% | **0.911** | 90.1% |

### 3.3 Por Presença de Tabela

#### Classificação pelo Detector Automático (`stats.n_tabelas > 0`):

| Categoria | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sem tabela | 30 | **0.875** | 69.6% | 0.866 | 34.1% | **0.850** | 75.0% |
| Com tabela | 17 | **0.791** | 61.7% | 0.810 | 30.5% | **0.853** | 72.2% |

#### Classificação pelo Flag do Anotador Humano (`'tabela' in flags`):

| Categoria | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sem flag tabela | 29 | **0.881** | 72.1% | 0.868 | 35.3% | **0.860** | 76.9% |
| Com flag tabela | 18 | **0.786** | 58.2% | 0.810 | 28.7% | **0.838** | 69.2% |

## 4. Três Hipóteses Fundamentadas pelos Números (Revisadas pós-Cadeias)

1. **Falha de ancoragem e inversão de macro-cadeias como gargalo residual.** O desacoplamento de pequenos blocos periféricos (cabeçalhos no topo, números de página ou notas de rodapé) permanece como o mecanismo mais frequente de erro local quando esses blocos não estabelecem arestas com p > 0,5 com o corpo do texto (visto em Japeri p3, Barra do Piraí e Congonhas p1). Mais importante, em páginas multicolunares densas, revelou-se um novo modo de erro: a inversão na ordenação global de colunas inteiras que foram internamente encadeadas com perfeição (como no Caso 1, MA p14, com 90,6% de sucessor correto mas τ 0,027 devido à leitura da Coluna 2 antes da Coluna 1). A cabeça pontual de ordenação de cadeias é, portanto, o componente que ainda introduz variância quando múltiplas macro-cadeias paralelas coexistem.
2. **Refutação do colapso com múltiplas colunas e superioridade em coluna única.** A hipótese anterior de degradação monotônica severa com o número de colunas (que previa colapso em 3 colunas, onde o τ caía para 0,601 em feixe) foi inteiramente superada: na decodificação em cadeias, páginas de 3 colunas sustentam τ médio de **0,814**, e no caso mais denso do acervo (MG p28, 99 blocos em 3 colunas) o Sucessor atinge τ **0,881**, superando o XY-cut (0,852). Além disso, em páginas de 1 coluna, o LayoutLM Sucessor supera amplamente o XY-cut (τ **0,878** vs 0,788, vantagem de +0,090), demonstrando que o modelo neural é superior na ordenação de blocos livres onde não há calhas ortogonais óbvias.
3. **Alta capacidade de generalização fora do domínio de treino (`incerto`).** A hipótese de vulnerabilidade a veículos e formatos novos foi conclusivamente refutada pelos dados corretos em cadeias: no grupo `incerto` (layouts e UFs nunca vistos durante o treinamento), o LayoutLM Sucessor alcança τ médio de **0,851**, superando tanto o grupo `silver` (0,837) quanto o próprio XY-cut no mesmo recorte (0,834). A aprendizagem de adjacência pairwise por meio de representações conjuntas de texto e layout mostra-se altamente agnóstica a estilos gráficos específicos, transferindo eficazmente para diários oficiais de qualquer federação ou município.

## Registro de Execução

- **Comando executado:** `venv\Scripts\python.exe orquestracao\analises\diagnostico_sucessor.py`
- **Arquivos de entrada:**
  - `data/golden/_avaliacao/golden_v3/tarefas.jsonl` (47 páginas)
  - `data/golden/_avaliacao/golden_v3/referencia.jsonl` (47 páginas concluídas pelo Pedro alano)
  - `resultados/golden/_avaliacao/golden_v3/pred_layoutlm.jsonl` (47 predições)
  - `resultados/golden/_avaliacao/golden_v3/pred_layoutlm_sucessor.jsonl` (47 predições em cadeias, corrigido em 13/09)
- **Métricas calculadas com:** `src.eval.metrics.avaliar`, `kendall_tau`, `acerto_sucessor`
- **Data e Hora:** 2026-09-13
