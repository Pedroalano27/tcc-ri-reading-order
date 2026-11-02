## Contexto

O Pedro terminou o `golden_v4`: a ordem de leitura de 45 páginas (44 concluídas, 1 pulada) anotada
sobre as **regiões corrigidas à mão no Diamond** (`data/golden/golden_v4/`, montado por
`src/anotacao/preparar_ordem_diamond.py`; regras em `docs/GUIA_ORDEM_LEITURA.md`). Até aqui a ordem
humana era sobre os blocos do extrator v3 (`_avaliacao/golden_v3`, 47 páginas). As 20 páginas do
`diamond_piloto` estão nos **dois** conjuntos (mesma página, segmentações diferentes).
`orquestracao/avaliar_v4.sh` acabou de rodar (log em `orquestracao/logs/avaliar_v4/`):
`src/eval/avaliar_golden.py` nos dois conjuntos (métodos locais: fluxo do PDF, aleatória, ingênua,
XY-cut, LayoutLM pontual e sucessor com 3 sementes cada, ablações sem layout, sem posição, sem viés
geométrico e sem texto; VLM `gemini-3.1-flash-lite` com e sem marcas desenhadas na imagem; LLMs de texto
do Kaggle só existem, por enquanto, no `golden_v3`). Resultados em
`resultados/golden/golden_v4/avaliacao.{json,md}` e `resultados/golden/_avaliacao/golden_v3/...`, com
as predições `pred_*.jsonl` ao lado. Segmentação: `resultados/diamond/*/avaliacao.{json,md}`.

## Tarefa

Crie **só** `src/eval/relatorio_v4.py`, `notebooks/relatorio_ordem_v4.ipynb` e `docs/RELATORIO_V4.md`
(o `.md` é gerado pelo script; o notebook chama as funções do script e mostra as mesmas tabelas e duas
figuras). Nada de GPU, rede ou alteração de dados.

O script lê anotações, tarefas e predições e recalcula as métricas com `src/eval/metrics.py` (as mesmas
funções do `avaliar_golden.py`: τ de Kendall, sucessor correto, ARD normalizado, acerto exato), para
poder cortar por página. Seções do relatório:

1. **Resumo** em 5 a 8 linhas, só com números do relatório.
2. **`golden_v4` (44 páginas):** tabela de todos os métodos — τ médio com IC 95% por bootstrap (semente
   fixa), mediana, p10, sucessor correto, ARD normalizado, acerto exato, permutações válidas (VLM/LLM) —
   ordenada por τ; média ± desvio das 3 sementes de cada formulação do LayoutLM.
3. **Testes pareados:** Wilcoxon de cada método contra a XY-cut no `golden_v4`, com correção de
   Holm; diga quais diferenças sobrevivem.
4. **Efeito da segmentação (20 páginas comuns):** para cada método presente nos dois conjuntos, τ e
   sucessor correto no `golden_v3` × `golden_v4` nas mesmas 20 páginas, diferença e Wilcoxon pareado.
   Ressalva: a referência também mudou (a ordem foi reanotada sobre outras caixas, pela mesma pessoa).
5. **Por tipo de página:** τ por número de colunas (1, 2, 3+) e com/sem tabela no `golden_v4`, para
   XY-cut, LayoutLM sucessor (semente 42), VLM com marcas e a melhor LLM disponível.
6. **VLM:** com × sem marcas (τ, sucessor, válidas, segundos por página); onde erra mais (as 5 piores
   páginas do VLM com marcas, com page_id, colunas e τ).
7. **LayoutLM fora do domínio de treino:** ele foi treinado sobre blocos do extrator v3; compare o τ no
   `golden_v3` e no `golden_v4` e a queda relativa por formulação.
8. **Segmentação (Diamond):** reproduza as tabelas principais de `resultados/diamond/*/avaliacao.json`
   (v3, proposta, regiões, Rose, regiões v3 + classes do Rose).
9. **Custo humano:** tempo ativo por página no `golden_v2`, `golden_v4`, `diamond_piloto` e
   `diamond_treino` (mediana e total, só páginas concluídas).
10. **Limitações:** anotador único; ancoragem da proposta no Diamond; referência reanotada; texto só
    em imagem (13,8% das páginas do acervo têm região de texto sem palavra no PDF — número do
    levantamento de 13/09 no `COMUNICACAO_AGENTES.md`); LLMs do `golden_v4` pendentes do Kaggle.
11. **Próximos passos sugeridos** para extração e treino, cada um apoiado num número do relatório.

Regras: todo número vem de cálculo do script (nada digitado à mão, exceto o 13,8% citado com a
fonte); método ausente aparece como "—" com o motivo; o script roda de novo sem erro quando chegarem as
predições das LLMs do Kaggle no `golden_v4`. Rode `venv\Scripts\python.exe src\eval\relatorio_v4.py` e
confira que o notebook executa (`venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute
notebooks/relatorio_ordem_v4.ipynb --output relatorio_ordem_v4.ipynb` se o jupyter estiver instalado;
senão, execute as células com `exec` num script de verificação e diga isso).

## Resposta final

Em FEITO: a seção 1 (resumo) e as tabelas das seções 2 e 4.
