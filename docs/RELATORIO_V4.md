# Relatório de Avaliação — Golden v4 e Comparação de Segmentação

> Relatório técnico consolidado da ordem de leitura humana no `golden_v4` (regiões Diamond)
> confrontada com o `golden_v3` (blocos automáticos v3), testes de hipóteses, sensibilidade
> e medições de segmentação e esforço humano.

## 1. Resumo Executivo

1. O lote `golden_v4` possui **44 páginas concluídas** (1 pulada) anotadas por especialista humano sobre as regiões refinadas manualmente no Diamond.
2. O modelo multimodal **Gemini 3.1 Flash Lite lidera o ranking global**: a configuração **com marcas, sem classes** atingiu **τ = 0,966** (IC 95%: 0,937–0,988; 94,2% de sucessor; 40/44 permutações válidas, 90,9%) e a configuração **com marcas e classes** obteve **τ = 0,962** (IC 95%: 0,925–0,987; 94,4% de sucessor; 38/44 válidas, 86,4%).
3. **Não há efeito mensurável das classes humanas no prompt do VLM**: a diferença de τ entre a versão com classes e sem classes é de apenas **-0,004** (Wilcoxon pareado p = 0,078, sem significância estatística). Além disso, no `golden_v3` (onde o prompt não recebia classes humanas, apenas anotação de tabelas pelo detector), o VLM com marcas já alcançava **τ = 0,924** (88,9% de sucessor). As **marcas visuais sobre a imagem (Set-of-Mark)** têm efeito medido: sem marcas visuais, o τ recua de 0,962 para 0,942 (Wilcoxon pareado p = 0,0087), o acerto de sucessor cai de 94,4% para 90,3% e as permutações válidas caem de 38 para 30 de 44 (86,4% → 68,2%). Mesmo sem marcas, o VLM ainda supera a XY-cut após Holm.
4. As **LLMs de texto** (Qwen 3.8 27B e Gemma 4 31B), avaliadas no Kaggle sobre 2× Tesla T4, recebem exclusivamente texto e coordenadas normalizadas (sem classes e sem imagem). A melhor LLM foi a **LLM Qwen 3.8 27B (few-shot 2)**, com **τ = 0,876**, 75,9% de sucessor correto e 29/44 (65.9%) permutações válidas, ficando abaixo do VLM com marcas (τ = 0,962).
5. Entre os modelos locais e LLMs, embora o **LayoutLM sucessor (semente 42)** (τ = 0,890; média das 3 sementes: τ = 0,870 ± 0,022, sucessor 62,1%) e a melhor LLM de texto (LLM Qwen 3.8 27B (few-shot 2), τ = 0,876) apresentem τ médio numericamente superior à heurística XY-cut (τ = 0,825, sucessor 71,5%), **a diferença não é estatisticamente significativa** após correção de comparações múltiplas por Holm-Bonferroni (p ajustado = 1,00 e 0,92, respectivamente; p bruto = 0,183 e 0,077).
6. Nos testes pareados de Wilcoxon com correção de Holm contra a XY-cut (21 comparações), **apenas as três configurações do VLM obtiveram superioridade estatisticamente significante** (com marcas e classes: p = 5,43e-06; com marcas, sem classes: p = 9,76e-06; sem marcas, com classes: p = 1,98e-04). Nenhuma formulação do LayoutLM, nenhuma das quatro LLMs e nem a ordem ingênua apresentaram diferença significante frente à XY-cut.
7. Nas **20 páginas comuns** entre `golden_v3` e `golden_v4`, o τ do LayoutLM sucessor permaneceu estável (+0,003, p = 0,981), porém a continuidade local sofreu queda de **-10,1 pontos percentuais** no sucessor correto (68,3% → 58,3%, p = 0,055). As LLMs de texto também apresentaram redução de τ nas 20 páginas (Qwen 3.8 27B fs2: 0,932 → 0,845, Δ = -0,087), mas a queda não é estatisticamente significativa (p = 0,121).
8. O custo humano ativo para anotar a ordem sobre as regiões Diamond no `golden_v4` teve mediana de **16,0 s/página** (total de 12,8 min para as 44 páginas). Trata-se de tarefas diferentes da retificação geométrica de caixas e rotulagem de classes no Diamond, com tempo menor (4 a 6 vezes mais rápido que a mediana de 98,5 s no piloto e 67,0 s no treino). Entre as páginas do `golden_v4`, as medianas foram de 17,0 s/página nas 20 páginas já vistas (ordenadas no `golden_v3`) e 15,0 s/página nas 24 novas, sem efeito aparente de familiaridade nesta amostra.

## 2. Resultados no `golden_v4` (44 páginas)

Avaliação contra a ordem humana anotada por **Pedro alano** em 44 páginas concluídas sobre as regiões do Diamond. Métodos ordenados por τ médio decrescente.

| Método | n | τ Kendall médio (IC 95%) | Mediana | p10 | Sucessor correto | ARD norm. | Acerto exato | Permutações válidas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| VLM Gemini 3.1 Flash Lite (sem classes) | 44 | **0,966** (0,937–0,988) | 1,000 | 0,830 | 94,2% | 0,016 | 65,9% | 40/44 (90.9%) |
| VLM Gemini 3.1 Flash Lite (com marcas) | 44 | **0,962** (0,925–0,987) | 1,000 | 0,889 | 94,4% | 0,017 | 68,2% | 38/44 (86.4%) |
| VLM Gemini 3.1 Flash Lite (sem marcas) | 44 | **0,942** (0,908–0,971) | 1,000 | 0,760 | 90,3% | 0,025 | 52,3% | 30/44 (68.2%) |
| LayoutLM sucessor (semente 42) | 44 | **0,890** (0,845–0,932) | 0,940 | 0,667 | 66,6% | 0,043 | 9,1% | 44/44 (100%) |
| LayoutLM suc. sem viés geom. | 44 | **0,880** (0,820–0,928) | 0,959 | 0,771 | 68,9% | 0,049 | 9,1% | 44/44 (100%) |
| LLM Qwen 3.8 27B (few-shot 2) | 44 | **0,876** (0,820–0,923) | 0,958 | 0,692 | 75,9% | 0,051 | 36,4% | 29/44 (65.9%) |
| LayoutLM sucessor (semente 2) | 44 | **0,873** (0,822–0,919) | 0,951 | 0,667 | 65,7% | 0,051 | 6,8% | 44/44 (100%) |
| LayoutLM suc. sem texto | 44 | **0,863** (0,796–0,918) | 0,930 | 0,670 | 72,9% | 0,055 | 22,7% | 44/44 (100%) |
| LLM Qwen 3.8 27B (zero-shot) | 44 | **0,859** (0,781–0,923) | 0,967 | 0,569 | 80,2% | 0,058 | 36,4% | 31/44 (70.5%) |
| LayoutLM pontual (semente 1) | 44 | **0,852** (0,785–0,905) | 0,912 | 0,714 | 38,2% | 0,054 | 13,6% | 44/44 (100%) |
| LayoutLM pontual (semente 2) | 44 | **0,850** (0,791–0,899) | 0,901 | 0,697 | 38,8% | 0,056 | 11,4% | 44/44 (100%) |
| LLM Gemma 4 31B (few-shot 2) | 44 | **0,848** (0,770–0,922) | 0,981 | 0,357 | 78,9% | 0,063 | 34,1% | 31/44 (70.5%) |
| LayoutLM sucessor (semente 1) | 44 | **0,847** (0,792–0,896) | 0,905 | 0,667 | 53,8% | 0,060 | 9,1% | 44/44 (100%) |
| LayoutLM pontual (semente 42) | 44 | **0,847** (0,803–0,887) | 0,898 | 0,686 | 35,3% | 0,060 | 6,8% | 44/44 (100%) |
| XY-cut (heurística de colunas) | 44 | **0,825** (0,763–0,886) | 0,922 | 0,538 | 71,5% | 0,083 | 27,3% | 44/44 (100.0%) |
| LLM Gemma 4 31B (zero-shot) | 44 | **0,822** (0,746–0,892) | 0,979 | 0,401 | 79,9% | 0,078 | 34,1% | 37/44 (84.1%) |
| Ingênua (topo→base, esq.→dir.) | 44 | **0,713** (0,639–0,785) | 0,648 | 0,339 | 57,5% | 0,124 | 18,2% | 44/44 (100.0%) |
| Fluxo do PDF (referência silver) | 44 | **0,632** (0,497–0,761) | 0,832 | 0,000 | 73,9% | 0,137 | 13,6% | 44/44 (100.0%) |
| LayoutLM suc. sem posição | 44 | **0,321** (0,188–0,453) | 0,272 | -0,287 | 66,3% | 0,266 | 6,8% | 44/44 (100%) |
| LayoutLM suc. sem layout | 44 | **0,280** (0,196–0,371) | 0,266 | -0,118 | 31,4% | 0,247 | 2,3% | 44/44 (100%) |
| LayoutLM pontual sem layout | 44 | **0,124** (0,058–0,184) | 0,089 | -0,062 | 9,6% | 0,289 | 0,0% | 44/44 (100%) |
| Ordem do detector (entrada embaralhada) | 44 | **0,053** (0,014–0,094) | 0,054 | -0,143 | 5,3% | 0,319 | 0,0% | 44/44 (100.0%) |

### Resumo das Formulações do LayoutLM (3 Sementes)

- **LayoutLM Pontual (sementes 42, 1, 2):** τ médio = **0,850 ± 0,003** | Sucessor = **37,4% ± 1,9%** | ARD norm. = **0,057 ± 0,003** | Acerto exato = **10,6% ± 3,5%**
- **LayoutLM Sucessor (sementes 42, 1, 2):** τ médio = **0,870 ± 0,022** | Sucessor = **62,1% ± 7,1%** | ARD norm. = **0,051 ± 0,009** | Acerto exato = **8,3% ± 1,3%**

## 3. Testes Pareados contra a Heurística XY-cut no `golden_v4`

Teste de postos com sinais de Wilcoxon pareado página a página (n = 44) entre cada método e a heurística de referência XY-cut. Correção de comparações múltiplas por Holm-Bonferroni (α = 0,05).

| Posto | Método | n | Δ τ médio | p-valor bruto | Limiar Holm | p-valor ajustado | Sobrevive Holm? | Interpretação |
|---:|---|---:|---:|---:|---:|---:|:---:|---|
| 1 | Ordem do detector (entrada embaralhada) | 44 | -0,772 | 7.61e-09 | 2.38e-03 | 1.60e-07 | **Sim** | Inferior à XY-cut (p < limiar Holm) |
| 2 | LayoutLM pontual sem layout | 44 | -0,700 | 8.16e-09 | 2.50e-03 | 1.63e-07 | **Sim** | Inferior à XY-cut (p < limiar Holm) |
| 3 | LayoutLM suc. sem layout | 44 | -0,545 | 2.36e-08 | 2.63e-03 | 4.49e-07 | **Sim** | Inferior à XY-cut (p < limiar Holm) |
| 4 | LayoutLM suc. sem posição | 44 | -0,504 | 6.77e-07 | 2.78e-03 | 1.22e-05 | **Sim** | Inferior à XY-cut (p < limiar Holm) |
| 5 | VLM Gemini 3.1 Flash Lite (com marcas) | 44 | +0,137 | 5.43e-06 | 2.94e-03 | 9.23e-05 | **Sim** | Superior à XY-cut (p < limiar Holm) |
| 6 | VLM Gemini 3.1 Flash Lite (sem classes) | 44 | +0,141 | 9.76e-06 | 3.13e-03 | 1.56e-04 | **Sim** | Superior à XY-cut (p < limiar Holm) |
| 7 | VLM Gemini 3.1 Flash Lite (sem marcas) | 44 | +0,117 | 1.98e-04 | 3.33e-03 | 2.97e-03 | **Sim** | Superior à XY-cut (p < limiar Holm) |
| 8 | Ingênua (topo→base, esq.→dir.) | 44 | -0,112 | 7.39e-03 | 3.57e-03 | 1.04e-01 | **Não** | Sem diferença significativa |
| 9 | Fluxo do PDF (referência silver) | 44 | -0,193 | 5.49e-02 | 3.85e-03 | 7.13e-01 | **Não** | Sem diferença significativa |
| 10 | LLM Qwen 3.8 27B (few-shot 2) | 44 | +0,052 | 7.68e-02 | 4.17e-03 | 9.22e-01 | **Não** | Sem diferença significativa |
| 11 | LLM Qwen 3.8 27B (zero-shot) | 44 | +0,034 | 1.80e-01 | 4.55e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 12 | LayoutLM sucessor (semente 42) | 44 | +0,066 | 1.83e-01 | 5.00e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 13 | LayoutLM suc. sem texto | 44 | +0,038 | 2.12e-01 | 5.56e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 14 | LayoutLM suc. sem viés geom. | 44 | +0,055 | 2.16e-01 | 6.25e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 15 | LayoutLM sucessor (semente 2) | 44 | +0,049 | 2.71e-01 | 7.14e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 16 | LayoutLM pontual (semente 1) | 44 | +0,027 | 2.97e-01 | 8.33e-03 | 1.00e+00 | **Não** | Sem diferença significativa |
| 17 | LLM Gemma 4 31B (few-shot 2) | 44 | +0,023 | 3.30e-01 | 1.00e-02 | 1.00e+00 | **Não** | Sem diferença significativa |
| 18 | LayoutLM pontual (semente 2) | 44 | +0,026 | 3.97e-01 | 1.25e-02 | 1.00e+00 | **Não** | Sem diferença significativa |
| 19 | LayoutLM pontual (semente 42) | 44 | +0,022 | 6.84e-01 | 1.67e-02 | 1.00e+00 | **Não** | Sem diferença significativa |
| 20 | LayoutLM sucessor (semente 1) | 44 | +0,022 | 7.12e-01 | 2.50e-02 | 1.00e+00 | **Não** | Sem diferença significativa |
| 21 | LLM Gemma 4 31B (zero-shot) | 44 | -0,003 | 8.38e-01 | 5.00e-02 | 1.00e+00 | **Não** | Sem diferença significativa |

> **Análise de significância:** Das 21 comparações, **7 sobrevivem à correção de Holm**: três superiores à XY-cut (VLM Gemini 3.1 Flash Lite (com marcas), VLM Gemini 3.1 Flash Lite (sem classes), VLM Gemini 3.1 Flash Lite (sem marcas)) e quatro inferiores (Ordem do detector (entrada embaralhada), LayoutLM pontual sem layout, LayoutLM suc. sem layout, LayoutLM suc. sem posição). Nenhuma formulação do LayoutLM, nenhuma das quatro LLMs de texto e nem a ordem ingênua apresentaram diferença estatisticamente significante contra a XY-cut após correção múltipla; embora o τ médio do LayoutLM sucessor (Δ = +0,066) e das LLMs (Δ = +0,023 a +0,052) seja numericamente maior, a variabilidade entre páginas impede sustentar superioridade estatística.

## 4. Efeito da Segmentação nas 20 Páginas Comuns (`golden_v3` × `golden_v4`)

> **Ressalva metodológica:** A referência humana também mudou entre os dois conjuntos. No `golden_v3`, a ordem foi anotada sobre os blocos produzidos pelo extrator automático v3; no `golden_v4`, a ordem foi reanotada pelo mesmo anotador sobre as regiões retificadas à mão no Diamond.

| Método | τ v3 | τ v4 | Δ τ (v4−v3) | p (τ) | Sucessor v3 | Sucessor v4 | Δ Sucessor | p (suc.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LayoutLM suc. sem layout | 0,371 | 0,214 | **-0,158** | 5.26e-02 | 31,9% | 24,3% | **-7,6%** | 2.66e-01 |
| LayoutLM suc. sem posição | 0,484 | 0,205 | **-0,278** | 1.13e-02 | 71,0% | 60,6% | **-10,3%** | 3.86e-02 |
| LayoutLM suc. sem texto | 0,880 | 0,846 | **-0,034** | 6.36e-01 | 78,5% | 64,0% | **-14,5%** | 8.98e-03 |
| LayoutLM suc. sem viés geom. | 0,898 | 0,868 | **-0,029** | 7.56e-01 | 71,5% | 62,5% | **-9,0%** | 6.84e-02 |
| Ordem do detector (entrada embaralhada) | 0,012 | 0,030 | **+0,019** | 7.47e-01 | 7,6% | 6,1% | **-1,4%** | 4.92e-01 |
| Fluxo do PDF (referência silver) | 0,545 | 0,528 | **-0,017** | 6.79e-01 | 71,1% | 69,5% | **-1,5%** | 5.10e-01 |
| LayoutLM pontual (semente 42) | 0,867 | 0,865 | **-0,002** | 8.13e-01 | 34,8% | 32,9% | **-2,0%** | 4.38e-01 |
| LayoutLM pontual sem layout | 0,235 | 0,143 | **-0,092** | 6.83e-02 | 11,4% | 10,1% | **-1,4%** | 3.88e-01 |
| LayoutLM sucessor (semente 42) | 0,864 | 0,867 | **+0,003** | 9.81e-01 | 68,3% | 58,3% | **-10,1%** | 5.52e-02 |
| LLM Gemma 4 31B (zero-shot) | 0,901 | 0,836 | **-0,064** | 7.36e-02 | 80,7% | 74,6% | **-6,1%** | 4.68e-02 |
| LLM Gemma 4 31B (few-shot 2) | 0,890 | 0,827 | **-0,063** | 2.15e-01 | 79,8% | 72,7% | **-7,1%** | 2.11e-01 |
| LLM Qwen 3.8 27B (zero-shot) | 0,922 | 0,836 | **-0,086** | 8.40e-02 | 75,4% | 76,1% | **+0,7%** | 7.58e-01 |
| LLM Qwen 3.8 27B (few-shot 2) | 0,932 | 0,845 | **-0,087** | 1.21e-01 | 77,7% | 71,6% | **-6,1%** | 7.03e-02 |
| Ingênua (topo→base, esq.→dir.) | 0,748 | 0,724 | **-0,025** | 3.27e-01 | 55,8% | 54,8% | **-0,9%** | 5.51e-01 |
| LayoutLM pontual (semente 1) | 0,907 | 0,896 | **-0,011** | 3.31e-01 | 48,2% | 41,7% | **-6,5%** | 5.35e-02 |
| LayoutLM pontual (semente 2) | 0,891 | 0,879 | **-0,013** | 5.57e-01 | 44,7% | 41,9% | **-2,9%** | 5.00e-01 |
| LayoutLM sucessor (semente 1) | 0,882 | 0,833 | **-0,049** | 2.67e-01 | 62,2% | 46,5% | **-15,7%** | 3.65e-02 |
| LayoutLM sucessor (semente 2) | 0,888 | 0,867 | **-0,021** | 2.87e-01 | 69,1% | 58,5% | **-10,6%** | 2.77e-02 |
| VLM Gemini 3.1 Flash Lite (com marcas) | 0,941 | 0,937 | **-0,004** | 5.28e-01 | 91,6% | 92,0% | **+0,4%** | 1.00e+00 |
| VLM Gemini 3.1 Flash Lite (sem classes) | — | — | — | — | — | — | — | Ausente no golden_v3 |
| VLM Gemini 3.1 Flash Lite (sem marcas) | — | — | — | — | — | — | — | Ausente no golden_v3 |
| XY-cut (heurística de colunas) | 0,816 | 0,783 | **-0,033** | 7.77e-02 | 74,1% | 66,9% | **-7,3%** | 3.07e-01 |

## 5. Avaliação por Tipo de Página no `golden_v4`

Desempenho em τ de Kendall estratificado por densidade de colunas e presença de tabelas para os métodos-chave.

| Estrutura da Página | n | XY-cut | LayoutLM sucessor (sem. 42) | VLM com marcas | Qwen 3.8 27B (few-shot 2) |
|---|---:|---:|---:|---:|---:|
| 1 coluna (Colunas) | 24 | 0,752 | 0,920 | **0,949** | 0,863 |
| 2 colunas (Colunas) | 13 | 0,919 | 0,847 | **0,978** | 0,860 |
| 3+ colunas (Colunas) | 7 | 0,901 | 0,869 | **0,975** | 0,951 |
| Sem tabela (Tabela) | 30 | 0,815 | 0,897 | **0,948** | 0,870 |
| Com tabela (Tabela) | 14 | 0,846 | 0,876 | **0,992** | 0,890 |

*Nota sobre LLMs:* As LLMs de texto (Qwen 3.8 27B e Gemma 4 31B) recebem exclusivamente texto e coordenadas dos blocos no prompt, sem classes anotadas e sem a imagem da página. A coluna fixa o modelo **LLM Qwen 3.8 27B (few-shot 2)**, melhor LLM no resultado global do `golden_v4` (τ = 0,876), evitando seleção oportunista da melhor LLM em cada estrato.

## 6. Avaliação do Modelo Visual-Linguístico (VLM)

### 6.1 Ablação de Marcas Visuais e Classes Semânticas

| Configuração | n | τ Kendall médio (IC 95%) | Sucessor correto | Permutações válidas | Latência média |
|---|---:|---:|---:|---:|---:|
| **Com marcas e classes** (`gemini-3.1-flash-lite`) | 44 | **0,962** (0,925–0,987) | **94,4%** | 38/44 (86,4%) | 9,4 s/pág. |
| **Com marcas, sem classes** (`gemini-3.1-flash-lite`) | 44 | **0,966** (0,937–0,988) | 94,2% | **40/44 (90,9%)** | 7,4 s/pág. |
| **Sem marcas, com classes** (`gemini-3.1-flash-lite`) | 44 | 0,942 (0,908–0,971) | 90,3% | 30/44 (68,2%) | 6,2 s/pág. |

#### Análise do Papel das Classes Semânticas vs. Marcas Visuais

1. **Impacto das classes no prompt:** No desenho original do `golden_v4`, cada caixa fornecida ao VLM trazia a classe semântica anotada manualmente no Diamond (`cabecalho`, `rodape`, `assinatura`, `texto`, `titulo`, `tabela`). Na ablação **sem classes**, o modelo recebeu a mesma imagem com marcas e as mesmas coordenadas e textos, sem a classe. A diferença no τ de Kendall médio foi de apenas **-0,004** (0,962 com classes vs. 0,966 sem classes), com teste pareado de Wilcoxon indicando ausência de significância estatística (**p = 0,078**). A proporção de permutações válidas inclusive subiu de 86,4% para 90,9%.
2. **Confirmação pelo `golden_v3`:** No lote `golden_v3` (47 páginas), onde as caixas eram oriundas do extrator automático e não possuíam classes humanas (apenas anotação geométrica de tabelas pelo detector Docling Heron), o mesmo VLM com marcas obteve **τ = 0,924** e **88,9%** de sucessor correto, indicando que o desempenho não depende de classes humanas prévias para ordenar páginas de Diários Oficiais.
3. **Efeito das marcas visuais (Set-of-Mark):** A comparação pareada entre a versão com marcas e classes e a versão sem marcas e com classes nas mesmas 44 páginas resulta em: τ 0,962 → 0,942 (Wilcoxon pareado p = 0,0087), acerto de sucessor de 94,4% para 90,3% e permutações válidas 38 → 30 de 44 (86,4% → 68,2%). Mesmo sem marcas visuais, o VLM ainda supera a XY-cut com significância estatística após correção de Holm (p bruto = 1,98e-04; p ajustado por Holm = 2,97e-03).
4. **Comparação com LLMs textuais:** Modelos puramente textuais (Qwen 3.8 27B e Gemma 4 31B), que recebem texto e coordenadas sem classes e sem a renderização visual da página, atingiram no máximo τ = 0,876 (LLM Qwen 3.8 27B (few-shot 2); 29/44 (65.9%) de permutações válidas). No entanto, essa comparação mistura duas dimensões (modalidade e família/tamanho de modelo), não permitindo atribuir a diferença à integração multimodal; o desenho experimental não separa o efeito da imagem do efeito do modelo, pois uma comparação isolada da imagem exigiria rodar o mesmo Gemini apenas com texto.

### 6.2 As 5 Piores Páginas do VLM com Marcas

Páginas do `golden_v4` com menor τ de Kendall para o VLM Gemini 3.1 Flash Lite (com marcas e classes). Todas as colunas contêm valores estritamente mensurados a partir das anotações e predições.

| Posto | ID da Página | Blocos | Colunas | Tabelas | Válida? | Rótulos devolvidos | τ Kendall | Sucessor correto |
|---:|---|---:|---:|---:|:---:|---:|---:|---:|
| 1 | `official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0` | 19 | 1 | 0 | Sim | 19 | **0,368** | 88,9% |
| 2 | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 129 | 1 | 0 | Não | 120 | **0,721** | 57,0% |
| 3 | `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | 100 | 2 | 0 | Não | 94 | **0,788** | 32,3% |
| 4 | `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31` | 49 | 1 | 0 | Sim | 49 | **0,828** | 85,4% |
| 5 | `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | 42 | 3 | 0 | Não | 41 | **0,889** | 80,5% |

## 7. LayoutLM Fora do Domínio de Treinamento

O modelo LayoutLM foi treinado sobre blocos automáticos do extrator v3 (`data/processed/blocos/`). Abaixo avalia-se o comportamento ao ser aplicado às regiões retificadas à mão no Diamond (`golden_v4`).

| Formulação e Semente | τ no `golden_v3` (47 págs.) | τ no `golden_v4` (44 págs.) | Queda relativa τ | Sucessor `v3` | Sucessor `v4` | Queda relativa Sucessor |
|---|---:|---:|---:|---:|---:|---:|
| LayoutLM Pontual (semente 42) | 0,846 | 0,847 | **+0,1%** | 32,8% | 35,3% | **+7,6%** |
| LayoutLM Pontual (semente 1) | 0,879 | 0,852 | **-3,1%** | 42,0% | 38,2% | **-9,1%** |
| LayoutLM Pontual (semente 2) | 0,866 | 0,850 | **-1,8%** | 37,9% | 38,8% | **+2,5%** |
| LayoutLM Sucessor (semente 42) | 0,845 | 0,890 | **+5,4%** | 66,8% | 66,6% | **-0,2%** |
| LayoutLM Sucessor (semente 1) | 0,865 | 0,847 | **-2,1%** | 61,1% | 53,8% | **-11,8%** |
| LayoutLM Sucessor (semente 2) | 0,882 | 0,873 | **-0,9%** | 67,6% | 65,7% | **-2,8%** |

- **Média LayoutLM Pontual:** τ 0,864 → 0,850 (-1,6%)
- **Média LayoutLM Sucessor:** τ 0,864 → 0,870 (+0,7%)

> **Observação sobre continuidade local:** Embora o τ de Kendall se mantenha praticamente estável, a acurácia de sucessor correto sofre reduções quando testada nas 20 páginas comuns. A queda de -10,1 pp na semente 42 tem p = 0,055 (não significativa); as sementes 1 e 2 apresentam p bruto de 0,037 e 0,028 sem correção para múltiplos testes. A queda observada é compatível com a sensibilidade do sucessor ao corte das caixas, lembrando que a referência humana também foi reanotada entre os dois conjuntos (limitação 3).

## 8. Avaliação da Segmentação no Diamond

Reprodução dos resultados de `resultados/diamond/*/avaliacao.json` comparando a segmentação em regiões contra o gabarito humano.

### Diamond Piloto (20 páginas, in-sample)

| Sistema | Páginas | Regiões gabarito | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (% palavras) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `v3` | 20 | 523 (754) | 0,647 | 0,512 | 0,457 | 0,296 | 83,8% |
| `proposta` | 20 | 764 (754) | 0,937 | 0,870 | 0,867 | 0,788 | 90,7% |
| `regioes_v2` | 20 | 763 (754) | 0,952 | 0,893 | 0,887 | 0,840 | 91,4% |
| `regioes` | 20 | 764 (754) | 0,951 | 0,891 | 0,885 | 0,848 | 91,5% |
| `rose:rose_piloto_v2` | 19 | 667 (674) | 0,955 | 0,908 | 0,901 | 0,847 | 89,3% |
| `regioes_v3+rose:todas` | 19 | 686 (674) | 0,949 | 0,887 | 0,881 | 0,843 | 89,3% |
| `regioes_v3+rose:assinatura_cabecalho` | 19 | 686 (674) | 0,949 | 0,887 | 0,881 | 0,857 | 91,2% |
| `regioes_v3+rose:assinatura_cabecalho_titulo_rodape` | 19 | 686 (674) | 0,949 | 0,887 | 0,881 | 0,856 | 91,1% |

### Diamond Treino (25 páginas anotadas)

| Sistema | Páginas | Regiões gabarito | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (% palavras) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `v3` | 25 | 650 (770) | 0,689 | 0,576 | 0,561 | 0,324 | 85,2% |
| `proposta` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,789 | 90,7% |
| `regioes_v2` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,789 | 90,7% |
| `regioes` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,793 | 90,7% |
| `rose:rose_treino` | 25 | 838 (770) | 0,908 | 0,883 | 0,881 | 0,764 | 90,0% |
| `regioes_v3+rose:todas` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,766 | 90,0% |
| `regioes_v3+rose:assinatura_cabecalho` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,800 | 91,4% |
| `regioes_v3+rose:assinatura_cabecalho_titulo_rodape` | 25 | 857 (770) | 0,916 | 0,899 | 0,896 | 0,793 | 91,1% |

## 9. Custo Humano de Anotação e Custo Computacional

### 9.1 Custo Humano de Anotação

Tempo ativo de trabalho por página registrado na ferramenta de anotação (apenas páginas concluídas).

| Conjunto | Tarefa humana | Páginas concluídas | Tempo total ativo | Mediana por página | Média por página | Média por elemento |
|---|---|---:|---:|---:|---:|---:|
| **golden_v2** | Golden v2 (ordem sobre blocos v3) | 26 | **18,2 min** | **27,5 s** | 42,0 s | 1,6 s/bloco |
| **golden_v4** | Golden v4 (ordem sobre regiões Diamond) | 44 | **12,8 min** | **16,0 s** | 17,4 s | 0,5 s/bloco |
| **diamond_piloto** | Diamond piloto (caixas e classes) | 20 | **55,1 min** | **98,5 s** | 165,2 s | 4,2 s/bloco |
| **diamond_treino** | Diamond treino (caixas e classes) | 25 | **34,6 min** | **67,0 s** | 83,1 s | 2,6 s/bloco |

**Familiaridade no `golden_v4`:** Do total de 44 páginas concluídas do `golden_v4`, **20 páginas já haviam sido ordenadas** pelo mesmo anotador humano durante a campanha do `golden_v3` (sobre os blocos do extrator v3). As medianas foram de 17,0 s nas 20 páginas já vistas e 15,0 s nas 24 novas, sem efeito aparente de familiaridade nesta amostra:
- **20 páginas já vistas (ordenadas no v3):** mediana de **17,0 s/página** (média 19,1 s; tempo total 6,3 min).
- **24 páginas novas:** mediana de **15,0 s/página** (média 16,1 s; tempo total 6,4 min).
- **Total (44 páginas):** mediana de **16,0 s/página** (média 17,4 s; tempo total 12,8 min).

Cabe ressaltar que ordenar blocos e retificar caixas são tarefas diferentes. O tempo de anotação da ordem sobre regiões pré-segmentadas é menor (4 a 6 vezes mais rápido) do que a retificação geométrica de caixas e rotulagem de classes no Diamond (mediana de 67,0 s a 98,5 s).

### 9.2 Custo Computacional de Inferência

Registro de tempo de execução e taxa de permutações válidas para os métodos neurais e LLMs avaliados no `golden_v4`. As LLMs de texto foram executadas via Ollama no Kaggle (2× Tesla T4, contexto 8.192 tokens); o VLM foi executado via API Gemini 3.1 Flash Lite.

| Método | Modelo | Few-shot | Plataforma | Tempo / pág. | Permutações válidas | Tempo total |
|---|---|---|---|---:|---:|---:|
| LLM Qwen 3.8 27B (zero-shot) | `qwen3.8:27b` | 0 ex. | Tesla T4 + Tesla T4 | 20,29 s | 68.9% | 15,7 min |
| LLM Qwen 3.8 27B (few-shot 2) | `qwen3.8:27b` | 2 ex. | Tesla T4 + Tesla T4 | 21,66 s | 64.4% | 16,7 min |
| LLM Gemma 4 31B (zero-shot) | `gemma4:31b` | 0 ex. | Tesla T4 + Tesla T4 | 27,76 s | 82.2% | 21,6 min |
| LLM Gemma 4 31B (few-shot 2) | `gemma4:31b` | 2 ex. | Tesla T4 + Tesla T4 | 31,17 s | 68.9% | 24,1 min |
| VLM Gemini 3.1 Flash Lite (com marcas) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | 9,4 s | 38/44 (86,4%) | — |
| VLM Gemini 3.1 Flash Lite (sem classes) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | 7,4 s | 40/44 (90,9%) | — |
| VLM Gemini 3.1 Flash Lite (sem marcas) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | 6,2 s | 30/44 (68,2%) | — |
| LayoutLM sucessor (semente 42) | `layoutlm_sucessor` | — | Local (RTX 4050) | ~0,02 s | 44/44 (100%) | < 1 s |
| XY-cut | — | — | Local (CPU) | < 0,001 s | 44/44 (100%) | < 0,1 s |

## 10. Limitações

1. **Anotador único:** Todas as anotações do `golden_v4` e dos lotes do Diamond foram realizadas por um único anotador humano (Pedro alano). Não há medida de concordância inter-anotador para este lote (o teto teórico só foi medido no `golden_v1`/`v2`).
2. **Ancoragem da proposta no Diamond:** O anotador corrigiu caixas e classes a partir da pré-anotação gerada pelo algoritmo (`proposta`), o que ancora as decisões humanas nas fronteiras pré-existentes e infla a aparente precisão da proposta.
3. **Referência reanotada:** Na comparação entre `golden_v3` e `golden_v4` nas 20 páginas comuns, além da segmentação ter mudado, a ordem de leitura foi refeita, misturando o efeito de corte de blocos com possíveis variações de julgamento do anotador.
4. **Texto só em imagem:** Conforme levantamento de 13/09 registrado no `COMUNICACAO_AGENTES.md`, **13,8% das páginas do acervo** possuem regiões de texto impressas puramente como imagem (sem palavras digitais na camada do PDF). Como o pipeline atual não inclui OCR, essas regiões permanecem totalmente invisíveis aos modelos de ordenação.
5. **Classes humanas e regras no prompt do VLM:** As classes das caixas fornecidas no prompt do VLM provêm da anotação humana realizada no Diamond, e o prompt incorpora as mesmas regras e convenções do guia seguido pelo anotador. Embora a ablação sem classes demonstre que o modelo mantém τ = 0,966 mesmo sem os rótulos de classe, a presença das diretrizes de ordenação no system prompt do modelo multimodal favorece o VLM em comparação com métodos heurísticos e neurais locais que operam sem acesso a essas regras explícitas.
6. **Segmentação corrigida à mão:** O `golden_v4` utiliza segmentação retificada manualmente pelo especialista no Diamond. Dessa forma, os resultados medem o desempenho da ordenação com segmentação ideal, não o pipeline automático completo de ponta a ponta.
7. **VLM em API fechada no nível gratuito:** O modelo Gemini 3.1 Flash Lite foi avaliado via API comercial no nível gratuito. Como a API é fechada, a versão interna do modelo pode mudar pelo provedor, impondo limitações de reprodutibilidade.

## 11. Próximos Passos Sugeridos

1. **Re-treinar o LayoutLM sobre as regiões Diamond:** O modelo atual treinado no extrator v3 preserva o τ global médio (0,850 e 0,870), mas sofreu redução de continuidade local nas 20 páginas comuns (-10,1 pp no sucessor correto para a semente 42, p = 0,055). Hipótese a testar: o re-treino sobre as caixas Diamond restabelece as transições aprendidas entre regiões retificadas.
2. **Avaliar o VLM como fonte de rótulo de ordem:** O Gemini 3.1 Flash Lite com marcas obteve τ = 0,962 (com classes) e τ = 0,966 (sem classes), com 94,4% e 94,2% de sucessor correto (diferença estatisticamente significante frente à XY-cut após correção de Holm, p = 5,43e-06 e p = 9,76e-06). Recomenda-se avaliar formalmente seu emprego para geração de pseudo-rótulos de ordem somente após mensurar a taxa de concordância inter-anotador com humanos em páginas inéditas e estritamente sem classes humanas no prompt (cenário em que atingiu τ = 0,966 no `golden_v4` e τ = 0,924 no `golden_v3`).
3. **Manter as marcas no protocolo do VLM:** A ausência de marcadores visuais (Set-of-Mark) reduziu o desempenho do Gemini 3.1 Flash Lite nas 44 páginas: τ 0,962 → 0,942 (Wilcoxon pareado p = 0,0087), acerto de sucessor de 94,4% para 90,3% e permutações válidas de 38 para 30 de 44 (86,4% → 68,2%). Mesmo sem marcas, o VLM ainda supera a XY-cut após Holm.
4. **Incorporar o Rose no classificador de blocos:** Na avaliação de segmentação em regiões, a comparação entre `regioes` (0,848) e `regioes_v3+rose:assinatura_cabecalho` (0,857) no piloto e 0,793 → 0,800 no treino (25 páginas) resultou em ganho de cerca de 0,01 no F1 com classe, o qual não foi testado estatisticamente.
5. **Escalar a anotação de ordem:** O tempo mediano de ordenação foi de 16,0 s/página no `golden_v4` (medianas de 17,0 s nas 20 páginas já vistas e 15,0 s nas 24 novas, sem efeito aparente de familiaridade nesta amostra). Por serem tarefas diferentes, o tempo de ordenação é menor (4 a 6 vezes) que a retificação geométrica de caixas e classes no Diamond (mediana de 67,0 s a 98,5 s), indicando baixo custo temporal para a ordenação sobre regiões pré-corrigidas.
