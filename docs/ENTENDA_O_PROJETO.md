# Entenda o projeto, do zero

Este documento explica **o que estamos fazendo, por que, e o que cada coisa significa**.
A ideia é você ler uma vez de ponta a ponta e depois consultar em pedaços. Todo termo
técnico é explicado na primeira vez que aparece, e há um glossário no fim.

Os outros documentos são complementares:
[METODOLOGIA.md](METODOLOGIA.md) descreve o desenho experimental em linguagem de artigo,
[RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md) traz os números,
[DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md) o histórico com os erros do caminho e
[ROADMAP.md](ROADMAP.md) o que falta fazer.

**Sumário**

1. [O problema em uma página](#1-o-problema-em-uma-página)
2. [As dez palavras que aparecem o tempo todo](#2-as-dez-palavras-que-aparecem-o-tempo-todo)
3. [Os dados: de PDF a blocos](#3-os-dados-de-pdf-a-blocos)
4. [A referência: contra o que comparamos](#4-a-referência-contra-o-que-comparamos)
5. [Os métodos, um a um](#5-os-métodos-um-a-um)
6. [As métricas, com exemplos](#6-as-métricas-com-exemplos)
7. [O protocolo: as regras do jogo](#7-o-protocolo-as-regras-do-jogo)
8. [O que já sabemos](#8-o-que-já-sabemos)
9. [O que existe no repositório](#9-o-que-existe-no-repositório)
10. [O que fazer a seguir, e por quê](#10-o-que-fazer-a-seguir-e-por-quê)
11. [Perguntas que você pode ter](#11-perguntas-que-você-pode-ter)
12. [Como isso vira o texto do TCC](#12-como-isso-vira-o-texto-do-tcc)
13. [Glossário](#13-glossário)

---

## 1. O problema em uma página

Um PDF de diário oficial não guarda "um texto". Ele guarda **pedaços de texto com
coordenadas**: "este trecho começa no ponto x=57, y=210 da página". Quem monta o arquivo
(o software de diagramação da imprensa oficial) escreve esses pedaços na ordem que lhe
convém — que não é necessariamente a ordem em que uma pessoa lê.

Quando a página tem **duas ou três colunas**, isso vira um problema sério. Se você
simplesmente pegar os pedaços e ordenar de cima para baixo, o texto pula de uma coluna
para a outra no meio da frase:

```
Ordem correta:      "Fica nomeado o servidor João da Silva para o cargo de Assessor..."
Ordem por altura:   "Fica nomeado o servidor   PORTARIA Nº 42 — O Secretário, no uso..."
                     João da Silva para...     ...resolve exonerar..."
```

O texto resultante tem todas as palavras, mas **não faz sentido em sequência**.

**Por que isso importa para o TCC.** O trabalho é da área de Recuperação de Informação
(RI). Um sistema de busca, ou um RAG (busca que alimenta uma LLM para responder
perguntas), consome esse texto. Se ele chega picotado:

- os **trechos** que um RAG entrega à LLM misturam dois assuntos;
- **buscas por frase exata** falham ("pregão eletrônico nº 18/CPL/2023");
- a **segmentação em atos** (onde começa e termina cada portaria) sai errada;
- a **citação** mostrada ao usuário aparece truncada.

**Detecção de ordem de leitura** é a tarefa de, dado o conjunto de pedaços sem ordem,
descobrir a sequência em que um humano leria a página. É o objeto do TCC.

---

## 2. As dez palavras que aparecem o tempo todo

| Palavra | O que quer dizer aqui |
|---|---|
| **Bloco** | Um pedaço de texto da página, tipicamente um parágrafo ou um trecho de coluna, com sua caixa de coordenadas. É a unidade que ordenamos. Uma página tem de 3 a 200 blocos; a média no nosso material é cerca de 35. |
| **Bounding box** | A caixa retangular do bloco: `[x0, y0, x1, y1]`, em pontos da página (1 ponto = 1/72 de polegada). O `y` cresce **para baixo**. |
| **Ordem de leitura** | A sequência dos blocos como uma pessoa leria. É uma **permutação**: a mesma lista de blocos, em outra ordem. |
| **Veículo** | Cada fonte de diário: um estado (CE, MA) ou um município (Japeri, Salvador). Cada veículo tem seu layout, repetido por anos. |
| **Método** | Qualquer coisa que receba blocos sem ordem e devolva uma ordem: heurística, modelo treinado ou LLM. |
| **Referência** | A ordem considerada correta na hora de medir. Pode ser automática (*silver*) ou anotada por humano (*gold*). |
| **τ (tau) de Kendall** | A métrica principal: o quanto a ordem predita concorda com a referência. Vai de −1 (invertida) a 1 (idêntica). |
| **Baseline** | Método simples de comparação. Se o modelo sofisticado não bate o baseline, ele não se justifica. |
| **Ablação** | Experimento em que se **remove** um ingrediente do modelo, para medir quanto ele contribuía. |
| **Latência** | Tempo para ordenar uma página. É o eixo de eficiência do trade-off que o TCC estuda. |

---

## 3. Os dados: de PDF a blocos

### 3.1 O acervo

O orientador cedeu **4.644 PDFs** de diários oficiais, cerca de **310 mil páginas**, de 23
estados e 8 municípios, de 2010 a 2026 (inventário em [ACERVO.md](ACERVO.md)). Dois fatos
importantes:

- **Cerca de 96% são PDFs digitais**, ou seja, têm camada de texto com coordenadas. Não
  precisamos de OCR (o reconhecimento óptico que lê texto de imagem). É isso que permite
  rodar o projeto inteiro num notebook.
- **Goiás não está no acervo.** Daí a ideia de usar Goiás como teste "fora do domínio":
  um layout que nenhum modelo viu.

### 3.2 Como um PDF vira dados (`src/data/extrator.py`)

O caminho é PDF → palavras → linhas → blocos:

1. **Palavras.** A biblioteca `pdfplumber` devolve cada palavra com sua caixa. Duas
   sutilezas custaram tempo:
   - o modo padrão dela **já reordena** as palavras geometricamente; para saber a ordem
     real em que o arquivo foi escrito é preciso pedir `use_text_flow=True`;
   - alguns diários imprimem o texto duas vezes para simular negrito, o que duplica
     palavras — daí o `dedupe_chars`.
2. **Linhas.** Palavras que se sobrepõem verticalmente e estão próximas na horizontal
   viram uma linha. O limite de distância é **1,8 vez a largura média de um caractere**.
   Esse detalhe existe para a linha **não atravessar a calha** (o espaço em branco entre
   duas colunas) e juntar texto de colunas diferentes.
3. **Blocos.** Linhas logo abaixo umas das outras, com sobreposição horizontal e altura de
   fonte parecida, viram um bloco. Mudança de tamanho de fonte começa bloco novo, o que
   separa títulos do corpo.
4. **Filtros.** Descartamos páginas com menos de 3 ou mais de 200 blocos, e páginas com
   mais de 5% de caracteres ilegíveis (o `(cid:N)` que aparece quando a fonte não informa
   o mapeamento para caracteres).

Cada bloco recebe um **identificador embaralhado** (`b0`, `b17`, …, sorteados com semente
fixa). Isso é de propósito: nenhum método pode adivinhar a ordem pelo nome do bloco.

### 3.3 As três ordens que o extrator já calcula

Para cada página guardamos três ordens candidatas, que aparecem o tempo todo:

| Nome | O que é |
|---|---|
| `stream` | A ordem do **fluxo do arquivo**: a sequência em que o software de publicação escreveu o texto. |
| `naive` | Ordenar por `(y, x)`: de cima para baixo, da esquerda para a direita. É o que muitos pipelines fazem por padrão. |
| `xycut` | A saída da heurística XY-cut (seção 5.3), que entende colunas. |

### 3.4 As coletas que existem hoje

| Pasta | O que tem | Para quê |
|---|---|---|
| `data/processed/blocos/` | 777 páginas de 30 veículos | Caracterização e experimento principal (treino, validação, teste) |
| `data/processed/blocos_extra/` | 3.117 páginas dos 7 veículos de treino | Curva de aprendizado (efeito de mais dados) |
| `data/processed/blocos_ri_japeri/` | 269 páginas: todas as páginas das 27 edições de Japeri | Piloto de recuperação de informação |
| `data/golden/golden_v1/` | 30 páginas para anotar à mão | Avaliação definitiva |

---

## 4. A referência: contra o que comparamos

Para medir se um método acertou é preciso saber qual é a ordem certa. Aí está o nó do
projeto: **ninguém nos deu a resposta**.

### 4.1 Rótulo *silver* e rótulo *gold*

- **Gold** (padrão-ouro): a ordem anotada por uma pessoa. É a verdade, mas custa tempo.
- **Silver** (prata): uma aproximação automática, boa o bastante para treinar e comparar,
  mas com erros conhecidos.

Nossa referência silver é a ordem `stream`, o fluxo do arquivo. A intuição: em muitos
diários, o software escreve o texto na mesma ordem em que ele é lido.

### 4.2 O problema: o fluxo do PDF só é confiável em um terço dos veículos

Medimos, veículo por veículo, o quanto o fluxo do arquivo concorda com a XY-cut. Resultado:
**em apenas 11 dos 30 veículos** essa concordância é alta (τ mediano ≥ 0,7). Em veículos de
coluna única, onde ler é trivialmente de cima para baixo, o fluxo ainda discorda — Manaus
(τ 0,33), Congonhas (0,33), Curitiba (0,57).

Por isso a referência silver **só é usada nos 11 veículos confiáveis**, e é neles que
treinamos e testamos. Os outros 19 ficam fora do experimento principal — e são justamente
o alvo da anotação manual.

### 4.3 O viés que isso cria (e que precisa estar no texto do TCC)

A confiabilidade foi decidida **comparando o fluxo com a XY-cut**. Ou seja: escolhemos
para o teste os veículos em que a XY-cut concorda com a referência. Isso favorece a
XY-cut. Duas mitigações:

- a decisão é **por veículo, não por página** — assim, dentro de um veículo confiável, as
  páginas em que a heurística erra continuam no teste;
- o **Golden Dataset** anotado à mão elimina o viés de vez. É por isso que anotar as 30
  páginas é a tarefa mais valiosa da lista.

### 4.4 O Golden Dataset (`data/golden/golden_v1`)

30 páginas, 1.044 blocos, em dois grupos:

| Grupo | Páginas | Pergunta que responde |
|---|---:|---|
| `silver` | 10, dos veículos de teste | A referência automática concorda com um humano? Se sim, tudo o que medimos até aqui se sustenta. |
| `incerto` | 20, dos veículos não confiáveis | Onde hoje não sabemos quem acerta, quem acerta? |

A ferramenta de anotação (`src/anotacao/`) mostra a página com os blocos **sem nenhuma
ordem sugerida**. Se ela sugerisse a ordem da XY-cut para você "só corrigir", você seria
puxado para a resposta da heurística e o Golden nasceria viciado. As regras de leitura
estão em [GUIA_ANOTACAO.md](GUIA_ANOTACAO.md).

---

## 5. Os métodos, um a um

Todos recebem exatamente a mesma coisa: os blocos de uma página, **embaralhados**, com
texto e coordenadas. Todos devolvem uma ordem.

### 5.1 Ordem do detector (o piso)

Devolve os blocos como chegaram, ou seja, embaralhados. Serve para saber quanto vale "não
fazer nada": τ ≈ 0. Todo método precisa ficar bem acima disso.

### 5.2 Ingênua

Ordena por `(y, x)`: de cima para baixo e, empatando a altura, da esquerda para a direita.
É o baseline honesto — é o que um pipeline faria sem pensar. Em página de coluna única,
acerta quase tudo; em multicoluna, intercala as colunas.

### 5.3 XY-cut (a heurística que hoje ganha)

Algoritmo clássico de análise de documentos (Nagy & Seth, 1984). A ideia é **cortar a
página recursivamente**:

1. Procure **calhas verticais**: faixas de largura ≥ 4 pontos onde nenhum bloco encosta.
   Se existirem, a página tem colunas: divida ali, ordene cada coluna recursivamente e
   concatene da esquerda para a direita.
2. Se não houver calha, procure **blocos largos** (≥ 60% da largura do grupo). Um título
   que atravessa a página funciona como **separador de seções**: ordene o que está acima
   dele, depois ele, depois o que está abaixo.
3. Se nada disso valer, ordene por `(y, x)`.

Duas proteções foram necessárias: colunas estreitas demais (menos de 12% da largura) são
fundidas com a vizinha, senão a numeração de artigos na margem virava "coluna".

É rápida (0,14 ms por página), não precisa de treino e é, hoje, o método a bater.

### 5.4 BiLSTM (o baseline de rede neural "antiga")

**LSTM** é um tipo de rede recorrente: percorre uma sequência item a item carregando uma
"memória" que decide o que guardar e o que esquecer. **BiLSTM** são duas passadas, uma
para frente e outra para trás, concatenadas, para que cada bloco enxergue o contexto dos
dois lados. Aqui ela percorre os blocos embaralhados e dá **uma nota** a cada um; ordenar
pelas notas dá a ordem predita.

Três variantes, para isolar de onde vem a informação:

- **só texto**: cada bloco vira um saco de palavras codificado por *hashing* (cada palavra
  cai num de 2¹⁸ baldes, e os vetores são somados). Sem coordenadas.
- **só geometria**: 8 números da caixa (posições, largura, altura, centro). Sem texto.
- **texto + geometria**.

### 5.5 LayoutLM (o modelo central do TCC)

Três camadas de conceito, de fora para dentro:

- **Transformer**: arquitetura em que cada pedaço de texto (token) "olha" para todos os
  outros e decide de quem depende. É a base de praticamente todo modelo de linguagem atual.
- **BERT**: um transformer pré-treinado a adivinhar palavras escondidas em textos. Dele sai
  um vetor por token, que carrega o significado no contexto.
- **LayoutLM** (Xu et al., 2020): um BERT que, além do texto, recebe **as coordenadas de
  cada token** — quatro tabelas de posição 2D (x0, y0, x1, y1), com as caixas normalizadas
  para a escala 0–1000. Ele enxerga a geometria da página nativamente. Tem 113 milhões de
  parâmetros: é pequeno perto de uma LLM e roda tranquilo na RTX 4050.

**Como usamos.** Formulamos a tarefa como *learning to rank* pontual — o mesmo esquema do
ranqueamento de documentos em RI:

- cada bloco entra com seus primeiros tokens, todos marcados com a caixa do bloco;
- a saída de cada bloco (média dos vetores dos seus tokens) passa por uma pequena rede que
  produz **uma nota**;
- o alvo da nota é a posição normalizada do bloco na referência: numa página de 10 blocos,
  o primeiro vale 0,0; o último, 1,0; o do meio, 0,5;
- a perda é o **erro quadrático médio** (MSE) entre a nota prevista e esse alvo;
- ordenar pelas notas dá a ordem.

"Pontual" (*pointwise*) quer dizer que cada bloco é pontuado sozinho. As alternativas
seriam **par a par** (dado o par A e B, quem vem antes?) ou **em lista** (gerar a sequência
inteira, como faz o LayoutReader, com um decodificador). Guarde isso: a seção 8.5 mostra
que essa escolha é hoje o principal limite do modelo.

**Ablação sem layout.** O mesmo treino com **todas as caixas zeradas**. Se o desempenho
despenca, é porque a geometria é o que resolve a tarefa — e é exatamente o que acontece.

**Palavras de treino que você vai ver:**

| Termo | Significado |
|---|---|
| *Fine-tuning* | Continuar o treino de um modelo já pré-treinado, agora na nossa tarefa. |
| Época | Uma passada por todas as páginas de treino. |
| Lote (*batch*) | Quantas páginas o modelo vê antes de ajustar os pesos. |
| Taxa de aprendizado | O tamanho do passo do ajuste. Grande demais desestabiliza; pequena demais não sai do lugar. |
| fp16 | Fazer as contas com números de 16 bits: metade da memória e mais velocidade. |
| Validação | Conjunto separado, usado para escolher o melhor momento de parar. Nunca é o teste. |

### 5.6 LLM generativa via Ollama

Uma **LLM** (modelo de linguagem grande) prevê a próxima palavra e, com isso, responde,
resume, ordena. **Ollama** é o programa que roda uma LLM na sua própria máquina.

Damos à LLM a lista de blocos embaralhados, rotulados `B1`…`Bn`, com as coordenadas e o
começo do texto, e pedimos um JSON com a ordem de leitura. Conceitos envolvidos:

| Termo | Significado |
|---|---|
| *Zero-shot* | Só a instrução, sem exemplos resolvidos. |
| *Few-shot* | A instrução mais alguns exemplos resolvidos no próprio prompt. Usamos páginas de **treino**, nunca de teste. |
| Temperatura 0 | Escolher sempre a palavra mais provável: saída estável e reprodutível. |
| Janela de contexto | Quantos tokens o modelo vê de uma vez. Página grande exige janela grande, e janela grande consome memória de GPU. |
| Permutação válida | A resposta traz cada bloco exatamente uma vez. Quando não traz, reparamos (removendo repetidos, anexando os que faltam) e registramos a falha: essa taxa é um resultado por si só. |

Rodamos o `llava:7b`, que estava instalado, mas é um modelo **multimodal**, feito para
imagens — e ele foi mal. Por isso o pacote do Kaggle: rodar Qwen 2.5 de 7B, 14B e 32B, que
são modelos de **texto** e não cabem nos 6 GB da sua placa.

---

## 6. As métricas, com exemplos

Use este exemplo em tudo o que vem a seguir. Referência: **A B C D**. Predição: **A C B D**
(trocamos os dois do meio).

### 6.1 τ de Kendall — a métrica principal

Olhe todos os **pares** de blocos (são 6: AB, AC, AD, BC, BD, CD) e conte em quantos as
duas ordens concordam sobre quem vem primeiro. Aqui só o par (B, C) está invertido:

> τ = (concordantes − discordantes) / total = (5 − 1) / 6 = **0,667**

Por que τ e não "quantos blocos estão na posição exata"? Porque essa segunda medida sofre
**efeito cascata**: um bloco deslocado no começo empurra todos os outros e a página inteira
conta como errada. Foi assim que, no diagnóstico inicial, apareceu um "86% de desordem"
que estava inflado e teve de ser retirado.

### 6.2 Sucessor correto — a métrica que criamos aqui

Conte quantos blocos são seguidos, na predição, **pelo mesmo bloco que os segue na
referência**. Na predição A C B D, os pares seguidos são (A,C), (C,B) e (B,D); na
referência, os corretos são (A,B), (B,C) e (C,D). Nenhum coincide:

> Sucessor correto = **0%** — com τ de 0,667.

Esse exemplo é o coração de uma das descobertas do projeto: **τ alto não garante texto
legível**. Trocar dois vizinhos custa um par no τ, mas desfaz até três emendas do texto. E
é a emenda que importa para busca por trechos, citação e RAG.

### 6.3 ARD (*Average Relative Distance*)

Média de quantas posições cada bloco andou. No exemplo, B foi da posição 1 para a 2, C da 2
para a 1, A e D ficaram: ARD = (0+1+1+0)/4 = **0,5**. O **ARD normalizado** divide pelo
número de blocos, para comparar páginas de tamanhos diferentes. Vem do LayoutReader, o
trabalho de referência da área.

### 6.4 BLEU de página — reportado, mas não confiável aqui

O BLEU compara sequências de palavras (n-gramas) entre o texto reconstruído e o texto de
referência. O problema: como ordenamos **blocos**, quase todos os n-gramas ficam **dentro**
de um bloco e sobrevivem a qualquer reordenação. Numa página completamente invertida o
BLEU ainda marca **82,7**, e uma ordem aleatória marca 94,2. Ele é reportado por
continuidade com a literatura, mas não sustenta conclusão.

### 6.5 Acerto exato e latência

**Acerto exato**: a página saiu perfeita (1) ou não (0). É severo — a XY-cut acerta 18,9%
das páginas inteiras. **Latência**: milissegundos por página, medidos do jeito mais honesto
possível, incluindo a tokenização, uma página por vez.

### 6.6 A estatística: por que não basta a média

- **Intervalo de confiança de 95% (bootstrap).** Sorteamos 2.000 vezes uma amostra de
  páginas do mesmo tamanho (com repetição) e recalculamos a média. O intervalo entre o
  percentil 2,5 e o 97,5 dessas médias é o IC. Ele responde: "se eu tivesse pegado outras
  95 páginas, quanto o número poderia mudar?".
- **Pior caso (p10).** O valor abaixo do qual estão as 10% piores páginas. Um método pode
  ir bem na média e falhar feio em algumas páginas — e num sistema real são essas que
  chegam ao suporte.
- **Teste de Wilcoxon pareado.** Compara dois métodos página a página e devolve um
  **p-valor**: a chance de ver uma diferença desse tamanho se, na verdade, os dois fossem
  equivalentes. Abaixo de 0,05, dizemos que a diferença é significativa.

---

## 7. O protocolo: as regras do jogo

Estas regras existem para que a comparação seja justa; elas são metade da metodologia do
TCC.

1. **Todos recebem a mesma entrada.** Os blocos chegam embaralhados por uma permutação fixa
   por página (a semente é o identificador da página). Assim a ordem de entrada não carrega
   informação: o método só pode acertar olhando texto e geometria.
2. **Divisão por veículo, nunca por página.** Treino: Volta Redonda, Salvador, PA, PE, PR,
   RR e SC (152 páginas). Validação: RN (15). Teste: CE, MA e RJ (95). Se dividíssemos as
   páginas ao acaso, o mesmo layout apareceria no treino e no teste, o modelo decoraria o
   template e as métricas ficariam infladas.
3. **Mesma referência para todos.**
4. **Sementes fixas** em tudo o que sorteia: amostragem, embaralhamento, bootstrap.
5. **Nada de olhar o teste** para tomar decisões. Quem decide quando parar o treino é a
   validação.

---

## 8. O que já sabemos

Os números completos estão em [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md).
Aqui vai a leitura de cada achado.

### 8.1 O problema existe mesmo em PDF digital

Em 19 dos 30 veículos, a ordem interna do arquivo não é a ordem de leitura. Isso derruba a
saída fácil ("é só usar o texto do PDF") e justifica o trabalho.

### 8.2 A heurística é o método a bater

No teste de 95 páginas:

| Método | τ | Pior caso (p10) | Sucessor correto | Latência |
|---|---:|---:|---:|---:|
| XY-cut | **0,837** | 0,496 | 64,2% | 0,14 ms |
| Ingênua | 0,753 | 0,347 | 52,5% | 0,015 ms |
| BiLSTM (geometria) | 0,731 | 0,459 | 27,1% | 7,1 ms |
| LayoutLM | 0,671 | 0,345 | 13,4% | 18 ms |
| LLM llava:7b | 0,099 | −0,333 | 8,5% | 8.415 ms |
| Sem ordenar | −0,005 | −0,200 | 4,8% | — |

A linha da LLM vem do subconjunto de 15 páginas pequenas em que ela foi avaliada; as
demais, das 95 páginas de teste.

Isso não é vergonha: é resultado. Em layouts regulares, regra geométrica é forte, e a
literatura diz o mesmo. A pergunta do TCC vira "**em que páginas, e a que custo**, um
modelo aprendido supera a heurística".

### 8.3 A geometria é o que resolve a tarefa

Com as caixas zeradas, o LayoutLM cai de τ 0,671 para 0,122; a BiLSTM só com texto fica em
0,066. É a evidência mais limpa a favor da premissa do trabalho — e é o tipo de resultado
que uma ablação existe para produzir.

### 8.4 A LLM pequena falhou, e o modo de falha é interessante

O `llava:7b` ficou em τ 0,099. O detalhe revelador: a ordem que ele devolve tem τ mediano
de **0,905 com a ordem em que os blocos chegaram** e 0,121 com a correta. Ou seja, ele
**copia a entrada** em vez de raciocinar sobre as coordenadas. Além disso, uma em cada
cinco respostas nem era uma permutação válida, e cada página levou 8,4 segundos.

Ressalvas honestas: é um modelo multimodal, pequeno, que não coube inteiro na GPU. É
exatamente por isso que existe o pacote do Kaggle.

### 8.5 O τ escondia o problema do LayoutLM

O LayoutLM tem τ 0,671, mas só **13,4%** de sucessores corretos, contra 64,2% da XY-cut.
Ele sabe mais ou menos onde cada bloco fica e troca vizinhos o tempo todo. A causa provável
é a formulação pontual: dois blocos vizinhos na mesma coluna recebem notas quase iguais, e
qualquer ruído os inverte.

Consequência prática: para RI, o que importa é a continuidade, e é justamente aí que o
modelo vai pior. A saída é mudar a formulação para **prever o sucessor** de cada bloco.

### 8.6 Mais dados ajudam — e muito

Ampliamos o treino de 152 para 3.235 páginas (21 vezes):

| Páginas de treino | τ | Pior caso | Sucessor correto |
|---:|---:|---:|---:|
| 152 | 0,694 | 0,387 | 15,6% |
| 400 | 0,721 | 0,442 | 16,8% |
| 1.000 | 0,730 | 0,455 | 15,1% |
| 2.000 | 0,761 | 0,494 | 19,1% |
| 3.235 | **0,786** | **0,527** | 20,8% |

Três leituras:

1. O τ sobe cerca de 0,03 a cada vez que o treino dobra, **sem sinal de estacionar**. A
   distância para a XY-cut caiu de 0,14 para 0,05.
2. No **pior caso**, o LayoutLM já passou a heurística (0,527 contra 0,496).
3. A **continuidade quase não melhorou** (de 15,6% para 20,8%). Confirma que ela depende da
   formulação, não do volume de dados.

A BiLSTM de geometria, na mesma curva, não se mexe (0,721 → 0,702): ela satura com
pouquíssimo dado.

### 8.7 O impacto em RI: a ordem pesa no texto, não em achar a página

Piloto em Japeri, com 269 páginas e 915 consultas geradas a partir de 421 atos que já vêm
com o texto na ordem certa:

- **Achar a página certa não depende da ordem.** MRR@10 entre 0,99 e 1,00 para todos os
  métodos. Faz sentido: a busca por palavras-chave usa um "saco de palavras", e o saco é o
  mesmo em qualquer ordem.
- **O texto entregue depende.** Frases de 12 palavras dos atos que chegam intactas: 45,4%
  sem ordenar, 53,4% com o fluxo do PDF, 49,7% com a XY-cut, 45,7% com o LayoutLM.
- **Em Japeri, o fluxo do PDF preservou mais texto que a XY-cut** — e Japeri está entre os
  veículos ditos "não confiáveis". Discordar da XY-cut não prova que o fluxo esteja errado.

Esse é o elo do trabalho com a área de RI, e ele é mais fino do que o discurso fácil: o
ganho não está em encontrar o documento, está no **contexto entregue** a quem lê ou à LLM.

### 8.8 O que ainda não sabemos

- Se a referência automática concorda com um humano (só a anotação diz).
- Quem acerta nos 19 veículos não confiáveis.
- Se uma LLM de verdade (14B, 32B, ou uma API paga) resolve a tarefa, e a que custo.
- Se o LayoutLM com formulação de sucessor fecha a distância.
- Se o efeito em RI aumenta numa coleção maior, com busca densa e com um RAG completo.

---

## 9. O que existe no repositório

### 9.1 Mapa dos módulos

| Arquivo | O que faz |
|---|---|
| `src/data/extrair_zips.py` | Descompacta os ZIPs do acervo, saneando nomes que o Windows recusa |
| `src/data/extrator.py` | PDF → blocos + as três ordens candidatas |
| `src/data/diagnostico_acervo.py` | Inventário e qualidade dos PDFs |
| `src/eval/caracterizar.py` | Mede a concordância entre ordens por veículo e define treino/validação/teste |
| `src/eval/protocolo.py` | O contrato comum: partições, entrada embaralhada, gravação de predições |
| `src/eval/metrics.py` | τ, sucessor correto, ARD, BLEU, acerto exato, reparo de permutação |
| `src/eval/baselines.py` | Ordem do detector, ingênua e XY-cut |
| `src/models/lstm_ordem.py` | BiLSTM nas três variantes |
| `src/models/layoutlm_ordem.py` | LayoutLM: treino, avaliação e ablação |
| `src/eval/llm_ordem.py` | LLM via Ollama: zero-shot, few-shot, retomada, registro da execução |
| `src/eval/comparar.py` | Junta todas as predições e gera as tabelas |
| `src/eval/figuras.py` | As figuras 1 a 6 |
| `src/eval/latencia_hardware.py` | Latência de todos os métodos na mesma máquina |
| `src/eval/avaliar_golden.py` | Todos os métodos contra a anotação humana |
| `src/anotacao/preparar_lote.py` | Sorteia páginas e renderiza as imagens de um lote de anotação |
| `src/anotacao/servidor.py` + `ferramenta.html` | A ferramenta de anotação |
| `src/ri/piloto_japeri.py` | O experimento de recuperação de informação |
| `src/kaggle/montar_pacote.py` | Gera o zip e o notebook para o Kaggle |
| `src/kaggle/importar_resultados.py` | Traz os resultados do Kaggle de volta |
| `src/rodar_experimentos.py` | Orquestra a bateria principal |
| `src/rodar_curva_aprendizado.py` | Orquestra a curva de aprendizado |

### 9.2 Onde ficam os resultados

- `resultados/pred_<metodo>.jsonl` — a ordem que cada método previu para cada página.
- `resultados/comparacao.md` e `.json` — as tabelas finais.
- `resultados/curva_aprendizado/`, `resultados/ri_japeri/`, `resultados/golden/` — os
  experimentos novos.
- `docs/figuras/` — as 8 figuras.
- `resultados/logs/` — a saída bruta de cada execução, para conferência.

### 9.3 Os comandos que você mais vai usar

Anotar o Golden Dataset:

```bash
venv\Scripts\python.exe src\anotacao\servidor.py
```

Avaliar contra a anotação humana:

```bash
venv\Scripts\python.exe src\eval\avaliar_golden.py --lote golden_v1
```

Refazer as tabelas depois de qualquer experimento novo:

```bash
venv\Scripts\python.exe src\eval\comparar.py
```

Gerar o pacote do Kaggle:

```bash
venv\Scripts\python.exe src\kaggle\montar_pacote.py
```

---

## 10. O que fazer a seguir, e por quê

Em ordem de valor para o TCC:

1. **Anotar as 30 páginas do `golden_v1`** (1 a 2 horas). Só isso remove o viés da
   referência automática e responde quem acerta nos veículos incertos. É a única tarefa
   que ninguém pode fazer por você.
2. **Rodar as LLMs no Kaggle** (10 minutos de setup, 4 a 6 horas de execução). Sem isso, a
   comparação "LayoutLM × LLM" fica frágil: a banca dirá que a LLM testada era fraca.
3. **Levar as perguntas ao orientador** ([ROADMAP.md](ROADMAP.md)), principalmente: ele
   espera avaliação de RI (busca e RAG) além da avaliação da ordenação?
4. **Mudar a formulação do LayoutLM** para prever o sucessor de cada bloco. É a correção
   apontada pela seção 8.5, e é o experimento mais interessante que resta.
5. **Escalar os dados de treino**, já que a curva não estacionou. O gargalo é a velocidade
   de extração dos PDFs; trocar o `pdfplumber` pelo PyMuPDF resolve.
6. **Ampliar o piloto de RI**: mais veículos, consultas em linguagem natural, busca densa
   e um RAG completo medindo a qualidade das respostas.

---

## 11. Perguntas que você pode ter

**Se a XY-cut ganha, o TCC não perdeu o sentido?**
Não. O trabalho pergunta se vale a pena usar modelos pesados para essa tarefa. "Não vale,
exceto em tais casos" é uma resposta legítima e útil — e agora ela vem com números,
ablação, curva de aprendizado e um efeito medido em RI. Além disso, o LayoutLM já supera a
heurística no pior caso e continua melhorando com dados.

**Uma placa de vídeo melhor mudaria os resultados?**
Não os de eficácia. Os mesmos pesos produzem a mesma ordem em qualquer GPU; a placa muda o
tempo. Ela ajuda a rodar **LLMs maiores** (que não cabem em 6 GB) — e é por isso que o
Kaggle entra, de graça.

**Por que não usar direto o GPT-4 ou o Gemini?**
Podem entrar como "teto de desempenho" e como eixo de custo financeiro, e isso está no
roadmap. Mas o TCC compara um modelo local e barato com LLMs; começar pelas abertas mantém
tudo reprodutível e sem custo.

**Por que o LayoutLM, sendo grande, perde para uma regra simples?**
Por três motivos somados: pouco dado rotulado (152 páginas no experimento principal, e a
curva mostra que isso pesava), a formulação pontual (que troca vizinhos) e o tokenizador em
inglês, que fragmenta o português. Nada disso é sobre "modelo grande ou pequeno".

**O que é, afinal, o "sucessor correto"?**
A fração de blocos que, na ordem prevista, são seguidos pelo bloco certo. É a medida de
continuidade do texto. Veja o exemplo da seção 6.2: dá para ter τ 0,667 e 0% de sucessor.

**Por que só 95 páginas de teste?**
Porque a referência confiável só existe em 11 veículos, e três deles foram reservados para
teste. Com o Golden Dataset e mais extração, esse número cresce.

**Posso confiar nos números atuais?**
Como resultados **preliminares**, sim: o protocolo é justo e está documentado. Como
resultados **finais**, não — falta a referência humana. Está escrito assim em todos os
documentos, e é o tipo de honestidade que a banca valoriza.

---

## 12. Como isso vira o texto do TCC

| Capítulo | De onde sai |
|---|---|
| 1. Introdução | Seção 1 deste guia, mais o piloto de RI (seção 8.7) como motivação concreta |
| 2. Fundamentação teórica | [LITERATURA.md](LITERATURA.md) e a seção 5 deste guia |
| 3. Dados | [ACERVO.md](ACERVO.md), seções 3 e 4 daqui, [GUIA_ANOTACAO.md](GUIA_ANOTACAO.md) |
| 4. Metodologia | [METODOLOGIA.md](METODOLOGIA.md); seções 5, 6 e 7 daqui explicam o mesmo em linguagem simples |
| 5. Desenvolvimento | [DIARIO_DE_BORDO.md](DIARIO_DE_BORDO.md), inclusive os erros e correções — capítulo mais fácil de escrever do que parece |
| 6. Resultados | [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md) e `docs/figuras/` |
| 7. Conclusão e trabalhos futuros | Seções 8.8 e 10 daqui, mais o [ROADMAP.md](ROADMAP.md) |

Três frases que o trabalho já pode defender, com evidência:

1. "A ordem interna dos PDFs de diários oficiais não é a ordem de leitura em 19 dos 30
   veículos analisados."
2. "A informação que resolve a tarefa está na geometria: zerar as coordenadas derruba o τ
   do LayoutLM de 0,671 para 0,122."
3. "As métricas usuais de ordem de leitura escondem o que importa para RI: o LayoutLM tem
   τ 0,671 e apenas 13% de sucessores corretos, e é a continuidade que determina o texto
   entregue a um sistema de busca ou a um RAG."

---

## 13. Glossário

| Termo | Definição |
|---|---|
| **Ablação** | Remover um ingrediente do modelo para medir sua contribuição. |
| **ARD** | *Average Relative Distance*: deslocamento médio, em posições, entre a ordem prevista e a correta. |
| **Baseline** | Método simples usado como referência de comparação. |
| **BERT** | Modelo transformer pré-treinado a prever palavras escondidas; base do LayoutLM. |
| **BLEU** | Métrica de sobreposição de n-gramas, vinda da tradução automática. Pouco discriminativa em granularidade de bloco. |
| **BM25** | Função clássica de ranqueamento em busca: pontua documentos pela frequência dos termos da consulta, dando mais peso a termos raros e descontando documentos longos. |
| **Bloco** | Unidade de texto que ordenamos (parágrafo ou trecho de coluna) com sua caixa. |
| **Bootstrap** | Reamostragem com repetição, usada para estimar o intervalo de confiança. |
| **Calha** | Faixa vertical em branco entre duas colunas. |
| **Época** | Uma passada completa pelos dados de treino. |
| **Few-shot** | Colocar exemplos resolvidos dentro do prompt da LLM. |
| **Fine-tuning** | Continuar o treino de um modelo pré-treinado na tarefa específica. |
| **Gold / silver** | Referência anotada por humano / referência automática aproximada. |
| **IC 95%** | Faixa em que a média cairia em 95% das reamostragens. |
| **Kendall (τ)** | Correlação de ordem baseada em pares concordantes e discordantes. |
| **Latência** | Tempo por página. |
| **Learning to rank** | Aprender a ordenar itens; pontual, par a par ou em lista. |
| **LayoutLM** | BERT com coordenadas 2D nos embeddings de entrada. |
| **LayoutReader** | Trabalho de 2021 que trata ordem de leitura com decodificador seq2seq; origem das métricas BLEU e ARD. |
| **LLM** | Modelo de linguagem grande, generativo. |
| **LSTM / BiLSTM** | Rede recorrente com memória; bidirecional lê a sequência nos dois sentidos. |
| **MRR@10** | Média de 1/posição do primeiro resultado relevante, olhando os 10 primeiros. |
| **MSE** | Erro quadrático médio, a perda usada no treino do LayoutLM. |
| **OCR** | Reconhecimento óptico de caracteres: extrair texto de imagem. |
| **Ollama** | Programa que roda LLMs localmente. |
| **p10** | Percentil 10: o desempenho nas 10% piores páginas. |
| **Permutação** | Reordenação de uma lista sem perder nem repetir elementos. |
| **p-valor** | Chance de observar a diferença medida se os métodos fossem equivalentes. |
| **RAG** | *Retrieval-Augmented Generation*: buscar trechos e entregá-los a uma LLM para responder. |
| **Sucessor correto** | Fração de blocos seguidos, na predição, pelo bloco certo. |
| **Token** | Pedaço de palavra que o modelo processa. |
| **Transformer** | Arquitetura em que cada token atende a todos os outros. |
| **Veículo** | Fonte de diário (estado ou município). |
| **Wilcoxon** | Teste estatístico pareado, sem suposição de normalidade. |
| **XY-cut** | Heurística que corta a página em colunas e seções recursivamente. |
| **Zero-shot** | Pedir a tarefa à LLM sem exemplos resolvidos. |
