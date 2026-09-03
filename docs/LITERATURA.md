# Fichamento Bibliográfico e Referências do TCC

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
