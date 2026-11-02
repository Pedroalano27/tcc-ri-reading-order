## Contexto

Você já escreveu `resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md` (script
`orquestracao/analises/diagnostico_sucessor.py`). **As predições do sucessor usadas ali estavam
erradas por um defeito de configuração, não do modelo:** `src/eval/avaliar_golden.py` chamava
`prever()` sem dizer o modo, e o padrão da função era **busca em feixe**. No teste, a linha principal
do método usa **decodificação em cadeias** (limiar 0,5), e na mesma busca em feixe o teste também cai
(τ 0,754 contra 0,878). O padrão foi corrigido e a avaliação do Golden foi refeita: o arquivo
`resultados/golden/_avaliacao/golden_v3/pred_layoutlm_sucessor.jsonl` agora é o de cadeias. Portanto,
a hipótese sobre a "decodificação em cadeias" foi tirada de predições em feixe.

## Tarefa

Rode o seu script de novo sobre as predições atuais e **reescreva**
`resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md`. Mantenha a mesma estrutura e
acrescente, no topo, uma seção curta "Correção de 13/09" com:
- o τ e o sucessor correto do sucessor no Golden antes (feixe: 0,699 e 67,1%) e depois (cadeias);
- o que muda nas três hipóteses: quais se mantêm, quais caem, quais mudam.

Mesmas regras de antes: só estes dois arquivos; nada de GPU, treino ou avaliação; todo número vem do
cálculo, com o comando registrado.

## Resposta final

Em FEITO: os números novos e as hipóteses revistas.
