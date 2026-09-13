# Guia de anotação da ordem de leitura (Golden Dataset)

Este guia define **como** anotar e **por que** cada regra existe. Ele é a base da
seção "Protocolo de anotação" da metodologia: a banca vai perguntar como a verdade
de referência foi construída, e a resposta está aqui.

---

## Para que serve a anotação

Até agora, todos os resultados usam uma referência **automática**: o fluxo do PDF, nos
veículos em que ele concorda com a XY-cut. Isso tem dois problemas conhecidos:

1. favorece a XY-cut por construção (ressalva registrada em `RESULTADOS_PRELIMINARES.md`);
2. não diz nada sobre os 19 veículos em que o fluxo do PDF não é confiável.

A anotação humana resolve os dois. Cada grupo do lote responde a uma pergunta:

| Grupo | De onde vêm as páginas | Pergunta que responde |
|---|---|---|
| `silver` | veículos de teste (CE, MA, RJ) | A referência automática concorda com um humano? Se sim, os resultados preliminares ficam validados. |
| `incerto` | veículos em que o fluxo do PDF não é confiável | Onde hoje não sabemos quem acerta: XY-cut, LayoutLM ou LLM? |
| `official_diary_go` | Goiás, fora do acervo | Os métodos funcionam num veículo que nenhum deles viu (teste fora do domínio)? |

O lote `golden_v1` já está pronto: **30 páginas** (10 `silver` + 20 `incerto`, uma ou
duas de cada veículo), **1.044 blocos** no total, cerca de 35 por página.

---

## Passo a passo

1. **Abrir a ferramenta** (na pasta do projeto):

   ```
   venv\Scripts\python.exe src\anotacao\servidor.py
   ```

   O navegador abre em `http://127.0.0.1:8770`. Escreva seu nome no campo **Anotador**.

2. **Anotar.** Tudo é salvo sozinho em `data/golden/golden_v1/anotacoes.jsonl`, segundos
   depois de cada clique. Pode fechar e voltar outro dia: a ferramenta reabre na
   primeira página pendente.

3. **Avaliar**, a qualquer momento, mesmo com o lote pela metade:

   ```
   venv\Scripts\python.exe src\eval\avaliar_golden.py --lote golden_v1
   ```

   O relatório sai em `resultados/golden/golden_v1/avaliacao.md`.

---

## Como usar a ferramenta

| Ação | Como |
|---|---|
| Numerar um bloco | clique nele; ele recebe o próximo número |
| Numerar uma coluna inteira | arraste um retângulo sobre **uma** coluna; os blocos de dentro entram de cima para baixo |
| Corrigir | clique num bloco já numerado: a sequência é cortada ali e você continua dele |
| Desfazer | <kbd>Z</kbd>, <kbd>Backspace</kbd> ou <kbd>Ctrl</kbd>+<kbd>Z</kbd> |
| Conferir | leia o painel **Texto na ordem escolhida**: as frases precisam emendar |
| Concluir | <kbd>Enter</kbd> (só conclui com todos os blocos numerados; os que faltam piscam) |
| Pular | menu **Pular esta página…**, com o motivo |
| Navegar | <kbd>←</kbd> <kbd>→</kbd> ou a lista à esquerda |
| Zoom | <kbd>+</kbd> <kbd>−</kbd>, **Página inteira**, **Largura** |
| Trilha (setas entre blocos) | <kbd>T</kbd> liga e desliga |

Blocos **laranja tracejados** ainda não têm número; **azuis** já têm; o **azul forte** é o
último numerado. Passar o mouse mostra, na barra de cima, o número que o bloco vai
receber e o começo do texto dele.

### Como ir rápido

O **laço é o atalho que mais economiza tempo**: um arrasto sobre uma coluna numera todos
os blocos dela de cima para baixo, e a ferramenta avisa quantos entraram ("4 blocos
numerados de cima para baixo. Confira; Z desfaz."). Numa página de duas colunas bem
comportada, dá para fechar tudo com três ou quatro arrastos — cabeçalho, coluna esquerda,
coluna direita, rodapé — e só depois ajustar no clique o que ficou fora de ordem.

Anote em sessões curtas. Dez páginas por vez, três dias seguidos, custa menos do que
tentar fechar as 30 de uma vez, e a ferramenta reabre exatamente onde você parou.

---

## Regras de leitura

1. **Leia como uma pessoa leria a página impressa.** A pergunta é sempre: "em que
   ordem eu leria isto para entender o conteúdo?".
2. **Cabeçalho do diário primeiro** (nome do diário, órgão, data, número da edição).
   **Rodapé por último** (número da página, endereço, carimbos de rodapé).
3. **Colunas:** a da esquerda inteira, de cima para baixo, depois a próxima.
4. **Título ou bloco que atravessa as colunas separa seções:** leia o que está acima
   dele (coluna por coluna), depois o título, depois as colunas abaixo dele.
5. **Ato que continua na coluna seguinte:** siga a continuação do texto. Use o painel
   de texto para confirmar que a frase emenda.
6. **Tabela:** desde o `golden_v2`, a ferramenta mostra a tabela inteira como **uma caixa só**,
   com contorno verde tracejado (o extrator acha a tabela com um detector de layout; ver
   `src/data/layout.py`). Numere-a no ponto em que a tabela é lida, em geral logo depois do
   título dela; a ordem das células não entra na anotação. Se a tabela vier picada em várias
   caixas (o detector não a reconheceu), leia linha por linha, da esquerda para a direita.
   Nos dois casos, marque **Tem tabela**.
7. **Assinaturas, cargos e datas no fim de um ato** pertencem ao ato: vêm logo depois
   do texto dele, antes do próximo ato.
8. **Marginália** (texto na margem, selo, número de artigo solto): onde ela é lida
   naturalmente, em geral junto do trecho que acompanha.
9. **Duas leituras igualmente plausíveis:** escolha a mais natural e marque **Ordem
   ambígua**. Essas páginas são analisadas à parte.
10. **Bloco que mistura texto de colunas diferentes** (erro do extrator): numere-o onde
    começa o texto dele e marque **Bloco mistura colunas**. Não dá para dividir o bloco
    na ferramenta, e isso é de propósito: todos os métodos recebem os mesmos blocos.

---

## Cuidados metodológicos (vão para o texto do TCC)

- **Anotação cega.** A ferramenta não mostra nenhuma ordem automática: os blocos
  aparecem sem número e com identificadores embaralhados. Não consulte os resultados
  dos métodos antes de terminar o lote.
- **Não reanote depois de ver os resultados.** Cada anotação guarda a hora em que foi
  salva (`salvo_em`); corrigir páginas depois de ver quem acertou introduz viés de
  confirmação.
- **Concordância entre anotadores.** Peça a um colega que anote 8 a 10 páginas do mesmo
  lote com o nome dele. O avaliador calcula o tau entre vocês dois, que é o teto
  realista de qualquer método. Acima de 0,9 é concordância muito alta.
- **Páginas puladas** são contadas e relatadas, nunca descartadas em silêncio.
- **Custo.** A ferramenta mede o tempo ativo por página (o relógio para após 60 s
  sem mexer). O custo humano de anotar é um dado de eficiência para o capítulo de
  resultados: quanto custa produzir a referência que os métodos tentam imitar.

---

## Goiás (grupo fora do domínio)

O plano original do TCC previa 20 páginas de Goiás, que não está no acervo.

1. Baixe algumas edições de datas variadas em
   [diariooficial.go.gov.br](https://www.diariooficial.go.gov.br) (10 a 20 PDFs bastam)
   e salve em `data/raw/official_diary_go/`.
2. Prepare o lote, que extrai os blocos e sorteia as páginas:

   ```
   venv\Scripts\python.exe src\anotacao\preparar_lote.py --lote goias --grupo official_diary_go:20 --extrair
   ```

3. Ele aparece no seletor **Lote** da ferramenta.

---

## Quanto tempo leva

Estimativa inicial: 2 a 4 minutos por página, ou seja, **1 a 2 horas** para as 30
páginas do `golden_v1`. O número real sai no relatório do avaliador; anote-o no
diário de bordo.
