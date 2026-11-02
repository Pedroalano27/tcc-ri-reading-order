# Tarefa T30 — Gerador do Dataset Rose (pseudo-rotulagem de caixas e classes por VLM)

## Contexto
O Pedro está anotando o conjunto **Diamond** (`data/diamond/diamond_piloto/`, `docs/GUIA_DIAMOND.md`)
como gabarito humano oficial de caixas delimitadoras e classes de layout (9 classes:
`titulo`, `texto`, `lista`, `tabela`, `assinatura`, `cabecalho`, `rodape`, `figura`, `outro`).

Para escalar o treino e avaliar o estado-da-arte de modelos multimodais em diários oficiais brasileiros,
criaremos o dataset **Rose** (pseudo-rotulagem por VLM). Ele segue rigorosamente o mesmo formato
do Diamond, mas é produzido de forma automatizada por VLMs (Gemini ou GPT-4o) com ancoragem
nas palavras reais da camada de texto do PDF.

## Escopo e Arquivos Permitidos
- CRIAR: `src/data/gerar_rose.py`
- CRIAR: `tests/test_rose.py`
- NÃO TOCAR: `src/data/extrator.py`, `src/anotacao/servidor.py`, `data/raw/`, arquivos de anotação humana.

## Requisitos de Implementação (`src/data/gerar_rose.py`)

1. **Entrada e Argumentos:**
   - `--colecao`: caminho com JSONLs de blocos ou tarefas (ex.: `data/diamond/diamond_piloto/tarefas.jsonl`
     ou `data/processed/blocos_extra/`)
   - `--saida`: pasta do lote (padrão: `data/diamond/rose_piloto`)
   - `--provedor`: `gemini` (padrão) ou `openai` (GPT-4o-mini / GPT-4o)
   - `--modelo`: nome do modelo na API (padrão: `gemini-2.5-flash` ou `gpt-4o-mini`)
   - `--limite`: número máximo de páginas a rotular
   - `--dry-run`: processa uma página sem chamar a API (usa mock ou só imprime o prompt estruturado)

2. **Ancoragem Fiel nas Palavras do PDF (Crítico):**
   - O script NÃO deve deixar a VLM alucinar coordenadas soltas de pixels.
   - O prompt envia:
     a) A imagem da página (renderizada via `pdfplumber`/`PIL` em 110 DPI);
     b) A lista de palavras ou blocos candidatos pré-segmentados com seus índices e textos.
   - A VLM responde em JSON estrito associando cada bloco/grupo à classe correspondente (1 a 9)
     e indicando fusões/divisões.
   - O script calcula a `bbox` [x0, top, x1, bottom] final ajustando exatamente ao envelope
     das palavras do PDF.

3. **Formato de Saída (Compatível com o Diamond):**
   - Produz `data/diamond/<lote>/tarefas.jsonl` e `data/diamond/<lote>/anotacoes.jsonl`.
   - Cada anotação possui: `page_id`, `anotador="VLM:<modelo>"`, `status="concluida"`,
     `regioes` com `id`, `classe`, `bbox` e `de`.
   - Garante que nenhuma palavra com letra/dígito fique sem caixa (`fora == 0`) e nenhuma palavra
     fique em mais de uma caixa que não seja figura (`duplas == 0`).

4. **Testes (`tests/test_rose.py`):**
   - Teste unitário de parsing da resposta da VLM para o formato de regiões do Diamond.
   - Teste de cálculo de envelope de palavras e verificação de que `salvar_diamond()` aceita a anotação sem erro.

## Validação Obrigatória
```bash
venv\Scripts\python.exe -m unittest tests.test_rose -v
venv\Scripts\python.exe -c "import ast; ast.parse(open('src/data/gerar_rose.py', encoding='utf-8').read()); print('ok')"
```
