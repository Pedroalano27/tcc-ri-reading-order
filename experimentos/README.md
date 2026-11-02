# Experimentos — como registrar e comparar

Estrutura criada em 02/11/2026 para a fase de novembro ([plano](../docs/PLANO_PESQUISA.md)).

| Arquivo | Para quê |
|---|---|
| [HIPOTESES.md](HIPOTESES.md) | hipóteses falsificáveis com critérios de sucesso e de abandono definidos antes |
| `cards/E###_*.md` | um cartão por experimento: pergunta, método, critérios, execuções, conclusão, "para o texto do TCC" |
| `registro.jsonl` | uma linha por execução (commit, hash da configuração e dos dados, ambiente, métricas, veredito). Só cresce |
| [REGISTRO.md](REGISTRO.md) | tabela gerada do jsonl (não editar à mão) |
| [DATASETS.md](DATASETS.md) | versões nomeadas dos dados (D1, D2...) com hashes |
| [NAO_FUNCIONOU.md](NAO_FUNCIONOU.md) | tentativas sem ganho, com motivo e aprendizado; consultar antes de propor algo |
| `consultas/` | perguntas e respostas do ChatGPT (orientador técnico), com as decisões tiradas de cada uma |
| `TESTE_CEGO.lock` | (a criar no E001) lista e hashes das páginas do teste cego; ninguém as abre até a avaliação final |
| [modelo_cartao.md](modelo_cartao.md) | modelo usado por `registro.py novo` |

## Ciclo de um experimento

1. **Abrir o cartão** antes de rodar, com a hipótese e os critérios preenchidos:
   ```bash
   venv/Scripts/python.exe -B src/exp/registro.py novo --titulo "Oráculos do grafo" --frente ordenacao --hipotese H0
   ```
2. **Rodar** o script do experimento. O script escreve o relatório em `resultados/<pasta>/` e um `metricas.json` no formato `{"golden_v4": {"tau": .., "quebras": .., "sucessor": ..}, ...}`.
3. **Registrar** cada execução:
   ```bash
   venv/Scripts/python.exe -B src/exp/registro.py registrar --id E002 --metricas resultados/oraculos/metricas.json \
       --config resultados/oraculos/config.json --dados resultados/unidades_sem_caixas/bancadas/golden_v4.jsonl \
       --ambiente local --veredito inconclusivo --nota "oráculo de candidatos K=24: -31%"
   ```
   O veredito é um destes: `melhorou`, `piorou`, `inconclusivo`, `abandonado`, `falhou` ou `controle`.
4. **Concluir o cartão:** escrever a conclusão e a seção "Para o texto do TCC". Se não funcionou, acrescentar uma linha em NAO_FUNCIONOU.md.

## Regras

- **Critérios antes dos números.** Um critério alterado depois de ver o resultado fica registrado no cartão como alteração, com o motivo.
- **Teste cego:** só o orquestrador o avalia, uma vez, com o método congelado.
- **Âncora:** todo experimento novo reproduz a regra no golden_v4 (τ 0,985948 e 6,045455 quebras) antes de reportar qualquer coisa.
- **Números:** todo número de relatório ou cartão sai de um arquivo gerado por script.
