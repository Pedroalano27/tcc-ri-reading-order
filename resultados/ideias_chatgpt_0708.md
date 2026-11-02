# Ideias do ChatGPT (GPT-6.1 Sol) para o TCC — 07/10/2026 ~23:50

Conversa completa (pedida pelo Pedro, contexto sem dados do parceiro): https://chatgpt.com/c/6ac7003c-0800-83e9-806f-318f4f8800f6
Leitura feita pelo Claude com `get_page_text` no Chrome. Abaixo, só o resumo do que é aproveitável; as estimativas de
retorno são opinião do modelo, não medição.

## Frente A — extração sem parágrafos
1. **Calhas locais, não globais:** ocupação horizontal em janelas verticais sobrepostas (8 a 15 alturas de linha),
   pontuar cada vão por largura, persistência vertical e texto dos dois lados; rejeitar "colunas" estreitas sem
   suporte. Só depois formar linhas dentro de cada zona. (Já temos `vales_locais`; falta o critério de suporte e
   persistência, que é exatamente o defeito das faixas estreitas.)
2. **Hierarquia página → zona → coluna → linhas**, com título transversal como barreira (colunas acima, título, colunas
   abaixo). Distinguir título, tabela e quadro transversais.
3. **Objetos nativos do PDF:** `get_drawings()` do PyMuPDF para traços verticais (separadores de coluna) e
   retângulos (tabelas, quadros); `find_tables()`; imagens posicionadas para logo e brasão; fonte e estilo dos spans.
4. **Posse de palavras e tabela × lista de nomes:** exigir mais de um alinhamento de colunas e/ou grade vetorial;
   exemplos negativos difíceis (listas de servidores, assinaturas); na dúvida marcar "incerto".
5. **Concorrentes de detector:** DocLayout-YOLO (rodando no Kaggle esta noite) e Docling Heron (já usado nos átomos).

## Frente B — ordenador aprendido
1. Pequeno conjunto humano independente; medir ordem isolada (mesmas linhas corrigidas) e pipeline completo.
2. **Aprender correções locais da regra** (melhor aposta imediata): candidatos por transição ambígua + classificador de
   pares leve; medir ANTES o recall do conjunto de candidatos (ele limita o resultado).
3. Hierarquia: encoder local por região + encoder global sobre colunas/zonas/tabelas; embedding textual curto
   pré-calculado por linha.
4. Perda de sucessor + ranking de precedência, negativos difíceis, balanceamento por tipo de transição; decodificação
   com restrição (sem ciclos).
5. Referência derivada como supervisão fraca (peso menor); aumento de dados que preserva a ordem.

## Frente C — anotação
- **LAREX** (caixas, classes e ordem no mesmo fluxo), **eScriptorium** (ordem de linhas por arrastar), **CVAT**
  (ordem só como atributo numérico). Piloto de 10 páginas medindo o tempo real por página.
- Pré-anotação completa importada e correção só das diferenças; guardar hash do PDF, dimensões e transformação
  PDF → imagem (cuidado com recorte e rotação).
- Conversor explícito para o Label Studio: caixa = `rectanglelabels`, ordem absoluta = `Number` com `perRegion`,
  pré-anotação em `predictions`, final em `annotations`, coordenadas em % da imagem. Testar uma página completa de
  ida e volta antes de converter tudo.
- Protocolo de ordem escrito e dupla anotação de uma amostra.

## O que o Claude já sabia e o que é novo
- Já sabíamos: representação em linhas, calhas por projeção, conversão para o formato do Label Studio.
- Novo e barato: (A3) usar as linhas e retângulos vetoriais do PDF; (A1) critério de suporte/persistência das calhas;
  (B2) corrigir só as transições ambíguas da regra, medindo antes o recall de candidatos; (C) LAREX como alternativa.
- Ressalva do próprio ChatGPT: o híbrido de 67 linhas ainda não prova superioridade sobre a regra no mesmo conjunto.

## Decisões da noite a partir disso
- Codex (cota voltou): treinador com texto, extrator v2 (A1 a A4) e corretor de transições (B2).
- Antigravity: auditoria, lote classificável e classificador simples (já rodando).

## Seguimento 08/10 (02:45) — 3 experimentos baratos propostos pelo ChatGPT
Pergunta: com os resultados da noite (extrator v2 sem efeito em linhas; 50% das quebras da regra em margens no golden_v4;
variante de margens com ganho pequeno e não conclusivo; recall de candidatos 96-98%), qual a melhor próxima descoberta.
1. **Margens por repetição entre páginas + veto de corpo** (60-90 min, CPU): linhas recorrentes no mesmo PDF (texto
   normalizado sem números de página e datas + posição + estilo; pares e ímpares) como evidência de cabeçalho/rodapé,
   posição extrema só como candidato; veto de corpo para linha alinhada à coluna com continuidade e estilo compatíveis;
   cabeçalho composto lido por faixas horizontais, da esquerda para a direita; marcas laterais com 2 políticas fixas
   (ancorar na zona ou fluxo final). Sucesso: recuperar >= 25% dos 47 sucessores de corpo marginalizado, saldo positivo
   fora do ajuste. Risco: títulos recorrentes do corpo; páginas sem vizinhas.
2. **Diagnóstico de candidatos e reordenação restrita na coluna** (45-75 min, CPU): separar erros (sucessor fora dos
   candidatos, em outra coluna, na mesma coluna); alertas sem usar a referência (salto sobre linhas próximas, retorno
   vertical, mudança de alinhamento, travessia de objeto); janelas de 4-8 linhas só nos alertas; alternativas por mover
   uma linha ou trocar vizinhos; calcular o ORÁCULO das alternativas (teto); abandonar se o oráculo não melhora.
3. **Regra + modelo textual com intervenção seletiva** (60-90 min após o checkpoint): o modelo só altera a regra onde há
   alerta geométrico, discordância e vantagem de score acima de um limiar escolhido na validação; curva fração de
   transições alteradas x quebras finais; contar reparos e regressões. Se nenhum limiar dá saldo positivo fora do
   ajuste, a descoberta é que o modelo ainda não serve de corretor seletivo.
Observação do ChatGPT: os 27 casos do golden_v3_novo já foram consultados; servem de comparação externa, mas deixaram
de ser teste totalmente intocado.
