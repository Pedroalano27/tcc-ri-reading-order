# Ordem de leitura sem regiões finas

## Resumo em cinco linhas

1. Nas 44 páginas, o plano com seleção LOPO alcançou τ = 0,917, contra 0,825 da XY-cut em regiões humanas e 0,798 no extrator automático.
2. O sucessor em regiões foi 82,1%, contra 71,5% da referência; em linhas, 92,1% contra 88,6%.
3. A diferença pareada de τ em regiões foi 0,092, IC 95% [0,016; 0,162], Wilcoxon p = 0,01300.
4. No estrato multicoluna, τ de regiões foi 0,887 contra 0,913; o ganho agregado não significa vitória em todos os layouts.
5. Veredito: vale avançar com projeção local, política de margens e átomos bem delimitados; a melhora é exploratória e precisa de teste novo por veículo antes de substituir o pipeline.

## Dados e auditoria

Foram lidas 45 tarefas e 46 registros de anotação: {'concluida': 44, 'pulada': 1, 'rascunho': 1}. Filtrou-se `concluida` antes de deduplicar por `page_id`; um rascunho posterior não revoga a ordem concluída. Nenhuma página concluída foi excluída.

Distribuição pelo `stats.n_colunas` fornecido: {'1': 24, '2': 13, '3': 7}. Esse campo é uma estimativa geométrica do preparador do Golden, não uma anotação independente de colunas; serve somente para estratificar e nunca alimenta o preditor.

Dimensões idênticas entre Golden e Diamond em todas as páginas. A associação por centro e menor região, preferindo não figura, recuperou 1438 regiões e 4729 linhas com palavras. Textos reconstruídos divergentes: 3; divergências no multiconjunto de tokens: 0; regiões sem palavras: 0; centros de palavras fora da página (tolerância de um ponto): 0. As divergências são somente de ordenação de palavras em cabeçalhos com fontes de alturas diferentes (Seropédica e Salvador): o agrupador atual atualiza a altura da faixa, o montador do Golden não o fazia. Nenhuma é perda de palavras ou erro de escala/coordenadas.

Há 36195 palavras; 24 ficam fora das regiões-ouro e 0 pertencem geometricamente a mais de uma caixa. As primeiras continuam na predição e são excluídas apenas da régua sem referência; as segundas recebem um único dono pelo critério do preparador. Hashes das quatro entradas e dos módulos reutilizados foram conferidos antes/depois e estão no JSON.

## Implementação e réguas

O preditor recebe somente palavras e regiões cruas `table`/`picture`. Não recebe ordem do PDF, `bloco` das palavras, regiões humanas, classes finas do detector nem contagem de colunas. Aceita átomos por score, suprime caixas com pelo menos 60% da própria área dentro de uma aceita (tabela primeiro) e atribui por centro. Palavras dentro de imagem também saem do fluxo: trata-se exatamente da proposta pedida, inclusive quando o detector chama um cabeçalho decorativo de imagem.

O restante é agrupado com `src.data.regioes.linhas` e partido nos grandes vãos horizontais. Foram comparadas: (a) XY-cut recursiva diretamente nos fragmentos de linha e átomos; (b) projeção horizontal da ocupação por envelopes das linhas, com vales de espaço em branco, suporte vertical dos dois lados e recursão. Linhas largas são retiradas do perfil; caixas que atravessam os cortes separam seções acima/abaixo. Sem vale, a projeção recorre à XY-cut existente. Isso permite layout variável por faixa, mas a regra de pontes pode interromper colunas indevidamente.

A terceira abordagem, `projecao_local`, vota em vales que reaparecem em pelo menos duas janelas verticais sobrepostas (altura igual ao maior valor entre cem pontos e doze alturas de linha, passo de meia janela). Ela evita que um rodapé de outro arranjo abafe a calha do corpo. Também exige que uma ponte cubra pelo menos 10% da largura do conjunto em cada lado do corte: um título curto iniciado na calha é atribuído à coluna pelo centro, em vez de interromper toda a página. Há fallback para o perfil global e para XY-cut. As janelas e o filtro de pontes são hipóteses geométricas fixas, não classes finas.

As variantes `*_margens` adicionam uma política geométrica fixa: itens com centro acima de 7% da altura e base acima de 10% vêm primeiro; abaixo de 95% vêm por último. Marcas reconhecidas pela expressão `RE_MARCACAO` vão antes do rodapé. São heurísticas de posição/conteúdo, sem previsão de classe fina. Os limiares de margem não foram varridos; podem deslocar conteúdo legítimo.

**Regiões:** posição prevista = mediana dos ranks das palavras daquela região. **Linhas:** ouro = regiões na ordem humana, expandidas com `linhas()` de cima para baixo e palavras da esquerda para a direita; posição prevista da linha = mediana dos ranks de suas palavras. Átomos são expandidos internamente por esse mesmo critério só para medir linhas, permanecendo contíguos na predição. Todas as ordens avaliadas são permutações completas dos mesmos identificadores, sem consertar faltantes pela ordem humana. Empates usam geometria e ID, nunca rank-ouro.

XY-cut e ingênua em regiões humanas têm segmentação-oráculo; sua régua de regiões usa a sequência diretamente e a régua de linhas expande cada região internamente. A XY-cut recalculada e a ingênua coincidiram exatamente com as armazenadas em todas as páginas. O extrator automático é `propor(..., regras=True)` com `fundir=True` atual; as palavras são reassociadas às caixas pelo mesmo critério, ordenadas por XY-cut e expandidas por linhas.

Fallback de palavras sem caixa do extrator automático: 16 (anexadas geometricamente ao fim, sem consultar o ouro). Empates na projeção LOPO: 0 em regiões e 0 em linhas.

## Seleção de parâmetros e inferência

A grade final tem 60 configurações: score ≥ 0,45/0,65/0,85; vão de linha > 1,2/2,0 alturas medianas; projeção com vale ≤ 0,08/0,20 da ocupação positiva mediana, em bins de dois pontos e largura mínima de quatro pontos; seis variantes de abordagem/política. O cache já elimina detecções abaixo de 0,45, portanto não permite avaliar um detector mais permissivo.

**Exploração declarada:** a primeira grade tinha 36 configurações sem projeção local. Após medir e inspecionar os erros dessas mesmas páginas, acrescentou-se a hipótese de janelas locais e suporte dos dois lados. Portanto, o desenho da abordagem local foi informado por este ouro. A validação por página abaixo não torna essa fase um teste independente.

O resultado **LOPO** escolhe a configuração de maior τ médio de regiões nas outras páginas, sem usar a métrica da página retida; desempates usam sucessor e depois a ordem fixa da grade. A melhor configuração na amostra também é mostrada, **com seleção e avaliação nas mesmas páginas**, portanto otimista. O desenvolvimento do algoritmo foi feito neste conjunto: LOPO reduz o viés de escolher parâmetros, mas não apaga o viés de desenvolvimento nem o parentesco entre páginas do mesmo veículo.

Melhor configuração na amostra: `projecao_local_margens_s0.45_g1.2_v0.08`. Escolhas LOPO: {'projecao_local_margens_s0.45_g1.2_v0.08': 42, 'projecao_local_s0.45_g1.2_v0.20': 2}. Não há treino de rede, uso de GPU, OCR ou acesso a dados de terceiros. Foram executados 8 controles sintéticos: colunas, faixa que interrompe colunas, atomicidade/NMS e uma contraprova de inversão de tabelas por pequenas diferenças de topo.

Médias macro por página; IC percentil 95% com 5000 reamostras de páginas, semente 42. IC de diferenças usa pares das mesmas páginas. Os IC são condicionais às configurações selecionadas: não refazem a seleção dentro do bootstrap. Wilcoxon bilateral pareado (`zero_method='wilcox'`, SciPy `method='auto'`), com p bruto e correção Holm entre as três métricas de cada régua. Testes são exploratórios, não um teste de equivalência/não inferioridade.

## Tabela principal — todas as páginas

Régua de regiões (comparável ao relatório do TCC):

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,825 [0,766; 0,882] | 71,5% [63,2; 79,6] | 0,083 [0,056; 0,111] |
| Ingênua nas regiões-ouro | 0,713 [0,642; 0,785] | 57,5% [48,2; 67,0] | 0,124 [0,093; 0,155] |
| XY-cut no extrator automático | 0,798 [0,737; 0,857] | 66,4% [58,4; 74,6] | 0,093 [0,065; 0,122] |
| Sem bbox fina — seleção por página (LOPO) | 0,917 [0,868; 0,957] | 82,1% [74,9; 88,2] | 0,035 [0,019; 0,055] |
| Sem bbox fina — melhor na amostra* | 0,937 [0,896; 0,970] | 85,2% [79,6; 90,2] | 0,026 [0,013; 0,042] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,903 [0,849; 0,948] | 83,0% [76,8; 88,6] | 0,039 [0,022; 0,060] |

Régua de linhas:

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,848 [0,785; 0,909] | 88,6% [84,5; 92,4] | 0,074 [0,044; 0,105] |
| Ingênua nas regiões-ouro | 0,749 [0,671; 0,827] | 86,1% [82,0; 90,1] | 0,117 [0,081; 0,154] |
| XY-cut no extrator automático | 0,810 [0,739; 0,877] | 85,8% [81,5; 89,9] | 0,092 [0,059; 0,126] |
| Sem bbox fina — seleção por página (LOPO) | 0,945 [0,889; 0,983] | 92,1% [88,2; 95,3] | 0,026 [0,008; 0,054] |
| Sem bbox fina — melhor na amostra* | 0,979 [0,968; 0,989] | 92,2% [88,3; 95,4] | 0,009 [0,005; 0,014] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,968 [0,949; 0,985] | 92,9% [89,4; 95,6] | 0,015 [0,007; 0,024] |

\* Selecionada na mesma amostra; não é estimativa de generalização. O oráculo tabela/imagem é um contrafactual com caixas humanas dessas classes, usando a configuração LOPO correspondente; não é um método disponível em produção.

A referência reproduziu τ = 0,825 e sucessor = 71,5%, como os valores citados de 0,825 e 71,5%.

## Estratificação por número de colunas

### Uma coluna — n = 24

Regiões:

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,752 [0,658; 0,843] | 61,5% [49,2; 74,0] | 0,117 [0,073; 0,162] |
| Ingênua nas regiões-ouro | 0,736 [0,643; 0,831] | 62,1% [49,8; 74,9] | 0,125 [0,080; 0,169] |
| XY-cut no extrator automático | 0,753 [0,660; 0,846] | 62,8% [51,7; 74,4] | 0,117 [0,072; 0,162] |
| Sem bbox fina — seleção por página (LOPO) | 0,942 [0,886; 0,982] | 84,4% [74,5; 92,2] | 0,026 [0,008; 0,051] |
| Sem bbox fina — melhor na amostra* | 0,979 [0,968; 0,989] | 90,1% [85,5; 94,3] | 0,010 [0,005; 0,015] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,942 [0,884; 0,982] | 86,2% [79,1; 92,2] | 0,026 [0,008; 0,052] |

Linhas:

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,755 [0,650; 0,857] | 84,1% [77,8; 90,1] | 0,120 [0,070; 0,170] |
| Ingênua nas regiões-ouro | 0,741 [0,638; 0,841] | 85,2% [78,8; 91,3] | 0,127 [0,078; 0,177] |
| XY-cut no extrator automático | 0,749 [0,645; 0,852] | 83,4% [77,4; 89,3] | 0,122 [0,073; 0,173] |
| Sem bbox fina — seleção por página (LOPO) | 0,923 [0,821; 0,988] | 94,3% [92,0; 96,4] | 0,038 [0,006; 0,089] |
| Sem bbox fina — melhor na amostra* | 0,986 [0,977; 0,993] | 94,5% [92,1; 96,6] | 0,007 [0,003; 0,011] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,973 [0,946; 0,990] | 93,8% [91,3; 96,1] | 0,013 [0,005; 0,027] |

### Multicoluna — n = 20

Regiões:

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,913 [0,863; 0,953] | 83,5% [75,0; 90,9] | 0,041 [0,022; 0,064] |
| Ingênua nas regiões-ouro | 0,686 [0,572; 0,799] | 52,0% [38,5; 65,8] | 0,123 [0,078; 0,168] |
| XY-cut no extrator automático | 0,853 [0,781; 0,915] | 70,7% [59,1; 81,3] | 0,063 [0,036; 0,094] |
| Sem bbox fina — seleção por página (LOPO) | 0,887 [0,803; 0,954] | 79,4% [69,0; 88,5] | 0,047 [0,020; 0,079] |
| Sem bbox fina — melhor na amostra* | 0,887 [0,803; 0,954] | 79,4% [69,0; 88,5] | 0,047 [0,020; 0,079] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,857 [0,763; 0,936] | 79,2% [68,7; 88,3] | 0,055 [0,027; 0,089] |

Linhas:

| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,961 [0,927; 0,986] | 94,1% [90,1; 97,3] | 0,019 [0,007; 0,036] |
| Ingênua nas regiões-ouro | 0,760 [0,632; 0,882] | 87,2% [82,0; 91,9] | 0,106 [0,052; 0,163] |
| XY-cut no extrator automático | 0,884 [0,792; 0,960] | 88,7% [82,4; 93,9] | 0,055 [0,019; 0,100] |
| Sem bbox fina — seleção por página (LOPO) | 0,971 [0,948; 0,990] | 89,5% [81,8; 95,9] | 0,012 [0,005; 0,021] |
| Sem bbox fina — melhor na amostra* | 0,971 [0,948; 0,990] | 89,5% [81,8; 95,9] | 0,012 [0,005; 0,021] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 0,963 [0,932; 0,988] | 91,7% [84,7; 96,9] | 0,016 [0,005; 0,031] |

O ganho em regiões se concentra no estrato classificado como uma coluna: τ 0,752 → 0,942. No estrato multicoluna, o plano perde em τ de regiões e sucessor, enquanto τ de linhas muda de 0,961 para 0,971; sucessor de linhas cai de 94,1% para 89,5%.

**Cuidado com esse estrato:** a inspeção mostra o Legislativo do RJ com três colunas e Manaus com duas tabelas lado a lado, embora ambos tenham `stats.n_colunas = 1`. Duque de Caxias/capa também tem duas colunas visuais e está no estrato de uma. AC e MS, com uma tabela larga e cabeçalho em campos, entram como multicoluna. Mantive o campo solicitado sem corrigir dados; não interpretar estas tabelas como separação perfeita da complexidade visual.

## Wilcoxon e diferenças pareadas contra XY-cut nas regiões-ouro

| Método | Régua | Métrica | Δ médio (IC 95%) | Ganha/empata/perde | W | p bruto | p Holm |
|---|---|---|---:|---:|---:|---:|---:|
| Sem bbox fina — seleção por página (LOPO) | regioes | tau | 0,092 [0,016; 0,162] | 23/11/10 | 141,5 | 0,013002 | 0,034370 |
| Sem bbox fina — seleção por página (LOPO) | regioes | sucessor | 0,107 [-0,013; 0,213] | 22/11/11 | 168,0 | 0,044405 | 0,044405 |
| Sem bbox fina — seleção por página (LOPO) | regioes | ard | -0,047 [-0,080; -0,014] | 23/11/10 | 139,0 | 0,011457 | 0,034370 |
| Sem bbox fina — seleção por página (LOPO) | linhas | tau | 0,097 [0,013; 0,176] | 24/7/13 | 175,0 | 0,007751 | 0,022701 |
| Sem bbox fina — seleção por página (LOPO) | linhas | sucessor | 0,035 [-0,012; 0,082] | 17/8/19 | 276,0 | 0,370518 | 0,370518 |
| Sem bbox fina — seleção por página (LOPO) | linhas | ard | -0,048 [-0,086; -0,006] | 24/8/12 | 163,0 | 0,007567 | 0,022701 |
| Sem bbox fina — melhor na amostra* | regioes | tau | 0,112 [0,037; 0,185] | 24/11/9 | 119,0 | 0,003905 | 0,010754 |
| Sem bbox fina — melhor na amostra* | regioes | sucessor | 0,138 [0,035; 0,237] | 23/12/9 | 122,0 | 0,007921 | 0,010754 |
| Sem bbox fina — melhor na amostra* | regioes | ard | -0,056 [-0,089; -0,023] | 24/11/9 | 117,5 | 0,003585 | 0,010754 |
| Sem bbox fina — melhor na amostra* | linhas | tau | 0,131 [0,071; 0,195] | 25/8/11 | 113,0 | 0,000548 | 0,001548 |
| Sem bbox fina — melhor na amostra* | linhas | sucessor | 0,036 [-0,011; 0,083] | 18/9/17 | 253,0 | 0,309864 | 0,309864 |
| Sem bbox fina — melhor na amostra* | linhas | ard | -0,065 [-0,096; -0,036] | 25/9/10 | 103,0 | 0,000516 | 0,001548 |

Δ = plano − referência; ARD negativo é melhora. Ausência de significância não prova equivalência.

## Sensibilidade e continuidade ocultada pela mediana

| Abordagem | Configuração de maior τ na amostra* | τ regiões | Sucessor regiões | τ linhas | Sucessor linhas |
|---|---|---:|---:|---:|---:|
| projecao | `projecao_s0.45_g1.2_v0.20` | 0,921 | 80,7% | 0,928 | 90,8% |
| projecao_local | `projecao_local_s0.45_g1.2_v0.20` | 0,930 | 83,1% | 0,946 | 92,9% |
| projecao_local_margens | `projecao_local_margens_s0.45_g1.2_v0.08` | 0,937 | 85,2% | 0,979 | 92,2% |
| projecao_margens | `projecao_margens_s0.45_g1.2_v0.08` | 0,924 | 83,3% | 0,963 | 90,3% |
| xy_linhas | `xy_linhas_s0.45_g1.2_v0.12` | 0,805 | 64,4% | 0,793 | 70,1% |
| xy_margens | `xy_margens_s0.45_g1.2_v0.12` | 0,907 | 79,5% | 0,946 | 85,7% |

Todas as configurações e métricas por página estão no JSON; as linhas acima também são selecionadas na amostra.

| Score | Melhor configuração na amostra* | τ regiões | Sucessor regiões | τ linhas |
|---|---|---:|---:|---:|
| 0,45 | `projecao_local_margens_s0.45_g1.2_v0.08` | 0,937 | 85,2% | 0,979 |
| 0,65 | `projecao_local_margens_s0.65_g1.2_v0.08` | 0,916 | 83,3% | 0,977 |
| 0,85 | `projecao_local_s0.85_g1.2_v0.20` | 0,916 | 82,1% | 0,947 |

A projeção por mediana pode esconder texto interrompido: computou-se também a fração de regiões-ouro cujas palavras reaparecem em mais de um trecho da sequência real (ignorando palavras sem dono).

| Método | Regiões fragmentadas (média por página) | τ somente linhas de texto | Sucessor somente linhas de texto |
|---|---:|---:|---:|
| XY-cut nas regiões-ouro | 0,0% | 0,838 [0,769; 0,903] | 87,2% [82,9; 91,3] |
| Ingênua nas regiões-ouro | 0,0% | 0,678 [0,578; 0,771] | 78,5% [70,9; 85,4] |
| XY-cut no extrator automático | 1,3% | 0,795 [0,721; 0,863] | 83,4% [77,5; 88,6] |
| Sem bbox fina — seleção por página (LOPO) | 3,6% | 0,910 [0,830; 0,970] | 87,0% [80,6; 92,4] |
| Sem bbox fina — melhor na amostra* | 3,6% | 0,925 [0,849; 0,977] | 87,2% [80,8; 92,5] |
| LOPO com tabela/imagem do ouro (diagnóstico) | 2,9% | 0,890 [0,800; 0,961] | 86,6% [80,1; 92,2] |

‘Somente texto’ exclui tabelas/figuras humanas, mas inclui títulos, listas, assinaturas e margens; evita que muitas linhas de uma tabela dominem a interpretação da continuidade.

### Teste da hipótese local nas páginas inspecionadas

As duas configurações abaixo têm os mesmos score, vão e limiar de vale. Mudam conjuntamente a votação em janelas e o critério de ponte; esta comparação não separa o efeito de cada componente e foi motivada pelos erros da amostra.

| Página | τ regiões: perfil global → local | τ linhas: global → local | Sucessor de linhas: global → local |
|---|---:|---:|---:|
| `official_diary_ma/executive_official_diary_2023-03-06.pdf#p71` | 0,836 → 1,000 | 0,780 → 1,000 | 97,1% → 100,0% |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 0,555 → 0,979 | 0,501 → 0,988 | 3,8% → 89,1% |

No RJ, o rodapé contém outro arranjo de colunas: o perfil global não encontrou a calha do corpo e intercalou linhas; a versão local recuperou o corpo. No MA, ‘ARTIGOS’ começa dentro da calha mas pertence à coluna direita: tratá-lo como ponte interrompia a esquerda. São falhas da organização espacial que um detector de tabela/imagem sozinho não corrige.

## Onde o plano perde mais

Páginas ordenadas pela perda de τ de regiões do LOPO contra a referência. Diagnósticos abaixo são evidência geométrica e contrafactual, não rótulos causais anotados.

| Página (`page_id`, índice de página do arquivo) | Colunas | τ referência → plano | Δ τ | Sucessor ref. → plano | τ com átomos-ouro |
|---|---:|---:|---:|---:|---:|
| `official_diary_ac/executive_official_diary_2022-08-03.pdf#p109` | 2 | 1,000 → 0,333 | -0,667 | 100,0% → 33,3% | 0,333 |
| `official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48` | 2 | 1,000 → 0,600 | -0,400 | 100,0% → 50,0% | 0,600 |
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 1 | 1,000 → 0,667 | -0,333 | 100,0% → 0,0% | 1,000 |
| `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 3 | 1,000 → 0,800 | -0,200 | 100,0% → 25,0% | 0,400 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 3 | 0,867 → 0,733 | -0,133 | 40,0% → 60,0% | 0,733 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2` | 3 | 0,867 → 0,733 | -0,133 | 40,0% → 60,0% | 0,733 |

A régua de regiões dá peso igual a páginas com poucas caixas e a páginas com muito texto. Por isso as trocas de campos no cabeçalho de AC/MS aparecem entre as maiores perdas, embora o corpo da tabela esteja correto. Para não esconder falhas no conteúdo, seguem também os maiores recuos nas réguas de linhas (união dos maiores recuos de τ e de sucessor).

| Página | Regiões / linhas-ouro | τ linhas: ref. → plano | Sucessor de linhas: ref. → plano | τ linhas com átomos-ouro |
|---|---:|---:|---:|---:|
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 4 / 218 | 1,000 → 0,014 | 100,0% → 98,6% | 1,000 |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | 15 / 155 | 0,708 → 0,474 | 96,1% → 94,8% | 0,708 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2` | 6 / 11 | 0,964 → 0,855 | 70,0% → 50,0% | 0,855 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 6 / 12 | 0,970 → 0,879 | 72,7% → 54,5% | 0,879 |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | 21 / 150 | 0,715 → 0,887 | 95,3% → 53,7% | 0,767 |

### `official_diary_ac/executive_official_diary_2022-08-03.pdf#p109`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 2 inversões entre regiões, 2 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,000. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b2 (tabela): 100,0%.
Regiões mais deslocadas (posições começam em zero):

- `b1` (cabecalho), ouro 2 → predição 0: “DIÁRIO OFICIAL 110”.
- `b3` (cabecalho), ouro 0 → predição 1: “110 Quarta-feira, 03 de Agosto de 2022”.
- `b0` (cabecalho), ouro 1 → predição 2: “Nº 13.341”.

**Inspeção:** tabela larga bem delimitada, sem intercalação no corpo. A falha está na ordem dos campos da faixa superior: a bbox de ‘DIÁRIO OFICIAL 110’ começa mais acima e esse campo é lido antes do campo esquerdo, embora pertençam à mesma faixa visual. A política de margens separa cabeçalho/corpo, mas ainda ordena seus fragmentos por topo exato. Um detector melhor de tabela não resolve essa tolerância vertical. A perda em regiões é grande porque há poucas regiões, enquanto a régua de linhas permanece quase perfeita.

### `official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 2 inversões entre regiões, 2 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,000. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b0 (tabela): 100,0%.
Regiões mais deslocadas (posições começam em zero):

- `b3` (cabecalho), ouro 0 → predição 2: “Diário Oficial Eletrônico n. 10.553- Suplemento”.
- `b4` (cabecalho), ouro 1 → predição 0: “29 de junho de 2021”.
- `b2` (cabecalho), ouro 2 → predição 1: “Página 49”.

**Inspeção:** campos do cabeçalho na mesma faixa visual, tabela única no corpo. Pequenas diferenças subpontuais de topo nas palavras colocam data e página antes do nome do diário. As caixas arredondadas do ouro empatam nesse topo e a referência as lê da esquerda para a direita. O corpo e a tabela não são a causa: é preciso agrupar campos por faixa com tolerância, sem depender de uma classe fina para cada um.

### `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22`

Configuração: `projecao_local_s0.45_g1.2_v0.20`. Das 1 inversões entre regiões, 0 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,333. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b1 (tabela): 100,0%; b2 (tabela): 100,0%.
Regiões mais deslocadas (posições começam em zero):

- `b1` (tabela), ouro 2 → predição 1: “4711 108.195-0A ORLANDO TEIXEIRA DA SILVA APROVADO 4712 108.513-1A ORLEILSON CAVALCANTE AMAZONAS NÃO HABILITADO 4713 091.165-8B OSCAR ALBERTO DA COSTA HURTADO APROVADO 4714 088.302”.
- `b2` (tabela), ouro 1 → predição 2: “4603 111.181-7A NELY NASCIMENTO VITAL APROVADO 4604 085.051-9B NELY WANDA DA SILVA ALENCAR APROVADO 4605 122.805-6A NEODETE KORBES MAUES APROVADO 4606 083.814-4B NERLISON DE SOUZA ”.
- `b3` (cabecalho), ouro 0 → predição 0: “Manaus, segunda-feira, 13 de março de 2023”.

**Inspeção:** duas tabelas lado a lado, ambas integralmente detectadas. Na configuração escolhida ao deixar esta página de fora, não há política de margens; cabeçalho e rodapé centralizados bloqueiam o corte vertical, não há linhas suficientes para o perfil e o fallback desempata pelo topo. A tabela direita começa ligeiramente acima e vem antes da esquerda. O oráculo corrige a ordem ao usar caixas ajustadas/arredondadas: isso não significa que a tabela estivesse ausente. A alta continuidade de linhas dentro dos átomos convive com a inversão de quase todo o conteúdo da página.

### `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 1 inversões entre regiões, 1 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em -0,400. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b1 (tabela): 68,2%.
Regiões mais deslocadas (posições começam em zero):

- `b0` (cabecalho), ouro 2 → predição 1: “Página 234”.
- `b4` (cabecalho), ouro 1 → predição 2: “5 de novembro de 2024”.
- `b3` (cabecalho), ouro 0 → predição 0: “Diário Oficial Eletrônico n. 11.660 - Suplemento”.

**Inspeção:** o detector gera uma tabela estreita à esquerda e outra larga que absorve parte do cabeçalho. A atribuição à menor tabela reparte as palavras de uma única tabela humana; o cabeçalho absorvido participa do átomo e sua mediana muda a ordem dos campos. Melhor delimitação/instanciamento ajudaria, mas o oráculo ainda perde por ordenar campos do topo por coordenadas exatas. Não atribuir esta perda só a coluna mal detectada.

### `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 2 inversões entre regiões, 2 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,000. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: não há tabela/imagem humana.
Regiões mais deslocadas (posições começam em zero):

- `b5` (rodape), ouro 3 → predição 5: “Barra do Piraí/RJ”.
- `b2` (rodape), ouro 4 → predição 3: “3”.
- `b1` (rodape), ouro 5 → predição 4: “DIÁRIO OFICIAL ELETRÔNICO garante autenticidade deste documento visualizado diretamente no portal www.barradopirai.rj.gov.br”.

**Inspeção:** sumário e cartaz, sem corpo de jornal em colunas. As imagens puras não têm texto no ouro. No rodapé, o nome do município, a página e a autenticação ocupam campos lado a lado, mas a autenticação tem várias linhas. O fluxo por linhas intercala esses campos; a política de fim da página não preserva a unidade de cada campo. Três classes não distinguem nem agrupam esses rodapés. O `stats.n_colunas` decorre dos campos laterais e não descreve o corpo.

### `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 2 inversões entre regiões, 2 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,000. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: não há tabela/imagem humana.
Regiões mais deslocadas (posições começam em zero):

- `b1` (rodape), ouro 3 → predição 5: “Barra do Piraí/RJ”.
- `b3` (rodape), ouro 4 → predição 3: “3”.
- `b2` (rodape), ouro 5 → predição 4: “DIÁRIO OFICIAL ELETRÔNICO garante autenticidade deste documento visualizado diretamente no portal www.barradopirai.rj.gov.br”.

**Inspeção:** repete o arranjo de sumário/cartaz e campos no rodapé de Barra do Piraí. A autenticação é interrompida pelo número da página e pelo nome do município. Imagens são corretamente tratadas como átomos sem texto, mas sua posição não é avaliável pelo Golden; o erro medido vem da organização dos fragmentos textuais do rodapé.

### `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26`

Configuração: `projecao_local_s0.45_g1.2_v0.20`. Das 30 inversões entre regiões, 1 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em 0,000. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b0 (tabela): 100,0%; b3 (tabela): 100,0%; b5 (tabela): 100,0%; b6 (tabela): 100,0%; b7 (tabela): 100,0%; b9 (tabela): 100,0%; b11 (tabela): 100,0%; b13 (tabela): 100,0%.
Regiões mais deslocadas (posições começam em zero):

- `b11` (tabela), ouro 9 → predição 3: “DOUGLAS VICTOR GUEDES XAVIER 02/05/2015 ANNE GABRYELLE SANTOS VICENTE 23/03/2014 FERNANDA SIMPLICIO DA SILVA 02/04/2014 LUAN DANIEL SANTOS MACIEL DINIZ 25/07/2012 LEONARDO RAVI RAM”.
- `b8` (titulo), ouro 5 → predição 11: “6º ANO DO ENS. FUND. II FILHOS E NETOS DE POLICIAIS MILITARES DA PARAÍBA PCD”.
- `b5` (tabela), ouro 6 → predição 12: “NOME DO CONTEMPLADO DN JOAN ANTÔNIO TENORIO DA COSTA 18/11/2014”.

**Inspeção:** tabelas em duas colunas visuais, embora o estrato fornecido seja uma coluna. A escolha LOPO também removeu a política de margens nesta página. O cabeçalho atravessa a calha e o perfil não a resolve; caixas de tabelas à direita começam ligeiramente acima das correspondentes à esquerda e o fallback intercala partes das colunas. Caixas humanas reduzem a perda de linhas, mas não resolvem toda a ordenação. A necessidade principal é organização de faixas/colunas e desempate estável entre átomos, além de qualidade das bordas.

### `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`

Configuração: `projecao_local_margens_s0.45_g1.2_v0.08`. Das 6 inversões entre regiões, 3 envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em -0,133. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: b0 (tabela): 100,0%; b3 (tabela): 100,0%; b4 (tabela): 100,0%; b11 (tabela): 100,0%.
Regiões mais deslocadas (posições começam em zero):

- `b14` (cabecalho), ouro 3 → predição 0: “45”.
- `b11` (tabela), ouro 16 → predição 19: “Código Nota TWa%$q61 3,25 KUy&$u98 4,25 WPn&%o75 4,25 VJq$#r74 2,75 EXq%$a55 4,25 YWy##m74 2,75 SVh$$c86 3,75 TEd#$u31 4,25 IMg$#z18 2,00 LAa##v52 2,75 VWe$%u56 2,75 ZSe##c12 2,00 ”.
- `b17` (cabecalho), ouro 0 → predição 1: “Boletim Oficial do Município”.

**Inspeção:** tabelas independentes lado a lado. O detector propõe tanto caixas por coluna quanto caixas que englobam as duas tabelas; uma caixa larga remanescente recebe palavras dos dois lados. Sua expansão interna por linhas intercala as tabelas, derrubando a continuidade mesmo quando a projeção por mediana acerta boa parte das regiões. Aqui um detector de três classes com melhor **delimitação de instâncias** ajudaria diretamente; classificar como ‘tabela’ a caixa larga já é correto e não basta.

## O que um detector de três classes resolveria

Mantendo a configuração LOPO e substituindo apenas os átomos detectados pelas caixas humanas de tabela/imagem, o τ em regiões vai de 0,917 para 0,903; o sucessor vai de 82,1% para 83,0%. Em linhas, τ vai de 0,945 para 0,968. O contrafactual também remove falsos positivos de tabela/imagem e pode alterar as colunas; não é um teto matemático e não simula um detector treinado.

Uma detecção melhor pode preservar tabelas que hoje viram texto, evitar que fotos/logos absorvam palavras externas e corrigir a caixa de um átomo que bloqueia uma calha. Ela não decide a continuidade entre colunas, não reconhece sozinha título que atravessa colunas, não distingue cabeçalho/rodapé do texto com apenas essas três classes e não fornece OCR, ordem de células, legenda associada ou semântica do ato. A classe ‘texto’ não foi usada como bbox de região neste plano: usar caixas textuais previstas seria outra variante de segmentação.

O diagnóstico usa somente átomos que ficaram no Golden com texto: imagens puras, mesmo corretamente detectadas, somem no contrafactual. Além disso, caixas humanas podem ser mais justas às palavras do que a borda visual da tabela. Logo, o oráculo não simula uma taxonomia de três classes perfeita. Sua queda em τ de regiões reforça que bordas e política de colunas/margens interagem: melhorar detecção não garante melhora monótona da ordenação.

## Limitações e recomendação

- Amostra pequena e de conveniência: páginas já anotadas do piloto/treino Diamond, mesmo anotador e famílias de layout repetidas. Bootstrap por página não modela dependência por veículo; seus intervalos podem ser estreitos demais.
- Ouro de linhas derivado das regiões, sem anotação humana independente dentro delas. Linhas de tabela usam topo→base/esquerda→direita; este experimento mede a posição da tabela e essa expansão, não sua estrutura semântica. Imagens sem texto foram retiradas ao montar o Golden e sua posição não pode ser avaliada aqui.
- Caixas Diamond partiram de propostas automáticas corrigidas, com possível ancoragem na granularidade original. A referência em regiões tem segmentação humana disponível, ao contrário dos métodos automáticos. Não atribuir toda diferença apenas ao algoritmo de ordenação.
- Medianas apagam intercalações dentro das regiões e linhas. A fragmentação complementar revela parte delas, mas não avalia palavra por palavra, OCR, fidelidade de frases nem impacto em RI.
- Parâmetros e desenvolvimento exploratórios sobre estas páginas; LOPO por página não equivale a teste novo por veículo. Os p-valores da melhor variante na amostra são especialmente otimistas, e a correção Holm não corrige a exploração de algoritmos.
- Cache Docling truncado em score 0,45, somente PDFs com camada de texto; não se avaliou modelo de três classes treinado, imagem pura ou custo do detector. Não é um experimento de latência nem comparação de treinamento entre taxonomias.

**Recomendação:** sim, vale seguir o plano como uma alternativa ao extrator fino, **com projeção local, políticas de margens e átomos que respeitem colunas**. O protótipo melhora a média global de τ nas duas réguas, mas a continuidade local não apresenta melhora inequívoca e o estrato multicoluna perde em regiões. Antes de adotá-lo, testar em páginas novas desenhadas/anotadas sem proposta e separar veículos para desenvolvimento/teste; exigir continuidade de linhas e regiões junto com τ; validar tabela/imagem e políticas de margens. Manter o comparador de regiões finas no TCC e não apresentar este ganho exploratório como prova de que três classes bastam em todo layout.

## Reprodução

```powershell
$env:PYTHONIOENCODING='utf-8'
venv\Scripts\python.exe -B orquestracao\analises\ordem_sem_bbox.py
```

Execução determinística; bootstrap com 5000 reamostras e semente 42. JSON contém hashes, configurações, métricas por página, ordens projetadas e sequências de linhas/átomos das variantes selecionadas. O Markdown é gerado diretamente desses resultados.
