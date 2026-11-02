# Guia de ordem de leitura sobre as regiões do Diamond

Este guia serve a **duas** coisas ao mesmo tempo: é a instrução para o Pedro ordenar as páginas do
`golden_v4` e é, palavra por palavra, a instrução que o ordenador por VLM (`src/eval/vlm_ordem.py`)
recebe. As regras entre os marcadores `regras:inicio` e `regras:fim` são lidas pelo script; mudar uma
regra aqui muda as duas coisas. Assim, humano e modelo são avaliados contra o **mesmo** critério.

Ele complementa o `GUIA_ANOTACAO.md` (o da ordem sobre os blocos do extrator v3). A diferença: no
`golden_v4` as caixas são as **regiões corrigidas à mão no Diamond**, cada uma com classe (título,
texto, lista, tabela, assinatura, cabeçalho, rodapé, figura, outro). Não há mais "bloco que mistura
colunas": a segmentação já foi conferida. Regiões **sem nenhuma palavra na camada de texto do PDF**
(brasão, foto, cartaz com o texto desenhado na imagem) não entram no lote: todos os métodos ordenam
texto e precisam receber os mesmos blocos. Para leitor de tela elas contariam (texto alternativo), mas
isso fica fora desta medida.

## Como anotar

```bash
venv\Scripts\python.exe src\anotacao\servidor.py
```

Escolha o lote **`golden_v4`**. A ferramenta é a mesma do Golden (clique ou laço numera, `Z` desfaz,
`Enter` conclui). A cor da caixa não indica ordem; tabela continua com contorno verde.

## Por que estas regras

Resumem três fontes: (1) as regras que o Pedro já usou nos lotes `golden_v1` e `golden_v2`
(`docs/GUIA_ANOTACAO.md`); (2) o critério de **sequência significativa** das diretrizes de
acessibilidade — WCAG 2.2, critério 1.3.2 (*Meaningful Sequence*): quando a ordem muda o sentido, a
sequência de leitura correta precisa ser determinável —, que é o que um leitor de tela percorre, e o
requisito de **ordem lógica de leitura** da estrutura de tags do PDF/UA (ISO 14289-1); (3) a
convenção de leitura de jornais e diários em colunas (páginas "Manhattan"): coluna inteira de cima
para baixo, seções separadas por títulos que atravessam as colunas, matéria que continua na coluna
seguinte.

<!-- regras:inicio -->
1. Leia como uma pessoa leria a página impressa para entender o conteúdo, do começo ao fim.
2. Cabeçalho do diário (nome do diário, órgão, data, edição, número da página no topo) vem primeiro,
   de cima para baixo e da esquerda para a direita. Rodapé do diário (número da página, endereço,
   autenticação) vem por último.
3. Em várias colunas, leia a coluna da esquerda inteira, de cima para baixo, e depois a próxima.
4. Uma região larga que atravessa as colunas (título de seção, faixa, tabela larga) separa a página em
   seções: leia tudo o que está acima dela, coluna por coluna, depois ela, depois as colunas abaixo.
5. Um ato que continua no pé de uma coluna segue no topo da coluna seguinte; confirme que o texto emenda.
6. Dentro de um ato, siga a ordem impressa: título, ementa, texto, campos, local e data, assinatura. A
   assinatura pertence ao ato: vem logo depois dele e antes do próximo título.
7. Tabela e lista são uma unidade: entram no ponto em que são lidas, em geral logo depois do título ou do
   parágrafo que as apresenta.
8. Só há caixas com texto: brasão, foto e cartaz cujo texto está só na imagem ficam fora da ordem. Uma
   figura com texto (carimbo, selo) entra onde aparece no fluxo.
9. Legenda e nota de margem são lidas junto do trecho que acompanham.
10. Região da classe "outro" (lixo da camada de texto, marcas de diagramação) vai para o fim, logo
    antes do rodapé.
11. Com duas leituras igualmente plausíveis, escolha a que segue a ordem das colunas e marque a página
    como ambígua.
<!-- regras:fim -->

## Cuidados metodológicos

- **Anotação cega:** a ferramenta não mostra nenhuma ordem automática, e os identificadores são
  embaralhados. Não olhe as predições do VLM ou dos outros métodos antes de terminar o lote.
- **Mesma régua:** o prompt do VLM usa exatamente as regras acima. Se uma regra mudar depois de o VLM
  rodar, rode o VLM de novo.
- **Segmentação × ordem:** as 20 páginas do `diamond_piloto` já foram ordenadas no `golden_v3` sobre os
  blocos do extrator v3. Ordená-las de novo sobre as regiões do Diamond permite medir quanto a
  segmentação muda a ordem e os métodos — com a ressalva de que é a mesma pessoa, que já viu essas páginas.
