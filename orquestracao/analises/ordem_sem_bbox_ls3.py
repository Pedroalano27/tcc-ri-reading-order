"""Avalia o plano de ordem sem caixas finas com o detector ls3, somente CPU.

Importa a geometria do experimento original e as reguas defensivas da revisao
justa. Mantem a grade e a politica de margens; mede principalmente a sequencia
real de palavras, sem esconder intercalacao na mediana de regioes. As caixas
do Diamond na revisao usada pelo Golden incluem figuras sem palavras para a
avaliacao do detector. Nenhum dado, fonte anterior ou quadro e alterado.

Uso na raiz: venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_ls3.py
--do-zero refaz detector e grade; --conferir verifica o relatorio salvo.
Unicas saidas: resultados/ordem_sem_bbox_ls3_pred.jsonl (cache do detector) e
resultados/ordem_sem_bbox_ls3.md (relatorio e checkpoint comprimido por pagina).
Uma linha truncada do cache apos queda e ignorada. Hashes invalidam caches
incompativeis. Nao abre PDFs nem exports LS: usa imagens e palavras congeladas.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import base64
import collections
import hashlib
import json
import math
import os
import re
import statistics
import time
import zlib

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import ordem_sem_bbox_justo as j

MD = RAIZ / "resultados/ordem_sem_bbox_ls3.md"
PRED = RAIZ / "resultados/ordem_sem_bbox_ls3_pred.jsonl"
PESOS = RAIZ / "runs/detect/ls3/weights/best.pt"
MARCADOR = "ORDEM_SEM_BBOX_LS3_CHECKPOINT_V1"
REGUAS = ("palavras", "linhas", "regioes")
METRICAS = ("tau", "sucessor", "ard")
FONTES = ("docling", "ls3", "ouro", "nenhum", "texto_ls3")
NOMES = {
    "xy_ouro": "XY-cut regiões-ouro, pura†",
    "xy_ouro_margens": "XY-cut regiões-ouro + mesmas margens†",
    "docling": "(a) Linhas + átomos Docling, LOPO",
    "ls3": "(b) Linhas + átomos ls3, LOPO",
    "ouro": "(c) Linhas + átomos ouro, LOPO†",
    "nenhum": "(d) Linhas, sem átomos, LOPO",
    "texto_ls3": "Caixas texto/tabela/imagem ls3 + XY-cut, LOPO",
    "ls3_comum": "ls3 nos parâmetros LOPO do Docling",
    "ouro_comum": "Ouro nos parâmetros LOPO do Docling†",
    "nenhum_comum": "Sem átomos nos parâmetros LOPO do Docling",
    "docling_regioes": "Docling, LOPO por τ de regiões (legado)",
}
PRINCIPAIS = ("xy_ouro", "xy_ouro_margens") + FONTES


def escrever(path, texto):
    """Fecha e sincroniza cada checkpoint antes de continuar o calculo."""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
        f.flush()
        os.fsync(f.fileno())


def digest(p):
    return j.digest(p)


def entradas(qs):
    ps = list(o.ENTRADAS) + list(o.FONTES) + [Path(o.__file__), Path(j.__file__), Path(__file__), PESOS,
        RAIZ / "src/data/taxonomia_layout.py", RAIZ / "Ultralytics/settings.json"]
    ps += [RAIZ / f"data/diamond/{l}/anotacoes.jsonl" for l in ("diamond_piloto", "diamond_treino")]
    ps += [RAIZ / "data/golden/golden_v4/img" / q["p"]["imagem"] for q in qs]
    return {p.relative_to(RAIZ).as_posix(): digest(p) for p in ps}


def preparar():
    qs = j.preparar()
    anns = {l: j.ler_jsonl(RAIZ / f"data/diamond/{l}/anotacoes.jsonl")
            for l in ("diamond_piloto", "diamond_treino")}
    for q in qs:
        p = q["p"]
        aa = [a for a in anns[p["origem"]] if a.get("page_id") == p["page_id"]
              and a.get("status") == "concluida"
              and a.get("salvo_em") == p.get("diamond", {}).get("salvo_em")]
        if len(aa) != 1:
            raise ValueError(f"Revisão Diamond congelada ausente/ambígua: {p['page_id']}")
        q["diamond_ouro"] = aa[0].get("regioes", [])
        for r in q["diamond_ouro"]:
            if len(r.get("bbox", [])) != 4 or o.area(r["bbox"]) <= 0:
                raise ValueError(f"Caixa Diamond inválida: {p['page_id']} {r}")
        q["veiculo"] = p["page_id"].split("/", 1)[0]
        q["colunas"] = j.colunas(q)
    return qs


def carregar_md():
    if not MD.exists():
        return None
    t = MD.read_text(encoding="utf-8")
    m = re.search(r"<!-- " + MARCADOR + r"\n([A-Za-z0-9+/=]+)\n-->", t)
    if not m:
        return None
    try:
        return json.loads(zlib.decompress(base64.b64decode(m.group(1))))
    except (ValueError, zlib.error):
        return None


def salvar_md(R, texto):
    raw = json.dumps(R, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ck = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
    escrever(MD, texto + f"\n<!-- {MARCADOR}\n{ck}\n-->\n")


def carregar_pred(chave):
    rows = {}
    if PRED.exists():
        with PRED.open(encoding="utf-8") as f:
            for l in f:
                try:
                    a = json.loads(l)
                except (ValueError, json.JSONDecodeError):
                    continue
                if a.get("chave") == chave:
                    rows[a["page_id"]] = a
    return rows


def detectar(qs, H, R, do_zero, threads):
    """Prediz pixels da imagem original; converte e guarda sem arredondar."""
    from importlib.metadata import version
    versoes = {n: version(n) for n in ("ultralytics", "torch", "numpy", "scipy", "Pillow")}
    meta = {"peso_sha256": H[PESOS.relative_to(RAIZ).as_posix()], "imgsz": 1024,
            "device": "cpu", "conf": 0.25, "iou_nms": 0.7, "max_det": 300,
            "threads": threads, "versoes": versoes,
            "imagens": {k: v for k, v in H.items() if "/img/" in k},
            "golden_sha256": H["data/golden/golden_v4/tarefas.jsonl"]}
    chave = hashlib.sha256(json.dumps(meta, sort_keys=True).encode("utf-8")).hexdigest()
    if R.get("chave_pred") != chave:
        R["rows"] = []
    R["chave_pred"] = chave
    pred = {} if do_zero else carregar_pred(chave)
    pids = {q["p"]["page_id"] for q in qs}
    pred = {k: v for k, v in pred.items() if k in pids}
    # Reescrever limpa cauda truncada e duplicatas; somente esta saida e tocada.
    escrever(PRED, "".join(json.dumps(v, ensure_ascii=False, allow_nan=False) + "\n"
                          for k, v in sorted(pred.items())))
    modelo = None
    R["detector"] = meta
    for i, q in enumerate(qs):
        pid = q["p"]["page_id"]
        if pid in pred:
            q["ls3"] = pred[pid]["regioes"]
            continue
        if modelo is None:
            # Configuracao ja existente/valida; nao criar settings nem salvar imagens.
            os.environ["YOLO_CONFIG_DIR"] = str(RAIZ)
            os.environ["YOLO_OFFLINE"] = "true"
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            os.environ["OMP_NUM_THREADS"] = str(threads)
            os.environ["MKL_NUM_THREADS"] = str(threads)
            import torch
            torch.set_num_threads(threads)
            torch.set_num_interop_threads(1)
            from ultralytics import YOLO
            from ultralytics.utils import SETTINGS
            # dict.__setitem__ evita a persistencia automatica de JSONDict.
            dict.__setitem__(SETTINGS, "sync", False)
            modelo = YOLO(str(PESOS))
            modelo.to("cpu")
        p = q["p"]
        img = RAIZ / "data/golden/golden_v4/img" / p["imagem"]
        with Image.open(img) as im:
            wpx, hpx = im.size
        sx, sy = p["dimensions"]["width"] / wpx, p["dimensions"]["height"] / hpx
        t0 = time.perf_counter()
        res = modelo.predict(str(img), device="cpu", imgsz=1024, conf=0.25, iou=0.7,
                             max_det=300, verbose=False, save=False, save_txt=False)[0]
        if tuple(res.orig_shape) != (hpx, wpx):
            raise ValueError(f"Geometria inesperada da imagem: {pid}")
        rr = []
        for b in res.boxes:
            cls = str(res.names[int(b.cls.item())])
            if cls not in ("texto", "tabela", "imagem"):
                raise ValueError(f"Peso não é ls3: {cls}")
            px = [float(v) for v in b.xyxy[0].tolist()]
            rr.append({"id": f"d{len(rr)}", "classe": cls, "score": float(b.conf.item()),
                       "bbox_px": px, "bbox": [px[0]*sx, px[1]*sy, px[2]*sx, px[3]*sy]})
        rec = {"page_id": pid, "chave": chave, "modelo": meta, "imagem": img.relative_to(RAIZ).as_posix(),
               "dimensions": p["dimensions"], "imagem_px": [wpx, hpx], "escala_px_pt": [sx, sy],
               "tempo_ms": (time.perf_counter()-t0)*1000, "regioes": rr}
        with PRED.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        pred[pid] = rec
        q["ls3"] = rr
        print(f"[CPU detector {i+1}/{len(qs)}] {len(rr)} caixas, {rec['tempo_ms']:.0f} ms: {pid}", flush=True)
        R["n_pred"] = len(pred)
        salvar_md(R, parcial(R))
    R["n_pred"] = len(pred)
    R["tempos_detector_ms"] = [pred[q["p"]["page_id"]]["tempo_ms"] for q in qs]
    if len(pred) != len(qs):
        raise ValueError("Cache de predições incompleto")
    return pred


def dets(q, fonte):
    if fonte == "docling":
        return q["d"].get("detector", {}).get("regioes", [])
    if fonte in ("ls3", "texto_ls3"):
        return [{"rotulo": "table" if r["classe"] == "tabela" else "picture",
                 "score": r["score"], "bbox": r["bbox"]}
                for r in q["ls3"] if r["classe"] in ("tabela", "imagem")]
    if fonte == "ouro":
        # Inclui tambem caixas sem palavras da revisao humana completa.
        return [{"rotulo": "table" if r["classe"] == "tabela" else "picture", "score": 1.0,
                 "bbox": r["bbox"]} for r in q["diamond_ouro"] if r["classe"] in ("tabela", "figura")]
    return []


def prever(q, c, fonte):
    ws, h = q["ws"], q["h"]
    ats, livres = o.atomos(ws, dets(q, fonte), c.score)
    textos = []
    fallback = len(livres)
    if fonte == "texto_ls3":
        textos = [{"tipo": "texto_ls3", "bbox": r["bbox"], "ks": [], "score": r["score"]}
                  for r in q["ls3"] if r["classe"] == "texto" and r["score"] >= c.score]
        restos = []
        for k in livres:
            cand = [m for m in textos if o.contem(m["bbox"], o.centro(ws[k]))]
            if cand:
                min(cand, key=lambda m: (o.area(m["bbox"]), -m["score"], m["bbox"]))["ks"].append(k)
            else:
                restos.append(k)
        livres = restos
        fallback = len(livres)
    items = ats + textos + o.linhas_partidas(ws, livres, c.gap, h)
    diag = {"max_colunas": 1, "pontes": 0, "n_atomos": len(ats),
            "atomos_sem_palavras": sum(not a["ks"] for a in ats), "caixas_texto": len(textos),
            "texto_sem_palavras": sum(not a["ks"] for a in textos), "fallback_palavras": fallback,
            "palavras_em_texto_ls3": sum(len(a["ks"]) for a in textos)}
    politica = "geo" if c.abordagem.endswith("margens") else None
    ini, corpo, marcas, fim = j.particao(items, ws, q["p"]["dimensions"]["height"], politica)
    diag.update(margem_topo=len(ini), margem_fim=len(fim), marcas=len(marcas))
    if c.abordagem.startswith("projecao"):
        ordem = o.ordenar_projecao(items, corpo, h, c.vale, diag, local="local" in c.abordagem)
    else:
        ordem = o.xycut(corpo, o.boxes(items))
    chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
    ordem = sorted(ini, key=chave) + ordem + sorted(marcas, key=chave) + sorted(fim, key=chave)
    if sorted(ordem) != list(range(len(items))):
        raise ValueError("Ordenador perdeu ou repetiu itens")
    items = [items[i] for i in ordem]
    seq = o.fluxo(items, ws)
    if len(seq) != len(ws) or set(seq) != set(range(len(ws))):
        raise ValueError("Saída perdeu ou repetiu palavras")
    return seq, items, diag


def avaliar(q, seq, diag=None, ordem=None):
    a = j.avaliar(q, seq, ordem)
    if diag:
        a["diag"].update(diag)
    return a


def bases(q):
    ws = q["ws"]
    items = [{"id": r["id"], "tipo": r["classe"], "bbox": r["bbox"], "ks": q["reg_words"][r["id"]]}
             for r in q["p"]["bounding_boxes"]]
    out = {}
    for nome, pol in (("xy_ouro", None), ("xy_ouro_margens", "geo")):
        ini, corpo, marcas, fim = j.particao(items, ws, q["p"]["dimensions"]["height"], pol)
        chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
        ids = sorted(ini, key=chave) + o.xycut(corpo, o.boxes(items)) + sorted(marcas, key=chave) + sorted(fim, key=chave)
        seq = o.fluxo([items[i] for i in ids], ws)
        seq += [k for k in range(len(ws)) if k not in set(q["gt_w"])]
        out[nome] = avaliar(q, seq, {"margem_topo": len(ini), "margem_fim": len(fim), "marcas": len(marcas)},
                            [items[i]["id"] for i in ids])
    return out


def iou(a, b):
    x = o.inter(a, b)
    return x / (o.area(a) + o.area(b) - x) if x else 0.0


def qualidade(q, fonte, score):
    """IoU geometrico real, casamento 1-1 de cardinalidade maxima por classe."""
    gg = [{"classe": "tabela" if r["classe"] == "tabela" else "imagem" if r["classe"] == "figura" else "texto",
           "bbox": r["bbox"], "id": r["id"]} for r in q["diamond_ouro"]]
    if fonte == "ls3":
        pp = [r for r in q["ls3"] if r["score"] >= score]
    else:
        pp = [{"classe": "tabela" if r["rotulo"] == "table" else "imagem", "bbox": r["bbox"], "id": str(i)}
              for i, r in enumerate(dets(q, fonte)) if r.get("rotulo") in ("table", "picture") and r["score"] >= score]
    out = {}
    for cls in ("tabela", "imagem"):
        gs, ps = [r for r in gg if r["classe"] == cls], [r for r in pp if r["classe"] == cls]
        pares = []
        if gs and ps:
            M = np.array([[iou(g["bbox"], p["bbox"]) for p in ps] for g in gs])
            reward = (M >= 0.5) * (1 + M / (min(M.shape) + 1))
            ii, jj = linear_sum_assignment(-reward)
            pares = [{"ouro": gs[a]["id"], "pred": ps[b]["id"], "iou": float(M[a, b])}
                     for a, b in zip(ii, jj) if M[a, b] >= 0.5]
        out[cls] = {"ouro": len(gs), "pred": len(ps), "tp": len(pares), "pares": pares,
                    "sem_par_ouro": [g for g in gs if g["id"] not in {m["ouro"] for m in pares}],
                    "sem_par_pred": [p for p in ps if p["id"] not in {m["pred"] for m in pares}]}
    return out


def compacto(a):
    # Guarda toda a grade, mas as ordens reais so nas variantes selecionadas.
    return {r: a[r] for r in REGUAS} | {"diag": a["diag"]}


def parcial(R):
    rows = R.get("rows", [])
    out = ["# Ordem sem bbox fina com ls3 — execução parcial", "",
           f"Detector: {R.get('n_pred', 0)} páginas em cache. Grade: {len(rows)} páginas concluídas.",
           "Resultados parciais; o veredito será escrito após seleção e inferência agrupada.", ""]
    if rows:
        cid = "projecao_local_margens_s0.45_g1.2_v0.08"
        out += ["| Fonte (configuração fixa provisória) | τ de palavras | Sucessor |", "|---|---:|---:|"]
        for fonte in FONTES[:4]:
            vals = [r["variantes"][fonte][cid]["palavras"] for r in rows]
            out.append(f"| {fonte} | {f(media([v['tau'] for v in vals]))} | {f(100*media([v['sucessor'] for v in vals]),1)}% |")
    return "\n".join(out) + "\n"


def media(v):
    a = [x for x in v if x is not None and math.isfinite(x)]
    return statistics.mean(a) if a else None


def f(x, n=3):
    return "—" if x is None or not math.isfinite(x) else f"{x:.{n}f}".replace(".", ",")


def grade(fonte):
    return [c for c in o.grade() if fonte != "texto_ls3" or not c.abordagem.startswith("projecao")]


def matrizes(rows, fonte, regua="palavras", m="tau"):
    cs = grade(fonte)
    return np.array([[r["variantes"][fonte][c.id][regua][m] for r in rows] for c in cs], dtype=float)


def escolher(T, U, W, excluidos):
    """Uma escolha por reamostra e por pagina; copia retida nunca e treinamento."""
    T, U = np.nan_to_num(T), np.nan_to_num(U)
    totals, suc = W @ T.T, W @ U.T
    ids = np.zeros((len(W), T.shape[1]), dtype=int)
    for p in range(T.shape[1]):
        ix = excluidos[p]
        A = np.round(totals - W[:, ix] @ T[:, ix].T, 12)
        B = np.round(suc - W[:, ix] @ U[:, ix].T, 12)
        emp = A == A.max(axis=1, keepdims=True)
        ids[:, p] = np.argmax(np.where(emp, B, -np.inf), axis=1)
    return ids


def pesos_cluster(qs, nboot, seed):
    grupos = sorted({q["veiculo"] for q in qs})
    gi = np.array([grupos.index(q["veiculo"]) for q in qs])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(grupos), size=(nboot, len(grupos)))
    counts = np.zeros((nboot, len(grupos)))
    for g in range(len(grupos)):
        counts[:, g] = (draws == g).sum(axis=1)
    return counts[:, gi], gi, grupos


def resumir(v, W):
    v = np.array(v, dtype=float)
    valid = np.isfinite(v)
    den = W @ valid.astype(float)
    boot = np.divide(W @ np.nan_to_num(v), den, out=np.full(len(W), np.nan), where=den > 0)
    return {"media": float(np.nanmean(v)) if valid.any() else None,
            "ic95": np.nanquantile(boot, [0.025, 0.975]).tolist() if np.isfinite(boot).any() else [None, None],
            "n": int(valid.sum())}, boot


def selecionados(R, qs, W, gi):
    rows = R["rows"]
    selections, boot_ids, metodos, specs = {}, {}, {}, {}
    for fonte in FONTES:
        specs[fonte] = (fonte, "palavras", "page")
    specs["docling_regioes"] = ("docling", "regioes", "page")
    for nome, (fonte, regua, fold) in specs.items():
        T = matrizes(rows, fonte, regua, "tau")
        U = matrizes(rows, fonte, regua, "sucessor")
        excluded = [[p] for p in range(len(rows))]
        selections[nome] = escolher(T, U, np.ones((1, len(rows))), excluded)[0].tolist()
        boot_ids[nome] = escolher(T, U, W, excluded)
        cs = grade(fonte)
        metodos[nome] = [rows[p]["variantes"][fonte][cs[idx].id] for p, idx in enumerate(selections[nome])]
    for fonte in ("ls3", "ouro", "nenhum"):
        nome = fonte + "_comum"
        selections[nome] = selections["docling"]
        boot_ids[nome] = boot_ids["docling"]
        specs[nome] = (fonte, "palavras", "page")
        cs = grade(fonte)
        metodos[nome] = [rows[p]["variantes"][fonte][cs[idx].id] for p, idx in enumerate(selections[nome])]
    for nome in ("xy_ouro", "xy_ouro_margens"):
        metodos[nome] = [r["bases"][nome] for r in rows]
    sumarios, boots = {}, {}
    for nome, regs in metodos.items():
        sumarios[nome], boots[nome] = {}, {}
        for regua in REGUAS:
            sumarios[nome][regua], boots[nome][regua] = {}, {}
            for m in METRICAS:
                if nome in specs:
                    fonte = specs[nome][0]
                    mat = matrizes(rows, fonte, regua, m)
                    vals = mat[boot_ids[nome], np.arange(len(rows))[None, :]]
                    valid = np.isfinite(vals)
                    den = (W * valid).sum(axis=1)
                    boot = np.divide((W * np.nan_to_num(vals)).sum(axis=1), den,
                                     out=np.full(len(W), np.nan), where=den > 0)
                    stat = {"media": media([r[regua][m] for r in regs]),
                            "ic95": np.nanquantile(boot, [0.025, 0.975]).tolist(),
                            "n": sum(r[regua][m] is not None for r in regs)}
                else:
                    stat, boot = resumir([r[regua][m] for r in regs], W)
                sumarios[nome][regua][m], boots[nome][regua][m] = stat, boot
        vals = [r["diag"]["fracao"] for r in regs]
        sumarios[nome]["fragmentacao"], _ = resumir(vals, W)
        sumarios[nome]["paginas_fragmentadas"] = sum((v or 0) > 0 for v in vals)
        sumarios[nome]["fragmentacao_estrita"] = media([r["diag"]["fracao_estrita"] for r in regs])
    R["selecao"] = {n: [grade(specs[n][0])[i].id for i in ids] for n, ids in selections.items()}
    R["resumo"] = sumarios
    R["por_metodo"] = metodos
    return metodos, boots


def pratt(d):
    d = np.round(np.asarray(d, dtype=float), 12)
    d = d[np.isfinite(d)]
    if not len(d) or np.all(d == 0):
        return 1.0
    return float(wilcoxon(d, zero_method="pratt", alternative="two-sided", method="auto").pvalue)


def contrastes(R, metodos, boots, gi):
    out = []
    for a, b in (("ls3", "docling"), ("ls3_comum", "docling"), ("texto_ls3", "ls3"),
                 ("ls3", "nenhum"), ("ls3", "xy_ouro_margens")):
        for regua in REGUAS:
            for m in METRICAS:
                d = np.array([x[regua][m] - y[regua][m] if x[regua][m] is not None and y[regua][m] is not None
                              else np.nan for x, y in zip(metodos[a], metodos[b])])
                dg = np.array([np.nanmean(d[gi == g]) for g in sorted(set(gi))])
                boot = boots[a][regua][m] - boots[b][regua][m]
                sign = -1 if m == "ard" else 1
                out.append({"a": a, "b": b, "regua": regua, "metrica": m,
                            "delta": float(np.nanmean(d)), "ic95": np.nanquantile(boot, [0.025, 0.975]).tolist(),
                            "pratt_paginas": pratt(d), "pratt_veiculos": pratt(dg),
                            "ganha": int(sum(sign*d > 1e-12)), "empata": int(sum(abs(d) <= 1e-12)),
                            "perde": int(sum(sign*d < -1e-12))})
    for campo in ("pratt_paginas", "pratt_veiculos"):
        maior = 0
        for k, a in enumerate(sorted(out, key=lambda a: a[campo])):
            maior = max(maior, min(1, (len(out)-k)*a[campo]))
            a[campo + "_holm"] = maior
    R["contrastes"] = out


def evidencia_atomos(q, items):
    tipos = {r["id"]: r["classe"] for r in q["p"]["bounding_boxes"]}
    dono = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
    out = []
    for m in items:
        if m["tipo"] not in ("table", "picture"):
            continue
        cont = collections.Counter(dono[k] for k in m["ks"] if k in dono)
        out.append({"tipo": m["tipo"], "bbox": m["bbox"], "palavras": len(m["ks"]),
                    "ouro_coberto": dict(cont),
                    "palavras_de_texto": sum(n for rid, n in cont.items() if tipos[rid] not in ("tabela", "figura"))})
    return out


def erros(R, qs):
    out = []
    for p, q in enumerate(qs):
        seqs, ev = {}, {}
        classes = {r["id"]: r["classe"] for r in q["p"]["bounding_boxes"]}
        dono = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
        for fonte in ("docling", "ls3", "ls3_comum", "texto_ls3"):
            src = "ls3" if fonte == "ls3_comum" else fonte
            cid = R["selecao"][fonte][p]
            c = next(c for c in grade(src) if c.id == cid)
            seq, items, diag = prever(q, c, src)
            med = avaliar(q, seq, diag)
            if compacto(med) != R["por_metodo"][fonte][p]:
                raise ValueError(f"Variante selecionada não reproduziu cache: {fonte} {p}")
            seqs[fonte] = seq
            runs = []
            for k in seq:
                rid = dono.get(k, "SEM_OURO")
                if not runs or runs[-1]["id"] != rid:
                    runs.append({"id": rid, "n": 1})
                else:
                    runs[-1]["n"] += 1
            at = evidencia_atomos(q, items)
            dist = {rid: [m["ouro_coberto"].get(rid, 0) for m in at if m["tipo"] == "table"]
                    for rid, cls in classes.items() if cls == "tabela"}
            tx = [m for m in items if m["tipo"] == "texto_ls3"]
            ev[fonte] = {"config": cid, "atomos": evidencia_atomos(q, items),
                          "sequencia_palavras": seq, "diag": med["diag"], "trechos_regioes": runs,
                          "palavras_tabela_por_atomo": dist,
                          "tabelas_primeira_ocorrencia": list(dict.fromkeys(r["id"] for r in runs
                                                             if classes.get(r["id"]) == "tabela")),
                          "caixas_texto": [{"bbox": m["bbox"], "palavras": len(m["ks"])} for m in tx]}
        dif = seqs["docling"] != seqs["ls3"]
        a, b = R["por_metodo"]["docling"][p], R["por_metodo"]["ls3"][p]
        comum = R["por_metodo"]["ls3_comum"][p]
        gt = q["gt_w"]
        # Pares de palavras vizinhas no ouro: evidencia da continuidade real.
        consertos, quebras = [], []
        apos = {n: {a: b for a, b in zip(s, s[1:])} for n, s in seqs.items()}
        for k1, k2 in zip(gt, gt[1:]):
            aa, bb = apos["docling"].get(k1) == k2, apos["ls3"].get(k1) == k2
            if aa != bb:
                (consertos if bb else quebras).append([k1, k2])
        atom_a, atom_b = ev["docling"]["atomos"], ev["ls3"]["atomos"]
        capt_a, capt_b = sum(x["palavras_de_texto"] for x in atom_a), sum(x["palavras_de_texto"] for x in atom_b)
        razoes = []
        for rid, dist_a in ev["docling"]["palavras_tabela_por_atomo"].items():
            dist_b = ev["ls3"]["palavras_tabela_por_atomo"][rid]
            if sum(n > 0 for n in dist_a) > 1 and sum(n > 0 for n in dist_b) == 1:
                razoes.append(f"tabela {rid}: palavras repartidas em {sum(n > 0 for n in dist_a)} átomos Docling passam a um átomo ls3; leitura interna deixa de ser separada por caixas")
        ta, tb = (ev[n]["tabelas_primeira_ocorrencia"] for n in ("docling", "ls3"))
        if ta != tb and ta and tb:
            razoes.append(f"ordem de primeira ocorrência de tabelas muda de {'→'.join(ta)} para {'→'.join(tb)}")
        if capt_b > capt_a:
            razoes.append(f"ls3 põe {capt_b-capt_a} palavras textuais adicionais em átomos; possível fusão indevida")
        elif capt_b < capt_a:
            razoes.append(f"ls3 libera {capt_a-capt_b} palavras textuais antes capturadas por átomos Docling")
        if len(atom_a) != len(atom_b):
            razoes.append(f"quantidade de átomos {len(atom_a)}→{len(atom_b)} muda as barreiras da ordenação")
        if ev["docling"]["config"] != ev["ls3"]["config"]:
            razoes.append("a seleção também muda parâmetros; consultar troca com configuração comum")
            if a["palavras"]["tau"] is not None and comum["palavras"]["tau"] is not None and abs(comum["palavras"]["tau"]-a["palavras"]["tau"]) <= 1e-12:
                razoes.insert(0, "diferença desaparece com parâmetros comuns: efeito da seleção da família, não evidência isolada do detector")
        if dif and not razoes:
            razoes.append("caixas atômicas mudam envelopes/cortes mesmo com contagens iguais")
        if not dif:
            razoes.append("saída de palavras idêntica")
        out.append({"page_id": q["p"]["page_id"], "colunas": q["colunas"], "mudou": dif,
                    "delta_tau": b["palavras"]["tau"]-a["palavras"]["tau"] if len(gt) > 1 else None,
                    "delta_sucessor": b["palavras"]["sucessor"]-a["palavras"]["sucessor"] if len(gt) > 1 else None,
                    "delta_comum": comum["palavras"]["tau"]-a["palavras"]["tau"] if len(gt) > 1 else None,
                    "pares_consertados": consertos, "pares_quebrados": quebras,
                    "evidencia": ev, "motivos_geometricos": razoes})
    R["erros"] = out
    maiores = sorted((e for e in out if (e["delta_tau"] or 0) > 0), key=lambda e: e["delta_tau"], reverse=True)[:2]
    ids = {e["page_id"] for e in maiores}
    R["concentracao_ganho"] = {"paginas": sorted(ids),
                              "delta_sem_maiores": media([e["delta_tau"] for e in out if e["page_id"] not in ids]),
                              "contribuicao_macro": sum(e["delta_tau"] for e in maiores)/len(out)}


def detector_resumo(R):
    sums = {}
    for fonte in ("docling", "ls3"):
        for score in (0.25, 0.45):
            for cls in ("tabela", "imagem"):
                chave = f"{fonte}_{score:.2f}_{cls}"
                vals = [r["qualidade"][f"{fonte}_{score:.2f}"][cls] for r in R["rows"]]
                ng, npred, tp = [sum(v[k] for v in vals) for k in ("ouro", "pred", "tp")]
                sums[chave] = {"ouro": ng, "pred": npred, "tp": tp, "fp": npred-tp, "fn": ng-tp,
                               "revocacao": tp/ng if ng else None, "precisao": tp/npred if npred else None,
                               "tp_geometria_identica": sum(abs(par["iou"]-1) <= 1e-10 for v in vals for par in v["pares"])}
    R["qualidade_detector"] = sums


def estratos(R, qs, metodos, W):
    out = {}
    for rotulo, ids in (("uma coluna geométrica", [i for i, q in enumerate(qs) if q["colunas"]["n"] == 1]),
                        ("multicoluna geométrica", [i for i, q in enumerate(qs) if q["colunas"]["n"] > 1])):
        if not ids:
            continue
        ss = {}
        for nome in PRINCIPAIS:
            ss[nome] = {m: resumir([metodos[nome][i]["palavras"][m] for i in ids], W[:, ids])[0] for m in METRICAS}
            ss[nome]["fragmentacao"] = media([metodos[nome][i]["diag"]["fracao"] for i in ids])
            ss[nome]["tau_linhas"] = media([metodos[nome][i]["linhas"]["tau"] for i in ids])
        out[rotulo] = {"n": len(ids), "metodos": ss}
    R["estratos"] = out
    # Sensibilidade LOVO: mesmas grades, excluindo todas as paginas do veiculo.
    excluded = [[i for i, qq in enumerate(qs) if qq["veiculo"] == q["veiculo"]] for q in qs]
    lovo = {}
    for fonte in FONTES:
        ids = escolher(matrizes(R["rows"], fonte), matrizes(R["rows"], fonte, m="sucessor"),
                       np.ones((1, len(qs))), excluded)[0]
        vals = [R["rows"][p]["variantes"][fonte][grade(fonte)[i].id] for p, i in enumerate(ids)]
        lovo[fonte] = {m: media([v["palavras"][m] for v in vals]) for m in METRICAS}
        lovo[fonte]["fragmentacao"] = media([v["diag"]["fracao"] for v in vals])
    R["lovo"] = lovo


def controles():
    """Casos substantivos: intercalacao, paginas/caixas vazias, pixels e IoU."""
    q = {"ws": [["a", 0, 0, 1, 1], ["b", 0, 2, 1, 3], ["c", 2, 0, 3, 1], ["d", 2, 2, 3, 3]],
         "p": {"bounding_boxes": [{"id": "A", "bbox": [0, 0, 1, 3]}, {"id": "B", "bbox": [2, 0, 3, 3]}]},
         "gt_r": ["A", "B"], "gt_l": ["A0", "A1", "B0", "B1"], "gt_w": [0, 1, 2, 3],
         "reg_words": {"A": [0, 1], "B": [2, 3]},
         "gold_lines": [{"id": s, "ks": [k], "bbox": [0, k, 1, k+1]} for k, s in enumerate(["A0", "A1", "B0", "B1"])]}
    a = avaliar(q, [0, 2, 1, 3])
    if a["regioes"]["tau"] != 1 or not (a["palavras"]["tau"] < 1 and a["diag"]["fracao"] == 1):
        raise ValueError("Regua principal nao detecta intercalacao")
    vazia = {"ws": [], "p": {"bounding_boxes": [{"id": "Z", "bbox": [0, 0, 10, 10]}]},
             "gt_r": ["Z"], "gt_l": [], "gt_w": [], "reg_words": {"Z": []}, "gold_lines": []}
    a = avaliar(vazia, [])
    if a["palavras"]["tau"] is not None or a["diag"]["regioes_sem_palavras"] != ["Z"]:
        raise ValueError("Pagina vazia ganhou medida perfeita ou perdeu diagnostico")
    q2 = dict(q, p={**q["p"], "dimensions": {"height": 10}}, h=1,
              diamond_ouro=[], d={"detector": {"regioes": []}}, ls3=[])
    for fonte in FONTES:
        for caso in (q2, dict(q2, ws=[], gt_w=[])):
            seq, _, _ = prever(caso, o.Config("xy_margens", 0.45, 1.2), fonte)
            if set(seq) != set(range(len(caso["ws"]))):
                raise ValueError("Fallback perdeu palavras")
    g = {"diamond_ouro": [{"id": "a", "classe": "tabela", "bbox": [0, 0, 10, 10]}],
         "ls3": [{"id": "1", "classe": "tabela", "bbox": [0, 0, 10, 10], "score": .9},
                 {"id": "2", "classe": "tabela", "bbox": [0, 0, 10, 10], "score": .8}]}
    if qualidade(g, "ls3", .25)["tabela"]["tp"] != 1:
        raise ValueError("Casamento contou duplicata como TP")
    if pratt([0, 0, 0]) != 1:
        raise ValueError("Pratt nao preservou empates")
    T = np.array([[1, .4, .2], [.2, .8, .4], [.4, .6, .9]])
    U = np.array([[.1, .2, .3], [.3, .2, .1], [.5, .5, .5]])
    W = np.array([[1, 1, 1], [2, 1, 1], [0, 4, 2]])
    excluidos = [[p] for p in range(T.shape[1])]
    ids = escolher(T, U, W, excluidos)
    for b, w in enumerate(W):
        for p in range(T.shape[1]):
            treino = w.copy()
            treino[p] = 0
            esperado = max(range(len(T)), key=lambda i: (round(float(T[i] @ treino), 12),
                                                        round(float(U[i] @ treino), 12), -i))
            if ids[b, p] != esperado:
                raise ValueError("Bootstrap vetorizado diverge da selecao LOPO direta")
    return ["intercalação detectada em palavras apesar de mediana perfeita", "página e região vazias sem assert",
            "fallback sem detecção preserva palavras nas fontes", "casamento IoU não duplica TP", "Pratt preserva zeros",
            "seleção bootstrap coincide com LOPO direto e exclui cópias da página"]


def cel(x, percentual=False):
    s = 100 if percentual else 1
    n = 1 if percentual else 3
    return f"{f(x['media']*s if x['media'] is not None else None,n)}{'%' if percentual else ''} [{f(x['ic95'][0]*s if x['ic95'][0] is not None else None,n)}; {f(x['ic95'][1]*s if x['ic95'][1] is not None else None,n)}]"


def tabela(R, nomes, regua):
    out = ["| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ | ARD norm. ↓ | Regiões fragmentadas |",
           "|---|---:|---:|---:|---:|"]
    for n in nomes:
        s = R["resumo"][n]
        out.append(f"| {NOMES[n]} | {cel(s[regua]['tau'])} | {cel(s[regua]['sucessor'],True)} | {cel(s[regua]['ard'])} | {f(100*s['fragmentacao']['media'],1)}% |")
    return out


def contraste(R, a, b, regua="palavras", metrica="tau"):
    return next(t for t in R["contrastes"] if (t["a"], t["b"], t["regua"], t["metrica"]) == (a, b, regua, metrica))


def veredito(R):
    t = contraste(R, "ls3", "docling")
    u = contraste(R, "ls3", "docling", metrica="sucessor")
    if t["ic95"][0] > 0 and t["pratt_veiculos_holm"] < .05 and u["delta"] >= 0:
        return "ls3 melhora a ordem nesta amostra exploratória; confirmar em veículos e ouro novos antes de substituir Docling."
    if t["delta"] < 0:
        return "a troca para ls3 não melhorou a ordem média; manter Docling como comparador e validar o detector em ouro novo."
    return "ls3 é uma alternativa viável nesta amostra, mas a superioridade sobre Docling não ficou demonstrada."


def relatorio(R):
    S, A = R["resumo"], R["auditoria"]
    t = contraste(R, "ls3", "docling")
    u = contraste(R, "texto_ls3", "ls3")
    common = contraste(R, "ls3_comum", "docling")
    out = ["# Plano do orientador de ponta a ponta com o detector ls3", "", "## Resumo em cinco linhas", "",
           f"1. Nas {A['paginas']} páginas de {A['veiculos']} veículos, a saída real tem τ de palavras {f(S['docling']['palavras']['tau']['media'])} com Docling e {f(S['ls3']['palavras']['tau']['media'])} com ls3; Δ = {f(t['delta'])}, IC 95% [{f(t['ic95'][0])}; {f(t['ic95'][1])}].",
           f"2. A XY-cut ouro com as mesmas margens chega a {f(S['xy_ouro_margens']['palavras']['tau']['media'])}; a fração de regiões fragmentadas é {f(100*S['ls3']['fragmentacao']['media'],1)}% no ls3.",
           f"3. A variante que ordena caixas de texto ls3 chega a {f(S['texto_ls3']['palavras']['tau']['media'])}; ganho sobre usar apenas seus átomos = {f(u['delta'])} (IC [{f(u['ic95'][0])}; {f(u['ic95'][1])}]).",
           f"4. A IoU ≥ 0,5/confiança ≥ 0,25, ls3 tem revocação/precisão de tabela {f(100*R['qualidade_detector']['ls3_0.25_tabela']['revocacao'],1)}%/{f(100*R['qualidade_detector']['ls3_0.25_tabela']['precisao'],1)}% e imagem {f(100*R['qualidade_detector']['ls3_0.25_imagem']['revocacao'],1)}%/{f(100*R['qualidade_detector']['ls3_0.25_imagem']['precisao'],1)}%.",
           f"5. **Veredito: {veredito(R)}** Amostra pequena, desenvolvimento no próprio Golden e viés de ancoragem impedem uma conclusão confirmatória.",
           "", "## Protocolo e leitura das réguas", "",
           "Detector local nas imagens do `golden_v4`, `YOLO(best.pt).predict(..., device=\"cpu\", imgsz=1024, conf=0.25, iou=0.7, max_det=300)`. Caixas em pixels originais convertidas por escalas separadas largura/altura para pontos PDF; sem arredondamento. Nomes de classes vêm dos pesos. Palavras vêm do Diamond congelado: não há OCR nem abertura/reextração de PDFs. Assim, ponta a ponta aqui é detector→itens→ordem da camada digital existente, e não imagem→transcrição de PDFs escaneados.",
           f"Grade original congelada: {len(o.grade())} variantes por fonte de átomos; {len(grade('texto_ls3'))} na família XY-cut de caixas ls3. Mesmos limiares de confiança, gap e vales do anterior. Átomos passam pela mesma supressão conservadora; cada palavra tem um único dono. Sem átomos, todas as palavras passam por linhas/gaps. Caixas de texto ls3 recebem palavras por centro e menor caixa, depois da prioridade tabela/imagem; palavras livres viram linhas e não são descartadas. Dentro de cada caixa/átomo, `linhas()` emite de cima para baixo e da esquerda para a direita.",
           "Seleção leave-one-page-out (LOPO) igual para as quatro fontes: maximizar média de τ de **palavras** nas demais páginas; desempatar pelo sucessor de palavras e pela ordem original da grade. O ouro humano entra só na avaliação/seleção e na fonte (c), diagnóstico indisponível em produção. A linha legado mantém seleção por τ de regiões para reproduzir o anterior; ela não governa o veredito. A troca em configuração comum usa, em cada página, exatamente os parâmetros selecionados pelo Docling.",
           "Mesma política geométrica em métodos com margens e na baseline justa: marcas primeiro na classificação (todas as palavras casam com `RE_MARCACAO`); topo se centro < 7% e base < 10% da altura; rodapé se centro > 95%. Saída = topo, corpo ordenado, marcas, rodapé. Os limiares e desempates são literalmente os anteriores, sem classes humanas de margem.",
           "**Régua principal: sequência real de palavras**, identificadas por índice, sem projeção por mediana. Ouro = regiões na ordem humana e palavras ordenadas por `linhas()` dentro de cada região: a ordem interna não foi anotada separadamente. Reportamos τ, sucessor e ARD macro por página. Sucessor de palavras pode ser alto pela preservação dos pares internos; ler junto com fragmentação. **Regiões e linhas são réguas secundárias**, projetadas por mediana, que podem esconder texto intercalado. Fragmentação = fração das regiões com palavras que reaparecem em mais de um trecho. Palavras fora do ouro são mantidas na saída, mas não têm referência de ordem; também calculamos fragmentação estrita, que as considera interrupção.",
           f"Auditoria: {A['palavras']} palavras na entrada, {A['palavras_avaliadas']} com referência, {A['sem_ouro']} fora do ouro, {A['ambiguas']} com dono ambíguo; {A['regioes']} regiões e {A['linhas']} linhas avaliadas. Regiões sem palavras = {A['regioes_vazias']}; páginas sem palavras = {A['paginas_vazias']}. A preparação do Golden havia retirado {A['visuais_retiradas']} caixas sem texto; o detector é avaliado contra {A['diamond_regioes']} caixas Diamond completas, incluindo {A['diamond_vazias']} sem palavras. A ordem dessas caixas retiradas não é recuperável da anotação Golden e não entra na régua de palavras.",
           "", "## Tabela principal — saída real de palavras", "",
           "† usa informação humana em produção ou como diagnóstico; não é um concorrente de detecção autônoma.", ""]
    out += tabela(R, PRINCIPAIS, "palavras")
    out += ["", "## Troca com parâmetros comuns e seleção legada", ""] + tabela(R,
            ("docling", "ls3_comum", "ouro_comum", "nenhum_comum", "docling_regioes"), "palavras")
    out += ["", f"Com parâmetros iguais, Δ ls3−Docling = {f(common['delta'])}, IC [{f(common['ic95'][0])}; {f(common['ic95'][1])}]. Diferenças entre essa linha e (b) decorrem da seleção por fonte. O oráculo pode piorar: átomos perfeitos não corrigem automaticamente cortes, pontes ou a leitura interna de tabelas.",
            "", "## Réguas secundárias", "", "### Regiões por mediana", ""]
    out += tabela(R, PRINCIPAIS, "regioes")
    out += ["", "### Linhas por mediana", ""] + tabela(R, PRINCIPAIS, "linhas")
    out += ["", "| Método | Páginas com regiões fragmentadas | Fração estrita média |", "|---|---:|---:|"]
    for n in PRINCIPAIS:
        out.append(f"| {NOMES[n]} | {S[n]['paginas_fragmentadas']}/{A['paginas']} | {f(100*S[n]['fragmentacao_estrita'],1)}% |")
    out += ["", "## Detector contra Diamond completo (colapso em três classes)", "",
            "Usamos a revisão Diamond com o mesmo `salvo_em` registrada pelo Golden, incluindo regiões sem texto. Colapso solicitado: tabela→tabela, figura→imagem, demais classes Diamond→texto. Este colapso das nove classes não recupera a distinção manuscrita `heading` das dezesseis classes LS. Não excluímos `outro` do Diamond. Casamento geométrico 1–1 por classe, de cardinalidade máxima, desempatado pela soma de IoUs; aceitação IoU ≥ 0,5. Precisão/revocação micro sobre todas as páginas, não Jaccard de palavras. Confiança fixa 0,25 é a saída usual do detector; 0,45 é sensibilidade ao menor limiar usado na grade de átomos. Não se seleciona o limiar usando os TPs.",
            "Docling usa o cache do experimento anterior, previamente filtrado com `score_min` = " +
            ", ".join(f(s,2) for s in R["docling_cache"]["score_min"]) +
            ". A linha Docling a confiança 0,25 apenas reavalia esse cache: não recupera detecções abaixo do filtro original e não é uma nova inferência a 0,25. A comparação em 0,45 compartilha o piso de confiança, mas os scores dos modelos não são calibrados entre si.",
            "", "| Detector | Confiança | Classe | Ouro | Preditas | TP | FP | FN | Revocação | Precisão |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for fonte in ("docling", "ls3"):
        for score in (.25, .45):
            for cls in ("tabela", "imagem"):
                v = R["qualidade_detector"][f"{fonte}_{score:.2f}_{cls}"]
                out.append(f"| {fonte} | {f(score,2)} | {cls} | {v['ouro']} | {v['pred']} | {v['tp']} | {v['fp']} | {v['fn']} | {f(100*v['revocacao'],1)}% | {f(100*v['precisao'],1)}% |")
    out += ["", "**Sinal mensurável de ancoragem:** entre os acertos a confiança 0,25, há " +
            "; ".join(f"{src}/{cls}: {R['qualidade_detector'][f'{src}_0.25_{cls}']['tp_geometria_identica']} caixas com IoU exatamente 1"
                      for src in ("docling", "ls3") for cls in ("tabela", "imagem")) +
            ". Coincidência de geometria é esperada quando uma proposta é mantida; isso favorece o detector de origem na avaliação de caixas. Não prova que a caixa esteja errada, mas reforça a necessidade de ouro desenhado do zero. Os totais de caixas retiradas no preparo e de caixas geometricamente sem palavras medem critérios distintos, não são contagens intercambiáveis."]
    out += ["", "## Inferência pareada", "",
            f"Bootstrap percentil com {R['bootstrap']['n']} reamostras e semente {R['bootstrap']['seed']}: sorteamos veículos com reposição, preservamos todas as páginas do grupo e recalculamos a média macro por página. **A escolha LOPO é refeita dentro de cada reamostra**, a partir da grade congelada; excluímos todas as cópias da página retida, mas suas páginas irmãs continuam, como no LOPO solicitado. Isto não torna LOPO um teste em veículos desconhecidos. Os IC de fragmentação e de estratos são condicionais às escolhas já feitas. Bootstrap não refaz o desenvolvimento do algoritmo nem o treino do detector.",
            f"Wilcoxon bilateral com `zero_method=\"pratt\"`; diferenças arredondadas a doze casas para identificar empates numéricos. Por página é diagnóstico dependente; também mostramos Pratt nas médias por veículo. Holm cobre conjuntamente os {len(R['contrastes'])} contrastes/réguas/métricas apresentados em cada unidade; não corrige a exploração histórica. IC e testes não demonstram equivalência. Ganho/empate/perda inverte o sinal para ARD.",
            "", "| Contraste A−B | Régua/métrica | Δ (IC por veículo, seleção refeita) | G/E/P | Pratt página | Pratt veículo | Holm veículo |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for v in R["contrastes"]:
        out.append(f"| {v['a']}−{v['b']} | {v['regua']}/{v['metrica']} | {f(v['delta'])} [{f(v['ic95'][0])}; {f(v['ic95'][1])}] | {v['ganha']}/{v['empata']}/{v['perde']} | {f(v['pratt_paginas'],6)} | {f(v['pratt_veiculos'],6)} | {f(v['pratt_veiculos_holm'],6)} |")
    out += ["", "## Colunas e sensibilidade por veículo", "",
            "Estrato congelado e sem ouro: calhas recorrentes estimadas pelas palavras do corpo (mesmo critério da reanálise justa). É uma classificação geométrica, não uma contagem visual humana; pode errar. Guardamos também o metadado antigo para auditoria. IC destes estratos é condicional às configurações globais, sem repetir seleção no estrato.", "",
            "| Estrato | n | Método | τ palavras | Sucessor palavras | Fragmentação |", "|---|---:|---|---:|---:|---:|"]
    for estrato, obj in R["estratos"].items():
        for n in PRINCIPAIS:
            v = obj["metodos"][n]
            out.append(f"| {estrato} | {obj['n']} | {NOMES[n]} | {cel(v['tau'])} | {cel(v['sucessor'],True)} | {f(100*v['fragmentacao'],1)}% |")
    out += ["", "LOVO, apenas sensibilidade: exclui o veículo inteiro do ajuste, mas o desenvolvimento histórico ainda viu estas páginas.", "",
            "| Fonte | τ palavras LOPO | τ palavras LOVO | Sucessor LOVO | Fragmentação LOVO |", "|---|---:|---:|---:|---:|"]
    for n in FONTES:
        v = R["lovo"][n]
        out.append(f"| {n} | {f(S[n]['palavras']['tau']['media'])} | {f(v['tau'])} | {f(100*v['sucessor'],1)}% | {f(100*v['fragmentacao'],1)}% |")
    ee = R["erros"]
    out += ["", "## Análise de erro: onde a troca muda a saída", "",
            f"Saída real alterada em {sum(e['mudou'] for e in ee)}/{len(ee)} páginas. Em τ de palavras, ls3 melhora/empata/piora {t['ganha']}/{t['empata']}/{t['perde']}; pares consecutivos corrigidos = {sum(len(e['pares_consertados']) for e in ee)}, quebrados = {sum(len(e['pares_quebrados']) for e in ee)}. Esses pares são contados na saída integral, inclusive interrupções por palavras fora do ouro. Motivos abaixo são **diagnósticos geométricos**, não prova causal; a coluna comum isola a troca do detector. Caixas ls3 maiores podem fundir colunas; caixas menores podem liberar texto e também perder tabelas.", "",
            "| Página | Δ τ palavras | Δ sucessor (pp) | Δ τ parâmetros comuns | Átomos Docling→ls3 | Evidência / hipótese |",
            "|---|---:|---:|---:|---:|---|"]
    ganhos = sorted([e for e in ee if (e['delta_tau'] or 0) > 1e-12], key=lambda e: e['delta_tau'], reverse=True)[:5]
    perdas = sorted([e for e in ee if (e['delta_tau'] or 0) < -1e-12], key=lambda e: e['delta_tau'])[:5]
    for e in ganhos + perdas:
        ev = e["evidencia"]
        out.append(f"| `{e['page_id']}` | {f(e['delta_tau'],6)} | {f(100*e['delta_sucessor'],2)} | {f(e['delta_comum'],6)} | {len(ev['docling']['atomos'])}→{len(ev['ls3']['atomos'])} | {'; '.join(e['motivos_geometricos'])} |")
    conc = R["concentracao_ganho"]
    out += ["", f"**Concentração do ganho:** as {len(conc['paginas'])} maiores melhorias contribuem {f(conc['contribuicao_macro'])} para a média macro. Sem essas páginas, a diferença média é {f(conc['delta_sem_maiores'])}. Isto é diagnóstico de influência, não uma nova amostra de teste nem justificativa para excluir páginas."]
    # Explicacoes produzidas dos trechos reais, nao de numeros escritos a mao.
    elegiveis = [e for e in ee if e["delta_comum"] is not None]
    inspecoes = (max(elegiveis, key=lambda e: e["delta_comum"]), min(elegiveis, key=lambda e: e["delta_comum"])) if elegiveis else ()
    for e in inspecoes:
        ev = e["evidencia"]
        out += ["", f"**Inspeção de `{e['page_id']}`:** τ de palavras Docling→ls3 = {f(R['por_metodo']['docling'][[r['page_id'] for r in R['rows']].index(e['page_id'])]['palavras']['tau'])}→{f(R['por_metodo']['ls3'][[r['page_id'] for r in R['rows']].index(e['page_id'])]['palavras']['tau'])}; sucessor muda {f(100*e['delta_sucessor'],2)} pontos percentuais."]
        for src in ("docling", "ls3"):
            dist = ev[src]["palavras_tabela_por_atomo"]
            dc = ev[src]["diag"]
            descr = "; ".join(f"{rid}: {','.join(str(n) for n in counts if n)} palavras nos átomos que a capturam" for rid, counts in dist.items()) or "sem tabelas de referência"
            runs = ev[src]["trechos_regioes"]
            primeiros = "→".join(r["id"] for r in runs[:12])
            out.append(f"- {src}: {descr}; {dc['pontes']} pontes de projeção, {dc['margem_topo']} itens no topo e {dc['margem_fim']} no fim. Início da saída real: `{primeiros}`. Fragmentação = {f(100*dc['fracao'],1)}%.")
        out.append("A distribuição por átomo mostra tanto divisões internas de uma tabela como fusões de tabelas distintas; mudanças da política de margens também surgem quando o envelope do átomo muda. Melhor continuidade pode coexistir com pior ordem global: separar tabelas paralelas evita intercalação, mas o ordenamento ainda pode trocar uma tabela de coluna.")
    out += ["", "### Variante com caixas de texto: delimita melhor?", "",
            f"No τ de palavras, caixas de texto ls3 melhoram/empatam/pioram {u['ganha']}/{u['empata']}/{u['perde']} páginas contra a projeção com os átomos ls3. A fragmentação média cai de {f(100*S['ls3']['fragmentacao']['media'],1)}% para {f(100*S['texto_ls3']['fragmentacao']['media'],1)}%, mas a ordem global média cai. Portanto, nesta variante, caixas ajudam a preservar unidades locais; não mostram vantagem global de delimitação/ordenação de colunas.",
            "", "| Página (maiores perdas de caixas texto) | τ projeção ls3 | τ caixas ls3 | Caixas texto | Palavras em caixas texto | Fallback em linhas |",
            "|---|---:|---:|---:|---:|---:|"]
    inds = sorted(range(len(ee)), key=lambda p: (R["por_metodo"]["texto_ls3"][p]["palavras"]["tau"] or 0)-(R["por_metodo"]["ls3"][p]["palavras"]["tau"] or 0))[:4]
    for p in inds:
        e, dc = ee[p], ee[p]["evidencia"]["texto_ls3"]["diag"]
        out.append(f"| `{e['page_id']}` | {f(R['por_metodo']['ls3'][p]['palavras']['tau'])} | {f(R['por_metodo']['texto_ls3'][p]['palavras']['tau'])} | {dc['caixas_texto']} | {dc['palavras_em_texto_ls3']} | {dc['fallback_palavras']} |")
    out += ["", "### Casos de detector nas páginas de maior mudança", "",
            "| Página | Classe | Docling TP/FP/FN | ls3 TP/FP/FN (conf. 0,25) |", "|---|---|---:|---:|"]
    rows = {r["page_id"]: r for r in R["rows"]}
    for e in ganhos + perdas:
        for cls in ("tabela", "imagem"):
            cells = []
            for src in ("docling", "ls3"):
                v = rows[e["page_id"]]["qualidade"][f"{src}_0.25"][cls]
                cells.append(f"{v['tp']}/{v['pred']-v['tp']}/{v['ouro']-v['tp']}")
            out.append(f"| `{e['page_id']}` | {cls} | {cells[0]} | {cells[1]} |")
    out += ["", "## Configurações escolhidas", "", "| Método | Configuração | Páginas |", "|---|---|---:|"]
    for n, ids in R["selecao"].items():
        for c, count in sorted(collections.Counter(ids).items()):
            out.append(f"| {n} | `{c}` | {count} |")
    tempos = R["tempos_detector_ms"]
    out += ["", "## Limitações, viés e recomendação", "",
            f"Amostra pequena ({A['paginas']} páginas, {A['veiculos']} veículos), escolhida para problemas de layout; não representa a frequência dos layouts no acervo. O Golden foi ordenado sobre regiões Diamond corrigidas a partir de pré-anotação: há **viés de ancoragem** em caixas/classes e na unidade que a ordem humana recebe. O detector foi treinado no parceiro; a origem humana das anotações não elimina possível ancoragem em propostas. Não inspecionamos os exports LS nem provamos ausência de duplicatas documentais entre LS e Golden; o teste é externo por projeto, mas a independência documental não está demonstrada. As heurísticas originais foram desenvolvidas olhando este Golden; LOPO/LOVO não desfazem essa circularidade.",
            "O oráculo de átomos e as regiões de referência são diagnósticos; nunca são entrada do caminho ls3. A anotação de ordem excluiu imagens sem palavras; a revocação do detector cobre essas imagens, mas a métrica de ordem não mede sua colocação. Não há estrutura interna de tabelas, OCR, texto alternativo nem validação extrínseca de RI. O colapso LS e o Diamond diferem especialmente em assinaturas manuscritas. Precisão/revocação dependem de IoU e confiança, com poucas instâncias de tabela e imagem; não equivalem a mAP ou desempenho em todo o dataset LS.",
            f"Execução CPU com {R['detector']['threads']} threads; tempo observado do detector: média {f(statistics.mean(tempos),1)} ms/página, mediana {f(statistics.median(tempos),1)} ms/página, p95 {f(float(np.quantile(tempos,.95)),1)} ms. Inclui a primeira chamada/aquecimento, exclui carregamento do modelo, e sofre concorrência com outros trabalhos; não é benchmark controlado. Não foi usada GPU.",
            "**Recomendação:** conservar as três classes como entrada viável de layout, mas congelar detector, limiares e política antes de teste novo, desenhado sem proposta e separado por veículo/documento. Decidir adoção pela ordem real, continuidade e fragmentação, com as caixas visuais incluídas na nova anotação. A revocação de imagem menor que a do Docling deve ser validada separadamente: o bom τ de palavras não avalia posicionamento das figuras vazias. A família de caixas de texto só ajuda se melhora esses critérios; não assumir que melhora colunas por detectar mais regiões. Manter Docling e XY-cut com margens como controles.",
            "", "## Reprodução e integridade", "",
            "```powershell", "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_ls3.py --do-zero",
            "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_ls3.py --conferir", "```", "",
            "O JSONL guarda uma predição por página, caixas pixels/pontos, escalas, confiança, tempos, versões e hash dos pesos. O checkpoint comprimido neste Markdown guarda grade/métricas por página, configurações, réguas e sequências reais selecionadas; a retomada não precisa executar de novo páginas concluídas. Relatório gerado desse objeto, reaberto e conferido byte a byte na parte legível. Execução com `--do-zero` descarta caches analíticos e refaz inclusive a detecção; o horário/latência podem mudar. Entradas são somente leitura, e seus SHA-256 são conferidos ao fim.",
            f"Controles sintéticos: {len(R['controles'])}, todos aprovados. Cache de detecção: {R['n_pred']} páginas. Pesos SHA-256: `{R['detector']['peso_sha256']}`."]
    return "\n".join(out) + "\n"


def conferir():
    R = carregar_md()
    if not R or not R.get("concluido"):
        raise ValueError("Relatório não está concluído")
    esperado = relatorio(R)
    atual = MD.read_text(encoding="utf-8").split(f"\n<!-- {MARCADOR}")[0]
    if atual != esperado:
        raise ValueError("Markdown diverge dos resultados do checkpoint")
    with PRED.open(encoding="utf-8") as ff:
        preds = [json.loads(l) for l in ff if l.strip()]
    if len(preds) != R["auditoria"]["paginas"] or len({p['page_id'] for p in preds}) != len(preds):
        raise ValueError("Cache de detecção com páginas duplicadas/ausentes")
    if {p["page_id"] for p in preds} != {r["page_id"] for r in R["rows"]}:
        raise ValueError("IDs do cache de detecção divergem da avaliação")
    for p in preds:
        if p["chave"] != R["chave_pred"] or p["modelo"] != R["detector"]:
            raise ValueError("Metadados do cache de detecção divergem da avaliação")
        sx, sy = p["escala_px_pt"]
        for b in p["regioes"]:
            px = b["bbox_px"]
            if not np.allclose(b["bbox"], [px[0]*sx, px[1]*sy, px[2]*sx, px[3]*sy], rtol=0, atol=1e-10):
                raise ValueError("Conversão pixels/pontos inconsistente")
    for r in R["rows"]:
        for fonte in FONTES:
            if len(r["variantes"][fonte]) != len(grade(fonte)):
                raise ValueError("Grade incompleta")
    # Conferencia numerica independente da formatacao do Markdown.
    for nome, vals in R["por_metodo"].items():
        for regua in REGUAS:
            for m in METRICAS:
                med = media([v[regua][m] for v in vals])
                esperado = R["resumo"][nome][regua][m]["media"]
                if (med is None) != (esperado is None) or (med is not None and not math.isclose(med, esperado, abs_tol=1e-12, rel_tol=0)):
                    raise ValueError(f"Media da tabela diverge das paginas: {nome}/{regua}/{m}")
    copia = {"rows": R["rows"]}
    detector_resumo(copia)
    if copia["qualidade_detector"] != R["qualidade_detector"]:
        raise ValueError("Tabela de detector diverge dos casamentos por pagina")
    if entradas(preparar()) != R["hashes"]:
        raise ValueError("Entradas atuais divergem das usadas no relatorio")
    print("[OK] Relatório bate com resultados salvos; 44 predições únicas, conversão px→pt e grade conferidas.")
    print("Veredito:", veredito(R))
    print("\n".join(tabela(R, PRINCIPAIS, "palavras")))
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    if args.conferir:
        conferir()
        return
    if args.bootstrap < 2000 or args.threads < 1:
        ap.error("bootstrap exige pelo menos 2000; threads exige valor positivo")
    qs = preparar()
    H = entradas(qs)
    R = None if args.do_zero else carregar_md()
    if not R or R.get("hashes") != H:
        R = {"hashes": H, "rows": [], "n_pred": 0}
    R["concluido"] = False
    R["controles"] = controles()
    salvar_md(R, parcial(R))
    detectar(qs, H, R, args.do_zero, args.threads)
    prontas = {r["page_id"]: r for r in R["rows"]}
    for p, q in enumerate(qs):
        pid = q["p"]["page_id"]
        if pid in prontas:
            continue
        row = {"page_id": pid, "veiculo": q["veiculo"], "colunas": q["colunas"],
               "auditoria": q["auditoria"], "bases": bases(q), "variantes": {}, "qualidade": {}}
        for fonte in FONTES:
            vv, memo = {}, {}
            for c in grade(fonte):
                # Ouro/nenhum nao dependem do score; evita recalculo redundante.
                chave = (c.abordagem, c.gap, c.vale, c.score if fonte not in ("ouro", "nenhum") else 0)
                if chave not in memo:
                    seq, _, diag = prever(q, c, fonte)
                    memo[chave] = compacto(avaliar(q, seq, diag))
                vv[c.id] = memo[chave]
            row["variantes"][fonte] = vv
        for fonte in ("docling", "ls3"):
            for score in (.25, .45):
                row["qualidade"][f"{fonte}_{score:.2f}"] = qualidade(q, fonte, score)
        prontas[pid] = row
        R["rows"] = [prontas[q2["p"]["page_id"]] for q2 in qs if q2["p"]["page_id"] in prontas]
        salvar_md(R, parcial(R))
        print(f"[Grade {p+1}/{len(qs)}] {pid}", flush=True)
    A = {"paginas": len(qs), "veiculos": len({q['veiculo'] for q in qs}),
         "palavras": sum(len(q['ws']) for q in qs), "palavras_avaliadas": sum(len(q['gt_w']) for q in qs),
         "regioes": sum(len(q['gt_r']) for q in qs), "linhas": sum(len(q['gt_l']) for q in qs),
         "sem_ouro": sum(q['auditoria']['sem_ouro'] for q in qs), "ambiguas": sum(q['auditoria']['ambiguas'] for q in qs),
         "regioes_vazias": sum(q['auditoria']['regioes_vazias'] for q in qs),
         "paginas_vazias": sum(q['auditoria']['sem_palavras'] for q in qs),
         "visuais_retiradas": sum(q['auditoria']['visuais_retiradas'] for q in qs),
         "diamond_regioes": sum(len(q['diamond_ouro']) for q in qs),
         "diamond_vazias": sum(sum(not ks for ks in o.donos(q['ws'], q['diamond_ouro'])[0]) for q in qs)}
    R["auditoria"] = A
    R["docling_cache"] = {"score_min": sorted({q["d"]["detector"].get("score_min", 0) for q in qs}),
                          "modelos": sorted({q["d"]["detector"].get("modelo", "") for q in qs}),
                          "revisoes": sorted({q["d"]["detector"].get("revisao", "") for q in qs})}
    R["bootstrap"] = {"n": args.bootstrap, "seed": args.semente}
    W, gi, grupos = pesos_cluster(qs, args.bootstrap, args.semente)
    print("[Inferência] seleção LOPO refeita por bootstrap agrupado...", flush=True)
    metodos, boots = selecionados(R, qs, W, gi)
    contrastes(R, metodos, boots, gi)
    detector_resumo(R)
    estratos(R, qs, metodos, W)
    erros(R, qs)
    if entradas(qs) != H:
        raise ValueError("Entradas/fontes/pesos mudaram durante a execução; não finalizar o relatório")
    R["concluido"] = True
    salvar_md(R, relatorio(R))
    conferir()


if __name__ == "__main__":
    main()
