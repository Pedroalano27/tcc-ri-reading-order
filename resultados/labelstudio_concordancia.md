# Concordância entre Anotadores Humanos no Dataset de Layout (Label Studio)

> **Data de geração:** 2026-10-03 02:38:30 | **Amostra avaliada:** 333 páginas (335 pares de anotadores independentes)

## Resumo Executivo

1. **Localização geométrica robusta:** A detecção de caixas delimitadoras atinge F1 macro de 93,7% [92,4%; 94,9%] em IoU ≥ 0,5, caindo para 92,2% em IoU ≥ 0,75 e 91,5% em IoU ≥ 0,9.
2. **Concordância semântica nas 16 classes:** Entre caixas casadas em IoU ≥ 0,5, o acerto de classe é de 91,8% com Kappa de Cohen κ = 0,892 [0,870; 0,912] (Quase perfeita (0,81 - 1,00)).
3. **Ganho expressivo com colapso de granularidade:** Ao agrupar para as 9 classes do extrator o Kappa sobe para κ = 0,943 [0,926; 0,957], e atinge κ = 0,970 [0,953; 0,984] nas 3 classes (texto/tabela/imagem), revelando que o desacordo reside em fronteiras semânticas finas.
4. **Impacto substancial da ancoragem:** Em 39,5% [36,4%; 42,3%] das caixas casadas ambos os anotadores mantiveram passivamente a pré-anotação da máquina (`origin == 'prediction'`); ao isolar as caixas onde ao menos um anotador realizou intervenção ativa, o Kappa nas 16 classes recua para κ = 0,847 [0,818; 0,875] (queda de 0,045 pontos).
5. **Teto empírico do TCC:** Estes valores representam a fronteira máxima esperada para modelos automatizados (Docling, LayoutLM, extratores); nenhum modelo de extração deve ser cobrado de superar a concordância do consenso humano livre de viés.

## 1. Inventário do Dataset de Concordância

| Arquivo de Export | Tarefas com Anotação Dupla | Caixas Avaliadas |
|---|---:|---:|
| `ls_p05_seed1.json` | 118 | — |
| `ls_p13_seed2.json` | 23 | — |
| `ls_p15_seed3.json` | 3 | — |
| `ls_p23_seed2_order.json` | 189 | — |
| **Total Consolidado** | **333 páginas (335 pares)** | **13332 caixas** |

## 2. Concordância de Localização Geométrica (Detecção de Caixas)

Casamento guloso 1-1 por IoU (maior IoU primeiro), independente de classe.

| Limiar IoU | Pares Casados (TP) | Precisão Micro (IC 95%) | Revocação Micro (IC 95%) | F1 Micro (IC 95%) | F1 Macro / Pág. (IC 95%) |
|---|---:|---:|---:|---:|---:|
| **IoU ≥ 0,50** | 6318 | 92,6% [90,6%; 94,1%] | 97,1% [96,3%; 97,7%] | 94,8% [93,4%; 95,8%] | **93,7%** [92,4%; 94,9%] |
| **IoU ≥ 0,75** | 6230 | 91,3% [91,3%; 91,3%] | 95,7% [95,7%; 95,7%] | 93,5% [91,8%; 94,7%] | **92,2%** [90,6%; 93,5%] |
| **IoU ≥ 0,90** | 6177 | 90,5% [90,5%; 90,5%] | 94,9% [94,9%; 94,9%] | 92,7% [90,9%; 94,1%] | **91,5%** [89,7%; 92,9%] |

## 3. Concordância Semântica de Classificação (Caixas Casadas em IoU ≥ 0,5)

| Esquema Taxonômico | N de Classes | Caixas Casadas | Acerto de Classe (IC 95%) | Kappa de Cohen κ (IC 95%) | Grau de Concordância |
|---|---:|---:|---:|---:|---|
| **Guia Oficial (Original)** | 16 | 6318 | 91,8% [90,2%; 93,3%] | **0,892** [0,870; 0,912] | Quase perfeita (0,81 - 1,00) |
| **Extrator TCC (Colapso)** | 9 | 6318 | 96,0% [94,8%; 97,0%] | **0,943** [0,926; 0,957] | Quase perfeita (0,81 - 1,00) |
| **Tripartido (Texto/Tabela/Imagem)** | 3 | 6316 | 99,2% [98,8%; 99,6%] | **0,970** [0,953; 0,984] | Quase perfeita (0,81 - 1,00) |

*Nota sobre as 3 classes:* conforme o protocolo, `unknown` é excluído; `table` → tabela; `figure`, `chart`, `heading` → imagem; demais classes → texto.

## 4. Análise do Viés de Ancoragem da Pré-Anotação

A pré-anotação automática reduz a fadiga humana, mas induz viés de confirmação (ancoragem): o anotador tende a aceitar a geometria e o rótulo sugeridos pela máquina. Abaixo compara-se o dataset completo contra o subconjunto onde **pelo menos um anotador realizou intervenção ativa** (`origin == 'manual'` ou `'prediction-changed'`).

| Conjunto Analisado | Caixas Casadas | % do Total | Acerto 16c (IC 95%) | Kappa 16c (IC 95%) | Acerto 9c (IC 95%) | Kappa 9c (IC 95%) | Acerto 3c (IC 95%) | Kappa 3c (IC 95%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Todas as caixas casadas** | 6318 | 100,0% | 91,8% | 0,892 | 96,0% | 0,943 | 99,2% | 0,970 |
| **Ambos aceitaram pré-anotação** (`prediction`) | 2495 | **39,5%** | — | — | — | — | — | — |
| **Ao menos um anotador mexeu** (Ativo) | 3823 | 60,5% | **86,5%** [83,9%; 89,0%] | **0,847** [0,818; 0,875] | **93,4%** [91,5%; 95,0%] | **0,919** [0,896; 0,939] | **98,7%** [98,0%; 99,4%] | **0,958** [0,936; 0,979] |
| **Impacto da Ancoragem (Δ)** | — | — | -5,3% | -0,045 | -2,6% | -0,024 | -0,5% | -0,011 |

## 5. F1 por Classe nas 16 Classes do Guia (Localização IoU ≥ 0,5 + Classe)

| Classe | Função no Guia | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP (IoU ≥ 0,5) | F1 Classe (IC 95%) | Acerto Condicional entre Casadas |
|---|---|---:|---:|---:|---:|---:|
| `act` | Titulo de ato normativo | 305 | 210 | 202 | **78,4%** [68,5%; 86,5%] | 141,8% |
| `act section` | Subtitulo ou divisao interna de ato | 124 | 88 | 71 | **67,0%** [52,5%; 79,3%] | 105,2% |
| `paragraph` | Texto corrente | 2968 | 2950 | 2804 | **94,8%** [93,0%; 96,1%] | 188,2% |
| `signature` | Bloco textual ou digital de assinatura | 308 | 242 | 219 | **79,6%** [69,5%; 86,8%] | 151,6% |
| `heading` | Assinatura manuscrita ou rubrica | 83 | 68 | 60 | **79,5%** [58,8%; 95,2%] | 190,5% |
| `id` | Identificadores, protocolos e codigos | 82 | 92 | 71 | **81,6%** [68,8%; 90,3%] | 157,8% |
| `header` | Cabecalho geral da pagina (recorrente, topo) | 851 | 798 | 730 | **88,5%** [85,6%; 91,3%] | 191,9% |
| `footer` | Rodape geral da pagina (recorrente, base) | 323 | 288 | 260 | **85,1%** [80,8%; 88,9%] | 166,7% |
| `table` | Estrutura tabular | 388 | 390 | 386 | **99,2%** [98,5%; 99,8%] | 200,0% |
| `chart` | Grafico de dados | 12 | 12 | 12 | **100,0%** [100,0%; 100,0%] | 200,0% |
| `figure` | Imagem, fotografia, mapa ou ilustracao | 572 | 467 | 426 | **82,0%** [77,5%; 86,3%] | 180,5% |
| `caption` | Legenda de tabela, figura ou grafico | 170 | 158 | 131 | **79,9%** [71,4%; 86,6%] | 149,7% |
| `title` | Titulo principal de documento NAO normativo | 235 | 381 | 191 | **62,0%** [53,2%; 70,6%] | 101,1% |
| `section title` | Titulo de secao de documento nao normativo | 235 | 243 | 137 | **57,3%** [46,1%; 67,9%] | 86,7% |
| `sub section title` | Titulo de subsecao de documento nao normativo | 168 | 117 | 100 | **70,2%** [51,0%; 81,1%] | 111,7% |
| `unknown` | Classificacao duvidosa | 1 | 3 | 1 | **50,0%** [0,0%; 100,0%] | 100,0% |

## 6. F1 por Classe nos Esquemas Reduzidos

### 6.1. Esquema de 9 Classes do Extrator

| Classe Extrator | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP | F1 Classe (IC 95%) |
|---|---:|---:|---:|---:|
| `assinatura` | 391 | 310 | 279 | **79,6%** [69,4%; 87,5%] |
| `cabecalho` | 851 | 798 | 730 | **88,5%** [85,6%; 91,3%] |
| `figura` | 584 | 479 | 438 | **82,4%** [77,9%; 86,7%] |
| `outro` | 1 | 3 | 1 | **50,0%** [0,0%; 100,0%] |
| `rodape` | 323 | 288 | 260 | **85,1%** [80,8%; 88,9%] |
| `tabela` | 388 | 390 | 386 | **99,2%** [98,5%; 99,8%] |
| `texto` | 3220 | 3200 | 3029 | **94,4%** [92,7%; 95,7%] |
| `titulo` | 1067 | 1039 | 943 | **89,6%** [85,9%; 92,5%] |

### 6.2. Esquema Tripartido (3 Classes)

| Macroclasse | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP | F1 Classe (IC 95%) |
|---|---:|---:|---:|---:|
| `texto` | 5769 | 5567 | 5383 | **95,0%** [93,5%; 96,0%] |
| `tabela` | 388 | 390 | 386 | **99,2%** [98,5%; 99,8%] |
| `imagem` | 667 | 547 | 498 | **82,0%** [77,1%; 86,7%] |

## 7. As 10 Confusões de Classes Mais Frequentes

Pares não ordenados de classes atribuídas pelos dois anotadores em uma mesma caixa física casada em IoU ≥ 0,5.

| Ranking | Par de Classes Confundidas | Ocorrências | % dos Desacordos | Contexto Típico em Diários Oficiais |
|---|---|---:|---:|---|
| 1 | `section title` ↔ `title` | 60 | 11,6% | Nível hierárquico de títulos (título geral vs título de seção) |
| 2 | `section title` ↔ `sub section title` | 58 | 11,2% | Subdivisões finas de seções administrativas |
| 3 | `act` ↔ `title` | 43 | 8,3% | Distinção entre título normativo (decreto/portaria) vs título administrativo comum |
| 4 | `paragraph` ↔ `signature` | 40 | 7,7% | Ambiguidade visual ou funcional da taxonomia |
| 5 | `figure` ↔ `title` | 22 | 4,3% | Ambiguidade visual ou funcional da taxonomia |
| 6 | `footer` ↔ `paragraph` | 21 | 4,1% | Rodapé com notas ou avisos legais vs texto corrente final |
| 7 | `act` ↔ `section title` | 19 | 3,7% | Ambiguidade visual ou funcional da taxonomia |
| 8 | `caption` ↔ `paragraph` | 19 | 3,7% | Legenda explicativa curta confundida com parágrafo |
| 9 | `act section` ↔ `section title` | 19 | 3,7% | Ambiguidade visual ou funcional da taxonomia |
| 10 | `act section` ↔ `title` | 19 | 3,7% | Ambiguidade visual ou funcional da taxonomia |

## 8. Como Ler estes Resultados

### 8.1. O Teto Empírico Realista para Modelos de Extração
Em Aprendizado de Máquina e Recuperação de Informação, a taxa de concordância inter-anotador humana estabelece a **fronteira de Bayes empírica** (o limite superior de desempenho). Nenhum modelo automatizado (Docling Heron, YOLOv8, RT-DETR ou LayoutLM) pode ser razoavelmente cobrado de concordar com anotações de teste além da taxa em que humanos independentes concordam entre si sob o mesmo guia de rotulagem. Se o F1 de localização humano em IoU ≥ 0,5 atinge 93,7% e o Kappa de Cohen nas 16 classes é de κ = 0,892, um modelo que alcance métricas próximas já está operando na faixa de ruído humano intrínseco.

### 8.2. A Ilusão da Concordância Inflada (Viés de Ancoragem)
A ancoragem cognitiva (Kahneman & Tversky, 1974; Skirzyński et al., 2021) é um risco metodológico central quando dados são anotados a partir de pré-rotulação por máquina. Quando um modelo sugere caixas e classes, o esforço cognitivo necessário para validar passivamente a sugestão é ordens de grandeza menor do que o esforço para redelinear a caixa ou trocar o rótulo. O fato de 39,5% das caixas terem permanecido intocadas por ambos os anotadores infla artificialmente os coeficientes de concordância. A verdadeira consistência do julgamento humano é evidenciada nas caixas onde houve modificação: nelas, o Kappa de 16 classes recua para κ = 0,847. Esta é a medida honesta que deve embasar as conclusões da dissertação.

### 8.3. O Efeito do Colapso de Granularidade Taxonômica
A taxonomia de 16 classes exige distinções de alta carga semântica (como determinar se um bloco em negrito é um ato normativo `act` ou um título administrativo comum `title`, ou se um identificador `id` deve ser isolado do corpo `paragraph`). Como revelado na matriz de confusão, os maiores desacordos são puramente terminológicos, e não estruturais. Ao colapsar a taxonomia para 9 classes (extrator) e especialmente para 3 classes (texto/tabela/imagem, κ = 0,970), a concordância humana salta para níveis quase perfeitos. Para a tarefa downstream de Recuperação de Informação (segmentação de chunks e ordenação de leitura), o colapso preserva toda a informação necessária para o leitor e para o pipeline de embeddings.

### 8.4. Limitações Metodológicas Declaradas
1. **Tamanho amostral restrito:** Apenas uma fração das páginas do acervo possui dupla anotação concluída e não cancelada (333 páginas). Embora o cluster bootstrap atenue a incerteza fornecendo intervalos empíricos rigorosos, a variabilidade entre diários municipais e estaduais é ampla.
2. **Homogeneidade de anotadores:** Os dados provêm de equipe de pesquisa parceira treinada no mesmo guia, o que pode mitigar divergências conceituais grosseiras, mas perpetuar convenções compartilhadas.
3. **Casamento guloso estocástico:** Casamentos 1-1 por IoU assumem que caixas sobrepostas representam o mesmo fenômeno textual; fusões ou fracionamentos de blocos (1-para-N) são penalizados como falsos negativos/positivos de localização.
