# E017 — HIER-1 congelado nas externas (golden_v3_novo e teste silver)

- **Frente:** ordenacao
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-04
- **Estado:** planejado

## Pergunta e hipótese

O HIER-1 do E016 (grafo E004 dentro dos segmentos, regra entre segmentos), congelado sem nenhum ajuste, tem menos quebras que o híbrido 67 sem perder τ além da margem nas bancadas externas.

## Por que pode funcionar aqui

E016 (ajuste): HIER-1 4,659 / τ 0,9854 no golden_v4 vs híbrido 5,136 / 0,9797; RN 12,133 / 0,9568 vs 16,400 / 0,9587. **Hipótese nova, motivada por esse resultado** (o E016 foi NÃO GO pelo portão); autorizada pelo Pedro em 04/11. Externas nunca vistas para o HIER-1.

## Método

- Entrada / representação: idêntica ao E016 (código e hash congelados antes de rodar).
- Dados de treino (versão, `registro.py dados`): nenhum novo; modelo do E004.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local, < 1 h.

## Critério de sucesso (decidido antes de rodar)

Regra 3b do protocolo aprovado (04/11), contra o híbrido 67, com IC95 bootstrap por veículo: (1) segurança — limite inferior do IC de Δτ ≥ −0,005 em golden_v3_novo E em teste silver; (2) superioridade — limite superior do IC de Δquebras < 0 em pelo menos uma das duas e Δquebras médio ≤ 0 na outra. Passando, o HIER-1 é congelado como finalista do teste cego.

## Critério de abandono

Falhar (1) ou (2): HIER-1 fica como exploratório; finalistas do teste cego = híbrido 67 e regra.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 05/11 ~00:50, local (CPU), Codex, `orquestracao/analises/e017_hier1_externas.py`; código e modelo
  congelados antes das externas (`congelamento.json`); E016 reproduzido (golden_v4 4,659 / τ 0,9854).

| Bancada | Regra | Híbrido 67 | HIER-1 | Δ quebras vs híbrido [IC95] | LI do IC95 de Δτ vs híbrido |
|---|---:|---:|---:|---:|---:|
| golden_v3_novo | 9,222 / 0,9596 | 7,889 / 0,9590 | **6,667 / 0,9594** | −1,222 [−2,429; +0,611] | −0,0044 |
| teste silver | 27,449 / 0,9596 | 26,427 / 0,9591 | **25,056 / 0,9584** | −1,371 [−5,077; −0,316] | −0,0025 |

  (1) Segurança nas duas ✔; (2) superioridade no silver (IC < 0) e Δ médio ≤ 0 no v3 ✔. **GO.**
  Fonte: `resultados/e017_hier1_externas/RELATORIO.md`, `resumo_registro.json`.

## Conclusão e aprendizado

1. **Primeiro candidato que passa:** a ordenação em dois níveis mantém o τ do híbrido e reduz as
   quebras nas duas externas. O HIER-1 entra congelado como **finalista do teste cego**, ao lado do
   híbrido 67 (baseline) e da regra (âncora).
2. **Ressalva importante:** na bancada humana da Data Policy (E012, 123 págs, 29 veículos), avaliada
   em paralelo e fora deste critério, o HIER-1 **não** supera o híbrido (−0,20 [−1,72; +0,99]; LI de
   Δτ −0,043). A margem de segurança no golden_v3_novo também foi apertada (−0,0044 vs −0,005).
   O teste cego decide; a expectativa realista é de ganho pequeno.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
