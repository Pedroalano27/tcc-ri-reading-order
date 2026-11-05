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

- 02/11 18:20, local (CPU), `orquestracao/analises/e002_oraculos.py` (Codex, 13 min) →
  `resultados/e002_oraculos/RELATORIO.md`, `metricas.json`. Âncora reproduzida (τ 0,985948; 6,045455).

| Bancada | Regra | Híbrido 67 | Teto grafo (matching K32) | Teto residual | Teto roteamento |
|---|---:|---:|---:|---:|---:|
| golden_v4 (quebras/pág) | 6,045 | 5,136 | 1,045 | 1,909 | 3,591 |
| golden_v3_novo | 9,222 | 7,889 | 1,259 | 2,222 | 6,000 |
| teste_silver | 27,449 | 26,427 | 19,787 | 19,966 | 21,224 |
| validação RN | 16,667 | — | 6,333 | 6,333 | — |

Fonte: `resultados/e002_oraculos/resumo_registro.json`. Critério de GO (≥ 20% no ajuste): **GO**,
redução de 67,5% na média v4 + RN (matching K32).

## Conclusão e aprendizado

1. **Há espaço para o grafo de arestas:** com escores perfeitos, o decodificador por matching
   sobre K = 32 candidatos tira cerca de 5 das 6 quebras por página no golden_v4. Vale treinar (E004).
2. **O limite está nos escores, não nos candidatos:** a continuação na mesma coluna tem recall
   de 99,97% com K 24/32. Exceção: "fim de coluna → topo da próxima" tem recall de só 69% (9/13)
   mesmo com K 32 — o E004 precisa de candidatos extras para topo de coluna.
3. **Metade das quebras da regra é cabeçalho/rodapé/marca marginal** (3,045 de 6,045 no v4):
   é onde o teto mais ganha (−2,6). Feature de "margem/repetição" é prioridade no E004.
4. O teto do matching **reduz o τ** (0,917 no v4): otimizar só arestas locais pode embaralhar a
   ordem global. O E004 precisa reportar τ junto e ter restrição de coluna no decodificador.
5. No teste silver os tetos caem pouco (27,4 → 19,8): a referência silver (fluxo do PDF) tem
   transições que nenhum candidato alcança; o silver mede mal o ganho fino.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
