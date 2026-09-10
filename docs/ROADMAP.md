# Roadmap e Próximos Passos

O que falta para o TCC, em ordem de prioridade, e como cada documento do repositório
alimenta o texto final.

---

## 🗣️ Perguntas para levar ao orientador

1. **Rótulo silver.** Usar a ordem do fluxo do PDF como supervisão, restrita aos
   veículos em que ela concorda com a heurística de colunas, é aceitável para o
   treino — deixando a avaliação definitiva para o Golden Dataset manual?
2. **Goiás como teste out-of-domain.** O acervo não tem Goiás. Treinar nas 23 UFs e
   testar em Goiás mede generalização para um layout nunca visto. De acordo?
3. **APIs comerciais como terceiro competidor.** As saídas do Azure e do Google em
   Japeri sugerem que já houve orçamento para isso. Há créditos para processar o
   Golden Dataset nas duas APIs? Isso completaria o eixo de custo financeiro.
4. **Granularidade.** Blocos (alinhado a detectores tipo YOLO) ou palavras (como no
   LayoutReader, onde o BLEU é mais informativo)?
5. **Infraestrutura.** Os scripts do acervo mencionam um servidor `/nfs/`. Há GPU com
   mais memória no laboratório? LayoutXLM e LayoutReader ficam apertados em 6 GB.
6. **DocLayNet.** Ele anota categorias de layout, **não** ordem de leitura. O papel
   dele no trabalho seria pré-treino/detecção de layout — confirmar se ainda faz
   sentido mantê-lo no plano.

---

## 🔴 Prioridade alta (próximas 2 semanas)

### 1. Golden Dataset — a avaliação definitiva
- [ ] Baixar diários de Goiás em [diariooficial.go.gov.br](https://www.diariooficial.go.gov.br)
- [ ] Selecionar **20 páginas estratificadas por layout**: 1, 2 e 3 colunas; com e sem
      cabeçalho de largura inteira; ao menos 3 com tabelas
- [ ] Extrair os blocos com `src/data/extrator.py`
- [ ] Anotar a ordem de leitura à mão. Sugestão: renderizar cada página com os blocos
      numerados (como na figura 2) e corrigir a ordem num JSON
- [ ] Anotação dupla em parte das páginas (idealmente com outra pessoa) para medir a
      concordância entre anotadores — dá o **teto humano** da tarefa

### 2. Auditar o rótulo silver
- [ ] Inspecionar visualmente ~30 páginas dos veículos "confiáveis" e contar em quantas
      o fluxo do PDF coincide com a leitura humana
- [ ] Reportar essa taxa na metodologia — é o que legitima a supervisão silver

### 3. LLM de texto, não multimodal
- [ ] `ollama pull qwen2.5:7b` (≈ 4,7 GB) e repetir `src/eval/llm_ordem.py --modelo qwen2.5:7b`
- [ ] Versão *few-shot* (2 páginas resolvidas no prompt)
- [ ] Medir o efeito do tamanho da página: a confiabilidade de formato cai com o número de blocos?

### 4. APIs comerciais
- [ ] Converter as saídas do Azure (`resultado_azure_lote_layout.jsonl`) e do Google
      (`document (1).json`) para o formato do protocolo
- [ ] Medir a concordância Azure × Google × fluxo do PDF na mesma página
- [ ] Levantar o preço por página de cada API para o eixo de custo

---

## 🟡 Prioridade média

- [ ] **LayoutXLM** (multilíngue) no lugar do LayoutLM em inglês — o tokenizador atual
      remove acentos e fragmenta o português
- [ ] **LayoutReader** (Wang et al., 2021) como baseline forte da literatura
- [ ] **Granularidade de linha** — mais blocos por página, tarefa mais difícil
- [ ] **Extração mais rápida** com PyMuPDF (tipicamente dezenas de vezes mais rápido que
      o `pdfplumber`) para escalar de ~1.000 para dezenas de milhares de páginas
- [ ] **Pré-treino de adaptação de domínio**: continuar o pré-treino do LayoutLM
      (MLM com posição 2D) sobre o acervo, e medir o ganho
- [ ] **Eficiência completa**: memória de pico, vazão em lote, custo estimado em
      R$ por mil páginas (energia local × preço das APIs)
- [ ] **Análise de erros**: categorizar as páginas em que cada método falha (tabelas,
      notas de rodapé, colunas desiguais)

## 🟢 Prioridade baixa / se sobrar tempo

- [ ] Ordem de leitura em nível de palavra, comparável ao LayoutReader
- [ ] Impacto a jusante: medir se a ordem correta melhora um sistema de RAG simples
      sobre os diários (fecha o argumento da introdução)
- [ ] Interface de demonstração: enviar um PDF e ver a ordem de leitura desenhada

---

## 📝 Mapa do texto do TCC

| Capítulo | Fonte no repositório |
|---|---|
| 1. Introdução — problema, motivação (RAG e agentes) | `README.md` (seções Problema e Objetivo) |
| 2. Fundamentação teórica | `docs/LITERATURA.md` |
| 3. Dados — o acervo | `docs/ACERVO.md` |
| 4. Metodologia | `docs/METODOLOGIA.md` |
| 5. Desenvolvimento — decisões e dificuldades | `docs/DIARIO_DE_BORDO.md` |
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
python src/eval/llm_ordem.py --modelo llava:7b --paginas 40
python src/eval/comparar.py
python src/eval/figuras.py
```
