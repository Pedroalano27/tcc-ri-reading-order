## Contexto

Na sua revisão anterior da segmentação v3 (`orquestracao/logs/20260912_220506_T18_codex_resposta.md`)
você achou seis defeitos. O Claude corrigiu os seis, sem outras mudanças de regra:

| Achado | Correção | Onde |
|---|---|---|
| 1. CropBox ≠ MediaBox | `renderizar_pdf` devolve `(PageImage.bbox, PageImage.scale)`; o `Detector` converte com `ponto = pixel / escala + bbox[0:2]`; o cache grava `bbox_imagem` e `escala`, e `carregar_cache` ignora registro sem `escala` | `src/data/layout.py` |
| 2. Projeção "limpa" com palavra sem par | "limpa" exige também zero palavras novas sem par e nenhuma palavra antiga perdida, a não ser separador (sem letra nem dígito). A inversão interna de ordem dentro de um bloco foi mantida de propósito e documentada: a garantia é sobre a ordem dos blocos | `src/anotacao/projetar_ordem.py:projetar_pagina` |
| 3. Junção de letras em texto corrido | `RE_LETRAS` sem vírgula nem ponto e vírgula; a sequência só se junta com pelo menos 75% de pedaços de UMA letra | `src/data/extrator.py:_juntar_letras_espacadas` |
| 4. Casamento dependente da ordem de visita | `casar_palavras`: cada palavra antiga escolhe a palavra nova, entre todas as candidatas, por (contém o centro sem folga, mesmo texto, distância, índice) | `src/anotacao/projetar_ordem.py` |
| 5. Corredores incompatíveis | a descida continua do trecho branco que sobrou na subida | `src/data/extrator.py:_cortes_locais` |
| 6. Cauda truncada no cache | `GravadorCache` encerra com quebra de linha uma última linha sem `\n` antes de acrescentar | `src/data/layout.py` |

Efeitos já medidos: numa página do Golden v1 (SP) a imagem começa em y = 50 pt, ou seja, as
tabelas dela estavam deslocadas; o cache antigo foi apagado. A projeção do Golden v1 continua
com 20 páginas limpas, 5 com conflito, 4 sem anotação e 1 rejeitada, agora sem nenhuma palavra
sem par; o lote `golden_v2` foi regerado (29 páginas, 814 blocos; ninguém tinha anotado).

## Tarefa: REVISÃO das correções, sem alterar nenhum arquivo

1. Reexecute as suas reproduções dos seis achados contra o código atual e diga, para cada um,
   se a correção resolve e se introduz outro defeito.
2. Procure regressões nas próprias correções. Por exemplo: a regra dos 75% deixa de juntar algum
   título espaçado real? O corredor único deixa de cortar calha real quando a subida estreita o
   trecho branco? A conversão de coordenadas está certa em página girada com CropBox deslocada?
   O critério novo de "limpa" gera conflito falso por causa da folga de 0,6 pt?
3. Não repita a análise de desempenho.

As mesmas restrições da revisão anterior: nada de detector, `preparar_lote.py`,
`projetar_ordem.py` pela linha de comando ou `reextrair.py`, porque gravam em `data/` e usam a
GPU (reservada: o Claude está rodando o detector sobre as coleções). Use as páginas que já estão
em `data/processed/layout` e trechos de Python que só leem.

## Resposta final

Em FEITO: para cada achado, "resolvido", "resolvido com ressalva" ou "não resolvido", com a
reprodução. Depois, os defeitos novos, se houver, no mesmo formato da revisão anterior. Não
invente achados para preencher a lista.
