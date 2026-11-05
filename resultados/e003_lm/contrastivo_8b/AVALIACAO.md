# Continuidade de linguagem nas arestas de leitura

1. Exportação completa com linhas e átomos ls3 congelados; regra e candidatos importados.
2. Âncora v4 reproduzida: τ 0,985948; 6,045455 quebras/página.
3. Escores completos; escolhas restritas a golden_v4 e validação RN.
4. Golden v3 novo é externo ao ajuste atual, mas já foi consultado, inclusive nos candidatos anteriores.
5. seletiva: ajuste conservou a regra; global: ajuste conservou a regra.

Relatório gerado por `ordem_lm_arestas.py`. Números medidos em `resultados/ordem_lm/`; estimativas abaixo são fórmulas explícitas.

## Exportação

| Bancada | Páginas | Fontes | Pares | Bytes | MiB | Recall candidatos | Teto arestas-ouro |
|---|---:|---:|---:|---:|---:|---:|---:|
| golden_v4 | 44 | 3729 | 19197 | 9865651 | 9,409 | 97,78% | 98,21% |
| golden_v3_novo | 27 | 2258 | 11355 | 6752588 | 6,440 | 96,76% | 97,36% |
| teste_silver | 89 | 8942 | 43367 | 23688809 | 22,591 | 93,95% | 87,03% |
| validacao_silver | 15 | 2566 | 13201 | 6783828 | 6,470 | 95,64% | 96,67% |

Total: 87120 pares; 47090876 bytes. Exportação: 26,371 s.
Hashes SHA-256 de arquivos, fontes e páginas em `pares/MANIFESTO.json`. Arquivos do cluster contêm somente entrada automática, sem ouro.
Sobreposições silver/humanas são conservadas conforme a bancada original; bancadas não são amostras independentes somáveis.

Contexto: últimas 48 palavras, modo `caminho`; continuação: primeiras 24. Tabelas/imagens são marcadores; FIM é pontuado pelo token EOS.
O contexto acompanha a regra original e não é recalculado após intervenções. Cabeçalhos e rodapés também recebem candidatos.

## Como executar

Da raiz, um processo por vez:

```powershell
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py exportar
venv/Scripts/python.exe -B cluster/pontuar_pares_lm.py --entrada resultados/ordem_lm/pares --saida resultados/ordem_lm/escores --modelo Qwen/Qwen3-0.6B --dtype float16 --lote 4 --dispositivo cuda --bancada golden_v4 --limite-paginas 3
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-0.6B
```

Cluster Linux aarch64: copiar somente `cluster/pontuar_pares_lm.py`, `cluster/requisitos_pontuar.txt` e `pares/`. O script não importa o repositório. Não enviar anotações.

```bash
pip install -r requisitos_pontuar.txt
python -B pontuar_pares_lm.py --entrada pares --saida escores --modelo Qwen/Qwen3-8B --dtype bfloat16 --lote 8 --dispositivo cuda
# Opcional: --nsp neuralmind/bert-base-portuguese-cased
```

NSP só entra se a cabeça estiver presente no checkpoint; cabeça inicializada aleatoriamente é recusada. Fumaça local não baixa NSP.
A saída acrescenta o nome sanitizado do modelo. Ao receber `escores/<modelo>/`, executar `decodificar --escores DIR`; o mesmo código gera a avaliação completa.
Retomada por página: valida hash de pares, configuração e revisão do modelo; repara somente a última linha interrompida dos escores.

## Escore e decodificação

Causal: soma e média do logp dos tokens da continuação, sem chat template. Tokenização explícita: contexto + quebra de linha; continuação prefixada por espaço, codificada separadamente. Sem token de raciocínio ou geração. Lotes com padding à esquerda e posições explícitas; sem reuso KV entre pares.
Combinação: w_regra × indicador de sucessor original + w_geo × prior + w_lm × log-softmax(escore LM por fonte) + w_nsp × (logit IsNext − NotNext). O escore LM é o logp médio condicional ou o contraste explicitamente identificado na execução. O corretor não tinha prior escalar por candidato; usa-se sobreposição horizontal/(1 + distância vertical em alturas). FIM tem prior zero e continuação EOS, política conservada nos dois termos.
Seletiva: melhor candidato precisa vencer o sucessor original tanto no LM quanto na combinação por margem estrita; move uma unidade em raio de doze posições, preserva arestas já aceitas e cobertura. Global: recalcula melhor−segunda melhor aresta viável por fonte, fixa primeiro o maior regret, impede ciclos e grau de entrada/saída maior que um; FIM privado permite vários caminhos. Costura pela primeira unidade de cada caminho na regra. Esta é uma implementação operacional de max-regret, não reprodução certificada do artigo.
Grade predefinida: 12 configurações, descritas no JSON da avaliação. Seleção minimiza média dos deltas de quebras das duas bancadas de ajuste, com peso igual por bancada; desempata pelo maior τ. Se nenhuma configuração reduzir quebras, conserva a regra. Sem ajuste completo não há seleção. A escolha é salva em `selecao.json` antes de avaliar externos, que recebem somente as configurações escolhidas.
Oráculo: teto independente por aresta = sucessores-ouro alcançáveis presentes nos candidatos, incluindo bordas internas com adjacência preservada. É um limite otimista, pois a linha inteira também precisa estar intacta; não é teto de quebras ou τ. A ordem oracular fixa arestas-ouro realizáveis com prioridade alta e aplica a mesma cobertura/costura; sua realização pode ficar abaixo do teto independente. Ouro nunca entra nos decoders automáticos.
Métricas oficiais importadas: τ de palavras, quebras e sucessor de linhas. Acurácia de aresta micro = sucessores-ouro de linhas inteiras recuperados / todas as transições-ouro entre linhas; inclui bordas internas aos átomos, exclui FIM. Reporta-se também sucessor macro por página. Não há comparabilidade direta com percentuais de outro corpus/artigo.
Reparos/regressões contam sucessores-ouro recuperados/perdidos, não diferenças de quebras de palavras. Diagnóstico mantém categorias das transições-ouro do corretor. IC percentil por veículo e Wilcoxon bilateral Pratt sobre diferenças médias por veículo; parâmetros de reamostragem importados da bancada. RN tem um veículo: IC degenerado e teste não informativo.

## Execução pontuada

Modelo: `Qwen/Qwen3-8B`; revisão: `None`.
Escore: **contrastivo**. Subtrai logp_soma marginal e divide pelo mesmo n_tokens antes do log-softmax por fonte. FIM também subtrai a marginal de EOS.
Estado: completo.
Escolhas congeladas: `{"seletiva": "regra", "global": "regra"}`.

| Bancada | Cobertura |
|---|---:|
| golden_v4 | 44/44 |
| validacao_silver | 15/15 |
| golden_v3_novo | 27/27 |
| teste_silver | 89/89 |

Marginais: `C:\Users\pedro\dev\tcc-ri-reading-order\resultados\ordem_lm\escores_marginal\Qwen_Qwen3-8B`. Contexto vazio contém somente BOS; continuação idêntica à condicional, inclusive espaço prefixado.
Revisão resolvida ausente em escores legados; identidade exata dos pesos não certificada.

Pontuação: 175 páginas; 4617,166 s; média 26,384 s/página; inicialização (download/carga) 456,457 s.
Memória máxima observada (MiB): `{"cuda_pico_alocado_mb": 17683.947265625, "cuda_pico_reservado_mb": 30820.0, "pico_rss_mb": 5649.546875}`.
O pico RSS inclui carga; tempo por página inclui tokenização e transferências, exclui carga e download. Memória CUDA é alocada/reservada pelo PyTorch.
Pontuação marginal adicional: 274,737 s; carga 138,833 s. Soma dos tempos de pontuação dos dois termos: 4891,904 s. O custo marginal é pago uma vez por destino/página e pode ser reutilizado entre configurações.

| Bancada | Método | n | Quebras/pág [IC] | τ [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Arestas certas/ouro | Reparos/regressões | Páginas melhor/igual/pior (quebras) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| golden_v4 | regra | 44 | 6,045 [4,023; 8,887] | 0,985948 [0,973495; 0,995020] | 0,948129 [0,913551; 0,972411] | 0,927240 [0,878100; 0,960833] | 4448/4685 (94,94%) | 0/0 | 0/44/0 |
| golden_v4 | oraculo | 44 | 2,114 [1,277; 3,239] | 0,883272 [0,792640; 0,960416] | 0,974731 [0,947632; 0,991869] | 0,975283 [0,955663; 0,989244] | 4613/4685 (98,46%) | 165/0 | 33/11/0 |
| validacao_silver | regra | 15 | 16,667 [16,667; 16,667] | 0,957218 [0,957218; 0,957218] | 0,952328 [0,952328; 0,952328] | 0,910859 [0,910859; 0,910859] | 4762/5012 (95,01%) | 0/0 | 0/15/0 |
| validacao_silver | oraculo | 15 | 10,867 [10,867; 10,867] | 0,828194 [0,828194; 0,828194] | 0,972452 [0,972452; 0,972452] | 0,947417 [0,947417; 0,947417] | 4849/5012 (96,75%) | 87/0 | 11/4/0 |
| golden_v3_novo | regra | 27 | 9,222 [4,900; 12,867] | 0,959557 [0,915350; 0,997056] | 0,928415 [0,898586; 0,965853] | 0,911301 [0,880648; 0,935563] | 2674/2912 (91,83%) | 0/0 | 0/27/0 |
| golden_v3_novo | oraculo | 27 | 3,444 [1,682; 5,100] | 0,913020 [0,832075; 0,996596] | 0,963606 [0,941882; 0,988083] | 0,960830 [0,929214; 0,978231] | 2825/2912 (97,01%) | 151/0 | 21/6/0 |
| teste_silver | regra | 89 | 27,449 [22,184; 32,316] | 0,959565 [0,889505; 0,998435] | 0,825401 [0,729346; 0,898717] | 0,840212 [0,770803; 0,940858] | 12501/14848 (84,19%) | 0/0 | 0/89/0 |
| teste_silver | oraculo | 89 | 22,787 [15,231; 30,895] | 0,947327 [0,820892; 0,993001] | 0,851524 [0,744445; 0,938936] | 0,869017 [0,787942; 0,971826] | 12909/14848 (86,94%) | 408/0 | 62/27/0 |

| Bancada | Método | Métrica | Δ [IC95 veículo] | p Wilcoxon veículo |
|---|---|---|---:|---:|
| golden_v4 | oraculo | quebras | -3,931818 [-5,790802; -2,565190] | 0,000012 |
| golden_v4 | oraculo | tau | -0,102676 [-0,192367; -0,024131] | 0,328620 |
| golden_v4 | oraculo | fid12 | 0,026603 [0,017294; 0,036633] | 0,000022 |
| golden_v4 | oraculo | sucessor_linhas | 0,048043 [0,026378; 0,078323] | 0,000012 |
| validacao_silver | oraculo | quebras | -5,800000 [-5,800000; -5,800000] | 0,317311 |
| validacao_silver | oraculo | tau | -0,129024 [-0,129024; -0,129024] | 0,317311 |
| validacao_silver | oraculo | fid12 | 0,020124 [0,020124; 0,020124] | 0,317311 |
| validacao_silver | oraculo | sucessor_linhas | 0,036558 [0,036558; 0,036558] | 0,317311 |
| golden_v3_novo | oraculo | quebras | -5,777778 [-8,644462; -2,750000] | 0,005857 |
| golden_v3_novo | oraculo | tau | -0,046537 [-0,109590; -0,000093] | 0,358326 |
| golden_v3_novo | oraculo | fid12 | 0,035192 [0,019540; 0,048422] | 0,005857 |
| golden_v3_novo | oraculo | sucessor_linhas | 0,049529 [0,032862; 0,065438] | 0,005857 |
| teste_silver | oraculo | quebras | -4,662921 [-13,384615; -1,421053] | 0,108809 |
| teste_silver | oraculo | tau | -0,012238 [-0,068613; 0,000244] | 0,285049 |
| teste_silver | oraculo | fid12 | 0,026123 [0,015099; 0,047067] | 0,108809 |
| teste_silver | oraculo | sucessor_linhas | 0,028805 [0,017139; 0,039731] | 0,108809 |

### Diagnóstico por categoria

| Bancada | Método | Categoria | Certas/ouro | Reparos/regressões |
|---|---|---|---:|---:|
| golden_v4 | regra | Continuação na mesma coluna | 3101/3149 | 0/0 |
| golden_v4 | regra | Fim de coluna → topo da próxima | 10/13 | 0/0 |
| golden_v4 | regra | Entrada/saída de tabela ou imagem | 52/60 | 0/0 |
| golden_v4 | regra | Salto ou fronteira de elemento transversal | 8/26 | 0/0 |
| golden_v4 | regra | Cabeçalho/rodapé/marca marginal | 82/213 | 0/0 |
| golden_v4 | regra | Outro | 1195/1224 | 0/0 |
| golden_v4 | oraculo | Continuação na mesma coluna | 3136/3149 | 35/0 |
| golden_v4 | oraculo | Fim de coluna → topo da próxima | 10/13 | 0/0 |
| golden_v4 | oraculo | Entrada/saída de tabela ou imagem | 55/60 | 3/0 |
| golden_v4 | oraculo | Salto ou fronteira de elemento transversal | 19/26 | 11/0 |
| golden_v4 | oraculo | Cabeçalho/rodapé/marca marginal | 177/213 | 95/0 |
| golden_v4 | oraculo | Outro | 1216/1224 | 21/0 |
| validacao_silver | regra | Continuação na mesma coluna | 2224/2245 | 0/0 |
| validacao_silver | regra | Fim de coluna → topo da próxima | 3/3 | 0/0 |
| validacao_silver | regra | Entrada/saída de tabela ou imagem | 10/18 | 0/0 |
| validacao_silver | regra | Salto ou fronteira de elemento transversal | 6/13 | 0/0 |
| validacao_silver | regra | Cabeçalho/rodapé/marca marginal | 46/132 | 0/0 |
| validacao_silver | regra | Outro | 2473/2601 | 0/0 |
| validacao_silver | oraculo | Continuação na mesma coluna | 2243/2245 | 19/0 |
| validacao_silver | oraculo | Fim de coluna → topo da próxima | 3/3 | 0/0 |
| validacao_silver | oraculo | Entrada/saída de tabela ou imagem | 12/18 | 2/0 |
| validacao_silver | oraculo | Salto ou fronteira de elemento transversal | 9/13 | 3/0 |
| validacao_silver | oraculo | Cabeçalho/rodapé/marca marginal | 96/132 | 50/0 |
| validacao_silver | oraculo | Outro | 2486/2601 | 13/0 |
| golden_v3_novo | regra | Continuação na mesma coluna | 1767/1882 | 0/0 |
| golden_v3_novo | regra | Fim de coluna → topo da próxima | 6/8 | 0/0 |
| golden_v3_novo | regra | Entrada/saída de tabela ou imagem | 57/66 | 0/0 |
| golden_v3_novo | regra | Salto ou fronteira de elemento transversal | 5/7 | 0/0 |
| golden_v3_novo | regra | Cabeçalho/rodapé/marca marginal | 46/87 | 0/0 |
| golden_v3_novo | regra | Outro | 793/862 | 0/0 |
| golden_v3_novo | oraculo | Continuação na mesma coluna | 1858/1882 | 91/0 |
| golden_v3_novo | oraculo | Fim de coluna → topo da próxima | 6/8 | 0/0 |
| golden_v3_novo | oraculo | Entrada/saída de tabela ou imagem | 64/66 | 7/0 |
| golden_v3_novo | oraculo | Salto ou fronteira de elemento transversal | 5/7 | 0/0 |
| golden_v3_novo | oraculo | Cabeçalho/rodapé/marca marginal | 64/87 | 18/0 |
| golden_v3_novo | oraculo | Outro | 828/862 | 35/0 |
| teste_silver | regra | Continuação na mesma coluna | 6960/7145 | 0/0 |
| teste_silver | regra | Fim de coluna → topo da próxima | 28/33 | 0/0 |
| teste_silver | regra | Entrada/saída de tabela ou imagem | 84/126 | 0/0 |
| teste_silver | regra | Salto ou fronteira de elemento transversal | 114/183 | 0/0 |
| teste_silver | regra | Cabeçalho/rodapé/marca marginal | 127/307 | 0/0 |
| teste_silver | regra | Outro | 5188/7054 | 0/0 |
| teste_silver | oraculo | Continuação na mesma coluna | 7121/7145 | 161/0 |
| teste_silver | oraculo | Fim de coluna → topo da próxima | 29/33 | 1/0 |
| teste_silver | oraculo | Entrada/saída de tabela ou imagem | 90/126 | 6/0 |
| teste_silver | oraculo | Salto ou fronteira de elemento transversal | 152/183 | 38/0 |
| teste_silver | oraculo | Cabeçalho/rodapé/marca marginal | 193/307 | 66/0 |
| teste_silver | oraculo | Outro | 5324/7054 | 136/0 |

### Grade — somente ajuste

| Configuração | Δ quebras médio v4/RN | Δ τ médio v4/RN |
|---|---:|---:|
| seletiva_r0.5_t0.5 | 85,946212 | -0,030588 |
| seletiva_r0.5_t1.5 | 71,575000 | -0,023190 |
| seletiva_r1.0_t0.5 | 79,898485 | -0,026936 |
| seletiva_r1.0_t1.5 | 61,515152 | -0,014685 |
| seletiva_r2.0_t0.5 | 61,515152 | -0,014685 |
| seletiva_r2.0_t1.5 | 41,686364 | -0,010058 |
| global_r0.5_n0.0 | 82,617424 | -0,273881 |
| global_r0.5_n0.2 | 82,617424 | -0,273881 |
| global_r1.0_n0.0 | 62,160606 | -0,223511 |
| global_r1.0_n0.2 | 62,160606 | -0,223511 |
| global_r2.0_n0.0 | 17,726515 | -0,158124 |
| global_r2.0_n0.2 | 17,726515 | -0,158124 |

Avaliação detalhada em `avaliacao.json` junto a este relatório quando --saida é informado; predições em `pred/`, somente `page_id` e `ordem`. Sem --saida, a ablação mantém os destinos históricos.

### Leitura dos resultados

seletiva: ajuste conservou a regra; global: ajuste conservou a regra.
Avaliar também os contrastes de τ: reduzir quebras não garante preservar a ordem global. Seleção e testes sem correção de multiplicidade são exploratórios; o Golden v4 já foi usado no desenvolvimento da regra, e golden_v3_novo foi consultado antes. A referência silver é o fluxo PDF, com limitações em tabelas. Os percentuais não demonstram reprodução dos resultados de outro corpus.

## Limite dos candidatos

O nível solicitado foi mantido sem ampliar candidatos usando resultados externos. Recall abaixo de 95%: teste_silver = 93,95%. O denominador de recall contém bordas externas alcançáveis entre unidades; o teto de arestas usa todas as transições-ouro de linhas, incluindo as internas e inalcançáveis, por isso pode ser menor.

## Estimativa de tempo no cluster

Planejamento, não benchmark: operações aproximadas = 2 × parâmetros × tokens processados. São incluídos contexto e continuação de cada par, pois o script usa padding e não compartilha KV. Desconsidera padding, atenção, tokenização, I/O e download; a vazão efetiva assumida deve absorver parte desses custos. A GPU de 80 GB não foi identificada/medida.
Tokens supostos: 6923488–11539148 = 4615659 palavras × 1,5–2,5 tokens/palavra. Vazão efetiva assumida: 20–80 TFLOP/s. Faixa deliberadamente ampla, não extrapolada da RTX.

| Modelo bf16 | Memória apenas pesos (GB decimais) | Horas estimadas |
|---|---:|---:|
| Qwen/Qwen3-8B (aprox.) | 16,0 | 0,38–2,56 |
| Modelo ~30B | 60,0 | 1,44–9,62 |

Pesos de ~30B deixam memória para ativações/KV em 80 GB, mas o lote pode precisar cair. O log de cada página permite recalcular ETA real após o primeiro arquivo. Modelo, revisão, tokenizer, dtype e lote devem permanecer fixos na retomada.

## Números que dependem dos escores integrais do cluster

- Tempo e memória reais dos modelos grandes, tokens reais e custo total.
- Configurações escolhidas apenas em v4/RN, incluindo eventual conservação da regra.
- Quebras/página, τ, sucessor macro e acurácia micro de aresta nas bancadas completas.
- Reparos/regressões e diagnóstico por continuação, troca de coluna, margens e demais categorias.
- IC e Wilcoxon por veículo contra a regra, cobertura completa e distância ao oráculo realizado.
- Evidência sobre redução de quebras fora do ajuste; nenhum resultado da fumaça responde a essa pergunta.
