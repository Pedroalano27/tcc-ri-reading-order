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

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
