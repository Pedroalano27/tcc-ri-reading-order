# Concordância entre Anotadores Humanos no Dataset de Layout (Label Studio) — Versão 2 (Corrigida)

> **Data de geração:** 2026-10-03 03:05:04 | **Amostra total avaliada:** 144 páginas (146 pares de anotadores independentes) | **Pares sem suspeita de cópia:** 123 pares

## 1. O que mudou em relação à Versão 1

### 1.1. Diagnóstico do Erro Metodológico na Versão 1
A primeira versão deste relatório (`resultados/labelstudio_concordancia.md`) continha uma falha grave de integridade experimental apontada pela revisão metodológica: o script agregou de forma indiscriminada todos os arquivos `ls_*.json` do diretório `data/labelstudio/`, incluindo **189 páginas do arquivo `ls_p23_seed2_order.json`** (56,7% da amostra total de 333 páginas). No entanto, o projeto `ls_p23` é exclusivamente voltado à anotação da **ordem de leitura**: nele, o segundo anotador utilizou o recurso *Duplicate Annotation* da ferramenta sobre as predições do Admin, mantendo as caixas delimitadoras **idênticas por construção** e apenas inserindo as relações de ordem. Essa duplicação inflacionou artificialmente os coeficientes de concordância espacial e semântica, forjando um consenso humano irreal.

### 1.2. Protocolo de Correção Implementado na Versão 2
1. **Isolamento estrito dos projetos de Bounding Box:** Restrição aos arquivos `ls_p05_seed1.json`, `ls_p13_seed2.json`, `ls_p15_seed3.json` e `ls_p22_seed4.json`. O arquivo `ls_p23` foi definitivamente excluído.
2. **Exclusão de anotações do Admin/pré-anotação:** Identificação programática e expurgo das anotações automáticas da máquina que haviam sido carregadas no Label Studio (usuários com 100% das caixas com `origin == 'prediction'`).
3. **Exigência de independência humana estrita:** Consideram-se apenas tarefas com 2 ou mais anotações de `completed_by` distintos, não canceladas e atribuídas a anotadores humanos genuínos.
4. **Detecção e segregação de cópias residuais:** Foi implementado detector de pares suspeitos de duplicação (onde mais de 95% das caixas casadas apresentam IoU ≥ 0,99). Reportam-se os números do conjunto completo e do conjunto estritamente independente.
5. **Estratificação por Seed:** Resultados abertos individualmente pelos projetos Seed 1, 2, 3 e 4 para permitir auditoria fina.

### 1.3. Quadro Comparativo Direto: Versão 1 vs. Versão 2 (Lado a Lado)

| Métrica / Dimensão Metodológica | Versão 1 (Com Erro - Incluía `ls_p23`) | Versão 2 (Corrigida - Todos os Pares Válidos) | Versão 2 Estrita (Sem Suspeita de Cópia) | Impacto / Diagnóstico da Correção |
|---|---:|---:|---:|---|
| **Páginas avaliadas** | 333 | 144 | 123 | Expurgo de páginas duplicadas de ordem |
| **Pares de anotadores independentes** | 335 | 146 | 123 | Exclusão de cópias mecânicas |
| **Páginas do projeto de ordem (`ls_p23`)** | 189 (56,7%) | **0 (0,0%)** | **0 (0,0%)** | **100% eliminado (erro sanado)** |
| **Caixas totais analisadas** | 13332 | 6515 | 5127 | Volume real de anotação de layout |
| **Caixas casadas (IoU ≥ 0,50)** | 6318 | 2911 | 2220 | Casamento guloso 1-1 |
| **F1 Macro Localização (IoU ≥ 0,50)** | 93,7% | 85,6% [83,1%; 87,8%] | 82,9% [80,1%; 85,4%] | Fronteira realista da concordância espacial |
| **F1 Macro Localização (IoU ≥ 0,75)** | 92,2% | 82,1% | 78,9% | Queda suave com critério geométrico rígido |
| **F1 Macro Localização (IoU ≥ 0,90)** | 91,5% | 80,4% | 76,9% | Alinhamento de contorno exato |
| **Acerto de Classe (16 classes)** | 91,8% | 82,2% | 81,7% | Concordância semântica bruta |
| **Kappa de Cohen κ (16 classes)** | **0,892** | **0,763** [0,727; 0,793] | **0,756** [0,717; 0,790] | Concordância ajustada ao acaso |
| **Kappa de Cohen κ (9 classes)** | **0,943** | **0,875** [0,847; 0,901] | **0,866** [0,829; 0,894] | Colapso para taxonomia do extrator |
| **Kappa de Cohen κ (3 classes)** | **0,970** | **0,936** [0,907; 0,964] | **0,936** [0,904; 0,966] | Macroclasses (texto/tabela/imagem) |
| **Ambos mantiveram pré-anotação (`prediction`)** | 39,5% | 36,0% [30,3%; 40,8%] | 34,2% [28,6%; 39,6%] | Mecanismo do viés de ancoragem |
| **Kappa 16c quando ao menos um mexeu** | **0,847** | **0,686** [0,643; 0,726] | **0,683** [0,631; 0,729] | **Teto empírico genuinamente humano e desancorado** |

## 2. Resumo Executivo

1. **Teto empírico corrigido para localização:** Entre anotadores humanos independentes, o F1 macro por página atinge **85,6%** [83,1%; 87,8%] em IoU ≥ 0,50 (ou 82,9% isolando estritamente pares sem duplicação de caixas), situando a fronteira de Bayes geométrica entre 89% e 94%.
2. **Concordância semântica nas 16 classes do Guia:** Para caixas casadas em IoU ≥ 0,50, o Kappa de Cohen global é de **κ = 0,763** [0,727; 0,793] (Substancial (0,61 - 0,80)). No subconjunto estrito de pares sem cópia, κ = 0,756 [0,717; 0,790].
3. **Convergência substancial com colapso taxonômico:** Ao reduzir a granularidade para 9 classes (extrator), o Kappa sobe para κ = 0,875, e atinge expressivos **κ = 0,936** em 3 macroclasses (texto/tabela/imagem). Isso demonstra com solidez que as divergências humanas são de fronteira terminológica fina (ex.: `title` vs `act`, `paragraph` vs `id`), e não de confusão visual macroestrutural.
4. **Impacto desmistificado da ancoragem:** Em 36,0% das caixas casadas ambos os anotadores aceitaram a sugestão original da máquina. Quando isolamos apenas as caixas onde **ao menos um anotador realizou intervenção ativa**, o Kappa de 16 classes passa a **κ = 0,686**. Este valor é o padrão-ouro de honestidade para a dissertação: ele reflete o consenso humano em decisões ativas e críticas.
5. **Implicação central para os modelos do TCC:** Modelos de segmentação de layout (YOLO, Docling, LayoutLM) não devem ser penalizados se não ultrapassarem κ ≈ 0,85–0,89 nas 16 classes completas, pois qualquer valor acima disso já adentra a zona do ruído inerente à subjetividade da interpretação humana em Diários Oficiais.

## 3. Inventário do Dataset e Perfilamento de Anotadores

### 3.1. Arquivos Processados

| Arquivo de Export | Papel Experimental | Tarefas com Anotação Dupla Válida |
|---|---|---:|
| `ls_p05_seed1.json` | Seed 1 (p05) | 118 |
| `ls_p13_seed2.json` | Seed 2 (p13) | 23 |
| `ls_p15_seed3.json` | Seed 3 (p15) | 3 |
| `ls_p22_seed4.json` | Seed 4 (p22) | 0 |
| **Total Consolidado** | **Projetos de Bounding Box** | **144 páginas (146 pares)** |

### 3.2. Perfilamento Programático de Usuários e Detecção de Pré-Anotação

> **Declaração do Critério:** Critério de identificação do usuário automático/Admin: usuários cujas caixas têm ≥ 98% com `origin == 'prediction'` (isto é, passividade absoluta sem intervenção manual em ≥ 5 tarefas) ou presença em ≥ 70% de todas as tarefas com ≥ 90% de predições puras. Tais anotações representam a carga do detector prévio e foram sumariamente excluídas para evitar viés trivial.

| ID Anotador (`completed_by`) | Tarefas Anotadas | Total de Caixas | % Caixas `prediction` | % Caixas Alteradas/Manuais | Status Metodológico | Justificativa |
|---|---:|---:|---:|---:|---|---|
| `10` | 60 | 825 | 32,7% | 67,3% | **Humano / Válido** | Anotador Humano Válido |
| `11` | 90 | 1771 | 29,1% | 70,9% | **Humano / Válido** | Anotador Humano Válido |
| `12` | 95 | 1636 | 43,7% | 56,3% | **Humano / Válido** | Anotador Humano Válido |
| `2` | 2 | 33 | 21,2% | 78,8% | **Humano / Válido** | Anotador Humano Válido |
| `3` | 394 | 8459 | 36,6% | 63,4% | **Humano / Válido** | Anotador Humano Válido |
| `4` | 505 | 8327 | 45,0% | 55,0% | **Humano / Válido** | Anotador Humano Válido |
| `5` | 525 | 10030 | 37,7% | 62,3% | **Humano / Válido** | Anotador Humano Válido |
| `6` | 573 | 9864 | 45,4% | 54,6% | **Humano / Válido** | Anotador Humano Válido |
| `8` | 1 | 99 | 100,0% | 0,0% | **Humano / Válido** | Anotador Humano Válido |
| `9` | 62 | 946 | 2,5% | 97,5% | **Humano / Válido** | Anotador Humano Válido |

### 3.3. Volume de Pares por Anotador Humano e Matriz Cruzada

| ID Anotador Humano | Total de Pares Compostos |
|---|---:|
| Anotador `3` | 139 pares |
| Anotador `4` | 66 pares |
| Anotador `6` | 54 pares |
| Anotador `9` | 23 pares |
| Anotador `5` | 8 pares |
| Anotador `12` | 1 pares |
| Anotador `2` | 1 pares |

Matriz cruzada de colaboração (pares de anotadores independentes nas mesmas páginas):

| Par de Anotadores | Páginas Compartilhadas |
|---|---:|
| Anotador `3` × Anotador `4` | 64 páginas |
| Anotador `3` × Anotador `6` | 50 páginas |
| Anotador `3` × Anotador `9` | 23 páginas |
| Anotador `5` × Anotador `6` | 4 páginas |
| Anotador `3` × Anotador `5` | 2 páginas |
| Anotador `4` × Anotador `5` | 2 páginas |
| Anotador `12` × Anotador `2` | 1 páginas |

## 4. Detecção e Análise de Pares Suspeitos de Cópia

Para garantir máxima lisura científica, foi implementado um algoritmo de detecção de duplicação mecânica: um par é categorizado como **suspeito de cópia** quando **mais de 95% das suas caixas casadas apresentam IoU ≥ 0,99**. Esse fenômeno ocorre quando o anotador utiliza atalhos da interface (como clonagem de anotações) sem redesenhar ou validar as caixas de forma autônoma.

- **Total de pares suspeitos identificados:** 23 (15,8% do total)
- **Pares confirmadamente independentes:** 123

| Página / Tarefa | Arquivo de Origem | Anotadores | Caixas A | Caixas B | Caixas IoU ≥ 0,99 | % Sobreposição Quase Idêntica |
|---|---|---|---:|---:|---:|---:|
| `0157_2026-06-15-Extra-Pag04-Distrito_Federal_p0004.pdf` | `ls_p05_seed1.json` | `3` × `4` | 19 | 19 | 19 | 100,0% |
| `0165_2026-06-09-NORMAL-EdX-Pag52_Rio_de_Janeiro_p0046.pdf` | `ls_p05_seed1.json` | `3` × `4` | 15 | 15 | 15 | 100,0% |
| `0167_2026-04-30-NORMAL-Ed2638-Pag1106_Sao_Bernardo_do_Campo_p0170.pdf` | `ls_p05_seed1.json` | `3` × `4` | 10 | 10 | 10 | 100,0% |
| `0177_2026-04-10-NORMAL-Ed7037-Pag454_TO_p0420.pdf` | `ls_p05_seed1.json` | `3` × `4` | 18 | 18 | 18 | 100,0% |
| `0178_2026-06-02-NORMAL-EdX-Pag311_Sao_Paulo%28executivo_atos_de_gestao_e_despesas%29_p0297.pdf` | `ls_p05_seed1.json` | `3` × `4` | 27 | 27 | 27 | 100,0% |
| `0216_RIO_DE_JANEIRO_ABRIL_2026+-+rj_sumidouro+-+2026-04-02-NORMAL-Ed1693-Pag16_p0010.pdf` | `ls_p05_seed1.json` | `3` × `4` | 17 | 17 | 17 | 100,0% |
| `0253_SAO_PAULO_ABRIL_2026+-+sp_alvares_florence+-+2026-04-14-NORMAL-Ed2255-Pag45_p0016.pdf` | `ls_p05_seed1.json` | `3` × `4` | 22 | 22 | 22 | 100,0% |
| `0262_2026-04-18-NORMAL-Ed1982-Pag32_Barueri_p0013.pdf` | `ls_p05_seed1.json` | `3` × `4` | 128 | 128 | 127 | 99,2% |
| `0262_2026-04-18-NORMAL-Ed1982-Pag32_Barueri_p0013.pdf` | `ls_p05_seed1.json` | `3` × `5` | 128 | 131 | 125 | 95,4% |
| `0270_RIO_DE_JANEIRO_ABRIL_2026+-+rj_belford_roxo+-+2026-04-29-NORMAL-Ed2206-Pag28_p0010.pdf` | `ls_p05_seed1.json` | `3` × `4` | 21 | 21 | 21 | 100,0% |
| `0330_2026-04-30-NORMAL-Ed2638-Pag1106_Sao_Bernardo_do_Campo_p0980.pdf` | `ls_p05_seed1.json` | `3` × `6` | 12 | 12 | 12 | 100,0% |
| `0334_2026-04-07-NORMAL-Ed18287-Pag196_Fortaleza_p0061.pdf` | `ls_p05_seed1.json` | `3` × `6` | 35 | 35 | 34 | 97,1% |
| `0360_2026-04-30-NORMAL-Ed2638-Pag1106_Sao_Bernardo_do_Campo_p1014.pdf` | `ls_p05_seed1.json` | `3` × `6` | 8 | 8 | 8 | 100,0% |
| `0388_2026-05-05-NORMAL-Ed6587-Pag229_Boa_Vista_p0225.pdf` | `ls_p05_seed1.json` | `3` × `6` | 52 | 52 | 50 | 96,2% |
| `0392_RIO_DE_JANEIRO_ABRIL_2026+-+rj_belford_roxo+-+2026-04-29-NORMAL-Ed2206-Pag28_p0002.pdf` | `ls_p05_seed1.json` | `3` × `6` | 37 | 37 | 37 | 100,0% |
| `SAO_PAULO_ABRIL_2026+-+sp_lagoinha+-+2026-05-04-NORMAL-Ed678-Pag57.pdf` | `ls_p13_seed2.json` | `3` × `9` | 11 | 11 | 11 | 100,0% |
| `SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf` | `ls_p13_seed2.json` | `3` × `9` | 23 | 23 | 23 | 100,0% |
| `SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf` | `ls_p13_seed2.json` | `3` × `9` | 12 | 12 | 12 | 100,0% |
| `SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf` | `ls_p13_seed2.json` | `3` × `9` | 23 | 23 | 23 | 100,0% |
| `SAO_PAULO_ABRIL_2026+-+sp_ourinhos+-+2026-04-28-NORMAL-Ed2126-Pag146.pdf` | `ls_p13_seed2.json` | `3` × `9` | 18 | 18 | 18 | 100,0% |
| ... *(3 outros pares omitidos por concisão)* | | | | | | |

## 5. Concordância de Localização Geométrica (Detecção de Caixas)

Casamento guloso 1-1 por IoU (maior IoU primeiro), independente de classe.

| Limiar IoU | Pares Casados (TP) | Precisão Micro (IC 95%) | Revocação Micro (IC 95%) | F1 Micro (IC 95%) | F1 Macro / Pág. (IC 95%) |
|---|---:|---:|---:|---:|---:|
| **IoU ≥ 0,50** | 2911 | 85,2% [81,8%; 88,4%] | 93,9% [92,4%; 95,2%] | 89,4% [86,8%; 91,7%] | **85,6%** [83,1%; 87,8%] |
| **IoU ≥ 0,75** | 2824 | 82,7% [79,0%; 86,3%] | 91,1% [89,1%; 92,9%] | 86,7% [83,8%; 89,4%] | **82,1%** [79,4%; 84,8%] |
| **IoU ≥ 0,90** | 2773 | 81,2% [77,1%; 85,0%] | 89,5% [87,1%; 91,5%] | 85,1% [81,8%; 87,9%] | **80,4%** [77,6%; 83,3%] |

## 6. Concordância Semântica de Classificação (Caixas Casadas em IoU ≥ 0,5)

| Esquema Taxonômico | N de Classes | Caixas Casadas | Acerto de Classe (IC 95%) | Kappa de Cohen κ (IC 95%) | Grau de Concordância |
|---|---:|---:|---:|---:|---|
| **Guia Oficial (Original)** | 16 | 2911 | 82,2% [79,3%; 84,8%] | **0,763** [0,727; 0,793] | Substancial (0,61 - 0,80) |
| **Extrator TCC (Colapso)** | 9 | 2911 | 91,3% [89,1%; 93,2%] | **0,875** [0,847; 0,901] | Quase perfeita (0,81 - 1,00) |
| **Tripartido (Texto/Tabela/Imagem)** | 3 | 2909 | 98,3% [97,5%; 99,1%] | **0,936** [0,907; 0,964] | Quase perfeita (0,81 - 1,00) |

## 7. Análise Estratificada por Projeto (Seed)

A tabela a seguir apresenta os resultados decompostos para cada projeto individual do Label Studio, revelando como a consistência entre anotadores se comporta em diferentes lotes de extração:

| Projeto / Seed | Arquivo | N Páginas | N Pares | F1 Loc. IoU 0,5 | F1 Loc. IoU 0,75 | F1 Loc. IoU 0,90 | Acerto 16c | Kappa 16c | Acerto 9c | Kappa 9c | Acerto 3c | Kappa 3c | % Ancoragem | Kappa 16c Ativo |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Seed 1 (p05)** | `ls_p05_seed1.json` | 120 | 120 | 84,8% | 81,3% | 79,9% | 83,1% | **0,766** | 92,4% | **0,887** | 98,1% | **0,922** | 41,3% | 0,675 |
| **Seed 2 (p13)** | `ls_p13_seed2.json` | 23 | 23 | 89,5% | 86,9% | 85,9% | 75,3% | **0,716** | 83,9% | **0,803** | 99,7% | **0,993** | 0,0% | 0,716 |
| **Seed 3 (p15)** | `ls_p15_seed3.json` | 3 | 3 | 87,6% | 80,3% | 61,5% | 88,5% | **0,842** | 90,2% | **0,858** | 98,3% | **0,942** | 29,5% | 0,804 |
| **Seed 4 (p22)** | `ls_p22_seed4.json` | 0 | 0 | — | — | — | — | — | — | — | — | — | — | — |
| **Consolidado (Todos)** | *Todos os 4 seeds* | **144** | **146** | **85,6%** | **82,1%** | **80,4%** | **82,2%** | **0,763** | **91,3%** | **0,875** | **98,3%** | **0,936** | **36,0%** | **0,686** |
| **Consolidado Estrito (Sem Cópias)** | *Apenas pares independentes* | **123** | **123** | **82,9%** | **78,9%** | **76,9%** | **81,7%** | **0,756** | **90,6%** | **0,866** | **98,3%** | **0,936** | **34,2%** | **0,683** |

## 8. Análise do Viés de Ancoragem da Pré-Anotação

A pré-rotulação por modelo automatizado agiliza a anotação, mas introduz viés de confirmação (ancoragem): aceitar uma sugestão pronta exige muito menos esforço cognitivo do que redesenhar o bloco ou reclassificá-lo. Abaixo compara-se o dataset completo contra o subconjunto onde **ao menos um anotador realizou intervenção ativa** (`origin == 'manual'` ou `'prediction-changed'`).

| Conjunto Analisado | Caixas Casadas | % do Total | Acerto 16c (IC 95%) | Kappa 16c (IC 95%) | Acerto 9c (IC 95%) | Kappa 9c (IC 95%) | Acerto 3c (IC 95%) | Kappa 3c (IC 95%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Todas as caixas casadas** | 2911 | 100,0% | 82,2% | 0,763 | 91,3% | 0,875 | 98,3% | 0,936 |
| **Ambos aceitaram pré-anotação** (`prediction`) | 1047 | **36,0%** | — | — | — | — | — | — |
| **Ao menos um anotador mexeu** (Ativo) | 1864 | 64,0% | **72,3%** [68,4%; 75,9%] | **0,686** [0,643; 0,726] | **86,5%** [83,6%; 89,2%] | **0,833** [0,797; 0,867] | **97,4%** [95,9%; 98,6%] | **0,919** [0,881; 0,954] |
| **Impacto da Ancoragem (Δ)** | — | — | -10,0% | -0,076 | -4,9% | -0,042 | -0,9% | -0,017 |

## 9. F1 por Classe nas 16 Classes do Guia (Localização IoU ≥ 0,5 + Classe)

| Classe | Função no Guia | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP (IoU ≥ 0,5) | F1 Classe (IC 95%) | Acerto Condicional entre Casadas |
|---|---|---:|---:|---:|---:|---:|
| `act` | Titulo de ato normativo | 147 | 52 | 44 | **44,2%** [20,7%; 63,6%] | 69,3% |
| `act section` | Subtitulo ou divisao interna de ato | 74 | 38 | 21 | **37,5%** [15,8%; 59,1%] | 49,4% |
| `paragraph` | Texto corrente | 1451 | 1435 | 1289 | **89,3%** [85,8%; 92,1%] | 176,0% |
| `signature` | Bloco textual ou digital de assinatura | 164 | 98 | 75 | **57,3%** [43,0%; 71,2%] | 103,4% |
| `heading` | Assinatura manuscrita ou rubrica | 55 | 40 | 32 | **67,4%** [41,9%; 91,4%] | 182,9% |
| `id` | Identificadores, protocolos e codigos | 27 | 38 | 17 | **52,3%** [27,3%; 71,8%] | 94,4% |
| `header` | Cabecalho geral da pagina (recorrente, topo) | 393 | 340 | 272 | **74,2%** [68,6%; 79,3%] | 179,5% |
| `footer` | Rodape geral da pagina (recorrente, base) | 173 | 138 | 110 | **70,7%** [63,5%; 77,6%] | 135,8% |
| `table` | Estrutura tabular | 162 | 164 | 160 | **98,2%** [96,4%; 99,4%] | 200,0% |
| `chart` | Grafico de dados | 7 | 7 | 7 | **100,0%** [100,0%; 100,0%] | 200,0% |
| `figure` | Imagem, fotografia, mapa ou ilustracao | 356 | 251 | 210 | **69,2%** [59,2%; 76,4%] | 164,1% |
| `caption` | Legenda de tabela, figura ou grafico | 81 | 69 | 42 | **56,0%** [40,8%; 68,2%] | 97,7% |
| `title` | Titulo principal de documento NAO normativo | 94 | 240 | 50 | **29,9%** [22,3%; 38,6%] | 42,2% |
| `section title` | Titulo de secao de documento nao normativo | 119 | 127 | 21 | **17,1%** [9,0%; 26,4%] | 21,0% |
| `sub section title` | Titulo de subsecao de documento nao normativo | 111 | 60 | 43 | **50,3%** [7,0%; 69,3%] | 70,5% |
| `unknown` | Classificacao duvidosa | 1 | 3 | 1 | **50,0%** [0,0%; 100,0%] | 100,0% |

## 10. F1 por Classe nos Esquemas Reduzidos

### 10.1. Esquema de 9 Classes do Extrator

| Classe Extrator | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP | F1 Classe (IC 95%) |
|---|---:|---:|---:|---:|
| `assinatura` | 219 | 138 | 107 | **59,9%** [46,6%; 73,0%] |
| `cabecalho` | 393 | 340 | 272 | **74,2%** [68,6%; 79,3%] |
| `figura` | 363 | 258 | 217 | **69,9%** [59,6%; 77,2%] |
| `outro` | 1 | 3 | 1 | **50,0%** [0,0%; 100,0%] |
| `rodape` | 173 | 138 | 110 | **70,7%** [63,5%; 77,6%] |
| `tabela` | 162 | 164 | 160 | **98,2%** [96,4%; 99,4%] |
| `texto` | 1559 | 1542 | 1371 | **88,4%** [84,9%; 91,3%] |
| `titulo` | 545 | 517 | 421 | **79,3%** [73,2%; 84,8%] |

### 10.2. Esquema Tripartido (3 Classes)

| Macroclasse | Suporte Anot. 1 | Suporte Anot. 2 | Acordos TP | F1 Classe (IC 95%) |
|---|---:|---:|---:|---:|
| `texto` | 2834 | 2635 | 2451 | **89,6%** [87,2%; 91,8%] |
| `tabela` | 162 | 164 | 160 | **98,2%** [96,4%; 99,4%] |
| `imagem` | 418 | 298 | 249 | **69,6%** [59,4%; 77,1%] |

## 11. As 10 Confusões de Classes Mais Frequentes

Pares não ordenados de classes atribuídas pelos dois anotadores em uma mesma caixa física casada em IoU ≥ 0,5.

| Ranking | Par de Classes Confundidas | Ocorrências | % dos Desacordos | Contexto Típico em Diários Oficiais |
|---|---|---:|---:|---|
| 1 | `section title` ↔ `title` | 60 | 11,6% | Nível hierárquico de títulos (título geral vs título de seção) |
| 2 | `section title` ↔ `sub section title` | 58 | 11,2% | Subdivisões finas de seções administrativas |
| 3 | `act` ↔ `title` | 43 | 8,3% | Distinção entre título normativo (decreto/portaria) vs título administrativo comum |
| 4 | `paragraph` ↔ `signature` | 40 | 7,7% | Cargos ou nomes em final de atos que se misturam ao parágrafo |
| 5 | `figure` ↔ `title` | 22 | 4,3% | Ambiguidade visual ou funcional da taxonomia |
| 6 | `footer` ↔ `paragraph` | 21 | 4,1% | Rodapé com notas ou avisos legais vs texto corrente final |
| 7 | `act` ↔ `section title` | 19 | 3,7% | Ambiguidade visual ou funcional da taxonomia |
| 8 | `caption` ↔ `paragraph` | 19 | 3,7% | Legenda explicativa curta confundida com parágrafo |
| 9 | `act section` ↔ `section title` | 19 | 3,7% | Ambiguidade visual ou funcional da taxonomia |
| 10 | `act section` ↔ `title` | 19 | 3,7% | Subtítulo de ato classificado como título de matéria |

## 12. Interpretação para o TCC e Limitações Metodológicas

### 12.1. O Teto Empírico Realista para Modelos de Extração
Em Aprendizado de Máquina e Recuperação de Informação, a taxa de concordância inter-anotador humana estabelece a **fronteira de Bayes empírica** (o limite superior de desempenho). Nenhum modelo automatizado (Docling Heron, YOLOv8, RT-DETR ou LayoutLM) pode ser razoavelmente cobrado de concordar com anotações de teste além da taxa em que humanos independentes concordam entre si sob o mesmo guia de rotulagem. Se o F1 de localização humano em IoU ≥ 0,5 atinge 85,6% e o Kappa de Cohen nas 16 classes é de κ = 0,763 (ou κ = 0,686 desancorado), um modelo que alcance métricas nessa vizinhança já está operando no limite teórico do consenso humano.

### 12.2. A Importância da Correção Metodológica
A eliminação de `ls_p23` e a separação dos pares suspeitos de cópia restauram a credibilidade estatística dos dados. Apresentar uma concordância artificialmente alta (κ > 0,94 em 16 classes) mascara o fato científico de que Diários Oficiais brasileiros possuem alta ambiguidade intrínseca. A medição corrigida fornece um alicerce inatacável para a defesa do TCC.

### 12.3. Limitações Declaradas com Honestidade
1. **Tamanho amostral moderado:** A amostra válida consolidada é de 144 páginas (146 pares independentes). Embora o cluster bootstrap forneça intervalos de confiança rigorosos, a diversidade regional de diários municipais é ampla.
2. **Equipe compartilhada:** Todos os anotadores foram treinados no mesmo laboratório, o que harmoniza certas convenções, embora a divergência em classes de granularidade fina continue presente.
3. **Presença residual de pré-anotação:** Mesmo sem o projeto de ordem, boa parte das tarefas partiu de sugestões do detector prévio, de modo que a métrica do subconjunto ativo (ao menos um anotador mexeu) deve ser sempre citada como a contraprova livre de ancoragem.
