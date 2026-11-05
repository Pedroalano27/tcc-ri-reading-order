1. Âncora golden_v4 reproduzida: τ 0,985948; 6,045455 quebras/página.
2. Execução completa das famílias candidatos, decodificação e residual nas quatro bancadas.
3. Grafo: GO; oraculo_decodificador_matching_K32, redução 67,51% no desenvolvimento v4 + RN.
4. Roteamento usa somente predições salvas; RN não possui os quatro métodos e fica indisponível.
5. Todas as variantes medidas preservam 100% das palavras e as expansões internas congeladas.
6. Oráculos usam referência; golden_v3_novo já foi consultado anteriormente; nenhum teste cego é avaliado.

# E002 — tetos das famílias de ordenação

## Protocolo e limitações

Relatório gerado integralmente pelo script. CPU, um processo, sem modelos novos; caches atômicos por página e passo residual. Fontes e hashes em `cache/manifesto.json`. Métricas completas, ordens, sucessores ausentes e operações ficam nos caches de página.

A régua é `corretor_de_transicoes.medir`, que importa `bancada_ordenadores` e `erros_ponta_a_ponta`: τ de palavras, quebras, fidelidade integral de 12 e sucessor de linhas intactas. IDs embaralhados por `ordem_entrada` (random.Random entrada-page_id). A cobertura considera todas as palavras extraídas, inclusive fora da referência humana; não mede conteúdo inexistente na camada digital.

Candidatos: `nivel` da função existente amplia listas e não limita o grau. Aqui preservam-se as propostas do nível 3 (regra primeiro), completadas com as propostas do nível 32 por distância euclidiana entre centros. Empates pela entrada embaralhada. K limita destinos reais; FIM privado é adicional. K=12/24/32 usam listas aninhadas, sem ouro. Recall é micro sobre fronteiras externas alcançáveis; internas e inalcançáveis são mostradas separadamente. Recall de erros usa somente sucessores perdidos pela regra.

No mesmo grafo, escores são 1 para fronteiras de palavras-ouro realizáveis (inclusive uma linha humana dividida em unidades), 0 nas demais; FIM vale 1 apenas na última palavra-ouro. Guloso global prioriza escore; matching maximiza a soma com FIM privado e elimina a menor aresta dos ciclos; max-regret é importado de `ordem_lm_arestas`. Todos costuram pela PRIMEIRA unidade de cada caminho na regra. Escores binários geram empates; os tetos realizados são atingíveis por estes algoritmos, não provas de ótimo global.

Residual: escolhe maior redução estrita de quebras entre trocas vizinhas, movimentos de 1–4 unidades de texto na mesma coluna (até 8 posições, sem atravessar margens/átomos/pontes) e reinserções de linhas de margem/título antes/depois dos candidatos K32 ou nas extremidades. Título é proxy automática: até 16 palavras e ≥70% das letras maiúsculas; inclui pontes. Desempate determinístico pela enumeração. Para quando nenhuma operação melhora quebras; não atravessa platôs e portanto é ótimo local. Custos de borda vêm de eventos() oficial, conferidos na sequência inteira a cada operação.

Categorias importadas do corretor, inclusive tabela/imagem (classe adicional conservada). São proxies geométricas exclusivas, não causas humanas. As tabelas por classe decompõem quebras segundo a transição esperada; sucessores usam as caixas das linhas-ouro como no corretor. Não equivalem a executar um método só naquela classe. Avaliação de corpo: aqui apenas a decomposição automática em classes; não há uma segunda referência humana de corpo, e métricas globais incluem a página inteira.

Ajuste/seleção somente golden_v4 + RN, com peso igual por bancada e desempate por τ; seleção congelada antes das bancadas externas. Golden_v3_novo é externo nesta execução, mas já foi consultado em rodadas anteriores. O teste silver CE/MA/RJ tem ruído do fluxo PDF e piso interno aos átomos. Mantêm-se as sobreposições históricas entre bancadas, que não são amostras independentes somáveis. IC95 percentil com 5.000 bootstraps por veículo e Wilcoxon bilateral Pratt sobre deltas médios por veículo, descritivos. RN tem um veículo: IC degenerado, teste não informativo.

RN não tem LayoutReader/reordenação restrita salvos; não se executam modelos para preenchê-los. Híbrido 67 fica disponível só nas páginas RN densas que selecionam a regra; sua média parcial NÃO representa a bancada. Roteamento e suas métricas RN são nulos. Roteamento minimiza quebras por página, desempata por τ e ordem fixa dos métodos; informa todos os empates por quebras.

Critério do cartão: ≥20% de redução de quebras no desenvolvimento. Resultado: **GO**, regra 11,356 → 3,689 quebras/página na média de v4/RN. A escolha vale para as externas sem nova seleção.

## golden_v4

Páginas processadas: 44; veículos: 27.

| Método | n | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| regra_colunas | 44 | 0,985948 | 6,045 | 11,885 | 0,948129 | 0,927240 | 0,000 [0,000; 0,000] | 1,000000 | 0/44/0 | 0/0 | 100% |
| hibrido67 | 44 | 0,979738 | 5,136 | 6,041 | 0,973419 | 0,966143 | -0,909 [-1,776; -0,095] | 0,022323 | 16/24/4 | 58/16 | 100% |
| layoutreader_pronto | 44 | 0,913071 | 18,386 | 11,088 | 0,935197 | 0,927182 | 12,341 [-0,637; 37,951] | 0,875629 | 24/6/14 | 155/693 | 100% |
| regra_reordena | 44 | 0,985967 | 5,182 | 10,905 | 0,954405 | 0,936322 | -0,864 [-1,610; -0,309] | 0,014913 | 8/35/1 | 37/0 | 100% |
| oraculo_decodificador_guloso_K12 | 44 | 0,854957 | 1,523 | 1,706 | 0,991191 | 0,990322 | -4,523 [-6,512; -3,000] | 0,000009 | 35/9/0 | 188/1 | 100% |
| oraculo_decodificador_matching_K12 | 44 | 0,899448 | 1,432 | 1,622 | 0,991595 | 0,991079 | -4,614 [-6,625; -3,083] | 0,000009 | 35/9/0 | 191/0 | 100% |
| oraculo_decodificador_maxregret_K12 | 44 | 0,854957 | 1,523 | 1,706 | 0,991191 | 0,990322 | -4,523 [-6,512; -3,000] | 0,000009 | 35/9/0 | 188/1 | 100% |
| oraculo_decodificador_guloso_K24 | 44 | 0,855446 | 1,295 | 1,432 | 0,993426 | 0,992158 | -4,750 [-6,800; -3,200] | 0,000009 | 35/9/0 | 198/1 | 100% |
| oraculo_decodificador_matching_K24 | 44 | 0,880017 | 1,205 | 1,358 | 0,993846 | 0,992824 | -4,841 [-6,953; -3,256] | 0,000009 | 35/9/0 | 201/0 | 100% |
| oraculo_decodificador_maxregret_K24 | 44 | 0,855446 | 1,295 | 1,432 | 0,993426 | 0,992158 | -4,750 [-6,800; -3,200] | 0,000009 | 35/9/0 | 198/1 | 100% |
| oraculo_decodificador_guloso_K32 | 44 | 0,871074 | 1,159 | 1,245 | 0,994805 | 0,993687 | -4,886 [-6,930; -3,326] | 0,000009 | 35/9/0 | 205/1 | 100% |
| oraculo_decodificador_matching_K32 | 44 | 0,916792 | 1,045 | 1,135 | 0,995642 | 0,994559 | -5,000 [-7,114; -3,375] | 0,000009 | 35/9/0 | 209/0 | 100% |
| oraculo_decodificador_maxregret_K32 | 44 | 0,871074 | 1,159 | 1,245 | 0,994805 | 0,993687 | -4,886 [-6,930; -3,326] | 0,000009 | 35/9/0 | 205/1 | 100% |
| oraculo_residual | 44 | 0,989684 | 1,909 | 2,450 | 0,987893 | 0,986299 | -4,136 [-5,651; -2,875] | 0,000012 | 33/11/0 | 171/0 | 100% |
| oraculo_roteamento | 44 | 0,993508 | 3,591 | 4,248 | 0,983027 | 0,977842 | -2,455 [-3,237; -1,703] | 0,000021 | 27/17/0 | 116/12 | 100% |

### Recall de candidatos por classe

Regra e híbrido 67 são referências na tabela acima; não geram candidatos. Recall não é uma métrica de ordem: a família (a) não recebe τ artificial no JSON.

| K | Classe | Presentes/elegíveis | Recall | Erros presentes/elegíveis | Recall erros | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 3144/3148 | 99,87% | 44/48 | 91,67% | 1 | 0 |
| 12 | Fim de coluna → topo da próxima | 9/13 | 69,23% | 0/3 | 0,00% | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 58/59 | 98,31% | 6/7 | 85,71% | 0 | 1 |
| 12 | Salto ou fronteira de elemento transversal | 19/25 | 76,00% | 13/18 | 72,22% | 1 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 175/204 | 85,78% | 100/128 | 78,12% | 8 | 3 |
| 12 | Outro | 107/112 | 95,54% | 23/28 | 82,14% | 1112 | 1 |
| 24 | Continuação na mesma coluna | 3147/3148 | 99,97% | 47/48 | 97,92% | 1 | 0 |
| 24 | Fim de coluna → topo da próxima | 9/13 | 69,23% | 0/3 | 0,00% | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 59/59 | 100,00% | 7/7 | 100,00% | 0 | 1 |
| 24 | Salto ou fronteira de elemento transversal | 19/25 | 76,00% | 13/18 | 72,22% | 1 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 183/204 | 89,71% | 107/128 | 83,59% | 8 | 3 |
| 24 | Outro | 109/112 | 97,32% | 25/28 | 89,29% | 1112 | 1 |
| 32 | Continuação na mesma coluna | 3147/3148 | 99,97% | 47/48 | 97,92% | 1 | 0 |
| 32 | Fim de coluna → topo da próxima | 9/13 | 69,23% | 0/3 | 0,00% | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 59/59 | 100,00% | 7/7 | 100,00% | 0 | 1 |
| 32 | Salto ou fronteira de elemento transversal | 19/25 | 76,00% | 13/18 | 72,22% | 1 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 187/204 | 91,67% | 111/128 | 86,72% | 8 | 3 |
| 32 | Outro | 110/112 | 98,21% | 26/28 | 92,86% | 1112 | 1 |

### Decomposição por classe de erro da regra

| Método | Classe | Quebras/pág | Δ quebras [IC95 veículo] | p veículo | Sucessores certos/ouro | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra_colunas | Continuação na mesma coluna | 1,227 | 0,000 [0,000; 0,000] | 1,000000 | 3101/3149 | 0/0 |
| regra_colunas | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| regra_colunas | Entrada/saída de tabela ou imagem | 0,205 | 0,000 [0,000; 0,000] | 1,000000 | 52/60 | 0/0 |
| regra_colunas | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| regra_colunas | Cabeçalho/rodapé/marca marginal | 3,045 | 0,000 [0,000; 0,000] | 1,000000 | 82/213 | 0/0 |
| regra_colunas | Outro | 1,091 | 0,000 [0,000; 0,000] | 1,000000 | 1195/1224 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 1,114 | -0,114 [-0,225; -0,022] | 0,045625 | 3107/3149 | 6/0 |
| hibrido67 | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,432 | 0,227 [0,022; 0,548] | 0,045708 | 42/60 | 1/11 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 2,295 | -0,750 [-1,429; -0,244] | 0,004247 | 119/213 | 42/5 |
| hibrido67 | Outro | 0,818 | -0,273 [-0,592; 0,000] | 0,232909 | 1204/1224 | 9/0 |
| layoutreader_pronto | Continuação na mesma coluna | 14,977 | 13,750 [1,375; 38,381] | 0,185073 | 2496/3149 | 32/637 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,136 | 0,068 [0,000; 0,189] | 0,157373 | 7/13 | 0/3 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,682 | 0,477 [0,128; 0,951] | 0,008374 | 30/60 | 1/23 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,114 | -0,295 [-1,024; 0,082] | 0,937545 | 19/26 | 14/3 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 1,205 | -1,841 [-2,574; -1,050] | 0,000528 | 167/213 | 93/8 |
| layoutreader_pronto | Outro | 1,273 | 0,182 [-0,512; 1,079] | 0,911995 | 1191/1224 | 15/19 |
| regra_reordena | Continuação na mesma coluna | 0,864 | -0,364 [-0,700; -0,114] | 0,008362 | 3118/3149 | 17/0 |
| regra_reordena | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,205 | 0,000 [0,000; 0,000] | 1,000000 | 52/60 | 0/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,409 | 0,000 [0,000; 0,000] | 1,000000 | 8/26 | 0/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 2,977 | -0,068 [-0,143; 0,000] | 0,083379 | 85/213 | 3/0 |
| regra_reordena | Outro | 0,659 | -0,432 [-0,861; -0,114] | 0,016137 | 1212/1224 | 17/0 |
| oraculo_decodificador_guloso_K12 | Continuação na mesma coluna | 0,295 | -0,932 [-2,000; -0,286] | 0,001703 | 3141/3149 | 40/0 |
| oraculo_decodificador_guloso_K12 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_guloso_K12 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_guloso_K12 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_guloso_K12 | Cabeçalho/rodapé/marca marginal | 0,682 | -2,364 [-3,250; -1,474] | 0,000030 | 189/213 | 107/0 |
| oraculo_decodificador_guloso_K12 | Outro | 0,386 | -0,705 [-1,163; -0,326] | 0,001500 | 1217/1224 | 22/0 |
| oraculo_decodificador_matching_K12 | Continuação na mesma coluna | 0,295 | -0,932 [-2,000; -0,286] | 0,001703 | 3141/3149 | 40/0 |
| oraculo_decodificador_matching_K12 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_matching_K12 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_matching_K12 | Salto ou fronteira de elemento transversal | 0,068 | -0,341 [-1,100; 0,000] | 0,157373 | 21/26 | 13/0 |
| oraculo_decodificador_matching_K12 | Cabeçalho/rodapé/marca marginal | 0,636 | -2,409 [-3,340; -1,488] | 0,000030 | 192/213 | 110/0 |
| oraculo_decodificador_matching_K12 | Outro | 0,364 | -0,727 [-1,180; -0,357] | 0,000647 | 1217/1224 | 22/0 |
| oraculo_decodificador_maxregret_K12 | Continuação na mesma coluna | 0,295 | -0,932 [-2,000; -0,286] | 0,001703 | 3141/3149 | 40/0 |
| oraculo_decodificador_maxregret_K12 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_maxregret_K12 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_maxregret_K12 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_maxregret_K12 | Cabeçalho/rodapé/marca marginal | 0,682 | -2,364 [-3,250; -1,474] | 0,000030 | 189/213 | 107/0 |
| oraculo_decodificador_maxregret_K12 | Outro | 0,386 | -0,705 [-1,163; -0,326] | 0,001500 | 1217/1224 | 22/0 |
| oraculo_decodificador_guloso_K24 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3145/3149 | 44/0 |
| oraculo_decodificador_guloso_K24 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_guloso_K24 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_guloso_K24 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_guloso_K24 | Cabeçalho/rodapé/marca marginal | 0,591 | -2,455 [-3,342; -1,524] | 0,000030 | 194/213 | 112/0 |
| oraculo_decodificador_guloso_K24 | Outro | 0,295 | -0,795 [-1,263; -0,400] | 0,001268 | 1218/1224 | 23/0 |
| oraculo_decodificador_matching_K24 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3145/3149 | 44/0 |
| oraculo_decodificador_matching_K24 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_matching_K24 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_matching_K24 | Salto ou fronteira de elemento transversal | 0,068 | -0,341 [-1,100; 0,000] | 0,157373 | 21/26 | 13/0 |
| oraculo_decodificador_matching_K24 | Cabeçalho/rodapé/marca marginal | 0,523 | -2,523 [-3,477; -1,568] | 0,000030 | 197/213 | 115/0 |
| oraculo_decodificador_matching_K24 | Outro | 0,295 | -0,795 [-1,263; -0,400] | 0,001268 | 1218/1224 | 23/0 |
| oraculo_decodificador_maxregret_K24 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3145/3149 | 44/0 |
| oraculo_decodificador_maxregret_K24 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 10/13 | 0/0 |
| oraculo_decodificador_maxregret_K24 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_maxregret_K24 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_maxregret_K24 | Cabeçalho/rodapé/marca marginal | 0,591 | -2,455 [-3,342; -1,524] | 0,000030 | 194/213 | 112/0 |
| oraculo_decodificador_maxregret_K24 | Outro | 0,295 | -0,795 [-1,263; -0,400] | 0,001268 | 1218/1224 | 23/0 |
| oraculo_decodificador_guloso_K32 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3147/3149 | 46/0 |
| oraculo_decodificador_guloso_K32 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 11/13 | 1/0 |
| oraculo_decodificador_guloso_K32 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_guloso_K32 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_guloso_K32 | Cabeçalho/rodapé/marca marginal | 0,500 | -2,545 [-3,500; -1,568] | 0,000030 | 197/213 | 115/0 |
| oraculo_decodificador_guloso_K32 | Outro | 0,250 | -0,841 [-1,333; -0,442] | 0,001273 | 1219/1224 | 24/0 |
| oraculo_decodificador_matching_K32 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3147/3149 | 46/0 |
| oraculo_decodificador_matching_K32 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 11/13 | 1/0 |
| oraculo_decodificador_matching_K32 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_matching_K32 | Salto ou fronteira de elemento transversal | 0,068 | -0,341 [-1,100; 0,000] | 0,157373 | 21/26 | 13/0 |
| oraculo_decodificador_matching_K32 | Cabeçalho/rodapé/marca marginal | 0,432 | -2,614 [-3,625; -1,610] | 0,000030 | 201/213 | 119/0 |
| oraculo_decodificador_matching_K32 | Outro | 0,227 | -0,864 [-1,356; -0,457] | 0,001276 | 1219/1224 | 24/0 |
| oraculo_decodificador_maxregret_K32 | Continuação na mesma coluna | 0,250 | -0,977 [-2,047; -0,309] | 0,001701 | 3147/3149 | 46/0 |
| oraculo_decodificador_maxregret_K32 | Fim de coluna → topo da próxima | 0,023 | -0,045 [-0,116; 0,000] | 0,157373 | 11/13 | 1/0 |
| oraculo_decodificador_maxregret_K32 | Entrada/saída de tabela ou imagem | 0,045 | -0,159 [-0,425; 0,000] | 0,083417 | 58/60 | 6/0 |
| oraculo_decodificador_maxregret_K32 | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,075; 0,045] | 0,534300 | 20/26 | 13/1 |
| oraculo_decodificador_maxregret_K32 | Cabeçalho/rodapé/marca marginal | 0,500 | -2,545 [-3,500; -1,568] | 0,000030 | 197/213 | 115/0 |
| oraculo_decodificador_maxregret_K32 | Outro | 0,250 | -0,841 [-1,333; -0,442] | 0,001273 | 1219/1224 | 24/0 |
| oraculo_residual | Continuação na mesma coluna | 0,591 | -0,636 [-1,167; -0,238] | 0,002866 | 3134/3149 | 33/0 |
| oraculo_residual | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| oraculo_residual | Entrada/saída de tabela ou imagem | 0,182 | -0,023 [-0,077; 0,000] | 0,317311 | 53/60 | 1/0 |
| oraculo_residual | Salto ou fronteira de elemento transversal | 0,091 | -0,318 [-1,051; 0,000] | 0,317311 | 21/26 | 13/0 |
| oraculo_residual | Cabeçalho/rodapé/marca marginal | 0,705 | -2,341 [-3,143; -1,488] | 0,000030 | 186/213 | 104/0 |
| oraculo_residual | Outro | 0,273 | -0,818 [-1,273; -0,437] | 0,000652 | 1215/1224 | 20/0 |
| oraculo_roteamento | Continuação na mesma coluna | 0,841 | -0,386 [-0,829; 0,000] | 0,013027 | 3121/3149 | 24/4 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 0,068 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 0,250 | 0,045 [0,000; 0,109] | 0,157373 | 49/60 | 1/4 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 0,364 | -0,045 [-0,154; 0,000] | 0,317311 | 10/26 | 2/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 1,591 | -1,455 [-2,170; -0,757] | 0,000098 | 150/213 | 70/2 |
| oraculo_roteamento | Outro | 0,477 | -0,614 [-1,044; -0,267] | 0,002841 | 1212/1224 | 19/2 |

Operações residuais: 87; por tipo: {'bloco_coluna': 5, 'vizinhas': 40, 'reinsercao': 42}. Páginas com operações: 33. Sequência de cada operação salva no cache.

Roteamento — vitórias exclusivas: {'layoutreader_pronto': 7, 'regra_reordena': 3}; presença no mínimo (inclui empates): {'layoutreader_pronto': 30, 'hibrido67': 29, 'regra_colunas': 17, 'regra_reordena': 23}; escolhidos após desempate: {'layoutreader_pronto': 23, 'regra_colunas': 17, 'regra_reordena': 4}; páginas empatadas: 34.

### Sucessores-ouro fora dos candidatos

Lista integral, sem texto nem coordenadas humanas, identificada por página, linha, unidade e K:

K=12: 49 sucessores ausentes.
- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`: `b27:l6` → `b27:l7`; `b56` → `b58`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`: `b12:l0` → `b1:l0`; `b15` → `b2`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2`: `b4:l4` → `b5:l0`; `b1` → `b12`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3`: `b5:l1` → `b4:l0`; `b27` → `b19`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`: `b4:l32` → `b6:l0`; `b3` → `b19`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0`: `b11:l9` → `b7:l0`; `b114` → `b90`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0`: `b3:l13` → `b3:l14`; `b55` → `b85`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`: `b7:l0` → `b0:l0`; `b70` → `b58`; Outro; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`: `b4:l0` → `b17:l0`; `b62` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p3`: `b10:l0` → `b15:l0`; `b34` → `b33`; Outro; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b34:l0` → `b45:l0`; `b27` → `b61`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b35:l0` → `b21:l0`; `b43` → `b75`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b31:l0` → `b2:l0`; `b101` → `b95`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b8:l0` → `b7:l0`; `b65` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b54:l2` → `b5:l0`; `b66` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`: `b12:l1` → `b5:l0`; `b50` → `b45`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`: `b8:l0` → `b18:l0`; `b26` → `b6`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf#p0`: `b39:l1` → `b51:l0`; `b65` → `b136`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35`: `b34:l6` → `b2:l0`; `b28` → `b118`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5`: `b8:l2` → `b3:l0`; `b14` → `b17`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b35:l0` → `b0:l0`; `b45` → `b123`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b0:l0` → `b15:l0`; `b123` → `b124`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b20:l10` → `b81:l0`; `b84` → `b464`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b32:l2` → `b13:l0`; `b416` → `b362`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b57:l0` → `b66:l0`; `b74` → `b73`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b66:l0` → `b25:l0`; `b73` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b2:l1` → `b50:l0`; `b125` → `b135`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6`: `b32:l13` → `b21:l0`; `b165` → `b108`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b101:l1` → `b46:l0`; `b71` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b12:l1` → `b29:l0`; `b308` → `b167`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b29:l0` → `b100:l0`; `b167` → `b272`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b84:l3` → `b51:l0`; `b99` → `b128`; Outro; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b93:l1` → `b37:l0`; `b88` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b88:l2` → `b120:l0`; `b173` → `b223`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b79:l0` → `b127:l0`; `b109` → `b321`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13`: `b9:l1` → `b30:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13`: `b27:l4` → `b27:l5`; `b82` → `b30`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rr/2021-09-23_DiarioRR.pdf#p10`: `b9:l1` → `b1:l0`; `b14` → `b24`; Cabeçalho/rodapé/marca marginal; erro da regra: False.
- `official_diary_sc/2023-11-27_22151.pdf#p28`: `b22:l3` → `b30:l0`; `b251` → `b69`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b35:l0` → `b4:l0`; `b10` → `b54`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b21:l0` → `b15:l0`; `b84` → `b20`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b15:l0` → `b11:l0`; `b20` → `b1`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b24:l0` → `b26:l0`; `b70` → `b35`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b4:l0` → `b13:l0`; `b12` → `b102`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b44:l0` → `b22:l0`; `b117` → `b85`; Salto ou fronteira de elemento transversal; erro da regra: False.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b37:l0` → `b7:l0`; `b11` → `b96`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2022-12-13_4783.pdf#p10`: `b24:l1` → `b11:l0`; `b65` → `b40`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2024-04-17_5147.pdf#p47`: `b71:l0` → `b49:l0`; `b21` → `b102`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2024-04-17_5147.pdf#p47`: `b56:l1` → `b35:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.

K=24: 35 sucessores ausentes.
- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`: `b27:l6` → `b27:l7`; `b56` → `b58`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf#p3`: `b5:l1` → `b4:l0`; `b27` → `b19`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0`: `b11:l9` → `b7:l0`; `b114` → `b90`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`: `b7:l0` → `b0:l0`; `b70` → `b58`; Outro; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`: `b4:l0` → `b17:l0`; `b62` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b34:l0` → `b45:l0`; `b27` → `b61`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b35:l0` → `b21:l0`; `b43` → `b75`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b8:l0` → `b7:l0`; `b65` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b54:l2` → `b5:l0`; `b66` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`: `b8:l0` → `b18:l0`; `b26` → `b6`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35`: `b34:l6` → `b2:l0`; `b28` → `b118`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5`: `b8:l2` → `b3:l0`; `b14` → `b17`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b35:l0` → `b0:l0`; `b45` → `b123`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b0:l0` → `b15:l0`; `b123` → `b124`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b20:l10` → `b81:l0`; `b84` → `b464`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b32:l2` → `b13:l0`; `b416` → `b362`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b57:l0` → `b66:l0`; `b74` → `b73`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b66:l0` → `b25:l0`; `b73` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b2:l1` → `b50:l0`; `b125` → `b135`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6`: `b32:l13` → `b21:l0`; `b165` → `b108`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b101:l1` → `b46:l0`; `b71` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b12:l1` → `b29:l0`; `b308` → `b167`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b29:l0` → `b100:l0`; `b167` → `b272`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b93:l1` → `b37:l0`; `b88` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b88:l2` → `b120:l0`; `b173` → `b223`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b79:l0` → `b127:l0`; `b109` → `b321`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13`: `b9:l1` → `b30:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b35:l0` → `b4:l0`; `b10` → `b54`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b15:l0` → `b11:l0`; `b20` → `b1`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b4:l0` → `b13:l0`; `b12` → `b102`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b44:l0` → `b22:l0`; `b117` → `b85`; Salto ou fronteira de elemento transversal; erro da regra: False.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b37:l0` → `b7:l0`; `b11` → `b96`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2022-12-13_4783.pdf#p10`: `b24:l1` → `b11:l0`; `b65` → `b40`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2024-04-17_5147.pdf#p47`: `b71:l0` → `b49:l0`; `b21` → `b102`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2024-04-17_5147.pdf#p47`: `b56:l1` → `b35:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.

K=32: 30 sucessores ausentes.
- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`: `b27:l6` → `b27:l7`; `b56` → `b58`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0`: `b11:l9` → `b7:l0`; `b114` → `b90`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`: `b4:l0` → `b17:l0`; `b62` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b34:l0` → `b45:l0`; `b27` → `b61`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: `b35:l0` → `b21:l0`; `b43` → `b75`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b8:l0` → `b7:l0`; `b65` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114`: `b54:l2` → `b5:l0`; `b66` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`: `b8:l0` → `b18:l0`; `b26` → `b6`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35`: `b34:l6` → `b2:l0`; `b28` → `b118`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5`: `b8:l2` → `b3:l0`; `b14` → `b17`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b35:l0` → `b0:l0`; `b45` → `b123`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b0:l0` → `b15:l0`; `b123` → `b124`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b20:l10` → `b81:l0`; `b84` → `b464`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`: `b32:l2` → `b13:l0`; `b416` → `b362`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b66:l0` → `b25:l0`; `b73` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41`: `b2:l1` → `b50:l0`; `b125` → `b135`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6`: `b32:l13` → `b21:l0`; `b165` → `b108`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b101:l1` → `b46:l0`; `b71` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b12:l1` → `b29:l0`; `b308` → `b167`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b29:l0` → `b100:l0`; `b167` → `b272`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b93:l1` → `b37:l0`; `b88` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b88:l2` → `b120:l0`; `b173` → `b223`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `b79:l0` → `b127:l0`; `b109` → `b321`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p13`: `b9:l1` → `b30:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14`: `b15:l0` → `b11:l0`; `b20` → `b1`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b4:l0` → `b13:l0`; `b12` → `b102`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b44:l0` → `b22:l0`; `b117` → `b85`; Salto ou fronteira de elemento transversal; erro da regra: False.
- `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: `b37:l0` → `b7:l0`; `b11` → `b96`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2022-12-13_4783.pdf#p10`: `b24:l1` → `b11:l0`; `b65` → `b40`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_to/2024-04-17_5147.pdf#p47`: `b56:l1` → `b35:l0`; `b83` → `b75`; Cabeçalho/rodapé/marca marginal; erro da regra: True.

## validacao_silver

Páginas processadas: 15; veículos: 1.

| Método | n | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| regra_colunas | 15 | 0,957218 | 16,667 | 10,285 | 0,952328 | 0,910859 | 0,000 [0,000; 0,000] | 1,000000 | 0/15/0 | 0/0 | 100% |
| hibrido67 (parcial) | 13 | 0,958544 | 17,846 | 9,554 | 0,955769 | 0,916132 | 0,000 [0,000; 0,000] | 1,000000 | 0/13/0 | 0/0 | 100% |
| layoutreader_pronto | 0 | indisponível | — | — | — | — | — | — | — | — | — |
| regra_reordena | 0 | indisponível | — | — | — | — | — | — | — | — | — |
| oraculo_decodificador_guloso_K12 | 15 | 0,884257 | 7,867 | 4,733 | 0,974786 | 0,959917 | -8,800 [-8,800; -8,800] | 0,317311 | 11/4/0 | 133/1 | 100% |
| oraculo_decodificador_matching_K12 | 15 | 0,926062 | 7,733 | 4,482 | 0,977447 | 0,962161 | -8,933 [-8,933; -8,933] | 0,317311 | 11/4/0 | 135/1 | 100% |
| oraculo_decodificador_maxregret_K12 | 15 | 0,884257 | 7,867 | 4,733 | 0,974786 | 0,959917 | -8,800 [-8,800; -8,800] | 0,317311 | 11/4/0 | 133/1 | 100% |
| oraculo_decodificador_guloso_K24 | 15 | 0,917701 | 6,933 | 4,034 | 0,979389 | 0,966135 | -9,733 [-9,733; -9,733] | 0,317311 | 11/4/0 | 146/0 | 100% |
| oraculo_decodificador_matching_K24 | 15 | 0,968748 | 6,600 | 3,482 | 0,984100 | 0,971043 | -10,067 [-10,067; -10,067] | 0,317311 | 11/4/0 | 151/0 | 100% |
| oraculo_decodificador_maxregret_K24 | 15 | 0,917701 | 6,933 | 4,034 | 0,979389 | 0,966135 | -9,733 [-9,733; -9,733] | 0,317311 | 11/4/0 | 146/0 | 100% |
| oraculo_decodificador_guloso_K32 | 15 | 0,917122 | 6,467 | 3,404 | 0,984409 | 0,971818 | -10,200 [-10,200; -10,200] | 0,317311 | 11/4/0 | 153/0 | 100% |
| oraculo_decodificador_matching_K32 | 15 | 0,963931 | 6,333 | 3,345 | 0,984810 | 0,972372 | -10,333 [-10,333; -10,333] | 0,317311 | 11/4/0 | 155/0 | 100% |
| oraculo_decodificador_maxregret_K32 | 15 | 0,917122 | 6,467 | 3,404 | 0,984409 | 0,971818 | -10,200 [-10,200; -10,200] | 0,317311 | 11/4/0 | 153/0 | 100% |
| oraculo_residual | 15 | 0,969152 | 6,333 | 3,739 | 0,980504 | 0,968800 | -10,333 [-10,333; -10,333] | 0,317311 | 11/4/0 | 155/0 | 100% |
| oraculo_roteamento | 0 | indisponível | — | — | — | — | — | — | — | — | — |

### Recall de candidatos por classe

Regra e híbrido 67 são referências na tabela acima; não geram candidatos. Recall não é uma métrica de ordem: a família (a) não recebe τ artificial no JSON.

| K | Classe | Presentes/elegíveis | Recall | Erros presentes/elegíveis | Recall erros | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 2244/2245 | 99,96% | 20/21 | 95,24% | 0 | 0 |
| 12 | Fim de coluna → topo da próxima | 3/3 | 100,00% | 0/0 | indisponível% | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 12/12 | 100,00% | 2/2 | 100,00% | 0 | 6 |
| 12 | Salto ou fronteira de elemento transversal | 10/13 | 76,92% | 5/7 | 71,43% | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 95/132 | 71,97% | 49/86 | 56,98% | 0 | 0 |
| 12 | Outro | 113/139 | 81,29% | 51/77 | 66,23% | 2462 | 50 |
| 24 | Continuação na mesma coluna | 2245/2245 | 100,00% | 21/21 | 100,00% | 0 | 0 |
| 24 | Fim de coluna → topo da próxima | 3/3 | 100,00% | 0/0 | indisponível% | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 12/12 | 100,00% | 2/2 | 100,00% | 0 | 6 |
| 24 | Salto ou fronteira de elemento transversal | 13/13 | 100,00% | 7/7 | 100,00% | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 96/132 | 72,73% | 50/86 | 58,14% | 0 | 0 |
| 24 | Outro | 127/139 | 91,37% | 65/77 | 84,42% | 2462 | 50 |
| 32 | Continuação na mesma coluna | 2245/2245 | 100,00% | 21/21 | 100,00% | 0 | 0 |
| 32 | Fim de coluna → topo da próxima | 3/3 | 100,00% | 0/0 | indisponível% | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 12/12 | 100,00% | 2/2 | 100,00% | 0 | 6 |
| 32 | Salto ou fronteira de elemento transversal | 13/13 | 100,00% | 7/7 | 100,00% | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 99/132 | 75,00% | 53/86 | 61,63% | 0 | 0 |
| 32 | Outro | 130/139 | 93,53% | 68/77 | 88,31% | 2462 | 50 |

### Decomposição por classe de erro da regra

| Método | Classe | Quebras/pág | Δ quebras [IC95 veículo] | p veículo | Sucessores certos/ouro | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra_colunas | Continuação na mesma coluna | 1,400 | 0,000 [0,000; 0,000] | 1,000000 | 2224/2245 | 0/0 |
| regra_colunas | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| regra_colunas | Entrada/saída de tabela ou imagem | 0,533 | 0,000 [0,000; 0,000] | 1,000000 | 10/18 | 0/0 |
| regra_colunas | Salto ou fronteira de elemento transversal | 0,400 | 0,000 [0,000; 0,000] | 1,000000 | 6/13 | 0/0 |
| regra_colunas | Cabeçalho/rodapé/marca marginal | 5,267 | 0,000 [0,000; 0,000] | 1,000000 | 46/132 | 0/0 |
| regra_colunas | Outro | 9,067 | 0,000 [0,000; 0,000] | 1,000000 | 2473/2601 | 0/0 |
| hibrido67 (parcial) | Continuação na mesma coluna | 1,615 | 0,000 [0,000; 0,000] | 1,000000 | 2202/2223 | 0/0 |
| hibrido67 (parcial) | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| hibrido67 (parcial) | Entrada/saída de tabela ou imagem | 0,231 | 0,000 [0,000; 0,000] | 1,000000 | 10/13 | 0/0 |
| hibrido67 (parcial) | Salto ou fronteira de elemento transversal | 0,462 | 0,000 [0,000; 0,000] | 1,000000 | 6/13 | 0/0 |
| hibrido67 (parcial) | Cabeçalho/rodapé/marca marginal | 5,462 | 0,000 [0,000; 0,000] | 1,000000 | 41/118 | 0/0 |
| hibrido67 (parcial) | Outro | 10,077 | 0,000 [0,000; 0,000] | 1,000000 | 216/340 | 0/0 |
| layoutreader_pronto | indisponível | — | — | — | — | — |
| regra_reordena | indisponível | — | — | — | — | — |
| oraculo_decodificador_guloso_K12 | Continuação na mesma coluna | 0,067 | -1,333 [-1,333; -1,333] | 0,317311 | 2244/2245 | 20/0 |
| oraculo_decodificador_guloso_K12 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_guloso_K12 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_guloso_K12 | Salto ou fronteira de elemento transversal | 0,200 | -0,200 [-0,200; -0,200] | 0,317311 | 10/13 | 5/1 |
| oraculo_decodificador_guloso_K12 | Cabeçalho/rodapé/marca marginal | 2,067 | -3,200 [-3,200; -3,200] | 0,317311 | 96/132 | 50/0 |
| oraculo_decodificador_guloso_K12 | Outro | 5,133 | -3,933 [-3,933; -3,933] | 0,317311 | 2529/2601 | 56/0 |
| oraculo_decodificador_matching_K12 | Continuação na mesma coluna | 0,067 | -1,333 [-1,333; -1,333] | 0,317311 | 2244/2245 | 20/0 |
| oraculo_decodificador_matching_K12 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_matching_K12 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_matching_K12 | Salto ou fronteira de elemento transversal | 0,200 | -0,200 [-0,200; -0,200] | 0,317311 | 10/13 | 5/1 |
| oraculo_decodificador_matching_K12 | Cabeçalho/rodapé/marca marginal | 1,867 | -3,400 [-3,400; -3,400] | 0,317311 | 98/132 | 52/0 |
| oraculo_decodificador_matching_K12 | Outro | 5,200 | -3,867 [-3,867; -3,867] | 0,317311 | 2529/2601 | 56/0 |
| oraculo_decodificador_maxregret_K12 | Continuação na mesma coluna | 0,067 | -1,333 [-1,333; -1,333] | 0,317311 | 2244/2245 | 20/0 |
| oraculo_decodificador_maxregret_K12 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_maxregret_K12 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_maxregret_K12 | Salto ou fronteira de elemento transversal | 0,200 | -0,200 [-0,200; -0,200] | 0,317311 | 10/13 | 5/1 |
| oraculo_decodificador_maxregret_K12 | Cabeçalho/rodapé/marca marginal | 2,067 | -3,200 [-3,200; -3,200] | 0,317311 | 96/132 | 50/0 |
| oraculo_decodificador_maxregret_K12 | Outro | 5,133 | -3,933 [-3,933; -3,933] | 0,317311 | 2529/2601 | 56/0 |
| oraculo_decodificador_guloso_K24 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_guloso_K24 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_guloso_K24 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_guloso_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_guloso_K24 | Cabeçalho/rodapé/marca marginal | 2,067 | -3,200 [-3,200; -3,200] | 0,317311 | 97/132 | 51/0 |
| oraculo_decodificador_guloso_K24 | Outro | 4,467 | -4,600 [-4,600; -4,600] | 0,317311 | 2538/2601 | 65/0 |
| oraculo_decodificador_matching_K24 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_matching_K24 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_matching_K24 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_matching_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_matching_K24 | Cabeçalho/rodapé/marca marginal | 1,800 | -3,467 [-3,467; -3,467] | 0,317311 | 100/132 | 54/0 |
| oraculo_decodificador_matching_K24 | Outro | 4,400 | -4,667 [-4,667; -4,667] | 0,317311 | 2540/2601 | 67/0 |
| oraculo_decodificador_maxregret_K24 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_maxregret_K24 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_maxregret_K24 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_maxregret_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_maxregret_K24 | Cabeçalho/rodapé/marca marginal | 2,067 | -3,200 [-3,200; -3,200] | 0,317311 | 97/132 | 51/0 |
| oraculo_decodificador_maxregret_K24 | Outro | 4,467 | -4,600 [-4,600; -4,600] | 0,317311 | 2538/2601 | 65/0 |
| oraculo_decodificador_guloso_K32 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_guloso_K32 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_guloso_K32 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_guloso_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_guloso_K32 | Cabeçalho/rodapé/marca marginal | 1,800 | -3,467 [-3,467; -3,467] | 0,317311 | 100/132 | 54/0 |
| oraculo_decodificador_guloso_K32 | Outro | 4,267 | -4,800 [-4,800; -4,800] | 0,317311 | 2542/2601 | 69/0 |
| oraculo_decodificador_matching_K32 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_matching_K32 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_matching_K32 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_matching_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_matching_K32 | Cabeçalho/rodapé/marca marginal | 1,600 | -3,667 [-3,667; -3,667] | 0,317311 | 101/132 | 55/0 |
| oraculo_decodificador_matching_K32 | Outro | 4,333 | -4,733 [-4,733; -4,733] | 0,317311 | 2543/2601 | 70/0 |
| oraculo_decodificador_maxregret_K32 | Continuação na mesma coluna | 0,000 | -1,400 [-1,400; -1,400] | 0,317311 | 2245/2245 | 21/0 |
| oraculo_decodificador_maxregret_K32 | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_decodificador_maxregret_K32 | Entrada/saída de tabela ou imagem | 0,400 | -0,133 [-0,133; -0,133] | 0,317311 | 12/18 | 2/0 |
| oraculo_decodificador_maxregret_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,400 [-0,400; -0,400] | 0,317311 | 13/13 | 7/0 |
| oraculo_decodificador_maxregret_K32 | Cabeçalho/rodapé/marca marginal | 1,800 | -3,467 [-3,467; -3,467] | 0,317311 | 100/132 | 54/0 |
| oraculo_decodificador_maxregret_K32 | Outro | 4,267 | -4,800 [-4,800; -4,800] | 0,317311 | 2542/2601 | 69/0 |
| oraculo_residual | Continuação na mesma coluna | 0,200 | -1,200 [-1,200; -1,200] | 0,317311 | 2242/2245 | 18/0 |
| oraculo_residual | Fim de coluna → topo da próxima | 0,000 | 0,000 [0,000; 0,000] | 1,000000 | 3/3 | 0/0 |
| oraculo_residual | Entrada/saída de tabela ou imagem | 0,533 | 0,000 [0,000; 0,000] | 1,000000 | 10/18 | 0/0 |
| oraculo_residual | Salto ou fronteira de elemento transversal | 0,400 | 0,000 [0,000; 0,000] | 1,000000 | 7/13 | 1/0 |
| oraculo_residual | Cabeçalho/rodapé/marca marginal | 1,133 | -4,133 [-4,133; -4,133] | 0,317311 | 108/132 | 62/0 |
| oraculo_residual | Outro | 4,067 | -5,000 [-5,000; -5,000] | 0,317311 | 2547/2601 | 74/0 |
| oraculo_roteamento | indisponível | — | — | — | — | — |

Operações residuais: 73; por tipo: {'reinsercao': 35, 'bloco_coluna': 30, 'vizinhas': 8}. Páginas com operações: 11. Sequência de cada operação salva no cache.

Roteamento indisponível: faltam predições salvas dos quatro métodos; nenhuma média de subconjunto é declarada teto da bancada.

### Sucessores-ouro fora dos candidatos

Lista integral, sem texto nem coordenadas humanas, identificada por página, linha, unidade e K:

K=12: 67 sucessores ausentes.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l0` → `silver:l1`; `b95` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l1` → `silver:l2`; `b92` → `b106`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l25` → `silver:l26`; `b115` → `b8`; Salto ou fronteira de elemento transversal; erro da regra: False.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l49` → `silver:l50`; `b87` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l106` → `silver:l107`; `b152` → `b26`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l159` → `silver:l160`; `b164` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l161` → `silver:l162`; `b12` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l171` → `silver:l172`; `b170` → `b102`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l172` → `silver:l173`; `b102` → `b103`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l174` → `silver:l175`; `b165` → `b46`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l175` → `silver:l176`; `b46` → `b51`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l177` → `silver:l178`; `b139` → `b2`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l0` → `silver:l1`; `b121` → `b35`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l1` → `silver:l2`; `b35` → `b93`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l75` → `silver:l76`; `b103` → `b70`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l167` → `silver:l168`; `b120` → `b62`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l169` → `silver:l170`; `b20` → `b42`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l0` → `silver:l1`; `b253` → `b27`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l1` → `silver:l2`; `b27` → `b77`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l101` → `silver:l102`; `b194` → `b163`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l190` → `silver:l191`; `b127` → `b172`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l283` → `silver:l284`; `b254` → `b166`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l3` → `silver:l4`; `b8` → `b45`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l103` → `silver:l104`; `b271` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l200` → `silver:l201`; `b267` → `b60`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l296` → `silver:l297`; `b126` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l0` → `silver:l1`; `b218` → `b19`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l1` → `silver:l2`; `b19` → `b95`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l101` → `silver:l102`; `b166` → `b154`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l194` → `silver:l195`; `b133` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l283` → `silver:l284`; `b46` → `b143`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: `silver:l3` → `silver:l4`; `b3` → `b18`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: `silver:l17` → `silver:l18`; `b13` → `b11`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: `silver:l30` → `silver:l31`; `b16` → `b20`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l0` → `silver:l1`; `b35` → `b169`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l1` → `silver:l2`; `b169` → `b125`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l65` → `silver:l66`; `b132` → `b119`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l66` → `silver:l67`; `b119` → `b139`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l67` → `silver:l68`; `b139` → `b37`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l68` → `silver:l69`; `b37` → `b200`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l93` → `silver:l94`; `b15` → `b114`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l98` → `silver:l99`; `b80` → `b36`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l99` → `silver:l100`; `b36` → `b67`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l100` → `silver:l101`; `b67` → `b171`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l111` → `silver:l112`; `b84` → `b140`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l113` → `silver:l114`; `b47` → `b72`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l115` → `silver:l116`; `b17` → `b2`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l200` → `silver:l201`; `b154` → `b190`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l3` → `silver:l4`; `b41` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l59` → `silver:l60`; `b73` → `b1`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l72` → `silver:l73`; `b5` → `b54`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l80` → `silver:l81`; `b76` → `b113`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l176` → `silver:l177`; `b170` → `b153`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l178` → `silver:l179`; `b169` → `b7`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l4` → `silver:l5`; `b79` → `b13`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l5` → `silver:l6`; `b13` → `b163`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l10` → `silver:l11`; `b113` → `b34`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l11` → `silver:l12`; `b34` → `b5`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l16` → `silver:l17`; `b152` → `b206`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l17` → `silver:l18`; `b206` → `b195`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l22` → `silver:l23`; `b99` → `b189`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l95` → `silver:l96`; `b91` → `b115`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l97` → `silver:l98`; `b102` → `b14`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l118` → `silver:l119`; `b44` → `b164`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l120` → `silver:l121`; `b140` → `b97`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l162` → `silver:l163`; `b64` → `b151`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l206` → `silver:l207`; `b174` → `b49`; Outro; erro da regra: True.

K=24: 48 sucessores ausentes.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l0` → `silver:l1`; `b95` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l1` → `silver:l2`; `b92` → `b106`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l49` → `silver:l50`; `b87` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l106` → `silver:l107`; `b152` → `b26`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l159` → `silver:l160`; `b164` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l161` → `silver:l162`; `b12` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l171` → `silver:l172`; `b170` → `b102`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l172` → `silver:l173`; `b102` → `b103`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l174` → `silver:l175`; `b165` → `b46`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l175` → `silver:l176`; `b46` → `b51`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l177` → `silver:l178`; `b139` → `b2`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l0` → `silver:l1`; `b121` → `b35`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l1` → `silver:l2`; `b35` → `b93`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l75` → `silver:l76`; `b103` → `b70`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l167` → `silver:l168`; `b120` → `b62`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l169` → `silver:l170`; `b20` → `b42`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l0` → `silver:l1`; `b253` → `b27`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l1` → `silver:l2`; `b27` → `b77`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l101` → `silver:l102`; `b194` → `b163`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l190` → `silver:l191`; `b127` → `b172`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l283` → `silver:l284`; `b254` → `b166`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l3` → `silver:l4`; `b8` → `b45`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l103` → `silver:l104`; `b271` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l200` → `silver:l201`; `b267` → `b60`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l296` → `silver:l297`; `b126` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l0` → `silver:l1`; `b218` → `b19`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l1` → `silver:l2`; `b19` → `b95`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l101` → `silver:l102`; `b166` → `b154`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l194` → `silver:l195`; `b133` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l283` → `silver:l284`; `b46` → `b143`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: `silver:l3` → `silver:l4`; `b3` → `b18`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46`: `silver:l17` → `silver:l18`; `b13` → `b11`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l0` → `silver:l1`; `b35` → `b169`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l1` → `silver:l2`; `b169` → `b125`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l65` → `silver:l66`; `b132` → `b119`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l66` → `silver:l67`; `b119` → `b139`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l68` → `silver:l69`; `b37` → `b200`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l93` → `silver:l94`; `b15` → `b114`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l98` → `silver:l99`; `b80` → `b36`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l111` → `silver:l112`; `b84` → `b140`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l113` → `silver:l114`; `b47` → `b72`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l200` → `silver:l201`; `b154` → `b190`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l3` → `silver:l4`; `b41` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l80` → `silver:l81`; `b76` → `b113`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l176` → `silver:l177`; `b170` → `b153`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l178` → `silver:l179`; `b169` → `b7`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l17` → `silver:l18`; `b206` → `b195`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l206` → `silver:l207`; `b174` → `b49`; Outro; erro da regra: True.

K=32: 42 sucessores ausentes.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l0` → `silver:l1`; `b95` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l1` → `silver:l2`; `b92` → `b106`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l49` → `silver:l50`; `b87` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l106` → `silver:l107`; `b152` → `b26`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l159` → `silver:l160`; `b164` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l161` → `silver:l162`; `b12` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l171` → `silver:l172`; `b170` → `b102`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l172` → `silver:l173`; `b102` → `b103`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l174` → `silver:l175`; `b165` → `b46`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l175` → `silver:l176`; `b46` → `b51`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p1`: `silver:l177` → `silver:l178`; `b139` → `b2`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l0` → `silver:l1`; `b121` → `b35`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l1` → `silver:l2`; `b35` → `b93`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l75` → `silver:l76`; `b103` → `b70`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13`: `silver:l167` → `silver:l168`; `b120` → `b62`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l0` → `silver:l1`; `b253` → `b27`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l1` → `silver:l2`; `b27` → `b77`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l101` → `silver:l102`; `b194` → `b163`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l190` → `silver:l191`; `b127` → `b172`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p17`: `silver:l283` → `silver:l284`; `b254` → `b166`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l3` → `silver:l4`; `b8` → `b45`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l103` → `silver:l104`; `b271` → `b133`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l200` → `silver:l201`; `b267` → `b60`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p2`: `silver:l296` → `silver:l297`; `b126` → `b138`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l0` → `silver:l1`; `b218` → `b19`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l1` → `silver:l2`; `b19` → `b95`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l101` → `silver:l102`; `b166` → `b154`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l194` → `silver:l195`; `b133` → `b92`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p39`: `silver:l283` → `silver:l284`; `b46` → `b143`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l0` → `silver:l1`; `b35` → `b169`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l1` → `silver:l2`; `b169` → `b125`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l66` → `silver:l67`; `b119` → `b139`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l68` → `silver:l69`; `b37` → `b200`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l93` → `silver:l94`; `b15` → `b114`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l98` → `silver:l99`; `b80` → `b36`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l113` → `silver:l114`; `b47` → `b72`; Outro; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p11`: `silver:l200` → `silver:l201`; `b154` → `b190`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l3` → `silver:l4`; `b41` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l80` → `silver:l81`; `b76` → `b113`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l176` → `silver:l177`; `b170` → `b153`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2021-11-20_Ordinaria.pdf#p24`: `silver:l178` → `silver:l179`; `b169` → `b7`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p3`: `silver:l206` → `silver:l207`; `b174` → `b49`; Outro; erro da regra: True.

## golden_v3_novo

Páginas processadas: 27; veículos: 10.

| Método | n | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| regra_colunas | 27 | 0,959557 | 9,222 | 17,206 | 0,928415 | 0,911301 | 0,000 [0,000; 0,000] | 1,000000 | 0/27/0 | 0/0 | 100% |
| hibrido67 | 27 | 0,958977 | 7,889 | 13,739 | 0,941220 | 0,938410 | -1,333 [-2,649; -0,364] | 0,027670 | 7/18/2 | 39/5 | 100% |
| layoutreader_pronto | 27 | 0,950875 | 16,222 | 18,145 | 0,927948 | 0,908337 | 7,000 [-2,130; 22,250] | 0,838153 | 14/5/8 | 95/285 | 100% |
| regra_reordena | 27 | 0,959578 | 7,778 | 14,720 | 0,936469 | 0,925754 | -1,444 [-2,391; 0,263] | 0,425964 | 7/18/2 | 49/8 | 100% |
| oraculo_decodificador_guloso_K12 | 27 | 0,944079 | 2,000 | 3,197 | 0,976672 | 0,986234 | -7,222 [-9,930; -4,631] | 0,004920 | 22/5/0 | 184/0 | 100% |
| oraculo_decodificador_matching_K12 | 27 | 0,958985 | 1,889 | 3,165 | 0,976915 | 0,986517 | -7,333 [-10,025; -4,645] | 0,005005 | 22/5/0 | 187/0 | 100% |
| oraculo_decodificador_maxregret_K12 | 27 | 0,944079 | 2,000 | 3,197 | 0,976672 | 0,986234 | -7,222 [-9,930; -4,631] | 0,004920 | 22/5/0 | 184/0 | 100% |
| oraculo_decodificador_guloso_K24 | 27 | 0,926477 | 1,370 | 1,838 | 0,983350 | 0,992005 | -7,852 [-11,206; -4,863] | 0,005005 | 22/5/0 | 201/0 | 100% |
| oraculo_decodificador_matching_K24 | 27 | 0,942610 | 1,259 | 1,806 | 0,983593 | 0,992288 | -7,963 [-11,261; -4,875] | 0,005034 | 22/5/0 | 204/0 | 100% |
| oraculo_decodificador_maxregret_K24 | 27 | 0,926477 | 1,370 | 1,838 | 0,983350 | 0,992005 | -7,852 [-11,206; -4,863] | 0,005005 | 22/5/0 | 201/0 | 100% |
| oraculo_decodificador_guloso_K32 | 27 | 0,926477 | 1,370 | 1,838 | 0,983350 | 0,992005 | -7,852 [-11,206; -4,863] | 0,005005 | 22/5/0 | 201/0 | 100% |
| oraculo_decodificador_matching_K32 | 27 | 0,942610 | 1,259 | 1,806 | 0,983593 | 0,992288 | -7,963 [-11,261; -4,875] | 0,005034 | 22/5/0 | 204/0 | 100% |
| oraculo_decodificador_maxregret_K32 | 27 | 0,926477 | 1,370 | 1,838 | 0,983350 | 0,992005 | -7,852 [-11,206; -4,863] | 0,005005 | 22/5/0 | 201/0 | 100% |
| oraculo_residual | 27 | 0,962132 | 2,222 | 3,681 | 0,975461 | 0,977345 | -7,000 [-10,500; -3,526] | 0,005034 | 22/5/0 | 179/0 | 100% |
| oraculo_roteamento | 27 | 0,974915 | 6,000 | 10,861 | 0,950999 | 0,951781 | -3,222 [-3,958; -2,176] | 0,010961 | 16/11/0 | 95/12 | 100% |

### Recall de candidatos por classe

Regra e híbrido 67 são referências na tabela acima; não geram candidatos. Recall não é uma métrica de ordem: a família (a) não recebe τ artificial no JSON.

| K | Classe | Presentes/elegíveis | Recall | Erros presentes/elegíveis | Recall erros | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 1877/1882 | 99,73% | 110/115 | 95,65% | 0 | 0 |
| 12 | Fim de coluna → topo da próxima | 6/8 | 75,00% | 0/2 | 0,00% | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 63/65 | 96,92% | 7/8 | 87,50% | 0 | 1 |
| 12 | Salto ou fronteira de elemento transversal | 7/7 | 100,00% | 2/2 | 100,00% | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 72/86 | 83,72% | 27/41 | 65,85% | 1 | 0 |
| 12 | Outro | 84/110 | 76,36% | 37/63 | 58,73% | 752 | 6 |
| 24 | Continuação na mesma coluna | 1882/1882 | 100,00% | 115/115 | 100,00% | 0 | 0 |
| 24 | Fim de coluna → topo da próxima | 6/8 | 75,00% | 0/2 | 0,00% | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 64/65 | 98,46% | 7/8 | 87,50% | 0 | 1 |
| 24 | Salto ou fronteira de elemento transversal | 7/7 | 100,00% | 2/2 | 100,00% | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 78/86 | 90,70% | 33/41 | 80,49% | 1 | 0 |
| 24 | Outro | 90/110 | 81,82% | 43/63 | 68,25% | 752 | 6 |
| 32 | Continuação na mesma coluna | 1882/1882 | 100,00% | 115/115 | 100,00% | 0 | 0 |
| 32 | Fim de coluna → topo da próxima | 6/8 | 75,00% | 0/2 | 0,00% | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 64/65 | 98,46% | 7/8 | 87,50% | 0 | 1 |
| 32 | Salto ou fronteira de elemento transversal | 7/7 | 100,00% | 2/2 | 100,00% | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 78/86 | 90,70% | 33/41 | 80,49% | 1 | 0 |
| 32 | Outro | 90/110 | 81,82% | 43/63 | 68,25% | 752 | 6 |

### Decomposição por classe de erro da regra

| Método | Classe | Quebras/pág | Δ quebras [IC95 veículo] | p veículo | Sucessores certos/ouro | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra_colunas | Continuação na mesma coluna | 3,704 | 0,000 [0,000; 0,000] | 1,000000 | 1767/1882 | 0/0 |
| regra_colunas | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| regra_colunas | Entrada/saída de tabela ou imagem | 0,333 | 0,000 [0,000; 0,000] | 1,000000 | 57/66 | 0/0 |
| regra_colunas | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| regra_colunas | Cabeçalho/rodapé/marca marginal | 1,519 | 0,000 [0,000; 0,000] | 1,000000 | 46/87 | 0/0 |
| regra_colunas | Outro | 3,481 | 0,000 [0,000; 0,000] | 1,000000 | 793/862 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 3,407 | -0,296 [-0,625; -0,062] | 0,046624 | 1777/1882 | 10/0 |
| hibrido67 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,150; 0,000] | 0,317311 | 58/66 | 1/0 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 1,296 | -0,222 [-0,929; 0,000] | 0,157874 | 52/87 | 11/5 |
| hibrido67 | Outro | 2,704 | -0,778 [-1,667; -0,071] | 0,047376 | 810/862 | 17/0 |
| layoutreader_pronto | Continuação na mesma coluna | 12,593 | 8,889 [0,000; 23,684] | 0,410536 | 1527/1882 | 22/262 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,111 | 0,037 [0,000; 0,167] | 0,317311 | 5/8 | 1/2 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,407 | 0,074 [-0,188; 0,286] | 0,953453 | 55/66 | 4/6 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,037 | -0,074 [-0,321; 0,087] | 0,940748 | 6/7 | 2/1 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 0,741 | -0,778 [-1,530; -0,278] | 0,016924 | 66/87 | 25/5 |
| layoutreader_pronto | Outro | 2,333 | -1,148 [-1,750; -0,111] | 0,100680 | 825/862 | 41/9 |
| regra_reordena | Continuação na mesma coluna | 2,889 | -0,815 [-1,559; -0,091] | 0,122706 | 1793/1882 | 29/3 |
| regra_reordena | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,167; 0,000] | 0,317311 | 58/66 | 1/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 1,593 | 0,074 [0,000; 0,308] | 0,317311 | 44/87 | 0/2 |
| regra_reordena | Outro | 2,815 | -0,667 [-1,300; 0,474] | 0,425638 | 809/862 | 19/3 |
| oraculo_decodificador_guloso_K12 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1872/1882 | 105/0 |
| oraculo_decodificador_guloso_K12 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_guloso_K12 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_guloso_K12 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_guloso_K12 | Cabeçalho/rodapé/marca marginal | 0,296 | -1,222 [-2,261; -0,548] | 0,042890 | 78/87 | 32/0 |
| oraculo_decodificador_guloso_K12 | Outro | 1,556 | -1,926 [-3,137; -1,000] | 0,005857 | 830/862 | 37/0 |
| oraculo_decodificador_matching_K12 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1872/1882 | 105/0 |
| oraculo_decodificador_matching_K12 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_matching_K12 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_matching_K12 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_matching_K12 | Cabeçalho/rodapé/marca marginal | 0,185 | -1,333 [-2,412; -0,565] | 0,042890 | 81/87 | 35/0 |
| oraculo_decodificador_matching_K12 | Outro | 1,556 | -1,926 [-3,137; -1,000] | 0,005857 | 830/862 | 37/0 |
| oraculo_decodificador_maxregret_K12 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1872/1882 | 105/0 |
| oraculo_decodificador_maxregret_K12 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_maxregret_K12 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_maxregret_K12 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_maxregret_K12 | Cabeçalho/rodapé/marca marginal | 0,296 | -1,222 [-2,261; -0,548] | 0,042890 | 78/87 | 32/0 |
| oraculo_decodificador_maxregret_K12 | Outro | 1,556 | -1,926 [-3,137; -1,000] | 0,005857 | 830/862 | 37/0 |
| oraculo_decodificador_guloso_K24 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_guloso_K24 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_guloso_K24 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_guloso_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_guloso_K24 | Cabeçalho/rodapé/marca marginal | 0,259 | -1,259 [-2,278; -0,609] | 0,016924 | 80/87 | 34/0 |
| oraculo_decodificador_guloso_K24 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_decodificador_matching_K24 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_matching_K24 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_matching_K24 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_matching_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_matching_K24 | Cabeçalho/rodapé/marca marginal | 0,148 | -1,370 [-2,440; -0,632] | 0,016924 | 83/87 | 37/0 |
| oraculo_decodificador_matching_K24 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_decodificador_maxregret_K24 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_maxregret_K24 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_maxregret_K24 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_maxregret_K24 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_maxregret_K24 | Cabeçalho/rodapé/marca marginal | 0,259 | -1,259 [-2,278; -0,609] | 0,016924 | 80/87 | 34/0 |
| oraculo_decodificador_maxregret_K24 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_decodificador_guloso_K32 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_guloso_K32 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_guloso_K32 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_guloso_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_guloso_K32 | Cabeçalho/rodapé/marca marginal | 0,259 | -1,259 [-2,278; -0,609] | 0,016924 | 80/87 | 34/0 |
| oraculo_decodificador_guloso_K32 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_decodificador_matching_K32 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_matching_K32 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_matching_K32 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_matching_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_matching_K32 | Cabeçalho/rodapé/marca marginal | 0,148 | -1,370 [-2,440; -0,632] | 0,016924 | 83/87 | 37/0 |
| oraculo_decodificador_matching_K32 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_decodificador_maxregret_K32 | Continuação na mesma coluna | 0,037 | -3,667 [-7,088; -0,903] | 0,006864 | 1880/1882 | 113/0 |
| oraculo_decodificador_maxregret_K32 | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_decodificador_maxregret_K32 | Entrada/saída de tabela ou imagem | 0,037 | -0,296 [-0,737; -0,050] | 0,047188 | 65/66 | 8/0 |
| oraculo_decodificador_maxregret_K32 | Salto ou fronteira de elemento transversal | 0,000 | -0,111 [-0,321; 0,000] | 0,317311 | 7/7 | 2/0 |
| oraculo_decodificador_maxregret_K32 | Cabeçalho/rodapé/marca marginal | 0,259 | -1,259 [-2,278; -0,609] | 0,016924 | 80/87 | 34/0 |
| oraculo_decodificador_maxregret_K32 | Outro | 0,963 | -2,519 [-3,353; -1,880] | 0,005857 | 837/862 | 44/0 |
| oraculo_residual | Continuação na mesma coluna | 0,481 | -3,222 [-6,588; -0,516] | 0,010429 | 1870/1882 | 103/0 |
| oraculo_residual | Fim de coluna → topo da próxima | 0,074 | 0,000 [0,000; 0,000] | 1,000000 | 6/8 | 0/0 |
| oraculo_residual | Entrada/saída de tabela ou imagem | 0,222 | -0,111 [-0,400; 0,000] | 0,157874 | 60/66 | 3/0 |
| oraculo_residual | Salto ou fronteira de elemento transversal | 0,037 | -0,074 [-0,214; 0,000] | 0,317311 | 6/7 | 1/0 |
| oraculo_residual | Cabeçalho/rodapé/marca marginal | 0,185 | -1,333 [-2,414; -0,533] | 0,016924 | 79/87 | 33/0 |
| oraculo_residual | Outro | 1,222 | -2,259 [-3,000; -1,529] | 0,005825 | 832/862 | 39/0 |
| oraculo_roteamento | Continuação na mesma coluna | 2,778 | -0,926 [-1,760; -0,100] | 0,062482 | 1800/1882 | 42/9 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 0,037 | -0,037 [-0,107; 0,000] | 0,317311 | 7/8 | 1/0 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 0,296 | -0,037 [-0,150; 0,000] | 0,317311 | 58/66 | 1/0 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 0,111 | 0,000 [0,000; 0,000] | 1,000000 | 5/7 | 0/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 0,889 | -0,630 [-1,333; -0,194] | 0,047376 | 63/87 | 18/1 |
| oraculo_roteamento | Outro | 1,889 | -1,593 [-2,143; -0,789] | 0,016924 | 824/862 | 33/2 |

Operações residuais: 86; por tipo: {'reinsercao': 9, 'vizinhas': 45, 'bloco_coluna': 32}. Páginas com operações: 22. Sequência de cada operação salva no cache.

Roteamento — vitórias exclusivas: {'layoutreader_pronto': 7, 'regra_reordena': 2}; presença no mínimo (inclui empates): {'regra_colunas': 11, 'regra_reordena': 14, 'hibrido67': 16, 'layoutreader_pronto': 19}; escolhidos após desempate: {'regra_colunas': 10, 'layoutreader_pronto': 15, 'regra_reordena': 2}; páginas empatadas: 18.

### Sucessores-ouro fora dos candidatos

Lista integral, sem texto nem coordenadas humanas, identificada por página, linha, unidade e K:

K=12: 49 sucessores ausentes.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5`: `b25:l1` → `b3:l0`; `b30` → `b23`; Outro; erro da regra: True.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5`: `b3:l0` → `b11:l0`; `b23` → `b11`; Outro; erro da regra: True.
- `official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf#p41`: `b7:l0` → `b7:l1`; `b16` → `b13`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p6`: `b4:l23` → `b0:l0`; `b45` → `b4`; Entrada/saída de tabela ou imagem; erro da regra: False.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p56`: `b43:l0` → `b29:l0`; `b11` → `b24`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p60`: `b17:l0` → `b16:l0`; `b82` → `b1`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p14`: `b17:l0` → `b10:l0`; `b44` → `b11`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p24`: `b30:l0` → `b23:l0`; `b48` → `b89`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b51:l0` → `b51:l1`; `b29` → `b77`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b51:l1` → `b2:l0`; `b77` → `b63`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b46:l0` → `b45:l0`; `b20` → `b153`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b45:l14` → `b32:l0`; `b10` → `b158`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b4:l0` → `b58:l0`; `b86` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b7:l15` → `b49:l0`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b39:l0` → `b39:l1`; `b52` → `b140`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b39:l1` → `b21:l0`; `b140` → `b41`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b22:l12` → `b10:l0`; `b143` → `b11`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b1:l0` → `b19:l0`; `b25` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b47:l13` → `b11:l0`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b16:l0` → `b16:l1`; `b100` → `b127`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b16:l1` → `b44:l0`; `b127` → `b149`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b57:l5` → `b36:l0`; `b102` → `b144`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b35:l0` → `b50:l0`; `b8` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b20:l6` → `b26:l0`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b34:l0` → `b34:l1`; `b160` → `b57`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b40:l0` → `b38:l0`; `b117` → `b135`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16`: `b11:l18` → `b8:l0`; `b48` → `b46`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_pi_v2/executive_official_diary_2024_05_29_104_2024_15_340.pdf#p0`: `b13:l2` → `b10:l0`; `b30` → `b18`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223`: `b2:l2` → `b1:l0`; `b2` → `b41`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b28:l0` → `b21:l0`; `b235` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b21:l0` → `b15:l0`; `b289` → `b297`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b15:l0` → `b24:l0`; `b297` → `b111`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b5:l4` → `b11:l0`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b27:l5` → `b20:l0`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b5:l1` → `b4:l0`; `b61` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b4:l0` → `b34:l0`; `b100` → `b30`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b34:l0` → `b38:l0`; `b30` → `b85`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b17:l5` → `b14:l0`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b27:l0` → `b35:l0`; `b78` → `b77`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b3:l1` → `b10:l0`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b11:l0` → `b13:l0`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b9:l31` → `b21:l0`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b21:l31` → `b27:l0`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b30:l4` → `b15:l0`; `b84` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b42:l6` → `b36:l0`; `b31` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b40:l1` → `b33:l0`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b11:l0` → `b46:l0`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b42:l31` → `b34:l0`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b34:l31` → `b37:l0`; `b80` → `b64`; Outro; erro da regra: True.

K=24: 31 sucessores ausentes.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5`: `b25:l1` → `b3:l0`; `b30` → `b23`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b45:l14` → `b32:l0`; `b10` → `b158`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b4:l0` → `b58:l0`; `b86` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b7:l15` → `b49:l0`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b22:l12` → `b10:l0`; `b143` → `b11`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b1:l0` → `b19:l0`; `b25` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b47:l13` → `b11:l0`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b35:l0` → `b50:l0`; `b8` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b20:l6` → `b26:l0`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b40:l0` → `b38:l0`; `b117` → `b135`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16`: `b11:l18` → `b8:l0`; `b48` → `b46`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b28:l0` → `b21:l0`; `b235` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b21:l0` → `b15:l0`; `b289` → `b297`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b15:l0` → `b24:l0`; `b297` → `b111`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b5:l4` → `b11:l0`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b27:l5` → `b20:l0`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b5:l1` → `b4:l0`; `b61` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b4:l0` → `b34:l0`; `b100` → `b30`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b34:l0` → `b38:l0`; `b30` → `b85`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b17:l5` → `b14:l0`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b27:l0` → `b35:l0`; `b78` → `b77`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b3:l1` → `b10:l0`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b11:l0` → `b13:l0`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b9:l31` → `b21:l0`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b21:l31` → `b27:l0`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b30:l4` → `b15:l0`; `b84` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b42:l6` → `b36:l0`; `b31` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b40:l1` → `b33:l0`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b11:l0` → `b46:l0`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b42:l31` → `b34:l0`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b34:l31` → `b37:l0`; `b80` → `b64`; Outro; erro da regra: True.

K=32: 31 sucessores ausentes.
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf#p5`: `b25:l1` → `b3:l0`; `b30` → `b23`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b45:l14` → `b32:l0`; `b10` → `b158`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b4:l0` → `b58:l0`; `b86` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b7:l15` → `b49:l0`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b22:l12` → `b10:l0`; `b143` → `b11`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b1:l0` → `b19:l0`; `b25` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b47:l13` → `b11:l0`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b35:l0` → `b50:l0`; `b8` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b20:l6` → `b26:l0`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `b40:l0` → `b38:l0`; `b117` → `b135`; Outro; erro da regra: True.
- `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16`: `b11:l18` → `b8:l0`; `b48` → `b46`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b28:l0` → `b21:l0`; `b235` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b21:l0` → `b15:l0`; `b289` → `b297`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b15:l0` → `b24:l0`; `b297` → `b111`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b5:l4` → `b11:l0`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `b27:l5` → `b20:l0`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b5:l1` → `b4:l0`; `b61` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b4:l0` → `b34:l0`; `b100` → `b30`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b34:l0` → `b38:l0`; `b30` → `b85`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b17:l5` → `b14:l0`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `b27:l0` → `b35:l0`; `b78` → `b77`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b3:l1` → `b10:l0`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b11:l0` → `b13:l0`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b9:l31` → `b21:l0`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b21:l31` → `b27:l0`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b30:l4` → `b15:l0`; `b84` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `b42:l6` → `b36:l0`; `b31` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b40:l1` → `b33:l0`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b11:l0` → `b46:l0`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b42:l31` → `b34:l0`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `b34:l31` → `b37:l0`; `b80` → `b64`; Outro; erro da regra: True.

## teste_silver

Páginas processadas: 89; veículos: 3.

| Método | n | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões | Cobertura |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| regra_colunas | 89 | 0,959565 | 27,449 | 44,496 | 0,825401 | 0,840212 | 0,000 [0,000; 0,000] | 1,000000 | 0/89/0 | 0/0 | 100% |
| hibrido67 | 89 | 0,959092 | 26,427 | 43,157 | 0,834332 | 0,849525 | -1,022 [-1,895; -0,077] | 0,108809 | 14/72/3 | 102/11 | 100% |
| layoutreader_pronto | 89 | 0,941850 | 31,247 | 41,826 | 0,829754 | 0,841286 | 3,798 [-8,000; 54,231] | 1,000000 | 38/30/21 | 633/972 | 100% |
| regra_reordena | 89 | 0,959615 | 26,449 | 43,643 | 0,831979 | 0,848023 | -1,000 [-1,692; -0,395] | 0,108809 | 24/61/4 | 132/43 | 100% |
| oraculo_decodificador_guloso_K12 | 89 | 0,950428 | 20,719 | 37,260 | 0,858222 | 0,881631 | -6,730 [-15,308; -2,842] | 0,108809 | 63/26/0 | 594/1 | 100% |
| oraculo_decodificador_matching_K12 | 89 | 0,941816 | 20,618 | 37,189 | 0,858663 | 0,881790 | -6,831 [-15,462; -2,842] | 0,108809 | 63/26/0 | 602/0 | 100% |
| oraculo_decodificador_maxregret_K12 | 89 | 0,950428 | 20,719 | 37,260 | 0,858222 | 0,881631 | -6,730 [-15,308; -2,842] | 0,108809 | 63/26/0 | 594/1 | 100% |
| oraculo_decodificador_guloso_K24 | 89 | 0,949617 | 20,157 | 36,371 | 0,861694 | 0,885058 | -7,292 [-15,923; -3,763] | 0,108809 | 64/25/0 | 644/1 | 100% |
| oraculo_decodificador_matching_K24 | 89 | 0,938995 | 20,124 | 36,375 | 0,861290 | 0,884904 | -7,326 [-16,154; -3,763] | 0,108809 | 64/25/0 | 646/0 | 100% |
| oraculo_decodificador_maxregret_K24 | 89 | 0,949617 | 20,157 | 36,371 | 0,861694 | 0,885058 | -7,292 [-15,923; -3,763] | 0,108809 | 64/25/0 | 644/1 | 100% |
| oraculo_decodificador_guloso_K32 | 89 | 0,946949 | 19,775 | 35,714 | 0,865465 | 0,887513 | -7,674 [-16,462; -4,263] | 0,108809 | 64/25/0 | 678/1 | 100% |
| oraculo_decodificador_matching_K32 | 89 | 0,939701 | 19,787 | 35,778 | 0,864818 | 0,887170 | -7,663 [-16,615; -4,237] | 0,108809 | 64/25/0 | 676/0 | 100% |
| oraculo_decodificador_maxregret_K32 | 89 | 0,946949 | 19,775 | 35,714 | 0,865465 | 0,887513 | -7,674 [-16,462; -4,263] | 0,108809 | 64/25/0 | 678/1 | 100% |
| oraculo_residual | 89 | 0,960488 | 19,966 | 35,635 | 0,866151 | 0,887362 | -7,483 [-12,692; -4,000] | 0,108809 | 64/25/0 | 657/0 | 100% |
| oraculo_roteamento | 89 | 0,966534 | 21,225 | 36,811 | 0,860584 | 0,877306 | -6,225 [-8,395; -3,737] | 0,108809 | 44/45/0 | 614/60 | 100% |

### Recall de candidatos por classe

Regra e híbrido 67 são referências na tabela acima; não geram candidatos. Recall não é uma métrica de ordem: a família (a) não recebe τ artificial no JSON.

| K | Classe | Presentes/elegíveis | Recall | Erros presentes/elegíveis | Recall erros | Internos | Inalcançáveis |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | Continuação na mesma coluna | 7133/7140 | 99,90% | 175/180 | 97,22% | 0 | 5 |
| 12 | Fim de coluna → topo da próxima | 27/33 | 81,82% | 0/5 | 0,00% | 0 | 0 |
| 12 | Entrada/saída de tabela ou imagem | 91/94 | 96,81% | 7/10 | 70,00% | 0 | 32 |
| 12 | Salto ou fronteira de elemento transversal | 162/183 | 88,52% | 48/69 | 69,57% | 0 | 0 |
| 12 | Cabeçalho/rodapé/marca marginal | 243/269 | 90,33% | 116/142 | 81,69% | 0 | 38 |
| 12 | Outro | 708/989 | 71,59% | 258/539 | 47,87% | 6058 | 1324 |
| 24 | Continuação na mesma coluna | 7136/7140 | 99,94% | 177/180 | 98,33% | 0 | 5 |
| 24 | Fim de coluna → topo da próxima | 27/33 | 81,82% | 0/5 | 0,00% | 0 | 0 |
| 24 | Entrada/saída de tabela ou imagem | 92/94 | 97,87% | 8/10 | 80,00% | 0 | 32 |
| 24 | Salto ou fronteira de elemento transversal | 169/183 | 92,35% | 55/69 | 79,71% | 0 | 0 |
| 24 | Cabeçalho/rodapé/marca marginal | 246/269 | 91,45% | 119/142 | 83,80% | 0 | 38 |
| 24 | Outro | 748/989 | 75,63% | 298/539 | 55,29% | 6058 | 1324 |
| 32 | Continuação na mesma coluna | 7137/7140 | 99,96% | 177/180 | 98,33% | 0 | 5 |
| 32 | Fim de coluna → topo da próxima | 27/33 | 81,82% | 0/5 | 0,00% | 0 | 0 |
| 32 | Entrada/saída de tabela ou imagem | 92/94 | 97,87% | 8/10 | 80,00% | 0 | 32 |
| 32 | Salto ou fronteira de elemento transversal | 171/183 | 93,44% | 57/69 | 82,61% | 0 | 0 |
| 32 | Cabeçalho/rodapé/marca marginal | 249/269 | 92,57% | 122/142 | 85,92% | 0 | 38 |
| 32 | Outro | 769/989 | 77,76% | 319/539 | 59,18% | 6058 | 1324 |

### Decomposição por classe de erro da regra

| Método | Classe | Quebras/pág | Δ quebras [IC95 veículo] | p veículo | Sucessores certos/ouro | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|
| regra_colunas | Continuação na mesma coluna | 2,135 | 0,000 [0,000; 0,000] | 1,000000 | 6960/7145 | 0/0 |
| regra_colunas | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| regra_colunas | Entrada/saída de tabela ou imagem | 0,483 | 0,000 [0,000; 0,000] | 1,000000 | 84/126 | 0/0 |
| regra_colunas | Salto ou fronteira de elemento transversal | 0,742 | 0,000 [0,000; 0,000] | 1,000000 | 114/183 | 0/0 |
| regra_colunas | Cabeçalho/rodapé/marca marginal | 3,034 | 0,000 [0,000; 0,000] | 1,000000 | 127/307 | 0/0 |
| regra_colunas | Outro | 21,000 | 0,000 [0,000; 0,000] | 1,000000 | 5188/7054 | 0/0 |
| hibrido67 | Continuação na mesma coluna | 1,944 | -0,191 [-0,342; 0,000] | 0,165518 | 6977/7145 | 19/2 |
| hibrido67 | Fim de coluna → topo da próxima | 0,045 | -0,011 [-0,026; 0,000] | 0,317311 | 29/33 | 1/0 |
| hibrido67 | Entrada/saída de tabela ou imagem | 0,472 | -0,011 [-0,026; 0,000] | 0,317311 | 84/126 | 0/0 |
| hibrido67 | Salto ou fronteira de elemento transversal | 0,663 | -0,079 [-0,184; 0,000] | 0,317311 | 121/183 | 7/0 |
| hibrido67 | Cabeçalho/rodapé/marca marginal | 2,910 | -0,124 [-0,342; 0,079] | 0,592980 | 137/307 | 19/9 |
| hibrido67 | Outro | 20,393 | -0,607 [-1,184; 0,000] | 0,165518 | 5244/7054 | 56/0 |
| layoutreader_pronto | Continuação na mesma coluna | 9,910 | 7,775 [-1,105; 54,154] | 0,592980 | 6268/7145 | 147/839 |
| layoutreader_pronto | Fim de coluna → topo da próxima | 0,124 | 0,067 [0,000; 0,385] | 0,165518 | 22/33 | 2/8 |
| layoutreader_pronto | Entrada/saída de tabela ou imagem | 0,528 | 0,045 [-0,231; 0,211] | 0,592980 | 80/126 | 4/8 |
| layoutreader_pronto | Salto ou fronteira de elemento transversal | 0,371 | -0,371 [-2,154; -0,026] | 0,108809 | 148/183 | 38/4 |
| layoutreader_pronto | Cabeçalho/rodapé/marca marginal | 2,562 | -0,472 [-1,079; 0,079] | 0,285049 | 167/307 | 65/25 |
| layoutreader_pronto | Outro | 17,753 | -3,247 [-5,763; 2,385] | 0,285049 | 5477/7054 | 377/88 |
| regra_reordena | Continuação na mesma coluna | 1,798 | -0,337 [-0,846; -0,237] | 0,108809 | 6990/7145 | 36/6 |
| regra_reordena | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| regra_reordena | Entrada/saída de tabela ou imagem | 0,483 | 0,000 [0,000; 0,000] | 1,000000 | 84/126 | 0/0 |
| regra_reordena | Salto ou fronteira de elemento transversal | 0,730 | -0,011 [-0,026; 0,000] | 0,317311 | 115/183 | 1/0 |
| regra_reordena | Cabeçalho/rodapé/marca marginal | 3,034 | 0,000 [0,000; 0,000] | 1,000000 | 127/307 | 0/0 |
| regra_reordena | Outro | 20,348 | -0,652 [-1,105; -0,132] | 0,108809 | 5246/7054 | 95/37 |
| oraculo_decodificador_guloso_K12 | Continuação na mesma coluna | 0,169 | -1,966 [-5,538; -0,921] | 0,108809 | 7135/7145 | 175/0 |
| oraculo_decodificador_guloso_K12 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_guloso_K12 | Entrada/saída de tabela ou imagem | 0,404 | -0,079 [-0,538; 0,000] | 0,317311 | 91/126 | 7/0 |
| oraculo_decodificador_guloso_K12 | Salto ou fronteira de elemento transversal | 0,146 | -0,596 [-3,462; -0,026] | 0,108809 | 166/183 | 52/0 |
| oraculo_decodificador_guloso_K12 | Cabeçalho/rodapé/marca marginal | 1,921 | -1,112 [-2,154; 0,000] | 0,165518 | 218/307 | 91/0 |
| oraculo_decodificador_guloso_K12 | Outro | 18,022 | -2,978 [-4,000; -1,711] | 0,108809 | 5456/7054 | 268/0 |
| oraculo_decodificador_matching_K12 | Continuação na mesma coluna | 0,169 | -1,966 [-5,538; -0,921] | 0,108809 | 7135/7145 | 175/0 |
| oraculo_decodificador_matching_K12 | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| oraculo_decodificador_matching_K12 | Entrada/saída de tabela ou imagem | 0,404 | -0,079 [-0,538; 0,000] | 0,317311 | 91/126 | 7/0 |
| oraculo_decodificador_matching_K12 | Salto ou fronteira de elemento transversal | 0,157 | -0,584 [-3,385; -0,026] | 0,108809 | 165/183 | 51/0 |
| oraculo_decodificador_matching_K12 | Cabeçalho/rodapé/marca marginal | 1,742 | -1,292 [-2,308; -0,368] | 0,108809 | 220/307 | 93/0 |
| oraculo_decodificador_matching_K12 | Outro | 18,090 | -2,910 [-4,184; -1,368] | 0,108809 | 5464/7054 | 276/0 |
| oraculo_decodificador_maxregret_K12 | Continuação na mesma coluna | 0,169 | -1,966 [-5,538; -0,921] | 0,108809 | 7135/7145 | 175/0 |
| oraculo_decodificador_maxregret_K12 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_maxregret_K12 | Entrada/saída de tabela ou imagem | 0,404 | -0,079 [-0,538; 0,000] | 0,317311 | 91/126 | 7/0 |
| oraculo_decodificador_maxregret_K12 | Salto ou fronteira de elemento transversal | 0,146 | -0,596 [-3,462; -0,026] | 0,108809 | 166/183 | 52/0 |
| oraculo_decodificador_maxregret_K12 | Cabeçalho/rodapé/marca marginal | 1,921 | -1,112 [-2,154; 0,000] | 0,165518 | 218/307 | 91/0 |
| oraculo_decodificador_maxregret_K12 | Outro | 18,022 | -2,978 [-4,000; -1,711] | 0,108809 | 5456/7054 | 268/0 |
| oraculo_decodificador_guloso_K24 | Continuação na mesma coluna | 0,135 | -2,000 [-5,615; -0,947] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_guloso_K24 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_guloso_K24 | Entrada/saída de tabela ou imagem | 0,382 | -0,101 [-0,615; 0,000] | 0,165518 | 92/126 | 8/0 |
| oraculo_decodificador_guloso_K24 | Salto ou fronteira de elemento transversal | 0,124 | -0,618 [-3,615; -0,026] | 0,108809 | 170/183 | 56/0 |
| oraculo_decodificador_guloso_K24 | Cabeçalho/rodapé/marca marginal | 1,910 | -1,124 [-2,231; 0,000] | 0,165518 | 220/307 | 93/0 |
| oraculo_decodificador_guloso_K24 | Outro | 17,551 | -3,449 [-4,132; -2,605] | 0,108809 | 5497/7054 | 309/0 |
| oraculo_decodificador_matching_K24 | Continuação na mesma coluna | 0,124 | -2,011 [-5,615; -0,974] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_matching_K24 | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| oraculo_decodificador_matching_K24 | Entrada/saída de tabela ou imagem | 0,382 | -0,101 [-0,615; 0,000] | 0,165518 | 92/126 | 8/0 |
| oraculo_decodificador_matching_K24 | Salto ou fronteira de elemento transversal | 0,124 | -0,618 [-3,615; -0,026] | 0,108809 | 170/183 | 56/0 |
| oraculo_decodificador_matching_K24 | Cabeçalho/rodapé/marca marginal | 1,742 | -1,292 [-2,385; -0,342] | 0,108809 | 222/307 | 95/0 |
| oraculo_decodificador_matching_K24 | Outro | 17,697 | -3,303 [-4,132; -2,263] | 0,108809 | 5498/7054 | 310/0 |
| oraculo_decodificador_maxregret_K24 | Continuação na mesma coluna | 0,135 | -2,000 [-5,615; -0,947] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_maxregret_K24 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_maxregret_K24 | Entrada/saída de tabela ou imagem | 0,382 | -0,101 [-0,615; 0,000] | 0,165518 | 92/126 | 8/0 |
| oraculo_decodificador_maxregret_K24 | Salto ou fronteira de elemento transversal | 0,124 | -0,618 [-3,615; -0,026] | 0,108809 | 170/183 | 56/0 |
| oraculo_decodificador_maxregret_K24 | Cabeçalho/rodapé/marca marginal | 1,910 | -1,124 [-2,231; 0,000] | 0,165518 | 220/307 | 93/0 |
| oraculo_decodificador_maxregret_K24 | Outro | 17,551 | -3,449 [-4,132; -2,605] | 0,108809 | 5497/7054 | 309/0 |
| oraculo_decodificador_guloso_K32 | Continuação na mesma coluna | 0,135 | -2,000 [-5,615; -0,947] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_guloso_K32 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_guloso_K32 | Entrada/saída de tabela ou imagem | 0,382 | -0,101 [-0,615; 0,000] | 0,165518 | 92/126 | 8/0 |
| oraculo_decodificador_guloso_K32 | Salto ou fronteira de elemento transversal | 0,090 | -0,652 [-3,846; -0,026] | 0,108809 | 173/183 | 59/0 |
| oraculo_decodificador_guloso_K32 | Cabeçalho/rodapé/marca marginal | 1,876 | -1,157 [-2,308; 0,000] | 0,165518 | 223/307 | 96/0 |
| oraculo_decodificador_guloso_K32 | Outro | 17,236 | -3,764 [-4,289; -3,105] | 0,108809 | 5525/7054 | 337/0 |
| oraculo_decodificador_matching_K32 | Continuação na mesma coluna | 0,124 | -2,011 [-5,615; -0,974] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_matching_K32 | Fim de coluna → topo da próxima | 0,056 | 0,000 [0,000; 0,000] | 1,000000 | 28/33 | 0/0 |
| oraculo_decodificador_matching_K32 | Entrada/saída de tabela ou imagem | 0,393 | -0,090 [-0,615; 0,000] | 0,317311 | 92/126 | 8/0 |
| oraculo_decodificador_matching_K32 | Salto ou fronteira de elemento transversal | 0,101 | -0,640 [-3,769; -0,026] | 0,108809 | 172/183 | 58/0 |
| oraculo_decodificador_matching_K32 | Cabeçalho/rodapé/marca marginal | 1,730 | -1,303 [-2,462; -0,289] | 0,108809 | 225/307 | 98/0 |
| oraculo_decodificador_matching_K32 | Outro | 17,382 | -3,618 [-4,263; -2,789] | 0,108809 | 5523/7054 | 335/0 |
| oraculo_decodificador_maxregret_K32 | Continuação na mesma coluna | 0,135 | -2,000 [-5,615; -0,947] | 0,108809 | 7137/7145 | 177/0 |
| oraculo_decodificador_maxregret_K32 | Fim de coluna → topo da próxima | 0,056 | 0,000 [-0,026; 0,077] | 0,781511 | 28/33 | 1/1 |
| oraculo_decodificador_maxregret_K32 | Entrada/saída de tabela ou imagem | 0,382 | -0,101 [-0,615; 0,000] | 0,165518 | 92/126 | 8/0 |
| oraculo_decodificador_maxregret_K32 | Salto ou fronteira de elemento transversal | 0,090 | -0,652 [-3,846; -0,026] | 0,108809 | 173/183 | 59/0 |
| oraculo_decodificador_maxregret_K32 | Cabeçalho/rodapé/marca marginal | 1,876 | -1,157 [-2,308; 0,000] | 0,165518 | 223/307 | 96/0 |
| oraculo_decodificador_maxregret_K32 | Outro | 17,236 | -3,764 [-4,289; -3,105] | 0,108809 | 5525/7054 | 337/0 |
| oraculo_residual | Continuação na mesma coluna | 0,494 | -1,640 [-3,385; -0,868] | 0,108809 | 7107/7145 | 147/0 |
| oraculo_residual | Fim de coluna → topo da próxima | 0,045 | -0,011 [-0,026; 0,000] | 0,317311 | 29/33 | 1/0 |
| oraculo_residual | Entrada/saída de tabela ou imagem | 0,449 | -0,034 [-0,154; 0,000] | 0,165518 | 87/126 | 3/0 |
| oraculo_residual | Salto ou fronteira de elemento transversal | 0,326 | -0,416 [-2,308; 0,000] | 0,165518 | 152/183 | 38/0 |
| oraculo_residual | Cabeçalho/rodapé/marca marginal | 1,719 | -1,315 [-3,308; -0,026] | 0,108809 | 236/307 | 109/0 |
| oraculo_residual | Outro | 16,933 | -4,067 [-5,447; -2,868] | 0,108809 | 5547/7054 | 359/0 |
| oraculo_roteamento | Continuação na mesma coluna | 0,730 | -1,404 [-3,000; -0,632] | 0,108809 | 7086/7145 | 143/17 |
| oraculo_roteamento | Fim de coluna → topo da próxima | 0,034 | -0,022 [-0,077; 0,000] | 0,165518 | 30/33 | 2/0 |
| oraculo_roteamento | Entrada/saída de tabela ou imagem | 0,449 | -0,034 [-0,231; 0,000] | 0,317311 | 88/126 | 4/0 |
| oraculo_roteamento | Salto ou fronteira de elemento transversal | 0,416 | -0,326 [-1,615; -0,026] | 0,108809 | 143/183 | 29/0 |
| oraculo_roteamento | Cabeçalho/rodapé/marca marginal | 2,629 | -0,404 [-0,895; 0,000] | 0,165518 | 163/307 | 55/19 |
| oraculo_roteamento | Outro | 16,966 | -4,034 [-5,842; -2,077] | 0,108809 | 5545/7054 | 381/24 |

Operações residuais: 310; por tipo: {'bloco_coluna': 126, 'vizinhas': 136, 'reinsercao': 48}. Páginas com operações: 64. Sequência de cada operação salva no cache.

Roteamento — vitórias exclusivas: {'layoutreader_pronto': 23, 'regra_reordena': 6}; presença no mínimo (inclui empates): {'layoutreader_pronto': 67, 'hibrido67': 56, 'regra_colunas': 45, 'regra_reordena': 53}; escolhidos após desempate: {'layoutreader_pronto': 52, 'regra_colunas': 31, 'regra_reordena': 6}; páginas empatadas: 60.

### Sucessores-ouro fora dos candidatos

Lista integral, sem texto nem coordenadas humanas, identificada por página, linha, unidade e K:

K=12: 344 sucessores ausentes.
- `official_diary_ce/do20220512p03.pdf#p3`: `silver:l38` → `silver:l39`; `b72` → `b76`; Continuação na mesma coluna; erro da regra: False.
- `official_diary_ce/do20220530p02.pdf#p81`: `silver:l0` → `silver:l1`; `b27` → `b42`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l0` → `silver:l1`; `b47` → `b96`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l1` → `silver:l2`; `b96` → `b136`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l9` → `silver:l10`; `b164` → `b151`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l11` → `silver:l12`; `b68` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l12` → `silver:l13`; `b64` → `b18`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l19` → `silver:l20`; `b127` → `b102`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l20` → `silver:l21`; `b102` → `b50`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l26` → `silver:l27`; `b57` → `b39`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l27` → `silver:l28`; `b39` → `b158`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l28` → `silver:l29`; `b158` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l29` → `silver:l30`; `b60` → `b106`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l32` → `silver:l33`; `b46` → `b53`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l33` → `silver:l34`; `b53` → `b22`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l40` → `silver:l41`; `b80` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l41` → `silver:l42`; `b63` → `b37`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l48` → `silver:l49`; `b69` → `b41`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l49` → `silver:l50`; `b41` → `b71`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l55` → `silver:l56`; `b100` → `b118`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l57` → `silver:l58`; `b21` → `b121`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l58` → `silver:l59`; `b121` → `b19`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l63` → `silver:l64`; `b12` → `b24`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l64` → `silver:l65`; `b24` → `b78`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l65` → `silver:l66`; `b78` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l69` → `silver:l70`; `b145` → `b104`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l70` → `silver:l71`; `b104` → `b160`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l77` → `silver:l78`; `b108` → `b83`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l81` → `silver:l82`; `b166` → `b117`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l82` → `silver:l83`; `b117` → `b92`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l88` → `silver:l89`; `b99` → `b111`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l94` → `silver:l95`; `b120` → `b43`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l95` → `silver:l96`; `b43` → `b8`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l101` → `silver:l102`; `b148` → `b123`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l102` → `silver:l103`; `b123` → `b56`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l105` → `silver:l106`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l106` → `silver:l107`; `b55` → `b89`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l111` → `silver:l112`; `b129` → `b16`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l112` → `silver:l113`; `b16` → `b162`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l116` → `silver:l117`; `b88` → `b85`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l117` → `silver:l118`; `b85` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l120` → `silver:l121`; `b174` → `b48`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l121` → `silver:l122`; `b48` → `b87`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l127` → `silver:l128`; `b101` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l128` → `silver:l129`; `b124` → `b155`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l129` → `silver:l130`; `b155` → `b9`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l130` → `silver:l131`; `b9` → `b168`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l132` → `silver:l133`; `b133` → `b66`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l136` → `silver:l137`; `b171` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l140` → `silver:l141`; `b77` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l141` → `silver:l142`; `b93` → `b1`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l143` → `silver:l144`; `b7` → `b90`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l148` → `silver:l149`; `b35` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l150` → `silver:l151`; `b153` → `b126`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l151` → `silver:l152`; `b126` → `b135`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l157` → `silver:l158`; `b114` → `b157`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l163` → `silver:l164`; `b110` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l164` → `silver:l165`; `b31` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l170` → `silver:l171`; `b146` → `b62`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l0` → `silver:l1`; `b72` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l1` → `silver:l2`; `b150` → `b6`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l9` → `silver:l10`; `b123` → `b81`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l11` → `silver:l12`; `b43` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l12` → `silver:l13`; `b137` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l19` → `silver:l20`; `b100` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l23` → `silver:l24`; `b59` → `b110`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l24` → `silver:l25`; `b110` → `b4`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l30` → `silver:l31`; `b62` → `b47`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l32` → `silver:l33`; `b51` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l33` → `silver:l34`; `b31` → `b77`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l40` → `silver:l41`; `b160` → `b127`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l44` → `silver:l45`; `b111` → `b14`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l45` → `silver:l46`; `b14` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l52` → `silver:l53`; `b18` → `b105`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l58` → `silver:l59`; `b149` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l59` → `silver:l60`; `b64` → `b45`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l66` → `silver:l67`; `b108` → `b138`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l71` → `silver:l72`; `b161` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l77` → `silver:l78`; `b97` → `b80`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l78` → `silver:l79`; `b80` → `b91`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l84` → `silver:l85`; `b19` → `b95`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l86` → `silver:l87`; `b58` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l87` → `silver:l88`; `b67` → `b115`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l93` → `silver:l94`; `b89` → `b147`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l99` → `silver:l100`; `b56` → `b134`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l100` → `silver:l101`; `b134` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l106` → `silver:l107`; `b79` → `b140`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l112` → `silver:l113`; `b7` → `b3`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l113` → `silver:l114`; `b3` → `b128`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l120` → `silver:l121`; `b116` → `b125`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l122` → `silver:l123`; `b119` → `b73`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l123` → `silver:l124`; `b73` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l129` → `silver:l130`; `b83` → `b42`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l131` → `silver:l132`; `b33` → `b46`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l132` → `silver:l133`; `b46` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l139` → `silver:l140`; `b132` → `b36`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l141` → `silver:l142`; `b86` → `b70`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l142` → `silver:l143`; `b70` → `b156`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l148` → `silver:l149`; `b2` → `b75`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l150` → `silver:l151`; `b159` → `b120`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l151` → `silver:l152`; `b120` → `b99`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l157` → `silver:l158`; `b16` → `b109`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l74` → `silver:l75`; `b47` → `b3`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l75` → `silver:l76`; `b3` → `b86`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l76` → `silver:l77`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l79` → `silver:l80`; `b11` → `b26`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l17` → `silver:l18`; `b47` → `b39`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l27` → `silver:l28`; `b49` → `b44`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l96` → `silver:l97`; `b60` → `b66`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l152` → `silver:l153`; `b34` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20260113p03.pdf#p18`: `silver:l49` → `silver:l50`; `b2` → `b9`; Continuação na mesma coluna; erro da regra: False.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l6` → `silver:l7`; `b46` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l20` → `silver:l21`; `b111` → `b99`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l21` → `silver:l22`; `b99` → `b76`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l35` → `silver:l36`; `b114` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l36` → `silver:l37`; `b69` → `b75`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l50` → `silver:l51`; `b113` → `b54`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l51` → `silver:l52`; `b54` → `b36`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l52` → `silver:l53`; `b36` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l64` → `silver:l65`; `b13` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l65` → `silver:l66`; `b136` → `b130`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l79` → `silver:l80`; `b12` → `b42`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l80` → `silver:l81`; `b42` → `b85`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l99` → `silver:l100`; `b70` → `b15`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l100` → `silver:l101`; `b15` → `b135`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l114` → `silver:l115`; `b133` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l115` → `silver:l116`; `b18` → `b34`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l129` → `silver:l130`; `b106` → `b86`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l130` → `silver:l131`; `b86` → `b96`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-29.pdf#p56`: `silver:l17` → `silver:l18`; `b16` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-29.pdf#p90`: `silver:l93` → `silver:l94`; `b4` → `b110`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l6` → `silver:l7`; `b107` → `b102`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l7` → `silver:l8`; `b102` → `b36`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l49` → `silver:l50`; `b124` → `b23`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l52` → `silver:l53`; `b22` → `b90`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l56` → `silver:l57`; `b81` → `b32`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l59` → `silver:l60`; `b41` → `b82`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l68` → `silver:l69`; `b25` → `b80`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l102` → `silver:l103`; `b112` → `b114`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l119` → `silver:l120`; `b21` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l4` → `silver:l5`; `b42` → `b40`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l5` → `silver:l6`; `b40` → `b12`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l25` → `silver:l26`; `b9` → `b1`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l31` → `silver:l32`; `b37` → `b15`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l33` → `silver:l34`; `b32` → `b46`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l37` → `silver:l38`; `b14` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l45` → `silver:l46`; `b6` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l30` → `silver:l31`; `b65` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l55` → `silver:l56`; `b77` → `b2`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l56` → `silver:l57`; `b2` → `b72`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p34`: `silver:l19` → `silver:l20`; `b21` → `b6`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p59`: `silver:l29` → `silver:l30`; `b83` → `b23`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l39` → `silver:l40`; `b31` → `b91`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l40` → `silver:l41`; `b91` → `b97`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l48` → `silver:l49`; `b32` → `b38`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l53` → `silver:l54`; `b10` → `b19`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l58` → `silver:l59`; `b79` → `b42`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l160` → `silver:l161`; `b15` → `b84`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l163` → `silver:l164`; `b26` → `b99`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l166` → `silver:l167`; `b83` → `b33`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l169` → `silver:l170`; `b65` → `b51`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l172` → `silver:l173`; `b5` → `b63`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l177` → `silver:l178`; `b67` → `b0`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l181` → `silver:l182`; `b90` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l185` → `silver:l186`; `b60` → `b59`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l187` → `silver:l188`; `b23` → `b81`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l188` → `silver:l189`; `b81` → `b85`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l191` → `silver:l192`; `b103` → `b78`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l193` → `silver:l194`; `b57` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l196` → `silver:l197`; `b62` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l198` → `silver:l199`; `b6` → `b3`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l200` → `silver:l201`; `b16` → `b56`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l201` → `silver:l202`; `b56` → `b54`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2026-01-14.pdf#p46`: `silver:l1` → `silver:l2`; `b12` → `b36`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2026-01-14.pdf#p46`: `silver:l16` → `silver:l17`; `b30` → `b9`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2026-01-14.pdf#p46`: `silver:l58` → `silver:l59`; `b0` → `b27`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l1` → `silver:l2`; `b61` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l2` → `silver:l3`; `b94` → `b83`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l6` → `silver:l7`; `b4` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l7` → `silver:l8`; `b6` → `b59`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l8` → `silver:l9`; `b59` → `b29`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l9` → `silver:l10`; `b29` → `b137`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l10` → `silver:l11`; `b137` → `b77`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l11` → `silver:l12`; `b77` → `b63`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l12` → `silver:l13`; `b63` → `b28`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l13` → `silver:l14`; `b28` → `b153`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l15` → `silver:l16`; `b20` → `b35`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l16` → `silver:l17`; `b35` → `b46`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l18` → `silver:l19`; `b158` → `b139`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l19` → `silver:l20`; `b139` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l21` → `silver:l22`; `b88` → `b131`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l22` → `silver:l23`; `b131` → `b75`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l24` → `silver:l25`; `b91` → `b122`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l25` → `silver:l26`; `b122` → `b92`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l27` → `silver:l28`; `b19` → `b12`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l28` → `silver:l29`; `b12` → `b78`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l30` → `silver:l31`; `b23` → `b80`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l31` → `silver:l32`; `b80` → `b141`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l33` → `silver:l34`; `b125` → `b32`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l34` → `silver:l35`; `b32` → `b157`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l36` → `silver:l37`; `b2` → `b40`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l37` → `silver:l38`; `b40` → `b156`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l39` → `silver:l40`; `b36` → `b147`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l40` → `silver:l41`; `b147` → `b150`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l42` → `silver:l43`; `b0` → `b146`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l43` → `silver:l44`; `b146` → `b126`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l45` → `silver:l46`; `b134` → `b93`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l46` → `silver:l47`; `b93` → `b112`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l48` → `silver:l49`; `b119` → `b107`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l49` → `silver:l50`; `b107` → `b30`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l51` → `silver:l52`; `b114` → `b154`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l52` → `silver:l53`; `b154` → `b152`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l54` → `silver:l55`; `b85` → `b108`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l55` → `silver:l56`; `b108` → `b10`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l57` → `silver:l58`; `b86` → `b84`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l58` → `silver:l59`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l62` → `silver:l63`; `b14` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l63` → `silver:l64`; `b103` → `b90`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l64` → `silver:l65`; `b90` → `b52`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l65` → `silver:l66`; `b52` → `b37`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l66` → `silver:l67`; `b37` → `b140`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l67` → `silver:l68`; `b140` → `b41`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l68` → `silver:l69`; `b41` → `b159`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l69` → `silver:l70`; `b159` → `b53`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l71` → `silver:l72`; `b11` → `b58`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l72` → `silver:l73`; `b58` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l74` → `silver:l75`; `b104` → `b95`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l75` → `silver:l76`; `b95` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l77` → `silver:l78`; `b81` → `b87`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l78` → `silver:l79`; `b87` → `b65`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l80` → `silver:l81`; `b5` → `b67`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l81` → `silver:l82`; `b67` → `b142`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l83` → `silver:l84`; `b132` → `b66`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l84` → `silver:l85`; `b66` → `b3`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l86` → `silver:l87`; `b124` → `b33`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l87` → `silver:l88`; `b33` → `b151`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l89` → `silver:l90`; `b34` → `b121`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l90` → `silver:l91`; `b121` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l92` → `silver:l93`; `b42` → `b138`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l93` → `silver:l94`; `b138` → `b76`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l95` → `silver:l96`; `b7` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l96` → `silver:l97`; `b27` → `b26`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l98` → `silver:l99`; `b123` → `b64`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l99` → `silver:l100`; `b64` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l101` → `silver:l102`; `b45` → `b44`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l102` → `silver:l103`; `b44` → `b56`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l104` → `silver:l105`; `b82` → `b155`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l105` → `silver:l106`; `b155` → `b143`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l107` → `silver:l108`; `b25` → `b24`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l108` → `silver:l109`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l112` → `silver:l113`; `b47` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l113` → `silver:l114`; `b128` → `b43`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l114` → `silver:l115`; `b43` → `b100`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l115` → `silver:l116`; `b100` → `b68`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l116` → `silver:l117`; `b68` → `b127`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l117` → `silver:l118`; `b127` → `b149`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l118` → `silver:l119`; `b149` → `b16`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l119` → `silver:l120`; `b16` → `b129`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l121` → `silver:l122`; `b144` → `b39`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l122` → `silver:l123`; `b39` → `b73`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l124` → `silver:l125`; `b130` → `b97`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l125` → `silver:l126`; `b97` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l127` → `silver:l128`; `b116` → `b115`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l128` → `silver:l129`; `b115` → `b48`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l130` → `silver:l131`; `b113` → `b17`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l131` → `silver:l132`; `b17` → `b38`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l133` → `silver:l134`; `b55` → `b51`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l134` → `silver:l135`; `b51` → `b102`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l136` → `silver:l137`; `b8` → `b79`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l137` → `silver:l138`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l141` → `silver:l142`; `b148` → `b135`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l142` → `silver:l143`; `b135` → `b13`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l143` → `silver:l144`; `b13` → `b160`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l144` → `silver:l145`; `b160` → `b60`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l145` → `silver:l146`; `b60` → `b57`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l147` → `silver:l148`; `b110` → `b21`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l148` → `silver:l149`; `b21` → `b9`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l150` → `silver:l151`; `b105` → `b106`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l151` → `silver:l152`; `b106` → `b96`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l153` → `silver:l154`; `b1` → `b133`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l154` → `silver:l155`; `b133` → `b71`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l156` → `silver:l157`; `b120` → `b101`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l157` → `silver:l158`; `b101` → `b118`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l159` → `silver:l160`; `b117` → `b145`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l0` → `silver:l1`; `b314` → `b74`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l1` → `silver:l2`; `b74` → `b178`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l9` → `silver:l10`; `b59` → `b221`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l56` → `silver:l57`; `b225` → `b146`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l94` → `silver:l95`; `b114` → `b158`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l236` → `silver:l237`; `b308` → `b131`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l0` → `silver:l1`; `b83` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l1` → `silver:l2`; `b115` → `b144`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l3` → `silver:l4`; `b8` → `b121`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l28` → `silver:l29`; `b63` → `b98`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l32` → `silver:l33`; `b128` → `b101`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l44` → `silver:l45`; `b59` → `b1`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l47` → `silver:l48`; `b112` → `b35`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l48` → `silver:l49`; `b35` → `b108`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l67` → `silver:l68`; `b5` → `b43`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l84` → `silver:l85`; `b124` → `b22`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l93` → `silver:l94`; `b48` → `b118`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l110` → `silver:l111`; `b61` → `b21`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l119` → `silver:l120`; `b52` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l120` → `silver:l121`; `b20` → `b93`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l129` → `silver:l130`; `b119` → `b41`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l140` → `silver:l141`; `b30` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l744` → `silver:l745`; `b123` → `b37`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l759` → `silver:l760`; `b51` → `b82`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l0` → `silver:l1`; `b94` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l1` → `silver:l2`; `b289` → `b116`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l133` → `silver:l134`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l270` → `silver:l271`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l0` → `silver:l1`; `b133` → `b287`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l1` → `silver:l2`; `b287` → `b21`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l0` → `silver:l1`; `b167` → `b50`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l1` → `silver:l2`; `b50` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p21`: `silver:l1` → `silver:l2`; `b313` → `b173`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p21`: `silver:l3` → `silver:l4`; `b229` → `b47`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l3` → `silver:l4`; `b167` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l5` → `silver:l6`; `b223` → `b136`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l13` → `silver:l14`; `b109` → `b112`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l19` → `silver:l20`; `b322` → `b117`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l27` → `silver:l28`; `b110` → `b321`; Outro; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l28` → `silver:l29`; `b321` → `b242`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l33` → `silver:l34`; `b96` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l48` → `silver:l49`; `b75` → `b272`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p2`: `silver:l2` → `silver:l3`; `b165` → `b191`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l3` → `silver:l4`; `b30` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l28` → `silver:l29`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l98` → `silver:l99`; `b78` → `b89`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l106` → `silver:l107`; `b22` → `b77`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l4` → `silver:l5`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l6` → `silver:l7`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l67` → `silver:l68`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l99` → `silver:l100`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l128` → `silver:l129`; `b84` → `b116`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l139` → `silver:l140`; `b31` → `b160`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l167` → `silver:l168`; `b150` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l191` → `silver:l192`; `b46` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l4` → `silver:l5`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l6` → `silver:l7`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l67` → `silver:l68`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l99` → `silver:l100`; `b80` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l159` → `silver:l160`; `b121` → `b92`; Entrada/saída de tabela ou imagem; erro da regra: True.

K=24: 290 sucessores ausentes.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l0` → `silver:l1`; `b47` → `b96`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l1` → `silver:l2`; `b96` → `b136`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l9` → `silver:l10`; `b164` → `b151`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l11` → `silver:l12`; `b68` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l12` → `silver:l13`; `b64` → `b18`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l19` → `silver:l20`; `b127` → `b102`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l20` → `silver:l21`; `b102` → `b50`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l26` → `silver:l27`; `b57` → `b39`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l27` → `silver:l28`; `b39` → `b158`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l28` → `silver:l29`; `b158` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l29` → `silver:l30`; `b60` → `b106`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l32` → `silver:l33`; `b46` → `b53`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l33` → `silver:l34`; `b53` → `b22`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l40` → `silver:l41`; `b80` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l41` → `silver:l42`; `b63` → `b37`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l48` → `silver:l49`; `b69` → `b41`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l49` → `silver:l50`; `b41` → `b71`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l55` → `silver:l56`; `b100` → `b118`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l57` → `silver:l58`; `b21` → `b121`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l58` → `silver:l59`; `b121` → `b19`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l63` → `silver:l64`; `b12` → `b24`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l64` → `silver:l65`; `b24` → `b78`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l65` → `silver:l66`; `b78` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l69` → `silver:l70`; `b145` → `b104`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l70` → `silver:l71`; `b104` → `b160`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l77` → `silver:l78`; `b108` → `b83`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l81` → `silver:l82`; `b166` → `b117`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l82` → `silver:l83`; `b117` → `b92`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l88` → `silver:l89`; `b99` → `b111`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l94` → `silver:l95`; `b120` → `b43`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l95` → `silver:l96`; `b43` → `b8`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l101` → `silver:l102`; `b148` → `b123`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l102` → `silver:l103`; `b123` → `b56`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l105` → `silver:l106`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l106` → `silver:l107`; `b55` → `b89`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l112` → `silver:l113`; `b16` → `b162`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l116` → `silver:l117`; `b88` → `b85`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l117` → `silver:l118`; `b85` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l120` → `silver:l121`; `b174` → `b48`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l121` → `silver:l122`; `b48` → `b87`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l127` → `silver:l128`; `b101` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l129` → `silver:l130`; `b155` → `b9`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l130` → `silver:l131`; `b9` → `b168`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l136` → `silver:l137`; `b171` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l140` → `silver:l141`; `b77` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l141` → `silver:l142`; `b93` → `b1`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l148` → `silver:l149`; `b35` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l150` → `silver:l151`; `b153` → `b126`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l151` → `silver:l152`; `b126` → `b135`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l157` → `silver:l158`; `b114` → `b157`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l163` → `silver:l164`; `b110` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l164` → `silver:l165`; `b31` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l170` → `silver:l171`; `b146` → `b62`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l0` → `silver:l1`; `b72` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l1` → `silver:l2`; `b150` → `b6`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l9` → `silver:l10`; `b123` → `b81`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l11` → `silver:l12`; `b43` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l12` → `silver:l13`; `b137` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l19` → `silver:l20`; `b100` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l23` → `silver:l24`; `b59` → `b110`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l24` → `silver:l25`; `b110` → `b4`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l30` → `silver:l31`; `b62` → `b47`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l32` → `silver:l33`; `b51` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l33` → `silver:l34`; `b31` → `b77`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l40` → `silver:l41`; `b160` → `b127`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l44` → `silver:l45`; `b111` → `b14`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l45` → `silver:l46`; `b14` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l52` → `silver:l53`; `b18` → `b105`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l58` → `silver:l59`; `b149` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l59` → `silver:l60`; `b64` → `b45`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l66` → `silver:l67`; `b108` → `b138`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l71` → `silver:l72`; `b161` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l77` → `silver:l78`; `b97` → `b80`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l78` → `silver:l79`; `b80` → `b91`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l84` → `silver:l85`; `b19` → `b95`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l86` → `silver:l87`; `b58` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l87` → `silver:l88`; `b67` → `b115`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l93` → `silver:l94`; `b89` → `b147`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l99` → `silver:l100`; `b56` → `b134`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l100` → `silver:l101`; `b134` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l106` → `silver:l107`; `b79` → `b140`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l112` → `silver:l113`; `b7` → `b3`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l113` → `silver:l114`; `b3` → `b128`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l120` → `silver:l121`; `b116` → `b125`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l122` → `silver:l123`; `b119` → `b73`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l123` → `silver:l124`; `b73` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l129` → `silver:l130`; `b83` → `b42`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l131` → `silver:l132`; `b33` → `b46`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l132` → `silver:l133`; `b46` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l139` → `silver:l140`; `b132` → `b36`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l141` → `silver:l142`; `b86` → `b70`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l142` → `silver:l143`; `b70` → `b156`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l148` → `silver:l149`; `b2` → `b75`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l150` → `silver:l151`; `b159` → `b120`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l151` → `silver:l152`; `b120` → `b99`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l157` → `silver:l158`; `b16` → `b109`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l76` → `silver:l77`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l79` → `silver:l80`; `b11` → `b26`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l17` → `silver:l18`; `b47` → `b39`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l27` → `silver:l28`; `b49` → `b44`; Outro; erro da regra: True.
- `official_diary_ce/do20240429p01.pdf#p51`: `silver:l96` → `silver:l97`; `b60` → `b66`; Outro; erro da regra: True.
- `official_diary_ce/do20260113p03.pdf#p18`: `silver:l49` → `silver:l50`; `b2` → `b9`; Continuação na mesma coluna; erro da regra: False.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l20` → `silver:l21`; `b111` → `b99`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l21` → `silver:l22`; `b99` → `b76`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l35` → `silver:l36`; `b114` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l50` → `silver:l51`; `b113` → `b54`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l52` → `silver:l53`; `b36` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l64` → `silver:l65`; `b13` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l65` → `silver:l66`; `b136` → `b130`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l79` → `silver:l80`; `b12` → `b42`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l99` → `silver:l100`; `b70` → `b15`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l100` → `silver:l101`; `b15` → `b135`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l114` → `silver:l115`; `b133` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l115` → `silver:l116`; `b18` → `b34`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l129` → `silver:l130`; `b106` → `b86`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-29.pdf#p56`: `silver:l17` → `silver:l18`; `b16` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l68` → `silver:l69`; `b25` → `b80`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l119` → `silver:l120`; `b21` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l4` → `silver:l5`; `b42` → `b40`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l5` → `silver:l6`; `b40` → `b12`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l25` → `silver:l26`; `b9` → `b1`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l33` → `silver:l34`; `b32` → `b46`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l37` → `silver:l38`; `b14` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l45` → `silver:l46`; `b6` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l30` → `silver:l31`; `b65` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l55` → `silver:l56`; `b77` → `b2`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l56` → `silver:l57`; `b2` → `b72`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p34`: `silver:l19` → `silver:l20`; `b21` → `b6`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l48` → `silver:l49`; `b32` → `b38`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l58` → `silver:l59`; `b79` → `b42`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l169` → `silver:l170`; `b65` → `b51`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l172` → `silver:l173`; `b5` → `b63`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l177` → `silver:l178`; `b67` → `b0`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l181` → `silver:l182`; `b90` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l185` → `silver:l186`; `b60` → `b59`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l188` → `silver:l189`; `b81` → `b85`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l193` → `silver:l194`; `b57` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l198` → `silver:l199`; `b6` → `b3`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l1` → `silver:l2`; `b61` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l2` → `silver:l3`; `b94` → `b83`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l6` → `silver:l7`; `b4` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l7` → `silver:l8`; `b6` → `b59`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l9` → `silver:l10`; `b29` → `b137`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l10` → `silver:l11`; `b137` → `b77`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l12` → `silver:l13`; `b63` → `b28`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l13` → `silver:l14`; `b28` → `b153`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l15` → `silver:l16`; `b20` → `b35`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l16` → `silver:l17`; `b35` → `b46`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l18` → `silver:l19`; `b158` → `b139`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l19` → `silver:l20`; `b139` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l21` → `silver:l22`; `b88` → `b131`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l22` → `silver:l23`; `b131` → `b75`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l24` → `silver:l25`; `b91` → `b122`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l25` → `silver:l26`; `b122` → `b92`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l27` → `silver:l28`; `b19` → `b12`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l28` → `silver:l29`; `b12` → `b78`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l30` → `silver:l31`; `b23` → `b80`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l31` → `silver:l32`; `b80` → `b141`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l33` → `silver:l34`; `b125` → `b32`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l34` → `silver:l35`; `b32` → `b157`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l36` → `silver:l37`; `b2` → `b40`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l37` → `silver:l38`; `b40` → `b156`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l39` → `silver:l40`; `b36` → `b147`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l40` → `silver:l41`; `b147` → `b150`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l42` → `silver:l43`; `b0` → `b146`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l43` → `silver:l44`; `b146` → `b126`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l45` → `silver:l46`; `b134` → `b93`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l46` → `silver:l47`; `b93` → `b112`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l48` → `silver:l49`; `b119` → `b107`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l49` → `silver:l50`; `b107` → `b30`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l51` → `silver:l52`; `b114` → `b154`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l52` → `silver:l53`; `b154` → `b152`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l54` → `silver:l55`; `b85` → `b108`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l55` → `silver:l56`; `b108` → `b10`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l57` → `silver:l58`; `b86` → `b84`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l58` → `silver:l59`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l62` → `silver:l63`; `b14` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l63` → `silver:l64`; `b103` → `b90`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l65` → `silver:l66`; `b52` → `b37`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l66` → `silver:l67`; `b37` → `b140`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l68` → `silver:l69`; `b41` → `b159`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l69` → `silver:l70`; `b159` → `b53`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l71` → `silver:l72`; `b11` → `b58`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l72` → `silver:l73`; `b58` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l74` → `silver:l75`; `b104` → `b95`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l75` → `silver:l76`; `b95` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l77` → `silver:l78`; `b81` → `b87`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l78` → `silver:l79`; `b87` → `b65`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l80` → `silver:l81`; `b5` → `b67`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l81` → `silver:l82`; `b67` → `b142`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l83` → `silver:l84`; `b132` → `b66`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l84` → `silver:l85`; `b66` → `b3`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l86` → `silver:l87`; `b124` → `b33`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l87` → `silver:l88`; `b33` → `b151`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l89` → `silver:l90`; `b34` → `b121`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l90` → `silver:l91`; `b121` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l92` → `silver:l93`; `b42` → `b138`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l93` → `silver:l94`; `b138` → `b76`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l95` → `silver:l96`; `b7` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l96` → `silver:l97`; `b27` → `b26`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l98` → `silver:l99`; `b123` → `b64`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l99` → `silver:l100`; `b64` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l101` → `silver:l102`; `b45` → `b44`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l102` → `silver:l103`; `b44` → `b56`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l104` → `silver:l105`; `b82` → `b155`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l105` → `silver:l106`; `b155` → `b143`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l107` → `silver:l108`; `b25` → `b24`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l108` → `silver:l109`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l112` → `silver:l113`; `b47` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l113` → `silver:l114`; `b128` → `b43`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l115` → `silver:l116`; `b100` → `b68`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l116` → `silver:l117`; `b68` → `b127`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l118` → `silver:l119`; `b149` → `b16`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l119` → `silver:l120`; `b16` → `b129`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l121` → `silver:l122`; `b144` → `b39`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l122` → `silver:l123`; `b39` → `b73`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l124` → `silver:l125`; `b130` → `b97`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l125` → `silver:l126`; `b97` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l127` → `silver:l128`; `b116` → `b115`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l128` → `silver:l129`; `b115` → `b48`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l130` → `silver:l131`; `b113` → `b17`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l131` → `silver:l132`; `b17` → `b38`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l133` → `silver:l134`; `b55` → `b51`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l134` → `silver:l135`; `b51` → `b102`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l136` → `silver:l137`; `b8` → `b79`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l137` → `silver:l138`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l141` → `silver:l142`; `b148` → `b135`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l142` → `silver:l143`; `b135` → `b13`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l144` → `silver:l145`; `b160` → `b60`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l145` → `silver:l146`; `b60` → `b57`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l147` → `silver:l148`; `b110` → `b21`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l148` → `silver:l149`; `b21` → `b9`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l150` → `silver:l151`; `b105` → `b106`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l151` → `silver:l152`; `b106` → `b96`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l153` → `silver:l154`; `b1` → `b133`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l154` → `silver:l155`; `b133` → `b71`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l156` → `silver:l157`; `b120` → `b101`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l157` → `silver:l158`; `b101` → `b118`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l159` → `silver:l160`; `b117` → `b145`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l0` → `silver:l1`; `b314` → `b74`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l1` → `silver:l2`; `b74` → `b178`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l9` → `silver:l10`; `b59` → `b221`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l56` → `silver:l57`; `b225` → `b146`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l94` → `silver:l95`; `b114` → `b158`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l236` → `silver:l237`; `b308` → `b131`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l0` → `silver:l1`; `b83` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l3` → `silver:l4`; `b8` → `b121`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l28` → `silver:l29`; `b63` → `b98`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l47` → `silver:l48`; `b112` → `b35`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l48` → `silver:l49`; `b35` → `b108`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l67` → `silver:l68`; `b5` → `b43`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l93` → `silver:l94`; `b48` → `b118`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l110` → `silver:l111`; `b61` → `b21`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l119` → `silver:l120`; `b52` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l129` → `silver:l130`; `b119` → `b41`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l140` → `silver:l141`; `b30` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l744` → `silver:l745`; `b123` → `b37`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l759` → `silver:l760`; `b51` → `b82`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l0` → `silver:l1`; `b94` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l1` → `silver:l2`; `b289` → `b116`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l133` → `silver:l134`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l270` → `silver:l271`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l0` → `silver:l1`; `b133` → `b287`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l1` → `silver:l2`; `b287` → `b21`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l0` → `silver:l1`; `b167` → `b50`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l1` → `silver:l2`; `b50` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p21`: `silver:l1` → `silver:l2`; `b313` → `b173`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p21`: `silver:l3` → `silver:l4`; `b229` → `b47`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l3` → `silver:l4`; `b167` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l5` → `silver:l6`; `b223` → `b136`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l19` → `silver:l20`; `b322` → `b117`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l33` → `silver:l34`; `b96` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l48` → `silver:l49`; `b75` → `b272`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p2`: `silver:l2` → `silver:l3`; `b165` → `b191`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l3` → `silver:l4`; `b30` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l28` → `silver:l29`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l98` → `silver:l99`; `b78` → `b89`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l4` → `silver:l5`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l6` → `silver:l7`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l67` → `silver:l68`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l99` → `silver:l100`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l128` → `silver:l129`; `b84` → `b116`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l139` → `silver:l140`; `b31` → `b160`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l167` → `silver:l168`; `b150` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l191` → `silver:l192`; `b46` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l4` → `silver:l5`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l6` → `silver:l7`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l67` → `silver:l68`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l99` → `silver:l100`; `b80` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l159` → `silver:l160`; `b121` → `b92`; Entrada/saída de tabela ou imagem; erro da regra: True.

K=32: 263 sucessores ausentes.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l1` → `silver:l2`; `b96` → `b136`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l9` → `silver:l10`; `b164` → `b151`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l11` → `silver:l12`; `b68` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l12` → `silver:l13`; `b64` → `b18`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l19` → `silver:l20`; `b127` → `b102`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l20` → `silver:l21`; `b102` → `b50`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l26` → `silver:l27`; `b57` → `b39`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l27` → `silver:l28`; `b39` → `b158`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l28` → `silver:l29`; `b158` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l29` → `silver:l30`; `b60` → `b106`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l32` → `silver:l33`; `b46` → `b53`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l33` → `silver:l34`; `b53` → `b22`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l40` → `silver:l41`; `b80` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l41` → `silver:l42`; `b63` → `b37`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l48` → `silver:l49`; `b69` → `b41`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l49` → `silver:l50`; `b41` → `b71`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l55` → `silver:l56`; `b100` → `b118`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l57` → `silver:l58`; `b21` → `b121`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l58` → `silver:l59`; `b121` → `b19`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l63` → `silver:l64`; `b12` → `b24`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l64` → `silver:l65`; `b24` → `b78`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l65` → `silver:l66`; `b78` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l69` → `silver:l70`; `b145` → `b104`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l70` → `silver:l71`; `b104` → `b160`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l77` → `silver:l78`; `b108` → `b83`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l81` → `silver:l82`; `b166` → `b117`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l82` → `silver:l83`; `b117` → `b92`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l88` → `silver:l89`; `b99` → `b111`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l94` → `silver:l95`; `b120` → `b43`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l95` → `silver:l96`; `b43` → `b8`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l101` → `silver:l102`; `b148` → `b123`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l102` → `silver:l103`; `b123` → `b56`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l105` → `silver:l106`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l106` → `silver:l107`; `b55` → `b89`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l112` → `silver:l113`; `b16` → `b162`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l116` → `silver:l117`; `b88` → `b85`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l117` → `silver:l118`; `b85` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l120` → `silver:l121`; `b174` → `b48`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l121` → `silver:l122`; `b48` → `b87`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l127` → `silver:l128`; `b101` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l129` → `silver:l130`; `b155` → `b9`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l130` → `silver:l131`; `b9` → `b168`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l136` → `silver:l137`; `b171` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l140` → `silver:l141`; `b77` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l141` → `silver:l142`; `b93` → `b1`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l148` → `silver:l149`; `b35` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l150` → `silver:l151`; `b153` → `b126`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l151` → `silver:l152`; `b126` → `b135`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l157` → `silver:l158`; `b114` → `b157`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l163` → `silver:l164`; `b110` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l164` → `silver:l165`; `b31` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p3`: `silver:l170` → `silver:l171`; `b146` → `b62`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l0` → `silver:l1`; `b72` → `b150`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l9` → `silver:l10`; `b123` → `b81`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l11` → `silver:l12`; `b43` → `b137`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l12` → `silver:l13`; `b137` → `b103`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l19` → `silver:l20`; `b100` → `b63`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l23` → `silver:l24`; `b59` → `b110`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l24` → `silver:l25`; `b110` → `b4`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l30` → `silver:l31`; `b62` → `b47`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l32` → `silver:l33`; `b51` → `b31`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l33` → `silver:l34`; `b31` → `b77`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l40` → `silver:l41`; `b160` → `b127`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l44` → `silver:l45`; `b111` → `b14`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l45` → `silver:l46`; `b14` → `b93`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l52` → `silver:l53`; `b18` → `b105`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l58` → `silver:l59`; `b149` → `b64`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l59` → `silver:l60`; `b64` → `b45`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l66` → `silver:l67`; `b108` → `b138`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l71` → `silver:l72`; `b161` → `b124`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l77` → `silver:l78`; `b97` → `b80`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l78` → `silver:l79`; `b80` → `b91`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l84` → `silver:l85`; `b19` → `b95`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l86` → `silver:l87`; `b58` → `b67`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l87` → `silver:l88`; `b67` → `b115`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l93` → `silver:l94`; `b89` → `b147`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l99` → `silver:l100`; `b56` → `b134`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l100` → `silver:l101`; `b134` → `b141`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l106` → `silver:l107`; `b79` → `b140`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l112` → `silver:l113`; `b7` → `b3`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l113` → `silver:l114`; `b3` → `b128`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l120` → `silver:l121`; `b116` → `b125`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l122` → `silver:l123`; `b119` → `b73`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l123` → `silver:l124`; `b73` → `b60`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l129` → `silver:l130`; `b83` → `b42`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l131` → `silver:l132`; `b33` → `b46`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l132` → `silver:l133`; `b46` → `b40`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l139` → `silver:l140`; `b132` → `b36`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l141` → `silver:l142`; `b86` → `b70`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l142` → `silver:l143`; `b70` → `b156`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l148` → `silver:l149`; `b2` → `b75`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l150` → `silver:l151`; `b159` → `b120`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p4`: `silver:l151` → `silver:l152`; `b120` → `b99`; Outro; erro da regra: True.
- `official_diary_ce/do20220908p01.pdf#p46`: `silver:l76` → `silver:l77`; `b86` → `b55`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l20` → `silver:l21`; `b111` → `b99`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l35` → `silver:l36`; `b114` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l50` → `silver:l51`; `b113` → `b54`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l52` → `silver:l53`; `b36` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l64` → `silver:l65`; `b13` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l79` → `silver:l80`; `b12` → `b42`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l99` → `silver:l100`; `b70` → `b15`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l114` → `silver:l115`; `b133` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-20.pdf#p5`: `silver:l129` → `silver:l130`; `b106` → `b86`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-09-29.pdf#p56`: `silver:l17` → `silver:l18`; `b16` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l68` → `silver:l69`; `b25` → `b80`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-12.pdf#p38`: `silver:l119` → `silver:l120`; `b21` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l4` → `silver:l5`; `b42` → `b40`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l25` → `silver:l26`; `b9` → `b1`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l37` → `silver:l38`; `b14` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55`: `silver:l45` → `silver:l46`; `b6` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l30` → `silver:l31`; `b65` → `b16`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l55` → `silver:l56`; `b77` → `b2`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2021-12-20.pdf#p1`: `silver:l56` → `silver:l57`; `b2` → `b72`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-03-06.pdf#p34`: `silver:l19` → `silver:l20`; `b21` → `b6`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l58` → `silver:l59`; `b79` → `b42`; Entrada/saída de tabela ou imagem; erro da regra: True.
- `official_diary_ma/executive_official_diary_2023-08-02_59_64.pdf#p0`: `silver:l181` → `silver:l182`; `b90` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l1` → `silver:l2`; `b61` → `b94`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l2` → `silver:l3`; `b94` → `b83`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l6` → `silver:l7`; `b4` → `b6`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l7` → `silver:l8`; `b6` → `b59`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l9` → `silver:l10`; `b29` → `b137`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l10` → `silver:l11`; `b137` → `b77`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l12` → `silver:l13`; `b63` → `b28`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l13` → `silver:l14`; `b28` → `b153`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l15` → `silver:l16`; `b20` → `b35`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l16` → `silver:l17`; `b35` → `b46`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l18` → `silver:l19`; `b158` → `b139`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l19` → `silver:l20`; `b139` → `b69`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l21` → `silver:l22`; `b88` → `b131`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l22` → `silver:l23`; `b131` → `b75`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l24` → `silver:l25`; `b91` → `b122`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l25` → `silver:l26`; `b122` → `b92`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l27` → `silver:l28`; `b19` → `b12`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l28` → `silver:l29`; `b12` → `b78`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l30` → `silver:l31`; `b23` → `b80`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l31` → `silver:l32`; `b80` → `b141`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l33` → `silver:l34`; `b125` → `b32`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l34` → `silver:l35`; `b32` → `b157`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l36` → `silver:l37`; `b2` → `b40`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l37` → `silver:l38`; `b40` → `b156`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l39` → `silver:l40`; `b36` → `b147`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l40` → `silver:l41`; `b147` → `b150`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l42` → `silver:l43`; `b0` → `b146`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l43` → `silver:l44`; `b146` → `b126`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l45` → `silver:l46`; `b134` → `b93`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l46` → `silver:l47`; `b93` → `b112`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l48` → `silver:l49`; `b119` → `b107`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l49` → `silver:l50`; `b107` → `b30`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l51` → `silver:l52`; `b114` → `b154`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l52` → `silver:l53`; `b154` → `b152`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l54` → `silver:l55`; `b85` → `b108`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l55` → `silver:l56`; `b108` → `b10`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l57` → `silver:l58`; `b86` → `b84`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l58` → `silver:l59`; `b84` → `b70`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l62` → `silver:l63`; `b14` → `b103`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l63` → `silver:l64`; `b103` → `b90`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l65` → `silver:l66`; `b52` → `b37`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l66` → `silver:l67`; `b37` → `b140`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l68` → `silver:l69`; `b41` → `b159`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l69` → `silver:l70`; `b159` → `b53`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l71` → `silver:l72`; `b11` → `b58`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l72` → `silver:l73`; `b58` → `b18`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l74` → `silver:l75`; `b104` → `b95`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l75` → `silver:l76`; `b95` → `b74`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l77` → `silver:l78`; `b81` → `b87`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l78` → `silver:l79`; `b87` → `b65`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l80` → `silver:l81`; `b5` → `b67`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l81` → `silver:l82`; `b67` → `b142`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l83` → `silver:l84`; `b132` → `b66`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l84` → `silver:l85`; `b66` → `b3`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l86` → `silver:l87`; `b124` → `b33`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l87` → `silver:l88`; `b33` → `b151`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l89` → `silver:l90`; `b34` → `b121`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l90` → `silver:l91`; `b121` → `b22`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l92` → `silver:l93`; `b42` → `b138`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l93` → `silver:l94`; `b138` → `b76`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l95` → `silver:l96`; `b7` → `b27`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l96` → `silver:l97`; `b27` → `b26`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l98` → `silver:l99`; `b123` → `b64`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l99` → `silver:l100`; `b64` → `b136`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l101` → `silver:l102`; `b45` → `b44`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l102` → `silver:l103`; `b44` → `b56`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l104` → `silver:l105`; `b82` → `b155`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l105` → `silver:l106`; `b155` → `b143`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l107` → `silver:l108`; `b25` → `b24`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l108` → `silver:l109`; `b24` → `b31`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l112` → `silver:l113`; `b47` → `b128`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l113` → `silver:l114`; `b128` → `b43`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l115` → `silver:l116`; `b100` → `b68`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l116` → `silver:l117`; `b68` → `b127`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l118` → `silver:l119`; `b149` → `b16`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l119` → `silver:l120`; `b16` → `b129`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l121` → `silver:l122`; `b144` → `b39`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l122` → `silver:l123`; `b39` → `b73`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l124` → `silver:l125`; `b130` → `b97`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l125` → `silver:l126`; `b97` → `b49`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l127` → `silver:l128`; `b116` → `b115`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l128` → `silver:l129`; `b115` → `b48`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l130` → `silver:l131`; `b113` → `b17`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l131` → `silver:l132`; `b17` → `b38`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l133` → `silver:l134`; `b55` → `b51`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l134` → `silver:l135`; `b51` → `b102`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l136` → `silver:l137`; `b8` → `b79`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l137` → `silver:l138`; `b79` → `b111`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l141` → `silver:l142`; `b148` → `b135`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l142` → `silver:l143`; `b135` → `b13`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l144` → `silver:l145`; `b160` → `b60`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l145` → `silver:l146`; `b60` → `b57`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l147` → `silver:l148`; `b110` → `b21`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l148` → `silver:l149`; `b21` → `b9`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l150` → `silver:l151`; `b105` → `b106`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l151` → `silver:l152`; `b106` → `b96`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l153` → `silver:l154`; `b1` → `b133`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l154` → `silver:l155`; `b133` → `b71`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l156` → `silver:l157`; `b120` → `b101`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l157` → `silver:l158`; `b101` → `b118`; Outro; erro da regra: True.
- `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`: `silver:l159` → `silver:l160`; `b117` → `b145`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l0` → `silver:l1`; `b314` → `b74`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l1` → `silver:l2`; `b74` → `b178`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l9` → `silver:l10`; `b59` → `b221`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l56` → `silver:l57`; `b225` → `b146`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l94` → `silver:l95`; `b114` → `b158`; Continuação na mesma coluna; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: `silver:l236` → `silver:l237`; `b308` → `b131`; Fim de coluna → topo da próxima; erro da regra: False.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l0` → `silver:l1`; `b83` → `b115`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l3` → `silver:l4`; `b8` → `b121`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l28` → `silver:l29`; `b63` → `b98`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l48` → `silver:l49`; `b35` → `b108`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l67` → `silver:l68`; `b5` → `b43`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l93` → `silver:l94`; `b48` → `b118`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l110` → `silver:l111`; `b61` → `b21`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l119` → `silver:l120`; `b52` → `b20`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l140` → `silver:l141`; `b30` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p15`: `silver:l759` → `silver:l760`; `b51` → `b82`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l0` → `silver:l1`; `b94` → `b289`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l1` → `silver:l2`; `b289` → `b116`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l133` → `silver:l134`; `b312` → `b98`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: `silver:l270` → `silver:l271`; `b261` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l0` → `silver:l1`; `b133` → `b287`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p4`: `silver:l1` → `silver:l2`; `b287` → `b21`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l0` → `silver:l1`; `b167` → `b50`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p16`: `silver:l1` → `silver:l2`; `b50` → `b215`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte I (Poder Executivo)_2026-01-14.pdf#p21`: `silver:l3` → `silver:l4`; `b229` → `b47`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l3` → `silver:l4`; `b167` → `b308`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l5` → `silver:l6`; `b223` → `b136`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l19` → `silver:l20`; `b322` → `b117`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l33` → `silver:l34`; `b96` → `b123`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: `silver:l48` → `silver:l49`; `b75` → `b272`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p2`: `silver:l2` → `silver:l3`; `b165` → `b191`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l3` → `silver:l4`; `b30` → `b100`; Cabeçalho/rodapé/marca marginal; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l28` → `silver:l29`; `b104` → `b92`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: `silver:l98` → `silver:l99`; `b78` → `b89`; Salto ou fronteira de elemento transversal; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l4` → `silver:l5`; `b146` → `b185`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l6` → `silver:l7`; `b79` → `b125`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l67` → `silver:l68`; `b112` → `b189`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l99` → `silver:l100`; `b9` → `b163`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l139` → `silver:l140`; `b31` → `b160`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l167` → `silver:l168`; `b150` → `b131`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0`: `silver:l191` → `silver:l192`; `b46` → `b139`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l4` → `silver:l5`; `b94` → `b120`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l6` → `silver:l7`; `b52` → `b48`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l67` → `silver:l68`; `b26` → `b25`; Fim de coluna → topo da próxima; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l99` → `silver:l100`; `b80` → `b64`; Outro; erro da regra: True.
- `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0`: `silver:l159` → `silver:l160`; `b121` → `b92`; Entrada/saída de tabela ou imagem; erro da regra: True.

