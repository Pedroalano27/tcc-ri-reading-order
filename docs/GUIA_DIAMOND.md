# Diamond: guia de anotação de caixas e classes

O Golden anota a **ordem** dos blocos que o extrator entrega. O Diamond anota a **própria
segmentação**: onde cada região começa e termina, e o que ela é. Serve para medir o extrator
e, depois, treinar um segmentador (detector ajustado aos diários ou rotulagem de palavras com o
LayoutLM).

## Como abrir

```bash
venv\Scripts\python.exe src\anotacao\servidor.py --diamond
```

Abre `http://127.0.0.1:8770/diamond`. Escreva seu nome em **Anotador** (o mesmo de sempre).
Tudo é salvo sozinho, como rascunho, em `data/diamond/<lote>/anotacoes.jsonl`.

## O que chega pronto

Cada página vem com uma **proposta**: as regiões do detector Docling Heron (as mesmas do cache
de layout) ajustadas às palavras do PDF, com os blocos das regras v3 cobrindo o que o detector
não viu. Você só corrige. O painel mostra os **alertas**, e <kbd>N</kbd> leva ao próximo:

| Alerta | O que é | Impede concluir? |
|---|---|---|
| Palavras sem caixa | palavra com letra ou dígito fora de qualquer caixa (vermelho) | sim |
| Palavras em duas caixas | palavra dentro de duas caixas que não são figura (magenta) | sim |
| Caixa atravessa colunas | a caixa junta palavras de blocos lado a lado | não |
| Campos ou artigos na mesma caixa | uma linha do meio abre um campo em MAIÚSCULAS ("OBJETO: …") ou um artigo ("Art. 2º") | não |
| Rótulo sem o valor na caixa | a caixa é só um rótulo terminado em ":" | não |
| Parece assinatura | nome e cargo numa caixa que não é Assinatura | não |
| Proposta juntou caixas sobrepostas | o detector marcou duas regiões que disputavam palavras; viraram uma | não |
| Detector pouco confiante | score abaixo de 0,55 | não |
| Só as regras viram | o detector não marcou nada ali | não |

Os três últimos só aparecem enquanto a caixa está como a proposta deixou. Os de regra ("campos",
"rótulo", "assinatura") são pistas: se a sua leitura for outra (por exemplo, "Mat.:" e "Cargo:"
dentro de um registro de lista), ignore.

## Regras

- **Uma caixa por parágrafo**, dentro de uma coluna. Nunca atravesse colunas.
- **Título** (1): título de ato ou de seção — DECRETO Nº…, PORTARIA…, RESOLVE: — em caixa própria.
- **Texto** (2): parágrafo corrido, inclusive a ementa (resumo recuado do ato).
- **Campos** ("PROCESSO SEI: 267…", "ACORDANTE: Ver. …", "OBJETO: …"): **uma caixa por campo,
  com o rótulo junto do valor**, mesmo quando o valor quebra linha. Nunca separe o rótulo do valor,
  e nunca junte dois campos. Linha de local e data ("Porto Alegre, 24 de fevereiro de 2023.") é Texto.
- **Lista** (3): a lista contígua inteira (itens com marcador, relação de nomes) numa caixa só.
- **Tabela** (4): a tabela inteira numa caixa só.
- **Assinatura** (5): nome e cargo de quem assina, no fim do ato.
- **Cabeçalho** (6) e **Rodapé** (7): topo e pé do diário — nome, data, edição, número da página.
- **Figura** (8): brasão, foto, carimbo, QR code. Pode conter texto; o texto de um cabeçalho
  decorado ganha caixa própria.
- **Outro** (9): o que não cabe em nenhuma.

Na dúvida, escolha e marque **Página difícil**. Estas regras são do piloto: o que não funcionar
nas 20 páginas muda antes das 200.

## Mouse e teclado

| Ação | Como |
|---|---|
| Selecionar | clique (Shift soma; Shift+arraste numa área vazia seleciona várias) |
| Desenhar caixa nova | arraste numa área vazia (Alt+arraste desenha por cima de outra caixa); ela se ajusta às palavras |
| Mover / redimensionar | arraste a caixa selecionada / as alças |
| Classe | <kbd>1</kbd>–<kbd>9</kbd> ou os botões do painel (sem seleção, define a classe da próxima caixa) |
| Ajustar às palavras | <kbd>A</kbd> (<kbd>Shift</kbd>+<kbd>A</kbd> em todas) |
| Dividir | <kbd>D</kbd> e clique na altura do corte; <kbd>Shift</kbd>+<kbd>D</kbd> na largura |
| Juntar | <kbd>J</kbd> |
| Apagar | <kbd>Del</kbd> |
| Desfazer / refazer | <kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> |
| Camadas | <kbd>L</kbd> rótulos · <kbd>P</kbd> palavras · <kbd>B</kbd> blocos das regras · <kbd>M</kbd> detector |
| Zoom | <kbd>+</kbd> <kbd>−</kbd> ou Ctrl+roda |
| Concluir / navegar | <kbd>Enter</kbd> / <kbd>←</kbd> <kbd>→</kbd> |

## O que é gravado

Uma linha por página e anotador: as regiões (`id`, `classe`, `bbox` em pontos, `de` = de qual
região da proposta veio), marcações, nota, tempo ativo, e `mudancas` — quantas regiões da proposta
ficaram intactas, mudaram de caixa, de classe, foram apagadas ou criadas. Isso mede quanto a
pré-anotação ajuda e onde o detector erra.

## Lotes

```bash
venv\Scripts\python.exe src\anotacao\preparar_diamond.py --lote diamond_piloto --de-lote _avaliacao/golden_v3 --n 20
```

O piloto usa páginas do `golden_v3`, que já têm ordem anotada: com as caixas corrigidas, dá para
medir quanto a segmentação limita a ordem. A proposta dele é a v1 (sem regras).

```bash
venv\Scripts\python.exe src\anotacao\preparar_diamond.py --lote diamond_treino --colecao data/processed/blocos data/processed/blocos_extra --n 200 --workers 6
```

O `diamond_treino` sorteia 200 páginas de todos os veículos **menos os três de teste** (CE, MA e RJ),
guardados para avaliar o segmentador sem vazamento, e de nenhuma página já usada no Golden ou no
Diamond. A proposta é a v2 (`src/data/regioes.py` com as regras tiradas das correções do piloto).

## Medir um segmentador

```bash
venv\Scripts\python.exe src\eval\avaliar_diamond.py --lote diamond_piloto --ablacao --rose rose_piloto
```

Compara, pelas palavras de cada região, os blocos v3, a proposta gravada, `src/data/regioes.py` e os
lotes do Rose com a anotação humana; grava `resultados/diamond/<lote>/avaliacao.{json,md}`.
