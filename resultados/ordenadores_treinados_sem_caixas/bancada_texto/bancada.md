# Ordenadores sobre unidades sem caixas finas

## Resposta em cinco linhas

- **linhas** — golden_v4: sucessor_linhas_texto_s42, 20,77 quebras/página; golden_v3_novo: sucessor_linhas_texto_s42, 23,19 quebras/página; teste_silver: sucessor_linhas_texto_s42, 50,46 quebras/página.
- **colunas** — golden_v4: pendente; golden_v3_novo: pendente; teste_silver: pendente.
- **colunas_margens** — golden_v4: pendente; golden_v3_novo: pendente; teste_silver: pendente.
- **Custo da representação (teto exportado)** — pendente.
- Menos erros significa menor média de quebras; empates ficam explícitos. Comparação de bancada só é conclusiva após completar os seis ordenadores. O teto mediano não garante ótimo combinatório; o piso interno canônico é irredutível.

## Âncoras

P2 canônico reexecutado: τ 0,985948, 6,045455 quebras/página. Extrator + XY-cut + margens importado: τ 0,952424, 8,931818. As sequências e métricas P2 conferem por página com o histórico; P1m vem de `resultados/erros_ponta_a_ponta.json`. A configuração é `projecao_local_margens` 0,45 / 1,2 / 0,08. A regra sobre linhas reproduz τ 0,985948 e 6,045455 quebras/página: 44 sequências idênticas ao P2. Toda unidade é um conjunto de palavras; `ordem_sem_bbox.fluxo()` ordena suas palavras em todas as representações, bancadas e predições externas.

## Diagnóstico separado: custo de `ks` cru

No golden_v4/linhas, regra com `ks` cru: τ **0,983190**, **16,86 quebras/página**, piso interno **11,07**. Com expansão canônica, piso **0,545455**. A ordem crua difere em 10 páginas. Esses números crus não entram na comparação de ordenadores. Saídas bloqueadas anteriores preservadas em `resultados/ordenadores_sem_caixas/arquivo_0030/`.


Vão lado a lado = palavras na mesma linha geométrica separadas por mais de `max(4; 1,2 × altura mediana)`. Nas faixas, a expansão canônica pode intercalar esses trechos; isso é um custo da representação, ainda presente no piso. A tipologia e os exemplos descrevem divergências entre expansões; não certificam que toda mudança melhora a leitura.

## golden_v4

44 páginas, 27 veículos; 5 páginas de veículos vistos no treino e 39 não vistos. 

Valores macro por página [IC 95% agrupado por veículo]. Piso é média de quebras internas por página.

| Representação | Ordenador | Veículos | n | τ palavras | Quebras/página | Quebras/mil | Fidelidade 12 | Sucessor linhas | Piso interno | p veículo (quebras) | >510 agrupadas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| linhas | sucessor_linhas_texto_s42 | todos (27) | 44 | 0,942 [0,888; 0,975] | 20,77 [6,31; 45,83] | 19,77 [11,70; 29,28] | 88,7 [83,2; 93,5]% | 86,7 [80,2; 92,2]% | 0,55 [0,05; 1,21] | — | 0 |
| linhas | sucessor_linhas_texto_s42 | vistos (5) | 5 | 0,987 [0,966; 1,000] | 16,20 [4,40; 35,80] | 11,86 [4,26; 23,53] | 93,3 [85,7; 98,1]% | 93,1 [86,0; 97,7]% | 1,20 [0,00; 3,60] | — | 0 |
| linhas | sucessor_linhas_texto_s42 | não vistos (22) | 39 | 0,936 [0,875; 0,973] | 21,36 [5,58; 48,51] | 20,78 [12,11; 31,32] | 88,2 [82,0; 93,4]% | 85,9 [78,6; 91,9]% | 0,46 [0,03; 1,11] | — | 0 |
## golden_v3_novo

27 páginas, 10 veículos; 0 páginas de veículos vistos no treino e 27 não vistos. Não há páginas vistas nesta bancada; por isso não existe estimativa para esse grupo.

Valores macro por página [IC 95% agrupado por veículo]. Piso é média de quebras internas por página.

| Representação | Ordenador | Veículos | n | τ palavras | Quebras/página | Quebras/mil | Fidelidade 12 | Sucessor linhas | Piso interno | p veículo (quebras) | >510 agrupadas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| linhas | sucessor_linhas_texto_s42 | todos (10) | 27 | 0,931 [0,860; 0,988] | 23,19 [6,71; 48,19] | 26,75 [11,57; 40,68] | 86,7 [76,3; 94,8]% | 84,7 [75,7; 90,7]% | 0,26 [0,00; 0,67] | — | 0 |
| linhas | sucessor_linhas_texto_s42 | não vistos (10) | 27 | 0,931 [0,860; 0,988] | 23,19 [6,71; 48,19] | 26,75 [11,57; 40,68] | 86,7 [76,3; 94,8]% | 84,7 [75,7; 90,7]% | 0,26 [0,00; 0,67] | — | 0 |
## teste_silver

89 páginas, 3 veículos; 0 páginas de veículos vistos no treino e 89 não vistos. Não há páginas vistas nesta bancada; por isso não existe estimativa para esse grupo.

Valores macro por página [IC 95% agrupado por veículo]. Piso é média de quebras internas por página.

| Representação | Ordenador | Veículos | n | τ palavras | Quebras/página | Quebras/mil | Fidelidade 12 | Sucessor linhas | Piso interno | p veículo (quebras) | >510 agrupadas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| linhas | sucessor_linhas_texto_s42 | todos (3) | 89 | 0,930 [0,813; 0,974] | 50,46 [35,42; 128,85] | 59,91 [36,56; 82,17] | 74,4 [59,3; 82,9]% | 71,0 [61,5; 74,7]% | 16,18 [7,85; 23,87] | — | 0 |

## Quando a mediana não é teto

Nas comparações completas disponíveis, a ordem mediana não ficou abaixo da regra em τ nem em quebras médias.

Posto mediano é um oráculo de referência, sem garantia de máximo τ ou mínimo de quebras. Onde perde para a regra, não é teto de verdade. O piso interno tem garantia: nenhuma permutação de unidades conserta essas transições.


## Protocolo e limitações

Bootstrap percentil de 95%, 5000 reamostras de veículos, semente 20261004; todas as páginas de cada veículo sorteado ficam juntas. A média é macro por página. Quebras/mil também é média das taxas por página. O JSON guarda totais, IC de todas as métricas e deltas pareados.

Wilcoxon bilateral Pratt (`zero_method='pratt'`, aproximação normal) sobre médias das diferenças pareadas por veículo, contra regra_colunas na mesma representação e bancada. O JSON inclui os testes de τ, quebras, taxa por mil, fidelidade 12 e sucessor de linhas. P-valores exploratórios sem correção de multiplicidade; células sem base completa ficam pendentes. Com poucos veículos, especialmente no silver, a inferência tem baixa resolução.

Golden v4 foi usado no desenvolvimento da regra de colunas e na escolha dos parâmetros; não é teste independente. Golden v3 novo usa páginas adicionais, mas pode repetir veículos/layouts do desenvolvimento. A coluna vistos refere-se ao split de treino do TCC, não ao treino prévio do detector ls3 ou do LayoutReader. O ouro humano é ordem de regiões expandida geometricamente, não anotação independente de cada palavra/linha; no v3 há projeção sobre blocos do extrator. Tabelas têm ordem interna potencialmente ambígua.

Silver usa fluxo de conteúdo PDF, só CE/MA/RJ do split congelado. É referência automática escolhida por concordância com XY-cut por veículo, favorecendo regras geométricas. Linhas silver são trechos contíguos do fluxo, separados por linhas geométricas com gap 1,2; sucessor silver não é ouro humano. Há 21 páginas em comum entre silver e as bancadas humanas: tabelas separadas, sem somar como observações independentes.

Teto = `ordens.stream` da tarefa 01, derivada do posto mediano das palavras. Unidades que atravessam a referência impedem um teto combinatório exato. O piso soma `eventos(fluxo([unidade], palavras), gt_w)` dentro de cada unidade, incluindo palavras sem referência interpostas; reordenar IDs não altera esses pares. O custo do teto inclui esse piso e fronteiras da ordem mediana; não atribuir tudo ao ordenador. Unidades sem palavras participam da permutação, mas não das métricas textuais.

Entrada determinística `random.Random(f'entrada-{page_id}')`, via protocolo; preditores automáticos recebem apenas IDs, caixas, tipos/texto e palavras. LayoutReader usa o adaptador local em CPU/float32; acima de 510 unidades, há agrupamento geométrico ou hierarquia espacial, preservando todas as unidades. A carga de pesos é sequencial (`HF_DEACTIVATE_ASYNC_LOAD=1`), com leitura direta (`disable_mmap=True`): a materialização por memória mapeada esperou no Windows, mesmo após desativar a carga assíncrona. Isso mede um híbrido nessas páginas, não inferência neural direta em todas as linhas. A coluna >510 mostra páginas efetivamente agrupadas; diagnósticos por página ficam no JSON. Um único processo, threads no máximo 4, sem workers ou abertura de PDFs. Nenhum treino/modelo de linguagem nesta tarefa. ls3 só fornece detecções em cache; seus dados parceiros não foram lidos.

## Retomada e integração

```powershell
venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py
venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --metodos layoutreader_pronto --max-minutos 30
venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --avaliar-pred resultados/ordenadores_sem_caixas/pred/modelo__linhas__golden_v4.jsonl
venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --conferir
```

Contrato JSONL estrito: `{"page_id": "...", "ordem": ["b0", "b1"]}`. Nomes: `<ordenador>__<linhas|colunas|colunas_margens>__<golden_v4|golden_v3_novo|teste_silver>.jsonl`; `teste` é aceito como alias. Opções explícitas `--ordenador`, `--representacao`, `--bancada` aceitam nomes externos. Predições parciais têm cobertura declarada. IDs/páginas incompatíveis falham; nunca são reparados. `--avaliar-pred` atualiza só a predição recebida e o relatório, reaproveitando resultados anteriores; nenhum modelo é carregado. Predições e métricas são persistidas a cada página. Fontes e código são identificados por SHA-256; mudança de fontes é recusada. Shards de entrada são fechados após cada linha, antes do processamento. `ancora_ok.json` só é publicado quando as âncoras e as 54 combinações obrigatórias estão completas e conferidas.

Progresso persistido: `{"ancoras": {"concluidas": 44, "esperadas": 44}}`.
