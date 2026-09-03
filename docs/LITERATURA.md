# Fichamento Bibliográfico e Referências do TCC

Este documento compila as leituras acadêmicas fundamentais que dão suporte teórico e metodológico ao trabalho sobre **detecção de ordem de leitura em Diários Oficiais**.

> ⚠️ **Antes de citar no texto final do TCC:** conferir os dados bibliográficos completos (páginas, DOI, editora) de cada referência na fonte original ou no DBLP. As entradas abaixo servem para orientar a leitura e a argumentação, não como referências já formatadas.

---

## 🎯 Núcleo Teórico da Tarefa

### 1. LayoutLM: Pre-training of Text and Layout for Document Image Understanding (Xu, Li, Cui, Huang, Wei & Zhou — KDD, 2020)
*   **Relevância para o TCC:** É o modelo central da nossa proposta. O LayoutLM estende a arquitetura BERT incorporando *2-D position embeddings* — as coordenadas das bounding boxes entram diretamente na representação de entrada, junto com os embeddings de token. Isso significa que o modelo **aprende a geometria da página nativamente**, em vez de tratar o documento como texto linearizado.
*   **Pontos-chave:**
    *   Embeddings de posição 2D construídos a partir das coordenadas normalizadas (escala 0–1000) da bounding box de cada token.
    *   Pré-treino sobre documentos escaneados em larga escala, transferível para tarefas de *Document AI* a jusante.
    *   Modelo leve o bastante para inferência local — base do nosso argumento de eficiência.
*   **Conexão direta:** justifica cientificamente por que uma arquitetura consciente de layout deve superar redes recorrentes convencionais (nossa baseline LSTM), que só enxergam a sequência textual.
*   **Verificar também:** LayoutLMv2 e LayoutLMv3 (Huang et al., ACM MM 2022), que adicionam a modalidade visual. Decidir explicitamente no TCC qual versão será usada e justificar a escolha pelo custo computacional.

### 2. LayoutReader: Pre-training of Text and Layout for Reading Order Detection (Wang, Xu, Cui, Shang & Wei — EMNLP, 2021)
*   **Relevância para o TCC:** É o trabalho que ataca **exatamente a nossa tarefa** e define o protocolo experimental que adotamos. Formula a detecção de ordem de leitura como um problema *sequence-to-sequence* sobre as bounding boxes e constrói o dataset **ReadingBank** para treiná-la.
*   **Pontos-chave:**
    *   **Origem das nossas métricas:** avalia com **BLEU** e **ARD (Average Relative Distance)** — a mesma dupla que usaremos, o que ancora nossa avaliação em precedente da literatura.
    *   Demonstra que a ordem emitida por detectores de layout diverge sistematicamente da ordem de leitura humana em layouts complexos.
*   **Conexão direta:** é a nossa principal referência metodológica. Nossa contribuição se distingue por (a) aplicar ao domínio de Diários Oficiais brasileiros e (b) confrontar a abordagem leve com LLMs generativas, comparação que o artigo não faz.

### 3. DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis (Pfitzmann, Auer, Dolfi, Nassar & Staar — KDD, 2022)
*   **Relevância para o TCC:** É a nossa base de dados pública. Reúne páginas de documentos reais — incluindo **leis, editais e relatórios governamentais** — com anotação humana de layout em formato COCO, o que o torna especialmente próximo do domínio dos Diários Oficiais.
*   **Pontos-chave:**
    *   Anotação humana (não sintética), com múltiplos anotadores e medida de concordância.
    *   Diversidade de layouts, incluindo os multicolunas que são a origem do nosso problema.
*   **Uso no projeto:** base de treino e validação em escala, complementada pelo nosso *Golden Dataset* de 20 páginas de diários de Goiás para avaliação no domínio-alvo.

---

## ⚖️ Fundamentação do Trade-off Eficácia × Eficiência

### 4. Pretrained Transformers for Text Ranking: BERT and Beyond (Yates, Nogueira & Lin, 2021)
*   **Relevância para o TCC:** Principal fonte para o eixo de **eficiência** do nosso trade-off. Documenta a transição da correspondência exata de termos (BM25) para a correspondência semântica densa, e — crucialmente para nós — analisa em profundidade o **custo de inferência de Transformers em documentos longos**.
*   **Pontos-chave:**
    *   Complexidade quadrática $O(N^2)$ do mecanismo de atenção como limite prático para textos longos.
    *   Distinção entre *bi-encoders* (baratos, pré-computáveis) e *cross-encoders* (caros, mais eficazes) — o mesmo dilema estrutural que enfrentamos entre LayoutLM e LLM.
    *   Discussão sistemática de eficácia versus custo, que é o enquadramento do nosso TCC.
*   **Conexão direta:** sustenta teoricamente por que uma página de diário com dezenas de blocos de texto é cara para uma LLM processar, e por que isso importa em escala.

### 5. Risk-Sensitive Deep Neural Learning to Rank (Rodrigues, Sousa, Rosa & Gonçalves — SIGIR, 2022)
*   **Relevância para o TCC:** Artigo do nosso orientador, Prof. Thierson. Mostra que modelos neurais profundos, embora superiores **na média**, apresentam alta variância e risco de **falha catastrófica** em casos onde métodos mais simples são robustos.
*   **Conexão com o TCC:** motiva uma análise que vai além da média das métricas. Devemos reportar não só o BLEU/ARD médio, mas a **distribuição e os piores casos** — investigando se a LLM generativa, apesar de eventualmente melhor na média, falha de forma imprevisível em páginas de layout atípico, enquanto o LayoutLM especializado se mantém estável. Este é um ângulo de análise que fortalece o trabalho e dialoga diretamente com a linha de pesquisa do orientador.

---

## 📖 Contexto Histórico e Metodológico

### 6. Semi-supervised Sequence Learning (Dai & Le — Google, 2015)
*   **Relevância para o TCC:** Trabalho seminal que provou a viabilidade de pré-treinar redes recorrentes de forma não supervisionada para depois especializá-las em tarefas subsequentes. Fundamenta metodologicamente o **paradigma pré-treino → fine-tuning** que o LayoutLM herda e leva adiante.
*   **Uso no TCC:** situar historicamente a nossa baseline LSTM e explicar por que ela é um ponto de comparação legítimo, e não um espantalho.

### 7. BLEU: a Method for Automatic Evaluation of Machine Translation (Papineni, Roukos, Ward & Zhu — ACL, 2002)
*   **Relevância para o TCC:** Referência original da métrica BLEU, necessária para fundamentar formalmente nossa avaliação. Importante discutir no texto a **adaptação de contexto**: BLEU foi concebida para tradução automática, e nós a aplicamos sobre o texto reconstruído a partir da ordem predita — justificar essa transposição (seguindo o precedente do LayoutReader) é obrigatório para a defesa.

---

## 📝 Anotações de Direcionamento Científico

*   **ELMo (Peters et al., 2018):** citar como exemplo consolidado de BiLSTMs profundas pré-treinadas que atingiram o estado da arte antes da hegemonia dos Transformers. Serve para mostrar que a baseline LSTM é uma escolha informada.
*   **Complementaridade das métricas:** explicitar no texto por que BLEU **e** ARD são necessárias. BLEU premia o encadeamento local (blocos vizinhos corretos) e pode mascarar um bloco deslocado para muito longe; ARD captura exatamente esse erro global. Uma predição pode ter BLEU alto e ARD ruim — e a discussão desses casos enriquece a análise.
*   **Justificar o recorte do escopo:** deixar claro na introdução que ordem de leitura é um **problema a montante** de RAG e Agentes de IA. O trabalho não avalia a qualidade final da resposta do agente, mas a qualidade da entrada que o alimenta — delimitação importante para a banca.
*   **Ponto de atenção na comparação:** LayoutLM é *treinado* na tarefa; a LLM é avaliada em *zero-shot* ou *few-shot*. Essa assimetria precisa ser declarada explicitamente como limitação metodológica, ou a comparação fica vulnerável na defesa.
