# Datasets sem caixas finas

Versoes experimentais; originais preservados. Apenas tabela/imagem sao atomos. Texto representado por linhas ou faixas de coluna, nunca por paragrafo rotulado.

614 paginas unicas; 44 paginas na bancada humana. Split por fonte herdado, sem treino novo do modelo. Referencia derivada da ordem humana de regioes; nao referencia independente de palavras.

| LayoutReader pronto em CPU | tau palavras | Sucessor palavras | ms/pagina |
|---|---:|---:|---:|
| linhas | 0.8984 | 0.9620 | 1283.2 |
| colunas | 0.8503 | 0.9604 | 144.5 |

Resultados exploratorios sobre 44 paginas usadas no desenvolvimento. Versao colunas impoe ordem geometrica interna; modelo decide entre faixas. Nao demonstra generalizacao nem efeito de treinar LayoutLM nesta representacao.
