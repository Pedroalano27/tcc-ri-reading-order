# E014 — Grafo do E004 com ordenacao das cadeias pela regra (recuperar o tau)

- **Frente:** ordenacao
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

A queda de τ do grafo do E004 vem da ordem relativa das cadeias (trechos contínuos), não das arestas: ordenar as cadeias pela posição da regra (ou aceitar só trocas locais do grafo dentro da coluna da regra) recupera o τ (≥ regra − 0,005) mantendo ≥ 60% da redução de quebras do E004 no ajuste.

## Por que pode funcionar aqui

E004 (02/11): o grafo K24 max-regret reduz quebras vs regra em todas as bancadas (v4 −2,43; v3_novo −2,70, IC<0; silver −3,30, IC<0) e vs híbrido no silver (−2,28, IC<0), mas τ cai 0,017–0,048 e as quebras por 1.000 palavras pioram no v4 (7,78 × 6,04 do híbrido) — sinal de que acerta as ligações locais e erra a costura global. O E002 já mostrava o mesmo padrão no teto do matching (τ 0,917).

## Método

- Entrada / representação: linhas + átomos ls3; escores calibrados do modelo do E004 (sem retreinar).
- Dados de treino (versão, `registro.py dados`): nenhum novo; reusa o modelo do E004.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local, < 1 h.

## Critério de sucesso (decidido antes de rodar)

No ajuste (v4 + RN): τ médio ≥ τ da regra − 0,005 e redução de quebras ≥ 60% da do E004. Nas externas (golden_v3_novo, teste silver): Δ quebras vs híbrido 67 ≤ 0 nas duas, com IC95 por veículo < 0 em pelo menos uma, e τ ≥ regra − 0,005.

## Critério de abandono

Nenhuma variante recupera o τ sem perder mais de 40% do ganho de quebras: a costura global é o gargalo e o próximo passo é decodificação com restrição de coluna/blocos (ou GNN, E011).

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 00:32, local (CPU), Codex, `orquestracao/analises/e014_cadeias.py` (sem retreinar; pico 189 MiB).
  Diagnóstico: a perda de τ do grafo está **entre cadeias**, não dentro delas (golden_v4: Δτ entre
  −0,048, interno ≈ 0). Variantes no ajuste (quebras / τ):

| Variante | golden_v4 | validação RN |
|---|---:|---:|
| regra | 6,045 / 0,9859 | 16,667 / 0,9572 |
| grafo E004 = (a) 1ª linha | 3,614 / 0,9380 | 9,467 / 0,6867 |
| **(b) mediana da regra** | **3,568 / 0,9867** | 9,267 / 0,8910 |
| (c) corretor local | 3,727 / 0,9378 | 9,467 / 0,6906 |
| (d) local + margens | 3,841 / 0,9380 | 10,933 / 0,6903 |

  Nenhuma variante tem τ médio v4+RN ≥ regra − 0,005 → **NÃO GO / abandono pelo cartão**; externas
  não rodadas. Fonte: `resultados/e014_cadeias/resumo_registro.json`, `RELATORIO.md`.

## Conclusão e aprendizado

A hipótese de diagnóstico se confirmou (o τ se perde na costura entre cadeias) e a variante (b)
recupera o τ **no golden_v4** mantendo o ganho de quebras. A falha no RN é concentrada: uma página
(`official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40`, Δτ −0,987) sai praticamente invertida.
O RN tem um só veículo e referência silver. Isso é uma **falha catastrófica rara** a investigar, não
um padrão — segue no E015 com critério novo, decidido antes de ver as externas.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
