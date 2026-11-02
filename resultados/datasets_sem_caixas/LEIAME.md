# Versões experimentais sem caixas de parágrafo

Pedido do Pedro em 04/10: investigar representações que evitem a segmentação fina de texto e preservem tabelas e imagens inteiras. Não substituem o dataset oficial.

- `linhas/`: palavras agrupadas por linha, com separação de calhas; tabelas e imagens atômicas.
- `colunas/`: linhas agrupadas em faixas de coluna, admitindo mudanças de colunas e elementos que atravessam a página. Tabelas e imagens atômicas.
- Cada pasta contém `treino.jsonl`, `validacao.jsonl`, `teste.jsonl`, `sem_split.jsonl` e `bancada_humana.jsonl`. A bancada sobrepõe os demais arquivos; não concatenar tudo.
- `referencias/` guarda a referência separadamente. A ordem humana de regiões é expandida para palavras com ordem geométrica interna. Não é uma anotação humana independente de cada palavra.
- `manifesto.json` registra cobertura e hashes das fontes; `validacao_exportacao.json` registra integridade.

As unidades chegam embaralhadas. `ks` identifica as palavras; `bbox` contém apenas o envelope da unidade escolhida; `coluna` associa linhas à faixa. O campo legado final de cada palavra vem da extração original e não é usado pelo ordenador. Não usar esse campo como rótulo de treino. Texto não passa pelo segmentador de parágrafos antigo.

As fontes são páginas já extraídas em `data/diamond/`, não o acervo inteiro. Split por veículo herdado de `splits.json`; páginas sem veículo elegível permanecem em `sem_split`. Exportar treino não cria supervisão humana. Detectores e parâmetros herdados são exploratórios, sem seleção nova de checkpoint.

A identificação de calhas exige suporte vertical e pelo menos quatro linhas de cada lado. Páginas curtas ou colunas irregulares podem permanecer como uma faixa. Não é ausência total de geometria: permanecem coordenadas de palavras, linhas e faixas.

Para repetir: `venv\Scripts\python.exe src\data\dataset_sem_caixas_finas.py --avaliar`.

A avaliação usa LayoutReader pré-treinado local em CPU, sem treino novo. Acima de 510 unidades, o adaptador existente agrupa geometricamente para respeitar o limite do modelo; portanto esse caso não mede ordenação puramente neural de todas as linhas. A versão colunas também impõe ordem geométrica interna. Os resultados são de desenvolvimento, não prova de generalização. Comparar variantes na mesma referência de palavras, nunca usar IDs de blocos de outra segmentação.
