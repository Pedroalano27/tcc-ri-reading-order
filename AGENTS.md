# AGENTS.md — manual para agentes de IA neste repositório

Este projeto é trabalhado por **mais de um agente de IA ao mesmo tempo** (Claude Code,
Codex, Antigravity), na mesma pasta, sob a supervisão do Pedro, autor do TCC. Este arquivo
vale para todos eles.

## Antes de fazer qualquer coisa

1. Leia [`docs/HANDOFF.md`](docs/HANDOFF.md) — estado atual do projeto, com precisão.
2. Leia as entradas mais recentes de [`COMUNICACAO_AGENTES.md`](COMUNICACAO_AGENTES.md) —
   o que os outros agentes fizeram, acharam ou estão fazendo agora.
3. Confira a seção **Reservas ativas** do quadro. Se o arquivo, a pasta ou a GPU de que
   você precisa estiver reservado por outro agente, não mexa: escolha outra tarefa ou
   registre um PEDIDO.
4. Reserve o que vai usar (adicione uma linha em Reservas ativas) **antes** de começar.

## Ao terminar (ou ao parar no meio)

1. Registre uma entrada no quadro, logo abaixo do marcador `NOVAS ENTRADAS AQUI`, no
   formato descrito lá. Diga o que fez, quais arquivos tocou, o resultado **com números** e
   o que fica para depois.
2. Remova sua linha de Reservas ativas.
3. Se mudou o estado de uma tarefa (T01, T02...), atualize a tabela de tarefas.
4. Se descobriu algo que muda o estado descrito em `docs/HANDOFF.md`, atualize o handoff.

## Se você foi despachado pelo Claude

Algumas sessões são abertas pelo Claude por linha de comando, com
[`orquestracao/despachar.py`](orquestracao/despachar.py): o Codex CLI (`gpt-6-astra`) recebe as
tarefas técnicas e o Antigravity CLI (Gemini Flash) as braçais. Nesse caso, o prompt que você
recebeu vale acima das instruções de "Antes" e "Ao terminar" deste arquivo:

- **não edite `COMUNICACAO_AGENTES.md`**: o Claude reservou antes e registra depois, a partir
  da sua resposta final;
- mexa **só** no que o escopo do prompt permite;
- termine com as seções `FEITO`, `ARQUIVOS`, `EVIDÊNCIA` e `PENDÊNCIAS`.

As regras duras abaixo continuam valendo integralmente.

## O projeto em cinco linhas

TCC de Recuperação de Informação (INF-UFG): **detecção de ordem de leitura em Diários
Oficiais**. Dado um conjunto de blocos de texto com coordenadas e sem ordem, recuperar a
ordem de leitura humana. Compara heurísticas geométricas (XY-cut), BiLSTM, LayoutLM (duas
formulações) e LLMs, no trade-off eficácia × eficiência. Todo o texto do projeto é em
português. Conceitos explicados em [`docs/ENTENDA_O_PROJETO.md`](docs/ENTENDA_O_PROJETO.md).

## Ambiente

- Windows 11. Pasta do projeto: `C:\Users\pedro\dev\tcc-ri-reading-order`.
- **Python 3.11 do ambiente virtual: sempre `venv\Scripts\python.exe`.** O `python` do PATH
  é o atalho da Microsoft Store e trava.
- GPU: NVIDIA RTX 4050 Laptop, **6 GB**. `torch 2.9.1+cu128`, driver 577.05.
- 20 núcleos lógicos. `pdfplumber` é o gargalo de extração.
- Não há suíte de testes automatizados. A validação é por scripts (seção Validação).

## Regras duras

1. **Nunca apague, edite ou regenere anotação humana** (`data/golden/**/anotacoes.jsonl`),
   mesmo que o nome do anotador pareça de teste. Arquive numa subpasta com um `LEIAME.md`
   explicando. O nome do anotador fica guardado no navegador e pode vir preenchido errado.
2. **Nunca regenere um lote do Golden** (`src/data/reextrair.py --no-lugar` sobre
   `tarefas.jsonl`) que tenha anotação humana: os identificadores de bloco mudam e a
   anotação deixa de valer.
3. **Nunca modifique `data/raw/`** (acervo do orientador, 19 GB, sem cópia).
4. **Uma tarefa de GPU por vez.** Reserve a GPU no quadro. Dois treinos do LayoutLM na
   mesma 6 GB estouram a memória.
5. **Não faça commit, push, merge ou rebase sem o Pedro pedir.** Nunca force push.
6. **Não publique nada externamente** (Kaggle, GitHub, APIs, Artifacts) sem autorização
   explícita do Pedro na conversa. As contas são dele.
7. **Todo número escrito em documento vem de um arquivo em `resultados/`** ou de um
   comando registrado no quadro. Não arredonde de memória, não estime.
8. **Decisão metodológica** (o que muda um número do TCC: referência, divisão
   treino/teste, métricas, filtros, segmentação final) exige uma entrada `DECISÃO` no
   quadro com justificativa **e** confirmação do Pedro.
9. **Não avalie predições contra blocos de outra segmentação.** Predições
   (`resultados/pred_*.jsonl`) guardam identificadores de bloco; eles só valem para a
   pasta de blocos em que foram geradas. Use `TCC_DIR_BLOCOS` para apontar a pasta certa.
10. **Não troque arquivos de outro agente por reescrita inteira.** Edite o trecho. Se
    precisar reescrever, registre antes no quadro.

## Mapa do repositório

```text
AGENTS.md                  este manual
COMUNICACAO_AGENTES.md     quadro compartilhado entre agentes (tarefas, reservas, registro)
CLAUDE.md                  ponteiro para este manual (lido pelo Claude Code)
docs/
  HANDOFF.md               estado atual, onde está cada informação, próximos passos
  ENTENDA_O_PROJETO.md     guia didático do projeto inteiro, com glossário
  METODOLOGIA.md           desenho experimental (dados, protocolo, métodos, métricas, ameaças)
  RESULTADOS_PRELIMINARES.md  números e figuras (segmentação v1)
  DIARIO_DE_BORDO.md       histórico; no fim, tabelas de problemas e de decisões
  ROADMAP.md               pendências e perguntas para o orientador
  GUIA_ANOTACAO.md         regras de anotação do Golden Dataset
  KAGGLE.md                passo a passo dos notebooks do Kaggle
  ACERVO.md                inventário dos 4.644 PDFs
  LITERATURA.md            fichamento
  figuras/                 figuras geradas por src/eval/figuras.py e outros
  apresentacao/            fonte da página de apresentação para o orientador
src/
  data/extrator.py         PDF → palavras → linhas → blocos → três ordens candidatas
  data/reextrair.py        re-extrai AS MESMAS páginas com o código atual; mede qualidade
  eval/protocolo.py        divisão, referência, entrada embaralhada; TCC_DIR_BLOCOS
  eval/metrics.py          τ de Kendall, sucessor correto, ARD, BLEU, acerto exato
  eval/caracterizar.py     concordância entre ordens por veículo → splits.json
  eval/baselines.py        ordem do detector, ingênua, XY-cut
  eval/comparar.py         tabela principal, IC, p10, Wilcoxon → resultados/comparacao.*
  eval/figuras.py          figuras e paleta (COR, ROTULO)
  eval/llm_ordem.py        LLM via Ollama, zero/few-shot, com retomada
  eval/avaliar_golden.py   métodos contra a anotação humana
  eval/latencia_hardware.py  latência de todos os métodos na mesma máquina
  models/lstm_ordem.py     BiLSTM (texto, geometria, ambos)
  models/layoutlm_ordem.py LayoutLM pontual (learning to rank)
  models/layoutlm_sucessor.py  LayoutLM que prevê o sucessor; decodificação em cadeias
  anotacao/                ferramenta de anotação (servidor.py na porta 8770)
  kaggle/                  pacote e notebooks do Kaggle; importador de resultados
  ri/piloto_japeri.py      avaliação extrínseca de RI (BM25, fidelidade de frases)
  rodar_curva_aprendizado.py  curva de aprendizado, retomável
data/                      raw/ (PDFs), processed/ (blocos), golden/ (anotação) — ver HANDOFF 2.3
models/                    checkpoints (não versionados) — ver HANDOFF 2.4
resultados/                predições, comparações, logs — ver HANDOFF 2.5
notebooks/                 notebooks do Kaggle gerados por src/kaggle/montar_pacote.py
```

Os módulos `src/data/parser.py`, `src/models/lstm.py` e `src/eval/llm_client.py` são de um
escopo anterior do TCC e não são usados.

## Convenções de código

- Comentários e docstrings dos `.py` em **português sem acento** (é o padrão existente).
  Documentos `.md` em português **com** acento.
- Cada módulo começa com um docstring que explica o que faz, **por quê** e como usar.
  Mantenha esse padrão; é dali que o texto do TCC é escrito.
- Caminhos a partir de `RAIZ_PROJETO` / `DIR_RESULTADOS` de `src/eval/protocolo.py`.
- Predições: `resultados/pred_<metodo>.jsonl`, uma linha por página,
  `{"page_id", "ordem_pred", "tempo_ms"}`. O `comparar.py` descobre métodos novos sozinho;
  nomes de exibição ficam em `NOMES` (`comparar.py`) e `ROTULO`/`COR` (`figuras.py`).
- Métrica nova em `metrics.py` precisa entrar também em `avaliar()`: os consumidores leem
  as chaves de lá.
- Figuras: paleta de `src/eval/figuras.py`; textos em português, números com vírgula.

## Armadilhas técnicas conhecidas

| Armadilha | O que fazer |
|---|---|
| `pdfplumber.extract_words()` padrão já devolve as palavras pré-ordenadas geometricamente | Para a ordem real do arquivo: `use_text_flow=True` |
| BLEU em granularidade de bloco é quase insensível (página invertida = 82,7) | Nunca usar como métrica principal |
| "Fração de blocos fora da posição" sofre efeito cascata | Usar τ de Kendall e ARD; não citar o antigo "86% de desordem" |
| PowerShell: filtrar processos só por `CommandLine -like` casa com o próprio comando e mata o shell | Filtrar antes por `Name = 'python.exe'` |
| Nome de arquivo com `:` (ex.: `llava:7b`) cria fluxo alternativo NTFS no Windows | Sanear nomes de arquivo |
| Console do Windows mostra `ResoluÃ§Ã£o` | Os dados estão em UTF-8; use `sys.stdout.reconfigure(encoding="utf-8")` |
| Busca recursiva (`grep -r .`) no repositório passa de 2 minutos | Excluir `data/`, `venv/`, `models/`; ou buscar só em `src/` e `docs/` |
| PDFs de PE levam ~50 s cada no `pdfplumber` | Contar com isso ao re-extrair `blocos_extra` |
| `data/processed/blocos_extra/` ausente faz o treino ampliado rodar com **zero** páginas extras, sem erro | Conferir a contagem de páginas no log de treino (até a tarefa T01 criar a proteção) |
| O melhor checkpoint do LayoutLM sucessor precisa ser escolhido com a **mesma decodificação** do teste | Padrão atual: `--decodificacao cadeias` na validação e no teste |
| Porta 8770 é da ferramenta de anotação | Não subir outro servidor nela |
| O nome do anotador fica salvo no navegador e pode vir preenchido com o de outra pessoa | Conferir o campo Anotador antes de anotar |
| O segmentador tem três versões em jogo e os dados não batem com o código | Ler `docs/HANDOFF.md`, seção 2.2, antes de mexer em `extrator.py` ou em `data/processed/` |

## Validação

```bash
venv\Scripts\python.exe src\eval\metrics.py
venv\Scripts\python.exe src\data\reextrair.py --entrada data\processed\blocos --so-medir
venv\Scripts\python.exe -c "import ast,glob; [ast.parse(open(f,encoding='utf-8').read(),f) for f in glob.glob('src/**/*.py',recursive=True)]; print('ok')"
```

Mais comandos e o padrão para testar o segmentador numa página: `docs/HANDOFF.md`, seção 5.
