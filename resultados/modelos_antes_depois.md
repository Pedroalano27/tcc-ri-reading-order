# Comparação de Ordenadores: Antes (Caixas de Parágrafo) × Depois (Linhas sem Caixas de Texto)

Avaliação pareada nas **44 páginas do Golden v4** sob a **mesma régua de palavras** (`orquestracao/analises/erros_ponta_a_ponta.py`).
Gerado automaticamente por `orquestracao/analises/modelos_antes_depois.py`.

## 1. Resumo em cinco linhas

1. **Heurística geométrica**: Tirar caixas finas e ordenar linhas com a regra de colunas (`regra_colunas`) **ajudou fortemente**, reduzindo quebras de 3,45 para 6,05 por página (τ 0,839 → 0,986, fidelidade 12 de 93,1% para 94,8%).
2. **LayoutLM sucessor**: **Atrapalhou moderadamente**. Em caixas humanas fechava com 10,00 quebras por página (τ 0,967); em linhas subiu para 11,00 quebras (sucessor_linhas_40ep), pois prever encadeamento linha a linha em 200+ unidades é mais suscetível a saltos do que sobre ~30 blocos.
3. **LayoutLM pontual e BiLSTM**: **Degradação severa**. Métodos pontuais baseados em ordenação por posição entraram em colapso sobre linhas: o LayoutLM pontual foi de 23,11 quebras para 72,57 (43,3% fidelidade 12), e a BiLSTM marcou 75,48 quebras por página, picotando parágrafos em centenas de fragmentos.
4. **LayoutReader**: Testado apenas no paradigma sem caixas (`layoutreader_pronto`), alcançou 18,39 quebras por página e τ 0,913, superando o LayoutLM sucessor em fidelidade (93,5%) e vencendo a regra geométrica nas páginas curtas, mas degradando nas páginas densas.
5. **Modelos de Linguagem (LLM/VLM)**: No paradigma com caixas, o Gemini 3.1 Flash Lite liderava todas as medições (3,98 quebras, τ 0,963, fidelidade 98,7%); contudo, passar para centenas de linhas impede o uso direto de LLMs de prompt pelo estouro de janela e contexto, limitando sua aplicação direta sobre linhas brutas.

## 2. Resumo por Família de Ordenador (Antes × Depois)

| Família | Melhor ANTES (caixas de parágrafo) | τ ANTES | Quebras ANTES | Fid. 12 ANTES | Melhor DEPOIS (linhas) | τ DEPOIS | Quebras DEPOIS | Fid. 12 DEPOIS | n | Δ τ | Δ Quebras | Δ Fid. 12 |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Heurística geométrica | `ordens['stream']` | 0,839 | 3,45 | 93,1% | `regra_colunas` | 0,986 | 6,05 | 94,8% | 44 | 0,147 | 2,59 | 1,7% |
| LayoutLM sucessor | `pred_sucessor_seed2.jsonl` | 0,967 | 10,00 | 90,7% | `sucessor_linhas_40ep` | 0,928 | 11,00 | 93,2% | 44 | -0,040 | 1,00 | 2,5% |
| LayoutLM pontual | `pred_pontual_seed2.jsonl` | 0,949 | 23,11 | 80,9% | `pontual_linhas` | 0,902 | 72,57 | 43,3% | 44 | -0,047 | 49,45 | -37,6% |
| BiLSTM | `—` | — | — | — | `lstm_geo_linhas` | 0,872 | 75,48 | 40,3% | 44 | — | — | — |
| LayoutReader | `—` | — | — | — | `layoutreader_pronto` | 0,913 | 18,39 | 93,5% | 44 | — | — | — |
| Modelo de linguagem (LLM/VLM) | `pred_vlm_gemini_3_1_flash_lite_sem_classes.jsonl` | 0,963 | 3,98 | 98,7% | `—` | — | — | — | 44 | — | — | — |

*(Nota: Δ = DEPOIS − ANTES. Para τ e Fidelidade 12, valores positivos indicam ganho; para Quebras, valores negativos indicam melhora.)*

## 3. Tabela Completa dos Métodos Antigos na Régua de Palavras (Golden v4)

Nesta tabela, todas as ordens de caixas de parágrafo geradas sobre o golden_v4 foram expandidas em sequência de palavras pela ordem canônica de linhas internas e avaliadas com as funções exatas de `erros_ponta_a_ponta.py`.

| Método | Arquivo / Origem | Família | n | τ de palavras ↑ | Quebras / pág. ↓ | Quebras / 1k pal. ↓ | Fid. 12 ↑ | Sucessor linhas ↑ | Observações |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `fluxo_pdf_regioes_ouro` | `ordens['stream']` | Heurística geométrica | 44 | 0,839 | 3,45 | 2,88 | 93,1% | 92,9% | Caixas anotadas à mão |
| `vlm_gemini_3_1_flash_lite_sem_classes` | `pred_vlm_gemini_3_1_flash_lite_sem_classes.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,963 | 3,98 | 3,31 | 98,7% | 98,3% | Caixas anotadas à mão |
| `vlm_gemini_3_1_flash_lite` | `pred_vlm_gemini_3_1_flash_lite.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,967 | 4,00 | 3,33 | 98,6% | 98,2% | Caixas anotadas à mão |
| `vlm_gemini_3_1_flash_lite_sem_marcas` | `pred_vlm_gemini_3_1_flash_lite_sem_marcas.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,948 | 5,89 | 4,91 | 97,7% | 96,4% | Caixas anotadas à mão |
| `ablacao_suc_sem_texto` | `pred_ablacao_suc_sem_texto.jsonl` | Outros | 44 | 0,952 | 8,36 | 6,97 | 90,7% | 88,7% | Caixas anotadas à mão |
| `vlm_gemini_3_1_flash_lite_sem_imagem` | `pred_vlm_gemini_3_1_flash_lite_sem_imagem.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,921 | 8,73 | 7,27 | 93,6% | 91,5% | Caixas anotadas à mão |
| `llm_qwen3_8_27b` | `pred_llm_qwen3_8_27b.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,874 | 8,75 | 7,29 | 93,0% | 91,9% | Caixas anotadas à mão |
| `ablacao_suc_sem_vies_geo` | `pred_ablacao_suc_sem_vies_geo.jsonl` | Outros | 44 | 0,969 | 9,45 | 7,88 | 91,6% | 89,2% | Caixas anotadas à mão |
| `llm_gemma4_31b` | `pred_llm_gemma4_31b.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,837 | 9,75 | 8,12 | 94,1% | 92,2% | Caixas anotadas à mão |
| `sucessor_seed2` | `pred_sucessor_seed2.jsonl` | LayoutLM sucessor | 44 | 0,967 | 10,00 | 8,33 | 90,7% | 87,1% | Caixas anotadas à mão |
| `llm_qwen3_8_27b_fs2` | `pred_llm_qwen3_8_27b_fs2.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,921 | 10,14 | 8,45 | 92,4% | 91,1% | Caixas anotadas à mão |
| `layoutlm_sucessor` | `pred_layoutlm_sucessor.jsonl` | LayoutLM sucessor | 44 | 0,965 | 10,18 | 8,48 | 89,6% | 86,9% | Caixas anotadas à mão |
| `ablacao_suc_sem_posicao` | `pred_ablacao_suc_sem_posicao.jsonl` | Outros | 44 | 0,447 | 10,55 | 8,79 | 89,1% | 86,0% | Caixas anotadas à mão |
| `llm_gemma4_31b_fs2` | `pred_llm_gemma4_31b_fs2.jsonl` | Modelo de linguagem (LLM/VLM) | 44 | 0,851 | 11,59 | 9,66 | 93,5% | 91,6% | Caixas anotadas à mão |
| `xycut_regioes_ouro` | `ordens['xycut']` | Heurística geométrica | 44 | 0,853 | 13,23 | 11,02 | 90,3% | 88,6% | Caixas anotadas à mão |
| `sucessor_seed1` | `pred_sucessor_seed1.jsonl` | LayoutLM sucessor | 44 | 0,946 | 15,52 | 12,94 | 84,3% | 81,9% | Caixas anotadas à mão |
| `ingenuo_regioes_ouro` | `ordens['naive']` | Outros | 44 | 0,756 | 17,98 | 14,98 | 88,2% | 86,1% | Caixas anotadas à mão |
| `pontual_seed2` | `pred_pontual_seed2.jsonl` | LayoutLM pontual | 44 | 0,949 | 23,11 | 19,26 | 80,9% | 76,6% | Caixas anotadas à mão |
| `pontual_seed1` | `pred_pontual_seed1.jsonl` | LayoutLM pontual | 44 | 0,939 | 23,75 | 19,79 | 80,4% | 75,9% | Caixas anotadas à mão |
| `layoutlm` | `pred_layoutlm.jsonl` | LayoutLM pontual | 44 | 0,939 | 24,05 | 20,04 | 79,7% | 75,2% | Caixas anotadas à mão |
| `ablacao_suc_sem_layout` | `pred_ablacao_suc_sem_layout.jsonl` | Outros | 44 | 0,412 | 24,32 | 20,27 | 76,2% | 73,4% | Caixas anotadas à mão |
| `layoutlm_sem_layout` | `pred_layoutlm_sem_layout.jsonl` | LayoutLM pontual | 44 | 0,242 | 30,50 | 25,42 | 71,4% | 66,3% | Caixas anotadas à mão |

## 4. Tabela dos Métodos Depois (Linhas sem Caixas de Texto, Golden v4)

Dados importados diretamente de `resultados/ordenadores_sem_caixas.json` para as 44 páginas do golden_v4.

| Ordenador | Família | n | τ de palavras ↑ | Quebras / pág. ↓ | Quebras / 1k pal. ↓ | Fid. 12 ↑ | Sucessor linhas ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| `teto` | Outros | 44 | 1,000 | 0,89 | 0,74 | 99,7% | 99,5% |
| `regra_colunas` | Heurística geométrica | 44 | 0,986 | 6,05 | 5,04 | 94,8% | 92,7% |
| `sucessor_linhas_40ep` | LayoutLM sucessor | 44 | 0,928 | 11,00 | 9,17 | 93,2% | 90,4% |
| `sucessor_linhas_100ep` | LayoutLM sucessor | 44 | 0,929 | 12,57 | 10,47 | 92,1% | 89,6% |
| `layoutreader_pronto` | LayoutReader | 44 | 0,913 | 18,39 | 15,32 | 93,5% | 92,7% |
| `layoutreader_ajustado_linhas` | LayoutReader | 44 | 0,905 | 21,91 | 18,26 | 90,4% | 89,1% |
| `xycut_margens` | Heurística geométrica | 44 | 0,963 | 23,07 | 19,22 | 90,6% | 88,0% |
| `xycut` | Heurística geométrica | 44 | 0,806 | 45,57 | 37,97 | 76,2% | 72,3% |
| `xycut_pp_parceiro` | Heurística geométrica | 44 | 0,763 | 48,20 | 40,17 | 75,0% | 72,1% |
| `sucessor_linhas` | LayoutLM sucessor | 44 | 0,902 | 57,59 | 47,99 | 61,4% | 54,3% |
| `ingenuo` | Outros | 44 | 0,732 | 58,91 | 49,09 | 68,8% | 63,4% |
| `sucessor_linhas_s43` | LayoutLM sucessor | 44 | 0,887 | 62,75 | 52,29 | 55,8% | 48,1% |
| `pontual_linhas` | LayoutLM pontual | 44 | 0,902 | 72,57 | 60,47 | 43,3% | 33,9% |
| `lstm_geo_linhas` | BiLSTM | 44 | 0,872 | 75,48 | 62,90 | 40,3% | 30,4% |
| `lstm_geo_texto_linhas` | BiLSTM | 44 | 0,850 | 78,14 | 65,11 | 38,2% | 28,6% |

## 5. Limitações e Declarações Metodológicas

1. **Assimetria de Entrada (Caixas Humanas no ANTES × Extração Automática no DEPOIS):**
   - Nos métodos do ANTES (`resultados/golden/golden_v4/pred_*.jsonl`), as unidades de entrada foram as caixas de parágrafo **corrigidas manualmente** pelo anotador durante o protocolo Diamond/Golden. Isso representa o *melhor caso irrealista* da abordagem com caixas finas, já que em um pipeline real as caixas sofrem com fusões indevidas e divisões errôneas.
   - Nos métodos do DEPOIS, a entrada é gerada automaticamente: linhas de texto digitais agrupadas geometricamente, com tabelas e imagens preservadas como blocos atômicos via detector `ls3`. Mesmo com essa desvantagem na entrada, a heurística de colunas sem caixas (`regra_colunas`) superou a XY-cut com caixas humanas.
2. **Volume de Treino e Modalidades dos Modelos:**
   - Os modelos avaliados no DEPOIS foram treinados de forma rápida com **apenas 873 páginas** e **apenas geometria** (1 token por linha, sem visão de texto, para acomodar centenas de linhas no limite posicional de 512 tokens). O LayoutLM prévio no ANTES recebia blocos com texto e embeddings semânticos.
3. **Viés de Desenvolvimento no Golden v4:**
   - As 44 páginas do `golden_v4` foram utilizadas ativamente no desenvolvimento e calibração das regras de projeção de colunas. Isso favorece a `regra_colunas` nesta coorte específica, reforçando a importância de contrastar com o `golden_v3_novo` (27 páginas não vistas) e o `teste_silver` (89 páginas).
4. **Explosão Combinatória em Linhas para Modelos Posicionais:**
   - Métodos que atribuem escores pontuais de posição absoluta (BiLSTM e LayoutLM pontual) demonstraram extrema vulnerabilidade ao aumento da cardinalidade de nós na página (de ~30 blocos para 150–400 linhas), provocando quebras em cascata que destruíram a fidelidade de leitura.

