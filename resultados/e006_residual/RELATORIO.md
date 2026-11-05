1. Âncora golden_v4: τ 0,985948; 6,045455 quebras/página.
2. Ajuste v4 + RN com peso igual; λ=2,0, M=20 congelados.
3. golden_v4: residual 4,431818 quebras/página; validacao_silver: residual 13,733333 quebras/página; golden_v3_novo: residual 7,074074 quebras/página; teste_silver: residual 24,887640 quebras/página
4. Veredito pelo cartão E006: NÃO GO.
5. CPU, sem retreino, referências fora da busca, palavras preservadas e cache por página/passo.
6. golden_v3_novo já foi consultado em rodadas anteriores; teste cego não foi avaliado.

# E006 — correção residual local

Relatório integralmente gerado pelo script.

## Método, seleção e limitações

Ordem inicial: híbrido 67 salvo (LayoutReader até 67 unidades, regra nas demais). Operações importadas literalmente de `e002_oraculos.operacoes` e `mover`: troca vizinha; bloco de 1–4 textos até 8 posições na coluna sem atravessar margem/átomo/ponte; reinserção de margem/título antes/depois dos candidatos K32 ou nas extremidades. A restrição de barreira vale para bloco_coluna; vizinhas e reinserções conservam exatamente a definição do E002, inclusive suas exceções.

Ganho = soma de log P das arestas criadas menos removidas, com FIM privado do E004 e sem escore de INÍCIO. Maior ganho estritamente acima de λ; empate pela enumeração E002. M limita operações, e ∞ termina em ótimo local estrito. Para o ajuste, os prefixos 5/20 da trajetória ∞ são exatamente as buscas limitadas. Não se atravessam platôs. O ouro é usado só depois de cada predição, para medição, e no oráculo diagnóstico salvo.

Modelo LightGBM e calibração Platt OOF do E004 importados, sem retreino/recalibração. Os pares do pool K32+extras mantêm suas features e escores. Pares fora desse pool são inferidos pelo mesmo modelo/features com rank terminal e relativo 1 (extrapolação, contada nos caches). Não se lhes atribui escore zero. A cobertura não mede texto ausente da camada digital.

Seleção: mínima média de quebras de golden_v4/RN, com peso 1/2 para cada bancada, e τ médio ≥ híbrido médio − 0,005. Desempates: maior τ, menor M, maior λ; fixados no código antes da medição. O item 3 do cartão é depois conferido separadamente nas três bancadas principais. Nenhum parâmetro é escolhido pelas externas.

Oráculo residual é o teto local diagnóstico E002 salvo, iniciado na regra; não é um limite matemático para a busca iniciada no híbrido. RN não tinha predições LayoutReader nas páginas leves: o script exige complemento explícito e nunca substitui pela regra ou usa média parcial. Regra_reordena não existe salva para RN e é omitida nessa bancada auxiliar.

Estatística importada: 5000 bootstraps por veículo, semente 20261004, IC95 percentil; Wilcoxon Pratt bilateral sobre os deltas médios por veículo, descritivo. Médias principais por página; as três bancadas principais são separadas e não são amostras independentes somáveis. RN tem um veículo: IC degenerado. Silver usa fluxo PDF ruidoso e pode ter átomos enormes que dominam τ. Regressões/reparos comparam sucessores-ouro intactos, inclusive no critério 4, relativamente ao híbrido; o critério é exigido em cada externa separadamente.

Corpo é projeção diagnóstica importada do E014: exclui margens detectadas automaticamente e usa a régua oficial; não existe gabarito humano independente de corpo. Quebras/1.000 macro dividem por palavras-ouro por página; micro divide pelo total de palavras-ouro. Fidelidade de 12 é importada. O teste cego é barrado por ID/PDF antes da desserialização de cada registro.

Pico RSS medido pelo SO: 2757,3 MiB (limite 3072 MiB); threads 4, processos 1, num_workers 0. Manifesto e trilhas por operação ficam em `resultados/e006_residual/cache/722c5d8576dc383e20398ee53fdf92420c0dc7bc250dd5f877fd92ce651c8417`. O código é arquivado quando o ajuste completo permite congelar os parâmetros.

## Grade do ajuste (sem externas)

| λ | M | Quebras (v4/RN 1/2) | τ | Δτ híbrido | Elegível |
|---:|---:|---:|---:|---:|---|
| 0,0 | 5 | 8,738636 | 0,947999 | -0,021198 | False |
| 0,0 | 20 | 7,303788 | 0,947981 | -0,021215 | False |
| 0,0 | ∞ | 7,303788 | 0,947981 | -0,021215 | False |
| 0,5 | 5 | 8,838636 | 0,947627 | -0,021570 | False |
| 0,5 | 20 | 7,870455 | 0,947628 | -0,021569 | False |
| 0,5 | ∞ | 7,870455 | 0,947628 | -0,021569 | False |
| 1,0 | 5 | 8,916667 | 0,947502 | -0,021695 | False |
| 1,0 | 20 | 8,281818 | 0,947503 | -0,021694 | False |
| 1,0 | ∞ | 8,281818 | 0,947503 | -0,021694 | False |
| 2,0 | 5 | 9,105303 | 0,970152 | 0,000955 | True |
| 2,0 | 20 | 9,082576 | 0,970152 | 0,000955 | True |
| 2,0 | ∞ | 9,082576 | 0,970152 | 0,000955 | True |
| 4,0 | 5 | 9,593939 | 0,971127 | 0,001930 | True |
| 4,0 | 20 | 9,571212 | 0,971128 | 0,001931 | True |
| 4,0 | ∞ | 9,571212 | 0,971128 | 0,001931 | True |

## golden_v4

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 macro / micro | Fid12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 44 / 27 | 0,985948 | 6,045455 | 11,884752 / 7,353958 | 0,948129 | 0,927240 | 100,0% |
| hibrido67 | 44 / 27 | 0,979738 | 5,136364 | 6,041242 / 6,248099 | 0,973419 | 0,966143 | 100,0% |
| regra_reordena | 44 / 27 | 0,985967 | 5,181818 | 10,904691 / 6,303392 | 0,954405 | 0,936322 | 100,0% |
| oraculo_residual | 44 / 27 | 0,989684 | 1,909091 | 2,450334 / 2,322302 | 0,987893 | 0,986299 | 100,0% |
| e006_residual | 44 / 27 | 0,977974 | 4,431818 | 8,534229 / 5,391059 | 0,956767 | 0,952266 | 100,0% |

### Contrastes pareados

| Método | Referência | Métrica | Δ [IC95 veículo] | p veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|
| regra | hibrido67 | tau | 0,006211 [-0,009968; 0,033051] | 0,127972 | 4/24/16 |
| regra | hibrido67 | quebras | 0,909091 [0,095238; 1,775567] | 0,022323 | 4/24/16 |
| regra | hibrido67 | quebras_mil | 5,843509 [0,457171; 14,066405] | 0,040740 | 4/24/16 |
| regra | hibrido67 | fid12 | -0,025290 [-0,063276; -0,000783] | 0,136481 | 5/25/14 |
| regra | hibrido67 | sucessor_linhas | -0,038903 [-0,092315; -0,004194] | 0,031875 | 4/24/16 |
| regra | regra_reordena | tau | -0,000018 [-0,000043; -0,000001] | 0,052640 | 2/34/8 |
| regra | regra_reordena | quebras | 0,863636 [0,309394; 1,609756] | 0,014913 | 1/35/8 |
| regra | regra_reordena | quebras_mil | 0,980061 [0,307305; 1,776912] | 0,014934 | 1/35/8 |
| regra | regra_reordena | fid12 | -0,006277 [-0,011817; -0,001896] | 0,004877 | 0/36/8 |
| regra | regra_reordena | sucessor_linhas | -0,009082 [-0,017734; -0,002452] | 0,004877 | 0/36/8 |
| hibrido67 | regra | tau | -0,006211 [-0,033051; 0,009968] | 0,127972 | 16/24/4 |
| hibrido67 | regra | quebras | -0,909091 [-1,775567; -0,095238] | 0,022323 | 16/24/4 |
| hibrido67 | regra | quebras_mil | -5,843509 [-14,066405; -0,457171] | 0,040740 | 16/24/4 |
| hibrido67 | regra | fid12 | 0,025290 [0,000783; 0,063276] | 0,136481 | 14/25/5 |
| hibrido67 | regra | sucessor_linhas | 0,038903 [0,004194; 0,092315] | 0,031875 | 16/24/4 |
| hibrido67 | regra_reordena | tau | -0,006229 [-0,033062; 0,009953] | 0,370509 | 15/20/9 |
| hibrido67 | regra_reordena | quebras | -0,045455 [-0,958333; 0,975000] | 0,834662 | 14/21/9 |
| hibrido67 | regra_reordena | quebras_mil | -4,863449 [-12,961476; 0,461111] | 0,484401 | 14/21/9 |
| hibrido67 | regra_reordena | fid12 | 0,019013 [-0,005501; 0,056696] | 0,683343 | 12/22/10 |
| hibrido67 | regra_reordena | sucessor_linhas | 0,029821 [-0,003452; 0,080558] | 0,397301 | 14/21/9 |
| regra_reordena | regra | tau | 0,000018 [0,000001; 0,000043] | 0,052640 | 8/34/2 |
| regra_reordena | regra | quebras | -0,863636 [-1,609756; -0,309394] | 0,014913 | 8/35/1 |
| regra_reordena | regra | quebras_mil | -0,980061 [-1,776912; -0,307305] | 0,014934 | 8/35/1 |
| regra_reordena | regra | fid12 | 0,006277 [0,001896; 0,011817] | 0,004877 | 8/36/0 |
| regra_reordena | regra | sucessor_linhas | 0,009082 [0,002452; 0,017734] | 0,004877 | 8/36/0 |
| regra_reordena | hibrido67 | tau | 0,006229 [-0,009953; 0,033062] | 0,370509 | 9/20/15 |
| regra_reordena | hibrido67 | quebras | 0,045455 [-0,975000; 0,958333] | 0,834662 | 9/21/14 |
| regra_reordena | hibrido67 | quebras_mil | 4,863449 [-0,461111; 12,961476] | 0,484401 | 9/21/14 |
| regra_reordena | hibrido67 | fid12 | -0,019013 [-0,056696; 0,005501] | 0,683343 | 10/22/12 |
| regra_reordena | hibrido67 | sucessor_linhas | -0,029821 [-0,080558; 0,003452] | 0,397301 | 9/21/14 |
| oraculo_residual | regra | tau | 0,003736 [0,000656; 0,007861] | 0,000132 | 32/11/1 |
| oraculo_residual | regra | quebras | -4,136364 [-5,651163; -2,874864] | 0,000012 | 33/11/0 |
| oraculo_residual | regra | quebras_mil | -9,434418 [-17,170033; -4,048732] | 0,000012 | 33/11/0 |
| oraculo_residual | regra | fid12 | 0,039764 [0,018081; 0,073838] | 0,000012 | 31/13/0 |
| oraculo_residual | regra | sucessor_linhas | 0,059059 [0,028298; 0,106211] | 0,000012 | 32/12/0 |
| oraculo_residual | hibrido67 | tau | 0,009946 [-0,005981; 0,036309] | 0,028102 | 21/19/4 |
| oraculo_residual | hibrido67 | quebras | -3,227273 [-5,000000; -1,804239] | 0,000219 | 24/18/2 |
| oraculo_residual | hibrido67 | quebras_mil | -3,590908 [-5,442270; -1,864656] | 0,000445 | 24/18/2 |
| oraculo_residual | hibrido67 | fid12 | 0,014474 [0,006293; 0,023430] | 0,000967 | 21/21/2 |
| oraculo_residual | hibrido67 | sucessor_linhas | 0,020157 [0,008863; 0,031618] | 0,000834 | 23/19/2 |
| oraculo_residual | regra_reordena | tau | 0,003717 [0,000635; 0,007846] | 0,000307 | 28/14/2 |
| oraculo_residual | regra_reordena | quebras | -3,272727 [-4,522727; -2,186047] | 0,000030 | 30/14/0 |
| oraculo_residual | regra_reordena | quebras_mil | -8,454357 [-15,872784; -3,239530] | 0,000030 | 30/14/0 |
| oraculo_residual | regra_reordena | fid12 | 0,033487 [0,012801; 0,066522] | 0,000030 | 28/16/0 |
| oraculo_residual | regra_reordena | sucessor_linhas | 0,049977 [0,020841; 0,094107] | 0,000030 | 29/15/0 |
| e006_residual | regra | tau | -0,007974 [-0,031299; 0,004243] | 0,143413 | 17/22/5 |
| e006_residual | regra | quebras | -1,613636 [-2,523810; -0,785714] | 0,007202 | 18/23/3 |
| e006_residual | regra | quebras_mil | -3,350523 [-6,631943; -1,077410] | 0,004600 | 18/23/3 |
| e006_residual | regra | fid12 | 0,008638 [0,003284; 0,014350] | 0,011909 | 15/24/5 |
| e006_residual | regra | sucessor_linhas | 0,025026 [0,008500; 0,047504] | 0,003112 | 18/23/3 |
| e006_residual | hibrido67 | tau | -0,001763 [-0,009788; 0,004364] | 0,970643 | 12/19/13 |
| e006_residual | hibrido67 | quebras | -0,704545 [-1,727320; 0,227273] | 0,119094 | 13/20/11 |
| e006_residual | hibrido67 | quebras_mil | 2,492986 [-1,333170; 7,755607] | 0,465827 | 13/20/11 |
| e006_residual | hibrido67 | fid12 | -0,016652 [-0,055482; 0,007962] | 0,549254 | 11/21/12 |
| e006_residual | hibrido67 | sucessor_linhas | -0,013877 [-0,046926; 0,009813] | 0,566019 | 12/21/11 |
| e006_residual | regra_reordena | tau | -0,007992 [-0,031336; 0,004234] | 0,353897 | 15/23/6 |
| e006_residual | regra_reordena | quebras | -0,750000 [-1,346961; -0,131550] | 0,080519 | 15/25/4 |
| e006_residual | regra_reordena | quebras_mil | -2,370462 [-5,379606; -0,338053] | 0,048689 | 15/25/4 |
| e006_residual | regra_reordena | fid12 | 0,002361 [-0,001752; 0,006570] | 0,464233 | 11/27/6 |
| e006_residual | regra_reordena | sucessor_linhas | 0,015944 [0,003306; 0,034314] | 0,043258 | 15/25/4 |

### Sucessores reparados e perdidos

| Método | Referência | Reparos | Regressões |
|---|---|---:|---:|
| regra | regra | 0 | 0 |
| regra | hibrido67 | 16 | 58 |
| regra | regra_reordena | 0 | 37 |
| hibrido67 | regra | 58 | 16 |
| hibrido67 | hibrido67 | 0 | 0 |
| hibrido67 | regra_reordena | 43 | 38 |
| regra_reordena | regra | 37 | 0 |
| regra_reordena | hibrido67 | 38 | 43 |
| regra_reordena | regra_reordena | 0 | 0 |
| oraculo_residual | regra | 171 | 0 |
| oraculo_residual | hibrido67 | 134 | 5 |
| oraculo_residual | regra_reordena | 134 | 0 |
| e006_residual | regra | 83 | 12 |
| e006_residual | hibrido67 | 58 | 29 |
| e006_residual | regra_reordena | 50 | 16 |

Operações do candidato: 53; por tipo: `{"reinsercao": 25, "vizinhas": 28}`; páginas alteradas: 26.

| Veículo | Δ quebras vs regra | Δ quebras vs híbrido | Δτ vs híbrido |
|---|---:|---:|---:|
| official_diary_MG_congonhas | -2,500000 | 0,000000 | 0,000000 |
| official_diary_RJ_barra_do_pirai | -2,666667 | 3,000000 | -0,014852 |
| official_diary_RJ_duque_de_caxias | -3,000000 | -2,500000 | -0,067958 |
| official_diary_RJ_seropedica | -1,000000 | -0,500000 | -0,000535 |
| official_diary_RJ_volta_redonda | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ac | -2,000000 | -1,000000 | 0,024656 |
| official_diary_al | -0,666667 | 0,000000 | -0,000717 |
| official_diary_am_manaus | 3,000000 | 0,000000 | 0,000000 |
| official_diary_ap | -1,500000 | -1,500000 | 0,002522 |
| official_diary_ba_salvador | 4,000000 | -2,000000 | 0,042523 |
| official_diary_ce | 0,000000 | 2,000000 | -0,000061 |
| official_diary_ma | 0,000000 | 0,000000 | 0,000000 |
| official_diary_mg | -9,000000 | -9,000000 | 0,000010 |
| official_diary_ms | 0,000000 | 1,000000 | -0,000568 |
| official_diary_pb | -4,000000 | -4,500000 | 0,010955 |
| official_diary_pe | -3,000000 | -3,000000 | 0,000002 |
| official_diary_pi_v2 | 0,000000 | 2,000000 | -0,000121 |
| official_diary_pr_curitiba | 0,000000 | 0,000000 | 0,000000 |
| official_diary_rj | -12,000000 | -12,000000 | 0,000107 |
| official_diary_rj_japeri | -2,000000 | -1,000000 | -0,002745 |
| official_diary_rn | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ro | -4,500000 | 0,000000 | 0,000000 |
| official_diary_rr | 1,000000 | 3,000000 | -0,015734 |
| official_diary_rs_porto_alegre | -1,500000 | -1,000000 | 0,003174 |
| official_diary_sc | 0,000000 | 0,000000 | 0,000000 |
| official_diary_se | -0,500000 | -0,500000 | 0,001761 |
| official_diary_to | 0,000000 | 0,000000 | 0,000000 |

| Classe de sucessor | Reparos vs híbrido | Regressões vs híbrido |
|---|---:|---:|
| mesma_coluna | 16 | 0 |
| proxima_coluna | 0 | 0 |
| tabela_imagem | 3 | 0 |
| transversal | 4 | 0 |
| margem | 26 | 29 |
| outro | 9 | 0 |

### Corpo (diagnóstico por margens automáticas)

| Método | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|
| regra | 0,993467 | 2,931818 | 3,325766 | 0,985674 | 0,977845 |
| hibrido67 | 0,986295 | 2,772727 | 2,703639 | 0,988822 | 0,985116 |
| regra_reordena | 0,993489 | 2,136364 | 2,438819 | 0,990759 | 0,986097 |
| oraculo_residual | 0,993037 | 1,227273 | 1,444410 | 0,994620 | 0,992439 |
| e006_residual | 0,984154 | 2,022727 | 2,155881 | 0,991113 | 0,988206 |

## golden_v3_novo

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 macro / micro | Fid12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 27 / 10 | 0,959557 | 9,222222 | 17,205754 / 10,471865 | 0,928415 | 0,911301 | 100,0% |
| hibrido67 | 27 / 10 | 0,958977 | 7,888889 | 13,739464 / 8,957860 | 0,941220 | 0,938410 | 100,0% |
| regra_reordena | 27 / 10 | 0,959578 | 7,777778 | 14,720045 / 8,831693 | 0,936469 | 0,925754 | 100,0% |
| oraculo_residual | 27 / 10 | 0,962132 | 2,222222 | 3,681067 / 2,523341 | 0,975461 | 0,977345 | 100,0% |
| e006_residual | 27 / 10 | 0,938615 | 7,074074 | 14,527112 / 8,032635 | 0,930090 | 0,927707 | 100,0% |

### Contrastes pareados

| Método | Referência | Métrica | Δ [IC95 veículo] | p veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|
| regra | hibrido67 | tau | 0,000580 [-0,005062; 0,004980] | 0,151855 | 2/17/8 |
| regra | hibrido67 | quebras | 1,333333 [0,363636; 2,648682] | 0,027670 | 2/18/7 |
| regra | hibrido67 | quebras_mil | 3,466289 [0,665607; 9,191916] | 0,027670 | 2/18/7 |
| regra | hibrido67 | fid12 | -0,012805 [-0,028351; -0,003514] | 0,016924 | 2/17/8 |
| regra | hibrido67 | sucessor_linhas | -0,027108 [-0,061825; -0,006827] | 0,027670 | 2/18/7 |
| regra | regra_reordena | tau | -0,000020 [-0,000110; 0,000058] | 0,099906 | 2/17/8 |
| regra | regra_reordena | quebras | 1,444444 [-0,263246; 2,391343] | 0,425964 | 2/18/7 |
| regra | regra_reordena | quebras_mil | 2,485708 [-0,010497; 4,591081] | 0,366915 | 2/18/7 |
| regra | regra_reordena | fid12 | -0,008054 [-0,013426; -0,001959] | 0,123765 | 2/18/7 |
| regra | regra_reordena | sucessor_linhas | -0,014452 [-0,022753; -0,001706] | 0,152358 | 1/19/7 |
| hibrido67 | regra | tau | -0,000580 [-0,004980; 0,005062] | 0,151855 | 8/17/2 |
| hibrido67 | regra | quebras | -1,333333 [-2,648682; -0,363636] | 0,027670 | 7/18/2 |
| hibrido67 | regra | quebras_mil | -3,466289 [-9,191916; -0,665607] | 0,027670 | 7/18/2 |
| hibrido67 | regra | fid12 | 0,012805 [0,003514; 0,028351] | 0,016924 | 8/17/2 |
| hibrido67 | regra | sucessor_linhas | 0,027108 [0,006827; 0,061825] | 0,027670 | 7/18/2 |
| hibrido67 | regra_reordena | tau | -0,000600 [-0,005014; 0,005005] | 0,640316 | 7/14/6 |
| hibrido67 | regra_reordena | quebras | 0,111111 [-2,353493; 1,696970] | 0,194009 | 6/15/6 |
| hibrido67 | regra_reordena | quebras_mil | -0,980581 [-8,226514; 3,341196] | 0,232439 | 6/15/6 |
| hibrido67 | regra_reordena | fid12 | 0,004751 [-0,003389; 0,022459] | 0,323922 | 7/15/5 |
| hibrido67 | regra_reordena | sucessor_linhas | 0,012656 [-0,008377; 0,052451] | 0,160984 | 6/15/6 |
| regra_reordena | regra | tau | 0,000020 [-0,000058; 0,000110] | 0,099906 | 8/17/2 |
| regra_reordena | regra | quebras | -1,444444 [-2,391343; 0,263246] | 0,425964 | 7/18/2 |
| regra_reordena | regra | quebras_mil | -2,485708 [-4,591081; 0,010497] | 0,366915 | 7/18/2 |
| regra_reordena | regra | fid12 | 0,008054 [0,001959; 0,013426] | 0,123765 | 7/18/2 |
| regra_reordena | regra | sucessor_linhas | 0,014452 [0,001706; 0,022753] | 0,152358 | 7/19/1 |
| regra_reordena | hibrido67 | tau | 0,000600 [-0,005005; 0,005014] | 0,640316 | 6/14/7 |
| regra_reordena | hibrido67 | quebras | -0,111111 [-1,696970; 2,353493] | 0,194009 | 6/15/6 |
| regra_reordena | hibrido67 | quebras_mil | 0,980581 [-3,341196; 8,226514] | 0,232439 | 6/15/6 |
| regra_reordena | hibrido67 | fid12 | -0,004751 [-0,022459; 0,003389] | 0,323922 | 5/15/7 |
| regra_reordena | hibrido67 | sucessor_linhas | -0,012656 [-0,052451; 0,008377] | 0,160984 | 6/15/6 |
| oraculo_residual | regra | tau | 0,002574 [0,000785; 0,006332] | 0,005062 | 21/6/0 |
| oraculo_residual | regra | quebras | -7,000000 [-10,500291; -3,526316] | 0,005034 | 22/5/0 |
| oraculo_residual | regra | quebras_mil | -13,524686 [-22,736432; -5,421095] | 0,005062 | 22/5/0 |
| oraculo_residual | regra | fid12 | 0,047046 [0,022999; 0,071195] | 0,005857 | 20/7/0 |
| oraculo_residual | regra | sucessor_linhas | 0,066044 [0,042430; 0,094061] | 0,005062 | 22/5/0 |
| oraculo_residual | hibrido67 | tau | 0,003154 [0,000084; 0,006635] | 0,125786 | 18/6/3 |
| oraculo_residual | hibrido67 | quebras | -5,666667 [-9,976220; -0,958288] | 0,018826 | 18/7/2 |
| oraculo_residual | hibrido67 | quebras_mil | -10,058397 [-20,322636; -0,648421] | 0,066193 | 18/7/2 |
| oraculo_residual | hibrido67 | fid12 | 0,034241 [0,000293; 0,065104] | 0,153042 | 18/6/3 |
| oraculo_residual | hibrido67 | sucessor_linhas | 0,038935 [0,003502; 0,074379] | 0,102470 | 18/7/2 |
| oraculo_residual | regra_reordena | tau | 0,002554 [0,000744; 0,006285] | 0,018904 | 19/7/1 |
| oraculo_residual | regra_reordena | quebras | -5,555556 [-8,486824; -2,346154] | 0,005825 | 20/7/0 |
| oraculo_residual | regra_reordena | quebras_mil | -11,038978 [-18,728758; -4,149590] | 0,005857 | 20/7/0 |
| oraculo_residual | regra_reordena | fid12 | 0,038992 [0,012451; 0,065473] | 0,014306 | 19/7/1 |
| oraculo_residual | regra_reordena | sucessor_linhas | 0,051591 [0,026808; 0,083617] | 0,005857 | 20/7/0 |
| e006_residual | regra | tau | -0,020943 [-0,057514; 0,001941] | 0,202622 | 14/9/4 |
| e006_residual | regra | quebras | -2,148148 [-3,107143; -1,358889] | 0,005005 | 13/10/4 |
| e006_residual | regra | quebras_mil | -2,678641 [-7,008840; -0,358391] | 0,009344 | 13/10/4 |
| e006_residual | regra | fid12 | 0,001675 [-0,019951; 0,022852] | 0,074462 | 14/9/4 |
| e006_residual | regra | sucessor_linhas | 0,016406 [0,005625; 0,037439] | 0,010724 | 12/11/4 |
| e006_residual | hibrido67 | tau | -0,020362 [-0,052433; 0,000149] | 0,837419 | 8/13/6 |
| e006_residual | hibrido67 | quebras | -0,814815 [-2,138159; 0,333333] | 0,257820 | 8/14/5 |
| e006_residual | hibrido67 | quebras_mil | 0,787648 [-2,131990; 3,794553] | 0,918282 | 8/14/5 |
| e006_residual | hibrido67 | fid12 | -0,011130 [-0,038870; 0,013224] | 0,837419 | 8/13/6 |
| e006_residual | hibrido67 | sucessor_linhas | -0,010702 [-0,033189; 0,007790] | 0,795182 | 7/15/5 |
| e006_residual | regra_reordena | tau | -0,020963 [-0,057584; 0,001896] | 0,220671 | 11/12/4 |
| e006_residual | regra_reordena | quebras | -0,703704 [-3,071429; 0,914286] | 0,064078 | 10/13/4 |
| e006_residual | regra_reordena | quebras_mil | -0,192933 [-6,632310; 3,331537] | 0,153042 | 10/13/4 |
| e006_residual | regra_reordena | fid12 | -0,006379 [-0,032092; 0,017764] | 0,153042 | 11/12/4 |
| e006_residual | regra_reordena | sucessor_linhas | 0,001954 [-0,015355; 0,032653] | 0,150897 | 9/14/4 |

### Sucessores reparados e perdidos

| Método | Referência | Reparos | Regressões |
|---|---|---:|---:|
| regra | regra | 0 | 0 |
| regra | hibrido67 | 5 | 39 |
| regra | regra_reordena | 8 | 49 |
| hibrido67 | regra | 39 | 5 |
| hibrido67 | hibrido67 | 0 | 0 |
| hibrido67 | regra_reordena | 28 | 35 |
| regra_reordena | regra | 49 | 8 |
| regra_reordena | hibrido67 | 35 | 28 |
| regra_reordena | regra_reordena | 0 | 0 |
| oraculo_residual | regra | 179 | 0 |
| oraculo_residual | hibrido67 | 151 | 6 |
| oraculo_residual | regra_reordena | 142 | 4 |
| e006_residual | regra | 61 | 8 |
| e006_residual | hibrido67 | 30 | 11 |
| e006_residual | regra_reordena | 41 | 29 |

Operações do candidato: 25; por tipo: `{"bloco_coluna": 11, "reinsercao": 3, "vizinhas": 11}`; páginas alteradas: 16.

| Veículo | Δ quebras vs regra | Δ quebras vs híbrido | Δτ vs híbrido |
|---|---:|---:|---:|
| official_diary_RJ_barra_do_pirai | -2,000000 | -2,000000 | 0,000459 |
| official_diary_ac | -1,500000 | 1,000000 | -0,012428 |
| official_diary_ap | -2,000000 | -2,000000 | 0,001858 |
| official_diary_ce | -2,333333 | 0,333333 | -0,087519 |
| official_diary_ma | -0,714286 | -0,714286 | -0,000379 |
| official_diary_mg | -4,000000 | -4,000000 | 0,000215 |
| official_diary_pi_v2 | -1,500000 | 2,000000 | -0,000061 |
| official_diary_rj | -3,400000 | -3,400000 | 0,000086 |
| official_diary_ro | -3,000000 | 0,000000 | 0,000000 |
| official_diary_se | -5,000000 | 0,000000 | 0,000000 |

| Classe de sucessor | Reparos vs híbrido | Regressões vs híbrido |
|---|---:|---:|
| mesma_coluna | 13 | 3 |
| proxima_coluna | 0 | 0 |
| tabela_imagem | 3 | 1 |
| transversal | 0 | 0 |
| margem | 2 | 6 |
| outro | 12 | 1 |

### Corpo (diagnóstico por margens automáticas)

| Método | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|
| regra | 0,959496 | 7,703704 | 15,301645 | 0,936030 | 0,925058 |
| hibrido67 | 0,960716 | 6,555556 | 12,736183 | 0,947488 | 0,949111 |
| regra_reordena | 0,959518 | 6,111111 | 12,339064 | 0,945547 | 0,944375 |
| oraculo_residual | 0,961545 | 2,000000 | 3,123290 | 0,977886 | 0,981050 |
| e006_residual | 0,924019 | 5,592593 | 13,495082 | 0,941627 | 0,940462 |

## teste_silver

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 macro / micro | Fid12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 89 / 3 | 0,959565 | 27,449438 | 44,495551 / 25,631879 | 0,825401 | 0,840212 | 100,0% |
| hibrido67 | 89 / 3 | 0,959092 | 26,426966 | 43,157243 / 24,677110 | 0,834332 | 0,849525 | 100,0% |
| regra_reordena | 89 / 3 | 0,959615 | 26,449438 | 43,642505 / 24,698094 | 0,831979 | 0,848023 | 100,0% |
| oraculo_residual | 89 / 3 | 0,960488 | 19,966292 | 35,634537 / 18,644228 | 0,866151 | 0,887362 | 100,0% |
| e006_residual | 89 / 3 | 0,953281 | 24,887640 | 42,371075 / 23,239710 | 0,837250 | 0,853915 | 100,0% |

### Contrastes pareados

| Método | Referência | Métrica | Δ [IC95 veículo] | p veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|
| regra | hibrido67 | tau | 0,000473 [-0,000483; 0,001598] | 1,000000 | 7/66/16 |
| regra | hibrido67 | quebras | 1,022472 [0,076923; 1,894737] | 0,108809 | 3/72/14 |
| regra | hibrido67 | quebras_mil | 1,338308 [0,051975; 1,847069] | 0,108809 | 3/72/14 |
| regra | hibrido67 | fid12 | -0,008931 [-0,010450; -0,000277] | 0,108809 | 0/74/15 |
| regra | hibrido67 | sucessor_linhas | -0,009313 [-0,011315; -0,000078] | 0,108809 | 3/72/14 |
| regra | regra_reordena | tau | -0,000049 [-0,000105; -0,000008] | 0,108809 | 8/59/22 |
| regra | regra_reordena | quebras | 1,000000 [0,394737; 1,692308] | 0,108809 | 4/61/24 |
| regra | regra_reordena | quebras_mil | 0,853045 [0,632840; 1,065089] | 0,108809 | 4/61/24 |
| regra | regra_reordena | fid12 | -0,006579 [-0,009232; -0,004186] | 0,108809 | 4/64/21 |
| regra | regra_reordena | sucessor_linhas | -0,007812 [-0,011463; -0,004976] | 0,108809 | 4/61/24 |
| hibrido67 | regra | tau | -0,000473 [-0,001598; 0,000483] | 1,000000 | 16/66/7 |
| hibrido67 | regra | quebras | -1,022472 [-1,894737; -0,076923] | 0,108809 | 14/72/3 |
| hibrido67 | regra | quebras_mil | -1,338308 [-1,847069; -0,051975] | 0,108809 | 14/72/3 |
| hibrido67 | regra | fid12 | 0,008931 [0,000277; 0,010450] | 0,108809 | 15/74/0 |
| hibrido67 | regra | sucessor_linhas | 0,009313 [0,000078; 0,011315] | 0,108809 | 14/72/3 |
| hibrido67 | regra_reordena | tau | -0,000523 [-0,001606; 0,000378] | 1,000000 | 21/48/20 |
| hibrido67 | regra_reordena | quebras | -0,022472 [-0,526316; 1,615385] | 1,000000 | 16/56/17 |
| hibrido67 | regra_reordena | quebras_mil | -0,485262 [-0,781981; 0,824931] | 1,000000 | 16/56/17 |
| hibrido67 | regra_reordena | fid12 | 0,002353 [-0,003910; 0,005631] | 0,592980 | 17/60/12 |
| hibrido67 | regra_reordena | sucessor_linhas | 0,001501 [-0,005348; 0,005494] | 1,000000 | 16/56/17 |
| regra_reordena | regra | tau | 0,000049 [0,000008; 0,000105] | 0,108809 | 22/59/8 |
| regra_reordena | regra | quebras | -1,000000 [-1,692308; -0,394737] | 0,108809 | 24/61/4 |
| regra_reordena | regra | quebras_mil | -0,853045 [-1,065089; -0,632840] | 0,108809 | 24/61/4 |
| regra_reordena | regra | fid12 | 0,006579 [0,004186; 0,009232] | 0,108809 | 21/64/4 |
| regra_reordena | regra | sucessor_linhas | 0,007812 [0,004976; 0,011463] | 0,108809 | 24/61/4 |
| regra_reordena | hibrido67 | tau | 0,000523 [-0,000378; 0,001606] | 1,000000 | 20/48/21 |
| regra_reordena | hibrido67 | quebras | 0,022472 [-1,615385; 0,526316] | 1,000000 | 17/56/16 |
| regra_reordena | hibrido67 | quebras_mil | 0,485262 [-0,824931; 0,781981] | 1,000000 | 17/56/16 |
| regra_reordena | hibrido67 | fid12 | -0,002353 [-0,005631; 0,003910] | 0,592980 | 12/60/17 |
| regra_reordena | hibrido67 | sucessor_linhas | -0,001501 [-0,005494; 0,005348] | 1,000000 | 17/56/16 |
| oraculo_residual | regra | tau | 0,000922 [0,000457; 0,001381] | 0,108809 | 57/25/7 |
| oraculo_residual | regra | quebras | -7,483146 [-12,692308; -4,000000] | 0,108809 | 64/25/0 |
| oraculo_residual | regra | quebras_mil | -8,861014 [-10,001170; -6,833515] | 0,108809 | 64/25/0 |
| oraculo_residual | regra | fid12 | 0,040750 [0,031538; 0,050714] | 0,108809 | 62/27/0 |
| oraculo_residual | regra | sucessor_linhas | 0,047151 [0,032201; 0,062900] | 0,108809 | 64/25/0 |
| oraculo_residual | hibrido67 | tau | 0,001396 [0,000748; 0,002055] | 0,108809 | 50/26/13 |
| oraculo_residual | hibrido67 | quebras | -6,460674 [-12,615385; -3,526316] | 0,108809 | 57/31/1 |
| oraculo_residual | hibrido67 | quebras_mil | -7,522707 [-8,154100; -6,781540] | 0,108809 | 57/31/1 |
| oraculo_residual | hibrido67 | fid12 | 0,031818 [0,021164; 0,040264] | 0,108809 | 52/36/1 |
| oraculo_residual | hibrido67 | sucessor_linhas | 0,037838 [0,026045; 0,051586] | 0,108809 | 57/31/1 |
| oraculo_residual | regra_reordena | tau | 0,000873 [0,000448; 0,001373] | 0,108809 | 56/26/7 |
| oraculo_residual | regra_reordena | quebras | -6,483146 [-11,000000; -3,605263] | 0,108809 | 63/26/0 |
| oraculo_residual | regra_reordena | quebras_mil | -8,007969 [-8,936081; -5,956610] | 0,108809 | 63/26/0 |
| oraculo_residual | regra_reordena | fid12 | 0,034171 [0,026795; 0,041481] | 0,108809 | 61/28/0 |
| oraculo_residual | regra_reordena | sucessor_linhas | 0,039339 [0,026775; 0,051437] | 0,108809 | 63/26/0 |
| e006_residual | regra | tau | -0,006284 [-0,015390; 0,000649] | 1,000000 | 31/51/7 |
| e006_residual | regra | quebras | -2,561798 [-7,076923; -0,789474] | 0,108809 | 30/57/2 |
| e006_residual | regra | quebras_mil | -2,124476 [-3,746815; -1,685085] | 0,108809 | 30/57/2 |
| e006_residual | regra | fid12 | 0,011850 [0,009945; 0,022176] | 0,108809 | 29/57/3 |
| e006_residual | regra | sucessor_linhas | 0,013703 [0,011729; 0,018936] | 0,108809 | 30/57/2 |
| e006_residual | hibrido67 | tau | -0,005811 [-0,013792; 0,000166] | 1,000000 | 23/52/14 |
| e006_residual | hibrido67 | quebras | -1,539326 [-7,000000; -0,315789] | 0,108809 | 21/60/8 |
| e006_residual | hibrido67 | quebras_mil | -0,786168 [-3,694840; -0,161787] | 0,108809 | 21/60/8 |
| e006_residual | hibrido67 | fid12 | 0,002918 [-0,000429; 0,021899] | 1,000000 | 18/62/9 |
| e006_residual | hibrido67 | sucessor_linhas | 0,004391 [0,001259; 0,018858] | 0,108809 | 21/60/8 |
| e006_residual | regra_reordena | tau | -0,006334 [-0,015398; 0,000543] | 1,000000 | 21/60/8 |
| e006_residual | regra_reordena | quebras | -1,561798 [-5,384615; -0,394737] | 0,108809 | 20/64/5 |
| e006_residual | regra_reordena | quebras_mil | -1,271431 [-2,869910; -0,943768] | 0,108809 | 20/64/5 |
| e006_residual | regra_reordena | fid12 | 0,005271 [0,000989; 0,017989] | 0,108809 | 19/66/4 |
| e006_residual | regra_reordena | sucessor_linhas | 0,005892 [0,002425; 0,013510] | 0,108809 | 20/64/5 |

### Sucessores reparados e perdidos

| Método | Referência | Reparos | Regressões |
|---|---|---:|---:|
| regra | regra | 0 | 0 |
| regra | hibrido67 | 11 | 102 |
| regra | regra_reordena | 43 | 132 |
| hibrido67 | regra | 102 | 11 |
| hibrido67 | hibrido67 | 0 | 0 |
| hibrido67 | regra_reordena | 88 | 86 |
| regra_reordena | regra | 132 | 43 |
| regra_reordena | hibrido67 | 86 | 88 |
| regra_reordena | regra_reordena | 0 | 0 |
| oraculo_residual | regra | 657 | 0 |
| oraculo_residual | hibrido67 | 574 | 8 |
| oraculo_residual | regra_reordena | 568 | 0 |
| e006_residual | regra | 234 | 6 |
| e006_residual | hibrido67 | 157 | 20 |
| e006_residual | regra_reordena | 167 | 28 |

Operações do candidato: 100; por tipo: `{"vizinhas": 35, "bloco_coluna": 40, "reinsercao": 25}`; páginas alteradas: 45.

| Veículo | Δ quebras vs regra | Δ quebras vs híbrido | Δτ vs híbrido |
|---|---:|---:|---:|
| official_diary_ce | -2,789474 | -0,894737 | -0,013792 |
| official_diary_ma | -0,789474 | -0,315789 | 0,000166 |
| official_diary_rj | -7,076923 | -7,000000 | 0,000048 |

| Classe de sucessor | Reparos vs híbrido | Regressões vs híbrido |
|---|---:|---:|
| mesma_coluna | 49 | 4 |
| proxima_coluna | 0 | 0 |
| tabela_imagem | 1 | 0 |
| transversal | 15 | 0 |
| margem | 7 | 15 |
| outro | 85 | 1 |

### Corpo (diagnóstico por margens automáticas)

| Método | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|
| regra | 0,958613 | 24,404494 | 42,795159 | 0,837730 | 0,854708 |
| hibrido67 | 0,959083 | 23,494382 | 41,480164 | 0,846454 | 0,863272 |
| regra_reordena | 0,958665 | 23,404494 | 41,921330 | 0,844749 | 0,862817 |
| oraculo_residual | 0,959168 | 18,247191 | 35,067615 | 0,871761 | 0,891312 |
| e006_residual | 0,948352 | 21,865169 | 40,740980 | 0,849322 | 0,867741 |

## validacao_silver

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 macro / micro | Fid12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 15 / 1 | 0,957218 | 16,666667 | 10,284740 / 8,913609 | 0,952328 | 0,910859 | 100,0% |
| hibrido67 | 15 / 1 | 0,958656 | 16,400000 | 9,585398 / 8,770992 | 0,957104 | 0,916949 | 100,0% |
| oraculo_residual | 15 / 1 | 0,969152 | 6,333333 | 3,739462 / 3,387172 | 0,980504 | 0,968800 | 100,0% |
| e006_residual | 15 / 1 | 0,962330 | 13,733333 | 8,404603 / 7,344814 | 0,961586 | 0,928194 | 100,0% |

### Contrastes pareados

| Método | Referência | Métrica | Δ [IC95 veículo] | p veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|
| regra | hibrido67 | tau | -0,001439 [-0,001439; -0,001439] | 0,317311 | 1/13/1 |
| regra | hibrido67 | quebras | 0,266667 [0,266667; 0,266667] | 0,317311 | 0/13/2 |
| regra | hibrido67 | quebras_mil | 0,699342 [0,699342; 0,699342] | 0,317311 | 0/13/2 |
| regra | hibrido67 | fid12 | -0,004776 [-0,004776; -0,004776] | 0,317311 | 0/13/2 |
| regra | hibrido67 | sucessor_linhas | -0,006090 [-0,006090; -0,006090] | 0,317311 | 0/13/2 |
| hibrido67 | regra | tau | 0,001439 [0,001439; 0,001439] | 0,317311 | 1/13/1 |
| hibrido67 | regra | quebras | -0,266667 [-0,266667; -0,266667] | 0,317311 | 2/13/0 |
| hibrido67 | regra | quebras_mil | -0,699342 [-0,699342; -0,699342] | 0,317311 | 2/13/0 |
| hibrido67 | regra | fid12 | 0,004776 [0,004776; 0,004776] | 0,317311 | 2/13/0 |
| hibrido67 | regra | sucessor_linhas | 0,006090 [0,006090; 0,006090] | 0,317311 | 2/13/0 |
| oraculo_residual | regra | tau | 0,011934 [0,011934; 0,011934] | 0,317311 | 10/4/1 |
| oraculo_residual | regra | quebras | -10,333333 [-10,333333; -10,333333] | 0,317311 | 11/4/0 |
| oraculo_residual | regra | quebras_mil | -6,545277 [-6,545277; -6,545277] | 0,317311 | 11/4/0 |
| oraculo_residual | regra | fid12 | 0,028176 [0,028176; 0,028176] | 0,317311 | 11/4/0 |
| oraculo_residual | regra | sucessor_linhas | 0,057941 [0,057941; 0,057941] | 0,317311 | 11/4/0 |
| oraculo_residual | hibrido67 | tau | 0,010496 [0,010496; 0,010496] | 0,317311 | 10/5/0 |
| oraculo_residual | hibrido67 | quebras | -10,066667 [-10,066667; -10,066667] | 0,317311 | 10/5/0 |
| oraculo_residual | hibrido67 | quebras_mil | -5,845936 [-5,845936; -5,845936] | 0,317311 | 10/5/0 |
| oraculo_residual | hibrido67 | fid12 | 0,023400 [0,023400; 0,023400] | 0,317311 | 10/5/0 |
| oraculo_residual | hibrido67 | sucessor_linhas | 0,051851 [0,051851; 0,051851] | 0,317311 | 10/5/0 |
| e006_residual | regra | tau | 0,005112 [0,005112; 0,005112] | 0,317311 | 9/5/1 |
| e006_residual | regra | quebras | -2,933333 [-2,933333; -2,933333] | 0,317311 | 10/5/0 |
| e006_residual | regra | quebras_mil | -1,880136 [-1,880136; -1,880136] | 0,317311 | 10/5/0 |
| e006_residual | regra | fid12 | 0,009258 [0,009258; 0,009258] | 0,317311 | 10/5/0 |
| e006_residual | regra | sucessor_linhas | 0,017335 [0,017335; 0,017335] | 0,317311 | 10/5/0 |
| e006_residual | hibrido67 | tau | 0,003674 [0,003674; 0,003674] | 0,317311 | 10/4/1 |
| e006_residual | hibrido67 | quebras | -2,666667 [-2,666667; -2,666667] | 0,317311 | 9/4/2 |
| e006_residual | hibrido67 | quebras_mil | -1,180795 [-1,180795; -1,180795] | 0,317311 | 9/4/2 |
| e006_residual | hibrido67 | fid12 | 0,004482 [0,004482; 0,004482] | 0,317311 | 9/4/2 |
| e006_residual | hibrido67 | sucessor_linhas | 0,011245 [0,011245; 0,011245] | 0,317311 | 9/4/2 |

### Sucessores reparados e perdidos

| Método | Referência | Reparos | Regressões |
|---|---|---:|---:|
| regra | regra | 0 | 0 |
| regra | hibrido67 | 0 | 4 |
| hibrido67 | regra | 4 | 0 |
| hibrido67 | hibrido67 | 0 | 0 |
| oraculo_residual | regra | 155 | 0 |
| oraculo_residual | hibrido67 | 151 | 0 |
| e006_residual | regra | 44 | 0 |
| e006_residual | hibrido67 | 42 | 2 |

Operações do candidato: 23; por tipo: `{"reinsercao": 12, "bloco_coluna": 5, "vizinhas": 6}`; páginas alteradas: 11.

| Veículo | Δ quebras vs regra | Δ quebras vs híbrido | Δτ vs híbrido |
|---|---:|---:|---:|
| official_diary_rn | -2,933333 | -2,666667 | 0,003674 |

| Classe de sucessor | Reparos vs híbrido | Regressões vs híbrido |
|---|---:|---:|
| mesma_coluna | 9 | 0 |
| proxima_coluna | 0 | 0 |
| tabela_imagem | 0 | 0 |
| transversal | 0 | 0 |
| margem | 18 | 2 |
| outro | 15 | 0 |

### Corpo (diagnóstico por margens automáticas)

| Método | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|
| regra | 0,977603 | 11,200000 | 6,254538 | 0,972619 | 0,945747 |
| hibrido67 | 0,977564 | 11,200000 | 6,254538 | 0,972619 | 0,945747 |
| oraculo_residual | 0,978028 | 4,866667 | 2,677092 | 0,987504 | 0,978095 |
| e006_residual | 0,977611 | 9,600000 | 5,379503 | 0,977022 | 0,954202 |

## Veredito item a item (cartão E006)

**NÃO GO**.

- 1_menos_quebras_reordena_v4_e_v3: PASSA.
- 2a_delta_hibrido_nao_positivo_externas: PASSA.
- 2b_ic95_negativo_ao_menos_uma_externa: PASSA.
- 3_tau_margem_nas_tres: FALHA.
- 4_regressoes_ate_um_terco_reparos_em_cada_externa: FALHA.
