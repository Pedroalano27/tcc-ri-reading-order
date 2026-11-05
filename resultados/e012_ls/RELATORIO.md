# E012 — bancada humana Data Policy (seed 2)

Gerado por `orquestracao/analises/e012_bancada_ls.py`. Só agregados: os dados e as predições por página são do projeto parceiro (uso autorizado, não publicado) e ficam fora do git.

Montagem: `{"paginas": 123, "pagina_vazia": 3}`. Veículos: 29.

## todas (123 páginas, 29 veículos)

| Método | τ | Quebras/pág | Sucessor | Δ quebras vs híbrido [IC95 veículo] | Δ τ vs híbrido [IC95 veículo] |
|---|---:|---:|---:|---:|---:|
| regra | 0,9538 | 8,577 | 0,8863 | +1,398 [+0,326; +2,485] | -0,0157 [-0,0455; +0,0028] |
| hibrido67 | 0,9695 | 7,179 | 0,9311 | — | — |
| grafo_e004 | 0,9090 | 6,675 | 0,9201 | -0,504 [-2,103; +0,625] | -0,0605 [-0,1202; -0,0191] |
| hier1 | 0,9561 | 6,976 | 0,9165 | -0,203 [-1,717; +0,992] | -0,0134 [-0,0432; +0,0049] |

## sem copia comprovada da pre-anotacao (108 páginas, 28 veículos)

| Método | τ | Quebras/pág | Sucessor | Δ quebras vs híbrido [IC95 veículo] | Δ τ vs híbrido [IC95 veículo] |
|---|---:|---:|---:|---:|---:|
| regra | 0,9498 | 9,167 | 0,8943 | +1,426 [+0,348; +2,570] | -0,0156 [-0,0505; +0,0045] |
| hibrido67 | 0,9654 | 7,741 | 0,9295 | — | — |
| grafo_e004 | 0,8968 | 7,278 | 0,9189 | -0,463 [-2,190; +0,810] | -0,0686 [-0,1369; -0,0221] |
| hier1 | 0,9505 | 7,611 | 0,9149 | -0,130 [-1,769; +1,201] | -0,0149 [-0,0497; +0,0052] |

Viés conhecido: a referência partiu de uma pré-anotação XY-cut; páginas aceitas sem mudança favorecem ordens parecidas com a regra. 15 páginas têm cópia comprovada da pré-anotação; nas demais a origem não pôde ser verificada. O segundo estrato exclui as 15 comprovadas.
