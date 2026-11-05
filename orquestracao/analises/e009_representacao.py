"""Compara caixas automaticas de outubro e linhas/atomos, com palavras fixas.

Reusa P1 congelado (Heron + propor/regras + blocos v3) nas bancadas humanas
e reconstrui a mesma receita no silver com deteccoes existentes. Importa a
regua e os ordenadores, sem mudar parametros, referencias ou segmentacoes.
Orfas recebem linhas de fallback antes de ordenar: nenhum ganho pode vir de
apagar palavras. A cobertura anterior ao fallback tambem fica explicita.

Uso da raiz: venv/Scripts/python.exe -B
orquestracao/analises/e009_representacao.py [--somente-ancora] [--conferir]
CPU, um processo, quatro threads, sem detector, PDF, GPU ou rede. Toda escrita
fica em resultados/e009_representacao/. Caches atomicos por pagina/operacao
permitem retomar com o mesmo comando. O lacre e verificado antes de ler cada
registro; nao importa carregadores de corpus que possam abrir paginas cegas.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", HF_DEACTIVATE_ASYNC_LOAD="1",
                  TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="4",
                  MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4", PYTHONDONTWRITEBYTECODE="1")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import collections
import itertools
import json
import math
import re
import statistics
import time
import types
from contextlib import contextmanager
from datetime import datetime, timezone

from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e

OUT = RAIZ / "resultados/e009_representacao"
COORTES = b.BANCADAS
REPS = ("A", "B")
ORDENADORES = ("regra", "hibrido67")
METRICAS = (*b.METRICAS, "entre_unidades")
VERSAO = "e009-v1-palavras-fixas"
CEGAS = set()
LACRE = None
LR = None
INFO_LR = {}
DEPENDENCIAS = {}
PADRAO_PID = re.compile(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")')


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def ler(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def gravar(path, valor):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()), f"Escrita fora de E009: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(valor, str):
            f.write(valor)
        else:
            json.dump(valor, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def vigiar(pid=None):
    lock = RAIZ / "experimentos/TESTE_CEGO.lock"
    exigir((b.sha(lock) if lock.exists() else None) == LACRE, "O lacre mudou durante a execucao")
    exigir(pid not in CEGAS, f"Pagina cega bloqueada: {pid}")


def registros(path, permitidos=None):
    """Le so metadado page_id antes de desserializar qualquer pagina permitida."""
    with Path(path).open(encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            match = PADRAO_PID.search(linha)
            exigir(match is not None, f"Registro sem page_id: {path}")
            pid = json.loads(match[1])
            if pid in CEGAS or permitidos is not None and pid not in permitidos:
                continue
            vigiar(pid)
            obj = json.loads(linha)
            exigir(obj["page_id"] == pid, "Metadado de pagina inconsistente")
            yield obj


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


def paginas(coorte):
    if coorte != "teste_silver":
        for obj in registros(b.UNIDADES / "bancadas" / (coorte + ".jsonl")):
            exigir(obj["particao"] == coorte, "Bancada humana divergente")
            yield obj, obj["representacoes"]["linhas"]
    else:
        splits = ler(RAIZ / "data/processed/splits.json")
        for uf in splits["teste"]:
            base = b.UNIDADES / "linhas"
            pp = registros(base / (uf + ".jsonl"))
            ww = registros(base / (uf + ".palavras.jsonl"))
            for p, obj in itertools.zip_longest(pp, ww):
                exigir(p is not None and obj is not None and p["page_id"] == obj["page_id"],
                       "Shards silver divergentes")
                exigir(p["uf"] == uf and p["particao"] == "teste", "Split silver divergente")
                exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
                       obj["gt_w"] == list(range(len(obj["palavras"]))), "Silver nao e fluxo PDF")
                yield {**obj, "uf": uf, "particao": coorte}, p


# Embrulha a funcao da bancada; so muda o destino dos caches, nao a metrica.
MEDIR = types.FunctionType(b.metricas.__code__,
    {**b.metricas.__globals__, "OUT": OUT, "gravar": gravar},
    argdefs=b.metricas.__defaults__)
MEDIR.__kwdefaults__ = b.metricas.__kwdefaults__


def medir(obj, p, ordem):
    vigiar(p["page_id"])
    met = dict(MEDIR(obj, p, ordem))
    exp = b.expansoes(obj, p)
    seq = [k for uid in ordem for k in exp[uid]]
    exigir(sorted(seq) == list(range(len(obj["palavras"]))), "Cobertura final diferente de 100%")
    eventos = e.eventos(seq, obj["gt_w"])
    met["entre_unidades"] = met["quebras"] - met["piso_interno"]
    # Diagnostico das arestas; confere a soma com a metrica importada.
    dono = {k: uid for uid, ks in exp.items() for k in ks}
    internas = sum(dono[x["a"]] == dono[x["b"]] for x in eventos)
    exigir(internas == met["piso_interno"], "Decomposicao de quebras inconsistente")
    q = b.referencia(obj, p)
    rank = {k: i for i, k in enumerate(seq)}
    ls = {L["id"]: L["ks"] for L in q["gold_lines"]}
    intactas = {lid: all(rank[z] == rank[a] + 1 for a, z in zip(ks, ks[1:]))
                for lid, ks in ls.items()}
    hits = [intactas[a] and intactas[z] and rank[ls[z][0]] == rank[ls[a][-1]] + 1
            for a, z in zip(q["gt_l"], q["gt_l"][1:])]
    exigir(hits and abs(statistics.mean(hits) - met["sucessor_linhas"]) < 1e-12,
           "Diagnostico divergiu do sucessor de linhas oficial")
    exigir(all(met[k] is not None and math.isfinite(met[k]) for k in METRICAS),
           "Metrica ausente; nao imputar zero")
    return {"metricas": met, "ordem": ordem, "seq": seq,
            "sucessores_certinhos": [i for i, hit in enumerate(hits) if hit],
            "sucessores_elegiveis": len(hits)}


def ancora():
    rows = []
    for obj, p in paginas("golden_v4"):
        ordem, _ = b.prever(p, obj["palavras"], "regra_colunas")
        met = medir(obj, p, ordem)["metricas"]
        rows.append({"page_id": p["page_id"], "tau": met["tau"], "quebras": met["quebras"]})
    med = {k: statistics.mean(r[k] for r in rows) for k in ("tau", "quebras")}
    ok = len(rows) == 44 and abs(med["tau"] - .985948) < .0000005 and abs(med["quebras"] - 6.045455) < .0000005
    gravar(OUT / "ancora.json", {"aprovada": ok, "n": len(rows), **med, "paginas": rows})
    exigir(ok, f"PARAR: ancora obrigatoria nao reproduzida: {med}")
    print(f"Ancora aprovada: tau {med['tau']:.6f}; quebras {med['quebras']:.6f}", flush=True)
    return med


def cobertura(obj, unidades):
    """Conta IDs atribuidos; sobreposicao geometrica fica em campo separado."""
    c = collections.Counter(k for u in unidades for k in u["ks"])
    ouro = set(obj["gt_w"])
    disponiveis = set(range(len(obj["palavras"])))
    exigir(set(c) <= disponiveis, "ID de palavra fora da pagina")
    hits = collections.Counter()
    for k, w in enumerate(obj["palavras"]):
        centro = e.o.centro(w)
        hits[k] = sum(e.o.contem(u["bbox"], centro) for u in unidades)
    def contar(ids):
        n = len(ids)
        cobertas = sum(c[k] > 0 for k in ids)
        duplicadas = sum(c[k] > 1 for k in ids)
        orfas = n - cobertas
        return {"n": n, "cobertas": cobertas, "duplicadas": duplicadas, "orfas": orfas,
                "cobertas_pct": 100*cobertas/n, "duplicadas_pct": 100*duplicadas/n,
                "orfas_pct": 100*orfas/n,
                "geometricamente_multiplas": sum(hits[k] > 1 for k in ids)}
    return {"ouro": contar(ouro), "disponiveis": contar(disponiveis),
            "ids_orfaos": sorted(disponiveis - set(c)),
            "ids_duplicados": sorted(k for k, n in c.items() if n > 1)}


def completar(obj, p, itens):
    us = [{"id": f"a{i}", "bbox": list(u["bbox"]), "ks": list(u["ks"]),
           "tipo": u.get("tipo", "texto"),
           "text": " ".join(obj["palavras"][k][0] for k in u["ks"])} for i, u in enumerate(itens)]
    antes = cobertura(obj, us)
    exigir(not antes["ids_duplicados"], "Caixas atribuiram uma palavra a mais de uma unidade")
    for i, L in enumerate(e.o.linhas(obj["palavras"], antes["ids_orfaos"])):
        us.append({"id": f"livre{i}", "bbox": L["bbox"], "ks": L["ks"], "tipo": "livre",
                   "text": " ".join(obj["palavras"][k][0] for k in L["ks"])})
    novo = {k: p[k] for k in ("page_id", "uf", "dimensions")}
    novo["bounding_boxes"] = us
    b.auditar_unidades(novo, obj)
    return novo, {"antes_fallback": antes, "final": cobertura(obj, us),
                  "unidades_fallback": len(us) - len(itens)}


def carregar_historico():
    # Arquivo antigo tem apenas as duas bancadas humanas, verificadas pelos
    # page_id antes de desserializar o JSON agregado (nenhuma pagina cega).
    texto = e.JSON.read_text(encoding="utf-8")
    ids = {json.loads(m[1]) for m in PADRAO_PID.finditer(texto)}
    exigir(not ids & CEGAS, "Historico contem pagina cega")
    return json.loads(texto)


def auditar_fontes(hist):
    """Prova que os indices de palavra antigos ainda nomeiam as mesmas palavras."""
    hashes = {}
    fontes = {}
    un_manifesto = ler(b.UNIDADES / "manifesto.json")
    for co in COORTES[:2]:
        for obj, p in paginas(co):
            pid = p["page_id"]
            vigiar(pid)
            fonte = obj["origem_palavras"]
            path = (RAIZ / fonte).resolve()
            exigir(path.is_relative_to(RAIZ / "data/diamond") or
                   path.is_relative_to(RAIZ / "resultados/ordem_sem_bbox_cache/palavras"),
                   f"Origem de palavras fora das fontes autorizadas: {fonte}")
            exigir("labelstudio" not in fonte.lower(), "Fonte do parceiro bloqueada")
            exigir(fonte in hist["hashes"], "Origem ausente no historico de palavras")
            if fonte not in hashes:
                hashes[fonte] = b.sha(path)
                exigir(hashes[fonte] == hist["hashes"][fonte], "Palavras historicas mudaram: " + fonte)
                if path.suffix == ".jsonl":
                    exigir(un_manifesto["hashes"].get(fonte) == hashes[fonte], "Exportacao usa outra fonte Diamond")
                    fontes[fonte] = {r["page_id"]: r for r in registros(path)}
                else:
                    fontes[fonte] = ler(path)
            src = fontes[fonte][pid] if path.suffix == ".jsonl" else fontes[fonte]
            # O exportador conserva as dimensoes da tarefa v3 (uma casa),
            # enquanto o cache canonico guarda duas casas. Nao muda a pagina.
            exigir(src["page_id"] == pid and all(round(src["dimensions"][k], 1) ==
                   round(p["dimensions"][k], 1) for k in ("width", "height")),
                   "Origem de palavras trocou pagina: " + pid)
            exigir([w[:5] for w in src["palavras"]] == [w[:5] for w in obj["palavras"]],
                   "Indices de palavras nao correspondem ao historico")
    for nome in ("src/data/extrator.py", "src/data/regioes.py", "src/data/layout.py"):
        hashes[nome] = b.sha(RAIZ / nome)
        exigir(hashes[nome] == hist["hashes"][nome], "Receita automatica de outubro mudou: " + nome)
    # Reuso das predicoes B exige os mesmos shards e pesos da bancada antiga.
    texto = b.JSON.read_text(encoding="utf-8")
    exigir(not {json.loads(m[1]) for m in PADRAO_PID.finditer(texto)} & CEGAS,
           "Bancada antiga contem pagina cega")
    bancada = json.loads(texto)
    paths = [b.UNIDADES / "bancadas" / (co + ".jsonl") for co in COORTES[:2]]
    paths += [b.UNIDADES / "linhas" / (uf + suf)
              for uf in ler(RAIZ / "data/processed/splits.json")["teste"]
              for suf in (".jsonl", ".palavras.jsonl")]
    paths += [RAIZ / "models/terceiros/layoutreader" / n for n in ("model.safetensors", "config.json")]
    paths += [RAIZ / "orquestracao/analises/ordem_layoutreader.py", Path(b.__file__)]
    for path in paths:
        nome = b.rel(path)
        hashes[nome] = b.sha(path)
        exigir(bancada["fontes"].get(nome) == hashes[nome], "Cache LayoutReader de outra fonte: " + nome)
    return {"hashes_palavras_e_unidades_conferidos": hashes,
            "palavras_identicas_por_id": True, "receita_caixas_outubro_identica": True,
            "layoutreader_B_mesmos_shards_pesos_adaptador": True}


def fontes_layout(ids_por_uf):
    out = {}
    for uf, ids in ids_por_uf.items():
        path = RAIZ / "data/processed/layout" / (uf + ".jsonl")
        if not path.exists():
            continue
        for r in registros(path, ids):
            if r.get("revisao") == e.layout.REVISAO and "escala" in r and r.get("regioes") is not None:
                out[r["page_id"]] = r
    return out


def caixas_silver(obj, p, det):
    ws = [{"t": w[0], "x0": w[1], "top": w[2], "x1": w[3], "bottom": w[4], "s": i}
          for i, w in enumerate(obj["palavras"])]
    blocos = e.extrator.segmentar(ws, e.layout.tabelas(det["regioes"]))
    dono = {id(w): i for i, bloco in enumerate(blocos) for L in bloco["linhas"] for w in L["ws"]}
    palavras = [list(w[:5]) + [dono.get(id(sw), -1)] for w, sw in zip(obj["palavras"], ws)]
    bs = [{"id": f"v{i}", "bbox": [round(bl[k], 1) for k in ("x0", "top", "x1", "bottom")],
           **({"tipo": "tabela"} if bl.get("tabela") else {})} for i, bl in enumerate(blocos)]
    rs = e.o.propor(palavras, bs, det["regioes"], regras=True)
    ks, _, _ = e.o.donos(obj["palavras"], rs)
    itens = [{"id": r["id"], "bbox": r["bbox"], "ks": kws, "tipo": r["classe"]}
             for r, kws in zip(rs, ks)]
    return completar(obj, p, itens)


def preparar_A(obj, p, coorte, hist, det):
    if coorte != "teste_silver":
        r = hist[p["page_id"]]
        exigir(r["palavras"] == len(obj["palavras"]) and r["palavras_ouro"] == len(obj["gt_w"]),
               "Palavras historicas divergentes")
        itens = sorted((u for u in r["metodos"]["P1"]["items"] if u["tipo"] != "livre"),
                       key=lambda u: u["id"])
        return completar(obj, p, itens)
    return caixas_silver(obj, p, det[p["page_id"]])


def predicoes_B():
    out = {}
    for coorte in COORTES:
        path = b.OUT / "pred" / f"layoutreader_pronto__linhas__{coorte}.jsonl"
        if path.exists():
            for r in registros(path):
                out[(coorte, r["page_id"])] = r["ordem"]
    return out


def ordem_hibrida(obj, p, rep, coorte, regra, preds, conferir):
    global LR, INFO_LR
    if len(p["bounding_boxes"]) > 67:
        return regra, {"escolhido": "regra", "limiar": 67}
    if rep == "B" and (coorte, p["page_id"]) in preds:
        ordem = preds[(coorte, p["page_id"])]
        b.auditar_unidades(p, obj)
        exigir(set(ordem) == {u["id"] for u in p["bounding_boxes"]}, "Cache LayoutReader de outra representacao")
        return ordem, {"escolhido": "layoutreader_pronto", "origem": "cache outubro", "limiar": 67}
    auto = {k: p[k] for k in ("page_id", "dimensions", "bounding_boxes")}
    fp = b.digest([auto, DEPENDENCIAS, "LayoutReader CPU float32, limiar 67"])
    path = OUT / "cache/predicoes" / (fp + ".json")
    if path.exists():
        r = ler(path)
        exigir(r["fingerprint"] == fp, "Cache neural incompativel")
        return r["ordem"], r["diag"]
    exigir(not conferir, f"Cache neural ausente para --conferir: {p['page_id']}")
    if LR is None:
        print("Carregando LayoutReader pronto em CPU; detector nao sera carregado", flush=True)
        LR = b.carregar_layoutreader()
        INFO_LR = LR.info
        gravar(OUT / "cache/layoutreader.json", INFO_LR)
    ordem, diag = b.prever(auto, obj["palavras"], "layoutreader_pronto", LR)
    diag.update(escolhido="layoutreader_pronto", origem="CPU nesta execucao", limiar=67)
    gravar(path, {"fingerprint": fp, "page_id": p["page_id"], "ordem": ordem, "diag": diag})
    return ordem, diag


def historico_pagina(obj, p, row):
    """Reexecuta o diagnostico antigo e a definicao atual, sem somar bancadas."""
    q = b.referencia(obj, p)
    saida = {}
    for m in ("P1", "P1m", "P2"):
        velho = row["metodos"][m]
        seq = e.o.fluxo(velho["items"], obj["palavras"])
        exigir(seq == velho["seq"], "IDs de palavras/expansao do historico divergiram")
        dono = {k: i for i, item in enumerate(velho["items"]) for k in item["ks"]}
        evs = e.eventos(seq, q["gt_w"])
        piso_antigo = sum(dono[x["a"]] == dono[x["b"]] and not x["livre"] for x in evs)
        piso_atual = sum(len(e.eventos(e.o.fluxo([u], obj["palavras"]), q["gt_w"]))
                         for u in velho["items"])
        exigir(piso_antigo == velho["piso_interno"] and len(evs) == velho["quebras"],
               "Historico nao reproduzido")
        saida[m] = {"piso_antigo": piso_antigo, "piso_atual": piso_atual,
                    "quebras": len(evs)}
    return saida


def conferir_pagina(row, obj, p, coorte, hist, det, preds):
    """Audita mapas, ordens, sequencias e decomposicao com a regua importada."""
    a, cov_a = preparar_A(obj, p, coorte, hist, det)
    cov_b = cobertura(obj, p["bounding_boxes"])
    exigir(row["cobertura"]["A"] == cov_a and row["cobertura"]["B"]["final"] == cov_b,
           "Cobertura salva divergiu dos mapas")
    for rep, page in (("A", a), ("B", p)):
        exigir(row["unidades"][rep] == page["bounding_boxes"], "Unidades salvas divergentes")
        regra, _ = b.prever(page, obj["palavras"], "regra_colunas")
        exigir(row["resultados"][rep+"_regra"]["ordem"] == regra, "Regra salva divergente")
        ordem_h, _ = ordem_hibrida(obj, page, rep, coorte, regra, preds, True)
        exigir(row["resultados"][rep+"_hibrido67"]["ordem"] == ordem_h, "Hibrido salvo divergente")
        for ordenador in ORDENADORES:
            salvo = row["resultados"][rep+"_"+ordenador]
            novo = medir(obj, page, salvo["ordem"])
            exigir(all(salvo[k] == v for k, v in novo.items()), "Metrica/sequencia salva divergente")
    if coorte != "teste_silver":
        exigir(row["historico"] == historico_pagina(obj, p, hist[p["page_id"]]),
               "Reconstrucao historica divergente")


def processar(obj, p, coorte, hist, det, preds, conferir):
    pid = p["page_id"]
    vigiar(pid)
    hist_row = hist.get(pid) if coorte != "teste_silver" else None
    fp = b.digest([VERSAO, DEPENDENCIAS, obj, p,
                   hist_row if hist_row else det.get(pid), preds.get((coorte, pid))])
    path = OUT / "cache/paginas" / coorte / (e.ac.chave(pid) + ".json")
    if path.exists():
        row = ler(path)
        if row["fingerprint"] == fp and row.get("completa"):
            if conferir:
                conferir_pagina(row, obj, p, coorte, hist, det, preds)
            return row
    exigir(not conferir, f"Pagina sem cache valido: {pid}")
    a, cov_a = preparar_A(obj, p, coorte, hist, det)
    cov_b = cobertura(obj, p["bounding_boxes"])
    row = {"page_id": pid, "uf": p["uf"], "bancada": coorte, "fingerprint": fp,
           "palavras": len(obj["palavras"]), "palavras_ouro": len(obj["gt_w"]),
           "cobertura": {"A": cov_a, "B": {"antes_fallback": cov_b, "final": cov_b,
                                               "unidades_fallback": 0}},
           "unidades": {rep: page["bounding_boxes"] for rep, page in (("A", a), ("B", p))},
           "resultados": {}}
    for rep, page in (("A", a), ("B", p)):
        regra, diag = b.prever(page, obj["palavras"], "regra_colunas")
        for ordenador in ORDENADORES:
            ordem, dg = (regra, {**diag, "escolhido": "regra"}) if ordenador == "regra" else ordem_hibrida(
                obj, page, rep, coorte, regra, preds, conferir)
            res = medir(obj, page, ordem)
            row["resultados"][f"{rep}_{ordenador}"] = {**res, "diag": dg}
            gravar(path, row)
    if hist_row:
        row["historico"] = historico_pagina(obj, p, hist_row)
    row["completa"] = True
    gravar(path, row)
    return row


def contraste(rows, atual, base):
    W = b.PESOS_CLUSTER(rows)
    saida = {}
    for k in METRICAS:
        ds = [r["resultados"][atual]["metricas"][k] - r["resultados"][base]["metricas"][k] for r in rows]
        por_uf = {uf: statistics.mean(d for r, d in zip(rows, ds) if r["uf"] == uf)
                  for uf in sorted({r["uf"] for r in rows})}
        saida[k] = {**e.media_ic(ds, W), "por_veiculo": por_uf,
                    "wilcoxon_veiculo": e.pratt(list(por_uf.values())),
                    "melhor": sum(d < -1e-12 if k in ("quebras", "quebras_mil", "piso_interno", "entre_unidades")
                                  else d > 1e-12 for d in ds),
                    "igual": sum(abs(d) <= 1e-12 for d in ds)}
        saida[k]["pior"] = len(ds) - saida[k]["melhor"] - saida[k]["igual"]
    reparos = regressoes = 0
    for r in rows:
        a, z = r["resultados"][base], r["resultados"][atual]
        exigir(a["sucessores_elegiveis"] == z["sucessores_elegiveis"], "Universos de sucessores divergentes")
        aa, zz = set(a["sucessores_certinhos"]), set(z["sucessores_certinhos"])
        reparos += len(zz-aa)
        regressoes += len(aa-zz)
    saida["reparos_sucessor"] = reparos
    saida["regressoes_sucessor"] = regressoes
    return saida


def resumir(rows):
    W = b.PESOS_CLUSTER(rows)
    out = {"n": len(rows), "veiculos": len({r["uf"] for r in rows}), "metodos": {}, "contrastes": {}}
    for rep in REPS:
        for ordenador in ORDENADORES:
            nome = f"{rep}_{ordenador}"
            ms = {k: e.media_ic([r["resultados"][nome]["metricas"][k] for r in rows], W) for k in METRICAS}
            for k in ("quebras", "piso_interno", "entre_unidades"):
                ms[k]["total"] = sum(r["resultados"][nome]["metricas"][k] for r in rows)
            out["metodos"][nome] = ms
            out["contrastes"][nome + "-B_regra"] = contraste(rows, nome, "B_regra")
            out["contrastes"][nome + "-" + rep + "_regra"] = contraste(rows, nome, rep + "_regra")
    for ordenador in ORDENADORES:
        out["contrastes"]["B-A_" + ordenador] = contraste(rows, "B_"+ordenador, "A_"+ordenador)
    out["cobertura"] = {}
    for rep in REPS:
        out["cobertura"][rep] = {}
        for fase in ("antes_fallback", "final"):
            fases = [r["cobertura"][rep][fase]["ouro"] for r in rows]
            totais = {k: sum(c[k] for c in fases) for k in ("n", "cobertas", "duplicadas", "orfas", "geometricamente_multiplas")}
            totais.update({k + "_pct": 100*totais[k]/totais["n"] for k in ("cobertas", "duplicadas", "orfas")})
            totais["paginas_com_orfas"] = sum(c["orfas"] > 0 for c in fases)
            out["cobertura"][rep][fase] = totais
    return out


def numero(x, n=6):
    return f"{x:.{n}f}".replace(".", ",")


def intervalo(z):
    return f"{numero(z['media'])} [{numero(z['ic'][0])}; {numero(z['ic'][1])}]"


def publicar(dados, anc, inventario, manifesto):
    resumos = {co: resumir(rows) for co, rows in dados.items() if rows}
    criterios = {}
    for co in COORTES[:2]:
        s = resumos[co]
        for ordenador in ORDENADORES:
            d = s["contrastes"]["B-A_" + ordenador]["quebras"]
            criterios[co+"/"+ordenador] = d["media"] < 0 and d["ic"][1] < 0
        criterios[co+"/cobertura"] = all(r["cobertura"]["B"]["antes_fallback"]["ouro"]["cobertas"] >=
            r["cobertura"]["A"]["antes_fallback"]["ouro"]["cobertas"] for r in dados[co])
    completa = all(inventario[co]["faltantes_A"] == 0 and len(dados[co]) == inventario[co]["paginas"] for co in COORTES)
    veredito = "SUCESSO" if completa and all(criterios.values()) else "CRITÉRIO NÃO ATINGIDO" if completa else "INCONCLUSIVO: COBERTURA DE PÁGINAS INCOMPLETA"
    historico = {co: {m: {k: sum(r["historico"][m][k] for r in dados[co])
                 for k in ("piso_antigo", "piso_atual", "quebras")} for m in ("P1", "P1m", "P2")} for co in COORTES[:2]}
    somas = {m: {k: sum(historico[co][m][k] for co in COORTES[:2]) for k in ("piso_antigo", "piso_atual")} for m in ("P1", "P1m", "P2")}
    historico_ok = somas["P1"]["piso_antigo"] == 213 and somas["P2"]["piso_antigo"] == 29
    resumo = {co+"/"+nome: {"tau": ms["tau"]["media"], "quebras": ms["quebras"]["media"],
                             "sucessor": ms["sucessor_linhas"]["media"]}
              for co, s in resumos.items() for nome, ms in s["metodos"].items()}
    exigir(all(v is not None and math.isfinite(v) for ms in resumo.values() for v in ms.values()), "Resumo com nulos")
    gravar(OUT / "resumo_registro.json", resumo)
    gravar(OUT / "resultados.json", {"ancora": anc, "inventario": inventario, "resumos": resumos,
            "veredito": veredito, "criterios": criterios, "historico": historico, "historico_somas": somas,
            "historico_213_29_reproduzido": historico_ok, "manifesto": manifesto, "layoutreader": INFO_LR})
    s4, s3 = resumos["golden_v4"], resumos["golden_v3_novo"]
    linhas = ["# E009 — caixas automáticas × linhas automáticas", "",
        f"1. Âncora reproduzida: τ {numero(anc['tau'])}; {numero(anc['quebras'])} quebras/página no golden_v4.",
        f"2. Páginas pareadas: " + "; ".join(f"{co} {s['n']}" for co, s in resumos.items()) + ".",
        "3. Δ B − A com regra: v4 " + intervalo(s4["contrastes"]["B-A_regra"]["quebras"]) + "; v3 novo " + intervalo(s3["contrastes"]["B-A_regra"]["quebras"]) + ".",
        "4. Δ B − A com híbrido 67: v4 " + intervalo(s4["contrastes"]["B-A_hibrido67"]["quebras"]) + "; v3 novo " + intervalo(s3["contrastes"]["B-A_hibrido67"]["quebras"]) + ".",
        "5. Cobertura final: " + "; ".join(f"{co} A/B {numero(s['cobertura']['A']['final']['cobertas_pct'],2)}%/{numero(s['cobertura']['B']['final']['cobertas_pct'],2)}%" for co,s in resumos.items()) + ".",
        f"6. Histórico reproduzido na definição antiga: {somas['P1']['piso_antigo']} → {somas['P2']['piso_antigo']}; na atual: {somas['P1']['piso_atual']} → {somas['P2']['piso_atual']} quebras internas.",
        "", f"**Veredito pelo cartão: {veredito}.**", "",
        "Os critérios são aplicados sem alteração: Δ quebras < 0 e limite superior do IC95 < 0 em cada bancada humana e ordenador, com cobertura de B ≥ A. Não há critério de abandono: trata-se de medição de base.", "",
        ("O ganho de qualidade de ordenação exigido pelo cartão foi demonstrado." if veredito == "SUCESSO" else
         "Este E009 não sustenta a justificativa de superioridade da representação simplificada em quebras totais com ordenador fixo. O piso interno menor não basta para concluir melhor ordenação; custo e qualidade da anotação ainda dependem do E008."), "",
        "## Representações e controle", "",
        "A = caixas automáticas do pipeline de outubro P1/P1m: `propor(regras=True)`, Docling Heron + blocos automáticos v3. Não são caixas humanas nem um detector puro de parágrafos. Nas bancadas humanas reutilizam-se as unidades congeladas de `erros_ponta_a_ponta.json`; no silver, a mesma receita recebe palavras canônicas e cache Heron. B = `linhas` exportadas em `resultados/unidades_sem_caixas/`, incluindo átomos ls3. O ls3 ignora suas caixas de texto em B. A comparação caracteriza estes dois pipelines de representação; a origem dos átomos também difere, portanto não isola apenas o tamanho da unidade.", "",
        "Cada unidade guarda os IDs de palavra em `cache/paginas/`. Antes de ordenar, órfãs de A viram linhas com `ordem_sem_bbox.linhas()`. A posse é exclusiva; cobertura por atribuição e sobreposição geométrica são diagnósticos distintos. Toda palavra disponível, inclusive fora do ouro, permanece exatamente uma vez nas duas saídas. A cobertura é da camada digital, não de texto em imagem sem OCR.", "",
        "Os ordenadores são os mesmos `bancada_ordenadores.prever`: regra de colunas e LayoutReader pronto até 67 unidades, regra acima. O limiar é aplicado ao número de unidades de cada representação, incluindo vazias/fallback. Isso conserva a política, mas pode mudar a rota ao mudar a representação. O híbrido se aplica a caixas pela interface genérica do adaptador; não se retreina nem se escolhe limiar. Expansão interna sempre `ordem_sem_bbox.fluxo()`. Entrada `random.Random(f'entrada-{page_id}')` via protocolo/adaptador.", "",
        f"Nenhum detector executado (CPU ou GPU); LayoutReader apenas em CPU/float32, no máximo quatro threads, um processo e zero workers. Predições de caixas ausentes: " + "; ".join(f"{co}: {z['faltantes_A']}" for co,z in inventario.items()) + ".", ""]
    for co, s in resumos.items():
        linhas += [f"## {co}", "", f"{s['n']} páginas, {s['veiculos']} veículos. Médias por página; IC95 agrupado por veículo.", "",
            "| Representação/ordenador | τ palavras | Quebras/página | Dentro de unidades/página | Entre unidades/página | Fidelidade 12 | Sucessor linhas | Quebras/mil |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for nome, ms in s["metodos"].items():
            linhas.append("| " + nome + " | " + " | ".join(numero(ms[k]["media"]) for k in
                ("tau", "quebras", "piso_interno", "entre_unidades", "fid12", "sucessor_linhas", "quebras_mil")) + " |")
        linhas += ["", "| Cobertura ouro | N palavras | Cobertas % | Duplicadas % | Órfãs % | Múltiplas caixas geométricas |", "|---|---:|---:|---:|---:|---:|"]
        for rep in REPS:
            for fase in ("antes_fallback", "final"):
                z = s["cobertura"][rep][fase]
                linhas.append(f"| {rep}/{fase} | {z['n']} | {numero(z['cobertas_pct'])} | {numero(z['duplicadas_pct'])} | {numero(z['orfas_pct'])} | {z['geometricamente_multiplas']} |")
        linhas += ["", "| Contraste | Métrica | Δ [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior |", "|---|---|---:|---:|---:|"]
        for nome in ("B-A_regra", "B-A_hibrido67", "A_regra-B_regra", "A_hibrido67-B_regra", "B_hibrido67-B_regra", "A_hibrido67-A_regra"):
            for k in METRICAS:
                z = s["contrastes"][nome][k]
                linhas.append(f"| {nome} | {k} | {intervalo(z)} | {numero(z['wilcoxon_veiculo']['p'])} | {z['melhor']}/{z['igual']}/{z['pior']} |")
        linhas += ["", "| Contraste | Sucessores reparados | Sucessores regredidos |", "|---|---:|---:|"]
        for nome in ("B-A_regra", "B-A_hibrido67", "A_hibrido67-B_regra", "B_hibrido67-B_regra"):
            z = s["contrastes"][nome]
            linhas.append(f"| {nome} | {z['reparos_sucessor']} | {z['regressoes_sucessor']} |")
        linhas += ["", "| Veículo | Páginas | Δ quebras B − A regra | Δ quebras B − A híbrido 67 |", "|---|---:|---:|---:|"]
        for uf in sorted({r["uf"] for r in dados[co]}):
            dr = s["contrastes"]["B-A_regra"]["quebras"]["por_veiculo"][uf]
            dh = s["contrastes"]["B-A_hibrido67"]["quebras"]["por_veiculo"][uf]
            linhas.append(f"| {uf} | {sum(r['uf'] == uf for r in dados[co])} | {numero(dr)} | {numero(dh)} |")
        rotas = {nome: sum(r["resultados"][nome]["diag"]["escolhido"] == "layoutreader_pronto" for r in dados[co]) for nome in ("A_hibrido67", "B_hibrido67")}
        linhas += ["", "Páginas roteadas ao LayoutReader: " + "; ".join(f"{k}: {v}" for k,v in rotas.items()) + ".", ""]
    linhas += ["## Reconstrução de 213 → 29", "",
        "A fonte numérica exata é `resultados/erros_ponta_a_ponta.json`, resumida em seu Markdown. O relatório da noite cita a comparação de pipelines, mas não contém literalmente o par 213 → 29. O par soma as duas bancadas humanas; aparece aqui só para reconstrução histórica, sem inferência sobre a soma.", "",
        "| Bancada | Pipeline | Piso antigo | Piso atual (bancada) | Quebras totais antigas |", "|---|---|---:|---:|---:|"]
    for co, met in historico.items():
        for m, z in met.items():
            linhas.append(f"| {co} | {m} | {z['piso_antigo']} | {z['piso_atual']} | {z['quebras']} |")
    linhas += ["", f"Na definição original, o par é {'confirmado' if historico_ok else 'não reproduzido'}: contam-se eventos com as duas palavras na mesma unidade, excluindo palavras fora do ouro interpostas. A bancada atual soma `eventos(fluxo([unidade]), gt_w)` e inclui essas intercalações internas; daí {somas['P1']['piso_atual']} → {somas['P2']['piso_atual']}. A direção histórica só se confirma sob a régua atual se o segundo total continuar menor; isso é " + ("verdadeiro" if somas['P2']['piso_atual'] < somas['P1']['piso_atual'] else "falso") + ". Não representa redução de quebras totais nem garante ganho com ordenador fixo.", "",
        "## Critérios e limitações", "", *[f"- {k}: {'atendido' if v else 'não atendido'}." for k,v in criterios.items()], "",
        f"Bootstrap importado da bancada: {b.NBOOT} reamostras de veículos, semente {b.SEMENTE}, percentis de 95%; todas as páginas de um veículo sorteado permanecem juntas, mantendo média por página. Wilcoxon Pratt bilateral sobre médias dos deltas por veículo, exploratório e sem correção de multiplicidade. Dados por veículo e IC de todas as métricas ficam em `resultados.json`. Silver tem apenas {resumos.get('teste_silver',{}).get('veiculos',0)} veículos; baixa resolução inferencial.", "",
        "golden_v4 foi usado para desenvolver a regra e escolher o limiar 67. golden_v3_novo já foi consultado em rodadas anteriores; não é teste confirmatório independente. O silver CE/MA/RJ é sensibilidade: fluxo do PDF ruidoso, seleção por concordância com XY-cut e divergência nas tabelas. Bancadas podem compartilhar páginas e veículos: não somar como observações independentes. Não houve ajuste nesta execução nem consulta à validação RN para escolher parâmetros.", "",
        "O ouro humano anota ordem de regiões, com expansão geométrica para palavras/linhas, não transcrição ou sucessão independente de cada palavra. Há viés de pré-anotação no Diamond e de blocos no v3; tabelas são ambíguas. Relata-se a página inteira com palavras fora do ouro preservadas; não há referência independente só do corpo. Dentro/entre unidades é decomposição operacional dos eventos emitidos, não atribuição causal de erro ao detector. A duplicação geométrica não implica duplicação na saída.", "",
        "O teste cego foi excluído pelo lacre antes da desserialização de cada página. Não se abriram PDFs, imagens, `data/labelstudio`, exports ou fontes do parceiro; só foram usados derivados e caches próprios já existentes. Nada foi gravado em `data/`. O E009 não mede tempo de anotação nem justifica sozinho a adoção no E008.", "",
        "Reexecução: `venv/Scripts/python.exe -B orquestracao/analises/e009_representacao.py`. Auditoria sem nova inferência: acrescentar `--conferir`. Manifesto, hashes e comando ficam em `manifesto.json`; resultados parciais e mapas de palavras em `cache/`. Todos os números deste relatório foram escritos por este script.", ""]
    gravar(OUT / "RELATORIO.md", "\n".join(linhas))
    print("Veredito: " + veredito, flush=True)


def main():
    global CEGAS, LACRE, DEPENDENCIAS, INFO_LR
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--somente-ancora", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    lock = RAIZ / "experimentos/TESTE_CEGO.lock"
    LACRE = b.sha(lock) if lock.exists() else None
    CEGAS = set(ler(lock)["page_id"]) if lock.exists() else set()
    paths = [*b.DEP_PATHS, e.JSON, RAIZ / "models/terceiros/layoutreader/model.safetensors",
             RAIZ / "models/terceiros/layoutreader/config.json"]
    DEPENDENCIAS = {b.rel(p): b.sha(p) for p in paths}
    inicio = time.perf_counter()
    with trava():
        anc = ancora()
        if args.somente_ancora:
            return
        hist = carregar_historico()
        auditoria_fontes = auditar_fontes(hist)
        print("Fontes conferidas: mesmos IDs/palavras e receita de caixas de outubro", flush=True)
        if (OUT / "cache/layoutreader.json").exists():
            INFO_LR = ler(OUT / "cache/layoutreader.json")
        elif (OUT / "resultados.json").exists():
            INFO_LR = ler(OUT / "resultados.json").get("layoutreader", {})
            if INFO_LR:
                gravar(OUT / "cache/layoutreader.json", INFO_LR)
        antigas = {r["page_id"]: r for r in hist["paginas"]}
        silver = collections.defaultdict(set)
        for _, p in paginas("teste_silver"):
            silver[p["uf"]].add(p["page_id"])
        det = fontes_layout(silver)
        inventario = {}
        for co in COORTES:
            ids = [p["page_id"] for _, p in paginas(co)]
            exigir(len(ids) == len(set(ids)), "Pagina repetida na bancada")
            disponiveis = det if co == "teste_silver" else antigas
            faltantes = sorted(set(ids) - set(disponiveis))
            inventario[co] = {"paginas": len(ids), "faltantes_A": len(faltantes), "ids_faltantes_A": faltantes}
        gravar(OUT / "inventario.json", inventario)
        print("Disponibilidade de caixas: " + json.dumps(inventario, ensure_ascii=False), flush=True)
        preds = predicoes_B()
        dados = {}
        manifesto = {"versao": VERSAO, "data_utc": datetime.now(timezone.utc).isoformat(),
            "comando": "venv/Scripts/python.exe -B " + " ".join(sys.argv),
            "script_sha256": b.sha(Path(__file__)), "dependencias": DEPENDENCIAS,
            "lacre_sha256": LACRE, "paginas_cegas_bloqueadas": len(CEGAS),
            "device": "cpu", "threads": 4, "num_workers": 0, "processos_pesados": 1,
            "inferencia_detector_cpu": 0, "inferencia_detector_gpu": 0,
            "parametros_ajustados": 0, "limiar_hibrido": 67,
            "auditoria_fontes": auditoria_fontes,
            "deteccoes_silver_sha256": b.digest(det),
            "predicoes_layoutreader_B_sha256": b.digest(sorted((co, pid, ordem) for (co,pid),ordem in preds.items()))}
        gravar(OUT / "manifesto.json", manifesto)
        for co in COORTES:
            rows = []
            for obj, p in paginas(co):
                if p["page_id"] in inventario[co]["ids_faltantes_A"]:
                    continue
                rows.append(processar(obj, p, co, antigas, det, preds, args.conferir))
                print(f"{co}: {len(rows)}/{inventario[co]['paginas']} paginas", flush=True)
                gravar(OUT / "progresso.json", {"bancada": co, "concluidas": len(rows),
                        "segundos": time.perf_counter()-inicio})
            exigir(rows, f"Nenhuma pagina com caixas em {co}; nao emitir medias")
            dados[co] = rows
        publicar(dados, anc, inventario, manifesto)
        vigiar()


if __name__ == "__main__":
    main()
