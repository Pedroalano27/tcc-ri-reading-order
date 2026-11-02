Você será o orientador técnico-científico de um TCC (Ciência da Computação, UFG) sobre ORDEM DE LEITURA em Diários Oficiais brasileiros (PDFs digitais multicoluna, 2 a 5 colunas, cabeçalhos/rodapés, títulos transversais, tabelas, marcas laterais). Preciso de um plano de experimentos priorizado para as próximas semanas, com hipóteses falsificáveis. Responda em português, direto, com decisões (não um survey).

ESTADO ATUAL (números medidos):
- Acervo: 4.644 PDFs (~310 mil páginas, 23 UFs + municípios), ~96% digitais (palavras com coordenadas, sem OCR). Divisão por VEÍCULO: treino 7 veículos, validação RN, teste CE/MA/RJ.
- Representação atual da página: LINHAS de texto (palavras agrupadas por linha) + átomos de tabela/imagem detectados por um YOLO (mAP50 0,83 em 3 classes). Antes usávamos caixas de parágrafo; trocamos porque as caixas erravam muito (erros internos de caixa: 213 -> 29 quebras no conjunto).
- Métrica principal: "quebras de leitura por página" (transições de palavra que não seguem a referência), tau de Kendall de palavras, acurácia de sucessor de linha.
- Bancadas: golden_v4 (44 páginas anotadas por humano; usada para desenvolver a regra), golden_v3_novo (27 páginas humanas, já consultadas antes), teste silver (89 páginas CE/MA/RJ; referência = fluxo de texto do PDF, ruidosa).
- Melhor método: REGRA de colunas por projeção local com política de margens (cabeçalho primeiro, rodapé por último): golden_v4 tau 0,986 / 6,05 quebras; v3 0,960 / 9,22; silver 0,960 / 27,45.
- LayoutLM "sucessor" (classifica o próximo elemento, só geometria, 3.140 páginas silver de treino): 0,924/9,00 | 0,928/10,41 | 0,934/29,15 (variância entre sementes ~0,3-0,5 quebras). Mais dado ajudou (873 -> 3.140 páginas). LayoutLM lendo o texto das linhas PIOROU (20,8 quebras). LayoutReader (word-level, ajustado): perde da regra. BiLSTM: perde.
- Diagnóstico: ~34-50% das quebras da regra estão em cabeçalho/rodapé/marcas laterais; ~20-40% em "continuação dentro da mesma coluna".
- Tentativas pós-regra: corretor de transições (MLP): sem ganho; margens por repetição entre páginas do mesmo PDF: ganho só no ajuste, não generaliza; regra+modelo seletivo: piora; reordenação restrita dentro da coluna (janelas 4-8 linhas, escore fixo): 6,05->5,18 | 9,22->7,78 | 27,45->26,45, IC por veículo inclui zero (promissora, inconclusiva).
- Em andamento: pontuação de arestas candidatas por LM causal (ideia do arXiv 2607.01018, path cover com max-regret) com Qwen3-8B em DGX Spark; candidatos têm recall 96-98% nas humanas e 94% no silver.
- Projeto parceiro (CEIA/Data Policy, mesmo domínio de diários): ~417 páginas (129 PDFs) com ordem anotada em Label Studio no nível de CAIXA (relações continue/skip_noise/new_doc/end); uso no TCC ainda não autorizado. Um pré-anotador deles (XY-cut + floresta de decisão) tem sucessor 0,815; com revisão de LLM (Opus) 0,918.
- Recursos: RTX 4050 6 GB local; Kaggle 2xT4; DGX Spark (GB10, até 80 GB por job, fila compartilhada, 1 job por usuário); Gemini API; agentes de código.
- Anotação humana é o gargalo (só o autor anota; ~45 páginas por rodada).

IDEIA DO AUTOR A AVALIAR: simplificar a anotação/segmentação: anotar só elementos estruturais complexos (tabelas, figuras, quadros, talvez cabeçalho/rodapé) e deixar o texto como linhas automáticas, resolvendo a classificação fina do texto depois. Hipótese: menos caixas -> menos erros de segmentação -> ordem melhor e anotação mais barata.

PERGUNTAS:
1. Que FAMÍLIAS de método devo testar para superar a regra, em ordem de prioridade e custo? Considere: aprendizado de relações par-a-par com decodificação global (grafo/TSP/path cover), GNN sobre linhas, transformer de ordenação (pointer network), LayoutLMv3/LayoutReader adaptados para linhas, correção residual sobre a regra, VLM (Qwen-VL etc.) reordenando a saída da regra, LM causal como sinal de continuidade. Para cada uma: por que pode funcionar AQUI, custo, e o critério de abandono.
2. Como desenhar o experimento da anotação simplificada para responder à hipótese de forma limpa (variáveis, controles, métrica, n de páginas)?
3. Como lidar com a falta de anotação humana: silver do PDF (ruidoso), pré-anotação + revisão, dados do parceiro, síntese? Quantas páginas humanas novas preciso, e como dividir (desenvolvimento vs teste cego intocado)?
4. Protocolo estatístico mínimo (IC por veículo, Wilcoxon, correção de múltiplas comparações?) e regra de parada para cada ideia.
5. Um cronograma de 4-6 semanas realista com marcos e o que vira capítulo do TCC.
