# Relatório da Execução Noturna — Segmentação v3

**Data:** 13 de setembro de 2026  
**Autor:** Antigravity CLI (`gemini-3.8-flash-high`)  
**Tempo estimado de leitura:** 5 minutos  
**Objetivo:** Sintetizar os resultados do pipeline experimental executado durante a noite de 12 para 13/09/2026 sobre a segmentação v3 (calhas locais e detecção de tabelas pelo Docling Heron), em comparação com a segmentação v1.

---

## 1. O que rodou

**Fonte dos dados:** `orquestracao/logs/noite_v3/status.jsonl` e `orquestracao/logs/noite_v3/*.log`

Os passos `golden_v3` e `ri_japeri_piloto` do roteiro principal avaliaram o LayoutLM sucessor com busca em feixe, por um padrão errado em `prever()`; no teste, o método usa decodificação em cadeias. O padrão foi corrigido (`src/models/layoutlm_sucessor.py`) e os passos foram refeitos por `orquestracao/noite_v3_correcao.sh` como `golden_v3_cadeias` e `ri_japeri_piloto_cadeias`. Os arquivos em `resultados/` já são os corrigidos (e o passo `relatorio_antigravity` do roteiro principal falhou de propósito: o prompt dele foi substituído por este).

| # | Passo | Início | Fim | Duração | Código de saída |
|---|---|---|---|---:|---:|
| 1 | `pacote_kaggle` | 2026-09-13 01:30:55 | 2026-09-13 01:30:57 | 2s | 0 |
| 2 | `ri_japeri_reextrair` | 2026-09-13 01:30:57 | 2026-09-13 01:31:45 | 48s | 0 |
| 3 | `lstm_geo` | 2026-09-13 01:31:45 | 2026-09-13 01:33:07 | 1m22s (82s) | 0 |
| 4 | `lstm_texto` | 2026-09-13 01:33:07 | 2026-09-13 01:34:41 | 1m34s (94s) | 0 |
| 5 | `lstm_geo_texto` | 2026-09-13 01:34:41 | 2026-09-13 01:36:17 | 1m36s (96s) | 0 |
| 6 | `curva` | 2026-09-13 01:36:17 | 2026-09-13 02:43:10 | 1h06m53s (4013s) | 0 |
| 7 | `layoutlm_avaliar` | 2026-09-13 02:43:13 | 2026-09-13 02:43:22 | 9s | 0 |
| 8 | `sucessor_avaliar` | 2026-09-13 02:43:22 | 2026-09-13 02:43:32 | 10s | 0 |
| 9 | `sucessor_limiar_0.0` | 2026-09-13 02:43:32 | 2026-09-13 02:43:42 | 10s | 0 |
| 10 | `sucessor_limiar_0.3` | 2026-09-13 02:43:42 | 2026-09-13 02:43:52 | 10s | 0 |
| 11 | `sucessor_limiar_0.7` | 2026-09-13 02:43:52 | 2026-09-13 02:44:02 | 10s | 0 |
| 12 | `sucessor_limiar_0.9` | 2026-09-13 02:44:02 | 2026-09-13 02:44:12 | 10s | 0 |
| 13 | `sucessor_feixe` | 2026-09-13 02:44:12 | 2026-09-13 02:44:22 | 10s | 0 |
| 14 | `golden_v3` | 2026-09-13 02:44:23 | 2026-09-13 02:44:35 | 12s | 0 |
| 15 | `comparar` | 2026-09-13 02:44:35 | 2026-09-13 02:44:43 | 8s | 0 |
| 16 | `curva_figura` | 2026-09-13 02:44:43 | 2026-09-13 02:44:45 | 2s | 0 |
| 17 | `ri_japeri_piloto` | 2026-09-13 02:44:45 | 2026-09-13 02:45:05 | 20s | 0 |
| 18 | `latencia` | 2026-09-13 02:45:05 | 2026-09-13 02:45:24 | 19s | 0 |
| 19 | `ablacao_suc_sem_vies_geo_treinar` | 2026-09-13 02:45:24 | 2026-09-13 02:55:21 | 9m57s (597s) | 0 |
| 20 | `ablacao_suc_sem_vies_geo_avaliar` | 2026-09-13 02:55:21 | 2026-09-13 02:55:31 | 10s | 0 |
| 21 | `ablacao_suc_sem_posicao_treinar` | 2026-09-13 02:55:31 | 2026-09-13 03:06:03 | 10m32s (632s) | 0 |
| 22 | `ablacao_suc_sem_posicao_avaliar` | 2026-09-13 03:06:03 | 2026-09-13 03:06:13 | 10s | 0 |
| 23 | `ablacao_suc_sem_layout_treinar` | 2026-09-13 03:06:13 | 2026-09-13 03:16:23 | 10m10s (610s) | 0 |
| 24 | `ablacao_suc_sem_layout_avaliar` | 2026-09-13 03:16:23 | 2026-09-13 03:16:33 | 10s | 0 |
| 25 | `comparar_final` | 2026-09-13 03:16:33 | 2026-09-13 03:16:43 | 10s | 0 |
| 26 | `relatorio_antigravity` | 2026-09-13 03:16:43 | 2026-09-13 03:16:43 | 0s | 1 |
| 27 | `golden_v3_cadeias` | 2026-09-13 03:17:26 | 2026-09-13 03:17:38 | 12s | 0 |
| 28 | `ri_japeri_piloto_cadeias` | 2026-09-13 03:17:38 | 2026-09-13 03:17:57 | 19s | 0 |
| 29 | `comparar_pos_correcao` | 2026-09-13 03:17:57 | 2026-09-13 03:18:07 | 10s | 0 |
| 30 | `diagnostico_antigravity` | 2026-09-13 03:18:07 | 2026-09-13 03:22:50 | 4m43s (283s) | 0 |

### Detalhe do passo com código diferente de zero (`relatorio_antigravity`)

- **Passo:** `relatorio_antigravity` (passo 26, código 1)
- **Log em `orquestracao/logs/noite_v3/relatorio_antigravity.log`:**
  ```text
  Traceback (most recent call last):
    File "C:\Users\pedro\dev\tcc-ri-reading-order\orquestracao\despachar.py", line 285, in <module>
      main()
    File "C:\Users\pedro\dev\tcc-ri-reading-order\orquestracao\despachar.py", line 186, in main
      with open(a.prompt, encoding="utf-8") as f:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  FileNotFoundError: [Errno 2] No such file or directory: 'orquestracao/prompts/T13_relatorio_noite_v3.md'
  ```
- **Causa provável:** O arquivo de prompt `orquestracao/prompts/T13_relatorio_noite_v3.md` foi propositalmente renomeado pelo Claude para impedir a geração prematura de um relatório com os números não corrigidos da busca em feixe, sendo substituído após o script de correção pelo prompt definitivo executado nesta sessão.

*Leitura da seção:* O pipeline noturno concluiu com sucesso 29 de suas 30 etapas, totalizando mais de 2 horas de execução contínua com treinos locais, curva de aprendizado e ablações.

---

## 2. Segmentação v1 → v3

**Fontes dos dados:**
- `resultados/qualidade_segmentacao_v3_blocos.json` (data: 2026-09-12 23:21:31)
- `resultados/qualidade_segmentacao_v3_blocos_extra.json` (data: 2026-09-13 01:29:57)
- `resultados/qualidade_segmentacao_v3_blocos_ri_japeri.json` (data: 2026-09-13 01:31:44)

| Coleção | Estado | Páginas | Blocos/página | Blocos sobrepostos | % Blocos sobrepostos | Blocos de 1 palavra | % Blocos 1 palavra |
|---|---|---:|---:|---:|---:|---:|---:|
| `blocos` (`data/processed/blocos`) | Antes (v1) | 777 | 48,2 | 9.368 | 25,00% | 12.087 | 32,26% |
| | Depois (v3) | 754 | 30,6 | 999 | 4,33% | 2.098 | 9,09% |
| `blocos_extra` (`data/processed/blocos_extra`) | Antes (v1) | 3.117 | 61,8 | 42.955 | 22,29% | 60.502 | 31,39% |
| | Depois (v3) | 3.071 | 38,1 | 4.665 | 3,99% | 8.664 | 7,41% |
| `blocos_ri_japeri` (`data/processed/blocos_ri_japeri`) | Antes (v1) | 269 | 39,2 | 2.655 | 25,17% | 3.068 | 29,08% |
| | Depois (v3) | 269 | 19,8 | 110 | 2,07% | 497 | 9,34% |

*Leitura da seção:* A segmentação v3 reduziu a taxa de sobreposição de blocos de ~22–25% para ~2–4% e os blocos de uma única palavra de ~29–32% para ~7–9% em todas as coleções, eliminando a fragmentação excessiva de parágrafos e tratando tabelas inteiras como blocos únicos.

---

## 3. Teste (silver) v1 → v3

**Fontes dos dados:**
- `resultados_segmentacao_v1/comparacao.json` (95 páginas de teste)
- `resultados/comparacao.json` (89 páginas de teste)

A comparação é realizada entre segmentações diferentes das mesmas páginas de teste dos veículos não vistos `official_diary_ce`, `official_diary_ma` e `official_diary_rj` (95 páginas na v1 vs. 89 páginas na v3, em que 6 páginas saíram pelo filtro de mínimo de 3 blocos por conterem quase exclusivamente tabelas consolidadas).

| Método | τ Kendall (v1, n=95) | τ Kendall (v3, n=89) | Sucessor correto (v1) | Sucessor correto (v3) | ARD norm. (v1) | ARD norm. (v3) |
|---|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | -0,005 | -0,020 | 4,8% | 6,3% | 0,330 | 0,335 |
| Ingênua (topo→base, esq.→dir.) | 0,753 | 0,790 | 52,5% | 69,0% | 0,106 | 0,092 |
| XY-cut (heurística de colunas) | 0,837 | 0,891 | 64,2% | 78,4% | 0,067 | 0,045 |
| BiLSTM: só texto | 0,066 | 0,102 | 5,5% | 5,2% | 0,309 | 0,300 |
| BiLSTM: só geometria | 0,731 | 0,801 | 27,1% | 31,4% | 0,105 | 0,080 |
| BiLSTM: texto + geometria | 0,628 | 0,711 | 15,5% | 18,5% | 0,136 | 0,109 |
| LayoutLM pontual: um escore por bloco | 0,671 | 0,800 | 13,4% | 29,8% | 0,123 | 0,080 |

*(Nota: O método `layoutlm_sucessor` não estava presente na tabela principal de `resultados_segmentacao_v1/comparacao.json`; na v3, ele atinge τ = 0,878, sucessor correto = 71,3% e ARD norm. = 0,052).*

*Leitura da seção:* Na v3, o XY-cut passa de 0,837 para 0,891 em τ e de 64,2% para 78,4% em sucessor correto, enquanto o LayoutLM pontual avança de 0,671 para 0,800 em τ e dobra sua continuidade local (13,4% para 29,8%).

---

## 4. Curva de aprendizado v1 → v3

**Fontes dos dados:**
- `resultados_segmentacao_v1/curva_aprendizado/curva.json` (tamanhos de treino: 152, 400, 1000, 2000, 3235; teste n=95)
- `resultados/curva_aprendizado/curva.json` (tamanhos de treino: 152, 400, 1000, 2000, 3189; teste n=89)

### Segmentação v1 (`resultados_segmentacao_v1/curva_aprendizado/curva.json`)

| Modelo | N = 152 | N = 400 | N = 1000 | N = 2000 | N = 3235 |
|---|---:|---:|---:|---:|---:|
| LayoutLM pontual (τ) | 0,694 | 0,721 | 0,730 | 0,761 | 0,786 |
| LayoutLM pontual (sucessor) | 15,6% | 16,8% | 15,1% | 19,1% | 20,8% |
| BiLSTM geométrica (τ) | 0,721 | 0,678 | 0,697 | 0,691 | 0,702 |
| BiLSTM geométrica (sucessor) | 24,7% | 18,6% | 18,8% | 18,1% | 17,4% |

*(O LayoutLM sucessor não constava no arquivo da curva da v1).*

### Segmentação v3 (`resultados/curva_aprendizado/curva.json`)

| Modelo | N = 152 | N = 400 | N = 1000 | N = 2000 | N = 3189 |
|---|---:|---:|---:|---:|---:|
| LayoutLM pontual (τ) | 0,707 | 0,706 | 0,757 | 0,767 | 0,800 |
| LayoutLM pontual (sucessor) | 19,2% | 20,8% | 22,6% | 22,5% | 29,8% |
| **LayoutLM sucessor (τ)** | **0,710** | **0,743** | **0,810** | **0,852** | **0,878** |
| **LayoutLM sucessor (sucessor)** | **43,2%** | **47,2%** | **55,8%** | **61,0%** | **71,3%** |
| BiLSTM geométrica (τ) | 0,796 | 0,692 | 0,748 | 0,793 | 0,761 |
| BiLSTM geométrica (sucessor) | 33,6% | 19,3% | 23,2% | 28,7% | 26,1% |

*Leitura da seção:* Na v3, o LayoutLM sucessor apresenta ganho monotônico robusto com o aumento do volume de treino, progredindo de τ 0,710 e 43,2% de sucessor (N=152) para τ 0,878 e 71,3% de sucessor (N=3.189), enquanto a BiLSTM não demonstra escalabilidade com os dados adicionais.

---

## 5. Golden (anotação humana)

**Fontes dos dados:**
- `resultados/golden/_avaliacao/golden_v3/avaliacao.md`
- `resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md`

### 5.1 Todas as páginas anotadas (n = 47)

*Copiada de `resultados/golden/_avaliacao/golden_v3/avaliacao.md`*:

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 47 | **0.714** (0.594-0.822) | 0.143 | 78% | 0.109 | 21% |
| Ordem do detector (sem ordenar) | 47 | **-0.007** (-0.050-0.038) | -0.143 | 7% | 0.336 | 0% |
| Ingênua (topo→base, esq.→dir.) | 47 | **0.781** (0.722-0.842) | 0.510 | 60% | 0.098 | 32% |
| XY-cut (heurística de colunas) | 47 | **0.851** (0.796-0.901) | 0.556 | 74% | 0.068 | 23% |
| LayoutLM pontual: um escore por bloco | 47 | **0.846** (0.809-0.880) | 0.702 | 33% | 0.062 | 6% |
| LayoutLM sucessor: prevê o próximo bloco | 47 | **0.845** (0.780-0.897) | 0.600 | 67% | 0.066 | 9% |

### 5.2 Grupo `incerto` (n = 26)

*Copiada de `resultados/golden/_avaliacao/golden_v3/avaliacao.md`*:

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 26 | **0.544** (0.349-0.708) | -0.333 | 68% | 0.169 | 8% |
| Ordem do detector (sem ordenar) | 26 | **-0.024** (-0.094-0.044) | -0.222 | 7% | 0.341 | 0% |
| Ingênua (topo→base, esq.→dir.) | 26 | **0.795** (0.706-0.882) | 0.502 | 61% | 0.092 | 27% |
| XY-cut (heurística de colunas) | 26 | **0.834** (0.758-0.909) | 0.505 | 72% | 0.077 | 27% |
| LayoutLM pontual: um escore por bloco | 26 | **0.861** (0.810-0.901) | 0.712 | 36% | 0.056 | 4% |
| LayoutLM sucessor: prevê o próximo bloco | 26 | **0.851** (0.795-0.904) | 0.600 | 64% | 0.062 | 4% |

### 5.3 Grupo `silver` (n = 21)

*Copiada de `resultados/golden/_avaliacao/golden_v3/avaliacao.md`*:

| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |
|---|---:|---:|---:|---:|---:|---:|
| Fluxo do PDF (referência silver) | 21 | **0.925** (0.844-0.984) | 0.814 | 89% | 0.034 | 38% |
| Ordem do detector (sem ordenar) | 21 | **0.014** (-0.027-0.062) | -0.098 | 6% | 0.331 | 0% |
| Ingênua (topo→base, esq.→dir.) | 21 | **0.765** (0.683-0.852) | 0.524 | 59% | 0.107 | 38% |
| XY-cut (heurística de colunas) | 21 | **0.873** (0.805-0.936) | 0.616 | 76% | 0.056 | 19% |
| LayoutLM pontual: um escore por bloco | 21 | **0.828** (0.771-0.875) | 0.702 | 29% | 0.069 | 10% |
| LayoutLM sucessor: prevê o próximo bloco | 21 | **0.837** (0.715-0.932) | 0.717 | 71% | 0.071 | 14% |

### 5.4 Resumo da seção "Correção de 13/09" (`diagnostico_sucessor.md`)

O diagnóstico refeito registrou o impacto direto da mudança de busca em feixe para decodificação em cadeias (limiar 0,5) no Golden (`golden_v3`, n=47):

| Métrica | Antes (Busca em Feixe) | Depois (Decodificação em Cadeias) | Variação (Δ) |
|---|---:|---:|---:|
| τ de Kendall Médio | 0,699 | **0,845** | **+0,146** |
| τ no Percentil 10 (p10) | 0,275 | **0,591** | **+0,316** |
| Sucessor Correto Médio | 67,1% | **66,8%** | **-0,3 p.p.** |
| Diferença vs LayoutLM Pontual (τ) | -0,147 (0,699 vs 0,846) | **-0,001** (0,845 vs 0,846) | Empate técnico |
| Diferença vs XY-cut (τ) | -0,152 (0,699 vs 0,851) | **-0,007** (0,845 vs 0,851) | Diferença residual |

**Revisão das três hipóteses formuladas anteriormente:**
1. **Hipótese 1 (Falha de ancoragem de cabeçalhos): Refutou-se o colapso generalizado.** Casos antes desastrosos recuperaram-se (PI p223 foi de τ 0,143 para 0,714; PI p0 foi de 0,543 para 0,981). O erro residual decorre de pequenos blocos periféricos sem aresta forte e de inversão macro entre colunas cujos blocos internos foram encadeados perfeitamente (caso MA p14, com 90,6% de acerto local mas τ 0,027 por ler a coluna 2 antes da 1).
2. **Hipótese 2 (Degradação com número de colunas): Caiu.** O modelo em cadeias sustenta τ > 0,81 em todas as configurações: em 3 colunas, o τ médio subiu de 0,601 para 0,814 (em MG p28 com 99 blocos em 3 colunas, o Sucessor obteve τ 0,881 vs 0,852 do XY-cut), e em 1 coluna supera expressivamente o XY-cut (0,878 vs 0,788).
3. **Hipótese 3 (Vulnerabilidade no grupo incerto): Caiu completamente.** No grupo `incerto` (veículos e layouts novos), o Sucessor alcança τ 0,851, superando o grupo `silver` (0,837) e superando o próprio XY-cut no grupo incerto (0,834).

*Leitura da seção:* A anotação humana confirma a validade da referência silver onde ela se aplica (τ 0,925 do fluxo no grupo silver) e mostra que, com a decodificação em cadeias, o LayoutLM sucessor empata com o modelo pontual em τ (0,845 vs 0,846) dobrando a continuidade do texto (67% vs 33%).

---

## 6. Ablações e limiar

**Fonte dos dados:** `resultados/comparacao.json` e `resultados/comparacao.md` (n = 89 páginas de teste)

| Método | τ Kendall | τ p10 | Sucessor correto | ARD | ARD norm. | BLEU | Acerto exato | Latência (ms/pág.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ablacao_suc_sem_layout` | **0,216** | -0,075 | 30,6% | 9,29 | 0,266 | 97,5 | 4,5% | 19,2 |
| `ablacao_suc_sem_posicao` | **0,374** | -0,178 | 65,5% | 9,03 | 0,246 | 98,7 | 13,5% | 19,2 |
| `ablacao_suc_sem_vies_geo` | **0,853** | 0,556 | 67,1% | 1,93 | 0,057 | 98,9 | 20,2% | 18,1 |
| `layoutlm_sucessor_feixe` | **0,754** | 0,281 | 71,3% | 4,30 | 0,096 | 98,9 | 15,7% | 20,8 |
| `suc_limiar_00` | **0,756** | 0,208 | 72,9% | 4,48 | 0,103 | 99,0 | 19,1% | 20,5 |
| `suc_limiar_03` | **0,855** | 0,600 | 71,6% | 2,12 | 0,062 | 98,9 | 19,1% | 19,1 |
| **`layoutlm_sucessor` (limiar 0,5)** | **0,878** | **0,666** | **71,3%** | **1,96** | **0,052** | **98,9** | **21,3%** | **18,5** |
| `suc_limiar_07` | **0,873** | 0,677 | 66,6% | 2,10 | 0,054 | 98,8 | 18,0% | 20,2 |
| `suc_limiar_09` | **0,860** | 0,719 | 55,8% | 2,18 | 0,058 | 98,4 | 13,5% | 19,3 |

*Leitura da seção:* As ablações comprovam que a geometria 2D é essencial para a ordenação (sem caixas de layout o τ despenca para 0,216), que a decodificação em feixe degrada significativamente o ranking global em relação a cadeias (0,754 vs 0,878), e que o limiar 0,5 estabelece o equilíbrio ideal entre correlação global e sucessores locais.

---

## 7. RI em Japeri e latência

**Fontes dos dados:**
- `resultados/ri_japeri/resultado.md` (v3, após correção)
- `resultados_segmentacao_v1/ri_japeri/resultado.md` (v1)
- `resultados/latencia_rtx4050_v3.json`

### 7.1 Piloto de RI em Japeri (269 páginas, 27 edições)

Consultas avaliadas:
- v1: 326 frase, 266 título, 323 termos
- v3: 281 frase, 266 título, 310 termos

Teto de frases preservadas por pelo menos um método: **54,6% na v1** vs. **92,2% na v3**.

| Método | Frases preservadas (v1) | Frases preservadas (v3) | Dif. piso (v3) | Contexto RAG (v1) | Contexto RAG (v3) | MRR@10 frase (v3) | MRR@10 título (v3) | MRR@10 termos (v3) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 45,4% | 85,1% | +0,0 p.p. | 44,8% | 82,9% | 0,991 | 0,992 | 0,990 |
| Fluxo do PDF (extração comum) | 53,4% | 92,2% | +7,1 p.p. | 52,8% | 91,8% | 1,000 | 0,994 | 0,991 |
| Ingênua (topo→base, esq.→dir.) | 48,8% | 88,3% | +3,2 p.p. | 48,5% | 87,2% | 1,000 | 0,996 | 0,992 |
| XY-cut (heurística de colunas) | 49,7% | 89,3% | +4,3 p.p. | 49,4% | 87,9% | 1,000 | 0,996 | 0,992 |
| LayoutLM pontual | 45,7% | 85,8% | +0,7 p.p. | 44,8% | 85,1% | 1,000 | 0,988 | 0,994 |
| LayoutLM sucessor (cadeias) | *(não medido)* | **90,4%** | **+5,3 p.p.** | *(não medido)* | **89,7%** | **1,000** | **0,992** | **0,993** |

### 7.2 Latência de Inferência por Hardware

**Arquivo:** `resultados/latencia_rtx4050_v3.json`  
**Ambiente:** Intel Core i7 (20 núcleos lógicos), NVIDIA GeForce RTX 4050 Laptop GPU (6 GB), Windows 11, PyTorch 2.9.1+cu128, 89 páginas de teste.

| Método | Média (ms/pág.) | Mediana (ms/pág.) | Percentil 90 (ms/pág.) |
|---|---:|---:|---:|
| Ingênua (`naive`) | 0,008 ms | 0,006 ms | 0,016 ms |
| XY-cut (`xycut`) | 0,061 ms | 0,044 ms | 0,122 ms |
| BiLSTM geométrica (`lstm_geo`) | 4,245 ms | 3,281 ms | 7,394 ms |
| LayoutLM pontual (`layoutlm`) | 11,876 ms | 11,605 ms | 13,222 ms |
| LayoutLM sucessor (`layoutlm_sucessor`) | 16,652 ms | 15,425 ms | 23,121 ms |

*(Na segmentação v1 não havia arquivo `latencia_*.json` dedicado; as latências médias registradas na tabela do teste de 95 páginas em `resultados_segmentacao_v1/comparacao.json` foram: naive 0,015 ms, XY-cut 0,141 ms, BiLSTM geo 7,068 ms e LayoutLM pontual 18,029 ms).*

*Leitura da seção:* Na v3, o teto de frases de atos preservadas salta de 54,6% para 92,2%, com o LayoutLM sucessor alcançando 90,4% de preservação e 89,7% de trechos úteis para RAG operando a 16,7 ms por página na GPU.

---

## 8. O que falta o Pedro fazer

1. **Conferência do pacote Kaggle:**
   - O pacote foi gerado com sucesso no passo `pacote_kaggle` em 2026-09-13 01:30:57 (log `orquestracao/logs/noite_v3/pacote_kaggle.log`).
   - Arquivo gerado: `dist/kaggle/tcc_ordem_leitura.zip` (12.564.464 bytes, ~12,0 MB), contendo 83 arquivos incluindo o código, os blocos extraídos na v3 e os dois lotes anotados do Golden Dataset.
2. **Ações pendentes do Pedro:**
   - Fazer upload de `dist/kaggle/tcc_ordem_leitura.zip` como **nova versão do dataset** no Kaggle.
   - Executar **apenas** o notebook `kaggle_llm_ordem.ipynb` (as LLMs de 27–35B excedem os 6 GB da RTX 4050 local e requerem o ambiente de nuvem com GPUs T4).
   - **Não** é necessário rodar o notebook `kaggle_treino_ordem.ipynb`: todos os treinos locais, curva completa de aprendizado em 5 pontos, varreduras de limiar e ablações já foram integralmente processados durante a noite.
   - Seguir o roteiro descrito em `docs/KAGGLE.md` para a importação posterior das predições das LLMs.

---

## 9. Rodada extra: sementes e ablações no Golden

Executada pelo roteiro `orquestracao/noite_v3_extra.sh` para avaliar a variância amostral entre sementes de treino (sementes 1 e 2, além da 42 do roteiro principal) nas duas formulações do LayoutLM (treino ampliado com 3.189 páginas), a ablação sem layout 2D do modelo pontual (`layoutlm_sem_layout`) e o comportamento de todas as ablações frente à anotação humana do Golden Dataset.

### 9.1 Status dos passos da rodada extra

**Fonte dos dados:** `orquestracao/logs/noite_v3/status.jsonl`

| # | Passo | Início | Fim | Duração | Código de saída |
|---|---|---|---|---:|---:|
| 32 | `layoutlm_sem_layout_treinar` | 2026-09-13 03:28:17 | 2026-09-13 03:36:54 | 8m37s (517s) | 0 |
| 33 | `layoutlm_sem_layout_avaliar` | 2026-09-13 03:36:54 | 2026-09-13 03:37:04 | 10s | 0 |
| 34 | `sucessor_seed1_treinar` | 2026-09-13 03:37:04 | 2026-09-13 03:47:09 | 10m05s (605s) | 0 |
| 35 | `sucessor_seed1_avaliar` | 2026-09-13 03:47:09 | 2026-09-13 03:47:19 | 10s | 0 |
| 36 | `pontual_seed1_treinar` | 2026-09-13 03:47:19 | 2026-09-13 03:56:00 | 8m41s (521s) | 0 |
| 37 | `pontual_seed1_avaliar` | 2026-09-13 03:56:00 | 2026-09-13 03:56:10 | 10s | 0 |
| 38 | `sucessor_seed2_treinar` | 2026-09-13 03:56:10 | 2026-09-13 04:06:17 | 10m07s (607s) | 0 |
| 39 | `sucessor_seed2_avaliar` | 2026-09-13 04:06:17 | 2026-09-13 04:06:27 | 10s | 0 |
| 40 | `pontual_seed2_treinar` | 2026-09-13 04:06:27 | 2026-09-13 04:15:09 | 8m42s (522s) | 0 |
| 41 | `pontual_seed2_avaliar` | 2026-09-13 04:15:09 | 2026-09-13 04:15:19 | 10s | 0 |
| 42 | `golden_v3_extra` | 2026-09-13 04:15:19 | 2026-09-13 04:15:56 | 37s | 0 |
| 43 | `comparar_extra` | 2026-09-13 04:15:56 | 2026-09-13 04:16:09 | 13s | 0 |

Todos os 12 passos da rodada extra concluíram com código 0.

### 9.2 Teste, 89 páginas: variância entre sementes

**Fonte dos dados:** `resultados/comparacao.json` (campo `todas_as_paginas`)

| Formulação | Semente | τ Kendall | Sucessor correto | ARD normalizado |
|---|---|---:|---:|---:|
| LayoutLM pontual | 42 (roteiro principal) | 0,800 (0,7996) | 29,8% (29,75%) | 0,080 (0,0800) |
| LayoutLM pontual | 1 | 0,820 (0,8196) | 31,6% (31,61%) | 0,072 (0,0715) |
| LayoutLM pontual | 2 | 0,814 (0,8142) | 30,0% (30,04%) | 0,074 (0,0744) |
| **LayoutLM pontual** | **Média** | **0,811 (0,8111)** | **30,5% (30,47%)** | **0,075 (0,0753)** |
| **LayoutLM pontual** | **Desvio-padrão amostral** | **0,010 (0,0103)** | **1,0% (1,00%)** | **0,004 (0,0043)** |
| LayoutLM sucessor | 42 (roteiro principal) | 0,878 (0,8778) | 71,3% (71,34%) | 0,052 (0,0517) |
| LayoutLM sucessor | 1 | 0,849 (0,8489) | 57,3% (57,32%) | 0,061 (0,0607) |
| LayoutLM sucessor | 2 | 0,894 (0,8944) | 73,0% (73,05%) | 0,044 (0,0437) |
| **LayoutLM sucessor** | **Média** | **0,874 (0,8737)** | **67,2% (67,24%)** | **0,052 (0,0520)** |
| **LayoutLM sucessor** | **Desvio-padrão amostral** | **0,023 (0,0230)** | **8,6% (8,63%)** | **0,009 (0,0085)** |

### 9.3 Golden, 47 páginas: sementes e comparação com XY-cut

**Fonte dos dados:** `resultados/golden/_avaliacao/golden_v3/avaliacao.json` (campo `geral`)

| Formulação / Método | Semente | τ Kendall | Sucessor correto | ARD normalizado |
|---|---|---:|---:|---:|
| XY-cut (referência) | — | 0,851 (0,8514) | 74,0% (73,98%) | 0,068 (0,0677) |
| LayoutLM pontual | 42 (roteiro principal) | 0,846 (0,8458) | 32,8% (32,79%) | 0,062 (0,0617) |
| LayoutLM pontual | 1 | 0,879 (0,8794) | 42,0% (41,98%) | 0,048 (0,0482) |
| LayoutLM pontual | 2 | 0,866 (0,8662) | 37,9% (37,85%) | 0,054 (0,0536) |
| **LayoutLM pontual** | **Média** | **0,864 (0,8638)** | **37,5% (37,54%)** | **0,055 (0,0545)** |
| **LayoutLM pontual** | **Desvio-padrão amostral** | **0,017 (0,0169)** | **4,6% (4,60%)** | **0,007 (0,0068)** |
| LayoutLM sucessor | 42 (roteiro principal) | 0,845 (0,8448) | 66,8% (66,77%) | 0,066 (0,0658) |
| LayoutLM sucessor | 1 | 0,865 (0,8653) | 61,1% (61,07%) | 0,056 (0,0565) |
| LayoutLM sucessor | 2 | 0,882 (0,8818) | 67,6% (67,59%) | 0,050 (0,0497) |
| **LayoutLM sucessor** | **Média** | **0,864 (0,8639)** | **65,1% (65,14%)** | **0,057 (0,0573)** |
| **LayoutLM sucessor** | **Desvio-padrão amostral** | **0,019 (0,0185)** | **3,6% (3,55%)** | **0,008 (0,0080)** |

### 9.4 Ablações no Golden (47 páginas)

**Fonte dos dados:** `resultados/golden/_avaliacao/golden_v3/avaliacao.json` (campo `geral`)

| Modelo / Variante | Tipo | τ Kendall | Sucessor correto | ARD normalizado |
|---|---|---:|---:|---:|
| LayoutLM pontual (semente 42) | Modelo completo | 0,846 (0,8458) | 32,8% (32,79%) | 0,062 (0,0617) |
| `layoutlm_sem_layout` | Ablação (sem layout 2D) | 0,155 (0,1549) | 9,0% (9,01%) | 0,282 (0,2825) |
| LayoutLM sucessor (semente 42) | Modelo completo | 0,845 (0,8448) | 66,8% (66,77%) | 0,066 (0,0658) |
| `ablacao_suc_sem_vies_geo` | Ablação (sem viés geométrico) | 0,871 (0,8713) | 68,7% (68,66%) | 0,052 (0,0524) |
| `ablacao_suc_sem_posicao` | Ablação (sem embeddings de posição) | 0,389 (0,3888) | 65,0% (64,97%) | 0,240 (0,2397) |
| `ablacao_suc_sem_layout` | Ablação (sem layout 2D) | 0,248 (0,2477) | 30,0% (29,99%) | 0,255 (0,2551) |

### 9.5 Leitura dos resultados

No Golden (47 páginas), a diferença de τ entre as formulações do LayoutLM e o XY-cut (0,0056 no modelo pontual e 0,0066 no sucessor para a semente 42; ou 0,0124 no pontual e 0,0125 no sucessor para a média das três sementes) é **menor** do que o desvio-padrão amostral entre sementes (0,0169 no pontual e 0,0185 no sucessor).

### 9.6 Comando de cálculo das médias e desvios-padrão

As médias e desvios-padrão amostrais (`statistics.mean` e `statistics.stdev`, com $N-1$ graus de liberdade) foram calculados em Python diretamente dos JSONs com o comando:

```bash
venv\Scripts\python.exe -c "import json, statistics; comp = json.load(open('resultados/comparacao.json', encoding='utf-8'))['todas_as_paginas']; av = json.load(open('resultados/golden/_avaliacao/golden_v3/avaliacao.json', encoding='utf-8'))['geral']; [(print(f'=== {name} {k} ==='), print(f'media={statistics.mean([d[k] for d in g]):.4f}, stdev={statistics.stdev([d[k] for d in g]):.4f}')) for name, g in [('teste_pontual', [comp['layoutlm'], comp['pontual_seed1'], comp['pontual_seed2']]), ('teste_sucessor', [comp['layoutlm_sucessor'], comp['sucessor_seed1'], comp['sucessor_seed2']]), ('golden_pontual', [av['layoutlm'], av['pontual_seed1'], av['pontual_seed2']]), ('golden_sucessor', [av['layoutlm_sucessor'], av['sucessor_seed1'], av['sucessor_seed2']])] for k in ['tau', 'sucessor', 'ard_norm']]"
```
