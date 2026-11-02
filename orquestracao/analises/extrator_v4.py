"""Constroi e mede regioes v4 na convencao do guia, sem alterar dados ou src.

O detector do dominio fornece a segmentacao inicial; a camada digital fornece
palavras, ajustes de caixa e recuperacao de texto. A grade de parametros e
avaliada deixando uma FONTE inteira de fora, nunca ajustando na pagina avaliada.
Os caches anteriores sao somente leitura. Derivados internos ficam exclusivamente
em resultados/extrator_v4_cache. Nao ha OCR, treino, GPU ou acesso a rede.

Uso, da raiz: venv/Scripts/python.exe orquestracao/analises/extrator_v4.py
--do-zero refaz todos os derivados geometricos, preservando os insumos congelados.
--kaggle acrescenta RT-DETR L local em CPU; --autoteste verifica casos sinteticos.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.dont_write_bytecode = True
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["YOLO_OFFLINE"] = "true"
os.environ["YOLO_AUTOINSTALL"] = "false"

import numpy as np
from scipy.stats import wilcoxon
from orquestracao.analises import extrator_vs_detector_ls as anterior
from src.data.extrator import segmentar, _faixas_de_base
from src.data.taxonomia_layout import GUIA, GUIA_PARA_EXTRATOR

CACHE = RAIZ / "resultados/extrator_v4_cache"
RELATORIO = RAIZ / "resultados/extrator_v4.md"
os.environ["YOLO_CONFIG_DIR"] = str(CACHE / "ultralytics_config")
REGUAS = {"loc50": (None, .5), "loc75": (None, .75),
          "c3_50": (3, .5), "c3_75": (3, .75),
          "c16_50": (16, .5), "c16_75": (16, .75)}
SEMENTE = 20261003


@dataclass(frozen=True)
class Config:
    base: str = "uniao"
    score: float = .25
    folga: float = .5  # Alturas medianas de palavra, em pontos do PDF.
    contencao: float = .98
    par_classe: float = .5
    detector: bool = True
    ajuste: bool = True
    orfas: bool = True
    conflitos: bool = True
    texto: bool = True
    sem_texto: bool = True


PADRAO = Config()
ABLACOES = {"sem_a_detector": "detector", "sem_b_ajuste": "ajuste",
            "sem_c_orfas": "orfas", "sem_d_conflitos": "conflitos",
            "sem_e_texto": "texto", "sem_f_sem_texto": "sem_texto"}


def ler(p):
    return anterior.ler(p)


def salvar(p, obj):
    anterior.salvar(p, obj)


def numero(v, casas=3):
    return anterior.numero(v, casas)


def probabilidade(v):
    return f"{v:.3g}".replace(".", ",") if 0 < v < 1e-6 else numero(v, 6)


def macroclasse(c):
    return c if c in anterior.CLASSES3 else anterior.mapa3(c)


def fina(c):
    return {"texto": "paragraph", "tabela": "table", "imagem": "figure"}.get(c, c)


def score_caixa(b):
    s = b.get("score")
    return 1. if s is None else float(s)


def area(b):
    return max(0., b[2]-b[0]) * max(0., b[3]-b[1])


def intersecao(a, b):
    return max(0., min(a[2], b[2])-max(a[0], b[0])) * max(0., min(a[3], b[3])-max(a[1], b[1]))


def envelope(ws):
    return [min(w["x0"] for w in ws), min(w["top"] for w in ws),
            max(w["x1"] for w in ws), max(w["bottom"] for w in ws)]


def matriz_centros(ws, caixas):
    if not ws or not caixas:
        return np.zeros((len(ws), len(caixas)), dtype=bool)
    xy = np.array([[(w["x0"]+w["x1"])/2, (w["top"]+w["bottom"])/2] for w in ws])
    bb = np.array([b["bbox"] for b in caixas])
    # Bordas inclusivas; propriedade unica e resolvida explicitamente abaixo.
    return ((xy[:, None, :] >= bb[None, :, :2]) & (xy[:, None, :] <= bb[None, :, 2:])).all(axis=2)


def atribuir(ws, caixas, unica=True):
    dentro = matriz_centros(ws, caixas)
    grupos = [[] for _ in caixas]
    for i in range(len(ws)):
        js = np.flatnonzero(dentro[i]).tolist()
        if unica and js:
            # Tabela/texto antes de imagem; caixa menor, score e ordem desempatam.
            js = [min(js, key=lambda j: (macroclasse(caixas[j]["classe"]) == "imagem",
                                        area(caixas[j]["bbox"]), -score_caixa(caixas[j]), j))]
        for j in js:
            grupos[j].append(i)
    return grupos


def ler_texto(ws):
    if not ws:
        return ""
    linhas = _faixas_de_base(ws)
    return "\n".join(" ".join(w["t"] for w in sorted(L["ws"], key=lambda w: (w["x0"], w["s"])))
                     for L in sorted(linhas, key=lambda L: min(w["top"] for w in L["ws"])))


def caixas_base(detectores, cfg):
    nome = "ls3" if cfg.base == "uniao" else cfg.base
    caixas = [{**b, "bbox": list(b["bbox"]), "classe": fina(b["classe"]),
               "origem_v4": nome} for b in detectores.get(nome, []) if score_caixa(b) >= cfg.score]
    if cfg.base == "uniao":
        outras = [{**b, "classe": fina(b["classe"])} for b in detectores.get("ls16", [])
                  if score_caixa(b) >= cfg.score]
        # Pareamento 1-1 e COMPATIVEL em 3 classes: a uniao nao troca tabela por texto.
        _, pares = anterior.emparelhar(caixas, outras, cfg.par_classe, 3)
        for i, j, _ in pares:
            caixas[i]["classe"] = outras[j]["classe"]
            caixas[i]["origem_classe"] = "ls16"
    return caixas


def resolver_conflitos(caixas, limiar):
    """Suprime caixas contidas e particiona intersecoes com cortes retangulares.

    A maior caixa e preservada na contencao. Em intersecoes parciais escolhe o
    corte x/y que remove menos area, com desempate fixo. Pode perder texto real
    sobreposto (carimbo), uma limitacao a medir, nao uma propriedade do ouro.
    """
    caixas = [{**b, "bbox": list(b["bbox"])} for b in caixas]
    remover = set()
    ordem = sorted(range(len(caixas)), key=lambda j: (-area(caixas[j]["bbox"]),
                                                    -score_caixa(caixas[j]), j))
    for pos, j in enumerate(ordem):
        if j in remover:
            continue
        for k in ordem[pos+1:]:
            if k not in remover and intersecao(caixas[j]["bbox"], caixas[k]["bbox"]) / max(1e-9, area(caixas[k]["bbox"])) >= limiar:
                remover.add(k)
    caixas = [b for j, b in enumerate(caixas) if j not in remover]
    cortes = 0
    for j in range(len(caixas)):
        for k in range(j+1, len(caixas)):
            a, b = caixas[j]["bbox"], caixas[k]["bbox"]
            if intersecao(a, b) <= 1e-8:
                continue
            escolhas = []
            for eixo in (0, 1):
                ca, cb = (a[eixo]+a[eixo+2])/2, (b[eixo]+b[eixo+2])/2
                esquerda = ca <= cb
                l, r = (a, b) if esquerda else (b, a)
                lo, hi = max(l[eixo], r[eixo]), min(l[eixo+2], r[eixo+2])
                corte = min(hi, max(lo, (ca+cb)/2))
                nl, nr = list(l), list(r)
                nl[eixo+2], nr[eixo] = corte, corte
                perda = area(l)+area(r)-area(nl)-area(nr)
                escolhas.append((perda, eixo, esquerda, nl, nr))
            _, _, esquerda, nl, nr = min(escolhas, key=lambda z: (z[0], z[1]))
            caixas[j]["bbox"], caixas[k]["bbox"] = (nl, nr) if esquerda else (nr, nl)
            cortes += 1
    caixas = [b for b in caixas if area(b["bbox"]) > 1e-8]
    return caixas, {"suprimidas": len(remover), "cortes": cortes}


def subtrair_retangulo(a, b):
    """Partes retangulares de a fora de b; sem aproximar o formato em L."""
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return [a]
    partes = [[a[0], a[1], a[2], y0], [a[0], y1, a[2], a[3]],
              [a[0], y0, x0, y1], [x1, y0, a[2], y1]]
    return [p for p in partes if area(p) > 1e-8]


def recuperar_apos_cortes(ws, caixas):
    """Conserva palavras que um corte retangular expulsou de um canto da caixa.

    A subtracao exata das caixas ja presentes pode fragmentar a caixa recuperada,
    mas nao reintroduz intersecoes nem duplica proprietarios. Separadores sem
    letras/digitos continuam sujeitos ao descarte do segmentador v3.
    """
    dentro = matriz_centros(ws, caixas).any(axis=1)
    resto = [w for i, w in enumerate(ws) if not dentro[i]]
    novas = 0
    for B in segmentar(resto):
        grupo = [w for L in B["linhas"] for w in L["ws"]]
        partes = [envelope(grupo)]
        for b in caixas:
            partes = [p for parte in partes for p in subtrair_retangulo(parte, b["bbox"])]
        for bb in partes:
            if matriz_centros(grupo, [{"bbox": bb}]).any():
                caixas.append({"bbox": bb, "classe": "paragraph", "score": 1., "origem_v4": "orfas_pos_corte"})
                novas += 1
    return caixas, novas


def propor_v4(palavras, detectores, cfg=PADRAO):
    """Etapas independentes; entrada/saida em pontos, sem consultar anotacoes.

    Palavras sao dicionarios t/x0/x1/top/bottom/s; detectores e um mapa de listas
    id/bbox/classe/score. 'palavras_ids' e a propriedade explicita de cada palavra.
    Sem camada digital conserva somente as caixas do detector, sem inventar OCR.
    """
    t = time.perf_counter()
    caixas = caixas_base(detectores, cfg) if cfg.detector else []
    ws = [dict(w) for w in palavras]
    tem_texto = any(re.search(r"[0-9A-Za-zÀ-ÿ]", w.get("t", "")) for w in ws)
    stats = {"orfas_iniciais": 0, "orfas_finais": 0, "novas": 0, "anexadas": 0,
             "suprimidas": 0, "cortes": 0, "duplicadas": 0, "novas_pos_corte": 0,
             "orfas_alfanum": 0}
    if not tem_texto:
        caixas = caixas if cfg.sem_texto else []
        for j, b in enumerate(caixas):
            b.update(id=f"v4_{j}", texto="", palavras_ids=[])
        return caixas, stats, (time.perf_counter()-t)*1000
    if cfg.ajuste:
        grupos = atribuir(ws, caixas, unica=False)
        for b, ids in zip(caixas, grupos):
            if macroclasse(b["classe"]) == "texto" and ids:
                b["bbox"] = envelope([ws[i] for i in ids])
    cobertas = matriz_centros(ws, caixas).any(axis=1)
    resto = [w for i, w in enumerate(ws) if not cobertas[i]]
    stats["orfas_iniciais"] = len(resto)
    if cfg.orfas and resto:
        altura = statistics.median(max(.1, w["bottom"]-w["top"]) for w in ws)
        # O segmentador v3 opera em pontos, sem ajustes aos seus parametros.
        for B in segmentar(resto):
            grupo = [w for L in B["linhas"] for w in L["ws"]]
            bb = envelope(grupo)
            candidatos = []
            for j, b in enumerate(caixas):
                if macroclasse(b["classe"]) != "texto":
                    continue
                a = b["bbox"]
                dx, dy = max(0., a[0]-bb[2], bb[0]-a[2]), max(0., a[1]-bb[3], bb[1]-a[3])
                sx = max(0., min(a[2], bb[2])-max(a[0], bb[0])) / max(.1, min(a[2]-a[0], bb[2]-bb[0]))
                sy = max(0., min(a[3], bb[3])-max(a[1], bb[1])) / max(.1, min(a[3]-a[1], bb[3]-bb[1]))
                if cfg.folga > 0 and max(dx, dy) <= cfg.folga*altura and (sx >= .5 or sy >= .5):
                    unido = [min(a[0], bb[0]), min(a[1], bb[1]), max(a[2], bb[2]), max(a[3], bb[3])]
                    # Impede que anexacao atravesse outra caixa da pagina.
                    if not any(k != j and intersecao(unido, o["bbox"])-intersecao(a, o["bbox"]) > 1e-8
                               for k, o in enumerate(caixas)):
                        candidatos.append((dx+dy, -score_caixa(b), j, unido))
            if candidatos:
                _, _, j, unido = min(candidatos)
                caixas[j]["bbox"] = unido
                stats["anexadas"] += len(grupo)
            else:
                caixas.append({"id": "orfa", "bbox": bb, "classe": "paragraph", "score": 1., "origem_v4": "orfas"})
                stats["novas"] += 1
    if cfg.conflitos:
        caixas, conflitos = resolver_conflitos(caixas, cfg.contencao)
        stats.update(conflitos)
        if cfg.orfas:
            caixas, novas = recuperar_apos_cortes(ws, caixas)
            stats["novas_pos_corte"] = novas
    grupos = atribuir(ws, caixas, unica=cfg.conflitos)
    vistos = Counter(i for ids in grupos for i in ids)
    stats["orfas_finais"] = len(ws)-len(vistos)
    stats["orfas_alfanum"] = sum(i not in vistos and bool(re.search(r"[0-9A-Za-zÀ-ÿ]", w.get("t", ""))) for i, w in enumerate(ws))
    stats["duplicadas"] = sum(n-1 for n in vistos.values())
    for j, (b, ids) in enumerate(zip(caixas, grupos)):
        b.update(id=f"v4_{j}", palavras_ids=ids,
                 texto=ler_texto([ws[i] for i in ids]) if cfg.texto else "")
    return caixas, stats, (time.perf_counter()-t)*1000


def normalizar_espacos(t):
    return " ".join(str(t or "").split())


def distancia(a, b):
    """Levenshtein exata com vetores de bits, sem dependencias adicionais."""
    if len(a) > len(b):
        a, b = b, a
    if not a:
        return len(b)
    m, eq = len(a), {}
    for i, c in enumerate(a):
        eq[c] = eq.get(c, 0) | (1 << i)
    vp, vn, erro, topo, mascara = (1 << m)-1, 0, m, 1 << (m-1), (1 << m)-1
    for c in b:
        x = eq.get(c, 0) | vn
        d = (((x & vp)+vp) ^ vp) | x
        hp, hn = vn | ~(d | vp), vp & d
        erro += bool(hp & topo) - bool(hn & topo)
        hp, hn = (hp << 1) | 1, hn << 1
        vp, vn = (hn | ~(d | hp)) & mascara, d & hp & mascara
    return erro


def assinatura_codigo():
    funcoes = (macroclasse, fina, score_caixa, area, intersecao, envelope, matriz_centros, atribuir,
               ler_texto, caixas_base, resolver_conflitos, subtrair_retangulo, recuperar_apos_cortes,
               propor_v4, normalizar_espacos, distancia, carregar, gerar)
    return anterior.sha([inspect.getsource(Config), *[inspect.getsource(f) for f in funcoes],
                         anterior.codigo_id("src/data/extrator.py"), list(REGUAS.items())])


def carregar():
    ouro = ler(anterior.CACHE / "ouro.json")
    assert ouro and len(ouro["paginas"]) == 317
    paginas = ouro["paginas"]
    assert len({p["fonte"] for p in paginas}) == 42
    ctx = []
    for p in paginas:
        dados = {et: ler(anterior.caminho_cache(p, et)) for et in ("palavras", "docling", "extrator", "ls3", "ls16")}
        assert all(dados.values()) and not any(c.get("erro") for c in dados.values()), p["page_id"]
        assert all(dados[n]["entrada_id"] == p["entrada_id"] for n in ("ls3", "ls16"))
        assert dados["palavras"]["assinatura"] == anterior.assinatura_palavras(p), "Palavras mudaram"
        assert dados["extrator"]["assinatura"] == anterior.assinatura_extrator(dados["palavras"], dados["docling"]), "Extrator mudou"
        w, d = dados["palavras"], dados["docling"]
        x0, y0, x1, y1 = d["bbox_imagem"]
        sx, sy = p["width"]/(x1-x0), p["height"]/(y1-y0)
        palavras = [{**z, "x0": z["x0"]-x0, "x1": z["x1"]-x0,
                     "top": z["top"]-y0, "bottom": z["bottom"]-y0} for z in w["ws"]]
        visiveis = [z for z in palavras if 0 <= (z["x0"]+z["x1"])/2 <= x1-x0
                    and 0 <= (z["top"]+z["bottom"])/2 <= y1-y0]
        excluidas = len(palavras)-len(visiveis)
        palavras = visiveis
        detectores = {n: [{**b, "bbox": [b["bbox"][0]/sx, b["bbox"][1]/sy,
                                         b["bbox"][2]/sx, b["bbox"][3]/sy]} for b in dados[n]["caixas"]]
                      for n in ("ls3", "ls16")}
        ctx.append({"p": p, "dados": dados, "ws": palavras, "detectores": detectores,
                    "sx": sx, "sy": sy, "sem_texto": w["sem_texto"], "palavras_fora_recorte": excluidas})
    assinatura = anterior.sha([ouro["assinatura"], assinatura_codigo(),
                               [[c["dados"][n]["assinatura"] for n in ("palavras", "docling", "extrator", "ls3", "ls16")] for c in ctx]])
    return ctx, assinatura


def auditar_dataset():
    """Conta conversoes incrementalmente e distingue-as do split utilizavel."""
    paginas = set()
    n = 0
    for seed in range(1, 5):
        for tarefa in anterior.jsonl(RAIZ / f"data/labelstudio/conv_seed{seed}/tarefas.jsonl"):
            n += 1
            if tarefa.get("page_id"):
                paginas.add(tarefa["page_id"])
    split = ler(RAIZ / "data/deteccao/ls_split.json")["paginas"]
    return {"tarefas_convertidas": n, "paginas_convertidas": len(paginas), "paginas_split": len(split),
            "particoes": dict(Counter(p.get("split", "ausente") for p in split.values())),
            "fora_split": len(paginas-set(split))}


def gerar(c, cfg):
    caixas, stats, ms = propor_v4(c["ws"], c["detectores"], cfg)
    sx, sy = c["sx"], c["sy"]
    caixas_px = [{**b, "bbox": [max(0., b["bbox"][0]*sx), max(0., b["bbox"][1]*sy),
                               min(float(c["p"]["width"]), b["bbox"][2]*sx),
                               min(float(c["p"]["height"]), b["bbox"][3]*sy)]} for b in caixas]
    caixas_px = [b for b in caixas_px if area(b["bbox"]) > 0]
    nomes = ["ls3", "ls16"] if cfg.base == "uniao" else [cfg.base]
    det_ms = sum(c["dados"][n]["tempo_ms"] for n in nomes) if cfg.detector else 0.
    palavras_ms = c["dados"]["palavras"]["tempo_palavras_ms"]
    # Raster LS de entrada ja existe, tal como nos detectores puros anteriores.
    return {"caixas": caixas_px, "stats": stats, "pos_ms": ms,
            "tempo_ms": det_ms+palavras_ms+ms, "config": asdict(cfg)}


def medir(ouro, pred):
    return {nome: anterior.emparelhar(ouro, pred, lim, regua)[0] for nome, (regua, lim) in REGUAS.items()}


def sintetizar(registros, B):
    out = {"n": len(registros), "metricas": {}}
    for nome in REGUAS:
        cont = [r["contagens"][nome] for r in registros]
        total = np.array(cont).sum(axis=0)
        out["metricas"][nome] = {"contagens": total.tolist(), "f1": float(anterior.f1(total)),
                                  "ic95": anterior.intervalo(cont, B),
                                  "macro": float(np.mean(anterior.f1(cont)))}
    tempos = [r["tempo_ms"] for r in registros]
    out["tempo_ms"] = {"media": float(np.mean(tempos)), "mediana": float(np.median(tempos)),
                        "p95": float(np.percentile(tempos, 95))}
    out["pos_ms"] = float(np.mean([r.get("pos_ms", 0) for r in registros]))
    out["stats"] = dict(sum((Counter(r.get("stats", {})) for r in registros), Counter()))
    return out


def grade_configs():
    # Definida antes de medir; so se pode elevar conf pois cache original corta em .25.
    return [Config(base=b, score=s, folga=f, contencao=k)
            for b in ("ls3", "ls16", "uniao") for s in (.25, .45, .65)
            for f in (0., .5, 1.) for k in (.9, .98, 1.)]


def avaliar_config(ctx, cfg, assinatura, do_zero=False):
    chave = anterior.sha(asdict(cfg))[:16]
    caminho = CACHE / "grade" / (chave+".json")
    sig = anterior.sha([assinatura, asdict(cfg)])
    cache = None if do_zero else ler(caminho)
    registros = cache.get("registros", []) if cache and cache.get("assinatura") == sig else []
    for c in ctx[len(registros):]:
        pred = gerar(c, cfg)
        registros.append({"page_id": c["p"]["page_id"], "contagens": medir(c["p"]["ouro"], pred["caixas"]),
                          **{k: pred[k] for k in ("stats", "tempo_ms", "pos_ms")}})
        if len(registros) % 25 == 0 or len(registros) == len(ctx):
            salvar(caminho, {"assinatura": sig, "config": asdict(cfg), "registros": registros})
    assert [r["page_id"] for r in registros] == [c["p"]["page_id"] for c in ctx]
    return registros


def selecionar(ctx, configs, grades):
    """A selecao recebe somente os indices das OUTRAS fontes, por construcao."""
    fontes = sorted({c["p"]["fonte"] for c in ctx})
    arr = np.array([[r["contagens"]["loc50"] for r in rs] for rs in grades])
    arr75 = np.array([[r["contagens"]["loc75"] for r in rs] for rs in grades])
    folds, configs_pagina, registros = [], {}, []
    for fonte in fontes:
        train = np.array([i for i, c in enumerate(ctx) if c["p"]["fonte"] != fonte])
        test = np.array([i for i, c in enumerate(ctx) if c["p"]["fonte"] == fonte])
        f50, f75 = anterior.f1(arr[:, train].sum(axis=1)), anterior.f1(arr75[:, train].sum(axis=1))
        # Objetivo fixo: F1 micro loc50; desempate loc75, depois ordem da grade.
        j = max(range(len(configs)), key=lambda j: (f50[j], f75[j], -j))
        folds.append({"fonte": fonte, "train_n": len(train), "test_n": len(test),
                      "config": asdict(configs[j]), "f1_train": float(f50[j]), "indice_config": j})
        for i in test:
            configs_pagina[ctx[i]["p"]["page_id"]] = configs[j]
    for i, c in enumerate(ctx):
        cfg = configs_pagina[c["p"]["page_id"]]
        j = configs.index(cfg)
        registros.append(grades[j][i])
    return configs_pagina, registros, folds


def puro_validado(ctx):
    """Referencia justa: mesmo ajuste de score e selecao de base, sem regras v4."""
    candidatos = [(n, score) for n in ("ls3", "ls16") for score in (.25, .45, .65)]
    grades = []
    for nome, score in candidatos:
        grades.append([{"page_id": c["p"]["page_id"],
                        "contagens": medir(c["p"]["ouro"], [b for b in c["dados"][nome]["caixas"] if score_caixa(b) >= score]),
                        "tempo_ms": c["dados"][nome]["tempo_ms"], "base": nome, "score": score}
                       for c in ctx])
    arr = np.array([[r["contagens"]["loc50"] for r in rs] for rs in grades])
    arr75 = np.array([[r["contagens"]["loc75"] for r in rs] for rs in grades])
    escolhidos, folds = {}, []
    for fonte in sorted({c["p"]["fonte"] for c in ctx}):
        train = [i for i, c in enumerate(ctx) if c["p"]["fonte"] != fonte]
        test = [i for i, c in enumerate(ctx) if c["p"]["fonte"] == fonte]
        f50, f75 = anterior.f1(arr[:, train].sum(axis=1)), anterior.f1(arr75[:, train].sum(axis=1))
        j = max(range(len(candidatos)), key=lambda j: (f50[j], f75[j], -j))
        folds.append({"fonte": fonte, "base": candidatos[j][0], "score": candidatos[j][1]})
        for i in test:
            escolhidos[i] = grades[j][i]
    return [escolhidos[i] for i in range(len(ctx))], folds


def pareado(a, b, ctx, regua, B):
    x, y = np.array([r["contagens"][regua] for r in a]), np.array([r["contagens"][regua] for r in b])
    dif = anterior.f1(x)-anterior.f1(y)
    rng = np.random.default_rng(SEMENTE)
    ids = rng.integers(0, len(x), (B, len(x)))
    micro_boot = anterior.f1(x[ids].sum(axis=1))-anterior.f1(y[ids].sum(axis=1))
    macro_boot = dif[ids].mean(axis=1)
    # Sensibilidade ao agrupamento: reamostra FONTES inteiras, conservando paginas.
    fontes = sorted({c["p"]["fonte"] for c in ctx})
    por_fonte = [[i for i, c in enumerate(ctx) if c["p"]["fonte"] == f] for f in fontes]
    xf = np.array([x[ii].sum(axis=0) for ii in por_fonte])
    yf = np.array([y[ii].sum(axis=0) for ii in por_fonte])
    fi = rng.integers(0, len(fontes), (B, len(fontes)))
    boot_fonte = anterior.f1(xf[fi].sum(axis=1))-anterior.f1(yf[fi].sum(axis=1))
    medf = np.array([dif[ii].mean() for ii in por_fonte])
    return {"delta_micro": float(anterior.f1(x.sum(axis=0))-anterior.f1(y.sum(axis=0))),
            "ic95_micro": np.percentile(micro_boot, [2.5, 97.5]).tolist(),
            "delta_macro": float(dif.mean()), "ic95_macro": np.percentile(macro_boot, [2.5, 97.5]).tolist(),
            "ic95_fontes": np.percentile(boot_fonte, [2.5, 97.5]).tolist(),
            "p": float(wilcoxon(dif, zero_method="wilcox").pvalue) if np.any(np.abs(dif) > 1e-12) else 1.,
            "p_fontes": float(wilcoxon(medf).pvalue) if np.any(np.abs(medf) > 1e-12) else 1.,
            "ganha": int(sum(dif > 1e-12)), "empata": int(sum(np.abs(dif) <= 1e-12)), "perde": int(sum(dif < -1e-12))}


def autoteste():
    # Levenshtein contra programacao dinamica independente, incluindo Unicode.
    rng = random.Random(SEMENTE)
    def lenta(a, b):
        linha = list(range(len(b)+1))
        for i, c in enumerate(a, 1):
            nova = [i]
            for j, d in enumerate(b, 1):
                nova.append(min(nova[-1]+1, linha[j]+1, linha[j-1]+(c != d)))
            linha = nova
        return linha[-1]
    n = 0
    for _ in range(300):
        a = "".join(rng.choices("abç õ", k=rng.randrange(30)))
        b = "".join(rng.choices("abç õ", k=rng.randrange(30)))
        assert distancia(a, b) == lenta(a, b), (a, b)
        n += 1
    w = [{"t": "teste", "x0": 1., "x1": 11., "top": 2., "bottom": 10., "s": 0},
         {"t": "órfã", "x0": 1., "x1": 12., "top": 30., "bottom": 38., "s": 1}]
    det = {"ls3": [{"id": "a", "bbox": [0, 0, 14, 14], "classe": "texto", "score": .9}],
           "ls16": [{"id": "b", "bbox": [0, 0, 14, 14], "classe": "header", "score": .9}]}
    pred, stats, _ = propor_v4(w, det)
    assert pred[0]["classe"] == "header" and pred[0]["bbox"] == [1., 2., 11., 10.]
    assert stats["novas"] == 1 and stats["orfas_finais"] == 0
    assert len([b for b in pred if b["texto"]]) == 2
    assert len(propor_v4([], det)[0]) == 1
    assert not propor_v4([], det, replace(PADRAO, sem_texto=False))[0]
    caixas = [{"bbox": [0, 0, 10, 10], "classe": "paragraph", "score": .9},
              {"bbox": [2, 2, 8, 8], "classe": "paragraph", "score": .8},
              {"bbox": [8, 0, 18, 10], "classe": "paragraph", "score": .9}]
    res, st = resolver_conflitos(caixas, .98)
    assert len(res) == 2 and st["suprimidas"] == 1 and intersecao(res[0]["bbox"], res[1]["bbox"]) == 0
    tab = {"ls3": [{"bbox": [0, 0, 20, 20], "classe": "tabela", "score": .9}]}
    assert propor_v4(w[:1], tab, replace(PADRAO, base="ls3"))[0][0]["bbox"] == [0, 0, 20, 20]
    assert det["ls3"][0]["bbox"] == [0, 0, 14, 14], "Entrada foi mutada"
    assert score_caixa({"score": None}) == 1. and score_caixa({}) == 1.
    # Uma palavra no canto retirado por corte deve ganhar uma caixa disjunta.
    canto = [{"t": "canto", "x0": 7., "x1": 9., "top": 1., "bottom": 3., "s": 0}]
    recuperadas, novas = recuperar_apos_cortes(canto, [{"bbox": [0, 4, 10, 10], "classe": "paragraph"}])
    assert novas == 1 and matriz_centros(canto, recuperadas).any()
    assert intersecao(recuperadas[0]["bbox"], recuperadas[1]["bbox"]) == 0
    assert sum(area(p) for p in subtrair_retangulo([0,0,10,10],[2,2,8,8])) == 64
    # Mudar exclusivamente o ouro da fonte avaliada nao pode mudar seu parametro.
    ctx = [{"p": {"fonte": f, "page_id": str(i)}} for i, f in enumerate(("a", "a", "b", "c"))]
    configs = [PADRAO, replace(PADRAO, score=.65)]
    grades = [[{"page_id": str(i), "contagens": {"loc50": [3, 1, 1], "loc75": [2, 2, 2]}} for i in range(4)],
              [{"page_id": str(i), "contagens": {"loc50": [2, 2, 2], "loc75": [2, 2, 2]}} for i in range(4)]]
    antes = selecionar(ctx, configs, grades)[0]
    for i in (0, 1):
        grades[0][i]["contagens"]["loc50"] = [0, 50, 50]
        grades[1][i]["contagens"]["loc50"] = [50, 0, 0]
    depois = selecionar(ctx, configs, grades)[0]
    assert antes["0"] == depois["0"] and antes["1"] == depois["1"], "Vazamento da fonte excluida"
    print(f"AUTOTESTE: {n} pares de texto e casos de geometria/etapas aprovados", flush=True)


def diagnosticar(ctx, preds):
    """Erros e texto em pares globais; origens nunca entram no processamento."""
    origens = defaultdict(Counter)
    classes = defaultdict(Counter)
    textos, exemplos = [], []
    tipos = defaultdict(list)
    confusoes = Counter()
    cobertura = Counter()
    for i, c in enumerate(ctx):
        p, pred, gold = c["p"], preds[i]["caixas"], c["p"]["ouro"]
        cont, pares = anterior.emparelhar(gold, pred, .5)
        _, pares3 = anterior.emparelhar(gold, pred, .5, 3)
        _, pares16 = anterior.emparelhar(gold, pred, .5, 16)
        achadas = {j for j, _, _ in pares}
        achadas3 = {j for j, _, _ in pares3}
        achadas16 = {j for j, _, _ in pares16}
        for j, b in enumerate(gold):
            origens[b.get("origem", "ausente")].update(n=1, tp=j in achadas)
            if macroclasse(b["classe"]) is not None:
                origens[b.get("origem", "ausente")].update(n3=1, tp3=j in achadas3)
            classes[b["classe"]].update(n=1, tp=j in achadas, tp16=j in achadas16, perdidas=j not in achadas)
        for j, k, _ in pares:
            if gold[j]["classe"] != pred[k]["classe"]:
                confusoes[gold[j]["classe"]+" → "+pred[k]["classe"]] += 1
            ref, txt = normalizar_espacos(gold[j].get("texto")), normalizar_espacos(pred[k].get("texto"))
            cobertura["pares"] += 1
            if not ref:
                cobertura["ouro_vazio"] += 1
                continue
            cobertura["comparaveis"] += 1
            cobertura["pred_vazio"] += not bool(txt)
            erro = distancia(ref, txt)/len(ref)
            textos.append({"page_id": p["page_id"], "ouro_id": gold[j]["id"], "classe": gold[j]["classe"],
                           "cer": erro, "identico": ref == txt, "nchar": len(ref), "sem_texto": c["sem_texto"]})
        labels = ["sem camada" if c["sem_texto"] else "com camada"]
        labels += ["com tabela"] if any(b["classe"] == "table" for b in gold) else ["sem tabela"]
        labels += ["com imagem/rubrica"] if any(macroclasse(b["classe"]) == "imagem" for b in gold) else ["sem imagem/rubrica"]
        for label in labels:
            tipos[label].append(i)
        puro_cont = medir(gold, c["dados"]["ls3"]["caixas"])["loc50"]
        exemplos.append({"i": i, "page_id": p["page_id"], "fonte": p["fonte"],
                         "delta": float(anterior.f1(cont)-anterior.f1(puro_cont)),
                         "f1": float(anterior.f1(cont)), "perdidas": [j for j in range(len(gold)) if j not in achadas]})
    def resumo_texto(rs):
        return {"n": len(rs), "cer_mediana": float(np.median([r["cer"] for r in rs])) if rs else None,
                "identico": float(np.mean([r["identico"] for r in rs])) if rs else None,
                "cer_p90": float(np.percentile([r["cer"] for r in rs], 90)) if rs else None}
    texto = {"total": resumo_texto(textos), "com_camada": resumo_texto([r for r in textos if not r["sem_texto"]]),
             "sem_camada": resumo_texto([r for r in textos if r["sem_texto"]]), "cobertura": dict(cobertura),
             "por_classe": {cl: resumo_texto([r for r in textos if r["classe"] == cl]) for cl in GUIA}}
    selecionados, fontes = [], set()
    for ex in sorted(exemplos, key=lambda x: (x["delta"], x["f1"], x["page_id"])):
        if ex["fonte"] not in fontes and ex["perdidas"]:
            selecionados.append(ex)
            fontes.add(ex["fonte"])
        if len(selecionados) == 5:
            break
    return {"origens": {k: dict(v) for k, v in origens.items()}, "classes": {k: dict(v) for k, v in classes.items()},
            "confusoes": dict(confusoes.most_common(12)), "texto": texto,
            "tipos": dict(tipos), "exemplos": selecionados, "texto_pares": textos}


def exemplos_imagens(ctx, preds, diag):
    from PIL import Image, ImageDraw
    for ex in diag["exemplos"]:
        c = ctx[ex["i"]]
        p = c["p"]
        caminho = CACHE / "exemplos" / (anterior.chave(p)+".jpg")
        with Image.open(RAIZ / "data/deteccao/ls16/images/test" / p["img"]) as im:
            im = im.convert("RGB")
        desenho = ImageDraw.Draw(im)
        for boxes, cor in ((p["ouro"], "#199447"), (preds[ex["i"]]["caixas"], "#df3030")):
            for b in boxes:
                desenho.rectangle(b["bbox"], outline=cor, width=3)
        im.thumbnail((1000, 1500))
        caminho.parent.mkdir(parents=True, exist_ok=True)
        im.save(caminho, quality=82)
        ex["imagem"] = str(caminho.relative_to(RELATORIO.parent)).replace("\\", "/")
        j = ex["perdidas"][0]
        gold = p["ouro"][j]
        ious = anterior.matriz_iou([gold], preds[ex["i"]]["caixas"])
        ex["caixa"] = {"id": gold["id"], "classe": gold["classe"], "origem": gold["origem"],
                       "trecho": normalizar_espacos(gold["texto"])[:160],
                       "maior_iou": float(ious.max()) if ious.size else 0.}


def avaliar_diamond(cfg):
    from src.eval.avaliar_diamond import medir_pagina, resumir
    from src.data import regioes
    from orquestracao.analises.extrator_hibrido_ls import para9, para3
    tarefas = {t["page_id"]: t for t in anterior.jsonl(RAIZ / "data/diamond/diamond_teste/tarefas.jsonl")}
    ouro = {a["page_id"]: a for a in anterior.jsonl(RAIZ / "data/diamond/diamond_teste/anotacoes.jsonl")
            if a.get("status") == "concluida" and not str(a.get("anotador", "")).startswith("VLM:")}
    assert len(ouro) == 11
    det = {n: {t["page_id"]: t["regioes"] for t in anterior.jsonl(RAIZ / f"resultados/deteccao/pred_{n}_diamond_teste.jsonl")}
           for n in ("ls3", "ls16")}
    totais, registros = defaultdict(Counter), defaultdict(list)
    for pid in sorted(ouro):
        t = tarefas[pid]
        ws = [{"t": w[0], "x0": w[1], "top": w[2], "x1": w[3], "bottom": w[4], "s": i}
              for i, w in enumerate(t["palavras"])]
        detectores = {n: det[n][pid] for n in det}
        pred_padrao = propor_v4(ws, detectores, PADRAO)[0]
        pred_val = propor_v4(ws, detectores, cfg)[0]
        sistemas = {"extrator": regioes.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True),
                    "ls3": det["ls3"][pid], "ls16": det["ls16"][pid],
                    "v4_padrao": pred_padrao, "v4_validacao_ls": pred_val}
        for regua, mapa in (("9", para9), ("3", para3)):
            for nome, pred in sistemas.items():
                g = [{**b, "classe": mapa(b["classe"])} for b in ouro[pid]["regioes"]]
                pp = [{**b, "classe": mapa(b["classe"])} for b in pred]
                m = medir_pagina(t["palavras"], g, pp)
                totais[regua+"/"+nome].update(m)
                registros[regua+"/"+nome].append({"page_id": pid, "medidas": dict(m)})
    out = {"n": len(ouro), "config_validacao_ls": asdict(cfg),
           "sistemas": {k: resumir(v) for k, v in totais.items()}, "registros": dict(registros)}
    assert out["sistemas"]["9/extrator"]["f1_j50"] == .851, "Baseline Diamond divergiu"
    salvar(CACHE / "diamond.json", out)
    return out


def prever_kaggle(ctx, threads):
    import torch
    from ultralytics import RTDETR
    from PIL import Image
    torch.set_num_threads(threads)
    nome = "ls16_rtdetr_l_1024"
    peso = RAIZ / f"models/detector_ls/{nome}/best.pt"
    sig_modelo = anterior.sha([hashlib.sha256(peso.read_bytes()).hexdigest(), "cpu", 1024, .25, .7, 300])
    modelo, resultados = None, []
    for i, c in enumerate(ctx):
        p = c["p"]
        caminho = CACHE / "kaggle" / (anterior.chave(p)+".json")
        assinatura = anterior.sha([p["entrada_id"], sig_modelo])
        cache = ler(caminho)
        if not cache or cache.get("assinatura") != assinatura:
            if modelo is None:
                modelo = RTDETR(str(peso)).to("cpu")
                assert set(modelo.names.values()) == set(GUIA)
                modelo.predict(Image.new("RGB", (1024, 1024), "white"), device="cpu", imgsz=1024,
                               conf=.25, iou=.7, max_det=300, verbose=False, save=False)
            t = time.perf_counter()
            r = modelo.predict(str(RAIZ / "data/deteccao/ls16/images/test" / p["img"]), device="cpu", imgsz=1024,
                               conf=.25, iou=.7, max_det=300, verbose=False, save=False)[0]
            ms = (time.perf_counter()-t)*1000
            boxes = [{"id": str(k), "bbox": list(map(float, bb)), "classe": modelo.names[int(cid)], "score": float(score)}
                     for k, (bb, cid, score) in enumerate(zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()))]
            cache = {"assinatura": assinatura, "caixas": boxes, "tempo_ms": ms, "dispositivo": "cpu"}
            salvar(caminho, cache)
        c["dados"][nome] = cache
        c["detectores"][nome] = [{**b, "bbox": [b["bbox"][0]/c["sx"], b["bbox"][1]/c["sy"],
                                                b["bbox"][2]/c["sx"], b["bbox"][3]/c["sy"]]} for b in cache["caixas"]]
        resultados.append({"page_id": p["page_id"], "contagens": medir(p["ouro"], cache["caixas"]), "tempo_ms": cache["tempo_ms"]})
        if (i+1) % 10 == 0 or i+1 == len(ctx):
            print(f"KAGGLE CPU: {i+1}/{len(ctx)}", flush=True)
    return resultados


def tabela(sistemas, nomes=None, ic=True):
    linhas = ["| Sistema | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 16 classes 0,50 | 16 classes 0,75 | ms/página |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for nome in nomes or list(sistemas):
        s = sistemas[nome]
        valores = []
        for r in REGUAS:
            m = s["metricas"][r]
            if (nome == "ls3" or s.get("sem_classes16")) and r.startswith("c16"):
                valores.append("—")
            else:
                valores.append(anterior.ic_texto(m["f1"], m["ic95"]) if ic else numero(m["f1"]))
        linhas.append("| "+" | ".join([nome, *valores, numero(s["tempo_ms"]["media"], 1)])+" |")
    return linhas


def escrever_relatorio(r):
    s = r["sistemas"]
    principal = "v4_cv" if "v4_cv" in s else "v4_padrao"
    f = lambda nome, regua="loc50": s[nome]["metricas"][regua]["f1"]
    ganho, vs_puro = f(principal)-f("extrator"), f(principal)-f("ls3")
    veredito = "supera" if vs_puro > 0 else "perde para" if vs_puro < 0 else "empata com"
    linhas = ["# Extrator v4 — detector do domínio e palavras do PDF", "",
              f"1. **Veredito:** {principal} melhora a localização sobre o extrator atual em {numero(ganho)} ({numero(100*ganho, 1)} pontos percentuais); {veredito} o ls3 puro por {numero(abs(vs_puro))}.",
              f"2. F1 de localização IoU ≥ 0,50: extrator {numero(f('extrator'))}; ls3 {numero(f('ls3'))}; ls16 {numero(f('ls16'))}; {principal} {numero(f(principal))}.",
              f"3. Universo congelado: {r['n']} páginas, {r['fontes']} fontes nominais, {r['ouro_n']} caixas; {r['sem_texto']} páginas sem camada digital.",
              f"4. Limiar padrão e ajuste por fonte são separados; estado desta execução: **{r['estado']}**.",
              "5. Ouro corrigido de pré-anotação carrega ancoragem; a convenção do guia difere do Diamond do autor. Uso exclusivamente interno do parceiro Data Policy.", "",
              "## Tabela principal", "", "F1 micro por caixa. IC 95% por bootstrap de páginas entre colchetes. Os tempos reutilizam custos medidos nos caches de insumo e acrescentam o processamento v4 medido nesta execução.", ""]
    principais = [n for n in ("extrator", "ls3", "ls16", "puro_cv", "v4_padrao", "v4_cv") if n in s]
    linhas += tabela(s, principais)
    linhas += ["", "O ls3 puro não possui 16 classes: a coluna correspondente fica sem número. O extrator atual e as caixas v4 sem par ls16 usam rótulos representativos do mapa do projeto (texto→paragraph, tabela→table, imagem→figure); o F1 fino desses sistemas é uma projeção limitada, não um classificador das 16 funções.", "",
               "## Protocolo, parâmetros e validação por fonte", "",
               "Mesma régua de extrator_vs_detector_ls.py: emparelhamento bipartido 1–1 que maximiza primeiro TP e depois IoU; TP/FP/FN somados antes do F1. unknown fica fora somente da régua 3 classes. Nenhuma transcrição, origem ou caixa humana entra na produção das regiões. As palavras e o índice da página são os insumos verificados e congelados do experimento anterior.", "",
               f"Configuração padrão: `{json.dumps(asdict(PADRAO), ensure_ascii=False, sort_keys=True)}`.", "",
               "A união preserva exclusivamente a localização do ls3 e associa classes ls16 por casamento 1–1 com IoU ≥ 0,50 e concordância em 3 classes; não acrescenta outra caixa ls16. Sem par usa o rótulo representativo. As caixas de texto ajustam-se ao envelope das palavras com centro dentro; tabela/imagem conservam a geometria nessa etapa. Órfãs passam pelo segmentador v3 em pontos, podendo ser anexadas quando a folga cabe no parâmetro e a união não atravessa outra caixa. Contenção suprime a caixa menor; interseções restantes recebem um corte x/y com menor perda de área. Palavras expulsas de cantos por um corte recebem caixas com subtração retangular exata das caixas já presentes, sem reintroduzir sobreposição. Cada palavra alfanumérica visível tem um único proprietário explícito com c+d ligadas, inclusive na borda do corte; separadores sem letras/dígitos seguem o descarte v3.", "",
               f"O recorte visível do raster é respeitado: {r['palavras_fora_recorte']} tokens cujos centros estão fora dele não entram no v4. As caixas finais são limitadas às dimensões da imagem, como as propostas do extrator anterior; a transformação pontos→pixels conserva a origem do CropBox.", "",
               "Parâmetros fixos herdados do v3 não foram reaprendidos: critérios de linhas, calhas e parágrafos. Também são fixos o IoU de associação de classes, a concordância em 3 classes e a regra de corte com menor área perdida. São padrões estruturais predefinidos, não limiares escolhidos no ouro. A grade de ajuste eleva score mínimo {0,25; 0,45; 0,65}, testa folga {0; 0,5; 1} altura de palavra, contenção {0,90; 0,98; 1,00} e base {ls3; ls16; união}. Como o cache corta em 0,25, não é possível pesquisar scores menores sem nova inferência.", ""]
    if "folds" in r:
        linhas += [f"Grade predefinida com {r['grade_n']} configurações. Para cada fonte, os parâmetros e a base são escolhidos apenas nas outras fontes por F1 micro de localização 0,50 (desempate por localização 0,75 e ordem fixa da grade). As predições fora da fonte são concatenadas antes de medir v4_cv. A ablação retira uma etapa usando os mesmos parâmetros escolhidos para o v4 completo, sem novo ajuste.", "",
                   "| Configuração escolhida | Fontes |", "|---|---:|"]
        escolhas = Counter(json.dumps(fold["config"], sort_keys=True) for fold in r["folds"])
        for cfg, n in escolhas.most_common():
            c = json.loads(cfg)
            linhas.append(f"| {c['base']}; score {numero(c['score'],2)}; folga {numero(c['folga'],2)}; contenção {numero(c['contencao'],2)} | {n} |")
        linhas += ["", "O teste original vira um conjunto de desenvolvimento com validação cruzada de pós-processamento. Isso evita ajustar na fonte avaliada, mas não cria um novo teste independente: a proposta de regras conhece o domínio e a comparação anterior. Não se ajustou na convenção Diamond."]
    if "folds_puro" in r:
        escolhas_puro = Counter((f["base"], f["score"]) for f in r["folds_puro"])
        delta = f("v4_cv")-f("puro_cv")
        linhas += ["", "Controle do efeito do score: puro_cv escolhe entre ls3/ls16 e scores {0,25; 0,45; 0,65} nas outras fontes, pela mesma função objetivo do v4. Assim o detector recebe a mesma oportunidade de reduzir falsos positivos, sem ajuste de geometria nem recuperação de órfãs.",
                   "Escolhas do puro_cv: "+"; ".join(f"{base}, score {numero(score,2)}: {n} fontes" for (base, score), n in escolhas_puro.most_common())+".",
                   f"Contra esse controle ajustado, Δ localização v4_cv−puro_cv = **{numero(delta)}**. Este é o contraste adequado para atribuir ganho adicional às regras, além da comparação pedida com detectores padrão."]
    auditoria = r.get("auditoria_split") or {}
    linhas += ["", f"Auditoria nominal preservada: {len(auditoria.get('paginas_afetadas', []))} página(s) com alias confirmado entre teste e treino/validação (pag df↔df). A divisão não foi alterada. IC de páginas pode ser otimista por dependência intrafonte e por compartilhar os conjuntos de ajuste dos folds.", ""]
    if "pareados" in r:
        linhas += ["## Teste pareado", "", "Diferença v4_cv−comparador; Wilcoxon bilateral sobre F1 por página, sem arredondar. IC micro é bootstrap pareado de páginas. A coluna por fontes reamostra fontes inteiras como análise de sensibilidade, sem reaprender parâmetros em cada bootstrap.", "",
                   "| Comparador / régua | Δ micro [IC páginas] | IC por fontes | Δ médio por página | p páginas | p fontes | Ganha/empata/perde |",
                   "|---|---:|---:|---:|---:|---:|---:|"]
        for chave, d in r["pareados"].items():
            linhas.append(f"| {chave} | {anterior.ic_texto(d['delta_micro'],d['ic95_micro'])} | [{numero(d['ic95_fontes'][0])}; {numero(d['ic95_fontes'][1])}] | {anterior.ic_texto(d['delta_macro'],d['ic95_macro'])} | {probabilidade(d['p'])} | {probabilidade(d['p_fontes'])} | {d['ganha']}/{d['empata']}/{d['perde']} |")
        linhas += ["", "O melhor detector puro com limiares padrão é ls3, escolhido na comparação anterior e conservado como referência fixa. O controle puro_cv escolhe a base e o score somente nas fontes de ajuste. Os p são exploratórios e não corrigidos por múltiplas comparações. A reutilização do teste para desenvolver regras e os folds correlacionados limitam qualquer leitura confirmatória.", ""]
    linhas += ["## Bases e ablação", "", "As bases padrão usam as mesmas etapas e limiares, sem ajuste. As linhas cv_base repetem a escolha de parâmetros nas outras fontes, restringindo a grade àquela base. As ablações cv conservam a escolha da base e dos limiares do fold completo. Sem a: somente agrupamento de palavras órfãs por v3. Sem f: descarta páginas sem palavras. Sem e: geometria idêntica, mas nenhuma transcrição é entregue.", ""]
    linhas += tabela(s, [n for n in s if n.startswith("v4_") and n not in principais and not n.startswith("v4_kaggle")], False)
    if "diagnosticos" in r:
        linhas += ["", "## Qualidade do texto", "",
                   "Pares de localização IoU ≥ 0,50, independentemente de classe. CER = distância Levenshtein em caracteres / caracteres da transcrição humana, podendo ultrapassar 1. Somente espaços são normalizados; caixa, acentos, pontuação e hífens são preservados. Texto lido por linha e da esquerda para a direita, sem OCR e sem reconstrução de células de tabela. Ouro sem transcrição não tem CER e é contado à parte. Esta análise está condicionada às caixas que cada sistema consegue localizar.", "",
                   "| Sistema | Pares | Ouro vazio | Pares comparáveis | Predição vazia | CER mediana | CER p90 | Texto idêntico |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for nome, diag in r["diagnosticos"].items():
            tx, co = diag["texto"]["total"], diag["texto"]["cobertura"]
            linhas.append(f"| {nome} | {co.get('pares',0)} | {co.get('ouro_vazio',0)} | {tx['n']} | {co.get('pred_vazio',0)} | {numero(tx['cer_mediana'])} | {numero(tx['cer_p90'])} | {numero(100*tx['identico'],1) if tx['identico'] is not None else '—'}% |")
        linhas += ["", "Para os detectores puros e o extrator atual, o texto desta tabela é uma leitura diagnóstica adicional da mesma camada PDF nas caixas congeladas, sem exclusividade entre caixas; não é saída originalmente entregue pelos detectores. O v4 efetivamente entrega texto e propriedade das palavras. Isso permite distinguir qualidade de localização e efeitos do ajuste/exclusividade na transcrição."]
        diag = r["diagnosticos"][principal]
        linhas += ["", "| Classe no ouro (v4_cv) | Pares com transcrição | CER mediana | Texto idêntico |", "|---|---:|---:|---:|"]
        for cl, tx in diag["texto"]["por_classe"].items():
            if tx["n"]:
                linhas.append(f"| {cl} | {tx['n']} | {numero(tx['cer_mediana'])} | {numero(100*tx['identico'],1)}% |")
        co = diag["texto"]["sem_camada"]
        linhas += ["", f"Sem camada digital: {co['n']} pares com transcrição humana não vazia, CER mediana {numero(co['cer_mediana'])}; nessas páginas o v4 entrega somente caixas e texto vazio. Não confundir vazio correto em imagem com transcrição recuperada.", "",
                   "## Revocação por origem da caixa do ouro", "", "Casamento global antes do estrato; nenhuma predição pode acertar duas caixas de origens distintas. Origem é o campo labels com fallback para rectangle, preservado pelo cache anterior.", "",
                   "| Sistema | Origem | Ouro loc | Revocação loc50 | Ouro 3 classes | Revocação 3 classes |", "|---|---|---:|---:|---:|---:|"]
        for nome, dd in r["diagnosticos"].items():
            for origem in anterior.ORIGENS:
                v = dd["origens"].get(origem, {})
                n, n3 = v.get("n",0), v.get("n3",0)
                linhas.append(f"| {nome} | {origem} | {n} | {numero(v.get('tp',0)/n) if n else '—'} | {n3} | {numero(v.get('tp3',0)/n3) if n3 else '—'} |")
        linhas += ["", "## Onde ainda erra", "", "Perdas são caixas humanas sem par de localização. Revocação fina exige classe igual. Os tipos de página se sobrepõem, e suas contagens não devem ser somadas.", "",
                   "| Classe humana | Caixas | Perdidas loc | Revocação loc50 v4 | Revocação loc50 ls3 | Revocação fina v4 |", "|---|---:|---:|---:|---:|---:|---:|"]
        for cl, cc in sorted(diag["classes"].items(), key=lambda item: -item[1]["perdidas"]):
            puro = r["diagnosticos"]["ls3"]["classes"][cl]
            linhas.append(f"| {cl} | {cc['n']} | {cc['perdidas']} | {numero(cc['tp']/cc['n'])} | {numero(puro['tp']/puro['n'])} | {numero(cc['tp16']/cc['n'])} |")
        linhas += ["", "| Tipo de página | Páginas | Extrator loc50 | ls3 loc50 | v4_cv loc50 | Δ v4−ls3 |", "|---|---:|---:|---:|---:|---:|"]
        for tipo, st in r["estratos"].items():
            linhas.append(f"| {tipo} | {st['n']} | {numero(st['extrator'])} | {numero(st['ls3'])} | {numero(st[principal])} | {numero(st[principal]-st['ls3'])} |")
        linhas += ["", "Confusões de classe nos pares já localizados: "+"; ".join(f"{cl}: {n}" for cl, n in diag["confusoes"].items())+".", "",
                   "Exemplos adversos selecionados automaticamente pelas maiores perdas por página contra ls3, em fontes distintas; não representam a frequência do erro. Verde: ouro; vermelho: v4.", ""]
        for ex in diag["exemplos"]:
            bb = ex["caixa"]
            linhas.append(f"- **{ex['fonte']}**, `{ex['page_id']}`: F1 loc50 {numero(ex['f1'])}, Δ ls3 {numero(ex['delta'])}. Caixa {bb['id']} ({bb['classe']}, {bb['origem']}) sem par; maior IoU {numero(bb['maior_iou'])}; trecho “{bb['trecho']}”. [Inspeção interna]({ex['imagem']}).")
        stats = s[principal]["stats"]
        linhas += ["", f"Diagnóstico do processamento: {stats.get('orfas_iniciais',0)} palavras órfãs após ajuste; {stats.get('novas',0)} caixas criadas nessa etapa; {stats.get('anexadas',0)} palavras anexadas; {stats.get('suprimidas',0)} caixas suprimidas; {stats.get('cortes',0)} cortes; {stats.get('novas_pos_corte',0)} caixas adicionais recuperam cantos expulsos pelos cortes. Terminam sem caixa {stats.get('orfas_finais',0)} tokens, dos quais {stats.get('orfas_alfanum',0)} são alfanuméricos; {stats.get('duplicadas',0)} atribuições duplicadas.", "",
                   "Leitura das oportunidades: detector maior só rende se melhorar localização na mesma régua, não basta mAP anunciado. O desnível entre localização e F1 fino e as confusões acima justificam testar classificação por texto para funções como act, id e signature. A ablação decide o valor das regras: envelope obrigatório pode retirar margens que fazem parte da convenção; órfãs aumentam cobertura textual e também falsos positivos; contenção pode apagar regiões legítimas sobrepostas. O próximo teste deve medir essas hipóteses em páginas independentes anotadas do zero.", ""]
        abls = [n for n in s if n.startswith("v4_cv_sem_")]
        melhor_abl = max(abls, key=lambda n: f(n))
        melhor75 = max(abls, key=lambda n: f(n,"loc75"))
        linhas += [f"Evidência para priorizar regras: {melhor_abl} dá F1 loc50 {numero(f(melhor_abl))}, Δ {numero(f(melhor_abl)-f(principal))} contra o completo; {melhor75} dá loc75 {numero(f(melhor75,'loc75'))}, Δ {numero(f(melhor75,'loc75')-f(principal,'loc75'))}. Estes resultados são ablações exploratórias, não uma nova configuração selecionada em teste independente.", ""]
    if "diamond" in r:
        d = r["diamond"]
        linhas += ["## Referência na convenção antiga: Diamond", "", f"{d['n']} páginas concluídas por humano; régua importada de src/eval/avaliar_diamond.py. É Jaccard dos conjuntos de palavras por região, não IoU geométrico. Caixas sem palavras não contribuem a essa régua. A referência foi desenhada do zero pelo autor; isso reduz ancoragem, mas não remove subjetividade nem permite generalização com n pequeno.", "",
                   "| Sistema / régua | F1 Jaccard 0,50 | F1 Jaccard 0,90 | F1 com classe | Classe por palavra |", "|---|---:|---:|---:|---:|"]
        for chave, st in d["sistemas"].items():
            linhas.append(f"| {chave} | {numero(st['f1_j50'])} | {numero(st['f1_j90'])} | {numero(st['f1_j50_classe'])} | {numero(st['classe_certa_palavras'])} |")
        dv = d["sistemas"]["9/v4_validacao_ls"]["f1_j50"]-d["sistemas"]["9/extrator"]["f1_j50"]
        linhas += ["", f"Na régua antiga de 9 classes, v4 validado no LS muda {numero(dv)} frente ao extrator atual. Sua configuração foi escolhida em todas as páginas LS, nunca nas 11 Diamond: `{json.dumps(d['config_validacao_ls'],ensure_ascii=False,sort_keys=True)}`. O resultado confirma que granularidade e convenção são parte da tarefa; não se pode intercambiar os dois F1.", ""]
        linhas += ["O Diamond tampouco é teste intocado para o extrator antigo: a docstring de src/data/regioes.py registra que fundir_fragmentos foi calibrada no diamond_teste. A vantagem do antigo nesse lote mistura compatibilidade de convenção e adaptação prévia às páginas; não permite isolar causalmente esses fatores.", ""]
    if "kaggle" in r:
        linhas += ["## Detector maior do Kaggle (separado)", "", "RT-DETR L de 16 classes, checkpoint local, mesmo split; inferência integral em CPU a 1024 pixels, conf 0,25. Etapas v4 e limiares padrão fixos, sem seleção posterior. O modelo maior foi escolhido pelo mAP anunciado no próprio teste na nota do autor: seleção exploratória, não confirmação independente. O mAP não é comparado diretamente com F1 nesta tabela.", ""]
        linhas += tabela(r["kaggle"])
        kg = r["kaggle"]
        puro = kg["rtdetr_l_puro"]["metricas"]["loc50"]
        completo = kg["v4_kaggle_padrao"]
        fp = puro["contagens"][1]
        delta = completo["metricas"]["loc50"]["f1"]-f("v4_padrao")
        linhas += ["", f"O detector maior puro tem {fp} falsos positivos nessa régua e nesse score. O v4 suprime {completo['stats'].get('suprimidas',0)} caixas por contenção, além das outras etapas, e eleva seu F1 para {numero(completo['metricas']['loc50']['f1'])}. Contra o v4 padrão com união local, a localização muda {numero(delta)}; ainda fica abaixo do ls3 puro {numero(f('ls3'))}. O ganho é do conjunto de etapas, não uma ablação causal do detector maior ou da contenção isoladamente."]
    else:
        linhas += ["## Detector maior do Kaggle", "", "Ainda não avaliado nesta execução. --kaggle acrescenta RT-DETR L em CPU e guarda inferência por página para retomada."]
    ds = r["dataset"]
    linhas += ["", "## Limitações e tempo", "",
               f"Anotação corrigindo pré-anotação induz viés de ancoragem: até uma caixa manual é desenhada com sugestões visíveis. Origem não equivale a dificuldade e não permite concluir causalmente que um modelo herdou erros. A contagem incremental encontra {ds['paginas_convertidas']} páginas únicas nas conversões do parceiro e {ds['paginas_split']} no split de detecção, com {ds['fora_split']} fora do split (motivo não auditado aqui). A divisão contém {ds['particoes'].get('train',0)} páginas de treino, {ds['particoes'].get('val',0)} de validação e {ds['particoes'].get('test',0)} de teste. Este pós-processamento usa somente as {r['n']} páginas pedidas e os detectores existentes. Não houve novo treinamento nem uso das outras partições para ajustar regras.", "",
               "Poucas fontes e páginas por fonte tornam estimativas frágeis; há um alias nominal conhecido. O bootstrap principal reamostra páginas, não resolve dependência entre fontes ou seleção dos parâmetros. CER só nos pares localizados favorece cada sistema de maneira diferente. A camada PDF pode conter OCR embutido, falhas de Unicode ou texto parcial; não foi auditada palavra por palavra. A exclusividade de palavras não assegura cobertura total nem uma ordem humana dentro da região. Não medimos ordem entre regiões nem RI extrínseca.", "",
               "Latência de CPU inclui os custos congelados de inferência dos detectores e extração de palavras; união soma as duas inferências. A imagem raster LS já existe; produção a partir de PDF precisa acrescentar renderização. Custos do extrator atual incluem renderização/Docling do cache anterior. As tarefas concorrentes e as datas distintas impedem tratar estes números como benchmark controlado. Inicialização, leitura de cache, avaliação e escolha de parâmetros ficam fora; tempo de pós-processamento v4 é medido separadamente abaixo.", "",
               "| Sistema | Pós-processamento médio (ms) | Tempo total mediano (ms) | Tempo total p95 (ms) |", "|---|---:|---:|---:|"]
    for nome in principais:
        st = s[nome]
        linhas.append(f"| {nome} | {numero(st['pos_ms'],1)} | {numero(st['tempo_ms']['mediana'],1)} | {numero(st['tempo_ms']['p95'],1)} |")
    linhas += ["", "## Esqueleto para um módulo futuro em src/data/extrator_v4.py", "",
               "```python", "@dataclass(frozen=True)", "class ConfigV4:", "    base: str", "    score: float", "    folga_alturas: float", "    contencao: float", "    etapas: tuple[str, ...]", "",
               "def detectar(imagem, modelo_local, *, device='cpu'):", "    # Caixas em pixels e classes do guia; sem baixar pesos.", "    ...", "",
               "def propor_v4(palavras_pdf, detectores_em_pontos, config):", "    caixas = caixas_base(detectores_em_pontos, config)", "    # b: envelope; c: orfas v3; d: contencao/cortes e propriedade unica.", "    # e: texto da camada; f: detector sozinho quando nao ha palavras.", "    return caixas  # id, bbox, classe, score, texto, palavras_ids, origem_v4", "```", "",
               "A implementação funcional está no script desta análise; nenhum módulo src foi alterado. Configuração e convenção devem ser explícitas antes de qualquer adoção no TCC.", "",
               "## Reprodução e conferência", "", "```powershell",
               "venv/Scripts/python.exe orquestracao/analises/extrator_v4.py --autoteste",
               "venv/Scripts/python.exe orquestracao/analises/extrator_v4.py --do-zero --kaggle",
               "```", "",
               f"Bootstrap: {r['bootstrap']} reamostras, semente {SEMENTE}. Assinatura dos insumos e algoritmo: `{r['assinatura']}`. Execução do zero solicitada: {r['do_zero']}. --do-zero refaz a grade, a avaliação e os diagnósticos; conserva caches de palavras/PDF/detectores já autorizados. JSON verificável, configurações por fonte, métricas por página, predições com texto e exemplos ficam em resultados/extrator_v4_cache/. O relatório e sua tabela são conferidos pelo script contra o JSON de resultados. Derivados do parceiro não devem sair deste repositório."]
    conteudo = "\n".join(linhas)+"\n"
    tmp = RELATORIO.with_suffix(".md.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fobj:
        fobj.write(conteudo)
        fobj.flush()
        os.fsync(fobj.fileno())
    os.replace(tmp, RELATORIO)
    return conteudo


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--kaggle", action="store_true")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    autoteste()
    if args.autoteste:
        return
    ctx, assinatura = carregar()
    dataset = auditar_dataset()
    B = args.bootstrap
    dados, sistemas = {}, {}
    for nome in ("extrator", "ls3", "ls16"):
        rs = [{"page_id": c["p"]["page_id"], "contagens": medir(c["p"]["ouro"], c["dados"][nome]["caixas"]),
               "tempo_ms": c["dados"][nome]["tempo_ms"]} for c in ctx]
        dados[nome], sistemas[nome] = rs, sintetizar(rs, B)
    # Baselines sao reconstruidas da mesma predicao congelada, sem reexecutar modelos.
    esperadas = ler(anterior.CACHE / "metricas.json")
    for nome in ("extrator", "ls3", "ls16"):
        assert round(sistemas[nome]["metricas"]["loc50"]["f1"],3) == {"extrator": .573, "ls3": .780, "ls16": .753}[nome]
    padrao_rs = avaliar_config(ctx, PADRAO, assinatura, args.do_zero)
    dados["v4_padrao"], sistemas["v4_padrao"] = padrao_rs, sintetizar(padrao_rs, B)
    r = {"n": len(ctx), "fontes": len({c['p']['fonte'] for c in ctx}),
         "ouro_n": sum(len(c['p']['ouro']) for c in ctx), "sem_texto": sum(c['sem_texto'] for c in ctx),
         "palavras_fora_recorte": sum(c['palavras_fora_recorte'] for c in ctx),
         "assinatura": assinatura, "bootstrap": B, "do_zero": args.do_zero, "estado": "limiares padrão medidos; CV em andamento",
         "dataset": dataset,
         "sistemas": sistemas, "auditoria_split": ler(anterior.CACHE / "auditoria_split.json")}
    salvar(CACHE / "resultados.json", r)
    escrever_relatorio(r)
    print("PADRÃO MEDIDO; relatório inicial gravado", flush=True)
    print("\n".join(tabela(sistemas, ic=False)), flush=True)
    configs, grades = grade_configs(), []
    for i, cfg in enumerate(configs):
        rs = padrao_rs if cfg == PADRAO else avaliar_config(ctx, cfg, assinatura, args.do_zero)
        grades.append(rs)
        if (i+1) % 9 == 0:
            print(f"GRADE: {i+1}/{len(configs)}", flush=True)
    cfg_pagina, cv_rs, folds = selecionar(ctx, configs, grades)
    dados["v4_cv"], sistemas["v4_cv"] = cv_rs, sintetizar(cv_rs, B)
    r.update(folds=folds, grade_n=len(configs), estado="CV concluída; diagnósticos em andamento")
    puro_rs, folds_puro = puro_validado(ctx)
    dados["puro_cv"], sistemas["puro_cv"] = puro_rs, sintetizar(puro_rs, B)
    sistemas["puro_cv"]["sem_classes16"] = any(rr["base"] == "ls3" for rr in puro_rs)
    r["folds_puro"] = folds_puro
    for base in ("ls3", "ls16"):
        nome = "v4_base_"+base+"_padrao"
        rs = grades[configs.index(replace(PADRAO, base=base))]
        dados[nome], sistemas[nome] = rs, sintetizar(rs, B)
    for base in ("ls3", "ls16", "uniao"):
        js = [j for j, cfg in enumerate(configs) if cfg.base == base]
        _, rs, _ = selecionar(ctx, [configs[j] for j in js], [grades[j] for j in js])
        nome = "v4_cv_base_"+base
        dados[nome], sistemas[nome] = rs, sintetizar(rs, B)
    preds_cv = [gerar(c, cfg_pagina[c["p"]["page_id"]]) for c in ctx]
    salvar(CACHE / "predicoes_cv.json", {"assinatura": assinatura, "paginas": [{"page_id": c["p"]["page_id"], **p} for c, p in zip(ctx, preds_cv)]})
    for nome, etapa in ABLACOES.items():
        rs, preds = [], []
        for c in ctx:
            cfg = replace(cfg_pagina[c["p"]["page_id"]], **{etapa: False})
            p = gerar(c, cfg)
            preds.append(p)
            rs.append({"page_id": c["p"]["page_id"], "contagens": medir(c["p"]["ouro"], p["caixas"]),
                       **{k: p[k] for k in ("stats", "tempo_ms", "pos_ms")}})
        dados["v4_cv_"+nome], sistemas["v4_cv_"+nome] = rs, sintetizar(rs, B)
        print("ABLAÇÃO: "+nome, flush=True)
        if etapa == "texto":
            assert all(a["contagens"] == b["contagens"] for a, b in zip(rs, cv_rs))
            assert all(not box["texto"] for p in preds for box in p["caixas"])
    r["pareados"] = {nome+"/"+regua: pareado(cv_rs, dados[nome], ctx, regua, B)
                     for nome in ("extrator", "ls3", "puro_cv") for regua in ("loc50", "c3_50")}
    diagnosticos = {}
    for nome in ("extrator", "ls3", "ls16", "puro_cv", "v4_padrao", "v4_cv"):
        if nome == "v4_cv":
            preds = preds_cv
        elif nome == "v4_padrao":
            preds = [gerar(c, PADRAO) for c in ctx]
        else:
            # Leitura diagnostica do PDF em caixas das baselines: nao altera suas regioes.
            preds = []
            for i, c in enumerate(ctx):
                base = puro_rs[i]["base"] if nome == "puro_cv" else nome
                score = puro_rs[i]["score"] if nome == "puro_cv" else 0.
                boxes = [{**b, "bbox": list(b["bbox"])} for b in c["dados"][base]["caixas"] if score_caixa(b) >= score]
                ws_px = [{**w, "x0": w["x0"]*c["sx"], "x1": w["x1"]*c["sx"],
                          "top": w["top"]*c["sy"], "bottom": w["bottom"]*c["sy"]} for w in c["ws"]]
                grupos = atribuir(ws_px, boxes, unica=False)
                for b, ii in zip(boxes, grupos):
                    b["texto"] = ler_texto([c["ws"][j] for j in ii])
                preds.append({"caixas": boxes})
        diagnosticos[nome] = diagnosticar(ctx, preds)
        print("DIAGNÓSTICO: "+nome, flush=True)
    exemplos_imagens(ctx, preds_cv, diagnosticos["v4_cv"])
    r["diagnosticos"] = diagnosticos
    r["estratos"] = {}
    for tipo, ii in diagnosticos["v4_cv"]["tipos"].items():
        r["estratos"][tipo] = {"n": len(ii), **{nome: float(anterior.f1(np.array([dados[nome][i]["contagens"]["loc50"] for i in ii]).sum(axis=0)))
                                               for nome in ("extrator", "ls3", "v4_cv")}}
    # Diamond nunca e usado para escolher qualquer parametro.
    melhor = max(range(len(configs)), key=lambda j: (float(anterior.f1(np.array([rr["contagens"]["loc50"] for rr in grades[j]]).sum(axis=0))),
                                                     float(anterior.f1(np.array([rr["contagens"]["loc75"] for rr in grades[j]]).sum(axis=0))), -j))
    r["diamond"] = avaliar_diamond(configs[melhor])
    r["estado"] = "avaliação local completa; detector Kaggle pendente" if args.kaggle else "completa (detectores locais)"
    r["registros"] = dados
    salvar(CACHE / "resultados.json", r)
    escrever_relatorio(r)
    print("RELATÓRIO LOCAL COMPLETO", flush=True)
    if args.kaggle:
        puro = prever_kaggle(ctx, args.threads)
        cfg = replace(PADRAO, base="ls16_rtdetr_l_1024")
        rs = avaliar_config(ctx, cfg, anterior.sha([assinatura, [c['dados'][cfg.base]['assinatura'] for c in ctx]]), args.do_zero)
        r["kaggle"] = {"rtdetr_l_puro": sintetizar(puro,B), "v4_kaggle_padrao": sintetizar(rs,B)}
        r["registros_kaggle"] = {"puro": puro, "v4": rs}
        for regua in ("loc50", "c3_50"):
            r["pareados"]["rtdetr_l_puro/"+regua] = pareado(cv_rs, puro, ctx, regua, B)
        r["estado"] = "completa (locais e RT-DETR L Kaggle)"
    salvar(CACHE / "resultados.json", r)
    conteudo = escrever_relatorio(r)
    # Conferencia do arquivo salvo contra a saida exata da tabela derivada do JSON.
    salvo = ler(CACHE / "resultados.json")
    esperado = "\n".join(tabela(salvo["sistemas"], ["extrator","ls3","ls16","puro_cv","v4_padrao","v4_cv"]))
    assert esperado in RELATORIO.read_text(encoding="utf-8")
    assert conteudo == RELATORIO.read_text(encoding="utf-8")
    assert sistemas["v4_cv"]["stats"].get("duplicadas", 0) == 0
    assert sistemas["v4_cv"]["stats"].get("orfas_alfanum", 0) == 0
    salvar(CACHE / "conferencia.json", {"assinatura": assinatura, "do_zero": args.do_zero,
                                       "tabela_bate_com_json": True, "relatorio_bate_com_saida": True,
                                       "n": len(ctx), "cv_fonte_excluida": len(folds), "autoteste": True})
    print("\n"+esperado, flush=True)
    print("CONFERÊNCIA: relatório = tabela da saída = resultados.json; propriedade única aprovada", flush=True)
    print("RELATÓRIO: resultados/extrator_v4.md", flush=True)


if __name__ == "__main__":
    main()
