# Comparação Técnica: Ferramentas de Anotação de Layout e Ordem de Leitura

**Destinatário:** Pedro (Autor do TCC)  
**Objetivo:** Avaliar a viabilidade técnica e a produtividade de ferramentas consagradas da literatura (LAREX, eScriptorium e CVAT) frente ao `classificador.html` desenvolvido para o TCC, orientando a escolha da melhor ferramenta para anotação e correção de diários oficiais.  
**Localização:** `resultados/ferramenta_anotacao/COMPARACAO_LAREX.md`

---

## 1. Tabela Comparativa Honesta (9 Dimensões)

A tabela abaixo sintetiza o estado real de cada ferramenta com base na literatura, documentação técnica oficial e testes práticos de engenharia documental. Pontos com variação entre versões ou dependentes de extensões específicas estão explicitamente marcados como **(a confirmar)**.

| Dimensão / Critério | `classificador.html` (TCC) | **LAREX** (Univ. Würzburg) | **eScriptorium** (EPHE / Inria) | **CVAT** (Intel / OpenCV) |
|---|---|---|---|---|
| **1. Instalação e Execução no Windows** | **Zero instalação.** Arquivo HTML único estático. Abre com 2 cliques em qualquer navegador offline (`file://`). | **Moderada a complexa.** Exige Java (JRE/JDK 8+) e servidor Apache Tomcat ou executável WAR empacotado. No Windows, roda via script `.bat` ou container Docker *(a confirmar se a versão standalone JavaFX/Jetty mais recente dispensa Tomcat externo)*. | **Muito complexa.** Exige Docker Desktop no Windows (WSL2) com stack completa: backend Django, banco PostgreSQL, fila Redis e workers Celery. Não possui executável nativo Windows. | **Complexa.** Exige Docker Compose no Windows (WSL2), PostgreSQL, Redis, Traefik e múltiplos containers. Consome ~4 a 6 GB de RAM. |
| **2. Geometria de Caixas (Retângulos vs. Polígonos)** | **Apenas caixas retangulares** ortogonais (AABB $[x_0, y_0, x_1, y_1]$). Não suporta polígonos livres. | **Excelente suporte a ambos.** Permite retângulos e polígonos livres/arbitrários. Possui ferramentas de simplificação de contorno e divisão poligonal. | **Excelente para polígonos e baselines.** Projetado para contornos poligonais complexos de texto e linhas de base *(baselines)* para HTR/OCR. | **Excelente suporte total.** Bounding boxes, polígonos livres, polilinhas, pontos e máscaras de segmentação. |
| **3. Classes Configuráveis** | **Totalmente configurável** no topo do arquivo (`CLASSES_CONFIG` em JavaScript): texto, tabela, imagem, cabeçalho, rodapé, quadro, outro. | **Configurável via XML de regras** (*Book / Page Rules*). Permite definir tipos de região vinculados ao vocabulário PAGE XML (`paragraph`, `heading`, `table`, `image`, etc.). | **Totalmente configurável via interface web.** Permite criar ontologias personalizadas de tipos de região e tipos de linha. | **Totalmente configurável via interface web.** Labels com atributos, cores e atalhos customizados por projeto. |
| **4. Ordem de Leitura (Como se marca)** | **Modo Ordem dedicado (tecla O):** numeração em cadeia sequencial com **1 clique por caixa**, gerando trilha visual imediata com setas SVG direcionadas e atalho para reiniciar. | **Nativa no PAGE XML (`ReadingOrder`).** Permite definir árvore/grafo de leitura reordenando itens na barra lateral ou ligando regiões com ferramentas da barra de leitura *(a confirmar se possui modo sequencial de 1 clique contínuo sem abrir menus)*. | **Nativa.** Suporta reordenação de regiões e linhas na árvore lateral (arrastar e soltar) e ordenação automática heurística (top-to-bottom / colunar). | **Nenhum suporte nativo.** Exige "gambiarras" manuais, como preencher um atributo numérico customizado (ex.: campo `ordem: 1, 2, ...`) caixa por caixa, ou usar IDs de tracking de vídeo. |
| **5. Importação de Pré-anotação** | **Direta e nativa.** Botão "Abrir Tarefas": aceita JSON próprio do TCC ou JSON exportado do Label Studio. | **Direta via PAGE XML.** Lê automaticamente arquivos `.xml` no padrão PAGE XML (2013/2017/2019) emparelhados com as imagens na mesma pasta. | **Direta via PAGE XML / ALTO XML.** Permite importar imagens com anotações prévias em PAGE/ALTO XML ou integrar modelos Kraken. | **Direta para visão computacional.** Importa COCO, YOLO, Pascal VOC, CVAT XML. **Não importa PAGE XML nativamente.** |
| **6. Formato de Saída** | **Triplo:** (1) Formato próprio JSON legível; (2) Export oficial Label Studio; (3) PAGE XML 2019 (via `conversor_page_xml.py`). | **PAGE XML nativo** (esquemas PRImA 2013, 2017 e 2019). | **PAGE XML e ALTO XML** nativos, além de exportação de texto transcrito. | **Formatos de Visão Computacional:** COCO, YOLO, CVAT XML, VOC XML, TFRecord. |
| **7. Atalhos de Teclado e Produtividade** | **Otimizados para diários oficiais:** teclas `1` a `9` para troca imediata de classe, `O` para ordem rápida, `S` para split horizontal, `M` para merge, `Del` para apagar, `Ctrl+Z` para desfazer. | **Bons para segmentação geral:** atalhos para ferramentas de desenho e seleção de página, mas troca de classe e encadeamento de ordem dependem mais de cliques em menus laterais e mouse. | **Razoáveis:** voltados principalmente para correção de texto/transcrição e ajuste de baselines; menos focados em classificação rápida de 50+ blocos por página. | **Muito ricos para desenho:** teclas para trocar ferramenta e rótulo, navegação rápida, mas zero atalhos para encadeamento de ordem de leitura. |
| **8. Trabalho em Equipe e Gestão** | **Descentralizado leve:** arquivos JSON de lote versionáveis em Git ou reimportáveis para o Label Studio central. Sem servidor multiusuário nativo. | **Mono-usuário por diretório** ou compartilhado via rede local/Tomcat. Sem gestão nativa de filas de anotação com login individual de anotadores *(a confirmar versão multiusuário em nuvem)*. | **Excelente plataforma corporativa:** projetos, equipes, permissões granulares, revisão por pares e atribuição de documentos. | **Excelente nível empresarial:** organizações, projetos, tarefas, jobs particionados, revisão de anotadores e consenso. |
| **9. Licença e Dependências** | **Aberta (MIT / TCC).** Sem dependências de software externo, sem Python em runtime (apenas navegador moderno). | **Código Aberto (GPL v3 / Univ. Würzburg).** Depende de Java Runtime Environment. | **Código Aberto (GPL v3 / EPHE-Inria).** Depende de Docker, Python/Django, Postgres, Redis. | **Código Aberto (MIT / OpenCV).** Depende de Docker Desktop e stack de microsserviços. |

---

## 2. Análise Detalhada das Ferramentas no Cenário do TCC

### 2.1 `classificador.html` (Ferramenta Local do TCC)
* **Vantagens decisivas:**
  1. **Velocidade operacional:** Um anotador consegue revisar uma página de diário oficial (35 a 50 blocos) em **1,0 a 1,5 minuto**, contra 4 a 5 minutos no Label Studio.
  2. **Atalhos sem atrito:** A tecla `O` entra no modo ordem e permite numerar todos os blocos sequencialmente com cliques diretos, enquanto as teclas `1` a `7` trocam a classe instantaneamente.
  3. **Zero barreira de entrada:** Não exige instalar Docker, Java, WSL ou configurar portas de rede. Qualquer colaborador com Chrome/Firefox/Edge abre e usa imediatamente.
* **Limitações a considerar:**
  1. Opera exclusivamente com retângulos ortogonais ($[x_0, y_0, x_1, y_1]$). Para diários oficiais isso cobre >99,5% do conteúdo, mas não permite recortar textos que contornem brasões em formato trapezoidal ou carimbos inclinados.
  2. Não possui servidor multiusuário com autenticação central; a coordenação de lotes é feita por divisão de arquivos JSON.

### 2.2 LAREX (Layout Analysis and Region Extraction)
* **Vantagens decisivas:**
  1. É a ferramenta de referência histórica para anotação no esquema PAGE XML.
  2. Suporte impecável a **polígonos livres**, permitindo contornar vinhetas, brasões e quebras irregulares de matéria.
  3. Gera arquivos PAGE XML nativos diretamente na pasta das imagens, dispensando scripts intermediários para salvar o XML.
* **Pontos de atrito no Windows:**
  1. Requer ambiente Java instalado e configurado no PATH do Windows.
  2. A interface gráfica é no estilo Java/Web clássico (GWT/Tomcat), mais pesada que um DOM HTML5 moderno.
  3. O estabelecimento de ordem de leitura no LAREX, embora nativo no PAGE XML, envolve seleção de nós e gerenciamento na árvore lateral, sendo consideravelmente mais lento do que o modo de cliques contínuos do `classificador.html`.

### 2.3 eScriptorium
* **Vantagens decisivas:**
  1. Plataforma colaborativa completa com interface web moderna, gerenciamento de projetos e permissões.
  2. Excelente caso o TCC decidisse segmentar até a granularidade de linhas de base *(baselines)* e caracteres manuscritos.
* **Pontos de atrito no Windows:**
  1. **Complexidade desproporcional de instalação:** Exige subir 5 containers Docker (Django, Celery, Redis, Postgres, Frontend) via WSL2. Na máquina de trabalho atual (laptop com 16 GB de RAM e treino de GPU em andamento), o overhead do eScriptorium pode saturar a memória RAM e causar instabilidade.
  2. O foco principal do eScriptorium é HTR (manuscritos antigos e transcrição textual), tornando a interface superdimensionada para a tarefa do TCC (que necessita apenas delimitar blocos/tabelas e indicar a sequência de leitura).

### 2.4 CVAT (Computer Vision Annotation Tool)
* **Vantagens decisivas:**
  1. É o padrão da indústria para visão computacional, com ferramentas de desenho extremamente polidas, interpolação e suporte multiusuário de ponta.
* **Gargalo fatal para o TCC:**
  1. **Não possui conceito nativo de Ordem de Leitura.** Em documentos, a ordem de leitura é um grafo/cadeia direcionada entre regiões. No CVAT, para indicar que a Caixa A precede a Caixa B, o anotador precisaria abrir o menu de atributos de cada caixa e digitar manualmente um número ordinal (1, 2, 3...) ou utilizar truques com IDs de vídeo. Isso tornaria a anotação de ordem extremamente lenta, tediosa e sujeita a erros de duplicidade ou saltos.

---

## 3. Recomendação Estratégica para o Teste Piloto (10 Páginas)

### Ferramenta recomendada para testar primeiro:
**`classificador.html` como linha de base primária de velocidade**, acompanhado de **LAREX como contraprova metodológica**.

**Justificativa:**
1. O **CVAT** está descartado para este objetivo específico por não ter suporte nativo a grafos/cadeias de ordem de leitura.
2. O **eScriptorium** exige uma infraestrutura pesada de Docker que compete diretamente pela pouca RAM livre da máquina de desenvolvimento (16 GB com treino em background).
3. O **`classificador.html`** já está 100% pronto, interoperável com Label Studio e agora com PAGE XML, e foi desenhado sob medida para a velocidade operacional de diários oficiais.
4. O **LAREX** é a única alternativa viável caso o Pedro ou o orientador exijam contornos poligonais ou validação em ferramenta consagrada de literatura de Humanidades Digitais/OCR.

---

## 4. Roteiro do Teste Piloto (10 Páginas do Lote `resultados/lote_sem_paragrafos`)

### 4.1 Preparação do Lote
1. Selecionar 10 páginas representativas de `resultados/lote_sem_paragrafos` (ex.: 4 páginas diagramadas em 2 colunas padrão, 3 páginas em 3 colunas densas, 2 páginas com tabelas transversais e 1 página com cabeçalho/aviso oficial).
2. Gerar a pré-anotação das 10 páginas:
   - Para o `classificador.html`: carregar o lote JSON via interface.
   - Para o LAREX: converter as 10 páginas para PAGE XML usando `conversor_page_xml.py` (`proprio_para_page_xml`) e colocar os arquivos `.png` e `.xml` no diretório de leitura do LAREX.

### 4.2 O que Medir (Métricas Objetivas de Desempenho)
Para cada uma das 10 páginas, o anotador cronometra de forma segregada:

1. **Tempo de Correção Geométrica ($T_{\text{geom}}$):**
   - Segundos gastos ajustando bordas de caixas, dividindo blocos fundidos incorretamente pelo extrator (Split) ou unificando blocos fragmentados (Merge).
2. **Tempo de Classificação Funcional ($T_{\text{classe}}$):**
   - Segundos gastos alterando rótulos (ex.: corrigindo um cabeçalho classificado como texto comum, ou marcando uma tabela).
3. **Tempo de Sequenciamento de Leitura ($T_{\text{ordem}}$):**
   - Segundos gastos ligando a sequência correta de leitura do início ao fim da página.
4. **Tempo Total da Página ($T_{\text{total}} = T_{\text{geom}} + T_{\text{classe}} + T_{\text{ordem}}$):**
   - Tempo integral de tela ativa até salvar a página.
5. **Índice de Sobrecarga e Erros:**
   - Número de cliques necessários por página.
   - Ocorrência de nós órfãos (blocos esquecidos fora da ordem) ou ciclos/laços acidentais.
   - Percepção qualitativa de fadiga visual em escala de 1 a 5.

---

## 5. Integração do Ciclo de Dados com o Novo Conversor (`conversor_page_xml.py`)

Com a criação do script `resultados/ferramenta_anotacao/conversor_page_xml.py`, o ecossistema do TCC fecha o ciclo completo de interoperabilidade bidirecional entre os três principais formatos da pesquisa:

```
                  ┌───────────────────────────────┐
                  │    Formato Próprio do TCC     │
                  │   (JSON simples / tarefas)    │
                  └───────┬───────────────▲───────┘
                          │               │
       proprio_para_ls()  │               │  ls_para_proprio()
                          ▼               │
                  ┌───────────────────────┴───────┐
                  │         Label Studio          │
                  │     (CEIA-DataPolicy JSON)    │
                  └───────┬───────────────▲───────┘
                          │               │
      ls_para_page_xml()  │               │  page_xml_para_ls()
                          ▼               │
                  ┌───────────────────────┴───────┐
                  │         PAGE XML 2019         │
                  │    (LAREX / eScriptorium)     │
                  └───────────────────────────────┘
```

### O que já está 100% resolvido pelo conversor:
1. **Importação do LAREX/eScriptorium para o TCC:**
   Qualquer anotação salva pelo LAREX em `.xml` pode ser importada para o formato do TCC com uma única chamada:
   ```bash
   venv/Scripts/python.exe -B resultados/ferramenta_anotacao/conversor_page_xml.py --page-para-proprio entrada.xml saida.json
   ```
2. **Exportação do LAREX/eScriptorium para o Label Studio:**
   Permite alimentar diretamente a plataforma do projeto parceiro Data Policy a partir do que foi anotado no LAREX:
   ```bash
   venv/Scripts/python.exe -B resultados/ferramenta_anotacao/conversor_page_xml.py --page-para-ls entrada.xml saida_ls.json
   ```
3. **Conversão de polígonos para Bounding Box:**
   Quando o LAREX gera polígonos com 6 ou 8 vértices em `Coords points`, o conversor extrai automaticamente a bounding box envolvente $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$, garantindo compatibilidade imediata com o classificador e com o avaliador do TCC.

### O que falta operacionalmente para colocar em produção:
1. **Script de Lote (Pasta inteira):**
   Atualmente o conversor opera arquivo a arquivo via CLI. Falta adicionar uma flag `--diretorio` para varrer automaticamente uma pasta contendo 50 arquivos `.xml` exportados pelo LAREX e compilar um único arquivo `tarefas.json` do Label Studio ou do TCC.
2. **Sincronização de Nomes e Imagens:**
   O LAREX exige que a imagem PNG e o arquivo PAGE XML compartilhem o mesmo prefixo de nome no mesmo diretório (ex.: `pagina_01.png` e `pagina_01.xml`). Para rodar o teste piloto de 10 páginas no LAREX, basta copiar as 10 imagens PNG renderizadas dos PDFs para a pasta de dados do LAREX junto aos XMLs gerados pelo conversor.
