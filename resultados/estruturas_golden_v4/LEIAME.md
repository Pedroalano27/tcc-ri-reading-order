# Variante com estruturas da página

45 tarefas do Golden v4, exportadas em `linhas.jsonl` e `colunas.jsonl`. Não substitui as versões anteriores. Cabeçalhos/rodapés: detector automático (score ≥ 0,6) ou margem extrema isolada. Quadros externos: moldura retangular ou duas linhas horizontais largas, com texto institucional sobre imprensa e publicações. Não usa classes humanas como entrada. O exemplo do RJ fica inteiro fora das três colunas principais.

`validacao.json`: 92 unidades de cabeçalho, 42 de rodapé e um quadro externo; contagem de unidades, não de páginas nem acertos. Todas as palavras preservadas exatamente uma vez. Isso não mede precisão/recall. Quadros rasterizados, sem linhas ou sem termos institucionais não estão cobertos; o cabeçalho pode continuar em várias unidades. Imagens/logotipos internos conservam sua detecção visual e podem estar dentro do envelope do quadro. Não houve nova avaliação de ordenação: os números anteriores não valem para esta variante.

Gerador: `venv\Scripts\python.exe src\data\comparador_golden_v4.py`. Comparador: `resultados/comparador_golden_v4/index.html`, opções “margens/quadros”.
