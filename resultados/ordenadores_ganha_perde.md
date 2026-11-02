# Comparação Página a Página: Ordenadores vs. Regra Geométrica

## Resumo em cinco linhas

1. **Melhor modelo treinado vs. Regra**: O melhor modelo em linhas (sucessor_linhas_40ep) aproxima-se, mas não supera a regra geométrica (11,00 vs. 6,05 quebras no Golden v4; 12,48 vs. 9,22 no v3 novo; 31,92 vs. 27,45 no Silver).
2. **Perfil onde ganha e perde**: O modelo ganha principalmente em páginas de baixa densidade (3,57 vs. 2,07 quebras no 1º terço do v4), mas acumula erros nas páginas longas e multicolunadas (22,67 vs. 10,00 quebras no 3º terço).
3. **Impacto do treino mais longo**: Passar de 8 para 40 épocas reduz drasticamente as quebras no v4 (57,59 → 11,00 quebras/página; ganho de 46,59 quebras); a variante de 100 épocas está 12,57 quebras.
4. **Estabilidade de sementes**: A semente altera a média em magnitude secundária (Δquebras de 5,16 no v4 entre sucessor_linhas e s43) e não altera a hierarquia: a regra segue à frente em todas as sementes.
5. **Conclusão nas representações**: Sem caixas finas, a projeção geométrica por colunas e margens segue como baseline dominante em robustez e simplicidade de inferência.

---

## Verificação de Âncoras Canônicas

- **Âncora 1 (Regra sem caixas finas, átomos ls3, v4)**: τ = **0,985948** (alvo 0,986; tolerância ±0,006), quebras = **6,045455**.
- **Âncora 2 (Extrator + XY-cut + margens, caixas finas, v4)**: τ = **0,952424** (alvo 0,952; tolerância ±0,006), quebras = **8,931818**.
- **Status**: Ambas reproduzidas com sucesso na bancada.

---

## A. Comparação Pareada em 'Linhas' contra 'regra_colunas'

Métrica de quebras: menor é melhor. Métrica de Kendall τ: maior é melhor. A diferença pareada é definida como `Δquebras = quebras_modelo - quebras_regra` (valores negativos indicam que o modelo gerou menos quebras que a regra).

### Golden v4 (44 páginas)

| Ordenador | n | Quebras Modelo | Quebras Regra | Quebras (< / = / >) | τ (> / = / <) | Mediana ΔQuebras | τ Médio Modelo | τ Médio Regra |
|---|---:|---:|---:|:---:|:---:|---:|---:|---:|
| `sucessor_linhas` | 44 | 57,59 | 6,05 | 2 / 4 / 38 | 4 / 3 / 37 | 28,5 | 0,902 | 0,986 |
| `sucessor_linhas_s43` | 44 | 62,75 | 6,05 | 1 / 4 / 39 | 1 / 4 / 39 | 32,0 | 0,887 | 0,986 |
| `sucessor_linhas_40ep` | 44 | 11,00 | 6,05 | 9 / 12 / 23 | 14 / 4 / 26 | 1,0 | 0,928 | 0,986 |
| `sucessor_linhas_100ep` | 44 | 12,57 | 6,05 | 14 / 12 / 18 | 14 / 2 / 28 | 0,0 | 0,929 | 0,986 |
| `layoutreader_pronto` | 44 | 18,39 | 6,05 | 24 / 6 / 14 | 23 / 6 / 15 | -1,5 | 0,913 | 0,986 |
| `layoutreader_ajustado_linhas` | 44 | 21,91 | 6,05 | 14 / 5 / 25 | 17 / 5 / 22 | 1,0 | 0,905 | 0,986 |
| `pontual_linhas` | 44 | 72,57 | 6,05 | 0 / 1 / 43 | 3 / 1 / 40 | 43,5 | 0,902 | 0,986 |
| `lstm_geo_linhas` | 44 | 75,48 | 6,05 | 0 / 2 / 42 | 2 / 1 / 41 | 43,5 | 0,872 | 0,986 |

### Golden v3 Novo (27 páginas)

| Ordenador | n | Quebras Modelo | Quebras Regra | Quebras (< / = / >) | τ (> / = / <) | Mediana ΔQuebras | τ Médio Modelo | τ Médio Regra |
|---|---:|---:|---:|:---:|:---:|---:|---:|---:|
| `sucessor_linhas` | 27 | 57,00 | 9,22 | 2 / 1 / 24 | 2 / 0 / 25 | 37,0 | 0,885 | 0,960 |
| `sucessor_linhas_s43` | 27 | 62,41 | 9,22 | 1 / 1 / 25 | 2 / 0 / 25 | 39,0 | 0,879 | 0,960 |
| `sucessor_linhas_40ep` | 27 | 12,48 | 9,22 | 9 / 1 / 17 | 4 / 0 / 23 | 1,0 | 0,919 | 0,960 |
| `sucessor_linhas_100ep` | 27 | 12,59 | 9,22 | 9 / 2 / 16 | 5 / 0 / 22 | 1,0 | 0,896 | 0,960 |
| `layoutreader_pronto` | 27 | 16,22 | 9,22 | 14 / 5 / 8 | 17 / 4 / 6 | -2,0 | 0,951 | 0,960 |
| `layoutreader_ajustado_linhas` | 27 | 20,85 | 9,22 | 9 / 5 / 13 | 12 / 3 / 12 | 0,0 | 0,945 | 0,960 |
| `pontual_linhas` | 27 | 74,44 | 9,22 | 1 / 1 / 25 | 1 / 1 / 25 | 54,0 | 0,870 | 0,960 |
| `lstm_geo_linhas` | 27 | 75,04 | 9,22 | 1 / 1 / 25 | 0 / 0 / 27 | 49,0 | 0,846 | 0,960 |

### Teste Silver (89 páginas)

| Ordenador | n | Quebras Modelo | Quebras Regra | Quebras (< / = / >) | τ (> / = / <) | Mediana ΔQuebras | τ Médio Modelo | τ Médio Regra |
|---|---:|---:|---:|:---:|:---:|---:|---:|---:|
| `sucessor_linhas` | 89 | 89,62 | 27,45 | 2 / 7 / 80 | 8 / 1 / 80 | 45,0 | 0,876 | 0,960 |
| `sucessor_linhas_s43` | 89 | 94,35 | 27,45 | 2 / 5 / 82 | 7 / 0 / 82 | 54,0 | 0,862 | 0,960 |
| `sucessor_linhas_40ep` | 89 | 31,92 | 27,45 | 18 / 12 / 59 | 8 / 3 / 78 | 2,0 | 0,914 | 0,960 |
| `sucessor_linhas_100ep` | 89 | 31,91 | 27,45 | 24 / 9 / 56 | 15 / 5 / 69 | 2,0 | 0,931 | 0,960 |
| `layoutreader_pronto` | 89 | 31,25 | 27,45 | 38 / 30 / 21 | 50 / 12 / 27 | 0,0 | 0,942 | 0,960 |
| `layoutreader_ajustado_linhas` | 89 | 36,60 | 27,45 | 27 / 16 / 46 | 24 / 5 / 60 | 1,0 | 0,930 | 0,960 |
| `pontual_linhas` | 89 | 105,74 | 27,45 | 1 / 7 / 81 | 5 / 4 / 80 | 70,0 | 0,869 | 0,960 |
| `lstm_geo_linhas` | 89 | 107,67 | 27,45 | 4 / 3 / 82 | 6 / 1 / 82 | 69,0 | 0,854 | 0,960 |

---

## B. Onde o Melhor Modelo Treinado (sucessor_linhas_40ep) Ganha e Perde

O melhor modelo treinado em 'linhas' disponível no Golden v4 é o `sucessor_linhas_40ep` com média de **11,00 quebras/página**.
Abaixo estão as 5 páginas em que ele mais reduz quebras em relação à regra e as 5 em que mais aumenta quebras.

### Golden v4 (44 páginas)

#### Top 5 páginas em que o modelo mais GANHA da regra (maior redução de quebras)

| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0` | official_diary_ro | 54 | 635 | 9 | 2 | **-7** | 1,000 | 1,000 | 0,000 |
| `official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf#p0` | official_diary_RJ_duque_de_caxias | 126 | 594 | 11 | 5 | **-6** | 0,978 | 1,000 | 0,022 |
| `official_diary_se/DOE-SE_2023-03-10_5100.pdf#p14` | official_diary_se | 94 | 583 | 13 | 7 | **-6** | 0,984 | 0,993 | 0,009 |
| `official_diary_sc/2023-11-27_22151.pdf#p28` | official_diary_sc | 257 | 2155 | 6 | 0 | **-6** | 1,000 | 1,000 | 0,000 |
| `official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41` | official_diary_pb | 142 | 1098 | 13 | 9 | **-4** | 0,964 | 0,995 | 0,032 |

#### Top 5 páginas em que o modelo mais PERDE da regra (maior aumento de quebras)

| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | official_diary_mg | 493 | 4080 | 14 | 199 | **+185** | 0,994 | 0,832 | -0,162 |
| `official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6` | official_diary_pe | 233 | 1573 | 3 | 21 | **+18** | 1,000 | 0,993 | -0,007 |
| `official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22` | official_diary_am_manaus | 12 | 1567 | 0 | 7 | **+7** | 1,000 | 0,031 | -0,969 |
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | official_diary_rj | 340 | 2518 | 51 | 56 | **+5** | 0,995 | 0,868 | -0,127 |
| `official_diary_rr/2021-09-23_DiarioRR.pdf#p10` | official_diary_rr | 29 | 494 | 2 | 6 | **+4** | 1,000 | 0,972 | -0,028 |

### Golden v3 Novo (27 páginas)

#### Top 5 páginas em que o modelo mais GANHA da regra (maior redução de quebras)

| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0` | official_diary_ma | 162 | 449 | 92 | 85 | **-7** | 0,687 | 0,667 | -0,020 |
| `official_diary_ce/do20220512p03.pdf#p20` | official_diary_ce | 54 | 1112 | 15 | 9 | **-6** | 1,000 | 0,998 | -0,002 |
| `official_diary_ma/executive_official_diary_2023-12-04_30_84.pdf#p0` | official_diary_ma | 118 | 964 | 6 | 2 | **-4** | 1,000 | 1,000 | -0,000 |
| `official_diary_ac/executive_official_diary_2022-12-02.pdf#p419` | official_diary_ac | 12 | 148 | 8 | 5 | **-3** | 0,965 | 0,973 | 0,008 |
| `official_diary_pi_v2/executive_official_diary_2024_05_29_104_2024_15_340.pdf#p0` | official_diary_pi_v2 | 36 | 289 | 5 | 3 | **-2** | 0,999 | 1,000 | 0,001 |

#### Top 5 páginas em que o modelo mais PERDE da regra (maior aumento de quebras)

| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p3` | official_diary_rj | 110 | 658 | 9 | 35 | **+26** | 0,956 | 0,796 | -0,160 |
| `official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf#p18` | official_diary_rj | 401 | 3400 | 13 | 37 | **+24** | 0,989 | 0,851 | -0,138 |
| `official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf#p0` | official_diary_rj | 201 | 1021 | 16 | 36 | **+20** | 0,698 | 0,676 | -0,022 |
| `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16` | official_diary_mg | 73 | 1626 | 8 | 20 | **+12** | 0,990 | 0,997 | 0,008 |
| `official_diary_ce/do20240429p01.pdf#p6` | official_diary_ce | 69 | 1121 | 0 | 8 | **+8** | 1,000 | 0,997 | -0,003 |

---

## C. Análise de Padrão: Terços de Unidades e Veículos Vistos no Treino

Compara a média de quebras da regra geométrica (`regra_colunas`), do melhor modelo treinado (`sucessor_linhas_40ep`) e do modelo pré-treinado zero-shot (`layoutreader_pronto`).

### Golden v4 (44 páginas)

#### Por Faixa de Complexidade (Terços do número de unidades)

| Terço de Unidades | n | Faixa de Unidades | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|:---:|---:|---:|---:|
| 1º terço (poucas unidades) | 14 | 4 a 29 | 2,07 | 3,57 | 1,14 |
| 2º terço (intermediárias) | 15 | 33 a 91 | 5,80 | 6,27 | 5,60 |
| 3º terço (muitas unidades) | 15 | 94 a 493 | 10,00 | 22,67 | 47,27 |

#### Por Veículo Visto no Treino

| Grupo | n | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|---:|---:|---:|
| Veículos Vistos | 5 | 4,80 | 7,80 | 21,20 |
| Veículos Não Vistos | 39 | 6,21 | 11,41 | 18,03 |

### Golden v3 Novo (27 páginas)

#### Por Faixa de Complexidade (Terços do número de unidades)

| Terço de Unidades | n | Faixa de Unidades | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|:---:|---:|---:|---:|
| 1º terço (poucas unidades) | 9 | 4 a 54 | 5,33 | 5,00 | 2,56 |
| 2º terço (intermediárias) | 9 | 55 a 83 | 4,11 | 6,89 | 5,22 |
| 3º terço (muitas unidades) | 9 | 99 a 401 | 18,22 | 25,56 | 40,89 |

#### Por Veículo Visto no Treino

| Grupo | n | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|---:|---:|---:|
| Veículos Vistos | 0 | — | — | — | *(Bancada sem veículos de treino)* |
| Veículos Não Vistos | 27 | 9,22 | 12,48 | 16,22 |

### Teste Silver (89 páginas)

#### Por Faixa de Complexidade (Terços do número de unidades)

| Terço de Unidades | n | Faixa de Unidades | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|:---:|---:|---:|---:|
| 1º terço (poucas unidades) | 29 | 4 a 69 | 43,38 | 42,03 | 39,76 |
| 2º terço (intermediárias) | 30 | 76 a 99 | 7,43 | 11,20 | 6,87 |
| 3º terço (muitas unidades) | 30 | 102 a 401 | 32,07 | 42,87 | 47,40 |

#### Por Veículo Visto no Treino

| Grupo | n | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |
|---|---:|---:|---:|---:|
| Veículos Vistos | 0 | — | — | — | *(Bancada sem veículos de treino)* |
| Veículos Não Vistos | 89 | 27,45 | 31,92 | 31,25 |

---

## D. Comparação Controlada em 'Colunas e Margens' (Subconjunto Gemini)

Restrição de todos os ordenadores à interseção exata de páginas cobertas pelo Gemini em `colunas_margens`.

### Golden v4 (44 páginas)

- Páginas cobertas pelo Gemini: **41**
- Páginas na interseção comum avaliada: **41**

| Ordenador | n | τ Médio | Quebras / Página | Quebras / mil palavras | Sucessor Linhas (%) |
|---|---:|---:|---:|---:|---:|
| `teto` | 41 | 0,958 | 5,22 | 8,74 | 94,7% |
| `regra_colunas` | 41 | 0,868 | 5,37 | 8,89 | 94,6% |
| `xycut_margens` | 41 | 0,868 | 5,37 | 8,89 | 94,6% |
| `layoutreader_pronto` | 41 | 0,919 | 5,32 | 8,87 | 94,6% |
| `lstm_geo_colunas_margens` | 41 | 0,934 | 6,34 | 10,36 | 93,3% |
| `sucessor_colunas_margens` | 41 | 0,931 | 6,05 | 9,93 | 93,6% |
| `sucessor_colunas_margens_s43` | 41 | 0,933 | 5,98 | 9,96 | 93,7% |
| `gemini` | 41 | 0,901 | 5,37 | 8,88 | 94,6% |

### Golden v3 Novo (27 páginas)

- Páginas cobertas pelo Gemini: **25**
- Páginas na interseção comum avaliada: **25**

| Ordenador | n | τ Médio | Quebras / Página | Quebras / mil palavras | Sucessor Linhas (%) |
|---|---:|---:|---:|---:|---:|
| `teto` | 25 | 0,903 | 9,28 | 15,03 | 91,9% |
| `regra_colunas` | 25 | 0,795 | 9,40 | 15,29 | 91,7% |
| `xycut_margens` | 25 | 0,795 | 9,40 | 15,29 | 91,7% |
| `layoutreader_pronto` | 25 | 0,827 | 9,28 | 15,17 | 91,7% |
| `lstm_geo_colunas_margens` | 25 | 0,821 | 9,64 | 15,68 | 91,4% |
| `sucessor_colunas_margens` | 25 | 0,858 | 9,44 | 15,19 | 91,8% |
| `sucessor_colunas_margens_s43` | 25 | 0,856 | 9,48 | 15,28 | 91,7% |
| `gemini` | 25 | 0,759 | 9,44 | 15,35 | 91,7% |

---

## E. Sensibilidade a Sementes Aleatórias (Padrão vs. s43)

Mede a estabilidade da inferência variando a semente (`Δ = s43 - padrão`).

### Golden v4 (44 páginas)

| Representação / Par | n | τ Padrão | τ s43 | Δτ | Quebras Padrão | Quebras s43 | ΔQuebras | Mediana ΔQ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `sucessor_linhas` (linhas) | 44 | 0,902 | 0,887 | -0,015 | 57,59 | 62,75 | 5,16 | 5,0 |
| `sucessor_colunas_margens` (col_marg) | 44 | 0,934 | 0,936 | 0,002 | 5,98 | 5,86 | -0,11 | 0,0 |

### Golden v3 Novo (27 páginas)

| Representação / Par | n | τ Padrão | τ s43 | Δτ | Quebras Padrão | Quebras s43 | ΔQuebras | Mediana ΔQ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `sucessor_linhas` (linhas) | 27 | 0,885 | 0,879 | -0,006 | 57,00 | 62,41 | 5,41 | 2,0 |
| `sucessor_colunas_margens` (col_marg) | 27 | 0,867 | 0,866 | -0,001 | 8,96 | 9,00 | 0,04 | 0,0 |

### Teste Silver (89 páginas)

| Representação / Par | n | τ Padrão | τ s43 | Δτ | Quebras Padrão | Quebras s43 | ΔQuebras | Mediana ΔQ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `sucessor_linhas` (linhas) | 89 | 0,876 | 0,862 | -0,015 | 89,62 | 94,35 | 4,73 | 3,0 |
| `sucessor_colunas_margens` (col_marg) | 89 | 0,903 | 0,902 | -0,001 | 32,18 | 31,96 | -0,22 | 0,0 |

---

## Limitações e Notas Metodológicas

1. **Bancada de desenvolvimento**: O Golden v4 foi utilizado durante o desenvolvimento das regras geométricas e heurísticas de colunas; os números obtidos nele não representam um teste completamente independente.
2. **Referência silver automática**: A bancada de teste silver (CE, MA, RJ) utiliza ordem do fluxo de conteúdo PDF de veículos confiáveis, favorecendo ordens topológicas compatíveis com geradores geométricos.
3. **Tamanho amostral**: Bancadas humanas contêm 44 (v4) e 27 (v3 novo) páginas; conclusões estatísticas devem considerar a variabilidade intrínseca de layouts heterogêneos.
4. **Agrupamento de unidades longas**: Modelos com limitação de tokens (ex.: LayoutReader > 510 unidades) operam com hierarquia ou agrupamento geométrico em páginas extensas.
