"""Mede o oraculo hierarquico e HIER-1 no ajuste, sem treino nem GPU.

Observa as folhas/faixas da propria regra de colunas, sem copiar sua logica.
Reusa features, calibracao, candidatos e max-regret do E004. A referencia so
entra no diagnostico, nos oraculos e na regua oficial importada. Nao abre
externas, PDFs, anotacoes originais ou dados do parceiro. Persiste uma pagina
por arquivo, com hashes das fontes e substituicao atomica, para retomar.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e016_hierarquico.py
  --somente-ancora | --autoteste | --conferir | --max-minutos 30
Unicas escritas: este script e resultados/e016_hierarquico/. CPU, quatro
threads, um processo, num_workers=0. Nenhuma escolha usa conjunto externo.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse
import collections
import gc
import itertools
import json
import math
import random
import statistics
import time
import warnings
from contextlib import contextmanager
from functools import lru_cache

from orquestracao.analises import e004_grafo as g
from orquestracao.analises import e014_cadeias as h
from orquestracao.analises import e002_oraculos as o
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

c, np = g.c, g.np
OUT = RAIZ / "resultados/e016_hierarquico"
COORTES = ("golden_v4", "validacao_silver")
GRAFO, CFG = h.GRAFO, h.CFG
METODOS = ("regra", "hibrido67", GRAFO, "oraculo_hierarquico",
           "oraculo_interna_segmentos_regra", "oraculo_segmentos_interna_grafo",
           "hier1", "oraculo_hierarquico_quebras")
EXEC = FONTE = FONTE2 = INFO = MODELO = LOCK_SHA = PRAZO = None
FONTES = {}


def exigir(ok, mensagem):
    g.exigir(ok, mensagem)


def gravar(path, obj):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora do E016")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, path)


def fonte(path):
    path = Path(path).resolve()
    exigir(path.is_relative_to(RAIZ), "Fonte fora do repositorio")
    nome = path.relative_to(RAIZ).as_posix()
    exigir(not any(s in nome for s in ("labelstudio", "golden_v3_novo", "teste_silver",
                                       "data/raw/", "data/golden/", "data/diamond/")),
           "Fonte fora do ajuste: " + nome)
    exigir(path.is_file(), "Fonte ausente: " + nome)
    FONTES[nome] = c.sha(path)
    return path


def ler(path, pagina=False):
    path = fonte(path)
    raw = path.read_text(encoding="utf-8")
    if pagina:
        m = o.re.search(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")', raw)
        exigir(m is not None, "Cache sem page_id")
        o.permitido(json.loads(m.group(1)))
    return json.loads(raw)


def vigiar():
    exigir(o.ler_lock()[0] == LOCK_SHA, "Lacre cego mudou")
    if PRAZO is not None and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; repetir retoma paginas prontas")
    mem = b.memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 800, "RAM insuficiente; cache preservado")
    exigir(g.medir_memoria()["pico_rss_mb"] < 3072, "RSS excede 3 GiB")


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if not f.tell():
            f.write(b"0")
            f.flush()
        f.seek(0)
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def paginas(co):
    exigir(co in COORTES, "Somente bancadas de ajuste")
    yield from o.paginas(co)


def iniciar():
    global EXEC, FONTE, FONTE2, INFO
    for path in [Path(__file__), Path(g.__file__), Path(h.__file__), Path(o.__file__),
                 Path(c.__file__), Path(o.lm.__file__), *b.DEP_PATHS,
                 RAIZ / "data/processed/splits.json",
                 b.UNIDADES / "bancadas/golden_v4.jsonl"]:
        fonte(path)
    splits = ler(RAIZ / "data/processed/splits.json")
    exigir(splits["validacao"] == ["official_diary_rn"], "Validacao nao e apenas RN")
    for suf in (".jsonl", ".palavras.jsonl"):
        fonte(b.UNIDADES / "linhas" / ("official_diary_rn" + suf))
    for path in sorted((RAIZ / "experimentos/cards").glob("E016_*.md")):
        fonte(path)
    pointer = ler(g.CACHE / "ultima_execucao.json")
    FONTE = (g.OUT / pointer["execucao"]).resolve()
    exigir(FONTE.is_relative_to(g.OUT), "Ponteiro E004 invalido")
    sel = ler(FONTE / "selecao_congelada.json")
    exigir(sel["metodo"] == GRAFO and sel["config"] == CFG, "E004 congelado mudou")
    INFO = ler(FONTE / "modelo.json")
    exigir(INFO["concluido"] and c.sha(fonte(FONTE / "modelo.txt")) == INFO["sha256"],
           "Modelo E004 mudou")
    man2 = ler(o.OUT / "cache/manifesto.json")
    FONTE2 = o.OUT / "cache" / man2["assinatura"]
    # Conferir somente hashes relevantes do E004; nunca abrir fontes externas.
    man4 = ler(g.CACHE / "manifesto.json")
    for nome, sha in FONTES.items():
        if nome in man4["fontes"]:
            exigir(sha == man4["fontes"][nome], "Fonte difere do E004: " + nome)
    # E006 ja completou em CPU as duas predições leves que faltavam no RN.
    for co in COORTES:
        pred = b.OUT / "pred" / f"layoutreader_pronto__linhas__{co}.jsonl"
        if pred.exists():
            fonte(pred)
    for obj, p in paginas("validacao_silver"):
        if len(p["bounding_boxes"]) <= 67:
            fonte(RAIZ / "resultados/e006_residual/predicoes_rn" /
                  (e.ac.chave(p["page_id"]) + ".json"))
    man = {"fontes": dict(FONTES), "lock_sha256": LOCK_SHA,
           "origem_e004": FONTE.relative_to(RAIZ).as_posix(), "config": CFG,
           "bancadas": COORTES, "metodos": METODOS, "cpu": True,
           "threads": 4, "num_workers": 0, "treino": False,
           "segmentacao": "folhas e pontes da recursao original; margens; atomos singleton",
           "portao": "criterios E016 sem alteracao; medias de bancadas com peso igual"}
    EXEC = OUT / "cache" / c.digest(man)
    gravar(EXEC / "manifesto.json", man)
    return man


def segmentar(ctx):
    """Observa a regra original; nunca recebe ordem ou caixas humanas."""
    folhas, pontes, rastros = [], set(), []
    codigo = e.o.ordenar_projecao.__code__
    anterior = sys.getprofile()
    def perfil(frame, evento, arg):
        if evento != "return" or frame.f_code is not codigo:
            return
        loc = frame.f_locals
        ids = list(loc["ids"])
        if not ids:
            return
        cortes = list(loc.get("cortes", []))
        largos = list(loc.get("largos", []))
        rastros.append({"ids": [ctx["cs"][i]["id"] for i in ids],
                        "cortes": cortes, "profundidade": loc["depth"],
                        "pontes": [ctx["cs"][i]["id"] for i in largos]})
        if not cortes or loc["depth"] > 60:
            folhas.append(ids)
        pontes.update(largos)
    try:
        sys.setprofile(perfil)
        ordem, _ = b.prever(ctx["auto"], ctx["ws"], "regra_colunas")
    finally:
        sys.setprofile(anterior)
    exigir(ordem == ctx["ordem"], "Regra capturada divergiu")
    dono, tipos = {}, {}
    for j, ids in enumerate(folhas):
        for i in ids:
            uid = ctx["cs"][i]["id"]
            exigir(uid not in dono, "Folhas sobrepostas")
            dono[uid] = f"folha_{j}"
            tipos[uid] = "coluna_local"
    for i in pontes:
        uid = ctx["cs"][i]["id"]
        exigir(uid not in dono, "Ponte tambem em folha")
        dono[uid], tipos[uid] = "ponte_" + uid, "faixa_transversal"
    for uid, tipo in ctx["margem"].items():
        exigir(uid not in dono, "Margem tambem no corpo")
        dono[uid], tipos[uid] = "margem_" + tipo, tipo
    exigir(set(dono) == set(ordem), "Estrutura nao cobre pagina")
    for uid in ordem:
        tipo = c.tipo_unidade(ctx["mapa"][uid])
        if tipo != "texto":
            dono[uid], tipos[uid] = "atomo_" + uid, tipo
    # Cada atomo/faixa corta a folha em trechos menores na ordem da regra.
    segmentos = []
    for _, grupo in itertools.groupby(ordem, key=dono.__getitem__):
        us = list(grupo)
        segmentos.append({"id": f"s{len(segmentos)}", "unidades": us,
                          "tipo": tipos[us[0]], "origem": dono[us[0]],
                          "bbox": e.o.envelope([ctx["mapa"][u]["bbox"] for u in us])})
    exigir([u for s in segmentos for u in s["unidades"]] == ordem,
           "Segmentos nao reproduzem regra")
    return segmentos, rastros


def diagnostico(segmentos, ctx, q, trs):
    su = {u: s["id"] for s in segmentos for u in s["unidades"]}
    sw = {k: su[u] for u, ks in ctx["exp"].items() for k in ks}
    exigir(sorted(sw) == list(range(len(ctx["ws"]))), "Cobertura incompleta")
    runs = collections.Counter(k for k, _ in itertools.groupby([sw[k] for k in q["gt_w"]]))
    dentro = sum(su[t["a"]] == su[t["z"]] for t in trs)
    ww = sum(sw[a] == sw[z] for a, z in zip(q["gt_w"], q["gt_w"][1:]))
    por = [{**s, "palavras": sum(len(ctx["exp"][u]) for u in s["unidades"]),
            "visitas_ouro": runs[s["id"]], "violado": runs[s["id"]] > 1}
           for s in segmentos]
    return {"segmentos": por, "n_segmentos": len(por), "cobertura_unidades": 1.,
            "cobertura_palavras": 1., "sucessores_ouro": len(trs),
            "sucessores_dentro": dentro, "sucessores_entre": len(trs)-dentro,
            "palavras_sucessores_dentro": ww,
            "palavras_sucessores_entre": len(q["gt_w"])-1-ww,
            "violados": sum(s["violado"] for s in por),
            "visitas_excedentes": sum(max(0, x-1) for x in runs.values()),
            "sem_ouro": sum(not s["visitas_ouro"] for s in por)}


def resolver_milp(custos, lower, upper, inteiros, linhas):
    """Otimizacao esparsa, exata; nunca aceita incumbente sem prova."""
    ri, ci, vs, lo, hi = [], [], [], [], []
    for j, (coef, a, z) in enumerate(linhas):
        for i, valor in coef.items():
            ri.append(j); ci.append(i); vs.append(float(valor))
        lo.append(a); hi.append(z)
    A = coo_matrix((vs, (ri, ci)), shape=(len(linhas), len(custos))).tocsc()
    vigiar()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected")
        res = milp(np.asarray(custos, dtype=float), integrality=np.asarray(inteiros),
                   bounds=Bounds(lower, upper),
                   constraints=LinearConstraint(A, lo, hi),
                   options={"time_limit": 60., "mip_rel_gap": 0., "threads": 4,
                            "random_seed": 0})
    exigir(res.success and res.status == 0 and getattr(res, "mip_gap", 0.) <= 1e-9,
           "Oraculo sem prova de otimalidade; cache preservado: " + str(res.message))
    return res


def ordenar_ouro(blocos, exp, gt):
    """Ordem de blocos com tau maximo; intercalacoes nao viram perfeicao ficticia.

    Intervalos disjuntos do ouro tem precedencia obrigatoria no otimo. Somente
    componentes sobrepostas exigem DP exata ou MILP de ordenacao linear. A
    expansao de palavras dentro de cada bloco permanece imutavel.
    """
    rank = {k: i for i, k in enumerate(gt)}
    ranks = {u: sorted(rank[k] for k in exp[u] if k in rank) for u in blocos}
    vazios = [u for u in blocos if not ranks[u]]
    eleg = sorted((u for u in blocos if ranks[u]), key=lambda u: (ranks[u][0], u))
    comps = []
    fim = -1
    for u in eleg:
        if ranks[u][0] > fim:
            comps.append([])
        comps[-1].append(u)
        fim = max(fim, ranks[u][-1])
    resultado, detalhes = [], []
    for comp in comps:
        n = len(comp)
        if n == 1:
            resultado += comp
            continue
        custo = np.zeros((n, n), dtype=np.int64)
        for i, u in enumerate(comp):
            for j, v in enumerate(comp):
                if i != j:
                    custo[i, j] = np.searchsorted(ranks[v], ranks[u]).sum()
        if n <= 16:
            @lru_cache(None)
            def dp(mask):
                if not mask:
                    return 0, ()
                melhor = None
                for j in range(n):
                    if mask & (1 << j):
                        anterior = mask ^ (1 << j)
                        valor, seq = dp(anterior)
                        candidato = (valor + sum(int(custo[i, j]) for i in range(n)
                                                if anterior & (1 << i)), seq + (j,))
                        if melhor is None or candidato < melhor:
                            melhor = candidato
                return melhor
            valor, seq = dp((1 << n)-1)
            dp.cache_clear()
        else:
            pares = [(i, j) for i in range(n) for j in range(i+1, n)]
            custos = [int(custo[i, j]-custo[j, i]) for i, j in pares] + [0.]*n
            m = len(pares)
            restr = []
            for z, (i, j) in enumerate(pares):
                restr += [({m+j: 1, m+i: -1, z: -n}, 1-n, math.inf),
                          ({m+j: 1, m+i: -1, z: -n}, -math.inf, -1)]
            res = resolver_milp(custos, [0.]*(m+n), [1.]*m+[n-1.]*n,
                                 [1]*m+[0]*n, restr)
            seq = tuple(sorted(range(n), key=lambda i: res.x[m+i]))
            valor = sum(int(custo[i, j]) for a, i in enumerate(seq) for j in seq[a+1:])
        resultado += [comp[i] for i in seq]
        detalhes.append({"blocos": n, "inversoes_entre": valor, "exato": True})
    return resultado + vazios, detalhes


def oraculo_quebras(segmentos, ctx, q):
    """Minimo exato de quebras sob a particao e unidades canonicas.

    Toda quebra e N_ouro-1 menos adjacencias de palavras certas. As internas
    as unidades sao constantes. Cada fronteira que pode preservar uma
    sucessao-ouro e uma variavel binaria. Postos locais impedem ciclos e
    prendem as pontas; postos dos segmentos impedem revisitas. As cadeias
    restantes sempre podem ser empacotadas. A reconstrucao e conferida com
    eventos() oficial: o objetivo provado precisa fechar exatamente.
    """
    exp, gt = ctx["exp"], q["gt_w"]
    segs = {s["id"]: [u for u in s["unidades"] if exp[u]] for s in segmentos}
    segs = {s: us for s, us in segs.items() if us}
    us = [u for vv in segs.values() for u in vv]
    dono = {u: s for s, vv in segs.items() for u in vv}
    prox = dict(zip(gt, gt[1:]))
    inicios = {exp[u][0]: u for u in us}
    edges = [(u, inicios[prox[exp[u][-1]]]) for u in us
             if exp[u][-1] in prox and prox[exp[u][-1]] in inicios
             and inicios[prox[exp[u][-1]]] != u]
    ne = len(edges)
    iu = {u: ne+i for i, u in enumerate(us)}
    iss = {s: ne+len(us)+i for i, s in enumerate(segs)}
    custos = [-1.]*ne + [0.]*(len(us)+len(segs))
    lower = [0.]*len(custos)
    upper = [1.]*ne + [len(segs[dono[u]])-1. for u in us] + [len(segs)-1.]*len(segs)
    restr, incoming, outgoing = [], collections.defaultdict(list), collections.defaultdict(list)
    for i, (u, v) in enumerate(edges):
        a, z = dono[u], dono[v]
        if a == z:
            M = len(segs[a])
            restr += [({iu[v]: 1, iu[u]: -1, i: -M}, 1-M, math.inf),
                      ({iu[v]: 1, iu[u]: -1, i: M}, -math.inf, 1+M)]
        else:
            outgoing[a].append(i); incoming[z].append(i)
            restr += [({iu[u]: 1, i: -(len(segs[a])-1)}, 0, math.inf),
                      ({iu[v]: 1, i: len(segs[z])-1}, -math.inf, len(segs[z])-1)]
            M = len(segs)
            restr += [({iss[z]: 1, iss[a]: -1, i: -M}, 1-M, math.inf),
                      ({iss[z]: 1, iss[a]: -1, i: M}, -math.inf, 1+M)]
    for grupos in (incoming, outgoing):
        for es in grupos.values():
            restr.append(({i: 1 for i in es}, -math.inf, 1))
    if ne:
        res = resolver_milp(custos, lower, upper, [1]*ne+[0]*(len(custos)-ne), restr)
        escolhidas = [edges[i] for i in range(ne) if res.x[i] > .5]
    else:
        escolhidas = []
    sin, sout, saida = {}, {}, {u: None for u in us}
    for u, v in escolhidas:
        a, z = dono[u], dono[v]
        if a == z:
            saida[u] = v
        else:
            sin[z], sout[a] = v, u
    internas = {}
    for s, vv in segs.items():
        chains = h.cadeias(vv, {u: saida[u] for u in vv})
        primeiro = next((ch for ch in chains if ch[0] == sin.get(s)), None)
        ultimo = next((ch for ch in chains if ch[-1] == sout.get(s)), None)
        if primeiro is not None and primeiro is ultimo:
            exigir(len(chains) == 1, "Pontas da mesma cadeia nao cobrem segmento")
            internas[s] = primeiro
            continue
        livres = [ch for ch in chains if ch is not primeiro and ch is not ultimo]
        ex = {str(i): [k for u in ch for k in exp[u]] for i, ch in enumerate(livres)}
        ordem, _ = ordenar_ouro(list(ex), ex, gt)
        internas[s] = (primeiro or []) + [u for i in ordem for u in livres[int(i)]] + (ultimo or [])
    ss = {s: None for s in segs}
    for u, v in escolhidas:
        if dono[u] != dono[v]:
            ss[dono[u]] = dono[v]
    chains = h.cadeias(list(segs), ss)
    ex = {str(i): [k for s in ch for u in internas[s] for k in exp[u]]
          for i, ch in enumerate(chains)}
    ordem, _ = ordenar_ouro(list(ex), ex, gt)
    segord = [s for i in ordem for s in chains[int(i)]]
    completos = {s["id"]: s for s in segmentos}
    resultado = []
    for s in segord:
        resultado += internas[s] + [u for u in completos[s]["unidades"] if not exp[u]]
    resultado += [u for s in segmentos if s["id"] not in segs for u in s["unidades"]]
    certos_internos = sum(max(0, sum(k in set(gt) for k in exp[u])-1) -
                           len(e.eventos(exp[u], gt)) for u in us)
    piso = len(gt)-1-certos_internos-len(escolhidas)
    seq = [k for u in resultado for k in exp[u]]
    exigir(len(e.eventos(seq, gt)) == piso, "Otimo de quebras nao fecha com regua")
    return resultado, {"minimo_quebras": piso, "otimo_provado": True,
                       "arestas_possiveis": ne, "arestas_preservadas": len(escolhidas)}


def escores(co, p, ctx):
    global MODELO
    path = EXEC / "escores" / co / (e.ac.chave(p["page_id"]) + ".json")
    if path.exists():
        row = b.ler(path)
        exigir(row["entrada"] == ctx["entrada"], "Cache de escores divergente")
        return dict(((u, v), x) for u, v, x in row["escores"])
    if MODELO is None:
        import lightgbm as lgb
        MODELO = lgb.Booster(model_file=str(FONTE / "modelo.txt"))
    _, cand, extras = g.candidatos(ctx)
    X, edges = g.matriz_features(ctx, cand[32], extras)
    z = MODELO.predict(X, raw_score=True, num_threads=4)
    cal = INFO["calibracao"]
    probs = dict(zip(edges, g.expit(cal["a"]*z + cal["b"]).tolist()))
    gravar(path, {"page_id": p["page_id"], "entrada": ctx["entrada"],
                  "escores": [[u, v, x] for (u, v), x in probs.items()]})
    return probs


def hier1(segmentos, ctx, cand, probs):
    """Decodifica candidatos E004 filtrados; FIM calibrado sempre preservado."""
    internas = {}
    for s in segmentos:
        us = s["unidades"]
        conjunto = set(us)
        candidatos = {u: [v for v in cand[u] if v is None or v in conjunto] for u in us}
        internas[s["id"]] = g.decodificar({**ctx, "ordem": us}, candidatos, probs, CFG)
    return internas


def salvo_hibrido(co, p, ctx):
    if len(ctx["cs"]) > 67:
        return ctx["ordem"]
    if co == "validacao_silver":
        path = RAIZ / "resultados/e006_residual/predicoes_rn" / (e.ac.chave(p["page_id"]) + ".json")
        r = ler(path, pagina=True)
        exigir(r["pagina_sha256"] == c.digest(p), "RN LayoutReader de outra segmentacao")
        return r["ordem"]
    path = b.OUT / "pred" / f"layoutreader_pronto__linhas__{co}.jsonl"
    rs = [r for r in o.linhas_seguras(path) if r["page_id"] == p["page_id"]]
    exigir(len(rs) == 1, "LayoutReader ausente/duplicado")
    return rs[0]["ordem"]


def processar(co, obj, p):
    path = EXEC / "paginas" / co / (e.ac.chave(p["page_id"]) + ".json")
    fp = c.digest([obj, p])
    if path.exists():
        row = b.ler(path)
        exigir(row["fonte_pagina"] == fp, "Cache de pagina divergente")
        for nome, sha in row["fontes_pagina"].items():
            exigir(c.sha(fonte(RAIZ / nome)) == sha, "Fonte do cache mudou: " + nome)
        return row
    anteriores = set(FONTES)
    t0 = time.perf_counter()
    ctx, trs, q = g.preparar_pagina(obj, p)
    entrada = list(range(len(ctx["cs"])))
    random.Random(f"entrada-{p['page_id']}").shuffle(entrada)
    exigir(ctx["entrada"] == [ctx["cs"][i]["id"] for i in entrada], "Embaralhamento mudou")
    segmentos, rastro = segmentar(ctx)
    diag = diagnostico(segmentos, ctx, q, trs)
    probs = escores(co, p, ctx)
    _, candidatos, _ = g.candidatos(ctx)
    igrafo = hier1(segmentos, ctx, candidatos[24], probs)
    interna, otim = {}, []
    for s in segmentos:
        interna[s["id"]], ds = ordenar_ouro(s["unidades"], ctx["exp"], q["gt_w"])
        otim += ds
    sx = {s["id"]: [k for u in s["unidades"] for k in ctx["exp"][u]] for s in segmentos}
    sgold, ds = ordenar_ouro(list(sx), sx, q["gt_w"])
    otim += ds
    sr = list(sx)
    achatar = lambda ss, ii: [u for s in ss for u in ii[s]]
    ordens = {"regra": ctx["ordem"], "hibrido67": salvo_hibrido(co, p, ctx),
              GRAFO: g.decodificar(ctx, candidatos[24], probs, CFG),
              "oraculo_hierarquico": achatar(sgold, interna),
              "oraculo_interna_segmentos_regra": achatar(sr, interna),
              "oraculo_segmentos_interna_grafo": achatar(sgold, igrafo),
              "hier1": achatar(sr, igrafo)}
    ordens["oraculo_hierarquico_quebras"], otqb = oraculo_quebras(segmentos, ctx, q)
    antigo = ler(FONTE / "inferencia" / co / (e.ac.chave(p["page_id"]) + ".json"), pagina=True)
    exigir(antigo["resultados"][GRAFO]["ordem"] == ordens[GRAFO], "E004 nao reproduzido")
    plano = ler(FONTE2 / co / (o.hashlib.sha256(p["page_id"].encode("utf-8")).hexdigest()+".json"), pagina=True)
    exigir(plano["resultados"]["regra_colunas"]["ordem"] == ctx["ordem"], "E002 de outra representacao")
    plano = plano["resultados"]["oraculo_decodificador_matching_K32"]
    plano_medido, _, _, _ = c.medir(obj, p, plano["ordem"])
    exigir(all(abs(plano_medido[k]-plano["metricas"][k]) < 1e-11 for k in o.METRICAS),
           "Teto plano do E002 nao reproduzido")
    resultados, corpo, hits, iguais = {}, {}, {}, {}
    for nome, ordem in ordens.items():
        key = tuple(ordem)
        if key not in iguais:
            iguais[key] = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
        resultados[nome] = iguais[key]
        corpo[nome] = h.avaliar_corpo(q, ctx, ordem)
        seq = [k for u in ordem for k in ctx["exp"][u]]
        hits[nome] = o.lm.acertos(q, seq, trs, resultados[nome]["metricas"])
        exigir(all(resultados[nome]["metricas"][k] is not None for k in o.METRICAS),
               "Metrica principal indefinida")
        if nome in ("regra", GRAFO) or (nome == "hibrido67" and nome in antigo["resultados"]):
            for k in o.METRICAS:
                exigir(abs(resultados[nome]["metricas"][k]-antigo["resultados"][nome]["metricas"][k]) < 1e-11,
                       "Controle difere do E004: " + nome + "/" + k)
    pares = {nome: {base: {tipo: {
        "reparos": sum(new and not old for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo),
        "regressoes": sum(old and not new for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo)}
        for tipo in c.TIPOS} for base in ("regra", "hibrido67", GRAFO)} for nome, nh in hits.items()}
    row = {"page_id": p["page_id"], "uf": obj["uf"], "fonte_pagina": fp,
           "resultados": resultados, "corpo": corpo, "pares_sucessor": pares,
           "diagnostico": diag, "rastro_regra": rastro, "otimos_tau": otim,
           "otimo_quebras": otqb, "teto_plano_e002": plano_medido,
           "fontes_pagina": {k: v for k, v in FONTES.items() if k not in anteriores},
           "segundos": time.perf_counter()-t0}
    gravar(path, row)
    return row


def portao(dados, resumos, teto):
    media = lambda m, k: statistics.mean(resumos[co][m]["metricas"][k]["media"] for co in COORTES)
    tau_h = media("hibrido67", "tau")
    tau_o = media("oraculo_hierarquico", "tau")
    qr, qg, q1 = (media(m, "quebras") for m in ("regra", GRAFO, "hier1"))
    ganho = (qr-q1)/(qr-qg)
    # Cada bancada conserva o proprio teto plano E002; 1,05 no v4 e arredondado.
    # Usa valor exato salvo; nao troca a tolerancia 30% do cartao.
    limites = {co: 1.3*teto[co]["quebras"] for co in COORTES}
    qb_o = {co: resumos[co]["oraculo_hierarquico"]["metricas"]["quebras"]["media"] for co in COORTES}
    minqb = {co: resumos[co]["oraculo_hierarquico_quebras"]["metricas"]["quebras"]["media"] for co in COORTES}
    checks = {"oraculo_tau": tau_o >= tau_h-.005-1e-12,
              "oraculo_quebras": all(qb_o[co] <= limites[co]+1e-12 for co in COORTES),
              "hier1_retencao": ganho >= .7-1e-12}
    # IC do ajuste = media das medias das bancadas, bootstrap independente
    # por veiculo em cada bancada (RN tem um grupo). Funcoes oficiais.
    dist = []
    for co in COORTES:
        rs = dados[co]
        ds = np.array([r["resultados"]["hier1"]["metricas"]["tau"] -
                       r["resultados"]["hibrido67"]["metricas"]["tau"] for r in rs])
        W = b.PESOS_CLUSTER(rs)
        dist.append((W @ ds)/W.sum(axis=1))
    ic = np.percentile((dist[0]+dist[1])/2, [2.5, 97.5]).tolist()
    checks["hier1_tau_ic"] = ic[0] >= -.005-1e-12
    impossivel = any(minqb[co] > limites[co]+1e-12 for co in COORTES) or not checks["oraculo_tau"]
    passou = all(checks.values())
    if passou:
        veredito = "GO da fase 1; fase 2 não executada."
    elif impossivel:
        veredito = "NÃO GO da fase 1: o oráculo não passa; encerrar esta linha do grafo conforme o cartão."
    elif not checks["oraculo_quebras"]:
        veredito = "NÃO GO da fase 1 para a ordem oracular de τ; limites separados não provam inviabilidade conjunta."
    else:
        veredito = "NÃO GO da fase 1: HIER-1 não atende ao portão; nenhuma externa foi executada."
    return {"veredito": veredito, "passou": passou, "criterios": checks,
            "tau_oraculo": tau_o, "tau_hibrido": tau_h, "retencao_ganho_e004": ganho,
            "hier1_delta_tau": media("hier1", "tau")-tau_h, "hier1_delta_tau_ic95": ic,
            "limites_quebras": limites, "quebras_oraculo": qb_o,
            "minimo_quebras_provado": minqb, "inviabilidade_provada": impossivel}


def relatorio(dados, resumos, an, gate):
    f, ic = o.f, o.ic
    linhas = [f"1. Âncora reproduzida no golden_v4: τ {f(an['tau'],6)}; {f(an['quebras'],6)} quebras/página.",
              "2. Fase 1 executada somente em golden_v4 e validação silver RN, com linhas + átomos ls3 e cobertura integral.",
              "3. Segmentação e violações do ouro: " + "; ".join(
                  co+f": {f(statistics.mean(r['diagnostico']['n_segmentos'] for r in rs),3)} segmentos/página, "
                  f"{sum(r['diagnostico']['violados'] for r in rs)} segmentos violados" for co, rs in dados.items())+".",
              f"4. HIER-1 retém {f(100*gate['retencao_ganho_e004'],2)}% da redução do E004; Δτ vs híbrido {f(gate['hier1_delta_tau'],6)} "
              f"[{f(gate['hier1_delta_tau_ic95'][0],6)}; {f(gate['hier1_delta_tau_ic95'][1],6)}] no ajuste.",
              "5. Golden_v3_novo já foi consultado em rodadas anteriores; externas e teste cego não foram abertos nesta fase.",
              "6. Veredito: "+gate["veredito"], "", "# E016 — Oráculo hierárquico e HIER-1", "",
              "## Execução e definições", "",
              "CPU, quatro threads, um processo, num_workers=0, sem retreino. A regra é reexecutada antes de qualquer número novo. "
              "Entrada embaralhada pelo protocolo e conferida com random.Random(f'entrada-{page_id}'). "
              "Toda medição usa erros_ponta_a_ponta, bancada_ordenadores e avaliar_ordem do E002; "
              "não se reimplementam τ, quebras, fidelidade ou sucessor. Fontes e hashes estão no manifesto/estado. "
              "Saídas por página e escores calibrados permitem retomada após queda.", "",
              "Segmentos: folhas terminais da recursão ordenar_projecao(local=True), observadas no retorno da própria função; "
              "cada faixa transversal que a regra detecta é singleton e já corta as colunas acima/abaixo. "
              "Topo, marca e rodapé são grupos separados pela partição geométrica original. "
              "Cada átomo tabela/imagem é singleton e corta sua folha em trechos anteriores/posteriores na ordem da regra. "
              "Não há limiar novo, título semântico, caixa humana nem referência na segmentação. "
              "A concatenação dos segmentos na ordem da regra reproduz exatamente a regra; nenhuma palavra/unidade é removida. "
              "Quando não há vale detectável, a folha conserva o fallback XY-cut da regra: não se inventa uma coluna.", "",
              "HIER-1 filtra os candidatos K24 enriquecidos do E004 à mesma partição, conserva FIM e os escores Platt originais "
              "e chama o max-regret importado em cada segmento. Features e probabilidades são as da página inteira, "
              "antes de qualquer filtro. Segmentos seguem a regra. O grafo plano é reproduzido por página contra o cache congelado.", "",
              "Oráculo hierárquico: ordem interna e entre segmentos com τ de palavras máximo, respeitando unidades/átomos "
              "e suas expansões canônicas. Componentes de intervalos-ouro sobrepostos são resolvidas exatamente por DP/MILP. "
              "Ouro que reentra num segmento ou unidade pode impedir τ=1: nenhuma partição ou átomo é desfeito. "
              "As quebras são medidas na mesma ordem, não combinadas com τ de outra predição. "
              "Oráculos parciais: interna perfeita + segmentos pela regra; interna pelo E004 local + segmentos perfeitos. "
              "Um controle adicional calcula o mínimo exato de quebras permitido pela partição via MILP esparso de "
              "adjacências-ouro, sem candidatos K. O objetivo provado é conferido com eventos() oficial na sequência reconstruída. "
              "Esse mínimo é um certificado para rejeitar a hierarquia se exceder o limite, mesmo quando outra ordem poderia ter τ maior. "
              "A ordem desse controle minimiza quebras; o desempate entre soluções não garante o maior τ.", "",
              f"IC95 percentil por veículo: {b.NBOOT} reamostras, semente {b.SEMENTE}, funções importadas. "
              "Médias por página dentro de cada bancada. Ajuste conjunto = média de v4 e RN com peso igual, como E004/E014; "
              "IC conjunto = média das reamostras independentes das duas bancadas. "
              "Wilcoxon Pratt bilateral sobre as médias de Δ de cada veículo; p descritivo, sem seleção por p. "
              "RN tem um veículo, portanto seu IC degenera. As três bancadas oficiais permanecem separadas: "
              "somente golden_v4 é executada; golden_v3_novo e teste silver são externas não executadas. "
              "RN aparece separadamente como apêndice de ajuste. Sem somar páginas entre bancadas.", "",
              "## Portão da fase 1", "",
              "Critérios do cartão preservados: oráculo τ ≥ híbrido − 0,005; quebras ≤ 1,30 × teto plano E002 de cada bancada "
              "(o 1,05 do cartão é o arredondamento do valor exato salvo no v4); HIER-1 retém ≥70% da redução absoluta "
              "de quebras do E004 contra a regra, e limite inferior do IC95 de Δτ vs híbrido ≥−0,005 no ajuste. "
              "Relatam-se também resultados por bancada para expor heterogeneidade. Nenhuma externa é acionada pelo script.", "",
              "| Condição | Resultado |", "|---|---|"]
    for k, v in gate["criterios"].items():
        linhas.append(f"| {k} | {'PASSA' if v else 'FALHA'} |")
    linhas += ["", "| Bancada | Limite de quebras | Quebras na ordem de τ máximo | Mínimo de quebras provado |",
               "|---|---:|---:|---:|"]
    for co in COORTES:
        linhas.append(f"| {co} | {f(gate['limites_quebras'][co],6)} | {f(gate['quebras_oraculo'][co],6)} | {f(gate['minimo_quebras_provado'][co],6)} |")
    linhas += ["", "**"+gate["veredito"]+"**", ""]
    registro = {}
    for co in COORTES:
        rs, rr = dados[co], resumos[co]
        ds = [r["diagnostico"] for r in rs]
        soma = lambda k: sum(d[k] for d in ds)
        linhas += [f"## {co} — ajuste", "",
                   f"{len(rs)} páginas; {len({r['uf'] for r in rs})} veículos. "
                   f"Segmentos por página: média {f(statistics.mean(d['n_segmentos'] for d in ds),3)}, "
                   f"mínimo {min(d['n_segmentos'] for d in ds)}, máximo {max(d['n_segmentos'] for d in ds)}. "
                   f"Cobertura de unidades e palavras: {f(100*min(d['cobertura_palavras'] for d in ds),1)}% em todas as páginas.", "",
                   f"Sucessores-ouro de linhas (pontas atribuídas por IDs de palavra): {soma('sucessores_dentro')}/{soma('sucessores_ouro')} "
                   f"dentro ({f(100*soma('sucessores_dentro')/soma('sucessores_ouro'),2)}%); "
                   f"{soma('sucessores_entre')}/{soma('sucessores_ouro')} entre segmentos "
                   f"({f(100*soma('sucessores_entre')/soma('sucessores_ouro'),2)}%). "
                   f"Segmentos violados: {soma('violados')}/{soma('n_segmentos')}; visitas excedentes: {soma('visitas_excedentes')}; "
                   f"segmentos sem ouro: {soma('sem_ouro')}. Violado = mais de uma visita no fluxo de palavras-ouro; "
                   "linhas humanas que atravessam segmentos podem ter suas pontas em partições diferentes.", "",
                   "| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |",
                   "|---|---:|---:|---:|---:|---:|"]
        for nome, s in rr.items():
            mm = {k: v["media"] for k, v in s["metricas"].items()}
            linhas.append(f"| {nome} | "+" | ".join(f(mm[k],6) for k in o.METRICAS)+" |")
            registro[co+"/"+nome] = {"tau": mm["tau"], "quebras": mm["quebras"], "sucessor": mm["sucessor_linhas"]}
        linhas += ["", "### Qual nível limita", "",
                   "Substituições oraculares a partir do HIER-1, uma de cada vez. Δ = oráculo parcial − HIER-1; "
                   "valor negativo de quebras indica potencial de reparo. As ordens maximizam τ, por isso não são "
                   "limites independentes de quebras nem parcelas que possam ser somadas.", "",
                   "| Nível substituído pelo ouro | Δτ | Δ quebras/pág |", "|---|---:|---:|"]
        for titulo, nome in (("interno; segmentos continuam pela regra", "oraculo_interna_segmentos_regra"),
                             ("entre segmentos; interna continua pelo grafo", "oraculo_segmentos_interna_grafo")):
            dt = rr[nome]["metricas"]["tau"]["media"]-rr["hier1"]["metricas"]["tau"]["media"]
            dq = rr[nome]["metricas"]["quebras"]["media"]-rr["hier1"]["metricas"]["quebras"]["media"]
            linhas.append(f"| {titulo} | {f(dt,6)} | {f(dq,6)} |")
        qint = rr["oraculo_interna_segmentos_regra"]["metricas"]["quebras"]["media"]
        qseg = rr["oraculo_segmentos_interna_grafo"]["metricas"]["quebras"]["media"]
        linhas += ["", "Neste diagnóstico, a substituição " +
                   ("interna" if qint < qseg else "entre segmentos" if qseg < qint else "dos dois níveis empata") +
                   " oferece o maior reparo de quebras. " +
                   ("Mesmo com ambos os níveis livres para escolher o mínimo de quebras, a partição falha no limite do cartão."
                    if gate["minimo_quebras_provado"][co] > gate["limites_quebras"][co] else
                    "O mínimo de quebras desta bancada cabe no limite; isso sozinho não certifica a condição conjunta de τ e quebras."), ""]
        linhas += ["", "### Δ pareado, IC95 e Wilcoxon por veículo", "",
                   "M/I/P = páginas que melhoram/igualam/pioram, respeitando o sentido de cada métrica.", "",
                   "| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |",
                   "|---|---|---|---:|---:|---:|"]
        for nome, s in rr.items():
            if nome in ("regra", "hibrido67"):
                continue
            for base in ("regra", "hibrido67"):
                for k, d in s["contrastes"][base].items():
                    linhas.append(f"| {nome} | {base} | {k} | {ic(d,6)} | {f(d['wilcoxon_veiculo']['p'],6)} | "
                                  f"{d['melhor']}/{d['igual']}/{d['pior']} |")
        linhas += ["", "### Sucessores: reparos e regressões por classe", "",
                   "| Método | Base | Classe | Reparos | Regressões |", "|---|---|---|---:|---:|"]
        for nome in METODOS[3:]:
            for base in ("regra", "hibrido67"):
                for tipo, cc in rr[nome]["pares_sucessor"][base].items():
                    linhas.append(f"| {nome} | {base} | {tipo} | {cc['reparos']} | {cc['regressoes']} |")
        linhas += ["", "### Corpo sem margens — diagnóstico", "",
                   "Mesma exclusão automática para todos os métodos, importada do E014; sem seleção.", "",
                   "| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |", "|---|---:|---:|---:|---:|"]
        for nome, s in rr.items():
            linhas.append(f"| {nome} | "+" | ".join(f(s["corpo"][k]["media"],6)
                          for k in ("tau", "quebras", "fid12", "sucessor_linhas"))+" |")
        linhas += ["", "### HIER-1: diferenças por veículo", "",
                   "| Veículo | Δτ vs regra | Δ quebras vs regra | Δτ vs híbrido | Δ quebras vs híbrido |",
                   "|---|---:|---:|---:|---:|"]
        for uf in sorted({r["uf"] for r in rs}):
            vals = [rr["hier1"]["contrastes"][base][k]["por_veiculo"][uf]
                    for base in ("regra", "hibrido67") for k in ("tau", "quebras")]
            linhas.append(f"| {uf} | "+" | ".join(f(v,6) for v in vals)+" |")
        linhas += ["", "### Segmentação por página", "",
                   "| Página | Segmentos | Cobertura | Ouro linhas dentro/entre | Segmentos violados | Mínimo quebras |",
                   "|---|---:|---:|---:|---:|---:|"]
        for r in rs:
            d = r["diagnostico"]
            linhas.append(f"| `{r['page_id']}` | {d['n_segmentos']} | {f(100*d['cobertura_palavras'],1)}% | "
                          f"{d['sucessores_dentro']}/{d['sucessores_entre']} | {d['violados']} | {r['otimo_quebras']['minimo_quebras']} |")
        linhas.append("")
    linhas += ["## Bancadas externas", "", "golden_v3_novo: NÃO EXECUTADA. teste silver CE/MA/RJ: NÃO EXECUTADO. "
               "Nenhum arquivo dessas bancadas foi aberto ou avaliado nesta fase. Teste cego preservado.", "",
               "## Limitações", "", "Estudo exploratório, um anotador humano, silver ruidoso e poucos veículos. "
               "Golden_v3_novo já foi consultado em rodadas anteriores e não é confirmatório. RN tem só um veículo; "
               "IC degenerado não representa incerteza entre veículos novos. Fronteiras são as da regra, não fronteiras semânticas de atos. "
               "Título só provoca corte quando reconhecido geometricamente como faixa transversal. "
               "Violações não demonstram erro humano: a hierarquia e as unidades automáticas podem ser incompatíveis com o ouro. "
               "Não se confundem mínimo de quebras e máximo de τ de ordens diferentes; a decisão inclui certificado de inviabilidade "
               "quando o mínimo de quebras já excede o limite. Ganho local sem segurança de τ não autoriza fase 2. "
               "Nenhuma anotação, dado, cartão, documentação, registro compartilhado ou modelo foi alterado.", ""]
    return "\n".join(linhas), registro


def autoteste():
    """Confere otimos contra enumeracao em exemplos pequenos intercalados."""
    casos = [({"a": [0, 1], "b": [2, 3], "c": [4]}, [["a", "c"], ["b"]]),
             ({"a": [0, 3], "b": [1, 2], "c": [4]}, [["a", "b"], ["c"]]),
             ({"a": [2, 0], "b": [1, 3], "c": [4]}, [["a", "b"], ["c"]]),
             ({"a": [0], "b": [1], "c": [2]}, [["a", "c"], ["b"]])]
    casos = [(exp, groups, list(range(sum(map(len, exp.values()))))) for exp, groups in casos]
    rng = random.Random(20261103)
    for _ in range(40):
        ids = list("abcd")
        ws = list(range(7))
        rng.shuffle(ws)
        exp = {u: [] for u in ids}
        for k in ws:
            exp[rng.choice(ids)].append(k)
        rng.shuffle(ids)
        corte = rng.randrange(1, len(ids))
        # Inclui unidades vazias, livres, atomos intercalados e ciclos possiveis.
        gt = sorted(rng.sample(range(7), rng.randrange(3, 8)))
        casos.append((exp, [ids[:corte], ids[corte:]], gt))
    for exp, groups, gt in casos:
        segs = [{"id": str(i), "unidades": us} for i, us in enumerate(groups)]
        ordem, diag = oraculo_quebras(segs, {"exp": exp}, {"gt_w": gt})
        possibilidades = []
        for sg in itertools.permutations(groups):
            for internas in itertools.product(*(list(itertools.permutations(us)) for us in sg)):
                possibilidades.append([u for vv in internas for u in vv])
        minimo = min(len(e.eventos([k for u in seq for k in exp[u]], gt)) for seq in possibilidades)
        exigir(diag["minimo_quebras"] == minimo, "MILP diverge da enumeracao")
        interna = {s["id"]: ordenar_ouro(s["unidades"], exp, gt)[0] for s in segs}
        sx = {s["id"]: [k for u in s["unidades"] for k in exp[u]] for s in segs}
        ss, _ = ordenar_ouro(list(sx), sx, gt)
        pred = [k for s in ss for u in interna[s] for k in exp[u]]
        maxtau = max(e.o.kendall_tau([k for u in seq for k in exp[u]], gt) for seq in possibilidades)
        exigir(abs(e.o.kendall_tau(pred, gt)-maxtau) < 1e-12, "Oraculo tau diverge da enumeracao")
    exp = {f"u{i:02d}": [i, i+17] for i in range(17)}
    esperado = sorted(exp)
    ordem, _ = ordenar_ouro(esperado[::-1], exp, list(range(34)))
    exigir(ordem == esperado, "Ramo MILP de tau nao resolveu componente de 17 blocos")
    print(f"Autoteste: {len(casos)} casos com enumeracao; mais componente de 17 blocos no MILP de tau.", flush=True)


def main():
    global LOCK_SHA, PRAZO
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--somente-ancora", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--max-minutos", type=float, default=45.)
    args = ap.parse_args()
    LOCK_SHA, o.PROTEGIDOS = o.ler_lock()
    o.PROTEGIDOS.update(x.rsplit("#p", 1)[0] for x in list(o.PROTEGIDOS) if "#p" in x)
    PRAZO = time.monotonic()+60*args.max_minutos
    if "torch" in sys.modules:
        sys.modules["torch"].set_num_threads(4)
    with trava():
        if args.autoteste:
            autoteste()
            return
        # Antes de caches, metricas, diagnosticos ou resultados novos.
        an = o.ancora()
        if args.somente_ancora:
            return
        if args.conferir:
            pointer = b.ler(OUT / "cache/ultima_execucao.json")
            estado = b.ler(OUT / pointer["execucao"] / "estado.json")
            exigir(estado["manifesto"]["lock_sha256"] == LOCK_SHA, "Lacre difere da execucao")
            for nome, sha in estado["fontes"].items():
                exigir(c.sha(RAIZ / nome) == sha, "Fonte mudou: " + nome)
            for co, rs in estado["dados"].items():
                for r in rs:
                    path = OUT / pointer["execucao"] / "paginas" / co / (e.ac.chave(r["page_id"])+".json")
                    exigir(b.ler(path) == r, "Cache por pagina diverge do estado")
            md, registro = relatorio(estado["dados"], estado["resumos"], an, estado["portao"])
            exigir(md == (OUT / "RELATORIO.md").read_text(encoding="utf-8"), "Relatorio diverge do estado")
            exigir(registro == b.ler(OUT / "resumo_registro.json"), "Resumo diverge do estado")
            exigir(all(co in COORTES for co in estado["dados"]), "Estado contem externa")
            print("Conferencia: fontes, relatorio e resumo coerentes; somente ajuste.", flush=True)
            return
        man = iniciar()
        dados = {}
        for co in COORTES:
            dados[co] = []
            for obj, p in paginas(co):
                vigiar()
                row = processar(co, obj, p)
                dados[co].append(row)
                print(f"{co} {len(dados[co])}: {row['diagnostico']['n_segmentos']} segmentos; "
                      f"min quebras {row['otimo_quebras']['minimo_quebras']}; {p['page_id']}", flush=True)
                gc.collect()
        exigir(len(dados["golden_v4"]) == 44 and len(dados["validacao_silver"]) == 15, "Coorte incompleta")
        resumos = {co: h.resumir(rs, METODOS) for co, rs in dados.items()}
        teto = {co: {k: statistics.mean(r["teto_plano_e002"][k] for r in rs)
                      for k in o.METRICAS} for co, rs in dados.items()}
        gate = portao(dados, resumos, teto)
        md, registro = relatorio(dados, resumos, an, gate)
        for nome, sha in FONTES.items():
            exigir(c.sha(RAIZ / nome) == sha, "Fonte alterada durante a execucao: " + nome)
        estado = {"ancora": an, "manifesto": man, "fontes": dict(FONTES),
                  "dados": dados, "resumos": resumos, "portao": gate,
                  "memoria": g.medir_memoria(), "completo": True}
        gravar(EXEC / "estado.json", estado)
        gravar(OUT / "RELATORIO.md", md)
        gravar(OUT / "resumo_registro.json", registro)
        gravar(OUT / "cache/ultima_execucao.json", {"execucao": EXEC.relative_to(OUT).as_posix()})
        print(gate["veredito"], flush=True)
        print(json.dumps(gate, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
