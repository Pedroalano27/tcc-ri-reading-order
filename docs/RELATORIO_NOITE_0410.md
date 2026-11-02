# Noite de 04→05/10/2026: ordenadores sobre a representação sem caixas finas

Pergunta do Pedro: **"testar os ordenadores nesse novo tipo de modelo"**, isto é, com o texto sem caixas finas
(linhas ou faixas de coluna; só tabela e imagem como bloco; margens separadas), qual ordenador erra menos.
Plano: `orquestracao/noite_0410/PLANO.md`. Orquestração: Claude; execução: Codex CLI, Antigravity CLI, GPU local
e API gratuita do Gemini (autorizada pelo Pedro para as 71 páginas do Golden).

## 1. Resposta curta

1. **Em linhas, a regra geométrica de colunas continua na frente de todos os ordenadores treinados.** No
   golden_v4: τ 0,986 e 6,05 quebras por página, contra 0,928 e 11,00 do melhor modelo treinado nesta noite
   (LayoutLM sucessor, 40 épocas; com 100 épocas, 0,929 e 12,57) e 0,913 e 18,39 do LayoutReader pré-treinado.
2. **Treino curto engana.** O mesmo LayoutLM sucessor com 8 épocas dava 57,59 quebras por página; com 40 épocas,
   11,00; com 100, 12,57, sem ganho adicional. BiLSTM e LayoutLM pontual, que ordenam por posição, picotam o texto (72 a 75 quebras por página).
3. **Em faixas de coluna quase não há o que ordenar.** A página tem de 3 a 4 unidades na mediana; as quebras
   ficam entre 5,2 e 6,3 com qualquer ordenador, até o ingênuo, porque o erro que sobra está dentro das faixas.
   Só o τ distingue: os modelos treinados chegam a 0,934, o LayoutReader pronto a 0,923, a regra a 0,854; o teto
   da representação é 0,960, abaixo de linhas com a regra (0,986).
4. **Pista nova: um híbrido por densidade.** O LayoutReader pronto erra menos que a regra nas páginas com poucas
   linhas e desaba nas densas. Usando o LayoutReader até 67 unidades e a regra acima disso (limiar escolhido só
   no golden_v4), as quebras caem de 9,22 para 7,89 por página no golden_v3 novo e de 27,45 para 26,43 no teste
   silver, que não participaram da escolha.
5. **Comparado ao pipeline de hoje** (caixas finas + XY-cut + margens: 0,952 e 8,93 no golden_v4; 0,938 e 11,41
   no golden_v3 novo), linhas com a regra segue melhor nas duas medidas, e o híbrido um pouco melhor ainda em
   quebras.

Tudo isto vale com as ressalvas da seção 5: modelos treinados só com geometria, em 873 páginas, com uma única
execução longa; e sem a revisão adversarial, porque o Codex esgotou a cota da semana.

## 2. O que foi montado

- **Unidades com supervisão** (`orquestracao/analises/unidades_sem_caixas.py`, relatório
  `resultados/unidades_sem_caixas.md`): três representações (`linhas`, `colunas`, `colunas_margens`) no mesmo
  esquema de `data/processed/blocos`, com a ordem de referência por unidade. Referência silver = fluxo do PDF
  por palavra; nas bancadas humanas, a sequência-ouro de palavras de `erros_ponta_a_ponta.py`. Átomos pelo
  detector `ls3`. Nada foi gravado em `data/`.
- **Treino congelado em 873 páginas** (`resultados/unidades_sem_caixas/treino_noite.json`): prefixo de 891 páginas
  de uma ordem embaralhada fixa das 3.217 elegíveis, 8 puladas por recorte deslocado no PDF. A exportação
  completa levaria mais de três horas; cortei para sobrar noite para os treinos. Todos os modelos usam
  exatamente essas páginas.
- **Bancada única** (`orquestracao/analises/bancada_ordenadores.py`, relatório
  `resultados/ordenadores_sem_caixas.md`): qualquer ordenador entrega a ordem das unidades e a bancada mede em
  palavras (τ, quebras por página, trechos de 12 palavras intactos, sucessor de linhas), com as funções de
  `erros_ponta_a_ponta.py`. Âncoras reproduzidas: regra de colunas 0,985948 e 6,045455; extrator + XY-cut +
  margens 0,952424 e 8,931818 (golden_v4).
- **Decisão de bancada (minha, registrada no quadro):** a ordem das palavras *dentro* de cada unidade é sempre
  a expansão canônica do método já medido (`ordem_sem_bbox.fluxo()`); o ordenador decide só a ordem entre
  unidades. Com a ordem interna crua da exportação, a regra dava 16,86 quebras por página em vez de 6,05 (o
  Codex parou na âncora e localizou a causa, quase toda dentro das tabelas).
- **Treinador em fluxo** (`orquestracao/analises/treinar_sem_caixas.py`, do Codex): reaproveita as redes do TCC
  (BiLSTM, LayoutLM pontual e sucessor) e o LayoutReader; um token por unidade, com a caixa da unidade, para
  caber páginas com centenas de linhas no limite de 512 tokens. Ou seja, **os modelos desta noite não leem o
  texto, só a geometria**.

## 3. Resultados

Tabela completa, gerada por script: `resultados/tabela_noite_0410.md`
(`orquestracao/analises/tabela_noite_0410.py`). Cada célula: τ de palavras / quebras por página / trechos de 12
palavras intactos. Bancadas: golden_v4 (44 páginas, usadas no desenvolvimento da regra de colunas), golden_v3
novo (27 páginas, fora do desenvolvimento) e teste silver (89 páginas de CE, MA e RJ, referência automática).

### 3.1 Linhas

| Ordenador | golden_v4 | golden_v3 novo | teste silver |
|---|---:|---:|---:|
| Teto (unidades na ordem de referência) | 1,000 / 0,89 / 99,7% | 1,000 / 0,70 / 99,8% | 0,997 / 17,12 / 89,0% |
| **Regra de colunas** | **0,986 / 6,05 / 94,8%** | **0,960 / 9,22 / 92,8%** | **0,960 / 27,45 / 82,5%** |
| LayoutLM sucessor, 100 épocas | 0,929 / 12,57 / 92,1% | 0,896 / 12,59 / 89,5% | 0,931 / 31,91 / 80,9% |
| LayoutLM sucessor, 40 épocas | 0,928 / 11,00 / 93,2% | 0,919 / 12,48 / 89,4% | 0,914 / 31,92 / 80,5% |
| LayoutReader pré-treinado | 0,913 / 18,39 / 93,5% | 0,951 / 16,22 / 92,8% | 0,942 / 31,25 / 83,0% |
| LayoutReader ajustado (4 épocas) | 0,905 / 21,91 / 90,4% | 0,945 / 20,85 / 89,3% | 0,930 / 36,60 / 80,2% |
| XY-cut + margens | 0,963 / 23,07 / 90,6% | 0,901 / 15,07 / 88,3% | 0,936 / 32,47 / 79,6% |
| XY-cut | 0,806 / 45,57 / 76,2% | 0,805 / 30,07 / 76,0% | 0,806 / 50,44 / 62,9% |
| LayoutLM sucessor, 8 épocas | 0,902 / 57,59 / 61,4% | 0,885 / 57,00 / 63,4% | 0,876 / 89,62 / 50,8% |
| Ingênuo (cima para baixo) | 0,732 / 58,91 / 68,8% | 0,804 / 52,96 / 71,4% | 0,772 / 72,99 / 57,8% |
| LayoutLM sucessor, 8 épocas, semente 43 | 0,887 / 62,75 / 55,8% | 0,879 / 62,41 / 58,2% | 0,862 / 94,35 / 46,8% |
| LayoutLM pontual, 8 épocas | 0,902 / 72,57 / 43,3% | 0,870 / 74,44 / 47,6% | 0,869 / 105,74 / 37,3% |
| BiLSTM geométrico | 0,872 / 75,48 / 40,3% | 0,846 / 75,04 / 46,5% | 0,854 / 107,67 / 35,6% |
| BiLSTM geométrico + texto | 0,850 / 78,14 / 38,2% | 0,818 / 78,04 / 43,7% | 0,812 / 110,62 / 32,8% |

Leituras:
- A representação em linhas quase não custa nada (teto de 0,89 quebra por página no golden_v4): todo o erro é
  do ordenador, e a regra de colunas está a cerca de 5 quebras por página do teto.
- O LayoutReader pré-treinado tem menos quebras que a regra em 24 das 44 páginas do golden_v4 (igual em 6, mais
  em 14) e em 14 das 27 do golden_v3 novo, mas a média é pior porque ele desaba nas páginas densas: no terço
  com mais unidades do golden_v4, 47,27 quebras contra 10,00 da regra; no terço com menos, 1,14 contra 2,07
  (`resultados/ordenadores_ganha_perde.md`, seções A e C).
- Ajustar o LayoutReader nos nossos dados (4 épocas, só as quatro últimas camadas, um token por linha) piorou
  um pouco em todas as bancadas.
- No teste silver o piso é alto (17,12 quebras no teto) porque a referência é o fluxo do PDF por palavra e a
  ordem canônica dentro das tabelas discorda dele; ali vale a comparação entre ordenadores, não o valor absoluto.

### 3.2 Faixas de coluna com margens

| Ordenador | golden_v4 | golden_v3 novo | teste silver |
|---|---:|---:|---:|
| Teto | 0,960 / 5,20 / 95,3% | 0,909 / 8,81 / 92,6% | 0,946 / 25,25 / 83,4% |
| LayoutReader pré-treinado | 0,923 / 5,30 / 95,2% | 0,838 / 8,81 / 92,5% | 0,888 / 25,57 / 83,4% |
| Ingênuo | 0,772 / 5,30 / 95,3% | 0,600 / 9,00 / 92,4% | 0,665 / 27,62 / 82,7% |
| XY-cut | 0,837 / 5,32 / 95,3% | 0,673 / 8,93 / 92,5% | 0,728 / 25,53 / 83,3% |
| XY-cut + margens | 0,854 / 5,34 / 95,2% | 0,809 / 8,93 / 92,5% | 0,866 / 25,53 / 83,3% |
| Regra de colunas | 0,854 / 5,34 / 95,2% | 0,809 / 8,93 / 92,5% | 0,859 / 25,56 / 83,3% |
| Gemini (41 e 25 páginas) | 0,901 / 5,37 / 95,2% | 0,759 / 9,44 / 92,0% | — |
| LayoutLM sucessor, semente 43 | 0,936 / 5,86 / 94,9% | 0,866 / 9,00 / 92,5% | 0,902 / 31,96 / 80,4% |
| LayoutLM sucessor | 0,934 / 5,98 / 94,8% | 0,867 / 8,96 / 92,5% | 0,903 / 32,18 / 80,4% |
| BiLSTM geométrico | 0,934 / 6,25 / 94,7% | 0,833 / 9,15 / 92,3% | 0,907 / 32,24 / 80,3% |

Leituras:
- Com faixas, a página tem de 3 a 4 unidades na mediana (`resultados/unidades_sem_caixas.md`). A ordem entre
  elas muda pouco as quebras; o piso interno (quebras que nenhuma ordem conserta) é de 3,95 por página no
  golden_v4 e 6,81 no golden_v3 novo. O defeito está na formação das faixas, não no ordenador.
- No τ os modelos treinados ordenam as faixas melhor que a regra (0,934 contra 0,854 no golden_v4; 0,867 contra
  0,809 no golden_v3 novo), mas o teto dessa representação (0,960 e 0,909) fica abaixo de linhas com a regra
  (0,986 e 0,960).
- O Gemini, nas mesmas páginas que ele cobriu, não supera o LayoutReader pronto nem o LayoutLM sucessor
  (`resultados/ordenadores_ganha_perde.md`, seção D: 0,901 contra 0,919 e 0,931 no golden_v4; 0,759 contra
  0,827 e 0,858 no golden_v3 novo). Sete das 142 respostas não eram permutações válidas e ficaram de fora.
- As duas sementes do sucessor em faixas dão o mesmo resultado (0,934 e 0,936).

### 3.3 Híbrido por densidade (pista, não método validado)

`resultados/hibrido_regra_layoutreader.md` (`orquestracao/analises/hibrido_regra_layoutreader.py`): LayoutReader
pré-treinado quando a página tem até 67 unidades, regra de colunas acima disso. O limiar foi escolhido só no
golden_v4.

| Bancada | Regra: τ / quebras | Híbrido: τ / quebras | Δ quebras [IC 95% por veículo] | Híbrido melhor / igual / pior |
|---|---:|---:|---:|---:|
| golden_v4 (escolha do limiar) | 0,986 / 6,05 | 0,980 / 5,14 | −0,91 [−1,78; −0,10] | 16 / 24 / 4 |
| golden_v3 novo | 0,960 / 9,22 | 0,959 / 7,89 | −1,33 [−2,63; −0,35] | 7 / 18 / 2 |
| teste silver | 0,960 / 27,45 | 0,959 / 26,43 | −1,02 [−1,89; −0,08] | 14 / 72 / 3 |

O ganho é pequeno, mas aparece nas três bancadas e o τ quase não muda. Falta testar com um limiar escolhido por
validação cruzada e em mais páginas humanas.

### 3.4 Treino longo do LayoutLM sucessor em linhas

| Épocas | Tempo de treino | Melhor τ de validação (15 páginas de RN) | golden_v4: τ / quebras | golden_v3 novo: τ / quebras |
|---:|---:|---:|---:|---:|
| 8 | 12 min | 0,869 | 0,902 / 57,59 | 0,885 / 57,00 |
| 40 | 66 min | 0,935 | 0,928 / 11,00 | 0,919 / 12,48 |
| 100 | 156 min | 0,932 | 0,929 / 12,57 | 0,896 / 12,59 |

De 8 para 40 épocas o ganho é enorme; de 40 para 100 não há ganho. Com estas 873 páginas e este desenho (um
token por linha, só geometria), o sucessor estaciona em 11 a 13 quebras por página, cerca do dobro da regra no
golden_v4. Contra a regra, a versão de 100 épocas tem menos quebras em 14 páginas do golden_v4, igual em 12 e
mais em 18 (`resultados/ordenadores_ganha_perde.md`, seção A). O que falta testar é mais dado e texto, não
mais épocas.

## 4. O que cada agente fez

- **Codex** (até esgotar a cota): exportação das unidades e âncoras (26 min); bancada, que parou corretamente
  quando a âncora não fechou (22 min); bancada corrigida com as tabelas dos ordenadores sem treino (62 min);
  treinador em fluxo e quatro BiLSTM em CPU (41 min, interrompido pelo limite). Limite de uso às 02:20 e, a
  partir das 04:07, **limite semanal até 09/10 às 19:06**.
- **Antigravity**: auditoria de vazamento (`resultados/auditoria_bancadas_treino.md`: 6 páginas do golden_v4
  estavam no inventário de treino e foram excluídas; 5 das 44 páginas do golden_v4 são de veículos de treino);
  diagnóstico das faixas estreitas (`resultados/faixas_estreitas.md`: 13 de 614 páginas, 0,58% das palavras,
  concentrado em PE, SC e PR); cola do Gemini; análise página a página (`resultados/ordenadores_ganha_perde.md`).
- **Claude**: plano, revisão de cada entrega, exportação do treino, decisão da ordem interna, roteiros de GPU
  depois da queda do Codex, Gemini, tabela-resumo, híbrido por densidade e este relatório.
- **GPU**: oito treinos concluídos (o último terminou às 07:32); uma falha (LayoutReader com uma opção de memória que o
  modelo não aceita), corrigida e refeita.

Falhas de operação e correções: a exportação do treino caiu duas vezes (o Windows não troca arquivo que outro
processo está lendo; uma página de PDF com recorte deslocado abortava tudo) e foi corrigida para não regravar
arquivo igual e para pular e registrar página de treino assim. Nenhuma queda de máquina; memória entre 53% e
69% de commit.

## 5. Ressalvas

1. **Só geometria.** Um token por unidade: os LayoutLM e o LayoutReader desta noite não usam o texto. O achado
   de 13/09 (o sucessor sem texto não piora) vale para blocos; em linhas não foi testado.
2. **873 páginas de treino**, contra 3.235 do melhor modelo anterior. A curva de aprendizado antiga dava cerca
   de +0,03 de τ a cada dobra de dados.
3. **Uma semente nas execuções longas.** As versões de 8 épocas variam de 57,59 a 62,75 quebras entre
   sementes; as de 40 e de 100 épocas têm uma semente cada. A validação tem 15 páginas e oscila (0,87 a 0,93 nas últimas épocas).
4. **golden_v4 foi usado para desenvolver a regra de colunas**, o que a favorece ali. Por isso o golden_v3 novo
   e o teste silver estão sempre ao lado; neles a ordem dos métodos é a mesma.
5. **Referências derivadas.** Nas bancadas humanas, a ordem das palavras vem da ordem humana das regiões com
   ordem geométrica interna; no silver, do fluxo do PDF.
6. **Sem revisão adversarial.** Estavam pedidos ao Codex e não foram feitos: acerto de sucessor por tipo de
   transição (mesma coluna, troca de coluna, entrada e saída de tabela), comparação das decodificações (gulosa,
   feixe, cadeias) no mesmo checkpoint, ruído do rótulo por mediana e efeito de retirar as páginas com tabela.
7. **Gemini com cobertura parcial** (41 de 44 e 25 de 27 páginas em faixas com margens).

## 6. Decisões e próximos passos para o Pedro

1. **Representação de trabalho:** os números apontam para linhas + átomos como base (teto quase perfeito) e não
   para faixas de coluna como unidade indivisível (teto de τ 0,96 e piso de 4 a 7 quebras por página). As faixas
   continuam úteis para visualizar.
2. **Ordenador:** manter a regra de colunas como método e tratar os modelos como complemento. Vale testar o
   híbrido por densidade com validação cruzada.
3. **Treino de verdade do sucessor em linhas:** exportar as 3.217 páginas (a exportação é retomável e o cache das
   873 está pronto: `venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 0`,
   de 2h30 a 3h30 de CPU pelo ritmo desta noite) e treinar 40 épocas (mais que isso não ajudou), com duas ou três sementes. Cabe numa noite da GPU local
   ou no Kaggle.
4. **Pendências do Codex** (seção 5, item 6) ficam para quando a cota voltar, em 09/10, ou para outra ferramenta.
5. Nada foi enviado ao professor nem publicado; sem commit nem push.

## 7. Noite de 06→07/10 (complemento)

- **Exportação completa do treino:** 3.140 páginas nas três representações (43 puladas por recorte deslocado),
  contagens em `resultados/unidades_sem_caixas/treino_noite.json`; o conjunto de 873 páginas da noite anterior
  ficou em `treino_noite_873.json`. Terminou às 05:00.
- **Modelos com todo o dado: não saíram.** A GPU esteve ocupada por outro programa das 23:40 até pelo menos 07:56
  (4 a 6 GB em uso). A cadeia `orquestracao/noite_0610/rodar.sh` continua esperando a placa livre para treinar o
  LayoutLM sucessor em linhas (sementes 42 e 43, 20 épocas) e medir nas bancadas; para parar, criar
  `orquestracao/noite_0610/STOP`.
- **XY-Cut++ do projeto parceiro na nossa bancada** (`orquestracao/analises/xycut_pp_parceiro.py`, importando do
  clone local, sem copiar código; parâmetros padrão deles), τ de palavras / quebras por página, golden_v4 e
  golden_v3 novo: em linhas 0,763 / 48,20 e 0,805 / 47,85 (regra de colunas: 0,986 / 6,05 e 0,960 / 9,22); em
  faixas com margens 0,857 / 5,52 e 0,730 / 9,00 (regra: 0,854 / 5,34 e 0,809 / 8,93). Os limiares padrão são
  para blocos de parágrafo em pixels e não foram ajustados para linhas em pontos de PDF: não é veredito sobre o
  algoritmo.
- **Repositórios do CEIA-Datapolicy** (clones só de leitura em `C:\Users\pedro\dev\ceia_datapolicy`, fora do
  projeto): síntese em `resultados/ceia_datapolicy/SINTESE.md` (pasta fora do git; uso interno). O mais útil é o
  ramo `feature/wilker/xycut_pp` de `Benchmark-LayoutAnalysis`, com XY-Cut++ em Python e serviços de ordem e de
  medição de ordem, e o repositório `Benchmark`, com a régua oficial de detecção do projeto.
- **Painéis das reclamações do Pedro** (`resultados/reclamacoes_x_novo/`, 28 páginas com nota nos Golden): as
  reclamações de tabela e de caixa que pula de coluna melhoram; logo e título como imagem não; aparecem defeitos
  novos (colunas não separadas, sobreposição de tabela com faixa de texto, lista classificada como tabela). Só 8
  dos 28 painéis foram examinados.

## 8. Noite de 07→08/10 (rascunho escrito às 05:20; números da semente 43 entram no fim)

Pedido do Pedro: melhorar o extrator novo sem parágrafos, achar erros e inconsistências, criar um lote classificável,
treinar o LayoutLM nessa estrutura, achar uma forma de anotar mais simples que o Label Studio e usar o ChatGPT para
ideias. Orquestração do Claude (Sonnet 5.5), Codex e Antigravity; o PC reiniciou duas vezes (21:01 e 23:14), o que
parou o treino da noite anterior; retomado do checkpoint.

### 8.1 Extrator novo sem parágrafos
- **Auditoria** (`resultados/auditoria_extrator_sem_paragrafos.md`, Antigravity): 32,1% das 614 páginas têm defeito
  grave; os mais frequentes são tabela suspeita (20,0%), linha com altura anômala (16,8%) e sobreposição tabela x texto
  (8,0%); concentrados em am_manaus, RJ_duque_de_caxias, RJ_seropedica e ba_salvador.
- **Extrator v2** (`resultados/extrator_sem_paragrafos_v2.md`, Codex): calhas locais com suporte, linhas vetoriais do
  PDF, tabela x lista, fusão de cabeçalhos. **Efeito praticamente nulo em linhas**: golden_v4 6,05 → 5,93 quebras por
  página; golden_v3 novo 9,22 inalterado. Em faixas de coluna melhora pouco. Conclusão: em linhas só 0,55 quebra por
  página nasce nas caixas; a extração está perto do teto e o erro que resta é de ordenação.
- **Lote classificável** de 60 páginas (30 piores pela auditoria e 30 aleatórias; sem páginas dos Golden):
  `data/diamond/lote_sem_paragrafos` (`resultados/lote_sem_paragrafos/LEIAME.md`). Abrir:
  `venv\Scripts\python.exe src\anotacao\servidor.py --diamond`, `http://127.0.0.1:8770/diamond`, lote `lote_sem_paragrafos`.

### 8.2 Onde a regra de colunas erra (golden_v4, 44 páginas)
Diagnóstico por tipo de transição (`resultados/corretor_de_transicoes.md`, Codex): **50,4% das quebras estão em
cabeçalho, rodapé e marcas marginais** (213 transições, 61,5% erradas); elemento transversal 69% de erro mas só 6,8% das
quebras; continuação na mesma coluna 1,5% de erro e 20% das quebras. No golden_v3 novo: continuação 40% e margens 16%.
Recall dos candidatos de sucessor: 96 a 98%.

### 8.3 Tentativas de melhorar a regra (todas medidas fora da amostra de ajuste)
| Variante | golden_v4 (ajuste) | golden_v3 novo | teste silver | Leitura |
|---|---|---|---|---|
| Regra original | 6,05 | 9,22 | 27,45 | referência (quebras por página) |
| Margens (Codex 06) | menos | −0,48 [IC inclui 0] | −0,68 [IC inclui 0] | pequeno, não conclusivo |
| Margens por repetição entre páginas (Codex 07) | 4,89 | +1,00 (pior) | −0,03 | **não generaliza** (sobreajuste) |
| Reordenação restrita na coluna (Codex 08) | 5,18 | 7,78 | 26,45 | melhora nas três, IC externo inclui 0; teto do oráculo −42,6% |
| Regra + modelo textual seletivo (Codex 09) | +0,86 (pior) | +1,37 (pior) | +2,01 (pior) | **conservar a regra** |
| Corretor MLP com 24 páginas (Codex 05) | — | — | — | sem ganho (amostra minúscula) |

Painéis da reordenação restrita (`resultados/reordenacao_restrita/PAINEIS.md`): a maior "melhora" do golden_v3 novo
(ma, suplemento: 92 → 72 quebras) é uma página de lista tabular (nome, situação) com τ 0,69 em que a variante troca a
ordem de células da mesma linha; a referência ali é derivada, então esse ganho não prova melhora geral dentro de
colunas de texto corrido.

### 8.4 Modelos aprendidos sobre linhas (τ / quebras por página; golden_v4 | golden_v3 novo | teste silver)
- Regra de colunas: 0,986/6,05 | 0,960/9,22 | 0,960/27,45.
- LayoutLM sucessor, geometria, **873 páginas**, 40 épocas: 0,928/11,00 | 0,919/12,48 | 0,914/31,92.
- LayoutLM sucessor, geometria, **3.140 páginas** (todo o treino), 20 épocas, semente 42: 0,924/9,00 | 0,928/10,41 |
  0,934/29,15. **Mais dado ajudou**, e o modelo chega perto da regra, mas ainda fica atrás.
- LayoutLM sucessor **lendo o texto** das linhas (K tokens por linha), 3.140 páginas, 20 épocas, semente 42:
  0,942/20,77 | 0,931/23,19 | 0,930/50,46. **Ler o texto não ajuda**: τ um pouco maior no golden_v4 mas as quebras mais
  que dobram (a ordem global melhora e a continuidade local piora).

### 8.5 Variância entre sementes do modelo com todo o dado (τ / quebras por página)
| Semente | golden_v4 | golden_v3 novo | teste silver |
|---|---|---|---|
| 42 | 0,924 / 9,00 | 0,928 / 10,41 | 0,934 / 29,15 |
| 43 | 0,945 / 8,68 | 0,923 / 10,81 | 0,934 / 29,63 |
| Regra de colunas (determinística) | 0,986 / 6,05 | 0,960 / 9,22 | 0,960 / 27,45 |

Duas sementes só, então é uma estimativa grosseira: o modelo varia de 0,3 a 0,5 quebra por página entre sementes (τ até
0,02 no golden_v4). A diferença para a regra (3,0 quebras no golden_v4, 1,4 a 1,6 no golden_v3 novo, cerca de 2 no
silver) é maior que essa variação nas três bancadas, então o modelo ainda perde para a regra de forma consistente. Por
outro lado, ganhos de 0,5 a 1,4 quebra por página das variantes de regra da seção 8.3 têm o mesmo tamanho do ruído de
amostra: só a reordenação restrita melhora nas três bancadas, e ainda sem confirmação estatística.

### 8.6 Pendências e o que testar de manhã
1. **Lote classificável:** abrir no servidor Diamond e corrigir cerca de 10 páginas, medindo o tempo por página
   (`venv\Scripts\python.exe src\anotacao\servidor.py --diamond`, `http://127.0.0.1:8770/diamond`, lote `lote_sem_paragrafos`).
2. **Classificador simples** (`resultados/ferramenta_anotacao/classificador.html`): testar com o mouse (desenhar, arrastar
   bordas, dividir, ordem); no navegador embutido carregaram o exemplo, a tecla de classe, o desfazer e a exportação
   para o Label Studio (rectanglelabels, relation, textarea) e o teste de ida e volta em Python passou.
3. **LAREX:** comparar com o classificador em 10 páginas do lote (`resultados/ferramenta_anotacao/COMPARACAO_LAREX.md`);
   o conversor PAGE XML está em `resultados/ferramenta_anotacao/conversor_page_xml.py`.
4. **Kaggle:** se rodou `notebooks/kaggle_detector_ls.ipynb` (dois DocLayout-YOLO), baixar `saida_ls.zip` e importar com
   `src/kaggle/importar_resultados.py` (ver `docs/KAGGLE.md`).
5. Os modelos aprendidos ainda perdem para a regra de colunas; as variantes de regra que melhoram o golden_v4 não
   generalizam; a reordenação restrita é a mais consistente, mas exploratória e com IC externo que inclui zero.
6. Resumo para o professor ainda sem estes números; os 71 páginas anotadas continuam sendo o limite de tudo.

### 8.7 O que deu errado e o que errei
- A `comum.txt` de `noite_0710` proibiu comandos também para o Codex (a regra era para o Antigravity): as tarefas 02 e 03
  só escreveram scripts, sem executar. Corrigido com as tarefas 04 e 05 (executar e validar).
- O treino com texto falhou duas vezes: uma página com 509 linhas não cabia nos 510 tokens com CLS e SEP, e depois a
  trava de integridade do treinador recusou retomar com o código alterado. Corrigido com um limite de 508 unidades na
  compactação e pasta nova (as tentativas falhas ficaram arquivadas).
- A cota do Codex acabou duas vezes (a segunda às 03:49) e a fila retomou sozinha.
- O PC reiniciou às 21:01 sem desligar direito (o treino da noite anterior parou na época 4 e foi retomado do
  checkpoint) e às 23:14 por Windows Update.
- Eu disse ao Pedro que a cota do Codex tinha voltado definitivamente; ele corrigiu que ela existe e que ele a zerou.
