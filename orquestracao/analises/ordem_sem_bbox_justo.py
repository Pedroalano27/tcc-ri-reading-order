"""Reanalisa de forma pareada a ordem sem caixas finas, sem defender o metodo.

Importa o experimento original, mas nao chama seu main nem seus carregadores
com assert para palavras ausentes. Usa somente CPU, caches locais e palavras
ja extraidas; nao abre PDFs, nao carrega modelos e nao escreve em data/.

Unicas saidas novas: este script e resultados/ordem_sem_bbox_justo.md. Para
retomar apos queda sem criar outro arquivo, o proprio Markdown guarda um
checkpoint comprimido em comentario HTML, com hashes e metricas por pagina.
Ele e atualizado apos cada pagina; numeros parciais ja ficam legiveis.

Uso na raiz: venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_justo.py
Recalcular sem cache: acrescentar --do-zero. Conferir: acrescentar --conferir.
Comentarios/docstrings sem acento seguem a convencao do repositorio.
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
import itertools
import json
import math
import os
import re
import statistics
import zlib
import numpy as np
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o

SAIDA = RAIZ / "resultados/ordem_sem_bbox_justo.md"
ORIGINAL = RAIZ / "resultados/ordem_sem_bbox.json"
MARCADOR = "ORDEM_SEM_BBOX_JUSTO_CHECKPOINT_V1"
REGUAS = ("regioes", "linhas", "palavras")
ROTULO_REGUA = {"regioes": "regiões", "linhas": "linhas", "palavras": "palavras"}
METRICAS = ("tau", "sucessor", "ard")
FAMILIAS = ("xy_linhas", "xy_margens", "projecao_local", "projecao_local_margens")
NOMES = {
    "xy_ouro": "XY-cut ouro, pura",
    "xy_ouro_geo": "XY-cut ouro + margens geométricas",
    "xy_ouro_classe": "XY-cut ouro + classes humanas de margem†",
    "xy_auto": "XY-cut automática, pura",
    "xy_auto_geo": "XY-cut automática + margens geométricas",
    "xy_auto_classe": "XY-cut automática + classes previstas de margem",
    "ing_ouro": "Ingênua ouro, pura",
    "ing_ouro_geo": "Ingênua ouro + margens geométricas",
    "ing_auto": "Ingênua automática, pura",
    "ing_auto_geo": "Ingênua automática + margens geométricas",
    "original_lopo": "Plano original, LOPO / seleção por τ de regiões",
    "original_lovo": "Plano original, LOVO / seleção por τ de regiões",
    "plano_lovo": "Plano LOVO / seleção por τ de palavras",
    "oraculo_lovo": "Plano LOVO + tabela/imagem humana†",
    "oraculo_lopo": "Plano original LOPO + tabela/imagem humana†",
    "ab_xy_sem": "XY-cut de linhas, sem margens (2×2)",
    "ab_xy_com": "XY-cut de linhas, com margens (2×2)",
    "ab_proj_sem": "Projeção local, sem margens (2×2)",
    "ab_proj_com": "Projeção local, com margens (2×2)",
    "sens_xy_linhas": "XY-cut de linhas sem margens (seleção própria)",
    "sens_xy_margens": "XY-cut de linhas com margens (seleção própria)",
    "sens_projecao_local": "Projeção local sem margens (seleção própria)",
    "sens_projecao_local_margens": "Projeção local com margens (seleção própria)",
}
BASES = tuple(k for k in NOMES if k.startswith(("xy_", "ing_")))
AB = ("ab_xy_sem", "ab_xy_com", "ab_proj_sem", "ab_proj_com")
PRINCIPAIS = BASES + ("plano_lovo", "original_lopo", "original_lovo")


def ler_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def hashes():
    caminhos = o.ENTRADAS + o.FONTES + [Path(o.__file__), Path(__file__), ORIGINAL,
        RAIZ / "resultados/ordem_sem_bbox.md", RAIZ / "resultados/revisao_ordem_sem_bbox.md"]
    return {p.relative_to(RAIZ).as_posix(): digest(p) for p in caminhos}


def preparar():
    """Mesmas paginas concluidas; caixas vazias recebem diagnostico explicito."""
    tarefas = {p["page_id"]: p for p in ler_jsonl(o.ENTRADAS[0])}
    anns = {a["page_id"]: a for a in ler_jsonl(o.ENTRADAS[1]) if a.get("status") == "concluida"}
    ds = {l: {p["page_id"]: p for p in ler_jsonl(RAIZ / f"data/diamond/{l}/tarefas.jsonl")}
          for l in ("diamond_piloto", "diamond_treino")}
    ps = []
    for pid, a in sorted(anns.items()):
        p = tarefas[pid]
        d = ds[p["origem"]][pid]
        if p["dimensions"] != d["dimensions"]:
            raise ValueError(f"Dimensões diferentes: {pid}")
        rs, ws = p["bounding_boxes"], d.get("palavras", [])
        if len(a["ordem"]) != len(rs) or set(a["ordem"]) != {r["id"] for r in rs}:
            raise ValueError(f"Ordem humana não é permutação completa: {pid}")
        kws, livres, amb = o.donos(ws, rs)
        por_r, por_l, ls = {}, {}, []
        for r, ks in zip(rs, kws):
            rid = r["id"]
            por_r[rid] = ks
            por_l[rid] = []
            for i, L in enumerate(o.linhas(ws, ks)):
                lid = f"{rid}:l{i}"
                por_l[rid].append(lid)
                ls.append({"id": lid, "regiao": rid, "ks": L["ks"], "bbox": L["bbox"]})
        gt_l = [lid for rid in a["ordem"] for lid in por_l[rid]]
        por_id = {L["id"]: L for L in ls}
        gt_w = [k for lid in gt_l for k in por_id[lid]["ks"]]
        ps.append({"p": p, "d": d, "ws": ws, "gt_r": a["ordem"], "gt_l": gt_l,
                   "gt_w": gt_w, "reg_words": por_r, "gold_lines": ls,
                   "h": statistics.median(w[4] - w[2] for w in ws) if ws else 10.0,
                   "auditoria": {"palavras": len(ws), "sem_ouro": len(livres), "ambiguas": amb,
                                  "regioes_vazias": sum(not ks for ks in kws),
                                  "sem_palavras": int(not ws),
                                  "visuais_retiradas": p.get("diamond", {}).get("regioes_sem_texto", 0)}})
    if len(ps) != 44:
        raise ValueError(f"O estudo solicitado exige 44 páginas; há {len(ps)}")
    return ps


def metricas(pred, gt):
    if len(pred) != len(gt) or set(pred) != set(gt):
        raise ValueError("Sequências avaliadas não são permutações dos mesmos IDs")
    if len(gt) < 2:
        return dict.fromkeys(METRICAS, None)
    return {"tau": o.kendall_tau(pred, gt), "sucessor": o.acerto_sucessor(pred, gt),
            "ard": o.ard_normalizado(pred, gt)}


def avaliar(q, seq, ordem_regioes=None):
    """Tau de palavras usa a saida real; mediana fica so como regua secundaria."""
    if len(seq) != len(set(seq)) or any(k < 0 or k >= len(q["ws"]) for k in seq):
        raise ValueError("Predição com palavras duplicadas ou IDs inválidos")
    rank = {k: i for i, k in enumerate(seq)}
    elegiveis = set(q["gt_w"])
    pw = [k for k in seq if k in elegiveis]
    if set(pw) != elegiveis:
        raise ValueError("Predição perdeu palavras com referência")
    rbox = {r["id"]: r["bbox"] for r in q["p"]["bounding_boxes"]}
    rr = {}
    vazias = []
    for rid, ks in q["reg_words"].items():
        if ks:
            rr[rid] = statistics.median(rank[k] for k in ks)
        else:
            vazias.append(rid)
            b = rbox[rid]
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            proximo = min(seq, key=lambda k: ((o.centro(q["ws"][k])[0] - cx)**2 +
                                            (o.centro(q["ws"][k])[1] - cy)**2, k), default=None)
            rr[rid] = rank[proximo] if proximo is not None else b[1]
    pr = ordem_regioes if ordem_regioes is not None else sorted(
        rr, key=lambda rid: (rr[rid], rbox[rid][1], rbox[rid][0], rid))
    lr = {L["id"]: statistics.median(rank[k] for k in L["ks"]) for L in q["gold_lines"]}
    lbox = {L["id"]: L["bbox"] for L in q["gold_lines"]}
    pl = sorted(lr, key=lambda lid: (lr[lid], lbox[lid][1], lbox[lid][0], lid))
    dono = {k: rid for rid, ks in q["reg_words"].items() for k in ks}
    def contar(fluxo):
        runs = collections.Counter()
        anterior = object()
        for k in fluxo:
            atual = dono.get(k)
            if atual != anterior and atual is not None:
                runs[atual] += 1
            anterior = atual
        return {rid: n for rid, n in runs.items() if n > 1}
    fragmentadas = contar(pw)
    estritas = contar(seq)
    nr = sum(bool(ks) for ks in q["reg_words"].values())
    return {"regioes": metricas(pr, q["gt_r"]), "linhas": metricas(pl, q["gt_l"]),
            "palavras": metricas(pw, q["gt_w"]),
            "diag": {"fragmentadas": fragmentadas, "fragmentadas_estritas": estritas,
                     "fracao": len(fragmentadas) / nr if nr else None,
                     "fracao_estrita": len(estritas) / nr if nr else None,
                     "mediana_perfeita_fragmentada": bool(fragmentadas and list(pr) == q["gt_r"]),
                     "regioes_sem_palavras": vazias, "palavras_avaliadas": len(pw),
                     "palavras_fora_ouro": len(seq) - len(pw)}}


def particao(items, ws, H, politica):
    """Mesma precedencia/regex/limiares do original; classe troca apenas margens."""
    ini, corpo, marcas, fim = [], [], [], []
    for i, m in enumerate(items):
        b = m["bbox"]
        cy = (b[1] + b[3]) / 2
        if politica and m["ks"] and all(o.RE_MARCACAO.match(ws[k][0]) for k in m["ks"]):
            marcas.append(i)
        elif politica == "geo" and cy < 0.07 * H and b[3] < 0.10 * H:
            ini.append(i)
        elif politica == "classe" and m.get("tipo") == "cabecalho":
            ini.append(i)
        elif politica == "geo" and cy > 0.95 * H:
            fim.append(i)
        elif politica == "classe" and m.get("tipo") == "rodape":
            fim.append(i)
        else:
            corpo.append(i)
    return ini, corpo, marcas, fim


def baselines(q):
    saida = {}
    for origem in ("ouro", "auto"):
        rs = q["p"]["bounding_boxes"] if origem == "ouro" else o.propor(
            q["ws"], q["d"].get("blocos_v3", []), q["d"].get("detector", {}).get("regioes", []), regras=True)
        kws, livres, _ = o.donos(q["ws"], rs)
        items = [{"bbox": r["bbox"], "ks": ks, "tipo": r.get("classe"), "id": r.get("id", str(i))}
                 for i, (r, ks) in enumerate(zip(rs, kws))]
        bs = o.boxes(items)
        chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
        for algoritmo, politica in (("xy", None), ("xy", "geo"), ("xy", "classe"), ("ing", None), ("ing", "geo")):
            ini, corpo, marcas, fim = particao(items, q["ws"], q["p"]["dimensions"]["height"], politica)
            ordem = o.xycut(corpo, bs) if algoritmo == "xy" else sorted(corpo, key=chave)
            ordem = sorted(ini, key=chave) + ordem + sorted(marcas, key=chave) + sorted(fim, key=chave)
            seq = o.fluxo([items[i] for i in ordem], q["ws"])
            seq += [k for L in o.linhas(q["ws"], livres) for k in L["ks"]]
            rid = [items[i]["id"] for i in ordem] if origem == "ouro" else None
            nome = f"{algoritmo}_{origem}" + (f"_{politica}" if politica else "")
            saida[nome] = avaliar(q, seq, rid)
            saida[nome]["diag"].update(regioes_previstas=len(rs), fallback=len(livres),
                topo=len(ini), rodape=len(fim), marcas=len(marcas))
            if origem == "ouro" and politica is None:
                armazenada = q["p"]["ordens"]["xycut" if algoritmo == "xy" else "naive"]
                if rid != armazenada:
                    raise ValueError(f"Baseline difere da armazenada: {q['p']['page_id']}")
    return saida


def colunas(q):
    """Criterio fixo sem ouro: calhas recorrentes no corpo, a partir de palavras."""
    H = q["p"]["dimensions"]["height"]
    ks = [k for k, w in enumerate(q["ws"]) if 0.10 * H <= o.centro(w)[1] <= 0.95 * H
          and not o.RE_MARCACAO.match(w[0])]
    items = o.linhas_partidas(q["ws"], ks, 1.2, q["h"])
    ids = list(range(len(items)))
    cortes = o.vales_locais(items, ids, q["h"], 0.08)
    if not cortes:
        cortes = o.vales(items, ids, q["h"], 0.08)
    return {"n": len(cortes) + 1, "cortes": cortes, "fragmentos": len(items),
            "antigo": q["p"].get("stats", {}).get("n_colunas"),
            "imagem": q["p"].get("imagem"), "largura": q["p"]["dimensions"]["width"]}


def checkpoint(R):
    raw = json.dumps(R, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return f"\n<!-- {MARCADOR}\n{base64.b64encode(zlib.compress(raw, 9)).decode('ascii')}\n-->\n"


def carregar_cache(H):
    if not SAIDA.exists():
        return None
    try:
        s = SAIDA.read_text(encoding="utf-8")
        m = re.search(rf"<!-- {MARCADOR}\n([A-Za-z0-9+/=]+)\n-->", s)
        R = json.loads(zlib.decompress(base64.b64decode(m.group(1))).decode("utf-8")) if m else None
        return R if R and R["hashes"] == H else None
    except (ValueError, zlib.error, AttributeError):
        return None


def gravar(texto, R):
    with SAIDA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(texto + checkpoint(R))
        f.flush()
        os.fsync(f.fileno())


def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def parcial(R):
    rows = R["paginas"]
    vals = [p["bases"]["xy_ouro"]["regioes"]["tau"] for p in rows]
    return ("# Reanálise justa — execução parcial\n\n"
            f"Páginas concluídas: {len(rows)}. XY-cut ouro, τ médio parcial = {f(statistics.mean(vals)) if vals else '—'}.\n\n"
            "Ainda não há veredito: seleção e inferência aguardam todas as páginas. "
            "O comentário no fim guarda o checkpoint para retomada.\n")


def matrizes(rows, cs, regua, metrica):
    return np.array([[p["variantes"][c.id][regua][metrica] if p["variantes"][c.id][regua][metrica] is not None
                      else np.nan for p in rows] for c in cs])


def escolher(T, U, candidatos, pesos):
    """Mesmo desempate: tau, sucessor, primeira configuracao da grade."""
    return max(candidatos, key=lambda i: (float(np.nansum(T[i] * pesos)),
                                         float(np.nansum(U[i] * pesos)), -i))


def selecao(rows, cs):
    grupos = np.array([p["veiculo"] for p in rows])
    T, U = matrizes(rows, cs, "regioes", "tau"), matrizes(rows, cs, "regioes", "sucessor")
    W, V = matrizes(rows, cs, "palavras", "tau"), matrizes(rows, cs, "palavras", "sucessor")
    familias = {a: [i for i, c in enumerate(cs) if c.abordagem == a] for a in FAMILIAS}
    todos = sum(familias.values(), [])
    parametros = list(itertools.product((0.45, 0.65, 0.85), (1.2, 2.0), (0.08, 0.20)))
    def index(a, s, g, v):
        return next(i for i, c in enumerate(cs) if c.abordagem == a and c.score == s and c.gap == g
                    and (not a.startswith("projecao") or c.vale == v))
    bracos = np.array([[index(a, s, g, v) for a in FAMILIAS] for s, g, v in parametros])
    TW, UV = np.nanmean(W[bracos], axis=1), np.nanmean(V[bracos], axis=1)
    ids = collections.defaultdict(list)
    for j in range(len(rows)):
        pesos = (grupos != grupos[j]).astype(float)
        pp = np.ones(len(rows)); pp[j] = 0
        ids["original_lopo"].append(escolher(T, U, range(len(cs)), pp))
        ids["original_lovo"].append(escolher(T, U, range(len(cs)), pesos))
        ids["plano_lovo"].append(escolher(W, V, todos, pesos))
        h = escolher(TW, UV, range(len(parametros)), pesos)
        for a, i in zip(AB, bracos[h]):
            ids[a].append(int(i))
        for a, cand in familias.items():
            ids["sens_" + a].append(escolher(W, V, cand, pesos))
    specs = {"original_lovo": {"T": T, "U": U, "cand": list(range(len(cs))), "map": np.arange(len(cs))},
             "plano_lovo": {"T": W, "U": V, "cand": todos, "map": np.arange(len(cs))},
             "comum": {"T": TW, "U": UV, "cand": list(range(len(parametros))), "map": bracos}}
    for a, cand in familias.items():
        specs["sens_" + a] = {"T": W, "U": V, "cand": cand, "map": np.arange(len(cs))}
    return dict(ids), specs, bracos


def boot_indices(rows, nboot, seed):
    grupos = sorted({p["veiculo"] for p in rows})
    gi = np.array([grupos.index(p["veiculo"]) for p in rows])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(grupos), (nboot, len(grupos)))
    contagens = np.stack([(draws == g).sum(axis=1) for g in range(len(grupos))], axis=1)
    return grupos, gi, contagens


def bootstrap_selecao(spec, gi, counts):
    """Refaz LOVO dentro de cada reamostra; exclui todas as copias do veiculo."""
    T, U = spec["T"], spec["U"]
    cand = np.array(spec["cand"])
    saida = np.zeros((len(counts), len(gi)), dtype=int)
    for g in range(counts.shape[1]):
        pesos = counts[:, gi].astype(float)
        pesos[:, gi == g] = 0
        st = pesos @ np.nan_to_num(T[cand]).T
        su = pesos @ np.nan_to_num(U[cand]).T
        bons = np.isclose(st, st.max(axis=1, keepdims=True), atol=1e-12, rtol=0)
        su = np.where(bons, su, -np.inf)
        bons &= np.isclose(su, su.max(axis=1, keepdims=True), atol=1e-12, rtol=0)
        # cand pode estar fora de ordem; desempate final e sempre indice da grade.
        escolhidos = np.min(np.where(bons, cand[None, :], len(T)), axis=1)
        saida[:, gi == g] = escolhidos[:, None]
    return saida


def media_boot(v, pesos):
    validos = np.isfinite(v)
    num = (np.nan_to_num(v) * pesos).sum(axis=1)
    den = (validos * pesos).sum(axis=1)
    return np.divide(num, den, out=np.full(len(pesos), np.nan), where=den > 0)


def agregar(rows, metodos, cs, ids, specs, nboot, seed):
    grupos, gi, counts = boot_indices(rows, nboot, seed)
    pesos = counts[:, gi]
    selecionados = {nome: bootstrap_selecao(spec, gi, counts) for nome, spec in specs.items()}
    C = selecionados.pop("comum")
    for a, nome in enumerate(AB):
        selecionados[nome] = specs["comum"]["map"][C, a]
    S, B = {}, {}
    for nome, regs in metodos.items():
        S[nome], B[nome] = {}, {}
        for regua in REGUAS:
            S[nome][regua], B[nome][regua] = {}, {}
            for m in METRICAS:
                v = np.array([r[regua][m] if r[regua][m] is not None else np.nan for r in regs])
                if nome in selecionados:
                    M = matrizes(rows, cs, regua, m)
                    draws = M[selecionados[nome], np.arange(len(rows))[None, :]]
                else:
                    # LOPO e oraculos: IC agrupado condicional, explicitamente identificado.
                    draws = np.broadcast_to(v, pesos.shape)
                b = media_boot(draws, pesos)
                B[nome][regua][m] = b
                fin = b[np.isfinite(b)]
                S[nome][regua][m] = {"media": float(np.nanmean(v)) if np.isfinite(v).any() else None,
                    "ic95": np.quantile(fin, [0.025, 0.975]).tolist() if len(fin) else [None, None],
                    "n": int(np.isfinite(v).sum()), "bootstrap_selecao": nome in selecionados}
        S[nome]["fragmentacao"] = statistics.mean(r["diag"]["fracao"] for r in regs if r["diag"]["fracao"] is not None)
    return S, B, grupos, gi


def teste_pratt(d):
    d = np.round(np.asarray(d, dtype=float), 12)
    d = d[np.isfinite(d)]
    if not len(d) or np.all(d == 0):
        return 1.0
    return float(wilcoxon(d, zero_method="pratt", alternative="two-sided", method="approx").pvalue)


def permutacao(d, gi, nperm, seed):
    """Troca de sinal simultanea por veiculo; zeros permanecem na amostra."""
    soma = np.array([d[gi == g].sum() for g in sorted(set(gi))])
    ativo = soma[np.abs(soma) > 1e-12]
    observado = abs(soma.sum())
    if not len(ativo):
        return {"p": 1.0, "exato": True, "reamostras": 1, "grupos_ativos": 0}
    exato = len(ativo) <= 18
    total = 2 ** len(ativo) if exato else nperm
    rng = np.random.default_rng(seed)
    extremos = 0
    for ini in range(0, total, 4096):
        n = min(4096, total - ini)
        signs = (((np.arange(ini, ini + n, dtype=np.uint64)[:, None] >>
                   np.arange(len(ativo), dtype=np.uint64)[None, :]) & 1) * 2.0 - 1) if exato else rng.integers(0, 2, (n, len(ativo))) * 2 - 1
        extremos += int((np.abs(signs @ ativo) >= observado - 1e-12).sum())
    return {"p": extremos / total if exato else (extremos + 1) / (total + 1),
            "exato": exato, "reamostras": total, "grupos_ativos": len(ativo)}


def testes(metodos, B, gi, nperm, seed):
    contrastes = [("plano_lovo", "xy_ouro_geo"), ("plano_lovo", "xy_auto_geo"),
                 ("ab_proj_com", "ab_xy_com"), ("ab_proj_sem", "ab_xy_sem"),
                 ("xy_ouro_geo", "xy_ouro"), ("xy_auto_geo", "xy_auto"),
                 ("original_lopo", "xy_ouro"), ("original_lovo", "xy_ouro"),
                 ("original_lovo", "xy_ouro_geo")]
    out = []
    for a, b in contrastes:
        for regua, m in [(r, "tau") for r in REGUAS] + [("linhas", "sucessor"), ("palavras", "sucessor")]:
            d = np.array([x[regua][m] - y[regua][m] for x, y in zip(metodos[a], metodos[b])])
            bd = B[a][regua][m] - B[b][regua][m]
            perm = permutacao(d, gi, nperm, seed)
            out.append({"a": a, "b": b, "regua": regua, "metrica": m,
                        "delta": float(d.mean()), "ic95": np.quantile(bd, [0.025, 0.975]).tolist(),
                        "p_pratt_paginas": teste_pratt(d),
                        "p_pratt_veiculos": teste_pratt([d[gi == g].mean() for g in sorted(set(gi))]),
                        "permutacao": perm,
                        "ganha": int((d > 1e-12).sum()), "empata": int((abs(d) <= 1e-12).sum()),
                        "perde": int((d < -1e-12).sum())})
    anterior = 0
    for i, t in enumerate(sorted(out, key=lambda x: x["permutacao"]["p"])):
        anterior = max(anterior, min(1, (len(out) - i) * t["permutacao"]["p"]))
        t["p_holm"] = anterior
    return out


def efeitos(S, B):
    """Efeitos fatoriais com parametros comuns, sem atribuir causalidade externa."""
    definicoes = {
        "politica_xy": {"ab_xy_com": 1, "ab_xy_sem": -1},
        "politica_projecao": {"ab_proj_com": 1, "ab_proj_sem": -1},
        "projecao_sem": {"ab_proj_sem": 1, "ab_xy_sem": -1},
        "projecao_com": {"ab_proj_com": 1, "ab_xy_com": -1},
        "interacao": {"ab_proj_com": 1, "ab_xy_com": -1, "ab_proj_sem": -1, "ab_xy_sem": 1},
        "media_politica": {"ab_xy_com": .5, "ab_xy_sem": -.5, "ab_proj_com": .5, "ab_proj_sem": -.5},
        "media_projecao": {"ab_proj_sem": .5, "ab_xy_sem": -.5, "ab_proj_com": .5, "ab_xy_com": -.5},
    }
    E = {}
    for nome, coefs in definicoes.items():
        E[nome] = {}
        for r in REGUAS:
            d = sum(v * S[k][r]["tau"]["media"] for k, v in coefs.items())
            b = sum(v * B[k][r]["tau"] for k, v in coefs.items())
            E[nome][r] = {"media": d, "ic95": np.quantile(b, [.025, .975]).tolist()}
    return E


def estratos(rows, metodos, nboot, seed):
    """Estratos fixos sem refazer selecao: IC exploratorios condicionais por grupo."""
    filtros = {"uma": lambda n: n == 1, "multi": lambda n: n > 1,
               "duas": lambda n: n == 2, "tres": lambda n: n == 3, "quatro": lambda n: n == 4}
    saida = {}
    for nome, filtro in filtros.items():
        ix = [i for i, p in enumerate(rows) if filtro(p["colunas"]["n"])]
        if not ix:
            continue
        _, _, counts = boot_indices([rows[i] for i in ix], nboot, seed)
        grupos = sorted({rows[i]["veiculo"] for i in ix})
        gi = np.array([grupos.index(rows[i]["veiculo"]) for i in ix])
        pesos = counts[:, gi]
        S = {}
        for m, regs in metodos.items():
            S[m] = {}
            for r in REGUAS:
                S[m][r] = {}
                for k in METRICAS:
                    v = np.array([regs[i][r][k] for i in ix], dtype=float)
                    b = media_boot(np.broadcast_to(v, pesos.shape), pesos)
                    S[m][r][k] = {"media": float(np.nanmean(v)), "ic95": np.quantile(b, [.025, .975]).tolist()}
            S[m]["fragmentacao"] = statistics.mean(regs[i]["diag"]["fracao"] for i in ix)
        saida[nome] = {"n": len(ix), "veiculos": len(grupos), "indices": ix, "resumos": S}
    return saida


def controles():
    """Casos de borda e contraprova da mediana, sem assert."""
    q = {"ws": [], "h": 10, "p": {"page_id": "sintetico/vazio", "dimensions": {"width": 400, "height": 842},
        "bounding_boxes": [{"id": "fig", "bbox": [10, 100, 50, 200], "classe": "figura"}]},
        "d": {"detector": {"regioes": []}}, "reg_words": {"fig": []}, "gold_lines": [],
        "gt_r": ["fig"], "gt_l": [], "gt_w": []}
    seq, _, _ = o.prever(q, o.Config("projecao_local_margens", 0.45, 1.2, 0.08))
    r = avaliar(q, seq)
    if seq or r["palavras"]["tau"] is not None or r["diag"]["regioes_sem_palavras"] != ["fig"]:
        raise ValueError("Controle de página vazia falhou")
    ws = [[str(k), 10 + (k >= 10) * 100, 100 + k % 10 * 10,
           18 + (k >= 10) * 100, 108 + k % 10 * 10, -1] for k in range(20)]
    q.update(ws=ws, gt_r=["a", "b", "fig"], gt_w=list(range(20)),
             reg_words={"a": list(range(10)), "b": list(range(10, 20)), "fig": []})
    q["p"]["bounding_boxes"] = [{"id": "a", "bbox": [10, 100, 18, 198]},
        {"id": "b", "bbox": [110, 100, 118, 198]}, {"id": "fig", "bbox": [250, 200, 300, 250]}]
    intercalada = [k for par in zip(range(10), range(10, 20)) for k in par]
    r = avaliar(q, intercalada)
    if len(r["diag"]["fragmentadas"]) != 2 or r["palavras"]["tau"] >= 1:
        raise ValueError("Controle de intercalação falhou")
    # Contraprova sem figura: a mediana e perfeita apesar da fragmentacao.
    q["gt_r"] = ["a", "b"]
    q["reg_words"].pop("fig")
    q["p"]["bounding_boxes"] = q["p"]["bounding_boxes"][:2]
    r = avaliar(q, intercalada)
    return {"pagina_vazia": True, "regiao_vazia": True,
            "intercalacao": {"tau_regioes": r["regioes"]["tau"], "tau_palavras": r["palavras"]["tau"],
                              "fracao_fragmentadas": r["diag"]["fracao"]}}


def cel(obj, percent=False):
    escala, n = (100, 1) if percent else (1, 3)
    a, b = obj["ic95"]
    return f"{f(obj['media'] * escala, n)}{'%' if percent else ''} [{f(a * escala, n)}; {f(b * escala, n)}]" if obj["media"] is not None else "—"


def tabela(S, nomes, regua):
    out = ["| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ | ARD normalizado ↓ |",
           "|---|---:|---:|---:|"]
    for nome in nomes:
        r = S[nome][regua]
        out.append(f"| {NOMES.get(nome, nome)} | {cel(r['tau'])} | {cel(r['sucessor'], True)} | {cel(r['ard'])} |")
    return out


def relatorio(R):
    S = R["resumos"]
    rows, metodos = R["paginas"], R["metodos"]
    n, ng = len(rows), len(R["veiculos"])
    media = lambda m, r="palavras", k="tau": S[m][r][k]["media"]
    delta = lambda a, b, r="palavras", k="tau": media(a, r, k) - media(b, r, k)
    E = R.get("efeitos", {})
    busca_teste = lambda a, b, r="palavras", k="tau": next((t for t in R.get("testes", [])
        if (t["a"], t["b"], t["regua"], t["metrica"]) == (a, b, r, k)), None)
    def frase_teste(t):
        if t is None:
            return "Inferência ainda em execução."
        return (f"Δ = {f(t['delta'])}, IC 95% [{f(t['ic95'][0])}; {f(t['ic95'][1])}], "
                f"Pratt por página p = {f(t['p_pratt_paginas'], 6)}, por veículo p = {f(t['p_pratt_veiculos'], 6)}, "
                f"permutação por veículo p = {f(t['permutacao']['p'], 6)}, Holm p = {f(t['p_holm'], 6)}.")
    audit = {k: sum(p["auditoria"][k] for p in rows) for k in rows[0]["auditoria"]}
    fragments = {m: [i for i, r in enumerate(metodos[m]) if r["diag"]["fragmentadas"]]
                 for m in ("original_lopo", "plano_lovo")}
    perfeita = {m: [i for i in fragments[m] if metodos[m][i]["diag"]["mediana_perfeita_fragmentada"]]
                for m in fragments}
    ganho_original = delta("original_lopo", "xy_ouro", "regioes")
    recuperado = delta("xy_ouro_geo", "xy_ouro", "regioes") / ganho_original
    out = ["# Reanálise justa: ordem de leitura sem bounding box fina", "",
           "## Resumo em cinco linhas", ""]
    out += [f"1. Nas {n} páginas de {ng} veículos, reproduzimos τ de regiões {f(media('original_lopo','regioes'))} contra {f(media('xy_ouro','regioes'))}; a mesma política leva a XY-cut ouro a {f(media('xy_ouro_geo','regioes'))}, recuperando {f(100*recuperado,1)}% do ganho alegado.",
            f"2. Na saída real, o plano original tem τ de palavras {f(media('original_lopo'))}, abaixo de {f(media('xy_ouro_geo'))} da XY-cut ouro com margens; com seleção LOVO por palavras, o plano chega a {f(media('plano_lovo'))}.",
            f"3. O ganho residual deste plano sobre a XY-cut ouro justa é {f(delta('plano_lovo','xy_ouro_geo'))}; " + (f"IC 95% [{f(busca_teste('plano_lovo','xy_ouro_geo')['ic95'][0])}; {f(busca_teste('plano_lovo','xy_ouro_geo')['ic95'][1])}] e permutação p = {f(busca_teste('plano_lovo','xy_ouro_geo')['permutacao']['p'],3)}." if busca_teste('plano_lovo','xy_ouro_geo') else "inferência em execução."),
            f"4. Na ablação com parâmetros comuns, a projeção acrescenta {f(delta('ab_proj_com','ab_xy_com'))} em τ de palavras após margens, frente a {f(delta('ab_proj_sem','ab_xy_sem'))} sem margens; há contribuição dos dois componentes e forte interação.",
            f"5. Veredito: retirar a alegação de superioridade geral; priorizar a política no pipeline de regiões e validar em ouro novo. A mediana oculta fragmentação em {len(fragments['plano_lovo'])} páginas, incluindo {len(perfeita['plano_lovo'])} com ordem de regiões perfeita.", "",
            "## Amostra, entrada e réguas", "",
            f"Mesmas {n} páginas concluídas, sem exclusão adicional. Grupo = parte do `page_id` antes da primeira barra (veículo), preservando nomes distintos, como `official_diary_mg` e `official_diary_MG_congonhas`. Há {ng} grupos, com distribuição de páginas {dict(sorted(collections.Counter(collections.Counter(p['veiculo'] for p in rows).values()).items()))} (chave = páginas por veículo; valor = veículos).",
            f"Foram associadas {audit['palavras']} palavras; {audit['sem_ouro']} estão fora do ouro e {audit['ambiguas']} têm dono geométrico ambíguo. Regiões-ouro vazias: {audit['regioes_vazias']}; páginas vazias: {audit['sem_palavras']}. O metadado do Golden registra {audit['visuais_retiradas']} regiões sem texto retiradas na preparação; elas não são recolocadas nem avaliadas aqui.",
            "**Principal: palavras.** Identificadores são os índices das palavras no Diamond, nunca o texto (palavras repetidas são distintas). Ouro = regiões na ordem humana; dentro delas, `linhas()` agrupa faixas verticais, ordena-as de cima para baixo e palavras da esquerda para a direita. A predição é expandida na ordem em que o método realmente emite palavras. Nenhuma mediana intervém no τ de palavras. As palavras fora do ouro continuam na saída e só são excluídas do cálculo sem referência. Médias macro por página; uma página longa não domina a média.",
            "**Secundárias: regiões e linhas.** Mantivemos as duas réguas anteriores, projetando por mediana dos postos das palavras. Para regiões-ouro, as baselines usam diretamente a ordem de caixas. Além do τ, reportamos sucessor e ARD normalizado nas três réguas. Sucessor de palavras é inflado pelos pares internos preservados em regiões/tabelas; sucessor de linhas e fragmentação continuam necessários para avaliar continuidade.",
            "**Fragmentação.** Conta regiões cujas palavras aparecem em mais de um trecho na saída, dividindo pelo total de regiões com palavras, primeiro ignorando palavras sem ouro (reproduz o original); a versão estrita conta uma palavra sem dono como interrupção. Uma região vazia não recebe uma mediana fictícia: apenas na régua secundária usa o posto da palavra geometricamente mais próxima, ou geometria se a página inteira for vazia; esse fallback é explicitamente diagnóstico. Réguas com menos de dois itens retornam ausência de medida, sem premiar páginas vazias como perfeitas.",
            "Não há GPU, modelos ao vivo, rede, OCR nem leitura dos exports do parceiro. O extrator automático é o mesmo `propor(..., regras=True)` atual. Mantivemos sua associação por centro/menor caixa e o fallback geométrico de palavras livres ao fim, idênticos em todas as baselines automáticas.", "",
            "## Política igual para todos", "",
            f"Precedência literal do original: primeiro marcas, quando **todas** as palavras do item casam com `RE_MARCACAO` (`{o.RE_MARCACAO.pattern}`); depois topo se centro < {f(.07,2)} × altura e base < {f(.10,2)} × altura; depois rodapé se centro > {f(.95,2)} × altura; o restante é corpo. Saída = topo, corpo ordenado, marcas, rodapé; topo/marcas/rodapé usam `(y0, x0, índice)` como no original. As regiões permanecem inteiras: não subdividimos uma caixa para beneficiar a baseline.",
            "A variante de classe troca **somente** o teste geométrico de topo/rodapé por `cabecalho`/`rodape`, preservando a mesma regex de marcas, precedência e ordenação interna. Nas caixas-ouro isso usa classes humanas (diagnóstico de oráculo, †); nas automáticas usa classes previstas. Não é um detector de três classes.",
            f"Conhecer as classes humanas acrescenta {f(delta('xy_ouro_classe','xy_ouro_geo'))} em τ de palavras e {f(delta('xy_ouro_classe','xy_ouro_geo','regioes'))} em regiões sobre a política geométrica. Classes previstas mudam esses valores em {f(delta('xy_auto_classe','xy_auto_geo'))} e {f(delta('xy_auto_classe','xy_auto_geo','regioes'))}. Portanto saber a classe correta ajuda modestamente aqui; prever classe não garante esse ganho.", "",
            "## Tabela principal — sequência de saída real", "",
            "IC percentil agrupado por veículo; para LOVO e ablação a seleção é refeita dentro de cada bootstrap. IC do LOPO antigo é agrupado, mas condicional às predições, mostrado apenas para diagnóstico. † informação humana indisponível em produção.", ""]
    out += tabela(S, PRINCIPAIS, "palavras")
    out += ["", "| Método | Regiões fragmentadas (média por página) | Páginas com fragmentação |", "|---|---:|---:|"]
    for m in PRINCIPAIS:
        out.append(f"| {NOMES[m]} | {f(100*S[m]['fragmentacao'],1)}% | {sum(bool(r['diag']['fragmentadas']) for r in metodos[m])}/{n} |")
    for regua in ("regioes", "linhas"):
        out += ["", f"## Régua secundária: {ROTULO_REGUA[regua]}", ""] + tabela(S, PRINCIPAIS, regua)
    out += ["", "## Seleção sem páginas irmãs no ajuste", "",
            f"Usamos a grade original de {len(o.grade())} configurações. A reprodução LOPO e a troca isolada para LOVO usam **toda** a grade original e o objetivo original (τ de regiões, desempate por sucessor e índice da grade). O plano principal usa as {sum(c.abordagem in FAMILIAS for c in o.grade())} variantes XY-cut de linhas/projeção local, com/sem margens, e seleciona por τ **de palavras**, desempate por sucessor de palavras e índice. Não mistura projeção global com local na nova comparação fatorial. Toda escolha exclui todas as páginas do veículo avaliado. Não há ajuste de limiares fixos de margens, janelas, pontes ou regex.",
            "| Seleção | τ regiões | τ linhas | τ palavras |", "|---|---:|---:|---:|"]
    for m in ("original_lopo", "original_lovo", "plano_lovo"):
        out.append(f"| {NOMES[m]} | {f(media(m,'regioes'))} | {f(media(m,'linhas'))} | {f(media(m))} |")
    out += ["", "| Seleção / braço | Configurações escolhidas e número de páginas |", "|---|---|"]
    for m, ids in R["selecao"].items():
        out.append(f"| {NOMES.get(m,m)} | " + "; ".join(f"`{c}`: {q}" for c,q in collections.Counter(ids).items()) + " |")
    out += ["", "LOVO mede a extrapolação dos parâmetros entre veículos dentro desta amostra; não desfaz a inspeção prévia de todos esses veículos durante o desenvolvimento do algoritmo. A escolha nova da régua também é uma reanálise exploratória, e não pré-registro.", "",
            "## Ablação 2 × 2 com parâmetros idênticos", "",
            "Em cada fold LOVO escolhemos **um único** trio `(score, gap, vale)` maximizando a média do τ de palavras dos quatro braços nas páginas de ajuste; desempate pela média de sucessor e ordem fixa dos trios. Aplicamos esse trio aos quatro braços do veículo retido. A grade comum varia score, gap e vale; XY-cut é indiferente a vale. Assim a remoção de política/projeção não muda átomos, fragmentos de entrada nem outros parâmetros. O critério simétrico pode escolher um trio menos favorável a um braço do que sua própria seleção.", ""]
    for r in REGUAS:
        out += [f"### {ROTULO_REGUA[r].capitalize()}", ""] + tabela(S, AB, r) + [""]
    if E:
        nomes_e = {"politica_xy": "Margens na XY-cut", "politica_projecao": "Margens na projeção",
                   "projecao_sem": "Projeção sem margens", "projecao_com": "Projeção com margens",
                   "interacao": "Interação (diferença de diferenças)", "media_politica": "Efeito médio da política",
                   "media_projecao": "Efeito médio da projeção"}
        out += ["| Efeito sobre τ | Palavras (IC 95%) | Regiões (IC 95%) | Linhas (IC 95%) |", "|---|---:|---:|---:|"]
        for e, titulo in nomes_e.items():
            out.append(f"| {titulo} | " + " | ".join(cel(E[e][r]) for r in ("palavras","regioes","linhas")) + " |")
        total = delta("ab_proj_com", "ab_xy_sem")
        out += ["", f"O ganho conjunto é {f(total)} em τ de palavras. Dividir a interação igualmente (média dos dois caminhos do fatorial) atribui {f(100*E['media_politica']['palavras']['media']/total,1)}% à política e {f(100*E['media_projecao']['palavras']['media']/total,1)}% à projeção. Essa decomposição **descreve o fatorial**, não o ganho original contra regiões-ouro. Interação negativa indica efeitos parcialmente substitutos: somar ganhos isolados superestima o ganho conjunto."]
        t = busca_teste("ab_proj_com", "ab_xy_com")
        if t:
            out += ["", f"Após margens, a projeção melhora {t['ganha']} páginas, empata em {t['empata']} e piora {t['perde']}, com apenas {t['permutacao']['grupos_ativos']} veículos contribuindo para a diferença. A permutação exata dá p = {f(t['permutacao']['p'],3)}. O efeito residual é concentrado; o IC percentil positivo não basta para declarar superioridade robusta."]
    out += ["", "### Sensibilidade: mesma seleção, permitindo parâmetros próprios por braço", "",
            "Cada braço é selecionado com o mesmo LOVO/τ de palavras, mas pode escolher seu próprio trio. Esta tabela estima o desempenho de cada família; não a usamos para atribuir os efeitos causais da ablação.", ""]
    for r in ("palavras", "regioes"):
        out += [f"Régua de {ROTULO_REGUA[r]}:", ""] + tabela(S, ["sens_" + a for a in FAMILIAS], r) + [""]
    out += ["## Inferência agrupada e comparação com o original", "",
            f"Bootstrap com {R['parametros']['bootstrap']} reamostras e semente {R['parametros']['semente']}: sorteamos {ng} veículos com reposição, mantemos todas as suas páginas e recalculamos a média macro por página. Nos métodos selecionados, cada reamostra refaz a escolha usando multiplicidades dos veículos e excluindo todas as cópias do veículo retido; o custo é só selecionar a partir da grade de predições já calculadas. Não re-treinamos nem refazemos o desenho da heurística. Baselines fixas são reamostradas aos pares.",
            "Pratt é bilateral, com diferenças arredondadas em doze casas para remover ruído numérico de empates; apresentamos por página (diagnóstico que ainda tem dependência) e nas médias de cada veículo (unidades independentes presumidas). Permutação troca o sinal de todas as diferenças de um veículo simultaneamente, preservando empates e correlação interna; estatística = diferença macro por página. Enumeramos todos os sinais quando há poucos grupos com diferença; nos demais casos usamos Monte Carlo e correção +1. Os testes de sinais e Pratt são condicionais às predições selecionadas, enquanto o IC LOVO inclui nova seleção; discordâncias entre eles não são prova de equivalência ou de significância. A hipótese de simetria/troca de sinais é uma suposição, não assegurada por desenho aleatorizado.",
            f"Correção Holm conjunta sobre {len(R.get('testes',[]))} contrastes/métricas apresentados, cobrindo as três réguas e sucessor de linhas/palavras. Não corrige a exploração histórica do algoritmo. IC percentil e testes não são intercambiáveis, sobretudo quando o ganho está concentrado em poucos veículos.", ""]
    if "reproducao" in R:
        old = R["reproducao"]["testes_originais"]["plano_cv"]["regioes"]["tau"]
        out += [f"Reprodução do original: {len(R['reproducao']['discrepancias_lopo'])} discrepâncias nas métricas LOPO por página e {len(R['reproducao']['discrepancias_grade'])} na grade completa; hashes das entradas/módulos originais coincidem: {'sim' if R['reproducao']['hashes_originais_iguais'] else 'não'}. O original reportava Δ de regiões = {f(old['diferenca'])}, IC por página [{f(old['ic95'][0])}; {f(old['ic95'][1])}], Wilcoxon com descarte de zeros p = {f(old['p'],6)} e {old['empata']} empates. Abaixo isolamos a mudança de unidade/seleção, depois a baseline justa.", ""]
        familias_antigas = R["reproducao"]["familias_originais"]
        out += [f"A sensibilidade original, selecionada na mesma amostra, dava τ regional {f(familias_antigas['xy_linhas']['resumo']['regioes']['tau']['media'])} para XY-cut de linhas pura e {f(familias_antigas['xy_margens']['resumo']['regioes']['tau']['media'])} com margens. A ablação nova não exige reproduzir essas médias otimizadas no próprio teste: muda seleção e mantém os parâmetros pareados; os valores originais de toda a grade foram conferidos por página.", ""]
    out += ["| Contraste (A − B) | Régua / métrica | Δ (IC 95%) | G/E/P | Pratt pág. | Pratt veículo | Permutação veículo | Holm |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for t in R.get("testes", []):
        out.append(f"| {NOMES[t['a']]} − {NOMES[t['b']]} | {ROTULO_REGUA[t['regua']]} / {'τ' if t['metrica']=='tau' else t['metrica']} | {f(t['delta'])} [{f(t['ic95'][0])}; {f(t['ic95'][1])}] | {t['ganha']}/{t['empata']}/{t['perde']} | {f(t['p_pratt_paginas'],6)} | {f(t['p_pratt_veiculos'],6)} | {f(t['permutacao']['p'],6)} | {f(t['p_holm'],6)} |")
    out += ["", "G/E/P = ganha/empata/perde por página; todos os contrastes usam métricas em que maior é melhor. As contagens, tipo exato/Monte Carlo e número de sinais testados estão no checkpoint.", "",
            "## Estratos reprodutíveis por calhas do corpo", "",
            "O critério não lê `stats.n_colunas`, classes ou ordem humana: palavras com centro entre dez e noventa e cinco por cento da altura, excluindo marcas; `linhas_partidas(gap=1.2)`; `vales_locais(limiar=0.08)` e fallback para `vales`. Os vales usam envelopes de fragmentos, bins de dois pontos, suporte vertical em ambos os lados e recorrência em janelas sobrepostas. Número = cortes aceitos + um, limitado pelo algoritmo a quatro. Score do detector não intervém: até páginas só de tabelas podem revelar a calha entre tabelas. Usa o valor fixo, não a configuração escolhida contra o ouro.",
            "É um estrato geométrico de **colunas detectadas**, não uma verdade visual anotada. Células de tabelas podem criar falsa calha (Salvador) e poucos fragmentos podem esconder colunas. As tabelas abaixo não autorizam dizer que toda página de uma coluna é trivial ou que a avaliação só faz sentido em multicoluna. Mantivemos os critérios sem corrigir resultados a posteriori; a tabela de cortes e links permite inspeção visual.", ""]
    estr = R.get("estratos", {})
    nomes_g = {"uma": "Uma coluna detectada", "multi": "Multicoluna detectada", "duas": "Duas", "tres": "Três", "quatro": "Quatro"}
    subset = ("xy_ouro", "xy_ouro_geo", "xy_auto_geo", "original_lopo", "plano_lovo")
    for g, obj in estr.items():
        out += [f"### {nomes_g[g]} — {obj['n']} páginas, {obj['veiculos']} veículos", "",
                "| Método | τ palavras (IC 95%) | τ regiões (IC 95%) | Sucessor linhas | Sucessor palavras | Fragmentação |", "|---|---:|---:|---:|---:|---:|"]
        for m in subset:
            r = obj["resumos"][m]
            out.append(f"| {NOMES[m]} | {cel(r['palavras']['tau'])} | {cel(r['regioes']['tau'])} | {f(100*r['linhas']['sucessor']['media'],1)}% | {f(100*r['palavras']['sucessor']['media'],1)}% | {f(100*r['fragmentacao'],1)}% |")
    out += ["", "IC por veículo dentro de cada estrato, condicionais às escolhas LOVO globais; não retunamos métodos para cada estrato. Estratos muito pequenos, especialmente os de três/quatro colunas, não sustentam inferência própria.", "",
            f"Páginas que mudam do número antigo para o novo: {sum(p['colunas']['antigo'] != p['colunas']['n'] for p in rows)}; páginas que mudam entre uma/multicoluna: {sum((p['colunas']['antigo'] == 1) != (p['colunas']['n'] == 1) for p in rows)}.", "",
            "| Página (imagem original) | Número antigo → novo | Cortes em pontos PDF |", "|---|---:|---|"]
    for p in rows:
        c = p["colunas"]
        if c["antigo"] != c["n"]:
            out.append(f"| [{p['page_id']}](../data/golden/golden_v4/img/{c['imagem']}) | {c['antigo']} → {c['n']} | " + ("; ".join(f(x,2) for x in c["cortes"]) or "sem calha aceita") + " |")
    out += ["", "Conferência visual pontual (sem substituir o critério): RJ Legislativo tem três colunas no corpo; Manaus tem duas tabelas paralelas; MS de junho tem uma tabela larga; MG e PE têm quatro colunas de texto. Salvador tem duas faixas principais de tabelas, mas o perfil detecta uma calha interna extra. SE de março combina uma coluna textual e uma faixa gráfica; a régua de palavras não mede conteúdo da imagem. Essas observações são limitações do estratificador, não novas anotações.", "",
            "## Páginas em que a mediana oculta intercalação", "",
            f"Plano original LOPO: {len(fragments['original_lopo'])} páginas com fragmentação; plano LOVO por palavras: {len(fragments['plano_lovo'])}. Fração macro {f(100*S['plano_lovo']['fragmentacao'],1)}%. Não chamamos toda fragmentação de severa: uma interrupção de rodapé e duas tabelas alternando muitas vezes têm efeitos distintos. A ordem por mediana não registra o número de trechos. Em {len(perfeita['plano_lovo'])} páginas a sequência projetada de regiões é exatamente a humana, embora palavras de regiões estejam intercaladas.", "",
            "| Página | Regiões: número de trechos | τ regiões | τ palavras | Ordem de regiões perfeita? |", "|---|---|---:|---:|---|"]
    for i in sorted(set(fragments["original_lopo"] + fragments["plano_lovo"])):
        r = metodos["plano_lovo"][i]
        out.append(f"| `{rows[i]['page_id']}` | " + "; ".join(f"{rid}: {q}" for rid,q in r["diag"]["fragmentadas"].items()) + f" | {f(r['regioes']['tau'])} | {f(r['palavras']['tau'])} | {'sim' if i in perfeita['plano_lovo'] else 'não'} |")
    estritas = sum(bool(r["diag"]["fragmentadas_estritas"]) for r in metodos["plano_lovo"])
    out += ["", f"Incluindo palavras fora do ouro como interrupções, há {estritas} páginas com fragmentação estrita; ignorá-las dá {len(fragments['plano_lovo'])}.", ""]
    if "reproducao" in R and estr:
        oldmulti = R["reproducao"]["resumo_original"]["multi"]
        newmulti = estr["multi"]["resumos"]
        j_manaus = next(i for i,p in enumerate(rows) if "am_manaus" in p["page_id"])
        j_caxias = next(i for i,p in enumerate(rows) if "duque" in p["page_id"] and "#p44" in p["page_id"])
        j_ms = next(i for i,p in enumerate(rows) if "#p233" in p["page_id"])
        out += ["## Resposta aos nove itens da revisão adversarial", ""]
        respostas = [
            ("1. Mediana mascara intercalação — procede em parte",
             f"A contraprova sintética dá τ de regiões {f(R['controles']['intercalacao']['tau_regioes'])} e τ de palavras {f(R['controles']['intercalacao']['tau_palavras'])}, com {f(100*R['controles']['intercalacao']['fracao_fragmentadas'],1)}% das regiões fragmentadas. Há {len(fragments['plano_lovo'])} páginas reais com fragmentação e {len(perfeita['plano_lovo'])} com ordem regional perfeita. Em Caxias #p44, uma dupla de regiões reaparece até {max(metodos['plano_lovo'][j_caxias]['diag']['fragmentadas'].values())} vezes; τ regional {f(metodos['plano_lovo'][j_caxias]['regioes']['tau'])} versus palavra {f(metodos['plano_lovo'][j_caxias]['palavras']['tau'])}. Porém não procede atribuir **todo** o ganho antigo à mediana: mesmo na saída real o LOPO supera a XY-cut pura em {f(delta('original_lopo','xy_ouro'))}. A comparação justa é que desfaz essa vitória, com diferença {f(delta('original_lopo','xy_ouro_geo'))}."),
            ("2. Perda multicoluna / paradoxo de Simpson — procede em parte",
             f"Reproduzimos no estrato antigo τ de regiões {f(oldmulti['plano_cv']['regioes']['tau']['media'])} vs {f(oldmulti['xy_ouro']['regioes']['tau']['media'])} e sucessor de linhas {f(100*oldmulti['plano_cv']['linhas']['sucessor']['media'],1)}% vs {f(100*oldmulti['xy_ouro']['linhas']['sucessor']['media'],1)}%. Mas os rótulos estavam errados; no novo multicoluna, o LOPO tem τ de regiões {f(newmulti['original_lopo']['regioes']['tau']['media'])} vs {f(newmulti['xy_ouro']['regioes']['tau']['media'])} da pura, e τ de palavras {f(newmulti['original_lopo']['palavras']['tau']['media'])} vs {f(newmulti['xy_ouro_geo']['palavras']['tau']['media'])} da justa. O LOVO por palavras tem τ {f(newmulti['plano_lovo']['palavras']['tau']['media'])} e sucessor de linhas {f(100*newmulti['plano_lovo']['linhas']['sucessor']['media'],1)}% vs {f(100*newmulti['xy_ouro_geo']['linhas']['sucessor']['media'],1)}%. Há falha de continuidade e heterogeneidade, mas não perda em todas as réguas. Nem no antigo estrato a proposta perdia τ de linhas: {f(oldmulti['plano_cv']['linhas']['tau']['media'])} vs {f(oldmulti['xy_ouro']['linhas']['tau']['media'])}. Não é demonstrado um paradoxo de Simpson clássico: não há inversão de sinal uniforme em todos os estratos."),
            ("3. Assimetria da política de margens — procede",
             f"XY-cut ouro sobe {f(media('xy_ouro','regioes'))} → {f(media('xy_ouro_geo','regioes'))} em τ regional, recuperando {f(100*recuperado,1)}% da diferença original. Na palavra sobe {f(media('xy_ouro'))} → {f(media('xy_ouro_geo'))}. A ablação mostra margens na XY-cut de linhas +{f(delta('ab_xy_com','ab_xy_sem'))} e contribuição adicional da projeção com margens +{f(delta('ab_proj_com','ab_xy_com'))}. A política domina a explicação da manchete original; não elimina toda contribuição da projeção."),
            ("4. Desenvolvimento informado pelo ouro / regras fora da seleção — procede",
             f"O original declara expansão de sua grade inicial de {sum('local' not in c.abordagem for c in o.grade())} para {len(o.grade())} configurações após inspeção destas páginas. LOVO por palavras escolhe a mesma configuração em {max(collections.Counter(R['selecao']['plano_lovo']).values())}/{n} páginas, mas nenhuma das regras fixas foi desenhada num conjunto novo. A melhoria regional de {f(media('original_lovo','regioes'))} para {f(media('plano_lovo','regioes'))} ao trocar o objetivo é reanálise, não evidência independente. Esta tarefa não pode estimar numericamente o viés de desenvolvimento sem dados inéditos."),
            ("5. LOPO não respeita veículos — procede, com efeito pontual pequeno nesta grade",
             f"Há {ng} veículos para {n} páginas; {sum(v>1 for v in collections.Counter(p['veiculo'] for p in rows).values())} veículos têm múltiplas páginas. Trocar só LOPO por LOVO com o objetivo original muda τ regional {f(media('original_lopo','regioes'),6)} → {f(media('original_lovo','regioes'),6)}, palavra {f(media('original_lopo'),6)} → {f(media('original_lovo'),6)}; o número de páginas com escolha diferente é {sum(a!=b for a,b in zip(R['selecao']['original_lopo'],R['selecao']['original_lovo']))}. A independência não existia; não é correto concluir que esse vazamento de veículo explica sozinho o ganho observado."),
            ("6. Casos vazios e palavras fora do ouro — procede em parte",
             f"Há de fato um assert para região vazia e mediana de alturas sem fallback no carregador antigo. Nesta amostra há {audit['regioes_vazias']} regiões-ouro vazias e {audit['sem_palavras']} páginas vazias; testes sintéticos de ambos passaram. {audit['visuais_retiradas']} regiões sem texto constam como retiradas antes do Golden, não páginas inteiras descartadas por esta execução. {audit['sem_ouro']} palavras fora do ouro permanecem na predição, mas não têm referência avaliável. Portanto procede a fragilidade/limitação de cobertura; não procede alegar abortos observados ou filtragem adicional de páginas pelo script."),
            ("7. Inferência otimista / zeros / multiplicidade — procede em parte",
             frase_teste(busca_teste('original_lovo','xy_ouro','regioes')) + " Contra a baseline justa na régua principal: " + frase_teste(busca_teste('plano_lovo','xy_ouro_geo')) +
             f" Refizemos seleção no bootstrap agrupado e preservamos zeros em Pratt. Contudo os {R['reproducao']['testes_originais']['plano_cv']['regioes']['tau']['empata']} zeros removidos pelo Wilcoxon original não demonstram por si sós p inflado: `wilcox` é uma convenção legítima de ranqueamento. A dependência e a seleção exploratória são as limitações fortes. Intervalo condicional não é necessariamente errado para algoritmo congelado; é incompleto para incerteza de seleção. Holm ampliado não corrige o histórico de tentativas."),
            ("8. Tabelas achatadas / tabelas paralelas — procede em parte",
             f"O fluxo interno usa y/x, exatamente como a referência derivada; não existe ouro de estrutura de células para quantificar erro semântico vertical. A falha entre tabelas é real: Manaus no LOPO antigo tem τ de linhas {f(metodos['original_lopo'][j_manaus]['linhas']['tau'])} e palavras {f(metodos['original_lopo'][j_manaus]['palavras']['tau'])}; no LOVO por palavras com margens ambos são {f(metodos['plano_lovo'][j_manaus]['palavras']['tau'])}. Já Caxias #p44 mantém sucessor de linhas {f(100*metodos['plano_lovo'][j_caxias]['linhas']['sucessor'],1)}%, frente a {f(100*metodos['xy_ouro_geo'][j_caxias]['linhas']['sucessor'],1)}% da XY-cut justa. Margens corrigem o caso Manaus, mas não a instância larga que mistura tabelas; átomos não garantem continuidade correta entre instâncias."),
            ("9. Queda com oráculo prova compensação de erros / overfitting — procede em parte",
             f"Reproduzimos o oráculo LOPO: τ regional {f(media('original_lopo','regioes'))} → {f(media('oraculo_lopo','regioes'))}, mas τ de palavras {f(media('original_lopo'))} → {f(media('oraculo_lopo'))}. No LOVO por palavras, região {f(media('plano_lovo','regioes'))} → {f(media('oraculo_lovo','regioes'))}, palavra {f(media('plano_lovo'))} → {f(media('oraculo_lovo'))} e sucessor de palavras {f(100*media('plano_lovo',k='sucessor'),1)}% → {f(100*media('oraculo_lovo',k='sucessor'),1)}%. Em MS #p233, o τ de palavras sem oráculo é {f(metodos['plano_lovo'][j_ms]['palavras']['tau'])}. Há sensibilidade e ausência de monotonicidade na régua regional. Uma heurística não tem garantia matemática de melhorar quando as caixas mudam; esta queda não prova overfitting/compensação como causa. O oráculo altera falsos positivos, limites e instâncias, e exclui imagens sem texto; não é detector perfeito nem teto de desempenho.")]
        for titulo, texto in respostas:
            out += [f"### {titulo}", "", texto, ""]
    out += ["## Limitações e recomendação para o TCC", "",
            f"Amostra pequena e de conveniência ({n} páginas, {ng} veículos), mesmo anotador, geometria já inspecionada no desenvolvimento. Anotação por correção de pré-anotação traz **viés de ancoragem**: granularidade e caixas humanas podem favorecer o pipeline que as propôs. Não há teste independente dentro desta tarefa; cross-validation não apaga esse viés.",
            "A referência dentro de cada região é algorítmica, não anotação humana de palavras/células. τ palavra mede inversões entre todas as palavras, dando peso quadrático a regiões longas dentro de cada página; τ região dá peso semelhante a um campo de cabeçalho e a uma tabela inteira. Por isso seus valores não são intercambiáveis. Sucessor de palavras também pode esconder inversão de tabelas completas: quase todos os pares internos sobrevivem.",
            "Os grupos pelo prefixo do page_id representam veículos, não famílias tipográficas independentes comprovadas; edições distintas do mesmo veículo ficam juntas, mas dois veículos podem usar o mesmo template. Bootstrap e testes ainda presumem independência entre grupos e não estimam efeitos de novos estilos não representados.",
            "Caixas-ouro são segmentação-oráculo. Baselines automáticas são a comparação mais próxima da produção; ainda compartilham cache de detecção, regras desenvolvidas no Diamond e camada de texto digital. Não medimos OCR, texto dentro de imagens, ordem semântica de células, latência ou impacto em RI. O cache do detector já corta scores baixos. O estratificador automático é falível e usa projeção, favorecendo estratos em que a própria projeção tem suporte.",
            f"**O que sobra da afirmação original:** há sinal exploratório de que ordenar linhas diretamente pode funcionar, e a projeção contribui além de uma XY-cut de linhas; não há evidência robusta de que substitua regiões finas. Dar margens à XY-cut ouro reduz a vantagem regional original de {f(ganho_original)} para {f(delta('original_lopo','xy_ouro_geo','regioes'))}, e na palavra inverte a comparação ({f(delta('original_lopo','xy_ouro_geo'))}). Mesmo o novo plano LOVO tem diferença principal inconclusiva contra essa referência justa. Ausência de diferença significativa não prova equivalência.",
            f"**Pipeline atual de regiões:** vale priorizar a política geométrica como candidata simples para validação: no automático, τ palavra {f(media('xy_auto'))} → {f(media('xy_auto_geo'))} e sucessor de linhas {f(100*media('xy_auto','linhas','sucessor'),1)}% → {f(100*media('xy_auto_geo','linhas','sucessor'),1)}%; a ingênua não recebe ganho similar. Não adotá-la universalmente sem avaliar regressões: em τ de palavras a XY-cut automática com margens ganha em {sum(x['palavras']['tau'] > y['palavras']['tau']+1e-12 for x,y in zip(metodos['xy_auto_geo'],metodos['xy_auto']))}, empata em {sum(abs(x['palavras']['tau']-y['palavras']['tau'])<=1e-12 for x,y in zip(metodos['xy_auto_geo'],metodos['xy_auto']))} e perde em {sum(x['palavras']['tau'] < y['palavras']['tau']-1e-12 for x,y in zip(metodos['xy_auto_geo'],metodos['xy_auto']))} páginas.",
            "Congelar heurísticas/limiares e testar veículos inéditos com anotação desenhada do zero; usar palavra como régua principal, sucessor de linhas e fragmentação como restrições de continuidade; comparar sempre política igual e registrar regressões de cabeçalhos/rodapés. Mudança do protocolo ou adoção no pipeline depende da decisão do Pedro; esta tarefa entrega diagnóstico e não muda o pipeline.", "",
            "## Reprodução e integridade", "", "```powershell",
            "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_justo.py --do-zero",
            "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_justo.py --conferir", "```", "",
            "Executar sem `--do-zero` retoma páginas com checkpoint e hashes idênticos. A execução grava números parciais logo após cada página. Os únicos arquivos criados são o script e este Markdown; o checkpoint comprimido no comentário final contém hashes SHA-256, métricas de toda a grade por página, escolhas, testes e resultados usados para gerar as tabelas. Não contém transcrições nem dados do parceiro. `--conferir` reabre, decodifica, compara o relatório integral com sua renderização e confere os hashes atuais. A execução normal também confere hashes antes/depois e a reprodução por página do original.", "",
            "Para ler o estado numérico sem gravar outro arquivo: importar este módulo e chamar `carregar_cache(hashes())`. Controles sintéticos verificam página sem palavras, região sem palavras e intercalação com mediana perfeita, sem assert nessas condições.", "",
            "### Hashes das entradas e fontes", "", "| Arquivo | SHA-256 |", "|---|---|"]
    for p,h in R["hashes"].items():
        out.append(f"| `{p}` | `{h}` |")
    out.append("")
    # Separa paragrafos e tabelas sem quebrar tabelas, resumo numerado ou comandos.
    espacado, em_codigo = [], False
    for linha in out:
        if espacado and linha and espacado[-1] and not em_codigo:
            anterior = espacado[-1]
            prosa = not linha.startswith(("|", "#", "```")) and not re.match(r"^\d+\.", linha)
            prosa_anterior = not anterior.startswith(("|", "#", "```")) and not re.match(r"^\d+\.", anterior)
            if (linha.startswith("|") and not anterior.startswith("|")) or (prosa and prosa_anterior):
                espacado.append("")
        espacado.append(linha)
        if linha.startswith("```"):
            em_codigo = not em_codigo
    return "\n".join(espacado)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--permutacoes", type=int, default=50000)
    ap.add_argument("--semente", type=int, default=42)
    args = ap.parse_args()
    if args.bootstrap < 2000 or args.permutacoes < 10000:
        raise ValueError("Use pelo menos 2000 bootstraps e 10000 permutações")
    H = hashes()
    R = None if args.do_zero else carregar_cache(H)
    if args.conferir:
        if not R or "resumos" not in R:
            raise ValueError("Não há execução completa com hashes atuais")
        texto = relatorio(R) + checkpoint(R)
        if SAIDA.read_text(encoding="utf-8") != texto:
            raise ValueError("Relatório não coincide com os resultados serializados")
        print("[OK] Relatório idêntico à renderização do checkpoint; hashes atuais conferidos.")
        return
    ps, cs = preparar(), o.grade()
    R = R or {"hashes": H, "paginas": [], "controles": controles()}
    n = len(R["paginas"])
    for j, q in enumerate(ps):
        if j < n:
            continue
        row = {"page_id": q["p"]["page_id"], "veiculo": q["p"]["page_id"].split("/", 1)[0],
               "auditoria": q["auditoria"], "colunas": colunas(q), "bases": baselines(q), "variantes": {}}
        for c in cs:
            seq, _, diag = o.prever(q, c)
            r = avaliar(q, seq)
            r["diag"].update(diag)
            row["variantes"][c.id] = r
        R["paginas"].append(row)
        gravar(parcial(R), R)
        print(f"[página {j+1}/{len(ps)}] {row['page_id']}", flush=True)
    rows = R["paginas"]
    ids, specs, bracos = selecao(rows, cs)
    metodos = {nome: [p["bases"][nome] for p in rows] for nome in BASES}
    for nome, escolhas in ids.items():
        metodos[nome] = [p["variantes"][cs[i].id] for p, i in zip(rows, escolhas)]
    for nome, fonte in (("oraculo_lovo", "plano_lovo"), ("oraculo_lopo", "original_lopo")):
        metodos[nome] = []
        for q, i in zip(ps, ids[fonte]):
            seq, _, _ = o.prever(q, cs[i], oraculo=True)
            metodos[nome].append(avaliar(q, seq))
    R["selecao"] = {nome: [cs[i].id for i in ix] for nome, ix in ids.items()}
    R["metodos"] = metodos
    R["parametros"] = {"bootstrap": args.bootstrap, "permutacoes": args.permutacoes, "semente": args.semente}
    print("[inferência] Bootstrap por veículo com nova seleção dentro de cada reamostra", flush=True)
    S, B, grupos, gi = agregar(rows, metodos, cs, ids, specs, args.bootstrap, args.semente)
    R["resumos"], R["veiculos"] = S, grupos
    gravar(relatorio(R), R)
    print("[inferência] Pratt e permutação pareada por veículo", flush=True)
    R["testes"] = testes(metodos, B, gi, args.permutacoes, args.semente)
    R["efeitos"] = efeitos(S, B)
    R["estratos"] = estratos(rows, metodos, args.bootstrap, args.semente)
    with ORIGINAL.open(encoding="utf-8") as arq:
        antigo = json.load(arq)
    discrep, discrep_grade = [], []
    for row, old, j in zip(rows, antigo["por_pagina"], range(len(rows))):
        if row["page_id"] != old["page_id"]:
            raise ValueError("Páginas não coincidem com a execução original")
        for regua in ("regioes", "linhas"):
            for m in METRICAS:
                if abs(metodos["original_lopo"][j][regua][m] - old["metodos"]["plano_cv"][regua][m]) > 1e-12:
                    discrep.append([row["page_id"], regua, m])
                for c in cs:
                    if abs(row["variantes"][c.id][regua][m] - old["variantes"][c.id][regua][m]) > 1e-12:
                        discrep_grade.append([row["page_id"], c.id, regua, m])
    R["reproducao"] = {"discrepancias_lopo": discrep, "resumo_original": antigo["resumo"],
                        "discrepancias_grade": discrep_grade,
                        "testes_originais": antigo["testes"], "familias_originais": antigo["melhores_familias"],
                        "hashes_originais_iguais": all(H.get(p) == h for p, h in antigo["hashes"].items())}
    if discrep or discrep_grade:
        raise ValueError(f"Reprodução LOPO/grade difere: {(discrep + discrep_grade)[:3]}")
    if round(S["xy_ouro"]["regioes"]["tau"]["media"], 3) != 0.825:
        raise ValueError("Não foi reproduzido o baseline 0,825")
    if H != hashes():
        raise ValueError("Alguma entrada ou fonte mudou durante a execução")
    gravar(relatorio(R), R)
    if SAIDA.read_text(encoding="utf-8") != relatorio(R) + checkpoint(R):
        raise ValueError("Relatório difere do resultado medido")
    print("\n".join(tabela(S, PRINCIPAIS, "palavras")))
    print("[OK] Relatório reaberto, números conferidos, entradas preservadas.", flush=True)


if __name__ == "__main__":
    main()
