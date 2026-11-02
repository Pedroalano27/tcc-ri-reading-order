# Relatório da noite de 02 para 03/10/2026

Escrito pelo Claude (orquestrador). Versão das 07:00 de 03/10; a seção 6 lista o que ainda estava rodando.
Todo número abaixo sai de um arquivo em `resultados/` ou de um log, indicado ao lado. Nada foi commitado.

**Como ler a confiança de cada número.** Executei eu mesmo, ou vi a saída direta de: treinos e mAP dos
detectores, as duas tabelas do `diamond_teste`, a comparação nas 317 páginas (reexecutei o script duas vezes)
e o LayoutReader (reexecutei). Dos relatórios do Codex li o veredito e as tabelas, sem auditar o código. Os
scripts do Antigravity (concordância, ancoragem, baselines de ordem do Label Studio, avaliação do Gemini,
PyMuPDF, extrator híbrido) rodaram pela fila e eu li os resumos: trate-os como **não revisados**.

**Correção de enquadramento (03/10, 09:15, a pedido do Pedro).** Duas perguntas foram respondidas de lado nesta
noite e as seções abaixo devem ser lidas com isto em mente:
- *Frente B.* A ideia "sem bbox fina" não é para ganhar da XY-cut: é para **diminuir os erros do sistema**, porque
  a maior parte deles nasce na etapa das caixas finas. A comparação que importa é **automático contra
  automático** (seção 2.10), não contra regiões humanas (seções 2.2 a 2.4).
- *Frente A.* O pedido era usar o dataset anotado por humanos para **melhorar o extrator**. O que foi medido de
  madrugada (detector dentro do extrator antigo, julgado na convenção antiga) não responde a isso. A resposta
  está na tarefa do extrator v4, com o detector como base (seção 6).

---

## 1. Resumo em dez linhas

1. **Frente B (plano do professor: só texto / tabela / imagem, ordem no texto).** Ele entrega ordem de leitura
   com τ de palavras entre 0,95 e 0,99 em quatro conjuntos, sem caixas finas.
2. Mas **não é melhor** que a XY-cut sobre regiões humanas quando as duas recebem a mesma regra de
   cabeçalho/rodapé: diferença de 0,008 em τ de palavras, IC 95% [−0,056; 0,040], p = 0,59 (golden_v4).
3. **90,1% do ganho** que o primeiro relatório atribuía ao plano (τ de regiões 0,825 → 0,917) vem dessa regra
   de margens, que a XY-cut de referência não tinha recebido.
4. A regra de margens é um **ganho barato para o pipeline atual**: XY-cut sobre o extrator automático vai de
   τ de palavras 0,819 para 0,952 no golden_v4. Em páginas novas o efeito é grande sobre regiões humanas
   (0,905 → 0,976) e pequeno sobre blocos automáticos v3 (0,913 → 0,918).
5. Tratar tabela e imagem como bloco único vale cerca de 0,10 de τ (0,868 sem átomos → 0,968 com Docling →
   0,986 com o nosso detector de 3 classes).
6. **Frente A (extrator).** O detector de 3 classes treinado no dataset do Label Studio chega a mAP50 0,826 em
   fontes não vistas; o de 16 classes, 0,483 (as classes finas de título não se sustentam).
7. **Cada sistema ganha no gabarito da sua convenção de caixas:** nas 317 páginas do Label Studio o detector
   de 3 classes faz F1 de localização 0,780 contra 0,573 do extrator; nas 11 páginas anotadas do zero pelo
   Pedro, o extrator faz 0,851 contra 0,765.
8. O pré-treino no dataset do parceiro ajuda na convenção do TCC (ajuste fino no Diamond: 0,750 partindo do
   modelo genérico, 0,789 partindo do detector de 16 classes), mas não alcança o extrator de regras (0,851).
9. **Velocidade:** com o PyMuPDF no lugar do pdfplumber o extrator inteiro fica 33 vezes mais rápido (2,585 s →
   0,078 s por página), mas 43 de 104 páginas mudam algum bloco (93,49% dos blocos idênticos). Fica como
   módulo opcional, com testes; não serve para regenerar a referência silver.
10. **Gemini reavaliado em páginas novas** (item de ação da reunião): τ 0,896 contra 0,891 da XY-cut nas 89
    páginas de teste. A vantagem que ele tinha no golden (0,962) praticamente some.

---

## 2. Frente B — ordem de leitura sem bounding box fina

### 2.1 O que mudou durante a noite

O primeiro experimento do Codex (`resultados/ordem_sem_bbox.md`) dizia τ de regiões 0,917 contra 0,825 da
XY-cut, nas 44 páginas do `golden_v4`. A revisão adversarial (`resultados/revisao_ordem_sem_bbox.md`) apontou
que o método novo tinha uma política de margens (topo primeiro, rodapé por último, marcas antes do rodapé) e
a XY-cut de referência não, e que a projeção por mediana esconde texto intercalado. Mandei refazer com
linhas de base justas e passei a exigir, em todas as tarefas seguintes, a régua de **palavras** como principal.

### 2.2 Reanálise justa (golden_v4, 44 páginas) — `resultados/ordem_sem_bbox_justo.md`

| Método | τ de palavras | τ de regiões |
|---|---:|---:|
| XY-cut nas regiões humanas, pura | 0,853 | 0,825 |
| XY-cut nas regiões humanas + margens (geometria) | 0,972 | 0,908 |
| XY-cut nas regiões humanas + cabeçalho/rodapé pela classe humana | 0,979 | 0,918 |
| XY-cut no extrator automático, pura | 0,819 | 0,798 |
| XY-cut no extrator automático + margens (geometria) | 0,952 | 0,899 |
| XY-cut no extrator automático + classes previstas | 0,940 | 0,889 |
| Plano sem bbox, seleção por página (o número original) | 0,946 | 0,917 |
| Plano sem bbox, seleção deixando o veículo de fora, por palavras | 0,980 | 0,937 |

A política recupera 90,1% do ganho original em τ de regiões. O ganho residual do plano sobre a XY-cut justa é
0,008 (IC 95% [−0,056; 0,040]; permutação por veículo p = 0,590). A mediana escondia fragmentação em 18 páginas.

### 2.3 Plano de ponta a ponta com o nosso detector — `resultados/ordem_sem_bbox_ls3.md`

τ da sequência real de palavras, mesmas 44 páginas, IC 95% por veículo:

| Origem dos blocos atômicos | τ | Sucessor | Regiões fragmentadas |
|---|---:|---:|---:|
| Nenhum (tudo é texto) | 0,868 [0,822; 0,967] | 91,0% | 8,5% |
| Docling (tabela e imagem) | 0,968 [0,906; 0,992] | 97,5% | 4,8% |
| Detector de 3 classes `ls3` | 0,986 [0,911; 0,994] | 98,8% | 2,9% |
| Tabela e figura do ouro humano (diagnóstico) | 0,979 [0,926; 0,994] | 98,8% | 3,0% |
| Caixas de texto do `ls3` ordenadas por XY-cut | 0,943 [0,890; 0,977] | 98,7% | 2,0% |

`ls3` contra Docling: Δτ = 0,018, IC 95% [−0,046; 0,054] — viável, sem superioridade demonstrada.

### 2.4 Validação em páginas que não entraram no desenvolvimento

τ de palavras, configuração congelada do golden_v4:

| Conjunto | n | Plano sem bbox | XY-cut + margens | XY-cut pura | Fonte |
|---|---:|---:|---:|---:|---|
| Label Studio, projeto 23 (regiões humanas; átomos humanos) | 123 | 0,966 | 0,976 | 0,905 | `ordem_sem_bbox_validacao_ls.md` |
| Idem, átomos do `ls3` (inclui páginas de treino do detector) | 123 | 0,954 | 0,976 | 0,905 | idem |
| Golden v3, páginas fora do v4 (blocos v3, ordem humana cega) | 27 | 0,971 | 0,918 | 0,913 | `ordem_sem_bbox_validacao_acervo.md` |
| Golden v3, páginas repetidas do v4 | 20 | 0,983 | 0,950 | 0,845 | idem |
| Teste silver, páginas novas | 86 | 0,968 | 0,948 | 0,942 | idem |

- No Label Studio a diferença contra a XY-cut com margens é −0,010 (IC [−0,050; 0,018]): não confirma ganho.
  Ressalva: essa ordem humana foi feita corrigindo a sugestão da XY-cut.
- No acervo do TCC o plano fica à frente (+0,05 nas 27 páginas humanas novas), mas sem significância
  (Wilcoxon p = 0,289) e com continuidade um pouco pior (sucessor 99,1% → 98,1%; 3,1% de regiões fragmentadas).
  Ressalva: todos os veículos dessas páginas já apareciam no golden_v4.

### 2.5 LayoutReader (ordenador pronto) — `resultados/ordem_layoutreader.md`

| Método (golden_v4, 44 páginas) | τ de palavras | ms por página (CPU) |
|---|---:|---:|
| Projeção de colunas (nosso) | 0,946 | 11,6 |
| LayoutReader ordenando linhas e átomos | 0,888 | 643,6 |
| LayoutReader + margens | 0,903 | 741,6 |
| Híbrido: projeção agrupa, LayoutReader ordena | 0,936 | 489,5 |
| LayoutReader sobre regiões humanas (diagnóstico) | 0,963 | 283,8 |

Veredito: manter a projeção. O modelo pronto (`hantian/layoutreader`, CC BY-NC-SA 4.0, em `models/terceiros/`)
é pior em linhas e cerca de 50 vezes mais lento.

### 2.6 Gemini em páginas novas — `resultados/vlm_ordem_teste.md` (não revisado)

Partição de teste, 89 páginas (CE, MA, RJ), referência silver, blocos v3:

| Método | τ (IC 95%) | Sucessor | Tempo por página |
|---|---:|---:|---:|
| Gemini 3.1 Flash Lite com imagem e marcas | 0,896 (0,853–0,934) | 82,5% | 6,98 s |
| XY-cut | 0,891 (0,846–0,930) | 78,4% | 0,33 ms |
| Ingênua | 0,790 (0,734–0,844) | 69,0% | 0,05 ms |

Wilcoxon pareado: τ p = 0,008; sucessor p = 0,061. Por veículo: CE 0,983 × 0,989; MA 0,883 × 0,852; RJ
0,677 × 0,717, com só 23,1% de permutações válidas no RJ. 75 das 89 respostas foram permutações válidas de
primeira. A referência dessa partição favorece a XY-cut por construção; leio como empate. No golden o mesmo
modelo tinha 0,924 (v3) e 0,962 (v4, com a classe humana no prompt).

### 2.7 Ordem no Label Studio como segundo conjunto — `resultados/ordem_ls_baselines.md` (não revisado)

125 páginas com cadeia válida: XY-cut τ 0,884 e sucessor 75,4%; ingênua 0,824. 49,6% das páginas e 69,9% das
ligações foram aceitas como a XY-cut sugeriu. Nas 63 páginas em que o anotador mudou algo, a XY-cut cai para
τ 0,792 e sucessor 57,3%.

### 2.8 A política de margens como módulo, na régua oficial de blocos — `resultados/politica_margens.md`

O Codex criou `src/eval/politica_margens.py` e `tests/test_politica_margens.py` (18 testes novos; a suíte
completa passou com 144) sem tocar em `baselines.py`. A variante recomendada separa as margens **antes** e
recalcula a XY-cut só no corpo. XY-cut sem → com a política, na régua de blocos do TCC:

| Conjunto | n | τ de Kendall | Sucessor correto | ARD norm. | Δτ [IC 95%] |
|---|---:|---:|---:|---:|---:|
| Teste silver | 89 | 0,891 → 0,928 | 78,4% → 83,2% | 0,045 → 0,029 | 0,037 [0,013; 0,064] |
| golden_v3 | 47 | 0,851 → 0,908 | 74,0% → 76,8% | 0,068 → 0,041 | 0,057 [0,020; 0,102] |
| golden_v4 | 44 | 0,825 → 0,908 | 71,5% → 82,0% | 0,083 → 0,034 | 0,083 [0,004; 0,163] |

Ressalvas do próprio relatório: a política piorou 6, 4 e 7 páginas, respectivamente; com o limiar de topo em 5%
o sinal do ganho no teste se inverte; aplicada só como pós-processamento (sem recalcular a XY-cut no corpo) cai
para τ 0,799 no v4. O golden_v4 foi usado para escolher os limiares; teste silver e golden_v3 são os testes
limpos. No teste silver, a XY-cut com margens (0,928) fica acima do Gemini (0,896, seção 2.6).

### 2.10 Automático contra automático (a pergunta do autor)

Só pipelines sem nenhuma informação humana na entrada, τ da sequência real de palavras; números já presentes nas
seções 2.2 a 2.4, reorganizados:

| Conjunto | Pipeline atual: caixas finas automáticas + XY-cut | Atual + política de margens | Plano sem bbox fina |
|---|---:|---:|---:|
| golden_v4, 44 páginas (caixas do extrator `propor()`) | 0,819 | 0,952 | 0,968 (Docling) / 0,986 (`ls3`) |
| golden_v3 fora do v4, 27 páginas (blocos v3) | 0,913 | 0,918 | 0,971 (Docling) |
| Teste silver, 86 páginas novas (blocos v3) | 0,942 | 0,948 | 0,968 (Docling) |

Os números do golden_v4 vêm de dois relatórios (`ordem_sem_bbox_justo.md` e `ordem_sem_bbox_ls3.md`) e não foram
testados entre si. Evidência de que o erro se concentra nas caixas e classes finas: concordância humana de kappa
0,936 em 3 classes contra 0,763 em 16; detector com mAP50 0,826 em 3 classes contra 0,483 em 16; extrator com
classe certa em 97,8% das palavras em 3 classes contra 76,9% em 9. Falta a contagem direta de erros de ponta a
ponta e a origem de cada um (caixa ou ordenação): tarefa `12` do Codex (seção 6). Painéis lado a lado das caixas
de hoje e da ideia nova: `resultados/comparacao_fino_x_grosso/` (`orquestracao/analises/comparacao_visual_fino_x_grosso.py`).

### 2.11 Contagem de erros de ponta a ponta — `resultados/erros_ponta_a_ponta.md` (Codex, tarefa `12`, 03/10 13:13)

71 páginas com ordem humana (44 do golden_v4 e 27 do golden_v3 fora do v4), 27 veículos, 59.949 palavras com
referência. Nenhum pipeline recebe caixa, classe ou ordem humana. Quebra = transição da saída que não é o
sucessor na leitura humana.

| Pipeline | Quebras por página | τ palavras | Sucessor de linhas | Fidelidade 12 | Quebras dentro de uma unidade |
|---|---:|---:|---:|---:|---:|
| Ordem ingênua | 85,46 | 0,759 | 50,8% | 56,2% | — |
| Extrator atual + XY-cut | 16,14 | 0,830 | 85,7% | 87,5% | 213 |
| Extrator atual + XY-cut + margens | 9,87 | 0,947 | 91,2% | 92,3% | 213 |
| Sem bbox fina, átomos `ls3` | 7,25 | 0,976 | 92,1% | 94,1% | 29 |
| Sem bbox fina, átomos Docling | 10,99 | 0,977 | 89,9% | 92,2% | 314 |

- Contra o pipeline atual: −8,89 quebras por página [−13,13; −4,89], Holm por veículo p = 0,010; ganha em 38
  páginas, empata em 13, perde em 20.
- Contra o atual com margens: −2,62 [−5,77; 0,18], p por veículo = 0,913; ganha em 14, empata em 29, perde em 28.
  O ganho médio vem de poucas páginas densas (as cinco maiores diferenças somam 230 quebras; o saldo total é 186).
- Origem das 1.146 quebras do pipeline atual: 197 em caixa fundida, 13 em caixa partida, 16 de ordem interna
  (226 ao todo, 19,7% das quebras, associadas às caixas); 912 residuais, das quais 442 somem com a política de margens.
  O relatório conclui que a hipótese de que a maioria das quebras nasce nas caixas **não é sustentada** nessa
  régua; a regra é conservadora (o resíduo não certifica caixas corretas).
- Com átomos do Docling a proposta perde a vantagem em quebras (10,99): as tabelas do Docling trazem 304 quebras
  internas. O ganho depende do detector `ls3`, treinado no dataset do parceiro.
- A prévia do Antigravity (`erros_ponta_a_ponta_previa.md`) chamava de P2 a variante Docling; o Codex refez a
  conferência do zero, sem divergência por página.

### 2.9 Leitura para o TCC

- A afirmação defensável é de **equivalência prática**, não de superioridade: ordenar linhas com tabela e
  imagem como blocos chega à qualidade de ordenar regiões finas feitas por humano, e fica igual ou acima de
  ordenar os blocos automáticos. Ausência de significância não prova equivalência; faltam páginas de veículos novos.
- A **política de margens** merece virar método do TCC ("XY-cut + margens"): melhora a XY-cut na régua oficial
  nos três conjuntos, com IC que exclui zero (seção 2.8), e o módulo com testes está pronto. É sensível ao
  limiar de topo e piora algumas páginas; adotar é decisão metodológica do autor.
- O ponto fraco do plano é a **continuidade**: 3% a 5% das regiões saem com texto intercalado.

---

## 3. Frente A — extrator e detectores

### 3.1 Detectores treinados no dataset do Label Studio

YOLOv8s, 1024 px, 60 épocas, 1.590 páginas de treino, split por fonte. Teste = 317 páginas de fontes não vistas.

| Modelo | mAP50 validação | mAP50 teste | mAP50-95 teste | Fonte |
|---|---:|---:|---:|---|
| `ls3` (texto / tabela / imagem) | 0,790 | 0,826 | 0,706 | `resultados/deteccao/ls3_map_teste.json` |
| `ls16` (16 classes do guia) | 0,530 | 0,483 | 0,394 | `resultados/deteccao/ls16_map_teste.json` |

`ls3` por classe (AP50): tabela 0,855; imagem 0,828; texto 0,795. `ls16`: table 0,83; figure 0,82; header 0,82;
paragraph 0,70; footer 0,67; signature 0,60; id 0,60; heading 0,58; act section 0,52; act 0,49; title 0,42;
caption 0,39; section title 0,16; sub section title 0,12; chart 0,02.

### 3.2 Nas 317 páginas do Label Studio — `resultados/extrator_vs_detector_ls_teste.md`

F1 micro por caixa, IC 95% por bootstrap de páginas:

| Sistema | Localização IoU ≥ 0,5 | Localização IoU ≥ 0,75 | 3 classes | 9 classes | 16 classes | ms/página (CPU) |
|---|---:|---:|---:|---:|---:|---:|
| Extrator (regras + Docling) | 0,573 [0,530; 0,614] | 0,399 | 0,555 | 0,480 | — | 4.486,8 |
| `ls3` | 0,780 [0,743; 0,816] | 0,731 | 0,769 | — | — | 711,2 |
| `ls16` | 0,753 [0,720; 0,783] | 0,705 | 0,743 | 0,668 | 0,622 | 277,7 |

Revocação por origem da caixa do ouro (IoU ≥ 0,5): extrator 0,481 manual / 0,563 aceita da máquina / 0,663
ajustada; `ls3` 0,780 / 0,915 / 0,896; `ls16` 0,714 / 0,894 / 0,856. Compatível com os detectores herdarem a
pré-anotação, sem provar. 11 páginas não têm camada de texto; 6 estão em envelopes PKCS#7; 1 página de teste
é de uma fonte que também está no treino (alias "pag df" / "df").

### 3.3 Nas 11 páginas anotadas do zero (`diamond_teste`)

Régua oficial por palavras. Fontes: `resultados/deteccao/comparacao_detector_ls.txt` e
`comparacao_ajuste_fino_diamond.txt`.

| Sistema | F1@0,5 | F1@0,9 | F1 com classe (9) | F1 com classe (3) | Classe certa (3) |
|---|---:|---:|---:|---:|---:|
| Extrator (regras + Docling) | 0,851 | 0,754 | 0,696 | 0,824 | 97,8% |
| `ls3` | 0,765 | 0,646 | 0,431 | 0,731 | 93,0% |
| `ls16` | 0,753 | 0,648 | 0,628 | 0,718 | 94,7% |
| Ajuste fino no Diamond, partindo do modelo genérico | 0,750 | 0,631 | 0,639 | 0,722 | 86,9% |
| Ajuste fino no Diamond, partindo do `ls16` | 0,789 | 0,675 | 0,642 | 0,759 | 92,4% |
| Ajuste fino no Diamond, partindo do `ls3` | 0,775 | 0,644 | 0,653 | 0,753 | 94,6% |

Ajuste fino: `data/deteccao/diamond_yolo` (200 páginas de treino, 19 de validação), 120 épocas, mesmos
hiperparâmetros nos três; roteiro em `orquestracao/noite_0210/gpu2.sh`. Onze páginas: sem teste de significância.

### 3.4 Extrator híbrido — `resultados/extrator_hibrido_ls.md` (Antigravity, não revisado)

Trocar o Docling por um detector do domínio dentro do `propor()` não melhora o extrator nas 11 páginas: a
melhor variante (regiões do ajuste fino partindo do `ls16`) empata em F1@0,5 (0,851) e sobe o F1@0,9 de 0,754
para 0,772, com 6 páginas melhores e 5 piores. As uniões e a variante "só tabela e imagem" ficam abaixo.

### 3.5 Teto humano e ancoragem no dataset do parceiro (Antigravity, não revisados)

- **Concordância entre anotadores** (`resultados/labelstudio_concordancia_v2.md`, 144 páginas, 146 pares, só
  projetos de bounding box): F1 de localização 85,6% [83,1; 87,8] em IoU ≥ 0,5; kappa de classe 0,763 em 16
  classes, 0,875 em 9 e 0,936 em 3. Sem os pares suspeitos de cópia (123 pares): 82,9% e kappa 0,756.
  A primeira versão (`labelstudio_concordancia.md`, F1 93,7%) está **errada**: incluía 189 páginas do projeto de
  ordem, onde a segunda anotação é cópia da primeira. Não usar.
- **Ancoragem** (`resultados/labelstudio_ancoragem.md`, 2.119 páginas, 38.517 caixas): 40,0% aceitas como a
  máquina sugeriu, 44,8% ajustadas, 15,2% criadas do zero.

### 3.6 Velocidade — `resultados/pymupdf_palavras.md` (Antigravity, não revisado)

60 páginas de 30 veículos: pdfplumber 4,917 s por página em média (mediana 1,468 s); PyMuPDF 0,024 s (mediana
0,019 s); aceleração média de 208,9 vezes. 99,4% das palavras do pdfplumber têm par no PyMuPDF com o mesmo
texto e IoU ≥ 0,7. PyMuPDF 1.28.2 foi instalado no venv (licença AGPL); o torch não foi afetado.

**O que importa é o bloco, e aí a paridade não é total** — `resultados/extrator_pymupdf_paridade.md` (Codex,
tarefa T14; módulo novo `src/data/palavras_pymupdf.py`, `tests/test_palavras_pymupdf.py`; a suíte passou com
126 testes, 21 deles novos; `src/data/extrator.py` não foi tocado):

| Amostra | Blocos pdfplumber / PyMuPDF | Blocos idênticos | Páginas com todos os blocos iguais | s/página pdfplumber / PyMuPDF | Ganho |
|---|---:|---:|---:|---:|---:|
| Bancada de 44 páginas | 1.451 / 1.445 | 90,90% | 28 de 44 | 2,412 / 0,079 | 30,64× |
| 60 páginas extras | 1.761 / 1.750 | 95,63% | 33 de 60 | 2,713 / 0,077 | 35,31× |
| Total | 3.212 / 3.195 | 93,49% | 61 de 104 | 2,585 / 0,078 | 33,31× |

"Idêntico" = mesmo texto e IoU ≥ 0,95. O extrator inteiro (palavras + segmentação) fica cerca de 33 vezes mais
rápido, mas 43 das 104 páginas mudam algum bloco. Veredito do Codex: o módulo fica como opção; **não pode virar
o padrão com paridade garantida e a referência silver não deve ser regenerada com ele**. A conclusão otimista
do relatório do Antigravity ("pode substituir com segurança") vale para as palavras, não para os blocos.

**Tabela e imagem direto da camada do PDF, sem rede neural** — `resultados/caminho_rapido_pymupdf.md` (Codex).
No golden_v4, mantendo as palavras do pdfplumber e trocando só a origem dos blocos atômicos do plano sem bbox:

| Origem de tabela e imagem | τ de palavras | Regiões fragmentadas |
|---|---:|---:|
| Nenhuma | 0,917 | 6,5% |
| Docling (rede neural) | 0,946 | 3,6% |
| PyMuPDF, variante conservadora (sem rede) | 0,967 | 2,6% |
| PyMuPDF incluindo a estratégia `text` de tabelas | 0,829 | 18,4% |

O pipeline completo em CPU cai de 4,389 para 0,541 s por página (8,1 vezes). Trocando também as palavras pelo
PyMuPDF, o τ cai para 0,920 (medido nas 98,9% de palavras pareadas). O relatório pede detector como reserva
para tabela sem grade, imagem composta e PDF digitalizado.

### 3.8 Modelos maiores treinados no Kaggle (zip recebido às 09:24)

Mesmo split. Métricas em `resultados/kaggle/detector_ls/`, pesos em `models/detector_ls/`.

| Modelo | mAP50 teste | mAP50-95 teste | Épocas | F1@0,5 no `diamond_teste` |
|---|---:|---:|---:|---:|
| 3 classes, YOLO11m 1280 px | 0,792 | 0,659 | 70 (limite de 3,5 h) | 0,771 |
| 16 classes, YOLO11m 1280 px | 0,510 | 0,409 | 52 | 0,771 |
| 16 classes, RT-DETR-L 1024 px | 0,517 | 0,430 | 60 | 0,747 |
| 3 classes, YOLOv8s local (referência) | 0,826 | 0,706 | 60 | 0,765 |
| 16 classes, YOLOv8s local (referência) | 0,483 | 0,394 | 60 | 0,753 |

Os dois DocLayout-YOLO caíram no início com erro do `wandb` (nome de projeto com barra); corrigido em
`src/kaggle/montar_pacote_ls.py` e no notebook regenerado. Tabela do `diamond_teste`:
`resultados/deteccao/comparacao_kaggle_ls_diamond.txt` (extrator 0,851). Modelo maior rende cerca de 0,03 de
mAP50 em 16 classes e nada em 3; o quadro não muda.

### 3.9 Classificador de classe pelo texto (Antigravity, não revisado) — `resultados/classificador_regioes_ls.md`

Regressão logística sobre n-gramas do texto transcrito, geometria e contexto, treinada em 28.949 caixas. Nas
mesmas 4.659 caixas do teste: acurácia 0,734 contra 0,788 do detector `ls16`; F1 macro 0,452 contra 0,552. Só
ganha em `footer` (+0,217), `sub section title` (+0,104), `header` (+0,030) e `act` (+0,013). O resumo do
próprio relatório afirma o contrário dos números; vale a tabela. Um classificador simples de texto não resolve
as classes finas.

### 3.10 Extrator v4: o detector como base — `resultados/extrator_v4.md` (Codex)

Resposta ao pedido de usar o dataset anotado por humanos para melhorar o extrator. O v4 parte das caixas do
detector treinado no dataset e aplica por cima: ajuste das caixas de texto às palavras do PDF, caixas para
palavras órfãs, resolução de sobreposição e leitura do texto de cada caixa. Limiares escolhidos por validação
cruzada deixando a fonte de fora. 317 páginas de teste, convenção do guia, F1 micro com IC 95%:

| Sistema | Localização IoU ≥ 0,5 | Localização IoU ≥ 0,75 | 3 classes | 16 classes | ms/página |
|---|---:|---:|---:|---:|---:|
| Extrator atual (regras + Docling) | 0,573 [0,530; 0,614] | 0,399 | 0,555 | 0,422 | 4.486,8 |
| Detector `ls3` puro, score padrão | 0,780 [0,743; 0,816] | 0,731 | 0,769 | — | 711,2 |
| Detector puro com score escolhido por validação cruzada (`ls3`, ≥ 0,45) | 0,799 [0,760; 0,834] | 0,753 | 0,787 | — | 711,2 |
| v4 completo, limiares por validação cruzada | 0,763 [0,727; 0,797] | 0,582 | 0,751 | 0,437 | 3.678,8 |
| v4 sem o ajuste às palavras | 0,778 | 0,718 | 0,765 | 0,438 | 3.678,7 |
| v4 sem as caixas de palavras órfãs | 0,790 | 0,608 | 0,777 | 0,453 | 3.678,8 |
| v4 com o RT-DETR-L do Kaggle como base, limiares padrão | 0,768 [0,731; 0,800] | 0,586 | 0,748 | 0,621 | 5.322,6 |

- **O dataset melhora muito o extrator na convenção do guia:** de 0,573 para 0,799 de F1 de localização com o
  detector treinado nele, e seis vezes mais rápido. v4 contra o extrator atual: +0,190 [0,148; 0,235],
  p = 1,2e-20, ganha em 225 páginas e perde em 72.
- **As regras por cima do detector atrapalham nesse gabarito:** v4 contra o detector ajustado, −0,035
  [−0,048; −0,024]. Ajustar a caixa às palavras derruba a localização justa (0,718 → 0,582), porque as caixas do
  ouro não são justas às palavras; criar caixas para palavras órfãs acrescenta falsos positivos.
- O que o v4 entrega e o detector puro não: cada palavra em uma caixa só e o texto de cada caixa lido do PDF
  (67,1% das caixas com texto idêntico à transcrição humana; mediana do erro de caracteres 0,000).
- Nas 11 páginas do `diamond_teste` (convenção antiga) o v4 faz 0,771 contra 0,851 do extrator atual. O relatório
  lembra que a etapa 7 do extrator atual foi calibrada nessas mesmas 11 páginas: o 0,851 não é um teste intocado.

### 3.7 Leitura para o TCC

- "Quem é melhor, extrator ou detector?" depende de qual convenção de caixas é o gabarito. Isso é um resultado,
  e reforça o achado de ancoragem que o TCC já tinha.
- O dataset do parceiro **ajuda** como pré-treino (+0,039 de F1@0,5 no teste do zero), mas o extrator de
  regras segue na frente na convenção do TCC, e trocar o detector dentro dele não muda o resultado: o que
  limita o extrator ali não é o componente visual.
- As 16 classes do guia não se sustentam num detector pequeno (títulos de seção com AP50 de 0,12 a 0,16),
  enquanto as 3 classes chegam perto da concordância humana. Isso favorece o plano do professor.
- A troca do pdfplumber pelo PyMuPDF dá 33 vezes de velocidade no extrator, ao custo de mudar blocos em 41%
  das páginas. Adotar é decisão do autor: ganha-se tempo e perde-se a comparabilidade com tudo o que já foi
  medido sobre a segmentação atual.

---

## 4. Outros resultados

- **Massa de anotação do Gemini** (`data/diamond/massa1_gemini`): de 273 para 345 de 383 páginas. As 38
  restantes (páginas densas, quase todas de Duque de Caxias) falham sempre na validação; parei o job.
- **Galerias para conferir a olho:** `resultados/galeria_ordem_sem_bbox/index.html` (44 páginas do golden_v4,
  colunas e caminho de leitura) e `resultados/galeria_extrator_detector/index.html` (ouro, extrator e
  detectores nas 11 páginas). Não abri nenhuma das duas.

---

## 5. Operação

- **Causa provável da queda de 02/10:** o `C:` fica num SSD externo USB e o treino abria 12 processos de
  leitura de imagens (20 GB comprometidos numa máquina de 16 GB). A memória comprometida chegou a 37,4 de
  37,8 GB às 02:36 de hoje, antes de eu religar o treino com 1 worker (`src/models/detector_layout.py` agora
  respeita `--workers` na retomada; `orquestracao/noite_detector_ls.sh` usa `--workers 1`).
- **Retomada depois de uma queda:** `bash orquestracao/noite_0210/iniciar.sh` (não duplica o que já roda).
  Painel: `bash orquestracao/noite_0210/status.sh`.
- **Codex:** bateu no limite de uso às 06:07, com cinco tarefas concluídas e a sexta em 43 de 44 páginas (eu
  mesmo concluí). Volta às 07:29.
- **Correção de um aviso meu:** o PDF de Curitiba não estava corrompido; o original no S3 já termina em zeros.
- **Não feito:** commit e push (sem resposta do Pedro). Tudo continua só no SSD USB.
- **Kaggle:** `dist/kaggle/ls_deteccao.zip` e `notebooks/kaggle_detector_ls.ipynb` prontos; depende do Pedro.

---

## 6. Estado final das filas

Todas as tarefas terminaram: fila do Codex encerrada em 03/10 13:29 (11 tarefas, a última foi a `12`, seção 2.11)
e a do Antigravity em 03/10 13:30 (12 tarefas). Treinos `ls3` e `ls16` concluídos; ordem do Gemini no teste pronta
(89 páginas); massa do Gemini parada em 345/383. Nada ficou rodando. O trabalho de 04/10 (Codex, em conversa direta
com o Pedro) está em `docs/HANDOFF_CODEX_0410.md`.

---

## 7. Decisões que ficam com o Pedro

1. **Commit e push** do que foi produzido (nada desde `912e0ae` está no GitHub).
2. Adotar **"XY-cut + margens"** como método novo do TCC (é decisão metodológica; a evidência está na seção 2).
3. Adotar ou não o **módulo PyMuPDF** no extrator: 33 vezes mais rápido, mas muda blocos em 43 de 104 páginas.
4. Como apresentar a frente A: sugiro "cada um ganha na sua convenção", com o teste do zero como juiz do TCC.
5. Rodar o **Kaggle** para ter os modelos maiores (YOLO11m, RT-DETR, DocLayout-YOLO).
