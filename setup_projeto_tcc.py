import os
import subprocess
import sys

# Definindo a estrutura de pastas
FOLDERS = [
    "data/raw",
    "data/processed",
    "models",
    "notebooks",
    "src/data",
    "src/models",
    "src/eval",
    "docs"
]

# Conteúdo do README.md
README_CONTENT = """# Análise Comparativa de Eficácia e Eficiência Computacional entre LSTMs Pré-treinadas e Large Language Models (LLMs) para Extração de Informações de Alto Valor em Diários Oficiais

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
source venv/bin/activate  # No Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Rodar a pipeline de testes de exemplo:
```bash
python src/data/parser.py
python src/models/lstm.py
python src/eval/llm_client.py
```
"""

# Conteúdo do LITERATURA.md
LITERATURA_CONTENT = """# Fichamento Bibliográfico e Referências do TCC

Este documento compila as leituras acadêmicas fundamentais que dão suporte teórico e metodológico ao trabalho.

---

## 📚 Livros e Artigos Base

### 1. Pretrained Transformers for Text Ranking: BERT and Beyond (Yates, Nogueira, & Lin, 2021)
*   **Relevância para o TCC:** Este livro apresenta detalhadamente a transição dos sistemas clássicos de correspondência exata de termos (como BM25) para a correspondência semântica densa gerada por modelos de linguagem pré-treinados (Transformers). É a nossa principal fonte para justificar o problema do custo de inferência computacional em documentos longos e o dilema "Eficácia vs. Eficiência".
*   **Pontos-chave:**
    *   Problema da incompatibilidade de vocabulário (*vocabulary mismatch problem*).
    *   Complexidade quadrática da atenção em Transformers limitando o processamento de textos longos.
    *   Discussão sobre técnicas de representação densa (*Bi-encoders*) e reordenamento (*Cross-encoders*).

### 2. Risk-Sensitive Deep Neural Learning to Rank (Rodrigues, Sousa, Rosa, & Gonçalves - SIGIR 2022)
*   **Relevância para o TCC:** Artigo do nosso orientador, Prof. Thierson. Ele aborda o fato de que modelos de aprendizado profundo para ranqueamento (como BERT), embora excelentes na média, trazem alta instabilidade e risco de "falha catastrófica" em consultas simples onde o BM25 é eficaz.
*   **Conexão com o TCC:** Avaliaremos se a nossa LSTM pré-treinada e especializada apresenta um comportamento mais estável e sensível ao risco em relação à flutuação das respostas de LLMs comerciais.

### 3. Semi-supervised Sequence Learning (Dai & Le - Google, 2015)
*   **Relevância para o TCC:** Este trabalho seminal provou que é possível pré-treinar redes recorrentes (LSTMs) em dados textuais não rotulados de forma não supervisionada (prevendo a próxima palavra) para estabilizar e melhorar massivamente seu desempenho em tarefas de classificação subsequentes. É a base científica do nosso plano de pré-treino da LSTM nos diários antigos.

---

## 📝 Anotações de Direcionamento Científico
*   **ELMo (Peters et al., 2018):** Lembrar de citar o ELMo como exemplo consolidado de BiLSTMs profundas pré-treinadas que atingiram o estado da arte antes da hegemonia exclusiva dos Transformers, mostrando a viabilidade prática da nossa proposta.
"""

# Dependências básicas no requirements.txt
REQUIREMENTS_CONTENT = """torch>=2.0.0
transformers>=4.30.0
pypdf>=3.9.0
pdfplumber>=0.9.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.2.0
tqdm>=4.65.0
requests>=2.31.0
jupyter>=1.0.0
matplotlib>=3.7.0
"""

# Código Mock de extração de PDF (src/data/parser.py)
PARSER_CODE = """import os
import pypdf

def extract_text_from_pdf(pdf_path):
    \"\"\"
    Função de exemplo que extrai o texto bruto de um PDF usando a biblioteca pypdf.
    \"\"\"
    print(f"[*] Iniciando extração de texto do arquivo: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[!] Erro: Arquivo {pdf_path} não encontrado. Retornando texto fictício (mock).")
        return "AVISO DE LICITAÇÃO. OBJETO: Aquisição de equipamentos de informática para a UFG. DATA: 15/09/2026. VALOR: R$ 150.000,00."
    
    text = ""
    try:
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text += page.extract_text() or ""
        print(f"[+] Extração concluída com sucesso! Total de {len(reader.pages)} páginas lidas.")
    except Exception as e:
        print(f"[!] Erro ao abrir PDF: {e}")
    
    return text

if __name__ == "__main__":
    # Testando a lógica de parsing
    sample_text = extract_text_from_pdf("data/raw/diario_exemplo.pdf")
    print(f"\\n Trecho do texto extraído (primeiros 150 caracteres):\\n{sample_text[:150]}...")
"""

# Código Mock da Arquitetura LSTM (src/models/lstm.py)
LSTM_CODE = """import torch
import torch.nn as nn

class DiarioLSTM(nn.Module):
    \"\"\"
    Arquitetura de rede neural recorrente (LSTM) projetada para tarefas de processamento de texto.
    Pode ser pré-treinada para prever a próxima palavra (Modelagem de Linguagem)
    e depois adaptada (fine-tuned) para classificação ou extração de entidades.
    \"\"\"
    def __init__(self, vocab_size, embedding_dim, hidden_dim, output_dim, num_layers=2):
        super(DiarioLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            embedding_dim, 
            hidden_dim, 
            num_layers=num_layers, 
            batch_first=True, 
            bidirectional=True  # Bi-LSTM para capturar contexto esquerdo e direito
        )
        # Como é bidirecional, a dimensão de entrada da linear é hidden_dim * 2
        self.fc = nn.Linear(hidden_dim * 2, output_dim)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)
        predictions = self.fc(lstm_out)
        return predictions

if __name__ == "__main__":
    print("[*] Instanciando modelo LSTM de teste...")
    # Parâmetros fictícios de teste
    vocab_size = 1000  # Tamanho do vocabulário
    embedding_dim = 128
    hidden_dim = 256
    output_dim = 5     # Ex: 5 tipos de entidades jurídicas (Rótulos)
    
    model = DiarioLSTM(vocab_size, embedding_dim, hidden_dim, output_dim)
    print(model)
    
    # Criando entrada fictícia (batch_size=2, sequence_length=10)
    test_input = torch.randint(0, vocab_size, (2, 10))
    output = model(test_input)
    print(f"\\n[+] Sucesso! Formato de saída do modelo (Batch, Seq_Len, Classes): {output.shape}")
"""

# Código Mock do Cliente de LLM para comparação (src/eval/llm_client.py)
LLM_CLIENT_CODE = """import json

def call_llm_extractor(text_snippet):
    \"\"\"
    Mock que simula a chamada de uma API de LLM (como OpenAI, Anthropic, ou Llama local via Ollama).
    Recebe um trecho de texto do diário e retorna um JSON estruturado com a licitação extraída.
    \"\"\"
    print("[*] Enviando requisição para a LLM...")
    
    # Simulação de prompt interno e geração do retorno
    mock_response_json = {
        "tipo_documento": "Aviso de Licitação",
        "objeto": "Aquisição de equipamentos de informática para a UFG",
        "orgao_demandante": "Universidade Federal de Goiás",
        "data_abertura": "15/09/2026",
        "valor_estimado": 150000.00
    }
    
    return mock_response_json

if __name__ == "__main__":
    text = "AVISO DE LICITAÇÃO. OBJETO: Aquisição de equipamentos de informática para a UFG. DATA: 15/09/2026. VALOR: R$ 150.000,00."
    extracted_data = call_llm_extractor(text)
    print("\\n[+] Dados extraídos estruturados pela LLM (Gabarito de Teste):")
    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))
"""

def main():
    print("=== INICIANDO CRIAÇÃO DO AMBIENTE LOCAL DO SEU TCC ===")
    
    # 1. Criando as pastas
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
        print(f"[+] Pasta criada: {folder}")
        
    # 2. Escrevendo os arquivos de documentação
    files_to_write = {
        "README.md": README_CONTENT,
        "docs/LITERATURA.md": LITERATURA_CONTENT,
        "requirements.txt": REQUIREMENTS_CONTENT,
        "src/data/parser.py": PARSER_CODE,
        "src/models/lstm.py": LSTM_CODE,
        "src/eval/llm_client.py": LLM_CLIENT_CODE
    }
    
    for filepath, content in files_to_write.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Arquivo criado: {filepath}")
        
    # 3. Inicializando o repositório Git localmente se o usuário tiver o git instalado
    try:
        subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)
        # Criando o .gitignore básico para não subir PDFs nem pesos de modelos
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env

# Modelos e Dados Grandes
data/raw/*
!data/raw/.gitkeep
models/*
!models/.gitkeep
*.pt
*.pth
*.bin
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        
        # Criando arquivos vazios de marcação para pastas grandes
        with open("data/raw/.gitkeep", "w") as f: pass
        with open("models/.gitkeep", "w") as f: pass
        
        print("[+] Repositório Git inicializado localmente com arquivo .gitignore.")
    except Exception as e:
        print("[!] Aviso: Git não encontrado ou não inicializado. Sem problemas, você pode rodar 'git init' manualmente.")

    print("\n=== SUCESSO! SEU PROJETO FOI ESTRUTURADO COM SUCESSO ===")
    print("Instruções:")
    print("1. Abra a pasta do projeto na sua IDE (como VS Code).")
    print("2. Crie seu ambiente virtual e instale as dependências usando 'requirements.txt'.")
    print("3. Rode os scripts da pasta 'src/' para testar a sua base inicial de código.")

if __name__ == "__main__":
    main()
