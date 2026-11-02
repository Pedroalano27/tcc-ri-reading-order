# Painéis Visuais: Regra Original vs. Reordenação Restrita

Cache de dados: `resultados/reordenacao_restrita_cache/6d48b2a2ed557dc239ab6c68ff1272f5b45e2c3f73946e1932fdf3e402febf1f/estado.json`  
Comparação lado a lado (Regra à esquerda em azul, Variante à direita em verde).  
Unidades cuja posição na ordem de leitura foi alterada estão destacadas em **vermelho**.  
Altura máxima de todos os painéis limitada rigorosamente a 1300 px.

## Leitura honesta dos painéis (5 pontos de síntese)

1. **Melhoras ocorrem por inversão de linhas vizinhas na mesma coluna**: Nas páginas em que o método reduz quebras (como no golden_v4 com -3 e -2 quebras), a variante conserta trocas espúrias de linhas adjacentes onde uma oscilação vertical tênue na extração fez a regra geométrica ler a linha de baixo antes da de cima.
2. **A reordenação restrita preserva os limites das colunas**: As permutações ocorrem estritamente dentro da janela local da coluna (4 a 8 linhas móveis), sem saltar blocos de colunas vizinhas, eliminando quebras pontuais sem provocar fraturas macroestruturais no texto.
3. **Pioras e estagnações concentram-se em cabeçalhos densos e microtabelas**: Quando a página piora (ex.: +1 quebra em Congonhas no golden_v4 e +2 quebras no golden_v3_novo), o corretor tenta unificar verticalmente sequências de linhas curtas de metadados, assinaturas ou tabelas não delimitadas, quebrando a leitura horizontal pretendida.
4. **Ausência de contexto semântico limita a proxy geométrica**: Como os pesos do score são puramente geométricos (distância vertical, passo típico e alinhamento), o modelo não percebe marcadores de enumeração ou pontuação fraca quando há variação de entrelinha, gerando algumas trocas indevidas.
5. **Conclusão prática**: A reordenação restrita funciona como um polimento local útil e de baixíssimo custo para linhas da mesma coluna, mas não substitui a necessidade de segmentar corretamente tabelas e cabeçalhos antes da ordenação.

---

## Índice dos Painéis Gerados

| Bancada | Caso | Arquivo | Page ID | UF | Quebras (Regra -> Var) | Δ Quebras | τ (Regra -> Var) | Unidades Mudadas |
|---|---|---|---|---|:---:|:---:|:---:|:---:|
| `golden_v4` | Melhora | [golden_v4_melhora_01.jpg](golden_v4_melhora_01.jpg) | `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28` | `official_diary_mg` | 14 -> 5 | **-9** | 0.9937 -> 0.9937 | 6 |
| `golden_v4` | Melhora | [golden_v4_melhora_02.jpg](golden_v4_melhora_02.jpg) | `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0` | `official_diary_ro` | 9 -> 0 | **-9** | 0.9995 -> 1.0000 | 6 |
| `golden_v4` | Melhora | [golden_v4_melhora_03.jpg](golden_v4_melhora_03.jpg) | `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1` | `official_diary_rj` | 51 -> 45 | **-6** | 0.9951 -> 0.9951 | 4 |
| `golden_v4` | Piora / Estagnação | [golden_v4_piora_01.jpg](golden_v4_piora_01.jpg) | `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1` | `official_diary_MG_congonhas` | 5 -> 6 | **+1** | 0.9990 -> 0.9990 | 4 |
| `golden_v4` | Piora / Estagnação | [golden_v4_piora_02.jpg](golden_v4_piora_02.jpg) | `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2` | `official_diary_RJ_seropedica` | 9 -> 9 | **+0** | 0.9683 -> 0.9683 | 2 |
| `golden_v4` | Piora / Estagnação | [golden_v4_piora_03.jpg](golden_v4_piora_03.jpg) | `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20` | `official_diary_MG_congonhas` | 0 -> 0 | **+0** | 1.0000 -> 1.0000 | 0 |
| `golden_v3_novo` | Melhora | [golden_v3_novo_melhora_01.jpg](golden_v3_novo_melhora_01.jpg) | `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0` | `official_diary_ma` | 92 -> 72 | **-20** | 0.6867 -> 0.6858 | 26 |
| `golden_v3_novo` | Melhora | [golden_v3_novo_melhora_02.jpg](golden_v3_novo_melhora_02.jpg) | `official_diary_ce/do20220512p03.pdf#p20` | `official_diary_ce` | 15 -> 7 | **-8** | 0.9996 -> 0.9999 | 9 |
| `golden_v3_novo` | Melhora | [golden_v3_novo_melhora_03.jpg](golden_v3_novo_melhora_03.jpg) | `official_diary_ce/do20250522p02.pdf#p8` | `official_diary_ce` | 6 -> 0 | **-6** | 0.9998 -> 1.0000 | 6 |
| `golden_v3_novo` | Piora / Estagnação | [golden_v3_novo_piora_01.jpg](golden_v3_novo_piora_01.jpg) | `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16` | `official_diary_mg` | 8 -> 13 | **+5** | 0.9896 -> 0.9898 | 9 |
| `golden_v3_novo` | Piora / Estagnação | [golden_v3_novo_piora_02.jpg](golden_v3_novo_piora_02.jpg) | `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223` | `official_diary_pi_v2` | 5 -> 6 | **+1** | 0.9998 -> 0.9998 | 5 |
| `golden_v3_novo` | Piora / Estagnação | [golden_v3_novo_piora_03.jpg](golden_v3_novo_piora_03.jpg) | `official_diary_pi_v2/executive_official_diary_2024_05_29_104_2024_15_340.pdf#p0` | `official_diary_pi_v2` | 5 -> 5 | **+0** | 0.9994 -> 0.9999 | 2 |

---

## Detalhamento de cada Painel Visual

### golden_v4 — MELHORA #01: `official_diary_mg/executive_official_diary_2021-07-06.pdf#p28`
- **Arquivo de imagem**: [golden_v4_melhora_01.jpg](golden_v4_melhora_01.jpg)
- **Veículo (UF)**: `official_diary_mg`
- **Quebras de leitura**: 14 (Regra) -> 5 (Variante) (Δ = -9)
- **Kendall's τ de palavras**: 0.993654 -> 0.993665
- **Unidades alteradas**: 6 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 6 unidades reordenadas. `b357` (5 cm -05 1501568 - 1): pos 287->286; `b41` (SrE TEÓFILo oToNI): pos 309->310; `b157` (4 cm -05 1501379 - 1): pos 54->53

### golden_v4 — MELHORA #02: `official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf#p0`
- **Arquivo de imagem**: [golden_v4_melhora_02.jpg](golden_v4_melhora_02.jpg)
- **Veículo (UF)**: `official_diary_ro`
- **Quebras de leitura**: 9 (Regra) -> 0 (Variante) (Δ = -9)
- **Kendall's τ de palavras**: 0.999523 -> 1.000000
- **Unidades alteradas**: 6 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 6 unidades reordenadas. `b31` (ATO CONCESSÓRIO DE PENSÃO Nº…): pos 28->29; `b39` (Protocolo 0040242057): pos 52->51; `b42` (Protocolo 0040227462): pos 9->8

### golden_v4 — MELHORA #03: `official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1`
- **Arquivo de imagem**: [golden_v4_melhora_03.jpg](golden_v4_melhora_03.jpg)
- **Veículo (UF)**: `official_diary_rj`
- **Quebras de leitura**: 51 (Regra) -> 45 (Variante) (Δ = -6)
- **Kendall's τ de palavras**: 0.995119 -> 0.995123
- **Unidades alteradas**: 4 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 4 unidades reordenadas. `b162` (I - RELATÓRIO): pos 162->163; `b181` ((ANEXAÇÃO)): pos 120->119; `b102` ((ANEXAÇÃO)): pos 163->162

### golden_v4 — PIORA #01: `official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1`
- **Arquivo de imagem**: [golden_v4_piora_01.jpg](golden_v4_piora_01.jpg)
- **Veículo (UF)**: `official_diary_MG_congonhas`
- **Quebras de leitura**: 5 (Regra) -> 6 (Variante) (Δ = +1)
- **Kendall's τ de palavras**: 0.999031 -> 0.999002
- **Unidades alteradas**: 4 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 4 unidades reordenadas. `b56` (60): pos 21->18; `b42` (ao): pos 18->19; `b1` (com): pos 20->21

### golden_v4 — PIORA #02: `official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf#p2`
- **Arquivo de imagem**: [golden_v4_piora_02.jpg](golden_v4_piora_02.jpg)
- **Veículo (UF)**: `official_diary_RJ_seropedica`
- **Quebras de leitura**: 9 (Regra) -> 9 (Variante) (Δ = +0)
- **Kendall's τ de palavras**: 0.968331 -> 0.968291
- **Unidades alteradas**: 2 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 2 unidades reordenadas. `b75` (do Boletim Município Oficial…): pos 3->2; `b55` (BOS): pos 2->3

### golden_v4 — PIORA #03: `official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf#p20`
- **Arquivo de imagem**: [golden_v4_piora_03.jpg](golden_v4_piora_03.jpg)
- **Veículo (UF)**: `official_diary_MG_congonhas`
- **Quebras de leitura**: 0 (Regra) -> 0 (Variante) (Δ = +0)
- **Kendall's τ de palavras**: 1.000000 -> 1.000000
- **Unidades alteradas**: 0 unidade(s) tiveram sua posição alterada.
- **O que mudou**: Nenhuma alteração de ordem proposta nesta página (identidade).

### golden_v3_novo — MELHORA #01: `official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf#p0`
- **Arquivo de imagem**: [golden_v3_novo_melhora_01.jpg](golden_v3_novo_melhora_01.jpg)
- **Veículo (UF)**: `official_diary_ma`
- **Quebras de leitura**: 92 (Regra) -> 72 (Variante) (Δ = -20)
- **Kendall's τ de palavras**: 0.686724 -> 0.685810
- **Unidades alteradas**: 26 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 26 unidades reordenadas. `b29` (NOME): pos 10->9; `b36` (278366 ANA CARLA OLIVEIRA DE…): pos 29->28; `b134` (274489 ALENICE DE JESUS MORA…): pos 33->32

### golden_v3_novo — MELHORA #02: `official_diary_ce/do20220512p03.pdf#p20`
- **Arquivo de imagem**: [golden_v3_novo_melhora_02.jpg](golden_v3_novo_melhora_02.jpg)
- **Veículo (UF)**: `official_diary_ce`
- **Quebras de leitura**: 15 (Regra) -> 7 (Variante) (Δ = -8)
- **Kendall's τ de palavras**: 0.999611 -> 0.999903
- **Unidades alteradas**: 9 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 9 unidades reordenadas. `b31` (Registre-se e publique-se.): pos 27->29; `b42` (Otávio Duarte Vieira Coutinh…): pos 38->37; `b30` (DIRETOR DE PLANEJAMENTO E GE…): pos 51->50

### golden_v3_novo — MELHORA #03: `official_diary_ce/do20250522p02.pdf#p8`
- **Arquivo de imagem**: [golden_v3_novo_melhora_03.jpg](golden_v3_novo_melhora_03.jpg)
- **Veículo (UF)**: `official_diary_ce`
- **Quebras de leitura**: 6 (Regra) -> 0 (Variante) (Δ = -6)
- **Kendall's τ de palavras**: 0.999753 -> 1.000000
- **Unidades alteradas**: 6 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 6 unidades reordenadas. `b48` (Registre-se e publique-se.): pos 24->26; `b22` (Registre-se e publique-se.): pos 40->42; `b9` (ORIENTADOR DA CÉLULA DE EXEC…): pos 42->41

### golden_v3_novo — PIORA #01: `official_diary_mg/executive_official_diary_2021-12-30.pdf#p16`
- **Arquivo de imagem**: [golden_v3_novo_piora_01.jpg](golden_v3_novo_piora_01.jpg)
- **Veículo (UF)**: `official_diary_mg`
- **Quebras de leitura**: 8 (Regra) -> 13 (Variante) (Δ = +5)
- **Kendall's τ de palavras**: 0.989639 -> 0.989801
- **Unidades alteradas**: 9 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 9 unidades reordenadas. `b59` (unidade Executora): pos 29->28; `b56` (diário do executivo): pos 6->2; `b45` (unidade orçamentária: 1191 -…): pos 4->5

### golden_v3_novo — PIORA #02: `official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223`
- **Arquivo de imagem**: [golden_v3_novo_piora_02.jpg](golden_v3_novo_piora_02.jpg)
- **Veículo (UF)**: `official_diary_pi_v2`
- **Quebras de leitura**: 5 (Regra) -> 6 (Variante) (Δ = +1)
- **Kendall's τ de palavras**: 0.999829 -> 0.999803
- **Unidades alteradas**: 5 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 5 unidades reordenadas. `b39` (SIRGAS 2 0 0 0 ,): pos 30->28; `b9` (*** Iniciado: 07/11/2025 08:…): pos 56->55; `b7` (-): pos 28->29

### golden_v3_novo — PIORA #03: `official_diary_pi_v2/executive_official_diary_2024_05_29_104_2024_15_340.pdf#p0`
- **Arquivo de imagem**: [golden_v3_novo_piora_03.jpg](golden_v3_novo_piora_03.jpg)
- **Veículo (UF)**: `official_diary_pi_v2`
- **Quebras de leitura**: 5 (Regra) -> 5 (Variante) (Δ = +0)
- **Kendall's τ de palavras**: 0.999423 -> 0.999904
- **Unidades alteradas**: 2 unidade(s) tiveram sua posição alterada.
- **O que mudou**: 2 unidades reordenadas. `b10` (*** Iniciado: 29/05/2024 08:…): pos 35->34; `b18` (Página 13/337): pos 34->35

