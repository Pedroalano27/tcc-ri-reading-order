# Resultados da Fase de Métodos Aprendidos sobre Linhas (Novembro de 2026)

Este capítulo apresenta os resultados empíricos da fase de investigação focada em métodos aprendidos sobre a representação em linhas de texto combinadas a átomos estruturais indivisíveis. A exposição organiza-se em seis eixos analíticos fundamentais: (1) o protocolo experimental de governança, caracterizando os critérios pré-registrados, a partição rigorosa entre conjuntos de ajuste e testes externos e o lacre confirmatório do teste cego; (2) os limites teóricos alcançáveis pelas distintas famílias de intervenção, determinados mediante formulações oraculares de potencial máximo; (3) a avaliação dos sinais de ordenação derivados de geometria aprendida, modelos causais de linguagem e seleção em nível de página; (4) a análise aprofundada da tensão conceitual e empírica entre continuidade local e preservação da macro-ordem global; (5) o estudo de granularidade entre caixas de parágrafo e linhas atômicas; e (6) a síntese integrativa dos resultados e suas implicações para o encerramento do projeto.

---

## 1. Protocolo Experimental e Governança Metodológica

### 1.1 Critérios Pré-Registrados e Governança Contra Sobreajuste
A fase experimental de novembro de 2026 foi desenhada para superar a principal ameaça metodológica diagnosticada nas fases preliminares do projeto: a seleção de hiperparâmetros ou regras baseada na inspeção cumulativa de bancadas de teste, resultando em sobreajuste ao leiaute dos conjuntos consultados <!-- fonte: docs/PLANO_PESQUISA.md -->. Para assegurar validade confirmatória, estabeleceu-se um protocolo de governança experimental restritivo, documentado no plano de pesquisa <!-- fonte: docs/PLANO_PESQUISA.md --> e operado por cartões pré-registrados em `experimentos/cards/` <!-- fonte: experimentos/REGISTRO.md -->.

Todo experimento formulado nesta fase obedece às seguintes regras mandatórias:
1. **Critérios de Decisão Antecipados:** Todo cartão experimental fixa formalmente suas hipóteses, seu critério de sucesso quantitativo (*GO*) e seu critério de abandono (*NÃO GO*) antes do início da execução ou inspeção das saídas <!-- fonte: docs/PLANO_PESQUISA.md -->;
2. **Separação Funcional de Conjuntos:** A busca de hiperparâmetros, pontos de corte, calibrações de probabilidade e seleção de modelos restringe-se exclusivamente ao conjunto de ajuste. As bancadas externas não fornecem sinal para nenhuma tomada de decisão algorítmica <!-- fonte: docs/PLANO_PESQUISA.md -->;
3. **Registro Fiel de Resultados Negativos:** Intervenções que não superam os critérios pré-estabelecidos são formalmente arquivadas como resultados NÃO GO em `experimentos/NAO_FUNCIONOU.md`, documentando o aprendizado sem relaxamento retroativo de margens <!-- fonte: experimentos/NAO_FUNCIONOU.md -->;
4. **Preservação de Conteúdo e Âncora:** Nenhuma técnica pode alterar o vocabulário ou omitir palavras da camada digital. Todos os relatórios devem reproduzir, antes de qualquer computação, a âncora exata da regra de colunas no conjunto de ajuste <!-- fonte: docs/PLANO_PESQUISA.md -->.

### 1.2 Âncora Metodológica de Reprodutibilidade
Para atestar a integridade do ambiente computacional, das tabelas de coordenadas e das rotinas oficiais de métricas, instituiu-se uma âncora de controle estrito: a execução do algoritmo determinístico de regra de colunas sobre o conjunto `golden_v4`. Qualquer discrepância numérica interrompe imediatamente a cadeia de execução. Em todos os relatórios desta fase, a âncora foi reproduzida com precisão:
- Correlação de postos de Kendall sobre palavras: $\tau = 0,985948$ <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->;
- Descontinuidade de leitura: $6,045455$ <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> quebras por página.

### 1.3 Estrutura e Papel das Bancadas de Avaliação
O desenho experimental particiona os dados em três camadas de isolamento metodológico:

```
+-------------------------------------------------------------------------------+
|                             CONJUNTO DE AJUSTE                                |
|  - golden_v4 (44 págs, 27 veículos, anotação humana)                          |
|  - validacao_silver (15 págs, 1 veículo RN, referência automática)            |
|  --> Seleção e congelamento de hiperparâmetros, pesos e limiares              |
+---------------------------------------+---------------------------------------+
                                        | (Modelos e parâmetros congelados)
                                        v
+-------------------------------------------------------------------------------+
|                       BANCADAS DE DESENVOLVIMENTO EXTERNO                     |
|  - golden_v3_novo (27 págs, 10 veículos, anotação humana; consultado antes)   |
|  - teste_silver (89 págs, 3 veículos CE/MA/RJ, referência automática)         |
|  --> Avaliação de generalização e robustez (sem ajuste retroativo)            |
+---------------------------------------+---------------------------------------+
                                        | (Apenas o modelo finalista)
                                        v
+-------------------------------------------------------------------------------+
|                            TESTE CEGO CONFIRMATÓRIO                           |
|  - E001 (90 págs, 15 PDFs CE, 15 PDFs MA, 16 PDFs RJ; sobreposição zero)     |
|  - Lacre: experimentos/TESTE_CEGO.lock (imutável, 0 acessos prévios)          |
|  --> Avaliação confirmatória única, no encerramento do estudo                 |
+-------------------------------------------------------------------------------+
```

O conjunto de ajuste reúne 44 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> páginas do `golden_v4` distribuídas em 27 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> veículos distintos, somadas a 15 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> páginas da validação silver do Rio Grande do Norte (`validacao_silver`), totalizando 59 <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> páginas de calibração. A inclusão da validação silver de RN assegura representatividade de páginas densas e de veículos externos aos anotadores humanos primários.

As bancadas de desenvolvimento externo reúnem o `golden_v3_novo`, com 27 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> páginas humanas em 10 <!-- fonte: resultados/e006_residual/RELATORIO.md --> veículos, e o `teste_silver`, composto por 89 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> páginas de 3 <!-- fonte: resultados/e006_residual/RELATORIO.md --> veículos (Ceará, Maranhão e Rio de Janeiro). Como o `golden_v3_novo` havia sido consultado em rodadas do ciclo de desenvolvimento de outubro, ele não pode ser categorizado como um teste estritamente cego, funcionando como um conjunto externo de monitoramento <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->.

Por fim, o teste confirmatório definitivo foi formalizado no experimento E001 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->. Foram sorteadas 90 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> páginas de PDFs absolutamente nunca tocados por nenhum experimento ou partição prévia do repositório, com distribuição uniforme de 30 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> páginas para o Ceará (15 PDFs <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->), 30 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> para o Maranhão (15 PDFs <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->) e 30 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> para o Rio de Janeiro (16 PDFs <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->). A conferência algorítmica comprovou sobreposição zero <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> contra os 1.085 <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md --> PDFs previamente catalogados no repositório. Esse lote teve seus hashes criptográficos SHA-256 e sementes de sorteio selados no arquivo `experimentos/TESTE_CEGO.lock` <!-- fonte: experimentos/cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md -->, sendo rigorosamente proibida a abertura, inspeção ou avaliação dessas tarefas até a execução confirmatória final do estudo <!-- fonte: docs/PLANO_PESQUISA.md -->.

### 1.4 Régua de Avaliação e Inferência Estatística
A avaliação ponta a ponta apoia-se em rotinas congeladas que operam sobre palavras individuais após a reconstrução geométrica das unidades ordenadas:
- **Desfecho Primário de Continuidade Local (Quebras/Página):** Contagem de pares consecutivos de palavras cuja adjacência na ordem predita viola a ordem de leitura humana. O cálculo decompõe quebras ocorridas no interior das unidades atômicas (*piso interno*) e quebras verificadas na fronteira entre unidades sucessivas (*entre unidades*) <!-- fonte: resultados/e009_representacao/RELATORIO.md -->;
- **Controle Normalizado (Quebras/1.000 palavras):** Densidade de quebras ponderada pela extensão textual da página, eliminando distorções de volume <!-- fonte: resultados/e004_grafo/RELATORIO.md -->;
- **Desfecho Secundário de Macro-Ordem Global ($\tau$ de Kendall):** Coeficiente de correlação de postos relativo ao par de palavras, medindo a fidelidade da sequência global da página <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->;
- **Diagnósticos de Transição:** Acurácia do sucessor imediato entre linhas físicas intactas e fidelidade de blocos contíguos de 12 palavras (*Fid12*) <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->;
- **Controle de Cobertura Textual:** Exigência de preservação de 100% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> das palavras digitais extraídas, impedindo que métodos reduzam quebras por exclusão de elementos de difícil ordenação.

A incerteza amostral é reportada por intervalos de confiança de 95% (IC 95%) derivados de 5.000 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> reamostragens por *bootstrap* agrupado por veículo, complementados pelo teste de postos sinalizados de Wilcoxon com correção de continuidade de Pratt aplicado sobre os deltas médios por veículo <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->.

---

## 2. Limites Alcançáveis da Ordenação: A Análise de Oráculos

Antes de despender recursos no treinamento de modelos estatísticos ou neurais, investigaram-se os limites teóricos superiores alcançáveis pelas distintas famílias de intervenção. Esse diagnóstico foi conduzido através de formulações oraculares nos experimentos E002 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> e E016 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.

### 2.1 Tetos Teóricos do Grafo, Busca Residual e Roteamento (E002)
O experimento E002 avaliou três formulações de teto ótimo: (a) o espaço de candidatos de sucessão sob oráculos de escore perfeito; (b) a busca residual puramente local; e (c) o roteamento perfeito entre os métodos pré-existentes.

```
+---------------------------------------------------------------------------------------+
|                 ESPAÇO DE BUSCA E TETOS TEÓRICOS DE QUEBRAS (E002)                   |
|                                                                                       |
|   Regra de Colunas (Controle):        [========== 6,05 quebras/pág ==========]        |
|   Híbrido por Densidade (Baseline):   [======== 5,14 quebras/pág ========]            |
|   Teto Roteamento por Página:         [====== 3,59 quebras/pág ======]                |
|   Teto Residual Local:                [=== 1,91 quebras/pág ===]                      |
|   Teto Grafo de Arestas (Matching):   [= 1,05 =]                                      |
+---------------------------------------------------------------------------------------+
```

A análise de cobertura (*recall*) dos candidatos gerados a partir da regra e complementados por proximidade euclidiana revelou que o gargalo do problema não reside na geração de candidatos, mas na sua pontuação:

Tabela 1: Cobertura (*recall*) acumulada do gerador de candidatos por classe de transição no `golden_v4`.
| Classe de Transição | $K=12$ | $K=24$ | $K=32$ | Erros da Regra Alcançáveis ($K=32$) |
|---|---:|---:|---:|---:|
| Continuação na mesma coluna | 99,87% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 99,97% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 99,97% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 97,92% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| Entrada/saída de tabela ou imagem | 98,31% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 100,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 100,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 100,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| Salto de elemento transversal | 76,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 76,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 76,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 72,22% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| Cabeçalho, rodapé ou margem | 85,78% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 89,71% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 91,67% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 86,72% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| Fim de coluna $\to$ topo da próxima | 69,23% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 69,23% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 69,23% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 0,00% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| Outras transições | 95,54% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 97,32% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 98,21% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 92,86% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |

A decomposição evidenciou duas propriedades capitais: (1) a continuação vertical simples exibe cobertura virtualmente perfeita ($99,97\%$ <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> com $K=32$); e (2) transições de transposição de coluna ("fim de coluna $\to$ topo da próxima") apresentaram cobertura deficiente de apenas 69,23% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> (com $0,00\%$ <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> de recuperação dos erros da regra). Essa constatação exigiu que os modelos subsequentes incorporassem candidatos adicionais específicos de topo de coluna.

Ao alimentar algoritmos de decodificação global com escores perfeitos das arestas verdadeiras, obtiveram-se os limites fundamentais de redução de erro:

Tabela 2: Desempenho oracular comparativo das famílias de ordenação (E002).
| Bancada | Regra de Colunas | Híbrido 67 | Teto Grafo ($K=32$) | Teto Residual Local | Teto Roteamento |
|---|---:|---:|---:|---:|---:|
| `golden_v4` (quebras/pág) | 6,045 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 5,136 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 1,045 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 1,909 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 3,591 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> |
| `golden_v4` ($\tau$) | 0,9859 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 0,9797 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 0,9168 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 0,9897 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | 0,9935 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> |
| `golden_v3_novo` (quebras) | 9,222 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 7,889 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 1,259 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 2,222 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 6,000 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> |
| `teste_silver` (quebras) | 27,449 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 26,427 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 19,787 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 19,966 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 21,224 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> |
| `validacao_silver` RN (quebras) | 16,667 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | — <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 6,333 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | 6,333 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> | — <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> |

O oráculo de decodificação por emparelhamento (*matching*) sobre $K=32$ candidatos produziu uma redução média de 67,51% <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> das quebras no conjunto de ajuste (`golden_v4` + RN), superando amplamente o limiar pré-estabelecido de 20% e concedendo o veredito de **GO** para a formulação de grafos relacionais (E004) <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md -->.

Entretanto, o E002 desvelou um alerta metodológico crítico: a otimização estritamente local de arestas pelo *matching* perfeito derrubou o coeficiente $\tau$ para 0,9168 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> no `golden_v4` e 0,943 <!-- fonte: experimentos/REGISTRO.md --> no `golden_v3_novo`. Ao selecionar arestas com base unicamente na contiguidade imediata, o algoritmo montou caminhos desconexos que foram costurados em ordem arbitrária, degradando a correlação global. Em contrapartida, o oráculo residual, restrito a operações locais de baixo risco (trocas vizinhas e reinserções), reduziu as quebras para 1,909 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> preservando $\tau = 0,9897$ <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->.

### 2.2 O Limite da Decomposição Estrutural: Oráculo Hierárquico (E016)
Para investigar se a restrição da busca a macro-segmentos resolveria o dilema entre ordem local e global, o experimento E016 avaliou um oráculo hierárquico em dois níveis: linhas ordenadas no interior de blocos estruturais seguros, com os blocos subsequentemente ordenados em nível de página <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.

A partição geométrica automática gerou uma média de 7,5 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> segmentos por página no `golden_v4`. O gabarito humano comprovou que 94,3% <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> de todas as transições de leitura ocorrem inteiramente dentro desses segmentos, confirmando sua coesão estrutural. Contudo, em 35 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> dos 332 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> segmentos formados, a ordem humana cruzava as fronteiras dos blocos, impondo um custo incontornável à formulação particionada.

Os tetos alcançados no `golden_v4` decompuseram com exatidão a origem do erro:
- Oráculo hierárquico ótimo ($\tau$ máximo): 2,795 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras/página e $\tau = 0,9935$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->;
- Ordem interna perfeita com segmentos ordenados pela regra simples: 3,250 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras/página e $\tau = 0,9874$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->;
- Ordem interna gerada pelo grafo do E004 com segmentos ordenados pelo gabarito perfeito: 4,250 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras/página e $\tau = 0,9916$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->;
- Algoritmo prático HIER-1 (grafo no interior, regra entre segmentos): 4,659 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras/página e $\tau = 0,9854$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.

Esse diagnóstico oracular comprovou que a maior parcela do erro remanescente decorre da inferência local de sucessão dentro dos segmentos (que eleva as quebras a 4,250 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> mesmo sob macro-ordem perfeita), enquanto ordenar segmentos perfeitos via regra simples atinge 3,250 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras.

---

## 3. Exploração dos Sinais de Ordenação

Investigou-se a contribuição de três modalidades distintas de sinais computacionais para guiar a ordenação de linhas: atributos geométricos aprendidos via modelos de *gradient boosting*, continuidade semântica obtida por modelos causais de linguagem e meta-classificadores de roteamento em nível de página.

### 3.1 Geometria e Relações Estruturais Aprendidas (E004)
O experimento E004 treinou um classificador de arestas LightGBM utilizando 3.140 <!-- fonte: resultados/e004_grafo/RELATORIO.md --> páginas do conjunto silver de treino (`treino_noite.json`), compreendendo 436.454 <!-- fonte: resultados/e004_grafo/RELATORIO.md --> transições positivas e um pool de negativos difíceis balanceados, limitados a 4.000.000 <!-- fonte: resultados/e004_grafo/RELATORIO.md --> de pares com calibração empírica de probabilidades de Platt <!-- fonte: resultados/e004_grafo/RELATORIO.md -->.

A análise de importância de atributos (*gain*) no treinamento revelou a hierarquia de relevância dos sinais:
- `sucessor_regra`: gain de 14.252.259,971 <!-- fonte: resultados/e004_grafo/RELATORIO.md -->;
- `primeira_abaixo`: gain de 953.149,393 <!-- fonte: resultados/e004_grafo/RELATORIO.md -->;
- `dist_h`: gain de 470.922,060 <!-- fonte: resultados/e004_grafo/RELATORIO.md -->;
- `gap_y_h`: gain de 348.541,003 <!-- fonte: resultados/e004_grafo/RELATORIO.md -->;
- `dy_pagina`: gain de 299.929,453 <!-- fonte: resultados/e004_grafo/RELATORIO.md -->.

O atributo derivado do predecessor geométrico determinístico (`sucessor_regra`) dominou o aprendizado por uma ordem de magnitude, evidenciando que o modelo neural atua fundamentalmente como um corretor fino das decisões da regra geométrica clássica.

A decodificação global congelada no ajuste (`grafo_K24_maxregret_t0.00`) proporcionou ganhos expressivos na redução de quebras frente à regra de colunas e ao baseline híbrido 67:
- No `golden_v4`: redução para 3,614 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> quebras/página (contra 6,045 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> da regra e 5,136 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> do híbrido; $\Delta = -1,52$ [IC 95%: $-3,50$; $-0,07$] <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> vs híbrido);
- No `golden_v3_novo`: 6,519 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> quebras/página (contra 9,222 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> da regra e 7,889 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> do híbrido; $\Delta = -1,37$ [IC 95%: $-2,56$; $+0,23$] <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> vs híbrido);
- No `teste_silver`: 24,146 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> quebras/página (contra 27,449 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> da regra e 26,427 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> do híbrido; $\Delta = -2,28$ [IC 95%: $-11,31$; $-0,34$] <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> vs híbrido).

O modelo de arestas tornou-se o primeiro algoritmo do projeto a superar o híbrido 67 em quebras de leitura em todas as bancadas externas avaliadas. Não obstante, o critério pré-registrado de tolerância de correlação ($\Delta\tau \ge -0,005$ vs regra) falhou de forma contundente: no `golden_v3_novo`, o $\tau$ decaiu de 0,960 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> para 0,942 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> ($\Delta = -0,017$ <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md -->), replicando-se no `teste_silver` (0,960 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md --> para 0,943 <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md -->). O veredito do cartão foi rigorosamente registrado como **NÃO GO** <!-- fonte: experimentos/cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md -->.

### 3.2 Continuidade Linguística via Modelos Causais de Linguagem (E003)
A hipótese H3 postulava que a modelagem probabilística da transição textual entre linhas resolveria ambiguidades de leiaute em quebras de coluna e hifenização <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md -->. Para testá-la, o experimento E003 pontuou 87.120 <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> pares candidatos através do modelo causal Qwen3-8B em precisão bfloat16 executado na infraestrutura de cluster DGX Spark (jobs 1053, 1115 e 1137 <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md -->), totalizando 4.891,9 <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> segundos de computação com pico de memória reservada de 30.820 <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> MiB.

Avaliaram-se duas formulações teóricas ao longo de uma grade de 12 <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> configurações de decodificação:
1. **Ablação Condicional Simples ($\log P(t_j \mid t_i)$):** Avaliação pura da probabilidade do texto da linha $t_j$ dado o contexto de 48 palavras anteriores. Todas as 12 configurações no ajuste degradaram o desempenho, aumentando as quebras de leitura em um intervalo catastrófico de $\Delta = +12,2$ a $+95,9$ <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md --> quebras por página;
2. **Escore Contrastivo Ponto a Ponto:** Normalização pela probabilidade marginal independente da linha de destino:
$$\text{Escore}(t_i \to t_j) = \frac{\log P(t_j \mid t_i) - \log P(t_j \mid \text{BOS})}{|t_j|}$$
A formulação contrastiva objetivava penalizar destinos frequentes ou triviais. Contudo, os resultados obtidos demonstraram piora ainda mais acentuada: os acréscimos de quebra no ajuste oscilaram entre $\Delta = +17,7$ e $+86,0$ <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md --> quebras por página (a melhor variante contrastiva gerou $\Delta = +17,7$ <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md --> contra $+12,2$ <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md --> da ablação condicional).

Em obediência ao protocolo congelado, que estipulava que a ausência de ganho no ajuste congelaria a regra original, a seleção automática registrou `{"seletiva": "regra", "global": "regra"}` <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md -->, barrando a aplicação dos escores do modelo causal nas bancadas externas. A razão fundamental dessa falha reside na magnitude dos pesos de ponderação empregados ($0,5$ a $2,0$): ao competir diretamente com os custos geométricos de coluna na função de decodificação, o sinal linguístico induziu saltos de leitura entre colunas paralelas sempre que uma sentença encontrava plausibilidade semântica na coluna adjacente, destruindo a macro-estrutura do documento.

### 3.3 Seleção Automática de Método em Nível de Página (E005)
Diante da heterogeneidade de leiautes do acervo, o experimento E005 testou a hipótese de que meta-classificadores supervisionados (árvore rasa, regressão logística e LightGBM) superariam a heurística univariada congelada do baseline híbrido 67 (que aciona o LayoutReader para páginas com até 67 unidades e a regra para páginas mais densas) <!-- fonte: experimentos/cards/E005_seletor_de_m_todo_por_p_gina_regra_x_lay.md -->.

O protocolo executou uma validação cruzada agrupada do tipo *Leave-One-Vehicle-Out* (LOVO), totalizando 160 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> observações em 27 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> veículos territoriais distintos, roteando entre regra de colunas, LayoutReader e o grafo do E004:

Tabela 3: Desempenho dos seletores de método por página em validação cruzada LOVO (E005).
| Seletor / Método | Quebras/página | $\Delta$ Quebras vs Híbrido 67 | IC 95% do $\Delta$ por Veículo | $p$-valor Wilcoxon | Veredito |
|---|---:|---:|---:|---:|---|
| Híbrido 67 (Controle Congelado) | 17,444 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 0,000 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | [0,000; 0,000] <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 1,0000 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | Referência |
| Árvore Rasa | 21,225 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | +3,781 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | [$-3,280$; $+20,473$] <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 0,3373 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | NÃO GO |
| LightGBM Multivariado | 22,500 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | +5,056 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | [$-1,057$; $+20,923$] <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 0,8926 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | NÃO GO |
| Regressão Logística | 15,156 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | -2,288 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | [$-4,962$; $+1,635$] <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 0,0996 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | NÃO GO |
| Oráculo de Roteamento (Teto) | 13,138 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | -4,306 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | [$-6,223$; $-1,875$] <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | 0,0000 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | Teto Teórico |

Embora a regressão logística tenha obtido redução pontual de 2,288 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> quebras na média agregada, seu intervalo de confiança por veículo cruzou zero amplamente ($-4,962$ a $+1,635$ <!-- fonte: resultados/e005_seletor/RELATORIO.md -->), sofrendo degradação de $+0,841$ <!-- fonte: resultados/e005_seletor/RELATORIO.md --> quebras por página no `golden_v4`. Os demais modelos superajustaram severamente às amostras de treino de cada fold. O critério pré-registrado de superioridade não foi atendido por nenhum classificador multivariado, consagrando a superioridade e robustez da regra simples baseada na densidade física de linhas (limiar 67) <!-- fonte: experimentos/cards/E005_seletor_de_m_todo_por_p_gina_regra_x_lay.md -->.

---

## 4. A Tensão Conceitual entre Continuidade Local e Ordem Global

A investigação dos métodos aprendidos colocou em evidência o fenômeno central da fase de novembro: **a dissociação entre a eficácia de contiguidade local (medida por quebras e sucessor) e a preservação da macro-ordem topológica da página (medida por $\tau$)**.

```
+-------------------------------------------------------------------------------+
|                       O DILEMA DE ORDENAÇÃO LOCAL vs GLOBAL                   |
|                                                                               |
|   MODELOS DE GRAFO / RESIDUAL (E004, E006, E015):                             |
|   - Acerto de ligações imediatas:       Quebras caem significativamente       |
|   - Fragilidade de macro-sequência:     Inversões de blocos e colunas         |
|   - Consequência métrica:               Queda severa de tau de palavras       |
|                                                                               |
|   DECOMPOSIÇÃO ALGÉBRICA (diagnostico_tau_v3):                                |
|   - Inversão de dois trechos contíguos de tamanho N1 e N2 gera penalização    |
|     proporcional a N1 * N2 pares de palavras invertidas.                      |
|   - Exemplo Tocantins p10 (E004): 2 colunas invertidas geram Delta tau = -0,94|
|     com redução líquida de quebras locais (Delta quebras = -1).               |
+-------------------------------------------------------------------------------+
```

### 4.1 A Hipótese da Costura de Cadeias (E014 e E015)
Diante da degradação de $\tau$ no grafo do E004, formulou-se a hipótese de que o modelo classificava com perfeição os sucessores internos de pequenos blocos de texto (cadeias), mas errava ao conectá-las na sequência global da página <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md -->.

No experimento E014, o diagnóstico comprovou que o $\tau$ interno às cadeias permaneceu praticamente intacto, com a perda decorrendo inteiramente da costura inter-cadeias ($\Delta\tau = -0,048$ <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md --> no `golden_v4`). Testaram-se quatro heurísticas de ordenação das cadeias resultantes do grafo: (a) primeira linha; (b) mediana da posição da regra; (c) corretor local restrito à coluna; e (d) corretor local com tratamento de margens <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md -->.

A variante de ordenação de cadeias pela **mediana da regra** obteve sucesso notável no `golden_v4`: alcançou 3,568 <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md --> quebras/página com recuperação total da correlação ($\tau = 0,9867$ <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md -->, superior aos 0,9859 <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md --> da regra e aos 0,9797 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> do híbrido). Contudo, na validação RN, a variante sofreu uma queda abrupta para $\tau = 0,8910$ <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md -->, violando o critério formal de seleção do ajuste e determinando o abandono do E014 <!-- fonte: experimentos/cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md -->.

Para avaliar se a falha no RN constituía um caso isolado e se a mediana generalizava para documentos externos, o experimento E015 estabeleceu um protocolo confirmatório prévio com mecanismo de salvaguarda <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->. Ao avaliar as bancadas externas, o E015 revelou:
- No `golden_v3_novo`: as quebras reduziram para 6,519 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> (contra 7,889 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> do híbrido; $\Delta = -1,370$ <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->), mas o $\tau$ decaiu para 0,9417 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> (contra 0,9596 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> da regra; $\Delta = -0,0178$ <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->);
- No `teste_silver`: as quebras caíram para 24,146 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> (contra 26,427 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> do híbrido; $\Delta = -2,281$ [IC 95%: $-11,385$; $-0,368$] <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->), mantendo $\tau = 0,9551$ <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> (dentro da margem de $-0,005$).

Como o critério 2 exigia $\tau \ge \tau_{\text{regra}} - 0,005$ em ambas as bancadas externas, a persistência da perda no `golden_v3_novo` sacramentou o veredito de **NÃO GO** do E015 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->.

### 4.2 A Busca Residual Local com Função de Ganho (E006)
Buscando blindar o método contra perturbações topológicas de grande amplitude, o experimento E006 restringiu as ações algorítmicas a uma busca local gulosa a partir da sequência inicial fornecida pelo híbrido 67 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->. As operações permitidas limitaram-se a trocas vizinhas, deslocamento intra-coluna de blocos curtos (1 a 4 linhas) e reinserções de cabeçalhos e rodapés, aceitas apenas quando o incremento de log-verossimilhança das arestas pelo modelo do E004 superava um limiar $\lambda$ <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->.

A varredura de calibração no ajuste congelou $\lambda = 2,0$ <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> e um máximo de $M = 20$ <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> operações por página. O método demonstrou ganhos expressivos na redução de quebras em todas as bancadas:
- `golden_v4`: reduziu para 4,432 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> quebras/página ($\tau = 0,978$ <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->), superando o híbrido 67 (5,136 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->) e a reordenação restrita (5,182 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->);
- `golden_v3_novo`: reduziu para 7,074 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> quebras/página (contra 7,889 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> do híbrido e 7,778 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> da reordenação restrita);
- `teste_silver`: reduziu para 24,888 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> quebras/página (contra 26,427 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> do híbrido e 26,449 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> da reordenação).

Não obstante a eficácia na eliminação de quebras, o E006 violou dois critérios pré-estabelecidos eliminatórios:
1. **Degradação de $\tau$ no `golden_v3_novo`:** O índice decaiu para 0,939 <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> ($\Delta = -0,020$ <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md --> vs híbrido), ultrapassando a margem máxima de 0,005;
2. **Taxa de Regressões Excessiva:** No `golden_v3_novo`, o método efetuou 30 <!-- fonte: resultados/e006_residual/RELATORIO.md --> reparos de sucessores-ouro ao custo de 11 <!-- fonte: resultados/e006_residual/RELATORIO.md --> regressões. A proporção de $11/30 = 36,7\%$ violou o teto tolerado de um terço ($33,3\%$) estabelecido no critério 4 do cartão, resultando em veredito de **NÃO GO** <!-- fonte: experimentos/cards/E006_correcao_residual_local_guiada_pelo_mode.md -->.

### 4.3 Diagnóstico Algébrico da Perda de $\tau$ (`diagnostico_tau_v3`)
Para desvendar a causalidade matemática por trás da persistente perda de $\tau$ no `golden_v3_novo`, executou-se uma decomposição analítica exata das inversões de palavras sobre 175 <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md --> páginas processadas <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->.

A formulação matemática demonstra que, quando duas unidades $u$ e $v$ contendo $|u|$ e $|v|$ palavras trocam de ordem relativa, o impacto no $\tau$ é dado por:
$$\Delta\tau = \frac{-2 \cdot (|u| \cdot |v| - 2c)}{\binom{N_{\text{ouro}}}{2}}$$
onde $c$ representa o número de pares originalmente concordantes. Quando dois blocos extensos de texto correto são invertidos entre si, a penalização no $\tau$ escala quadraticamente com o produto de seus tamanhos, mesmo que internamente ambos os blocos possuam continuidade perfeita e nenhuma quebra de leitura adicional seja computada <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->.

O diagnóstico revelou os seguintes achados fundamentais:
- **A Contraprova dos Átomos Gigantes:** No caso isolado da página `official_diary_rn/...#p40`, duas tabelas monolíticas contendo cerca de 1.740 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> palavras cada (representando aproximadamente 50% <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> da página cada) foram permutadas pelo modelo de grafo. Essa inversão única derrubou o $\tau$ da página para 0,013 <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md --> sem gerar nenhuma quebra adicional <!-- fonte: experimentos/cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md -->. Contudo, no `golden_v3_novo`, unidades com mais de 20% das palavras explicaram exatamente **0,00%** <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md --> da perda de $\tau$, refutando a hipótese de que distorções no $v3$ decorressem de tabelas volumosas;
- **Hiper-Concentração do Erro em Poucas Páginas:** A quase totalidade da degradação de $\tau$ concentra-se em pouquíssimas páginas atípicas. No `golden_v4`, duas páginas do Tocantins (`official_diary_to/...#p10` e `#p47`) responderam sozinhas por 80,52% <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md --> de toda a perda bruta de $\tau$ frente à regra. Na página `#p10`, o modelo de grafo inverteu as duas colunas inteiras de texto, resultando em $\Delta\tau = -0,940247$ <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md --> com redução de uma quebra de leitura ($\Delta = -1$ <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->) <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->;
- **Páginas Críticas no `golden_v3_novo`:** No conjunto externo, a perda bruta do grafo e da mediana é dominada por edições densas de três colunas do Rio de Janeiro: as páginas `official_diary_rj/...Boletim_7197.pdf#p44` e `...Poder Legislativo...#p3` acumulam mais de 90% <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md --> da perda bruta, em decorrência de permutações macroscópicas entre colunas <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->.

Essa constatação evidenciou que os modelos de arestas e grafos locais são estruturalmente cegos à macro-organização dos diários oficiais, exigindo restrições geométricas rígidas de nível superior.

### 4.4 Decodificação Hierárquica e o Erro de Calibração do Portão (E016)
Como resposta direta ao diagnóstico de $\tau$ e à consulta técnica ao orientador <!-- fonte: experimentos/consultas/2026-11-03_chatgpt_03_resposta.md -->, implementou-se no experimento E016 a abordagem de decodificação hierárquica em dois níveis <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.

O método HIER-1 ordenou as linhas internas de cada segmento geométrico através do modelo de grafo E004 e, subsequentemente, ordenou os segmentos na página via regra de colunas <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->. Os resultados no `golden_v4` consagraram o HIER-1 como o primeiro algoritmo da pesquisa a obter, simultaneamente, redução nas quebras de leitura e preservação estrita do coeficiente $\tau$:
- Quebras por página: 4,659 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> (superando o híbrido 67, com 5,136 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->, e a regra de colunas, com 6,045 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->);
- Correlação de postos: $\tau = 0,9854$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> (superando o híbrido 67, com 0,9797 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->, e virtualmente empatado com a regra, 0,9859 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->).

Apesar do êxito descritivo do HIER-1, o experimento foi registrado como **NÃO GO da Fase 1** em decorrência de um erro de calibração formalmente registrado no cartão do experimento <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->:
> *"Erro meu no desenho do portão: comparei o oráculo hierárquico com o teto plano (1,05), que ignora qualquer restrição; restringir a ordem a segmentos custa quebras por construção (o ouro 'viola' 35 segmentos). O limiar de 30% era apertado demais. Fica registrado; o veredito não muda."* <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->

O critério pré-registrado exigia que o oráculo hierárquico atingisse quebras no máximo 30% superiores ao teto plano do grafo ($1,045 \times 1,30 = 1,359$ quebras). Contudo, a própria imposição de fronteiras de segmentos impede fisicamente a resolução das 35 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> transições humanas que atravessam os blocos, estabelecendo um piso analítico de 2,795 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> quebras. O portão revelou-se matematicamente inatingível por concepção. Em cumprimento à integridade metodológica estrita do projeto, o veredito NÃO GO foi rigorosamente mantido, impedindo o teste confirmatório do HIER-1 nas bancadas externas sem pré-registro de um novo cartão <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.

---

## 5. Granularidade: Caixas de Parágrafo versus Linhas Atômicas (E009)

Um dos pilares conceituais do projeto consistia na premissa de que a substituição de caixas envolventes de parágrafo por linhas atômicas constituía, por si só, uma solução superior para o problema da ordem de leitura, ancorada na redução histórica de 213 para 29 quebras internas documentada nas fases preliminares <!-- fonte: experimentos/NAO_FUNCIONOU.md -->. O experimento E009 submeteu essa premissa a teste formal com pareamento estrito de documentos, ordenadores idênticos e controle de 100% <!-- fonte: resultados/e009_representacao/RELATORIO.md --> da cobertura digital de palavras <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->.

Tabela 4: Comparação de granularidade sob cobertura controlada: Caixas Automáticas (A) vs Linhas Atômicas (B) no experimento E009.
| Bancada / Ordenador | A (Caixas): Total | A (Caixas): Dentro | A (Caixas): Entre | B (Linhas): Total | B (Linhas): Dentro | B (Linhas): Entre | $\Delta$ (B $-$ A) Total [IC 95%] |
|---|---:|---:|---:|---:|---:|---:|---:|
| `golden_v4` / Regra | 5,477 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 1,591 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 3,886 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 6,045 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 0,545 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 5,500 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | +0,568 [$-2,93$; $+3,21$] <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> |
| `golden_v4` / Híbrido 67 | 4,750 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 1,591 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 3,159 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 5,136 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 0,545 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | 4,591 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> | +0,386 [$-3,29$; $+3,27$] <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> |
| `golden_v3_novo` / Regra | 11,000 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 5,30 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 5,70 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 9,22 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 0,26 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 8,96 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | -1,78 [$-3,64$; $+0,72$] <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> |
| `golden_v3_novo` / Híbrido 67 | 8,96 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 5,30 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 3,67 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 7,89 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 0,26 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | 7,63 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> | -1,07 [$-3,95$; $+1,77$] <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> |

A decomposição dos erros revelou um resultado metodológico seminal:
1. **Confirmação do Piso Interno:** A transição para linhas de fato reduz drasticamente os erros internos incorrigíveis às unidades (no `golden_v4`, cai de 1,591 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> para 0,545 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> quebras/página; no `golden_v3_novo`, desaba de 5,30 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> para 0,26 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->);
2. **Transferência Proporcional para as Fronteiras:** Ao fragmentar a página em linhas individuais, o número de unidades a ordenar multiplica-se expressivamente, elevando a complexidade combinatória do ordenador. Consequentemente, as quebras verificadas *entre unidades* aumentaram na exata proporção da redução interna (no `golden_v4` sob a regra, saltam de 3,886 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> para 5,500 <!-- fonte: resultados/e009_representacao/RELATORIO.md --> quebras/página; no `golden_v3_novo`, sobem de 5,70 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> para 8,96 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->);
3. **Equivalência Estatística no Cômputo Global:** Em termos de quebras totais por página, nenhuma das comparações atingiu o critério pré-registrado de superioridade estatística ($\Delta < 0$ com IC 95% estritamente negativo). No `golden_v4`, a representação em linhas apresentou ligeiro aumento nominal de quebras (+0,568 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> sob a regra e +0,386 <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md --> sob o híbrido), enquanto no `golden_v3_novo` a redução observada teve seus intervalos de confiança cruzando o zero <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->.

Conclusão metodológica do E009: **a adoção de linhas automáticas não resolve a ordem de leitura por virtude intrínseca de representação, mas desloca a carga de erro da segmentação física para o algoritmo de ordenação** <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->. Linhas eliminam a sobreposição destrutiva que corrompia as palavras dentro de caixas de parágrafo, mas exigem decodificadores relacionais capazes de gerenciar dezenas de transições inter-unidades na página.

---

## 6. Síntese dos Resultados e Implicações para o TCC

### 6.1 Tabela Sinóptica Consolidada da Fase de Novembro
A Tabela 5 consolida os principais métodos, controles, oráculos e baselines avaliados ao longo da fase de novembro de 2026 nas bancadas de ajuste e desenvolvimento externo.

Tabela 5: Consolidação sinóptica dos experimentos da Fase de Novembro de 2026.
| Método / Experimento | Família / Paradigma | `golden_v4` (Quebras / $\tau$) | `golden_v3_novo` (Quebras / $\tau$) | `teste_silver` (Quebras / $\tau$) | Veredito Oficial |
|---|---|---:|---:|---:|---|
| **Regra de Colunas** | Controle Determinístico (Âncora) | 6,045 <!-- fonte: experimentos/REGISTRO.md --> / 0,986 <!-- fonte: experimentos/REGISTRO.md --> | 9,222 <!-- fonte: experimentos/REGISTRO.md --> / 0,960 <!-- fonte: experimentos/REGISTRO.md --> | 27,449 <!-- fonte: experimentos/REGISTRO.md --> / 0,960 <!-- fonte: experimentos/REGISTRO.md --> | Controle |
| **LayoutReader Pronto** | Modelo Pré-Treinado (Seq2Seq) | 18,386 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> / 0,913 <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> | — | — | Baseline |
| **Regra com Reordenação Restrita** | Heurística Intra-Coluna | 5,182 <!-- fonte: resultados/e006_residual/RELATORIO.md --> / 0,986 <!-- fonte: resultados/e006_residual/RELATORIO.md --> | 7,778 <!-- fonte: resultados/e006_residual/RELATORIO.md --> / 0,960 <!-- fonte: resultados/e006_residual/RELATORIO.md --> | 26,449 <!-- fonte: resultados/e006_residual/RELATORIO.md --> / 0,960 <!-- fonte: resultados/e006_residual/RELATORIO.md --> | Baseline |
| **Híbrido por Densidade (Limiar 67)** | Heurística Univariada (Baseline Congelado) | 5,136 <!-- fonte: experimentos/REGISTRO.md --> / 0,980 <!-- fonte: experimentos/REGISTRO.md --> | 7,889 <!-- fonte: experimentos/REGISTRO.md --> / 0,959 <!-- fonte: experimentos/REGISTRO.md --> | 26,427 <!-- fonte: experimentos/REGISTRO.md --> / 0,959 <!-- fonte: experimentos/REGISTRO.md --> | **Baseline Congelado** |
| **E004 (Grafo LightGBM Max-Regret)** | Grafo Relacional Global | 3,614 <!-- fonte: experimentos/REGISTRO.md --> / 0,938 <!-- fonte: experimentos/REGISTRO.md --> | 6,519 <!-- fonte: experimentos/REGISTRO.md --> / 0,942 <!-- fonte: experimentos/REGISTRO.md --> | 24,146 <!-- fonte: experimentos/REGISTRO.md --> / 0,943 <!-- fonte: experimentos/REGISTRO.md --> | NÃO GO ($\tau$ degradado) |
| **E003 (LM Causal Contrastivo)** | Modelo Linguístico (Qwen3-8B) | Piora $+17,7$ quebras <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md --> | Não avaliado <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> | Não avaliado <!-- fonte: resultados/e003_lm/contrastivo_8b/AVALIACAO.md --> | NÃO GO (destrói ordem) |
| **E005 (Seletor Multivariado LOVO)** | Meta-Classificador de Página | 5,977 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> / 0,977 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | Perde do Híbrido 67 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | Perde do Híbrido 67 <!-- fonte: resultados/e005_seletor/RELATORIO.md --> | NÃO GO (sobreajuste) |
| **E006 (Correção Residual Local)** | Busca Local Guiada por Grafo | 4,432 <!-- fonte: experimentos/REGISTRO.md --> / 0,978 <!-- fonte: experimentos/REGISTRO.md --> | 7,074 <!-- fonte: experimentos/REGISTRO.md --> / 0,939 <!-- fonte: experimentos/REGISTRO.md --> | 24,888 <!-- fonte: experimentos/REGISTRO.md --> / 0,953 <!-- fonte: experimentos/REGISTRO.md --> | NÃO GO ($\tau$ e regressões) |
| **E014/E015 (Cadeias Mediana)** | Grafo com Ordenação por Mediana | 3,568 <!-- fonte: experimentos/REGISTRO.md --> / 0,987 <!-- fonte: experimentos/REGISTRO.md --> | 6,519 <!-- fonte: experimentos/REGISTRO.md --> / 0,942 <!-- fonte: experimentos/REGISTRO.md --> | 24,146 <!-- fonte: experimentos/REGISTRO.md --> / 0,955 <!-- fonte: experimentos/REGISTRO.md --> | NÃO GO ($\tau$ externo) |
| **E016 (HIER-1)** | Decodificação Hierárquica | 4,659 <!-- fonte: experimentos/REGISTRO.md --> / 0,985 <!-- fonte: experimentos/REGISTRO.md --> | Não avaliado <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> | Não avaliado <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md --> | NÃO GO (portão Fase 1) |
| **Teto Residual Local (E002)** | Oráculo Local Ótimo | 1,909 <!-- fonte: experimentos/REGISTRO.md --> / 0,990 <!-- fonte: experimentos/REGISTRO.md --> | 2,222 <!-- fonte: experimentos/REGISTRO.md --> / 0,962 <!-- fonte: experimentos/REGISTRO.md --> | 19,966 <!-- fonte: experimentos/REGISTRO.md --> / 0,960 <!-- fonte: experimentos/REGISTRO.md --> | Teto Teórico |
| **Teto Grafo Matching K32 (E002)** | Oráculo Global Ótimo | 1,045 <!-- fonte: experimentos/REGISTRO.md --> / 0,917 <!-- fonte: experimentos/REGISTRO.md --> | 1,259 <!-- fonte: experimentos/REGISTRO.md --> / 0,943 <!-- fonte: experimentos/REGISTRO.md --> | 19,787 <!-- fonte: experimentos/REGISTRO.md --> / 0,940 <!-- fonte: experimentos/REGISTRO.md --> | Teto Teórico |

### 6.2 O Híbrido 67 como Baseline Insuperado
O balanço empírico da fase de novembro estabelece que o **híbrido por densidade com limiar 67** (LayoutReader nas páginas com até 67 unidades, regra de colunas nas demais) permanece como a formulação prática mais robusta e eficaz do projeto <!-- fonte: experimentos/NAO_FUNCIONOU.md -->.

Ele entrega o melhor equilíbrio estatístico comprovado entre as três bancadas:
- No `golden_v4`: 5,136 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> quebras/página ($\Delta = -0,909$ [IC 95%: $-1,776$; $-0,095$] <!-- fonte: resultados/e002_oraculos/RELATORIO.md --> vs regra, $p = 0,0223$ <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->) com $\tau = 0,9797$ <!-- fonte: resultados/e002_oraculos/RELATORIO.md -->;
- No `golden_v3_novo`: 7,889 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> quebras/página ($\Delta = -1,333$ <!-- fonte: experimentos/NAO_FUNCIONOU.md --> vs regra) com $\tau = 0,959$ <!-- fonte: experimentos/REGISTRO.md -->;
- No `teste_silver`: 26,427 <!-- fonte: experimentos/cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md --> quebras/página ($\Delta = -1,022$ <!-- fonte: resultados/e006_residual/RELATORIO.md --> vs regra) com $\tau = 0,959$ <!-- fonte: experimentos/REGISTRO.md -->.

É o único algoritmo cujos intervalos de confiança por veículo situam-se inteiramente abaixo de zero em todas as bancadas de avaliação <!-- fonte: docs/PLANO_PESQUISA.md -->, sem incorrer nas falhas catastróficas de correlação global $\tau$ que desclassificaram os métodos aprendidos não-lineares.

### 6.3 O Valor Metodológico dos Resultados Não Go
A rigorosa documentação dos vereditos NÃO GO constitui uma contribuição científica de primeira ordem para a literatura de processamento de documentos oficiais e análise de leiaute:
1. **Modelos Neurais Causais Não Operam como Decodificadores Diretos:** A ineficácia do Qwen3-8B demonstrou que probabilidades de transição textual não substituem priors geométricos fortes em leiautes multicolunares, devendo ser incorporadas como atributos auxiliares de modelos relacionais, e não como árbitros aditivos de decodificação <!-- fonte: experimentos/cards/E003_lm_causal_contrastivo_nas_arestas.md -->;
2. **Grafos Planos Sofrem de Cegueira Topológica:** Modelos relacionais aprendidos (como LightGBM ou redes neurais de arestas) minimizam com sucesso os conflitos de contiguidade local imediata, mas geram permutações macroscópicas danosas quando desprovidos de restrições estruturais de ordem superior <!-- fonte: resultados/diagnostico_tau_v3/RELATORIO.md -->;
3. **Deslocamento de Erro entre Granularidades:** O experimento E009 desfez a premissa de que a segmentação em linhas resolve o problema da ordem, provando que ela apenas transfere os erros da física do recorte para a combinatória da sequência <!-- fonte: experimentos/cards/E009_representacao_para_inferencia_caixas_aut.md -->;
4. **Viabilidade Promissora da Decodificação Hierárquica:** A formulação HIER-1 do E016 demonstrou ser o caminho mais promissor para reconciliar quebras reduzidas (4,659 <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->) com alta fidelidade global ($\tau = 0,9854$ <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->). O equívoco conceitual na calibração inicial do portão de validação deixa as portas abertas para que, em fases subsequentes, essa arquitetura em dois níveis seja formalmente submetida à validação confirmatória única sobre o lote lacrado do teste cego (E001) <!-- fonte: experimentos/cards/E016_oraculo_e_decodificacao_hierarquica_linh.md -->.
