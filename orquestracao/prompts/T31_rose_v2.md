## Contexto

`src/data/gerar_rose.py` (T30) pede a um VLM (Gemini) que agrupe as palavras do PDF em regiões e dê
a classe de cada uma, no formato do Diamond (`docs/GUIA_DIAMOND.md`). Comparado com a anotação humana
do `data/diamond/diamond_piloto` (15 páginas), o Rose acerta a classe de 94% das palavras — melhor que
a pré-anotação do detector (92%) —, mas **junta demais**: 241 regiões contra 456 do humano (F1 de
regiões 0,60, contra 0,93 da proposta). E: páginas puladas só aparecem no console; a docstring diz que
resposta incompleta interrompe, mas `main` preenche órfãs; com `preencher_orfas=True` a repetição por
"incompleta" é código morto; o limite do plano gratuito é 15 req/min e 500 req/dia
(`gemini-3.1-flash-lite`).

## Tarefa: Rose v2

Altere **só** `src/data/gerar_rose.py` e `tests/test_rose.py`.

1. **Novo modo `--modo regioes` (padrão).** A tarefa de entrada precisa ter `proposta` (lotes do Diamond
   gerados por `src/anotacao/preparar_diamond.py`; sem `proposta`, erro claro). O VLM recebe a imagem e
   a lista das regiões propostas (`id`, classe proposta, `bbox`, e o texto da região — palavras cujo
   centro cai nela, por linha, cortado em ~60 palavras) e responde, em JSON estrito, **uma entrada por
   região proposta** (todas, sem repetir):
   `{"regioes": [{"id": "p3", "classe": 1..9, "unir_com": "p2" ou null, "quebras": [indices de palavra]}]}`
   - `unir_com`: a região é a continuação da região indicada (mesma unidade: título quebrado em duas
     caixas; nome e cargo de uma assinatura; rótulo e valor do mesmo campo). Resolva cadeias
     (p4→p3→p2) com union-find; recuse ciclos e união com figura.
   - `quebras`: índices de palavra (dentro da região) em que começa uma região nova — vários campos
     ("ACORDANTE:", "OBJETO:") ou vários artigos na mesma caixa. Recuse índice fora da região.
   - A classe da região unida é a da primeira região da cadeia (a mais acima).
   - Caixa final = envelope das palavras; figura sem palavras mantém a `bbox` proposta.
   - Valide cobertura como hoje (`fora == 0`, `duplas == 0`); se falhar, a página vai para `erros.jsonl`.
   - Cada região gravada leva `de` (id ou lista de ids da proposta) e `origem: "vlm"`.
   O prompt deve trazer as regras do guia (uma caixa por parágrafo dentro de uma coluna; título separado;
   campo com rótulo e valor na mesma caixa, um campo por caixa; lista contígua e tabela inteiras; nome e
   cargo = assinatura; local e data = texto; cabeçalho e rodapé do diário) e **dizer para manter a
   segmentação proposta quando não houver motivo claro para unir ou quebrar**.
2. Mantenha o modo atual como `--modo palavras`, com a docstring corrigida (diga que órfãs são
   preenchidas pela proposta e marque essas regiões com `origem: "proposta"`).
3. **Registro de falhas:** toda página pulada vai para `<saida>/erros.jsonl` com `page_id`, `erro`,
   `tentativas`, `momento`. No fim, imprima quantas gravadas, puladas e por motivo.
4. **Ritmo e cota:** `--rpm` (padrão 14) espaça as chamadas; HTTP 429/503 → espera crescente (até 5
   tentativas); se a mensagem da API indicar cota **diária** esgotada, pare o lote de forma limpa (tudo
   gravado, código de saída 0 e aviso). Guarde o texto do erro HTTP (sem a chave) para essa decisão.
5. **Chave:** se `GEMINI_API_KEY` não estiver no ambiente, leia o `.env` da raiz (linhas `NOME=valor`)
   sem imprimir o valor.
6. **`--retomar`** continua valendo nos dois modos; `--paginas-ids arquivo.txt` (opcional) restringe
   a coleção a uma lista de `page_id`.
7. Registre em `tarefa["rose"]`: `modo`, `modelo`, `prompt_sha256`, resposta, tempo e tentativas.

## Testes

Em `tests/test_rose.py`, sem rede (substitua `chamar_vlm` por função falsa): parse do modo `regioes`
(unir cadeia, quebra, figura sem palavras, recusa de ciclo, recusa de id faltando/repetido, cobertura),
`erros.jsonl` gravado ao pular, parada limpa na cota diária, espaçamento pelo `--rpm` (substitua
`time.sleep`), leitura da chave do `.env` num diretório temporário, e os 22 testes antigos passando.

## Regras

Sem rede, sem chamar a API de verdade, sem GPU. Não toque em `data/`, em `src/anotacao/` nem no
extrator. Rode `venv\Scripts\python.exe -m unittest discover -s tests -v` (todos passam) e
`venv\Scripts\python.exe src\data\gerar_rose.py --colecao data/diamond/diamond_piloto/tarefas.jsonl --dry-run`
(imprime o prompt do modo `regioes` de uma página, sem gravar nada).

## Resposta final

Em FEITO: o contrato de resposta do modo `regioes`, quantos testes e o tamanho do prompt da página do
dry-run (caracteres).
