"""Diagnostica a perda de tau das ordens JA SALVAS de E004, E015 e E006.

Reusa a regua oficial, sem inferencia, treino, PDF ou alteracao do protocolo.
Decompoe exatamente o delta de tau por pares de unidades que mudaram de lado,
e mede sensibilidades com peso igual por unidade e por linha de referencia.
O unico artefato de saida e RELATORIO.md; seu comentario final contem o cache
compactado por pagina, com hashes, para retomada apos interrupcao.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/diagnostico_tau_v3.py
  --autoteste       # verifica a decomposicao em exemplos sinteticos
  --conferir        # confere fontes/cache e reproduz o relatorio sem remedir
CPU, quatro threads, um processo. Nao abre teste cego, data/ ou modelos.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse
import base64
import bisect
import collections
import hashlib
import itertools
import json
import math
import re
import statistics as st
import time
import zlib

from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from orquestracao.analises import ordem_lm_arestas as lm
from src.eval.protocolo import ordem_entrada

if "torch" in sys.modules:
    sys.modules["torch"].set_num_threads(4)

OUT = RAIZ / "resultados/diagnostico_tau_v3"
MD = OUT / "RELATORIO.md"
LOCK = RAIZ / "experimentos/TESTE_CEGO.lock"
COORTES = ("golden_v4", "golden_v3_novo", "teste_silver", "validacao_silver")
ESPERADO = dict(zip(COORTES, (44, 27, 89, 15)))
METODOS = ("regra", "hibrido67", "grafo", "mediana", "residual")
CANDIDATOS = METODOS[2:]
BASES = METODOS[:2]
GRAFO = "grafo_K24_maxregret_t0.00"
METRICAS = ("tau", "tau_unidades", "tau_linhas", "tau_unidades_mediana",
            "quebras", "quebras_mil", "fid12", "sucessor_linhas")
TAUS = METRICAS[:4]
MARCADOR = "<!-- CACHE_DIAGNOSTICO_TAU_V3 "
FONTES = {}
PROTEGIDOS = set()
LOCK_SHA = None


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.resolve().relative_to(RAIZ).as_posix()


def fonte(path):
    path = path.resolve()
    exigir(path.is_relative_to(RAIZ) and not path.is_relative_to(RAIZ / "data"),
           "Leitura fora do escopo de resultados/codigo: " + str(path))
    valor = sha(path)
    chave = rel(path)
    exigir(chave not in FONTES or FONTES[chave] == valor, "Fonte mudou durante a leitura: " + chave)
    FONTES[chave] = valor
    return path


def ler_lock():
    if not LOCK.exists():
        return None, set()
    raw = LOCK.read_text(encoding="utf-8")
    obj = json.loads(raw)
    # Protege tambem o PDF inteiro, conservadoramente, como nos experimentos.
    ids = obj.get("page_id", [])
    exigir(isinstance(ids, list) and ids and all(isinstance(x, str) and "#p" in x for x in ids),
           "Formato desconhecido do lock cego; parada obrigatoria")
    protegidos = set(ids) | {x.rsplit("#p", 1)[0] for x in ids}
    protegidos.update(obj.get("pdfs_sha256", {}))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest(), protegidos


def permitido(pid):
    pdf = pid.rsplit("#p", 1)[0]
    exigir(pid not in PROTEGIDOS and pdf not in PROTEGIDOS,
           "Pagina/PDF protegido pelo teste cego; abortando antes de desserializar")


def verificar_id(raw):
    m = re.search(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")', raw)
    exigir(m is not None, "Registro sem page_id")
    pid = json.loads(m.group(1))
    permitido(pid)
    return pid


def ler(path, pagina=False):
    path = fonte(path)
    raw = path.read_text(encoding="utf-8")
    if pagina:
        verificar_id(raw)
    return json.loads(raw)


def jsonl_seguro(path):
    # Valida ID antes de desserializar palavras, unidades ou referencia.
    with path.open(encoding="utf-8") as f:
        for raw in f:
            if raw.strip():
                verificar_id(raw)
                yield json.loads(raw)
    fonte(path)


def paginas(co, ufs):
    if co.startswith("golden"):
        for obj in jsonl_seguro(b.UNIDADES / "bancadas" / (co + ".jsonl")):
            exigir(obj["particao"] == co, "Particao humana divergente")
            yield obj, obj["representacoes"]["linhas"]
    else:
        part = "validacao" if co == "validacao_silver" else "teste"
        for uf in ufs[part]:
            pp = b.UNIDADES / "linhas" / (uf + ".jsonl")
            wp = pp.with_name(uf + ".palavras.jsonl")
            for p, obj in itertools.zip_longest(jsonl_seguro(pp), jsonl_seguro(wp)):
                exigir(p and obj and p["page_id"] == obj["page_id"], "Shards divergentes")
                exigir(p["uf"] == uf and p["particao"] == part, "Split silver divergente")
                exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
                       obj["gt_w"] == list(range(len(obj["palavras"]))), "Referencia silver divergente")
                yield {**obj, "uf": uf}, p


def execucoes():
    runs = {}
    for nome in ("e004_grafo", "e014_cadeias", "e015_mediana", "e006_residual"):
        root = RAIZ / "resultados" / nome
        meta = ler(root / "cache/ultima_execucao.json")
        run = (root / meta["execucao"]).resolve()
        exigir(run.is_relative_to(root), "Ponteiro de cache fora do experimento")
        runs[nome] = run
    escolha = ler(RAIZ / "resultados/e006_residual/congelamento.json")["escolha"]["metodo"]
    return runs, escolha


def salvos(co, pid, runs, escolha):
    nome = e.ac.chave(pid) + ".json"
    rows = {}
    for ex, sub in (("e004_grafo", "inferencia"), ("e015_mediana", "avaliacao"),
                    ("e006_residual", "avaliacao")):
        row = ler(runs[ex] / sub / co / nome, pagina=True)
        exigir(row["page_id"] == pid, "Cache de outra pagina")
        rows[ex] = row
    rg, rm, rr = (rows[x] for x in ("e004_grafo", "e015_mediana", "e006_residual"))
    residual = escolha if escolha in rr["resultados"] else "e006_residual"
    mapas = {"regra": (rr, "regra"), "hibrido67": (rr, "hibrido67"),
             "grafo": (rg, GRAFO), "mediana": (rm, "b_mediana"), "residual": (rr, residual)}
    saida = {n: row["resultados"][nm] for n, (row, nm) in mapas.items()}
    for n in ("regra", "hibrido67", "grafo"):
        nm = GRAFO if n == "grafo" else n
        for row in (rg, rm, rr):
            if nm in row["resultados"]:
                exigir(row["resultados"][nm]["ordem"] == saida[n]["ordem"], "Ordens dos caches divergem")
                for k in ("tau", "quebras", "quebras_mil", "fid12", "sucessor_linhas"):
                    exigir(abs(row["resultados"][nm]["metricas"][k] - saida[n]["metricas"][k]) < 1e-11,
                           "Metricas dos caches divergem")
    # Mediana original e a variante com salvaguarda sao distinguidas, sem escolher.
    guard = rm["resultados"]["b_mediana_salvaguarda"]["ordem"] != saida["mediana"]["ordem"]
    pares = {}
    for n in CANDIDATOS:
        row = rr if n == "residual" else rm
        nm = residual if n == "residual" else GRAFO if n == "grafo" else "b_mediana"
        pares[n] = row["pares_sucessor"].get(nm, {})
    corpos = {n: row.get("corpo", {}).get(nm) for n, (row, nm) in mapas.items()}
    corpos["grafo"] = rm["corpo"][GRAFO]
    return saida, pares, corpos, guard, rr["operacoes"][residual]


def ancora(runs, ufs):
    valores = []
    for obj, p in paginas("golden_v4", ufs):
        path = runs["e004_grafo"] / "inferencia/golden_v4" / (e.ac.chave(p["page_id"]) + ".json")
        row = ler(path, pagina=True)
        ordem = row["resultados"]["regra"]["ordem"]
        b.auditar_unidades(p, obj)
        exp = b.expansoes(obj, p)
        exigir(len(ordem) == len(exp) and set(ordem) == set(exp), "Ancora usa outra segmentacao")
        seq = [k for u in ordem for k in exp[u]]
        tau = e.o.kendall_tau(seq, obj["gt_w"])
        quebras = len(e.eventos(seq, obj["gt_w"]))
        valores.append((tau, quebras))
    a = {"n": len(valores), "tau": st.mean(v[0] for v in valores),
         "quebras": st.mean(v[1] for v in valores)}
    exigir(a["n"] == 44 and abs(a["tau"] - .985948) < .00000051 and
           abs(a["quebras"] - 6.045455) < .00000051, "PARE: ancora nao reproduzida: " + str(a))
    print("Ancora reproduzida: " + str(a), flush=True)
    return a


def colunas(p, ws):
    # Mesmas funcoes geometricas do contexto E004; nenhuma ordem e predita.
    cs = p["bounding_boxes"]
    h = st.median(w[4] - w[2] for w in ws if w[4] > w[2])
    _, corpo, _, _ = e.j.particao(cs, ws, p["dimensions"]["height"], "geo")
    cortes = e.o.vales_locais(cs, corpo, h, e.FIXA.vale) if corpo else []
    if not cortes and corpo:
        cortes = e.o.vales(cs, corpo, h, e.FIXA.vale)
    return len(cortes) + 1, {u["id"]: bisect.bisect_right(cortes, (u["bbox"][0]+u["bbox"][2])/2)
                            for u in cs}


def decompor(base, nova, ranks, tamanhos, n_palavras, cols=None):
    """Particiona pares trocados; usa Kendall oficial para fechar a identidade.

    Para u antes de v na base, c conta pares ouro com palavra(u)>palavra(v).
    Trocar os dois acrescenta |u|*|v|-2*c inversoes. Nao e outra regua de tau:
    e uma atribuicao exata da variacao do tau existente, validada por pagina.
    """
    pos = {u: i for i, u in enumerate(nova)}
    den = math.comb(sum(len(x) for x in ranks.values()), 2)
    grandes = {u for u, tam in tamanhos.items() if tam > .20*n_palavras}
    out = {"delta": 0., "delta_grandes": 0., "adverso": 0., "adverso_grandes": 0.,
           "favoravel": 0., "favoravel_grandes": 0., "pares_trocados": 0,
           "grandes_movidas": [], "principais_pares": [],
           "delta_mesma_coluna": 0., "delta_entre_colunas": 0.}
    tocadas = set()
    principais = []
    for i, u in enumerate(base):
        for v in base[i+1:]:
            if pos[u] < pos[v]:
                continue
            out["pares_trocados"] += 1
            tocadas.update((u, v))
            a, z = ranks[u], ranks[v]
            c = sum(bisect.bisect_left(z, x) for x in a)
            inversoes = len(a)*len(z)-2*c
            delta = -2*inversoes/den if den else 0.
            grande = u in grandes or v in grandes
            out["delta"] += delta
            out["delta_grandes"] += delta if grande else 0.
            chave_col = "delta_mesma_coluna" if cols is None or cols[u] == cols[v] else "delta_entre_colunas"
            out[chave_col] += delta
            tipo = "adverso" if delta < 0 else "favoravel"
            out[tipo] += abs(delta)
            out[tipo+"_grandes"] += abs(delta) if grande else 0.
            if delta:
                principais.append({"u": u, "v": v, "delta": delta, "grande": grande})
    out["grandes_movidas"] = sorted(grandes & tocadas)
    adversos = sorted((p for p in principais if p["delta"] < 0), key=lambda x: x["delta"])
    favoraveis = sorted((p for p in principais if p["delta"] > 0), key=lambda x: -x["delta"])
    # Mostra perdas mesmo quando um unico reparo favoravel tem peso maior.
    out["principais_pares"] = adversos[:8] + favoraveis[:3]
    return out


def analisar(co, obj, p, runs, escolha):
    pid = p["page_id"]
    salvo, pares_salvos, corpos, guard, ops = salvos(co, pid, runs, escolha)
    ids = b.auditar_unidades(p, obj)
    exp = b.expansoes(obj, p)
    q = b.referencia(obj, p)
    gt = q["gt_w"]
    rg = {k: i for i, k in enumerate(gt)}
    dono = {k: u for u, ks in exp.items() for k in ks}
    ranks = {u: sorted(rg[k] for k in ks if k in rg) for u, ks in exp.items()}
    tamanhos = {u: len(ks) for u, ks in exp.items()}
    tipos = {u["id"]: u.get("tipo", "texto") for u in p["bounding_boxes"]}
    gold_u = list(dict.fromkeys(dono[k] for k in gt))
    gold_um = sorted(gold_u, key=lambda u: (st.median(ranks[u]), ranks[u][0]))
    dono_l = {k: L["id"] for L in q["gold_lines"] for k in L["ks"]}
    gold_l = q["gt_l"]
    linhas = {L["id"]: L["ks"] for L in q["gold_lines"]}
    trs = [{"linha_a": a, "linha_z": z, "palavra_a": linhas[a][-1], "palavra_z": linhas[z][0]}
           for a, z in zip(gold_l, gold_l[1:])]
    nc, cols = colunas(p, obj["palavras"])
    maior = max(tamanhos, key=tamanhos.get)
    atomos = [u for u in ids if tipos[u] != "texto"]
    maior_atomo = max(atomos, key=tamanhos.get) if atomos else None
    fragmentadas = sum(any(z != a+1 for a, z in zip(rs, rs[1:])) for rs in ranks.values())
    out = {"page_id": pid, "uf": obj["uf"], "unidades": len(ids), "palavras": len(obj["palavras"]),
           "ouro": len(gt), "linhas": len(gold_l), "colunas": nc, "tipos": tipos,
           "maior": maior, "maior_atomo": maior_atomo, "tamanhos": tamanhos, "cols": cols,
           "unidades_ouro_intercaladas": fragmentadas, "unidades_sem_ouro": sum(not x for x in ranks.values()),
           "salvaguarda_difere": guard, "metricas": {}, "contrastes": {}, "corpo": corpos,
           "ordens": {}, "linhas_fragmentadas": {}, "operacoes_residuais": ops}
    hits = {}
    for nome, row in salvo.items():
        ordem = row["ordem"]
        exigir(len(ordem) == len(ids) and set(ordem) == set(ids), "Predicao de outra segmentacao")
        exigir(row["cobertura_palavras"] == 1., "Cobertura incompleta")
        seq = [k for u in ordem for k in exp[u]]
        met = row["metricas"].copy()
        exigir(abs(e.o.kendall_tau(seq, gt)-met["tau"]) < 1e-11, "Tau salvo nao reproduzido")
        exigir(len(e.eventos(seq, gt)) == met["quebras"], "Quebras salvas nao reproduzidas")
        pu = [u for u in ordem if ranks[u]]
        pl = list(dict.fromkeys(dono_l[k] for k in seq if k in dono_l))
        exigir(set(pl) == set(gold_l) and len(pl) == len(gold_l), "Linhas nao pareadas")
        met["tau_unidades"] = e.o.kendall_tau(pu, gold_u)
        met["tau_unidades_mediana"] = e.o.kendall_tau(pu, gold_um)
        met["tau_linhas"] = e.o.kendall_tau(pl, gold_l)
        hits[nome] = lm.acertos(q, seq, trs, met)
        out["metricas"][nome] = {k: met[k] for k in METRICAS}
        out["ordens"][nome] = ordem
        runs_l = [lid for lid, _ in itertools.groupby(dono_l[k] for k in seq if k in dono_l)]
        cont = collections.Counter(runs_l)
        out["linhas_fragmentadas"][nome] = sum(v > 1 for v in cont.values())
    # Confere a permutacao de entrada do protocolo, sem executar ordenador.
    indices = ordem_entrada({"page_id": pid, "bounding_boxes": p["bounding_boxes"]})
    import random
    esperada = list(range(len(ids)))
    random.Random(f"entrada-{pid}").shuffle(esperada)
    exigir(indices == esperada, "Entrada embaralhada divergente")
    for nome in CANDIDATOS:
        out["contrastes"][nome] = {}
        for base in BASES:
            d = decompor(salvo[base]["ordem"], salvo[nome]["ordem"], ranks, tamanhos, len(obj["palavras"]), cols)
            dif = out["metricas"][nome]["tau"] - out["metricas"][base]["tau"]
            exigir(abs(d["delta"]-dif) < 1e-10, "Decomposicao de tau nao fecha: " + pid)
            exigir(abs(d["delta_mesma_coluna"]+d["delta_entre_colunas"]-dif) < 1e-10,
                   "Particao geometrica nao fecha: " + pid)
            rep = sum(new and not old for old, new in zip(hits[base], hits[nome]))
            reg = sum(old and not new for old, new in zip(hits[base], hits[nome]))
            if base in pares_salvos[nome]:
                antigo = pares_salvos[nome][base]
                exigir(rep == sum(v["reparos"] for v in antigo.values()) and
                       reg == sum(v["regressoes"] for v in antigo.values()), "Sucessores divergem do cache")
            d.update(reparos=rep, regressoes=reg)
            out["contrastes"][nome][base] = d
    return out


def f(x, n=6):
    if x is not None and abs(x) < .5*10**(-n):
        x = 0.
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def tabela(cab, rows):
    return ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"] + [
        "| " + " | ".join(str(x) for x in row) + " |" for row in rows]


def delta(r, nome, base, k):
    return r["metricas"][nome][k] - r["metricas"][base][k]


def sinal(v):
    return "perde" if v < -1e-12 else "ganha" if v > 1e-12 else "iguala"


def concentracao(rows, nome, base):
    perdas = sorted((r for r in rows if delta(r, nome, base, "tau") < -1e-12),
                    key=lambda r: delta(r, nome, base, "tau"))
    total = -sum(delta(r, nome, base, "tau") for r in perdas)
    acumulado, top = 0., []
    for r in perdas:
        acumulado -= delta(r, nome, base, "tau")
        top.append((r, acumulado/total))
        if acumulado >= .8*total:
            break
    return top, total


def resumo_curto(estado):
    v3 = estado["dados"]["golden_v3_novo"]
    frases = []
    for nome in CANDIDATOS:
        top, perda = concentracao(v3, nome, "hibrido67")
        frases.append(f"{nome}: Δτ palavras {f(st.mean(delta(r,nome,'hibrido67','tau') for r in v3))}; "
                      f"{len(top)} página(s) cobrem ≥80% da perda bruta")
    perdas = sum(-r["contrastes"][n]["hibrido67"]["delta"] for r in v3 for n in CANDIDATOS
                 if r["contrastes"][n]["hibrido67"]["delta"] < -1e-12)
    grandes = -sum(r["contrastes"][n]["hibrido67"]["delta_grandes"] for r in v3 for n in CANDIDATOS
                   if r["contrastes"][n]["hibrido67"]["delta"] < -1e-12)
    return [f"1. Âncora reproduzida: golden_v4 τ {f(estado['ancora']['tau'])} e {f(estado['ancora']['quebras'])} quebras/página.",
            "2. " + "; ".join(frases) + ".",
            f"3. Unidades >20% explicam {f(100*grandes/perdas,2)}% da perda bruta vs híbrido no v3; o caso de átomos gigantes do RN não explica essa perda.",
            "4. Grafo/mediana ganham τ de unidades vs híbrido no v3, mas perdem τ de palavras/linhas; residual perde nas três granularidades.",
            "5. Golden_v3_novo já foi consultado em rodadas anteriores; diagnóstico sem seleção, novo modelo ou veredito de cartão.",
            "6. CPU, ordens salvas, cobertura integral; teste cego preservado; proposta confirmatória depende de registro prévio."]


def estatisticas(rows):
    ls = []
    ms = []
    for nome in METODOS:
        mm = rows[0]["metricas"][nome]
        vals = lambda k: [r["metricas"][nome][k] for r in rows]
        ms.append([nome, *[f(fun(vals(k))) for k in TAUS for fun in (st.mean, st.median)],
                   f(st.mean(vals("quebras"))), f(st.mean(vals("fid12"))), f(st.mean(vals("sucessor_linhas")))])
    ls += tabela(["Método", "τ palavras média", "mediana", "τ unidades média", "mediana",
                  "τ linhas média", "mediana", "τ unid. âncora mediana média", "mediana",
                  "Quebras/pág", "Fid12", "Sucessor linhas"], ms)
    ls += ["", "### Contrastes pareados", "",
           "Δ = método − base. M/I/P respeita o sentido da métrica. A mediana Δ é a mediana das diferenças "
           "pareadas, distinta da diferença entre as medianas absolutas acima. IC95 por veículo; p de Wilcoxon "
           "Pratt aplicado às médias pareadas dos veículos, bilateral, descritivo.", ""]
    W = b.PESOS_CLUSTER(rows)
    grupos = sorted({r["uf"] for r in rows})
    tab = []
    for nome in CANDIDATOS:
        for base in BASES:
            for k in METRICAS:
                ds = [delta(r, nome, base, k) for r in rows]
                ic = e.media_ic(ds, W)
                dvs = [st.mean(d for r, d in zip(rows, ds) if r["uf"] == uf) for uf in grupos]
                p = e.pratt(dvs)["p"]
                orientado = [-d for d in ds] if k in ("quebras", "quebras_mil") else ds
                cont = [sum(v > 1e-12 for v in orientado), sum(abs(v) <= 1e-12 for v in orientado),
                        sum(v < -1e-12 for v in orientado)]
                tab.append([nome, base, k, f(ic["media"]), f(st.median(ds)),
                            f"[{f(ic['ic'][0])}; {f(ic['ic'][1])}]", f(p), "/".join(map(str, cont))])
    ls += tabela(["Método", "Base", "Métrica", "Δ médio", "Mediana Δ", "IC95 veículo", "p veículo", "M/I/P"], tab)
    ls += ["", "### A afirmação descritiva ‘perde τ’ depende do peso?", ""]
    tab = []
    for nome in CANDIDATOS:
        for base in BASES:
            ds = [st.mean(delta(r, nome, base, k) for r in rows) for k in TAUS]
            med = [st.median(r["metricas"][nome][k] for r in rows) -
                   st.median(r["metricas"][base][k] for r in rows) for k in TAUS[:3]]
            tab.append([nome, base, *[f"{f(v)} ({sinal(v)})" for v in ds],
                        "; ".join(f"{k}: {f(v)}" for k, v in zip(("pal.", "unid.", "lin."), med)),
                        "sim" if len({sinal(v) for v in ds[:3]}) > 1 else "não"])
    ls += tabela(["Método", "Base", "Δ média palavras", "Δ média unidades", "Δ média linhas",
                  "Δ média unid. âncora mediana", "Δ medianas absolutas", "Sinal muda?"], tab)
    ls += ["", "### Sucessores corretos recuperados/perdidos", ""]
    ls += tabela(["Método", "Base", "Reparos", "Regressões"], [
        [nome, base, sum(r["contrastes"][nome][base]["reparos"] for r in rows),
         sum(r["contrastes"][nome][base]["regressoes"] for r in rows)]
        for nome in CANDIDATOS for base in BASES])
    ls += ["", "### Corpo e fragmentação de linhas (diagnósticos já salvos)", "",
           "Corpo usa a máscara automática de margens dos experimentos de origem; não cria uma "
           "nova política de avaliação. Fragmentação conta linhas-ouro que reaparecem em trechos separados "
           "da sequência; τ de linhas pela primeira ocorrência não penaliza toda essa fragmentação.", ""]
    tab = []
    for nome in METODOS:
        cs = [r["corpo"][nome] for r in rows if r["corpo"][nome] and r["corpo"][nome].get("elegivel")]
        tab.append([nome, len(cs), *[f(st.mean(z[k] for z in cs)) if cs else "—" for k in
                                    ("tau", "quebras", "fid12", "sucessor_linhas")],
                    sum(r["linhas_fragmentadas"][nome] for r in rows)])
    ls += tabela(["Método", "n corpo", "τ palavras corpo", "Quebras corpo", "Fid12 corpo",
                  "Sucessor corpo", "Linhas fragmentadas (total)"], tab)
    return ls


def atribuicao(rows):
    ls = ["### Quanto da diferença vem de unidades >20% da página?", ""]
    tab = []
    for nome in CANDIDATOS:
        for base in BASES:
            ds = [r["contrastes"][nome][base] for r in rows]
            losers = [d for d in ds if d["delta"] < -1e-12]
            perda = sum(-d["delta"] for d in losers)
            netgrande = -sum(d["delta_grandes"] for d in losers)
            adverso = sum(d["adverso"] for d in ds)
            advgrande = sum(d["adverso_grandes"] for d in ds)
            tab.append([nome, base, sum(bool(d["grandes_movidas"]) for d in ds),
                        f(st.mean(d["delta_grandes"] for d in ds)),
                        f(st.mean(d["delta"]-d["delta_grandes"] for d in ds)), f(perda),
                        f(netgrande), f(100*netgrande/perda, 2)+"%" if perda else "—",
                        f(100*advgrande/adverso, 2)+"%" if adverso else "—"])
    ls += tabela(["Método", "Base", "Páginas grande muda lado", "Δτ médio pares com grande",
                  "Δτ médio demais pares", "Perda bruta páginas (Στ)", "Parcela líquida grande nos perdedores (Στ)",
                  "% perda bruta explicada", "% contribuições adversas com grande"], tab)
    ls += ["", "As duas colunas Δτ somam exatamente o Δ médio total. Cada par com duas unidades grandes "
           "entra uma única vez. ‘% perda bruta explicada’ soma a contribuição líquida desses pares somente "
           "nas páginas que pioraram e divide pela soma das quedas dessas páginas; pode exceder 100% se outros "
           "pares compensarem a perda. A última coluna usa todas as contribuições adversas, antes de compensações, "
           "e fica entre 0% e 100%. Trata-se de atribuição algébrica, não de causalidade nem de exclusão de páginas.", ""]
    return ls


def paginas_80(rows):
    ls = ["### Páginas que acumulam pelo menos 80% da perda bruta", "",
          "Ordenadas pela queda de τ, separadamente para cada método/base. O denominador soma somente "
          "quedas; ganhos não cancelam os casos ruins. Στ não é outra média. Maior unidade inclui linhas; "
          "‘átomo’ usa tipo automático diferente de texto. Colunas são a proxy geométrica global do E004.", ""]
    tab, detalhes = [], {}
    for nome in CANDIDATOS:
        for base in BASES:
            top, total = concentracao(rows, nome, base)
            if not top:
                ls += [f"{nome} × {base}: nenhuma perda de τ.", ""]
            for r, acumulada in top:
                u, a = r["maior"], r["maior_atomo"]
                tam = r["tamanhos"][u]
                atom = (f"{a}: {r['tamanhos'][a]} ({f(100*r['tamanhos'][a]/r['palavras'],2)}%)" if a else "nenhum")
                tab.append([nome, base, f"`{r['page_id']}`", f(delta(r,nome,base,"tau")),
                            f(delta(r,nome,base,"quebras"),0), f(total), f(100*acumulada,2)+"%",
                            r["unidades"], f"{r['palavras']}/{r['ouro']}",
                            f"{u}: {tam} ({f(100*tam/r['palavras'],2)}%)", atom, r["colunas"]])
                detalhes.setdefault(r["page_id"], (r, []))[1].append((nome, base))
    ls += tabela(["Método", "Base", "Página", "Δτ", "Δ quebras", "Perda bruta total Στ", "% acumulada",
                  "Unidades", "Palavras total/ouro", "Maior unidade: palavras (%)", "Maior átomo", "Colunas"], tab)
    ls += ["", "#### O que trocou de posição nessas páginas", "",
           "Postos começam em zero. A lista inclui todas as unidades cujo posto mudou, inclusive deslocamentos "
           "causados pela movimentação de outra unidade; não representa uma sequência inferida de operações. "
           "Os maiores pares trocados explicam a contribuição ao Δτ (valor negativo = piora).", ""]
    for pid, (r, comps) in detalhes.items():
        ls += [f"<details><summary>{pid}</summary>", ""]
        for nome, base in comps:
            bp = {u: i for i, u in enumerate(r["ordens"][base])}
            np = {u: i for i, u in enumerate(r["ordens"][nome])}
            moved = [u for u in r["ordens"][base] if bp[u] != np[u]]
            d = r["contrastes"][nome][base]
            ls += [f"**{nome} × {base}**: {len(moved)} unidades com posto diferente; "
                   f"{d['pares_trocados']} pares mudaram de lado; grandes envolvidas: "
                   f"`{', '.join(d['grandes_movidas']) or 'nenhuma'}`. "
                   f"Δτ de pares na mesma coluna {f(d['delta_mesma_coluna'])}; "
                   f"entre colunas {f(d['delta_entre_colunas'])} (proxy geométrica).", ""]
            ls += tabela(["Unidade", "Tipo", "Palavras", "% página", "Coluna", "Posto base → método"], [
                [u, r["tipos"][u], r["tamanhos"][u], f(100*r["tamanhos"][u]/r["palavras"],2),
                 r["cols"][u], f"{bp[u]} → {np[u]}"] for u in moved])
            ls += ["", "Maiores contribuições (até oito adversas e três favoráveis): " + "; ".join(
                f"`{d0['u']}` ({r['tamanhos'][d0['u']]} pal.) antes de `{d0['v']}` "
                f"({r['tamanhos'][d0['v']]} pal.) na base, depois no método: Δτ {f(d0['delta'])}"
                for d0 in d["principais_pares"]) + ".", ""]
            if nome == "residual":
                ls += ["Operações já salvas pelo E006: " + json.dumps(r["operacoes_residuais"], ensure_ascii=False) + ".", ""]
        ls += ["</details>", ""]
    return ls


def por_pagina(rows):
    ls = ["### Todas as páginas: Δτ de palavras / Δ quebras", "",
          "Cada célula é método − base; página inteira, sem remover átomos.", ""]
    ls += tabela(["Página", *[n+" × "+base for n in CANDIDATOS for base in BASES]], [
        [f"`{r['page_id']}`", *[f"{f(delta(r,n,base,'tau'))} / {f(delta(r,n,base,'quebras'),0)}"
                                 for n in CANDIDATOS for base in BASES]] for r in rows])
    return ls


def conclusoes(estado):
    ls = ["## Interpretação em linguagem simples (diagnóstico, sem veredito)", ""]
    for co in COORTES[:3]:
        rows = estado["dados"][co]
        ls += [f"**{co}.**", ""]
        for nome in CANDIDATOS:
            ds = [st.mean(delta(r,nome,"hibrido67",k) for r in rows) for k in TAUS[:3]]
            top, total = concentracao(rows, nome, "hibrido67")
            losers = [r for r in rows if delta(r,nome,"hibrido67","tau") < -1e-12]
            grandes = -sum(r["contrastes"][nome]["hibrido67"]["delta_grandes"] for r in losers)
            padrao = ("o sinal da perda depende da granularidade" if len({sinal(v) for v in ds}) > 1
                      else "o sinal é o mesmo nas três granularidades")
            ls.append(f"- {nome}: {padrao}; Δ médio palavras/unidades/linhas = "
                      f"{' / '.join(f(v) for v in ds)}. {len(top)} de {len(rows)} páginas acumulam ≥80% "
                      f"das quedas; pares envolvendo unidades >20% explicam "
                      f"{f(100*grandes/total,2)+'%' if total else 'parcela não definida (sem quedas)'} "
                      "da perda bruta nas páginas que pioram.")
        ls += [""]
    v3 = estado["dados"]["golden_v3_novo"]
    casos = {}
    for nome in CANDIDATOS:
        for r, _ in concentracao(v3, nome, "hibrido67")[0]:
            casos[r["page_id"]] = r
    ls += ["Tipos de página que concentram as perdas no golden_v3_novo (união dos casos acima):", ""]
    ls += tabela(["Página", "Unidades (>67 = densa)", "Colunas estimadas", "Maior unidade (%)", "Tipo"], [
        [f"`{r['page_id']}`", r["unidades"], r["colunas"],
         f(100*r["tamanhos"][r["maior"]]/r["palavras"],2), r["tipos"][r["maior"]]] for r in casos.values()])
    ls += ["", "**De onde vem a perda no v3:** o padrão dominante é falha de ordenação com concentração "
           "em poucas páginas, somada ao efeito dos pesos e da média. A hipótese de que a perda externa "
           "seja explicada por átomos gigantes como no RN não se sustenta nesta atribuição. "
           "Para grafo/mediana, os casos dominantes são páginas densas do RJ com três colunas estimadas "
           "e sem unidade gigante. A melhora agregada do τ de unidades contra o híbrido vem do balanço "
           "das demais páginas e não apaga as trocas erradas nas páginas críticas. Contra a regra, "
           "os três τ médios do grafo/mediana caem (ver tabela de contrastes).", ""]
    for nome in CANDIDATOS:
        top, total = concentracao(v3, nome, "hibrido67")
        for r, acumulada in top:
            ds = [delta(r,nome,"hibrido67",k) for k in TAUS[:3]]
            ls += [f"- {nome}, `{r['page_id']}`: Δτ palavras/unidades/linhas "
                   f"{' / '.join(f(v) for v in ds)}; Δ quebras "
                   f"{f(delta(r,nome,'hibrido67','quebras'),0)}; perda acumulada "
                   f"{f(100*acumulada,2)}%. A queda é observável nas granularidades acima."]
            if nome == "residual" and r["operacoes_residuais"]:
                op = r["operacoes_residuais"][0]
                tamanho = sum(r["tamanhos"][u] for u in op["unidades"])
                ls += [f"  A operação salva `{op['tipo']}` moveu `{', '.join(op['unidades'])}` "
                       f"({len(op['unidades'])} unidades, {tamanho} palavras) do posto {op['origem']} "
                       f"para {op['destino']}. A maior unidade da página pode permanecer parada; "
                       "por isso ter uma unidade >20% não implica que ela explique a perda."]
    ls += ["", "A troca de dois trechos corretos por dentro é uma falha real de ordem global, mesmo quando "
           "quase todos os sucessores locais são preservados. O τ de palavras dá peso ao produto dos tamanhos "
           "dos trechos: ele pode tornar poucas decisões sobre átomos muito maiores que muitas correções de "
           "vizinhança. Quando os sinais divergem nas sensibilidades, a frase genérica ‘o método perde τ’ "
           "precisa especificar **τ de palavras, média por página**. Isso caracteriza tanto erro do método "
           "quanto efeito do peso da métrica; não demonstra que a referência esteja errada nem autoriza "
           "descartar os casos. Atribuição nula a grandes não exclui falhas globais envolvendo vários itens menores.", "",
           "## Proposta para registrar antes de abrir o teste cego (não aplicada)", "",
           "Manter **quebras por página como desfecho primário do estudo**, conforme o plano. Para o controle "
           "de ordem global, manter **τ de palavras da régua atual como τ principal**, com macro-média das UFs "
           "e IC95 do Δ por bootstrap de PDFs; publicar também médias por página/UF para rastreabilidade. "
           "Conservar o contraste final previamente definido contra híbrido 67 e regra e a política de cobertura. "
           "Este diagnóstico não altera margens de não inferioridade nem escolhe métrica pelo sinal observado.", "",
           "Pré-especificar como sensibilidades, em todas as páginas e com os mesmos métodos: τ de linhas "
           "de referência com peso igual, τ de unidades com peso igual, medianas absolutas por página e mediana "
           "dos Δ pareados. Fixar a projeção por primeira ocorrência e publicar a âncora mediana das unidades "
           "apenas como verificação da ambiguidade; contar fragmentações, unidades sem ouro e reentradas. "
           "Pré-especificar o estrato ‘maior unidade >20% das palavras da página’, publicar ambos os estratos "
           "sem excluir páginas, as maiores quedas e a decomposição algébrica; os estratos não mudam a decisão "
           "confirmatória. Relatar sucessores, reparos/regressões e fidelidade de 12 junto de τ.", "",
           "Registrar agora definições, denominadores, agregação, semente/reamostras, comparações e regra de "
           "multiplicidade (Holm se houver até três finalistas), com aprovação do Pedro/orquestrador. "
           "Só depois realizar a única avaliação confirmatória pelo orquestrador. Nenhum cartão, registro "
           "ou protocolo foi alterado por este script.", ""]
    return ls


def relatorio(estado):
    dados = estado["dados"]
    completo = all(len(dados.get(co, [])) == ESPERADO[co] for co in COORTES)
    if not completo:
        return "\n".join(["Diagnóstico em andamento; cache retomável no comentário final.",
                           f"Âncora: τ {f(estado['ancora']['tau'])}; quebras {f(estado['ancora']['quebras'])}.",
                           *[f"{co}: {len(dados.get(co, []))}/{ESPERADO[co]} páginas." for co in COORTES]]) + "\n"
    ls = [*resumo_curto(estado), "", "# Diagnóstico da perda de τ no golden_v3_novo", "",
          "## Escopo, integridade e definições", "",
          "Somente ordens/medições salvas e representação congelada em resultados/unidades_sem_caixas. "
          "E004: grafo K24 max-regret t0; E015: mediana original (b_mediana); E006: configuração já escolhida "
          f"`{estado['escolha']}`. A mediana com salvaguarda difere da original em "
          f"{sum(r['salvaguarda_difere'] for rs in dados.values() for r in rs)} páginas nestas bancadas. "
          "Não há treino, nova escolha de parâmetros, inferência de modelo, abertura de PDF ou leitura/escrita "
          "sob data/. O lock protege páginas e PDFs inteiros, com validação de ID antes da desserialização. "
          "Entrada embaralhada conferida com random.Random(f'entrada-{page_id}').", "",
          f"Âncora recalculada a partir das predições da regra, pela expansão canônica e funções oficiais: "
          f"{estado['ancora']['n']} páginas; τ {f(estado['ancora']['tau'],12)}; "
          f"{f(estado['ancora']['quebras'],12)} quebras/página. A análise só começou após essa conferência. "
          "Cada ordem é uma permutação da mesma segmentação com cobertura integral; τ de palavras e quebras "
          "salvos são reproduzidos página a página. Fidelidade de 12 e sucessor vêm das medições salvas; "
          "reparos/regressões usam ordem_lm_arestas.acertos e conferem os pares salvos quando disponíveis.", "",
          "τ de unidades: projetar a referência de palavras para IDs de unidade, conservar a primeira "
          "ocorrência de cada ID e chamar o mesmo kendall_tau oficial. Unidades sem palavra-ouro ficam fora "
          "desse τ (são contadas). A referência pode intercalar uma unidade: por isso também se informa "
          "τ de unidades com âncora na mediana dos postos de suas palavras, desempate pelo primeiro posto. "
          "Esta é somente uma sensibilidade à projeção, sem seleção.", "",
          "τ de linhas: projetar a sequência predita de palavras para IDs de **linha da referência**, "
          "conservar primeira ocorrência e chamar kendall_tau contra gt_l. Cada linha conta uma vez, "
          "inclusive dentro de átomos; não é τ de unidades nem um indicador de integridade da linha. "
          "Linhas fragmentadas podem ter τ alto: o sucessor oficial continua exigindo linhas intactas. "
          "No silver essas linhas são trechos geométricos partidos para respeitar o fluxo do PDF.", "",
          "Decomposição: apenas pares de unidades que trocam ordem relativa podem mudar τ de palavras. "
          "Para u antes de v na base, c é o número de pares de palavras-ouro u,v em ordem inversa no ouro. "
          "A troca acrescenta |u|·|v|−2c inversões, logo Δτ = −2·Δinversões/C(Nouro,2). "
          "A soma dos pares fecha o Δτ oficial em cada página (tolerância 10⁻¹⁰). ‘Grande’ usa estritamente "
          ">20% das palavras totais da página, sem arredondamento; atribuição usa só pares de palavras-ouro. "
          "Livre/não anotado continua na sequência ao medir quebras, conforme a régua.", "",
          f"Bootstrap importado: {b.NBOOT} reamostras, semente {b.SEMENTE}, percentil 95%, reamostragem "
          "de veículos inteiros e média por página; nenhuma página é tratada como independente dentro "
          "do veículo. Não há teste confirmatório aqui. As três bancadas são separadas; RN é apêndice "
          "do ajuste, com IC degenerado (um veículo). Bancadas podem compartilhar páginas e não se somam.", ""]
    for co in COORTES:
        rows = dados[co]
        ls += [f"## {co}" + (" — apêndice do ajuste" if co == "validacao_silver" else ""), "",
               f"{len(rows)} páginas; {len({r['uf'] for r in rows})} veículos; "
               f"{sum(r['unidades_ouro_intercaladas'] for r in rows)} unidades não contíguas no ouro; "
               f"{sum(r['unidades_sem_ouro'] for r in rows)} unidades sem palavras-ouro. "
               "As contagens não significam erro de anotação: átomos e linhas automáticas podem recobrir "
               "trechos intercalados da referência.", ""]
        ls += estatisticas(rows) + [""] + atribuicao(rows)
        if co in COORTES[:2]:
            ls += paginas_80(rows) + por_pagina(rows) + [""]
    rn = next(r for r in dados["validacao_silver"] if r["page_id"].endswith("DOE-RN_2022-12-29_Ordinaria.pdf#p40"))
    ls += ["## RN p40: contraprova ao resumo ‘seis linhas curtas’", "",
           f"`{rn['page_id']}` tem {rn['unidades']} unidades e {rn['palavras']} palavras. "
           "Os tamanhos abaixo vêm da expansão canônica, sem abrir o PDF. A troca observada envolve "
           "duas unidades grandes, e não apenas linhas curtas.", ""]
    ls += tabela(["Unidade", "Tipo", "Palavras", "% página"], [
        [u, rn["tipos"][u], rn["tamanhos"][u], f(100*rn["tamanhos"][u]/rn["palavras"],2)]
        for u in rn["ordens"]["regra"]])
    ls += [""] + tabela(["Método", "Ordem", "τ palavras", "τ unidades", "τ linhas", "Quebras", "Sucessor"], [
        [n, " → ".join(rn["ordens"][n]), *[f(rn["metricas"][n][k]) for k in
         ("tau", "tau_unidades", "tau_linhas", "quebras", "sucessor_linhas")]] for n in METODOS]) + [""]
    ls += conclusoes(estado)
    ls += ["## Limitações e rastreabilidade", "",
           "Golden_v3_novo já foi consultado em rodadas anteriores: este diagnóstico é exploratório e não "
           "recupera independência confirmatória. Há poucos veículos e páginas, um anotador humano, "
           "referência silver ruidosa e dependência entre páginas/bancadas. Os ICs por veículo com poucos "
           "grupos e os p-valores não sustentam decisões de superioridade. Nenhuma conclusão visual "
           "sobre o conteúdo foi feita. A coluna estimada é uma proxy global, não anotação humana de layout.", "",
           "A sensibilidade de unidades depende da segmentação e da projeção de uma referência que pode "
           "intercalar a mesma unidade; τ de linhas depende da definição de linha, sobretudo no silver. "
           "São diagnósticos complementares, não razões para apagar a queda do τ de palavras. Não há "
           "medição de incerteza da anotação, causalidade de features ou generalização ao teste cego.", "",
           "Fontes consumidas são verificadas por SHA256 antes de concluir e na retomada; o cache por página "
           "fica compactado no comentário deste mesmo relatório para não criar outro artefato. A retomada "
           "não confia em cache com código, lock ou fontes diferentes. Escrita atômica somente neste "
           "relatório; código e fontes de outros agentes não são alterados.", "",
           f"Comando: `venv/Scripts/python.exe -B orquestracao/analises/diagnostico_tau_v3.py`. "
           f"Conferência: acrescentar `--conferir`. Páginas processadas: {sum(len(x) for x in dados.values())}; "
           f"código SHA256 `{estado['codigo_sha256']}`; lock SHA256 `{estado['lock_sha256']}`.", "",
           "### Execuções congeladas lidas", ""]
    ls += [f"- {k}: `{v}`." for k, v in estado["execucoes"].items()]
    ls += ["", "<details><summary>Fontes e hashes consumidos</summary>", ""]
    ls += tabela(["Arquivo", "SHA256"], [[f"`{p}`", f"`{s}`"] for p, s in sorted(estado["fontes"].items())])
    ls += ["", "</details>", ""]
    return "\n".join(ls) + "\n"


def publicar(estado):
    estado["fontes"] = dict(FONTES)
    payload = base64.b64encode(zlib.compress(json.dumps(estado, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8"), 9)).decode("ascii")
    texto = relatorio(estado) + "\n" + MARCADOR + payload + " -->\n"
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = MD.with_suffix(".md.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f0:
        f0.write(texto)
        f0.flush()
        os.fsync(f0.fileno())
    os.replace(tmp, MD)
    return texto


def cache():
    if not MD.exists():
        return None
    texto = MD.read_text(encoding="utf-8")
    exigir(MARCADOR in texto, "Relatorio existente sem cache reconhecido; nao sobrescrever")
    payload = texto.split(MARCADOR, 1)[1].split(" -->", 1)[0]
    obj = json.loads(zlib.decompress(base64.b64decode(payload)).decode("utf-8"))
    exigir(obj["codigo_sha256"] == sha(Path(__file__)), "Codigo mudou; cache anterior preservado")
    exigir(obj["lock_sha256"] == LOCK_SHA, "Lock mudou; cache anterior preservado")
    for p, s in obj["fontes"].items():
        exigir(sha(RAIZ / p) == s, "Fonte do cache mudou: " + p)
    FONTES.update(obj["fontes"])
    return obj


def autoteste():
    casos = [({"a": [0, 1, 2, 3], "b": [4], "c": [5, 6, 7]}, ["a", "b", "c"], ["c", "a", "b"]),
             ({"a": [0, 2, 4], "b": [1, 3], "c": [5]}, ["a", "b", "c"], ["b", "c", "a"])]
    for exp, base, nova in casos:
        ranks = {u: sorted(ks) for u, ks in exp.items()}
        gt = sorted(k for ks in exp.values() for k in ks)
        d = decompor(base, nova, ranks, {u: len(ks) for u, ks in exp.items()}, len(gt))
        seq = lambda ordem: [k for u in ordem for k in exp[u]]
        esperado = e.o.kendall_tau(seq(nova), gt)-e.o.kendall_tau(seq(base), gt)
        exigir(abs(d["delta"]-esperado) < 1e-12, "Autoteste: atribuicao incorreta")
        exigir(decompor(base, base, ranks, {u: len(ks) for u, ks in exp.items()}, len(gt))["delta"] == 0,
               "Autoteste: identidade incorreta")
        exigir(abs(d["delta"]-d["favoravel"]+d["adverso"]) < 1e-12, "Autoteste: sinais incorretos")
    print("Autoteste: 2 casos, com atomos grandes e referencia intercalada; identidades conferidas.")


def main():
    global LOCK_SHA, PROTEGIDOS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoteste", action="store_true")
    parser.add_argument("--conferir", action="store_true")
    parser.add_argument("--recalcular", action="store_true",
                        help="Refaz somente o relatorio desta analise, ignorando seu cache embutido")
    args = parser.parse_args()
    if args.autoteste:
        autoteste()
        return
    LOCK_SHA, PROTEGIDOS = ler_lock()
    if LOCK.exists():
        fonte(LOCK)
    # Os veiculos sao metadados dos caches, evitando inclusive ler splits em data/.
    runs, escolha = execucoes()
    # Veiculos fixos do protocolo solicitado; IDs, particoes e contagens sao
    # conferidos contra cada shard e os caches dos tres experimentos.
    ufs = {"validacao": ["official_diary_rn"],
           "teste": ["official_diary_ce", "official_diary_ma", "official_diary_rj"]}
    for p in {Path(__file__), Path(lm.__file__), *b.DEP_PATHS}:
        fonte(p)
    exigir(not (args.conferir and args.recalcular), "Escolha conferir OU recalcular")
    antigo = None if args.recalcular else cache()
    if args.conferir:
        exigir(antigo is not None and all(len(antigo["dados"].get(co, [])) == ESPERADO[co] for co in COORTES),
               "Cache completo ausente")
        # Ancora e revalidada mesmo no modo conferir, sem abrir outros conjuntos.
        a = ancora(runs, ufs)
        exigir(a == antigo["ancora"], "Ancora mudou")
        anterior = MD.read_text(encoding="utf-8")
        novo = relatorio(antigo)
        exigir(anterior.split(MARCADOR, 1)[0].rstrip() == novo.rstrip(), "Texto divergiu do cache")
        print("Conferencia: fontes, ancora, decomposicoes em cache e relatorio reproduzidos; nenhuma escrita.")
        return
    a = ancora(runs, ufs)
    estado = antigo or {"codigo_sha256": sha(Path(__file__)), "lock_sha256": LOCK_SHA,
                       "execucoes": {k: rel(v) for k, v in runs.items()}, "escolha": escolha,
                       "ancora": a, "dados": {co: [] for co in COORTES}, "fontes": {}}
    inicio = time.monotonic()
    for co in COORTES:
        rows = estado["dados"][co]
        prontos = {r["page_id"] for r in rows}
        ids = []
        for obj, p in paginas(co, ufs):
            exigir(ler_lock()[0] == LOCK_SHA, "Lock cego mudou durante a execucao")
            pid = p["page_id"]
            ids.append(pid)
            if pid in prontos:
                continue
            rows.append(analisar(co, obj, p, runs, escolha))
            prontos.add(pid)
            publicar(estado)
            print(f"{co}: {len(rows)}/{ESPERADO[co]}; {time.monotonic()-inicio:.1f}s", flush=True)
        exigir(len(ids) == len(set(ids)) == len(rows) == ESPERADO[co] and set(ids) == prontos,
               "Conjunto incompleto/duplicado: " + co)
        # Mantem a ordem do shard tambem quando a execucao foi retomada.
        ordem = {pid: i for i, pid in enumerate(ids)}
        rows.sort(key=lambda r: ordem[r["page_id"]])
    for p, s in FONTES.items():
        exigir(sha(RAIZ / p) == s, "Fonte mudou ao concluir: " + p)
    exigir(ler_lock()[0] == LOCK_SHA, "Lock cego mudou ao concluir")
    publicar(estado)
    print(f"Concluido: {sum(len(rs) for rs in estado['dados'].values())} paginas; {rel(MD)}", flush=True)


if __name__ == "__main__":
    main()
