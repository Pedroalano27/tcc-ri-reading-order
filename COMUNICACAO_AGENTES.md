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
| — | nada reservado | — | — |

---

## Tarefas

Status: `aberta` · `em andamento (agente)` · `bloqueada (motivo)` · `em revisão` · `feita`.

| ID | Tarefa | Dono sugerido | Depende de | Status |
|---|---|---|---|---|
| T01 | Proteção contra `blocos_extra` ausente | Codex | — | feita (revisada; ajustes na T17) |
| T02 | Bancada de avaliação do segmentador | Codex | — | feita |
| T03 | Fechar a versão do segmentador | Claude propõe, Codex implementa, Pedro aprova | T02, T10 | feita pelo Claude; aprovação do Pedro em curso (anotando); REVISÃO do Codex pendente |
| T04 | Preservar os artefatos da segmentação v1 | Antigravity | — | feita |
| T05 | Re-extrair as três coleções com a versão final | Antigravity | T03, T04 | bloqueada (segmentação v3 em discussão; ver Registro 20:11) |
| T06 | Regenerar o lote `golden_v1` | Antigravity | T03 | feita (Claude) |
| T07 | Recalcular `splits.json` e comparar | Antigravity roda, Claude analisa | T05 | aberta |
| T08 | Anotar o `golden_v1` | Pedro | T06 | feita (26 concluídas; 4 puladas por tabela) |
| T09 | Refazer todos os números locais | Antigravity roda, Claude confere | T05, T07 | aberta |
| T10 | Conversor das APIs comerciais (Azure e Google) → formato do protocolo | Codex | — | feita (revisada) |
| T11 | Análise de sensibilidade à segmentação | Claude | T09, T10 | aberta |
| T12 | Kaggle: pacote, execução e importação | Antigravity prepara, Pedro executa | T09 | aberta |
| T13 | Atualizar resultados e apresentação | Claude | T11, T12 | aberta |
| T14 | Extrator mais rápido com PyMuPDF (opcional) | Codex | T03 | aberta |
| T15 | Levar as perguntas ao orientador | Pedro | — | aberta |
| T16 | Folhas de inspeção visual das páginas-problema | Antigravity | — | feita (revisada) |
| T17 | Ajustes da revisão da T01: `n_treino ≤ 0` e extras parciais | Codex | — | feita (verificada pelo Claude) |

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
