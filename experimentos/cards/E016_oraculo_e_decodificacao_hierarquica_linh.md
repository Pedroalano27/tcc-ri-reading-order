# E016 — Oraculo e decodificacao hierarquica: linhas dentro de segmentos, segmentos ordenados globalmente

- **Frente:** ordenacao
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

Ordenar em dois níveis (linhas pelo grafo E004 dentro de segmentos estruturais; segmentos ordenados globalmente) mantém ≥ 70% da redução de quebras do E004 e recupera o τ: limite inferior do IC95 de Δτ vs híbrido 67 ≥ −0,005 no ajuste e nas externas.

## Por que pode funcionar aqui

E004/E014/E015/E006: o grafo acerta sucessões locais e erra a costura global; diagnóstico de τ (03/11): a perda vem de páginas densas de 3 colunas onde trechos certos são costurados na ordem errada. E009: linhas deslocam os erros para entre unidades. ChatGPT, consulta 03 (`experimentos/consultas/2026-11-03_chatgpt_03_resposta.md`): P0 = decodificação hierárquica; parar se nem o oráculo hierárquico atingir o critério.

## Método

- Entrada / representação: linhas + átomos ls3; segmentos = partição da página por fronteiras geométricas/estruturais confiáveis (colunas, faixas transversais, margens, tabelas), menores que a coluna inteira quando houver título transversal.
- Dados de treino (versão, `registro.py dados`): fase 1 (oráculo, HIER-1) sem treino novo; HIER-2 treina o par-a-par de segmentos no silver (e, depois, no humano convertido — E012).
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local.

## Critério de sucesso (decidido antes de rodar)

Fase 1 (portão, só ajuste v4 + RN): o ORÁCULO hierárquico (ordem interna e ordem dos segmentos perfeitas dadas as restrições) tem τ ≥ τ do híbrido − 0,005 e quebras ≤ 30% acima do teto plano (1,05 no v4); e HIER-1 (sem oráculo) mantém ≥ 70% da redução de quebras do E004 no ajuste com limite inferior do IC95 de Δτ vs híbrido ≥ −0,005. Fase 2 (externas, uma vez, com a variante congelada): limite superior do IC95 de Δquebras vs híbrido < 0 em pelo menos uma externa e ≤ 0 na média da outra; limite inferior do IC95 de Δτ vs híbrido ≥ −0,005 nas duas.

## Critério de abandono

Se o oráculo hierárquico não passar o portão da fase 1, encerrar a linha do grafo (resultado exploratório) e investir no fallback e na análise de falhas (marco do dia 8 da consulta 03).

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 04:39, local (CPU), Codex, `orquestracao/analises/e016_hierarquico.py`, só ajuste.
  Segmentos: 7,5/página no v4 (94,3% dos sucessores-ouro ficam dentro de um segmento; 35 de 332 segmentos
  "violados" pelo ouro). Quebras / τ:

| Método | golden_v4 | validação RN |
|---|---:|---:|
| regra | 6,045 / 0,9859 | 16,667 / 0,9572 |
| híbrido 67 | 5,136 / 0,9797 | 16,400 / 0,9587 |
| grafo E004 | 3,614 / 0,9380 | 9,467 / 0,6867 |
| oráculo hierárquico (τ máximo) | 2,795 / 0,9935 | 8,067 / 0,9805 |
| oráculo: interna perfeita + segmentos pela regra | 3,250 / 0,9874 | 8,667 / 0,9580 |
| oráculo: interna pelo grafo + segmentos perfeitos | 4,250 / 0,9916 | 11,533 / 0,9793 |
| **HIER-1** (grafo dentro, regra entre segmentos) | **4,659 / 0,9854** | 12,133 / 0,9568 |

  Portão: oráculo τ ✔; oráculo quebras ✘ (2,80 > 1,36); HIER-1 retenção ✘ (61% < 70%);
  HIER-1 IC de Δτ ✘ (limite inferior −0,0063 < −0,005). **NÃO GO da fase 1.**
  Fonte: `resultados/e016_hierarquico/resumo_registro.json`, `RELATORIO.md`.

## Conclusão e aprendizado

1. **Erro meu no desenho do portão:** comparei o oráculo hierárquico com o teto *plano* (1,05), que
   ignora qualquer restrição; restringir a ordem a segmentos custa quebras por construção (o ouro
   "viola" 35 segmentos). O limiar de 30% era apertado demais. Fica registrado; o veredito não muda.
2. Mesmo reprovado, o HIER-1 é o primeiro método com menos quebras **e** τ não pior que o híbrido no
   golden_v4 (4,66 / 0,985 × 5,14 / 0,980). No RN fica entre a regra e o grafo.
3. O nível que mais limita é o **interno** (grafo dentro dos segmentos: 4,25 com segmentos perfeitos)
   — não a ordem dos segmentos (3,25 com interna perfeita e segmentos pela regra).
4. Qualquer continuação (ex.: congelar o HIER-1 e testá-lo nas externas) é **hipótese nova, motivada por
   este resultado**, e precisa de cartão próprio com critério antes de rodar — decisão do Pedro.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
