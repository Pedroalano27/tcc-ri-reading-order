1. Âncora reproduzida: τ 0,985948; 6,045455 quebras/página no golden_v4.
2. Veredito do cartão E004: NÃO GO.
3. Selecionado grafo_K24_maxregret_t0.00; redução de 42,41% no ajuste v4/RN.
4. Execução completa; seleção preservada nas externas.
5. CPU, um processo, quatro threads; cobertura integral nas ordens efetivamente medidas.
6. Golden_v3_novo já foi consultado em rodadas anteriores; teste cego não aberto nem avaliado.

# E004 — grafo de arestas aprendidas

## Execução e protocolo

Este relatório e seu resumo são produzidos pelo script. Caches atômicos, fontes e hashes em `cache/manifesto.json`; o diretório de execução é `cache/1238a2d3214b898c7eeb91680518c308da0bea644aa60a8b6ee15b358ed7b7b8`. Nenhum resultado ausente é substituído por estimativa.

Régua importada: `corretor_de_transicoes.medir`, via `e002_oraculos.avaliar_ordem`, `bancada_ordenadores` e `erros_ponta_a_ponta`. τ de palavras, quebras por página/1.000 palavras-ouro (denominador da régua existente), fidelidade integral de 12 e sucessor de linhas intactas. Entrada por `ordem_entrada`, random.Random(f'entrada-{page_id}'). Átomos ls3 e expansão interna congelados; nenhuma palavra descartada.

Candidatos conservam os K destinos do E002 e FIM privado, adicionando os três primeiros itens das colunas à direita e dos trechos abaixo para fontes do último terço da coluna ou cuja regra sai da coluna. A condição pos≥0,65 e a escala 2,5 alturas são proxies geométricas existentes, fixadas antes da medição. Extras não consomem K. Uma matriz K32+extras treina o classificador; os K menores restringem o mesmo escore e mantêm o rank de candidato do grafo máximo.

Features: geometria normalizada pela página/altura, sobreposição, alinhamento esquerdo, primeira abaixo, colunas, posições e sucessor da regra, tipos automáticos, faixa topo/rodapé/marca, pontuação/hífen, maiúscula/minúscula, numeração, comprimentos e rank do candidato. Somente dados automáticos entram nas features. Recorrência só é usada se já vier como `repeticao_entre_paginas`; não são abertos PDFs vizinhos para calculá-la, pois poderiam conter páginas cegas.

Supervisão importa `alvos_silver`: apenas fontes/alvos cuja expansão é trecho contíguo verificável do fluxo PDF; as demais são contadas como exclusões, sem impor sucessor por mediana. Todos os demais candidatos são negativos; fontes cujo ouro está fora do grafo mantêm todos os negativos. FIM é positivo só no fim real. Não há pesos de confiança novos: o corpus não fornece três níveis supervisionados; confiança da regra é uma proxy, não certeza do silver.

Treino exclusivamente nos shards base+extra usados pelo exportador `treino_noite.json`, deduplicados e conferidos contra 3.140 IDs. Nunca usa RN nem páginas humanas/external/teste cego. Duas configurações (15/31 folhas; mínimo 100 exemplos/folha), checkpoints 40/80/120 árvores, learning rate 0,08, max_bin 31. Mantidos os três folds agrupados somente dentro do treino (máximo duas configurações × três folds). A logloss de seleção e a calibração Platt usam os candidatos OOF COMPLETOS, não amostrados, com peso igual por veículo. Assim a calibração corrige empiricamente a mudança de prevalência e de composição dos negativos, sem aplicar uma correção analítica uniforme que seria inadequada aos negativos difíceis preservados. Depois há refit amostrado nas 3.140 páginas. A transferência dessa calibração ao refit é uma aproximação explicitada, sem recalibrar no ouro humano/RN.

Decisão de método autorizada nesta retomada: amostragem exclusivamente no treino, preservando todos os positivos e negativos com a feature rank_candidato ≤ 4 (rank baseado em zero, portanto cinco posições). Os demais negativos são sorteados uniformemente sem reposição, semente 7, até o limite global de quatro milhões de pares. A escolha não depende de resultados de ajuste ou externos. Matrizes originais e caches de features são preservados; novas matrizes amostradas em memmap por veículo. Avaliação e candidatos de inferência permanecem completos.

Memória: free_raw_data=True, um Dataset construído implicitamente por chamada de treino/fold e liberado antes da avaliação; leituras em lotes fecham os mapas para evitar acumular páginas residentes. max_bin=31, amostra de construção de bins=20.000 e pool de histogramas=32 MiB. A proteção continua exigindo RAM livre ≥800 MiB e commit livre ≥1.200 MiB; há também limite de RSS de 3.072 MiB. Pico RSS medido pelo sistema operacional (peak_wset), inclusive entre chamadas do vigia.

Decodificação reutiliza guloso, matching e max-regret do E002, com probabilidade calibrada e FIM privado. Limiar remove arestas reais abaixo de 0/0,5/0,8/0,95; FIM permanece. Para cada decodificador há variante que veta retorno para coluna anterior, exceto arestas que envolvem margem/cabeçalho. A costura de caminhos continua sendo a do E002; o veto se aplica às arestas do grafo, não garante monotonicidade da sequência costurada.

K, decodificador, limiar e veto escolhidos pela média de quebras de golden_v4/RN com peso igual; desempate por τ e nome. O arquivo `selecao_congelada.json` precede a abertura/avaliação das externas. IC95 percentil em 5.000 bootstraps por veículo e Wilcoxon Pratt nas médias dos veículos, importados; caráter exploratório. RN tem um veículo, portanto IC degenerado e p pouco informativo. Não se somam as bancadas sobrepostas.

Híbrido 67 e regra_reordena usam somente ordens salvas. RN não tem LayoutReader/reordena salvos; páginas densas permitem híbrido=regra, mas sua média parcial não representa RN e os contrastes indicam o n pareado. Nenhum modelo de GPU é executado para completar lacunas.

Critérios do cartão: {"ajuste_reducao_10": true, "golden_v3_novo_hibrido": true, "golden_v3_novo_tau": false, "teste_silver_hibrido": true, "teste_silver_tau": false}.

Pico de RSS desta execução: 574,72 MiB; RSS na publicação: 376,94 MiB. Medição: psutil: RSS e peak_wset do sistema operacional. Em retomadas, este pico cobre o processo atual; os picos de treino e checkpoints são preservados separadamente.

Amostragem efetiva: 15443552 → 4000000 pares; 2221380 obrigatórios (todos os 436454 positivos incluídos) e 1778620 de 13222172 negativos restantes. Fração fixa realizada: 0,134517990 (semente 7); taxa de retenção dos obrigatórios = 1. Correção: Sem correcao analitica: selecao de hiperparametros e Platt em OOF completo nao amostrado. Pico RSS até o fim do treino: 574,72 MiB.

LightGBM 4.7.0; 3140 páginas; 15443552 pares; 436454 positivos. Tempo de features 760,96 s; treino CV+refit 184,05 s. Semente fixa 20261102 (esta execução não estima variância entre três sementes).

### Importância das features (gain)

| Feature | Gain |
|---|---:|
| sucessor_regra | 14252259,971 |
| primeira_abaixo | 953149,393 |
| dist_h | 470922,060 |
| gap_y_h | 348541,003 |
| dy_pagina | 299929,453 |
| dy_h | 274431,326 |
| j_pos_coluna | 259410,602 |
| i_y | 238697,134 |
| dx_h | 225165,129 |
| sobreposicao_x | 179713,961 |
| i_pos_coluna | 172427,181 |
| i_altura | 148294,166 |
| i_x | 147958,584 |
| j_altura | 136653,305 |
| alinha_esquerda_h | 124953,908 |
| i_largura | 111489,527 |
| j_log_caracteres | 108053,403 |
| dx_pagina | 97721,601 |
| dist_pagina | 96170,022 |
| mesma_coluna | 78481,604 |
| j_largura | 60046,241 |
| delta_pos_regra | 58518,244 |
| j_log_palavras | 51640,665 |
| rank_candidato_relativo | 48807,784 |
| rank_candidato | 47032,259 |
| i_log_palavras | 46005,164 |
| i_log_caracteres | 39501,610 |
| j_pos_regra | 37403,292 |
| i_pos_regra | 34465,684 |
| j_y | 22857,023 |
| j_coluna | 21841,285 |
| i_margem_topo | 18835,005 |
| i_ponto_final | 18719,854 |
| j_x | 17767,757 |
| i_margem_rodape | 13248,773 |
| i_fim_coluna | 12362,078 |
| i_coluna | 11137,162 |
| i_pontuacao_final | 10824,717 |
| j_margem_rodape | 9085,202 |
| j_inicio_minuscula | 8203,351 |
| j_inicio_maiuscula | 6884,214 |
| candidato_extra | 4800,865 |
| i_inicio_minuscula | 3634,543 |
| j_imagem | 3297,810 |
| salto_coluna | 2846,368 |
| i_ponte | 2399,907 |
| j_pontuacao_final | 1817,296 |
| i_numeracao | 1689,702 |
| j_ponto_final | 1591,845 |
| i_inicio_maiuscula | 1502,101 |
| j_numeracao | 1066,005 |
| i_tabela | 537,803 |
| j_margem_topo | 479,175 |
| j_fim_coluna | 344,915 |
| j_texto | 316,856 |
| j_tabela | 213,824 |
| j_hifen_final | 103,463 |
| j_ponte | 96,276 |
| i_texto | 83,436 |
| i_imagem | 60,887 |
| i_margem_marca | 0,000 |
| i_hifen_final | 0,000 |
| i_repeticao | 0,000 |
| i_repeticao_disponivel | 0,000 |
| j_margem_marca | 0,000 |
| j_repeticao | 0,000 |
| j_repeticao_disponivel | 0,000 |
| fim | 0,000 |

Pares preparados: 3140 páginas, 7 veículos, 15443552 pares e 436454 positivos; 5403 fontes válidas sem ouro no grafo. Tempo registrado de extração: 760,96 s. Matrizes mapeadas/cache prontos para retomada.

Exclusões da supervisão silver: `{"sem_palavras": 2794, "fonte_nao_contigua_ou_interna_divergente": 6616, "alvo_nao_contiguo_ou_fronteira_interna": 5145}`.

## golden_v4 — ajuste

Páginas: 44; veículos: 27.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 44 | 0,985948 | 6,045455 | 11,885 | 0,948129 | 0,927240 | 100% |
| hibrido67 | 44 | 0,979738 | 5,136364 | 6,041 | 0,973419 | 0,966143 | 100% |
| regra_reordena | 44 | 0,985967 | 5,181818 | 10,905 | 0,954405 | 0,936322 | 100% |
| layoutreader_pronto | 44 | 0,913071 | 18,386364 | 11,088 | 0,935197 | 0,927182 | 100% |
| grafo_K24_maxregret_t0.00 | 44 | 0,937961 | 3,613636 | 7,778 | 0,963953 | 0,955269 | 100% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
| regra | regra | 44 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra | regra | 44 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra | regra | 44 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra | regra | 44 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra | regra | 44 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra | hibrido67 | 44 | tau | 0,006211 [-0,009968; 0,033051] | 0,127972 | 4/24/16 |
| regra | hibrido67 | 44 | quebras | 0,909091 [0,095238; 1,775567] | 0,022323 | 4/24/16 |
| regra | hibrido67 | 44 | quebras_mil | 5,843509 [0,457171; 14,066405] | 0,040740 | 4/24/16 |
| regra | hibrido67 | 44 | fid12 | -0,025290 [-0,063276; -0,000783] | 0,136481 | 5/25/14 |
| regra | hibrido67 | 44 | sucessor_linhas | -0,038903 [-0,092315; -0,004194] | 0,031875 | 4/24/16 |
| hibrido67 | regra | 44 | tau | -0,006211 [-0,033051; 0,009968] | 0,127972 | 16/24/4 |
| hibrido67 | regra | 44 | quebras | -0,909091 [-1,775567; -0,095238] | 0,022323 | 16/24/4 |
| hibrido67 | regra | 44 | quebras_mil | -5,843509 [-14,066405; -0,457171] | 0,040740 | 16/24/4 |
| hibrido67 | regra | 44 | fid12 | 0,025290 [0,000783; 0,063276] | 0,136481 | 14/25/5 |
| hibrido67 | regra | 44 | sucessor_linhas | 0,038903 [0,004194; 0,092315] | 0,031875 | 16/24/4 |
| hibrido67 | hibrido67 | 44 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| hibrido67 | hibrido67 | 44 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| hibrido67 | hibrido67 | 44 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| hibrido67 | hibrido67 | 44 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| hibrido67 | hibrido67 | 44 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| regra_reordena | regra | 44 | tau | 0,000018 [0,000001; 0,000043] | 0,052640 | 8/34/2 |
| regra_reordena | regra | 44 | quebras | -0,863636 [-1,609756; -0,309394] | 0,014913 | 8/35/1 |
| regra_reordena | regra | 44 | quebras_mil | -0,980061 [-1,776912; -0,307305] | 0,014934 | 8/35/1 |
| regra_reordena | regra | 44 | fid12 | 0,006277 [0,001896; 0,011817] | 0,004877 | 8/36/0 |
| regra_reordena | regra | 44 | sucessor_linhas | 0,009082 [0,002452; 0,017734] | 0,004877 | 8/36/0 |
| regra_reordena | hibrido67 | 44 | tau | 0,006229 [-0,009953; 0,033062] | 0,370509 | 9/20/15 |
| regra_reordena | hibrido67 | 44 | quebras | 0,045455 [-0,975000; 0,958333] | 0,834662 | 9/21/14 |
| regra_reordena | hibrido67 | 44 | quebras_mil | 4,863449 [-0,461111; 12,961476] | 0,484401 | 9/21/14 |
| regra_reordena | hibrido67 | 44 | fid12 | -0,019013 [-0,056696; 0,005501] | 0,683343 | 10/22/12 |
| regra_reordena | hibrido67 | 44 | sucessor_linhas | -0,029821 [-0,080558; 0,003452] | 0,397301 | 9/21/14 |
| layoutreader_pronto | regra | 44 | tau | -0,072877 [-0,142894; -0,015683] | 0,159733 | 23/6/15 |
| layoutreader_pronto | regra | 44 | quebras | 12,340909 [-0,636600; 37,951282] | 0,875629 | 24/6/14 |
| layoutreader_pronto | regra | 44 | quebras_mil | -0,796776 [-10,674428; 9,065099] | 0,691695 | 24/6/14 |
| layoutreader_pronto | regra | 44 | fid12 | -0,012932 [-0,072421; 0,039481] | 0,763856 | 23/7/14 |
| layoutreader_pronto | regra | 44 | sucessor_linhas | -0,000058 [-0,072015; 0,066448] | 0,718460 | 24/6/14 |
| layoutreader_pronto | hibrido67 | 44 | tau | -0,066667 [-0,130903; -0,015829] | 0,100911 | 7/26/11 |
| layoutreader_pronto | hibrido67 | 44 | quebras | 13,250000 [0,404643; 38,513974] | 0,599871 | 8/26/10 |
| layoutreader_pronto | hibrido67 | 44 | quebras_mil | 5,046733 [0,193235; 11,940388] | 0,667893 | 8/26/10 |
| layoutreader_pronto | hibrido67 | 44 | fid12 | -0,038222 [-0,086461; -0,004387] | 0,419317 | 9/26/9 |
| layoutreader_pronto | hibrido67 | 44 | sucessor_linhas | -0,038960 [-0,093039; -0,002874] | 0,667893 | 8/26/10 |
| grafo_K24_maxregret_t0.00 | regra | 44 | tau | -0,047987 [-0,147284; 0,003696] | 0,512256 | 16/19/9 |
| grafo_K24_maxregret_t0.00 | regra | 44 | quebras | -2,431818 [-4,139535; -1,162668] | 0,000513 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | 44 | quebras_mil | -4,106956 [-8,299765; -1,291931] | 0,001055 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | 44 | fid12 | 0,015824 [0,006260; 0,026694] | 0,002085 | 19/23/2 |
| grafo_K24_maxregret_t0.00 | regra | 44 | sucessor_linhas | 0,028029 [0,008366; 0,056655] | 0,000835 | 21/21/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 44 | tau | -0,041776 [-0,143114; 0,021494] | 0,932963 | 16/9/19 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 44 | quebras | -1,522727 [-3,500000; -0,074869] | 0,069212 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 44 | quebras_mil | 1,736553 [-1,856740; 6,157636] | 0,952089 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 44 | fid12 | -0,009466 [-0,039952; 0,013016] | 0,923364 | 18/11/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 44 | sucessor_linhas | -0,010874 [-0,038913; 0,012273] | 0,971242 | 17/10/17 |

### Recall por classe, antes → depois dos extras

| K | Classe | E002 presentes/elegíveis | Recall E002 | Novo presentes/elegíveis | Recall novo | Erros presentes/elegíveis | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 3144/3148 | 0,998729 | 3144/3148 | 0,998729 | 44/48 | 1 | 0 |
| 12 | Fim de coluna → topo da próxima | 9/13 | 0,692308 | 13/13 | 1,000000 | 3/3 | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 58/59 | 0,983051 | 58/59 | 0,983051 | 6/7 | 0 | 1 |
| 12 | Salto ou fronteira de elemento transversal | 19/25 | 0,760000 | 21/25 | 0,840000 | 14/18 | 1 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 175/204 | 0,857843 | 180/204 | 0,882353 | 105/128 | 8 | 3 |
| 12 | Outro | 107/112 | 0,955357 | 107/112 | 0,955357 | 23/28 | 1112 | 1 |
| 24 | Continuação na mesma coluna | 3147/3148 | 0,999682 | 3147/3148 | 0,999682 | 47/48 | 1 | 0 |
| 24 | Fim de coluna → topo da próxima | 9/13 | 0,692308 | 13/13 | 1,000000 | 3/3 | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 59/59 | 1,000000 | 59/59 | 1,000000 | 7/7 | 0 | 1 |
| 24 | Salto ou fronteira de elemento transversal | 19/25 | 0,760000 | 21/25 | 0,840000 | 14/18 | 1 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 183/204 | 0,897059 | 188/204 | 0,921569 | 112/128 | 8 | 3 |
| 24 | Outro | 109/112 | 0,973214 | 109/112 | 0,973214 | 25/28 | 1112 | 1 |
| 32 | Continuação na mesma coluna | 3147/3148 | 0,999682 | 3147/3148 | 0,999682 | 47/48 | 1 | 0 |
| 32 | Fim de coluna → topo da próxima | 9/13 | 0,692308 | 13/13 | 1,000000 | 3/3 | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 59/59 | 1,000000 | 59/59 | 1,000000 | 7/7 | 0 | 1 |
| 32 | Salto ou fronteira de elemento transversal | 19/25 | 0,760000 | 21/25 | 0,840000 | 14/18 | 1 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 187/204 | 0,916667 | 192/204 | 0,941176 | 116/128 | 8 | 3 |
| 32 | Outro | 110/112 | 0,982143 | 110/112 | 0,982143 | 26/28 | 1112 | 1 |

### Decomposição de quebras e sucessores por classe

| Método | Classe | Quebras/pág | Δ regra [IC95 veículo] | p veículo | Certos/ouro | Reparos/regressões vs regra |
|---|---|---:|---:|---:|---:|---:|
| regra | Continuação na mesma coluna | 1,227 | 0,000 [0,000; 0,000] | 1,000000 | 3101/3149 | 0/0 |
| regra | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| regra | Entrada/saída de tabela ou imagem | 0,205 | 0,000 [0,000; 0,000] | 1,000000 | 52/60 | 0/0 |
| regra | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| regra | Cabeçalho/rodapé/marca marginal | 3,045 | 0,000 [0,000; 0,000] | 1,000000 | 82/213 | 0/0 |
| regra | Outro | 1,091 | 0,000 [0,000; 0,000] | 1,000000 | 1195/1224 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 1,114 | -0,114 [-0,225; -0,022] | 0,045625 | 3107/3149 | 6/0 |
| hibrido67 | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,432 | 0,227 [0,022; 0,548] | 0,045708 | 42/60 | 1/11 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 2,295 | -0,750 [-1,429; -0,244] | 0,004247 | 119/213 | 42/5 |
| hibrido67 | Outro | 0,818 | -0,273 [-0,592; 0,000] | 0,232909 | 1204/1224 | 9/0 |
| regra_reordena | Continuação na mesma coluna | 0,864 | -0,364 [-0,700; -0,114] | 0,008362 | 3118/3149 | 17/0 |
| regra_reordena | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,205 | 0,000 [0,000; 0,000] | 1,000000 | 52/60 | 0/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 2,977 | -0,068 [-0,143; 0,000] | 0,083379 | 85/213 | 3/0 |
| regra_reordena | Outro | 0,659 | -0,432 [-0,861; -0,114] | 0,016137 | 1212/1224 | 17/0 |
| layoutreader_pronto | Continuação na mesma coluna | 14,977 | 13,750 [1,375; 38,381] | 0,185073 | 2496/3149 | 32/637 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,136 | 0,068 [0,000; 0,189] | 0,157373 | 7/13 | 0/3 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,682 | 0,477 [0,128; 0,951] | 0,008374 | 30/60 | 1/23 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,114 | -0,295 [-1,024; 0,082] | 0,937545 | 19/26 | 14/3 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 1,205 | -1,841 [-2,574; -1,050] | 0,000528 | 167/213 | 93/8 |
| layoutreader_pronto | Outro | 1,273 | 0,182 [-0,512; 1,079] | 0,911995 | 1191/1224 | 15/19 |
| grafo_K24_maxregret_t0.00 | Continuação na mesma coluna | 0,500 | -0,727 [-1,659; -0,176] | 0,004869 | 3134/3149 | 33/0 |
| grafo_K24_maxregret_t0.00 | Fim de coluna → topo da próxima | 0,091 | 0,023 [0,000; 0,067] | 0,317311 | 9/13 | 0/1 |
| grafo_K24_maxregret_t0.00 | Entrada/saída de tabela ou imagem | 0,205 | 0,000 [0,000; 0,000] | 1,000000 | 52/60 | 0/0 |
| grafo_K24_maxregret_t0.00 | Salto ou fronteira de elemento transversal | 0,182 | -0,227 [-0,775; 0,045] | 0,534300 | 18/26 | 11/1 |
| grafo_K24_maxregret_t0.00 | Cabeçalho/rodapé/marca marginal | 1,955 | -1,091 [-1,860; -0,400] | 0,006127 | 129/213 | 51/4 |
| grafo_K24_maxregret_t0.00 | Outro | 0,682 | -0,409 [-0,842; -0,048] | 0,098463 | 1211/1224 | 17/1 |

Tempo médio registrado por página: contexto/features/escore 166,60 ms; decoder 77,53 ms. Exclui a régua; contexto inicial também prepara diagnóstico, portanto é limite superior do custo produtivo.

## validacao_silver — ajuste

Páginas: 15; veículos: 1.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 15 | 0,957218 | 16,666667 | 10,285 | 0,952328 | 0,910859 | 100% |
| hibrido67 (parcial) | 13 | 0,958544 | 17,846154 | 9,554 | 0,955769 | 0,916132 | 100% |
| regra_reordena | 0 | indisponível | — | — | — | — | — |
| layoutreader_pronto | 0 | indisponível | — | — | — | — | — |
| grafo_K24_maxregret_t0.00 | 15 | 0,686666 | 9,466667 | 6,132 | 0,970249 | 0,947916 | 100% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
| regra | regra | 15 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| regra | regra | 15 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| regra | regra | 15 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| regra | regra | 15 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| regra | regra | 15 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| regra | hibrido67 (parcial) | 13 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| regra | hibrido67 (parcial) | 13 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| regra | hibrido67 (parcial) | 13 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| regra | hibrido67 (parcial) | 13 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| regra | hibrido67 (parcial) | 13 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | regra (parcial) | 13 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | regra (parcial) | 13 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | regra (parcial) | 13 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | regra (parcial) | 13 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | regra (parcial) | 13 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | hibrido67 (parcial) | 13 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | hibrido67 (parcial) | 13 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | hibrido67 (parcial) | 13 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | hibrido67 (parcial) | 13 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| hibrido67 | hibrido67 (parcial) | 13 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/13/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | tau | -0,270551 [-0,270551; -0,270551] | 0,317311 | 3/4/8 |
| grafo_K24_maxregret_t0.00 | regra | 15 | quebras | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | quebras_mil | -4,152893 [-4,152893; -4,152893] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | fid12 | 0,017921 [0,017921; 0,017921] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | sucessor_linhas | 0,037057 [0,037057; 0,037057] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 (parcial) | 13 | tau | -0,170445 [-0,170445; -0,170445] | 0,317311 | 3/4/6 |
| grafo_K24_maxregret_t0.00 | hibrido67 (parcial) | 13 | quebras | -8,153846 [-8,153846; -8,153846] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 (parcial) | 13 | quebras_mil | -4,268513 [-4,268513; -4,268513] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 (parcial) | 13 | fid12 | 0,018070 [0,018070; 0,018070] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 (parcial) | 13 | sucessor_linhas | 0,038096 [0,038096; 0,038096] | 0,317311 | 9/4/0 |

### Recall por classe, antes → depois dos extras

| K | Classe | E002 presentes/elegíveis | Recall E002 | Novo presentes/elegíveis | Recall novo | Erros presentes/elegíveis | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 2244/2245 | 0,999555 | 2244/2245 | 0,999555 | 20/21 | 0 | 0 |
| 12 | Fim de coluna → topo da próxima | 3/3 | 1,000000 | 3/3 | 1,000000 | 0/0 | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 12/12 | 1,000000 | 12/12 | 1,000000 | 2/2 | 0 | 6 |
| 12 | Salto ou fronteira de elemento transversal | 10/13 | 0,769231 | 12/13 | 0,923077 | 7/7 | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 95/132 | 0,719697 | 95/132 | 0,719697 | 49/86 | 0 | 0 |
| 12 | Outro | 113/139 | 0,812950 | 113/139 | 0,812950 | 51/77 | 2462 | 50 |
| 24 | Continuação na mesma coluna | 2245/2245 | 1,000000 | 2245/2245 | 1,000000 | 21/21 | 0 | 0 |
| 24 | Fim de coluna → topo da próxima | 3/3 | 1,000000 | 3/3 | 1,000000 | 0/0 | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 12/12 | 1,000000 | 12/12 | 1,000000 | 2/2 | 0 | 6 |
| 24 | Salto ou fronteira de elemento transversal | 13/13 | 1,000000 | 13/13 | 1,000000 | 7/7 | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 96/132 | 0,727273 | 96/132 | 0,727273 | 50/86 | 0 | 0 |
| 24 | Outro | 127/139 | 0,913669 | 127/139 | 0,913669 | 65/77 | 2462 | 50 |
| 32 | Continuação na mesma coluna | 2245/2245 | 1,000000 | 2245/2245 | 1,000000 | 21/21 | 0 | 0 |
| 32 | Fim de coluna → topo da próxima | 3/3 | 1,000000 | 3/3 | 1,000000 | 0/0 | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 12/12 | 1,000000 | 12/12 | 1,000000 | 2/2 | 0 | 6 |
| 32 | Salto ou fronteira de elemento transversal | 13/13 | 1,000000 | 13/13 | 1,000000 | 7/7 | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 99/132 | 0,750000 | 99/132 | 0,750000 | 53/86 | 0 | 0 |
| 32 | Outro | 130/139 | 0,935252 | 130/139 | 0,935252 | 68/77 | 2462 | 50 |

### Decomposição de quebras e sucessores por classe

| Método | Classe | Quebras/pág | Δ regra [IC95 veículo] | p veículo | Certos/ouro | Reparos/regressões vs regra |
|---|---|---:|---:|---:|---:|---:|
| regra | Continuação na mesma coluna | 1,400 | 0,000 [0,000; 0,000] | 1,000000 | 2224/2245 | 0/0 |
| regra | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| regra | Entrada/saída de tabela ou imagem | 0,533 | 0,000 [0,000; 0,000] | 1,000000 | 10/18 | 0/0 |
| regra | Salto ou fronteira de elemento transversal | 0,400 | 0,000 [0,000; 0,000] | 1,000000 | 6/13 | 0/0 |
| regra | Cabeçalho/rodapé/marca marginal | 5,267 | 0,000 [0,000; 0,000] | 1,000000 | 46/132 | 0/0 |
| regra | Outro | 9,067 | 0,000 [0,000; 0,000] | 1,000000 | 2473/2601 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 1,615 | 0,000 [0,000; 0,000] | 1,000000 | 2202/2223 | 0/0 |
| hibrido67 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,231 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,462 | 0,000 [0,000; 0,000] | 1,000000 | 6/13 | 0/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 5,462 | 0,000 [0,000; 0,000] | 1,000000 | 41/118 | 0/0 |
| hibrido67 | Outro | 10,077 | 0,000 [0,000; 0,000] | 1,000000 | 216/340 | 0/0 |
| grafo_K24_maxregret_t0.00 | Continuação na mesma coluna | 0,267 | -1,133 [-1,133; -1,133] | 0,317311 | 2241/2245 | 17/0 |
| grafo_K24_maxregret_t0.00 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| grafo_K24_maxregret_t0.00 | Entrada/saída de tabela ou imagem | 0,467 | -0,067 [-0,067; -0,067] | 0,317311 | 10/18 | 0/0 |
| grafo_K24_maxregret_t0.00 | Salto ou fronteira de elemento transversal | 0,333 | -0,067 [-0,067; -0,067] | 0,317311 | 7/13 | 1/0 |
| grafo_K24_maxregret_t0.00 | Cabeçalho/rodapé/marca marginal | 2,800 | -2,467 [-2,467; -2,467] | 0,317311 | 84/132 | 38/0 |
| grafo_K24_maxregret_t0.00 | Outro | 5,600 | -3,467 [-3,467; -3,467] | 0,317311 | 2525/2601 | 53/1 |

Tempo médio registrado por página: contexto/features/escore 693,43 ms; decoder 165,46 ms. Exclui a régua; contexto inicial também prepara diagnóstico, portanto é limite superior do custo produtivo.

## golden_v3_novo — externa

Páginas: 27; veículos: 10.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 27 | 0,959557 | 9,222222 | 17,206 | 0,928415 | 0,911301 | 100% |
| hibrido67 | 27 | 0,958977 | 7,888889 | 13,739 | 0,941220 | 0,938410 | 100% |
| regra_reordena | 27 | 0,959578 | 7,777778 | 14,720 | 0,936469 | 0,925754 | 100% |
| layoutreader_pronto | 27 | 0,950875 | 16,222222 | 18,145 | 0,927948 | 0,908337 | 100% |
| grafo_K24_maxregret_t0.00 | 27 | 0,941737 | 6,518519 | 12,942 | 0,941194 | 0,935275 | 100% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
| regra | regra | 27 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra | regra | 27 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra | regra | 27 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra | regra | 27 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra | regra | 27 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra | hibrido67 | 27 | tau | 0,000580 [-0,005062; 0,004980] | 0,151855 | 2/17/8 |
| regra | hibrido67 | 27 | quebras | 1,333333 [0,363636; 2,648682] | 0,027670 | 2/18/7 |
| regra | hibrido67 | 27 | quebras_mil | 3,466289 [0,665607; 9,191916] | 0,027670 | 2/18/7 |
| regra | hibrido67 | 27 | fid12 | -0,012805 [-0,028351; -0,003514] | 0,016924 | 2/17/8 |
| regra | hibrido67 | 27 | sucessor_linhas | -0,027108 [-0,061825; -0,006827] | 0,027670 | 2/18/7 |
| hibrido67 | regra | 27 | tau | -0,000580 [-0,004980; 0,005062] | 0,151855 | 8/17/2 |
| hibrido67 | regra | 27 | quebras | -1,333333 [-2,648682; -0,363636] | 0,027670 | 7/18/2 |
| hibrido67 | regra | 27 | quebras_mil | -3,466289 [-9,191916; -0,665607] | 0,027670 | 7/18/2 |
| hibrido67 | regra | 27 | fid12 | 0,012805 [0,003514; 0,028351] | 0,016924 | 8/17/2 |
| hibrido67 | regra | 27 | sucessor_linhas | 0,027108 [0,006827; 0,061825] | 0,027670 | 7/18/2 |
| hibrido67 | hibrido67 | 27 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| hibrido67 | hibrido67 | 27 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| hibrido67 | hibrido67 | 27 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| hibrido67 | hibrido67 | 27 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| hibrido67 | hibrido67 | 27 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| regra_reordena | regra | 27 | tau | 0,000020 [-0,000058; 0,000110] | 0,099906 | 8/17/2 |
| regra_reordena | regra | 27 | quebras | -1,444444 [-2,391343; 0,263246] | 0,425964 | 7/18/2 |
| regra_reordena | regra | 27 | quebras_mil | -2,485708 [-4,591081; 0,010497] | 0,366915 | 7/18/2 |
| regra_reordena | regra | 27 | fid12 | 0,008054 [0,001959; 0,013426] | 0,123765 | 7/18/2 |
| regra_reordena | regra | 27 | sucessor_linhas | 0,014452 [0,001706; 0,022753] | 0,152358 | 7/19/1 |
| regra_reordena | hibrido67 | 27 | tau | 0,000600 [-0,005005; 0,005014] | 0,640316 | 6/14/7 |
| regra_reordena | hibrido67 | 27 | quebras | -0,111111 [-1,696970; 2,353493] | 0,194009 | 6/15/6 |
| regra_reordena | hibrido67 | 27 | quebras_mil | 0,980581 [-3,341196; 8,226514] | 0,232439 | 6/15/6 |
| regra_reordena | hibrido67 | 27 | fid12 | -0,004751 [-0,022459; 0,003389] | 0,323922 | 5/15/7 |
| regra_reordena | hibrido67 | 27 | sucessor_linhas | -0,012656 [-0,052451; 0,008377] | 0,160984 | 6/15/6 |
| layoutreader_pronto | regra | 27 | tau | -0,008682 [-0,044392; 0,011608] | 0,838256 | 17/4/6 |
| layoutreader_pronto | regra | 27 | quebras | 7,000000 [-2,130435; 22,250329] | 0,838153 | 14/5/8 |
| layoutreader_pronto | regra | 27 | quebras_mil | 0,939286 [-7,348811; 7,815402] | 0,759463 | 14/5/8 |
| layoutreader_pronto | regra | 27 | fid12 | -0,000467 [-0,034490; 0,025810] | 0,759463 | 16/4/7 |
| layoutreader_pronto | regra | 27 | sucessor_linhas | -0,002965 [-0,062181; 0,052348] | 0,540291 | 14/5/8 |
| layoutreader_pronto | hibrido67 | 27 | tau | -0,008102 [-0,045276; 0,010976] | 0,508883 | 9/14/4 |
| layoutreader_pronto | hibrido67 | 27 | quebras | 8,333333 [0,235181; 22,947758] | 0,123232 | 7/14/6 |
| layoutreader_pronto | hibrido67 | 27 | quebras_mil | 4,405575 [0,416212; 9,882331] | 0,123232 | 7/14/6 |
| layoutreader_pronto | hibrido67 | 27 | fid12 | -0,013272 [-0,042927; 0,004089] | 0,440900 | 8/14/5 |
| layoutreader_pronto | hibrido67 | 27 | sucessor_linhas | -0,030073 [-0,080596; 0,000339] | 0,440900 | 7/14/6 |
| grafo_K24_maxregret_t0.00 | regra | 27 | tau | -0,017820 [-0,052402; 0,001460] | 0,721277 | 10/11/6 |
| grafo_K24_maxregret_t0.00 | regra | 27 | quebras | -2,703704 [-3,263158; -2,153750] | 0,005698 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | 27 | quebras_mil | -4,264012 [-7,004880; -2,758572] | 0,005857 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | 27 | fid12 | 0,012779 [0,005176; 0,017981] | 0,102470 | 11/12/4 |
| grafo_K24_maxregret_t0.00 | regra | 27 | sucessor_linhas | 0,023974 [0,009214; 0,040091] | 0,074462 | 13/11/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 27 | tau | -0,017240 [-0,052709; 0,004620] | 0,307434 | 6/11/10 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 27 | quebras | -1,370370 [-2,558824; 0,230769] | 0,258449 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 27 | quebras_mil | -0,797723 [-2,973005; 2,672809] | 0,681519 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 27 | fid12 | -0,000026 [-0,018935; 0,009917] | 0,474959 | 8/11/8 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 27 | sucessor_linhas | -0,003134 [-0,030139; 0,010360] | 0,759463 | 9/12/6 |

### Recall por classe, antes → depois dos extras

| K | Classe | E002 presentes/elegíveis | Recall E002 | Novo presentes/elegíveis | Recall novo | Erros presentes/elegíveis | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 1877/1882 | 0,997343 | 1877/1882 | 0,997343 | 110/115 | 0 | 0 |
| 12 | Fim de coluna → topo da próxima | 6/8 | 0,750000 | 8/8 | 1,000000 | 2/2 | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 63/65 | 0,969231 | 64/65 | 0,984615 | 8/8 | 0 | 1 |
| 12 | Salto ou fronteira de elemento transversal | 7/7 | 1,000000 | 7/7 | 1,000000 | 2/2 | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 72/86 | 0,837209 | 73/86 | 0,848837 | 28/41 | 1 | 0 |
| 12 | Outro | 84/110 | 0,763636 | 87/110 | 0,790909 | 40/63 | 752 | 6 |
| 24 | Continuação na mesma coluna | 1882/1882 | 1,000000 | 1882/1882 | 1,000000 | 115/115 | 0 | 0 |
| 24 | Fim de coluna → topo da próxima | 6/8 | 0,750000 | 8/8 | 1,000000 | 2/2 | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 64/65 | 0,984615 | 65/65 | 1,000000 | 8/8 | 0 | 1 |
| 24 | Salto ou fronteira de elemento transversal | 7/7 | 1,000000 | 7/7 | 1,000000 | 2/2 | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 78/86 | 0,906977 | 79/86 | 0,918605 | 34/41 | 1 | 0 |
| 24 | Outro | 90/110 | 0,818182 | 92/110 | 0,836364 | 45/63 | 752 | 6 |
| 32 | Continuação na mesma coluna | 1882/1882 | 1,000000 | 1882/1882 | 1,000000 | 115/115 | 0 | 0 |
| 32 | Fim de coluna → topo da próxima | 6/8 | 0,750000 | 8/8 | 1,000000 | 2/2 | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 64/65 | 0,984615 | 65/65 | 1,000000 | 8/8 | 0 | 1 |
| 32 | Salto ou fronteira de elemento transversal | 7/7 | 1,000000 | 7/7 | 1,000000 | 2/2 | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 78/86 | 0,906977 | 79/86 | 0,918605 | 34/41 | 1 | 0 |
| 32 | Outro | 90/110 | 0,818182 | 92/110 | 0,836364 | 45/63 | 752 | 6 |

### Decomposição de quebras e sucessores por classe

| Método | Classe | Quebras/pág | Δ regra [IC95 veículo] | p veículo | Certos/ouro | Reparos/regressões vs regra |
|---|---|---:|---:|---:|---:|---:|
| regra | Continuação na mesma coluna | 3,704 | 0,000 [0,000; 0,000] | 1,000000 | 1767/1882 | 0/0 |
| regra | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| regra | Entrada/saída de tabela ou imagem | 0,333 | 0,000 [0,000; 0,000] | 1,000000 | 57/66 | 0/0 |
| regra | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| regra | Cabeçalho/rodapé/marca marginal | 1,519 | 0,000 [0,000; 0,000] | 1,000000 | 46/87 | 0/0 |
| regra | Outro | 3,481 | 0,000 [0,000; 0,000] | 1,000000 | 793/862 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 3,407 | -0,296 [-0,625; -0,062] | 0,046624 | 1777/1882 | 10/0 |
| hibrido67 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,150; 0,000] | 0,317311 | 58/66 | 1/0 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 1,296 | -0,222 [-0,929; 0,000] | 0,157874 | 52/87 | 11/5 |
| hibrido67 | Outro | 2,704 | -0,778 [-1,667; -0,071] | 0,047376 | 810/862 | 17/0 |
| regra_reordena | Continuação na mesma coluna | 2,889 | -0,815 [-1,559; -0,091] | 0,122706 | 1793/1882 | 29/3 |
| regra_reordena | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,167; 0,000] | 0,317311 | 58/66 | 1/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 1,593 | 0,074 [0,000; 0,308] | 0,317311 | 44/87 | 0/2 |
| regra_reordena | Outro | 2,815 | -0,667 [-1,300; 0,474] | 0,425638 | 809/862 | 19/3 |
| layoutreader_pronto | Continuação na mesma coluna | 12,593 | 8,889 [0,000; 23,684] | 0,410536 | 1527/1882 | 22/262 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,111 | 0,037 [0,000; 0,167] | 0,317311 | 5/8 | 1/2 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,407 | 0,074 [-0,188; 0,286] | 0,953453 | 55/66 | 4/6 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,037 | -0,074 [-0,321; 0,087] | 0,940748 | 6/7 | 2/1 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 0,741 | -0,778 [-1,530; -0,278] | 0,016924 | 66/87 | 25/5 |
| layoutreader_pronto | Outro | 2,333 | -1,148 [-1,750; -0,111] | 0,100680 | 825/862 | 41/9 |
| grafo_K24_maxregret_t0.00 | Continuação na mesma coluna | 3,074 | -0,630 [-0,900; -0,375] | 0,010693 | 1796/1882 | 32/3 |
| grafo_K24_maxregret_t0.00 | Fim de coluna → topo da próxima | 0,111 | 0,037 [0,000; 0,167] | 0,317311 | 5/8 | 0/1 |
| grafo_K24_maxregret_t0.00 | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,333; 0,136] | 0,860991 | 58/66 | 3/2 |
| grafo_K24_maxregret_t0.00 | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| grafo_K24_maxregret_t0.00 | Cabeçalho/rodapé/marca marginal | 1,074 | -0,444 [-1,200; -0,100] | 0,047376 | 54/87 | 11/3 |
| grafo_K24_maxregret_t0.00 | Outro | 1,852 | -1,630 [-1,973; -0,857] | 0,010853 | 823/862 | 32/2 |

Tempo médio registrado por página: contexto/features/escore 201,35 ms; decoder 65,82 ms. Exclui a régua; contexto inicial também prepara diagnóstico, portanto é limite superior do custo produtivo.

## teste_silver — externa

Páginas: 89; veículos: 3.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 89 | 0,959565 | 27,449438 | 44,496 | 0,825401 | 0,840212 | 100% |
| hibrido67 | 89 | 0,959092 | 26,426966 | 43,157 | 0,834332 | 0,849525 | 100% |
| regra_reordena | 89 | 0,959615 | 26,449438 | 43,643 | 0,831979 | 0,848023 | 100% |
| layoutreader_pronto | 89 | 0,941850 | 31,247191 | 41,826 | 0,829754 | 0,841286 | 100% |
| grafo_K24_maxregret_t0.00 | 89 | 0,942613 | 24,146067 | 41,817 | 0,838883 | 0,854450 | 100% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
| regra | regra | 89 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra | regra | 89 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra | regra | 89 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra | regra | 89 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra | regra | 89 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra | hibrido67 | 89 | tau | 0,000473 [-0,000483; 0,001598] | 1,000000 | 7/66/16 |
| regra | hibrido67 | 89 | quebras | 1,022472 [0,076923; 1,894737] | 0,108809 | 3/72/14 |
| regra | hibrido67 | 89 | quebras_mil | 1,338308 [0,051975; 1,847069] | 0,108809 | 3/72/14 |
| regra | hibrido67 | 89 | fid12 | -0,008931 [-0,010450; -0,000277] | 0,108809 | 0/74/15 |
| regra | hibrido67 | 89 | sucessor_linhas | -0,009313 [-0,011315; -0,000078] | 0,108809 | 3/72/14 |
| hibrido67 | regra | 89 | tau | -0,000473 [-0,001598; 0,000483] | 1,000000 | 16/66/7 |
| hibrido67 | regra | 89 | quebras | -1,022472 [-1,894737; -0,076923] | 0,108809 | 14/72/3 |
| hibrido67 | regra | 89 | quebras_mil | -1,338308 [-1,847069; -0,051975] | 0,108809 | 14/72/3 |
| hibrido67 | regra | 89 | fid12 | 0,008931 [0,000277; 0,010450] | 0,108809 | 15/74/0 |
| hibrido67 | regra | 89 | sucessor_linhas | 0,009313 [0,000078; 0,011315] | 0,108809 | 14/72/3 |
| hibrido67 | hibrido67 | 89 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| hibrido67 | hibrido67 | 89 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| hibrido67 | hibrido67 | 89 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| hibrido67 | hibrido67 | 89 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| hibrido67 | hibrido67 | 89 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| regra_reordena | regra | 89 | tau | 0,000049 [0,000008; 0,000105] | 0,108809 | 22/59/8 |
| regra_reordena | regra | 89 | quebras | -1,000000 [-1,692308; -0,394737] | 0,108809 | 24/61/4 |
| regra_reordena | regra | 89 | quebras_mil | -0,853045 [-1,065089; -0,632840] | 0,108809 | 24/61/4 |
| regra_reordena | regra | 89 | fid12 | 0,006579 [0,004186; 0,009232] | 0,108809 | 21/64/4 |
| regra_reordena | regra | 89 | sucessor_linhas | 0,007812 [0,004976; 0,011463] | 0,108809 | 24/61/4 |
| regra_reordena | hibrido67 | 89 | tau | 0,000523 [-0,000378; 0,001606] | 1,000000 | 20/48/21 |
| regra_reordena | hibrido67 | 89 | quebras | 0,022472 [-1,615385; 0,526316] | 1,000000 | 17/56/16 |
| regra_reordena | hibrido67 | 89 | quebras_mil | 0,485262 [-0,824931; 0,781981] | 1,000000 | 17/56/16 |
| regra_reordena | hibrido67 | 89 | fid12 | -0,002353 [-0,005631; 0,003910] | 0,592980 | 12/60/17 |
| regra_reordena | hibrido67 | 89 | sucessor_linhas | -0,001501 [-0,005494; 0,005348] | 1,000000 | 17/56/16 |
| layoutreader_pronto | regra | 89 | tau | -0,017716 [-0,036648; -0,001170] | 0,108809 | 50/12/27 |
| layoutreader_pronto | regra | 89 | quebras | 3,797753 [-8,000000; 54,230769] | 1,000000 | 38/30/21 |
| layoutreader_pronto | regra | 89 | quebras_mil | -2,669338 [-8,430175; 21,129744] | 1,000000 | 38/30/21 |
| layoutreader_pronto | regra | 89 | fid12 | 0,004354 [-0,129460; 0,041757] | 1,000000 | 39/32/18 |
| layoutreader_pronto | regra | 89 | sucessor_linhas | 0,001074 [-0,168836; 0,044816] | 1,000000 | 38/30/21 |
| layoutreader_pronto | hibrido67 | 89 | tau | -0,017242 [-0,036668; 0,000428] | 0,285049 | 34/35/20 |
| layoutreader_pronto | hibrido67 | 89 | quebras | 4,820225 [-6,105263; 54,307692] | 1,000000 | 24/47/18 |
| layoutreader_pronto | hibrido67 | 89 | quebras_mil | -1,331031 [-6,583106; 21,181719] | 1,000000 | 24/47/18 |
| layoutreader_pronto | hibrido67 | 89 | fid12 | -0,004578 [-0,129737; 0,031307] | 1,000000 | 24/47/18 |
| layoutreader_pronto | hibrido67 | 89 | sucessor_linhas | -0,008239 [-0,168914; 0,033501] | 1,000000 | 24/47/18 |
| grafo_K24_maxregret_t0.00 | regra | 89 | tau | -0,016953 [-0,043074; -0,000940] | 0,108809 | 21/53/15 |
| grafo_K24_maxregret_t0.00 | regra | 89 | quebras | -3,303371 [-11,384615; -0,815789] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | 89 | quebras_mil | -2,678536 [-5,533066; -1,488111] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | 89 | fid12 | 0,013482 [0,003029; 0,036290] | 0,108809 | 28/57/4 |
| grafo_K24_maxregret_t0.00 | regra | 89 | sucessor_linhas | 0,014239 [0,006451; 0,022996] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 89 | tau | -0,016479 [-0,043095; 0,000658] | 0,285049 | 21/43/25 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 89 | quebras | -2,280899 [-11,307692; -0,342105] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 89 | quebras_mil | -1,340228 [-5,481091; -0,218504] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 89 | fid12 | 0,004550 [-0,007345; 0,036013] | 0,592980 | 20/54/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 89 | sucessor_linhas | 0,004926 [-0,004019; 0,022918] | 0,285049 | 25/50/14 |

### Recall por classe, antes → depois dos extras

| K | Classe | E002 presentes/elegíveis | Recall E002 | Novo presentes/elegíveis | Recall novo | Erros presentes/elegíveis | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 7133/7140 | 0,999020 | 7133/7140 | 0,999020 | 175/180 | 0 | 5 |
| 12 | Fim de coluna → topo da próxima | 27/33 | 0,818182 | 32/33 | 0,969697 | 4/5 | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 91/94 | 0,968085 | 92/94 | 0,978723 | 8/10 | 0 | 32 |
| 12 | Salto ou fronteira de elemento transversal | 162/183 | 0,885246 | 165/183 | 0,901639 | 51/69 | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 243/269 | 0,903346 | 243/269 | 0,903346 | 116/142 | 0 | 38 |
| 12 | Outro | 708/989 | 0,715875 | 711/989 | 0,718908 | 261/539 | 6058 | 1324 |
| 24 | Continuação na mesma coluna | 7136/7140 | 0,999440 | 7136/7140 | 0,999440 | 177/180 | 0 | 5 |
| 24 | Fim de coluna → topo da próxima | 27/33 | 0,818182 | 32/33 | 0,969697 | 4/5 | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 92/94 | 0,978723 | 93/94 | 0,989362 | 9/10 | 0 | 32 |
| 24 | Salto ou fronteira de elemento transversal | 169/183 | 0,923497 | 172/183 | 0,939891 | 58/69 | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 246/269 | 0,914498 | 246/269 | 0,914498 | 119/142 | 0 | 38 |
| 24 | Outro | 748/989 | 0,756320 | 751/989 | 0,759353 | 301/539 | 6058 | 1324 |
| 32 | Continuação na mesma coluna | 7137/7140 | 0,999580 | 7137/7140 | 0,999580 | 177/180 | 0 | 5 |
| 32 | Fim de coluna → topo da próxima | 27/33 | 0,818182 | 32/33 | 0,969697 | 4/5 | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 92/94 | 0,978723 | 93/94 | 0,989362 | 9/10 | 0 | 32 |
| 32 | Salto ou fronteira de elemento transversal | 171/183 | 0,934426 | 174/183 | 0,950820 | 60/69 | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 249/269 | 0,925651 | 249/269 | 0,925651 | 122/142 | 0 | 38 |
| 32 | Outro | 769/989 | 0,777553 | 771/989 | 0,779575 | 321/539 | 6058 | 1324 |

### Decomposição de quebras e sucessores por classe

| Método | Classe | Quebras/pág | Δ regra [IC95 veículo] | p veículo | Certos/ouro | Reparos/regressões vs regra |
|---|---|---:|---:|---:|---:|---:|
| regra | Continuação na mesma coluna | 2,135 | 0,000 [0,000; 0,000] | 1,000000 | 6960/7145 | 0/0 |
| regra | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| regra | Entrada/saída de tabela ou imagem | 0,483 | 0,000 [0,000; 0,000] | 1,000000 | 84/126 | 0/0 |
| regra | Salto ou fronteira de elemento transversal | 0,742 | 0,000 [0,000; 0,000] | 1,000000 | 114/183 | 0/0 |
| regra | Cabeçalho/rodapé/marca marginal | 3,034 | 0,000 [0,000; 0,000] | 1,000000 | 127/307 | 0/0 |
| regra | Outro | 21,000 | 0,000 [0,000; 0,000] | 1,000000 | 5188/7054 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 1,944 | -0,191 [-0,342; 0,000] | 0,165518 | 6977/7145 | 19/2 |
| hibrido67 | Fim de coluna → topo da próxima | 0,045 | -0,011 [-0,026; 0,000] | 0,317311 | 29/33 | 1/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,472 | -0,011 [-0,026; 0,000] | 0,317311 | 84/126 | 0/0 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,663 | -0,079 [-0,184; 0,000] | 0,317311 | 121/183 | 7/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 2,910 | -0,124 [-0,342; 0,079] | 0,592980 | 137/307 | 19/9 |
| hibrido67 | Outro | 20,393 | -0,607 [-1,184; 0,000] | 0,165518 | 5244/7054 | 56/0 |
| regra_reordena | Continuação na mesma coluna | 1,798 | -0,337 [-0,846; -0,237] | 0,108809 | 6990/7145 | 36/6 |
| regra_reordena | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,483 | 0,000 [0,000; 0,000] | 1,000000 | 84/126 | 0/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,730 | -0,011 [-0,026; 0,000] | 0,317311 | 115/183 | 1/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 3,034 | 0,000 [0,000; 0,000] | 1,000000 | 127/307 | 0/0 |
| regra_reordena | Outro | 20,348 | -0,652 [-1,105; -0,132] | 0,108809 | 5246/7054 | 95/37 |
| layoutreader_pronto | Continuação na mesma coluna | 9,910 | 7,775 [-1,105; 54,154] | 0,592980 | 6268/7145 | 147/839 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,124 | 0,067 [0,000; 0,385] | 0,165518 | 22/33 | 2/8 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,528 | 0,045 [-0,231; 0,211] | 0,592980 | 80/126 | 4/8 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,371 | -0,371 [-2,154; -0,026] | 0,108809 | 148/183 | 38/4 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 2,562 | -0,472 [-1,079; 0,079] | 0,285049 | 167/307 | 65/25 |
| layoutreader_pronto | Outro | 17,753 | -3,247 [-5,763; 2,385] | 0,285049 | 5477/7054 | 377/88 |
| grafo_K24_maxregret_t0.00 | Continuação na mesma coluna | 0,921 | -1,213 [-4,846; -0,211] | 0,108809 | 7069/7145 | 114/5 |
| grafo_K24_maxregret_t0.00 | Fim de coluna → topo da próxima | 0,079 | 0,022 [0,000; 0,077] | 0,165518 | 25/33 | 0/3 |
| grafo_K24_maxregret_t0.00 | Entrada/saída de tabela ou imagem | 0,427 | -0,056 [-0,385; 0,000] | 0,317311 | 90/126 | 6/0 |
| grafo_K24_maxregret_t0.00 | Salto ou fronteira de elemento transversal | 0,315 | -0,427 [-2,769; -0,026] | 0,102470 | 152/183 | 39/1 |
| grafo_K24_maxregret_t0.00 | Cabeçalho/rodapé/marca marginal | 3,000 | -0,034 [-0,385; 0,026] | 1,000000 | 129/307 | 3/1 |
| grafo_K24_maxregret_t0.00 | Outro | 19,404 | -1,596 [-3,077; -0,632] | 0,108809 | 5330/7054 | 153/11 |

Tempo médio registrado por página: contexto/features/escore 263,34 ms; decoder 91,29 ms. Exclui a régua; contexto inicial também prepara diagnóstico, portanto é limite superior do custo produtivo.

## Varredura no ajuste, sem externas

| K | Decoder | Limiar | Veto coluna | Quebras v4 | Quebras RN | Média | τ médio |
|---:|---|---:|---|---:|---:|---:|---:|
| 12 | guloso | 0,00 | False | 3,841 | 11,333 | 7,587 | 0,863872 |
| 12 | guloso | 0,00 | True | 4,000 | 11,400 | 7,700 | 0,863470 |
| 12 | guloso | 0,50 | False | 4,432 | 12,067 | 8,249 | 0,877199 |
| 12 | guloso | 0,50 | True | 4,523 | 12,200 | 8,361 | 0,879756 |
| 12 | guloso | 0,80 | False | 5,295 | 14,733 | 10,014 | 0,948362 |
| 12 | guloso | 0,80 | True | 5,318 | 14,867 | 10,092 | 0,948368 |
| 12 | guloso | 0,95 | False | 5,682 | 16,333 | 11,008 | 0,957968 |
| 12 | guloso | 0,95 | True | 5,682 | 16,333 | 11,008 | 0,957968 |
| 12 | matching | 0,00 | False | 3,727 | 10,667 | 7,197 | 0,789581 |
| 12 | matching | 0,00 | True | 3,864 | 10,733 | 7,298 | 0,788530 |
| 12 | matching | 0,50 | False | 4,318 | 11,800 | 8,059 | 0,849649 |
| 12 | matching | 0,50 | True | 4,409 | 11,933 | 8,171 | 0,852207 |
| 12 | matching | 0,80 | False | 5,295 | 14,600 | 9,948 | 0,948380 |
| 12 | matching | 0,80 | True | 5,318 | 14,733 | 10,026 | 0,948386 |
| 12 | matching | 0,95 | False | 5,682 | 16,200 | 10,941 | 0,957986 |
| 12 | matching | 0,95 | True | 5,682 | 16,200 | 10,941 | 0,957986 |
| 12 | maxregret | 0,00 | False | 3,705 | 10,600 | 7,152 | 0,801188 |
| 12 | maxregret | 0,00 | True | 3,841 | 10,733 | 7,287 | 0,799898 |
| 12 | maxregret | 0,50 | False | 4,364 | 11,800 | 8,082 | 0,849649 |
| 12 | maxregret | 0,50 | True | 4,455 | 11,933 | 8,194 | 0,852206 |
| 12 | maxregret | 0,80 | False | 5,295 | 14,600 | 9,948 | 0,948380 |
| 12 | maxregret | 0,80 | True | 5,318 | 14,733 | 10,026 | 0,948386 |
| 12 | maxregret | 0,95 | False | 5,682 | 16,200 | 10,941 | 0,957986 |
| 12 | maxregret | 0,95 | True | 5,682 | 16,200 | 10,941 | 0,957986 |
| 24 | guloso | 0,00 | False | 4,136 | 10,867 | 7,502 | 0,867938 |
| 24 | guloso | 0,00 | True | 4,273 | 10,933 | 7,603 | 0,867835 |
| 24 | guloso | 0,50 | False | 4,773 | 12,133 | 8,453 | 0,873359 |
| 24 | guloso | 0,50 | True | 4,841 | 12,267 | 8,554 | 0,875913 |
| 24 | guloso | 0,80 | False | 5,659 | 14,933 | 10,296 | 0,946768 |
| 24 | guloso | 0,80 | True | 5,682 | 15,067 | 10,374 | 0,946774 |
| 24 | guloso | 0,95 | False | 6,114 | 16,533 | 11,323 | 0,956861 |
| 24 | guloso | 0,95 | True | 6,114 | 16,533 | 11,323 | 0,956861 |
| 24 | matching | 0,00 | False | 3,591 | 9,667 | 6,629 | 0,800576 |
| 24 | matching | 0,00 | True | 3,659 | 9,733 | 6,696 | 0,799585 |
| 24 | matching | 0,50 | False | 4,273 | 11,867 | 8,070 | 0,875842 |
| 24 | matching | 0,50 | True | 4,341 | 12,000 | 8,170 | 0,878392 |
| 24 | matching | 0,80 | False | 5,523 | 14,667 | 10,095 | 0,945282 |
| 24 | matching | 0,80 | True | 5,545 | 14,800 | 10,173 | 0,945288 |
| 24 | matching | 0,95 | False | 6,023 | 16,400 | 11,211 | 0,957353 |
| 24 | matching | 0,95 | True | 6,023 | 16,400 | 11,211 | 0,957353 |
| 24 | maxregret | 0,00 | False | 3,614 | 9,467 | 6,540 | 0,812314 |
| 24 | maxregret | 0,00 | True | 3,682 | 9,600 | 6,641 | 0,811084 |
| 24 | maxregret | 0,50 | False | 4,318 | 11,733 | 8,026 | 0,848977 |
| 24 | maxregret | 0,50 | True | 4,386 | 11,867 | 8,127 | 0,851528 |
| 24 | maxregret | 0,80 | False | 5,523 | 14,667 | 10,095 | 0,945282 |
| 24 | maxregret | 0,80 | True | 5,545 | 14,800 | 10,173 | 0,945288 |
| 24 | maxregret | 0,95 | False | 6,023 | 16,400 | 11,211 | 0,957353 |
| 24 | maxregret | 0,95 | True | 6,023 | 16,400 | 11,211 | 0,957353 |
| 32 | guloso | 0,00 | False | 4,591 | 11,200 | 7,895 | 0,836117 |
| 32 | guloso | 0,00 | True | 4,773 | 11,267 | 8,020 | 0,835646 |
| 32 | guloso | 0,50 | False | 5,205 | 12,533 | 8,869 | 0,872577 |
| 32 | guloso | 0,50 | True | 5,273 | 12,667 | 8,970 | 0,875137 |
| 32 | guloso | 0,80 | False | 6,045 | 15,333 | 10,689 | 0,946418 |
| 32 | guloso | 0,80 | True | 6,091 | 15,467 | 10,779 | 0,946425 |
| 32 | guloso | 0,95 | False | 6,523 | 16,933 | 11,728 | 0,956513 |
| 32 | guloso | 0,95 | True | 6,523 | 16,933 | 11,728 | 0,956513 |
| 32 | matching | 0,00 | False | 3,659 | 9,667 | 6,663 | 0,786418 |
| 32 | matching | 0,00 | True | 3,773 | 9,733 | 6,753 | 0,784159 |
| 32 | matching | 0,50 | False | 4,432 | 11,867 | 8,149 | 0,875053 |
| 32 | matching | 0,50 | True | 4,500 | 12,000 | 8,250 | 0,877614 |
| 32 | matching | 0,80 | False | 5,750 | 14,667 | 10,208 | 0,944942 |
| 32 | matching | 0,80 | True | 5,795 | 14,800 | 10,298 | 0,944949 |
| 32 | matching | 0,95 | False | 6,432 | 16,400 | 11,416 | 0,957043 |
| 32 | matching | 0,95 | True | 6,432 | 16,400 | 11,416 | 0,957043 |
| 32 | maxregret | 0,00 | False | 3,636 | 9,467 | 6,552 | 0,798158 |
| 32 | maxregret | 0,00 | True | 3,750 | 9,600 | 6,675 | 0,795660 |
| 32 | maxregret | 0,50 | False | 4,477 | 11,733 | 8,105 | 0,848188 |
| 32 | maxregret | 0,50 | True | 4,545 | 11,867 | 8,206 | 0,850749 |
| 32 | maxregret | 0,80 | False | 5,750 | 14,667 | 10,208 | 0,944942 |
| 32 | maxregret | 0,80 | True | 5,795 | 14,800 | 10,298 | 0,944949 |
| 32 | maxregret | 0,95 | False | 6,386 | 16,400 | 11,393 | 0,957044 |
| 32 | maxregret | 0,95 | True | 6,386 | 16,400 | 11,393 | 0,957044 |

## Limitações e retomada

Silver tem ruído sistemático no fluxo do PDF e piso interno aos átomos; negativos difíceis não corrigem rótulos errados. Categorias do E002 são proxies automáticas, sem causalidade humana. Margens correspondem à partição automática da regra. A página inteira entra nas métricas; a decomposição mostra margens/corpo, mas não cria uma segunda referência humana independente de corpo. Não há avaliação confirmatória nem três sementes neste pedido de semente fixa. Uma execução incompleta não satisfaz o critério de abandono/sucesso.

Retomar da raiz com `venv/Scripts/python.exe -B orquestracao/analises/e004_grafo.py`. A dependência exigida é `lightgbm` no mesmo venv. `--etapa diagnostico` executa só ajuste e não abre externas. `--max-minutos` interrompe entre páginas/lotes/20 árvores; repetir preserva o resultado concluído. `--conferir` verifica hashes dos caches, o relatório e o JSON sem alterá-los.
