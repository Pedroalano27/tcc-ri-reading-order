## Contexto

Revisão do Claude sobre a sua T37b (`src/eval/relatorio_v4.py` → `docs/RELATORIO_V4.md` e
`notebooks/relatorio_ordem_v4.ipynb`). As tabelas estão corretas; faltam ajustes de rótulo e de texto onde
a afirmação não bate com os números. Altere só esses três arquivos (o `.md` continua gerado pelo script).
Sem GPU, rede ou alteração de dados.

## Correções

1. **Rótulo errado de `aleatoria`:** não é "Ordem do detector (sem ordenar)". É a permutação
   embaralhada com semente por página (`src/eval/protocolo.py::ordem_entrada`) em que os blocos chegam aos
   métodos. Renomeie para "Aleatória (ordem de entrada embaralhada)" em `NOMES` e onde mais aparecer.
2. **Seção 1, item 5:** p = 0,183 e p = 0,077 são os p **brutos**. Escreva os ajustados por Holm (1,00 e
   0,92, da tabela da seção 3) ou diga explicitamente "p bruto".
3. **Seção 1, item 7:** a queda de τ das LLMs nas 20 páginas não é significativa (p = 0,121): diga isso.
4. **Familiaridade (seções 1, 9.1 e 11):** os números mostram o contrário do texto: mediana de 17,0 s nas
   20 páginas já vistas e 15,0 s nas 24 novas. Tire "reduziu o esforço de leitura" e "resultou em". Escreva
   só que as medianas foram 17,0 s (já vistas) e 15,0 s (novas), sem efeito aparente de familiaridade
   nesta amostra. Em 9.1 e na seção 1, diga que ordenar e retificar caixas são tarefas diferentes antes de
   comparar os tempos ("4 a 6 vezes") e troque "expressivamente menor" por "menor".
5. **Seção 6.1, itens 1 a 4:**
   - item 1: o VLM não recebe "recortes"; recebe a página inteira com as marcas desenhadas. Troque por
     "a mesma imagem com marcas e as mesmas coordenadas e textos, sem a classe".
   - item 2: tire "com alta fidelidade" e troque "confirmando que o modelo não depende" por "indicando
     que o desempenho não depende".
   - item 3: troque o título "Decisividade das marcas" e as frases "elemento crítico" e "caiu
     drasticamente" por números. Calcule no script o Wilcoxon pareado de τ entre "com marcas e classes" e
     "sem marcas, com classes" (as mesmas 44 páginas; o Claude obteve p = 0,0087) e escreva: τ 0,962 → 0,942
     (p = …), sucessor 94,4% → 90,3%, permutações válidas 38 → 30 de 44. Diga que sem marcas o VLM ainda
     supera a XY-cut após Holm.
   - item 4: a comparação com as LLMs de texto mistura duas coisas (modalidade e família/tamanho de
     modelo), então não permite atribuir a diferença à "integração multimodal". Tire "é, portanto, o
     mecanismo primário de desambiguação" e diga que o desenho não separa o efeito da imagem do efeito do
     modelo; a comparação isolada da imagem seria rodar o mesmo Gemini só com texto.
6. **Seção 5:** a coluna "Melhor LLM disponível" escolhe a melhor das 4 LLMs **em cada estrato**, o que
   favorece as LLMs. Troque por uma LLM fixa, a melhor no geral (Qwen 3.8 27B few-shot 2), e ponha o nome
   no cabeçalho.
7. **Seção 7, observação:** tire "pois a correlação macroscópica de postos continua consistente" e
   "revelando que". A queda de −10,1 pp da semente 42 tem p = 0,055 (não significativa); as sementes 1 e 2
   têm p bruto 0,037 e 0,028 sem correção. Diga que a queda é compatível com sensibilidade do sucessor ao
   corte das caixas, lembrando que a referência também foi reanotada (limitação 3).
8. **Seção 10, nova limitação:** o `golden_v4` usa segmentação corrigida à mão, então os resultados
   medem a ordenação com segmentação ideal, não o pipeline automático completo. Outra: o VLM é uma API
   fechada no nível gratuito (versão do modelo pode mudar; reprodutibilidade limitada).
9. **Seção 11:**
   - item 1: "deve restabelecer" → "hipótese a testar: …".
   - item 3: tire "Padronizar marcas visuais em interfaces de VLM" e "confirmando que modelos
     multimodais … dependem"; um modelo só não generaliza. Reescreva como: manter as marcas no protocolo
     do VLM, com os números do item 5.3 acima.
   - item 4: a comparação do piloto está errada (0,788 é a `proposta` em 20 páginas; 0,857 é
     `regioes_v3+rose` em 19 páginas, dentro da amostra). Use `regioes` (0,848) vs
     `regioes_v3+rose:assinatura_cabecalho` (0,857) no piloto, e 0,793 → 0,800 no treino (25 páginas). Diga
     que o ganho é de cerca de 0,01 no F1 com classe e não foi testado estatisticamente.

Rode `venv\Scripts\python.exe src\eval\relatorio_v4.py`, confira que o notebook executa como antes e cole
na resposta as seções 1, 6.1, 9.1 e 11 novas.
