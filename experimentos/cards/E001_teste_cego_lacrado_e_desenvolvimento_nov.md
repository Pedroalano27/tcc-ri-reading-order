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

<!-- Preenchido por `src/exp/registro.py registrar`; resumo humano aqui. -->

## Conclusão e aprendizado

<!-- O que mudou no nosso entendimento. Se não funcionou, copiar para NAO_FUNCIONOU.md. -->

## Para o texto do TCC

<!-- Capítulo/seção onde entra, figura/tabela gerada, frase-resumo. -->
