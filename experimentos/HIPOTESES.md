# Hipóteses da fase de novembro

Cada hipótese é falsificável e tem critério decidido **antes** dos experimentos. Os
critérios vêm da [consulta 01 ao ChatGPT](consultas/2026-11-02_chatgpt_01_resposta.md),
com ajustes do Claude. Valores em quebras de leitura por página.

| ID | Hipótese | Experimento | Sucesso | Abandono |
|---|---|---|---|---|
| H-central | Especializar o método por tipo de página + otimizar globalmente as relações entre linhas supera a regra e o híbrido 67 | todos | critério de superioridade no teste cego (≥ 10% sobre o macro de UFs, IC95 < 0, nenhum veículo pior > 0,5) | — |
| H0 | A maior parte dos erros da regra é corrigível com os candidatos e as operações permitidas | E002 | oráculo ≥ 20% abaixo da regra no desenvolvimento | oráculo < 20%: revisar candidatos/granularidade antes de treinar |
| H1 | Arestas aprendidas + decodificação global superam sucessores independentes e a regra | E004 | ≥ 10% menos quebras que a regra no desenvolvimento; ganho sobre o híbrido nas páginas densas | 2 configurações sem atingir |
| H2 | A maior parte do ganho residual vem de alterações locais de baixo risco | E006 | supera a reordenação restrita atual em v3 e v4, com erros introduzidos ≤ 1/3 dos removidos | não superar |
| H3 | A continuidade linguística (LM causal, escore contrastivo) discrimina sucessores quando a geometria não basta | E003 | ≥ 0,5 quebra/página sobre a variante só geométrica, mesmos candidatos e decodificador | < 0,5 |
| H4 | A imagem (VLM) resolve títulos transversais e margens que a geometria não resolve | E007 | corrige ≥ 25% dos erros nas regiões selecionadas sem piora fora delas | < 25% |
| H5 | O contexto de vizinhança (GNN) melhora o ranqueamento além das features manuais | E011 | ≥ 0,5 quebra ou ≥ 2 pp no sucessor difícil sobre o LightGBM | não atingir |
| H6 | Anotar sobre linhas automáticas é mais rápido | E008 | ≥ 25% menos tempo mediano (1ª sessão) | — |
| H7 | A anotação simplificada tem menos erros de segmentação | E008 | ≥ 30% menos erros de união/divisão | — |
| H8 | O pipeline simplificado não piora a ordem | E008/E009 | não inferior, com margem de 0,5 | — |
| H9 | Menos caixas não perde conteúdo | E008/E009 | cobertura de palavras igual (idealmente 100%) | — |
| H10 | Um seletor por página simples supera o limiar fixo de densidade | E005 | melhor que o limiar 67 em validação cruzada agrupada por veículo | não superar: manter o limiar 67 |
| H11 | Mais silver estratificado por confiança melhora os pontuadores de aresta | E010 | curva de aprendizado com ganho além da variância entre sementes | sem ganho de 3.140 para 10 mil páginas |
