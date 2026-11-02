## Contexto

Você escreveu `src/eval/relatorio_v4.py`, `notebooks/relatorio_ordem_v4.ipynb` e `docs/RELATORIO_V4.md`
(T37). O Claude revisou e pede as correções abaixo. Desde então rodou uma ablação nova: o VLM no
`golden_v4` **sem as classes das caixas no prompt** (`pred_vlm_gemini_3_1_flash_lite_sem_classes.jsonl`,
já avaliado em `resultados/golden/golden_v4/avaliacao.json`). Motivo: no `golden_v4` cada caixa leva a
classe anotada à mão no Diamond (cabeçalho, rodapé, assinatura...), e só o VLM recebe essa informação; os
outros métodos não. No `golden_v3` (sem classes humanas; só `tabela`) o VLM com marcas tem τ 0,924.

## Correções (altere só os três arquivos; o `.md` continua gerado pelo script)

1. **VLM e classes:** inclua o VLM sem classes na tabela da seção 2, na seção 3 (Wilcoxon + Holm) e na
   seção 6, numa tabela "com marcas e classes / com marcas, sem classes / sem marcas, com classes". Na seção
   1 e na 6, diga quanto do τ do VLM vem das classes (diferença e Wilcoxon pareado entre com e sem classes)
   e cite o τ do VLM no `golden_v3` (calculado pelo script a partir das predições de lá). Nas limitações,
   acrescente: as classes do prompt vêm da anotação humana; o prompt usa as mesmas regras do guia que o
   anotador seguiu (é o desenho do experimento, mas favorece o VLM frente a métodos sem regras).
2. **Não afirme superioridade sem significância:** onde o texto diz que o LayoutLM "supera" a XY-cut,
   escreva que o τ médio é maior mas a diferença não é significativa após Holm. Revise todo o relatório
   por frases assim.
3. **Seção 6.2:** a coluna "Diagnóstico do erro" é heurística do script, não análise. Troque por
   colunas medidas (n de blocos, colunas, tabelas, válida, rótulos devolvidos) e tire o texto
   interpretativo.
4. **Seção 9 (custo):** acrescente que 20 das 44 páginas do `golden_v4` já tinham sido ordenadas pelo
   mesmo anotador no `golden_v3` (familiaridade reduz o tempo); mostre a mediana separada para essas 20 e
   para as 24 novas.
5. **Seção 11:** retire "apto a gerar pseudo-rotulações confiáveis". Proponha, com os números, avaliar o
   VLM como fonte de rótulo de ordem só depois de medir a concordância com o humano em páginas novas e sem
   classes humanas. Mantenha os outros passos, sem adjetivos que os números não sustentam.
6. **Seção 4:** a linha do VLM sem marcas diz "Ausente no golden_v3": mantenha, e acrescente a do VLM sem
   classes como ausente no `golden_v3` também.
7. **LLMs de texto no `golden_v4` (chegaram do Kaggle):** `resultados/golden/golden_v4/pred_llm_qwen3_8_27b*.jsonl`
   e `pred_llm_gemma4_31b*.jsonl` (zero-shot e few-shot com 2 exemplos), já em `avaliacao.json`; o registro
   (tempo por página na T4, proporção de permutações válidas) está em
   `resultados/golden/golden_v4/execucoes_llm.jsonl`. Inclua as quatro nas tabelas das seções 2, 3 e 4
   (agora com os dois lotes) e no custo (seção 9), no lugar de qualquer "pendente do Kaggle". As LLMs
   recebem só texto e coordenadas, sem classes: diga isso ao compará-las com o VLM.

Rode `venv\Scripts\python.exe src\eval\relatorio_v4.py`, confira o notebook como antes e cole na resposta
as seções 1 e 6 novas. Sem GPU, rede ou alteração de dados.
