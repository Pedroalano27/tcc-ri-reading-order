## Contexto

A segmentação v3 (`src/data/extrator.py`, `src/data/layout.py`, `src/anotacao/projetar_ordem.py`)
passou por três revisões do Codex, que acharam defeitos reais com reproduções pequenas. As
correções não têm teste automático. Esta tarefa transforma essas reproduções em testes de
regressão. O pytest **não** está instalado: use `unittest`, da biblioteca padrão, e não instale
nada.

## Escopo

Crie somente `tests/__init__.py` (vazio) e `tests/test_segmentacao_v3.py`. Não altere nenhum outro
arquivo. Não use GPU, não rode o detector (`layout.Detector`) nem scripts que gravam em `data/` ou em
`resultados/`: o treino da noite está rodando.

## Casos (cada um é um método de teste; entradas sintéticas, montadas no próprio teste)

Palavras são dicts `{"t", "x0", "x1", "top", "bottom", "s"}`. Para uma linha: cada token com largura
`5 * len(t)` pt, vão de 2,5 pt, `top=100`, altura 9.

`extrator._juntar_letras_espacadas`:
1. juntam: `R E S O L V E:` → `["RESOLVE:"]`; `PA R E C E R` → `["PARECER"]`; `A T O S` → `["ATOS"]`;
   `w w w. c o n g o` → `["www.congo"]`;
2. não juntam (a lista sai igual): `e se eu me`, `SP RJ MG ES`, `I, II e XI do`, `e o Sr. J.`.

`extrator._cortes_locais(faixas, vao_max=36, larg_min=3.0, n_min=4, fator_espaco=0.1)`, com faixas
`{"ws": [...], "top", "bottom"}` e cada palavra ocupando um intervalo `[a, b]`:
3. cinco faixas iguais com palavras em `[0,10]` e `[30,60]` → há corte (`len(cortes) == 5`);
4. corredores incompatíveis: duas faixas `[0,10],[14,60]`, a central `[0,10],[30,60]`, duas
   `[0,26],[30,60]` → nenhum corte envolve as palavras da faixa central;
5. calha válida só abaixo: cinco faixas `[0,150]`; uma `[0,50],[60,150]`; a alvo `[0,50],[90,150]`;
   três `[0,80],[90,150]` → o par de palavras da faixa alvo está em `cortes`.

`projetar_ordem.projetar_pagina(anotacao, palavras_antigas, palavras_novas)`, com palavras
`[texto, x0, top, x1, bottom]`:
6. mesma segmentação, as duas ordens de inserção do dict de palavras novas → `"limpa"` nas duas;
   antigas `{"b0": [["A",0,0,1,1],["B",1.1,0,2.1,1]], "b1": [["C",10,0,11,1]]}`, ordem `["b0","b1"]`;
7. palavra nova sem par (`["NOVA",30,0,34,1]` acrescentada a b0) → `"conflito"` e
   `palavras_novas_sem_par == ["NOVA"]`;
8. separador perdido (antiga `["***",5,0,6,1]` em b0, ausente nas novas) → `"limpa"`;
9. texto exato antes de substring: antigas `{"b0": [["AA",0,0,4,4]], "b1": [["A",0,0,4,4]]}`, as
   duas atribuições de ids nas novas → `"limpa"` nas duas.

`layout.tabelas`:
10. `tabelas(None) is None`;
11. duas detecções `table` quase iguais (score 0,9 e 0,8) e uma `picture` → uma caixa só, a de 0,9;
    uma `table` com score 0,4 → fora.

`layout.GravadorCache` e `layout.carregar_cache`, numa pasta de `tempfile.TemporaryDirectory()`:
12. arquivo `x.jsonl` com um registro válido (com `"revisao": layout.REVISAO` e `"escala": 1.0`)
    seguido de um fragmento sem quebra de linha; gravar outro registro com o gravador →
    `carregar_cache` devolve os dois page_ids;
13. idem, com o fragmento terminando no meio de um caractere UTF-8 (bytes `b'{"page_id":"Edi\xc3'`)
    → sem exceção, os dois registros válidos voltam;
14. `gravador.falha(pid, uf, "erro")` → `carregar_cache` devolve `None` para esse page_id.

## Validação

`venv\Scripts\python.exe -m unittest tests.test_segmentacao_v3 -v` com todos passando. Se algum
caso falhar por defeito do código, e não do teste, **não corrija o código**: marque o teste com
`@unittest.expectedFailure`, com um comentário que diga o defeito, e relate na resposta final.

## Resposta final

Em FEITO: a saída resumida do unittest (quantos passaram e falharam) e a lista de casos marcados
como falha esperada, com o motivo.
