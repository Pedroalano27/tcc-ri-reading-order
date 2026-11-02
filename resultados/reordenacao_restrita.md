# Reordenação restrita dentro da coluna

Âncora reproduzida: τ 0,985948 e 6,045455 quebras/página em 44 páginas.  
Diagnóstico e alternativas: 160 páginas processadas; três bancadas separadas abaixo.  
Teto na coluna (v4): 54 → 31 quebras; redução 42,59%; passa o critério para investigar o score.  
Quebras/página (regra / score / oráculo): golden_v4: 6,045 / 5,182 / 4,909; golden_v3_novo: 9,222 / 7,778 / 6,963; teste_silver: 27,449 / 26,449 / 24,831.  
Melhorou a média de quebras nas três bancadas, com τ praticamente preservado. IC externo inclui zero em golden_v3_novo. Wilcoxon por veículo não confirma ganho nas bancadas externas; resultado exploratório.

Relatório escrito pelo script a partir das execuções, sem números editados à mão. Score fixo é a alternativa exploratória; oráculo usa a referência apenas para escolher a melhor alternativa do conjunto congelado.

## Controles

| Método | τ palavras | Quebras/página |
|---|---:|---:|
| Regra original, reexecutada e sequência idêntica ao P2 | 0,985948 | 6,045455 |
| Extrator + XY-cut + margens, controle histórico P1m | 0,952424 | 8,931818 |

A âncora obrigatória usa tolerância de arredondamento na sexta casa; P1m é importado do histórico, sem reextração. Detecções congeladas de ls3 são reexecutadas geometricamente, sem carregar pesos ou consultar o projeto parceiro.

## Diagnóstico de candidatos

Nível 3, o nível usado pelo corretor anterior; candidatos importados sem ampliar ou alterar a função. Denominador: sucessores de linhas perdidos classificados como continuação na mesma coluna pelo contexto do corretor. As três classes são exclusivas. Uma fronteira interna à unidade ou inalcançável não se torna corrigível por aparecer nos candidatos.

| Bancada / grupo | Erros de sucessor na coluna | Ausente | Presente, outra coluna | Presente, mesma coluna | Internos à unidade | Fronteira inalcançável |
|---|---:|---:|---:|---:|---:|---:|
| golden_v4 / todos | 48 | 8 | 0 | 40 | 0 | 0 |
| golden_v4 / vistos | 6 | 2 | 0 | 4 | 0 | 0 |
| golden_v4 / nao_vistos | 42 | 6 | 0 | 36 | 0 | 0 |
| golden_v3_novo / todos | 115 | 13 | 0 | 102 | 0 | 0 |
| golden_v3_novo / nao_vistos | 115 | 13 | 0 | 102 | 0 | 0 |
| teste_silver / todos | 185 | 19 | 0 | 166 | 0 | 5 |

Coluna atribuída é a proxy global pelo centro da unidade; a tipologia de sucessor usa também a caixa da linha-ouro. Assim um erro tipado na mesma coluna pode ter unidades atribuídas a colunas diferentes. Não são causas humanas anotadas.

## Três exemplos reais de cada classe

### Sucessor ausente dos candidatos

Exemplos disponíveis nesta execução: 3 (até três exibidos).

- `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41` (golden_v3_novo); `b16` → `b13`, colunas 0 → 0. Interno à unidade: False; fronteira alcançável: True.

Origem: JESUS DE NAZARÉ DE ALMEIDA VIDAL ROSA DE ALMEIDA GUTERRES VERA DE NAZARÉ FERREIRA DINIZ

Sucessor esperado: Secretário de Estado da Fazenda Coordenadora de Contabilidade Analista de Finanças e Controle - CGE/AP

Ordem humana (trecho): `b0:l0` 1 O déficit será apurado pela diferença entre a receita realizada e a despesa liquidada nos cinco primeiros bimestres e a despesa empenhada no último bimestre. → `b7:l0` JESUS DE NAZARÉ DE ALMEIDA VIDAL ROSA DE ALMEIDA GUTERRES VERA DE NAZARÉ FERREIRA DINIZ → `b7:l1` Secretário de Estado da Fazenda Coordenadora de Contabilidade Analista de Finanças e Controle - CGE/AP → `b7:l2` Contadora CRC/AP nº 000183/O-5 Contadora - CRC PA 007142/O-7 T-AP → `b7:l3` CPF nº 094.892.152-87 CPF n° 137.556.842-68

Ordem da regra (trecho): `b6` CPF nº 094.892.152-87 → `b16` VERA DE NAZARÉ FERREIRA DINIZ → `b9` Analista de Finanças e Controle - CGE/AP → `b12` Contadora - CRC PA 007142/O-7 T-AP → `b5` CPF n° 137.556.842-68

Candidatos: `b9`, `b5`, `b12`, fim.

- `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41` (golden_v3_novo); `b9` → `b17`, colunas 0 → 0. Interno à unidade: False; fronteira alcançável: True.

Origem: Secretário de Estado da Fazenda Coordenadora de Contabilidade Analista de Finanças e Controle - CGE/AP

Sucessor esperado: Contadora CRC/AP nº 000183/O-5 Contadora - CRC PA 007142/O-7 T-AP

Ordem humana (trecho): `b7:l0` JESUS DE NAZARÉ DE ALMEIDA VIDAL ROSA DE ALMEIDA GUTERRES VERA DE NAZARÉ FERREIRA DINIZ → `b7:l1` Secretário de Estado da Fazenda Coordenadora de Contabilidade Analista de Finanças e Controle - CGE/AP → `b7:l2` Contadora CRC/AP nº 000183/O-5 Contadora - CRC PA 007142/O-7 T-AP → `b7:l3` CPF nº 094.892.152-87 CPF n° 137.556.842-68 → `b5:l0` 42 de 112

Ordem da regra (trecho): `b16` VERA DE NAZARÉ FERREIRA DINIZ → `b9` Analista de Finanças e Controle - CGE/AP → `b12` Contadora - CRC PA 007142/O-7 T-AP → `b5` CPF n° 137.556.842-68 → `b3` 42 de 112

Candidatos: `b5`, `b16`, `b12`, fim.

- `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41` (golden_v3_novo); `b12` → `b6`, colunas 0 → 0. Interno à unidade: False; fronteira alcançável: True.

Origem: Contadora CRC/AP nº 000183/O-5 Contadora - CRC PA 007142/O-7 T-AP

Sucessor esperado: CPF nº 094.892.152-87 CPF n° 137.556.842-68

Ordem humana (trecho): `b7:l1` Secretário de Estado da Fazenda Coordenadora de Contabilidade Analista de Finanças e Controle - CGE/AP → `b7:l2` Contadora CRC/AP nº 000183/O-5 Contadora - CRC PA 007142/O-7 T-AP → `b7:l3` CPF nº 094.892.152-87 CPF n° 137.556.842-68 → `b5:l0` 42 de 112

Ordem da regra (trecho): `b9` Analista de Finanças e Controle - CGE/AP → `b12` Contadora - CRC PA 007142/O-7 T-AP → `b5` CPF n° 137.556.842-68 → `b3` 42 de 112

Candidatos: `b9`, `b5`, `b16`, fim.

### Presente, em outra coluna atribuída

Exemplos disponíveis nesta execução: 0 (até três exibidos).

Não houve caso observado; não há exemplo real a reproduzir nesta classe. O pedido de três exemplos não pode ser satisfeito aqui sem inventar casos ou mudar a tipologia congelada.

### Presente, na mesma coluna atribuída

Exemplos disponíveis nesta execução: 3 (até três exibidos).

- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` (golden_v3_novo); `b51` → `b43`, colunas 1 → 1. Interno à unidade: False; fronteira alcançável: True.

Origem: para que surtam os devidos e legais efeitos.

Sucessor esperado: Barra do Piraí, 28 de julho de 2022.

Ordem humana (trecho): `b23:l6` junto ao Instituto Estadual Do Ambiente. Para constar lavrei o presente edital, → `b23:l7` para que surtam os devidos e legais efeitos. → `b8:l0` Barra do Piraí, 28 de julho de 2022. → `b24:l0` Luiz Tadeu da Silva Barros → `b24:l1` Chefe da Divisão de Fiscalização

Ordem da regra (trecho): `b49` junto ao Instituto Estadual Do Ambiente. Para constar lavrei o presente edital, → `b51` para que surtam os devidos e legais efeitos. → `b11` EXTRATO CONTRATUAL → `b43` Barra do Piraí, 28 de julho de 2022. → `b59` Luiz Tadeu da Silva Barros

Candidatos: `b43`, `b11`, `b49`, `b60`, `b3`, `b0`, fim.

- `official_diary_ac/executive_official_diary_2022-12-02.pdf#p419` (golden_v3_novo); `b6` → `b8`, colunas 0 → 0. Interno à unidade: False; fronteira alcançável: True.

Origem: Natureza Jurídica não encontrada

Sucessor esperado: PREFEITURA MUNICIPAL DE PLACIDO DE CASTRO

Ordem humana (trecho): `b0:l0` 420 DIÁRIO OFICIAL → `b5:l0` Natureza Jurídica não encontrada → `b5:l1` PREFEITURA MUNICIPAL DE PLACIDO DE CASTRO → `b5:l2` LEI DE DIRETRIZES ORÇAMENTÁRIAS 2023 → `b1:l0` Demonstrativo da Evolução da Despesa (conforme art. 22, III da Lei nº 4.320/64)

Ordem da regra (trecho): `b5` Página: 3/3 → `b6` Natureza Jurídica não encontrada → `b0` Data: 22/11/2022 → `b8` PREFEITURA MUNICIPAL DE PLACIDO DE CASTRO → `b11` LEI DE DIRETRIZES ORÇAMENTÁRIAS 2023

Candidatos: `b11`, `b0`, `b8`, `b10`, fim.

- `official_diary_ac/executive_official_diary_2022-12-02.pdf#p419` (golden_v3_novo); `b5` → `b0`, colunas 0 → 0. Interno à unidade: False; fronteira alcançável: True.

Origem: Página: 3/3

Sucessor esperado: Data: 22/11/2022

Ordem humana (trecho): `b6:l0` Seleção: Alteração em 01/01/2023 (C); Realização da despesa por: Empenho → `b4:l0` Página: 3/3 → `b3:l0` Data: 22/11/2022 → `b7:l0` Realizado Fixado LDO → `b7:l1` Código Especificação

Ordem da regra (trecho): `b9` 420 → `b5` Página: 3/3 → `b6` Natureza Jurídica não encontrada → `b0` Data: 22/11/2022 → `b8` PREFEITURA MUNICIPAL DE PLACIDO DE CASTRO

Candidatos: `b1`, `b4`, `b0`, `b6`, fim.

## Alertas sem consultar a referência

Salto: linha alinhada da coluna de origem até quatro alturas abaixo é ultrapassada; retorno: recuo vertical maior que 0,75 altura, exceto a transição fim→topo da próxima coluna reconhecida pelo corretor; alinhamento: mudança acima de 1,5 altura no melhor dos dois lados ou sobreposição horizontal abaixo de 0,4; objeto: átomo na borda ou obstáculo entre as linhas. Margens são excluídas.

Precisão = alertas cuja palavra final comparável da unidade de origem inicia uma quebra emitida / alertas com essa borda comparável. Cobertura geral = esses eventos cobertos / todas as quebras. Cobertura na coluna usa só eventos tipados na mesma coluna. Alertas sem referência na borda são contados separadamente. Alertas sobrepostos entram uma vez na união; não somar as linhas por tipo.

| Bancada / grupo | Alerta | Quantidade / avaliáveis / sem referência | Precisão | Cobertura quebras | Cobertura na coluna | Cobertura fronteiras de unidade |
|---|---|---:|---:|---:|---:|---:|
| golden_v4 / todos | uniao | 952 / 906 / 46 | 100/906 = 11,04% | 100/266 = 37,59% | 44/54 = 81,48% | 100/242 = 41,32% |
| golden_v4 / todos | salto | 18 / 18 / 0 | 17/18 = 94,44% | 17/266 = 6,39% | 17/54 = 31,48% | 17/242 = 7,02% |
| golden_v4 / todos | retorno | 39 / 34 / 5 | 26/34 = 76,47% | 26/266 = 9,77% | 13/54 = 24,07% | 26/242 = 10,74% |
| golden_v4 / todos | alinhamento | 808 / 799 / 9 | 65/799 = 8,14% | 65/266 = 24,44% | 31/54 = 57,41% | 65/242 = 26,86% |
| golden_v4 / todos | objeto | 127 / 90 / 37 | 19/90 = 21,11% | 19/266 = 7,14% | 1/54 = 1,85% | 19/242 = 7,85% |
| golden_v4 / vistos | uniao | 156 / 146 / 10 | 11/146 = 7,53% | 11/24 = 45,83% | 5/10 = 50,00% | 11/18 = 61,11% |
| golden_v4 / vistos | salto | 0 / 0 / 0 | 0/0 = — | 0/24 = 0,00% | 0/10 = 0,00% | 0/18 = 0,00% |
| golden_v4 / vistos | retorno | 4 / 2 / 2 | 2/2 = 100,00% | 2/24 = 8,33% | 0/10 = 0,00% | 2/18 = 11,11% |
| golden_v4 / vistos | alinhamento | 121 / 121 / 0 | 7/121 = 5,79% | 7/24 = 29,17% | 4/10 = 40,00% | 7/18 = 38,89% |
| golden_v4 / vistos | objeto | 35 / 25 / 10 | 4/25 = 16,00% | 4/24 = 16,67% | 1/10 = 10,00% | 4/18 = 22,22% |
| golden_v4 / nao_vistos | uniao | 796 / 760 / 36 | 89/760 = 11,71% | 89/242 = 36,78% | 39/44 = 88,64% | 89/224 = 39,73% |
| golden_v4 / nao_vistos | salto | 18 / 18 / 0 | 17/18 = 94,44% | 17/242 = 7,02% | 17/44 = 38,64% | 17/224 = 7,59% |
| golden_v4 / nao_vistos | retorno | 35 / 32 / 3 | 24/32 = 75,00% | 24/242 = 9,92% | 13/44 = 29,55% | 24/224 = 10,71% |
| golden_v4 / nao_vistos | alinhamento | 687 / 678 / 9 | 58/678 = 8,55% | 58/242 = 23,97% | 27/44 = 61,36% | 58/224 = 25,89% |
| golden_v4 / nao_vistos | objeto | 92 / 65 / 27 | 15/65 = 23,08% | 15/242 = 6,20% | 0/44 = 0,00% | 15/224 = 6,70% |
| golden_v3_novo / todos | uniao | 587 / 573 / 14 | 167/573 = 29,14% | 167/249 = 67,07% | 95/100 = 95,00% | 167/242 = 69,01% |
| golden_v3_novo / todos | salto | 9 / 9 / 0 | 8/9 = 88,89% | 8/249 = 3,21% | 8/100 = 8,00% | 8/242 = 3,31% |
| golden_v3_novo / todos | retorno | 29 / 28 / 1 | 27/28 = 96,43% | 27/249 = 10,84% | 12/100 = 12,00% | 27/242 = 11,16% |
| golden_v3_novo / todos | alinhamento | 498 / 492 / 6 | 149/492 = 30,28% | 149/249 = 59,84% | 88/100 = 88,00% | 149/242 = 61,57% |
| golden_v3_novo / todos | objeto | 82 / 74 / 8 | 11/74 = 14,86% | 11/249 = 4,42% | 0/100 = 0,00% | 11/242 = 4,55% |
| golden_v3_novo / nao_vistos | uniao | 587 / 573 / 14 | 167/573 = 29,14% | 167/249 = 67,07% | 95/100 = 95,00% | 167/242 = 69,01% |
| golden_v3_novo / nao_vistos | salto | 9 / 9 / 0 | 8/9 = 88,89% | 8/249 = 3,21% | 8/100 = 8,00% | 8/242 = 3,31% |
| golden_v3_novo / nao_vistos | retorno | 29 / 28 / 1 | 27/28 = 96,43% | 27/249 = 10,84% | 12/100 = 12,00% | 27/242 = 11,16% |
| golden_v3_novo / nao_vistos | alinhamento | 498 / 492 / 6 | 149/492 = 30,28% | 149/249 = 59,84% | 88/100 = 88,00% | 149/242 = 61,57% |
| golden_v3_novo / nao_vistos | objeto | 82 / 74 / 8 | 11/74 = 14,86% | 11/249 = 4,42% | 0/100 = 0,00% | 11/242 = 4,55% |
| teste_silver / todos | uniao | 2601 / 2558 / 43 | 603/2558 = 23,57% | 603/2443 = 24,68% | 183/190 = 96,32% | 603/1003 = 60,12% |
| teste_silver / todos | salto | 88 / 88 / 0 | 80/88 = 90,91% | 80/2443 = 3,27% | 70/190 = 36,84% | 80/1003 = 7,98% |
| teste_silver / todos | retorno | 115 / 108 / 7 | 101/108 = 93,52% | 101/2443 = 4,13% | 36/190 = 18,95% | 101/1003 = 10,07% |
| teste_silver / todos | alinhamento | 2305 / 2305 / 0 | 473/2305 = 20,52% | 473/2443 = 19,36% | 117/190 = 61,58% | 473/1003 = 47,16% |
| teste_silver / todos | objeto | 211 / 168 / 43 | 47/168 = 27,98% | 47/2443 = 1,92% | 4/190 = 2,11% | 47/1003 = 4,69% |

## Alternativas e teto

Só alertas propõem janelas: quatro a oito linhas móveis da mesma coluna, em raio local de slots, com amplitude máxima de dezoito unidades. Linhas marginais, transversais, tabelas, imagens e slots de outras colunas ficam fixos. A ordem das propostas é geométrica, sem olhar acerto. Sobreposições são descartadas, mantendo uma unidade fixa com palavras entre janelas. Alternativas: identidade, trocar vizinhos ou mover uma linha para outro slot da mesma coluna. Cada linha aparece exatamente uma vez.

Score = soma ponderada de alinhamento, espaçamento típico da coluna, penalidade de retorno, continuidade de altura/estilo de caixa e caixa alta, objetos atravessados, pontuação/hifenização e deslocamento. São proxies, sem fonte tipográfica/semântica completa. Pesos fixos: `{"alinhamento": 0.6, "espacamento": 1.2, "retorno": 3.0, "estilo": 0.3, "objeto": 4.0, "pontuacao": 0.15, "deslocamento": 0.03}`; vantagem mínima `0.75`. Não houve treino nem busca de pesos em RN, v4 ou bancadas externas.

Oráculo minimiza quebras de palavras nas alternativas de cada janela, incluindo as bordas fixas; desempata pelo menor número de quebras na coluna e depois identidade. A separação por palavra fixa torna os deltas aditivos. O script confere essa igualdade com a régua de página e que o oráculo vence ou empata com regra e score em cada página. É o teto exato de QUEBRAS deste conjunto de janelas; não é teto de τ, de todas as janelas possíveis ou de todas as permutações. Tabela/imagem não é desmembrada.

| Bancada | Janelas | Alternativas (inclui identidade) | Janelas mudadas pelo score | Janelas mudadas pelo oráculo |
|---|---:|---:|---:|---:|
| golden_v4 | 224 | 10973 | 15 | 20 |
| golden_v3_novo | 124 | 6187 | 27 | 27 |
| teste_silver | 548 | 27073 | 81 | 95 |

Gate obrigatório, somente desenvolvimento v4: 54 → 31 quebras na coluna, 42,59% de redução; aprovado.

## golden_v4

Cobertura: 44/44 páginas; completa.

| Grupo | Método | n / veículos | τ palavras [IC] | Quebras/página [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Reparos / regressões / saldo | Quebras na coluna |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Regra original | 44 / 27 | 0,985948 [0,973495; 0,995020] | 6,045 [4,023; 8,887] | 94,81% [91,36; 97,24] | 92,72% [87,81; 96,08] | 0 / 0 / 0 | 54 |
| todos | Regra + reordenação (pesos fixos) | 44 / 27 | 0,985967 [0,973516; 0,995041] | 5,182 [3,375; 7,739] | 95,44% [92,03; 97,85] | 93,63% [89,03; 96,87] | 39 / 1 / 38 | 38 |
| todos | Oráculo restrito | 44 / 27 | 0,985969 [0,973526; 0,995038] | 4,909 [3,119; 7,405] | 95,50% [92,07; 97,92] | 93,75% [89,14; 96,99] | 53 / 3 / 50 | 31 |
| vistos | Regra original | 5 / 5 | 0,997638 [0,994112; 0,999926] | 4,800 [2,600; 7,600] | 98,49% [98,09; 98,89] | 97,70% [96,96; 98,54] | 0 / 0 / 0 | 10 |
| vistos | Regra + reordenação (pesos fixos) | 5 / 5 | 0,997639 [0,994112; 0,999930] | 4,200 [2,400; 7,200] | 98,67% [98,23; 99,05] | 97,86% [96,96; 98,77] | 3 / 0 / 3 | 8 |
| vistos | Oráculo restrito | 5 / 5 | 0,997641 [0,994112; 0,999934] | 3,000 [0,400; 6,600] | 99,06% [98,30; 99,81] | 98,20% [96,96; 99,45] | 9 / 0 / 9 | 6 |
| nao_vistos | Regra original | 39 / 22 | 0,984450 [0,970860; 0,994281] | 6,205 [4,000; 9,395] | 94,34% [90,34; 97,03] | 92,09% [86,60; 95,77] | 0 / 0 / 0 | 44 |
| nao_vistos | Regra + reordenação (pesos fixos) | 39 / 22 | 0,984470 [0,970868; 0,994306] | 5,308 [3,243; 8,135] | 95,03% [91,16; 97,71] | 93,09% [87,95; 96,75] | 36 / 1 / 35 | 30 |
| nao_vistos | Oráculo restrito | 39 / 22 | 0,984473 [0,970876; 0,994307] | 5,154 [3,125; 7,892] | 95,04% [91,16; 97,72] | 93,18% [88,05; 96,82] | 44 / 3 / 41 | 25 |

Δ método−regra; negativo em quebras significa melhoria. Wilcoxon bilateral Pratt sobre médias pareadas por veículo.

| Grupo | Método | Δ quebras [IC 95% veículo] | p veículo | Δ τ [IC 95% veículo] | p veículo | Melhor / igual / pior (páginas, quebras) |
|---|---|---:|---:|---:|---:|---:|
| todos | regra_reordena | -0,864 [-1,610; -0,309] | 0,014913 | 0,000018 [0,000001; 0,000043] | 0,052640 | 8 / 35 / 1 |
| todos | oraculo_reordena | -1,136 [-1,951; -0,521] | 0,001705 | 0,000021 [0,000002; 0,000047] | 0,022023 | 10 / 34 / 0 |
| vistos | regra_reordena | -0,600 [-1,800; 0,000] | 0,317311 | 0,000001 [0,000000; 0,000004] | 0,317311 | 1 / 4 / 0 |
| vistos | oraculo_reordena | -1,800 [-4,200; 0,000] | 0,159854 | 0,000003 [0,000000; 0,000008] | 0,159854 | 2 / 3 / 0 |
| nao_vistos | regra_reordena | -0,897 [-1,700; -0,289] | 0,025169 | 0,000021 [0,000001; 0,000049] | 0,078448 | 7 / 31 / 1 |
| nao_vistos | oraculo_reordena | -1,051 [-1,886; -0,395] | 0,004993 | 0,000024 [0,000002; 0,000053] | 0,060185 | 8 / 31 / 0 |
## golden_v3_novo

Cobertura: 27/27 páginas; completa.

| Grupo | Método | n / veículos | τ palavras [IC] | Quebras/página [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Reparos / regressões / saldo | Quebras na coluna |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Regra original | 27 / 10 | 0,959557 [0,915350; 0,997056] | 9,222 [4,900; 12,867] | 92,84% [89,86; 96,59] | 91,13% [88,06; 93,56] | 0 / 0 / 0 | 100 |
| todos | Regra + reordenação (pesos fixos) | 27 / 10 | 0,959578 [0,915349; 0,997156] | 7,778 [3,708; 10,957] | 93,65% [90,42; 97,75] | 92,58% [88,79; 95,42] | 50 / 11 / 39 | 78 |
| todos | Oráculo restrito | 27 / 10 | 0,959575 [0,915344; 0,997141] | 6,963 [3,045; 10,000] | 94,00% [90,83; 98,09] | 93,37% [90,30; 95,88] | 63 / 2 / 61 | 72 |
| nao_vistos | Regra original | 27 / 10 | 0,959557 [0,915350; 0,997056] | 9,222 [4,900; 12,867] | 92,84% [89,86; 96,59] | 91,13% [88,06; 93,56] | 0 / 0 / 0 | 100 |
| nao_vistos | Regra + reordenação (pesos fixos) | 27 / 10 | 0,959578 [0,915349; 0,997156] | 7,778 [3,708; 10,957] | 93,65% [90,42; 97,75] | 92,58% [88,79; 95,42] | 50 / 11 / 39 | 78 |
| nao_vistos | Oráculo restrito | 27 / 10 | 0,959575 [0,915344; 0,997141] | 6,963 [3,045; 10,000] | 94,00% [90,83; 98,09] | 93,37% [90,30; 95,88] | 63 / 2 / 61 | 72 |

Δ método−regra; negativo em quebras significa melhoria. Wilcoxon bilateral Pratt sobre médias pareadas por veículo.

| Grupo | Método | Δ quebras [IC 95% veículo] | p veículo | Δ τ [IC 95% veículo] | p veículo | Melhor / igual / pior (páginas, quebras) |
|---|---|---:|---:|---:|---:|---:|
| todos | regra_reordena | -1,444 [-2,391; 0,263] | 0,425964 | 0,000020 [-0,000058; 0,000110] | 0,099906 | 7 / 18 / 2 |
| todos | oraculo_reordena | -2,259 [-3,325; -0,917] | 0,010907 | 0,000018 [-0,000157; 0,000124] | 0,132169 | 10 / 17 / 0 |
| nao_vistos | regra_reordena | -1,444 [-2,391; 0,263] | 0,425964 | 0,000020 [-0,000058; 0,000110] | 0,099906 | 7 / 18 / 2 |
| nao_vistos | oraculo_reordena | -2,259 [-3,325; -0,917] | 0,010907 | 0,000018 [-0,000157; 0,000124] | 0,132169 | 10 / 17 / 0 |
## teste_silver

Cobertura: 89/89 páginas; completa.

| Grupo | Método | n / veículos | τ palavras [IC] | Quebras/página [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Reparos / regressões / saldo | Quebras na coluna |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Regra original | 89 / 3 | 0,959565 [0,889505; 0,998435] | 27,449 [22,184; 32,316] | 82,54% [72,93; 89,87] | 84,02% [77,08; 94,09] | 0 / 0 / 0 | 190 |
| todos | Regra + reordenação (pesos fixos) | 89 / 3 | 0,959615 [0,889513; 0,998443] | 26,449 [20,816; 31,921] | 83,20% [73,41; 90,79] | 84,80% [77,58; 94,63] | 132 / 43 / 89 | 160 |
| todos | Oráculo restrito | 89 / 3 | 0,959650 [0,889517; 0,998493] | 24,831 [18,316; 30,763] | 83,95% [73,97; 91,97] | 85,67% [78,47; 94,73] | 233 / 0 / 233 | 115 |

Δ método−regra; negativo em quebras significa melhoria. Wilcoxon bilateral Pratt sobre médias pareadas por veículo.

| Grupo | Método | Δ quebras [IC 95% veículo] | p veículo | Δ τ [IC 95% veículo] | p veículo | Melhor / igual / pior (páginas, quebras) |
|---|---|---:|---:|---:|---:|---:|
| todos | regra_reordena | -1,000 [-1,692; -0,395] | 0,108809 | 0,000049 [0,000008; 0,000105] | 0,108809 | 24 / 61 / 4 |
| todos | oraculo_reordena | -2,618 [-3,868; -1,553] | 0,108809 | 0,000085 [0,000012; 0,000137] | 0,108809 | 33 / 56 / 0 |

Reparos/regressões contam palavras de origem que deixam de iniciar / passam a iniciar uma quebra da régua oficial; saldo = reparos−regressões = quebras da regra−quebras do método. Não confundir com o diagnóstico de sucessores-ouro perdidos. ‘Quebras na coluna’ mantém o mesmo contexto/categoria original em todos os métodos e inclui o piso interno à unidade.

## Conclusão

Melhorou a média de quebras nas três bancadas, com τ praticamente preservado. IC externo inclui zero em golden_v3_novo. Wilcoxon por veículo não confirma ganho nas bancadas externas; resultado exploratório.

As alternativas e os pesos foram fixados antes da leitura das medidas externas. O ganho do oráculo demonstra espaço dentro das janelas, mas não demonstra que a seleção automática acertará sempre. O score também introduz regressões, contadas nas tabelas. Esta execução não demonstra superioridade generalizável nem substitui a avaliação dos outros modelos do TCC; demonstra uma correção geométrica local sobre a representação em linhas, mantendo a régua de palavras e a referência de cada bancada.

## Inferência e limitações

IC percentil de 95% por veículo, 5000 reamostras, semente 20261004, importados da bancada; médias macro por página. Wilcoxon bilateral Pratt sobre médias de diferenças por veículo, sem correção de multiplicidade; evidência exploratória. Os IC são de grupos de veículos; não eliminam viés de desenvolvimento, seleção do conjunto de janelas ou referência automática.

Golden v4 foi usado no desenvolvimento da regra e no gate deste experimento. Golden v3 novo é externo a este ajuste, mas já foi consultado nos experimentos anteriores e pode compartilhar veículos/layouts; não é teste totalmente intocado. Ouro deriva da ordem humana de regiões expandida em palavras, não de anotação independente de todas as linhas. ‘Vistos’ significa os sete veículos do split de treino dos modelos do TCC; este experimento não treina nada. Não informa quais veículos ls3 viu no pré-treino.

Teste silver conserva todas as páginas da bancada original de CE, MA e RJ, inclusive sobreposições humanas, pois nenhuma é usada para treino. O fluxo de conteúdo PDF é a referência automática, selecionada por confiabilidade do veículo; tabelas têm piso alto por discordância da expansão canônica com o fluxo. As bancadas são reportadas separadamente, sem tratá-las como amostras independentes somadas.

Sobreposição silver/humanas: 21 páginas. Bancadas humanas entre si: 0 páginas.

## Artefatos e retomada

Estado/hashes/caches: `resultados/reordenacao_restrita_cache/6d48b2a2ed557dc239ab6c68ff1272f5b45e2c3f73946e1932fdf3e402febf1f`. Uma página por vez, um processo, sem multiprocessing/DataLoader, sem modelos carregados, sem GPU e sem leitura de PDFs ou de dados parceiros. As ordens automáticas recebem a mesma entrada embaralhada determinística pela função do protocolo importada pela bancada.

- `resultados/ordenadores_sem_caixas/pred/regra_reordena__linhas__golden_v4.jsonl`.
- `resultados/ordenadores_sem_caixas/pred/oraculo_reordena__linhas__golden_v4.jsonl`.
- `resultados/ordenadores_sem_caixas/pred/regra_reordena__linhas__golden_v3_novo.jsonl`.
- `resultados/ordenadores_sem_caixas/pred/oraculo_reordena__linhas__golden_v3_novo.jsonl`.
- `resultados/ordenadores_sem_caixas/pred/regra_reordena__linhas__teste_silver.jsonl`.
- `resultados/ordenadores_sem_caixas/pred/oraculo_reordena__linhas__teste_silver.jsonl`.

A avaliação do contrato é executada com `indice_pred`, `ler_offset`, `auditar_unidades`, `referencia`, `expansoes` e a função `medir` do corretor (que importa integralmente `erros_ponta_a_ponta.medir`); não se chama `bancada.main/avaliar/metricas`, que alterariam relatórios/caches existentes. Estatísticas vêm de `bancada.resumo`.

```powershell
venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py
venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py --max-minutos 30
venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py --conferir
```

