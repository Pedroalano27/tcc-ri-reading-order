# Avaliação do Extrator Híbrido com Detectores Treinados no Domínio

**Lote de Teste:** `data/diamond/diamond_teste` (11 páginas anotadas do zero pelo Pedro, sem pré-anotação / sem viés de ancoragem).  
**Objetivo:** Verificar se a substituição ou combinação do detector genérico visual (Docling Heron) por detectores treinados em diários oficiais (Label Studio 16 classes, LS 3 classes e modelos fine-tuned no Diamond) melhora a qualidade da segmentação do extrator de regiões.

---

## 1. Resumo Executivo (5 Linhas)

VEREDITO: NENHUMA variante supera o extrator atual em F1@0,5 global (empate em 0,851 com '(b) extrator c/ det diamond_ft_ls16'; ganha em 6 paginas, empata em 0, perde em 5).
F1 COM CLASSE: No F1@0,5 com classe, o extrator atual alcanca 0.696, enquanto a melhor variante '(c) uniao: det diamond_ft_ls16 + Docling' alcanca 0.691 (-0.005).
COMPONENTE HIBRIDO: A estrategia de uniao (c) e de apenas tabela/imagem (d) preservam a estabilidade do segmentador estrutural v3, enquanto a substituicao direta (b) sofre com classes ausentes no detector.
DETECTOR PURO: Todos os detectores puros (e) perdem significativamente para o extrator baseado em regras (F1@0,5 de 0.753 a 0.765 vs 0,851).
LIMITACAO METODOLOGICA: A amostra tem apenas n = 11 paginas; diferencas de F1 inferiores a 0,02 devem ser interpretadas como empate estatistico e nao como avanco conclusivo.

---

## 2. Tabelas Principais de Resultados

### 2.1 Régua de 9 Classes (Diamond / Extrator)
*Régua completa: `titulo`, `texto`, `lista`, `tabela`, `assinatura`, `cabecalho`, `rodape`, `figura`, `outro`.*

| Sistema | F1@0,5 | F1@0,9 | F1 c/ classe | Classe % (palavras) | Regiões (pred/gold) |
|:---|---:|---:|---:|---:|---:|
| (a) extrator atual (regras+Docling) | 0.851 | 0.754 | 0.696 | 76.9% | 370/328 |
| (b) extrator c/ det ls16 | 0.841 | 0.754 | 0.688 | 76.8% | 364/328 |
| (b) extrator c/ det ls3 | 0.834 | 0.741 | 0.524 | 72.2% | 382/328 |
| (b) extrator c/ det diamond_ft_ls16 | 0.851 | 0.772 | 0.689 | 72.0% | 377/328 |
| (b) extrator c/ det diamond_ft_coco | 0.810 | 0.715 | 0.663 | 76.3% | 366/328 |
| (c) uniao: det ls16 + Docling | 0.830 | 0.749 | 0.686 | 76.8% | 366/328 |
| (c) uniao: det ls3 + Docling | 0.845 | 0.760 | 0.537 | 72.9% | 380/328 |
| (c) uniao: det diamond_ft_ls16 + Docling | 0.829 | 0.748 | 0.691 | 72.8% | 381/328 |
| (c) uniao: det diamond_ft_coco + Docling | 0.823 | 0.732 | 0.681 | 76.8% | 377/328 |
| (d) so tab/img: det ls16 | 0.679 | 0.609 | 0.364 | 72.8% | 276/328 |
| (d) so tab/img: det ls3 | 0.677 | 0.601 | 0.363 | 72.8% | 278/328 |
| (d) so tab/img: det diamond_ft_ls16 | 0.684 | 0.615 | 0.370 | 72.8% | 277/328 |
| (d) so tab/img: det diamond_ft_coco | 0.679 | 0.609 | 0.364 | 72.8% | 276/328 |
| (e) detector ls16 puro | 0.753 | 0.648 | 0.628 | 75.6% | 363/328 |
| (e) detector ls3 puro | 0.765 | 0.646 | 0.431 | 68.0% | 378/328 |
| (e) detector diamond_ft_ls16 puro | 0.789 | 0.675 | 0.642 | 62.2% | 389/328 |
| (e) detector diamond_ft_coco puro | 0.750 | 0.631 | 0.639 | 60.0% | 373/328 |

### 2.2 Régua de 3 Classes (Texto / Tabela / Imagem)
*Régua colapsada: macroestrutura visual dos diários.*

| Sistema | F1@0,5 | F1@0,9 | F1 c/ classe | Classe % (palavras) | Regiões (pred/gold) |
|:---|---:|---:|---:|---:|---:|
| (a) extrator atual (regras+Docling) | 0.850 | 0.750 | 0.824 | 97.8% | 371/328 |
| (b) extrator c/ det ls16 | 0.840 | 0.750 | 0.817 | 98.0% | 365/328 |
| (b) extrator c/ det ls3 | 0.833 | 0.737 | 0.807 | 97.2% | 383/328 |
| (b) extrator c/ det diamond_ft_ls16 | 0.850 | 0.768 | 0.830 | 98.3% | 378/328 |
| (b) extrator c/ det diamond_ft_coco | 0.809 | 0.711 | 0.788 | 98.1% | 367/328 |
| (c) uniao: det ls16 + Docling | 0.829 | 0.745 | 0.806 | 97.6% | 367/328 |
| (c) uniao: det ls3 + Docling | 0.843 | 0.756 | 0.818 | 97.6% | 381/328 |
| (c) uniao: det diamond_ft_ls16 + Docling | 0.828 | 0.744 | 0.808 | 97.8% | 382/328 |
| (c) uniao: det diamond_ft_coco + Docling | 0.822 | 0.728 | 0.796 | 97.8% | 378/328 |
| (d) so tab/img: det ls16 | 0.678 | 0.605 | 0.651 | 98.0% | 277/328 |
| (d) so tab/img: det ls3 | 0.675 | 0.596 | 0.649 | 98.0% | 279/328 |
| (d) so tab/img: det diamond_ft_ls16 | 0.683 | 0.611 | 0.660 | 98.1% | 278/328 |
| (d) so tab/img: det diamond_ft_coco | 0.678 | 0.605 | 0.655 | 98.1% | 277/328 |
| (e) detector ls16 puro | 0.753 | 0.648 | 0.718 | 94.7% | 363/328 |
| (e) detector ls3 puro | 0.765 | 0.646 | 0.731 | 93.0% | 378/328 |
| (e) detector diamond_ft_ls16 puro | 0.789 | 0.675 | 0.759 | 92.4% | 389/328 |
| (e) detector diamond_ft_coco puro | 0.750 | 0.631 | 0.722 | 86.9% | 373/328 |

---

## 3. Análise Detalhada por Página contra a Linha de Base (a)

São exatamente **11 páginas** desenhadas do zero. Diferenças pontuais não devem ser sobrestimadas.

### 3.1 Resumo de Vitórias, Empates e Derrotas

| Variante vs Extrator Atual (a) | Ganha (Δ > 0) | Empata (Δ = 0) | Perde (Δ < 0) | Δ Médio F1@0,5 (9 cls) | Δ Médio F1@0,5 (3 cls) |
|:---|---:|---:|---:|---:|---:|
| (b) extrator c/ det ls16 | 7 | 0 | 4 | -0.003 | -0.003 |
| (b) extrator c/ det ls3 | 6 | 0 | 5 | -0.008 | -0.008 |
| (b) extrator c/ det diamond_ft_ls16 | 6 | 0 | 5 | -0.014 | -0.014 |
| (b) extrator c/ det diamond_ft_coco | 4 | 2 | 5 | -0.056 | -0.055 |
| (c) uniao: det ls16 + Docling | 7 | 0 | 4 | -0.015 | -0.015 |
| (c) uniao: det ls3 + Docling | 6 | 0 | 5 | +0.005 | +0.005 |
| (c) uniao: det diamond_ft_ls16 + Docling | 6 | 1 | 4 | -0.030 | -0.030 |
| (c) uniao: det diamond_ft_coco + Docling | 5 | 2 | 4 | -0.044 | -0.044 |
| (d) so tab/img: det ls16 | 4 | 0 | 7 | -0.148 | -0.147 |
| (d) so tab/img: det ls3 | 4 | 0 | 7 | -0.149 | -0.149 |
| (d) so tab/img: det diamond_ft_ls16 | 4 | 0 | 7 | -0.148 | -0.148 |
| (d) so tab/img: det diamond_ft_coco | 4 | 0 | 7 | -0.151 | -0.151 |
| (e) detector ls16 puro | 3 | 2 | 6 | -0.026 | -0.025 |
| (e) detector ls3 puro | 5 | 1 | 5 | -0.005 | -0.004 |
| (e) detector diamond_ft_ls16 puro | 4 | 2 | 5 | -0.015 | -0.014 |
| (e) detector diamond_ft_coco puro | 3 | 2 | 6 | -0.050 | -0.049 |

### 3.2 Diferença de F1@0,5 (Δ = Variante - Base) por Página (Régua 9 Classes)

| Sistema | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | Média Δ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (a) extrator atual (F1 absoluto) | 0.875 | 0.845 | 0.704 | 0.895 | 0.788 | 0.889 | 0.962 | 0.863 | 1.000 | 0.895 | 0.545 | 0.851 |
| (b) extrator c/ det ls16 (Δ) | +0.054 | +0.016 | +0.171 | +0.050 | +0.115 | +0.111 | -0.312 | +0.031 | -0.111 | -0.004 | -0.152 | -0.003 |
| (b) extrator c/ det ls3 (Δ) | +0.054 | +0.012 | +0.153 | +0.009 | +0.024 | +0.111 | -0.136 | -0.048 | -0.111 | -0.004 | -0.152 | -0.008 |
| (b) extrator c/ det diamond_ft_ls16 (Δ) | +0.125 | -0.007 | +0.190 | +0.105 | +0.115 | -0.089 | -0.425 | +0.095 | -0.111 | +0.010 | -0.158 | -0.014 |
| (b) extrator c/ det diamond_ft_coco (Δ) | +0.022 | -0.023 | +0.190 | +0.059 | +0.000 | +0.000 | -0.550 | +0.001 | -0.111 | -0.012 | -0.187 | -0.056 |
| (c) uniao: det ls16 + Docling (Δ) | +0.054 | +0.016 | +0.171 | +0.002 | +0.115 | +0.111 | -0.312 | -0.063 | -0.111 | +0.005 | -0.152 | -0.015 |
| (c) uniao: det ls3 + Docling (Δ) | +0.054 | +0.012 | +0.153 | +0.049 | +0.024 | +0.111 | -0.023 | -0.048 | -0.111 | -0.012 | -0.152 | +0.005 |
| (c) uniao: det diamond_ft_ls16 + Docling (Δ) | +0.125 | +0.004 | +0.153 | +0.011 | +0.115 | -0.089 | -0.391 | +0.000 | -0.111 | +0.007 | -0.158 | -0.030 |
| (c) uniao: det diamond_ft_coco + Docling (Δ) | +0.022 | +0.004 | +0.171 | +0.050 | +0.000 | +0.000 | -0.421 | -0.019 | -0.111 | +0.011 | -0.187 | -0.044 |
| (d) so tab/img: det ls16 (Δ) | +0.054 | -0.133 | +0.196 | +0.059 | +0.024 | -0.344 | -0.704 | -0.160 | -0.111 | -0.348 | -0.158 | -0.148 |
| (d) so tab/img: det ls3 (Δ) | +0.054 | -0.133 | +0.196 | +0.042 | +0.024 | -0.344 | -0.704 | -0.160 | -0.111 | -0.348 | -0.158 | -0.149 |
| (d) so tab/img: det diamond_ft_ls16 (Δ) | +0.054 | -0.133 | +0.196 | +0.096 | +0.024 | -0.389 | -0.704 | -0.160 | -0.111 | -0.348 | -0.158 | -0.148 |
| (d) so tab/img: det diamond_ft_coco (Δ) | +0.054 | -0.133 | +0.196 | +0.068 | +0.024 | -0.389 | -0.704 | -0.160 | -0.111 | -0.348 | -0.158 | -0.151 |
| (e) detector ls16 puro (Δ) | -0.029 | +0.016 | +0.296 | -0.098 | +0.051 | +0.000 | -0.039 | -0.085 | +0.000 | -0.242 | -0.158 | -0.026 |
| (e) detector ls3 puro (Δ) | +0.054 | +0.012 | +0.296 | -0.118 | +0.051 | +0.111 | -0.053 | -0.048 | +0.000 | -0.206 | -0.158 | -0.005 |
| (e) detector diamond_ft_ls16 puro (Δ) | +0.125 | +0.012 | +0.190 | -0.004 | +0.087 | +0.000 | -0.227 | -0.033 | +0.000 | -0.119 | -0.201 | -0.015 |
| (e) detector diamond_ft_coco puro (Δ) | +0.022 | -0.039 | +0.190 | -0.063 | +0.024 | +0.000 | -0.281 | -0.039 | +0.000 | -0.149 | -0.212 | -0.050 |

#### Índice das 11 Páginas Avaliadas
- **P1**: `official_diary_MG_congonhas/executive_official_diary_2014-04-09_998.pdf#p1` (595x842 pt, 308 palavras, 16 regiões no gabarito)
- **P2**: `official_diary_RJ_duque_de_caxias/executive_official_diary_2022-08-05_Boletim_7175.pdf#p13` (595x842 pt, 706 palavras, 38 regiões no gabarito)
- **P3**: `official_diary_ms/executive_official_diary_48977_2025-03-27.pdf#p359` (595x842 pt, 340 palavras, 23 regiões no gabarito)
- **P4**: `official_diary_pe/2021-08-12_1-Poder Executivo.pdf#p4` (794x1040 pt, 1729 palavras, 55 regiões no gabarito)
- **P5**: `official_diary_pi_v2/executive_official_diary_2025_04_30_81_2025.pdf#p174` (595x842 pt, 392 palavras, 16 regiões no gabarito)
- **P6**: `official_diary_pr_curitiba/31-Supl2_2023-02-14.pdf#p76` (595x842 pt, 209 palavras, 6 regiões no gabarito)
- **P7**: `official_diary_ro/executive_official_diary_2021-11-11.pdf#p344` (595x842 pt, 1157 palavras, 25 regiões no gabarito)
- **P8**: `official_diary_rr/2023-11-14_DiarioRR.pdf#p23` (595x842 pt, 469 palavras, 28 regiões no gabarito)
- **P9**: `official_diary_rs_porto_alegre/5393_ce_20241023_executivo.pdf#p4` (595x842 pt, 353 palavras, 4 regiões no gabarito)
- **P10**: `official_diary_se/DOE-SE_2022-03-18_4475.pdf#p10` (930x1276 pt, 1499 palavras, 120 regiões no gabarito)
- **P11**: `official_diary_to/2023-07-24_4946_22_50.pdf#p0` (595x842 pt, 1182 palavras, 14 regiões no gabarito)

---

## 4. Tabelas de Tradução de Vocabulários

O extrator `seg.propor(palavras, blocos_v3, regioes_detector, regras=True)` foi originalmente concebido para receber as predições do detector **Docling Heron** (vocabulário do DocLayNet). Cada vocabulário de detector do domínio é traduzido para o rótulo Docling correspondente antes da ingestão pelo pipeline geométrico:

### 4.1 Vocabulário LS16 (16 classes do guia do Label Studio)
| Classe (16 classes do guia) | Rótulo Docling Equivalente | Classe Resultante no Extrator |
|:---|:---|:---|
| `act` | `title` | `titulo` |
| `act section` | `section_header` | `titulo` |
| `caption` | `caption` | `texto` |
| `chart` | `picture` | `figura` |
| `figure` | `picture` | `figura` |
| `footer` | `page_footer` | `rodape` |
| `header` | `page_header` | `cabecalho` |
| `heading` | `text` | `texto` |
| `id` | `key_value_region` | `texto` |
| `paragraph` | `text` | `texto` |
| `section title` | `section_header` | `titulo` |
| `signature` | `text` | `texto` |
| `sub section title` | `section_header` | `titulo` |
| `table` | `table` | `tabela` |
| `title` | `title` | `titulo` |
| `unknown` | `text` | `texto` |

### 4.2 Vocabulário LS3 (3 classes: texto / tabela / imagem)
| Classe (3 classes) | Rótulo Docling Equivalente | Classe Resultante no Extrator |
|:---|:---|:---|
| `figura` | `picture` | `figura` |
| `figure` | `picture` | `figura` |
| `imagem` | `picture` | `figura` |
| `tabela` | `table` | `tabela` |
| `table` | `table` | `tabela` |
| `text` | `text` | `texto` |
| `texto` | `text` | `texto` |

### 4.3 Vocabulário 9 Classes (Detectores fine-tuned no Diamond)
| Classe (9 classes Diamond FT) | Rótulo Docling Equivalente | Classe Resultante no Extrator |
|:---|:---|:---|
| `assinatura` | `text` | `texto` |
| `cabecalho` | `page_header` | `cabecalho` |
| `figura` | `picture` | `figura` |
| `lista` | `list_item` | `lista` |
| `outro` | `text` | `texto` |
| `rodape` | `page_footer` | `rodape` |
| `tabela` | `table` | `tabela` |
| `texto` | `text` | `texto` |
| `titulo` | `title` | `titulo` |

---

## 5. Limitações e Ameaças à Validade

1. **Amostra Reduzida (n = 11 páginas):** O lote `diamond_teste` é rigoroso por ter sido anotado do zero sem qualquer pré-anotação (elimina 100% o viés de ancoragem), mas possui tamanho estatístico restrito. Um ganho de 1 página representa ~9% da amostra.
2. **Ausência da Classe Assinatura nos Detectores Visuais:** Nem o Docling original nem os detectores genéricos têm representação visual confiável para assinaturas textuais puras (nomes seguidos de cargo). As assinaturas continuam sendo recuperadas pelas regras heurísticas do extrator (`eh_assinatura`, etapa 6).
3. **Viés de Ancoragem nos Dados de Treino do Label Studio:** Os detectores treinados no Label Studio (`ls16`, `ls3`) utilizaram anotações onde ~85% das caixas eram correções de uma pré-anotação automática, podendo carregar certas assimetrias e granularidades do modelo gerador original.
4. **Resolução de Conflitos na União:** Na abordagem (c), o limiar de 60% de sobreposição para descarte do Docling preserva caixas do domínio, mas em páginas complexas multicolunas pode gerar sobreposições marginais que acionam a etapa de fusão de fragmentos do extrator.
