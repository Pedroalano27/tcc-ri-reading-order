# Caminho rápido digital com PyMuPDF

Estado: CONCLUÍDO. CPU; PyMuPDF 1.28.2; nenhuma GPU, OCR, rede ou modelo no caminho rápido.

## Resumo em cinco linhas

1. Veredito: o caminho digital acelera a extração, mas não substitui universalmente o detector para tabelas sem grade e imagens compostas.
2. Nas 44 páginas Golden, trocando só átomos: τ 0,967 PyMuPDF, 0,946 Docling, 0,917 sem átomos; com words realmente MuPDF, τ 0,920 em suporte comum (diagnóstico otimista).
3. No Diamond, PyMuPDF conservador recupera 78,4% das tabelas e 59,1% das imagens; no LS digital, 49,4% e 34,5%.
4. No tempo fim a fim pareado de 44 páginas, a aceleração é 8,1×; há 11 páginas LS sem palavras, fora da aplicabilidade do caminho digital.
5. Recomendação: PyMuPDF primeiro, com verificação de texto/geometria; detector/OCR como fallback para evidência tabular ou visual inconclusiva, validando a política em ouro independente.

## Protocolo e rastreabilidade

Conferência de 10 das 60 páginas já medidas; semente fixa, duas de PE, SP e MG incluídos. Não se repetiu a medição inteira já existente. O relatório anterior não foi editado. Golden: 44/44 páginas medidas, revisões Diamond exatamente da data congelada no Golden, incluindo figuras sem texto. LS: 317/317 páginas de teste com PDF local e ouro convertido dos quatro seeds; nenhum export grande é carregado como texto integral.
As 16 classes vêm de `src/data/taxonomia_layout.py`: table → tabela; figure/chart/heading → imagem; unknown e classe ausente/inválida ficam fora; as demais são texto. O detector geométrico emite somente table/picture; o texto restante vem da camada digital, sem caixas finas semânticas. A qualidade abaixo mede localização de tabela/imagem, não F1 de segmentação do texto.
Predições e ouro são pareados por classe, um a um, maximizando primeiro a cardinalidade com IoU ≥ 0,5 e depois IoU. Precisão/recall/F1 micro de regiões, macro de páginas somente nas métricas de ordem. Não confundir os dois ouros: convenções de caixa e classe diferem.
Seed 20261003; bootstrap percentil de 5000 reamostras agrupadas por veículo (parte antes da primeira barra), preservando todas as páginas dos veículos sorteados. IC condicional às configurações LOPO antigas, congeladas e não selecionadas novamente; não estima incerteza do desenvolvimento. Wilcoxon bilateral pareado com zero_method='pratt', aproximação normal; p é exploratório, páginas do mesmo veículo não são independentes. Nenhuma decisão de adoção foi aplicada ao pipeline.
Hashes das entradas, fontes e PDFs invalidam caches; cada página é salva atomicamente antes da próxima. Tempos incluem abertura do PDF por página e ordem; não incluem leitura do ouro, matching, hashes, escrita de cache/relatório. Não há remoção de outliers nem inferência de tempos do detector a partir de caches antigos.

## Palavras: auditoria do relatório existente

`get_text('words', sort=False)` é usado diretamente: não se afirma identidade com o contrato que desduplica caracteres, descarta texto girado e junta letras espaçadas no pdfplumber. Matching exige texto NFKC igual e centros próximos (até três pontos em x e cinco ou meia altura em y); reportam-se também multiconjunto exato e tolerância máxima das quatro bordas.
| Veículo / página | Palavras plumber / MuPDF | Pares espaciais | Pares com todas as bordas ≤ 2 pt / ≤ 5 pt | τ da ordem dos pares | s plumber / MuPDF |
|---|---:|---:|---:|---:|---:|
| `official_diary_RJ_seropedica/executive_official_diary_2022-04-11_967.pdf#p1` | 63 / 63 | 63 | 0 / 56 | 1,000 | 0,090 / 0,026 |
| `official_diary_ce/do20250314p03.pdf#p45` | 1740 / 1740 | 1740 | 0 / 1740 | 1,000 | 2,596 / 0,018 |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | 4360 / 4608 | 3331 | 3292 / 3331 | 1,000 | 55,736 / 0,057 |
| `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30` | 1597 / 1590 | 1296 | 1 / 1296 | 1,000 | 3,028 / 0,022 |
| `official_diary_pe/2021-08-27_1-Poder Executivo.pdf#p10` | 2922 / 2922 | 2922 | 2921 / 2921 | 1,000 | 14,249 / 0,029 |
| `official_diary_pe/2026-01-09_1-Poder Executivo.pdf#p8` | 3427 / 3427 | 3426 | 3426 / 3426 | 1,000 | 25,659 / 0,034 |
| `official_diary_pr/executive_official_diary_2023-12-04.pdf#p101` | 1695 / 1570 | 1570 | 1566 / 1570 | 1,000 | 7,068 / 0,038 |
| `official_diary_pr_curitiba/24-Supl1_2024-02-05.pdf#p7` | 238 / 236 | 236 | 207 / 236 | 1,000 | 0,164 / 0,011 |
| `official_diary_rn/DOE-RN_2022-11-23_Ordinaria.pdf#p30` | 2050 / 2052 | 2033 | 0 / 2033 | 1,000 | 6,405 / 0,055 |
| `official_diary_sp/Executivo - Caderno 2_2022-12-06.pdf#p43` | 3534 / 3566 | 3530 | 3530 / 3530 | 1,000 | 20,914 / 0,043 |

No total, 21626 palavras plumber, 21774 MuPDF, 20147 pares (93,2% do plumber); multiconjunto exatamente igual em 2/10 páginas. Logo, a afirmação antiga de paridade garantida/perda nula não é sustentada por esta auditoria.
| Página | Mediana |Δx0| / |Δy0| / |Δx1| / |Δy1|, pt | p95, pt | Rotação |
|---|---|---|---:|
| `official_diary_RJ_seropedica/executive_official_diary_2022-04-11_967.pdf#p1` | 0,000 / 4,015 / 0,000 / 0,000 | 0,000 / 5,800 / 0,000 / 0,000 | 0 |
| `official_diary_ce/do20250314p03.pdf#p45` | 0,000 / 2,776 / 0,000 / 0,000 | 0,000 / 2,776 / 0,000 / 0,000 | 0 |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | 0,000 / 1,883 / 0,000 / 0,001 | 0,000 / 1,884 / 0,000 / 0,004 | 0 |
| `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30` | 0,000 / 2,478 / 0,000 / 0,000 | 0,000 / 2,478 / 0,000 / 0,001 | 0 |
| `official_diary_pe/2021-08-27_1-Poder Executivo.pdf#p10` | 0,000 / 0,696 / 0,000 / 0,000 | 0,000 / 0,696 / 0,000 / 0,000 | 0 |
| `official_diary_pe/2026-01-09_1-Poder Executivo.pdf#p8` | 0,000 / 0,696 / 0,000 / 0,000 | 0,001 / 0,696 / 0,001 / 0,000 | 0 |
| `official_diary_pr/executive_official_diary_2023-12-04.pdf#p101` | 0,000 / 0,733 / 0,000 / 0,000 | 0,000 / 0,766 / 0,000 / 0,094 | 0 |
| `official_diary_pr_curitiba/24-Supl1_2024-02-05.pdf#p7` | 0,000 / 0,818 / 0,000 / 0,000 | 0,000 / 2,256 / 0,000 / 0,736 | 0 |
| `official_diary_rn/DOE-RN_2022-11-23_Ordinaria.pdf#p30` | 0,000 / 2,776 / 0,000 / 0,000 | 0,000 / 2,776 / 0,000 / 0,000 | 0 |
| `official_diary_sp/Executivo - Caderno 2_2022-12-06.pdf#p43` | 0,000 / 0,053 / 0,000 / 0,053 | 0,000 / 0,054 / 0,000 / 0,054 | 0 |

Categorias automáticas dos não pareados (não são diagnóstico causal de fonte): {'outra divergencia': 1184, 'espacos/tokenizacao': 80, 'hifen/travessao': 130, 'CID/caractere substituto': 5, 'sem vizinho espacial': 80}. Caracteres de spans invisíveis: 0; palavras MuPDF duplicadas com mesma caixa arredondada: 0. Invisibilidade não é inferida da transcrição; um span tipo 3/opacidade zero pode ser camada OCR. Não foi aplicada deshifenização entre linhas.
Diferenças sistemáticas: métricas verticais de fonte alteram top/bottom; espaços sintetizados/tokenização e a junção de letras do extrator mudam o inventário; ligaduras são normalizadas só no matching; CIDs/substitutos dependem da codificação. A ordem nativa é do conteúdo e pode diferir entre parsers; não é ordem humana nem parâmetro de ordenação. O teste de pares não mede equivalência semântica de palavras fundidas ou partidas.
Coordenadas retornadas pelo MuPDF são relativas à CropBox **não rotacionada**; page.rect é rotacionada. Para o ouro Diamond usamos a transformação explícita para MediaBox rotacionada do módulo opcional existente; para LS aplicamos rotation_matrix e escala separada x/y da imagem. Não se usa a heurística de subtrair CropBox olhando as primeiras palavras. [API oficial de coordenadas](https://pymupdf.readthedocs.io/en/latest/page.html).

| Exemplo | pdfplumber | MuPDF | Categoria automática |
|---|---|---|---|
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | diário | Diário | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | executivo | Executivo | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | ofício | Ofício | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | 48 .162/2021 | 162/2021 | espacos/tokenizacao |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | 5191000174/2016 . | 5191000174/2016. | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | SEINFrA | SEINFRA | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | rinha . | rinha. | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | objeto: | Objeto: | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | nio . | nio. | outra divergencia |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p25` | vigência: | Vigência: | outra divergencia |
| `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30` | comunidade | Comunidade | outra divergencia |
| `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30` | curtifrança, | Curtifrança, | outra divergencia |

## Regras sem detector

Conservador = find_tables(lines) + agrupamento de traços/retângulos + get_image_info + vetores. As duas estratégias find_tables são executadas com `use_layout=False`, sem pymupdf_layout. Tabelas exigem pelo menos duas linhas, duas colunas e área de quatrocentos pontos quadrados. A estratégia text é apresentada isoladamente e como ablação acrescentada ao conservador, sem escolher pelo desempenho no ouro.
Traços: cluster_drawings com tolerância de três pontos; pelo menos três horizontais e duas verticais distintas, sem curvas. Retângulos finos contam como traços. Fundo/borda com área acima de noventa por cento da página é excluído do agrupamento. Vetores: cluster com lados de pelo menos doze pontos, área de pelo menos cento e quarenta e quatro, e quatro curvas/diagonais; exclui os que ficam majoritariamente em tabela. Imagens raster: retângulos válidos com área mínima de dezesseis pontos quadrados. NMS elimina duplicatas da mesma classe. Não une tabelas adjacentes.
Score geométrico 1 é marcador de regra aceita, sem probabilidade calibrada: os limiares de confiança LOPO não selecionam os candidatos MuPDF. Isso é uma limitação da troca de origem, não uma comparação de confiança entre detector e regras. [Estratégias e desenhos na API oficial](https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables).

## Qualidade das regiões — Diamond congelado

| Método | Classe | TP / FP / FN | Precisão | Revocação | F1 |
|---|---|---:|---:|---:|---:|
| find_tables(lines) | tabela | 29 / 8 / 8 | 78,4% | 78,4% | 78,4% |
| find_tables(lines) | imagem | 0 / 0 / 66 | — | 0,0% | 0,0% |
| find_tables(text) | tabela | 4 / 38 / 33 | 9,5% | 10,8% | 10,1% |
| find_tables(text) | imagem | 0 / 0 / 66 | — | 0,0% | 0,0% |
| Agrupamento de traços/retângulos | tabela | 27 / 15 / 10 | 64,3% | 73,0% | 68,4% |
| Agrupamento de traços/retângulos | imagem | 0 / 0 / 66 | — | 0,0% | 0,0% |
| Imagens incorporadas | tabela | 0 / 0 / 37 | — | 0,0% | 0,0% |
| Imagens incorporadas | imagem | 36 / 60 / 30 | 37,5% | 54,5% | 44,4% |
| Desenhos vetoriais grandes | tabela | 0 / 0 / 37 | — | 0,0% | 0,0% |
| Desenhos vetoriais grandes | imagem | 6 / 22 / 60 | 21,4% | 9,1% | 12,8% |
| PyMuPDF conservador | tabela | 29 / 17 / 8 | 63,0% | 78,4% | 69,9% |
| PyMuPDF conservador | imagem | 39 / 82 / 27 | 32,2% | 59,1% | 41,7% |
| PyMuPDF conservador + text | tabela | 30 / 43 / 7 | 41,1% | 81,1% | 54,5% |
| PyMuPDF conservador + text | imagem | 39 / 82 / 27 | 32,2% | 59,1% | 41,7% |
| Docling congelado | tabela | 36 / 5 / 1 | 87,8% | 97,3% | 92,3% |
| Docling congelado | imagem | 51 / 44 / 15 | 53,7% | 77,3% | 63,4% |

Inclui tabela/figura da revisão humana Diamond, também as figuras sem palavras excluídas do lote de ordem. Docling = detector.regioes congelado, filtrado no score da configuração LOPO de cada página. O cache anterior já tem seu piso de confiança; não se simula recall abaixo dele.

## Qualidade — Label Studio interno

Páginas com palavras: 306; sem palavras: 11. Ausência de camada textual é um marcador operacional de digitalizada/vetorizada, não prova de scanner. Páginas com menos de vinte palavras: 59. Não se usa OCR. PKCS#7 extraídos apenas para temporário em resultados: 6 páginas.
Regiões-ouro LS sem palavras associadas, incluindo elementos gráficos: 1467. Permanecem na régua de detecção por IoU; não se aborta nem se atribui texto fictício.
Páginas com raster cobrindo pelo menos sessenta por cento da área: 75; dessas, 70 ainda têm palavras. Ter algum texto (por exemplo, só um cabeçalho digital) não comprova PDF nascido digital nem dispensa OCR no corpo. O estrato 'com palavras' inclui esses casos híbridos, e o subconjunto confirmado por transcrição abaixo ajuda a explicitar esse viés.
Índice do mapa é de base um, convertido por pagina−1; índice do acervo/Golden já é base zero. Escala = largura/altura em pixels do ouro dividida por page.rect em pontos. Para cada PDF local conferimos a transcrição em suas caixas e, quando existem, ambas as páginas vizinhas. A escala x/y evita arredondamento do raster; diferença de aspecto maior que três por cento é sinalizada.
Verificação positiva: 293/306 páginas digitais têm F1 espacial de tokens ≥ 0,5, aspecto compatível e nenhuma vizinha melhor em mais de 0,05; vizinha melhor: 0; aspecto suspeito: 0. Não se escolhe outra página/escala pelo ouro: casos incertos permanecem declarados. Sem texto/transcrição suficiente não se pode confirmar o alinhamento pelo texto.

F1 espacial de transcrição: mediana 0,991. Classe inválida/ausente: 1; unknown fora: 3. Resultados abaixo incluem todas as digitais, evitando esconder baixo alinhamento.

| Método | Classe | TP / FP / FN | Precisão | Revocação | F1 |
|---|---|---:|---:|---:|---:|
| find_tables(lines) | tabela | 186 / 46 / 203 | 80,2% | 47,8% | 59,9% |
| find_tables(lines) | imagem | 0 / 0 / 576 | — | 0,0% | 0,0% |
| find_tables(text) | tabela | 65 / 175 / 324 | 27,1% | 16,7% | 20,7% |
| find_tables(text) | imagem | 0 / 0 / 576 | — | 0,0% | 0,0% |
| Agrupamento de traços/retângulos | tabela | 143 / 92 / 246 | 60,9% | 36,8% | 45,8% |
| Agrupamento de traços/retângulos | imagem | 0 / 0 / 576 | — | 0,0% | 0,0% |
| Imagens incorporadas | tabela | 0 / 0 / 389 | — | 0,0% | 0,0% |
| Imagens incorporadas | imagem | 185 / 411 / 391 | 31,0% | 32,1% | 31,6% |
| Desenhos vetoriais grandes | tabela | 0 / 0 / 389 | — | 0,0% | 0,0% |
| Desenhos vetoriais grandes | imagem | 15 / 144 / 561 | 9,4% | 2,6% | 4,1% |
| PyMuPDF conservador | tabela | 192 / 96 / 197 | 66,7% | 49,4% | 56,7% |
| PyMuPDF conservador | imagem | 199 / 540 / 377 | 26,9% | 34,5% | 30,3% |
| PyMuPDF conservador + text | tabela | 204 / 191 / 185 | 51,6% | 52,4% | 52,0% |
| PyMuPDF conservador + text | imagem | 199 / 540 / 377 | 26,9% | 34,5% | 30,3% |

Páginas com palavras cuja confirmação por transcrição ficou inconclusiva:

| Página | Índice zero | F1 espacial | Escala x / y, px/pt | Vizinha melhor |
|---|---:|---:|---:|---|
| `0331_SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24_p0011/0331_SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24_p0011.pdf#p1` | 0 | 0,467 | 2,0834 / 2,0839 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p115` | 114 | 0,488 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p128` | 127 | 0,065 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p129` | 128 | 0,069 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p131` | 130 | 0,154 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p135` | 134 | 0,070 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p137` | 136 | 0,083 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p138` | 137 | 0,102 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p140` | 139 | 0,082 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p143` | 142 | 0,380 | 2,7785 / 2,7783 | False |
| `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146/SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf#p82` | 81 | 0,141 | 2,7785 / 2,7783 | False |
| `lote_20260717_151620/SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213/SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213.pdf#p111` | 110 | 0,000 | 2,7788 / 2,7781 | False |
| `lote_20260717_151620/SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213/SAO_PAULO_ABRIL_2026+-+sp_santos+-+2026-04-01-NORMAL-Ed0-Pag213.pdf#p159` | 158 | — | 2,7788 / 2,7781 | False |

Subconjunto com página/escala confirmadas por texto (seleção favorece PDFs de transcrição fácil):

| Método | Classe | TP / FP / FN | Precisão | Revocação | F1 |
|---|---|---:|---:|---:|---:|
| PyMuPDF conservador | tabela | 192 / 96 / 184 | 66,7% | 51,1% | 57,8% |
| PyMuPDF conservador | imagem | 196 / 523 / 322 | 27,3% | 37,8% | 31,7% |
| PyMuPDF conservador + text | tabela | 204 / 188 / 172 | 52,0% | 54,3% | 53,1% |
| PyMuPDF conservador + text | imagem | 196 / 523 / 322 | 27,3% | 37,8% | 31,7% |

Sem camada textual: diagnóstico de regiões, fora do domínio do pipeline de palavras. Uma imagem de página inteira não é equivalente a todas as figuras/tabelas internas:

| Método | Classe | TP / FP / FN | Precisão | Revocação | F1 |
|---|---|---:|---:|---:|---:|
| PyMuPDF conservador | tabela | 0 / 0 / 7 | — | 0,0% | 0,0% |
| PyMuPDF conservador | imagem | 6 / 12 / 6 | 33,3% | 50,0% | 40,0% |
| PyMuPDF conservador + text | tabela | 0 / 0 / 7 | — | 0,0% | 0,0% |
| PyMuPDF conservador + text | imagem | 6 / 12 / 6 | 33,3% | 50,0% | 40,0% |

## Efeito na ordem — principal: palavras na saída real

Mesmas palavras/IDs congelados do Diamond em todos os braços: muda apenas a origem dos átomos. Isso isola a detecção e não mede a mudança de tokenização do extrator; o tempo fim a fim, por sua vez, extrai as palavras de cada biblioteca ao vivo. Nenhum ID de segmentação diferente é comparado diretamente.
Configurações LOPO por página lidas do JSON do relatório original, sem nova seleção: {'projecao_local_margens_s0.45_g1.2_v0.08': 42, 'projecao_local_s0.45_g1.2_v0.20': 2}. A política permanece desligada nas páginas em que o LOPO original assim escolheu; a baseline justa recebe topo/marcas/rodapé do método com os mesmos limiares fixos, em todas as caixas de referência.
XY-cut ouro pura e XY-cut ouro com margens são oráculos de segmentação (†), não pipelines disponíveis sem anotação. Precedência: marcas pela mesma regex primeiro; topo centro < sete por cento e base < dez por cento; rodapé centro > noventa e cinco por cento. Emissão: topo, corpo, marcas, rodapé. A linha justa não usa classe humana para decidir margem.
Ouro de palavras = regiões na sequência humana, palavras internas por linhas geométricas. A ordem interna de tabela não foi anotada independentemente. Sucessor de palavras é inflado por pares dentro das regiões; fragmentação estrita conta qualquer interrupção por palavra de outra região ou sem ouro. Régua com menos de dois itens retorna ausência de medida.

| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |
|---|---:|---:|---:|---:|
| XY-cut ouro, pura† | 0,853 [0,776; 0,923] | 98,4% [97,8; 99,0] | 0,072 [0,038; 0,110] | 0,0% |
| XY-cut ouro + mesmas margens† | 0,972 [0,939; 0,992] | 99,2% [98,6; 99,6] | 0,013 [0,004; 0,027] | 0,0% |
| Plano LOPO + átomos Docling | 0,946 [0,886; 0,988] | 97,8% [96,0; 99,3] | 0,027 [0,006; 0,057] | 3,6% |
| Plano LOPO + PyMuPDF conservador | 0,967 [0,933; 0,991] | 96,7% [92,2; 99,2] | 0,014 [0,004; 0,027] | 2,6% |
| Plano LOPO + PyMuPDF incluindo text | 0,829 [0,749; 0,897] | 94,6% [90,9; 97,0] | 0,079 [0,048; 0,114] | 18,4% |
| Plano LOPO sem átomos | 0,917 [0,848; 0,970] | 91,2% [84,3; 96,4] | 0,035 [0,014; 0,061] | 6,5% |

| Origem de átomos | Átomos aceitos (soma) | Sem palavras (soma) |
|---|---:|---:|
| docling | 126 | 74 |
| rapido | 142 | 71 |
| rapido_text | 112 | 28 |
| nenhum | 0 | 0 |

Diagnóstico do pipeline realmente puro, extraindo words ao vivo: 35784/36171 palavras-ouro pareadas exatamente por texto/centro (98,9%). Nas palavras comuns, τ macro 0,920 [0,877; 0,961] (IC por veículo, condicional ao matching/configurações). Faltantes do ouro: 387; palavras MuPDF sem par: 568. Este τ em suporte comum exclui erros de tokenização e pode ser otimista; não é comparável diretamente à tabela controlada acima e não demonstra identidade fim a fim. A alteração das alturas/fragmentação das palavras também muda a geometria dos vales; detectar as mesmas tabelas não assegura a mesma ordem ao trocar o parser.

| Página: maiores perdas ao trocar também as palavras | τ com palavras congeladas | τ words MuPDF, comuns | Palavras comuns / ouro |
|---|---:|---:|---:|
| `official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf#p35` | 0,995 | 0,508 | 794 / 794 |
| `official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf#p0` | 1,000 | 0,527 | 1368 / 1368 |
| `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 0,968 | 0,579 | 778 / 778 |
| `official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p59` | 1,000 | 0,629 | 790 / 796 |
| `official_diary_ac/executive_official_diary_2025-02-11.pdf#p114` | 0,926 | 0,570 | 1130 / 1196 |

Há perdas de ordem mesmo em páginas com todas as palavras pareadas: igualdade do inventário textual não basta para preservar agrupamento de linhas e calhas. Não se recalibrou o limiar de vão pela altura nova da fonte, pois o protocolo exige congelar o LOPO.


Regiões sem palavras contadas: 0; páginas sem palavras: 0. Palavras sem região-ouro: 24. Fallback de região vazia por vizinho geométrico é somente secundário; páginas vazias não recebem nota perfeita.

| Comparação pareada (A − B) | Métrica | Diferença [IC 95% por veículo] | p Pratt bruto | n / empates |
|---|---|---:|---:|---:|
| rapido − docling | palavras/tau | 0,021 [-0,016; 0,080] | 0,86221 (Holm 1,00000) | 44 / 27 |
| rapido − docling | palavras/sucessor | -1,108 [-4,265; 1,011] | 0,42264 (Holm 1,00000) | 44 / 28 |
| rapido − docling | palavras/ard | -0,013 [-0,042; 0,004] | 0,87271 (Holm 1,00000) | 44 / 27 |
| rapido − docling | regioes/tau | 0,017 [-0,017; 0,058] | 0,71105 (Holm 1,00000) | 44 / 31 |
| rapido − docling | regioes/sucessor | 4,742 [-1,827; 12,411] | 0,21785 (Holm 1,00000) | 44 / 32 |
| rapido − docling | regioes/ard | -0,006 [-0,022; 0,007] | 0,71105 (Holm 1,00000) | 44 / 31 |
| rapido − docling | linhas/tau | 0,024 [-0,010; 0,082] | 0,79760 (Holm 1,00000) | 44 / 29 |
| rapido − docling | linhas/sucessor | 0,581 [-1,448; 3,247] | 0,08947 (Holm 1,00000) | 44 / 29 |
| rapido − docling | linhas/ard | -0,012 [-0,041; 0,005] | 0,96748 (Holm 1,00000) | 44 / 28 |
| rapido − nenhum | palavras/tau | 0,050 [0,013; 0,099] | 0,00102 (Holm 0,03475) | 44 / 27 |
| rapido − nenhum | palavras/sucessor | 5,446 [2,035; 9,700] | 0,00107 (Holm 0,03536) | 44 / 27 |
| rapido − nenhum | palavras/ard | -0,021 [-0,039; -0,006] | 0,00035 (Holm 0,01264) | 44 / 28 |
| rapido − nenhum | regioes/tau | 0,035 [-0,003; 0,081] | 0,24225 (Holm 1,00000) | 44 / 37 |
| rapido − nenhum | regioes/sucessor | 5,675 [0,673; 11,230] | 0,01439 (Holm 0,41719) | 44 / 38 |
| rapido − nenhum | regioes/ard | -0,012 [-0,029; 0,003] | 0,24225 (Holm 1,00000) | 44 / 37 |
| rapido − nenhum | linhas/tau | 0,031 [-0,001; 0,071] | 0,00454 (Holm 0,14079) | 44 / 32 |
| rapido − nenhum | linhas/sucessor | 4,941 [1,249; 9,720] | 0,00095 (Holm 0,03315) | 44 / 33 |
| rapido − nenhum | linhas/ard | -0,012 [-0,028; 0,000] | 0,00454 (Holm 0,14079) | 44 / 32 |
| rapido − xy_margens | palavras/tau | -0,005 [-0,045; 0,037] | 0,09067 (Holm 1,00000) | 44 / 17 |
| rapido − xy_margens | palavras/sucessor | -2,494 [-6,926; -0,085] | 0,00154 (Holm 0,04918) | 44 / 18 |
| rapido − xy_margens | palavras/ard | 0,001 [-0,015; 0,017] | 0,12846 (Holm 1,00000) | 44 / 18 |
| rapido − xy_margens | regioes/tau | 0,026 [-0,014; 0,071] | 0,57655 (Holm 1,00000) | 44 / 26 |
| rapido − xy_margens | regioes/sucessor | 4,919 [0,522; 10,327] | 0,19073 (Holm 1,00000) | 44 / 27 |
| rapido − xy_margens | regioes/ard | -0,005 [-0,023; 0,010] | 0,79225 (Holm 1,00000) | 44 / 29 |
| rapido − xy_margens | linhas/tau | 0,009 [-0,013; 0,039] | 0,41744 (Holm 1,00000) | 44 / 20 |
| rapido − xy_margens | linhas/sucessor | -1,606 [-3,949; 0,673] | 0,02085 (Holm 0,58390) | 44 / 21 |
| rapido − xy_margens | linhas/ard | -0,003 [-0,016; 0,006] | 0,52344 (Holm 1,00000) | 44 / 21 |
| rapido_text − rapido | palavras/tau | -0,138 [-0,225; -0,059] | 0,03355 (Holm 0,77161) | 44 / 20 |
| rapido_text − rapido | palavras/sucessor | -2,067 [-7,303; 3,700] | 0,02085 (Holm 0,58390) | 44 / 21 |
| rapido_text − rapido | palavras/ard | 0,065 [0,032; 0,101] | 0,04409 (Holm 0,96987) | 44 / 21 |
| rapido_text − rapido | regioes/tau | -0,134 [-0,213; -0,059] | 0,02398 (Holm 0,59962) | 44 / 22 |
| rapido_text − rapido | regioes/sucessor | -18,422 [-30,789; -6,046] | 0,02247 (Holm 0,58413) | 44 / 22 |
| rapido_text − rapido | regioes/ard | 0,060 [0,028; 0,094] | 0,05032 (Holm 1,00000) | 44 / 22 |
| rapido_text − rapido | linhas/tau | -0,145 [-0,223; -0,079] | 0,07542 (Holm 1,00000) | 44 / 21 |
| rapido_text − rapido | linhas/sucessor | -24,299 [-38,162; -12,277] | 0,03159 (Holm 0,75815) | 44 / 21 |
| rapido_text − rapido | linhas/ard | 0,067 [0,038; 0,101] | 0,07341 (Holm 1,00000) | 44 / 21 |

Holm considera conjuntamente as comparações/métricas/réguas desta tabela; não corrige toda a história exploratória anterior. p sem significância não demonstra equivalência ou não inferioridade. Sucessor em pontos percentuais nesta tabela; ARD menor é melhor.

## Estratos de colunas detectadas, sem usar ouro

Uma coluna: 20 páginas; critério fixo de calhas da reanálise justa, não anotação visual independente.

| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |
|---|---:|---:|---:|---:|
| XY-cut ouro, pura† | 0,951 [0,837; 0,999] | 98,9% [98,0; 99,6] | 0,024 [0,000; 0,081] | 0,0% |
| XY-cut ouro + mesmas margens† | 0,993 [0,983; 1,000] | 98,8% [97,9; 99,6] | 0,003 [0,000; 0,008] | 0,0% |
| Plano LOPO + átomos Docling | 0,994 [0,986; 1,000] | 98,6% [97,1; 99,6] | 0,003 [0,000; 0,006] | 2,2% |
| Plano LOPO + PyMuPDF conservador | 0,993 [0,986; 0,999] | 97,9% [96,4; 99,2] | 0,003 [0,001; 0,007] | 2,8% |
| Plano LOPO + PyMuPDF incluindo text | 0,995 [0,991; 0,998] | 98,3% [97,5; 99,2] | 0,003 [0,001; 0,005] | 5,6% |
| Plano LOPO sem átomos | 0,925 [0,808; 0,996] | 92,6% [84,3; 97,8] | 0,030 [0,002; 0,074] | 3,8% |

Multicoluna: 24 páginas; critério fixo de calhas da reanálise justa, não anotação visual independente.

| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |
|---|---:|---:|---:|---:|
| XY-cut ouro, pura† | 0,770 [0,687; 0,856] | 98,0% [97,3; 98,8] | 0,113 [0,070; 0,153] | 0,0% |
| XY-cut ouro + mesmas margens† | 0,954 [0,897; 0,991] | 99,4% [99,0; 99,7] | 0,021 [0,005; 0,045] | 0,0% |
| Plano LOPO + átomos Docling | 0,906 [0,804; 0,982] | 97,1% [93,7; 99,4] | 0,047 [0,009; 0,098] | 4,8% |
| Plano LOPO + PyMuPDF conservador | 0,945 [0,879; 0,988] | 95,6% [86,7; 99,6] | 0,024 [0,006; 0,049] | 2,4% |
| Plano LOPO + PyMuPDF incluindo text | 0,692 [0,593; 0,783] | 91,5% [86,0; 95,4] | 0,142 [0,102; 0,183] | 29,1% |
| Plano LOPO sem átomos | 0,910 [0,841; 0,963] | 90,1% [80,4; 96,9] | 0,039 [0,017; 0,065] | 8,8% |

## Réguas secundárias: mediana de ranks

As duas tabelas abaixo preservam comparabilidade histórica. A mediana pode esconder intercalação de texto; não é o veredito principal.

Regioes:

| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |
|---|---:|---:|---:|---:|
| XY-cut ouro, pura† | 0,825 [0,758; 0,889] | 71,5% [62,3; 80,5] | 0,083 [0,052; 0,115] | 0,0% |
| XY-cut ouro + mesmas margens† | 0,908 [0,856; 0,956] | 82,0% [74,1; 89,3] | 0,034 [0,018; 0,052] | 0,0% |
| Plano LOPO + átomos Docling | 0,917 [0,868; 0,963] | 82,1% [74,2; 89,4] | 0,035 [0,016; 0,055] | 3,6% |
| Plano LOPO + PyMuPDF conservador | 0,934 [0,896; 0,969] | 86,9% [81,4; 91,9] | 0,029 [0,014; 0,045] | 2,6% |
| Plano LOPO + PyMuPDF incluindo text | 0,800 [0,724; 0,873] | 68,5% [57,4; 79,1] | 0,089 [0,057; 0,122] | 18,4% |
| Plano LOPO sem átomos | 0,898 [0,845; 0,949] | 81,2% [74,5; 87,9] | 0,041 [0,022; 0,060] | 6,5% |

Linhas:

| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |
|---|---:|---:|---:|---:|
| XY-cut ouro, pura† | 0,848 [0,775; 0,916] | 88,6% [84,5; 92,7] | 0,074 [0,041; 0,110] | 0,0% |
| XY-cut ouro + mesmas margens† | 0,960 [0,926; 0,986] | 94,3% [90,9; 97,0] | 0,018 [0,007; 0,032] | 0,0% |
| Plano LOPO + átomos Docling | 0,945 [0,886; 0,986] | 92,1% [87,0; 96,0] | 0,026 [0,007; 0,055] | 3,6% |
| Plano LOPO + PyMuPDF conservador | 0,969 [0,952; 0,985] | 92,7% [87,6; 96,2] | 0,014 [0,007; 0,022] | 2,6% |
| Plano LOPO + PyMuPDF incluindo text | 0,824 [0,746; 0,891] | 68,4% [56,2; 79,3] | 0,081 [0,051; 0,116] | 18,4% |
| Plano LOPO sem átomos | 0,938 [0,896; 0,973] | 87,8% [81,4; 93,4] | 0,027 [0,012; 0,044] | 6,5% |

## Tempo fim a fim por página

Threads Torch = 2; CPU, modelo Docling local em eval/no_grad, renderização original do projeto na resolução de src/data/layout.py. Ambos os pipelines executam a mesma ordenação congelada em suas próprias palavras e regiões; tabela text é ablação adicional. Modelo é aquecido uma vez; carregamento fica separado. Abertura é por página, sem amortizar entre páginas do mesmo PDF. Cache de disco do sistema está aquecido; ordem de medição é fixa e há carga concorrente nesta máquina.

| Pipeline CPU | n | Média s/pág. | Mediana | p95 | pág./s |
|---|---:|---:|---:|---:|---:|
| pdfplumber + renderização + Docling + ordem | 44 | 4,389 | 3,075 | 9,740 | 0,23 |
| PyMuPDF conservador + ordem | 44 | 0,541 | 0,258 | 1,690 | 1,85 |
| PyMuPDF com text + ordem | 44 | 1,271 | 0,783 | 3,271 | 0,79 |

Aceleração pareada conservador: 8,1×. Vazão é n/soma dos tempos, não média de inversos. O tempo não vem da comparação antiga de palavras nem de um cache de GPU.
| Etapa | pdfplumber + Docling, média s | PyMuPDF conservador, média s |
|---|---:|---:|
| Abertura + palavras | 2,601 | 0,033 |
| Renderização | 0,080 | — |
| Regiões | 1,697 | 0,501 |
| Ordem | 0,009 | 0,007 |

Carga do Docling CPU: 8,426 s (fora das latências aquecidas).

Cauda lenta do caminho geométrico (sem descartar páginas):

| Página | PyMuPDF total, s | Palavras, s | Regiões, s | Docling total, s |
|---|---:|---:|---:|---:|
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 7,119 | 0,066 | 7,021 | 15,509 |
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 2,115 | 0,025 | 2,083 | 7,961 |
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | 1,832 | 0,058 | 1,737 | 39,932 |
| `official_diary_ba_salvador/dom-8379-27-09-2022.pdf#p5` | 0,884 | 0,022 | 0,856 | 3,584 |
| `official_diary_sc/2023-11-27_22151.pdf#p28` | 0,863 | 0,070 | 0,778 | 10,054 |

Remover rede não torna find_tables/clustering custo constante: páginas com muitos objetos vetoriais continuam lentas. O ganho de palavras isoladas não deve ser anunciado como aceleração fim a fim. Um orçamento de tempo para análise geométrica seria hipótese futura; não se interromperam páginas para favorecer a medição.

Falhas internas de estratégias geométricas contadas: 0 no Golden e 0 no LS. Páginas com avisos de sintaxe/reparo MuPDF: 18 no Golden e 80 no LS. Os candidatos das outras estratégias permanecem disponíveis; falha não é ausência de tabela.

## Análise de erro com exemplos

Exemplos escolhidos deterministicamente por falha e diferença de τ, sem ajustar regras depois de vê-los. Bbox em pontos no Diamond e pixels no LS; caches conservam candidatos, pares, falsos positivos e falsos negativos.

- Diamond `official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31`: tabela TP/FP/FN 0/0/0; imagem 0/4/6; primeira caixa perdida: [218.5, 101.6, 277.7, 161.5].
- Diamond `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44`: tabela TP/FP/FN 0/0/4; imagem 1/0/0; primeira caixa perdida: [63.6, 128.6, 215.7, 446.8].
- Diamond `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233`: tabela TP/FP/FN 0/0/1; imagem 0/2/2; primeira caixa perdida: [43.1, 35.7, 471.8, 779.1].
- Diamond `official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2`: tabela TP/FP/FN 0/0/0; imagem 3/0/2; primeira caixa perdida: [259.4, 745.3, 387.9, 778.4].
- LS `lote_20260717_151620/2026-05-01-NORMAL-Pag99-MG/2026-05-01-NORMAL-Pag99-MG.pdf#p5`: tabela TP/FP/FN 2/5/21; imagem 0/1/0; primeira caixa perdida: [166.8, 306.8, 1145.5, 368.4].
- LS `lote_20260715_100540/SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24/SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24.pdf#p7`: tabela TP/FP/FN 0/0/13; imagem 1/5/6; primeira caixa perdida: [1561.9, 1099.3, 1904.4, 1366.0].
- LS `0331_SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24_p0011/0331_SAO_PAULO_ABRIL_2026+-+sp_tapirai+-+2026-04-13-NORMAL-Ed1323-Pag24_p0011.pdf#p1`: tabela TP/FP/FN 0/0/1; imagem 1/5/17; primeira caixa perdida: [310.9, 1704.6, 913.6, 1894.6].
- LS `lote_20260715_100540/2026-04-17-NORMAL-Ed7482-Pag69_Belo_Horizonte/2026-04-17-NORMAL-Ed7482-Pag69_Belo_Horizonte.pdf#p51`: tabela TP/FP/FN 0/3/8; imagem 1/5/9; primeira caixa perdida: [1332.2, 532.0, 1931.6, 770.9].

Maiores perdas/ganhos de τ de palavras ao trocar Docling por PyMuPDF:

| Página | τ Docling | τ PyMuPDF | Δ | Fragmentação PyMuPDF |
|---|---:|---:|---:|---:|
| `official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233` | 0,608 | 0,320 | -0,288 | 0,0% |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44` | 0,892 | 0,768 | -0,124 | 9,5% |
| `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | 0,987 | 0,968 | -0,018 | 0,0% |
| `official_diary_ce/do20220530p02.pdf#p53` | 1,000 | 0,987 | -0,013 | 5,6% |
| `official_diary_pi_v2/executive_official_diary_2024_01_12_9_2024_243_297.pdf#p0` | 0,999 | 1,000 | 0,001 | 0,0% |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` | 0,978 | 1,000 | 0,022 | 0,0% |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26` | 0,483 | 0,854 | 0,371 | 0,0% |
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | 0,021 | 1,000 | 0,979 | 0,0% |

Mecanismos esperados e verificáveis nos caches: lines perde tabelas sem traços; text confunde colunas/listas alinhadas com uma tabela ampla; retângulos de fundo e títulos com moldura criam falsos positivos; imagens incorporadas podem ser fragmentos, máscara ou página inteira, enquanto uma figura humana reúne vários objetos; vetores não distinguem automaticamente rubrica, brasão, gráfico e ornamento. A caixa de um objeto PDF não é necessariamente a região semântica humana.

Inspeção visual em memória do PDF MS `executive_official_diary_48733_2024-11-05.pdf#p233`: a grande região humana reúne dados tabulares sem grade; o conservador deixa as palavras livres e o perfil passa a tratá-las como colunas de texto. Os rasters de cabeçalho/rodapé aparecem como candidatos a imagem. É um exemplo concreto em que 'não encontrou tabela' não autoriza dispensar o detector.

## Limitações e recomendação de desenho

Amostra pequena do Golden e poucos exemplos de algumas classes; páginas de um mesmo veículo são dependentes. O Diamond e o Label Studio foram anotados corrigindo pré-anotação, com viés de ancoragem: a comparação pode favorecer caixas já propostas, e não é um teste independente de validade humana. Algoritmo original foi desenvolvido no Golden; LOPO antigo não apaga esse viés nem garante generalização por veículo.
A régua principal isola a troca de átomos sobre palavras pdfplumber congeladas; não autoriza regenerar silver/Golden com get_text(words), cuja tokenização e altura diferem. Linhas internas de tabela são uma convenção geométrica, sem ouro independente de células. O LS não traz ordem humana neste experimento: é ouro de detecção, não de leitura. Figuras sem palavras entram na detecção, mas não produzem palavras para medir ordem.
PDF digital não garante texto legível; também há texto invisível/OCR, fontes quebradas, CropBox não trivial e rotação. PDFs digitalizados exigem OCR e detecção visual para estrutura interna. Imagem de página inteira não substitui detecção de tabelas/imagens. Falhas e páginas/regiões sem palavras são contadas, sem assert ou descarte silencioso.
PyMuPDF tem licenciamento AGPL ou comercial; avaliar compatibilidade antes de distribuir serviço ou código integrado. [Licença oficial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright). Esta análise não dá parecer jurídico. O material Data Policy permanece interno sob resultados/, sem cópia externa/publicação.
Desenho recomendado: extrair palavras e objetos digitais primeiro; usar tabelas de grade e imagens incorporadas como candidatos rápidos; sinalizar texto ausente/ilegível, raster de página inteira, geometria contraditória, excesso de candidatos text ou evidência de alinhamentos sem grade para fallback ao detector (e OCR quando necessário). A regra 'não achou nada' sozinha é insuficiente: nenhuma tabela pode significar página textual correta ou falso negativo. Limiares de fallback precisam de validação independente e não foram ajustados neste estudo.
Não é proposto um pipeline híbrido com número estimado: a recomendação é desenho futuro. Adotar o caminho rápido para palavras é uma decisão separada de retirar o detector de tabela/imagem; exigiria validar segmentação e referência. Não se editou qualquer arquivo preexistente, dado humano, quadro ou pipeline.

## Reprodução e conferência

```powershell
venv/Scripts/python.exe -B orquestracao/analises/caminho_rapido_pymupdf.py --do-zero
venv/Scripts/python.exe -B orquestracao/analises/caminho_rapido_pymupdf.py --conferir
```

Controle sintético: {'pagina_vazia': True, 'regiao_vazia': True, 'matching_um_a_um': True, 'cropbox_com_rotacoes': [0, 90, 180, 270], 'intercalacao_penalizada': True}. Comparação com execução anterior sem cache: OK: qualidade, ordem e auditorias idênticas à execução anterior; tempos medidos novamente.. Tempos naturalmente variam; a conferência exige identidade dos resultados de qualidade/ordem/alinhamento e reconstrói o Markdown dos resultados desta execução.
Hash do script: `86d2bc36696ea1319082d63cd2cb88a381390e8cc6e6a4abfc9df68e6331bcb2`. Hashes de entradas e métricas por página em `resultados/caminho_rapido_pymupdf_cache/estado.json`; caches são internos e retomáveis. Relatório gerado integralmente pelo script.
