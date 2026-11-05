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

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
