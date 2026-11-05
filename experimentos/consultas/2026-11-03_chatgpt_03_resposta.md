# Consulta 03 ao ChatGPT — resposta (resumo fiel)

Conversa: https://chatgpt.com/c/6ae8d81e-3ce0-83e9-a114-20b580d695e7 (03/11, ~04:05; "pensou por 1m 54s").
Pergunta: `2026-11-03_chatgpt_03_pergunta.md`. Resumo escrito pelo orquestrador; os números citados são os
que nós enviamos, não novos.

## Diagnóstico
O gargalo deixou de ser a classificação das sucessões locais e passou a ser a **montagem global das cadeias**.
O E014 (3,57 quebras / τ 0,987 no v4) é a evidência mais importante. Próximas duas semanas: **decodificação
hierárquica + supervisão humana por regiões**, com o híbrido 67 como baseline obrigatório.

## 1. Prioridades
- **P0 (b)** decodificação hierárquica com restrições: página → segmentos estruturais (colunas, faixas
  transversais, margens, tabelas, fronteiras de ato; segmentos menores que a coluna inteira); nível 1 =
  grafo E004 dentro de segmentos seguros; nível 2 = ordem global dos segmentos; fallback para o híbrido 67.
  - HIER-1: E004 dentro dos segmentos, regra ordena os segmentos.
  - HIER-2: E004 dentro; LightGBM par-a-par entre segmentos sob um DAG de precedências.
  - HIER-3: HIER-2 + fallback conservador para o híbrido quando inverter segmento protegido ou houver conflito.
  - Não transformar sucessão geométrica em restrição rígida sem medir a precisão das arestas protegidas.
  - Hipótese: mantém ≥ 70% da redução de quebras do E004 e recupera τ dentro da margem 0,005. Se nem o
    **oráculo hierárquico** atingir isso, parar.
- **P0 (e)** gerador de candidatos entre blocos + proteção contra inversões (recall de 69% em fim de coluna).
- **P1 (a)** treinar com a Data Policy (não resolve sozinho um decodificador inadequado).
- **P2 (d)** LM como feature de aresta (ablação barata, escores já existem).
- **P3 (c)** GNN/transformer relacional — sem evidência de falta de capacidade.

## 2. Margem de τ
Manter 0,005 (conservadora e fixada antes). Δτ −0,017 ≈ 0,85 p.p. de pares de palavras invertidos, que em
páginas grandes são milhares de relações; para RAG, inverter trechos longos pode ser pior que algumas quebras
locais (o impacto real depende do chunking). Regra a pré-registrar para variantes **novas** (hierárquicas),
antes do teste cego — **desfecho co-primário por interseção**, não escore composto:
1. Segurança: limite inferior do IC95 pareado de Δτ vs híbrido 67 ≥ −0,005 (senão, falha).
2. Superioridade: limite superior do IC95 de Δquebras < 0 (senão, ganho não confirmado).
3. Robustez: Δ por UF, regressões graves, distribuição de deslocamentos (obrigatório, não muda 1–2).
Bootstrap agrupado por PDF e estratificado por UF. Os NÃO GO existentes continuam NÃO GO. Avaliação de RAG
(chunks fixos, mistura de atos) só exploratória.

## 3. Conversão da Data Policy (caixa → linha)
Conversor que preserva incerteza: alinhar palavras às caixas (cobertura de palavras; IoU só auxiliar);
classificar caixas (simples de 1 coluna, multicoluna, tabela, figura, ruído, ambígua/sobreposta); expandir
linhas dentro da caixa só quando houver uma sequência geometricamente verificável; transferir
continue/new_doc/end/skip_noise para o nível de regiões e gerar sucessores de linha só quando início e fim
das regiões forem inequívocos; **mascarar relações ambíguas na perda** (não fabricar rótulos); guardar
trilha de auditoria. Armadilhas: caixas que atravessam colunas, palavras em duas caixas, tabelas com ordem
própria, linhas cortadas, ruído intercalado, regiões com vários atos, "continue" que não é sucessão imediata.
Auditoria manual estratificada de 25–30 páginas (cobertura, % convertido sem ambiguidade, erro amostrado).
Fatorial 2×2: {silver, humano} × {decodificador plano, hierárquico}. Se a conversão cobrir pouco, treinar
só o classificador **entre regiões** com rótulos humanos e reusar o E004 dentro.

## 4. E009
Elimina a hipótese de que linhas, sozinhas, melhoram a ordem total; favorece a representação hierárquica
(linhas como elementos, segmentos protegidos como unidades globais). Não voltar às caixas como representação
universal. Em H6–H9, separar tempo, cobertura, erros internos e externos; H8 como não inferioridade da ordem
final. A anotação simplificada pode vencer por custo e reprodutibilidade mesmo sem melhorar quebras.

## 5. Plano de 14 dias
D1–2 oráculo hierárquico (segmentar, cobertura das transições entre blocos, restrições, teto em v4/v3) ·
D3–5 conversão Data Policy + auditoria · D6–8 HIER-1/2 e 2×2 silver × humano · D9–11 HIER-3 + fallback,
por página/veículo e τ nas densas · D12–14 congelar uma variante, registrar protocolo, seeds, hashes.
**Marco no dia 8:** se a hierarquia não recuperar o τ nas densas do v3, parar com classificadores novos e
focar no fallback e na análise de falhas.

## O que NÃO fazer
GNN/transformer relacional nestas 2 semanas; LM causal como decodificador de novo; usar o teste cego para
escolher qualquer coisa; transformar relações ambíguas em rótulos de linha; relaxar a margem 0,005 para
aprovar E004/E014/E015.
