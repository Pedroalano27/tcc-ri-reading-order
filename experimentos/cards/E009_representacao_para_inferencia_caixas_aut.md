# E009 — Representacao para inferencia: caixas automaticas x linhas automaticas

- **Frente:** anotacao
- **Hipótese do backlog:** H8 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

Com os mesmos documentos, a mesma referência e o mesmo ordenador (regra e híbrido 67), representar a página por linhas automáticas + átomos ls3 tem menos quebras que representá-la por caixas automáticas de parágrafo (detector), com cobertura de palavras igual (controlada por IDs de palavra).

## Por que pode funcionar aqui

Histórico de 04/10: com caixas de parágrafo, 213 quebras ficavam dentro das caixas; com linhas, 29 (`docs/RELATORIO_NOITE_0410.md`). Nunca foi formalizado com cobertura controlada e IC; é a base metodológica da anotação simplificada (E008, H8/H9).

## Método

- Entrada / representação: (A) caixas automáticas do detector usado nas noites de outubro; (B) linhas + átomos ls3; mesma página, mesmas palavras.
- Dados de treino (versão, `registro.py dados`): nenhum.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local; reusa caches de detecção existentes (sem rodar detector na GPU, salvo se faltar).

## Critério de sucesso (decidido antes de rodar)

B − A em quebras/página < 0 com IC95 por veículo < 0 em golden_v4 e golden_v3_novo, com a regra e com o híbrido 67; cobertura de palavras de B ≥ A. Decomposição: quebras dentro de unidade × entre unidades.

## Critério de abandono

Não há abandono: é medição de base. Se B não for melhor, a anotação simplificada (E008) perde a justificativa de qualidade e isso vai para o texto.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 03:27, local (CPU), Codex, `orquestracao/analises/e009_representacao.py`; cobertura 100% nas
  duas representações. Fonte: `resultados/e009_representacao/RELATORIO.md`.

| Bancada / ordenador | A caixas: total (dentro + entre) | B linhas: total (dentro + entre) |
|---|---:|---:|
| golden_v4 / regra | 5,48 (1,59 + 3,89) | 6,05 (0,55 + 5,50) |
| golden_v4 / híbrido 67 | 4,75 (1,59 + 3,16) | 5,14 (0,55 + 4,59) |
| golden_v3_novo / regra | 11,00 (5,30 + 5,70) | 9,22 (0,26 + 8,96) |
| golden_v3_novo / híbrido 67 | 8,96 (5,30 + 3,67) | 7,89 (0,26 + 7,63) |

  Δ B − A (quebras/página): regra v4 +0,57 [−2,93; +3,21], v3_novo −1,78 [−3,64; +0,72];
  híbrido v4 +0,39 [−3,29; +3,27], v3_novo −1,07 [−3,95; +1,77]. **Critério não atingido.**

## Conclusão e aprendizado

**Resultado metodológico importante e que corrige uma leitura antiga.** O número "213 → 29" (04/10)
se confirma, mas só para as quebras *dentro* das unidades (213 → 31 na régua atual). Linhas eliminam
esse erro, porém criam mais unidades para ordenar, e os erros *entre* unidades sobem na mesma
proporção: o total por página não muda de forma significativa. Ou seja, a representação em linhas
**desloca** o problema da segmentação para a ordenação — o que justifica o foco do TCC em ordenar
melhor, e enfraquece o argumento de qualidade da anotação simplificada (H8 precisa ser medida no E008,
não presumida).

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
