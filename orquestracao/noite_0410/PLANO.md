# Plano da noite de 04→05/10: ordenadores sobre a representação sem caixas finas

**Pergunta (palavras do Pedro):** "testar os ordenadores nesse novo tipo de modelo".
O novo tipo é a representação sem caixas finas (texto em linhas ou faixas de coluna; só tabela e imagem como
bloco; cabeçalho, rodapé e quadros separados). Até agora só a regra geométrica e o LayoutReader pronto foram
medidos nela. Falta medir os ordenadores do TCC: XY-cut, BiLSTM, LayoutLM pontual e sucessor, LayoutReader
ajustado e, se autorizado, o Gemini.

**Resposta esperada de manhã:** uma tabela única, na régua de palavras de `resultados/erros_ponta_a_ponta.md`
(τ, quebras por página, fidelidade de 12), com cada ordenador em cada representação, em três bancadas
(golden_v4, golden_v3 novo, teste silver), ao lado do pipeline atual com caixas finas.

## O que torna isso viável em uma noite

- Supervisão já existe: a referência silver do protocolo (ordem do fluxo do PDF) em 3.223 páginas de treino
  (152 da base e 3.071 extras, 7 veículos), validação em RN e teste em CE, MA e RJ. Os PDFs estão em `data/raw/`.
- Os treinadores leem a pasta de `TCC_DIR_BLOCOS`. Exportando as unidades novas no esquema de
  `data/processed/blocos`, BiLSTM e LayoutLM rodam sem mudar de código.
- A bancada de avaliação reaproveita as funções de `orquestracao/analises/erros_ponta_a_ponta.py`.

## Etapas

| # | Quem | O quê | Depende de | Saída |
|---|---|---|---|---|
| 1 | Codex `01` | Exportar as unidades (linhas, colunas, colunas com margens) com ordem de referência por unidade, no esquema de blocos | — | `resultados/unidades_sem_caixas.md` |
| 2 | Antigravity `01` | Auditoria de vazamento entre treino e bancadas | — | `resultados/auditoria_bancadas_treino.md` |
| 3 | Antigravity `02` | Diagnóstico das faixas estreitas e cabeçalhos fragmentados | — | `resultados/faixas_estreitas.md` |
| 4 | Claude | Revisar a etapa 1 e rodar a exportação completa do treino em CPU | 1, 2 | `resultados/unidades_sem_caixas/treino_noite.json` (amostra fixa de 1.500 páginas, por tempo) |
| 5 | Codex `02` | Bancada única + ordenadores sem treino (teto, ingênuo, XY-cut, XY-cut com margens, regra de colunas, LayoutReader pronto) | 1 | `resultados/ordenadores_sem_caixas.md` |
| 6 | Codex `03` | BiLSTM em CPU; roteiros de GPU para LayoutLM sucessor, pontual e LayoutReader ajustado | 4, 5 | `resultados/ordenadores_treinados_sem_caixas.md` |
| 7 | Fila da GPU | Treinar os roteiros, um por vez, quando a placa liberar | 6 | linhas novas na tabela da etapa 5 |
| 8 | Claude | Gemini ordenando as faixas das 71 páginas do Golden (só com autorização) | 5 | idem |
| 9 | Codex `04` (a escrever) | Revisão adversarial e análise de erros por tipo de página | 7 | relatório final |
| 10 | Claude | `docs/RELATORIO_NOITE_0410.md` e entrada no quadro | tudo | — |

## Restrições desta noite

- **GPU:** às 23:06 estava ocupada pelo `vlm_infer.py` de outro trabalho do Pedro (5,5 GB, 99%); às 23:15 já
  estava livre (0,5 GB). A fila da GPU só começa com a memória da placa abaixo de 1,1 GB e nunca mexe em
  processo que não seja dela.
- **Memória:** 0,9 GB de RAM livre e commit em 79% às 23:10; 3,0 GB e 59% às 23:15, depois que o outro trabalho
  terminou. Um processo pesado por vez; sem workers.
- **Codex** tem limite de uso; a ordem das tarefas põe o essencial primeiro. Se ele parar, o Claude assume.
- Sem commit, push ou publicação. `data/labelstudio/` fica fora desta noite (só os pesos do detector `ls3`).
- Treinar com a referência silver nas unidades novas é experimento, registrado como DECISÃO no quadro ao lançar.

## Para lançar

```bash
bash orquestracao/noite_0410/iniciar.sh
```

Acompanhar: `bash orquestracao/noite_0410/status.sh`. Parar: criar `orquestracao/noite_0410/STOP`.
