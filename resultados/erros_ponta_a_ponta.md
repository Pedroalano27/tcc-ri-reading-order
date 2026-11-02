# Erros de ponta a ponta: automático contra automático

## Resumo em cinco linhas

1. P1: 19,7% das quebras são associadas às caixas pela regra operacional [IC 95% 2,1%; 35,1%]; P1m: 31,8%. A hipótese de que a maioria das quebras nasce nas caixas não é sustentada nesta régua.
2. Quebras por página: P0 = 85,46; P1 = 16,14; P1m = 9,87; P2 = 7,25; P2d = 10,99.
3. P2 reduz a média observada de quebras contra P1 em 55,1% (Δ=-8,89 [-13,13; -4,89] por página) e contra P1m em 26,5% (Δ=-2,62 [-5,77; 0,18]); o IC contra P1m inclui ausência de melhora.
4. Fidelidade integral de 12 palavras: P1 87,5%; P1m 92,3%; P2 94,1%; Pratt por veículo P2−P1m, quebras: p=0,913017.
5. São 71 páginas de 27 veículos; analisar v4 e v3 novo separadamente. A comparação mede reordenação do texto digital disponível, com referência interna derivada e viés de ancoragem.

## Protocolo e entradas

P0: palavras ordenadas por (top, x0, índice), sem detector. P1: `propor(regras=True)` atual, com palavras e blocos v3 automáticos, cache automático Docling e XY-cut. P1m: as mesmas caixas, com `src/eval/politica_margens.py:xycut_margens`, variante geométrica recomendada (recorte do corpo). P2: somente átomos tabela/imagem do ls3; caixas texto do detector são ignoradas. P2d: mesmo algoritmo, átomos Docling. Nenhum pipeline recebe caixas, classes ou ordem humanas: `automatico()` limita expressamente o contrato de entrada.

Configuração única congelada, sem seleção nesta execução: `projecao_local_margens_s0.45_g1.2_v0.08`; é a escolhida pelo ls3 em todas as páginas da análise anterior. Docling usa exatamente esses parâmetros, sem escolher a exceção LOPO anterior. Detector ls3: best.pt, CPU, imgsz=1024, conf=0,25, IoU NMS=0,7, max_det=300; átomos retidos com confiança ≥ 0,45. Topo: centro < 7% e base < 10%; rodapé: centro > 95%; saída topo→corpo→marcas→rodapé. Peso SHA-256: `c3b7cff2f6e6c0eb7d1166b178cb14b58979f27e2ec39bcd5c1bddb8d88ca85e`.

V4 reutiliza palavras, associação aos blocos v3 e detector **anteriores à correção humana**, congelados nas tarefas Diamond; `propor` é executado agora. V3 novo reutiliza palavras extraídas do PDF pelo script de validação do acervo e reconstrói `segmentar()` com tabelas Docling; não reaproveita regiões de referência como entrada. Imagens dos lotes originais servem ao ls3. As dimensões são auditadas; não há OCR, rede ou abertura de exports Label Studio. As palavras fora das regiões-ouro permanecem na saída. Ouro: ordem humana cega de regiões, com `linhas()` dentro de cada região. A palavra tem identidade por índice de extração, evitando casamento por conteúdo repetido para τ.

Amostra solicitada: 44 páginas concluídas do v4 e 27 do v3 fora de **todas** as tarefas v4 (incluindo a pulada). Total de palavras disponíveis=59998; com referência=59949; sem referência=49. Não há exclusões nesta execução.

## Definições operacionais no texto final

- **τ de palavras:** permutação dos IDs com referência na sequência efetivamente emitida; palavras sem referência não têm posto-ouro. Não há projeção por mediana.
- **Sucessor correto de linhas:** fração dos pares de linhas consecutivas do ouro que aparecem intactos e diretamente adjacentes na saída completa. Ambas as linhas precisam preservar todos os IDs em ordem. Uma linha intercalada não recebe crédito pelo seu posto mediano.
- **Fidelidade integral 6/12/24:** todas as janelas consecutivas dos tokens-ouro, incluindo fronteiras de linhas e regiões, procuradas no texto final normalizado por `piloto_japeri.tokens`. Reutiliza literalmente `preservada()` com `MIN_ALINHADAS=k` em namespace isolado; exige k/k, sem mudar o módulo. Confere cada contagem por conjuntos de n-gramas. Também guarda o controle original tolerante 10/12 do piloto. Repetições lexicais podem preservar uma frase em outra posição: esse é o comportamento de busca textual solicitado, distinto da régua de IDs da prévia. Não são necessariamente frases sintáticas.
- **Quebra de continuidade:** transição entre palavras sucessivas com referência na saída que não é o sucessor-ouro, ou cujo espaço foi interrompido por palavras sem referência. Cada transição conta uma vez; um salto de coluna não vira centenas de inversões. Não conta início/fim nem inventa ordem para palavras não anotadas. A contagem projetada sem livres também fica no JSON para conferir a prévia.
- **Trecho intercalado:** retorno a uma região-ouro já visitada depois de outra região (A→B→A): cada retorno conta um evento; uma região com três visitas conta dois. Não confunde bloco inteiro fora de ordem com intercalação. O JSON guarda também quantas regiões foram afetadas.
- **Bloco deslocado:** região-ouro com texto cujo posto de **primeira aparição** na saída difere em mais de N=3 postos do ouro. Não usa caixas humanas para prever, nem mediana para apagar intercalamento. Sensibilidade com N=5 também é reportada. É uma régua adicional, com efeito cascata de posições; não soma com quebras/intercalações para formar um total arbitrário.

## Tabela principal: todas as páginas

| Pipeline | τ palavras ↑ | Sucessor de linhas ↑ | Quebras: total / página ↓ | Fid. 6 ↑ | Fid. 12 ↑ | Fid. 24 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| P0 | 0,759 [0,666; 0,846] | 50,8% [37,2%; 64,4%] | 6068 / 85,46 [50,86; 127,69] | 73,7% [64,9%; 82,0%] | 56,2% [42,9%; 69,1%] | 46,6% [31,5%; 61,5%] |
| P1 | 0,830 [0,750; 0,907] | 85,7% [81,9%; 89,4%] | 1146 / 16,14 [10,26; 21,82] | 93,0% [90,4%; 95,4%] | 87,5% [83,6%; 91,3%] | 79,8% [73,5%; 85,9%] |
| P1m | 0,947 [0,900; 0,984] | 91,2% [88,2%; 94,0%] | 701 / 9,87 [5,15; 14,89] | 95,1% [92,9%; 97,4%] | 92,3% [88,9%; 95,6%] | 88,5% [82,9%; 93,6%] |
| P2 | 0,976 [0,956; 0,992] | 92,1% [88,9%; 94,6%] | 515 / 7,25 [4,76; 9,88] | 95,9% [93,8%; 97,7%] | 94,1% [91,6%; 96,4%] | 91,8% [88,5%; 94,9%] |
| P2d | 0,977 [0,961; 0,991] | 89,9% [85,6%; 93,4%] | 780 / 10,99 [5,93; 16,82] | 94,2% [91,0%; 97,1%] | 92,2% [88,3%; 95,6%] | 90,1% [85,7%; 94,1%] |

### V4 — desenvolvimento

n=44; veículos=27.

| Pipeline | τ palavras ↑ | Sucessor de linhas ↑ | Quebras: total / página ↓ | Fid. 6 ↑ | Fid. 12 ↑ | Fid. 24 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| P0 | 0,726 [0,630; 0,816] | 47,8% [34,8%; 60,6%] | 3759 / 85,43 [56,78; 122,95] | 72,2% [63,8%; 79,7%] | 52,4% [39,6%; 64,5%] | 42,8% [28,1%; 56,9%] |
| P1 | 0,819 [0,737; 0,895] | 85,7% [81,6%; 89,7%] | 716 / 16,27 [10,17; 23,77] | 93,2% [90,4%; 95,6%] | 87,2% [82,4%; 91,6%] | 78,8% [71,1%; 86,0%] |
| P1m | 0,952 [0,906; 0,984] | 91,7% [87,6%; 95,3%] | 393 / 8,93 [3,93; 15,79] | 95,7% [92,9%; 98,0%] | 92,6% [88,4%; 96,4%] | 88,6% [81,6%; 94,6%] |
| P2 | 0,986 [0,974; 0,995] | 92,7% [87,8%; 96,0%] | 266 / 6,05 [4,09; 8,91] | 96,4% [93,3%; 98,3%] | 94,8% [91,3%; 97,2%] | 92,9% [88,4%; 96,1%] |
| P2d | 0,980 [0,961; 0,994] | 89,6% [83,4%; 95,0%] | 455 / 10,34 [4,92; 17,33] | 93,9% [89,2%; 98,0%] | 91,8% [86,2%; 96,7%] | 90,0% [83,8%; 95,4%] |

### V3 fora do V4 — páginas adicionais

n=27; veículos=10.

| Pipeline | τ palavras ↑ | Sucessor de linhas ↑ | Quebras: total / página ↓ | Fid. 6 ↑ | Fid. 12 ↑ | Fid. 24 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| P0 | 0,812 [0,687; 0,974] | 55,6% [34,0%; 83,2%] | 2309 / 85,52 [19,59; 152,92] | 76,1% [62,9%; 93,6%] | 62,2% [42,1%; 89,0%] | 52,8% [28,8%; 84,7%] |
| P1 | 0,848 [0,728; 0,971] | 85,6% [78,7%; 91,9%] | 430 / 15,93 [5,94; 25,90] | 92,7% [88,3%; 96,8%] | 88,1% [82,4%; 94,2%] | 81,3% [72,8%; 91,2%] |
| P1m | 0,938 [0,859; 0,990] | 90,4% [86,8%; 93,7%] | 308 / 11,41 [4,94; 16,76] | 94,2% [90,4%; 98,3%] | 91,7% [87,8%; 96,8%] | 88,4% [82,6%; 94,5%] |
| P2 | 0,960 [0,914; 0,997] | 91,1% [88,0%; 93,6%] | 249 / 9,22 [4,91; 12,77] | 95,1% [92,5%; 97,9%] | 92,8% [89,9%; 96,5%] | 90,0% [85,9%; 94,9%] |
| P2d | 0,971 [0,942; 0,998] | 90,3% [87,4%; 93,8%] | 325 / 12,04 [4,30; 19,41] | 94,8% [92,1%; 98,4%] | 92,9% [89,7%; 97,4%] | 90,3% [85,9%; 95,9%] |

## Contagens adicionais: total / média por página [IC 95%]

| Pipeline | Intercalações | Deslocados >3 | Deslocados >5 | Quebras/1.000 palavras |
|---|---:|---:|---:|---:|
| P0 | 3790 / 53,38 [28,06; 84,31] | 1128 / 15,89 [9,25; 23,00] | 1004 / 14,14 [8,26; 20,63] | 86,03 [57,89; 116,15] |
| P1 | 177 / 2,49 [0,22; 5,41] | 952 / 13,41 [7,50; 19,25] | 794 / 11,18 [6,26; 16,18] | 24,43 [15,03; 34,86] |
| P1m | 171 / 2,41 [0,16; 5,30] | 357 / 5,03 [1,05; 10,37] | 285 / 4,01 [0,71; 8,36] | 17,04 [8,93; 25,92] |
| P2 | 106 / 1,49 [0,63; 2,49] | 150 / 2,11 [0,31; 4,77] | 108 / 1,52 [0,26; 3,28] | 13,91 [8,50; 19,74] |
| P2d | 266 / 3,75 [0,86; 7,23] | 124 / 1,75 [0,26; 3,90] | 90 / 1,27 [0,23; 2,78] | 21,19 [10,93; 33,48] |

## Origem das quebras: associação e piso irredutível

P1/P1m: nas **duas palavras da transição errada emitida**, mesma região-ouro e caixas distintas → caixa partida; regiões distintas e mesma caixa → caixa fundida; mesma caixa/mesma região → erro interno da caixa. Restante → ordenação residual. Esta regra implementa os dois casos geométricos pedidos, mas a categoria residual **não certifica** que as caixas estejam corretas. Uma região partida ainda pode ser ordenada corretamente; sua quebra pode ter causas conjuntas. Não se estima erro de classe isolado porque não há ouro de classes independente em ambas as coortes. A fração associada não é estimativa causal identificada.

P2/P2d: mesma unidade atômica → átomo interno; fronteira envolvendo átomo atual ou esperado → átomo associado à fronteira; mesma linha-ouro em itens texto distintos → linha partida; mesmo item texto → erro interno de linha; salto horizontal maior que max(4 alturas de letra, 10% da largura), quando o sucessor esperado fica perto → proxy de coluna errada; restante → ordenação residual. **Envolver átomo não prova detecção errada**, e o proxy de coluna não é inspeção humana. As categorias são mutuamente exclusivas, na precedência declarada; palavras livres interpostas recebem categoria própria.

| Origem | P1 | P1m | P2 | P2d |
|---|---:|---:|---:|---:|
| caixa_partida | 13 | 10 | 0 | 0 |
| caixa_fundida | 197 | 197 | 0 | 0 |
| interno_caixa | 16 | 16 | 0 | 0 |
| ordenacao_residual | 912 | 470 | 399 | 361 |
| fora_ouro | 8 | 8 | 19 | 19 |
| atomo_interno | 0 | 0 | 6 | 304 |
| atomo_fronteira | 0 | 0 | 34 | 55 |
| linha_partida | 0 | 0 | 18 | 16 |
| linha_interna | 0 | 0 | 23 | 10 |
| coluna_proxy | 0 | 0 | 16 | 15 |

| Coorte | Caixas associadas P1 | Caixas associadas P1m |
|---|---:|---:|
| v4 | 10,2% | 18,6% |
| v3_novo | 35,6% | 48,7% |
| todas | 19,7% | 31,8% |

**Piso verificável de erro interno:** reordenar itens inteiros jamais corrige um par errado já emitido dentro do mesmo item (caixa/linha/átomo). Não exige reordenação com ouro nem intervenção em produção. Total / fração das quebras: P1: 213 / 18,6%; P1m: 213 / 30,4%; P2: 29 / 5,6%; P2d: 314 / 40,3%. Este piso fornece evidência mais forte de erro herdado do que uma mera associação nas fronteiras.

## Inferência pareada

IC percentil de 95%, 5000 bootstrap agrupados por veículo, semente 20261003: sorteia veículos com reposição e conserva suas páginas; estatística é média macro por página, mantendo os mesmos pesos nos contrastes. Não sorteia palavras como observações independentes. Não refaz treino ou desenvolvimento histórico. Pratt bilateral (`zero_method='pratt'`, aproximação normal, diferenças arredondadas a 12 casas) tanto por página quanto nas médias de veículo. O teste por veículo evita tratar páginas irmãs como independentes; Holm cobre os contrastes/métricas da tabela em cada coorte e unidade. P-valores são exploratórios.

| Coorte | P2−base | Métrica | Δ [IC por veículo] | G/E/P | p página | p veículo | Holm veículo |
|---|---|---|---:|---:|---:|---:|---:|
| todas | P1 | tau | 0,146 [0,075; 0,224] | 41/9/21 | 0,000356 | 0,000298 | 0,005065 |
| todas | P1 | sucessor_linhas | 6,4% [3,2%; 10,0%] | 39/14/18 | 0,000398 | 0,000800 | 0,011204 |
| todas | P1 | fid6 | 2,9% [0,8%; 5,1%] | 43/11/17 | 0,000492 | 0,004743 | 0,061665 |
| todas | P1 | fid12 | 6,6% [3,6%; 10,0%] | 44/10/17 | 0,000048 | 0,000430 | 0,006881 |
| todas | P1 | fid24 | 12,0% [7,5%; 17,5%] | 41/16/14 | 0,000012 | 0,000106 | 0,001908 |
| todas | P1 | quebras | -8,887 [-13,132; -4,889] | 38/13/20 | 0,000730 | 0,000666 | 0,009994 |
| todas | P1 | quebras_mil | -10,518 [-18,288; -3,718] | 38/13/20 | 0,002590 | 0,008496 | 0,101955 |
| todas | P1 | intercalacoes | -1,000 [-3,430; 0,853] | 10/42/19 | 0,097778 | 0,207260 | 1,000000 |
| todas | P1 | deslocados3 | -11,296 [-16,403; -6,500] | 29/38/4 | 0,000009 | 0,000044 | 0,000881 |
| todas | P1 | deslocados5 | -9,662 [-14,257; -5,519] | 29/38/4 | 0,000010 | 0,000044 | 0,000881 |
| todas | P1m | tau | 0,029 [0,000; 0,068] | 17/23/31 | 0,146296 | 0,725834 | 1,000000 |
| todas | P1m | sucessor_linhas | 0,9% [-1,0%; 3,1%] | 15/30/26 | 0,263300 | 0,725834 | 1,000000 |
| todas | P1m | fid6 | 0,8% [-1,0%; 2,5%] | 18/25/28 | 0,242026 | 0,894183 | 1,000000 |
| todas | P1m | fid12 | 1,8% [-0,2%; 4,3%] | 17/29/25 | 0,434563 | 0,856067 | 1,000000 |
| todas | P1m | fid24 | 3,3% [0,3%; 7,1%] | 15/35/21 | 0,646434 | 0,366895 | 1,000000 |
| todas | P1m | quebras | -2,620 [-5,770; 0,175] | 14/29/28 | 0,137858 | 0,913017 | 1,000000 |
| todas | P1m | quebras_mil | -3,134 [-9,750; 2,185] | 14/29/28 | 0,114642 | 0,837129 | 1,000000 |
| todas | P1m | intercalacoes | -0,915 [-3,382; 0,911] | 10/43/18 | 0,099150 | 0,250772 | 1,000000 |
| todas | P1m | deslocados3 | -2,915 [-6,563; -0,244] | 8/57/6 | 0,505516 | 0,231838 | 1,000000 |
| todas | P1m | deslocados5 | -2,493 [-5,879; -0,034] | 7/58/6 | 0,698272 | 0,368930 | 1,000000 |
| v4 | P1 | tau | 0,167 [0,090; 0,251] | 24/7/13 | 0,003582 | 0,002256 | 0,033842 |
| v4 | P1 | sucessor_linhas | 7,0% [2,5%; 11,7%] | 23/9/12 | 0,011496 | 0,001770 | 0,030082 |
| v4 | P1 | fid6 | 3,2% [0,2%; 6,3%] | 23/8/13 | 0,026076 | 0,008159 | 0,106065 |
| v4 | P1 | fid12 | 7,6% [3,4%; 12,5%] | 23/7/14 | 0,008783 | 0,001920 | 0,030717 |
| v4 | P1 | fid24 | 14,1% [7,6%; 21,7%] | 22/13/9 | 0,001608 | 0,000621 | 0,011186 |
| v4 | P1 | quebras | -10,227 [-16,095; -5,187] | 21/9/14 | 0,025749 | 0,003056 | 0,042787 |
| v4 | P1 | quebras_mil | -11,062 [-21,639; -2,253] | 21/9/14 | 0,044302 | 0,008159 | 0,106065 |
| v4 | P1 | intercalacoes | -0,568 [-3,818; 1,417] | 3/26/15 | 0,004583 | 0,046550 | 0,481939 |
| v4 | P1 | deslocados3 | -14,818 [-22,698; -8,044] | 20/23/1 | 0,000033 | 0,000065 | 0,001306 |
| v4 | P1 | deslocados5 | -13,364 [-20,887; -6,953] | 20/23/1 | 0,000028 | 0,000065 | 0,001306 |
| v4 | P1m | tau | 0,034 [0,001; 0,081] | 12/15/17 | 0,583326 | 0,883669 | 1,000000 |
| v4 | P1m | sucessor_linhas | 1,0% [-2,1%; 4,4%] | 10/15/19 | 0,294009 | 0,903408 | 1,000000 |
| v4 | P1m | fid6 | 0,7% [-1,7%; 3,3%] | 10/16/18 | 0,235643 | 0,941679 | 1,000000 |
| v4 | P1m | fid12 | 2,2% [-0,7%; 5,7%] | 10/16/18 | 0,302908 | 0,922292 | 1,000000 |
| v4 | P1m | fid24 | 4,3% [0,2%; 9,7%] | 9/22/13 | 0,684413 | 0,532738 | 1,000000 |
| v4 | P1m | quebras | -2,886 [-7,763; 0,812] | 8/16/20 | 0,094398 | 0,523348 | 1,000000 |
| v4 | P1m | quebras_mil | -3,253 [-13,286; 4,151] | 8/16/20 | 0,100764 | 0,732793 | 1,000000 |
| v4 | P1m | intercalacoes | -0,477 [-3,834; 1,538] | 3/26/15 | 0,004592 | 0,043813 | 0,481939 |
| v4 | P1m | deslocados3 | -4,818 [-11,475; -0,381] | 5/36/3 | 0,407653 | 0,209174 | 1,000000 |
| v4 | P1m | deslocados5 | -4,455 [-10,750; -0,204] | 4/37/3 | 0,625537 | 0,343349 | 1,000000 |
| v3_novo | P1 | tau | 0,112 [0,010; 0,231] | 17/2/8 | 0,039891 | 0,139414 | 1,000000 |
| v3_novo | P1 | sucessor_linhas | 5,5% [-0,7%; 11,1%] | 16/5/6 | 0,008260 | 0,100680 | 1,000000 |
| v3_novo | P1 | fid6 | 2,5% [-0,7%; 4,4%] | 20/3/4 | 0,002646 | 0,114128 | 1,000000 |
| v3_novo | P1 | fid12 | 4,8% [-0,0%; 8,0%] | 21/3/3 | 0,000534 | 0,082731 | 1,000000 |
| v3_novo | P1 | fid24 | 8,7% [1,2%; 14,8%] | 19/3/5 | 0,002256 | 0,102470 | 1,000000 |
| v3_novo | P1 | quebras | -6,704 [-13,122; -0,552] | 17/4/6 | 0,006203 | 0,100680 | 1,000000 |
| v3_novo | P1 | quebras_mil | -9,631 [-19,762; 3,095] | 17/4/6 | 0,015024 | 0,153042 | 1,000000 |
| v3_novo | P1 | intercalacoes | -1,704 [-4,364; 0,476] | 7/16/4 | 0,328036 | 0,873404 | 1,000000 |
| v3_novo | P1 | deslocados3 | -5,556 [-13,261; 0,805] | 9/15/3 | 0,069327 | 0,440900 | 1,000000 |
| v3_novo | P1 | deslocados5 | -3,630 [-9,500; 1,700] | 9/15/3 | 0,082433 | 0,440900 | 1,000000 |
| v3_novo | P1m | tau | 0,022 [-0,011; 0,096] | 5/8/14 | 0,067400 | 1,000000 | 1,000000 |
| v3_novo | P1m | sucessor_linhas | 0,7% [-2,4%; 3,2%] | 5/15/7 | 0,690845 | 0,567938 | 1,000000 |
| v3_novo | P1m | fid6 | 0,9% [-1,5%; 2,3%] | 8/9/10 | 0,703731 | 0,607959 | 1,000000 |
| v3_novo | P1m | fid12 | 1,1% [-1,7%; 2,8%] | 7/13/7 | 0,867922 | 0,323922 | 1,000000 |
| v3_novo | P1m | fid24 | 1,6% [-1,2%; 4,8%] | 6/13/8 | 0,788210 | 0,323922 | 1,000000 |
| v3_novo | P1m | quebras | -2,185 [-4,577; 0,412] | 6/13/8 | 0,837689 | 0,538167 | 1,000000 |
| v3_novo | P1m | quebras_mil | -2,941 [-8,168; 5,299] | 6/13/8 | 0,749117 | 0,681519 | 1,000000 |
| v3_novo | P1m | intercalacoes | -1,630 [-4,121; 0,417] | 7/17/3 | 0,240673 | 0,581989 | 1,000000 |
| v3_novo | P1m | deslocados3 | 0,185 [-3,176; 1,960] | 3/21/3 | 0,986737 | 0,815540 | 1,000000 |
| v3_novo | P1m | deslocados5 | 0,704 [-2,333; 2,600] | 3/21/3 | 0,960227 | 0,815540 | 1,000000 |

## Conferência independente da prévia

A prévia chamou de P2 o método **Docling**, que aqui é P2d. Reproduzimos sua regra de entrada (sem embaralhamento), filtragem de palavras livres, atribuição de caixa partida usando o **sucessor esperado** e fidelidade por IDs, com código novo. Assim se distingue mudança de definição de erro de contagem.

| Pipeline da prévia | Métrica | Valor salvo | Recalculado | Confere |
|---|---|---:|---:|---|
| P1 | total_quebras | 713,00000000 | 713,00000000 | sim |
| P1 | tau_media | 0,81853825 | 0,81853825 | sim |
| P1 | fid6_media | 0,91498084 | 0,91498084 | sim |
| P1 | fid12_media | 0,84803244 | 0,84803244 | sim |
| P1 | fid24_media | 0,76828191 | 0,76828191 | sim |
| P1m | total_quebras | 390,00000000 | 390,00000000 | sim |
| P1m | tau_media | 0,95242425 | 0,95242425 | sim |
| P1m | fid6_media | 0,95128569 | 0,95128569 | sim |
| P1m | fid12_media | 0,91719807 | 0,91719807 | sim |
| P1m | fid24_media | 0,87902114 | 0,87902114 | sim |
| P2 | total_quebras | 448,00000000 | 448,00000000 | sim |
| P2 | tau_media | 0,98012109 | 0,98012109 | sim |
| P2 | fid6_media | 0,93436378 | 0,93436378 | sim |
| P2 | fid12_media | 0,91799558 | 0,91799558 | sim |
| P2 | fid24_media | 0,89881459 | 0,89881459 | sim |

Conferência por página, incluindo origens de P2d: 1276 comparações; 0 divergências. Detalhes completos no JSON.
Origens reproduzidas (partida/fundida/interno/residual): P1 = 15/68/0/630; P1m = 11/68/0/311.
**Não confere a interpretação da prévia:** P2d−P1m = **1,32 quebras/página**, e 6,93 quebras/1.000 palavras (Pratt p=0,047604): o sinal reportado como redução era aumento. A própria fração minoritária de erros de caixa contradizia a conclusão de 'esmagadora maioria'. p maior que 0,05 não demonstra ganho; p menor que 0,05 não informa direção sem o sinal. A prévia não mediu ls3, v3 novo, intercalações, deslocamentos, sucessor real de linhas, IC por veículo nem fidelidade lexical com a função do piloto. Essas extensões estão presentes aqui.

## Exemplos de página e regressões

Selecionados automaticamente pelos maiores ganhos e perdas absolutos de P2 contra P1m; não ajustam parâmetros.

| Página | Coorte | Quebras P1 / P1m / P2 / P2d | Δ P2−P1m | Fid12 P1m→P2 | Intercalações P1m→P2 |
|---|---|---:|---:|---:|---:|
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | v4 | 75/74/9/69 | -65 | 53,7%→94,8% | 65→0 |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | v4 | 96/96/51/47 | -45 | 71,6%→88,4% | 0→12 |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | v4 | 58/58/14/14 | -44 | 94,0%→98,4% | 3→3 |
| `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0` | v3_novo | 138/134/92/96 | -42 | 3,7%→26,1% | 85→43 |
| `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13` | v4 | 17/5/15/30 | 10 | 95,8%→93,3% | 0→3 |
| `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41` | v3_novo | 0/0/9/0 | 9 | 100,0%→83,4% | 0→0 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` | v4 | 3/2/10/4 | 8 | 98,7%→98,3% | 0→1 |
| `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | v4 | 48/6/13/13 | 7 | 95,7%→91,1% | 0→8 |

Transições concretas para inspeção (primeira quebra de P2; textos vêm das palavras extraídas, não de explicação inventada):

- `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`: saída «45»→«Quarta-feira»; esperado «BOLETIM»; categoria `ordenacao_residual`, salto-ouro=-6 palavras.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: saída «(cid:1)»→«(cid:11)(cid:12)(cid:10)Ç(cid:2)(cid:6)(cid:14)(cid:12)(cid:13)(cid:10)(cid:2)»; esperado «(cid:2)(cid:3)(cid:4)»; categoria `linha_interna`, salto-ouro=9 palavras.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: saída «Gerais»→«ExTrATo»; esperado «diário»; categoria `ordenacao_residual`, salto-ouro=12 palavras.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: saída «INSCRIÇÃO»→«1»; esperado «NOME»; categoria `ordenacao_residual`, salto-ouro=2 palavras.
- `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13`: saída «JAPERI»→«14»; esperado «ANO»; categoria `ordenacao_residual`, salto-ouro=-4 palavras.
- `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41`: saída «VIDAL»→«Secretário»; esperado «ROSA»; categoria `ordenacao_residual`, salto-ouro=10 palavras.
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5`: saída «DO»→«SALVADOR-BAHIA»; esperado «CONTRIBUINTE»; categoria `atomo_fronteira`, salto-ouro=-16 palavras.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: saída «cial»→«42»; esperado «R$»; categoria `ordenacao_residual`, salto-ouro=-12 palavras.

## Limitações e recomendação

Amostra pequena e de conveniência; v4 participou do desenvolvimento do método e as páginas novas do v3 continuam em veículos majoritariamente conhecidos. A ordem humana é cega às ordens automáticas, mas as regiões do Diamond foram anotadas **corrigindo pré-anotação**, com viés de ancoragem. No v3, a ordem humana está sobre blocos do extrator ou sua projeção: ele não é um ouro independente de segmentação e pode subestimar exatamente os erros de caixas investigados. Não juntar coortes apaga essa diferença. Há ouro de ordem de regiões, não de transcrição nem ordem palavra a palavra; `linhas()` também é usado no interior do ouro e dos itens previstos, favorecendo convenções comuns. Tabelas podem ter ordem interna ambígua; não demonstramos correção de célula sem anotação independente.

Pipelines preservam o mesmo saco de palavras digitais; portanto não medem palavras ausentes, OCR, transcrição, bytes mal codificados ou erros sem efeito na sequência. Uma classe errada só é detectável aqui quando muda o texto final. P1 usa a proposta atual por regras, não um detector visual novo de caixas finas. Imagens v3/v4 têm resoluções originais diferentes, com redimensionamento comum do ls3; o cache Docling traz seu próprio piso de confiança. Medidas de fidelidade são macro: páginas curtas pesam igual às longas; taxas por 1.000 palavras e totais ajudam a interpretar. Identificar uma quebra com caixa partida não prova que dispensar caixas resolve essa quebra. Fronteiras envolvendo átomos e proxy de coluna são diagnósticos auditáveis, não categorias causais humanas.

A hipótese de que a maioria das quebras nasce nas caixas não é sustentada nesta régua. O efeito observado de P2 deve ser descrito com seus dois controles: redução relativa contra P1=55,1%, contra P1m=26,5%, IC do segundo contraste=-2,62 [-5,77; 0,18]. Contra P1m, P2 reduz quebras em 14 páginas, empata em 29 e aumenta em 28: o ganho médio se concentra em algumas correções grandes, não em melhora uniforme. Recomenda-se manter P1m como controle obrigatório e validar os casos de regressão em ouro de palavras/linhas desenhado independentemente. Não adotar a ideia com a justificativa de 'maioria causada pelas caixas' sem esse ouro. Ganho em τ não autoriza concluir menor número de quebras; equivalência não é demonstrada por ausência de significância.

## Reprodutibilidade

Executar na raiz:

```powershell
venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py
venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py --do-zero
venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py --conferir
```

`--do-zero` descarta o cache de resultados da avaliação, recalcula segmentação/propostas/ordens/métricas/bootstrap e compara os números com a execução anterior. Reusa apenas palavras/imagens/detecções automáticas congeladas; `--reinferir` opcional também refaz ls3 em CPU. Isso separa execução do zero da avaliação de reextração/modelo. JSON guarda hashes de entradas, configurações, resultados completos, sequências de IDs, itens e eventos por página; caches ficam exclusivamente sob `resultados/erros_ponta_a_ponta_cache/`. `--conferir` confere o Markdown regenerado byte a byte, resumos recalculados dos resultados por página e os hashes; nenhum arquivo existente de outro experimento é modificado.

Conferência da reexecução: numeros identicos a execucao anterior.
