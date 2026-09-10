# Diário de Bordo do TCC

Registro cronológico de **tudo** o que foi feito no projeto, com as decisões tomadas,
as alternativas descartadas e os problemas encontrados no caminho. Serve de fonte
para os capítulos de Metodologia e de Desenvolvimento do texto do TCC.

Documentos relacionados:
[METODOLOGIA.md](METODOLOGIA.md) · [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md) ·
[ACERVO.md](ACERVO.md) · [ROADMAP.md](ROADMAP.md) · [LITERATURA.md](LITERATURA.md)

---

## Sessão 1 — 2026-09-03: repositório, escopo e ambiente

### 1.1 Repositório no GitHub

- A pasta do projeto já era um repositório git local, sem commits, na branch `master`.
- Antes do primeiro commit, busca por segredos (chaves de API, tokens, senhas) nos
  arquivos: nenhum encontrado.
- Criado `notebooks/.gitkeep` (o git não versiona pastas vazias).
- Commit inicial `e8aacd3`: 17 arquivos, 941 linhas. Branch renomeada para `main`
  (padrão do GitHub).
- O GitHub CLI (`gh`) não estava instalado; o repositório
  [Pedroalano27/tcc-ri-reading-order](https://github.com/Pedroalano27/tcc-ri-reading-order)
  foi criado manualmente e o remoto configurado para o push.

### 1.2 Realinhamento de escopo

O resumo de diretrizes produzido com o NotebookLM definiu o escopo: **detecção de
ordem de leitura (Reading Order Detection) em Diários Oficiais**, comparando o
**LayoutLM** (modelo leve, consciente de layout) com **LLMs generativas**, sob o
trade-off de eficácia × eficiência de Recuperação de Informação. Métricas: BLEU de
página e ARD.

**Descoberta:** todo o conteúdo do repositório tinha sido escrito sob um escopo
anterior — *extração de informações de alto valor (licitações)* com LSTM × LLM. O
README, a literatura e os módulos de `src/` estavam desalinhados.

Ações (commit `2521c55`):
- `README.md` reescrito: novo título, problema, objetivo, métricas, estratégia de dados.
- `docs/LITERATURA.md` reescrito: acrescentados **LayoutLM** (Xu et al., 2020),
  **LayoutReader** (Wang et al., 2021 — origem das métricas BLEU/ARD),
  **DocLayNet** (Pfitzmann et al., 2022) e **BLEU** (Papineni et al., 2002); as três
  referências antigas foram recontextualizadas para o novo enquadramento.
- `get_predataset.py` reescrito: as 5 páginas sintéticas antigas eram idênticas e o
  embaralhamento não tinha semente. Agora: semente fixa (reprodutível — verificado por
  hash), 1 a 3 colunas, cabeçalho/rodapé de largura inteira, nenhuma página chega já
  ordenada, metadados de layout por página.

### 1.3 Formato dos dados

Pergunta levantada: *os arquivos são JSON — isso serve para ler diários oficiais?*
Resposta registrada: **o formato JSON é o correto** (é o formato intermediário
universal da área: PDF → caixas com texto e coordenadas → modelo); o **conteúdo**
sintético é que não serve para resultados — é andaime para testar o código.

### 1.4 Ambiente de desenvolvimento

| Etapa | O que aconteceu | Decisão |
|---|---|---|
| Python | O padrão do sistema era o **3.14.7**, recente demais para o `torch` | Usado o **3.11.9** já instalado |
| GPU | **RTX 4050 Laptop, 6 GB VRAM**, compute capability 8.9 | Instalar `torch` com CUDA |
| OneDrive | O git falhou com `Permission denied: unable to open loose object` — o OneDrive travava arquivos de `.git/objects` durante a sincronização | Projeto movido para **`C:\Users\pedro\dev\tcc-ri-reading-order`** (o GitHub é o backup) |
| `torch` (1ª tentativa) | `pip install -r requirements.txt` instalou **2.14.0+cpu**: o PyPI não serve wheels CUDA para Windows | Usar o índice oficial do PyTorch |
| `torch` (2ª tentativa) | `2.14.0+cu130` instalou, mas `cudaErrorNotSupported`: o driver **577.05 suporta até CUDA 12.9** | — |
| `torch` (3ª tentativa) | **`2.9.1+cu128`** → GPU reconhecida; 10 multiplicações 4000×4000 em 0,47 s | Versão fixada no README e no `requirements.txt` |
| Ollama | Já instalado (0.33.2), com `llava:7b` | Usado como LLM local |

Commit `783815b`: `requirements.txt` completado (`datasets`, `sacrebleu`, `pillow`,
`ollama`) e seção de instalação reescrita.

---

## Sessão 2 — 2026-09-09: o acervo do orientador

### 2.1 Extração

- 8 arquivos ZIP do Google Drive (partes independentes), **14,6 GB** compactados,
  **18,7 GB** descompactados, **4.660 arquivos** (4.644 PDFs e 16 auxiliares).
- **A primeira extração falhou em 100% dos arquivos.** A pasta raiz dentro dos ZIPs
  chama-se `"Diários "` — com espaço no final, nome que o Windows rejeita.
  Solução: saneamento dos caminhos (`src/data/extrair_zips.py`). Resultado:
  4.660 arquivos em 116 s, zero erros.

### 2.2 Diagnóstico (detalhes em [ACERVO.md](ACERVO.md))

- **4.644 PDFs, ~310.000 páginas**, 23 UFs + 8 municípios, 2010–2026.
- **~96% digitais** (camada de texto com coordenadas): o pipeline dispensa YOLO e OCR.
- Integridade: 154 de 155 PDFs amostrados abrem.
- Texto ilegível `(cid:N)`: **PI 86%** (inutilizável; o professor já tinha refeito
  como `pi_v2`), **AC 32%**, RJ 2,8%, PE 1,1%, demais 0%.
- **Goiás não está no acervo** (faltam GO, DF, ES, MT) → proposta: usar Goiás como
  teste *out-of-domain*.
- **Japeri (RJ)** traz saídas do **Azure Document Intelligence** (228 parágrafos) e do
  **Google Document AI** (258 blocos) para o mesmo documento, além de atos já
  categorizados em JSON.

Commit `be566a8`: `docs/ACERVO.md` e scripts de extração e diagnóstico.

---

## Sessão 3 — 2026-09-10: pipeline experimental completo

### 3.1 Duas correções metodológicas (importantes para a defesa)

**Correção 1 — a métrica de "desordem" estava inflada.** O diagnóstico de 09-09
reportou "86% de desordem", medida como *fração de linhas fora da posição exata*.
Essa medida sofre de **efeito cascata**: um único bloco deslocado no início empurra
todos os seguintes uma posição, e a página inteira conta como "fora de posição"
(foi o que produziu "130 de 133 linhas fora de posição"). O número **não deve ser
citado**. Foi substituída pelo **τ de Kendall** (conta pares discordantes, imune ao
efeito cascata) e pelo **ARD** — as métricas usadas daqui em diante.

**Correção 2 — a "ordem crua do PDF" não era crua.** O `extract_words()` padrão do
`pdfplumber` **pré-ordena** as palavras geometricamente (de cima para baixo, da
esquerda para a direita). A ordem medida em 09-09 era, portanto, a ordem geométrica
ingênua — não a ordem em que o arquivo foi escrito. A verdadeira ordem do fluxo de
conteúdo exige `extract_words(use_text_flow=True)`. O extrator novo mede as duas
separadamente.

### 3.2 O pipeline construído

```
PDF ──► extrator.py ──► blocos + 3 ordens ──► caracterizar.py ──► splits.json
                         (stream, naive,          │
                          xycut)                  ▼
                                   ┌──── protocolo.py (mesma entrada para todos) ────┐
                                   ▼            ▼            ▼             ▼          ▼
                             baselines.py  lstm_ordem.py  layoutlm_ordem.py  llm_ordem.py
                                   └────────────┴──── pred_*.jsonl ──┴──────────┘
                                                          ▼
                                            comparar.py ──► figuras.py
```

| Módulo | Função |
|---|---|
| `src/data/extrator.py` | PDF → palavras (em ordem de fluxo) → linhas (sem atravessar calhas entre colunas) → blocos (parágrafos) → três ordens candidatas |
| `src/eval/metrics.py` | τ de Kendall, ARD, ARD normalizado, BLEU de página, acerto exato, reparo de permutações |
| `src/eval/caracterizar.py` | Mede a concordância entre as ordens por veículo; define os veículos confiáveis e a divisão treino/validação/teste |
| `src/eval/protocolo.py` | Garante entrada idêntica para todos os métodos (permutação fixa por página) e a mesma referência |
| `src/eval/baselines.py` | Ordem do detector, ingênua e XY-cut |
| `src/models/lstm_ordem.py` | BiLSTM em três variantes (texto, geometria, ambos) |
| `src/models/layoutlm_ordem.py` | LayoutLM como learning-to-rank; ablação sem layout |
| `src/eval/llm_ordem.py` | LLM zero-shot via Ollama, com medição de confiabilidade de formato |
| `src/eval/comparar.py` | Tabelas, intervalos de confiança, pior caso, testes de Wilcoxon |
| `src/eval/figuras.py` | Figuras para o texto |

### 3.3 Execução

- **Métricas validadas** em casos controlados. Achado: numa página **totalmente
  invertida**, o BLEU ainda marca **82,7** (enquanto τ = −1). Em granularidade de
  bloco, quase todos os n-gramas são internos aos blocos e sobrevivem a qualquer
  reordenação. **O BLEU não pode ser a métrica principal nesta granularidade.**
- **Extração, 1ª rodada:** 14 PDFs × 4 páginas por veículo, 9 processos. Rápida nos
  veículos leves, lenta nos densos (páginas de MG com mais de 6.000 palavras levam
  vários segundos no `pdfplumber`). Interrompida após concluir 15 veículos.
- **Extração, 2ª rodada:** os 17 veículos restantes com 6 PDFs × 3 páginas, 10 processos.
- **Teste de fumaça do LayoutLM na GPU:** pico de **3,09 GB de VRAM** com micro-lote
  de 4 páginas e sequência de 418 tokens; inferência em **22–38 ms por página**.

Os números dos experimentos estão em [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md).

---

## Problemas encontrados e soluções

| Problema | Causa | Solução |
|---|---|---|
| Não havia como criar o repositório pela linha de comando | GitHub CLI ausente | Repositório criado pela interface web |
| `Permission denied` em objetos do git | OneDrive sincronizando `.git/` | Projeto movido para fora do OneDrive |
| `torch` sem GPU | PyPI serve só a build CPU no Windows | Índice oficial do PyTorch |
| `cudaErrorNotSupported` | Driver 577.05 não suporta CUDA 13 | `torch 2.9.1+cu128` |
| Sem wheels do `torch` | Python 3.14 recente demais | Python 3.11.9 |
| Extração dos ZIPs falhou 100% | Pasta `"Diários "` com espaço final | Saneamento dos caminhos |
| `python` travando | Atalho da Microsoft Store (`WindowsApps\python.exe`) | Usar sempre `venv\Scripts\python.exe` |
| "86% de desordem" | Métrica posicional com efeito cascata | τ de Kendall e ARD |
| "Ordem crua" pré-ordenada | Padrão do `pdfplumber` | `use_text_flow=True` |
| Extração lenta em páginas densas | Custo do `pdfplumber` | Amostra menor nos veículos pesados; PyMuPDF como otimização futura |

## Decisões e justificativas

| Decisão | Alternativas consideradas | Por quê |
|---|---|---|
| Unidade = **bloco** (parágrafo/trecho de coluna) | Palavra (como no LayoutReader), linha | Alinha com a saída de detectores de layout tipo YOLO, que produzem regiões; cabe na janela de 512 tokens do LayoutLM |
| Referência = **fluxo do PDF nos veículos em que ele é confiável** | Usar a própria XY-cut como referência; anotar à mão | Escala sem anotação manual; usar a heurística como referência a tornaria imbatível por definição (circularidade); a confiabilidade é decidida **por veículo**, não por página, para não selecionar só as páginas em que a heurística acerta |
| Divisão **por veículo** | Aleatória por página | O mesmo veículo repete o template por anos; divisão aleatória vazaria o layout do teste para o treino e inflaria as métricas |
| Entrada **embaralhada** com permutação fixa | Entregar na ordem do fluxo ou na ingênua | A ordem de entrada não carrega informação: o método só acerta usando texto e geometria. Simula um detector que entrega caixas sem ordem |
| LayoutLM como **learning to rank pontual** | Seq2seq com ponteiro (LayoutReader), classificação par a par | Mais simples e estável; conecta a tarefa à área de Learning to Rank, linha de pesquisa do orientador |
| `microsoft/layoutlm-base-uncased` | LayoutXLM (multilíngue), LayoutLMv3 | A v1 não exige imagem nem `detectron2` (difícil de instalar no Windows). Limitação: tokenizador em inglês |
| `llava:7b` como LLM | `qwen2.5:7b`, `llama3.1:8b` | Já estava instalado; o download de ~5 GB de outro modelo ficou a critério do autor |
| **τ de Kendall como métrica principal** | BLEU | BLEU é insensível em granularidade de bloco (página invertida = 82,7) |
