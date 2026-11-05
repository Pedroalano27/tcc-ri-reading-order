1. Âncora reproduzida no golden_v4: τ 0,985948; 6,045455 quebras/página.
2. Fase 1 executada somente em golden_v4 e validação silver RN, com linhas + átomos ls3 e cobertura integral.
3. Segmentação e violações do ouro: golden_v4: 7,545 segmentos/página, 35 segmentos violados; validacao_silver: 5,800 segmentos/página, 19 segmentos violados.
4. HIER-1 retém 61,46% da redução do E004; Δτ vs híbrido 0,001914 [-0,006302; 0,015500] no ajuste.
5. Golden_v3_novo já foi consultado em rodadas anteriores; externas e teste cego não foram abertos nesta fase.
6. Veredito: NÃO GO da fase 1: o oráculo não passa; encerrar esta linha do grafo conforme o cartão.

# E016 — Oráculo hierárquico e HIER-1

## Execução e definições

CPU, quatro threads, um processo, num_workers=0, sem retreino. A regra é reexecutada antes de qualquer número novo. Entrada embaralhada pelo protocolo e conferida com random.Random(f'entrada-{page_id}'). Toda medição usa erros_ponta_a_ponta, bancada_ordenadores e avaliar_ordem do E002; não se reimplementam τ, quebras, fidelidade ou sucessor. Fontes e hashes estão no manifesto/estado. Saídas por página e escores calibrados permitem retomada após queda.

Segmentos: folhas terminais da recursão ordenar_projecao(local=True), observadas no retorno da própria função; cada faixa transversal que a regra detecta é singleton e já corta as colunas acima/abaixo. Topo, marca e rodapé são grupos separados pela partição geométrica original. Cada átomo tabela/imagem é singleton e corta sua folha em trechos anteriores/posteriores na ordem da regra. Não há limiar novo, título semântico, caixa humana nem referência na segmentação. A concatenação dos segmentos na ordem da regra reproduz exatamente a regra; nenhuma palavra/unidade é removida. Quando não há vale detectável, a folha conserva o fallback XY-cut da regra: não se inventa uma coluna.

HIER-1 filtra os candidatos K24 enriquecidos do E004 à mesma partição, conserva FIM e os escores Platt originais e chama o max-regret importado em cada segmento. Features e probabilidades são as da página inteira, antes de qualquer filtro. Segmentos seguem a regra. O grafo plano é reproduzido por página contra o cache congelado.

Oráculo hierárquico: ordem interna e entre segmentos com τ de palavras máximo, respeitando unidades/átomos e suas expansões canônicas. Componentes de intervalos-ouro sobrepostos são resolvidas exatamente por DP/MILP. Ouro que reentra num segmento ou unidade pode impedir τ=1: nenhuma partição ou átomo é desfeito. As quebras são medidas na mesma ordem, não combinadas com τ de outra predição. Oráculos parciais: interna perfeita + segmentos pela regra; interna pelo E004 local + segmentos perfeitos. Um controle adicional calcula o mínimo exato de quebras permitido pela partição via MILP esparso de adjacências-ouro, sem candidatos K. O objetivo provado é conferido com eventos() oficial na sequência reconstruída. Esse mínimo é um certificado para rejeitar a hierarquia se exceder o limite, mesmo quando outra ordem poderia ter τ maior. A ordem desse controle minimiza quebras; o desempate entre soluções não garante o maior τ.

IC95 percentil por veículo: 5000 reamostras, semente 20261004, funções importadas. Médias por página dentro de cada bancada. Ajuste conjunto = média de v4 e RN com peso igual, como E004/E014; IC conjunto = média das reamostras independentes das duas bancadas. Wilcoxon Pratt bilateral sobre as médias de Δ de cada veículo; p descritivo, sem seleção por p. RN tem um veículo, portanto seu IC degenera. As três bancadas oficiais permanecem separadas: somente golden_v4 é executada; golden_v3_novo e teste silver são externas não executadas. RN aparece separadamente como apêndice de ajuste. Sem somar páginas entre bancadas.

## Portão da fase 1

Critérios do cartão preservados: oráculo τ ≥ híbrido − 0,005; quebras ≤ 1,30 × teto plano E002 de cada bancada (o 1,05 do cartão é o arredondamento do valor exato salvo no v4); HIER-1 retém ≥70% da redução absoluta de quebras do E004 contra a regra, e limite inferior do IC95 de Δτ vs híbrido ≥−0,005 no ajuste. Relatam-se também resultados por bancada para expor heterogeneidade. Nenhuma externa é acionada pelo script.

| Condição | Resultado |
|---|---|
| oraculo_tau | PASSA |
| oraculo_quebras | FALHA |
| hier1_retencao | FALHA |
| hier1_tau_ic | FALHA |

| Bancada | Limite de quebras | Quebras na ordem de τ máximo | Mínimo de quebras provado |
|---|---:|---:|---:|
| golden_v4 | 1,359091 | 2,795455 | 2,136364 |
| validacao_silver | 8,233333 | 8,066667 | 6,466667 |

**NÃO GO da fase 1: o oráculo não passa; encerrar esta linha do grafo conforme o cartão.**

## golden_v4 — ajuste

44 páginas; 27 veículos. Segmentos por página: média 7,545, mínimo 2, máximo 36. Cobertura de unidades e palavras: 100,0% em todas as páginas.

Sucessores-ouro de linhas (pontas atribuídas por IDs de palavra): 4418/4685 dentro (94,30%); 267/4685 entre segmentos (5,70%). Segmentos violados: 35/332; visitas excedentes: 48; segmentos sem ouro: 64. Violado = mais de uma visita no fluxo de palavras-ouro; linhas humanas que atravessam segmentos podem ter suas pontas em partições diferentes.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,985948 | 6,045455 | 11,884752 | 0,948129 | 0,927240 |
| hibrido67 | 0,979738 | 5,136364 | 6,041242 | 0,973419 | 0,966143 |
| grafo_K24_maxregret_t0.00 | 0,937961 | 3,613636 | 7,777795 | 0,963953 | 0,955269 |
| oraculo_hierarquico | 0,993515 | 2,795455 | 5,851541 | 0,968074 | 0,966262 |
| oraculo_interna_segmentos_regra | 0,987386 | 3,250000 | 6,286449 | 0,966028 | 0,963442 |
| oraculo_segmentos_interna_grafo | 0,991574 | 4,250000 | 8,472574 | 0,959828 | 0,949203 |
| hier1 | 0,985445 | 4,659091 | 8,877056 | 0,957802 | 0,946650 |
| oraculo_hierarquico_quebras | 0,939802 | 2,136364 | 4,338262 | 0,969301 | 0,975874 |

### Qual nível limita

Substituições oraculares a partir do HIER-1, uma de cada vez. Δ = oráculo parcial − HIER-1; valor negativo de quebras indica potencial de reparo. As ordens maximizam τ, por isso não são limites independentes de quebras nem parcelas que possam ser somadas.

| Nível substituído pelo ouro | Δτ | Δ quebras/pág |
|---|---:|---:|
| interno; segmentos continuam pela regra | 0,001941 | -1,409091 |
| entre segmentos; interna continua pelo grafo | 0,006129 | -0,409091 |

Neste diagnóstico, a substituição interna oferece o maior reparo de quebras. Mesmo com ambos os níveis livres para escolher o mínimo de quebras, a partição falha no limite do cartão.


### Δ pareado, IC95 e Wilcoxon por veículo

M/I/P = páginas que melhoram/igualam/pioram, respeitando o sentido de cada métrica.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
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
| oraculo_hierarquico | regra | tau | 0,007567 [0,001428; 0,017525] | 0,000016 | 31/13/0 |
| oraculo_hierarquico | regra | quebras | -3,250000 [-4,428755; -2,186047] | 0,000022 | 30/14/0 |
| oraculo_hierarquico | regra | quebras_mil | -6,033210 [-9,854044; -2,849413] | 0,000022 | 30/14/0 |
| oraculo_hierarquico | regra | fid12 | 0,019945 [0,012971; 0,027715] | 0,000016 | 28/15/1 |
| oraculo_hierarquico | regra | sucessor_linhas | 0,039021 [0,021028; 0,061008] | 0,000022 | 30/14/0 |
| oraculo_hierarquico | hibrido67 | tau | 0,013777 [0,000307; 0,039083] | 0,002459 | 21/17/6 |
| oraculo_hierarquico | hibrido67 | quebras | -2,340909 [-3,820625; -0,979592] | 0,000755 | 22/16/6 |
| oraculo_hierarquico | hibrido67 | quebras_mil | -0,189701 [-4,103249; 5,427291] | 0,008352 | 22/16/6 |
| oraculo_hierarquico | hibrido67 | fid12 | -0,005345 [-0,045797; 0,019794] | 0,003675 | 21/17/6 |
| oraculo_hierarquico | hibrido67 | sucessor_linhas | 0,000119 [-0,035483; 0,024673] | 0,013673 | 22/16/6 |
| oraculo_interna_segmentos_regra | regra | tau | 0,001438 [0,000180; 0,003529] | 0,000030 | 29/15/0 |
| oraculo_interna_segmentos_regra | regra | quebras | -2,795455 [-3,727273; -1,902439] | 0,000044 | 28/16/0 |
| oraculo_interna_segmentos_regra | regra | quebras_mil | -5,598303 [-9,369738; -2,434035] | 0,000044 | 28/16/0 |
| oraculo_interna_segmentos_regra | regra | fid12 | 0,017899 [0,011366; 0,024898] | 0,000030 | 26/18/0 |
| oraculo_interna_segmentos_regra | regra | sucessor_linhas | 0,036202 [0,018079; 0,058586] | 0,000044 | 28/16/0 |
| oraculo_interna_segmentos_regra | hibrido67 | tau | 0,007649 [-0,008072; 0,033589] | 0,061975 | 19/18/7 |
| oraculo_interna_segmentos_regra | hibrido67 | quebras | -1,886364 [-3,075166; -0,720930] | 0,002054 | 21/17/6 |
| oraculo_interna_segmentos_regra | hibrido67 | quebras_mil | 0,245207 [-3,495836; 5,724915] | 0,010351 | 21/17/6 |
| oraculo_interna_segmentos_regra | hibrido67 | fid12 | -0,007391 [-0,047600; 0,016984] | 0,009783 | 20/18/6 |
| oraculo_interna_segmentos_regra | hibrido67 | sucessor_linhas | -0,002701 [-0,037624; 0,021479] | 0,020420 | 21/17/6 |
| oraculo_segmentos_interna_grafo | regra | tau | 0,005626 [-0,000137; 0,016005] | 0,028680 | 16/21/7 |
| oraculo_segmentos_interna_grafo | regra | quebras | -1,795455 [-2,800109; -0,930191] | 0,000411 | 19/24/1 |
| oraculo_segmentos_interna_grafo | regra | quebras_mil | -3,412178 [-6,738771; -1,110605] | 0,000523 | 19/24/1 |
| oraculo_segmentos_interna_grafo | regra | fid12 | 0,011700 [0,005840; 0,017928] | 0,000266 | 18/23/3 |
| oraculo_segmentos_interna_grafo | regra | sucessor_linhas | 0,021963 [0,006259; 0,044700] | 0,001490 | 19/23/2 |
| oraculo_segmentos_interna_grafo | hibrido67 | tau | 0,011836 [-0,003300; 0,038342] | 0,171809 | 15/14/15 |
| oraculo_segmentos_interna_grafo | hibrido67 | quebras | -0,886364 [-2,175000; 0,181818] | 0,130389 | 14/16/14 |
| oraculo_segmentos_interna_grafo | hibrido67 | quebras_mil | 2,431332 [-1,467686; 7,639491] | 0,932544 | 14/16/14 |
| oraculo_segmentos_interna_grafo | hibrido67 | fid12 | -0,013590 [-0,048473; 0,010267] | 0,707767 | 16/14/14 |
| oraculo_segmentos_interna_grafo | hibrido67 | sucessor_linhas | -0,016940 [-0,049805; 0,008398] | 0,762420 | 14/16/14 |
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
| oraculo_hierarquico_quebras | regra | tau | -0,046146 [-0,114025; 0,003149] | 0,360227 | 20/9/15 |
| oraculo_hierarquico_quebras | regra | quebras | -3,909091 [-5,441860; -2,642857] | 0,000012 | 33/11/0 |
| oraculo_hierarquico_quebras | regra | quebras_mil | -7,546489 [-12,563921; -3,581167] | 0,000012 | 33/11/0 |
| oraculo_hierarquico_quebras | regra | fid12 | 0,021173 [0,012928; 0,029842] | 0,000066 | 30/12/2 |
| oraculo_hierarquico_quebras | regra | sucessor_linhas | 0,048633 [0,025895; 0,079739] | 0,000012 | 33/11/0 |
| oraculo_hierarquico_quebras | hibrido67 | tau | -0,039935 [-0,108995; 0,016001] | 0,366895 | 14/15/15 |
| oraculo_hierarquico_quebras | hibrido67 | quebras | -3,000000 [-4,795000; -1,486979] | 0,000269 | 25/14/5 |
| oraculo_hierarquico_quebras | hibrido67 | quebras_mil | -1,702980 [-5,032430; 2,463695] | 0,002053 | 25/14/5 |
| oraculo_hierarquico_quebras | hibrido67 | fid12 | -0,004117 [-0,044956; 0,022421] | 0,004600 | 23/16/5 |
| oraculo_hierarquico_quebras | hibrido67 | sucessor_linhas | 0,009731 [-0,016230; 0,029663] | 0,002615 | 24/15/5 |

### Sucessores: reparos e regressões por classe

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| oraculo_hierarquico | regra | mesma_coluna | 34 | 1 |
| oraculo_hierarquico | regra | proxima_coluna | 1 | 1 |
| oraculo_hierarquico | regra | tabela_imagem | 3 | 0 |
| oraculo_hierarquico | regra | transversal | 8 | 1 |
| oraculo_hierarquico | regra | margem | 79 | 6 |
| oraculo_hierarquico | regra | outro | 19 | 0 |
| oraculo_hierarquico | hibrido67 | mesma_coluna | 28 | 1 |
| oraculo_hierarquico | hibrido67 | proxima_coluna | 1 | 1 |
| oraculo_hierarquico | hibrido67 | tabela_imagem | 13 | 0 |
| oraculo_hierarquico | hibrido67 | transversal | 8 | 1 |
| oraculo_hierarquico | hibrido67 | margem | 56 | 20 |
| oraculo_hierarquico | hibrido67 | outro | 10 | 0 |
| oraculo_interna_segmentos_regra | regra | mesma_coluna | 34 | 1 |
| oraculo_interna_segmentos_regra | regra | proxima_coluna | 0 | 1 |
| oraculo_interna_segmentos_regra | regra | tabela_imagem | 1 | 0 |
| oraculo_interna_segmentos_regra | regra | transversal | 0 | 1 |
| oraculo_interna_segmentos_regra | regra | margem | 69 | 5 |
| oraculo_interna_segmentos_regra | regra | outro | 19 | 0 |
| oraculo_interna_segmentos_regra | hibrido67 | mesma_coluna | 28 | 1 |
| oraculo_interna_segmentos_regra | hibrido67 | proxima_coluna | 0 | 1 |
| oraculo_interna_segmentos_regra | hibrido67 | tabela_imagem | 12 | 1 |
| oraculo_interna_segmentos_regra | hibrido67 | transversal | 0 | 1 |
| oraculo_interna_segmentos_regra | hibrido67 | margem | 48 | 21 |
| oraculo_interna_segmentos_regra | hibrido67 | outro | 10 | 0 |
| oraculo_segmentos_interna_grafo | regra | mesma_coluna | 21 | 0 |
| oraculo_segmentos_interna_grafo | regra | proxima_coluna | 1 | 0 |
| oraculo_segmentos_interna_grafo | regra | tabela_imagem | 2 | 2 |
| oraculo_segmentos_interna_grafo | regra | transversal | 8 | 0 |
| oraculo_segmentos_interna_grafo | regra | margem | 35 | 4 |
| oraculo_segmentos_interna_grafo | regra | outro | 16 | 1 |
| oraculo_segmentos_interna_grafo | hibrido67 | mesma_coluna | 18 | 3 |
| oraculo_segmentos_interna_grafo | hibrido67 | proxima_coluna | 1 | 0 |
| oraculo_segmentos_interna_grafo | hibrido67 | tabela_imagem | 12 | 2 |
| oraculo_segmentos_interna_grafo | hibrido67 | transversal | 8 | 0 |
| oraculo_segmentos_interna_grafo | hibrido67 | margem | 29 | 35 |
| oraculo_segmentos_interna_grafo | hibrido67 | outro | 9 | 3 |
| hier1 | regra | mesma_coluna | 21 | 0 |
| hier1 | regra | proxima_coluna | 0 | 0 |
| hier1 | regra | tabela_imagem | 0 | 2 |
| hier1 | regra | transversal | 1 | 0 |
| hier1 | regra | margem | 26 | 3 |
| hier1 | regra | outro | 16 | 1 |
| hier1 | hibrido67 | mesma_coluna | 18 | 3 |
| hier1 | hibrido67 | proxima_coluna | 0 | 0 |
| hier1 | hibrido67 | tabela_imagem | 11 | 3 |
| hier1 | hibrido67 | transversal | 1 | 0 |
| hier1 | hibrido67 | margem | 22 | 36 |
| hier1 | hibrido67 | outro | 9 | 3 |
| oraculo_hierarquico_quebras | regra | mesma_coluna | 39 | 2 |
| oraculo_hierarquico_quebras | regra | proxima_coluna | 1 | 1 |
| oraculo_hierarquico_quebras | regra | tabela_imagem | 4 | 0 |
| oraculo_hierarquico_quebras | regra | transversal | 12 | 1 |
| oraculo_hierarquico_quebras | regra | margem | 94 | 4 |
| oraculo_hierarquico_quebras | regra | outro | 22 | 1 |
| oraculo_hierarquico_quebras | hibrido67 | mesma_coluna | 33 | 2 |
| oraculo_hierarquico_quebras | hibrido67 | proxima_coluna | 1 | 1 |
| oraculo_hierarquico_quebras | hibrido67 | tabela_imagem | 14 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | transversal | 12 | 1 |
| oraculo_hierarquico_quebras | hibrido67 | margem | 65 | 12 |
| oraculo_hierarquico_quebras | hibrido67 | outro | 13 | 1 |

### Corpo sem margens — diagnóstico

Mesma exclusão automática para todos os métodos, importada do E014; sem seleção.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,993467 | 2,931818 | 0,985674 | 0,977845 |
| hibrido67 | 0,986295 | 2,772727 | 0,988822 | 0,985116 |
| grafo_K24_maxregret_t0.00 | 0,940957 | 1,568182 | 0,990664 | 0,985138 |
| oraculo_hierarquico | 0,998669 | 1,318182 | 0,994728 | 0,992808 |
| oraculo_interna_segmentos_regra | 0,993538 | 1,568182 | 0,994058 | 0,991675 |
| oraculo_segmentos_interna_grafo | 0,998267 | 1,818182 | 0,991537 | 0,985832 |
| hier1 | 0,993136 | 2,045455 | 0,990866 | 0,984768 |
| oraculo_hierarquico_quebras | 0,950607 | 1,181818 | 0,993095 | 0,990331 |

### HIER-1: diferenças por veículo

| Veículo | Δτ vs regra | Δ quebras vs regra | Δτ vs híbrido | Δ quebras vs híbrido |
|---|---:|---:|---:|---:|
| official_diary_MG_congonhas | -0,006819 | 0,000000 | -0,007304 | 2,500000 |
| official_diary_RJ_barra_do_pirai | -0,003555 | -2,666667 | -0,033763 | 3,000000 |
| official_diary_RJ_duque_de_caxias | 0,000051 | -3,000000 | -0,067958 | -2,500000 |
| official_diary_RJ_seropedica | -0,000468 | 0,000000 | -0,000769 | 0,500000 |
| official_diary_RJ_volta_redonda | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ac | 0,000238 | -1,000000 | 0,000181 | 0,000000 |
| official_diary_al | 0,000000 | 0,000000 | 0,016007 | 0,666667 |
| official_diary_am_manaus | 0,000000 | 0,000000 | 0,008900 | -3,000000 |
| official_diary_ap | -0,000071 | 1,000000 | -0,000071 | 1,000000 |
| official_diary_ba_salvador | -0,000041 | 2,000000 | 0,447940 | -4,000000 |
| official_diary_ce | 0,000000 | 0,000000 | -0,000061 | 2,000000 |
| official_diary_ma | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_mg | 0,000010 | -9,000000 | 0,000010 | -9,000000 |
| official_diary_ms | 0,000568 | -1,000000 | 0,000000 | 0,000000 |
| official_diary_pb | 0,000615 | -4,000000 | 0,000607 | -4,500000 |
| official_diary_pe | 0,000002 | -3,000000 | 0,000002 | -3,000000 |
| official_diary_pi_v2 | 0,000000 | 0,000000 | -0,000581 | 2,000000 |
| official_diary_pr_curitiba | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_rj | -0,000001 | -7,000000 | -0,000001 | -7,000000 |
| official_diary_rj_japeri | -0,000026 | -4,000000 | -0,003163 | -3,000000 |
| official_diary_rn | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| official_diary_ro | 0,000159 | -3,000000 | -0,000079 | 1,500000 |
| official_diary_rr | 0,000000 | 0,000000 | -0,000328 | 2,000000 |
| official_diary_rs_porto_alegre | 0,000100 | -1,500000 | 0,003174 | -1,000000 |
| official_diary_sc | 0,000006 | -3,000000 | 0,000006 | -3,000000 |
| official_diary_se | -0,000070 | 0,000000 | -0,000070 | 0,000000 |
| official_diary_to | 0,000000 | 0,000000 | 0,000000 | 0,000000 |

### Segmentação por página

| Página | Segmentos | Cobertura | Ouro linhas dentro/entre | Segmentos violados | Mínimo quebras |
|---|---:|---:|---:|---:|---:|
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | 4 | 100,0% | 53/2 | 0 | 0 |
| `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20` | 3 | 100,0% | 14/1 | 0 | 0 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 10 | 100,0% | 6/5 | 1 | 2 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3` | 6 | 100,0% | 29/4 | 1 | 2 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2` | 8 | 100,0% | 5/5 | 1 | 2 |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | 10 | 100,0% | 139/10 | 2 | 4 |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` | 8 | 100,0% | 116/5 | 0 | 0 |
| `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 36 | 100,0% | 50/36 | 1 | 7 |
| `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p3` | 9 | 100,0% | 29/5 | 3 | 7 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` | 6 | 100,0% | 106/3 | 1 | 2 |
| `official_diary_ac/executive_official_diary_2022-08-03.pdf#p109` | 3 | 100,0% | 84/2 | 0 | 0 |
| `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114` | 4 | 100,0% | 138/5 | 2 | 2 |
| `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | 4 | 100,0% | 71/2 | 0 | 1 |
| `official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf#p0` | 3 | 100,0% | 146/2 | 0 | 0 |
| `official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf#p9` | 4 | 100,0% | 108/3 | 0 | 0 |
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 6 | 100,0% | 212/5 | 0 | 0 |
| `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35` | 6 | 100,0% | 106/7 | 3 | 4 |
| `official_diary_ap/2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373` | 3 | 100,0% | 50/2 | 0 | 0 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` | 15 | 100,0% | 135/13 | 0 | 7 |
| `official_diary_ce/do20220530p02.pdf#p53` | 6 | 100,0% | 67/4 | 0 | 1 |
| `official_diary_ma/executive_official_diary_2023-03-06.pdf#p71` | 6 | 100,0% | 101/4 | 0 | 0 |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | 7 | 100,0% | 483/7 | 3 | 4 |
| `official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48` | 5 | 100,0% | 114/2 | 0 | 0 |
| `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 4 | 100,0% | 67/1 | 0 | 0 |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | 13 | 100,0% | 143/11 | 0 | 0 |
| `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | 5 | 100,0% | 135/5 | 2 | 2 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | 11 | 100,0% | 207/4 | 0 | 0 |
| `official_diary_pi_v2/executive_official_diary_2024_01_12_9_2024_243_297.pdf#p0` | 6 | 100,0% | 27/4 | 1 | 2 |
| `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p2` | 6 | 100,0% | 34/4 | 1 | 2 |
| `official_diary_pr_curitiba/24-Supl1_2024-02-05.pdf#p4` | 5 | 100,0% | 13/2 | 0 | 0 |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 27 | 100,0% | 304/34 | 7 | 25 |
| `official_diary_rj_japeri/JAPERI-5606-09-DE-MAIO-2024.pdf#p3` | 2 | 100,0% | 13/1 | 0 | 0 |
| `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13` | 10 | 100,0% | 102/8 | 1 | 2 |
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p59` | 4 | 100,0% | 80/2 | 0 | 1 |
| `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0` | 3 | 100,0% | 55/2 | 0 | 0 |
| `official_diary_ro/executive_official_diary_suplemento_2026-01-09.pdf#p16` | 4 | 100,0% | 54/2 | 0 | 0 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p10` | 16 | 100,0% | 58/12 | 0 | 0 |
| `official_diary_rs_porto_alegre/4689_cl_20230227_legislativo.pdf#p1` | 3 | 100,0% | 45/2 | 0 | 0 |
| `official_diary_rs_porto_alegre/4689_cl_20230227_legislativo.pdf#p2` | 3 | 100,0% | 12/2 | 0 | 0 |
| `official_diary_sc/2023-11-27_22151.pdf#p28` | 4 | 100,0% | 251/3 | 0 | 0 |
| `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | 8 | 100,0% | 77/13 | 2 | 9 |
| `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31` | 12 | 100,0% | 107/7 | 1 | 2 |
| `official_diary_to/2022-12-13_4783.pdf#p10` | 11 | 100,0% | 139/11 | 1 | 2 |
| `official_diary_to/2024-04-17_5147.pdf#p47` | 3 | 100,0% | 133/3 | 1 | 2 |

## validacao_silver — ajuste

15 páginas; 1 veículos. Segmentos por página: média 5,800, mínimo 3, máximo 13. Cobertura de unidades e palavras: 100,0% em todas as páginas.

Sucessores-ouro de linhas (pontas atribuídas por IDs de palavra): 4909/5012 dentro (97,94%); 103/5012 entre segmentos (2,06%). Segmentos violados: 19/87; visitas excedentes: 34; segmentos sem ouro: 3. Violado = mais de uma visita no fluxo de palavras-ouro; linhas humanas que atravessam segmentos podem ter suas pontas em partições diferentes.

| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| regra | 0,957218 | 16,666667 | 10,284740 | 0,952328 | 0,910859 |
| hibrido67 | 0,958656 | 16,400000 | 9,585398 | 0,957104 | 0,916949 |
| grafo_K24_maxregret_t0.00 | 0,686666 | 9,466667 | 6,131847 | 0,970249 | 0,947916 |
| oraculo_hierarquico | 0,980481 | 8,066667 | 4,859146 | 0,972592 | 0,959217 |
| oraculo_interna_segmentos_regra | 0,957982 | 8,666667 | 5,190396 | 0,969685 | 0,956265 |
| oraculo_segmentos_interna_grafo | 0,979276 | 11,533333 | 7,293900 | 0,964235 | 0,937836 |
| hier1 | 0,956778 | 12,133333 | 7,622965 | 0,961153 | 0,934895 |
| oraculo_hierarquico_quebras | 0,763372 | 6,466667 | 3,707049 | 0,979472 | 0,969079 |

### Qual nível limita

Substituições oraculares a partir do HIER-1, uma de cada vez. Δ = oráculo parcial − HIER-1; valor negativo de quebras indica potencial de reparo. As ordens maximizam τ, por isso não são limites independentes de quebras nem parcelas que possam ser somadas.

| Nível substituído pelo ouro | Δτ | Δ quebras/pág |
|---|---:|---:|
| interno; segmentos continuam pela regra | 0,001205 | -3,466667 |
| entre segmentos; interna continua pelo grafo | 0,022498 | -0,600000 |

Neste diagnóstico, a substituição interna oferece o maior reparo de quebras. O mínimo de quebras desta bancada cabe no limite; isso sozinho não certifica a condição conjunta de τ e quebras.


### Δ pareado, IC95 e Wilcoxon por veículo

M/I/P = páginas que melhoram/igualam/pioram, respeitando o sentido de cada métrica.

| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |
|---|---|---|---:|---:|---:|
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
| oraculo_hierarquico | regra | tau | 0,023263 [0,023263; 0,023263] | 0,317311 | 10/5/0 |
| oraculo_hierarquico | regra | quebras | -8,600000 [-8,600000; -8,600000] | 0,317311 | 10/5/0 |
| oraculo_hierarquico | regra | quebras_mil | -5,425594 [-5,425594; -5,425594] | 0,317311 | 10/5/0 |
| oraculo_hierarquico | regra | fid12 | 0,020264 [0,020264; 0,020264] | 0,317311 | 10/5/0 |
| oraculo_hierarquico | regra | sucessor_linhas | 0,048358 [0,048358; 0,048358] | 0,317311 | 10/5/0 |
| oraculo_hierarquico | hibrido67 | tau | 0,021824 [0,021824; 0,021824] | 0,317311 | 10/4/1 |
| oraculo_hierarquico | hibrido67 | quebras | -8,333333 [-8,333333; -8,333333] | 0,317311 | 10/4/1 |
| oraculo_hierarquico | hibrido67 | quebras_mil | -4,726252 [-4,726252; -4,726252] | 0,317311 | 10/4/1 |
| oraculo_hierarquico | hibrido67 | fid12 | 0,015488 [0,015488; 0,015488] | 0,317311 | 9/4/2 |
| oraculo_hierarquico | hibrido67 | sucessor_linhas | 0,042268 [0,042268; 0,042268] | 0,317311 | 10/4/1 |
| oraculo_interna_segmentos_regra | regra | tau | 0,000765 [0,000765; 0,000765] | 0,317311 | 10/5/0 |
| oraculo_interna_segmentos_regra | regra | quebras | -8,000000 [-8,000000; -8,000000] | 0,317311 | 10/5/0 |
| oraculo_interna_segmentos_regra | regra | quebras_mil | -5,094344 [-5,094344; -5,094344] | 0,317311 | 10/5/0 |
| oraculo_interna_segmentos_regra | regra | fid12 | 0,017357 [0,017357; 0,017357] | 0,317311 | 10/5/0 |
| oraculo_interna_segmentos_regra | regra | sucessor_linhas | 0,045406 [0,045406; 0,045406] | 0,317311 | 10/5/0 |
| oraculo_interna_segmentos_regra | hibrido67 | tau | -0,000674 [-0,000674; -0,000674] | 0,317311 | 10/4/1 |
| oraculo_interna_segmentos_regra | hibrido67 | quebras | -7,733333 [-7,733333; -7,733333] | 0,317311 | 10/4/1 |
| oraculo_interna_segmentos_regra | hibrido67 | quebras_mil | -4,395002 [-4,395002; -4,395002] | 0,317311 | 10/4/1 |
| oraculo_interna_segmentos_regra | hibrido67 | fid12 | 0,012581 [0,012581; 0,012581] | 0,317311 | 9/4/2 |
| oraculo_interna_segmentos_regra | hibrido67 | sucessor_linhas | 0,039316 [0,039316; 0,039316] | 0,317311 | 10/4/1 |
| oraculo_segmentos_interna_grafo | regra | tau | 0,022058 [0,022058; 0,022058] | 0,317311 | 7/5/3 |
| oraculo_segmentos_interna_grafo | regra | quebras | -5,133333 [-5,133333; -5,133333] | 0,317311 | 8/6/1 |
| oraculo_segmentos_interna_grafo | regra | quebras_mil | -2,990840 [-2,990840; -2,990840] | 0,317311 | 8/6/1 |
| oraculo_segmentos_interna_grafo | regra | fid12 | 0,011907 [0,011907; 0,011907] | 0,317311 | 8/5/2 |
| oraculo_segmentos_interna_grafo | regra | sucessor_linhas | 0,026977 [0,026977; 0,026977] | 0,317311 | 8/6/1 |
| oraculo_segmentos_interna_grafo | hibrido67 | tau | 0,020620 [0,020620; 0,020620] | 0,317311 | 8/4/3 |
| oraculo_segmentos_interna_grafo | hibrido67 | quebras | -4,866667 [-4,866667; -4,866667] | 0,317311 | 7/5/3 |
| oraculo_segmentos_interna_grafo | hibrido67 | quebras_mil | -2,291498 [-2,291498; -2,291498] | 0,317311 | 7/5/3 |
| oraculo_segmentos_interna_grafo | hibrido67 | fid12 | 0,007131 [0,007131; 0,007131] | 0,317311 | 7/4/4 |
| oraculo_segmentos_interna_grafo | hibrido67 | sucessor_linhas | 0,020887 [0,020887; 0,020887] | 0,317311 | 7/5/3 |
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
| oraculo_hierarquico_quebras | regra | tau | -0,193846 [-0,193846; -0,193846] | 0,317311 | 2/4/9 |
| oraculo_hierarquico_quebras | regra | quebras | -10,200000 [-10,200000; -10,200000] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | regra | quebras_mil | -6,577690 [-6,577690; -6,577690] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | regra | fid12 | 0,027144 [0,027144; 0,027144] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | regra | sucessor_linhas | 0,058220 [0,058220; 0,058220] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | hibrido67 | tau | -0,195284 [-0,195284; -0,195284] | 0,317311 | 2/4/9 |
| oraculo_hierarquico_quebras | hibrido67 | quebras | -9,933333 [-9,933333; -9,933333] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | hibrido67 | quebras_mil | -5,878349 [-5,878349; -5,878349] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | hibrido67 | fid12 | 0,022367 [0,022367; 0,022367] | 0,317311 | 11/4/0 |
| oraculo_hierarquico_quebras | hibrido67 | sucessor_linhas | 0,052130 [0,052130; 0,052130] | 0,317311 | 11/4/0 |

### Sucessores: reparos e regressões por classe

| Método | Base | Classe | Reparos | Regressões |
|---|---|---|---:|---:|
| oraculo_hierarquico | regra | mesma_coluna | 19 | 0 |
| oraculo_hierarquico | regra | proxima_coluna | 0 | 1 |
| oraculo_hierarquico | regra | tabela_imagem | 1 | 0 |
| oraculo_hierarquico | regra | transversal | 6 | 1 |
| oraculo_hierarquico | regra | margem | 31 | 2 |
| oraculo_hierarquico | regra | outro | 76 | 0 |
| oraculo_hierarquico | hibrido67 | mesma_coluna | 19 | 0 |
| oraculo_hierarquico | hibrido67 | proxima_coluna | 0 | 1 |
| oraculo_hierarquico | hibrido67 | tabela_imagem | 1 | 0 |
| oraculo_hierarquico | hibrido67 | transversal | 6 | 1 |
| oraculo_hierarquico | hibrido67 | margem | 31 | 6 |
| oraculo_hierarquico | hibrido67 | outro | 76 | 0 |
| oraculo_interna_segmentos_regra | regra | mesma_coluna | 18 | 0 |
| oraculo_interna_segmentos_regra | regra | proxima_coluna | 0 | 1 |
| oraculo_interna_segmentos_regra | regra | tabela_imagem | 0 | 0 |
| oraculo_interna_segmentos_regra | regra | transversal | 0 | 0 |
| oraculo_interna_segmentos_regra | regra | margem | 29 | 2 |
| oraculo_interna_segmentos_regra | regra | outro | 76 | 0 |
| oraculo_interna_segmentos_regra | hibrido67 | mesma_coluna | 18 | 0 |
| oraculo_interna_segmentos_regra | hibrido67 | proxima_coluna | 0 | 1 |
| oraculo_interna_segmentos_regra | hibrido67 | tabela_imagem | 0 | 0 |
| oraculo_interna_segmentos_regra | hibrido67 | transversal | 0 | 0 |
| oraculo_interna_segmentos_regra | hibrido67 | margem | 29 | 6 |
| oraculo_interna_segmentos_regra | hibrido67 | outro | 76 | 0 |
| oraculo_segmentos_interna_grafo | regra | mesma_coluna | 15 | 0 |
| oraculo_segmentos_interna_grafo | regra | proxima_coluna | 0 | 1 |
| oraculo_segmentos_interna_grafo | regra | tabela_imagem | 1 | 0 |
| oraculo_segmentos_interna_grafo | regra | transversal | 6 | 1 |
| oraculo_segmentos_interna_grafo | regra | margem | 7 | 2 |
| oraculo_segmentos_interna_grafo | regra | outro | 53 | 1 |
| oraculo_segmentos_interna_grafo | hibrido67 | mesma_coluna | 15 | 0 |
| oraculo_segmentos_interna_grafo | hibrido67 | proxima_coluna | 0 | 1 |
| oraculo_segmentos_interna_grafo | hibrido67 | tabela_imagem | 1 | 0 |
| oraculo_segmentos_interna_grafo | hibrido67 | transversal | 6 | 1 |
| oraculo_segmentos_interna_grafo | hibrido67 | margem | 6 | 5 |
| oraculo_segmentos_interna_grafo | hibrido67 | outro | 53 | 1 |
| hier1 | regra | mesma_coluna | 14 | 0 |
| hier1 | regra | proxima_coluna | 0 | 1 |
| hier1 | regra | tabela_imagem | 0 | 0 |
| hier1 | regra | transversal | 0 | 0 |
| hier1 | regra | margem | 4 | 1 |
| hier1 | regra | outro | 53 | 1 |
| hier1 | hibrido67 | mesma_coluna | 14 | 0 |
| hier1 | hibrido67 | proxima_coluna | 0 | 1 |
| hier1 | hibrido67 | tabela_imagem | 0 | 0 |
| hier1 | hibrido67 | transversal | 0 | 0 |
| hier1 | hibrido67 | margem | 3 | 4 |
| hier1 | hibrido67 | outro | 53 | 1 |
| oraculo_hierarquico_quebras | regra | mesma_coluna | 20 | 0 |
| oraculo_hierarquico_quebras | regra | proxima_coluna | 0 | 0 |
| oraculo_hierarquico_quebras | regra | tabela_imagem | 2 | 0 |
| oraculo_hierarquico_quebras | regra | transversal | 6 | 0 |
| oraculo_hierarquico_quebras | regra | margem | 51 | 2 |
| oraculo_hierarquico_quebras | regra | outro | 76 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | mesma_coluna | 20 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | proxima_coluna | 0 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | tabela_imagem | 2 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | transversal | 6 | 0 |
| oraculo_hierarquico_quebras | hibrido67 | margem | 49 | 4 |
| oraculo_hierarquico_quebras | hibrido67 | outro | 76 | 0 |

### Corpo sem margens — diagnóstico

Mesma exclusão automática para todos os métodos, importada do E014; sem seleção.

| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|
| regra | 0,977603 | 11,200000 | 0,972619 | 0,945747 |
| hibrido67 | 0,977564 | 11,200000 | 0,972619 | 0,945747 |
| grafo_K24_maxregret_t0.00 | 0,684942 | 6,933333 | 0,977618 | 0,965229 |
| oraculo_hierarquico | 0,999175 | 4,400000 | 0,989993 | 0,980455 |
| oraculo_interna_segmentos_regra | 0,977822 | 5,000000 | 0,986776 | 0,977338 |
| oraculo_segmentos_interna_grafo | 0,998588 | 6,333333 | 0,983104 | 0,970458 |
| hier1 | 0,977235 | 6,933333 | 0,979887 | 0,967341 |
| oraculo_hierarquico_quebras | 0,779733 | 4,466667 | 0,986694 | 0,977429 |

### HIER-1: diferenças por veículo

| Veículo | Δτ vs regra | Δ quebras vs regra | Δτ vs híbrido | Δ quebras vs híbrido |
|---|---:|---:|---:|---:|
| official_diary_rn | -0,000440 | -4,533333 | -0,001879 | -4,266667 |

### Segmentação por página

| Página | Segmentos | Cobertura | Ouro linhas dentro/entre | Segmentos violados | Mínimo quebras |
|---|---:|---:|---:|---:|---:|
| `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1` | 13 | 100,0% | 170/16 | 3 | 7 |
| `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13` | 8 | 100,0% | 187/10 | 2 | 18 |
| `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17` | 5 | 100,0% | 276/9 | 2 | 6 |
| `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2` | 5 | 100,0% | 289/9 | 2 | 6 |
| `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39` | 5 | 100,0% | 276/9 | 2 | 6 |
| `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46` | 4 | 100,0% | 29/4 | 1 | 2 |
| `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11` | 4 | 100,0% | 196/6 | 2 | 3 |
| `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24` | 8 | 100,0% | 217/10 | 2 | 12 |
| `official_diary_rn/DOE-RN_2022-11-23_Ordinaria.pdf#p30` | 3 | 100,0% | 175/2 | 0 | 0 |
| `official_diary_rn/DOE-RN_2022-11-23_Ordinaria.pdf#p5` | 9 | 100,0% | 168/8 | 0 | 0 |
| `official_diary_rn/DOE-RN_2022-11-23_Ordinaria.pdf#p51` | 6 | 100,0% | 201/5 | 0 | 27 |
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3` | 3 | 100,0% | 204/3 | 1 | 2 |
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40` | 5 | 100,0% | 2263/6 | 2 | 8 |
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p59` | 4 | 100,0% | 78/2 | 0 | 0 |
| `official_diary_rn/DOE-RN_2023-08-02_Ordinaria_33_52.pdf#p0` | 5 | 100,0% | 180/4 | 0 | 0 |

## Bancadas externas

golden_v3_novo: NÃO EXECUTADA. teste silver CE/MA/RJ: NÃO EXECUTADO. Nenhum arquivo dessas bancadas foi aberto ou avaliado nesta fase. Teste cego preservado.

## Limitações

Estudo exploratório, um anotador humano, silver ruidoso e poucos veículos. Golden_v3_novo já foi consultado em rodadas anteriores e não é confirmatório. RN tem só um veículo; IC degenerado não representa incerteza entre veículos novos. Fronteiras são as da regra, não fronteiras semânticas de atos. Título só provoca corte quando reconhecido geometricamente como faixa transversal. Violações não demonstram erro humano: a hierarquia e as unidades automáticas podem ser incompatíveis com o ouro. Não se confundem mínimo de quebras e máximo de τ de ordens diferentes; a decisão inclui certificado de inviabilidade quando o mínimo de quebras já excede o limite. Ganho local sem segurança de τ não autoriza fase 2. Nenhuma anotação, dado, cartão, documentação, registro compartilhado ou modelo foi alterado.
