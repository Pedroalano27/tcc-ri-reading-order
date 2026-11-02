# Análise Aprofundada do Ecossistema Acessilia para o TCC

**Data da análise:** 13 de setembro de 2026  
**Autor:** Antigravity CLI (`gemini-3.8-flash-high`), sob despacho do Claude  
**Contexto:** Avaliação técnica dos repositórios de código aberto do projeto **Acessilia** (A11yDevs) para reaproveitamento no TCC de Recuperação de Informação e Ordem de Leitura em Diários Oficiais (INF-UFG).

---

## 1. Visão Geral dos Três Repositórios

Os três repositórios estão localizados localmente em `C:\Users\pedro\OneDrive\Documentos\Acessilia\` e foram analisados em modo estritamente **somente leitura**.

```
C:\Users\pedro\OneDrive\Documentos\Acessilia\
├── acessilia/                      (aplicação principal, backend, frontend, docs, bugs)
├── acessilia-structure-extractor/  (serviço de extração estrutural, Docling, PyMuPDF, schemas)
└── acessilia-dataset/              (documentos de teste, intermediários e saídas acessíveis)
```

### 1.1 `acessilia`

- **Propósito:** Plataforma completa de acessibilização de documentos e imagens (PDF, DOCX, imagens), convertendo arquivos para múltiplos formatos acessíveis (TXT, DOCX, PDF, PDF/UA, HTML, MP3 via TTS, ZIP) utilizando modelos de linguagem/visão (Ollama, OpenRouter), estruturação de layout (Docling) e planejamento de acessibilidade (PDDL / Agno).
- **Arquitetura:** Estruturada em camadas *Domain → Application → Interface*:
  - `backend/` (Domínio e Aplicação):
    - `backend/api/`: Servidor FastAPI (`server.py`), executor de tarefas em segundo plano (`worker.py`), endpoints REST para upload, jobs, histórico e download.
    - `backend/core/manifest/`: Implementação completa do gerador de manifesto estrutural (`builder.py`, 825 linhas; `models.py`, 338 linhas; `docling_extractor.py`, `pymupdf_extractor.py`, `schema.py`).
    - `backend/agents/`: Orquestrador de planejamento PDDL (`pddl_orchestrator.py`, 379 linhas) com suporte aos backends `docling` e `pymupdf`.
    - `backend/pipeline/`: Normalização e sanitização semântica (`sanitizer.py`, `table_ast.py`, `semantic_rules.py`).
    - `backend/export/`: Renderizadores e exportadores para HTML, DOCX, PDF/UA e áudio MP3 (`html_export.py`, `tts_export.py`, etc.).
  - `frontend/` (Interfaces):
    - `frontend/cli/`: Interface de linha de comando (`run.py`, `bot-acess`).
    - `frontend/web/`: Painel web Jinja2/HTML (`app.py`, porta 8001).
    - `frontend/telegram/`: Bot de mensageria via Telegram (`bot.py`).
- **Estado (Git):**
  - Último commit: `e71475a32c3ae2efed196a975756086c2937710b` (AuthorDate: 2026-09-08 22:00:18 -0300; CommitDate: 2026-09-13 16:01:39 -0300) por Pedroalano27: `"docs(bugs): reenquadra 0005 como causa raiz confirmada e correcao sugerida"`.
  - Branch ativa: `docs/registro-bugs-homologacao` (285 commits no histórico).
  - Alterações locais em andamento: exatamente 3 itens detectados via `git status --short`: `M backend/locales/en_US/LC_MESSAGES/messages.po`, `M backend/locales/pt_BR/LC_MESSAGES/messages.po` e untracked `?? frontend/bot.lock`.
- **Maturidade:** Alta. Possui 49 arquivos de teste em `tests/`, cobrindo clientes, renderizadores, pipeline canônico e resiliência. A suíte principal sem modelos pesados (`pytest -m "not docling"`) executa com 136 testes passando e 0 skips. O CI (`.github/workflows/ci.yml`) possui matriz para as variantes `slim` e `docling`, cache persistente de modelos Hugging Face e build automatizado de imagens Docker para entrega contínua.

### 1.2 `acessilia-structure-extractor`

- **Propósito:** Microsserviço e CLI especializado na extração estrutural de documentos, isolando a carga pesada de processamento de layout (Docling in-process ou `docling-serve` remoto) e gerando um `ProcessingManifest` validado por JSON Schema Draft 2020-12.
- **Arquitetura:**
  - `src/acessilia_extractor/cli/`: Ponto de entrada CLI (`acessilia-extract`, `__init__.py`, 123 linhas).
  - `src/acessilia_extractor/extractors.py`: Interfaces e implementações `DoclingManifestExtractor` (Docling local via `DocumentConverter`) e `DoclingServeExtractor` (cliente HTTP para API REST v1 do container `docling-serve`).
  - `src/acessilia_extractor/pipeline/`: Módulos de suporte `sanitizer.py` (72 linhas) e `table_ast.py` (329 linhas).
  - `schemas/processing_manifest.schema.json`: Esquema JSON formal com 760 linhas.
  - `tests/snapshot_comparator.py`: Módulo comparador de manifestos normalizados que descarta campos voláteis (timestamps, IDs de execução) para aferir estabilidade de regressão.
  - `scripts/validate_snapshots.py`: Automação para validar a extração contra os snapshots de `acessilia-dataset`.
- **Estado (Git):**
  - Último commit: `bb96c32290f9111db9d664a695ce3a6e07c216a2` (2026-08-17 02:12:43 -0300) por Marcelo Akira Inuzuka: `"Atualiza submódulo dataset (processing-manifests docling 2.118)"`.
  - Branch ativa: `main` (9 commits no histórico). Working tree limpa.
- **Maturidade:** Em desenvolvimento / Média. Possui infraestrutura de contêineres (`Dockerfile` multi-stage, `docker-compose.yml`, `docker-compose.test-snapshot.yml`), mas **não possui integração contínua (sem `.github/`)**.
  - **Achado crítico de versionamento:** O arquivo `.gitignore` (linha 30: `MANIFEST`) no sistema Windows (NTFS sem distinção de maiúsculas/minúsculas) causou a ignorância silenciosa do diretório `src/acessilia_extractor/manifest/` no commit `0d18859`. Como resultado, os arquivos `builder.py`, `models.py` e `schema.py` não foram incluídos neste repositório isolado, embora existam e funcionem plenamente no repositório principal `acessilia` (`backend/core/manifest/`).

### 1.3 `acessilia-dataset`

- **Propósito:** Repositório compartilhado de governança de dados contendo documentos fonte de teste, artefatos intermediários estruturados e saídas esperadas para validação de ponta a ponta e testes de snapshot do ecossistema. Utilizado como submódulo Git (`tests/dataset`) pelo extrator estrutural.
- **Arquitetura:**
  - `input/`: Documentos de teste enumerados (`001.pdf` a `008.pdf`, `005.jpeg`) e `input/manifest.csv` indexando formato, tamanho, páginas, idioma e desafios de acessibilidade (tabelas, equações, gráficos).
  - `intermediate/`: Artefatos derivados mapeados por `intermediate/manifest.csv`:
    - `processing-manifest/*.json`: Manifestos estruturais gerados pelo extrator.
    - `canonical-document/*.json`: Documentos acessíveis canônicos com texto e estrutura de blocos.
    - `pddl-plan/*.json`: Planos de acessibilização com seleção de obrigações e custos nominais.
  - `outputs/`: Formatos finais acessíveis (`txt/`, `html/`, `pdf/`, `pdf_ua/`, `mp3/`, `epub/`) e `outputs/manifest.csv`.
- **Estado (Git):**
  - Último commit: `ce8a753855558b9e4aac382b33ad67415a3c3110` (2026-08-17 02:12:42 -0300) por Marcelo Akira Inuzuka: `"Atualiza processing-manifests para docling 2.118 (docling-serve 1.30)"`.
  - Branch ativa: `main` (8 commits no histórico). Working tree limpa.
- **Maturidade:** Alta em organização de dados. Registros reprodutíveis com hashes SHA-256 e metadados de extração; sem rotinas de CI autônomas por ser um repositório puramente de dados e fixtures.

---

## 2. Extração de Estrutura em Detalhe

### 2.1 Uso do Docling e do PyMuPDF

O ecossistema implementa duas estratégias complementares de extração:

1. **Docling (Motor Principal de Layout e DLA):**
   - **Modo Local (`DoclingManifestExtractor`, em `extractors.py:33-116`):** Instancia `DocumentConverter` com pipeline `PdfPipelineOptions(do_ocr=True, do_table_structure=True, ocr_options=RapidOcrOptions(backend="torch"), enable_remote_services=False)`. A extração opera sobre a página inteira, aplicando modelos de Document Layout Analysis (DLA) e Table Structure Recognition (TableFormer/Heron).
   - **Modo Remoto (`DoclingServeExtractor`, em `extractors.py:118-176`):** Envia o arquivo PDF via HTTP multipart para o serviço `docling-serve-cpu:latest` na rota `/v1/convert/file` com `to_formats=["json"]`. O JSON de resposta do Docling v2 é convertido pelo wrapper `_BuildDoclingDocument` (`extractors.py:178-240`), que normaliza coleções heterogêneas (`texts`, `pictures`, `tables`, `groups`) expondo o método iterador padrão `iterate_items()`.
2. **PyMuPDF / Fitz (Extrator Rápido de Fallback):**
   - Implementado em `acessilia/backend/core/manifest/pymupdf_extractor.py:29-210` como `PyMuPDFManifestExtractor`.
   - Utiliza `fitz.open(source_path)` e lê blocos brutos de texto com `page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)`.
   - Agrupa spans de caracteres, calcula o tamanho mediano de fonte por página, detecta estilos (negrito) e infere tipos semânticos via `classify_text_block()` (títulos por tamanho de fonte relativo, listas por marcadores `-`, `*`, `1.`).
   - Retorna um `_PseudoDocument` que simula a interface do Docling (`iterate_items()`, `pages`, `num_pages()`). Opera em centésimos de segundo, sem dependência de PyTorch ou modelos de visão, servindo de contingência quando o Docling falha ou não está instalado.

### 2.2 O Esquema Canônico (`schemas/processing_manifest.schema.json` e `models.py`)

O modelo `ProcessingManifest` (versão 1.1.0, esquema `urn:a11y-devs:schema:processing-manifest:1.1.0`) é definido em Pydantic com modo estrito (`ConfigDict(extra="forbid")`) em `models.py:39`:

#### Tipologia de Elementos (`ElementType`, `models.py:15-33`)
O esquema define 17 tipos normalizados:
`title`, `heading`, `paragraph`, `list_item`, `table`, `picture`, `formula`, `code`, `caption`, `footnote`, `page_header`, `page_footer`, `checkbox`, `key_value`, `form`, `group`, `unknown`.

#### Sinais Armazenados por Cada Elemento (`ManifestElement`, `models.py:83-97`)
- `id`: Identificador único formatado (`element-000001`, sequencial 1-based com preenchimento a 6 dígitos).
- `type`: Classe normalizada (`ElementType`).
- `raw_label`: Rótulo original devolvido pelo extrator (ex.: `section_header`, `text`, `table`, `picture`).
- **`reading_order`:** Inteiro sequencial $\ge 1$ que define a posição do elemento no fluxo de leitura.
- `hierarchy_level`: Nível hierárquico inteiro $\ge 0$ (ex.: títulos de nível 1 a 6, corpo de texto nível 1).
- `text`: Texto extraído, higienizado via `sanitize_text()`. Pode ser `None` em figuras ou tabelas não linearizadas.
- `source_ref` e `parent_ref`: Ponteiros de URI interna do documento original (ex.: `#/texts/0`, `#/body`).
- `parent_id`: Identificador do elemento pai resolvido no grafo do documento.
- `page_number`: Número da página (1-based).
- `confidence`: Confiança do classificador (`float` entre 0.0 e 1.0 ou `None`).
- **`provenance` (`list[Provenance]`):** Rastreabilidade física exata:
  - `page_number`: Página física.
  - `bbox` (`BoundingBox`): Coordenadas `left`, `top`, `right`, `bottom` e `coord_origin` (`"TOPLEFT"` ou `"BOTTOMLEFT"`).
  - `char_start` e `char_end`: Índices exatos dos caracteres no fluxo de texto.
- `metadata`: Metadados estruturais adicionais:
  - `content_layer`: Distinção entre conteúdo principal (`"body"`) e mobiliário/periferia (`"furniture"` para cabeçalhos e rodapés).
  - `docling_class`: Classe do objeto interno Docling (ex.: `TextItem`, `TableItem`, `SectionHeaderItem`).
  - Para tabelas: `table_ast`, `table_row_count`, `table_column_count`, `table_has_header`, `table_linearization_hint`.

### 2.3 Obtenção da Ordem de Leitura

No código de construção do manifesto (`acessilia/backend/core/manifest/builder.py:173`):
```python
for reading_order, (item, tree_level) in enumerate(iterator, start=1):
    ...
```
- **Fato:** O sinal `reading_order` é gerado pela enumeração direta da sequência de elementos fornecida pelo iterador `document.iterate_items(with_groups=True, traverse_pictures=True)`.
- No Docling, a travessia decorre da árvore interna de layout gerada pelo modelo de visão, que ordena os blocos hierarquicamente por meio da ordenação interna de leitura do Docling.
- No `PyMuPDFManifestExtractor` (`pymupdf_extractor.py:108-120`), a iteração segue a ordem nativa devolvida por `page.get_text("dict")` (a ordem interna dos blocos presentes no stream do PDF).

### 2.4 Tratamento de Tabelas e Causa Raiz do BUG-0005

O relatório `acessilia/docs/bugs/0005-docling-table-cells-descartadas.md` descreve uma falha de grande relevância arquitetural:

- **Sintoma:** Tabelas extraídas pelo Docling chegavam ao manifesto e ao documento final vazias (`text=None`, sem `table_ast`). No caso do arquivo `007.pdf` do dataset (cuja página é uma tabela de grandezas físicas), o documento final continha apenas 73 caracteres (o título), descartando quase 100% do conteúdo da página.
- **Investigação:** O modelo DLA e o TableFormer do Docling extraíram a tabela com perfeição (em `007.pdf`: 8 linhas, 3 colunas, 22 células e marcação de cabeçalho). O problema **não** era de visão nem do Docling.
- **Causa Raiz Confirmada (`builder.py:727-772`):** A função `_extract_table_ast(item)` inspecionava apenas os atributos e chaves `table_ast`, `table`, `table_data`, `grid`, `rows` e `cells` no próprio objeto `item`. No entanto, a API do Docling v2 armazena a malha estruturada em **`item.data.table_cells`**. Como `data` não estava entre os candidatos avaliados, o extrator ignorava os dados tabulares e atribuía `None` à estrutura da tabela.
- **Correção Validada por Pedro:** Criar um adaptador no início de `_extract_table_ast` que leia `item.data.table_cells`, agrupe as células por `start_row_offset_idx`, ordene por `start_col_offset_idx`, preserve spans (`row_span`, `col_span`) e cabeçalhos (`column_header`), alimentando a função existente `normalize_table_ast()` (`table_ast.py:18-79`).

### 2.5 Versões Fixadas nos Manifestos

Conforme verificado em `acessilia-dataset/intermediate/manifest.csv` e `processing-manifest/001.json`:
- **Docling inicial:** 2.87.0 com configuração `{"ocr": true, "table_structure": true, "remote_services": false}`.
- **Docling atualizado:** 2.118 (via `docling-serve 1.30` executado sobre CPU em container Docker).
- **Formatos de coordenadas:** Suporte a origem `TOPLEFT` (PyMuPDF) e `BOTTOMLEFT` (Docling PDF nativo), com conversão explícita no esquema.

---

## 3. Dataset: Estrutura, Geração e Lições para o Conjunto Diamond

### 3.1 Formato das Pastas

O repositório `acessilia-dataset` utiliza um padrão de três estágios estritamente indexados por arquivos CSV:

| Diretório | Arquivos Típicos | Papel | Indexador |
|---|---|---|---|
| `input/` | `001.pdf` a `008.pdf`, `005.jpeg` | Documentos fonte brutos (tutoriais de programação, apostilas, fotos) | `input/manifest.csv` |
| `intermediate/` | `processing-manifest/*.json`<br>`canonical-document/*.json`<br>`pddl-plan/*.json` | Artefatos intermediários da esteira: manifesto estrutural, documento canônico unificado e plano PDDL | `intermediate/manifest.csv` |
| `outputs/` | `txt/`, `html/`, `pdf/`, `pdf_ua/`, `mp3/`, `epub/` | Produtos finais acessíveis validados contra as diretrizes WCAG e PDF/UA | `outputs/manifest.csv` |

A geração dos artefatos intermediários é automatizada pelo script `scripts/generate_dataset_intermediates.py` (executado dentro do container `acessilia:test-pr24`), garantindo reprodutibilidade sem poluir o ambiente local.

### 3.2 O que o Acessilia Ensina para o Conjunto Diamond do TCC

O Pedro planeja criar o conjunto **Diamond** para o TCC: aproximadamente 200 páginas de diários oficiais com **caixas delimitadoras (blocos) corrigidas à mão**, permitindo treinar e avaliar diretamente a etapa de segmentação (hoje o Golden v1/v2/v3 só anota a ordem de blocos pré-extraídos).

O desenho do Acessilia traz lições essenciais para o Diamond:

1. **Separação Rígida entre Geometria, Conteúdo e Ordem:**
   O modelo `ManifestElement` ensina que cada bloco anotado deve carregar três camadas ortogonais:
   - **Camada Física/Geométrica:** `bbox` (`[left, top, right, bottom]`), página e sistema de coordenadas (sempre `TOPLEFT`, em pontos PostScript / PDF).
   - **Camada Textual Digital:** `text`, `char_start`, `char_end` (garantindo que o texto venha sempre da camada digital do PDF, sem ruído de OCR).
   - **Camada Relacional / Sequencial:** `reading_order` (ordem na leitura humana) e `parent_id` (vínculo com o ato administrativo ou coluna mãe).
2. **Taxonomia de Classes de Região Específica para Diários:**
   O Acessilia mapeia 17 classes genéricas. Para o Diamond de diários oficiais, essa lista pode ser adaptada para uma taxonomia enxuta e representativa:
   - `ato_cabecalho` (título de lei, decreto, portaria);
   - `ato_ementa` (resumo em recuo à direita);
   - `paragrafo` (texto corrido da coluna);
   - `tabela` (tabela de cargos, vencimentos, balancetes);
   - `assinatura` (cargo e nome da autoridade ao final);
   - `metadado_pagina` (cabeçalho e rodapé do diário, número de página).
3. **Esquema JSON Formal com Validação Automática:**
   Assim como o Acessilia utiliza `jsonschema` (Draft 2020-12) e Pydantic para barrar manifestos corrompidos, o Diamond precisa de um `diamond_schema.json`. O validador deve impedir erros comuns de anotação manual:
   - Bounding boxes com largura/altura nulas ou negativas (`right <= left` ou `bottom <= top`);
   - Blocos órfãos ou identificadores duplicados na mesma página;
   - Lacunas ou repetições na sequência de `reading_order` (deve ser permutação de $1 \dots N$).
4. **Governança de Proveniência e Hashes:**
   O `input/manifest.csv` do Acessilia armazena o hash SHA-256 do PDF original, contagem de páginas e identificador do documento. No Diamond, cada anotação deve registrar o SHA-256 do diário em `data/raw/` e a semente do sorteio, garantindo auditabilidade científica.

---

## 4. Lições dos Relatórios Técnicos

A leitura de `docs/bugs/`, `RELATORIO-HOMOLOGACAO.md`, `comparativo-modelos-visao.md` e dos planos de arquitetura revela lições valiosas diretamente aplicáveis ao extrator e aos modelos do TCC:

### 4.1 Desempenho e Custo Computacional do Docling

- **Tempo de Inicialização e Execução:** Em `0004-api-blocks-during-inference.md`, relata-se que a inicialização do pipeline do Docling em CPU leva cerca de 22 segundos. Na homologação (`RELATORIO-HOMOLOGACAO.md`), o processamento E2E de um PDF simples de 3 páginas levou 57 segundos.
- **Impacto para o TCC:** Nosso acervo de diários possui 4.644 PDFs (19 GB), com coleções de 777 páginas no experimento principal e 3.117 páginas extras. **Rodar o pipeline completo do Docling (com OCR e layout em todas as páginas) inviabilizaria o tempo hábil do TCC** em hardware local (levaria semanas em CPU).
- **Conclusão prática:** O TCC acertou ao adotar a estratégia de **cache persistente** em `data/processed/layout/` e ao restringir a inferência do Docling Heron apenas à detecção visual rápida de tabelas (`src/data/layout.py`), mantendo a extração textual no `pdfplumber`.

### 4.2 Limitações de Modelos de Visão Pequenos e Inconsistência de VLMs

- **Falha de Modelos Pequenos em CPU:** No relatório `comparativo-modelos-visao.md`, Pedro testou o modelo `llava:7b` via Ollama local para descrição de imagens e constatou comportamento errático: para a exata mesma imagem de silhueta, o modelo alternou aleatoriamente entre recusar a tarefa (*"Desculpe, mas não posso fornecer uma descrição..."*) e descrever a cena.
- **Conexão Direta com o TCC:** Esse resultado de homologação do Acessilia replica com exatidão o achado documentado no `HANDOFF.md` do TCC (seção 4.2, achado 7), onde a `llava:7b` obteve $\tau$ de Kendall de apenas 0,099 na ordenação de blocos (pior que heurística ingênua e próxima ao piso aleatório). Modelos multimodais pequenos (7B) quantizados em CPU não têm coerência espacial suficiente para tarefas de layout documental complexo.
- **Modelos Maiores:** A homologação do Acessilia comprovou que modelos de grande porte (`qwen3-vl-8b` em VM dedicada, com 65 s/imagem, e `minimax-m3` via API) entregam qualidade impecável sem recusas. Porém, serviços gratuitos de API são instáveis (erros 404/403 frequentes por oscilação de cotas).

### 4.3 Bloqueio de Threads e Isolamento de Tarefas

- O bug **0004** demonstrou que despachar rotinas pesadas de processamento em `asyncio.create_task()` sem transferir a execução para processos ou threads dedicadas (`asyncio.to_thread` / `run_in_executor`) congela o event loop e derruba a responsividade.
- No TCC, isso reforça a importância das diretrizes de `AGENTS.md`: rotinas pesadas de extração e segmentação devem rodar sempre em `multiprocessing.Pool` com contagem explícita de workers, sem concorrência descontrolada que esgote a memória RAM ou a VRAM da GPU (RTX 4050, 6 GB).

---

## 5. Oportunidades para o TCC (Ordenadas por Valor / Esforço)

Abaixo estão detalhadas as cinco principais oportunidades de reaproveitamento, ordenadas pela relação valor científico versus esforço de implementação.

---

### Oportunidade 1: Esquema Canônico e Validador Estrutural para o Dataset Diamond
*Relação Valor / Esforço:* **Máxima (Alto Valor / Baixo Esforço)**

- **O que reaproveitar:**
  - `acessilia/backend/core/manifest/models.py` (linhas 39-97: `BoundingBox`, `Provenance`, `ManifestElement`, `ElementType`);
  - `acessilia-structure-extractor/schemas/processing_manifest.schema.json` (validação Draft 2020-12).
- **Como encaixaria no TCC:**
  - O TCC precisa do conjunto Diamond (~200 páginas com caixas delimitadoras corrigidas pelo Pedro). Em vez de inventar um formato ad-hoc, adota-se um subconjunto enxuto do esquema do Acessilia, armazenado em `data/diamond/anotacoes.jsonl`.
  - Cada entrada representa a página e sua lista de blocos: `id`, `bbox`, `reading_order`, `tipo` (`titulo`, `corpo`, `tabela`, `cabecalho_rodape`), `origem` (`auto` ou `corrigido_humano`) e `texto`.
- **Esforço estimado:** Baixo (1 a 2 dias). Basta criar `src/data/diamond_schema.py` com validação Pydantic.
- **Riscos:** Praticamente nulos. Esquema já testado e compatível com JSON padrão.

---

### Oportunidade 2: Módulo de Testes de Regressão e Comparador de Snapshots de Segmentação
*Relação Valor / Esforço:* **Muito Alta (Alto Valor / Baixo a Médio Esforço)**

- **O que reaproveitar:**
  - `acessilia-structure-extractor/tests/snapshot_comparator.py` (linhas 47-98: `_strip_keys`, `_normalize_manifest`, `_normalize_metadata`).
- **Como encaixaria no TCC:**
  - O maior desafio do projeto nas últimas sessões foi a instabilidade do segmentador (`src/data/extrator.py`), que oscilou entre v1 (sobreposição), B (superfusão de texto corrido) e C (hiperfragmentação).
  - O script de snapshot compara a saída do extrator contra uma amostra de referência de páginas (as 4 páginas-problema + 40 da bancada T02), descartando variações irrelevantes e alertando imediatamente se uma alteração de código quebrar caixas de tabela ou fundir colunas vizinhas.
- **Esforço estimado:** Baixo a Médio (~2 dias). Adaptação de `snapshot_comparator.py` para operar sobre o formato de blocos do TCC.
- **Riscos:** Baixos. Protege o projeto contra regressões silenciosas antes de re-extrações massivas.

---

### Oportunidade 3: Proposta de Regiões Multiclasse do Docling Heron Fundidas às Palavras do PDF
*Relação Valor / Esforço:* **Alta (Alto Valor Científico / Médio a Alto Esforço)**

- **O que reaproveitar:**
  - Mapeamento de rótulos do Docling (`builder.py:38-59`, `LABEL_TO_TYPE`);
  - Estratégia de casamento espacial entre bboxes do detector visual e texto digital (`src/data/layout.py` e `src/data/extrator.py`).
- **Como encaixaria no TCC:**
  - Atualmente, `src/data/layout.py` usa o modelo visual Docling Heron (RT-DETRv2 treinado no DocLayNet) **apenas para rotular tabelas**. As demais regiões (títulos, parágrafos, colunas) dependem de regras manuais de calhas e linhas de base em `extrator.py`.
  - A oportunidade consiste em capturar **todas as classes** preditas pelo Heron (parágrafos, títulos de seção, tabelas) e utilizá-las como propostas de regiões ("region proposals"), fundindo as palavras da camada digital do PDF que caem dentro de cada envelope geométrico.
- **Esforço estimado:** Médio a Alto (3 a 5 dias de engenharia e avaliação rigorosa).
- **Riscos:** O Docling Heron pode cometer erros de fusão entre colunas estreitas em diários com diagramação densa (como RJ ou MA). Exigirá comparação direta de $\tau$ de Kendall e taxa de sobreposição na bancada T02 antes de adoção.

---

### Oportunidade 4: Fundamentação e Avaliação Extrínseca: A Ordem de Leitura como Requisito de Acessibilidade
*Relação Valor / Esforço:* **Alta (Alto Valor Textual / Baixo Esforço de Implementação)**

- **O que reaproveitar:**
  - Conceitos de acessibilidade digital e conformidade WCAG/PDF-UA formalizados na documentação do Acessilia (`docs/bugs/0005-docling-table-cells-descartadas.md`, `schemas/accessible_document.schema.json`, linearização de tabelas em `table_ast.py:linearize_table_for_text`).
- **Como encaixaria no TCC:**
  - O TCC aborda ordem de leitura pelo viés de Recuperação de Informação (fidelidade de passagens recuperadas pelo BM25). O Acessilia fornece a justificativa de impacto humano e social: para tecnologias assistivas (leitores de tela NVDA, sintetizadores de voz), **a ordem de leitura correta é a diferença entre a compreensão e a completa desinformação** de atos estatais por cidadãos com deficiência visual.
  - Pode integrar a introdução da monografia, a motivação em `docs/ENTENDA_O_PROJETO.md` e a discussão de impacto social.
- **Esforço estimado:** Baixo (redação conceitual e enriquecimento bibliográfico).
- **Riscos:** Nenhum.

---

### Oportunidade 5: Heurísticas Semânticas para Detecção de Títulos e Atos em Destaque
*Relação Valor / Esforço:* **Média (Médio Valor / Médio Esforço)**

- **O que reaproveitar:**
  - Regras de identificação de caixas e títulos de `builder.py:209-294` (`_normalize_callout_groups`, `_is_callout_title_candidate`, `_uppercase_ratio`).
- **Como encaixaria no TCC:**
  - Ajudar o segmentador a identificar cabeçalhos centralizados de atos (ex.: "RESOLVE:", "DECRETO Nº 1.234") que cortam a página horizontalmente e atuam como separadores naturais de leitura.
- **Esforço estimado:** Médio (2 a 3 dias).
- **Riscos:** Médio. Regras criadas para apostilas didáticas precisam ser calibradas para o jargão jurídico de diários oficiais para evitar cortes espúrios.

---

## 6. Licenças, Riscos Legais e Créditos

### 6.1 Licença de Cada Repositório

| Repositório | Licença Declarada | Situação Real nos Arquivos | Compatibilidade com o TCC |
|---|---|---|---|
| `acessilia` | MIT | `pyproject.toml:6` (`license = "MIT"`), `README.md:232` (MIT © 2026 Jhonata Fernandes Cordeiro). Sem arquivo `LICENSE` na raiz. | **Totalmente compatível** |
| `acessilia-structure-extractor` | MIT | `pyproject.toml:10` (`license = {text = "MIT"}`). Arquivo `LICENSE` possui cabeçalho MIT (linhas 1-22), seguido por texto residual da GPL v3 (linhas 23-667), decorrente do commit `f61f326` ("Troca licença de GPL v3+ para MIT"). Intenção autoral comprovada: MIT. | **Compatível** (reaproveitando o código autoral sob MIT) |
| `acessilia-dataset` | MIT | Arquivo `LICENSE` com texto canônico da licença MIT (Copyright (c) 2026 A11yDevs). | **Totalmente compatível** |

### 6.2 O Alerta Crítico do PyMuPDF (GNU AGPL-3.0)

A biblioteca **PyMuPDF** (importada como `fitz`) é distribuída comercialmente pela Artifex Software sob a **GNU Affero General Public License v3 (AGPL-3.0)**.
- **Implicação da AGPL-3.0:** Trata-se de uma licença com efeito viral estrito (copyleft forte), inclusive para interação remota via rede. Qualquer software que importe ou realize link direto com o PyMuPDF precisa ter seu código-fonte integral licenciado sob a AGPL-3.0 ao ser distribuído ou disponibilizado publicamente.
- **Impacto no TCC:**
  - O TCC atualmente utiliza `pdfplumber` (baseado em `pdfminer.six`, licença MIT) para a extração digital de palavras, e `transformers` / `torch` (Apache-2.0) para os modelos.
  - Se reaproveitarmos módulos do Acessilia que importam PyMuPDF (como `pymupdf_extractor.py`), ou se executarmos a tarefa opcional T14 ("Extrator mais rápido com PyMuPDF"), **o repositório do TCC passará a ser legalmente governado pela AGPL-3.0**.
  - **Recomendação jurídica:**
    1. Para os módulos centrais (`src/data/extrator.py`, modelos e pipelines principais), **não importar PyMuPDF**. Manter o uso do `pdfplumber` (MIT).
    2. Reaproveitar do Acessilia apenas as estruturas de dados, heurísticas lógicas e esquemas Pydantic, que são código autoral MIT do time do Acessilia.
    3. Se o PyMuPDF for utilizado em algum script auxiliar de benchmark (T14), isolá-lo em script independente com declaração explícita de licença AGPL.

### 6.3 Modelos Pré-treinados (Docling Heron e DocLayNet)

- O modelo visual **Docling Heron** (`docling-project/docling-layout-heron`) é baseado na arquitetura RT-DETRv2 e publicado sob licença permissiva **Apache-2.0**.
- O corpus de anotação de layout **DocLayNet** (IBM) é licenciado sob a **CDLA-Permissive-1.0** (Community Data License Agreement – Permissive), que autoriza expressamente o uso, treinamento e publicação acadêmica com atribuição.
- Não há qualquer impedimento legal no uso do Heron para geração de cache de layout offline.

### 6.4 Texto Sugerido para Créditos

#### Para a Monografia / Artigo do TCC (Seção Metodológica / Agradecimentos)
> *"Agradecemos aos desenvolvedores do projeto de código aberto Acessilia (A11yDevs) — em especial a Jhonata Fernandes Cordeiro e Marcelo Akira Inuzuka —, cujas definições de esquema canônico para documentos estruturados e análises sobre o comportamento do motor Docling serviram de referência técnica para a padronização do nosso conjunto de dados e para a contextualização do impacto da detecção de ordem de leitura na acessibilidade digital."*

#### Para o `README.md` do Repositório do TCC
> ### Créditos e Agradecimentos
> Este projeto reutiliza e adapta conceitos arquiteturais de esquemas estruturais desenvolvidos pelo projeto de código aberto [Acessilia](https://github.com/A11yDevs/acessilia) (licença MIT, A11yDevs). Agradecemos aos contribuidores do Acessilia pelo compartilhamento de ferramentas e lições técnicas no tratamento de documentos digitais e acessibilidade.

---

## 7. O que NÃO Vale a Pena Reaproveitar (com Justificativa)

Para manter o foco e evitar desperdício de tempo no cronograma do TCC, as seguintes frentes do Acessilia devem ser **descartadas**:

1. **Motor de Planejamento PDDL e Agno (`core/planning/`, `core/execution/`):**
   - *Por quê:* O Acessilia usa PDDL (Fast Downward) para calcular a rota ótima de transformação acessível (ex.: se deve chamar OCR, MathML ou descrição visual para cada obrigação). No TCC, nosso problema é estritamente predizer a permutação ordenada dos blocos de texto e avaliar a recuperação de informação via BM25. Introduzir planejadores clássicos adicionaria centenas de dependências sem qualquer ganho experimental.
2. **Pipeline Completo do Docling em Tempo Real (com OCR):**
   - *Por quê:* Rodar OCR local via Docling consome de 1 a 2 minutos por página em CPU. Como os diários oficiais do acervo (19 GB) já contêm texto digital nativo, a extração via `pdfplumber` roda em frações de segundo por página. O Docling só tem valor no TCC rodado offline para gerar bounding boxes de tabelas em cache (`data/processed/layout/`).
3. **Módulos de Fala / TTS e Renderizadores Finais (`backend/export/`, `edge-tts`):**
   - *Por quê:* Gerar arquivos `.mp3`, `.docx` ou `.epub` faz parte de um produto de tecnologia assistiva, enquanto o TCC se encerra na avaliação de métricas de ordenação ($\tau$, sucessor, ARD) e avaliação de RI (MRR, fidelidade de frases).
4. **Submódulo Git do `acessilia-dataset` no TCC:**
   - *Por quê:* O dataset do Acessilia contém materiais pedagógicos gerais (tutoriais Java, apostilas de ciências). O domínio de Diários Oficiais tem características visuais e semânticas completamente distintas (três a quatro colunas densas, atos jurídicos contínuos). Incorporar os PDFs do Acessilia poluiria o domínio experimental.
5. **Painel Web, Bot de Telegram e Infraestrutura SaaS (`frontend/`, `backend/api/`):**
   - *Por quê:* O escopo do trabalho acadêmico é científico e experimental, operado via scripts de linha de comando e notebooks no Kaggle, e não um serviço web multiusuário com fila de atendimento.
6. **Dependência Obrigatória do PyMuPDF:**
   - *Por quê:* A licença AGPL-3.0 imporia restrições de licenciamento desnecessárias ao código-fonte do TCC, sendo perfeitamente dispensável frente à maturidade do `pdfplumber`.

---
*Documento elaborado estritamente com base nos artefatos inspecionados em disco, preservando a integridade dos repositórios consultados.*
