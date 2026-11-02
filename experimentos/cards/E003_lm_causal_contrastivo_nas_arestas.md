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

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
