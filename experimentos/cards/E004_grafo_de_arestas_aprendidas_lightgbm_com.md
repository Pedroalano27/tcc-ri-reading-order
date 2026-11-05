# E004 — Grafo de arestas aprendidas (LightGBM) com decodificação global

- **Frente:** ordenacao
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-02
- **Estado:** planejado

## Pergunta e hipótese

Um classificador de arestas (LightGBM) sobre candidatos K ≤ 32, decodificado globalmente, tem ≥ 10% menos quebras/página que a regra no ajuste (golden_v4 + RN) e não perde para o híbrido 67 nas bancadas externas, sem piorar o τ em mais de 0,005.

## Por que pode funcionar aqui

E002: com escores perfeitos o matching K32 reduz 6,05 → 1,05 quebras/página no golden_v4 (teto de 67,5% no ajuste); recall de candidatos 99,97% na continuação de coluna. Metade das quebras da regra é cabeçalho/rodapé/marca. Literatura: grafos de relação + decodificação global (arXiv 2607.01018; FocalOrder 2601.07483). O sucessor do LayoutLM (escores independentes, decodificação em cadeia) não superou a regra.

## Método

- Entrada / representação: linhas + átomos ls3 congelados; candidatos do E002 (nível 3 da regra + top-K euclidiano, K ∈ {12, 24, 32}) + candidatos extras de "topo da próxima coluna".
- Dados de treino (versão, `registro.py dados`): silver de treino `resultados/unidades_sem_caixas/treino_noite.json` (3.140 páginas, hash 46fc38bc27bb40d4); níveis de confiança por transição se disponíveis.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local (LightGBM), 0 GPU-h; varreduras grandes podem ir à Spark.

## Critério de sucesso (decidido antes de rodar)

≥ 10% menos quebras/página que a regra na média golden_v4 + RN (seleção congelada só no ajuste); nas externas (golden_v3_novo, teste silver) Δ quebras vs híbrido 67 ≤ 0 em ambas, sem piora de τ > 0,005 vs regra.

## Critério de abandono

Menos de 10% de ganho sobre a regra no ajuste com os três decodificadores: registrar em NAO_FUNCIONOU e passar ao E006 (residual) e ao E005 (seletor).

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 02/11 23:44, local (CPU), Codex (tarefas 04 + 05b): treino LightGBM em 3.140 páginas silver com
  negativos amostrados (positivos + rank ≤ 4 + fração fixa dos demais), seleção no ajuste:
  `grafo_K24_maxregret_t0.00`. Fonte: `resultados/e004_grafo/RELATORIO.md`, `resumo_registro.json`.

| Bancada | Regra (τ / quebras) | Híbrido 67 | Grafo K24 max-regret |
|---|---:|---:|---:|
| golden_v4 (ajuste) | 0,986 / 6,05 | 0,980 / 5,14 | 0,938 / 3,61 |
| golden_v3_novo | 0,960 / 9,22 | 0,959 / 7,89 | 0,942 / 6,52 |
| teste silver | 0,960 / 27,45 | 0,959 / 26,43 | 0,943 / 24,15 |

Δ quebras vs híbrido: v4 −1,52 [−3,50; −0,07]; v3_novo −1,37 [−2,56; +0,23]; silver −2,28 [−11,31; −0,34].
Critérios: redução ≥ 10% no ajuste ✔ (42,4%); quebras ≤ híbrido nas externas ✔; **τ ✘** (cai 0,017 no
v3_novo e no silver). **Veredito pelo cartão: NÃO GO.**

## Conclusão e aprendizado

O grafo aprendido é o **primeiro método que reduz as quebras abaixo do híbrido nas duas externas**,
mas paga em τ: acerta as ligações locais e erra a costura entre trechos. Como o critério foi decidido
antes, o E004 não passa; a hipótese de diagnóstico (a perda está na ordem das cadeias) vira o E014.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
