# Relatório Técnico: Mecanismos de Ordem de Leitura no Acessilia e Oportunidades para o TCC

> **Resumo Executivo (6 linhas):**
> 1. O Acessilia não possui modelo próprio de ordenação: herda a ordem do Docling por enumeração (`builder.py:304`) ou adota ordenação ingênua topo-base no PyMuPDF (`region_extractor.py:96`).
> 2. O protótipo `reorder_xycut.py` no Acessilia é um porte do próprio TCC (desligado por padrão via `READING_ORDER_XYCUT=0`) e é mais simplificado que o código atual da bancada.
> 3. Cabeçalho e rodapé recebem rótulos semânticos (`content_layer: "furniture"`), mas não possuem política de margens na ordenação; marcas laterais não são tratadas.
> 4. O `acessilia-dataset` possui 46 páginas processadas em JSON, sem nenhum Diário Oficial e sem layouts multicoluna densos (apenas apostilas didáticas e slides de química).
> 5. As mudanças até 20/09 extraíram o Docling do core para o serviço Toolbox e corrigiram o isolamento do cache (Bug #99), sem nenhuma alteração algorítmica de ordem.
> 6. Para o TCC, o ordenador do Docling só é viável via contêiner ou ambiente virtual isolado em CPU; o código do Acessilia em si não adiciona ganho à heurística `projecao_local_margens`.

---

## 1. Onde e Como a Ordem de Leitura é Definida no Acessilia

A investigação detalhada do código-fonte nos três repositórios (`acessilia`, `acessilia-structure-extractor` e `acessilia-dataset`) revela como o Acessilia gera e manipula o atributo `reading_order`:

### 1.1 Construtor do Manifesto Canônico (`builder.py`)
No repositório `acessilia`, o ponto focal onde a ordem é atribuída localiza-se em [`backend/core/manifest/builder.py`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/core/manifest/builder.py#L297-L326), na função `_build_elements()`:

```python
def _build_elements(document: Any, *, enable_callouts: bool = True) -> list[ManifestElement]:
    elements: list[ManifestElement] = []
    try:
        iterator = document.iterate_items(with_groups=True, traverse_pictures=True)
    except TypeError:
        iterator = document.iterate_items(with_groups=True)

    for reading_order, (item, tree_level) in enumerate(iterator, start=1):
        ...
        elements.append(ManifestElement(id=f"element-{reading_order:06d}", reading_order=reading_order, ...))
```

- **Mecanismo:** A variável `reading_order` (inteiro $1 \dots N$) nasce puramente da **enumeração sequencial do iterador** fornecido pelo objeto de documento.
- **Origem:** O Acessilia não aplica nenhuma rede neural ou classificador de transição próprio; ele consome a árvore de nós devolvida pelo extrator subjacente.

### 1.2 Extrator Docling Local e Remoto
- **Docling Local ([`backend/core/manifest/docling_extractor.py:32-70`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/core/manifest/docling_extractor.py#L32-L70)):** Quando o Docling roda diretamente, `document` é uma instância nativa de `DoclingDocument`. O método `iterate_items()` percorre a árvore hierárquica construída pelo motor do Docling. Essa árvore resulta da combinação dos modelos de visão (Docling Heron / RT-DETRv2) e da heurística de montagem de fluxo do Docling.
- **Docling Remoto ([`acessilia-structure-extractor/src/acessilia_extractor/extractors.py:178-239`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia-structure-extractor/src/acessilia_extractor/extractors.py#L178-L239)):** No adaptador `_BuildDoclingDocument` do cliente `DoclingServeExtractor`, ocorre uma **degradação severa da ordem**. Em `_build_items()` (linhas 191–214), o código varre dicionários fixos na seguinte sequência:
  ```python
  collections = {"texts": 1, "pictures": 1, "tables": 1, "groups": 1, "key_value_items": 1, "form_items": 1}
  for coll_name, default_level in collections.items():
      items = self._payload.get(coll_name, [])
      ...
  ```
  Neste caso remoto, **todos os textos da página inteira são emitidos antes de todas as figuras e de todas as tabelas**, destruindo qualquer intercalação correta entre blocos de texto e tabelas no fluxo de leitura.

### 1.3 Extrator PyMuPDF e Ordenação Geométrica
- **No Extrator Estrutural ([`backend/core/manifest/pymupdf_extractor.py:108-146`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/core/manifest/pymupdf_extractor.py#L108-L146)):** Na função `_extract_semantic_blocks()`, o código obtém blocos via `page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)`. Ele itera diretamente na chave `blocks` na ordem devolvida pela biblioteca, sem invocar ordenação geométrica explícita (`sort=True` não é passado).
- **No Extrator de Regiões ([`backend/tools/region_extractor.py:67-97`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/tools/region_extractor.py#L67-L97)):** Na função `extract_regions()`, a ordem é forçada na linha 96:
  ```python
  regions.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
  ```
  Trata-se da **ordenação ingênua topo-abaixo ($y_0$) e esquerda-direita ($x_0$)**, que falha catastroficamente em layouts de 2 a 4 colunas ao intercalar parágrafos de colunas adjacentes. A mesma ordenação ingênua é repetida em [`backend/tools/toolbox_layout_structurer.py:158`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/tools/toolbox_layout_structurer.py#L158).

### 1.4 O Protótipo XY-cut no Acessilia (`reorder_xycut.py`)
Em [`backend/core/manifest/reorder_xycut.py`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/core/manifest/reorder_xycut.py#L1-L10), consta a implementação do algoritmo XY-cut recursivo.
- O próprio cabeçalho do módulo declara textualmente:
  > *"Portado do TCC de ordem de leitura (Pedro Alano). Puro stdlib — sem PyMuPDF (AGPL), torch ou modelos. Recebe uma lista de bounding boxes e devolve a ordem de leitura."*
- Em [`backend/core/manifest/builder.py:111-185`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/core/manifest/builder.py#L111-L185), a função `_apply_xycut_reading_order()` é acionada por `_xycut_enabled()`, que checa a variável `READING_ORDER_XYCUT` (cujo padrão é **desligado/vazio**).
- Quando ativada, a reordenação é aplicada por página: se `count_columns(caixas) >= 2`, invoca `xycut_order(caixas)`; se coluna única, preserva a ordem do extrator.
- A função renumera o campo `element.reading_order` de 1 a $N$, mas mantém a sequência da lista original para preservar referências de pais (`parent_id`).

### 1.5 O Módulo `sanitizer.py`
O arquivo [`backend/pipeline/sanitizer.py`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/backend/pipeline/sanitizer.py#L23-L58) contém unicamente as funções `sanitize_text()` e `sanitize_block_text()`. Seu objetivo é higienizar vazamentos de prompts de LLM (`PROMPT_LEAK_PATTERNS`, como "chain of thought", "system prompt") e caracteres de controle ou artefatos de formatação Markdown. **Não possui nenhuma lógica geométrica nem toca na ordem dos blocos.**

---

## 2. Tratamento de Cabeçalho, Rodapé, Marcas, Tabelas e Colunas

O calcanhar de Aquiles do TCC está em cabeçalho, rodapé e marcas laterais (responsáveis por ~34% das quebras da regra de colunas) e na transição contínua dentro da coluna. Vejamos como o Acessilia lida com cada elemento:

| Elemento | Tratamento no Acessilia | Tratamento no TCC (`projecao_local_margens`) | Comparativo / Lição |
|---|---|---|---|
| **Cabeçalho (`page_header`)** | Rotulado via Docling Heron ou `LABEL_TO_TYPE`. Recebe `metadata["content_layer"] = "furniture"`. | Isolado explicitamente por política de margens no topo: $c_y < 0,07 H$ e $y_1 < 0,10 H \rightarrow$ `inicio`. | O Acessilia apenas classifica o tipo semântico, mas **não o isola na ordem**. No XY-cut, se o cabeçalho não for largo ($\ge 0,60 W$), ele é tragado para dentro da 1ª coluna. |
| **Rodapé (`page_footer`)** | Rotulado pelo modelo; marcado como `"furniture"`. | Isolado explicitamente no fim da página: $c_y > 0,95 H \rightarrow$ `fim`. | O Acessilia não possui margem inferior na ordenação; rodapés estreitos (como data ou número de página à direita) são lidos no meio da última coluna. |
| **Número de página** | Inexistente como classe dedicada; fundido no cabeçalho ou rodapé. | Tratado dentro da faixa de margem superior ou inferior. | Nenhum avanço no Acessilia. |
| **Marcas laterais** | **Completamente ignoradas.** O texto vaza como parágrafo normal. | Detectadas via regex (`RE_MARCACAO`) e empurradas para o bloco `marcas` após o corpo e antes do rodapé. | O Acessilia não possui heurísticas de rejeição ou reposicionamento de tags de diagramação (`<#SEGRASE...>`, `<@textFrameStart>`). |
| **Tabelas** | Detectadas pelo Docling/Heron como caixa única (`type: "table"`). Células internas estruturadas no `table_ast` (após fix do BUG-0005). | Tratadas como átomos indivisíveis pelo detector YOLO (`ls3`), com prioridade de NMS sobre linhas de texto. | Conceitualmente idêntico: a tabela é um átomo e não deve ter suas linhas internas fragmentadas na ordem da página. |
| **Colunas** | Detectadas por calhas vazias no `reorder_xycut.py` (`_cortes_verticais`), sem tolerância a ruído vertical. | Projeção vertical com histograma de tinta (`vales`), detecção em janelas locais (`vales_locais`) e tratamento de pontes. | O algoritmo do TCC é muito superior e mais robusto a colunas de diários com larguras e quebras heterogêneas. |
| **Quadros / Callouts** | Detectados por recuo em relação à banda principal (`_estimate_main_text_band` em `builder.py:504`). | Tratados como seções ou pontes se atravessarem calhas. | O Acessilia possui heurística elegante para detectar caixas recuadas didáticas, mas **não altera a ordem de leitura**, apenas adiciona metadados (`callout_id`). |

---

## 3. Diagnóstico do `acessilia-dataset`

A inspeção em [`acessilia-dataset/`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia-dataset) demonstra claramente o escopo de dados do projeto:

### 3.1 Inventário dos Documentos e Intermediários
Conforme indexado em [`input/manifest.csv`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia-dataset/input/manifest.csv) e [`intermediate/manifest.csv`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia-dataset/intermediate/manifest.csv):

| ID | Arquivo Fonte | Formato | Páginas | Status Intermediário | Domínio / Conteúdo |
|---|---|---|---:|---|---|
| `001` | `java-oo-3pgs.pdf` | PDF | 3 | Concluído (`001.json`) | Tutorial de Java OO (Caelum), coluna única com callouts. |
| `002` | `java-oo-369pgs.pdf` | PDF | 369 | **Skipped** | Livro completo de Java OO. |
| `003` | `java-oo-caps-9-11-39pgs.pdf` | PDF | 39 | Concluído (`003.json`) | Capítulos de Java OO, coluna única. |
| `004` | `java-oo-tables-pg26.pdf` | PDF | 1 | Concluído (`004.json`) | Página isolada com tabela de código. |
| `005` | `sunset-skyline.jpeg` | Imagem | 1 | Concluído (`005.json`) | Fotografia geral (sem texto documental). |
| `006` | `grandezas-e-medidas-42pgs.pdf` | PDF | 42 | **Skipped** | Apresentação de Química. |
| `007` | `grandezas-e-medidas-pg3-42.pdf`| PDF | 1 | Concluído (`007.json`) | Slide com tabela de grandezas físicas. |
| `008` | `grandezas-e-medidas-pg7-42.pdf`| PDF | 1 | Concluído (`008.json`) | Slide com gráfico de barras. |

- **Total Efetivo:** Apenas 6 arquivos processados, somando **45 páginas de PDF e 1 imagem**.
- **Formato dos Intermediários:** JSON validado contra o esquema `ProcessingManifest v1.1.0`. Cada elemento armazena coordenadas da bounding box em pontos do PDF (sistema `BOTTOMLEFT`), `reading_order` sequencial e metadados (`content_layer`, `docling_class`).
- **Presença de Diários Oficiais:** **ZERO.** Não há nenhum PDF de Diário Oficial no repositório.
- **Presença de Documentos Multicoluna:** **NENHUMA.** Os documentos são apostilas com layout de livro de uma coluna com notas à margem ou lâminas de apresentação.
- **Conclusão:** O `acessilia-dataset` **não serve como bancada de teste ou avaliação extra para o TCC**. Ele reflete outro domínio documental e não estressa os desafios de segmentação ou de ordenação em colunas densas.

---

## 4. Evolução após 13/09 (Commits até 20/09)

A leitura do histórico do Git (`.git/logs/HEAD`, `.git/COMMIT_EDITMSG`) e do relatório de homologação [`docs/bugs/RELATORIO-VALIDACAO-CORE-2026-09-20.md`](file:///C:/Users/pedro/OneDrive/Documentos/Acessilia/acessilia/docs/bugs/RELATORIO-VALIDACAO-CORE-2026-09-20.md) confirma os seguintes fatos:

1. **Remoção do Docling do Core:**
   - No commit `ebf6e5e8223b` (20/09/2026), a arquitetura do core do Acessilia foi consolidada com a exclusão do Docling local das dependências diretas (`pyproject.toml`). O processamento de layout foi totalmente transferido para o serviço externo **Acessilia Toolbox** (`PIPELINE_ENGINE=pddl`).
   - O structurer local agora é exclusivamente o fallback PyMuPDF ou o cliente HTTP `ToolboxLayoutStructurer` (`backend/tools/toolbox_layout_structurer.py`).
2. **Correção do Bug #99 (Isolamento de Cache e Tokens):**
   - O PR #100 e o teste `tests/test_issue_99_cross_user.py` implementaram o isolamento criptográfico do cache entre usuários: chave gerada com SHA-256 completo (64 caracteres) + tamanho do arquivo, e amarração estrita de tokens de download ao `task_id` e ao usuário proprietário. Não houve impacto na extração estrutural.
3. **Validação de Entrada de Arquivos:**
   - Adição de `tests/test_validators_edge_cases.py` (21 testes) cobrindo regras de extensão e limites de payload em `backend/tools/validators.py`.
4. **Impacto na Ordem de Leitura:**
   - **Nulo.** Nenhuma alteração algorítmica de ordenação, nem no `reorder_xycut.py` nem no `builder.py`, foi realizada nesse período. A ordem continua dependendo do que o serviço Toolbox/Docling retorna via rede ou da ordenação ingênua do PyMuPDF.

---

## 5. Proposta Concreta: Integrando o Ordenador do Docling na Bancada do TCC

A tarefa **T29** do TCC permaneceu aberta e bloqueada devido a um conflito de dependências:
> *"T29 | Ordem de leitura do Docling como método de comparação (teste e Golden) | Claude | bloqueada: o docling-ibm-models 4.x não traz mais o preditor de ordem, e instalar o docling no venv troca o torch com CUDA; precisa de venv separado"*

### 5.1 O Problema da Dependência
No ambiente do TCC (`venv\`), o PyTorch instalado é o `torch 2.9.1+cu128` (CUDA 12.8 acelerando a RTX 4050). A instalação direta do pacote `docling` substitui o PyTorch por versões CPU ou rodas CUDA conflitantes do ecossistema Hugging Face/IBM, desconfigurando a aceleração de GPU dos modelos locais (`LayoutLM` e `YOLO`). Além disso, nas versões recentes do `docling-ibm-models` ($\ge 3.0$), o preditor de ordem foi fundido dentro da arquitetura do `StandardPdfPipeline` e do `DoclingDocument`.

### 5.2 Desenho da Solução: Módulo de Comparação Isolado em CPU

Para incluir o Docling como **mais um ordenador de base** nas bancadas do TCC (ao lado do XY-cut, da heurística ingênua e do `projecao_local_margens`), a arquitetura ideal consiste em um wrapper que execute em processo isolado em **CPU**:

```mermaid
flowchart LR
    A["Bancada TCC<br/>(Linhas e Átomos)"] --> B["Serializador de Entrada<br/>(BBoxes e Tipos)"]
    B --> C["Subprocesso / Venv Isolado<br/>(CPU: docling-core)"]
    C --> D["Montagem de DoclingDocument<br/>(TextItem / TableItem)"]
    D --> E["Linearizador de Leitura Docling<br/>(Tree Traversal / Assemble)"]
    E --> F["Permutação de Índices<br/>list[int]"]
    F --> G["Avaliação de Métricas<br/>(τ de Kendall, Sucessor, ARD)"]
```

### 5.3 Classes e Funções a Invocar
No ambiente isolado (ex.: `venv_docling` ou contêiner CPU), não é necessário rodar OCR nem renderização de imagem:
1. **Entrada esperada:** Uma lista de dicionários contendo a bounding box em pontos do PDF `[x0, top, x1, bottom]` (origem `TOPLEFT`), o tipo (`"texto"`, `"table"`, `"picture"`) e as dimensões da página $(W, H)$.
2. **Importações necessárias:**
   ```python
   from docling_core.types.doc import (
       BoundingBox,
       CoordOrigin,
       DoclingDocument,
       DocItemLabel,
       ProvenanceItem,
       Size,
   )
   ```
3. **Procedimento de Montagem Programática:**
   - Instanciar um `DoclingDocument(name=page_id)`.
   - Adicionar a página com `Size(width=W, height=H)`.
   - Para cada átomo/linha $i \in 0 \dots N-1$:
     - Criar `BoundingBox(l=b[0], t=b[1], r=b[2], b=b[3], coord_origin=CoordOrigin.TOPLEFT)`.
     - Adicionar o item semântico correspondente via API do documento:
       - Se `"table"`: `doc.add_table(prov=[...])`
       - Se `"picture"`: `doc.add_picture(prov=[...])`
       - Se `"texto"`: `doc.add_text(label=DocItemLabel.PARAGRAPH, prov=[...])`
4. **Extração da Permutação:**
   - Executar a travessia de linearização do Docling:
     ```python
     ordem_pred = []
     for item, _level in doc.iterate_items():
         idx_original = mapa_refs[item.self_ref]
         ordem_pred.append(idx_original)
     ```
   - Retornar `ordem_pred` (uma permutação estrita de $0 \dots N-1$).

### 5.4 Viabilidade Computacional
- **Execução em CPU:** Totalmente viável. O ordenamento de uma árvore de 50 a 150 blocos sem passar por OCR ou redes convolucionais leva **menos de 15 ms por página em CPU**.
- **Independência:** Implementado como um script independente (ex.: `src/eval/docling_ordem.py` chamando o interpretador isolado via `subprocess.run`), ele gera o arquivo de predição `resultados/pred_docling.jsonl`, permitindo que `src/eval/comparar.py` incorpore o Docling na tabela comparativa oficial sem tocar no ambiente PyTorch CUDA principal.

---

## 6. Leitura Honesta: O que NÃO Serve

Para evitar esforço inútil no cronograma do TCC, os seguintes componentes do Acessilia devem ser explicitamente **descartados**:

1. **A ordenação nativa do PyMuPDF / ToolboxLayout (`(r.bbox[1], r.bbox[0])`):**
   - É a clássica ordenação ingênua topo-abaixo. O TCC já a possui implementada em `src/eval/baselines.py:ordem_ingenua()`, onde já foi provado que ela colapsa em páginas com mais de uma coluna (atingindo $\tau$ baixo e alta taxa de picotamento de texto).
2. **O módulo `reorder_xycut.py` do Acessilia:**
   - Não agrega nada ao TCC porque é uma cópia direta de uma versão anterior do próprio TCC. A versão atual que o TCC já possui em `orquestracao/analises/ordem_sem_bbox.py` (`projecao_local_margens`) é substancialmente mais avançada: inclui votação por vales locais em janelas verticais, tratamento de pontes largas e a crucial política de margens (cabeçalho no topo, rodapé e marcas no final).
3. **O acervo do `acessilia-dataset` como bancada experimental:**
   - Contém apenas materiais de cursos (Java e Química) de coluna única ou slides. A incorporação desses documentos no TCC não forneceria nenhuma evidência sobre a complexidade de Diários Oficiais brasileiros (3 a 4 colunas densas, atos administrativos múltiplos, diagramação assimétrica).
4. **Heurísticas de Callout Didático (`_normalize_callout_groups`):**
   - Regras desenhadas para encontrar caixas de notas com recuo ("super e sub classe") em apostilas. Em diários oficiais, essas regras geram falsos positivos ao tentar agrupar ementas ou despachos recuados, além de não impactarem o fluxo sequencial da leitura.
5. **Sanitizador Textual (`backend/pipeline/sanitizer.py`):**
   - Projetado para filtrar vazamentos de prompt de LLMs e caracteres de controle. Os ruídos que afetam os Diários Oficiais são marcas de paginação gráfica do InDesign (`<#SEGRASE...>`, `<@textFrameStart>`), que exigem regexes específicas do domínio de publicação oficial.
6. **Motor de Planejamento PDDL / Fast Downward:**
   - Resolve o problema de selecionar quais ferramentas de acessibilidade chamar (audiodescrição vs. MathML vs. OCR). O TCC foca estritamente na permutação ótima de recuperação de ordem para Recuperação de Informação e coerência de leitura.
