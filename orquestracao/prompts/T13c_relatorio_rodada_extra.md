## Contexto

Você escreveu `docs/RELATORIO_NOITE_V3.md`. Depois dele, `orquestracao/noite_v3_extra.sh` rodou uma
rodada extra: os passos `layoutlm_sem_layout_*`, `sucessor_seed{1,2}_*`, `pontual_seed{1,2}_*`,
`golden_v3_extra` e `comparar_extra` em `orquestracao/logs/noite_v3/status.jsonl`. As sementes 1 e 2
repetem o treino das duas formulações do LayoutLM no maior treino (3.189 páginas); a semente 42 é a do
roteiro principal, com os métodos `layoutlm` e `layoutlm_sucessor`.

## Tarefa

**Acrescente** ao fim de `docs/RELATORIO_NOITE_V3.md` uma seção `## 9. Rodada extra: sementes e
ablações no Golden`. Não altere as seções que já existem, não altere nenhum outro arquivo e não use GPU.

Conteúdo:
1. Status dos passos da rodada extra (tabela, como na seção 1).
2. **Teste, 89 páginas** (`resultados/comparacao.json`): para cada formulação, τ, sucessor correto e
   ARD normalizado das três sementes (42, 1, 2), mais média e desvio-padrão amostral das três.
3. **Golden, 47 páginas** (`resultados/golden/_avaliacao/golden_v3/avaliacao.json`, campo `geral`):
   o mesmo para as três sementes de cada formulação, e a linha do XY-cut para referência.
4. **Ablações no Golden:** `layoutlm_sem_layout`, `ablacao_suc_sem_vies_geo`,
   `ablacao_suc_sem_posicao` e `ablacao_suc_sem_layout`, com τ, sucessor correto e ARD normalizado,
   ao lado dos modelos completos (semente 42).
5. Uma frase de leitura: a diferença de τ entre as formulações e o XY-cut no Golden é maior ou menor que
   o desvio-padrão entre sementes? Só constatar, sem conclusão metodológica.

Mesmas regras: todo número vem dos arquivos, com o caminho citado; média e desvio calculados em Python,
com o comando registrado na seção; se um passo falhou ou um método não está no arquivo, diga isso no
lugar do número.

## Resposta final

Em FEITO: a tabela do item 3 e a frase do item 5.
