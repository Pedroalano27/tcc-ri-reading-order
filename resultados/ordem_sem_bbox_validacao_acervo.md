# Validação no acervo: ordem de leitura sem bounding box fina

Estado: **concluído**.

## Resumo em cinco linhas

1. **Veredito:** O ganho médio de τ se confirma em páginas humanas novas, sobretudo multicoluna detectada; não se confirma superioridade geral, pois a continuidade piora e o teste pareado é inconclusivo.
2. Nas 27 humanas novas: τ de palavras 0,971, XY-cut pura 0,913, XY-cut com margens 0,918; Δ justo 0,053.
3. Nas 86 silver novas: τ de palavras 0,968, XY-cut pura 0,942, com margens 0,948; Δ justo 0,020; a seleção silver favorece XY-cut.
4. Fragmentação do método: 3,1% das regiões por página em A nova e 2,7% em B nova; a mediana de regiões não mede a sequência real.
5. Recomendação: manter o método como experimento congelado e reportar condições/estratos; não substituir o pipeline nem alegar generalização para veículos inéditos com esta amostra.

## Amostra e ausência de ajuste

Configuração principal **`projecao_local_margens_s0.45_g1.2_v0.08`**, escolhida anteriormente no golden_v4. Sensibilidade **`projecao_local_s0.45_g1.2_v0.08`**: muda apenas a política de margens. Não há grade, seleção, treino ou ajuste nestes dados.

| Conjunto | Páginas previstas | Avaliadas | Veículos avaliados |
|---|---:|---:|---:|
| A — humanas novas | 27 | 27 | 10 |
| A — humanas repetidas | 20 | 20 | 19 |
| B — silver novas | 86 | 86 | 3 |
| B — silver completo | 89 | 89 | 3 |
| B — silver repetidas (diagnóstico) | 3 | 3 | 3 |

Repetição = igualdade literal de `page_id` contra **todas** as tarefas do golden_v4, incluindo a página pulada. Novidade aqui é de página, não necessariamente de veículo/template. A humana usa `referencia.jsonl` concluída e os blocos v3; a silver usa `carregar_particao('teste')` e `referencia()` do protocolo, sem trocar segmentação.

A e B compartilham **21 páginas**; não agregamos as amostras. As referências A e B podem divergir nessas páginas. B completo e B novo também não são evidências independentes.

**Silver enviesado em favor da XY-cut:** seus veículos foram escolhidos porque o fluxo de conteúdo do PDF concordava com a heurística. Essa referência não substitui leitura humana e não autoriza declarar todo desacordo erro do método.

A ordem humana do Golden foi anotada de forma cega, sem sugestão automática de ordenação. A geometria/segmentação dos blocos já é automática; parte da referência foi projetada de uma segmentação anterior apenas em páginas sem conflito. Portanto a independência da ordem não torna a segmentação um ouro de palavras/células.

## Auditoria de extração e coordenadas

Palavras são extraídas de `data/raw/<uf>/<arquivo>` na página de índice zero, com `pdfplumber` e `palavras_da_pagina()` (fluxo, deduplicação e junção de letras do extrator). O preditor recebe apenas texto/geometria e detecções table/picture: não usa fluxo como ordem, ordem humana ou caixas finas. O sistema é `[x0, top, x1, bottom]` em pontos.

A associação é por centro, menor caixa e preferência por não figura, como no script original. Comparamos dimensões, envelopes das palavras por caixa e multiconjunto de tokens após a limpeza do extrator. Diferenças de agrupamento de linhas/translineação não são automaticamente erro de coordenadas. Nenhuma caixa é escalada ou reposicionada para melhorar resultado.

| Conjunto | Palavras extraídas | Sem bloco | Dono ambíguo | Blocos vazios | Páginas vazias | Excluídas por auditoria/extração | Maior erro de dimensões (pt) | Envelopes divergentes (>0,15 pt) | Tokens divergentes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A — humanas novas | 23803 | 25 | 25 | 0 | 0 | 0 | 0,03600 | 2 | 7 |
| A — humanas repetidas | 17277 | 18 | 2 | 0 | 0 | 0 | 0,05000 | 0 | 0 |
| B — silver novas | 90892 | 206 | 43 | 0 | 0 | 0 | 0,02400 | 2 | 6 |
| B — silver completo | 95311 | 218 | 43 | 0 | 0 | 0 | 0,02400 | 2 | 6 |

Layout disponível no cache original: 136 registros A/B; cache novo: 0; falhas de layout: 0. Valores A/B incluem a interseção, portanto não são contagem de páginas únicas.

Regiões vazias são contadas e excluídas **da projeção de todos os métodos**, sem mediana fictícia. Página sem duas palavras avaliáveis não ganha nota perfeita: é registrada sem medida. Erros de PDF/referência/coordenadas são registrados, não tratados por assert. Átomos table/picture sem palavras permanecem na saída do método, mas não têm ordem textual avaliável.

## Réguas e comparação justa

**Principal — sequência real de palavras:** índices distintos mesmo para palavras iguais. Referência = blocos na ordem humana (A) ou silver (B), expandidos por `linhas()` de cima para baixo e esquerda para direita dentro de cada bloco. Comparamos diretamente a permutação de palavras emitida pelo método; não projetamos palavras/linhas por mediana. Palavras sem bloco continuam na saída, mas não têm referência e saem das métricas. Médias macro por página.

**Continuidade:** fração de blocos com palavras que aparecem em mais de um trecho da saída. A versão principal ignora palavras sem dono como no original; a estrita também conta essas palavras como interrupção. Sucessor de trechos de linha/bloco usa a sequência real comprimindo somente repetições consecutivas do mesmo dono, preservando suas reaparições; compara pares com vizinhos da referência e penaliza intercalação. Não há mediana nessa régua.

**Secundária — regiões:** mediana dos postos das palavras de cada bloco, com desempate por geometria e ID; baselines usam sua ordem diretamente. Regiões sem palavras não entram. A mediana pode ocultar intercalação e estes números não decidem o veredito principal.

Todas as baselines recebem as mesmas caixas e a permutação `ordem_entrada()`. São comparadores condicionais à segmentação v3 disponível, e não uma medição ponta a ponta do custo de obtê-la. Na XY-cut com margens, a precedência e os limiares são idênticos: marcas por `RE_MARCACAO` primeiro na classificação; topo se centro < 7% e base < 10%; rodapé se centro > 95%; saída topo, corpo por XY-cut, marcas, rodapé. Faixas especiais ordenadas por `(top, x0, índice)`. As caixas de referência ficam inteiras, enquanto o método classifica fragmentos de linha/átomos: igualdade de política, não de granularidade.

## Tabela principal — saída real de palavras

| Conjunto | n / veículos | Método | τ (IC 95% por veículo) ↑ | Sucessor (IC 95%) ↑ | ARD norm. (IC 95%) ↓ |
|---|---:|---|---:|---:|---:|
| A — humanas novas | 27 / 10 | XY-cut pura | 0,913 [0,820; 0,980] | 98,9% [98,5%; 99,3%] | 0,043 [0,010; 0,088] |
| A — humanas novas | 27 / 10 | XY-cut + mesmas margens | 0,918 [0,824; 0,983] | 99,1% [98,5%; 99,5%] | 0,040 [0,008; 0,087] |
| A — humanas novas | 27 / 10 | Ingênua | 0,800 [0,666; 0,972] | 98,3% [97,2%; 99,5%] | 0,094 [0,014; 0,157] |
| A — humanas novas | 27 / 10 | Sem bbox fina — congelado | 0,971 [0,942; 0,998] | 98,1% [97,2%; 99,4%] | 0,014 [0,001; 0,028] |
| A — humanas novas | 27 / 10 | Sem bbox fina sem margens (sensibilidade) | 0,948 [0,894; 0,992] | 97,8% [97,0%; 99,0%] | 0,025 [0,004; 0,052] |
| A — humanas repetidas | 20 / 19 | XY-cut pura | 0,845 [0,722; 0,944] | 99,0% [98,5%; 99,4%] | 0,074 [0,027; 0,135] |
| A — humanas repetidas | 20 / 19 | XY-cut + mesmas margens | 0,950 [0,885; 0,989] | 98,8% [97,9%; 99,5%] | 0,022 [0,005; 0,049] |
| A — humanas repetidas | 20 / 19 | Ingênua | 0,771 [0,633; 0,892] | 98,2% [97,3%; 99,1%] | 0,108 [0,051; 0,174] |
| A — humanas repetidas | 20 / 19 | Sem bbox fina — congelado | 0,983 [0,971; 0,994] | 98,5% [97,0%; 99,4%] | 0,008 [0,003; 0,014] |
| A — humanas repetidas | 20 / 19 | Sem bbox fina sem margens (sensibilidade) | 0,940 [0,840; 0,994] | 98,6% [97,5%; 99,5%] | 0,030 [0,003; 0,080] |
| B — silver novas | 86 / 3 | XY-cut pura | 0,942 [0,861; 1,000] | 99,2% [98,7%; 99,7%] | 0,027 [0,000; 0,065] |
| B — silver novas | 86 / 3 | XY-cut + mesmas margens | 0,948 [0,871; 1,000] | 99,3% [99,0%; 99,7%] | 0,024 [0,000; 0,060] |
| B — silver novas | 86 / 3 | Ingênua | 0,780 [0,539; 1,000] | 98,6% [97,4%; 100,0%] | 0,102 [0,000; 0,190] |
| B — silver novas | 86 / 3 | Sem bbox fina — congelado | 0,968 [0,930; 1,000] | 98,8% [98,0%; 99,6%] | 0,015 [0,000; 0,032] |
| B — silver novas | 86 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,961 [0,920; 1,000] | 98,6% [97,9%; 99,6%] | 0,019 [0,000; 0,037] |
| B — silver completo | 89 / 3 | XY-cut pura | 0,934 [0,803; 1,000] | 99,2% [98,7%; 99,7%] | 0,029 [0,000; 0,083] |
| B — silver completo | 89 / 3 | XY-cut + mesmas margens | 0,939 [0,812; 1,000] | 99,3% [99,0%; 99,7%] | 0,026 [0,000; 0,079] |
| B — silver completo | 89 / 3 | Ingênua | 0,771 [0,507; 1,000] | 98,6% [97,4%; 100,0%] | 0,105 [0,000; 0,199] |
| B — silver completo | 89 / 3 | Sem bbox fina — congelado | 0,965 [0,909; 1,000] | 98,8% [98,0%; 99,6%] | 0,016 [0,000; 0,042] |
| B — silver completo | 89 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,958 [0,900; 1,000] | 98,7% [97,9%; 99,6%] | 0,020 [0,000; 0,047] |
| B — silver repetidas (diagnóstico) | 3 / 3 | XY-cut pura | 0,703 [0,114; 1,000] | 99,1% [97,5%; 100,0%] | 0,104 [0,000; 0,310] |
| B — silver repetidas (diagnóstico) | 3 / 3 | XY-cut + mesmas margens | 0,705 [0,114; 1,000] | 99,2% [97,5%; 100,0%] | 0,103 [0,000; 0,310] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Ingênua | 0,534 [0,114; 1,000] | 98,5% [97,5%; 100,0%] | 0,189 [0,000; 0,310] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Sem bbox fina — congelado | 0,888 [0,665; 1,000] | 99,4% [98,3%; 100,0%] | 0,055 [0,000; 0,164] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,884 [0,659; 1,000] | 99,3% [98,3%; 100,0%] | 0,057 [0,000; 0,167] |

**Interpretação do ganho humano novo:** Δ justo 0,05343 [0,00404; 0,12815]; Pratt por página p=0,289152, por veículo p=0,250000. Ganha/empata/perde em 9/12/6 páginas, mediana de Δ=0,00000. O IC da média pode ser positivo enquanto o teste de postos pareados é inconclusivo: medem aspectos distintos da distribuição. Algumas melhoras grandes sustentam a média; não há vitória uniforme.

### Sensibilidade à associação geométrica (diagnóstico posterior)

O RJ Municipalidades `#p0` tem letras estilizadas em caixas que se sobrepõem: a preferência pela menor caixa transfere uma letra entre blocos e muda seus envelopes; dimensões da página conferem. As outras divergências de tokens são translineação/pontuação produzidas por agrupadores de linhas diferentes. Conservamos o critério original e todos esses casos nas tabelas principais. A retirada da página com envelopes divergentes abaixo é somente diagnóstico posterior, sem reajuste do método nem do filtro principal.

| Conjunto | Páginas retiradas | n restante | τ palavras método | τ palavras XY-cut+margens | Δ |
|---|---|---:|---:|---:|---:|
| A — humanas novas | `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0` | 26 | 0,976 | 0,938 | 0,03760 |
| B — silver novas | `official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf#p0` | 85 | 0,969 | 0,954 | 0,01509 |

## Continuidade real

| Conjunto | Método | Blocos fragmentados (IC 95%) | Fragmentação estrita | Sucessor trechos de bloco | Sucessor trechos de linha |
|---|---|---:|---:|---:|---:|
| A — humanas novas | XY-cut pura | 0,0% [0,0%; 0,0%] | 0,0% | 73,9% | 92,9% |
| A — humanas novas | XY-cut + mesmas margens | 0,0% [0,0%; 0,0%] | 0,0% | 76,4% | 93,9% |
| A — humanas novas | Ingênua | 0,0% [0,0%; 0,0%] | 0,0% | 63,1% | 89,0% |
| A — humanas novas | Sem bbox fina — congelado | 3,1% [1,4%; 5,1%] | 3,1% | 80,3% | 91,3% |
| A — humanas novas | Sem bbox fina sem margens (sensibilidade) | 2,7% [1,1%; 5,1%] | 2,7% | 76,1% | 90,2% |
| A — humanas repetidas | XY-cut pura | 0,0% [0,0%; 0,0%] | 0,0% | 74,2% | 93,4% |
| A — humanas repetidas | XY-cut + mesmas margens | 0,0% [0,0%; 0,0%] | 0,0% | 77,4% | 92,5% |
| A — humanas repetidas | Ingênua | 0,0% [0,0%; 0,0%] | 0,0% | 58,7% | 88,4% |
| A — humanas repetidas | Sem bbox fina — congelado | 7,3% [2,6%; 13,4%] | 7,3% | 79,0% | 90,9% |
| A — humanas repetidas | Sem bbox fina sem margens (sensibilidade) | 3,3% [0,8%; 6,6%] | 3,3% | 83,1% | 93,4% |
| B — silver novas | XY-cut pura | 0,0% [0,0%; 0,0%] | 0,0% | 78,7% | 94,6% |
| B — silver novas | XY-cut + mesmas margens | 0,0% [0,0%; 0,0%] | 0,0% | 83,7% | 95,5% |
| B — silver novas | Ingênua | 0,0% [0,0%; 0,0%] | 0,0% | 69,6% | 90,3% |
| B — silver novas | Sem bbox fina — congelado | 2,7% [0,0%; 4,8%] | 2,8% | 82,0% | 93,7% |
| B — silver novas | Sem bbox fina sem margens (sensibilidade) | 1,3% [0,0%; 3,8%] | 1,5% | 80,1% | 93,2% |
| B — silver completo | XY-cut pura | 0,0% [0,0%; 0,0%] | 0,0% | 78,4% | 94,5% |
| B — silver completo | XY-cut + mesmas margens | 0,0% [0,0%; 0,0%] | 0,0% | 83,2% | 95,4% |
| B — silver completo | Ingênua | 0,0% [0,0%; 0,0%] | 0,0% | 69,0% | 90,3% |
| B — silver completo | Sem bbox fina — congelado | 2,7% [0,0%; 5,1%] | 2,9% | 82,1% | 93,8% |
| B — silver completo | Sem bbox fina sem margens (sensibilidade) | 1,4% [0,0%; 4,5%] | 1,6% | 80,2% | 93,2% |

Sucessor de palavras é dominado por pares internos a blocos longos e pode permanecer alto mesmo quando dois blocos inteiros se invertem; ler junto com τ e as duas medidas de continuidade. Baselines de blocos são contíguas por construção e emitem somente palavras associadas aos blocos; a fragmentação estrita delas não avalia posicionamento de palavras sem dono. No método, essas palavras permanecem na sequência real, e a versão estrita é um diagnóstico adicional de sua cobertura.

## Régua secundária — blocos por mediana

| Conjunto | n / veículos | Método | τ (IC 95% por veículo) ↑ | Sucessor (IC 95%) ↑ | ARD norm. (IC 95%) ↓ |
|---|---:|---|---:|---:|---:|
| A — humanas novas | 27 / 10 | XY-cut pura | 0,878 [0,771; 0,949] | 73,9% [61,3%; 81,9%] | 0,054 [0,023; 0,101] |
| A — humanas novas | 27 / 10 | XY-cut + mesmas margens | 0,901 [0,799; 0,966] | 76,4% [60,5%; 86,5%] | 0,044 [0,016; 0,088] |
| A — humanas novas | 27 / 10 | Ingênua | 0,806 [0,689; 0,952] | 63,1% [43,4%; 86,6%] | 0,088 [0,021; 0,139] |
| A — humanas novas | 27 / 10 | Sem bbox fina — congelado | 0,927 [0,854; 0,977] | 84,2% [77,6%; 89,4%] | 0,033 [0,011; 0,065] |
| A — humanas novas | 27 / 10 | Sem bbox fina sem margens (sensibilidade) | 0,892 [0,797; 0,956] | 79,8% [73,6%; 84,3%] | 0,049 [0,020; 0,092] |
| A — humanas repetidas | 20 / 19 | XY-cut pura | 0,816 [0,716; 0,903] | 74,2% [61,5%; 84,6%] | 0,086 [0,045; 0,133] |
| A — humanas repetidas | 20 / 19 | XY-cut + mesmas margens | 0,918 [0,872; 0,956] | 77,4% [65,9%; 88,0%] | 0,036 [0,020; 0,055] |
| A — humanas repetidas | 20 / 19 | Ingênua | 0,769 [0,664; 0,866] | 58,7% [44,3%; 73,4%] | 0,104 [0,060; 0,152] |
| A — humanas repetidas | 20 / 19 | Sem bbox fina — congelado | 0,924 [0,867; 0,974] | 86,3% [78,8%; 93,3%] | 0,033 [0,012; 0,056] |
| A — humanas repetidas | 20 / 19 | Sem bbox fina sem margens (sensibilidade) | 0,915 [0,844; 0,963] | 87,0% [80,7%; 92,1%] | 0,040 [0,018; 0,073] |
| B — silver novas | 86 / 3 | XY-cut pura | 0,900 [0,781; 0,989] | 78,7% [70,5%; 84,1%] | 0,041 [0,005; 0,088] |
| B — silver novas | 86 / 3 | XY-cut + mesmas margens | 0,938 [0,795; 0,988] | 83,7% [65,5%; 89,5%] | 0,025 [0,006; 0,079] |
| B — silver novas | 86 / 3 | Ingênua | 0,799 [0,483; 0,997] | 69,6% [22,7%; 98,2%] | 0,089 [0,001; 0,207] |
| B — silver novas | 86 / 3 | Sem bbox fina — congelado | 0,927 [0,824; 0,989] | 82,2% [71,7%; 84,9%] | 0,030 [0,005; 0,072] |
| B — silver novas | 86 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,904 [0,792; 0,990] | 81,2% [75,4%; 85,4%] | 0,041 [0,005; 0,086] |
| B — silver completo | 89 / 3 | XY-cut pura | 0,891 [0,717; 0,989] | 78,4% [66,2%; 84,5%] | 0,045 [0,005; 0,110] |
| B — silver completo | 89 / 3 | XY-cut + mesmas margens | 0,928 [0,730; 0,988] | 83,2% [61,5%; 89,8%] | 0,029 [0,006; 0,101] |
| B — silver completo | 89 / 3 | Ingênua | 0,790 [0,442; 0,997] | 69,0% [22,1%; 98,3%] | 0,092 [0,001; 0,220] |
| B — silver completo | 89 / 3 | Sem bbox fina — congelado | 0,922 [0,784; 0,989] | 82,5% [72,1%; 85,3%] | 0,033 [0,005; 0,092] |
| B — silver completo | 89 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,898 [0,752; 0,990] | 81,4% [75,3%; 85,8%] | 0,044 [0,005; 0,106] |
| B — silver repetidas (diagnóstico) | 3 / 3 | XY-cut pura | 0,622 [-0,053; 1,000] | 68,0% [13,9%; 100,0%] | 0,137 [0,000; 0,373] |
| B — silver repetidas (diagnóstico) | 3 / 3 | XY-cut + mesmas margens | 0,649 [-0,053; 1,000] | 71,3% [13,9%; 100,0%] | 0,124 [0,000; 0,373] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Ingênua | 0,536 [-0,053; 1,000] | 52,4% [13,9%; 100,0%] | 0,179 [0,000; 0,373] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Sem bbox fina — congelado | 0,767 [0,301; 1,000] | 92,1% [76,4%; 100,0%] | 0,108 [0,000; 0,325] |
| B — silver repetidas (diagnóstico) | 3 / 3 | Sem bbox fina sem margens (sensibilidade) | 0,727 [0,264; 1,000] | 87,9% [73,6%; 100,0%] | 0,128 [0,000; 0,343] |

## Inferência pareada contra XY-cut

IC percentil 95%: 5000 reamostras, semente 20261003. Reamostragem principal sorteia **veículos inteiros** com reposição e mantém todas suas páginas; estima a mesma média por página com denominador variável. Não refaz seleção porque a configuração está congelada. IC por páginas, solicitado inicialmente, aparece apenas como sensibilidade da diferença: ignora dependência do veículo.

Wilcoxon bilateral pareado com `zero_method='pratt'`, `method='auto'`, diferenças quantizadas em doze casas para evitar falsos não zeros. Mostramos p por página e por médias de veículo. O primeiro não corrige a correlação intraveículo; o segundo tem pouquíssimos grupos em B. p Holm por conjunto abrange as duas réguas, três métricas e duas baselines; não corrige a história de desenvolvimento nem os estratos exploratórios. IC com um veículo degenera e não mede generalização; B tem apenas três veículos.

| Conjunto | Régua | Comparador | Métrica | Δ método − comparador (IC veículo) | IC páginas | G/E/P | p Pratt página | p Holm | p Pratt veículo |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| A — humanas novas | palavras | XY-cut pura | tau | 0,05829 [0,01014; 0,13044] | [0,01616; 0,11364] | 18/5/4 | 0,001645 | 0,016659 | 0,117188 |
| A — humanas novas | palavras | XY-cut pura | sucessor | -0,00851 [-0,01613; 0,00195] | [-0,02476; 0,00332] | 13/6/8 | 0,460745 | 1,000000 | 0,882812 |
| A — humanas novas | palavras | XY-cut pura | ard | -0,02904 [-0,06502; -0,00507] | [-0,05695; -0,00765] | 18/5/4 | 0,001514 | 0,016659 | 0,117188 |
| A — humanas novas | palavras | XY-cut + mesmas margens | tau | 0,05343 [0,00404; 0,12815] | [0,01084; 0,10893] | 9/12/6 | 0,289152 | 1,000000 | 0,250000 |
| A — humanas novas | palavras | XY-cut + mesmas margens | sucessor | -0,00971 [-0,01778; 0,00107] | [-0,02619; 0,00237] | 5/14/8 | 0,427693 | 1,000000 | 0,375000 |
| A — humanas novas | palavras | XY-cut + mesmas margens | ard | -0,02668 [-0,06396; -0,00203] | [-0,05495; -0,00501] | 9/12/6 | 0,289152 | 1,000000 | 0,250000 |
| A — humanas novas | regioes | XY-cut pura | tau | 0,04969 [0,00908; 0,09672] | [0,00938; 0,08947] | 17/7/3 | 0,004870 | 0,043833 | 0,117188 |
| A — humanas novas | regioes | XY-cut pura | sucessor | 0,10294 [0,06414; 0,17962] | [0,05102; 0,16112] | 18/8/1 | 0,000231 | 0,002773 | 0,003906 |
| A — humanas novas | regioes | XY-cut pura | ard | -0,02195 [-0,04130; -0,00447] | [-0,03973; -0,00301] | 17/7/3 | 0,005251 | 0,043833 | 0,117188 |
| A — humanas novas | regioes | XY-cut + mesmas margens | tau | 0,02640 [0,00102; 0,06514] | [-0,00770; 0,06037] | 8/17/2 | 0,067801 | 0,406806 | 0,125000 |
| A — humanas novas | regioes | XY-cut + mesmas margens | sucessor | 0,07760 [0,01784; 0,18172] | [0,02695; 0,13649] | 9/17/1 | 0,009904 | 0,069328 | 0,062500 |
| A — humanas novas | regioes | XY-cut + mesmas margens | ard | -0,01136 [-0,02842; -0,00060] | [-0,02681; 0,00470] | 8/17/2 | 0,072107 | 0,406806 | 0,125000 |
| A — humanas repetidas | palavras | XY-cut pura | tau | 0,13758 [0,04153; 0,26292] | [0,04273; 0,25385] | 14/1/5 | 0,014456 | 0,173478 | 0,005831 |
| A — humanas repetidas | palavras | XY-cut pura | sucessor | -0,00539 [-0,02202; 0,00711] | [-0,01867; 0,00568] | 10/2/8 | 0,895951 | 1,000000 | 0,586565 |
| A — humanas repetidas | palavras | XY-cut pura | ard | -0,06618 [-0,12704; -0,01990] | [-0,12325; -0,02097] | 14/1/5 | 0,014456 | 0,173478 | 0,005831 |
| A — humanas repetidas | palavras | XY-cut + mesmas margens | tau | 0,03319 [-0,00338; 0,09800] | [-0,00328; 0,09440] | 8/2/10 | 0,985094 | 1,000000 | 0,762559 |
| A — humanas repetidas | palavras | XY-cut + mesmas margens | sucessor | -0,00322 [-0,01053; 0,00429] | [-0,00950; 0,00348] | 5/2/13 | 0,130206 | 0,874080 | 0,204472 |
| A — humanas repetidas | palavras | XY-cut + mesmas margens | ard | -0,01405 [-0,04057; 0,00142] | [-0,03927; 0,00141] | 8/3/9 | 0,910608 | 1,000000 | 0,686531 |
| A — humanas repetidas | regioes | XY-cut pura | tau | 0,10797 [-0,00909; 0,23419] | [0,00272; 0,21400] | 14/3/3 | 0,024727 | 0,224264 | 0,009799 |
| A — humanas repetidas | regioes | XY-cut pura | sucessor | 0,12143 [-0,02717; 0,27381] | [-0,01440; 0,25331] | 12/3/5 | 0,124869 | 0,874080 | 0,047965 |
| A — humanas repetidas | regioes | XY-cut pura | ard | -0,05251 [-0,10929; -0,00076] | [-0,10109; -0,00614] | 14/3/3 | 0,022426 | 0,224264 | 0,008711 |
| A — humanas repetidas | regioes | XY-cut + mesmas margens | tau | 0,00642 [-0,05663; 0,06985] | [-0,05538; 0,06566] | 9/7/4 | 0,338549 | 1,000000 | 0,171529 |
| A — humanas repetidas | regioes | XY-cut + mesmas margens | sucessor | 0,08909 [-0,01143; 0,19186] | [-0,00984; 0,18827] | 10/7/3 | 0,042429 | 0,339431 | 0,068233 |
| A — humanas repetidas | regioes | XY-cut + mesmas margens | ard | -0,00325 [-0,02916; 0,02221] | [-0,02739; 0,02206] | 9/7/4 | 0,338549 | 1,000000 | 0,171529 |
| B — silver novas | palavras | XY-cut pura | tau | 0,02625 [-0,00002; 0,06903] | [0,01111; 0,04430] | 43/15/28 | 0,000170 | 0,001193 | 0,500000 |
| B — silver novas | palavras | XY-cut pura | sucessor | -0,00419 [-0,01066; -0,00067] | [-0,00971; 0,00003] | 22/26/38 | 0,236387 | 0,945547 | 0,250000 |
| B — silver novas | palavras | XY-cut pura | ard | -0,01155 [-0,03247; 0,00001] | [-0,02042; -0,00443] | 44/15/27 | 0,000053 | 0,000428 | 0,500000 |
| B — silver novas | palavras | XY-cut + mesmas margens | tau | 0,02032 [-0,00002; 0,05914] | [0,00522; 0,03857] | 14/35/37 | 0,010348 | 0,062086 | 0,500000 |
| B — silver novas | palavras | XY-cut + mesmas margens | sucessor | -0,00560 [-0,01122; -0,00068] | [-0,01121; -0,00124] | 9/35/42 | 0,000006 | 0,000060 | 0,250000 |
| B — silver novas | palavras | XY-cut + mesmas margens | ard | -0,00862 [-0,02786; 0,00001] | [-0,01762; -0,00150] | 15/35/36 | 0,016050 | 0,080248 | 0,500000 |
| B — silver novas | regioes | XY-cut pura | tau | 0,02686 [-0,00055; 0,04896] | [0,00540; 0,04706] | 43/36/7 | 0,000000 | 0,000004 | 0,500000 |
| B — silver novas | regioes | XY-cut pura | sucessor | 0,03474 [0,00848; 0,06842] | [0,00715; 0,06036] | 38/39/9 | 0,000038 | 0,000345 | 0,250000 |
| B — silver novas | regioes | XY-cut pura | ard | -0,01138 [-0,02162; 0,00019] | [-0,01827; -0,00387] | 44/35/7 | 0,000000 | 0,000003 | 0,500000 |
| B — silver novas | regioes | XY-cut + mesmas margens | tau | -0,01093 [-0,03561; 0,02880] | [-0,03696; 0,01067] | 12/61/13 | 0,893008 | 1,000000 | 1,000000 |
| B — silver novas | regioes | XY-cut + mesmas margens | sucessor | -0,01440 [-0,06645; 0,06211] | [-0,05709; 0,02330] | 12/60/14 | 0,728035 | 1,000000 | 1,000000 |
| B — silver novas | regioes | XY-cut + mesmas margens | ard | 0,00457 [-0,00659; 0,01316] | [-0,00306; 0,01352] | 13/61/12 | 0,863312 | 1,000000 | 1,000000 |
| B — silver completo | palavras | XY-cut pura | tau | 0,03162 [-0,00002; 0,10604] | [0,01352; 0,05457] | 45/15/29 | 0,000090 | 0,000632 | 0,500000 |
| B — silver completo | palavras | XY-cut pura | sucessor | -0,00394 [-0,00923; -0,00070] | [-0,00940; 0,00000] | 24/26/39 | 0,361769 | 1,000000 | 0,250000 |
| B — silver completo | palavras | XY-cut pura | ard | -0,01284 [-0,04121; 0,00001] | [-0,02285; -0,00520] | 46/15/28 | 0,000028 | 0,000227 | 0,500000 |
| B — silver completo | palavras | XY-cut + mesmas margens | tau | 0,02582 [-0,00002; 0,09692] | [0,00754; 0,04903] | 15/36/38 | 0,014740 | 0,088441 | 0,500000 |
| B — silver completo | palavras | XY-cut + mesmas margens | sucessor | -0,00534 [-0,00974; -0,00071] | [-0,01091; -0,00131] | 10/36/43 | 0,000012 | 0,000121 | 0,250000 |
| B — silver completo | palavras | XY-cut + mesmas margens | ard | -0,00997 [-0,03695; 0,00001] | [-0,02001; -0,00236] | 16/36/37 | 0,022246 | 0,111228 | 0,500000 |
| B — silver completo | regioes | XY-cut pura | tau | 0,03085 [-0,00054; 0,06718] | [0,00973; 0,05119] | 45/37/7 | 0,000000 | 0,000001 | 0,500000 |
| B — silver completo | regioes | XY-cut pura | sucessor | 0,04172 [0,00826; 0,06925] | [0,01268; 0,07017] | 40/40/9 | 0,000015 | 0,000131 | 0,250000 |
| B — silver completo | regioes | XY-cut pura | ard | -0,01198 [-0,02209; 0,00019] | [-0,01879; -0,00478] | 46/36/7 | 0,000000 | 0,000001 | 0,500000 |
| B — silver completo | regioes | XY-cut + mesmas margens | tau | -0,00659 [-0,03467; 0,05381] | [-0,03296; 0,01641] | 13/63/13 | 0,932900 | 1,000000 | 0,750000 |
| B — silver completo | regioes | XY-cut + mesmas margens | sucessor | -0,00689 [-0,06470; 0,10541] | [-0,05139; 0,03232] | 13/62/14 | 0,899768 | 1,000000 | 0,750000 |
| B — silver completo | regioes | XY-cut + mesmas margens | ard | 0,00387 [-0,00978; 0,01282] | [-0,00356; 0,01262] | 14/63/12 | 0,715223 | 1,000000 | 1,000000 |

ARD negativo significa melhora. Ausência de significância não prova equivalência ou não inferioridade.

## Estratos — colunas, veículo, grupo e familiaridade

Critério fixo de colunas: palavras com centro entre 10% e 95% da altura, retirando marcas; `linhas_partidas(gap=1.2)`, `vales_locais(vale=0.08)` e fallback para `vales`. Cortes aceitos + um, até quatro colunas. Reutiliza o detector de calhas do método, aplicado às palavras antes dos átomos para não esconder calhas entre tabelas. Não lê `stats.n_colunas` nem ordem/caixas humanas. Uma coluna detectada não prova uma coluna visual; células podem criar falso corte. O máximo de colunas no decodificador também fica persistido para diagnóstico.

Cada célula de τ abaixo traz média [IC 95% agrupado por veículo]. Estratos por veículo com um só grupo têm IC degenerado; as médias servem para descrever casos, não para inferir novos templates. Não há ajuste por estrato.

### A — humanas novas

| Estrato | n / veículos | τ palavras fixo | τ XY-cut | τ XY-cut+margens | Δ justo palavras | τ regiões fixo / XY-cut+margens | Sucessor palavras fixo / justa | Fragmentação fixo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| colunas/1 coluna detectada | 14 / 7 | 0,997 [0,990; 1,000] | 0,998 [0,992; 1,000] | 0,997 [0,992; 1,000] | -0,000 | 0,926 / 0,915 | 99,2% / 99,4% | 2,5% |
| colunas/multicoluna detectada | 13 / 4 | 0,943 [0,893; 0,993] | 0,822 [0,622; 0,920] | 0,832 [0,625; 0,935] | 0,111 | 0,929 / 0,886 | 96,9% / 98,7% | 3,7% |
| familiaridade/veículo já visto no v4 | 27 / 10 | 0,971 [0,942; 0,998] | 0,913 [0,820; 0,980] | 0,918 [0,824; 0,983] | 0,053 | 0,927 / 0,901 | 98,1% / 99,1% | 3,1% |
| grupo/incerto | 9 / 7 | 0,994 [0,988; 0,999] | 0,919 [0,788; 0,997] | 0,919 [0,788; 0,997] | 0,075 | 0,904 / 0,871 | 98,9% / 98,9% | 4,6% |
| grupo/silver | 18 / 3 | 0,960 [0,907; 1,000] | 0,910 [0,761; 1,000] | 0,917 [0,766; 1,000] | 0,043 | 0,939 / 0,916 | 97,7% / 99,2% | 2,3% |
| veiculo/official_diary_RJ_barra_do_pirai | 1 / 1 | 0,997 [0,997; 0,997] | 0,788 [0,788; 0,788] | 0,787 [0,787; 0,787] | 0,210 | 0,895 / 0,698 | 98,7% / 96,9% | 3,8% |
| veiculo/official_diary_ac | 2 / 1 | 0,982 [0,982; 0,982] | 0,985 [0,985; 0,985] | 0,985 [0,985; 0,985] | -0,003 | 0,750 / 0,778 | 97,3% / 97,6% | 5,6% |
| veiculo/official_diary_ap | 1 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 0,000 | 1,000 / 1,000 | 100,0% / 100,0% | 0,0% |
| veiculo/official_diary_ce | 6 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,000 | 0,991 / 0,991 | 99,7% / 99,7% | 0,0% |
| veiculo/official_diary_ma | 7 / 1 | 0,963 [0,963; 0,963] | 0,939 [0,939; 0,939] | 0,955 [0,955; 0,955] | 0,008 | 0,977 / 0,971 | 96,6% / 99,2% | 3,1% |
| veiculo/official_diary_mg | 1 / 1 | 0,990 [0,990; 0,990] | 0,516 [0,516; 0,516] | 0,516 [0,516; 0,516] | 0,474 | 0,942 / 0,796 | 99,5% / 98,9% | 2,4% |
| veiculo/official_diary_pi_v2 | 2 / 1 | 1,000 [1,000; 1,000] | 0,999 [0,999; 0,999] | 1,000 [1,000; 1,000] | -0,000 | 1,000 / 1,000 | 99,2% / 100,0% | 9,6% |
| veiculo/official_diary_rj | 5 / 1 | 0,907 [0,907; 0,907] | 0,761 [0,761; 0,761] | 0,766 [0,766; 0,766] | 0,141 | 0,824 / 0,749 | 96,8% / 98,5% | 4,1% |
| veiculo/official_diary_ro | 1 / 1 | 1,000 [1,000; 1,000] | 0,998 [0,998; 0,998] | 1,000 [1,000; 1,000] | 0,000 | 0,978 / 0,978 | 99,4% / 99,4% | 0,0% |
| veiculo/official_diary_se | 1 / 1 | 0,996 [0,996; 0,996] | 1,000 [1,000; 1,000] | 0,996 [0,996; 0,996] | 0,000 | 0,825 / 0,813 | 99,3% / 99,3% | 5,3% |
### A — humanas repetidas

| Estrato | n / veículos | τ palavras fixo | τ XY-cut | τ XY-cut+margens | Δ justo palavras | τ regiões fixo / XY-cut+margens | Sucessor palavras fixo / justa | Fragmentação fixo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| colunas/1 coluna detectada | 12 / 11 | 0,991 [0,979; 1,000] | 0,920 [0,746; 1,000] | 0,995 [0,989; 1,000] | -0,004 | 0,906 / 0,949 | 98,0% / 98,5% | 7,5% |
| colunas/multicoluna detectada | 8 / 8 | 0,971 [0,948; 0,991] | 0,733 [0,597; 0,866] | 0,882 [0,745; 0,974] | 0,089 | 0,951 / 0,870 | 99,2% / 99,2% | 6,9% |
| familiaridade/veículo já visto no v4 | 20 / 19 | 0,983 [0,971; 0,994] | 0,845 [0,722; 0,944] | 0,950 [0,885; 0,989] | 0,033 | 0,924 / 0,918 | 98,5% / 98,8% | 7,3% |
| grupo/incerto | 17 / 16 | 0,980 [0,967; 0,993] | 0,851 [0,718; 0,954] | 0,974 [0,950; 0,992] | 0,007 | 0,912 / 0,926 | 98,3% / 98,7% | 7,9% |
| grupo/silver | 3 / 3 | 0,998 [0,995; 1,000] | 0,813 [0,445; 1,000] | 0,815 [0,445; 1,000] | 0,184 | 0,992 / 0,870 | 99,5% / 99,2% | 3,7% |
| veiculo/official_diary_MG_congonhas | 1 / 1 | 0,999 [0,999; 0,999] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,001 | 0,985 / 0,985 | 99,3% / 99,7% | 0,0% |
| veiculo/official_diary_RJ_barra_do_pirai | 2 / 1 | 0,955 [0,955; 0,955] | 1,000 [1,000; 1,000] | 0,978 [0,978; 0,978] | -0,023 | 0,733 / 0,867 | 91,7% / 95,0% | 33,3% |
| veiculo/official_diary_RJ_duque_de_caxias | 1 / 1 | 0,917 [0,917; 0,917] | 0,836 [0,836; 0,836] | 0,862 [0,862; 0,862] | 0,055 | 0,937 / 0,789 | 98,9% / 98,0% | 0,0% |
| veiculo/official_diary_RJ_seropedica | 1 / 1 | 0,987 [0,987; 0,987] | 0,966 [0,966; 0,966] | 0,984 [0,984; 0,984] | 0,003 | 0,951 / 0,909 | 98,7% / 99,4% | 7,1% |
| veiculo/official_diary_ac | 1 / 1 | 0,926 [0,926; 0,926] | 0,621 [0,621; 0,621] | 0,911 [0,911; 0,911] | 0,015 | 0,897 / 0,897 | 99,2% / 99,6% | 17,4% |
| veiculo/official_diary_al | 1 / 1 | 0,998 [0,998; 0,998] | 0,081 [0,081; 0,081] | 0,998 [0,998; 0,998] | -0,000 | 0,977 / 0,977 | 98,6% / 99,6% | 0,0% |
| veiculo/official_diary_ap | 1 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 0,000 | 1,000 / 1,000 | 100,0% / 100,0% | 0,0% |
| veiculo/official_diary_ce | 1 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,000 | 1,000 / 1,000 | 99,8% / 100,0% | 0,0% |
| veiculo/official_diary_ma | 1 / 1 | 1,000 [1,000; 1,000] | 0,994 [0,994; 0,994] | 1,000 [1,000; 1,000] | 0,000 | 1,000 / 1,000 | 100,0% / 100,0% | 0,0% |
| veiculo/official_diary_mg | 1 / 1 | 0,994 [0,994; 0,994] | 0,875 [0,875; 0,875] | 0,875 [0,875; 0,875] | 0,119 | 0,961 / 0,852 | 99,7% / 99,3% | 4,0% |
| veiculo/official_diary_ms | 1 / 1 | 0,999 [0,999; 0,999] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,001 | 0,600 / 1,000 | 99,5% / 100,0% | 0,0% |
| veiculo/official_diary_pb | 1 / 1 | 0,964 [0,964; 0,964] | 0,511 [0,511; 0,511] | 0,981 [0,981; 0,981] | -0,017 | 0,941 / 0,905 | 98,8% / 99,5% | 12,5% |
| veiculo/official_diary_pi_v2 | 1 / 1 | 1,000 [1,000; 1,000] | 0,999 [0,999; 0,999] | 1,000 [1,000; 1,000] | 0,000 | 1,000 / 0,989 | 98,6% / 99,2% | 10,0% |
| veiculo/official_diary_rj | 1 / 1 | 0,995 [0,995; 0,995] | 0,445 [0,445; 0,445] | 0,445 [0,445; 0,445] | 0,551 | 0,976 / 0,610 | 98,6% / 97,6% | 11,0% |
| veiculo/official_diary_rj_japeri | 1 / 1 | 1,000 [1,000; 1,000] | 0,994 [0,994; 0,994] | 0,994 [0,994; 0,994] | 0,006 | 1,000 / 0,905 | 100,0% / 96,0% | 0,0% |
| veiculo/official_diary_ro | 1 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 0,000 | 1,000 / 0,956 | 100,0% / 99,5% | 0,0% |
| veiculo/official_diary_rs_porto_alegre | 1 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,000 | 1,000 / 1,000 | 99,2% / 100,0% | 5,0% |
| veiculo/official_diary_se | 1 / 1 | 0,984 [0,984; 0,984] | 0,967 [0,967; 0,967] | 0,989 [0,989; 0,989] | -0,005 | 0,847 / 0,843 | 97,8% / 98,5% | 8,8% |
| veiculo/official_diary_to | 1 / 1 | 0,986 [0,986; 0,986] | 0,620 [0,620; 0,620] | 1,000 [1,000; 1,000] | -0,014 | 0,941 / 1,000 | 99,4% / 100,0% | 3,4% |
### B — silver novas

| Estrato | n / veículos | τ palavras fixo | τ XY-cut | τ XY-cut+margens | Δ justo palavras | τ regiões fixo / XY-cut+margens | Sucessor palavras fixo / justa | Fragmentação fixo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| colunas/1 coluna detectada | 41 / 3 | 0,986 [0,886; 1,000] | 0,986 [0,887; 1,000] | 0,986 [0,887; 1,000] | -0,000 | 0,946 / 0,943 | 99,0% / 99,3% | 0,5% |
| colunas/multicoluna detectada | 45 / 3 | 0,952 [0,916; 1,000] | 0,901 [0,833; 1,000] | 0,913 [0,845; 1,000] | 0,039 | 0,910 / 0,934 | 98,5% / 99,4% | 4,7% |
| familiaridade/veículo já visto no v4 | 86 / 3 | 0,968 [0,930; 1,000] | 0,942 [0,861; 1,000] | 0,948 [0,871; 1,000] | 0,020 | 0,927 / 0,938 | 98,8% / 99,3% | 2,7% |
| veiculo/official_diary_ce | 37 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,000 | 0,989 / 0,988 | 99,6% / 99,7% | 0,0% |
| veiculo/official_diary_ma | 37 / 1 | 0,948 [0,948; 0,948] | 0,910 [0,910; 0,910] | 0,920 [0,920; 0,920] | 0,028 | 0,899 / 0,935 | 98,1% / 99,0% | 4,8% |
| veiculo/official_diary_rj | 12 / 1 | 0,930 [0,930; 0,930] | 0,861 [0,861; 0,861] | 0,871 [0,871; 0,871] | 0,059 | 0,824 / 0,795 | 98,0% / 99,1% | 4,6% |
### B — silver completo

| Estrato | n / veículos | τ palavras fixo | τ XY-cut | τ XY-cut+margens | Δ justo palavras | τ regiões fixo / XY-cut+margens | Sucessor palavras fixo / justa | Fragmentação fixo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| colunas/1 coluna detectada | 42 / 3 | 0,986 [0,886; 1,000] | 0,986 [0,887; 1,000] | 0,987 [0,887; 1,000] | -0,000 | 0,947 / 0,945 | 99,0% / 99,3% | 0,5% |
| colunas/multicoluna detectada | 47 / 3 | 0,946 [0,893; 1,000] | 0,886 [0,767; 1,000] | 0,897 [0,778; 1,000] | 0,049 | 0,899 / 0,914 | 98,6% / 99,3% | 4,7% |
| familiaridade/veículo já visto no v4 | 89 / 3 | 0,965 [0,909; 1,000] | 0,934 [0,803; 1,000] | 0,939 [0,812; 1,000] | 0,026 | 0,922 / 0,928 | 98,8% / 99,3% | 2,7% |
| veiculo/official_diary_ce | 38 / 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | -0,000 | 0,989 / 0,988 | 99,6% / 99,7% | 0,0% |
| veiculo/official_diary_ma | 38 / 1 | 0,950 [0,950; 0,950] | 0,912 [0,912; 0,912] | 0,922 [0,922; 0,922] | 0,027 | 0,902 / 0,937 | 98,2% / 99,0% | 4,7% |
| veiculo/official_diary_rj | 13 / 1 | 0,909 [0,909; 0,909] | 0,803 [0,803; 0,803] | 0,812 [0,812; 0,812] | 0,097 | 0,784 / 0,730 | 98,0% / 99,0% | 5,1% |

## Análise das oito maiores perdas em páginas novas

Ranking por Δ τ **da sequência real de palavras** contra XY-cut pura. Considera A/B novas; uma página compartilhada aparece uma vez, priorizando a referência humana. Abaixo há também Δ contra a XY-cut justa e τ de regiões para expor desacordo entre réguas. Motivos são diagnósticos de geometria/inspeção, não rótulos causais anotados; não houve mudança de configuração após inspeção.

| Página / fonte | τ palavras XY-cut → método | Δ pura / justa | τ regiões XY-cut → método | Fragmentação | Motivo e relação com golden_v4 |
|---|---:|---:|---:|---:|---|
| `official_diary_ma/executive_official_diary_2021-11-19.pdf#p55` (B) | 0,46517 → 0,44434 | -0,02083 / -0,02151 | 0,402 → 0,411 | 9,7% | Expediente e quadro de preços: calha local do quadro não detectada; rótulos de lista ficam num bloco vertical separado das descrições, e um bloco v3 une células das duas colunas. A saída intercala esses blocos, mas o silver também põe seções visualmente fora de ordem: a perda não demonstra erro humano. Tabelas lado a lado/calha ausente já apareciam em Manaus/Caxias no v4; referência v3 que fatora a lista e mistura colunas é limitação nova desta validação. |
| `official_diary_ac/executive_official_diary_2022-12-02.pdf#p419` (A) | 0,97003 → 0,96488 | -0,00515 / -0,00515 | 0,556 → 0,500 | 11,1% | Cabeçalho/área acima da tabela: topo exato inverte campos laterais; linhas do título do relatório são interrompidas pelo campo de página/data à direita. A tabela permanece atômica. Desempate de campos do cabeçalho já aparecia em AC/MS no v4; esta instância de campo lateral no corpo é nova. |
| `official_diary_se/DOE-SE_2022-03-18_4475.pdf#p15` (A) | 0,99974 → 0,99564 | -0,00410 / 0,00006 | 0,918 → 0,825 | 5,3% | Marcas de diagramação textFrameStart/SEGRASE mudam para antes do rodapé, embora a ordem humana v3 as tenha mantido entre blocos de conteúdo. Campo de número/página também se fragmenta. As tabelas empilhadas ficam preservadas. Margens/campos fragmentados eram conhecidos no v4; avaliar marcas como blocos ordenáveis nesta referência v3 é uma nova incompatibilidade de representação. |
| `official_diary_ma/executive_official_diary_2026-01-14.pdf#p46` (B) | 0,99673 → 0,99618 | -0,00055 / -0,00091 | 0,980 → 0,980 | 4,0% | Cabeçalho e data/assinatura: o número da página vira átomo picture separado da data, fragmentando o bloco v3; a ordem silver data→assinatura diverge da posição visual assinatura→data. A tabela central não se intercala. Campos de cabeçalho e imagens que capturam texto já ocorriam no v4; discrepância semântica do silver limita a atribuição causal. |
| `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p34` (B) | 1,00000 → 0,99970 | -0,00029 / 0,00000 | 0,867 → 0,333 | 0,0% | Cabeçalho sobre tabela longa: campos muito curtos com top diferentes são permutados; DIÁRIO OFICIAL é átomo picture. Corpo da tabela preservado e nenhuma região fragmentada. Mesmo motivo geométrico de cabeçalho/átomos do v4; perda pequena em palavras e grande sensibilidade regional por haver poucos blocos. |
| `official_diary_ma/executive_official_diary_2021-09-20.pdf#p26` (B) | 0,99852 → 0,99831 | -0,00021 / -0,00169 | 0,333 → 0,333 | 33,3% | Cabeçalho: campo de data/número se reparte porque o número é picture; a margem ordena fragmentos por top e troca o campo esquerdo com o direito. Corpo é uma tabela única preservada. Calhas detectadas aqui são células da tabela, não duas colunas de leitura: viés do estratificador. Campos e dependência da delimitação de átomos são conhecidos no v4. |
| `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223` (A) | 1,00000 → 0,99983 | -0,00017 / -0,00017 | 1,000 → 1,000 | 12,5% | Rodapé: contPageBreak pertence ao mesmo bloco v3 que edição/data, mas a regra de marcas o emite separadamente antes do rodapé, quebrando a contiguidade. A mediana conserva a ordem perfeita dos blocos e esconde a interrupção. Campos de rodapé intercalados eram conhecidos em Barra do Piraí/v4; o marcador incorporado ao bloco v3 é uma incompatibilidade nova. |
| `official_diary_ma/executive_official_diary_2021-09-29.pdf#p54` (B) | 0,99915 → 0,99900 | -0,00016 / -0,00100 | 0,333 → 0,333 | 33,3% | Cabeçalho: o átomo picture do número da página separa data/número; diferenças de top invertem os campos superiores. Tabela única permanece atômica. Calhas internas correspondem a células, não a colunas independentes de texto. Repete o erro conhecido de cabeçalho no v4, com falso multicoluna produzido pelo estratificador. |

Os oito casos foram inspecionados nas figuras intermediárias e nas sequências/caixas do cache. Cabeçalho/rodapé, desempate por topo e dependência da delimitação dos átomos já constavam das inspeções do v4 (AC/MS, Barra do Piraí e Caxias); tabelas lado a lado e calha ausente também (Manaus/PB/Caxias). As novidades são da **régua v3/silver**: bloco que mistura células de colunas distintas, marcadores isolados/incorporados a blocos humanos, lista fatorada em rótulos e texto e fluxo silver visualmente incoerente. Não há evidência para atribuir estas oito perdas a título atravessando colunas; esse motivo foi uma hipótese de desenvolvimento (ponte/ARTIGOS no MA) e não deve ser inventado aqui. Também não confundir calhas entre células com colunas de jornal. Os casos não justificam reajustar o método após o teste.

## Limitações e recomendação para o TCC

Amostra humana pequena e de conveniência, um anotador, poucos exemplos por veículo e possível parentesco tipográfico. Páginas novas do mesmo veículo não equivalem a teste de domínio novo. A referência silver é selecionada por concordância com XY-cut. A interseção A/B e a repetição de B no golden_v4 impedem tratar o total como uma validação independente única.

A ordem humana cega evita ancoragem numa sugestão de **ordem**. Corrigir uma pré-anotação de **caixas/segmentação**, como no Diamond/v4, traz viés de ancoragem geométrica; isso continua pertinente ao resultado de desenvolvimento, mas não deve ser atribuído sem prova à ordem cega usada aqui. Em A, a segmentação v3 define a unidade que o humano ordenou. Projeção sem conflito conserva a ordem anotada, mas pode mudar o peso/unidade dos itens.

A expansão dentro de cada bloco é algorítmica, não ouro humano de palavras ou células. Blocos v3 que misturam colunas podem impor uma referência interna intercalada: melhora/piora de palavras nesses blocos não decide a leitura humana correta. A régua de regiões também herda esse defeito de segmentação. Tabelas são achatadas por y/x; não avaliamos estrutura semântica de células, OCR ou imagens sem texto. Palavras fora dos blocos e regiões vazias não têm referência textual avaliável.

As baselines preservam blocos inteiros e compartilham a expansão interna da referência, o que favorece seus pares internos; o método precisa reconstruir essa granularidade sem vê-la. τ de palavras pondera pares de palavras (peso maior para blocos longos dentro da página), enquanto τ de regiões pondera pares de blocos. Fragmentação e sucessores de trechos tornam essa diferença visível. Os números das duas réguas não são intercambiáveis.

Não demonstramos superioridade geral, equivalência ou vantagem ponta a ponta de latência. Recomenda-se apresentar a configuração congelada como diagnóstico de generalização por página, com comparação de margens iguais, estratos e falhas; não adotar no protocolo sem decisão do autor. Para sustentar substituição, obter ordem humana em páginas/veículos realmente inéditos e uma referência de leitura interna dos blocos problemáticos, mantendo a saída real e continuidade como critérios.

## Reprodução, retomada e integridade

```powershell
venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_acervo.py --do-zero
venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_acervo.py --conferir
```

Caches: `resultados/ordem_sem_bbox_cache/palavras/` (PDF/hash/página), `avaliacao_acervo/` (métricas e sequências por referência/hash), `validacao_acervo.json` (todos os números, hashes, testes e estratos), `inspecao_acervo/` (figuras intermediárias de erro). A execução padrão retoma hashes compatíveis; `--do-zero` reabre PDFs e recalcula tudo. O relatório é escrito após o primeiro lote com números e atualizado durante a execução. Não há leitura do Label Studio, rede, GPU, edição de dados, commit ou alteração do método anterior.

Controles sintéticos executados: 7; resultados: página vazia tratada; vazia sem nota perfeita; região vazia tratada; intercalação contada; mediana perfeita com palavras erradas; Pratt zeros; bootstrap por veículo.

`--conferir` compara o Markdown inteiro com sua renderização a partir do JSON e verifica todos os hashes de entrada/fontes/PDFs. A execução normal confere hashes antes/depois. Os hashes completos e as ordens previstas estão no JSON do cache; figuras de erro têm caixas v3 azuis, átomos Docling vermelhos e calhas verdes.

**Conferência final:** a execução do zero reproduziu as métricas, sequências, estratos e testes da execução anterior; relatório conferido por igualdade integral com a renderização do JSON.
