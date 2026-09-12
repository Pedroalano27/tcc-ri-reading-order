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

A **LSTM** convencional entra como *baseline* de rede recorrente, e as **heurísticas geométricas** (ingênua e XY-cut) como *baselines* sem aprendizado: servem para dimensionar o ganho que a consciência de layout e o aprendizado efetivamente trazem.

A hipótese sob teste é que **um modelo leve e especializado em layout alcança eficácia competitiva com LLMs generativas a uma fração do custo computacional** — o que, se confirmado, tem implicação prática direta no processamento de grandes volumes de diários.

Como o trabalho é da área de Recuperação de Informação, a ordem de leitura também é avaliada **pelo efeito na recuperação**: um piloto em Japeri (RJ) mede se a ordenação muda o que a busca encontra e o texto que chega a um RAG ([resultados, seção 6](docs/RESULTADOS_PRELIMINARES.md)).

---

## 📏 Métricas de Avaliação

| Métrica | O que mede |
|---|---|
| **τ de Kendall** (principal) | Concordância entre a ordem predita e a de referência: fração de pares de blocos na ordem certa, de −1 (invertida) a 1 (idêntica). |
| **Sucessor correto** | Fração dos blocos seguidos pelo bloco certo. Mede a continuidade local do texto — o que chega a um leitor, a um trecho de busca ou a um RAG. |
| **ARD** (*Average Relative Distance*) | Distância média entre a posição predita e a posição correta de cada caixa. Captura o erro de ordenação *global*, penalizando blocos deslocados para longe. |
| **BLEU de página** | Sobreposição de n-gramas entre o texto reconstruído na ordem predita e o texto na ordem de referência. Em granularidade de bloco é pouco discriminativo (uma página invertida ainda marca 82,7). |
| **Tempo de inferência** | Latência por página, medida nas mesmas condições de hardware para todas as abordagens. |

---

## 📊 Estratégia de Dados

1. **Acervo de Diários Oficiais** (`data/raw/`, não versionado) — 4.644 PDFs de 23 UFs e 8 municípios cedidos pelo orientador, cerca de 310 mil páginas ([docs/ACERVO.md](docs/ACERVO.md)). Os blocos com coordenadas são extraídos da camada de texto dos PDFs, e a ordem do fluxo do PDF serve de rótulo *silver* nos veículos em que ela é confiável.
2. **Golden Dataset** (`data/golden/`) — ordem de leitura anotada à mão numa ferramenta própria (`src/anotacao/`). O lote `golden_v1` tem 30 páginas de veículos de teste e de veículos em que o fluxo do PDF não é confiável; um lote de **Goiás**, fora do acervo, mede generalização fora do domínio ([docs/GUIA_ANOTACAO.md](docs/GUIA_ANOTACAO.md)).
3. **Pré-dataset sintético** (`data/predataset/`) — páginas simuladas geradas por [`get_predataset.py`](get_predataset.py), com layout multicolunas e ordem de leitura conhecida por construção, para validar a pipeline ponta a ponta.
4. **DocLayNet** — dataset público de análise de layout. Anota categorias de layout, não ordem de leitura; o papel dele no trabalho está em discussão.

---

## 📂 Estrutura do Repositório

```text
├── data/
│   ├── raw/                # PDFs brutos dos Diários Oficiais (não versionado)
│   ├── processed/          # Blocos extraídos e divisão treino/validação/teste (regenerável)
│   ├── golden/             # Lotes de anotação manual: tarefas e anotações (versionado)
│   └── predataset/         # Pré-dataset sintético de ordem de leitura (JSON)
├── models/                 # Pesos e checkpoints treinados (não versionado)
├── notebooks/              # Notebook do Kaggle (gerado por src/kaggle/montar_pacote.py)
├── resultados/             # Predições, comparações e logs dos experimentos
├── src/
│   ├── data/               # Extração dos ZIPs e dos blocos com bounding boxes dos PDFs
│   ├── models/             # LayoutLM e BiLSTM
│   ├── eval/               # Protocolo, baselines, LLM, métricas, comparação, figuras, avaliação humana
│   ├── anotacao/           # Ferramenta de anotação do Golden Dataset
│   ├── kaggle/             # Pacote e importação das LLMs rodadas no Kaggle
│   └── ri/                 # Avaliação extrínseca: efeito da ordem na recuperação
├── docs/                   # Metodologia, resultados, diário de bordo, guias e figuras
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

### 4. Rodar o pipeline experimental

Com os diários extraídos em `data/raw/` (ver [docs/ACERVO.md](docs/ACERVO.md)):

```bash
python src/data/extrator.py --pdfs-por-uf 14 --paginas-por-pdf 4 --workers 9
python src/eval/caracterizar.py
python src/eval/baselines.py
python src/models/layoutlm_ordem.py treinar
python src/models/layoutlm_ordem.py avaliar
python src/models/layoutlm_sucessor.py treinar
python src/models/layoutlm_sucessor.py avaliar
python src/models/lstm_ordem.py --variante geo_texto
python src/eval/llm_ordem.py --modelo llava:7b --paginas 20 --max-blocos 25
python src/eval/comparar.py
python src/eval/figuras.py
```

Experimentos e ferramentas da segunda etapa. O piloto e a curva exigem as coletas
extras descritas em [docs/METODOLOGIA.md](docs/METODOLOGIA.md), seção 3.2:

```bash
python src/ri/piloto_japeri.py                      # efeito da ordem na busca (Japeri)
python src/rodar_curva_aprendizado.py               # LayoutLM e BiLSTM com mais páginas de treino
python src/anotacao/servidor.py                     # ferramenta de anotação do Golden Dataset
python src/eval/avaliar_golden.py --lote golden_v1  # métodos contra a anotação humana
python src/kaggle/montar_pacote.py                  # treino e LLMs nas T4 do Kaggle (docs/KAGGLE.md)
```

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [docs/ENTENDA_O_PROJETO.md](docs/ENTENDA_O_PROJETO.md) | **Comece por aqui**: guia explicativo do projeto inteiro, com exemplos e glossário |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Estado atual do projeto, onde está cada informação e próximos passos |
| [AGENTS.md](AGENTS.md) · [COMUNICACAO_AGENTES.md](COMUNICACAO_AGENTES.md) | Regras para os agentes de IA que trabalham no repositório e quadro compartilhado entre eles |
| [docs/RESULTADOS_PRELIMINARES.md](docs/RESULTADOS_PRELIMINARES.md) | Números e figuras dos experimentos |
| [docs/METODOLOGIA.md](docs/METODOLOGIA.md) | Desenho experimental completo |
| [docs/DIARIO_DE_BORDO.md](docs/DIARIO_DE_BORDO.md) | Tudo o que foi feito, com decisões e problemas |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Próximos passos e perguntas para o orientador |
| [docs/GUIA_ANOTACAO.md](docs/GUIA_ANOTACAO.md) | Como anotar o Golden Dataset, com as regras de leitura |
| [docs/KAGGLE.md](docs/KAGGLE.md) | Como rodar as LLMs maiores na GPU gratuita do Kaggle |
| [docs/ACERVO.md](docs/ACERVO.md) | Diagnóstico dos 4.644 diários do acervo |
| [docs/LITERATURA.md](docs/LITERATURA.md) | Fichamento bibliográfico |

---

## 🚧 Estado Atual

- [x] Extração de blocos com bounding boxes a partir dos PDFs digitais (`src/data/extrator.py`)
- [x] Métricas: τ de Kendall, sucessor correto, ARD, BLEU de página (`src/eval/metrics.py`)
- [x] Protocolo experimental com divisão por veículo (`src/eval/protocolo.py`)
- [x] Baselines: ordem do detector, ingênua, XY-cut (`src/eval/baselines.py`)
- [x] BiLSTM em três variantes (`src/models/lstm_ordem.py`)
- [x] LayoutLM como learning-to-rank pontual, com ablação sem layout (`src/models/layoutlm_ordem.py`)
- [x] LayoutLM prevendo o **sucessor** de cada bloco, com viés geométrico par a par e
      decodificação em cadeias (`src/models/layoutlm_sucessor.py`)
- [x] LLM zero-shot e few-shot via Ollama (`src/eval/llm_ordem.py`)
- [x] Ferramenta de anotação e lote `golden_v1` com 30 páginas (`src/anotacao/`)
- [x] Pacote e dois notebooks do Kaggle: treino na T4 e LLMs de 7B a 32B (`src/kaggle/`)
- [x] Piloto de avaliação extrínseca de RI em Japeri (`src/ri/piloto_japeri.py`)
- [x] Curva de aprendizado com até 3.235 páginas de treino (`src/rodar_curva_aprendizado.py`)
- [ ] Anotação do Golden Dataset (`golden_v1` e Goiás)
- [ ] Rodar os dois notebooks do Kaggle: curva das duas formulações, ablações e as LLMs
- [ ] APIs comerciais (Azure, Google); LayoutXLM e LayoutReader

Os módulos `src/data/parser.py`, `src/models/lstm.py` e `src/eval/llm_client.py` são do escopo anterior (extração de entidades) e foram substituídos pelos listados acima.
