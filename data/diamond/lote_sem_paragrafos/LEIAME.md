# Lote Diamond Sem Caixas de Paragrafo (`lote_sem_paragrafos`)

Lote classificavel com **60 paginas estratificadas** preparadas a partir do extrator
novo sem caixas de paragrafo (linhas de texto corridas; tabelas e imagens atomicas;
cabecalhos, rodapes e quadros estruturais).

Este lote destina-se a **anotacao e correcao humana de segmentacao** pelo Pedro na
ferramenta Diamond (`src/anotacao/servidor.py --diamond`), sem ordem preenchida (anotacao cega).

---

## 1. Como Abrir o Lote no Diamond

O servidor local (`src/anotacao/servidor.py`) procura os lotes Diamond sob `data/diamond/<lote>/`.
Como os arquivos foram gerados sob `resultados/lote_sem_paragrafos/` (respeitando a regra de nao escrita em `data/`),
o lote deve ser copiado ou vinculado para `data/diamond/lote_sem_paragrafos/`.

### Passo a passo no PowerShell (Windows 11):

1. **Copiar a pasta do lote para `data/diamond/`:**
   ```powershell
   Copy-Item -Recurse resultados\lote_sem_paragrafos data\diamond\lote_sem_paragrafos
   ```
   *(Alternativa com juncao NTFS instantanea sem duplicar disco):*
   ```powershell
   cmd /c mklink /J data\diamond\lote_sem_paragrafos resultados\lote_sem_paragrafos
   ```

2. **Iniciar o servidor Diamond:**
   ```powershell
   venv\Scripts\python.exe src\anotacao\servidor.py --diamond
   ```

3. **Acessar a ferramenta no navegador:**
   - URL: **`http://127.0.0.1:8770/diamond`**
   - No seletor **Lote** (canto superior esquerdo), selecione: **`lote_sem_paragrafos`**
   - Informe seu nome no campo **Anotador** (ex.: `Pedro`).
   - As alteracoes sao salvas automaticamente em tempo real em `data/diamond/lote_sem_paragrafos/anotacoes.jsonl`.

---

## 2. O que Corrigir nas Paginas

A proposta que chega na tela contem as unidades do novo extrator como caixas iniciais.
O Pedro devera inspecionar e corrigir tres tipos principais de defeitos:

1. **Caixas com fronteiras erradas (Geometria):**
   - Linhas de texto que atravessam calhas entre colunas (dividir com <kbd>Shift</kbd>+<kbd>D</kbd> ou <kbd>D</kbd>).
   - Caixas de tabela ou figura que invadem texto corrido ou vice-versa.
   - Textos institucionais ou molduras que foram engolidos como texto simples.
   - Tecla <kbd>A</kbd> (<kbd>Shift</kbd>+<kbd>A</kbd> em todas) ajusta as bordas da caixa as palavras exatas de dentro.

2. **Classes erradas (Semantica):**
   - Títulos de secao/atos marcados como `texto` -> reclassificar para `titulo` (<kbd>1</kbd>).
   - Textos corridos marcados como `outro` ou `lista` -> reclassificar para `texto` (<kbd>2</kbd>).
   - Tabelas marcadas como texto ou figura -> reclassificar para `tabela` (<kbd>4</kbd>).
   - Assinaturas de autoridades -> reclassificar para `assinatura` (<kbd>5</kbd>).
   - Cabecalhos (<kbd>6</kbd>) e Rodapes (<kbd>7</kbd>) fragmentados ou ausentes.
   - Brasao/logo/QR code -> `figura` (<kbd>8</kbd>).

3. **Caixas que faltam:**
   - Palavras destacadas em vermelho (sem caixa): desenhe uma nova caixa arrastando o mouse na area.
   - Palavras destacadas em magenta (em duas caixas): ajuste ou redimensione as caixas concorrentes.

### Teclas rapidas:
- <kbd>1</kbd>–<kbd>9</kbd>: altera classe da caixa selecionada (1=Titulo, 2=Texto, 3=Lista, 4=Tabela, 5=Assinatura, 6=Cabecalho, 7=Rodape, 8=Figura, 9=Outro).
- <kbd>A</kbd>: ajusta caixa selecionada as palavras; <kbd>Shift</kbd>+<kbd>A</kbd>: ajusta todas.
- <kbd>D</kbd>: divide caixa na altura do clique; <kbd>Shift</kbd>+<kbd>D</kbd>: divide na largura.
- <kbd>J</kbd>: junta caixas selecionadas.
- <kbd>Del</kbd>: apaga caixa selecionada.
- <kbd>N</kbd>: navega para o proximo alerta.
- <kbd>Enter</kbd>: conclui e avanca.

---

## 3. Estratificacao da Amostra

O lote possui **60 paginas rigorosamente estratificadas**:
- **30 paginas com os piores achados do auditor** (`resultados/auditoria_extrator_sem_paragrafos.json`),
  garantindo diversificacao de defeitos graves (D1 a D7) e de orgaos publicadores.
- **30 paginas aleatorias** (semente fixa `20261008`) sorteadas sobre as paginas candidatas sem defeito grave
  para estimar a taxa real e nao viesada de erro do extrator.
- **Teto maximo de 4 paginas por veiculo** no lote todo para evitar sobre-representacao de qualquer diario oficial.
- **Exclusao estrita:** nenhuma pagina das bancadas humanas (`golden_v4` e `golden_v3`) e nenhuma de `data/labelstudio/`.

### Cobertura de Detectores nos Piores Achados:
- **D1 (Linha que atravessa colunas):** 2 paginas
- **D2 (Sobreposicao tabela x texto):** 8 paginas
- **D4 (Tabela suspeita / vazia):** 17 paginas
- **D5 (Cabecalho/rodape fragmentado):** 0 paginas
- **D6 (Linha com altura anomala):** 19 paginas
- **D7 (Texto sem dono perto de atomo):** 0 paginas

### Distribuicao de Paginas por Veiculo (Diario Oficial):

| Veiculo (`uf`) | Piores Achados | Aleatorias | Total no Lote |
|---|---:|---:|---:|
| `official_diary_MG_congonhas` | 0 | 2 | **2** |
| `official_diary_RJ_duque_de_caxias` | 3 | 1 | **4** |
| `official_diary_RJ_seropedica` | 3 | 1 | **4** |
| `official_diary_RJ_volta_redonda` | 3 | 1 | **4** |
| `official_diary_ac` | 0 | 3 | **3** |
| `official_diary_al` | 2 | 2 | **4** |
| `official_diary_am_manaus` | 3 | 1 | **4** |
| `official_diary_ap` | 1 | 2 | **3** |
| `official_diary_ba_salvador` | 3 | 1 | **4** |
| `official_diary_ms` | 2 | 2 | **4** |
| `official_diary_pa` | 2 | 2 | **4** |
| `official_diary_pe` | 3 | 0 | **3** |
| `official_diary_pr` | 0 | 1 | **1** |
| `official_diary_pr_curitiba` | 0 | 1 | **1** |
| `official_diary_rj_japeri` | 0 | 1 | **1** |
| `official_diary_rn` | 0 | 2 | **2** |
| `official_diary_ro` | 0 | 1 | **1** |
| `official_diary_rr` | 0 | 2 | **2** |
| `official_diary_sc` | 2 | 2 | **4** |
| `official_diary_se` | 2 | 0 | **2** |
| `official_diary_to` | 1 | 2 | **3** |

---

## 4. Validacao Tecnica com `servidor.py`

- **Status da Validacao:** PASSOU COM SUCESSO (0 erros)
- **Total de Tarefas Verificadas:** 60
- **Total de Imagens JPEG (110 dpi):** 60
- **Total de Palavras no Lote:** 51,336
- **Total de Regioes na Proposta:** 5,652
- **Distribuicao de Classes na Proposta:** `figura`: 126, `tabela`: 112, `texto`: 5414
- **Erros impeditivos:** 0
- **Avisos informativos de palavras pendentes de caixa:** 0 (esperados para correcao manual)

---

## 5. Tabela Completa das 60 Paginas do Lote

| N | Page ID | Veiculo | Motivo da Estratificacao | Palavras | Propostas | Imagem |
|---|---|---|---|---:|---:|---|
| 01 | `official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29` | `official_diary_am_manaus` | Pior achado [D1] | 912 | 77 | `001.jpg` |
| 02 | `official_diary_am_manaus/2025-09-30_caderno_1.pdf#p3` | `official_diary_am_manaus` | Pior achado [D1] | 755 | 78 | `002.jpg` |
| 03 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2023-02-03_Boletim_7250.pdf#p57` | `official_diary_RJ_duque_de_caxias` | Pior achado [D2] | 1127 | 114 | `003.jpg` |
| 04 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-10-03_Boletim_7199.pdf#p10` | `official_diary_RJ_duque_de_caxias` | Pior achado [D2] | 891 | 112 | `004.jpg` |
| 05 | `official_diary_sc/2021-04-09_21497_15_320.pdf#p0` | `official_diary_sc` | Pior achado [D2] | 1964 | 14 | `005.jpg` |
| 06 | `official_diary_ap/2021-12-22_DOEn7569_Edicao Ordinaria.pdf#p220` | `official_diary_ap` | Pior achado [D2] | 253 | 49 | `006.jpg` |
| 07 | `official_diary_pa/executive_official_diary_extra_2026-01-16.pdf#p9` | `official_diary_pa` | Pior achado [D2] | 903 | 93 | `007.jpg` |
| 08 | `official_diary_se/DOE-SE_2026-01-09_7381.pdf#p9` | `official_diary_se` | Pior achado [D2] | 1155 | 127 | `008.jpg` |
| 09 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-06-28_1845.pdf#p20` | `official_diary_RJ_volta_redonda` | Pior achado [D4] | 872 | 153 | `009.jpg` |
| 10 | `official_diary_RJ_volta_redonda/executive_official_diary_2022-12-15_1899.pdf#p4` | `official_diary_RJ_volta_redonda` | Pior achado [D4] | 1089 | 127 | `010.jpg` |
| 11 | `official_diary_RJ_seropedica/executive_official_diary_2022-04-13_969.pdf#p2` | `official_diary_RJ_seropedica` | Pior achado [D4] | 680 | 72 | `011.jpg` |
| 12 | `official_diary_RJ_seropedica/executive_official_diary_2022-04-27_977.pdf#p1` | `official_diary_RJ_seropedica` | Pior achado [D4] | 324 | 44 | `012.jpg` |
| 13 | `official_diary_sc/2021-04-28_21509_2_126.pdf#p0` | `official_diary_sc` | Pior achado [D4] | 137 | 37 | `013.jpg` |
| 14 | `official_diary_ba_salvador/dom-8796-30-05-2024.pdf#p15` | `official_diary_ba_salvador` | Pior achado [D4] | 687 | 87 | `014.jpg` |
| 15 | `official_diary_ms/executive_official_diary_47904_2023-06-19_251_721.pdf#p0` | `official_diary_ms` | Pior achado [D4] | 240 | 34 | `015.jpg` |
| 16 | `official_diary_ba_salvador/dom-8763-12-04-2024.pdf#p14` | `official_diary_ba_salvador` | Pior achado [D6] | 1000 | 136 | `016.jpg` |
| 17 | `official_diary_pe/2025-01-14_1-Poder Executivo.pdf#p1` | `official_diary_pe` | Pior achado [D6] | 1332 | 130 | `017.jpg` |
| 18 | `official_diary_pe/2024-02-06_1-Poder Executivo.pdf#p3` | `official_diary_pe` | Pior achado [D6] | 1336 | 123 | `018.jpg` |
| 19 | `official_diary_al/DOEAL-2026-01-14-SUPLEMENTO.pdf#p2` | `official_diary_al` | Pior achado [D6] | 539 | 106 | `019.jpg` |
| 20 | `official_diary_al/DOEAL-2025-10-14-SUPLEMENTO.pdf#p2` | `official_diary_al` | Pior achado [D6] | 535 | 109 | `020.jpg` |
| 21 | `official_diary_se/DOE-SE_2024-01-12_5749.pdf#p11` | `official_diary_se` | Pior achado [D6] | 1093 | 60 | `021.jpg` |
| 22 | `official_diary_am_manaus/2026-01-09_caderno_1.pdf#p9` | `official_diary_am_manaus` | Pior achado [D2+D4+D6] | 787 | 77 | `022.jpg` |
| 23 | `official_diary_RJ_seropedica/executive_official_diary_2022-04-25_975 Extra.pdf#p2` | `official_diary_RJ_seropedica` | Pior achado [D6] | 317 | 45 | `023.jpg` |
| 24 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-10-03_Boletim_7199.pdf#p6` | `official_diary_RJ_duque_de_caxias` | Pior achado [D2+D6] | 806 | 111 | `024.jpg` |
| 25 | `official_diary_ms/executive_official_diary_47942_2023-07-14_405_522.pdf#p0` | `official_diary_ms` | Pior achado [D4] | 299 | 34 | `025.jpg` |
| 26 | `official_diary_RJ_volta_redonda/executive_official_diary_2023-03-28_1930.pdf#p5` | `official_diary_RJ_volta_redonda` | Pior achado [D4] | 1042 | 122 | `026.jpg` |
| 27 | `official_diary_pe/2025-05-06_1-Poder Executivo.pdf#p3` | `official_diary_pe` | Pior achado [D6] | 1100 | 126 | `027.jpg` |
| 28 | `official_diary_to/2022-12-13_4783.pdf#p43` | `official_diary_to` | Pior achado [D4] | 816 | 43 | `028.jpg` |
| 29 | `official_diary_pa/executive_official_diary_2022-02-14.pdf#p24` | `official_diary_pa` | Pior achado [D4] | 1016 | 149 | `029.jpg` |
| 30 | `official_diary_ba_salvador/dom-9141-25-10-2025.pdf#p6` | `official_diary_ba_salvador` | Pior achado [D4+D6] | 1353 | 114 | `030.jpg` |
| 31 | `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-12-12_Boletim_7227.pdf#p6` | `official_diary_RJ_duque_de_caxias` | Amostra aleatoria | 980 | 134 | `031.jpg` |
| 32 | `official_diary_ms/executive_official_diary_48555_2024-07-08.pdf#p50` | `official_diary_ms` | Amostra aleatoria | 486 | 16 | `032.jpg` |
| 33 | `official_diary_ms/executive_official_diary_48414_2024-04-15.pdf#p34` | `official_diary_ms` | Amostra aleatoria | 578 | 73 | `033.jpg` |
| 34 | `official_diary_sc/2026-01-12_22673.pdf#p1` | `official_diary_sc` | Amostra aleatoria | 1546 | 211 | `034.jpg` |
| 35 | `official_diary_MG_congonhas/executive_official_diary_2021-06-14_2722.pdf#p2` | `official_diary_MG_congonhas` | Amostra aleatoria | 431 | 47 | `035.jpg` |
| 36 | `official_diary_rn/DOE-RN_2021-10-06_Ordinaria.pdf#p13` | `official_diary_rn` | Amostra aleatoria | 1922 | 172 | `036.jpg` |
| 37 | `official_diary_ap/2022-11-18_DOEn7793_Edicao Ordinaria.pdf#p151` | `official_diary_ap` | Amostra aleatoria | 252 | 37 | `037.jpg` |
| 38 | `official_diary_ac/executive_official_diary_2024-05-29.pdf#p189` | `official_diary_ac` | Amostra aleatoria | 1166 | 65 | `038.jpg` |
| 39 | `official_diary_ba_salvador/dom-8747-21-03-2024.pdf#p12` | `official_diary_ba_salvador` | Amostra aleatoria | 1255 | 159 | `039.jpg` |
| 40 | `official_diary_am_manaus/2023-08-02_caderno_2_37_54.pdf#p0` | `official_diary_am_manaus` | Amostra aleatoria | 1433 | 4 | `040.jpg` |
| 41 | `official_diary_ac/executive_official_diary_2025-02-11.pdf#p151` | `official_diary_ac` | Amostra aleatoria | 528 | 56 | `041.jpg` |
| 42 | `official_diary_rr/2024-01-16_DiarioRR.pdf#p13` | `official_diary_rr` | Amostra aleatoria | 494 | 51 | `042.jpg` |
| 43 | `official_diary_pr_curitiba/14-Supl1_2024-01-22.pdf#p144` | `official_diary_pr_curitiba` | Amostra aleatoria | 209 | 9 | `043.jpg` |
| 44 | `official_diary_ac/executive_official_diary_2023-07-26.pdf#p109` | `official_diary_ac` | Amostra aleatoria | 496 | 49 | `044.jpg` |
| 45 | `official_diary_rr/2024-01-16_DiarioRR.pdf#p19` | `official_diary_rr` | Amostra aleatoria | 417 | 48 | `045.jpg` |
| 46 | `official_diary_RJ_volta_redonda/executive_official_diary_2024-10-17_2122.pdf#p5` | `official_diary_RJ_volta_redonda` | Amostra aleatoria | 1005 | 141 | `046.jpg` |
| 47 | `official_diary_al/DOEAL-2025-10-02-COMPLETO.pdf#p19` | `official_diary_al` | Amostra aleatoria | 1116 | 124 | `047.jpg` |
| 48 | `official_diary_rn/DOE-RN_2021-10-16_Ordinaria.pdf#p46` | `official_diary_rn` | Amostra aleatoria | 294 | 35 | `048.jpg` |
| 49 | `official_diary_ro/executive_official_diary_2024-06-12.pdf#p316` | `official_diary_ro` | Amostra aleatoria | 312 | 6 | `049.jpg` |
| 50 | `official_diary_sc/2025-02-07_22448.pdf#p17` | `official_diary_sc` | Amostra aleatoria | 1870 | 257 | `050.jpg` |
| 51 | `official_diary_MG_congonhas/executive_official_diary_2014-09-30_1114.pdf#p5` | `official_diary_MG_congonhas` | Amostra aleatoria | 515 | 42 | `051.jpg` |
| 52 | `official_diary_al/DOEAL-2024-05-13-COMPLETO.pdf#p24` | `official_diary_al` | Amostra aleatoria | 1083 | 142 | `052.jpg` |
| 53 | `official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf#p18` | `official_diary_rj_japeri` | Amostra aleatoria | 819 | 115 | `053.jpg` |
| 54 | `official_diary_to/2024-04-17_5147.pdf#p50` | `official_diary_to` | Amostra aleatoria | 845 | 132 | `054.jpg` |
| 55 | `official_diary_ap/2025-05-05_DOEn8402_Edicao Ordinaria_34_62.pdf#p0` | `official_diary_ap` | Amostra aleatoria | 763 | 151 | `055.jpg` |
| 56 | `official_diary_RJ_seropedica/executive_official_diary_2022-05-05_984.pdf#p3` | `official_diary_RJ_seropedica` | Amostra aleatoria | 755 | 116 | `056.jpg` |
| 57 | `official_diary_pa/executive_official_diary_2022-02-14.pdf#p59` | `official_diary_pa` | Amostra aleatoria | 1275 | 174 | `057.jpg` |
| 58 | `official_diary_pa/executive_official_diary_2023-03-06.pdf#p27` | `official_diary_pa` | Amostra aleatoria | 1116 | 96 | `058.jpg` |
| 59 | `official_diary_to/2021-11-18_4498.pdf#p41` | `official_diary_to` | Amostra aleatoria | 1124 | 128 | `059.jpg` |
| 60 | `official_diary_pr/executive_official_diary_2021-09-23.pdf#p177` | `official_diary_pr` | Amostra aleatoria | 891 | 159 | `060.jpg` |
