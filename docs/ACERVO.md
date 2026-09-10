# Diagnóstico do Acervo de Diários Oficiais

Inventário e avaliação técnica do acervo cedido pelo orientador em **2026-09-09**.
Os arquivos estão em `data/raw/` (não versionados — 19 GB).

Reproduzir este diagnóstico: os scripts de análise estão descritos ao final.

---

## 📦 Visão Geral

| | |
|---|---|
| **Arquivos** | 4.644 PDFs + 16 auxiliares (JSON, TXT, PY) |
| **Volume** | 19 GB descompactados |
| **Páginas estimadas** | **~310.000** |
| **Cobertura** | 23 UFs + 8 municípios |
| **Período** | 2010–2026 (concentrado em 2021–2026) |
| **Integridade** | 154 de 155 PDFs abrem sem erro (99,4%) |
| **Camada de texto** | ~96% digitais — **dispensam OCR** |

> Para comparação: o **ReadingBank**, dataset do LayoutReader, tem ~500 mil páginas.
> Este acervo está na mesma ordem de grandeza.

---

## ✅ A Conclusão Central: os PDFs são digitais

De 62 PDFs amostrados em todas as UFs, **60 têm camada de texto** com coordenadas
extraíveis. Isso muda o desenho do pipeline:

- **Não é necessário YOLO** para detectar blocos
- **Não é necessário OCR** para ler o texto
- O `pdfplumber` entrega diretamente `(texto, x0, top, x1, bottom)` para cada palavra

O enunciado original do TCC — "YOLO e OCR geram as caixas" — descreve como o
problema aparece em pipelines de digitalização em geral. Neste acervo específico,
as caixas vêm do próprio PDF. **Isso deve ser declarado explicitamente na
metodologia**, e não enfraquece o trabalho: o problema de ordem de leitura é
idêntico, apenas a origem das caixas muda.

---

## 🎯 O Problema Existe (e é severo)

Medição sobre 155 PDFs, 2 páginas cada:

| Métrica | Resultado |
|---|---|
| Páginas **multicoluna** | **46%** |
| **Desordem média** — linhas fora de posição na ordem crua do PDF | **86%** |

Em um diário do RJ (Parte I, 2023-04-27, página 4): 2 colunas detectadas,
**130 de 133 linhas fora de posição (98%)**.

A ordem em que o PDF armazena o texto **não é** a ordem de leitura. O problema
que o TCC ataca está presente e é massivo.

---

## ⚠️ Problemas de Qualidade por UF

A coluna `cid%` mede a fração de texto que sai como `(cid:N)` — caracteres que a
fonte do PDF não permite decodificar, ou seja, texto perdido.

| UF | cid% | Situação |
|---|---|---|
| **PI** (`official_diary_pi`) | **86,3%** | ❌ **Inutilizável.** Texto majoritariamente ilegível. Use `official_diary_pi_v2` (0% cid), que o professor claramente reprocessou. |
| **AC** (`official_diary_ac`) | **32,1%** | ⚠️ Um terço do texto perdido. Excluir ou tratar com OCR. |
| RJ | 2,8% | ✅ Aceitável (concentrado no cabeçalho gráfico) |
| PE | 1,1% | ✅ Aceitável |
| **Demais 27** | **0,0%** | ✅ Limpos |

**Outro ponto de atenção:** `official_diary_ce` tem **0% de páginas multicoluna**
— é layout de coluna única. Tem pouco valor para a tarefa de ordem de leitura,
embora sirva para pré-treino de linguagem.

### PDFs corrompidos

1 de 155 na amostra (~0,6%). O próprio professor incluiu os scripts que usou para
tratá-los:

- `official_diary_ac/corrupt.py` — remove a última página com `pikepdf`
- `official_diary_ms/nois.py` — reprocessa com `ps2pdf` (Ghostscript)

O carregador de dados deve capturar exceções por arquivo e seguir adiante.

---

## 🚫 Goiás não está no acervo

**UFs presentes (23):** AC AL AM AP BA CE MA MG MS PA PB PE PI PR RJ RN RO RR RS SC SE SP TO
**UFs ausentes (4):** **GO** DF ES MT

O plano do TCC previa um *Golden Dataset* de 20 páginas de diários **de Goiás**.
Esse material precisa ser obtido à parte, em
[diariooficial.go.gov.br](https://www.diariooficial.go.gov.br). São apenas 20
páginas — perfeitamente viável manualmente.

**Isso abre uma oportunidade metodológica:** treinar nas 23 UFs do acervo e
avaliar em Goiás transforma o teste em uma avaliação de **generalização
out-of-domain** — o modelo é testado em um layout que nunca viu. É um desenho
experimental mais forte do que avaliar dentro do mesmo domínio, e um bom
argumento na defesa.

---

## 💎 Japeri (RJ): o subconjunto anotado

`official_diary_rj_japeri/` é qualitativamente diferente do resto. Além dos 40
PDFs, contém trabalho de anotação já pago e executado:

### `json_atos_japeri/`
- `decretos.json`, `portarias.json`, `leis.json`, `licitacoes.json`, `avisos.json`,
  `extratos.json`, `erratas.json`, `atas.json`, `outros.json` — atos com o **texto
  já reconstruído em ordem de leitura correta** (campos: `documento`, `texto`,
  `fonte`, `data_diario`)
- `resultado_azure_lote_layout.jsonl` / `.txt` — saída do **Azure Document
  Intelligence** (`prebuilt-layout`, API 2024-11-30): parágrafos com `polygon`
  e `content`, em ordem de leitura
- `resultado_azure_lote_ocr.txt` — OCR do Azure
- `pdf_bounding_boxes*.pdf` — visualizações das caixas detectadas

### `diarios_avaliados_apis_pagas/`
- `Google Doc AI Tests/document (1).json` — **Google Document AI**: 258 blocos
  com `boundingBox.normalizedVertices` e `text`, em ordem de leitura
- `executive_official_diary_2025-08-04_..._processado_completo.json` (34 MB)
- `*_Anotado_Resultados.pdf` — resultados anotados visualmente

### Por que isso importa

O documento `Parte I (Poder Executivo)_2021-06-10.pdf` foi processado **pelas
duas APIs comerciais**: Azure produziu 228 parágrafos, Google produziu 258 blocos.
Isso habilita três usos:

1. **Terceiro competidor na comparação** — o TCC passa de "LayoutLM × LLM" para
   **"LayoutLM local × LLM × APIs comerciais pagas"**, incluindo o eixo de custo
   financeiro real por página.
2. **Rótulos silver** — onde Azure e Google concordam, há forte evidência de
   ordem correta, utilizável como supervisão sem anotação manual.
3. **Medida de dificuldade** — onde as duas APIs discordam estão as páginas
   genuinamente difíceis, que merecem análise qualitativa no texto do TCC.

⚠️ **Cuidado metodológico:** a saída dessas APIs é *predição*, não verdade
humana. Usar como rótulo de treino é legítimo (supervisão silver, prática comum),
mas **não pode ser chamado de ground truth** na avaliação — para isso serve o
Golden Dataset anotado manualmente.

---

## 📐 Como usar o acervo nas três frentes

### 1. Pré-treinamento (~310.000 páginas)

Volume mais que suficiente. Duas rotas:

- **Adaptação de domínio do LayoutLM** — continuar o pré-treino (MLM com
  coordenadas 2D) sobre o vocabulário jurídico-administrativo brasileiro. É o
  que a literatura sugere quando o domínio-alvo difere do pré-treino original.
- **Pré-treino da baseline LSTM** — modelagem de linguagem (prever próxima
  palavra) sobre o texto dos diários, como fundamenta Dai & Le (2015).

**Excluir do pré-treino:** `official_diary_pi` (86% ilegível) e `official_diary_ac`
(32% ilegível) — texto corrompido degrada o vocabulário aprendido.

### 2. Criação do dataset supervisionado

Rotular ordem de leitura sem anotar 310 mil páginas à mão:

- **Rótulos geométricos** — para páginas de layout regular, a ordem correta é
  derivável por heurística (detectar colunas, ordenar por coluna e depois por
  `top`). Barato e escalável.
- **Rótulos silver do Azure/Google** — disponíveis para Japeri e RJ.
- **Concordância como filtro de confiança** — manter no treino apenas páginas
  onde heurística e API concordam; as divergentes vão para inspeção manual.

**Priorizar as UFs mais multicolunas**, onde o problema é mais rico:
BA-Salvador (100% multicoluna), RJ-Volta Redonda (90%), RJ-Barra do Piraí (80%),
RJ-Duque de Caxias (80%), TO (80%).

**Cuidado com vazamento:** o mesmo veículo publica com o mesmo template por anos.
Dividir treino/teste **por UF**, não aleatoriamente por página — senão o modelo
decora o layout e a métrica fica inflada.

### 3. Testes e avaliação

- **Golden Dataset** — 20 páginas anotadas manualmente. Único conjunto onde
  BLEU e ARD podem ser reportados como verdade. Baixar de Goiás (out-of-domain)
  ou reservar uma UF do acervo.
- **Conjunto de estresse** — páginas com cabeçalho/rodapé de largura inteira e
  3+ colunas, que quebram heurísticas ingênuas.
- **Baseline obrigatória** — reportar sempre a ordem crua do PDF como piso de
  comparação. Com 86% de desordem média, é um piso honesto e informativo.

---

## 🔁 Reprodução do diagnóstico

Os scripts usados foram, em ordem:

1. **Extração** — `zipfile` com saneamento de nomes. Atenção: a pasta raiz dos
   zips do Google Drive chama-se `"Diários "`, **com espaço final**, que o
   Windows rejeita como nome de diretório. Sem saneamento, a extração falha 100%.
2. **Diagnóstico digital × escaneado** — `pdfplumber`, contagem de `chars` na
   segunda página (a primeira costuma ser capa).
3. **Qualidade por UF** — fração de `(cid:N)`, detecção de colunas pela proporção
   de linhas curtas, desordem comparando a ordem crua com a ordem coluna-a-coluna.
4. **Contagem de páginas** — `pypdf`, amostra de 12 PDFs por UF extrapolada.
