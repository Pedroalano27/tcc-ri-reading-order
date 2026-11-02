# Unidades sem caixas finas — exportação para os ordenadores

Estado: amostra solicitada concluída. CPU, um processo, páginas em fluxo; sem treino de ordenador nesta tarefa.

Âncoras reexecutadas com os preditores P2/P1m e `erros_ponta_a_ponta.medir`, antes da exportação:

| Pipeline, golden_v4 | Páginas | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |
|---|---:|---:|---:|---:|---:|
| P2 | 44 | 0,985948 | 6,045455 | 94,81% | 92,72% |
| P1m | 44 | 0,952424 | 8,931818 | 92,62% | 91,70% |

Âncoras aprovadas pela tolerância solicitada. Não se avaliou um ordenador novo aqui.

| Partição | Representação | Páginas | Unidades | Mediana/página | p90 | Máximo | Páginas >510 | Unidades que atravessam | Palavras fora/vizinhas | Sem referência textual |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| golden_v3_novo | colunas | 27 | 110 | 3,0 | 6,4 | 14 | 0 | 51/90 (56,67%) | 44,72% | 20 |
| golden_v3_novo | colunas_margens | 27 | 117 | 3,0 | 7,0 | 15 | 0 | 51/96 (53,12%) | 44,54% | 21 |
| golden_v3_novo | linhas | 27 | 2258 | 69,0 | 161,4 | 401 | 0 | 2/2228 (0,09%) | 0,02% | 30 |
| golden_v3_novo_veiculos_nao_vistos | colunas | 27 | 110 | 3,0 | 6,4 | 14 | 0 | 51/90 (56,67%) | 44,72% | 20 |
| golden_v3_novo_veiculos_nao_vistos | colunas_margens | 27 | 117 | 3,0 | 7,0 | 15 | 0 | 51/96 (53,12%) | 44,54% | 21 |
| golden_v3_novo_veiculos_nao_vistos | linhas | 27 | 2258 | 69,0 | 161,4 | 401 | 0 | 2/2228 (0,09%) | 0,02% | 30 |
| golden_v4 | colunas | 44 | 239 | 3,5 | 8,7 | 35 | 0 | 83/175 (47,43%) | 39,36% | 64 |
| golden_v4 | colunas_margens | 44 | 241 | 4,0 | 8,7 | 35 | 0 | 63/175 (36,00%) | 31,43% | 66 |
| golden_v4 | linhas | 44 | 3729 | 56,0 | 145,8 | 493 | 0 | 4/3654 (0,11%) | 0,03% | 75 |
| golden_v4_veiculos_nao_vistos | colunas | 39 | 202 | 3,0 | 8,0 | 35 | 0 | 69/151 (45,70%) | 39,13% | 51 |
| golden_v4_veiculos_nao_vistos | colunas_margens | 39 | 202 | 4,0 | 7,0 | 35 | 0 | 49/149 (32,89%) | 29,58% | 53 |
| golden_v4_veiculos_nao_vistos | linhas | 39 | 3061 | 54,0 | 142,2 | 493 | 0 | 4/2999 (0,13%) | 0,03% | 62 |
| golden_v4_veiculos_vistos | colunas | 5 | 37 | 8,0 | 10,8 | 12 | 0 | 14/24 (58,33%) | 40,46% | 13 |
| golden_v4_veiculos_vistos | colunas_margens | 5 | 39 | 9,0 | 11,2 | 12 | 0 | 14/26 (53,85%) | 40,27% | 13 |
| golden_v4_veiculos_vistos | linhas | 5 | 668 | 113,0 | 247,4 | 257 | 0 | 0/655 (0,00%) | 0,00% | 13 |
| teste | colunas | 89 | 1009 | 3,0 | 20,4 | 169 | 0 | 195/929 (20,99%) | 29,56% | 80 |
| teste | colunas_margens | 89 | 999 | 3,0 | 18,2 | 169 | 0 | 187/919 (20,35%) | 29,67% | 80 |
| teste | linhas | 89 | 8942 | 87,0 | 164,6 | 401 | 0 | 52/8862 (0,59%) | 0,44% | 80 |
| treino | colunas | 151 | 1953 | 5,0 | 34,0 | 188 | 0 | 534/1768 (30,20%) | 34,55% | 185 |
| treino | colunas_margens | 151 | 2048 | 6,0 | 36,0 | 188 | 0 | 529/1863 (28,40%) | 31,77% | 185 |
| treino | linhas | 151 | 20226 | 129,0 | 211,0 | 489 | 0 | 252/20041 (1,26%) | 1,56% | 185 |
| treino_extra | colunas | 3023 | 42079 | 5,0 | 42,0 | 239 | 0 | 11903/39408 (30,20%) | 33,41% | 2671 |
| treino_extra | colunas_margens | 3023 | 45362 | 5,0 | 44,8 | 239 | 0 | 10848/42666 (25,43%) | 27,67% | 2696 |
| treino_extra | linhas | 3023 | 440260 | 139,0 | 237,8 | 538 | 4 | 6028/437589 (1,38%) | 2,21% | 2671 |
| validacao | colunas | 15 | 62 | 3,0 | 6,6 | 11 | 0 | 40/59 (67,80%) | 57,99% | 3 |
| validacao | colunas_margens | 15 | 56 | 3,0 | 5,6 | 7 | 0 | 37/53 (69,81%) | 57,90% | 3 |
| validacao | linhas | 15 | 2566 | 178,0 | 286,0 | 299 | 0 | 4/2563 (0,16%) | 0,02% | 3 |

Toda palavra disponível aparece em exatamente uma unidade em cada representação. A contagem inclui átomos sem palavras; o denominador de unidades que atravessam inclui só unidades com palavras na referência.

O rótulo de unidade é a mediana dos postos das suas palavras na referência. A fração fora/vizinhas conta palavras cujo posto é menor que o máximo da unidade anterior ou maior que o mínimo da seguinte, na ordem de medianas, considerando apenas vizinhas com referência. Uma palavra que viola ambos conta uma vez. Qualquer fração positiva marca a unidade como atravessando; é um diagnóstico de sobreposição de intervalos, não a métrica de eficácia de palavras e não certifica erro humano. Unidades sem palavra-ouro têm mediana nula e um posto auxiliar pela palavra-ouro geometricamente mais próxima, com marca explícita; não entram no denominador.

A silver usa **fluxo do PDF por palavra**, sem expansão dos blocos antigos: `palavras_da_pagina()` usa `use_text_flow=True`, guarda `s` e devolve palavras nesse fluxo. Os caches canônicos preservam a mesma lista; a sequência de referência é seus índices. A ordem `stream` dos blocos antigos usava o menor `s` do bloco, uma aproximação mais grossa. Não substituímos nem regeneramos a referência oficial armazenada.

Nas bancadas, a ordem-ouro de palavras é obtida por `ordem_sem_bbox_validacao_acervo.preparar`, com as mesmas funções `donos/linhas` usadas por `erros_ponta_a_ponta`. V4 usa palavras congeladas Diamond; v3 novo usa o cache canônico existente. A ordem humana é de regiões; sua expansão interna é geométrica, não anotação independente de palavras/células.

Página(s) de bancada excluída(s) do inventário de treino: 6. O inventário original tem 34 page_id compartilhados entre base e extra, que serão preservados na exportação completa e deduplicados pelo `montar_treino()` existente. IDs no manifesto. Há 3349 registros de páginas nas partições e 3293 page_id únicos; validação/teste preservam todas as páginas originais, inclusive sobreposições humanas, que não são amostras independentes. Bancadas e silver são reportadas separadamente.

Veículos de treino nas bancadas: v4 tem 5 páginas de veículos vistos e 39 não vistos; v3 novo tem 0 vistos e 27 não vistos. Ser visto significa pertencer ao split de treino silver; não significa que a página humana tenha entrado no treino.

Integridade e igualdade de page_id: as partições completas validação/teste são comparadas às fontes originais. Treino amostrado é comparado à seleção determinística elegível, após exclusão obrigatória das bancadas; o treino completo será comparado a todo esse universo elegível. Nenhuma página humana nem veículo RN/CE/MA/RJ aparece nas pastas de treino.

| Partição | Páginas cronometradas | Média s/página | Mediana | p90 | Máximo |
|---|---:|---:|---:|---:|---:|
| golden_v4 | 44 | 0,103 | 0,073 | 0,230 | 0,406 |
| golden_v3_novo | 27 | 0,164 | 0,059 | 0,243 | 1,763 |
| validacao | 15 | 6,850 | 5,143 | 13,365 | 20,566 |
| teste | 89 | 0,399 | 0,412 | 0,490 | 2,132 |
| treino | 151 | 3,298 | 2,008 | 5,145 | 31,950 |
| treino_extra | 3023 | 4,512 | 2,626 | 10,370 | 132,840 |

Maior pico de memória do processo registrado na criação das páginas ou nesta invocação: RSS 1226,5 MiB; memória comprometida 1880,9 MiB (API Windows). Tempo desta invocação 18954,7 s, incluindo âncoras, exportação e auditorias; tempos por página são os da criação original, preservados na retomada, e incluem leitura/hash/cache, renderização, detector quando necessário e três representações, excluindo âncoras e reexportações. Manifestos de invocações anteriores ficam em `cache/execucoes/`. Não é benchmark controlado; páginas humanas e parte da silver usam caches prévios.

Estimativa para as 43 páginas de treino restantes: 0,05 h, usando média de 3174 páginas de treino (4,454 s/página). Treino total elegível: 3217. Extrapolação de amostra base; extra pode ter densidade e custo de PDF diferentes. Não foi executado o treino completo.

Formato: `<representação>/<uf>.jsonl` e `<representação>_extra/<uf>.jsonl` seguem `bounding_boxes/ordens/stats/dimensions`; palavras e referência textual ficam no irmão `<uf>.palavras.jsonl`, ignorado pelo protocolo. `ks/tipo` são extras por unidade. `bancadas/{golden_v4,golden_v3_novo}.jsonl` tem uma linha por página com palavras, `gt_w/gt_l/gold_lines/reg_words` e três páginas compatíveis sob `representacoes`. IDs das unidades recebem permutação independente da referência; a entrada dos métodos usa `ordem_entrada`, semente `entrada-{page_id}`.

As representações são chamadas diretamente, sem copiar/reajustar sua lógica. Tabela/imagem: mesmos pesos ls3 e parâmetros P2, CPU, imgsz 1024, conf 0,25, NMS IoU 0,7, max_det 300; retenção de átomos ≥0,45. As classes finas do Docling e as classes humanas não entram nessas representações. `colunas_margens` chama `representar_estruturas`: ls3 não prevê cabeçalhos/rodapés, portanto a separação depende das bordas isoladas e da moldura/texto institucional. `ks` e texto internos são preservados como devolvidos pelas funções; não são reordenados pelo ouro.

Limitações: v4 usado no desenvolvimento das colunas; v3 novo pequeno e de conveniência; silver automática em veículos selecionados por concordância com XY-cut; veículos humanos vistos/não vistos separados acima. Sem OCR, sem uso de dados Label Studio, sem novos pesos. Cruzamento, perda de calha e ordem interna não podem ser corrigidos pelo ordenador de unidades indivisíveis. LayoutLM admite 512 tokens, incluindo especiais: acima de 510 unidades o codificador existente pode exceder o limite mesmo com um token por unidade; abaixo disso o orçamento textual por unidade encolhe. Não silenciosamente filtre essas páginas nem anuncie compatibilidade neural completa sem tratamento próprio na tarefa dos ordenadores.

Retomada: cada página completa é salva atomicamente; shards são publicados a cada 50 páginas e no encerramento. Caches completos sobrevivem mesmo antes da publicação. Treino base e depois extra têm embaralhamento fixo 20261004. `treino_pronto.json` só aparece quando o universo inteiro terminar.

Comando exato, da raiz, para o orquestrador continuar a exportação:

```powershell
venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 0
```

Auditoria sem inferência:

```powershell
venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 60 --conferir
venv/Scripts/python.exe -B -c "import os; os.environ['TCC_DIR_BLOCOS']='resultados/unidades_sem_caixas/colunas'; from src.eval import protocolo; print(len(protocolo.carregar_particao('validacao')))"
```

Todos os números desta página são calculados pelo script a partir dos caches; hashes e contagens detalhados em `resultados/unidades_sem_caixas/manifesto.json`.
