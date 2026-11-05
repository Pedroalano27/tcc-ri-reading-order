# Ferramenta de Anotação com Cronômetro e Log de Ações (E008)

Esta ferramenta foi desenvolvida para apoiar o **Experimento E008** do TCC (*Protocolo de Anotação Densa × Simplificada*, conforme documentado em [`docs/PLANO_PESQUISA.md`](../../../docs/PLANO_PESQUISA.md), Seção 2).

A ferramenta é uma evolução autônoma e autocontida do `classificador.html`, permitindo medir com precisão milimétrica:
1. **Tempo ativo humano por página** (com pausa automática após 60 s de inatividade e botão de pausa manual);
2. **Contagem e log temporal de todas as ações** (criação, exclusão, movimentação, redimensionamento, reclassificação, conexão de ordem, corte, fusão e desfazer);
3. **Dois modos de operação experimental** (*A — Densa* vs *B — Simplificada*);
4. **Apresentação pseudo-aleatória determinística** das páginas a partir de uma semente (seed) informada;
5. **Cobertura de palavras por unidade** (`palavras_cobertas`), viabilizando a verificação empírica da hipótese H9 ("anotação simplificada preserva 100% do conteúdo").

---

## 1. Como Abrir

- **Sem necessidade de servidor web ou Python rodando:** A ferramenta é 100% cliente (HTML5 + SVG + JavaScript puro).
- Basta abrir o arquivo `anotador.html` diretamente no seu navegador padrão (Google Chrome, Microsoft Edge, Firefox, Brave):
  ```text
  file:///C:/Users/pedro/dev/tcc-ri-reading-order/resultados/e008_anotacao/ferramenta/anotador.html
  ```
- Também pode ser aberto dando **duplo clique** sobre o arquivo no Windows Explorer.

---

## 2. Como Carregar as Tarefas e Imagens

1. **Tarefas de Entrada (`.jsonl` ou `.json`):**
   - Clique no botão **`📂 Abrir Tarefas`** no topo da tela.
   - Selecione o arquivo com o lote de páginas. Por exemplo:
     ```text
     data/diamond/lote_sem_paragrafos/tarefas.jsonl
     ```
   - O leitor detecta automaticamente arquivos JSON Lines (`.jsonl`), listas JSON padrão (`.json`) ou exports do Label Studio.
2. **Imagens da Página (`.jpg` ou `.png`):**
   - Clique no botão **`🖼️ Pasta Imagens`**.
   - Aponte para a pasta contendo os arquivos de imagem renderizados (por exemplo `resultados/lote_sem_paragrafos/img/`).
   - *Nota:* Caso abra as tarefas sem carregar a pasta de imagens, a ferramenta renderiza um fundo quadriculado com a geometria exata das caixas e os textos das palavras, permitindo operar mesmo sem as imagens em disco.

---

## 3. Os Dois Modos Experimentais

Ao iniciar a ferramenta (ou clicando no botão **`⚙️ Sessão`** no cabeçalho), o anotador escolhe o modo de operação:

| Aspecto | **Modo A — Densa** | **Modo B — Simplificada** |
|---|---|---|
| **Conceito** | Anotação editorial rica clássica de layout e parágrafos. | Anotação orientada a grafos sobre linhas automáticas e átomos. |
| **Unidades Iniciais** | Desenho do zero ou correção das caixas propostas/blocos v3. | As **linhas de texto automáticas** já vêm pré-carregadas como unidades. |
| **Classes Permitidas** | 10 classes completas:<br>1. Título<br>2. Texto<br>3. Lista<br>4. Assinatura<br>5. Tabela<br>6. Figura<br>7. Cabeçalho<br>8. Rodapé<br>9. Quadro<br>0. Outro | 5 classes essenciais:<br>1. Linha de Texto (`linha`)<br>2. Tabela (`tabela`)<br>3. Figura (`figura`)<br>4. Quadro (`quadro`)<br>5. Ruído / Pular (`skip_noise`) |
| **Foco da Ação Humana** | Desenhar limites de parágrafos, categorizar tipo textual e traçar ordem. | 1. Delimitar tabelas, figuras e quadros.<br>2. Marcar ruídos (cabeçalho/rodapé/lateral) com tecla `5` ou `N`.<br>3. Cortar (`S`) linhas que cruzaram calha.<br>4. Clicar a ordem entre linhas (`O`). |
| **Hipótese Associada** | Linha de base da anotação humana complexa. | **H6** (≥ 25% menos tempo), **H7** (menos erros de merge/split) e **H9** (100% palavras cobertas). |

---

## 4. Cronômetro Ativo e Log de Ações

Para garantir a validade científica das comparações de tempo (H6):

1. **Tempo Ativo (`tempo_ativo_s`):**
   - O cronômetro roda em milissegundos enquanto o anotador está interagindo com a página.
   - **Pausa Automática por Inatividade (60 segundos):** Se o usuário não mover o mouse nem pressionar teclas durante 60 segundos, o cronômetro entra em estado `Inativo (60s)` e para de acumular tempo. Ao primeiro toque subsequente, o cronômetro retoma automaticamente.
2. **Pausa Manual:**
   - O anotador pode pausar a qualquer momento pressionando o botão **`⏸️ Pausar`** (ou a tecla `P`).
   - Um overlay semitransparente escurece a página e impede alterações até que seja clicado **`▶️ Retomar Trabalho`**.
3. **Auditoria de Ações:**
   - Cada evento é registrado com seu carimbo relativo em milissegundos desde o início ativo da página:
     - `criar`: desenhar nova caixa;
     - `apagar`: excluir caixa(s) com Delete;
     - `mover`: deslocar caixa(s);
     - `redimensionar`: arrastar alça de dimensão;
     - `reclassificar`: alterar classe (teclas 1 a 9);
     - `ligar_ordem`: adicionar/remover elemento da sequência de leitura;
     - `dividir`: cortar caixa (tecla `S`);
     - `juntar`: unificar caixas (tecla `M`);
     - `desfazer`: reverter ação (Ctrl+Z);
     - `pular`: pular página com motivo.

---

## 5. Tabela de Atalhos de Teclado

| Tecla | Ação |
|---|---|
| `1` a `9` e `0` | Reclassifica a caixa selecionada imediatamente para a classe correspondente. |
| `N` | Marca a caixa selecionada como `skip_noise` (disponível no Modo B). |
| `O` | Ativa/Desativa o **Modo Ordem**: clique nas caixas sequencialmente para ligá-las. |
| `S` | Ativa o **Modo Dividir (Split)**: clique onde deseja fatiar a linha na horizontal. |
| `M` | Executa a **Fusão (Merge)** das caixas selecionadas (Shift+clique para selecionar mais de uma). |
| `Del` ou `Backspace` | Apaga a caixa selecionada. |
| `Ctrl+Z` | Desfaz a última ação (pilha com até 50 níveis). |
| `P` | Pausa ou retoma o cronômetro ativo. |
| `←` / `→` | Navega para a página anterior ou próxima do lote. |
| `Shift` + clique | Seleciona múltiplas caixas para juntar (`M`) ou apagar. |
| `Esc` | Limpa seleção de caixas e desativa modos especiais (Ordem / Dividir). |
| *Arrastar no vazio* | Desenha uma nova caixa retangular. |
| *Arrastar na alça* | Redimensiona a caixa nas 8 direções ortogonais/diagonais. |

---

## 6. Formato do JSON Exportado

A ferramenta gera três tipos de arquivo via botões dedicados:

### A. Exportação da Sessão Completa (`💾 Exportar Sessão (JSON)`)
Gera `anotacao_sessao_e008_<modo>_sem<semente>_<timestamp>.json`:
```json
{
  "versao_ferramenta": "E008-anotador-v1",
  "modo": "B — simplificada",
  "anotador": "Pedro",
  "semente": 20261102,
  "embaralhado": true,
  "data_inicio": "2026-11-02T21:00:00.000Z",
  "data_exportacao": "2026-11-02T21:35:12.450Z",
  "total_paginas": 60,
  "paginas_concluidas": 36,
  "tempo_total_ativo_s": 1285.4,
  "paginas": [
    {
      "page_id": "official_diary_am_manaus/2025-06-18_caderno_1.pdf#p29",
      "n": 1,
      "indice_sessao": 0,
      "indice_original": 0,
      "modo": "B — simplificada",
      "tempos": {
        "tempo_ativo_s": 38.6,
        "tempo_ativo_ms": 38612,
        "tempo_total_s": 45.2,
        "pausas_contagem": 0
      },
      "contagem_acoes": {
        "criar": 1,
        "apagar": 0,
        "mover": 0,
        "redimensionar": 1,
        "reclassificar": 2,
        "ligar_ordem": 42,
        "dividir": 1,
        "juntar": 0,
        "desfazer": 1,
        "pular": 0
      },
      "acoes": [
        {
          "tipo": "dividir",
          "t_ms": 4200,
          "detalhe": { "id_original": "p14", "novos_ids": ["cx_kh8_a", "cx_kh8_b"] }
        },
        {
          "tipo": "reclassificar",
          "t_ms": 8150,
          "detalhe": { "alteradas": [{ "id": "p3", "de": "figura", "para": "tabela" }] }
        },
        {
          "tipo": "ligar_ordem",
          "t_ms": 11200,
          "detalhe": { "caixa_id": "p1", "acao": "adicionar", "posicao": 1 }
        }
      ],
      "unidades": [
        {
          "id": "p1",
          "bbox": [311.8, 328.1, 538.7, 336.6],
          "classe": "linha",
          "texto": "por intermédio das Organizações",
          "palavras_cobertas": [214, 215, 216, 217]
        }
      ],
      "ordem": ["p1", "p2", "p4", "p6"],
      "motivo_pulo": null
    }
  ]
}
```

### B. Exportação da Página Atual (`📄 Exportar Página`)
Exporta exatamente o objeto de uma página individual encapsulado com os metadados da sessão, ideal para inspeções rápidas e salvamentos pontuais.

### C. Exportação Compatível com Label Studio (`🏷️ Label Studio`)
Gera arquivo compatível com o formato de importação/exportação corporativo do Label Studio:
- Retângulos em porcentagem (`type: rectanglelabels`);
- Transcrições textuais (`type: textarea`);
- Ordem de leitura como grafo de relações em cadeia (`type: relation`, com `labels: ["continue"]`).

---

## 7. Roteiro de 5 Minutos para Teste Prático (2 Páginas)

Para validar a ferramenta antes de iniciar a campanha completa do E008, siga estes passos:

### Passo 1: Abrir e Configurar a Sessão (1 min)
1. Dê duplo clique no arquivo `anotador.html` para abri-lo no navegador.
2. Na tela de boas-vindas (*Configurar Sessão Experimental*):
   - Escolha o modo: **`B — Simplificada`**;
   - Nome do anotador: `Pedro`;
   - Semente: `20261102`;
   - Deixe marcado `Embaralhar ordem das páginas com esta semente`;
   - Clique em **`▶️ Salvar e Iniciar Sessão`**.

### Passo 2: Carregar as Tarefas (30 s)
1. Clique em **`📂 Abrir Tarefas`** e selecione `data/diamond/lote_sem_paragrafos/tarefas.jsonl`.
2. A barra lateral esquerda será imediatamente preenchida com as 60 páginas do lote, ordenadas pela semente.
3. Observe que o cronômetro superior começou a rodar (`⏱️ 00:01`, `00:02`...).

### Passo 3: Testar Ações na Página 1 (2 min)
1. **Marcar Ruído:** Clique numa linha de cabeçalho ou rodapé e aperte `5` (ou `N`). Observe que ela ganha textura tracejada e sua classe muda para `skip_noise`.
2. **Dividir Linha:** Selecione uma linha qualquer, aperte `S` (Modo Dividir) e clique no meio da caixa. A linha é fatiada em duas metades com IDs derivados e palavras recalculadas.
3. **Pausar Cronômetro:** Pressione `P` ou clique no botão **`⏸️ Pausar`**. A tela escurece e o timer congela. Clique em **`▶️ Retomar Trabalho`** para continuar.
4. **Definir Ordem de Leitura:** Aperte `O` (Modo Ordem). Clique em 5 caixas na ordem desejada. Note as setas azuis com setas direcionadas e os círculos numerados `1`, `2`, `3`, `4`, `5`.
5. **Inspecionar Contadores:** No painel lateral direito, observe o quadro *Ações na Página (E008)* contabilizando cada operação realizada em tempo real.

### Passo 4: Avançar para a Página 2 e Testar Pular (1 min)
1. Clique em **`Próxima →`** (ou aperte a seta direita `→` no teclado).
2. O cronômetro da página 1 é pausado, gravando seu tempo ativo final, e a página 2 inicia do `00:00`.
3. Clique em **`⏭️ Pular`**, digite `Página de teste de pulo` e confirme. A página é marcada como `Pulada` e a ferramenta avança automaticamente.

### Passo 5: Exportar e Verificar os Resultados (30 s)
1. Clique no botão verde **`💾 Exportar Sessão (JSON)`**.
2. Abra o arquivo baixado no seu editor de texto ou VS Code:
   - Verifique que o campo `"modo"` é `"B — simplificada"`;
   - Verifique que `"semente"` é `20261102`;
   - Verifique que cada página contém `"tempo_ativo_s"`, a contagem de `"acoes"`, as `"unidades"` com suas coordenadas e a lista de `"palavras_cobertas"`.
3. Tudo pronto para o experimento E008!
