# Plano de pesquisa — fase de novembro/dezembro de 2026

Escrito em 02/11/2026 pelo Claude (orquestrador), depois de recuperar o contexto do projeto
([CONTEXTO_E_RECURSOS.md](CONTEXTO_E_RECURSOS.md)) e consultar o ChatGPT como orientador
técnico ([consulta 01](../experimentos/consultas/2026-11-02_chatgpt_01_resposta.md),
[consulta 02](../experimentos/consultas/2026-11-02_chatgpt_02_hibrido.md)). O que depende
do Pedro está em [DEPENDENCIAS.md](DEPENDENCIAS.md). O registro dos experimentos fica em
[`experimentos/`](../experimentos/README.md).

**Estado:** preparação concluída; **nenhum experimento novo foi iniciado**. A fase intensiva
começa quando o Pedro resolver os itens bloqueantes de DEPENDENCIAS.md e disser "pode começar".

---

## 1. Pergunta e hipótese central

**Pergunta do TCC:** como recuperar a ordem de leitura de diários oficiais multicoluna de
forma eficaz e barata, e o que de fato reduz os erros?

**Hipótese central desta fase (H-central):** a ordem melhora quando se **especializa o método
pelo tipo de página** e se **otimiza globalmente as relações de sucessão entre linhas**, sobre
uma representação simples (linhas automáticas + átomos de tabela/figura), em vez de buscar um
modelo único de ponta a ponta.

Evidência que sustenta a escolha:
- **Híbrido por densidade:** é o único resultado com IC95 por veículo abaixo de zero nas três bancadas. Ele usa o LayoutReader nas páginas leves e a regra nas densas.
- **Reordenação restrita:** melhora as três médias.
- **Modelos únicos:** todos perderam da regra (LayoutLM, LayoutReader, BiLSTM).
- **Acessilia/Dr.DocBench:** o XY-cut só ajudou quando aplicado **seletivamente** às páginas multicoluna.
- **Literatura:** o arXiv 2607.01018 usa path cover por linhas e chega a 88% de arestas certas, contra 75% do XY-cut.

**Baseline a superar:** o **híbrido por densidade com limiar 67, congelado**. A regra de
colunas continua como controle obrigatório (âncora 0,985948 / 6,045455 no golden_v4).

## 2. As três frentes

| Frente | Pergunta | Resultado que conta |
|---|---|---|
| **A. Ordenação** (prioridade absoluta) | Que combinação de seleção por página, grafo de arestas, correção residual e sinais (geometria, texto, LM, visão) reduz as quebras fora do ajuste? | Δ quebras no teste cego, com IC por PDF |
| **B. Anotação e segmentação simplificadas** | Anotar só estruturas complexas (tabela, figura, quadro, ruído) sobre linhas automáticas é mais barato, tem menos erros e preserva a ordem? | Tempo por página, erros de segmentação, não inferioridade da ordem, cobertura |
| **C. Dados** | Que gabarito humano novo é necessário e como aproveitar silver, dados do parceiro e síntese sem contaminar a avaliação? | Teste cego lacrado + desenvolvimento ampliado + silver estratificado por confiança |

### Avaliação da ideia de anotação simplificada (frente B)

A hipótese do Pedro tem uma base sólida: trocar caixas de parágrafo por linhas já reduziu os
erros internos de caixa de 213 para 29 quebras, e a extração em linhas está perto do teto
(o extrator v2 não mudou nada). Mas ela mistura **quatro afirmações** que precisam de testes
separados:

| Hipótese | Afirmação | Critério pré-registrado |
|---|---|---|
| H6 custo | anotar sobre linhas automáticas é mais rápido | ≥ 25% menos tempo mediano por página |
| H7 qualidade | gera menos erros de segmentação | ≥ 30% menos erros de união/divisão |
| H8 ordem | não piora a ordenação | não inferior, com margem de 0,5 quebra/página |
| H9 completude | não perde conteúdo | mesma cobertura de palavras (idealmente 100%) |

- **Vantagens:**
  - menos decisões humanas por página;
  - o erro de segmentação deixa de contaminar a ordem;
  - a representação fica alinhada à tarefa (relações entre linhas);
  - a classificação fina (título, assinatura, lista) passa a ser uma etapa separada, avaliada à parte.
- **Limitações:**
  - linhas automáticas também erram: linhas que atravessam a calha, tabelas sem detecção e marcas laterais;
  - perde-se a informação de parágrafo, útil para RI e para a recuperação de atos;
  - há um único anotador, logo sem concordância entre anotadores.
- **Desenho:** dois experimentos distintos, sem misturar anotação com algoritmo.
  - **E008, protocolo de anotação:** desenho cruzado em 36 páginas de desenvolvimento, 18 na ordem A→B e 18 na ordem B→A, com 7 a 10 dias entre as sessões e o tempo registrado pela ferramenta. A comparação principal usa só a primeira sessão de cada página.
  - **E009, representação para inferência:** caixas automáticas × linhas automáticas, com os documentos, a referência e o decodificador fixos e a cobertura controlada por IDs de palavra.
- **Regra de adoção:** se a anotação simplificada reduzir ≥ 25% do tempo, mantiver a cobertura e não perder ordem além da margem, ela é adotada, mesmo sem ganho de ordenação. Isso já é um resultado metodológico do TCC.

## 3. Experimentos planejados (backlog priorizado)

Os IDs viram cartões em `experimentos/cards/` quando cada um for aberto. Hipóteses em
[HIPOTESES.md](../experimentos/HIPOTESES.md).

Na coluna "Executor", Codex = implementação crítica e Agy = Antigravity.

| ID | Frente | Prioridade | O quê | Executor / ambiente | Custo | Abandono |
|---|---|---|---|---|---|---|
| **E001** | C | P0 | **Montar o teste cego lacrado**: 90 páginas de PDFs nunca tocados (30 CE, 30 MA, 30 RJ; ~15 PDFs por UF, ≤ 2 páginas por PDF) + `TESTE_CEGO.lock` com hashes. Montar também 45 de desenvolvimento novas | Codex, CPU local | 1 dia de máquina + anotação do Pedro | — |
| **E002** | A | P0 | **Oráculos:** (a) candidatos (recall por classe de erro, K = 12/24/32); (b) decodificador com escores perfeitos (guloso, matching, max-regret); (c) residual (só operações locais); (d) **roteamento por página** (melhor entre regra, LayoutReader, reordenação restrita e híbrido) | Codex, CPU | 1–2 dias | oráculo < 20% de redução → revisar candidatos antes de treinar |
| **E003** | A | P2 | **LM causal:** completar a validação RN do job 1053, pontuar log P(t_j) sem contexto (escore contrastivo), decodificar. Desenho 2×2 (geometria fixa/aprendida × com/sem LM) depois do E004 | Spark (Qwen3-8B) + CPU | 1 job de ~1 h + 1 dia | ganho < 0,5 quebra/página sobre a variante geométrica |
| **E004** | A | P1 | **Grafo de arestas aprendidas:** LightGBM com features de geometria, estrutura, texto barato e priors da regra, mais negativos difíceis. Treinado no silver de treino com 3 níveis de confiança e decodificado de 3 formas | Codex, CPU (Spark para varreduras) | 3–5 dias | 2 configurações sem −10% de quebras no desenvolvimento |
| **E005** | A | P1 | **Seletor por página:** limiar 67 congelado × seletor simples (densidade, nº de colunas, proporção de margem, transversais), com validação cruzada agrupada por veículo | Codex, CPU | 1–2 dias | não superar o limiar 67 fora da amostra |
| **E006** | A | P1 | **Correção residual com função de ganho:** troca de vizinhas, mover bloco curto na coluna, reinserir margem/título. Reportar erros introduzidos | Codex, CPU | 1–3 dias | não superar a reordenação restrita atual em v3 e v4 |
| **E007** | A | P3 | **VLM seletivo:** imagem + ordem proposta → permutação de IDs só no trecho suspeito, podendo se abster. 20–30 páginas difíceis do desenvolvimento | Spark (Qwen-VL) ou Gemini API | 2–3 dias | corrige < 25% dos erros das regiões |
| **E008** | B | P1 | **Protocolo de anotação densa × simplificada** (desenho cruzado, 36 páginas). Preparar: ferramenta com cronômetro e log de ações | Agy (ferramenta) + Pedro (anotação) | 2 dias + sessões do Pedro | — (resultado metodológico, qualquer que seja) |
| **E009** | B | P1 | **Representação:** caixas automáticas × linhas automáticas com cobertura controlada; formaliza o 213 → 29 | Codex, CPU | 1 dia | — |
| **E010** | C | P2 | **Silver ampliado (D4):** 10–20 mil páginas dos veículos de treino, exportadas no cluster, com nível de confiança por transição | Spark (CPU/GPU) | 1–2 jobs | — |
| **E011** | A | P4 | **GNN (GraphSAGE/GAT) ou LayoutLMv3 relacional:** só se o E004 mostrar falha por falta de contexto | Spark/Kaggle | 4–8 dias | < 0,5 quebra ou < 2 pp no sucessor difícil sobre o LightGBM |
| **E012** | C | liberado (02/11) | **Dados da Data Policy (uso autorizado):** conversão auditada de 20 páginas (caixa → linha), depois treino/ajuste | Claude, CPU local + Spark | 1–2 dias | se a conversão for ambígua em > 20% das relações |
| **E013** | A/infra | P5 | **DocLayout-YOLO no Kaggle** (detector alternativo de tabela/figura), só se o E002 mostrar erro relevante vindo de átomos | Kaggle | 1 sessão | — |

**O que fica de fora, com motivo** (ver [NAO_FUNCIONOU.md](../experimentos/NAO_FUNCIONOU.md)):
pointer network e LayoutReader readequado (baixo retorno esperado); LayoutLM lendo o texto
(piorou); mais variantes de margem ajustadas no golden_v4 (não generalizam).

## 4. Protocolo de avaliação (congelado)

- **Unidade:** linhas + átomos ls3. Régua: `erros_ponta_a_ponta` e `bancada_ordenadores`, que não são reimplementadas. A entrada é embaralhada por `page_id`.
- **Métricas:**
  - primária: quebras de leitura por página;
  - controles: quebras por 1.000 transições elegíveis e cobertura de palavras (nenhum método pode ganhar apagando conteúdo);
  - secundária: τ de palavras;
  - diagnóstico: sucessor de linha, reparos e regressões por classe de erro, tempo por página.

  Reportar a página inteira **e** só o corpo do texto, como o OmniDocBench, que ignora elementos marginais.
- **Conjuntos:**
  - **ajuste:** golden_v4 + validação silver RN;
  - **desenvolvimento externo:** golden_v3_novo (já consultado), teste silver CE/MA/RJ e 45 páginas novas de desenvolvimento;
  - **confirmatório:** o teste cego (E001), avaliado **uma única vez**, no fim.
- **Durante o desenvolvimento (exploratório):** Δ contra o baseline com IC95 por bootstrap agrupado por veículo/PDF, Wilcoxon descritivo e contagem de páginas melhor/igual/pior. Sem decisões por p-valor.
- **Confirmatório:** uma comparação, método final × híbrido 67 (e × regra), bootstrap por PDF. Com até 3 finalistas, correção de Holm.
- **Critério de superioridade (pré-registrado):**
  - ≥ 10% menos quebras na macro-média das UFs;
  - IC95 do Δ inteiramente abaixo de zero;
  - nenhum veículo piorando mais de 0,5 quebra por página;
  - cobertura e política de avaliação idênticas.

  Uma melhora de 10–15% com IC cruzando zero se registra como "promissor".
- **Modelos treináveis:** 3 sementes com média e desvio; a regra de seleção de checkpoint é congelada antes do teste cego.
- **Regra de parada por família:** orçamento de dias da tabela acima e no máximo 2 configurações substancialmente diferentes. Parar se o oráculo for baixo, se não houver ganho prático ou se houver piora recorrente num conjunto humano. O resultado negativo vai para NAO_FUNCIONOU.md com a explicação.

## 5. Quem faz o quê

| Atividade | Ferramenta | Por quê |
|---|---|---|
| Orquestração, revisão de resultados, registro, decisões, documentação | **Claude** (esta sessão, com `/loop`) | mantém o contexto e confere os números |
| Scripts de experimento (oráculos, grafo, seletor, corretor, montagem do teste cego) | **Codex** (`gpt-6.1-sol`, executa o que escreve) | precisão técnica; testa antes de entregar |
| Relatórios longos, figuras, ferramenta de anotação com cronômetro, gerador de layouts sintéticos, fichamento de artigos | **Antigravity** (`gemini-3.8-flash-high`, sem comandos) | volume, cota separada; tudo revisado pelo Claude |
| Decisões de método e de protocolo; revisão do plano ao fim de cada semana ou quando uma família bate a regra de parada | **ChatGPT** (Chrome) | orientador; consultas salvas em `experimentos/consultas/` |
| LM causal 8B–30B, VLM (Qwen-VL), silver ampliado, varreduras de sementes | **DGX Spark** | 80 GB por job; 1 job por vez; partição principal |
| Segunda GPU: sementes de baselines, DocLayout-YOLO | **Kaggle** (2× T4) | paralelo à Spark; automático só com o token (DEPENDENCIAS item 5) |
| Avaliação, CPU (LightGBM, decodificadores), modelos pequenos, ferramenta de anotação | **PC local** | régua e dados estão aqui |
| VLM sobre dados próprios (nunca da Data Policy) | **Gemini API** | piloto do E007 se não houver Qwen-VL na Spark |

**Dados da Data Policy:** uso autorizado pelo projeto (confirmado em 02/11); ficam só no PC e no cluster; nunca vão a Gemini,
Antigravity ou Codex.

## 6. Execução contínua (como a fase roda sem novas instruções)

1. **Filas de agentes** (`orquestracao/fase_nov/`):
   - `fila.sh codex`, `fila.sh agy` e `fila.sh cmd`, iniciadas por `iniciar.ps1`;
   - cada tarefa é um `.txt` com `#ESPERA` (dependência), `#SAIDA` (arquivo exigido) e, na fila `cmd`, `#GPU: sim`;
   - os jobs da Spark passam por `spark.sh` (`enviar` / `esperar` / `trazer`), que reaproveita o job se ele já estiver na fila;
   - `STOP` para tudo; `status.sh` mostra o estado em poucas linhas.
2. **Laço do Claude** (`/loop` nesta sessão), a cada 20–30 min:
   - ler o `status.sh`;
   - revisar cada entrega: âncora reproduzida, números conferidos contra os arquivos, sem tocar em `data/`;
   - registrar a execução com `src/exp/registro.py registrar`;
   - atualizar o cartão;
   - decidir o próximo passo pelas regras de parada;
   - enfileirar a tarefa seguinte.
3. **Pontos de consulta ao ChatGPT:** fim de cada semana (S1–S6), quando uma família atinge a regra de parada e antes de congelar o método final.
4. **O Pedro é acionado só** para os itens de DEPENDENCIAS.md, as sessões de anotação (E001/E008) e a escolha final antes do teste cego.

## 7. Cronograma (6 semanas, a partir de 03/11/2026)

| Semana | Ordenação (A) | Anotação (B) | Dados (C) | Entrega |
|---|---|---|---|---|
| S1 (03–09/11) | E002 oráculos; E003 completar LM | preparar a ferramenta com cronômetro (E008) | E001 montar teste cego + desenvolvimento | go/no-go do grafo e do roteamento |
| S2 (10–16/11) | E004 grafo LightGBM + 3 decodificadores; E005 seletor | 1ª sessão do cruzado (Pedro) | E010 silver ampliado (Spark) | baseline relacional |
| S3 (17–23/11) | E003 2×2 do LM; E006 residual | 2ª sessão do cruzado | anotar as 45 de desenvolvimento | escolher 2 abordagens |
| S4 (24–30/11) | combinar; E007 VLM só se necessário; **congelar** | E009 representação | iniciar a anotação do teste cego | código e hipóteses congelados |
| S5 (01–07/12) | ablações no desenvolvimento | análise do E008 | **concluir as 90 cegas** sem ver saídas | teste lacrado anotado |
| S6 (08–14/12) | **avaliação confirmatória única** | — | — | resultados finais + capítulos |

**Plano B (4 semanas):** 30 páginas de desenvolvimento, 60 cegas (20 por UF) e 24 cruzadas;
a afirmação de superioridade passa a ser mais cautelosa.

## 8. O que vira texto do TCC

Os resultados são organizados em quatro eixos, não um capítulo por modelo:
1. **Granularidade:** caixas × linhas, com controle de cobertura (E009, histórico 213 → 29).
2. **Inferência:** regra, seleção por página, relações locais e decodificação global (E002, E004, E005, E006).
3. **Sinais:** geometria, texto barato, LM causal e VLM (E003, E007; ablações).
4. **Generalização e custo:** teste cego por PDF/veículo, anotação simplificada e custo computacional (E001, E008).

LayoutLM, LayoutReader e BiLSTM entram como baselines e discussão.

**Registro para a escrita:** cada cartão tem a seção "Para o texto do TCC". O
[Diário de Bordo](DIARIO_DE_BORDO.md) recebe uma entrada por semana. As consultas ao
ChatGPT ficam guardadas como fundamentação das decisões. As versões de dados (D1, D2...) são
citáveis.

## 9. Riscos

| Risco | Efeito | Mitigação |
|---|---|---|
| Anotação demora mais que ~45 págs/rodada | teste cego atrasa | medir tempo nas 10 primeiras; plano B de 4 semanas |
| Fila da Spark longa / job cancelado | E003/E010 atrasam | retomada por página; partição principal; Kaggle como alternativa |
| Ganho só no ajuste (já aconteceu 3 vezes) | conclusão falsa | ajuste só em v4+RN; teste cego lacrado; cartão com critério antes de rodar |
| SSD USB cai e perde arquivos | perda de trabalho | commit frequente (DEPENDENCIAS item 1) |
| ~~Data Policy não autoriza~~ | resolvido em 02/11: uso autorizado | — |
| Nenhum método supera o híbrido | sem "vitória" | o TCC continua com resultados defensáveis: limites (oráculos), granularidade, custo de anotação e o próprio híbrido validado no teste cego |
