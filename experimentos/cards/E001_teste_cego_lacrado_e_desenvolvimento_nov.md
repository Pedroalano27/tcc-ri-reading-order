# E001 — Teste cego lacrado e desenvolvimento novo

- **Frente:** dataset
- **Hipótese do backlog:** H-central (ver [HIPOTESES.md](../HIPOTESES.md))
- **Aberto em:** 2026-11-02
- **Estado:** planejado

## Pergunta e hipótese

Montar um teste humano que nunca influenciou nenhuma escolha: 90 páginas de PDFs nunca tocados por nenhum conjunto (bancadas, Diamond, massa1, treino silver, lote_sem_paragrafos), 30 de CE, 30 de MA e 30 de RJ, ~15 PDFs por UF, no máximo 2 páginas por PDF, estratificadas por número de colunas e presença de tabela. Também 45 páginas novas de desenvolvimento (veículos de treino + RN). O lote_sem_paragrafos (60) NÃO serve como teste cego: todos os 57 PDFs dele já estão em outros conjuntos e 23 páginas estão nos dados exportados (verificado em 02/11).

## Por que pode funcionar aqui

Todo número humano atual vem de páginas já consultadas (golden_v4 ajustou a regra; golden_v3_novo foi consultado). Sem teste cego não há conclusão confirmatória.

## Método

- Entrada / representação:
- Dados de treino (versão, `registro.py dados`):
- Ajuste (onde se escolhem hiperparâmetros): golden_v4 + validação RN, salvo indicação.
- Avaliação: golden_v3_novo e teste silver (externos); teste cego quando existir.
- Controles obrigatórios: âncora da regra (golden_v4 τ 0,985948 / 6,045455 quebras) e baseline mais forte.
- Ambiente e custo estimado (GPU-h):

## Critério de sucesso (decidido antes de rodar)

Lista congelada em experimentos/TESTE_CEGO.lock (page_id, sha256 do PDF, semente de sorteio), verificação automática de não sobreposição por PDF com todos os conjuntos, tarefas geradas no formato da ferramenta de anotação (ordem NÃO pré-preenchida no teste cego).

## Critério de abandono

—

## Execuções

- 02/11 19:25, local, `orquestracao/analises/e001_montar_teste_cego.py` (Codex, 64 min) →
  `resultados/e001_teste_cego/RELATORIO.md`. **135 tarefas**: teste cego 90 (CE 30 páginas/15 PDFs,
  MA 30/15, RJ 30/16; semente 20261102) e desenvolvimento 45 (9 veículos; semente 20261103).
  Sobreposição com PDFs já tocados (1.085 PDFs referenciados no repositório): **0** por caminho e
  por sha256; teste × desenvolvimento: 0. Âncora reproduzida. Lacre: `experimentos/TESTE_CEGO.lock`.
- Copiado (sem sobrescrever) para `data/diamond/e001_teste_cego` e `data/diamond/e001_desenvolvimento`
  para anotação na ferramenta Diamond.
- **Limitação registrada:** o estrato do CE saiu quase todo de 1 coluna (29 de 30 páginas), porque
  é o que o acervo do CE tem; BA e PA no desenvolvimento só têm 2 páginas cada (acervo esgotado).

## Conclusão e aprendizado

O acervo dos veículos de desenvolvimento antigos está quase esgotado (ex.: PA 166 de 167 PDFs já
tocados): novos dados de desenvolvimento terão de vir de veículos ainda pouco usados (PR, RR, SC, RN).
Regra a partir daqui: nenhum agente abre `data/diamond/e001_teste_cego`; avaliação confirmatória única.

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
