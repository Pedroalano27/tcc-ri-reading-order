"""E012: bancada humana extra com as anotacoes de ordem da Data Policy (seed 2).

Monta as paginas no MESMO formato das bancadas golden (linhas + atomos ls3, referencia humana
expandida por palavras) e avalia regra, hibrido 67, grafo E004 e HIER-1 com a regua de sempre.

DADOS DA DATA POLICY: uso autorizado na pesquisa, NAO publicar. Saidas por pagina ficam em
resultados/ordem_ls/e012/ (fora do git); o relatorio em resultados/e012_ls/ so tem agregados.
Nunca passar estes dados a Codex/Antigravity/Gemini.

Uso na raiz: venv/Scripts/python.exe -B orquestracao/analises/e012_bancada_ls.py [--montar] [--avaliar]
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import argparse
import collections
import hashlib
import json
import random
import statistics
import time

from orquestracao.analises import ordem_sem_bbox_validacao_ls as V
from orquestracao.analises import unidades_sem_caixas as U
from orquestracao.analises import e016_hierarquico as H
from orquestracao.analises import e004_grafo as g
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import bancada_ordenadores as b

PRIV = RAIZ / "resultados/ordem_ls/e012"          # por pagina: fora do git
PUB = RAIZ / "resultados/e012_ls"                 # so agregados
BANCADA = PRIV / "ls_humana.jsonl"
METODOS = ("regra", "hibrido67", "grafo_e004", "hier1")
CLASSE = {"table": "tabela", "picture": "imagem"}


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def chave(pid):
    return hashlib.sha256(pid.encode()).hexdigest()


def ler(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gravar(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def montar():
    """Uma linha por pagina com cadeia humana valida, palavras do PDF e deteccao ls3 em cache."""
    tarefas = V.j.ler_jsonl(V.BASE / "convertido/tarefas.jsonl")
    anns = {a["page_id"]: a for a in V.j.ler_jsonl(V.BASE / "convertido/anotacoes.jsonl")
            if a["status"] == "concluida"}
    cont, linhas = collections.Counter(), []
    for t in tarefas:
        pid = t["page_id"]
        pal, det, meta = (V.BASE / d / (chave(pid) + ".json") for d in ("palavras", "detector", "paginas"))
        if pid not in anns or not pal.exists():
            cont["sem_anotacao_ou_palavras"] += 1
            continue
        ex = ler(pal)
        ws = ex["ws"]
        if not ws:
            cont["pagina_vazia"] += 1
            continue
        q = V.referencia(ex["p"], anns[pid], ws)
        if not q["gt_w"]:
            cont["sem_referencia"] += 1
            continue
        regs = []
        if det.exists():
            for r in ler(det)["regioes"]:
                if r["rotulo"] in CLASSE:
                    regs.append({"id": f"d{len(regs)}", "classe": CLASSE[r["rotulo"]],
                                 "score": r["score"], "bbox": r["bbox"]})
        else:
            cont["sem_detector"] += 1
        pm = ler(meta) if meta.exists() else {}
        dims = ex["p"]["dimensions"]
        exigir(max(w[3] for w in ws) <= dims["width"] * 1.02, f"Palavras fora da pagina: {pid}")
        uf = pm.get("veiculo") or pid.split("/")[0]
        m = {"page_id": pid, "uf": uf, "arquivo": pid.split("#")[0], "pagina": int(pid.rsplit("#p", 1)[1]),
             "dimensions": dims, "particao": "ls_humana", "colecao": "bancadas"}
        base = {k: m[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions")}
        base.update(palavras=ws, detector={"modelo": "ls3", "regioes": U.e.ls.dets({"ls3": regs}, "ls3")})
        rep_l, rep_c = U.representar(base)
        _, rep_m = U.representar_estruturas(base)
        reps = {nome: U.converter(m, r, ws, q["gt_w"]) for nome, r in zip(U.REPS, (rep_l, rep_c, rep_m))}
        linhas.append({**{k: m[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "particao")},
                       "palavras": ws, "gt_w": q["gt_w"], "referencia_palavras": q["gt_w"],
                       "gt_r": q["gt_r"], "gt_l": q["gt_l"], "reg_words": q["reg_words"],
                       "gold_lines": q["gold_lines"], "representacoes": reps,
                       "iguais_a_origem": pm.get("iguais_a_origem"), "auditoria_ls": q["auditoria"]})
        cont["paginas"] += 1
    PRIV.mkdir(parents=True, exist_ok=True)
    with open(BANCADA, "w", encoding="utf-8") as f:
        for row in linhas:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dict(cont)


def avaliar(lr):
    H.iniciar()
    rows = [json.loads(x) for x in open(BANCADA, encoding="utf-8")]
    out = []
    for i, obj in enumerate(rows):
        p = obj["representacoes"]["linhas"]
        path = PRIV / "paginas" / (chave(p["page_id"]) + ".json")
        if path.exists():
            out.append(ler(path))
            continue
        t0 = time.perf_counter()
        ctx, trs, q = g.preparar_pagina(obj, p)
        segmentos, _ = H.segmentar(ctx)
        probs = H.escores("ls_humana", p, ctx)
        _, cand, _ = g.candidatos(ctx)
        igrafo = H.hier1(segmentos, ctx, cand[24], probs)
        if len(ctx["cs"]) <= 67:
            hib, _ = b.prever(p, obj["palavras"], "layoutreader_pronto", lr)
        else:
            hib = ctx["ordem"]
        ordens = {"regra": ctx["ordem"], "hibrido67": hib,
                  "grafo_e004": g.decodificar(ctx, cand[24], probs, H.CFG),
                  "hier1": [u for s in segmentos for u in igrafo[s["id"]]]}
        met = {}
        for nome, ordem in ordens.items():
            m, *_ = c.medir(obj, p, ordem)
            met[nome] = {"tau": m["tau"], "quebras": m["quebras"], "sucessor": m["sucessor_linhas"]}
        row = {"page_id": p["page_id"], "uf": obj["uf"], "unidades": len(ctx["cs"]),
               "modificada": obj.get("iguais_a_origem") is False, "metricas": met,
               "segundos": time.perf_counter() - t0}
        gravar(path, row)
        out.append(row)
        print(f"[{i+1}/{len(rows)}] {row['segundos']:.1f}s", flush=True)
    return out


def bootstrap(rows, metodo, base, k, n=5000, semente=20261004):
    """IC95 percentil do delta medio, reamostrando veiculos inteiros."""
    por = collections.defaultdict(list)
    for r in rows:
        a, z = r["metricas"][metodo][k], r["metricas"][base][k]
        if a is not None and z is not None:
            por[r["uf"]].append(a - z)
    por = {u: v for u, v in por.items() if v}
    ufs = sorted(por)
    media = statistics.mean(d for u in ufs for d in por[u])
    rnd, amostras = random.Random(semente), []
    for _ in range(n):
        ds = [d for u in (rnd.choice(ufs) for _ in ufs) for d in por[u]]
        amostras.append(statistics.mean(ds))
    amostras.sort()
    return media, amostras[int(.025 * n)], amostras[int(.975 * n) - 1]


def metadados():
    """page_id -> (veiculo, bias) a partir das fichas da validacao de outubro."""
    out = {}
    for f in (V.BASE / "paginas").glob("*.json"):
        d = ler(f)
        out[d["page_id"]] = (d["veiculo"], d["bias"])
    return out


def relatorio(rows, cont):
    PUB.mkdir(parents=True, exist_ok=True)
    meta = metadados()
    for r in rows:
        exigir(r["page_id"] in meta, "Pagina sem ficha de veiculo: " + r["page_id"])
        r["uf"], r["bias"] = meta[r["page_id"]]
    estratos = {"todas": rows,
                "sem copia comprovada da pre-anotacao": [r for r in rows if r["bias"] != "igual_comprovada"]}
    resumo, L = {}, ["# E012 — bancada humana Data Policy (seed 2)", "",
                     "Gerado por `orquestracao/analises/e012_bancada_ls.py`. Só agregados: os dados e as predições "
                     "por página são do projeto parceiro (uso autorizado, não publicado) e ficam fora do git.", "",
                     f"Montagem: `{json.dumps(cont, ensure_ascii=False)}`. Veículos: {len({r['uf'] for r in rows})}.", ""]
    for nome, rs in estratos.items():
        if not rs:
            continue
        L += [f"## {nome} ({len(rs)} páginas, {len({r['uf'] for r in rs})} veículos)", "",
              "| Método | τ | Quebras/pág | Sucessor | Δ quebras vs híbrido [IC95 veículo] | Δ τ vs híbrido [IC95 veículo] |",
              "|---|---:|---:|---:|---:|---:|"]
        for mtd in METODOS:
            med = {k: statistics.mean(x for r in rs if (x := r["metricas"][mtd][k]) is not None)
                   for k in ("tau", "quebras", "sucessor")}
            resumo[f"ls_humana_{nome.split()[0]}/{mtd}"] = med
            if mtd == "hibrido67":
                dq = dt = "—"
            else:
                a = bootstrap(rs, mtd, "hibrido67", "quebras")
                t = bootstrap(rs, mtd, "hibrido67", "tau")
                dq = f"{a[0]:+.3f} [{a[1]:+.3f}; {a[2]:+.3f}]"
                dt = f"{t[0]:+.4f} [{t[1]:+.4f}; {t[2]:+.4f}]"
            L.append(f"| {mtd} | {med['tau']:.4f} | {med['quebras']:.3f} | {med['sucessor']:.4f} | {dq} | {dt} |")
        L.append("")
    L += ["Viés conhecido: a referência partiu de uma pré-anotação XY-cut; páginas aceitas sem mudança favorecem "
          "ordens parecidas com a regra. 15 páginas têm cópia comprovada da pré-anotação; nas demais a origem "
          "não pôde ser verificada. O segundo estrato exclui as 15 comprovadas.", ""]
    import re
    texto = re.sub(r"(?<=\d)\.(?=\d)", ",", "\n".join(L))
    (PUB / "RELATORIO.md").write_text(texto, encoding="utf-8")
    gravar(PUB / "resumo_registro.json", resumo)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--montar", action="store_true")
    ap.add_argument("--avaliar", action="store_true")
    a = ap.parse_args()
    cont = {}
    if a.montar or not BANCADA.exists():
        cont = montar()
        print("montagem:", cont, flush=True)
        gravar(PRIV / "montagem.json", cont)
    if a.avaliar:
        cont = cont or ler(PRIV / "montagem.json")
        lr = b.carregar_layoutreader()
        rows = avaliar(lr)
        relatorio(rows, cont)
        print((PUB / "RELATORIO.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
