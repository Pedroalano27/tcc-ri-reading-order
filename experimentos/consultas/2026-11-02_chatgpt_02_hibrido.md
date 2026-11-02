# Consulta 02 ao ChatGPT — o híbrido por densidade muda a prioridade? (02/11/2026)

- **Conversa:** a mesma da consulta 01 (https://chatgpt.com/c/6ae8d81e-3ce0-83e9-a114-20b580d695e7)
- **Pergunta, em resumo:** informei o híbrido por densidade (LayoutReader pronto em páginas com até 67 unidades, regra nas densas):
  - quebras por página 5,14 | 7,89 | 26,43;
  - Δ −0,91 [−1,78; −0,10] | −1,33 [−2,63; −0,35] | −1,02 [−1,89; −0,08];
  - limiar escolhido no golden_v4.

  Também informei o lote de 60 páginas não anotadas. Perguntei:
  1. se isso muda a prioridade;
  2. se o seletor deve ser aprendido;
  3. se o lote serve como teste cego.

## Resposta, em resumo

1. **Muda, sim.**
   - O híbrido passa a ser o **baseline principal a superar**, e a regra fica como controle.
   - **P0:** oráculo de **roteamento por página** (regra × LayoutReader × grafo) + oráculo do grafo.
   - **P1:** grafo de arestas e seletor adaptativo, como frentes paralelas.
   - O grafo não precisa vencer em todas as páginas: já vale se melhorar o híbrido nas páginas difíceis.
   - A hipótese central passa a ser **especialização de método por tipo de página**.
2. **Seletor:** não treinar um classificador complexo com 44 páginas, porque há muitos empates (24/44) e o rótulo de vencedor é instável.
   - Manter o limiar 67 **congelado** como baseline.
   - Testar um seletor simples a partir de densidade, número de colunas, proporção de margens e elementos transversais.
   - Usar validação cruzada agrupada por veículo/PDF e decidir pelo ganho esperado, penalizando erros graves.
   - Comparar contra o limiar 67, não só contra a regra. Se não superar fora da amostra, manter o seletor fixo.
3. **Usar as 60 páginas como teste cego**, *desde que* a seleção tenha sido independente dos métodos e **não haja PDFs em comum com o treino**. Se incluírem veículos de treino, elas medem generalização para PDFs novos, não para veículos novos; 30 páginas adicionais de CE/MA/RJ fortaleceriam a avaliação externa.

## Verificação feita pelo Claude depois da resposta

A condição do item 3 **não se cumpre**:
- **todos os 57 PDFs** do lote já aparecem em outros conjuntos de tarefas (principalmente `diamond_massa1`; 5 também nos goldens);
- **23 das 60 páginas** estão nos dados exportados em linhas (treino silver ou bancadas).

**Decisão:** o lote vira material de **desenvolvimento** (anotação cruzada, experimento de anotação). O teste cego é montado do zero, com PDFs nunca tocados: CE, MA e RJ, mais veículos fora do treino. Ver o E001 no [plano](../../docs/PLANO_PESQUISA.md).
