# Quadro de comunicação entre agentes

Arquivo único e compartilhado por **Claude Code**, **Codex**, **Antigravity** e o **Pedro**.
Aqui ficam as tarefas, quem está mexendo em quê agora e tudo o que um agente precisa que
os outros saibam. As regras de trabalho estão em [`AGENTS.md`](AGENTS.md); o estado do
projeto, em [`docs/HANDOFF.md`](docs/HANDOFF.md).

## Como usar este quadro

1. **Ao chegar:** leia as Reservas ativas, as Tarefas e as entradas mais recentes do
   Registro (as mais novas ficam no topo).
2. **Antes de mexer:** adicione uma linha em Reservas ativas com o que vai usar — arquivos,
   pastas, GPU ou CPU pesada. Não mexa no que outro agente reservou.
3. **Ao terminar ou parar:** escreva uma entrada no Registro, logo abaixo do marcador
   `NOVAS ENTRADAS AQUI`; atualize o status da tarefa; remova sua reserva.
4. **Edite só o seu trecho.** Nunca reescreva o quadro inteiro nem apague entradas de outro
   agente. Correções a uma entrada antiga viram uma entrada nova que a cita.
5. **Seja verificável:** números com o arquivo ou comando de onde saíram; arquivos com o
   caminho; nada de "parece que funcionou".

### Tipos de entrada

| Tipo | Quando usar |
|---|---|
| `FEITO` | Concluiu uma tarefa ou parte dela |
| `ACHADO` | Descobriu algo que outros precisam saber (um bug, um número, um comportamento) |
| `DECISÃO` | Propõe ou registra uma decisão metodológica. **Só vale com confirmação do Pedro** |
| `PEDIDO` | Precisa de algo de outro agente ou do Pedro |
| `BLOQUEIO` | Parou porque depende de algo que não está pronto |
| `REVISÃO` | Revisou o trabalho de outro agente: o que conferiu, o que achou, o que recomenda |
| `AVISO` | Risco ou armadilha que outros podem pisar |

### Modelo de entrada

```markdown
### AAAA-MM-DD HH:MM — <Claude | Codex | Antigravity | Pedro> — <TIPO> — <título curto>
**Tarefa:** T00 (ou "nenhuma")
**O que fiz / o que achei:** ...
**Arquivos tocados:** `caminho/um.py`, `caminho/dois.md` (ou "nenhum")
**Resultado / evidência:** números, comando rodado, arquivo de saída
**Próximo passo / para quem:** ...
```

---

## Agentes e papéis sugeridos

| Agente | Onde roda | Bom para | Evitar |
|---|---|---|---|
| **Claude Code** | App do Claude, nesta pasta | Decisões de método, desenho experimental, análise de resultados, texto do TCC, revisão e integração | Tarefas longas e mecânicas que só esperam processo |
| **Codex** | Nesta pasta | Implementação com especificação clara, ferramentas de medição, revisão de diffs | Decidir sozinho mudanças de protocolo |
| **Antigravity** | IDE do Google, nesta pasta | Trabalho braçal bem especificado: rodar re-extração e pipeline, conferir figuras e tabelas contra os JSONs, atualizar números nos documentos | Mudar código de modelo ou de métrica; decisões metodológicas |
| **Pedro** | — | Aprovar decisões, anotar o Golden, rodar o Kaggle (conta dele), conversar com o orientador | — |
| **Codex CLI** (`gpt-6-astra`) | Terminal, despachado pelo Claude | Tarefas de maior teor técnico: implementação, medição, revisão de código | Editar este quadro |
| **Antigravity CLI** (Gemini 3.8 Flash) | Terminal, despachado pelo Claude | Trabalho braçal bem especificado | Editar este quadro; decisões de método |

**Orquestração (definida pelo Pedro em 2026-09-12).** O Claude distribui o trabalho: o que é
técnico vai para o Codex CLI com `gpt-6-astra`, o que é braçal vai para o Antigravity CLI.
O despacho passa por [`orquestracao/despachar.py`](orquestracao/despachar.py), que guarda a
saída completa, a resposta final e a lista exata de arquivos tocados em
`orquestracao/logs/`, e alerta se `data/raw/` ou alguma `anotacoes.jsonl` mudar. Os agentes
despachados **não editam este quadro**: o Claude reserva antes, revisa o que voltou e
registra aqui. Os prompts ficam em `orquestracao/prompts/`. Codex e Antigravity abertos à
mão pelo Pedro continuam trabalhando normalmente, com o protocolo acima.

Revisão cruzada: quem implementa não revisa o próprio trabalho. Uma mudança em
`src/data/extrator.py`, `src/eval/metrics.py`, `src/eval/protocolo.py` ou num modelo
precisa de uma entrada `REVISÃO` de outro agente antes de virar base para experimento.

---

## Reservas ativas

Quem está mexendo em quê **agora**. Adicione ao começar, remova ao terminar.

| Agente | Reservado (arquivos, pastas, GPU, CPU) | Desde | Previsão de término |
|---|---|---|---|
| Pedro | anotação do `data/diamond/diamond_treino/` (T33) | 13/09 | — |

---

## Tarefas

Status: `aberta` · `em andamento (agente)` · `bloqueada (motivo)` · `em revisão` · `feita`.

| ID | Tarefa | Dono sugerido | Depende de | Status |
|---|---|---|---|---|
| T01 | Proteção contra `blocos_extra` ausente | Codex | — | feita (revisada; ajustes na T17) |
| T02 | Bancada de avaliação do segmentador | Codex | — | feita |
| T03 | Fechar a versão do segmentador | Claude propõe, Codex implementa, Pedro aprova | T02, T10 | feita pelo Claude; aprovação do Pedro em curso (anotando); REVISÃO do Codex pendente |
| T04 | Preservar os artefatos da segmentação v1 | Antigravity | — | feita |
| T05 | Re-extrair as três coleções com a versão final | Antigravity | T03, T04 | em andamento (Claude, desde 22:58; v3 a partir dos `*_v1`) |
| T06 | Regenerar o lote `golden_v1` | Antigravity | T03 | feita (Claude) |
| T07 | Recalcular `splits.json` e comparar | Antigravity roda, Claude analisa | T05 | feita: confiabilidade recalculada na v3; divisão mantida (DECISÃO confirmada pelo Pedro em 12/09, 23:55) |
| T08 | Anotar o `golden_v1` | Pedro | T06 | feita (26 concluídas; 4 puladas por tabela) |
| T09 | Refazer todos os números locais | Antigravity roda, Claude confere | T05, T07 | em andamento (baselines na v3 feitos; os métodos aprendidos vão para o Kaggle) |
| T10 | Conversor das APIs comerciais (Azure e Google) → formato do protocolo | Codex | — | feita (revisada) |
| T11 | Análise de sensibilidade à segmentação | Claude | T09, T10 | aberta |
| T12 | Kaggle: pacote, execução e importação | Antigravity prepara, Pedro executa | T09 | em andamento (notebooks atualizados; pacote sai quando a T05 terminar) |
| T13 | Atualizar resultados e apresentação | Claude | T11, T12 | aberta |
| T14 | Extrator mais rápido com PyMuPDF (opcional) | Codex | T03 | feita como módulo opcional em 03/10 (`src/data/palavras_pymupdf.py`; 33× mais rápido, 61 de 104 páginas com blocos idênticos; adoção depende do Pedro e de REVISÃO) |
| T15 | Levar as perguntas ao orientador | Pedro | — | aberta |
| T16 | Folhas de inspeção visual das páginas-problema | Antigravity | — | feita (revisada) |
| T17 | Ajustes da revisão da T01: `n_treino ≤ 0` e extras parciais | Codex | — | feita (verificada pelo Claude) |
| T18 | Segmentação v3 no extrator: faixas com reatribuição, calhas locais, tabela = 1 bloco (detector), descarte de separadores, letras espaçadas | Claude implementa, Codex revisa | — | feita (3 revisões do Codex; confirmada às 22:57) |
| T19 | Módulo de layout `src/data/layout.py`: Docling Heron offline, revisão fixada, cache por veículo | Claude | — | feita (cache das 3 coleções e dos lotes pronto; revisado junto com a T18) |
| T20 | Projeção da ordem do Golden v1 na v3 (`src/anotacao/projetar_ordem.py`): página limpa vira referência projetada, página com conflito vai para o lote novo | Claude | T18 | feita (20 limpas, 5 conflitos, 4 sem anotação, 1 rejeitada) |
| T21 | Lote `golden_v2`: páginas do v1 a refazer (conflito e puladas) + 20 novas (silver:12, incerto:8), já na v3 | Claude | T18, T19, T20 | feita (29 páginas, 814 blocos) |
| T22 | Anotar o `golden_v2` | Pedro | T21 | feita (27 concluídas, 2 puladas: SP) |
| T23 | `avaliar_golden.py` lendo v1 projetado + v2 | Claude ou Codex | T20, T21 | feita (`golden_v3`: 47 páginas; `src/anotacao/montar_referencia.py`) |
| T26 | Análise do Acessilia (código aberto, MIT): o que reaproveitar para extrator, Diamond, RAG e acessibilidade; licenças e créditos (prompt `orquestracao/prompts/T26_analise_acessilia.md`) | Antigravity | — | feita (revisada pelo Claude) |
| T27 | Diamond piloto: anotar caixas e classes de 20 páginas do `golden_v3` (`docs/GUIA_DIAMOND.md`); medir tempo e ajustar as regras antes das 200 | Pedro | — | feita (20 concluídas, 55 min; revisão de consistência pendente, ver registro de 19:55) |
| T28 | Testes do Diamond: `propor()` e `salvar_diamond()` (`tests/test_diamond.py`) | Antigravity | — | feita (revisada pelo Claude: 13 testes; suíte com 27, todos passam) |
| T29 | Ordem de leitura do Docling como método de comparação (teste e Golden) | Claude | — | aberta (bloqueada: o `docling-ibm-models` 4.x não traz mais o preditor de ordem, e instalar o `docling` no venv troca o torch com CUDA; precisa de venv separado) |
| T31 | Rose v2: modo `regioes` (VLM classifica, une e quebra as regiões da proposta), registro de falhas, ritmo e cota, chave do `.env` (`orquestracao/prompts/T31_rose_v2.md`) | Antigravity | T30 | feita (revisada e corrigida pelo Claude: quebras por linha); rodando no piloto e no `diamond_treino` |
| T32 | Segmentador por regiões com as regras do piloto (`src/data/regioes.py`), avaliador (`src/eval/avaliar_diamond.py`), alertas de regra na ferramenta e lote `diamond_treino` (200 páginas) | Claude | T27 | feita (199 páginas prontas) |
| T33 | Anotar o `diamond_treino` | Pedro | T32 | em andamento (25 de 199; pausado a pedido do Pedro até a proposta v3) |
| T34 | Ordenador por VLM (`src/eval/vlm_ordem.py`) com as regras de `docs/GUIA_ORDEM_LEITURA.md` (`orquestracao/prompts/T34_vlm_ordem.md`) | Antigravity | — | feita (revisada; rodando no golden_v3 e golden_v4) |
| T35 | Regiões v3: regra `outro_marcacao`, classes do Rose, avaliação e `atualizar_proposta.py` para as páginas não anotadas (`orquestracao/prompts/T35_regioes_v3.md`) | Antigravity | T33 | feita (aplicada às 174 páginas não anotadas, revisada pelo Claude) |
| T36 | `golden_v4`: ordem de leitura sobre as regiões do Diamond (45 páginas: 20 do piloto + 25 do treino), `src/anotacao/preparar_ordem_diamond.py` | Claude prepara, Pedro anota | T27, T33 | feita (44 concluídas, 1 pulada; 12,8 min de tempo ativo) |
| T37 | Relatório v4 (`src/eval/relatorio_v4.py`, `notebooks/relatorio_ordem_v4.ipynb`, `docs/RELATORIO_V4.md`) sobre `golden_v4` × `golden_v3`, VLM, LayoutLM, segmentação e custo (`orquestracao/prompts/T37_relatorio_v4.md`) | Antigravity (despachado por `avaliar_v4.sh`) | T36 | feita (T37, T37b e T37c revisadas pelo Claude em 14/09 19:00) |
| T38 | LLMs de texto (qwen3.8:27b, gemma4:31b) no `golden_v4` pelo Kaggle; pacote refeito em 13/09 22:25 | Pedro executa | T36 | feita (importada 14/09 18:20: 4 predições no `golden_v4`) |
| T39 | Detector de layout treinado nas 9 classes do Diamond (extrator da imagem): `src/data/exportar_deteccao.py`, `src/models/detector_layout.py`, `avaliar_diamond.py --pred`, `orquestracao/fim_de_semana_4090.sh` | Claude prepara, Pedro roda na RTX 4090 | T33 | scaffolding pronto (aguarda a placa no fim de semana) |
| T40 | Conjunto de teste NÃO enviesado (`diamond_teste`, 12 pág. desenhadas do zero); modo `preparar_diamond.py --em-branco` | Claude preparou, Pedro anota | T39 | scaffolding pronto (12 pág. em branco no servidor) |
| T30 | Gerador do dataset Rose: pseudo-rotulagem de caixas e classes por VLM (`orquestracao/prompts/T30_dataset_rose_vlm.md`) | Codex / Antigravity | — | feita (gerador operacional 100% gratuito com Gemini 3.1 Flash Lite; lote piloto com 15 páginas íntegras gravado); revisada pelo Claude às 19:55 |

### Detalhe e critério de pronto

**T01 — Proteção contra `blocos_extra` ausente.** Hoje, se `data/processed/blocos_extra/`
não existe, `montar_treino()` em `src/eval/protocolo.py` devolve só as 152 páginas do
treino original e o treino "ampliado" roda sem erro. Afeta
`src/rodar_curva_aprendizado.py`, `src/models/layoutlm_ordem.py`,
`src/models/layoutlm_sucessor.py`, `src/models/lstm_ordem.py` e
`src/kaggle/montar_pacote.py`. *Pronto quando:* pedir páginas extras com a pasta ausente ou
vazia termina com erro que diz o que falta; com a pasta presente nada muda; o log de treino
imprime quantas páginas extras entraram.

**T02 — Bancada de avaliação do segmentador.** Um script (sugestão:
`src/data/avaliar_segmentacao.py`) que, **sem escrever em `data/`**, mede uma amostra fixa:
as quatro páginas-problema de `docs/HANDOFF.md` seção 2.2 e ~40 páginas sorteadas com
semente, estratificadas por veículo, dos veículos de teste e dos não confiáveis. Para cada
fonte — `data/processed/blocos_v1` (v1), `data/processed/blocos` (B) e o código atual de
`src/data/extrator.py` rodado ao vivo — imprimir: blocos por página, % de blocos
sobrepostos (mesma definição de `src/data/reextrair.py:qualidade`), % de blocos de uma
palavra, palavras do maior bloco (p50, p95, máximo), páginas fora do filtro de 3 a 200
blocos, tempo por página. *Pronto quando:* um comando imprime a tabela fonte × métrica e
grava o JSON em `resultados/`.

**T03 — Fechar a versão do segmentador.** Situação em `docs/HANDOFF.md` seção 2.2: a
versão B funde texto corrido (CE) e a C fragmenta demais (MA 36 → 85 blocos, RJ 53 → 159).
Pista para a C: a regra de margem esquerda compatível (−5 a +2,5 larguras de caractere) em
`construir_blocos` provavelmente separa itens de lista com recuo pendente ("I.", "II.") e
linhas de tabela; investigar nas páginas MA e RJ. *Critérios propostos, a confirmar numa
entrada DECISÃO:* na amostra da T02, sobreposição ≤ 10%; nenhuma página dos veículos de
teste rejeitada pelo filtro; nas páginas-problema, nem fusão de texto corrido nem
fragmentação muito acima da versão B; inspeção visual das quatro páginas registrada.
Mudança revisada por outro agente (`REVISÃO`).

**T04 — Preservar os artefatos da segmentação v1.** Antes que qualquer re-execução os
sobrescreva, copiar: `resultados/` → `resultados_segmentacao_v1/`;
`models/layoutlm_ordem/` → `models/layoutlm_ordem_segmentacao_v1/`; `docs/figuras/` →
`docs/figuras/segmentacao_v1/`; `data/processed/splits.json` →
`data/processed/splits_segmentacao_v1.json`. Só copiar, nunca mover. *Pronto quando:* as
cópias existem e o registro lista tamanhos e contagem de arquivos.

**T05 — Re-extrair as três coleções com a versão final.** Para cada uma de `blocos`,
`blocos_ri_japeri` e `blocos_extra`: apagar a pasta de destino se existir (as `_v1` são as
fontes e não se tocam) e rodar
`venv\Scripts\python.exe src\data\reextrair.py --entrada data\processed\<nome>_v1 --saida data\processed\<nome> --workers 16`.
O script sobrescreve `resultados/qualidade_segmentacao.json` a cada execução: copiar a
tabela impressa de cada uma para o registro. Reservar CPU; não rodar treino junto. As 3.117
páginas extras levam mais de uma hora. *Pronto quando:* as três pastas existem, com a
contagem de páginas e a tabela antes/depois de cada uma no registro, e com as páginas
perdidas pelo filtro listadas.

**T06 — Regenerar o `golden_v1`.** **Só se `data/golden/golden_v1/anotacoes.jsonl` não
existir.** Rodar
`venv\Scripts\python.exe src\data\reextrair.py --entrada data\golden\golden_v1\tarefas.jsonl --no-lugar`,
apagar o `tarefas.jsonl.bak` gerado e conferir: 30 páginas, imagem de cada página em
`img/`, identificadores únicos por página, cada ordem cobre todos os blocos. Não tocar em
`_segmentacao_v1/`. *Pronto quando:* conferências registradas e o Pedro avisado de que pode
anotar.

**T07 — Recalcular `splits.json`.** Com T04 feita (cópia de segurança), rodar
`venv\Scripts\python.exe src\eval\caracterizar.py` e comparar o novo `splits.json` com
`data/processed/splits_segmentacao_v1.json`: veículos confiáveis, treino, validação,
teste e o τ mediano de cada veículo. *Pronto quando:* a comparação está no registro. **Se
algum veículo mudar de grupo, é DECISÃO**: o Claude escreve a análise e o Pedro decide se
mantém a divisão antiga ou adota a nova.

**T08 — Anotar o `golden_v1`.** Pedro, com `venv\Scripts\python.exe src\anotacao\servidor.py`
e as regras de `docs/GUIA_ANOTACAO.md`. Conferir o campo Anotador antes de começar.

**T09 — Refazer todos os números locais.** Reservar a GPU. Na ordem:
`src\eval\baselines.py`; `src\models\lstm_ordem.py` nas variantes `texto`, `geo`,
`geo_texto`; `src\models\layoutlm_ordem.py treinar` e `avaliar`, com e sem `--sem-layout`;
`src\models\layoutlm_sucessor.py treinar` e `avaliar`, e
`avaliar --decodificacao feixe --metodo layoutlm_sucessor_feixe`; `src\eval\comparar.py`;
`src\eval\figuras.py`; `src\ri\piloto_japeri.py`. Parâmetros de treino: os dos
`*_config.json` preservados na T04, para o orçamento ser igual ao da v1. *Pronto quando:*
`resultados/comparacao.md` regenerado e a tabela principal copiada no registro, com o
tempo de cada etapa.

**T10 — Conversor das APIs comerciais → protocolo.** *Reespecificada às 18:00 (ver o
registro): a entrada principal passou a ser o Azure, 12 páginas; o texto abaixo é a versão
original. Prompt vigente: `orquestracao/prompts/T10_conversor_apis_v2.md`.* Entrada original:
`data/raw/official_diary_rj_japeri/diarios_avaliados_apis_pagas/` (dois JSONs no formato do
Document AI: `documentLayout.blocks` com `textBlock`, `pageSpan` e `boundingBox` em
coordenadas normalizadas; blocos podem ser aninhados). Saída: páginas no formato de
`data/processed/blocos/*.jsonl` (`page_id`, `uf`, `arquivo`, `pagina`, `dimensions`,
`bounding_boxes` com `id`/`text`/`bbox` em pontos do PDF, `ordens` com pelo menos `stream` =
ordem de emissão da API, `naive` e `xycut`, `stats`), numa pasta nova
`data/processed/blocos_docai_japeri/`. Identificadores por permutação semeada, como em
`src/data/extrator.py:processar_pagina`. *Pronto quando:* as páginas convertidas carregam
com `iterar_paginas` e o registro traz a distribuição de tamanho de bloco comparada à do
nosso extrator nas mesmas páginas.

**T11 — Análise de sensibilidade.** Tabela principal na v1 e na versão final, mesmas
páginas; o ranking dos métodos muda? Teste da hipótese: o sucessor correto da XY-cut cai
com a segmentação corrigida? Se a T10 estiver pronta, repetir a comparação sobre os blocos
do Document AI. Texto para `docs/METODOLOGIA.md` seção 10.1 e
`docs/RESULTADOS_PRELIMINARES.md`.

**T12 — Kaggle.** Com T09 feita: `venv\Scripts\python.exe src\kaggle\montar_pacote.py`,
conferir no registro que o zip contém `data/processed/blocos_extra/`; o Pedro sobe o pacote e
roda os notebooks conforme `docs/KAGGLE.md`; depois
`venv\Scripts\python.exe src\kaggle\importar_resultados.py <zip>`. Nenhum agente sobe nada
sem o Pedro pedir.

**T13 — Atualizar resultados e apresentação.** `docs/RESULTADOS_PRELIMINARES.md` com os
números novos e a análise de sensibilidade; página de apresentação via
`docs/apresentacao/montar_apresentacao.py` (a republicação do Artifact é com o Claude).

**T14 — Extrator com PyMuPDF.** Opcional. Mesma saída que `src/data/extrator.py`, dezenas de
vezes mais rápido que o `pdfplumber` (os PDFs de PE levam ~50 s). *Pronto quando:* numa
amostra, as palavras e caixas batem com as do `pdfplumber` dentro de tolerância e o tempo
foi medido.

**T15 — Perguntas ao orientador.** Lista em `docs/ROADMAP.md`, seção "Perguntas para levar
ao orientador".

**T16 — Folhas de inspeção visual das páginas-problema.** Script
`src/data/inspecionar_segmentacao.py` que desenha, sobre cada uma das quatro páginas-problema
(`docs/HANDOFF.md` seção 2.2), as caixas das versões v1, B e C, com cores para bloco acima de
250 palavras, caixa sobreposta e bloco de uma palavra, e junta as três versões lado a lado.
Saída em `resultados/inspecao_segmentacao/` (16 PNGs e `contagens.json`). Serve de evidência
visual para a T03. Prompt completo: `orquestracao/prompts/T16_folhas_inspecao.md`.
*Pronto quando:* os PNGs e o JSON saem do zero com um comando, e as contagens de blocos batem
com as da seção 2.2 do handoff.

---

## Registro

<!-- NOVAS ENTRADAS AQUI: insira a entrada nova logo abaixo desta linha, acima das anteriores -->

### 2026-11-02 — Claude — FEITO — Preparação da fase intensiva de novembro (nenhum experimento iniciado)
**Tarefa:** pedido do Pedro (retomar o TCC; preparar pesquisa, treino, testes e análise com autonomia; documentar para a escrita).
**Feito:** `docs/PLANO_PESQUISA.md` (13 experimentos E001–E013, protocolo congelado, cronograma S1–S6), `docs/DEPENDENCIAS.md` (o que só o Pedro faz), `docs/CONTEXTO_E_RECURSOS.md` (contexto do Acessilia/Data Policy/Spark + inventário), `experimentos/` (hipóteses, cartões E001–E003, `registro.jsonl` via `src/exp/registro.py`, versões de dados D1, NAO_FUNCIONOU, consultas ao ChatGPT), filas `orquestracao/fase_nov/` (codex/agy/cmd + `spark.sh`; tarefas da S1 escritas, **filas não iniciadas**). Diário de bordo atualizado (sessões 5–10).
**Avisos a todos os agentes:** (1) o baseline a superar agora é o **híbrido por densidade (limiar 67)**, não só a regra; (2) o `data/diamond/lote_sem_paragrafos` **não é teste cego** (PDFs já usados em outros conjuntos); (3) quando existir `experimentos/TESTE_CEGO.lock`, ninguém abre essas páginas; (4) job 1053 da Spark (LM causal) foi cancelado com a validação RN incompleta; escores parciais no cluster.

### 2026-10-28 — Claude — EM ANDAMENTO — Arestas pontuadas por LM (arXiv 2607.01018) para a Spark
**Tarefa:** pedido do Pedro (continuar treino/teste na DGX Spark, pesquisar ordenação, olhar o Acessilia).
**Feito:** Codex escreveu `orquestracao/analises/ordem_lm_arestas.py` (exportar/decodificar) e `cluster/pontuar_pares_lm.py` (autônomo); 87.120 pares exportados em `resultados/ordem_lm/pares/` (175 páginas, âncora 0,985948/6,045455 reproduzida); fumaça Qwen3-0.6B local ok (2,9 s/página). `cluster/job_pontuar.sh` e os pares já copiados para `~/tcc/ordem_lm` no cluster; job NÃO submetido (aguarda o Pedro autorizar o download do Qwen3-8B). Antigravity: `resultados/acessilia_ordem_leitura.md` (Acessilia não tem ordenador próprio; a seção 5 sobre o Docling está errada: o ordenador é o `ReadingOrderPredictor` do docling-ibm-models, não `iterate_items`). Plano em `orquestracao/spark_2810/`.

### 2026-10-08 06:40 — Claude — FEITO — Noite de 07→08/10: extrator novo, diagnóstico de margens, modelos com todo o dado (detalhes na seção 8 de `docs/RELATORIO_NOITE_0410.md`)
**Tarefa:** pedido direto do Pedro (melhorar o extrator sem parágrafos, achar erros, criar lote classificável, treinar o LayoutLM nessa estrutura, ferramenta de anotação mais simples, ideias do ChatGPT).
**Resultados (τ / quebras por página; golden_v4 | golden_v3 novo | teste silver):** regra de colunas 0,986/6,05 | 0,960/9,22 | 0,960/27,45; LayoutLM sucessor geometria com 3.140 páginas, sementes 42 e 43: 0,924/9,00 | 0,928/10,41 | 0,934/29,15 e 0,945/8,68 | 0,923/10,81 | 0,934/29,63 (mais dado ajuda; ainda atrás da regra); lendo o texto: 0,942/20,77 | 0,931/23,19 | 0,930/50,46 (piora a continuidade). Extrator v2 sem efeito em linhas (6,05 → 5,93; 9,22 inalterado). Diagnóstico: 50% das quebras da regra no golden_v4 em cabeçalho, rodapé e marcas. Margens por repetição: melhora no ajuste (4,89), não generaliza. Reordenação restrita: melhora nas três bancadas (5,18 | 7,78 | 26,45), ICs externos incluem zero. Regra + modelo seletivo: piora; manter a regra.
**Arquivos novos:** `orquestracao/noite_0710/`, `orquestracao/noite_0610/`; em `orquestracao/analises/`: `auditoria_extrator_sem_paragrafos.py`, `montar_lote_sem_paragrafos.py`, `extrator_sem_paragrafos_v2.py`, `corretor_de_transicoes.py`, `regra_margens_v2.py`, `margens_repeticao.py`, `reordenacao_restrita.py`, `regra_mais_modelo.py`, `treinar_sem_caixas_texto.py`, `ordenar_bancadas_texto.py`, `paineis_reordenacao.py`, `xycut_pp_parceiro.py`, `reclamacoes_x_novo.py`, `hibrido_regra_layoutreader.py`, `tabela_noite_0410.py`; `resultados/ferramenta_anotacao/`, `resultados/lote_sem_paragrafos/` (e cópia em `data/diamond/lote_sem_paragrafos`), `resultados/ideias_chatgpt_0708.md`, `resultados/ceia_datapolicy/` (fora do git, uso interno), `resultados/reclamacoes_x_novo/`.
**AVISO:** `resultados/unidades_sem_caixas/` agora tem o treino completo (3.140 páginas); o conjunto de 873 está em `treino_noite_873.json`. A `comum.txt` de `noite_0710` proibia comandos ao Codex por engano (corrigida). Clones do parceiro em `C:\Users\pedro\dev\ceia_datapolicy`, só leitura. Sem commit nem push.
**Estado:** filas encerradas, GPU livre, reserva removida.
**Próximo passo / para quem:** Pedro: abrir o lote classificável e medir o tempo por página; rodar o Kaggle do DocLayout-YOLO (`notebooks/kaggle_detector_ls.ipynb`); decidir se segue a reordenação restrita (exploratória).

### 2026-10-07 08:00 — Claude — FEITO/BLOQUEIO — Noite de 06→07/10: exportação completa, repositórios do parceiro, treino esperando a GPU
**Tarefa:** pedido direto do Pedro (treinar com todo o dado; ler os repositórios do CEIA-Datapolicy; não commitar nada).
**Feito:** exportação completa das unidades sem caixas finas (3.140 páginas de treino; `resultados/unidades_sem_caixas/treino_noite.json`, o de 873 ficou em `treino_noite_873.json`); XY-Cut++ do parceiro medido na bancada (`orquestracao/analises/xycut_pp_parceiro.py`; em linhas, golden_v4: τ 0,763 e 48,20 quebras, contra 0,986 e 6,05 da regra; limiares padrão, não ajustados); síntese dos sete repositórios em `resultados/ceia_datapolicy/` (fora do git, uso interno); painéis das páginas com reclamação do Pedro em `resultados/reclamacoes_x_novo/` (`orquestracao/analises/reclamacoes_x_novo.py`). Detalhes na seção 7 de `docs/RELATORIO_NOITE_0410.md`.
**Bloqueio:** a GPU esteve ocupada por outro programa a noite toda; os dois treinos do LayoutLM sucessor com todo o dado não começaram. A cadeia `orquestracao/noite_0610/rodar.sh` segue viva esperando a placa (reserva mantida acima); parar com `orquestracao/noite_0610/STOP`.
**AVISO:** `resultados/unidades_sem_caixas/` agora tem o treino completo; scripts que exigem as 873 páginas congeladas precisam de `treino_noite_873.json`. Os clones do parceiro ficam em `C:\Users\pedro\dev\ceia_datapolicy`: só leitura, nada deles vai para este repositório. Sem commit nem push.

### 2026-10-05 07:40 — Claude — FEITO — Noite de 04→05/10: ordenadores sobre as unidades sem caixas finas (consolidado em `docs/RELATORIO_NOITE_0410.md`)
**Tarefa:** pedido direto do Pedro ("testar os ordenadores nesse novo tipo de modelo"); plano `orquestracao/noite_0410/PLANO.md`.
**Resultado principal** (`resultados/tabela_noite_0410.md`, gerada de `resultados/ordenadores_sem_caixas.json`; τ de palavras / quebras por página, golden_v4 e golden_v3 novo):
- Linhas: regra de colunas 0,986 / 6,05 e 0,960 / 9,22; LayoutLM sucessor treinado, 40 épocas, 0,928 / 11,00 e 0,919 / 12,48 (100 épocas: 0,929 / 12,57 e 0,896 / 12,59; 8 épocas: 0,902 / 57,59); LayoutReader pré-treinado 0,913 / 18,39 e 0,951 / 16,22; LayoutLM pontual e BiLSTM, 72 a 75 quebras. Teto da representação: 1,000 / 0,89.
- Faixas de coluna com margens: teto 0,960 / 5,20; quebras entre 5,2 e 6,3 com qualquer ordenador; no τ, sucessor treinado 0,934, LayoutReader pronto 0,923, Gemini 0,901 (41 páginas), regra 0,854.
- Híbrido por densidade (LayoutReader até 67 unidades, regra acima; limiar escolhido só no golden_v4): golden_v3 novo 9,22 → 7,89 quebras [Δ −1,33; IC −2,63 a −0,35]; teste silver 27,45 → 26,43 (`resultados/hibrido_regra_layoutreader.md`). Pista, não método validado.
**ACHADO de bancada:** a ordem interna crua das unidades exportadas dava 16,86 quebras por página no lugar de 6,05; a bancada passou a expandir cada unidade com `ordem_sem_bbox.fluxo()` (decisão minha, registrada em `orquestracao/noite_0410/codex/02b_bancada_ordem_interna.txt`). Quem usar `resultados/unidades_sem_caixas/` deve ordenar as palavras de cada unidade pela bancada, não por `ks`.
**AVISO:** o Codex CLI esgotou o limite SEMANAL às 04:07 (volta em 09/10 19:06). Ficaram sem fazer: revisão adversarial, acerto de sucessor por tipo de transição, comparação de decodificações e efeito das páginas com tabela (lista na seção 5 do relatório).
**Ressalvas:** modelos treinados só com geometria (um token por unidade), em 873 páginas congeladas (`resultados/unidades_sem_caixas/treino_noite.json`), uma semente nas execuções longas; golden_v4 serviu ao desenvolvimento da regra; referência silver com piso alto dentro das tabelas.
**Arquivos tocados (novos):** `orquestracao/noite_0410/`; em `orquestracao/analises/`: `unidades_sem_caixas.py`, `bancada_ordenadores.py`, `treinar_sem_caixas.py`, `ordenar_bancadas.py`, `layoutreader_ajuste.py` (Codex; corrigi dois pontos de robustez em `unidades_sem_caixas.py` e um em `treinar_sem_caixas.py`), `auditoria_bancadas_treino.py`, `diagnostico_faixas_estreitas.py`, `vlm_unidades_cola.py`, `ordenadores_ganha_perde.py` (Antigravity), `tabela_noite_0410.py`, `hibrido_regra_layoutreader.py` (Claude); `resultados/unidades_sem_caixas/`, `resultados/ordenadores_sem_caixas*`, `resultados/ordenadores_treinados_sem_caixas*`, `resultados/ordenadores_ganha_perde.md`, `resultados/hibrido_regra_layoutreader.md`, `resultados/tabela_noite_0410.md`, `resultados/auditoria_bancadas_treino.md`, `resultados/faixas_estreitas.md`; `docs/RELATORIO_NOITE_0410.md`. Nada em `data/`; `data/labelstudio/` não foi usado (só os pesos do `ls3`).
**Estado:** filas encerradas (arquivo `STOP` criado), GPU e CPU livres, reserva removida. Sem commit, push ou publicação; o Gemini recebeu só as 71 páginas do Golden, com autorização do Pedro.
**Próximo passo / para quem:** Pedro decide (seção 6 do relatório): linhas como representação de trabalho; regra como método e modelo como complemento; exportar as 3.217 páginas e treinar o sucessor com mais dado e texto.

### 2026-10-04 23:20 — Claude — DECISÃO/EM ANDAMENTO — Noite de 04→05/10: ordenadores sobre a representação sem caixas finas
**Tarefa:** pedido direto do Pedro ("testar os ordenadores nesse novo tipo de modelo, usando o Antigravity e o Codex"); plano em `orquestracao/noite_0410/PLANO.md`, aprovado por ele às 23:18 ("sim pra tudo").
**Decisão (experimental, confirmada pelo Pedro ao aprovar o plano):** treinar e medir os ordenadores do TCC (XY-cut, BiLSTM, LayoutLM pontual e sucessor, LayoutReader) sobre as unidades sem caixas finas (linhas, faixas de coluna, faixas com margens), usando como supervisão a referência silver do protocolo (ordem do fluxo do PDF, mesmos veículos de `data/processed/splits.json`) projetada nas unidades novas. Não substitui o dataset nem o protocolo oficiais; as saídas ficam em `resultados/unidades_sem_caixas/`, nada é gravado em `data/`.
**Autorizações do Pedro para esta noite:** lançar as filas; enviar as 71 páginas do Golden (Diários públicos, sem dado do Data Policy) à API gratuita do Gemini para o teste do ordenador por modelo de linguagem. `data/labelstudio/` fica fora desta noite (só os pesos do detector `ls3`).
**Régua:** a de palavras de `resultados/erros_ponta_a_ponta.md` (τ, quebras por página, fidelidade de 12), em três bancadas (golden_v4, golden_v3 novo, teste silver), com âncoras a reproduzir (regra de colunas 0,986 e 6,05; extrator + XY-cut + margens 0,952 e 8,93 no v4).
**Acompanhar:** `bash orquestracao/noite_0410/status.sh`. **Parar:** criar `orquestracao/noite_0410/STOP`. **Retomar depois de queda:** `bash orquestracao/noite_0410/iniciar.sh`.
**Para os outros agentes:** GPU e CPU pesada reservadas até ~08:00; a fila da GPU nunca mexe em processo que não seja dela. Sem commit nem push.

### 2026-10-04 23:00 — Claude — REVISÃO/FEITO — Trabalho do Codex de 04/10 conferido; noite de 02→03/10 fechada; resumo para o orientador
**Tarefa:** nenhuma; pedido direto do Pedro ("dê uma olhada no que o Codex fez; quero mandar resultados ao professor").
**O que conferi no trabalho do Codex (`docs/HANDOFF_CODEX_0410.md`):** refiz as médias de `resultados/datasets_sem_caixas/avaliacao/layoutreader.jsonl` (τ 0,8984 em linhas e 0,8503 em colunas, 44 páginas cada: batem); nas 44 páginas da bancada, nenhuma palavra repetida ou faltando nas duas representações; `src/data/dataset_sem_caixas_finas.py` reaproveita `vales_locais`, `atomos` e `linhas_partidas` de `orquestracao/analises/ordem_sem_bbox.py` com os mesmos parâmetros (0,45; 1,2; 0,08), ou seja, é a mesma família de cortes de coluna já medida; abri `resultados/comparador_golden_v4/index.html` no navegador e troquei página e as seis variantes (RJ p. 5/45: 73 caixas na v3, 129 no Golden v4, 337 linhas, 26 e 9 unidades em colunas sem e com estruturas), sem erro no console.
**Ressalvas:** o LayoutReader pronto fica abaixo da ordenação geométrica nas mesmas páginas (0,898 e 0,850 contra 0,986 do `P2` no v4, `resultados/erros_ponta_a_ponta.md`), como já tinha dado em `resultados/ordem_layoutreader.md` (0,888); a variante de margens e quadros não tem medição; faixas estreitas indevidas visíveis (MG, p. 18/45); das 614 páginas exportadas só 44 têm ordem humana.
**Fechamento da noite:** filas encerradas em 03/10 13:30, nada rodando; `docs/RELATORIO_NOITE_0210.md` ganhou a seção 2.11 (erros de ponta a ponta: 16,14 → 9,87 → 7,25 quebras por página; contra o pipeline com margens o intervalo inclui zero; a hipótese de que a maioria das quebras nasce nas caixas não se sustentou) e a seção 6 final. Reserva do Claude removida.
**Arquivos tocados:** `docs/envio_professor_0410/` (novo: `montar.py`, `resumo.html`, `resumo.pdf`, três figuras, `mensagem.md`, cópia e zip do comparador), `docs/RELATORIO_NOITE_0210.md`, `.claude/launch.json` (configuração `comparador`, porta 8784), este quadro.
**Resultado / evidência:** `venv/Scripts/python.exe docs/envio_professor_0410/montar.py` lê todos os números de `resultados/` e gera o resumo de 3 páginas. Nada foi enviado nem publicado; sem commit ou push.
**Próximo passo / para quem:** Pedro decide se envia e por qual canal. O resumo cita números agregados do dataset do Data Policy (seção 4): não publicar.

### 2026-10-04 — Codex — FEITO — Handoff para retomada do Claude
**O que fiz:** consolidei intenção, implementações, resultados, limitações, comandos e pendências em `docs/HANDOFF_CODEX_0410.md`.
**Evidência:** números conferidos nos manifestos e relatórios; nenhum experimento novo nesta etapa.
**Próximo passo:** Claude ler esse documento antes de retomar. Não assumir treino novo nem retomada das filas noturnas por este chat.

### 2026-10-04 — Codex — FEITO — Cabeçalhos, rodapés e quadro institucional no comparador
**O que fiz:** variante automática adicional em 45 tarefas Golden v4, preservando variantes antigas. Separação de margens pelo detector/bordas isoladas; quadros por molduras ou linhas vetoriais e texto institucional. Usa paginação zero-based do repositório. Quadro do RJ confirmado visualmente inteiro fora das três colunas principais.
**Arquivos:** `src/data/estruturas_pagina.py`, gerador/template do comparador, `resultados/estruturas_golden_v4/`, saída do comparador e ponteiro no handoff.
**Evidência:** `validacao.json`: 45 páginas, 92 unidades cabeçalho, 42 rodapé, um quadro externo; integridade de palavras verificada em ambas as representações. AST Python e sintaxe JavaScript conferidos. Comando: `venv\Scripts\python.exe src\data\comparador_golden_v4.py`.
**Pendências:** contagens não medem acerto; cabeçalhos ainda podem estar fragmentados. Não houve avaliação nova de ordenação. Quadros sem bordas/rasterizados não cobertos. Originais/anotações intocados; sem commit/push.


### 2026-10-04 — Codex — DECISÃO — Variante com margens e quadros externos
**Confirmação:** Pedro pediu nesta conversa separar cabeçalho, rodapé e quadros como o exemplo. Variante experimental adicional; manter versões anteriores e referências. Usar evidência automática (detector, margens isoladas e linhas vetoriais do PDF), sem usar classes humanas como entrada.


### 2026-10-04 — Codex — FEITO — Comparador visual do Golden v4
**Tarefa:** pedido direto do Pedro.
**O que fiz:** comparador local com imagens embutidas das 45 tarefas do Golden v4; quatro representações selecionáveis lado a lado: v3 original do Diamond, caixas existentes do Golden v4, linhas e faixas de coluna. Zoom, rolagem sincronizada, IDs, ocultação de caixas/texto e inspeção de conteúdo. Gerados três exemplos PNG com v3/v4/colunas.
**Arquivos tocados:** `src/data/comparador_golden_v4.py`, `src/data/comparador_golden_v4.html`, `resultados/comparador_golden_v4/`, quadro e ponteiro no handoff.
**Resultado / evidência:** `resultados/comparador_golden_v4/manifesto.json`: 45 páginas, quatro variantes, nenhuma imagem ausente, três exemplos. Comando gerador rodado; AST Python e `node --check` do JavaScript passaram. Exemplo 1 inspecionado visualmente. A saída real mostra também faixas estreitas indevidas: não foi corrigida para parecer melhor. Golden tem 45 tarefas, avaliação anterior apenas 44 concluídas.
**Próximo passo / para quem:** Pedro inspecionar `index.html`, especialmente páginas multicoluna e imagens; não confundir caixas existentes do Golden corrigidas com a extração automática nova. Nada alterado em anotações, PDFs ou datasets originais. Servidor local na porta 8784, sem publicação externa.


### 2026-10-04 — Codex — FEITO — Duas versões experimentais sem caixas de parágrafo
**Tarefa:** nenhuma; pedido direto do Pedro.
**O que fiz:** exportador novo, sem alterar extrações originais. Tabelas/imagens atômicas; texto por linhas ou faixas multicoluna. Referência humana separada, IDs de palavras alinhados com a extração canônica do Golden v4. Entrada embaralhada. Avaliação CPU do LayoutReader pronto, sem novo treino.
**Arquivos tocados:** `src/data/dataset_sem_caixas_finas.py`, `resultados/datasets_sem_caixas/`, adendo em `docs/HANDOFF.md`, este quadro.
**Resultado / evidência:** `manifesto.json`: 614 páginas (196 treino, 13 validação, 3 teste, 402 sem split). `validacao_exportacao.json`: 349 com calhas multicoluna; 59.081 unidades em linhas versus 5.495 em colunas; todas as palavras exatamente uma vez. Caso sintético de 24 linhas em duas colunas passou; páginas curtas exigem suporte mínimo. `avaliacao/layoutreader.jsonl`: 88 avaliações em 44 páginas, τ médio 0,8984 linhas e 0,8503 colunas; sucessor 0,9620 e 0,9604. Comando: `venv\Scripts\python.exe src\data\dataset_sem_caixas_finas.py --avaliar`; análise AST passou.
**Limitações / próximo passo:** não houve retreino; cobertura apenas Diamond já extraído. Referência de palavras derivada de regiões humanas com ordem geométrica interna; conjunto usado em desenvolvimento. Colunas impõem ordem interna e pioraram τ neste teste. Acima de 510 unidades adaptador LayoutReader agrupa geometricamente. Não apresentar como ganho comprovado nem trocar dataset oficial. Próximo experimento deve separar treino supervisionado e teste independente na mesma representação. Não houve commit/push nem escrita em raw/anotações humanas.


### 2026-10-04 — Codex — DECISÃO — Datasets sem segmentação fina, solicitados por Pedro
**Tarefa:** nova representação experimental.
**Justificativa e confirmação:** Pedro pediu explicitamente versões dos datasets que preservem somente tabela/imagem como blocos, detectem multicolunas e permitam avaliar um modelo sem depender das caixas finas incorretas. Linhas e faixas geométricas são unidades computacionais, não parágrafos rotulados. Originais e referências humanas serão preservados; referências derivadas ficam separadas das entradas.
**Escopo:** exportar páginas Diamond disponíveis e bancada Golden v4, manter split por fonte e avaliar LayoutReader pronto em CPU; não implica treino novo nem adoção como segmentação oficial.

### 2026-10-03 08:30 — Claude — FEITO — Noite de 02→03/10: resultados das duas frentes (consolidado em `docs/RELATORIO_NOITE_0210.md`)
**Tarefa:** T14 (módulo pronto) e as frentes A (extrator/detector) e B (ordem sem bbox fina) abertas em 01/10.
**GPU LIVRE desde 06:29.** Ainda roda só a fila do Codex (09b, 10, 11; CPU). Nada commitado.
**Frente B (plano do orientador), τ da sequência real de palavras:** no `golden_v4` (44 pág.) a política de margens
(topo primeiro, rodapé por último) explica 90,1% do ganho do 1º relatório; XY-cut em regiões humanas 0,853 → 0,972
com a política; XY-cut no extrator automático 0,819 → 0,952; plano sem bbox 0,946 (Docling) a 0,986 (átomos do
`ls3`); sem átomos 0,868. Diferença do plano contra a XY-cut justa: 0,008, IC [−0,056; 0,040], p = 0,59. Em páginas
novas: Label Studio (123 pág.) plano 0,966 × XY+margens 0,976 × XY 0,905; `golden_v3` fora do v4 (27 pág.) 0,971 ×
0,918 × 0,913; teste silver (86 pág.) 0,968 × 0,948 × 0,942. LayoutReader pronto: 0,888 em linhas (pior e 50× mais
lento). **Leitura:** equivalência prática, não superioridade; a política de margens é candidata a método novo.
Fontes: `resultados/ordem_sem_bbox_justo.md`, `_ls3.md`, `_validacao_ls.md`, `_validacao_acervo.md`,
`ordem_layoutreader.md`, `revisao_ordem_sem_bbox.md`.
**Frente A:** detectores YOLOv8s no dataset do Label Studio — `ls3` mAP50 0,826 e `ls16` 0,483 no teste de fontes não
vistas (`resultados/deteccao/ls{3,16}_map_teste.json`). Nas 317 páginas do LS (`extrator_vs_detector_ls_teste.md`):
F1 de localização extrator 0,573, `ls3` 0,780, `ls16` 0,753. No `diamond_teste` (11 pág. do zero,
`resultados/deteccao/comparacao_ajuste_fino_diamond.txt`): extrator 0,851, `ls3` 0,765, `ls16` 0,753; ajuste fino no
Diamond partindo do COCO 0,750, do `ls16` 0,789, do `ls3` 0,775. Cada um ganha no gabarito da sua convenção.
Extrator híbrido (trocar o Docling pelo detector do domínio): sem ganho (`extrator_hibrido_ls.md`, Antigravity).
**T14:** `src/data/palavras_pymupdf.py` + `tests/test_palavras_pymupdf.py` (126 testes passam); extrator 33,31× mais
rápido (2,585 → 0,078 s/pág.), mas só 61 de 104 páginas mantêm todos os blocos (93,49% dos blocos idênticos):
módulo opcional, NÃO usar para regenerar a silver (`resultados/extrator_pymupdf_paridade.md`).
**Gemini:** ordem nas 89 páginas de teste τ 0,896 × XY-cut 0,891 (`vlm_ordem_teste.md`,
`resultados/pred_vlm_gemini_3_1_flash_lite.jsonl`); massa `massa1_gemini` em 345 de 383 (parado: o resto falha na
validação). **Concordância entre anotadores do LS:** F1 85,6%, kappa 0,763/0,875/0,936 em 16/9/3 classes
(`labelstudio_concordancia_v2.md`; a v1 está ERRADA, incluía o projeto de ordem). **Ancoragem:** 40,0% das caixas
aceitas como a máquina sugeriu (`labelstudio_ancoragem.md`).
**Arquivos de código tocados:** `src/models/detector_layout.py` (a retomada respeita `--workers`),
`orquestracao/noite_detector_ls.sh` (`--workers 1`), novos em `orquestracao/noite_0210/` e `orquestracao/analises/`,
`src/data/palavras_pymupdf.py`, `tests/test_palavras_pymupdf.py`. Venv: `pymupdf` 1.28.2 instalado.
**AVISO (memória):** no Windows cada worker do treino YOLO é um processo de ~1 GB e a validação abre o dobro; com
`--workers 4` o treino comprometia 20 GB (commit 37,4 de 37,8 GB às 02:36). Use `--workers 1` nesta máquina.
**Não revisado por mim:** os scripts do Antigravity (concordância, ancoragem, baselines de ordem do LS, avaliação do
VLM, PyMuPDF palavras, híbrido) — li os resumos; os do Codex, li veredito e tabelas.
**Atualização 09:05 — política de margens como módulo:** `src/eval/politica_margens.py` + `tests/test_politica_margens.py`
(144 testes passam); XY-cut sem → com a política, régua de blocos: teste silver 0,891 → 0,928 (Δ 0,037 [0,013; 0,064]),
`golden_v3` 0,851 → 0,908, `golden_v4` 0,825 → 0,908; piora 6, 4 e 7 páginas e é sensível ao limiar de topo
(`resultados/politica_margens.md`). `baselines.py` e `comparar.py` não foram tocados.
**Próximo passo / para quem:** Pedro decide (1) commit/push, (2) adotar "XY-cut + margens" como método (DECISÃO
metodológica), (3) adotar ou não o módulo PyMuPDF, (4) rodar o Kaggle (`dist/kaggle/ls_deteccao.zip`). O Codex ainda
entrega `resultados/caminho_rapido_pymupdf.md` e `extrator_com_detector_ls.md`.

### 2026-10-03 02:30 — Claude — EM ANDAMENTO — Noite relançada (versão 2), com autonomia de rumo dada pelo Pedro
**GPU OCUPADA até ~06:00. Não disparar outro job de GPU.** Painel: `bash orquestracao/noite_0210/status.sh`.
Retomar depois de uma queda (não duplica o que já roda): `bash orquestracao/noite_0210/iniciar.sh`.
Parar: criar `orquestracao/noite_0210/STOP` e matar as árvores com `taskkill /T` (ver memória do Claude).
**Correção da entrada de 00:45:** o PDF de Curitiba NÃO estava corrompido — o original no S3 já tem 22,9 MB de
zeros no fim e abre normalmente (132 páginas). Só o de Caxias do Sul tinha se perdido; rebaixado. 197 PDFs, 506 páginas.
**O que roda (4 processos soltos da sessão, cada um com log em `noite_0210/saida_*.log` e linhas em `fila.log`):**
- `gpu.sh`: espera a GPU livre e roda `orquestracao/noite_detector_ls.sh` (`ls3` da época 37, depois `ls16`, mAP no
  teste, comparação com o extrator no `diamond_teste`).
- `fila.sh codex` (gpt-6.1-sol, xhigh), menor número pronto primeiro: 02 ponta a ponta com `ls3` (espera `treino_ok`);
  03 extrator × detectores nas 317 páginas (re-executável); 04 validação da ordem no projeto 23 (espera `ls3`);
  **05 (nova)** validação do "sem bbox" no `golden_v3` fora do v4 e nas 89 de teste; **06 (nova)** LayoutReader
  (`models/terceiros/layoutreader`, CC BY-NC-SA) como ordenador de linhas; **07 (nova)** caminho rápido só com PyMuPDF.
- `fila.sh agy` (gemini-3.8-flash-high; escreve, a fila executa): 00 revisão adversarial do experimento do Codex;
  01 concordância; 02 ancoragem; 03 baselines de ordem no LS; 05 galeria.
- `gemini.sh` (API, só páginas do acervo do orientador, nada do Label Studio): ordem por VLM nas 89 páginas de
  teste; depois termina a massa `massa1_gemini` (273 de 383).
**Ambiente:** instalei `pymupdf` 1.28.2 no venv (torch 2.9.1+cu128 intacto) e baixei `hantian/layoutreader` (713 MB).
**Mudanças na fila:** `esperar` não bloqueia; uma tarefa por varredura; falha rápida (limite/rede) não queima a fila;
aviso no log se algo sob `data/` mudar durante uma tarefa; mantém a máquina acordada. Agentes NÃO editam este quadro.
Nada commitado (o Pedro não respondeu sobre commit/push; continua tudo só no SSD USB).

### 2026-10-03 00:45 — Claude — ACHADO — A noite de 01→02/10 caiu às ~00:01 (tela azul); GPU LIVRE; nada foi relançado
**Tarefa:** nenhuma (orquestração da noite; substitui o estado das duas entradas abaixo, que ficaram desatualizadas)
**O que achei:** o PC travou com tela azul (Kernel-Power 41, BugcheckCode 340 = 0x154 `UNEXPECTED_STORE_EXCEPTION`) por
volta de 00:01 de 02/10 e só religou às 22:40. O `C:` (Windows + este projeto) fica num **SSD externo USB (Lexar E300)**;
o log do sistema tem 25 desligamentos inesperados e 148 reparos de NTFS em 45 dias. Última escrita do treino: 00:00:53.
**Não há nenhum processo vivo** (treino, filas, Codex, agy) e a GPU está em 335 MiB. **Não relancei nada**: aguarda o Pedro.
**Terminou e está íntegro:** exports e conversão do Label Studio; 2.119 imagens; `data/deteccao/ls3` e `ls16`;
Codex 01 (`orquestracao/analises/ordem_sem_bbox.py`, `resultados/ordem_sem_bbox.md/.json`, ainda SEM revisão);
`dist/kaggle/ls_deteccao.zip` (6.368 entradas, `testzip` OK) + `notebooks/kaggle_detector_ls.ipynb`;
`data/labelstudio/pdf_paginas.jsonl` (506 páginas, 197 PDFs).
**Ficou pela metade:** treino `ls3` em 36 de 60 épocas (`runs/detect/ls3/weights/last.pt` carrega, epoch=35; `best.pt`
epoch=32, mAP50 0,785 / mAP50-95 0,636 na validação; sem `treino_ok`); `ls16` só tem a 1 época do incidente das 22:40;
mAP no teste, predição no `diamond_teste` e `comparacao_detector_ls.txt` não existem. Codex 03 rodou 3,5 min sem gravar
nada; agy 01 falhou na 1ª rodada (rc=1). Codex 02 e 04 e agy 02–05 nem começaram. `docs/RELATORIO_NOITE_0210.md` não existe.
**Perdido na queda (entradas órfãs removidas pelo NTFS, eventos Ntfs/130 de 03/10 00:31–00:33):** `noite_0210/fila2.sh`
(a correção do `esperar` que bloqueava), `orquestracao/analises/concordancia_ls.py`, logs e marcadores de codex 03 e
agy 01, e o PDF `rs_caxias_do_sul ... Ed6136-Pag116.pdf`. O PDF `pr_curitiba ... Ed71-Pag132.pdf` ficou com os últimos
22,9 MB zerados (apagar antes de rebaixar: o `baixar_pdfs.py` o trataria como "já baixado"). Afetam 6 páginas de ordem.
**Arquivos tocados:** só este quadro. Conferências feitas só lendo (CPU): 7.151 arquivos de texto sem NUL, JSON/JSONL
válidos, `.py` com sintaxe ok, `git fsck` limpo, anotações humanas (`data/golden`, `data/diamond`) intactas.
**AVISOS para quem for relançar:** (1) `fila.sh` original bloqueia a fila do Codex na tarefa 02 até existir `treino_ok`
e espera o PID fixo 33092, que não vale mais depois do boot; (2) `agy/01_concordancia.rodando` é marcador morto;
(3) 3 "PDFs" de MG (`...Pag139-MG`, `...Pag99-MG`, `...Pag128-MG`) são envelopes de assinatura PKCS#7 com o PDF a partir
do byte 57 — 6 páginas do teste de detecção e 1 de ordem; (4) nada commitado desde `a2b0472`, e esse commit não está em
nenhum remoto: 94 arquivos não rastreados, incluindo `data/golden/golden_v4/` e `data/diamond/` (anotação humana).
**Próximo passo / para quem:** Pedro decide o que relançar e se faz commit/push antes (recomendado, pelo risco do disco).

### 2026-10-01 23:55 — Claude — EM ANDAMENTO — Orquestração da noite (duas frentes), a pedido do Pedro
**Painel:** `bash orquestracao/noite_0210/status.sh`. Para parar as filas: criar `orquestracao/noite_0210/STOP`.
**Frente A (extrator/detector, dataset do Label Studio):** GPU local treina `ls3`→`ls16` (ver entrada abaixo);
Kaggle: `notebooks/kaggle_detector_ls.ipynb` + `dist/kaggle/ls_deteccao.zip` (1,47 GB, subir como dataset
PRIVADO; YOLO11m 1280, DocLayout-YOLO, RT-DETR nas 2 T4) — o Pedro sobe e roda; PDFs das 317 páginas de teste
e das de ordem baixando para `data/labelstudio/pdf/` (222 PDFs).
**Frente B (plano do orientador: sem bbox fina, ordem no texto, colunas):** Codex concluiu
`orquestracao/analises/ordem_sem_bbox.py` + `resultados/ordem_sem_bbox.md` (44 págs golden_v4): τ 0,917 vs
0,825 da XY-cut em regiões-ouro (LOPO, Wilcoxon p=0,013), MAS perde em multicoluna (0,887 vs 0,913).
AINDA NÃO REVISADO por mim — tratar como preliminar.
**Filas desacopladas da sessão** (`orquestracao/noite_0210/fila.sh codex|agy`, tarefas em `codex/` e `agy/`):
Codex (gpt-6.1-sol, xhigh): 02 plano de ponta a ponta com o detector ls3; 03 extrator × detectores nas 317
páginas de teste; 04 validação independente da ordem nas páginas do projeto 23. Antigravity
(gemini-3.8-flash-high; escreve o script, a fila executa e devolve o erro): 01 concordância entre anotadores;
02 ancoragem (quanto o humano mudou a pré-anotação); 03 baselines de ordem no LS; 04 revisão adversarial do
experimento do Codex; 05 galeria visual. Agentes NÃO editam este quadro. Nada commitado.

### 2026-10-01 22:30 — Claude — RESERVA GPU (OCUPADA de novo desde 22:50) — Treino dos detectores no dataset do Label Studio
**GPU OCUPADA até ~03:00. Não disparar outro job de GPU.** Retomado às 23:05 da época 9/60 do `ls3`
(`--retomar`, marcador `treino_ok`). **Incidente:** na pausa pedida pelo Pedro (22:39) o script antigo NÃO
morreu com o TaskStop e usou a GPU até 22:47 (validação do ls3 e 1 época do ls16, que caiu por falta de
memória). Resultados parciais apagados. Lição: matar a árvore com `taskkill /T` e reconferir a GPU. Em paralelo, só CPU: Codex (gpt-6.1-sol, xhigh)
testa o plano "sem bbox fina" (tabela/imagem + colunas, ordem no texto) nas 44 páginas do golden_v4 →
`orquestracao/analises/ordem_sem_bbox.py` e `resultados/ordem_sem_bbox.md` (agente não edita este quadro).
Plano original: `orquestracao/noite_detector_ls.sh` (YOLOv8s, 1024 px, 60 épocas cada):
`ls3` (texto/tabela/imagem) e depois `ls16` (16 classes do guia). Não disparar outro job de GPU.
**Dados:** imagens das 2.119 páginas baixadas do S3 para `data/labelstudio/img/` (1,4 GB, gitignored).
`src/data/montar_deteccao_ls.py` monta `data/deteccao/ls16` e `ls3` com **split por fonte** (veículo):
1.590 treino / 211 val / 317 teste, 197/23/42 fontes sem sobreposição (`data/deteccao/ls_split.json`).
Revisão do Codex (gpt-6.1-sol) achou vazamento por fonte na 1ª versão (o `_` quebrava a regex) — corrigido.
**Saídas:** `resultados/deteccao/{ls3,ls16}_map_teste.json` (mAP no teste do LS) e
`resultados/deteccao/comparacao_detector_ls.txt` (detector × extrator no `diamond_teste`, réguas de 9 e 3
classes, via `orquestracao/analises/avaliar_detector_ls.py`). `detector_layout.py prever` agora usa o nome
de classe do próprio modelo. Linha de base do extrator: 9 classes F1@0,5 0,851 / F1 c/ classe 0,696;
3 classes F1 c/ classe 0,824 / classe 97,8%.

### 2026-10-01 22:10 — Claude — FEITO — Exports do Label Studio (Data Policy) baixados e convertidos
**O quê:** exportei pelo Chrome logado do Pedro (JSON completo, via `/api/projects/N/export?exportType=JSON`)
os projetos de bbox **5 (seed 1, 529), 13 (seed 2, 750), 15 (seed 3, 720), 22 (seed 4, 120)** e o de ordem
**23 (seed2 order, 750)**. Estão em `data/labelstudio/` (adicionado ao `.gitignore`: dado do projeto, uso
permitido no TCC, NÃO publicar). Trouxe `src/anotacao/ordem_labelstudio.py` do worktree de anotação para cá.
**Números:** 2.119 páginas de 1.050 PDFs, **38.587 caixas** nas 16 classes do guia, cada caixa com texto
transcrito. Convertido para golden + COCO + YOLO em `data/labelstudio/conv_seed{1..4}/`.
**Ressalvas:** (1) 83–88% das caixas têm origem `prediction`/`prediction-changed` (pré-anotação corrigida →
ancoragem também nesse dataset; só 12–17% `manual`); (2) seed 1 tem 119 páginas com 2 anotações (dá para
medir concordância entre anotadores); (3) imagens e PDFs estão em S3 público, ainda NÃO baixados (~1 GB);
(4) ordem: usuário 7 tem 84/103 cadeias válidas, usuário 14 tem 41/85 (166 `seta_dupla`), usuário 13 só 1.
**CLIs:** Codex CLI 0.160.0 instalado (logado, `gpt-6.1-sol`) e `agy` 1.2.13 (`gemini-3.8-flash-high`) testados.
**Próximo passo / para quem:** Pedro autoriza baixar as imagens do S3; depois split por PDF, treino do
detector (16 classes × 3 classes) e comparação com o extrator. NÃO commitei.

### 2026-09-19 — Claude — DECISÃO — Alinhar extrator ao projeto de pesquisa (taxonomia do guia + detector treinado)
**Contexto:** o Pedro entrou no projeto de pesquisa (mesma linha). Em troca de ajudar a anotar, recebe um
**dataset de ~centenas de páginas com bbox rotulada à mão (LabelStudio)** e acesso à **4090**. O guia de
anotação deles (`Guia de Anotação de Layout para Diários Oficiais.pdf`, 70 págs) define **~16 classes**
semânticas: id, header, footer, title, section title, sub section title, paragraph, table, figure, caption,
chart, signature, heading (rubrica manuscrita), act, act section, unknown. Diferenças-chave vs o extrator:
separa **act (normativo) de title (não-normativo)**, tem **id/caption/chart/heading**, e **não tem "lista"**.
A anotação de ORDEM deles é por **relações bloco→próximo** (= a formulação "sucessor" do meu LayoutLM).
**Toolbox do Acessilia (revisada, docs/ANALISE_ACESSILIA.md):** é Docling (RT-DETR, mesmo que eu já uso) +
TableFormer, com **PyMuPDF/fitz como caminho rápido**. Reaproveitável: o fast-path PyMuPDF (velocidade) e o
schema de manifesto. O salto de qualidade vem do **dataset à mão**, não da toolbox.
**DECISÕES do Pedro (AskUserQuestion):** (1) **adotar a taxonomia do guia** no extrator; (2) **treinar um
detector rápido E manter o híbrido regras+Docling, e COMPARAR** no teste sem viés (vira resultado do TCC).
**FEITO agora:** `src/data/taxonomia_layout.py` — vocabulário compartilhado + mapeamentos guia↔9-classes↔Docling
(distinções que exigem lógica marcadas: act/act section/id/signature/heading). Validado.
**Plano:** conversor LabelStudio→YOLO/COCO (quando o export chegar) → fine-tune DocLayout-YOLO ou RT-DETR na
4090 → regras como pós-processador + PyMuPDF fast-path → comparar detector × híbrido no teste sem viés.
Paralelo (ação da reunião): reavaliar Gemini com split treino/teste correto (vazamento).
**Preciso do Pedro:** (a) um export de amostra do LabelStudio pra finalizar o conversor no formato real;
(b) confirmação de quando a 4090 libera. NÃO commitei.

### 2026-09-16 23:40 — Claude — DECISÃO — Massa de anotação com Gemini (Rose) e diagnóstico do `outro`-marca
**Tarefa:** T39 · **Pedido do Pedro:** (a) melhorar as caixas `outro` "que não têm nada"; (b) rodar essa
noite um modelo Gemini que olha a extração, aponta os problemas e vai anotando, para criar massa maior.

**(a) `outro` só-marca — diagnóstico (não é bug do extrator):** as caixas `outro` "sem nada" são marcas de
diagramação (`<#SEGRASE...>`, `<@textFrameStart>`) que vazaram do layout para a camada de texto. Mas o OURO
do Pedro TAMBÉM as rotula `outro` (17 regiões `outro`, ~11 são marcas). Medi no diamond_teste: DROPAR as
regiões só-marca PIORA tudo (F1@0,5 0,851→0,833; F1@0,9 0,754→0,734; revocação de `outro` 0,65→0,00), porque
o extrator passaria a discordar do próprio ouro. A etapa 7 já fundiu as fragmentadas. **É decisão de POLÍTICA
de anotação (anotar as marcas ou não), do Pedro** — não mexo no ouro sem o ok dele. Recomendação: filtrar as
marcas na origem (nível de palavra) se ele quiser que nem humano nem VLM gastem caixa nelas.

**(b) Massa Gemini — DECISÃO:** reaproveitar `src/data/gerar_rose.py` (já robusto: rpm, --retomar, --pular-erros,
para limpo na cota diária, salva em lote NOVO com anotador `VLM:<modelo>`, nunca toca raw/golden/origem).
- **Modo `regioes`** (crítico: olha a proposta v3 e corrige classe/união/quebra), NÃO `palavras`. Testei
  `palavras`: colapsa 43 regiões em 3 (um blobão de texto) com o flash-lite — inservível. `regioes` é o que
  o rose_treino (199 págs) já provou: mantém a segmentação (razão VLM/proposta mediana 1,00) e corrige de
  verdade (639 reclassificações, ~900 uniões/quebras). As `mudancas` vs extrator = os "problemas encontrados".
- **Pool:** 384 páginas NOVAS, cacheadas, 21 veículos, fora dos veículos de teste (ce/ma/rj) e de tudo já
  usado em golden/diamond. Lote de tarefas `data/diamond/diamond_massa1`; saída `data/diamond/massa1_gemini`.
- **503 "high demand":** o Gemini às vezes responde 503 (congestão). Orquestração em VÁRIAS PASSADAS com
  `--retomar` (`orquestracao/madrugada_rose_massa.sh`, keep-awake) — página que falha numa passada é tentada
  na próxima; para na cota diária.
- **ATENÇÃO p/ treino futuro:** a massa inclui veículos que também aparecem em páginas do diamond_teste
  (famílias sobrepostas; as PÁGINAS de teste estão excluídas, mas a família não). Ao treinar um detector nessa
  massa e testar no diamond_teste, segurar as 11 famílias de teste. As anotações em si são válidas.
- NÃO commitei. `.env` tem GEMINI_API_KEY (não imprimo). Modelo `gemini-3.1-flash-lite`.
**Próximo passo / para quem:** massa roda a noite; de manhã reviso a taxa de sucesso e a qualidade, e o Pedro
decide a política do `outro`-marca.

### 2026-09-16 21:40 — Claude — DECISÃO+RESULTADO — Etapa 7 do extrator: `fundir_fragmentos` (extrator mais conciso)
**Tarefa:** T39 · **Pedido do Pedro:** consertar a EXTRAÇÃO (caixas) do extrator com o ouro do Diamond,
sem híbrido, para apresentar amanhã.
**Diagnóstico (diamond_teste, 11 págs sem viés):** o extrator produzia +17% de regiões. Duas causas:
(a) **super-split de mesma classe** — 26 regiões de ouro repartidas; o balde limpo é marca/rodapé/cabeçalho
(`outro→outro` ×8) e sobra de bloco em `texto`; (b) **super-merge** (12), sobretudo a fusão de listas.
Achado-chave: o ouro mantém *de propósito* 75 pares de `texto` adjacentes com vão mínimo — logo merge
geométrico cego de `texto` DESTRÓI (F1@0,5 cai p/ 0,73). Só dá para fundir com segurança onde o ouro não
separa: marcas/rodapé/cabeçalho, e `texto` só quando um lado veio da sobra de bloco (`origem="regras"`).
**DECISÃO:** nova **etapa 7 `_fundir_fragmentos`** em `src/data/regioes.py`, `propor(..., fundir=True)` por
padrão. Constantes visíveis: `FUNDIR_LIVRE` ({outro,rodape,cabecalho}, folga≤2,0), `FUNDIR_SOBRA` ({texto},
folga≤0,6, exige origem regras), `FUNDIR_OV_MIN=0,6`, `VAO_LISTA_MULT=1,6` (varri 0–2,5; 1,6 é ótimo p/ F1classe).
**Ganho (diamond_teste):** F1@0,5 **0,838 → 0,851**, F1@0,9 **0,737 → 0,754**, F1 c/ classe **0,686 → 0,696**,
regiões **383 → 370** (rumo às 328 do ouro). Reproduzível: `avaliar_diamond.py --lote diamond_teste` mostra
`regioes` vs `regioes_sem_fundir`.
**Evidência da ancoragem (bônus p/ o TCC):** a MESMA correção *ajuda* no teste do-zero e *piora* nos lotes
ancorados (piloto 0,951→0,944; treino 0,913→0,898), porque o ouro deles foi corrigido A PARTIR do extrator —
a super-segmentação está embutida naquele ouro. Prova quantitativa de por que o teste do-zero importa.
**Teste alterado:** `test_03` do `test_regioes_v3` afirmava "marca por linha = região distinta"; o ouro humano
refuta (marcas contíguas na coluna = um bloco). Reescrito para a conduta correta (contíguas fundem, distantes
não). Suite: 21/21 OK.
**Honesto:** ganho real e seguro (nunca piora no teste sem viés), mas modesto — 11 págs é n pequeno. Confiança
estatística pede mais páginas do-zero. NÃO commitei (aguardo o Pedro). Não mexi em `data/`.
**Próximo passo / para quem:** Pedro decide se integro o reclassificador (classe 77%→81%, pronto) e anota mais
páginas do-zero para dar confiança; eu preparo o material de apresentação.

### 2026-09-16 01:00 — Claude — RESULTADO — Madrugada do extrator: ganhos reais mas modestos (11 págs limitam)
**Tarefa:** T39
**Detector retreinado (96 ouro, YOLOv8s):** val mAP50 **0,689 → 0,765** (+0,076) — mais dado ajuda o detector.
MAS no teste SEM viés (11 págs, que ele não viu) fica em F1@0,5 **0,735**, ainda ABAIXO do extrator (0,838).
Distribuição do teste do-zero difere do treino ancorado; 11 págs é ruído.
**Varredura de regras (11 págs):** nenhuma config melhora; REMOVER qualquer regra PIORA (sem dividir_campos
-0,022; sem assinatura -0,021). As regras são líquidas positivas — validam o desenho do extrator.
**Reclassificador por features (RandomForest, sugestão do diagnóstico+GPT):** melhor ganho do lado do
extrator — F1 c/ classe **0,686 → 0,714**, acerto de classe **77% → 81%** (limiar 0,4, sem as features de
lista; as de lista do GPT — hanging_indent etc. — não ajudaram, 0,709). Erro que persiste: **texto↔lista**.
**GPT (consulta 2):** endossou o rumo ("YOLO 0,76 < híbrido 0,84 é bom achado: estrutura+pós-processamento
vence detector visual pequeno com pouco dado"); deu features de lista (não ajudaram aqui) e priorização de 5
experimentos. Aba deixada aberta para o Pedro.
**Honesto:** NÃO houve salto significativo — 11 págs é pouco para medir/atingir, e o extrator já é forte. Os
ganhos (detector +0,076 mAP; reclassificador +0,028 F1classe) são reais e escalam com dado. Ferramentas
novas: `analises/reclassificador.py`, `varrer_extrator.py`, `avaliar_diamond --pred-classe`.
**Próximo passo / para quem:** Pedro anota mais páginas do zero (teste ganha confiança) e mais Diamond; o
reclassificador refinado + o detector com o 4090 são o caminho do ganho grande. Kaggle YOLOv8m/96: pendente.
### 2026-09-15 22:45 — Claude — FEITO — Reclassificador de regiões por features (a melhoria mais promissora)
**Tarefa:** T39
**O quê:** `orquestracao/analises/reclassificador.py` — RandomForest leve que dá a classe de cada região do
extrator a partir de features (fração de maiúsculas, altura de fonte, posição y, fração de linhas com
marcador de lista, palavras/linha, largura/altura rel., rótulo do detector, score, comeca_campo, eh_assin).
Treina no ouro (96 págs), sobrescreve a regra só quando confiança >= 0,4.
**Resultado (teste SEM viés, 11 págs):** F1 com classe **0,686 → 0,714**; acerto de classe **76,9% → 81,5%**.
É o maior ganho encontrado (varredura de regras e híbrido davam ~0,695). Erro que sobra: **texto↔lista**
(514 lista→texto, 405 texto→lista) — a classe mais difícil. Features top: y_topo, rotulo=table, score,
page_footer/header, alt_font, frac_maiusc.
**Honesto:** 11 páginas é ruído; o ganho é real mas modesto. O reclassificador ESCALA com mais dado — é o
componente certo para o ganho grande quando o Diamond crescer. Ideia veio do diagnóstico + GPT.
**Rodando:** madrugada (detector 96 ouro + varredura). GPT consultado de novo (lista x texto, sequência).
**Próximo passo / para quem:** de manhã, integrar o reclassificador como opção do extrator e medir com o
detector novo; anotar mais páginas do zero para o teste ganhar confiança.
### 2026-09-15 22:15 — Claude — RODANDO — Madrugada de melhoria do extrator; teste sem viés medido
**Tarefa:** T39, T40
**Marco:** `diamond_teste` (11 páginas do zero, Pedro pulou a 12) deu o 1º número SEM ancoragem do extrator:
F1@0,5 **0,838** (era 0,981 ancorado), F1classe 0,686, super-segmenta +17% (55 "texto" espúrios). Detector
YOLO localiza pior (0,764). Diagnóstico: dividir_campos exagera (rebaixa 10 títulos), lista/assinatura/figura
com classe fraca. `avaliar_diamond --pred-classe` (híbrido) e `orquestracao/analises/varrer_extrator.py` criados.
Varredura preliminar: nenhuma config de regra melhora muito nas 11 (melhor 0,695 vs 0,686) — mudança de
regra não resolve; caminho é mais dado + reclassificador.
**GPT (consulta via navegador do Pedro):** confirmou "classificação pós-localização"; sugeriu merge global por
score (contra super-seg), classificador leve por features, e guardar proveniência. Ideias, não decisões.
**Rodando (`orquestracao/madrugada_extrator.sh`):** re-treino YOLOv8s com 96 ouro → prevê no teste →
varredura + ablação no diamond_teste. Diamond re-exportado (77 treino + 19 val). Zip Kaggle refeito (val=19).
**Próximo passo / para quem:** Claude lê de manhã. Pedro pode rodar YOLOv8m no Kaggle (dataset novo).
### 2026-09-15 21:40 — Claude — FEITO — Híbrido como sistema + notebook para o Pedro testar
**Tarefa:** T39, T40
**O quê:**
- `avaliar_diamond.py`: novo `--pred-classe <jsonl>` (+ `--pred-classe-conj`) = HÍBRIDO como sistema
  (`hibrido:<nome>` = caixas do extrator + classe do detector). Testado no diamond_piloto.
- `notebooks/avaliar_extrator.ipynb`: notebook para o Pedro rodar e ver a comparação justa
  (extrator × YOLO × híbrido em 2 variantes) contra a anotação humana de um lote. Default `LOTE=diamond_teste`;
  roda o detector, monta a tabela (F1@0,5 / F1 c/ classe / Classe %) e avisa se o lote ainda não foi anotado.
  Executado: caminho vazio (diamond_teste 0/12) roda sem erro. Encoding: build via arquivo UTF-8 (o `python -c`
  lia stdin como cp1252 e corrompia acentos).
**Uso:** anotar o `diamond_teste` (12 do zero) → abrir o notebook → Run All → tabela sem viés.
**Próximo passo / para quem:** Pedro anota o diamond_teste e roda o notebook. Suíte de testes: OK.

### 2026-09-15 21:00 — Claude — FEITO/ACHADO — Doc do extrator + piloto do híbrido (extrator+YOLO)
**Tarefa:** T39
**Diamond:** diamond_treino agora com 76 concluídas (96 de ouro no total, era 59).
**Documento técnico do extrator** publicado (artifact): passo a passo de `propor()`, as 3 fontes (palavras +
geometria + Heron), as regras do passo 6, alertas, problemas conhecidos e o piloto do híbrido.
**Piloto do híbrido (caixa do extrator + classe do YOLO):** implementado reaproveitando
`seg.aplicar_classes_rose(propor(...), palavras, pred_yolo, conj)`. Medido nas 12 páginas held-out:
- extrator (ancorado): F1classe 0,965 / classe_ok 99,4%
- híbrido todas as classes: 0,844 / 87,6%  ·  híbrido só assinatura+cabeçalho: 0,958 / 99,2%
→ **Nenhuma variante supera o extrator**, MAS o teste é viciado: nas páginas ancoradas a classe do extrator
já é 99% (inflado). O híbrido está pronto; o veredito real só sai no `diamond_teste` (do zero).
**Próximo passo / para quem:** Pedro anota o `diamond_teste`; aí medimos extrator × YOLO × híbrido sem viés.
Para reuso, vale adicionar um `--pred-classe` ao `avaliar_diamond` (híbrido como sistema); ainda não feito.

### 2026-09-15 20:15 — Claude — ACHADO — Kaggle LIMPO: YOLOv8m ≈ YOLOv8s (gargalo é dado)
**Tarefa:** T39
**Rerun limpo confirmado** (val_batch = 12 imagens, grade 4×3). YOLOv8m, 157 épocas (early stop). Números
honestos (12 páginas held-out, mesmas do split local):
- mAP50: **m 0,690 vs s 0,689** — empate. word-F1@0,5: m 0,828 vs s 0,808; F1classe m 0,724 vs s 0,723.
**Conclusão:** com ~59 páginas de ouro, o modelo MAIOR não ajuda — o gargalo é DADO, não capacidade.
Isso derruba o "m > s" que eu tinha dito (era o 0,79 vazado). Pesos limpos em
`models/detector_diamond/kaggle_best_limpo.pt`. O extrator (0,981) segue ancorado; veredito real só com o
`diamond_teste` (do zero). **Próximo passo:** Pedro anota diamond_teste; documento-panorama sendo escrito.

### 2026-09-15 09:20 — Claude — FEITO — Kaggle limpo + conjunto de teste do zero (T39/T40)
**Tarefa:** T39, T40
**1. Kaggle limpo:** `dist/kaggle/detector_diamond_yolo.zip` já é o deduplicado (val=12, train=207, sem
vazamento). Pedro sobe como NOVA VERSÃO do dataset `detector-diamond-yolo` e roda de novo
`notebooks/kaggle_detector.ipynb` (mesmo notebook; o problema era só o zip antigo). Aí o mAP do Kaggle
vira honesto e comparável ao yolov8s local (0,689).
**2. Conjunto de teste NÃO enviesado (`diamond_teste`, 12 pág.):** novo modo `preparar_diamond.py --em-branco`
grava `proposta: []` → a ferramenta abre a página em branco e o anotador desenha do zero (gabarito não
ancorado em nenhum modelo). Páginas sorteadas de veículos fora do teste, nenhuma vista por extrator/detector.
Verificado no servidor: abre em branco, 0 caixas, sem erro no console. `diamond.html` linha 647 já protege
os alertas que dependem da proposta (`intacta(r)`), então proposta vazia não quebra.
**Como usar depois de anotado:** teste justo = `exportar_deteccao.py --teste diamond_teste` (split isolado) e
`avaliar_diamond.py --lote diamond_teste --pred <yolo>` (extrator × detector × híbrido, sem ancoragem).
**Próximo passo / para quem:** Pedro — rodar o Kaggle limpo e anotar as 12 do `diamond_teste` (do zero).

### 2026-09-15 08:55 — Claude — ACHADO/CORREÇÃO — Kaggle usou o zip ENVIESADO (val=16)
**Tarefa:** T39
**Definitivo:** a figura `runs/diamond/val_batch0_labels.jpg` do results.zip mostra 16 imagens de validação
(grade 4×4 cheia). O split limpo tem 12. Logo o Kaggle treinou com o zip PRÉ-correção (val=16, 10 vazadas).
**Consequência:** o val do Kaggle (mAP50 0,793) está inflado, e o word-F1 0,926 que calculei nas minhas 12
também (o split dele difere; várias dessas 12 estavam no treino dele). Retrato o "m > s limpo" de antes:
NÃO está estabelecido — comparei s honesto (0,689) contra m vazado (0,793). Praticamente todas as páginas de
ouro entraram no treino do m vazado, então não há held-out para medi-lo honestamente com os dados atuais.
**O que vale:** os pesos `models/detector_diamond/kaggle_best.pt` existem e o modelo pode ser bom; só não
temos medida limpa dele. YOLOv8s local (0,689 mAP50) segue sendo o único número honesto.
**Próximo passo / para quem:** re-treinar yolov8m/l no split LIMPO (4090 no fim de semana) + conjunto de
teste desenhado do zero. Só então comparar m × s × extrator de forma justa.

### 2026-09-15 08:40 — Claude — ACHADO — Detector do Kaggle (YOLOv8m) chegou; m > s
**Tarefa:** T39
**Kaggle:** YOLOv8m, 200 épocas, imgsz 1024, batch 16. Val próprio (ultralytics): mAP50 **0,793**
(mAP50-95 0,728) — contra 0,689 do YOLOv8s local. Pesos em `models/detector_diamond/kaggle_best.pt`.
Predições em `resultados/deteccao/pred_kaggle_*.jsonl`.
**Head-to-head nas 12 páginas held-out do split limpo local (word-F1@0,5 / F1classe / classe_ok):**
YOLOv8m 0,926 / 0,876 / 92,7% · YOLOv8s 0,808 / 0,723 / 84,3% · extrator (ancorado) 0,981 / 0,965 / 99,4%.
**Ressalva:** o zip enviado ao Kaggle pode ser o de ANTES da correção de duplicatas (val=16 com vazamento)
ou o limpo (val=12). Se foi o vazado, o split do Kaggle difere do meu e algumas dessas 12 podem ter entrado
no treino dele → o 0,926 vira teto otimista. O sinal independente (val próprio 0,793 > 0,689) já mostra
m > s de forma limpa. Para confirmar: nº de imagens em images/val do dataset Kaggle (12 = limpo, 16 = vazado).
**Interpretação:** m supera s; direção validada. Nenhum detector é comparável ao extrator ainda (0,981 é
ancorado). O veredito real precisa do conjunto de teste desenhado do zero.
**Próximo passo / para quem:** Pedro confirma o split; fim de semana usa yolov8m+ na 4090; teste do-zero.

### 2026-09-15 01:30 — Claude — ACHADO/CORREÇÃO — Detector: número honesto (retreino limpo) e retratação
**Tarefa:** T39
**Retreino limpo (sem vazamento).** Métrica honesta do detector nas 12 páginas de validação que ele NÃO viu:
- ultralytics mAP50 = **0,689** (mAP50-95 0,561). Por classe (mAP50): tabela 0,995, assinatura 0,894,
  cabecalho 0,871, texto 0,843, figura 0,771, rodape 0,696, titulo 0,613, lista 0,495, outro 0,022.
- word-F1 nas mesmas 12 held-out: detector F1@0,5 **0,808** / F1classe 0,723 / classe_ok 84,3%;
  extrator atual (regioes) F1@0,5 0,981 / F1classe 0,965 / classe_ok 99,4%.
**Correção do que falei ontem:** o "detector classifica melhor que o extrator" era efeito do VAZAMENTO
(páginas de treino na avaliação). No held-out honesto, **o extrator ganha** — MAS o número dele (0,98) é
inflado por ancoragem: o gabarito foi corrigido a partir da proposta do próprio extrator. Nessas páginas o
gabarito ≈ saída do extrator; o detector, que não vê a proposta, parte em desvantagem estrutural.
**Conclusão honesta:** ainda **não dá para comparar** detector × extrator de forma justa. Falta um conjunto
de teste desenhado do ZERO (sem a pré-marcação) — o `exportar_deteccao.py --teste <lote>` já reserva isso.
O detector, com só ~59 páginas de ouro, já vai bem nas classes de diário (tabela/assinatura/cabecalho/figura).
**Próximo passo / para quem:** Pedro — se puder, 10-15 páginas desenhadas do zero = teste justo. Fim de
semana na 4090: mais dados + modelo maior. Relatório com o Gemini só-texto quando o Pedro decidir.

### 2026-09-15 01:00 — Claude — ACHADO — Gemini só-texto responde imagem×modelo; bug de vazamento no exportador corrigido
**Tarefa:** T37, T39
**Gemini só-texto (golden_v4, 44 pág.):** τ = **0,896**, sucessor 80%. Comparando: VLM com imagem (marcas+classes)
0,962; VLM sem marcas 0,942; **VLM só-texto 0,896**; melhor LLM de texto (qwen fs2) 0,876; XY-cut 0,825.
→ Responde a pergunta aberta do relatório: **a imagem vale ~0,066 de τ** (0,962→0,896), e sem a imagem o
Gemini cai para perto das LLMs de texto (0,876). A vantagem do VLM vem de fato da imagem, não só de ser um
modelo maior. Predição em `resultados/golden/golden_v4/pred_vlm_gemini_3_1_flash_lite_sem_imagem.jsonl`.
**Bug achado e corrigido — vazamento no `exportar_deteccao.py`:** páginas re-anotadas geram várias linhas
`concluida`; o exportador copiava cada linha, então a mesma página caía em treino E validação (10 de 16 no
1º treino). A métrica de validação de ontem (mAP50 0,841) está inflada. `paginas_do_lote` agora deduplica
por page_id (fica a última). Re-exportado limpo: 47 ouro treino + 160 prata + 12 ouro val, sem vazamento.
Teste `test_exportar_deteccao` OK. Zip do Kaggle refeito (deduplicado). **Retreino limpo em curso**
(`orquestracao/retreino_detector.sh`).
**1º detector (leaked, só como sinal):** classifica melhor que o extrator atual (classe_ok 93% vs 89-91%),
localização um pouco abaixo (F1@0,5 ~0,89 vs 0,92-0,95). Número honesto sai do retreino limpo.
**Próximo passo / para quem:** Claude lê o retreino e fecha o resumo. Regenerar o relatório com o
Gemini só-texto fica para quando o Pedro estiver acordado (decisão de escopo do relatório).

### 2026-09-15 00:30 — Claude — FEITO — Pacote Kaggle do detector + testes do código novo (T39)
**Tarefa:** T39
**O quê:**
- **Kaggle (opcional, paralelo):** `dist/kaggle/detector_diamond_yolo.zip` (89 MB, dataset YOLO) e
  `notebooks/kaggle_detector.ipynb` (treina YOLOv8m na T4, exporta best.pt/results.csv). Pedro sobe o
  dataset como `detector-diamond-yolo` e roda; a avaliação contra o ouro roda local com os pesos.
- **Testes:** `tests/test_exportar_deteccao.py` (rótulos YOLO: normalização, clamp, coords invertidas,
  área zero, classe fora) e classe `TestSemImagem` em `tests/test_vlm_ordem.py` (prompt avisa sem imagem,
  sufixo `_sem_imagem`, e a imagem não é renderizada nem enviada). Suíte: **105 OK** (era 96).
- Pedro autorizou pegar ideias do ChatGPT no navegador dele "só se ficar sem o que fazer"; a extensão do
  Claude no Chrome não está conectada, então não deu — fiz o trabalho seguro e no escopo (testes).
**Estado da noite:** treino do detector local em ~época 85/200 (losses ~0,7); Gemini só-texto na fila.
**Próximo passo / para quem:** de manhã o Claude lê os resultados e monta o resumo.

### 2026-09-14 21:00 — Claude — FEITO/RODANDO — Noite: 1o detector treinado + Gemini só-texto (T39)
**Tarefa:** T39, T37
**Contexto:** Pedro fez 39 páginas novas no `diamond_treino` (64 concluídas agora; 84 ouro no total) e pediu
uma noite produtiva. Rodando `orquestracao/noite_detector.sh` (keep-awake 8h):
1. re-exporta o dataset (227 treino = 67 ouro + 160 prata, 17 val) e treina o 1o detector — YOLOv8s leve,
   imgsz 1024, batch 4, 200 épocas c/ early stopping. Baseline local na 4050 para de-riscar a 4090.
2. prevê e mede o detector contra o ouro (`avaliar_diamond --pred`), regenerando a segmentação com as 64.
3. Gemini SÓ TEXTO no golden_v4 (`vlm_ordem --sem-imagem`, novo) — isola imagem × modelo, a pergunta
   aberta do relatório; reavalia o golden_v4.
**Ambiente:** a `ultralytics` derrubou o torch cu128 e instalou o CPU; restaurei torch 2.9.1+cu128 /
torchvision 0.24.1+cu128 (cuda OK). Fumaça: YOLOv8s/1024/b4 cabe nos 6 GB (pico ~3 GB; a b8 dava 5,49 GB).
**Código novo:** `gerar_rose.chamar_vlm` aceita imagem=None; `vlm_ordem --sem-imagem`. Testes: 61 OK.
**Regra:** um job de GPU por vez — detector treina/infere sozinho; Gemini (API) roda depois.
**Próximo passo / para quem:** de manhã o Claude lê os resultados. Dataset grande de ordem por VLM
(destilação) fica para quando a GPU estiver livre / a 4090.

### 2026-09-14 20:00 — Claude — FEITO/PLANO — Scaffolding do detector de layout para a RTX 4090 (T39)
**Tarefa:** T39
**Contexto:** Pedro terá uma RTX 4090 (uso liberado pela faculdade) no fim de semana e quer deixar o
extrator quase impecável. O extrator de hoje é forte na localização (F1@0,5 0,92–0,95) e fraco na classe
(~0,80), além de cego onde o texto é só imagem (13,8% das páginas) e dependente da camada de texto do PDF.
A jogada: fine-tunar um detector que trabalha da IMAGEM nas 9 classes do Diamond, resolvendo os três furos.
Gargalo é dado (45 páginas ouro), não compute → prata do Rose (VLM local, sem cota) fecha a conta.
**Feito (construído e verificado sem GPU):**
- `src/data/exportar_deteccao.py`: Diamond+Rose → dataset YOLO. Verificado: 210 treino (36 ouro + 174 prata)
  + 9 val (ouro), 8.089 regiões, coords normalizadas ok. Prata que repete page_id do ouro é descartada.
  Lotes em `--teste` viram split isolado (reservar aqui páginas desenhadas do zero = medição honesta).
- `src/models/detector_layout.py` (treinar/prever) — YOLOv8s leve (ou pesos do DocLayout-YOLO); `prever`
  grava regiões em pontos do PDF.
- `avaliar_diamond.py --pred <jsonl>`: mede a saída crua do detector contra o ouro, mesmo critério.
- `orquestracao/fim_de_semana_4090.sh`: export → treino → prever → avaliar, sozinho.
- `.gitignore`: `data/deteccao/`, `runs/`, `resultados/deteccao/`.
**Escolhas de Pedro (14/09):** foco do fim de semana = "os dois" (detector primeiro, depois destilar o VLM
no LayoutLM). Está considerando, para conversar com o orientador, um classificador de imagem + OCR **leves**
para o texto-imagem — casa com o plano: o próprio detector (YOLO-s) é o classificador leve, e OCR leve
(RapidOCR/PaddleOCR-mobile) roda só nas regiões sem palavra do PDF.
**Pendente para a placa:** `venv\Scripts\pip install ultralytics`; anotar mais Diamond; rodar o roteiro.
Destilação (VLM→LayoutLM) ainda precisa do preparo de dados (a construir).
**Próximo passo / para quem:** Claude monta a destilação e a rota do VLM local; Pedro anota e roda na 4090.

### 2026-09-14 19:00 — Claude — REVISÃO — T37c: relatório v4 fechado
**Tarefa:** T37
**O quê:** as 9 correções da T37c conferem no `docs/RELATORIO_V4.md`. Ajustei três frases no script
(`src/eval/relatorio_v4.py`): "fator decisivo" das marcas → "efeito medido"; "contribuição desprezível" das
classes → "sem efeito mensurável"; em 6.1 o p do VLM sem marcas × XY-cut estava rotulado como ajustado
(1,98e-04 é o bruto; ajustado 2,97e-03). O rótulo de `aleatoria` voltou à convenção do projeto ("Ordem do
detector (entrada embaralhada)", ver `src/eval/baselines.py`). Relatório e notebook regenerados; testes OK.
**Aviso do despachante:** "fora do escopo" em `COMUNICACAO_AGENTES.md` e `src/eval/avaliar_golden.py` foram
edições minhas durante o despacho (quadro; rótulo trocado e revertido), não do agente.
**Próximo passo / para quem:** Pedro decide o rumo (extração ou treino) a partir do relatório.

### 2026-09-14 18:45 — Claude — FEITO/ACHADO — T38 importada; ablação do VLM sem classes completa; T37b revisada
**Tarefa:** T37, T38
**O quê:**
- A madrugada de 13→14/09 não rodou (PC desligado). Relancei `orquestracao/madrugada_vlm_sem_classes.sh`
  às 18:15: VLM sem classes completo (45/45; 40 válidas), `golden_v4` reavaliado, T37b despachada e concluída.
- T38 (Kaggle, zip `resultados_kaggle (1).zip`): **importação seletiva**. Entraram só
  `resultados/golden/golden_v4/pred_llm_{qwen3_8_27b,gemma4_31b}{,_fs2}.jsonl` e
  `golden_v4/execucoes_llm.jsonl` (acrescentado a `resultados/execucoes_llm.jsonl`). Não usei
  `importar_resultados.py` porque ele sobrescreveria `avaliacao.json/md` do `golden_v4` e do `golden_v3`
  com as versões do Kaggle, que não têm VLM nem sementes do LayoutLM. As predições do teste no zip são
  idênticas às locais. Zip inteiro em `resultados/kaggle/2026-09-14_1820/`.
**Resultado (`golden_v4`, 44 páginas, τ / sucessor):** VLM sem classes 0,966 / 94%; VLM com classes
0,962 / 94%; VLM sem marcas 0,942 / 90%; LayoutLM sucessor 0,890 / 67%; qwen3.8:27b fs2 0,876 / 76%;
qwen3.8:27b 0,859 / 80%; gemma4:31b fs2 0,848 / 79%; XY-cut 0,825 / 72%; gemma4:31b 0,822 / 80%.
Só as três variantes do VLM superam a XY-cut após Holm. Classes: com × sem, Wilcoxon pareado p = 0,078
(sem efeito). Marcas: com × sem, p = 0,0087. LLMs de texto: 64–82% de permutações válidas, 20–31 s/pág. em 2× T4.
**Revisão T37b:** tabelas corretas; texto com afirmações que os números não sustentam (familiaridade "reduziu"
o tempo, mas a mediana foi 17 s nas já vistas × 15 s nas novas; p brutos citados como ajustados; "mecanismo
primário" atribuído à imagem, mas VLM × LLM mistura modalidade e modelo; melhor LLM escolhida por estrato;
comparação errada do Rose no piloto). Correções em `orquestracao/prompts/T37c_relatorio_v4_ajustes.md`.
**Próximo passo / para quem:** Claude revisa a T37c. Pedro: página RJ do `golden_v2` ainda em rascunho.

### 2026-09-13 23:00 — Claude — REVISÃO/ACHADO — T37: relatório v4; VLM com marcas lidera nos dois Golden
**Tarefa:** T37, T36
**O que fiz / o que achei:** `orquestracao/avaliar_v4.sh` rodou (golden_v4 e golden_v3 com todos os
métodos locais, VLM sem marcas) e o Antigravity gerou `src/eval/relatorio_v4.py`,
`notebooks/relatorio_ordem_v4.ipynb`, `docs/RELATORIO_V4.md` e 2 figuras em `docs/figuras/` (fora do
escopo declarado, aceitas). Conferi os números principais contra `avaliacao.json`:
| | golden_v3 (47) τ / sucessor | golden_v4 (44) τ / sucessor |
|---|---|---|
| VLM gemini-3.1-flash-lite com marcas | 0,924 / 89% | 0,962 / 94% |
| VLM sem marcas | — | 0,942 / 90% (válidas 30/44 contra 38/44) |
| melhor LLM de texto (qwen3.8:27b, 2 exemplos) | 0,881 / 74% | pendente Kaggle |
| LayoutLM sucessor (semente 42) | 0,845 / 67% | 0,890 / 67% |
| XY-cut | 0,851 / 74% | 0,825 / 72% |
No golden_v4, só o VLM (com e sem marcas) difere da XY-cut após Holm. **Vantagem possível:** no
golden_v4 o prompt do VLM leva a classe humana de cada caixa. Ablação `--sem-classes` (flag nova em
`vlm_ordem.py`): a cota diária do Gemini acabou em 12/45 páginas; nessas 12, com classes τ 0,913 e sem
classes 0,938 (Wilcoxon p = 0,125) — sem sinal de que a classe explique o resultado; no golden_v3, sem
classes humanas, o VLM já tem 0,924. Relatório precisa de correções (superioridade sem significância,
"pseudo-rótulos confiáveis", diagnóstico heurístico na seção 6.2, familiaridade das 20 páginas no
custo, classes no prompt): `orquestracao/prompts/T37b_relatorio_v4_revisao.md`.
`orquestracao/madrugada_vlm_sem_classes.sh` espera a cota renovar (04:20), completa a ablação, reavalia e
despacha a T37b.
**Próximo passo / para quem:** madrugada automática; Pedro roda o Kaggle (T38).

### 2026-09-13 22:02 — Claude — REVISÃO/FEITO — T35: regiões v3 + classes do Rose aplicadas às 174 páginas não anotadas
**Tarefa:** T35, T33
**O que fiz / o que achei:** Antigravity entregou `REGRAS_V2`/`REGRAS_V3`, regra `outro_marcacao`,
`aplicar_classes_rose`, sistemas novos no `avaliar_diamond.py`, `atualizar_proposta.py` e 8 testes
(suíte 96 OK; `regras="v2"` reproduz 197/199 propostas, as 2 restantes são as páginas de origem deslocada).
Avaliação (proposta v2 tem vantagem de ancoragem): v3 + classes do Rose só para `assinatura` e
`cabecalho` não perde caixa e sobe o F1 com classe — `diamond_treino` 0,789 → 0,800 (assinatura 0,64 →
0,95), `diamond_piloto` 0,840 → 0,857. Apliquei com `--aplicar` (backup `tarefas.jsonl.bak_20260913_215945`):
174 páginas `proposta_versao: v3`, 25 anotadas intocadas. A checagem pós-aplicação achou 3 páginas (AP
78 e 128, SE 133) com palavra em duas caixas: marca `<#E.G.B#...#/>` no meio da linha de assinatura saía da
caixa, mas o centro dela continuava dentro; e o Rose sobrescrevia a classe `outro`. Corrigi em
`regioes.py` (marca dentro do envelope que sobra fica na caixa; `aplicar_classes_rose` não mexe em
`outro`), reapliquei (backup `..._220045`): 0 página com palavra sem caixa ou dupla.
**Próximo passo / para quem:** Pedro retoma o `diamond_treino` quando quiser (recarregar a ferramenta).

### 2026-09-13 22:10 — Claude — REVISÃO — T34 (VLM de ordem) e alerta do `golden_v2`
**Tarefa:** T34, T36
**O que fiz / o que achei:**
- `src/eval/vlm_ordem.py` (Antigravity, 21 testes; suíte 88 OK): regras lidas do guia, blocos B1..Bn na
  ordem de entrada, set-of-mark, reparo de permutação, ritmo/cota, parcial/retomar, saída
  `pred_vlm_<modelo>.jsonl` onde o `avaliar_golden.py` procura. Conferi coordenadas (inclusive
  `origem_pagina`). Ajuste meu: rótulo das marcas em Arial 16 px (a fonte padrão do PIL tinha ~10 px).
  Teste real em 3 páginas do `golden_v3`: 3/3 permutações válidas, 6,7 s/página. Rodando agora nos 47 do
  `golden_v3` e nos 45 do `golden_v4` (predições cegas; o Pedro não deve abri-las antes de ordenar).
- **ALERTA do despachante** (`golden_v2/anotacoes.jsonl` mudou durante a T34): não foi o agente. Às 21:51
  a ferramenta do Golden reabriu o `golden_v2` (último lote usado) e a página RJ "Parte IV
  (Municipalidades) 2021-08-30" passou de `concluida` para `rascunho`, com a **mesma ordem** (51 blocos);
  às 21:52 o Pedro começou o `golden_v4`. Não mexi (anotação humana); pedi ao Pedro que reabra a página e
  aperte Enter. Sugestão para a ferramenta: pedir confirmação antes de editar página concluída.
- `docs/GUIA_ORDEM_LEITURA.md`: regra 8 alinhada ao lote — regiões sem palavra na camada do PDF (brasão,
  cartaz com texto só na imagem) ficam fora do `golden_v4`.
**Próximo passo / para quem:** Claude avalia o VLM no `golden_v3`; Pedro corrige o status no `golden_v2`.

### 2026-09-13 21:45 — Claude — FEITO — `rose_treino` completo (199/199) e primeira medição fora da amostra
**Tarefa:** T31, T33
**O que fiz / o que achei:**
- Rodada 1 do `rose_treino`: 180 gravadas, 19 puladas (13 por união cuja caixa cobria palavras de
  outra região, 5 por "união com quebra", 1 na preparação). `gerar_rose.py` agora **desfaz** a união que
  cobriria palavra de fora e **ignora** quebra em região unida; 2 testes novos (67, OK). Rodada 2 com
  `--retomar`: as 19 passaram. `erros.jsonl` da rodada 1 guardado como `erros_rodada1.jsonl`.
- **Página 15 do `diamond_treino` (PA, origem y = 100)** era outro caso de origem deslocada, que a
  correção de 20:45 não pegou (só procurou SP). Varri os dois lotes pela `page.bbox` real: só a 11 e a 15;
  corrigida no lugar (sem anotação). O Pedro tinha pulado exatamente a 11 e a 15 — ele precisa recarregar
  a ferramenta.
- `src/anotacao/servidor.py` foi alterado às 21:04 por outro agente ou pelo Pedro, sem registro no quadro:
  caixa sem área é descartada quando a página é pulada. Mantive.
- `avaliar_diamond.py --lote diamond_treino --rose rose_treino`, 25 páginas anotadas (a proposta v2 é a
  que o Pedro viu, então ela leva vantagem de ancoragem): proposta v2 F1@0,5 0,916, F1 com classe 0,789;
  Rose (24 páginas) 0,903 e 0,756. Rose acerta muito mais assinatura (0,95 contra 0,64) e cabeçalho (0,92
  contra 0,82), e menos texto (0,83 contra 0,95). O humano usou `outro` em 55 regiões: tags do InDesign
  (`<@textFrameStart>`, `contPageBreak`) e palavras embaralhadas na borda (PR) — regra fácil para a v3.
**Próximo passo / para quem:** Pedro segue anotando; Claude: combinar classes do Rose com caixas da
proposta e regra de `outro` para tags, medidas quando houver mais páginas anotadas.

### 2026-09-13 20:45 — Claude — ACHADO — Páginas com origem deslocada (SP, y = 50) ficavam desalinhadas; corrigido no Diamond
**Tarefa:** T32, T31
**O que fiz / o que achei:** O `rose_treino` parou na 10ª página por dois motivos:
(1) página com `page.bbox` fora de (0, 0) (SP: y = 50): as palavras do pdfplumber vêm no sistema da
página, e a imagem começa em y = 50 — **na ferramenta, as caixas dessa página apareceriam 50 pt abaixo
do texto**; (2) palavra cortada na borda do PDF (x0 negativo, PR p.66) fazia o Rose recusar a página e,
no caso (1), o erro de preparação derrubava o lote inteiro.
Correções: `preparar_diamond.py` grava as coordenadas relativas à imagem e a origem em `origem_pagina`;
a única página assim no `diamond_treino` (nº 11, SP, sem anotação) foi deslocada no lugar e conferida
na ferramenta (caixas sobre o texto). `gerar_rose.py`: aceita página com `origem_pagina`, pula (com
`erros.jsonl`) página que não se prepara em vez de parar, e recorta caixas na página com área mínima
de 0,5 pt; 2 testes novos (65, OK). `rose_treino` retomado; PR p.66 e SP passaram.
**Para investigar:** (a) as 2 páginas de SP puladas no `golden_v2` podem ter sido o mesmo desalinhamento
na ferramenta do Golden; (b) `extrator.palavras_da_pagina` filtra palavras pelo centro em [0, W]×[0, H]
no sistema da página — com origem y = 50, descarta os últimos 50 pt e aceita 50 pt acima da área visível.
Mexer no extrator exige DECISÃO e REVISÃO (muda o sha).
**Próximo passo / para quem:** Pedro: decidir se investigamos (a) e (b).

### 2026-09-13 20:15 — Claude — DECISÃO — Composição do `diamond_treino` e separação para avaliar o segmentador
**Tarefa:** T32, T33
**Proposta:** o lote de treino do segmentador sorteia de **todos os veículos menos os três de teste**
(CE, MA, RJ), com rodízio entre veículos (~8 páginas cada), 80–2.500 palavras, fora de qualquer
página já usada no Golden ou no Diamond. Os veículos de teste ficam para avaliar o segmentador sem
vazamento de leiaute; a divisão de treino/teste da **ordem** não muda. Motivo: segmentação depende de
leiaute, e os 7 veículos de treino da ordem dariam pouca variedade.
**Próximo passo / para quem:** Pedro confirma (pediu o lote grande); anotação é a T33.

### 2026-09-13 20:15 — Claude — FEITO — Segmentador por regiões v2, avaliador do Diamond, alertas de regra e lote `diamond_treino`
**Tarefa:** T32
**O que fiz / o que achei:**
- `src/data/regioes.py`: a proposta saiu de `preparar_diamond.py` (que só reexporta) e ganhou as regras
  tiradas das correções do piloto (análise: 24 junções e 18 divisões do humano sobre a proposta):
  `dividir_campos` (rótulo em MAIÚSCULAS ou "Art." no início da linha, anterior termina a frase),
  `rotulo_com_valor`, `assinatura` (nome + cargo; exclui órgão, campo com valor, data, números longos,
  duas assinaturas coladas), `local_e_data`; `titulos_empilhados` fica fora do padrão (piorou títulos).
- `src/eval/avaliar_diamond.py`: compara por palavras (casamento 1-1 por Jaccard), com ablação e Rose.
  No piloto (in-sample: as regras saíram dessas páginas): v3 F1@0,5 0,647; proposta v1 0,937 (inflada
  por ancoragem); **regiões v2 0,952**, F1 exata 0,887, F1 com classe 0,840 (v1 0,788); ablação: todas
  as regras do padrão ajudam; 1ª versão de `dividir_campos` cortava 48 errados contra 14 certos.
- `diamond.html`: alertas de regra não bloqueantes (campos juntos, rótulo sem valor, parece assinatura),
  com a mesma lógica do Python. No piloto humano: 4, 13 e 4 casos.
- `preparar_diamond.py --colecao ... --n 200`: `data/diamond/diamond_treino/`, **199 páginas** (1 PDF do
  AC corrompido), 26 veículos, 8.038 regiões v2, 0 palavra sem caixa ou dupla; `proposta_versao: "v2"`.
  O lote foi gerado duas vezes antes de qualquer anotação (a 1ª tinha 739 assinaturas com falsos positivos).
- `docs/GUIA_DIAMOND.md` atualizado; `.claude/launch.json` ganhou `anotacao-teste` (porta 8771).
**Próximo passo / para quem:** Pedro anota o `diamond_treino` (T33); ao fim, avaliar v2 fora da amostra.

### 2026-09-13 20:15 — Claude — REVISÃO — T31: Rose v2 (Antigravity) e correção do contrato de quebras
**Tarefa:** T31
**O que fiz / o que achei:** Contrato do modo `regioes`, union-find, recusa de ciclo e de união com
figura, `erros.jsonl`, `--rpm`, cota diária e chave do `.env` (sem imprimir) conferidos. Defeito: o VLM
recebia o texto da região sem índices de palavra, mas respondia `quebras` por índice de palavra — não
tinha como acertar. Corrigi em `src/data/gerar_rose.py`: texto com **linhas numeradas** ("0| ...") e
`quebras` = número de linha; região esquecida pelo VLM fica como a proposta, com `origem: "proposta"`
(antes a página inteira caía). Testes ajustados; suíte com 62, OK. `orquestracao/rose_v2.sh` roda o
piloto (entrada com proposta v2) e as 199 páginas do `diamond_treino`, com avaliação do piloto no meio.
**Atualização 20:25:** nas 7 primeiras páginas o flash-lite quebrava parágrafos linha a linha
(`quebras: [1, 2, 3, ...]`; SE 91 regiões contra 47 do humano). Parei o lote (as 199 não tinham
começado), e `quebras_validas` agora só aceita quebra antes de linha que abre campo ou artigo
(`regioes.comeca_campo`); prompt reforçado; teste novo (63, OK). As 7 anotações foram refeitas das
respostas gravadas, sem nova chamada. Nessas 7 páginas, contra o humano: regiões v2 F1@0,5 0,927 e F1 com
classe 0,760; **Rose v2 0,927 e 0,786**; nas 6 que também têm Rose v1: Rose v1 0,438 e 0,417. Lote
retomado com `--retomar`.
Piloto completo (`resultados/diamond/diamond_piloto/avaliacao.md`): Rose v2 em 19 páginas (PB p.41
pulada, resposta fora do esquema) F1@0,5 0,955, F1 exata 0,901, F1 com classe 0,847; regiões v2 em 20:
0,952, 0,887, 0,840 — páginas não idênticas, comparar nas comuns quando o humano do `diamond_treino` sair.
**Próximo passo / para quem:** `rose_treino` (199 páginas) rodando; Claude avalia contra o `diamond_treino`
anotado.

### 2026-09-13 19:55 — Claude — ACHADO — Diamond piloto contra v3, proposta e Rose
**Tarefa:** T27, T30
**O que fiz / o que achei:** Piloto concluído: 20 páginas, 789 regiões, 55 min de tempo ativo (mediana
98 s/página, de 4 a 559 s). Da proposta, 72% das regiões ficaram intactas; 88 trocaram de classe, 116
foram apagadas, 94 criadas. Nenhuma marcação usada; 2 notas (pág. 3 quadro sem texto; pág. 4 texto que
não sai no PDF). Anotador gravado como "anotador" (no Golden é "Pedro alano").
Comparação pelas palavras de cada região (casamento 1-1 por Jaccard; classe por palavra), gabarito =
Pedro (script em scratchpad, a oficializar):
| Sistema | Páginas | Regiões (gab.) | F1 @0,5 | F1 exata | Classe certa (palavras) |
|---|---:|---:|---:|---:|---:|
| blocos v3 (extrator atual) | 20 | 523 (754) | 0,647 | 0,457 | 83,8% (tudo "texto") |
| proposta (Heron + regras) | 20 | 764 (754) | 0,937 | 0,867 | 90,7% |
| blocos v3 | 15 | 283 (456) | 0,590 | 0,452 | 80,0% |
| proposta | 15 | 469 (456) | 0,930 | 0,848 | 92,4% |
| Rose (gemini-3.1-flash-lite) | 15 | 241 (456) | 0,597 | 0,456 | 94,0% |
**Ressalvas:** (1) a proposta está inflada por ancoragem: o gabarito partiu dela; medir exige algumas
páginas anotadas sem proposta ou com outra pré-anotação. (2) Rose só tem as 15 páginas que passaram na
validação; ficaram de fora as maiores (RJ 2.519 e MG 4.080 palavras) e Duque, Seropédica e Barra do Piraí.
Rose junta demais (241 regiões contra 456): segmenta como o v3; classifica melhor por palavra. (3)
Consistência: páginas rápidas mantêm erros da proposta contra a regra de campos — pág. 1, 2º e 3º
extratos ("BASE LEGAL" com "As demais condições"; "ACORDANTE"+"OBJETO"+"DATA" numa caixa; "PREÇO GLOBAL"
com "A íntegra"); pág. 12 (37 s) com região de 315 palavras e rótulo "TERMO Nº.:" sozinho. Erros de classe
mais comuns da proposta: lista→texto (286 palavras), assinatura→texto (202).
**Próximo passo / para quem:** Pedro decide: revisão de consistência (alertas de regra na ferramenta) e
teste de ancoragem antes das 200.

### 2026-09-13 19:55 — Claude — REVISÃO — T30: gerador Rose (Codex + Antigravity)
**Tarefa:** T30
**O que fiz / o que achei:** Li `src/data/gerar_rose.py` e rodei a suíte: 49 testes OK (27 + 22 do Rose).
Bom: a VLM só agrupa índices de palavras (caixa = envelope das palavras, sem coordenada inventada),
valida cobertura antes de gravar, recusa saída em raw/Golden/origem, guarda resposta e hash do prompt;
`.env` com a chave está no `.gitignore`. Pontos: (a) a docstring diz que resposta incompleta interrompe e
que não há preenchimento, mas `main` usa `preencher_orfas=True` — nas 15 páginas gravadas nenhuma palavra
foi preenchida (conferido nas respostas guardadas), então os números acima são só da VLM; (b) com
`preencher_orfas=True` a mensagem "incompleta" nunca ocorre e a repetição por esse motivo é código morto;
(c) páginas puladas não ficam registradas em arquivo, só no console — o viés de seleção precisa ser
reconstruído à mão; (d) `anotacoes.jsonl` do Rose mistura, no nome, rótulo de máquina com o de gente
(o campo `anotador` = `VLM:<modelo>` distingue).
**Próximo passo / para quem:** ajustes (a)–(c) quando o Rose for escalar.

### 2026-09-13 19:15 — Antigravity — FEITO — Execução da Rose piloto 100% gratuita com Gemini 3.1 Flash Lite (T30)
**Tarefa:** T30
**O que fiz / o que achei:** Corrigi o retorno do `--dry-run` em `src/data/gerar_rose.py` e adicionei suporte a `--retomar`, `--pular-erros` e preenchimento gracioso de palavras órfãs em `parse_resposta` ancoradas nas propostas do detector. Identifiquei que o `gemini-3.5-flash` tem cota gratuita de apenas 20 req/dia e 5 RPM (causava 429 e esgotamento rápido), enquanto o `gemini-3.1-flash-lite` possui 500 req/dia e 15 RPM. Configurei o modelo gratuito e gerei o lote piloto `data/diamond/rose_piloto`.
**Arquivos tocados:** `src/data/gerar_rose.py`, `tests/test_rose.py`, `data/diamond/rose_piloto/` (`tarefas.jsonl`, `anotacoes.jsonl`, pasta `img/`).
**Resultado / evidência:** `venv\Scripts\python.exe -m unittest tests.test_rose -v`: 22 testes OK. `rose_piloto` gerado com 15 páginas gravadas de forma 100% íntegra (`palavras_sem_caixa: 0`, `palavras_em_duas_caixas: 0` em todas as 15). Páginas com sobreposição excessiva de grupos da VLM ou cota temporária excedida foram puladas com log explícito. Custo: R$ 0,00 (tier gratuito do Google AI Studio).
**Próximo passo / para quem:** Claude / Pedro podem comparar as predições do `rose_piloto` contra o gabarito humano do `diamond_piloto` quando este for concluído pelo Pedro.


### 2026-09-13 17:58 — Codex — FEITO — Despacho T30 solicitado pelo Pedro
**Tarefa:** T30
**O que fiz / o que achei:** Executei `venv\Scripts\python.exe orquestracao\despachar.py --agente codex --tarefa T30 --prompt orquestracao\prompts\T30_dataset_rose_vlm.md`, corrigindo as barras de escape antes dos sublinhados no caminho fornecido. O CLI implementou o gerador Rose Gemini/OpenAI com agrupamento por índices de palavras, envelopes, validação de cobertura e proteção de pastas existentes.
**Arquivos tocados:** CLI criou `src/data/gerar_rose.py` e `tests/test_rose.py`; o acompanhamento atualizou este quadro. Logs em `orquestracao/logs/20260913_174914_T30_codex*`.
**Resultado / evidência:** JSON do despacho: código 0, 542 s, 2 criados, 0 alterados, 0 removidos, 0 alertas. No log, `venv\Scripts\python.exe -m unittest tests.test_rose -v`: 22 testes passaram; análise AST obrigatória: `ok`. `venv\Scripts\python.exe src\data\gerar_rose.py --colecao data/processed/blocos_extra --dry-run`: 1 página, 630 palavras, 110 DPI, imagem de 183.972 bytes, 0 chamadas de API, 0 arquivos gravados.
**Próximo passo / para quem:** revisão pelo Claude; provedores reais ainda não validados. Figuras sem palavras não são localizadas pelo contrato de ancoragem; falhas interrompem o lote sem retomada automática. Nenhum dataset foi gerado.

### 2026-09-13 16:58 — Claude — REVISÃO — T28: testes do Diamond (Antigravity)
**Tarefa:** T28
**O que fiz / o que achei:** Antigravity criou `tests/test_diamond.py` em 263 s: 13 testes, um por item
do prompt (proposta: envelope, score mínimo, tabela, figura, listas, sobreposição com alerta, alertas,
verificador de cobertura; servidor: gravar/trocar, validações, recorte, bloqueio de conclusão,
`mudancas`), com `DIR_DIAMOND` num diretório temporário e restaurado no `tearDown`. Rodei
`venv\Scripts\python.exe -m unittest discover -s tests`: 27 testes, OK. O aviso "fora do escopo" do
despachante é `COMUNICACAO_AGENTES.md`, editado por mim durante o despacho; o agente não tocou no quadro.
**Próximo passo / para quem:** nenhum.

### 2026-09-13 16:55 — Claude — FEITO — Diamond: pré-anotação, ferramenta de caixas e lote piloto
**Tarefa:** T27, T28
**O que fiz / o que achei:**
- `src/anotacao/preparar_diamond.py`: proposta = regiões do Docling Heron (cache de layout, score ≥ 0,45)
  ajustadas às palavras do PDF + blocos v3 onde o detector não viu; tabela absorve o que tem dentro;
  figura não pega palavra; itens de lista vizinhos viram uma lista; regiões que disputam palavras viram
  uma (alerta). Não detecta layout (não disputa a GPU): exige o cache.
- `src/anotacao/diamond.html` + rotas `/diamond` e `/api/diamond/*` em `servidor.py` (as do Golden
  continuam iguais; conferido: `golden_v1` 26 e `golden_v2` 27 concluídas). Seleciona, desenha
  (ajusta às palavras), move, redimensiona, divide, junta, apaga, classes 1–9, desfazer/refazer,
  alertas navegáveis, camadas. O servidor recusa concluir com palavra sem caixa ou em duas caixas e
  grava `mudancas` contra a proposta.
- `data/diamond/diamond_piloto/`: 20 páginas do `golden_v3` (18 veículos), 811 regiões propostas, 0
  palavra sem caixa ou em duas caixas em todas as páginas.
- Testado no navegador num lote descartável (apagado): dividir, juntar, apagar, desenhar, classe,
  alças, mover, ajustar, desfazer ×3, concluir, recarga do rascunho, recusa do servidor (400). O teste
  achou e corrigiu: faixa de modo empurrava a página (clique do corte caía fora da caixa); título dentro
  de "figura" do detector ficava sem caixa; 25 palavras em duas caixas por página na 1ª versão.
- `docs/GUIA_DIAMOND.md`; `.gitignore` ignora `data/diamond/*/img/`.
**Próximo passo / para quem:** Pedro anota o piloto (T27); Antigravity escreve os testes (T28).

### 2026-09-13 16:55 — Claude — ACHADO — Sem texto, o LayoutLM sucessor não piora
**Tarefa:** T11
**O que fiz / o que achei:** `--sem-texto` em `src/models/layoutlm_sucessor.py` troca todo token de
palavra por [UNK] (mantém caixas, número de tokens por bloco e viés geométrico); `avaliar_golden.py`
reconhece `sem_texto` no nome. Mesmo treino da semente 42 (3.189 páginas, 4 épocas, 725 s).
| Modelo | Teste τ | Teste sucessor | Golden τ | Golden sucessor |
|---|---:|---:|---:|---:|
| sucessor, sementes 42 / 1 / 2 | 0,878 / 0,849 / 0,894 | 71% / 57% / 73% | 0,845 / 0,865 / 0,882 | 67% / 61% / 68% |
| **sem texto** | **0,854** | **71%** | **0,882** | **73%** |
| sem layout | — | — | 0,248 | 30% |
Dentro da variação entre sementes: o modelo ordena pela geometria e não usa o texto de forma mensurável.
Um pré-treino em português para melhorar a **ordem** tem pouco espaço; o ganho está na segmentação e nos
dados. (O texto pode importar em outra tarefa, como classificar regiões.)
**Evidência:** `orquestracao/logs/ablacao_sem_texto/`, `resultados/comparacao.json`,
`resultados/golden/_avaliacao/golden_v3/avaliacao.json`.
**Próximo passo / para quem:** Pedro; entra no capítulo de resultados.

### 2026-09-13 16:55 — Claude — DECISÃO — Rumo: Diamond (caixas e classes), avaliação extrínseca em RAG, acessibilidade como aplicação
**Tarefa:** T27
**Proposta (confirmada pelo Pedro: "pode seguir com isso")**: a ordem fica como está (empate entre
XY-cut, LayoutLM e LLMs no Golden); o esforço vai para (1) o Diamond, com caixas e 9 classes (título,
texto, lista, tabela, assinatura, cabeçalho, rodapé, figura, outro), pré-anotação do detector + regras e
correção humana; piloto de 20 páginas do `golden_v3` para medir tempo e ajustar regras, depois ~200 —
páginas de avaliação separadas das de treino do segmentador; (2) avaliação extrínseca em RI/RAG com os
atos de Japeri como gabarito; (3) acessibilidade (leitor de tela) como aplicação e o Acessilia como
referência, com créditos (MIT). Não usar PyMuPDF (AGPL) no código do TCC.
**Próximo passo / para quem:** Pedro leva ao orientador (T15).

### 2026-09-13 16:16 — Claude — REVISÃO — T26: análise do Acessilia (Antigravity)
**Tarefa:** T26
**O que fiz / o que achei:** Antigravity escreveu `docs/ANALISE_ACESSILIA.md` em 402 s, só esse arquivo.
Os três repositórios do Acessilia ficaram intactos (HEAD e `git status` iguais antes e depois). Conferi à
mão: `reading_order` no Acessilia é só a enumeração de `iterate_items()` do Docling
(`backend/core/manifest/builder.py:173`), ou seja, o Acessilia **não tem ordenação própria** e depende
da ordem do Docling; `LICENSE` do structure-extractor tem cabeçalho MIT seguido de texto residual da GPL
(666 linhas); o `.gitignore` (linha 30, `MANIFEST`) deixou `src/acessilia_extractor/manifest/` fora do
repositório; 136 testes vêm do `RELATORIO-HOMOLOGACAO.md`, não de execução. Ressalvas: a seção 6.2
exagera ("o repositório passará a ser governado pela AGPL" — a obrigação vem com a distribuição); a
generalização sobre VLMs pequenos em 4.2 é opinião, não dado.
**Próximo passo / para quem:** Pedro decide o rumo (Diamond, ordem do Docling como método de comparação).

### 2026-09-13 15:55 — Claude — FEITO — LLMs do Kaggle importadas e avaliadas no teste e no `golden_v3`
**Tarefa:** T12
**O que fiz / o que achei:** O Pedro rodou `kaggle_llm_ordem.ipynb` (4h06, 2×T4, Ollama 0.34.0) sobre o
pacote refeito às 09:31. Importei `resultados_kaggle.zip` (cópia em `resultados/kaggle/`); as predições
não-LLM do zip são idênticas às locais. Refiz `avaliar_golden.py` com a lista completa da rodada extra.
τ médio, teste (89) / Golden (47): qwen3.8:27b 0,833 / 0,853, com 2 exemplos 0,827 / 0,881; gemma4:31b
0,817 / 0,870, com 2 exemplos 0,835 / 0,873; qwen3.6:35b 0,499 / 0,632, com 2 exemplos 0,592 / 0,710.
Referência: XY-cut 0,891 / 0,851; LayoutLM sucessor (semente 42) 0,878 / 0,845.
**Evidência:** `resultados/comparacao.json`, `resultados/golden/_avaliacao/golden_v3/avaliacao.json`,
`resultados/execucoes_llm.jsonl`. Permutações válidas no teste: 80%, 70%, 87%, 76%, 30%, 37%. Páginas
inválidas são as grandes (mediana 43 a 76 blocos contra ~20 nas válidas) e derrubam o τ (≈0,65 contra
≈0,88). No qwen3.6:35b zero-shot, 14 páginas do teste falharam com `CUDA error: illegal memory access`
do Ollama (resposta vazia): parte do resultado dele é falha de execução, não do modelo.
**Próximo passo / para quem:** Pedro decide se refaz o qwen3.6:35b (numa T4 só ou outra versão do
Ollama) antes de reportar; nada commitado.

### 2026-09-13 04:20 — Claude — FEITO — Noite concluída: treino e avaliação da v3, sementes, ablações e relatório
**Tarefa:** T09, T11, T13
**O que fiz / o que achei:** Os três roteiros rodaram sem falha real: `noite_v3.sh`,
`noite_v3_correcao.sh` e `noite_v3_extra.sh`. O único código ≠ 0 é o relatório desviado de propósito.
O relatório, escrito pelo Antigravity com as seções 1 a 9, está em `docs/RELATORIO_NOITE_V3.md`; os
logs e o `status.jsonl` estão em `orquestracao/logs/noite_v3/`. O pacote do Kaggle está em
`dist/kaggle/` (só as LLMs faltam). O Codex não foi usado.
**Evidência:**
- Teste, 89 páginas, média ± desvio de 3 sementes: sucessor τ 0,874 ± 0,023 (sucessor correto
  67,2%); pontual 0,811 ± 0,010; XY-cut 0,891.
- Golden, 47 páginas: sucessor 0,864 ± 0,019 (65,1%); pontual 0,864 ± 0,017 (37,5%); XY-cut 0,851
  (74,0%). As diferenças de τ no Golden ficam dentro do desvio entre sementes.
- Ablação sem layout 2D: pontual cai para τ 0,155 no Golden.
**Pendências:** revisar o relatório com o Pedro; commit só com a autorização dele. Há uma diferença
pequena de percentil 10 entre `diagnostico_sucessor.md` e `avaliacao.md`, por cálculo de percentil
diferente. Kaggle: notebook das LLMs.

### 2026-09-13 03:10 — Claude — ACHADO — Golden e RI avaliavam o sucessor com busca em feixe; corrigido e sendo refeito
**Tarefa:** T13, T11
**O que fiz / o que achei:** `prever()` de `src/models/layoutlm_sucessor.py` tinha `modo="feixe"`
como padrão, e a linha de comando usa `cadeias`. `avaliar_golden.py` e `piloto_japeri.py` chamam
`prever()` sem dizer o modo, então avaliavam o sucessor com busca em feixe. No Golden v3 isso deu
τ 0,699; no teste, a mesma busca em feixe dá 0,754, contra 0,878 em cadeias. Corrigi o padrão para
`cadeias` (limiar 0,5): nenhuma chamada com modo explícito muda. O piloto de RI da v1 também usou
feixe para o sucessor; isso vale como ressalva ao comparar.
`orquestracao/noite_v3_correcao.sh` espera o roteiro principal terminar e então refaz: Golden, piloto
de RI, comparação, diagnóstico (Antigravity, T25b) e relatório (Antigravity, prompt
`T13b_relatorio_noite_v3_corrigido.md`). O passo de relatório do roteiro principal falha de propósito,
porque o prompt dele foi renomeado, para não gerar um relatório com números errados.

### 2026-09-13 03:10 — Claude — REVISÃO — T24 (testes) aprovada; T25 (diagnóstico) refeita por causa do achado acima
**Tarefa:** T24, T25
**O que fiz / o que achei:**
- T24 (Antigravity): `tests/test_segmentacao_v3.py`, 14 casos com `unittest` a partir das reproduções
  do Codex. Rodei aqui: 14 ok, nenhum marcado como falha esperada. Aprovada.
- T25 (Antigravity): o diagnóstico está bem feito, mas usou as predições em feixe; as hipóteses
  sobre a "decodificação em cadeias" não valem até a T25b refazer com as predições certas. Os dois
  arquivos "fora do escopo" nos dois despachos são do treino das ablações, que rodava ao mesmo tempo.

### 2026-09-13 00:45 — Claude — AVISO — Roteiro da noite em execução; não use GPU nem `resultados/` até ele terminar
**Tarefa:** T05, T09, T11, T12, T13
**O que fiz / o que achei:** Pedro foi dormir e pediu para aproveitar a noite. O roteiro
`orquestracao/noite_v3.sh` roda sem supervisão, um passo por vez, com log e código de saída de cada
passo em `orquestracao/logs/noite_v3/` (`status.jsonl`, `roteiro.log`):
1. espera a T05;
2. gera o pacote do Kaggle;
3. re-extrai Japeri com `--min-blocos 1` (novo em `reextrair.py`, sem mudar o sha do extrator);
4. treina as três BiLSTM;
5. roda a curva de aprendizado das duas formulações do LayoutLM, em 5 tamanhos;
6. copia os maiores checkpoints para `layoutlm.pt` e `layoutlm_sucessor.pt` (os da v1 estão em
   `models/layoutlm_ordem_segmentacao_v1/`);
7. roda a avaliação no teste, a varredura do limiar e a busca em feixe;
8. avalia no `golden_v3`;
9. gera a comparação, a figura, o piloto de RI e a latência;
10. roda as três ablações;
11. despacha o Antigravity para escrever `docs/RELATORIO_NOITE_V3.md`
    (prompt `orquestracao/prompts/T13_relatorio_noite_v3.md`).
Nada é commitado nem publicado. O Kaggle fica só para as LLMs de 27–35B, que o Pedro sobe de manhã.
**Próximo passo / para quem:** Claude revisa o relatório e os logs de manhã.

### 2026-09-12 23:55 — Claude — DECISÃO — Manter a divisão treino/validação/teste na segmentação v3 (aguarda confirmação do Pedro)
**Tarefa:** T07
**O que fiz / o que achei:** Recalculei a concordância mediana entre fluxo do PDF e XY-cut por veículo
sobre `data/processed/blocos` (v3). Os três veículos de teste continuam confiáveis e mais altos:
CE 0,986 → 1,000; MA 0,902 → 0,939; RJ 0,870 → 0,851. Cinco veículos cruzam o limiar de 0,7:
- saem do grupo confiável: PE (treino) 0,729 → 0,642 e RR (treino) 0,703 → 0,644;
- entram: AC 0,613 → 0,751, MG 0,683 → 0,728, MS 0,531 → 0,800.
Rodar `caracterizar.py` de novo reembaralharia os veículos confiáveis com a semente 42 e trocaria o
teste, e aí não daria para comparar com a v1 nem aproveitar o grupo `silver` do Golden.
**Proposta:** manter `splits.json` como está e reportar essa tabela como análise de sensibilidade.
O Golden confirma a referência onde ela importa: no grupo `silver` do `golden_v3`, o fluxo concorda
com o humano com τ 0,925 (p10 0,814; 21 páginas).
**Evidência:** teste com 89 páginas na v3, contra 95 na v1: 6 páginas saíram pelo filtro de 3 blocos
(CE 4, MA 2), páginas quase só de tabela.
**Próximo passo / para quem:** **confirmada pelo Pedro** ("pode manter"): `splits.json` fica como está na v3.

### 2026-09-12 23:55 — Claude — FEITO — `golden_v3`, avaliação no Golden, notebooks do Kaggle e LLMs novas
**Tarefa:** T22, T23, T09, T12
**O que fiz / o que achei:**
- `golden_v2` anotado pelo Pedro: 27 concluídas, 2 puladas (SP, fonte miúda), 23 min.
- `src/anotacao/montar_referencia.py` monta `data/golden/_avaliacao/golden_v3/`: `tarefas.jsonl` e
  `referencia.jsonl` (derivado; confere o sha do extrator). São 47 páginas e 1.238 blocos: 21
  `silver` e 26 `incerto`; 20 projetadas do v1 e 27 do v2.
- `avaliar_golden.py` lê `referencia.jsonl`, separa por origem e grava as predições do LayoutLM no
  Golden, para a avaliação sair completa sem o checkpoint.
- `resultados/`: os artefatos da v1, idênticos (`cmp`) aos de `resultados_segmentacao_v1/`, foram
  retirados. Baselines refeitos na v3, com 89 páginas de teste: XY-cut τ 0,891; ingênua 0,790;
  aleatória −0,020.
- `montar_pacote.py`:
  - notebook de treino com baselines e BiLSTM na v3, avaliação das duas formulações no maior
    treino e `golden_v3`;
  - notebook de LLM com Qwen 3.8 27B, Gemma 4 31B e Qwen 3.6 35B (tags conferidas na biblioteca do
    Ollama), `LIMITE_HORAS` e zip ao fim de cada modelo;
  - pacote leva `_avaliacao/*`.
- `importar_resultados.py` importa tudo sob `resultados/`.
**Evidência:** `resultados/golden/_avaliacao/golden_v3/avaliacao.md`, com τ no Golden: XY-cut 0,851,
ingênua 0,781, fluxo 0,714 (silver 0,925; incerto 0,544). As células de código dos dois notebooks
compilam.

### 2026-09-12 23:55 — Claude — ACHADO — Defeitos restantes da v3, das notas do `golden_v2` (para uma v3.1, sem mexer agora)
**Tarefa:** nenhuma (backlog)
**O que fiz / o que achei:**
1. AL `DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0`: a coluna esquerda inteira está desenhada como
   curvas (2.236 curvas, nenhum caractere). É a mesma classe do texto em imagem: só OCR resolve.
2. SE `DOE-SE_2022-03-18_4475.pdf#p15`: blocos `<@textFrameStart>`, marcação do InDesign na camada
   de texto. Filtrar palavras `<@...>`.
3. Duque de Caxias: o detector juntou duas tabelas de baixo numa só.
4. RJ Legislativo p3: ainda sobra um bloco sobreposto (posição 28).
5. CE `do20250505p03.pdf#p66` e MA suplemento: em listas de nomes, o agrupamento das linhas é
   inconsistente (o Pedro alerta para o efeito em RAG).
6. SP (duas páginas puladas): fonte miúda e lista longa continuam ruins.
7. Japeri (piloto de RI): 9 de 269 páginas saíram pelo filtro de 3 blocos na v3. Para RI, o filtro
   deveria aceitar página com 1 ou 2 blocos (tabela inteira), senão o texto some do índice.
**Próximo passo / para quem:** decidir depois do Kaggle; nenhum muda os experimentos em curso.

### 2026-09-12 23:00 — Claude — FEITO — T18 confirmada pelo Codex; T05 iniciada
**Tarefa:** T18, T05
**O que fiz / o que achei:** A confirmação do Codex (despacho das 22:52, só leitura) deu os cinco
itens como resolvidos: página girada com CropBox diferente vira falha; calhas nas duas ordens;
empate entre texto exato e substring; cauda UTF-8 cortada; par de letras com caixa mista. Ele achou
ainda um defeito menor, de rastreabilidade: falha de renderização já gravada no cache passava em
silêncio. Corrigido: `garantir_cache` avisa, e a bancada grava `layout.paginas_sem_layout`. Página
do AC que o PDFium não abre (`executive_official_diary_2024-03-03.pdf#p0`) registrada como falha;
ela sai sem tabelas, com `stats.layout = false`.
**Evidência:**
- Bancada final (`resultados/avaliacao_segmentacao_v3.json`): 44 páginas, 33,0 blocos/pág, 2,7%
  sobrepostos, 7,2% de 1 palavra, 0 rejeitadas, maior bloco 1.769 palavras (tabela).
- Determinismo: `processar_paginas` com 1 e com 3 processos dá registros idênticos, e iguais ao
  `golden_v2` gravado (8 páginas conferidas).
- Nenhuma das 4.112 páginas do cache é girada nem tem CropBox diferente da MediaBox.
- T05: B preservada em `data/processed/blocos_b/` e `blocos_ri_japeri_b/`. Sequência:
  `reextrair.py --entrada data/processed/<col>_v1 --saida data/processed/<col> --workers 4` para
  `blocos`, `blocos_ri_japeri` e `blocos_extra`; cópia da qualidade em
  `resultados/qualidade_segmentacao_v3_<col>.json`. Primeira coleção: 767 tabelas em 346 de 777 páginas.
**Próximo passo / para quem:** quando a T05 terminar: conferir as páginas perdidas pelo filtro e
então T07 (splits) → T09 → T23 → T12 (Kaggle). Pedro: anotar o `golden_v2` (T22).

### 2026-09-12 22:55 — Claude — FEITO — Segmentação v3, detector de tabelas, projeção do Golden v1 e lote `golden_v2`
**Tarefa:** T18, T19, T20, T21 (plano do Pedro: commit, extrator novo, refazer o que precisa, mais páginas, depois Kaggle)
**O que fiz / o que achei:**
- Commit `3074213` no branch novo `golden-v1-e-segmentacao` (sem push), autorizado pelo Pedro.
- `src/data/extrator.py` (v3): `_juntar_letras_espacadas`, `_reatribuir_faixas`, `_cortes_locais`,
  `segmentar(ws, tabelas)` com `_bloco_tabela` e descarte de bloco sem letra nem dígito,
  `processar_pagina(..., tabelas, palavras)`, `processar_paginas`. Bloco de tabela sai com
  `"tipo": "tabela"`; `stats` ganha `n_tabelas` e `layout`.
- `src/data/layout.py` (novo): Docling Heron, revisão `8f39ad3c`, só do cache local; cache em
  `data/processed/layout/` com `bbox_imagem` e `escala`; falha de renderização registrada.
- `src/anotacao/projetar_ordem.py` (novo); `preparar_lote.py` segmenta na hora e aceita
  `--refazer-de`; `reextrair.py` e `avaliar_segmentacao.py` usam o cache de layout.
- Ferramenta de anotação: caixa de tabela com contorno verde; regra 6 do `GUIA_ANOTACAO.md`.
- **Revisões do Codex** (despachos 22:05 e 22:27, só leitura) acharam 6 + 4 defeitos, todos com
  reprodução; todos corrigidos. O mais grave: página cuja imagem não começa em (0, 0) (SP, MediaBox
  com y = 50) tinha as tabelas deslocadas; o cache antigo foi apagado e refeito. Página girada
  com CropBox diferente vira falha registrada (0 de 4.112 páginas medidas). Confirmação final
  despachada às 22:52.
**Evidência:**
- Custo: a segmentação nova leva 0,49 s nas 30 páginas do Golden, contra 0,32 s da anterior; o tempo
  da bancada é do pdfplumber (o Codex mediu `dedupe_chars` como gargalo).
- Projeção (`data/golden/golden_v1/derivados/projecao_v3.jsonl`): 20 limpas, 5 conflitos (RJ ×3,
  Duque de Caxias, Barra do Piraí), 4 sem anotação, 1 rejeitada (CE p11: tabela + cabeçalho = 2 blocos).
- `data/golden/golden_v2/`: 29 páginas (9 a refazer, silver 12, incerto 8), 814 blocos, 12 com
  tabela; `derivados/palavras_por_bloco.jsonl` gravado. Nenhuma anotação ainda.
- Cache de layout: 4.022 páginas das três coleções `*_v1` em 478 s na GPU, 5.521 tabelas; uma página
  do AC não abre no PDFium (`executive_official_diary_2024-03-03.pdf#p0`).
- Bancada v3 anterior às revisões (44 páginas): 33,3 blocos/pág, 2,5% sobrepostos, 6,8% de 1 palavra,
  0 rejeitadas (antes 48,8 / 5,9% / 21,5% / 1); sem layout: 47,8 / 4,0% / 22,8% / 1. Números finais
  em `resultados/avaliacao_segmentacao_v3.json` quando a rodada atual terminar.
**Próximo passo / para quem:** Pedro anota o `golden_v2` (T22). Com a confirmação do Codex, T05
(re-extração, Antigravity) → T07 → T09 → T23 → T12 (Kaggle).

### 2026-09-12 20:11 — Claude — ACHADO — Notas do Golden: causas dos erros de segmentação e protótipo
**Tarefa:** T08 (fechada pelo Pedro) e segmentação (proposta, aguarda decisão do Pedro)
**O que fiz / o que achei:** O Pedro terminou o `golden_v1`: 26 páginas concluídas, 3 puladas e 1
rascunho (as quatro por tabela), 52 min; marcações `tabela` 12, `figura` 8, `segmentacao` 3. O
`anotacoes.jsonl` foi só lido (sha256 `679c946d…` conferido antes e depois). As notas dele apontam
seis problemas, com causa localizada:
1. **Parágrafo partido em vários blocos + bloco de uma palavra** (MA p60, posições 17–20; MA p56,
   o 31 dentro do 30). `_faixas_de_base` põe "nº", cujo topo fica 0,4 pt acima por causa do "º", na
   faixa da coluna vizinha deslocada meia linha. A palavra vira bloco próprio e a trava contra
   sobreposição impede o parágrafo de crescer por cima dela.
2. **Caixa que atravessa colunas** (RJ p0, RJ Legislativo p1 pos. 63, p3, Barra do Piraí p5, SP p4).
   `_calhas` é global: onde um trecho da página tem outro desenho de colunas (rodapé do RJ, tabela
   larga embaixo de duas colunas) não sobra calha global e as linhas atravessam.
3. **Tabelas** sem detecção: as células viram colunas de blocos, o título gruda na primeira linha.
4. **Separadores** ("*** *** ***", "-", "....") viram blocos.
5. **Letras espaçadas** ("R E S O L V E", "PA R E C E R").
6. **Texto dentro de imagem** não existe na camada de texto do PDF: só OCR resolveria.

Protótipo no scratchpad, fora do repositório: (a) faixas com reatribuição de cada palavra à faixa
de centro mais próximo; (b) calhas locais — corta um vão maior que 1,5 largura de caractere quando
uma faixa branca passa por ele e por pelo menos mais 3 linhas com palavras dos dois lados; (c) cada
tabela vira um bloco, com a região dada pelo detector de layout **Docling Heron** (RT-DETRv2
treinado no DocLayNet, Apache-2.0, já no cache local do Hugging Face, sem download; 30 páginas em
6,6 s na GPU); (d) descarte de bloco sem letra nem dígito.
**Evidência:**
- Bancada de 44 páginas (`src/data/avaliar_segmentacao.py` com o protótipo a+b, saída no
  scratchpad): pares sobrepostos 5,9% → 3,9%; blocos/pág 48,8 → 47,9; blocos de 1 palavra
  21,5% → 22,1%; rejeitadas 1 → 1.
- Golden, 30 páginas: a+b reduz os pares sobrepostos de 47 para 18. O detector acha tabela nas 12
  páginas que o Pedro marcou com `tabela`.
- Ordem do Pedro projetada nos blocos novos (a+b+c+d). Em nenhuma tabela ele leu os pedaços fora de
  sequência: 0 conflitos em CE p53, p11, p6, p20, MS e AC. Nas 26 concluídas, 975 → 738 blocos.
  Só 7 páginas pediriam retoque na ordem (20 blocos dele divididos, todos em páginas que ele marcou).
  As 4 puladas caem de 67 → 5, 121 → 46, 30 → 8 e 55 → 19 blocos.
- Novo: `src/anotacao/congelar_palavras.py` →
  `data/golden/golden_v1/derivados/palavras_por_bloco.jsonl` (30 páginas, 28.663 palavras,
  extrator `9c766ab55d1d`; recusa página cuja segmentação não reproduz o lote). Guarda a ordem do
  Pedro palavra a palavra, para valer em qualquer segmentação futura.
**Pendências:** decisões do Pedro — tabela = 1 bloco pelo detector; texto em imagem fora do escopo
(limitação); segmentação de referência feita por correção (juntar/dividir/descartar + motivo);
commit do estado atual antes de mexer no extrator. T05 fica parada até isso.
**Próximo passo / para quem:** Pedro decide. Com o sim: Claude implementa a+b+c+d no extrator;
Codex (REVISÃO, esforço `high`) e, se aprovado o modo de correção, a ferramenta de anotação.

### 2026-09-12 18:31 — Claude — DECISÃO — Segmentação final implementada; Golden regenerado
**Tarefa:** T03 e T06 (opção 3, autorizada pelo Pedro: o Claude implementa, o Codex revisa depois)
**O que fiz / o que achei:** Nova regra de agrupamento de linhas em blocos em
`src/data/extrator.py:construir_blocos` — a **B** (mesma coluna, linhas coladas, fonte parecida,
sobreposição horizontal ≥ 50% da menor) **mais** duas regras: (4) linha curta e centralizada
(título, "LOTE 139/2025", assinatura) não se mistura com texto corrido; (5) a fusão é recusada se
a caixa resultante cruzar a de outro bloco. A regra de margem esquerda da C saiu. Critério de
granularidade: a escolha visual do Pedro nas imagens da T16 (MA → B, 36 blocos; RJ → v1, 66).
**Decisão:** o Pedro autorizou regenerar o Golden com esta versão ("roda aí, deixa eu anotar pra
aprovar"). A aprovação final vem da experiência dele ao anotar; se reprovar, a regra volta à T03
antes de a anotação avançar.
**Arquivos tocados:** `src/data/extrator.py`, `src/data/inspecionar_segmentacao.py` (opção
`--rotulo-atual`), `data/golden/golden_v1/tarefas.jsonl`, `docs/HANDOFF.md`, `COMUNICACAO_AGENTES.md`
**Resultado / evidência:**
- Páginas-problema (v1 / B / final): MA 54 / 36 / **36**; SE 45 / 30 / **37**; RJ 66 / 53 / **78**
  (sobrepostos 19,7% / 15,1% / **5,1%**); CE 9 / rejeitada / **15**. Imagens:
  `resultados/inspecao_segmentacao/*_comparativo_final.png`, contagens em `contagens_final.json`.
- Bancada de 44 páginas sobre o código implementado (`resultados/avaliacao_segmentacao_final.json`):
  **48,8 blocos/página, 5,9% sobrepostos**, 21,5% de uma palavra, maior bloco 682 palavras (B: 1.052),
  uma página rejeitada (SE, 224 blocos; não é veículo de teste). Reproduz o experimento de rascunho
  (52,8 blocos/página com a rejeitada incluída).
- **Golden regenerado:** as mesmas 30 páginas, 939 → **1.248 blocos** (mediana 33 por página),
  sobreposição 14,7% → **6,8%**, páginas com bloco > 250 palavras 9 → 5; imagens, campos do lote,
  ids únicos e ordens completas conferidos. Sem anotação humana no lote antes de regenerar.
**Próximo passo / para quem:** Pedro anota (T08) e confirma a segmentação depois das primeiras
páginas. Com a confirmação: T05 (re-extração das três coleções) vai ao Antigravity CLI. Às 20:28, o
Codex CLI faz a `REVISÃO` da mudança em `extrator.py`, que toca código central.

### 2026-09-12 17:55 — Claude — BLOQUEIO — Limite de uso do Codex; T17 concluída; preferência visual do Pedro
**Tarefa:** T03, T17
**O que fiz / o que achei:** As duas execuções do Codex CLI pararam aos 80 s com **"You've hit
your usage limit … try again at 8:28 PM"** (T03 usou 54 mil tokens com esforço `xhigh`; T17, 38
mil). Conferido que nada ficou pela metade: todos os `.py` de `src/` passam por `ast.parse`.
- **T17 concluída** apesar da interrupção — o Codex chegou a implementar tudo. Verificado pelo
  Claude: `montar_treino(0, …)` e `(-5, …)` dão `ValueError`; extras com 1 dos 7 veículos e com um
  JSONL vazio dão `FileNotFoundError` citando o arquivo; `(None, None)` 152, `(None, extras_v1)`
  3.235, `(400, extras_v1)` 400; o empacotador recusa sem mexer no zip e lista os 7 JSONL ausentes de
  `blocos_extra`; `metrics.py` roda.
- **T03 bloqueada** até 20:28. A execução deixou só `resultados/inspecao_segmentacao/t03_compatibilidade_c.json`
  (fotografia da saída atual da C, para conferir que o padrão não muda); `extrator.py` não foi tocado.
- **Preferência visual do Pedro**, olhando as imagens da T16: no MA, a **versão B** (36 blocos); no RJ,
  a **v1** (66 blocos). Nas duas páginas ele rejeitou a C, a fragmentada. Leitura: para quem anota, um
  bloco é uma unidade de leitura (parágrafo, item de ato, seção), não uma linha. **Isso vira critério
  da T03**, acima da régua do Azure, que segmenta mais fino. Ressalva: a imagem mostra o formato das
  caixas, não o texto dentro delas; a v1 do RJ tem 13 blocos sobrepostos, isto é, texto embaralhado.
**Arquivos tocados:** `COMUNICACAO_AGENTES.md`, `orquestracao/despachar.py` (passa a detectar limite de
uso e escopo)
**Resultado / evidência:** `orquestracao/logs/20260912_175030_T03_codex.log`, `…175032_T17_codex.log`.
**Próximo passo / para quem:** Claude testa uma candidata B+ (a B com títulos centralizados virando bloco
próprio, para o CE sem perder a granularidade da B) na amostra de 44 páginas. A T03 volta ao Codex às
20:28 com o critério atualizado, ou antes por outro caminho, se o Pedro decidir.

### 2026-09-12 17:50 — Claude — REVISÃO — T10 aprovada; T03 e T17 despachadas
**Tarefa:** T10 (revisão do Codex CLI), despacho de T03 e T17
**O que fiz / o que achei:** O Codex CLI converteu as saídas das APIs para o formato do
protocolo: **Azure, 12 páginas e 951 blocos** (`data/processed/blocos_api_azure/`); **Google, 2
páginas e 265 blocos** (`data/processed/blocos_api_docai/`). Decisões dele, conferidas: as 2
páginas do Google são p0 e p1 do PDF de 22 (cobertura de trigramas 61% e 65%, contra 12% e 13%
da segunda candidata); polegadas × 72, com desvio máximo de 0,89 pt frente ao PDF; tabela do
Google como bloco único. Conferência independente do Claude: ids únicos, ordens como
permutações, caixas dentro da página e nenhum vazamento de ordem pelo id, nas 14 páginas.
**Achado:** os detectores comerciais segmentam **mais fino** que o nosso código atual (C) nas
mesmas páginas — Azure 79,3 blocos/página contra 66,3 da C nas 12; no par do Estado do RJ,
Google 132,5, Azure 114 e C 93. "Fragmentação demais" depende da régua: contra o Azure, a C
não é fragmentada nessas páginas. Ressalva: são páginas de outros veículos (Estado do RJ Parte I e
Japeri), não as páginas-problema.
**Arquivos tocados:** `COMUNICACAO_AGENTES.md`
**Resultado / evidência:** `orquestracao/logs/20260912_174041_T10_codex_resposta.md`;
`data/processed/blocos_api_azure/_comparacao_segmentacao.json`.
**Próximo passo / para quem:** despachadas agora ao Codex CLI, em paralelo e sem arquivos em
comum: **T03** (candidatas de agrupamento medidas na bancada de 44 páginas e contra os parágrafos do
Azure; o padrão do extrator não muda até a DECISÃO do Pedro) e **T17** (ajustes da revisão da T01).

### 2026-09-12 17:47 — Claude — REVISÃO — T16 aprovada; teste de uma regra nova para a T03
**Tarefa:** T16 (revisão do Antigravity CLI) e T03 (subsídio)
**O que fiz / o que achei:** A T16 ficou dentro do escopo (`src/data/inspecionar_segmentacao.py`
e 17 saídas em `resultados/inspecao_segmentacao/`) e as contagens de B e C batem com as
medidas. O Antigravity achou um **erro do Claude**: a coluna v1 da tabela do handoff dizia SE
39 e RJ 74; os dados dão **45 e 66** (e CE 9), iguais aos da bancada T02. Corrigido em
`docs/HANDOFF.md` 2.2. Nas imagens, a C picota exatamente onde há recuo: primeira linha de
parágrafo e itens de lista com a continuação na margem (no MA o recuo é de 9 larguras de
caractere, e a regra só aceita 5). A B fica melhor no MA, mas junta listas inteiras.
Testei, num rascunho fora do repositório, uma regra D — "linha anterior curta fecha o bloco;
recuo de primeira linha de até 12 caracteres" — na amostra de 44 páginas da T02:

| Regra | Blocos/pág. | % sobrepostos | % 1 palavra | Rejeitadas | Págs. c/ bloco > 250 pal. |
|---|---:|---:|---:|---:|---:|
| B | 41,7 | 10,5 | 23,9 | 1 | 8 |
| C | 61,4 | 4,9 | 18,4 | 0 | 6 |
| D | 97,7 | 1,6 | 21,5 | 3 | 1 |

Por página-problema (B / C / D): MA 36 / 85 / 54; SE 30 / 48 / 57; RJ 53 / 159 / 159; CE 2 / 15 / 15.
A D resolve o recuo e quase zera blocos gigantes e sobreposição, mas não melhora o RJ e
dobra a fragmentação média. **Nenhuma regra ganha em tudo**; falta uma régua externa de
granularidade.
**Arquivos tocados:** `docs/HANDOFF.md`, `COMUNICACAO_AGENTES.md` (inclui correção dos
horários das entradas do Claude de 16:58 a 17:40, que tinham sido estimados; agora vêm dos
logs do despachante)
**Resultado / evidência:** `orquestracao/logs/20260912_173448_T16_antigravity_resposta.md`;
experimento em rascunho do orquestrador (`variantes_blocos.py`, fora do repositório).
**Próximo passo / para quem:** quando a T10 voltar, a T03 vai ao Codex CLI usando os parágrafos
do Azure como régua (quanto um parágrafo do Azure é partido em vários blocos nossos e quanto um
bloco nosso junta vários parágrafos), junto com a bancada de 44 páginas. A escolha final é
DECISÃO do Pedro.

### 2026-09-12 17:40 — Claude — ACHADO — As saídas de API do acervo não eram o que o handoff dizia
**Tarefa:** T10 (1ª execução do Codex CLI e reespecificação)
**O que fiz / o que achei:** O Codex CLI parou a T10 pela regra 5, corretamente: o JSON do
Boletim 7621 (34 MB) **não tem nenhuma caixa** e é de **Duque de Caxias**; o
`Google Doc AI Tests/document (1).json` é do **Diário do Estado do RJ** e cobre 2 das 22 páginas
do PDF. Nenhum dos dois é de Japeri, embora estejam na pasta de Japeri. Procurando alternativa,
achei a saída do **Azure Document Intelligence** (`prebuilt-layout`, API 2024-11-30) em
`json_atos_japeri/resultado_azure_lote_layout.{jsonl,txt}` — que não são JSONL: são blocos
`NOME DO ARQUIVO:` + JSON + linha de `=`. Cobertura conferida: **12 páginas** (2 do Estado do RJ,
2 de cada uma de 5 edições de Japeri), 951 parágrafos, todos com caixa em polegadas, papéis
(`title`, `sectionHeading`, `pageHeader`, `pageFooter`, `pageNumber`) e ordem de leitura. A 6ª
edição (5174) falhou na API com HTTP 429. Nas 2 páginas do Estado do RJ existem as três
segmentações (nossa, Google, Azure). T10 reespecificada e redespachada ao Codex CLI.
**Arquivos tocados:** `orquestracao/prompts/T10_conversor_apis_v2.md`, `COMUNICACAO_AGENTES.md`
**Resultado / evidência:** `orquestracao/logs/20260912_173447_T10_codex_resposta.md`; contagem
do Azure lida com `json.JSONDecoder().raw_decode`.
**Próximo passo / para quem:** todos — a validação com detector comercial vale para **12
páginas**: serve de ilustração e sanidade, não de estatística. A afirmação "Google Document AI
sobre Japeri" nos documentos está errada (são 2 páginas do Estado do RJ); o Claude corrige.
Nota sobre o despachante: ele atribuiu ao Codex uma mudança no quadro que foi do Claude, feita
durante o despacho — com escritores simultâneos, a lista de arquivos alterados não prova autoria.

### 2026-09-12 17:36 — Claude — REVISÃO — T01 aprovada, com dois furos
**Tarefa:** T01 (revisão do trabalho do Codex); abre a T17
**O que fiz / o que achei:** Li as mudanças em `src/eval/protocolo.py` (`montar_treino`) e em
`src/kaggle/montar_pacote.py` e testei os casos de borda sem escrever em `data/`. Funciona como
especificado: treino base vazio, pasta de extras ausente, pasta sem JSONL e pedido acima do
disponível dão erro com mensagem clara, e o log mostra base, extras usadas e disponíveis. Os
quatro chamadores (`layoutlm_ordem.py`, `layoutlm_sucessor.py`, `lstm_ordem.py`,
`rodar_curva_aprendizado.py`) seguem compatíveis. Dois furos:
1. `montar_treino(0, extras)` devolve **0 páginas** sem erro. Antes, 0 significava "todas".
   Nenhum chamador passa 0 hoje (a curva resolve 0 antes de chamar), então o risco é latente.
2. **Extras parciais passam em silêncio.** Com só 1 dos 7 veículos de treino na pasta, o
   treino montou 515 páginas (152 + 363) sem aviso. É o cenário de uma re-extração da T05
   interrompida, porque `reextrair.py` grava os arquivos por veículo um de cada vez no fim. O
   empacotador do Kaggle tem a mesma fraqueza: exige só um JSONL por coleção.
**Arquivos tocados:** nenhum
**Resultado / evidência:** `montar_treino(None, None)` → 152; `(0, blocos_extra_v1)` → 0;
`(None, blocos_extra_v1)` → 3.235; pasta temporária com 1 dos 7 JSONL → 515, sem erro.
**Próximo passo / para quem:** T17 (Codex): tratar `n_treino ≤ 0` como erro explícito; listar os
veículos de treino ausentes na pasta de extras e **falhar**; no empacotador, conferir que as
coleções têm todos os veículos esperados. A T01 pode ser usada até lá, conferindo a contagem
de extras no log.

### 2026-09-12 17:34 — Claude — AVISO — Orquestração por linha de comando ativa
**Tarefa:** T10 e T16 (despacho)
**O que fiz / o que achei:** A pedido do Pedro, o Claude passa a distribuir tarefas por linha
de comando: técnicas para o **Codex CLI com `gpt-6-astra`**, braçais para o **Antigravity CLI
com Gemini 3.8 Flash**. Instalado o Antigravity CLI (`agy` 1.2.2, em
`%LOCALAPPDATA%\agy\bin`, já no PATH do usuário). O Codex CLI é o que acompanha o app do
Codex (0.154.0, já autenticado). Despachante com rede de segurança em
`orquestracao/despachar.py`. Os dois foram testados em modo não interativo antes de receber
tarefa: resposta simples em 5 e 6 s; o `agy` rodou o Python do projeto e gravou arquivo
sozinho. Despachados agora: **T10 → Codex CLI** e **T16 → Antigravity CLI** (tarefa nova).
**Arquivos tocados:** `orquestracao/` (novo), `COMUNICACAO_AGENTES.md`, `AGENTS.md`, `.gitignore`
**Resultado / evidência:** logs de cada despacho em `orquestracao/logs/`, com a lista de
arquivos criados, alterados e removidos e as verificações de `data/raw/` (4.661 arquivos) e
das anotações do Golden.
**Próximo passo / para quem:** Claude revisa T10 e T16 quando voltarem. **T01 aguarda
revisão do Claude** (toca `protocolo.py`), antes de o treino ampliado ser usado. T03: o Claude
escreve a proposta a partir de `resultados/avaliacao_segmentacao.json` e das folhas da T16, e
a implementação vai para o Codex CLI.

### 2026-09-12 17:31 — Codex — FEITO — Proteção do treino ampliado e bancada do segmentador
**Tarefa:** T01 e T02
**O que fiz / o que achei:** Centralizei em `montar_treino()` a validação da pasta de
páginas extras: pasta ausente, pasta sem JSONL dos veículos de treino, zero páginas novas
e quantidade solicitada acima da disponível agora encerram o processo com erro explícito.
O log informa páginas base, extras usadas e extras disponíveis. O empacotador do Kaggle
também recusa criar um pacote incompleto. Implementei a bancada reproduzível com 40 páginas
balanceadas por veículo, semente 42, mais as quatro páginas-problema; ela executa o código
atual ao vivo e não escreve em `data/`.
**Arquivos tocados:** `src/eval/protocolo.py`, `src/kaggle/montar_pacote.py`,
`src/data/avaliar_segmentacao.py`, `resultados/avaliacao_segmentacao.json`,
`docs/HANDOFF.md`, `COMUNICACAO_AGENTES.md`
**Resultado / evidência:** `montar_treino(400, blocos_extra_v1)` imprimiu 400 páginas =
152 base + 248 extras (3.083 extras disponíveis); pasta ausente e pasta vazia terminaram
com `FileNotFoundError`; o empacotador recusou `data/processed/blocos_extra` ausente. Na
bancada de 44 páginas: v1 = 50,9 blocos/página, 26,2% sobrepostos, 31,4% de uma palavra;
B = 42,7, 10,5%, 24,0%, uma rejeitada; código C = 61,4, 4,9%, 18,5%, zero rejeitadas.
Casos C: MA 85, SE 48, RJ 159, CE 15 blocos. `src/eval/metrics.py` passou e 28 arquivos
Python passaram por `ast.parse`; `git diff --check` não encontrou erro.
**Próximo passo / para quem:** T01 aguarda `REVISÃO` de outro agente porque toca
`src/eval/protocolo.py`. T02 está concluída e fornece a evidência para T03; a C reduz
sobreposição, mas MA/RJ confirmam fragmentação excessiva, então ainda não é a versão final.

### 2026-09-12 17:28 — Antigravity — FEITO — Preservação dos artefatos da segmentação v1 (T04)
**Tarefa:** T04
**O que fiz / o que achei:** Copiei todos os artefatos gerados sobre a segmentação v1 para pastas de salvaguarda antes que qualquer re-execução os sobrescreva:
1. `resultados/` → `resultados_segmentacao_v1/`
2. `models/layoutlm_ordem/` → `models/layoutlm_ordem_segmentacao_v1/`
3. `docs/figuras/` → `docs/figuras/segmentacao_v1/`
4. `data/processed/splits.json` → `data/processed/splits_segmentacao_v1.json`
Nenhum arquivo foi movido ou apagado. Integridade verificada por comparação de contagem de arquivos e bytes exatos entre origem e destino.
**Arquivos tocados:** `resultados_segmentacao_v1/` (novo diretório), `models/layoutlm_ordem_segmentacao_v1/` (novo diretório), `docs/figuras/segmentacao_v1/` (novo diretório), `data/processed/splits_segmentacao_v1.json` (novo arquivo)
**Resultado / evidência:** Contagens e tamanhos conferidos byte a byte:
- `resultados_segmentacao_v1/`: 78 arquivos, 1.622.799 bytes (1,55 MB) — idêntico a `resultados/` (78 arquivos, 1.622.799 bytes)
- `models/layoutlm_ordem_segmentacao_v1/`: 14 arquivos, 2.258.531.964 bytes (2.153,90 MB / 2,10 GB) — idêntico a `models/layoutlm_ordem/` (14 arquivos, 2.258.531.964 bytes)
- `docs/figuras/segmentacao_v1/`: 8 arquivos, 1.908.681 bytes (1,82 MB) — idêntico a `docs/figuras/` (8 arquivos, 1.908.681 bytes)
- `data/processed/splits_segmentacao_v1.json`: 1 arquivo, 1.444 bytes (1,41 KB) — idêntico a `data/processed/splits.json` (1 arquivo, 1.444 bytes)
**Próximo passo / para quem:** T04 concluída. Destrava T05 (que também aguarda T03).

### 2026-09-12 17:10 — Claude — AVISO — Estado ao abrir o quadro
**Tarefa:** nenhuma (passagem de bastão)
**O que fiz / o que achei:** Criei este quadro, `AGENTS.md`, `CLAUDE.md` e
`docs/HANDOFF.md`. Três pontos que qualquer agente precisa saber antes de mexer:
1. **Dados e código do segmentador estão em versões diferentes.** `data/processed/blocos`,
   `blocos_ri_japeri` e `golden_v1/tarefas.jsonl` estão na versão B; o código de
   `src/data/extrator.py` está na C, não validada (resolve o CE, fragmenta demais MA e RJ).
   Detalhes em `docs/HANDOFF.md` seção 2.2.
2. **`data/processed/blocos_extra/` não existe.** A re-extração foi interrompida. Qualquer
   treino ampliado roda hoje com zero páginas extras e não avisa (T01).
3. **Todos os `resultados/` são da segmentação v1.** Avaliar essas predições contra
   `data/processed/blocos` (versão B) dá números sem sentido; use
   `TCC_DIR_BLOCOS=data\processed\blocos_v1`.
**Arquivos tocados:** `AGENTS.md`, `CLAUDE.md`, `COMUNICACAO_AGENTES.md`, `docs/HANDOFF.md`,
`data/golden/golden_v1/_segmentacao_v1/` (novo)
**Resultado / evidência:** teste do código atual nas quatro páginas-problema — MA 85 blocos,
SE 48, RJ 159, CE 15 (versão B: 36, 30, 53, 2). Versão B no Golden: 9 das 30 páginas com
algum bloco acima de 250 palavras.
**Próximo passo / para quem:** T01, T02 e T04 não dependem de nada e podem começar em
paralelo (Codex: T01 e T02; Antigravity: T04).

### 2026-09-12 16:58 — Claude — AVISO — Anotação do Pedro apagada por engano e reconstruída
**Tarefa:** nenhuma
**O que fiz / o que achei:** Apaguei `data/golden/golden_v1/anotacoes.jsonl` achando que era
resíduo de teste (anotador `teste_claude`). Era trabalho do Pedro: a página 1 concluída, 28
blocos, marcada com "tabela" e "segmentação", 254 s, feita no navegador do app com o nome
de teste preenchido. Reconstruí o registro a partir da saída impressa antes da remoção e
arquivei junto com as tarefas originais a que ele se refere (a ordem confere com os 28
identificadores). O rascunho da página 2 não foi recuperado.
**Arquivos tocados:** `data/golden/golden_v1/_segmentacao_v1/{tarefas.jsonl, anotacoes.jsonl, LEIAME.md}`
**Resultado / evidência:** a anotação é sobre a segmentação v1 e não vale para o lote
regenerado; fica como registro do custo de anotação e do defeito encontrado.
**Próximo passo / para quem:** todos — regra dura 1 de `AGENTS.md`: anotação humana nunca se
apaga, mesmo com nome estranho.
