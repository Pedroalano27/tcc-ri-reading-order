# Handoff: como orquestrar Codex, Antigravity, Gemini e GPU a partir de um chat do Claude

Escrito pelo Claude em 03/10/2026, depois da noite de 02→03/10 (resultados em
[`RELATORIO_NOITE_0210.md`](RELATORIO_NOITE_0210.md)). Serve para outro chat repetir o método neste repositório
ou em outro. Tudo o que está aqui foi usado de verdade; os scripts citados existem em
[`orquestracao/noite_0210/`](../orquestracao/noite_0210/).

---

## 1. A ideia em cinco linhas

1. O Claude **não executa o trabalho pesado**: escreve tarefas em arquivos de texto, e filas em `bash` as
   entregam a outros agentes, um de cada vez por agente.
2. As filas rodam **soltas da sessão** do Claude: se o chat cair ou o limite acabar, o trabalho continua.
3. O Claude acorda de tempos em tempos (25 a 45 min), lê um **painel compacto**, lê o veredito do que terminou,
   **decide o rumo** e enfileira a próxima tarefa.
4. Nenhum resultado é aceito sem revisão: outro agente revisa, ou o Claude reexecuta, ou o número é marcado
   como "não revisado".
5. Tudo é **retomável** com um comando, porque esta máquina cai.

## 2. Quem faz o quê

| Recurso | Bom para | Limite na prática | Como é chamado |
|---|---|---|---|
| **Claude (este chat)** | decidir, escrever tarefas, revisar, integrar, relatório | tokens do chat | — |
| **Codex CLI** (`gpt-6.1-sol`, esforço `xhigh`) | experimento técnico de ponta a ponta: escreve, roda, confere e relata | 27 a 47 min por tarefa; o limite de uso bateu depois de 5 tarefas completas e uma parcial (3h40) e voltou 1h20 depois | `codex exec` |
| **Antigravity CLI** (`gemini-3.8-flash-high`) | análise bem especificada, revisão de código, galerias | 3 a 9 min por tarefa; sem interface ele **não roda comandos nem acessa a web** | `agy -p=...` |
| **API do Gemini** | trabalho em lote por página (ordenar, anotar) | cota diária (acabou em ~273 chamadas; renova às 04:00 de Brasília); erros 503 | scripts do projeto (`src/eval/vlm_ordem.py`, `src/data/gerar_rose.py`), chave no `.env` |
| **GPU local** (RTX 4050, 6 GB) | um treino por vez | memória RAM, não a placa (seção 8) | script `bash` próprio |
| **Kaggle** (2× T4) | modelos maiores, 10 a 12 h | depende do Pedro subir e rodar | notebook + zip em `dist/kaggle/` |

## 3. Os comandos exatos

```bash
# Codex: o prompt entra pela entrada padrão ("-"); a resposta final vai para o arquivo de -o
{ cat comum.txt; echo; grep -v '^#' tarefa.txt; } | codex exec -m gpt-6.1-sol \
    -c 'model_reasoning_effort="xhigh"' -s workspace-write -o tarefa.out.md - > tarefa.log 2>&1
```

```bash
# Antigravity: o -p tem de vir colado ao prompt com "="; < /dev/null evita que ele espere o teclado
agy --model gemini-3.8-flash-high --mode accept-edits --print-timeout 1500s -p="$PROMPT" < /dev/null > tarefa.agy.log 2>&1
```

- **Codex** roda numa caixa de areia: escreve só dentro do repositório, não tem rede, não instala pacote, não
  enxerga processos. O que ele precisar (pacote, modelo) o Claude instala ou baixa antes e avisa no prompt.
- **Antigravity** em modo sem interface nega qualquer ferramenta de comando. O padrão que funciona: ele
  **escreve o script**, a fila **executa** e, se falhar, devolve as últimas 45 linhas do erro para ele corrigir,
  até 5 rodadas. Das 10 tarefas que ele concluiu na noite, 9 passaram na 1ª rodada e 1 na 2ª.
- Não use `--dangerously-skip-permissions`.

## 4. A fila ([`fila.sh`](../orquestracao/noite_0210/fila.sh))

Uma pasta por agente (`codex/`, `agy/`), um arquivo por tarefa: `NN_nome.txt`. As primeiras linhas podem trazer
cabeçalhos, que não vão para o agente:

```text
#ESPERA: runs/detect/ls3/treino_ok        (só roda quando esse arquivo existir; pode repetir a linha)
#SCRIPT: orquestracao/analises/x.py       (Antigravity: o script que ele escreve e a fila executa)
#SAIDA:  resultados/x.md                  (arquivo que tem de existir no fim)
TAREFA: ...
```

Regras da fila, todas aprendidas com erro:

- **Menor número pronto primeiro, uma tarefa por varredura.** Depois de cada tarefa a fila volta ao início da
  lista, então dá para mudar a prioridade só renomeando arquivos (`01b_`, `09b_`) e tarefas novas entram sozinhas.
- **`#ESPERA` não bloqueia.** Na primeira versão a fila parava na tarefa 02 esperando um treino e nunca chegava às outras.
- **Falha rápida não queima a fila.** Se o agente cai em menos de 2 minutos (limite de uso, rede, login), a
  fila registra, espera 20 minutos e tenta de novo, sem marcar a tarefa como falha. Falha lenta: 2 tentativas.
- Marcadores ao lado da tarefa: `.rodando`, `.done`, `.falhou`, `.out.md` (resposta final), `.tN.log`.
- Todo prompt recebe na frente o [`comum.txt`](../orquestracao/noite_0210/comum.txt): regras fixas (só arquivos
  novos, nada em `data/`, não editar o quadro, sem commit, sem GPU, sem rede, formato dos dados).
- Depois de cada tarefa a fila confere se algo sob `data/` mudou e grita `ALERTA` no log.
- A fila segura a máquina acordada (`SetThreadExecutionState`) e para se existir o arquivo `STOP`.

## 5. Lançar, acompanhar, retomar, parar

- **Lançar e retomar:** [`iniciar.ps1`](../orquestracao/noite_0210/iniciar.ps1) (ou `bash .../iniciar.sh`). Sobe
  cada componente com `Start-Process` oculto e **não duplica** o que já está rodando. Depois de uma queda, é só rodar de novo.
- **Por que não usar tarefa de fundo do chat:** ela é cortada em 10 a 30 minutos, e nesta máquina o corte mata só
  o shell de cima — os filhos continuam vivos e sem dono.
- **Acompanhar:** [`status.sh`](../orquestracao/noite_0210/status.sh) imprime GPU, treino, estado de cada tarefa,
  últimas linhas do `fila.log`, processos vivos e RAM livre em ~25 linhas. É o que o Claude lê a cada volta.
- **Parar um componente:** achar o `bash.exe` pela linha de comando e dar `taskkill /PID <raiz> /T /F`; conferir de
  novo os processos e a GPU um minuto depois. Nunca editar um `.sh` enquanto ele roda.

## 6. O laço do orquestrador

Depois de lançar, o Claude entra em `/loop` sem intervalo (modo dinâmico) e agenda o próprio despertar com
`ScheduleWakeup`. Em cada volta:

1. `status.sh` e memória (RAM livre e memória comprometida).
2. Ler **só** o que terminou: a resposta final do agente (`.out.md`, 15 a 30 linhas) e o resumo do relatório.
3. Decidir: aceitar, mandar revisar, refazer com outra pergunta, reordenar a fila, parar um job inútil.
4. Enfileirar tarefas novas (arquivo novo na pasta) e, se couber, usar a GPU ociosa.
5. Atualizar o relatório consolidado e dizer ao usuário, em texto, o que mudou.
6. Agendar a próxima volta para pouco depois do próximo evento esperado. Sem monitor de eventos: custa menos.

O relatório consolidado deve nascer **cedo** e ser atualizado, não escrito só no fim: se a sessão cair, ele já existe.

## 7. Como escrever uma tarefa que volta boa

Molde que funcionou (veja `orquestracao/noite_0210/codex/*.txt`):

1. **A pergunta, com o motivo** — o que o autor quer saber e por quê; números já conhecidos.
2. **Dados, com caminhos e formato** — e a ordem de conferir (índice de página, escala, coordenadas) antes de confiar.
3. **"Faça em `caminho/arquivo.py`"**, importando o que já existe e sem editar nada existente.
4. **Itens numerados** do que medir, com as réguas e a estatística pedidas (IC, teste pareado, estratos).
5. **Proteções:** nada escolhido olhando a página avaliada; declarar vieses; cache retomável em `resultados/`.
6. **Fecho:** "rode do zero e confira que o relatório bate com a saída"; resumo de 5 linhas com veredito; resposta
   final curta (veredito, tabela principal, caminhos).

Encadear tarefas: `#ESPERA` no artefato da anterior e uma nota "se `resultados/X.md` existir, leia e não repita".
Quando uma revisão muda as regras do jogo, acrescente um adendo a todas as tarefas pendentes
([`adendo_frente_b.txt`](../orquestracao/noite_0210/adendo_frente_b.txt)).

## 8. Revisar antes de acreditar

- **Revisão adversarial:** uma tarefa cujo papel é derrubar o resultado de outro agente, lendo o código. Foi ela que
  mostrou que 90% de um "ganho" vinha de uma regra dada a um lado só da comparação.
- **Reanálise justa:** depois da crítica, uma tarefa de árbitro que verifica com código cada ponto.
- **Erros que a revisão pegou nesta noite:** concordância entre anotadores inflada por incluir um projeto em que a
  segunda anotação é cópia da primeira; "PyMuPDF pode substituir com segurança" quando 43 de 104 páginas mudam blocos.
- **Erro que só o usuário pegou:** o orquestrador respondeu à pergunta errada duas vezes (comparou com um
  oráculo humano quando a pergunta era automático contra automático; testou o detector dentro do extrator antigo
  quando o pedido era o extrator novo a partir do dataset). **Antes de enfileirar, escreva a pergunta do usuário
  com as palavras dele e confira se a tarefa responde a ela.**
- No relatório, separar sempre: o que o Claude executou, o que só leu, o que ninguém revisou.

## 9. Armadilhas desta máquina

| Armadilha | O que fazer |
|---|---|
| Treino YOLO com `--workers 4` abre 12 processos de ~1 GB (a validação usa o dobro): 20 GB comprometidos em 16 GB de RAM | `--workers 1`; conferir a memória 3 minutos depois de subir um treino |
| O `C:` é um SSD externo USB; a máquina tem dezenas de desligamentos inesperados | tudo retomável; relatório cedo; lembrar o Pedro de commit e push |
| Arquivo criado minutos antes de uma queda some na primeira listagem da pasta | depois de uma queda, conferir integridade antes de retomar |
| Uso da GPU fica em 25 a 50% só com a tela ligada | decidir "GPU livre" pela memória (< 1,1 GB), não pela porcentagem |
| Heredoc com aspas quebra o comando do chat | gravar tarefas com a ferramenta de escrita, uma por arquivo |
| A fila tenta de novo 2 minutos antes de o limite do Codex voltar e dorme 20 minutos | matar o `sleep.exe` de 1200 s; a fila segue na hora |
| `wmic` não existe mais | contar processos com `Get-CimInstance Win32_Process`, filtrando primeiro por `Name` |
| Job que repete páginas que sempre falham (massa do Gemini) | parar e deixar um marcador para a retomada não relançar |

## 10. Regras do projeto que continuam valendo

Estão em [`AGENTS.md`](../AGENTS.md): reservar no quadro antes, registrar depois; agentes despachados não editam
o quadro; nunca tocar em anotação humana nem em `data/raw/`; um job de GPU por vez; sem commit, push ou publicação
sem o Pedro pedir; todo número vem de um arquivo. Dado do projeto Data Policy (`data/labelstudio/` e derivados) não
se publica e não vai para a API do Gemini; os derivados gerados pelas análises estão no `.gitignore`.

## 11. Texto para colar no outro chat

```text
Leia docs/HANDOFF_ORQUESTRACAO.md, AGENTS.md e as entradas mais recentes de COMUNICACAO_AGENTES.md.
Quero que você orquestre <OBJETIVO> usando o Codex CLI (gpt-6.1-sol, xhigh), o Antigravity CLI
(gemini-3.8-flash-high) e a GPU local, do jeito descrito no handoff:
- crie uma pasta orquestracao/<nome>/ copiando fila.sh, comum.txt, iniciar.ps1, iniciar.sh e status.sh de
  orquestracao/noite_0210/ e ajuste os caminhos;
- antes de enfileirar, escreva em uma frase a pergunta que cada tarefa responde e confirme comigo;
- escreva as tarefas no molde da seção 7, com #ESPERA, #SCRIPT e #SAIDA;
- suba tudo com iniciar.ps1, entre em /loop e acorde a cada 30 a 45 minutos;
- coloque um revisor adversarial em todo resultado que for virar número do TCC;
- treinos com --workers 1; confira a memória depois de subir;
- relatório consolidado em docs/ desde o primeiro resultado; quadro atualizado no fim;
- não faça commit nem push, e não mande dados de data/labelstudio para fora.
```

## 12. Lista de conferência

**Antes de subir:** GPU livre? CLIs respondem (`codex --version`, `agy --version`)? pacotes e modelos que os agentes
precisam já instalados? reserva no quadro? pergunta de cada tarefa conferida com o usuário?

**No fim:** painel sem tarefa rodando; relatório com fontes e com "não revisado" onde couber; entrada no quadro;
reservas removidas; decisões do usuário listadas; nada commitado sem pedido.
