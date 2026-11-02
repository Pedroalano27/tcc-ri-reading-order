# Corretor de transições sobre linhas

Âncoras aprovadas em 44 páginas: regra τ 0,985948, 6,045455 quebras/página.  
Diagnóstico completo: 71 páginas; cabeçalho/rodapé/marca marginal reúne 175 quebras (33,98%); bancadas separadas abaixo.  
Candidatos: nível 3; recall total golden_v4 98,21%, golden_v3_novo 97,36%, validacao_silver 96,61%.  
MLP CPU: 24 páginas de treino, 3 épocas concluídas; limiar RN 0,80.  
Sem ganho consistente nas bancadas humanas e no teste silver: conservar a regra de colunas e encerrar esta demonstração sem ampliar o treino. A amostra pequena não permite excluir ganho de outra configuração do corretor. Δ híbrido−regra: golden_v4: Δ quebras -0,136 [-0,326; 0,000], Δ τ -0,004854 [-0,010604; 0,000188]; golden_v3_novo: Δ quebras 0,222 [0,000; 0,412], Δ τ -0,001463 [-0,006049; -0,000003]; teste_silver: Δ quebras -0,015 [-0,429; 0,067], Δ τ -0,001172 [-0,008927; 0,000024].  

Relatório gerado pelo script; as medidas abaixo vêm dos caches desta execução. Resultados parciais são identificados por cobertura e não recebem uma conclusão final.

## Protocolo e estado

Regra congelada: `projecao_local_margens` com os parâmetros de `erros_ponta_a_ponta.FIXA`. Unidades de linhas e átomos congelados de ls3; texto vem da camada digital. Entrada pela função `ordem_entrada`, com a permutação `entrada-{page_id}`. Cada unidade é expandida por `ordem_sem_bbox.fluxo()`, como na bancada oficial.

A régua de τ, quebras, fidelidade de trechos de palavras e sucessor de linhas é importada de `erros_ponta_a_ponta`; não foi reimplementada. `referencia`, `expansoes`, `auditar_unidades` e `prever` vêm da bancada. Não se chama sua função `metricas`, que escreveria no cache de outro experimento.

Execução: `753b70c73bf909a03285b43c02605cbc8b97bf78e45412eea078de014cefbbd4`. Estado, hashes e resultados por página em `resultados/corretor_de_transicoes_cache/753b70c73bf909a03285b43c02605cbc8b97bf78e45412eea078de014cefbbd4/estado.json`.

Configuração efetiva: `{"versao": "transicoes-v2-veredito", "semente": 20261008, "n_treino": 24, "epocas": 3, "device": "cpu", "threads_max": 4, "num_workers": 0, "meta_recall": 0.95, "niveis_candidatos": [3, 8, 16, -1], "limiares": [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.01], "regra": "projecao_local_margens_s0.45_g1.2_v0.08", "arquitetura": [60, 32, 1], "features": ["fim", "dx_h", "dy_h", "gap_y_h", "gap_x_h", "overlap_x", "alinha_esq_h", "alinha_dir_h", "largura_a_h", "largura_z_h", "altura_a_h", "altura_z_h", "x_a", "y_a", "x_z", "y_z", "col_a", "col_z", "mesma_col", "pos_col_a", "pos_col_z", "calha_entre", "objeto_entre", "ponte_a", "ponte_z", "margem_a", "margem_z", "regra_escolheu", "confianca_regra", "dist_posto_regra", "tipo_par_mesma_coluna", "tipo_par_proxima_coluna", "tipo_par_tabela_imagem", "tipo_par_transversal", "tipo_par_margem", "tipo_par_outro", "tipo_regra_mesma_coluna", "tipo_regra_proxima_coluna", "tipo_regra_tabela_imagem", "tipo_regra_transversal", "tipo_regra_margem", "tipo_regra_outro", "a_ponto_final", "a_pontuacao_final", "a_hifen_final", "a_maiuscula_inicio", "a_lista", "a_n_palavras", "z_ponto_final", "z_pontuacao_final", "z_hifen_final", "z_maiuscula_inicio", "z_lista", "z_n_palavras", "tipo_a_texto", "tipo_a_tabela", "tipo_a_imagem", "tipo_z_texto", "tipo_z_tabela", "tipo_z_imagem"], "lr": 0.001}`.

Páginas de bancadas humanas, inclusive tarefas sem anotação concluída, são excluídas do treino, da validação e do teste silver desta execução. As bancadas humanas continuam completas. Esta exclusão é exigida pelo pedido; reduz a cobertura silver em relação à tabela histórica e impede comparar diretamente suas médias com médias históricas sem pareamento.

| Partição silver | Páginas usadas | Páginas humanas excluídas | Veículos |
|---|---:|---:|---:|
| treino | 24 | 0 | 7 |
| validacao | 14 | 1 | 1 |
| teste | 68 | 21 | 3 |

Duplicatas base/extra idênticas deduplicadas: 34. A lista de páginas usada por cada split e as exclusões ficam no estado. A amostra de treino é pequena e distribuída por veículo, escolhida pelo hash de IDs, sem consultar eficácia.

'Vistos' nas tabelas = veículos presentes na amostra de treino selecionada (efetivamente usada quando o treino está concluído). O estado também guarda `visto_split`, pertencimento aos veículos do split original, para distinguir os dois conceitos quando a amostra pequena não cobre algum veículo. Não significa visto pelo detector ls3.

Veículos da amostra de treino: `official_diary_RJ_volta_redonda`, `official_diary_ba_salvador`, `official_diary_pa`, `official_diary_pe`, `official_diary_pr`, `official_diary_rr`, `official_diary_sc`. PDFs compartilhados com tarefas humanas, em páginas diferentes: 0.

## Âncoras

Páginas rechecadas: 44. Status: aprovadas.

| Controle | τ palavras | Quebras/página |
|---|---:|---:|
| regra | 0,985948 | 6,045455 |
| P2 | 0,985948 | 6,045455 |
| P1m_historico | 0,952424 | 8,931818 |

Regra e P2 são reexecutados com detecções congeladas, sem carregar o detector. Também se confere a igualdade das sequências com o P2 histórico. P1m é a medida histórica de extrator + XY-cut + margens, importada de `resultados/erros_ponta_a_ponta.json`; não é uma reextração nova. Tolerâncias, valores-alvo e verificações estão no script. Se falhar, nenhuma tabela nova é liberada.

## Etapa de diagnóstico

Tipologia geométrica automática, em precedência exclusiva: margem (mesma partição da regra), tabela/imagem, elemento transversal ou obstáculo entre as linhas, retorno ao topo da próxima coluna, continuação na mesma coluna e outro. Fim/topo usam a posição relativa nas linhas de cada coluna; mudanças locais de calha podem cair em 'outro'. Não há ouro de classes/tipos nem inspeção humana que certifique estas causas. Transições dentro do mesmo átomo caem em 'outro', com marca de fronteira interna; não são entrada/saída de tabela. As caixas humanas não entram na classificação nem no modelo.

'Acerto de linha' exige que ambas as linhas-ouro estejam intactas e consecutivas, exatamente como na régua oficial. O script confere a soma contra essa régua. Erros de sucessor-ouro e quebras emitidas são denominadores diferentes: uma ordem errada pode omitir uma transição-ouro e criar outra. A fração de quebras abaixo usa cada evento de palavra emitido, associado ao tipo da transição esperada para sua palavra de origem. Eventos dentro de linha/átomo não viram fronteiras treináveis.

### golden_v4 — completo

**todos: 44 páginas, 27 veículos.**

| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Continuação na mesma coluna | 3149 | 3101 | 48 | 1,52% | 20,25% | 54 | 20,30% | 10 |
| Fim de coluna → topo da próxima | 13 | 10 | 3 | 23,08% | 1,27% | 3 | 1,13% | 0 |
| Entrada/saída de tabela ou imagem | 60 | 52 | 8 | 13,33% | 3,38% | 9 | 3,38% | 1 |
| Salto ou fronteira de elemento transversal | 26 | 8 | 18 | 69,23% | 7,59% | 18 | 6,77% | 0 |
| Cabeçalho/rodapé/marca marginal | 213 | 82 | 131 | 61,50% | 55,27% | 134 | 50,38% | 13 |
| Outro | 1224 | 1195 | 29 | 2,37% | 12,24% | 48 | 18,05% | 0 |

| Controle da representação | Total |
|---|---:|
| Transições-ouro internas à mesma unidade | 1122 |
| Fronteiras-ouro inalcançáveis por permutação de unidades | 5 |
| Piso interno de quebras (função oficial) | 24 |

**vistos: 5 páginas, 5 veículos.**

| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Continuação na mesma coluna | 587 | 581 | 6 | 1,02% | 37,50% | 10 | 41,67% | 5 |
| Fim de coluna → topo da próxima | 5 | 5 | 0 | 0,00% | 0,00% | 0 | 0,00% | 0 |
| Entrada/saída de tabela ou imagem | 16 | 16 | 0 | 0,00% | 0,00% | 0 | 0,00% | 0 |
| Salto ou fronteira de elemento transversal | 2 | 0 | 2 | 100,00% | 12,50% | 2 | 8,33% | 0 |
| Cabeçalho/rodapé/marca marginal | 17 | 10 | 7 | 41,18% | 43,75% | 5 | 20,83% | 1 |
| Outro | 165 | 164 | 1 | 0,61% | 6,25% | 7 | 29,17% | 0 |

| Controle da representação | Total |
|---|---:|
| Transições-ouro internas à mesma unidade | 160 |
| Fronteiras-ouro inalcançáveis por permutação de unidades | 1 |
| Piso interno de quebras (função oficial) | 6 |

**não vistos: 39 páginas, 22 veículos.**

| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Continuação na mesma coluna | 2562 | 2520 | 42 | 1,64% | 19,00% | 44 | 18,18% | 5 |
| Fim de coluna → topo da próxima | 8 | 5 | 3 | 37,50% | 1,36% | 3 | 1,24% | 0 |
| Entrada/saída de tabela ou imagem | 44 | 36 | 8 | 18,18% | 3,62% | 9 | 3,72% | 1 |
| Salto ou fronteira de elemento transversal | 24 | 8 | 16 | 66,67% | 7,24% | 16 | 6,61% | 0 |
| Cabeçalho/rodapé/marca marginal | 196 | 72 | 124 | 63,27% | 56,11% | 129 | 53,31% | 12 |
| Outro | 1059 | 1031 | 28 | 2,64% | 12,67% | 41 | 16,94% | 0 |

| Controle da representação | Total |
|---|---:|
| Transições-ouro internas à mesma unidade | 962 |
| Fronteiras-ouro inalcançáveis por permutação de unidades | 4 |
| Piso interno de quebras (função oficial) | 18 |

Exemplos de sucessores perdidos, extraídos das palavras e sem ajustar parâmetros:

| Página | Tipo | Origem → próxima linha-ouro |
|---|---|---|
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | Continuação na mesma coluna | amparo institucional de até 05 (cinco) → idosos, sendo 1 (uma) vaga para |
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | Continuação na mesma coluna | atendimento ao Grau III, com 60 → anos de idade ou mais, de |
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | Cabeçalho/rodapé/marca marginal | MUNICÍPIO DE CONGONHAS → w w w . congonhas . |
| `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | Cabeçalho/rodapé/marca marginal | g o v . b r → 2 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | Cabeçalho/rodapé/marca marginal | Secretaria Municipal de Saúde.............................................................................................................................................................................................................................................................13 → Barra do Piraí/RJ |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | Cabeçalho/rodapé/marca marginal | Barra do Piraí/RJ → 3 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | Cabeçalho/rodapé/marca marginal | 3 → DIÁRIO OFICIAL ELETRÔNICO garante autenticidade |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2` | Cabeçalho/rodapé/marca marginal | DIÁRIO OFICIAL ELETRÔNICO garante autenticidade → deste documento visualizado diretamente no portal |

Todas as transições e seus IDs estão no cache de diagnóstico por página.

### golden_v3_novo — completo

**todos: 27 páginas, 10 veículos.**

| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Continuação na mesma coluna | 1882 | 1767 | 115 | 6,11% | 48,32% | 100 | 40,16% | 1 |
| Fim de coluna → topo da próxima | 8 | 6 | 2 | 25,00% | 0,84% | 2 | 0,80% | 0 |
| Entrada/saída de tabela ou imagem | 66 | 57 | 9 | 13,64% | 3,78% | 9 | 3,61% | 1 |
| Salto ou fronteira de elemento transversal | 7 | 5 | 2 | 28,57% | 0,84% | 3 | 1,20% | 0 |
| Cabeçalho/rodapé/marca marginal | 87 | 46 | 41 | 47,13% | 17,23% | 41 | 16,47% | 0 |
| Outro | 862 | 793 | 69 | 8,00% | 28,99% | 94 | 37,75% | 5 |

| Controle da representação | Total |
|---|---:|
| Transições-ouro internas à mesma unidade | 753 |
| Fronteiras-ouro inalcançáveis por permutação de unidades | 7 |
| Piso interno de quebras (função oficial) | 7 |

**vistos: 0 páginas, 0 veículos.**

**não vistos: 27 páginas, 10 veículos.**

| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Continuação na mesma coluna | 1882 | 1767 | 115 | 6,11% | 48,32% | 100 | 40,16% | 1 |
| Fim de coluna → topo da próxima | 8 | 6 | 2 | 25,00% | 0,84% | 2 | 0,80% | 0 |
| Entrada/saída de tabela ou imagem | 66 | 57 | 9 | 13,64% | 3,78% | 9 | 3,61% | 1 |
| Salto ou fronteira de elemento transversal | 7 | 5 | 2 | 28,57% | 0,84% | 3 | 1,20% | 0 |
| Cabeçalho/rodapé/marca marginal | 87 | 46 | 41 | 47,13% | 17,23% | 41 | 16,47% | 0 |
| Outro | 862 | 793 | 69 | 8,00% | 28,99% | 94 | 37,75% | 5 |

| Controle da representação | Total |
|---|---:|
| Transições-ouro internas à mesma unidade | 753 |
| Fronteiras-ouro inalcançáveis por permutação de unidades | 7 |
| Piso interno de quebras (função oficial) | 7 |

Exemplos de sucessores perdidos, extraídos das palavras e sem ajustar parâmetros:

| Página | Tipo | Origem → próxima linha-ouro |
|---|---|---|
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Outro | legais efeitos. → Barra do Piraí, 28 de julho |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Continuação na mesma coluna | surtam os devidos e legais efeitos. → Barra do Piraí, 28 de julho |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Outro | Secretário Municipal do Ambiente → SAÚDE |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Outro | SAÚDE → EXTRATO CONTRATUAL |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Entrada/saída de tabela ou imagem | EXTRATO CONTRATUAL → INSTRUMENTO: 3° Termo Aditivo ao Contrato |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Cabeçalho/rodapé/marca marginal | Moreira Ferreira - Secretário de Saúde → Barra do Piraí/RJ 6 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Cabeçalho/rodapé/marca marginal | Barra do Piraí/RJ 6 → DIÁRIO OFICIAL ELETRÔNICO garante autenticidade |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5` | Cabeçalho/rodapé/marca marginal | deste documento visualizado diretamente no portal → www.barradopirai.rj.gov.br |

Todas as transições e seus IDs estão no cache de diagnóstico por página.

## Etapa de candidatos

Conjunto inicial: próximo abaixo na coluna, topo da próxima coluna, próxima ponte, escolha da regra, vizinhos por distância geométrica e FIN. Ampliações predefinidas adicionam mais vizinhos, próximos abaixo, topos de colunas, vizinhos na regra e objetos; a última inclui todas as outras unidades. Desempates seguem a entrada embaralhada. Nunca se inclui um candidato porque o ouro o revelou.

O recall total conta a fronteira de linhas-ouro que pode ser realizada: transições internas já consecutivas contam como alcançáveis sem decisão de sucessor. Fronteiras internas quebradas ou endpoints que não chegam à borda canônica da unidade contam como falha estrutural. O recall entre unidades tem somente fronteiras alcançáveis no denominador. São ambos reportados. Cobertura dos endpoints não garante que as duas linhas inteiras fiquem intactas: essa exigência adicional é medida pelo sucessor realizado da régua oficial. FIN não entra no denominador de sucessores entre linhas.

A ampliação até atingir a meta consulta RN e as duas bancadas humanas, conforme o pedido. Portanto essas páginas também participam do desenvolvimento do conjunto de candidatos; o limiar do híbrido e os pesos continuam exclusivos da validação RN e do treino silver, respectivamente. No teste silver o conjunto já está congelado: seu recall nunca determina uma ampliação.

### Nível 3

**golden_v4: completo.**

| Grupo | Tipo | Total | Cobertos | Recall total | Fronteiras alcançáveis entre unidades | Cobertas entre unidades | Recall entre | Falhas estruturais |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Continuação na mesma coluna | 3149 | 3140 | 99,71% | 3148 | 3139 | 99,71% | 0 |
| todos | Fim de coluna → topo da próxima | 13 | 9 | 69,23% | 13 | 9 | 69,23% | 0 |
| todos | Entrada/saída de tabela ou imagem | 60 | 56 | 93,33% | 59 | 56 | 94,92% | 1 |
| todos | Salto ou fronteira de elemento transversal | 26 | 16 | 61,54% | 25 | 15 | 60,00% | 0 |
| todos | Cabeçalho/rodapé/marca marginal | 213 | 163 | 76,53% | 204 | 157 | 76,96% | 3 |
| todos | Outro | 1224 | 1217 | 99,43% | 112 | 106 | 94,64% | 1 |
| todos | TOTAL | 4685 | 4601 | 98,21% | 3561 | 3482 | 97,78% | 5 |
| vistos | Continuação na mesma coluna | 587 | 584 | 99,49% | 587 | 584 | 99,49% | 0 |
| vistos | Fim de coluna → topo da próxima | 5 | 4 | 80,00% | 5 | 4 | 80,00% | 0 |
| vistos | Entrada/saída de tabela ou imagem | 16 | 16 | 100,00% | 16 | 16 | 100,00% | 0 |
| vistos | Salto ou fronteira de elemento transversal | 2 | 0 | 0,00% | 2 | 0 | 0,00% | 0 |
| vistos | Cabeçalho/rodapé/marca marginal | 17 | 12 | 70,59% | 16 | 12 | 75,00% | 1 |
| vistos | Outro | 165 | 165 | 100,00% | 5 | 5 | 100,00% | 0 |
| vistos | TOTAL | 792 | 781 | 98,61% | 631 | 621 | 98,42% | 1 |
| não vistos | Continuação na mesma coluna | 2562 | 2556 | 99,77% | 2561 | 2555 | 99,77% | 0 |
| não vistos | Fim de coluna → topo da próxima | 8 | 5 | 62,50% | 8 | 5 | 62,50% | 0 |
| não vistos | Entrada/saída de tabela ou imagem | 44 | 40 | 90,91% | 43 | 40 | 93,02% | 1 |
| não vistos | Salto ou fronteira de elemento transversal | 24 | 16 | 66,67% | 23 | 15 | 65,22% | 0 |
| não vistos | Cabeçalho/rodapé/marca marginal | 196 | 151 | 77,04% | 188 | 145 | 77,13% | 2 |
| não vistos | Outro | 1059 | 1052 | 99,34% | 107 | 101 | 94,39% | 1 |
| não vistos | TOTAL | 3893 | 3820 | 98,12% | 2930 | 2861 | 97,65% | 4 |

Tamanho médio do conjunto por fonte entre unidades: 4,153; máximo: 7. FIN excluído desses tamanhos.

**golden_v3_novo: completo.**

| Grupo | Tipo | Total | Cobertos | Recall total | Fronteiras alcançáveis entre unidades | Cobertas entre unidades | Recall entre | Falhas estruturais |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Continuação na mesma coluna | 1882 | 1869 | 99,31% | 1882 | 1869 | 99,31% | 0 |
| todos | Fim de coluna → topo da próxima | 8 | 6 | 75,00% | 8 | 6 | 75,00% | 0 |
| todos | Entrada/saída de tabela ou imagem | 66 | 62 | 93,94% | 65 | 62 | 95,38% | 1 |
| todos | Salto ou fronteira de elemento transversal | 7 | 7 | 100,00% | 7 | 7 | 100,00% | 0 |
| todos | Cabeçalho/rodapé/marca marginal | 87 | 65 | 74,71% | 86 | 64 | 74,42% | 0 |
| todos | Outro | 862 | 826 | 95,82% | 110 | 80 | 72,73% | 6 |
| todos | TOTAL | 2912 | 2835 | 97,36% | 2158 | 2088 | 96,76% | 7 |
| vistos | Continuação na mesma coluna | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | Fim de coluna → topo da próxima | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | Entrada/saída de tabela ou imagem | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | Salto ou fronteira de elemento transversal | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | Cabeçalho/rodapé/marca marginal | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | Outro | 0 | 0 | — | 0 | 0 | — | 0 |
| vistos | TOTAL | 0 | 0 | — | 0 | 0 | — | 0 |
| não vistos | Continuação na mesma coluna | 1882 | 1869 | 99,31% | 1882 | 1869 | 99,31% | 0 |
| não vistos | Fim de coluna → topo da próxima | 8 | 6 | 75,00% | 8 | 6 | 75,00% | 0 |
| não vistos | Entrada/saída de tabela ou imagem | 66 | 62 | 93,94% | 65 | 62 | 95,38% | 1 |
| não vistos | Salto ou fronteira de elemento transversal | 7 | 7 | 100,00% | 7 | 7 | 100,00% | 0 |
| não vistos | Cabeçalho/rodapé/marca marginal | 87 | 65 | 74,71% | 86 | 64 | 74,42% | 0 |
| não vistos | Outro | 862 | 826 | 95,82% | 110 | 80 | 72,73% | 6 |
| não vistos | TOTAL | 2912 | 2835 | 97,36% | 2158 | 2088 | 96,76% | 7 |

Tamanho médio do conjunto por fonte entre unidades: 4,030; máximo: 7. FIN excluído desses tamanhos.

**validacao_silver: completo.**

| Grupo | Tipo | Total | Cobertos | Recall total | Fronteiras alcançáveis entre unidades | Cobertas entre unidades | Recall entre | Falhas estruturais |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Continuação na mesma coluna | 2169 | 2167 | 99,91% | 2169 | 2167 | 99,91% | 0 |
| todos | Fim de coluna → topo da próxima | 2 | 2 | 100,00% | 2 | 2 | 100,00% | 0 |
| todos | Entrada/saída de tabela ou imagem | 18 | 11 | 61,11% | 12 | 11 | 91,67% | 6 |
| todos | Salto ou fronteira de elemento transversal | 13 | 8 | 61,54% | 13 | 8 | 61,54% | 0 |
| todos | Cabeçalho/rodapé/marca marginal | 129 | 90 | 69,77% | 129 | 90 | 69,77% | 0 |
| todos | Outro | 2601 | 2487 | 95,62% | 139 | 75 | 53,96% | 50 |
| todos | TOTAL | 4932 | 4765 | 96,61% | 2464 | 2353 | 95,50% | 56 |

Tamanho médio do conjunto por fonte entre unidades: 4,115; máximo: 7. FIN excluído desses tamanhos.

**teste_silver: completo.**

| Grupo | Tipo | Total | Cobertos | Recall total | Fronteiras alcançáveis entre unidades | Cobertas entre unidades | Recall entre | Falhas estruturais |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| todos | Continuação na mesma coluna | 5222 | 5201 | 99,60% | 5217 | 5201 | 99,69% | 5 |
| todos | Fim de coluna → topo da próxima | 24 | 20 | 83,33% | 24 | 20 | 83,33% | 0 |
| todos | Entrada/saída de tabela ou imagem | 92 | 66 | 71,74% | 69 | 66 | 95,65% | 23 |
| todos | Salto ou fronteira de elemento transversal | 156 | 137 | 87,82% | 156 | 137 | 87,82% | 0 |
| todos | Cabeçalho/rodapé/marca marginal | 237 | 162 | 68,35% | 205 | 162 | 79,02% | 32 |
| todos | Outro | 4949 | 3474 | 70,20% | 741 | 457 | 61,67% | 1191 |
| todos | TOTAL | 10680 | 9060 | 84,83% | 6412 | 6043 | 94,25% | 1251 |

Tamanho médio do conjunto por fonte entre unidades: 3,745; máximo: 7. FIN excluído desses tamanhos.

| Ampliação | Motivo observado |
|---|---|
| 3 | Meta atingida em todas as coortes; conjunto congelado. |

## Etapa de corretor

MLP de pares pequeno, com uma camada oculta. Uma decisão de fonte é um grupo de candidatos: cross-entropy sobre os escores do grupo, com probabilidades softmax. A escala das features é calculada apenas nos pares de treino. Não há embeddings, modelo remoto, GPU ou DataLoader. Features: distâncias/alturas normalizadas pela altura mediana de linha, sobreposição, alinhamento, posição na página/coluna, calha, objetos e pontes entre os dois, tipo de transição geométrica, tipo da unidade, escolha e confiança geométrica da regra, pontuação, maiúscula, hífen, tamanho e lista. A confiança da regra é um proxy heurístico; a probabilidade do MLP não tem calibração independente.

Supervisão silver usa somente fontes e alvos cuja expansão canônica coincide com um trecho contíguo do fluxo PDF. Unidades atravessadas, conteúdo interno divergente, fontes sem texto ou sucessor fora do conjunto são contados e excluídos da loss; jamais são consertados por mediana. O terminal FIN é negativo em todos os outros grupos e positivo no fim real.

Páginas com pares prontas: 24; decisões de fonte: 3227; pares: 16395; alvos fora do conjunto: 114. Exclusões de supervisão: `{"sem_palavras": 17, "fonte_nao_contigua_ou_interna_divergente": 20, "alvo_nao_contiguo_ou_fronteira_interna": 22}`.

| Época concluída | Loss média por decisão de fonte | Decisões |
|---:|---:|---:|
| 1 | 0,235958 | 3227 |
| 2 | 0,159969 | 3227 |
| 3 | 0,134986 | 3227 |

Parâmetros do MLP: 1985. Checkpoint de página: `resultados/corretor_de_transicoes_cache/753b70c73bf909a03285b43c02605cbc8b97bf78e45412eea078de014cefbbd4/modelo.pt`. Uma queda no meio de uma página refaz somente a página não confirmada. Pesos, otimizador, RNG e cursor são salvos juntos; treino e inferência são sequenciais.

Validação: 14 páginas de RN. Limiar escolhido: 0,80. Critério predefinido: minimizar quebras realizadas, sem reduzir τ médio de RN; empates favorecem τ, menos intervenções e maior limiar. O limiar acima da faixa de probabilidades desativa correções e reproduz exatamente a regra. Pesos e épocas não são escolhidos pelas bancadas humanas.

| Limiar | Quebras RN | τ RN | Propostas | Elegível |
|---:|---:|---:|---:|---|
| 0,50 | 16,714 | 0,950252 | 27 | não |
| 0,60 | 16,714 | 0,953686 | 21 | não |
| 0,70 | 16,929 | 0,952705 | 15 | não |
| 0,80 | 16,929 | 0,957215 | 14 | sim |
| 0,90 | 17,071 | 0,956929 | 12 | sim |
| 0,95 | 17,357 | 0,956023 | 7 | sim |
| 0,99 | 17,643 | 0,955456 | 3 | sim |
| 1,01 | 17,857 | 0,954162 | 0 | sim |

Só fronteiras ambíguas podem mudar no híbrido: continuação sobreposta, próxima e sem obstáculos tem confiança heurística alta e fica protegida. As demais, incluindo retornos e fronteiras de objetos/margens, são ambíguas. O classificador sozinho escolhe em todas as fontes. A decodificação resolve duplo predecessor e ciclo por confiança e reata cadeias pelo posto da regra; assim até 'corretor sozinho' tem a regra como informação/fallback. O relatório separa top-1 bruto dos pares e sucessor de linhas realizado na sequência final.

### Comparação final

Métricas macro por página [IC agrupado por veículo]. Top-1 bruto tem o denominador das fronteiras-ouro alcançáveis entre unidades; não inclui terminal nem decisões internas. Sucessor de linhas realizado usa todas as transições de linhas da régua oficial.

| Bancada | Grupo | n | Modelo | Top-1 bruto acertos/total | Top-1 macro [IC] | Sucessor linhas realizado [IC] | τ [IC] | Quebras/página [IC] | Fidelidade [IC] |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| golden_v4 | todos | 44 | regra | 3313/3561 | 84,909 [75,690; 92,424]% | 92,724 [87,773; 96,046]% | 0,985948 [0,974000; 0,995048] | 6,045 [4,085; 8,907] | 94,813 [91,275; 97,214]% |
| golden_v4 | todos | 44 | corretor | 3336/3561 | 88,443 [84,005; 92,375]% | 92,729 [87,747; 96,053]% | 0,951267 [0,897091; 0,989246] | 6,000 [4,086; 8,791] | 94,876 [91,322; 97,264]% |
| golden_v4 | todos | 44 | hibrido | 3326/3561 | 88,797 [82,983; 93,533]% | 92,840 [87,856; 96,168]% | 0,981094 [0,966219; 0,992596] | 5,909 [3,959; 8,755] | 94,911 [91,350; 97,289]% |
| golden_v4 | vistos | 5 | regra | 613/631 | 92,975 [85,841; 98,251]% | 97,698 [96,955; 98,545]% | 0,997638 [0,993868; 0,999928] | 4,800 [2,600; 7,600] | 98,491 [98,094; 98,887]% |
| golden_v4 | vistos | 5 | corretor | 614/631 | 93,600 [86,466; 98,251]% | 97,684 [97,282; 98,099]% | 0,897359 [0,693156; 0,999844] | 5,000 [3,200; 6,800] | 98,131 [97,595; 98,650]% |
| golden_v4 | vistos | 5 | hibrido | 614/631 | 93,600 [86,466; 98,251]% | 97,968 [97,351; 98,586]% | 0,999514 [0,998831; 0,999952] | 4,400 [2,600; 6,400] | 98,491 [98,094; 98,887]% |
| golden_v4 | nao_vistos | 39 | regra | 2700/2930 | 83,875 [73,506; 92,367]% | 92,086 [86,646; 95,831]% | 0,984450 [0,970784; 0,994628] | 6,205 [3,976; 9,342] | 94,341 [90,452; 97,059]% |
| golden_v4 | nao_vistos | 39 | corretor | 2722/2930 | 87,782 [83,008; 92,043]% | 92,094 [86,641; 95,795]% | 0,958179 [0,902816; 0,991881] | 6,128 [3,950; 9,229] | 94,458 [90,530; 97,161]% |
| golden_v4 | nao_vistos | 39 | hibrido | 2712/2930 | 88,181 [81,737; 93,454]% | 92,183 [86,705; 95,896]% | 0,978733 [0,962366; 0,991466] | 6,103 [3,881; 9,257] | 94,452 [90,534; 97,155]% |
| golden_v3_novo | todos | 27 | regra | 1928/2158 | 82,410 [76,903; 87,091]% | 91,130 [87,969; 93,613]% | 0,959557 [0,913505; 0,996898] | 9,222 [4,909; 12,770] | 92,841 [89,864; 96,501]% |
| golden_v3_novo | todos | 27 | corretor | 1932/2158 | 82,901 [77,676; 86,891]% | 91,106 [87,936; 93,613]% | 0,959456 [0,913504; 0,996898] | 9,259 [4,909; 12,867] | 92,799 [89,767; 96,501]% |
| golden_v3_novo | todos | 27 | hibrido | 1932/2158 | 83,197 [77,573; 87,624]% | 90,992 [87,975; 93,381]% | 0,958095 [0,912296; 0,995205] | 9,444 [5,055; 13,000] | 92,725 [89,712; 96,470]% |
| golden_v3_novo | nao_vistos | 27 | regra | 1928/2158 | 82,410 [76,903; 87,091]% | 91,130 [87,969; 93,613]% | 0,959557 [0,913505; 0,996898] | 9,222 [4,909; 12,770] | 92,841 [89,864; 96,501]% |
| golden_v3_novo | nao_vistos | 27 | corretor | 1932/2158 | 82,901 [77,676; 86,891]% | 91,106 [87,936; 93,613]% | 0,959456 [0,913504; 0,996898] | 9,259 [4,909; 12,867] | 92,799 [89,767; 96,501]% |
| golden_v3_novo | nao_vistos | 27 | hibrido | 1932/2158 | 83,197 [77,573; 87,624]% | 90,992 [87,975; 93,381]% | 0,958095 [0,912296; 0,995205] | 9,444 [5,055; 13,000] | 92,725 [89,712; 96,470]% |
| validacao_silver | todos | 14 | regra | 2270/2464 | 88,345 [88,345; 88,345]% | 90,449 [90,449; 90,449]% | 0,954162 [0,954162; 0,954162] | 17,857 [17,857; 17,857] | 94,892 [94,892; 94,892]% |
| validacao_silver | todos | 14 | corretor | 2286/2464 | 88,992 [88,992; 88,992]% | 91,075 [91,075; 91,075]% | 0,958438 [0,958438; 0,958438] | 16,786 [16,786; 16,786] | 95,176 [95,176; 95,176]% |
| validacao_silver | todos | 14 | hibrido | 2282/2464 | 88,711 [88,711; 88,711]% | 90,799 [90,799; 90,799]% | 0,957215 [0,957215; 0,957215] | 16,929 [16,929; 16,929] | 95,118 [95,118; 95,118]% |
| teste_silver | todos | 68 | regra | 5693/6412 | 84,582 [74,245; 89,096]% | 82,640 [75,597; 95,759]% | 0,972209 [0,944150; 0,998595] | 29,485 [24,903; 33,633] | 81,796 [72,025; 90,435]% |
| teste_silver | todos | 68 | corretor | 5715/6412 | 86,337 [75,329; 92,052]% | 82,631 [75,597; 95,847]% | 0,972234 [0,944150; 0,998592] | 29,426 [24,968; 33,633] | 81,771 [72,025; 90,639]% |
| teste_silver | todos | 68 | hibrido | 5712/6412 | 86,395 [74,540; 92,534]% | 82,637 [75,488; 95,803]% | 0,971037 [0,944175; 0,998016] | 29,471 [24,903; 33,700] | 81,807 [72,025; 90,539]% |

| Bancada | Grupo | Métrica | Δ híbrido−regra [IC] | p Wilcoxon página | p Wilcoxon veículo | Veículos |
|---|---|---|---:|---:|---:|---:|
| golden_v4 | todos | quebras | -0,136 [-0,326; 0,000] | 0,242052 | 0,180373 | 27 |
| golden_v4 | todos | tau | -0,004854 [-0,010604; 0,000188] | 0,058442 | 0,134294 | 27 |
| golden_v4 | todos | sucessor_linhas | 0,001 [0,000; 0,002] | 0,227737 | 0,093170 | 27 |
| golden_v4 | todos | fid12 | 0,001 [0,000; 0,002] | 0,096694 | 0,158263 | 27 |
| golden_v4 | vistos | quebras | -0,400 [-1,200; 0,000] | 0,317311 | 0,317311 | 5 |
| golden_v4 | vistos | tau | 0,001877 [0,000000; 0,005630] | 0,317311 | 0,317311 | 5 |
| golden_v4 | vistos | sucessor_linhas | 0,003 [0,000; 0,008] | 0,317311 | 0,317311 | 5 |
| golden_v4 | vistos | fid12 | 0,000 [0,000; 0,000] | 1,000000 | 1,000000 | 5 |
| golden_v4 | nao_vistos | quebras | -0,103 [-0,289; 0,030] | 0,401765 | 0,329904 | 22 |
| golden_v4 | nao_vistos | tau | -0,005717 [-0,012029; 0,000000] | 0,020998 | 0,054984 | 22 |
| golden_v4 | nao_vistos | sucessor_linhas | 0,001 [0,000; 0,002] | 0,377431 | 0,166693 | 22 |
| golden_v4 | nao_vistos | fid12 | 0,001 [0,000; 0,002] | 0,095967 | 0,153430 | 22 |
| golden_v3_novo | todos | quebras | 0,222 [0,000; 0,412] | 0,168927 | 0,247318 | 10 |
| golden_v3_novo | todos | tau | -0,001463 [-0,006049; -0,000003] | 0,025582 | 0,027670 | 10 |
| golden_v3_novo | todos | sucessor_linhas | -0,001 [-0,003; 0,001] | 0,180408 | 0,270912 | 10 |
| golden_v3_novo | todos | fid12 | -0,001 [-0,002; 0,001] | 0,180408 | 0,270912 | 10 |
| golden_v3_novo | nao_vistos | quebras | 0,222 [0,000; 0,412] | 0,168927 | 0,247318 | 10 |
| golden_v3_novo | nao_vistos | tau | -0,001463 [-0,006049; -0,000003] | 0,025582 | 0,027670 | 10 |
| golden_v3_novo | nao_vistos | sucessor_linhas | -0,001 [-0,003; 0,001] | 0,180408 | 0,270912 | 10 |
| golden_v3_novo | nao_vistos | fid12 | -0,001 [-0,002; 0,001] | 0,180408 | 0,270912 | 10 |
| validacao_silver | todos | quebras | -0,929 [-0,929; -0,929] | 0,009119 | 0,317311 | 1 |
| validacao_silver | todos | tau | 0,003054 [0,003054; 0,003054] | 0,187356 | 0,317311 | 1 |
| validacao_silver | todos | sucessor_linhas | 0,004 [0,004; 0,004] | 0,009239 | 0,317311 | 1 |
| validacao_silver | todos | fid12 | 0,002 [0,002; 0,002] | 0,009239 | 0,317311 | 1 |
| teste_silver | todos | quebras | -0,015 [-0,429; 0,067] | 0,679425 | 0,781511 | 3 |
| teste_silver | todos | tau | -0,001172 [-0,008927; 0,000024] | 0,794706 | 0,285049 | 3 |
| teste_silver | todos | sucessor_linhas | -0,000 [-0,001; 0,001] | 0,654795 | 1,000000 | 3 |
| teste_silver | todos | fid12 | 0,000 [-0,000; 0,001] | 0,575429 | 0,781511 | 3 |

Bootstrap e Wilcoxon usam as funções do avaliador importado: percentil por veículo, 5000 reamostras, semente 20261003; Wilcoxon bilateral Pratt, aproximação normal. P-valores exploratórios, sem correção por multiplicidade. Páginas do mesmo veículo não são tratadas como veículos independentes; o teste por página também fica visível como contraste. RN tem um único veículo: seu intervalo de cluster é degenerado, não mede generalização.

| Bancada | Propostas | Mantidas na ordem | Conflitos | Ciclos | Fronteiras alteradas após reatar cadeias |
|---|---:|---:|---:|---:|---:|
| golden_v4 | 32 | 23 | 9 | 0 | 64 |
| golden_v3_novo | 11 | 10 | 1 | 0 | 27 |
| validacao_silver | 14 | 14 | 0 | 0 | 28 |
| teste_silver | 23 | 23 | 0 | 0 | 65 |

| Bancada | Veredito observado |
|---|---|
| golden_v4 | Menos quebras em média; τ cai. IC das quebras inclui zero: evidência inconclusiva para ganho populacional. |
| golden_v3_novo | Mais quebras em média; τ cai. IC das quebras inclui zero: evidência inconclusiva para ganho populacional. |
| validacao_silver | Menos quebras em média; τ sobe. |
| teste_silver | Menos quebras em média; τ cai. IC das quebras inclui zero: evidência inconclusiva para ganho populacional. |

**Decisão desta demonstração:** Sem ganho consistente nas bancadas humanas e no teste silver: conservar a regra de colunas e encerrar esta demonstração sem ampliar o treino. A amostra pequena não permite excluir ganho de outra configuração do corretor.

O limiar permanece o escolhido em RN. A avaliação final encerra esta configuração; não se retreinam pesos nem se procura outro limiar usando resultados humanos ou de CE/MA/RJ. O veredito considera quebras e τ juntos: melhora de pares isolados ou da validação não demonstra melhora da sequência realizada nas bancadas finais.


## Limitações e retomada

golden_v4 participou do desenvolvimento da regra; golden_v3_novo tem páginas adicionais e amostra pequena de conveniência. A ordem humana é de regiões expandida geometricamente, não anotação independente de todas as linhas/palavras/células. O conjunto de candidatos é desenvolvido com as humanas nesta tarefa; declare isso ao discutir generalização. Silver é referência automática de veículos escolhidos por concordância com heurística; não fornece ordem humana independente. Veículos humanos vistos e não vistos são separados. PDFs compartilhados entre treino e páginas humanas, mesmo em páginas distintas, ficam no estado para auditoria e podem reduzir a independência documental.

O MLP foi desenhado para uma demonstração pequena; não há comparação com várias sementes nem potência estatística para declarar equivalência. Pontuação/maiúsculas são proxies baratos de estilo; não há fontes tipográficas/fontsize nos shards de palavras. Calhas são proxies globais, não segmentação humana de todas as mudanças locais. A regra fornece features e prioridade das cabeças ao decodificador: este experimento testa correção local da regra, não um ordenador neural independente.

Ciclos e conflitos podem desfazer propostas ou mudar outras fronteiras. Ganho de top-1 bruto não garante ganho de quebras/τ; a ordem final completa é medida. Erro interno de tabela/linha/átomo permanece indivisível. FIN e unidades vazias não têm sucessor textual anotado; participam da ordem, com esse limite explícito.

A execução mantém um processo, CPU, threads limitadas e um grupo de candidatos em RAM por vez. Hashes de fontes e configuração dão um namespace próprio; não mistura caches antigos. O script guarda pares, métricas, decisões e checkpoints antes de avançar. O controle de memória/prazo interrompe de forma retomável. Repita o mesmo comando. Fontes alteradas durante a execução invalidam a comparação.

```powershell
venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa diagnostico
venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa candidatos
venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa corretor --n-treino 24 --epocas 3 --max-minutos 30
venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --conferir
venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --autoteste
```

Predições JSONL no cache próprio seguem o contrato `page_id/ordem` da bancada. As métricas já foram calculadas por suas funções puras e pela régua oficial; nenhum relatório ou cache de outro experimento é escrito. Anotações, PDFs, docs e quadro de comunicação permanecem somente de leitura. Não há publicação, rede ou commit.
