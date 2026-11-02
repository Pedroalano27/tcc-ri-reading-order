## Contexto

O Diamond é o conjunto em que o Pedro corrige as caixas e as classes das regiões das páginas
(`docs/GUIA_DIAMOND.md`). Duas peças novas precisam de testes de regressão:

- `src/anotacao/preparar_diamond.py`, função `propor(palavras, blocos_v3, detector)`: monta a
  pré-anotação juntando o detector e as regras v3. Leia a docstring do módulo e as funções
  `_resolver_sobreposicoes` e `propor`.
- `src/anotacao/servidor.py`, função `salvar_diamond(lote, reg)` e `_mudancas(regioes, proposta)`:
  validam e gravam a anotação de uma página.

## Tarefa

Crie `tests/test_diamond.py`, no mesmo estilo de `tests/test_segmentacao_v3.py` (unittest, sem
dependência nova), com casos pequenos montados à mão (palavras e regiões sintéticas, poucas
dezenas de pontos). Cubra pelo menos:

`propor`:
1. uma região de texto do detector com três palavras dentro vira uma região de classe `texto`
   com a caixa ajustada ao envelope das palavras;
2. regiões com score abaixo de `SCORE_MIN` são ignoradas;
3. uma tabela com um parágrafo detectado dentro: fica só a tabela, com todas as palavras;
4. figura não pega palavra: palavras dentro de uma figura e fora de outras regiões caem nos blocos
   v3 (origem `regras`), e a figura continua na proposta com a caixa original;
5. dois itens de lista vizinhos na mesma coluna viram uma única região `lista`; dois itens em
   colunas diferentes não;
6. duas regiões que, ajustadas, cobrem palavras uma da outra viram uma só, com a classe da que tem
   mais palavras e o alerta `juntou_sobrepostas`;
7. alertas `so_regras`, `baixa_confianca` (score entre `SCORE_MIN` e `SCORE_CONFIANTE`) e
   `atravessa_colunas` (região com palavras de dois blocos v3 lado a lado);
8. em todos os casos acima, nenhuma palavra com letra ou dígito fica sem região ou em duas regiões
   que não sejam figura (escreva um verificador e use em todos).

`salvar_diamond` (aponte `servidor.DIR_DIAMOND` para um diretório temporário com
`tempfile.TemporaryDirectory` e monte ali `tarefas.jsonl`; restaure o valor no `tearDown`):
9. rascunho válido é gravado e relido; gravar de novo a mesma página e anotador troca a linha;
10. classe inválida, id repetido, caixa sem área e anotador vazio levantam `ValueError`;
11. caixa fora da página é recortada aos limites da página;
12. `concluida` com palavra sem caixa ou em duas caixas levanta `ValueError`; com tudo coberto, grava;
13. `mudancas`: intacta, só caixa, só classe, apagada e criada contadas corretamente.

## Regras desta tarefa

- Escreva **só** `tests/test_diamond.py`. Não altere código de `src/`: se achar um defeito, descreva
  em PENDÊNCIAS com o caso que falha (e deixe o teste marcado com `unittest.expectedFailure` e um
  comentário).
- Não toque em `data/`: nada de ler ou gravar os lotes reais.
- Rode `venv\Scripts\python.exe -m unittest tests.test_diamond -v` e também
  `venv\Scripts\python.exe -m unittest discover -s tests -v` (os 14 testes antigos precisam
  continuar passando). Sem GPU e sem rede.

## Resposta final

Em FEITO: quantos testes, quantos passam, e qualquer defeito encontrado.
