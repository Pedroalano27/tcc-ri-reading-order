## Objetivo

Escolher, **com medida**, a regra que agrupa linhas em blocos no segmentador
(`construir_blocos` em `src/data/extrator.py`), implementar as candidatas e deixar a
recomendação pronta para a decisão do Pedro. É a tarefa que destrava a re-extração (T05),
o Golden (T06) e todos os números do TCC.

## O que já se sabe

Leia `docs/HANDOFF.md` seção 2.2 e as entradas de 17:31 (Codex), 17:40 e 17:47 (Claude) no
registro de `COMUNICACAO_AGENTES.md`. Resumo:

- **v1** cortava a linha por limiar de distância: texto embaralhado dentro do bloco.
- **B** (corte em calha + agrupamento por coluna com sobreposição horizontal ≥ 50% da largura do
  menor): sobreposição caiu, mas **funde texto corrido** — no CE, página inteira em 2 blocos;
  títulos centralizados ("LOTE 139/2025") entram no parágrafo de baixo; listas inteiras viram um bloco.
- **C** (código atual: margem esquerda compatível entre −5 e +2,5 larguras de caractere): resolve o
  CE, mas **picota onde há recuo** — primeira linha de parágrafo e item de lista com continuação na
  margem. No MA o recuo é de 9 larguras de caractere. As imagens em
  `resultados/inspecao_segmentacao/*_comparativo.png` mostram isso.
- **D** (testada pelo Claude em rascunho): C trocando a margem por "linha anterior curta fecha o
  bloco" (linha termina antes de `borda_direita_da_coluna − 4 lc`, com a borda da coluna = percentil
  90 do `x1` das linhas daquela coluna) e recuo de primeira linha até 12 lc, mantendo a sobreposição
  ≥ 50% da B.

Bancada de 44 páginas (`src/data/avaliar_segmentacao.py`, amostra de `resultados/avaliacao_segmentacao.json`):

| Regra | Blocos/pág. | % sobrepostos | % 1 palavra | Rejeitadas | Págs. c/ bloco > 250 pal. |
|---|---:|---:|---:|---:|---:|
| B | 41,7 | 10,5 | 23,9 | 1 | 8 |
| C | 61,4 | 4,9 | 18,4 | 0 | 6 |
| D | 97,7 | 1,6 | 21,5 | 3 | 1 |

Por página-problema (B / C / D): MA 36 / 85 / 54; SE 30 / 48 / 57; **RJ 53 / 159 / 159**; CE 2 / 15 / 15.

Nenhuma regra ganha em tudo. A D não mexe no RJ e dobra a fragmentação média.

## Escopo

Pode **alterar** `src/data/extrator.py` (só a parte de linhas → blocos e o que ela precisar) e
`src/data/avaliar_segmentacao.py`. Pode **criar** `resultados/avaliacao_segmentacao_t03.json` e
arquivos novos em `resultados/inspecao_segmentacao/`.

**Não** re-extraia coleções, **não** escreva em `data/`, **não** altere `src/data/reextrair.py`,
`src/eval/*.py` nem `src/data/converter_apis.py`.

## O que fazer

1. **Régua externa.** A T10 produziu os parágrafos do Azure em `data/processed/blocos_api_azure/`
   (12 páginas; leia a resposta da T10 no registro para as ressalvas). Implemente na bancada uma
   medida de concordância com essa segmentação de referência, por página, usando as **palavras**
   (`palavras_da_pagina`) como unidade comum: cada palavra pertence a um bloco nosso e ao parágrafo
   do Azure cuja caixa contém o centro dela (palavras sem parágrafo ficam fora da conta). Reporte:
   - **fragmentação**: % de parágrafos do Azure cujas palavras caem em mais de um bloco nosso, e o
     número médio de blocos nossos por parágrafo, ponderado por palavras;
   - **fusão**: % de blocos nossos com palavras de mais de um parágrafo do Azure, ponderado por palavras;
   - blocos por página nossos × parágrafos por página do Azure.
2. **Candidatas selecionáveis.** Torne a regra de agrupamento um parâmetro de `construir_blocos` e de
   `segmentar` (sugestão: `regra="margem"`), com as candidatas **B**, **C** e **D** exatamente como
   descritas acima, e **pelo menos uma candidata sua** que ataque as duas falhas restantes: a
   fragmentação do RJ (descubra a causa nas imagens e nas linhas daquela página antes de propor) e a
   fragmentação média da D. Explique cada candidata num comentário curto.
3. **Não mude o comportamento padrão.** O padrão continua sendo a C (código atual) até a decisão do
   Pedro: `segmentar(ws)` sem argumento tem de devolver exatamente os mesmos blocos de hoje.
4. **Meça tudo:** para cada candidata, a bancada de 44 páginas (as métricas que ela já tem) **e** a
   concordância com o Azure nas 12 páginas. Grave em `resultados/avaliacao_segmentacao_t03.json` e
   gere, com `src/data/inspecionar_segmentacao.py` como referência de estilo, as imagens da sua melhor
   candidata nas quatro páginas-problema.
5. **Recomende** uma candidata, com os números e o critério usado. Critério sugerido, nesta ordem:
   (a) nenhuma página dos veículos de teste (CE, MA, RJ) rejeitada pelo filtro de 3 a 200 blocos;
   (b) sobreposição ≤ 5%; (c) menor soma de fragmentação e fusão contra o Azure; (d) menos páginas com
   bloco acima de 250 palavras. Se discordar do critério, diga por quê.

## Pronto quando

1. A resposta final traz a tabela candidata × métrica (bancada e Azure) e a recomendação.
2. `segmentar(ws)` sem argumento devolve os mesmos blocos que o código de antes, conferido nas quatro
   páginas-problema (MA 85, SE 48, RJ 159, CE 15).
3. `venv\Scripts\python.exe src\data\avaliar_segmentacao.py` roda com as candidatas sem erro.
4. Todos os `.py` de `src/` passam por `ast.parse`.
