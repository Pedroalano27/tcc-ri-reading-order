# Piloto de RI em Japeri: a ordem de leitura muda a busca?

269 páginas de 27 edições; 335 dos 421 atos anotados têm a edição no acervo. Consultas com página relevante: 326 do tipo frase, 266 do tipo titulo, 323 do tipo termos.

**Controle (página inteira como documento):** MRR@10 = 0,991 (frase), 0,987 (titulo), 0,995 (termos), idêntico para todos os métodos, porque o saco de palavras da página não depende da ordem.

**Frases preservadas por pelo menos um método:** 54,6%. O restante provavelmente difere entre o texto dos atos e a camada de texto do PDF (hifenização, OCR) ou atravessa páginas.

| Método | Frases preservadas | Diferença para o piso | Contexto para RAG | MRR@10 frase | MRR@10 título | MRR@10 termos |
|---|---:|---:|---:|---:|---:|---:|
| Ordem do detector (sem ordenar) | 45,4% | +0,0 p.p. | 44,8% | 0,988 | 0,994 | 0,982 |
| Fluxo do PDF (extração comum) | 53,4% | +8,0 p.p. | 52,8% | 0,998 | 0,994 | 0,997 |
| Ingênua (topo→base, esq.→dir.) | 48,8% | +3,4 p.p. | 48,5% | 0,997 | 0,991 | 0,991 |
| XY-cut (heurística de colunas) | 49,7% | +4,3 p.p. | 49,4% | 0,998 | 0,994 | 0,995 |
| LayoutLM: texto + layout 2D | 45,7% | +0,3 p.p. | 44,8% | 0,997 | 0,994 | 0,994 |

Frases preservadas: % das frases de 12 palavras dos atos que aparecem com ao menos 10 palavras alinhadas no texto da página produzido pelo método. Piso: blocos na ordem em que o detector os entrega. Contexto para RAG: % das consultas-frase em que o primeiro trecho devolvido contém a frase preservada. Busca por trechos: BM25 em janelas de 100 palavras (passo 50); a página vale o seu melhor trecho.
