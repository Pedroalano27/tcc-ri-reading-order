# Margens por repetição entre páginas e veto de corpo

1. Âncoras: aprovadas; referência e unidades preservadas. V4: quebras 6,045 → 4,886; τ 0,985948 → 0,990947.
2. Variante: Combinação / marcas ancoradas; parâmetros escolhidos só em v4 e RN.
3. golden_v3_novo: n=27; Δ quebras 1,000 [-0,834; 2,917]; Δ τ -0,011415 [-0,026585; 0,000399].
4. teste_silver sem sobreposição humana: n=68; Δ quebras -0,029 [-0,806; 1,000]; Δ τ -0,002296 [-0,016011; 0,000079].
5. Alvo operacional: Não atingido: corpo no v4 recuperou 40/47 (85,1%), com 3 novas perdas; saldo de todos os sucessores fora do ajuste: v3=-28; teste sem bancadas humanas=+0.

Relatório escrito pelo script a partir dos caches. Estado: tudo.

## Âncoras

| Controle | Páginas | τ palavras | Quebras/página |
|---|---:|---:|---:|
| Regra original | 44 | 0,985948 | 6,045455 |
| Extrator + XY-cut + margens | 44 | 0,952424 | 8,931818 |

Regra original reexecutada e sequência inteira conferida contra P2 histórico. P1m é a sequência histórica reavaliada na referência atual. Falha da âncora interrompe a execução antes do ajuste.

## Procedimento e limites

São as mesmas linhas e átomos ls3 congelados da bancada, com expansão interna canônica de `bancada_ordenadores.expansoes`. O detector não é carregado. O preditor recebe apenas texto, coordenadas, tipo automático e estilo nativo; classes humanas só entram no diagnóstico importado.

PyMuPDF extrai linhas e spans (fonte, tamanho e negrito) da página alvo e de até dez vizinhas próximas do mesmo PDF. Remove caixa, dígitos e datas do texto; número isolado ganha um marcador. Exige o mesmo texto normalizado, posição vertical aproximada e estilo compatível em pelo menos duas vizinhas. Quando o suporte ocorre apenas na mesma paridade, compara pares com pares e ímpares com ímpares. O índice da página é zero-based; a separação de paridades é equivalente à numeração iniciada em um.

A posição extrema (16% no topo/base) delimita candidata, e não decide sozinha no método de recorrência. Linhas recorrentes no interior ficam no corpo, exceto marca lateral. O veto exige alinhamento de coluna, espaçamento de linha e fonte/tamanho/negrito compatíveis com uma vizinha de corpo. Evidência forte que vence o veto exige recorrência em ao menos três páginas e 60% das vizinhas pertinentes, com sinal editorial, número isolado ou forma lateral. A semente de corpo deriva da partição automática original, não da referência.

Cabeçalhos e rodapés são ordenados por faixas horizontais de centros próximos (0,65 altura de palavra), e dentro delas da esquerda para a direita. O corpo reutiliza a projeção local original, sem novas barreiras. Marcas usam duas políticas aplicadas a todas as páginas: fluxo após corpo e antes de rodapé; ou inserção pela altura na zona/coluna geometricamente mais próxima. Nunca se escolhe a política por página.

A ablação só veto conserva a partição marginal original e testa a continuidade/estilo. A ablação só recorrência dispensa o veto. Só faixas isola a mudança de ordenação dos cabeçalhos. Linhas/átomos não são partidos. Menos de duas vizinhas ou coordenadas nativas incompatíveis conservam exatamente a regra original, inclusive nas ablações.

Sem treino, GPU, rede, OCR, multiprocessing ou dados do projeto parceiro. Um processo e uma página com palavras por vez; no máximo quatro threads nas bibliotecas numéricas. Caches por PDF/página/ordem, escrita atômica e parada por pouca RAM. O cache nativo valida caminho, tamanho e mtime do PDF; as fontes da bancada têm SHA-256.

golden_v4 foi usado no desenvolvimento da regra e no ajuste deste experimento. golden_v3_novo já foi consultado em rodadas anteriores: é comparação externa ao ajuste atual, não teste intocado. A silver é automática, por fluxo de palavras do PDF nos veículos confiáveis; a validação é RN e o teste CE, MA e RJ. RN exclui páginas presentes em qualquer tarefa humana, seguindo a tarefa 06. Veículos vistos seguem os sete veículos do split original, sem novo treino. Amostra humana pequena e referências humanas expandidas geometricamente dentro das regiões.

IC 95% por bootstrap de veículos e Wilcoxon bilateral Pratt sobre diferenças médias por veículo, importados das tarefas anteriores; as médias principais ponderam páginas. Com poucos veículos de teste, os IC/p-valores têm pouca resolução. Ablações exploratórias sem correção de multiplicidade. Teste completo e teste sem qualquer página das bancadas humanas são mostrados separados.

## Escolha congelada antes da comparação externa

`{"tolerancia_y": 0.008, "espacamento_h": 2.2}`; Combinação / marcas ancoradas.

Menor soma das medias de quebras v4+RN entre combinacoes; perda de tau <=0,002 em cada; maior tau e chave como desempate. Ablacoes usam os mesmos parametros.

Congelada em 2026-10-08 02:57:22; restrição de τ satisfeita: True.

Grade de configurações: 0 = tolerância vertical 0,8% da altura, espaçamento 1,8 alturas de palavra; 1 = tolerância vertical 1,4% da altura, espaçamento 1,8 alturas de palavra; 2 = tolerância vertical 0,8% da altura, espaçamento 2,2 alturas de palavra; 3 = tolerância vertical 1,4% da altura, espaçamento 2,2 alturas de palavra.

| Configuração | v4: τ / quebras | RN: τ / quebras |
|---|---:|---:|
| 0:original | 0,985948 / 6,045 | 0,954162 / 17,857 |
| 0:faixas_so | 0,987192 / 5,341 | 0,954186 / 17,857 |
| 0:recorrencia_final | 0,989266 / 5,682 | 0,964991 / 15,000 |
| 0:veto_final | 0,989063 / 4,977 | 0,963642 / 15,643 |
| 0:combinacao_final | 0,990436 / 5,159 | 0,964991 / 15,000 |
| 0:recorrencia_ancorada | 0,989703 / 5,477 | 0,964991 / 15,000 |
| 0:veto_ancorada | 0,989505 / 4,727 | 0,963642 / 15,643 |
| 0:combinacao_ancorada | 0,990873 / 4,955 | 0,964991 / 15,000 |
| 1:recorrencia_final | 0,983336 / 6,136 | 0,964982 / 15,143 |
| 1:veto_final | 0,989063 / 4,977 | 0,963642 / 15,643 |
| 1:combinacao_final | 0,990136 / 5,250 | 0,964991 / 15,000 |
| 1:recorrencia_ancorada | 0,983774 / 5,932 | 0,964982 / 15,143 |
| 1:veto_ancorada | 0,989505 / 4,727 | 0,963642 / 15,643 |
| 1:combinacao_ancorada | 0,990574 / 5,045 | 0,964991 / 15,000 |
| 2:recorrencia_final | 0,989266 / 5,682 | 0,964991 / 15,000 |
| 2:veto_final | 0,989132 / 4,932 | 0,963642 / 15,643 |
| 2:combinacao_final | 0,990509 / 5,091 | 0,964991 / 15,000 |
| 2:recorrencia_ancorada | 0,989703 / 5,477 | 0,964991 / 15,000 |
| 2:veto_ancorada | 0,989574 / 4,682 | 0,963642 / 15,643 |
| 2:combinacao_ancorada | 0,990947 / 4,886 | 0,964991 / 15,000 |
| 3:recorrencia_final | 0,983336 / 6,136 | 0,964982 / 15,143 |
| 3:veto_final | 0,989132 / 4,932 | 0,963642 / 15,643 |
| 3:combinacao_final | 0,990216 / 5,136 | 0,964991 / 15,000 |
| 3:recorrencia_ancorada | 0,983774 / 5,932 | 0,964982 / 15,143 |
| 3:veto_ancorada | 0,989574 / 4,682 | 0,963642 / 15,643 |
| 3:combinacao_ancorada | 0,990653 / 4,932 | 0,964991 / 15,000 |

## golden_v4

Cobertura: 44 páginas; completa.

| Ablação | n / veículos | τ [IC] | Quebras/página [IC] | Fidelidade de 12 (%) [IC] | Sucessor de linhas (%) [IC] |
|---|---:|---:|---:|---:|---:|
| Regra original | 44 / 27 | 0,985948 [0,973495; 0,995020] | 6,045 [4,023; 8,887] | 94,81 [91,36; 97,24] | 92,72 [87,81; 96,08] |
| Só faixas de cabeçalho | 44 / 27 | 0,987192 [0,974791; 0,995490] | 5,341 [3,311; 8,250] | 95,39 [91,83; 97,82] | 94,53 [91,36; 96,87] |
| Só recorrência / marcas ao final | 44 / 27 | 0,989266 [0,976401; 0,996905] | 5,682 [3,574; 8,638] | 95,09 [91,55; 97,52] | 94,24 [91,08; 96,65] |
| Só veto / marcas ao final | 44 / 27 | 0,989132 [0,976794; 0,996581] | 4,932 [2,857; 7,929] | 95,60 [91,97; 98,07] | 94,82 [91,59; 97,28] |
| Combinação / marcas ao final | 44 / 27 | 0,990509 [0,977685; 0,998124] | 5,091 [2,939; 8,068] | 95,49 [91,86; 98,00] | 94,83 [91,53; 97,34] |
| Só recorrência / marcas ancoradas | 44 / 27 | 0,989703 [0,976954; 0,997148] | 5,477 [3,463; 8,400] | 95,27 [91,72; 97,64] | 94,46 [91,29; 96,82] |
| Só veto / marcas ancoradas | 44 / 27 | 0,989574 [0,977307; 0,997033] | 4,682 [2,689; 7,619] | 95,81 [92,19; 98,25] | 95,16 [91,90; 97,54] |
| Combinação / marcas ancoradas **selecionada** | 44 / 27 | 0,990947 [0,978314; 0,998360] | 4,886 [2,833; 7,822] | 95,67 [92,03; 98,12] | 95,05 [91,80; 97,45] |

| Ablação contra original | Δ quebras [IC] / p veículo | Δ τ [IC] / p veículo | Δ fidelidade de 12 (p.p.) [IC] / p | Δ sucessor (p.p.) [IC] / p |
|---|---:|---:|---:|---:|
| Só faixas de cabeçalho | -0,705 [-1,067; -0,333] / 0,004737 | 0,001243 [0,000024; 0,003380] / 0,017021 | 0,572 [0,164; 1,181] / 0,009133 | 1,805 [0,424; 3,755] / 0,004778 |
| Só recorrência / marcas ao final | -0,364 [-1,296; 0,564] / 0,761420 | 0,003317 [-0,001053; 0,008243] / 0,923275 | 0,277 [-0,413; 1,174] / 0,722024 | 1,515 [-0,227; 3,671] / 0,521598 |
| Só veto / marcas ao final | -1,114 [-1,902; -0,442] / 0,004766 | 0,003183 [0,000113; 0,007096] / 0,041214 | 0,785 [0,252; 1,456] / 0,022665 | 2,097 [0,620; 4,039] / 0,004778 |
| Combinação / marcas ao final | -0,955 [-2,000; 0,000] / 0,139931 | 0,004561 [0,000138; 0,009583] / 0,262023 | 0,679 [-0,004; 1,575] / 0,185968 | 2,103 [0,445; 4,168] / 0,052172 |
| Só recorrência / marcas ancoradas | -0,568 [-1,512; 0,342] / 0,473580 | 0,003755 [-0,000488; 0,008514] / 0,630130 | 0,457 [-0,278; 1,404] / 0,873294 | 1,737 [-0,001; 3,855] / 0,271164 |
| Só veto / marcas ancoradas | -1,364 [-2,152; -0,649] / 0,001573 | 0,003626 [0,000458; 0,007523] / 0,008731 | 1,000 [0,413; 1,746] / 0,002982 | 2,438 [0,935; 4,306] / 0,001580 |
| Combinação / marcas ancoradas | -1,159 [-2,171; -0,222] / 0,060279 | 0,004998 [0,000781; 0,009850] / 0,131668 | 0,859 [0,145; 1,774] / 0,077130 | 2,325 [0,688; 4,358] / 0,018556 |

| Estrato: variante selecionada | n / veículos | τ [IC] | Quebras/página [IC] | Δ quebras [IC] / p | Fid.12 (%) [IC] | Sucessor (%) [IC] |
|---|---:|---:|---:|---:|---:|---:|
| todos | 44 / 27 | 0,990947 [0,978314; 0,998360] | 4,886 [2,833; 7,822] | -1,159 [-2,171; -0,222] / 0,060279 | 95,67 [92,03; 98,12] | 95,05 [91,80; 97,45] |
| vistos | 5 / 5 | 0,999222 [0,997769; 1,000000] | 4,400 [0,600; 8,200] | -0,400 [-2,000; 1,400] / 0,669815 | 98,88 [97,93; 99,80] | 98,72 [97,63; 99,81] |
| nao_vistos | 39 / 22 | 0,989886 [0,975891; 0,998103] | 4,949 [2,750; 8,195] | -1,256 [-2,366; -0,158] / 0,065600 | 95,26 [91,10; 97,98] | 94,58 [90,82; 97,23] |

| Ablação / subtipo original congelado | Perdidos original | Recuperados | Novos perdidos | Saldo | Perdidos variante |
|---|---:|---:|---:|---:|---:|
| Só faixas de cabeçalho / Corpo tratado como margem pelo limiar | 47 | 7 | 1 | +6 | 41 |
| Só faixas de cabeçalho / Marca marginal em posição errada | 40 | 14 | 0 | +14 | 26 |
| Só faixas de cabeçalho / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 2 | +6 | 22 |
| Só recorrência / marcas ao final / Corpo tratado como margem pelo limiar | 47 | 35 | 4 | +31 | 16 |
| Só recorrência / marcas ao final / Marca marginal em posição errada | 40 | 12 | 1 | +11 | 29 |
| Só recorrência / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 6 | +2 | 26 |
| Só veto / marcas ao final / Corpo tratado como margem pelo limiar | 47 | 26 | 0 | +26 | 21 |
| Só veto / marcas ao final / Marca marginal em posição errada | 40 | 14 | 0 | +14 | 26 |
| Só veto / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 3 | +5 | 23 |
| Combinação / marcas ao final / Corpo tratado como margem pelo limiar | 47 | 40 | 3 | +37 | 10 |
| Combinação / marcas ao final / Marca marginal em posição errada | 40 | 14 | 1 | +13 | 27 |
| Combinação / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 6 | +2 | 26 |
| Só recorrência / marcas ancoradas / Corpo tratado como margem pelo limiar | 47 | 35 | 4 | +31 | 16 |
| Só recorrência / marcas ancoradas / Marca marginal em posição errada | 40 | 21 | 1 | +20 | 20 |
| Só recorrência / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 6 | +2 | 26 |
| Só veto / marcas ancoradas / Corpo tratado como margem pelo limiar | 47 | 26 | 0 | +26 | 21 |
| Só veto / marcas ancoradas / Marca marginal em posição errada | 40 | 25 | 0 | +25 | 15 |
| Só veto / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 3 | +5 | 23 |
| Combinação / marcas ancoradas / Corpo tratado como margem pelo limiar | 47 | 40 | 3 | +37 | 10 |
| Combinação / marcas ancoradas / Marca marginal em posição errada | 40 | 23 | 1 | +22 | 18 |
| Combinação / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 6 | +2 | 26 |

Todos os tipos de sucessor: recuperados=81; novos perdidos=26; saldo=+55.
Sem nenhuma vizinha: 5; com uma só: 0; com 2–4: 6; com 5–10: 33; fallback total: 5.
Estilo associado em 3617/3729 unidades (inclui átomos, para os quais não se procura estilo).

| Estrato / subtipo: combinação selecionada | Perdidos original | Recuperados | Novos perdidos | Saldo |
|---|---:|---:|---:|---:|
| todos / Corpo tratado como margem pelo limiar | 47 | 40 | 3 | +37 |
| todos / Marca marginal em posição errada | 40 | 23 | 1 | +22 |
| todos / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 6 | +2 |
| vistos / Corpo tratado como margem pelo limiar | 6 | 3 | 1 | +2 |
| vistos / Marca marginal em posição errada | 1 | 1 | 0 | +1 |
| vistos / Cabeçalho multilinha/lado a lado fora de ordem | 0 | 0 | 1 | -1 |
| nao_vistos / Corpo tratado como margem pelo limiar | 41 | 37 | 2 | +35 |
| nao_vistos / Marca marginal em posição errada | 39 | 22 | 1 | +21 |
| nao_vistos / Cabeçalho multilinha/lado a lado fora de ordem | 28 | 8 | 5 | +3 |

No estrato todos, saldo em transições originalmente marginais=+62; em todas as demais transições=-7. A classificação permanece congelada: novas perdas no corpo originalmente comum não são reclassificadas como margem após a intervenção.

Maiores regressões observadas da combinação (sem escolha posterior de política):

- `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22`: quebras 0 → 7; Δ τ -0,002580; sucessores recuperados=0, novos perdidos=4.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`: quebras 9 → 12; Δ τ -0,010829; sucessores recuperados=1, novos perdidos=4.
- `official_diary_sc/2023-11-27_22151.pdf#p28`: quebras 6 → 9; Δ τ -0,003619; sucessores recuperados=0, novos perdidos=3.

## golden_v3_novo

Cobertura: 27 páginas; completa.

| Ablação | n / veículos | τ [IC] | Quebras/página [IC] | Fidelidade de 12 (%) [IC] | Sucessor de linhas (%) [IC] |
|---|---:|---:|---:|---:|---:|
| Regra original | 27 / 10 | 0,959557 [0,915350; 0,997056] | 9,222 [4,900; 12,867] | 92,84 [89,86; 96,59] | 91,13 [88,06; 93,56] |
| Só faixas de cabeçalho | 27 / 10 | 0,959909 [0,915677; 0,997346] | 8,778 [4,695; 12,118] | 93,08 [90,24; 96,72] | 91,67 [88,91; 93,78] |
| Só recorrência / marcas ao final | 27 / 10 | 0,941618 [0,897893; 0,996838] | 10,704 [5,227; 16,001] | 92,70 [89,85; 96,21] | 89,59 [85,57; 93,30] |
| Só veto / marcas ao final | 27 / 10 | 0,960326 [0,916805; 0,997346] | 8,630 [4,695; 11,974] | 93,11 [90,27; 96,72] | 91,70 [88,91; 93,82] |
| Combinação / marcas ao final | 27 / 10 | 0,947983 [0,906416; 0,996842] | 10,370 [5,038; 15,675] | 92,80 [89,89; 96,36] | 89,92 [85,97; 93,51] |
| Só recorrência / marcas ancoradas | 27 / 10 | 0,941778 [0,897966; 0,997131] | 10,556 [5,000; 15,919] | 92,78 [89,90; 96,31] | 89,73 [85,71; 93,50] |
| Só veto / marcas ancoradas | 27 / 10 | 0,960486 [0,916905; 0,997641] | 8,481 [4,448; 11,867] | 93,20 [90,34; 96,82] | 91,84 [89,09; 94,04] |
| Combinação / marcas ancoradas **selecionada** | 27 / 10 | 0,948143 [0,906514; 0,997139] | 10,222 [4,789; 15,561] | 92,88 [89,93; 96,46] | 90,06 [86,09; 93,72] |

| Ablação contra original | Δ quebras [IC] / p veículo | Δ τ [IC] / p veículo | Δ fidelidade de 12 (p.p.) [IC] / p | Δ sucessor (p.p.) [IC] / p |
|---|---:|---:|---:|---:|
| Só faixas de cabeçalho | -0,444 [-0,791; -0,091] / 0,047376 | 0,000351 [0,000011; 0,001288] / 0,123232 | 0,240 [-0,020; 0,469] / 0,293819 | 0,536 [0,032; 1,049] / 0,047376 |
| Só recorrência / marcas ao final | 1,481 [0,000; 3,280] / 0,193105 | -0,017939 [-0,041424; 0,000023] / 0,358326 | -0,142 [-0,504; 0,153] / 0,323922 | -1,543 [-3,245; -0,055] / 0,160984 |
| Só veto / marcas ao final | -0,593 [-0,897; -0,125] / 0,047188 | 0,000769 [0,000035; 0,001832] / 0,027670 | 0,272 [0,000; 0,483] / 0,243443 | 0,574 [0,091; 1,072] / 0,047376 |
| Combinação / marcas ao final | 1,148 [-0,480; 3,030] / 0,502019 | -0,011575 [-0,026878; 0,000033] / 0,540291 | -0,042 [-0,413; 0,307] / 0,795182 | -1,209 [-2,975; 0,431] / 0,567938 |
| Só recorrência / marcas ancoradas | 1,333 [-0,444; 3,176] / 0,471474 | -0,017779 [-0,041131; 0,000373] / 0,507624 | -0,059 [-0,429; 0,347] / 0,758239 | -1,402 [-3,138; 0,287] / 0,411770 |
| Só veto / marcas ancoradas | -0,741 [-1,200; -0,286] / 0,027553 | 0,000929 [0,000082; 0,002168] / 0,016924 | 0,355 [0,079; 0,623] / 0,123232 | 0,715 [0,293; 1,375] / 0,027670 |
| Combinação / marcas ancoradas | 1,000 [-0,834; 2,917] / 0,797308 | -0,011415 [-0,026585; 0,000399] / 0,721277 | 0,040 [-0,347; 0,504] / 0,758239 | -1,068 [-2,862; 0,780] / 0,918282 |

| Estrato: variante selecionada | n / veículos | τ [IC] | Quebras/página [IC] | Δ quebras [IC] / p | Fid.12 (%) [IC] | Sucessor (%) [IC] |
|---|---:|---:|---:|---:|---:|---:|
| todos | 27 / 10 | 0,948143 [0,906514; 0,997139] | 10,222 [4,789; 15,561] | 1,000 [-0,834; 2,917] / 0,797308 | 92,88 [89,93; 96,46] | 90,06 [86,09; 93,72] |
| nao_vistos | 27 / 10 | 0,948143 [0,906514; 0,997139] | 10,222 [4,789; 15,561] | 1,000 [-0,834; 2,917] / 0,797308 | 92,88 [89,93; 96,46] | 90,06 [86,09; 93,72] |
| vistos | 0 / 0 | — | — | — | — | — |

| Ablação / subtipo original congelado | Perdidos original | Recuperados | Novos perdidos | Saldo | Perdidos variante |
|---|---:|---:|---:|---:|---:|
| Só faixas de cabeçalho / Corpo tratado como margem pelo limiar | 4 | 0 | 1 | -1 | 5 |
| Só faixas de cabeçalho / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só faixas de cabeçalho / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 2 | +5 | 12 |
| Só recorrência / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 1 | 3 | -2 | 6 |
| Só recorrência / marcas ao final / Marca marginal em posição errada | 8 | 0 | 1 | -1 | 9 |
| Só recorrência / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 | 13 |
| Só veto / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 4 | 1 | +3 | 1 |
| Só veto / marcas ao final / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só veto / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 2 | +5 | 12 |
| Combinação / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 2 | 3 | -1 | 5 |
| Combinação / marcas ao final / Marca marginal em posição errada | 8 | 1 | 0 | +1 | 7 |
| Combinação / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 | 13 |
| Só recorrência / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 1 | 3 | -2 | 6 |
| Só recorrência / marcas ancoradas / Marca marginal em posição errada | 8 | 4 | 1 | +3 | 5 |
| Só recorrência / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 | 13 |
| Só veto / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 4 | 1 | +3 | 1 |
| Só veto / marcas ancoradas / Marca marginal em posição errada | 8 | 4 | 0 | +4 | 4 |
| Só veto / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 2 | +5 | 12 |
| Combinação / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 2 | 3 | -1 | 5 |
| Combinação / marcas ancoradas / Marca marginal em posição errada | 8 | 5 | 0 | +5 | 3 |
| Combinação / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 | 13 |

Todos os tipos de sucessor: recuperados=23; novos perdidos=51; saldo=-28.
Sem nenhuma vizinha: 5; com uma só: 0; com 2–4: 1; com 5–10: 21; fallback total: 5.
Estilo associado em 2197/2258 unidades (inclui átomos, para os quais não se procura estilo).

| Estrato / subtipo: combinação selecionada | Perdidos original | Recuperados | Novos perdidos | Saldo |
|---|---:|---:|---:|---:|
| todos / Corpo tratado como margem pelo limiar | 4 | 2 | 3 | -1 |
| todos / Marca marginal em posição errada | 8 | 5 | 0 | +5 |
| todos / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 |
| nao_vistos / Corpo tratado como margem pelo limiar | 4 | 2 | 3 | -1 |
| nao_vistos / Marca marginal em posição errada | 8 | 5 | 0 | +5 |
| nao_vistos / Cabeçalho multilinha/lado a lado fora de ordem | 17 | 7 | 3 | +4 |

No estrato todos, saldo em transições originalmente marginais=+14; em todas as demais transições=-42. A classificação permanece congelada: novas perdas no corpo originalmente comum não são reclassificadas como margem após a intervenção.

Maiores regressões observadas da combinação (sem escolha posterior de política):

- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p56`: quebras 2 → 21; Δ τ -0,147037; sucessores recuperados=2, novos perdidos=21.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p60`: quebras 5 → 23; Δ τ -0,145341; sucessores recuperados=2, novos perdidos=20.
- `official_diary_ac/executive_official_diary_2025-09-24.pdf#p41`: quebras 0 → 3; Δ τ -0,000059; sucessores recuperados=0, novos perdidos=3.

## validacao_silver

Cobertura: 14 páginas; completa.

| Ablação | n / veículos | τ [IC] | Quebras/página [IC] | Fidelidade de 12 (%) [IC] | Sucessor de linhas (%) [IC] |
|---|---:|---:|---:|---:|---:|
| Regra original | 14 / 1 | 0,954162 [0,954162; 0,954162] | 17,857 [17,857; 17,857] | 94,89 [94,89; 94,89] | 90,45 [90,45; 90,45] |
| Só faixas de cabeçalho | 14 / 1 | 0,954186 [0,954186; 0,954186] | 17,857 [17,857; 17,857] | 94,87 [94,87; 94,87] | 90,46 [90,46; 90,46] |
| Só recorrência / marcas ao final | 14 / 1 | 0,964991 [0,964991; 0,964991] | 15,000 [15,000; 15,000] | 96,09 [96,09; 96,09] | 91,95 [91,95; 91,95] |
| Só veto / marcas ao final | 14 / 1 | 0,963642 [0,963642; 0,963642] | 15,643 [15,643; 15,643] | 95,57 [95,57; 95,57] | 91,37 [91,37; 91,37] |
| Combinação / marcas ao final | 14 / 1 | 0,964991 [0,964991; 0,964991] | 15,000 [15,000; 15,000] | 96,09 [96,09; 96,09] | 91,95 [91,95; 91,95] |
| Só recorrência / marcas ancoradas | 14 / 1 | 0,964991 [0,964991; 0,964991] | 15,000 [15,000; 15,000] | 96,09 [96,09; 96,09] | 91,95 [91,95; 91,95] |
| Só veto / marcas ancoradas | 14 / 1 | 0,963642 [0,963642; 0,963642] | 15,643 [15,643; 15,643] | 95,57 [95,57; 95,57] | 91,37 [91,37; 91,37] |
| Combinação / marcas ancoradas **selecionada** | 14 / 1 | 0,964991 [0,964991; 0,964991] | 15,000 [15,000; 15,000] | 96,09 [96,09; 96,09] | 91,95 [91,95; 91,95] |

| Ablação contra original | Δ quebras [IC] / p veículo | Δ τ [IC] / p veículo | Δ fidelidade de 12 (p.p.) [IC] / p | Δ sucessor (p.p.) [IC] / p |
|---|---:|---:|---:|---:|
| Só faixas de cabeçalho | 0,000 [0,000; 0,000] / 1,000000 | 0,000024 [0,000024; 0,000024] / 0,317311 | -0,025 [-0,025; -0,025] / 0,317311 | 0,013 [0,013; 0,013] / 0,317311 |
| Só recorrência / marcas ao final | -2,857 [-2,857; -2,857] / 0,317311 | 0,010830 [0,010830; 0,010830] / 0,317311 | 1,198 [1,198; 1,198] / 0,317311 | 1,500 [1,500; 1,500] / 0,317311 |
| Só veto / marcas ao final | -2,214 [-2,214; -2,214] / 0,317311 | 0,009480 [0,009480; 0,009480] / 0,317311 | 0,677 [0,677; 0,677] / 0,317311 | 0,921 [0,921; 0,921] / 0,317311 |
| Combinação / marcas ao final | -2,857 [-2,857; -2,857] / 0,317311 | 0,010830 [0,010830; 0,010830] / 0,317311 | 1,198 [1,198; 1,198] / 0,317311 | 1,500 [1,500; 1,500] / 0,317311 |
| Só recorrência / marcas ancoradas | -2,857 [-2,857; -2,857] / 0,317311 | 0,010830 [0,010830; 0,010830] / 0,317311 | 1,198 [1,198; 1,198] / 0,317311 | 1,500 [1,500; 1,500] / 0,317311 |
| Só veto / marcas ancoradas | -2,214 [-2,214; -2,214] / 0,317311 | 0,009480 [0,009480; 0,009480] / 0,317311 | 0,677 [0,677; 0,677] / 0,317311 | 0,921 [0,921; 0,921] / 0,317311 |
| Combinação / marcas ancoradas | -2,857 [-2,857; -2,857] / 0,317311 | 0,010830 [0,010830; 0,010830] / 0,317311 | 1,198 [1,198; 1,198] / 0,317311 | 1,500 [1,500; 1,500] / 0,317311 |

| Estrato: variante selecionada | n / veículos | τ [IC] | Quebras/página [IC] | Δ quebras [IC] / p | Fid.12 (%) [IC] | Sucessor (%) [IC] |
|---|---:|---:|---:|---:|---:|---:|
| todos | 14 / 1 | 0,964991 [0,964991; 0,964991] | 15,000 [15,000; 15,000] | -2,857 [-2,857; -2,857] / 0,317311 | 96,09 [96,09; 96,09] | 91,95 [91,95; 91,95] |

| Ablação / subtipo original congelado | Perdidos original | Recuperados | Novos perdidos | Saldo | Perdidos variante |
|---|---:|---:|---:|---:|---:|
| Só faixas de cabeçalho / Corpo tratado como margem pelo limiar | 55 | 2 | 1 | +1 | 54 |
| Só faixas de cabeçalho / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só faixas de cabeçalho / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 0 | 0 | +0 | 6 |
| Só recorrência / marcas ao final / Corpo tratado como margem pelo limiar | 55 | 35 | 3 | +32 | 23 |
| Só recorrência / marcas ao final / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só recorrência / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 1 | 1 | +0 | 6 |
| Só veto / marcas ao final / Corpo tratado como margem pelo limiar | 55 | 29 | 2 | +27 | 28 |
| Só veto / marcas ao final / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só veto / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 0 | 0 | +0 | 6 |
| Combinação / marcas ao final / Corpo tratado como margem pelo limiar | 55 | 35 | 3 | +32 | 23 |
| Combinação / marcas ao final / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Combinação / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 1 | 1 | +0 | 6 |
| Só recorrência / marcas ancoradas / Corpo tratado como margem pelo limiar | 55 | 35 | 3 | +32 | 23 |
| Só recorrência / marcas ancoradas / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só recorrência / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 1 | 1 | +0 | 6 |
| Só veto / marcas ancoradas / Corpo tratado como margem pelo limiar | 55 | 29 | 2 | +27 | 28 |
| Só veto / marcas ancoradas / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Só veto / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 0 | 0 | +0 | 6 |
| Combinação / marcas ancoradas / Corpo tratado como margem pelo limiar | 55 | 35 | 3 | +32 | 23 |
| Combinação / marcas ancoradas / Marca marginal em posição errada | 8 | 0 | 0 | +0 | 8 |
| Combinação / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 1 | 1 | +0 | 6 |

Todos os tipos de sucessor: recuperados=44; novos perdidos=4; saldo=+40.
Sem nenhuma vizinha: 1; com uma só: 0; com 2–4: 0; com 5–10: 13; fallback total: 1.
Estilo associado em 2470/2484 unidades (inclui átomos, para os quais não se procura estilo).

| Estrato / subtipo: combinação selecionada | Perdidos original | Recuperados | Novos perdidos | Saldo |
|---|---:|---:|---:|---:|
| todos / Corpo tratado como margem pelo limiar | 55 | 35 | 3 | +32 |
| todos / Marca marginal em posição errada | 8 | 0 | 0 | +0 |
| todos / Cabeçalho multilinha/lado a lado fora de ordem | 6 | 1 | 1 | +0 |

## teste_silver

Cobertura: 89 páginas; completa.

| Ablação | n / veículos | τ [IC] | Quebras/página [IC] | Fidelidade de 12 (%) [IC] | Sucessor de linhas (%) [IC] |
|---|---:|---:|---:|---:|---:|
| Regra original | 89 / 3 | 0,959565 [0,889505; 0,998435] | 27,449 [22,184; 32,316] | 82,54 [72,93; 89,87] | 84,02 [77,08; 94,09] |
| Só faixas de cabeçalho | 89 / 3 | 0,959636 [0,889507; 0,998468] | 26,966 [21,132; 32,368] | 82,77 [72,93; 90,37] | 84,50 [77,05; 94,18] |
| Só recorrência / marcas ao final | 89 / 3 | 0,950305 [0,876999; 0,998577] | 28,045 [21,605; 34,000] | 82,47 [72,59; 90,05] | 83,58 [75,52; 93,70] |
| Só veto / marcas ao final | 89 / 3 | 0,959762 [0,890374; 0,998468] | 26,921 [21,132; 32,368] | 82,78 [72,93; 90,37] | 84,51 [77,05; 94,26] |
| Combinação / marcas ao final | 89 / 3 | 0,954304 [0,879341; 0,998502] | 27,798 [21,474; 33,816] | 82,49 [72,55; 90,07] | 83,75 [75,70; 93,92] |
| Só recorrência / marcas ancoradas | 89 / 3 | 0,950305 [0,876999; 0,998577] | 28,045 [21,605; 34,000] | 82,47 [72,59; 90,05] | 83,58 [75,52; 93,70] |
| Só veto / marcas ancoradas | 89 / 3 | 0,959762 [0,890374; 0,998468] | 26,921 [21,132; 32,368] | 82,78 [72,93; 90,37] | 84,51 [77,05; 94,26] |
| Combinação / marcas ancoradas **selecionada** | 89 / 3 | 0,954304 [0,879341; 0,998502] | 27,798 [21,474; 33,816] | 82,49 [72,55; 90,07] | 83,75 [75,70; 93,92] |

| Ablação contra original | Δ quebras [IC] / p veículo | Δ τ [IC] / p veículo | Δ fidelidade de 12 (p.p.) [IC] / p | Δ sucessor (p.p.) [IC] / p |
|---|---:|---:|---:|---:|
| Só faixas de cabeçalho | -0,483 [-1,053; 0,053] / 0,285049 | 0,000070 [0,000002; 0,000131] / 0,108809 | 0,229 [0,000; 0,502] / 0,165518 | 0,478 [-0,027; 1,113] / 0,285049 |
| Só recorrência / marcas ao final | 0,596 [-0,579; 1,684] / 0,285049 | -0,009261 [-0,017553; 0,000141] / 0,285049 | -0,067 [-0,347; 0,174] / 1,000000 | -0,438 [-1,564; 0,669] / 0,592980 |
| Só veto / marcas ao final | -0,528 [-1,053; 0,053] / 0,285049 | 0,000197 [0,000033; 0,000869] / 0,108809 | 0,239 [0,000; 0,502] / 0,165518 | 0,489 [-0,027; 1,113] / 0,285049 |
| Combinação / marcas ao final | 0,348 [-0,711; 1,500] / 0,592980 | -0,005261 [-0,010164; 0,000066] / 0,285049 | -0,046 [-0,380; 0,208] / 1,000000 | -0,269 [-1,376; 0,800] / 0,592980 |
| Só recorrência / marcas ancoradas | 0,596 [-0,579; 1,684] / 0,285049 | -0,009261 [-0,017553; 0,000141] / 0,285049 | -0,067 [-0,347; 0,174] / 1,000000 | -0,438 [-1,564; 0,669] / 0,592980 |
| Só veto / marcas ancoradas | -0,528 [-1,053; 0,053] / 0,285049 | 0,000197 [0,000033; 0,000869] / 0,108809 | 0,239 [0,000; 0,502] / 0,165518 | 0,489 [-0,027; 1,113] / 0,285049 |
| Combinação / marcas ancoradas | 0,348 [-0,711; 1,500] / 0,592980 | -0,005261 [-0,010164; 0,000066] / 0,285049 | -0,046 [-0,380; 0,208] / 1,000000 | -0,269 [-1,376; 0,800] / 0,592980 |

| Estrato: variante selecionada | n / veículos | τ [IC] | Quebras/página [IC] | Δ quebras [IC] / p | Fid.12 (%) [IC] | Sucessor (%) [IC] |
|---|---:|---:|---:|---:|---:|---:|
| todos | 89 / 3 | 0,954304 [0,879341; 0,998502] | 27,798 [21,474; 33,816] | 0,348 [-0,711; 1,500] / 0,592980 | 82,49 [72,55; 90,07] | 83,75 [75,70; 93,92] |
| sem_humanas | 68 / 3 | 0,969913 [0,942599; 0,998674] | 29,456 [24,097; 34,167] | -0,029 [-0,806; 1,000] / 0,592980 | 81,76 [71,68; 90,25] | 82,79 [75,13; 95,28] |

| Ablações no teste SEM páginas humanas | n | τ | Quebras/página | Δ quebras [IC] / p veículo | Saldo de sucessores |
|---|---:|---:|---:|---:|---:|
| Regra original | 68 | 0,972209 | 29,485 | 0,000 [0,000; 0,000] / 1,000000 | +0 |
| Só faixas de cabeçalho | 68 | 0,972291 | 28,926 | -0,559 [-1,161; 0,067] / 0,285049 | +38 |
| Só recorrência / marcas ao final | 68 | 0,967203 | 29,691 | 0,206 [-0,645; 1,857] / 0,285049 | -16 |
| Só veto / marcas ao final | 68 | 0,972291 | 28,926 | -0,559 [-1,161; 0,067] / 0,285049 | +38 |
| Combinação / marcas ao final | 68 | 0,969913 | 29,456 | -0,029 [-0,806; 1,000] / 0,592980 | +0 |
| Só recorrência / marcas ancoradas | 68 | 0,967203 | 29,691 | 0,206 [-0,645; 1,857] / 0,285049 | -16 |
| Só veto / marcas ancoradas | 68 | 0,972291 | 28,926 | -0,559 [-1,161; 0,067] / 0,285049 | +38 |
| Combinação / marcas ancoradas | 68 | 0,969913 | 29,456 | -0,029 [-0,806; 1,000] / 0,592980 | +0 |

| Ablação / subtipo original congelado | Perdidos original | Recuperados | Novos perdidos | Saldo | Perdidos variante |
|---|---:|---:|---:|---:|---:|
| Só faixas de cabeçalho / Corpo tratado como margem pelo limiar | 4 | 0 | 0 | +0 | 4 |
| Só faixas de cabeçalho / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Só faixas de cabeçalho / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 25 | 20 | +5 | 59 |
| Só recorrência / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 1 | 5 | -4 | 8 |
| Só recorrência / marcas ao final / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Só recorrência / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 31 | 20 | +11 | 53 |
| Só veto / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 4 | 0 | +4 | 0 |
| Só veto / marcas ao final / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Só veto / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 25 | 20 | +5 | 59 |
| Combinação / marcas ao final / Corpo tratado como margem pelo limiar | 4 | 2 | 4 | -2 | 6 |
| Combinação / marcas ao final / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Combinação / marcas ao final / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 31 | 20 | +11 | 53 |
| Só recorrência / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 1 | 5 | -4 | 8 |
| Só recorrência / marcas ancoradas / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Só recorrência / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 31 | 20 | +11 | 53 |
| Só veto / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 4 | 0 | +4 | 0 |
| Só veto / marcas ancoradas / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Só veto / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 25 | 20 | +5 | 59 |
| Combinação / marcas ancoradas / Corpo tratado como margem pelo limiar | 4 | 2 | 4 | -2 | 6 |
| Combinação / marcas ancoradas / Marca marginal em posição errada | 38 | 21 | 2 | +19 | 19 |
| Combinação / marcas ancoradas / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 31 | 20 | +11 | 53 |

Todos os tipos de sucessor: recuperados=81; novos perdidos=117; saldo=-36.
Sem nenhuma vizinha: 6; com uma só: 0; com 2–4: 3; com 5–10: 80; fallback total: 6.
Estilo associado em 8779/8942 unidades (inclui átomos, para os quais não se procura estilo).

| Estrato / subtipo: combinação selecionada | Perdidos original | Recuperados | Novos perdidos | Saldo |
|---|---:|---:|---:|---:|
| todos / Corpo tratado como margem pelo limiar | 4 | 2 | 4 | -2 |
| todos / Marca marginal em posição errada | 38 | 21 | 2 | +19 |
| todos / Cabeçalho multilinha/lado a lado fora de ordem | 64 | 31 | 20 | +11 |
| sem_humanas / Corpo tratado como margem pelo limiar | 0 | 0 | 3 | -3 |
| sem_humanas / Marca marginal em posição errada | 31 | 19 | 2 | +17 |
| sem_humanas / Cabeçalho multilinha/lado a lado fora de ordem | 46 | 23 | 16 | +7 |

No estrato sem_humanas, saldo em transições originalmente marginais=+32; em todas as demais transições=-32. A classificação permanece congelada: novas perdas no corpo originalmente comum não são reclassificadas como margem após a intervenção.

Maiores regressões observadas da combinação (sem escolha posterior de política):

- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p59`: quebras 3 → 8; Δ τ -0,026560; sucessores recuperados=0, novos perdidos=5.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: quebras 18 → 23; Δ τ -0,023695; sucessores recuperados=1, novos perdidos=6.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: quebras 45 → 49; Δ τ -0,002215; sucessores recuperados=0, novos perdidos=4.

Sobreposição com bancadas humanas: 21 páginas. O estrato sem_humanas é a avaliação externa mais limpa.

## O que as ablações mostram

A combinação selecionada continua a mesma da escolha v4+RN. Comparações com a ablação só veto são descritivas; ela não substitui a variante nas predições selecionadas após observar o teste.

| Bancada / estrato | Combinação: Δ quebras [IC] | Só veto, marcas ancoradas: Δ quebras [IC] | Recorrência adicionada ao veto: Δ quebras |
|---|---:|---:|---:|
| golden_v4 / todos | -1,159 [-2,171; -0,222] | -1,364 [-2,152; -0,649] | 0,205 |
| golden_v3_novo / todos | 1,000 [-0,834; 2,917] | -0,741 [-1,200; -0,286] | 1,741 |
| validacao_silver / todos | -2,857 [-2,857; -2,857] | -2,214 [-2,214; -2,214] | -0,643 |
| teste_silver / sem_humanas | -0,029 [-0,806; 1,000] | -0,559 [-1,161; 0,067] | 0,529 |

Só veto com marcas ancoradas: v3 9,222 → 8,481 quebras/página (p por veículo=0,027553); teste sem humanas 29,485 → 28,926 (p=0,285049). Esta ablação ajuda a separar o efeito de continuidade/estilo do efeito de exigir recorrência; o teste tem apenas os veículos do split e os IC devem acompanhar a leitura.

## Alvo e problemas que permanecem

Não atingido: corpo no v4 recuperou 40/47 (85,1%), com 3 novas perdas; saldo de todos os sucessores fora do ajuste: v3=-28; teste sem bancadas humanas=+0.

O alvo operacional exige recuperar pelo menos um quarto dos sucessores de corpo marginalizado do v4 e saldo positivo de todos os sucessores, separadamente no v3 e no teste sem bancadas humanas. Saldo por corpo, marca e cabeçalho também aparece acima; nenhum ganho interno substitui a comparação externa.

O diagnóstico usa literalmente o emparelhamento e os subtipos das tarefas 05/06, congelados pela regra original. Classes de regiões só são usadas no diagnóstico v4; v3 e silver usam proxies geométricos/lexicais e não têm a mesma qualidade de classificação. Sucessores perdidos e quebras emitidas têm denominadores diferentes.

Repetição não identifica cabeçalho exclusivo da primeira página, não distingue todo título recorrente de corpo e pode perder texto com extração nativa fragmentada. Estilo ausente impede veto; a exigência de negrito igual pode preservar uma falsa margem. Não corrige ordem interna de tabela/imagem, linha partida, OCR ausente, calhas ou títulos transversais. O fluxo silver dentro das tabelas pode divergir da expansão canônica.

Fontes, parâmetros, resultados por página, diagnósticos e ordens das ablações: `resultados/margens_repeticao_cache/`. Predições selecionadas: `resultados/ordenadores_sem_caixas/pred/regra_margens_rep__linhas__<bancada>.jsonl`.

## Verificação

{"paginas_reexecutadas": 174, "metodos_por_pagina": 8, "regua_completa_primeira_pagina_por_bancada": true, "contratos_e_estatisticas": true, "fontes_preservadas": true, "device": "cpu", "num_workers": 0}

Menor RAM física livre observada nas verificações: 3371,8 MiB (não é medida do pico de memória do processo).

Comando: `orquestracao/analises/margens_repeticao.py --conferir`
