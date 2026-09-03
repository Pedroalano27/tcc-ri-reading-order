# Análise Comparativa de Eficácia e Eficiência Computacional entre LSTMs Pré-treinadas e Large Language Models (LLMs) para Extração de Informações de Alto Valor em Diários Oficiais

Este repositório contém o código, a pipeline de dados e os experimentos referentes ao Trabalho de Conclusão de Curso (TCC) desenvolvido no Instituto de Informática da Universidade Federal de Goiás (INF-UFG).

**Orientador:** Prof. Dr. Thierson Couto Rosa

---

## 🎯 Objetivo do Projeto
O objetivo deste trabalho é avaliar o trade-off entre **eficácia** (precisão de extração) e **eficiência computacional** (tempo de processamento e custo de infraestrutura) ao processar grandes volumes de documentos longos (PDFs de Diários Oficiais publicados sob demanda). 

Comparamos duas abordagens distintas para a extração de informações de alto valor (como licitações e contratos):
1. **Redes Recorrentes Lineares:** Uma rede **LSTM (Long Short-Term Memory)** pré-treinada localmente em dados históricos de diários oficiais para especialização de domínio.
2. **Transformers de Larga Escala:** Modelos de Linguagem de Larga Escala (**LLMs**), que possuem excelente capacidade de representação contextual, mas demandam altíssimo custo computacional quadrático $O(N^2)$ e custo de API.

---

## 📂 Estrutura do Repositório

```text
├── data/
│   ├── raw/                # PDFs brutos dos Diários Oficiais (dados não versionados no Git)
│   └── processed/          # Textos limpos extraídos e datasets de treino/teste (JSON/CSV)
├── models/                 # Pesos e checkpoints dos modelos treinados (salvos localmente)
├── notebooks/              # Jupyter Notebooks para análise exploratória e geração de gráficos
├── src/
│   ├── data/               # Scripts de coleta, parsing e limpeza dos PDFs
│   ├── models/             # Arquitetura da LSTM e lógicas de pré-treino
│   └── eval/               # Scripts de integração com LLMs e cálculo de métricas (F1, tempo, custos)
├── docs/                   # Artigos de referência, notas de reuniões e relatórios
├── requirements.txt        # Dependências do projeto
└── README.md               # Este arquivo de documentação
```

---

## ⚙️ Requisitos de Instalação e Execução

### 1. Clonar e configurar o ambiente:
```bash
git clone <seu-repositorio-url>
cd <seu-repositorio>
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Rodar a pipeline de testes de exemplo:
```bash
python src/data/parser.py
python src/models/lstm.py
python src/eval/llm_client.py
```
