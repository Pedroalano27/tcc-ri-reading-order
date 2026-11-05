# E012 — Dados da Data Policy: bancada humana extra (126 paginas, 29 veiculos) e supervisao entre regioes

- **Frente:** dataset
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

(a) As anotações de ordem da Data Policy (seed 2, 126 páginas com cadeia válida, 29 veículos) servem como bancada humana adicional com a régua de palavras; (b) rótulos humanos entre regiões treinam um classificador par-a-par de segmentos melhor que o silver (2×2 da consulta 03).

## Por que pode funcionar aqui

`resultados/ordem_sem_bbox_validacao_ls.md` (out/2026) já construiu a referência por palavras (regiões na ordem humana, linhas dentro da região de cima para baixo) para 126 páginas. Viés conhecido: 62/125 páginas aceitaram a pré-anotação XY-cut sem mudança (`resultados/ordem_ls_baselines.md`) — a bancada favorece ordens parecidas com a regra; reportar sempre o estrato "páginas modificadas pelo anotador".

## Método

- Entrada / representação: export `data/labelstudio/ls_p23_seed2_order.json` (relações continue/skip_noise/new_doc/end por caixa) + palavras do PDF; linhas + átomos ls3 como nas outras bancadas.
- Dados de treino (versão, `registro.py dados`): (b) relações entre regiões convertidas com máscara para as ambíguas; split por PDF.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local (Claude apenas — dados da Data Policy NÃO vão para Codex/Antigravity/Gemini); LayoutReader nas páginas leves pode usar a GPU local.

## Critério de sucesso (decidido antes de rodar)

(a) Conversão auditada: em 25–30 páginas estratificadas, ≥ 95% das palavras cobertas e ≥ 80% das relações entre regiões convertidas sem ambiguidade; a âncora da regra reproduz o τ da validação de outubro. (b) definido depois de (a), antes de treinar.

## Critério de abandono

Ambiguidade > 20% das relações na auditoria: usar a Data Policy só como bancada de avaliação por regiões, sem treinar.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 05/11 ~00:30, local (CPU), Claude, `orquestracao/analises/e012_bancada_ls.py` (dados da Data Policy;
  por página em `resultados/ordem_ls/e012/`, fora do git). Export de outubro da seed 2: 123 páginas com
  cadeia humana válida e palavras, 29 veículos (3 páginas vazias descartadas). Mesma régua das outras
  bancadas; IC95 por bootstrap de veículos (5.000). Fonte: `resultados/e012_ls/RELATORIO.md`.

| Método | Quebras/pág | τ | Δ quebras vs híbrido [IC95] | Δ τ vs híbrido [IC95] |
|---|---:|---:|---:|---:|
| regra | 8,577 | 0,9538 | +1,398 [+0,326; +2,485] | −0,0157 [−0,0455; +0,0028] |
| **híbrido 67** | **7,179** | **0,9695** | — | — |
| grafo E004 | 6,675 | 0,9090 | −0,504 [−2,103; +0,625] | −0,0605 [−0,1202; −0,0191] |
| HIER-1 | 6,976 | 0,9561 | −0,203 [−1,717; +0,992] | −0,0134 [−0,0432; +0,0049] |

  Sem as 15 páginas com cópia comprovada da pré-anotação (108 págs, 28 veículos): mesmo padrão
  (regra +1,43 [+0,35; +2,57]; grafo −0,46 com τ −0,069 [IC < 0]; HIER-1 −0,13 [−1,77; +1,20]).
- 04/11 23:58, a sessão "Anotar layout de diários" reexportou as seeds de ordem: seed 2 com 740
  cadeias válidas e seed 1 (projeto 31) com 529. As páginas do usuário 13 são em boa parte
  pré-anotações sem revisão e devem ser excluídas (`data/labelstudio/MANIFESTO_ORDEM_20261104.md`).

## Conclusão e aprendizado

1. **O híbrido 67 se confirma em dado humano independente** (29 veículos, nenhum usado para escolher
   o limiar 67): a regra fica 1,40 quebra/página pior, com IC95 inteiro acima de zero.
2. **O padrão do grafo se repete:** menos quebras, τ significativamente menor (−0,06).
3. **O HIER-1 não supera o híbrido** nesta bancada: ganho de quebras pequeno e incerto, τ um pouco menor.
4. Com as exportações novas (seed 2: 283 + 236 + 65 revisadas; seed 1: 200 + 200 + 10 — cerca de 990 páginas após excluir as pré-anotações sem revisão), esta
   bancada pode crescer ~9×; falta extrair palavras e detecções dessas páginas (PDFs).

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
