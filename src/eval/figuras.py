"""
Gera as figuras do TCC em docs/figuras/ (PNG, 200 dpi).

Paleta: instância de referência validada (skill de dataviz). Cada método tem
uma cor FIXA em todas as figuras -- a cor segue a entidade, nunca a posição.
No gráfico de dispersão (todas as combinações de pares em cena) usam-se no
máximo duas cores, com rótulo direto em cada ponto.

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
from src.eval.protocolo import carregar_splits, iterar_paginas, DIR_RESULTADOS  # noqa: E402
from src.eval.metrics import kendall_tau  # noqa: E402

DIR_FIG = os.path.join(RAIZ, "docs", "figuras")

SUPERFICIE, TEXTO, TEXTO2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
NEUTRO = "#8f8e89"
COR = {                        # ordem fixa dos slots categóricos da paleta de referência
    "layoutlm": "#2a78d6",
    "layoutlm_sucessor": "#7d1442",
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
    "aleatoria": "Ordem do detector", "naive": "Ingênua", "xycut": "XY-cut",
    "lstm_texto": "BiLSTM (texto)", "lstm_geo": "BiLSTM (geometria)", "lstm_geo_texto": "BiLSTM (texto+geo)",
    "layoutlm_sem_layout": "LayoutLM sem layout", "layoutlm": "LayoutLM pontual",
    "layoutlm_sucessor": "LayoutLM sucessor", "llm_llava_7b": "LLM llava:7b",
}
MUNICIPIOS = {
    "MG_congonhas": "Congonhas (MG)", "RJ_barra_do_pirai": "Barra do Piraí (RJ)",
    "RJ_duque_de_caxias": "Duque de Caxias (RJ)", "RJ_seropedica": "Seropédica (RJ)",
    "RJ_volta_redonda": "Volta Redonda (RJ)", "am_manaus": "Manaus (AM)", "ba_salvador": "Salvador (BA)",
    "pr_curitiba": "Curitiba (PR)", "rj_japeri": "Japeri (RJ)", "rs_porto_alegre": "Porto Alegre (RS)",
    "pi_v2": "PI (v2)",
}


def virgula(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def nome_veiculo(uf):
    chave = uf.replace("official_diary_", "")
    return MUNICIPIOS.get(chave, chave.upper())


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


# ---------------------------------------------------------------------------

def fig_caracterizacao():
    with open(os.path.join(DIR_RESULTADOS, "caracterizacao.json"), encoding="utf-8") as f:
        c = json.load(f)
    por_uf, splits = c["por_uf"], c["splits"]
    papel = {u: "teste" for u in splits["teste"]} | {u: "validação" for u in splits["validacao"]} | \
            {u: "treino" for u in splits["treino"]}
    ufs = sorted(por_uf, key=lambda u: por_uf[u]["tau_xycut_stream_med"])
    todos = [por_uf[u][k] for u in ufs for k in ("tau_naive_stream_med", "tau_xycut_stream_med")]
    fig, ax = plt.subplots(figsize=(8.4, 0.28 * len(ufs) + 1.8))
    for k, u in enumerate(ufs):
        a, b = por_uf[u]["tau_naive_stream_med"], por_uf[u]["tau_xycut_stream_med"]
        ax.plot([a, b], [k, k], color=GRADE, lw=2, zorder=1)
        ax.text(1.03, k, papel.get(u, "não confiável"), va="center", fontsize=8,
                color=TEXTO if u in papel else TEXTO2, transform=ax.get_yaxis_transform())
    ax.scatter([por_uf[u]["tau_naive_stream_med"] for u in ufs], range(len(ufs)), s=36,
               color=COR["naive"], edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label="Ingênua (topo→base, esq.→dir.) × fluxo do PDF")
    ax.scatter([por_uf[u]["tau_xycut_stream_med"] for u in ufs], range(len(ufs)), s=36,
               color=COR["xycut"], edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label="XY-cut (colunas) × fluxo do PDF")
    ax.axvline(splits["limiar_tau"], color=TEXTO2, lw=1, ls=(0, (3, 3)), zorder=2)
    ax.text(splits["limiar_tau"], len(ufs) - 0.3,
            f" limiar de confiabilidade (τ = {virgula(splits['limiar_tau'], 1)})",
            fontsize=8, color=TEXTO2, va="bottom")
    ax.set_yticks(range(len(ufs)), [nome_veiculo(u) for u in ufs], fontsize=8)
    ax.set_xlabel("τ de Kendall mediano entre as duas ordens (1 = mesma ordem)")
    ax.set_xlim(min(todos) - 0.06, 1.02)
    ax.set_title("A ordem interna do PDF só coincide com a leitura em poucos veículos")
    ax.legend(loc="lower right", fontsize=8, title="pontos sobrepostos = as duas ordens coincidem",
              title_fontsize=7.5)
    ax.grid(axis="y", visible=False)
    salvar(fig, "fig1_caracterizacao_por_veiculo.png")


def fig_pagina_exemplo():
    import pdfplumber
    splits = carregar_splits()
    ref = splits["referencia"]
    todas = list(iterar_paginas(splits["treino"] + splits["validacao"] + splits["teste"]))
    candidatas = [p for p in todas if p["stats"]["n_colunas"] >= 2 and 10 <= p["stats"]["n_blocos"] <= 30
                  and kendall_tau(p["ordens"]["xycut"], p["ordens"][ref]) >= 0.9]
    if not candidatas:
        candidatas = [p for p in todas if 10 <= p["stats"]["n_blocos"] <= 40]
    p = min(candidatas, key=lambda p: kendall_tau(p["ordens"]["naive"], p["ordens"][ref]))
    caminho_pdf = os.path.join(RAIZ, "data", "raw", p["uf"], *p["arquivo"].split("/"))
    res = 90
    with pdfplumber.open(caminho_pdf) as pdf:
        img = pdf.pages[p["pagina"]].to_image(resolution=res).original
    esc = res / 72.0
    caixa = {c["id"]: c["bbox"] for c in p["bounding_boxes"]}
    alt_painel = 5.8 * img.height / img.width
    reserva = 0.75
    fig, eixos = plt.subplots(1, 2, figsize=(12, alt_painel + reserva))
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=alt_painel / (alt_painel + reserva), wspace=0.04)
    tau_naive = kendall_tau(p["ordens"]["naive"], p["ordens"][ref])
    for ax, (titulo, ordem) in zip(eixos, [
            (f"Ordem ingênua (topo→base, esq.→dir.): τ = {virgula(tau_naive)}", p["ordens"]["naive"]),
            ("Ordem de referência (fluxo do PDF): τ = 1,00", p["ordens"][ref])]):
        ax.imshow(img)
        ax.set_title(titulo, fontsize=11)
        ax.axis("off")
        centros = []
        for k, bid in enumerate(ordem, 1):
            x0, y0, x1, y1 = (v * esc for v in caixa[bid])
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=1, ec=TEXTO2))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            centros.append((cx, cy))
            ax.text(cx, cy, str(k), fontsize=7, fontweight="bold", color=SUPERFICIE, ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.2", fc=COR["layoutlm"], ec="none"), zorder=4)
        for (xa, ya), (xb, yb) in zip(centros, centros[1:]):
            ax.annotate("", xy=(xb, yb), xytext=(xa, ya), zorder=3,
                        arrowprops=dict(arrowstyle="-|>", color=COR["layoutlm"], lw=1.4, alpha=0.75,
                                        shrinkA=6, shrinkB=6))
    arquivo = os.path.splitext(os.path.basename(p["arquivo"]))[0]
    if len(arquivo) > 44:
        arquivo = arquivo[:43] + "…"
    fig.suptitle(f"O problema numa página real: {nome_veiculo(p['uf'])}, {arquivo}, p. {p['pagina'] + 1}",
                 fontsize=12, fontweight="bold", x=0.01, ha="left", y=0.998)
    salvar(fig, "fig2_problema_pagina_real.png")


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
            a2.plot(*zip(*vals), color=COR[nome], lw=2, marker="o", ms=4,
                    mec=SUPERFICIE, mew=1, label=ROTULO[nome])
            a2.annotate(virgula(vals[-1][1], 3), vals[-1], textcoords="offset points", xytext=(8, 0),
                        va="center", fontsize=9, color=TEXTO)
    a1.set(title="Perda de treino (MSE da posição normalizada)", xlabel="passo de otimização", ylabel="perda")
    a2.set(title="τ de Kendall na validação", xlabel="época", ylabel="τ médio")
    for a in (a1, a2):
        a.legend(fontsize=8)
    salvar(fig, "fig3_treino_layoutlm.png")


def carregar_metricas():
    regs = {}
    with open(os.path.join(DIR_RESULTADOS, "metricas_por_pagina.jsonl"), encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            regs.setdefault(r["metodo"], []).append(r)
    return regs


# deslocamento (pontos tipográficos) e alinhamento do rótulo de cada método, para não colidirem
DESLOCAMENTO = {
    "aleatoria": (9, 6, "left"), "naive": (9, -13, "left"), "xycut": (9, 6, "left"),
    "lstm_texto": (-9, 6, "right"), "lstm_geo": (-9, 6, "right"), "lstm_geo_texto": (-9, -13, "right"),
    "layoutlm_sem_layout": (9, -13, "left"), "layoutlm": (11, -3, "left"), "llm_llava_7b": (-9, 8, "right"),
}


def fig_tradeoff():
    with open(os.path.join(DIR_RESULTADOS, "comparacao.json"), encoding="utf-8") as f:
        c = json.load(f)
    todas, sub = c["todas_as_paginas"], c["subconjunto_llm"]
    pontos = [(m, r, False) for m, r in todas.items()]
    if "llm_llava_7b" in sub:
        pontos.append(("llm_llava_7b", sub["llm_llava_7b"], True))
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for m, r, subconj in pontos:
        destaque = m == "layoutlm"
        cor = COR["layoutlm"] if destaque else TEXTO2
        x = max(r["tempo_ms"], 1e-3)
        a, b = r["tau_ic95"]
        ax.errorbar(x, r["tau"], yerr=[[r["tau"] - a], [b - r["tau"]]], fmt="o", ms=9 if destaque else 7,
                    color=cor, mfc=SUPERFICIE if subconj else cor, mec=cor if subconj else SUPERFICIE,
                    mew=2, elinewidth=1.2, capsize=0, zorder=3)
        dx, dy, ha = DESLOCAMENTO.get(m, (9, 4, "left"))
        rotulo = ROTULO.get(m, m) + (f" ({r['n']} págs.)" if subconj else "")
        ax.annotate(rotulo, (x, r["tau"]), textcoords="offset points", xytext=(dx, dy), ha=ha,
                    fontsize=9, color=COR["layoutlm"] if destaque else TEXTO,
                    fontweight="bold" if destaque else "normal")
    ax.set_xscale("log")
    ax.set_xlim(4e-4, 4e4)
    ax.set_xlabel("latência por página (ms, escala log): menor é melhor")
    ax.set_ylabel("τ de Kendall médio: maior é melhor")
    ax.set_title("Eficácia × eficiência: qualidade da ordem contra custo por página")
    ax.text(0.0, -0.17, f"{c['paginas_teste']} páginas de teste; a LLM, num subconjunto de {c['n_subconjunto_llm']} "
            "páginas pequenas (ponto vazado). Barras = IC 95% (bootstrap).\nMétodos neurais numa RTX 4050 Laptop "
            "(6 GB); heurísticas na CPU i7-12650HX. O llava:7b não coube inteiro na GPU: 34% do modelo rodou na CPU.",
            transform=ax.transAxes, fontsize=8, color=TEXTO2, va="top")
    salvar(fig, "fig4_tradeoff_eficacia_eficiencia.png")


def fig_distribuicao():
    regs = carregar_metricas()
    ordem = [m for m in ("layoutlm", "xycut", "naive", "lstm_geo_texto", "layoutlm_sem_layout") if m in regs]
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for m in ordem:
        v = sorted(r["kendall_tau"] for r in regs[m])
        y = [(k + 1) / len(v) for k in range(len(v))]
        ax.step(v, y, where="post", color=COR[m], lw=2,
                label=f"{ROTULO[m]} (mediana {virgula(statistics.median(v))})")
    ax.axhline(0.10, color=TEXTO2, lw=1, ls=(0, (3, 3)))
    ax.text(-0.98, 0.115, "10% piores páginas", fontsize=8, color=TEXTO2)
    ax.set_xlim(-1, 1.01)
    ax.set_ylim(0, 1.01)
    ax.set_xlabel("τ de Kendall da página")
    ax.set_ylabel("fração acumulada das páginas")
    ax.set_title("Distribuição da qualidade por página (curva mais à direita = melhor)")
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
            ax.text(x, y + 0.015, virgula(y), ha="center", fontsize=7.5, color=TEXTO)
    ns = [max(pc[m].get(g, {}).get("n", 0) for m in ordem) for g in grupos]
    ax.set_xticks(range(len(grupos)), [f"{g}\n(n = {n} páginas)" for g, n in zip(grupos, ns)])
    ax.set_ylabel("τ de Kendall médio")
    ax.set_ylim(min(0, min(pc[m].get(g, {}).get("tau", 0) for m in ordem for g in grupos) - 0.05), 1.08)
    ax.set_title("Qualidade por número de colunas da página")
    ax.legend(ncol=len(ordem), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    ax.grid(axis="x", visible=False)
    salvar(fig, "fig6_tau_por_colunas.png")


def main():
    estilo()
    for f in (fig_caracterizacao, fig_pagina_exemplo, fig_treino, fig_tradeoff, fig_distribuicao, fig_colunas):
        try:
            f()
        except FileNotFoundError as e:
            print(f"  [--] {f.__name__}: dados ainda não disponíveis ({os.path.basename(str(e.filename))})")
        except Exception:
            print(f"  [!!] {f.__name__} falhou:")
            traceback.print_exc()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
