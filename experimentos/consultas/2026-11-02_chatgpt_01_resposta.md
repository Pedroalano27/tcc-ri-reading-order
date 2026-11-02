# Consulta 01 ao ChatGPT — plano de experimentos (02/11/2026)

- **Pergunta:** [2026-11-02_chatgpt_01_pergunta.md](2026-11-02_chatgpt_01_pergunta.md)
- **Conversa:** https://chatgpt.com/c/6ae8d81e-3ce0-83e9-a114-20b580d695e7 (conta do Pedro; raciocínio "Alta", ~4 min)
- **Registro:** resumo fiel feito pelo Claude, com os números e limiares que o ChatGPT propôs. Não é transcrição literal.

## Decisão central proposta

Concentrar o TCC na hipótese: *a ordem de leitura de diários pode ser melhorada combinando
restrições geométricas com otimização global de relações de sucessão entre linhas, sem
segmentação manual detalhada nem modelos multimodais grandes.* Não iniciar outro treino
pesado de LayoutLM, LayoutReader ou pointer network agora.

Três frentes: **principal**, grafo de sucessão entre linhas (arestas aprendidas e
decodificação global); **complementar**, correção residual conservadora da regra; e
**metodológica**, representação e anotação simplificadas, medindo qualidade e custo humano.

## Prioridades (custo aproximado, sem anotação)

| Prioridade | Família | Custo | Decisão |
|---|---|---|---|
| P0 | Oráculos do grafo + análise de erros | 1–2 dias | obrigatório |
| P1 | Arestas par-a-par + decodificação global | 3–5 dias | principal aposta |
| P1 | Correção residual local da regra | 1–3 dias | continuar |
| P2 | LM causal como escore de aresta | 2–4 dias | concluir o experimento |
| P3 | VLM reordenando trechos difíceis | 2–3 dias | piloto limitado |
| P4 | GNN sobre o grafo de linhas | 4–7 dias | condicional |
| P5 | LayoutLMv3 com relações entre linhas | 4–8 dias | baixa prioridade |
| P6 | Pointer network / transformer de permutação | 5–10 dias | não investir agora |
| P7 | LayoutReader readequado | 3–6 dias | encerrar como baseline |

- **P0 — três oráculos:**
  - de candidatos: quais relações verdadeiras o grafo nem propõe;
  - condicionado ao decodificador: escores perfeitos com o decodificador real;
  - residual: só as operações do corretor local.

  O limite é medido em quebras **por classe de erro**: margem, continuação na coluna, cruzamento de colunas e transversal. Se o oráculo não superar a regra em ≥ 20% no desenvolvimento, revisar candidatos e restrições antes de treinar qualquer coisa.
- **P1 grafo:**
  - Começar com LightGBM/CatBoost. Features: geometria relativa, contexto estrutural (cabeçalho/rodapé provável, faixa transversal, tabela, fonte), texto barato (hífen, pontuação, numeração, marcadores) e priors da regra.
  - Treinar com negativos difíceis.
  - K = 12, 24 e 32 candidatos por linha.
  - Comparar três decodificadores com os mesmos escores: guloso, matching com eliminação de ciclos e max-regret (path cover).
  - **Abandono:** com o oráculo bom, duas configurações razoáveis sem reduzir ≥ 10% das quebras no desenvolvimento.
- **P1 residual:**
  - Três operações apenas: troca de vizinhas; mover bloco curto dentro da coluna com deslocamento limitado; reposicionar margem ou título em pontos de inserção candidatos.
  - Função de ganho = arestas removidas × adicionadas.
  - Reportar erros introduzidos.
  - **Abandono:** não superar a reordenação restrita atual de forma consistente em v3 e v4.
- **P2 LM causal:**
  - Desenho 2×2 com os mesmos candidatos e o mesmo decodificador (geometria fixa ou aprendida × com ou sem LM).
  - Escore contrastivo [log P(t_j | t_i) − log P(t_j)] / |t_j|, em vez de perplexidade bruta.
  - **Abandono:** ganho < 0,5 quebra por página sobre a variante geométrica.
- **P3 VLM:**
  - Recebe a imagem e a ordem da regra, devolve só a permutação de IDs, pode se abster.
  - Piloto com 20–30 páginas difíceis do desenvolvimento, um modelo e um prompt fixo.
  - **Abandono:** corrigir < 25% dos erros das regiões selecionadas.
- **P4 GNN:** só se o classificador de arestas falhar comprovadamente por falta de contexto. Usaria GraphSAGE ou GAT de 2–3 camadas. **Abandono:** ganho < 0,5 quebra por página ou < 2 pontos percentuais no sucessor difícil sobre o LightGBM.
- **Literatura indicada:** arXiv 2607.01018 (path cover + max-regret, mas sem garantia de transferência) e *Modeling Layout Reading Order as Ordering Relations* (EMNLP 2024), mais próximo da formulação relacional.

## Anotação simplificada

- Avaliação favorável, mas com a ressalva de que são **quatro hipóteses separadas**, com critérios pré-registrados:

  | Hipótese | Afirmação | Critério |
  |---|---|---|
  | H6 | custo | ≥ 25% menos tempo mediano |
  | H7 | qualidade | ≥ 30% menos erros de união ou divisão |
  | H8 | ordem | não inferior, com margem de 0,5 quebra por página |
  | H9 | completude | mesma cobertura de palavras |

- **Desenho cruzado, com um anotador:** 36 páginas de desenvolvimento estratificadas. 18 são anotadas na ordem A→B e 18 na ordem B→A, com 7–10 dias entre as duas sessões e a ordem aleatória. O tempo, os cliques e as correções são registrados automaticamente. A análise principal de tempo usa só a **primeira sessão** de cada página.
- **Separar dois experimentos:**
  - **A:** protocolo de anotação (tempo e erros);
  - **B:** representação para inferência (caixas automáticas × linhas automáticas, com o resto fixo).
- **Condição simplificada:** linhas automáticas; revisão só de tabela, figura, quadro, ruído (`skip_noise`) e linhas erradas; classificação fina adiada.
- **Adoção:** se B reduzir ≥ 25% do tempo, mantiver a cobertura e não perder ordem além da margem, adotar a simplificada mesmo sem ganho de ordenação. Isso já é um resultado metodológico.

## Dados

- **135 páginas humanas novas:**
  - 45 de desenvolvimento, dos veículos de treino e RN;
  - **90 de teste cego**: 30 de CE, 30 de MA e 30 de RJ, de PDFs não usados, cerca de 15 PDFs por UF e no máximo 2 páginas por PDF.

  As 36 páginas cruzadas fazem parte das 45. O golden_v4 e o golden_v3_novo ficam no desenvolvimento para sempre. Na versão mínima de 4 semanas são 30 páginas de desenvolvimento, 60 cegas (20 por UF) e 24 cruzadas.
- **Silver:** usar seletivamente, com três níveis de confiança das transições (alta: mesma coluna e geometria compatível; baixa: mudança de coluna e margens).
- **Parceiro:** só com autorização explícita. Fazer antes uma conversão auditada de 20 páginas, porque a anotação é por caixa e não determina todos os vínculos entre linhas. Não comparar o 0,815/0,918 deles diretamente com os nossos números.
- **Síntese:** layouts parametrizados (2–5 colunas, títulos transversais, tabelas, cabeçalhos repetidos) para pré-treino e testes de estresse. Nunca substitui o teste humano.

## Protocolo estatístico

- **Métricas:**
  - primária: quebras por página;
  - controles: quebras por 1.000 transições elegíveis e cobertura de palavras (obrigatória: o método não pode ganhar apagando conteúdo);
  - diagnóstico: sucessor de linha, erros removidos e introduzidos, tempo por página.
  - Reportar duas versões da ordem: página inteira e só o corpo do texto, como o OmniDocBench, que ignora elementos marginais.
- **Confirmatório:** **uma única comparação**, método final × regra, no teste cego. Bootstrap agrupado **por PDF**; Wilcoxon sobre as diferenças agregadas por PDF. Com 3 finalistas, aplicar Holm. Nada de testes de significância durante o desenvolvimento, que é exploratório.
- **Critério de superioridade pré-registrado:**
  - ≥ 10% menos quebras na macro-média das UFs;
  - IC95 inteiramente abaixo de zero;
  - nenhum veículo piorando mais de 0,5 quebra por página;
  - cobertura e política de avaliação idênticas.

  Uma melhora de 10–15% com IC cruzando zero conta como "promissor".
- **Parada:** cada família tem orçamento de tempo e duas configurações substancialmente diferentes. Parar se o oráculo for baixo ou se não houver ganho prático. Priorizar estabilidade se as sementes variarem muito. Não promover um método só pelo golden_v4. Modelos treináveis: 3 sementes, com a regra de seleção congelada antes do teste cego.

## Cronograma de 6 semanas

| Semana | Foco | Entrega |
|---|---|---|
| S1 | Oráculos, avaliador congelado, auditoria de erros, regras de anotação | go/no-go do grafo |
| S2 | LightGBM/CatBoost + 3 decodificadores; anotar as 45 de desenvolvimento | baseline relacional |
| S3 | Qwen causal, ablações, 2ª anotação cruzada, corretor restrito | escolher 2 abordagens |
| S4 | Combinar, VLM só se necessário, congelar configuração, iniciar o gold cego | código e hipóteses congelados |
| S5 | Anotar as 90 cegas sem consultar as saídas dos modelos | teste selado |
| S6 | Avaliação confirmatória única, bootstrap, ablações, redação | resultados reproduzíveis |

## Capítulos (quatro eixos, não um capítulo por modelo)

1. **Granularidade:** caixas × linhas, com controle de cobertura.
2. **Inferência:** regra, relações locais e decodificação global.
3. **Sinais adicionais:** geometria, LM causal, residual e VLM seletivo.
4. **Generalização e custo:** veículos externos, bootstrap e anotação simplificada.

LayoutLM, LayoutReader e BiLSTM entram como baselines e discussão.

## O que o Claude aceitou, ajustou ou rejeitou

- **Aceito:**
  - P0 com os oráculos antes de qualquer treino;
  - grafo com GBDT e 3 decodificadores;
  - desenho 2×2 do LM;
  - escore contrastivo;
  - teste cego por PDF com uma única comparação confirmatória;
  - desenho cruzado da anotação;
  - critérios pré-registrados.
- **Ajustado:** o híbrido por densidade (que o ChatGPT não conhecia na primeira pergunta) entra como baseline a superar e como família própria, o seletor por página. Ver a consulta 02.
- **Ponto de atenção:** 171 sessões de anotação em 6 semanas pressupõem o ritmo de ~45 páginas por rodada. Medir o tempo real nas 10 primeiras e recalibrar. A versão mínima de 4 semanas fica como plano B.
