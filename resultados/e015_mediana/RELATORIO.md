1. Âncora reproduzida: golden_v4 τ 0,985948; 6,045455 quebras/página.
2. Salvaguarda fixa: τ de palavras mediana × regra < 0, sem referência; acionamentos no ajuste: golden_v4 0; validacao_silver 0.
3. golden_v3_novo: candidato τ 0,941737; quebras 6,518519; Δ vs híbrido -1,370370 [-2,558824; 0,230769].
4. teste_silver: candidato τ 0,955062; quebras 24,146067; Δ vs híbrido -2,280899 [-11,384615; -0,368421].
5. Modelo, mediana e salvaguarda sem novo ajuste; código e hashes congelados antes das externas; combinação só após o veredito.
6. Golden_v3_novo já foi consultado em rodadas anteriores; silver é ruidoso; resultado exploratório; teste cego preservado.

**Veredito do candidato (b)+salvaguarda: NÃO GO.**

## Protocolo e congelamento

Situação: Execução completa; exploração posterior ao veredito. Pico RSS 199,5 MiB. CPU, quatro threads, um processo, num_workers=0, sem treino ou GPU.

O E014 é importado para reconstruir o grafo E004 e a variante (b), medir cada ordem e resumir. Não há nova seleção. A salvaguarda usa as palavras de todas as unidades expandidas canonicamente pela bancada, com a regra como ordem de comparação; não lê a referência. O τ nos IDs de unidade é guardado apenas para diagnóstico, sem decidir o retorno. A entrada é embaralhada pelo protocolo com random.Random(f'entrada-{page_id}').

Estatística importada: 5000 reamostras, semente 20261004; médias principais por página, taxas macro por página e micro por palavra explicitadas. RN tem apenas um veículo e IC degenerado; híbrido RN é parcial nas páginas densas, pois faltam predições LayoutReader nas leves. As comparações externas exigem o híbrido completo. Valores de p são descritivos.

Congelado em 2026-11-03T03:56:20.494863+00:00; SHA256 do código `735eed5a53a209572aa5e90d6261dfd059df59fcd621eca2c399b03c8b53ca99`; assinatura `825ad4cf0a740012a0b9c74d1cf81b9728916ba5af84298df9733a036e6ce27d`. Evidência em `congelamento.json`, `cache/825ad4cf0a740012a0b9c74d1cf81b9728916ba5af84298df9733a036e6ce27d/codigo_congelado.py` e manifesto. Qualquer alteração de código/fontes impede retomar as externas.

## RN p40 — diagnóstico no ajuste

Página `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40`.

Regra: `['b4', 'b2', 'b1', 'b0', 'b6', 'b5', 'b3']`; mediana: `['b4', 'b2', 'b1', 'b0', 'b5', 'b3', 'b6']`; candidato: `['b4', 'b2', 'b1', 'b0', 'b5', 'b3', 'b6']`.

τ mediana × regra sem referência: palavras 0,012851; unidades 0,809524. Salvaguarda acionada: False.

| Cadeia de unidades | Postos na regra (base zero) | Mediana | Palavras |
|---|---|---:|---:|
| `['b4', 'b2', 'b1', 'b0', 'b5', 'b3']` | [0, 1, 2, 3, 5, 6] | 2,5 | 1752 |
| `['b6']` | [4] | 4,0 | 1744 |

| Unidade | Posto regra | Palavras | IDs de linha (início … fim) |
|---|---:|---:|---|
| b4 | 0 | 6 | silver:l0 |
| b2 | 1 | 9 | silver:l1 |
| b1 | 2 | 7 | silver:l2 |
| b0 | 3 | 1 | silver:l5 |
| b6 | 4 | 1744 | silver:l3, silver:l4, silver:l6 … silver:l1129, silver:l1130, silver:l1131 |
| b5 | 5 | 1 | silver:l1134 |
| b3 | 6 | 1728 | silver:l1132, silver:l1133, silver:l1135 … silver:l2267, silver:l2268, silver:l2269 |

A mediana pesa unidades igualmente. A cadeia que junta cabeçalho e o átomo final fica ancorada nos postos das unidades curtas do topo; ela é emitida inteira antes da outra cadeia. Assim, `b5`/`b3` passam à frente de `b6`, embora `b6` venha antes na regra. Os IDs de linha acima mostram a troca de duas grandes faixas do fluxo silver, não uma reversão literal de todas as linhas. O τ de palavras fica próximo de zero, mas positivo: a condição estrita `< 0` não detecta esta falha. Mesmo interpretar o teste nos IDs de unidade não acionaria a proteção nesta página.

| Método | τ palavras vs referência | Quebras/pág | Sucessor linhas |
|---|---:|---:|---:|
| regra | 0,999992 | 10,000000 | 0,995593 |
| b_mediana | 0,012843 | 10,000000 | 0,995593 |
| b_mediana_salvaguarda | 0,012843 | 10,000000 | 0,995593 |

## Efeito da salvaguarda no conjunto de ajuste

| Bancada | Páginas | Acionamentos | Δτ protegido − (b) | Δ quebras protegido − (b) |
|---|---:|---:|---:|---:|
| golden_v4 | 44 | 0 | 0,000000 | 0,000000 |
| validacao_silver | 15 | 0 | 0,000000 | 0,000000 |

## golden_v4 — ajuste

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 44 / 27 | 0,985948 | 6,045455 | 11,885 / 7,349 | 0,948129 | 0,927240 | 100,0% |
| hibrido67 | 44 / 27 | 0,979738 | 5,136364 | 6,041 / 6,244 | 0,973419 | 0,966143 | 100,0% |
| grafo_K24_maxregret_t0.00 | 44 / 27 | 0,937961 | 3,613636 | 7,778 / 4,393 | 0,963953 | 0,955269 | 100,0% |
| b_mediana | 44 / 27 | 0,986681 | 3,568182 | 7,278 / 4,338 | 0,965703 | 0,959057 | 100,0% |
| b_mediana_salvaguarda | 44 / 27 | 0,986681 | 3,568182 | 7,278 / 4,338 | 0,965703 | 0,959057 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | tau | 44 | -0,047987 [-0,147284; 0,003696] | 0,512256 | 16/19/9 |
| grafo_K24_maxregret_t0.00 | regra | quebras | 44 | -2,431818 [-4,139535; -1,162668] | 0,000513 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | 44 | -4,106956 [-8,299765; -1,291931] | 0,001055 | 20/22/2 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 44 | 0,015824 [0,006260; 0,026694] | 0,002085 | 19/23/2 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 44 | 0,028029 [0,008366; 0,056655] | 0,000835 | 21/21/2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | 44 | -0,041776 [-0,143114; 0,021494] | 0,932963 | 16/9/19 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | 44 | -1,522727 [-3,500000; -0,074869] | 0,069212 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | 44 | 1,736553 [-1,856740; 6,157636] | 0,952089 | 17/10/17 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 44 | -0,009466 [-0,039952; 0,013016] | 0,923364 | 18/11/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 44 | -0,010874 [-0,038913; 0,012273] | 0,971242 | 17/10/17 |
| b_mediana | regra | tau | 44 | 0,000732 [-0,005241; 0,006707] | 0,251724 | 17/20/7 |
| b_mediana | regra | quebras | 44 | -2,477273 [-4,190592; -1,200000] | 0,000240 | 20/23/1 |
| b_mediana | regra | quebras_mil | 44 | -4,606634 [-9,519562; -1,454718] | 0,000219 | 20/23/1 |
| b_mediana | regra | fid12 | 44 | 0,017574 [0,008374; 0,028446] | 0,000327 | 19/24/1 |
| b_mediana | regra | sucessor_linhas | 44 | 0,031817 [0,010625; 0,064814] | 0,000123 | 21/22/1 |
| b_mediana | hibrido67 | tau | 44 | 0,006943 [-0,010348; 0,034878] | 0,772894 | 16/10/18 |
| b_mediana | hibrido67 | quebras | 44 | -1,568182 [-3,538514; -0,139535] | 0,058695 | 17/11/16 |
| b_mediana | hibrido67 | quebras_mil | 44 | 1,236875 [-1,989710; 5,004735] | 0,754553 | 17/11/16 |
| b_mediana | hibrido67 | fid12 | 44 | -0,007715 [-0,037840; 0,014224] | 0,647336 | 18/12/14 |
| b_mediana | hibrido67 | sucessor_linhas | 44 | -0,007086 [-0,030987; 0,013811] | 0,718294 | 17/11/16 |
| b_mediana_salvaguarda | regra | tau | 44 | 0,000732 [-0,005241; 0,006707] | 0,251724 | 17/20/7 |
| b_mediana_salvaguarda | regra | quebras | 44 | -2,477273 [-4,190592; -1,200000] | 0,000240 | 20/23/1 |
| b_mediana_salvaguarda | regra | quebras_mil | 44 | -4,606634 [-9,519562; -1,454718] | 0,000219 | 20/23/1 |
| b_mediana_salvaguarda | regra | fid12 | 44 | 0,017574 [0,008374; 0,028446] | 0,000327 | 19/24/1 |
| b_mediana_salvaguarda | regra | sucessor_linhas | 44 | 0,031817 [0,010625; 0,064814] | 0,000123 | 21/22/1 |
| b_mediana_salvaguarda | hibrido67 | tau | 44 | 0,006943 [-0,010348; 0,034878] | 0,772894 | 16/10/18 |
| b_mediana_salvaguarda | hibrido67 | quebras | 44 | -1,568182 [-3,538514; -0,139535] | 0,058695 | 17/11/16 |
| b_mediana_salvaguarda | hibrido67 | quebras_mil | 44 | 1,236875 [-1,989710; 5,004735] | 0,754553 | 17/11/16 |
| b_mediana_salvaguarda | hibrido67 | fid12 | 44 | -0,007715 [-0,037840; 0,014224] | 0,647336 | 18/12/14 |
| b_mediana_salvaguarda | hibrido67 | sucessor_linhas | 44 | -0,007086 [-0,030987; 0,013811] | 0,718294 | 17/11/16 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | official_diary_MG_congonhas | -0,500000 | -0,006963 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_RJ_barra_do_pirai | -3,333333 | -0,006216 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_RJ_duque_de_caxias | -4,000000 | 0,010862 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_RJ_seropedica | 0,000000 | -0,003446 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ac | -3,500000 | 0,037050 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_al | 1,000000 | -0,010698 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_am_manaus | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ap | -1,500000 | 0,002522 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ba_salvador | 0,000000 | 0,009342 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ce | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ma | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_mg | -9,000000 | 0,000010 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ms | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_pb | -6,500000 | 0,018143 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_pe | -3,000000 | 0,000002 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_pi_v2 | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_pr_curitiba | 1,000000 | -0,313119 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rj | -29,000000 | 0,001411 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rj_japeri | -5,000000 | 0,025968 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rn | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ro | -3,000000 | 0,000159 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rr | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rs_porto_alegre | -1,500000 | 0,000100 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_sc | -3,000000 | 0,000006 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_se | -1,500000 | -0,030219 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_to | -1,000000 | -0,934256 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_MG_congonhas | 2,000000 | -0,007447 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_RJ_barra_do_pirai | 2,333333 | -0,036424 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_RJ_duque_de_caxias | -3,500000 | -0,057147 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_RJ_seropedica | 0,500000 | -0,003747 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ac | -2,500000 | 0,036993 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_al | 1,666667 | 0,005309 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_am_manaus | -3,000000 | 0,008900 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ap | -1,500000 | 0,002522 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ba_salvador | -6,000000 | 0,457322 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ce | 2,000000 | -0,000061 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ma | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_mg | -9,000000 | 0,000010 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ms | 1,000000 | -0,000568 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_pb | -7,000000 | 0,018134 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_pe | -3,000000 | 0,000002 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000581 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_pr_curitiba | 1,000000 | -0,313119 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rj | -29,000000 | 0,001411 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rj_japeri | -4,000000 | 0,022831 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rn | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ro | 1,500000 | -0,000079 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rr | 2,000000 | -0,000328 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rs_porto_alegre | -1,000000 | 0,003174 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_sc | -3,000000 | 0,000006 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_se | -1,500000 | -0,030219 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_to | -1,000000 | -0,934256 |
| b_mediana | regra | official_diary_MG_congonhas | -0,500000 | -0,005222 |
| b_mediana | regra | official_diary_RJ_barra_do_pirai | -3,666667 | -0,001696 |
| b_mediana | regra | official_diary_RJ_duque_de_caxias | -4,000000 | 0,010862 |
| b_mediana | regra | official_diary_RJ_seropedica | 0,000000 | -0,003446 |
| b_mediana | regra | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| b_mediana | regra | official_diary_ac | -3,500000 | 0,037050 |
| b_mediana | regra | official_diary_al | 1,000000 | -0,010698 |
| b_mediana | regra | official_diary_am_manaus | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_ap | -1,500000 | 0,002522 |
| b_mediana | regra | official_diary_ba_salvador | 0,000000 | 0,009342 |
| b_mediana | regra | official_diary_ce | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_ma | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_mg | -9,000000 | 0,000010 |
| b_mediana | regra | official_diary_ms | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_pb | -6,500000 | 0,018143 |
| b_mediana | regra | official_diary_pe | -3,000000 | 0,000002 |
| b_mediana | regra | official_diary_pi_v2 | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_rj | -29,000000 | 0,001411 |
| b_mediana | regra | official_diary_rj_japeri | -5,000000 | 0,025968 |
| b_mediana | regra | official_diary_rn | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_ro | -3,000000 | 0,000159 |
| b_mediana | regra | official_diary_rr | 0,000000 | 0,000000 |
| b_mediana | regra | official_diary_rs_porto_alegre | -1,500000 | 0,000100 |
| b_mediana | regra | official_diary_sc | -3,000000 | 0,000006 |
| b_mediana | regra | official_diary_se | -1,500000 | -0,030219 |
| b_mediana | regra | official_diary_to | -1,000000 | -0,027511 |
| b_mediana | hibrido67 | official_diary_MG_congonhas | 2,000000 | -0,005706 |
| b_mediana | hibrido67 | official_diary_RJ_barra_do_pirai | 2,000000 | -0,031904 |
| b_mediana | hibrido67 | official_diary_RJ_duque_de_caxias | -3,500000 | -0,057147 |
| b_mediana | hibrido67 | official_diary_RJ_seropedica | 0,500000 | -0,003747 |
| b_mediana | hibrido67 | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| b_mediana | hibrido67 | official_diary_ac | -2,500000 | 0,036993 |
| b_mediana | hibrido67 | official_diary_al | 1,666667 | 0,005309 |
| b_mediana | hibrido67 | official_diary_am_manaus | -3,000000 | 0,008900 |
| b_mediana | hibrido67 | official_diary_ap | -1,500000 | 0,002522 |
| b_mediana | hibrido67 | official_diary_ba_salvador | -6,000000 | 0,457322 |
| b_mediana | hibrido67 | official_diary_ce | 2,000000 | -0,000061 |
| b_mediana | hibrido67 | official_diary_ma | 0,000000 | 0,000000 |
| b_mediana | hibrido67 | official_diary_mg | -9,000000 | 0,000010 |
| b_mediana | hibrido67 | official_diary_ms | 1,000000 | -0,000568 |
| b_mediana | hibrido67 | official_diary_pb | -7,000000 | 0,018134 |
| b_mediana | hibrido67 | official_diary_pe | -3,000000 | 0,000002 |
| b_mediana | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000581 |
| b_mediana | hibrido67 | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| b_mediana | hibrido67 | official_diary_rj | -29,000000 | 0,001411 |
| b_mediana | hibrido67 | official_diary_rj_japeri | -4,000000 | 0,022831 |
| b_mediana | hibrido67 | official_diary_rn | 0,000000 | 0,000000 |
| b_mediana | hibrido67 | official_diary_ro | 1,500000 | -0,000079 |
| b_mediana | hibrido67 | official_diary_rr | 2,000000 | -0,000328 |
| b_mediana | hibrido67 | official_diary_rs_porto_alegre | -1,000000 | 0,003174 |
| b_mediana | hibrido67 | official_diary_sc | -3,000000 | 0,000006 |
| b_mediana | hibrido67 | official_diary_se | -1,500000 | -0,030219 |
| b_mediana | hibrido67 | official_diary_to | -1,000000 | -0,027511 |
| b_mediana_salvaguarda | regra | official_diary_MG_congonhas | -0,500000 | -0,005222 |
| b_mediana_salvaguarda | regra | official_diary_RJ_barra_do_pirai | -3,666667 | -0,001696 |
| b_mediana_salvaguarda | regra | official_diary_RJ_duque_de_caxias | -4,000000 | 0,010862 |
| b_mediana_salvaguarda | regra | official_diary_RJ_seropedica | 0,000000 | -0,003446 |
| b_mediana_salvaguarda | regra | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| b_mediana_salvaguarda | regra | official_diary_ac | -3,500000 | 0,037050 |
| b_mediana_salvaguarda | regra | official_diary_al | 1,000000 | -0,010698 |
| b_mediana_salvaguarda | regra | official_diary_am_manaus | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_ap | -1,500000 | 0,002522 |
| b_mediana_salvaguarda | regra | official_diary_ba_salvador | 0,000000 | 0,009342 |
| b_mediana_salvaguarda | regra | official_diary_ce | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_ma | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_mg | -9,000000 | 0,000010 |
| b_mediana_salvaguarda | regra | official_diary_ms | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_pb | -6,500000 | 0,018143 |
| b_mediana_salvaguarda | regra | official_diary_pe | -3,000000 | 0,000002 |
| b_mediana_salvaguarda | regra | official_diary_pi_v2 | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_rj | -29,000000 | 0,001411 |
| b_mediana_salvaguarda | regra | official_diary_rj_japeri | -5,000000 | 0,025968 |
| b_mediana_salvaguarda | regra | official_diary_rn | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_ro | -3,000000 | 0,000159 |
| b_mediana_salvaguarda | regra | official_diary_rr | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | regra | official_diary_rs_porto_alegre | -1,500000 | 0,000100 |
| b_mediana_salvaguarda | regra | official_diary_sc | -3,000000 | 0,000006 |
| b_mediana_salvaguarda | regra | official_diary_se | -1,500000 | -0,030219 |
| b_mediana_salvaguarda | regra | official_diary_to | -1,000000 | -0,027511 |
| b_mediana_salvaguarda | hibrido67 | official_diary_MG_congonhas | 2,000000 | -0,005706 |
| b_mediana_salvaguarda | hibrido67 | official_diary_RJ_barra_do_pirai | 2,000000 | -0,031904 |
| b_mediana_salvaguarda | hibrido67 | official_diary_RJ_duque_de_caxias | -3,500000 | -0,057147 |
| b_mediana_salvaguarda | hibrido67 | official_diary_RJ_seropedica | 0,500000 | -0,003747 |
| b_mediana_salvaguarda | hibrido67 | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ac | -2,500000 | 0,036993 |
| b_mediana_salvaguarda | hibrido67 | official_diary_al | 1,666667 | 0,005309 |
| b_mediana_salvaguarda | hibrido67 | official_diary_am_manaus | -3,000000 | 0,008900 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ap | -1,500000 | 0,002522 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ba_salvador | -6,000000 | 0,457322 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ce | 2,000000 | -0,000061 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ma | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | hibrido67 | official_diary_mg | -9,000000 | 0,000010 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ms | 1,000000 | -0,000568 |
| b_mediana_salvaguarda | hibrido67 | official_diary_pb | -7,000000 | 0,018134 |
| b_mediana_salvaguarda | hibrido67 | official_diary_pe | -3,000000 | 0,000002 |
| b_mediana_salvaguarda | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000581 |
| b_mediana_salvaguarda | hibrido67 | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rj | -29,000000 | 0,001411 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rj_japeri | -4,000000 | 0,022831 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rn | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ro | 1,500000 | -0,000079 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rr | 2,000000 | -0,000328 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rs_porto_alegre | -1,000000 | 0,003174 |
| b_mediana_salvaguarda | hibrido67 | official_diary_sc | -3,000000 | 0,000006 |
| b_mediana_salvaguarda | hibrido67 | official_diary_se | -1,500000 | -0,030219 |
| b_mediana_salvaguarda | hibrido67 | official_diary_to | -1,000000 | -0,027511 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 33 | 0 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 11 | 1 |
| grafo_K24_maxregret_t0.00 | regra | margem | 51 | 4 |
| grafo_K24_maxregret_t0.00 | regra | outro | 17 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 30 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 11 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 11 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 45 | 35 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 10 | 3 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana | regra | mesma_coluna | 33 | 0 |
| b_mediana | regra | proxima_coluna | 0 | 1 |
| b_mediana | regra | tabela_imagem | 0 | 0 |
| b_mediana | regra | transversal | 11 | 1 |
| b_mediana | regra | margem | 52 | 4 |
| b_mediana | regra | outro | 17 | 0 |
| b_mediana | hibrido67 | mesma_coluna | 30 | 3 |
| b_mediana | hibrido67 | proxima_coluna | 0 | 1 |
| b_mediana | hibrido67 | tabela_imagem | 11 | 1 |
| b_mediana | hibrido67 | transversal | 11 | 1 |
| b_mediana | hibrido67 | margem | 45 | 34 |
| b_mediana | hibrido67 | outro | 10 | 2 |
| b_mediana | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | margem | 1 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | outro | 1 | 0 |
| b_mediana_salvaguarda | regra | mesma_coluna | 33 | 0 |
| b_mediana_salvaguarda | regra | proxima_coluna | 0 | 1 |
| b_mediana_salvaguarda | regra | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | regra | transversal | 11 | 1 |
| b_mediana_salvaguarda | regra | margem | 52 | 4 |
| b_mediana_salvaguarda | regra | outro | 17 | 0 |
| b_mediana_salvaguarda | hibrido67 | mesma_coluna | 30 | 3 |
| b_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 1 |
| b_mediana_salvaguarda | hibrido67 | tabela_imagem | 11 | 1 |
| b_mediana_salvaguarda | hibrido67 | transversal | 11 | 1 |
| b_mediana_salvaguarda | hibrido67 | margem | 45 | 34 |
| b_mediana_salvaguarda | hibrido67 | outro | 10 | 2 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 1 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 1 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 44 | 0,993467 | 2,931818 | 0,985674 | 0,977845 |
| hibrido67 | 44 | 0,986295 | 2,772727 | 0,988822 | 0,985116 |
| grafo_K24_maxregret_t0.00 | 44 | 0,940957 | 1,568182 | 0,990664 | 0,985138 |
| b_mediana | 44 | 0,993270 | 1,500000 | 0,992335 | 0,987092 |
| b_mediana_salvaguarda | 44 | 0,993270 | 1,500000 | 0,992335 | 0,987092 |

## validacao_silver — ajuste

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 15 / 1 | 0,957218 | 16,666667 | 10,285 / 8,914 | 0,952328 | 0,910859 | 100,0% |
| hibrido67 (parcial) | 13 / 1 | 0,958544 | 17,846154 | 9,554 / 9,564 | 0,955769 | 0,916132 | 100,0% |
| grafo_K24_maxregret_t0.00 | 15 / 1 | 0,686666 | 9,466667 | 6,132 / 5,063 | 0,970249 | 0,947916 | 100,0% |
| b_mediana | 15 / 1 | 0,891034 | 9,266667 | 6,032 / 4,956 | 0,971302 | 0,948742 | 100,0% |
| b_mediana_salvaguarda | 15 / 1 | 0,891034 | 9,266667 | 6,032 / 4,956 | 0,971302 | 0,948742 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | tau | 15 | -0,270551 [-0,270551; -0,270551] | 0,317311 | 3/4/8 |
| grafo_K24_maxregret_t0.00 | regra | quebras | 15 | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | 15 | -4,152893 [-4,152893; -4,152893] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 15 | 0,017921 [0,017921; 0,017921] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 15 | 0,037057 [0,037057; 0,037057] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | 13 | -0,170445 [-0,170445; -0,170445] | 0,317311 | 3/4/6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | 13 | -8,153846 [-8,153846; -8,153846] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | 13 | -4,268513 [-4,268513; -4,268513] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 13 | 0,018070 [0,018070; 0,018070] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 13 | 0,038096 [0,038096; 0,038096] | 0,317311 | 9/4/0 |
| b_mediana | regra | tau | 15 | -0,066184 [-0,066184; -0,066184] | 0,317311 | 7/4/4 |
| b_mediana | regra | quebras | 15 | -7,400000 [-7,400000; -7,400000] | 0,317311 | 10/5/0 |
| b_mediana | regra | quebras_mil | 15 | -4,252268 [-4,252268; -4,252268] | 0,317311 | 10/5/0 |
| b_mediana | regra | fid12 | 15 | 0,018974 [0,018974; 0,018974] | 0,317311 | 10/5/0 |
| b_mediana | regra | sucessor_linhas | 15 | 0,037883 [0,037883; 0,037883] | 0,317311 | 10/5/0 |
| b_mediana | hibrido67 | tau | 13 | 0,000555 [0,000555; 0,000555] | 0,317311 | 7/4/2 |
| b_mediana | hibrido67 | quebras | 13 | -8,384615 [-8,384615; -8,384615] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | quebras_mil | 13 | -4,383177 [-4,383177; -4,383177] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | fid12 | 13 | 0,019286 [0,019286; 0,019286] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | sucessor_linhas | 13 | 0,039050 [0,039050; 0,039050] | 0,317311 | 9/4/0 |
| b_mediana_salvaguarda | regra | tau | 15 | -0,066184 [-0,066184; -0,066184] | 0,317311 | 7/4/4 |
| b_mediana_salvaguarda | regra | quebras | 15 | -7,400000 [-7,400000; -7,400000] | 0,317311 | 10/5/0 |
| b_mediana_salvaguarda | regra | quebras_mil | 15 | -4,252268 [-4,252268; -4,252268] | 0,317311 | 10/5/0 |
| b_mediana_salvaguarda | regra | fid12 | 15 | 0,018974 [0,018974; 0,018974] | 0,317311 | 10/5/0 |
| b_mediana_salvaguarda | regra | sucessor_linhas | 15 | 0,037883 [0,037883; 0,037883] | 0,317311 | 10/5/0 |
| b_mediana_salvaguarda | hibrido67 | tau | 13 | 0,000555 [0,000555; 0,000555] | 0,317311 | 7/4/2 |
| b_mediana_salvaguarda | hibrido67 | quebras | 13 | -8,384615 [-8,384615; -8,384615] | 0,317311 | 9/4/0 |
| b_mediana_salvaguarda | hibrido67 | quebras_mil | 13 | -4,383177 [-4,383177; -4,383177] | 0,317311 | 9/4/0 |
| b_mediana_salvaguarda | hibrido67 | fid12 | 13 | 0,019286 [0,019286; 0,019286] | 0,317311 | 9/4/0 |
| b_mediana_salvaguarda | hibrido67 | sucessor_linhas | 13 | 0,039050 [0,039050; 0,039050] | 0,317311 | 9/4/0 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | official_diary_rn | -7,200000 | -0,270551 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rn | -8,153846 | -0,170445 |
| b_mediana | regra | official_diary_rn | -7,400000 | -0,066184 |
| b_mediana | hibrido67 | official_diary_rn | -8,384615 | 0,000555 |
| b_mediana_salvaguarda | regra | official_diary_rn | -7,400000 | -0,066184 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rn | -8,384615 | 0,000555 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 17 | 0 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 1 | 0 |
| grafo_K24_maxregret_t0.00 | regra | margem | 38 | 0 |
| grafo_K24_maxregret_t0.00 | regra | outro | 53 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 17 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 1 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 36 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 53 | 1 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana | regra | mesma_coluna | 17 | 0 |
| b_mediana | regra | proxima_coluna | 0 | 0 |
| b_mediana | regra | tabela_imagem | 0 | 0 |
| b_mediana | regra | transversal | 1 | 0 |
| b_mediana | regra | margem | 41 | 0 |
| b_mediana | regra | outro | 53 | 1 |
| b_mediana | hibrido67 | mesma_coluna | 17 | 0 |
| b_mediana | hibrido67 | proxima_coluna | 0 | 0 |
| b_mediana | hibrido67 | tabela_imagem | 0 | 0 |
| b_mediana | hibrido67 | transversal | 1 | 0 |
| b_mediana | hibrido67 | margem | 39 | 0 |
| b_mediana | hibrido67 | outro | 53 | 1 |
| b_mediana | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | margem | 3 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana_salvaguarda | regra | mesma_coluna | 17 | 0 |
| b_mediana_salvaguarda | regra | proxima_coluna | 0 | 0 |
| b_mediana_salvaguarda | regra | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | regra | transversal | 1 | 0 |
| b_mediana_salvaguarda | regra | margem | 41 | 0 |
| b_mediana_salvaguarda | regra | outro | 53 | 1 |
| b_mediana_salvaguarda | hibrido67 | mesma_coluna | 17 | 0 |
| b_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 0 |
| b_mediana_salvaguarda | hibrido67 | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | hibrido67 | transversal | 1 | 0 |
| b_mediana_salvaguarda | hibrido67 | margem | 39 | 0 |
| b_mediana_salvaguarda | hibrido67 | outro | 53 | 1 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 3 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 15 | 0,977603 | 11,200000 | 0,972619 | 0,945747 |
| hibrido67 | 13 | 0,974157 | 12,230769 | 0,968886 | 0,937706 |
| grafo_K24_maxregret_t0.00 | 15 | 0,684942 | 6,933333 | 0,977618 | 0,965229 |
| b_mediana | 15 | 0,902498 | 6,533333 | 0,982103 | 0,969539 |
| b_mediana_salvaguarda | 15 | 0,902498 | 6,533333 | 0,982103 | 0,969539 |

## golden_v3_novo — externa

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 27 / 10 | 0,959557 | 9,222222 | 17,206 / 10,461 | 0,928415 | 0,911301 | 100,0% |
| hibrido67 | 27 / 10 | 0,958977 | 7,888889 | 13,739 / 8,948 | 0,941220 | 0,938410 | 100,0% |
| grafo_K24_maxregret_t0.00 | 27 / 10 | 0,941737 | 6,518519 | 12,942 / 7,394 | 0,941194 | 0,935275 | 100,0% |
| b_mediana | 27 / 10 | 0,941737 | 6,518519 | 12,942 / 7,394 | 0,941194 | 0,935275 | 100,0% |
| b_mediana_salvaguarda | 27 / 10 | 0,941737 | 6,518519 | 12,942 / 7,394 | 0,941194 | 0,935275 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | tau | 27 | -0,017820 [-0,052402; 0,001460] | 0,721277 | 10/11/6 |
| grafo_K24_maxregret_t0.00 | regra | quebras | 27 | -2,703704 [-3,263158; -2,153750] | 0,005698 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | 27 | -4,264012 [-7,004880; -2,758572] | 0,005857 | 13/12/2 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 27 | 0,012779 [0,005176; 0,017981] | 0,102470 | 11/12/4 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 27 | 0,023974 [0,009214; 0,040091] | 0,074462 | 13/11/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | 27 | -0,017240 [-0,052709; 0,004620] | 0,307434 | 6/11/10 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | 27 | -1,370370 [-2,558824; 0,230769] | 0,258449 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | 27 | -0,797723 [-2,973005; 2,672809] | 0,681519 | 9/13/5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 27 | -0,000026 [-0,018935; 0,009917] | 0,474959 | 8/11/8 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 27 | -0,003134 [-0,030139; 0,010360] | 0,759463 | 9/12/6 |
| b_mediana | regra | tau | 27 | -0,017820 [-0,052402; 0,001460] | 0,721277 | 10/11/6 |
| b_mediana | regra | quebras | 27 | -2,703704 [-3,263158; -2,153750] | 0,005698 | 13/12/2 |
| b_mediana | regra | quebras_mil | 27 | -4,264012 [-7,004880; -2,758572] | 0,005857 | 13/12/2 |
| b_mediana | regra | fid12 | 27 | 0,012779 [0,005176; 0,017981] | 0,102470 | 11/12/4 |
| b_mediana | regra | sucessor_linhas | 27 | 0,023974 [0,009214; 0,040091] | 0,074462 | 13/11/3 |
| b_mediana | hibrido67 | tau | 27 | -0,017240 [-0,052709; 0,004620] | 0,307434 | 6/11/10 |
| b_mediana | hibrido67 | quebras | 27 | -1,370370 [-2,558824; 0,230769] | 0,258449 | 9/13/5 |
| b_mediana | hibrido67 | quebras_mil | 27 | -0,797723 [-2,973005; 2,672809] | 0,681519 | 9/13/5 |
| b_mediana | hibrido67 | fid12 | 27 | -0,000026 [-0,018935; 0,009917] | 0,474959 | 8/11/8 |
| b_mediana | hibrido67 | sucessor_linhas | 27 | -0,003134 [-0,030139; 0,010360] | 0,759463 | 9/12/6 |
| b_mediana_salvaguarda | regra | tau | 27 | -0,017820 [-0,052402; 0,001460] | 0,721277 | 10/11/6 |
| b_mediana_salvaguarda | regra | quebras | 27 | -2,703704 [-3,263158; -2,153750] | 0,005698 | 13/12/2 |
| b_mediana_salvaguarda | regra | quebras_mil | 27 | -4,264012 [-7,004880; -2,758572] | 0,005857 | 13/12/2 |
| b_mediana_salvaguarda | regra | fid12 | 27 | 0,012779 [0,005176; 0,017981] | 0,102470 | 11/12/4 |
| b_mediana_salvaguarda | regra | sucessor_linhas | 27 | 0,023974 [0,009214; 0,040091] | 0,074462 | 13/11/3 |
| b_mediana_salvaguarda | hibrido67 | tau | 27 | -0,017240 [-0,052709; 0,004620] | 0,307434 | 6/11/10 |
| b_mediana_salvaguarda | hibrido67 | quebras | 27 | -1,370370 [-2,558824; 0,230769] | 0,258449 | 9/13/5 |
| b_mediana_salvaguarda | hibrido67 | quebras_mil | 27 | -0,797723 [-2,973005; 2,672809] | 0,681519 | 9/13/5 |
| b_mediana_salvaguarda | hibrido67 | fid12 | 27 | -0,000026 [-0,018935; 0,009917] | 0,474959 | 8/11/8 |
| b_mediana_salvaguarda | hibrido67 | sucessor_linhas | 27 | -0,003134 [-0,030139; 0,010360] | 0,759463 | 9/12/6 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ac | -1,500000 | 0,005043 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ap | 0,000000 | -0,005388 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ce | -2,833333 | 0,000106 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ma | -2,428571 | -0,000368 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_mg | -4,000000 | 0,000215 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_pi_v2 | -1,500000 | 0,000007 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rj | -3,600000 | -0,097855 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ro | -3,000000 | 0,000194 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_se | -4,000000 | 0,004268 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ac | 1,000000 | -0,012428 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ap | 0,000000 | -0,005388 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ce | -0,166667 | 0,009416 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ma | -2,428571 | -0,000368 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_mg | -4,000000 | 0,000215 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000367 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rj | -3,600000 | -0,097857 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ro | 0,000000 | 0,000000 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_se | 1,000000 | -0,000032 |
| b_mediana | regra | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| b_mediana | regra | official_diary_ac | -1,500000 | 0,005043 |
| b_mediana | regra | official_diary_ap | 0,000000 | -0,005388 |
| b_mediana | regra | official_diary_ce | -2,833333 | 0,000106 |
| b_mediana | regra | official_diary_ma | -2,428571 | -0,000368 |
| b_mediana | regra | official_diary_mg | -4,000000 | 0,000215 |
| b_mediana | regra | official_diary_pi_v2 | -1,500000 | 0,000007 |
| b_mediana | regra | official_diary_rj | -3,600000 | -0,097855 |
| b_mediana | regra | official_diary_ro | -3,000000 | 0,000194 |
| b_mediana | regra | official_diary_se | -4,000000 | 0,004268 |
| b_mediana | hibrido67 | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| b_mediana | hibrido67 | official_diary_ac | 1,000000 | -0,012428 |
| b_mediana | hibrido67 | official_diary_ap | 0,000000 | -0,005388 |
| b_mediana | hibrido67 | official_diary_ce | -0,166667 | 0,009416 |
| b_mediana | hibrido67 | official_diary_ma | -2,428571 | -0,000368 |
| b_mediana | hibrido67 | official_diary_mg | -4,000000 | 0,000215 |
| b_mediana | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000367 |
| b_mediana | hibrido67 | official_diary_rj | -3,600000 | -0,097857 |
| b_mediana | hibrido67 | official_diary_ro | 0,000000 | 0,000000 |
| b_mediana | hibrido67 | official_diary_se | 1,000000 | -0,000032 |
| b_mediana_salvaguarda | regra | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| b_mediana_salvaguarda | regra | official_diary_ac | -1,500000 | 0,005043 |
| b_mediana_salvaguarda | regra | official_diary_ap | 0,000000 | -0,005388 |
| b_mediana_salvaguarda | regra | official_diary_ce | -2,833333 | 0,000106 |
| b_mediana_salvaguarda | regra | official_diary_ma | -2,428571 | -0,000368 |
| b_mediana_salvaguarda | regra | official_diary_mg | -4,000000 | 0,000215 |
| b_mediana_salvaguarda | regra | official_diary_pi_v2 | -1,500000 | 0,000007 |
| b_mediana_salvaguarda | regra | official_diary_rj | -3,600000 | -0,097855 |
| b_mediana_salvaguarda | regra | official_diary_ro | -3,000000 | 0,000194 |
| b_mediana_salvaguarda | regra | official_diary_se | -4,000000 | 0,004268 |
| b_mediana_salvaguarda | hibrido67 | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ac | 1,000000 | -0,012428 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ap | 0,000000 | -0,005388 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ce | -0,166667 | 0,009416 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ma | -2,428571 | -0,000368 |
| b_mediana_salvaguarda | hibrido67 | official_diary_mg | -4,000000 | 0,000215 |
| b_mediana_salvaguarda | hibrido67 | official_diary_pi_v2 | 2,000000 | -0,000367 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rj | -3,600000 | -0,097857 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ro | 0,000000 | 0,000000 |
| b_mediana_salvaguarda | hibrido67 | official_diary_se | 1,000000 | -0,000032 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 32 | 3 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 3 | 2 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | regra | margem | 11 | 3 |
| grafo_K24_maxregret_t0.00 | regra | outro | 32 | 2 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 25 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 1 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 3 | 3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 7 | 5 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 16 | 3 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana | regra | mesma_coluna | 32 | 3 |
| b_mediana | regra | proxima_coluna | 0 | 1 |
| b_mediana | regra | tabela_imagem | 3 | 2 |
| b_mediana | regra | transversal | 0 | 0 |
| b_mediana | regra | margem | 11 | 3 |
| b_mediana | regra | outro | 32 | 2 |
| b_mediana | hibrido67 | mesma_coluna | 25 | 6 |
| b_mediana | hibrido67 | proxima_coluna | 0 | 1 |
| b_mediana | hibrido67 | tabela_imagem | 3 | 3 |
| b_mediana | hibrido67 | transversal | 0 | 0 |
| b_mediana | hibrido67 | margem | 7 | 5 |
| b_mediana | hibrido67 | outro | 16 | 3 |
| b_mediana | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana_salvaguarda | regra | mesma_coluna | 32 | 3 |
| b_mediana_salvaguarda | regra | proxima_coluna | 0 | 1 |
| b_mediana_salvaguarda | regra | tabela_imagem | 3 | 2 |
| b_mediana_salvaguarda | regra | transversal | 0 | 0 |
| b_mediana_salvaguarda | regra | margem | 11 | 3 |
| b_mediana_salvaguarda | regra | outro | 32 | 2 |
| b_mediana_salvaguarda | hibrido67 | mesma_coluna | 25 | 6 |
| b_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 1 |
| b_mediana_salvaguarda | hibrido67 | tabela_imagem | 3 | 3 |
| b_mediana_salvaguarda | hibrido67 | transversal | 0 | 0 |
| b_mediana_salvaguarda | hibrido67 | margem | 7 | 5 |
| b_mediana_salvaguarda | hibrido67 | outro | 16 | 3 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 27 | 0,959496 | 7,703704 | 0,936030 | 0,925058 |
| hibrido67 | 27 | 0,960716 | 6,555556 | 0,947488 | 0,949111 |
| grafo_K24_maxregret_t0.00 | 27 | 0,940307 | 5,370370 | 0,947788 | 0,943730 |
| b_mediana | 27 | 0,940307 | 5,370370 | 0,947788 | 0,943730 |
| b_mediana_salvaguarda | 27 | 0,940307 | 5,370370 | 0,947788 | 0,943730 |

## teste_silver — externa

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 89 / 3 | 0,959565 | 27,449438 | 44,496 / 25,632 | 0,825401 | 0,840212 | 100,0% |
| hibrido67 | 89 / 3 | 0,959092 | 26,426966 | 43,157 / 24,677 | 0,834332 | 0,849525 | 100,0% |
| grafo_K24_maxregret_t0.00 | 89 / 3 | 0,942613 | 24,146067 | 41,817 / 22,547 | 0,838883 | 0,854450 | 100,0% |
| b_mediana | 89 / 3 | 0,955062 | 24,146067 | 41,822 / 22,547 | 0,839043 | 0,854519 | 100,0% |
| b_mediana_salvaguarda | 89 / 3 | 0,955062 | 24,146067 | 41,822 / 22,547 | 0,839043 | 0,854519 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | tau | 89 | -0,016953 [-0,043074; -0,000940] | 0,108809 | 21/53/15 |
| grafo_K24_maxregret_t0.00 | regra | quebras | 89 | -3,303371 [-11,384615; -0,815789] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | quebras_mil | 89 | -2,678536 [-5,533066; -1,488111] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | regra | fid12 | 89 | 0,013482 [0,003029; 0,036290] | 0,108809 | 28/57/4 |
| grafo_K24_maxregret_t0.00 | regra | sucessor_linhas | 89 | 0,014239 [0,006451; 0,022996] | 0,108809 | 31/55/3 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tau | 89 | -0,016479 [-0,043095; 0,000658] | 0,285049 | 21/43/25 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras | 89 | -2,280899 [-11,307692; -0,342105] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | quebras_mil | 89 | -1,340228 [-5,481091; -0,218504] | 0,108809 | 25/50/14 |
| grafo_K24_maxregret_t0.00 | hibrido67 | fid12 | 89 | 0,004550 [-0,007345; 0,036013] | 0,592980 | 20/54/15 |
| grafo_K24_maxregret_t0.00 | hibrido67 | sucessor_linhas | 89 | 0,004926 [-0,004019; 0,022918] | 0,285049 | 25/50/14 |
| b_mediana | regra | tau | 89 | -0,004503 [-0,040418; 0,003662] | 0,592980 | 24/54/11 |
| b_mediana | regra | quebras | 89 | -3,303371 [-11,461538; -0,842105] | 0,108809 | 32/55/2 |
| b_mediana | regra | quebras_mil | 89 | -2,673865 [-5,565606; -1,527984] | 0,108809 | 32/55/2 |
| b_mediana | regra | fid12 | 89 | 0,013642 [0,003029; 0,036453] | 0,108809 | 29/57/3 |
| b_mediana | regra | sucessor_linhas | 89 | 0,014308 [0,006728; 0,023216] | 0,108809 | 32/55/2 |
| b_mediana | hibrido67 | tau | 89 | -0,004030 [-0,040438; 0,003179] | 1,000000 | 24/44/21 |
| b_mediana | hibrido67 | quebras | 89 | -2,280899 [-11,384615; -0,368421] | 0,108809 | 26/50/13 |
| b_mediana | hibrido67 | quebras_mil | 89 | -1,335557 [-5,513631; -0,258377] | 0,108809 | 26/50/13 |
| b_mediana | hibrido67 | fid12 | 89 | 0,004710 [-0,007345; 0,036177] | 0,592980 | 21/54/14 |
| b_mediana | hibrido67 | sucessor_linhas | 89 | 0,004995 [-0,003742; 0,023138] | 0,285049 | 26/50/13 |
| b_mediana_salvaguarda | regra | tau | 89 | -0,004503 [-0,040418; 0,003662] | 0,592980 | 24/54/11 |
| b_mediana_salvaguarda | regra | quebras | 89 | -3,303371 [-11,461538; -0,842105] | 0,108809 | 32/55/2 |
| b_mediana_salvaguarda | regra | quebras_mil | 89 | -2,673865 [-5,565606; -1,527984] | 0,108809 | 32/55/2 |
| b_mediana_salvaguarda | regra | fid12 | 89 | 0,013642 [0,003029; 0,036453] | 0,108809 | 29/57/3 |
| b_mediana_salvaguarda | regra | sucessor_linhas | 89 | 0,014308 [0,006728; 0,023216] | 0,108809 | 32/55/2 |
| b_mediana_salvaguarda | hibrido67 | tau | 89 | -0,004030 [-0,040438; 0,003179] | 1,000000 | 24/44/21 |
| b_mediana_salvaguarda | hibrido67 | quebras | 89 | -2,280899 [-11,384615; -0,368421] | 0,108809 | 26/50/13 |
| b_mediana_salvaguarda | hibrido67 | quebras_mil | 89 | -1,335557 [-5,513631; -0,258377] | 0,108809 | 26/50/13 |
| b_mediana_salvaguarda | hibrido67 | fid12 | 89 | 0,004710 [-0,007345; 0,036177] | 0,592980 | 21/54/14 |
| b_mediana_salvaguarda | hibrido67 | sucessor_linhas | 89 | 0,004995 [-0,003742; 0,023138] | 0,285049 | 26/50/13 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | official_diary_ce | -3,026316 | -0,000940 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_ma | -0,815789 | -0,024029 |
| grafo_K24_maxregret_t0.00 | regra | official_diary_rj | -11,384615 | -0,043074 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ce | -1,131579 | 0,000658 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_ma | -0,342105 | -0,024512 |
| grafo_K24_maxregret_t0.00 | hibrido67 | official_diary_rj | -11,307692 | -0,043095 |
| b_mediana | regra | official_diary_ce | -2,973684 | -0,000382 |
| b_mediana | regra | official_diary_ma | -0,842105 | 0,003662 |
| b_mediana | regra | official_diary_rj | -11,461538 | -0,040418 |
| b_mediana | hibrido67 | official_diary_ce | -1,078947 | 0,001216 |
| b_mediana | hibrido67 | official_diary_ma | -0,368421 | 0,003179 |
| b_mediana | hibrido67 | official_diary_rj | -11,384615 | -0,040438 |
| b_mediana_salvaguarda | regra | official_diary_ce | -2,973684 | -0,000382 |
| b_mediana_salvaguarda | regra | official_diary_ma | -0,842105 | 0,003662 |
| b_mediana_salvaguarda | regra | official_diary_rj | -11,461538 | -0,040418 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ce | -1,078947 | 0,001216 |
| b_mediana_salvaguarda | hibrido67 | official_diary_ma | -0,368421 | 0,003179 |
| b_mediana_salvaguarda | hibrido67 | official_diary_rj | -11,384615 | -0,040438 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | mesma_coluna | 114 | 5 |
| grafo_K24_maxregret_t0.00 | regra | proxima_coluna | 0 | 3 |
| grafo_K24_maxregret_t0.00 | regra | tabela_imagem | 6 | 0 |
| grafo_K24_maxregret_t0.00 | regra | transversal | 39 | 1 |
| grafo_K24_maxregret_t0.00 | regra | margem | 3 | 1 |
| grafo_K24_maxregret_t0.00 | regra | outro | 153 | 11 |
| grafo_K24_maxregret_t0.00 | hibrido67 | mesma_coluna | 98 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | proxima_coluna | 0 | 4 |
| grafo_K24_maxregret_t0.00 | hibrido67 | tabela_imagem | 6 | 0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | transversal | 37 | 6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | margem | 12 | 20 |
| grafo_K24_maxregret_t0.00 | hibrido67 | outro | 103 | 17 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | margem | 0 | 0 |
| grafo_K24_maxregret_t0.00 | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |
| b_mediana | regra | mesma_coluna | 114 | 5 |
| b_mediana | regra | proxima_coluna | 0 | 1 |
| b_mediana | regra | tabela_imagem | 6 | 0 |
| b_mediana | regra | transversal | 39 | 1 |
| b_mediana | regra | margem | 3 | 0 |
| b_mediana | regra | outro | 150 | 11 |
| b_mediana | hibrido67 | mesma_coluna | 98 | 6 |
| b_mediana | hibrido67 | proxima_coluna | 0 | 2 |
| b_mediana | hibrido67 | tabela_imagem | 6 | 0 |
| b_mediana | hibrido67 | transversal | 37 | 6 |
| b_mediana | hibrido67 | margem | 12 | 19 |
| b_mediana | hibrido67 | outro | 100 | 17 |
| b_mediana | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | proxima_coluna | 2 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | margem | 1 | 0 |
| b_mediana | grafo_K24_maxregret_t0.00 | outro | 0 | 3 |
| b_mediana_salvaguarda | regra | mesma_coluna | 114 | 5 |
| b_mediana_salvaguarda | regra | proxima_coluna | 0 | 1 |
| b_mediana_salvaguarda | regra | tabela_imagem | 6 | 0 |
| b_mediana_salvaguarda | regra | transversal | 39 | 1 |
| b_mediana_salvaguarda | regra | margem | 3 | 0 |
| b_mediana_salvaguarda | regra | outro | 150 | 11 |
| b_mediana_salvaguarda | hibrido67 | mesma_coluna | 98 | 6 |
| b_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 2 |
| b_mediana_salvaguarda | hibrido67 | tabela_imagem | 6 | 0 |
| b_mediana_salvaguarda | hibrido67 | transversal | 37 | 6 |
| b_mediana_salvaguarda | hibrido67 | margem | 12 | 19 |
| b_mediana_salvaguarda | hibrido67 | outro | 100 | 17 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 2 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 1 | 0 |
| b_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 0 | 3 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 89 | 0,958613 | 24,404494 | 0,837730 | 0,854708 |
| hibrido67 | 89 | 0,959083 | 23,494382 | 0,846454 | 0,863272 |
| grafo_K24_maxregret_t0.00 | 89 | 0,941542 | 21,123596 | 0,852052 | 0,869266 |
| b_mediana | 89 | 0,953957 | 21,134831 | 0,852096 | 0,869268 |
| b_mediana_salvaguarda | 89 | 0,953957 | 21,134831 | 0,852096 | 0,869268 |

## Acionamentos e quedas catastróficas

| Bancada | Acionamentos |
|---|---:|
| golden_v4 | 0 |
| validacao_silver | 0 |
| golden_v3_novo | 0 |
| teste_silver | 0 |


Páginas externas com Δτ < −0,5 contra a regra (lista completa):

- golden_v3_novo/b_mediana: nenhuma.
- golden_v3_novo/b_mediana_salvaguarda: nenhuma.
- teste_silver/b_mediana: nenhuma.
- teste_silver/b_mediana_salvaguarda: nenhuma.

## Critérios do cartão E015 — candidato (b)+salvaguarda

A variante (b) sem proteção é somente referência. O veredito abaixo não usa a combinação exploratória.

- golden_v3_novo: Δ quebras vs híbrido -1,370370 [-2,558824; 0,230769]; Δτ vs regra -0,017820 (mínimo permitido −0,005000).
- teste_silver: Δ quebras vs híbrido -2,280899 [-11,384615; -0,368421]; Δτ vs regra -0,004503 (mínimo permitido −0,005000).
- 1a_quebras_nao_pioram_nas_duas: PASSA.
- 1b_ic95_negativo_em_ao_menos_uma: PASSA.
- 2_tau_dentro_da_margem_nas_duas: FALHA.
- 3_sem_catastrofe_ou_salvaguarda_resolve_sem_violar_1_2: PASSA.
- Critério 3: 0 catástrofes sem salvaguarda; 0 no candidato.

**Veredito: NÃO GO.**

Pelo critério de abandono prévio, o grafo permanece como resultado exploratório e o híbrido 67 permanece finalista. Não se muda o limiar após ver as externas.

## Exploratório posterior ao veredito — híbrido 67 com candidato nas densas

LayoutReader até 67 unidades; (b)+salvaguarda acima de 67. Montado exclusivamente a partir das mesmas predições/medições já guardadas, depois de persistir o veredito. Não é novo candidato selecionado nem reavaliação das páginas.

## golden_v4 — ajuste

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| hibrido67 | 44 / 27 | 0,979738 | 5,136364 | 6,041 / 6,244 | 0,973419 | 0,966143 | 100,0% |
| hibrido67_mediana_salvaguarda | 44 / 27 | 0,980754 | 3,181818 | 4,395 / 3,868 | 0,982124 | 0,976386 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| hibrido67_mediana_salvaguarda | regra | tau | 44 | -0,005194 [-0,033190; 0,013021] | 0,155926 | 27/9/8 |
| hibrido67_mediana_salvaguarda | regra | quebras | 44 | -2,863636 [-4,600000; -1,449974] | 0,000722 | 29/10/5 |
| hibrido67_mediana_salvaguarda | regra | quebras_mil | 44 | -7,490159 [-15,768242; -1,819830] | 0,001270 | 29/10/5 |
| hibrido67_mediana_salvaguarda | regra | fid12 | 44 | 0,033995 [0,009162; 0,071367] | 0,001897 | 26/12/6 |
| hibrido67_mediana_salvaguarda | regra | sucessor_linhas | 44 | 0,049145 [0,013775; 0,102306] | 0,001168 | 29/10/5 |
| hibrido67_mediana_salvaguarda | hibrido67 | tau | 44 | 0,001017 [-0,004974; 0,006881] | 0,093483 | 11/29/4 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras | 44 | -1,954545 [-3,714377; -0,739105] | 0,001722 | 13/30/1 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras_mil | 44 | -1,646650 [-2,818488; -0,681913] | 0,001580 | 13/30/1 |
| hibrido67_mediana_salvaguarda | hibrido67 | fid12 | 44 | 0,008705 [0,003797; 0,014807] | 0,002735 | 12/31/1 |
| hibrido67_mediana_salvaguarda | hibrido67 | sucessor_linhas | 44 | 0,010243 [0,004321; 0,017379] | 0,001580 | 13/30/1 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | official_diary_MG_congonhas | -2,500000 | 0,000485 |
| hibrido67_mediana_salvaguarda | regra | official_diary_RJ_barra_do_pirai | -5,666667 | 0,030208 |
| hibrido67_mediana_salvaguarda | regra | official_diary_RJ_duque_de_caxias | -4,500000 | 0,078871 |
| hibrido67_mediana_salvaguarda | regra | official_diary_RJ_seropedica | -0,500000 | 0,000301 |
| hibrido67_mediana_salvaguarda | regra | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ac | -4,500000 | 0,037106 |
| hibrido67_mediana_salvaguarda | regra | official_diary_al | 0,333333 | -0,026705 |
| hibrido67_mediana_salvaguarda | regra | official_diary_am_manaus | 3,000000 | -0,008900 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ap | -1,500000 | 0,002522 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ba_salvador | 6,000000 | -0,447981 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ce | -2,000000 | 0,000061 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ma | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | regra | official_diary_mg | -9,000000 | 0,000010 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ms | -1,000000 | 0,000568 |
| hibrido67_mediana_salvaguarda | regra | official_diary_pb | -5,000000 | 0,018117 |
| hibrido67_mediana_salvaguarda | regra | official_diary_pe | -3,000000 | 0,000002 |
| hibrido67_mediana_salvaguarda | regra | official_diary_pi_v2 | -2,000000 | 0,000581 |
| hibrido67_mediana_salvaguarda | regra | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rj | -29,000000 | 0,001411 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rj_japeri | -6,000000 | 0,029106 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rn | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ro | -4,500000 | 0,000238 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rr | -2,000000 | 0,000328 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rs_porto_alegre | -0,500000 | -0,003074 |
| hibrido67_mediana_salvaguarda | regra | official_diary_sc | -3,000000 | 0,000006 |
| hibrido67_mediana_salvaguarda | regra | official_diary_se | -1,500000 | -0,030219 |
| hibrido67_mediana_salvaguarda | regra | official_diary_to | -1,000000 | -0,027511 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_MG_congonhas | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_RJ_barra_do_pirai | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_RJ_duque_de_caxias | -4,000000 | 0,010862 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_RJ_seropedica | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_RJ_volta_redonda | -1,000000 | 0,001831 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ac | -3,500000 | 0,037050 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_al | 1,000000 | -0,010698 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_am_manaus | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ap | -1,500000 | 0,002522 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ba_salvador | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ce | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ma | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_mg | -9,000000 | 0,000010 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ms | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_pb | -5,500000 | 0,018109 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_pe | -3,000000 | 0,000002 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_pi_v2 | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_pr_curitiba | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rj | -29,000000 | 0,001411 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rj_japeri | -5,000000 | 0,025968 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rn | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ro | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rr | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rs_porto_alegre | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_sc | -3,000000 | 0,000006 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_se | -1,500000 | -0,030219 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_to | -1,000000 | -0,027511 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | mesma_coluna | 36 | 0 |
| hibrido67_mediana_salvaguarda | regra | proxima_coluna | 0 | 1 |
| hibrido67_mediana_salvaguarda | regra | tabela_imagem | 1 | 11 |
| hibrido67_mediana_salvaguarda | regra | transversal | 11 | 1 |
| hibrido67_mediana_salvaguarda | regra | margem | 79 | 9 |
| hibrido67_mediana_salvaguarda | regra | outro | 19 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | mesma_coluna | 30 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | tabela_imagem | 0 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | transversal | 11 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | margem | 37 | 4 |
| hibrido67_mediana_salvaguarda | hibrido67 | outro | 10 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 3 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 1 | 11 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 31 | 8 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 3 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| hibrido67 | 44 | 0,986295 | 2,772727 | 0,988822 | 0,985116 |
| hibrido67_mediana_salvaguarda | 44 | 0,986351 | 1,522727 | 0,992478 | 0,989734 |

## validacao_silver — ajuste

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| hibrido67 (parcial) | 13 / 1 | 0,958544 | 17,846154 | 9,554 / 9,564 | 0,955769 | 0,916132 | 100,0% |
| hibrido67_mediana_salvaguarda (parcial) | 13 / 1 | 0,959099 | 9,461538 | 5,171 / 5,071 | 0,975055 | 0,955182 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| hibrido67_mediana_salvaguarda | regra | tau | 13 | 0,000555 [0,000555; 0,000555] | 0,317311 | 7/4/2 |
| hibrido67_mediana_salvaguarda | regra | quebras | 13 | -8,384615 [-8,384615; -8,384615] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | regra | quebras_mil | 13 | -4,383177 [-4,383177; -4,383177] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | regra | fid12 | 13 | 0,019286 [0,019286; 0,019286] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | regra | sucessor_linhas | 13 | 0,039050 [0,039050; 0,039050] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | hibrido67 | tau | 13 | 0,000555 [0,000555; 0,000555] | 0,317311 | 7/4/2 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras | 13 | -8,384615 [-8,384615; -8,384615] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras_mil | 13 | -4,383177 [-4,383177; -4,383177] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | hibrido67 | fid12 | 13 | 0,019286 [0,019286; 0,019286] | 0,317311 | 9/4/0 |
| hibrido67_mediana_salvaguarda | hibrido67 | sucessor_linhas | 13 | 0,039050 [0,039050; 0,039050] | 0,317311 | 9/4/0 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | official_diary_rn | -8,384615 | 0,000555 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rn | -8,384615 | 0,000555 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | mesma_coluna | 17 | 0 |
| hibrido67_mediana_salvaguarda | regra | proxima_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | regra | tabela_imagem | 0 | 0 |
| hibrido67_mediana_salvaguarda | regra | transversal | 1 | 0 |
| hibrido67_mediana_salvaguarda | regra | margem | 39 | 0 |
| hibrido67_mediana_salvaguarda | regra | outro | 53 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | mesma_coluna | 17 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | tabela_imagem | 0 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | transversal | 1 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | margem | 39 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | outro | 53 | 1 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 3 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 0 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| hibrido67 | 13 | 0,974157 | 12,230769 | 0,968886 | 0,937706 |
| hibrido67_mediana_salvaguarda | 13 | 0,964398 | 6,846154 | 0,979828 | 0,965158 |

## golden_v3_novo — externa

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| hibrido67 | 27 / 10 | 0,958977 | 7,888889 | 13,739 / 8,948 | 0,941220 | 0,938410 | 100,0% |
| hibrido67_mediana_salvaguarda | 27 / 10 | 0,940794 | 6,296296 | 11,832 / 7,142 | 0,948427 | 0,947030 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| hibrido67_mediana_salvaguarda | regra | tau | 27 | -0,018764 [-0,052884; 0,004036] | 0,609834 | 12/9/6 |
| hibrido67_mediana_salvaguarda | regra | quebras | 27 | -2,925926 [-3,531302; -2,500000] | 0,005825 | 14/10/3 |
| hibrido67_mediana_salvaguarda | regra | quebras_mil | 27 | -5,373892 [-10,661720; -3,007493] | 0,005857 | 14/10/3 |
| hibrido67_mediana_salvaguarda | regra | fid12 | 27 | 0,020012 [0,013685; 0,031237] | 0,010724 | 14/9/4 |
| hibrido67_mediana_salvaguarda | regra | sucessor_linhas | 27 | 0,035728 [0,019818; 0,066143] | 0,005857 | 14/10/3 |
| hibrido67_mediana_salvaguarda | hibrido67 | tau | 27 | -0,018184 [-0,052415; 0,000097] | 0,907143 | 4/19/4 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras | 27 | -1,592593 [-2,695652; -0,266667] | 0,047188 | 7/19/1 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras_mil | 27 | -1,907603 [-3,351793; -0,282606] | 0,047376 | 7/19/1 |
| hibrido67_mediana_salvaguarda | hibrido67 | fid12 | 27 | 0,007207 [0,000000; 0,012801] | 0,243443 | 6/19/2 |
| hibrido67_mediana_salvaguarda | hibrido67 | sucessor_linhas | 27 | 0,008620 [0,001748; 0,014665] | 0,047376 | 7/19/1 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ac | -2,500000 | 0,017471 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ap | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ce | -2,666667 | -0,009310 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ma | -2,428571 | -0,000368 |
| hibrido67_mediana_salvaguarda | regra | official_diary_mg | -4,000000 | 0,000215 |
| hibrido67_mediana_salvaguarda | regra | official_diary_pi_v2 | -3,500000 | 0,000374 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rj | -3,600000 | -0,097853 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ro | -3,000000 | 0,000194 |
| hibrido67_mediana_salvaguarda | regra | official_diary_se | -5,000000 | 0,004300 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_RJ_barra_do_pirai | -4,000000 | 0,000679 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ac | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ap | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ce | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ma | -2,428571 | -0,000368 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_mg | -4,000000 | 0,000215 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_pi_v2 | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rj | -3,600000 | -0,097855 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ro | 0,000000 | 0,000000 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_se | 0,000000 | 0,000000 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | mesma_coluna | 35 | 3 |
| hibrido67_mediana_salvaguarda | regra | proxima_coluna | 0 | 1 |
| hibrido67_mediana_salvaguarda | regra | tabela_imagem | 4 | 1 |
| hibrido67_mediana_salvaguarda | regra | transversal | 0 | 0 |
| hibrido67_mediana_salvaguarda | regra | margem | 15 | 6 |
| hibrido67_mediana_salvaguarda | regra | outro | 33 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | mesma_coluna | 25 | 3 |
| hibrido67_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | tabela_imagem | 3 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | transversal | 0 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | margem | 4 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | outro | 16 | 1 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 3 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 2 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 4 | 3 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 2 | 0 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| hibrido67 | 27 | 0,960716 | 6,555556 | 0,947488 | 0,949111 |
| hibrido67_mediana_salvaguarda | 27 | 0,941633 | 5,111111 | 0,954450 | 0,957335 |

## teste_silver — externa

| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| hibrido67 | 89 / 3 | 0,959092 | 26,426966 | 43,157 / 24,677 | 0,834332 | 0,849525 | 100,0% |
| hibrido67_mediana_salvaguarda | 89 / 3 | 0,954830 | 23,876404 | 41,303 / 22,295 | 0,843107 | 0,859110 | 100,0% |

### Diferenças pareadas

Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.

| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |
|---|---|---|---:|---:|---:|---:|
| hibrido67_mediana_salvaguarda | regra | tau | 89 | -0,004736 [-0,040398; 0,004752] | 0,592980 | 32/41/16 |
| hibrido67_mediana_salvaguarda | regra | quebras | 89 | -3,573034 [-11,538462; -1,131579] | 0,108809 | 37/47/5 |
| hibrido67_mediana_salvaguarda | regra | quebras_mil | 89 | -3,192690 [-5,617581; -2,407182] | 0,108809 | 37/47/5 |
| hibrido67_mediana_salvaguarda | regra | fid12 | 89 | 0,017706 [0,010904; 0,036730] | 0,108809 | 36/51/2 |
| hibrido67_mediana_salvaguarda | regra | sucessor_linhas | 89 | 0,018899 [0,014399; 0,023293] | 0,108809 | 37/47/5 |
| hibrido67_mediana_salvaguarda | hibrido67 | tau | 89 | -0,004262 [-0,040418; 0,004269] | 0,592980 | 16/64/9 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras | 89 | -2,550562 [-11,461538; -0,657895] | 0,108809 | 23/64/2 |
| hibrido67_mediana_salvaguarda | hibrido67 | quebras_mil | 89 | -1,854382 [-5,565606; -1,137575] | 0,108809 | 23/64/2 |
| hibrido67_mediana_salvaguarda | hibrido67 | fid12 | 89 | 0,008775 [0,000530; 0,036453] | 0,108809 | 21/66/2 |
| hibrido67_mediana_salvaguarda | hibrido67 | sucessor_linhas | 89 | 0,009586 [0,003929; 0,023216] | 0,108809 | 23/64/2 |

### Diferenças por veículo

| Método | Base | Veículo | Δ quebras/pág | Δτ |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | official_diary_ce | -3,289474 | -0,002023 |
| hibrido67_mediana_salvaguarda | regra | official_diary_ma | -1,131579 | 0,004752 |
| hibrido67_mediana_salvaguarda | regra | official_diary_rj | -11,538462 | -0,040398 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ce | -1,394737 | -0,000425 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_ma | -0,657895 | 0,004269 |
| hibrido67_mediana_salvaguarda | hibrido67 | official_diary_rj | -11,461538 | -0,040418 |

### Reparos e regressões de sucessores de linhas

Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| hibrido67_mediana_salvaguarda | regra | mesma_coluna | 116 | 5 |
| hibrido67_mediana_salvaguarda | regra | proxima_coluna | 1 | 1 |
| hibrido67_mediana_salvaguarda | regra | tabela_imagem | 6 | 0 |
| hibrido67_mediana_salvaguarda | regra | transversal | 44 | 1 |
| hibrido67_mediana_salvaguarda | regra | margem | 22 | 9 |
| hibrido67_mediana_salvaguarda | regra | outro | 156 | 11 |
| hibrido67_mediana_salvaguarda | hibrido67 | mesma_coluna | 97 | 3 |
| hibrido67_mediana_salvaguarda | hibrido67 | proxima_coluna | 0 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | tabela_imagem | 6 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | transversal | 37 | 1 |
| hibrido67_mediana_salvaguarda | hibrido67 | margem | 3 | 0 |
| hibrido67_mediana_salvaguarda | hibrido67 | outro | 100 | 11 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | mesma_coluna | 3 | 1 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | proxima_coluna | 3 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | tabela_imagem | 0 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | transversal | 5 | 0 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | margem | 20 | 9 |
| hibrido67_mediana_salvaguarda | grafo_K24_maxregret_t0.00 | outro | 6 | 3 |

### Corpo sem margens — diagnóstico

Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| hibrido67 | 89 | 0,959083 | 23,494382 | 0,846454 | 0,863272 |
| hibrido67_mediana_salvaguarda | 89 | 0,954584 | 20,977528 | 0,855578 | 0,872991 |

## Limitações e reprodução

As três bancadas principais são separadas; RN é ajuste adicional. Há sobreposição entre conjuntos, por isso não se somam as bancadas. Golden_v4 já orientou a regra e golden_v3_novo já foi consultado em rodadas anteriores. Silver pode ter ordem PDF errada e erro interno aos átomos. A mediana usa unidades sem ponderação por palavras; a salvaguarda não garante proximidade da referência e pode deixar passar grandes trocas quando o τ contra a regra fica positivo. O experimento reusa um único modelo/semente. IC com poucos veículos, especialmente os três do silver, tem precisão limitada. O corpo sem margens é uma projeção diagnóstica. Não houve inspeção visual de PDF nem acesso ao teste cego, ao Label Studio ou escrita sob data/.

Comando: `venv/Scripts/python.exe -B orquestracao/analises/e015_mediana.py`. `--etapa ajuste` nunca abre externas; a execução completa retoma caches atômicos por página. `--conferir` reconstrói os resumos dos caches sem inferência ou nova medição das páginas. Abertura das externas e veredito anteriores à exploração ficam registrados em JSON.
