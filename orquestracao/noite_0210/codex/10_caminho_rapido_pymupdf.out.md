O caminho digital ficou **8,1× mais rápido**, mas ainda precisa de fallback para tabelas sem grade, imagens compostas e PDFs digitalizados.

Nas 44 páginas Golden, mantendo as mesmas palavras e trocando somente os átomos:

| Método | τ de palavras | Regiões fragmentadas |
|---|---:|---:|
| XY-cut ouro pura | 0,853 | 0,0% |
| XY-cut ouro + margens | 0,972 | 0,0% |
| Plano + Docling | 0,946 | 3,6% |
| Plano + PyMuPDF conservador | 0,967 | 2,6% |
| PyMuPDF incluindo `text` | 0,829 | 18,4% |
| Plano sem átomos | 0,917 | 6,5% |

Ao trocar também as palavras por `get_text("words")`, o τ caiu para **0,920**, avaliado nos **98,9%** de palavras pareadas. Portanto, a geometria das palavras também precisa de validação.

O tempo completo em CPU caiu de **4,389 para 0,541 s/página**, ou **0,23 para 1,85 páginas/s**. A execução sem caches reproduziu os resultados; `--conferir` confirmou o relatório.

Arquivos: [script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/caminho_rapido_pymupdf.py) e [relatório completo](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/caminho_rapido_pymupdf.md).