# E015 — Cadeias do grafo ordenadas pela mediana da regra: externas e falha catastrofica

- **Frente:** ordenacao
- **Hipótese do backlog:** H1 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

Ordenar as cadeias do grafo do E004 pela mediana da posição na regra (variante (b) do E014, congelada sem nova seleção), com uma salvaguarda contra inversão de página inteira, tem menos quebras que o híbrido 67 nas externas sem piorar o τ.

## Por que pode funcionar aqui

E014: no golden_v4 a variante (b) tem 3,568 quebras e τ 0,9867 (regra 6,045 / 0,9859; híbrido 5,136 / 0,9797). Falhou no ajuste só pela validação RN, dominada por uma página invertida inteira. As externas (golden_v3_novo, teste silver) ainda NÃO foram vistas para (b).

## Método

- Entrada / representação: linhas + átomos ls3; modelo e escores do E004 sem retreinar; variante (b) do E014 congelada.
- Dados de treino (versão, `registro.py dados`): nenhum novo.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local, < 1 h.

## Critério de sucesso (decidido antes de rodar)

Decidido em 03/11 00:50, ANTES de rodar (b) nas externas: (1) golden_v3_novo e teste silver: Δ quebras de (b) vs híbrido 67 ≤ 0 nas duas, com IC95 por veículo < 0 em pelo menos uma; (2) τ de (b) ≥ τ da regra − 0,005 nas duas; (3) nenhuma página com Δτ < −0,5 vs regra nas externas, OU, se houver, a salvaguarda (definida só pela página RN p40 e congelada antes das externas) elimina todas sem violar (1)–(2). A salvaguarda candidata: se τ entre a ordem de (b) e a da regra < 0, devolver a ordem da regra na página.

## Critério de abandono

Falhar em (1) ou (2): o grafo fica como resultado exploratório no capítulo (ganho de quebras com custo de τ) e a fase de modelos encerra com o híbrido 67 como finalista.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 01:00, local (CPU), Codex, `orquestracao/analises/e015_mediana.py`; salvaguarda congelada
  antes das externas (acionamentos no ajuste: 0). Fonte: `resultados/e015_mediana/RELATORIO.md`.
  - golden_v3_novo: quebras 6,519 (híbrido 7,889; Δ −1,370 [−2,559; +0,231]); τ 0,9417 (regra 0,9596; Δ −0,0178) → **critério 2 falha**.
  - teste silver: quebras 24,146 (híbrido 26,427; Δ −2,281 [−11,385; −0,368]); τ 0,9551 (Δ −0,0045, dentro da margem).
  - Critérios 1a, 1b e 3 passam; 2 falha. **Veredito: NÃO GO.**
  - Exploratório (após o veredito): híbrido 67 com (b) nas páginas densas — golden_v4 3,18 quebras /
    τ 0,981; golden_v3_novo 6,30 / 0,941; teste silver 23,88 / 0,955 (híbrido: 5,14/0,980; 7,89/0,959; 26,43/0,959).

## Conclusão e aprendizado

1. A página RN p40 tem duas tabelas de ~1.740 palavras cada (b6 e b3, ~50% da página cada); o grafo
   coloca b6 depois de b3 e o τ de palavras da página cai para 0,013, com as quebras iguais às da regra.
   É uma falha real de ordem global (trocar dois trechos certos por dentro), amplificada pelo peso
   que o τ de palavras dá a trechos grandes. *(Corrigido em 03/11 03:15: antes eu tinha escrito
   "decidir se um átomo vem antes ou depois de 6 linhas curtas", o que estava errado — ver
   `resultados/diagnostico_tau_v3/RELATORIO.md`, seção "RN p40: contraprova".)*
2. A perda de τ no golden_v3_novo **persiste** com a mediana e com a combinação com o híbrido: ela
   vem das páginas densas e não é resolvida ordenando cadeias. A linha do grafo fica como **resultado
   exploratório**: menos quebras (sucessão local melhor) ao custo de τ (ordem global pior).
3. Pelo critério de abandono deste cartão, o híbrido 67 segue como finalista; restam no plano a
   correção residual (E006) e a representação (E009).

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
