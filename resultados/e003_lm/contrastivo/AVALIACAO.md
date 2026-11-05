# Continuidade de linguagem nas arestas de leitura

1. Exportação completa com linhas e átomos ls3 congelados; regra e candidatos importados.
2. Âncora v4 reproduzida: τ 0,985948; 6,045455 quebras/página.
3. Pontuação integral no cluster ainda pendente; resultados parciais são apenas fumaça.
4. Golden v3 novo é externo ao ajuste atual, mas já foi consultado, inclusive nos candidatos anteriores.
5. A pergunta sobre ganho fora do ajuste permanece aberta até a pontuação e avaliação completas.

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

Modelo: `Qwen/Qwen3-0.6B`; revisão: `c1899de289a04d12100db370d81485cdf75e47ca`.
Escore: **contrastivo**. Subtrai logp_soma marginal e divide pelo mesmo n_tokens antes do log-softmax por fonte. FIM também subtrai a marginal de EOS.
Estado: FUMAÇA/PARCIAL — sem conclusões nem seleção de pesos.
Configurações predefinidas da fumaça, sem escolha: `{"seletiva": "seletiva_r0.5_t0.5", "global": "global_r0.5_n0.0"}`.

| Bancada | Cobertura |
|---|---:|
| golden_v4 | 3/44 |
| validacao_silver | 0/15 |
| golden_v3_novo | 0/27 |
| teste_silver | 0/89 |

Marginais: `C:\Users\pedro\dev\tcc-ri-reading-order\resultados\e003_lm\escores_marginal\Qwen_Qwen3-0.6B`. Contexto vazio contém somente BOS; continuação idêntica à condicional, inclusive espaço prefixado.

Pontuação: 3 páginas; 578,924 s; média 192,975 s/página; inicialização (download/carga) 51,265 s.
Memória máxima observada (MiB): `{"pico_rss_mb": 4193.97265625, "rss_mb": 3628.16796875}`.
O pico RSS inclui carga; tempo por página inclui tokenização e transferências, exclui carga e download. Memória CUDA é alocada/reservada pelo PyTorch.
Pontuação marginal adicional: 36,950 s; carga 22,691 s. Soma dos tempos de pontuação dos dois termos: 615,874 s. O custo marginal é pago uma vez por destino/página e pode ser reutilizado entre configurações.

| Página pontuada | Pares | Segundos | Pico GPU alocado (MiB) |
|---|---:|---:|---:|
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | 271 | 418,022 | — |
| `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20` | 71 | 61,751 | — |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | 81 | 99,151 | — |

| Bancada | Método | n | Quebras/pág [IC] | τ [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Arestas certas/ouro | Reparos/regressões | Páginas melhor/igual/pior (quebras) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| golden_v4 | regra | 3 | 3,333 [2,500; 5,000] | 0,985223 [0,956637; 0,999515] | 0,861104 [0,631579; 0,975866] | 0,824242 [0,545455; 0,963636] | 72/81 (88,89%) | 0/0 | 0/3/0 |
| golden_v4 | seletiva_r0.5_t0.5 | 3 | 25,000 [8,000; 33,500] | 0,947644 [0,945263; 0,952406] | 0,313772 [0,312763; 0,315789] | 0,161616 [0,106061; 0,272727] | 12/81 (14,81%) | 0/60 | 0/0/3 |
| golden_v4 | global_r0.5_n0.0 | 3 | 23,000 [7,000; 31,000] | 0,800624 [0,786605; 0,828662] | 0,358639 [0,228070; 0,423924] | 0,280808 [0,239394; 0,363636] | 17/81 (20,99%) | 2/57 | 0/0/3 |
| golden_v4 | oraculo | 3 | 1,667 [1,500; 2,000] | 0,977981 [0,949233; 0,992355] | 0,899420 [0,719298; 0,989480] | 0,921212 [0,818182; 0,972727] | 76/81 (93,83%) | 4/0 | 2/1/0 |

| Bancada | Método | Métrica | Δ [IC95 veículo] | p Wilcoxon veículo |
|---|---|---|---:|---:|
| golden_v4 | seletiva_r0.5_t0.5 | quebras | 21,666667 [3,000000; 31,000000] | 0,179712 |
| golden_v4 | seletiva_r0.5_t0.5 | tau | -0,037578 [-0,054252; -0,004231] | 0,179712 |
| golden_v4 | seletiva_r0.5_t0.5 | fid12 | -0,547332 [-0,663104; -0,315789] | 0,179712 |
| golden_v4 | seletiva_r0.5_t0.5 | sucessor_linhas | -0,662626 [-0,857576; -0,272727] | 0,179712 |
| golden_v4 | global_r0.5_n0.0 | quebras | 19,666667 [2,000000; 28,500000] | 0,179712 |
| golden_v4 | global_r0.5_n0.0 | tau | -0,184598 [-0,212910; -0,127975] | 0,179712 |
| golden_v4 | global_r0.5_n0.0 | fid12 | -0,502465 [-0,551943; -0,403509] | 0,179712 |
| golden_v4 | global_r0.5_n0.0 | sucessor_linhas | -0,543434 [-0,724242; -0,181818] | 0,179712 |
| golden_v4 | oraculo | quebras | -1,666667 [-3,000000; -1,000000] | 0,179712 |
| golden_v4 | oraculo | tau | -0,007241 [-0,007403; -0,007160] | 0,179712 |
| golden_v4 | oraculo | fid12 | 0,038316 [0,013614; 0,087719] | 0,179712 |
| golden_v4 | oraculo | sucessor_linhas | 0,096970 [0,009091; 0,272727] | 0,179712 |

### Diagnóstico por categoria

| Bancada | Método | Categoria | Certas/ouro | Reparos/regressões |
|---|---|---|---:|---:|
| golden_v4 | regra | Continuação na mesma coluna | 64/66 | 0/0 |
| golden_v4 | regra | Fim de coluna → topo da próxima | 0/0 | 0/0 |
| golden_v4 | regra | Entrada/saída de tabela ou imagem | 1/1 | 0/0 |
| golden_v4 | regra | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| golden_v4 | regra | Cabeçalho/rodapé/marca marginal | 3/10 | 0/0 |
| golden_v4 | regra | Outro | 4/4 | 0/0 |
| golden_v4 | seletiva_r0.5_t0.5 | Continuação na mesma coluna | 9/66 | 0/55 |
| golden_v4 | seletiva_r0.5_t0.5 | Fim de coluna → topo da próxima | 0/0 | 0/0 |
| golden_v4 | seletiva_r0.5_t0.5 | Entrada/saída de tabela ou imagem | 0/1 | 0/1 |
| golden_v4 | seletiva_r0.5_t0.5 | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| golden_v4 | seletiva_r0.5_t0.5 | Cabeçalho/rodapé/marca marginal | 1/10 | 0/2 |
| golden_v4 | seletiva_r0.5_t0.5 | Outro | 2/4 | 0/2 |
| golden_v4 | global_r0.5_n0.0 | Continuação na mesma coluna | 11/66 | 0/53 |
| golden_v4 | global_r0.5_n0.0 | Fim de coluna → topo da próxima | 0/0 | 0/0 |
| golden_v4 | global_r0.5_n0.0 | Entrada/saída de tabela ou imagem | 1/1 | 0/0 |
| golden_v4 | global_r0.5_n0.0 | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| golden_v4 | global_r0.5_n0.0 | Cabeçalho/rodapé/marca marginal | 3/10 | 2/2 |
| golden_v4 | global_r0.5_n0.0 | Outro | 2/4 | 0/2 |
| golden_v4 | oraculo | Continuação na mesma coluna | 64/66 | 0/0 |
| golden_v4 | oraculo | Fim de coluna → topo da próxima | 0/0 | 0/0 |
| golden_v4 | oraculo | Entrada/saída de tabela ou imagem | 1/1 | 0/0 |
| golden_v4 | oraculo | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| golden_v4 | oraculo | Cabeçalho/rodapé/marca marginal | 7/10 | 4/0 |
| golden_v4 | oraculo | Outro | 4/4 | 0/0 |

Avaliação detalhada em `avaliacao.json` junto a este relatório quando --saida é informado; predições em `pred/`, somente `page_id` e `ordem`. Sem --saida, a ablação mantém os destinos históricos.

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
