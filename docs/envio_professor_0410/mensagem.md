# Rascunho da mensagem para o professor

Anexos: `resumo.pdf` (3 páginas, 3 MB) e `comparador_golden_v4.zip` (14 MB; dentro há um único HTML que abre no
navegador). Se for por WhatsApp, o PDF vai direto e o zip vai como documento.

---

Professor, boa noite.

Seguem os resultados desta semana sobre a ideia de não dividir o texto em caixas finas, deixando como bloco só
tabela e imagem e organizando o texto por colunas.

1. Nas 71 páginas com ordem anotada, as quebras de leitura caíram de 16,1 para 7,3 por página em relação ao
   pipeline atual (caixas finas + XY-cut), e o τ de palavras subiu de 0,830 para 0,976.
2. A maior parte desse ganho (71%) também aparece mantendo as caixas e apenas tratando cabeçalho e rodapé à parte
   (9,9 quebras por página). Entre essas duas alternativas a diferença ainda não é estatisticamente clara: a
   proposta ganha muito em poucas páginas densas e perde um pouco em várias simples.
3. O que a proposta resolve de fato são os erros que nascem dentro das caixas e que nenhuma reordenação conserta:
   213 no pipeline atual contra 29.
4. Testei um ordenador neural pronto (LayoutReader, sem retreino) sobre as novas unidades e ele ficou abaixo da
   ordenação geométrica (τ 0,898 contra 0,986 nas mesmas 44 páginas).
5. No extrator, o detector treinado no dataset anotado do Label Studio levou o F1 de localização de 0,573 para
   0,763 a 0,799 nas 317 páginas de teste.

O PDF tem as tabelas, as limitações e três pontos em que eu queria a sua opinião. O HTML do zip é um comparador
interativo das 45 páginas do Golden, lado a lado, nas representações antiga e nova.

Abraço,
Pedro
