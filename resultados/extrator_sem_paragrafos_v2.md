# Extrator sem parágrafos v2

A v2 não satisfaz o critério de melhora; o resultado negativo é preservado.

## Implementação

- A — calhas locais confirmadas por linhas dos dois lados, faixas verticais ocupadas em comum e persistência; faixas estreitas são fundidas pela remoção do corte mais fraco. Títulos e átomos transversais separam zonas.
- B — mantém linhas_partidas como ponto de partida e divide também no vão de uma calha local confirmada, sem cortar palavras nem unir parágrafos. Correção na segunda iteração: sem corte efetivo, conserva a linha original; o código inicial reagrupava seus fragmentos e introduzia cortes extras.
- C — get_drawings fornece traços verticais, retângulos e pares horizontais; find_tables confirma átomos existentes. Vetores nunca criam uma região ou uma calha sem suporte textual. Recorte/rotação incompatíveis desativam esta evidência e são registrados.
- D — uma tabela alinhada em uma coluna, sem grade ou confirmação nativa multicoluna, volta a linhas. Fronteiras vetoriais só estreitam um átomo confirmado; toda palavra tem posse exclusiva. Caixas geométricas ainda podem se sobrepor: posse exclusiva não garante ausência de sobreposição.
- E — reutiliza propostas automáticas de margens da exportação atual e funde somente fragmentos da mesma faixa horizontal e do mesmo tipo. Margens e quadros com várias linhas são divididos em linhas; só tabela e imagem permanecem como bloco na representação principal. Na segunda iteração, a fusão exige calha confirmada no corpo: sem esse suporte, conserva fragmentos de margens, pois a fusão pode impor uma ordem interna errada.

Configuração desta tabela: ABCE.
A pode ser desligado sem desligar B: nesse caso B ainda consulta calhas confirmadas para partir linhas, mas as faixas usam as zonas anteriores. C desliga toda evidência vetorial; D desliga correção de átomos; E desliga o isolamento/fusão de margens na representação nova.

Parâmetros numéricos fixos. A segunda iteração corrige B, restringe E e desliga D após o diagnóstico das bancadas; é desenvolvimento exploratório:

{"gap_original_h": 1.2, "janela_h": 12, "largura_min_mediana": 0.45, "largura_min_pagina": 0.12, "linhas_pareadas": 3, "max_cruzamento": 0.08, "min_faixas_colunas": 2, "passo_janela_h": 6, "persistencia_h": 4, "score_atomos": 0.45, "suporte_linhas": 4, "tolerancia_x_h": 0.5, "vale": 0.08}

## Âncoras

| Método | τ de palavras | Quebras/página |
|---|---:|---:|
| regra | 0,985948 | 6,045455 |
| P2 | 0,985948 | 6,045455 |
| P1m | 0,952424 | 8,931818 |

Âncora aprovada.

P2 e regra nas unidades são reexecutados; P1m é a sequência histórica reavaliada pela mesma medir(), sem refazer o extrator de caixas finas.

## Comparação antes e depois

Representação principal: linhas; faixas de coluna são diagnósticos adicionais. A tabela usa somente páginas pareadas concluídas. Médias por página, sem IC; uma execução determinística, sem treino.

| Bancada | Grupo | Representação | n pareado | Versão | τ | Quebras/página | Piso interno/página | Unidades/página | Fidelidade de 12 | Sucessor de linhas |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| golden_v4 | todos | linhas | 44 | antes | 0,985948 | 6,045455 | 0,545455 | 84,75 | 0,9481 | 0,9272 |
| golden_v4 | todos | linhas | 44 | depois | 0,985953 | 5,931818 | 0,545455 | 84,66 | 0,9486 | 0,9280 |
| golden_v4 | todos | colunas | 44 | antes | 0,815592 | 5,590909 | 3,727273 | 5,43 | 0,9497 | 0,9445 |
| golden_v4 | todos | colunas | 44 | depois | 0,771160 | 5,386364 | 3,977273 | 4,02 | 0,9487 | 0,9444 |
| golden_v4 | todos | colunas_margens | 44 | antes | 0,854196 | 5,340909 | 3,954545 | 5,48 | 0,9523 | 0,9472 |
| golden_v4 | todos | colunas_margens | 44 | depois | 0,837919 | 5,204545 | 3,727273 | 4,89 | 0,9500 | 0,9455 |
| golden_v4 | vistos | linhas | 5 | antes | 0,997638 | 4,800000 | 1,200000 | 133,60 | 0,9849 | 0,9770 |
| golden_v4 | vistos | linhas | 5 | depois | 0,997638 | 4,800000 | 1,200000 | 133,60 | 0,9849 | 0,9770 |
| golden_v4 | vistos | colunas | 5 | antes | 0,860782 | 5,600000 | 2,800000 | 7,40 | 0,9604 | 0,9527 |
| golden_v4 | vistos | colunas | 5 | depois | 0,731001 | 6,200000 | 3,400000 | 6,80 | 0,9545 | 0,9499 |
| golden_v4 | vistos | colunas_margens | 5 | antes | 0,864360 | 5,800000 | 2,800000 | 7,80 | 0,9594 | 0,9498 |
| golden_v4 | vistos | colunas_margens | 5 | depois | 0,734512 | 6,800000 | 3,400000 | 7,60 | 0,9494 | 0,9413 |
| golden_v4 | nao_vistos | linhas | 39 | antes | 0,984450 | 6,205128 | 0,461538 | 78,49 | 0,9434 | 0,9209 |
| golden_v4 | nao_vistos | linhas | 39 | depois | 0,984455 | 6,076923 | 0,461538 | 78,38 | 0,9440 | 0,9218 |
| golden_v4 | nao_vistos | colunas | 39 | antes | 0,809798 | 5,589744 | 3,846154 | 5,18 | 0,9483 | 0,9435 |
| golden_v4 | nao_vistos | colunas | 39 | depois | 0,776309 | 5,282051 | 4,051282 | 3,67 | 0,9480 | 0,9437 |
| golden_v4 | nao_vistos | colunas_margens | 39 | antes | 0,852893 | 5,282051 | 4,102564 | 5,18 | 0,9514 | 0,9469 |
| golden_v4 | nao_vistos | colunas_margens | 39 | depois | 0,851176 | 5,000000 | 3,769231 | 4,54 | 0,9501 | 0,9460 |
| golden_v3_novo | todos | linhas | 27 | antes | 0,959557 | 9,222222 | 0,259259 | 83,63 | 0,9284 | 0,9113 |
| golden_v3_novo | todos | linhas | 27 | depois | 0,959557 | 9,222222 | 0,259259 | 83,63 | 0,9284 | 0,9113 |
| golden_v3_novo | todos | colunas | 27 | antes | 0,809975 | 8,888889 | 6,888889 | 4,07 | 0,9254 | 0,9228 |
| golden_v3_novo | todos | colunas | 27 | depois | 0,802929 | 8,407407 | 6,370370 | 4,15 | 0,9270 | 0,9243 |
| golden_v3_novo | todos | colunas_margens | 27 | antes | 0,808810 | 8,925926 | 6,814815 | 4,33 | 0,9250 | 0,9208 |
| golden_v3_novo | todos | colunas_margens | 27 | depois | 0,790785 | 8,296296 | 6,222222 | 4,59 | 0,9273 | 0,9240 |
| golden_v3_novo | nao_vistos | linhas | 27 | antes | 0,959557 | 9,222222 | 0,259259 | 83,63 | 0,9284 | 0,9113 |
| golden_v3_novo | nao_vistos | linhas | 27 | depois | 0,959557 | 9,222222 | 0,259259 | 83,63 | 0,9284 | 0,9113 |
| golden_v3_novo | nao_vistos | colunas | 27 | antes | 0,809975 | 8,888889 | 6,888889 | 4,07 | 0,9254 | 0,9228 |
| golden_v3_novo | nao_vistos | colunas | 27 | depois | 0,802929 | 8,407407 | 6,370370 | 4,15 | 0,9270 | 0,9243 |
| golden_v3_novo | nao_vistos | colunas_margens | 27 | antes | 0,808810 | 8,925926 | 6,814815 | 4,33 | 0,9250 | 0,9208 |
| golden_v3_novo | nao_vistos | colunas_margens | 27 | depois | 0,790785 | 8,296296 | 6,222222 | 4,59 | 0,9273 | 0,9240 |

## Defeitos da auditoria

Mesma auditar_pagina() em ambas as versões, nas mesmas páginas. D1–D4 e D6–D7 recebem unidades em linhas; D5 recebe as respectivas margens automáticas de colunas_margens. Conta páginas afetadas, não número de ocorrências.

| Bancada | Grupo | n pareado | Detector | Antes | Depois |
|---|---|---:|---|---:|---:|
| golden_v4 | todos | 44 | D1 | 0 | 2 |
| golden_v4 | todos | 44 | D2 | 2 | 2 |
| golden_v4 | todos | 44 | D3 | 0 | 0 |
| golden_v4 | todos | 44 | D4 | 8 | 8 |
| golden_v4 | todos | 44 | D5 | 1 | 7 |
| golden_v4 | todos | 44 | D6 | 11 | 11 |
| golden_v4 | todos | 44 | D7 | 0 | 0 |
| golden_v4 | vistos | 5 | D1 | 0 | 0 |
| golden_v4 | vistos | 5 | D2 | 0 | 0 |
| golden_v4 | vistos | 5 | D3 | 0 | 0 |
| golden_v4 | vistos | 5 | D4 | 1 | 1 |
| golden_v4 | vistos | 5 | D5 | 0 | 1 |
| golden_v4 | vistos | 5 | D6 | 1 | 1 |
| golden_v4 | vistos | 5 | D7 | 0 | 0 |
| golden_v4 | nao_vistos | 39 | D1 | 0 | 2 |
| golden_v4 | nao_vistos | 39 | D2 | 2 | 2 |
| golden_v4 | nao_vistos | 39 | D3 | 0 | 0 |
| golden_v4 | nao_vistos | 39 | D4 | 7 | 7 |
| golden_v4 | nao_vistos | 39 | D5 | 1 | 6 |
| golden_v4 | nao_vistos | 39 | D6 | 10 | 10 |
| golden_v4 | nao_vistos | 39 | D7 | 0 | 0 |
| golden_v3_novo | todos | 27 | D1 | 0 | 0 |
| golden_v3_novo | todos | 27 | D2 | 3 | 3 |
| golden_v3_novo | todos | 27 | D3 | 0 | 0 |
| golden_v3_novo | todos | 27 | D4 | 4 | 4 |
| golden_v3_novo | todos | 27 | D5 | 0 | 1 |
| golden_v3_novo | todos | 27 | D6 | 4 | 4 |
| golden_v3_novo | todos | 27 | D7 | 0 | 0 |
| golden_v3_novo | nao_vistos | 27 | D1 | 0 | 0 |
| golden_v3_novo | nao_vistos | 27 | D2 | 3 | 3 |
| golden_v3_novo | nao_vistos | 27 | D3 | 0 | 0 |
| golden_v3_novo | nao_vistos | 27 | D4 | 4 | 4 |
| golden_v3_novo | nao_vistos | 27 | D5 | 0 | 1 |
| golden_v3_novo | nao_vistos | 27 | D6 | 4 | 4 |
| golden_v3_novo | nao_vistos | 27 | D7 | 0 | 0 |

Conferência com auditoria_extrator_sem_paragrafos.json na interseção de páginas disponível. O main da auditoria histórica prioriza estruturas_golden_v4/linhas.jsonl e depois datasets_sem_caixas; esta execução usa unidades_sem_caixas/bancadas. São exportações diferentes, mesmo quando o page_id coincide; a coluna histórica não substitui o antes pareado. D5 também recebe estruturas históricas na auditoria original. A cobertura nula do v3 novo significa ausência nessa auditoria, e não ausência de defeitos.

| Bancada | Páginas cobertas pelo JSON histórico | Detector | Histórico | Antes atual | Depois |
|---|---:|---|---:|---:|---:|
| golden_v4 | 44 | D1 | 3 | 0 | 2 |
| golden_v4 | 44 | D2 | 10 | 2 | 2 |
| golden_v4 | 44 | D3 | 0 | 0 | 0 |
| golden_v4 | 44 | D4 | 4 | 8 | 8 |
| golden_v4 | 44 | D5 | 36 | 1 | 7 |
| golden_v4 | 44 | D6 | 10 | 11 | 11 |
| golden_v4 | 44 | D7 | 6 | 0 | 0 |
| golden_v3_novo | 0 | D1 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D2 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D3 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D4 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D5 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D6 | 0 | 0 | 0 |
| golden_v3_novo | 0 | D7 | 0 | 0 | 0 |

## Resultado

A v2 não satisfaz o critério de melhora; o resultado negativo é preservado.

Critério aplicado à representação em linhas: o v4 não pode perder τ nem ganhar quebras; além disso, o v3 deve melhorar uma das duas medidas sem piorar a outra, ou o piso interno deve cair em uma bancada sem subir na outra. Faixas melhores sozinhas não declaram vitória da representação principal.
Preserva v4: sim; melhora v3: não; melhora piso: não.
Páginas com menos / mesmas / mais quebras nesta configuração: 2 / 69 / 0. As listas de extremos incluem empates quando faltam ganhos ou regressões.

## Páginas com maior mudança

Ordenação por Δ de quebras em linhas, com Δ de τ como desempate. Os grupos identificam os menores e maiores deltas observados; se não houver ganho ou regressão, o sinal do delta deixa isso explícito.

| Grupo | Bancada | page_id | Quebras antes | Depois | Δ quebras | τ antes | Depois | Δ τ |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Menores deltas | golden_v4 | official_diary_ac/executive_official_diary_2025-02-11.pdf#p114 | 10 | 7 | -3 | 0,925786 | 0,925901 | 0,000115 |
| Menores deltas | golden_v4 | official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41 | 13 | 11 | -2 | 0,963683 | 0,963783 | 0,000100 |
| Menores deltas | golden_v4 | official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1 | 5 | 5 | +0 | 0,999031 | 0,999031 | 0,000000 |
| Maiores deltas | golden_v4 | official_diary_to/2024-04-17_5147.pdf#p47 | 5 | 5 | +0 | 0,986327 | 0,986327 | 0,000000 |
| Maiores deltas | golden_v4 | official_diary_to/2022-12-13_4783.pdf#p10 | 5 | 5 | +0 | 0,987445 | 0,987445 | 0,000000 |
| Maiores deltas | golden_v4 | official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31 | 6 | 6 | +0 | 0,996248 | 0,996248 | 0,000000 |

## Evidência vetorial e painéis

Páginas com aviso vetorial: 0.
Os painéis finais são renderizados diretamente do PDF e da página indicados no page_id. O mapa antigo de imagens reutilizava um nome de imagem entre lotes e mostrou uma edição diferente na página do AC do v3 novo; as imagens iniciais excedentes ficam arquivadas em extrator_sem_paragrafos_v2/paineis_iniciais/ e não são evidência visual validada.
- [official_diary_ac/executive_official_diary_2025-02-11.pdf#p114](extrator_sem_paragrafos_v2/01_fe2075081668f517c8b9cbb6.jpg): linhas antes e depois.
- [official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf#p41](extrator_sem_paragrafos_v2/02_b2a5cd50f2cc16be781a7506.jpg): linhas antes e depois.
- [official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf#p1](extrator_sem_paragrafos_v2/03_25723bbc6318fa9e6c50510b.jpg): linhas antes e depois.
- [official_diary_to/2024-04-17_5147.pdf#p47](extrator_sem_paragrafos_v2/04_3c7415971a4758b329a182c8.jpg): linhas antes e depois.
- [official_diary_to/2022-12-13_4783.pdf#p10](extrator_sem_paragrafos_v2/05_d694ca87d46d1d9a88c24302.jpg): linhas antes e depois.
- [official_diary_se/DOE-SE_2026-01-16_7401.pdf#p31](extrator_sem_paragrafos_v2/06_49b4cc8933803d532df866f8.jpg): linhas antes e depois.
- [official_diary_ac/executive_official_diary_2022-08-03.pdf#p109](extrator_sem_paragrafos_v2/07_f92f64f16fc819255f28110b.jpg): linhas antes e depois.
- [official_diary_ac/executive_official_diary_2025-09-24.pdf#p41](extrator_sem_paragrafos_v2/08_9e6a0d05edbce5bc1be2cc09.jpg): linhas antes e depois.

## Rodadas e efeito por componente

Inicial: todos ligados. Iteração 1: retirar um componente por vez, mantendo os outros quatro. Iteração 2, quando executada: uma combinação fixada a partir desses diagnósticos. A retirada mede efeito condicionado aos outros componentes, não efeito isolado. A seleção usa ambas as bancadas humanas; não constitui validação independente.

| Rodada | Componentes ligados | Bancada | n | τ | Quebras/página | Piso interno | Unidades/página | Cumpre critério |
|---|---|---|---:|---:|---:|---:|---:|---|
| Inicial | ABCDE inicial | golden_v4 | 44 | 0,986342 | 5,909091 | 0,500000 | 84,57 | não |
| Inicial | ABCDE inicial | golden_v3_novo | 27 | 0,958933 | 10,592593 | 0,333333 | 90,96 | não |
| Iteração 1 | ABCD | golden_v4 | 44 | 0,986300 | 6,204545 | 0,500000 | 84,93 | não |
| Iteração 1 | ABCD | golden_v3_novo | 27 | 0,958939 | 10,481481 | 0,259259 | 91,07 | não |
| Iteração 1 | ABCE | golden_v4 | 44 | 0,986342 | 5,909091 | 0,500000 | 84,57 | não |
| Iteração 1 | ABCE | golden_v3_novo | 27 | 0,959551 | 9,333333 | 0,333333 | 83,52 | não |
| Iteração 1 | ACDE | golden_v4 | 44 | 0,985990 | 5,750000 | 0,545455 | 84,39 | não |
| Iteração 1 | ACDE | golden_v3_novo | 27 | 0,958933 | 10,592593 | 0,333333 | 90,96 | não |
| Iteração 1 | BCDE | golden_v4 | 44 | 0,986342 | 5,909091 | 0,500000 | 84,57 | não |
| Iteração 1 | BCDE | golden_v3_novo | 27 | 0,958933 | 10,592593 | 0,333333 | 90,96 | não |
| Iteração 1 | ABDE | golden_v4 | 44 | 0,983810 | 7,022727 | 0,500000 | 87,16 | não |
| Iteração 1 | ABDE | golden_v3_novo | 27 | 0,958933 | 10,592593 | 0,333333 | 94,26 | não |
| Iteração 2 | ABCE (B corrigido; E restrito) | golden_v4 | 44 | 0,985953 | 5,931818 | 0,545455 | 84,66 | não |
| Iteração 2 | ABCE (B corrigido; E restrito) | golden_v3_novo | 27 | 0,959557 | 9,222222 | 0,259259 | 83,63 | não |

### Maiores mudanças na implementação inicial

Preserva os casos que motivaram a segunda iteração, inclusive as regressões.

| Grupo | Bancada | page_id | Quebras antes | Depois | Δ quebras | τ antes | Depois |
|---|---|---|---:|---:|---:|---:|---:|
| Melhores | golden_v4 | official_diary_ac/executive_official_diary_2025-02-11.pdf#p114 | 10 | 7 | -3 | 0,925786 | 0,925901 |
| Melhores | golden_v4 | official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48 | 2 | 0 | -2 | 0,998864 | 1,000000 |
| Melhores | golden_v4 | official_diary_rr/2021-09-23_DiarioRR.pdf#p10 | 2 | 0 | -2 | 0,999672 | 1,000000 |
| Piores | golden_v3_novo | official_diary_mg/executive_official_diary_2021-12-30.pdf#p16 | 8 | 42 | +34 | 0,989639 | 0,972955 |
| Piores | golden_v4 | official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf#p0 | 3 | 7 | +4 | 0,998051 | 0,998332 |
| Piores | golden_v3_novo | official_diary_ac/executive_official_diary_2025-09-24.pdf#p41 | 0 | 3 | +3 | 1,000000 | 0,999826 |

## Incerteza pareada por veículo

Bootstrap pareado por veículo; cada reamostra sorteia veículos com reposição e inclui todas as suas páginas, preservando a média por página. IC percentil de 95%, com semente e reamostras registradas no estado. Δ = depois − antes; em quebras/piso, negativo é melhor. Os IC são descritivos e não corrigem a seleção de componentes nas bancadas.

| Bancada | Métrica | Δ médio | IC 95% |
|---|---|---:|---|
| golden_v4 | tau | 0,000005 | [0,000000; 0,000012] |
| golden_v4 | quebras | -0,113636 | [-0,291692; 0,000000] |
| golden_v4 | piso_interno | 0,000000 | [0,000000; 0,000000] |
| golden_v3_novo | tau | 0,000000 | [0,000000; 0,000000] |
| golden_v3_novo | quebras | 0,000000 | [0,000000; 0,000000] |
| golden_v3_novo | piso_interno | 0,000000 | [0,000000; 0,000000] |

Ganho confiável neste diagnóstico: não.
Unidades finais completas são publicadas somente com critério de melhora cumprido e IC inteiramente favorável em quebras ou piso interno. Isso ainda exige avaliação futura em páginas independentes.

## Limitações

- golden_v4 foi usado no desenvolvimento da regra e nas reclamações que motivaram estas correções; os parâmetros desta versão são fixados antes da comparação, mas a bancada não é independente do desenvolvimento.
- golden_v3_novo fica fora do v4, porém suas notas e a auditoria também motivaram a implementação. A amostra humana é pequena; veículos vistos e não vistos no treino são separados pelo splits.json vigente.
- Esta tarefa gera somente as duas bancadas humanas pedidas. Não mede teste silver nem retreina ordenadores. A referência silver do projeto é automática, do fluxo do PDF em veículos confiáveis; nenhum resultado silver novo é apresentado aqui.
- A ordem interna é sempre ordem_sem_bbox.fluxo(), inclusive em tabelas. O piso usa eventos() dentro de cada unidade; o teto por posto mediano da referência é diagnóstico, sem otimização combinatória.
- Os alertas D1–D7 são heurísticos. Na auditoria anterior, D1 e D4 não recuperaram as notas correspondentes do autor; uma queda de alertas isoladamente não demonstra melhora de leitura. D5 aqui recebe margens automáticas de ambas as versões nas mesmas páginas, e não as estruturas históricas exclusivas de parte do v4. As contagens não são o total do acervo da auditoria original.
- Listas com colunas de dados e tabelas sem bordas continuam ambíguas; uma grade pode faltar no PDF digital. Átomos vazios são conservados, pois podem ser tabelas/imagens rasterizadas. Não há OCR nem palavras novas para texto em imagem.
- A regra_colunas da bancada é preservada, inclusive sua busca de calhas. A hierarquia v2 orienta segmentação e metadados; não é uma troca oculta do ordenador. Nas faixas, a hierarquia também muda a unidade atômica.

## Retomada e proveniência

Resultados e unidades são salvos por página, com hashes das fontes, do PDF, do detector e do código. Exportações finais são montadas desses caches em fluxo. As origens ficam em leitura; não há treino, multiprocessing, DataLoader ou GPU.

Páginas com antes salvo: 71; com depois salvo: 71.

Estado: concluida.

Execução: venv/Scripts/python.exe -B orquestracao/analises/extrator_sem_paragrafos_v2.py

Fingerprint: 725acb54c96336b233b5c95a78afd947801b0e3b2a10d7a9982074a3cbae1dce

Hashes das fontes:

- data/processed/splits.json: f957e4c2e174600f9d71d26510226aabd894689870b3b5b7881a9b19640a587d
- data/raw/official_diary_ac/executive_official_diary_2022-08-03.pdf: 92c60ab581f454b544a3727acd6b6dfd58b0f5d411b7f9c6593dbe7544341cf2
- data/raw/official_diary_ac/executive_official_diary_2022-12-02.pdf: c0ac316106a31efb30ba9acb6376fa371f86036050901276eb8f44beb4ac0845
- data/raw/official_diary_ac/executive_official_diary_2025-02-11.pdf: 0765000195d745f931ffaa726a9bf069425c6fb40d982a3895ecc75384e27aa5
- data/raw/official_diary_ac/executive_official_diary_2025-09-24.pdf: 49ab8fdbc4f4b4853cb735123852468d0dd81fe6f43479fda3a9eedf4211fc30
- data/raw/official_diary_al/DOEAL-2021-10-06-COMPLETO_87_152.pdf: e3a73dc0ed613900044bb6241690e21a9c2d86e7dc8568a7d1fbbd45bc217ddd
- data/raw/official_diary_al/DOEAL-2023-03-22-COMPLETO_54_172.pdf: 1f2b9829900e207dd1f49409c6501b80d3c92020ee418a895c8c17f20dd33406
- data/raw/official_diary_al/DOEAL-2026-01-16-SUPLEMENTO.pdf: 8c90d7538ee24223d82a644b6cacc65937215783ee0e8e0e4a9ef7c9d96388c1
- data/raw/official_diary_am_manaus/2023-03-13_caderno_2.pdf: 317b5876b3ff95951404497a9c8426206034b427e42a892f79044e5ae6d88bfd
- data/raw/official_diary_ap/2024-02-20_DOEn8106_Edicao Ordinaria.pdf: 0846051b2553af1b1a0625798a7b95397c2946b5273ce8b51ffb40cfe03458c9
- data/raw/official_diary_ap/2024-05-07_DOEn8159_Edicao Ordinaria.pdf: f74e3396537e450a45f8702a3f6928d7a0f0a6bb8c4595d3f850be916b1e2cdb
- data/raw/official_diary_ap/2024-09-27_DOEn8257_Edicao Ordinaria.pdf: 1e3a4ff253b9b06ab73e1c74442f6fe38aeaba0fc66d9971186a84b5630487bf
- data/raw/official_diary_ba_salvador/dom-8379-27-09-2022.pdf: 17bbe2f3c239b22791b970e0d7a3002afe5b8748aee552f7b6e9cc2907dffd45
- data/raw/official_diary_ce/do20220512p03.pdf: 0496af669ca879b836c5f23044e143f9692393391017d6eda851fb19a512e49d
- data/raw/official_diary_ce/do20220530p02.pdf: dbd894a14a14f230cfd84537a7c62b473aeb6331e708e95dacc1af3514ab4ec1
- data/raw/official_diary_ce/do20240429p01.pdf: 2fabef378096d1dbff1425628b9240cab64d0b34ebc41217a6b156d2d736befb
- data/raw/official_diary_ce/do20250505p03.pdf: 4874129ccbba3183427da3ec687faea7aa5451869942c7b9edfb481a246c58f2
- data/raw/official_diary_ce/do20250522p02.pdf: 37f3c0b66e229ecaddea741029d1fbeaee36cb86b520644131cc98bb2d8403d6
- data/raw/official_diary_ce/do20260107p04.pdf: 0ccab4bce42b2a88bde1a76a7ba12ad24b5679032c72092ea20d1516582ef381
- data/raw/official_diary_ma/executive_official_diary_2021-11-12.pdf: 1450fc787e3ddc965321df2e5010cce5a361e3722068bf664027810c49a4fb6f
- data/raw/official_diary_ma/executive_official_diary_2021-11-19.pdf: 9c7ca3565d7b19c6e15c61c667754b93f198d68673d2259cf8da293068cc94ed
- data/raw/official_diary_ma/executive_official_diary_2021-12-20.pdf: d3a631fb7261a6ccc7abe42588dcea7eae044be5eb263cb7af3e013d46db237f
- data/raw/official_diary_ma/executive_official_diary_2023-03-06.pdf: 9700be14882799b108788df2f5dec9809a015c3f880708e1e7cfda8a4dad751a
- data/raw/official_diary_ma/executive_official_diary_2023-12-04_30_84.pdf: 168768cd672c2025f7fa26217cdafbedae93a2d45bc28e1a859376b870e17746
- data/raw/official_diary_ma/executive_official_diary_suplement_2025-02-21_202_378.pdf: 02258dabea326df3d7ffb212852209ac04c3381557f6ebb5dd7a925e3715b1b0
- data/raw/official_diary_mg/executive_official_diary_2021-07-06.pdf: 39f5a56b4e6767e0b050b9cab822ccd94975a5b9261a68d04fd1e86743a2659c
- data/raw/official_diary_mg/executive_official_diary_2021-12-30.pdf: c6357fe593feb9892d566feb185685d6fd3998fe72082f8a8a942ea5c58a6a54
- data/raw/official_diary_MG_congonhas/executive_official_diary_2020-12-10_2591.pdf: 315ac4ebab01e77b504fdb9c0c1b28ea42c86deb98dce595954b8b971031b1c7
- data/raw/official_diary_MG_congonhas/executive_official_diary_2022-09-02_3022.pdf: a985284dd7a33998cfbec661b4e2461b4aa0b9172f5796bb7e5558fe9241e823
- data/raw/official_diary_ms/executive_official_diary_46741_2021-06-29.pdf: 5c505f4d1af264c8c5212a590fd476d27ebdd61cee16b2baf1f0135d8366d215
- data/raw/official_diary_ms/executive_official_diary_48733_2024-11-05.pdf: 642ca33cc4c60ff1e165115aa4c33188ec5afc42bb9af4309b84fbc17e25db53
- data/raw/official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf: 4bc05f73a2a1b34b2abf12ca98b7d51f2a81d17e1026b8ce1244f32e4bbecace
- data/raw/official_diary_pb/Diario Oficial 10-09-2025 Portal.pdf: 2f6032576c42a7a8dbd42f84890b9a7901e1dd12e03ccecf217bb437282e1a02
- data/raw/official_diary_pe/2023-02-02_1-Poder Executivo.pdf: 1dada252153327b4e1c524d412ad373f2e944e1cc2e5e7f3ec5c5190434b3ebe
- data/raw/official_diary_pi_v2/executive_official_diary_2024_01_12_9_2024_243_297.pdf: 1b36feb34736dc1ba448d3d1cb2dbb70160dc4ec8e6a3f74c99306f25f43426c
- data/raw/official_diary_pi_v2/executive_official_diary_2024_05_29_104_2024_15_340.pdf: cb4d17853ecc31a1e278059e6c3629f8394e2024bc5cc5f49e6f11bf630c8703
- data/raw/official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf: f932cc92a1346fc33405eb213f9c491a6da1aa665a368b7502f0526c37b4dde4
- data/raw/official_diary_pr_curitiba/24-Supl1_2024-02-05.pdf: 36e62e7ec3195261d07b090fdde65f1ff59f592cb9034b6f737ccee27ea7f582
- data/raw/official_diary_rj/Parte I (Poder Executivo)_2022-01-05.pdf: ed277baed9b0a1434a64e75d27ec21e35989311cc8aaa7e77c245e2c16920b5d
- data/raw/official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf: be98b357570a856d3065fdf5f2e4a7b1588a31711164d38043c3fd9492e48539
- data/raw/official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf: bd5c413e401711d58905a12b1b7e71e6e7b14ac31552a10b5224d61960818317
- data/raw/official_diary_rj/Parte IV (Municipalidades)_2021-08-30.pdf: 429bb3d6ac38dc8d9d34e573513df2afddc77b1b2ed41ea8ad9279eeac4c646f
- data/raw/official_diary_rj/Parte IV (Municipalidades)_2025-11-10.pdf: 4e53db4bb76edbe6f2c2465c2634f6b7d908fa23add2322ef35fd938d3957feb
- data/raw/official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf: 898291ea7acee1d8a0704f0c174d7b27b157b107716fb94dd54684ce6ebb3d67
- data/raw/official_diary_RJ_barra_do_pirai/executive_official_diary_2022-08-02_139.pdf: 0ef99b7bcb2557fb17d94a931b1f572b8917d5a8894dbd38988a8a7a0b9fcf56
- data/raw/official_diary_RJ_barra_do_pirai/executive_official_diary_2023-11-24_214.pdf: 0c41a781af4eae9cd8487025001c539002993787a8a31190bb742aa3f866882a
- data/raw/official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf: bb39e49326007c13ccbe0a4f3e173a794b2b2669bf0431ca45ab8ff5bd346fd4
- data/raw/official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf: fcef7d6560c6339578f4a11dac50e95f75bfcc039b7c8cc5e4633c8a49bae4bc
- data/raw/official_diary_RJ_duque_de_caxias/executive_official_diary_2025-05-02_Boletim_7582_vol2.pdf: adcd8aeb396c517fe384f3ca3c08c0cfc360102f7cb612754fda0acb9094bc38
- data/raw/official_diary_rj_japeri/JAPERI-5606-09-DE-MAIO-2024.pdf: 3bec03c465fbfba0bb6891473c34aaf9d15916d6b5a8de52d86f7ea23e9fa65b
- data/raw/official_diary_rj_japeri/JAPERI-5690-06-DE-SETEMBRO-2024.pdf: 98b9de29db6daa3ffaea9d92cc55c5c8520f6f80aa5e1d096986efb78df55b6d
- data/raw/official_diary_RJ_seropedica/executive_official_diary_2022-05-09_986.pdf: d3363974b4be37ecc0d65ea89940f8a77fcc438b171f927d0b8bb8bdc19bebc5
- data/raw/official_diary_RJ_volta_redonda/executive_official_diary_2023-09-22_1987-extra.pdf: 777da18939b7a88c15c17d19bf1375b2c44ddb2528ee68b786b5dbd8ecbf3165
- data/raw/official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf: ddd84116a88fa114f8ae6de29de7beaf2b78b3453a14c0d5bb32bc254acae6d9
- data/raw/official_diary_ro/executive_official_diary_2023-07-26_304_320.pdf: d341dc45404ad6ad2f2e12d2b47588ff9cc690fe9b326187f129fc7945a7f951
- data/raw/official_diary_ro/executive_official_diary_2024-06-12.pdf: f1825f690f1790ecd81deef09b1822c86a278771384940f75ddd411dfbe5737b
- data/raw/official_diary_ro/executive_official_diary_suplemento_2026-01-09.pdf: 12c1d5d7c80c0a4c1c896b4f4c71f32e9f2a0e397314e139484d4a7763456104
- data/raw/official_diary_rr/2021-09-23_DiarioRR.pdf: f25999f70e4014f02eccc2dee421516b52f9567717733a291533938be90bf7f6
- data/raw/official_diary_rs_porto_alegre/4689_cl_20230227_legislativo.pdf: 52cb53c2dc75260013694ac1e1ab35fc0b7c761ef3838521435ccdd38193e647
- data/raw/official_diary_sc/2023-11-27_22151.pdf: 08aae24b8cf1687c480b82ab7bef0812f2dc7b305d8ef34597bd7ea34e2c3649
- data/raw/official_diary_se/DOE-SE_2022-03-18_4475.pdf: c55631b90fb5384894e25e90e63128f0dc4d0ff4836b06471824a04b487dd2c4
- data/raw/official_diary_se/DOE-SE_2023-03-10_5100.pdf: 4b37ac4a5418afb02d77064e7552a8b1e8205cfa947b922744b8432d02af39fe
- data/raw/official_diary_se/DOE-SE_2026-01-16_7401.pdf: c77927e3b92148220551f7c63b0a34358cabc4c592a2afca8b416a6f67faacdf
- data/raw/official_diary_to/2022-12-13_4783.pdf: 1e1b9054dcd56924c7c08da946b1cc1fdc4421607733b884dd27e551aaee9178
- data/raw/official_diary_to/2024-04-17_5147.pdf: c583e33de25ad9451a121b4f6e8049d69e09841109b759d4ab4ab3cab7b75167
- orquestracao/analises/auditoria_extrator_sem_paragrafos.py: 1e45f247be7d82765ecbcfb7f0f46aa11eefef8825cdef14e8f7ab28dd4e58a5
- orquestracao/analises/bancada_ordenadores.py: 42ab35c43393384e73951f8c9969c062e093621ace0e1d3346ebbb77f4e31831
- orquestracao/analises/erros_ponta_a_ponta.py: 870c83bdd4bc034eff3982b552ff907ef665cf0aecd0c5adc3c253bd16f38b88
- orquestracao/analises/extrator_sem_paragrafos_v2.py: fc575df2e40df6b5ac59f121fb5ffc815f2fd776675aaa3f6670a18d46af6923
- orquestracao/analises/ordem_layoutreader.py: ab0da59d9e9ce35a0608784c2ea14333912efd5df1942ec515b54034e3b6789a
- orquestracao/analises/ordem_sem_bbox.py: f6d4589ec7752272c3635e3eafbe91b640fd93339cd075fc1a5f2c70aeb8715f
- orquestracao/analises/ordem_sem_bbox_justo.py: 58aca7c6ee1e3bccdcbcd915a62b9fb71bc0814e5e5b8e8d48825d2cf8119736
- orquestracao/analises/ordem_sem_bbox_ls3.py: 3698cd220abba6815a4498f43469a3e578f5c2ec172025b051e8a86b140aaaa5
- orquestracao/analises/ordem_sem_bbox_validacao_acervo.py: bf0aca24402c2083fac360834e11855168fcb5378bf6b21abb4055fc3a76effe
- orquestracao/analises/reclamacoes_x_novo.py: aa90098f5931df8b23b268993260d916a062a39abfac327b62caefe6b28001d9
- orquestracao/analises/unidades_sem_caixas.py: ae129ce4b55020d3f7162a179ca0c255b638e08c00ac053bc75b0c908b72c3c3
- resultados/auditoria_extrator_sem_paragrafos.json: 8b9bb3411d5f177e4a9cedbae4f2a5e42c21f01fe4a3ba14a814baf42c2585cf
- resultados/erros_ponta_a_ponta.json: 15e329b002131afee7eed284ddaad9c11d672c9663c968a49b3b71f19a151098
- resultados/unidades_sem_caixas/bancadas/golden_v3_novo.jsonl: 3cbf0331eb778740b7f61f5f38d6bd07e1c0874038932a209f19f6875295f6e0
- resultados/unidades_sem_caixas/bancadas/golden_v4.jsonl: 683c64e71e63a753587912bc31ffa0973e4b3e7d24fadc08b05f4ce8ef49ea51
- resultados/unidades_sem_caixas/cache/detector/00e1f64ea5cffa09bf663320.json: 5075c17b7bab72167b72743aef95962ae1b5affd7316efc33716eeba5a1b6270
- resultados/unidades_sem_caixas/cache/detector/042a7a5036c278648496447f.json: c5058e51b587f02f894dd6f5d628891150810c6326bcccafac5342268f2cab26
- resultados/unidades_sem_caixas/cache/detector/06676fc3f2070dd27d8a9304.json: 9be15d0b4c0484f7948144aca2fd9bb5e46b7d0072d16a9ad574b1a074f83a08
- resultados/unidades_sem_caixas/cache/detector/0b1d49fd3400dc6e50f6a9d0.json: 1dbaf7ab8a58608b6e9ab2dae650ff2a2a4dfe36c6930442785cbc40a656566b
- resultados/unidades_sem_caixas/cache/detector/0b5ffb1f57e29ac0e29e5583.json: fe9dfd205b607149d355f2d184e9fff7ae58a4a589bb385488a20ba44fa1dd7d
- resultados/unidades_sem_caixas/cache/detector/0b83561888ee183bb8556334.json: 1d6976ff35cfe2ff6804c07fc867c6bf86d2bc7c38e7a3f81ee8f3c5ab29fb7a
- resultados/unidades_sem_caixas/cache/detector/0f67b25f69071cb273edaa30.json: 2d246945184c6a2e9d7c68e0cb37b3bd31036674c7b8109895bb0ed20d3d7353
- resultados/unidades_sem_caixas/cache/detector/1543464cfd30f1d10a817deb.json: e5c21d44fce40ee1aa770299a84bfcd73470f5ba8d74b6933db552967a65cf72
- resultados/unidades_sem_caixas/cache/detector/197de9eb139f715c978aff35.json: 434c7f964b75f7c1e7892b1723d0dbcd2cc0a8ee8e163985df0e5ae93b392d28
- resultados/unidades_sem_caixas/cache/detector/1b906447ddc9bc5877d907b2.json: fcfe485c4d0d1b00bb44cae77d89f292f49d2d285e22960c24784d51d6c11d14
- resultados/unidades_sem_caixas/cache/detector/1c0977c846dbfe981d319d7d.json: 6857c4d9d209d1bc1c84e223b0979c20bc74f9af3810982baa7647b77e6eb069
- resultados/unidades_sem_caixas/cache/detector/1c464b762e2b19870c7f7f5c.json: 195565015bc141ec22a36b8d60bc989690ea124c373cd580d8e7d3dd9f816115
- resultados/unidades_sem_caixas/cache/detector/1c4ab1c4718354e7d16492ac.json: 19848a40498e0f0d7858e0ba93b7210aef40ca9ff1b093a2efb73a65fa7b58c6
- resultados/unidades_sem_caixas/cache/detector/1dc27104f4d7d53f35162b36.json: 98d8cc4eedff60170a740ac5408367b520c1538e73fe2e7691c4283ff61e760b
- resultados/unidades_sem_caixas/cache/detector/25723bbc6318fa9e6c50510b.json: 35737d6d0ac68913e5c16b6003f86a1b8fc2b14dcb5ff0e3c8b2f4566c65cbde
- resultados/unidades_sem_caixas/cache/detector/280a63b0901a22caec62c2e1.json: 565cc7bb7c6515909f2d7f6d06f838c299dfb1fcc9ab02f7f9642fec553bccb6
- resultados/unidades_sem_caixas/cache/detector/29d1b2e6ce5100678a8b51d3.json: 38a220be933d0e9f77ef6485c84967c6fcb380444ea8e7d3017df42a6fe58ea6
- resultados/unidades_sem_caixas/cache/detector/2bd8e2f03e0a2a8f37afe58d.json: 2a1a44115175dbe8183a587897e9501bee730b57d3ea4b8809d4a140aa9fe490
- resultados/unidades_sem_caixas/cache/detector/2d8329878c997c6fa4626716.json: ee6d1c1bae3bfdc6c23d1491717f7ad5c96cfc5c0510992c5b28e1818b31a3d9
- resultados/unidades_sem_caixas/cache/detector/2e1bae65dfddf50917a011da.json: 00cfaecdb14f4e78d0f0ea745a140576f8026030d46dd2cc8d8e2db93557396f
- resultados/unidades_sem_caixas/cache/detector/399569ff491c6f02e46b0dc8.json: ccf184194e42b8bf9292578c3561d8eba113dbb5d4d5ea325e6ab036971fbbc5
- resultados/unidades_sem_caixas/cache/detector/3c7415971a4758b329a182c8.json: d07c1e465af87b60bdc1d252d09617f468a1312921188f3562b9e55288940ab4
- resultados/unidades_sem_caixas/cache/detector/3e6312b5bc4c569e7b975bed.json: 90477b9204b55f3d0aa88baf411056d89262f2bc8cccecdd65527179770ce499
- resultados/unidades_sem_caixas/cache/detector/45217f775da443d68b57e643.json: b52d752c52f502ebfe40514dcb628370a33ac55f81c77af0c1e7e32c81191588
- resultados/unidades_sem_caixas/cache/detector/473fb701b2fc4b5943c99d10.json: 836a78ec0c4547c6fc9aa3aa964143493c2b9203952a204663b9cf5feafd0a28
- resultados/unidades_sem_caixas/cache/detector/47b4d13140b313e56ba0bedf.json: 5c16aed9cae55d2c77662d9bc7371024b0d168c163c6ccfe060aaaa8aacaa750
- resultados/unidades_sem_caixas/cache/detector/49b4cc8933803d532df866f8.json: 2ca2692f504b41e850ff9d2722e997191b3b402b1f711cc73d43b1a0f8435f11
- resultados/unidades_sem_caixas/cache/detector/4b1a50a3afe7bc586419e53f.json: 4d6705df148827392e433da452048ace1abab2638cc5ac6a170428ab5056323b
- resultados/unidades_sem_caixas/cache/detector/56cef1c8ec847c46c4363b21.json: 82dc9c61a008d7d6ab3c3ab0b36e9f77194343acea581f3e6a41d0d8d7fc90ea
- resultados/unidades_sem_caixas/cache/detector/5a8b7aa56342d5ddfe6de6d2.json: bcae2417d342f10e7730033c419fca06991e22a625525bc19da78653fe417207
- resultados/unidades_sem_caixas/cache/detector/5ba3c821a80d89a83cf85f0a.json: 26237473d41fca515e7a1ece244ad000e5386365aeb43c4a48e984219c4e7a8d
- resultados/unidades_sem_caixas/cache/detector/5cd18aa43e2f4e16f22b02c6.json: adc91d6c974892217c734ff0c21a56a8d06f710428dcca08a415e5aa16cbbe8f
- resultados/unidades_sem_caixas/cache/detector/654b601bbb8b5e5f1fdf33b7.json: 810aa375eb0c9b93192b0a2b2cd32a63dcca53220e698806fa619496c8da8dd9
- resultados/unidades_sem_caixas/cache/detector/6c60bb94d1e4b8941818c72f.json: 181b7f7acac452105388525637d51f52182c9abdfab6bd7d41ec7edec04fc712
- resultados/unidades_sem_caixas/cache/detector/6faecd5279e23460e5ddf9d3.json: d60e159098bffd0da83f6f95ce89284021ba4f5d4e25c35b0afbc0ead016d84f
- resultados/unidades_sem_caixas/cache/detector/709993f4a51d08375cff98d5.json: ce83e9e7cf80cbbf2f0eaef48fe4cd88515a4e88c53d5f05d7d3bf2bad66b030
- resultados/unidades_sem_caixas/cache/detector/83a24e200b07f8f02978a90d.json: bff81a15cf32ec628a08190593b303d176730311f71d9035fb5d5e39f9b38540
- resultados/unidades_sem_caixas/cache/detector/843152277b3f5b24ba7e382c.json: 326f964c2d7cacfc93c2d54bdf40ee2e1caca48edab14ec60cbeb68650b8e939
- resultados/unidades_sem_caixas/cache/detector/85c78b677407b54a91b6e1fe.json: 9163a3427d510e1095bf5ce748a98128300a3b58bc52c216565e16c19ceb63a4
- resultados/unidades_sem_caixas/cache/detector/873fcf463e5f56d69291c17d.json: 1c8452cdb4859347608dad79b1541f60ec83bea19fe4a05787aaa0a13646e235
- resultados/unidades_sem_caixas/cache/detector/8816e53cb77f2b29f376592e.json: 3434407e58f8309219078eed1252fb777bfe084dc00cca7b0c71360f0fec73fc
- resultados/unidades_sem_caixas/cache/detector/8ac3354a856f83e1f3750dfc.json: 49cc99284dce5eb54af44dcce9a80bbb943d5e5007a10c3e52693d9627d1673c
- resultados/unidades_sem_caixas/cache/detector/92e5734a6ba8aa91b6c81346.json: 5c47dc6d7b2f32b43c64ca5e945c64bb5463d47c643565bcc7ba53e8c040f4d8
- resultados/unidades_sem_caixas/cache/detector/931a89724f47c6dbad055f83.json: 51272cbd3adcf5757346e4823aaa006b49e283f922714350c0dd46806d1637a4
- resultados/unidades_sem_caixas/cache/detector/9569f1d671a81de55f966279.json: f6939c39c2819f4c9535ed3153d69ad61de1cd72354b9488fb992c05c88d4521
- resultados/unidades_sem_caixas/cache/detector/95bb2775e6f43d4c135694cf.json: 5ab4a0269b929a9cae0c97ce3fb51e27d5969f28caca321a6c9745a91cb3d367
- resultados/unidades_sem_caixas/cache/detector/9d83c1aca14f39eef96c9fed.json: fd9ffd45f252057161b14e73aab7a58a41a30a81a5c1a82b4f5188b0ee0a7079
- resultados/unidades_sem_caixas/cache/detector/9e6a0d05edbce5bc1be2cc09.json: aec66ac8bb776f2fc2b1c694183ac8e9fc69f9a7bb39e7abcf43c1817237090b
- resultados/unidades_sem_caixas/cache/detector/a20ba89547f94c0c374c94cd.json: 3861e7c94099beb17b92e05c0ed3b47ec179dfb89291165f1e869f4b7ac1e217
- resultados/unidades_sem_caixas/cache/detector/b12a992bb12be9cb53a3f211.json: f60baca5b81e12dc3d0895e3d957e966bb1a40ac781db29ecef3206dcd2e6104
- resultados/unidades_sem_caixas/cache/detector/b2a5cd50f2cc16be781a7506.json: 18eb986624cd7f1aa89512f0a6579c1c900cdf58ff03acc46d2210e33e3f4bcf
- resultados/unidades_sem_caixas/cache/detector/b6a7139e34b5eeee5f25513c.json: 73b9eba0b3e6015050a33d1e0163a8819f30a3b143e4372cf57b37e5e140f110
- resultados/unidades_sem_caixas/cache/detector/b840b287f4c79d968e606647.json: ea29ba7e2593ef7ecfe0394c76a7f6a91a7784cfdf6c6506cf23f8a89941b98c
- resultados/unidades_sem_caixas/cache/detector/be682ebded1ce32f79b88684.json: e35fd813506e4e71f57722381ff5530b1ab305aeade10b40168b7d800f2560d4
- resultados/unidades_sem_caixas/cache/detector/c91032b5ded3ab401006a804.json: dfba2a84e9951e3266eebc9f6ac88f5dc3437e7fe7807e744ff18eb243959eb0
- resultados/unidades_sem_caixas/cache/detector/d0155d66e9a53f1fb615264f.json: fd70ea2c2bc4f6d7848a439bd97a58712a09fadce96028e45c96a6ed58eb72be
- resultados/unidades_sem_caixas/cache/detector/d05a585bd095c5670cdedf4b.json: 0de5dc9959322fc54e6737c21249644c44730e7f654ede899648a8b2a8202719
- resultados/unidades_sem_caixas/cache/detector/d5e099413a56b331525c1903.json: bd5e97c2f8b6e19e7486bf3b547a454d41856b4b71f0d7d4d02b148e3ba7140c
- resultados/unidades_sem_caixas/cache/detector/d5e0abadd9cabd3cc55059e5.json: 22d4473c26777e2a88f95fa62902e1e065f9a45628e77ed1520b2462fa9c8b8e
- resultados/unidades_sem_caixas/cache/detector/d694ca87d46d1d9a88c24302.json: 5bb6cd9e0312b09216b4da210635fd6765e9035d8da035ef3cff8624a0362a1c
- resultados/unidades_sem_caixas/cache/detector/dfa77e04a34cf87477b8111b.json: 4a402f2a408062b06ae90a899abfb14c47bfc1715edd481e385320e6bd8a5687
- resultados/unidades_sem_caixas/cache/detector/e052f3155014fb29851dda94.json: f997745d3db1f6cffe29adf8b344b26f9156b82b8439fbfd491ec4ecf4c53db3
- resultados/unidades_sem_caixas/cache/detector/e07ec9123744da9f75622bc6.json: 332ea5f91143162584f3941f7fb7aeecd9cfed0a543c7814c40384e3d61978a4
- resultados/unidades_sem_caixas/cache/detector/e8693eab591bf300a756723e.json: 6de66f537e6377237866067e798c59efc8907c8b224a47962c7579273a556ef6
- resultados/unidades_sem_caixas/cache/detector/e8f17eba337f089fe4563456.json: cf1097c7872cec3f1f4da2a32a0ea1318cf6a92de5a591214d26ca095edd99e3
- resultados/unidades_sem_caixas/cache/detector/ecc39b755dd39365f1d575d2.json: d74efa6ba28ab7a059e36aa29ac964df871298417a5cd2635b8bb3d9917b12e7
- resultados/unidades_sem_caixas/cache/detector/f3791c914e59f43f70b1f2cf.json: ec32f45a3d522917c794fa1c60e6a8c1361519441eeb095bd73c6e6778ee0304
- resultados/unidades_sem_caixas/cache/detector/f8c4ac1ef2e8bf534782db00.json: 26ca50c1df6897b0937261053ad30b5c8bbc065bcaef89474d4a4317d05d0eba
- resultados/unidades_sem_caixas/cache/detector/f92f64f16fc819255f28110b.json: 3c099fef38c518da00d6fd3914faa36cda6b03ad78ae12e53592881e39118ef3
- resultados/unidades_sem_caixas/cache/detector/fca281bde0cb65d71407c24a.json: a116bed16274bd29fcfd9584f84cd7d4853965e54c98d29927039b45e7503e73
- resultados/unidades_sem_caixas/cache/detector/fe2075081668f517c8b9cbb6.json: dec1eace36dcf988aaa7f972cb0b81635d6b2dc79fd0394a4610a94eeb80a0b2
- src/data/dataset_sem_caixas_finas.py: c7d890a4d3f3747c786b3ed7159f2ef979d7163ecb65d38923a33e3af4f48df4
- src/data/estruturas_pagina.py: 80318e9ddbf049fcacbc2d58647ad4b4093e5eaf35197ed3a4e4b9999cb7e18b
- src/data/extrator.py: c4d86890b89c13d154475129e9e2ce1bf073b84680317e04b9550e79748daa35
- src/data/regioes.py: d1af2d7bb5d663c2dfeacf46f10a01180fce17487f3e9fd06ab8c8138b5ed8ae
- src/eval/baselines.py: 634d6441b9f6850eae5f477199dd7b8c47d6814822478505abf2b9597f8bdaff
- src/eval/metrics.py: 9a84261a7ceaf65e2263c5754fee09f9a54dd1019752271332943064922fe3d7
- src/eval/politica_margens.py: 45c3796236d98ee350b82f30b192a0b614bb164fb56dacdc2cb2700900509b33
- src/eval/protocolo.py: 4fadd8fc523408dfc1aebac7e6f3faf85d8c3eb1e63acc9d1be6f8ee49625ba0
- src/ri/piloto_japeri.py: 69bf69e12132ef8dff00ef56aea4546a32eed63ddbb9064da5bad603414309c9

Comando desta configuração: `venv/Scripts/python.exe -B orquestracao/analises/extrator_sem_paragrafos_v2.py --sem-d --iteracao 2`.

RAM livre mínima observada: 3366,1 MB; duração desta execução: 81,8 s.

Sem exportação final aprovada. As unidades candidatas ficam nos caches por página; a exportação produzida pela implementação inicial foi arquivada em extrator_sem_paragrafos_v2/unidades_iniciais/.
