1. Âncora da regra reproduzida: τ 0,985948 / 6,045455 quebras/página no golden_v4.
2. E016 reproduzido: HIER-1 no golden_v4 4,659091 / τ 0,985445; código e modelo congelados antes das externas.
3. golden_v3_novo: HIER-1 6,666667 quebras/página, τ 0,959414; Δ quebras vs híbrido -1,222222 [-2,428571; 0,611111].
4. teste_silver: HIER-1 25,056180 quebras/página, τ 0,958401; Δ quebras vs híbrido -1,370787 [-5,076923; -0,315789].
5. Segurança nas duas externas: PASSA; superioridade em uma sem piora média na outra: PASSA.
6. Uma variante, sem ajuste nem retreino; golden_v3_novo já foi consultado em rodadas anteriores; teste cego preservado.

**Veredito: GO.** HIER-1 atende ao cartão e é finalista congelado do teste cego.

# E017 — HIER-1 congelado nas externas

## Protocolo e congelamento

Uma única configuração, autorizada pelo cartão E017 após o NÃO GO do E016; o portão anterior não foi alterado. Segmentação e HIER-1 são as funções importadas do E016. Escores são produzidos pela função original do E016 com o mesmo E004 e calibração; somente o namespace de caminhos de saída é isolado. K24, max-regret, limiar zero, nenhuma restrição adicional, regra entre segmentos. Sem GPU, treino ou inferência nova do LayoutReader; o híbrido usa suas predições congeladas até 67 unidades.

SHA-256 gravados em congelamento.json antes de abrir externas:

| Fonte | SHA-256 |
|---|---|
| e016_sha256 | `1313a23a22b3f67c805ae7f23b491b3fb9b29efc53e23dfa1c247aed0df648f9` |
| e004_sha256 | `dbb496c31860782be1d211ec2e1a50e84408242229d1373240339d2ce2642c06` |
| modelo_sha256 | `d71f30779b611b9d3ee725746eab2433737bc67d21ca91b8a0cf5b6c277127e9` |

CPU, quatro threads, um processo, num_workers=0. Caches atômicos por página/escores permitem retomada da mesma execução após queda; páginas prontas não são inferidas novamente. As ordens e métricas da regra, híbrido e grafo plano são conferidas contra os controles já existentes; no ajuste, também se conferem todos os segmentos e ordens do E016. Entrada conferida com random.Random(f'entrada-{page_id}'). Linhas e átomos ls3 congelados; cobertura integral, mesmas unidades e expansões canônicas em todos os métodos.

Régua importada: erros_ponta_a_ponta e bancada_ordenadores via avaliar_ordem do E002; sem reimplementar τ de palavras, quebras, fidelidade de 12 ou sucessor de linhas. Quebras/1.000 palavras é a média das taxas por página da régua (denominador: palavras com referência). Médias por página, bancadas separadas. IC95 percentil pareado, bootstrap por veículo com 5000 reamostras e semente 20261004, funções oficiais. Wilcoxon Pratt bilateral sobre as médias dos Δ por veículo, apenas descritivo. Esta rodada externa segue a unidade veículo do cartão E017; o teste cego tem outro bootstrap, por PDF estratificado por UF, e não é executado aqui.

## Critério E017, item a item

Interseção de segurança e superioridade, sem compensar perda de τ com ganho de quebras.

| Item | Valor observado | Limiar congelado | Resultado |
|---|---:|---|---|
| (1) Segurança: golden_v3_novo | LI Δτ = -0,004394 | ≥ −0,005 | PASSA |
| (1) Segurança: teste_silver | LI Δτ = -0,002458 | ≥ −0,005 | PASSA |
| (2) Superioridade: golden_v3_novo | LS Δquebras = 0,611111; média = -1,222222 | LS < 0 em pelo menos uma; média ≤ 0 na outra | LS ≥ 0 |
| (2) Superioridade: teste_silver | LS Δquebras = -0,315789; média = -1,370787 | LS < 0 em pelo menos uma; média ≤ 0 na outra | LS < 0 |
| (2) Condição conjunta de superioridade | uma LS < 0 e média da outra ≤ 0 | obrigatória | PASSA |

Robustez: Δ por veículo, regressões graves e deslocamentos são reportados abaixo e não mudam o critério.

## golden_v4 — ajuste

44 páginas; 27 veículos. Cobertura mínima de palavras: 100,0%.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,985948 | 6,045455 | 11,884752 | 0,948129 | 0,927240 |
| hibrido67 | 0,979738 | 5,136364 | 6,041242 | 0,973419 | 0,966143 |
| grafo_K24_maxregret_t0.00 | 0,937961 | 3,613636 | 7,777795 | 0,963953 | 0,955269 |
| hier1 | 0,985445 | 4,659091 | 8,877056 | 0,957802 | 0,946650 |

### Δ contra controles, IC95 e Wilcoxon por veículo

M/I/P = páginas melhores/iguais/piores, no sentido de cada métrica; Δ = método − base.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
| hibrido67 | regra | tau | -0,006211 [-0,033051; 0,009968] | 0,127972 | 16/24/4 |
| hibrido67 | regra | quebras | -0,909091 [-1,775567; -0,095238] | 0,022323 | 16/24/4 |
| hibrido67 | regra | quebras_mil | -5,843509 [-14,066405; -0,457171] | 0,040740 | 16/24/4 |
| hibrido67 | regra | fid12 | 0,025290 [0,000783; 0,063276] | 0,136481 | 14/25/5 |
| hibrido67 | regra | sucessor_linhas | 0,038903 [0,004194; 0,092315] | 0,031875 | 16/24/4 |
| grafo_K24_maxregret_t0.00 | regra | tau | -0,047987 [-0,147284; 0,003696] | 0,512256 | 16/19/9 |
| grafo_K24_maxregret_t0.00 | regra | quebras | -2,431818 [-4,139535; -1,162668] | 0,000513 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | -4,106956 [-8,299765; -1,291931] | 0,001055 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 0,015824 [0,006260; 0,026694] | 0,002085 | 19/23/2 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 0,028029 [0,008366; 0,056655] | 0,000835 | 21/21/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | -0,041776 [-0,143114; 0,021494] | 0,932963 | 16/9/19 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | -1,522727 [-3,500000; -0,074869] | 0,069212 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | 1,736553 [-1,856740; 6,157636] | 0,952089 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | -0,009466 [-0,039952; 0,013016] | 0,923364 | 18/11/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | -0,010874 [-0,038913; 0,012273] | 0,971242 | 17/10/17 |
| hier1 | regra | tau | -0,000503 [-0,001353; 0,000093] | 0,872338 | 11/23/10 |
| hier1 | regra | quebras | -1,386364 [-2,210582; -0,666477] | 0,004672 | 15/27/2 |
| hier1 | regra | quebras_mil | -3,007696 [-6,326180; -0,756479] | 0,005087 | 15/27/2 |
| hier1 | regra | fid12 | 0,009674 [0,004038; 0,015720] | 0,002260 | 15/26/3 |
| hier1 | regra | sucessor_linhas | 0,019410 [0,003751; 0,042196] | 0,006435 | 15/27/2 |
| hier1 | hibrido67 | tau | 0,005708 [-0,010725; 0,032878] | 0,569810 | 11/15/18 |
| hier1 | hibrido67 | quebras | -0,477273 [-1,534926; 0,428641] | 0,282800 | 12/17/15 |
| hier1 | hibrido67 | quebras_mil | 2,835813 [-0,924927; 7,942034] | 0,715805 | 12/17/15 |
| hier1 | hibrido67 | fid12 | -0,015616 [-0,049735; 0,007679] | 0,837129 | 14/15/15 |
| hier1 | hibrido67 | sucessor_linhas | -0,019493 [-0,051946; 0,005592] | 0,437344 | 12/17/15 |

### HIER-1 por veículo

| Veículo | Páginas | Δτ vs regra | Δquebras vs regra | Δτ vs híbrido | Δquebras vs híbrido |
|---|---:|---:|---:|---:|---:|
| official_diary_MG_congonhas | 2 | -0,006819 | 0,000000 | -0,007304 | 2,500000 |
| official_diary_RJ_barra_do_pirai | 3 | -0,003555 | -2,666667 | -0,033763 | 3,000000 |
| official_diary_RJ_duque_de_caxias | 2 | 0,000051 | -3,000000 | -0,067958 | -2,500000 |
| official_diary_RJ_seropedica | 2 | -0,000468 | 0,000000 | -0,000769 | 0,500000 |
| official_diary_RJ_volta_redonda | 1 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ac | 2 | 0,000238 | -1,000000 | 0,000181 | 0,000000 |
| official_diary_al | 3 | 0,000000 | 0,000000 | 0,016007 | 0,666667 |
| official_diary_am_manaus | 1 | 0,000000 | 0,000000 | 0,008900 | -3,000000 |
| official_diary_ap | 2 | -0,000071 | 1,000000 | -0,000071 | 1,000000 |
| official_diary_ba_salvador | 1 | -0,000041 | 2,000000 | 0,447940 | -4,000000 |
| official_diary_ce | 1 | 0,000000 | 0,000000 | -0,000061 | 2,000000 |
| official_diary_ma | 1 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_mg | 1 | 0,000010 | -9,000000 | 0,000010 | -9,000000 |
| official_diary_ms | 2 | 0,000568 | -1,000000 | 0,000000 | 0,000000 |
| official_diary_pb | 2 | 0,000615 | -4,000000 | 0,000607 | -4,500000 |
| official_diary_pe | 1 | 0,000002 | -3,000000 | 0,000002 | -3,000000 |
| official_diary_pi_v2 | 2 | 0,000000 | 0,000000 | -0,000581 | 2,000000 |
| official_diary_pr_curitiba | 1 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_rj | 1 | -0,000001 | -7,000000 | -0,000001 | -7,000000 |
| official_diary_rj_japeri | 2 | -0,000026 | -4,000000 | -0,003163 | -3,000000 |
| official_diary_rn | 1 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ro | 2 | 0,000159 | -3,000000 | -0,000079 | 1,500000 |
| official_diary_rr | 1 | 0,000000 | 0,000000 | -0,000328 | 2,000000 |
| official_diary_rs_porto_alegre | 2 | 0,000100 | -1,500000 | 0,003174 | -1,000000 |
| official_diary_sc | 1 | 0,000006 | -3,000000 | 0,000006 | -3,000000 |
| official_diary_se | 2 | -0,000070 | 0,000000 | -0,000070 | 0,000000 |
| official_diary_to | 2 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |

### Regressões graves do HIER-1: Δτ < −0,1 vs híbrido

1 páginas. Colunas = número de cortes globais do contexto original + 1 (proxy geométrica do E004; segmentos locais não equivalem a colunas).

| Página | Δτ | Unidades | Colunas | Segmentos |
|---|---:|---:|---:|---:|
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | -0,136019 | 23 | 2 | 10 |

### Reparos e regressões de sucessores

Contagem de arestas-ouro de linhas: errado→certo / certo→errado. Classes importadas, sem reinterpretar erros como causas.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 33 | 0 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 11 | 1 |
| grafo_K24_maxregret_t0.00 | regra | margem | 51 | 4 |
| grafo_K24_maxregret_t0.00 | regra | outro | 17 | 1 |
| grafo_K24_maxregret_t0.00 | regra | TOTAL | 112 | 7 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 30 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 11 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 11 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 45 | 35 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 10 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | TOTAL | 107 | 44 |
| hier1 | regra | mesma_coluna | 21 | 0 |
| hier1 | regra | proxima_coluna | 0 | 0 |
| hier1 | regra | tabela_imagem | 0 | 2 |
| hier1 | regra | transversal | 1 | 0 |
| hier1 | regra | margem | 26 | 3 |
| hier1 | regra | outro | 16 | 1 |
| hier1 | regra | TOTAL | 64 | 6 |
| hier1 | hibrido67 | mesma_coluna | 18 | 3 |
| hier1 | hibrido67 | proxima_coluna | 0 | 0 |
| hier1 | hibrido67 | tabela_imagem | 11 | 3 |
| hier1 | hibrido67 | transversal | 1 | 0 |
| hier1 | hibrido67 | margem | 22 | 36 |
| hier1 | hibrido67 | outro | 9 | 3 |
| hier1 | hibrido67 | TOTAL | 61 | 45 |

### Deslocamentos do HIER-1 em relação ao híbrido

Deslocamento absoluto em posições de unidade, todas as unidades/páginas: 240/3729 unidades mudam de posição; mediana 0,00, p90 0,00, máximo 36. Diagnóstico contra a ordem do híbrido, não contra o ouro; não decide o GO.

### Corpo sem margens — sensibilidade

Mesma projeção automática importada do E014 em todos os métodos; não seleciona páginas nem altera o veredito.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,993467 | 2,931818 | 0,985674 | 0,977845 |
| hibrido67 | 0,986295 | 2,772727 | 0,988822 | 0,985116 |
| grafo_K24_maxregret_t0.00 | 0,940957 | 1,568182 | 0,990664 | 0,985138 |
| hier1 | 0,993136 | 2,045455 | 0,990866 | 0,984768 |

## golden_v3_novo — externa

27 páginas; 10 veículos. Cobertura mínima de palavras: 100,0%.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,959557 | 9,222222 | 17,205754 | 0,928415 | 0,911301 |
| hibrido67 | 0,958977 | 7,888889 | 13,739464 | 0,941220 | 0,938410 |
| grafo_K24_maxregret_t0.00 | 0,941737 | 6,518519 | 12,941742 | 0,941194 | 0,935275 |
| hier1 | 0,959414 | 6,666667 | 12,907910 | 0,941063 | 0,934657 |

### Δ contra controles, IC95 e Wilcoxon por veículo

M/I/P = páginas melhores/iguais/piores, no sentido de cada métrica; Δ = método − base.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
| hibrido67 | regra | tau | -0,000580 [-0,004980; 0,005062] | 0,151855 | 8/17/2 |
| hibrido67 | regra | quebras | -1,333333 [-2,648682; -0,363636] | 0,027670 | 7/18/2 |
| hibrido67 | regra | quebras_mil | -3,466289 [-9,191916; -0,665607] | 0,027670 | 7/18/2 |
| hibrido67 | regra | fid12 | 0,012805 [0,003514; 0,028351] | 0,016924 | 8/17/2 |
| hibrido67 | regra | sucessor_linhas | 0,027108 [0,006827; 0,061825] | 0,027670 | 7/18/2 |
| grafo_K24_maxregret_t0.00 | regra | tau | -0,017820 [-0,052402; 0,001460] | 0,721277 | 10/11/6 |
| grafo_K24_maxregret_t0.00 | regra | quebras | -2,703704 [-3,263158; -2,153750] | 0,005698 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | -4,264012 [-7,004880; -2,758572] | 0,005857 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 0,012779 [0,005176; 0,017981] | 0,102470 | 11/12/4 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 0,023974 [0,009214; 0,040091] | 0,074462 | 13/11/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | -0,017240 [-0,052709; 0,004620] | 0,307434 | 6/11/10 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | -1,370370 [-2,558824; 0,230769] | 0,258449 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | -0,797723 [-2,973005; 2,672809] | 0,681519 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | -0,000026 [-0,018935; 0,009917] | 0,474959 | 8/11/8 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | -0,003134 [-0,030139; 0,010360] | 0,759463 | 9/12/6 |
| hier1 | regra | tau | -0,000143 [-0,001269; 0,001213] | 0,507624 | 11/12/4 |
| hier1 | regra | quebras | -2,555556 [-3,000000; -1,833333] | 0,007561 | 12/14/1 |
| hier1 | regra | quebras_mil | -4,297843 [-6,906327; -2,633732] | 0,007641 | 12/14/1 |
| hier1 | regra | fid12 | 0,012648 [0,003723; 0,017539] | 0,184573 | 10/13/4 |
| hier1 | regra | sucessor_linhas | 0,023356 [0,007630; 0,038752] | 0,082731 | 12/13/2 |
| hier1 | hibrido67 | tau | 0,000437 [-0,004394; 0,004950] | 0,414216 | 8/12/7 |
| hier1 | hibrido67 | quebras | -1,222222 [-2,428571; 0,611111] | 0,472352 | 9/14/4 |
| hier1 | hibrido67 | quebras_mil | -0,831554 [-3,137251; 2,963609] | 0,837419 | 9/14/4 |
| hier1 | hibrido67 | fid12 | -0,000157 [-0,020519; 0,010242] | 0,307434 | 8/12/7 |
| hier1 | hibrido67 | sucessor_linhas | -0,003752 [-0,033034; 0,010485] | 0,474959 | 9/13/5 |

### HIER-1 por veículo

| Veículo | Páginas | Δτ vs regra | Δquebras vs regra | Δτ vs híbrido | Δquebras vs híbrido |
|---|---:|---:|---:|---:|---:|
| official_diary_RJ_barra_do_pirai | 1 | 0,000679 | -4,000000 | 0,000679 | -4,000000 |
| official_diary_ac | 2 | 0,005043 | -1,500000 | -0,012428 | 1,000000 |
| official_diary_ap | 1 | -0,005388 | 0,000000 | -0,005388 | 0,000000 |
| official_diary_ce | 6 | 0,000106 | -2,833333 | 0,009416 | -0,166667 |
| official_diary_ma | 7 | 0,000024 | -2,571429 | 0,000024 | -2,571429 |
| official_diary_mg | 1 | 0,000215 | -4,000000 | 0,000215 | -4,000000 |
| official_diary_pi_v2 | 2 | 0,000007 | -1,500000 | -0,000367 | 2,000000 |
| official_diary_rj | 5 | -0,002089 | -3,400000 | -0,002091 | -3,400000 |
| official_diary_ro | 1 | 0,000194 | -3,000000 | 0,000000 | 0,000000 |
| official_diary_se | 1 | -0,000025 | 0,000000 | -0,004324 | 5,000000 |

### Regressões graves do HIER-1: Δτ < −0,1 vs híbrido

0 páginas. Colunas = número de cortes globais do contexto original + 1 (proxy geométrica do E004; segmentos locais não equivalem a colunas).

| Página | Δτ | Unidades | Colunas | Segmentos |
|---|---:|---:|---:|---:|

### Reparos e regressões de sucessores

Contagem de arestas-ouro de linhas: errado→certo / certo→errado. Classes importadas, sem reinterpretar erros como causas.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 32 | 3 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 3 | 2 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | margem | 11 | 3 |
| grafo_K24_maxregret_t0.00 | regra | outro | 32 | 2 |
| grafo_K24_maxregret_t0.00 | regra | TOTAL | 78 | 11 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 25 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 3 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 7 | 5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 16 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | TOTAL | 51 | 18 |
| hier1 | regra | mesma_coluna | 31 | 1 |
| hier1 | regra | proxima_coluna | 0 | 1 |
| hier1 | regra | tabela_imagem | 3 | 2 |
| hier1 | regra | transversal | 0 | 0 |
| hier1 | regra | margem | 4 | 2 |
| hier1 | regra | outro | 32 | 1 |
| hier1 | regra | TOTAL | 70 | 7 |
| hier1 | hibrido67 | mesma_coluna | 24 | 4 |
| hier1 | hibrido67 | proxima_coluna | 0 | 1 |
| hier1 | hibrido67 | tabela_imagem | 3 | 3 |
| hier1 | hibrido67 | transversal | 0 | 0 |
| hier1 | hibrido67 | margem | 4 | 8 |
| hier1 | hibrido67 | outro | 16 | 2 |
| hier1 | hibrido67 | TOTAL | 47 | 18 |

### Deslocamentos do HIER-1 em relação ao híbrido

Deslocamento absoluto em posições de unidade, todas as unidades/páginas: 155/2258 unidades mudam de posição; mediana 0,00, p90 0,00, máximo 23. Diagnóstico contra a ordem do híbrido, não contra o ouro; não decide o GO.

### Corpo sem margens — sensibilidade

Mesma projeção automática importada do E014 em todos os métodos; não seleciona páginas nem altera o veredito.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,959496 | 7,703704 | 0,936030 | 0,925058 |
| hibrido67 | 0,960716 | 6,555556 | 0,947488 | 0,949111 |
| grafo_K24_maxregret_t0.00 | 0,940307 | 5,370370 | 0,947788 | 0,943730 |
| hier1 | 0,959046 | 5,296296 | 0,948560 | 0,944609 |

## teste_silver — externa

89 páginas; 3 veículos. Cobertura mínima de palavras: 100,0%.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,959565 | 27,449438 | 44,495551 | 0,825401 | 0,840212 |
| hibrido67 | 0,959092 | 26,426966 | 43,157243 | 0,834332 | 0,849525 |
| grafo_K24_maxregret_t0.00 | 0,942613 | 24,146067 | 41,817015 | 0,838883 | 0,854450 |
| hier1 | 0,958401 | 25,056180 | 42,248135 | 0,835886 | 0,853424 |

### Δ contra controles, IC95 e Wilcoxon por veículo

M/I/P = páginas melhores/iguais/piores, no sentido de cada métrica; Δ = método − base.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
| hibrido67 | regra | tau | -0,000473 [-0,001598; 0,000483] | 1,000000 | 16/66/7 |
| hibrido67 | regra | quebras | -1,022472 [-1,894737; -0,076923] | 0,108809 | 14/72/3 |
| hibrido67 | regra | quebras_mil | -1,338308 [-1,847069; -0,051975] | 0,108809 | 14/72/3 |
| hibrido67 | regra | fid12 | 0,008931 [0,000277; 0,010450] | 0,108809 | 15/74/0 |
| hibrido67 | regra | sucessor_linhas | 0,009313 [0,000078; 0,011315] | 0,108809 | 14/72/3 |
| grafo_K24_maxregret_t0.00 | regra | tau | -0,016953 [-0,043074; -0,000940] | 0,108809 | 21/53/15 |
| grafo_K24_maxregret_t0.00 | regra | quebras | -3,303371 [-11,384615; -0,815789] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | -2,678536 [-5,533066; -1,488111] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 0,013482 [0,003029; 0,036290] | 0,108809 | 28/57/4 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 0,014239 [0,006451; 0,022996] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | -0,016479 [-0,043095; 0,000658] | 0,285049 | 21/43/25 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | -2,280899 [-11,307692; -0,342105] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | -1,340228 [-5,481091; -0,218504] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 0,004550 [-0,007345; 0,036013] | 0,592980 | 20/54/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 0,004926 [-0,004019; 0,022918] | 0,285049 | 25/50/14 |
| hier1 | regra | tau | -0,001165 [-0,001975; -0,000524] | 0,108809 | 25/57/7 |
| hier1 | regra | quebras | -2,393258 [-5,153846; -0,789474] | 0,108809 | 31/58/0 |
| hier1 | regra | quebras_mil | -2,247415 [-2,924060; -1,408316] | 0,108809 | 31/58/0 |
| hier1 | regra | fid12 | 0,010486 [0,003054; 0,016327] | 0,108809 | 28/60/1 |
| hier1 | regra | sucessor_linhas | 0,013213 [0,006515; 0,019151] | 0,108809 | 31/58/0 |
| hier1 | hibrido67 | tau | -0,000691 [-0,002458; 0,001074] | 0,592980 | 24/47/18 |
| hier1 | hibrido67 | quebras | -1,370787 [-5,076923; -0,315789] | 0,108809 | 25/53/11 |
| hier1 | hibrido67 | quebras_mil | -0,909108 [-2,670308; -0,138709] | 0,108809 | 25/53/11 |
| hier1 | hibrido67 | fid12 | 0,001554 [-0,007320; 0,014857] | 0,592980 | 20/57/12 |
| hier1 | hibrido67 | sucessor_linhas | 0,003900 [-0,003955; 0,015354] | 0,285049 | 25/53/11 |

### HIER-1 por veículo

| Veículo | Páginas | Δτ vs regra | Δquebras vs regra | Δτ vs híbrido | Δquebras vs híbrido |
|---|---:|---:|---:|---:|---:|
| official_diary_ce | 38 | -0,000524 | -3,052632 | 0,001074 | -1,157895 |
| official_diary_ma | 38 | -0,001975 | -0,789474 | -0,002458 | -0,315789 |
| official_diary_rj | 13 | -0,000668 | -5,153846 | -0,000688 | -5,076923 |

### Regressões graves do HIER-1: Δτ < −0,1 vs híbrido

1 páginas. Colunas = número de cortes globais do contexto original + 1 (proxy geométrica do E004; segmentos locais não equivalem a colunas).

| Página | Δτ | Unidades | Colunas | Segmentos |
|---|---:|---:|---:|---:|
| `official_diary_ma/executive_official_diary_2023-03-06.pdf#p34` | -0,100490 | 37 | 2 | 5 |

### Reparos e regressões de sucessores

Contagem de arestas-ouro de linhas: errado→certo / certo→errado. Classes importadas, sem reinterpretar erros como causas.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 114 | 5 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 3 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 6 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 39 | 1 |
| grafo_K24_maxregret_t0.00 | regra | margem | 3 | 1 |
| grafo_K24_maxregret_t0.00 | regra | outro | 153 | 11 |
| grafo_K24_maxregret_t0.00 | regra | TOTAL | 315 | 21 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 98 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 4 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 6 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 37 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 12 | 20 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 103 | 17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | TOTAL | 256 | 53 |
| hier1 | regra | mesma_coluna | 78 | 5 |
| hier1 | regra | proxima_coluna | 0 | 0 |
| hier1 | regra | tabela_imagem | 0 | 0 |
| hier1 | regra | transversal | 1 | 0 |
| hier1 | regra | margem | 0 | 0 |
| hier1 | regra | outro | 149 | 10 |
| hier1 | regra | TOTAL | 228 | 15 |
| hier1 | hibrido67 | mesma_coluna | 62 | 6 |
| hier1 | hibrido67 | proxima_coluna | 0 | 1 |
| hier1 | hibrido67 | tabela_imagem | 0 | 0 |
| hier1 | hibrido67 | transversal | 0 | 6 |
| hier1 | hibrido67 | margem | 9 | 19 |
| hier1 | hibrido67 | outro | 99 | 16 |
| hier1 | hibrido67 | TOTAL | 170 | 48 |

### Deslocamentos do HIER-1 em relação ao híbrido

Deslocamento absoluto em posições de unidade, todas as unidades/páginas: 717/8942 unidades mudam de posição; mediana 0,00, p90 0,00, máximo 75. Diagnóstico contra a ordem do híbrido, não contra o ouro; não decide o GO.

### Corpo sem margens — sensibilidade

Mesma projeção automática importada do E014 em todos os métodos; não seleciona páginas nem altera o veredito.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,958613 | 24,404494 | 0,837730 | 0,854708 |
| hibrido67 | 0,959083 | 23,494382 | 0,846454 | 0,863272 |
| grafo_K24_maxregret_t0.00 | 0,941542 | 21,123596 | 0,852052 | 0,869266 |
| hier1 | 0,957369 | 22,011236 | 0,848749 | 0,868258 |

## validacao_silver — apêndice de ajuste RN

15 páginas; 1 veículos. Cobertura mínima de palavras: 100,0%.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,957218 | 16,666667 | 10,284740 | 0,952328 | 0,910859 |
| hibrido67 | 0,958656 | 16,400000 | 9,585398 | 0,957104 | 0,916949 |
| grafo_K24_maxregret_t0.00 | 0,686666 | 9,466667 | 6,131847 | 0,970249 | 0,947916 |
| hier1 | 0,956778 | 12,133333 | 7,622965 | 0,961153 | 0,934895 |

### Δ contra controles, IC95 e Wilcoxon por veículo

M/I/P = páginas melhores/iguais/piores, no sentido de cada métrica; Δ = método − base.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
| hibrido67 | regra | tau | 0,001439 [0,001439; 0,001439] | 0,317311 | 1/13/1 |
| hibrido67 | regra | quebras | -0,266667 [-0,266667; -0,266667] | 0,317311 | 2/13/0 |
| hibrido67 | regra | quebras_mil | -0,699342 [-0,699342; -0,699342] | 0,317311 | 2/13/0 |
| hibrido67 | regra | fid12 | 0,004776 [0,004776; 0,004776] | 0,317311 | 2/13/0 |
| hibrido67 | regra | sucessor_linhas | 0,006090 [0,006090; 0,006090] | 0,317311 | 2/13/0 |
| grafo_K24_maxregret_t0.00 | regra | tau | -0,270551 [-0,270551; -0,270551] | 0,317311 | 3/4/8 |
| grafo_K24_maxregret_t0.00 | regra | quebras | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | -4,152893 [-4,152893; -4,152893] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 0,017921 [0,017921; 0,017921] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 0,037057 [0,037057; 0,037057] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | -0,271990 [-0,271990; -0,271990] | 0,317311 | 3/4/8 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | -6,933333 [-6,933333; -6,933333] | 0,317311 | 9/4/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | -3,453551 [-3,453551; -3,453551] | 0,317311 | 9/4/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 0,013145 [0,013145; 0,013145] | 0,317311 | 9/4/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 0,030967 [0,030967; 0,030967] | 0,317311 | 9/4/2 |
| hier1 | regra | tau | -0,000440 [-0,000440; -0,000440] | 0,317311 | 5/5/5 |
| hier1 | regra | quebras | -4,533333 [-4,533333; -4,533333] | 0,317311 | 5/10/0 |
| hier1 | regra | quebras_mil | -2,661775 [-2,661775; -2,661775] | 0,317311 | 5/10/0 |
| hier1 | regra | fid12 | 0,008825 [0,008825; 0,008825] | 0,317311 | 5/9/1 |
| hier1 | regra | sucessor_linhas | 0,024036 [0,024036; 0,024036] | 0,317311 | 5/10/0 |
| hier1 | hibrido67 | tau | -0,001879 [-0,001879; -0,001879] | 0,317311 | 6/4/5 |
| hier1 | hibrido67 | quebras | -4,266667 [-4,266667; -4,266667] | 0,317311 | 4/9/2 |
| hier1 | hibrido67 | quebras_mil | -1,962433 [-1,962433; -1,962433] | 0,317311 | 4/9/2 |
| hier1 | hibrido67 | fid12 | 0,004049 [0,004049; 0,004049] | 0,317311 | 4/8/3 |
| hier1 | hibrido67 | sucessor_linhas | 0,017946 [0,017946; 0,017946] | 0,317311 | 4/9/2 |

### HIER-1 por veículo

| Veículo | Páginas | Δτ vs regra | Δquebras vs regra | Δτ vs híbrido | Δquebras vs híbrido |
|---|---:|---:|---:|---:|---:|
| official_diary_rn | 15 | -0,000440 | -4,533333 | -0,001879 | -4,266667 |

### Regressões graves do HIER-1: Δτ < −0,1 vs híbrido

0 páginas. Colunas = número de cortes globais do contexto original + 1 (proxy geométrica do E004; segmentos locais não equivalem a colunas).

| Página | Δτ | Unidades | Colunas | Segmentos |
|---|---:|---:|---:|---:|

### Reparos e regressões de sucessores

Contagem de arestas-ouro de linhas: errado→certo / certo→errado. Classes importadas, sem reinterpretar erros como causas.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 17 | 0 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 1 | 0 |
| grafo_K24_maxregret_t0.00 | regra | margem | 38 | 0 |
| grafo_K24_maxregret_t0.00 | regra | outro | 53 | 1 |
| grafo_K24_maxregret_t0.00 | regra | TOTAL | 109 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 17 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 1 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 36 | 2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 53 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | TOTAL | 107 | 3 |
| hier1 | regra | mesma_coluna | 14 | 0 |
| hier1 | regra | proxima_coluna | 0 | 1 |
| hier1 | regra | tabela_imagem | 0 | 0 |
| hier1 | regra | transversal | 0 | 0 |
| hier1 | regra | margem | 4 | 1 |
| hier1 | regra | outro | 53 | 1 |
| hier1 | regra | TOTAL | 71 | 3 |
| hier1 | hibrido67 | mesma_coluna | 14 | 0 |
| hier1 | hibrido67 | proxima_coluna | 0 | 1 |
| hier1 | hibrido67 | tabela_imagem | 0 | 0 |
| hier1 | hibrido67 | transversal | 0 | 0 |
| hier1 | hibrido67 | margem | 3 | 4 |
| hier1 | hibrido67 | outro | 53 | 1 |
| hier1 | hibrido67 | TOTAL | 70 | 6 |

### Deslocamentos do HIER-1 em relação ao híbrido

Deslocamento absoluto em posições de unidade, todas as unidades/páginas: 300/2566 unidades mudam de posição; mediana 0,00, p90 1,00, máximo 83. Diagnóstico contra a ordem do híbrido, não contra o ouro; não decide o GO.

### Corpo sem margens — sensibilidade

Mesma projeção automática importada do E014 em todos os métodos; não seleciona páginas nem altera o veredito.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,977603 | 11,200000 | 0,972619 | 0,945747 |
| hibrido67 | 0,977564 | 11,200000 | 0,972619 | 0,945747 |
| grafo_K24_maxregret_t0.00 | 0,684942 | 6,933333 | 0,977618 | 0,965229 |
| hier1 | 0,977235 | 6,933333 | 0,979887 | 0,967341 |

## Limitações

Avaliação exploratória externa de uma hipótese motivada pelo ajuste do E016; não apaga seu NÃO GO. golden_v3_novo já foi consultado em rodadas anteriores e não é teste confirmatório. Uma anotação humana por página, silver ruidoso e seleção histórica dos veículos por concordância com heurística. Poucos veículos no teste silver tornam o IC discreto; RN tem um único veículo e IC degenerado. As médias são por página, não a macro-UF confirmatória do teste cego. Cobertura integral significa preservar as palavras digitais disponíveis, não comprovar ausência de falhas de OCR/extração. Segmentos geométricos podem impedir ordens humanas que reentram neles; colunas são uma proxy automática. O modelo treinado é o checkpoint já selecionado do E004, sem novas sementes ou treino. Nenhuma decisão foi tomada por p-valor, por diagnóstico de regressões ou por corpo sem margens. Nenhuma página/PDF lacrado, anotação original ou dado do parceiro foi aberto; nenhuma escrita em data/, documentação, cartão ou registro compartilhado. O teste cego permanece reservado ao orquestrador.
