# Regra + LayoutLM textual: intervenção seletiva

1. Escolha congelada em RN e golden_v4: `hibrido_estrito_3` (vantagem em logits).
2. golden_v4 (ajuste): Δ híbrido−regra 0,86 quebras/página.
3. golden_v3 novo: Δ 1,37 quebras/página.
4. Teste silver CE/MA/RJ: Δ 2,01 quebras/página.
5. O híbrido selecionado não melhora consistentemente fora do ajuste; conservar a regra.

Relatório gerado exclusivamente pelo script e seus caches de execução.

Estado: `resultados\regra_mais_modelo_cache\3f09221479a8b0c9224142d0b10b0577c164bdf43453b426d505ad88d367bc9d/estado.json`. CPU, quatro threads, uma página por vez; pesos locais, sem rede.

## Controles e protocolo

Regra `regra_colunas`, representação em linhas, átomos ls3 congelados. Entrada pela função original `ordem_entrada` (`random.Random(f"entrada-{page_id}")`). Expansão canônica `ordem_sem_bbox.fluxo()` e régua `erros_ponta_a_ponta.medir`; nenhum cálculo de eficácia foi substituído.

P2 e regra reexecutados por página contra as sequências históricas. P1m é controle histórico do pipeline extrator + XY-cut + margens; não foi reextraído. Aborta antes de números novos se τ divergir mais de 0,006 ou a média de quebras não reproduzir seis casas.

| Controle v4 | τ palavras | Quebras/página |
|---|---:|---:|
| regra | 0,985948 | 6,045455 |
| P2 | 0,985948 | 6,045455 |
| P1m_historico | 0,952424 | 8,931818 |

## Intervenção e escolha

Candidatos importados de `corretor_de_transicoes.candidatos`, nível 3 já estabelecido no experimento anterior. A escolha deste nível naquele trabalho consultou as duas bancadas humanas: golden_v3 é externo ao ajuste atual, mas não ao desenvolvimento histórico dos candidatos.

Alerta estrito: salto/retorno/alinhamento/objeto da tarefa 08, elemento transversal, disputa entre colunas com linha próxima ainda abaixo e margem com menos de duas vizinhas alinhadas ou continuidade próxima de corpo. Amplo acrescenta continuidade geométrica baixa, toda troca de coluna e toda fronteira de margem. Margem e suporte são proxies automáticos; nenhum rótulo humano entra no alerta.

O candidato de maior logit só substitui o sucessor original com alerta, discordância e vantagem estritamente maior que 0, 1 ou 3. Diferença de logits equivale à diferença de log-probabilidades na mesma fonte; não é confiança calibrada. Move uma unidade para após a fonte (ou a fonte ao fim para FIN), no máximo 12 posições na ordem corrente. Preserva cobertura, unicidade, ordem relativa das demais e todas as propostas previamente aceitas. A remoção e inserção podem mudar outras duas fronteiras: medimos todas as mudanças realizadas.

Seleção minimiza a média, com peso igual para RN e v4, do Δ de quebras por página. Desempate: maior Δτ, menos mudanças, alerta estrito e maior limiar. A escolha é gravada antes da avaliação dos dois conjuntos externos. Sem otimização no golden_v3 novo ou no teste.

Logits saem do mesmo encoder, ComTexto, lote e decoder em cadeias da inferência textual. Carregamento meta/mmap/assign evita duas cópias dos pesos. Em páginas agrupadas, só a última linha de uma faixa e a primeira da outra têm score de fronteira; arestas internas sem score ficam protegidas. O modelo sozinho conserva a expansão original das faixas.

Treino do checkpoint (somente lido): 3140 páginas, 20 épocas; veículos vistos = os sete do split de treino. Não houve novo treino. A inferência do modelo sozinho é conferida contra os JSONLs históricos onde disponíveis; RN é inferida agora.

## Resultados por bancada

Médias macro por página [IC 95% agrupado por veículo]. Δ = método−regra; menor quebra é melhor. Wilcoxon bilateral Pratt nas diferenças médias de cada veículo, p exploratório sem ajuste por múltiplas comparações. IC não é calculado durante uma bancada incompleta.

| Bancada / grupo | Método | n / veículos | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |
|---|---|---:|---:|---:|---:|---:|
| validacao_silver / todos | regra | 15 / 1 | 0,957218 [0,957218; 0,957218] | 16,67 [16,67; 16,67] | 95,23 [95,23; 95,23]% | 91,09 [91,09; 91,09]% |
| validacao_silver / todos | modelo | 15 / 1 | 0,942410 [0,942410; 0,942410] | 31,47 [31,47; 31,47] | 90,83 [90,83; 90,83]% | 85,83 [85,83; 85,83]% |
| validacao_silver / todos | hibrido_estrito_3 | 15 / 1 | 0,957005 [0,957005; 0,957005] | 17,93 [17,93; 17,93] | 94,72 [94,72; 94,72]% | 90,38 [90,38; 90,38]% |
| golden_v4 / todos | regra | 44 / 27 | 0,985948 [0,973495; 0,995020] | 6,05 [4,02; 8,89] | 94,81 [91,36; 97,24]% | 92,72 [87,81; 96,08]% |
| golden_v4 / todos | modelo | 44 / 27 | 0,941984 [0,888019; 0,974801] | 20,77 [6,31; 45,83] | 88,73 [83,22; 93,54]% | 86,73 [80,17; 92,24]% |
| golden_v4 / todos | hibrido_estrito_3 | 44 / 27 | 0,956568 [0,905867; 0,985623] | 6,91 [5,15; 9,62] | 92,30 [89,02; 95,16]% | 90,46 [85,90; 93,93]% |
| golden_v4 / vistos | regra | 5 / 5 | 0,997638 [0,994112; 0,999926] | 4,80 [2,60; 7,60] | 98,49 [98,09; 98,89]% | 97,70 [96,96; 98,54]% |
| golden_v4 / vistos | modelo | 5 / 5 | 0,986548 [0,966421; 0,999766] | 16,20 [4,40; 35,80] | 93,28 [85,70; 98,11]% | 93,13 [85,98; 97,67]% |
| golden_v4 / vistos | hibrido_estrito_3 | 5 / 5 | 0,997047 [0,994592; 0,999485] | 8,00 [5,00; 10,80] | 96,07 [92,88; 98,29]% | 95,01 [91,07; 97,46]% |
| golden_v4 / não vistos | regra | 39 / 22 | 0,984450 [0,970860; 0,994281] | 6,21 [4,00; 9,40] | 94,34 [90,34; 97,03]% | 92,09 [86,60; 95,77]% |
| golden_v4 / não vistos | modelo | 39 / 22 | 0,936271 [0,875079; 0,973474] | 21,36 [5,58; 48,51] | 88,15 [81,96; 93,41]% | 85,91 [78,55; 91,90]% |
| golden_v4 / não vistos | hibrido_estrito_3 | 39 / 22 | 0,951379 [0,893135; 0,983728] | 6,77 [4,79; 9,73] | 91,82 [87,96; 94,97]% | 89,88 [84,65; 93,74]% |
| golden_v3_novo / todos | regra | 27 / 10 | 0,959557 [0,915350; 0,997056] | 9,22 [4,90; 12,87] | 92,84 [89,86; 96,59]% | 91,13 [88,06; 93,56]% |
| golden_v3_novo / todos | modelo | 27 / 10 | 0,931019 [0,859585; 0,988124] | 23,19 [6,71; 48,19] | 86,66 [76,34; 94,81]% | 84,70 [75,69; 90,70]% |
| golden_v3_novo / todos | hibrido_estrito_3 | 27 / 10 | 0,953797 [0,909546; 0,990233] | 10,59 [6,58; 14,20] | 91,21 [87,82; 94,74]% | 88,99 [84,11; 91,97]% |
| golden_v3_novo / vistos | sem páginas | 0 / 0 | — | — | — | — |
| golden_v3_novo / não vistos | regra | 27 / 10 | 0,959557 [0,915350; 0,997056] | 9,22 [4,90; 12,87] | 92,84 [89,86; 96,59]% | 91,13 [88,06; 93,56]% |
| golden_v3_novo / não vistos | modelo | 27 / 10 | 0,931019 [0,859585; 0,988124] | 23,19 [6,71; 48,19] | 86,66 [76,34; 94,81]% | 84,70 [75,69; 90,70]% |
| golden_v3_novo / não vistos | hibrido_estrito_3 | 27 / 10 | 0,953797 [0,909546; 0,990233] | 10,59 [6,58; 14,20] | 91,21 [87,82; 94,74]% | 88,99 [84,11; 91,97]% |
| teste_silver / todos | regra | 89 / 3 | 0,959565 [0,889505; 0,998435] | 27,45 [22,18; 32,32] | 82,54 [72,93; 89,87]% | 84,02 [77,08; 94,09]% |
| teste_silver / todos | modelo | 89 / 3 | 0,930033 [0,813480; 0,974085] | 50,46 [35,42; 128,85] | 74,37 [59,27; 82,88]% | 70,99 [61,54; 74,67]% |
| teste_silver / todos | hibrido_estrito_3 | 89 / 3 | 0,954260 [0,889048; 0,996730] | 29,46 [25,26; 34,05] | 81,57 [71,88; 89,13]% | 81,97 [75,78; 93,86]% |

| Bancada / grupo | Método | Δ quebras [IC veículo] | p veículo | Δ τ [IC veículo] | p veículo | Reparos / regressões de sucessores de linhas |
|---|---|---:|---:|---:|---:|---:|
| validacao_silver / todos | modelo | 14,80 [14,80; 14,80] | 0,317311 | -0,014808 [-0,014808; -0,014808] | 0,317311 | 85 / 307 |
| validacao_silver / todos | hibrido_estrito_3 | 1,27 [1,27; 1,27] | 0,317311 | -0,000213 [-0,000213; -0,000213] | 0,317311 | 36 / 55 |
| golden_v4 / todos | modelo | 14,73 [1,50; 38,43] | 0,009352 | -0,043964 [-0,099323; -0,012195] | 0,002371 | 96 / 727 |
| golden_v4 / todos | hibrido_estrito_3 | 0,86 [0,10; 1,74] | 0,025513 | -0,029380 [-0,080855; -0,002586] | 0,007385 | 68 / 100 |
| golden_v4 / vistos | modelo | 11,40 [0,20; 31,80] | 0,173568 | -0,011090 [-0,031505; 0,004356] | 0,500184 | 6 / 53 |
| golden_v4 / vistos | hibrido_estrito_3 | 3,20 [0,60; 5,80] | 0,089686 | -0,000590 [-0,002988; 0,001349] | 0,414216 | 0 / 14 |
| golden_v4 / não vistos | modelo | 15,15 [0,83; 40,90] | 0,024910 | -0,048179 [-0,110110; -0,012308] | 0,003855 | 90 / 674 |
| golden_v4 / não vistos | hibrido_estrito_3 | 0,56 [-0,20; 1,42] | 0,106975 | -0,033071 [-0,092504; -0,002907] | 0,008146 | 68 / 86 |
| golden_v3_novo / todos | modelo | 13,96 [0,57; 37,89] | 0,126033 | -0,028538 [-0,056987; -0,007792] | 0,009344 | 55 / 422 |
| golden_v3_novo / todos | hibrido_estrito_3 | 1,37 [0,61; 2,37] | 0,036292 | -0,005761 [-0,018252; -0,001208] | 0,009344 | 29 / 68 |
| golden_v3_novo / não vistos | modelo | 13,96 [0,57; 37,89] | 0,126033 | -0,028538 [-0,056987; -0,007792] | 0,009344 | 55 / 422 |
| golden_v3_novo / não vistos | hibrido_estrito_3 | 1,37 [0,61; 2,37] | 0,036292 | -0,005761 [-0,018252; -0,001208] | 0,009344 | 29 / 68 |
| teste_silver / todos | modelo | 23,01 [3,11; 100,23] | 0,108809 | -0,029533 [-0,076025; -0,018810] | 0,108809 | 249 / 2300 |
| teste_silver / todos | hibrido_estrito_3 | 2,01 [-0,31; 3,08] | 0,285049 | -0,005306 [-0,010565; -0,000457] | 0,108809 | 173 / 353 |

**Escolha congelada: `hibrido_estrito_3`**. Objetivo 1,065152 Δ quebras; seleção em `selecao.json`.

## Curva de intervenção (as seis configurações)

A fração inclui o sucessor FIN de cada página: fontes cujo sucessor final mudou / número de unidades. Reparos/regressões usam as linhas-ouro inteiras intactas e são conferidos contra a métrica oficial. A grade fora do ajuste é diagnóstico, não autoriza trocar a escolha congelada.

| Bancada | Configuração | Transições alteradas | Fração | Quebras/página | Δ quebras | τ | Reparos | Regressões |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| validacao_silver | hibrido_estrito_0 | 218 | 8,50% | 21,40 | 4,73 | 0,956839 | 37 | 108 |
| validacao_silver | hibrido_estrito_1 | 179 | 6,98% | 18,93 | 2,27 | 0,956881 | 37 | 71 |
| validacao_silver | hibrido_estrito_3 | 157 | 6,12% | 17,93 | 1,27 | 0,957005 | 36 | 55 |
| validacao_silver | hibrido_amplo_0 | 221 | 8,61% | 21,53 | 4,87 | 0,956838 | 37 | 110 |
| validacao_silver | hibrido_amplo_1 | 182 | 7,09% | 19,07 | 2,40 | 0,956880 | 37 | 73 |
| validacao_silver | hibrido_amplo_3 | 160 | 6,24% | 18,07 | 1,40 | 0,957004 | 36 | 57 |
| golden_v4 | hibrido_estrito_0 | 581 | 15,58% | 11,43 | 5,39 | 0,955919 | 89 | 315 |
| golden_v4 | hibrido_estrito_1 | 426 | 11,42% | 8,57 | 2,52 | 0,956276 | 80 | 183 |
| golden_v4 | hibrido_estrito_3 | 300 | 8,05% | 6,91 | 0,86 | 0,956568 | 68 | 100 |
| golden_v4 | hibrido_amplo_0 | 590 | 15,82% | 11,59 | 5,55 | 0,955917 | 89 | 322 |
| golden_v4 | hibrido_amplo_1 | 438 | 11,75% | 8,80 | 2,75 | 0,956274 | 80 | 193 |
| golden_v4 | hibrido_amplo_3 | 306 | 8,21% | 7,00 | 0,95 | 0,956568 | 68 | 104 |
| golden_v3_novo | hibrido_estrito_0 | 317 | 14,04% | 11,81 | 2,59 | 0,952215 | 69 | 136 |
| golden_v3_novo | hibrido_estrito_1 | 240 | 10,63% | 10,89 | 1,67 | 0,952419 | 52 | 96 |
| golden_v3_novo | hibrido_estrito_3 | 160 | 7,09% | 10,59 | 1,37 | 0,953797 | 29 | 68 |
| golden_v3_novo | hibrido_amplo_0 | 340 | 15,06% | 12,56 | 3,33 | 0,952142 | 66 | 154 |
| golden_v3_novo | hibrido_amplo_1 | 262 | 11,60% | 11,48 | 2,26 | 0,952355 | 50 | 109 |
| golden_v3_novo | hibrido_amplo_3 | 180 | 7,97% | 10,89 | 1,67 | 0,953749 | 32 | 78 |
| teste_silver | hibrido_estrito_0 | 1678 | 18,77% | 35,64 | 8,19 | 0,951973 | 230 | 960 |
| teste_silver | hibrido_estrito_1 | 1255 | 14,03% | 32,19 | 4,74 | 0,953584 | 208 | 631 |
| teste_silver | hibrido_estrito_3 | 805 | 9,00% | 29,46 | 2,01 | 0,954260 | 173 | 353 |
| teste_silver | hibrido_amplo_0 | 1730 | 19,35% | 36,03 | 8,58 | 0,951935 | 230 | 996 |
| teste_silver | hibrido_amplo_1 | 1314 | 14,69% | 32,56 | 5,11 | 0,953536 | 210 | 667 |
| teste_silver | hibrido_amplo_3 | 852 | 9,53% | 29,61 | 2,16 | 0,954226 | 179 | 373 |

## Por que o modelo consegue ou não corrigir

Diagnóstico apenas das transições de linhas que a regra perdeu. Categorias abaixo são exclusivas: falha estrutural, transição interna, candidato ausente, score de faixa indisponível; depois, melhor candidato correto, o mesmo sucessor errado da regra, ou outro sucessor errado. Fronteira correta não garante linha inteira intacta. O recall total inclui transições internas preservadas.

| Bancada | Recall candidatos | Erros regra | Estrutural | Interna | Ausente | Sem score | Modelo correto | Mesmo erro | Outro erro | Correto + alerta estrito / amplo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validacao_silver | 96,67% | 250 | 56 | 1 | 110 | 0 | 62 | 7 | 14 | 54 / 61 |
| golden_v4 | 98,21% | 237 | 5 | 0 | 73 | 0 | 112 | 21 | 26 | 105 / 110 |
| golden_v3_novo | 97,36% | 238 | 7 | 0 | 68 | 0 | 84 | 65 | 14 | 73 / 78 |
| teste_silver | 87,03% | 2347 | 1399 | 3 | 523 | 0 | 257 | 112 | 53 | 233 / 245 |

No teste silver, recall total 87,03%: a meta de 95% foi atingida no ajuste, mas não se transfere a esta referência automática. Mesmo todos os candidatos têm teto de cobertura de fronteiras 90,58%, dadas 1399 fronteiras estruturalmente inalcançáveis. Não ampliamos candidatos usando o teste. Parte dessa limitação vem da discordância entre a expansão canônica e o fluxo silver dentro das unidades; a comparação usa a mesma representação para os três métodos.


Diagnóstico das propostas da configuração escolhida: uma fronteira alcançável entre unidades identifica o alvo-ouro da fonte. FIN e fontes sem alvo único ficam como não avaliáveis. Os contadores abaixo olham a aresta proposta; reparos/regressões da régua acima incluem também os efeitos da remoção e inserção nas outras fronteiras.

| Bancada | Propostas | Aceitas | Fora da janela | Conflito | Aceitas: regra errada → alvo certo | Aceitas: regra certa → alvo errado | Aceitas: ambos errados | Não avaliáveis | Regressões: fonte intervinda / outras |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validacao_silver | 103 | 64 | 27 | 12 | 32 | 11 | 17 | 4 | 11 / 44 |
| golden_v4 | 182 | 131 | 31 | 20 | 66 | 15 | 26 | 24 | 17 / 83 |
| golden_v3_novo | 82 | 62 | 15 | 5 | 24 | 11 | 11 | 16 | 10 / 58 |
| teste_silver | 419 | 323 | 46 | 50 | 152 | 60 | 79 | 32 | 71 / 282 |

O recall global alto inclui muitas transições fáceis já corretas. A coluna “Ausente” mostra quanto ele cai justamente nos erros da regra. “Mesmo erro” mede quando o modelo conserva o sucessor errado; a tabela de propostas mostra também quando um logit alto derruba uma decisão correta. Alertas geométricos e vantagem de score não garantem saldo positivo, e os movimentos têm efeitos nas fronteiras vizinhas. “Outras” conta sucessores de linhas perdidos cuja unidade de origem não teve proposta aceita. O critério compara somente o logit da aresta da fonte, sem garantir preservação das demais fronteiras; esse efeito é medido na saída, não vetado pelo ouro.

Nenhuma das seis configurações reduz as quebras médias nos dois conjuntos fora do ajuste. Nesta grade, o modelo ainda não serve como corretor seletivo consistente.

## Cobertura, limitações e reprodução

golden_v4 participou do desenvolvimento da regra e do ajuste desta grade. golden_v3 novo tem poucas páginas e candidatos já avaliados historicamente nele; não é validação humana totalmente intocada. Referência humana é ordem de regiões expandida em palavras. Silver é fluxo automático do PDF e inclui divergências dentro das tabelas, comuns aos três métodos; as quebras absolutas não medem apenas o ordenador. Sem nova semente de treino ou recalibração dos logits.

Bootstrap: 5000 reamostras de veículos, semente 20261004, mesma função isolada da bancada. RN tem somente um veículo: seu IC agrupado é degenerado e seu Wilcoxon não permite generalização.

| Bancada | Páginas previstas | Medidas | Completa |
|---|---:|---:|---|
| validacao_silver | 15 | 15 | sim |
| golden_v4 | 44 | 44 | sim |
| golden_v3_novo | 27 | 27 | sim |
| teste_silver | 89 | 89 | sim |

Sobreposição de páginas humanas com RN: 1; com teste silver: 21. São bancadas separadas, não somar como observações independentes. Nenhuma página é treinada aqui.

Comando completo: `venv/Scripts/python.exe -B orquestracao/analises/regra_mais_modelo.py`. Repetir retoma caches por hash das fontes; `--conferir` audita sem carregar a rede. Não altera `data/`, `docs/`, o quadro ou os módulos importados. Não usa detector ao vivo, GPU ou Data Policy.

Último estado: Experimento completo; escolha congelada e tres bancadas avaliadas.

Auditoria executada: 175 páginas e 1400 ordens com unicidade/cobertura, limiar, alertas e propostas aceitas conferidos.

Inferências com histórico idêntico: 160 páginas. Tempo mediano dos scores novos/cacheados: 567,8 ms; RAM livre mínima observada entre páginas: 2403,3 MB. Esta amostragem não mede pico instantâneo de RAM.
