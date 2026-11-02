# Margens e elementos transversais sobre linhas

Margens no v4: Cabeçalho multilinha/lado a lado fora de ordem = 28 sucessores perdidos; Marca marginal em posição errada = 40 sucessores perdidos; Corpo tratado como margem pelo limiar = 47 sucessores perdidos.  
Variante congelada: ev1_colunas_marca1_gap1.0_ponte0.06; margens por branco/continuidade, leitura por colunas e marcas pela posição, conforme ablações abaixo.  
Fora do ajuste: golden_v3_novo (27 páginas): Δ quebras -0,481 [-1,368; 0,591], Δ τ 0,000108 [-0,001201; 0,001528]; teste_silver (68 páginas): Δ quebras -0,676 [-1,677; 0,433], Δ τ -0,001297 [-0,003016; 0,000097].  
Não resolveu todas as margens/átomos: no v3, a fidelidade de 12 caiu 0,461 ponto percentual, e marcas tiveram 4 perdas líquidas a mais.  
Veredito: golden_v3_novo: menos quebras e τ maior/igual; IC das quebras inclui zero; teste_silver: menos quebras, com queda de τ; IC das quebras inclui zero.

Este relatório é escrito pelo script, a partir dos resultados por página. Não usa GPU, treino, rede ou Label Studio.

## Âncoras

Status: aprovadas; 44 páginas reexecutadas.

| Controle | τ palavras | Quebras/página |
|---|---:|---:|
| Regra original | 0,985948 | 6,045455 |
| Extrator + XY-cut + margens | 0,952424 | 8,931818 |

A ordem da regra é reexecutada com as unidades/átomos congelados e conferida palavra por palavra contra P2 histórico. Para o controle do extrator, reavaliam-se as sequências históricas P1m na referência atual; não se reextraem PDFs nem se reinfere o detector.

## Diagnóstico fino

Reutiliza `contexto`, `categoria` e `preparar_avaliacao` de `corretor_de_transicoes.py`. Cada sucessor-ouro de margem perdido recebe um subtipo exclusivo: corpo erroneamente separado, marca, par de cabeçalhos, cabeçalho após corpo, rodapé antes do corpo, outro. **Somente no diagnóstico v4**, usa a classe da região nas tarefas congeladas (cabecalho/rodape/texto etc.); as classes ficam fora do preditor. No v3, que não possui esse campo, usa proxies conservadores de texto/geometria. A classificação de subtipos das duas coortes não tem a mesma qualidade de supervisão. Um mesmo deslocamento pode perder mais de um sucessor. Quebras emitidas e sucessores perdidos têm denominadores distintos.

Cabeçalho combina faixa superior e vocabulário editorial; marca combina regex original, número isolado em borda ou forma lateral; rodapé combina faixa inferior e vocabulário de assinatura/publicação. Continuidade espacial/textual dá evidência de corpo. Os shards não guardam fonte/tamanho: não se inventa informação tipográfica.

### golden_v4

Veículos do treino original: 5 páginas vistas; 39 não vistas. Estratos vazios não recebem médias.

**todos: 44 páginas; 27 veículos.**

| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |
|---|---:|---:|---:|
| (a) Cabeçalho enviado para depois do corpo | 0 | 0,0% | 0 |
| (b) Rodapé antes de parte do corpo | 1 | 0,8% | 1 |
| (c) Cabeçalho multilinha/lado a lado fora de ordem | 28 | 21,4% | 39 |
| (d) Marca marginal em posição errada | 40 | 30,5% | 35 |
| (e) Corpo tratado como margem pelo limiar | 47 | 35,9% | 44 |
| (f) Outro / evidência insuficiente | 15 | 11,5% | 15 |
| Total | 131 | 100,0% | 134 |

**vistos: 5 páginas; 5 veículos.**

| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |
|---|---:|---:|---:|
| (a) Cabeçalho enviado para depois do corpo | 0 | 0,0% | 0 |
| (b) Rodapé antes de parte do corpo | 0 | 0,0% | 0 |
| (c) Cabeçalho multilinha/lado a lado fora de ordem | 0 | 0,0% | 0 |
| (d) Marca marginal em posição errada | 1 | 14,3% | 1 |
| (e) Corpo tratado como margem pelo limiar | 6 | 85,7% | 4 |
| (f) Outro / evidência insuficiente | 0 | 0,0% | 0 |
| Total | 7 | 100,0% | 5 |

**nao_vistos: 39 páginas; 22 veículos.**

| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |
|---|---:|---:|---:|
| (a) Cabeçalho enviado para depois do corpo | 0 | 0,0% | 0 |
| (b) Rodapé antes de parte do corpo | 1 | 0,8% | 1 |
| (c) Cabeçalho multilinha/lado a lado fora de ordem | 28 | 22,6% | 39 |
| (d) Marca marginal em posição errada | 39 | 31,5% | 34 |
| (e) Corpo tratado como margem pelo limiar | 41 | 33,1% | 40 |
| (f) Outro / evidência insuficiente | 15 | 12,1% | 15 |
| Total | 124 | 100,0% | 129 |

### golden_v3_novo

Veículos do treino original: 0 páginas vistas; 27 não vistas. Estratos vazios não recebem médias.

**todos: 27 páginas; 10 veículos.**

| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |
|---|---:|---:|---:|
| (a) Cabeçalho enviado para depois do corpo | 0 | 0,0% | 0 |
| (b) Rodapé antes de parte do corpo | 0 | 0,0% | 0 |
| (c) Cabeçalho multilinha/lado a lado fora de ordem | 17 | 41,5% | 16 |
| (d) Marca marginal em posição errada | 8 | 19,5% | 10 |
| (e) Corpo tratado como margem pelo limiar | 4 | 9,8% | 4 |
| (f) Outro / evidência insuficiente | 12 | 29,3% | 11 |
| Total | 41 | 100,0% | 41 |

**nao_vistos: 27 páginas; 10 veículos.**

| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |
|---|---:|---:|---:|
| (a) Cabeçalho enviado para depois do corpo | 0 | 0,0% | 0 |
| (b) Rodapé antes de parte do corpo | 0 | 0,0% | 0 |
| (c) Cabeçalho multilinha/lado a lado fora de ordem | 17 | 41,5% | 16 |
| (d) Marca marginal em posição errada | 8 | 19,5% | 10 |
| (e) Corpo tratado como margem pelo limiar | 4 | 9,8% | 4 |
| (f) Outro / evidência insuficiente | 12 | 29,3% | 11 |
| Total | 41 | 100,0% | 41 |

### Exemplos reais

São mostrados até três exemplos por subtipo, priorizando páginas distintas. Texto completo de todas as ocorrências e IDs de linha ficam nos caches; falta de exemplos não é preenchida artificialmente.

**(a) Cabeçalho enviado para depois do corpo**

Nenhuma ocorrência atribuída a este subtipo nesta execução.


**(b) Rodapé antes de parte do corpo**

Há somente 1 ocorrência(s) atribuída(s); não existem três exemplos para mostrar sem mudar a classificação ou inventar casos.

- `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0` (golden_v4; b11:l0 → b0:l0; entre unidades).
  - Humana: «ATO CONCESSÓRIO DE PENSÃO Nº 83 DE 25/07/2023» → «Autenticidade pode ser verificada em: https://ppe.sistemas.ro.gov.br/Diof/Pdf/17024».
  - Regra: «ATO CONCESSÓRIO DE PENSÃO Nº 83 DE 25/07/2023» → «Protocolo».

**(c) Cabeçalho multilinha/lado a lado fora de ordem**

- `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` (golden_v4; b17:l1 → b12:l0; entre unidades).
  - Humana: «do Município» → «Quarta-feira».
  - Regra: «do Município» → «28 de Setembro de 2022».
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` (golden_v4; b34:l0 → b22:l0; entre unidades).
  - Humana: «BOS do Boletim Município Oficial de Seropédica» → «Seropédica».
  - Regra: «BOS do Boletim Município Oficial de Seropédica» → «Artigo 4º: No laudo a ser realizado pela Comissão, no exercício de suas atribuições,».
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p3` (golden_v4; b5:l1 → b5:l2; entre unidades).
  - Humana: «Segunda-feira, 09 de Maio de 2022» → «Ano V - Nº 986».
  - Regra: «Segunda-feira, 09 de Maio de 2022» → «BOS do Boletim Município Oficial de Seropédica».

**(d) Marca marginal em posição errada**

- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` (golden_v4; b12:l0 → b1:l0; entre unidades).
  - Humana: «w w w . congonhas . m g . g o v . b r» → «2».
  - Regra: «w w w . congonhas . m g . g o v . b r» → «[fora da referência / fim]».
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` (golden_v4; b5:l0 → b2:l0; entre unidades).
  - Humana: «Barra do Piraí/RJ» → «3».
  - Regra: «Barra do Piraí/RJ» → «www.barradopirai.rj.gov.br».
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3` (golden_v4; b4:l0 → b3:l0; entre unidades).
  - Humana: «Barra do Piraí/RJ» → «4».
  - Regra: «Barra do Piraí/RJ» → «www.barradopirai.rj.gov.br».

**(e) Corpo tratado como margem pelo limiar**

- `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` (golden_v4; b11:l7 → b11:l8; entre unidades).
  - Humana: «Presidente: Silas Nogueira de Freitas Júnior» → «CONSELHO DE CONTRIBUINTE».
  - Regra: «Presidente: Silas Nogueira de Freitas Júnior» → «PODER LEGISLATIVO».
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114` (golden_v4; b8:l0 → b7:l0; entre unidades).
  - Humana: «DIÁRIO OFICIAL 115» → «de 2017, bem como, considerando o princípio da delegação de competência,».
  - Regra: «DIÁRIO OFICIAL 115» → «Nº 13.961».
- `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35` (golden_v4; b34:l5 → b34:l6; entre unidades).
  - Humana: «conforme requisitos técnicos a serem definidos em» → «regulamentação própria.».
  - Regra: «conforme requisitos técnicos a serem definidos em» → «Art. 7º Durante a realização da vistoria de identificação».

**(f) Outro / evidência insuficiente**

- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` (golden_v4; b9:l1 → b12:l0; entre unidades).
  - Humana: «MUNICÍPIO DE CONGONHAS» → «w w w . congonhas . m g . g o v . b r».
  - Regra: «MUNICÍPIO DE CONGONHAS» → «2».
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` (golden_v4; b4:l4 → b5:l0; entre unidades).
  - Humana: «Secretaria Municipal de Saúde.............................................................................................................................................................................................................................................................13» → «Barra do Piraí/RJ».
  - Regra: «Secretaria Municipal de Saúde.............................................................................................................................................................................................................................................................13» → «DIÁRIO OFICIAL ELETRÔNICO garante autenticidade».
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3` (golden_v4; b2:l0 → b6:l0; entre unidades).
  - Humana: «Boletim do Município de Barra do Piraí - Poderes Executivo e Legislativo | Ano 19 | Nº 214 | 24 de Novembro de 2023» → «ATOS DO PODER EXECUTIVO».
  - Regra: «Boletim do Município de Barra do Piraí - Poderes Executivo e Legislativo | Ano 19 | Nº 214 | 24 de Novembro de 2023» → «ADMINISTRAÇÃO».

## Variante e ajuste congelado

O preditor `prever(p, ws, parametros)` remove todos os campos humanos/silver antes de ordenar. A grade testa ordenação das margens por XY-cut (colunas) ou bandas de altura próxima; deslocamento das marcas de diagramação conforme sua posição; separação de margens pela maior faixa de branco nas bordas e continuidade com o corpo; e barreiras transversais que dividem corpo acima/abaixo. A regra original já trata pontes: a ablação transversal testa uma exigência alternativa de largura/suporte. Unidades e suas palavras internas permanecem congeladas. Nenhum exemplo do v3 ou de CE/MA/RJ seleciona parâmetros.

Parâmetros escolhidos: `{"evidencia": true, "gap_h": 1.0, "marcas_geo": true, "nome": "ev1_colunas_marca1_gap1.0_ponte0.06", "ordem_margens": "colunas", "ponte": 0.06}`.

Critério definido antes da avaliação final: minimizar soma das médias de quebras v4+RN; perda de tau <=0,002 em cada coorte; maior tau e nome como desempate. Os candidatos e os limiares foram desenhados a partir do diagnóstico v4. A consulta ao diagnóstico v3 exigida nesta tarefa não permite tratá-lo como validação cega da ideia; seus resultados não foram usados no ajuste numérico.

| Candidato | v4: τ / quebras | RN: τ / quebras |
|---|---:|---:|
| original | 0,985948 / 6,045 | 0,954162 / 17,857 |
| ev0_colunas_marca0 | 0,987841 / 5,364 | 0,954110 / 18,143 |
| ev0_colunas_marca1 | 0,988283 / 5,091 | 0,954110 / 18,143 |
| ev0_faixas_marca0 | 0,987178 / 5,341 | 0,954184 / 18,786 |
| ev0_faixas_marca1 | 0,987621 / 5,068 | 0,954184 / 18,786 |
| ev1_colunas_marca0 | 0,988888 / 5,205 | 0,961383 / 15,500 |
| ev1_colunas_marca1 | 0,989329 / 4,977 | 0,961383 / 15,500 |
| ev1_faixas_marca0 | 0,988081 / 5,318 | 0,961331 / 16,786 |
| ev1_faixas_marca1 | 0,988523 / 5,045 | 0,961331 / 16,786 |
| ev1_colunas_marca1_gap0.7_ponte0 | 0,989329 / 4,977 | 0,961383 / 15,500 |
| ev1_colunas_marca1_gap1.5_ponte0 | 0,990104 / 4,955 | 0,964871 / 15,429 |
| ev1_colunas_marca1_gap1.0_ponte0.06 | 0,989434 / 4,341 | 0,961389 / 15,143 |
| ev1_colunas_marca1_gap1.0_ponte0.1 | 0,989434 / 4,341 | 0,961389 / 15,143 |

RN exclui páginas presentes nas tarefas humanas, inclusive a tarefa v4 ainda sem conclusão. Seus IDs de ajuste estão no estado; sete veículos de treino são lidos somente do split para estratificar. Esta regra não aprende em páginas silver de treino e não usa repetição de páginas, fonte ou tamanho de fonte.

## Avaliação pareada

Médias por página, IC 95% por bootstrap de **veículos** (funções da bancada, 5.000 réplicas). Δ = variante − original. Wilcoxon bilateral Pratt aplicado a uma média de diferença por veículo; não se contam páginas de um veículo como observações independentes. RN tem apenas um veículo (IC degenerado) e CE/MA/RJ apenas três: inferência limitada. Percentuais de fidelidade e sucessor estão em pontos percentuais nos contrastes. Sem correção para múltiplas comparações.

| Bancada / estrato | n / veículos | τ original → v2 | Quebras original → v2 | Fidelidade 12 original → v2 | Sucessor linhas original → v2 | Melhor / igual / pior em quebras |
|---|---:|---:|---:|---:|---:|---:|
| golden_v4 / todos | 44 / 27 | 0,985948 → 0,989434 | 6,045 → 4,341 | 94,813 → 96,027 | 92,724 → 94,779 | 18 / 22 / 4 |
| golden_v4 / vistos | 5 / 5 | 0,997638 → 0,994632 | 4,800 → 5,000 | 98,491 → 98,481 | 97,698 → 97,526 | 1 / 2 / 2 |
| golden_v4 / nao_vistos | 39 / 22 | 0,984450 → 0,988767 | 6,205 → 4,256 | 94,341 → 95,713 | 92,086 → 94,427 | 17 / 20 / 2 |
| golden_v3_novo / todos | 27 / 10 | 0,959557 → 0,959665 | 9,222 → 8,741 | 92,841 → 92,381 | 91,130 → 91,098 | 10 / 12 / 5 |
| golden_v3_novo / nao_vistos | 27 / 10 | 0,959557 → 0,959665 | 9,222 → 8,741 | 92,841 → 92,381 | 91,130 → 91,098 | 10 / 12 / 5 |
| validacao_silver / todos | 14 / 1 | 0,954162 → 0,961389 | 17,857 → 15,143 | 94,892 → 96,252 | 90,449 → 92,110 | 7 / 5 / 2 |
| teste_silver / todos | 89 / 3 | 0,959565 → 0,958867 | 27,449 → 26,483 | 82,540 → 83,098 | 84,021 → 84,971 | 47 / 34 / 8 |
| teste_silver / sem_humanas | 68 / 3 | 0,972209 → 0,970912 | 29,485 → 28,809 | 81,796 → 82,044 | 82,640 → 83,322 | 36 / 24 / 8 |

| Bancada / estrato | Métrica | Original [IC] | v2 [IC] | Δ [IC por veículo] | p Wilcoxon por veículo |
|---|---|---:|---:|---:|---:|
| golden_v4 / todos | tau | 0,985948 [0,973495; 0,995020] | 0,989434 [0,977200; 0,996899] | 0,003485 [-0,000030; 0,007818] | 0,020306 |
| golden_v4 / todos | quebras | 6,045 [4,023; 8,887] | 4,341 [3,053; 5,864] | -1,705 [-3,364; -0,535] | 0,014266 |
| golden_v4 / todos | fid12 | 94,813 [91,355; 97,241] | 96,027 [93,278; 98,063] | 1,214 [0,423; 2,118] | 0,003235 |
| golden_v4 / todos | sucessor_linhas | 92,724 [87,810; 96,083] | 94,779 [91,607; 97,150] | 2,055 [0,645; 3,933] | 0,004704 |
| golden_v4 / vistos | tau | 0,997638 [0,994112; 0,999926] | 0,994632 [0,984101; 0,999997] | -0,003006 [-0,010044; 0,001091] | 0,571608 |
| golden_v4 / vistos | quebras | 4,800 [2,600; 7,600] | 5,000 [2,000; 8,200] | 0,200 [-1,600; 1,800] | 0,669815 |
| golden_v4 / vistos | fid12 | 98,491 [98,094; 98,887] | 98,481 [97,519; 99,412] | -0,010 [-0,707; 0,569] | 0,777297 |
| golden_v4 / vistos | sucessor_linhas | 97,698 [96,955; 98,545] | 97,526 [95,084; 99,306] | -0,172 [-2,436; 1,651] | 0,777297 |
| golden_v4 / nao_vistos | tau | 0,984450 [0,970860; 0,994281] | 0,988767 [0,975509; 0,997092] | 0,004318 [0,000597; 0,009043] | 0,004112 |
| golden_v4 / nao_vistos | quebras | 6,205 [4,000; 9,395] | 4,256 [2,886; 5,868] | -1,949 [-3,818; -0,687] | 0,003027 |
| golden_v4 / nao_vistos | fid12 | 94,341 [90,336; 97,031] | 95,713 [92,536; 97,957] | 1,371 [0,493; 2,428] | 0,002380 |
| golden_v4 / nao_vistos | sucessor_linhas | 92,086 [86,600; 95,774] | 94,427 [90,856; 97,043] | 2,340 [0,822; 4,442] | 0,002579 |
| golden_v3_novo / todos | tau | 0,959557 [0,915350; 0,997056] | 0,959665 [0,916567; 0,996273] | 0,000108 [-0,001201; 0,001528] | 0,225872 |
| golden_v3_novo / todos | quebras | 9,222 [4,900; 12,867] | 8,741 [5,300; 11,818] | -0,481 [-1,368; 0,591] | 0,186115 |
| golden_v3_novo / todos | fid12 | 92,841 [89,859; 96,585] | 92,381 [90,386; 95,003] | -0,461 [-2,060; 0,592] | 0,270912 |
| golden_v3_novo / todos | sucessor_linhas | 91,130 [88,065; 93,556] | 91,098 [88,396; 93,198] | -0,032 [-1,440; 0,966] | 0,270912 |
| golden_v3_novo / nao_vistos | tau | 0,959557 [0,915350; 0,997056] | 0,959665 [0,916567; 0,996273] | 0,000108 [-0,001201; 0,001528] | 0,225872 |
| golden_v3_novo / nao_vistos | quebras | 9,222 [4,900; 12,867] | 8,741 [5,300; 11,818] | -0,481 [-1,368; 0,591] | 0,186115 |
| golden_v3_novo / nao_vistos | fid12 | 92,841 [89,859; 96,585] | 92,381 [90,386; 95,003] | -0,461 [-2,060; 0,592] | 0,270912 |
| golden_v3_novo / nao_vistos | sucessor_linhas | 91,130 [88,065; 93,556] | 91,098 [88,396; 93,198] | -0,032 [-1,440; 0,966] | 0,270912 |
| validacao_silver / todos | tau | 0,954162 [0,954162; 0,954162] | 0,961389 [0,961389; 0,961389] | 0,007227 [0,007227; 0,007227] | 0,317311 |
| validacao_silver / todos | quebras | 17,857 [17,857; 17,857] | 15,143 [15,143; 15,143] | -2,714 [-2,714; -2,714] | 0,317311 |
| validacao_silver / todos | fid12 | 94,892 [94,892; 94,892] | 96,252 [96,252; 96,252] | 1,360 [1,360; 1,360] | 0,317311 |
| validacao_silver / todos | sucessor_linhas | 90,449 [90,449; 90,449] | 92,110 [92,110; 92,110] | 1,661 [1,661; 1,661] | 0,317311 |
| teste_silver / todos | tau | 0,959565 [0,889505; 0,998435] | 0,958867 [0,890435; 0,998849] | -0,000699 [-0,002368; 0,000930] | 1,000000 |
| teste_silver / todos | quebras | 27,449 [22,184; 32,316] | 26,483 [20,447; 32,658] | -0,966 [-2,538; 0,342] | 0,285049 |
| teste_silver / todos | fid12 | 82,540 [72,935; 89,872] | 83,098 [72,715; 91,157] | 0,558 [-0,220; 1,285] | 0,285049 |
| teste_silver / todos | sucessor_linhas | 84,021 [77,080; 94,086] | 84,971 [76,764; 94,869] | 0,949 [-0,317; 2,273] | 0,285049 |
| teste_silver / sem_humanas | tau | 0,972209 [0,944150; 0,998595] | 0,970912 [0,941135; 0,998646] | -0,001297 [-0,003016; 0,000097] | 1,000000 |
| teste_silver / sem_humanas | quebras | 29,485 [24,903; 33,633] | 28,809 [23,226; 34,067] | -0,676 [-1,677; 0,433] | 0,285049 |
| teste_silver / sem_humanas | fid12 | 81,796 [72,025; 90,435] | 82,044 [71,747; 90,783] | 0,248 [-0,278; 0,735] | 0,285049 |
| teste_silver / sem_humanas | sucessor_linhas | 82,640 [75,597; 95,759] | 83,322 [75,196; 95,994] | 0,682 [-0,401; 1,832] | 0,592980 |

Teste silver integral: 89 páginas, das quais 21 também estão nas tarefas humanas. A tabela integral preserva o contrato da bancada histórica; **o estrato sem_humanas (68 páginas) é a comparação de teste sem sobreposição com o ajuste humano**. A retirada é apenas uma análise adicional, não alteração do split nem das predições integrais. O v3 tem páginas disjuntas do v4. A referência silver pode discordar das tabelas expandidas geometricamente; seu piso absoluto de quebras é alto.

**Conclusão observada:** golden_v3_novo: menos quebras e τ maior/igual; IC das quebras inclui zero; teste_silver: menos quebras, com queda de τ; IC das quebras inclui zero.

### Diferenças médias por veículo fora do ajuste

| Bancada / estrato | Veículo | Δ τ | Δ quebras | Δ fidelidade 12 (pp) | Δ sucessor linhas (pp) |
|---|---|---:|---:|---:|---:|
| golden_v3_novo / todos | official_diary_RJ_barra_do_pirai | 0,000388 | -1,000 | 0,675 | 1,282 |
| golden_v3_novo / todos | official_diary_ac | 0,000000 | 0,000 | 0,000 | 0,000 |
| golden_v3_novo / todos | official_diary_ap | 0,000000 | 0,000 | 0,000 | 0,000 |
| golden_v3_novo / todos | official_diary_ce | -0,002304 | 1,333 | -3,662 | -2,772 |
| golden_v3_novo / todos | official_diary_ma | 0,000093 | -1,143 | 0,715 | 1,089 |
| golden_v3_novo / todos | official_diary_mg | 0,000000 | 0,000 | 0,000 | 0,000 |
| golden_v3_novo / todos | official_diary_pi_v2 | 0,000000 | 0,000 | 0,000 | 0,000 |
| golden_v3_novo / todos | official_diary_rj | 0,002292 | -2,000 | 0,719 | 0,992 |
| golden_v3_novo / todos | official_diary_ro | 0,000000 | 0,000 | 0,000 | 0,000 |
| golden_v3_novo / todos | official_diary_se | 0,004240 | -2,000 | 0,258 | 1,905 |
| teste_silver / sem_humanas | official_diary_ce | 0,000051 | -1,677 | 0,735 | 1,832 |
| teste_silver / sem_humanas | official_diary_ma | -0,003016 | 0,433 | -0,278 | -0,401 |
| teste_silver / sem_humanas | official_diary_rj | 0,000097 | -1,000 | 0,348 | 0,236 |

### Sucessores perdidos por tipo de transição

A categoria é a da regra original congelada, para não mudar o denominador depois de alterar margens. Corrigidas e novas são fronteiras-ouro completas (ambas as linhas intactas e adjacentes), não apenas acerto de pares de IDs.

| Bancada | Tipo | Original | v2 | Corrigidas | Novas perdas |
|---|---|---:|---:|---:|---:|
| golden_v4 | Continuação na mesma coluna | 48 | 37 | 14 | 3 |
| golden_v4 | Fim de coluna → topo da próxima | 3 | 3 | 0 | 0 |
| golden_v4 | Entrada/saída de tabela ou imagem | 8 | 9 | 0 | 1 |
| golden_v4 | Salto ou fronteira de elemento transversal | 18 | 3 | 15 | 0 |
| golden_v4 | Cabeçalho/rodapé/marca marginal | 131 | 78 | 64 | 11 |
| golden_v4 | Outro | 29 | 29 | 2 | 2 |
| golden_v3_novo | Continuação na mesma coluna | 115 | 116 | 0 | 1 |
| golden_v3_novo | Fim de coluna → topo da próxima | 2 | 2 | 0 | 0 |
| golden_v3_novo | Entrada/saída de tabela ou imagem | 9 | 9 | 0 | 0 |
| golden_v3_novo | Salto ou fronteira de elemento transversal | 2 | 2 | 0 | 0 |
| golden_v3_novo | Cabeçalho/rodapé/marca marginal | 41 | 25 | 23 | 7 |
| golden_v3_novo | Outro | 69 | 69 | 0 | 0 |

### Ganhos e perdas nos subtipos de margem

| Bancada | Subtipo | Original | v2 | Corrigidas | Novas perdas | Δ perdas |
|---|---|---:|---:|---:|---:|---:|
| golden_v4 | (a) Cabeçalho enviado para depois do corpo | 0 | 0 | 0 | 0 | 0 |
| golden_v4 | (b) Rodapé antes de parte do corpo | 1 | 1 | 0 | 0 | 0 |
| golden_v4 | (c) Cabeçalho multilinha/lado a lado fora de ordem | 28 | 20 | 14 | 6 | -8 |
| golden_v4 | (d) Marca marginal em posição errada | 40 | 24 | 16 | 0 | -16 |
| golden_v4 | (e) Corpo tratado como margem pelo limiar | 47 | 25 | 26 | 4 | -22 |
| golden_v4 | (f) Outro / evidência insuficiente | 15 | 8 | 8 | 1 | -7 |
| golden_v3_novo | (a) Cabeçalho enviado para depois do corpo | 0 | 0 | 0 | 0 | 0 |
| golden_v3_novo | (b) Rodapé antes de parte do corpo | 0 | 0 | 0 | 0 | 0 |
| golden_v3_novo | (c) Cabeçalho multilinha/lado a lado fora de ordem | 17 | 10 | 7 | 0 | -7 |
| golden_v3_novo | (d) Marca marginal em posição errada | 8 | 12 | 3 | 7 | 4 |
| golden_v3_novo | (e) Corpo tratado como margem pelo limiar | 4 | 0 | 4 | 0 | -4 |
| golden_v3_novo | (f) Outro / evidência insuficiente | 12 | 3 | 9 | 0 | -9 |

golden_v4: nenhum subtipo apresentou aumento líquido de perdas; novas perdas locais podem coexistir com correções.

golden_v3_novo: subtipos que pioraram: (d) Marca marginal em posição errada: +4.

## Painéis das piores páginas

Oito páginas de cada coorte humana, escolhidas pelo número de sucessores de margem perdidos; desempate por quebras de margem e page_id. Esquerda: posto de cada linha humana na sequência da regra; direita: posto na referência humana. Linhas que participam de uma perda de margem ficam vermelhas. O número se refere à linha expandida, não ao bloco de parágrafo. Uma linha intercalada pode ter um único posto inicial: o cache conserva a sequência integral para esse caso. A imagem original é descoberta por page_id nas tarefas, sem supor igualdade de numeração entre lotes.

| Bancada | Página | Perdas de margem | Painel |
|---|---|---:|---|
| golden_v4 | `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 5 | [PNG](margens_e_transversais/golden_v4/8ac3354a856f83e1f3750dfc.png) |
| golden_v4 | `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3` | 5 | [PNG](margens_e_transversais/golden_v4/6c60bb94d1e4b8941818c72f.png) |
| golden_v4 | `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114` | 10 | [PNG](margens_e_transversais/golden_v4/fe2075081668f517c8b9cbb6.png) |
| golden_v4 | `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | 13 | [PNG](margens_e_transversais/golden_v4/b2a5cd50f2cc16be781a7506.png) |
| golden_v4 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 6 | [PNG](margens_e_transversais/golden_v4/f8c4ac1ef2e8bf534782db00.png) |
| golden_v4 | `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13` | 9 | [PNG](margens_e_transversais/golden_v4/873fcf463e5f56d69291c17d.png) |
| golden_v4 | `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | 13 | [PNG](margens_e_transversais/golden_v4/0b5ffb1f57e29ac0e29e5583.png) |
| golden_v4 | `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31` | 6 | [PNG](margens_e_transversais/golden_v4/49b4cc8933803d532df866f8.png) |
| golden_v3_novo | `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | 3 | [PNG](margens_e_transversais/golden_v3_novo/e052f3155014fb29851dda94.png) |
| golden_v3_novo | `official_diary_ac/executive_official_diary_2022-12-02.pdf#p419` | 3 | [PNG](margens_e_transversais/golden_v3_novo/00e1f64ea5cffa09bf663320.png) |
| golden_v3_novo | `official_diary_ma/executive_official_diary_2021-11-12.pdf#p56` | 2 | [PNG](margens_e_transversais/golden_v3_novo/843152277b3f5b24ba7e382c.png) |
| golden_v3_novo | `official_diary_ma/executive_official_diary_2021-11-12.pdf#p60` | 2 | [PNG](margens_e_transversais/golden_v3_novo/2bd8e2f03e0a2a8f37afe58d.png) |
| golden_v3_novo | `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18` | 8 | [PNG](margens_e_transversais/golden_v3_novo/1c4ab1c4718354e7d16492ac.png) |
| golden_v3_novo | `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p39` | 4 | [PNG](margens_e_transversais/golden_v3_novo/b840b287f4c79d968e606647.png) |
| golden_v3_novo | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | 4 | [PNG](margens_e_transversais/golden_v3_novo/d05a585bd095c5670cdedf4b.png) |
| golden_v3_novo | `official_diary_se/DOE-SE_2022-03-18_4475.pdf#p15` | 7 | [PNG](margens_e_transversais/golden_v3_novo/95bb2775e6f43d4c135694cf.png) |

## Protocolo, limitações e retomada

Margens originais: centro < 7% e base < 10% no topo; centro > 95% no rodapé; topo → corpo → marcas → rodapé. Texto em linhas; tabelas/imagens indivisíveis. Entrada `random.Random(f"entrada-{page_id}")`, fornecida por `ordem_entrada`. Expansão canônica de palavras por `bancada_ordenadores.expansoes`; métricas importadas de `erros_ponta_a_ponta`.

golden_v4 participou do desenvolvimento da regra e serve ao ajuste. golden_v3_novo serve apenas à medição final. Silver usa fluxo automático do PDF e split por veículo, com RN para validação e CE/MA/RJ para teste; não é referência humana independente. Nas humanas, 'vistos' significa veículo no split original dos sete veículos de treino; esta variante não recebe treino. Não se usa a anotação como entrada do ordenador.

A referência humana foi expandida geometricamente de regiões: não é anotação independente de todas as palavras/linhas/células. Os subtipos são diagnósticos operacionais e podem se confundir; 'outro' preserva casos sem evidência. Classes congeladas disponíveis só no v4, usadas apenas para diagnóstico. Amostras pequenas e de conveniência; seleção entre várias variantes no v4/RN favorece esses resultados. Nenhum retreino/modelo neural nesta tarefa; não se pode inferir ganho com novas sementes ou veículos independentes.

Menor RAM livre observada: 3785,4 MB. Uma página com palavras em memória por vez; nenhum processo filho, DataLoader ou modelo carregado.

```powershell
venv/Scripts/python.exe -B orquestracao/analises/regra_margens_v2.py --etapa diagnostico
venv/Scripts/python.exe -B orquestracao/analises/regra_margens_v2.py --etapa tudo
```

Cópias intermediárias e assinaturas: `resultados/margens_e_transversais_cache/estado.json`. Nenhum arquivo anterior, dado bruto, anotação, documento ou quadro de comunicação é modificado.
