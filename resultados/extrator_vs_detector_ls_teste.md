# Extrator × detectores — teste de layout do Label Studio

## Resumo de cinco linhas

1. **Veredito:** ls3 tem o maior F1 de 3 classes a IoU 0,50 no teste observado; a escolha do melhor detector é exploratória.
2. Universo: 317 páginas de 42 chaves nominais de fonte no teste; 1 página(s) com alias confirmado de fonte do treino/validação; 5485 caixas de ouro (5482 em 3 classes).
3. Cobertura: extrator: 317/317; ls3: 317/317; ls16: 317/317. Detectores fora: nenhum.
4. PDFs sem texto: 11, entre 317 páginas inspecionadas; 6 páginas em envelopes PKCS#7; índice verificado antes da extração.
5. Uso interno do parceiro Data Policy. Ouro corrigido de pré-anotação tem viés de ancoragem; separação nominal de fontes não elimina esse viés nem resolve aliases.

Gerado pelo script em 2026-10-03T05:32:30-03:00. Execução completa do extrator.

## Tabela principal

F1 micro por caixa; IC 95% por bootstrap de páginas entre colchetes. Régua comum principal: 3 classes, IoU ≥ 0,50. Nenhum limiar foi escolhido no teste.

| Sistema | Páginas | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 9 classes 0,50 | 16 classes 0,50 | ms/página (média) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| extrator | 317 | 0,573 [0,530; 0,614] | 0,399 [0,366; 0,433] | 0,555 [0,513; 0,595] | 0,387 [0,354; 0,420] | 0,480 [0,440; 0,519] | — | 4486,8 |
| ls3 | 317 | 0,780 [0,743; 0,816] | 0,731 [0,694; 0,766] | 0,769 [0,732; 0,804] | 0,722 [0,685; 0,757] | — | — | 711,2 |
| ls16 | 317 | 0,753 [0,720; 0,783] | 0,705 [0,673; 0,735] | 0,743 [0,709; 0,774] | 0,697 [0,664; 0,727] | 0,668 [0,635; 0,697] | 0,622 [0,591; 0,652] | 277,7 |

| Detector | `treino_ok` | Checkpoint | Situação nesta execução |
|---|---|---|---|
| ls3 | existe | existe | concluído; incluído |
| ls16 | existe | existe | concluído; incluído |

**Auditoria do split: a premissa de fontes inteiramente inéditas tem uma exceção confirmada.** A tabela principal preserva todas as páginas e rótulos pedidos; não alteramos o arquivo de split.
- Alias pag df no teste ↔ df no treino/validação: 1 página(s) de teste; identidade confirmada por cabeçalhos.
  Evidência pag df: `lote_20260715_100540/2026-05-05-EXTRA-Pag-07-DF/2026-05-05-EXTRA-Pag-07-DF.pdf#p3`; cabeçalho “Diário Oficial do Distrito Federal - Edição Extra”.
  Evidência df: `0049_2026-05-05-NORMAL-Pag94-DF_p0086/0049_2026-05-05-NORMAL-Pag94-DF_p0086.pdf#p1`; cabeçalho “Diário Oficial do Distrito Federal”.

Sensibilidade exploratória excluindo somente páginas dos aliases confirmados; não substitui o resultado principal nem redefine o conjunto oficial:

| Sistema | Páginas sem alias confirmado | F1 3 classes 0,50 (IC 95%) |
|---|---:|---:|
| extrator | 316 | 0,556 [0,516; 0,596] |
| ls3 | 316 | 0,769 [0,732; 0,804] |
| ls16 | 316 | 0,743 [0,712; 0,773] |

## Protocolo e conferência do ouro

A referência é exatamente o teste exportado para YOLO; todas as classes e coordenadas foram conferidas contra `conv_seed1..4/tarefas.jsonl`. Caixas são limitadas à imagem; o filtro existente de largura/altura menor que 1 pixel é reproduzido. O script associa cada caixa por ID à anotação não cancelada que reproduz geometria, classe e transcrição convertidas. Em empate com origens diferentes usa `ambigua`, sem escolher um anotador arbitrariamente.
Há 30 páginas com múltiplas anotações candidatas; 1 com anotações equivalentes. Rotações de caixas no ouro: 3. Origem de rótulo e retângulo diferentes: 1 caixas. Filtro <1px: 0; classes fora do guia: 1.
O índice informado pelo LS é comparado nas alternativas zero/um com as transcrições (cobertura de tokens normalizados) e com o raster da imagem. Em páginas quase idênticas, tokens exclusivos da candidata presentes no ouro, ausentes na alternativa, e raster mais parecido confirmam o índice. Índices ainda ambíguos ou PDFs sem correspondência são registrados como falha, sem avaliar outra página. A verificação textual usa o ouro somente para identificar a página; essas transcrições não entram no extrator nem nos modelos.
Base inferida entre as páginas concluídas: {'1': 317}; 296 confirmadas com cobertura textual ≥ 0,20. As restantes dependem da correspondência visual. Falhas técnicas de PDF/índice: 0.
O extrator reproduz palavras_da_pagina → segmentar(com tabelas Docling) → palavras/blocos_v3/detector → propor(regras=True, fundir=True). O Docling Heron usa a revisão fixada em layout.py, CPU, DPI do módulo, limiar de cache 0,30 e de proposta 0,45. Portanto esta linha de base contém um detector visual pré-treinado, além das regras. A transformação pontos→pixels respeita a origem do recorte do raster; não supõe página em (0,0).
As 9 classes são a régua histórica do extrator, colapsada por GUIA_PARA_EXTRATOR: lista do extrator vira paragraph→texto. O mapa do guia ocupa 8 classes distintas, pois o guia não tem lista. As 3 classes: table→tabela; figure/chart/heading→imagem; unknown excluído; demais→texto. O mapa assinatura→signature perde a distinção de rubrica manuscrita: limitação real, sem usar o ouro para resolver. Localização sem classe inclui unknown também para ls3, que não foi treinado para detectá-lo. Na régua 3 classes removemos caixas unknown de ouro e predições; não ignoramos outra predição só por tocar um unknown.
Emparelhamento bipartido um a um, maximizando primeiro o número de pares válidos e depois IoU; classe precisa coincidir na régua correspondente. TP, FP e FN são somados antes de calcular F1=2TP/(2TP+FP+FN). Página sem ouro e sem predição tem F1 por página definido como zero (sem contribuição ao micro). Não medimos mAP nem ordem de leitura nesta tarefa.
Bootstrap: 2000 reamostras de páginas com reposição, semente 20261003. O IC não incorpora dependência entre páginas da mesma fonte; pode ser estreito demais. Por fonte, n pequeno (ou uma única página) torna o IC instável ou degenerado.

| Sistema / régua | TP | FP | FN | F1 micro | F1 macro por página |
|---|---:|---:|---:|---:|---:|
| extrator / loc50 | 3251 | 2614 | 2234 | 0,573 | 0,600 |
| extrator / loc75 | 2263 | 3602 | 3222 | 0,399 | 0,425 |
| extrator / c3_50 | 3146 | 2717 | 2336 | 0,555 | 0,575 |
| extrator / c3_75 | 2196 | 3667 | 3286 | 0,387 | 0,407 |
| extrator / c9_50 | 2725 | 3140 | 2760 | 0,480 | 0,495 |
| extrator / c9_75 | 1955 | 3910 | 3530 | 0,344 | 0,359 |
| ls3 / loc50 | 4838 | 2080 | 647 | 0,780 | 0,808 |
| ls3 / loc75 | 4531 | 2387 | 954 | 0,731 | 0,759 |
| ls3 / c3_50 | 4767 | 2151 | 715 | 0,769 | 0,796 |
| ls3 / c3_75 | 4474 | 2444 | 1008 | 0,722 | 0,749 |
| ls16 / loc50 | 4630 | 2182 | 855 | 0,753 | 0,773 |
| ls16 / loc75 | 4337 | 2475 | 1148 | 0,705 | 0,724 |
| ls16 / c3_50 | 4567 | 2244 | 915 | 0,743 | 0,763 |
| ls16 / c3_75 | 4285 | 2526 | 1197 | 0,697 | 0,715 |
| ls16 / c9_50 | 4105 | 2707 | 1380 | 0,668 | 0,675 |
| ls16 / c9_75 | 3867 | 2945 | 1618 | 0,629 | 0,638 |
| ls16 / c16_50 | 3823 | 2989 | 1662 | 0,622 | 0,637 |
| ls16 / c16_75 | 3602 | 3210 | 1883 | 0,586 | 0,602 |

## Páginas com e sem camada de texto

Sem texto = nenhuma palavra alfanumérica extraída; isso sugere digitalização, mas não prova ausência de texto visual. Página digitalizada com OCR embutido ou só cabeçalho textual e corpo digitalizado pertence ao grupo com texto. Texto escasso (<5 palavras) é também mostrado como subconjunto de com texto; não é somado de novo ao total.

| Sistema | Estrato | Páginas | Localização 0,50 | Localização 0,75 | 3 classes 0,50 |
|---|---|---:|---:|---:|---:|
| extrator | com_texto | 306 | 0,576 | 0,401 | 0,558 |
| extrator | sem_texto | 11 | 0,194 | 0,194 | 0,194 |
| extrator | texto_escasso | 0 | — | — | — |
| ls3 | com_texto | 306 | 0,778 | 0,729 | 0,767 |
| ls3 | sem_texto | 11 | 0,892 | 0,851 | 0,892 |
| ls3 | texto_escasso | 0 | — | — | — |
| ls16 | com_texto | 306 | 0,753 | 0,705 | 0,743 |
| ls16 | sem_texto | 11 | 0,753 | 0,726 | 0,753 |
| ls16 | texto_escasso | 0 | — | — | — |

O extrator pode preservar figuras detectadas visualmente sem texto, mas descarta outras regiões sem palavras; a separação é necessária para não esconder essa dependência. O detector lê a imagem e independe da camada textual.

## Ancoragem

Origem principal = campo origin do item labels; fallback para rectangle quando labels não tem origem. A revocação usa o emparelhamento global e só depois agrupa as caixas do ouro; uma predição não pode acertar mais de uma caixa por origem.

| Sistema | Origem | Caixas (todas) | TP localização 0,50 | Revocação localização | Caixas (3 classes) | TP com classe | Revocação 3 classes |
|---|---|---:|---:|---:|---:|---:|---:|
| extrator | manual | 996 | 479 | 0,481 | 995 | 454 | 0,456 |
| extrator | prediction | 2048 | 1154 | 0,563 | 2048 | 1135 | 0,554 |
| extrator | prediction-changed | 2440 | 1618 | 0,663 | 2438 | 1557 | 0,639 |
| extrator | ausente | 0 | 0 | — | 0 | 0 | — |
| extrator | ambigua | 1 | 0 | 0,000 | 1 | 0 | 0,000 |
| ls3 | manual | 996 | 777 | 0,780 | 995 | 763 | 0,767 |
| ls3 | prediction | 2048 | 1874 | 0,915 | 2048 | 1868 | 0,912 |
| ls3 | prediction-changed | 2440 | 2186 | 0,896 | 2438 | 2135 | 0,876 |
| ls3 | ausente | 0 | 0 | — | 0 | 0 | — |
| ls3 | ambigua | 1 | 1 | 1,000 | 1 | 1 | 1,000 |
| ls16 | manual | 996 | 711 | 0,714 | 995 | 692 | 0,695 |
| ls16 | prediction | 2048 | 1830 | 0,894 | 2048 | 1827 | 0,892 |
| ls16 | prediction-changed | 2440 | 2088 | 0,856 | 2438 | 2047 | 0,840 |
| ls16 | ausente | 0 | 0 | — | 0 | 0 | — |
| ls16 | ambigua | 1 | 1 | 1,000 | 1 | 1 | 1,000 |

extrator: revocação de localização em caixas mantidas−manuais = 0,083; alteradas−manuais = 0,182. São diferenças brutas, sem ajuste por dificuldade, fonte ou classe.

ls3: revocação de localização em caixas mantidas−manuais = 0,135; alteradas−manuais = 0,116. São diferenças brutas, sem ajuste por dificuldade, fonte ou classe.

ls16: revocação de localização em caixas mantidas−manuais = 0,180; alteradas−manuais = 0,142. São diferenças brutas, sem ajuste por dificuldade, fonte ou classe.

Diferenças de revocação por origem são compatíveis com herança de ancoragem, mas não a demonstram: as caixas manuais podem ser menores, mais difíceis, de classes/fontes distintas; prediction-changed pode significar só troca de classe ou texto. Sem teste desenhado do zero e sem controlar dificuldade/classe/fonte não é possível atribuir a diferença causalmente ao pré-anotador.

Mesmo manual é uma caixa adicionada enquanto a pré-anotação estava visível; não equivale a uma página anotada às cegas do zero. A origem é metadado do LS e não reconstrói todas as edições. Fontes inéditas evitam vazamento de layout do treino, mas preservam a mesma maneira de construir o ouro.

## Por fonte e teste pareado

Régua: F1 micro de 3 classes a IoU 0,50, IC por bootstrap das páginas da própria fonte. Uma fonte com uma página tem IC degenerado; a marca † sinaliza n<5. 'Sem comparação' significa que não há detector pronto em todas as páginas da fonte.

| Fonte | Páginas | extrator | ls3 | ls16 | Maior F1 observado |
|---|---:|---:|---:|---:|---|
| aracaju | 18 | 0,395 [0,355; 0,436] | 0,885 [0,838; 0,922] | 0,859 [0,808; 0,906] | ls3 |
| bahia † | 1 | 0,695 [0,695; 0,695] | 0,876 [0,876; 0,876] | 0,889 [0,889; 0,889] | ls16 |
| belo horizonte | 13 | 0,561 [0,376; 0,722] | 0,874 [0,784; 0,944] | 0,793 [0,707; 0,864] | ls3 |
| cafezal sul † | 1 | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] | extrator/ls3/ls16 |
| campos dos goytacazes † | 4 | 0,736 [0,514; 0,877] | 0,811 [0,637; 0,907] | 0,787 [0,649; 0,884] | ls3 |
| capela † | 2 | 0,730 [0,636; 0,780] | 0,938 [0,889; 0,973] | 0,938 [0,889; 0,973] | ls3/ls16 |
| corbelia | 13 | 0,596 [0,535; 0,670] | 0,724 [0,677; 0,768] | 0,684 [0,615; 0,751] | ls3 |
| cotegipe | 5 | 0,621 [0,483; 0,709] | 0,903 [0,733; 0,990] | 0,857 [0,721; 0,936] | ls3 |
| deodapolis | 5 | 0,520 [0,375; 0,781] | 0,874 [0,818; 0,934] | 0,854 [0,812; 0,897] | ls3 |
| doe pa | 16 | 0,602 [0,468; 0,736] | 0,799 [0,731; 0,962] | 0,743 [0,664; 0,904] | ls3 |
| dois irmaos † | 2 | 0,286 [0,074; 0,444] | 0,909 [0,783; 0,963] | 0,814 [0,806; 0,833] | ls3 |
| floreal † | 1 | 0,400 [0,400; 0,400] | 0,880 [0,880; 0,880] | 0,745 [0,745; 0,745] | ls3 |
| frei paulo † | 1 | 0,582 [0,582; 0,582] | 0,720 [0,720; 0,720] | 0,709 [0,709; 0,709] | ls3 |
| iepe † | 2 | 0,548 [0,421; 0,750] | 0,860 [0,846; 0,867] | 0,795 [0,787; 0,815] | ls3 |
| ipiranga † | 3 | 0,587 [0,457; 0,750] | 0,882 [0,788; 0,947] | 0,879 [0,839; 0,947] | ls3 |
| itamaraju † | 2 | 0,638 [0,333; 0,683] | 0,909 [0,857; 0,919] | 0,894 [0,667; 0,947] | ls3 |
| ituacu | 12 | 0,416 [0,281; 0,559] | 0,885 [0,827; 0,935] | 0,890 [0,844; 0,929] | ls16 |
| ji parana | 9 | 0,621 [0,507; 0,752] | 0,777 [0,689; 0,848] | 0,748 [0,659; 0,812] | ls3 |
| jundiai | 8 | 0,737 [0,660; 0,804] | 0,743 [0,648; 0,815] | 0,620 [0,556; 0,675] | ls3 |
| mg | 6 | 0,663 [0,566; 0,866] | 0,814 [0,744; 0,972] | 0,744 [0,679; 0,874] | ls3 |
| monte alto † | 2 | 0,667 [0,649; 0,696] | 0,862 [0,829; 0,917] | 0,794 [0,757; 0,846] | ls3 |
| morro chapeu † | 2 | 0,381 [0,345; 0,462] | 0,766 [0,710; 0,875] | 0,679 [0,647; 0,737] | ls3 |
| natal | 20 | 0,719 [0,620; 0,804] | 0,813 [0,771; 0,845] | 0,796 [0,768; 0,823] | ls3 |
| nossa senhora das dores † | 2 | 0,625 [0,625; 0,625] | 0,944 [0,889; 1,000] | 0,919 [0,842; 1,000] | ls3 |
| nova iguacu | 18 | 0,801 [0,630; 0,884] | 0,909 [0,808; 0,963] | 0,825 [0,714; 0,889] | ls3 |
| ourinhos | 30 | 0,610 [0,504; 0,702] | 0,826 [0,768; 0,879] | 0,747 [0,694; 0,798] | ls3 |
| ouro verde oeste | 6 | 0,525 [0,300; 0,682] | 0,818 [0,776; 0,878] | 0,750 [0,667; 0,846] | ls3 |
| pa | 18 | 0,698 [0,614; 0,765] | 0,847 [0,809; 0,908] | 0,837 [0,791; 0,906] | ls3 |
| pag df † | 1 | 0,235 [0,235; 0,235] | 0,795 [0,795; 0,795] | 0,700 [0,700; 0,700] | ls3 |
| pe † | 1 | 0,324 [0,324; 0,324] | 0,755 [0,755; 0,755] | 0,759 [0,759; 0,759] | ls16 |
| pinhais | 7 | 0,657 [0,446; 0,814] | 0,800 [0,662; 0,922] | 0,744 [0,592; 0,874] | ls3 |
| recife | 6 | 0,789 [0,760; 0,909] | 0,959 [0,865; 0,987] | 0,940 [0,908; 0,986] | ls3 |
| rio grande norte † | 2 | 0,982 [0,979; 1,000] | 0,947 [0,939; 1,000] | 0,900 [0,889; 0,902] | extrator |
| riodejaneiro legislativo † | 1 | 0,444 [0,444; 0,444] | 0,884 [0,884; 0,884] | 0,856 [0,856; 0,856] | ls3 |
| rn † | 3 | 0,573 [0,473; 0,758] | 0,578 [0,444; 0,848] | 0,670 [0,521; 0,896] | ls16 |
| rosario catete † | 2 | 0,484 [0,457; 0,519] | 0,872 [0,769; 0,945] | 0,817 [0,750; 0,868] | ls3 |
| santos | 36 | 0,374 [0,241; 0,528] | 0,584 [0,476; 0,689] | 0,606 [0,505; 0,693] | ls16 |
| sao domingos | 5 | 0,529 [0,434; 0,639] | 0,831 [0,768; 0,880] | 0,793 [0,729; 0,847] | ls3 |
| sao paulo empresarial jucesp † | 3 | 0,132 [0,104; 0,261] | 0,078 [0,062; 0,102] | 0,084 [0,061; 0,117] | extrator |
| sao paulo gestao despesas | 10 | 0,457 [0,288; 0,666] | 0,613 [0,507; 0,703] | 0,659 [0,618; 0,730] | ls16 |
| sapucaia | 13 | 0,547 [0,451; 0,663] | 0,787 [0,707; 0,861] | 0,811 [0,743; 0,861] | ls16 |
| tapirai | 5 | 0,353 [0,212; 0,595] | 0,757 [0,680; 0,831] | 0,667 [0,606; 0,720] | ls3 |

Vitórias por fonte (descritivas, sem teste múltiplo por fonte): {'ls3': 31, 'ls16': 7, 'extrator/ls3/ls16': 1, 'ls3/ls16': 1, 'extrator': 2}.
Melhor detector observado: ls3 (seleção pelo F1 micro 3 classes no próprio teste). Wilcoxon bilateral, pareado nos F1 por página: n=317, p=0,000000; diferença média detector−extrator=0,222 [0,194; 0,248]. Vitórias por página: detector 250, extrator 49, empates 18. O IC da diferença é bootstrap pareado. Selecionar o melhor no teste pode favorecer o detector; páginas da mesma fonte são correlacionadas. Não tratar p como confirmação independente da escolha.

## Tempo por página

CPU em todos os sistemas. Tempo de parede por página, sem carga/aquecimento do modelo e sem escrita de cache. Extrator inclui abertura/extração de palavras, renderização, Docling, segmentação e regras. YOLO inclui leitura da imagem, pré-processamento, inferência e pós-processamento. Verificação do índice com o ouro é preparação do experimento e fica fora. Sem excluir Docling, a comparação mede o custo real do extrator avaliado.

| Sistema | Páginas cronometradas | Média ms | Mediana ms | p95 ms | Soma s |
|---|---:|---:|---:|---:|---:|
| extrator | 317 | 4486,8 | 2313,0 | 16708,4 | 1422,3 |
| ls3 | 317 | 711,2 | 697,9 | 850,7 | 225,5 |
| ls16 | 317 | 277,7 | 270,2 | 330,0 | 88,0 |
Componentes médios do extrator (ms): palavras 2960,9; renderização 205,3; Docling 1287,4; segmentação/regras 33,1.
Tempos preservados do primeiro cálculo válido de cada etapa, não do acesso ao cache. Há concorrência com treino e outras tarefas na máquina; não é um benchmark em máquina ociosa. Retomadas misturam momentos de carga distintos e não incluem os custos de inicialização.

## Análise de erro e exemplos

Os indícios de divisão/fusão são geométricos: uma caixa toca pelo menos duas da outra segmentação com interseção ≥50% da área menor. Podem incluir sobreposições legítimas e não são uma nova métrica de acerto.

| Sistema | Ouro sem par IoU 0,50 | Predições sem par | Indícios de divisão | Indícios de fusão | Pares localizados com classe3 errada |
|---|---:|---:|---:|---:|---:|
| extrator | 2234 | 2614 | 623 | 395 | 118 |

extrator — classes mais perdidas: paragraph: 1086; header: 203; signature: 140; table: 139; caption: 137.
extrator — confusões em pares localizados (9 classes): titulo→texto: 107; cabecalho→texto: 72; texto→titulo: 65; assinatura→figura: 62; cabecalho→figura: 55.
| ls3 | 647 | 2080 | 954 | 397 | 95 |

ls3 — classes mais perdidas: paragraph: 254; caption: 62; header: 58; table: 56; signature: 45.
| ls16 | 855 | 2182 | 1248 | 441 | 87 |

ls16 — classes mais perdidas: paragraph: 296; header: 79; table: 76; caption: 75; figure: 51.
ls16 — confusões em pares localizados (9 classes): titulo→texto: 129; texto→titulo: 107; rodape→texto: 86; cabecalho→texto: 71; cabecalho→titulo: 45.

Exemplos selecionados automaticamente entre os menores F1 do extrator, em fontes distintas; são casos adversos e não uma amostra representativa.
- **santos**, `0408_SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213_p0096/0408_SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213_p0096.pdf#p1`: F1 3 classes=0,000; TP/FP/FN=[0, 134, 4]; palavras=1050. Caixa sem par com classe: `region_0003`, header, origem prediction-changed, trecho: “1º de abril de 2026 96 Diário Oficial de Santos”. Maior IoU desse ouro com uma predição: 0,149, classe predita header; geometria abaixo do limiar. 1 tabela(s) do ouro têm IoU ≥ 0,50 com predição classificada como figura. No pipeline, figura não recebe palavras; texto dessa área pode voltar como sobras de blocos e produzir fragmentação. [Sobreposição local](ls_teste_cache/exemplos/c88453d11d6d3d27a3d49125.jpg) (verde=ouro; vermelho=extrator).
- **nova iguacu**, `0445_RIO_DE_JANEIRO_ABRIL_2026+-+rj_nova_iguacu+-+2026-04-29-NORMAL-Ed0-Pag87_p0036/0445_RIO_DE_JANEIRO_ABRIL_2026+-+rj_nova_iguacu+-+2026-04-29-NORMAL-Ed0-Pag87_p0036.pdf#p1`: F1 3 classes=0,000; TP/FP/FN=[0, 0, 5]; palavras=0. Caixa sem par com classe: `region_0001`, table, origem prediction-changed, trecho: “”. O extrator não produziu caixa nessa página. Sem palavras, o pipeline só preserva regiões visuais de figura; as outras classes perdem suas caixas. [Sobreposição local](ls_teste_cache/exemplos/5a18510dbff828ca5bd41979.jpg) (verde=ouro; vermelho=extrator).
- **dois irmaos**, `lote_20260717_151620/RIO_GRANDE_SU_ABRIL_2026+-+rs_dois_irmaos+-+2026-04-29-NORMAL-Ed1314-Pag60/RIO_GRANDE_SU_ABRIL_2026+-+rs_dois_irmaos+-+2026-04-29-NORMAL-Ed1314-Pag60.pdf#p52`: F1 3 classes=0,074; TP/FP/FN=[1, 0, 25]; palavras=0. Caixa sem par com classe: `region_0001`, header, origem prediction-changed, trecho: “”. Maior IoU desse ouro com uma predição: 0,000, classe predita figure; geometria abaixo do limiar. Sem palavras, o pipeline só preserva regiões visuais de figura; as outras classes perdem suas caixas. [Sobreposição local](ls_teste_cache/exemplos/d04e89b87c440fb216daa41b.jpg) (verde=ouro; vermelho=extrator).

## Limitações e recomendação

O ouro não é uma adjudicação independente: representa a anotação escolhida pela conversão original, mesmo onde há vários anotadores. A taxonomia semântica do guia é mais fina que a do extrator; o colapso em 3/9 classes elimina distinções importantes. Retângulos rotacionados usam o mesmo envelope axis-aligned já exportado ao YOLO. F1 depende da granularidade das caixas e do limiar IoU. Não há OCR adicional; PDFs com OCR embutido, texto ilegível ou parcial exigem análise separada. A novidade de fontes foi conferida no split dos modelos LS; não auditamos os dados de pré-treino do Docling. Fontes com poucas páginas, ancoragem, dependência intrafonte e seleção do melhor detector limitam as inferências.
Recomendação medida: usar ls3 quando o objetivo é o maior F1 de layout em 3 classes nesse domínio. O outro sistema pode ser útil conforme custo/semântica; consultar os estratos e tempos antes de decidir. Para páginas sem camada de texto, priorizar um detector concluído com OCR posterior para obter texto; o presente teste de caixas não mede a qualidade desse OCR.
Para investigar ancoragem, usar futuramente páginas anotadas do zero, sem pré-anotação visível, por mais de um anotador e com adjudicação. Isso é uma recomendação de estudo, não altera o split ou as anotações atuais.

## Retomada e evidência

```powershell
venv/Scripts/python.exe orquestracao/analises/extrator_vs_detector_ls.py
venv/Scripts/python.exe orquestracao/analises/extrator_vs_detector_ls.py --so-relatorio
```

Cache interno: `resultados/ls_teste_cache/` (ouro, palavras, Docling, propostas, predições YOLO, PDFs temporários, exemplos e `metricas.json`). Todas as etapas têm assinatura de entrada/modelo/código e escrita atômica. A execução não grava em data/, não usa GPU, não baixa modelos, não altera o quadro e não faz commit. Os derivados do parceiro permanecem neste repositório e não devem ser publicados.
