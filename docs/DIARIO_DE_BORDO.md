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

### 3.4 Bateria de experimentos

- **Caracterização (777 páginas, 30 veículos).** O fluxo do PDF só se comporta como
  ordem de leitura em **11 veículos** (τ mediano ≥ 0,7 contra a XY-cut); com o limiar
  de 0,9, apenas 4. Até veículos de coluna única, como Manaus e Tocantins, têm o fluxo
  embaralhado. Consequência: o conjunto com referência confiável ficou pequeno —
  treino com 7 veículos (152 páginas), validação com RN (15), teste com CE, MA e RJ (95).
- **Orquestrador** (`src/rodar_experimentos.py`): a bateria completa rodou em 7,1 min,
  com a GPU em série e os BiLSTM em paralelo na CPU.
- **Rodada 1:** o LayoutLM treinou só 56 s (8 épocas × 19 passos) e ficou
  **subtreinado** — a validação ainda subia a cada época (τ 0,567 → 0,606). Teste: τ 0,660.
- **Rodada 2** (`src/rodar_treino_longo.py`): 40 épocas para o LayoutLM **e** para a
  ablação — na rodada 1 a ablação tinha só 4 épocas, uma comparação injusta. A
  validação do LayoutLM estabilizou em τ ≈ 0,62–0,63 a partir da época 10: **o limite
  é o volume de dados, não o tempo de treino**. Teste: τ 0,671. Sem layout, o modelo
  ficou no nível do acaso durante todo o treino (τ de validação ≈ −0,03) e chegou a
  τ 0,122 no teste — pistas textuais como "cabeçalho primeiro, assinatura no fim".
- **LLM:** 15 páginas (as de até 25 blocos), 80% de permutações válidas, 8,4 s por
  página. Modo de falha: **ecoa a ordem de entrada** (τ mediano de 0,905 com a entrada
  contra 0,121 com a referência).

Os números completos estão em [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md).

### 3.5 Ferramentas para a próxima etapa e primeiro teste de RI (noite de 2026-09-10)

Pedido: preparar o uso do Kaggle para LLMs maiores, um ambiente de rotulação "do jeito
mais fácil" e o máximo de informação para decidir o rumo do TCC.

- **Ferramenta de anotação** (`src/anotacao/`): servidor local só com a biblioteca padrão
  (`servidor.py`, porta 8770) e a página de anotação (`ferramenta.html`). Clique numera o
  bloco; arrastar um retângulo numera uma coluna de cima para baixo; clicar num bloco
  numerado corta a sequência; Z desfaz; o texto aparece na ordem escolhida para conferir
  se as frases emendam; cada mudança é salva como rascunho em cerca de 1 s; o tempo ativo
  é medido por página. Testada no navegador (clique, laço, salvamento automático); a
  anotação de teste foi apagada.
- **Lote `golden_v1`** (`preparar_lote.py`): 30 páginas e 1.044 blocos — 10 dos veículos de
  teste (valida o rótulo silver) e 20 dos veículos não confiáveis (onde não se sabe quem
  acerta). Protocolo em [GUIA_ANOTACAO.md](GUIA_ANOTACAO.md).
- **Avaliador contra humano** (`src/eval/avaliar_golden.py`): todos os métodos contra a
  anotação, por grupo, com concordância entre anotadores e custo da anotação. Testado de
  ponta a ponta com um lote temporário, apagado depois.
- **Kaggle** (`src/kaggle/`): pacote de 2,2 MB (código, blocos, tarefas do Golden,
  predições locais), notebook gerado por código e importador dos resultados.
  `llm_ordem.py` ganhou few-shot, partição do Golden, retomada após queda, janela de
  contexto automática e registro de cada execução — testado localmente com o llava:7b.
  `latencia_hardware.py` mede todos os métodos na mesma máquina. Guia em
  [KAGGLE.md](KAGGLE.md).
- **Métrica "sucessor correto"**: o LayoutLM tem τ 0,671, mas só 13,4% de sucessores
  corretos (XY-cut: 64,2%). A formulação pontual acerta a posição aproximada e troca
  vizinhos, o que picota o texto.
- **Piloto de RI em Japeri** (`src/ri/piloto_japeri.py`): 269 páginas e 915 consultas
  geradas dos atos. Achar a página certa não depende da ordem (MRR ≈ 0,99 para todos);
  o texto que chega ao leitor depende (frases preservadas: 45,4% sem ordenar, 53,4% com o
  fluxo do PDF, 49,7% com a XY-cut, 45,7% com o LayoutLM).
- **Curva de aprendizado** (`src/rodar_curva_aprendizado.py`): 3.117 páginas extras dos 7
  veículos de treino (`blocos_extra`), subconjuntos aninhados de 152 a 3.235 páginas,
  LayoutLM e BiLSTM de geometria. Resultado: o τ do LayoutLM sobe de 0,694 para 0,786 e o
  pior caso (0,527) passa o da XY-cut (0,496), mas o sucessor correto só vai de 16% para
  21%; a BiLSTM não se mexe (0,721 para 0,702). Mais dados corrigem a ordem global, não a
  continuidade.

---

## Sessão 4 — 2026-09-12: formulação de sucessor, Kaggle e conserto da segmentação

### 4.1 O LayoutLM passa a prever o sucessor (`src/models/layoutlm_sucessor.py`)

A formulação pontual acertava a posição aproximada e picotava o texto (13,4% de sucessor
correto). A nova formulação prevê, para cada bloco, **qual bloco vem logo depois**: a
página vira um caminho hamiltoniano num grafo de n+1 vértices, o escore de aresta é um
produto interno entre projeções dos vetores dos blocos somado a um viés geométrico par a
par (10 features relativas), e a perda é entropia cruzada por linha mais a perda de
posição antiga como auxiliar.

Um achado no caminho: decodificar o caminho inteiro pela matriz de sucessores dá
continuidade local ótima e **τ péssimo** (0,44 contra 0,72) — o modelo acerta o próximo
parágrafo dentro da coluna e erra o salto entre colunas, e um salto errado no meio
arruína tudo o que vem depois. A solução foi a **decodificação em cadeias**: aceitar só as
arestas de alta confiança, formando trechos contíguos, e ordenar os trechos pela posição
média prevista pela cabeça pontual. Cada cabeça faz o que sabe fazer.

Resultados no teste, mesmo orçamento de treino da versão pontual (medidos sobre a
segmentação antiga, a ser refeitos — ver 4.3):

| Modelo | Treino | τ | Sucessor correto |
|---|---:|---:|---:|
| LayoutLM pontual | 152 | 0,671 | 13,4% |
| LayoutLM sucessor | 152 | 0,720 | 38,2% |
| LayoutLM pontual | 3.235 | 0,786 | 20,8% |
| LayoutLM sucessor | 3.235 | 0,785 | **51,8%** |
| XY-cut (heurística) | — | 0,837 | 64,2% |

Com 3.235 páginas o τ empata com a versão pontual e a continuidade **dobra e meia**.
Detalhe de protocolo que custou uma rodada: o melhor checkpoint precisa ser escolhido
pelo τ de validação **medido com a mesma decodificação usada no teste**; selecionar pelo
τ do feixe escolhe outra época e derruba o resultado.

### 4.2 Kaggle: dois notebooks (`src/kaggle/montar_pacote.py`)

O pacote passou a levar todas as páginas extraídas (14 MB) e gera dois notebooks: um de
**treino** (curva das duas formulações, ablações, varredura do limiar, latência na T4,
avaliação contra o Golden) e o de **LLMs**. Ver [KAGGLE.md](KAGGLE.md).

### 4.3 A segmentação estava errada, e o erro era anterior à ordenação

Ao começar a anotar, o Pedro reparou em caixas ruins. A investigação separou dois
problemas que pareciam um só:

- **Não é defeito:** a fragmentação (mediana de 5 palavras por bloco). O Google Document
  AI, rodado pelo orientador sobre Japeri, produz a mesma distribuição (mediana 5, 22% de
  blocos de uma palavra). O cabeçalho de um diário é feito de muitas regiões pequenas.
- **É defeito, e grave:** 28,6% dos blocos se sobrepunham a outro, em 78% das páginas.
  Sobreposição de caixas é a assinatura de uma **linha cortada ao meio** cujas metades
  caíram em blocos diferentes, embaralhando o texto *dentro* do bloco — um teto sobre
  todos os métodos, que nenhuma ordenação desfaz.

Duas causas, as duas no critério de "onde cortar uma linha", que era um limiar de
distância (1,8 largura de caractere):

1. **entrada em negrito** ("**Art. 1º** Fica instituído…"): o corpo do parágrafo monta a
   linha primeiro e a entrada é rejeitada por uma folga que só existe enquanto ela está
   incompleta;
2. **texto justificado**: o espaço esticado entre palavras fica tão largo quanto uma
   calha estreita.

O conserto trocou o critério: a linha só é cortada onde passa uma **calha**, definida pela
consistência vertical (branca linha após linha), com limite **relativo** — num boletim
legislativo de três colunas a calha era cruzada por 13 de 142 linhas, mas a ocupação caía
de ~65 para 13. O agrupamento de linhas em blocos passou a ser restrito à coluna, e as
palavras cortadas por translineação são remontadas.

`src/data/reextrair.py` re-extrai **exatamente as mesmas páginas** de uma coleta (a lista
vem do próprio arquivo, em vez de re-amostrar), o que mantém o antes/depois comparável e
deixa as duas versões lado a lado para a análise de sensibilidade à granularidade
(`TCC_DIR_BLOCOS` aponta o pipeline inteiro para uma ou outra).

No lote do Golden: blocos sobrepostos 21,2% → 14,7%, blocos por página 34,8 → 31,3, e os
parágrafos remontados corretamente. O que resta está concentrado em poucas páginas de
tabela densa (88 dos 109 pares em 4 das 30 páginas).

**Consequência:** todos os números medidos antes desta correção precisam ser refeitos.

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
| Log da LLM "sumiu" | O nome do arquivo tinha `:` (de `llava:7b`); no Windows isso cria um *fluxo alternativo* do NTFS em vez de um arquivo | Nomes de log saneados; conteúdo resgatado do fluxo |
| LLM lenta, com latência inflada | `llava:7b` com contexto de 8.192 tokens não coube nos 6 GB: 34% das camadas rodaram na CPU | Registrado como ressalva; testar contexto menor e modelo de texto |
| Figura 2 mostrava uma página em que a ordem ingênua acertava | Critério de seleção restrito ao conjunto de teste | Seleção entre todos os veículos confiáveis, priorizando a maior discordância |
| LayoutLM subtreinado na rodada 1 | 152 páginas × 8 épocas = 152 passos | Rodada 2 com 40 épocas, e ablação com o mesmo orçamento |
| Validador de paleta da skill de visualização não rodou | Node.js não instalado | Usada a paleta de referência já validada, sem alterações |
| Coleta extra travou em Pernambuco (~50 s por PDF) | PDFs de PE muito densos para o `pdfplumber` | Interrompida em 525 de 1.089 PDFs (2.288 páginas); PR, RR e SC coletados à parte com amostra menor (70 PDFs × 5 páginas) |
| O comando que encerrava a coleta encerrou a si mesmo | O filtro por linha de comando casava com o próprio texto do comando no PowerShell | Filtrar os processos pelo nome `python.exe` antes de aplicar o padrão |
| "Teto" de frases preservadas abaixo de um método (51,8% × 53,4%) | A estimativa só considerava frases com no máximo uma emenda entre blocos | Estimativa descartada; relata-se a diferença para o piso e a fração preservada por algum método |
| A curva de aprendizado quebraria ao medir o primeiro modelo | `acerto_sucessor` criado em `metrics.py`, mas fora de `avaliar()` | Execução interrompida, função incluída em `avaliar()`, curva reiniciada |
| Modelo de sucessor com continuidade ótima e τ péssimo (0,44) | Decodificar o caminho inteiro pela matriz de sucessores: um salto errado entre colunas arruína tudo o que vem depois | Decodificação em cadeias: trechos locais de alta confiança ordenados pela cabeça de posição (τ 0,72) |
| Primeira rodada do modelo de sucessor escolheu a época errada | O melhor checkpoint era selecionado pelo τ da decodificação em feixe, e o teste usa a híbrida | Validar com a mesma decodificação do teste; rodada refeita |
| Texto embaralhado **dentro** do bloco (`Art. 1º rios, no âmbito…`) | Corte de linha por limiar de distância: a entrada em negrito é rejeitada por uma folga que só existe enquanto ela está incompleta, e o guloso de passada única nunca revisa | Corte só onde passa uma calha, detectada por consistência vertical |
| Parágrafo justificado picotado em 7 blocos | O espaço esticado da justificação fica tão largo quanto uma calha estreita | Mesmo conserto: a calha é branca linha após linha, o espaço esticado só naquela |
| Calhas não detectadas num boletim de 3 colunas | Limite absoluto de tolerância (4 de 142 linhas): a calha era cruzada por 13 títulos de largura total | Limite relativo — calha onde a ocupação cai abaixo de 25% da típica da página (de ~65 para 13) |
| Bloco largo engolindo linhas de outra coluna | O teste de sobreposição horizontal usava a largura do **menor**, então um bloco de página inteira aceitava qualquer linha estreita embaixo dele | Agrupamento de linhas em blocos restrito à coluna delimitada pelas calhas |
| Re-extrair com `extrator.py` tornaria o antes/depois incomparável | Ele re-amostra as páginas a cada execução | `src/data/reextrair.py`: a lista de páginas vem do próprio arquivo de entrada |

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
| Anotação **cega**, sem ordem sugerida | Pré-numerar com a XY-cut e só corrigir | A pré-numeração ancoraria o anotador na heurística e recriaria o viés que o Golden existe para eliminar; o laço por coluna compensa a velocidade |
| Golden com grupos `silver` e `incerto` (e Goiás depois) | Só páginas de Goiás, como no plano original | Cada grupo responde uma pergunta: validar a referência automática, decidir onde ela não existe e medir generalização fora do domínio |
| Kaggle com **Ollama** | vLLM; APIs pagas | Mesmo código e mesmo prompt da execução local, e gratuito; APIs pagas ficam como teto de desempenho |
| Latência do LayoutLM e da BiLSTM medida **sem os pesos treinados** no Kaggle | Levar o checkpoint de 450 MB | O tempo de inferência não depende dos valores dos pesos; o pacote fica com 2,2 MB |
| **Sucessor correto** como métrica adicional | Só τ e ARD | Mede a continuidade do texto, que é o que chega a um leitor ou a um RAG; revelou o problema da formulação pontual |
| Relevância do piloto de RI **por sobreposição de palavras** | Julgamentos de relevância manuais | Independe da ordem, então é a mesma para todos os métodos, e escala para centenas de consultas |
| Curva com subconjuntos **aninhados** | Amostras independentes por tamanho | O menor subconjunto é exatamente o treino original e cada ponto contém o anterior: menos variância entre pontos |
| LayoutLM prevendo **sucessor**, decodificado em cadeias | Seq2seq com ponteiro (LayoutReader); só a formulação pontual | Ataca diretamente a continuidade local, que é o que chega a um RAG, sem abrir mão do τ; o decodificador híbrido usa cada cabeça no que ela é boa |
| Viés geométrico **par a par** no escore de aresta | Só o produto interno dos vetores do LayoutLM | "Vem logo depois" é uma relação quase sempre geométrica: ou j está abaixo de i, ou i terminou a coluna e j abre a próxima. Fica como ablação |
| Corte de linha por **calha**, não por distância | Limiar de distância (versão anterior); limiar adaptado ao espaço da linha | Nenhum limiar de largura separa espaço justificado de calha estreita; a consistência vertical separa. Medido: 95% das folgas dentro de parágrafo cabem em 1,5 largura de caractere, mas a cauda ultrapassa qualquer limiar útil |
| Manter as **duas segmentações** lado a lado | Substituir a antiga e seguir | A granularidade vira variável controlada: se o ranking dos métodos mudar entre as duas, isso é resultado, não detalhe de implementação |
| Fragmentação **mantida** (blocos de 1 palavra) | Fundir blocos curtos vizinhos | É o que um detector real produz — o Google Document AI dá a mesma distribuição nos mesmos diários. Mexer nisso afastaria a entrada da premissa do trabalho |
