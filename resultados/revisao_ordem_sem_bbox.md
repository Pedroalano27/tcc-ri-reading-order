# Revisão Adversarial: Experimento "Ordem de Leitura Sem Bounding Box Fina"

**Objeto da auditoria:** Script [`orquestracao/analises/ordem_sem_bbox.py`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py) e relatório [`resultados/ordem_sem_bbox.md`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md).  
**Alegação sob escrutínio:** A ordenação direta de linhas (vales de projeção com tabela e imagem como blocos atômicos) atinge $\tau = 0,917$ contra $0,825$ da XY-cut sobre regiões humanas nas 44 páginas do `golden_v4`.

---

## Veredito

**O resultado NÃO se sustenta como evidência científica de que ordenar linhas sem caixas finas supera a XY-cut sobre regiões.**  
A superioridade nominal agregada ($\tau = 0,917$ vs $0,825$) é um artefato da métrica de projeção por mediana (que tolera intercalação severa), somado a heurísticas de margem ad-hoc e ao ganho restrito a páginas de coluna única ($0,752 \to 0,942$); no estrato multicoluna — onde a ordem de leitura é um problema real —, o método perde para a XY-cut em todas as métricas estruturais ($\tau$ de regiões $0,887$ vs $0,913$; sucessor de linhas $89,5\%$ vs $94,1\%$). Além disso, há circularidade no desenho do algoritmo (ajustado para consertar erros dessas exatas páginas) e a comparação é metodologicamente assimétrica, pois em produção não existem regiões humanas para mediar o ranqueamento.

---

## Lista de Problemas (do mais grave ao menos grave)

### 1. Efeito máscara da projeção por mediana (ocultação de intercalações severas)
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L393-L404`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L393-L404) (`projetar`) e [`resultados/ordem_sem_bbox.md#L31-L32`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L31-L32).
- **Problema:** O método proposto não prevê regiões: ele ordena fragmentos de linha e palavras soltas (`seq`). Para avaliar na "régua de regiões", calcula a mediana dos postos das palavras da região-ouro: `rr[rid] = statistics.median(rank[k] for k in ks)`.  
  **Demonstração do vício:** Suponha duas regiões contíguas de 10 palavras em duas colunas. Se o preditor intercalar perfeitamente as palavras (palavra da col 1, palavra da col 2, palavra da col 1...), a sequência real estará completamente destruída e ilegível. No entanto, os postos da coluna 1 serão $\{1, 3, 5, \dots, 19\}$ (mediana $10$) e os da coluna 2 serão $\{2, 4, 6, \dots, 20\}$ (mediana $11$). Ao ordenar por mediana, a ordem projetada das regiões fica `[Região 1, Região 2]`. O $\tau$ de Kendall resultante é **$1,000$ (perfeito)** e o sucessor de regiões é **$100\%$**, mascarando um colapso completo da leitura.
- **Evidência no próprio relatório:** Na régua de linhas do estrato multicoluna ([`resultados/ordem_sem_bbox.md#L120-L125`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L120-L125)), o sucessor cai de $94,1\%$ para $89,5\%$. Em páginas como Duque de Caxias (`#p44`, [`resultados/ordem_sem_bbox.md#L214`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L214)), o sucessor de linhas despenca de $95,3\%$ para $53,7\%$, enquanto a projeção por mediana de regiões ainda atribui $\tau$ elevado.
- **Correção sugerida:** Avaliar métodos sem caixas finas exclusivamente na sequência de saída produzida (palavras ou linhas). Se for necessário comparar contra regiões humanas, a penalidade por fragmentação deve invalidar a ordem (ex.: exigir contiguidade ou medir inversões no nível da palavra com BLEU/Word-Tau), em vez de colapsar tudo por mediana.

---

### 2. O Paradoxo Multicoluna (Perda onde a ordem de leitura é desafiadora)
- **Onde:** [`resultados/ordem_sem_bbox.md#L103-L127`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L103-L127) e [`orquestracao/analises/ordem_sem_bbox.py#L764-L767`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L764-L767).
- **Problema:** Em páginas de coluna única ($n=24$), ordenar texto é trivial (quase pura ordenação vertical por $y$). Toda a complexidade científica de ordem de leitura em Diários Oficiais reside no estrato **multicoluna** ($n=20$).  
  No estrato multicoluna:
  - $\tau$ de Kendall em regiões: **XY-cut ouro = $0,913$ vs Plano LOPO = $0,887$** (o plano perde por $-0,026$).
  - Sucessor em regiões: **XY-cut ouro = $83,5\%$ vs Plano LOPO = $79,4\%$** (o plano perde por $-4,1\%$).
  - ARD norm. em regiões: **XY-cut ouro = $0,041$ vs Plano LOPO = $0,047$** (pior).
  - Sucessor em linhas: **XY-cut ouro = $94,1\%$ vs Plano LOPO = $89,5\%$** (o plano perde por $-4,6\%$).  
  Todo o ganho global ($0,825 \to 0,917$) veio das páginas de 1 coluna ($0,752 \to 0,942$). O resultado agregado é uma manifestação clássica do Paradoxo de Simpson induzido pelo peso do estrato unicoluna.
- **Correção sugerida:** Não apresentar o número global de $0,917$ como manchete ou resumo sem a imediata ressalva de que o método perde para a XY-cut nas páginas multicoluna. Reclassificar os estratos com critério visual real (pois o relatório admite em [`#L129`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L129) que páginas com 2 e 3 colunas foram incorretamente rotuladas como 1 coluna pelo metadado antigo).

---

### 3. Comparação assimétrica e injusta com a XY-cut (Heurísticas de Margem)
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L358-L379`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L358-L379) vs [`#L428-L430`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L428-L430).
- **Problema:** O método proposto inclui uma regra hardcoded de margens e marcações:
  - Topo: centro $< 7\%$ e base $< 10\%$ da altura da página vai obrigatoriamente para o início ([`#L366`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L366));
  - Rodapé: centro $> 95\%$ vai obrigatoriamente para o fim ([`#L368`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L368));
  - Marcas (`RE_MARCACAO`): vão imediatamente antes do rodapé ([`#L364`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L364), [`#L379`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L379)).  
  A **XY-cut de referência (`xy_ouro`) NÃO recebeu essa política**. Ela foi executada de forma cega nas caixas humanas ([`#L423`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L423)).  
  A própria tabela de sensibilidade do relatório ([`resultados/ordem_sem_bbox.md#L158-L159`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L158-L159)) revela o impacto disso:
  - `xy_linhas` (sem margens): $\tau = 0,805$.
  - `xy_margens` (apenas adicionando as margens à XY-cut): $\tau = 0,907$!  
  Ou seja, mais de $80\%$ da diferença entre o baseline e a proposta decorre unicamente de terem sido injetadas regras ad-hoc de cabeçalho/rodapé/marcas no preditor novo, sem dar o mesmo tratamento ao competidor.
- **Correção sugerida:** Avaliar uma linha de base pareada justa: `xy_ouro_com_margens`. Comparar os métodos isolando a contribuição da projeção versus a contribuição da política de margens.

---

### 4. Circularidade no desenho do algoritmo e hiperparâmetros fora do LOPO
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L253`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L253), [`#L293`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L293), [`#L366-L368`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L366-L368), [`#L782-L787`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L782-L787) e [`resultados/ordem_sem_bbox.md#L41-L43`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L41-L43).
- **Problema:** O leave-one-page-out (LOPO) é nominal: ele apenas selecionou 3 hiperparâmetros na grade de 60 variantes (`score`, `gap`, `vale`). Toda a estrutura do algoritmo `projecao_local` foi desenvolvida inspecionando diretamente as falhas dessas mesmas 44 páginas:
  - Em [`#L782-L787`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L782-L787), o código contém testes específicos para as páginas do RJ e MA, cujas falhas motivaram as regras de "janela local" e "filtro de pontes de 10% da largura" ([`#L293`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L293): `min(c - b[0], b[2] - c) >= 0.10 * W`);
  - Limiares mágicos fixos: altura da janela local `max(100.0, 12 * h)` ([`#L253`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L253)), tolerância horizontal `0.015 * W` ([`#L262`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L262)), limites de margem $7\%$ e $95\%$ ([`#L366-L368`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L366-L368)).  
  Esses hiperparâmetros nunca foram variados nem validados em cross-validation; foram "chumbados" no código após visualização dos erros no conjunto de teste.
- **Correção sugerida:** Congelar os algoritmos e validar em páginas não vistas de outros diários, sem qualquer ajuste a posteriori.

---

### 5. Violação da independência amostral no LOPO (Agrupamento por Veículo)
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L735-L741`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L735-L741).
- **Problema:** As 44 páginas provêm de poucas edições repetidas dos mesmos veículos (ex.: Barra do Piraí, MS, AC, Porto Alegre). Deixar de fora uma página cuja edição "irmã" está no conjunto de treino não é uma validação out-of-sample real: o modelo já conhece a tipografia, a largura exata das colunas e a altura dos cabeçalhos do veículo. Não por acaso, em 42 das 44 páginas o LOPO escolheu exatamente a mesma configuração ([`resultados/ordem_sem_bbox.md#L45`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L45)).
- **Correção sugerida:** Implementar **Leave-One-Vehicle-Out** (partição por diário/veículo).

---

### 6. Fragilidade e falha crítica em casos de borda (Regiões e páginas vazias)
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L121`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L121) e [`#L139`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L139).
- **Problema:**  
  1. **Regiões-ouro sem palavras:** A linha 121 contém:  
     `assert all(kws), (pid, "regiao-ouro sem palavras; projecao nao definida")`.  
     Se uma página tiver uma imagem pura, carimbo ou caixa gráfica anotada pelo anotador humano sem palavras associadas, o script **aborta com exceção**. O método matemático da mediana é indefinido quando a região não contém palavras. O benchmark só rodou porque páginas com figuras puras foram previamente filtradas ou expurgadas do Golden.  
  2. **Páginas sem palavras:** A linha 139 faz `statistics.median(w[4] - w[2] for w in ws)`. Se `ws` for vazio, dispara `StatisticsError`.  
  3. **Palavras fora do ouro:** 24 palavras fora das regiões-ouro foram ignoradas na projeção ([`#L395`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L395)).
- **Correção sugerida:** Tratar explicitamente caixas puramente gráficas através de sua coordenada espacial (ex.: associar o posto do átomo mais próximo ou intercalar pelo envelope geométrico), removendo a dependência estrita de haver palavras em toda caixa.

---

### 7. Vícios na inferência estatística (Bootstrap condicional e teste de Wilcoxon)
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L452`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L452), [`#L469-L475`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L469-L475).
- **Problema:**  
  1. **Bootstrap condicional:** O bootstrap em [`#L446-L453`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L446-L453) reamostra as predições com a configuração já escolhida, em vez de reexecutar a seleção LOPO dentro de cada reamostra. Isso subestima a variância de seleção e gera intervalos de confiança excessivamente estreitos.  
  2. **Descarte massivo de empates no Wilcoxon:** O teste usa `zero_method="wilcox"` ([`#L469`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L469)). Na tabela ([`resultados/ordem_sem_bbox.md#L135-L137`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L135-L137)), há 11 empates em 44 páginas ($25\%$ da amostra descartada). O teste de Wilcoxon clássico com $N=33$ e dependência espacial entre páginas superestima a significância ($p = 0,013$).  
  3. **Correção de Holm restrita:** A correção de Holm ([`#L476-L480`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L476-L480)) foi aplicada apenas entre as 3 métricas da mesma régua, ignorando as duas réguas e as dezenas de iterações de teste de hipóteses exploratórias realizadas durante o desenvolvimento.
- **Correção sugerida:** Reamostrar por blocos (clusters de veículos) e incluir a etapa de seleção dentro do loop de bootstrap. Utilizar testes pareados por permutação que considerem empates (`zero_method="pratt"`).

---

### 8. Flattening horizontal cego em tabelas e quebra em tabelas adjacentes
- **Onde:** [`orquestracao/analises/ordem_sem_bbox.py#L291-L310`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L291-L310) e [`#L341`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L341).
- **Problema:**  
  1. Dentro do átomo de tabela, [`fluxo`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/orquestracao/analises/ordem_sem_bbox.py#L341) simplesmente agrupa palavras por $y$ e ordena por $x$. Uma tabela com leitura vertical por colunas ou blocos internos é cegamente achatada linha a linha.  
  2. Quando há duas tabelas paralelas lado a lado (ex.: Manaus, [`resultados/ordem_sem_bbox.md#L201`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L201), [`#L247`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L247)), o detector gera caixas ou pontes que bloqueiam o corte vertical. O desempate por topo subpontual inverteu a ordem completa das tabelas em Manaus ($\tau$ de linhas desabou para **$0,014$**).
- **Correção sugerida:** Adicionar tratamento para tabelas paralelas e reconhecer que átomos não podem ser tratados como caixas puramente horizontais sem análise estrutural interna.

---

### 9. O Paradoxo do Oráculo Tabela/Imagem
- **Onde:** [`resultados/ordem_sem_bbox.md#L60`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L60) e [`#L306-L310`](file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/ordem_sem_bbox.md#L306-L310).
- **Problema:** Ao substituir as detecções do Heron pelas caixas **humanas perfeitas** de tabelas e figuras (`oraculo_ti`), o $\tau$ de Kendall de regiões **caiu** de $0,917$ para $0,903$.  
  Um método robusto deveria melhorar ou se manter estável ao receber geometria perfeita. Essa queda demonstra que a heurística de vales de projeção depende de compensação de erros entre o detector e a projeção (overfitting em coordenadas ruidosas específicas).
- **Correção sugerida:** Documentar isso como evidência de instabilidade do algoritmo, e não como mera curiosidade contrafactual.

---

## O que precisaria ser feito para o número ser defensável numa banca de TCC

Para apresentar este experimento com solidez acadêmica diante de uma banca examinadora rigorosa, o autor precisaria:

1. **Abandonar a alegação de "vitória geral contra a XY-cut":**  
   Reconhecer de forma transparente e em destaque que a proposta **perde para a XY-cut em páginas multicoluna** ($\tau = 0,887$ vs $0,913$; sucessor $= 79,4\%$ vs $83,5\%$). A tese central deve admitir que o método é eficaz para colunas simples com cabeçalhos ruidosos, mas falha em layouts complexos.
2. **Avaliação na régua fim-a-fim real (Texto / Linhas):**  
   Eliminar a projeção retrospectiva por mediana como métrica primária. O método não gera regiões; portanto, seu resultado científico legítimo é na sequência de linhas ou na recuperação de passagens (avaliação extrínseca em RI/BM25). A régua de regiões só pode ser citada com aviso explícito de que a mediana mascara intercalações.
3. **Isolamento rigoroso de variáveis (Ablação de Margens):**  
   Apresentar o baseline da XY-cut acrescido da mesma política de margens (`xy_com_margens`). Se a XY-cut com margens obtém $\tau = 0,907$, a banca perceberá de imediato que o ganho do algoritmo de projeção pura é marginal ($+0,010$).
4. **Conjunto de Teste Independente e Divisão por Veículo (Leave-One-Vehicle-Out):**  
   Avaliar a configuração congelada em um lote de páginas novas nunca inspecionadas durante o desenho do código, garantindo que nenhum veículo do teste apareça no ajuste de parâmetros.
5. **Robustez a Casos de Borda sem Asserções:**  
   Substituir o `assert all(kws)` por tratamento elegante de elementos puramente visuais, provando que o pipeline é funcional em PDFs reais com figuras decorativas e páginas sem texto.
