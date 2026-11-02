## Contexto

`src/data/regioes.py` é o segmentador por regiões (pré-anotação do Diamond). A v2 (regras
`REGRAS_PADRAO`) gerou as propostas do `data/diamond/diamond_treino/` (199 páginas). O Pedro anotou 25
delas; `src/eval/avaliar_diamond.py --lote diamond_treino --rose rose_treino` dá, nessas 25:
proposta v2 F1@0,5 0,916 e F1@0,5 com classe 0,789; Rose (`data/diamond/rose_treino/`, VLM que corrige a
proposta) 0,903 e 0,756, mas com revocação muito maior em **assinatura** (0,95 contra 0,64) e
**cabeçalho** (0,92 contra 0,82). O humano marcou 55 regiões como `outro`: quase todas **marcas de
diagramação** que vazam na camada de texto (`<@textFrameStart>`, `<@textFrameStart/>`, `contPageBreak`) e
palavras embaralhadas na borda da página. O objetivo é a v3 da proposta, para as ~174 páginas que o Pedro
ainda não anotou.

## Tarefa

Altere **só** `src/data/regioes.py` e `src/eval/avaliar_diamond.py`; crie `src/anotacao/atualizar_proposta.py`
e `tests/test_regioes_v3.py`.

1. **Versões reproduzíveis** em `regioes.py`: guarde as regras da v2 em `REGRAS_V2` (igual ao
   `REGRAS_PADRAO` atual) e crie `REGRAS_V3`; `propor(..., regras=True)` passa a usar a v3; `regras="v2"`
   reproduz a v2. Confira que `propor(..., regras="v2")` devolve exatamente a `proposta` gravada nas 199
   páginas do `diamond_treino` (conte quantas batem; devem ser todas, exceto as páginas 11 e 15, cujas
   coordenadas foram deslocadas pela origem da página — nelas as caixas devem bater deslocadas).
2. **Regra `outro_marcacao`**: palavras que são marca de diagramação (comece por uma regex para `<@...>`,
   `contPageBreak` e variações; olhe o texto das regiões `outro` do humano no `diamond_treino` para
   completar a lista, sem pegar texto de verdade) saem da região em que estão e formam região(ões)
   `outro`, uma por linha; a região de origem é reajustada às palavras que ficaram (se ficar vazia, some).
   A cobertura continua completa (nenhuma palavra sem região ou em duas).
3. **Classes do Rose** (`aplicar_classes_rose(regioes, palavras, regioes_rose, classes)`): para cada
   região, a classe majoritária (por palavras) das regiões do Rose que cobrem as palavras dela; se estiver
   em `classes` e for diferente, adota. Não mexe em caixa.
4. **Avaliação** em `avaliar_diamond.py`: quando houver `--rose`, acrescente os sistemas
   `regioes_v3+rose:<conjunto>` para os conjuntos `todas`, `assinatura_cabecalho`,
   `assinatura_cabecalho_titulo_rodape` (classes do Rose sobre as caixas da v3). Mantenha `regioes` (v3) e
   inclua `regioes_v2`.
5. **Rode** e cole as tabelas na resposta:
   `venv\Scripts\python.exe src\eval\avaliar_diamond.py --lote diamond_treino --rose rose_treino`
   e `venv\Scripts\python.exe src\eval\avaliar_diamond.py --lote diamond_piloto --rose rose_piloto_v2`.
   Recomende a variante com maior F1@0,5 com classe que não perca mais de 0,005 de F1@0,5 em nenhum dos
   dois lotes. Lembre na resposta: a proposta v2 é a que o humano viu (vantagem de ancoragem).
6. **`atualizar_proposta.py --lote L --versao v3 [--rose LOTE_ROSE --classes-rose CONJ] [--aplicar]`**:
   recalcula a proposta **só das páginas sem nenhuma anotação** (qualquer anotador, qualquer status) em
   `data/diamond/L/anotacoes.jsonl`; sem `--aplicar`, só relata quantas páginas e regiões mudariam. Com
   `--aplicar`: cópia de segurança `tarefas.jsonl.bak_<data>`, **relê as anotações logo antes de gravar**
   (se o Pedro anotou uma página no meio, ela fica de fora), grava por arquivo temporário + `os.replace`,
   atualiza `proposta`, `proposta_versao`, `stats` de cada página alterada e registra em
   `data/diamond/L/derivados/atualizacoes.jsonl` (data, versão, páginas). Nunca toca em `anotacoes.jsonl`,
   `palavras`, `imagem`, `n`. **Rode só sem `--aplicar`** e cole o relato.

## Testes

`tests/test_regioes_v3.py`: marcação vira `outro` e a região de origem se ajusta; texto comum com `<` ou
"@" não vira `outro`; classes do Rose por maioria e só nas classes pedidas; `regras="v2"` igual à v2;
`atualizar_proposta` num diretório temporário: pula página com anotação (inclusive rascunho), relê antes de
gravar, não altera `anotacoes.jsonl`. Rode `venv\Scripts\python.exe -m unittest discover -s tests -v`
(todos passam, inclusive os 67 antigos).

## Regras

Sem GPU, sem rede. Não altere `data/` (a não ser que um teste crie um diretório temporário), nem
`tarefas.jsonl` de lote nenhum, nem outros arquivos de `src/`.

## Resposta final

Em FEITO: as duas tabelas, a variante recomendada e o relato do `atualizar_proposta.py` sem `--aplicar`.
