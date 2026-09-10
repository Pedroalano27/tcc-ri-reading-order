"""
Caracterizacao do acervo: quao grave e o problema de ordem de leitura?

Para cada pagina extraida, compara as tres ordens candidatas entre si
(stream = fluxo do PDF, naive = topo->base/esq->dir, xycut = heuristica de
colunas) com tau de Kendall e ARD normalizado.

Com isso responde:
  1. Em quanto a ordenacao ingenua (tipica de YOLO + OCR) erra?
  2. Em que veiculos o fluxo do PDF concorda com a heuristica de colunas?
     Onde concorda, o fluxo e um rotulo silver confiavel -- o software de
     publicacao escreve o texto na ordem de leitura.

Tambem define a divisao treino/validacao/teste POR UF e grava splits.json.
"""
from __future__ import annotations

import os
import sys
import json
import glob
import random
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.metrics import kendall_tau, ard_normalizado            # noqa: E402
from src.eval.protocolo import DIR_BLOCOS, ARQ_SPLITS, DIR_RESULTADOS  # noqa: E402

LIMIARES = (0.9, 0.85, 0.8, 0.7)   # tenta o mais exigente primeiro
MIN_UFS_CONFIAVEIS = 12
MIN_PAGINAS_UF = 10
FORCAR_TESTE = {"official_diary_rj"}   # tem saidas do Azure/Google: fica fora do treino


def main():
    paginas = []
    for caminho in sorted(glob.glob(os.path.join(DIR_BLOCOS, "official_diary_*.jsonl"))):
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                try:
                    r = json.loads(linha)
                except json.JSONDecodeError:
                    continue    # linha truncada por uma extracao interrompida
                o = r["ordens"]
                paginas.append({
                    "page_id": r["page_id"], "uf": r["uf"],
                    "n_blocos": r["stats"]["n_blocos"], "n_colunas": r["stats"]["n_colunas"],
                    "tau_naive_stream": kendall_tau(o["naive"], o["stream"]),
                    "tau_xycut_stream": kendall_tau(o["xycut"], o["stream"]),
                    "tau_naive_xycut": kendall_tau(o["naive"], o["xycut"]),
                    "ardn_naive_stream": ard_normalizado(o["naive"], o["stream"]),
                    "ardn_xycut_stream": ard_normalizado(o["xycut"], o["stream"]),
                    "ardn_naive_xycut": ard_normalizado(o["naive"], o["xycut"]),
                    "naive_igual_xycut": o["naive"] == o["xycut"],
                })

    por_uf = {}
    for p in paginas:
        por_uf.setdefault(p["uf"], []).append(p)

    resumo = {}
    for uf, ps in sorted(por_uf.items()):
        med = lambda k: statistics.median(x[k] for x in ps)
        resumo[uf] = {
            "paginas": len(ps),
            "blocos_medio": round(statistics.mean(x["n_blocos"] for x in ps), 1),
            "prop_multicoluna": round(sum(1 for x in ps if x["n_colunas"] >= 2) / len(ps), 3),
            "tau_naive_stream_med": round(med("tau_naive_stream"), 3),
            "tau_xycut_stream_med": round(med("tau_xycut_stream"), 3),
            "tau_naive_xycut_med": round(med("tau_naive_xycut"), 3),
            "ardn_naive_xycut_med": round(med("ardn_naive_xycut"), 3),
            "prop_naive_errada": round(sum(1 for x in ps if not x["naive_igual_xycut"]) / len(ps), 3),
        }

    # Veiculos com fluxo confiavel: concordancia mediana alta entre fluxo e heuristica.
    elegiveis = {uf: r for uf, r in resumo.items() if r["paginas"] >= MIN_PAGINAS_UF}
    for limiar in LIMIARES:
        confiaveis = sorted(uf for uf, r in elegiveis.items() if r["tau_xycut_stream_med"] >= limiar)
        if len(confiaveis) >= MIN_UFS_CONFIAVEIS:
            break

    rng = random.Random(42)
    ordem = sorted(confiaveis)
    rng.shuffle(ordem)
    teste = sorted(set(u for u in ordem if u in FORCAR_TESTE) |
                   set([u for u in ordem if u not in FORCAR_TESTE][: max(1, round(0.25 * len(ordem)) - 1)]))
    resto = [u for u in ordem if u not in teste]
    validacao = sorted(resto[: max(1, round(0.12 * len(ordem)))])
    treino = sorted(u for u in resto if u not in validacao)

    splits = {
        "referencia": "stream",
        "criterio_referencia": (
            f"Ordem do fluxo de conteudo do PDF, restrita aos veiculos em que ela concorda "
            f"com a heuristica XY-cut (tau de Kendall mediano >= {limiar}). Nesses veiculos o "
            f"software de publicacao grava o texto na ordem de leitura. A confiabilidade e "
            f"avaliada por VEICULO, nao por pagina, para nao selecionar apenas as paginas em "
            f"que a heuristica acerta -- o que favoreceria a propria heuristica."
        ),
        "limiar_tau": limiar,
        "treino": treino, "validacao": validacao, "teste": teste,
        "ufs_nao_confiaveis": sorted(set(resumo) - set(confiaveis)),
    }
    os.makedirs(os.path.dirname(ARQ_SPLITS), exist_ok=True)
    with open(ARQ_SPLITS, "w", encoding="utf-8") as f:
        json.dump(splits, f, ensure_ascii=False, indent=2)

    os.makedirs(DIR_RESULTADOS, exist_ok=True)
    with open(os.path.join(DIR_RESULTADOS, "caracterizacao.json"), "w", encoding="utf-8") as f:
        json.dump({"por_uf": resumo, "splits": splits, "n_paginas": len(paginas),
                   "global": {
                       "tau_naive_stream_med": statistics.median(p["tau_naive_stream"] for p in paginas),
                       "tau_xycut_stream_med": statistics.median(p["tau_xycut_stream"] for p in paginas),
                       "tau_naive_xycut_med": statistics.median(p["tau_naive_xycut"] for p in paginas),
                       "prop_multicoluna": sum(1 for p in paginas if p["n_colunas"] >= 2) / len(paginas),
                       "prop_naive_errada": sum(1 for p in paginas if not p["naive_igual_xycut"]) / len(paginas),
                   }}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR_RESULTADOS, "caracterizacao_paginas.jsonl"), "w", encoding="utf-8") as f:
        for p in paginas:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"{'UF':<34}{'pags':>5}{'blocos':>7}{'multi':>7}{'t(nv,st)':>9}{'t(xy,st)':>9}{'t(nv,xy)':>9}  split")
    print("-" * 98)
    papel = {u: "TESTE" for u in teste} | {u: "valid" for u in validacao} | {u: "treino" for u in treino}
    for uf, r in resumo.items():
        print(f"{uf:<34}{r['paginas']:>5}{r['blocos_medio']:>7}{r['prop_multicoluna']:>7.0%}"
              f"{r['tau_naive_stream_med']:>9.2f}{r['tau_xycut_stream_med']:>9.2f}"
              f"{r['tau_naive_xycut_med']:>9.2f}  {papel.get(uf, '-- nao confiavel')}")
    print("-" * 98)
    print(f"Paginas: {len(paginas)} | limiar de confiabilidade: tau >= {limiar} | "
          f"confiaveis: {len(confiaveis)} UFs")
    print(f"Treino {len(treino)} UFs | validacao {len(validacao)} | teste {len(teste)}")


if __name__ == "__main__":
    main()
