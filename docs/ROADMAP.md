# Roadmap e Próximos Passos

O que falta para o TCC, em ordem de prioridade, e como cada documento do repositório
alimenta o texto final. Atualizado em 2026-09-12.

---

## 🗣️ Perguntas para levar ao orientador

1. **Foco em RI.** A ordem de leitura é o objeto; a área é Recuperação de Informação. Além
   da avaliação da ordenação (τ, sucessor correto), o senhor espera uma **avaliação
   extrínseca** — o efeito na busca e num RAG? O piloto em Japeri já indica onde a ordem
   pesa: no texto entregue, e não em achar a página (resultados, seção 6).
2. **Atos de Japeri.** Como os 421 atos de `json_atos_japeri` foram produzidos: por
   anotação manual ou pela saída do Azure? Isso define se servem de referência gold ou silver.
3. **Rótulo silver.** Usar a ordem do fluxo do PDF como supervisão, restrita aos
   veículos em que ela concorda com a heurística de colunas, é aceitável para o
   treino — deixando a avaliação definitiva para o Golden Dataset manual?
4. **Goiás como teste fora do domínio.** O acervo não tem Goiás. Treinar nas outras UFs e
   testar em Goiás mede generalização para um layout nunca visto. De acordo?
5. **Infraestrutura.** Rodar as LLMs abertas (Qwen 2.5 de 7B a 32B) na GPU gratuita do
   Kaggle é aceitável? Os scripts do acervo mencionam um servidor `/nfs/`: há GPU no
   laboratório como alternativa?
6. **APIs comerciais como terceiro competidor.** As saídas do Azure e do Google em
   Japeri sugerem que já houve orçamento para isso. Há créditos para processar o
   Golden Dataset nas duas APIs? Isso completaria o eixo de custo financeiro.
7. **Granularidade.** Blocos (alinhado a detectores tipo YOLO) ou palavras (como no
   LayoutReader, onde o BLEU é mais informativo)?
8. **DocLayNet.** Ele anota categorias de layout, **não** ordem de leitura. O papel
   dele no trabalho seria pré-treino/detecção de layout — confirmar se ainda faz
   sentido mantê-lo no plano.

---

## ✅ Pronto para usar

| O quê | Como | Guia |
|---|---|---|
| Ferramenta de anotação e lote `golden_v1` (30 páginas) | `venv\Scripts\python.exe src\anotacao\servidor.py` | [GUIA_ANOTACAO.md](GUIA_ANOTACAO.md) |
| Avaliação contra a anotação humana | `venv\Scripts\python.exe src\eval\avaliar_golden.py --lote golden_v1` | idem |
| Re-extração e medida de qualidade da segmentação | `venv\Scripts\python.exe src\data
eextrair.py --entrada data\processedlocos --so-medir` | [METODOLOGIA.md](METODOLOGIA.md), seção 3.3.1 |
| LayoutLM com predição de sucessor | `venv\Scripts\python.exe src\models\layoutlm_sucessor.py treinar` | [METODOLOGIA.md](METODOLOGIA.md), seção 5.4 |
| Pacote e **dois** notebooks do Kaggle (treino e LLMs) | `venv\Scripts\python.exe src\kaggle\montar_pacote.py` | [KAGGLE.md](KAGGLE.md) |
| Piloto de RI em Japeri | `venv\Scripts\python.exe src\ri\piloto_japeri.py` | [RESULTADOS_PRELIMINARES.md](RESULTADOS_PRELIMINARES.md), seção 6 |
| Curva de aprendizado | `venv\Scripts\python.exe src\rodar_curva_aprendizado.py` | idem, seção 7 |

---

## 🔴 Prioridade alta (próximas 2 semanas)

### 1. Anotar o Golden Dataset
- [x] Ferramenta de anotação e lote `golden_v1` (10 páginas `silver` + 20 `incerto`)
- [ ] Anotar as 30 páginas (estimativa: 1 a 2 horas)
- [ ] Pedir a um colega que anote 8 a 10 das mesmas páginas (concordância entre anotadores)
- [ ] Rodar `avaliar_golden.py`: o rótulo silver se sustenta? Quem vence nos veículos incertos?
- [ ] Baixar 10 a 20 edições de Goiás e preparar o lote `goias`

### 2. Rodar tudo no Kaggle
- [x] Pacote, dois notebooks (treino e LLMs) e importador
- [ ] `kaggle_treino_ordem.ipynb`: curva das duas formulações, ablações, varredura do limiar
- [ ] `kaggle_llm_ordem.ipynb`: Qwen 2.5 de 7B, 14B e 32B, zero-shot e few-shot, no teste e no Golden
- [ ] Tabela de eficiência na mesma máquina (`resultados/latencia_kaggle_t4.json`)

### 3. Decidir pela curva de aprendizado
- [x] Curva do LayoutLM pontual: sobe sem estacionar (τ 0,694 → 0,786 de 152 a 3.235 páginas)
- [ ] Rodar a curva da formulação de sucessor no Kaggle e comparar as duas nos dois painéis da figura 7
- [ ] Se o τ continua subindo: escalar os dados (PyMuPDF para extrair dezenas de milhares de páginas)

### 4. Mudar a formulação do LayoutLM
- [x] Cabeça par a par sobre o LayoutLM, com viés geométrico relativo e perda de entropia
      cruzada por sucessor (`src/models/layoutlm_sucessor.py`)
- [x] Decodificação em cadeias: trechos locais de alta confiança ordenados pela cabeça de
      posição — resolve o τ baixo da decodificação em caminho puro
- [x] Comparar τ e sucessor correto com a versão pontual, mesmo orçamento de treino
- [ ] Ablações no Kaggle: sem viés geométrico, sem perda de posição, sem layout 2D
- [ ] Varredura do limiar da cadeia (0 a 0,9)
- [ ] Um decodificador com ponteiro, como o LayoutReader, como próximo passo

### 5. Análise de sensibilidade à granularidade
A segmentação em blocos é uma escolha nossa, e o TCC precisa mostrar que as conclusões não
dependem dela. Há duas segmentações das **mesmas páginas** (`blocos` e `blocos_v1`) e um
detector comercial disponível.
- [x] Corrigir o corte de linha (texto embaralhado dentro do bloco); medir antes/depois
- [ ] Rodar o pipeline inteiro nas duas segmentações (`TCC_DIR_BLOCOS`) e comparar o ranking
- [ ] Testar a hipótese: a super-segmentação inflava o sucessor da XY-cut?
- [ ] Converter os blocos das APIs comerciais para o formato do protocolo (Azure em 12
      páginas do Estado do RJ e de Japeri; Google em 2) e rodar a comparação sobre eles
- [ ] Investigar o resíduo: ~15% de caixas ainda se sobrepõem, concentradas em páginas de
      tabela densa

### 6. Avaliação extrínseca de RI (o elo com a área)
- [x] Piloto em Japeri: a busca de páginas satura; o texto entregue depende da ordem
- [ ] Coleção maior (vários veículos) e consultas em linguagem natural
- [ ] Busca densa (embeddings multilíngues) além do BM25
- [ ] RAG completo: perguntas sobre os atos, respondidas por uma LLM com os trechos de cada ordenação (Kaggle)

---

### 7. Refazer todos os números sobre a segmentação corrigida
- [ ] `baselines.py`, `caracterizar.py`, BiLSTM, LayoutLM (as duas formulações), `comparar.py`, figuras
- [ ] Piloto de RI e curva de aprendizado (a curva vai para o Kaggle)
- [ ] Refazer o pacote do Kaggle e a página de apresentação

---

## 🟡 Prioridade média

- [ ] **APIs comerciais**: converter as saídas do Azure (`resultado_azure_lote_layout.jsonl`) e
      do Google (`document (1).json`) para o formato do protocolo; preço por página
- [ ] **LayoutXLM** (multilíngue) no lugar do LayoutLM em inglês — o tokenizador atual
      remove acentos e fragmenta o português
- [ ] **LayoutReader** (Wang et al., 2021) como baseline forte da literatura
- [ ] **Extração mais rápida** com PyMuPDF (tipicamente dezenas de vezes mais rápido que
      o `pdfplumber`; os PDFs de PE levaram ~50 s cada)
- [ ] **Auditoria visual de SP**, onde a XY-cut e o fluxo do PDF estão anticorrelacionados
- [ ] **Análise de erros**: categorizar as páginas em que cada método falha (tabelas,
      notas de rodapé, colunas desiguais)
- [ ] **Várias sementes** por método, para intervalos entre execuções

## 🟢 Prioridade baixa / se sobrar tempo

- [ ] Granularidade de linha ou de palavra, comparável ao LayoutReader
- [ ] Pré-treino de adaptação de domínio do LayoutLM sobre o acervo
- [ ] Interface de demonstração: enviar um PDF e ver a ordem de leitura desenhada

---

## 📝 Mapa do texto do TCC

| Capítulo | Fonte no repositório |
|---|---|
| 1. Introdução — problema, motivação (RAG e agentes) | `README.md`; resultados, seção 6, como evidência do efeito em RI |
| 2. Fundamentação teórica | `docs/LITERATURA.md` |
| 3. Dados — o acervo e o Golden Dataset | `docs/ACERVO.md`, `docs/GUIA_ANOTACAO.md` |
| 4. Metodologia | `docs/METODOLOGIA.md` |
| 5. Desenvolvimento — decisões e dificuldades | `docs/DIARIO_DE_BORDO.md`, `docs/KAGGLE.md` |
| 6. Resultados e discussão | `docs/RESULTADOS_PRELIMINARES.md`, `docs/figuras/` |
| 7. Conclusão e trabalhos futuros | este roadmap |

## ♻️ Como reproduzir tudo do zero

```bash
python src/data/extrair_zips.py C:\caminho\para\os\zips
python src/data/extrator.py --pdfs-por-uf 14 --paginas-por-pdf 4 --workers 9
python src/eval/caracterizar.py
python src/eval/baselines.py
python src/models/layoutlm_ordem.py treinar
python src/models/layoutlm_ordem.py avaliar
python src/models/lstm_ordem.py --variante geo_texto
python src/eval/llm_ordem.py --modelo llava:7b --paginas 20 --max-blocos 25
python src/eval/comparar.py
python src/eval/figuras.py

# coletas extras (pastas separadas; nao alteram o protocolo)
python src/data/extrator.py --ufs official_diary_rj_japeri --pdfs-por-uf 999 --paginas-por-pdf 9999 --incluir-capa --workers 3 --saida data/processed/blocos_ri_japeri
python src/data/extrator.py --ufs official_diary_RJ_volta_redonda official_diary_ba_salvador official_diary_pa official_diary_pe --pdfs-por-uf 250 --paginas-por-pdf 6 --seed 7 --workers 6 --saida data/processed/blocos_extra
python src/data/extrator.py --ufs official_diary_pr official_diary_rr official_diary_sc --pdfs-por-uf 70 --paginas-por-pdf 5 --seed 7 --workers 7 --saida data/processed/blocos_extra

python src/ri/piloto_japeri.py
python src/rodar_curva_aprendizado.py
python src/anotacao/preparar_lote.py --lote golden_v1 --grupo silver:10 --grupo incerto:20
```

A coleta de PE foi interrompida em 525 de 1.089 PDFs por lentidão (seção 3.5 do diário de
bordo); para reproduzir exatamente, rode a segunda linha e interrompa no mesmo ponto, ou
aceite uma amostra de PE um pouco diferente.
