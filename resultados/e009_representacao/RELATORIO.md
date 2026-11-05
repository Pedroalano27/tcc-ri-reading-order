# E009 — caixas automáticas × linhas automáticas

1. Âncora reproduzida: τ 0,985948; 6,045455 quebras/página no golden_v4.
2. Páginas pareadas: golden_v4 44; golden_v3_novo 27; teste_silver 89.
3. Δ B − A com regra: v4 0,568182 [-2,926914; 3,209302]; v3 novo -1,777778 [-3,642857; 0,722500].
4. Δ B − A com híbrido 67: v4 0,386364 [-3,289053; 3,270332]; v3 novo -1,074074 [-3,950000; 1,766944].
5. Cobertura final: golden_v4 A/B 100,00%/100,00%; golden_v3_novo A/B 100,00%/100,00%; teste_silver A/B 100,00%/100,00%.
6. Histórico reproduzido na definição antiga: 213 → 29; na atual: 213 → 31 quebras internas.

**Veredito pelo cartão: CRITÉRIO NÃO ATINGIDO.**

Os critérios são aplicados sem alteração: Δ quebras < 0 e limite superior do IC95 < 0 em cada bancada humana e ordenador, com cobertura de B ≥ A. Não há critério de abandono: trata-se de medição de base.

Este E009 não sustenta a justificativa de superioridade da representação simplificada em quebras totais com ordenador fixo. O piso interno menor não basta para concluir melhor ordenação; custo e qualidade da anotação ainda dependem do E008.

## Representações e controle

A = caixas automáticas do pipeline de outubro P1/P1m: `propor(regras=True)`, Docling Heron + blocos automáticos v3. Não são caixas humanas nem um detector puro de parágrafos. Nas bancadas humanas reutilizam-se as unidades congeladas de `erros_ponta_a_ponta.json`; no silver, a mesma receita recebe palavras canônicas e cache Heron. B = `linhas` exportadas em `resultados/unidades_sem_caixas/`, incluindo átomos ls3. O ls3 ignora suas caixas de texto em B. A comparação caracteriza estes dois pipelines de representação; a origem dos átomos também difere, portanto não isola apenas o tamanho da unidade.

Cada unidade guarda os IDs de palavra em `cache/paginas/`. Antes de ordenar, órfãs de A viram linhas com `ordem_sem_bbox.linhas()`. A posse é exclusiva; cobertura por atribuição e sobreposição geométrica são diagnósticos distintos. Toda palavra disponível, inclusive fora do ouro, permanece exatamente uma vez nas duas saídas. A cobertura é da camada digital, não de texto em imagem sem OCR.

Os ordenadores são os mesmos `bancada_ordenadores.prever`: regra de colunas e LayoutReader pronto até 67 unidades, regra acima. O limiar é aplicado ao número de unidades de cada representação, incluindo vazias/fallback. Isso conserva a política, mas pode mudar a rota ao mudar a representação. O híbrido se aplica a caixas pela interface genérica do adaptador; não se retreina nem se escolhe limiar. Expansão interna sempre `ordem_sem_bbox.fluxo()`. Entrada `random.Random(f'entrada-{page_id}')` via protocolo/adaptador.

Nenhum detector executado (CPU ou GPU); LayoutReader apenas em CPU/float32, no máximo quatro threads, um processo e zero workers. Predições de caixas ausentes: golden_v4: 0; golden_v3_novo: 0; teste_silver: 0.

## golden_v4

44 páginas, 27 veículos. Médias por página; IC95 agrupado por veículo.

| Representação/ordenador | τ palavras | Quebras/página | Dentro de unidades/página | Entre unidades/página | Fidelidade 12 | Sucessor linhas | Quebras/mil |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_regra | 0,980001 | 5,477273 | 1,590909 | 3,886364 | 0,938305 | 0,929628 | 13,578986 |
| A_hibrido67 | 0,965834 | 4,750000 | 1,590909 | 3,159091 | 0,970124 | 0,963980 | 8,072459 |
| B_regra | 0,985948 | 6,045455 | 0,545455 | 5,500000 | 0,948129 | 0,927240 | 11,884752 |
| B_hibrido67 | 0,979738 | 5,136364 | 0,545455 | 4,590909 | 0,973419 | 0,966143 | 6,041242 |

| Cobertura ouro | N palavras | Cobertas % | Duplicadas % | Órfãs % | Múltiplas caixas geométricas |
|---|---:|---:|---:|---:|---:|
| A/antes_fallback | 36171 | 100,000000 | 0,000000 | 0,000000 | 122 |
| A/final | 36171 | 100,000000 | 0,000000 | 0,000000 | 122 |
| B/antes_fallback | 36171 | 100,000000 | 0,000000 | 0,000000 | 66 |
| B/final | 36171 | 100,000000 | 0,000000 | 0,000000 | 66 |

| Contraste | Métrica | Δ [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior |
|---|---|---:|---:|---:|
| B-A_regra | tau | 0,005947 [-0,004953; 0,024159] | 0,224567 | 10/16/18 |
| B-A_regra | quebras | 0,568182 [-2,926914; 3,209302] | 0,023087 | 5/18/21 |
| B-A_regra | quebras_mil | -1,694235 [-11,826416; 5,106216] | 0,081357 | 5/18/21 |
| B-A_regra | fid12 | 0,009823 [-0,013945; 0,040510] | 0,131327 | 7/17/20 |
| B-A_regra | sucessor_linhas | -0,002388 [-0,028358; 0,025464] | 0,253925 | 7/17/20 |
| B-A_regra | piso_interno | -1,045455 [-4,619269; 1,000000] | 0,265129 | 2/36/6 |
| B-A_regra | entre_unidades | 1,613636 [0,611077; 2,725057] | 0,004126 | 4/19/21 |
| B-A_hibrido67 | tau | 0,013903 [-0,020302; 0,044735] | 0,941679 | 11/19/14 |
| B-A_hibrido67 | quebras | 0,386364 [-3,289053; 3,270332] | 0,078827 | 7/19/18 |
| B-A_hibrido67 | quebras_mil | -2,031217 [-11,570904; 3,731050] | 0,112937 | 7/19/18 |
| B-A_hibrido67 | fid12 | 0,003294 [-0,012951; 0,024217] | 0,112937 | 9/19/16 |
| B-A_hibrido67 | sucessor_linhas | 0,002163 [-0,016498; 0,026059] | 0,241777 | 8/20/16 |
| B-A_hibrido67 | piso_interno | -1,045455 [-4,619269; 1,000000] | 0,265129 | 2/36/6 |
| B-A_hibrido67 | entre_unidades | 1,431818 [0,297872; 2,805655] | 0,026268 | 7/18/19 |
| A_regra-B_regra | tau | -0,005947 [-0,024159; 0,004953] | 0,224567 | 18/16/10 |
| A_regra-B_regra | quebras | -0,568182 [-3,209302; 2,926914] | 0,023087 | 21/18/5 |
| A_regra-B_regra | quebras_mil | 1,694235 [-5,106216; 11,826416] | 0,081357 | 21/18/5 |
| A_regra-B_regra | fid12 | -0,009823 [-0,040510; 0,013945] | 0,131327 | 20/17/7 |
| A_regra-B_regra | sucessor_linhas | 0,002388 [-0,025464; 0,028358] | 0,253925 | 20/17/7 |
| A_regra-B_regra | piso_interno | 1,045455 [-1,000000; 4,619269] | 0,265129 | 6/36/2 |
| A_regra-B_regra | entre_unidades | -1,613636 [-2,725057; -0,611077] | 0,004126 | 21/19/4 |
| A_hibrido67-B_regra | tau | -0,020114 [-0,048028; 0,004116] | 0,248350 | 27/7/10 |
| A_hibrido67-B_regra | quebras | -1,295455 [-4,047619; 2,456647] | 0,008314 | 29/7/8 |
| A_hibrido67-B_regra | quebras_mil | -3,812292 [-14,678994; 8,838637] | 0,009395 | 29/7/8 |
| A_hibrido67-B_regra | fid12 | 0,021996 [-0,015696; 0,064007] | 0,013246 | 27/8/9 |
| A_hibrido67-B_regra | sucessor_linhas | 0,036740 [-0,010143; 0,094008] | 0,012380 | 28/7/9 |
| A_hibrido67-B_regra | piso_interno | 1,045455 [-1,000000; 4,619269] | 0,265129 | 6/36/2 |
| A_hibrido67-B_regra | entre_unidades | -2,340909 [-3,707317; -1,095238] | 0,001695 | 30/6/8 |
| B_hibrido67-B_regra | tau | -0,006211 [-0,033051; 0,009968] | 0,127972 | 16/24/4 |
| B_hibrido67-B_regra | quebras | -0,909091 [-1,775567; -0,095238] | 0,022323 | 16/24/4 |
| B_hibrido67-B_regra | quebras_mil | -5,843509 [-14,066405; -0,457171] | 0,040740 | 16/24/4 |
| B_hibrido67-B_regra | fid12 | 0,025290 [0,000783; 0,063276] | 0,136481 | 14/25/5 |
| B_hibrido67-B_regra | sucessor_linhas | 0,038903 [0,004194; 0,092315] | 0,031875 | 16/24/4 |
| B_hibrido67-B_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| B_hibrido67-B_regra | entre_unidades | -0,909091 [-1,775567; -0,095238] | 0,022323 | 16/24/4 |
| A_hibrido67-A_regra | tau | -0,014166 [-0,039759; 0,005338] | 0,213604 | 19/18/7 |
| A_hibrido67-A_regra | quebras | -0,727273 [-1,666667; 0,255332] | 0,101986 | 18/18/8 |
| A_hibrido67-A_regra | quebras_mil | -5,506527 [-12,296684; -0,072682] | 0,067400 | 18/18/8 |
| A_hibrido67-A_regra | fid12 | 0,031819 [-0,001106; 0,072692] | 0,061277 | 17/21/6 |
| A_hibrido67-A_regra | sucessor_linhas | 0,034352 [0,003694; 0,071949] | 0,051065 | 18/18/8 |
| A_hibrido67-A_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| A_hibrido67-A_regra | entre_unidades | -0,727273 [-1,666667; 0,255332] | 0,101986 | 18/18/8 |

| Contraste | Sucessores reparados | Sucessores regredidos |
|---|---:|---:|
| B-A_regra | 96 | 92 |
| B-A_hibrido67 | 122 | 109 |
| A_hibrido67-B_regra | 151 | 122 |
| B_hibrido67-B_regra | 58 | 16 |

| Veículo | Páginas | Δ quebras B − A regra | Δ quebras B − A híbrido 67 |
|---|---:|---:|---:|
| official_diary_MG_congonhas | 2 | 1,500000 | 0,000000 |
| official_diary_RJ_barra_do_pirai | 3 | 1,666667 | 0,000000 |
| official_diary_RJ_duque_de_caxias | 2 | -29,500000 | -30,500000 |
| official_diary_RJ_seropedica | 2 | 4,500000 | 4,500000 |
| official_diary_RJ_volta_redonda | 1 | 0,000000 | 3,000000 |
| official_diary_ac | 2 | -4,500000 | -4,500000 |
| official_diary_al | 3 | 1,666667 | -2,000000 |
| official_diary_am_manaus | 1 | 0,000000 | 3,000000 |
| official_diary_ap | 2 | 3,000000 | 3,000000 |
| official_diary_ba_salvador | 1 | 8,000000 | 13,000000 |
| official_diary_ce | 1 | 0,000000 | 0,000000 |
| official_diary_ma | 1 | 0,000000 | -5,000000 |
| official_diary_mg | 1 | 6,000000 | 6,000000 |
| official_diary_ms | 2 | 0,000000 | -1,000000 |
| official_diary_pb | 2 | 3,500000 | 3,500000 |
| official_diary_pe | 1 | 3,000000 | 3,000000 |
| official_diary_pi_v2 | 2 | 0,000000 | 0,000000 |
| official_diary_pr_curitiba | 1 | 0,000000 | 0,000000 |
| official_diary_rj | 1 | 25,000000 | 25,000000 |
| official_diary_rj_japeri | 2 | 3,500000 | 6,000000 |
| official_diary_rn | 1 | -3,000000 | 0,000000 |
| official_diary_ro | 2 | 0,000000 | 0,000000 |
| official_diary_rr | 1 | 0,000000 | 0,000000 |
| official_diary_rs_porto_alegre | 2 | 0,000000 | 1,000000 |
| official_diary_sc | 1 | 6,000000 | 6,000000 |
| official_diary_se | 2 | 0,000000 | 3,000000 |
| official_diary_to | 2 | 3,000000 | -0,500000 |

Páginas roteadas ao LayoutReader: A_hibrido67: 37; B_hibrido67: 25.

## golden_v3_novo

27 páginas, 10 veículos. Médias por página; IC95 agrupado por veículo.

| Representação/ordenador | τ palavras | Quebras/página | Dentro de unidades/página | Entre unidades/página | Fidelidade 12 | Sucessor linhas | Quebras/mil |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_regra | 0,944567 | 11,000000 | 5,296296 | 5,703704 | 0,920758 | 0,903882 | 19,915853 |
| A_hibrido67 | 0,970338 | 8,962963 | 5,296296 | 3,666667 | 0,938592 | 0,931416 | 16,509711 |
| B_regra | 0,959557 | 9,222222 | 0,259259 | 8,962963 | 0,928415 | 0,911301 | 17,205754 |
| B_hibrido67 | 0,958977 | 7,888889 | 0,259259 | 7,629630 | 0,941220 | 0,938410 | 13,739464 |

| Cobertura ouro | N palavras | Cobertas % | Duplicadas % | Órfãs % | Múltiplas caixas geométricas |
|---|---:|---:|---:|---:|---:|
| A/antes_fallback | 23778 | 100,000000 | 0,000000 | 0,000000 | 125 |
| A/final | 23778 | 100,000000 | 0,000000 | 0,000000 | 125 |
| B/antes_fallback | 23778 | 100,000000 | 0,000000 | 0,000000 | 1 |
| B/final | 23778 | 100,000000 | 0,000000 | 0,000000 | 1 |

| Contraste | Métrica | Δ [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior |
|---|---|---:|---:|---:|
| B-A_regra | tau | 0,014990 [-0,014421; 0,058226] | 0,567938 | 4/9/14 |
| B-A_regra | quebras | -1,777778 [-3,642857; 0,722500] | 0,603395 | 4/16/7 |
| B-A_regra | quebras_mil | -2,710100 [-7,670632; 5,476361] | 0,716290 | 4/16/7 |
| B-A_regra | fid12 | 0,007657 [-0,019476; 0,022246] | 0,490214 | 5/14/8 |
| B-A_regra | sucessor_linhas | 0,007419 [-0,024079; 0,028693] | 0,559342 | 4/17/6 |
| B-A_regra | piso_interno | -5,037037 [-11,363636; 0,000000] | 0,157874 | 4/21/2 |
| B-A_regra | entre_unidades | 3,259259 [-1,437674; 8,466719] | 0,533003 | 4/15/8 |
| B-A_hibrido67 | tau | -0,011360 [-0,040631; 0,029489] | 0,499723 | 7/11/9 |
| B-A_hibrido67 | quebras | -1,074074 [-3,950000; 1,766944] | 0,876228 | 8/11/8 |
| B-A_hibrido67 | quebras_mil | -2,770247 [-9,238542; 5,084315] | 0,958594 | 8/11/8 |
| B-A_hibrido67 | fid12 | 0,002628 [-0,025605; 0,026307] | 0,876228 | 8/11/8 |
| B-A_hibrido67 | sucessor_linhas | 0,006993 [-0,026749; 0,038431] | 0,958594 | 6/11/10 |
| B-A_hibrido67 | piso_interno | -5,037037 [-11,363636; 0,000000] | 0,157874 | 4/21/2 |
| B-A_hibrido67 | entre_unidades | 3,962963 [-0,565217; 7,958617] | 0,275596 | 5/10/12 |
| A_regra-B_regra | tau | -0,014990 [-0,058226; 0,014421] | 0,567938 | 14/9/4 |
| A_regra-B_regra | quebras | 1,777778 [-0,722500; 3,642857] | 0,603395 | 7/16/4 |
| A_regra-B_regra | quebras_mil | 2,710100 [-5,476361; 7,670632] | 0,716290 | 7/16/4 |
| A_regra-B_regra | fid12 | -0,007657 [-0,022246; 0,019476] | 0,490214 | 8/14/5 |
| A_regra-B_regra | sucessor_linhas | -0,007419 [-0,028693; 0,024079] | 0,559342 | 6/17/4 |
| A_regra-B_regra | piso_interno | 5,037037 [0,000000; 11,363636] | 0,157874 | 2/21/4 |
| A_regra-B_regra | entre_unidades | -3,259259 [-8,466719; 1,437674] | 0,533003 | 8/15/4 |
| A_hibrido67-B_regra | tau | 0,010780 [-0,027602; 0,041317] | 0,168807 | 15/4/8 |
| A_hibrido67-B_regra | quebras | -0,259259 [-3,400294; 3,160167] | 0,284503 | 14/5/8 |
| A_hibrido67-B_regra | quebras_mil | -0,696043 [-10,348370; 6,441765] | 0,241121 | 14/5/8 |
| A_hibrido67-B_regra | fid12 | 0,010177 [-0,014751; 0,039961] | 0,139414 | 15/4/8 |
| A_hibrido67-B_regra | sucessor_linhas | 0,020115 [-0,013100; 0,063051] | 0,139414 | 16/5/6 |
| A_hibrido67-B_regra | piso_interno | 5,037037 [0,000000; 11,363636] | 0,157874 | 2/21/4 |
| A_hibrido67-B_regra | entre_unidades | -5,296296 [-8,606061; -1,610833] | 0,046853 | 18/4/5 |
| B_hibrido67-B_regra | tau | -0,000580 [-0,004980; 0,005062] | 0,151855 | 8/17/2 |
| B_hibrido67-B_regra | quebras | -1,333333 [-2,648682; -0,363636] | 0,027670 | 7/18/2 |
| B_hibrido67-B_regra | quebras_mil | -3,466289 [-9,191916; -0,665607] | 0,027670 | 7/18/2 |
| B_hibrido67-B_regra | fid12 | 0,012805 [0,003514; 0,028351] | 0,016924 | 8/17/2 |
| B_hibrido67-B_regra | sucessor_linhas | 0,027108 [0,006827; 0,061825] | 0,027670 | 7/18/2 |
| B_hibrido67-B_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| B_hibrido67-B_regra | entre_unidades | -1,333333 [-2,648682; -0,363636] | 0,027670 | 7/18/2 |
| A_hibrido67-A_regra | tau | 0,025770 [-0,009963; 0,086752] | 0,184573 | 12/6/9 |
| A_hibrido67-A_regra | quebras | -2,037037 [-4,000000; 0,100000] | 0,023629 | 13/7/7 |
| A_hibrido67-A_regra | quebras_mil | -3,406142 [-6,327905; -0,580123] | 0,014306 | 13/7/7 |
| A_hibrido67-A_regra | fid12 | 0,017833 [0,000172; 0,038748] | 0,018904 | 15/6/6 |
| A_hibrido67-A_regra | sucessor_linhas | 0,027534 [0,006038; 0,047475] | 0,014306 | 13/7/7 |
| A_hibrido67-A_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/27/0 |
| A_hibrido67-A_regra | entre_unidades | -2,037037 [-4,000000; 0,100000] | 0,023629 | 13/7/7 |

| Contraste | Sucessores reparados | Sucessores regredidos |
|---|---:|---:|
| B-A_regra | 92 | 53 |
| B-A_hibrido67 | 89 | 71 |
| A_hibrido67-B_regra | 106 | 90 |
| B_hibrido67-B_regra | 39 | 5 |

| Veículo | Páginas | Δ quebras B − A regra | Δ quebras B − A híbrido 67 |
|---|---:|---:|---:|
| official_diary_RJ_barra_do_pirai | 1 | -13,000000 | -8,000000 |
| official_diary_ac | 2 | 0,500000 | -2,000000 |
| official_diary_ap | 1 | 9,000000 | 9,000000 |
| official_diary_ce | 6 | -0,500000 | 0,500000 |
| official_diary_ma | 7 | -4,714286 | -6,142857 |
| official_diary_mg | 1 | 0,000000 | 1,000000 |
| official_diary_pi_v2 | 2 | 1,500000 | 0,000000 |
| official_diary_rj | 5 | -2,400000 | 2,600000 |
| official_diary_ro | 1 | 0,000000 | 0,000000 |
| official_diary_se | 1 | 0,000000 | 0,000000 |

Páginas roteadas ao LayoutReader: A_hibrido67: 27; B_hibrido67: 13.

## teste_silver

89 páginas, 3 veículos. Médias por página; IC95 agrupado por veículo.

| Representação/ordenador | τ palavras | Quebras/página | Dentro de unidades/página | Entre unidades/página | Fidelidade 12 | Sucessor linhas | Quebras/mil |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_regra | 0,952501 | 23,528090 | 17,775281 | 5,752809 | 0,847345 | 0,859691 | 38,792023 |
| A_hibrido67 | 0,944281 | 22,741573 | 17,775281 | 4,966292 | 0,855581 | 0,864052 | 38,097976 |
| B_regra | 0,959565 | 27,449438 | 16,179775 | 11,269663 | 0,825401 | 0,840212 | 44,495551 |
| B_hibrido67 | 0,959092 | 26,426966 | 16,179775 | 10,247191 | 0,834332 | 0,849525 | 43,157243 |

| Cobertura ouro | N palavras | Cobertas % | Duplicadas % | Órfãs % | Múltiplas caixas geométricas |
|---|---:|---:|---:|---:|---:|
| A/antes_fallback | 95311 | 99,785964 | 0,000000 | 0,214036 | 185 |
| A/final | 95311 | 100,000000 | 0,000000 | 0,000000 | 185 |
| B/antes_fallback | 95311 | 100,000000 | 0,000000 | 0,000000 | 2 |
| B/final | 95311 | 100,000000 | 0,000000 | 0,000000 | 2 |

| Contraste | Métrica | Δ [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior |
|---|---|---:|---:|---:|
| B-A_regra | tau | 0,007064 [-0,000617; 0,027893] | 0,285049 | 17/33/39 |
| B-A_regra | quebras | 3,921348 [0,605263; 8,538462] | 0,108809 | 11/40/38 |
| B-A_regra | quebras_mil | 5,703528 [0,572339; 11,518420] | 0,108809 | 11/40/38 |
| B-A_regra | fid12 | -0,021944 [-0,039902; -0,000754] | 0,108809 | 9/40/40 |
| B-A_regra | sucessor_linhas | -0,019479 [-0,040332; -0,001985] | 0,108809 | 13/40/36 |
| B-A_regra | piso_interno | -1,595506 [-4,973684; 4,153846] | 0,592980 | 10/50/29 |
| B-A_regra | entre_unidades | 5,516854 [4,384615; 5,842105] | 0,108809 | 13/39/37 |
| B-A_hibrido67 | tau | 0,014812 [-0,055016; 0,055816] | 1,000000 | 29/27/33 |
| B-A_hibrido67 | quebras | 3,685393 [1,868421; 10,461538] | 0,108809 | 27/30/32 |
| B-A_hibrido67 | quebras_mil | 5,059268 [1,698021; 8,004193] | 0,108809 | 27/30/32 |
| B-A_hibrido67 | fid12 | -0,021249 [-0,051620; -0,008494] | 0,108809 | 23/31/35 |
| B-A_hibrido67 | sucessor_linhas | -0,014527 [-0,018382; -0,010326] | 0,108809 | 29/30/30 |
| B-A_hibrido67 | piso_interno | -1,595506 [-4,973684; 4,153846] | 0,592980 | 10/50/29 |
| B-A_hibrido67 | entre_unidades | 5,280899 [3,368421; 6,842105] | 0,108809 | 32/26/31 |
| A_regra-B_regra | tau | -0,007064 [-0,027893; 0,000617] | 0,285049 | 39/33/17 |
| A_regra-B_regra | quebras | -3,921348 [-8,538462; -0,605263] | 0,108809 | 38/40/11 |
| A_regra-B_regra | quebras_mil | -5,703528 [-11,518420; -0,572339] | 0,108809 | 38/40/11 |
| A_regra-B_regra | fid12 | 0,021944 [0,000754; 0,039902] | 0,108809 | 40/40/9 |
| A_regra-B_regra | sucessor_linhas | 0,019479 [0,001985; 0,040332] | 0,108809 | 36/40/13 |
| A_regra-B_regra | piso_interno | 1,595506 [-4,153846; 4,973684] | 0,592980 | 29/50/10 |
| A_regra-B_regra | entre_unidades | -5,516854 [-5,842105; -4,384615] | 0,108809 | 37/39/13 |
| A_hibrido67-B_regra | tau | -0,015285 [-0,055333; 0,055036] | 1,000000 | 47/14/28 |
| A_hibrido67-B_regra | quebras | -4,707865 [-10,538462; -3,657895] | 0,108809 | 43/21/25 |
| A_hibrido67-B_regra | quebras_mil | -6,397575 [-9,273800; -3,545090] | 0,108809 | 43/21/25 |
| A_hibrido67-B_regra | fid12 | 0,030181 [0,018944; 0,051896] | 0,108809 | 48/23/18 |
| A_hibrido67-B_regra | sucessor_linhas | 0,023840 [0,015619; 0,029697] | 0,108809 | 41/21/27 |
| A_hibrido67-B_regra | piso_interno | 1,595506 [-4,153846; 4,973684] | 0,592980 | 29/50/10 |
| A_hibrido67-B_regra | entre_unidades | -6,303371 [-8,736842; -3,842105] | 0,108809 | 43/17/29 |
| B_hibrido67-B_regra | tau | -0,000473 [-0,001598; 0,000483] | 1,000000 | 16/66/7 |
| B_hibrido67-B_regra | quebras | -1,022472 [-1,894737; -0,076923] | 0,108809 | 14/72/3 |
| B_hibrido67-B_regra | quebras_mil | -1,338308 [-1,847069; -0,051975] | 0,108809 | 14/72/3 |
| B_hibrido67-B_regra | fid12 | 0,008931 [0,000277; 0,010450] | 0,108809 | 15/74/0 |
| B_hibrido67-B_regra | sucessor_linhas | 0,009313 [0,000078; 0,011315] | 0,108809 | 14/72/3 |
| B_hibrido67-B_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| B_hibrido67-B_regra | entre_unidades | -1,022472 [-1,894737; -0,076923] | 0,108809 | 14/72/3 |
| A_hibrido67-A_regra | tau | -0,008220 [-0,047713; 0,082929] | 0,592980 | 34/29/26 |
| A_hibrido67-A_regra | quebras | -0,786517 [-3,157895; 2,000000] | 0,414216 | 30/32/27 |
| A_hibrido67-A_regra | quebras_mil | -0,694047 [-2,972751; 2,244620] | 0,285049 | 30/32/27 |
| A_hibrido67-A_regra | fid12 | 0,008236 [-0,005914; 0,020504] | 0,285049 | 32/33/24 |
| A_hibrido67-A_regra | sucessor_linhas | 0,004361 [-0,019536; 0,025085] | 0,592980 | 29/32/28 |
| A_hibrido67-A_regra | piso_interno | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/89/0 |
| A_hibrido67-A_regra | entre_unidades | -0,786517 [-3,157895; 2,000000] | 0,414216 | 30/32/27 |

| Contraste | Sucessores reparados | Sucessores regredidos |
|---|---:|---:|
| B-A_regra | 128 | 444 |
| B-A_hibrido67 | 181 | 471 |
| A_hibrido67-B_regra | 561 | 180 |
| B_hibrido67-B_regra | 102 | 11 |

| Veículo | Páginas | Δ quebras B − A regra | Δ quebras B − A híbrido 67 |
|---|---:|---:|---:|
| official_diary_ce | 38 | 0,605263 | 1,868421 |
| official_diary_ma | 38 | 5,657895 | 3,184211 |
| official_diary_rj | 13 | 8,538462 | 10,461538 |

Páginas roteadas ao LayoutReader: A_hibrido67: 82; B_hibrido67: 27.

## Reconstrução de 213 → 29

A fonte numérica exata é `resultados/erros_ponta_a_ponta.json`, resumida em seu Markdown. O relatório da noite cita a comparação de pipelines, mas não contém literalmente o par 213 → 29. O par soma as duas bancadas humanas; aparece aqui só para reconstrução histórica, sem inferência sobre a soma.

| Bancada | Pipeline | Piso antigo | Piso atual (bancada) | Quebras totais antigas |
|---|---|---:|---:|---:|
| golden_v4 | P1 | 70 | 70 | 716 |
| golden_v4 | P1m | 70 | 70 | 393 |
| golden_v4 | P2 | 23 | 24 | 266 |
| golden_v3_novo | P1 | 143 | 143 | 430 |
| golden_v3_novo | P1m | 143 | 143 | 308 |
| golden_v3_novo | P2 | 6 | 7 | 249 |

Na definição original, o par é confirmado: contam-se eventos com as duas palavras na mesma unidade, excluindo palavras fora do ouro interpostas. A bancada atual soma `eventos(fluxo([unidade]), gt_w)` e inclui essas intercalações internas; daí 213 → 31. A direção histórica só se confirma sob a régua atual se o segundo total continuar menor; isso é verdadeiro. Não representa redução de quebras totais nem garante ganho com ordenador fixo.

## Critérios e limitações

- golden_v4/regra: não atendido.
- golden_v4/hibrido67: não atendido.
- golden_v4/cobertura: atendido.
- golden_v3_novo/regra: não atendido.
- golden_v3_novo/hibrido67: não atendido.
- golden_v3_novo/cobertura: atendido.

Bootstrap importado da bancada: 5000 reamostras de veículos, semente 20261004, percentis de 95%; todas as páginas de um veículo sorteado permanecem juntas, mantendo média por página. Wilcoxon Pratt bilateral sobre médias dos deltas por veículo, exploratório e sem correção de multiplicidade. Dados por veículo e IC de todas as métricas ficam em `resultados.json`. Silver tem apenas 3 veículos; baixa resolução inferencial.

golden_v4 foi usado para desenvolver a regra e escolher o limiar 67. golden_v3_novo já foi consultado em rodadas anteriores; não é teste confirmatório independente. O silver CE/MA/RJ é sensibilidade: fluxo do PDF ruidoso, seleção por concordância com XY-cut e divergência nas tabelas. Bancadas podem compartilhar páginas e veículos: não somar como observações independentes. Não houve ajuste nesta execução nem consulta à validação RN para escolher parâmetros.

O ouro humano anota ordem de regiões, com expansão geométrica para palavras/linhas, não transcrição ou sucessão independente de cada palavra. Há viés de pré-anotação no Diamond e de blocos no v3; tabelas são ambíguas. Relata-se a página inteira com palavras fora do ouro preservadas; não há referência independente só do corpo. Dentro/entre unidades é decomposição operacional dos eventos emitidos, não atribuição causal de erro ao detector. A duplicação geométrica não implica duplicação na saída.

O teste cego foi excluído pelo lacre antes da desserialização de cada página. Não se abriram PDFs, imagens, `data/labelstudio`, exports ou fontes do parceiro; só foram usados derivados e caches próprios já existentes. Nada foi gravado em `data/`. O E009 não mede tempo de anotação nem justifica sozinho a adoção no E008.

Reexecução: `venv/Scripts/python.exe -B orquestracao/analises/e009_representacao.py`. Auditoria sem nova inferência: acrescentar `--conferir`. Manifesto, hashes e comando ficam em `manifesto.json`; resultados parciais e mapas de palavras em `cache/`. Todos os números deste relatório foram escritos por este script.
