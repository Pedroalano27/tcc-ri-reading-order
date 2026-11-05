# E003 — LM causal contrastivo nas arestas

- **Frente:** ordenacao
- **Hipótese do backlog:** H3 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-02
- **Estado:** planejado

## Pergunta e hipótese

H3: a continuidade linguística discrimina sucessores quando a geometria não basta. Escore contrastivo [log P(t_j|t_i) − log P(t_j)]/|t_j| (Qwen3-8B), comparado no desenho 2×2 (geometria fixa/aprendida × com/sem LM) com os mesmos candidatos e decodificador.

## Por que pode funcionar aqui

arXiv 2607.01018: 88% de arestas certas em multicoluna sem treino; ~20–40% das quebras da regra são continuação na coluna, onde hifenização e frases cortadas são sinais textuais. O LayoutLM com texto não mede continuidade.

## Método

- Entrada / representação:
- Dados de treino (versão, `registro.py dados`):
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h):

## Critério de sucesso (decidido antes de rodar)

≥ 0,5 quebra/página de ganho sobre a variante só geométrica no desenvolvimento, sem piora em golden_v3_novo.

## Critério de abandono

< 0,5 quebra/página: registrar como ablação negativa.

## Execuções

- 28/10 e 02/11, Spark (jobs 1053 + 1115, Qwen3-8B, bf16): 175 páginas pontuadas (26,4 s/página),
  decodificadas localmente → `resultados/ordem_lm_arestas.md`. **Só o termo condicional**
  log P(t_j | t_i) (ablação; o contrastivo ainda não existe). Na grade de 12 configurações, todas
  **pioram** as quebras no ajuste v4/RN (Δ médio de +12,2 a +95,9 quebras/página); a seleção
  congelou a regra. Fonte: `resultados/ordem_lm/avaliacao/Qwen_Qwen3-8B/avaliacao.json`.
- 02/11 20:33, Spark (job 1137, 16 min): termo marginal log P(t_j | BOS) para 17.610 destinos;
  decodificação **contrastiva** [log P(t_j|t_i) − log P(t_j)]/|t_j| → `resultados/e003_lm/contrastivo_8b/AVALIACAO.md`.
  Também piora todas as 12 configurações no ajuste v4/RN (Δ médio de +17,7 a +86,0 quebras/página;
  pior que a ablação condicional na melhor configuração: +17,7 × +12,2). Seleção congelou a regra.
- **Leitura:** o LM usado como *decodificador* (somado aos priors da regra com pesos 0,5–2) desmonta a
  ordem; a grade não testou pesos pequenos do LM. H3 ainda não está refutada na forma do plano
  (escore do LM como *feature* do grafo, desenho 2×2 com o E004).

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
