# T14 — Paridade do extrator opcional PyMuPDF

Execução: `resultados/extrator_pymupdf_cache/20261003_080859_18c43f6f`; iniciada em 2026-10-03 08:08:59.
CPU, Windows-10-10.0.26200-SP0, Python 3.11.9, pdfplumber 0.11.10, PyMuPDF 1.28.2. Estado: 104/104 páginas processadas, 0 erros. Do zero: True.

## Resumo em cinco linhas

1. **Veredito: NAO pode virar o padrao como substituicao transparente: blocos e/ou silver divergem.**
2. Blocos idênticos (texto exato e IoU ≥ 0,95): 3003/3212 (93,49%); segmentação inteira igual em 61/104 páginas.
3. Splits detectados por palavras comuns: 11; fusões: 10; τ médio stream nos blocos casados: 1,000.
4. A referência silver inteira é preservada em 61/104 páginas; τ de palavras em fluxo (trace): 1,000. Não regenerar a silver com este módulo quando houver qualquer divergência.
5. Ponta a ponta: pdfplumber 2,585 s/página e PyMuPDF 0,078 s/página; aceleração 33,31×, com layout já em cache e sem GPU.

## Tabela principal

| Amostra | Páginas | Blocos PP / Mu | Blocos idênticos / PP | Páginas iguais | Partidos / fundidos | τ stream | τ naive | τ xycut | PP s/pág | Mu s/pág | Ganho |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bancada44 | 44 | 1451 / 1445 | 90,90% | 28 | 8 / 6 | 1,000 | 1,000 | 0,997 | 2,412 | 0,079 | 30,64× |
| extras60 | 60 | 1761 / 1750 | 95,63% | 33 | 3 / 4 | 1,000 | 0,994 | 0,994 | 2,713 | 0,077 | 35,31× |
| total | 104 | 3212 / 3195 | 93,49% | 61 | 11 / 10 | 1,000 | 0,997 | 0,996 | 2,585 | 0,078 | 33,31× |

Fração inversa de blocos idênticos / Mu: 93,99%. Médias de blocos/página: PP 30,88, Mu 30,72. “Página igual” exige bijeção completa dos blocos com o critério acima; não exige igualdade de bytes nem dos IDs aleatórios.

## Tempos e vazão

| Etapa | PP média s/pág | Mu média s/pág |
|---|---:|---:|
| abertura | 0,0033 | 0,0011 |
| acesso_pagina | 0,0336 | 0,0010 |
| palavras | 2,5383 | 0,0655 |
| segmentar | 0,0100 | 0,0100 |
| palavras_segmentar | 2,5483 | 0,0755 |
| total | 2,5853 | 0,0776 |

Vazão serial total: PP 0,39 páginas/s; Mu 12,88 páginas/s. “total” = abertura + acesso à página + palavras + segmentar. O PDF é reaberto por página, sem cache quente de objetos entre páginas; o acesso do pdfplumber inclui a enumeração das páginas. Pareamento, análise, testes, escrita de cache e leitura de layout ficam fora. Detecção/renderização de layout não foi repetida: estas não são latências do pipeline visual completo.

## Protocolo, identidades e ordem de fluxo

Bancada: 40 páginas de `blocos_v1`, seed 42, veículos `teste + ufs_nao_confiaveis`, mais as 4 páginas-problema, usando as funções originais. Extras: 60 páginas de `blocos`, sem sobreposição com a bancada, seed 20261003, sorteio em rodadas por veículo. O manifesto guarda os identificadores, tabelas e assinaturas. Nenhuma página é descartada pelo filtro de número de blocos. São usadas apenas tabelas já disponíveis em `data/processed/layout`; a mesma lista entra nos dois caminhos, sem gerar ou modificar o cache de layout.

Os pares são bijetivos por cardinalidade máxima em um grafo de texto EXATO e IoU. τ de blocos usa exclusivamente pares com IoU ≥ 0,95; IDs de um caminho não são comparados diretamente com IDs do outro. τ é macro por página, com exclusão de páginas com menos de dois pares. Palavras usam IoU ≥ 0,7. Splits/fusões são inferidos quando palavras casadas de um bloco pertencem a vários no outro; são evidência conservadora, não contagem exaustiva. Um split seguido de fusão pode entrar nas duas contagens.

Páginas com τ de blocos calculável: `{'stream': 103, 'naive': 103, 'xycut': 103}`. Blocos stream com ordem igual só no subconjunto: 103/104; ordem e universo completos iguais: 61/104. Uma correlação alta em pares sobreviventes não demonstra equivalência da referência silver.

Palavras PP / Mu: 110921 / 110894; casadas: 107571 (96,98% / 97,00%). τ macro do fluxo de palavras PP × trace: 1,000000; PP × `words(sort=False)`: 1,000000.

`words(sort=False)` não faz a ordenação geométrica opcional, mas deriva de TextPage, que agrupa caracteres em linhas/blocos. O módulo usa `get_texttrace()` e `seqno`, sem reagrupamento do TextPage ou espaços inventados. A sequência de desenho é uma aproximação melhor do fluxo, porém os parsers podem decodificar caracteres e Form XObjects de maneira diferente. A medida acima testa a concordância, sem prometer identidade universal. [API get_text](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text), [API get_texttrace](https://pymupdf.readthedocs.io/en/latest/functions.html#Page.get_texttrace).

## Páginas que mudam e evidência da causa

G = intervenção que mantém todos os textos, índices de fluxo e tokens do PP, trocando só as coordenadas das palavras casadas pelas do Mu. G diferente do PP demonstra que a geometria é suficiente para mudar blocos. Palavras não casadas podem refletir decodificação, limites dos tokens, orientação ou geometria fora da tolerância; não se atribui tudo a uma “melhoria” do parser.

| Página (índice desde zero) | Blocos PP→Mu | Idênticos | Partidos/fundidos | Palavras sem par PP/Mu | Desvio máx. pt | Intervenção G: idênticos/PP, n blocos |
|---|---:|---:|---:|---:|---:|---:|
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2023-04-17_Boletim_7279.pdf#p13` | 57→57 | 56 | 0/0 | 3/3 | 0,559 | 57/57, 57 |
| `official_diary_al/DOEAL-2022-11-25-SUPLEMENTO_1_8.pdf#p0` | 19→19 | 18 | 0/0 | 3/3 | 1,322 | 19/19, 19 |
| `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p36` | 33→32 | 16 | 4/4 | 15/0 | 0,012 | 30/33, 33 |
| `official_diary_mg/executive_official_diary_2021-12-30.pdf#p54` | 102→103 | 101 | 1/0 | 0/0 | 0,959 | 101/102, 103 |
| `official_diary_pb/Diario Oficial 03-01-2024 Portal_24_28.pdf#p0` | 39→39 | 36 | 0/0 | 3/3 | 1,018 | 38/39, 39 |
| `official_diary_pb/Diario Oficial 04-08-2023_46_56.pdf#p0` | 29→29 | 28 | 0/0 | 0/0 | 1,018 | 28/29, 29 |
| `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12` | 128→125 | 124 | 0/0 | 26/26 | 0,001 | 128/128, 128 |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | 73→73 | 71 | 0/0 | 24/24 | 0,865 | 73/73, 73 |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | 41→38 | 35 | 0/1 | 39/24 | 0,457 | 39/41, 40 |
| `official_diary_rj_japeri/JAPERI-5746-27-DE-NOVEMBRO-2024.pdf#p1` | 46→46 | 45 | 0/0 | 0/0 | 0,486 | 45/46, 46 |
| `official_diary_rj_japeri/JAPERI-5772-10-DE-JANEIRO-2025.pdf#p59` | 10→3 | 2 | 0/0 | 34/0 | 0,486 | 9/10, 10 |
| `official_diary_se/DOE-SE_2026-01-09_7381.pdf#p2` | 116→116 | 57 | 0/0 | 0/0 | 2,058 | 57/116, 116 |
| `official_diary_sp/Executivo - Caderno 1_2023-06-28_7_71.pdf#p0` | 7→8 | 7 | 0/0 | 1769/1782 | 0,001 | 7/7, 7 |
| `official_diary_sp/Executivo - Caderno 3_2024-04-02.pdf#p4` | 51→57 | 28 | 3/1 | 1290/1303 | 1,647 | 37/51, 54 |
| `official_diary_to/2021-09-24_4463.pdf#p35` | 37→37 | 36 | 0/0 | 0/0 | 0,540 | 36/37, 37 |
| `official_diary_to/2021-09-24_4463.pdf#p40` | 25→25 | 21 | 0/0 | 0/0 | 1,247 | 21/25, 25 |
| `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p1` | 46→47 | 41 | 2/3 | 0/0 | 8,690 | 41/46, 47 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16` | 46→46 | 44 | 0/0 | 0/0 | 0,323 | 44/46, 46 |
| `official_diary_RJ_volta_redonda/executive_official_diary_2025-02-20_2173.pdf#p1` | 29→29 | 26 | 0/0 | 0/0 | 0,323 | 26/29, 29 |
| `official_diary_ac/executive_official_diary_2025-09-24.pdf#p216` | 12→13 | 4 | 1/0 | 0/0 | 0,812 | 4/12, 13 |
| `official_diary_al/DOEAL-2023-05-23-COMPLETO_54_136.pdf#p0` | 39→39 | 27 | 0/0 | 0/0 | 0,576 | 27/39, 39 |
| `official_diary_am_manaus/2023-04-14_caderno_2.pdf#p25` | 8→2 | 2 | 0/0 | 15/0 | 0,002 | 8/8, 8 |
| `official_diary_ba_salvador/dom-8762-11-04-2024.pdf#p22` | 58→58 | 57 | 0/0 | 0/0 | 1,572 | 57/58, 58 |
| `official_diary_ba_salvador/dom-8908-07-11-2024.pdf#p37` | 55→53 | 52 | 0/1 | 0/0 | 1,571 | 52/55, 53 |
| `official_diary_ms/executive_official_diary_48555_2024-07-08.pdf#p22` | 17→17 | 16 | 0/0 | 0/0 | 0,767 | 16/17, 17 |
| `official_diary_ms/executive_official_diary_48977_2025-03-27.pdf#p170` | 13→13 | 12 | 0/0 | 0/0 | 0,767 | 12/13, 13 |
| `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30` | 19→19 | 18 | 0/0 | 76/76 | 1,473 | 19/19, 19 |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p21` | 5→5 | 4 | 0/0 | 0/0 | 1,018 | 4/5, 5 |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p7` | 12→12 | 11 | 0/0 | 0/0 | 1,018 | 11/12, 12 |
| `official_diary_pe/2026-01-09_1-Poder Executivo.pdf#p2` | 83→83 | 82 | 0/0 | 1/1 | 0,338 | 83/83, 83 |
| `official_diary_pr/executive_official_diary_2021-12-06.pdf#p62` | 41→41 | 40 | 0/0 | 0/0 | 1,215 | 40/41, 41 |
| `official_diary_pr/executive_official_diary_2022-12-01.pdf#p91` | 53→53 | 52 | 0/0 | 0/0 | 1,215 | 52/53, 53 |
| `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18` | 31→28 | 27 | 0/0 | 26/26 | 0,002 | 31/31, 31 |
| `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p34` | 6→2 | 1 | 0/0 | 26/26 | 0,000 | 6/6, 6 |
| `official_diary_rj_japeri/JAPERI-5422-03-DE-AGOSTO-2023_12_28.pdf#p0` | 3→3 | 2 | 0/0 | 0/0 | 0,486 | 2/3, 3 |
| `official_diary_rj_japeri/JAPERI-5772-10-DE-JANEIRO-2025.pdf#p29` | 3→3 | 2 | 0/0 | 0/0 | 0,486 | 2/3, 3 |
| `official_diary_rr/2022-09-27_DiarioRR.pdf#p44` | 11→11 | 9 | 0/0 | 0/0 | 1,512 | 9/11, 11 |
| `official_diary_rr/2024-01-16_DiarioRR.pdf#p19` | 18→18 | 16 | 0/0 | 0/0 | 1,512 | 16/18, 18 |
| `official_diary_se/DOE-SE_2024-10-17_6324.pdf#p3` | 53→53 | 42 | 0/0 | 0/0 | 1,139 | 42/53, 53 |
| `official_diary_sp/Executivo - Caderno 3_2023-07-12_90_123.pdf#p0` | 12→13 | 12 | 0/0 | 0/13 | 0,001 | 12/12, 12 |
| `official_diary_sp/Executivo - Caderno 3_2024-04-02.pdf#p182` | 9→10 | 9 | 0/0 | 0/13 | 0,002 | 9/9, 9 |
| `official_diary_to/2021-11-18_4498.pdf#p31` | 49→49 | 48 | 0/0 | 0/0 | 0,675 | 48/49, 49 |
| `official_diary_to/2021-11-18_4498.pdf#p41` | 50→50 | 48 | 0/0 | 0/0 | 0,675 | 48/50, 50 |

- `official_diary_RJ_duque_de_caxias/executive_official_diary_2023-04-17_Boletim_7279.pdf#p13`: geometria isolada não altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 3/3; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “PUBLICADO” [224,22; 11,35; 250,36; 18,42]; vizinhas Mu: “PUBLICADO” [224,22; 13,14; 250,36; 17,81] / “W” [224,23; 22,15; 229,70; 29,23].
  - Bloco afetado PP 0, palavra PP “EM” [252,17; 11,35; 258,83; 18,42]; vizinhas Mu: “EM” [252,17; 13,14; 258,83; 17,81] / “BOLETIM” [260,66; 13,14; 280,41; 17,81].
  - Bloco afetado Mu 0: palavra sem par estrito “PUBLICADO” [224,22; 13,14; 250,36; 17,81]; vizinhas PP: “PUBLICADO” [224,22; 11,35; 250,36; 18,42] / “W” [224,23; 22,15; 229,70; 29,23].
  - Bloco afetado Mu 0: palavra sem par estrito “EM” [252,17; 13,14; 258,83; 17,81]; vizinhas PP: “EM” [252,17; 11,35; 258,83; 18,42] / “BOLETIM” [260,66; 11,35; 280,41; 18,42].

- `official_diary_al/DOEAL-2022-11-25-SUPLEMENTO_1_8.pdf#p0`: geometria isolada não altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 3/3; aproximações do módulo `{'componentes_ligadura_unidos': 3, 'caracteres_desduplicados': 48}`.
  - Bloco afetado PP 4, palavra PP “Poder” [116,19; 145,68; 247,39; 173,68]; vizinhas Mu: “Poder” [116,19; 137,31; 247,40; 177,31] / “Digitalmente” [124,55; 121,90; 166,32; 129,90].
  - Bloco afetado PP 4, palavra PP “Executivo” [261,07; 145,68; 479,11; 173,68]; vizinhas Mu: “Executivo” [261,07; 137,31; 479,09; 177,31] / “7.397/2012” [226,39; 121,90; 262,62; 129,90].
  - Bloco afetado Mu 4: palavra sem par estrito “Poder” [116,19; 137,31; 247,40; 177,31]; vizinhas PP: “Poder” [116,19; 145,68; 247,39; 173,68] / “Digitalmente” [124,55; 121,90; 166,32; 129,90].
  - Bloco afetado Mu 4: palavra sem par estrito “Executivo” [261,07; 137,31; 479,09; 177,31]; vizinhas PP: “Executivo” [261,07; 145,68; 479,11; 173,68] / “7.397/2012” [226,39; 121,90; 262,62; 129,90].
  - Controle unitário no bloco PP 4: trocar só a caixa de “Poder” [116,19; 145,68; 247,39; 173,68] por “Poder” [116,19; 137,31; 247,40; 177,31] produz 19 blocos, dos quais 18/19 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 4: trocar só a caixa de “Executivo” [261,07; 145,68; 479,11; 173,68] por “Executivo” [261,07; 137,31; 479,09; 177,31] produz 19 blocos, dos quais 18/19 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p36`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 15/0; aproximações do módulo `{'orientacao_aproximada': 17, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 21, palavra PP “S” [83,72; 584,27; 144,60; 645,15]; vizinhas Mu: “CIENTIFIQUE-SE,” [92,46; 533,94; 150,23; 542,46] / “Manaus,” [117,95; 553,44; 144,72; 561,96].
  - Bloco afetado PP 21, palavra PP “E” [109,25; 558,74; 170,13; 619,62]; vizinhas Mu: “Manaus,” [117,95; 553,44; 144,72; 561,96] / “CIENTIFIQUE-SE,” [92,46; 533,94; 150,23; 542,46].

- `official_diary_mg/executive_official_diary_2021-12-30.pdf#p54`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 550, 'caracteres_desduplicados': 1}`.
  - Bloco afetado PP 3, palavra PP “GErAiS” [727,02; 100,83; 757,69; 108,83]; vizinhas Mu: “GErAiS” [726,46; 100,83; 756,73; 108,83] / “miLitAr” [726,77; 90,58; 761,70; 98,58].
  - Bloco afetado PP 3, palavra PP “miNAS” [698,59; 100,83; 725,10; 108,83]; vizinhas Mu: “miNAS” [698,27; 100,83; 724,62; 108,83] / “DE” [685,40; 100,83; 696,43; 108,83].
  - Controle unitário no bloco PP 3: trocar só a caixa de “GErAiS” [727,02; 100,83; 757,69; 108,83] por “GErAiS” [726,46; 100,83; 756,73; 108,83] produz 103 blocos, dos quais 101/102 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pb/Diario Oficial 03-01-2024 Portal_24_28.pdf#p0`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 3/3; aproximações do módulo `{'caracteres_desduplicados': 1}`.
  - Bloco afetado PP 9, palavra PP “(cid:31)” [333,87; 236,96; 340,16; 244,96]; vizinhas Mu: “�” [333,87; 236,90; 340,16; 244,98] / “553” [327,69; 245,90; 340,14; 253,98].
  - Bloco afetado PP 9, palavra PP “(cid:31)” [136,19; 245,96; 142,48; 253,96]; vizinhas Mu: “�” [136,19; 245,90; 142,48; 253,98] / “VAAT” [144,59; 245,90; 165,58; 253,98].
  - Bloco afetado Mu 9: palavra sem par estrito “�” [333,87; 236,90; 340,16; 244,98]; vizinhas PP: “(cid:31)” [333,87; 236,96; 340,16; 244,96] / “553” [327,69; 245,96; 340,14; 253,96].
  - Bloco afetado Mu 9: palavra sem par estrito “�” [136,19; 245,90; 142,48; 253,98]; vizinhas PP: “(cid:31)” [136,19; 245,96; 142,48; 253,96] / “VAAT” [144,59; 245,96; 165,58; 253,96].
  - Controle unitário no bloco PP 0: trocar só a caixa de “Diário” [607,37; 3,96; 644,32; 16,96] por “Diário” [607,37; 2,95; 644,33; 17,25] produz 39 blocos, dos quais 38/39 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 0: trocar só a caixa de “Ofi” [646,47; 3,96; 664,55; 16,96] por “Ofi” [646,47; 2,95; 664,56; 17,25] produz 39 blocos, dos quais 38/39 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pb/Diario Oficial 04-08-2023_46_56.pdf#p0`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “Diário” [607,37; 3,96; 644,32; 16,96]; vizinhas Mu: “Diário” [607,37; 2,95; 644,33; 17,25] / “8.666/93” [606,78; 38,96; 635,00; 46,96].
  - Bloco afetado PP 0, palavra PP “Ofi” [646,47; 3,96; 664,55; 16,96]; vizinhas Mu: “Ofi” [646,47; 2,95; 664,56; 17,25] / “cial” [663,84; 2,95; 686,01; 17,25].
  - Controle unitário no bloco PP 0: trocar só a caixa de “Diário” [607,37; 3,96; 644,32; 16,96] por “Diário” [607,37; 2,95; 644,33; 17,25] produz 29 blocos, dos quais 28/29 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 0: trocar só a caixa de “Ofi” [646,47; 3,96; 664,55; 16,96] por “Ofi” [646,47; 2,95; 664,56; 17,25] produz 29 blocos, dos quais 28/29 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p12`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 26/26; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21]; vizinhas Mu: “��Á���” [342,96; 53,27; 393,28; 68,21] / “��” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado PP 2, palavra PP “(cid:1)(cid:2)(cid:3)(cid:4)(cid:5)” [52,44; 60,06; 79,45; 68,03]; vizinhas Mu: “�����” [52,44; 60,06; 79,45; 68,03] / “favor” [52,44; 86,15; 67,95; 93,12].
  - Bloco afetado Mu 0: palavra sem par estrito “��Á���” [342,96; 53,27; 393,28; 68,21]; vizinhas PP: “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21] / “(cid:1)(cid:4)” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado Mu 0: palavra sem par estrito “�������” [417,94; 53,36; 473,42; 68,30]; vizinhas PP: “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [417,94; 53,36; 473,42; 68,30] / “(cid:1)(cid:9)” [421,53; 69,28; 429,10; 75,26].

- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 24/24; aproximações do módulo `{'fonte_ambigua': 1316, 'caracteres_desduplicados': 1}`.
  - Bloco afetado PP 1, palavra PP “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [349,51; 52,30; 399,84; 67,24]; vizinhas Mu: “��Á���” [349,51; 52,30; 399,84; 67,24] / “��” [357,23; 67,81; 365,50; 73,79].
  - Bloco afetado PP 1, palavra PP “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [424,49; 52,38; 479,97; 67,32]; vizinhas Mu: “�������” [424,49; 52,38; 479,97; 67,32] / “��” [421,53; 67,81; 429,10; 73,79].
  - Bloco afetado Mu 1: palavra sem par estrito “��Á���” [349,51; 52,30; 399,84; 67,24]; vizinhas PP: “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [349,51; 52,30; 399,84; 67,24] / “(cid:1)(cid:4)” [357,23; 67,81; 365,50; 73,79].
  - Bloco afetado Mu 1: palavra sem par estrito “�������” [424,49; 52,38; 479,97; 67,32]; vizinhas PP: “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [424,49; 52,38; 479,97; 67,32] / “(cid:1)(cid:9)” [421,53; 67,81; 429,10; 73,79].

- `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 39/24; aproximações do módulo `{'orientacao_aproximada': 71, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [349,51; 52,30; 399,84; 67,24]; vizinhas Mu: “��Á���” [349,51; 52,30; 399,84; 67,24] / “��” [357,23; 67,81; 365,50; 73,79].
  - Bloco afetado PP 1, palavra PP “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [424,49; 52,38; 479,97; 67,32]; vizinhas Mu: “�������” [424,49; 52,38; 479,97; 67,32] / “��” [421,53; 67,81; 429,10; 73,79].
  - Bloco afetado Mu 1: palavra sem par estrito “��Á���” [349,51; 52,30; 399,84; 67,24]; vizinhas PP: “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [349,51; 52,30; 399,84; 67,24] / “(cid:1)(cid:4)” [357,23; 67,81; 365,50; 73,79].
  - Bloco afetado Mu 1: palavra sem par estrito “�������” [424,49; 52,38; 479,97; 67,32]; vizinhas PP: “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [424,49; 52,38; 479,97; 67,32] / “(cid:1)(cid:9)” [421,53; 67,81; 429,10; 73,79].
  - Controle unitário no bloco PP 34: trocar só a caixa de “www.rj.gov.br” [176,13; 473,96; 332,49; 494,99] por “www.rj.gov.br” [176,13; 473,74; 332,49; 495,03] produz 40 blocos, dos quais 39/41 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_rj_japeri/JAPERI-5746-27-DE-NOVEMBRO-2024.pdf#p1`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 1}`.
  - Bloco afetado PP 2, palavra PP “ANO” [33,17; 38,87; 49,31; 46,87]; vizinhas Mu: “ANO” [33,17; 39,35; 49,31; 46,63] / “XXII” [51,44; 39,35; 65,74; 46,63].
  - Bloco afetado PP 2, palavra PP “XXII” [51,44; 38,87; 65,74; 46,87]; vizinhas Mu: “XXII” [51,44; 39,35; 65,74; 46,63] / “-” [67,75; 39,35; 70,17; 46,63].

- `official_diary_rj_japeri/JAPERI-5772-10-DE-JANEIRO-2025.pdf#p59`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 34/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 3, palavra PP “A” [70,29; 83,18; 118,50; 141,89]; vizinhas Mu: “-” [77,66; 39,35; 80,09; 46,63] / “XXIII” [59,15; 39,35; 75,66; 46,63].
  - Bloco afetado PP 3, palavra PP “VOZ” [125,84; 83,18; 257,97; 141,89]; vizinhas Mu: “5.772” [117,36; 39,35; 135,28; 46,63] / “-” [137,16; 39,35; 139,59; 46,63].

- `official_diary_se/DOE-SE_2026-01-09_7381.pdf#p2`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'fonte_ambigua': 838, 'fonte_sem_descritor': 62, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 14, palavra PP “II” [658,78; 174,06; 663,97; 184,81]; vizinhas Mu: “II” [658,78; 176,12; 663,97; 183,90] / “-” [666,50; 176,12; 669,09; 183,90].
  - Bloco afetado PP 14, palavra PP “-” [666,50; 174,06; 669,09; 184,81]; vizinhas Mu: “-” [666,50; 176,12; 669,09; 183,90] / “o” [671,56; 176,12; 675,46; 183,90].

- `official_diary_sp/Executivo - Caderno 1_2023-06-28_7_71.pdf#p0`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 1769/1782; aproximações do módulo `{'fonte_sem_descritor': 221, 'caracteres_desduplicados': 2}`.
  - Bloco afetado Mu 6: palavra sem par estrito “A” [322,00; 1268,66; 330,00; 1280,66]; vizinhas PP: “AQUISIÇÃO” [336,69; 1215,22; 355,85; 1222,22] / “AQUISICAO” [336,69; 1207,44; 355,77; 1214,44].
  - Bloco afetado Mu 6: palavra sem par estrito “Companhia” [333,34; 1268,66; 394,70; 1280,66]; vizinhas PP: “AQUISIÇÃO” [336,69; 1215,22; 355,85; 1222,22] / “AQUISICAO” [336,69; 1207,44; 355,77; 1214,44].

- `official_diary_sp/Executivo - Caderno 3_2024-04-02.pdf#p4`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 1290/1303; aproximações do módulo `{'fonte_sem_descritor': 219, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 4, palavra PP “189” [39,68; 103,63; 46,74; 110,63]; vizinhas Mu: “189” [39,68; 105,27; 46,74; 110,17] / “190” [39,68; 113,33; 46,74; 118,23].
  - Bloco afetado PP 5, palavra PP “LETICIA” [76,69; 103,63; 90,94; 110,63]; vizinhas Mu: “LETICIA” [76,69; 105,27; 90,94; 110,17] / “KAYKY” [76,68; 113,33; 89,21; 118,23].
  - Bloco afetado Mu 4: palavra sem par estrito “189” [39,68; 105,27; 46,74; 110,17]; vizinhas PP: “189” [39,68; 103,63; 46,74; 110,63] / “190” [39,68; 111,68; 46,74; 118,68].
  - Bloco afetado Mu 5: palavra sem par estrito “LETICIA” [76,69; 105,27; 90,94; 110,17]; vizinhas PP: “LETICIA” [76,69; 103,63; 90,94; 110,63] / “KAYKY” [76,68; 111,68; 89,21; 118,68].

- `official_diary_to/2021-09-24_4463.pdf#p35`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 10, 'caracteres_desduplicados': 3}`.
  - Bloco afetado PP 1, palavra PP “ANO” [284,53; 29,73; 300,13; 37,73]; vizinhas Mu: “ANO” [284,53; 30,27; 300,13; 37,47] / “XXXIII” [302,13; 30,27; 322,54; 37,47].
  - Bloco afetado PP 1, palavra PP “XXXIII” [302,13; 29,73; 322,54; 37,73]; vizinhas Mu: “XXXIII” [302,13; 30,27; 322,54; 37,47] / “ANO” [284,53; 30,27; 300,13; 37,47].

- `official_diary_to/2021-09-24_4463.pdf#p40`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 4, 'caracteres_desduplicados': 7}`.
  - Bloco afetado PP 12, palavra PP “FIGUEIRÓPOLIS” [34,02; 337,90; 97,21; 346,90]; vizinhas Mu: “FIGUEIRÓPOLIS” [34,02; 339,15; 97,21; 346,35] / “Municipal” [34,01; 311,94; 67,80; 319,94].
  - Bloco afetado PP 17, palavra PP “LAGOA” [306,14; 543,61; 333,77; 552,61]; vizinhas Mu: “LAGOA” [306,14; 544,86; 333,76; 552,06] / “CÂMARA” [306,14; 570,52; 340,37; 578,52].
  - Controle unitário no bloco PP 12: trocar só a caixa de “FIGUEIRÓPOLIS” [34,02; 337,90; 97,21; 346,90] por “FIGUEIRÓPOLIS” [34,02; 339,15; 97,21; 346,35] produz 25 blocos, dos quais 24/25 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p1`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 14, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 43, palavra PP “BOS” [85,89; 828,48; 159,65; 879,02]; vizinhas Mu: “BOS” [85,89; 837,17; 159,67; 875,17] / “Procuradoria” [62,66; 802,01; 114,19; 811,01].
  - Bloco afetado PP 43, palavra PP “do” [165,55; 852,87; 178,16; 866,91]; vizinhas Mu: “do” [165,55; 855,20; 178,16; 865,88] / “Município” [180,83; 855,20; 230,03; 865,88].
  - Controle unitário no bloco PP 43: trocar só a caixa de “BOS” [85,89; 828,48; 159,65; 879,02] por “BOS” [85,89; 837,17; 159,67; 875,17] produz 47 blocos, dos quais 41/46 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf#p16`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 38, palavra PP “EDITAL” [403,80; 659,18; 431,16; 667,32]; vizinhas Mu: “EDITAL” [403,80; 659,51; 431,16; 667,24] / “CASTRO” [408,31; 670,11; 436,45; 677,03].
  - Bloco afetado PP 38, palavra PP “Nº” [433,87; 659,18; 442,29; 667,32]; vizinhas Mu: “Nº” [433,87; 659,51; 442,29; 667,24] / “463/2023–” [445,13; 659,51; 481,72; 667,24].

- `official_diary_RJ_volta_redonda/executive_official_diary_2025-02-20_2173.pdf#p1`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 21, palavra PP “DECRETO” [376,92; 509,42; 414,77; 517,56]; vizinhas Mu: “DECRETO” [376,92; 509,75; 414,77; 517,48] / “Sistema” [377,11; 518,79; 402,49; 525,71].
  - Bloco afetado PP 21, palavra PP “Nº” [417,06; 509,42; 425,47; 517,56]; vizinhas Mu: “Nº” [417,06; 509,75; 425,47; 517,48] / “19.074” [427,76; 509,75; 451,44; 517,48].

- `official_diary_ac/executive_official_diary_2025-09-24.pdf#p216`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 6, palavra PP “ORÇAMENTOS” [196,25; 98,06; 255,49; 107,53]; vizinhas Mu: “ORÇAMENTOS” [196,25; 98,87; 255,49; 107,14] / “JANEIRO” [185,46; 111,19; 221,28; 119,46].
  - Bloco afetado PP 6, palavra PP “FISCAL” [257,77; 98,06; 286,70; 107,53]; vizinhas Mu: “FISCAL” [257,77; 98,87; 286,70; 107,14] / “RECEITAS” [256,62; 86,97; 298,41; 95,25].

- `official_diary_al/DOEAL-2023-05-23-COMPLETO_54_136.pdf#p0`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 25, 'caracteres_desduplicados': 1}`.
  - Bloco afetado PP 25, palavra PP “RESOLVE:” [341,94; 496,07; 380,20; 503,28]; vizinhas Mu: “RESOLVE:” [341,94; 495,50; 380,20; 503,54] / “SEF” [340,29; 479,04; 354,09; 487,08].
  - Bloco afetado PP 23, palavra PP “ESCRITURAÇÃO” [336,43; 446,58; 397,94; 453,79]; vizinhas Mu: “ESCRITURAÇÃO” [336,43; 446,01; 397,94; 454,05] / “DE” [333,46; 437,72; 344,07; 445,76].
  - Controle unitário no bloco PP 25: trocar só a caixa de “RESOLVE:” [341,94; 496,07; 380,20; 503,28] por “RESOLVE:” [341,94; 495,50; 380,20; 503,54] produz 39 blocos, dos quais 38/39 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_am_manaus/2023-04-14_caderno_2.pdf#p25`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 15/0; aproximações do módulo `{'orientacao_aproximada': 17, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 5, palavra PP “S” [92,27; 577,74; 150,72; 636,18]; vizinhas Mu: “DOM” [200,46; 806,66; 222,59; 816,14] / “\|” [225,24; 806,66; 227,89; 816,14].
  - Bloco afetado PP 5, palavra PP “E” [116,78; 553,23; 175,23; 611,68]; vizinhas Mu: “DOM” [200,46; 806,66; 222,59; 816,14] / “\|” [225,24; 806,66; 227,89; 816,14].

- `official_diary_ba_salvador/dom-8762-11-04-2024.pdf#p22`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “23” [543,61; 46,01; 571,96; 79,85]; vizinhas Mu: “23” [543,61; 47,59; 571,96; 79,21] / “2024” [516,03; 59,95; 529,03; 65,95].
  - Bloco afetado PP 2, palavra PP “2024” [516,03; 59,95; 529,03; 65,95]; vizinhas Mu: “2024” [516,03; 59,95; 529,03; 65,95] / “DE” [507,47; 59,95; 514,59; 65,95].
  - Controle unitário no bloco PP 2: trocar só a caixa de “23” [543,61; 46,01; 571,96; 79,85] por “23” [543,61; 47,59; 571,96; 79,21] produz 58 blocos, dos quais 57/58 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_ba_salvador/dom-8908-07-11-2024.pdf#p37`: geometria isolada altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 7, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “38” [50,52; 47,71; 78,87; 81,54]; vizinhas Mu: “38” [50,52; 49,28; 78,87; 80,90] / “SALVADOR-BAHIA” [86,62; 45,70; 133,04; 51,70].
  - Bloco afetado PP 3, palavra PP “QUINTA-FEIRA” [86,62; 52,90; 123,86; 58,90]; vizinhas Mu: “QUINTA-FEIRA” [86,62; 52,90; 123,86; 58,90] / “07” [86,62; 60,10; 93,13; 66,10].
  - Controle unitário no bloco PP 2: trocar só a caixa de “38” [50,52; 47,71; 78,87; 81,54] por “38” [50,52; 49,28; 78,87; 80,90] produz 53 blocos, dos quais 52/55 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_ms/executive_official_diary_48555_2024-07-08.pdf#p22`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 3, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “Secretaria” [120,72; 46,15; 190,36; 57,15]; vizinhas Mu: “Secretaria” [120,72; 45,38; 190,36; 57,48] / “Eletrônico” [130,58; 16,48; 195,64; 27,98].
  - Bloco afetado PP 2, palavra PP “de” [194,50; 46,15; 210,99; 57,15]; vizinhas Mu: “de” [194,50; 45,38; 210,99; 57,48] / “Estado” [215,13; 45,38; 260,93; 57,48].
  - Controle unitário no bloco PP 2: trocar só a caixa de “Secretaria” [120,72; 46,15; 190,36; 57,15] por “Secretaria” [120,72; 45,38; 190,36; 57,48] produz 17 blocos, dos quais 16/17 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 2: trocar só a caixa de “de” [194,50; 46,15; 210,99; 57,15] por “de” [194,50; 45,38; 210,99; 57,48] produz 17 blocos, dos quais 16/17 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_ms/executive_official_diary_48977_2025-03-27.pdf#p170`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 3, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 3, palavra PP “Delegacia-Geral” [114,52; 193,49; 222,53; 204,49]; vizinhas Mu: “Delegacia-Geral” [114,52; 192,73; 222,53; 204,83] / “Comissão” [106,84; 168,62; 150,05; 177,62].
  - Bloco afetado PP 3, palavra PP “da” [226,67; 193,49; 243,21; 204,49]; vizinhas Mu: “da” [226,67; 192,73; 243,21; 204,83] / “Polícia” [247,35; 192,73; 292,14; 204,83].
  - Controle unitário no bloco PP 3: trocar só a caixa de “Delegacia-Geral” [114,52; 193,49; 222,53; 204,49] por “Delegacia-Geral” [114,52; 192,73; 222,53; 204,83] produz 13 blocos, dos quais 12/13 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 3: trocar só a caixa de “da” [226,67; 193,49; 243,21; 204,49] por “da” [226,67; 192,73; 243,21; 204,83] produz 13 blocos, dos quais 12/13 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pa/executive_official_diary_2022-05-17.pdf#p30`: geometria isolada não altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 76/76; aproximações do módulo `{'componentes_ligadura_unidos': 6, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 18, palavra PP “Processo” [311,19; 399,71; 336,56; 406,71]; vizinhas Mu: “Processo” [311,19; 401,66; 336,56; 405,86] / “(doaÇÃo)” [304,71; 387,39; 341,94; 394,39].
  - Bloco afetado PP 18, palavra PP “NoMe” [369,73; 399,71; 383,70; 406,71]; vizinhas Mu: “NoMe” [369,73; 401,66; 383,71; 405,86] / “MoNTEiro” [373,09; 412,68; 396,31; 416,88].
  - Bloco afetado Mu 18: palavra sem par estrito “Processo” [311,19; 401,66; 336,56; 405,86]; vizinhas PP: “Processo” [311,19; 399,71; 336,56; 406,71] / “2021/1365789” [308,24; 414,93; 339,53; 421,93].
  - Bloco afetado Mu 18: palavra sem par estrito “NoMe” [369,73; 401,66; 383,71; 405,86]; vizinhas PP: “NoMe” [369,73; 399,71; 383,70; 406,71] / “MoNTEiro” [373,09; 410,73; 396,31; 417,73].

- `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p21`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “Diário” [607,37; 3,96; 644,32; 16,96]; vizinhas Mu: “Diário” [607,37; 2,95; 644,33; 17,25] / “Ofi” [646,47; 2,95; 664,56; 17,25].
  - Bloco afetado PP 0, palavra PP “Ofi” [646,47; 3,96; 664,55; 16,96]; vizinhas Mu: “Ofi” [646,47; 2,95; 664,56; 17,25] / “cial” [663,84; 2,95; 686,01; 17,25].
  - Controle unitário no bloco PP 0: trocar só a caixa de “Diário” [607,37; 3,96; 644,32; 16,96] por “Diário” [607,37; 2,95; 644,33; 17,25] produz 5 blocos, dos quais 4/5 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 0: trocar só a caixa de “Ofi” [646,47; 3,96; 664,55; 16,96] por “Ofi” [646,47; 2,95; 664,56; 17,25] produz 5 blocos, dos quais 4/5 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p7`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “Diário” [607,37; 3,96; 644,32; 16,96]; vizinhas Mu: “Diário” [607,37; 2,95; 644,33; 17,25] / “Ofi” [646,47; 2,95; 664,56; 17,25].
  - Bloco afetado PP 0, palavra PP “Ofi” [646,47; 3,96; 664,55; 16,96]; vizinhas Mu: “Ofi” [646,47; 2,95; 664,56; 17,25] / “cial” [663,84; 2,95; 686,01; 17,25].
  - Controle unitário no bloco PP 0: trocar só a caixa de “Diário” [607,37; 3,96; 644,32; 16,96] por “Diário” [607,37; 2,95; 644,33; 17,25] produz 12 blocos, dos quais 11/12 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 0: trocar só a caixa de “Ofi” [646,47; 3,96; 664,55; 16,96] por “Ofi” [646,47; 2,95; 664,56; 17,25] produz 12 blocos, dos quais 11/12 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pe/2026-01-09_1-Poder Executivo.pdf#p2`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 1/1; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “(cid:262)” [721,76; 56,18; 727,76; 66,18]; vizinhas Mu: “�” [721,76; 56,18; 727,76; 66,18] / “NÀ” [730,56; 56,18; 741,56; 66,18].
  - Bloco afetado PP 2, palavra PP “3” [759,76; 56,18; 765,36; 66,18]; vizinhas Mu: “3” [759,76; 56,18; 765,36; 66,18] / “-” [752,76; 56,18; 756,96; 66,18].
  - Bloco afetado Mu 2: palavra sem par estrito “�” [721,76; 56,18; 727,76; 66,18]; vizinhas PP: “(cid:262)” [721,76; 56,18; 727,76; 66,18] / “NÀ” [730,56; 56,18; 741,56; 66,18].

- `official_diary_pr/executive_official_diary_2021-12-06.pdf#p62`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'fonte_sem_descritor': 41, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “63” [516,17; 34,04; 527,51; 46,04]; vizinhas Mu: “63” [516,17; 35,25; 527,51; 45,45] / “11071” [480,81; 35,28; 499,94; 44,28].
  - Bloco afetado PP 0, palavra PP “11071” [480,81; 35,28; 499,94; 44,28]; vizinhas Mu: “11071” [480,81; 35,28; 499,94; 44,28] / “nº” [472,61; 35,28; 478,91; 44,28].
  - Controle unitário no bloco PP 0: trocar só a caixa de “63” [516,17; 34,04; 527,51; 46,04] por “63” [516,17; 35,25; 527,51; 45,45] produz 41 blocos, dos quais 40/41 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_pr/executive_official_diary_2022-12-01.pdf#p91`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'fonte_sem_descritor': 41, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 0, palavra PP “92” [67,83; 34,06; 79,17; 46,06]; vizinhas Mu: “92” [67,83; 35,27; 79,17; 45,47] / “5ª” [95,24; 35,26; 101,84; 44,26].
  - Bloco afetado PP 0, palavra PP “1º/Dez/2022” [125,39; 35,26; 162,88; 44,26]; vizinhas Mu: “1º/Dez/2022” [125,39; 35,26; 162,88; 44,26] / “\|” [118,98; 35,26; 123,48; 44,26].
  - Controle unitário no bloco PP 0: trocar só a caixa de “92” [67,83; 34,06; 79,17; 46,06] por “92” [67,83; 35,27; 79,17; 45,47] produz 53 blocos, dos quais 52/53 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 26/26; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21]; vizinhas Mu: “��Á���” [342,96; 53,27; 393,28; 68,21] / “��” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado PP 2, palavra PP “(cid:1)(cid:2)(cid:3)(cid:4)(cid:5)” [52,44; 60,06; 79,45; 68,03]; vizinhas Mu: “�����” [52,44; 60,06; 79,45; 68,03] / “07.12.77,” [52,44; 86,12; 81,53; 93,09].
  - Bloco afetado Mu 0: palavra sem par estrito “��Á���” [342,96; 53,27; 393,28; 68,21]; vizinhas PP: “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21] / “(cid:1)(cid:4)” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado Mu 0: palavra sem par estrito “�������” [417,94; 53,36; 473,42; 68,30]; vizinhas PP: “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [417,94; 53,36; 473,42; 68,30] / “(cid:1)(cid:9)” [421,53; 69,28; 429,10; 75,26].

- `official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p34`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 26/26; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21]; vizinhas Mu: “��Á���” [342,96; 53,27; 393,28; 68,21] / “��” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado PP 3, palavra PP “(cid:1)(cid:2)(cid:3)(cid:4)(cid:5)” [52,44; 60,06; 79,45; 68,03]; vizinhas Mu: “�����” [52,44; 60,06; 79,45; 68,03] / “���������” [83,04; 60,06; 128,33; 68,03].
  - Bloco afetado Mu 0: palavra sem par estrito “��Á���” [342,96; 53,27; 393,28; 68,21]; vizinhas PP: “(cid:1)(cid:2)Á(cid:3)(cid:2)(cid:4)” [342,96; 53,27; 393,28; 68,21] / “(cid:1)(cid:4)” [357,23; 69,28; 365,50; 75,26].
  - Bloco afetado Mu 0: palavra sem par estrito “�������” [417,94; 53,36; 473,42; 68,30]; vizinhas PP: “(cid:4)(cid:5)(cid:2)(cid:6)(cid:2)(cid:7)(cid:8)” [417,94; 53,36; 473,42; 68,30] / “(cid:1)(cid:9)” [421,53; 69,28; 429,10; 75,26].

- `official_diary_rj_japeri/JAPERI-5422-03-DE-AGOSTO-2023_12_28.pdf#p0`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “ANO” [38,18; 38,87; 54,46; 46,87]; vizinhas Mu: “ANO” [38,18; 39,35; 54,46; 46,63] / “XXII” [56,74; 39,35; 71,26; 46,63].
  - Bloco afetado PP 2, palavra PP “XXII” [56,74; 38,87; 71,26; 46,87]; vizinhas Mu: “XXII” [56,74; 39,35; 71,26; 46,63] / “-” [73,41; 39,35; 75,84; 46,63].

- `official_diary_rj_japeri/JAPERI-5772-10-DE-JANEIRO-2025.pdf#p29`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 2, palavra PP “ANO” [40,88; 38,87; 57,02; 46,87]; vizinhas Mu: “ANO” [40,88; 39,35; 57,01; 46,63] / “XXIII” [59,15; 39,35; 75,66; 46,63].
  - Bloco afetado PP 2, palavra PP “XXIII” [59,15; 38,87; 75,66; 46,87]; vizinhas Mu: “XXIII” [59,15; 39,35; 75,66; 46,63] / “ANO” [40,88; 39,35; 57,01; 46,63].

- `official_diary_rr/2022-09-27_DiarioRR.pdf#p44`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 2, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “Edição” [47,29; 19,78; 80,42; 28,78]; vizinhas Mu: “Edição” [47,29; 18,27; 80,42; 29,52] / “N°:” [83,23; 18,27; 99,60; 29,52].
  - Bloco afetado PP 1, palavra PP “N°:” [83,23; 19,78; 99,60; 28,78]; vizinhas Mu: “N°:” [83,23; 18,27; 99,60; 29,52] / “4292” [102,42; 18,27; 124,92; 29,52].
  - Controle unitário no bloco PP 1: trocar só a caixa de “Edição” [47,29; 19,78; 80,42; 28,78] por “Edição” [47,29; 18,27; 80,42; 29,52] produz 11 blocos, dos quais 10/11 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 1: trocar só a caixa de “N°:” [83,23; 19,78; 99,60; 28,78] por “N°:” [83,23; 18,27; 99,60; 29,52] produz 11 blocos, dos quais 10/11 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_rr/2024-01-16_DiarioRR.pdf#p19`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 4, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 1, palavra PP “Edição” [47,29; 19,78; 80,42; 28,78]; vizinhas Mu: “Edição” [47,29; 18,27; 80,42; 29,52] / “presente” [36,51; 34,02; 66,50; 43,02].
  - Bloco afetado PP 1, palavra PP “N°:” [83,23; 19,78; 99,60; 28,78]; vizinhas Mu: “N°:” [83,23; 18,27; 99,60; 29,52] / “Declaratório” [84,00; 34,02; 128,98; 43,02].
  - Controle unitário no bloco PP 1: trocar só a caixa de “Edição” [47,29; 19,78; 80,42; 28,78] por “Edição” [47,29; 18,27; 80,42; 29,52] produz 18 blocos, dos quais 17/18 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 1: trocar só a caixa de “N°:” [83,23; 19,78; 99,60; 28,78] por “N°:” [83,23; 18,27; 99,60; 29,52] produz 18 blocos, dos quais 17/18 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_se/DOE-SE_2024-10-17_6324.pdf#p3`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'fonte_ambigua': 4986, 'caracteres_desduplicados': 0}`.
  - Bloco afetado PP 36, palavra PP “EXONERAR” [126,36; 924,48; 216,04; 935,80]; vizinhas Mu: “EXONERAR” [126,36; 923,56; 216,04; 936,04] / “ELENISE” [125,29; 949,47; 178,59; 961,95].
  - Bloco afetado PP 40, palavra PP “Aracaju,” [126,35; 1015,41; 168,89; 1026,73]; vizinhas Mu: “Aracaju,” [126,35; 1014,51; 168,89; 1026,98] / “a” [132,23; 988,50; 137,76; 1000,97].
  - Controle unitário no bloco PP 36: trocar só a caixa de “EXONERAR” [126,36; 924,48; 216,04; 935,80] por “EXONERAR” [126,36; 923,56; 216,04; 936,04] produz 53 blocos, dos quais 52/53 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.
  - Controle unitário no bloco PP 40: trocar só a caixa de “Aracaju,” [126,35; 1015,41; 168,89; 1026,73] por “Aracaju,” [126,35; 1014,51; 168,89; 1026,98] produz 53 blocos, dos quais 52/53 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

- `official_diary_sp/Executivo - Caderno 3_2023-07-12_90_123.pdf#p0`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/13; aproximações do módulo `{'fonte_sem_descritor': 221, 'caracteres_desduplicados': 0}`.
  - Bloco afetado Mu 12: palavra sem par estrito “A” [322,00; 1268,66; 330,00; 1280,66]; vizinhas PP: “do” [330,04; 1215,22; 336,78; 1222,22] / “assunto” [305,92; 1215,22; 326,54; 1222,22].
  - Bloco afetado Mu 12: palavra sem par estrito “Companhia” [333,34; 1268,66; 394,70; 1280,66]; vizinhas PP: “do” [330,04; 1215,22; 336,78; 1222,22] / “e–mail:” [340,28; 1215,22; 359,97; 1222,22].

- `official_diary_sp/Executivo - Caderno 3_2024-04-02.pdf#p182`: geometria isolada não altera os blocos; textos/partição dos blocos divergem; palavras sem correspondência 0/13; aproximações do módulo `{'fonte_sem_descritor': 219, 'caracteres_desduplicados': 0}`.
  - Bloco afetado Mu 9: palavra sem par estrito “A” [322,00; 1254,49; 330,00; 1266,49]; vizinhas PP: “deverá” [327,01; 1207,15; 344,89; 1214,15] / “e230op@cps.sp.gov.br,” [308,17; 1215,21; 368,55; 1222,21].
  - Bloco afetado Mu 9: palavra sem par estrito “Companhia” [333,34; 1254,49; 394,70; 1266,49]; vizinhas PP: “deverá” [327,01; 1207,15; 344,89; 1214,15] / “ser” [347,65; 1207,15; 355,42; 1214,15].

- `official_diary_to/2021-11-18_4498.pdf#p31`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 10, 'caracteres_desduplicados': 7}`.
  - Bloco afetado PP 1, palavra PP “ANO” [279,34; 29,73; 294,94; 37,73]; vizinhas Mu: “ANO” [279,34; 30,27; 294,94; 37,47] / “XXXIII” [296,94; 30,27; 317,35; 37,47].
  - Bloco afetado PP 1, palavra PP “XXXIII” [296,94; 29,73; 317,35; 37,73]; vizinhas Mu: “XXXIII” [296,94; 30,27; 317,35; 37,47] / “ANO” [279,34; 30,27; 294,94; 37,47].

- `official_diary_to/2021-11-18_4498.pdf#p41`: geometria isolada altera os blocos; textos dos blocos iguais, caixas divergem; palavras sem correspondência 0/0; aproximações do módulo `{'componentes_ligadura_unidos': 20, 'caracteres_desduplicados': 4}`.
  - Bloco afetado PP 39, palavra PP “NATURATINS” [54,37; 665,95; 111,54; 675,95]; vizinhas Mu: “NATURATINS” [54,37; 666,58; 111,54; 675,58] / “PORTARIA” [39,79; 696,46; 80,98; 704,46].
  - Bloco afetado PP 1, palavra PP “ANO” [279,34; 29,73; 294,94; 37,73]; vizinhas Mu: “ANO” [279,34; 30,27; 294,94; 37,47] / “XXXIII” [296,94; 30,27; 317,35; 37,47].
  - Controle unitário no bloco PP 39: trocar só a caixa de “NATURATINS” [54,37; 665,95; 111,54; 675,95] por “NATURATINS” [54,37; 666,58; 111,54; 675,58] produz 50 blocos, dos quais 49/50 continuam idênticos. Texto e fluxo não foram alterados; o par usado neste controle aceita IoU ≥ 0,35.

### Divergências de ordem nos blocos sobreviventes

| Página | τ stream | τ naive | τ xycut | Pares / PP / Mu |
|---|---:|---:|---:|---:|
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | 1,000000 | 1,000000 | 0,878992 | 35 / 41 / 38 |
| `official_diary_se/DOE-SE_2026-01-09_7381.pdf#p2` | 1,000000 | 0,998747 | 0,998747 | 57 / 116 / 116 |
| `official_diary_RJ_barra_do_pirai/executive_official_diary_2025-09-11_166.pdf#p1` | 1,000000 | 0,991475 | 1,000000 | 69 / 69 / 69 |
| `official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p21` | 1,000000 | 0,666667 | 0,666667 | 4 / 5 / 5 |
| `official_diary_se/DOE-SE_2024-10-17_6324.pdf#p3` | 1,000000 | 0,997677 | 0,997677 | 42 / 53 / 53 |

## Auditoria da medição anterior

Leitura e recálculo de `resultados/pymupdf_palavras_cache.json`: 60 páginas, 64252 pares / 74635 palavras PP (86,09% micro; 92,22% macro). Médias totais: PP 4,917 s; Mu 0,024 s. O resumo anterior afirmava 99,4% de palavras casadas, o que não corresponde ao agregado do próprio cache. A classificação anterior chamada “acento_unicode” também incluía textos iguais (normalização idêntica): não prova divergência de acentos. Nem ausência de perda nem paridade dos blocos tinham sido demonstradas.

## Testes executados

| Conjunto | Testes | Código de saída | Tempo s | Log |
|---|---:|---:|---:|---|
| novos | 21 | 0 | 1,14 | `resultados\extrator_pymupdf_cache\20261003_080859_18c43f6f\testes_novos.txt` |
| suite | 126 | 0 | 1,34 | `resultados\extrator_pymupdf_cache\20261003_080859_18c43f6f\testes_suite.txt` |

A suíte inclui os novos testes; não somar as duas linhas. Comandos e saída completa estão nos logs e em `testes.json` da execução.

## Limitações e compatibilidade

- Amostra pequena e balanceada (104 páginas concluídas, 30 veículos), com páginas-problema escolhidas deliberadamente. Não representa a distribuição de todo o acervo nem demonstra igualdade em PDFs inéditos. Não é avaliação humana de qualidade.
- Não usa export ou anotações do Label Studio nem modifica dado humano. O viés de ancoragem de anotações feitas corrigindo pré-anotação não afeta este teste de equivalência entre parsers; continua uma limitação de avaliações humanas do projeto parceiro.
- Uma rodada cronometrada por página, processo serial, abertura fresca, caches do SO não controlados e outros trabalhos na máquina. Não interpretar pequenas diferenças de tempo como significativas nem extrapolar vazão para treino/layout/OCR.
- Campos emitidos: t, x0, x1, top, bottom, s. Tamanho/negrito não são emitidos pelo extrator original; altura e deduplicação são reproduzidas com descritores PDF/AFM. Fontes ambíguas/Type3 usam descender MuPDF e ficam no diagnóstico. Larguras, CMaps, ligaduras, espaços e transformações podem divergir. Diagnósticos acumulados: `{'componentes_ligadura_unidos': 1498, 'caracteres_desduplicados': 252, 'fonte_ambigua': 36563, 'orientacao_aproximada': 105, 'fonte_sem_descritor': 15639}`.
- Coordenadas seguem a MediaBox do pdfplumber, sem recorte pela CropBox. O caso CropBox com rotação é testado; o módulo não altera o documento. Não há OCR para texto em imagens. Envelope PKCS#7 é extraído somente em resultados/ pelo script, quando presente; arquivos normais com zeros finais abrem diretamente.
- PyMuPDF/MuPDF oferecem AGPL e licença comercial. A escolha de distribuição do projeto precisa considerar a licença antes de integrar a dependência. [Licenciamento oficial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).

## Diff proposto (não aplicado)

Opção local por variável de ambiente; o worker ainda abre pdfplumber para manter dimensões e os demais contratos. O parsing de caracteres do pdfplumber é evitado, mas a enumeração/abertura ainda existe. Não torna o novo caminho padrão e não autoriza regenerar a silver nem lotes humanos. Revisão cruzada e decisão do Pedro continuam necessárias.

```diff
--- a/src/data/extrator.py
+++ b/src/data/extrator.py
@@
 def palavras_da_pagina(page):
     """Palavras em ordem de fluxo do PDF, com o indice de fluxo em 's'."""
+    if os.environ.get("TCC_EXTRATOR_PALAVRAS", "pdfplumber") == "pymupdf":
+        import pymupdf
+        from src.data.palavras_pymupdf import palavras_da_pagina_pymupdf
+        with pymupdf.open(page.pdf.stream.name) as pdf:
+            return palavras_da_pagina_pymupdf(pdf[page.page_number - 1])
     try:
         page = page.dedupe_chars(tolerance=1)
```

Esse diff mínimo destina-se aos workers atuais com arquivo PDF local, não a BytesIO nem páginas recortadas via Page.crop(). O benchmark mede o módulo direto com PyMuPDF, não esse wrapper híbrido. Para remover também abertura/enumeração do pdfplumber, é preciso uma segunda alteração nos workers e nas dimensões, fora desta tarefa.

## Reprodução e conferência automática

`venv/Scripts/python.exe -B orquestracao/analises/extrator_pymupdf_paridade.py --do-zero`

Sem `--do-zero`, a execução atual retoma cada caminho cujo fingerprint confere. Hashes do extrator, módulo, PDF (tamanho/mtime) e tabelas invalidam caches incompatíveis. Arquivos incompletos são ignorados. Dados intermediários completos e resumos ficam no diretório indicado acima. As contagens da tabela são conferidas contra os registros antes de cada escrita do relatório.
