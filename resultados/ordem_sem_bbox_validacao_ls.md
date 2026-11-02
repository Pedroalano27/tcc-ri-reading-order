# Validação independente da ordem sem bounding box fina

## Resumo em cinco linhas

1. **Veredito: O ganho geral não se confirma em dado novo contra a XY-cut com as mesmas margens.**
2. 126 páginas com cadeia válida (123 com métrica de palavras), de 29 veículos: τ real 0,966 (átomos-ouro), 0,905 (XY-cut pura) e 0,976 (XY-cut com margens).
3. Contra a XY-cut justa: Δτ -0,010 [-0,050; 0,018]; Wilcoxon Pratt por página p=0,148510 e por veículo p=0,352720.
4. Multicoluna: 52 páginas; correções comprovadas da sugestão: 0; diferentes da XY-cut recalculada (sensibilidade): 72.
5. Detector: 89 páginas no treino, 13 na validação, 24 no teste; melhoria por voto interno é exploratória e não muda o veredito do método congelado.

## Configuração congelada e independência

`projecao_local_margens_s0.45_g1.2_v0.08`: abordagem=projecao_local_margens, score=0,45, gap=1,2, vale=0,08. É a configuração modal do LOPO anterior; escolhas registradas: `{'projecao_local_margens_s0.45_g1.2_v0.08': 42, 'projecao_local_s0.45_g1.2_v0.20': 2}`. Não houve reajuste nem seleção com a ordem LS. O score filtra átomos; todos os outros limiares são os do código importado, em pontos PDF. Hashes de fontes/dados constam em `manifesto.json`.
Páginas novas pertencem ao projeto parceiro Data Policy: uso exclusivamente interno. Independência aqui significa páginas não usadas no desenvolvimento original; não garante veículos inéditos. A melhoria foi executada no Golden antes das métricas LS. Caixas humanas de texto só entram nas baselines e na avaliação; o método usa palavras e átomos table/figure/chart/heading. A classe heading é rubrica manuscrita, não título. unknown fica fora dos átomos, mas continua na régua humana quando tem palavras.
Checagem de sobreposição com o Golden por nome de PDF e página: `{'pdfs_com_nome_em_comum': 0, 'paginas_com_identidade_em_comum': 0}`. É conferência de identidade nominal, não prova de conteúdos distintos por hash de raster.

## Réguas, margens e inferência

**Principal = sequência real de palavras.** Cada palavra recebe um ID próprio. Referência = regiões na ordem das relações humanas; dentro da região, `linhas()` emite topo→base/esquerda→direita. A predição é a expansão real dos itens, sem mediana. Portanto a ordenação interna não foi anotada independentemente: trata-se de uma referência geométrica derivada, não transcrição humana de leitura palavra a palavra. Tabelas também são lidas por linhas nesta régua. Sucessor de palavras é favorecido por pares internos longos; lê-se junto com fragmentação.
Fragmentação estrita = fração das regiões com palavras cuja saída tem mais de um trecho; palavras sem dono interrompem trechos. Regiões vazias ficam fora desse denominador, são contadas e só na régua secundária recebem o posto da palavra geometricamente mais próxima (ou geometria numa página vazia). Páginas/réguas com menos de dois itens têm métrica ausente, não acerto perfeito. Regiões por mediana são secundárias e podem esconder intercalação.
A baseline justa aplica às caixas-ouro a precedência literal: marcas quando todas as palavras casam com RE_MARCACAO; topo se centro < 7% da altura e base < 10%; rodapé se centro > 95%; saída = topo, corpo XY-cut, marcas, rodapé. Limiar, regex e desempate são idênticos ao método, preservando caixas inteiras.
Médias macro por página. IC percentil de 95%, 2000 reamostras de veículos inteiros, semente 20261003; grupos vêm de `ls_split.json`/`fonte_de()`, nunca do nome da edição. Com configuração fixa, não há seleção a refazer no bootstrap. Wilcoxon pareado `zero_method='pratt'`; diferenças arredondadas a doze casas só para distinguir empates numéricos. Reportamos também Pratt nas médias de diferenças por veículo. P por página pode ser otimista por dependência; Holm abrange a família de comparações de cada subconjunto, e análises por estrato continuam exploratórias.
Agrupamento corrige dois aliases do split, confirmados pelos cabeçalhos: `rio janeiro` e `rj` = D.O. do Município do Rio de Janeiro (tarefas 7200/7208); `doe pa` e `pa` = Diário Oficial do Estado do Pará (tarefas 7271/7191). As grafias originais e o split original do detector são preservados em cada resultado. Essa correção só define a unidade de reamostragem, sem alterar predições, limiares ou seleção de páginas.
Colunas: palavras do corpo (centro entre 10% e 95% da altura, sem marcas), linhas partidas com gap=1,2; `vales_locais(..., 0,08)` e fallback `vales`. Uma coluna = nenhum corte; multicoluna = ao menos um corte. É o detector do próprio método, não rótulo humano: pode errar e não resolve layouts que mudam por faixa.

## Tabela principal — saída real, palavras

† Usa caixas humanas; diagnóstico, indisponível em produção. A linha ls3 agregada inclui treino e é descritiva; a separação seguinte é obrigatória.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 123 | 0,893 [0,808; 0,956] | 99,2% [98,8; 99,5] | 0,054 [0,022; 0,096] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 123 | 0,905 [0,822; 0,967] | 99,3% [98,9; 99,5] | 0,047 [0,016; 0,089] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 123 | 0,976 [0,954; 0,993] | 99,3% [98,9; 99,6] | 0,012 [0,003; 0,023] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 123 | 0,966 [0,928; 0,991] | 98,8% [98,3; 99,2] | 0,017 [0,004; 0,036] | 4,1% [1,5; 6,7] |
| Sem bbox fina, detector ls3 CPU | 123 | 0,954 [0,915; 0,982] | 98,1% [97,2; 98,9] | 0,022 [0,008; 0,042] | 5,1% [2,5; 7,7] |

### Uma coluna

74 páginas, 26 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 71 | 0,963 [0,920; 0,991] | 99,3% [98,8; 99,6] | 0,018 [0,004; 0,040] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 71 | 0,964 [0,922; 0,990] | 99,4% [98,9; 99,7] | 0,018 [0,005; 0,039] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 71 | 0,983 [0,962; 0,997] | 99,3% [98,8; 99,6] | 0,008 [0,001; 0,019] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 71 | 0,975 [0,952; 0,994] | 98,9% [98,2; 99,4] | 0,012 [0,003; 0,024] | 2,8% [0,5; 5,2] |
| Sem bbox fina, detector ls3 CPU | 71 | 0,959 [0,927; 0,986] | 98,0% [96,5; 99,1] | 0,019 [0,006; 0,035] | 3,7% [1,3; 6,1] |

### Multicoluna

52 páginas, 14 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 52 | 0,797 [0,648; 0,918] | 99,0% [98,6; 99,4] | 0,101 [0,041; 0,176] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 52 | 0,824 [0,682; 0,943] | 99,1% [98,7; 99,6] | 0,088 [0,029; 0,159] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 52 | 0,966 [0,918; 0,992] | 99,3% [98,9; 99,7] | 0,017 [0,004; 0,041] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 52 | 0,953 [0,889; 0,991] | 98,6% [97,8; 99,2] | 0,024 [0,005; 0,056] | 5,7% [2,3; 9,9] |
| Sem bbox fina, detector ls3 CPU | 52 | 0,946 [0,880; 0,985] | 98,2% [97,2; 98,9] | 0,027 [0,007; 0,059] | 7,0% [3,3; 11,4] |

### Detector — páginas do treino (contaminadas)

89 páginas, 21 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 89 | 0,884 [0,791; 0,960] | 99,2% [98,8; 99,4] | 0,058 [0,020; 0,104] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 89 | 0,899 [0,808; 0,973] | 99,2% [98,8; 99,5] | 0,051 [0,013; 0,096] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 89 | 0,971 [0,943; 0,994] | 99,2% [98,7; 99,5] | 0,014 [0,003; 0,029] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 89 | 0,954 [0,906; 0,989] | 98,5% [98,0; 99,1] | 0,023 [0,006; 0,047] | 4,2% [1,1; 7,4] |
| Sem bbox fina, detector ls3 CPU | 89 | 0,952 [0,904; 0,988] | 98,4% [97,7; 99,0] | 0,024 [0,006; 0,048] | 4,8% [1,8; 7,9] |

### Detector — validação (usada na escolha do checkpoint)

13 páginas, 3 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 13 | 0,816 [0,608; 1,000] | 99,0% [98,0; 100,0] | 0,092 [0,000; 0,196] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 13 | 0,816 [0,608; 1,000] | 99,0% [98,1; 100,0] | 0,092 [0,000; 0,196] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 13 | 0,992 [0,989; 1,000] | 99,7% [99,5; 100,0] | 0,004 [0,000; 0,005] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 13 | 0,994 [0,989; 1,000] | 99,0% [98,1; 100,0] | 0,003 [0,000; 0,005] | 7,7% [0,0; 15,7] |
| Sem bbox fina, detector ls3 CPU | 13 | 0,930 [0,797; 1,000] | 97,4% [95,9; 100,0] | 0,033 [0,000; 0,095] | 10,0% [0,0; 15,1] |

### Detector — teste (fora de treino e validação)

24 páginas, 5 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 21 | 0,977 [0,865; 1,000] | 99,4% [96,9; 99,9] | 0,011 [0,000; 0,064] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 21 | 0,986 [0,914; 1,000] | 99,6% [97,7; 100,0] | 0,006 [0,000; 0,040] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 21 | 0,986 [0,914; 1,000] | 99,5% [97,7; 99,9] | 0,006 [0,000; 0,040] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 21 | 0,999 [0,999; 1,000] | 99,7% [99,6; 100,0] | 0,000 [0,000; 0,001] | 1,3% [0,0; 1,7] |
| Sem bbox fina, detector ls3 CPU | 21 | 0,975 [0,882; 0,999] | 97,2% [88,1; 99,7] | 0,011 [0,000; 0,051] | 3,1% [0,0; 15,4] |

### Detector — fora do treino, incluindo validação

37 páginas, 8 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 34 | 0,916 [0,756; 0,995] | 99,3% [98,1; 99,8] | 0,042 [0,003; 0,122] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 34 | 0,921 [0,762; 0,999] | 99,4% [98,4; 100,0] | 0,039 [0,000; 0,118] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 34 | 0,988 [0,955; 0,999] | 99,6% [98,8; 99,9] | 0,005 [0,000; 0,021] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 34 | 0,997 [0,994; 1,000] | 99,4% [98,8; 99,9] | 0,001 [0,000; 0,003] | 3,7% [0,4; 9,3] |
| Sem bbox fina, detector ls3 CPU | 34 | 0,957 [0,876; 0,993] | 97,3% [93,0; 99,2] | 0,019 [0,003; 0,057] | 5,7% [1,8; 13,1] |

### Humano mudou a sugestão — comprovado

0 páginas, 0 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|

### Sensibilidade — humano difere da XY-cut recalculada

72 páginas, 24 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 70 | 0,821 [0,704; 0,928] | 98,8% [98,3; 99,2] | 0,089 [0,036; 0,148] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 70 | 0,833 [0,718; 0,943] | 98,7% [98,3; 99,1] | 0,083 [0,028; 0,141] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 70 | 0,959 [0,926; 0,987] | 99,0% [98,5; 99,4] | 0,020 [0,006; 0,036] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 70 | 0,943 [0,885; 0,986] | 98,6% [98,1; 99,1] | 0,028 [0,007; 0,057] | 4,7% [1,5; 8,2] |
| Sem bbox fina, detector ls3 CPU | 70 | 0,927 [0,868; 0,974] | 98,1% [97,4; 98,7] | 0,036 [0,012; 0,065] | 6,5% [3,1; 9,8] |

### Sensibilidade — alinhamento textual confirmado

114 páginas, 27 veículos.

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 114 | 0,885 [0,796; 0,956] | 99,1% [98,7; 99,4] | 0,057 [0,022; 0,102] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 114 | 0,898 [0,810; 0,969] | 99,2% [98,8; 99,5] | 0,051 [0,015; 0,094] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 114 | 0,975 [0,948; 0,992] | 99,2% [98,8; 99,6] | 0,013 [0,004; 0,026] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 114 | 0,964 [0,926; 0,991] | 98,7% [98,2; 99,2] | 0,018 [0,004; 0,037] | 4,0% [1,5; 6,7] |
| Sem bbox fina, detector ls3 CPU | 114 | 0,958 [0,918; 0,986] | 98,2% [97,0; 98,9] | 0,021 [0,007; 0,040] | 4,8% [2,2; 7,6] |

## Ancoragem e sugestão ausente

Campo `iguais_a_origem` do conversor: {'igual_comprovada': 15, 'origem_ausente': 111}. O export contém referências a parent_prediction cujas predições não vieram no arquivo. Não inventamos a origem ausente. Subconjunto comprovado exige campo presente e iguais < total. Origem ausente é desconhecida, mesmo se a ordem coincide com a XY-cut atual.
A sensibilidade compara o humano à XY-cut recalculada nas caixas da revisão humana. Ela não comprova correção da proposta original: caixas podem ter sido editadas, IDs trocados e o código XY-cut pode diferir. O viés de ancoragem permanece em todos os subconjuntos; corrigir uma sugestão não equivale a anotação do zero.

## Régua secundária — regiões por mediana

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Ingênua nas caixas-ouro† | 125 | 0,823 [0,760; 0,877] | 66,5% [57,6; 73,6] | 0,076 [0,052; 0,105] | 0,0% [0,0; 0,0] |
| XY-cut nas caixas-ouro† | 125 | 0,881 [0,825; 0,926] | 74,8% [66,1; 82,4] | 0,052 [0,032; 0,079] | 0,0% [0,0; 0,0] |
| XY-cut ouro + mesmas margens† | 125 | 0,874 [0,826; 0,910] | 71,9% [62,9; 79,1] | 0,052 [0,036; 0,072] | 0,0% [0,0; 0,0] |
| Sem bbox fina, átomos-ouro† (diagnóstico) | 125 | 0,818 [0,743; 0,872] | 64,7% [58,2; 69,6] | 0,073 [0,051; 0,103] | 4,1% [1,5; 6,7] |
| Sem bbox fina, detector ls3 CPU | 125 | 0,813 [0,738; 0,870] | 64,4% [57,9; 69,4] | 0,074 [0,052; 0,104] | 5,1% [2,5; 7,7] |

## Testes pareados — todas as páginas

| Método − base | Régua | Métrica | n/grupos | Δ (IC por veículo) | ganha/empata/perde | p Pratt | p Holm | p Pratt veículo |
|---|---|---|---:|---:|---:|---:|---:|---:|
| ouro − xy | palavras | tau | 123/29 | 0,061 [0,010; 0,128] | 30/45/48 | 0,321919 | 1,000000 | 0,628501 |
| ouro − xy | palavras | sucessor | 123/29 | -0,005 [-0,009; -0,000] | 24/46/53 | 0,001666 | 0,038308 | 0,262022 |
| ouro − xy | palavras | ard | 123/29 | -0,030 [-0,064; -0,005] | 30/47/46 | 0,396835 | 1,000000 | 0,628501 |
| ouro − xy | regioes | tau | 125/29 | -0,063 [-0,134; 0,003] | 20/46/59 | 0,000096 | 0,002983 | 0,010922 |
| ouro − xy | regioes | sucessor | 125/29 | -0,102 [-0,189; -0,007] | 22/50/53 | 0,000589 | 0,014726 | 0,014029 |
| ouro − xy | regioes | ard | 125/29 | 0,020 [-0,008; 0,050] | 19/48/58 | 0,000113 | 0,003277 | 0,013950 |
| ouro − xy_margens | palavras | tau | 123/29 | -0,010 [-0,050; 0,018] | 28/52/43 | 0,148510 | 1,000000 | 0,352720 |
| ouro − xy_margens | palavras | sucessor | 123/29 | -0,005 [-0,010; -0,000] | 17/64/42 | 0,000793 | 0,019032 | 0,076352 |
| ouro − xy_margens | palavras | ard | 123/29 | 0,005 [-0,009; 0,025] | 27/54/42 | 0,149087 | 1,000000 | 0,289648 |
| ouro − xy_margens | regioes | tau | 125/29 | -0,055 [-0,104; -0,020] | 22/50/53 | 0,000106 | 0,003184 | 0,008526 |
| ouro − xy_margens | regioes | sucessor | 125/29 | -0,072 [-0,150; 0,008] | 32/48/45 | 0,033094 | 0,661871 | 0,104317 |
| ouro − xy_margens | regioes | ard | 125/29 | 0,021 [0,008; 0,038] | 22/52/51 | 0,000193 | 0,005214 | 0,004752 |
| ls3 − xy | palavras | tau | 123/29 | 0,049 [-0,003; 0,118] | 31/38/54 | 0,184698 | 1,000000 | 0,654913 |
| ls3 − xy | palavras | sucessor | 123/29 | -0,011 [-0,022; -0,004] | 22/42/59 | 0,000071 | 0,002334 | 0,019091 |
| ls3 − xy | palavras | ard | 123/29 | -0,025 [-0,059; 0,001] | 31/40/52 | 0,230113 | 1,000000 | 0,686696 |
| ls3 − xy | regioes | tau | 125/29 | -0,068 [-0,140; -0,001] | 20/45/60 | 0,000063 | 0,002136 | 0,009050 |
| ls3 − xy | regioes | sucessor | 125/29 | -0,105 [-0,195; -0,008] | 23/48/54 | 0,000566 | 0,014726 | 0,020014 |
| ls3 − xy | regioes | ard | 125/29 | 0,022 [-0,006; 0,052] | 19/47/59 | 0,000080 | 0,002568 | 0,011618 |
| ls3 − xy_margens | palavras | tau | 123/29 | -0,022 [-0,064; 0,009] | 26/47/50 | 0,007721 | 0,167801 | 0,012214 |
| ls3 − xy_margens | palavras | sucessor | 123/29 | -0,012 [-0,022; -0,004] | 16/58/49 | 0,000022 | 0,000782 | 0,016521 |
| ls3 − xy_margens | palavras | ard | 123/29 | 0,011 [-0,004; 0,031] | 25/49/49 | 0,007627 | 0,167801 | 0,010078 |
| ls3 − xy_margens | regioes | tau | 125/29 | -0,060 [-0,110; -0,024] | 21/50/54 | 0,000034 | 0,001203 | 0,003578 |
| ls3 − xy_margens | regioes | sucessor | 125/29 | -0,075 [-0,157; 0,007] | 33/48/44 | 0,045066 | 0,856261 | 0,159650 |
| ls3 − xy_margens | regioes | ard | 125/29 | 0,023 [0,009; 0,041] | 22/52/51 | 0,000185 | 0,005192 | 0,002920 |

## Exploratório — uma melhoria para átomos em colunas

Hipótese desenvolvida no Golden: caixas altas de tabelas lado a lado deixam poucos itens no perfil e impedem a detecção de uma calha. **Única mudança:** quando o perfil original não encontra cortes e há átomos, linhas internas desses átomos votam no mesmo detector de vales; as caixas continuam indivisíveis na saída. Sem novo limiar, nova grade ou ajuste LS. O restante (margens, score, ponte de 10%, recursão/fallback) permanece igual. O resultado é reportado mesmo se não melhorar; não selecionamos a versão vencedora após o LS.
No desenvolvimento Golden, os votos adicionais não melhoraram a ordem real. Portanto a hipótese não teve suporte nessa bancada; mantemos o teste LS explicitamente exploratório, sem promovê-lo ao método congelado.

| Desenvolvimento Golden | n | Docling congelado | Docling + voto | Ouro congelado | Ouro + voto |
|---|---:|---:|---:|---:|---:|
| todas | 44 | 0,980 [0,960; 0,993] | 0,980 [0,960; 0,993] | 0,986 [0,972; 0,995] | 0,986 [0,972; 0,995] |
| multicoluna | 24 | 0,968 [0,931; 0,992] | 0,968 [0,931; 0,992] | 0,979 [0,959; 0,994] | 0,979 [0,959; 0,994] |

### Validação exploratória LS: todas

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Sem bbox fina, átomos-ouro† (diagnóstico) | 123 | 0,966 [0,928; 0,991] | 98,8% [98,3; 99,2] | 0,017 [0,004; 0,036] | 4,1% [1,5; 6,7] |
| Exploratório: átomos-ouro + voto interno† | 123 | 0,982 [0,962; 0,994] | 98,8% [98,3; 99,2] | 0,009 [0,003; 0,019] | 4,1% [1,6; 6,7] |
| Sem bbox fina, detector ls3 CPU | 123 | 0,954 [0,915; 0,982] | 98,1% [97,2; 98,9] | 0,022 [0,008; 0,042] | 5,1% [2,5; 7,7] |
| Exploratório: ls3 + voto interno | 123 | 0,970 [0,945; 0,988] | 98,1% [97,2; 98,9] | 0,014 [0,006; 0,026] | 5,1% [2,6; 7,8] |
ouro_exp − ouro: Δτ 0,016 [0,000; 0,051]; p Pratt=0,083271, p por veículo=0,317311.
ls3_exp − ls3: Δτ 0,017 [0,000; 0,053]; p Pratt=0,083271, p por veículo=0,317311.

### Validação exploratória LS: multicoluna

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Sem bbox fina, átomos-ouro† (diagnóstico) | 52 | 0,953 [0,889; 0,991] | 98,6% [97,8; 99,2] | 0,024 [0,005; 0,056] | 5,7% [2,3; 9,9] |
| Exploratório: átomos-ouro + voto interno† | 52 | 0,982 [0,958; 0,994] | 98,7% [97,8; 99,2] | 0,009 [0,003; 0,021] | 5,7% [2,3; 9,9] |
| Sem bbox fina, detector ls3 CPU | 52 | 0,946 [0,880; 0,985] | 98,2% [97,2; 98,9] | 0,027 [0,007; 0,059] | 7,0% [3,3; 11,4] |
| Exploratório: ls3 + voto interno | 52 | 0,975 [0,947; 0,990] | 98,2% [97,2; 98,9] | 0,012 [0,005; 0,026] | 7,2% [3,4; 11,7] |
ouro_exp − ouro: Δτ 0,029 [0,000; 0,094]; p Pratt=0,157319, p por veículo=0,317311.
ls3_exp − ls3: Δτ 0,029 [0,000; 0,093]; p Pratt=0,157319, p por veículo=0,317311.

### Validação exploratória LS: ls3_teste

| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |
|---|---:|---:|---:|---:|---:|
| Sem bbox fina, átomos-ouro† (diagnóstico) | 21 | 0,999 [0,999; 1,000] | 99,7% [99,6; 100,0] | 0,000 [0,000; 0,001] | 1,3% [0,0; 1,7] |
| Exploratório: átomos-ouro + voto interno† | 21 | 0,999 [0,999; 1,000] | 99,7% [99,6; 100,0] | 0,000 [0,000; 0,001] | 1,3% [0,0; 1,7] |
| Sem bbox fina, detector ls3 CPU | 21 | 0,975 [0,882; 0,999] | 97,2% [88,1; 99,7] | 0,011 [0,000; 0,051] | 3,1% [0,0; 15,4] |
| Exploratório: ls3 + voto interno | 21 | 0,975 [0,882; 0,999] | 97,2% [88,1; 99,7] | 0,011 [0,000; 0,051] | 3,1% [0,0; 15,4] |
ouro_exp − ouro: Δτ 0,000 [0,000; 0,000]; p Pratt=1,000000, p por veículo=1,000000.
ls3_exp − ls3: Δτ 0,000 [0,000; 0,000]; p Pratt=1,000000, p por veículo=1,000000.

## Auditoria de PDF, índice e escala

Conversão: `{'tarefas_export': 750, 'automaticas_ignoradas': 750, 'humanas': 189, 'humanas_invalidas': 63, 'humanas_validas': 126}`. Extração: 126 páginas, 0 falhas. Totais calculados: `{'palavras': 64525, 'fora_ouro': 646, 'ambiguas': 53, 'regioes_vazias': 228, 'pagina_vazia': 3, 'regioes': 1852, 'paginas_pkcs7': 1, 'paginas_transcritas': 122, 'vizinha_melhor': 0, 'tokens_transcricao': 85120, 'tokens_comuns': 82287}`.
Índice usado = pagina do mapa/export − 1 (mapa e export precisam coincidir). Caixas do conversor estão em pixels; x e y são convertidos separadamente para pontos usando largura/altura real do PDF. Isso preserva constantes como janelas de cem pontos do método anterior. PDF encapsulado é o trecho do primeiro %PDF ao último %%EOF sob pdf_temporarios; originais nunca são alterados.
Verificação: tokens normalizados das palavras dentro das caixas vs transcrições, sem usar a ordem humana; páginas vizinhas (−1/+1) auditadas quando há texto transcrito. Alinhamento confirmado exige F1 de tokens ≥ 0,80 e nenhuma vizinha mais de 0,05 melhor. Esses limites são diagnóstico de qualidade da referência, não parâmetros de ordenação. Não trocamos índice nem ajustamos caixas para melhorar resultados. Transcrição vazia é ausência de prova, não prova de erro. A tabela de sensibilidade mostra só alinhamento confirmado.

| tarefa | página/índice | PDF px→pt x/y | F1 tokens | vizinha melhor | regiões sem palavras |
|---|---:|---:|---:|---|---:|
| 7177 | 17/16 | 0,35990/0,36000 | 1,000 | não | 2 |
| 7178 | 113/112 | 0,35990/0,35996 | 0,959 | não | 0 |
| 7179 | 66/65 | 0,35990/0,35996 | 0,950 | não | 0 |
| 7180 | 203/202 | 0,35994/0,40856 | 0,975 | não | 2 |
| 7181 | 8/7 | 0,35990/0,36000 | 1,000 | não | 5 |
| 7182 | 12/11 | 0,35990/0,36000 | 0,999 | não | 0 |
| 7183 | 91/90 | 0,35990/0,36000 | 1,000 | não | 0 |
| 7184 | 122/121 | 0,35990/0,35994 | 1,000 | não | 1 |
| 7185 | 141/140 | 0,35990/0,35994 | 1,000 | não | 1 |
| 7186 | 163/162 | 0,35990/0,35994 | 0,997 | não | 1 |
| 7187 | 4/3 | 0,35990/0,35994 | 0,367 | não | 0 |
| 7188 | 5/4 | 0,35990/0,35994 | 0,995 | não | 1 |
| 7189 | 1075/1074 | 0,35989/0,35987 | 0,989 | não | 2 |
| 7190 | 917/916 | 0,35989/0,35987 | 0,989 | não | 0 |
| 7191 | 120/119 | 0,35990/0,35994 | 1,000 | não | 0 |
| 7192 | 129/128 | 0,35990/0,35994 | 0,675 | não | 0 |
| 7193 | 132/131 | 0,35990/0,35994 | 0,994 | não | 0 |
| 7194 | 140/139 | 0,35990/0,35994 | 0,982 | não | 0 |
| 7195 | 29/28 | 0,35990/0,35994 | 0,968 | não | 0 |
| 7196 | 48/47 | 0,35990/0,35994 | 0,982 | não | 0 |
| 7197 | 52/51 | 0,35990/0,35994 | 0,995 | não | 0 |
| 7198 | 92/91 | 0,35990/0,35994 | 0,996 | não | 0 |
| 7199 | 98/97 | 0,35990/0,35994 | 0,998 | não | 0 |
| 7200 | 108/107 | 0,35989/0,35987 | 0,992 | não | 0 |
| 7201 | 11/10 | 0,35989/0,35987 | 0,995 | não | 0 |
| 7203 | 199/198 | 0,35989/0,35987 | 0,972 | não | 2 |
| 7204 | 28/27 | 0,35989/0,35987 | 0,934 | não | 2 |
| 7208 | 147/146 | 0,35989/0,35987 | 0,997 | não | 0 |
| 7209 | 198/197 | 0,35989/0,35987 | 0,934 | não | 0 |
| 7210 | 93/92 | 0,35989/0,35987 | 0,994 | não | 0 |
| 7211 | 124/123 | 0,35995/0,35998 | 1,000 | não | 0 |
| 7212 | 160/159 | 0,35995/0,35998 | 1,000 | não | 0 |
| 7213 | 190/189 | 0,35995/0,35998 | 0,990 | não | 0 |
| 7214 | 203/202 | 0,35995/0,35998 | 0,979 | não | 0 |
| 7215 | 204/203 | 0,35995/0,35998 | 0,946 | não | 1 |
| 7216 | 268/267 | 0,35995/0,35998 | 1,000 | não | 0 |
| 7217 | 30/29 | 0,35995/0,35998 | 0,954 | não | 1 |
| 7218 | 33/32 | 0,35995/0,35998 | 1,000 | não | 0 |
| 7219 | 494/493 | 0,35995/0,35998 | 0,999 | não | 0 |
| 7220 | 505/504 | 0,35995/0,35998 | 0,999 | não | 0 |
| 7221 | 510/509 | 0,35995/0,35998 | 0,999 | não | 0 |
| 7222 | 68/67 | 0,35995/0,35998 | 1,000 | não | 0 |
| 7223 | 10/9 | 0,35990/0,35994 | 0,978 | não | 9 |
| 7224 | 111/110 | 0,35990/0,35994 | 0,794 | não | 1 |
| 7226 | 13/12 | 0,35990/0,35994 | 0,924 | não | 2 |
| 7227 | 139/138 | 0,35990/0,35994 | 0,995 | não | 2 |
| 7229 | 152/151 | 0,35990/0,35994 | 0,991 | não | 2 |
| 7230 | 153/152 | 0,35990/0,35994 | 0,984 | não | 1 |
| 7238 | 27/26 | 0,35991/0,35997 | 0,907 | não | 1 |
| 7239 | 40/39 | 0,35991/0,35997 | 0,976 | não | 1 |
| 7240 | 63/62 | 0,35991/0,35997 | 0,975 | não | 1 |
| 7241 | 9/8 | 0,35991/0,35997 | 0,970 | não | 1 |
| 7242 | 27/26 | 0,35990/0,35994 | 0,948 | não | 3 |
| 7243 | 41/40 | 0,35990/0,35994 | 0,990 | não | 3 |
| 7244 | 56/55 | 0,35990/0,35994 | 1,000 | não | 3 |
| 7246 | 5/4 | 0,35990/0,35993 | 1,000 | não | 0 |
| 7247 | 145/144 | 0,36000/0,36000 | 0,994 | não | 0 |
| 7248 | 20/19 | 0,36000/0,36000 | 1,000 | não | 2 |
| 7250 | 26/25 | 0,36000/0,36000 | 1,000 | não | 0 |
| 7251 | 62/61 | 0,36000/0,36000 | 0,974 | não | 0 |
| 7252 | 83/82 | 0,36000/0,36000 | 1,000 | não | 0 |
| 7253 | 84/83 | 0,36000/0,36000 | 1,000 | não | 0 |
| 7254 | 89/88 | 0,36000/0,36000 | 0,994 | não | 0 |
| 7255 | 96/95 | 0,36000/0,36000 | 1,000 | não | 0 |
| 7256 | 110/109 | 0,35990/0,35994 | 0,992 | não | 1 |
| 7257 | 131/130 | 0,35990/0,35994 | 0,952 | não | 0 |
| 7259 | 46/45 | 0,35990/0,35994 | 0,991 | não | 0 |
| 7261 | 9/8 | 0,35990/0,35994 | 0,980 | não | 0 |
| 7262 | 176/175 | 0,35990/0,35994 | 0,999 | não | 3 |
| 7263 | 18/17 | 0,35990/0,35994 | 1,000 | não | 3 |
| 7264 | 19/18 | 0,35990/0,35994 | 1,000 | não | 3 |
| 7265 | 238/237 | 0,35990/0,35994 | 0,981 | não | 3 |
| 7266 | 329/328 | 0,35990/0,35994 | 1,000 | não | 3 |
| 7267 | 46/45 | 0,35990/0,35994 | 0,984 | não | 3 |
| 7268 | 49/48 | 0,35990/0,35994 | 0,981 | não | 3 |
| 7269 | 81/80 | 0,35990/0,35994 | 0,992 | não | 3 |
| 7270 | 99/98 | 0,35990/0,35994 | 0,903 | não | 3 |
| 7271 | 2/1 | 0,35998/0,35995 | 0,954 | não | 4 |
| 7274 | 102/101 | 0,35990/0,35994 | 0,923 | não | 0 |
| 7275 | 115/114 | 0,35990/0,35994 | 0,917 | não | 0 |
| 7276 | 289/288 | 0,35990/0,35994 | 0,899 | não | 0 |
| 7277 | 293/292 | 0,35990/0,35994 | 0,978 | não | 0 |
| 7278 | 65/64 | 0,35990/0,35994 | 0,991 | não | 0 |
| 7464 | 65/64 | 0,35990/0,35994 | 0,964 | não | 1 |
| 7616 | 37/36 | 0,35990/0,35994 | 0,983 | não | 1 |
| 7626 | 11/10 | 0,35990/0,35994 | 0,787 | não | 2 |
| 7628 | 43/42 | 0,35993/0,35995 | 0,981 | não | 0 |
| 7635 | 34/33 | 0,35990/0,35994 | 0,982 | não | 2 |
| 7639 | 66/65 | 0,35990/0,35994 | 1,000 | não | 2 |
| 7641 | 80/79 | 0,35990/0,35994 | 0,982 | não | 2 |
| 7642 | 167/166 | 0,35990/0,35994 | 0,781 | não | 0 |
| 7643 | 20/19 | 0,35990/0,35994 | 0,998 | não | 1 |
| 7644 | 29/28 | 0,35990/0,35994 | 0,990 | não | 1 |
| 7645 | 3/2 | 0,35990/0,35994 | 0,802 | não | 0 |
| 7650 | 19/18 | 0,36000/0,36000 | 0,995 | não | 3 |
| 7654 | 32/31 | 0,35990/0,35994 | 1,000 | não | 0 |
| 7665 | 34/33 | 0,35993/0,35995 | — | não | 4 |
| 7666 | 39/38 | 0,35993/0,35995 | 1,000 | não | 0 |
| 7667 | 41/40 | 0,35993/0,35995 | 0,996 | não | 1 |
| 7668 | 60/59 | 0,35993/0,35995 | 1,000 | não | 1 |
| 7669 | 61/60 | 0,35993/0,35995 | — | não | 5 |
| 7671 | 83/82 | 0,35993/0,35995 | — | não | 7 |
| 7674 | 14/13 | 0,36000/0,36000 | 0,300 | não | 14 |
| 7675 | 21/20 | 0,36000/0,36000 | 0,300 | não | 16 |
| 7676 | 18/17 | 0,35993/0,35995 | 0,991 | não | 1 |
| 7677 | 3/2 | 0,35993/0,35995 | 0,993 | não | 1 |
| 7681 | 11/10 | 0,35990/0,35994 | 0,864 | não | 7 |
| 7682 | 7/6 | 0,35990/0,35994 | 0,994 | não | 1 |
| 7683 | 10/9 | 0,36000/0,36000 | — | não | 5 |
| 7684 | 11/10 | 0,36000/0,36000 | 1,000 | não | 4 |
| 7685 | 12/11 | 0,36000/0,36000 | 1,000 | não | 0 |
| 7686 | 8/7 | 0,36000/0,36000 | 0,999 | não | 0 |
| 7687 | 1/0 | 0,35990/0,35994 | 0,536 | não | 17 |
| 7688 | 2/1 | 0,35990/0,35994 | 1,000 | não | 16 |
| 7690 | 1/0 | 0,35990/0,35994 | 1,000 | não | 7 |
| 7692 | 14/13 | 0,35990/0,35994 | 0,912 | não | 0 |
| 7693 | 15/14 | 0,35990/0,35994 | 0,969 | não | 0 |
| 7694 | 2/1 | 0,35990/0,35994 | 0,993 | não | 0 |
| 7695 | 33/32 | 0,35990/0,35994 | 0,957 | não | 2 |
| 7696 | 58/57 | 0,35990/0,35994 | 0,949 | não | 2 |
| 7697 | 109/108 | 0,35990/0,35994 | 0,997 | não | 3 |
| 7698 | 110/109 | 0,35990/0,35994 | 0,997 | não | 3 |
| 7699 | 116/115 | 0,35990/0,35994 | 0,992 | não | 3 |
| 7700 | 118/117 | 0,35990/0,35994 | 0,990 | não | 3 |
| 7702 | 145/144 | 0,35990/0,35994 | 0,987 | não | 2 |
| 7703 | 154/153 | 0,35990/0,35994 | 0,999 | não | 3 |

## Análise de erro

Piores diferenças na saída real contra a XY-cut justa, átomos-ouro; diagnóstico geométrico, sem causas humanas anotadas.

| tarefa/veículo | colunas | Δτ palavras | Δτ regiões | fragmentação | átomos/vazios | pontes | intervenção exploratória |
|---|---:|---:|---:|---:|---:|---:|---:|
| 7208 / rj | 2 | -0,913 | -0,200 | 0,0% | 2/0 | 0 | 1 |
| 7200 / rj | 2 | -0,590 | -0,222 | 0,0% | 6/0 | 0 | 1 |
| 7210 / rj | 1 | -0,493 | -0,088 | 0,0% | 6/0 | 0 | 1 |
| 7681 / sao jose vale rio preto | 1 | -0,122 | -0,800 | 0,0% | 3/3 | 0 | 0 |
| 7181 / df | 1 | -0,116 | -0,444 | 0,0% | 3/3 | 0 | 0 |
| 7177 / df | 1 | -0,095 | -0,533 | 0,0% | 1/1 | 0 | 0 |
| 7645 / teresina | 2 | -0,023 | 0,036 | 27,3% | 0/0 | 14 | 0 |
| 7241 / pb | 2 | -0,011 | -0,002 | 7,8% | 1/1 | 95 | 0 |
| 7193 / pa | 1 | -0,009 | -0,200 | 0,0% | 2/0 | 0 | 0 |
| 7259 / dom ma | 2 | -0,004 | 0,000 | 7,1% | 1/0 | 25 | 0 |

Tarefa 7208: sequência humana de regiões `['region_0019', 'region_0022', 'region_0021', 'region_0023', 'region_0024']`; trechos reais emitidos pelo método congelado `['region_0019', 'region_0021', 'region_0022', 'region_0023', 'region_0024']` (até quarenta transições; ∅ = palavra sem região). Repetições mostram intercalação, enquanto grandes permutações sem repetição mostram inversão de regiões inteiras.

Tarefa 7200: sequência humana de regiões `['region_0232', 'region_0237', 'region_0238', 'region_0241', 'region_0236', 'region_0240', 'AtawSKl1FL', 'region_0242', 'region_0243']`; trechos reais emitidos pelo método congelado `['region_0232', 'region_0236', 'region_0237', 'region_0238', 'region_0240', 'region_0241', 'AtawSKl1FL', 'region_0242', 'region_0243']` (até quarenta transições; ∅ = palavra sem região). Repetições mostram intercalação, enquanto grandes permutações sem repetição mostram inversão de regiões inteiras.

Tarefa 7210: sequência humana de regiões `['region_0001', 'region_0002', 'region_0004', 'region_0005', 'region_0006', 'region_0007', 'region_0009', 'region_0010', 'region_0003', 'region_0011', 'region_0012', 'region_0013', 'region_0014', 'region_0015', 'region_0016', 'region_0017', 'region_0018']`; trechos reais emitidos pelo método congelado `['region_0001', 'region_0002', 'region_0003', 'region_0004', 'region_0005', 'region_0006', 'region_0007', 'region_0009', 'region_0010', 'region_0011', 'region_0012', 'region_0013', 'region_0014', 'region_0015', 'region_0016', 'region_0017', 'region_0018']` (até quarenta transições; ∅ = palavra sem região). Repetições mostram intercalação, enquanto grandes permutações sem repetição mostram inversão de regiões inteiras.

Tarefa 7681: sequência humana de regiões `['region_0036', 'w8ie6nnunk', 'region_0038', 'region_0037', 'region_0041', 'region_0040', 'region_0042', 'region_0043', 'region_0044', 'region_0045', 'region_0046']`; trechos reais emitidos pelo método congelado `['region_0038', 'region_0037', 'w8ie6nnunk', 'region_0046']` (até quarenta transições; ∅ = palavra sem região). Repetições mostram intercalação, enquanto grandes permutações sem repetição mostram inversão de regiões inteiras.

Páginas sem camada textual utilizável: tarefas `[7665, 7669, 7671]`. Não são excluídas da contabilização de cadeias válidas nem recebem nota de palavras; o fallback de regiões nessas páginas é somente diagnóstico.

Há 2 páginas em que a projeção secundária de regiões é perfeita apesar de fragmentação. Átomos com palavras de regiões diferentes podem misturar o texto; a mediana oculta isso. Falhas de texto/escala, geometria humana incompleta, tabelas com leitura interna diferente e layouts por faixas são explicações alternativas, não causalidade estabelecida.

## Limitações e recomendação para o TCC

A amostra concluída é seletiva: páginas sem cadeia válida são excluídas; não representa todas as tarefas do parceiro. n por estrato e número de veículos, sobretudo no teste do detector, podem ser pequenos; IC com poucos grupos é instável. Caixas-ouro são informação humana, e nenhuma avaliação com elas é ganho de produção. Figuras sem texto não entram na métrica principal de palavras; seu posicionamento só aparece na régua secundária com fallback diagnóstico. A referência interna de palavras é geométrica. Não há OCR nem avaliação de texto em raster. O bootstrap agrupa veículos, mas a normalização dos nomes não assegura independência semântica total entre edições. Não provamos veículos inéditos nem anotação sem ancoragem. Páginas de validação do detector não são teste virgem.
**Recomendação:** apresentar a configuração congelada como validação externa de páginas, com régua real, baseline justa e estratos lado a lado. Não usar o τ agregado por mediana para afirmar superioridade geral. Manter a regra exploratória separada; qualquer adoção exige confirmação do Pedro e novo ouro anotado do zero, separado por veículo. Não mudar o protocolo principal do TCC com este script.

## Reprodução e conferência

`venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_ls.py --do-zero`
`venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_ls.py --conferir`
O relatório é gerado do mesmo objeto que `resultado.json`; --conferir recalcula agregados/testes e exige igualdade literal. --do-zero refaz Golden, conversão, extração e detector; havendo resultado anterior com os mesmos hashes, exige igualdade dos números (tempos são excluídos). Manifesto verifica fontes, export, mapa, split, PDFs e imagens antes/depois. Nenhum dado parceiro sai do repositório.
Conferência entre execuções: `{'execucao_do_zero': True, 'assinatura_numerica_igual': True, 'mesmos_hashes_de_codigo_e_dados': False, 'assinatura': 'fc9064185e63908da3c866421414226f1351bfa4c41601b2489d441649640084'}`. JSONs e relatório são gravados em temporário e substituídos após sincronização; caches incompletos são ignorados e a conversão mantém uma marca prévia de saída derivada. Versões do ambiente: `{'numpy': '2.4.6', 'scipy': '1.17.1', 'pdfplumber': '0.11.10', 'Pillow': '12.3.0', 'torch': '2.9.1+cu128', 'ultralytics': '8.4.152'}`.
