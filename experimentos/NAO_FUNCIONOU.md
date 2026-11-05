# O que não funcionou (e o que aprendemos)

Histórico das tentativas que não trouxeram ganho, para não repeti-las sem um motivo novo.
Cada linha aponta para o relatório de origem, onde estão os números completos. Para
reabrir uma ideia daqui, o cartão novo precisa dizer **o que mudou** (dado, representação,
métrica) que justifica tentar de novo.

Convenção dos números: τ de palavras / quebras de leitura por página, nas bancadas
golden_v4 | golden_v3_novo | teste silver (CE/MA/RJ). Regra de colunas = 0,986/6,05 |
0,960/9,22 | 0,960/27,45.

## Fase 1 — blocos de parágrafo (setembro de 2026)

| Tentativa | Resultado | Por que não funcionou / aprendizado | Fonte |
|---|---|---|---|
| Ordem nativa do PDF como referência ou baseline | Não confiável | A ordem do fluxo do PDF muitas vezes não é a de leitura; só serve como silver ruidoso | `docs/RESULTADOS_PRELIMINARES.md` §1 |
| LLM zero-shot ordenando blocos (Gemini) | Falhou | Perde a geometria, confunde colunas; caro e lento | `docs/RESULTADOS_PRELIMINARES.md` §4.4 |
| BLEU de página como métrica | Não discrimina | Na granularidade de bloco o BLEU satura; trocado por τ, sucessor e quebras | `docs/RESULTADOS_PRELIMINARES.md` §4.5 |
| LayoutLM "pontual" (posição absoluta) | τ 0,671, 13% de sucessor | Prever a posição de cada bloco não captura continuidade; levou à formulação de sucessor | `docs/HANDOFF.md` §0 |
| Medir só τ | Engana | τ alto com texto picotado; criada a métrica de sucessor e depois a de quebras | `docs/RESULTADOS_PRELIMINARES.md` §4.8 |
| Segmentação em blocos de parágrafo | Erros internos aos blocos | 213 quebras dentro das caixas; motivou a representação em linhas (213 → 29) | `docs/RELATORIO_NOITE_0410.md` |

## Fase 2 — representação em linhas, sem caixas finas (outubro de 2026)

| Tentativa | Resultado | Por que não funcionou / aprendizado | Fonte |
|---|---|---|---|
| Extrator sem parágrafos v2 | 6,05 → 5,93 no v4; v3 igual | A extração em linhas já está perto do teto; o erro restante é de ordenação | `resultados/extrator_sem_paragrafos_v2.md` |
| LayoutLM sucessor só geometria, 3.140 págs | 0,924/9,00 \| 0,928/10,41 \| 0,934/29,15 | Mais dado ajuda (873 → 3.140), mas ainda perde da regra; variância entre sementes de 0,3 a 0,5 quebras | `docs/RELATORIO_NOITE_0410.md` §8 |
| LayoutLM sucessor lendo o texto das linhas | 0,942/20,77 \| 0,931/23,19 \| 0,930/50,46 | O texto atrapalha a continuidade nesse formato (K tokens por linha, 510 tokens); não mede continuidade de frase | `resultados/ordenadores_treinados_sem_caixas/treino_com_texto.md` |
| LayoutReader ajustado em linhas | Perde da regra | Pré-treinado por palavra; a granularidade de linha não casa (igual ao relatado em arXiv 2607.01018) | `resultados/ordenadores_sem_caixas.md` |
| BiLSTM geometria / geometria+texto | Perde da regra | Pouca capacidade e dado; mantido só como baseline | `resultados/ordenadores_sem_caixas.md` |
| Corretor de transições (MLP sobre candidatos) | Sem ganho consistente | 24 páginas de treino, 3 épocas; amostra pequena não exclui outra configuração | `resultados/corretor_de_transicoes.md` |
| Margens e transversais v2 | Ganho pequeno, IC inclui zero | Variantes ajustadas no v4 não generalizam | `resultados/margens_e_transversais.md` |
| Margens por repetição entre páginas do mesmo PDF | v4 6,05 → 4,89; v3 +1,0 (piora) | Sobreajuste ao golden_v4; o veto de corpo erra fora do ajuste | `resultados/margens_por_repeticao.md` |
| Regra + LayoutLM textual seletivo | +0,86 \| +1,37 \| +2,01 quebras (piora) | O modelo confia nos mesmos erros da regra ou erra onde ela acerta | `resultados/regra_mais_modelo_seletivo.md` |

## Fase 3 — novembro de 2026 (registro em `experimentos/registro.jsonl`)

| Tentativa | Resultado | Por que não funcionou / aprendizado | Fonte |
|---|---|---|---|
| LM causal só com o termo condicional log P(t_j \| t_i) nas arestas (Qwen3-8B, 12 configurações) — E003, ablação | Piorou: Δ médio de +12,2 a +95,9 quebras/página no ajuste v4/RN; seleção ficou com a regra | Hipótese (não medida): sem normalizar pela probabilidade marginal, o escore premia destinos fáceis de prever, não os corretos; por isso o escore contrastivo (− log P(t_j)) é o teste real de H3 | `resultados/ordem_lm_arestas.md` |
| Seletor aprendido por página (árvore rasa, logística, LightGBM) entre regra, LayoutReader e grafo — E005 | Nenhum supera o híbrido 67 com IC95 < 0 (melhor: logística −2,29 [−4,96; +1,64]) | 160 páginas e 27 veículos são pouco para aprender o roteamento; a regra de densidade (1 feature) generaliza melhor | `resultados/e005_seletor/RELATORIO.md` |
| Grafo de arestas LightGBM (E004) e costura das cadeias pela regra (E014, E015) | Menos quebras que o híbrido nas externas (silver −2,28, IC<0), mas τ cai 0,018 no golden_v3_novo; NÃO GO nos três cartões | Acerta as ligações locais e erra a ordem global nas páginas densas; ordenar cadeias pela regra não recupera o τ fora do golden_v4 | `resultados/e015_mediana/RELATORIO.md` |
| Correção residual local guiada pelo modelo de arestas, a partir do híbrido 67 (E006) | Menos quebras que o híbrido e a reordenação nas externas, mas τ cai 0,020 no golden_v3_novo e as regressões passam de 1/3 dos reparos; NÃO GO | O modelo de arestas propõe trocas que desfazem sucessões certas; o ganho local não é confiável o bastante | `resultados/e006_residual/RELATORIO.md` |

## Em aberto (não é fracasso ainda)

| Tentativa | Estado |
|---|---|
| **Híbrido por densidade: LayoutReader nas páginas com até 67 unidades, regra nas densas** | **Melhor resultado já medido:** 5,14 \| 7,89 \| 26,43; Δ −0,91 \| −1,33 \| −1,02 com IC95 por veículo abaixo de zero nas três bancadas (`resultados/hibrido_regra_layoutreader.md`). Limiar escolhido no golden_v4; precisa de teste cego |
| Reordenação restrita dentro da coluna | Melhora nas três bancadas (5,18 \| 7,78 \| 26,45), mas IC por veículo inclui zero; precisa de teste cego |
| Arestas pontuadas por LM causal (Qwen3-8B, arXiv 2607.01018) | Job 1053 na Spark cancelado após 1h18 com ~95% dos pares pontuados; falta a validação RN |
| DocLayout-YOLO no Kaggle (detector alternativo) | Falhou duas vezes por wandb; notebook corrigido, não rodado de novo |

## Infraestrutura (erros que custaram tempo)

| Problema | Lição | Fonte |
|---|---|---|
| Regra "sem comandos" aplicada também ao Codex | Instruções por agente; o Codex precisa executar o que escreve | `docs/RELATORIO_NOITE_0410.md` §8.7 |
| Treinador recusa retomar após mudança de código | Trava de integridade é intencional; arquivar a pasta e relançar | idem |
| Pacote `zstandard` x86 do `~/.local` quebrando o torch nos nós ARM da Spark | Sempre `PYTHONNOUSERSITE=1` nos jobs | `cluster/job_pontuar.sh` |
| Job 1053 cancelado na partição `hpc-spark-45-ephem` após 1h18 (causa não confirmada; suspeita de preempção) | Preferir a partição principal e manter a retomada por página | job 1053 |
| wandb do DocLayout-YOLO valida o nome do projeto antes de checar se está desligado | Desligar pelas SETTINGS e usar nome relativo | `notebooks/kaggle_detector_ls.ipynb` |
