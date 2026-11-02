# LayoutLM sobre linhas com texto

Gerado por `treinar_sem_caixas_texto.py relatorio`. Fumaças são evidência de execução, não comparação de eficácia.

`ComTexto` lê o campo `text`, preservado por `pagina()`, e usa WordPiece do snapshot local com `local_files_only=True`. Cada subpalavra recebe a mesma caixa normalizada e o índice da unidade na entrada. Sucessor e pontual já somam estados e dividem pela contagem (`scatter_add_`); perdas, geometria, alvos e decodificação originais são reutilizados.

Orçamento teórico, calculado pelo script; não é medição do corpus. K é teto, sem preenchimento artificial para textos curtos.

| Unidades após preparação | K máximo por unidade |
|---|---:|
| 1–85 | 6 |
| 86–102 | 5 |
| 103–127 | 4 |
| 128–170 | 3 |
| 171–255 | 2 |
| 256–508 | 1 |

`K = max(1, min(6, 510 // n))`; o total com CLS/SEP é limitado a 510. Quando o prefixo ocupa todo o orçamento, reduz-se o excesso das unidades com mais tokens, com desempate pela entrada embaralhada. Nenhuma unidade é removida. Se não couber um token por unidade, há erro explícito. A compactação original acima do seu limite é preservada; não há segmentação nova.

## Âncoras

A bancada original foi chamada com saídas isoladas. P2 é reproduzido com detecções congeladas; P1m é importado do histórico, conforme o controle original. Tolerâncias são as da bancada.

| Controle golden_v4 | Páginas | τ palavras | Quebras/página |
|---|---:|---:|---:|
| P2 | 44 | 0,985948 | 6,045455 |
| P1m | 44 | 0,952424 | 8,931818 |
| regra_colunas_exportada | 44 | 0,985948 | 6,045455 |

## Treino e fumaça

K mediano e fração abaixo do teto referem-se a páginas únicas realmente usadas na perda, após preparação; validação não entra. O JSON também guarda a mediana dos tokens reais por unidade.

| Execução | Dispositivo | Selecionadas | Visitadas | Passos | Épocas | Segundos | K mediano | Fração K < 6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| fumaca_texto | cpu | 8 | 8 | 1 | 1 | 41,9 | 3,0 | 0,750 |
| sucessor_linhas_texto_s42 | cuda | 3140 | 3140 | 7860 | 20 | 6820,3 | 3,0 | 0,764 |
| sucessor_linhas_texto_s42 | cuda | 3140 | 1160 | 145 | 0 | 125,3 | 3,0 | 0,745 |

## Inferência e avaliação

Coortes separadas; grupos humanos seguem o split por veículo. Métricas importadas de `bancada_ordenadores.metricas`, que chama `erros_ponta_a_ponta.medir/eventos` e a expansão canônica.

| Modelo | Bancada | Grupo | n | Completa | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |
|---|---|---|---:|---|---:|---:|---:|---:|
| sucessor_linhas_texto_s42 | golden_v3_novo | todos | 27 | sim | 0,931019 | 23,19 | 86,66% | 84,70% |
| sucessor_linhas_texto_s42 | golden_v3_novo | nao_vistos | 27 | sim | 0,931019 | 23,19 | 86,66% | 84,70% |
| sucessor_linhas_texto_s42 | golden_v4 | todos | 44 | sim | 0,941984 | 20,77 | 88,73% | 86,73% |
| sucessor_linhas_texto_s42 | golden_v4 | vistos | 5 | sim | 0,986548 | 16,20 | 93,28% | 93,13% |
| sucessor_linhas_texto_s42 | golden_v4 | nao_vistos | 39 | sim | 0,936271 | 21,36 | 88,15% | 85,91% |
| sucessor_linhas_texto_s42 | teste_silver | todos | 89 | sim | 0,930033 | 50,46 | 74,37% | 70,99% |
`resultados/ordenadores_treinados_sem_caixas/fumaca_texto/pred_fumaca_texto/fumaca_texto__linhas__tempos.json`: 3 páginas com diagnóstico, 3 com repetição sem ouro e métricas originais.

## Limitações e operação

Não há conclusão sobre o ganho de texto antes da avaliação completa. Textos longos, inclusive tabelas, perdem o restante após o prefixo. Nas páginas densas K mínimo expõe só a primeira subpalavra da linha. O tokenizador uncased tem cobertura limitada do português. K nominal e número de tokens reais são distintos, especialmente em imagens sem texto.

Golden v4 foi usado no desenvolvimento da regra de colunas. O golden v3 adicional é pequeno. Referência humana é de regiões expandidas; silver é fluxo automático nos veículos confiáveis. Páginas humanas são excluídas do treino, mas alguns veículos humanos podem ser vistos. As coortes podem se sobrepor ao silver e não devem ser somadas. Fumaça com n pequeno não estima eficácia, generalização ou custo em GPU.

Leitura sequencial, sem DataLoader/workers e com até quatro threads. Checkpoint e estatísticas parciais são salvos pelo treinador original. Limite de tempo encerra seu orçamento; queda antes disso permite retomar `ultimo.pt`. Configuração inclui versão/hash do wrapper e tokenizador: não retomar checkpoints geométricos como se fossem textuais. Usar `ordenar_bancadas_texto.py` para reconstruir ComTexto; o ordenador antigo reconstrói UmToken e não serve para este checkpoint.

`gpu_texto.sh` não é executado pela implementação. Aguarda o marcador da semente anterior solicitada e a conclusão da fila antiga, que também prevê outra semente. Isso impede disputa entre filas sem trava comum.

## Reprodução da fumaça (CPU)

```powershell
venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas_texto.py treinar --modelo sucessor --representacao linhas --device cpu --n-treino 8 --max-passos 2 --max-minutos 3 --epocas 1 --nome fumaca_texto --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto
venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas_texto.py --checkpoint resultados/ordenadores_treinados_sem_caixas/fumaca_texto/melhor.pt --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto/pred_fumaca_texto --limite 1 --avaliar
venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas_texto.py relatorio
```

A inferência limitada usa uma página de cada bancada. A opção `--avaliar` registra cobertura parcial, sem apresentá-la como bancada completa.
