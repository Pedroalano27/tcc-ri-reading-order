"""Seletor simples entre a regra de colunas e o LayoutReader pronto, pela densidade da página.

Motivo (resultados/ordenadores_ganha_perde.md, seção C): em `linhas`, o LayoutReader pré-treinado erra
menos que a regra nas páginas com poucas unidades e desaba nas densas. Aqui o limiar de unidades é
escolhido SÓ no golden_v4 (desenvolvimento) e medido no golden_v3 novo e no teste silver.
Não roda modelo: usa as medições por página de resultados/ordenadores_sem_caixas.json.
Uso: venv/Scripts/python.exe -B orquestracao/analises/hibrido_regra_layoutreader.py
"""
import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BANCADAS = ("golden_v4", "golden_v3_novo", "teste_silver")


def br(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def main():
    d = json.loads((RAIZ / "resultados/ordenadores_sem_caixas.json").read_text(encoding="utf-8"))["resultados"]

    def paginas(ordenador, bancada):
        return {p["page_id"]: p for p in d[f"{ordenador}__linhas__{bancada}"]["paginas"]}
    dados = {b: (paginas("regra_colunas", b), paginas("layoutreader_pronto", b)) for b in BANCADAS}

    def medir(bancada, limiar):
        regra, lr = dados[bancada]
        linhas = []
        for pid, pr in regra.items():
            escolhido = lr[pid] if pr["unidades"] <= limiar else pr
            linhas.append((pr["uf"], escolhido["metricas"], pr["metricas"], lr[pid]["metricas"]))
        return linhas

    def media(linhas, i, chave):
        return sum(x[i][chave] for x in linhas) / len(linhas)

    candidatos = sorted({p["unidades"] for p in dados["golden_v4"][0].values()})
    melhor = min(candidatos, key=lambda t: (media(medir("golden_v4", t), 1, "quebras"), t))

    def ic(linhas, chave, n=5000):
        # bootstrap agrupado por veículo da diferença híbrido - regra
        por_uf = {}
        for uf, h, r, _ in linhas:
            por_uf.setdefault(uf, []).append(h[chave] - r[chave])
        ufs = sorted(por_uf)
        rng = random.Random(20261005)
        difs = []
        for _ in range(n):
            am = [v for u in (rng.choice(ufs) for _ in ufs) for v in por_uf[u]]
            difs.append(sum(am) / len(am))
        difs.sort()
        return difs[int(.025 * n)], difs[int(.975 * n)]

    out = ["# Híbrido por densidade: LayoutReader pronto nas páginas leves, regra de colunas nas densas", "",
           "Gerado por `orquestracao/analises/hibrido_regra_layoutreader.py` a partir das medições por página de",
           "`resultados/ordenadores_sem_caixas.json` (representação `linhas`). Nenhum modelo foi rodado de novo.", "",
           f"Limiar escolhido **só no golden_v4**: usar o LayoutReader quando a página tem até **{melhor} unidades**",
           "(linhas, tabelas e imagens); acima disso, a regra de colunas. O golden_v3 novo e o teste silver não",
           "participaram da escolha.", "",
           "| Bancada | n | Páginas no LayoutReader | Regra: τ / quebras | LayoutReader: τ / quebras | Híbrido: τ / quebras | Δ quebras híbrido − regra [IC 95% por veículo] | Híbrido melhor / igual / pior |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for b in BANCADAS:
        L = medir(b, melhor)
        n_lr = sum(p["unidades"] <= melhor for p in dados[b][0].values())
        lo, hi = ic(L, "quebras")
        g = sum(h["quebras"] < r["quebras"] for _, h, r, _ in L)
        e = sum(h["quebras"] == r["quebras"] for _, h, r, _ in L)
        dif = media(L, 1, "quebras") - media(L, 2, "quebras")
        out.append(f"| {b} | {len(L)} | {n_lr} | {br(media(L, 2, 'tau'), 3)} / {br(media(L, 2, 'quebras'))} | "
                   f"{br(media(L, 3, 'tau'), 3)} / {br(media(L, 3, 'quebras'))} | "
                   f"{br(media(L, 1, 'tau'), 3)} / {br(media(L, 1, 'quebras'))} | "
                   f"{br(dif)} [{br(lo)}; {br(hi)}] | {g} / {e} / {len(L) - g - e} |")
    out += ["", "Sensibilidade do limiar no golden_v4 (quebras por página do híbrido):", "",
            "| Limiar (unidades) | " + " | ".join(str(t) for t in candidatos[::4]) + " |",
            "|---|" + "---:|" * len(candidatos[::4]),
            "| Quebras | " + " | ".join(br(media(medir("golden_v4", t), 1, "quebras")) for t in candidatos[::4]) + " |", "",
            "Limitações: o limiar foi escolhido nas mesmas 44 páginas em que a regra de colunas foi desenvolvida;",
            "o golden_v3 novo tem 27 páginas; no teste silver a referência é o fluxo do PDF e o piso de quebras é",
            "alto por causa da ordem dentro das tabelas. É uma pista para testar, não um método validado."]
    (RAIZ / "resultados/hibrido_regra_layoutreader.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[5:13]))


if __name__ == "__main__":
    main()
