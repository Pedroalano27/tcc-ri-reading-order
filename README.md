# Análise Comparativa de Eficácia e Eficiência Computacional entre LayoutLM e Large Language Models (LLMs) para Detecção de Ordem de Leitura em Diários Oficiais

Este repositório contém o código, a pipeline de dados e os experimentos referentes ao Trabalho de Conclusão de Curso (TCC) desenvolvido no Instituto de Informática da Universidade Federal de Goiás (INF-UFG).

**Orientador:** Prof. Dr. Thierson Couto Rosa

---

## 🧩 O Problema

Pipelines modernos de digitalização de documentos combinam **detecção de layout** (YOLO) com **OCR** para extrair o conteúdo de PDFs. O resultado é um conjunto de *bounding boxes* — cada uma com seu texto e suas coordenadas 2D `[x0, y0, x1, y1]`.

O problema é que essas caixas vêm **sem ordem de leitura**. Em Diários Oficiais, cujo layout é tipicamente **multicolunas**, a ordem em que o detector emite as caixas raramente corresponde à ordem em que um humano lê a página. O resultado é um texto embaralhado, que alterna entre colunas no meio de uma frase e **destrói a coerência sintática** do documento.

Essa perda de coerência é fatal para as aplicações a jusante: sistemas de **RAG** e **Agentes de IA** que consomem esse texto recebem contexto fragmentado, e a qualidade das respostas degrada independentemente da qualidade do modelo de linguagem usado.

**Detecção de Ordem de Leitura (*Reading Order Detection*)** é a tarefa de, dado esse conjunto desordenado de caixas, recuperar a sequência correta de leitura.

---

## 🎯 Objetivo do Projeto

Avaliar o *trade-off* clássico de Recuperação de Informação entre **eficácia** (qualidade da ordenação recuperada) e **eficiência computacional** (tempo de inferência e custo de infraestrutura) na tarefa de detecção de ordem de leitura.

Comparamos duas famílias de abordagens:

1. **Modelo leve, especializado e consciente de layout — LayoutLM.**
   Baseado no BERT, o LayoutLM incorpora as coordenadas 2D das caixas diretamente nos *embeddings* de entrada, ou seja, **entende a geometria da página nativamente**. É um modelo pequeno, executável localmente, com custo de inferência previsível.

2. **Modelos de Linguagem de Larga Escala (LLMs), via Ollama.**
   Excelente capacidade de representação contextual e raciocínio *zero-shot*, mas com custo computacional de atenção quadrático $O(N^2)$ e latência substancialmente maior.

A **LSTM** convencional entra como *baseline* de rede recorrente: por operar sobre a sequência textual sem representação nativa da geometria 2D, serve para dimensionar o ganho que a consciência de layout efetivamente traz.

A hipótese sob teste é que **um modelo leve e especializado em layout alcança eficácia competitiva com LLMs generativas a uma fração do custo computacional** — o que, se confirmado, tem implicação prática direta no processamento de grandes volumes de diários.

---

## 📏 Métricas de Avaliação

| Métrica | O que mede |
|---|---|
| **BLEU de página** | Sobreposição de n-gramas entre o texto reconstruído na ordem predita e o texto na ordem do padrão-ouro. Captura se os blocos ficaram *localmente* bem encadeados. |
| **ARD** (*Average Relative Distance*) | Distância média entre a posição predita e a posição correta de cada caixa. Captura o erro de ordenação *global*, penalizando blocos deslocados para longe. |
| **Tempo de inferência** | Latência por página, medida nas mesmas condições de hardware para todas as abordagens. |

As duas primeiras são as métricas consagradas na literatura de *reading order detection*; a terceira é o eixo de eficiência do trade-off investigado.

---

## 📊 Estratégia de Dados

O projeto trabalha com três conjuntos, em ordem crescente de fidelidade ao caso real:

1. **Pré-dataset sintético** (`data/predataset/`) — páginas simuladas geradas por [`get_predataset.py`](get_predataset.py), com layout multicolunas e ordem de leitura conhecida por construção. Serve para validar a pipeline ponta a ponta antes de tocar em dados reais.
2. **DocLayNet** — dataset público de análise de layout de documentos (leis, editais, relatórios) com anotação humana, disponível no Hugging Face. Base de treino e validação em escala.
3. **Golden Dataset** — padrão-ouro de **20 páginas de Diários Oficiais do Estado de Goiás**, com a ordem de leitura anotada manualmente. É o conjunto que mede o desempenho no domínio-alvo real.

---

## 📂 Estrutura do Repositório

```text
├── data/
│   ├── raw/                # PDFs brutos dos Diários Oficiais (não versionado)
│   └── predataset/         # Pré-dataset sintético de ordem de leitura (JSON)
├── models/                 # Pesos e checkpoints treinados (não versionado)
├── notebooks/              # Análise exploratória e geração de gráficos
├── src/
│   ├── data/               # Coleta, parsing e extração de bounding boxes dos PDFs
│   ├── models/             # Arquiteturas: LayoutLM e baseline LSTM
│   └── eval/               # Cliente LLM (Ollama) e cálculo das métricas (BLEU, ARD, tempo)
├── docs/                   # Fichamento bibliográfico e notas de direcionamento
├── get_predataset.py       # Gerador do pré-dataset sintético
├── requirements.txt        # Dependências do projeto
└── README.md               # Este arquivo
```

---

## ⚙️ Instalação e Execução

### 1. Clonar e configurar o ambiente

O projeto usa **Python 3.11** (versões mais novas ainda não têm suporte estável no `torch`).

```bash
git clone https://github.com/Pedroalano27/tcc-ri-reading-order.git
cd tcc-ri-reading-order
python3.11 -m venv venv
venv\Scripts\activate        # Linux/macOS: source venv/bin/activate
```

### 2. Instalar as dependências

Instale o `torch` **primeiro**, pelo índice oficial do PyTorch — o PyPI não serve
wheels com CUDA para Windows, e um `pip install -r requirements.txt` direto traria
a build CPU-only:

```bash
pip install torch==2.9.1+cu128 --index-url https://download.pytorch.org/whl/cu128
```

```bash
pip install -r requirements.txt
```

Confirme que a GPU foi reconhecida:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

A tag `cu128` acompanha o driver NVIDIA em uso (577.05, que suporta até CUDA 12.9).
Verifique o seu com `nvidia-smi` e ajuste a tag se necessário.

### 3. Gerar o pré-dataset sintético

```bash
python get_predataset.py
```

### 4. Rodar os componentes da pipeline

```bash
python src/data/parser.py
python src/models/lstm.py
python src/eval/llm_client.py
```

---

## 🚧 Estado Atual

O repositório está em transição: os módulos em `src/` foram escritos sob um escopo anterior (extração de entidades) e estão sendo migrados para a tarefa de ordem de leitura. Componentes ainda pendentes:

- [ ] `src/models/layoutlm.py` — instanciação do LayoutLM com encoding das bboxes normalizadas
- [ ] `src/eval/metrics.py` — implementação de BLEU de página e ARD
- [ ] `src/eval/llm_client.py` — migrar de extração de entidades para prompt de ordenação via Ollama
- [ ] `src/data/parser.py` — migrar de `pypdf` (texto corrido) para extração de bboxes com coordenadas
- [ ] `src/models/lstm.py` — adaptar para baseline de ordenação
