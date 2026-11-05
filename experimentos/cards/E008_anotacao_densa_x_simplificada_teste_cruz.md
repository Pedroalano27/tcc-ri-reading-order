# E008 — Anotacao densa x simplificada (teste cruzado com cronometro)

- **Frente:** anotacao
- **Hipótese do backlog:** H6 (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-03
- **Estado:** planejado

## Pergunta e hipótese

Anotar sobre linhas automáticas (modo B, só tabelas/figuras/quadros/ruído e a ordem) custa ≥ 25% menos tempo mediano que a anotação densa (modo A), com ≥ 30% menos erros de segmentação, ordem não inferior (margem 0,5 quebra) e cobertura de palavras igual (H6–H9).

## Por que pode funcionar aqui

A troca de caixas de parágrafo por linhas levou os erros internos às caixas de 213 para 29 quebras (`docs/RELATORIO_NOITE_0410.md`); a anotação densa no Label Studio é o gargalo relatado pelo Pedro.

## Método

- Entrada / representação: lote de 36 páginas (`resultados/e008_anotacao/lote/`, semente 20261104), blocos de 18 em A→B e B→A.
- Dados de treino (versão, `registro.py dados`): não se aplica.
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h): `resultados/e008_anotacao/ferramenta/anotador.html` no navegador; 2 sessões do Pedro com ≥ 7 dias de intervalo.

## Critério de sucesso (decidido antes de rodar)

H6: tempo ativo mediano por página do modo B ≤ 75% do modo A (1ª sessão, comparação entre blocos). H7: erros de união/divisão ≥ 30% menores. H8: quebras da ordem anotada no modo B ≤ modo A + 0,5. H9: cobertura de palavras do modo B = 100%.

## Critério de abandono

Se H6 falhar (ganho de tempo < 25%) ou H8 falhar, manter a anotação densa no plano de dados.

<!-- Ex.: oráculo < 20% de redução; ou piora nas duas externas; ou 2 tentativas sem ganho. -->

## Execuções

- 03/11 00:13, Codex: lote montado — 36 páginas, 6/6/6 de 1/2/3+ colunas por bloco, 15 com tabela;
  sobreposição 0 com PDFs tocados e com o E001. Carga no `anotador.html` validada executando o
  JavaScript do leitor em Node (ensaio headless não rodou: `spawn EPERM`). Aguarda a 1ª sessão do Pedro.

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
