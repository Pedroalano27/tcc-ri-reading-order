# Metodologia Experimental

Desenho experimental do TCC, escrito para ser adaptado diretamente ao capítulo de
Metodologia. O código de cada etapa está indicado entre parênteses.

---

## 1. Formulação do problema

Uma página é um conjunto de blocos de texto $B = \{b_1, \dots, b_n\}$. Cada bloco tem
um texto $t_i$ e uma caixa delimitadora $(x_0, y_0, x_1, y_1)$ em coordenadas da
página. Os blocos chegam **sem ordem** — como na saída de um detector de layout.

**Detecção de ordem de leitura** é encontrar a permutação $\pi$ de $B$ que corresponde
à ordem em que um leitor humano percorre a página.

A tarefa é tratada como **ordenação (ranking)**: um modelo atribui um escore $s_i$ a
cada bloco e a ordem predita é a ordenação crescente dos escores. É a mesma estrutura
de um problema de *learning to rank* em Recuperação de Informação, com os blocos no
papel de documentos e a posição de leitura no papel da relevância.

## 2. Questões de pesquisa

| | Questão | Como é respondida |
|---|---|---|
| **QP1** | Quão grave é o problema de ordem de leitura nos Diários Oficiais? | Concordância entre a ordem ingênua e a de referência, por veículo (`caracterizar.py`) |
| **QP2** | Um modelo leve consciente de layout (LayoutLM) recupera a ordem a partir de texto e geometria? | τ de Kendall, sucessor correto e ARD no teste, contra heurísticas e BiLSTM |
| **QP3** | Quanto da eficácia vem da consciência de layout? | Ablação: LayoutLM com as caixas zeradas; BiLSTM só texto × só geometria |
| **QP4** | Uma LLM generativa resolve a tarefa? Com que confiabilidade de formato? | Eficácia e taxa de permutações válidas, zero-shot e few-shot, de 7B a 32B (`llm_ordem.py`) |
| **QP5** | Qual o trade-off entre eficácia e eficiência? | τ × latência por página, no mesmo hardware (figura 4, `latencia_hardware.py`) |
| **QP6** | A ordem de leitura muda o resultado da recuperação de informação? | Avaliação extrínseca: busca BM25 por páginas e por trechos e fidelidade do texto, em Japeri (`src/ri/piloto_japeri.py`) |
| **QP7** | Os resultados se sustentam contra a leitura humana? | Golden Dataset anotado (`src/anotacao/`, `avaliar_golden.py`) |

## 3. Dados

### 3.1 Acervo
4.644 PDFs de Diários Oficiais de 23 UFs e 8 municípios (2010–2026), cedidos pelo
orientador. Inventário e qualidade em [ACERVO.md](ACERVO.md). Excluído:
`official_diary_pi` (86% do texto ilegível).

### 3.2 Amostragem
Amostra estratificada por veículo, com semente fixa: até 14 PDFs × 4 páginas nos
veículos leves e 6 PDFs × 3 páginas nos veículos densos. A primeira página de cada
PDF (capa/expediente) é descartada.

Duas coletas adicionais, em pastas separadas para não alterar as partições do protocolo:

- **Curva de aprendizado** (`data/processed/blocos_extra/`, semente 7): 3.117 páginas
  extras dos mesmos 7 veículos de treino — até 6 páginas de cada PDF, e 5 páginas de 70
  PDFs em PR, RR e SC, cujos arquivos são mais pesados.
- **Piloto de RI** (`data/processed/blocos_ri_japeri/`): todas as páginas das 27 edições
  de Japeri, incluindo a capa (`--incluir-capa`).

### 3.3 Extração de blocos (`src/data/extrator.py`)
1. **Palavras** com `pdfplumber`, na ordem do fluxo de conteúdo
   (`use_text_flow=True`), após remover caracteres duplicados (negrito simulado) e
   descartar texto rotacionado e fora da área visível.
2. **Linhas**: palavras com sobreposição vertical ≥ 50% e distância horizontal ≤
   1,8 × a largura mediana de caractere. O limite impede que uma linha atravesse a
   calha entre colunas.
3. **Blocos**: linhas verticalmente adjacentes (distância ≤ 0,8 × altura mediana de
   linha), com sobreposição horizontal ≥ 50% e altura de fonte semelhante (±40%).
   Mudança de fonte inicia bloco novo (títulos separados do corpo).
4. **Filtros**: descartadas páginas com menos de 3 ou mais de 200 blocos, ou com
   mais de 5% de palavras ilegíveis.

Os identificadores dos blocos são atribuídos por permutação aleatória semeada, para
que nenhum identificador carregue informação de ordem.

### 3.4 Três ordens candidatas por página
| Ordem | Definição |
|---|---|
| `stream` | Ordem do **fluxo de conteúdo do PDF**: posição do primeiro caractere de cada bloco no fluxo. É a ordem em que o software de publicação escreveu o texto |
| `naive` | Ordenação por $(y_0, x_0)$: de cima para baixo, da esquerda para a direita |
| `xycut` | Heurística **XY-cut recursiva** (Nagy & Seth, 1984; Ha et al., 1995), descrita na seção 5 |

### 3.5 Rótulo de referência (silver)
Não há anotação manual em escala. A referência é a ordem **`stream`**, mas **apenas nos
veículos em que ela é confiável**: aqueles cuja concordância mediana com a XY-cut
atinge τ ≥ limiar (0,9 por padrão, relaxado até 0,7 se menos de 12 veículos se
qualificarem). O limiar efetivamente usado fica registrado em `splits.json`.

Por que decidir a confiabilidade **por veículo** e não por página: filtrar páginas
individuais pela concordância com a XY-cut selecionaria exatamente as páginas em que
a heurística acerta, e a tornaria imbatível no teste. Decidindo por veículo, as
páginas em que a XY-cut erra continuam no conjunto — e é nelas que um modelo
aprendido pode se diferenciar.

**Limitação assumida:** a ordem do fluxo é um rótulo *silver*. A avaliação definitiva
exige o **Golden Dataset** anotado manualmente (seção 3.6).

### 3.6 Golden Dataset (anotação humana)
A anotação manual é feita numa ferramenta local (`src/anotacao/`) que mostra a página
com os blocos **sem nenhuma ordem sugerida** e registra a sequência escolhida pelo
anotador, o tempo ativo gasto e marcações por página (tabela, ordem ambígua, erro de
segmentação). O protocolo completo, com as regras de leitura, está em
[GUIA_ANOTACAO.md](GUIA_ANOTACAO.md).

O primeiro lote, `golden_v1`, tem 30 páginas e 1.044 blocos em dois grupos:

| Grupo | Páginas | Função |
|---|---:|---|
| `silver` | 10, dos veículos de teste | Validar o rótulo automático usado em todos os resultados |
| `incerto` | 20, uma ou duas de cada veículo em que o fluxo do PDF não é confiável | Decidir quem acerta onde a referência automática não existe |

As páginas são sorteadas com semente fixa, em rodízio entre veículos e alternando
páginas de 1, 2 e 3+ colunas, com 6 a 80 blocos. Um lote de Goiás, fora do acervo, mede
generalização fora do domínio. Parte das páginas deve ser anotada por uma segunda
pessoa, para medir a concordância entre anotadores (o teto realista da tarefa).

## 4. Protocolo (`src/eval/protocolo.py`)

- **Divisão por veículo**: treino, validação e teste têm veículos disjuntos. O teste
  mede generalização para veículos cujo layout o modelo nunca viu.
  `official_diary_rj` é forçado no teste por ter saídas do Azure e do Google para
  comparação futura.
- **Entrada idêntica para todos os métodos**: os blocos de cada página chegam
  embaralhados por uma permutação determinística (semente = identificador da
  página). No treino, cada época usa uma permutação nova (aumento de dados).
- **Mesma referência** para todos os métodos.
- **Treino ampliado** (curva de aprendizado): `montar_treino()` junta as páginas extras
  às do protocolo em subconjuntos **aninhados** — o de 152 páginas é exatamente o treino
  original, e cada tamanho maior contém o anterior. Validação e teste não mudam.

## 5. Métodos comparados

### 5.1 Não aprendidos (`src/eval/baselines.py`)
- **Ordem do detector**: devolve a entrada como chegou. Piso da comparação.
- **Ingênua**: ordena por $(y_0, x_0)$. Em páginas multicolunas, intercala as colunas.
- **XY-cut recursiva**, aplicada a um grupo de blocos:
  1. Procura **calhas verticais** (faixas de x sem nenhum bloco, ≥ 4 pt). Se houver,
     divide em colunas e ordena cada coluna recursivamente, da esquerda para a direita.
     Colunas com menos de 12% da largura do grupo são fundidas à vizinha (evita tratar
     a numeração de artigos na margem como coluna).
  2. Senão, trata os blocos **largos** (≥ 60% da largura do grupo — cabeçalhos,
     títulos) como **separadores de seção**; ordena recursivamente cada seção entre
     eles, de cima para baixo.
  3. Senão, ordena por $(y_0, x_0)$.

### 5.2 BiLSTM (`src/models/lstm_ordem.py`)
Cada bloco vira um vetor de características; uma BiLSTM de 2 camadas (128 unidades por
direção) percorre os blocos na ordem de entrada e produz um escore por bloco.
Três variantes isolam as fontes de informação:
- **texto**: saco de palavras com *hashing* (2¹⁸ baldes, dimensão 64) — sem geometria;
- **geometria**: 8 características da caixa normalizada — sem texto;
- **texto + geometria**.

### 5.3 LayoutLM (`src/models/layoutlm_ordem.py`)
- **Modelo base:** `microsoft/layoutlm-base-uncased` (Xu et al., 2020), 113 M de
  parâmetros, com *embeddings* de posição 2D.
- **Entrada:** cada bloco contribui com seus primeiros $K$ tokens WordPiece
  ($K = \min(8, \lfloor 510/n \rfloor)$), todos com a caixa do bloco normalizada para
  0–1000.
- **Saída:** média dos estados ocultos dos tokens de cada bloco → MLP
  (768 → 256 → 1) → escore.
- **Treino:** *learning to rank* pontual — alvo $r_i/(n-1)$, a posição normalizada do
  bloco na referência, com perda MSE. AdamW (lr 4·10⁻⁵ no codificador, 10⁻³ na
  cabeça), aquecimento linear de 6%, lote efetivo de 8 páginas (micro-lote de 4 com
  acumulação), precisão mista fp16, recorte de gradiente em 1,0. Seleção do modelo
  pelo melhor τ na validação.
- **Ablação sem layout:** mesmas condições com todas as caixas zeradas.

### 5.4 LLMs generativas (`src/eval/llm_ordem.py`)
- **Modelos:** `llava:7b`, local, na primeira rodada; Qwen 2.5 de 7B, 14B e 32B via
  Ollama numa GPU T4 do Kaggle ([KAGGLE.md](KAGGLE.md)), com o mesmo código e o mesmo
  prompt.
- **Prompt:** instruções de leitura em português + blocos rotulados B1…Bn na ordem de
  entrada, com a caixa normalizada 0–1000 e as 12 primeiras palavras. Saída forçada a
  JSON (`format="json"`), temperatura 0, semente fixa.
- **Few-shot:** $K$ exemplos resolvidos de páginas de **treino** (6 a 16 blocos, de
  preferência multicoluna), como turnos usuário/assistente antes da página. Nenhuma
  página de teste ou do Golden é usada como exemplo.
- **Janela de contexto** única por execução, calculada pela maior página (trocar a
  janela faz o Ollama recarregar o modelo, o que contaminaria a latência).
- **Confiabilidade de formato:** mede-se a fração de respostas que são permutações
  válidas. Respostas inválidas são **reparadas** (ids inexistentes e repetidos
  removidos; faltantes anexados ao fim) e sinalizadas.
- **Páginas:** a primeira rodada usou só as páginas de teste com até 25 blocos (15); as
  rodadas no Kaggle usam as 95 páginas de teste e as 30 do Golden.
- **Rastreabilidade:** cada execução registra modelo, GPU, versão do Ollama, janela de
  contexto e tempos em `execucoes_llm.jsonl`; uma execução interrompida é retomada de
  onde parou.

## 6. Métricas (`src/eval/metrics.py`)

Seja $\pi$ a ordem predita, $\pi^*$ a de referência e $n$ o número de blocos.

| Métrica | Definição | Leitura |
|---|---|---|
| **τ de Kendall** | $\tau = \frac{C - D}{\binom{n}{2}}$, com $C$ e $D$ os pares concordantes e discordantes | 1 = ordem idêntica, 0 = sem relação, −1 = invertida. **Métrica principal** |
| **Sucessor correto** | fração dos pares consecutivos de $\pi$ que também são consecutivos em $\pi^*$ | Continuidade local do texto: o que chega a um leitor, a um trecho de busca ou a um RAG |
| **ARD** | $\frac{1}{n}\sum_{k} \lvert k - \mathrm{pos}_\pi(\pi^*_k)\rvert$, com penalidade $n$ para elemento ausente (Wang et al., 2021) | Deslocamento médio em posições; 0 = perfeito |
| **ARD normalizado** | ARD / $n$ | Comparável entre páginas de tamanhos diferentes |
| **BLEU de página** | BLEU (sacrebleu) do texto da página reconstruído na ordem predita contra a ordem de referência | Ver ressalva abaixo |
| **Acerto exato** | 1 se $\pi = \pi^*$ | Fração de páginas perfeitas |
| **Latência** | Tempo de parede por página, da entrada à ordem (inclui tokenização nos modelos neurais) | Eixo de eficiência |

**Ressalva sobre o BLEU.** Na granularidade de bloco, a maioria dos n-gramas é interna
aos blocos e se preserva em qualquer ordenação. Numa página completamente invertida o
BLEU ainda marca 82,7 (teste controlado em `metrics.py`). O BLEU é reportado por
continuidade com a literatura, mas **as conclusões se apoiam no τ, no sucessor correto e
no ARD**. No LayoutReader, onde a unidade é a palavra, o BLEU é bem mais discriminativo.

**Por que o sucessor correto.** O τ mede a ordem global: trocar dois vizinhos custa um
único par discordante, mas desfaz até três emendas do texto. Um método pode ter τ alto e
entregar o texto picotado — é o caso dos modelos com escore pontual (resultados, seção
4.8). Para os usos de RI (trechos, citações, RAG), a continuidade é o que importa.

**Por que não a "fração de blocos fora de posição":** sofre de efeito cascata — um
único bloco deslocado no início desloca todos os seguintes (ver
[DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md), correção 1).

## 7. Análise estatística

- **Intervalo de confiança de 95%** da média do τ por *bootstrap* (2.000 reamostragens
  de páginas).
- **Pior caso**: percentil 10 do τ por página. Um método bom na média pode falhar de
  forma catastrófica em algumas páginas — a preocupação central de Rodrigues et al.
  (SIGIR 2022) com modelos neurais de ranking.
- **Teste de Wilcoxon pareado** (τ por página) entre o LayoutLM e cada outro método, e
  entre a XY-cut e cada LLM.

## 8. Avaliação extrínseca: efeito na recuperação (`src/ri/piloto_japeri.py`)

A avaliação intrínseca (seção 6) mede a ordem; a extrínseca mede o que muda para um
sistema de RI que indexa o texto extraído.

- **Coleção:** todas as 269 páginas das 27 edições de Japeri, um veículo em que o fluxo
  do PDF não concorda com a XY-cut. O texto de cada página é montado na ordem de cada
  método.
- **Consultas e relevância:** os 421 atos de `json_atos_japeri` trazem o texto em ordem
  correta. De cada ato com a edição no acervo saem até três consultas: uma **frase** de 12
  palavras seguidas do corpo (a de maior IDF), o **título** (primeira linha) e os 8
  **termos** mais raros. É relevante a página que contém ao menos 90% das palavras da
  consulta (75% no caso dos termos). Como a relevância usa só sobreposição de palavras, ela
  independe da ordem e é a mesma para todos os métodos.
- **Busca:** BM25 ($k_1 = 1{,}2$, $b = 0{,}75$) com a página inteira como documento
  (controle: o saco de palavras não depende da ordem) e com trechos de 100 palavras, passo
  50, como num RAG; a página vale o seu melhor trecho. Medidas: MRR@10, Recall@1, Recall@5.
- **Fidelidade do texto:** fração das frases de 12 palavras dos atos que chegam ao texto
  da página com ao menos 10 palavras alinhadas; e **contexto para RAG**, a fração das
  consultas-frase cujo primeiro trecho devolvido contém a frase preservada.

## 9. Eficiência no mesmo hardware (`src/eval/latencia_hardware.py`)

Latência só é comparável na mesma máquina. O mesmo roteiro mede ingênua, XY-cut e
BiLSTM (CPU) e LayoutLM (GPU, batch 1, tokenização incluída) no notebook e na T4 do
Kaggle, onde também rodam as LLMs. O tempo de inferência não depende dos valores dos
pesos, então a medição usa a mesma arquitetura mesmo sem o checkpoint treinado. Cada
página é medida em três passadas e fica a mediana.

## 10. Ameaças à validade

| Ameaça | Efeito | Mitigação atual / planejada |
|---|---|---|
| Referência *silver* (fluxo do PDF) | O fluxo pode divergir da leitura humana mesmo em veículos "confiáveis" | Confiabilidade por veículo; grupo `silver` do Golden mede a concordância com humanos |
| Concordância com a XY-cut define os veículos confiáveis | Favorece layouts em que a heurística funciona | Critério por veículo, não por página; grupo `incerto` do Golden avalia os veículos excluídos |
| Anotador ancorado numa ordem automática | Golden enviesado a favor de um método | Ferramenta sem ordem sugerida; identificadores embaralhados; concordância entre anotadores |
| Tokenizador do LayoutLM em inglês sem acentos | Texto em português fragmentado em muitos sub-tokens | Testar LayoutXLM (multilíngue) |
| Granularidade de bloco depende da heurística de segmentação | Blocos grandes demais tornam a tarefa mais fácil | Relatar número médio de blocos; marcação de erro de segmentação na anotação |
| Amostra reduzida nos veículos densos | Menos páginas desses layouts no treino | Coleta extra para a curva; extração mais rápida com PyMuPDF |
| `llava:7b` é multimodal, não especializada em texto | Subestima a capacidade das LLMs | Qwen 2.5 de 7B a 32B no Kaggle, zero-shot e few-shot |
| Hardware diferente entre métodos | Latências incomparáveis | Todos os métodos medidos também na T4 do Kaggle (seção 9) |
| Origem dos atos de Japeri incerta (manual ou Azure) | A referência do piloto de RI pode ser silver | Confirmar com o orientador; a relevância só usa sobreposição de palavras |
