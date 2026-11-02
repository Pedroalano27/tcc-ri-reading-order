"""Diagnostica candidatos e testa permutacoes locais dentro da coluna, em CPU.

Importa contexto/categoria/candidatos do corretor e a regua da bancada.
Alertas e scores usam somente dados automaticos. O ouro entra no diagnostico,
na avaliacao e no oraculo das alternativas, jamais no ordenador automatico.
Janelas disjuntas, separadas por uma unidade fixa com palavras, tornam exato
o minimo de quebras entre as alternativas consideradas (nao entre todas as
permutacoes da pagina). Os atomos e as outras colunas conservam seus slots.

Uso, da raiz, sem rede, GPU, treino, workers ou processos filhos:
  venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py
  ... --somente-ancoras
  ... --max-minutos 30
  ... --conferir
  ... --autoteste
Uma pagina por vez; caches atomicos e relatorio atualizados a cada pagina.
Nao chama mains nem rotinas de escrita dos modulos importados. Nao le dados
do projeto parceiro, PDFs ou corpus de treino. Todas as saidas sao novas.
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
import gc
import itertools
import json
import math
import os
import statistics
import time
from contextlib import contextmanager

os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
if "torch" in sys.modules:
    sys.modules["torch"].set_num_threads(4)

BASE = RAIZ / "resultados/reordenacao_restrita_cache"
MD = RAIZ / "resultados/reordenacao_restrita.md"
PRED = RAIZ / "resultados/ordenadores_sem_caixas/pred"
VERSAO = "restrita-v1"
BANCADAS = b.BANCADAS
CLASSES = ("ausente", "outra_coluna", "mesma_coluna")
ALERTAS = ("salto", "retorno", "alinhamento", "objeto")
NOMES = {"ausente": "Sucessor ausente dos candidatos",
         "outra_coluna": "Presente, em outra coluna atribuída",
         "mesma_coluna": "Presente, na mesma coluna atribuída",
         "salto": "Salto sobre linhas próximas", "retorno": "Retorno vertical inesperado",
         "alinhamento": "Mudança brusca de alinhamento", "objeto": "Passagem por tabela/quadro"}
METODOS = ("regra_colunas", "regra_reordena", "oraculo_reordena")
PESOS = {"alinhamento": .6, "espacamento": 1.2, "retorno": 3.,
         "estilo": .3, "objeto": 4., "pontuacao": .15, "deslocamento": .03}
CONFIG = {"versao": VERSAO, "nivel_candidatos": 3, "janela_min": 4, "janela_max": 8,
          "raio_slots": 12, "ganho_score_min": .75, "pesos": PESOS,
          "gate_oraculo": .20, "gate_bancada": "golden_v4", "device": "cpu",
          "threads_max": 4, "num_workers": 0, "ajuste": "pesos fixos, sem treino ou ajuste no ouro"}
R = None
EXEC = None
PRAZO = None


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def ler(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def gravar(p, obj):
    p = Path(p).resolve()
    permitido = p == MD or p.is_relative_to(BASE) or (p.parent == PRED and
                 p.name.startswith(("regra_reordena__linhas__", "oraculo_reordena__linhas__")))
    exigir(permitido, f"Saida fora do escopo: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, p)


def vigiar():
    if PRAZO and time.monotonic() >= PRAZO:
        raise c.Interromper("Prazo atingido; o mesmo comando retoma as páginas concluídas.")
    mem = b.memoria()
    if mem and (mem["ram_livre_mb"] < 900 or mem["commit_livre_mb"] < 1200):
        raise c.Interromper(f"Memória livre insuficiente para continuar: {mem}")
    return mem


@contextmanager
def trava():
    # Reutiliza o lock com deteccao de PID morto, redirecionando so seu destino.
    # Os globals originais nao sao modificados: nenhuma escrita no outro cache.
    import types
    fn = types.FunctionType(c.trava.__wrapped__.__code__,
                            {**c.trava.__wrapped__.__globals__, "BASE": BASE,
                             "destino": lambda p: Path(p), "ler": ler})
    BASE.mkdir(parents=True, exist_ok=True)
    with contextmanager(fn)():
        yield


def fontes():
    splits = ler(RAIZ / "data/processed/splits.json")
    exigir(len(splits["treino"]) == 7 and splits["validacao"] == ["official_diary_rn"] and
           set(splits["teste"]) == {"official_diary_ce", "official_diary_ma", "official_diary_rj"},
           "Split difere do protocolo congelado")
    grupos = [set(splits[k]) for k in ("treino", "validacao", "teste")]
    exigir(all(not a & z for a, z in itertools.combinations(grupos, 2)), "Veiculos em splits distintos")
    ps = set(b.DEP_PATHS) | {Path(__file__), Path(c.__file__),
                           RAIZ / "data/processed/splits.json", e.JSON}
    ps |= {b.UNIDADES / "bancadas" / (co + ".jsonl") for co in BANCADAS[:2]}
    ps |= {b.UNIDADES / "linhas" / (uf + suf) for uf in splits["teste"]
           for suf in (".jsonl", ".palavras.jsonl")}
    for obj, p in b.paginas("golden_v4", "linhas"):
        ps.add(b.UNIDADES / "cache/detector" / (e.ac.chave(p["page_id"]) + ".json"))
    hs = {}
    for p in sorted(ps):
        vigiar()
        exigir(p.is_file(), f"Fonte ausente: {p}")
        hs[b.rel(p)] = c.sha(p)
    return hs, splits


def salvar():
    R["assinatura_numeros"] = c.digest({k: v for k, v in R.items() if k != "assinatura_numeros"})
    gravar(EXEC / "estado.json", R)
    gravar(MD, relatorio(R))


def ancoras():
    if R.get("ancoras", {}).get("aprovada"):
        return
    historico = ler(e.JSON)
    velhos = {r["page_id"]: {m: {k: r["metodos"][m][k] for k in ("seq", "tau", "quebras")}
                             for m in ("P2", "P1m")}
              for r in historico["paginas"] if r["coorte"] == "v4"}
    del historico
    rows = []
    # Cache de controle independe dos scores novos; depende de todas as fontes
    # usadas na ancora. Edicoes no novo script nao exigem refazer o controle.
    deps = {k: v for k, v in R["fontes"].items() if k != b.rel(__file__)}
    afp = c.digest([deps, "ancora-seq-v1", e.FIXA.id])
    for obj, p in b.paginas("golden_v4", "linhas"):
        vigiar()
        pid = p["page_id"]
        cp = BASE / "ancoras" / afp / (e.ac.chave(pid) + ".json")
        if cp.exists():
            row = ler(cp)
            exigir(row["pagina_sha"] == c.digest([obj, p]), "Cache de ancora incompatível")
        else:
            ordem, _ = b.prever(c.automatico(p), obj["palavras"], "regra_colunas")
            med, seq, q, _ = c.medir(obj, p, ordem)
            q["ls3"] = ler(b.UNIDADES / "cache/detector" / (e.ac.chave(pid) + ".json"))["regioes"]
            q["d"] = {"detector": {"regioes": []}}
            sp2, its, dg = e.ls.prever(q, e.FIXA, "ls3")
            exigir(seq == sp2 == velhos[pid]["P2"]["seq"], f"Sequencia de ancora diverge: {pid}")
            m2 = e.medir(q, sp2, its, dg, "P0")
            for k in ("tau", "quebras"):
                exigir(abs(med[k] - m2[k]) < 1e-12 and abs(m2[k] - velhos[pid]["P2"][k]) < 1e-12,
                       f"Metrica de ancora diverge: {pid}/{k}")
            row = {"page_id": pid, "uf": obj["uf"], "pagina_sha": c.digest([obj, p]),
                   "regra": {k: med[k] for k in ("tau", "quebras")},
                   "P1m_historico": {k: velhos[pid]["P1m"][k] for k in ("tau", "quebras")},
                   "seq_identica_P2": True}
            gravar(cp, row)
        rows.append(row)
        R["ancoras"] = {"aprovada": False, "paginas": rows}
        salvar()
        print(f"Âncoras: {len(rows)}/44", flush=True)
    exigir(len(rows) == 44 and {r["page_id"] for r in rows} == set(velhos), "Coorte de ancora diferente")
    ms = {m: {k: statistics.mean(r[m][k] for r in rows) for k in ("tau", "quebras")}
          for m in ("regra", "P1m_historico")}
    R["ancoras"]["medias"] = ms
    exigir(abs(ms["regra"]["tau"] - .985948) <= .00000051 and
           abs(ms["regra"]["quebras"] - 6.045455) <= .00000051,
           f"PARE: ancora obrigatoria nao bate: {ms['regra']}")
    exigir(abs(ms["P1m_historico"]["tau"] - .952) <= .006 and
           abs(ms["P1m_historico"]["quebras"] - 8.93) <= .0051, "Controle P1m nao bate")
    R["ancoras"].update(aprovada=True, fingerprint=afp)
    salvar()


def movel(ctx, uid):
    return (c.tipo_unidade(ctx["mapa"][uid]) == "texto" and uid not in ctx["margem"] and
            uid not in ctx["pontes"])


def detectar_alertas(ctx):
    """Alertas geometricos calculados antes de qualquer consulta a referencia."""
    out = []
    h = ctx["h"]
    for i, (a, z) in enumerate(zip(ctx["ordem"], ctx["ordem"][1:])):
        ua, uz = ctx["mapa"][a], ctx["mapa"][z]
        if a in ctx["margem"] or z in ctx["margem"]:
            continue
        ca, cz = ctx["col"][a], ctx["col"][z]
        dy = c.cy(uz) - c.cy(ua)
        nomes, saltadas = [], []
        if movel(ctx, a):
            for v in ctx["grupos"].get(ca, []):
                if v in (a, z) or not movel(ctx, v):
                    continue
                uv = ctx["mapa"][v]
                dv = c.cy(uv) - c.cy(ua)
                if .25*h < dv <= 4*h and c.sobreposicao(ua, uv) >= .25 and (
                        ca != cz or c.cy(uv) < c.cy(uz)-.25*h):
                    saltadas.append(v)
            if saltadas:
                nomes.append("salto")
        if dy < -.75*h and c.categoria(ctx, a, z) != "proxima_coluna":
            nomes.append("retorno")
        if movel(ctx, a) and movel(ctx, z) and ca == cz:
            delta = min(abs(ua["bbox"][0]-uz["bbox"][0]), abs(ua["bbox"][2]-uz["bbox"][2])) / h
            if delta > 1.5 or c.sobreposicao(ua, uz) < .4:
                nomes.append("alinhamento")
        if (c.tipo_unidade(ua) != "texto" or c.tipo_unidade(uz) != "texto" or
                c.obstaculos(ctx, ua, uz)):
            nomes.append("objeto")
        if nomes:
            out.append({"i": i, "a": a, "z": z, "tipos": nomes, "saltadas": saltadas})
    return out


def janelas(ctx, alerts):
    """Seleciona janelas somente a partir dos alertas, com um separador fixo."""
    ordem = ctx["ordem"]
    propostas = []
    for al in alerts:
        i = al["i"]
        for col in dict.fromkeys((ctx["col"][al["a"]], ctx["col"][al["z"]])):
            elegiveis = [j for j in range(max(0, i-12), min(len(ordem), i+14))
                         if ctx["col"][ordem[j]] == col and movel(ctx, ordem[j])]
            if len(elegiveis) < CONFIG["janela_min"]:
                continue
            centro = min(range(len(elegiveis)), key=lambda j: (abs(elegiveis[j]-i), j))
            ini = max(0, min(centro-3, len(elegiveis)-8))
            slots = elegiveis[ini:ini+8]
            # A janela contem de 4 a 8 linhas da MESMA coluna. Unidades entre
            # seus slots, inclusive tabelas e outras colunas, sao imoveis.
            lo, hi = slots[0], slots[-1]+1
            if hi-lo > 18:
                continue
            propostas.append({"lo": lo, "hi": hi, "slots": slots, "col": col,
                              "alertas": [al["i"]], "tipos": al["tipos"]})
    # Ordem fixa por posicao, sem ordenar por acerto ou score contra o ouro.
    propostas.sort(key=lambda w: (w["lo"], w["hi"], w["col"]))
    out = []
    for w in propostas:
        if out:
            ant = out[-1]
            if w["lo"] <= ant["hi"]:
                continue
            if not any(ctx["exp"][uid] for uid in ordem[ant["hi"]:w["lo"]]):
                continue
        out.append(w)
    return out


def alternativas(ctx, w):
    """Identidade, troca de vizinhos ou mover UMA linha para outro slot."""
    base = ctx["ordem"][w["lo"]:w["hi"]]
    slots = [s-w["lo"] for s in w["slots"]]
    linhas = [base[s] for s in slots]
    vistos = set()
    propostas = [linhas]
    for i in range(len(linhas)-1):
        nova = list(linhas)
        nova[i], nova[i+1] = nova[i+1], nova[i]
        propostas.append(nova)
    for i in range(len(linhas)):
        for j in range(len(linhas)):
            if i == j:
                continue
            nova = list(linhas)
            uid = nova.pop(i)
            nova.insert(j, uid)
            propostas.append(nova)
    for ls in propostas:
        key = tuple(ls)
        if key in vistos:
            continue
        vistos.add(key)
        seg = list(base)
        for s, uid in zip(slots, ls):
            seg[s] = uid
        yield seg


def features_par(ctx, a, z):
    ua, uz = ctx["mapa"][a], ctx["mapa"][z]
    if a in ctx["margem"] or z in ctx["margem"]:
        return {}
    dy = (c.cy(uz)-c.cy(ua)) / ctx["h"]
    mesma = ctx["col"][a] == ctx["col"][z]
    obs = c.obstaculos(ctx, ua, uz)
    if not (movel(ctx, a) and movel(ctx, z) and mesma):
        return {"objeto": min(3, obs)}
    ba, bz = ua["bbox"], uz["bbox"]
    alinha = min(abs(ba[0]-bz[0]), abs(ba[2]-bz[2])) / ctx["h"]
    sa, sz = ctx["estilos"][a], ctx["estilos"][z]
    ha, hz = max(.1, ba[3]-ba[1]), max(.1, bz[3]-bz[1])
    passo = ctx["passos"].get(ctx["col"][a], 1.3)
    retorno = 0. if dy >= -.25 else 2+min(6., abs(dy))
    espacamento = min(6., abs(dy-passo)/max(.5, passo))
    estilo = min(3., abs(math.log(ha/hz))) + abs(sa[3]-sz[3])*.3
    pont = sa[2]*(sz[3]+min(2., alinha)) + (1-sa[1])*sz[4]
    return {"alinhamento": min(4., alinha), "espacamento": espacamento,
            "retorno": retorno, "estilo": estilo, "objeto": min(3, obs), "pontuacao": pont}


def preparar_scores(ctx):
    ctx["estilos"] = {u: c.estilo(ctx, u) for u in ctx["ordem"]}
    passos = {}
    for col, grupo in ctx["grupos"].items():
        ys = sorted(c.cy(ctx["mapa"][u]) for u in grupo if movel(ctx, u))
        ds = [(z-a)/ctx["h"] for a, z in zip(ys, ys[1:]) if .4*ctx["h"] <= z-a <= 3*ctx["h"]]
        passos[col] = statistics.median(ds) if ds else 1.3
    ctx["passos"] = passos
    ctx["custos_par"] = {}


def score(ctx, w, seg):
    # Bordas de unidade e travessia de objetos: somente geometria e texto.
    ordem = ctx["ordem"]
    ls = ordem[max(0, w["lo"]-1):w["lo"]] + seg + ordem[w["hi"]:w["hi"]+1]
    custo = 0.
    for a, z in zip(ls, ls[1:]):
        if (a, z) not in ctx["custos_par"]:
            fs = features_par(ctx, a, z)
            ctx["custos_par"][a, z] = sum(PESOS[k]*v for k, v in fs.items())
        custo += ctx["custos_par"][a, z]
    orig = {u: j for j, u in enumerate(ordem[w["lo"]:w["hi"]])}
    for j, u in enumerate(seg):
        if orig[u] == j:
            continue
        custo += PESOS["deslocamento"] * abs(orig[u]-j)
        for v in ordem[w["lo"]+min(j, orig[u]):w["lo"]+max(j, orig[u])+1]:
            if v != u and c.tipo_unidade(ctx["mapa"][v]) != "texto":
                custo += PESOS["objeto"]
    return custo


def eventos_tipados(ctx, seq, gt):
    evs = e.eventos(seq, gt)
    dono = ctx["dono"]
    for ev in evs:
        ev["tipo"] = c.categoria(ctx, dono[ev["a"]], dono.get(ev["esperado"]))
        ev["dentro_unidade"] = dono[ev["a"]] == dono[ev["b"]]
    return evs


def bordas_oraculo(ctx, w, gt):
    # Uma palavra comparavel fixa de cada lado e todas as palavras livres
    # entre ela e a janela bastam para preservar os eventos de fronteira.
    ordem = ctx["ordem"]
    gset = set(gt)
    prefix = [k for u in ordem[:w["lo"]] for k in ctx["exp"][u]]
    suffix = [k for u in ordem[w["hi"]:] for k in ctx["exp"][u]]
    j = next((i for i in range(len(prefix)-1, -1, -1) if prefix[i] in gset), None)
    left = prefix[j:] if j is not None else prefix
    j = next((i for i, k in enumerate(suffix) if k in gset), None)
    right = suffix[:j+1] if j is not None else suffix
    return left, right


def resolver(ctx, ws, q):
    """Separacao estrita: score automatico antes do oraculo sobre o ouro."""
    out, oracle = list(ctx["ordem"]), list(ctx["ordem"])
    aud = []
    preparar_scores(ctx)
    gset = set(q["gt_w"])
    for a, z in zip(ws, ws[1:]):
        # Verificacao do teto, sem alterar as janelas automaticas: palavras
        # livres nao bastam para separar custos da regua comparavel.
        exigir(any(k in gset for u in ctx["ordem"][a["hi"]:z["lo"]] for k in ctx["exp"][u]),
               "Separador sem palavra comparavel; nao declarar este oraculo independente")
    pred_delta, or_delta = 0, 0
    for w in ws:
        alts = list(alternativas(ctx, w))
        vals = [score(ctx, w, seg) for seg in alts]
        ibest = min(range(len(alts)), key=lambda i: (vals[i], i))
        if vals[0]-vals[ibest] < CONFIG["ganho_score_min"]:
            ibest = 0
        out[w["lo"]:w["hi"]] = alts[ibest]
        # O calculo a seguir nao pode influenciar ibest nem o score.
        left, right = bordas_oraculo(ctx, w, q["gt_w"])
        custos = []
        for seg in alts:
            seq = left + [k for uid in seg for k in ctx["exp"][uid]] + right
            evs = eventos_tipados(ctx, seq, q["gt_w"])
            custos.append((len(evs), sum(ev["tipo"] == "mesma_coluna" for ev in evs)))
        io = min(range(len(alts)), key=lambda i: (*custos[i], i))
        oracle[w["lo"]:w["hi"]] = alts[io]
        pred_delta += custos[ibest][0] - custos[0][0]
        or_delta += custos[io][0] - custos[0][0]
        aud.append({**w, "n_alternativas": len(alts), "score_base": vals[0],
                    "score_escolhido": vals[ibest], "indice_score": ibest, "indice_oraculo": io,
                    "quebras_local_base": custos[0][0], "quebras_local_score": custos[ibest][0],
                    "quebras_local_oraculo": custos[io][0],
                    "ordem_base": alts[0], "ordem_score": alts[ibest], "ordem_oraculo": alts[io]})
    return out, oracle, aud, pred_delta, or_delta


def diagnostico(ctx, obj, p, trs, q):
    gold = {ls["id"]: ls for ls in q["gold_lines"]}
    ranks_l = {lid: i for i, lid in enumerate(q["gt_l"])}
    cont = {cl: 0 for cl in CLASSES}
    exemplos = {cl: [] for cl in CLASSES}
    inelegiveis = collections.Counter()
    cand_cache = {}
    for tr in trs:
        if tr["tipo"] != "mesma_coluna" or tr["acerto"]:
            continue
        a, z = tr["a"], tr["z"]
        if a not in cand_cache:
            cand_cache[a] = c.candidatos(ctx, a, CONFIG["nivel_candidatos"])
        cand = cand_cache[a]
        cl = "ausente" if z not in cand else "outra_coluna" if ctx["col"][a] != ctx["col"][z] else "mesma_coluna"
        cont[cl] += 1
        inelegiveis["internos_unidade"] += int(tr["interno"])
        inelegiveis["fronteira_inalcancavel"] += int(not tr["alcancavel"])
        if len(exemplos[cl]) >= 3:
            continue
        ix = ctx["rank_regra"][a]
        ig = ranks_l[tr["linha_a"]]
        texto_l = lambda lid: " ".join(obj["palavras"][k][0] for k in gold[lid]["ks"])
        exemplos[cl].append({"page_id": p["page_id"], "classe": cl, "a": a, "z": z,
            "col_a": ctx["col"][a], "col_z": ctx["col"][z], "candidatos": cand,
            "interno": tr["interno"], "alcancavel": tr["alcancavel"],
            "texto_a": texto_l(tr["linha_a"]), "texto_z": texto_l(tr["linha_z"]),
            "humana": [{"id": lid, "texto": texto_l(lid)} for lid in q["gt_l"][max(0, ig-1):ig+4]],
            "regra": [{"id": uid, "texto": ctx["mapa"][uid]["text"]} for uid in ctx["ordem"][max(0, ix-1):ix+4]]})
    return {"classes": cont, "inelegiveis": dict(inelegiveis), "exemplos": exemplos}


def avaliar_alertas(ctx, alerts, evs, gt, trs):
    """Precisao em arestas emitidas; cobertura de eventos de palavras reais."""
    gset = set(gt)
    erros = {ev["a"] for ev in evs}
    intern = {ev["a"] for ev in evs if ev["tipo"] == "mesma_coluna"}
    bound = {ev["a"] for ev in evs if ctx["exp"][ctx["dono"][ev["a"]]][-1] == ev["a"]}
    fontes_linhas = {tr["a"] for tr in trs if not tr["acerto"] and tr["tipo"] == "mesma_coluna"}
    fontes_total = {tr["a"] for tr in trs if not tr["acerto"]}
    res = {}
    for nome in ("uniao",) + ALERTAS:
        subset = [al for al in alerts if nome == "uniao" or nome in al["tipos"]]
        palavras = {ctx["exp"][al["a"]][-1] for al in subset if ctx["exp"][al["a"]] and
                    ctx["exp"][al["a"]][-1] in gset}
        origens = {al["a"] for al in subset}
        res[nome] = {"alertas": len(subset), "avaliaveis": len(palavras),
                     "sem_referencia_na_borda": len(subset)-len(palavras), "tp": len(palavras & erros),
                     "erros_total": len(erros), "erros_cobertos": len(palavras & erros),
                     "internos_coluna": len(intern), "internos_cobertos": len(palavras & intern),
                     "fronteiras": len(bound), "fronteiras_cobertas": len(palavras & bound),
                     "fontes_linha_erro": len(fontes_total), "fontes_linha_cobertas": len(origens & fontes_total),
                     "fontes_linha_internas": len(fontes_linhas),
                     "fontes_linha_internas_cobertas": len(origens & fontes_linhas)}
    return res


def medir_saida(ctx, obj, p, ordem, base_evs):
    med, seq, _, _ = c.medir(obj, p, ordem)
    evs = eventos_tipados(ctx, seq, obj["gt_w"])
    orig = {ev["a"] for ev in base_evs}
    novos = {ev["a"] for ev in evs}
    reparos, regressoes = len(orig-novos), len(novos-orig)
    exigir(reparos-regressoes == len(base_evs)-len(evs), "Saldo nao corresponde as quebras")
    return {"metricas": med, "reparos": reparos, "regressoes": regressoes,
            "saldo": reparos-regressoes,
            "quebras_internas_coluna": sum(ev["tipo"] == "mesma_coluna" for ev in evs)}, seq


def processar(co):
    rows = []
    expected = {"golden_v4": 44, "golden_v3_novo": 27, "teste_silver": 89}[co]
    ids = set()
    for obj, p in b.paginas(co, "linhas"):
        vigiar()
        pid = p["page_id"]
        exigir(pid not in ids, "Pagina repetida")
        ids.add(pid)
        cp = EXEC / "paginas" / co / (e.ac.chave(pid) + ".json")
        if cp.exists():
            row = ler(cp)
            exigir(row["pagina_sha"] == c.digest([obj, p]), "Pagina mudou durante retomada")
        else:
            ctx = c.contexto(c.automatico(p), obj["palavras"])
            ctx["dono"] = {k: u for u, ks in ctx["exp"].items() for k in ks}
            # Antes do ouro: alertas e as janelas estao congelados aqui.
            alerts = detectar_alertas(ctx)
            ws = janelas(ctx, alerts)
            med, _, trs, _ = c.preparar_avaliacao(obj, p, ctx)
            _, seq_base, q, _ = c.medir(obj, p, ctx["ordem"])
            evs = eventos_tipados(ctx, seq_base, q["gt_w"])
            auto, oracle, aud, d_auto, d_or = resolver(ctx, ws, q)
            sa, _ = medir_saida(ctx, obj, p, auto, evs)
            so, _ = medir_saida(ctx, obj, p, oracle, evs)
            exigir(sa["metricas"]["quebras"]-med["quebras"] == d_auto and
                   so["metricas"]["quebras"]-med["quebras"] == d_or,
                   "Janelas interagem: o oraculo local nao e o minimo exato de pagina")
            exigir(so["metricas"]["quebras"] <= med["quebras"] and
                   so["metricas"]["quebras"] <= sa["metricas"]["quebras"], "Oraculo nao e teto")
            exigir(set(auto) == set(oracle) == set(ctx["ordem"]) and len(auto) == len(oracle) == len(ctx["ordem"]),
                   "Permutacao invalida")
            sb = {"metricas": med, "reparos": 0, "regressoes": 0, "saldo": 0,
                  "quebras_internas_coluna": sum(ev["tipo"] == "mesma_coluna" for ev in evs)}
            row = {"page_id": pid, "uf": obj["uf"], "visto_treino": obj["uf"] in R["splits"]["treino"],
                   "pagina_sha": c.digest([obj, p]), "unidades": len(p["bounding_boxes"]),
                   "palavras_referencia": len(q["gt_w"]),
                   "diagnostico": diagnostico(ctx, obj, p, trs, q), "alertas": alerts,
                   "alertas_avaliacao": avaliar_alertas(ctx, alerts, evs, q["gt_w"], trs), "janelas": aud,
                   "ordens": dict(zip(METODOS, (ctx["ordem"], auto, oracle))),
                   "metodos": dict(zip(METODOS, (sb, sa, so)))}
            gravar(cp, row)
        rows.append(row)
        # Estado leve: nenhuma palavra nem pagina inteira fica em memoria.
        R.setdefault("bancadas", {})[co] = {"completa": False, "esperadas": expected,
            "paginas": [{k: v for k, v in r.items() if k not in ("ordens", "alertas", "janelas", "pagina_sha")}
                        | {"janelas_n": len(r["janelas"]), "alternativas_n": sum(w["n_alternativas"] for w in r["janelas"]),
                           "janelas_auto_alteradas": sum(w["indice_score"] != 0 for w in r["janelas"]),
                           "janelas_oraculo_alteradas": sum(w["indice_oraculo"] != 0 for w in r["janelas"])}
                        for r in rows]}
        salvar()
        if len(rows) % 5 == 0 or len(rows) == expected:
            print(f"{co}: {len(rows)}/{expected}, regra {row['metodos']['regra_colunas']['metricas']['quebras']}, "
                  f"score {row['metodos']['regra_reordena']['metricas']['quebras']}, "
                  f"oráculo {row['metodos']['oraculo_reordena']['metricas']['quebras']}", flush=True)
        del obj, p
        gc.collect()
    exigir(len(rows) == expected, f"Cobertura inesperada em {co}: {len(rows)}")
    R["bancadas"][co]["completa"] = True
    if co == "golden_v4":
        den = sum(r["metodos"]["regra_colunas"]["quebras_internas_coluna"] for r in rows)
        pos = sum(r["metodos"]["oraculo_reordena"]["quebras_internas_coluna"] for r in rows)
        ganho = (den-pos)/den if den else 0.
        R["gate"] = {"bancada": co, "antes": den, "depois_oraculo": pos, "fracao_reducao": ganho,
                     "aprovado": ganho >= CONFIG["gate_oraculo"]}
    salvar()


def resumos(co, rows):
    estado = {"resultados": {}}
    for m in METODOS:
        rs = [{k: r[k] for k in ("page_id", "uf", "visto_treino")} |
              {"metricas": r["metodos"][m]["metricas"], "diag": {}} for r in rows]
        estado["resultados"][f"{m}__linhas__{co}"] = {"completa": True, "paginas": rs}
    return {m: b.resumo(estado["resultados"][f"{m}__linhas__{co}"]["paginas"], estado, "linhas", co)
            for m in METODOS}


def publicar(co):
    exigir(R["bancadas"][co]["completa"], "Predicao parcial nao sera publicada")
    for m in METODOS[1:]:
        ls = []
        for row in R["bancadas"][co]["paginas"]:
            cp = EXEC / "paginas" / co / (e.ac.chave(row["page_id"]) + ".json")
            pag = ler(cp)
            # Gate negativo: alternativa automatica nao e promovida; conserva
            # a regra no contrato. O score exploratorio fica no cache/relatorio.
            usado = "regra_colunas" if m == "regra_reordena" and not R["gate"]["aprovado"] else m
            ls.append(json.dumps({"page_id": row["page_id"], "ordem": pag["ordens"][usado]}, ensure_ascii=False))
        p = PRED / f"{m}__linhas__{co}.jsonl"
        conteudo = "\n".join(ls) + "\n"
        if p.exists():
            exigir(p.read_text(encoding="utf-8") == conteudo, f"Arquivo ja existente diferente: {p}; nao sobrescrever")
        else:
            gravar(p, conteudo)
        R.setdefault("predicoes", {})[f"{m}__{co}"] = {"arquivo": b.rel(p), "sha256": c.sha(p),
                                                        "regra_preservada_por_gate": usado != m}


def conferir_predicoes(co):
    """Avalia de novo o JSONL estrito com as funcoes puras da bancada."""
    inds = {m: b.indice_pred(PRED / f"{m}__linhas__{co}.jsonl") for m in METODOS[1:]}
    rows = {r["page_id"]: r for r in R["bancadas"][co]["paginas"]}
    for m in METODOS[1:]:
        saved = R["predicoes"][f"{m}__{co}"]
        exigir(c.sha(RAIZ / saved["arquivo"]) == saved["sha256"], "Arquivo de predicao mudou")
    for obj, p in b.paginas(co, "linhas"):
        vigiar()
        for m in METODOS[1:]:
            path = PRED / f"{m}__linhas__{co}.jsonl"
            with open(path, "rb") as f:
                pred = b.ler_offset(f, inds[m][p["page_id"]])
            med, _, _, _ = c.medir(obj, p, pred["ordem"])
            usado = "regra_colunas" if m == "regra_reordena" and not R["gate"]["aprovado"] else m
            exigir(med == rows[p["page_id"]]["metodos"][usado]["metricas"], "Predicao diverge da bancada")
            cp = EXEC / "paginas" / co / (e.ac.chave(p["page_id"]) + ".json")
            pag = ler(cp)
            exigir(pred["ordem"] == pag["ordens"][usado], "Ordem do contrato difere do cache de pagina")
    exigir(all(set(ind) == set(rows) for ind in inds.values()), "Predicoes fora da coorte")
    R.setdefault("predicoes_conferidas", {})[co] = {"paginas": len(rows), "regua": "corretor.medir -> bancada + erros.medir"}
    salvar()


def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def pct(a, d):
    return f(a/d*100, 2)+"%" if d else "—"


def cel(v, n=3, percent=False):
    scale = 100 if percent else 1
    x = f(v["media"]*scale if v["media"] is not None else None, n)
    lo, hi = v["ic"]
    return x + ("%" if percent else "") + f" [{f(lo*scale if lo is not None else None,n)}; {f(hi*scale if hi is not None else None,n)}]"


def grupos(rows, co):
    return {g: [r for r in rows if g == "todos" or r["visto_treino"] == (g == "vistos")]
            for g in (("todos", "vistos", "nao_vistos") if co != "teste_silver" else ("todos",))}


def conclusao(r):
    banc = r.get("bancadas", {})
    if r.get("gate") and not r["gate"]["aprovado"]:
        return "O teto reprova a reordenação: abandonar estas alternativas e conservar a regra original."
    if not all(banc.get(co, {}).get("resumos") for co in BANCADAS):
        return "Conclusão pendente até completar as três bancadas e seus contrastes por veículo."
    difs = {co: banc[co]["resumos"]["regra_reordena"]["todos"]["contra_regra_colunas"]["quebras"] for co in BANCADAS}
    melhora = [co for co, d in difs.items() if d["delta"]["media"] < 0]
    piora = [co for co, d in difs.items() if d["delta"]["media"] > 0]
    if len(melhora) == len(BANCADAS):
        texto = "Melhorou a média de quebras nas três bancadas, com τ praticamente preservado."
    else:
        texto = "Resultado misto: média melhor em " + ", ".join(melhora) + "; pior em " + ", ".join(piora) + "."
    externos = [co for co in BANCADAS[1:] if difs[co]["delta"]["ic"][0] <= 0 <= difs[co]["delta"]["ic"][1]]
    if externos:
        texto += " IC externo inclui zero em " + ", ".join(externos) + "."
    sem_w = [co for co in BANCADAS[1:] if difs[co]["wilcoxon_veiculo"]["p"] >= .05]
    if sem_w:
        texto += " Wilcoxon por veículo não confirma ganho nas bancadas externas; resultado exploratório."
    else:
        texto += " Os contrastes por veículo apoiam o ganho, com as limitações de desenvolvimento e referência silver."
    return texto


def tabela_resultados(ls, co, dados):
    rows = dados["paginas"]
    ls += [f"## {co}", "", f"Cobertura: {len(rows)}/{dados['esperadas']} páginas; "
           + ("completa." if dados["completa"] else "parcial; médias provisórias, sem IC ou inferência."), ""]
    su = dados.get("resumos", {})
    ls += ["| Grupo | Método | n / veículos | τ palavras [IC] | Quebras/página [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Reparos / regressões / saldo | Quebras na coluna |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g, rs in grupos(rows, co).items():
        if not rs:
            continue
        for m in METODOS:
            ms = su.get(m, {}).get(g, {}).get("metricas")
            vals = []
            for k, n, per in (("tau", 6, False), ("quebras", 3, False), ("fid12", 2, True), ("sucessor_linhas", 2, True)):
                v = [r["metodos"][m]["metricas"][k] for r in rs if r["metodos"][m]["metricas"][k] is not None]
                vals.append(cel(ms[k], n, per) if ms else f(statistics.mean(v)*(100 if per else 1), n) + ("%" if per else ""))
            tot = [sum(r["metodos"][m][k] for r in rs) for k in ("reparos", "regressoes", "saldo")]
            internos = sum(r["metodos"][m]["quebras_internas_coluna"] for r in rs)
            nome = {"regra_colunas": "Regra original", "regra_reordena": "Regra + reordenação (pesos fixos)", "oraculo_reordena": "Oráculo restrito"}[m]
            ls.append(f"| {g} | {nome} | {len(rs)} / {len({r['uf'] for r in rs})} | " + " | ".join(vals) +
                      " | " + " / ".join(str(t) for t in tot) + f" | {internos} |")
    if su:
        ls += ["", "Δ método−regra; negativo em quebras significa melhoria. Wilcoxon bilateral Pratt sobre médias pareadas por veículo.", "",
               "| Grupo | Método | Δ quebras [IC 95% veículo] | p veículo | Δ τ [IC 95% veículo] | p veículo | Melhor / igual / pior (páginas, quebras) |",
               "|---|---|---:|---:|---:|---:|---:|"]
        for g, rs in grupos(rows, co).items():
            if not rs:
                continue
            for m in METODOS[1:]:
                tests = su[m][g]["contra_regra_colunas"]
                ds = [r["metodos"][m]["metricas"]["quebras"]-r["metodos"]["regra_colunas"]["metricas"]["quebras"] for r in rs]
                ls.append(f"| {g} | {m} | {cel(tests['quebras']['delta'],3)} | {f(tests['quebras']['wilcoxon_veiculo']['p'],6)} | "
                          f"{cel(tests['tau']['delta'],6)} | {f(tests['tau']['wilcoxon_veiculo']['p'],6)} | "
                          f"{sum(d<0 for d in ds)} / {sum(d==0 for d in ds)} / {sum(d>0 for d in ds)} |")


def relatorio(r):
    anc = r.get("ancoras", {})
    banc = r.get("bancadas", {})
    gate = r.get("gate")
    primeiro = (f"Âncora reproduzida: τ {f(anc['medias']['regra']['tau'],6)} e {f(anc['medias']['regra']['quebras'],6)} quebras/página em {len(anc['paginas'])} páginas."
                if anc.get("aprovada") else f"Âncoras em verificação: {len(anc.get('paginas',[]))} páginas; nenhuma conclusão liberada.")
    segunda = f"Diagnóstico e alternativas: {sum(len(v['paginas']) for v in banc.values())} páginas processadas; três bancadas separadas abaixo."
    terceira = (f"Teto na coluna (v4): {gate['antes']} → {gate['depois_oraculo']} quebras; redução {f(gate['fracao_reducao']*100,2)}%; "
                + ("passa o critério para investigar o score." if gate['aprovado'] else "abaixo do critério: abandonar estas alternativas e conservar a regra.")
                if gate else "Oráculo das alternativas ainda pendente; não promover correção antes do teto.")
    compara = []
    for co, d in banc.items():
        if d["completa"]:
            rs = d["paginas"]
            v = [statistics.mean(rw["metodos"][m]["metricas"]["quebras"] for rw in rs) for m in METODOS]
            compara.append(co+": "+" / ".join(f(x,3) for x in v))
    quarta = "Quebras/página (regra / score / oráculo): " + "; ".join(compara) + "." if compara else "Comparação final ainda pendente; resultados parciais são gravados por página."
    quinta = conclusao(r)
    ls = ["# Reordenação restrita dentro da coluna", "", primeiro+"  ", segunda+"  ", terceira+"  ", quarta+"  ", quinta, "",
          "Relatório escrito pelo script a partir das execuções, sem números editados à mão. "
          "Score fixo é a alternativa exploratória; oráculo usa a referência apenas para escolher a melhor alternativa do conjunto congelado.", ""]
    if r.get("parada"):
        ls += ["Estado da execução: "+r["parada"], ""]
    if anc.get("aprovada"):
        a = anc["medias"]
        ls += ["## Controles", "", "| Método | τ palavras | Quebras/página |", "|---|---:|---:|",
               f"| Regra original, reexecutada e sequência idêntica ao P2 | {f(a['regra']['tau'],6)} | {f(a['regra']['quebras'],6)} |",
               f"| Extrator + XY-cut + margens, controle histórico P1m | {f(a['P1m_historico']['tau'],6)} | {f(a['P1m_historico']['quebras'],6)} |", "",
               "A âncora obrigatória usa tolerância de arredondamento na sexta casa; P1m é importado do histórico, sem reextração. "
               "Detecções congeladas de ls3 são reexecutadas geometricamente, sem carregar pesos ou consultar o projeto parceiro.", ""]
    if not anc.get("aprovada"):
        return "\n".join(ls)+"\n"
    ls += ["## Diagnóstico de candidatos", "", "Nível 3, o nível usado pelo corretor anterior; candidatos importados sem ampliar ou alterar a função. "
           "Denominador: sucessores de linhas perdidos classificados como continuação na mesma coluna pelo contexto do corretor. "
           "As três classes são exclusivas. Uma fronteira interna à unidade ou inalcançável não se torna corrigível por aparecer nos candidatos.", "",
           "| Bancada / grupo | Erros de sucessor na coluna | Ausente | Presente, outra coluna | Presente, mesma coluna | Internos à unidade | Fronteira inalcançável |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for co, d in banc.items():
        for g, rs in grupos(d["paginas"], co).items():
            if not rs:
                continue
            ns = [sum(p['diagnostico']['classes'][k] for p in rs) for k in CLASSES]
            ns += [sum(p['diagnostico']['inelegiveis'].get(k,0) for p in rs) for k in ("internos_unidade", "fronteira_inalcancavel")]
            ls.append(f"| {co} / {g} | {sum(ns[:3])} | "+" | ".join(str(n) for n in ns)+" |")
    ls += ["", "Coluna atribuída é a proxy global pelo centro da unidade; a tipologia de sucessor usa também a caixa da linha-ouro. "
           "Assim um erro tipado na mesma coluna pode ter unidades atribuídas a colunas diferentes. Não são causas humanas anotadas.", "",
           "## Três exemplos reais de cada classe", ""]
    for cl in CLASSES:
        exemplos = []
        for co in ("golden_v3_novo", "golden_v4", "teste_silver"):
            for row in banc.get(co, {}).get("paginas", []):
                for ex in row["diagnostico"]["exemplos"][cl]:
                    if len(exemplos) < 3:
                        exemplos.append((co, ex))
        ls += [f"### {NOMES[cl]}", "", f"Exemplos disponíveis nesta execução: {len(exemplos)} (até três exibidos).", ""]
        if not exemplos:
            ls += ["Não houve caso observado; não há exemplo real a reproduzir nesta classe. "
                   "O pedido de três exemplos não pode ser satisfeito aqui sem inventar casos ou mudar a tipologia congelada.", ""]
        for co, ex in exemplos:
            ls += [f"- `{ex['page_id']}` ({co}); `{ex['a']}` → `{ex['z']}`, colunas {ex['col_a']} → {ex['col_z']}. "
                   f"Interno à unidade: {ex['interno']}; fronteira alcançável: {ex['alcancavel']}.",
                   "", "Origem: "+ex["texto_a"], "", "Sucessor esperado: "+ex["texto_z"], "",
                   ("Ordem humana" if co != "teste_silver" else "Ordem silver")+" (trecho): "+
                   " → ".join(f"`{v['id']}` {v['texto']}" for v in ex["humana"]), "",
                   "Ordem da regra (trecho): "+" → ".join(f"`{v['id']}` {v['texto']}" for v in ex["regra"]), "",
                   "Candidatos: "+", ".join("fim" if v is None else f"`{v}`" for v in ex["candidatos"])+".", ""]
    ls += ["## Alertas sem consultar a referência", "",
           "Salto: linha alinhada da coluna de origem até quatro alturas abaixo é ultrapassada; retorno: recuo vertical maior que 0,75 altura, "
           "exceto a transição fim→topo da próxima coluna reconhecida pelo corretor; alinhamento: mudança acima de 1,5 altura no melhor dos dois lados "
           "ou sobreposição horizontal abaixo de 0,4; objeto: átomo na borda ou obstáculo entre as linhas. Margens são excluídas.", "",
           "Precisão = alertas cuja palavra final comparável da unidade de origem inicia uma quebra emitida / alertas com essa borda comparável. "
           "Cobertura geral = esses eventos cobertos / todas as quebras. Cobertura na coluna usa só eventos tipados na mesma coluna. "
           "Alertas sem referência na borda são contados separadamente. Alertas sobrepostos entram uma vez na união; não somar as linhas por tipo.", "",
           "| Bancada / grupo | Alerta | Quantidade / avaliáveis / sem referência | Precisão | Cobertura quebras | Cobertura na coluna | Cobertura fronteiras de unidade |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for co, d in banc.items():
        for g, rs in grupos(d["paginas"], co).items():
            if not rs:
                continue
            for nome in ("uniao",)+ALERTAS:
                total = collections.Counter()
                for row in rs:
                    total.update(row["alertas_avaliacao"][nome])
                ls.append(f"| {co} / {g} | {nome} | {total['alertas']} / {total['avaliaveis']} / {total['sem_referencia_na_borda']} | "
                          f"{total['tp']}/{total['avaliaveis']} = {pct(total['tp'],total['avaliaveis'])} | "
                          f"{total['erros_cobertos']}/{total['erros_total']} = {pct(total['erros_cobertos'],total['erros_total'])} | "
                          f"{total['internos_cobertos']}/{total['internos_coluna']} = {pct(total['internos_cobertos'],total['internos_coluna'])} | "
                          f"{total['fronteiras_cobertas']}/{total['fronteiras']} = {pct(total['fronteiras_cobertas'],total['fronteiras'])} |")
    ls += ["", "## Alternativas e teto", "",
           "Só alertas propõem janelas: quatro a oito linhas móveis da mesma coluna, em raio local de slots, com amplitude máxima de dezoito unidades. "
           "Linhas marginais, transversais, tabelas, imagens e slots de outras colunas ficam fixos. A ordem das propostas é geométrica, sem olhar acerto. "
           "Sobreposições são descartadas, mantendo uma unidade fixa com palavras entre janelas. Alternativas: identidade, trocar vizinhos ou mover uma linha "
           "para outro slot da mesma coluna. Cada linha aparece exatamente uma vez.", "",
           "Score = soma ponderada de alinhamento, espaçamento típico da coluna, penalidade de retorno, continuidade de altura/estilo de caixa e caixa alta, "
           "objetos atravessados, pontuação/hifenização e deslocamento. São proxies, sem fonte tipográfica/semântica completa. "
           "Pesos fixos: `"+json.dumps(PESOS, ensure_ascii=False)+"`; vantagem mínima `"+str(CONFIG["ganho_score_min"])+"`. "
           "Não houve treino nem busca de pesos em RN, v4 ou bancadas externas.", "",
           "Oráculo minimiza quebras de palavras nas alternativas de cada janela, incluindo as bordas fixas; desempata pelo menor número de quebras na coluna "
           "e depois identidade. A separação por palavra fixa torna os deltas aditivos. O script confere essa igualdade com a régua de página e que o oráculo "
           "vence ou empata com regra e score em cada página. É o teto exato de QUEBRAS deste conjunto de janelas; não é teto de τ, de todas as janelas possíveis "
           "ou de todas as permutações. Tabela/imagem não é desmembrada.", "",
           "| Bancada | Janelas | Alternativas (inclui identidade) | Janelas mudadas pelo score | Janelas mudadas pelo oráculo |",
           "|---|---:|---:|---:|---:|"]
    for co, d in banc.items():
        rs = d["paginas"]
        ls.append(f"| {co} | "+" | ".join(str(sum(v[k] for v in rs)) for k in ("janelas_n", "alternativas_n", "janelas_auto_alteradas", "janelas_oraculo_alteradas"))+" |")
    if gate:
        ls += ["", f"Gate obrigatório, somente desenvolvimento v4: {gate['antes']} → {gate['depois_oraculo']} quebras na coluna, "
               f"{pct(gate['antes']-gate['depois_oraculo'],gate['antes'])} de redução; "
               + ("aprovado." if gate["aprovado"] else "reprovado. O problema excede as alternativas consideradas; não ajustar pesos ou ampliar este corretor nesta execução."), ""]
    for co, d in banc.items():
        tabela_resultados(ls, co, d)
    ls += ["", "Reparos/regressões contam palavras de origem que deixam de iniciar / passam a iniciar uma quebra da régua oficial; "
           "saldo = reparos−regressões = quebras da regra−quebras do método. Não confundir com o diagnóstico de sucessores-ouro perdidos. "
           "‘Quebras na coluna’ mantém o mesmo contexto/categoria original em todos os métodos e inclui o piso interno à unidade.", "",
           "## Conclusão", "", conclusao(r), "",
           "As alternativas e os pesos foram fixados antes da leitura das medidas externas. O ganho do oráculo demonstra espaço dentro das janelas, "
           "mas não demonstra que a seleção automática acertará sempre. O score também introduz regressões, contadas nas tabelas. "
           "Esta execução não demonstra superioridade generalizável nem substitui a avaliação dos outros modelos do TCC; demonstra uma correção geométrica local "
           "sobre a representação em linhas, mantendo a régua de palavras e a referência de cada bancada.", "",
           "## Inferência e limitações", "",
           f"IC percentil de 95% por veículo, {b.NBOOT} reamostras, semente {b.SEMENTE}, importados da bancada; médias macro por página. "
           "Wilcoxon bilateral Pratt sobre médias de diferenças por veículo, sem correção de multiplicidade; evidência exploratória. "
           "Os IC são de grupos de veículos; não eliminam viés de desenvolvimento, seleção do conjunto de janelas ou referência automática.", "",
           "Golden v4 foi usado no desenvolvimento da regra e no gate deste experimento. Golden v3 novo é externo a este ajuste, mas já foi consultado "
           "nos experimentos anteriores e pode compartilhar veículos/layouts; não é teste totalmente intocado. Ouro deriva da ordem humana de regiões "
           "expandida em palavras, não de anotação independente de todas as linhas. ‘Vistos’ significa os sete veículos do split de treino dos modelos do TCC; "
           "este experimento não treina nada. Não informa quais veículos ls3 viu no pré-treino.", "",
           "Teste silver conserva todas as páginas da bancada original de CE, MA e RJ, inclusive sobreposições humanas, pois nenhuma é usada para treino. "
           "O fluxo de conteúdo PDF é a referência automática, selecionada por confiabilidade do veículo; tabelas têm piso alto por discordância da expansão "
           "canônica com o fluxo. As bancadas são reportadas separadamente, sem tratá-las como amostras independentes somadas.", ""]
    if all(banc.get(co, {}).get("completa") for co in BANCADAS):
        ids = {co: {rw["page_id"] for rw in banc[co]["paginas"]} for co in BANCADAS}
        ls += [f"Sobreposição silver/humanas: {len(ids['teste_silver'] & (ids['golden_v4'] | ids['golden_v3_novo']))} páginas. "
               f"Bancadas humanas entre si: {len(ids['golden_v4'] & ids['golden_v3_novo'])} páginas.", ""]
    ls += ["## Artefatos e retomada", "", "Estado/hashes/caches: `"+b.rel(EXEC or BASE)+"`. "
           "Uma página por vez, um processo, sem multiprocessing/DataLoader, sem modelos carregados, sem GPU e sem leitura de PDFs ou de dados parceiros. "
           "As ordens automáticas recebem a mesma entrada embaralhada determinística pela função do protocolo importada pela bancada.", ""]
    for key, val in r.get("predicoes", {}).items():
        ls.append(f"- `{val['arquivo']}`" + (" — regra preservada após gate negativo." if val["regra_preservada_por_gate"] else "."))
    if gate and not gate["aprovado"]:
        ls += ["", "O score exploratório da tabela fica no cache; o arquivo `regra_reordena` conserva a regra por reprovação do teto, "
               "sem promover as alterações do score. O oráculo é só diagnóstico e não pode ser usado em produção."]
    ls += ["", "A avaliação do contrato é executada com `indice_pred`, `ler_offset`, `auditar_unidades`, `referencia`, `expansoes` e a função "
           "`medir` do corretor (que importa integralmente `erros_ponta_a_ponta.medir`); não se chama `bancada.main/avaliar/metricas`, "
           "que alterariam relatórios/caches existentes. Estatísticas vêm de `bancada.resumo`.", "",
           "```powershell", "venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py",
           "venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py --max-minutos 30",
           "venv/Scripts/python.exe -B orquestracao/analises/reordenacao_restrita.py --conferir", "```", ""]
    return "\n".join(ls)+"\n"


def autoteste():
    # O teste usa a funcao oficial eventos; nao cria outra regua de quebras.
    base = list(range(12))
    w1, w2 = (1, 5), (7, 11)
    alts1 = [base[1:5], [2, 1, 3, 4], [4, 1, 2, 3]]
    alts2 = [base[7:11], [8, 7, 9, 10], [10, 7, 8, 9]]
    gt = [0, 2, 1, 3, 4, 5, 6, 8, 7, 9, 10, 11]
    eb = len(e.eventos(base, gt))
    for a, z in itertools.product(alts1, alts2):
        nova = base[:1]+a+base[5:7]+z+base[11:]
        da = len(e.eventos([0]+a+[5], gt))-len(e.eventos(base[0:6], gt))
        dz = len(e.eventos([6]+z+[11], gt))-len(e.eventos(base[6:12], gt))
        exigir(len(e.eventos(nova, gt))-eb == da+dz, "Deltas nao aditivos")
    cs = [{"id": f"u{i}", "bbox": [10, i*15., 80, i*15.+10], "ks": [i], "tipo": "texto", "text": f"linha {i}"} for i in range(8)]
    ctx = {"ordem": [u["id"] for u in cs], "mapa": {u["id"]: u for u in cs},
           "col": {u["id"]: 0 for u in cs}, "margem": {}, "pontes": set()}
    w = {"lo": 0, "hi": 8, "slots": list(range(8)), "col": 0}
    als = list(alternativas(ctx, w))
    exigir(len({tuple(a) for a in als}) == len(als) and
           all(sorted(a) == sorted(ctx["ordem"]) for a in als), "Alternativas invalidas")
    print(f"AUTOTESTE: alternativas unicas ({len(als)}), permutacoes e deltas aditivos da regua oficial: ok", flush=True)


def main():
    global R, EXEC, PRAZO
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--somente-ancoras", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()
    exigir(args.max_minutos >= 0, "Prazo invalido")
    PRAZO = time.monotonic()+args.max_minutos*60 if args.max_minutos else None
    if args.autoteste:
        autoteste()
        return
    with trava():
        R = {"config": CONFIG, "preparando": True}
        if not args.conferir:
            gravar(MD, relatorio(R))
        try:
            hs, splits = fontes()
            fp = c.digest([hs, CONFIG])
            EXEC = BASE / fp
            if (EXEC / "estado.json").exists():
                R = ler(EXEC / "estado.json")
                exigir(R["assinatura_numeros"] == c.digest({k: v for k, v in R.items() if k != "assinatura_numeros"}), "Estado alterado")
            else:
                exigir(not args.conferir, "Sem estado para conferir; executar antes")
                R = {"config": CONFIG, "fingerprint": fp, "fontes": hs, "splits": splits,
                     "memoria_inicio": vigiar(), "bancadas": {}, "completa": False}
            if args.conferir:
                exigir(MD.read_text(encoding="utf-8") == relatorio(R), "Markdown diverge do estado")
                for co in BANCADAS:
                    conferir_predicoes(co)
                print("CONFERE: fontes, estado, relatório e todas as ordens reavaliadas na bancada", flush=True)
                return
            gravar(BASE / "ultima_execucao.json", {"fingerprint": fp})
            R.pop("parada", None)
            salvar()
            ancoras()
            if args.somente_ancoras:
                return
            for co in BANCADAS:
                if not R["bancadas"].get(co, {}).get("completa"):
                    processar(co)
                R["bancadas"][co]["resumos"] = resumos(co, R["bancadas"][co]["paginas"])
                salvar()
                publicar(co)
                if co not in R.get("predicoes_conferidas", {}):
                    conferir_predicoes(co)
                if co == "golden_v4" and not R["gate"]["aprovado"]:
                    R["parada"] = "PARADA METODOLÓGICA: oráculo abaixo de 20% de redução na coluna; problema fora das alternativas consideradas. Não ampliar ou ajustar o corretor."
                    salvar()
                    print(R["parada"], flush=True)
                    return
            exigir(fontes()[0] == hs, "Fontes mudaram durante execucao")
            R["completa"] = True
            salvar()
            print("RELATÓRIO:", b.rel(MD), flush=True)
            print("GATE:", json.dumps(R["gate"], ensure_ascii=False), flush=True)
        except (Exception, KeyboardInterrupt) as exc:
            R["parada"] = str(exc) or "Execução interrompida; retomar o mesmo comando."
            if EXEC is not None:
                salvar()
            else:
                gravar(MD, relatorio(R))
            if isinstance(exc, c.Interromper):
                print("PARADA RETOMÁVEL:", R["parada"], flush=True)
                return
            raise


if __name__ == "__main__":
    main()
