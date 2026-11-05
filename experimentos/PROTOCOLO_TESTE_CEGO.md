# Protocolo da avaliação confirmatória no teste cego (E001)

**Estado: APROVADO pelo Pedro em 04/11/2026, com a regra 3b.** Nada aqui foi aplicado; o teste cego continua lacrado
(`experimentos/TESTE_CEGO.lock`) e ainda não tem gabarito humano. Este documento precisa ser aprovado
**antes** de qualquer avaliação nas 90 páginas, e depois disso não muda.

Origem: `docs/PLANO_PESQUISA.md` (seção 4), recomendação do ChatGPT na consulta 01
(`experimentos/consultas/2026-11-02_chatgpt_01_resposta.md`) e o diagnóstico de τ de 03/11
(`resultados/diagnostico_tau_v3/RELATORIO.md`), que mostrou que, nas mesmas ordens, o sinal de Δτ pode
mudar conforme se pondere palavras, linhas ou unidades.

## 1. Desfechos

- **Primário:** quebras por página (régua `corretor_de_transicoes.medir`, a mesma de todas as bancadas).
- **Controle de ordem global:** τ de Kendall de palavras, média por página (régua atual).
- **Sensibilidades (pré-especificadas, todas as páginas, mesmos métodos):** τ de linhas da referência com
  peso igual; τ de unidades com peso igual; medianas por página e mediana dos Δ pareados; sucessor de
  linhas; reparos/regressões de sucessores; fidelidade de 12; cobertura de palavras.
- **Estrato pré-especificado:** páginas cuja maior unidade tem > 20% das palavras. Publicar os dois
  estratos sem excluir páginas; os estratos não mudam a decisão.

## 2. Comparações

- Finalistas: no máximo 3 métodos, congelados (código, pesos e limiares com hash) antes de abrir o teste.
  Hoje: **híbrido 67** (baseline a superar), **regra de colunas** (âncora) e **HIER-1** (E017, GO em
  05/11; código e modelo congelados em `resultados/e017_hier1_externas/congelamento.json`).
- Contraste principal: candidato − híbrido 67 em quebras por página.
- Agregação: macro-média das 3 UFs (CE, MA, RJ, 30 páginas cada); IC95 do Δ por bootstrap de PDFs
  (5.000 reamostras, semente 20261102); Holm se houver mais de um contraste confirmatório.

## 3. Critério de superioridade

Redução ≥ 10% nas quebras (macro-UF) **e** IC95 do Δ < 0 **e** nenhuma UF pior em mais de 0,5 quebra/página
(estes três vêm do plano) **e**, proposta nova, τ de palavras não inferior ao híbrido com margem de
0,005 (acrescentada porque os candidatos de novembro trocaram quebras por τ). Sem candidato que passe, o resultado
confirmatório é "híbrido 67 vs regra" e os demais métodos entram no texto como exploratórios.

## 3b. Regra de decisão co-primária (proposta da consulta 03 ao ChatGPT, para variantes novas)

Para qualquer candidato novo (ex.: decodificação hierárquica, E016), as duas condições valem juntas, por
interseção — sem escore composto que compense perda de τ com ganho de quebras:
1. **Segurança:** limite inferior do IC95 pareado de Δτ (candidato − híbrido 67) ≥ −0,005.
2. **Superioridade:** limite superior do IC95 de Δquebras (candidato − híbrido 67) < 0.
3. **Robustez (obrigatório reportar, não decide):** Δ por UF, páginas com regressão grave, distribuição dos
   deslocamentos.
Bootstrap agrupado por PDF e estratificado por UF. Os NÃO GO já registrados (E004, E005, E006, E014, E015)
continuam NÃO GO. Fonte: `experimentos/consultas/2026-11-03_chatgpt_03_resposta.md`, seção 2.

Se esta regra for aprovada, ela substitui a margem "τ médio ≥ híbrido − 0,005" do item 3 por uma versão
mais exigente (limite do IC, não a média) — decidir antes de abrir o teste.

## 4. Execução

Uma única vez, pelo orquestrador (Claude), depois de: (a) gabarito humano das 90 páginas pronto;
(b) este protocolo aprovado; (c) finalistas congelados. Nenhum agente abre as páginas antes disso.
Relatório com todos os desfechos, inclusive os desfavoráveis.

## Aprovação

- [x] Pedro aprovou em 04/11/2026, com a regra co-primária 3b (substitui a margem pela média do item 3). Sem outras alterações.
