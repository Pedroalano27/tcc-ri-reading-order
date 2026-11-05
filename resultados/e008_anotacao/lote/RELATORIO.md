# E008 — Lote de anotação densa × simplificada

Lote pronto: **36 páginas**, semente **20261104**. Este preparo não mede as hipóteses H6–H9.

Âncora reproduzida com os módulos originais: τ **0,985948** e **6,045455** quebras/página, em 44 páginas do golden_v4 (`ancora.json`).

## Composição

| Bloco | Ordem entre sessões | 1 coluna | 2 colunas | 3+ colunas | Tabela ls3 |
|---|---|---:|---:|---:|---:|
| 1 | A→B | 6 | 6 | 6 | 7 |
| 2 | B→A | 6 | 6 | 6 | 8 |

| Veículo | PDFs | Páginas | 1 coluna | 2 colunas | 3+ colunas | Tabela ls3 |
|---|---:|---:|---:|---:|---:|---:|
| official_diary_pr | 6 | 6 | 3 | 3 | 0 | 1 |
| official_diary_rr | 1 | 1 | 1 | 0 | 0 | 1 |
| official_diary_sc | 7 | 11 | 3 | 0 | 8 | 4 |
| official_diary_rn | 5 | 7 | 0 | 6 | 1 | 4 |
| official_diary_ce | 3 | 3 | 3 | 0 | 0 | 1 |
| official_diary_ma | 3 | 5 | 2 | 3 | 0 | 4 |
| official_diary_rj | 3 | 3 | 0 | 0 | 3 | 0 |

Total: 28 PDFs; 15 páginas com tabela; mínimo observado de 97 palavras. Nenhuma página zero; no máximo duas páginas, não consecutivas, por PDF.

## Exclusão e auditoria

- lote_x_tocados_pdf: **0**.
- lote_x_e001_pdf: **0**.
- lote_x_excluidos_sha256: **0**.

Inventário: 1233 nomes excluídos; 44150 fontes locais seguras conferidas; 1231 nomes do cache/lacre E001 excluídos conservadoramente. Evidência em `cache/inventario.json`.

O manifesto real do E001 não tem uma lista de PDFs: contém hashes de artefatos. Foram usados somente os nomes e hashes do inventário, do cache de hashes e dos metadados do lacre. Isso exclui também PDFs candidatos não escolhidos pelo E001. Nenhuma tarefa, imagem ou conteúdo de página do teste cego foi aberto. O SHA-256 do manifesto foi registrado, sem abrir os artefatos que ele referencia.

## Sorteio e representação

Listas de PDFs permutadas por veículo com a semente 20261104; veículos percorridos em rodadas. Até doze páginas internas em ordem sorteada por PDF, parando em duas elegíveis não consecutivas. Filtro: pelo menos 80 palavras e no máximo 5% de glifos ilegíveis, como no E001. O primeiro fim de rodada com quotas viáveis encerra o pool: 77 páginas candidatas após 7 rodadas. Seleção binária com custo pseudoaleatório fixo por página, quotas exatas por coluna, mínimo de tabelas, máximo por PDF e presença dos sete veículos. Não é uma amostra aleatória simples do acervo; probabilidades de inclusão não foram estimadas.

As colunas são a estimativa automática de calhas da representação canônica, não uma classificação humana. Tabela ls3 significa detecção com score ≥ 0,45; pode incluir falsos positivos/negativos. O detector e a renderização são os mesmos do E001 (CPU, offline). As linhas e átomos vêm de `unidades_sem_caixas.representar`, sem parágrafos; todas as palavras têm um único dono pelos IDs canônicos. `proposta` é embaralhada por `ordem_entrada` com `random.Random(f"entrada-{page_id}")`; não há ordem humana/automática pré-preenchida.

Coordenadas de 3 propostas foram recortadas aos limites da página com a mesma regra do E001. As coordenadas anteriores ficam em `bbox_original`; palavras e IDs canônicos são preservados. A cobertura efetiva após o recorte também foi conferida pelo conversor original do anotador.

Cada bloco tem seis páginas de cada estrato. A divisão equilibra tabelas por estrato e no total, além das contagens por veículo, com diferença máxima de uma quando o total é ímpar. A ordem de apresentação está em `blocos.json` e nas linhas do JSONL: primeiro bloco 1, depois bloco 2. Não reembaralhar na interface.

## Uso pelo Pedro

1. Abra `../ferramenta/anotador.html`. Confira o nome Pedro. Crie cópias temporárias dos dois blocos com o comando abaixo; o lote canônico permanece intacto.

```powershell
$e008 = "resultados/e008_anotacao/lote/tarefas.jsonl"
Get-Content -LiteralPath $e008 -Encoding UTF8 | Select-Object -First 18 | Set-Content -Encoding UTF8 "$env:TEMP/e008_bloco_1.jsonl"
Get-Content -LiteralPath $e008 -Encoding UTF8 | Select-Object -Last 18 | Set-Content -Encoding UTF8 "$env:TEMP/e008_bloco_2.jsonl"
```

2. **Sessão 1:** bloco 1 no modo **A — Densa**, depois bloco 2 no modo **B — Simplificada**. No A, selecione origem **em branco**: desenhar e classificar as caixas densas do zero. No B, corrigir linhas/átomos automáticos e marcar estruturas/ruído. Nos dois, anotar a ordem de leitura.
3. Configure a semente 20261104 e **desmarque embaralhar**. Selecione o arquivo temporário do bloco em Abrir Tarefas e carregue a pasta `lote/img` em Pasta Imagens. A ordem já foi sorteada. O modo é global, não muda por metadado de tarefa.
4. Exporte a sessão ao terminar cada bloco; identifique externamente sessão, bloco, modo e data. Exporte antes de trocar modo. **Depois de configurar cada novo modo, reimporte o JSONL original do bloco**, pois a troca de modo reconverte o estado normalizado da ferramenta e pode perder as propostas. Não continue a anotação anterior no outro modo.
5. **Sessão 2, pelo menos sete dias depois (preferencialmente sete a dez):** bloco 1 no **B**, bloco 2 no **A**; mesma ordem dentro dos blocos, reimportando os dados iniciais e sem consultar o resultado da sessão 1. Use sempre A em branco e B com proposta. Exporte separadamente cada bloco. A análise principal usa só a primeira sessão de cada página; a segunda mede os efeitos cruzados/memória.
6. Pause o cronômetro em interrupções e registre os pulos. Preserve os exports originais. Nenhuma anotação foi criada por este preparo.

A escolha operacional A em branco usa uma opção existente do anotador e evita tratar linhas automáticas como caixas densas. Assim, o custo compara desenho denso do zero com correção de proposta simplificada: não isola apenas a taxonomia, e não representa uma condição densa com caixas de parágrafo pré-anotadas.

## Validação do anotador

Playwright instalado: False; Selenium instalado: False. Nenhuma biblioteca foi instalada. Ensaio headless: Não concluído neste ambiente: Error: spawn EPERM. Detalhes da tentativa em `cache/validacao_anotador.json`; foi usada a alternativa de validação pelo código.

O código do leitor foi inspecionado (`carregarArquivoTarefas`, `converterTarefasEntrada`, `normalizarPalavras`, `calcularPalavrasCobertas`). Seu JavaScript original foi executado em Node/vm para **36 páginas**, incluindo as duas primeiras: modo B carrega propostas, modo A em branco inicia sem caixas, ambos sem ordem preenchida. Todos os JPEGs foram decodificados/verificados com PIL. Nenhuma palavra ficou sem cobertura no conversor geométrico.

O conversor do anotador recalcula pertencimento por centro da palavra e tolerância geométrica, ignorando os IDs fornecidos: 43 palavras tiveram cobertura por mais de uma proposta. Isso é um diagnóstico da interface; os IDs canônicos da representação não têm perda/duplicação. Não demonstra H9 nem valida exportação após edição. Detalhes por página em `cache/validacao_anotador.json`.

Quando disponível, o ensaio headless abre o HTML original, importa duas páginas, navega entre elas e confere imagens decodificadas, elementos SVG, propostas no modo B e início em branco no A, sem erros JavaScript. Não valida precisão do cronômetro, persistência do autosave, ações ou exports no navegador. Recomenda-se também o ensaio manual descrito no LEIAME, sem usar seus tempos como anotação experimental e recarregando os dados iniciais antes da sessão real.

## Bancadas e limites

| Bancada | Uso neste preparo |
|---|---|
| golden_v4 | Reprodução da âncora, sem ajuste |
| golden_v3_novo | Não avaliada; já consultada em rodadas anteriores |
| teste silver CE/MA/RJ | Não avaliado; PDFs identificados excluídos |

Não há referência humana nas páginas novas. Δ contra a regra, IC95 por veículo, Wilcoxon por veículo, páginas melhor/igual/pior e reparos/regressões de sucessores não se aplicam ao preparo: serão calculados após anotação pela régua existente, mantendo as três bancadas separadas. Não há alegação de qualidade nem tempo humano novo.

Limitações: estratos e tabelas automáticos, acervo condicionado às exclusões e ao texto digital (sem OCR), páginas quase vazias/capas excluídas, anotador único e possível memória entre sessões. A ausência de uso anterior é verificável nos artefatos locais inventariados, sem garantir ausência de consulta humana não registrada. Cartão E008 não existia em `experimentos/cards/` nesta execução; escopo extraído da tarefa e do plano. Nenhum arquivo pré-existente ou anotação humana foi alterado. Nenhuma escrita em data/, leitura de dados do parceiro, uso de GPU ou publicação.

## Retomar ou conferir

```powershell
venv/Scripts/python.exe -B orquestracao/analises/e008_montar_lote_cruzado.py
venv/Scripts/python.exe -B orquestracao/analises/e008_montar_lote_cruzado.py --conferir
```

Depois do manifesto final, a execução padrão só confere os hashes, sem ressorteio ou reextração. Todos os números deste relatório são produzidos pelo script a partir dos artefatos da execução. Hashes de PDFs, código, tarefas, imagens, blocos e relatório estão em `manifesto.json`.
