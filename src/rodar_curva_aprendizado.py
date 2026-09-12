"""
Curva de aprendizado: o LayoutLM (e a BiLSTM geometrica) melhora com mais paginas de treino?

A pergunta decide o rumo do TCC. Se o tau continuar subindo com mais dados, a derrota para a
XY-cut era falta de dado, e o acervo tem dezenas de milhares de paginas. Se estacionar abaixo
dela, e um resultado real.

O treino e ampliado com paginas extras dos MESMOS 7 veiculos de treino (data/processed/
blocos_extra, coletadas pelo extrator com --saida), em subconjuntos aninhados: o de 152 paginas
e exatamente o treino original. Validacao e teste sao os do protocolo, intocados.

Epocas por tamanho: ~6.000 passagens de pagina para o LayoutLM (o treino original fez 152 x 40),
com minimo de 4 epocas; a selecao do melhor modelo continua pelo tau de validacao. A BiLSTM roda
em paralelo, na CPU.

Duas formulacoes do LayoutLM entram na curva:
  layoutlm            pontual (um escore por bloco, ordem por sort) -- src/models/layoutlm_ordem.py
  layoutlm_sucessor   preve o proximo bloco de cada bloco -- src/models/layoutlm_sucessor.py

Saidas:
  resultados/curva_aprendizado/curva.json      tau (IC 95%), p10, sucessor, ARD e tempo por tamanho
  resultados/curva_aprendizado/pred_*.jsonl    predicoes no teste
  docs/figuras/fig7_curva_aprendizado.png      dois paineis: tau e sucessor correto

Uso:
    python src/rodar_curva_aprendizado.py [--tamanhos 152 400 1000 2000 0]
    python src/rodar_curva_aprendizado.py --modelos layoutlm_sucessor --tamanhos 0
    (0 = todas as paginas disponiveis)
"""
from __future__ import annotations

import os
import sys
import json
import math
import time
import random
import argparse
import threading
import statistics
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from src.eval.protocolo import carregar_splits, carregar_particao, montar_treino, DIR_RESULTADOS  # noqa: E402
from src.eval.metrics import avaliar  # noqa: E402

PY = sys.executable
DIR = os.path.join(DIR_RESULTADOS, "curva_aprendizado")
DIR_LOGS = os.path.join(DIR_RESULTADOS, "logs")
EXTRA = os.path.join(RAIZ, "data", "processed", "blocos_extra")
DIR_MODELOS = os.path.join(RAIZ, "models", "layoutlm_ordem")
TRAVA = threading.Lock()


def rodar(cmd, log):
    with open(os.path.join(DIR_LOGS, log), "w", encoding="utf-8") as f:
        return subprocess.run(cmd, cwd=RAIZ, stdout=f, stderr=subprocess.STDOUT).returncode


def metricas(arq_pred, teste, ref):
    regs = []
    with open(arq_pred, encoding="utf-8") as f:
        for l in f:
            d = json.loads(l)
            p = teste[d["page_id"]]
            r = avaliar(d["ordem_pred"], p["ordens"][ref], {c["id"]: c["text"] for c in p["bounding_boxes"]})
            r["n_colunas"] = p["stats"]["n_colunas"]
            regs.append(r)
    t = sorted(r["kendall_tau"] for r in regs)
    rng = random.Random(7)
    medias = sorted(statistics.mean(rng.choices(t, k=len(t))) for _ in range(2000))
    por_col = {}
    for r in regs:
        g = "1" if r["n_colunas"] <= 1 else ("2" if r["n_colunas"] == 2 else "3+")
        por_col.setdefault(g, []).append(r["kendall_tau"])
    return {"n": len(t), "tau": statistics.mean(t), "ic95": [medias[50], medias[1949]],
            "p10": t[int(0.1 * len(t))], "ard_norm": statistics.mean(r["ard_norm"] for r in regs),
            "sucessor": statistics.mean(r["acerto_sucessor"] for r in regs),
            "tau_por_colunas": {g: statistics.mean(v) for g, v in sorted(por_col.items())}}


def referencias():
    """Linhas horizontais da figura: os metodos sem treino, nas duas metricas."""
    try:
        with open(os.path.join(DIR_RESULTADOS, "comparacao.json"), encoding="utf-8") as f:
            todas = json.load(f)["todas_as_paginas"]
    except (OSError, KeyError):
        return {}
    ref = {m: todas[m]["tau"] for m in ("xycut", "naive", "layoutlm", "lstm_geo") if m in todas}
    ref.update({f"{m}_sucessor": todas[m]["sucessor"] for m in ("xycut", "naive") if m in todas})
    return ref


ROTULOS = {"layoutlm": "LayoutLM pontual", "layoutlm_sucessor": "LayoutLM sucessor",
           "lstm_geo": "BiLSTM (geometria)"}


def figura(dados):
    """Dois paineis lado a lado: ordem global (tau) e continuidade local (sucessor).

    Separar as duas e o ponto da figura: a formulacao pontual e a de sucessor trocam
    de lugar de um painel para o outro, e e isso que a media do tau escondia.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullLocator, PercentFormatter
    from src.eval.figuras import estilo, salvar, virgula, COR, TEXTO2

    estilo()
    fig, axs = plt.subplots(1, 2, figsize=(11.2, 4.4))
    tamanhos = dados["tamanhos"]
    paineis = [(axs[0], "tau", "τ de Kendall no teste (95 páginas)", "Ordem global: τ de Kendall", 1),
               (axs[1], "sucessor", "Blocos seguidos do bloco certo", "Continuidade local: sucessor correto", 100)]
    for ax, chave, rot_y, titulo, escala in paineis:
        for m in ("layoutlm", "layoutlm_sucessor", "lstm_geo"):
            pts = sorted((int(n), r) for n, r in dados["resultados"].get(m, {}).items() if chave in r)
            if not pts:
                continue
            xs, ys = [n for n, _ in pts], [escala * r[chave] for _, r in pts]
            if chave == "tau":
                ax.fill_between(xs, [escala * r["ic95"][0] for _, r in pts],
                                [escala * r["ic95"][1] for _, r in pts], color=COR[m], alpha=0.13, linewidth=0)
            ax.plot(xs, ys, "-o", color=COR[m], lw=2, ms=6, label=ROTULOS[m], zorder=3)
            ax.annotate(virgula(ys[-1], 3) if escala == 1 else f"{ys[-1]:.0f}%".replace(".", ","),
                        (xs[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                        va="center", fontsize=9, color=TEXTO2)
        for m, rot, ls in (("xycut", "XY-cut", "--"), ("naive", "Ingênua", ":")):
            v = dados["referencias"].get(m if chave == "tau" else f"{m}_sucessor")
            if v is not None:
                ax.axhline(escala * v, color=COR[m], lw=1.6, ls=ls, zorder=2)
                ax.text(tamanhos[0], escala * v + 0.012 * escala, f"{rot} (sem treino)",
                        color=COR[m], fontsize=9, va="bottom", ha="left")
        ax.set_xscale("log")
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticks(tamanhos)
        ax.set_xticklabels([f"{n:,}".replace(",", ".") for n in tamanhos])
        ax.set_xlim(tamanhos[0] / 1.25, tamanhos[-1] * 1.5)
        ax.set_xlabel("Páginas de treino (escala logarítmica)")
        ax.set_ylabel(rot_y)
        ax.set_title(titulo, fontsize=11)
        if escala == 100:
            ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))
    axs[0].legend(loc="lower right")
    fig.suptitle("Curva de aprendizado: mais páginas de treino corrigem a ordem, não a continuidade",
                 fontsize=12.5, y=0.99)
    salvar(fig, "fig7_curva_aprendizado.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tamanhos", type=int, nargs="*", default=[152, 400, 1000, 2000, 0])
    ap.add_argument("--modelos", nargs="*", default=["layoutlm", "layoutlm_sucessor", "lstm_geo"],
                    choices=["layoutlm", "layoutlm_sucessor", "lstm_geo"])
    ap.add_argument("--sem-lstm", action="store_true", help="atalho para tirar a BiLSTM de --modelos")
    ap.add_argument("--manter-modelos", action="store_true", help="nao apaga os checkpoints intermediarios")
    ap.add_argument("--micro-batch", type=int, default=4,
                    help="paginas por passagem na GPU; o batch efetivo continua 8 (acumulacao). "
                         "Numa GPU de 16 GB (T4), 8 ou 12 acelera sem mudar a otimizacao")
    ap.add_argument("--so-figura", action="store_true", help="refaz so a figura a partir de curva.json")
    ap.add_argument("--refazer", action="store_true",
                    help="refaz tudo; por padrao os tamanhos ja medidos em curva.json sao pulados")
    a = ap.parse_args()
    os.makedirs(DIR, exist_ok=True)
    os.makedirs(DIR_LOGS, exist_ok=True)
    arq_json = os.path.join(DIR, "curva.json")
    if a.so_figura:
        with open(arq_json, encoding="utf-8") as f:
            return figura(json.load(f))

    modelos = [m for m in a.modelos if not (a.sem_lstm and m == "lstm_geo")]
    total = len(montar_treino(None, EXTRA))
    tamanhos = sorted({min(n, total) if n else total for n in a.tamanhos})
    print(f"[*] paginas de treino disponiveis: {total} | tamanhos: {tamanhos} | modelos: {modelos}", flush=True)
    ref = carregar_splits()["referencia"]
    teste = {p["page_id"]: p for p in carregar_particao("teste")}
    anterior = {}
    if os.path.exists(arq_json) and not a.refazer:   # retomada: nao repete o que ja foi medido
        with open(arq_json, encoding="utf-8") as f:
            anterior = json.load(f).get("resultados", {})
    dados = {"paginas_disponiveis": total, "tamanhos": tamanhos, "referencias": referencias(),
             "resultados": {m: anterior.get(m, {}) for m in ("layoutlm", "layoutlm_sucessor", "lstm_geo")},
             "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}

    def gravar():
        with TRAVA, open(arq_json, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def trilha_lstm():
        for n in tamanhos:
            if str(n) in dados["resultados"]["lstm_geo"]:
                continue
            ep = min(40, max(8, math.ceil(12000 / n)))
            nome = f"curva_lstm_geo_n{n}"
            t0 = time.time()
            cod = rodar([PY, "src/models/lstm_ordem.py", "--variante", "geo", "--nome", nome, "--n-treino", str(n),
                         "--blocos-extra", EXTRA, "--dir-saida", DIR, "--epocas", str(ep),
                         "--max-minutos", "15", "--threads", "8"], f"{nome}.log")
            if cod != 0:
                print(f"  [!] lstm_geo n={n} falhou; veja resultados/logs/{nome}.log", flush=True)
                continue
            r = {**metricas(os.path.join(DIR, f"pred_{nome}.jsonl"), teste, ref), "epocas": ep,
                 "segundos_treino": round(time.time() - t0)}
            dados["resultados"]["lstm_geo"][str(n)] = r
            gravar()
            print(f"  [lstm_geo] {n:>5} paginas: tau {r['tau']:.3f} (IC {r['ic95'][0]:.3f}-{r['ic95'][1]:.3f}) "
                  f"em {r['segundos_treino']} s", flush=True)

    th = None
    if "lstm_geo" in modelos:
        th = threading.Thread(target=trilha_lstm)
        th.start()

    for modelo in [m for m in modelos if m != "lstm_geo"]:
        script = "src/models/layoutlm_sucessor.py" if modelo == "layoutlm_sucessor" else "src/models/layoutlm_ordem.py"
        for n in tamanhos:
            if str(n) in dados["resultados"][modelo]:
                print(f"  [{modelo}] {n:>5} paginas: ja medido em curva.json; pulando", flush=True)
                continue
            ep = min(40, max(4, math.ceil(6000 / n)))
            nome = f"curva_{modelo}_n{n}"
            t0 = time.time()
            cod = rodar([PY, script, "treinar", "--nome", nome, "--n-treino", str(n),
                         "--blocos-extra", EXTRA, "--dir-saida", DIR, "--epocas", str(ep),
                         "--max-minutos", "45", "--micro-batch", str(a.micro_batch)],
                        f"{nome}_treinar.log")
            seg = time.time() - t0
            if cod == 0:
                cod = rodar([PY, script, "avaliar", "--nome", nome, "--dir-saida", DIR], f"{nome}_avaliar.log")
            if cod != 0:
                print(f"  [!] {modelo} n={n} falhou; veja resultados/logs/{nome}_*.log", flush=True)
                continue
            with open(os.path.join(DIR_MODELOS, f"{nome}_config.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            r = {**metricas(os.path.join(DIR, f"pred_{nome}.jsonl"), teste, ref), "epocas": ep,
                 "epocas_concluidas": cfg["epocas_concluidas"],
                 "melhor_val": cfg.get("melhor_val", cfg.get("melhor_val_tau")),
                 "segundos_treino": round(seg)}
            dados["resultados"][modelo][str(n)] = r
            gravar()
            print(f"  [{modelo}] {n:>5} paginas: tau {r['tau']:.3f} "
                  f"(IC {r['ic95'][0]:.3f}-{r['ic95'][1]:.3f}) | sucessor {r['sucessor']:.1%} | "
                  f"{ep} epocas em {r['segundos_treino']} s", flush=True)
            if n != tamanhos[-1] and not a.manter_modelos:
                os.remove(os.path.join(DIR_MODELOS, f"{nome}.pt"))

    if th:
        th.join()
    dados["fim"] = time.strftime("%Y-%m-%d %H:%M:%S")
    gravar()
    figura(dados)
    print(f"[OK] curva em {arq_json}")


if __name__ == "__main__":
    main()
