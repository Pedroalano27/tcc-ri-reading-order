# E006 — Correcao residual local guiada pelo modelo de arestas do E004

- **Frente:** ordenacao
- **Hipótese do backlog:** H2 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

Partindo da ordem do híbrido 67 e aplicando só operações locais de baixo risco (troca de vizinhas, mover bloco curto de 1–4 linhas dentro da mesma coluna, reinserir linha de margem/cabeçalho/rodapé), aceitas quando o ganho de log-verossimilhança das arestas do modelo E004 passa de um limiar, reduz as quebras em relação à reordenação restrita atual sem perder τ.

## Por que pode funcionar aqui

E002: teto do residual 6,05 → 1,91 quebras/página no golden_v4 com τ 0,990 (o τ não cai porque as operações são locais). E004/E015: o modelo de arestas acerta a sucessão local (quebras caem) mas a costura global perde τ — usar o modelo só para decisões locais aproveita o que ele faz bem. A reordenação restrita atual (sem modelo) tem Δ −0,86 vs regra no v4.

## Método

- Entrada / representação: linhas + átomos ls3; ordem inicial = híbrido 67; escores calibrados do E004 (sem retreinar).
- Dados de treino (versão, `registro.py dados`): nenhum novo; limiar de ganho escolhido só no ajuste.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): CPU local, < 2 h.

## Critério de sucesso (decidido antes de rodar)

(1) Menos quebras que a reordenação restrita atual (regra_reordena) no golden_v4 E no golden_v3_novo; (2) Δ quebras vs híbrido 67 ≤ 0 em golden_v3_novo e teste silver, com IC95 por veículo < 0 em pelo menos uma; (3) τ ≥ τ do híbrido 67 − 0,005 nas três bancadas; (4) sucessores-ouro perdidos (regressões) ≤ 1/3 dos recuperados (reparos) nas externas.

## Critério de abandono

Falhar (1) ou (2): a correção local não compensa; o híbrido 67 é o método final e o capítulo de resultados fecha com ele + os negativos.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 01:32 (Codex) + 02:07 (complemento de 2 predições LayoutReader do RN em CPU): λ = 2,0 e
  M = 20 escolhidos no ajuste. Quebras / τ: golden_v4 4,432 / 0,978 (híbrido 5,136 / 0,980);
  golden_v3_novo 7,074 / 0,939 (híbrido 7,889 / 0,959; reordena 7,778); teste silver 24,888 / 0,953
  (híbrido 26,427 / 0,959). Itens 1, 2a, 2b passam; **3 (τ) e 4 (regressões ≤ 1/3 dos reparos) falham → NÃO GO.**
  Fonte: `resultados/e006_residual/RELATORIO.md`, `resumo_registro.json`.

## Conclusão e aprendizado

Mesmo restrito a operações locais, o modelo do E004 derruba o τ no golden_v3_novo (−0,020 vs híbrido).
Os quatro métodos que usam esse modelo (E004, E014, E015, E006) perdem τ justamente ali: ou o modelo
erra num tipo de página do v3_novo, ou o τ de palavras é dominado por poucas páginas (como a RN p40).
Diagnóstico pedido antes de qualquer nova tentativa.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
