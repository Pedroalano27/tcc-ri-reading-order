1. Âncora reproduzida: τ 0,985948; 6,045455 quebras/página no golden_v4.
2. Diagnóstico no ajuste: contribuição entre cadeias ao Δτ: golden_v4 -0,048121; validacao_silver -0,270929; cinco páginas detalhadas abaixo.
3. E004 reproduzido sem treino: mesmo modelo, calibração e ordem por página; (a) é idêntica ao E004.
4. Nenhuma variante elegível no ajuste; externas e combinação híbrida não executadas.
5. Golden_v3_novo já foi consultado em rodadas anteriores; nenhuma seleção usa externas; teste cego não foi aberto.
6. Veredito: NÃO GO / abandono: nenhuma variante atende a margem de τ no ajuste.

## Execução e definições

Situação: Concluído por abandono no ajuste; nenhuma variante elegível; externas e combinação não executadas. Execução `cache/0df917eb466413ac2f437692ba5ae4724266bc547df0b185aa15be890d832e25`. Pico RSS 189,3 MiB; CPU, quatro threads, um processo, zero GPU, sem retreino.

Fontes, hashes e caches por página estão no manifesto e estado desta execução. Entrada embaralhada importada do protocolo com `random.Random(f'entrada-{page_id}')`. Linhas + átomos ls3 congelados; expansão canônica da bancada; cobertura integral exigida.

(a) cadeias pelo posto da primeira linha: exatamente a costura já usada pelo max-regret. (b) cadeias pela mediana dos postos de todas as unidades na regra; empate pela primeira. (c) mantém as arestas selecionadas do grafo se coluna(i)=coluna(j) ou j é margem/topo/rodapé; preenche lacunas com arestas da regra, sem duas entradas ou ciclos (guloso importado com precedência grafo > regra > FIM). (d) parte de (c), retira margens e reinsere cadeias marginais junto ao predecessor do grafo; se ausente, antes do sucessor; se ambos ausentes, pelo posto da regra. A ordem do corpo fica fixa. Colunas e margens vêm de `contexto()` do E004, sem novos limiares.

Seleção: média das médias de v4/RN com peso igual, como no E004; entre variantes com τ ≥ regra − 0,005, escolhe menor quebra (desempate por maior τ e nome). O sucesso no ajuste também exige reter ≥ 60% da redução absoluta de quebras do E004. A combinação usa LayoutReader até 67 unidades e a variante congelada acima disso, sem seleção adicional.

IC95 percentil: 5000 bootstraps por veículo e semente 20261004, funções importadas; Wilcoxon Pratt sobre médias pareadas por veículo. Médias principais por página; IC reamostra veículos inteiros conservando suas páginas. RN tem um veículo e IC degenerado. Melhor/igual/pior usa orientação da métrica; valores de p são descritivos. RN não tem LayoutReader salvo: híbrido e combinação são parciais em 13 páginas densas; as duas leves ficam ausentes, sem imputação. A seleção usa todas as 15 páginas com regra/grafo/variantes.

## Diagnóstico anterior à seleção (somente ajuste)

Cadeia = caminho de arestas efetivamente fixadas pelo max-regret, antes da costura. Correta internamente = subsequência de palavras sem inversões; contígua exige também todos os sucessores de palavras corretos. Fora de ordem = participa de inversão com outra cadeia. Linhas são IDs da referência, unidades são IDs automáticos; uma linha dividida entre cadeias pode aparecer nas duas categorias. Não se somam conjuntos sobrepostos.

As inversões são derivadas do τ importado; sua partição interna/entre cadeias fecha exatamente a diferença de τ contra a regra. Arestas erradas podem unir trechos remotos numa só cadeia: nesse caso o erro é interno, mesmo que cada trecho isolado esteja correto.

| Ajuste | Inversões internas grafo/regra | Entre grafo/regra | Δτ interno | Δτ entre | Cadeias boas fora: palavras/linhas/unidades | Cadeias com erro: palavras/linhas/unidades |
|---|---:|---:|---:|---:|---:|---:|
| golden_v4 | 33558/34544 | 438161/68273 | 0,000134 | -0,048121 | 5876/746/657 | 17975/2406/1956 |
| validacao_silver | 132193/137560 | 6333799/418976 | 0,000378 | -0,270929 | 6735/742/742 | 15364/3664/1281 |

golden_v4: subconjunto de cadeias também contíguas fora de ordem: {'cadeias': 20, 'palavras': 1192, 'linhas': 198}.
validacao_silver: subconjunto de cadeias também contíguas fora de ordem: {'cadeias': 12, 'palavras': 6699, 'linhas': 730}.

### Cinco maiores quedas de τ no ajuste

- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40`: Δτ -0,987149 (dentro 0,000000; entre -0,987149). Inversões internas 22, entre 3015378.
  - cadeia internamente errada, 1752 palavras, 12 inversões; posto da primeira/mediano na regra 0/2,5. `b4` (silver:l0): “Natal, 29 de dezembro de 2022”; `b2` (silver:l1): “Diário Oficial do Estado do Rio Grande do Norte”; `b5` (silver:l1134): “Código”; `b3` (silver:l1132, silver:l1133, silver:l1135): “Marca/Modelo Díesel DENATRAN 2022 2021 2020 2019 2018 2017 2016 2015 2014 2013 I/PEUGEOT RCZ THP NÃO 161667 0,”.
  - cadeia internamente errada, 1744 palavras, 10 inversões; posto da primeira/mediano na regra 4/4,0. `b6` (silver:l10, silver:l100, silver:l1000): “Marca/Modelo Díesel DENATRAN 2022 2021 2020 2019 2018 2017 2016 2015 2014 2013 I/MMC OUTLANDER 2.0 NÃO 211766 ”.
- `official_diary_to/2022-12-13_4783.pdf#p10`: Δτ -0,940247 (dentro 0,000000; entre -0,940247). Inversões internas 4, entre 212040.
  - cadeia internamente errada, 479 palavras, 4 inversões; posto da primeira/mediano na regra 0/70,5. `b51` (b21:l0): “DIÁRIO OFICIAL No 6228”; `b12` (b39:l0): “11”; `b18` (b27:l0): “PAULO CÉSAR BENFICA FILHO”; `b56` (b27:l1): “Secretário de Estado da Administração”.
  - cadeia internamente correta deslocada, 465 palavras, 0 inversões; posto da primeira/mediano na regra 5/25,0. `b33` (b5:l1): “DE 7 DE DEZEMBRO DE 2022.”; `b86` (b14:l0): “O SECRETÁRIO DE ESTADO DA ADMINISTRAÇÃO, no uso”; `b50` (b24:l0): “PAULO CÉSAR BENFICA FILHO”; `b65` (b24:l1): “Secretário de Estado da Administração”.
- `official_diary_to/2024-04-17_5147.pdf#p47`: Δτ -0,928266 (dentro 0,000000; entre -0,928266). Inversões internas 4, entre 174363.
  - cadeia internamente errada, 500 palavras, 4 inversões; posto da primeira/mediano na regra 0/99,0. `b0` (b47:l0): “DIÁRIO OFICIAL No 6552”; `b105` (b61:l0): “48”; `b132` (b68:l0): “EONILDA BATISTA MARTINS”; `b81` (b68:l1): “Presidente”.
  - cadeia internamente correta deslocada, 361 palavras, 0 inversões; posto da primeira/mediano na regra 4/34,5. `b102` (b49:l0): “EXTRATO DE CONTRATO”; `b16` (b45:l0): “PROCESSO: 01/2024”; `b48` (b56:l0): “LEILA MÁRCIA ASCENSO GAMA”; `b83` (b56:l1): “Presidente da Associação”.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: Δτ -0,855332 (dentro 0,000000; entre -0,855332). Inversões internas 978, entre 19656.
  - cadeia internamente errada, 168 palavras, 978 inversões; posto da primeira/mediano na regra 0/23,0. `b25` (silver:l0): “Diário”; `b24` (silver:l1): “Oficial”; `b1` (silver:l29): “http://equador.rn.gov.br/.”; `b16` (silver:l30): “Equador - RN, 15 de Outubro de 2021 PEDRO FREIRE DE SOUZA FILHO Pregoeiro Oficial”.
  - cadeia internamente correta deslocada, 126 palavras, 0 inversões; posto da primeira/mediano na regra 8/15,0. `b4` (silver:l5): “PREFEITURA MUNICIPAL DE JARDIM DE PIRANHAS”; `b5` (silver:l6): “EXTRATO DE CONTRATO”; `b6` (silver:l16): “ROGÉRIO SOARES -”; `b13` (silver:l17): “Prefeito Constitucional”.
  - cadeia correta, 0 palavras, 0 inversões; posto da primeira/mediano na regra 34/34,0. `b27` (): “”.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: Δτ -0,828163 (dentro 0,000000; entre -0,828163). Inversões internas 4279, entre 1556786.
  - cadeia internamente errada, 859 palavras, 4279 inversões; posto da primeira/mediano na regra 0/245,0. `b254` (silver:l0): “Diário”; `b72` (silver:l1): “Oficial”; `b62` (silver:l295): “matérias previstas no inciso XI, do caput do art. 19, ad referendum do Colegiado”; `b126` (silver:l296): “Microrregional, quando necessário para os termos aditivos:”.
  - cadeia internamente correta deslocada, 962 palavras, 0 inversões; posto da primeira/mediano na regra 7/58,0. `b228` (silver:l5): “o Presidente do Colegiado Microrregional deve suspender, declarar o término, con-”; `b275` (silver:l6): “vocar nova assembleia ou continuar a assembleia em caráter informativo.”; `b148` (silver:l102): “I - o voto favorável de 2/3 (dois terços) dos Municípios integrantes”; `b271` (silver:l103): “da Microrregião;”.
  - cadeia internamente correta deslocada, 876 palavras, 0 inversões; posto da primeira/mediano na regra 8/154,0. `b133` (silver:l104): “II - o cômputo como voto favorável válido, no caso de alienação de”; `b194` (silver:l105): “controle, somente dos entes federados que tenham editado leis autorizativas em até”; `b160` (silver:l199): “§ 4º Os votos do Estado serão computados apenas se os votos dos”; `b267` (silver:l200): “Municípios não produzirem deliberação com mais da metade dos votos.”.

## Varredura e congelamento no ajuste

| Variante | τ médio | Quebras médias | Δτ vs regra | Ganho E004 retido | τ elegível | Passa ajuste |
|---|---:|---:|---:|---:|---|---|
| a_primeira | 0,812314 | 6,540152 | -0,159269 | 100,00% | False | False |
| b_mediana | 0,938857 | 6,417424 | -0,032726 | 102,55% | False | False |
| c_local | 0,814231 | 6,596970 | -0,157351 | 98,82% | False | False |
| d_local_margens | 0,814155 | 7,387121 | -0,157428 | 82,41% | False | False |

Regra no ajuste: τ 0,971583, quebras 11,356061; E004 6,540152 quebras. Resultado da seleção em `selecao_congelada.json` antes de qualquer externa.

Nenhum parâmetro ou algoritmo foi alterado depois desta varredura. A mediana recupera o τ no golden_v4, mas não atende à margem na RN; a média do ajuste impede selecionar uma variante válida. O critério de abandono é aplicado sem afrouxar a margem nem escolher pelo golden_v4 isolado. As tabelas por veículo a seguir detalham a variante de maior τ no ajuste apenas como diagnóstico.

### Maiores perdas da mediana no ajuste (não usada para selecionar outra variante)

| Página | Bancada | Δτ mediana vs regra | Δ quebras |
|---|---|---:|---:|
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40` | validacao_silver | -0,987149 | 0,000000 |
| `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1` | validacao_silver | -0,095669 | -8,000000 |
| `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31` | golden_v4 | -0,067300 | 0,000000 |
| `official_diary_to/2022-12-13_4783.pdf#p10` | golden_v4 | -0,035520 | -1,000000 |
| `official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf#p0` | golden_v4 | -0,032093 | 3,000000 |

## golden_v4 — ajuste

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 44 / 27 | 0,985948 | 6,045455 | 11,885 / 7,349 | 0,948129 | 0,927240 | 100,0% |
| hibrido67 | 44 / 27 | 0,979738 | 5,136364 | 6,041 / 6,244 | 0,973419 | 0,966143 | 100,0% |
| grafo_K24_maxregret_t0.00 | 44 / 27 | 0,937961 | 3,613636 | 7,778 / 4,393 | 0,963953 | 0,955269 | 100,0% |
| a_primeira | 44 / 27 | 0,937961 | 3,613636 | 7,778 / 4,393 | 0,963953 | 0,955269 | 100,0% |
| b_mediana | 44 / 27 | 0,986681 | 3,568182 | 7,278 / 4,338 | 0,965703 | 0,959057 | 100,0% |
| c_local | 44 / 27 | 0,937817 | 3,727273 | 7,780 / 4,531 | 0,963138 | 0,954585 | 100,0% |
| d_local_margens | 44 / 27 | 0,937982 | 3,840909 | 7,863 / 4,669 | 0,963172 | 0,953828 | 100,0% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
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
| a_primeira | regra | 44 | tau | -0,047987 [-0,147284; 0,003696] | 0,512256 | 16/19/9 |
| a_primeira | regra | 44 | quebras | -2,431818 [-4,139535; -1,162668] | 0,000513 | 20/22/2 |
| a_primeira | regra | 44 | quebras_mil | -4,106956 [-8,299765; -1,291931] | 0,001055 | 20/22/2 |
| a_primeira | regra | 44 | fid12 | 0,015824 [0,006260; 0,026694] | 0,002085 | 19/23/2 |
| a_primeira | regra | 44 | sucessor_linhas | 0,028029 [0,008366; 0,056655] | 0,000835 | 21/21/2 |
| a_primeira | hibrido67 | 44 | tau | -0,041776 [-0,143114; 0,021494] | 0,932963 | 16/9/19 |
| a_primeira | hibrido67 | 44 | quebras | -1,522727 [-3,500000; -0,074869] | 0,069212 | 17/10/17 |
| a_primeira | hibrido67 | 44 | quebras_mil | 1,736553 [-1,856740; 6,157636] | 0,952089 | 17/10/17 |
| a_primeira | hibrido67 | 44 | fid12 | -0,009466 [-0,039952; 0,013016] | 0,923364 | 18/11/15 |
| a_primeira | hibrido67 | 44 | sucessor_linhas | -0,010874 [-0,038913; 0,012273] | 0,971242 | 17/10/17 |
| a_primeira | grafo_K24_maxregret_t0.00 | 44 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 44 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 44 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 44 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 44 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/44/0 |
| b_mediana | regra | 44 | tau | 0,000732 [-0,005241; 0,006707] | 0,251724 | 17/20/7 |
| b_mediana | regra | 44 | quebras | -2,477273 [-4,190592; -1,200000] | 0,000240 | 20/23/1 |
| b_mediana | regra | 44 | quebras_mil | -4,606634 [-9,519562; -1,454718] | 0,000219 | 20/23/1 |
| b_mediana | regra | 44 | fid12 | 0,017574 [0,008374; 0,028446] | 0,000327 | 19/24/1 |
| b_mediana | regra | 44 | sucessor_linhas | 0,031817 [0,010625; 0,064814] | 0,000123 | 21/22/1 |
| b_mediana | hibrido67 | 44 | tau | 0,006943 [-0,010348; 0,034878] | 0,772894 | 16/10/18 |
| b_mediana | hibrido67 | 44 | quebras | -1,568182 [-3,538514; -0,139535] | 0,058695 | 17/11/16 |
| b_mediana | hibrido67 | 44 | quebras_mil | 1,236875 [-1,989710; 5,004735] | 0,754553 | 17/11/16 |
| b_mediana | hibrido67 | 44 | fid12 | -0,007715 [-0,037840; 0,014224] | 0,647336 | 18/12/14 |
| b_mediana | hibrido67 | 44 | sucessor_linhas | -0,007086 [-0,030987; 0,013811] | 0,718294 | 17/11/16 |
| b_mediana | grafo_K24_maxregret_t0.00 | 44 | tau | 0,048719 [0,000094; 0,144768] | 0,045708 | 5/39/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 44 | quebras | -0,045455 [-0,111111; 0,000000] | 0,157373 | 2/42/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 44 | quebras_mil | -0,499678 [-1,302916; 0,000000] | 0,157373 | 2/42/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 44 | fid12 | 0,001750 [0,000000; 0,004866] | 0,157373 | 2/42/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 44 | sucessor_linhas | 0,003788 [0,000000; 0,009260] | 0,157373 | 2/42/0 |
| c_local | regra | 44 | tau | -0,048131 [-0,147497; 0,003475] | 0,558360 | 15/20/9 |
| c_local | regra | 44 | quebras | -2,318182 [-3,837209; -1,133333] | 0,000563 | 20/22/2 |
| c_local | regra | 44 | quebras_mil | -4,104532 [-8,299201; -1,322708] | 0,001055 | 20/22/2 |
| c_local | regra | 44 | fid12 | 0,015009 [0,005543; 0,025721] | 0,002085 | 19/23/2 |
| c_local | regra | 44 | sucessor_linhas | 0,027345 [0,007700; 0,056019] | 0,001254 | 20/22/2 |
| c_local | hibrido67 | 44 | tau | -0,041920 [-0,143425; 0,021266] | 0,717982 | 14/11/19 |
| c_local | hibrido67 | 44 | quebras | -1,409091 [-3,205128; -0,065183] | 0,074491 | 16/12/16 |
| c_local | hibrido67 | 44 | quebras_mil | 1,738978 [-1,832617; 6,192579] | 0,828446 | 16/12/16 |
| c_local | hibrido67 | 44 | fid12 | -0,010281 [-0,040732; 0,012365] | 0,923364 | 18/11/15 |
| c_local | hibrido67 | 44 | sucessor_linhas | -0,011558 [-0,039551; 0,011697] | 0,980813 | 16/11/17 |
| c_local | grafo_K24_maxregret_t0.00 | 44 | tau | -0,000144 [-0,000693; 0,000365] | 0,192309 | 1/39/4 |
| c_local | grafo_K24_maxregret_t0.00 | 44 | quebras | 0,113636 [-0,024390; 0,350000] | 0,299122 | 1/40/3 |
| c_local | grafo_K24_maxregret_t0.00 | 44 | quebras_mil | 0,002425 [-0,226157; 0,191006] | 0,347077 | 1/40/3 |
| c_local | grafo_K24_maxregret_t0.00 | 44 | fid12 | -0,000815 [-0,002123; 0,000000] | 0,157373 | 0/42/2 |
| c_local | grafo_K24_maxregret_t0.00 | 44 | sucessor_linhas | -0,000684 [-0,001588; 0,000000] | 0,083417 | 0/41/3 |
| d_local_margens | regra | 44 | tau | -0,047967 [-0,147488; 0,003667] | 0,558360 | 15/20/9 |
| d_local_margens | regra | 44 | quebras | -2,204545 [-3,697800; -1,069767] | 0,000563 | 20/22/2 |
| d_local_margens | regra | 44 | quebras_mil | -4,022143 [-8,213738; -1,238171] | 0,001151 | 20/22/2 |
| d_local_margens | regra | 44 | fid12 | 0,015043 [0,005780; 0,025551] | 0,002085 | 19/23/2 |
| d_local_margens | regra | 44 | sucessor_linhas | 0,026588 [0,007124; 0,055229] | 0,001254 | 20/22/2 |
| d_local_margens | hibrido67 | 44 | tau | -0,041756 [-0,143232; 0,021440] | 0,700064 | 14/11/19 |
| d_local_margens | hibrido67 | 44 | quebras | -1,295455 [-3,045538; -0,019213] | 0,111545 | 16/12/16 |
| d_local_margens | hibrido67 | 44 | quebras_mil | 1,821366 [-1,680736; 6,232124] | 0,866158 | 16/12/16 |
| d_local_margens | hibrido67 | 44 | fid12 | -0,010246 [-0,040615; 0,011797] | 0,923364 | 18/11/15 |
| d_local_margens | hibrido67 | 44 | sucessor_linhas | -0,012315 [-0,039759; 0,010417] | 0,942484 | 16/11/17 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 44 | tau | 0,000020 [-0,000310; 0,000434] | 0,204777 | 1/39/4 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 44 | quebras | 0,227273 [0,000000; 0,511628] | 0,158229 | 1/39/4 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 44 | quebras_mil | 0,084813 [-0,175445; 0,337641] | 0,204777 | 1/39/4 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 44 | fid12 | -0,000781 [-0,002020; 0,000000] | 0,157373 | 0/42/2 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 44 | sucessor_linhas | -0,001441 [-0,002960; -0,000218] | 0,045708 | 0/40/4 |

### Δ por veículo — variante de maior τ no ajuste, sem seleção válida

| Método | Base | Veículo | Δ quebras | Δτ |
|---|---|---|---:|---:|
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
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_MG_congonhas | 0,000000 | 0,001741 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_RJ_barra_do_pirai | -0,333333 | 0,004520 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_RJ_duque_de_caxias | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_RJ_seropedica | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_RJ_volta_redonda | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ac | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_al | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_am_manaus | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ap | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ba_salvador | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ce | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ma | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_mg | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ms | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_pb | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_pe | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_pi_v2 | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_pr_curitiba | -1,000000 | 0,313119 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rj | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rj_japeri | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rn | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_ro | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rr | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rs_porto_alegre | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_sc | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_se | 0,000000 | 0,000000 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_to | 0,000000 | 0,906745 |

### Sucessores: reparos e regressões contra a regra

Contagens de transições de linhas, sem compensar regressões com reparos de outra classe.

| Método | Classe | Referência | Certos | Reparos | Regressões | Quebras |
|---|---|---:|---:|---:|---:|---:|
| regra | mesma_coluna | 3149 | 3101 | 0 | 0 | 54 |
| regra | proxima_coluna | 13 | 10 | 0 | 0 | 3 |
| regra | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| regra | transversal | 26 | 8 | 0 | 0 | 18 |
| regra | margem | 213 | 82 | 0 | 0 | 134 |
| regra | outro | 1224 | 1195 | 0 | 0 | 48 |
| hibrido67 | mesma_coluna | 3149 | 3107 | 6 | 0 | 49 |
| hibrido67 | proxima_coluna | 13 | 10 | 0 | 0 | 3 |
| hibrido67 | tabela_imagem | 60 | 42 | 1 | 11 | 19 |
| hibrido67 | transversal | 26 | 8 | 0 | 0 | 18 |
| hibrido67 | margem | 213 | 119 | 42 | 5 | 101 |
| hibrido67 | outro | 1224 | 1204 | 9 | 0 | 36 |
| grafo_K24_maxregret_t0.00 | mesma_coluna | 3149 | 3134 | 33 | 0 | 22 |
| grafo_K24_maxregret_t0.00 | proxima_coluna | 13 | 9 | 0 | 1 | 4 |
| grafo_K24_maxregret_t0.00 | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| grafo_K24_maxregret_t0.00 | transversal | 26 | 18 | 11 | 1 | 8 |
| grafo_K24_maxregret_t0.00 | margem | 213 | 129 | 51 | 4 | 86 |
| grafo_K24_maxregret_t0.00 | outro | 1224 | 1211 | 17 | 1 | 30 |
| a_primeira | mesma_coluna | 3149 | 3134 | 33 | 0 | 22 |
| a_primeira | proxima_coluna | 13 | 9 | 0 | 1 | 4 |
| a_primeira | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| a_primeira | transversal | 26 | 18 | 11 | 1 | 8 |
| a_primeira | margem | 213 | 129 | 51 | 4 | 86 |
| a_primeira | outro | 1224 | 1211 | 17 | 1 | 30 |
| b_mediana | mesma_coluna | 3149 | 3134 | 33 | 0 | 22 |
| b_mediana | proxima_coluna | 13 | 9 | 0 | 1 | 4 |
| b_mediana | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| b_mediana | transversal | 26 | 18 | 11 | 1 | 8 |
| b_mediana | margem | 213 | 130 | 52 | 4 | 87 |
| b_mediana | outro | 1224 | 1212 | 17 | 0 | 27 |
| c_local | mesma_coluna | 3149 | 3134 | 33 | 0 | 21 |
| c_local | proxima_coluna | 13 | 9 | 0 | 1 | 4 |
| c_local | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| c_local | transversal | 26 | 14 | 7 | 1 | 12 |
| c_local | margem | 213 | 128 | 50 | 4 | 88 |
| c_local | outro | 1224 | 1210 | 16 | 1 | 30 |
| d_local_margens | mesma_coluna | 3149 | 3134 | 33 | 0 | 22 |
| d_local_margens | proxima_coluna | 13 | 9 | 0 | 1 | 4 |
| d_local_margens | tabela_imagem | 60 | 52 | 0 | 0 | 9 |
| d_local_margens | transversal | 26 | 14 | 7 | 1 | 12 |
| d_local_margens | margem | 213 | 123 | 45 | 4 | 92 |
| d_local_margens | outro | 1224 | 1210 | 16 | 1 | 30 |

### Reparos/regressões de sucessores contra os três controles

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
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

### Corpo sem margens — diagnóstico sem seleção

Mesma régua importada aplicada à projeção das palavras/linhas sem as margens automáticas da regra. Não é novo ouro humano nem substitui a página inteira; transições sobre lacunas passam a ser vizinhas.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 44 | 0,993467 | 2,931818 | 0,985674 | 0,977845 |
| hibrido67 | 44 | 0,986295 | 2,772727 | 0,988822 | 0,985116 |
| grafo_K24_maxregret_t0.00 | 44 | 0,940957 | 1,568182 | 0,990664 | 0,985138 |
| a_primeira | 44 | 0,940957 | 1,568182 | 0,990664 | 0,985138 |
| b_mediana | 44 | 0,993270 | 1,500000 | 0,992335 | 0,987092 |
| c_local | 44 | 0,940858 | 1,636364 | 0,990319 | 0,985366 |
| d_local_margens | 44 | 0,940858 | 1,636364 | 0,990319 | 0,985366 |

## validacao_silver — ajuste

| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|
| regra | 15 / 1 | 0,957218 | 16,666667 | 10,285 / 8,914 | 0,952328 | 0,910859 | 100,0% |
| hibrido67 (parcial) | 13 / 1 | 0,958544 | 17,846154 | 9,554 / 9,564 | 0,955769 | 0,916132 | 100,0% |
| grafo_K24_maxregret_t0.00 | 15 / 1 | 0,686666 | 9,466667 | 6,132 / 5,063 | 0,970249 | 0,947916 | 100,0% |
| a_primeira | 15 / 1 | 0,686666 | 9,466667 | 6,132 / 5,063 | 0,970249 | 0,947916 | 100,0% |
| b_mediana | 15 / 1 | 0,891034 | 9,266667 | 6,032 / 4,956 | 0,971302 | 0,948742 | 100,0% |
| c_local | 15 / 1 | 0,690646 | 9,466667 | 6,143 / 5,063 | 0,970124 | 0,947888 | 100,0% |
| d_local_margens | 15 / 1 | 0,690328 | 10,933333 | 6,782 / 5,847 | 0,966979 | 0,942167 | 100,0% |

### Diferenças pareadas

| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |
|---|---|---:|---|---:|---:|---:|
| grafo_K24_maxregret_t0.00 | regra | 15 | tau | -0,270551 [-0,270551; -0,270551] | 0,317311 | 3/4/8 |
| grafo_K24_maxregret_t0.00 | regra | 15 | quebras | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | quebras_mil | -4,152893 [-4,152893; -4,152893] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | fid12 | 0,017921 [0,017921; 0,017921] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | regra | 15 | sucessor_linhas | 0,037057 [0,037057; 0,037057] | 0,317311 | 10/5/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 13 | tau | -0,170445 [-0,170445; -0,170445] | 0,317311 | 3/4/6 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 13 | quebras | -8,153846 [-8,153846; -8,153846] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 13 | quebras_mil | -4,268513 [-4,268513; -4,268513] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 13 | fid12 | 0,018070 [0,018070; 0,018070] | 0,317311 | 9/4/0 |
| grafo_K24_maxregret_t0.00 | hibrido67 | 13 | sucessor_linhas | 0,038096 [0,038096; 0,038096] | 0,317311 | 9/4/0 |
| a_primeira | regra | 15 | tau | -0,270551 [-0,270551; -0,270551] | 0,317311 | 3/4/8 |
| a_primeira | regra | 15 | quebras | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| a_primeira | regra | 15 | quebras_mil | -4,152893 [-4,152893; -4,152893] | 0,317311 | 10/5/0 |
| a_primeira | regra | 15 | fid12 | 0,017921 [0,017921; 0,017921] | 0,317311 | 10/5/0 |
| a_primeira | regra | 15 | sucessor_linhas | 0,037057 [0,037057; 0,037057] | 0,317311 | 10/5/0 |
| a_primeira | hibrido67 | 13 | tau | -0,170445 [-0,170445; -0,170445] | 0,317311 | 3/4/6 |
| a_primeira | hibrido67 | 13 | quebras | -8,153846 [-8,153846; -8,153846] | 0,317311 | 9/4/0 |
| a_primeira | hibrido67 | 13 | quebras_mil | -4,268513 [-4,268513; -4,268513] | 0,317311 | 9/4/0 |
| a_primeira | hibrido67 | 13 | fid12 | 0,018070 [0,018070; 0,018070] | 0,317311 | 9/4/0 |
| a_primeira | hibrido67 | 13 | sucessor_linhas | 0,038096 [0,038096; 0,038096] | 0,317311 | 9/4/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 15 | tau | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 15 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 15 | quebras_mil | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 15 | fid12 | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| a_primeira | grafo_K24_maxregret_t0.00 | 15 | sucessor_linhas | 0,000000 [0,000000; 0,000000] | 1,000000 | 0/15/0 |
| b_mediana | regra | 15 | tau | -0,066184 [-0,066184; -0,066184] | 0,317311 | 7/4/4 |
| b_mediana | regra | 15 | quebras | -7,400000 [-7,400000; -7,400000] | 0,317311 | 10/5/0 |
| b_mediana | regra | 15 | quebras_mil | -4,252268 [-4,252268; -4,252268] | 0,317311 | 10/5/0 |
| b_mediana | regra | 15 | fid12 | 0,018974 [0,018974; 0,018974] | 0,317311 | 10/5/0 |
| b_mediana | regra | 15 | sucessor_linhas | 0,037883 [0,037883; 0,037883] | 0,317311 | 10/5/0 |
| b_mediana | hibrido67 | 13 | tau | 0,000555 [0,000555; 0,000555] | 0,317311 | 7/4/2 |
| b_mediana | hibrido67 | 13 | quebras | -8,384615 [-8,384615; -8,384615] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | 13 | quebras_mil | -4,383177 [-4,383177; -4,383177] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | 13 | fid12 | 0,019286 [0,019286; 0,019286] | 0,317311 | 9/4/0 |
| b_mediana | hibrido67 | 13 | sucessor_linhas | 0,039050 [0,039050; 0,039050] | 0,317311 | 9/4/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 15 | tau | 0,204368 [0,204368; 0,204368] | 0,317311 | 7/8/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 15 | quebras | -0,200000 [-0,200000; -0,200000] | 0,317311 | 2/13/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 15 | quebras_mil | -0,099375 [-0,099375; -0,099375] | 0,317311 | 2/13/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 15 | fid12 | 0,001054 [0,001054; 0,001054] | 0,317311 | 2/13/0 |
| b_mediana | grafo_K24_maxregret_t0.00 | 15 | sucessor_linhas | 0,000826 [0,000826; 0,000826] | 0,317311 | 2/13/0 |
| c_local | regra | 15 | tau | -0,266572 [-0,266572; -0,266572] | 0,317311 | 4/4/7 |
| c_local | regra | 15 | quebras | -7,200000 [-7,200000; -7,200000] | 0,317311 | 10/5/0 |
| c_local | regra | 15 | quebras_mil | -4,141512 [-4,141512; -4,141512] | 0,317311 | 10/5/0 |
| c_local | regra | 15 | fid12 | 0,017796 [0,017796; 0,017796] | 0,317311 | 10/5/0 |
| c_local | regra | 15 | sucessor_linhas | 0,037029 [0,037029; 0,037029] | 0,317311 | 10/5/0 |
| c_local | hibrido67 | 13 | tau | -0,165854 [-0,165854; -0,165854] | 0,317311 | 4/4/5 |
| c_local | hibrido67 | 13 | quebras | -8,153846 [-8,153846; -8,153846] | 0,317311 | 9/4/0 |
| c_local | hibrido67 | 13 | quebras_mil | -4,255382 [-4,255382; -4,255382] | 0,317311 | 9/4/0 |
| c_local | hibrido67 | 13 | fid12 | 0,017926 [0,017926; 0,017926] | 0,317311 | 9/4/0 |
| c_local | hibrido67 | 13 | sucessor_linhas | 0,038064 [0,038064; 0,038064] | 0,317311 | 9/4/0 |
| c_local | grafo_K24_maxregret_t0.00 | 15 | tau | 0,003979 [0,003979; 0,003979] | 0,317311 | 2/13/0 |
| c_local | grafo_K24_maxregret_t0.00 | 15 | quebras | 0,000000 [0,000000; 0,000000] | 1,000000 | 1/13/1 |
| c_local | grafo_K24_maxregret_t0.00 | 15 | quebras_mil | 0,011380 [0,011380; 0,011380] | 0,317311 | 1/13/1 |
| c_local | grafo_K24_maxregret_t0.00 | 15 | fid12 | -0,000125 [-0,000125; -0,000125] | 0,317311 | 1/13/1 |
| c_local | grafo_K24_maxregret_t0.00 | 15 | sucessor_linhas | -0,000028 [-0,000028; -0,000028] | 0,317311 | 1/13/1 |
| d_local_margens | regra | 15 | tau | -0,266890 [-0,266890; -0,266890] | 0,317311 | 4/4/7 |
| d_local_margens | regra | 15 | quebras | -5,733333 [-5,733333; -5,733333] | 0,317311 | 10/5/0 |
| d_local_margens | regra | 15 | quebras_mil | -3,502717 [-3,502717; -3,502717] | 0,317311 | 10/5/0 |
| d_local_margens | regra | 15 | fid12 | 0,014651 [0,014651; 0,014651] | 0,317311 | 10/5/0 |
| d_local_margens | regra | 15 | sucessor_linhas | 0,031308 [0,031308; 0,031308] | 0,317311 | 10/5/0 |
| d_local_margens | hibrido67 | 13 | tau | -0,166220 [-0,166220; -0,166220] | 0,317311 | 4/4/5 |
| d_local_margens | hibrido67 | 13 | quebras | -6,461538 [-6,461538; -6,461538] | 0,317311 | 9/4/0 |
| d_local_margens | hibrido67 | 13 | quebras_mil | -3,518310 [-3,518310; -3,518310] | 0,317311 | 9/4/0 |
| d_local_margens | hibrido67 | 13 | fid12 | 0,014297 [0,014297; 0,014297] | 0,317311 | 9/4/0 |
| d_local_margens | hibrido67 | 13 | sucessor_linhas | 0,031463 [0,031463; 0,031463] | 0,317311 | 9/4/0 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 15 | tau | 0,003661 [0,003661; 0,003661] | 0,317311 | 4/8/3 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 15 | quebras | 1,466667 [1,466667; 1,466667] | 0,317311 | 0/8/7 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 15 | quebras_mil | 0,650176 [0,650176; 0,650176] | 0,317311 | 0/8/7 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 15 | fid12 | -0,003270 [-0,003270; -0,003270] | 0,317311 | 0/9/6 |
| d_local_margens | grafo_K24_maxregret_t0.00 | 15 | sucessor_linhas | -0,005749 [-0,005749; -0,005749] | 0,317311 | 0/8/7 |

### Δ por veículo — variante de maior τ no ajuste, sem seleção válida

| Método | Base | Veículo | Δ quebras | Δτ |
|---|---|---|---:|---:|
| b_mediana | regra | official_diary_rn | -7,400000 | -0,066184 |
| b_mediana | hibrido67 | official_diary_rn | -8,384615 | 0,000555 |
| b_mediana | grafo_K24_maxregret_t0.00 | official_diary_rn | -0,200000 | 0,204368 |

### Sucessores: reparos e regressões contra a regra

Contagens de transições de linhas, sem compensar regressões com reparos de outra classe.

| Método | Classe | Referência | Certos | Reparos | Regressões | Quebras |
|---|---|---:|---:|---:|---:|---:|
| regra | mesma_coluna | 2245 | 2224 | 0 | 0 | 21 |
| regra | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| regra | tabela_imagem | 18 | 10 | 0 | 0 | 8 |
| regra | transversal | 13 | 6 | 0 | 0 | 6 |
| regra | margem | 132 | 46 | 0 | 0 | 79 |
| regra | outro | 2601 | 2473 | 0 | 0 | 136 |
| hibrido67 | mesma_coluna | 2223 | 2202 | 0 | 0 | 21 |
| hibrido67 | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| hibrido67 | tabela_imagem | 13 | 10 | 0 | 0 | 3 |
| hibrido67 | transversal | 13 | 6 | 0 | 0 | 6 |
| hibrido67 | margem | 118 | 41 | 0 | 0 | 71 |
| hibrido67 | outro | 340 | 216 | 0 | 0 | 131 |
| grafo_K24_maxregret_t0.00 | mesma_coluna | 2245 | 2241 | 17 | 0 | 4 |
| grafo_K24_maxregret_t0.00 | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| grafo_K24_maxregret_t0.00 | tabela_imagem | 18 | 10 | 0 | 0 | 7 |
| grafo_K24_maxregret_t0.00 | transversal | 13 | 7 | 1 | 0 | 5 |
| grafo_K24_maxregret_t0.00 | margem | 132 | 84 | 38 | 0 | 42 |
| grafo_K24_maxregret_t0.00 | outro | 2601 | 2525 | 53 | 1 | 84 |
| a_primeira | mesma_coluna | 2245 | 2241 | 17 | 0 | 4 |
| a_primeira | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| a_primeira | tabela_imagem | 18 | 10 | 0 | 0 | 7 |
| a_primeira | transversal | 13 | 7 | 1 | 0 | 5 |
| a_primeira | margem | 132 | 84 | 38 | 0 | 42 |
| a_primeira | outro | 2601 | 2525 | 53 | 1 | 84 |
| b_mediana | mesma_coluna | 2245 | 2241 | 17 | 0 | 4 |
| b_mediana | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| b_mediana | tabela_imagem | 18 | 10 | 0 | 0 | 7 |
| b_mediana | transversal | 13 | 7 | 1 | 0 | 5 |
| b_mediana | margem | 132 | 87 | 41 | 0 | 39 |
| b_mediana | outro | 2601 | 2525 | 53 | 1 | 84 |
| c_local | mesma_coluna | 2245 | 2241 | 17 | 0 | 4 |
| c_local | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| c_local | tabela_imagem | 18 | 10 | 0 | 0 | 7 |
| c_local | transversal | 13 | 6 | 0 | 0 | 6 |
| c_local | margem | 132 | 85 | 39 | 0 | 41 |
| c_local | outro | 2601 | 2525 | 53 | 1 | 84 |
| d_local_margens | mesma_coluna | 2245 | 2241 | 17 | 0 | 4 |
| d_local_margens | proxima_coluna | 3 | 3 | 0 | 0 | 0 |
| d_local_margens | tabela_imagem | 18 | 10 | 0 | 0 | 7 |
| d_local_margens | transversal | 13 | 6 | 0 | 0 | 6 |
| d_local_margens | margem | 132 | 63 | 18 | 1 | 63 |
| d_local_margens | outro | 2601 | 2525 | 53 | 1 | 84 |

### Reparos/regressões de sucessores contra os três controles

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
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

### Corpo sem margens — diagnóstico sem seleção

Mesma régua importada aplicada à projeção das palavras/linhas sem as margens automáticas da regra. Não é novo ouro humano nem substitui a página inteira; transições sobre lacunas passam a ser vizinhas.

| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 15 | 0,977603 | 11,200000 | 0,972619 | 0,945747 |
| hibrido67 | 13 | 0,974157 | 12,230769 | 0,968886 | 0,937706 |
| grafo_K24_maxregret_t0.00 | 15 | 0,684942 | 6,933333 | 0,977618 | 0,965229 |
| a_primeira | 15 | 0,684942 | 6,933333 | 0,977618 | 0,965229 |
| b_mediana | 15 | 0,902498 | 6,533333 | 0,982103 | 0,969539 |
| c_local | 15 | 0,688695 | 7,066667 | 0,976925 | 0,964494 |
| d_local_margens | 15 | 0,688695 | 7,066667 | 0,976925 | 0,964494 |

## golden_v3_novo — não executada

Não houve variante elegível para congelar no ajuste. A bancada não foi aberta nem avaliada pelo E014; não há resultado a registrar.

## teste_silver — não executada

Não houve variante elegível para congelar no ajuste. A bancada não foi aberta nem avaliada pelo E014; não há resultado a registrar.

## Híbrido 67 com variante nas páginas densas — não executado

A combinação exploratória depende da variante congelada. Sem variante elegível, não se escolhe uma alternativa inválida para completar esta análise.

## Veredito pelo cartão E014

NÃO GO / abandono: nenhuma variante atende a margem de τ no ajuste.

Próximo passo indicado pelo próprio cartão: decodificação com restrição global de coluna/blocos ou GNN (E011). Apenas filtrar arestas pela coluna não garante a ordem global das cadeias, pois uma cadeia que começa em cabeçalho ainda pode ancorar uma coluna inteira cedo demais.

## Limitações e retomada

Resultado exploratório: golden_v4 já orientou a regra; golden_v3_novo foi consultado em rodadas anteriores. As bancadas se sobrepõem e não são somadas. Silver tem ruído na referência PDF e piso interno aos átomos; a contagem de cadeias corretas é diagnóstico, sem atribuição humana de causalidade. Mediana é por unidade, sem ponderar palavras. Coluna/margem é proxy geométrica congelada. O experimento reusa um modelo de uma semente, sem estimar variância de treino. IC com poucos veículos (três no teste silver e um em RN) é limitado. A combinação híbrida não participa do veredito/seleção. Nenhum teste cego foi aberto.

Executar `venv/Scripts/python.exe -B orquestracao/analises/e014_cadeias.py` retoma por página; `--etapa diagnostico` e `--etapa ajuste` nunca abrem externas. `--conferir` verifica assinatura, relatório e resumo sem nova inferência. RAM livre mínima 800 MiB, commit livre 1.200 MiB, RSS máximo 3.072 MiB; uma página e um processo por vez.
