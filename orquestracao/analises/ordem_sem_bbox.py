"""Compara ordem por regioes finas e por linhas, tabelas e imagens atomicas.

Experimento exploratorio, somente CPU, sobre as anotacoes concluidas do golden_v4.
Reutiliza linhas/propor, XY-cut e metricas do repositorio. Nao le PDFs, nao usa
detector ao vivo e nao altera dados. A ordem humana so entra na avaliacao, na
selecao leave-one-page-out e no contrafactual explicitamente chamado de oraculo.

Uso (PowerShell, na raiz):
    $env:PYTHONIOENCODING='utf-8'
    venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox.py

Unicas saidas: resultados/ordem_sem_bbox.json e resultados/ordem_sem_bbox.md.
Cada execucao recalcula todas as predicoes; o Markdown e gerado do mesmo objeto
que vai ao JSON, com verificacao de hashes das entradas antes e depois.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import collections
import hashlib
import itertools
import json
import math
import statistics
from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import wilcoxon
from src.eval.baselines import caixas, xycut
from src.eval.metrics import kendall_tau, acerto_sucessor, ard_normalizado
from src.eval.protocolo import RAIZ_PROJETO
from src.data.regioes import linhas, propor, RE_MARCACAO

RAIZ = Path(RAIZ_PROJETO)
SAIDA_JSON = RAIZ / "resultados/ordem_sem_bbox.json"
SAIDA_MD = RAIZ / "resultados/ordem_sem_bbox.md"
ENTRADAS = [RAIZ / f"data/golden/golden_v4/{n}.jsonl" for n in ("tarefas", "anotacoes")]
ENTRADAS += [RAIZ / f"data/diamond/{l}/tarefas.jsonl" for l in ("diamond_piloto", "diamond_treino")]
FONTES = [RAIZ / p for p in ("src/data/regioes.py", "src/data/extrator.py", "src/eval/metrics.py", "src/eval/baselines.py")]
METRICAS = ("tau", "sucessor", "ard")
NOMES = {
    "xy_ouro": "XY-cut nas regiões-ouro",
    "ingenua": "Ingênua nas regiões-ouro",
    "xy_auto": "XY-cut no extrator automático",
    "plano_cv": "Sem bbox fina — seleção por página (LOPO)",
    "plano_melhor": "Sem bbox fina — melhor na amostra*",
    "oraculo_ti": "LOPO com tabela/imagem do ouro (diagnóstico)",
}


def ler(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def hashes():
    return {str(p.relative_to(RAIZ)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in ENTRADAS + FONTES}


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def centro(w):
    return (w[1] + w[3]) / 2, (w[2] + w[4]) / 2


def contem(b, c):
    return b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3]


def envelope(bs):
    return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]


def donos(palavras, regioes):
    """Reproduz a associacao do Golden: centro, menor caixa, nao figura primeiro."""
    saida = [[] for _ in regioes]
    ambiguas = 0
    livres = []
    for k, w in enumerate(palavras):
        ds = [i for i, r in enumerate(regioes) if contem(r["bbox"], centro(w))]
        if not ds:
            livres.append(k)
            continue
        ambiguas += len(ds) > 1
        nf = [i for i in ds if regioes[i].get("classe") != "figura"]
        alvo = min(nf or ds, key=lambda i: (area(regioes[i]["bbox"]), i))
        saida[alvo].append(k)
    return saida, livres, ambiguas


def preparar():
    ts = {p["page_id"]: p for p in ler(ENTRADAS[0])}
    todas = ler(ENTRADAS[1])
    # Filtrar ANTES de deduplicar: um rascunho posterior nao apaga uma ordem concluida.
    anns = {a["page_id"]: a for a in todas if a["status"] == "concluida"}
    ds = {l: {p["page_id"]: p for p in ler(RAIZ / f"data/diamond/{l}/tarefas.jsonl")}
          for l in ("diamond_piloto", "diamond_treino")}
    ps = []
    for pid in sorted(anns):
        p, a = ts[pid], anns[pid]
        d = ds[p["origem"]][pid]
        assert p["dimensions"] == d["dimensions"], (pid, "dimensoes diferentes")
        ws, rs = d["palavras"], p["bounding_boxes"]
        assert len(a["ordem"]) == len(rs) and set(a["ordem"]) == {r["id"] for r in rs}
        for r in rs + d["detector"]["regioes"]:
            assert len(r["bbox"]) == 4 and area(r["bbox"]) > 0, (pid, r)
        kws, livres, amb = donos(ws, rs)
        assert all(kws), (pid, "regiao-ouro sem palavras; projecao nao definida")
        por_r, por_l, ls = {}, {}, []
        divergencias = []
        divergencias_tokens = []
        for r, ks in zip(rs, kws):
            por_r[r["id"]] = ks
            rl = linhas(ws, ks)
            texto = " ".join(L["texto"] for L in rl)
            if " ".join(texto.split()) != " ".join(r["text"].split()):
                divergencias.append(r["id"])
                if collections.Counter(texto.split()) != collections.Counter(r["text"].split()):
                    divergencias_tokens.append(r["id"])
            por_l[r["id"]] = []
            for i, L in enumerate(rl):
                lid = f"{r['id']}:l{i}"
                por_l[r["id"]].append(lid)
                ls.append({"id": lid, "regiao": r["id"], "ks": L["ks"], "bbox": L["bbox"]})
        gt_l = [lid for rid in a["ordem"] for lid in por_l[rid]]
        h = statistics.median(w[4] - w[2] for w in ws)
        fora = sum(not (-1 <= centro(w)[0] <= p["dimensions"]["width"] + 1 and
                        -1 <= centro(w)[1] <= p["dimensions"]["height"] + 1) for w in ws)
        ps.append({"p": p, "d": d, "ws": ws, "gt_r": a["ordem"], "gt_l": gt_l,
                   "reg_words": por_r, "gold_lines": ls, "h": h,
                   "texto_ids": {L["id"] for L in ls if next(r for r in rs if r["id"] == L["regiao"])["classe"] not in ("tabela", "figura")},
                   "auditoria": {"palavras": len(ws), "sem_regiao_ouro": len(livres),
                                  "sobreposicao_ouro": amb, "texto_divergente": divergencias,
                                  "tokens_divergentes": divergencias_tokens,
                                  "centros_fora_pagina": fora}})
    assert len(ps) == 44, f"Esperadas 44 paginas concluidas, encontradas {len(ps)}"
    return ps, {"tarefas": len(ts), "anotacoes": len(todas),
                "status": dict(collections.Counter(a["status"] for a in todas)), "concluidas": len(ps)}


def linhas_partidas(ws, ks, gap, h):
    """Agrupa com linhas() e rompe vaos horizontais, sem usar blocos ou regioes finas."""
    saida = []
    for L in linhas(ws, ks):
        grupos = [[]]
        fim = -math.inf
        for k in L["ks"]:
            if grupos[-1] and ws[k][1] - fim > max(4.0, gap * h):
                grupos.append([])
            grupos[-1].append(k)
            fim = max(fim, ws[k][3])
        for g in grupos:
            saida.append({"tipo": "texto", "ks": g, "bbox": envelope([ws[k][1:5] for k in g])})
    return saida


def atomos(ws, det, score):
    """NMS conservador; tabela tem prioridade; cada palavra fica em um unico item."""
    cand = [r for r in det if r["rotulo"] in ("table", "picture") and r["score"] >= score]
    cand.sort(key=lambda r: (r["rotulo"] != "table", -r["score"], r["bbox"]))
    aceitos = []
    for r in cand:
        if any(inter(r["bbox"], m["bbox"]) >= 0.6 * area(r["bbox"]) for m in aceitos):
            continue
        aceitos.append({"tipo": r["rotulo"], "bbox": list(r["bbox"]), "score": r["score"], "ks": []})
    livres = []
    for k, w in enumerate(ws):
        dentro = [m for m in aceitos if contem(m["bbox"], centro(w))]
        if dentro:
            m = min(dentro, key=lambda a: (a["tipo"] != "table", area(a["bbox"]), -a["score"]))
            m["ks"].append(k)
        else:
            livres.append(k)
    return aceitos, livres


def boxes(items):
    return [{"x0": m["bbox"][0], "top": m["bbox"][1], "x1": m["bbox"][2], "bottom": m["bbox"][3]}
            for m in items]


def vales(items, ids, h, limiar):
    """Projecao de tinta por envelopes de linhas; linhas largas nao abafam a calha.

    Bins de 2 pontos, soma de altura ocupada. Vales <= limiar da mediana da
    tinta positiva, largura >= 4 pontos. Exige massa e suporte vertical dos
    dois lados; retorna no maximo tres cortes (ate quatro colunas).
    """
    if len(ids) < 8:
        return []
    bs = [items[i]["bbox"] for i in ids]
    lo, _, hi, _ = envelope(bs)
    W = hi - lo
    if W < 80:
        return []
    eleg = [b for b in bs if 0.12 * W <= b[2] - b[0] < 0.60 * W]
    if len(eleg) < 8:
        return []
    passo = 2.0
    n = int(math.ceil(W / passo)) + 1
    hist = np.zeros(n)
    for b in eleg:
        ini = max(0, int((b[0] - lo) / passo))
        fim = min(n, int(math.ceil((b[2] - lo) / passo)))
        hist[ini:fim] += max(h, min(b[3] - b[1], 2 * h))
    pos = hist[hist > 0]
    if not len(pos):
        return []
    baixa = hist <= limiar * np.median(pos)
    faixas = []
    ini = None
    for j, baixa_j in enumerate(np.r_[baixa, False]):
        if baixa_j and ini is None:
            ini = j
        if not baixa_j and ini is not None:
            if j - ini >= 2:
                x = lo + (ini + j) * passo / 2
                esq = [b for b in eleg if b[2] <= x]
                dire = [b for b in eleg if b[0] >= x]
                if (lo + 0.16 * W < x < hi - 0.16 * W and len(esq) >= 4 and len(dire) >= 4
                        and min(max(b[3] for b in esq), max(b[3] for b in dire))
                        - max(min(b[1] for b in esq), min(b[1] for b in dire)) > 2 * h):
                    faixas.append((j - ini, x))
            ini = None
    escolhidos = []
    for _, x in sorted(faixas, reverse=True):
        if all(abs(x - c) >= 0.16 * W for c in escolhidos):
            escolhidos.append(x)
        if len(escolhidos) == 3:
            break
    return sorted(escolhidos)


def vales_locais(items, ids, h, limiar):
    """Vota em calhas que reaparecem em janelas verticais, para tolerar rodape distinto."""
    if len(ids) < 8:
        return []
    lo, y0, hi, y1 = envelope([items[i]["bbox"] for i in ids])
    W = hi - lo
    janela = max(100.0, 12 * h)
    candidatos = []
    for y in np.arange(y0, y1, janela / 2):
        locais = [i for i in ids if y <= (items[i]["bbox"][1] + items[i]["bbox"][3]) / 2 < y + janela]
        for x in vales(items, locais, h, limiar):
            if lo + 0.16 * W < x < hi - 0.16 * W:
                candidatos.append((x, float(y)))
    grupos = []
    for x, y in sorted(candidatos):
        if grupos and abs(x - statistics.median(t[0] for t in grupos[-1])) <= max(4, 0.015 * W):
            grupos[-1].append((x, y))
        else:
            grupos.append([(x, y)])
    aceitos = []
    for g in sorted(grupos, key=lambda g: len({y for _, y in g}), reverse=True):
        x = statistics.median(t[0] for t in g)
        # Janelas sobrepostas contam como evidencia exploratoria, nao como amostras independentes.
        if len({y for _, y in g}) >= 2 and all(abs(x - c) >= 0.16 * W for c in aceitos):
            aceitos.append(x)
        if len(aceitos) == 3:
            break
    return sorted(aceitos)


def ordenar_projecao(items, ids, h, limiar, diag, depth=0, local=False):
    if not ids:
        return []
    if depth > 60:
        return sorted(ids, key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
    cortes = vales_locais(items, ids, h, limiar) if local else vales(items, ids, h, limiar)
    if local and not cortes:
        cortes = vales(items, ids, h, limiar)
    if not cortes:
        # Fallback usa XY-cut verdadeiro; tambem trata uma faixa larga sem vale.
        return xycut(ids, boxes(items))
    diag["max_colunas"] = max(diag["max_colunas"], len(cortes) + 1)
    W = max(items[i]["bbox"][2] for i in ids) - min(items[i]["bbox"][0] for i in ids)
    # Uma palavra iniciada no gutter (ARTIGOS) nao e uma faixa larga.
    def atravessa(i, c):
        b = items[i]["bbox"]
        return b[0] < c < b[2] and (not local or min(c - b[0], b[2] - c) >= 0.10 * W)
    largos = [i for i in ids if any(atravessa(i, c) for c in cortes)]
    if largos:
        largos.sort(key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
        diag["pontes"] += len(largos)
        conj = set(largos)
        ys = [(items[i]["bbox"][1] + items[i]["bbox"][3]) / 2 for i in largos]
        secoes = [[] for _ in range(len(largos) + 1)]
        for i in ids:
            if i not in conj:
                cy = (items[i]["bbox"][1] + items[i]["bbox"][3]) / 2
                secoes[sum(y < cy for y in ys)].append(i)
        saida = []
        for j, sec in enumerate(secoes):
            saida.extend(ordenar_projecao(items, sec, h, limiar, diag, depth + 1, local))
            if j < len(largos):
                saida.append(largos[j])
        return saida
    grupos = [[] for _ in range(len(cortes) + 1)]
    for i in ids:
        cx = (items[i]["bbox"][0] + items[i]["bbox"][2]) / 2
        grupos[sum(c < cx for c in cortes)].append(i)
    return [i for g in grupos for i in ordenar_projecao(items, g, h, limiar, diag, depth + 1, local)]


@dataclass(frozen=True)
class Config:
    abordagem: str
    score: float
    gap: float
    vale: float = 0.12

    @property
    def id(self):
        return f"{self.abordagem}_s{self.score:.2f}_g{self.gap:.1f}_v{self.vale:.2f}"


def grade():
    cs = []
    for score, gap in itertools.product((0.45, 0.65, 0.85), (1.2, 2.0)):
        for abordagem in ("xy_linhas", "xy_margens", "projecao", "projecao_margens", "projecao_local", "projecao_local_margens"):
            for vale in ((0.08, 0.20) if abordagem.startswith("projecao") else (0.12,)):
                cs.append(Config(abordagem, score, gap, vale))
    return cs


def fluxo(items, ws):
    """Expande atomos so para a regua de linhas; sua posicao continua indivisivel."""
    return [k for m in items for L in linhas(ws, m["ks"]) for k in L["ks"]]


def prever(q, c, oraculo=False):
    ws, p, h = q["ws"], q["p"], q["h"]
    if oraculo:
        det = [{"rotulo": "table" if r["classe"] == "tabela" else "picture", "score": 1.0, "bbox": r["bbox"]}
               for r in p["bounding_boxes"] if r["classe"] in ("tabela", "figura")]
    else:
        det = q["d"]["detector"]["regioes"]
    ats, livres = atomos(ws, det, c.score)
    items = ats + linhas_partidas(ws, livres, c.gap, h)
    diag = {"max_colunas": 1, "pontes": 0, "n_atomos": len(ats),
            "atomos_sem_palavras": sum(not a["ks"] for a in ats),
            "n_linhas_pred": len(items) - len(ats), "margem_topo": 0, "margem_fim": 0, "marcas": 0}
    ids = list(range(len(items)))
    inicio, fim, marcas = [], [], []
    if c.abordagem.endswith("margens"):
        corpo = []
        H = p["dimensions"]["height"]
        for i in ids:
            m = items[i]
            cy = (m["bbox"][1] + m["bbox"][3]) / 2
            if m["ks"] and all(RE_MARCACAO.match(ws[k][0]) for k in m["ks"]):
                marcas.append(i)
            elif cy < 0.07 * H and m["bbox"][3] < 0.10 * H:
                inicio.append(i)
            elif cy > 0.95 * H:
                fim.append(i)
            else:
                corpo.append(i)
        ids = corpo
        diag.update(margem_topo=len(inicio), margem_fim=len(fim), marcas=len(marcas))
    if c.abordagem.startswith("projecao"):
        ordem = ordenar_projecao(items, ids, h, c.vale, diag, local="local" in c.abordagem)
    else:
        ordem = xycut(ids, boxes(items))
    chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
    ordem = sorted(inicio, key=chave) + ordem + sorted(marcas, key=chave) + sorted(fim, key=chave)
    assert sorted(ordem) == list(range(len(items)))
    items = [items[i] for i in ordem]
    seq = fluxo(items, ws)
    assert len(seq) == len(ws) and set(seq) == set(range(len(ws)))
    return seq, items, diag


def metricas(pred, gt):
    assert len(pred) == len(gt) and set(pred) == set(gt)
    return {"tau": kendall_tau(pred, gt), "sucessor": acerto_sucessor(pred, gt),
            "ard": ard_normalizado(pred, gt)}


def projetar(q, seq):
    rank = {k: i for i, k in enumerate(seq)}
    rr = {rid: statistics.median(rank[k] for k in ks) for rid, ks in q["reg_words"].items()}
    lr = {L["id"]: statistics.median(rank[k] for k in L["ks"]) for L in q["gold_lines"]}
    # Empate nao usa posicao humana nem ordem dos ids na anotacao.
    rbox = {r["id"]: r["bbox"] for r in q["p"]["bounding_boxes"]}
    lbox = {L["id"]: L["bbox"] for L in q["gold_lines"]}
    pr = sorted(rr, key=lambda rid: (rr[rid], rbox[rid][1], rbox[rid][0], rid))
    pl = sorted(lr, key=lambda lid: (lr[lid], lbox[lid][1], lbox[lid][0], lid))
    return pr, pl, {"empates_regioes": len(rr) - len(set(rr.values())),
                    "empates_linhas": len(lr) - len(set(lr.values()))}


def avaliar_fluxo(q, seq, pr=None):
    pr_proj, pl, diag = projetar(q, seq)
    pr = pr if pr is not None else pr_proj
    texto_ids = q["texto_ids"]
    por_w = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
    vis = [por_w[k] for k in seq if k in por_w]
    runs = collections.Counter(a for i, a in enumerate(vis) if i == 0 or vis[i - 1] != a)
    diag["regioes_fragmentadas"] = sum(v > 1 for v in runs.values())
    diag["fracao_regioes_fragmentadas"] = diag["regioes_fragmentadas"] / len(q["gt_r"])
    return {"regioes": metricas(pr, q["gt_r"]), "linhas": metricas(pl, q["gt_l"]),
            "linhas_texto": metricas([l for l in pl if l in texto_ids], [l for l in q["gt_l"] if l in texto_ids]),
            "diag": diag, "ordem_regioes": pr, "ordem_linhas": pl}


def baselines(q):
    p, ws = q["p"], q["ws"]
    bs, ids = caixas(p), [r["id"] for r in p["bounding_boxes"]]
    xy = [ids[i] for i in xycut(list(range(len(ids))), bs)]
    ing = [ids[i] for i in sorted(range(len(ids)), key=lambda i: (bs[i]["top"], bs[i]["x0"]))]
    assert xy == p["ordens"]["xycut"], (p["page_id"], "XY-cut recalculada difere da armazenada")
    assert ing == p["ordens"]["naive"]
    saida = {}
    for nome, ordem in (("xy_ouro", xy), ("ingenua", ing)):
        seq = [k for rid in ordem for L in linhas(ws, q["reg_words"][rid]) for k in L["ks"]]
        saida[nome] = avaliar_fluxo(q, seq, ordem)
    auto = propor(ws, q["d"]["blocos_v3"], q["d"]["detector"]["regioes"], regras=True)
    ks, livres, _ = donos(ws, auto)
    items = [{"bbox": r["bbox"], "ks": g, "tipo": r["classe"]} for r, g in zip(auto, ks)]
    ordem = xycut(list(range(len(items))), boxes(items))
    seq = fluxo([items[i] for i in ordem], ws)
    # Sem regioes para palavras descartadas pelo extrator: ficam no fim geometricamente.
    seq += [k for L in linhas(ws, livres) for k in L["ks"]]
    assert len(seq) == len(ws) and len(set(seq)) == len(ws)
    saida["xy_auto"] = avaliar_fluxo(q, seq)
    saida["xy_auto"]["diag"].update(n_regioes_pred=len(auto), palavras_fallback=len(livres))
    return saida


def resumo(regs, nboot, seed):
    rng = np.random.default_rng(seed)
    amostras = rng.integers(0, len(regs), size=(nboot, len(regs)))
    ret = {"n": len(regs)}
    for regua in ("regioes", "linhas", "linhas_texto"):
        ret[regua] = {}
        for m in METRICAS:
            v = np.array([r[regua][m] for r in regs])
            ic = np.quantile(v[amostras].mean(axis=1), [0.025, 0.975])
            ret[regua][m] = {"media": float(v.mean()), "ic95": ic.tolist()}
    ret["fragmentacao_media"] = statistics.mean(r["diag"]["fracao_regioes_fragmentadas"] for r in regs)
    return ret


def testes(a, b, nboot, seed):
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(a), size=(nboot, len(a)))
    out = {}
    for regua in ("regioes", "linhas"):
        testes_r = {}
        for m in METRICAS:
            d = np.array([x[regua][m] - y[regua][m] for x, y in zip(a, b)])
            if np.all(np.abs(d) < 1e-12):
                stat, p = 0.0, 1.0
            else:
                w = wilcoxon(d, zero_method="wilcox", alternative="two-sided", method="auto")
                stat, p = float(w.statistic), float(w.pvalue)
            testes_r[m] = {"diferenca": float(d.mean()), "ic95": np.quantile(d[ix].mean(axis=1), [0.025, 0.975]).tolist(),
                           "wilcoxon_W": stat, "p": p,
                           "ganha": int(sum(d > 1e-12) if m != "ard" else sum(d < -1e-12)),
                           "empata": int(sum(abs(d) <= 1e-12)),
                           "perde": int(sum(d < -1e-12) if m != "ard" else sum(d > 1e-12))}
        crescente = sorted(METRICAS, key=lambda m: testes_r[m]["p"])
        anterior = 0
        for j, m in enumerate(crescente):
            anterior = max(anterior, min(1.0, (len(METRICAS) - j) * testes_r[m]["p"]))
            testes_r[m]["p_holm"] = anterior
        out[regua] = testes_r
    return out


def diagnostico(q, c, aval, oracle, items):
    p, ws = q["p"], q["ws"]
    ats = [m for m in items if m["tipo"] in ("table", "picture")]
    cobertura = []
    for r in p["bounding_boxes"]:
        if r["classe"] not in ("tabela", "figura"):
            continue
        tipo = "table" if r["classe"] == "tabela" else "picture"
        g = set(q["reg_words"][r["id"]])
        cand = [m for m in ats if m["tipo"] == tipo]
        cob = max((len(g.intersection(m["ks"])) / len(g) for m in cand), default=0.0)
        cobertura.append({"id": r["id"], "classe": r["classe"], "cobertura_palavras": cob})
    cls = {r["id"]: r["classe"] for r in p["bounding_boxes"]}
    gtpos = {rid: i for i, rid in enumerate(q["gt_r"])}
    pred = aval["ordem_regioes"]
    desloc = sorted(pred, key=lambda rid: abs(pred.index(rid) - gtpos[rid]), reverse=True)[:5]
    pp = {rid: i for i, rid in enumerate(pred)}
    inv = [(a, b) for i, a in enumerate(q["gt_r"]) for b in q["gt_r"][i + 1:] if pp[a] > pp[b]]
    margens = sum(cls[a] in ("cabecalho", "rodape", "outro") or cls[b] in ("cabecalho", "rodape", "outro") for a, b in inv)
    textos = {r["id"]: r["text"] for r in p["bounding_boxes"]}
    return {"atomos_ouro": cobertura, "inversoes": len(inv), "inversoes_com_margem_ou_marca": margens,
            "deslocados": [{"id": r, "classe": cls[r], "pos_ouro": gtpos[r], "pos_pred": pp[r], "texto": textos[r][:180]}
                           for r in desloc],
            "delta_oraculo_tau": oracle["regioes"]["tau"] - aval["regioes"]["tau"],
            "config": asdict(c)}


def verificar_sinteticos():
    """Testa hipoteses geometricas e invariantes sem abrir dados ou criar arquivos."""
    casos = []
    for faixa in (False, True):
        items = [{"bbox": [x, y, x + 90, y + 8], "ks": [], "tipo": "texto"}
                 for x in (10, 130) for y in (80, 100, 120, 140)]
        if faixa:
            items.append({"bbox": [10, 165, 220, 175], "ks": [], "tipo": "texto"})
            items += [{"bbox": [x, y, x + 90, y + 8], "ks": [], "tipo": "texto"}
                      for x in (10, 130) for y in (200, 220, 240, 260)]
        ids = list(range(len(items)))
        for abordagem in ("xy", "projecao", "projecao_local"):
            diag = {"max_colunas": 1, "pontes": 0}
            pred = xycut(ids, boxes(items)) if abordagem == "xy" else ordenar_projecao(
                items, ids, 8, 0.08, diag, local=abordagem.endswith("local"))
            assert pred == ids, ("sintetico", faixa, abordagem, pred)
            casos.append({"caso": "duas_colunas_com_faixa" if faixa else "duas_colunas", "metodo": abordagem, "ok": True})
    ws = [["a", 10, 100, 20, 110, -1], ["b", 40, 100, 50, 110, -1], ["c", 10, 120, 20, 130, -1]]
    det = [{"rotulo": "table", "score": 0.9, "bbox": [5, 95, 60, 140]},
           {"rotulo": "table", "score": 0.8, "bbox": [6, 96, 59, 139]}]
    ats, livres = atomos(ws, det, 0.45)
    assert len(ats) == 1 and ats[0]["ks"] == [0, 1, 2] and not livres
    casos.append({"caso": "tabela_atomica_e_supressao_de_duplicata", "ok": True})
    # Contraprova: cabecalho central estreito abafa o corte; ruido no topo inverte tabelas.
    ws = [["cabecalho", 110, 30, 240, 40, -1], ["esquerda", 20, 200, 80, 210, -1],
          ["direita", 220, 200, 280, 210, -1], ["rodape", 110, 810, 240, 820, -1]]
    det = [{"rotulo": "table", "score": 0.9, "bbox": [20, 100.2, 180, 780]},
           {"rotulo": "table", "score": 0.9, "bbox": [220, 100.0, 380, 780]}]
    q = {"ws": ws, "h": 10, "p": {"dimensions": {"width": 400, "height": 842}},
         "d": {"detector": {"regioes": det}}}
    sem, _, _ = prever(q, Config("projecao_local", 0.45, 1.2, 0.20))
    com, _, _ = prever(q, Config("projecao_local_margens", 0.45, 1.2, 0.20))
    assert sem == [0, 2, 1, 3] and com == [0, 1, 2, 3], (sem, com)
    casos.append({"caso": "contraprova_jitter_tabelas_e_margens", "ok": True,
                  "sem_margens": sem, "com_margens": com})
    return casos


def f(v, n=3):
    return f"{v:.{n}f}".replace(".", ",")


def cel(x, percent=False):
    k, n, sufixo = (100, 1, "%") if percent else (1, 3, "")
    a, b = x["ic95"]
    return f"{f(k * x['media'], n)}{sufixo} [{f(k * a, n)}; {f(k * b, n)}]"


def tabela(sumarios, metodos, regua):
    out = ["| Método | τ de Kendall ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |",
           "|---|---:|---:|---:|"]
    for m in metodos:
        r = sumarios[m][regua]
        out.append(f"| {NOMES.get(m, m)} | {cel(r['tau'])} | {cel(r['sucessor'], True)} | {cel(r['ard'])} |")
    return out


def relatorio(R):
    S = R["resumo"]["todas"]
    cv, ref, auto = S["plano_cv"]["regioes"], S["xy_ouro"]["regioes"], S["xy_auto"]["regioes"]
    tl = R["testes"]["plano_cv"]["regioes"]["tau"]
    melhor = R["melhor_config"]
    out = ["# Ordem de leitura sem regiões finas", "",
           "## Resumo em cinco linhas", "",
           f"1. Nas {R['amostra']['concluidas']} páginas, o plano com seleção LOPO alcançou τ = {f(cv['tau']['media'])}, contra {f(ref['tau']['media'])} da XY-cut em regiões humanas e {f(auto['tau']['media'])} no extrator automático.",
           f"2. O sucessor em regiões foi {f(100 * cv['sucessor']['media'], 1)}%, contra {f(100 * ref['sucessor']['media'], 1)}% da referência; em linhas, {f(100 * S['plano_cv']['linhas']['sucessor']['media'], 1)}% contra {f(100 * S['xy_ouro']['linhas']['sucessor']['media'], 1)}%.",
           f"3. A diferença pareada de τ em regiões foi {f(tl['diferenca'])}, IC 95% [{f(tl['ic95'][0])}; {f(tl['ic95'][1])}], Wilcoxon p = {f(tl['p'], 5)}.",
           f"4. No estrato multicoluna, τ de regiões foi {f(R['resumo']['multi']['plano_cv']['regioes']['tau']['media'])} contra {f(R['resumo']['multi']['xy_ouro']['regioes']['tau']['media'])}; o ganho agregado não significa vitória em todos os layouts.",
           "5. Veredito: vale avançar com projeção local, política de margens e átomos bem delimitados; a melhora é exploratória e precisa de teste novo por veículo antes de substituir o pipeline.", "",
           "## Dados e auditoria", "",
           f"Foram lidas {R['amostra']['tarefas']} tarefas e {R['amostra']['anotacoes']} registros de anotação: {R['amostra']['status']}. Filtrou-se `concluida` antes de deduplicar por `page_id`; um rascunho posterior não revoga a ordem concluída. Nenhuma página concluída foi excluída.", "",
           f"Distribuição pelo `stats.n_colunas` fornecido: {R['contagem_colunas']}. Esse campo é uma estimativa geométrica do preparador do Golden, não uma anotação independente de colunas; serve somente para estratificar e nunca alimenta o preditor.", "",
           f"Dimensões idênticas entre Golden e Diamond em todas as páginas. A associação por centro e menor região, preferindo não figura, recuperou {R['auditoria']['regioes']} regiões e {R['auditoria']['linhas']} linhas com palavras. Textos reconstruídos divergentes: {R['auditoria']['textos_divergentes']}; divergências no multiconjunto de tokens: {R['auditoria']['tokens_divergentes']}; regiões sem palavras: {R['auditoria']['regioes_sem_palavras']}; centros de palavras fora da página (tolerância de um ponto): {R['auditoria']['centros_fora_pagina']}. As divergências são somente de ordenação de palavras em cabeçalhos com fontes de alturas diferentes (Seropédica e Salvador): o agrupador atual atualiza a altura da faixa, o montador do Golden não o fazia. Nenhuma é perda de palavras ou erro de escala/coordenadas.", "",
           f"Há {R['auditoria']['palavras']} palavras; {R['auditoria']['sem_regiao_ouro']} ficam fora das regiões-ouro e {R['auditoria']['sobreposicao_ouro']} pertencem geometricamente a mais de uma caixa. As primeiras continuam na predição e são excluídas apenas da régua sem referência; as segundas recebem um único dono pelo critério do preparador. Hashes das quatro entradas e dos módulos reutilizados foram conferidos antes/depois e estão no JSON.", "",
           "## Implementação e réguas", "",
           "O preditor recebe somente palavras e regiões cruas `table`/`picture`. Não recebe ordem do PDF, `bloco` das palavras, regiões humanas, classes finas do detector nem contagem de colunas. Aceita átomos por score, suprime caixas com pelo menos 60% da própria área dentro de uma aceita (tabela primeiro) e atribui por centro. Palavras dentro de imagem também saem do fluxo: trata-se exatamente da proposta pedida, inclusive quando o detector chama um cabeçalho decorativo de imagem.", "",
           "O restante é agrupado com `src.data.regioes.linhas` e partido nos grandes vãos horizontais. Foram comparadas: (a) XY-cut recursiva diretamente nos fragmentos de linha e átomos; (b) projeção horizontal da ocupação por envelopes das linhas, com vales de espaço em branco, suporte vertical dos dois lados e recursão. Linhas largas são retiradas do perfil; caixas que atravessam os cortes separam seções acima/abaixo. Sem vale, a projeção recorre à XY-cut existente. Isso permite layout variável por faixa, mas a regra de pontes pode interromper colunas indevidamente.", "",
           "A terceira abordagem, `projecao_local`, vota em vales que reaparecem em pelo menos duas janelas verticais sobrepostas (altura igual ao maior valor entre cem pontos e doze alturas de linha, passo de meia janela). Ela evita que um rodapé de outro arranjo abafe a calha do corpo. Também exige que uma ponte cubra pelo menos 10% da largura do conjunto em cada lado do corte: um título curto iniciado na calha é atribuído à coluna pelo centro, em vez de interromper toda a página. Há fallback para o perfil global e para XY-cut. As janelas e o filtro de pontes são hipóteses geométricas fixas, não classes finas.", "",
           "As variantes `*_margens` adicionam uma política geométrica fixa: itens com centro acima de 7% da altura e base acima de 10% vêm primeiro; abaixo de 95% vêm por último. Marcas reconhecidas pela expressão `RE_MARCACAO` vão antes do rodapé. São heurísticas de posição/conteúdo, sem previsão de classe fina. Os limiares de margem não foram varridos; podem deslocar conteúdo legítimo.", "",
           "**Regiões:** posição prevista = mediana dos ranks das palavras daquela região. **Linhas:** ouro = regiões na ordem humana, expandidas com `linhas()` de cima para baixo e palavras da esquerda para a direita; posição prevista da linha = mediana dos ranks de suas palavras. Átomos são expandidos internamente por esse mesmo critério só para medir linhas, permanecendo contíguos na predição. Todas as ordens avaliadas são permutações completas dos mesmos identificadores, sem consertar faltantes pela ordem humana. Empates usam geometria e ID, nunca rank-ouro.", "",
           "XY-cut e ingênua em regiões humanas têm segmentação-oráculo; sua régua de regiões usa a sequência diretamente e a régua de linhas expande cada região internamente. A XY-cut recalculada e a ingênua coincidiram exatamente com as armazenadas em todas as páginas. O extrator automático é `propor(..., regras=True)` com `fundir=True` atual; as palavras são reassociadas às caixas pelo mesmo critério, ordenadas por XY-cut e expandidas por linhas.", "",
           f"Fallback de palavras sem caixa do extrator automático: {R['auditoria']['fallback_auto']} (anexadas geometricamente ao fim, sem consultar o ouro). Empates na projeção LOPO: {R['auditoria']['empates_cv_regioes']} em regiões e {R['auditoria']['empates_cv_linhas']} em linhas.", "",
           "## Seleção de parâmetros e inferência", "",
           f"A grade final tem {len(R['grade'])} configurações: score ≥ 0,45/0,65/0,85; vão de linha > 1,2/2,0 alturas medianas; projeção com vale ≤ 0,08/0,20 da ocupação positiva mediana, em bins de dois pontos e largura mínima de quatro pontos; seis variantes de abordagem/política. O cache já elimina detecções abaixo de 0,45, portanto não permite avaliar um detector mais permissivo.", "",
           f"**Exploração declarada:** a primeira grade tinha {R['grade_inicial']} configurações sem projeção local. Após medir e inspecionar os erros dessas mesmas páginas, acrescentou-se a hipótese de janelas locais e suporte dos dois lados. Portanto, o desenho da abordagem local foi informado por este ouro. A validação por página abaixo não torna essa fase um teste independente.", "",
           "O resultado **LOPO** escolhe a configuração de maior τ médio de regiões nas outras páginas, sem usar a métrica da página retida; desempates usam sucessor e depois a ordem fixa da grade. A melhor configuração na amostra também é mostrada, **com seleção e avaliação nas mesmas páginas**, portanto otimista. O desenvolvimento do algoritmo foi feito neste conjunto: LOPO reduz o viés de escolher parâmetros, mas não apaga o viés de desenvolvimento nem o parentesco entre páginas do mesmo veículo.", "",
           f"Melhor configuração na amostra: `{melhor['id']}`. Escolhas LOPO: {R['selecao_cv']}. Não há treino de rede, uso de GPU, OCR ou acesso a dados de terceiros. Foram executados {len(R['sinteticos'])} controles sintéticos: colunas, faixa que interrompe colunas, atomicidade/NMS e uma contraprova de inversão de tabelas por pequenas diferenças de topo.", "",
           f"Médias macro por página; IC percentil 95% com {R['bootstrap']['reamostras']} reamostras de páginas, semente {R['bootstrap']['semente']}. IC de diferenças usa pares das mesmas páginas. Os IC são condicionais às configurações selecionadas: não refazem a seleção dentro do bootstrap. Wilcoxon bilateral pareado (`zero_method='wilcox'`, SciPy `method='auto'`), com p bruto e correção Holm entre as três métricas de cada régua. Testes são exploratórios, não um teste de equivalência/não inferioridade.", "",
           "## Tabela principal — todas as páginas", "",
           "Régua de regiões (comparável ao relatório do TCC):", ""]
    principais = ["xy_ouro", "ingenua", "xy_auto", "plano_cv", "plano_melhor", "oraculo_ti"]
    out += tabela(S, principais, "regioes")
    out += ["", "Régua de linhas:", ""] + tabela(S, principais, "linhas")
    out += ["", "\* Selecionada na mesma amostra; não é estimativa de generalização. O oráculo tabela/imagem é um contrafactual com caixas humanas dessas classes, usando a configuração LOPO correspondente; não é um método disponível em produção.", "",
            f"A referência reproduziu τ = {f(S['xy_ouro']['regioes']['tau']['media'])} e sucessor = {f(100 * S['xy_ouro']['regioes']['sucessor']['media'], 1)}%, como os valores citados de 0,825 e 71,5%.", "",
            "## Estratificação por número de colunas", ""]
    for grupo, nome in (("uma", "Uma coluna"), ("multi", "Multicoluna")):
        out += [f"### {nome} — n = {R['resumo'][grupo]['xy_ouro']['n']}", "", "Regiões:", ""]
        out += tabela(R["resumo"][grupo], principais, "regioes")
        out += ["", "Linhas:", ""] + tabela(R["resumo"][grupo], principais, "linhas") + [""]
    out += [f"O ganho em regiões se concentra no estrato classificado como uma coluna: τ {f(R['resumo']['uma']['xy_ouro']['regioes']['tau']['media'])} → {f(R['resumo']['uma']['plano_cv']['regioes']['tau']['media'])}. No estrato multicoluna, o plano perde em τ de regiões e sucessor, enquanto τ de linhas muda de {f(R['resumo']['multi']['xy_ouro']['linhas']['tau']['media'])} para {f(R['resumo']['multi']['plano_cv']['linhas']['tau']['media'])}; sucessor de linhas cai de {f(100*R['resumo']['multi']['xy_ouro']['linhas']['sucessor']['media'],1)}% para {f(100*R['resumo']['multi']['plano_cv']['linhas']['sucessor']['media'],1)}%.", "",
            "**Cuidado com esse estrato:** a inspeção mostra o Legislativo do RJ com três colunas e Manaus com duas tabelas lado a lado, embora ambos tenham `stats.n_colunas = 1`. Duque de Caxias/capa também tem duas colunas visuais e está no estrato de uma. AC e MS, com uma tabela larga e cabeçalho em campos, entram como multicoluna. Mantive o campo solicitado sem corrigir dados; não interpretar estas tabelas como separação perfeita da complexidade visual.", ""]
    out += ["## Wilcoxon e diferenças pareadas contra XY-cut nas regiões-ouro", "",
            "| Método | Régua | Métrica | Δ médio (IC 95%) | Ganha/empata/perde | W | p bruto | p Holm |",
            "|---|---|---|---:|---:|---:|---:|---:|"]
    for metodo in ("plano_cv", "plano_melhor"):
        for regua in ("regioes", "linhas"):
            for m in METRICAS:
                t = R["testes"][metodo][regua][m]
                a, b = t["ic95"]
                out.append(f"| {NOMES[metodo]} | {regua} | {m} | {f(t['diferenca'])} [{f(a)}; {f(b)}] | {t['ganha']}/{t['empata']}/{t['perde']} | {f(t['wilcoxon_W'], 1)} | {f(t['p'], 6)} | {f(t['p_holm'], 6)} |")
    out += ["", "Δ = plano − referência; ARD negativo é melhora. Ausência de significância não prova equivalência.", "",
            "## Sensibilidade e continuidade ocultada pela mediana", "",
            "| Abordagem | Configuração de maior τ na amostra* | τ regiões | Sucessor regiões | τ linhas | Sucessor linhas |",
            "|---|---|---:|---:|---:|---:|"]
    for fam, obj in R["melhores_familias"].items():
        r = obj["resumo"]
        out.append(f"| {fam} | `{obj['id']}` | {f(r['regioes']['tau']['media'])} | {f(100*r['regioes']['sucessor']['media'],1)}% | {f(r['linhas']['tau']['media'])} | {f(100*r['linhas']['sucessor']['media'],1)}% |")
    out += ["", "Todas as configurações e métricas por página estão no JSON; as linhas acima também são selecionadas na amostra.", "",
            "| Score | Melhor configuração na amostra* | τ regiões | Sucessor regiões | τ linhas |",
            "|---|---|---:|---:|---:|"]
    for score, obj in R["melhores_scores"].items():
        r = obj["resumo"]
        out.append(f"| {f(float(score),2)} | `{obj['id']}` | {f(r['regioes']['tau']['media'])} | {f(100*r['regioes']['sucessor']['media'],1)}% | {f(r['linhas']['tau']['media'])} |")
    out += ["", "A projeção por mediana pode esconder texto interrompido: computou-se também a fração de regiões-ouro cujas palavras reaparecem em mais de um trecho da sequência real (ignorando palavras sem dono).", "",
            "| Método | Regiões fragmentadas (média por página) | τ somente linhas de texto | Sucessor somente linhas de texto |",
            "|---|---:|---:|---:|"]
    for m in principais:
        out.append(f"| {NOMES[m]} | {f(100*S[m]['fragmentacao_media'],1)}% | {cel(S[m]['linhas_texto']['tau'])} | {cel(S[m]['linhas_texto']['sucessor'],True)} |")
    out += ["", "‘Somente texto’ exclui tabelas/figuras humanas, mas inclui títulos, listas, assinaturas e margens; evita que muitas linhas de uma tabela dominem a interpretação da continuidade.", "",
            "### Teste da hipótese local nas páginas inspecionadas", "",
            "As duas configurações abaixo têm os mesmos score, vão e limiar de vale. Mudam conjuntamente a votação em janelas e o critério de ponte; esta comparação não separa o efeito de cada componente e foi motivada pelos erros da amostra.", "",
            "| Página | τ regiões: perfil global → local | τ linhas: global → local | Sucessor de linhas: global → local |",
            "|---|---:|---:|---:|"]
    for e in R["hipotese_local"]:
        a, b = e["global"], e["local"]
        out.append(f"| `{e['page_id']}` | {f(a['regioes']['tau'])} → {f(b['regioes']['tau'])} | {f(a['linhas']['tau'])} → {f(b['linhas']['tau'])} | {f(100*a['linhas']['sucessor'],1)}% → {f(100*b['linhas']['sucessor'],1)}% |")
    out += ["", "No RJ, o rodapé contém outro arranjo de colunas: o perfil global não encontrou a calha do corpo e intercalou linhas; a versão local recuperou o corpo. No MA, ‘ARTIGOS’ começa dentro da calha mas pertence à coluna direita: tratá-lo como ponte interrompia a esquerda. São falhas da organização espacial que um detector de tabela/imagem sozinho não corrige.", "",
            "## Onde o plano perde mais", "",
            "Páginas ordenadas pela perda de τ de regiões do LOPO contra a referência. Diagnósticos abaixo são evidência geométrica e contrafactual, não rótulos causais anotados.", "",
            "| Página (`page_id`, índice de página do arquivo) | Colunas | τ referência → plano | Δ τ | Sucessor ref. → plano | τ com átomos-ouro |",
            "|---|---:|---:|---:|---:|---:|"]
    for e in R["piores"]:
        out.append(f"| `{e['page_id']}` | {e['colunas']} | {f(e['referencia']['regioes']['tau'])} → {f(e['plano']['regioes']['tau'])} | {f(e['delta_tau'])} | {f(100*e['referencia']['regioes']['sucessor'],1)}% → {f(100*e['plano']['regioes']['sucessor'],1)}% | {f(e['oraculo']['regioes']['tau'])} |")
    out += ["", "A régua de regiões dá peso igual a páginas com poucas caixas e a páginas com muito texto. Por isso as trocas de campos no cabeçalho de AC/MS aparecem entre as maiores perdas, embora o corpo da tabela esteja correto. Para não esconder falhas no conteúdo, seguem também os maiores recuos nas réguas de linhas (união dos maiores recuos de τ e de sucessor).", "",
            "| Página | Regiões / linhas-ouro | τ linhas: ref. → plano | Sucessor de linhas: ref. → plano | τ linhas com átomos-ouro |",
            "|---|---:|---:|---:|---:|"]
    for e in R["piores_linhas"]:
        out.append(f"| `{e['page_id']}` | {e['n_regioes']} / {e['n_linhas']} | {f(e['referencia']['linhas']['tau'])} → {f(e['plano']['linhas']['tau'])} | {f(100*e['referencia']['linhas']['sucessor'],1)}% → {f(100*e['plano']['linhas']['sucessor'],1)}% | {f(e['oraculo']['linhas']['tau'])} |")
    analisados = {e["page_id"]: e for e in R["piores"] + R["piores_linhas"]}
    for e in analisados.values():
        d = e["diagnostico"]
        out += ["", f"### `{e['page_id']}`", "",
                f"Configuração: `{e['config']}`. Das {d['inversoes']} inversões entre regiões, {d['inversoes_com_margem_ou_marca']} envolvem cabeçalho, rodapé ou marca. O oráculo tabela/imagem muda τ em {f(d['delta_oraculo_tau'])}. Cobertura dos átomos humanos por um único átomo detectado da mesma classe: " + ("; ".join(f"{x['id']} ({x['classe']}): {f(100*x['cobertura_palavras'],1)}%" for x in d["atomos_ouro"]) or "não há tabela/imagem humana") + ".",
                "Regiões mais deslocadas (posições começam em zero):", ""]
        for b in d["deslocados"][:3]:
            out.append(f"- `{b['id']}` ({b['classe']}), ouro {b['pos_ouro']} → predição {b['pos_pred']}: “{b['texto'].replace('|','/').replace(chr(10),' ')}”.")
        nota = R.get("notas_inspecao", {}).get(e["page_id"])
        if nota:
            out += ["", nota]
    out += ["", "## O que um detector de três classes resolveria", "",
            f"Mantendo a configuração LOPO e substituindo apenas os átomos detectados pelas caixas humanas de tabela/imagem, o τ em regiões vai de {f(S['plano_cv']['regioes']['tau']['media'])} para {f(S['oraculo_ti']['regioes']['tau']['media'])}; o sucessor vai de {f(100*S['plano_cv']['regioes']['sucessor']['media'],1)}% para {f(100*S['oraculo_ti']['regioes']['sucessor']['media'],1)}%. Em linhas, τ vai de {f(S['plano_cv']['linhas']['tau']['media'])} para {f(S['oraculo_ti']['linhas']['tau']['media'])}. O contrafactual também remove falsos positivos de tabela/imagem e pode alterar as colunas; não é um teto matemático e não simula um detector treinado.", "",
            "Uma detecção melhor pode preservar tabelas que hoje viram texto, evitar que fotos/logos absorvam palavras externas e corrigir a caixa de um átomo que bloqueia uma calha. Ela não decide a continuidade entre colunas, não reconhece sozinha título que atravessa colunas, não distingue cabeçalho/rodapé do texto com apenas essas três classes e não fornece OCR, ordem de células, legenda associada ou semântica do ato. A classe ‘texto’ não foi usada como bbox de região neste plano: usar caixas textuais previstas seria outra variante de segmentação.", "",
            "O diagnóstico usa somente átomos que ficaram no Golden com texto: imagens puras, mesmo corretamente detectadas, somem no contrafactual. Além disso, caixas humanas podem ser mais justas às palavras do que a borda visual da tabela. Logo, o oráculo não simula uma taxonomia de três classes perfeita. Sua queda em τ de regiões reforça que bordas e política de colunas/margens interagem: melhorar detecção não garante melhora monótona da ordenação.", "",
            "## Limitações e recomendação", "",
            "- Amostra pequena e de conveniência: páginas já anotadas do piloto/treino Diamond, mesmo anotador e famílias de layout repetidas. Bootstrap por página não modela dependência por veículo; seus intervalos podem ser estreitos demais.",
            "- Ouro de linhas derivado das regiões, sem anotação humana independente dentro delas. Linhas de tabela usam topo→base/esquerda→direita; este experimento mede a posição da tabela e essa expansão, não sua estrutura semântica. Imagens sem texto foram retiradas ao montar o Golden e sua posição não pode ser avaliada aqui.",
            "- Caixas Diamond partiram de propostas automáticas corrigidas, com possível ancoragem na granularidade original. A referência em regiões tem segmentação humana disponível, ao contrário dos métodos automáticos. Não atribuir toda diferença apenas ao algoritmo de ordenação.",
            "- Medianas apagam intercalações dentro das regiões e linhas. A fragmentação complementar revela parte delas, mas não avalia palavra por palavra, OCR, fidelidade de frases nem impacto em RI.",
            "- Parâmetros e desenvolvimento exploratórios sobre estas páginas; LOPO por página não equivale a teste novo por veículo. Os p-valores da melhor variante na amostra são especialmente otimistas, e a correção Holm não corrige a exploração de algoritmos.",
            "- Cache Docling truncado em score 0,45, somente PDFs com camada de texto; não se avaliou modelo de três classes treinado, imagem pura ou custo do detector. Não é um experimento de latência nem comparação de treinamento entre taxonomias.", "",
            "**Recomendação:** sim, vale seguir o plano como uma alternativa ao extrator fino, **com projeção local, políticas de margens e átomos que respeitem colunas**. O protótipo melhora a média global de τ nas duas réguas, mas a continuidade local não apresenta melhora inequívoca e o estrato multicoluna perde em regiões. Antes de adotá-lo, testar em páginas novas desenhadas/anotadas sem proposta e separar veículos para desenvolvimento/teste; exigir continuidade de linhas e regiões junto com τ; validar tabela/imagem e políticas de margens. Manter o comparador de regiões finas no TCC e não apresentar este ganho exploratório como prova de que três classes bastam em todo layout.", "",
            "## Reprodução", "", "```powershell", "$env:PYTHONIOENCODING='utf-8'",
            "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox.py", "```", "",
            f"Execução determinística; bootstrap com {R['bootstrap']['reamostras']} reamostras e semente {R['bootstrap']['semente']}. JSON contém hashes, configurações, métricas por página, ordens projetadas e sequências de linhas/átomos das variantes selecionadas. O Markdown é gerado diretamente desses resultados.", ""]
    return "\n".join(out)


# Notas qualitativas sao preenchidas apos inspecao das paginas, sem alterar as predicoes.
NOTAS_INSPECAO = {
    "official_diary_ac/executive_official_diary_2022-08-03.pdf#p109":
        "**Inspeção:** tabela larga bem delimitada, sem intercalação no corpo. A falha está na ordem dos campos da faixa superior: a bbox de ‘DIÁRIO OFICIAL 110’ começa mais acima e esse campo é lido antes do campo esquerdo, embora pertençam à mesma faixa visual. A política de margens separa cabeçalho/corpo, mas ainda ordena seus fragmentos por topo exato. Um detector melhor de tabela não resolve essa tolerância vertical. A perda em regiões é grande porque há poucas regiões, enquanto a régua de linhas permanece quase perfeita.",
    "official_diary_ms/executive_official_diary_46741_2021-06-29.pdf#p48":
        "**Inspeção:** campos do cabeçalho na mesma faixa visual, tabela única no corpo. Pequenas diferenças subpontuais de topo nas palavras colocam data e página antes do nome do diário. As caixas arredondadas do ouro empatam nesse topo e a referência as lê da esquerda para a direita. O corpo e a tabela não são a causa: é preciso agrupar campos por faixa com tolerância, sem depender de uma classe fina para cada um.",
    "official_diary_am_manaus/2023-03-13_caderno_2.pdf#p22":
        "**Inspeção:** duas tabelas lado a lado, ambas integralmente detectadas. Na configuração escolhida ao deixar esta página de fora, não há política de margens; cabeçalho e rodapé centralizados bloqueiam o corte vertical, não há linhas suficientes para o perfil e o fallback desempata pelo topo. A tabela direita começa ligeiramente acima e vem antes da esquerda. O oráculo corrige a ordem ao usar caixas ajustadas/arredondadas: isso não significa que a tabela estivesse ausente. A alta continuidade de linhas dentro dos átomos convive com a inversão de quase todo o conteúdo da página.",
    "official_diary_ms/executive_official_diary_48733_2024-11-05.pdf#p233":
        "**Inspeção:** o detector gera uma tabela estreita à esquerda e outra larga que absorve parte do cabeçalho. A atribuição à menor tabela reparte as palavras de uma única tabela humana; o cabeçalho absorvido participa do átomo e sua mediana muda a ordem dos campos. Melhor delimitação/instanciamento ajudaria, mas o oráculo ainda perde por ordenar campos do topo por coordenadas exatas. Não atribuir esta perda só a coluna mal detectada.",
    "official_diary_RJ_barra_do_pirai/executive_official_diary_2022-05-26_095.pdf#p2":
        "**Inspeção:** sumário e cartaz, sem corpo de jornal em colunas. As imagens puras não têm texto no ouro. No rodapé, o nome do município, a página e a autenticação ocupam campos lado a lado, mas a autenticação tem várias linhas. O fluxo por linhas intercala esses campos; a política de fim da página não preserva a unidade de cada campo. Três classes não distinguem nem agrupam esses rodapés. O `stats.n_colunas` decorre dos campos laterais e não descreve o corpo.",
    "official_diary_RJ_barra_do_pirai/executive_official_diary_2026-01-16_010.pdf#p2":
        "**Inspeção:** repete o arranjo de sumário/cartaz e campos no rodapé de Barra do Piraí. A autenticação é interrompida pelo número da página e pelo nome do município. Imagens são corretamente tratadas como átomos sem texto, mas sua posição não é avaliável pelo Golden; o erro medido vem da organização dos fragmentos textuais do rodapé.",
    "official_diary_pb/Diario Oficial 10-01-2026 Portal.pdf#p26":
        "**Inspeção:** tabelas em duas colunas visuais, embora o estrato fornecido seja uma coluna. A escolha LOPO também removeu a política de margens nesta página. O cabeçalho atravessa a calha e o perfil não a resolve; caixas de tabelas à direita começam ligeiramente acima das correspondentes à esquerda e o fallback intercala partes das colunas. Caixas humanas reduzem a perda de linhas, mas não resolvem toda a ordenação. A necessidade principal é organização de faixas/colunas e desempate estável entre átomos, além de qualidade das bordas.",
    "official_diary_RJ_duque_de_caxias/executive_official_diary_2022-09-28_Boletim_7197.pdf#p44":
        "**Inspeção:** tabelas independentes lado a lado. O detector propõe tanto caixas por coluna quanto caixas que englobam as duas tabelas; uma caixa larga remanescente recebe palavras dos dois lados. Sua expansão interna por linhas intercala as tabelas, derrubando a continuidade mesmo quando a projeção por mediana acerta boa parte das regiões. Aqui um detector de três classes com melhor **delimitação de instâncias** ajudaria diretamente; classificar como ‘tabela’ a caixa larga já é correto e não basta.",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--semente", type=int, default=42)
    args = ap.parse_args()
    assert args.bootstrap >= 2000
    antes = hashes()
    sinteticos = verificar_sinteticos()
    ps, amostra = preparar()
    cs = grade()
    regs = {m: [] for m in ("xy_ouro", "ingenua", "xy_auto")}
    vr = {c.id: [] for c in cs}
    for j, q in enumerate(ps):
        for m, r in baselines(q).items():
            regs[m].append(r)
        for c in cs:
            seq, _, diag = prever(q, c)
            r = avaliar_fluxo(q, seq)
            r["diag"].update(diag)
            vr[c.id].append(r)
        print(f"[página {j+1}/{len(ps)}] {q['p']['page_id']}", flush=True)
    taus = np.array([[r["regioes"]["tau"] for r in vr[c.id]] for c in cs])
    sucs = np.array([[r["regioes"]["sucessor"] for r in vr[c.id]] for c in cs])
    total_t, total_s = taus.sum(axis=1), sucs.sum(axis=1)
    def escolher(indices, excluir=None):
        return max(indices, key=lambda i: (total_t[i] - (taus[i, excluir] if excluir is not None else 0),
                                          total_s[i] - (sucs[i, excluir] if excluir is not None else 0), -i))
    best = escolher(range(len(cs)))
    cv_ids = [escolher(range(len(cs)), j) for j in range(len(ps))]
    regs["plano_melhor"] = vr[cs[best].id]
    regs["plano_cv"] = [vr[cs[i].id][j] for j, i in enumerate(cv_ids)]
    regs["oraculo_ti"] = []
    detalhes = []
    sequencias_melhor = []
    for j, (q, i) in enumerate(zip(ps, cv_ids)):
        c = cs[i]
        seq, items, _ = prever(q, c)
        osq, _, _ = prever(q, c, oraculo=True)
        oracle = avaliar_fluxo(q, osq)
        regs["oraculo_ti"].append(oracle)
        detalhes.append({"page_id": q["p"]["page_id"], "colunas": q["p"]["stats"]["n_colunas"],
                         "n_regioes": len(q["gt_r"]), "n_linhas": len(q["gt_l"]),
                         "config": c.id, "referencia": regs["xy_ouro"][j], "plano": regs["plano_cv"][j],
                         "oraculo": oracle,
                         "delta_tau": regs["plano_cv"][j]["regioes"]["tau"] - regs["xy_ouro"][j]["regioes"]["tau"],
                         "diagnostico": diagnostico(q, c, regs["plano_cv"][j], oracle, items),
                         "sequencia": [{"tipo": m["tipo"], "bbox": m["bbox"], "palavras": m["ks"],
                                        "texto": " ".join(q["ws"][k][0] for L in linhas(q["ws"], m["ks"]) for k in L["ks"])} for m in items]})
        _, melhores_items, _ = prever(q, cs[best])
        sequencias_melhor.append({"page_id": q["p"]["page_id"], "config": cs[best].id,
                                 "sequencia": [{"tipo": m["tipo"], "bbox": m["bbox"], "palavras": m["ks"],
                                                "texto": " ".join(q["ws"][k][0] for L in linhas(q["ws"], m["ks"]) for k in L["ks"])}
                                               for m in melhores_items]})
    indices = {"todas": list(range(len(ps))), "uma": [j for j, q in enumerate(ps) if q["p"]["stats"]["n_colunas"] == 1],
               "multi": [j for j, q in enumerate(ps) if q["p"]["stats"]["n_colunas"] > 1]}
    sumarios = {g: {m: resumo([rs[j] for j in inds], args.bootstrap, args.semente) for m, rs in regs.items()}
                for g, inds in indices.items()}
    auditoria = {k: sum(q["auditoria"][k] for q in ps) for k in ("palavras", "sem_regiao_ouro", "sobreposicao_ouro", "centros_fora_pagina")}
    auditoria.update(regioes=sum(len(q["gt_r"]) for q in ps), linhas=sum(len(q["gt_l"]) for q in ps),
                     textos_divergentes=sum(len(q["auditoria"]["texto_divergente"]) for q in ps), regioes_sem_palavras=0,
                     tokens_divergentes=sum(len(q["auditoria"]["tokens_divergentes"]) for q in ps),
                     fallback_auto=sum(r["diag"]["palavras_fallback"] for r in regs["xy_auto"]),
                     empates_cv_regioes=sum(r["diag"]["empates_regioes"] for r in regs["plano_cv"]),
                     empates_cv_linhas=sum(r["diag"]["empates_linhas"] for r in regs["plano_cv"]))
    def obj_melhor(inds):
        i = escolher(inds)
        return {"id": cs[i].id, "config": asdict(cs[i]), "resumo": resumo(vr[cs[i].id], args.bootstrap, args.semente)}
    piores_linhas = {}
    for m, n in (("tau", 4), ("sucessor", 2)):
        for e in sorted(detalhes, key=lambda e: e["plano"]["linhas"][m] - e["referencia"]["linhas"][m])[:n]:
            piores_linhas[e["page_id"]] = e
    hipotese_local = [{"page_id": q["p"]["page_id"],
                       "global": vr["projecao_margens_s0.45_g1.2_v0.08"][j],
                       "local": vr["projecao_local_margens_s0.45_g1.2_v0.08"][j]}
                      for j, q in enumerate(ps) if q["p"]["page_id"] in (
                          "official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1",
                          "official_diary_ma/executive_official_diary_2023-03-06.pdf#p71")]
    R = {"amostra": amostra, "auditoria": auditoria, "hashes": antes, "sinteticos": sinteticos,
         "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "bootstrap": {"reamostras": args.bootstrap, "semente": args.semente},
         "contagem_colunas": dict(collections.Counter(q["p"]["stats"]["n_colunas"] for q in ps)),
         "grade": [{"id": c.id, **asdict(c)} for c in cs],
         "grade_inicial": sum("local" not in c.abordagem for c in cs),
         "melhor_config": {"id": cs[best].id, **asdict(cs[best])},
         "selecao_cv": dict(collections.Counter(cs[i].id for i in cv_ids)),
         "resumo": sumarios,
         "testes": {m: testes(regs[m], regs["xy_ouro"], args.bootstrap, args.semente) for m in ("plano_cv", "plano_melhor")},
         "melhores_familias": {a: obj_melhor([i for i, c in enumerate(cs) if c.abordagem == a]) for a in sorted({c.abordagem for c in cs})},
         "melhores_scores": {str(s): obj_melhor([i for i, c in enumerate(cs) if c.score == s]) for s in sorted({c.score for c in cs})},
         "por_pagina": [{"page_id": q["p"]["page_id"], "auditoria": q["auditoria"],
                         "metodos": {m: rs[j] for m, rs in regs.items()},
                         "variantes": {c.id: vr[c.id][j] for c in cs}} for j, q in enumerate(ps)],
         "sequencias_cv": detalhes, "sequencias_melhor": sequencias_melhor,
         "piores": sorted(detalhes, key=lambda e: e["delta_tau"])[:6],
         "piores_linhas": list(piores_linhas.values()), "hipotese_local": hipotese_local,
         "notas_inspecao": NOTAS_INSPECAO}
    assert antes == hashes(), "Entradas ou fontes mudaram durante a execucao; nao gravar resultado."
    # Verificacao substantiva da reproducao pedida, sem substituir o valor medido.
    ref = sumarios["todas"]["xy_ouro"]["regioes"]
    assert round(ref["tau"]["media"], 3) == 0.825
    assert round(ref["sucessor"]["media"] * 100, 1) == 71.5
    SAIDA_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    # Reabrir o JSON garante que o Markdown e uma representacao do artefato salvo.
    salvo = json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
    md = relatorio(salvo)
    SAIDA_MD.write_text(md, encoding="utf-8")
    assert SAIDA_MD.read_text(encoding="utf-8") == relatorio(salvo)
    print("\nRégua de regiões:")
    print("\n".join(tabela(sumarios["todas"], list(regs), "regioes")))
    print("\nRégua de linhas:")
    print("\n".join(tabela(sumarios["todas"], list(regs), "linhas")))
    print("Melhor configuração:", cs[best].id, "| LOPO:", R["selecao_cv"])
    print("Auditoria:", auditoria)
    print("[OK] JSON relido, relatório conferido e hashes preservados.")


if __name__ == "__main__":
    main()
