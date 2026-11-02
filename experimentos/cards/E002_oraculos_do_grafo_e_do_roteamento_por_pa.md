# E002 — Oraculos do grafo e do roteamento por pagina

- **Frente:** ordenacao
- **Hipótese do backlog:** H0 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-02
- **Estado:** planejado

## Pergunta e hipótese

H0: a maior parte dos erros da regra é corrigível com os candidatos e operações disponíveis. Quanto cada família poderia ganhar, no máximo, e em que classe de erro (margem, continuação na coluna, troca de coluna, transversal)?

## Por que pode funcionar aqui

Recall dos candidatos 96–98% nas humanas; reordenação restrita já tem teto de −42% na coluna; o roteamento (híbrido) já é o melhor resultado. Falta saber o teto de cada abordagem antes de investir em treino (recomendação P0 do ChatGPT).

## Método

- Entrada / representação:
- Dados de treino (versão, `registro.py dados`):
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h):

## Critério de sucesso (decidido antes de rodar)

Tabela de tetos por bancada e por classe de erro para: (a) candidatos K=12/24/32; (b) decodificadores guloso/matching/max-regret com escores perfeitos; (c) operações residuais; (d) roteamento por página entre regra, LayoutReader, reordenação restrita, híbrido 67. Go para o grafo (E004) se o teto (b) ficar ≥ 20% abaixo da regra no desenvolvimento.

## Critério de abandono

Teto (b) < 20%: não treinar o grafo; revisar candidatos e granularidade.

## Execuções

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
