# Metodologia Experimental: Dados, Representação, Métricas e Protocolo

Este capítulo descreve a metodologia experimental adotada para a investigação e avaliação sistemática da ordem de leitura em Diários Oficiais brasileiros. Estrutura-se a exposição em seis seções fundamentais: (1) a caracterização do acervo documental de diários oficiais, contemplando o universo de dados, os critérios de amostragem e a triagem de qualidade textual; (2) a fundamentação da representação atômica em linhas de texto combinadas a átomos estruturais de tabela e imagem, articulada ao histórico de superação dos erros de segmentação em blocos; (3) a definição, caracterização e partição dos conjuntos de avaliação humanos e automáticos, contrastando os papéis de ajuste, desenvolvimento externo e teste confirmatório; (4) a formulação matemática rigorosa das métricas de eficácia de ordenação, continuidade local e cobertura textual; (5) o protocolo experimental, detalhando a âncora metodológica de reprodutibilidade, as técnicas de inferência estatística por *bootstrap* e o pré-registro sistemático de hipóteses e cartões experimentais; e (6) a análise aprofundada das principais ameaças à validade científica e das limitações intrínsecas ao desenho do estudo.

---

## 1. Acervo de Diários Oficiais

### 1.1 Procedência e Dimensão do Acervo Primário
A pesquisa apoia-se em um acervo empírico expressivo de publicações governamentais brasileiras fornecido diretamente pelo docente orientador em 09/09/2026 <!-- fonte: docs/CONTEXTO_E_RECURSOS.md -->, composto por 8 <!-- fonte: docs/CONTEXTO_E_RECURSOS.md --> arquivos compactados no formato ZIP disponibilizados via Google Drive. A descompactação e o saneamento dos caminhos de diretório resultaram em um volume de 14,6 <!-- fonte: docs/DIARIO_DE_BORDO.md --> gigabytes (GB) compactados e 18,7 <!-- fonte: docs/DIARIO_DE_BORDO.md --> GB em disco, totalizando 4.660 <!-- fonte: docs/DIARIO_DE_BORDO.md --> arquivos, dos quais 4.644 <!-- fonte: docs/ACERVO.md --> constituem arquivos válidos no formato PDF (*Portable Document Format*) e 16 <!-- fonte: docs/DIARIO_DE_BORDO.md --> representam arquivos auxiliares de catalogação e controle.

O conjunto compreende uma estimativa conservadora de aproximadamente 310.000 <!-- fonte: docs/ACERVO.md --> páginas diagramadas, publicadas ao longo de uma janela temporal que se estende de 2010 <!-- fonte: docs/ACERVO.md --> a 2026 <!-- fonte: docs/ACERVO.md -->. A distribuição geográfica abrange 31 <!-- fonte: docs/CONTEXTO_E_RECURSOS.md --> pastas territoriais distintas, contemplando veículos estaduais de 23 <!-- fonte: docs/ACERVO.md --> Unidades Federativas (UFs) e 8 <!-- fonte: docs/ACERVO.md --> veículos municipais de capitais e cidades de grande porte (Congonhas-MG, Barra do Piraí-RJ, Duque de Caxias-RJ, Seropédica-RJ, Volta Redonda-RJ, Manaus-AM, Salvador-BA, Curitiba-PR, Japeri-RJ e Porto Alegre-RS <!-- fonte: src/eval/figuras.py -->). Quatro Unidades da Federação não figuram no acervo recebido: Goiás (GO), Distrito Federal (DF), Espírito Santo (ES) e Mato Grosso (MT) <!-- fonte: docs/ACERVO.md -->. A cadeia de custódia primária anterior à disponibilização pelo orientador (como eventuais rotinas de raspagem automatizada próprias ou cooperação com repositórios públicos como o projeto Querido Diário) não constava formalmente documentada nos arquivos de metadados <!-- fonte: docs/CONTEXTO_E_RECURSOS.md -->.

Em complemento a esse acervo de base, a pesquisa conta com o aproveitamento metodológico de um conjunto de anotações de um projeto parceiro, usado com autorização formal <!-- fonte: docs/PLANO_PESQUISA.md -->, cuja aplicação restringe-se estritamente aos ambientes de computação autorizados, sem incorporação a modelos ou repositórios externos.

### 1.2 Triagem de Qualidade, Camada Digital e Descarte de Veículos
Uma premissa de eficiência do presente trabalho consiste no aproveitamento da camada digital de texto embutida no próprio PDF, dispensando a aplicação generalizada de Reconhecimento Óptico de Caracteres (*Optical Character Recognition* — OCR) sobre o texto corrido. O diagnóstico automatizado de integridade revelou que cerca de 96% <!-- fonte: docs/ACERVO.md --> das páginas do acervo são genuinamente digitais, contendo texto programático acessível associado a fontes e coordenadas espaciais.

Entretanto, a integridade da extração de caracteres varia criticamente entre os órgãos emissores, em decorrência de distorções nas tabelas de mapeamento de fontes (*Font Encoding / ToUnicode CMap*). Quando o mapa de caracteres é corrompido durante a compilação do arquivo pelo órgão oficial, a extração de texto via bibliotecas programáticas como `pdfplumber` resulta em sequências de substituição ininteligíveis, expressas por glifos na forma `(cid:N)`. O diagnóstico amostral revelou os seguintes índices de ilegibilidade por veículo:
- **Piauí (`official_diary_pi`):** apresentou 86% <!-- fonte: docs/ACERVO.md --> de seu texto comprometido por codificação `(cid:N)`, inviabilizando qualquer processamento algorítmico do texto original. O veículo original foi inteiramente descartado das bancadas de referência, sendo provisoriamente substituído pelo subconjunto retificado `pi_v2` <!-- fonte: docs/ACERVO.md -->;
- **Acre (`official_diary_ac`):** apresentou 32% <!-- fonte: docs/ACERVO.md --> de caracteres ilegíveis, sendo classificado como inadequado para a extração de sequências automáticas (*silver labels*);
- **Rio de Janeiro (`official_diary_rj`):** registrou 2,8% <!-- fonte: docs/ACERVO.md --> de texto corrompido, índice contornável em nível de página;
- **Pernambuco (`official_diary_pe`):** apresentou 1,1% <!-- fonte: docs/ACERVO.md --> de falha, demandando filtragem pontual;
- **Demais veículos estaduais:** apresentaram 0% <!-- fonte: docs/ACERVO.md --> de texto comprometido na amostragem inicial.

Além da integridade das fontes, avaliou-se a concordância entre o fluxo de extração de palavras nativo do PDF (acionado via parâmetro `use_text_flow=True`) e a sequência lógica esperada da diagramação. Observou-se que o fluxo interno do arquivo reflete de forma fidedigna a ordem humana de leitura em apenas 11 <!-- fonte: docs/DIARIO_DE_BORDO.md --> dos 30 <!-- fonte: docs/DIARIO_DE_BORDO.md --> veículos analisados (adotando-se um limiar de concordância mediano de correlação de postos $\tau \ge 0,7$ <!-- fonte: docs/DIARIO_DE_BORDO.md --> contra a decomposição em colunas). Em veículos de coluna única e diagramação estritamente linear, como certas edições de Manaus e Tocantins, o fluxo de compilação gráfica interna revelou-se sistematicamente embaralhado. Essa constatação evidenciou que o fluxo bruto do PDF não pode ser assumido cegamente como ordem de leitura canônica, exigindo uma cuidadosa partição entre veículos cuja ordem nativa é aproveitável como referência preliminar (*silver*) e veículos dependentes de intervenção humana.

[FIGURA: docs/figuras/fig1_caracterizacao_por_veiculo.png]

---

## 2. Representação em Linhas e Átomos Estruturais

### 2.1 O Histórico do Problema: Fragmentação e Fusão em Blocos de Parágrafo
Nos estágios iniciais do projeto (fases documentadas em setembro de 2026), adotou-se a formulação tradicional da literatura de Análise de Leiaute de Documentos, na qual a página é particionada em "blocos de texto" delimitados por caixas envolventes retangulares (*bounding boxes*), correspondentes idealmente a parágrafos, seções ou atos administrativos. Sob esse paradigma, um algoritmo extrator agrupava palavras em linhas horizontais e, subsequentemente, fundia linhas adjacentes em caixas de parágrafo através de limiares de proximidade geométrica.

A avaliação qualitativa e quantitativa dessa abordagem revelou uma falha metodológica severa, decorrente de duas peculiaridades estruturais onipresentes na tipografia dos diários oficiais:
1. **Entradas em Negrito em Cabeças de Artigo:** Linhas iniciadas por termos destacados (tais como "**Art. 1º** Fica instituído...") apresentam espaçamentos e fontes diferenciados. O extrator inicial processava o corpo do parágrafo isoladamente e rejeitava a linha de abertura em negrito por ultrapassar a tolerância espacial de proximidade, gerando fragmentação artificial;
2. **Justificação Tipográfica Agressiva:** Em páginas organizadas em colunas estreitas, a justificação do texto expande os espaços entre palavras de forma pronunciada, criando vãos brancos de largura equivalente ou superior à largura de calhas entre colunas. Consequentemente, o extrator cortava linhas no meio de uma frase ou agrupava segmentos de colunas paralelas horizontais adjacentes em um mesmo bloco.

Como resultado, na segmentação inicial em blocos (versão v1), 28,6% <!-- fonte: docs/DIARIO_DE_BORDO.md --> dos blocos apresentavam sobreposição geométrica mútua, fenômeno observado em nada menos que 78% <!-- fonte: docs/DIARIO_DE_BORDO.md --> das páginas. Quando duas caixas se sobrepõem, o texto contido em seu interior é truncado e intercalado internamente antes mesmo de qualquer tentativa de ordenação. Estabeleceu-se, portanto, um "teto intransponível de erro": nenhuma técnica de ordenação de blocos — por mais sofisticada que fosse a rede neural ou o modelo de linguagem — era capaz de reconstruir a ordem de leitura correta, visto que as sentenças já se encontravam corrompidas dentro das próprias unidades elementares entregues ao modelo.

Tentativas subsequentes de refinar os limiares de agrupamento de blocos (versões B e C do extrator) demonstraram um dilema insolúvel: a imposição de regras restritivas para evitar a sobreposição de colunas resultava em hiperfragmentação em certos estados (a exemplo de edições do Maranhão que saltavam de 36 <!-- fonte: docs/HANDOFF.md --> para 85 <!-- fonte: docs/HANDOFF.md --> blocos, e do Rio de Janeiro que passavam de 53 <!-- fonte: docs/HANDOFF.md --> para 159 <!-- fonte: docs/HANDOFF.md --> caixas), enquanto em outros veículos o algoritmo fundia textos longos em megablocos indivisíveis (no Ceará, páginas inteiras de texto corrido colapsavam em apenas 2 <!-- fonte: docs/HANDOFF.md --> blocos monolíticos).

### 2.2 A Transição para a Representação em Linhas + Átomos (ls3)
A superação desse impasse deu-se com uma ruptura de representação concebida no início de outubro de 2026: **a eliminação definitiva de caixas finas de parágrafo como unidades de ordenação**. A representação adotada neste trabalho ancora-se em duas entidades primárias:
1. **Linhas Físicas de Texto:** Unidades atômicas de escrita, geradas geometricamente pela projeção horizontal de palavras contíguas que compartilham linha de base e não cruzam calhas verticais confirmadas;
2. **Átomos Estruturais Indivisíveis:** Regiões complexas que possuem estrutura interna bidimensional própria, tais como tabelas (*tables*) e figuras/imagens (*pictures* ou selos/brasões), tratadas como nós monolíticos na sequência global de leitura.

Para a detecção automática desses átomos estruturais, emprega-se o detector neural YOLO modelo `ls3`, treinado especificamente para a segmentação de tabelas e figuras em diários oficiais, com desempenho congelado de mAP50 de 0,826 <!-- fonte: docs/CONTEXTO_E_RECURSOS.md -->. Na inferência, retêm-se os átomos estruturais com limiar de confiança $\ge 0,45$ <!-- fonte: resultados/erros_ponta_a_ponta.md -->, IoU de supressão de não-máximos de 0,7 <!-- fonte: resultados/erros_ponta_a_ponta.md --> e resolução de entrada de 1.024 <!-- fonte: resultados/erros_ponta_a_ponta.md --> pixels. Todo o texto não pertencente a um átomo é decomposto estritamente em suas linhas constituintes.

A ordenação das palavras *no interior* de cada unidade atômica (dentro de cada linha ou no interior das células de uma tabela) é congelada via fluxo geométrico canônico horizontal (`ordem_sem_bbox.fluxo()`), cabendo aos modelos e ordenadores determinar exclusivamente a permutação das unidades atômicas na página <!-- fonte: docs/RELATORIO_NOITE_0410.md -->.

### 2.3 Evidência Empírica da Superioridade da Representação (213 → 29 quebras)
A comprovação empírica definitiva da superioridade da representação atômica em linhas foi formalizada no experimento de erros de ponta a ponta <!-- fonte: resultados/erros_ponta_a_ponta.md -->, que avaliou 71 <!-- fonte: resultados/erros_ponta_a_ponta.md --> páginas de 27 <!-- fonte: resultados/erros_ponta_a_ponta.md --> veículos distintos, comparando pipelines baseados em blocos de parágrafo (P1 e sua variante com tratamento de margens P1m) contra o pipeline em linhas com átomos ls3 (P2).

O indicador mais contundente dessa análise reside no **piso irredutível de erro interno**: trata-se da contagem de pares de palavras consecutivas incorretas emitidas no interior de uma mesma unidade atômica, as quais jamais poderiam ser corrigidas por nenhuma permutação posterior das unidades entregues ao ordenador. Conforme documentado no relatório experimental:
- O pipeline clássico em caixas de parágrafo (P1) apresentou um piso interno de **213 quebras** <!-- fonte: resultados/erros_ponta_a_ponta.md --> (correspondendo a 18,6% <!-- fonte: resultados/erros_ponta_a_ponta.md --> de todas as quebras observadas na amostragem);
- A variante com ajuste geométrico de margens (P1m) manteve o mesmo piso de **213 quebras** <!-- fonte: resultados/erros_ponta_a_ponta.md --> (representando 30,4% <!-- fonte: resultados/erros_ponta_a_ponta.md --> de suas quebras);
- O pipeline fundamentado em linhas + átomos ls3 (P2) reduziu esse piso para apenas **29 quebras** <!-- fonte: resultados/erros_ponta_a_ponta.md --> (apenas 5,6% <!-- fonte: resultados/erros_ponta_a_ponta.md --> do total).

Essa redução drástica de 213 <!-- fonte: resultados/erros_ponta_a_ponta.md --> para 29 <!-- fonte: resultados/erros_ponta_a_ponta.md --> quebras internas demonstrou que a segmentação em linhas isola os erros geométricos nas fronteiras naturais do texto, transferindo a quase totalidade do desafio para a etapa de inferência de ordem. No cômputo geral da macro-amostra de 71 <!-- fonte: resultados/erros_ponta_a_ponta.md --> páginas:
- O baseline ingênuo sem detector (P0) registrou média de 85,46 <!-- fonte: resultados/erros_ponta_a_ponta.md --> quebras por página;
- O método clássico de blocos com XY-cut (P1) registrou 16,14 <!-- fonte: resultados/erros_ponta_a_ponta.md --> quebras por página;
- O método de blocos com recorte de margens (P1m) atingiu 9,87 <!-- fonte: resultados/erros_ponta_a_ponta.md --> quebras por página;
- O pipeline proposto em linhas e átomos (P2) alcançou **7,25 quebras por página** <!-- fonte: resultados/erros_ponta_a_ponta.md -->, consubstanciando uma redução média de 55,1% <!-- fonte: resultados/erros_ponta_a_ponta.md --> frente ao P1 (Δ = −8,89 [IC 95%: −13,13; −4,89] <!-- fonte: resultados/erros_ponta_a_ponta.md -->) e de 26,5% <!-- fonte: resultados/erros_ponta_a_ponta.md --> frente ao P1m (Δ = −2,62 [IC 95%: −5,77; 0,18] <!-- fonte: resultados/erros_ponta_a_ponta.md -->).

Ademais, a análise de teto teórico revelou que a representação em linhas atinge teto quase perfeito: quando as unidades são ordenadas segundo o gabarito humano, o teto residual de erro é de apenas 0,89 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> quebras por página no `golden_v4` e 0,70 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> no `golden_v3_novo`, com correlação $\tau = 1,000$ <!-- fonte: docs/RELATORIO_NOITE_0410.md --> e preservação de trechos contíguos de 12 palavras em 99,7% <!-- fonte: docs/RELATORIO_NOITE_0410.md --> e 99,8% <!-- fonte: docs/RELATORIO_NOITE_0410.md -->, respectivamente. Em contrapartida, representações intermediárias baseadas em faixas amplas de coluna apresentaram teto intrínseco limitado a 5,20 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> quebras por página, em decorrência de erros internos de empacotamento vertical.

[FIGURA: docs/figuras/fig2_problema_pagina_real.png]

---

## 3. Conjuntos de Avaliação e Particionamento de Dados

### 3.1 Composição e Papel das Bancadas de Avaliação
O desenho experimental estrutura-se sobre uma hierarquia deliberada de conjuntos de dados, separando rigidamente os conjuntos destinados à exploração, calibragem e desenvolvimento daqueles reservados a validações externas e confirmação estatística. As versões dos arquivos de dados são rastreadas por identificadores criptográficos SHA-256 (tabela de versões D1 <!-- fonte: experimentos/DATASETS.md -->), assegurando que nenhum dado seja alterado retrospectivamente.

A composição dos conjuntos opera segundo os seguintes estratos:

| Conjunto | Tamanho | Origem da Referência | Papel Metodológico | Risco de Reúso / Condição |
|---|---:|---|---|---|
| **`golden_v4`** | 44 págs. <!-- fonte: docs/RELATORIO_V4.md --> (27 UFs <!-- fonte: resultados/erros_ponta_a_ponta.md -->) | Humana (especialista) sobre regiões Diamond | **Ajuste e Desenvolvimento** (escolha de limiares, regras e parada) | Já consultado extensivamente; alto viés de ancoragem exploratória |
| **`golden_v3_novo`** | 27 págs. <!-- fonte: resultados/erros_ponta_a_ponta.md --> (10 UFs <!-- fonte: resultados/erros_ponta_a_ponta.md -->) | Humana (anotação v3 fora das tarefas v4) | **Desenvolvimento Externo** (verificação de generalização preliminar) | Já consultado em rodadas prévias de outubro; serve como controle externo relativo |
| **Validação Silver RN** | 15 págs. <!-- fonte: docs/DIARIO_DE_BORDO.md --> (1 UF) | Fluxo nativo confiável do PDF (`use_text_flow`) | **Validação de Treino** (seleção de checkpoints de modelos neurais) | Isolado do teste; acoplado estritamente ao conjunto de ajuste |
| **Teste Silver CE/MA/RJ** | 89 págs. <!-- fonte: docs/RELATORIO_NOITE_0410.md --> (3 UFs) | Fluxo nativo confiável do PDF (`use_text_flow`) | **Avaliação Externa em Larga Escala** (veículos nunca vistos no treino) | Não supervisionado; ruído inerente ao fluxo nativo em tabelas |
| **Treino Silver** | 3.140 págs. <!-- fonte: docs/RELATORIO_NOITE_0410.md --> (7 UFs <!-- fonte: data/processed/splits.json -->) | Fluxo nativo em linhas + átomos ls3 | **Treino Supervisionado** de modelos aprendidos | Congelado no arquivo `treino_noite.json` <!-- fonte: experimentos/DATASETS.md --> |
| **Teste Cego (E001)** | 90 págs. <!-- fonte: docs/PLANO_PESQUISA.md --> (3 UFs) | Humana (anotação cega em preparação) | **Teste Confirmatório Final** (avaliação de hipótese central) | **Lacrado** até a rodada final; blindado contra inspeção de código |

### 3.2 O Problema do Reúso de Amostras e a Necessidade do Teste Cego
A integridade dos achados experimentais em tarefas de ordenação de documentos confronta um desafio metodológico frequentemente negligenciado: o **sobreajuste de projeto decorrente do reúso cumulativo de dados de teste** (*test set fatigue* ou *data snooping*). 

O lote `golden_v4` constitui o conjunto humano mais refinado do projeto: compreende 44 <!-- fonte: docs/RELATORIO_V4.md --> páginas concluídas (de 45 <!-- fonte: docs/RELATORIO_V4.md --> tarefas originais, com 1 <!-- fonte: docs/RELATORIO_V4.md --> página excluída por deslocamento na caixa do PDF), anotadas pelo especialista humano (Pedro Alano <!-- fonte: docs/RELATORIO_V4.md -->) sobre regiões retificadas na ferramenta Diamond. O esforço humano mediano de ordenação foi de 16,0 <!-- fonte: docs/RELATORIO_V4.md --> segundos por página (total de 12,8 <!-- fonte: docs/RELATORIO_V4.md --> minutos para o conjunto). Contudo, o `golden_v4` foi utilizado iterativamente como banco de ensaio para a formulação da própria regra de colunas e para a fixação de heurísticas de margem. 

Essa exposição contínua gera sobreajuste evidente. Um exemplo documentado ocorreu no desenvolvimento de regras de margem por repetição entre páginas do mesmo PDF: no `golden_v4`, a heurística reduziu as quebras de 6,05 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> para 4,89 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> por página; ao ser aplicada ao conjunto externo `golden_v3_novo`, a mesma regra provocou uma **piora de +1,00 quebra por página** <!-- fonte: docs/RELATORIO_NOITE_0410.md -->, demonstrando que o algoritmo havia memorizado idiossincrasias da amostra de ajuste. Similarmente, o melhor resultado histórico do projeto — o modelo híbrido por densidade, que aciona o LayoutReader em páginas de até 67 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> unidades e a regra de colunas nas páginas densas — teve seu limiar escolhido estritamente no `golden_v4` (atingindo 5,14 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> quebras no v4, 7,89 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> no v3 novo e 26,43 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> no silver <!-- fonte: docs/RELATORIO_NOITE_0410.md -->).

Embora o `golden_v3_novo` (27 <!-- fonte: resultados/erros_ponta_a_ponta.md --> páginas) represente páginas externas ao v4, ele já foi inspecionado em rodadas experimentais anteriores, operando como conjunto semi-explorado. Para restabelecer o rigor da inferência confirmatória, o plano de pesquisa formalizou o experimento E001 <!-- fonte: docs/PLANO_PESQUISA.md -->: a criação de um **teste cego lacrado**, composto por 90 <!-- fonte: docs/PLANO_PESQUISA.md --> páginas extraídas de PDFs nunca antes manipulados no projeto (30 do Ceará, 30 do Maranhão e 30 do Rio de Janeiro; distribuídas em aproximadamente 15 PDFs por estado, com no máximo 2 páginas por PDF <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->). Os identificadores dessas páginas permanecem bloqueados criptograficamente sob o arquivo `TESTE_CEGO.lock` <!-- fonte: experimentos/README.md -->. As predições dos modelos serão submetidas a esse teste uma única vez, no encerramento da campanha experimental, impedindo retroalimentação de hiperparâmetros.

---

## 4. Métricas de Avaliação

A mensuração da eficácia de um ordenador de leitura requer métricas que combinem a fidelidade da ordem global com a continuidade local necessária à leitura humana e ao processamento downstream de PLN e RI.

### 4.1 Coeficiente $\tau$ de Kendall Ponderado por Palavras
O coeficiente de correlação de postos $\tau$ de Kendall mede a concordância global relativa entre a sequência predita e a sequência de referência. Diferentemente de métricas posicionais absolutas — a exemplo da fração de elementos fora do posto exato, que padece de efeito cascata —, o $\tau$ avalia a consistência de ordenação para cada par não ordenado de elementos.

Neste trabalho, o $\tau$ é computado **estritamente sobre a sequência de palavras com referência válida**, e não sobre blocos ou linhas agregadas. Seja $W = \{w_1, w_2, \dots, w_M\}$ o conjunto de $M$ palavras presentes na página para as quais existe anotação no padrão-ouro. Dadas as permutações bijetivas $\pi_{\text{pred}}$ e $\pi_{\text{gt}}$ que mapeiam cada palavra $w \in W$ aos seus respectivos postos nas sequências predita e de referência, define-se:

$$\tau = \frac{C - D}{\frac{1}{2} M (M - 1)}$$

Onde:
- $C$ é o número de pares de palavras $(w_i, w_j)$, com $i < j$, que são **concordantes**, isto é:
  $$(\pi_{\text{gt}}(w_i) < \pi_{\text{gt}}(w_j) \land \pi_{\text{pred}}(w_i) < \pi_{\text{pred}}(w_j)) \;\lor\; (\pi_{\text{gt}}(w_i) > \pi_{\text{gt}}(w_j) \land \pi_{\text{pred}}(w_i) > \pi_{\text{pred}}(w_j))$$
- $D$ é o número de pares **discordantes**, nos quais a ordem relativa inverte-se na predição:
  $$(\pi_{\text{gt}}(w_i) < \pi_{\text{gt}}(w_j) \land \pi_{\text{pred}}(w_i) > \pi_{\text{pred}}(w_j)) \;\lor\; (\pi_{\text{gt}}(w_i) > \pi_{\text{gt}}(w_j) \land \pi_{\text{pred}}(w_i) < \pi_{\text{pred}}(w_j))$$

O coeficiente varia no intervalo $[-1, 1]$, onde $+1$ indica concordância perfeita, $0$ expressa ausência de correlação estatística e $-1$ denota inversão completa da sequência.

### 4.2 Quebras de Leitura por Página e Quebras por Mil Palavras
Embora o $\tau$ capture a conformidade macroscópica da ordenação, ele falha em discriminar a **continuidade local**. Uma troca isolada de dois blocos adjacentes penaliza apenas um par discordante no $\tau$, porém quebra o fluxo de leitura de duas a três sentenças. Por essa razão, este projeto estabelece as **quebras de continuidade** como métrica primária de eficácia.

Seja $\pi_{\text{gt}} = (g_1, g_2, \dots, g_M)$ a sequência ordenada de palavras do gabarito humano, e defina-se a função sucessor canônico $\text{prox}(g_k) = g_{k+1}$ para $k \in \{1, \dots, M-1\}$, com $\text{prox}(g_M) = \emptyset$. Seja $S = (s_1, s_2, \dots, s_K)$ a sequência completa de palavras emitida pelo algoritmo avaliado (incluindo palavras livres que porventura não constem no gabarito). Uma transição entre duas palavras consecutivas com referência na predição, $s_a$ e $s_b$, constitui uma **quebra de continuidade** se $s_b$ não for o sucessor canônico de $s_a$, ou se a transição foi fisicamente interrompida pela interposição de palavras não referenciadas. Formalmente:

$$Q = \sum_{k=1}^{K-1} \mathbb{I}\Big(\text{prox}(s_k) \neq s_{k+1} \;\lor\; \text{livre}(s_k, s_{k+1})\Big)$$

Onde $\mathbb{I}(\cdot)$ denota a função indicadora. Para comparar páginas com diferentes volumes de texto de forma justa, computa-se também a taxa normalizada de quebras por 1.000 palavras elegíveis:

$$Q_{\text{mil}} = \frac{Q \times 1000}{M}$$

### 4.3 Acurácia de Sucessor de Linhas
Para avaliar se o algoritmo preserva a contiguidade física das linhas tipográficas (evitando que linhas de uma coluna sejam intercaladas em outra), define-se a acurácia de sucessor de linhas.

Seja $\mathcal{L}_{\text{gt}} = (L_1, L_2, \dots, L_P)$ a sequência de $P$ linhas de referência do documento, onde cada linha $L_j = (w_{j,1}, w_{j,2}, \dots, w_{j,|L_j|})$ é composta por uma sequência de palavras anotadas. Uma linha $L_j$ é definida como **intacta** na predição se e somente se todas as suas palavras surgem de maneira estritamente adjacente e na mesma ordem na sequência predita:

$$\text{intacta}(L_j) = \forall k \in \{1, \dots, |L_j|-1\}, \quad \text{pos}(w_{j, k+1}) = \text{pos}(w_{j, k}) + 1$$

Um par de linhas consecutivas $(L_j, L_{j+1})$ é computado como um **sucessor de linhas correto** se ambas as linhas estiverem intactas e a primeira palavra de $L_{j+1}$ suceder diretamente a última palavra de $L_j$:

$$\text{sucessor\_válido}(L_j, L_{j+1}) = \text{intacta}(L_j) \;\land\; \text{intacta}(L_{j+1}) \;\land\; \Big(\text{pos}(w_{j+1, 1}) = \text{pos}(w_{j, |L_j|}) + 1\Big)$$

A acurácia de sucessor de linhas representa a fração de transições interlinhas corretas:

$$\text{Acc}_{\text{suc}} = \frac{\sum_{j=1}^{P-1} \mathbb{I}\Big(\text{sucessor\_válido}(L_j, L_{j+1})\Big)}{P - 1}$$

### 4.4 Cobertura de Palavras
Para garantir que nenhum método seja artificialmente favorecido pela omissão ou descarte de elementos de difícil ordenação (tais como cabeçalhos densos, assinaturas marginais ou notas de rodapé), impõe-se a métrica de controle de cobertura:

$$\text{Cob} = \frac{|W_{\text{emitidas}} \cap W_{\text{PDF}}|}{|W_{\text{PDF}}|} \times 100\%$$

O contrato experimental do projeto exige que a cobertura seja de 100% <!-- fonte: docs/PLANO_PESQUISA.md --> para todo e qualquer ordenador executado sobre o texto digital. Predições que truncam unidades ou não devolvem permutações válidas são invalidadas ou penalizadas com o envio de palavras residuais ao final da página.

### 4.5 Exemplo Pedagógico Comparativo
Para ilustrar a divergência entre as métricas, considere-se uma página simplificada diagramada em duas colunas, contendo 4 linhas de texto com 2 palavras cada ($M = 8$ palavras):
- Coluna 1: Linha $L_1 = [w_1, w_2]$, Linha $L_2 = [w_3, w_4]$
- Coluna 2: Linha $L_3 = [w_5, w_6]$, Linha $L_4 = [w_7, w_8]$

A sequência canônica de leitura humana percorre a coluna 1 de cima para baixo e, a seguir, a coluna 2:
$$\pi_{\text{gt}} = (w_1, w_2, w_3, w_4, w_5, w_6, w_7, w_8)$$

Suponha que um algoritmo ingênuo realize a leitura horizontal linha por linha, intercalando as colunas ($L_1 \to L_3 \to L_2 \to L_4$):
$$\pi_{\text{pred}} = (w_1, w_2, w_5, w_6, w_3, w_4, w_7, w_8)$$

Nesse cenário:
1. **$\tau$ de Kendall:** O número total de pares possíveis é $\frac{8 \times 7}{2} = 28$. Na sequência predita, apenas os pares formados entre $\{w_5, w_6\}$ e $\{w_3, w_4\}$ estão invertidos (4 inversões: $(w_5, w_3), (w_5, w_4), (w_6, w_3), (w_6, w_4)$). Assim, $C = 24$ e $D = 4$:
   $$\tau = \frac{24 - 4}{28} = \frac{20}{28} \approx 0,714$$
   O $\tau$ registra um índice aparentemente satisfatório ($\approx 0,71$), mascarando o fato de que a leitura está severamente comprometida.
2. **Quebras de Continuidade:** As transições entre palavras consecutivas na predição são:
   - $(w_1, w_2)$: correta ($\text{prox}(w_1) = w_2$);
   - $(w_2, w_5)$: **quebra** ($\text{prox}(w_2) = w_3 \neq w_5$);
   - $(w_5, w_6)$: correta ($\text{prox}(w_5) = w_6$);
   - $(w_6, w_3)$: **quebra** ($\text{prox}(w_6) = w_7 \neq w_3$);
   - $(w_3, w_4)$: correta ($\text{prox}(w_3) = w_4$);
   - $(w_4, w_7)$: **quebra** ($\text{prox}(w_4) = w_5 \neq w_7$);
   - $(w_7, w_8)$: correta ($\text{prox}(w_7) = w_8$).
   Totalizam-se $Q = 3$ quebras em 7 transições ($Q_{\text{mil}} = \frac{3 \times 1000}{8} = 375$ quebras por mil palavras).
3. **Acurácia de Sucessor de Linhas:** As linhas individuais mantiveram suas palavras adjacentes (todas as 4 linhas estão intactas). Contudo, os pares consecutivos esperados são $(L_1, L_2)$, $(L_2, L_3)$ e $(L_3, L_4)$. Na saída predita, as transições interlinhas foram $L_1 \to L_3$, $L_3 \to L_2$ e $L_2 \to L_4$. Nenhuma das transições emitidas coincide com a referência. Logo:
   $$\text{Acc}_{\text{suc}} = \frac{0}{3} = 0,0\%$$
O exemplo evidencia com clareza como a acurácia de sucessor e as quebras expõem instantaneamente a destruição da continuidade sintática, ao passo que o $\tau$ pontual preserva um valor artificialmente elevado.

---

## 5. Protocolo Experimental e Inferência Estatística

### 5.1 Âncora Metodológica Obrigatória de Reprodutibilidade
Para resguardar o projeto contra regressões silenciosas de código, alterações de ambiente ou inconsistências em bibliotecas numéricas, adota-se o princípio da **Âncora Obrigatória**: nenhum script ou relatório experimental é aceito como válido se não reproduzir previamente, com precisão de seis casas decimais, as métricas da regra geométrica de colunas sobre o conjunto `golden_v4` <!-- fonte: orquestracao/analises/bancada_ordenadores.py -->:
- $\tau$ de palavras: **0,985948** <!-- fonte: orquestracao/analises/bancada_ordenadores.py -->
- Quebras por página: **6,045455** <!-- fonte: orquestracao/analises/bancada_ordenadores.py -->

A validação dessa âncora é executada deterministicamente no início de qualquer pipeline de teste através da importação de `orquestracao/analises/bancada_ordenadores.py`. Caso os valores divirjam, a execução é compulsoriamente abortada para investigação de integridade.

Adicionalmente, para garantir que nenhum método usufrua da ordenação implícita em que os objetos foram gravados no arquivo PDF, a entrada de cada página é submetida a um embaralhamento pseudoaleatório reprodutível, fixado pela função `random.Random(f"entrada-{page_id}")` proveniente de `src/eval/protocolo.py` <!-- fonte: src/eval/protocolo.py -->.

### 5.2 Inferência Estatística e Tratamento de Dependência Intra-Documental
Documentos jurídicos e diários oficiais apresentam forte correlação de estilo tipográfico intra-documental: páginas pertencentes a uma mesma edição de um diário compartilham diagramadores, fontes, larguras de coluna e padrões de cabeçalho. Tratar páginas de um mesmo PDF como observações independentes e identicamente distribuídas (*i.i.d.*) falseia os testes de hipótese, subestimando as variâncias e gerando intervalos de confiança artificialmente estreitos.

Para contornar essa ameaça, a inferência estatística do projeto adota formalmente:
1. **Intervalos de Confiança por Bootstrap Agrupado (*Cluster Bootstrap*):** Computam-se intervalos de confiança percentis de 95% baseados em $B = 5.000$ <!-- fonte: resultados/erros_ponta_a_ponta.md --> reamostragens com reposição agrupadas por veículo e PDF (semente congelada `20261003` <!-- fonte: resultados/erros_ponta_a_ponta.md -->). O procedimento sorteia veículos inteiros, preservando a totalidade de suas páginas associadas e calculando a macro-média;
2. **Testes Pareados de Postos com Sinais de Wilcoxon / Pratt:** A significância estatística das diferenças pareadas entre métodos ($\Delta \tau$ e $\Delta Q$) é aferida pelo teste de postos com sinais de Wilcoxon. Quando há presença expressiva de empates pontuais (diferenças nulas entre métodos em páginas simples), utiliza-se o método de Pratt (`zero_method='pratt'`) <!-- fonte: resultados/erros_ponta_a_ponta.md -->;
3. **Correção para Comparações Múltiplas:** Toda bateria de testes pareados envolvendo múltiplos modelos contra o baseline é submetida à correção estrita de taxas de erro por família via procedimento de **Holm-Bonferroni** com nível de significância global $\alpha = 0,05$ <!-- fonte: docs/RELATORIO_V4.md -->.

### 5.3 Pré-Registro de Hipóteses, Cartões e Registro de Resultados Negativos
Em estrita observância às melhores práticas de ciência aberta e reprodutibilidade empírica, a fase de investigações do projeto adotou o pré-registro compulsório de hipóteses antes da execução dos experimentos. Cada iniciativa experimental é regida por um **Cartão de Experimento** individual arquivado em `experimentos/cards/E###_*.md`, no qual constam previamente formuladas a pergunta científica, a hipótese associada constante em `experimentos/HIPOTESES.md`, o critério quantitativo pré-registrado de sucesso (*go*) e o critério explícito de abandono (*no-go*) <!-- fonte: experimentos/README.md -->.

O critério formal de superioridade para o método final foi pré-registrado da seguinte forma <!-- fonte: docs/PLANO_PESQUISA.md -->:
- Redução de pelo menos 10% <!-- fonte: docs/PLANO_PESQUISA.md --> nas quebras de leitura sobre a macro-média das UFs;
- Intervalo de confiança de 95% do $\Delta Q$ estritamente abaixo de zero;
- Nenhum veículo apresentando degradação superior a 0,5 <!-- fonte: docs/PLANO_PESQUISA.md --> quebra por página;
- Idêntica cobertura de palavras (100% <!-- fonte: docs/PLANO_PESQUISA.md -->) e conformidade de representação.

Todas as execuções são compulsoriamente registradas no arquivo sequencial `experimentos/registro.jsonl` <!-- fonte: experimentos/README.md -->, registrando o hash do commit Git, os parâmetros de configuração e o hash dos dados de entrada. Abordagens que falham em superar os baselines ou que demonstram inviabilidade prática não são descartadas da narrativa científica; são integralmente documentadas e catalogadas no arquivo `experimentos/NAO_FUNCIONOU.md` <!-- fonte: experimentos/NAO_FUNCIONOU.md -->, prevenindo a duplicação inútil de esforços computacionais e enriquecendo a discussão sobre as limitações dos modelos testados.

---

## 6. Ameaças à Validade

A análise crítica dos procedimentos e resultados experimentais impõe o mapeamento explícito das ameaças à validade que circunscrevem as conclusões do trabalho:

### 6.1 Validade de Conclusão e Poder Estatístico
1. **Dimensão dos Conjuntos Humanos:** As bancadas de anotação humana especializada (`golden_v4` com 44 <!-- fonte: docs/RELATORIO_V4.md --> páginas e `golden_v3_novo` com 27 <!-- fonte: resultados/erros_ponta_a_ponta.md --> páginas) possuem dimensões compactas em razão do custo cognitivo e da morosidade da rotulação manual. Consequentemente, para diferenças moderadas de desempenho entre modelos neurais, o poder estatístico dos testes pareados é limitado, resultando em intervalos de confiança amplos que frequentemente interceptam o zero após correções para múltiplos testes <!-- fonte: docs/RELATORIO_V4.md -->;
2. **Variância Estocástica entre Sementes:** O treinamento de modelos neurais conscientes de layout (como o LayoutLM) exibiu variabilidade mensurável entre sementes aleatórias de inicialização (oscilação observada de 0,3 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> a 0,5 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> quebra por página entre as sementes 42 e 43 <!-- fonte: docs/RELATORIO_NOITE_0410.md -->). Essa oscilação estocástica assemelha-se à magnitude de ganho de certas heurísticas geométricas finas, exigindo cautela na atribuição de causalidade aos hiperparâmetros de arquitetura;
3. **Ruído na Referência Silver:** No conjunto de teste silver (89 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> páginas), a ordem de referência baseia-se no fluxo programático do PDF. Como o fluxo do PDF discorda da leitura humana em tabelas densas, o piso intrínseco de quebras da referência silver é elevado (17,12 <!-- fonte: docs/RELATORIO_NOITE_0410.md --> quebras no teto teórico), tornando esse conjunto ruidoso para a avaliação de ganhos finos em estruturas complexas.

### 6.2 Validade Interna
1. **Anotador Único Especialista:** A totalidade dos lotes humanos de referência (`golden_v1`, `v2`, `v3` e `v4`) foi anotada por um único especialista humano (Pedro Alano <!-- fonte: docs/RELATORIO_V4.md -->). A ausência de uma campanha sistemática de múltiplos anotadores independentes para o `golden_v4` impede o cálculo formal da concordância inter-anotador (*Cohen's Kappa* ou correlação $\tau$ inter-humana), de modo que o gabarito embute decisões interpretativas idiossincráticas do especialista em casos de ambiguidade de leitura <!-- fonte: docs/RELATORIO_V4.md -->;
2. **Viés de Ancoragem na Retificação do Diamond:** No preparo do lote `golden_v4`, o anotador humano refinou caixas e rótulos semânticos sobre uma proposta geométrica preliminar gerada algorítmicamente <!-- fonte: docs/RELATORIO_V4.md -->. A apresentação prévia dos contornos calculados induz um viés cognitivo de ancoragem (*anchoring effect*), no qual o humano tende a aceitar fronteiras propostas que não desenharia espontaneamente em uma tela em branco;
3. **Mudança Simultânea de Referência e Geometria:** Na transição histórica do `golden_v3` para o `golden_v4`, alterou-se concomitantemente a geometria das caixas e a ordem de referência anotada <!-- fonte: docs/RELATORIO_V4.md -->. Essa dupla modificação dificulta a decomposição analítica precisa entre a fração de ganho decorrente da melhora da segmentação e a fração originada da reordenação humana.

### 6.3 Validade de Construto
1. **Saturação de Métricas Tradicionais (Insensibilidade do BLEU):** A adoção histórica do BLEU de página como métrica de ordenação revelou-se inadequada para granularidades amplas. Conforme demonstrado empiricamente nas etapas preliminares do projeto, uma página com blocos de parágrafo totalmente invertidos ($\tau = -1$) mantinha um índice BLEU artificialmente elevado de **82,7** <!-- fonte: docs/DIARIO_DE_BORDO.md -->, uma vez que a quase totalidade dos n-gramas lexicais é interna aos blocos e sobrevive intacta a qualquer permutação grosseira. Daí decorre a necessidade construtiva da adoção das quebras de continuidade e do sucessor de linhas;
2. **Definições Operacionais de Quebra:** A contagem de quebras depende da hipótese de que toda transição que diverge do gabarito prejudica a leitura. Em determinados atos normativos dotados de independência semântica (por exemplo, portarias isoladas dispostas em colunas adjacentes sob um mesmo cabeçalho geral), a leitura de uma coluna antes da outra pode ser semanticamente indiferente para o leitor humano, mas é penalizada como quebra pela métrica operacional.

### 6.4 Validade Externa e Generalização
1. **Lacunas Geográficas no Acervo:** Conforme exposto na Seção 1.1, o acervo primário não contempla publicações oficiais de Goiás, Distrito Federal, Espírito Santo e Mato Grosso <!-- fonte: docs/ACERVO.md -->. Em que pese a diversidade tipográfica dos 23 estados cobertos, os resultados obtidos não podem ser generalizados universalmente para normas gráficas específicas de diários desses quatro entes federativos;
2. **Páginas Impressas em Imagem Rasterizada:** O pipeline atual assume a presença de texto digital acessível. Levantamentos amostrais registraram que aproximadamente 13,8% <!-- fonte: docs/RELATORIO_V4.md --> das páginas do acervo apresentam atos ou páginas inteiras em formato puramente gráfico (imagens digitalizadas de decretos antigos, extratos orçamentários escaneados ou carimbos institucionais) desprovidos de texto na camada digital. Como o pipeline corrente não integra OCR de forma nativa sobre essas regiões, tais conteúdos permanecem invisíveis aos modelos de ordenação, restringindo o escopo das conclusões às porções digitais dos diários oficiais.
