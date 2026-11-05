# Registro de experimentos

Gerado por `src/exp/registro.py tabela` a partir de `registro.jsonl`. Não editar à mão.

## Cartões

| ID | Título | Execuções | Último veredito |
|---|---|---:|---|
| [E001](cards/E001_teste_cego_lacrado_e_desenvolvimento_nov.md) | E001 — Teste cego lacrado e desenvolvimento novo | 1 | controle |
| [E002](cards/E002_oraculos_do_grafo_e_do_roteamento_por_pa.md) | E002 — Oraculos do grafo e do roteamento por pagina | 1 | melhorou |
| [E003](cards/E003_lm_causal_contrastivo_nas_arestas.md) | E003 — LM causal contrastivo nas arestas | 2 | piorou |
| [E004](cards/E004_grafo_de_arestas_aprendidas_lightgbm_com.md) | E004 — Grafo de arestas aprendidas (LightGBM) com decodificação global | 1 | inconclusivo |
| [E005](cards/E005_seletor_de_m_todo_por_p_gina_regra_x_lay.md) | E005 — Seletor de método por página (regra x LayoutReader x grafo) | 1 | inconclusivo |
| [E006](cards/E006_correcao_residual_local_guiada_pelo_mode.md) | E006 — Correcao residual local guiada pelo modelo de arestas do E004 | 1 | abandonado |
| [E008](cards/E008_anotacao_densa_x_simplificada_teste_cruz.md) | E008 — Anotacao densa x simplificada (teste cruzado com cronometro) | 0 | planejado |
| [E009](cards/E009_representacao_para_inferencia_caixas_aut.md) | E009 — Representacao para inferencia: caixas automaticas x linhas automaticas | 1 | inconclusivo |
| [E012](cards/E012_dados_da_data_policy_bancada_humana_extr.md) | E012 — Dados da Data Policy: bancada humana extra (126 paginas, 29 veiculos) e supervisao entre regioes | 1 | controle |
| [E014](cards/E014_grafo_do_e004_com_ordenacao_das_cadeias.md) | E014 — Grafo do E004 com ordenacao das cadeias pela regra (recuperar o tau) | 1 | abandonado |
| [E015](cards/E015_cadeias_do_grafo_ordenadas_pela_mediana_.md) | E015 — Cadeias do grafo ordenadas pela mediana da regra: externas e falha catastrofica | 1 | abandonado |
| [E016](cards/E016_oraculo_e_decodificacao_hierarquica_linh.md) | E016 — Oraculo e decodificacao hierarquica: linhas dentro de segmentos, segmentos ordenados globalmente | 1 | abandonado |
| [E017](cards/E017_hier_1_congelado_nas_externas_golden_v3_.md) | E017 — HIER-1 congelado nas externas (golden_v3_novo e teste silver) | 1 | melhorou |

## Execuções

| ID | Quando | Commit | Ambiente | Bancada | τ | Quebras/pág | Sucessor | Veredito | Nota |
|---|---|---|---|---|---:|---:|---:|---|---|
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v4/regra_colunas | 0,986 | 6,045 | 0,927 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v4/oraculo_decodificador_matching_K32 | 0,917 | 1,045 | 0,995 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v4/oraculo_residual | 0,990 | 1,909 | 0,986 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v4/oraculo_roteamento | 0,994 | 3,591 | 0,978 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | validacao_silver/regra_colunas | 0,957 | 16,667 | 0,911 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | validacao_silver/oraculo_decodificador_matching_K32 | 0,964 | 6,333 | 0,972 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | validacao_silver/oraculo_residual | 0,969 | 6,333 | 0,969 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v3_novo/regra_colunas | 0,960 | 9,222 | 0,911 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v3_novo/hibrido67 | 0,959 | 7,889 | 0,938 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v3_novo/oraculo_decodificador_matching_K32 | 0,943 | 1,259 | 0,992 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v3_novo/oraculo_residual | 0,962 | 2,222 | 0,977 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | golden_v3_novo/oraculo_roteamento | 0,975 | 6,000 | 0,952 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | teste_silver/regra_colunas | 0,960 | 27,449 | 0,840 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | teste_silver/hibrido67 | 0,959 | 26,427 | 0,850 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | teste_silver/oraculo_decodificador_matching_K32 | 0,940 | 19,787 | 0,887 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | teste_silver/oraculo_residual | 0,960 | 19,966 | 0,887 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E002 | 2026-11-02T18:40 | 7dd036d* | local | teste_silver/oraculo_roteamento | 0,967 | 21,225 | 0,877 | melhorou | GO (teto, usa referencia): grafo matching K32 reduz quebras 6,05->1,05 (v4), 9,2 |
| E003 | 2026-11-02T18:40 | 7dd036d* | spark | ajuste_v4_RN/melhor_config_global_r2.0 | -0,188 | 12,205 |  | piorou | Ablacao so condicional log P(tj|ti), Qwen3-8B: as 12 configs pioram (valores = D |
| E003 | 2026-11-02T18:40 | 7dd036d* | spark | ajuste_v4_RN/melhor_config_seletiva_r2.0_t1.5 | -0,014 | 20,429 |  | piorou | Ablacao so condicional log P(tj|ti), Qwen3-8B: as 12 configs pioram (valores = D |
| E001 | 2026-11-02T19:44 | 7dd036d* | local | - |  |  |  | controle | Teste cego 90 pags (CE/MA/RJ 30 cada) + dev 45; sobreposicao 0 com 1.085 PDFs to |
| E003 | 2026-11-02T20:48 | 7dd036d* | spark | ajuste_v4_RN/contrastivo_melhor_global_r2.0 | -0,158 | 17,727 |  | piorou | Contrastivo (Qwen3-8B) como decodificador: as 12 configs pioram (valores = DELTA |
| E003 | 2026-11-02T20:48 | 7dd036d* | spark | ajuste_v4_RN/contrastivo_melhor_seletiva_r2.0_t1.5 | -0,010 | 41,686 |  | piorou | Contrastivo (Qwen3-8B) como decodificador: as 12 configs pioram (valores = DELTA |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v4/grafo_K24_maxregret_t0.00 | 0,938 | 3,614 | 0,955 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | validacao_silver/grafo_K24_maxregret_t0.00 | 0,687 | 9,467 | 0,948 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v3_novo/regra | 0,960 | 9,222 | 0,911 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v3_novo/hibrido67 | 0,959 | 7,889 | 0,938 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | golden_v3_novo/grafo_K24_maxregret_t0.00 | 0,942 | 6,519 | 0,935 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | teste_silver/regra | 0,960 | 27,449 | 0,840 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | teste_silver/hibrido67 | 0,959 | 26,427 | 0,850 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E004 | 2026-11-03T00:04 | 7dd036d* | local | teste_silver/grafo_K24_maxregret_t0.00 | 0,943 | 24,146 | 0,854 | inconclusivo | NAO GO pelo criterio de tau. Quebras caem vs regra em todas (v4 -2,43; v3n -2,70 |
| E005 | 2026-11-03T00:04 | 7dd036d* | local | - |  |  |  | inconclusivo | NAO GO: nenhum seletor supera o hibrido 67 com IC<0 em LOVO (160 obs, 27 veiculo |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/grafo_K24_maxregret_t0.00 | 0,938 | 3,614 | 0,955 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/a_primeira | 0,938 | 3,614 | 0,955 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/b_mediana | 0,987 | 3,568 | 0,959 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/c_local | 0,938 | 3,727 | 0,955 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | golden_v4/d_local_margens | 0,938 | 3,841 | 0,954 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/hibrido67 | 0,959 | 17,846 | 0,916 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/grafo_K24_maxregret_t0.00 | 0,687 | 9,467 | 0,948 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/a_primeira | 0,687 | 9,467 | 0,948 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/b_mediana | 0,891 | 9,267 | 0,949 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/c_local | 0,691 | 9,467 | 0,948 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E014 | 2026-11-03T00:46 | 7dd036d* | local | validacao_silver/d_local_margens | 0,690 | 10,933 | 0,942 | abandonado | NAO GO: nenhuma variante com tau >= regra-0,005 na media v4+RN. Mas (b) mediana  |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/grafo_K24_maxregret_t0.00 | 0,938 | 3,614 | 0,955 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/b_mediana | 0,987 | 3,568 | 0,959 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/b_mediana_salvaguarda | 0,987 | 3,568 | 0,959 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v4/hibrido67_mediana_salvaguarda | 0,981 | 3,182 | 0,976 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/hibrido67 | 0,959 | 17,846 | 0,916 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/grafo_K24_maxregret_t0.00 | 0,687 | 9,467 | 0,948 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/b_mediana | 0,891 | 9,267 | 0,949 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/b_mediana_salvaguarda | 0,891 | 9,267 | 0,949 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | validacao_silver/hibrido67_mediana_salvaguarda | 0,959 | 9,462 | 0,955 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/regra | 0,960 | 9,222 | 0,911 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/hibrido67 | 0,959 | 7,889 | 0,938 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/grafo_K24_maxregret_t0.00 | 0,942 | 6,519 | 0,935 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/b_mediana | 0,942 | 6,519 | 0,935 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/b_mediana_salvaguarda | 0,942 | 6,519 | 0,935 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | golden_v3_novo/hibrido67_mediana_salvaguarda | 0,941 | 6,296 | 0,947 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/regra | 0,960 | 27,449 | 0,840 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/hibrido67 | 0,959 | 26,427 | 0,850 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/grafo_K24_maxregret_t0.00 | 0,943 | 24,146 | 0,854 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/b_mediana | 0,955 | 24,146 | 0,855 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/b_mediana_salvaguarda | 0,955 | 24,146 | 0,855 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E015 | 2026-11-03T01:19 | 7dd036d* | local | teste_silver/hibrido67_mediana_salvaguarda | 0,955 | 23,876 | 0,859 | abandonado | NAO GO: quebras vs hibrido -1,37 (v3n, IC cruza 0) e -2,28 (silver, IC<0) passam |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v4/regra_reordena | 0,986 | 5,182 | 0,936 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v4/oraculo_residual | 0,990 | 1,909 | 0,986 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v4/e006_residual | 0,978 | 4,432 | 0,952 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | validacao_silver/hibrido67 | 0,959 | 16,400 | 0,917 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | validacao_silver/oraculo_residual | 0,969 | 6,333 | 0,969 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | validacao_silver/e006_residual | 0,962 | 13,733 | 0,928 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v3_novo/regra | 0,960 | 9,222 | 0,911 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v3_novo/hibrido67 | 0,959 | 7,889 | 0,938 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v3_novo/regra_reordena | 0,960 | 7,778 | 0,926 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v3_novo/oraculo_residual | 0,962 | 2,222 | 0,977 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | golden_v3_novo/e006_residual | 0,939 | 7,074 | 0,928 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | teste_silver/regra | 0,960 | 27,449 | 0,840 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | teste_silver/hibrido67 | 0,959 | 26,427 | 0,850 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | teste_silver/regra_reordena | 0,960 | 26,449 | 0,848 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | teste_silver/oraculo_residual | 0,960 | 19,966 | 0,887 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E006 | 2026-11-03T02:31 | 7dd036d* | local | teste_silver/e006_residual | 0,953 | 24,888 | 0,854 | abandonado | NAO GO (lambda=2, M=20): quebras < reordena e < hibrido nas externas (v3n 7,07;  |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v4/A_regra | 0,980 | 5,477 | 0,930 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v4/A_hibrido67 | 0,966 | 4,750 | 0,964 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v4/B_regra | 0,986 | 6,045 | 0,927 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v4/B_hibrido67 | 0,980 | 5,136 | 0,966 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v3_novo/A_regra | 0,945 | 11,000 | 0,904 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v3_novo/A_hibrido67 | 0,970 | 8,963 | 0,931 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v3_novo/B_regra | 0,960 | 9,222 | 0,911 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | golden_v3_novo/B_hibrido67 | 0,959 | 7,889 | 0,938 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | teste_silver/A_regra | 0,953 | 23,528 | 0,860 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | teste_silver/A_hibrido67 | 0,944 | 22,742 | 0,864 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | teste_silver/B_regra | 0,960 | 27,449 | 0,840 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E009 | 2026-11-03T03:59 | 7dd036d* | local | teste_silver/B_hibrido67 | 0,959 | 26,427 | 0,850 | inconclusivo | Linhas zeram os erros dentro das unidades (v4 1,59->0,55; v3n 5,30->0,26) mas au |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/grafo_K24_maxregret_t0.00 | 0,938 | 3,614 | 0,955 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/oraculo_hierarquico | 0,994 | 2,795 | 0,966 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/oraculo_interna_segmentos_regra | 0,987 | 3,250 | 0,963 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/oraculo_segmentos_interna_grafo | 0,992 | 4,250 | 0,949 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/hier1 | 0,985 | 4,659 | 0,947 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | golden_v4/oraculo_hierarquico_quebras | 0,940 | 2,136 | 0,976 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/hibrido67 | 0,959 | 16,400 | 0,917 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/grafo_K24_maxregret_t0.00 | 0,687 | 9,467 | 0,948 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/oraculo_hierarquico | 0,980 | 8,067 | 0,959 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/oraculo_interna_segmentos_regra | 0,958 | 8,667 | 0,956 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/oraculo_segmentos_interna_grafo | 0,979 | 11,533 | 0,938 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/hier1 | 0,957 | 12,133 | 0,935 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E016 | 2026-11-03T04:54 | 7dd036d* | local | validacao_silver/oraculo_hierarquico_quebras | 0,763 | 6,467 | 0,969 | abandonado | Fase 1 NAO GO: oraculo hierarquico 2,80 quebras (tau 0,9935) > limite 1,36 (1,3x |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_todas/regra | 0,954 | 8,577 | 0,886 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_todas/hibrido67 | 0,970 | 7,179 | 0,931 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_todas/grafo_e004 | 0,909 | 6,675 | 0,920 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_todas/hier1 | 0,956 | 6,976 | 0,916 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_sem/regra | 0,950 | 9,167 | 0,894 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_sem/hibrido67 | 0,965 | 7,741 | 0,930 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_sem/grafo_e004 | 0,897 | 7,278 | 0,919 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E012 | 2026-11-05T00:03 | 6837829 | local | ls_humana_sem/hier1 | 0,950 | 7,611 | 0,915 | controle | Bancada humana Data Policy seed2 (export de out): 123 pags, 29 veiculos. Hibrido |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v4/regra | 0,986 | 6,045 | 0,927 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v4/hibrido67 | 0,980 | 5,136 | 0,966 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v4/grafo_K24_maxregret_t0.00 | 0,938 | 3,614 | 0,955 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v4/hier1 | 0,985 | 4,659 | 0,947 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v3_novo/regra | 0,960 | 9,222 | 0,911 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v3_novo/hibrido67 | 0,959 | 7,889 | 0,938 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v3_novo/grafo_K24_maxregret_t0.00 | 0,942 | 6,519 | 0,935 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | golden_v3_novo/hier1 | 0,959 | 6,667 | 0,935 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | teste_silver/regra | 0,960 | 27,449 | 0,840 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | teste_silver/hibrido67 | 0,959 | 26,427 | 0,850 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | teste_silver/grafo_K24_maxregret_t0.00 | 0,943 | 24,146 | 0,854 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | teste_silver/hier1 | 0,958 | 25,056 | 0,853 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | validacao_silver/regra | 0,957 | 16,667 | 0,911 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | validacao_silver/hibrido67 | 0,959 | 16,400 | 0,917 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | validacao_silver/grafo_K24_maxregret_t0.00 | 0,687 | 9,467 | 0,948 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |
| E017 | 2026-11-05T00:07 | 6837829* | local | validacao_silver/hier1 | 0,957 | 12,133 | 0,935 | melhorou | GO: HIER-1 congelado. v3n 6,67 / tau 0,9594 (hibrido 7,89 / 0,9590), dq -1,22 [- |

`*` = árvore de trabalho com alterações não commitadas no momento da execução.
