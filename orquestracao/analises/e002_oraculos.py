"""Mede os oraculos E002 sem treinar modelos nem alterar fontes congeladas.

Usa linhas e atomos ls3, candidatos/categorias do corretor e a regua oficial
importada. Confere a ancora antes de produzir resultados. Os quatro conjuntos
sao conservados como na bancada original (inclusive sobreposicoes silver).
Cada pagina e cada passo residual sao persistidos atomicamente no cache local.
Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e002_oraculos.py
  [--max-minutos 30] [--autoteste] [--somente-ancora]
Nao usa GPU, rede, DataLoader, multiprocessing, PDFs ou dados do parceiro.
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
import collections
import hashlib
import itertools
import json
import math
import re
import statistics
import time
from contextlib import contextmanager
from functools import lru_cache

from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import ordem_lm_arestas as lm
import numpy as np
from scipy.optimize import linear_sum_assignment

if "torch" in sys.modules:
    sys.modules["torch"].set_num_threads(4)

OUT = RAIZ / "resultados/e002_oraculos"
LOCK = RAIZ / "experimentos/TESTE_CEGO.lock"
COORTES = ("golden_v4", "validacao_silver", "golden_v3_novo", "teste_silver")
DESENV = COORTES[:2]
KS = (12, 24, 32)
DECODERS = ("guloso", "matching", "maxregret")
METRICAS = ("tau", "quebras", "quebras_mil", "fid12", "sucessor_linhas")
PRAZO = None
PROTEGIDOS = set()
ASSINATURA_LOCK = None


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def gravar(path, obj):
    path = path.resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora de E002")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def ler_lock():
    if not LOCK.exists():
        return None, set()
    raw = LOCK.read_text(encoding="utf-8")
    # Aceita JSON/JSONL ou lista textual de IDs; desconhecido implica parada.
    ids = set(re.findall(r'[^\s"<>\[\]{},]+/[^"\r\n<>]*?\.pdf#p\d+', raw))
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = None
    def visitar(x):
        if isinstance(x, str) and ("#p" in x or x.lower().endswith(".pdf")):
            ids.add(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                if "#p" in k or k.lower().endswith(".pdf"):
                    ids.add(k)
                visitar(v)
        elif isinstance(x, list):
            for v in x:
                visitar(v)
    visitar(obj)
    exigir(ids, "TESTE_CEGO.lock existe mas seu formato nao foi reconhecido; abortando")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest(), ids


def permitido(pid):
    pdf = pid.rsplit("#p", 1)[0]
    exigir(not any(pid == x or pdf == x or pdf.endswith("/"+x) for x in PROTEGIDOS),
           "Pagina/PDF protegido pelo teste cego; nenhum calculo permitido")


def linhas_seguras(path):
    with path.open(encoding="utf-8") as f:
        for raw in f:
            if not raw.strip():
                continue
            # Verifica somente o ID antes de desserializar palavras/unidades.
            m = re.search(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")', raw)
            exigir(m is not None, "Registro sem page_id: "+str(path))
            permitido(json.loads(m.group(1)))
            yield json.loads(raw)


def vigiar():
    if PRAZO is not None and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; repetir o comando retoma o cache")
    assinatura, _ = ler_lock()
    exigir(assinatura == ASSINATURA_LOCK, "O lock cego mudou; reinicie para revalidar fontes")
    mem = b.memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 700, "RAM insuficiente; cache preservado")


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Lock de arquivo do SO: libera automaticamente inclusive apos queda.
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


def paginas(co):
    if co in c.HUMANAS:
        for obj in linhas_seguras(b.UNIDADES / "bancadas" / (co+".jsonl")):
            exigir(obj["particao"] == co, "Particao humana mudou")
            yield obj, obj["representacoes"]["linhas"]
        return
    part = "validacao" if co == "validacao_silver" else "teste"
    splits = b.ler(RAIZ / "data/processed/splits.json")
    for uf in splits[part]:
        pp = b.UNIDADES / "linhas" / (uf+".jsonl")
        wp = pp.with_name(uf+".palavras.jsonl")
        for p, obj in itertools.zip_longest(linhas_seguras(pp), linhas_seguras(wp)):
            exigir(p and obj and p["page_id"] == obj["page_id"], "Shards divergentes")
            exigir(p["uf"] == uf and p["particao"] == part, "Split silver mudou")
            exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
                   obj["gt_w"] == list(range(len(obj["palavras"]))), "Referencia silver mudou")
            yield {**obj, "uf": uf}, p


def ancora():
    rows = []
    for obj, p in paginas("golden_v4"):
        ordem, _ = b.prever(c.automatico(p), obj["palavras"], "regra_colunas")
        med, _, _, _ = c.medir(obj, p, ordem)
        rows.append({"page_id": p["page_id"], **{k: med[k] for k in ("tau", "quebras")}})
    out = {k: statistics.mean(r[k] for r in rows) for k in ("tau", "quebras")}
    exigir(len(rows) == 44 and abs(out["tau"]-.985948) <= .00000051 and
           abs(out["quebras"]-6.045455) <= .00000051,
           "PARE: ancora obrigatoria nao reproduzida: "+str(out))
    print("Âncora reproduzida: "+str(out), flush=True)
    return {"n": len(rows), **out}


def fontes():
    paths = set(b.DEP_PATHS) | {Path(__file__), Path(c.__file__), Path(lm.__file__),
             RAIZ / "data/processed/splits.json", b.JSON}
    for co in c.HUMANAS:
        paths.add(b.UNIDADES / "bancadas" / (co+".jsonl"))
    splits = b.ler(RAIZ / "data/processed/splits.json")
    for part in ("validacao", "teste"):
        for uf in splits[part]:
            paths.update(b.UNIDADES / "linhas" / (uf+s) for s in (".jsonl", ".palavras.jsonl"))
    for co in COORTES:
        for metodo in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
            path = b.OUT / "pred" / f"{metodo}__linhas__{co}.jsonl"
            if path.exists():
                paths.add(path)
    return {p.relative_to(RAIZ).as_posix(): c.sha(p) for p in sorted(paths)}


def carregar_salvos():
    dados = b.ler(b.JSON)["resultados"]
    preds, medidas = {}, {}
    for co in COORTES:
        preds[co], medidas[co] = {}, {}
        for metodo in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
            path = b.OUT / "pred" / f"{metodo}__linhas__{co}.jsonl"
            if path.exists():
                rows = list(linhas_seguras(path))
                preds[co][metodo] = {r["page_id"]: r["ordem"] for r in rows}
                exigir(len(rows) == len(preds[co][metodo]), "Predicoes duplicadas")
            chave = f"{metodo}__linhas__{co}"
            medidas[co][metodo] = {r["page_id"]: r["metricas"] for r in dados.get(chave, {}).get("paginas", [])}
    return preds, medidas


def candidatos(ctx):
    """Top-K explicito: propostas existentes, depois distancia euclidiana.

    nivel do corretor NAO e K. Preserva propostas de nivel 3 (regra primeiro),
    completa pelo pool de nivel 32 por distancia; empates pela entrada fixa.
    K conta destinos reais; FIM privado adicional nao consome uma vaga.
    """
    ranks = {u: i for i, u in enumerate(ctx["entrada"])}
    out = {k: {} for k in KS}
    for u in ctx["entrada"]:
        a = ctx["mapa"][u]
        dist = lambda v: (math.hypot(c.cx(ctx["mapa"][v])-c.cx(a),
                                    c.cy(ctx["mapa"][v])-c.cy(a)), ranks[v])
        prioritarios = [v for v in c.candidatos(ctx, u, 3) if v is not None]
        prioritarios.sort(key=lambda v: (v != ctx["regra"][u], *dist(v)))
        pool = [v for v in c.candidatos(ctx, u, max(KS)) if v is not None and v not in prioritarios]
        pool.sort(key=dist)
        lista = prioritarios + pool
        exigir(len(lista) >= min(max(KS), len(ctx["ordem"])-1), "Pool insuficiente")
        for k in KS:
            out[k][u] = lista[:k]+[None]
    return out


def costurar(regra, saida):
    entrada = {z: a for a, z in saida.items() if z is not None}
    exigir(len(entrada) == sum(z is not None for z in saida.values()), "Grau de entrada > 1")
    rank = {u: i for i, u in enumerate(regra)}
    seq = []
    for u in sorted((u for u in regra if u not in entrada), key=rank.__getitem__):
        while u is not None:
            exigir(u not in seq, "Ciclo no path cover")
            seq.append(u)
            u = saida.get(u)
    exigir(len(seq) == len(regra) and set(seq) == set(regra), "Cobertura incompleta")
    return seq


def guloso(regra, scores):
    rank = {u: i for i, u in enumerate(regra)}
    saida, entrada = {}, set()
    pai = {u: u for u in regra}
    def raiz(u):
        while pai[u] != u:
            pai[u] = pai[pai[u]]
            u = pai[u]
        return u
    edges = [(s, u, v) for u, vs in scores.items() for v, s in vs.items()]
    edges.sort(key=lambda x: (-x[0], rank[x[1]], rank.get(x[2], len(rank))))
    for _, u, v in edges:
        if u in saida or (v is not None and (v in entrada or raiz(u) == raiz(v))):
            continue
        saida[u] = v
        if v is not None:
            entrada.add(v)
            pai[raiz(u)] = raiz(v)
    return costurar(regra, saida)


def matching(regra, scores):
    n = len(regra)
    rank = {u: i for i, u in enumerate(regra)}
    # Colunas FIM privadas permitem path cover com qualquer numero de caminhos.
    matriz = np.full((n, 2*n), 1e6)
    for u, vs in scores.items():
        i = rank[u]
        for v, score in vs.items():
            matriz[i, n+i if v is None else rank[v]] = -score
    ri, ci = linear_sum_assignment(matriz)
    exigir(all(matriz[i, j] < 1e6 for i, j in zip(ri, ci)), "Matching usou aresta proibida")
    saida = {regra[i]: regra[j] if j < n else None for i, j in zip(ri, ci)}
    # Remove a aresta de menor escore de cada ciclo; empate pelo posto da regra.
    vistos = set()
    for inicio in regra:
        caminho, local, u = [], {}, inicio
        while u is not None and u not in vistos and u not in local:
            local[u] = len(caminho)
            caminho.append(u)
            u = saida[u]
        if u in local:
            ciclo = caminho[local[u]:]
            corte = min(ciclo, key=lambda a: (scores[a][saida[a]], -rank[a]))
            saida[corte] = None
        vistos.update(caminho)
    return costurar(regra, saida)


def escores_ouro(ctx, cand, q):
    # Inclui fronteiras dentro de uma linha humana dividida em varias unidades.
    prox = dict(zip(q["gt_w"], q["gt_w"][1:]))
    return {u: {v: (int(ctx["exp"][u][-1] == q["gt_w"][-1]) if ctx["exp"][u] else 0) if v is None else
                int(bool(ctx["exp"][u]) and bool(ctx["exp"][v]) and
                    prox.get(ctx["exp"][u][-1]) == ctx["exp"][v][0])
                for v in vs} for u, vs in cand.items()}


def auditoria_candidatos(trs, cand):
    resumo = {t: dict(ouro=0, erros_regra=0, elegiveis=0, presentes=0,
                     erros_elegiveis=0, erros_presentes=0, internos=0, inalcancaveis=0)
              for t in c.TIPOS}
    ausentes = []
    for tr in trs:
        s = resumo[tr["tipo"]]
        s["ouro"] += 1
        s["erros_regra"] += int(not tr["acerto"])
        s["internos"] += int(tr["interno"])
        s["inalcancaveis"] += int(not tr["alcancavel"])
        if not tr["interno"] and tr["alcancavel"]:
            presente = tr["z"] in cand[tr["a"]]
            s["elegiveis"] += 1
            s["presentes"] += int(presente)
            s["erros_elegiveis"] += int(not tr["acerto"])
            s["erros_presentes"] += int(not tr["acerto"] and presente)
            if not presente:
                ausentes.append(tr)
    return {"classes": resumo, "ausentes": ausentes}


def titulos(ctx):
    """Proxy automatica de titulo: linha curta predominantemente maiuscula."""
    ids = set(ctx["margem"]) | set(ctx["pontes"])
    for u in ctx["cs"]:
        letras = [ch for ch in u["text"] if ch.isalpha()]
        if c.tipo_unidade(u) == "texto" and len(u["ks"]) <= 16 and letras and sum(ch.isupper() for ch in letras)/len(letras) >= .7:
            ids.add(u["id"])
    return ids


def operacoes(ctx, ordem, cand):
    """Gera movimentos sem ouro. Destino e indice na lista apos retirar trecho."""
    n = len(ordem)
    especiais = titulos(ctx)
    for i in range(n-1):
        yield "vizinhas", i, 1, i+1
    for i in range(n):
        for tam in range(1, min(4, n-i)+1):
            bloco = ordem[i:i+tam]
            col = ctx["col"][bloco[0]]
            if any(c.tipo_unidade(ctx["mapa"][u]) != "texto" or u in ctx["pontes"] or
                   u in ctx["margem"] or ctx["col"][u] != col for u in bloco):
                continue
            for j in range(max(0, i-8), min(n-tam, i+8)+1):
                if j == i:
                    continue
                atravessadas = ordem[j:i] if j < i else ordem[i+tam:j+tam]
                if all(ctx["col"][u] == col and u not in ctx["pontes"] and
                       u not in ctx["margem"] and c.tipo_unidade(ctx["mapa"][u]) == "texto"
                       for u in atravessadas):
                    yield "bloco_coluna", i, tam, j
        if ordem[i] in especiais and c.tipo_unidade(ctx["mapa"][ordem[i]]) == "texto":
            resto = ordem[:i]+ordem[i+1:]
            alvos = set(cand[ordem[i]]) - {None}
            # Ponto antes/depois dos candidatos, mais inicio/fim da pagina.
            js = {0, n-1}
            for pos, u in enumerate(resto):
                if u in alvos:
                    js.update((pos, pos+1))
            for j in sorted(js):
                if j != i:
                    yield "reinsercao", i, 1, j


def mover(ordem, i, tam, j):
    trecho = ordem[i:i+tam]
    resto = ordem[:i]+ordem[i+tam:]
    return resto[:j]+trecho+resto[j:]


def residual(ctx, q, cand, path, fingerprint):
    """Descida estrita de quebras; custo de bordas vem de eventos() oficial.

    As expansoes internas sao fixas. Resume bordas comparaveis e conserva
    palavras livres; o custo de cada nova borda e medido pela funcao importada.
    Reconfere a sequencia completa pela mesma funcao apos cada movimento.
    """
    gt, gset = q["gt_w"], set(q["gt_w"])
    dados = {}
    for u, ks in ctx["exp"].items():
        inds = [i for i, k in enumerate(ks) if k in gset]
        dados[u] = (ks[inds[0]], ks[inds[-1]], inds[0] > 0, inds[-1] < len(ks)-1) if inds else None
    livre = next((k for ks in ctx["exp"].values() for k in ks if k not in gset), None)
    @lru_cache(maxsize=None)
    def borda(a, z, livre_entre):
        seq = [dados[a][1]] + ([livre] if livre_entre else []) + [dados[z][0]]
        return len(e.eventos(seq, gt))
    def bordas(seq):
        anterior, livres = None, False
        for u in seq:
            d = dados[u]
            if d is None:
                livres = livres or bool(ctx["exp"][u])
                continue
            if anterior is not None:
                yield anterior, u, livres or dados[anterior][3] or d[2]
            anterior, livres = u, False
    def custo_local(seq):
        return sum(borda(*edge) for edge in bordas(seq))
    ordem, historico = list(ctx["ordem"]), []
    if path.exists():
        salvo = b.ler(path)
        if salvo["fingerprint"] == fingerprint:
            ordem, historico = salvo["ordem"], salvo["operacoes"]
            if salvo["concluido"]:
                return ordem, historico
    while True:
        vigiar()
        # Bordas externas: basta uma unidade comparavel a cada lado.
        custo = custo_local(ordem)
        melhor, melhor_delta = None, 0
        for idx, (tipo, i, tam, j) in enumerate(operacoes(ctx, ordem, cand)):
            if idx % 2000 == 0:
                vigiar()
            lo, hi = min(i, j), max(i+tam, j+tam)
            left, right = lo-1, hi
            while left >= 0 and dados[ordem[left]] is None:
                left -= 1
            while right < len(ordem) and dados[ordem[right]] is None:
                right += 1
            lo2, hi2 = max(0, left), min(len(ordem), right+1)
            antes = ordem[lo2:hi2]
            depois = mover(antes, i-lo2, tam, j-lo2)
            delta = custo_local(depois)-custo_local(antes)
            if delta < melhor_delta:
                melhor_delta, melhor = delta, (tipo, i, tam, j)
        if melhor is None:
            gravar(path, {"fingerprint": fingerprint, "ordem": ordem, "operacoes": historico, "concluido": True})
            return ordem, historico
        tipo, i, tam, j = melhor
        nova = mover(ordem, i, tam, j)
        seq = lambda order: [k for u in order for k in ctx["exp"][u]]
        delta_oficial = len(e.eventos(seq(nova), gt))-len(e.eventos(seq(ordem), gt))
        exigir(delta_oficial == melhor_delta and custo_local(nova)-custo == delta_oficial,
               "Custo local divergiu da regua oficial")
        historico.append({"tipo": tipo, "origem": i, "tamanho": tam, "destino": j,
                          "unidades": ordem[i:i+tam], "delta_quebras": delta_oficial})
        ordem = nova
        gravar(path, {"fingerprint": fingerprint, "ordem": ordem, "operacoes": historico, "concluido": False})


def avaliar_ordem(obj, p, ctx, ordem, trs, q):
    med, seq, _, _ = c.medir(obj, p, ordem)
    exigir(sorted(seq) == list(range(len(obj["palavras"]))), "Cobertura de palavras diferente de 100%")
    ranks = {k: i for i, k in enumerate(seq)}
    intactas = {L["id"]: all(ranks[z] == ranks[a]+1 for a, z in zip(L["ks"], L["ks"][1:])) for L in q["gold_lines"]}
    cont = {t: dict(ouro=0, certos=0, reparos=0, regressoes=0, quebras=0) for t in c.TIPOS}
    for tr in trs:
        hit = intactas[tr["linha_a"]] and intactas[tr["linha_z"]] and ranks[tr["palavra_z"]] == ranks[tr["palavra_a"]]+1
        s = cont[tr["tipo"]]
        s["ouro"] += 1
        s["certos"] += int(hit)
        s["reparos"] += int(hit and not tr["acerto"])
        s["regressoes"] += int(tr["acerto"] and not hit)
    if trs:
        exigir(abs(sum(x["certos"] for x in cont.values())/len(trs)-med["sucessor_linhas"]) < 1e-12,
               "Diagnostico diverge do sucessor oficial")
    dono = {k: u for u, ks in ctx["exp"].items() for k in ks}
    for ev in e.eventos(seq, q["gt_w"]):
        cont[c.categoria(ctx, dono[ev["a"]], dono.get(ev["esperado"]))]["quebras"] += 1
    exigir(sum(x["quebras"] for x in cont.values()) == med["quebras"], "Classes nao particionam quebras")
    return {"metricas": med, "classes": cont, "cobertura_palavras": 1.,
            "palavras": len(seq), "ordem": ordem}


def processar(co, obj, p, cache, fingerprint, preds, antigas):
    inicio = time.perf_counter()
    ctx = c.contexto(p, obj["palavras"])
    _, _, trs, _ = c.preparar_avaliacao(obj, p, ctx)
    q = b.referencia(obj, p)
    cand = candidatos(ctx)
    medidas_seq = {}
    def medir(nome, ordem):
        chave = tuple(ordem)
        if chave not in medidas_seq:
            medidas_seq[chave] = avaliar_ordem(obj, p, ctx, ordem, trs, q)
        rows[nome] = medidas_seq[chave]
        antigo = antigas.get(nome, {}).get(p["page_id"])
        if antigo:
            for k in METRICAS:
                a, z = antigo[k], rows[nome]["metricas"][k]
                exigir(a is None and z is None or a is not None and z is not None and abs(a-z) < 1e-12,
                       f"Metrica salva divergiu: {co}/{nome}/{k}")
    rows = {}
    medir("regra_colunas", ctx["ordem"])
    for metodo in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
        ordem = preds.get(metodo, {}).get(p["page_id"])
        if ordem is not None:
            if metodo == "regra_colunas":
                exigir(ordem == ctx["ordem"], "Regra salva divergiu da ancora")
            else:
                medir(metodo, ordem)
    if len(p["bounding_boxes"]) > 67:
        medir("hibrido67", ctx["ordem"])
    elif "layoutreader_pronto" in rows:
        medir("hibrido67", rows["layoutreader_pronto"]["ordem"])
    recall = {}
    for k in KS:
        recall[str(k)] = auditoria_candidatos(trs, cand[k])
        scores = escores_ouro(ctx, cand[k], q)
        for dec, fn in (("guloso", guloso), ("matching", matching), ("maxregret", lm.max_regret)):
            vigiar()
            ordem = fn(ctx["ordem"], scores)
            medir(f"oraculo_decodificador_{dec}_K{k}", ordem)
    ordem, oper = residual(ctx, q, cand[max(KS)], cache.with_name(cache.stem+"_residual.json"), fingerprint)
    medir("oraculo_residual", ordem)
    metodos_rota = ("regra_colunas", "layoutreader_pronto", "regra_reordena", "hibrido67")
    vitorias = None
    if all(m in rows for m in metodos_rota):
        minimo = min(rows[m]["metricas"]["quebras"] for m in metodos_rota)
        empatados = [m for m in metodos_rota if rows[m]["metricas"]["quebras"] == minimo]
        escolhido = min(empatados, key=lambda m: (-rows[m]["metricas"]["tau"], metodos_rota.index(m)))
        medir("oraculo_roteamento", rows[escolhido]["ordem"])
        vitorias = {"escolhido": escolhido, "minimo_quebras": empatados}
    return {"fingerprint": fingerprint, "page_id": p["page_id"], "uf": obj["uf"],
            "unidades": len(ctx["ordem"]), "resultados": rows, "candidatos": recall,
            "operacoes": oper, "roteamento": vitorias, "segundos": time.perf_counter()-inicio}


def media(vals):
    vals = [v for v in vals if v is not None]
    return statistics.mean(vals) if vals else None


def resumir(rows):
    resumo = {}
    W = b.PESOS_CLUSTER(rows)
    nomes = sorted(set().union(*(r["resultados"] for r in rows)))
    for nome in nomes:
        inds = [i for i, r in enumerate(rows) if nome in r["resultados"]]
        rs = [rows[i] for i in inds]
        grupo = {"n": len(rs), "completo": len(rs) == len(rows), "metricas": {}, "delta": {},
                 "classes": {}, "cobertura_palavras": min(r["resultados"][nome]["cobertura_palavras"] for r in rs)}
        for k in METRICAS:
            v = [r["resultados"][nome]["metricas"][k] for r in rs]
            base = [r["resultados"]["regra_colunas"]["metricas"][k] for r in rs]
            ds = [None if a is None or z is None else a-z for a, z in zip(v, base)]
            por_uf = {uf: media([d for r, d in zip(rs, ds) if r["uf"] == uf]) for uf in sorted({r["uf"] for r in rs})}
            grupo["metricas"][k] = e.media_ic(v, W[:, inds])
            validos = [d for d in por_uf.values() if d is not None]
            sinal = -1 if k in ("quebras", "quebras_mil") else 1
            grupo["delta"][k] = {**e.media_ic(ds, W[:, inds]), "wilcoxon_veiculo": e.pratt(validos),
                "por_veiculo": por_uf, "melhor": sum(d is not None and sinal*d > 1e-12 for d in ds),
                "igual": sum(d is not None and abs(d) <= 1e-12 for d in ds),
                "pior": sum(d is not None and sinal*d < -1e-12 for d in ds)}
        for tipo in c.TIPOS:
            cont = collections.Counter()
            for r in rs:
                cont.update(r["resultados"][nome]["classes"][tipo])
            ds = [r["resultados"][nome]["classes"][tipo]["quebras"]-
                  r["resultados"]["regra_colunas"]["classes"][tipo]["quebras"] for r in rs]
            por_uf = [media([d for r, d in zip(rs, ds) if r["uf"] == uf]) for uf in sorted({r["uf"] for r in rs})]
            grupo["classes"][tipo] = {**cont, "quebras_por_pagina": cont["quebras"]/len(rs),
                    "delta_quebras": e.media_ic(ds, W[:, inds]), "wilcoxon_veiculo": e.pratt(por_uf)}
        resumo[nome] = grupo
    return resumo


def f(v, n=3):
    return "indisponível" if v is None else f"{v:.{n}f}".replace(".", ",")


def ic(v, n=3):
    return f"{f(v['media'], n)} [{f(v['ic'][0], n)}; {f(v['ic'][1], n)}]"


def selecionar(resumos):
    nomes = [f"oraculo_decodificador_{d}_K{k}" for k in KS for d in DECODERS]
    # Duas bancadas de desenvolvimento com peso igual, como no LM anterior.
    def criterio(m):
        return (media([resumos[co][m]["metricas"]["quebras"]["media"] for co in DESENV]),
                -media([resumos[co][m]["metricas"]["tau"]["media"] for co in DESENV]), nomes.index(m))
    escolhido = min(nomes, key=criterio)
    base = media([resumos[co]["regra_colunas"]["metricas"]["quebras"]["media"] for co in DESENV])
    teto = criterio(escolhido)[0]
    reducao = 1-teto/base
    return {"metodo": escolhido, "regra": base, "teto": teto, "reducao": reducao,
            "decisao": "GO" if reducao >= .2 else "NO-GO", "agregacao": "peso igual por bancada v4/RN"}


def publicar(dados, an, manifesto, concluido):
    resumos = {co: resumir(rs) for co, rs in dados.items() if rs}
    completos = concluido and all(co in resumos for co in COORTES)
    escolha = selecionar(resumos) if completos else None
    topo = [f"1. Âncora golden_v4 reproduzida: τ {f(an['tau'], 6)}; {f(an['quebras'], 6)} quebras/página.",
            "2. "+("Execução completa das famílias candidatos, decodificação e residual nas quatro bancadas." if completos else "Execução parcial retomável; sem decisão go/no-go."),
            (f"3. Grafo: {escolha['decisao']}; {escolha['metodo']}, redução {f(100*escolha['reducao'], 2)}% no desenvolvimento v4 + RN." if escolha else "3. Grafo: decisão pendente da execução completa."),
            "4. Roteamento usa somente predições salvas; RN não possui os quatro métodos e fica indisponível.",
            "5. Todas as variantes medidas preservam 100% das palavras e as expansões internas congeladas.",
            "6. Oráculos usam referência; golden_v3_novo já foi consultado anteriormente; nenhum teste cego é avaliado."]
    ls = topo + ["", "# E002 — tetos das famílias de ordenação", "", "## Protocolo e limitações", "",
        "Relatório gerado integralmente pelo script. CPU, um processo, sem modelos novos; caches atômicos por página e passo residual. Fontes e hashes em `cache/manifesto.json`. Métricas completas, ordens, sucessores ausentes e operações ficam nos caches de página.", "",
        "A régua é `corretor_de_transicoes.medir`, que importa `bancada_ordenadores` e `erros_ponta_a_ponta`: τ de palavras, quebras, fidelidade integral de 12 e sucessor de linhas intactas. IDs embaralhados por `ordem_entrada` (random.Random entrada-page_id). A cobertura considera todas as palavras extraídas, inclusive fora da referência humana; não mede conteúdo inexistente na camada digital.", "",
        "Candidatos: `nivel` da função existente amplia listas e não limita o grau. Aqui preservam-se as propostas do nível 3 (regra primeiro), completadas com as propostas do nível 32 por distância euclidiana entre centros. Empates pela entrada embaralhada. K limita destinos reais; FIM privado é adicional. K=12/24/32 usam listas aninhadas, sem ouro. Recall é micro sobre fronteiras externas alcançáveis; internas e inalcançáveis são mostradas separadamente. Recall de erros usa somente sucessores perdidos pela regra.", "",
        "No mesmo grafo, escores são 1 para fronteiras de palavras-ouro realizáveis (inclusive uma linha humana dividida em unidades), 0 nas demais; FIM vale 1 apenas na última palavra-ouro. Guloso global prioriza escore; matching maximiza a soma com FIM privado e elimina a menor aresta dos ciclos; max-regret é importado de `ordem_lm_arestas`. Todos costuram pela PRIMEIRA unidade de cada caminho na regra. Escores binários geram empates; os tetos realizados são atingíveis por estes algoritmos, não provas de ótimo global.", "",
        "Residual: escolhe maior redução estrita de quebras entre trocas vizinhas, movimentos de 1–4 unidades de texto na mesma coluna (até 8 posições, sem atravessar margens/átomos/pontes) e reinserções de linhas de margem/título antes/depois dos candidatos K32 ou nas extremidades. Título é proxy automática: até 16 palavras e ≥70% das letras maiúsculas; inclui pontes. Desempate determinístico pela enumeração. Para quando nenhuma operação melhora quebras; não atravessa platôs e portanto é ótimo local. Custos de borda vêm de eventos() oficial, conferidos na sequência inteira a cada operação.", "",
        "Categorias importadas do corretor, inclusive tabela/imagem (classe adicional conservada). São proxies geométricas exclusivas, não causas humanas. As tabelas por classe decompõem quebras segundo a transição esperada; sucessores usam as caixas das linhas-ouro como no corretor. Não equivalem a executar um método só naquela classe. Avaliação de corpo: aqui apenas a decomposição automática em classes; não há uma segunda referência humana de corpo, e métricas globais incluem a página inteira.", "",
        "Ajuste/seleção somente golden_v4 + RN, com peso igual por bancada e desempate por τ; seleção congelada antes das bancadas externas. Golden_v3_novo é externo nesta execução, mas já foi consultado em rodadas anteriores. O teste silver CE/MA/RJ tem ruído do fluxo PDF e piso interno aos átomos. Mantêm-se as sobreposições históricas entre bancadas, que não são amostras independentes somáveis. IC95 percentil com 5.000 bootstraps por veículo e Wilcoxon bilateral Pratt sobre deltas médios por veículo, descritivos. RN tem um veículo: IC degenerado, teste não informativo.", "",
        "RN não tem LayoutReader/reordenação restrita salvos; não se executam modelos para preenchê-los. Híbrido 67 fica disponível só nas páginas RN densas que selecionam a regra; sua média parcial NÃO representa a bancada. Roteamento e suas métricas RN são nulos. Roteamento minimiza quebras por página, desempata por τ e ordem fixa dos métodos; informa todos os empates por quebras.", ""]
    if escolha:
        ls += [f"Critério do cartão: ≥20% de redução de quebras no desenvolvimento. Resultado: **{escolha['decisao']}**, regra {f(escolha['regra'])} → {f(escolha['teto'])} quebras/página na média de v4/RN. A escolha vale para as externas sem nova seleção.", ""]
    metricas = {}
    for co, resumo in resumos.items():
        rs = dados[co]
        ls += [f"## {co}", "", f"Páginas processadas: {len(rs)}; veículos: {len({r['uf'] for r in rs})}.", "",
               "| Método | n | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões | Cobertura |",
               "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        nomes = ["regra_colunas", "hibrido67", "layoutreader_pronto", "regra_reordena"] + [f"oraculo_decodificador_{d}_K{k}" for k in KS for d in DECODERS] + ["oraculo_residual", "oraculo_roteamento"]
        for nome in nomes:
            s = resumo.get(nome)
            if not s:
                ls.append(f"| {nome} | 0 | indisponível | — | — | — | — | — | — | — | — | — |")
                continue
            ms, ds = s["metricas"], s["delta"]["quebras"]
            rep = sum(v["reparos"] for v in s["classes"].values())
            reg = sum(v["regressoes"] for v in s["classes"].values())
            parcial = " (parcial)" if not s["completo"] else ""
            ls.append(f"| {nome}{parcial} | {s['n']} | {f(ms['tau']['media'], 6)} | {f(ms['quebras']['media'])} | {f(ms['quebras_mil']['media'])} | {f(ms['fid12']['media'], 6)} | {f(ms['sucessor_linhas']['media'], 6)} | {ic(ds)} | {f(ds['wilcoxon_veiculo']['p'], 6)} | {ds['melhor']}/{ds['igual']}/{ds['pior']} | {rep}/{reg} | {f(100*s['cobertura_palavras'], 0)}% |")
            if s["completo"]:
                metricas[f"{co}/{nome}"] = {"tau": ms["tau"]["media"], "quebras": ms["quebras"]["media"], "sucessor": ms["sucessor_linhas"]["media"]}
        if "oraculo_roteamento" not in resumo:
            metricas[f"{co}/oraculo_roteamento"] = {"tau": None, "quebras": None, "sucessor": None}
        if escolha:
            metricas[f"{co}/oraculo_decodificador_melhor_desenvolvimento"] = metricas[f"{co}/{escolha['metodo']}"]
        ls += ["", "### Recall de candidatos por classe", "",
               "Regra e híbrido 67 são referências na tabela acima; não geram candidatos. Recall não é uma métrica de ordem: a família (a) não recebe τ artificial no JSON.", "",
               "| K | Classe | Presentes/elegíveis | Recall | Erros presentes/elegíveis | Recall erros | Internos | Inalcançáveis |",
               "|---:|---|---:|---:|---:|---:|---:|---:|"]
        for k in KS:
            for tipo in c.TIPOS:
                s = collections.Counter()
                for r in rs:
                    s.update(r["candidatos"][str(k)]["classes"][tipo])
                ratio = lambda a, z: 100*a/z if z else None
                ls.append(f"| {k} | {c.ROTULOS[tipo]} | {s['presentes']}/{s['elegiveis']} | {f(ratio(s['presentes'], s['elegiveis']), 2)}% | {s['erros_presentes']}/{s['erros_elegiveis']} | {f(ratio(s['erros_presentes'], s['erros_elegiveis']), 2)}% | {s['internos']} | {s['inalcancaveis']} |")
        ls += ["", "### Decomposição por classe de erro da regra", "",
               "| Método | Classe | Quebras/pág | Δ quebras [IC95 veículo] | p veículo | Sucessores certos/ouro | Reparos/regressões |",
               "|---|---|---:|---:|---:|---:|---:|"]
        for nome in nomes:
            s = resumo.get(nome)
            if not s:
                ls.append(f"| {nome} | indisponível | — | — | — | — | — |")
                continue
            for tipo, z in s["classes"].items():
                ls.append(f"| {nome}{' (parcial)' if not s['completo'] else ''} | {c.ROTULOS[tipo]} | {f(z['quebras_por_pagina'])} | {ic(z['delta_quebras'])} | {f(z['wilcoxon_veiculo']['p'], 6)} | {z['certos']}/{z['ouro']} | {z['reparos']}/{z['regressoes']} |")
        ops = collections.Counter(o["tipo"] for r in rs for o in r["operacoes"])
        ls += ["", f"Operações residuais: {sum(ops.values())}; por tipo: {dict(ops)}. Páginas com operações: {sum(bool(r['operacoes']) for r in rs)}. Sequência de cada operação salva no cache.", ""]
        if all(r["roteamento"] is not None for r in rs):
            unicas, escolhidos, minimos = collections.Counter(), collections.Counter(), collections.Counter()
            for r in rs:
                rota = r["roteamento"]
                escolhidos[rota["escolhido"]] += 1
                minimos.update(rota["minimo_quebras"])
                if len(rota["minimo_quebras"]) == 1:
                    unicas.update(rota["minimo_quebras"])
            ls += [f"Roteamento — vitórias exclusivas: {dict(unicas)}; presença no mínimo (inclui empates): {dict(minimos)}; escolhidos após desempate: {dict(escolhidos)}; páginas empatadas: {sum(len(r['roteamento']['minimo_quebras']) > 1 for r in rs)}.", ""]
        else:
            ls += ["Roteamento indisponível: faltam predições salvas dos quatro métodos; nenhuma média de subconjunto é declarada teto da bancada.", ""]
        ls += ["### Sucessores-ouro fora dos candidatos", "",
               "Lista integral, sem texto nem coordenadas humanas, identificada por página, linha, unidade e K:", ""]
        for k in KS:
            faltantes = [(r["page_id"], tr) for r in rs for tr in r["candidatos"][str(k)]["ausentes"]]
            ls.append(f"K={k}: {len(faltantes)} sucessores ausentes.")
            for pid, tr in faltantes:
                ls.append(f"- `{pid}`: `{tr['linha_a']}` → `{tr['linha_z']}`; `{tr['a']}` → `{tr['z']}`; {c.ROTULOS[tr['tipo']]}; erro da regra: {not tr['acerto']}.")
            ls.append("")
    gravar(OUT / "metricas.json", metricas)
    gravar(OUT / "cache/resumos.json", {"completo": completos, "selecao": escolha, "bancadas": resumos})
    gravar(OUT / "RELATORIO.md", "\n".join(ls)+"\n")


def autoteste():
    # Mesmo grafo nos tres decoders, ciclos de score zero e arestas perfeitas.
    ordem = ["c", "a", "b", "d"]
    scores = {u: {z: int((u, z) in (("a", "b"), ("b", "c"), ("c", "d"))) for z in ordem if z != u} for u in ordem}
    for u in ordem:
        scores[u][None] = int(u == "d")
    for fn in (guloso, matching, lm.max_regret):
        exigir(fn(ordem, scores) == ["a", "b", "c", "d"], "Decoder perdeu aresta-ouro")
        zero = {u: {z: 0 for z in vs} for u, vs in scores.items()}
        exigir(set(fn(ordem, zero)) == set(ordem), "Decoder perdeu cobertura com empates")
    exigir(mover(list("abcdef"), 1, 2, 3) == list("adebcf"), "Movimento a direita incorreto")
    exigir(mover(list("abcdef"), 3, 2, 1) == list("adebcf"), "Movimento a esquerda incorreto")
    print("Autoteste dos decodificadores e movimentos aprovado", flush=True)


def main():
    global PRAZO, PROTEGIDOS, ASSINATURA_LOCK
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-minutos", type=float, default=0)
    parser.add_argument("--autoteste", action="store_true")
    parser.add_argument("--somente-ancora", action="store_true")
    args = parser.parse_args()
    ASSINATURA_LOCK, PROTEGIDOS = ler_lock()
    if args.autoteste:
        autoteste()
    if args.max_minutos:
        PRAZO = time.monotonic()+60*args.max_minutos
    with trava():
        an = ancora()
        if args.somente_ancora:
            return
        manifesto = {"fontes": fontes(), "lock_cego_sha256": ASSINATURA_LOCK,
                     "K": KS, "decodificadores": DECODERS, "ancora": an,
                     "cpu": True, "processos": 1, "num_workers": 0, "threads": 4}
        assinatura = c.digest(manifesto)
        manifesto["assinatura"] = assinatura
        gravar(OUT / "cache/manifesto.json", manifesto)
        preds, antigas = carregar_salvos()
        dados = {co: [] for co in COORTES}
        try:
            for co in COORTES:
                for obj, p in paginas(co):
                    vigiar()
                    pid = p["page_id"]
                    fp = c.digest([assinatura, obj, p])
                    path = OUT / "cache" / assinatura / co / (hashlib.sha256(pid.encode("utf-8")).hexdigest()+".json")
                    row = b.ler(path) if path.exists() else None
                    if not row or row["fingerprint"] != fp:
                        row = processar(co, obj, p, path, fp, preds[co], antigas[co])
                        gravar(path, row)
                    dados[co].append(row)
                    print(f"{co}: {len(dados[co])} páginas; {pid}; {f(row['segundos'], 1)} s na primeira execução", flush=True)
                # Congela escolha antes de abrir as bancadas externas.
                if co == "validacao_silver":
                    escolha = selecionar({d: resumir(dados[d]) for d in DESENV})
                    gravar(OUT / "cache/selecao_desenvolvimento.json", {"assinatura": assinatura, **escolha})
                publicar(dados, an, manifesto, False)
        except (TimeoutError, KeyboardInterrupt):
            publicar(dados, an, manifesto, False)
            print("Execução parcial preservada; repita o mesmo comando", flush=True)
            return
        publicar(dados, an, manifesto, True)
        print("Concluído: resultados/e002_oraculos/RELATORIO.md e metricas.json", flush=True)


if __name__ == "__main__":
    main()
