## Contexto

Segunda revisão sua (`orquestracao/logs/20260912_222753_T18_codex_resposta.md`): quatro achados
resolvidos com ressalva e dois restantes. O Claude aplicou mais cinco mudanças pequenas:

| Seu achado | Mudança | Onde |
|---|---|---|
| 1. CropBox assimétrica em página girada | a página girada com CropBox diferente da MediaBox não é renderizada: vira falha registrada no cache (`regioes` = None) e sai sem tabelas. Medido: das 4.112 páginas do acervo, **nenhuma** é girada e nenhuma tem CropBox diferente da MediaBox (o `y = 50` do SP é MediaBox com origem deslocada, coberto pela correção anterior) | `src/data/layout.py:renderizar_pdf`, `GravadorCache.falha`, `tabelas(None)` |
| 2. Regressão das calhas | `_cortes_locais` tenta as duas ordens (subir e depois descer; descer e depois subir), sempre com um corredor só em cada tentativa | `src/data/extrator.py` |
| 3. Empate texto exato × substring | a chave de casamento separa igualdade (`tn != t`) de substring (`t not in tn`) | `src/anotacao/projetar_ordem.py:casar_palavras` |
| 4. UTF-8 incompleto | `carregar_cache` abre com `errors="replace"`: a linha vira JSON inválido e é ignorada | `src/data/layout.py` |
| ressalva da junção de letras | par de letras só entra na sequência se tiver a mesma caixa (`"PA"` sim, `"Sr."` não) | `src/data/extrator.py:_juntar_letras_espacadas` |

Também: páginas que não renderizam passam a ficar registradas no cache como falha, e
`reextrair.py`, `preparar_lote.py`, `projetar_ordem.py` e `avaliar_segmentacao.py` segmentam essas
páginas sem tabelas (`stats.layout = false`), avisando.

## Tarefa: CONFIRMAÇÃO, sem alterar nenhum arquivo

Reexecute as suas reproduções dos itens 1 a 4 e da ressalva contra o código atual e diga se cada
um está resolvido. Procure só defeitos NOVOS introduzidos por essas cinco mudanças e pelo
tratamento de `regioes` = None nos quatro chamadores. Não repita o resto da revisão.

Mesmas restrições: nada de detector nem de scripts que gravam em `data/` (a GPU e a CPU estão
com o Claude). Trechos de Python só de leitura; para multiprocessing no Windows, o código com
`Pool` precisa estar num arquivo com `if __name__ == "__main__":`, não no stdin.

## Resposta final

Em FEITO: uma linha por item ("resolvido" ou "não resolvido", com a reprodução) e, se houver,
defeitos novos no formato das revisões anteriores. Se tudo estiver resolvido, diga isso
explicitamente: é a condição para liberar a re-extração das coleções (T05).
