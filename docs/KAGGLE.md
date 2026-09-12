# Rodando os experimentos pesados no Kaggle

**Por que o Kaggle:** GPU grátis (duas T4 de 16 GB) por cerca de 30 horas por semana. É o
bastante para duas coisas que a RTX 4050 de 6 GB não dá conta: rodar LLMs de 7B a 32B
parâmetros inteiras na GPU, e treinar a curva de aprendizado das duas formulações do
LayoutLM sem ocupar o seu computador por horas.

São **dois notebooks**, cada um com seu próprio limite de 12 horas:

| Notebook | O que faz | Tempo estimado |
|---|---|---|
| `kaggle_treino_ordem.ipynb` | Curva de aprendizado das duas formulações do LayoutLM, ablações da formulação de sucessor, varredura do limiar de decodificação, latência de todos os métodos na T4, avaliação contra a anotação humana | 2 a 4 h |
| `kaggle_llm_ordem.ipynb` | Qwen 2.5 de 7B, 14B e 32B, zero-shot e com 2 exemplos, no teste e nas páginas anotadas | 4 a 6 h |

Rode o de treino **primeiro**: ele produz os checkpoints e as predições que deixam a tabela
final do outro completa.

Tudo lá dentro usa o mesmo protocolo do projeto: mesmas páginas, mesmos blocos embaralhados
pela mesma permutação, mesma referência, mesmas métricas.

---

## Passo a passo

### 1. Conta (uma vez só)

Crie a conta em [kaggle.com](https://www.kaggle.com) e verifique o telefone (*Settings* →
*Phone verification*). Sem a verificação, o notebook não tem GPU nem internet.

### 2. Gerar o pacote (no seu computador)

```bash
venv\Scripts\python.exe src\kaggle\montar_pacote.py
```

Isso gera, em `dist\kaggle\`:

- `tcc_ordem_leitura.zip`, cerca de 14 MB: código, **todas** as páginas já extraídas (as 262
  do protocolo, as 3.117 extras da curva e as 269 de Japeri), as tarefas e as anotações do
  Golden Dataset, e as predições locais dos outros métodos. Os 19 GB de PDFs e as imagens do
  Golden não vão — nada lá precisa deles;
- os dois notebooks (há cópias em `notebooks/`).

Rode de novo sempre que o código ou os dados mudarem — inclusive **depois de anotar o
Golden Dataset**, para que a anotação suba junto.

### 3. Subir o pacote como Dataset

*Datasets* → *New Dataset* → arraste o `tcc_ordem_leitura.zip` → título
`tcc-ordem-leitura` → deixe **Private** → *Create*.

Nas próximas vezes, em vez de criar outro dataset, abra o mesmo e use *New Version*: os
notebooks continuam apontando para ele.

### 4. Importar cada notebook

1. *Code* → *New Notebook* → *File* → *Import Notebook* → escolha o `.ipynb`.
2. No painel à direita, em *Session options*: *Accelerator* **GPU T4 x2** e *Internet* **On**.
3. *Add Input* → *Your Datasets* → `tcc-ordem-leitura`.

### 5. Rodar

1. Se quiser, ajuste a célula `CONFIGURACAO` no topo.
2. *Save Version* → **Save & Run All (Commit)** → *Save*. A execução acontece em segundo
   plano, por até 12 horas, mesmo com o navegador fechado e o computador desligado.

### 6. Trazer os resultados

1. Na versão salva, aba *Output* → baixe `resultados_kaggle.zip`.
2. No projeto:

   ```bash
   venv\Scripts\python.exe src\kaggle\importar_resultados.py caminho\para\resultados_kaggle.zip
   ```

   Isso copia as predições para `resultados/`, guarda uma cópia versionada em
   `resultados/kaggle/<data>/` e atualiza `resultados/comparacao.md`.
3. O notebook de treino também deixa o checkpoint do melhor modelo (`curva_layoutlm_sucessor_n*.pt`,
   cerca de 450 MB) solto na aba *Output*. Baixe só se quiser rodar esse modelo localmente;
   coloque-o em `models\layoutlm_ordem\`.

---

## O que a célula de configuração controla

**`kaggle_treino_ordem.ipynb`**

| Variável | Para que serve |
|---|---|
| `TAMANHOS` | Tamanhos de treino da curva. `0` significa "todas as páginas extras disponíveis" |
| `MODELOS` | `layoutlm_sucessor` (formulação nova) e `layoutlm` (pontual). A nova vem primeiro, para o caso de o tempo acabar |
| `MICRO_BATCH` | Páginas por passagem na GPU. Na T4 (16 GB) cabe 12; o batch **efetivo** continua 8 por acumulação, então a otimização não muda — só a velocidade |
| `ABLACOES` | Treina as variantes sem viés geométrico, sem perda de posição e sem layout 2D |
| `LIMIARES` | Varredura do limiar da decodificação em cadeias. Custa segundos: só troca a decodificação de um modelo já treinado |
| `LOTE_GOLDEN` | Lote de anotação a avaliar, se já houver `anotacoes.jsonl` |

**`kaggle_llm_ordem.ipynb`**

| Variável | Para que serve |
|---|---|
| `MODELOS` | Modelos do Ollama, na ordem em que rodam. O 32B ocupa as duas T4 |
| `FEW_SHOT` | `0` = zero-shot; `2` = dois exemplos resolvidos (de páginas de treino) no prompt |
| `PARTICOES` | `teste` = 95 páginas do protocolo; `golden:<lote>` = páginas com anotação humana |
| `MAX_BLOCOS` | Limite de blocos por página. 200 inclui todas |

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
  checkpoint. Para levar os checkpoints (+450 MB cada), use `montar_pacote.py --com-modelo`.
- **O micro-batch não é um hiperparâmetro escondido.** Ele muda quantas páginas passam
  juntas pela GPU, não o batch efetivo do otimizador (8, por acumulação de gradiente).
  Treinar na T4 com `MICRO_BATCH = 12` dá o mesmo modelo que treinar na 4050 com 4, mais rápido.
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
| A sessão caiu no meio | Rode de novo: `--retomar` continua as LLMs de onde pararam, e a curva pula os tamanhos que já estão em `curva.json` |
| "Lote golden_v1 ainda sem anotacoes.jsonl" | Anote no projeto, refaça o pacote e suba uma nova versão do dataset |
| Acabou a cota semanal | Veja em *Settings* quanto resta; a cota renova toda semana |
| Sem memória (OOM) na T4 | Baixe `MICRO_BATCH` para 8 ou 4 |
