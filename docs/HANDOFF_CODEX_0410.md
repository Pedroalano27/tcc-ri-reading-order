# Handoff para o Claude — Codex, 04/10/2026

## O que o Pedro quer

Reduzir dependência de caixas de texto erradas/não uniformes. A frente sem caixas finas não é apenas melhorar XY-cut: experimentar datasets sem segmentação em parágrafos, preservando tabelas/imagens e identificando multicolunas, e testar um ordenador. Depois pediu comparação visual no Golden v4 e separação de cabeçalho, rodapé e quadros institucionais como o da Imprensa Oficial do RJ.

Mudanças experimentais pedidas diretamente e registradas como DECISÃO no quadro. Não substituímos o dataset oficial. Não houve novo treino, commit, push, publicação externa ou escrita em PDFs/anotações humanas. Este chat não retomou nem verificou filas/treinos noturnos: não inferir execução pelos pedidos antigos de /loop.

## Arquivos criados

- `src/data/dataset_sem_caixas_finas.py`: exportador de linhas e faixas de coluna, com tabelas/imagens atômicas; entrada embaralhada; avaliação opcional LayoutReader.
- `resultados/datasets_sem_caixas/`: versões por split, referências separadas, manifesto com hashes, validação e relatório.
- `src/data/estruturas_pagina.py`: isola margens e quadros antes de formar colunas, sem consultar classes humanas.
- `resultados/estruturas_golden_v4/`: linhas/colunas com estruturas para 45 tarefas; validação, LEIAME e exemplo RJ.
- `src/data/comparador_golden_v4.py` e `.html`: gerador e template do comparador.
- `resultados/comparador_golden_v4/index.html`: comparador autossuficiente, imagens embutidas; pode ser enviado ao professor e aberto no navegador sem servidor.
- `resultados/comparador_golden_v4/exemplo_1.png` a `exemplo_3.png`: v3 / Golden v4 / colunas iniciais, sem a variante posterior de margens.
- `resultados/estruturas_golden_v4/exemplo_rj.png`: quadro institucional inteiro separado das três colunas.

`docs/HANDOFF.md` recebeu um adendo no topo; o corpo continua sendo o estado histórico de setembro. Decisões e registros completos estão em `COMUNICACAO_AGENTES.md`. Scripts reservados em `orquestracao/analises/` foram importados, não editados.

## Resultados verificados

Fontes: páginas já extraídas em `data/diamond/*/tarefas.jsonl`, deduplicadas por page_id. Não foi extraído o acervo inteiro. Na bancada humana, a extração canônica associada ao Golden v4 prevalece para manter índices de palavras compatíveis.

`resultados/datasets_sem_caixas/manifesto.json`: **614 páginas**; 196 treino, 13 validação, 3 teste e 402 sem split. Split por veículo herdado de `data/processed/splits.json`. Exportar treino não cria supervisão humana. A bancada humana sobrepõe os demais arquivos: não concatenar tudo.

`validacao_exportacao.json`: **349 páginas** com evidência de multicolunas; **59.081 unidades** por linhas e **5.495** por colunas. Todas as palavras exatamente uma vez. Caso sintético de 24 linhas em duas colunas passou. Calhas exigem suporte de pelo menos quatro linhas por lado; páginas curtas podem não ser separadas.

`avaliacao/layoutreader.jsonl` e `RELATORIO.md`: **88 avaliações em 44 páginas concluídas**, LayoutReader local pré-treinado em CPU, sem retreino.

| Representação | τ palavras | Sucessor palavras | Tempo médio ms/página |
|---|---:|---:|---:|
| Linhas | 0,8984 | 0,9620 | 1283,2 |
| Colunas | 0,8503 | 0,9604 | 144,5 |

**Colunas pioraram τ nesse teste.** Não afirmar ganho comprovado. Tempo desta execução não é benchmark controlado. Referência de palavras deriva da ordem humana de regiões com ordem geométrica interna; não é anotação humana independente de palavras. Páginas usadas no desenvolvimento, não teste independente. Colunas impõem ordem interna geométrica. Acima de 510 unidades, o adaptador LayoutReader existente agrupa geometricamente: não mede ordenação puramente neural de todas as linhas.

## Margens e quadros externos

Variante adicional aplicada às **45 tarefas** Golden v4; avaliação anterior usa **44 concluídas**. Segundo `resultados/estruturas_golden_v4/validacao.json`: **92 unidades de cabeçalho, 42 de rodapé e um quadro externo**. São unidades, não páginas nem acertos. Integridade de palavras conferida em ambas as representações.

Margens: detector automático `page_header`/`page_footer`, score mínimo 0,6, ou bordas extremas de 4,5% com intervalo de uma linha. Quadros: retângulo ou par de linhas horizontais largas do PDF, mais texto institucional sobre imprensa/publicações. Não usa classes humanas como entrada. PDF indexado por `pagina` **zero-based**, igual ao extrator.

Página verificada visualmente: `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`. Quadro inteiro fora das três colunas principais.

Limitações: cabeçalhos ainda podem estar fragmentados; quadros sem moldura ou rasterizados não são cobertos. Logos/imagens podem conservar caixa dentro do envelope do quadro; atribuição de palavras é exclusiva. Palavras dos quadros/margens seguem a sequência original da extração; ordem interna ainda precisa ser auditada. **Essa variante não foi avaliada com LayoutReader; os números anteriores não se aplicam a ela.**

## Tecnologias e comparador

Detector pré-existente nas 45 páginas: `docling-project/docling-layout-heron`, não detector treinado nesta sessão. Extração original por pdfplumber, análise vetorial adicional por PyMuPDF, imagens com Pillow, interface HTML/CSS/JavaScript e SVG. LayoutReader é ordenador separado, não gerador das caixas.

Seis opções: v3 armazenado no Diamond; caixas existentes do Golden v4 (incluindo correções humanas); linhas; colunas; linhas com estruturas; colunas com estruturas. Comparação lado a lado, zoom, rolagem sincronizada, IDs, ocultação de caixas/texto e inspeção ao clicar. Padrão à direita: colunas com estruturas. Azul texto, laranja tabela, rosa imagem, verde margens, roxo quadro. Foram mantidas saídas reais, inclusive faixas estreitas indevidas.

Endereço usado: `http://127.0.0.1:8784/resultados/comparador_golden_v4/index.html`. Servidor HTTP Python iniciado nesta sessão na porta 8784; confirmar se ainda está ativo. O HTML dispensa servidor para compartilhar. Não foi enviado ao professor nem hospedado externamente. AST Python e sintaxe JavaScript (`node --check`) passaram; exemplos PNG inspecionados. Não houve teste funcional completo por automação de navegador.

## Reprodução

```powershell
venv\Scripts\python.exe src\data\dataset_sem_caixas_finas.py --avaliar
venv\Scripts\python.exe src\data\comparador_golden_v4.py
venv\Scripts\python.exe -m http.server 8784 --bind 127.0.0.1
```

Primeiro comando regenera versões experimentais e avaliação, não Golden. Segundo gera comparador e versões com estruturas. Alguns documentos, validações e PNG RJ foram produzidos por comandos pontuais; não são todos regenerados automaticamente. Dependências dos scripts de análise e modelo LayoutReader local permanecem necessárias.

## Próximos passos

1. Revisar as seis variantes com Pedro/professor; medir erros de calhas e margens, distinguindo Golden humano de saída automática.
2. Avaliar variante de estruturas na mesma referência de palavras, especialmente ordem interna do quadro; registrar resultados separados.
3. Corrigir faixas estreitas e fragmentação de cabeçalhos com validação fora das páginas usadas para calibrar.
4. Para estudar treinamento, criar supervisão compatível com essas unidades e teste independente. Não adaptar IDs de blocos de outra segmentação nem assumir rótulos nos 196 exemplos exportados.
5. Não regenerar lotes com anotações humanas nem modificar `data/raw/`. Revisar protocolo antes de expandir cobertura.

## GitHub pendente e estado compartilhado

Pedro perguntou sobre `https://github.com/CEIA-Datapolicy`. Consulta pública: organização sem repositórios públicos. Ele confirmou acesso aos privados quando autenticado. Falta receber link de repositório específico; não houve acesso autenticado, clone ou análise. Não pedir senha/token na conversa.

A árvore Git já apresentava numerosas alterações de outros agentes, incluindo anotações humanas no status. Este chat não as editou nem reverteu. Não atribuir essas diferenças a esta sessão. Nenhum treino novo, automação ou orquestração recorrente iniciado aqui. Na retomada noturna, conferir status real e reservas atuais.
