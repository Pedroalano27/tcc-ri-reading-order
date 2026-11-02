## Contexto

O Pedro contribui com o **Acessilia** (A11yDevs), um projeto de código aberto de acessibilização de
documentos e imagens. Ele quer saber o que dá para aproveitar dele neste TCC, dando os créditos.
Os três repositórios estão clonados localmente, **fora deste projeto**:

- `C:\Users\pedro\OneDrive\Documentos\Acessilia\acessilia` — aplicação principal (backend, frontend,
  docs, relatórios de bugs e de homologação);
- `C:\Users\pedro\OneDrive\Documentos\Acessilia\acessilia-structure-extractor` — serviço de extração
  de estrutura (Docling e PyMuPDF, estrutura canônica, REST e MCP);
- `C:\Users\pedro\OneDrive\Documentos\Acessilia\acessilia-dataset` — PDFs de entrada, documento
  canônico, planos PDDL e manifestos de processamento.

O rumo que o Pedro está considerando para o TCC (ainda não decidido):
1. melhorar o **extrator de blocos** (`src/data/extrator.py`: regras sobre as palavras da camada de
   texto do PDF + detector Docling Heron só para tabelas, em `src/data/layout.py`), possivelmente
   combinando com detectores de layout prontos (Docling, DocLayout-YOLO) e treinando algo;
2. criar um conjunto **Diamond**: cerca de 200 páginas de diários com as caixas (blocos) corrigidas à
   mão pelo Pedro, para treinar e avaliar o extrator — hoje o Golden só anota a **ordem** dos blocos;
3. avaliar o efeito da segmentação e da ordem de leitura em **RI e RAG**, e no valor fora dos diários
   (a ordem de leitura é central para leitores de tela, o que liga o TCC à acessibilidade).

## Tarefa

Faça uma análise **a fundo** do código, dos esquemas, dos documentos e dos relatórios dos três
repositórios e escreva `docs/ANALISE_ACESSILIA.md`, em português, com estas seções:

1. **Visão geral.** Para cada repositório: propósito, arquitetura, módulos principais (com caminho),
   estado (último commit, via `git log -1`), maturidade (testes, CI).
2. **Extração de estrutura em detalhe.** Como o `acessilia-structure-extractor` usa o Docling e o
   PyMuPDF; o esquema canônico (`schemas/`): quais elementos existem (títulos, parágrafos, tabelas,
   listas, figuras, cabeçalho e rodapé), quais sinais cada um guarda (bbox, página, proveniência,
   rótulo, confiança, **ordem de leitura**); como a ordem de leitura é obtida; como tabelas são
   tratadas (leia `acessilia/docs/bugs/0005-docling-table-cells-descartadas.md`); versões do Docling e
   dos modelos fixadas nos manifestos.
3. **Dataset.** Formato de `input/`, `intermediate/` (documento canônico, plano PDDL, manifesto) e
   `outputs/`; como é gerado; o que ele ensina para o **formato do Diamond** (classes de região,
   esquema JSON, proveniência, versionamento).
4. **Lições dos relatórios.** O que `docs/bugs/`, `RELATORIO-HOMOLOGACAO.md`,
   `comparativo-modelos-visao.md` e os planos em `docs/` dizem que é relevante para um extrator de
   diários oficiais (falhas do Docling, custo, modelos de visão, desempenho).
5. **Oportunidades para o TCC**, ordenadas por valor/esforço, cada uma com: o que reaproveitar
   (arquivo e trecho), como encaixaria neste projeto (quais módulos daqui), esforço estimado, riscos.
   Considere pelo menos: usar a saída do Docling (todas as classes, não só tabela) como proposta de
   regiões a fundir com as palavras do nosso extrator; o esquema canônico como formato do Diamond; o
   harness de testes e snapshots; a avaliação de acessibilidade como aplicação da ordem de leitura.
6. **Licenças e créditos.** Licença de cada repositório e de cada dependência que seria reaproveitada
   (leia `pyproject.toml`, `poetry.lock` e metadados locais; não acesse a rede). Diga explicitamente o
   que muda se o código reaproveitado depender do **PyMuPDF (AGPL-3.0)** e o que vale para modelos
   (Heron e outros). Texto sugerido para os créditos no TCC e no README.
7. **O que não vale a pena**, com o motivo.

## Regras desta tarefa (além das gerais)

- Os três repositórios do Acessilia são **somente leitura**: não crie, altere nem apague nada lá, não
  rode `git` que mude estado (checkout, pull, stash, commit etc.), não rode `docker`, testes que
  gravem arquivos ou instalação de pacotes. `git log`, `git show` e leitura de arquivos podem.
  O repositório `acessilia` tem 3 alterações locais do Pedro em andamento: não toque.
- Neste projeto, escreva **só** `docs/ANALISE_ACESSILIA.md`. Nada de GPU, treino ou rede.
- Separe **fato** (com caminho do arquivo e, quando fizer sentido, linha) de **sugestão**. Não invente
  funcionalidades: se algo não está no código, diga que não encontrou.

## Resposta final

Em FEITO: as três oportunidades de maior valor e a situação das licenças, em poucas linhas.
