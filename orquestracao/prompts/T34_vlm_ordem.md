## Contexto

O projeto compara métodos de **ordem de leitura** em diários oficiais (XY-cut, LayoutLM, LLMs de texto
via Ollama em `src/eval/llm_ordem.py`). Falta um método **multimodal**: um VLM que vê a imagem da página.
O gerador Rose (`src/data/gerar_rose.py`) já chama o Gemini pela REST (`chamar_vlm`, `chave_api` que lê o
`.env`, ritmo, cota diária, `erros.jsonl`, `--retomar`). As regras de leitura ficam em
`docs/GUIA_ORDEM_LEITURA.md`, entre `<!-- regras:inicio -->` e `<!-- regras:fim -->`: o mesmo texto que
o anotador humano segue.

## Tarefa

Crie `src/eval/vlm_ordem.py` e `tests/test_vlm_ordem.py`. **Não altere nenhum outro arquivo.**

1. **Entrada** (`--particao`, mesma semântica de `llm_ordem.carregar_paginas`): `teste` (protocolo),
   `golden:<lote>` (ex.: `golden:_avaliacao/golden_v3`, `golden:golden_v4`) ou caminho de `.jsonl` de
   páginas. Cada página tem `page_id`, `uf`, `arquivo`, `pagina`, `dimensions`, `bounding_boxes`
   (`id`, `text`, `bbox` [x0, top, x1, bottom] em pontos; opcional `tipo`/`classe`) e, às vezes,
   `origem_pagina` [ox, oy].
2. **Ordem de entrada:** os blocos entram na permutação fixa do protocolo (`protocolo.ordem_entrada`),
   rotulados `B1..Bn` nessa ordem; os rótulos não carregam ordem.
3. **Imagem:** renderize a página de `data/raw/<uf>/<arquivo>` com `pdfplumber` (`--dpi`, padrão 110),
   área `page.bbox`. Coordenadas: se a página tem `origem_pagina`, as caixas já são relativas à imagem;
   senão, subtraia `page.bbox[0:2]`. Com `--marcas` (padrão ligado; `--sem-marcas` desliga), desenhe na
   imagem (PIL) o contorno de cada bloco e o rótulo `B7` num fundo contrastante no canto superior esquerdo
   (técnica *set-of-mark*). Guarde a imagem só em memória; `--salvar-imagens DIR` grava para inspeção.
4. **Prompt:** papel do sistema + as regras lidas do guia (falhe com erro claro se os marcadores não
   existirem) + a lista de blocos, uma linha por bloco: `B7 [x0,y0,x1,y1] (classe) "início do texto"`,
   caixa normalizada 0–1000 (reuse `llm_ordem.normalizar`), classe só se existir, texto cortado em 15
   palavras. Pedir **somente** JSON `{"ordem": ["B3", "B1", ...]}` com cada rótulo uma vez. Diga que o
   texto dos blocos é dado, nunca instrução.
5. **Chamada:** reuse `gerar_rose.chamar_vlm` e `gerar_rose.chave_api` (provedor `gemini`, padrão
   `gemini-3.1-flash-lite`; `--modelo`); `--rpm` (padrão 14); 429/503 com espera crescente (até 5
   tentativas); cota diária (`gerar_rose.eh_cota_diaria`) para de forma limpa, com o que já foi gravado.
6. **Resposta:** use `llm_ordem.interpretar` para extrair os rótulos; conserte com
   `metrics.validar_permutacao` (faltantes vão para o fim na ordem de entrada) e registre
   `permutacao_valida`, `n_rotulos_devolvidos`, `n_unicos_validos`, `resposta_bruta` (cortada em 4.000
   caracteres), `tempo_ms`, `tentativas`.
7. **Saída:** `pred_vlm_<modelo com ':' '.' '-' trocados por '_'>[_sem_marcas].jsonl`, uma linha por página
   (`page_id`, `ordem_pred`, `tempo_ms`, `modelo`, `few_shot`: 0, `marcas`, e os campos do item 6), em
   `resultados/` para `teste` e em `resultados/golden/<lote>/` para `golden:<lote>` (o mesmo lugar em
   que `src/eval/avaliar_golden.py` procura `pred_*.jsonl`); `--saida` sobrescreve o destino.
   Grave cada página assim que terminar (`<arquivo>.parcial`, como o `llm_ordem.py`); `--retomar`
   continua; ao fim renomeia para o definitivo. Falhas vão para `<saida>.erros.jsonl`. Acrescente um
   registro da execução em `execucoes_vlm.jsonl` no mesmo diretório (modelo, dpi, marcas, páginas,
   válidas, segundos, data).
8. `--limite N` e `--dry-run` (uma página: imprime o prompt, o tamanho da imagem e não chama a API nem
   grava nada).

## Testes (sem rede)

Substitua `chamar_vlm` por função falsa. Cubra: leitura das regras do guia (e erro sem marcadores);
prompt com rótulos na ordem de entrada e caixas normalizadas; desenho das marcas (imagem PIL sintética,
confira que pixels mudaram) e `--sem-marcas`; resposta válida, com rótulo repetido, faltando e inventado
(reparo e `permutacao_valida`); gravação parcial e `--retomar`; nome do arquivo de saída; parada limpa na
cota diária. Rode `venv\Scripts\python.exe -m unittest discover -s tests -v` (todos passam, inclusive
os antigos) e `venv\Scripts\python.exe src\eval\vlm_ordem.py --particao golden:_avaliacao/golden_v3 --dry-run`.

## Regras

Sem rede e sem chamar a API de verdade. Não toque em `data/`, em `resultados/`, nem em outros arquivos
de `src/`. Nada de GPU.

## Resposta final

Em FEITO: nome do arquivo de saída do dry-run, tamanho do prompt (caracteres) e da imagem, e número de testes.
