# Extrator v4 — detector do domínio e palavras do PDF

1. **Veredito:** v4_cv melhora a localização sobre o extrator atual em 0,190 (19,0 pontos percentuais); perde para o ls3 puro por 0,017.
2. F1 de localização IoU ≥ 0,50: extrator 0,573; ls3 0,780; ls16 0,753; v4_cv 0,763.
3. Universo congelado: 317 páginas, 42 fontes nominais, 5485 caixas; 11 páginas sem camada digital.
4. Limiar padrão e ajuste por fonte são separados; estado desta execução: **completa (locais e RT-DETR L Kaggle)**.
5. Ouro corrigido de pré-anotação carrega ancoragem; a convenção do guia difere do Diamond do autor. Uso exclusivamente interno do parceiro Data Policy.

## Tabela principal

F1 micro por caixa. IC 95% por bootstrap de páginas entre colchetes. Os tempos reutilizam custos medidos nos caches de insumo e acrescentam o processamento v4 medido nesta execução.

| Sistema | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 16 classes 0,50 | 16 classes 0,75 | ms/página |
|---|---:|---:|---:|---:|---:|---:|---:|
| extrator | 0,573 [0,530; 0,614] | 0,399 [0,366; 0,433] | 0,555 [0,513; 0,595] | 0,387 [0,354; 0,420] | 0,422 [0,387; 0,457] | 0,321 [0,291; 0,351] | 4486,8 |
| ls3 | 0,780 [0,743; 0,816] | 0,731 [0,694; 0,766] | 0,769 [0,732; 0,804] | 0,722 [0,685; 0,757] | — | — | 711,2 |
| ls16 | 0,753 [0,720; 0,783] | 0,705 [0,673; 0,735] | 0,743 [0,709; 0,774] | 0,697 [0,664; 0,727] | 0,622 [0,591; 0,652] | 0,586 [0,555; 0,615] | 277,7 |
| puro_cv | 0,799 [0,760; 0,834] | 0,753 [0,715; 0,787] | 0,787 [0,750; 0,822] | 0,743 [0,705; 0,779] | — | — | 711,2 |
| v4_padrao | 0,757 [0,722; 0,791] | 0,571 [0,539; 0,603] | 0,742 [0,707; 0,776] | 0,561 [0,528; 0,593] | 0,582 [0,550; 0,614] | 0,469 [0,438; 0,498] | 3956,4 |
| v4_cv | 0,763 [0,727; 0,797] | 0,582 [0,548; 0,615] | 0,751 [0,715; 0,785] | 0,573 [0,539; 0,606] | 0,437 [0,408; 0,465] | 0,380 [0,353; 0,406] | 3678,8 |

O ls3 puro não possui 16 classes: a coluna correspondente fica sem número. O extrator atual e as caixas v4 sem par ls16 usam rótulos representativos do mapa do projeto (texto→paragraph, tabela→table, imagem→figure); o F1 fino desses sistemas é uma projeção limitada, não um classificador das 16 funções.

## Protocolo, parâmetros e validação por fonte

Mesma régua de extrator_vs_detector_ls.py: emparelhamento bipartido 1–1 que maximiza primeiro TP e depois IoU; TP/FP/FN somados antes do F1. unknown fica fora somente da régua 3 classes. Nenhuma transcrição, origem ou caixa humana entra na produção das regiões. As palavras e o índice da página são os insumos verificados e congelados do experimento anterior.

Configuração padrão: `{"ajuste": true, "base": "uniao", "conflitos": true, "contencao": 0.98, "detector": true, "folga": 0.5, "orfas": true, "par_classe": 0.5, "score": 0.25, "sem_texto": true, "texto": true}`.

A união preserva exclusivamente a localização do ls3 e associa classes ls16 por casamento 1–1 com IoU ≥ 0,50 e concordância em 3 classes; não acrescenta outra caixa ls16. Sem par usa o rótulo representativo. As caixas de texto ajustam-se ao envelope das palavras com centro dentro; tabela/imagem conservam a geometria nessa etapa. Órfãs passam pelo segmentador v3 em pontos, podendo ser anexadas quando a folga cabe no parâmetro e a união não atravessa outra caixa. Contenção suprime a caixa menor; interseções restantes recebem um corte x/y com menor perda de área. Palavras expulsas de cantos por um corte recebem caixas com subtração retangular exata das caixas já presentes, sem reintroduzir sobreposição. Cada palavra alfanumérica visível tem um único proprietário explícito com c+d ligadas, inclusive na borda do corte; separadores sem letras/dígitos seguem o descarte v3.

O recorte visível do raster é respeitado: 55 tokens cujos centros estão fora dele não entram no v4. As caixas finais são limitadas às dimensões da imagem, como as propostas do extrator anterior; a transformação pontos→pixels conserva a origem do CropBox.

Parâmetros fixos herdados do v3 não foram reaprendidos: critérios de linhas, calhas e parágrafos. Também são fixos o IoU de associação de classes, a concordância em 3 classes e a regra de corte com menor área perdida. São padrões estruturais predefinidos, não limiares escolhidos no ouro. A grade de ajuste eleva score mínimo {0,25; 0,45; 0,65}, testa folga {0; 0,5; 1} altura de palavra, contenção {0,90; 0,98; 1,00} e base {ls3; ls16; união}. Como o cache corta em 0,25, não é possível pesquisar scores menores sem nova inferência.

Grade predefinida com 81 configurações. Para cada fonte, os parâmetros e a base são escolhidos apenas nas outras fontes por F1 micro de localização 0,50 (desempate por localização 0,75 e ordem fixa da grade). As predições fora da fonte são concatenadas antes de medir v4_cv. A ablação retira uma etapa usando os mesmos parâmetros escolhidos para o v4 completo, sem novo ajuste.

| Configuração escolhida | Fontes |
|---|---:|
| ls3; score 0,45; folga 1,00; contenção 0,90 | 42 |

O teste original vira um conjunto de desenvolvimento com validação cruzada de pós-processamento. Isso evita ajustar na fonte avaliada, mas não cria um novo teste independente: a proposta de regras conhece o domínio e a comparação anterior. Não se ajustou na convenção Diamond.

Controle do efeito do score: puro_cv escolhe entre ls3/ls16 e scores {0,25; 0,45; 0,65} nas outras fontes, pela mesma função objetivo do v4. Assim o detector recebe a mesma oportunidade de reduzir falsos positivos, sem ajuste de geometria nem recuperação de órfãs.
Escolhas do puro_cv: ls3, score 0,45: 42 fontes.
Contra esse controle ajustado, Δ localização v4_cv−puro_cv = **-0,035**. Este é o contraste adequado para atribuir ganho adicional às regras, além da comparação pedida com detectores padrão.

Auditoria nominal preservada: 1 página(s) com alias confirmado entre teste e treino/validação (pag df↔df). A divisão não foi alterada. IC de páginas pode ser otimista por dependência intrafonte e por compartilhar os conjuntos de ajuste dos folds.

## Teste pareado

Diferença v4_cv−comparador; Wilcoxon bilateral sobre F1 por página, sem arredondar. IC micro é bootstrap pareado de páginas. A coluna por fontes reamostra fontes inteiras como análise de sensibilidade, sem reaprender parâmetros em cada bootstrap.

| Comparador / régua | Δ micro [IC páginas] | IC por fontes | Δ médio por página | p páginas | p fontes | Ganha/empata/perde |
|---|---:|---:|---:|---:|---:|---:|
| extrator/loc50 | 0,190 [0,148; 0,235] | [0,131; 0,244] | 0,164 [0,133; 0,195] | 1,22e-20 | 0,000002 | 225/20/72 |
| extrator/c3_50 | 0,196 [0,154; 0,240] | [0,137; 0,250] | 0,174 [0,143; 0,205] | 4,99e-22 | 7,67e-07 | 227/20/70 |
| ls3/loc50 | -0,017 [-0,032; -0,003] | [-0,039; 0,003] | -0,044 [-0,061; -0,028] | 0,000367 | 0,016732 | 129/36/152 |
| ls3/c3_50 | -0,018 [-0,033; -0,004] | [-0,039; 0,002] | -0,047 [-0,064; -0,031] | 0,000019 | 0,007183 | 121/38/158 |
| puro_cv/loc50 | -0,035 [-0,048; -0,024] | [-0,052; -0,020] | -0,056 [-0,071; -0,041] | 2,87e-11 | 0,000373 | 84/76/157 |
| puro_cv/c3_50 | -0,036 [-0,049; -0,025] | [-0,053; -0,021] | -0,058 [-0,073; -0,043] | 1,95e-12 | 0,000229 | 80/78/159 |
| rtdetr_l_puro/loc50 | 0,209 [0,189; 0,229] | [0,177; 0,234] | 0,160 [0,136; 0,184] | 4,04e-29 | 3,95e-09 | 267/8/42 |
| rtdetr_l_puro/c3_50 | 0,203 [0,183; 0,223] | [0,172; 0,229] | 0,152 [0,127; 0,175] | 4,41e-28 | 6,73e-09 | 264/8/45 |

O melhor detector puro com limiares padrão é ls3, escolhido na comparação anterior e conservado como referência fixa. O controle puro_cv escolhe a base e o score somente nas fontes de ajuste. Os p são exploratórios e não corrigidos por múltiplas comparações. A reutilização do teste para desenvolver regras e os folds correlacionados limitam qualquer leitura confirmatória.

## Bases e ablação

As bases padrão usam as mesmas etapas e limiares, sem ajuste. As linhas cv_base repetem a escolha de parâmetros nas outras fontes, restringindo a grade àquela base. As ablações cv conservam a escolha da base e dos limiares do fold completo. Sem a: somente agrupamento de palavras órfãs por v3. Sem f: descarta páginas sem palavras. Sem e: geometria idêntica, mas nenhuma transcrição é entregue.

| Sistema | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 16 classes 0,50 | 16 classes 0,75 | ms/página |
|---|---:|---:|---:|---:|---:|---:|---:|
| v4_base_ls3_padrao | 0,757 | 0,571 | 0,742 | 0,561 | 0,431 | 0,372 | 3678,6 |
| v4_base_ls16_padrao | 0,753 | 0,577 | 0,738 | 0,566 | 0,597 | 0,482 | 3245,8 |
| v4_cv_base_ls3 | 0,763 | 0,582 | 0,751 | 0,573 | 0,437 | 0,380 | 3678,8 |
| v4_cv_base_ls16 | 0,756 | 0,582 | 0,740 | 0,569 | 0,598 | 0,485 | 3246,8 |
| v4_cv_base_uniao | 0,763 | 0,582 | 0,751 | 0,573 | 0,584 | 0,477 | 3959,0 |
| v4_cv_sem_a_detector | 0,223 | 0,144 | 0,218 | 0,142 | 0,101 | 0,075 | 3005,8 |
| v4_cv_sem_b_ajuste | 0,778 | 0,718 | 0,765 | 0,708 | 0,438 | 0,409 | 3678,7 |
| v4_cv_sem_c_orfas | 0,790 | 0,608 | 0,777 | 0,599 | 0,453 | 0,397 | 3678,8 |
| v4_cv_sem_d_conflitos | 0,760 | 0,584 | 0,749 | 0,575 | 0,434 | 0,380 | 3678,3 |
| v4_cv_sem_e_texto | 0,763 | 0,582 | 0,751 | 0,573 | 0,437 | 0,380 | 3678,2 |
| v4_cv_sem_f_sem_texto | 0,754 | 0,573 | 0,742 | 0,564 | 0,433 | 0,375 | 3680,8 |

## Qualidade do texto

Pares de localização IoU ≥ 0,50, independentemente de classe. CER = distância Levenshtein em caracteres / caracteres da transcrição humana, podendo ultrapassar 1. Somente espaços são normalizados; caixa, acentos, pontuação e hífens são preservados. Texto lido por linha e da esquerda para a direita, sem OCR e sem reconstrução de células de tabela. Ouro sem transcrição não tem CER e é contado à parte. Esta análise está condicionada às caixas que cada sistema consegue localizar.

| Sistema | Pares | Ouro vazio | Pares comparáveis | Predição vazia | CER mediana | CER p90 | Texto idêntico |
|---|---:|---:|---:|---:|---:|---:|---:|
| extrator | 3251 | 626 | 2625 | 28 | 0,000 | 0,259 | 68,2% |
| ls3 | 4838 | 1366 | 3472 | 136 | 0,000 | 0,357 | 66,0% |
| ls16 | 4630 | 1281 | 3349 | 127 | 0,000 | 0,346 | 67,0% |
| puro_cv | 4602 | 1262 | 3340 | 130 | 0,000 | 0,357 | 66,5% |
| v4_padrao | 4499 | 1273 | 3226 | 129 | 0,000 | 0,370 | 67,1% |
| v4_cv | 4454 | 1231 | 3223 | 126 | 0,000 | 0,357 | 67,1% |

Para os detectores puros e o extrator atual, o texto desta tabela é uma leitura diagnóstica adicional da mesma camada PDF nas caixas congeladas, sem exclusividade entre caixas; não é saída originalmente entregue pelos detectores. O v4 efetivamente entrega texto e propriedade das palavras. Isso permite distinguir qualidade de localização e efeitos do ajuste/exclusividade na transcrição.

| Classe no ouro (v4_cv) | Pares com transcrição | CER mediana | Texto idêntico |
|---|---:|---:|---:|
| act | 111 | 0,000 | 69,4% |
| act section | 69 | 0,000 | 73,9% |
| paragraph | 1495 | 0,000 | 63,2% |
| signature | 108 | 0,000 | 74,1% |
| heading | 5 | 1,000 | 0,0% |
| id | 36 | 0,000 | 94,4% |
| header | 504 | 0,000 | 87,3% |
| footer | 176 | 0,000 | 77,8% |
| table | 257 | 0,009 | 36,2% |
| chart | 2 | 0,000 | 100,0% |
| figure | 43 | 1,000 | 34,9% |
| caption | 69 | 0,000 | 79,7% |
| title | 165 | 0,000 | 75,8% |
| section title | 93 | 0,000 | 78,5% |
| sub section title | 88 | 0,111 | 38,6% |
| unknown | 2 | 0,000 | 100,0% |

Sem camada digital: 0 pares com transcrição humana não vazia, CER mediana —; nessas páginas o v4 entrega somente caixas e texto vazio. Não confundir vazio correto em imagem com transcrição recuperada.

## Revocação por origem da caixa do ouro

Casamento global antes do estrato; nenhuma predição pode acertar duas caixas de origens distintas. Origem é o campo labels com fallback para rectangle, preservado pelo cache anterior.

| Sistema | Origem | Ouro loc | Revocação loc50 | Ouro 3 classes | Revocação 3 classes |
|---|---|---:|---:|---:|---:|
| extrator | manual | 996 | 0,481 | 995 | 0,456 |
| extrator | prediction | 2048 | 0,563 | 2048 | 0,554 |
| extrator | prediction-changed | 2440 | 0,663 | 2438 | 0,639 |
| extrator | ausente | 0 | — | 0 | — |
| extrator | ambigua | 1 | 0,000 | 1 | 0,000 |
| ls3 | manual | 996 | 0,780 | 995 | 0,767 |
| ls3 | prediction | 2048 | 0,915 | 2048 | 0,912 |
| ls3 | prediction-changed | 2440 | 0,896 | 2438 | 0,876 |
| ls3 | ausente | 0 | — | 0 | — |
| ls3 | ambigua | 1 | 1,000 | 1 | 1,000 |
| ls16 | manual | 996 | 0,714 | 995 | 0,695 |
| ls16 | prediction | 2048 | 0,894 | 2048 | 0,892 |
| ls16 | prediction-changed | 2440 | 0,856 | 2438 | 0,840 |
| ls16 | ausente | 0 | — | 0 | — |
| ls16 | ambigua | 1 | 1,000 | 1 | 1,000 |
| puro_cv | manual | 996 | 0,700 | 995 | 0,688 |
| puro_cv | prediction | 2048 | 0,881 | 2048 | 0,878 |
| puro_cv | prediction-changed | 2440 | 0,861 | 2438 | 0,841 |
| puro_cv | ausente | 0 | — | 0 | — |
| puro_cv | ambigua | 1 | 1,000 | 1 | 1,000 |
| v4_padrao | manual | 996 | 0,682 | 995 | 0,663 |
| v4_padrao | prediction | 2048 | 0,863 | 2048 | 0,860 |
| v4_padrao | prediction-changed | 2440 | 0,841 | 2438 | 0,814 |
| v4_padrao | ausente | 0 | — | 0 | — |
| v4_padrao | ambigua | 1 | 1,000 | 1 | 1,000 |
| v4_cv | manual | 996 | 0,652 | 995 | 0,637 |
| v4_cv | prediction | 2048 | 0,865 | 2048 | 0,862 |
| v4_cv | prediction-changed | 2440 | 0,833 | 2438 | 0,813 |
| v4_cv | ausente | 0 | — | 0 | — |
| v4_cv | ambigua | 1 | 1,000 | 1 | 1,000 |

## Onde ainda erra

Perdas são caixas humanas sem par de localização. Revocação fina exige classe igual. Os tipos de página se sobrepõem, e suas contagens não devem ser somadas.

| Classe humana | Caixas | Perdidas loc | Revocação loc50 v4 | Revocação loc50 ls3 | Revocação fina v4 |
|---|---:|---:|---:|---:|---:|---:|
| paragraph | 2218 | 355 | 0,840 | 0,885 | 0,839 |
| header | 728 | 130 | 0,821 | 0,920 | 0,000 |
| table | 396 | 90 | 0,773 | 0,859 | 0,760 |
| caption | 206 | 86 | 0,583 | 0,699 | 0,000 |
| figure | 505 | 76 | 0,850 | 0,919 | 0,776 |
| signature | 242 | 65 | 0,731 | 0,814 | 0,000 |
| title | 279 | 56 | 0,799 | 0,910 | 0,000 |
| footer | 245 | 47 | 0,808 | 0,890 | 0,000 |
| act | 159 | 33 | 0,792 | 0,855 | 0,000 |
| section title | 149 | 33 | 0,779 | 0,852 | 0,000 |
| heading | 80 | 29 | 0,637 | 0,812 | 0,000 |
| sub section title | 125 | 18 | 0,856 | 0,904 | 0,000 |
| act section | 102 | 10 | 0,902 | 0,971 | 0,000 |
| id | 45 | 2 | 0,956 | 0,933 | 0,000 |
| chart | 3 | 1 | 0,667 | 0,667 | 0,000 |
| unknown | 3 | 0 | 1,000 | 1,000 | 0,000 |

| Tipo de página | Páginas | Extrator loc50 | ls3 loc50 | v4_cv loc50 | Δ v4−ls3 |
|---|---:|---:|---:|---:|---:|
| com camada | 306 | 0,576 | 0,778 | 0,760 | -0,018 |
| sem tabela | 135 | 0,521 | 0,764 | 0,774 | 0,011 |
| com imagem/rubrica | 238 | 0,563 | 0,801 | 0,790 | -0,011 |
| com tabela | 182 | 0,620 | 0,796 | 0,753 | -0,043 |
| sem imagem/rubrica | 79 | 0,608 | 0,708 | 0,672 | -0,036 |
| sem camada | 11 | 0,194 | 0,892 | 0,929 | 0,037 |

Confusões de classe nos pares já localizados: header → paragraph: 593; title → paragraph: 220; footer → paragraph: 196; signature → paragraph: 174; act → paragraph: 126; caption → paragraph: 120; section title → paragraph: 116; sub section title → paragraph: 107; act section → paragraph: 92; heading → figure: 48; id → paragraph: 43; figure → paragraph: 26.

Exemplos adversos selecionados automaticamente pelas maiores perdas por página contra ls3, em fontes distintas; não representam a frequência do erro. Verde: ouro; vermelho: v4.

- **nova iguacu**, `lote_20260715_100540/RIO_DE_JANEIRO_ABRIL_2026+-+rj_nova_iguacu+-+2026-04-29-NORMAL-Ed0-Pag87/RIO_DE_JANEIRO_ABRIL_2026+-+rj_nova_iguacu+-+2026-04-29-NORMAL-Ed0-Pag87.pdf#p39`: F1 loc50 0,000, Δ ls3 -0,500. Caixa region_0075 (table, prediction-changed) sem par; maior IoU 0,401; trecho “14 DIREITOS DA CIDADANIA - - - 14.244 ASSISTÊNCIA COMUNITÁRIA - - - 14.224.5045 PROGRAMA ALUGUEL SOCIAL - - 15 URBANISMO 207.618.297,88 64.019.756,08 271.638.05”. [Inspeção interna](extrator_v4_cache/exemplos/57e44e2af75971a17c020e0b.jpg).
- **sao paulo gestao despesas**, `0423_2026-06-02-NORMAL-EdX-Pag311_Sao_Paulo(executivo_atos_de_gestao_e_despesas)_p0060/0423_2026-06-02-NORMAL-EdX-Pag311_Sao_Paulo(executivo_atos_de_gestao_e_despesas)_p0060.pdf#p1`: F1 loc50 0,375, Δ ls3 -0,500. Caixa region_0001 (header, prediction-changed) sem par; maior IoU 0,339; trecho “60/311 - Diário Oficial do Estado de São Paulo”. [Inspeção interna](extrator_v4_cache/exemplos/fb31c7d93fd25a1b4f4c1837.jpg).
- **pa**, `lote_20260715_100540/2026-04-01-EXTRA-Ed20260401-EXTRA-Pag164_PA/2026-04-01-EXTRA-Ed20260401-EXTRA-Pag164_PA.pdf#p132`: F1 loc50 0,429, Δ ls3 -0,481. Caixa region_0062 (header, prediction-changed) sem par; maior IoU 0,245; trecho “132  DIÁRIO OFICIAL Nº 36.582”. [Inspeção interna](extrator_v4_cache/exemplos/cdaf6de671a2a8d7b9b3c658.jpg).
- **natal**, `lote_20260715_100540/2026-04-20-NORMAL-Ed0-Pag103_Natal/2026-04-20-NORMAL-Ed0-Pag103_Natal.pdf#p15`: F1 loc50 0,286, Δ ls3 -0,464. Caixa region_0067 (figure, prediction-changed) sem par; maior IoU 0,000; trecho “”. [Inspeção interna](extrator_v4_cache/exemplos/80d18503225cffeaea06774e.jpg).
- **jundiai**, `lote_20260916_184436/2026-04-29-NORMAL-Ed5809-Pag223_Jundiai/2026-04-29-NORMAL-Ed5809-Pag223_Jundiai.pdf#p89`: F1 loc50 0,333, Δ ls3 -0,449. Caixa region_0003 (header, prediction-changed) sem par; maior IoU 0,488; trecho “Imprensa Oficial do Município de Jundiaí Edição 5809 | 2ª edição de 29 de abril de 2026”. [Inspeção interna](extrator_v4_cache/exemplos/e1e5da9bbc90cc03c51a6b57.jpg).

Diagnóstico do processamento: 6037 palavras órfãs após ajuste; 450 caixas criadas nessa etapa; 4137 palavras anexadas; 340 caixas suprimidas; 252 cortes; 38 caixas adicionais recuperam cantos expulsos pelos cortes. Terminam sem caixa 178 tokens, dos quais 0 são alfanuméricos; 0 atribuições duplicadas.

Leitura das oportunidades: detector maior só rende se melhorar localização na mesma régua, não basta mAP anunciado. O desnível entre localização e F1 fino e as confusões acima justificam testar classificação por texto para funções como act, id e signature. A ablação decide o valor das regras: envelope obrigatório pode retirar margens que fazem parte da convenção; órfãs aumentam cobertura textual e também falsos positivos; contenção pode apagar regiões legítimas sobrepostas. O próximo teste deve medir essas hipóteses em páginas independentes anotadas do zero.

Evidência para priorizar regras: v4_cv_sem_c_orfas dá F1 loc50 0,790, Δ 0,027 contra o completo; v4_cv_sem_b_ajuste dá loc75 0,718, Δ 0,136. Estes resultados são ablações exploratórias, não uma nova configuração selecionada em teste independente.

## Referência na convenção antiga: Diamond

11 páginas concluídas por humano; régua importada de src/eval/avaliar_diamond.py. É Jaccard dos conjuntos de palavras por região, não IoU geométrico. Caixas sem palavras não contribuem a essa régua. A referência foi desenhada do zero pelo autor; isso reduz ancoragem, mas não remove subjetividade nem permite generalização com n pequeno.

| Sistema / régua | F1 Jaccard 0,50 | F1 Jaccard 0,90 | F1 com classe | Classe por palavra |
|---|---:|---:|---:|---:|
| 9/extrator | 0,851 | 0,754 | 0,696 | 0,769 |
| 9/ls3 | 0,765 | 0,646 | 0,431 | 0,680 |
| 9/ls16 | 0,753 | 0,648 | 0,628 | 0,756 |
| 9/v4_padrao | 0,771 | 0,668 | 0,622 | 0,763 |
| 9/v4_validacao_ls | 0,750 | 0,648 | 0,397 | 0,696 |
| 3/extrator | 0,850 | 0,750 | 0,824 | 0,978 |
| 3/ls3 | 0,765 | 0,646 | 0,731 | 0,930 |
| 3/ls16 | 0,753 | 0,648 | 0,718 | 0,947 |
| 3/v4_padrao | 0,771 | 0,668 | 0,742 | 0,964 |
| 3/v4_validacao_ls | 0,750 | 0,648 | 0,715 | 0,953 |

Na régua antiga de 9 classes, v4 validado no LS muda -0,101 frente ao extrator atual. Sua configuração foi escolhida em todas as páginas LS, nunca nas 11 Diamond: `{"ajuste": true, "base": "ls3", "conflitos": true, "contencao": 0.9, "detector": true, "folga": 1.0, "orfas": true, "par_classe": 0.5, "score": 0.45, "sem_texto": true, "texto": true}`. O resultado confirma que granularidade e convenção são parte da tarefa; não se pode intercambiar os dois F1.

O Diamond tampouco é teste intocado para o extrator antigo: a docstring de src/data/regioes.py registra que fundir_fragmentos foi calibrada no diamond_teste. A vantagem do antigo nesse lote mistura compatibilidade de convenção e adaptação prévia às páginas; não permite isolar causalmente esses fatores.

## Detector maior do Kaggle (separado)

RT-DETR L de 16 classes, checkpoint local, mesmo split; inferência integral em CPU a 1024 pixels, conf 0,25. Etapas v4 e limiares padrão fixos, sem seleção posterior. O modelo maior foi escolhido pelo mAP anunciado no próprio teste na nota do autor: seleção exploratória, não confirmação independente. O mAP não é comparado diretamente com F1 nesta tabela.

| Sistema | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 16 classes 0,50 | 16 classes 0,75 | ms/página |
|---|---:|---:|---:|---:|---:|---:|---:|
| rtdetr_l_puro | 0,554 [0,527; 0,579] | 0,521 [0,494; 0,547] | 0,548 [0,521; 0,572] | 0,517 [0,490; 0,543] | 0,512 [0,486; 0,536] | 0,485 [0,459; 0,511] | 2350,1 |
| v4_kaggle_padrao | 0,768 [0,731; 0,800] | 0,586 [0,552; 0,617] | 0,748 [0,712; 0,780] | 0,574 [0,540; 0,605] | 0,621 [0,589; 0,651] | 0,499 [0,467; 0,530] | 5322,6 |

O detector maior puro tem 7786 falsos positivos nessa régua e nesse score. O v4 suprime 6822 caixas por contenção, além das outras etapas, e eleva seu F1 para 0,768. Contra o v4 padrão com união local, a localização muda 0,010; ainda fica abaixo do ls3 puro 0,780. O ganho é do conjunto de etapas, não uma ablação causal do detector maior ou da contenção isoladamente.

## Limitações e tempo

Anotação corrigindo pré-anotação induz viés de ancoragem: até uma caixa manual é desenhada com sugestões visíveis. Origem não equivale a dificuldade e não permite concluir causalmente que um modelo herdou erros. A contagem incremental encontra 2119 páginas únicas nas conversões do parceiro e 2118 no split de detecção, com 1 fora do split (motivo não auditado aqui). A divisão contém 1590 páginas de treino, 211 de validação e 317 de teste. Este pós-processamento usa somente as 317 páginas pedidas e os detectores existentes. Não houve novo treinamento nem uso das outras partições para ajustar regras.

Poucas fontes e páginas por fonte tornam estimativas frágeis; há um alias nominal conhecido. O bootstrap principal reamostra páginas, não resolve dependência entre fontes ou seleção dos parâmetros. CER só nos pares localizados favorece cada sistema de maneira diferente. A camada PDF pode conter OCR embutido, falhas de Unicode ou texto parcial; não foi auditada palavra por palavra. A exclusividade de palavras não assegura cobertura total nem uma ordem humana dentro da região. Não medimos ordem entre regiões nem RI extrínseca.

Latência de CPU inclui os custos congelados de inferência dos detectores e extração de palavras; união soma as duas inferências. A imagem raster LS já existe; produção a partir de PDF precisa acrescentar renderização. Custos do extrator atual incluem renderização/Docling do cache anterior. As tarefas concorrentes e as datas distintas impedem tratar estes números como benchmark controlado. Inicialização, leitura de cache, avaliação e escolha de parâmetros ficam fora; tempo de pós-processamento v4 é medido separadamente abaixo.

| Sistema | Pós-processamento médio (ms) | Tempo total mediano (ms) | Tempo total p95 (ms) |
|---|---:|---:|---:|
| extrator | 0,0 | 2313,0 | 16708,4 |
| ls3 | 0,0 | 697,9 | 850,7 |
| ls16 | 0,0 | 270,2 | 330,0 |
| puro_cv | 0,0 | 697,9 | 850,7 |
| v4_padrao | 6,6 | 1712,2 | 15778,7 |
| v4_cv | 6,7 | 1439,8 | 15453,4 |

## Esqueleto para um módulo futuro em src/data/extrator_v4.py

```python
@dataclass(frozen=True)
class ConfigV4:
    base: str
    score: float
    folga_alturas: float
    contencao: float
    etapas: tuple[str, ...]

def detectar(imagem, modelo_local, *, device='cpu'):
    # Caixas em pixels e classes do guia; sem baixar pesos.
    ...

def propor_v4(palavras_pdf, detectores_em_pontos, config):
    caixas = caixas_base(detectores_em_pontos, config)
    # b: envelope; c: orfas v3; d: contencao/cortes e propriedade unica.
    # e: texto da camada; f: detector sozinho quando nao ha palavras.
    return caixas  # id, bbox, classe, score, texto, palavras_ids, origem_v4
```

A implementação funcional está no script desta análise; nenhum módulo src foi alterado. Configuração e convenção devem ser explícitas antes de qualquer adoção no TCC.

## Reprodução e conferência

```powershell
venv/Scripts/python.exe orquestracao/analises/extrator_v4.py --autoteste
venv/Scripts/python.exe orquestracao/analises/extrator_v4.py --do-zero --kaggle
```

Bootstrap: 2000 reamostras, semente 20261003. Assinatura dos insumos e algoritmo: `421d6e41e987323f2601c94274db8209e7fbbe061858c9ce1e655bd5ca48f22b`. Execução do zero solicitada: True. --do-zero refaz a grade, a avaliação e os diagnósticos; conserva caches de palavras/PDF/detectores já autorizados. JSON verificável, configurações por fonte, métricas por página, predições com texto e exemplos ficam em resultados/extrator_v4_cache/. O relatório e sua tabela são conferidos pelo script contra o JSON de resultados. Derivados do parceiro não devem sair deste repositório.
