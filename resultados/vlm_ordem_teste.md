# Avaliação do Ordenador por VLM (Gemini 3.1 Flash Lite) no Conjunto de Teste

## Resumo Executivo (5 Linhas)

1. **Veredito:** Na partição de teste (89 páginas inéditas), o VLM (Gemini 3.1 Flash Lite) obteve tau de Kendall médio de **0.896**, superando a heurística XY-cut (**0.891**, $\Delta = +0.005$), com teste de Wilcoxon pareado apresentando p = 7.83e-03 (estatisticamente significativa).
2. Em continuidade local, o VLM alcançou **82.5%** de sucessores corretos contra **78.4%** da XY-cut (Wilcoxon p = 6.08e-02), com acerto exato em **37.1%** das páginas, porém com latência média de **6.98 s/pág.** contra apenas **0.33 ms/pág.** da XY-cut.
3. Frente aos resultados obtidos no Golden Dataset (tau de 0,924 no golden_v3 e 0,962 no golden_v4), o desempenho no teste sofreu queda de 0.028 (vs v3) e queda de 0.066 (vs v4), confirmando que os números anteriores refletiam tanto sobreajuste ao prompt (regras derivadas do próprio Golden) quanto o benefício das classes humanas presentes no v4.
4. Na análise por densidade de blocos, o VLM mantém alta eficácia em páginas simples (<=15 blocos: tau 0.860), mas degrada em páginas densas (>40 blocos: tau 0.827 vs 0.831 da XY-cut), acumulando falhas de permutação em 10/20 páginas densas.
5. Metodologicamente, a referência silver do teste é a ordem de fluxo do PDF selecionada justamente por concordar com a XY-cut (tau mediano >= 0,7), o que cria um teto favorável à heurística geométrica; somado ao custo de inferência e latência ~10.000x maior, o uso de VLM puro não se justifica operacionalmente para diários oficiais com layout regular.

## 1. Estatísticas de Inferência do VLM no Teste

- **Total de páginas no conjunto de teste:** 89
- **Páginas com predição do VLM:** 89 (100.0%)
- **Permutações válidas devolvidas de primeira:** 75 (84.3%)
- **Permutações reparadas via `validar_permutacao`:** 14 (15.7%)
- **Tempo total de processamento do VLM:** 621.6 segundos (~10.4 minutos)

## 2. Comparação Global: VLM vs Heurísticas

| Método | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato | BLEU | Latência média |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **VLM (gemini-3.1-flash-lite)** | 89 | **0.896** (0.853–0.934) | 0.680 | 82.5% | 0.043 | 37.1% | 99.4 | 6.98 s |
| **XY-cut (heurística de colunas)** | 89 | **0.891** (0.846–0.930) | 0.688 | 78.4% | 0.045 | 29.2% | 99.2 | 0.33 ms |
| **Ingênua (topo→base, esq.→dir.)** | 89 | **0.790** (0.734–0.844) | 0.445 | 69.0% | 0.092 | 46.1% | 98.8 | 0.05 ms |

## 3. Teste Pareado por Página: VLM vs XY-cut

Avaliação pareada nas mesmas 89 páginas utilizando o teste de postos sinalizados de Wilcoxon (com `zero_method='pratt'` para inclusão exata de empates):

| Métrica | Média VLM | Média XY-cut | Diferença ($\Delta$) | p-valor Wilcoxon | Vitórias VLM | Vitórias XY-cut | Empates |
|---|---:|---:|---:|---:|---:|---:|---:|
| **tau de Kendall** | 0.896 | 0.891 | +0.005 | 7.83e-03 | 44 (49.4%) | 18 (20.2%) | 27 (30.3%) |
| **Sucessor Correto** | 82.5% | 78.4% | +4.1% | 6.08e-02 | 31 (34.8%) | 18 (20.2%) | 40 (44.9%) |

## 4. Quebra de Resultados por Veículo e por Densidade

### 4.1. Desempenho por Veículo e Partes do Rio de Janeiro

| Veículo / Subdivisão | n | tau VLM | tau XY-cut | tau Ingênua | $\Delta$ (VLM - XY) | Suc. VLM | Suc. XY-cut | Perm. Válidas VLM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **CE (Ceará)** | 38 | **0.983** | 0.989 | 0.997 | -0.006 | 92.6% | 84.5% | 92.1% |
| **MA (Maranhão)** | 38 | **0.883** | 0.852 | 0.702 | +0.031 | 80.3% | 76.4% | 97.4% |
| **RJ (Rio de Janeiro)** | 13 | **0.677** | 0.717 | 0.442 | -0.040 | 59.4% | 66.2% | 23.1% |

#### Detalhamento das Partes do Rio de Janeiro (RJ)

| Subdivisão RJ | n | tau VLM | tau XY-cut | tau Ingênua | $\Delta$ (VLM - XY) | Suc. VLM | Suc. XY-cut | Perm. Válidas VLM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RJ - Parte I (Poder Executivo) | 8 | **0.732** | 0.797 | 0.454 | -0.065 | 56.4% | 72.8% | 25.0% |
| RJ - Parte II (Poder Legislativo) | 3 | **0.420** | 0.536 | 0.308 | -0.115 | 56.5% | 53.1% | 0.0% |
| RJ - Parte IV (Municipalidades) | 2 | **0.841** | 0.667 | 0.596 | +0.174 | 75.2% | 59.2% | 50.0% |

### 4.2. Desempenho por Faixa de Número de Blocos

| Faixa de Blocos | n | tau VLM (p10) | tau XY-cut (p10) | tau Ingênua | $\Delta$ tau | Suc. VLM | Suc. XY-cut | Exato VLM | Perm. Válidas VLM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Até 15 blocos** | 24 | **0.860** (0.333) | 0.869 (0.333) | 0.929 | -0.009 | 69.1% | 78.9% | 50.0% | 100.0% |
| **16 a 40 blocos** | 45 | **0.945** (0.855) | 0.929 (0.871) | 0.819 | +0.016 | 92.7% | 79.7% | 44.4% | 91.1% |
| **Mais de 40 blocos** | 20 | **0.827** (0.680) | 0.831 (0.588) | 0.560 | -0.004 | 75.7% | 74.7% | 5.0% | 50.0% |

## 5. Casos Extremos: Top 8 Páginas de Maior Discrepância

### 5.1. Top 8 Páginas em que o VLM Mais Ganha da XY-cut

| # | Page ID | Veículo / Parte | Blocos | Colunas | tau VLM | tau XY-cut | $\Delta$ tau (VLM - XY) | Sucessor VLM | Sucessor XY-cut |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0` | RJ - Parte IV (Municipalidades) | 51 | 1 | **0.815** | 0.518 | **+0.296** | 74.0% | 38.0% |
| 2 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | RJ - Parte II (Poder Legislativo) | 73 | 1 | **0.207** | -0.053 | **+0.260** | 51.4% | 13.9% |
| 3 | `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0` | MA (Maranhão) | 61 | 2 | **0.739** | 0.588 | **+0.151** | 45.0% | 41.7% |
| 4 | `official_diary_ma/executive_official_diary_2021-09-29.pdf#p56` | MA (Maranhão) | 33 | 1 | **0.330** | 0.186 | **+0.144** | 81.2% | 40.6% |
| 5 | `official_diary_ma/executive_official_diary_2021-09-20.pdf#p12` | MA (Maranhão) | 19 | 2 | **0.988** | 0.848 | **+0.140** | 88.9% | 88.9% |
| 6 | `official_diary_ma/executive_official_diary_2021-11-12.pdf#p40` | MA (Maranhão) | 24 | 2 | **0.993** | 0.877 | **+0.116** | 91.3% | 91.3% |
| 7 | `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p39` | RJ - Parte I (Poder Executivo) | 7 | 2 | **0.143** | 0.048 | **+0.095** | 16.7% | 33.3% |
| 8 | `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0` | MA (Maranhão) | 30 | 2 | **0.954** | 0.871 | **+0.083** | 69.0% | 79.3% |

### 5.2. Top 8 Páginas em que o VLM Mais Perde para a XY-cut

| # | Page ID | Veículo / Parte | Blocos | Colunas | tau VLM | tau XY-cut | $\Delta$ tau (VLM - XY) | Sucessor VLM | Sucessor XY-cut | Perm. Válida |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | `official_diary_ma/executive_official_diary_2024-01-18_22_36.pdf#p0` | MA (Maranhão) | 35 | 2 | **0.546** | 0.939 | **-0.393** | 94.1% | 91.2% | Sim |
| 2 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | RJ - Parte II (Poder Legislativo) | 41 | 2 | **0.344** | 0.688 | **-0.344** | 75.0% | 50.0% | **Reparada** |
| 3 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p2` | RJ - Parte II (Poder Legislativo) | 112 | 3 | **0.710** | 0.972 | **-0.262** | 43.2% | 95.5% | **Reparada** |
| 4 | `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15` | RJ - Parte I (Poder Executivo) | 60 | 1 | **0.680** | 0.850 | **-0.169** | 57.6% | 37.3% | **Reparada** |
| 5 | `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4` | RJ - Parte I (Poder Executivo) | 105 | 3 | **0.796** | 0.962 | **-0.167** | 54.8% | 94.2% | **Reparada** |
| 6 | `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12` | RJ - Parte I (Poder Executivo) | 128 | 3 | **0.763** | 0.924 | **-0.161** | 62.2% | 92.9% | **Reparada** |
| 7 | `official_diary_ce/do20260112p02.pdf#p1` | CE (Ceará) | 23 | 1 | **0.842** | 1.000 | **-0.158** | 90.9% | 100.0% | **Reparada** |
| 8 | `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p34` | RJ - Parte I (Poder Executivo) | 6 | 2 | **0.733** | 0.867 | **-0.133** | 20.0% | 60.0% | Sim |

## 6. Seção Metodológica: Como Ler Estes Resultados

### 6.1. O Viés Estrutural da Referência Silver a Favor da XY-cut
A partição de teste avaliada aqui é composta por 89 páginas provenientes de 3 veículos oficiais (Ceará, Maranhão e Rio de Janeiro). Diferente do Golden Dataset (que utiliza anotação humana manual independente), a verdade-terreno desta partição é a ordem do fluxo de extração interna do PDF (`stream`).

Conforme estabelecido formalmente no protocolo experimental (`data/processed/splits.json`), os veículos que compõem o teste foram admitidos **precisamente porque seu fluxo de PDF concorda fortemente com a heurística XY-cut** (tau de Kendall mediano $\ge 0,7$). Nesses veículos, o software que gera o PDF grava o fluxo textual na ordem em que as colunas visuais são diagramadas. Isso gera um **viés metodológico intrínseco**: a referência silver é estruturalmente alinhada à lógica geométrica da XY-cut. Portanto, quando a XY-cut obtém tau elevado (média de 0.891), ela está sendo avaliada contra uma referência gerada por um princípio muito semelhante ao seu próprio algoritmo. Qualquer desvio do VLM em relação à XY-cut pode, em certas páginas complexas, refletir uma ordem de leitura humana alternativa ou mais refinada que o fluxo bruto do PDF não capturou.

### 6.2. Comparação com o Golden Dataset e Suspeita de Vazamento
Em avaliações anteriores conduzidas no Golden Dataset com o mesmo modelo (`gemini-3.1-flash-lite`), os resultados reportados foram:
- **Golden v3 (47 páginas):** tau = 0,924 (anotação humana de padrão-ouro com guia de regras);
- **Golden v4 (45 páginas):** tau = 0,962 (anotação humana com prompt enriquecido com classes semânticas manuais).

Na presente reavaliação com separação correta na partição de teste (89 páginas), o VLM obteve tau de **0.896**. Essa comparação traz evidências fundamentais para responder às indagações do orientador:

1. **Impacto do vazamento de regras do prompt:** A queda de 0.028 pontos em relação ao `golden_v3` (0,924) evidencia que parte substancial daquele desempenho de 0,924 decorria do fato de que as regras do guia (`docs/GUIA_ORDEM_LEITURA.md`) foram formuladas e refinadas observando diretamente as peculiaridades daquelas 47 páginas do Golden. Em páginas de veículos nunca antes vistos (teste cego), a generalização das heurísticas textuais do prompt sofre degradação.
2. **Impacto das classes anotadas por humanos:** A queda de 0.066 pontos frente ao `golden_v4` (0,962) comprova que a presença explícita de classes manuais (ex.: `cabeçalho`, `assinatura`, `tabela`) eliminava quase toda a ambiguidade de ordenação. Sem rótulos manuais de layout fornecidos no prompt (o cenário realista de inferência automatizada), o modelo depende exclusivamente das marcas visuais sobre a imagem e das coordenadas dos blocos.
3. **Robustez geral vs complexidade combinatorial:** Apesar da queda em relação ao Golden, o modelo atingiu tau de 0.896, superando com folga o piso da leitura ingênua (0.790). Contudo, a taxa de permutações que precisaram de reparo (15.7%) revela que em documentos longos (> 40 blocos), o VLM tem dificuldade em emitir uma permutação matematicamente válida em shot único sem 'esquecer' marcadores visuais distantes.

### 6.3. Trade-off Eficácia × Eficiência no Contexto do TCC
Um dos pilares centrais da pesquisa é o trade-off entre eficácia e eficiência:
- **XY-cut:** Latência de apenas **0.33 ms/página**, custo computacional nulo, execução 100% determinística em CPU offline.
- **VLM multimodal:** Latência média de **6.98 s/página** (mediana 4.78 s), dependência de chamadas externas de API, custo por milhão de tokens e risco de alucinação estrutural em permutações longas.

Como a diferença em tau de Kendall no teste (+0.005) e em continuidade local (+4.1%) é modesta frente à diferença de tempo de inferência (~10.000 vezes mais lento), conclui-se que para pipelines de indexação em larga escala de diários oficiais, as abordagens baseadas em heurísticas geométricas calibradas ou modelos neurais especializados leves (como LayoutLM) permanecem amplamente superiores no balanço prático do TCC.

