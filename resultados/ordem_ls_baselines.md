# Avaliação de Heurísticas de Ordem de Leitura no Conjunto Label Studio (Seed 2)

## Resumo Executivo

1. Foram avaliadas 125 páginas de diários oficiais com cadeias completas e válidas anotadas por humanos no export Seed 2 do Label Studio.
2. No conjunto geral, a heurística XY-cut obteve τ de Kendall médio de 0,884 e acerto de sucessor de 75,4%, superando a abordagem ingênua (0,824 e 66,5%).
3. O processo de anotação sofreu forte viés de ancoragem por ter partido de uma pré-anotação gerada pela própria XY-cut: 49,6% das páginas (62/125) e 69,9% das ligações foram aceitas sem nenhuma modificação.
4. No subconjunto de páginas em que os anotadores efetivamente intervieram e corrigiram a ordem (n = 63), a XY-cut cai para τ = 0,792 e sucessor = 57,3%.
5. Em contraste com o Golden Dataset v4 (44 páginas anotadas do zero, onde a XY-cut registrou τ = 0,825 e sucessor = 71,5%), os números globais do Label Studio estão inflados pela aceitação passiva da sugestão algorítmica.

## Contexto e Desenho Experimental

Este relatório avalia um segundo conjunto de páginas anotadas, derivado das anotações de ordem de leitura do projeto parceiro Datapolicy no Label Studio (`data/labelstudio/ls_p23_seed2_order.json`). Os dados foram convertidos para a estrutura do TCC via `src/anotacao/ordem_labelstudio.py converter`. Foram selecionadas exclusivamente páginas com cadeias de relações válidas (`status = 'concluida'`) produzidas por anotadores humanos identificados (descartando anotações anônimas ou com rótulo 'desconhecido'). Quando uma página continha múltiplas anotações humanas válidas, adotou-se a mais recente como gabarito oficial.

## Concordância Interanotador nas Páginas em Comum

Nenhuma página deste lote possui anotações concluídas duplicadas por múltiplos anotadores humanos simultaneamente. Cada página concluída foi anotada por um único anotador humano.

## Desempenho Geral das Heurísticas de Referência

Abaixo estão os resultados consolidados para as **125 páginas** do conjunto de teste Label Studio. Os intervalos de confiança de 95% foram calculados por bootstrap não paramétrico sobre as páginas com 2.000 reamostragens (semente fixa 7):

| Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |
|---|---:|---:|---:|---:|---:|
| Ordem de entrada / detector (piso) | 125 | **0,627** (0,566 a 0,690) | **63,2%** (58,0% a 68,4%) | 0,145 (0,123 a 0,168) | 23,2% |
| Ingênua (topo→base, esq.→dir.) | 125 | **0,824** (0,786 a 0,859) | **66,5%** (61,2% a 72,0%) | 0,076 (0,061 a 0,092) | 25,6% |
| XY-cut (heurística de colunas) | 125 | **0,884** (0,853 a 0,914) | **75,4%** (70,5% a 80,0%) | 0,051 (0,038 a 0,065) | 43,2% |

## Resultados Estratificados por Anotador

A variabilidade entre anotadores reflete critérios subjetivos de ordenação (ex.: tratamento de cabeçalhos institucionais, rodapés e quebras entre documentos normativos):

### Anotador: `usuario 13` (n = 1 páginas)
| Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |
|---|---:|---:|---:|---:|---:|
| Ordem de entrada / detector (piso) | 1 | **-0,333** (-0,333 a -0,333) | **50,0%** (50,0% a 50,0%) | 0,444 (0,444 a 0,444) | 0,0% |
| Ingênua (topo→base, esq.→dir.) | 1 | **0,833** (0,833 a 0,833) | **37,5%** (37,5% a 37,5%) | 0,074 (0,074 a 0,074) | 0,0% |
| XY-cut (heurística de colunas) | 1 | **0,889** (0,889 a 0,889) | **62,5%** (62,5% a 62,5%) | 0,049 (0,049 a 0,049) | 0,0% |

### Anotador: `usuario 14` (n = 40 páginas)
| Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |
|---|---:|---:|---:|---:|---:|
| Ordem de entrada / detector (piso) | 40 | **0,442** (0,315 a 0,571) | **57,1%** (48,1% a 65,9%) | 0,205 (0,158 a 0,251) | 15,0% |
| Ingênua (topo→base, esq.→dir.) | 40 | **0,780** (0,693 a 0,857) | **63,9%** (54,5% a 73,4%) | 0,092 (0,062 a 0,126) | 25,0% |
| XY-cut (heurística de colunas) | 40 | **0,869** (0,810 a 0,921) | **76,0%** (68,8% a 82,9%) | 0,057 (0,035 a 0,081) | 37,5% |

### Anotador: `usuario 7` (n = 84 páginas)
| Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |
|---|---:|---:|---:|---:|---:|
| Ordem de entrada / detector (piso) | 84 | **0,727** (0,671 a 0,780) | **66,3%** (59,8% a 72,6%) | 0,113 (0,092 a 0,135) | 27,4% |
| Ingênua (topo→base, esq.→dir.) | 84 | **0,844** (0,805 a 0,883) | **68,1%** (61,4% a 74,7%) | 0,068 (0,052 a 0,085) | 26,2% |
| XY-cut (heurística de colunas) | 84 | **0,892** (0,855 a 0,927) | **75,3%** (69,2% a 81,3%) | 0,049 (0,033 a 0,066) | 46,4% |

## Quantificação do Viés de Ancoragem (Anchoring Bias)

Diferentemente do Golden Dataset do TCC (onde a anotação é executada às cegas a partir do zero), a interface do Label Studio deste projeto parceiro carregava previamente as relações geométricas preditas pela própria heurística **XY-cut**. O anotador humano tinha a tarefa de revisar e corrigir eventuais erros.

- **Páginas idênticas à sugestão:** 62 de 125 páginas (**49,6%** foram mantidas 100% inalteradas pelo humano).
- **Páginas com alterações pelo humano:** 63 de 125 páginas (**50,4%** receberam pelo menos uma correção).
- **Ligações preservadas da pré-anotação:** 1206 de 1726 conexões direcionadas (**69,9%** de todas as ligações sucessoras foram aceitas sem ajuste).

Para isolar o efeito da acomodação/ancoragem dos anotadores, a tabela abaixo compara o desempenho das heurísticas entre o grupo de páginas mantidas e o grupo onde o humano realizou correções ativas:

| Subconjunto | Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |
|---|---|---:|---:|---:|---:|---:|
| Páginas mantidas (sem edição) | Ingênua | 62 | **0,870** (0,812 a 0,919) | **74,5%** (66,1% a 82,0%) | 0,050 (0,032 a 0,073) | 46,8% |
| Páginas mantidas (sem edição) | XY-cut | 62 | **0,978** (0,958 a 0,994) | **93,8%** (88,9% a 97,7%) | 0,008 (0,003 a 0,015) | 87,1% |
| Páginas alteradas (com edição) | Ingênua | 63 | **0,777** (0,727 a 0,827) | **58,6%** (51,8% a 65,3%) | 0,101 (0,079 a 0,123) | 4,8% |
| Páginas alteradas (com edição) | XY-cut | 63 | **0,792** (0,741 a 0,839) | **57,3%** (52,1% a 62,6%) | 0,094 (0,073 a 0,116) | 0,0% |

## Comparação com o Benchmark Golden Dataset v4

O `golden_v4` é o benchmark primário do TCC, composto por **44 páginas** de múltiplos estados anotadas do zero pelo autor da pesquisa, sem nenhuma pré-anotação algorítmica (anotação cega). A tabela a seguir contrasta o comportamento da XY-cut entre os dois ambientes de teste:

| Conjunto de Avaliação | Tipo de Anotação | n páginas | τ Kendall XY-cut | Sucessor Correto XY-cut | Acerto Exato |
|---|---|---:|---:|---:|---:|
| **Label Studio (Total)** | Correção de pré-anotação | 125 | **0,884** | **75,4%** | 43,2% |
| **Label Studio (Alteradas)** | Correção efetiva | 63 | **0,792** | **57,3%** | 0,0% |
| **Golden Dataset v4** | Anotação cega (do zero) | 44 | **0,825** | **71,5%** | 22,7% |

### Conclusões Metodológicas e Limitações

1. **Favorecimento estrutural da heurística:** A XY-cut atinge índices artificialmente elevados (τ = 0,884) no total do Label Studio porque o humano atuou como validador de um rascunho construído por ela mesma. Quando um layout complexo apresentava ordem plausível, o anotador tendeu a aprová-la.
2. **Comportamento sob divergência:** No subgrupo onde o humano deliberadamente corrigiu a cadeia (n = 63), a XY-cut obteve τ = 0,792 e sucessor = 57,3%, evidenciando os pontos cegos da geometria pura (intercalação de matérias, títulos de largura total inseridos no meio de colunas e caixas isoladas).
3. **Recomendação para o TCC:** Este conjunto do Label Studio deve ser tratado como uma **bancada de auditoria de pré-anotação** e não como gabarito neutro equivalente ao Golden Dataset v4. A inclusão destas métricas no texto do TCC ilustra com clareza o impacto do viés de ancoragem em tarefas de recuperação de ordem e estruturação documental.
