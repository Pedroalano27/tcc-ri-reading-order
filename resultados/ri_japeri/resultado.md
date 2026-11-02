# Piloto de RI em Japeri: a ordem de leitura muda a busca?

269 páginas de 27 edições; 335 dos 421 atos anotados têm a edição no acervo. Consultas com página relevante: 281 do tipo frase, 266 do tipo titulo, 310 do tipo termos.

**Controle (página inteira como documento):** MRR@10 = 0,991 (frase), 0,987 (titulo), 0,995 (termos), idêntico para todos os métodos, porque o saco de palavras da página não depende da ordem.

**Frases preservadas por pelo menos um método:** 92,2%. O restante provavelmente difere entre o texto dos atos e a camada de texto do PDF (hifenização, OCR) ou atravessa páginas.

| Método | Frases preservadas | Diferença para o piso | Contexto para RAG | MRR@10 frase | MRR@10 título | MRR@10 termos |
|---|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 85,1% | +0,0 p.p. | 82,9% | 0,991 | 0,992 | 0,990 |
| Fluxo do PDF (extração comum) | 92,2% | +7,1 p.p. | 91,8% | 1,000 | 0,994 | 0,991 |
| Ingênua (topo→base, esq.→dir.) | 88,3% | +3,2 p.p. | 87,2% | 1,000 | 0,996 | 0,992 |
| XY-cut (heurística de colunas) | 89,3% | +4,3 p.p. | 87,9% | 1,000 | 0,996 | 0,992 |
| LayoutLM pontual | 85,8% | +0,7 p.p. | 85,1% | 1,000 | 0,988 | 0,994 |
| LayoutLM sucessor | 90,4% | +5,3 p.p. | 89,7% | 1,000 | 0,992 | 0,993 |

Frases preservadas: % das frases de 12 palavras dos atos que aparecem com ao menos 10 palavras alinhadas no texto da página produzido pelo método. Piso: blocos na ordem em que o detector os entrega. Contexto para RAG: % das consultas-frase em que o primeiro trecho devolvido contém a frase preservada. Busca por trechos: BM25 em janelas de 100 palavras (passo 50); a página vale o seu melhor trecho.
