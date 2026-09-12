# Rodando as LLMs no Kaggle

**Por que o Kaggle:** GPU grátis (duas T4 de 16 GB) por cerca de 30 horas por semana. É o
bastante para rodar LLMs de 7B, 14B e 32B parâmetros inteiras na GPU. Na RTX 4050 (6 GB),
só um 7B cabe, e o llava:7b ainda ficou com 34% na CPU.

**O que roda lá** (tudo com o mesmo protocolo do projeto: mesmas páginas, mesmos blocos
embaralhados, mesma referência, mesmas métricas):

- as LLMs Qwen 2.5 de 7B, 14B e 32B, zero-shot e com 2 exemplos resolvidos (few-shot),
  nas 95 páginas de teste e nas 30 páginas do Golden Dataset;
- a latência de ingênua, XY-cut, BiLSTM e LayoutLM **na mesma T4**, para que a tabela de
  eficiência compare máquinas iguais.

---

## Passo a passo

### 1. Conta (uma vez só)

Crie a conta em [kaggle.com](https://www.kaggle.com) e verifique o telefone (*Settings* →
*Phone verification*). Sem a verificação, o notebook não tem GPU nem internet.

### 2. Gerar o pacote (no seu computador)

```
venv\Scripts\python.exe src\kaggle\montar_pacote.py
```

Isso gera, em `dist\kaggle\`:

- `tcc_ordem_leitura.zip`, com cerca de 2 MB: código, blocos já extraídos, tarefas do
  Golden (sem imagens) e as predições locais dos outros métodos. Os 19 GB de PDFs não vão;
- `kaggle_llm_ordem.ipynb`, o notebook (há uma cópia em `notebooks/`).

Rode de novo sempre que o código ou os dados mudarem.

### 3. Subir o pacote como Dataset

*Datasets* → *New Dataset* → arraste o `tcc_ordem_leitura.zip` → título
`tcc-ordem-leitura` → deixe **Private** → *Create*.

### 4. Importar o notebook

1. *Code* → *New Notebook* → *File* → *Import Notebook* → escolha `kaggle_llm_ordem.ipynb`.
2. No painel à direita, em *Session options*: *Accelerator* **GPU T4 x2** e *Internet* **On**.
3. *Add Input* → *Your Datasets* → `tcc-ordem-leitura`.

### 5. Rodar

1. Se quiser, ajuste a célula `CONFIGURACAO`: modelos, few-shot e partições.
2. *Save Version* → **Save & Run All (Commit)** → *Save*. A execução acontece em segundo
   plano, por até 12 horas, mesmo com o navegador fechado.

Estimativa de tempo, a confirmar na primeira execução: com a configuração padrão (3 modelos ×
zero-shot e few-shot × teste e Golden), algo entre 4 e 6 horas. O 32B é o mais demorado.

### 6. Trazer os resultados

1. Na versão salva, aba *Output* → baixe `resultados_kaggle.zip`.
2. No projeto:

   ```
   venv\Scripts\python.exe src\kaggle\importar_resultados.py caminho\para\resultados_kaggle.zip
   ```

   Isso copia as predições para `resultados/`, guarda uma cópia versionada em
   `resultados/kaggle/<data>/` e atualiza `resultados/comparacao.md` com as LLMs novas.
3. Depois de anotar o Golden, as LLMs entram também na avaliação humana:

   ```
   venv\Scripts\python.exe src\eval\avaliar_golden.py --lote golden_v1
   ```

---

## Cuidados metodológicos (para o texto do TCC)

- **Mesma entrada para todos.** A LLM recebe os blocos na mesma permutação fixa que os
  outros métodos, rotulados B1..Bn na ordem de entrada. Os rótulos não carregam
  informação de ordem.
- **Few-shot sem vazamento.** Os exemplos resolvidos vêm só de páginas de treino, nunca
  do teste nem do Golden.
- **Determinismo.** Temperatura 0 e semente fixa. Cada execução registra modelo, GPU,
  versão do Ollama, janela de contexto e tempos em `execucoes_llm.jsonl`.
- **Eficiência na mesma máquina.** Compare a latência das LLMs com a do LayoutLM usando
  `resultados/latencia_kaggle_t4.json`, medido na mesma T4. A latência do LayoutLM não
  depende dos pesos treinados, então o notebook mede a mesma arquitetura mesmo sem o
  checkpoint. Para levar o checkpoint (+450 MB), use `montar_pacote.py --com-modelo`.
- **Formato.** A proporção de permutações válidas devolvidas por cada LLM também é um
  resultado: ela mede a confiabilidade de formato. Saídas inválidas são reparadas e
  sinalizadas.

---

## Problemas comuns

| Sintoma | Solução |
|---|---|
| "Pacote nao encontrado" | Faltou *Add Input* com o dataset `tcc-ordem-leitura` |
| Não aparece a opção de GPU ou de internet | Verifique o telefone da conta |
| Download do 32B demora | É normal: são cerca de 20 GB |
| A sessão caiu no meio | Rode de novo: `--retomar` continua de onde parou |
| Acabou a cota semanal | Veja em *Settings* quanto resta; a cota renova toda semana |
