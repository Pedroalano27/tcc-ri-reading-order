# {ID} — {TITULO}

- **Frente:** {FRENTE}
- **Hipótese do backlog:** {HIPOTESE} (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** {DATA}
- **Estado:** planejado

## Pergunta e hipótese

<!-- Uma frase falsificável. Ex.: "Somar o escore de continuidade de um LM causal à regra de colunas reduz as quebras por página no teste silver sem piorar o golden_v3_novo." -->

## Por que pode funcionar aqui

<!-- Evidência anterior (nossa ou da literatura) que justifica gastar tempo. -->

## Método

- Entrada / representação:
- Dados de treino (versão, `registro.py dados`):
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h):

## Critério de sucesso (decidido antes de rodar)

<!-- Ex.: Δ quebras < 0 nas duas bancadas externas, IC95 por veículo do Δ abaixo de zero em pelo menos uma, sem piora de τ > 0,005. -->

## Critério de abandono

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
