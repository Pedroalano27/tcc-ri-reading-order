# Contexto consolidado e recursos disponíveis — levantamento de 02/11/2026

Levantamento feito antes da fase intensiva de experimentos de novembro. Reúne o estado do
TCC, o que foi recuperado de outras conversas (Acessilia, anotação da Data Policy, cluster)
e o inventário de dados, ferramentas e ambientes. Serve de ponto de partida para o
[plano de pesquisa](PLANO_PESQUISA.md) e de fonte para o texto do TCC (capítulos de
Metodologia e Desenvolvimento).

---

## 1. Como o contexto foi recuperado

O Claude Code (aplicativo desktop) não lê conversas do claude.ai nem do ChatGPT, mas lê as
**transcrições locais das sessões do próprio Claude Code** (`~/.claude/projects/*/*.jsonl`)
e as memórias de cada projeto. Foram lidas:

| Sessão | Pasta | Período | Conteúdo útil para o TCC |
|---|---|---|---|
| "Projeto de IA com agents para acessibilidade" (Acessilia) | `OneDrive/Documentos/Acessilia` | 13/09 → 01/11 | QA/homologação do Acessilia; Dr.DocBench; PR do XY-cut na `docstruct`; TeleOCR |
| "Anotar layout de diários (foco)" | worktree `gallant-blackburn-49f6f3` | 25/10 → 02/11 | anotação de ordem da Data Policy no Label Studio; pré-anotador; configuração da DGX Spark; LLMs locais |
| Sessão inicial do TCC | `dev/tcc-ri-reading-order` | 03/09 → 15/09 | origem do acervo; ambiente; Kaggle |
| Esta sessão | `dev/tcc-ri-reading-order` | 04/10 → hoje | representação em linhas, regra de colunas, noites de experimentos |

Conversas no claude.ai (web) e no ChatGPT **não são acessíveis** por ferramenta. A
alternativa adotada é a **ponte por arquivo**: cada consulta ao ChatGPT é feita pelo Chrome
com um prompt autocontido salvo em `experimentos/consultas/` e a resposta é salva ao lado,
com as decisões tiradas dela. Assim nenhum contexto fica preso numa conversa.

## 2. Acessilia e Dr.DocBench — o que importa para o TCC

O Acessilia (A11yDevs, Prof. Marcelo Akira) é uma plataforma de acessibilização de
documentos. O papel do Pedro é **tester/homologador**, não desenvolvedor do núcleo. Pontos
que tocam o TCC:

- **Ordem de leitura no Acessilia:** não há ordenador próprio; a ordem vem do Docling/MinerU
  (fusão de árvores, "esqueleto do MinerU"). Análise detalhada em
  `resultados/acessilia_ordem_leitura.md` (28/10).
- **XY-cut do TCC portado para a lib `docstruct`:** PR A11yDevs/acessilia#121, **mesclado
  pelo professor em 09/10**. Seletivo (só páginas multicoluna, limiar de equilíbrio 0,7),
  desligado por padrão. Na réplica local do protocolo do Dr.DocBench (dev-120): Reading_Order
  69,8 → +1,65 (IC95 +0,45 a +3,3; 7 páginas melhoram, 0 pioram). O experimento completo no
  dev-986 dependia de uma placa do cluster e não foi feito.
- **Dr.DocBench** (shared task de Document Parsing, EvalAI): métrica Reading_Order por página;
  o XY-cut "em tudo" não ajudou (páginas visuais pioram), só o seletivo. Prazo encerrado em
  10/10. Lição para o TCC: **ganho de ordem depende do tipo de página** — a mesma conclusão
  do híbrido por densidade do TCC (seção 4).
- **TeleOCR** (1,2B, Apache-2.0) integrado à Toolbox (PR #30, mesclado em 06/10); leu melhor
  que Docling e MinerU em páginas digitalizadas. Pouco relevante aqui (96% do acervo é digital).
- **Release 0.2.0** do Acessilia em produção (fim de outubro); o foco do grupo passou ao Gestor.
  Nada disso exige trabalho do TCC.

**Conclusão:** o Acessilia não traz método novo de ordenação, mas dá ao TCC (a) uma
aplicação real do XY-cut (citável) e (b) evidência externa de que a ordenação deve ser
seletiva por tipo de página.

## 3. Data Policy (CEIA) — anotação de ordem e pré-anotador

Projeto parceiro (repositório `CEIA-Datapolicy/official-diaries-analysis`), mesmo domínio
(diários oficiais). Recuperado da sessão de anotação:

- Ordem anotada no **Label Studio** em nível de **caixa**, com relações `continue`,
  `skip_noise`, `new_doc` e `end`, e bordas entre páginas. Cada página é uma cadeia de n−1
  relações, o que equivale a um gabarito de **sucessor**.
- Seed 2 (projeto 23): Kamilla 7177–7464, João 7465–7702, Pedro 7703–7927. Seed 6 (issue #69):
  Pedro 8640–8727. Pré-anotador do grupo treinado com **417 páginas de 129 PDFs**.
- **Pré-anotador** (regras + floresta de decisão sobre a ordem do XY-cut, 1,2 MB, sem GPU):
  teste com 80 páginas: média de 3 F1 0,519, sucessor 0,815; com revisão do Opus 0,705/0,918;
  com gemma4 31B no cluster 0,622/0,887; com qwen3.8 27B 0,560/0,839.
- Kamilla relatou que o XY-cut também foi o melhor nos testes dela, e que havia erros de ordem
  em algumas anotações, já corrigidos.
- **Regra em vigor (atualizada em 02/11):** uso na pesquisa **autorizado** pelo projeto; os dados e predições página a página **não são publicados** (repositório público) e
  autorização**, e não podem ir para Gemini/Antigravity/Codex. Podem ir ao cluster do CEIA
  (autorizado em 27/10). Ver [DEPENDENCIAS.md](DEPENDENCIAS.md), item 2.

## 4. Estado do TCC (números medidos)

Representação: **linhas** de texto + átomos de tabela/imagem (detector YOLO `ls3`, mAP50 0,826).
Métrica: quebras de leitura por página (↓), τ de Kendall de palavras, sucessor de linhas.
Bancadas: golden_v4 (44 págs, humana, usada para desenvolver a regra), golden_v3_novo (27,
humana, já consultada), teste silver CE/MA/RJ (89, referência = fluxo do PDF).

| Método | golden_v4 | golden_v3_novo | teste silver | Fonte |
|---|---:|---:|---:|---|
| Extrator + XY-cut + margens | 0,952 / 8,93 | — | — | `resultados/erros_ponta_a_ponta.md` |
| **Regra de colunas** (projeção local + margens) | 0,986 / 6,05 | 0,960 / 9,22 | 0,960 / 27,45 | `resultados/ordenadores_sem_caixas.md` |
| LayoutLM sucessor, geometria, 3.140 págs (s42) | 0,924 / 9,00 | 0,928 / 10,41 | 0,934 / 29,15 | `docs/RELATORIO_NOITE_0410.md` §8 |
| LayoutLM sucessor lendo texto | 0,942 / 20,77 | 0,931 / 23,19 | 0,930 / 50,46 | idem |
| **Híbrido por densidade** (LayoutReader ≤ 67 unidades, regra acima) | 0,980 / **5,14** | 0,959 / **7,89** | 0,959 / **26,43** | `resultados/hibrido_regra_layoutreader.md` |
| Reordenação restrita dentro da coluna | 5,18 | 7,78 | 26,45 | `resultados/reordenacao_restrita.md` |

O híbrido por densidade é o **único resultado com IC95 por veículo abaixo de zero nas três
bancadas** (Δ −0,91 | −1,33 | −1,02), mas o limiar foi escolhido no golden_v4. A reordenação
restrita melhora as médias, com IC incluindo zero. Tudo o mais perde da regra (ver
`experimentos/NAO_FUNCIONOU.md`).

**Em andamento:** arestas pontuadas por LM causal (Qwen3-8B, arXiv 2607.01018) — 87.120 pares
exportados; job 1053 na Spark pontuou golden_v4, golden_v3_novo e teste silver e foi
cancelado na validação RN (2 de 15 páginas). Escores ficam em `~/tcc/ordem_lm/escores/` no
cluster; falta trazer, completar a RN e decodificar.

## 5. Dados

| Conjunto | Onde | Tamanho | Origem | Uso |
|---|---|---|---|---|
| Acervo bruto | `data/raw/` (fora do git) | 4.644 PDFs, ~310 mil págs, 31 pastas (UF/município) | 8 ZIPs do Google Drive enviados pelo orientador em 09/09 | treino silver, bancadas |
| Splits por veículo | `data/processed/splits.json` | treino 7 veículos, validação RN, teste CE/MA/RJ | definido em setembro | todos os experimentos |
| Golden v1/v2/v3 | `data/golden/` | 30 + 29 págs (+ v3 de avaliação) | anotação do Pedro em caixas de parágrafo | histórico; v3_novo = 27 págs fora do v4 |
| **Golden v4** | `data/golden/golden_v4/` | 45 tarefas / 44 avaliáveis | anotação do Pedro (ordem) | ajuste |
| Diamond (segmentação) | `data/diamond/*` | piloto 20, treino 101 de 199, teste 11, rose 15+19+199, massa1_gemini 345 | Pedro + Gemini | detector/segmentação |
| Lote sem parágrafos | `data/diamond/lote_sem_paragrafos/` | 60 págs estratificadas, sem anotação | gerado em 07/10 | **candidato a teste cego** |
| Treino silver em linhas | `resultados/unidades_sem_caixas/` | 3.140 págs | fluxo do PDF, veículos de treino | treino de modelos |
| Data Policy (Label Studio) | `data/labelstudio/` | seeds 1–4 (layout) e seed 2 (ordem) | projeto parceiro | **bloqueado** (seção 3) |
| Japeri com APIs comerciais | `data/processed/blocos_api_*` | Azure 12 págs, Google 2 | APIs pagas | comparação |
| Pares para LM | `resultados/ordem_lm/pares/` | 87.120 pares, 175 págs | exportados em 28/10 | experimento E-LM |

A procedência anterior ao orientador (de onde ele obteve os PDFs, por exemplo raspagem
própria ou projeto Querido Diário) **não está registrada** — pergunta a fazer a ele para a
seção de dados do TCC.

## 6. Ferramentas e ambientes

| Recurso | Capacidade | Limitações observadas | Papel no plano |
|---|---|---|---|
| PC local | RTX 4050 6 GB, 16 GB RAM, Windows, venv Python 3.11 + torch cu128 | C: em SSD USB que cai; laptop reinicia (Windows Update); 1 job de GPU por vez | desenvolvimento, avaliação, modelos pequenos |
| DGX Spark (CEIA) | GB10, até 80 GB por job, contêiner NGC PyTorch, Slurm, internet no login | VPN obrigatória; fila compartilhada; **1 job rodando por usuário**; partição `ephem` cancelou job; nó de login x86 e nós ARM | treinos grandes, LMs 8B–30B, varreduras de sementes |
| Kaggle | 2× T4 (30 h/semana), 12 h por sessão | sem CLI configurada aqui (upload manual); notebooks precisam de Internet ON | treinos médios em lote, segunda GPU paralela |
| Claude (este) | orquestração, implementação, análise, documentação | cota semanal; contexto longo | orquestrador |
| Codex CLI (`gpt-6.1-sol`) | implementação precisa, executa e testa o que escreve | cota; não recebe dados da Data Policy | scripts de experimento |
| Antigravity CLI (`gemini-3.8-flash-high`) | leitura e escrita em volume | não executa comandos; precisa de `--add-dir` fora do repo; erra afirmações (revisar) | relatórios, varreduras de código, rascunhos |
| ChatGPT (Chrome) | orientador técnico/científico | só pelo navegador; respostas longas demoram | decisões de método e protocolo |
| Gemini API (`.env`) | VLM/LLM pago por token | não recebe dados da Data Policy | baseline VLM, pré-anotação de dados próprios |
| Ollama local / no cluster | gemma4 31B, qwen3.8 27B baixados no cluster | não expõe logprob por token | LLM/VLM local |

## 7. Pendências herdadas

- Trabalho desde 12/09 **sem commit** (centenas de arquivos); SSD instável — risco de perda.
- Kaggle: DocLayout-YOLO a rodar de novo (notebook corrigido em 08/10).
- Job da LM causal a completar (validação RN) e decodificar.
- Teste cego humano: não existe; todo número humano atual vem de páginas já consultadas.
