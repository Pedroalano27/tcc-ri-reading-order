# Handoff do projeto — estado em 2026-09-12

Documento de passagem de bastão para qualquer agente de IA (Codex, Antigravity, uma nova
sessão do Claude) ou pessoa que entre no projeto agora. Escrito pelo Claude ao fim da
sessão 4.

**Leia nesta ordem:** este arquivo → [`AGENTS.md`](../AGENTS.md) (regras e armadilhas) →
[`COMUNICACAO_AGENTES.md`](../COMUNICACAO_AGENTES.md) (quadro compartilhado, tarefas
abertas e reservas). Para entender os conceitos do zero:
[`ENTENDA_O_PROJETO.md`](ENTENDA_O_PROJETO.md).

---

## 0. Resumo em dez linhas

1. TCC de graduação (INF-UFG, orientador Prof. Dr. Thierson Couto Rosa), área de
   **Recuperação de Informação**. Autor: Pedro (GitHub `Pedroalano27`).
2. Tarefa: **detecção de ordem de leitura** em Diários Oficiais — dado um conjunto de
   blocos de texto com coordenadas e sem ordem, recuperar a sequência em que um humano lê.
3. Pergunta central: o trade-off **eficácia × eficiência** entre heurísticas geométricas,
   BiLSTM, **LayoutLM** (modelo leve, consciente de layout) e **LLMs** generativas.
4. Até aqui a heurística **XY-cut vence** em τ de Kendall (0,837); o LayoutLM pontual
   ficou em 0,671 com só 13% de continuidade local.
5. Criamos a métrica **sucessor correto**, que revelou que o τ esconde texto picotado.
6. Criamos uma **formulação nova do LayoutLM que prevê o sucessor** de cada bloco, com
   decodificação em cadeias: com 3.235 páginas de treino chega a τ 0,785 e **51,8%** de
   sucessor correto (XY-cut 64,2%).
7. Ao começar a anotar o Golden Dataset, o Pedro achou **defeitos na segmentação em
   blocos**. Eles eram reais e anteriores à ordenação (texto embaralhado dentro do bloco).
8. O conserto está **pela metade**: há três versões do segmentador em jogo e os dados em
   disco não batem com o código (seção 2). **Todos os números acima foram medidos na
   segmentação antiga e precisam ser refeitos.**
9. O Golden Dataset (30 páginas) **ainda não tem anotação válida**; não anotar até a
   segmentação ser fechada.
10. Pacote e dois notebooks do Kaggle (2× T4) estão prontos em código, **nunca executados**,
    e o pacote em `dist/` está desatualizado.

---

## 1. Onde está cada informação

| Pergunta | Onde responder |
|---|---|
| O que é o projeto, com todos os conceitos explicados | [`docs/ENTENDA_O_PROJETO.md`](ENTENDA_O_PROJETO.md) |
| Desenho experimental em linguagem de artigo | [`docs/METODOLOGIA.md`](METODOLOGIA.md) |
| Todos os números e figuras (segmentação v1) | [`docs/RESULTADOS_PRELIMINARES.md`](RESULTADOS_PRELIMINARES.md), `resultados/comparacao.md`, `docs/figuras/` |
| Histórico completo, problemas e decisões com justificativa | [`docs/DIARIO_DE_BORDO.md`](DIARIO_DE_BORDO.md) — tabelas "Problemas encontrados" e "Decisões e justificativas" no fim |
| O que falta e perguntas para o orientador | [`docs/ROADMAP.md`](ROADMAP.md) |
| Inventário dos 4.644 PDFs do acervo | [`docs/ACERVO.md`](ACERVO.md) |
| Como anotar o Golden Dataset | [`docs/GUIA_ANOTACAO.md`](GUIA_ANOTACAO.md) |
| Como rodar no Kaggle | [`docs/KAGGLE.md`](KAGGLE.md) |
| Fichamento bibliográfico | [`docs/LITERATURA.md`](LITERATURA.md) |
| Regras para agentes e armadilhas técnicas | [`AGENTS.md`](../AGENTS.md) |
| Tarefas abertas, quem está mexendo em quê, avisos entre agentes | [`COMUNICACAO_AGENTES.md`](../COMUNICACAO_AGENTES.md) |
| Como o Claude despacha tarefas ao Codex CLI (`gpt-6-astra`) e ao Antigravity CLI, prompts usados e logs de cada execução | [`orquestracao/despachar.py`](../orquestracao/despachar.py), `orquestracao/prompts/`, `orquestracao/logs/` (fora do git) |
| Parágrafos das APIs comerciais no formato do protocolo (Azure 12 páginas, Google 2) | `data/processed/blocos_api_azure/`, `data/processed/blocos_api_docai/`, gerados por `src/data/converter_apis.py` |
| Imagens das quatro páginas-problema com as caixas de cada versão | `resultados/inspecao_segmentacao/`, geradas por `src/data/inspecionar_segmentacao.py` |
| Página de apresentação para o orientador (segmentação v1, sem a formulação de sucessor) | https://claude.ai/code/artifact/690922c1-da40-4598-aa6e-7f18fe1bc6f3 — fonte em `docs/apresentacao/` |

Cada `.py` tem um docstring no topo explicando o que faz, por quê e como usar. Leia o
docstring antes de mudar um módulo: as decisões não óbvias estão escritas ali.

---

## 2. Estado atual, com precisão

### 2.1 Git

- Último commit: `912e0ae` (2026-09-12 11:45, já enviado ao GitHub). **Tudo o que foi
  feito depois dele está sem commit** — a formulação de sucessor, o conserto da
  segmentação, os notebooks novos e estes documentos, cerca de 30 arquivos. Confira com
  `git status`.
- Commit e push só quando o Pedro pedir.
- Não versionados por decisão (`.gitignore`): `data/raw/` (19 GB de PDFs),
  `data/processed/`, `models/`, `resultados/**/*.jsonl` (exceto `resultados/kaggle/`),
  `dist/`, imagens do Golden.

### 2.2 Três versões do segmentador

O segmentador é o trecho de [`src/data/extrator.py`](../src/data/extrator.py) que
transforma palavras em linhas e linhas em blocos. Três versões convivem:

| Versão | Critério de corte de linha e de agrupamento | Onde está | Situação |
|---|---|---|---|
| **v1** | Linha cortada onde o vão passa de 1,8 largura de caractere; linha entra no bloco se sobrepõe ≥ 50% da largura do **menor** | Dados em `data/processed/*_v1/`; todos os `resultados/` | **Defeituosa.** 25% dos blocos se sobrepõem a outro; texto embaralhado dentro do bloco (entrada em negrito "Art. 1º", texto justificado) |
| **B** | Linha cortada só em **calha** (coluna de x quase sem tinta, limite relativo de 25% da ocupação típica) ou vão > 8 caracteres; bloco restrito à coluna | Dados em `data/processed/blocos/`, `data/processed/blocos_ri_japeri/`, `data/golden/golden_v1/tarefas.jsonl` | Sobreposição 25% → **9,1%**. Mas **funde demais texto corrido**: 6 páginas de teste do CE viraram 2 blocos e foram rejeitadas pelo filtro (teste 95 → 89); 9 das 30 páginas do Golden têm um bloco com mais de 250 palavras (uma com 1.067) |
| **C** | B + linha só entra no bloco se a **margem esquerda** for compatível (−5 a +2,5 caracteres) | **É o código atual** de `extrator.py` | **Não validada.** Nas 4 páginas-problema: resolve o CE (2 → 15 blocos) mas **fragmenta demais** o MA (36 → 85) e o RJ (53 → 159) |

Medidas nas 4 páginas-problema, para reproduzir (seção 5):

| Página | v1 | B | C |
|---|---:|---:|---:|
| MA `executive_official_diary_2024-01-18_22_36.pdf` p0 — entrada em negrito | 54 | 36 | 85 |
| SE `DOE-SE_2023-03-10_5100.pdf` p14 — justificado picotado | 45 | 30 | 48 |
| RJ `Parte II (Poder Legislativo)_2024-02-06.pdf` p1 — três colunas | 66 | 53 | 159 |
| CE `do20250314p03.pdf` p45 — texto corrido | 9 | 2 (rejeitada) | 15 |

Correção de 2026-09-12 17:46: a coluna v1 citava 39 (SE) e 74 (RJ), números de uma versão
intermediária do extrator. Os valores acima vêm de `data/processed/blocos_v1/` e conferem com a
bancada T02 e com as folhas da T16. Imagens das três versões: `resultados/inspecao_segmentacao/`.

**Atualização de 2026-09-12 18:31: versão final implementada.** A regra de agrupamento passou a
ser a B mais duas regras — linha curta e centralizada não se mistura com texto corrido, e nenhuma
fusão pode fazer duas caixas se cruzarem (docstring de `construir_blocos`). Páginas-problema:
MA 36, SE 37, RJ 78, CE 15. Bancada de 44 páginas: 48,8 blocos/página, 5,9% sobrepostos, uma
rejeitada fora dos veículos de teste. O Golden foi regenerado com ela (1.248 blocos) e o Pedro está
anotando; a aprovação final vem dessa anotação. **Os dados em `data/processed/` continuam na
versão B** até a re-extração (T05). Registro completo no quadro, entrada DECISÃO de 18:31.

**Atualização de 2026-09-12 22:55: segmentação v3 (T18 a T21).** Depois de anotar o Golden v1, o
Pedro apontou seis defeitos; as causas estão no quadro (ACHADO de 20:11) e a v3 corrige cinco:
- *faixas de linha de base com reatribuição pelo centro* — o "nº" que caía na linha da coluna ao
  lado e partia parágrafos (MA);
- *calhas locais* (`_cortes_locais`) — as caixas que pulavam de coluna onde um trecho da página
  tem outro desenho de colunas (RJ, Barra do Piraí, SP);
- *tabela = um bloco* (`"tipo": "tabela"`), com a região dada pelo detector de layout **Docling
  Heron** em [`src/data/layout.py`](../src/data/layout.py) — RT-DETRv2 treinado no DocLayNet,
  revisão fixada, só do cache local do Hugging Face. **É o único componente visual do pipeline**:
  o texto continua vindo da camada digital do PDF;
- *descarte de bloco sem letra nem dígito* (separadores "*** ***");
- *junção de letras espaçadas* ("R E S O L V E").
O sexto, texto dentro de imagem, fica fora: exigiria OCR (limitação declarada).

Bancada de 44 páginas (`resultados/avaliacao_segmentacao_v3.json`, código final): 33,0
blocos/página, 2,7% sobrepostos, 7,2% de blocos de uma palavra e nenhuma página rejeitada (final:
48,8 / 5,9% / 21,5% / 1). Maior bloco: 1.769 palavras, uma tabela. O código passou por três revisões do Codex (despachos das 22:05, 22:27 e
22:52, logs em `orquestracao/logs/`). A ordem anotada no Golden v1 foi levada para a v3 por
[`src/anotacao/projetar_ordem.py`](../src/anotacao/projetar_ordem.py): 20 páginas saem limpas e 5
com conflito, que voltam para anotação no lote `golden_v2` junto com as 4 puladas e 20 páginas
novas. **T05 em andamento desde 22:58**: `data/processed/blocos`, `blocos_ri_japeri` e
`blocos_extra` estão sendo regravados na v3 a partir das coleções `*_v1`; as versões B foram
renomeadas para `blocos_b` e `blocos_ri_japeri_b`.

A bancada T02 foi implementada em `src/data/avaliar_segmentacao.py`. Na amostra fixa de
44 páginas (40 sorteadas de forma balanceada por veículo + as 4 páginas-problema), a v1
teve 50,9 blocos/página, 26,2% de blocos sobrepostos e 31,4% de blocos de uma palavra; a
B teve 42,7, 10,5% e 24,0%, com uma página rejeitada; a C teve 61,4, 4,9% e 18,5%, sem
rejeições. A C reduz bem a sobreposição, mas os casos MA (85 blocos) e RJ (159) confirmam
fragmentação excessiva. Evidência completa: `resultados/avaliacao_segmentacao.json`.

### 2.3 Dados

| Pasta | Páginas | Segmentação | Observação |
|---|---:|---|---|
| `data/raw/` | 4.644 PDFs | — | Acervo do orientador; nunca modificar |
| `data/processed/blocos_v1/` | 777 | v1 | Coleta do experimento principal (30 veículos) |
| `data/processed/blocos/` | 777 esperadas | v3 | **Em re-extração (T05)**, a partir de `blocos_v1` |
| `data/processed/blocos_b/` | 762 | B | Versão B preservada (antes `data/processed/blocos/`); 15 páginas perdidas pelo filtro de 3 a 200 blocos |
| `data/processed/blocos_extra_v1/` | 3.117 | v1 | Páginas extras dos 7 veículos de treino (curva de aprendizado) |
| `data/processed/blocos_extra/` | 3.117 esperadas | v3 | **Em re-extração (T05)**, a partir de `blocos_extra_v1`. Enquanto não terminar, o treino ampliado para com erro (T01) |
| `data/processed/blocos_ri_japeri_v1/` | 269 | v1 | Todas as páginas das 27 edições de Japeri (piloto de RI) |
| `data/processed/blocos_ri_japeri/` | 269 esperadas | v3 | **Em re-extração (T05)**, a partir de `blocos_ri_japeri_v1` |
| `data/processed/blocos_ri_japeri_b/` | 263 | B | Versão B preservada |
| `data/processed/splits.json` | — | calculado sobre v1 | Divisão por veículo (seção 3). Precisa ser recalculada na segmentação final e comparada |
| `data/golden/golden_v1/tarefas.jsonl` | 30 (1.248 blocos) | final | **Anotado** pelo Pedro: 26 concluídas, 4 puladas (tabela). Nunca regenerar. `derivados/palavras_por_bloco.jsonl` congela as palavras de cada bloco; `derivados/projecao_v3.jsonl` leva a ordem para a v3 (20 limpas, 5 conflitos) |
| `data/golden/golden_v2/tarefas.jsonl` | 29 (814 blocos) | v3 | 9 páginas do v1 a refazer (5 conflitos, 4 puladas) + 20 novas (silver 12, incerto 8). **Anotado** pelo Pedro: 27 concluídas, 2 puladas (SP). Nunca regenerar |
| `data/golden/_avaliacao/golden_v3/` | 47 (1.238 blocos) | v3 | **Conjunto de avaliação do Golden**, derivado (`src/anotacao/montar_referencia.py`): 20 páginas do v1 projetadas + 27 do v2; `referencia.jsonl` no lugar de `anotacoes.jsonl`. Grupos: silver 21, incerto 26 |
| `data/processed/layout/` | 4.112 | — | Cache do detector de layout (regiões por página, em pontos). Regenerável com `src/data/layout.py` |
| `data/golden/golden_v1/_segmentacao_v1/` | 30 (1.044 blocos) | v1 | Arquivo: lote original e uma página anotada pelo Pedro sobre ele. Ver o `LEIAME.md` da pasta |

A variável de ambiente `TCC_DIR_BLOCOS` troca a pasta de blocos lida por **todo** o
pipeline (`src/eval/protocolo.py`); `TCC_DIR_RESULTADOS` troca a pasta de saída.

### 2.4 Modelos treinados (`models/layoutlm_ordem/`, ~450 MB cada, todos sobre v1)

| Checkpoint | O que é |
|---|---|
| `layoutlm.pt` | LayoutLM pontual, 152 páginas, 40 épocas |
| `layoutlm_sem_layout.pt` | Ablação: caixas zeradas |
| `curva_layoutlm_n3235.pt` | Pontual, 3.235 páginas, 4 épocas |
| `layoutlm_sucessor.pt` | Sucessor, 152 páginas, 40 épocas |
| `curva_layoutlm_sucessor_n3235.pt` | Sucessor, 3.235 páginas, 4 épocas — o melhor modelo até aqui |

Cada um tem um `*_config.json` ao lado com hiperparâmetros, tempo e melhor validação.
Os checkpoints **não servem para a segmentação nova** sem re-treino: os blocos mudam.

### 2.5 Resultados (`resultados/`)

**Atualização de 2026-09-12 23:55.** Os resultados da segmentação v1 estão em
`resultados_segmentacao_v1/` (cópia idêntica, conferida com `cmp`) e saíram de `resultados/`,
que passa a guardar a v3. Já na v3: baselines no teste de 89 páginas (XY-cut τ 0,891; ingênua
0,790; aleatória −0,020) e `resultados/golden/_avaliacao/golden_v3/avaliacao.md`. Os métodos
aprendidos (BiLSTM, as duas formulações do LayoutLM, curva, ablações) e as LLMs novas vêm do Kaggle
(T12). A divisão treino/validação/teste foi mantida (DECISÃO de 23:55 no quadro, confirmada pelo
Pedro). O texto abaixo descreve a v1.

#### Resultados da v1 (`resultados_segmentacao_v1/`)

- `pred_<metodo>.jsonl`: uma linha por página, `{"page_id", "ordem_pred", "tempo_ms"}`.
  Os identificadores de bloco são os da segmentação v1. **Avaliá-los contra
  `data/processed/blocos/` (versão B) produz lixo**: use `TCC_DIR_BLOCOS=data/processed/blocos_v1`.
- `comparacao.json` / `comparacao.md`: tabela principal. **Ainda não inclui as
  predições da formulação de sucessor** (o `comparar.py` não foi re-rodado depois delas).
- `curva_aprendizado/curva.json`: curva do LayoutLM pontual e da BiLSTM.
- `ri_japeri/resultado.json`: piloto de RI.
- `qualidade_segmentacao.json`: medida de antes/depois da última re-extração (é
  sobrescrito a cada execução de `src/data/reextrair.py`).
- `resultados/golden/`: vazio.

### 2.6 Kaggle

- Código pronto: [`src/kaggle/montar_pacote.py`](../src/kaggle/montar_pacote.py) gera
  `dist/kaggle/tcc_ordem_leitura.zip` (código + todas as páginas extraídas + Golden) e dois
  notebooks, também copiados em `notebooks/`:
  - `kaggle_treino_ordem.ipynb` — curva das duas formulações, ablações, varredura do limiar
    de decodificação, latência na T4, avaliação contra o Golden;
  - `kaggle_llm_ordem.ipynb` — Qwen 2.5 de 7B, 14B e 32B via Ollama, zero-shot e few-shot.
- **Nunca executados.** O `dist/` atual (14 MB, 2026-09-12 14:14) foi gerado antes da
  re-extração e contém a segmentação v1 **sem** as páginas extras corretas. Regenerar só
  depois de fechar a segmentação, re-extrair e refazer os números (T05, T09, T12).
- Upload e execução usam a conta do Pedro: são dele (ou com autorização explícita dele).

---

## 3. O protocolo experimental (não mudar sem decisão registrada)

- **Referência *silver*:** ordem do fluxo de conteúdo do PDF (`stream`), só nos veículos em
  que ela concorda com a XY-cut (τ de Kendall mediano ≥ 0,7). A confiabilidade é decidida
  **por veículo**, não por página, para não favorecer a heurística. Na v1: 11 de 30
  veículos confiáveis.
- **Divisão por veículo** (o mesmo veículo repete o layout por anos; dividir por página
  vazaria o layout): treino = 7 veículos (Volta Redonda, Salvador, PA, PE, PR, RR, SC;
  152 páginas), validação = RN (15), teste = CE, MA, RJ (95 na v1). Os 19 veículos
  restantes são "não confiáveis" e só entram pelo Golden.
- **Entrada embaralhada:** todos os métodos recebem os blocos na mesma permutação fixa
  por página, `random.Random(f"entrada-{page_id}")`.
- **Métricas** (`src/eval/metrics.py`): τ de Kendall (principal), sucessor correto, ARD e
  ARD normalizado, BLEU de página (reportado mas quase insensível), acerto exato,
  latência. IC 95% por bootstrap (2.000 reamostras), pior caso p10, Wilcoxon pareado.
- **Golden Dataset:** anotação cega (a ferramenta nunca mostra ordem automática), grupos
  `silver` (10 páginas de veículos de teste — valida a referência automática) e `incerto`
  (20 páginas de veículos não confiáveis — decide quem acerta onde não há referência).

---

## 4. O que já sabemos (todos na segmentação v1)

### 4.1 Tabela principal — 95 páginas de teste

| Método | τ | τ p10 | Sucessor correto | ARD norm. | ms/página |
|---|---:|---:|---:|---:|---:|
| Ordem do detector (piso) | −0,005 | −0,200 | 4,8% | 0,330 | 0,0 |
| Ingênua (topo→base) | 0,753 | 0,347 | 52,5% | 0,106 | 0,0 |
| **XY-cut** | **0,837** | **0,496** | **64,2%** | **0,067** | 0,1 |
| BiLSTM só texto | 0,066 | −0,195 | 5,5% | 0,309 | 6,8 |
| BiLSTM só geometria | 0,731 | 0,459 | 27,1% | 0,105 | 7,1 |
| BiLSTM texto + geometria | 0,628 | 0,334 | 15,5% | 0,136 | 8,3 |
| LayoutLM sem layout (ablação) | 0,122 | −0,099 | 5,5% | 0,294 | 13,8 |
| LayoutLM pontual (152 págs.) | 0,671 | 0,345 | 13,4% | 0,123 | 18,0 |
| LayoutLM sucessor, cadeias (152 págs.) | 0,720 | — | 38,2% | 0,109 | 22,7 |
| LayoutLM sucessor, feixe (152 págs.) | 0,440 | — | 40,6% | 0,205 | 24,6 |
| LayoutLM pontual (3.235 págs.) | 0,786 | 0,527 | 20,8% | — | — |
| LayoutLM sucessor, cadeias (3.235 págs.) | 0,785 | — | **51,8%** | 0,086 | 20,7 |
| LLM llava:7b zero-shot (15 págs. ≤ 25 blocos) | 0,099 | — | 8,5% | — | ~segundos |

"—" = não calculado ainda (rodar `comparar.py`). Todas as diferenças da primeira rodada
contra a XY-cut foram significativas (Wilcoxon, p < 0,05).

### 4.2 Achados, em ordem de importância

1. **A geometria é o que resolve a tarefa.** Sem as caixas, o LayoutLM cai de 0,671 para
   0,122; a BiLSTM só de texto não sai do acaso.
2. **O τ esconde o texto picotado.** O LayoutLM pontual tinha τ razoável e só 13% de
   sucessor: trocava vizinhos o tempo todo. Causa: formulação pontual (uma nota por bloco).
3. **A formulação de sucessor resolve a continuidade sem perder o τ.** Com o mesmo
   orçamento de treino: 152 páginas, τ 0,671 → 0,720 e sucessor 13% → 38%; 3.235 páginas,
   τ igual (0,786 × 0,785) e sucessor 21% → 52%.
4. **Decodificar o caminho inteiro pela matriz de sucessores destrói o τ** (0,44): o
   modelo acerta o próximo parágrafo na coluna e erra o salto entre colunas. A
   **decodificação em cadeias** (arestas de alta confiança formam trechos; trechos
   ordenados pela cabeça de posição) é o que funciona.
5. **Mais dados ajudam o LayoutLM pontual e não a BiLSTM:** τ 0,694 → 0,786 de 152 a
   3.235 páginas (~+0,03 por dobra, sem platô); o pior caso p10 (0,527) passa o da XY-cut
   (0,496). BiLSTM de geometria: 0,721 → 0,702.
6. **Em RI, achar a página não depende da ordem; o texto entregue depende.** Piloto em
   Japeri (269 páginas, 915 consultas geradas de 421 atos, BM25 próprio): MRR@10 entre
   0,987 e 0,998 para todas as ordens; frases de 12 palavras preservadas: 45,4% sem
   ordenar, 53,4% fluxo do PDF, 49,7% XY-cut, 45,7% LayoutLM pontual.
7. **A LLM pequena falhou** (llava:7b é multimodal e rodou 34% na CPU): τ 0,099.
8. **Fragmentação não é defeito:** o Google Document AI, em 2 páginas do Diário Oficial do
   Estado do RJ, dá a mesma distribuição de tamanho de bloco (mediana 5 palavras, 22% de
   blocos de uma palavra). A amostra é pequena; a T10 amplia com as 12 páginas do Azure. **Sobreposição de
   caixas é defeito:** assinatura de linha cortada ao meio.
9. **Hipótese em aberto:** a super-segmentação da v1 pode inflar o sucessor das
   heurísticas geométricas (parágrafo picotado em caixas empilhadas = "próximo bloco"
   trivial). A análise de sensibilidade responde (T11).

---

## 5. Como reproduzir o estado e validar mudanças

Sempre com o Python do ambiente virtual: `venv\Scripts\python.exe` (Windows).

```bash
venv\Scripts\python.exe src\eval\metrics.py
```
Auto-teste das métricas: imprime uma tabela com casos controlados (página invertida,
troca de vizinhos).

```bash
venv\Scripts\python.exe src\data\reextrair.py --entrada data\processed\blocos --so-medir
```
Mede a qualidade de uma segmentação (sobreposição, blocos de uma palavra) sem escrever nada.

```bash
venv\Scripts\python.exe src\data\reextrair.py --entrada data\processed\blocos_v1 --saida data\processed\blocos_teste --workers 16
```
Re-extrai **as mesmas páginas** com o código atual para outra pasta (~5 min para 777
páginas com 16 processos; as 3.117 extras levam mais de uma hora por causa dos PDFs de PE).

Para testar o segmentador numa página só, sem escrever arquivos, o padrão é:
`pdfplumber.open(pdf).pages[n]` → `palavras_da_pagina()` → `segmentar()` (ambos em
`src/data/extrator.py`). As quatro páginas-problema estão na seção 2.2.

```bash
set TCC_DIR_BLOCOS=data\processed\blocos_v1
venv\Scripts\python.exe src\eval\comparar.py
```
Refaz a tabela principal sobre a segmentação em que as predições atuais foram geradas.

Não há suíte de testes automatizados: a validação é feita por esses scripts, pelas
métricas de qualidade e por inspeção visual das páginas-problema.

---

## 6. Próximos passos, em ordem

As tarefas executáveis, com dono sugerido e critério de pronto, estão no quadro
[`COMUNICACAO_AGENTES.md`](../COMUNICACAO_AGENTES.md) (T01 a T15). Aqui vai o raciocínio
da ordem:

1. **Proteger contra falhas silenciosas** (T01) antes de gastar GPU: a proteção foi
   implementada e aguarda revisão cruzada; sem `blocos_extra`, o treino ampliado agora
   termina com erro explícito.
2. **Preservar a v1** (T04) antes que qualquer re-execução a sobrescreva: ela é a linha de
   base da análise de sensibilidade. `caracterizar.py` sobrescreve `splits.json`, os
   treinos sobrescrevem os checkpoints e `figuras.py` sobrescreve `docs/figuras/`.
3. **Fechar o segmentador com medida, não no olho** (T02, T03). Montar uma amostra fixa de
   páginas e uma tabela versão × métrica (blocos por página, sobreposição, % de blocos de
   uma palavra, maior bloco em palavras, páginas rejeitadas pelo filtro). Critério:
   sobreposição baixa **e** nenhuma fusão de texto corrido **e** nenhuma fragmentação
   explosiva nas quatro páginas-problema. A referência externa possível são os blocos das
   APIs comerciais (T10): Azure em 12 páginas (Estado do RJ e Japeri) e Google em 2.
4. **Re-extrair tudo com a versão final** (T05) e **regenerar o Golden** (T06) — o Golden
   só enquanto não houver anotação humana válida.
5. **Recalcular `splits.json`** (T07): a lista de veículos confiáveis foi decidida sobre a
   v1. Se mudar, é decisão metodológica — registrar no quadro e confirmar com o Pedro.
6. **Pedro anota o Golden** (T08).
7. **Refazer os números** (T09) localmente e **rodar o Kaggle** (T12).
8. **Análise de sensibilidade** v1 × final (T11) e **atualizar resultados e
   apresentação** (T13).

---

## 7. Perguntas em aberto para o orientador

Detalhadas em [`ROADMAP.md`](ROADMAP.md): foco em RI e avaliação extrínseca; procedência
dos 421 atos de Japeri (manual ou Azure); aceitabilidade do rótulo silver; Goiás como teste
fora do domínio; uso do Kaggle ou de GPU do laboratório; créditos para APIs comerciais;
granularidade de bloco × palavra; papel do DocLayNet.

---

## 8. O que NÃO fazer

A lista completa está em [`AGENTS.md`](../AGENTS.md). As três que mais custariam:

- **Apagar ou regenerar anotação humana.** Já aconteceu uma vez nesta sessão: um registro
  com nome de anotador de teste era, na verdade, trabalho do Pedro. Arquive, não apague.
- **Avaliar predições contra blocos de outra segmentação.** Os identificadores mudam.
- **Rodar dois treinos na GPU ao mesmo tempo** (RTX 4050, 6 GB).
