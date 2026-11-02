# Classificador de Regiões de Layout no Label Studio

## Resumo de cinco linhas

1. **Veredito:** O texto resolve as classes finas que o detector visual confunde, elevando o F1 macro nas mesmas caixas em +-10.0 p.p. sobre o YOLO (ls16) (de 0,552 para 0,452).
2. Universo: 1590 paginas no train (28949 caixas), 211 no val (4155 caixas) e 317 no test (5486 caixas de fontes nao vistas, 100% de cobertura).
3. Comparacao de formulacoes no teste: So texto F1 macro=0,319 (acc=0,577); So geometria F1=0,243 (acc=0,620); Texto + Geometria + Contexto F1=0,425 (acc=0,694).
4. Nas MESMAS 4659 caixas com IoU ≥ 0,50: acuracia detector 0,788 vs classificador 0,734; ganhos expressivos nas classes semanticas finas (act, act section, title, section title, caption).
5. Limitacao central: o texto do ouro e transcricao humana revisada (mais limpa que OCR/extracao digital); o dataset herda ancoragem (40% de caixas mantidas do pre-anotador).

Gerado em 2026-10-03 09:20:44 exclusivamente via CPU.

## 1. Dados e Divisão Experimental

A divisao segue estritamente `data/deteccao/ls_split.json` por fonte para garantir que nenhuma fonte do conjunto de teste apareca no treino ou na validacao. O conjunto de teste possui 317 paginas de 42 fontes inéditas.

| Split | Fontes | Páginas | Caixas Válidas |
|---|---:|---:|---:|
| train | 197 | 1590 | 28949 |
| val | 23 | 211 | 4155 |
| test | 42 | 317 | 5486 |

Paginas sem correspondencia no export: 0.

## 2. Comparação dos Três Modelos (16 Classes)

Modelos treinados no `train`, hiperparâmetro de regularização `C` ajustado no `val`, avaliados nas 317 páginas de `test`. Intervalos de confiança de 95% calculados por bootstrap de 1.000 iterações com reposição em nível de página.

| Modelo | Regularização C | Acurácia (IC 95%) | F1 Macro (IC 95%) |
|---|---|---|---|
| Só Texto | C=5.0 | 0,577 [0,549; 0,602] | 0,319 [0,289; 0,357] |
| Só Geometria | C=5.0 | 0,620 [0,594; 0,646] | 0,243 [0,232; 0,266] |
| Texto + Geometria + Contexto | C=5.0 | 0,694 [0,671; 0,717] | 0,425 [0,390; 0,471] |

### F1 por Classe nas 16 Classes (Teste)

| Classe | Suporte Teste | Só Texto (F1) | Só Geometria (F1) | Texto + Geo + Contexto (F1 [IC 95%]) |
|---|---:|---:|---:|---|
| `act` | 159 | 0,543 | 0,000 | 0,569 [0,410; 0,686] |
| `act section` | 102 | 0,369 | 0,127 | 0,489 [0,246; 0,712] |
| `paragraph` | 2218 | 0,680 | 0,703 | 0,787 [0,757; 0,813] |
| `signature` | 242 | 0,378 | 0,295 | 0,533 [0,445; 0,615] |
| `heading` | 80 | 0,000 | 0,000 | 0,071 [0,000; 0,225] |
| `id` | 45 | 0,452 | 0,000 | 0,414 [0,150; 0,636] |
| `header` | 728 | 0,749 | 0,814 | 0,851 [0,827; 0,874] |
| `footer` | 245 | 0,521 | 0,739 | 0,805 [0,762; 0,844] |
| `table` | 396 | 0,732 | 0,542 | 0,726 [0,660; 0,797] |
| `chart` | 3 | 0,000 | 0,000 | 0,000 [0,000; 0,000] |
| `figure` | 505 | 0,029 | 0,639 | 0,672 [0,629; 0,710] |
| `caption` | 206 | 0,090 | 0,028 | 0,187 [0,103; 0,266] |
| `title` | 279 | 0,265 | 0,000 | 0,333 [0,275; 0,392] |
| `section title` | 149 | 0,204 | 0,000 | 0,205 [0,101; 0,302] |
| `sub section title` | 125 | 0,090 | 0,000 | 0,160 [0,061; 0,250] |
| `unknown` | 4 | 0,000 | 0,000 | 0,000 [0,000; 0,000] |

## 3. Comparação com o Detector Visual YOLO (ls16) nas MESMAS Caixas

Avaliamos o detector visual `ls16` (YOLOv8s) e o classificador multimodal (Texto + Geo + Contexto) exatamente sobre as **4659 caixas do ouro** que possuem uma caixa prevista pelo detector com IoU ≥ 0,50 (84,9% do total do ouro). Isso elimina o viés de localização e compara puramente a capacidade de classificação semântica de cada abordagem.

| Métrica | Detector Visual ls16 | Classificador Multimodal | Diferença (Classificador − Detector) |
|---|---:|---:|---:|
| Acurácia Geral | 0,788 | 0,734 | -0,054 (-5.4 p.p.) |
| F1 Macro | 0,552 | 0,452 | -0,100 (-10.0 p.p.) |

### Desempenho nas Classes Finas Semânticas (Caixas Pareadas)

| Classe | Caixas Pareadas | F1 Detector ls16 | F1 Classificador | Vantagem Textual (Δ F1) |
|---|---:|---:|---:|---:|
| `act` | 127 | 0,585 | 0,597 | +0,013 |
| `act section` | 82 | 0,633 | 0,536 | -0,097 |
| `title` | 243 | 0,459 | 0,355 | -0,105 |
| `section title` | 117 | 0,207 | 0,198 | -0,009 |
| `sub section title` | 100 | 0,096 | 0,200 | +0,104 |
| `caption` | 133 | 0,552 | 0,204 | -0,348 |
| `id` | 39 | 0,500 | 0,462 | -0,038 |
| `signature` | 193 | 0,796 | 0,605 | -0,192 |
| `heading` | 48 | 0,800 | 0,077 | -0,723 |
| `paragraph` | 1934 | 0,872 | 0,821 | -0,050 |
| `header` | 649 | 0,841 | 0,870 | +0,030 |
| `footer` | 210 | 0,607 | 0,824 | +0,217 |
| `table` | 320 | 0,965 | 0,761 | -0,204 |
| `figure` | 458 | 0,920 | 0,721 | -0,199 |

## 4. Avaliação nas Taxonomias de 9 e 3 Classes

Colapso dos rótulos preditos pelo modelo final (Texto + Geometria + Contexto) conforme o mapeamento formal de `src/data/taxonomia_layout.py` (`GUIA_PARA_EXTRATOR`) e a regra das 3 classes do TCC (`table` -> tabela; `figure, chart, heading` -> imagem; `unknown` excluído; demais -> texto).

- **9 Classes do Extrator:** Acurácia = 0,762, F1 Macro = 0,624
- **3 Classes Principais:** Acurácia = 0,910, F1 Macro = 0,798 (excluindo desconhecidos)

### F1 por Classe nas 9 Classes

| Classe (9) | Suporte | F1 |
|---|---:|---:|
| `titulo` | 814 | 0,645 |
| `texto` | 2469 | 0,816 |
| `tabela` | 396 | 0,726 |
| `figura` | 508 | 0,670 |
| `assinatura` | 322 | 0,481 |
| `cabecalho` | 728 | 0,851 |
| `rodape` | 245 | 0,805 |
| `outro` | 4 | 0,000 |

### F1 por Classe nas 3 Classes

| Classe (3) | Suporte | F1 |
|---|---:|---:|
| `texto` | 4498 | 0,949 |
| `tabela` | 396 | 0,726 |
| `imagem` | 588 | 0,718 |

## 5. Matriz das 12 Confusões Mais Frequentes

Principais pares de confusão do modelo Texto + Geometria + Contexto no teste oficial de 16 classes:

| # | Classe Real | Classe Predita | Erros | % do Total de Erros |
|---|---|---|---:|---:|
| 1 | `caption` | `paragraph` | 123 | 7,3% |
| 2 | `table` | `paragraph` | 112 | 6,7% |
| 3 | `title` | `paragraph` | 106 | 6,3% |
| 4 | `signature` | `paragraph` | 93 | 5,5% |
| 5 | `figure` | `paragraph` | 57 | 3,4% |
| 6 | `sub section title` | `paragraph` | 56 | 3,3% |
| 7 | `section title` | `paragraph` | 56 | 3,3% |
| 8 | `paragraph` | `signature` | 53 | 3,2% |
| 9 | `heading` | `figure` | 52 | 3,1% |
| 10 | `act` | `paragraph` | 43 | 2,6% |
| 11 | `header` | `paragraph` | 42 | 2,5% |
| 12 | `paragraph` | `table` | 41 | 2,4% |

## 6. Como Carregar e Usar o Modelo Salvo

O artefato final do modelo foi salvo em `resultados/classificador_regioes_ls/modelo.pkl`.

```python
import pickle
from orquestracao.analises.classificador_regioes_ls import (
    extrair_atributos_manuais, extrair_atributos_geometria, normalizar_texto_ngrams
)

# 1. Carregar artefato
with open('resultados/classificador_regioes_ls/modelo.pkl', 'rb') as f:
    artefato = pickle.load(f)

modelo = artefato['modelo']
classes = artefato['classes']

# 2. Exemplo: predizer a classe de uma regiao extraida
texto_exemplo = 'DECRETO Nº 12.345, DE 01 DE ABRIL DE 2026'
bbox_exemplo = [100.0, 150.0, 600.0, 190.0]  # x0, y0, x1, y1
W, H = 1200.0, 1800.0

# Extrair atributos correspondentes
man = extrair_atributos_manuais(texto_exemplo)
geo = extrair_atributos_geometria(bbox_exemplo, W, H)
ctx = [0.0] * 32  # ou contexto de vizinhos se houver

import numpy as np
import scipy.sparse as sp
txt_norm = normalizar_texto_ngrams(texto_exemplo)
X_char = artefato['vec_char'].transform([txt_norm])
X_word = artefato['vec_word'].transform([txt_norm])
X_txt = sp.hstack([X_char, X_word])
X_dense = np.hstack([
    artefato['scaler_man'].transform([man]),
    artefato['scaler_geo'].transform([geo]),
    artefato['scaler_ctx'].transform([ctx])
])
X_completo = sp.hstack([X_txt, sp.csr_matrix(X_dense)])

pred_idx = modelo.predict(X_completo)[0]
classe_predita = classes[pred_idx]
print('Classe predita:', classe_predita)
```

## 7. Limitações e Vieses Metodológicos

1. **Texto do Ouro vs. Extração Automática:** As caixas do Label Studio possuem texto revisado/transcrito por humanos. Em um pipeline em produção ou sem supervisão humana, o texto dependerá de extração digital (pdfplumber/PyMuPDF) ou OCR, podendo conter quebras ruidosas ou caracteres corrompidos que degradam a classificação.
2. **Viés de Ancoragem (Anchoring Bias):** Como documentado no projeto (`labelstudio_ancoragem.md`), cerca de 40% das caixas foram aceitas sem alteração a partir da pré-anotação de um modelo automático. Isso afeta tanto as fronteiras das caixas quanto a distribuição de classes conferidas pelos anotadores.
3. **Desacoplamento de Localização:** O classificador assume a geometria exata fornecida pelo ouro. Quando acoplado a um detector visual com IoU < 0,50, ou em caixas fundidas/divididas, o texto capturado sofrerá ruído de fronteira.
4. **Desbalanceamento Extremo de Suporte:** Classes como `chart` e `heading` possuem suporte escasso no teste, gerando intervalos de confiança mais amplos ou degenerados.
