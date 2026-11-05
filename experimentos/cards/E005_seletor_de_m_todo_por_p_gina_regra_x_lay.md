# E005 — Seletor de método por página (regra x LayoutReader x grafo)

- **Frente:** ordenacao
- **Hipótese do backlog:** H10 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-02
- **Estado:** planejado

## Pergunta e hipótese

Um seletor por página simples (densidade, nº de colunas, proporção de margem, transversais), escolhendo entre regra, LayoutReader e o grafo do E004, tem menos quebras que o limiar fixo de 67 unidades em validação cruzada agrupada por veículo.

## Por que pode funcionar aqui

O híbrido 67 (um seletor de 1 feature) é o melhor resultado medido; o E002 mostra teto de roteamento por página de 3,59 quebras no golden_v4 (regra 6,05; híbrido 5,14), ou seja, ainda há ganho na escolha por página.

## Método

- Entrada / representação:
- Dados de treino (versão, `registro.py dados`):
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h):

## Critério de sucesso (decidido antes de rodar)

Δ quebras < 0 vs híbrido 67 na validação cruzada agrupada por veículo (todas as bancadas de desenvolvimento juntas), com IC95 por veículo abaixo de zero; nenhuma bancada pior em mais de 0,5 quebra/página.

## Critério de abandono

Não superar o limiar 67 fora da amostra: manter o limiar 67 congelado (H10 refutada).

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 02/11 23:47, local, `orquestracao/analises/e005_seletor.py` (Codex): validação cruzada deixando
  um veículo de fora (160 observações, 27 veículos), roteando entre regra, LayoutReader e grafo E004.
  Nenhum seletor supera o híbrido 67 com IC95 < 0: logística −2,29 [−4,96; +1,64]; árvore rasa +3,78;
  LightGBM +5,06 quebras/página. Fonte: `resultados/e005_seletor/RELATORIO.md`. **NÃO GO.**

## Conclusão e aprendizado

Com os dados que temos (160 páginas), aprender o roteamento não supera a regra simples de densidade;
mantém-se o limiar 67 congelado (H10 refutada nesta escala). Revisitar só se o E014 mudar os métodos roteáveis.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
