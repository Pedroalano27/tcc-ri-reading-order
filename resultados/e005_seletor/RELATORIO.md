1. Âncora reproduzida: τ 0,985948; 6,045455 quebras/página.
2. CV conjunta: 160 observações, 139 páginas distintas, 27 veículos; leave-one-vehicle-out.
3. Veredito E005: NÃO GO nos seletores executados; manter o híbrido 67 congelado.
4. Métodos roteáveis: regra, layoutreader_pronto, grafo_e004; E004: 2. Veredito do cartão E004: NÃO GO.
5. RN: 0 páginas com todos os candidatos; ausências explícitas, sem executar ordenadores.
6. Golden_v3_novo já foi consultado em rodadas anteriores; análise exploratória, sem abrir ou avaliar teste cego.

# E005 — seletor de método por página

## Protocolo congelado e alcance

Todos os números e este texto são escritos pelo script. Fontes, versões, parâmetros e hashes em `cache/manifesto.json`; resultados completos, folds, contrastes por veículo e classes em `cache/estado.json`. CPU, um processo, quatro threads, num_workers=0. Nenhum PDF, anotação original ou dado do parceiro é aberto.

A régua é importada de `corretor_de_transicoes.preparar_avaliacao/medir`, `bancada_ordenadores` e `erros_ponta_a_ponta`. Mantêm-se linhas + átomos ls3, expansão interna canônica e todas as palavras. Quebras/1.000 usa o denominador da régua existente (palavras-ouro); não é apresentado como novo denominador de transições. Fid12 é integral. Features usam somente dados automáticos e concordância dos sucessores (incluindo FIM). A partição geométrica e os desempates usam `ordem_entrada`, random.Random(f'entrada-{page_id}'). Alvo é o menor número de quebras; empate escolhe regra, depois a ordem fixa dos candidatos, sem desempate por τ.

A CV conjunta solicitada reúne as bancadas de desenvolvimento, com parâmetros fixados no código antes da execução. Nenhum parâmetro, limiar, semente ou checkpoint é escolhido em v3/silver. Rótulos desses conjuntos entram no treino dos outros folds nesta análise conjunta, portanto seus resultados conjuntos NÃO são transferência externa independente. A análise adicional `transferencia_ajuste` treina só em golden_v4 + RN disponível e exclui o veículo avaliado também desse treino. Nenhum fold vê qualquer página ou PDF do veículo de destino, inclusive suas ocorrências nas outras bancadas.

Sobreposição histórica preservada: 21 observações repetem page_id entre bancadas. O agregado usa as observações solicitadas (mesmo peso por observação); não são amostras independentes. Bootstrap e folds agrupam todas as ocorrências pelo mesmo veículo. Há referências humanas/silver diferentes para parte dessas páginas; isso pode produzir rótulos conflitantes.

IC95 percentil por veículo: 5000 reamostras, mesma função da bancada. Wilcoxon bilateral Pratt sobre diferenças médias por veículo, descritivo; nenhuma decisão depende de p. Semente primária 42 congelada; as demais medem sensibilidade, sem selecionar semente. Critério do cartão: Δ quebras < 0 contra híbrido 67 na CV conjunta, IC95 inteiro < 0, nenhuma bancada piorando > 0,5 quebra/página. Não se acrescenta o critério geral de 10% ao cartão E005.

E004: 2. Veredito do cartão E004: NÃO GO. Por solicitação explícita nesta retomada, a seleção congelada do grafo concluído entra como candidato de roteamento mesmo se seu critério individual resultar NÃO GO. Isso testa seleção por página, sem mudar o critério do E005 ou adotar o grafo isoladamente. E004 pendente continua excluído, sem substituição por estimativa.

Dependências indisponíveis: nenhuma. Não se substitui LightGBM por outro algoritmo. Depois de disponibilizar a dependência no venv, repetir o comando refaz a comparação com a nova versão de ambiente registrada.

Configurações fixas: `{"arvore_rasa": {"max_depth": 3, "min_samples_leaf": 5}, "logistica": {"C": 1.0, "max_iter": 2000, "solver": "lbfgs"}, "lightgbm": {"n_estimators": 50, "num_leaves": 7, "max_depth": 3, "min_child_samples": 10, "learning_rate": 0.05, "reg_lambda": 1.0, "n_jobs": 4, "verbosity": -1, "deterministic": true, "force_col_wise": true}}`. Sem pesos de classe, sem ajuste de limiar de probabilidade e sem busca de hiperparâmetros. StandardScaler da logística é ajustado apenas no treino de cada fold. A árvore tem profundidade máxima 3; LightGBM tem 7 folhas e 50 árvores. Classes ausentes no treino não podem ser previstas; fold de uma classe usa a constante correspondente.

## CV conjunta — agregado exploratório

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| regra | 160 | 0,966819 | 18,487500 | 30,922428 | 0,876535 | 0,876141 |
| layoutreader_pronto | 160 | 0,935459 | 25,175000 | 29,376999 | 0,875321 | 0,876222 |
| grafo_e004 | 160 | 0,941186 | 15,525000 | 27,583527 | 0,890542 | 0,895815 |
| hibrido67 | 160 | 0,964750 | 17,443750 | 27,986093 | 0,890618 | 0,896594 |
| arvore_rasa | 160 | 0,958702 | 21,225000 | 28,789554 | 0,882954 | 0,882495 |
| logistica | 160 | 0,949458 | 15,156250 | 25,910626 | 0,899015 | 0,902764 |
| lightgbm | 160 | 0,951670 | 22,500000 | 29,615208 | 0,879592 | 0,882056 |
| oraculo_roteamento | 160 | 0,959470 | 13,137500 | 23,178197 | 0,911312 | 0,919702 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra | regra | 160 | 0,000 [0,000; 0,000] | 1,000000 | 0/160/0 | 0/0 |
| regra | hibrido67 | 160 | 1,044 [0,381; 1,748] | 0,008723 | 9/114/37 | 32/199 |
| layoutreader_pronto | regra | 160 | 6,688 [-3,558; 28,486] | 0,838055 | 76/41/43 | 883/1950 |
| layoutreader_pronto | hibrido67 | 160 | 7,731 [-2,059; 29,133] | 0,841743 | 39/87/34 | 684/1918 |
| grafo_e004 | regra | 160 | -2,962 [-5,645; -1,297] | 0,000152 | 64/89/7 | 505/39 |
| grafo_e004 | hibrido67 | 160 | -1,919 [-4,983; -0,473] | 0,048288 | 51/73/36 | 414/115 |
| hibrido67 | regra | 160 | -1,044 [-1,748; -0,381] | 0,008723 | 37/114/9 | 199/32 |
| hibrido67 | hibrido67 | 160 | 0,000 [0,000; 0,000] | 1,000000 | 0/160/0 | 0/0 |
| arvore_rasa | regra | 160 | 2,737 [-4,866; 19,765] | 0,048524 | 52/90/18 | 723/1165 |
| arvore_rasa | hibrido67 | 160 | 3,781 [-3,280; 20,473] | 0,337326 | 34/98/28 | 598/1207 |
| logistica | regra | 160 | -3,331 [-6,069; 0,741] | 0,003062 | 72/66/22 | 845/308 |
| logistica | hibrido67 | 160 | -2,288 [-4,962; 1,635] | 0,099605 | 52/78/30 | 712/342 |
| lightgbm | regra | 160 | 4,013 [-2,526; 20,296] | 0,110231 | 61/67/32 | 574/1221 |
| lightgbm | hibrido67 | 160 | 5,056 [-1,057; 20,923] | 0,892610 | 36/89/35 | 413/1227 |
| oraculo_roteamento | regra | 160 | -5,350 [-7,214; -2,946] | 0,000009 | 95/65/0 | 897/53 |
| oraculo_roteamento | hibrido67 | 160 | -4,306 [-6,223; -1,875] | 0,000030 | 66/94/0 | 727/50 |

Critério por seletor: `{"arvore_rasa": {"delta_negativo": false, "ic95_abaixo_zero": false, "nenhuma_bancada_piora_mais_05": false, "delta_por_bancada": {"golden_v4": 0.38636363636363635, "golden_v3_novo": 6.62962962962963, "teste_silver": 4.595505617977528}, "go": false}, "logistica": {"delta_negativo": true, "ic95_abaixo_zero": false, "nenhuma_bancada_piora_mais_05": false, "delta_por_bancada": {"golden_v4": 0.8409090909090909, "golden_v3_novo": -0.2222222222222222, "teste_silver": -4.46067415730337}, "go": false}, "lightgbm": {"delta_negativo": false, "ic95_abaixo_zero": false, "nenhuma_bancada_piora_mais_05": false, "delta_por_bancada": {"golden_v4": 1.0, "golden_v3_novo": 6.814814814814815, "teste_silver": 6.52808988764045}, "go": false}}`.

## golden_v4 — CV conjunta

Total: 44 páginas; ausências: `{}`. Médias parciais têm o n explícito e ficam nulas no resumo de registro.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| regra | 44 | 0,985948 | 6,045455 | 11,884752 | 0,948129 | 0,927240 |
| layoutreader_pronto | 44 | 0,913071 | 18,386364 | 11,087975 | 0,935197 | 0,927182 |
| grafo_e004 | 44 | 0,937961 | 3,613636 | 7,777795 | 0,963953 | 0,955269 |
| hibrido67 | 44 | 0,979738 | 5,136364 | 6,041242 | 0,973419 | 0,966143 |
| arvore_rasa | 44 | 0,974384 | 5,522727 | 10,649109 | 0,952489 | 0,941221 |
| logistica | 44 | 0,977009 | 5,977273 | 7,481117 | 0,967610 | 0,958207 |
| lightgbm | 44 | 0,964467 | 6,136364 | 8,250404 | 0,961764 | 0,953450 |
| oraculo_roteamento | 44 | 0,952256 | 2,659091 | 3,552573 | 0,985859 | 0,982017 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra | regra | 44 | 0,000 [0,000; 0,000] | 1,000000 | 0/44/0 | 0/0 |
| regra | hibrido67 | 44 | 0,909 [0,095; 1,776] | 0,022323 | 4/24/16 | 16/58 |
| layoutreader_pronto | regra | 44 | 12,341 [-0,637; 37,951] | 0,875629 | 24/6/14 | 155/693 |
| layoutreader_pronto | hibrido67 | 44 | 13,250 [0,405; 38,514] | 0,599871 | 8/26/10 | 97/677 |
| grafo_e004 | regra | 44 | -2,432 [-4,140; -1,163] | 0,000513 | 20/22/2 | 112/7 |
| grafo_e004 | hibrido67 | 44 | -1,523 [-3,500; -0,075] | 0,069212 | 17/10/17 | 107/44 |
| hibrido67 | regra | 44 | -0,909 [-1,776; -0,095] | 0,022323 | 16/24/4 | 58/16 |
| hibrido67 | hibrido67 | 44 | 0,000 [0,000; 0,000] | 1,000000 | 0/44/0 | 0/0 |
| arvore_rasa | regra | 44 | -0,523 [-1,977; 1,426] | 0,038085 | 15/24/5 | 116/96 |
| arvore_rasa | hibrido67 | 44 | 0,386 [-1,140; 2,295] | 0,363738 | 11/20/13 | 96/118 |
| logistica | regra | 44 | -0,068 [-3,578; 5,140] | 0,015639 | 18/22/4 | 130/119 |
| logistica | hibrido67 | 44 | 0,841 [-2,632; 5,884] | 0,173749 | 13/20/11 | 106/137 |
| lightgbm | regra | 44 | 0,091 [-1,790; 2,581] | 0,277635 | 16/19/9 | 129/136 |
| lightgbm | hibrido67 | 44 | 1,000 [-0,750; 3,191] | 0,950235 | 9/21/14 | 97/146 |
| oraculo_roteamento | regra | 44 | -3,386 [-5,000; -2,131] | 0,000012 | 31/13/0 | 153/11 |
| oraculo_roteamento | hibrido67 | 44 | -2,477 [-4,233; -1,233] | 0,000098 | 18/26/0 | 109/9 |

Reparos/regressões de sucessores por classe (regra; híbrido67):

| Método | Classe | vs regra | vs híbrido67 |
|---|---|---:|---:|
| arvore_rasa | Continuação na mesma coluna | 33/77 | 28/78 |
| arvore_rasa | Fim de coluna → topo da próxima | 0/1 | 0/1 |
| arvore_rasa | Entrada/saída de tabela ou imagem | 0/9 | 6/5 |
| arvore_rasa | Salto ou fronteira de elemento transversal | 14/1 | 14/1 |
| arvore_rasa | Cabeçalho/rodapé/marca marginal | 50/6 | 38/31 |
| arvore_rasa | Outro | 19/2 | 10/2 |
| logistica | Continuação na mesma coluna | 33/108 | 28/109 |
| logistica | Fim de coluna → topo da próxima | 0/2 | 0/2 |
| logistica | Entrada/saída de tabela ou imagem | 0/1 | 11/2 |
| logistica | Salto ou fronteira de elemento transversal | 12/2 | 12/2 |
| logistica | Cabeçalho/rodapé/marca marginal | 65/1 | 44/17 |
| logistica | Outro | 20/5 | 11/5 |
| lightgbm | Continuação na mesma coluna | 33/109 | 28/110 |
| lightgbm | Fim de coluna → topo da próxima | 0/1 | 0/1 |
| lightgbm | Entrada/saída de tabela ou imagem | 0/10 | 6/6 |
| lightgbm | Salto ou fronteira de elemento transversal | 12/2 | 12/2 |
| lightgbm | Cabeçalho/rodapé/marca marginal | 66/7 | 42/20 |
| lightgbm | Outro | 18/7 | 9/7 |
| oraculo_roteamento | Continuação na mesma coluna | 40/3 | 34/3 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 0/0 | 0/0 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 1/4 | 8/1 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 12/0 | 12/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 80/2 | 44/3 |
| oraculo_roteamento | Outro | 20/2 | 11/2 |

## validacao_silver — CV conjunta

Total: 15 páginas; ausências: `{"layoutreader_pronto_sem_predicao": 15}`. Médias parciais têm o n explícito e ficam nulas no resumo de registro.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| regra | 15 | 0,957218 | 16,666667 | 10,284740 | 0,952328 | 0,910859 |
| layoutreader_pronto | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| grafo_e004 | 15 | 0,686666 | 9,466667 | 6,131847 | 0,970249 | 0,947916 |
| hibrido67 | 13 | 0,958544 | 17,846154 | 9,553831 | 0,955769 | 0,916132 |
| arvore_rasa | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| logistica | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| lightgbm | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| oraculo_roteamento | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra | regra | 15 | 0,000 [0,000; 0,000] | 1,000000 | 0/15/0 | 0/0 |
| regra | hibrido67 | 13 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 |
| grafo_e004 | regra | 15 | -7,200 [-7,200; -7,200] | 0,317311 | 10/5/0 | 109/1 |
| grafo_e004 | hibrido67 | 13 | -8,154 [-8,154; -8,154] | 0,317311 | 9/4/0 | 107/1 |
| hibrido67 | regra | 13 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 |
| hibrido67 | hibrido67 | 13 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 |

Reparos/regressões de sucessores por classe (regra; híbrido67):

| Método | Classe | vs regra | vs híbrido67 |
|---|---|---:|---:|
| arvore_rasa | Continuação na mesma coluna | indisponível | indisponível |
| arvore_rasa | Fim de coluna → topo da próxima | indisponível | indisponível |
| arvore_rasa | Entrada/saída de tabela ou imagem | indisponível | indisponível |
| arvore_rasa | Salto ou fronteira de elemento transversal | indisponível | indisponível |
| arvore_rasa | Cabeçalho/rodapé/marca marginal | indisponível | indisponível |
| arvore_rasa | Outro | indisponível | indisponível |
| logistica | Continuação na mesma coluna | indisponível | indisponível |
| logistica | Fim de coluna → topo da próxima | indisponível | indisponível |
| logistica | Entrada/saída de tabela ou imagem | indisponível | indisponível |
| logistica | Salto ou fronteira de elemento transversal | indisponível | indisponível |
| logistica | Cabeçalho/rodapé/marca marginal | indisponível | indisponível |
| logistica | Outro | indisponível | indisponível |
| lightgbm | Continuação na mesma coluna | indisponível | indisponível |
| lightgbm | Fim de coluna → topo da próxima | indisponível | indisponível |
| lightgbm | Entrada/saída de tabela ou imagem | indisponível | indisponível |
| lightgbm | Salto ou fronteira de elemento transversal | indisponível | indisponível |
| lightgbm | Cabeçalho/rodapé/marca marginal | indisponível | indisponível |
| lightgbm | Outro | indisponível | indisponível |
| oraculo_roteamento | Continuação na mesma coluna | indisponível | indisponível |
| oraculo_roteamento | Fim de coluna → topo da próxima | indisponível | indisponível |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | indisponível | indisponível |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | indisponível | indisponível |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | indisponível | indisponível |
| oraculo_roteamento | Outro | indisponível | indisponível |

## golden_v3_novo — CV conjunta

Total: 27 páginas; ausências: `{}`. Médias parciais têm o n explícito e ficam nulas no resumo de registro.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| regra | 27 | 0,959557 | 9,222222 | 17,205754 | 0,928415 | 0,911301 |
| layoutreader_pronto | 27 | 0,950875 | 16,222222 | 18,145040 | 0,927948 | 0,908337 |
| grafo_e004 | 27 | 0,941737 | 6,518519 | 12,941742 | 0,941194 | 0,935275 |
| hibrido67 | 27 | 0,958977 | 7,888889 | 13,739464 | 0,941220 | 0,938410 |
| arvore_rasa | 27 | 0,950778 | 14,518519 | 15,043509 | 0,935822 | 0,919663 |
| logistica | 27 | 0,932095 | 7,666667 | 14,795723 | 0,945210 | 0,933611 |
| lightgbm | 27 | 0,942744 | 14,703704 | 15,302447 | 0,934373 | 0,917663 |
| oraculo_roteamento | 27 | 0,950941 | 5,740741 | 11,144940 | 0,952123 | 0,952568 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra | regra | 27 | 0,000 [0,000; 0,000] | 1,000000 | 0/27/0 | 0/0 |
| regra | hibrido67 | 27 | 1,333 [0,364; 2,649] | 0,027670 | 2/18/7 | 5/39 |
| layoutreader_pronto | regra | 27 | 7,000 [-2,130; 22,250] | 0,838153 | 14/5/8 | 95/285 |
| layoutreader_pronto | hibrido67 | 27 | 8,333 [0,235; 22,948] | 0,123232 | 7/14/6 | 56/280 |
| grafo_e004 | regra | 27 | -2,704 [-3,263; -2,154] | 0,005698 | 13/12/2 | 78/11 |
| grafo_e004 | hibrido67 | 27 | -1,370 [-2,559; 0,231] | 0,258449 | 9/13/5 | 51/18 |
| hibrido67 | regra | 27 | -1,333 [-2,649; -0,364] | 0,027670 | 7/18/2 | 39/5 |
| hibrido67 | hibrido67 | 27 | 0,000 [0,000; 0,000] | 1,000000 | 0/27/0 | 0/0 |
| arvore_rasa | regra | 27 | 5,296 [-2,735; 19,778] | 1,000000 | 13/9/5 | 92/236 |
| arvore_rasa | hibrido67 | 27 | 6,630 [-1,400; 20,632] | 0,152358 | 7/16/4 | 57/235 |
| logistica | regra | 27 | -1,556 [-3,375; 0,549] | 0,125293 | 14/8/5 | 87/49 |
| logistica | hibrido67 | 27 | -0,222 [-1,967; 1,647] | 0,716107 | 9/13/5 | 55/51 |
| lightgbm | regra | 27 | 5,481 [-2,615; 20,039] | 1,000000 | 12/9/6 | 89/239 |
| lightgbm | hibrido67 | 27 | 6,815 [-1,147; 20,947] | 0,265037 | 6/16/5 | 54/238 |
| oraculo_roteamento | regra | 27 | -3,481 [-3,966; -3,000] | 0,005729 | 18/9/0 | 93/4 |
| oraculo_roteamento | hibrido67 | 27 | -2,148 [-3,240; -0,684] | 0,016847 | 13/14/0 | 60/5 |

Reparos/regressões de sucessores por classe (regra; híbrido67):

| Método | Classe | vs regra | vs híbrido67 |
|---|---|---:|---:|
| arvore_rasa | Continuação na mesma coluna | 29/226 | 20/227 |
| arvore_rasa | Fim de coluna → topo da próxima | 1/1 | 1/1 |
| arvore_rasa | Entrada/saída de tabela ou imagem | 4/3 | 3/3 |
| arvore_rasa | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| arvore_rasa | Cabeçalho/rodapé/marca marginal | 20/5 | 12/3 |
| arvore_rasa | Outro | 38/1 | 21/1 |
| logistica | Continuação na mesma coluna | 25/40 | 16/41 |
| logistica | Fim de coluna → topo da próxima | 0/1 | 0/1 |
| logistica | Entrada/saída de tabela ou imagem | 4/4 | 3/4 |
| logistica | Salto ou fronteira de elemento transversal | 0/1 | 0/1 |
| logistica | Cabeçalho/rodapé/marca marginal | 22/1 | 17/2 |
| logistica | Outro | 36/2 | 19/2 |
| lightgbm | Continuação na mesma coluna | 29/228 | 20/229 |
| lightgbm | Fim de coluna → topo da próxima | 1/1 | 1/1 |
| lightgbm | Entrada/saída de tabela ou imagem | 4/3 | 3/3 |
| lightgbm | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| lightgbm | Cabeçalho/rodapé/marca marginal | 17/5 | 9/3 |
| lightgbm | Outro | 38/2 | 21/2 |
| oraculo_roteamento | Continuação na mesma coluna | 35/1 | 25/1 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 0/1 | 0/1 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 4/1 | 3/1 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 0/0 | 0/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 21/1 | 16/2 |
| oraculo_roteamento | Outro | 33/0 | 16/0 |

## teste_silver — CV conjunta

Total: 89 páginas; ausências: `{}`. Médias parciais têm o n explícito e ficam nulas no resumo de registro.

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| regra | 89 | 0,959565 | 27,449438 | 44,495551 | 0,825401 | 0,840212 |
| layoutreader_pronto | 89 | 0,941850 | 31,247191 | 41,826212 | 0,829754 | 0,841286 |
| grafo_e004 | 89 | 0,942613 | 24,146067 | 41,817015 | 0,838883 | 0,854450 |
| hibrido67 | 89 | 0,959092 | 26,426966 | 43,157243 | 0,834332 | 0,849525 |
| arvore_rasa | 89 | 0,953353 | 31,022472 | 41,928012 | 0,832538 | 0,842187 |
| logistica | 89 | 0,941105 | 21,966292 | 38,393780 | 0,851088 | 0,865996 |
| lightgbm | 89 | 0,948052 | 32,955056 | 44,519656 | 0,822349 | 0,835958 |
| oraculo_roteamento | 89 | 0,965624 | 20,561798 | 36,531291 | 0,862075 | 0,878924 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra | regra | 89 | 0,000 [0,000; 0,000] | 1,000000 | 0/89/0 | 0/0 |
| regra | hibrido67 | 89 | 1,022 [0,077; 1,895] | 0,108809 | 3/72/14 | 11/102 |
| layoutreader_pronto | regra | 89 | 3,798 [-8,000; 54,231] | 1,000000 | 38/30/21 | 633/972 |
| layoutreader_pronto | hibrido67 | 89 | 4,820 [-6,105; 54,308] | 1,000000 | 24/47/18 | 531/961 |
| grafo_e004 | regra | 89 | -3,303 [-11,385; -0,816] | 0,108809 | 31/55/3 | 315/21 |
| grafo_e004 | hibrido67 | 89 | -2,281 [-11,308; -0,342] | 0,108809 | 25/50/14 | 256/53 |
| hibrido67 | regra | 89 | -1,022 [-1,895; -0,077] | 0,108809 | 14/72/3 | 102/11 |
| hibrido67 | hibrido67 | 89 | 0,000 [0,000; 0,000] | 1,000000 | 0/89/0 | 0/0 |
| arvore_rasa | regra | 89 | 3,573 [-7,842; 52,462] | 1,000000 | 24/57/8 | 515/833 |
| arvore_rasa | hibrido67 | 89 | 4,596 [-5,947; 52,538] | 1,000000 | 16/62/11 | 445/854 |
| logistica | regra | 89 | -5,483 [-11,385; -1,316] | 0,108809 | 40/36/13 | 628/140 |
| logistica | hibrido67 | 89 | -4,461 [-11,308; -0,842] | 0,108809 | 30/45/14 | 551/154 |
| lightgbm | regra | 89 | 5,506 [-3,553; 52,692] | 1,000000 | 33/39/17 | 356/846 |
| lightgbm | hibrido67 | 89 | 6,528 [-1,658; 52,769] | 1,000000 | 21/52/16 | 262/843 |
| oraculo_roteamento | regra | 89 | -6,888 [-11,692; -3,737] | 0,108809 | 46/43/0 | 651/38 |
| oraculo_roteamento | hibrido67 | 89 | -5,865 [-11,615; -3,263] | 0,108809 | 35/54/0 | 558/36 |

Reparos/regressões de sucessores por classe (regra; híbrido67):

| Método | Classe | vs regra | vs híbrido67 |
|---|---|---:|---:|
| arvore_rasa | Continuação na mesma coluna | 134/748 | 117/748 |
| arvore_rasa | Fim de coluna → topo da próxima | 1/5 | 1/6 |
| arvore_rasa | Entrada/saída de tabela ou imagem | 4/0 | 4/0 |
| arvore_rasa | Salto ou fronteira de elemento transversal | 30/1 | 30/8 |
| arvore_rasa | Cabeçalho/rodapé/marca marginal | 32/11 | 29/18 |
| arvore_rasa | Outro | 314/68 | 264/74 |
| logistica | Continuação na mesma coluna | 157/82 | 142/84 |
| logistica | Fim de coluna → topo da próxima | 1/3 | 0/3 |
| logistica | Entrada/saída de tabela ou imagem | 6/8 | 6/8 |
| logistica | Salto ou fronteira de elemento transversal | 36/3 | 36/10 |
| logistica | Cabeçalho/rodapé/marca marginal | 51/12 | 42/13 |
| logistica | Outro | 377/32 | 325/36 |
| lightgbm | Continuação na mesma coluna | 111/767 | 92/765 |
| lightgbm | Fim de coluna → topo da próxima | 2/5 | 1/5 |
| lightgbm | Entrada/saída de tabela ou imagem | 4/1 | 4/1 |
| lightgbm | Salto ou fronteira de elemento transversal | 37/2 | 30/2 |
| lightgbm | Cabeçalho/rodapé/marca marginal | 43/9 | 32/8 |
| lightgbm | Outro | 159/62 | 103/62 |
| oraculo_roteamento | Continuação na mesma coluna | 159/11 | 140/9 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 2/1 | 1/1 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 7/0 | 7/0 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 44/0 | 37/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 43/5 | 33/5 |
| oraculo_roteamento | Outro | 396/21 | 340/21 |

## Transferência com treino restrito ao ajuste

Cada veículo é excluído de todo o treino v4/RN. As médias por bancada mantêm seus próprios gabaritos. A CV conjunta não escolhe o modelo usado nesta tabela.


### golden_v4

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| hibrido67 | 44 | 0,979738 | 5,136364 | 6,041242 | 0,973419 | 0,966143 |
| arvore_rasa | 44 | 0,911750 | 18,636364 | 13,867739 | 0,928330 | 0,913075 |
| logistica | 44 | 0,957692 | 3,750000 | 5,245510 | 0,977138 | 0,970385 |
| lightgbm | 44 | 0,936724 | 4,795455 | 7,272834 | 0,969629 | 0,960722 |
| oraculo_roteamento | 44 | 0,952256 | 2,659091 | 3,552573 | 0,985859 | 0,982017 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| hibrido67 | regra | 44 | -0,909 [-1,776; -0,095] | 0,022323 | 16/24/4 | 58/16 |
| hibrido67 | hibrido67 | 44 | 0,000 [0,000; 0,000] | 1,000000 | 0/44/0 | 0/0 |
| arvore_rasa | regra | 44 | 12,591 [-0,223; 38,149] | 0,980535 | 13/20/11 | 101/643 |
| arvore_rasa | hibrido67 | 44 | 13,500 [0,826; 38,865] | 0,038219 | 3/28/13 | 64/648 |
| logistica | regra | 44 | -2,295 [-4,302; -0,190] | 0,002867 | 26/12/6 | 153/56 |
| logistica | hibrido67 | 44 | -1,386 [-3,433; 0,587] | 0,018237 | 14/24/6 | 110/55 |
| lightgbm | regra | 44 | -1,250 [-3,707; 1,739] | 0,023673 | 22/13/9 | 142/87 |
| lightgbm | hibrido67 | 44 | -0,341 [-2,700; 2,478] | 0,198292 | 9/27/8 | 93/80 |
| oraculo_roteamento | regra | 44 | -3,386 [-5,000; -2,131] | 0,000012 | 31/13/0 | 153/11 |
| oraculo_roteamento | hibrido67 | 44 | -2,477 [-4,233; -1,233] | 0,000098 | 18/26/0 | 109/9 |

### validacao_silver

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| hibrido67 | 13 | 0,958544 | 17,846154 | 9,553831 | 0,955769 | 0,916132 |
| arvore_rasa | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| logistica | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| lightgbm | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |
| oraculo_roteamento | 0 | indisponível | indisponível | indisponível | indisponível | indisponível |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| hibrido67 | regra | 13 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 |
| hibrido67 | hibrido67 | 13 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 |

### golden_v3_novo

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| hibrido67 | 27 | 0,958977 | 7,888889 | 13,739464 | 0,941220 | 0,938410 |
| arvore_rasa | 27 | 0,957263 | 15,925926 | 19,267824 | 0,924239 | 0,904149 |
| logistica | 27 | 0,951132 | 6,925926 | 13,518337 | 0,949077 | 0,944000 |
| lightgbm | 27 | 0,958481 | 6,814815 | 13,813878 | 0,944021 | 0,935879 |
| oraculo_roteamento | 27 | 0,950941 | 5,740741 | 11,144940 | 0,952123 | 0,952568 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| hibrido67 | regra | 27 | -1,333 [-2,649; -0,364] | 0,027670 | 7/18/2 | 39/5 |
| hibrido67 | hibrido67 | 27 | 0,000 [0,000; 0,000] | 1,000000 | 0/27/0 | 0/0 |
| arvore_rasa | regra | 27 | 6,704 [-2,400; 21,445] | 0,759311 | 14/6/7 | 86/267 |
| arvore_rasa | hibrido67 | 27 | 8,037 [-0,080; 22,145] | 0,288128 | 8/13/6 | 54/269 |
| logistica | regra | 27 | -2,296 [-3,562; -0,939] | 0,010622 | 17/6/4 | 88/30 |
| logistica | hibrido67 | 27 | -0,963 [-2,417; 0,000] | 0,122948 | 10/15/2 | 49/25 |
| lightgbm | regra | 27 | -2,407 [-3,303; -0,500] | 0,125540 | 16/7/4 | 92/31 |
| lightgbm | hibrido67 | 27 | -1,074 [-2,500; 1,273] | 0,670913 | 10/14/3 | 60/33 |
| oraculo_roteamento | regra | 27 | -3,481 [-3,966; -3,000] | 0,005729 | 18/9/0 | 93/4 |
| oraculo_roteamento | hibrido67 | 27 | -2,148 [-3,240; -0,684] | 0,016847 | 13/14/0 | 60/5 |

### teste_silver

| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| hibrido67 | 89 | 0,959092 | 26,426966 | 43,157243 | 0,834332 | 0,849525 |
| arvore_rasa | 89 | 0,943450 | 33,573034 | 44,536711 | 0,816478 | 0,829492 |
| logistica | 89 | 0,948472 | 22,393258 | 38,486381 | 0,849713 | 0,864206 |
| lightgbm | 89 | 0,956956 | 23,662921 | 41,135708 | 0,842995 | 0,860203 |
| oraculo_roteamento | 89 | 0,965624 | 20,561798 | 36,531291 | 0,862075 | 0,878924 |

| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| hibrido67 | regra | 89 | -1,022 [-1,895; -0,077] | 0,108809 | 14/72/3 | 102/11 |
| hibrido67 | hibrido67 | 89 | 0,000 [0,000; 0,000] | 1,000000 | 0/89/0 | 0/0 |
| arvore_rasa | regra | 89 | 6,124 [-2,842; 54,231] | 1,000000 | 34/33/22 | 408/954 |
| arvore_rasa | hibrido67 | 89 | 7,146 [-0,947; 54,308] | 1,000000 | 21/48/20 | 317/954 |
| logistica | regra | 89 | -5,056 [-7,632; -1,816] | 0,108809 | 41/35/13 | 631/181 |
| logistica | hibrido67 | 89 | -4,034 [-6,923; -1,342] | 0,108809 | 29/48/12 | 549/190 |
| lightgbm | regra | 89 | -3,787 [-11,385; -1,026] | 0,108809 | 43/36/10 | 404/67 |
| lightgbm | hibrido67 | 89 | -2,764 [-11,308; -0,553] | 0,108809 | 30/51/8 | 313/67 |
| oraculo_roteamento | regra | 89 | -6,888 [-11,692; -3,737] | 0,108809 | 46/43/0 | 651/38 |
| oraculo_roteamento | hibrido67 | 89 | -5,865 [-11,615; -3,263] | 0,108809 | 35/54/0 | 558/36 |

## Sensibilidade às sementes

Média ± desvio padrão amostral das métricas agregadas entre sementes; não é IC e não escolhe o vencedor.

| Modo | Método | Quebras/pág média ± dp | τ média ± dp |
|---|---|---:|---:|
| cv_conjunta | arvore_rasa | 21,593750 ± 0,319484 | 0,957381 ± 0,001708 |
| cv_conjunta | logistica | 15,156250 ± 0,000000 | 0,949458 ± 0,000000 |
| cv_conjunta | lightgbm | 22,500000 ± 0,000000 | 0,951670 ± 0,000000 |
| transferencia_ajuste | arvore_rasa | 26,466667 ± 0,018042 | 0,936319 ± 0,000645 |
| transferencia_ajuste | logistica | 14,656250 ± 0,000000 | 0,951456 ± 0,000000 |
| transferencia_ajuste | lightgbm | 15,631250 ± 0,000000 | 0,951650 ± 0,000000 |

## Árvore rasa para o TCC

Árvore ajustada somente em v4/RN com candidatos disponíveis, semente primária. É uma descrição do modelo de implantação; suas métricas de treino não são reportadas como validação. As árvores efetivamente avaliadas fora de veículo vêm a seguir e ficam também nos caches dos folds.

Classes: `{"0": "regra", "1": "layoutreader_pronto", "2": "grafo_e004"}`.

```text
|--- tem_transversal <= 0.5000
|   |--- prop_cabecalho <= 0.0203
|   |   |--- class: 0
|   |--- prop_cabecalho >  0.0203
|   |   |--- largura_media_coluna <= 0.8186
|   |   |   |--- class: 1
|   |   |--- largura_media_coluna >  0.8186
|   |   |   |--- class: 1
|--- tem_transversal >  0.5000
|   |--- prop_cabecalho <= 0.0348
|   |   |--- class: 2
|   |--- prop_cabecalho >  0.0348
|   |   |--- class: 0

```

Features: unidades = linhas e átomos; colunas = máximo local informado pela regra; margem = marca/cabeçalho/rodapé entre unidades de texto; transversais = pontes geométricas; largura média = extensão horizontal dos grupos de coluna normalizada pela largura da página; concordância = fração de decisões de sucessor idênticas. Todas são calculadas antes de consultar o gabarito.

### Árvore sem o veículo official_diary_MG_congonhas

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_RJ_barra_do_pirai

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- largura_media_coluna <= 0.3723
|   |   |--- n_unidades <= 181.5000
|   |   |   |--- class: 2
|   |   |--- n_unidades >  181.5000
|   |   |   |--- class: 2
|   |--- largura_media_coluna >  0.3723
|   |   |--- n_unidades <= 22.0000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  22.0000
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_RJ_duque_de_caxias

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- concordancia_regra_grafo_e004 <= 0.8840
|   |   |   |--- class: 2
|   |   |--- concordancia_regra_grafo_e004 >  0.8840
|   |   |   |--- class: 2
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_RJ_seropedica

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_RJ_volta_redonda

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 116.0000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  116.0000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ac

```text
|--- concordancia_regra_grafo_e004 <= 0.9942
|   |--- n_unidades <= 132.0000
|   |   |--- concordancia_regra_layoutreader <= 0.9651
|   |   |   |--- class: 1
|   |   |--- concordancia_regra_layoutreader >  0.9651
|   |   |   |--- class: 0
|   |--- n_unidades >  132.0000
|   |   |--- n_unidades <= 295.5000
|   |   |   |--- class: 2
|   |   |--- n_unidades >  295.5000
|   |   |   |--- class: 2
|--- concordancia_regra_grafo_e004 >  0.9942
|   |--- n_imagens <= 1.5000
|   |   |--- n_unidades <= 107.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  107.5000
|   |   |   |--- class: 0
|   |--- n_imagens >  1.5000
|   |   |--- class: 1

```

### Árvore sem o veículo official_diary_al

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 128.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  128.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.6638
|   |   |   |--- class: 2
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.6638
|   |   |   |--- class: 2

```

### Árvore sem o veículo official_diary_am_manaus

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ap

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ba_salvador

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- n_unidades <= 23.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  23.5000
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ce

```text
|--- n_unidades <= 132.0000
|   |--- concordancia_regra_grafo_e004 <= 0.9582
|   |   |--- prop_cabecalho <= 0.0153
|   |   |   |--- class: 0
|   |   |--- prop_cabecalho >  0.0153
|   |   |   |--- class: 1
|   |--- concordancia_regra_grafo_e004 >  0.9582
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|--- n_unidades >  132.0000
|   |--- n_unidades <= 295.5000
|   |   |--- tem_transversal <= 0.5000
|   |   |   |--- class: 1
|   |   |--- tem_transversal >  0.5000
|   |   |   |--- class: 2
|   |--- n_unidades >  295.5000
|   |   |--- class: 2

```

### Árvore sem o veículo official_diary_ma

```text
|--- largura_media_coluna <= 0.4670
|   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.9515
|   |   |--- n_unidades <= 131.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  131.5000
|   |   |   |--- class: 2
|   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.9515
|   |   |--- class: 1
|--- largura_media_coluna >  0.4670
|   |--- concordancia_regra_layoutreader <= 0.9477
|   |   |--- n_unidades <= 23.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  23.5000
|   |   |   |--- class: 1
|   |--- concordancia_regra_layoutreader >  0.9477
|   |   |--- n_unidades <= 79.0000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  79.0000
|   |   |   |--- class: 0

```

### Árvore sem o veículo official_diary_mg

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- largura_media_coluna <= 0.3723
|   |   |--- n_unidades <= 181.5000
|   |   |   |--- class: 2
|   |   |--- n_unidades >  181.5000
|   |   |   |--- class: 2
|   |--- largura_media_coluna >  0.3723
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ms

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.9602
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.9602
|   |   |   |--- class: 0
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_pb

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- largura_media_coluna <= 0.3723
|   |   |--- n_unidades <= 181.5000
|   |   |   |--- class: 2
|   |   |--- n_unidades >  181.5000
|   |   |   |--- class: 2
|   |--- largura_media_coluna >  0.3723
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_pe

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_pi_v2

```text
|--- concordancia_regra_grafo_e004 <= 0.9942
|   |--- n_unidades <= 188.0000
|   |   |--- concordancia_regra_layoutreader <= 0.9651
|   |   |   |--- class: 1
|   |   |--- concordancia_regra_layoutreader >  0.9651
|   |   |   |--- class: 0
|   |--- n_unidades >  188.0000
|   |   |--- prop_cabecalho <= 0.0133
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0133
|   |   |   |--- class: 2
|--- concordancia_regra_grafo_e004 >  0.9942
|   |--- prop_rodape <= 0.0451
|   |   |--- n_unidades <= 107.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  107.5000
|   |   |   |--- class: 0
|   |--- prop_rodape >  0.0451
|   |   |--- class: 1

```

### Árvore sem o veículo official_diary_pr_curitiba

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_rj

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |--- n_unidades <= 53.0000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  53.0000
|   |   |   |--- class: 1
|   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |--- tem_transversal <= 0.5000
|   |   |   |--- class: 1
|   |   |--- tem_transversal >  0.5000
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_imagens <= 1.5000
|   |   |--- n_unidades <= 116.0000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  116.0000
|   |   |   |--- class: 1
|   |--- n_imagens >  1.5000
|   |   |--- class: 1

```

### Árvore sem o veículo official_diary_rj_japeri

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- largura_media_coluna <= 0.3723
|   |   |--- n_unidades <= 181.5000
|   |   |   |--- class: 2
|   |   |--- n_unidades >  181.5000
|   |   |   |--- class: 2
|   |--- largura_media_coluna >  0.3723
|   |   |--- n_unidades <= 22.0000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  22.0000
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_rn

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_ro

```text
|--- concordancia_regra_grafo_e004 <= 0.9942
|   |--- n_unidades <= 188.0000
|   |   |--- concordancia_regra_layoutreader <= 0.9654
|   |   |   |--- class: 1
|   |   |--- concordancia_regra_layoutreader >  0.9654
|   |   |   |--- class: 0
|   |--- n_unidades >  188.0000
|   |   |--- prop_cabecalho <= 0.0133
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0133
|   |   |   |--- class: 2
|--- concordancia_regra_grafo_e004 >  0.9942
|   |--- n_imagens <= 1.5000
|   |   |--- n_unidades <= 107.5000
|   |   |   |--- class: 0
|   |   |--- n_unidades >  107.5000
|   |   |   |--- class: 0
|   |--- n_imagens >  1.5000
|   |   |--- class: 1

```

### Árvore sem o veículo official_diary_rr

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.9602
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.9602
|   |   |   |--- class: 0
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_rs_porto_alegre

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_sc

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 128.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  128.5000
|   |   |--- prop_margem <= 0.0162
|   |   |   |--- class: 2
|   |   |--- prop_margem >  0.0162
|   |   |   |--- class: 2

```

### Árvore sem o veículo official_diary_se

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- n_unidades <= 71.5000
|   |   |   |--- class: 1
|   |   |--- n_unidades >  71.5000
|   |   |   |--- class: 2
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- n_unidades <= 112.5000
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1
|   |--- n_unidades >  112.5000
|   |   |--- largura_media_coluna <= 0.2789
|   |   |   |--- class: 2
|   |   |--- largura_media_coluna >  0.2789
|   |   |   |--- class: 1

```

### Árvore sem o veículo official_diary_to

```text
|--- concordancia_regra_grafo_e004 <= 0.9641
|   |--- tem_transversal <= 0.5000
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 <= 0.7260
|   |   |   |--- class: 0
|   |   |--- concordancia_layoutreader_pronto_grafo_e004 >  0.7260
|   |   |   |--- class: 1
|   |--- tem_transversal >  0.5000
|   |   |--- prop_cabecalho <= 0.0155
|   |   |   |--- class: 2
|   |   |--- prop_cabecalho >  0.0155
|   |   |   |--- class: 1
|--- concordancia_regra_grafo_e004 >  0.9641
|   |--- largura_media_coluna <= 0.2789
|   |   |--- class: 2
|   |--- largura_media_coluna >  0.2789
|   |   |--- n_imagens <= 1.5000
|   |   |   |--- class: 0
|   |   |--- n_imagens >  1.5000
|   |   |   |--- class: 1

```

## Limitações e veredito

NÃO GO nos seletores executados; manter o híbrido 67 congelado.

O limiar 67 e a própria regra já foram desenvolvidos em v4: seus controles não se tornam inéditos com LOOV. Golden_v3_novo já foi consultado em rodadas anteriores. Referência silver é ruidosa, sobretudo dentro de átomos; o oráculo apenas escolhe as ordens existentes, sem consertá-las. Seu teto usa o gabarito e é inalcançável como preditor. RN sem LayoutReader não permite alvo, features de concordância ou roteamento perfeito completos; páginas RN densas têm somente híbrido parcial igual à regra. Não se preenche a ausência escolhendo regra nas páginas leves.

Cobertura de palavras é integral nas ordens avaliadas, conferida por IDs/expansões da régua; não mede palavras ausentes da camada digital. Reporta-se a página inteira, com diagnóstico geométrico de margens e outras classes. Não existe aqui uma referência humana independente só do corpo; o diagnóstico de classe não deve ser citado como métrica completa do corpo. IC por veículo com poucos grupos (especialmente silver) tem baixa resolução. Os testes são exploratórios e não substituem o confirmatório por PDF. Não há nova avaliação do teste cego.

Retomada: `venv/Scripts/python.exe -B orquestracao/analises/e005_seletor.py`; verificação sem alterar saídas: mesmo comando com `--conferir`. Apenas caches cuja assinatura de código, fontes, parâmetros e versões coincide são reaproveitados.
