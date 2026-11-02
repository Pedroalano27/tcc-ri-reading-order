**FEITO:** bancada implementada com retomada, avaliação externa e execução em CPU.

**ARQUIVOS:** [script](C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/bancada_ordenadores.py), [relatório](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordenadores_sem_caixas.md) e [JSON](C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordenadores_sem_caixas.json).

**EVIDÊNCIA:** a regra sobre `ks` exportados fez **16,86 quebras/página**, contra **6,05** da âncora. A diferença está na ordem interna de **10 páginas**; usar a expansão canônica reproduz exatamente as 44 sequências históricas. AST, autotestes e conferência passaram.

**PENDÊNCIA:** compatibilizar `ks` na tarefa 01. Parei conforme a regra da âncora, sem publicar tabelas comparativas nem carregar o LayoutReader.