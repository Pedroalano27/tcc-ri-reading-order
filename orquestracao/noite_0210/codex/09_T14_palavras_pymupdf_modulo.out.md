O módulo opcional está pronto, mas **não pode virar padrão com paridade garantida**: apenas 61/104 páginas mantiveram todos os blocos. Não regenere a silver com esse caminho.

| Amostra | Blocos PP / Mu | Idênticos¹ | Páginas iguais | PP / Mu, s/página | Ganho |
|---|---:|---:|---:|---:|---:|
| Bancada 44 | 1451 / 1445 | 90,90% | 28/44 | 2,412 / 0,079 | 30,64× |
| Extras 60 | 1761 / 1750 | 95,63% | 33/60 | 2,713 / 0,077 | 35,31× |
| **Total** | **3212 / 3195** | **93,49%** | **61/104** | **2,585 / 0,078** | **33,31×** |

¹ Texto exato e IoU ≥ 0,95, sobre os blocos do pdfplumber. CPU, com layout em cache. O τ stream foi 1,000 nos blocos casados; isso não garante equivalência do conjunto completo.

**126 testes passaram, incluindo 21 novos.** Medição final executada do zero e conferida por resegmentação dos caches. O extrator original foi preservado.

- [Módulo opcional](C:/Users/pedro/dev/tcc-ri-reading-order/src/data/palavras_pymupdf.py)
- [Testes](C:/Users/pedro/dev/tcc-ri-reading-order/tests/test_palavras_pymupdf.py)
- [Script de medição](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/extrator_pymupdf_paridade.py)
- [Relatório completo, causas e diff proposto](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/extrator_pymupdf_paridade.md)

Caches retomáveis em `resultados/extrator_pymupdf_cache/`.