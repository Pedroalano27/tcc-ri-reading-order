# E003 — preparo do escore contrastivo

Gerado por `venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py preparo`. Todos os números medidos vêm dos JSONs indicados; a estimativa de tempo é explicitamente calculada. Nenhum comando foi executado no cluster nesta tarefa.

## Âncora e proteção dos dados

Âncora reexecutada em 44 páginas: τ 0,985948 e 6,045455 quebras/página. Sequências idênticas ao P2 histórico. Os IDs do manifesto foram conferidos contra `experimentos/TESTE_CEGO.lock` antes da leitura das páginas; sem interseção. Nada foi gravado em data/; data/labelstudio/ não foi lido nem usado. A fumaça avalia somente golden_v4. golden_v3_novo já foi consultado em rodadas anteriores e continua externo ao ajuste atual.

## Contrato e compatibilidade

`exportar-marginal` deriva os arquivos dos pares condicionais congelados, sem gerar candidatos novos. Mantém o JSONL agrupado por página, aceito pelo job: cada linha tem page_id e pares; dentro de pares há exatamente um item por id_destino distinto naquela página, inclusive null/FIM. Cada item tem id_fonte=null, contexto vazio e a continuação original (primeiras palavras já exportadas). Destinos diferentes com texto igual continuam distintos. Manifestos locais guardam hashes; somente os JSONLs e o pontuador são necessários no cluster.

O contexto vazio é um único BOS, sem espaço ou quebra de linha. O BOS vem do tokenizer ou, quando ausente nele, da configuração do modelo. A continuação mantém o espaço prefixado e a tokenização separada original; FIM continua sendo EOS. O BOS não entra em n_tokens. Contextos condicionais não vazios mantêm o comportamento v1.

Com `--escores-marginal DIR`: s=(logp_soma_condicional−logp_soma_marginal)/n_tokens. A subtração precede o log-softmax por fonte e a combinação com os priors. Sem a opção, usa logp_media condicional (ablação). O decodificador confere hashes dos pares e configurações, destinos únicos, texto idêntico, modelo/dtype, revisão disponível e n_tokens igual; falta de marginal é erro, sem descartar páginas silenciosamente. A revisão resolvida ausente nos escores legados é registrada como limitação, não presumida igual. A retomada do pontuador continua por página, com flush/fsync e reparo só da última linha interrompida. O hash do script mudou: pontuações novas usam outra pasta; as antigas continuam legíveis.

Leitura/validação dos escores legados Qwen3-8B, sem nova avaliação: golden_v4: 44 páginas; golden_v3_novo: 27 páginas; teste_silver: 89 páginas; validacao_silver: 15 páginas. Evidência: `verificacao_preparo.json`.

## Exportação marginal

Fonte: `resultados/ordem_lm/pares_marginal/MANIFESTO.json`.

| Bancada | Páginas | Pares condicionais | Destinos marginais | Bytes JSONL | MiB |
|---|---:|---:|---:|---:|---:|
| golden_v4 | 44 | 19197 | 3761 | 486646 | 0,464 |
| golden_v3_novo | 27 | 11355 | 2275 | 301047 | 0,287 |
| teste_silver | 89 | 43367 | 8995 | 1237808 | 1,180 |
| validacao_silver | 15 | 13201 | 2579 | 357109 | 0,341 |

Total: 17610 itens marginais / 87120 condicionais; 2382610 bytes (2,272 MiB) em JSONL. Manifesto local: 1982 bytes. Exportação: 4,163 s.

As bancadas preservam as sobreposições históricas; não devem ser somadas como amostras independentes para inferência.

## Fumaça local executada

Execução sequencial em CPU, quatro threads, sem multiprocessing; modelo já presente no cache, acesso à rede desabilitado. Comandos da raiz, em PowerShell:

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py autoteste
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py exportar-marginal
venv/Scripts/python.exe -B cluster/pontuar_pares_lm.py --entrada resultados/ordem_lm/pares --saida resultados/e003_lm/escores_condicional --modelo Qwen/Qwen3-0.6B --revisao c1899de289a04d12100db370d81485cdf75e47ca --dtype float32 --lote 4 --threads 4 --dispositivo cpu --bancada golden_v4 --limite-paginas 3
venv/Scripts/python.exe -B cluster/pontuar_pares_lm.py --entrada resultados/ordem_lm/pares_marginal --saida resultados/e003_lm/escores_marginal --modelo Qwen/Qwen3-0.6B --revisao c1899de289a04d12100db370d81485cdf75e47ca --dtype float32 --lote 4 --threads 4 --dispositivo cpu --bancada golden_v4 --limite-paginas 3
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/e003_lm/escores_condicional/Qwen_Qwen3-0.6B --saida resultados/e003_lm/condicional
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/e003_lm/escores_condicional/Qwen_Qwen3-0.6B --escores-marginal resultados/e003_lm/escores_marginal/Qwen_Qwen3-0.6B --saida resultados/e003_lm/contrastivo
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py preparo
```

| Termo | Páginas | Itens pontuados | Tokens de continuação | Tempo de pontuação (s) | Carga (s) | Pico RSS (MiB) |
|---|---:|---:|---:|---:|---:|---:|
| condicional | 3 | 423 | 7882 | 578,924 | 51,265 | 4193,973 |
| marginal | 3 | 96 | 2246 | 36,950 | 22,691 | 4458,219 |

BOS usado: 151643 (config_modelo); EOS: 151645. A contagem de tokens condicional/marginal foi conferida para cada aresta na decodificação, incluindo FIM. Os autotestes exercitam deduplicação, mudança de preferência pelo contraste, divisão por n_tokens, recusa de tokens divergentes e cobertura dos decodificadores.

Exemplo real (primeira aresta não-FIM da primeira página): (-114,298600 − (-129,264412)) / 41 = 0,365020. IDs e valores completos em `verificacao_preparo.json`.

Páginas da fumaça:

- `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`
- `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20`
- `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2`

As configurações são as predefinidas para fumaça; não houve escolha de parâmetros ou checkpoint. IC95 e Wilcoxon abaixo são descritivos de uma amostra mínima; não sustentam conclusão sobre H3.

| Bancada | Condicional pontuadas/esperadas | Contrastivo pontuadas/esperadas |
|---|---:|---:|
| golden_v4 | 3/44 | 3/44 |
| golden_v3_novo | 0/27 | 0/27 |
| teste_silver | 0/89 | 0/89 |
| validacao_silver | 0/15 | 0/15 |

### Golden v4 — somente fumaça

| Escore | Decoder | Quebras/pág | τ | Fidelidade 12 | Sucessor linhas | Δ quebras [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior | Reparos/regressões |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| condicional | seletiva (seletiva_r0.5_t0.5) | 24,667 | 0,878590 | 0,304906 | 0,151515 | 21,333 [4,000; 30,000] | 0,179712 | 0/0/3 | 0/63 |
| condicional | global (global_r0.5_n0.0) | 23,000 | 0,443039 | 0,374067 | 0,272727 | 19,667 [1,000; 29,000] | 0,179712 | 0/0/3 | 1/56 |
| contrastivo | seletiva (seletiva_r0.5_t0.5) | 25,000 | 0,947644 | 0,313772 | 0,161616 | 21,667 [3,000; 31,000] | 0,179712 | 0/0/3 | 0/60 |
| contrastivo | global (global_r0.5_n0.0) | 23,000 | 0,800624 | 0,358639 | 0,280808 | 19,667 [2,000; 28,500] | 0,179712 | 0/0/3 | 2/57 |

Mudanças de ordem entre condicional e contrastivo: seletiva: 3 páginas; global: 3 páginas. Régua importada de erros_ponta_a_ponta/bancada_ordenadores; entrada e desempates seguem entrada-{page_id}. Cobertura integral de unidades e palavras validada para cada predição. Detalhes, IC95 e Wilcoxon de todas as métricas e diagnóstico por classe estão em `condicional/AVALIACAO.md`, `contrastivo/AVALIACAO.md` e nos respectivos `avaliacao.json`.

### Golden v3 novo e teste silver

Arquivos marginais exportados; nenhuma página dessas bancadas foi pontuada ou avaliada nesta fumaça. Os contrastes externos, páginas melhor/igual/pior e reparos/regressões completos aguardam os escores do cluster. RN também aguarda pontuação marginal integral.

## Comandos preparados para o cluster — NÃO executados

Copiar apenas os JSONLs de entrada automática e os scripts, sem anotações nem o manifesto de auditoria. Estes comandos usam o alias SSH já configurado no projeto. Executar da raiz local quando autorizado:

```powershell
ssh dgx-spark "mkdir -p ~/tcc/ordem_lm/pares_marginal ~/tcc/repo/cluster ~/tcc/logs"
scp cluster/pontuar_pares_lm.py cluster/requisitos_pontuar.txt dgx-spark:~/tcc/ordem_lm/
scp cluster/job_pontuar.sh dgx-spark:~/tcc/repo/cluster/
scp resultados/ordem_lm/pares_marginal/golden_v4.jsonl resultados/ordem_lm/pares_marginal/golden_v3_novo.jsonl resultados/ordem_lm/pares_marginal/teste_silver.jsonl resultados/ordem_lm/pares_marginal/validacao_silver.jsonl dgx-spark:~/tcc/ordem_lm/pares_marginal/
ssh dgx-spark "cd ~/tcc/repo && sbatch --partition=hpc-spark-45 --time=02:00:00 cluster/job_pontuar.sh Qwen/Qwen3-8B --entrada pares_marginal --saida escores_marginal"
```

O job executa em ~/tcc/ordem_lm; os argumentos extras aparecem depois dos defaults, portanto --entrada pares_marginal e --saida escores_marginal prevalecem. Mantém bf16, lote e quatro threads; usa a partição principal, PYTHONNOUSERSITE=1 e retomada por página. Reenviar o mesmo comando retoma quando a saída tem configuração/hash idênticos. Não misturar as novas marginais com as pastas condicionais existentes. O nome sanitizado do modelo é acrescentado à saída.

Após o job, trazer os escores e decodificar localmente:

```powershell
New-Item -ItemType Directory -Force resultados/ordem_lm/escores_marginal | Out-Null
scp -r dgx-spark:~/tcc/ordem_lm/escores_marginal/Qwen_Qwen3-8B resultados/ordem_lm/escores_marginal/
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --saida resultados/e003_lm/ablacao_8b
venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --escores-marginal resultados/ordem_lm/escores_marginal/Qwen_Qwen3-8B --saida resultados/e003_lm/contrastivo_8b
```

## Estimativa de tempo

Proxy calculada com os escores condicionais Qwen3-8B já existentes na NVIDIA GB10: 87120 itens em 4617,166 s, ou 0,052998 s/item. À mesma vazão por item, 17610 marginais custariam 933,291 s = 15,55 min, mais carga/ambiente/fila. A carga histórica registrada foi 456,457 s. Fonte: `resultados/ordem_lm/escores/Qwen_Qwen3-8B/`.

É uma estimativa de planejamento, não uma medição marginal no cluster: BOS encurta a entrada, mas padding, distribuição de comprimentos, EOS, lote e tokenização afetam a vazão. O limite de tempo solicitado no comando deixa folga; atualizar a ETA com as primeiras páginas do job. Os tempos da fumaça em CPU/0.6B não são extrapolados para a GB10/8B.

## O que falta para o 2×2 (depende do E004)

| Geometria | Sem LM | Com LM contrastivo |
|---|---|---|
| Fixa (regra/priors) | mesmos candidatos e decoder, peso LM zero | mesmos candidatos e decoder, contraste 8B |
| Aprendida (LightGBM, E004) | escores de arestas do E004 | mesmos escores + contraste 8B |

- Pontuar todas as marginais com Qwen3-8B e auditar identidade dos pesos/tokenizer: a revisão resolvida dos condicionais antigos está ausente. Se não for possível certificar a revisão, registrar essa limitação ou repontuar os dois termos com revisão fixada, sem sobrescrever os escores antigos.
- Aguardar o E004 definir e exportar os escores geométricos aprendidos. Congelar um mesmo conjunto de candidatos e um mesmo decoder para as quatro células; se os candidatos/continuações mudarem, pontuar as arestas novas e exportar suas marginais, mantendo o teste cego lacrado.
- Congelar grade/normalização e escolher pesos somente em golden_v4 + validação RN. A fumaça 0.6B só verifica o caminho. A seleção atual do script é a grade histórica de geometria fixa; o adaptador do E004 e a comparação controlada das quatro células continuam pendentes.
- Produzir as três bancadas separadas (v4, v3 novo, teste silver), com RN separada para ajuste; reportar Δ/IC95 por veículo e Wilcoxon por veículo, páginas melhor/igual/pior, reparos/regressões de sucessores, cobertura e custo, incluindo o híbrido 67 como baseline forte. A régua atual preserva todos os elementos marginais; uma análise só do corpo ainda exige uma política comum e explícita.
- Tratar a comparação como exploratória: v4 já foi usado no desenvolvimento da regra, v3 novo já foi consultado e silver usa fluxo PDF ruidoso. Aplicar o critério pré-registrado do cartão E003 somente após o 2×2 completo; avaliação confirmatória do teste cego cabe ao orquestrador.
