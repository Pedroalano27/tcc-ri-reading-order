"""Recostura o path cover do E004, sem treino, GPU ou escrita nas fontes.

Diagnostica primeiro a perda de tau no ajuste; compara quatro variantes e
congela uma pela regra do cartao antes de abrir as externas. Importa modelo,
features, calibracao, decoder, regua e inferencia de colunas do E004. O perfil
de retorno observa as arestas locais do decoder original sem copia-lo.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e014_cadeias.py
  --etapa diagnostico  # somente golden_v4 e RN
  --etapa ajuste      # congela a selecao, sem abrir externas
  --max-minutos 30    # cache atomico por pagina, retomavel
  --conferir          # confere relatorio e resumo sem nova inferencia
Toda escrita fica em resultados/e014_cadeias/. Uma pagina por vez, CPU/4
threads, sem multiprocessing ou DataLoader; vigia RSS, RAM e commit.
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
import json
import math
import statistics
import time
from contextlib import contextmanager

from orquestracao.analises import e004_grafo as g
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
o, c = g.o, g.c
np = g.np
OUT = RAIZ / "resultados/e014_cadeias"
GRAFO = "grafo_K24_maxregret_t0.00"
VARIANTES = ("a_primeira", "b_mediana", "c_local", "d_local_margens")
CFG = {"K": 24, "decoder": "maxregret", "limiar": 0., "restricao_coluna": False}
PRAZO = None
LOCK_SHA = None
EXEC = None
FONTE = None
MODELO = None
INFO = None
ASSINATURA = None


def exigir(ok, mensagem):
    g.exigir(ok, mensagem)


def gravar(path, obj):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora de E014")
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


def ler(path):
    return b.ler(path) if path.exists() else None


def vigiar():
    if PRAZO is not None and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; repetir retoma paginas prontas")
    exigir(o.ler_lock()[0] == LOCK_SHA, "Lacre cego mudou")
    mem = b.memoria()
    rss = g.medir_memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 800 and mem["commit_livre_mb"] >= 1200,
           "Memoria insuficiente; caches preservados: " + str(mem))
    exigir(rss["pico_rss_mb"] <= 3072, "RSS excedeu 3 GiB; caches preservados")


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if f.tell() == 0:
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


def iniciar():
    """Confere somente fontes, sem desserializar paginas externas."""
    global FONTE, INFO, ASSINATURA, EXEC
    ponteiro = b.ler(g.CACHE / "ultima_execucao.json")
    FONTE = g.OUT / ponteiro["execucao"]
    sel = b.ler(FONTE / "selecao_congelada.json")
    exigir(sel["metodo"] == GRAFO and sel["config"] == CFG, "E004 selecionado mudou")
    INFO = b.ler(FONTE / "modelo.json")
    exigir(INFO["concluido"] and c.sha(FONTE / "modelo.txt") == INFO["sha256"],
           "Modelo E004 ausente ou alterado")
    man = b.ler(g.CACHE / "manifesto.json")
    fontes = {}
    for nome, sha in man["fontes"].items():
        # Nao acessa o treino nem pastas de dados desnecessarias a este teste.
        if nome.startswith("orquestracao/") or nome.startswith("src/") or (
                nome.startswith("resultados/unidades_sem_caixas/") and
                "/linhas_extra/" not in nome and not nome.endswith("treino_noite.json")) or (
                nome.startswith("resultados/ordenadores_sem_caixas/") and "/pred/" in nome) or (
                nome == "data/processed/splits.json"):
            exigir("labelstudio" not in nome, "Fonte proibida")
            exigir(c.sha(RAIZ / nome) == sha, "Fonte E004 mudou: " + nome)
            fontes[nome] = sha
    for path in (Path(__file__), Path(g.__file__), FONTE / "modelo.json",
                 FONTE / "modelo.txt", FONTE / "selecao_congelada.json",
                 *sorted((RAIZ / "experimentos/cards").glob("E014_*.md"))):
        fontes[path.relative_to(RAIZ).as_posix()] = c.sha(path)
    man14 = {"fontes": fontes, "lock_sha256": LOCK_SHA,
             "origem_e004": FONTE.relative_to(RAIZ).as_posix(),
             "config": CFG, "variantes": VARIANTES,
             "ajuste": "media de v4/RN com peso igual; tau >= regra-0.005; menor quebras",
             "treino": False, "cpu": True, "threads": 4, "num_workers": 0}
    ASSINATURA = c.digest(man14)
    EXEC = OUT / "cache" / ASSINATURA
    return man14


def capturar_grafo(ctx, cand, probs):
    """Observa saida no retorno do decoder importado; nao o reimplementa."""
    capturado = {}
    codigo = o.lm.max_regret.__code__
    anterior = sys.getprofile()
    def perfil(frame, evento, arg):
        if evento == "return" and frame.f_code is codigo:
            capturado.update(frame.f_locals["saida"])
    try:
        sys.setprofile(perfil)
        ordem = g.decodificar(ctx, cand, probs, CFG)
    finally:
        sys.setprofile(anterior)
    exigir(set(capturado) == set(ctx["ordem"]), "Captura de arestas incompleta")
    exigir(o.costurar(ctx["ordem"], capturado) == ordem, "Arestas nao reproduzem E004")
    return ordem, capturado


def cadeias(regra, saida):
    entradas = {v for v in saida.values() if v is not None}
    exigir(len(entradas) == sum(v is not None for v in saida.values()), "Entrada duplicada")
    out, vistos = [], set()
    for uid in regra:
        if uid in entradas:
            continue
        atual, u = [], uid
        while u is not None:
            exigir(u not in vistos, "Ciclo nas cadeias")
            atual.append(u)
            vistos.add(u)
            u = saida.get(u)
        out.append(atual)
    exigir(vistos == set(regra), "Cadeias nao cobrem pagina")
    return out


def grafo_pagina(co, obj, p, ctx):
    """Reusa escores calibrados por pagina; nunca escreve no E004."""
    global MODELO
    path = EXEC / "escores" / co / (e.ac.chave(p["page_id"]) + ".json")
    row = ler(path)
    if row:
        exigir(row["entrada"] == ctx["entrada"], "Entrada embaralhada mudou")
        return row
    if MODELO is None:
        import lightgbm as lgb
        MODELO = lgb.Booster(model_file=str(FONTE / "modelo.txt"))
    _, cand, extras = g.candidatos(ctx)
    X, edges = g.matriz_features(ctx, cand[32], extras)
    z = MODELO.predict(X, raw_score=True, num_threads=4)
    cal = INFO["calibracao"]
    probs = dict(zip(edges, g.expit(cal["a"] * z + cal["b"]).tolist()))
    ordem, saida = capturar_grafo(ctx, cand[24], probs)
    antigo = b.ler(FONTE / "inferencia" / co / (e.ac.chave(p["page_id"]) + ".json"))
    exigir(antigo["resultados"][GRAFO]["ordem"] == ordem, "Nao reproduziu a ordem E004")
    row = {"page_id": p["page_id"], "entrada": ctx["entrada"], "ordem": ordem,
           "saida": saida, "escores": [[u, v, s] for (u, v), s in probs.items()]}
    gravar(path, row)
    return row


def inversoes(seq, gt):
    """Contagem derivada do tau oficial, sem implementar outra metrica."""
    if len(seq) < 2:
        return 0
    exigir(set(seq) == set(gt), "Subsequencias nao pareadas")
    return round((1 - e.o.kendall_tau(seq, gt)) * math.comb(len(seq), 2) / 2)


def diagnosticar(obj, p, ctx, row, q):
    """Particiona as inversoes por pertencimento a mesma cadeia do grafo."""
    chains = cadeias(ctx["ordem"], row["saida"])
    gt, rg = q["gt_w"], {k: i for i, k in enumerate(q["gt_w"])}
    dono = {k: i for i, ch in enumerate(chains) for u in ch for k in ctx["exp"][u] if k in rg}
    seq = [k for u in row["ordem"] for k in ctx["exp"][u] if k in rg]
    seqregra = [k for u in ctx["ordem"] for k in ctx["exp"][u] if k in rg]
    gols = {k: L["id"] for L in q["gold_lines"] for k in L["ks"]}
    detalhes = []
    internas_g, internas_r = 0, 0
    for i, ch in enumerate(chains):
        sq = [k for u in ch for k in ctx["exp"][u] if k in rg]
        gg = sorted(sq, key=rg.__getitem__)
        sr = [k for k in seqregra if dono[k] == i]
        inv = inversoes(sq, gg)
        internas_g += inv
        internas_r += inversoes(sr, gg)
        ranks = [rg[k] for k in sq]
        detalhes.append({"cadeia": i, "unidades": ch, "palavras": len(sq),
            "posto_primeira_regra": ctx["rank_regra"][ch[0]],
            "posto_mediano_regra": statistics.median(ctx["rank_regra"][u] for u in ch),
            "linhas": sorted({gols[k] for k in sq}), "inversoes_internas": inv,
            "correta_internamente": inv == 0,
            "contigua_no_ouro": all(z == a+1 for a, z in zip(ranks, ranks[1:])),
            "min": min(ranks) if ranks else -1, "max": max(ranks) if ranks else -1,
            "trechos": [{"id": u, "linhas_ouro": sorted({gols[k] for k in ctx["exp"][u] if k in gols}),
                          "texto": ctx["mapa"][u]["text"][:110]} for u in dict.fromkeys(ch[:2]+ch[-2:])]})
    for i, d in enumerate(detalhes):
        antes = max((x["max"] for x in detalhes[:i]), default=-1)
        depois = min((x["min"] for x in detalhes[i+1:] if x["palavras"]), default=len(gt))
        d["fora_de_ordem"] = bool(d["palavras"] and (antes > d["min"] or depois < d["max"]))
    ig, ir = inversoes(seq, gt), inversoes(seqregra, gt)
    pares = math.comb(len(gt), 2)
    delta_interno = -2*(internas_g-internas_r)/pares
    delta_entre = -2*((ig-internas_g)-(ir-internas_r))/pares
    tau_g, tau_r = e.o.kendall_tau(seq, gt), e.o.kendall_tau(seqregra, gt)
    exigir(abs(delta_interno+delta_entre-(tau_g-tau_r)) < 1e-11, "Decomposicao nao fecha")
    def contagem(ds):
        return {"cadeias": len(ds), "unidades": sum(len(d["unidades"]) for d in ds),
                "palavras": sum(d["palavras"] for d in ds),
                "linhas": len({L for d in ds for L in d["linhas"]})}
    boas_fora = [d for d in detalhes if d["correta_internamente"] and d["fora_de_ordem"]]
    ruins = [d for d in detalhes if not d["correta_internamente"]]
    return {"page_id": p["page_id"], "uf": obj["uf"], "tau_grafo": tau_g,
            "tau_regra": tau_r, "delta_tau": tau_g-tau_r,
            "delta_interno": delta_interno, "delta_entre": delta_entre,
            "inversoes_grafo": ig, "inversoes_regra": ir,
            "inversoes_internas_grafo": internas_g, "inversoes_internas_regra": internas_r,
            "inversoes_entre_grafo": ig-internas_g, "inversoes_entre_regra": ir-internas_r,
            "boas_fora": contagem(boas_fora), "erros_dentro": contagem(ruins),
            "corretas_contiguas_fora": contagem([d for d in boas_fora if d["contigua_no_ouro"]]),
            "cadeias": detalhes}


def executar_diagnostico():
    dados = {}
    for co in o.DESENV:
        dados[co] = []
        for obj, p in o.paginas(co):
            vigiar()
            path = EXEC / "diagnostico" / co / (e.ac.chave(p["page_id"]) + ".json")
            row = ler(path)
            if row is None:
                ctx = c.contexto(p, obj["palavras"])
                gr = grafo_pagina(co, obj, p, ctx)
                row = diagnosticar(obj, p, ctx, gr, b.referencia(obj, p))
                gravar(path, row)
            dados[co].append(row)
            print(f"Diagnóstico {co}: {len(dados[co])}", flush=True)
            gc.collect()
    return dados


def texto_diagnostico(dados):
    f = o.f
    ls = ["## Diagnóstico anterior à seleção (somente ajuste)", "",
          "Cadeia = caminho de arestas efetivamente fixadas pelo max-regret, antes da costura. "
          "Correta internamente = subsequência de palavras sem inversões; contígua exige também "
          "todos os sucessores de palavras corretos. Fora de ordem = participa de inversão com outra cadeia. "
          "Linhas são IDs da referência, unidades são IDs automáticos; uma linha dividida entre cadeias "
          "pode aparecer nas duas categorias. Não se somam conjuntos sobrepostos.", "",
          "As inversões são derivadas do τ importado; sua partição interna/entre cadeias fecha "
          "exatamente a diferença de τ contra a regra. Arestas erradas podem unir trechos remotos "
          "numa só cadeia: nesse caso o erro é interno, mesmo que cada trecho isolado esteja correto.", "",
          "| Ajuste | Inversões internas grafo/regra | Entre grafo/regra | Δτ interno | Δτ entre | "
          "Cadeias boas fora: palavras/linhas/unidades | Cadeias com erro: palavras/linhas/unidades |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    extras = []
    for co, rs in dados.items():
        soma = lambda k: sum(r[k] for r in rs)
        cnt = lambda k: "/".join(str(sum(r[k][v] for r in rs)) for v in ("palavras", "linhas", "unidades"))
        ls.append(f"| {co} | {soma('inversoes_internas_grafo')}/{soma('inversoes_internas_regra')} | "
                  f"{soma('inversoes_entre_grafo')}/{soma('inversoes_entre_regra')} | "
                  f"{f(statistics.mean(r['delta_interno'] for r in rs),6)} | "
                  f"{f(statistics.mean(r['delta_entre'] for r in rs),6)} | {cnt('boas_fora')} | {cnt('erros_dentro')} |")
        cont = {k: sum(r["corretas_contiguas_fora"][k] for r in rs) for k in ("cadeias", "palavras", "linhas")}
        extras.append(f"{co}: subconjunto de cadeias também contíguas fora de ordem: {cont}.")
    ls += ["", *extras, "", "### Cinco maiores quedas de τ no ajuste", ""]
    piores = sorted([r for rs in dados.values() for r in rs], key=lambda r: r["delta_tau"])[:5]
    for r in piores:
        ls += [f"- `{r['page_id']}`: Δτ {f(r['delta_tau'],6)} "
               f"(dentro {f(r['delta_interno'],6)}; entre {f(r['delta_entre'],6)}). "
               f"Inversões internas {r['inversoes_internas_grafo']}, entre {r['inversoes_entre_grafo']}."]
        ds = sorted(r["cadeias"], key=lambda d: (d["inversoes_internas"], d["fora_de_ordem"], d["palavras"]), reverse=True)[:3]
        for d in ds:
            desc = "cadeia internamente errada" if d["inversoes_internas"] else "cadeia internamente correta deslocada" if d["fora_de_ordem"] else "cadeia correta"
            trechos = "; ".join(f"`{x['id']}` ({', '.join(x['linhas_ouro'][:3])}): “{x['texto'].replace(chr(10),' ')}”" for x in d["trechos"])
            ls.append(f"  - {desc}, {d['palavras']} palavras, {d['inversoes_internas']} inversões; "
                      f"posto da primeira/mediano na regra {d['posto_primeira_regra']}/{f(d['posto_mediano_regra'],1)}. {trechos}.")
    return "\n".join(ls) + "\n"


def variantes(ctx, gr):
    """Quatro algoritmos fixos do cartao; nao recebe referencia."""
    regra, rank, saida = ctx["ordem"], ctx["rank_regra"], gr["saida"]
    chs = cadeias(regra, saida)
    a = [u for ch in sorted(chs, key=lambda ch: rank[ch[0]]) for u in ch]
    exigir(a == gr["ordem"], "Variante a deve ser identidade do max-regret E004")
    med = sorted(chs, key=lambda ch: (statistics.median(rank[u] for u in ch), rank[ch[0]]))
    bb = [u for ch in med for u in ch]
    aceitas = {u: v for u, v in saida.items() if v is not None and
               (ctx["col"][u] == ctx["col"][v] or v in ctx["margem"])}
    # Prioridade ordinal fixa: grafo, depois regra, depois FIM. Os valores
    # apenas expressam precedencia, nao sao novos escores ou hiperparametros.
    scores = {u: {None: 0.} for u in regra}
    for u, v in ctx["regra"].items():
        if v is not None:
            scores[u][v] = 1.
    for u, v in aceitas.items():
        scores[u][v] = 2.
    cc = o.guloso(regra, scores)
    posto_c = {u: i for i, u in enumerate(cc)}
    exigir(all(posto_c[v] == posto_c[u]+1 for u, v in aceitas.items()),
           "Corretor local perdeu aresta aceita")
    # Reinsercao preserva a ordem do corpo de c. Cadeias marginais mantem
    # suas arestas; ancora no predecessor do grafo, ou sucessor, ou regra.
    margens = set(ctx["margem"])
    corpo = [u for u in cc if u not in margens]
    posto = {u: i for i, u in enumerate(corpo)}
    pred = {v: u for u, v in saida.items() if v is not None}
    sm = {u: saida[u] if saida[u] in margens else None for u in regra if u in margens}
    cm = cadeias([u for u in regra if u in margens], sm)
    slots = collections.defaultdict(list)
    for ch in cm:
        anterior, seguinte = pred.get(ch[0]), saida[ch[-1]]
        if anterior in posto:
            slot = posto[anterior]+1
        elif seguinte in posto:
            slot = posto[seguinte]
        else:
            slot = next((i for i, u in enumerate(corpo) if rank[u] > rank[ch[0]]), len(corpo))
        slots[slot].append(ch)
    dd = []
    for i in range(len(corpo)+1):
        for ch in sorted(slots[i], key=lambda ch: rank[ch[0]]):
            dd.extend(ch)
        if i < len(corpo):
            dd.append(corpo[i])
    out = dict(zip(VARIANTES, (a, bb, cc, dd)))
    for seq in out.values():
        exigir(len(seq) == len(regra) and set(seq) == set(regra), "Variante perdeu unidade")
    exigir([u for u in dd if u not in margens] == corpo, "Reinsercao mudou corpo")
    return out, {"arestas_grafo": sum(v is not None for v in saida.values()),
                 "aceitas_locais": len(aceitas), "margens": len(margens)}


def avaliar_corpo(q, ctx, ordem):
    """Projecao diagnostica fixa pelo detector de margens da propria regra."""
    excluir = {k for u in ctx["margem"] for k in ctx["exp"][u]}
    gt = [k for k in q["gt_w"] if k not in excluir]
    if len(gt) < 2:
        return {"elegivel": False}
    gl = [{**L, "ks": [k for k in L["ks"] if k not in excluir]} for L in q["gold_lines"]]
    gl = [L for L in gl if L["ks"]]
    lids = {L["id"] for L in gl}
    qq = {**q, "gt_w": gt, "gold_lines": gl, "gt_l": [u for u in q["gt_l"] if u in lids],
          "reg_words": {u: [k for k in ks if k not in excluir] for u, ks in q["reg_words"].items()}}
    seq = [k for u in ordem for k in ctx["exp"][u] if k not in excluir]
    med = e.medir(qq, seq, [], {}, "P0")
    return {"elegivel": True, **{k: med[k] for k in o.METRICAS}}


def avaliar_pagina(co, obj, p, nomes, salvos):
    path = EXEC / "avaliacao" / co / (e.ac.chave(p["page_id"]) + ".json")
    row = ler(path)
    if row and set(nomes) <= set(row.get("solicitados", [])):
        exigir(row["page_id"] == p["page_id"], "Cache de outra pagina")
        return row
    t0 = time.perf_counter()
    ctx, trs, q = g.preparar_pagina(obj, p)
    gr = grafo_pagina(co, obj, p, ctx)
    vv, info = variantes(ctx, gr)
    lr = salvos.get("layoutreader_pronto", {}).get(p["page_id"])
    densa = len(ctx["cs"]) > 67
    exigir(co in o.DESENV or densa or lr is not None, "Comparador externo incompleto")
    ordens = {"regra": ctx["ordem"], GRAFO: gr["ordem"], **vv}
    if densa or lr is not None:
        ordens["hibrido67"] = ctx["ordem"] if densa else lr
    for nome in nomes:
        if nome.startswith("hibrido67_"):
            base = nome.removeprefix("hibrido67_")
            if densa or lr is not None:
                ordens[nome] = vv[base] if densa else lr
    resultados, corpos, iguais, corpos_iguais, hits = {}, {}, {}, {}, {}
    for nome in nomes:
        if nome not in ordens:
            continue
        ordem = ordens[nome]
        chave = tuple(ordem)
        if chave not in iguais:
            iguais[chave] = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
        resultados[nome] = iguais[chave]
        if chave not in corpos_iguais:
            corpos_iguais[chave] = avaliar_corpo(q, ctx, ordem)
        corpos[nome] = corpos_iguais[chave]
        seq = [k for uid in ordem for k in ctx["exp"][uid]]
        hits[nome] = o.lm.acertos(q, seq, trs, resultados[nome]["metricas"])
        exigir(all(resultados[nome]["metricas"][k] is not None for k in o.METRICAS),
               "Metrica principal indefinida")
    antigo = b.ler(FONTE / "inferencia" / co / (e.ac.chave(p["page_id"]) + ".json"))
    for nome in ("regra", "hibrido67", GRAFO):
        if nome not in resultados:
            continue
        for k in o.METRICAS:
            exigir(abs(resultados[nome]["metricas"][k]-antigo["resultados"][nome]["metricas"][k]) < 1e-11,
                   "Comparador divergiu do E004: " + nome + "/" + k)
    pares_sucessor = {}
    for nome, nh in hits.items():
        pares_sucessor[nome] = {}
        for base in ("regra", "hibrido67", GRAFO):
            if base not in hits:
                continue
            pares_sucessor[nome][base] = {tipo: {"reparos": sum(new and not old for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo),
                                               "regressoes": sum(old and not new for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo)}
                                           for tipo in c.TIPOS}
    row = {"page_id": p["page_id"], "uf": obj["uf"], "unidades": len(ctx["cs"]),
           "resultados": resultados, "corpo": corpos, "info": info,
           "pares_sucessor": pares_sucessor, "solicitados": nomes,
           "segundos": time.perf_counter()-t0}
    gravar(path, row)
    return row


def avaliar_coorte(co, nomes):
    salvos = g.predicoes_salvas(co)
    rows = []
    for obj, p in o.paginas(co):
        vigiar()
        rows.append(avaliar_pagina(co, obj, p, nomes, salvos))
        print(f"Avaliação {co}: {len(rows)}", flush=True)
        gc.collect()
    return rows


def selecionar(dados):
    def media(nome, metrica):
        return statistics.mean(statistics.mean(r["resultados"][nome]["metricas"][metrica]
                               for r in dados[co]) for co in o.DESENV)
    tr, qr, qg = media("regra", "tau"), media("regra", "quebras"), media(GRAFO, "quebras")
    ganho = qr-qg
    exigir(ganho > 0, "E004 nao tem ganho no ajuste")
    alternativas = []
    for nome in VARIANTES:
        tau, quebras = media(nome, "tau"), media(nome, "quebras")
        alternativas.append({"metodo": nome, "tau": tau, "quebras": quebras,
            "delta_tau": tau-tr, "ganho_retido": (qr-quebras)/ganho,
            "tau_elegivel": tau >= tr-.005-1e-12,
            "passa_ajuste": tau >= tr-.005-1e-12 and (qr-quebras)/ganho >= .60-1e-12})
    elegiveis = [x for x in alternativas if x["tau_elegivel"]]
    melhor = min(elegiveis, key=lambda x: (x["quebras"], -x["tau"], x["metodo"])) if elegiveis else None
    escolha = {"congelado": True, "assinatura": ASSINATURA,
        "metodo": melhor["metodo"] if melhor else None, "escolhida": melhor,
        "tau_regra": tr, "quebras_regra": qr, "quebras_e004": qg,
        "alternativas": alternativas, "criterio": "media v4/RN com peso igual; "
        "tau >= regra-0.005; menor quebras, desempate maior tau e nome; "
        "60% de ganho retido e criterio de sucesso, nao afrouxado"}
    path = EXEC / "selecao_congelada.json"
    anterior = ler(path)
    exigir(anterior is None or anterior == escolha, "Selecao congelada mudou")
    if anterior is None:
        gravar(path, escolha)
    return escolha


def resumir(rows, nomes):
    """Bootstrap por veiculo e Wilcoxon importados, sem escolher por p-valor."""
    resumo = {}
    for nome in nomes:
        rs = [r for r in rows if nome in r["resultados"]]
        if not rs:
            continue
        W = b.PESOS_CLUSTER(rs)
        res = {"n": len(rs), "veiculos": len({r["uf"] for r in rs}),
               "completo": len(rs) == len(rows), "metricas": {}, "contrastes": {},
               "classes": {}, "corpo": {}, "pares_sucessor": {}}
        for k in o.METRICAS:
            res["metricas"][k] = e.media_ic([r["resultados"][nome]["metricas"][k] for r in rs], W)
        # Media de taxas por pagina e taxa micro sao distintas e ambas explicitas.
        res["quebras_mil_micro"] = 1000*sum(r["resultados"][nome]["metricas"]["quebras"] for r in rs)/sum(r["resultados"][nome]["palavras"] for r in rs)
        for base in ("regra", "hibrido67", GRAFO):
            rr = [r for r in rs if base in r["resultados"]]
            if not rr:
                continue
            testes = {}
            for k in o.METRICAS:
                ds = [r["resultados"][nome]["metricas"][k]-r["resultados"][base]["metricas"][k] for r in rr]
                por = {uf: statistics.mean(d for r, d in zip(rr, ds) if r["uf"] == uf) for uf in sorted({r["uf"] for r in rr})}
                sinal = -1 if k in ("quebras", "quebras_mil") else 1
                testes[k] = {**e.media_ic(ds, b.PESOS_CLUSTER(rr)), "por_veiculo": por,
                    "wilcoxon_veiculo": e.pratt(list(por.values())),
                    "melhor": sum(sinal*d > 1e-12 for d in ds),
                    "igual": sum(abs(d) <= 1e-12 for d in ds),
                    "pior": sum(sinal*d < -1e-12 for d in ds)}
            res["contrastes"][base] = testes
            res["pares_sucessor"][base] = {tipo: {k: sum(r["pares_sucessor"][nome][base][tipo][k] for r in rr)
                                                  for k in ("reparos", "regressoes")} for tipo in c.TIPOS}
        for tipo in c.TIPOS:
            soma = collections.Counter()
            for r in rs:
                soma.update(r["resultados"][nome]["classes"][tipo])
            res["classes"][tipo] = dict(soma)
        for k in o.METRICAS:
            vals = [r["corpo"][nome].get(k) for r in rs]
            res["corpo"][k] = e.media_ic(vals, W)
        res["cobertura"] = min(r["resultados"][nome]["cobertura_palavras"] for r in rs)
        resumo[nome] = res
    return resumo


def veredito(estado):
    sel = estado.get("escolha")
    if not sel:
        return "PENDENTE: seleção ainda não executada."
    if sel["escolhida"] is None:
        return "NÃO GO / abandono: nenhuma variante atende a margem de τ no ajuste."
    if not sel["escolhida"]["passa_ajuste"]:
        return "NÃO GO / abandono: a variante recupera τ, mas retém menos de 60% do ganho do E004 no ajuste."
    if not estado["completo"]:
        return "PENDENTE: ajuste aprovado, externas incompletas."
    nome, rr = sel["metodo"], estado["resumos"]
    externos = [rr[co][nome] for co in o.COORTES[2:]]
    quebra_ok = all(r["contrastes"]["hibrido67"]["quebras"]["media"] <= 1e-12 for r in externos)
    ic_ok = any(r["contrastes"]["hibrido67"]["quebras"]["ic"][1] < 0 for r in externos)
    tau_ok = all(r["contrastes"]["regra"]["tau"]["media"] >= -.005-1e-12 for r in externos)
    if quebra_ok and ic_ok and tau_ok:
        return "GO exploratório pelo cartão E014: ajuste e ambas as externas atendem aos critérios; teste cego permanece lacrado."
    return f"NÃO GO pelo cartão E014: quebras ≤ híbrido nas duas externas = {quebra_ok}; IC95 < 0 em ao menos uma = {ic_ok}; margem de τ nas duas = {tau_ok}."


def relatorio(estado):
    f, ic = o.f, o.ic
    an, sel = estado["ancora"], estado.get("escolha")
    nome = sel["metodo"] if sel else None
    sem_elegivel = bool(sel and nome is None)
    audit_nome = nome or (max(sel["alternativas"], key=lambda z: z["tau"])["metodo"] if sel else None)
    perda = "; ".join(co+" "+f(statistics.mean(r["delta_entre"] for r in rs),6)
                      for co, rs in estado["diagnostico"].items() if rs)
    linhas = [f"1. Âncora reproduzida: τ {f(an['tau'],6)}; {f(an['quebras'],6)} quebras/página no golden_v4.",
        "2. Diagnóstico no ajuste: contribuição entre cadeias ao Δτ: "+(perda or "pendente")+"; cinco páginas detalhadas abaixo.",
        "3. E004 reproduzido sem treino: mesmo modelo, calibração e ordem por página; (a) é idêntica ao E004.",
        ("4. Nenhuma variante elegível no ajuste; externas e combinação híbrida não executadas." if sem_elegivel else
         f"4. Variante congelada somente em v4/RN: {nome or 'pendente'}; híbrido combinado é apenas exploratório."),
        "5. Golden_v3_novo já foi consultado em rodadas anteriores; nenhuma seleção usa externas; teste cego não foi aberto.",
        "6. Veredito: " + veredito(estado), "", "## Execução e definições", "",
        f"Situação: {estado['situacao']}. Execução `{EXEC.relative_to(OUT).as_posix()}`. "
        f"Pico RSS {f(estado['memoria']['pico_rss_mb'],1)} MiB; CPU, quatro threads, um processo, zero GPU, sem retreino.", "",
        "Fontes, hashes e caches por página estão no manifesto e estado desta execução. "
        "Entrada embaralhada importada do protocolo com `random.Random(f'entrada-{page_id}')`. "
        "Linhas + átomos ls3 congelados; expansão canônica da bancada; cobertura integral exigida.", "",
        "(a) cadeias pelo posto da primeira linha: exatamente a costura já usada pelo max-regret. "
        "(b) cadeias pela mediana dos postos de todas as unidades na regra; empate pela primeira. "
        "(c) mantém as arestas selecionadas do grafo se coluna(i)=coluna(j) ou j é margem/topo/rodapé; "
        "preenche lacunas com arestas da regra, sem duas entradas ou ciclos (guloso importado com precedência grafo > regra > FIM). "
        "(d) parte de (c), retira margens e reinsere cadeias marginais junto ao predecessor do grafo; "
        "se ausente, antes do sucessor; se ambos ausentes, pelo posto da regra. A ordem do corpo fica fixa. "
        "Colunas e margens vêm de `contexto()` do E004, sem novos limiares.", "",
        "Seleção: média das médias de v4/RN com peso igual, como no E004; "
        "entre variantes com τ ≥ regra − 0,005, escolhe menor quebra (desempate por maior τ e nome). "
        "O sucesso no ajuste também exige reter ≥ 60% da redução absoluta de quebras do E004. "
        "A combinação usa LayoutReader até 67 unidades e a variante congelada acima disso, sem seleção adicional.", "",
        f"IC95 percentil: {b.NBOOT} bootstraps por veículo e semente {b.SEMENTE}, funções importadas; "
        "Wilcoxon Pratt sobre médias pareadas por veículo. Médias principais por página; "
        "IC reamostra veículos inteiros conservando suas páginas. RN tem um veículo e IC degenerado. "
        "Melhor/igual/pior usa orientação da métrica; valores de p são descritivos. "
        "RN não tem LayoutReader salvo: híbrido e combinação são parciais em 13 páginas densas; "
        "as duas leves ficam ausentes, sem imputação. A seleção usa todas as 15 páginas com regra/grafo/variantes.", "", texto_diagnostico(estado["diagnostico"])]
    if sel:
        linhas += ["## Varredura e congelamento no ajuste", "", "| Variante | τ médio | Quebras médias | Δτ vs regra | Ganho E004 retido | τ elegível | Passa ajuste |",
                   "|---|---:|---:|---:|---:|---|---|"]
        for a in sel["alternativas"]:
            linhas.append(f"| {a['metodo']} | {f(a['tau'],6)} | {f(a['quebras'],6)} | {f(a['delta_tau'],6)} | {f(100*a['ganho_retido'],2)}% | {a['tau_elegivel']} | {a['passa_ajuste']} |")
        linhas += ["", f"Regra no ajuste: τ {f(sel['tau_regra'],6)}, quebras {f(sel['quebras_regra'],6)}; "
                   f"E004 {f(sel['quebras_e004'],6)} quebras. Resultado da seleção em `selecao_congelada.json` antes de qualquer externa.", ""]
    if sem_elegivel:
        linhas += ["Nenhum parâmetro ou algoritmo foi alterado depois desta varredura. "
                   "A mediana recupera o τ no golden_v4, mas não atende à margem na RN; "
                   "a média do ajuste impede selecionar uma variante válida. O critério de abandono é aplicado "
                   "sem afrouxar a margem nem escolher pelo golden_v4 isolado. "
                   "As tabelas por veículo a seguir detalham a variante de maior τ no ajuste apenas como diagnóstico.", "",
                   "### Maiores perdas da mediana no ajuste (não usada para selecionar outra variante)", "",
                   "| Página | Bancada | Δτ mediana vs regra | Δ quebras |", "|---|---|---:|---:|"]
        for r in estado["casos_mediana"]:
            linhas.append(f"| `{r['page_id']}` | {r['coorte']} | {f(r['delta_tau'],6)} | {f(r['delta_quebras'],6)} |")
        linhas.append("")
    registro = {}
    for co, resumo in estado["resumos"].items():
        linhas += [f"## {co} — {'ajuste' if co in o.DESENV else 'externa'}", "",
                   "| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |",
                   "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for met, r in resumo.items():
            mm = {k: v["media"] for k, v in r["metricas"].items()}
            label = met if r["completo"] else met+" (parcial)"
            linhas.append(f"| {label} | {r['n']} / {r['veiculos']} | {f(mm['tau'],6)} | {f(mm['quebras'],6)} | {f(mm['quebras_mil'],3)} / {f(r['quebras_mil_micro'],3)} | {f(mm['fid12'],6)} | {f(mm['sucessor_linhas'],6)} | {f(100*r['cobertura'],1)}% |")
            registro[co+"/"+met] = {"tau": mm["tau"], "quebras": mm["quebras"], "sucessor": mm["sucessor_linhas"]}
        linhas += ["", "### Diferenças pareadas", "", "| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |",
                   "|---|---|---:|---|---:|---:|---:|"]
        for met, r in resumo.items():
            if met in ("regra", "hibrido67", GRAFO):
                if met != GRAFO:
                    continue
                bases = ("regra", "hibrido67")
            else:
                bases = ("regra", "hibrido67", GRAFO)
            for base in bases:
                if base not in r["contrastes"]:
                    continue
                for k, d in r["contrastes"][base].items():
                    linhas.append(f"| {met} | {base} | {d['n']} | {k} | {ic(d,6)} | {f(d['wilcoxon_veiculo']['p'],6)} | {d['melhor']}/{d['igual']}/{d['pior']} |")
        linhas += ["", "### Δ por veículo — "+("variante de maior τ no ajuste, sem seleção válida" if sem_elegivel else "variante congelada e combinação exploratória"), "",
                   "| Método | Base | Veículo | Δ quebras | Δτ |", "|---|---|---|---:|---:|"]
        for met in (audit_nome, "hibrido67_"+nome if nome else None):
            if met not in resumo:
                continue
            for base in ("regra", "hibrido67", GRAFO):
                ds = resumo[met]["contrastes"][base]
                for uf, delta in ds["quebras"]["por_veiculo"].items():
                    linhas.append(f"| {met} | {base} | {uf} | {f(delta,6)} | {f(ds['tau']['por_veiculo'][uf],6)} |")
        linhas += ["", "### Sucessores: reparos e regressões contra a regra", "",
                   "Contagens de transições de linhas, sem compensar regressões com reparos de outra classe.", "",
                   "| Método | Classe | Referência | Certos | Reparos | Regressões | Quebras |", "|---|---|---:|---:|---:|---:|---:|"]
        for met, r in resumo.items():
            for tipo, cc in r["classes"].items():
                linhas.append(f"| {met} | {tipo} | {cc['ouro']} | {cc['certos']} | {cc['reparos']} | {cc['regressoes']} | {cc['quebras']} |")
        linhas += ["", "### Reparos/regressões de sucessores contra os três controles", "",
                   "| Método | Base | Classe | Reparos | Regressões |", "|---|---|---|---:|---:|"]
        for met in (audit_nome, "hibrido67_"+nome if nome else None):
            if met not in resumo:
                continue
            for base, cc in resumo[met]["pares_sucessor"].items():
                for tipo, z in cc.items():
                    linhas.append(f"| {met} | {base} | {tipo} | {z['reparos']} | {z['regressoes']} |")
        linhas += ["", "### Corpo sem margens — diagnóstico sem seleção", "",
                   "Mesma régua importada aplicada à projeção das palavras/linhas sem as margens automáticas da regra. "
                   "Não é novo ouro humano nem substitui a página inteira; transições sobre lacunas passam a ser vizinhas.", "",
                   "| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |", "|---|---:|---:|---:|---:|---:|"]
        for met, r in resumo.items():
            mc = r["corpo"]
            linhas.append(f"| {met} | {mc['tau']['n']} | {f(mc['tau']['media'],6)} | {f(mc['quebras']['media'],6)} | {f(mc['fid12']['media'],6)} | {f(mc['sucessor_linhas']['media'],6)} |")
        linhas.append("")
    if sem_elegivel:
        for co in o.COORTES[2:]:
            linhas += [f"## {co} — não executada", "", "Não houve variante elegível para congelar no ajuste. "
                       "A bancada não foi aberta nem avaliada pelo E014; não há resultado a registrar.", ""]
        linhas += ["## Híbrido 67 com variante nas páginas densas — não executado", "",
                   "A combinação exploratória depende da variante congelada. Sem variante elegível, "
                   "não se escolhe uma alternativa inválida para completar esta análise.", ""]
    linhas += ["## Veredito pelo cartão E014", "", veredito(estado), "",
        ("Próximo passo indicado pelo próprio cartão: decodificação com restrição global de coluna/blocos "
         "ou GNN (E011). Apenas filtrar arestas pela coluna não garante a ordem global das cadeias, "
         "pois uma cadeia que começa em cabeçalho ainda pode ancorar uma coluna inteira cedo demais."
         if sem_elegivel else "O veredito usa a variante congelada; a combinação híbrida continua exploratória."),
        "", "## Limitações e retomada", "",
        "Resultado exploratório: golden_v4 já orientou a regra; golden_v3_novo foi consultado em rodadas anteriores. "
        "As bancadas se sobrepõem e não são somadas. Silver tem ruído na referência PDF e piso interno aos átomos; "
        "a contagem de cadeias corretas é diagnóstico, sem atribuição humana de causalidade. "
        "Mediana é por unidade, sem ponderar palavras. Coluna/margem é proxy geométrica congelada. "
        "O experimento reusa um modelo de uma semente, sem estimar variância de treino. "
        "IC com poucos veículos (três no teste silver e um em RN) é limitado. "
        "A combinação híbrida não participa do veredito/seleção. Nenhum teste cego foi aberto.", "",
        "Executar `venv/Scripts/python.exe -B orquestracao/analises/e014_cadeias.py` retoma por página; "
        "`--etapa diagnostico` e `--etapa ajuste` nunca abrem externas. "
        "`--conferir` verifica assinatura, relatório e resumo sem nova inferência. "
        "RAM livre mínima 800 MiB, commit livre 1.200 MiB, RSS máximo 3.072 MiB; uma página e um processo por vez.", ""]
    return "\n".join(linhas), registro


def publicar(an, man, diag, dados, escolha, situacao, completo=False):
    estado = {"ancora": an, "manifesto": man, "diagnostico": diag, "escolha": escolha,
              "situacao": situacao, "completo": completo, "memoria": g.medir_memoria(),
              "resumos": {co: resumir(rows, list(dict.fromkeys(nome for r in rows for nome in r["resultados"])))
                          for co, rows in dados.items() if rows}}
    estado["casos_mediana"] = sorted([
        {"page_id": r["page_id"], "coorte": co,
         "delta_tau": r["resultados"]["b_mediana"]["metricas"]["tau"]-r["resultados"]["regra"]["metricas"]["tau"],
         "delta_quebras": r["resultados"]["b_mediana"]["metricas"]["quebras"]-r["resultados"]["regra"]["metricas"]["quebras"]}
        for co, rs in dados.items() if co in o.DESENV for r in rs if "b_mediana" in r["resultados"]],
        key=lambda z: z["delta_tau"])[:5]
    texto, registro = relatorio(estado)
    exigir(all(v is not None and math.isfinite(v) for z in registro.values() for v in z.values()), "Registro nulo")
    estado["assinatura_numeros"] = c.digest([estado["resumos"], escolha, registro])
    gravar(EXEC / "estado.json", estado)
    gravar(OUT / "RELATORIO.md", texto)
    gravar(OUT / "resumo_registro.json", registro)
    gravar(OUT / "cache/ultima_execucao.json", {"execucao": EXEC.relative_to(OUT).as_posix(),
           "assinatura_numeros": estado["assinatura_numeros"]})


def conferir():
    estado = b.ler(EXEC / "estado.json")
    exigir(c.digest(estado["manifesto"]) == ASSINATURA, "Fontes mudaram")
    texto, registro = relatorio(estado)
    exigir((OUT / "RELATORIO.md").read_text(encoding="utf-8") == texto, "Relatorio divergiu")
    exigir(b.ler(OUT / "resumo_registro.json") == registro, "Registro divergiu")
    for co, resumo in estado["resumos"].items():
        rows = []
        for path in sorted((EXEC / "avaliacao" / co).glob("*.json")):
            row = b.ler(path)
            o.permitido(row["page_id"])
            exigir(all(r["cobertura_palavras"] == 1 for r in row["resultados"].values()), "Cobertura divergiu")
            rows.append(row)
        # A ordem original das paginas afeta draws bootstrap e e preservada.
        ordem = b.ler(EXEC / ("ordem_"+co+".json"))
        por_id = {r["page_id"]: r for r in rows}
        rows = [por_id[pid] for pid in ordem]
        nomes = list(dict.fromkeys(nome for r in rows for nome in r["resultados"]))
        exigir(c.digest(resumir(rows, nomes)) == c.digest(resumo), "Resumo nao reproduziu")
    exigir(c.digest([estado["resumos"], estado["escolha"], registro]) == estado["assinatura_numeros"], "Numeros mudaram")
    print("CONFERE: hashes, cobertura, resumos, relatório e registro sem valores nulos.", flush=True)


def main():
    global PRAZO, LOCK_SHA
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapa", choices=("diagnostico", "ajuste", "tudo"), default="tudo")
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    LOCK_SHA, o.PROTEGIDOS = o.ler_lock()
    o.ASSINATURA_LOCK = LOCK_SHA
    if args.max_minutos:
        PRAZO = time.monotonic() + args.max_minutos*60
    with trava():
        an = o.ancora()
        man = iniciar()
        if args.conferir:
            conferir()
            return 0
        gravar(EXEC / "manifesto.json", man)
        diag, dados, escolha = {}, {}, None
        try:
            diag = executar_diagnostico()
            publicar(an, man, diag, dados, escolha, "Diagnóstico concluído; externas não abertas")
            if args.etapa == "diagnostico":
                return 0
            nomes = ["regra", "hibrido67", GRAFO, *VARIANTES]
            for co in o.DESENV:
                dados[co] = avaliar_coorte(co, nomes)
                gravar(EXEC / ("ordem_"+co+".json"), [r["page_id"] for r in dados[co]])
            escolha = selecionar(dados)
            if escolha["metodo"]:
                exploratoria = "hibrido67_"+escolha["metodo"]
                for co in o.DESENV:
                    dados[co] = avaliar_coorte(co, nomes+[exploratoria])
            if not escolha["metodo"]:
                publicar(an, man, diag, dados, escolha,
                         "Concluído por abandono no ajuste; nenhuma variante elegível; externas e combinação não executadas", True)
                conferir()
                return 0
            publicar(an, man, diag, dados, escolha, "Seleção congelada; externas ainda não abertas")
            if args.etapa == "ajuste":
                return 0
            nomes_ext = ["regra", "hibrido67", GRAFO, escolha["metodo"], exploratoria]
            for co in o.COORTES[2:]:
                exigir(b.ler(EXEC / "selecao_congelada.json") == escolha, "Selecao alterada antes da externa")
                dados[co] = avaliar_coorte(co, nomes_ext)
                gravar(EXEC / ("ordem_"+co+".json"), [r["page_id"] for r in dados[co]])
                publicar(an, man, diag, dados, escolha, "Externa concluída com seleção preservada")
            publicar(an, man, diag, dados, escolha, "Execução completa", True)
            conferir()
        except (TimeoutError, KeyboardInterrupt) as ex:
            publicar(an, man, diag, dados, escolha, "PARCIAL retomável: "+str(ex))
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
