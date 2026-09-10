"""
Gera as figuras do TCC em docs/figuras/ (PNG, 200 dpi).

Paleta: instancia de referencia validada (skill de dataviz). Cada metodo tem
uma cor FIXA em todas as figuras -- a cor segue a entidade, nunca a posicao.
No grafico de dispersao (todas as combinacoes de pares em cena) usam-se no
maximo duas cores, com rotulo direto em cada ponto.

Uso:
    python src/eval/figuras.py
"""
from __future__ import annotations

import os
import sys
import csv
import json
import statistics
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
from src.eval.protocolo import carregar_splits, carregar_particao, DIR_RESULTADOS  # noqa: E402
from src.eval.metrics import kendall_tau  # noqa: E402

DIR_FIG = os.path.join(RAIZ, "docs", "figuras")

SUPERFICIE, TEXTO, TEXTO2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
NEUTRO = "#8f8e89"
COR = {                        # ordem fixa dos slots categoricos da paleta de referencia
    "layoutlm": "#2a78d6",
    "xycut": "#eb6834",
    "naive": "#1baf7a",
    "lstm_geo_texto": "#eda100",
    "layoutlm_sem_layout": "#e87ba4",
    "llm_llava_7b": "#008300",
    "lstm_geo": "#4a3aa7",
    "lstm_texto": "#e34948",
    "aleatoria": NEUTRO,
}
ROTULO = {
    "aleatoria": "Ordem do detector", "naive": "Ingenua", "xycut": "XY-cut",
    "lstm_texto": "BiLSTM texto", "lstm_geo": "BiLSTM geometria", "lstm_geo_texto": "BiLSTM texto+geo",
    "layoutlm_sem_layout": "LayoutLM sem layout", "layoutlm": "LayoutLM", "llm_llava_7b": "LLM llava:7b",
}


def estilo():
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO2, "xtick.color": TEXTO2, "ytick.color": TEXTO2,
        "text.color": TEXTO, "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "legend.frameon": False,
    })


def salvar(fig, nome):
    os.makedirs(DIR_FIG, exist_ok=True)
    caminho = os.path.join(DIR_FIG, nome)
    fig.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {caminho}")


def curto(uf):
    return uf.replace("official_diary_", "").replace("_", " ").upper() if len(uf) < 22 else \
        uf.replace("official_diary_", "").replace("_", " ").title()


# ---------------------------------------------------------------------------

def fig_caracterizacao():
    with open(os.path.join(DIR_RESULTADOS, "caracterizacao.json"), encoding="utf-8") as f:
        c = json.load(f)
    por_uf, splits = c["por_uf"], c["splits"]
    papel = {u: "teste" for u in splits["teste"]} | {u: "validacao" for u in splits["validacao"]} | \
            {u: "treino" for u in splits["treino"]}
    ufs = sorted(por_uf, key=lambda u: por_uf[u]["tau_naive_stream_med"])
    fig, ax = plt.subplots(figsize=(8.2, 0.28 * len(ufs) + 1.6))
    for k, u in enumerate(ufs):
        a, b = por_uf[u]["tau_naive_stream_med"], por_uf[u]["tau_xycut_stream_med"]
        ax.plot([a, b], [k, k], color=GRADE, lw=2, zorder=1)
        ax.text(1.04, k, papel.get(u, "nao confiavel"), va="center", fontsize=8, color=TEXTO2,
                transform=ax.get_yaxis_transform())
    ax.scatter([por_uf[u]["tau_naive_stream_med"] for u in ufs], range(len(ufs)), s=34,
               color=COR["naive"], edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label="Ingenua (topo-base, esq-dir) vs. fluxo do PDF")
    ax.scatter([por_uf[u]["tau_xycut_stream_med"] for u in ufs], range(len(ufs)), s=34,
               color=COR["xycut"], edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label="XY-cut (colunas) vs. fluxo do PDF")
    ax.axvline(splits["limiar_tau"], color=TEXTO2, lw=1, ls=(0, (3, 3)), zorder=2)
    ax.text(splits["limiar_tau"], len(ufs) - 0.2, f" limiar de confiabilidade (tau={splits['limiar_tau']})",
            fontsize=8, color=TEXTO2, va="bottom")
    ax.set_yticks(range(len(ufs)), [curto(u) for u in ufs], fontsize=8)
    ax.set_xlabel("tau de Kendall mediano entre as ordens (1 = mesma ordem)")
    ax.set_xlim(min(-0.1, min(por_uf[u]["tau_naive_stream_med"] for u in ufs) - 0.05), 1.02)
    ax.set_title("Concordancia entre as ordens candidatas e o fluxo do PDF, por veiculo")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", visible=False)
    salvar(fig, "fig1_caracterizacao_por_veiculo.png")


def fig_pagina_exemplo():
    import pdfplumber
    splits = carregar_splits()
    ref = splits["referencia"]
    candidatas = [p for p in carregar_particao("teste")
                  if p["stats"]["n_colunas"] == 2 and 12 <= p["stats"]["n_blocos"] <= 30
                  and kendall_tau(p["ordens"]["xycut"], p["ordens"][ref]) >= 0.95]
    if not candidatas:
        candidatas = [p for p in carregar_particao("teste") if 10 <= p["stats"]["n_blocos"] <= 40]
    p = min(candidatas, key=lambda p: kendall_tau(p["ordens"]["naive"], p["ordens"][ref]))
    caminho_pdf = os.path.join(RAIZ, "data", "raw", p["uf"], *p["arquivo"].split("/"))
    res = 90
    with pdfplumber.open(caminho_pdf) as pdf:
        img = pdf.pages[p["pagina"]].to_image(resolution=res).original
    esc = res / 72.0
    caixa = {c["id"]: c["bbox"] for c in p["bounding_boxes"]}

    fig, eixos = plt.subplots(1, 2, figsize=(12, 9.2))
    for ax, (titulo, ordem) in zip(eixos, [
            (f"Ordem ingenua (topo-base, esq-dir)  -  tau = "
             f"{kendall_tau(p['ordens']['naive'], p['ordens'][ref]):.2f}", p["ordens"]["naive"]),
            ("Ordem de referencia (fluxo do PDF)  -  tau = 1.00", p["ordens"][ref])]):
        ax.imshow(img)
        ax.set_title(titulo, fontsize=11)
        ax.axis("off")
        centros = []
        for k, bid in enumerate(ordem, 1):
            x0, y0, x1, y1 = (v * esc for v in caixa[bid])
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=1, ec=TEXTO2))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            centros.append((cx, cy))
            ax.text(cx, cy, str(k), fontsize=7.5, fontweight="bold", color=SUPERFICIE, ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.25", fc=COR["layoutlm"], ec="none"), zorder=4)
        for (xa, ya), (xb, yb) in zip(centros, centros[1:]):
            ax.annotate("", xy=(xb, yb), xytext=(xa, ya), zorder=3,
                        arrowprops=dict(arrowstyle="-|>", color=COR["layoutlm"], lw=1.4, alpha=0.75,
                                        shrinkA=7, shrinkB=7))
    fig.suptitle(f"O problema em uma pagina real  -  {curto(p['uf'])}, {p['arquivo'][:60]}, p. {p['pagina'] + 1}",
                 fontsize=12, fontweight="bold", x=0.02, ha="left")
    salvar(fig, "fig2_problema_pagina_real.png")
    return p["page_id"]


def fig_treino():
    series = {}
    for nome in ("layoutlm", "layoutlm_sem_layout"):
        arq = os.path.join(DIR_RESULTADOS, f"treino_{nome}.csv")
        if os.path.exists(arq):
            with open(arq, encoding="utf-8") as f:
                series[nome] = list(csv.DictReader(f))
    if not series:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
    for nome, linhas in series.items():
        perdas = [(int(l["passo"]), float(l["loss"])) for l in linhas if l["loss"]]
        vals = [(int(l["epoca"]), float(l["val_tau"])) for l in linhas if l["val_tau"]]
        if perdas:
            a1.plot(*zip(*perdas), color=COR[nome], lw=2, label=ROTULO[nome])
        if vals:
            a2.plot(*zip(*vals), color=COR[nome], lw=2, marker="o", ms=8,
                    mec=SUPERFICIE, mew=2, label=ROTULO[nome])
            a2.annotate(f"{vals[-1][1]:.3f}", vals[-1], textcoords="offset points", xytext=(8, 0),
                        va="center", fontsize=9, color=TEXTO)
    a1.set(title="Perda de treino (MSE da posicao normalizada)", xlabel="passo de otimizacao", ylabel="perda")
    a2.set(title="tau de Kendall na validacao", xlabel="epoca", ylabel="tau medio")
    for a in (a1, a2):
        a.legend(fontsize=8)
    salvar(fig, "fig3_treino_layoutlm.png")


def carregar_metricas():
    arq = os.path.join(DIR_RESULTADOS, "metricas_por_pagina.jsonl")
    regs = {}
    with open(arq, encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            regs.setdefault(r["metodo"], []).append(r)
    return regs


def fig_tradeoff():
    with open(os.path.join(DIR_RESULTADOS, "comparacao.json"), encoding="utf-8") as f:
        c = json.load(f)
    res = c["subconjunto_llm"] or c["todas_as_paginas"]
    n = next(iter(res.values()))["n"]
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    for m, r in res.items():
        destaque = m == "layoutlm"
        cor = COR["layoutlm"] if destaque else TEXTO2
        x = max(r["tempo_ms"], 1e-3)
        a, b = r["tau_ic95"]
        ax.errorbar(x, r["tau"], yerr=[[r["tau"] - a], [b - r["tau"]]], fmt="o", ms=9 if destaque else 7,
                    color=cor, mec=SUPERFICIE, mew=2, elinewidth=1.2, capsize=0, zorder=3)
        ax.annotate(ROTULO.get(m, m), (x, r["tau"]), textcoords="offset points", xytext=(9, 4),
                    fontsize=9, color=TEXTO, fontweight="bold" if destaque else "normal")
    ax.set_xscale("log")
    ax.set_xlabel("latencia por pagina (ms, escala log)  -  menor e melhor")
    ax.set_ylabel("tau de Kendall medio  -  maior e melhor")
    ax.set_title("Eficacia x eficiencia: qualidade da ordem contra custo por pagina")
    ax.text(0.0, -0.16, f"{n} paginas de teste comuns a todos os metodos; barras = IC 95% (bootstrap). "
            "Latencias em uma RTX 4050 Laptop (metodos neurais) e CPU i7-12650HX (heuristicas).",
            transform=ax.transAxes, fontsize=8, color=TEXTO2)
    salvar(fig, "fig4_tradeoff_eficacia_eficiencia.png")


def fig_distribuicao():
    regs = carregar_metricas()
    ordem = [m for m in ("layoutlm", "xycut", "naive", "lstm_geo_texto", "layoutlm_sem_layout") if m in regs]
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for m in ordem:
        v = sorted(r["kendall_tau"] for r in regs[m])
        y = [(k + 1) / len(v) for k in range(len(v))]
        ax.step(v, y, where="post", color=COR[m], lw=2, label=f"{ROTULO[m]} (mediana {statistics.median(v):.2f})")
    ax.axhline(0.10, color=TEXTO2, lw=1, ls=(0, (3, 3)))
    ax.text(-0.98, 0.115, "10% piores paginas", fontsize=8, color=TEXTO2)
    ax.set_xlim(-1, 1.01)
    ax.set_ylim(0, 1.01)
    ax.set_xlabel("tau de Kendall da pagina")
    ax.set_ylabel("fracao acumulada das paginas")
    ax.set_title("Distribuicao da qualidade por pagina (curva mais a direita = melhor)")
    ax.legend(loc="upper left", fontsize=8)
    salvar(fig, "fig5_distribuicao_tau_por_pagina.png")


def fig_colunas():
    with open(os.path.join(DIR_RESULTADOS, "comparacao.json"), encoding="utf-8") as f:
        pc = json.load(f)["por_colunas"]
    ordem = [m for m in ("layoutlm", "xycut", "naive", "lstm_geo_texto") if m in pc]
    grupos = sorted({g for m in ordem for g in pc[m]})
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    larg = 0.8 / len(ordem)
    for k, m in enumerate(ordem):
        xs = [i + (k - (len(ordem) - 1) / 2) * larg for i in range(len(grupos))]
        ys = [pc[m].get(g, {}).get("tau", 0) for g in grupos]
        ax.bar(xs, ys, width=larg - 0.03, color=COR[m], label=ROTULO[m], zorder=2)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.015, f"{y:.2f}", ha="center", fontsize=7.5, color=TEXTO)
    ns = [max(pc[m].get(g, {}).get("n", 0) for m in ordem) for g in grupos]
    ax.set_xticks(range(len(grupos)), [f"{g}\n(n={n})" for g, n in zip(grupos, ns)])
    ax.set_ylabel("tau de Kendall medio")
    ax.set_ylim(min(0, min(pc[m].get(g, {}).get("tau", 0) for m in ordem for g in grupos) - 0.05), 1.08)
    ax.set_title("Qualidade por numero de colunas da pagina")
    ax.legend(ncol=len(ordem), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.grid(axis="x", visible=False)
    salvar(fig, "fig6_tau_por_colunas.png")


def main():
    estilo()
    for f in (fig_caracterizacao, fig_pagina_exemplo, fig_treino, fig_tradeoff, fig_distribuicao, fig_colunas):
        try:
            f()
        except FileNotFoundError as e:
            print(f"  [--] {f.__name__}: dados ainda nao disponiveis ({os.path.basename(str(e.filename))})")
        except Exception:
            print(f"  [!!] {f.__name__} falhou:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
