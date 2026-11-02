"""Compara cinco pipelines automaticos no texto final dos Golden v4 e v3 novo.

As caixas e a ordem humanas entram apenas no avaliador. Reutiliza geometria,
preparo e caches existentes, sem chamar mains que gravam sobre esses arquivos.
Reconstrui blocos v3 automaticos nas paginas novas; ls3 faltante roda em CPU.
Persiste cada pagina e gera o relatorio dos numeros, para permitir retomada.

Uso na raiz: venv\\Scripts\\python.exe -B orquestracao\\analises\\erros_ponta_a_ponta.py
--do-zero recalcula todas as predicoes geometricas, metricas e estatisticas,
mas conserva os caches de palavras/detectores; --reinferir tambem refaz ls3 em
CPU. --conferir verifica hashes, JSON, Markdown e os resultados por pagina.
Unicas saidas: resultados/erros_ponta_a_ponta.md, .json e _cache/**.
Nao grava em data/, nao usa GPU, rede, anotacao como entrada ou selecao LOPO.
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
import collections
import hashlib
import json
import math
import os
import statistics
import types
import warnings

import numpy as np
from PIL import Image
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import ordem_sem_bbox_justo as j
from orquestracao.analises import ordem_sem_bbox_ls3 as ls
from orquestracao.analises import ordem_sem_bbox_validacao_acervo as ac
from src.data import extrator, layout
from src.eval.politica_margens import xycut_margens
from src.eval.protocolo import ordem_entrada
from src.ri import piloto_japeri as ri

BASE = RAIZ / "resultados/erros_ponta_a_ponta_cache"
JSON = RAIZ / "resultados/erros_ponta_a_ponta.json"
MD = RAIZ / "resultados/erros_ponta_a_ponta.md"
FIXA = o.Config("projecao_local_margens", 0.45, 1.2, 0.08)
SEMENTE, NBOOT, N_DESLOCAMENTO = 20261003, 5000, 3
METODOS = ("P0", "P1", "P1m", "P2", "P2d")
METRICAS = ("tau", "sucessor_linhas", "fid6", "fid12", "fid24", "quebras",
            "quebras_mil", "intercalacoes", "deslocados3", "deslocados5")
SEGMENTACAO = {"caixa_partida", "caixa_fundida", "interno_caixa"}
ORIGENS_P1 = ("caixa_partida", "caixa_fundida", "interno_caixa", "ordenacao_residual", "fora_ouro")
ORIGENS_P2 = ("atomo_interno", "atomo_fronteira", "linha_partida", "linha_interna",
              "coluna_proxy", "ordenacao_residual", "fora_ouro")


def ler(path):
    return ac.carregar(path)


def gravar(path, obj):
    """Escreve so em resultados novos, com substituicao atomica."""
    path = Path(path).resolve()
    if BASE.resolve() not in path.parents and path not in (JSON.resolve(), MD.resolve()):
        raise ValueError(f"Destino nao autorizado: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha(path):
    return ac.sha(path)


def fonte(path):
    return Path(path).relative_to(RAIZ).as_posix()


def automatico(q):
    """Contrato de entrada: apenas palavras, blocos/detector automaticos e dimensoes."""
    return {"ws": q["ws"], "h": q["h"], "d": {
        "blocos_v3": q["d"]["blocos_v3"], "detector": q["d"]["detector"]},
        "p": {k: q["p"][k] for k in ("page_id", "dimensions")}, "ls3": q["ls3"]}


def carregar_amostra():
    """Importa o preparo v4; v3 novo usa palavras/cache e segmentar sem ouro."""
    qs = j.preparar()
    for q in qs:
        q["coorte"] = "v4"
        q["imagem_path"] = RAIZ / "data/golden/golden_v4/img" / q["p"]["imagem"]
        q["origem_palavras"] = "Diamond congelado (automatico)"
    ids_v4 = {p["page_id"] for p in j.ler_jsonl(o.ENTRADAS[0])}
    root = RAIZ / "data/golden/_avaliacao/golden_v3"
    refs = {r["page_id"]: r for r in ac.ler_jsonl(root / "referencia.jsonl")
            if r.get("status") == "concluida"}
    ts = [p for p in ac.ler_jsonl(root / "tarefas.jsonl") if p["page_id"] not in ids_v4]
    dc = layout.carregar_cache(ufs={p["uf"] for p in ts})
    for p in ts:
        pid = p["page_id"]
        epath = ac.CACHE / "palavras" / (ac.chave(pid) + ".json")
        e = ler(epath)
        if not e or e.get("erro"):
            raise ValueError(f"Cache de palavras ausente/invalido: {pid}")
        if pid not in dc or dc[pid] is None:
            raise ValueError(f"Cache Docling ausente: {pid}")
        det = dc[pid]
        q, aud = ac.preparar({"p": p, "gt": refs[pid]["ordem"]}, e, det)
        if q is None:
            raise ValueError(f"Auditoria v3 falhou: {pid}: {aud}")
        ws = [{"t": w[0], "x0": w[1], "top": w[2], "x1": w[3], "bottom": w[4], "s": i}
              for i, w in enumerate(e["palavras"])]
        bs = extrator.segmentar(ws, layout.tabelas(det))
        dono = {id(w): i for i, b in enumerate(bs) for L in b["linhas"] for w in L["ws"]}
        q["ws"] = [list(w) + [dono.get(id(sw), -1)] for w, sw in zip(e["palavras"], ws)]
        q["d"] = {"blocos_v3": [{"id": f"v{i}", "bbox": [round(b[k], 1) for k in
                      ("x0", "top", "x1", "bottom")], **({"tipo": "tabela"} if b.get("tabela") else {})}
                    for i, b in enumerate(bs)], "detector": {"regioes": det}}
        folder = "golden_v1" if str(p.get("origem", "")).startswith("golden_v1") else "golden_v2"
        q.update(coorte="v3_novo", imagem_path=RAIZ / "data/golden" / folder / "img" / p["imagem"],
                 origem_palavras=fonte(epath))
        qs.append(q)
    if len(qs) != 71 or len({q["p"]["page_id"] for q in qs}) != len(qs):
        raise ValueError("Amostra nao corresponde a v4 + v3 fora de todas as tarefas v4")
    return sorted(qs, key=lambda q: (q["coorte"], q["p"]["page_id"]))


def hashes(qs):
    paths = list(o.ENTRADAS) + list(o.FONTES) + [Path(__file__), Path(j.__file__), Path(ls.__file__),
        Path(ac.__file__), Path(ri.__file__), RAIZ / "src/eval/politica_margens.py",
        RAIZ / "src/data/layout.py", RAIZ / "src/data/taxonomia_layout.py", ls.PESOS,
        RAIZ / "resultados/ordem_sem_bbox_ls3.md", ls.PRED,
        RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl",
        RAIZ / "data/golden/_avaliacao/golden_v3/referencia.jsonl"]
    paths += [q["imagem_path"] for q in qs]
    paths += [RAIZ / f"data/processed/layout/{uf}.jsonl" for uf in {q["p"]["uf"] for q in qs}]
    paths += [ac.CACHE / "palavras" / (ac.chave(q["p"]["page_id"]) + ".json")
              for q in qs if q["coorte"] == "v3_novo"]
    for n in ("erros_ponta_a_ponta_previa.md", "erros_ponta_a_ponta_previa.json"):
        if (RAIZ / "resultados" / n).exists():
            paths.append(RAIZ / "resultados" / n)
    return {fonte(p): sha(p) for p in sorted(set(paths))}


def carregar_ls3(q, H, reinferir, modelo):
    """Reusa cache auditado v4 ou infere pagina nova em CPU e persiste."""
    pid = q["p"]["page_id"]
    meta = {"peso": H[fonte(ls.PESOS)], "imagem": H[fonte(q["imagem_path"])],
            "dimensions": q["p"]["dimensions"], "imgsz": 1024, "conf": .25, "iou": .7,
            "max_det": 300, "device": "cpu"}
    fp = ac.digest(meta)
    path = BASE / "detector" / (ac.chave(pid) + ".json")
    saved = ler(path) if not reinferir else None
    if saved and saved.get("fingerprint") == fp:
        return saved["regioes"], modelo, "cache_novo"
    if q["coorte"] == "v4" and not reinferir:
        ck = ls.carregar_md()
        if ck and ck.get("detector", {}).get("peso_sha256") == meta["peso"]:
            if ck["detector"]["imagens"].get(fonte(q["imagem_path"])) != meta["imagem"]:
                raise ValueError("Imagem v4 mudou desde a inferencia ls3")
            antigo = ls.carregar_pred(ck["chave_pred"]).get(pid)
            if antigo and antigo["dimensions"] == meta["dimensions"]:
                gravar(path, {"fingerprint": fp, "meta": meta, "regioes": antigo["regioes"],
                              "origem": fonte(ls.PRED)})
                return antigo["regioes"], modelo, "cache_v4"
    if modelo is None:
        os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1", YOLO_OFFLINE="true",
                          YOLO_CONFIG_DIR=str(RAIZ), OMP_NUM_THREADS="2", MKL_NUM_THREADS="2")
        import torch
        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        from ultralytics import YOLO
        from ultralytics.utils import SETTINGS
        dict.__setitem__(SETTINGS, "sync", False)
        modelo = YOLO(str(ls.PESOS)).to("cpu")
    with Image.open(q["imagem_path"]) as im:
        wpx, hpx = im.size
    pred = modelo.predict(str(q["imagem_path"]), device="cpu", imgsz=1024, conf=.25, iou=.7,
                          max_det=300, verbose=False, save=False, save_txt=False)[0]
    if tuple(pred.orig_shape) != (hpx, wpx):
        raise ValueError("Dimensoes da imagem inconsistentes")
    sx, sy = q["p"]["dimensions"]["width"] / wpx, q["p"]["dimensions"]["height"] / hpx
    regs = []
    for b in pred.boxes:
        cls = pred.names[int(b.cls.item())]
        if cls not in ("texto", "tabela", "imagem"):
            raise ValueError(f"Peso nao e de tres classes: {cls}")
        x0, y0, x1, y1 = map(float, b.xyxy[0].tolist())
        regs.append({"id": f"d{len(regs)}", "classe": cls, "score": float(b.conf.item()),
                     "bbox": [x0 * sx, y0 * sy, x1 * sx, y1 * sy]})
    gravar(path, {"fingerprint": fp, "meta": meta, "regioes": regs, "origem": "CPU"})
    return regs, modelo, "CPU"


def prever_p1(q):
    """Propor atual e XY-cut com a entrada fixa; palavras livres vao ao final."""
    ws = q["ws"]
    rs = o.propor(ws, q["d"]["blocos_v3"], q["d"]["detector"]["regioes"], regras=True)
    kws, livres, amb = o.donos(ws, rs)
    items = [{"bbox": r["bbox"], "ks": ks, "tipo": r["classe"], "id": r["id"]}
             for r, ks in zip(rs, kws)]
    p = {"page_id": q["p"]["page_id"], "dimensions": q["p"]["dimensions"],
         "bounding_boxes": [{**r, "text": " ".join(ws[k][0] for k in ks)} for r, ks in zip(rs, kws)]}
    pure = [rs[i]["id"] for i in o.xycut(ordem_entrada(p), o.boxes(items))]
    marg = xycut_margens(p)
    by = {it["id"]: it for it in items}
    free = [{"tipo": "livre", "bbox": L["bbox"], "ks": L["ks"], "id": f"livre{i}"}
            for i, L in enumerate(o.linhas(ws, livres))]
    out = {}
    for name, order in (("P1", pure), ("P1m", marg)):
        its = [by[x] for x in order] + free
        out[name] = (o.fluxo(its, ws), its, {"caixas": len(rs), "livres": len(livres), "ambiguas": amb})
    return out


def prever_todos(q):
    """Nenhuma chave humana atravessa o contrato automatico()."""
    q = automatico(q)
    out = prever_p1(q)
    seq = sorted(range(len(q["ws"])), key=lambda k: (q["ws"][k][2], q["ws"][k][1], k))
    out["P0"] = (seq, [], {})
    out["P2"] = ls.prever(q, FIXA, "ls3")
    out["P2d"] = ls.prever(q, FIXA, "docling")
    for name, (seq, _, _) in out.items():
        if len(seq) != len(q["ws"]) or set(seq) != set(range(len(q["ws"]))):
            raise ValueError(f"{name} perdeu/repetiu palavras")
    return out


def funcao_preservada(limiar):
    """Reusa literalmente preservada() em namespace com limiar isolado."""
    return types.FunctionType(ri.preservada.__code__, {**ri.preservada.__globals__, "MIN_ALINHADAS": limiar},
                              argdefs=ri.preservada.__defaults__)


def fidelidade(seq, gt, ws):
    """Texto normalizado pelo piloto, janelas integrais e controle tolerante 10/12."""
    ouro = ri.tokens(" ".join(ws[k][0] for k in gt))
    saida = ri.tokens(" ".join(ws[k][0] for k in seq))
    pos = ri.indice_posicoes(saida)
    res = {"tokens_ouro": len(ouro), "tokens_saida": len(saida)}
    for tam in (6, 12, 24):
        preservar = funcao_preservada(tam)
        intactas = 0
        for ini in range(max(0, len(ouro) - tam + 1)):
            frase = ouro[ini:ini + tam]
            # Toda coincidencia integral precisa alinhar o token mais raro.
            # Reduz candidatos, preservando a semantica da funcao do piloto.
            raro = min(range(tam), key=lambda k: len(pos.get(frase[k], ())))
            offsets = {i - raro for i in pos.get(frase[raro], ()) if 0 <= i - raro <= len(saida) - tam}
            restrito = {t: set() for t in set(frase)}
            for off in offsets:
                for k, t in enumerate(frase):
                    if saida[off+k] == t:
                        restrito[t].add(off+k)
            intactas += preservar(frase, saida, restrito)
        den = max(0, len(ouro) - tam + 1)
        res[f"fid{tam}"] = intactas / den if den else None
        res[f"janelas{tam}"] = den
        res[f"intactas{tam}"] = intactas
        # Conferencia independente: n-gramas lexicais, sem IDs ou tolerancia.
        janelas = {tuple(saida[i:i + tam]) for i in range(max(0, len(saida) - tam + 1))}
        esperado = sum(tuple(ouro[i:i + tam]) in janelas for i in range(den))
        if esperado != intactas:
            raise AssertionError("preservada() divergiu da janela integral")
    den = max(0, len(ouro) - 11)
    res["fid12_piloto_10de12"] = sum(ri.preservada(ouro[i:i + 12], saida, pos) for i in range(den)) / den if den else None
    return res


def eventos(seq, gt):
    """Quebra na transicao comparavel, incluindo palavras livres interpostas."""
    prox = dict(zip(gt, gt[1:]))
    ranks = {k: i for i, k in enumerate(seq)}
    gset, grank = set(gt), {k: i for i, k in enumerate(gt)}
    pw = [k for k in seq if k in gset]
    ev = []
    for a, b in zip(pw, pw[1:]):
        livre = ranks[b] != ranks[a] + 1
        if prox.get(a) != b or livre:
            ev.append({"a": a, "b": b, "esperado": prox.get(a), "livre": livre,
                       "pos_saida": ranks[a], "salto_ouro": grank[b] - grank[a]})
    return ev


def origem(ev, q, itens, metodo, previa=False):
    """Associacao operacional; nao transforma proximidade em prova causal."""
    reg = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
    lin = {k: L["id"] for L in q["gold_lines"] for k in L["ks"]}
    it = {k: i for i, item in enumerate(itens) for k in item["ks"]}
    conta, detalhes = collections.Counter(), []
    for e in ev:
        a, b, c = e["a"], e["b"], e["esperado"]
        ia, ib, ic = it.get(a), it.get(b), it.get(c)
        if e["livre"]:
            cat = "fora_ouro"
        elif metodo in ("P1", "P1m"):
            if previa and c is not None and reg[a] == reg[c] and ia != ic:
                cat = "caixa_partida"
            elif ia == ib and reg[a] != reg[b]:
                cat = "caixa_fundida"
            elif ia == ib:
                cat = "interno_caixa"
            elif not previa and reg[a] == reg[b]:
                cat = "caixa_partida"
            else:
                cat = "ordenacao_residual"
        else:
            atom = lambda i: i is not None and itens[i]["tipo"] in ("table", "picture")
            if ia == ib and atom(ia):
                cat = "atomo_interno"
            elif any(atom(i) for i in (ia, ib, ic)):
                cat = "atomo_fronteira"
            elif lin[a] == lin[b] and ia != ib:
                cat = "linha_partida"
            elif ia == ib:
                cat = "linha_interna"
            elif (c is not None and reg[a] == reg[c]
                  and abs(o.centro(q["ws"][a])[0] - o.centro(q["ws"][b])[0]) > max(4*q["h"], .10*q["p"]["dimensions"]["width"])
                  and abs(o.centro(q["ws"][a])[0] - o.centro(q["ws"][c])[0]) <= max(4*q["h"], .10*q["p"]["dimensions"]["width"])):
                cat = "coluna_proxy"
            else:
                cat = "ordenacao_residual"
        conta[cat] += 1
        detalhes.append({**e, "categoria": cat, "reg_a": reg[a], "reg_b": reg[b],
                         "item_a": ia, "item_b": ib})
    return dict(conta), detalhes


def medir(q, seq, itens, diag, metodo):
    gt = q["gt_w"]
    cobertos = set(gt)
    pw = [k for k in seq if k in cobertos]
    ev = eventos(seq, gt)
    ranks = {k: i for i, k in enumerate(seq)}
    linhas = {L["id"]: L["ks"] for L in q["gold_lines"]}
    intacta = {lid: all(ranks[b] == ranks[a] + 1 for a, b in zip(ks, ks[1:])) for lid, ks in linhas.items()}
    acertos = sum(intacta[a] and intacta[b] and ranks[linhas[b][0]] == ranks[linhas[a][-1]] + 1
                  for a, b in zip(q["gt_l"], q["gt_l"][1:]))
    dono = {k: r for r, ks in q["reg_words"].items() for k in ks}
    runs = ac.trechos(pw, dono)
    cont = collections.Counter(runs)
    ordem_primeira = list(dict.fromkeys(runs))
    gold_r = [r for r in q["gt_r"] if q["reg_words"][r]]
    grank = {r: i for i, r in enumerate(gold_r)}
    des = [abs(i - grank[r]) for i, r in enumerate(ordem_primeira)]
    res = {"tau": o.kendall_tau(pw, gt), "quebras": len(ev),
           "quebras_mil": len(ev) * 1000 / len(gt), "intercalacoes": sum(n-1 for n in cont.values()),
           "regioes_intercaladas": sum(n > 1 for n in cont.values()),
           "deslocados3": sum(d > N_DESLOCAMENTO for d in des), "deslocados5": sum(d > 5 for d in des),
           "sucessor_linhas": acertos / (len(q["gt_l"])-1) if len(q["gt_l"]) > 1 else None,
           "linhas_intactas": sum(intacta.values()), "linhas": len(linhas),
           "quebras_sem_livres": sum(not e["livre"] for e in ev),
           "quebras_projecao": len(eventos(pw, gt)), "diag": diag, "seq": seq, "items": itens,
           **fidelidade(seq, gt, q["ws"])}
    if metodo != "P0":
        res["origens"], res["eventos"] = origem(ev, q, itens, metodo)
        # Todos os pares internos ao mesmo item sobrevivem a qualquer reordenacao
        # dos itens atomicos. E um piso verificavel, nao uma escolha pelo ouro.
        res["piso_interno"] = sum(e["item_a"] == e["item_b"] and not e["livre"] for e in res["eventos"])
        if metodo in ("P1", "P1m"):
            res["origens_regra_previa"], _ = origem(eventos(pw, gt), q, itens, metodo, previa=True)
    return res


def pesos_cluster(rows):
    grupos = sorted({r["uf"] for r in rows})
    gi = np.array([grupos.index(r["uf"]) for r in rows])
    rng = np.random.default_rng(SEMENTE)
    amostra = rng.integers(0, len(grupos), (NBOOT, len(grupos)))
    count = np.zeros((NBOOT, len(grupos)), dtype=int)
    for i, draw in enumerate(amostra):
        count[i] = np.bincount(draw, minlength=len(grupos))
    return count[:, gi].astype(float)


def media_ic(v, W):
    vals = np.array([np.nan if x is None else x for x in v], dtype=float)
    mask = np.isfinite(vals)
    if not mask.any():
        return {"media": None, "ic": [None, None], "n": 0}
    den = W[:, mask].sum(axis=1)
    b = W[:, mask] @ vals[mask] / np.where(den == 0, np.nan, den)
    b = b[np.isfinite(b)]
    return {"media": float(vals[mask].mean()), "ic": np.percentile(b, [2.5, 97.5]).tolist(), "n": int(mask.sum())}


def pratt(v):
    arr = np.round(np.asarray(v, dtype=float), 12)
    if not len(arr) or np.all(arr == 0):
        return {"W": 0., "p": 1.}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t = wilcoxon(arr, zero_method="pratt", alternative="two-sided", method="approx")
    return {"W": float(t.statistic), "p": float(t.pvalue)}


def resumir(rows):
    W = pesos_cluster(rows)
    out = {"n": len(rows), "veiculos": len({r["uf"] for r in rows}), "metodos": {}, "testes": {}}
    for m in METODOS:
        met = {k: media_ic([r["metodos"][m][k] for r in rows], W) for k in METRICAS}
        for k in ("quebras", "intercalacoes", "deslocados3", "deslocados5"):
            met[k]["total"] = sum(r["metodos"][m][k] for r in rows)
        origem_total = collections.Counter()
        anterior = collections.Counter()
        for r in rows:
            origem_total.update(r["metodos"][m].get("origens", {}))
            anterior.update(r["metodos"][m].get("origens_regra_previa", {}))
        met.update(origens=dict(origem_total), origens_regra_previa=dict(anterior))
        if m != "P0":
            met["piso_interno"] = sum(r["metodos"][m]["piso_interno"] for r in rows)
        met["fracao_caixas"] = sum(origem_total[k] for k in SEGMENTACAO) / met["quebras"]["total"] if met["quebras"]["total"] else 0
        if m in ("P1", "P1m"):
            numer = [sum(r["metodos"][m]["origens"].get(k, 0) for k in SEGMENTACAO) for r in rows]
            denom = [r["metodos"][m]["quebras"] for r in rows]
            n, d = W @ np.array(numer), W @ np.array(denom)
            vals = n[d > 0] / d[d > 0]
            met["fracao_caixas_ic"] = np.percentile(vals, [2.5, 97.5]).tolist()
        out["metodos"][m] = met
    for base in ("P1", "P1m"):
        for k in METRICAS:
            inds = [i for i, r in enumerate(rows) if r["metodos"]["P2"][k] is not None and r["metodos"][base][k] is not None]
            d = [rows[i]["metodos"]["P2"][k] - rows[i]["metodos"][base][k] for i in inds]
            group_d = [statistics.mean(d[z] for z, i in enumerate(inds) if rows[i]["uf"] == uf)
                       for uf in sorted({rows[i]["uf"] for i in inds})]
            sentido = -1 if k in ("quebras", "quebras_mil", "intercalacoes", "deslocados3", "deslocados5") else 1
            t = {**media_ic(d, W[:, inds]), "pagina": pratt(d), "veiculo": pratt(group_d),
                 "ganha": sum(x*sentido > 1e-12 for x in d), "empata": sum(abs(x) <= 1e-12 for x in d),
                 "perde": sum(x*sentido < -1e-12 for x in d)}
            out["testes"][f"P2-{base}/{k}"] = t
    # Holm por coorte, cobrindo todos os contrastes/metrica em ambas as unidades.
    for unidade in ("pagina", "veiculo"):
        pares = sorted((t[unidade]["p"], chave) for chave, t in out["testes"].items())
        anterior = 0.
        for i, (p, chave) in enumerate(pares):
            anterior = max(anterior, min(1., p * (len(pares)-i)))
            out["testes"][chave][unidade]["holm"] = anterior
    return out


def auditar_previa(qs):
    """Reconta com codigo independente, sem executar o script da previa."""
    path = RAIZ / "resultados/erros_ponta_a_ponta_previa.json"
    if not path.exists():
        return {"existe": False}
    antigo = ler(path)
    pp = {r["page_id"]: r for r in antigo["por_pagina"]}
    rows, checagens, divergencias = [], [], []
    verificacoes_pagina = 0
    for q in qs:
        if q["coorte"] != "v4":
            continue
        aq = automatico(q)
        rs = o.propor(aq["ws"], aq["d"]["blocos_v3"], aq["d"]["detector"]["regioes"], regras=True)
        kws, livres, _ = o.donos(q["ws"], rs)
        its = [{"bbox": r["bbox"], "ks": ks, "tipo": r["classe"]} for r, ks in zip(rs, kws)]
        ms = {}
        for m, pol in (("P1", None), ("P1m", "geo")):
            ini, corpo, marcas, fim = j.particao(its, q["ws"], q["p"]["dimensions"]["height"], pol)
            key = lambda i: (its[i]["bbox"][1], its[i]["bbox"][0], i)
            order = sorted(ini, key=key) + o.xycut(corpo, o.boxes(its)) + sorted(marcas, key=key) + sorted(fim, key=key)
            free = [{"tipo": "livre", "bbox": L["bbox"], "ks": L["ks"]} for L in o.linhas(q["ws"], livres)]
            ordered = [its[i] for i in order] + free
            ms[m] = (o.fluxo(ordered, q["ws"]), ordered)
        seq, items, _ = o.prever(aq, FIXA)
        ms["P2"] = (seq, items)
        registro = {"page_id": q["p"]["page_id"], "metodos": {}}
        for m, (seq, items) in ms.items():
            gtset = set(q["gt_w"])
            pw = [k for k in seq if k in gtset]
            ev = eventos(pw, q["gt_w"])
            if m != "P2":
                ori = origem(ev, q, items, m, previa=True)[0]
            else:
                reg = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
                atoms = {k for item in items if item["tipo"] in ("table", "picture") for k in item["ks"]}
                c = collections.Counter()
                for e in ev:
                    if any(w in atoms for w in (e["a"], e["b"], e["esperado"])):
                        c["bloco_atomico"] += 1
                    elif reg[e["a"]] == reg[e["b"]]:
                        c["mesma_regiao_ouro"] += 1
                    else:
                        c["entre_regioes_ouro"] += 1
                ori = dict(c)
            fid = {}
            for k in (6, 12, 24):
                janela = {tuple(pw[i:i+k]) for i in range(len(pw)-k+1)}
                den = max(0, len(q["gt_w"])-k+1)
                fid[f"fid{k}"] = sum(tuple(q["gt_w"][i:i+k]) in janela for i in range(den)) / den if den else 1.
            registro["metodos"][m] = {"tau": o.kendall_tau(pw, q["gt_w"]), "quebras": len(ev),
                                      "quebras_mil": len(ev)*1000/len(pw), "origens": ori, **fid}
            old = pp[q["p"]["page_id"]][m]
            pares = [("tau", registro["metodos"][m]["tau"], old["tau"]),
                     ("quebras", len(ev), old["quebras"]),
                     ("quebras_mil", registro["metodos"][m]["quebras_mil"], old["quebras_por_mil"])]
            pares += [(f"fid{k}", fid[f"fid{k}"], old["fidelidade"][str(k)]) for k in (6,12,24)]
            equivalencias = {"interno_caixa": "ordem_dentro_caixa", "ordenacao_residual": "ordem_entre_caixas"}
            for cat in old["origens"]:
                atual = next((k for k, v in equivalencias.items() if v == cat), cat)
                pares.append((cat, ori.get(atual,0), old["origens"][cat]))
            for k, v, esperado in pares:
                verificacoes_pagina += 1
                if abs(v-esperado) > 1e-10:
                    divergencias.append({"page_id": q["p"]["page_id"], "metodo": m,
                                         "metrica": k, "salvo": esperado, "recalculado": v})
        rows.append(registro)
    for m in ("P1", "P1m", "P2"):
        agg = antigo["agregados"][m]
        medido = {"total_quebras": sum(r["metodos"][m]["quebras"] for r in rows),
                  "tau_media": statistics.mean(r["metodos"][m]["tau"] for r in rows),
                  **{f"fid{k}_media": statistics.mean(r["metodos"][m][f"fid{k}"] for r in rows) for k in (6,12,24)}}
        for k, v in medido.items():
            checagens.append({"metodo": m, "metrica": k, "salvo": agg[k], "recalculado": v,
                              "confere": abs(v-agg[k]) < 1e-10})
    diff = [r["metodos"]["P2"]["quebras"]-r["metodos"]["P1m"]["quebras"] for r in rows]
    diff_mil = [r["metodos"]["P2"]["quebras_mil"]-r["metodos"]["P1m"]["quebras_mil"] for r in rows]
    origem_total = {m: dict(sum((collections.Counter(r["metodos"][m]["origens"]) for r in rows), collections.Counter()))
                    for m in ("P1", "P1m")}
    return {"existe": True, "checagens": checagens, "delta_quebras": statistics.mean(diff),
            "delta_quebras_mil": statistics.mean(diff_mil), "teste_mil": pratt(diff_mil),
            "origens": origem_total, "rows": rows, "verificacoes_pagina": verificacoes_pagina,
            "divergencias_pagina": divergencias}


def f(x, n=2):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def pct(x):
    return f(100*x, 1) + "%"


def cel(x, percent=False, n=2):
    fmt = (lambda v: pct(v)) if percent else (lambda v: f(v, n))
    return f"{fmt(x['media'])} [{fmt(x['ic'][0])}; {fmt(x['ic'][1])}]" if x["media"] is not None else "—"


def tabela(s):
    lines = ["| Pipeline | τ palavras ↑ | Sucessor de linhas ↑ | Quebras: total / página ↓ | Fid. 6 ↑ | Fid. 12 ↑ | Fid. 24 ↑ |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for m in METODOS:
        a = s["metodos"][m]
        lines.append(f"| {m} | {cel(a['tau'], n=3)} | {cel(a['sucessor_linhas'], True)} | {a['quebras']['total']} / {cel(a['quebras'])} | {cel(a['fid6'], True)} | {cel(a['fid12'], True)} | {cel(a['fid24'], True)} |")
    return lines


def relatorio(R):
    s = R["resumos"]["todas"]
    p1, p1m, p2 = (s["metodos"][k] for k in ("P1", "P1m", "P2"))
    t1, tm = (s["testes"][f"P2-{b}/quebras"] for b in ("P1", "P1m"))
    reduce1 = -t1["media"]/p1["quebras"]["media"]
    reducem = -tm["media"]/p1m["quebras"]["media"]
    maioria = p1["fracao_caixas"] > .5
    verdict = "A hipótese de que a maioria das quebras nasce nas caixas recebe apoio nesta régua." if maioria else "A hipótese de que a maioria das quebras nasce nas caixas não é sustentada nesta régua."
    R["veredito"] = verdict
    lines = ["# Erros de ponta a ponta: automático contra automático", "", "## Resumo em cinco linhas", "",
        f"1. P1: {pct(p1['fracao_caixas'])} das quebras são associadas às caixas pela regra operacional [IC 95% {pct(p1['fracao_caixas_ic'][0])}; {pct(p1['fracao_caixas_ic'][1])}]; P1m: {pct(p1m['fracao_caixas'])}. {verdict}",
        "2. Quebras por página: " + "; ".join(f"{m} = {f(s['metodos'][m]['quebras']['media'])}" for m in METODOS) + ".",
        f"3. P2 reduz a média observada de quebras contra P1 em {pct(reduce1)} (Δ={cel(t1)} por página) e contra P1m em {pct(reducem)} (Δ={cel(tm)}); o IC contra P1m inclui ausência de melhora.",
        f"4. Fidelidade integral de 12 palavras: P1 {pct(p1['fid12']['media'])}; P1m {pct(p1m['fid12']['media'])}; P2 {pct(p2['fid12']['media'])}; Pratt por veículo P2−P1m, quebras: p={f(tm['veiculo']['p'],6)}.",
        f"5. São {s['n']} páginas de {s['veiculos']} veículos; analisar v4 e v3 novo separadamente. A comparação mede reordenação do texto digital disponível, com referência interna derivada e viés de ancoragem.", "",
        "## Protocolo e entradas", "",
        "P0: palavras ordenadas por (top, x0, índice), sem detector. P1: `propor(regras=True)` atual, com palavras e blocos v3 automáticos, cache automático Docling e XY-cut. P1m: as mesmas caixas, com `src/eval/politica_margens.py:xycut_margens`, variante geométrica recomendada (recorte do corpo). P2: somente átomos tabela/imagem do ls3; caixas texto do detector são ignoradas. P2d: mesmo algoritmo, átomos Docling. Nenhum pipeline recebe caixas, classes ou ordem humanas: `automatico()` limita expressamente o contrato de entrada.", "",
        f"Configuração única congelada, sem seleção nesta execução: `{FIXA.id}`; é a escolhida pelo ls3 em todas as páginas da análise anterior. Docling usa exatamente esses parâmetros, sem escolher a exceção LOPO anterior. Detector ls3: best.pt, CPU, imgsz=1024, conf=0,25, IoU NMS=0,7, max_det=300; átomos retidos com confiança ≥ {f(FIXA.score)}. Topo: centro < 7% e base < 10%; rodapé: centro > 95%; saída topo→corpo→marcas→rodapé. Peso SHA-256: `{R['hashes'][fonte(ls.PESOS)]}`.", "",
        "V4 reutiliza palavras, associação aos blocos v3 e detector **anteriores à correção humana**, congelados nas tarefas Diamond; `propor` é executado agora. V3 novo reutiliza palavras extraídas do PDF pelo script de validação do acervo e reconstrói `segmentar()` com tabelas Docling; não reaproveita regiões de referência como entrada. Imagens dos lotes originais servem ao ls3. As dimensões são auditadas; não há OCR, rede ou abertura de exports Label Studio. As palavras fora das regiões-ouro permanecem na saída. Ouro: ordem humana cega de regiões, com `linhas()` dentro de cada região. A palavra tem identidade por índice de extração, evitando casamento por conteúdo repetido para τ.", "",
        f"Amostra solicitada: {R['resumos']['v4']['n']} páginas concluídas do v4 e {R['resumos']['v3_novo']['n']} do v3 fora de **todas** as tarefas v4 (incluindo a pulada). Total de palavras disponíveis={sum(r['palavras'] for r in R['paginas'])}; com referência={sum(r['palavras_ouro'] for r in R['paginas'])}; sem referência={sum(r['palavras']-r['palavras_ouro'] for r in R['paginas'])}. Não há exclusões nesta execução.", "",
        "## Definições operacionais no texto final", "",
        "- **τ de palavras:** permutação dos IDs com referência na sequência efetivamente emitida; palavras sem referência não têm posto-ouro. Não há projeção por mediana.",
        "- **Sucessor correto de linhas:** fração dos pares de linhas consecutivas do ouro que aparecem intactos e diretamente adjacentes na saída completa. Ambas as linhas precisam preservar todos os IDs em ordem. Uma linha intercalada não recebe crédito pelo seu posto mediano.",
        "- **Fidelidade integral 6/12/24:** todas as janelas consecutivas dos tokens-ouro, incluindo fronteiras de linhas e regiões, procuradas no texto final normalizado por `piloto_japeri.tokens`. Reutiliza literalmente `preservada()` com `MIN_ALINHADAS=k` em namespace isolado; exige k/k, sem mudar o módulo. Confere cada contagem por conjuntos de n-gramas. Também guarda o controle original tolerante 10/12 do piloto. Repetições lexicais podem preservar uma frase em outra posição: esse é o comportamento de busca textual solicitado, distinto da régua de IDs da prévia. Não são necessariamente frases sintáticas.",
        "- **Quebra de continuidade:** transição entre palavras sucessivas com referência na saída que não é o sucessor-ouro, ou cujo espaço foi interrompido por palavras sem referência. Cada transição conta uma vez; um salto de coluna não vira centenas de inversões. Não conta início/fim nem inventa ordem para palavras não anotadas. A contagem projetada sem livres também fica no JSON para conferir a prévia.",
        "- **Trecho intercalado:** retorno a uma região-ouro já visitada depois de outra região (A→B→A): cada retorno conta um evento; uma região com três visitas conta dois. Não confunde bloco inteiro fora de ordem com intercalação. O JSON guarda também quantas regiões foram afetadas.",
        f"- **Bloco deslocado:** região-ouro com texto cujo posto de **primeira aparição** na saída difere em mais de N={N_DESLOCAMENTO} postos do ouro. Não usa caixas humanas para prever, nem mediana para apagar intercalamento. Sensibilidade com N=5 também é reportada. É uma régua adicional, com efeito cascata de posições; não soma com quebras/intercalações para formar um total arbitrário.", "",
        "## Tabela principal: todas as páginas", ""] + tabela(s)
    for coorte, label in (("v4", "V4 — desenvolvimento"), ("v3_novo", "V3 fora do V4 — páginas adicionais")):
        lines += ["", f"### {label}", "", f"n={R['resumos'][coorte]['n']}; veículos={R['resumos'][coorte]['veiculos']}.", ""] + tabela(R["resumos"][coorte])
    lines += ["", "## Contagens adicionais: total / média por página [IC 95%]", "",
              "| Pipeline | Intercalações | Deslocados >3 | Deslocados >5 | Quebras/1.000 palavras |",
              "|---|---:|---:|---:|---:|"]
    for m in METODOS:
        a = s["metodos"][m]
        lines.append(f"| {m} | {a['intercalacoes']['total']} / {cel(a['intercalacoes'])} | {a['deslocados3']['total']} / {cel(a['deslocados3'])} | {a['deslocados5']['total']} / {cel(a['deslocados5'])} | {cel(a['quebras_mil'])} |")
    lines += ["", "## Origem das quebras: associação e piso irredutível", "",
        "P1/P1m: nas **duas palavras da transição errada emitida**, mesma região-ouro e caixas distintas → caixa partida; regiões distintas e mesma caixa → caixa fundida; mesma caixa/mesma região → erro interno da caixa. Restante → ordenação residual. Esta regra implementa os dois casos geométricos pedidos, mas a categoria residual **não certifica** que as caixas estejam corretas. Uma região partida ainda pode ser ordenada corretamente; sua quebra pode ter causas conjuntas. Não se estima erro de classe isolado porque não há ouro de classes independente em ambas as coortes. A fração associada não é estimativa causal identificada.", "",
        "P2/P2d: mesma unidade atômica → átomo interno; fronteira envolvendo átomo atual ou esperado → átomo associado à fronteira; mesma linha-ouro em itens texto distintos → linha partida; mesmo item texto → erro interno de linha; salto horizontal maior que max(4 alturas de letra, 10% da largura), quando o sucessor esperado fica perto → proxy de coluna errada; restante → ordenação residual. **Envolver átomo não prova detecção errada**, e o proxy de coluna não é inspeção humana. As categorias são mutuamente exclusivas, na precedência declarada; palavras livres interpostas recebem categoria própria.", "",
        "| Origem | P1 | P1m | P2 | P2d |", "|---|---:|---:|---:|---:|"]
    for cat in tuple(dict.fromkeys(ORIGENS_P1 + ORIGENS_P2)):
        lines.append("| " + cat + " | " + " | ".join(str(s["metodos"][m]["origens"].get(cat, 0)) for m in ("P1","P1m","P2","P2d")) + " |")
    lines += ["", "| Coorte | Caixas associadas P1 | Caixas associadas P1m |", "|---|---:|---:|"]
    for c in ("v4", "v3_novo", "todas"):
        cs = R["resumos"][c]["metodos"]
        lines.append(f"| {c} | {pct(cs['P1']['fracao_caixas'])} | {pct(cs['P1m']['fracao_caixas'])} |")
    lines += ["", "**Piso verificável de erro interno:** reordenar itens inteiros jamais corrige um par errado já emitido dentro do mesmo item (caixa/linha/átomo). Não exige reordenação com ouro nem intervenção em produção. Total / fração das quebras: " + "; ".join(f"{m}: {s['metodos'][m]['piso_interno']} / {pct(s['metodos'][m]['piso_interno']/s['metodos'][m]['quebras']['total'])}" for m in ("P1","P1m","P2","P2d")) + ". Este piso fornece evidência mais forte de erro herdado do que uma mera associação nas fronteiras."]
    lines += ["", "## Inferência pareada", "",
        f"IC percentil de 95%, {NBOOT} bootstrap agrupados por veículo, semente {SEMENTE}: sorteia veículos com reposição e conserva suas páginas; estatística é média macro por página, mantendo os mesmos pesos nos contrastes. Não sorteia palavras como observações independentes. Não refaz treino ou desenvolvimento histórico. Pratt bilateral (`zero_method='pratt'`, aproximação normal, diferenças arredondadas a 12 casas) tanto por página quanto nas médias de veículo. O teste por veículo evita tratar páginas irmãs como independentes; Holm cobre os contrastes/métricas da tabela em cada coorte e unidade. P-valores são exploratórios.", "",
        "| Coorte | P2−base | Métrica | Δ [IC por veículo] | G/E/P | p página | p veículo | Holm veículo |", "|---|---|---|---:|---:|---:|---:|---:|"]
    for coorte in ("todas", "v4", "v3_novo"):
        for base in ("P1", "P1m"):
            for k in METRICAS:
                t = R["resumos"][coorte]["testes"][f"P2-{base}/{k}"]
                lines.append(f"| {coorte} | {base} | {k} | {cel(t, percent=k.startswith('fid') or k=='sucessor_linhas', n=3)} | {t['ganha']}/{t['empata']}/{t['perde']} | {f(t['pagina']['p'],6)} | {f(t['veiculo']['p'],6)} | {f(t['veiculo']['holm'],6)} |")
    lines += ["", "## Conferência independente da prévia", ""]
    a = R["previa"]
    if a["existe"]:
        lines += ["A prévia chamou de P2 o método **Docling**, que aqui é P2d. Reproduzimos sua regra de entrada (sem embaralhamento), filtragem de palavras livres, atribuição de caixa partida usando o **sucessor esperado** e fidelidade por IDs, com código novo. Assim se distingue mudança de definição de erro de contagem.", "",
            "| Pipeline da prévia | Métrica | Valor salvo | Recalculado | Confere |", "|---|---|---:|---:|---|"]
        for ch in a["checagens"]:
            lines.append(f"| {ch['metodo']} | {ch['metrica']} | {f(ch['salvo'],8)} | {f(ch['recalculado'],8)} | {'sim' if ch['confere'] else 'NÃO'} |")
        lines += ["", f"Conferência por página, incluindo origens de P2d: {a['verificacoes_pagina']} comparações; {len(a['divergencias_pagina'])} divergências. Detalhes completos no JSON.",
            "Origens reproduzidas (partida/fundida/interno/residual): " + "; ".join(m + " = " + "/".join(str(a["origens"][m].get(k,0)) for k in ORIGENS_P1[:4]) for m in ("P1","P1m")) + ".",
            f"**Não confere a interpretação da prévia:** P2d−P1m = **{f(a['delta_quebras'])} quebras/página**, e {f(a['delta_quebras_mil'])} quebras/1.000 palavras (Pratt p={f(a['teste_mil']['p'],6)}): o sinal reportado como redução era aumento. A própria fração minoritária de erros de caixa contradizia a conclusão de 'esmagadora maioria'. p maior que 0,05 não demonstra ganho; p menor que 0,05 não informa direção sem o sinal. A prévia não mediu ls3, v3 novo, intercalações, deslocamentos, sucessor real de linhas, IC por veículo nem fidelidade lexical com a função do piloto. Essas extensões estão presentes aqui."]
    else:
        lines += ["Não havia prévia para conferir."]
    lines += ["", "## Exemplos de página e regressões", "",
        "Selecionados automaticamente pelos maiores ganhos e perdas absolutos de P2 contra P1m; não ajustam parâmetros.", "",
        "| Página | Coorte | Quebras P1 / P1m / P2 / P2d | Δ P2−P1m | Fid12 P1m→P2 | Intercalações P1m→P2 |", "|---|---|---:|---:|---:|---:|"]
    ordenadas = sorted(R["paginas"], key=lambda r: r["metodos"]["P2"]["quebras"]-r["metodos"]["P1m"]["quebras"])
    exemplos = list({r["page_id"]: r for r in ordenadas[:4]+ordenadas[-4:][::-1]}.values())
    for r in exemplos:
        ms = r["metodos"]
        lines.append(f"| `{r['page_id']}` | {r['coorte']} | " + "/".join(str(ms[m]["quebras"]) for m in ("P1","P1m","P2","P2d")) + f" | {ms['P2']['quebras']-ms['P1m']['quebras']} | {pct(ms['P1m']['fid12'])}→{pct(ms['P2']['fid12'])} | {ms['P1m']['intercalacoes']}→{ms['P2']['intercalacoes']} |")
    lines += ["", "Transições concretas para inspeção (primeira quebra de P2; textos vêm das palavras extraídas, não de explicação inventada):", ""]
    for r in exemplos:
        if r["exemplos"]:
            e = r["exemplos"][0]
            lines.append(f"- `{r['page_id']}`: saída «{e['a']}»→«{e['b']}»; esperado «{e['esperado']}»; categoria `{e['categoria']}`, salto-ouro={e['salto_ouro']} palavras.")
    lines += ["", "## Limitações e recomendação", "",
        "Amostra pequena e de conveniência; v4 participou do desenvolvimento do método e as páginas novas do v3 continuam em veículos majoritariamente conhecidos. A ordem humana é cega às ordens automáticas, mas as regiões do Diamond foram anotadas **corrigindo pré-anotação**, com viés de ancoragem. No v3, a ordem humana está sobre blocos do extrator ou sua projeção: ele não é um ouro independente de segmentação e pode subestimar exatamente os erros de caixas investigados. Não juntar coortes apaga essa diferença. Há ouro de ordem de regiões, não de transcrição nem ordem palavra a palavra; `linhas()` também é usado no interior do ouro e dos itens previstos, favorecendo convenções comuns. Tabelas podem ter ordem interna ambígua; não demonstramos correção de célula sem anotação independente.", "",
        "Pipelines preservam o mesmo saco de palavras digitais; portanto não medem palavras ausentes, OCR, transcrição, bytes mal codificados ou erros sem efeito na sequência. Uma classe errada só é detectável aqui quando muda o texto final. P1 usa a proposta atual por regras, não um detector visual novo de caixas finas. Imagens v3/v4 têm resoluções originais diferentes, com redimensionamento comum do ls3; o cache Docling traz seu próprio piso de confiança. Medidas de fidelidade são macro: páginas curtas pesam igual às longas; taxas por 1.000 palavras e totais ajudam a interpretar. Identificar uma quebra com caixa partida não prova que dispensar caixas resolve essa quebra. Fronteiras envolvendo átomos e proxy de coluna são diagnósticos auditáveis, não categorias causais humanas.", "",
        verdict + f" O efeito observado de P2 deve ser descrito com seus dois controles: redução relativa contra P1={pct(reduce1)}, contra P1m={pct(reducem)}, IC do segundo contraste={cel(tm)}. Contra P1m, P2 reduz quebras em {tm['ganha']} páginas, empata em {tm['empata']} e aumenta em {tm['perde']}: o ganho médio se concentra em algumas correções grandes, não em melhora uniforme. Recomenda-se manter P1m como controle obrigatório e validar os casos de regressão em ouro de palavras/linhas desenhado independentemente. Não adotar a ideia com a justificativa de 'maioria causada pelas caixas' sem esse ouro. Ganho em τ não autoriza concluir menor número de quebras; equivalência não é demonstrada por ausência de significância.", "",
        "## Reprodutibilidade", "",
        "Executar na raiz:", "", "```powershell",
        "venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py",
        "venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py --do-zero",
        "venv/Scripts/python.exe -B orquestracao/analises/erros_ponta_a_ponta.py --conferir", "```", "",
        "`--do-zero` descarta o cache de resultados da avaliação, recalcula segmentação/propostas/ordens/métricas/bootstrap e compara os números com a execução anterior. Reusa apenas palavras/imagens/detecções automáticas congeladas; `--reinferir` opcional também refaz ls3 em CPU. Isso separa execução do zero da avaliação de reextração/modelo. JSON guarda hashes de entradas, configurações, resultados completos, sequências de IDs, itens e eventos por página; caches ficam exclusivamente sob `resultados/erros_ponta_a_ponta_cache/`. `--conferir` confere o Markdown regenerado byte a byte, resumos recalculados dos resultados por página e os hashes; nenhum arquivo existente de outro experimento é modificado.", "",
        "Conferência da reexecução: " + R.get("conferencia_do_zero", "pendente nesta execução") + ".", ""]
    return "\n".join(lines)


def autoteste():
    ws = [[str(i), i*10., 10., i*10.+5, 20., 0] for i in range(30)]
    gt = list(range(30))
    assert not eventos(gt, gt)
    assert len(eventos([0,2,1]+list(range(3,30)), gt)) == 3
    assert funcao_preservada(6)(list("abcdef"), list("abcdef"))
    assert not funcao_preservada(6)(list("abcdef"), list("abcxef"))
    assert ri.preservada(list("abcdefghijkl"), list("abcxefghijkx"))
    assert not funcao_preservada(12)(list("abcdefghijkl"), list("abcxefghijkx"))
    seq = list(range(15))+list(range(20,30))+list(range(15,20))
    assert len(eventos(seq, gt)) == 2
    assert ri.MIN_ALINHADAS == 10
    q = {"ws": ws, "gt_w": gt, "gt_r": ["A","B"], "reg_words": {"A": gt[:15], "B": gt[15:]},
         "p": {"dimensions": {"width": 300}}, "h": 10,
         "gold_lines": [{"id": f"l{i}", "ks": gt[i*5:(i+1)*5]} for i in range(6)],
         "gt_l": [f"l{i}" for i in range(6)]}
    itens = [{"tipo": "texto", "ks": gt}]
    certo = medir(q, gt, itens, {}, "P1")
    assert certo["quebras"] == 0 and certo["sucessor_linhas"] == 1 and certo["fid12"] == 1
    ev = [{"a": 0, "b": 15, "esperado": 1, "livre": False}]
    assert origem(ev, q, itens, "P1")[0] == {"caixa_fundida": 1}
    ev[0]["b"] = 2
    assert origem(ev, q, itens, "P1")[0] == {"interno_caixa": 1}
    itens = [{"tipo": "texto", "ks": [0]}, {"tipo": "texto", "ks": gt[1:]}]
    assert origem(ev, q, itens, "P1")[0] == {"caixa_partida": 1}
    assert origem(ev, q, itens, "P2")[0] == {"linha_partida": 1}
    return "permutacao, quebras, linhas intactas, fidelidade e categorias de origem: ok"


def assinatura_numeros(R):
    campos = {k: R[k] for k in ("resumos", "previa")}
    campos["paginas"] = [{k: r[k] for k in r if k not in ("origem_ls3",)} for r in R["paginas"]]
    return ac.digest(campos)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--reinferir", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    print(autoteste(), flush=True)
    qs = carregar_amostra()
    H = hashes(qs)
    anterior = ler(JSON)
    if args.conferir:
        if not anterior or anterior["hashes"] != H:
            raise ValueError("Hashes divergiram ou resultado ausente")
        texto = relatorio(anterior)
        if MD.read_text(encoding="utf-8") != texto:
            raise AssertionError("Markdown nao corresponde ao JSON")
        if assinatura_numeros(anterior) != anterior["assinatura_numeros"]:
            raise AssertionError("Numeros divergem da assinatura")
        for c in ("todas", "v4", "v3_novo"):
            rows = anterior["paginas"] if c == "todas" else [r for r in anterior["paginas"] if r["coorte"] == c]
            if ac.digest(resumir(rows)) != ac.digest(anterior["resumos"][c]):
                raise AssertionError("Resumo nao corresponde aos resultados por pagina")
        print("CONFERE: hashes, assinatura, resumos por pagina e Markdown identicos; arquivos nao modificados.")
        return
    fp = ac.digest(H)
    rows, modelo = [], None
    for i, q in enumerate(qs, 1):
        path = BASE / "paginas" / (ac.chave(q["p"]["page_id"]) + ".json")
        old = ler(path) if not args.do_zero and not args.reinferir else None
        if old and old.get("fingerprint") == fp:
            rows.append(old["resultado"])
        else:
            q["ls3"], modelo, origem_ls3 = carregar_ls3(q, H, args.reinferir, modelo)
            preds = prever_todos(q)
            r = {"page_id": q["p"]["page_id"], "uf": q["p"]["uf"], "coorte": q["coorte"],
                 "palavras": len(q["ws"]), "palavras_ouro": len(q["gt_w"]),
                 "auditoria": q["auditoria"], "origem_ls3": origem_ls3,
                 "metodos": {m: medir(q, *preds[m], m) for m in METODOS}}
            r["exemplos"] = [{**e, "a": q["ws"][e["a"]][0], "b": q["ws"][e["b"]][0],
                               "esperado": q["ws"][e["esperado"]][0] if e["esperado"] is not None else "FIM"}
                              for e in r["metodos"]["P2"]["eventos"][:3]]
            gravar(path, {"fingerprint": fp, "resultado": r})
            rows.append(r)
        print(f"[{i}/{len(qs)}] {q['coorte']} " + q["p"]["page_id"] + " | quebras " +
              " ".join(f"{m}={rows[-1]['metodos'][m]['quebras']}" for m in METODOS), flush=True)
        # Relatorio imediato com numeros parciais, antes de inferir outra pagina.
        gravar(MD, "# Erros de ponta a ponta — execução parcial\n\n" +
               f"Concluídas {len(rows)} de {len(qs)} páginas. Caches persistidos, apenas CPU.\n\n" +
               "| Pipeline | Quebras totais | Média por página |\n|---|---:|---:|\n" +
               "\n".join(f"| {m} | {sum(r['metodos'][m]['quebras'] for r in rows)} | {f(statistics.mean(r['metodos'][m]['quebras'] for r in rows))} |" for m in METODOS) + "\n")
    for q in qs:
        if "ls3" not in q:
            q["ls3"], modelo, _ = carregar_ls3(q, H, False, modelo)
    R = {"hashes": H, "config": {"fixa": FIXA.id, "nboot": NBOOT, "semente": SEMENTE,
         "deslocamento": N_DESLOCAMENTO, "device": "cpu"}, "autoteste": autoteste(), "paginas": rows,
         "resumos": {c: resumir(rows if c == "todas" else [r for r in rows if r["coorte"] == c])
                     for c in ("todas", "v4", "v3_novo")}, "previa": auditar_previa(qs)}
    R["assinatura_numeros"] = assinatura_numeros(R)
    if anterior and anterior.get("hashes") == H and args.do_zero:
        if anterior.get("assinatura_numeros") != R["assinatura_numeros"]:
            raise AssertionError("Reexecucao do zero divergiu dos numeros anteriores")
        R["conferencia_do_zero"] = "numeros identicos a execucao anterior"
    elif anterior and anterior.get("conferencia_do_zero"):
        R["conferencia_do_zero"] = anterior["conferencia_do_zero"]
    if hashes(qs) != H:
        raise ValueError("Entradas mudaram durante a execucao")
    gravar(MD, relatorio(R))
    gravar(JSON, R)
    print("\n" + "\n".join(tabela(R["resumos"]["todas"])), flush=True)
    print(R["veredito"])
    print("Relatorio e JSON gravados. Assinatura:", R["assinatura_numeros"])


if __name__ == "__main__":
    main()
