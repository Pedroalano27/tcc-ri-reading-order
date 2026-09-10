# Resultados Preliminares

Primeira bateria completa de experimentos, executada em **2026-09-10** numa
RTX 4050 Laptop (6 GB) e CPU i7-12650HX. O desenho experimental está em
[METODOLOGIA.md](METODOLOGIA.md); os números brutos, em `resultados/`
(`comparacao.json`, `comparacao.md`, `caracterizacao.json` e os logs de cada etapa).

> ⚠️ **Como ler estes resultados.** A referência é um rótulo *silver* (a ordem do
> fluxo do PDF nos veículos em que ela é confiável), o treino tem só 152 páginas de
> 7 veículos, e cada experimento foi rodado uma vez, com uma semente. São resultados
> **preliminares**: servem para validar o pipeline, dimensionar o problema e orientar
> as próximas decisões — não para as conclusões finais do TCC, que dependem do
> Golden Dataset anotado manualmente.

---

## 1. Caracterização: a ordem interna do PDF não é confiável

Amostra de **777 páginas de 30 veículos** (23 UFs e 7 municípios; o PI foi excluído
por ter 86% do texto ilegível). **50% das páginas são multicoluna.**

Para cada página foram comparadas três ordens (τ de Kendall mediano):

| Par de ordens | τ mediano |
|---|---:|
| Ingênua (topo→base, esq.→dir.) × fluxo do PDF | 0,556 |
| XY-cut (heurística de colunas) × fluxo do PDF | 0,618 |
| Ingênua × XY-cut | 0,923 |

**O fluxo de conteúdo do PDF só se comporta como ordem de leitura em 11 dos 30
veículos** (τ mediano com a XY-cut ≥ 0,7). Com o limiar mais exigente de 0,9, sobram
apenas 4 (CE, Volta Redonda, PR e MA).

O caso mais revelador são os veículos de **coluna única**, onde ler é trivialmente de
cima para baixo — a ordem ingênua e a XY-cut coincidem (τ = 1,00) — e ainda assim o
fluxo do PDF discorda: Manaus (τ = 0,33), Congonhas (0,33), Tocantins (0,58),
Curitiba (0,57), Porto Alegre (0,61). Nesses veículos, o software de publicação grava
o texto numa ordem que não é a de leitura.

**Implicação para o TCC:** ter o PDF digital *não* resolve o problema. A ordem
interna do arquivo não é confiável na maioria dos veículos, então um método de ordem
de leitura baseado em layout é necessário mesmo sem OCR. Isso reforça a motivação do
trabalho — e mostra por que o Golden Dataset manual é indispensável: o rótulo silver
só existe para um terço dos veículos.

**Caso a auditar:** em SP, a XY-cut e o fluxo do PDF estão *anticorrelacionados*
(τ = −0,12), com 92% das páginas multicoluna. Ou a heurística falha no layout de SP,
ou o fluxo está invertido — precisa de inspeção visual.

![Concordância por veículo](figuras/fig1_caracterizacao_por_veiculo.png)

![O problema numa página real](figuras/fig2_problema_pagina_real.png)

---

## 2. Configuração

| Partição | Veículos | Páginas |
|---|---|---:|
| Treino | Volta Redonda (RJ), Salvador (BA), PA, PE, PR, RR, SC | 152 |
| Validação | RN | 15 |
| Teste | CE, MA, RJ | 95 |

Referência: ordem do fluxo do PDF, nos veículos com τ mediano ≥ 0,7 contra a XY-cut.
Os veículos de teste nunca aparecem no treino. O LayoutLM e sua ablação foram
treinados com o mesmo orçamento: 40 épocas (seção 4.3).

---

## 3. Comparação principal — 95 páginas de teste

| Método | τ Kendall (IC 95%) ↑ | τ pior caso (p10) ↑ | ARD ↓ | ARD norm. ↓ | BLEU ↑ | Acerto exato ↑ | Latência (ms/pág.) ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | −0,005 (−0,056 a 0,043) | −0,200 | 16,29 | 0,330 | 94,2 | 1,1% | 0,001 |
| Ingênua (topo→base, esq.→dir.) | 0,753 (0,704 a 0,804) | 0,347 | 5,84 | 0,106 | 96,9 | 1,1% | 0,015 |
| **XY-cut (heurística de colunas)** | **0,837** (0,788 a 0,880) | **0,496** | **3,46** | **0,067** | 96,8 | **18,9%** | 0,141 |
| BiLSTM: só texto | 0,066 (0,024 a 0,111) | −0,195 | 16,21 | 0,309 | 94,2 | 1,1% | 6,8 |
| BiLSTM: só geometria | 0,731 (0,691 a 0,769) | 0,459 | 5,85 | 0,105 | 94,7 | 7,4% | 7,1 |
| BiLSTM: texto + geometria | 0,628 (0,588 a 0,666) | 0,334 | 7,09 | 0,136 | 94,3 | 2,1% | 8,3 |
| LayoutLM sem layout (ablação) | 0,122 (0,084 a 0,160) | −0,099 | 15,64 | 0,294 | 94,1 | 0,0% | 13,8 |
| LayoutLM: texto + layout 2D | 0,671 (0,636 a 0,707) | 0,345 | 6,25 | 0,123 | 94,6 | 3,2% | 18,0 |

### Subconjunto com a LLM — 15 páginas com até 25 blocos

Todos os métodos nas mesmas 15 páginas. Por serem páginas pequenas, a ordem entre os
métodos muda: aqui a ingênua supera a XY-cut.

| Método | τ Kendall (IC 95%) ↑ | τ p10 ↑ | ARD norm. ↓ | Latência (ms/pág.) ↓ |
|---|---:|---:|---:|---:|
| Ingênua | **0,817** (0,724 a 0,905) | 0,562 | 0,073 | 0,006 |
| BiLSTM: só geometria | 0,732 (0,630 a 0,827) | 0,419 | 0,104 | 2,6 |
| XY-cut | 0,680 (0,492 a 0,843) | 0,429 | 0,126 | 0,043 |
| LayoutLM | 0,658 (0,549 a 0,768) | 0,333 | 0,131 | 17,6 |
| LayoutLM sem layout | 0,233 (0,120 a 0,344) | −0,099 | 0,261 | 12,5 |
| **LLM llava:7b (zero-shot)** | **0,099** (−0,027 a 0,224) | −0,333 | 0,306 | **8.414,7** |
| Ordem do detector | 0,040 (−0,173 a 0,257) | −0,410 | 0,309 | 0,001 |

---

## 4. O que os números dizem

### 4.1 A heurística XY-cut é o método a bater
Com τ = 0,837, o melhor pior caso (0,496) e 18,9% das páginas perfeitamente
ordenadas, a heurística de colunas vence todos os métodos aprendidos nesta rodada —
em 0,14 ms por página. O resultado é coerente com a literatura: em layouts regulares,
regras geométricas são fortes. **O espaço para modelos aprendidos está nas páginas em
que a heurística falha** — e a seção 4.6 mostra onde elas estão.

Uma ressalva que favorece a XY-cut: os veículos de teste foram escolhidos entre os que
têm fluxo confiável, e a confiabilidade foi medida pela concordância *com a própria
XY-cut*. O Golden Dataset elimina esse viés.

### 4.2 Layout é indispensável
| | Sem geometria | Com geometria |
|---|---:|---:|
| BiLSTM | 0,066 (só texto) | 0,731 (só geometria) |
| LayoutLM (40 épocas nos dois casos) | 0,122 (caixas zeradas) | 0,671 |

Com os blocos embaralhados, **o texto sozinho quase não recupera a ordem de leitura**.
Sem as caixas, o LayoutLM ainda pesca pistas textuais — cabeçalhos tendem a vir
primeiro, assinaturas e rodapés por último —, o que explica o τ de 0,122 em vez de
zero; mas perde 0,55 de τ. Esta é a evidência mais limpa desta rodada a favor da
premissa do trabalho: **a informação que resolve a tarefa está na geometria 2D**.

### 4.3 Com pouco dado, geometria explícita vence texto
O BiLSTM **só com geometria** (0,731) superou o BiLSTM **com texto e geometria**
(0,628) e o LayoutLM (0,671). Com 152 páginas de treino, o texto codificado por
*hashing* (16 milhões de parâmetros de *embedding*) mais atrapalha do que ajuda — o
modelo sobreajusta.

O treino do LayoutLM foi feito em duas rodadas:

| Rodada | Épocas | Tempo | Melhor τ na validação | τ no teste |
|---|---:|---:|---:|---:|
| 1 | 8 | 56 s | 0,606 (ainda subindo) | 0,660 |
| 2 | 40 | 247 s | 0,631 (estável desde a época 10) | 0,671 |

Quintuplicar o treino rendeu só +0,011 de τ no teste: **o gargalo é o volume de dados
rotulados, não o tempo de treino.**

![Curvas de treino](figuras/fig3_treino_layoutlm.png)

### 4.4 A LLM zero-shot falha — e o modo de falha é revelador
O `llava:7b` obteve τ = **0,099**, estatisticamente indistinguível do acaso no
subconjunto de 15 páginas. Mas o dado mais interessante é *como* ele erra:

| τ da ordem devolvida pela LLM contra… | média | mediana |
|---|---:|---:|
| …a ordem em que os blocos **chegaram** | 0,661 | **0,905** |
| …a ordem **correta** | 0,099 | 0,121 |

**A LLM ecoa a ordem de entrada.** Em 11 das 15 páginas, a resposta ficou mais perto da
ordem em que os blocos foram apresentados do que da ordem correta. Em vez de raciocinar
sobre as coordenadas, o modelo tende a devolver os rótulos na sequência em que os leu
(B1, B2, B4, B5, …).

**Confiabilidade de formato:** 12 de 15 respostas (80%) eram permutações válidas. As
falhas foram de três tipos — bloco repetido (21 rótulos com 20 distintos), geração
além do necessário (29 rótulos para 18 blocos) e omissão (17 de 21 blocos).

**Custo:** 8,4 s por página em média (1,8 a 17,6 s), ~1.155 tokens de entrada e ~77 de
saída, 11,9 tokens/s. No mesmo subconjunto, é **~480 vezes** a latência do LayoutLM e
**~200 mil vezes** a da XY-cut.

Ressalvas importantes: o `llava:7b` é um modelo **multimodal**, não um modelo de texto
especializado; com contexto de 8.192 tokens ele **não coube inteiro nos 6 GB da GPU**
(34% das camadas rodaram na CPU, o que infla a latência); e 15 páginas é uma amostra
pequena. O próximo passo é repetir com um modelo de texto (`qwen2.5:7b`) e com
exemplos no prompt (*few-shot*).

### 4.5 O BLEU não discrimina nesta granularidade
A ordem **aleatória** marca BLEU **94,2**; a XY-cut, 96,8. Em nível de bloco, quase
todos os n-gramas são internos aos blocos e sobrevivem a qualquer reordenação (numa
página totalmente invertida, o BLEU ainda dá 82,7). **As conclusões devem se apoiar no
τ de Kendall e no ARD**; o BLEU fica como métrica de continuidade com a literatura.

### 4.6 A vantagem da heurística encolhe com o número de colunas

| Método | 1 coluna (39 págs.) | 2 colunas (39) | 3+ colunas (17) |
|---|---:|---:|---:|
| XY-cut | 0,896 | 0,821 | 0,737 |
| Ingênua | 0,793 | 0,731 | 0,709 |
| BiLSTM: só geometria | 0,713 | 0,758 | 0,709 |
| LayoutLM | 0,627 | 0,725 | 0,649 |
| *Vantagem da XY-cut sobre o LayoutLM* | *0,269* | *0,096* | *0,088* |

A XY-cut perde 0,16 de τ entre páginas de 1 e de 3+ colunas; os modelos aprendidos
são mais estáveis entre os grupos. A vantagem da heurística sobre o LayoutLM cai de
0,27 nas páginas de coluna única para 0,09 nas de três ou mais colunas. **É nos
layouts difíceis que o modelo aprendido chega mais perto** — onde há mais a ganhar.

![τ por número de colunas](figuras/fig6_tau_por_colunas.png)

### 4.7 Eficiência
| Método | Latência por página | Onde roda |
|---|---:|---|
| Ingênua | 0,015 ms | CPU |
| XY-cut | 0,14 ms | CPU |
| BiLSTM | 7–8 ms | CPU |
| LayoutLM | 18 ms | GPU (~3 GB de VRAM no treino) |
| LLM llava:7b | 8.400 ms | GPU + CPU (não cabe em 6 GB) |

![Eficácia × eficiência](figuras/fig4_tradeoff_eficacia_eficiencia.png)

![Distribuição do τ por página](figuras/fig5_distribuicao_tau_por_pagina.png)

---

## 5. Significância estatística

Testes de Wilcoxon pareados sobre o τ por página:

| Comparação | Páginas | τ médio | p-valor |
|---|---:|---|---:|
| LayoutLM × ordem do detector | 95 | 0,671 × −0,005 | 8,4·10⁻¹⁷ |
| LayoutLM × ingênua | 95 | 0,671 × 0,753 | 0,013 |
| LayoutLM × XY-cut | 95 | 0,671 × 0,837 | 2,6·10⁻¹¹ |
| LayoutLM × BiLSTM só texto | 95 | 0,671 × 0,066 | 2,6·10⁻¹⁶ |
| LayoutLM × BiLSTM só geometria | 95 | 0,671 × 0,731 | 8,2·10⁻⁹ |
| LayoutLM × BiLSTM texto + geometria | 95 | 0,671 × 0,628 | 4,6·10⁻⁵ |
| LayoutLM × LayoutLM sem layout | 95 | 0,671 × 0,122 | 2,6·10⁻¹⁶ |
| LayoutLM × LLM | 15 | 0,658 × 0,099 | 6,1·10⁻⁵ |
| XY-cut × LLM | 15 | 0,680 × 0,099 | 0,0012 |

Todas as diferenças são significativas ao nível de 5%.

---

## 6. Limitações desta rodada

- **Referência silver** e escolha dos veículos confiáveis pela concordância com a
  XY-cut — viés a favor da heurística.
- **Pouco dado de treino**: 152 páginas de 7 veículos.
- **Uma única execução** por método; sem variação de semente.
- **LLM**: modelo multimodal, 15 páginas, parcialmente na CPU.
- **Tokenizador do LayoutLM em inglês**, sem acentos.
- **Granularidade de bloco** depende da heurística de segmentação.

## 7. O que isto sugere para o TCC

1. A premissa se sustenta: **o problema existe mesmo em PDFs digitais** (seção 1) e
   **a geometria é o que resolve a tarefa** (seção 4.2).
2. A comparação central muda de figura: o competidor a bater não é a LLM — que falhou
   e custa ~480× mais que o LayoutLM —, mas a **heurística geométrica**. A pergunta
   mais interessante passa a ser *em que páginas um modelo aprendido supera a
   heurística*, e a que custo — e a seção 4.6 aponta para os layouts de muitas colunas.
3. As próximas prioridades (detalhadas em [ROADMAP.md](ROADMAP.md)): Golden Dataset
   manual, mais dados de treino, LLM de texto e *few-shot*, auditoria visual do
   rótulo silver.

## Figuras

| Arquivo | Conteúdo |
|---|---|
| `figuras/fig1_caracterizacao_por_veiculo.png` | Concordância entre ordens, por veículo |
| `figuras/fig2_problema_pagina_real.png` | Ordem ingênua × referência numa página real |
| `figuras/fig3_treino_layoutlm.png` | Curvas de treino e validação (LayoutLM e ablação) |
| `figuras/fig4_tradeoff_eficacia_eficiencia.png` | τ × latência — o trade-off do TCC |
| `figuras/fig5_distribuicao_tau_por_pagina.png` | Distribuição do τ por página (pior caso) |
| `figuras/fig6_tau_por_colunas.png` | τ por número de colunas |
