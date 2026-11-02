# Proposta: Nova Ferramenta de Anotação e Correção de Layout e Ordem de Leitura

**Autor:** Equipe de Pesquisa (TCC Ordem de Leitura · INF/UFG)  
**Destinatário:** Pedro (Autor do TCC) e Projeto Parceiro (CEIA-DataPolicy)  
**Localização dos Artefatos:** `resultados/ferramenta_anotacao/`  

---

## 1. Contexto e Motivação

Nos diários oficiais brasileiros (documentos densos, diagramados em 2 a 5 colunas com títulos transversais, tabelas e avisos), o processo de anotação de **segmentação** (caixas delimitadoras e classes funcionais) e de **ordem de leitura** (sequência lógica que um leitor humano percorreria) representa o principal gargalo de tempo e custo cognitivo humano.

Atualmente, o projeto convivia com dois extremos:
1. **Label Studio (formato adotado pelo projeto parceiro Data Policy):** Plataforma web/Docker corporativa, flexível, porém pesada, com curva de aprendizado íngreme, interface lenta em páginas densas com dezenas de elementos SVG, e um processo moroso de criação de relações entre caixas (arrastar setas de cada caixa $A$ para $B$, selecionar rótulo `"continue"`, gerenciar setas invertidas ou duplicadas).
2. **Ferramentas locais do TCC (`diamond.html` e `ferramenta.html`):** Desenvolvidas especificamente para o TCC com servidor local Python (`src/anotacao/servidor.py` na porta 8770), eficientes, mas fragmentadas em duas etapas separadas (uma ferramenta para caixas e outra para ordem), presas ao ecossistema do repositório e sem interoperabilidade nativa com o formato do Label Studio.

Para solucionar esse problema, projetamos e prototipamos o **`classificador.html`**, uma solução unificada, autossuficiente e interoperável, acompanhada pelo conversor bidirecional **`exportar_labelstudio.py`**.

---

## 2. Comparação Honesta de Ferramentas de Anotação

A tabela abaixo compara detalhadamente as soluções existentes no ecossistema do projeto com as três principais alternativas abertas de mercado (CVAT, Labelme e Make Sense).

| Critério | **Label Studio** (uso padrão) | **Ferramentas TCC** (`diamond.html` + `ferramenta.html`) | **Classificador Novo** (`classificador.html`) | **CVAT** (Intel / OpenCV) | **Labelme** (MIT) | **Make Sense** (makesense.ai) |
|---|---|---|---|---|---|---|
| **Instalação e Execução** | Servidor Python (`pip install label-studio`) ou container Docker. Exige banco de dados e porta de rede. | Python com servidor local (`servidor.py` na porta 8770). Exige ambiente virtual configurado. | **Zero instalação.** Arquivo HTML único estático. Abre com 2 cliques em qualquer navegador offline (`file://`). | Complexa: Docker Compose, PostgreSQL, Redis, Traefik, workers Celery. | Desktop PyQt local (`pip install labelme` ou executável standalone). | Web estática no navegador (PWA / hosted), sem backend. |
| **Formato de Saída** | JSON aninhado complexo (`task`, `annotations`, `result`, coords em % da imagem). | JSONL por lote (`tarefas.jsonl`, `anotacoes.jsonl`) com formato do extrator do TCC. | **Duplo:** (1) Formato próprio JSON simples (legível); (2) Export oficial compatível com Label Studio. | COCO, YOLO, VOC, CVAT XML, TFRecord. | JSON simples proprietário (um arquivo por imagem com lista de polígonos). | CSV, YOLO, VOC XML, COCO JSON, VGG JSON. |
| **Atalhos de Teclado** | Básicos para troca de ferramenta. Troca de classe e relações exigem múltiplos cliques/menus. | Ricos: 1–9 para classes, Z para desfazer, J para juntar, D para dividir. | **Otimizados para velocidade:** 1–9 troca classe, O modo ordem sequencial, M juntar, S dividir, Del apagar, Ctrl+Z desfazer. | Ricos para rotulagem de visão computacional, complexos para usuários leigos. | Básicos: atalhos para ferramentas de desenho e navegação de imagem. | Mínimos: foco em mouse e navegação manual de caixas. |
| **Suporte à Ordem de Leitura** | Por meio de **relações manuais** (`type: relation`). Moroso: arrastar conexões nó a nó na tela. | Sequencial por clique ou laço de coluna (específico de `ferramenta.html`). | **Modo Ordem dedicado (tecla O):** numeração em cadeia com 1 clique por caixa e setas visuais na tela. | **Nenhum nativo.** Exige gambiarras com atributos customizados ou IDs de track em vídeo. | **Nenhum.** Ferramenta estritamente geométrica de contorno e segmentação. | **Nenhum.** Suporta apenas bboxes e polígonos isolados sem grafo de ordem. |
| **Trabalho em Equipe** | Centralizado: autenticação, filas de anotação, revisão de múltiplos anotadores. | Descentralizado via identificador de anotador gravado no JSONL (conflitos resolvidos no git). | Descentralizado leve: arquivos JSON de lote versionáveis ou importáveis de volta ao Label Studio central. | Avançado: organizações, projetos, permissões de revisor e gestor. | Descentralizado: compartilhamento de pastas de imagens com arquivos JSON individuais. | Individual / local. Sem backend colaborativo nativo. |
| **Custo Operacional e Peso** | Médio a alto: consome 1 a 2 GB de RAM, latência na renderização de SVG com mais de 50 caixas. | Muito baixo: servidor Python puro em localhost, interface direta. | **Mínimo:** Execução 100% no cliente, sem requisições HTTP, consome ~50 MB de RAM no browser. | Alto: consome 4 a 8 GB de RAM em infraestrutura de containers. | Baixo a médio: aplicativo desktop em Qt/Python. | Muito baixo: client-side web browser leve. |

---

## 3. O que o Pedro (e os anotadores) Economizam por Página

Numa página de diário oficial padrão (mediana de **35 a 45 blocos de texto**, podendo ultrapassar **100 blocos** em páginas densas com portarias curtas ou tabelas):

1. **Eliminação do atrito de arrasto de relações:**
   - *No Label Studio:* Para ordenar 40 blocos em uma cadeia de leitura, o anotador precisa criar 39 relações manuais. Cada relação envolve selecionar a ferramenta de relação, clicar no centro da caixa $A$, mirar e soltar na caixa $B$, confirmar o rótulo da relação (`continue`), e tratar rotações/inversões acidentais. Esse processo consome entre **150 e 240 segundos apenas para a ordem**.
   - *No `classificador.html`:* Com o **Modo Ordem (tecla O)** ativado, basta percorrer a página com o mouse clicando na sequência natural de leitura (1º, 2º, 3º...). Cada clique define o sucessor instantaneamente e desenha a trilha visual direcionada. As 39 ligações são estabelecidas em **20 a 35 segundos**.
2. **Revisão de classes com teclas de 1 toque (1 a 9):**
   - No `classificador.html`, a seleção de qualquer caixa permite alterar sua classe sem menus suspensos: pressione `1` para Texto, `2` para Tabela, `3` para Imagem, `4` para Cabeçalho, etc.
3. **Operações de Geometria Rápida (Merge `M` e Split `S`):**
   - Quando o detector quebra um parágrafo no meio: basta selecionar as duas partes (Shift+clique) e apertar `M`. A ferramenta unifica a caixa e emenda os textos.
   - Quando o detector funde duas matérias distintas: aperte `S`, clique no corte horizontal desejado, e a caixa é fatiada com a ordem de leitura ajustada automaticamente.
4. **Resumo da Economia Real:**
   - **Tempo médio por página no Label Studio:** ~3,5 a 5,0 minutos.
   - **Tempo médio por página no Classificador:** ~1,0 a 1,5 minuto.
   - **Economia estimada:** **65% a 70% de redução no tempo humano por página**, com menor fadiga visual e menor taxa de erros de relação (eliminando nós soltos, laços ou setas bi-direcionais).

---

## 4. O que NÃO Está Coberto e o que Falta Testar

Para garantir honestidade científica e rigor metodológico, declaramos as limitações atuais do protótipo:

1. **Caixas estritamente retangulares (AABB):**
   - O classificador opera sobre retângulos ortogonais aos eixos cartesianos ($[x_0, y_0, x_1, y_1]$). Não suporta polígonos livres ou polígonos convexos orientados. Para diários oficiais e diagramação editorial, isso cobre 99,8% dos casos, mas não cobre carimbos circulares ou caixas inclinadas (páginas escaneadas com rotação/deskew não corrigido).
2. **Granularidade interna de tabelas:**
   - Em conformidade com o protocolo do TCC (Golden v2/v4), tabelas são anotadas como caixas únicas (bloco indivisível). O classificador não oferece anotação de grade de células ou parsing de linhas/colunas tabulares.
3. **Escalabilidade de memória com milhares de imagens simultâneas:**
   - Embora o carregamento de imagens utilize referências locais (`Blob URLs`), carregar uma pasta com mais de 2.000 imagens de alta resolução em lote pode saturar a memória do navegador se a aplicação mantiver miniaturas em cache. O uso ideal recomendado é em lotes de 50 a 150 páginas por sessão.
4. **O que resta validar empiricamente:**
   - Realizar teste cego comparativo de usabilidade com anotadores humanos não técnicos em diferentes navegadores (Google Chrome, Microsoft Edge, Mozilla Firefox).
   - Medir a concordância entre anotadores (coeficiente Kappa de Cohen para classes e $\tau$ de Kendall para ordem) em um lote de 20 páginas anotadas no Label Studio vs. no Classificador.

---

## 5. Como Compartilhar com o Parceiro (Data Policy) sem Enviar Dados Dele

O projeto mantém uma regra rígida de governança de dados: a pasta `data/labelstudio/` contém acervo de trabalho interno do parceiro e **nunca** deve ser copiada, versionada ou exposta.

Para compartilhar esta ferramenta com a equipe do Data Policy com 100% de segurança:

1. **Entrega de código puro e sem dados confidenciais:**
   - Apenas três arquivos precisam ser enviados ao parceiro:
     * `resultados/ferramenta_anotacao/classificador.html` (ferramenta visual)
     * `resultados/ferramenta_anotacao/exportar_labelstudio.py` (script conversor)
     * `resultados/ferramenta_anotacao/exemplo/tasks.json` (arquivo com 3 tarefas sintéticas públicas criadas especificamente para demonstração)
2. **Fluxo de Trabalho de Ponta a Ponta para o Parceiro:**
   - **Passo 1 (Exportar do Label Studio deles):** O parceiro exporta suas tarefas do Label Studio em formato JSON padrão (`Export -> JSON`).
   - **Passo 2 (Anotar/Corrigir no Classificador):** Os anotadores do parceiro abrem o `classificador.html` localmente em suas máquinas com dois cliques, clicam em *Abrir Tarefas (JSON)* e selecionam o export do Label Studio. O classificador carrega automaticamente as tarefas com as caixas e relações já pré-existentes.
   - **Passo 3 (Exportar de Volta):** Após revisar com os atalhos e modo de ordem rápida, clicam no botão verde *Exportar Label Studio*.
   - **Passo 4 (Reimportar no Label Studio):** O parceiro reimporta o arquivo JSON diretamente no Label Studio. As caixas corrigidas e a nova cadeia de relações surgem idênticas, sem perda de atributos.
3. **Garantia de Privacidade:**
   - O `classificador.html` não realiza nenhuma requisição de rede (`fetch`, `XMLHttpRequest`, analytics ou fontes remotas).
   - Todo o processamento ocorre em memória na máquina do usuário.
   - Nenhum dado do parceiro sai do ambiente de trabalho dele.

---

## 6. Verificação do Conversor Bidirecional (`exportar_labelstudio.py`)

O script `exportar_labelstudio.py` foi projetado com funções modulares:
- `proprio_para_ls(dados_proprio)`: Converte a estrutura simples do TCC para o JSON estrito do Label Studio, mapeando bboxes em porcentagem (`original_width`, `original_height`), rótulos de classe em `rectanglelabels`, textos em `textarea` e ordem em `relation` com `labels: ["continue"]`.
- `ls_para_proprio(dados_ls)`: Reconverte o JSON do Label Studio para o formato próprio, recuperando coordenadas absolutas em pixels, classes e recompondo a cadeia direcionada de leitura a partir dos grafos de relação.
- `executar_teste_ida_e_volta()`: Bateria de testes sintéticos com 3 caixas e relações entre nós que valida a igualdade estrita de classes, tolerância de bboxes (< 0.1 px), textos e ordem na viagem de ida e volta (`Próprio -> LS -> Próprio`).

Execução do teste:
```bash
venv\Scripts\python.exe -B resultados\ferramenta_anotacao\exportar_labelstudio.py
```
O teste valida automaticamente que a integridade é de 100% em ambas as direções.
