## Contexto

Durante a noite de 12 para 13/09/2026, o roteiro `orquestracao/noite_v3.sh` rodou, sem ninguém
acompanhando, o pipeline experimental sobre a **segmentação v3** (tabela = um bloco, calhas
locais; ver `docs/METODOLOGIA.md` seção 3.3.2 e `docs/HANDOFF.md` seção 2.2). O Pedro vai ler de
manhã o que aconteceu. Os resultados da segmentação anterior (v1) estão em
`resultados_segmentacao_v1/`, e os da v3 em `resultados/`.

## Correção feita durante a noite (leia antes)

Os passos `golden_v3` e `ri_japeri_piloto` do roteiro principal avaliaram o LayoutLM sucessor com
**busca em feixe**, por um padrão errado em `prever()`; no teste, o método usa decodificação em
cadeias. O padrão foi corrigido (`src/models/layoutlm_sucessor.py`) e os passos foram refeitos por
`orquestracao/noite_v3_correcao.sh` como `golden_v3_cadeias` e `ri_japeri_piloto_cadeias`. Os
arquivos em `resultados/` já são os corrigidos. No relatório, cite a correção em uma frase na seção
1 (o passo `relatorio_antigravity` do roteiro principal falha de propósito: o prompt dele foi
substituído por este), e use sempre os números atuais dos arquivos. Leia também
`resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md` (refeito) e resuma a seção
"Correção de 13/09" dele na seção 5.

## Tarefa

Crie **um único arquivo**, `docs/RELATORIO_NOITE_V3.md`, em português, para o Pedro ler em cinco
minutos. Não altere nenhum outro arquivo e não rode treino, avaliação nem nada que use GPU. Pode
rodar trechos de Python que só leem arquivos.

Seções, nesta ordem:

1. **O que rodou.** Tabela com cada passo de `orquestracao/logs/noite_v3/status.jsonl` (passo,
   início, fim, duração, código de saída). Para cada passo com código diferente de 0, as últimas
   linhas relevantes do log em `orquestracao/logs/noite_v3/<passo>.log` e uma frase sobre a causa
   provável.
2. **Segmentação v1 → v3.** Por coleção, a partir de `resultados/qualidade_segmentacao_v3_*.json`:
   páginas, blocos por página, blocos sobrepostos e blocos de uma palavra, antes e depois.
3. **Teste (silver) v1 → v3.** A partir de `resultados/comparacao.json` e
   `resultados_segmentacao_v1/comparacao.json`: para cada método presente nos dois, τ de Kendall,
   sucessor correto e ARD normalizado lado a lado. Diga o número de páginas de cada lado (95 na
   v1, 89 na v3) e que a comparação é entre segmentações diferentes das mesmas páginas.
4. **Curva de aprendizado v1 → v3.** A partir dos dois `curva_aprendizado/curva.json`: τ e sucessor
   correto por tamanho de treino e por modelo.
5. **Golden (anotação humana).** A partir de `resultados/golden/_avaliacao/golden_v3/avaliacao.md`:
   a tabela geral e as dos grupos `silver` e `incerto`, copiadas.
6. **Ablações e limiar.** Os métodos `ablacao_suc_*`, `suc_limiar_*` e `layoutlm_sucessor_feixe` que
   aparecerem em `resultados/comparacao.json`.
7. **RI em Japeri e latência.** Os números de `resultados/ri_japeri/resultado.md` e dos arquivos
   `resultados/latencia_*.json`, comparados com os equivalentes da v1 quando existirem.
8. **O que falta o Pedro fazer.** Subir `dist/kaggle/tcc_ordem_leitura.zip` como nova versão do
   dataset e rodar **só** `kaggle_llm_ordem.ipynb` (as LLMs de 27–35B não cabem na 4050; o treino já
   rodou localmente), seguindo `docs/KAGGLE.md`; conferir se o pacote foi gerado (passo
   `pacote_kaggle`).

## Regras

- **Todo número vem de um arquivo, com o caminho citado na seção.** Nada de estimar, arredondar
  diferente do arquivo ou completar com número que não esteja lá. Se um arquivo não existir ou um
  passo falhou, escreva isso explicitamente no lugar da tabela.
- Não interprete além do que os números mostram. Uma frase de leitura por seção basta ("na v3, o
  XY-cut passa de A para B no teste"); conclusões metodológicas ficam para o Pedro e o Claude.
- Na resposta final, liste as seções que ficaram incompletas e por quê.
