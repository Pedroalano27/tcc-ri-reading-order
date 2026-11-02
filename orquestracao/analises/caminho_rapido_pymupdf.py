"""Mede um caminho digital sem redes para palavras, tabelas, imagens e ordem.

Usa PyMuPDF em CPU, sem OCR ou pymupdf_layout, e compara com palavras do
pdfplumber e Docling local. Mantem as escolhas LOPO do estudo anterior por
pagina. A regua principal e a sequencia real de palavras do Diamond; a troca
de atomos usa as mesmas palavras congeladas para isolar a deteccao.

Uso, da raiz: venv/Scripts/python.exe -B orquestracao/analises/caminho_rapido_pymupdf.py
--do-zero refaz todas as medicoes, preservando a verificacao da execucao anterior.
--conferir reconstrui o Markdown e verifica igualdade com os caches.
--sem-docling permite diagnosticar um ambiente sem pesos, declarando a ausencia.
Unicas saidas: resultados/caminho_rapido_pymupdf.md e caches/temporarios sob
resultados/caminho_rapido_pymupdf_cache/. Nao escreve nos dados ou fontes.
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
import inspect
import json
import math
import os
import random
import re
import statistics
import time
import unicodedata
from dataclasses import asdict
from importlib.metadata import version
from types import SimpleNamespace

import numpy as np
import pymupdf
from scipy.optimize import linear_sum_assignment
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import ordem_sem_bbox_justo as j
from src.data.extrator import palavras_da_pagina
from src.data.palavras_pymupdf import _matriz_pdfplumber
from src.data.taxonomia_layout import GUIA

BASE = RAIZ / "resultados/caminho_rapido_pymupdf_cache"
MD = RAIZ / "resultados/caminho_rapido_pymupdf.md"
SEMENTE = 20261003
NBOOT = 5000
NOMES = {"xy": "XY-cut ouro, pura†", "xy_margens": "XY-cut ouro + mesmas margens†",
         "docling": "Plano LOPO + átomos Docling", "rapido": "Plano LOPO + PyMuPDF conservador",
         "rapido_text": "Plano LOPO + PyMuPDF incluindo text", "nenhum": "Plano LOPO sem átomos"}
DET_NOMES = {"lines": "find_tables(lines)", "text": "find_tables(text)",
             "tracos": "Agrupamento de traços/retângulos", "raster": "Imagens incorporadas",
             "vetor": "Desenhos vetoriais grandes", "rapido": "PyMuPDF conservador",
             "rapido_text": "PyMuPDF conservador + text", "docling": "Docling congelado"}


def gravar(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        f.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, allow_nan=False))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def ler(path):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def jsonl(path):
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError as e:
                    raise ValueError(f"JSONL inválido: {path.name}, linha {n}") from e


def digest(path):
    return j.digest(path)


def chave(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def arquivo_cache(tipo, pid):
    return BASE / tipo / (chave(pid) + ".json")


def pdf_util(path):
    """Desembrulha PKCS#7; nunca regrava nem corta zeros dos PDFs originais."""
    with path.open("rb") as f:
        inicio = f.read(1024)
    if inicio.startswith(b"%PDF"):
        return path, False
    raw = path.read_bytes()
    ini, fim = raw.find(b"%PDF"), raw.rfind(b"%%EOF")
    if ini < 0 or fim < ini:
        raise ValueError("Arquivo sem trecho PDF completo")
    dest = BASE / "pdf_temporarios" / (digest(path) + ".pdf")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        with tmp.open("wb") as f:
            f.write(raw[ini:fim+5])
        os.replace(tmp, dest)
    return dest, True


def valido(b):
    return len(b) == 4 and all(math.isfinite(float(v)) for v in b) and o.area(b) > 0


def iou(a, b):
    inter = o.inter(a, b)
    return inter / max(1e-12, o.area(a) + o.area(b) - inter)


def bbox(b, matriz):
    return [float(v) for v in pymupdf.Rect(b) * matriz]


def palavras(page, sistema="visivel"):
    """words retorna CropBox nao girada; transforma explicitamente, sem adivinhar offsets."""
    mat = _matriz_pdfplumber(page) if sistema == "plumber" else page.rotation_matrix
    raw = page.get_text("words", sort=False)
    return [[str(w[4]), *bbox(w[:4], mat)] for w in raw if str(w[4]).strip() and valido(w[:4])]


def regiao(rotulo, b, fonte, **extras):
    return dict(rotulo=rotulo, bbox=[float(x) for x in b], score=1.0, fonte=fonte, **extras)


def nms(rs):
    """Suprime duplicatas da mesma classe; nunca funde tabelas adjacentes."""
    out = []
    for r in rs:
        if not valido(r.get("bbox", [])):
            continue
        if any(r["rotulo"] == m["rotulo"] and
               (iou(r["bbox"], m["bbox"]) >= .5 or
                o.inter(r["bbox"], m["bbox"]) >= .9 * min(o.area(r["bbox"]), o.area(m["bbox"])))
               for m in out):
            continue
        out.append(r)
    return out


def sinais(paths):
    """Conta segmentos ortogonais e curvas, inclusive retangulos finos preenchidos."""
    h, v, curves, diag, rects = [], [], 0, 0, 0
    for path in paths:
        for it in path.get("items", []):
            if it[0] == "l":
                a, b = it[1:3]
                if abs(a.y-b.y) <= 1 and abs(a.x-b.x) >= 8:
                    h.append((a.y+b.y)/2)
                elif abs(a.x-b.x) <= 1 and abs(a.y-b.y) >= 8:
                    v.append((a.x+b.x)/2)
                elif abs(a.x-b.x) > 2 and abs(a.y-b.y) > 2:
                    diag += 1
            elif it[0] == "c":
                curves += 1
            elif it[0] == "re":
                r = it[1]
                if r.width >= 8 and r.height <= 3:
                    h.append((r.y0+r.y1)/2)
                elif r.height >= 8 and r.width <= 3:
                    v.append((r.x0+r.x1)/2)
                elif r.width >= 8 and r.height >= 8:
                    rects += 1
                    h.extend((r.y0, r.y1)); v.extend((r.x0, r.x1))
    def distintos(xs):
        out = []
        for x in sorted(xs):
            if not out or x-out[-1] > 3:
                out.append(x)
        return len(out)
    return dict(h=distintos(h), v=distintos(v), curvas=curves, diagonais=diag, retangulos=rects)


def detectar(page, sistema="visivel", incluir_text=True):
    """Regras congeladas antes da medicao. Nenhum classificador ou modelo de layout."""
    mat = _matriz_pdfplumber(page) if sistema == "plumber" else page.rotation_matrix
    tempos, erros = {}, []
    ini = time.perf_counter()
    paths = page.get_drawings()
    tempos["drawings"] = time.perf_counter()-ini
    out = {k: [] for k in ("lines", "text", "tracos", "raster", "vetor")}
    for strategy in ("lines", "text") if incluir_text else ("lines",):
        ini = time.perf_counter()
        try:
            # use_layout=False impede dependencia opcional de analise de layout.
            found = page.find_tables(strategy=strategy, paths=paths, use_layout=False)
            for t in found.tables:
                b = list(t.bbox)
                if valido(b) and t.row_count >= 2 and t.col_count >= 2 and o.area(b) >= 400:
                    out[strategy].append(regiao("table", bbox(b, mat), strategy,
                                               linhas=t.row_count, colunas=t.col_count))
        except Exception as e:
            erros.append(strategy+": "+str(e)[:160])
        tempos[strategy] = time.perf_counter()-ini
    ini = time.perf_counter()
    # Exclui fundos/bordas que conectariam todos os desenhos da pagina.
    paths = [p for p in paths if o.area(list(p["rect"])) < .90*o.area(list(page.rect))]
    clusters = page.cluster_drawings(drawings=paths, x_tolerance=3, y_tolerance=3)
    for c in clusters:
        b = list(c)
        if not valido(b) or c.width < 12 or c.height < 12:
            continue
        membros = [p for p in paths if (p["rect"] & c).is_empty is False
                   or c.contains(p["rect"])]
        s = sinais(membros)
        grid = s["h"] >= 3 and s["v"] >= 2
        if grid and o.area(b) >= 400 and not s["curvas"]:
            out["tracos"].append(regiao("table", bbox(b, mat), "tracos", sinais=s))
        elif o.area(b) >= 144 and s["curvas"]+s["diagonais"] >= 4:
            out["vetor"].append(regiao("picture", bbox(b, mat), "vetor", sinais=s))
    tempos["clusters"] = time.perf_counter()-ini
    ini = time.perf_counter()
    for info in page.get_image_info(hashes=False, xrefs=False):
        b = info.get("bbox", [])
        if valido(b) and o.area(b) >= 16:
            out["raster"].append(regiao("picture", bbox(b, mat), "raster"))
    tempos["images"] = time.perf_counter()-ini
    for k in out:
        out[k] = nms(out[k])
    tables = nms(out["lines"]+out["tracos"])
    vetores = [r for r in out["vetor"] if not any(o.inter(r["bbox"], t["bbox"]) >=
                      .6*o.area(r["bbox"]) for t in tables)]
    out["rapido"] = nms(tables+out["raster"]+vetores)
    out["rapido_text"] = nms(out["rapido"]+out["text"])
    return out, tempos, erros


def prever(q, det, c):
    """Mesma geometria/limiares do LOPO; casos vazios nao usam assert."""
    ws = q["ws"]
    ats, livres = o.atomos(ws, det, c.score)
    items = ats + o.linhas_partidas(ws, livres, c.gap, q["h"])
    diag = {"max_colunas": 1, "pontes": 0, "n_atomos": len(ats),
            "atomos_sem_palavras": sum(not a["ks"] for a in ats)}
    politica = "geo" if c.abordagem.endswith("margens") else None
    ini, corpo, marcas, fim = j.particao(items, ws, q["p"]["dimensions"]["height"], politica)
    if c.abordagem.startswith("projecao"):
        ordem = o.ordenar_projecao(items, corpo, q["h"], c.vale, diag, local="local" in c.abordagem)
    else:
        ordem = o.xycut(corpo, o.boxes(items))
    key = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
    ordem = sorted(ini, key=key)+ordem+sorted(marcas, key=key)+sorted(fim, key=key)
    seq = o.fluxo([items[i] for i in ordem], ws)
    if sorted(seq) != list(range(len(ws))):
        raise ValueError("Ordenador perdeu ou duplicou palavras")
    diag.update(topo=len(ini), rodape=len(fim), marcas=len(marcas))
    return seq, diag


def comparar_regioes(pred, gt, rotulo):
    """Matching bipartido de cardinalidade maxima a IoU >= .5, depois maior IoU."""
    pp = [r for r in pred if r.get("rotulo") == rotulo and valido(r.get("bbox", []))]
    gg = [r for r in gt if r.get("rotulo") == rotulo and valido(r.get("bbox", []))]
    mat = np.array([[iou(a["bbox"], b["bbox"]) for b in gg] for a in pp])
    pares = []
    if pp and gg:
        custo = np.where(mat >= .5, min(len(pp),len(gg))+1+mat, 0.)
        rr, cc = linear_sum_assignment(custo, maximize=True)
        pares = [(int(a), int(b), float(mat[a,b])) for a,b in zip(rr,cc) if mat[a,b] >= .5]
    usop, usog = {a for a,b,v in pares}, {b for a,b,v in pares}
    return dict(tp=len(pares), fp=len(pp)-len(pares), fn=len(gg)-len(pares),
                pares=pares, falsos=[pp[i] for i in range(len(pp)) if i not in usop],
                perdidos=[gg[i] for i in range(len(gg)) if i not in usog])


def qualidade(pred, gt):
    return {k: comparar_regioes(pred, gt, k) for k in ("table", "picture")}


def tokens(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return collections.Counter(re.findall(r"[a-z0-9]+", s))


def auditar_texto(p, ws):
    grupos, livres, amb = o.donos(ws, p.get("bounding_boxes", []))
    hit, nr, npred, n = 0, 0, 0, 0
    for r, ks in zip(p.get("bounding_boxes", []), grupos):
        a = tokens(r.get("text") or "")
        if not a:
            continue
        b = tokens(" ".join(ws[k][0] for k in ks))
        hit += sum((a & b).values()); nr += sum(a.values()); npred += sum(b.values()); n += 1
    return dict(f1=2*hit/(nr+npred) if nr+npred else None,
                recall=hit/nr if nr else None, comuns=hit, ouro=nr, pdf=npred, regioes=n,
                regioes_sem_palavras=sum(not ks for ks in grupos))


def mapear_palavras(a, b):
    """Pareia texto exato e centros proximos; uma palavra nunca e usada duas vezes."""
    por_texto = collections.defaultdict(list)
    for k, w in enumerate(b):
        por_texto[unicodedata.normalize("NFKC", w[0])].append(k)
    pares, usados = [], set()
    for i, w in enumerate(a):
        cx, cy = o.centro(w)
        cs = [k for k in por_texto[unicodedata.normalize("NFKC", w[0])] if k not in usados
              and abs(o.centro(b[k])[0]-cx) <= 3
              and abs(o.centro(b[k])[1]-cy) <= max(5, (w[4]-w[2])/2)]
        if cs:
            k = min(cs, key=lambda k: (sum((x-y)**2 for x,y in zip(o.centro(w),o.centro(b[k]))), k))
            usados.add(k); pares.append((i,k))
    return pares


def comparar_palavras(a, b):
    pares = mapear_palavras(a,b)
    dif = np.array([[abs(x-y) for x,y in zip(a[i][1:5],b[k][1:5])] for i,k in pares])
    ta, tb = collections.Counter(w[0] for w in a), collections.Counter(w[0] for w in b)
    n = sum((ta & tb).values())
    pa, pb = {i for i,k in pares}, {k for i,k in pares}
    ex = []
    classes = collections.Counter()
    for i,w in enumerate(a):
        if i in pa or not b:
            continue
        k = min(range(len(b)), key=lambda k: sum((x-y)**2 for x,y in zip(o.centro(w),o.centro(b[k]))))
        z = b[k]
        if sum((x-y)**2 for x,y in zip(o.centro(w),o.centro(z))) > 400:
            categoria = "sem vizinho espacial"
        elif "(cid:" in w[0] or "\ufffd" in w[0]+z[0]:
            categoria = "CID/caractere substituto"
        elif any(c in w[0]+z[0] for c in "\ufb00\ufb01\ufb02\ufb03\ufb04"):
            categoria = "ligadura"
        elif any(c in w[0]+z[0] for c in "-\u00ad\u2013\u2014"):
            categoria = "hifen/travessao"
        elif w[0] in z[0] or z[0] in w[0]:
            categoria = "espacos/tokenizacao"
        else:
            categoria = "outra divergencia"
        classes[categoria] += 1
        if len(ex) < 10:
            ex.append(dict(plumber=w[0], mupdf=z[0], categoria=categoria, bbox=w[1:5]))
    ranks = [k for i,k in pares]
    ordem_tau = o.kendall_tau(ranks, sorted(ranks)) if len(ranks)>1 else None
    return dict(n_plumber=len(a), n_mupdf=len(b), pares=len(pares),
                multiconjunto=n, mesmo_multiconjunto=ta==tb,
                cobertura_plumber=len(pares)/len(a) if a else None,
                cobertura_mupdf=len(pares)/len(b) if b else None,
                bbox_tol2=int(np.sum(np.max(dif,axis=1)<=2)) if len(dif) else 0,
                bbox_tol5=int(np.sum(np.max(dif,axis=1)<=5)) if len(dif) else 0,
                bbox_mediana=np.median(dif,axis=0).tolist() if len(dif) else [],
                bbox_p95=np.percentile(dif,95,axis=0).tolist() if len(dif) else [],
                tau_ordem=ordem_tau, categorias=dict(classes), exemplos=ex,
                nao_pareadas_mupdf=len(b)-len(pb))


def preparar():
    qs = j.preparar()
    old = ler(RAIZ / "resultados/ordem_sem_bbox.json")
    cs = {c.id:c for c in o.grade()}
    cfgs = {r["page_id"]:cs[r["config"]] for r in old["sequencias_cv"]}
    anns = {l:list(jsonl(RAIZ / f"data/diamond/{l}/anotacoes.jsonl"))
            for l in ("diamond_piloto", "diamond_treino")}
    for q in qs:
        p = q["p"]
        rev = [a for a in anns[p["origem"]] if a.get("page_id")==p["page_id"]
               and a.get("status")=="concluida" and a.get("salvo_em")==p["diamond"]["salvo_em"]]
        if len(rev)!=1:
            raise ValueError("Revisão Diamond congelada ausente/ambígua")
        q["det_ouro"] = [regiao("table" if r["classe"]=="tabela" else "picture",r["bbox"],"ouro")
                         for r in rev[0].get("regioes",[]) if r.get("classe") in ("tabela","figura")]
        q["cfg"] = cfgs[p["page_id"]]
        q["colunas"] = j.colunas(q)["n"]
    mapa = {p["page_id"]:p for p in jsonl(RAIZ / "data/labelstudio/pdf_paginas.jsonl")
            if p.get("uso")=="teste_deteccao" and (RAIZ/p.get("pdf_local","ausente")).is_file()}
    ls = {}
    cont = collections.Counter()
    for seed in range(1,5):
        for p in jsonl(RAIZ/f"data/labelstudio/conv_seed{seed}/tarefas.jsonl"):
            if p.get("page_id") not in mapa:
                continue
            if p["page_id"] in ls:
                raise ValueError("Dois ouros LS para a mesma página: seleção precisa ser explícita")
            ls[p["page_id"]] = dict(p=p, mapa=mapa[p["page_id"]], seed=seed)
            for r in p.get("bounding_boxes",[]):
                if not valido(r.get('bbox',[])):
                    cont['bbox_invalida'] += 1
                if r.get("classe") not in GUIA:
                    cont["classe_ausente_invalida"] += 1
                elif r["classe"]=="unknown":
                    cont["unknown_fora"] += 1
    cont.update(mapa=len(mapa), com_ouro=len(ls), sem_ouro=len(mapa.keys()-ls.keys()))
    cache = ler(RAIZ/"resultados/pymupdf_palavras_cache.json")
    if cache and (RAIZ/"resultados/pymupdf_palavras.md").exists():
        pool = [v for v in cache["paginas"].values() if v.get("status")=="ok"]
        rng = random.Random(SEMENTE)
        pe = [p for p in pool if p["uf"]=="official_diary_pe"]
        escolhidas = rng.sample(pe,min(2,len(pe)))
        # SP e MG explicitamente auditados: relatorio antigo faz alegacoes geometricas fortes.
        for uf in ("official_diary_sp","official_diary_mg"):
            candidatos = [p for p in pool if p["uf"]==uf]
            if candidatos:
                escolhidas += rng.sample(candidatos,1)
        outros = [p for p in pool if p not in escolhidas and p["uf"]!="official_diary_pe"]
        escolhidas += rng.sample(outros,10-len(escolhidas))
        origem = "Conferência de 10 das 60 páginas já medidas; semente fixa, duas de PE, SP e MG incluídos."
    else:
        from orquestracao.analises.pymupdf_palavras import carregar_catalogo_paginas, sortear_amostra
        escolhidas = sortear_amostra(carregar_catalogo_paginas(str(RAIZ/"data/processed/blocos")))
        origem = "Medição integral de 60 páginas, semente fixa e pelo menos cinco de PE."
    return qs, list(ls.values()), cont, sorted(escolhidas,key=lambda p:p["page_id"]), origem


def linha_rapida(p, path, sistema, idx, chave_entrada, do_zero):
    arq = arquivo_cache("paginas",p["page_id"])
    cached = None if do_zero else ler(arq)
    if cached and cached.get("chave")==chave_entrada:
        return cached
    pymupdf.TOOLS.mupdf_warnings(reset=True)
    ini = time.perf_counter()
    util, envelope = pdf_util(path)
    with pymupdf.open(util) as doc:
        if not 0 <= idx < len(doc):
            raise ValueError("Índice de página fora do PDF")
        pg = doc[idx]
        ws = palavras(pg,sistema)
        twords = time.perf_counter()-ini
        det, tempos, erros = detectar(pg,sistema)
        w,h = pg.rect.width,pg.rect.height
        row = dict(page_id=p["page_id"],chave=chave_entrada,ws=ws,det=det,tempos=tempos,
                   twords=twords, erros=erros,indice_zero=idx,n_paginas=len(doc),pkcs7=envelope,
                   largura=w,altura=h,rotacao=pg.rotation,mediabox=list(pg.mediabox),
                   cropbox=list(pg.cropbox),digital=bool(ws),sistema=sistema)
        row['raster_pagina']=any(o.area(r['bbox'])>=.6*w*h for r in det['raster'])
        if sistema=="visivel":
            W,H = p["dimensions"]["width"],p["dimensions"]["height"]
            sx,sy = W/w,H/h
            px = dict(p,bounding_boxes=[dict(r,bbox=[r["bbox"][0]/sx,r["bbox"][1]/sy,
                  r["bbox"][2]/sx,r["bbox"][3]/sy]) for r in p.get("bounding_boxes",[])
                  if valido(r.get("bbox",[]))])
            row["escala_pt_px"] = [sx,sy]
            row["aspecto_erro"] = abs(sx/sy-1)
            row["texto"] = auditar_texto(px,ws)
            row["alternativas"] = []
            for z in (idx-1,idx+1):
                if 0<=z<len(doc) and row["texto"]["ouro"]:
                    row["alternativas"].append(dict(indice_zero=z,**auditar_texto(px,palavras(doc[z]))))
            f1 = row["texto"]["f1"]
            row["vizinha_melhor"] = any(f1 is not None and x["f1"] is not None
                                       and x["f1"]>f1+.05 for x in row["alternativas"])
            row["verificada"] = bool(f1 is not None and f1>=.5 and not row["vizinha_melhor"]
                                      and row["aspecto_erro"]<.03)
            row["sparse"] = len(ws)<20
    row['avisos_pdf']=pymupdf.TOOLS.mupdf_warnings(reset=True)
    gravar(arq,row)
    return row


def auditar_palavras(ps, do_zero, chave_base, ao_salvar=None):
    import pdfplumber
    out=[]
    for i,p in enumerate(ps):
        path=RAIZ/"data/raw"/p["uf"]/p["arquivo"]
        ck=chave([chave_base,digest(path),p["pagina"]])
        arq=arquivo_cache("palavras",p["page_id"])
        row=None if do_zero else ler(arq)
        if not row or row.get("chave")!=ck:
            util,_=pdf_util(path)
            start=time.perf_counter()
            with pdfplumber.open(util) as doc:
                pg=doc.pages[int(p["pagina"])]
                a=[[w["t"],w["x0"],w["top"],w["x1"],w["bottom"]] for w in palavras_da_pagina(pg)]
                tpl=time.perf_counter()-start
                mb=list(pg.mediabox); cb=list(pg.cropbox); rot=pg.rotation
            start=time.perf_counter()
            with pymupdf.open(util) as doc:
                pg=doc[int(p["pagina"])]
                b=palavras(pg,"plumber")
                tm=time.perf_counter()-start
                trace=pg.get_texttrace()
                invisible=sum(len(s.get("chars",[])) for s in trace if s.get("type")==3 or s.get("opacity",1)==0)
                duplicates=len(b)-len({(w[0],*(round(v,2) for v in w[1:5])) for w in b})
            row=dict(page_id=p["page_id"],uf=p["uf"],chave=ck,tplumber=tpl,tmupdf=tm,
                     mediabox=mb,cropbox=cb,rotacao=rot,invisiveis=invisible,duplicatas=duplicates,
                     comparacao=comparar_palavras(a,b))
            gravar(arq,row)
        out.append(row)
        if ao_salvar:
            ao_salvar(out)
        print(f"Palavras {i+1}/{len(ps)}: {p['uf']} pares={row['comparacao']['pares']}",flush=True)
    return out


def benchmark(qs, rows, do_zero, chave_base, threads, sem_docling, ao_salvar=None):
    """Latencia fim-a-fim de ambos os pipelines, mesmas paginas e geometria."""
    import pdfplumber
    model=None; carga=None; out=[]
    for i,q in enumerate(qs):
        p=q["p"]; pid=p["page_id"]; c=q["cfg"]
        path=RAIZ/"data/raw"/p["uf"]/p["arquivo"]
        ck=chave([chave_base,digest(path),asdict(c),threads,sem_docling])
        arq=arquivo_cache("tempo",pid)
        r=None if do_zero else ler(arq)
        if not r or r.get("chave")!=ck:
            r=dict(page_id=pid,chave=ck,threads=threads)
            util,_=pdf_util(path)
            for variant in ("rapido","rapido_text"):
                t0=time.perf_counter()
                with pymupdf.open(util) as doc:
                    pg=doc[int(p["pagina"])]; ws=palavras(pg,"plumber")
                    tw=time.perf_counter()-t0
                    ds,ts,err=detectar(pg,"plumber",incluir_text=variant=="rapido_text")
                    td=time.perf_counter()-t0-tw
                    aux=dict(p=p,ws=ws,h=statistics.median(w[4]-w[2] for w in ws) if ws else 10)
                    start=time.perf_counter(); seq,diag=prever(aux,ds[variant],c)
                    to=time.perf_counter()-start
                r[variant]=dict(total=time.perf_counter()-t0,palavras=tw,regioes=td,ordem=to,
                                n_palavras=len(seq),erros=err)
            if sem_docling:
                r["docling_erro"]="Detector ao vivo desativado explicitamente"
            else:
                try:
                    if model is None:
                        os.environ["HF_HUB_OFFLINE"]="1"
                        os.environ["TRANSFORMERS_OFFLINE"]="1"
                        os.environ["CUDA_VISIBLE_DEVICES"]="-1"
                        import torch
                        torch.set_num_threads(threads)
                        torch.set_num_interop_threads(1)
                        from src.data.layout import Detector,DPI
                        start=time.perf_counter()
                        model=Detector(dispositivo="cpu",permitir_download=False)
                        carga=time.perf_counter()-start
                        # Aquecimento nao entra no tempo de paginas nem usa dados externos.
                        from PIL import Image
                        model([Image.new("RGB",(600,800),"white")],[((0,0,600,800),1)])
                        gravar(BASE/"modelo.json",dict(carga_s=carga,threads=threads,device="cpu"))
                    from src.data.layout import DPI
                    t0=time.perf_counter()
                    with pdfplumber.open(util) as doc:
                        pg=doc.pages[int(p["pagina"])]
                        ws=[[w["t"],w["x0"],w["top"],w["x1"],w["bottom"]] for w in palavras_da_pagina(pg)]
                        tw=time.perf_counter()-t0
                        start=time.perf_counter(); pi=pg.to_image(resolution=DPI)
                        im=pi.original.convert("RGB"); tr=time.perf_counter()-start
                        start=time.perf_counter(); ds=model([im],[(tuple(pi.bbox),float(pi.scale))])[0]
                        td=time.perf_counter()-start
                        aux=dict(p=p,ws=ws,h=statistics.median(w[4]-w[2] for w in ws) if ws else 10)
                        start=time.perf_counter(); seq,diag=prever(aux,ds,c); to=time.perf_counter()-start
                    r["docling"]=dict(total=time.perf_counter()-t0,palavras=tw,render=tr,regioes=td,
                                      ordem=to,n_palavras=len(seq))
                except (Exception,SystemExit) as e:
                    r["docling_erro"]=f"{type(e).__name__}: {e}"
            gravar(arq,r)
        out.append(r)
        if ao_salvar:
            ao_salvar(out)
        print(f"Tempo {i+1}/{len(qs)}: {pid} PyMuPDF={r['rapido']['total']:.3f}s Docling="+
              (f"{r['docling']['total']:.3f}s" if 'docling' in r else r.get('docling_erro','ausente')),flush=True)
    return out


def bootstrap(rows, metodo, regua, metrica):
    grupos=collections.defaultdict(list)
    for r in rows:
        v=r["metodos"][metodo][regua].get(metrica)
        if v is not None:
            grupos[r["veiculo"]].append(v)
    if not grupos:
        return dict(media=None,ic=[None,None])
    vals=list(grupos.values()); rng=np.random.default_rng(SEMENTE)
    sums=np.array([sum(v) for v in vals]); ns=np.array([len(v) for v in vals])
    ix=rng.integers(0,len(vals),size=(NBOOT,len(vals)))
    boots=sums[ix].sum(axis=1)/ns[ix].sum(axis=1)
    return dict(media=float(sums.sum()/ns.sum()),ic=np.percentile(boots,[2.5,97.5]).tolist())


def teste(rows, a, b, regua, metrica):
    vals=[]; groups=collections.defaultdict(list)
    for r in rows:
        x=r["metodos"][a][regua].get(metrica); y=r["metodos"][b][regua].get(metrica)
        if x is not None and y is not None:
            vals.append((x,y)); groups[r["veiculo"]].append(x-y)
    if not vals:
        return dict(delta=None,ic=[None,None],p=None,n=0,empates=0)
    x,y=np.array(vals).T; d=x-y
    p=1.0 if np.all(np.abs(d)<1e-14) else float(wilcoxon(x,y,zero_method="pratt",method="approx").pvalue)
    vs=list(groups.values()); sums=np.array([sum(v) for v in vs]); ns=np.array([len(v) for v in vs])
    rng=np.random.default_rng(SEMENTE); ix=rng.integers(0,len(vs),size=(NBOOT,len(vs)))
    boots=sums[ix].sum(axis=1)/ns[ix].sum(axis=1)
    return dict(delta=float(np.mean(d)),ic=np.percentile(boots,[2.5,97.5]).tolist(),p=p,
                n=len(d),empates=int(np.sum(np.abs(d)<1e-14)))


def resumir_deteccao(rows, nome):
    out={}
    for cls in ("table","picture"):
        tp=sum(r["qualidade"][nome][cls]["tp"] for r in rows if nome in r["qualidade"])
        fp=sum(r["qualidade"][nome][cls]["fp"] for r in rows if nome in r["qualidade"])
        fn=sum(r["qualidade"][nome][cls]["fn"] for r in rows if nome in r["qualidade"])
        out[cls]=dict(tp=tp,fp=fp,fn=fn,precisao=tp/(tp+fp) if tp+fp else None,
                      recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)
    return out


def f(v,n=3):
    return "—" if v is None else f"{v:.{n}f}".replace(".",",")


def pct(v):
    return "—" if v is None else f(100*v,1)+"%"


def cel(v,percent=False):
    mul=100 if percent else 1; n=1 if percent else 3
    if v["media"] is None:
        return "—"
    return f(v["media"]*mul,n)+("%" if percent else "")+" ["+f(v["ic"][0]*mul,n)+"; "+f(v["ic"][1]*mul,n)+"]"


def tabela_det(rows, nomes):
    out=["| Método | Classe | TP / FP / FN | Precisão | Revocação | F1 |",
         "|---|---|---:|---:|---:|---:|"]
    for nome in nomes:
        s=resumir_deteccao(rows,nome)
        for cls,rot in (("table","tabela"),("picture","imagem")):
            v=s[cls]
            out.append(f"| {DET_NOMES[nome]} | {rot} | {v['tp']} / {v['fp']} / {v['fn']} | {pct(v['precisao'])} | {pct(v['recall'])} | {pct(v['f1'])} |")
    return out


def tabela_ordem(rows, regua):
    out=["| Método | τ ↑ (IC 95% por veículo) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas |",
         "|---|---:|---:|---:|---:|"]
    for nome in NOMES:
        ss={m:bootstrap(rows,nome,regua,m) for m in ("tau","sucessor","ard")}
        frag=[r["metodos"][nome]["diag"]["fracao_estrita"] for r in rows
              if r["metodos"][nome]["diag"]["fracao_estrita"] is not None]
        out.append(f"| {NOMES[nome]} | {cel(ss['tau'])} | {cel(ss['sucessor'],True)} | {cel(ss['ard'])} | {pct(statistics.mean(frag) if frag else None)} |")
    return out


def tabela_tempo(rows):
    out=["| Pipeline CPU | n | Média s/pág. | Mediana | p95 | pág./s |",
         "|---|---:|---:|---:|---:|---:|"]
    for k,label in (("docling","pdfplumber + renderização + Docling + ordem"),
                    ("rapido","PyMuPDF conservador + ordem"),("rapido_text","PyMuPDF com text + ordem")):
        vs=[r[k]["total"] for r in rows if k in r]
        if vs:
            out.append(f"| {label} | {len(vs)} | {f(statistics.mean(vs))} | {f(statistics.median(vs))} | {f(float(np.percentile(vs,95)))} | {f(len(vs)/sum(vs),2)} |")
    return out


def relatorio(R):
    gs,ls,ws,ts=R.get("golden",[]),R.get("ls",[]),R.get("palavras",[]),R.get("tempo",[])
    out=["# Caminho rápido digital com PyMuPDF", "",
         f"Estado: {'CONCLUÍDO' if R.get('concluido') else 'PARCIAL, retomável'}. CPU; PyMuPDF {R['versoes']['PyMuPDF']}; nenhuma GPU, OCR, rede ou modelo no caminho rápido.",""]
    if gs and ts:
        tau={k:bootstrap(gs,k,"palavras","tau")["media"] for k in NOMES}
        sd=resumir_deteccao(gs,"rapido"); sl=resumir_deteccao([r for r in ls if r["digital"]],"rapido")
        matched=[r for r in ts if "docling" in r]
        rat=sum(r["docling"]["total"] for r in matched)/sum(r["rapido"]["total"] for r in matched) if matched else None
        pure=[r['puro']['metricas']['tau'] for r in gs if 'puro' in r and r['puro']['metricas']['tau'] is not None]
        out += ["## Resumo em cinco linhas", "",
                "1. Veredito: o caminho digital acelera a extração, mas não substitui universalmente o detector para tabelas sem grade e imagens compostas.",
                f"2. Nas {len(gs)} páginas Golden, trocando só átomos: τ {f(tau['rapido'])} PyMuPDF, {f(tau['docling'])} Docling, {f(tau['nenhum'])} sem átomos; com words realmente MuPDF, τ {f(statistics.mean(pure) if pure else None)} em suporte comum (diagnóstico otimista).",
                f"3. No Diamond, PyMuPDF conservador recupera {pct(sd['table']['recall'])} das tabelas e {pct(sd['picture']['recall'])} das imagens; no LS digital, {pct(sl['table']['recall'])} e {pct(sl['picture']['recall'])}.",
                f"4. No tempo fim a fim pareado de {len(matched)} páginas, a aceleração é {f(rat,1)}×; há {sum(not r['digital'] for r in ls)} páginas LS sem palavras, fora da aplicabilidade do caminho digital.",
                "5. Recomendação: PyMuPDF primeiro, com verificação de texto/geometria; detector/OCR como fallback para evidência tabular ou visual inconclusiva, validando a política em ouro independente.",""]
    out += ["## Protocolo e rastreabilidade", "",
            f"{R['origem_palavras']} Não se repetiu a medição inteira já existente. O relatório anterior não foi editado. Golden: {len(gs)}/{R['n_golden']} páginas medidas, revisões Diamond exatamente da data congelada no Golden, incluindo figuras sem texto. LS: {len(ls)}/{R['ls_catalogo']['com_ouro']} páginas de teste com PDF local e ouro convertido dos quatro seeds; nenhum export grande é carregado como texto integral.",
            "As 16 classes vêm de `src/data/taxonomia_layout.py`: table → tabela; figure/chart/heading → imagem; unknown e classe ausente/inválida ficam fora; as demais são texto. O detector geométrico emite somente table/picture; o texto restante vem da camada digital, sem caixas finas semânticas. A qualidade abaixo mede localização de tabela/imagem, não F1 de segmentação do texto.",
            "Predições e ouro são pareados por classe, um a um, maximizando primeiro a cardinalidade com IoU ≥ 0,5 e depois IoU. Precisão/recall/F1 micro de regiões, macro de páginas somente nas métricas de ordem. Não confundir os dois ouros: convenções de caixa e classe diferem.",
            f"Seed {SEMENTE}; bootstrap percentil de {NBOOT} reamostras agrupadas por veículo (parte antes da primeira barra), preservando todas as páginas dos veículos sorteados. IC condicional às configurações LOPO antigas, congeladas e não selecionadas novamente; não estima incerteza do desenvolvimento. Wilcoxon bilateral pareado com zero_method='pratt', aproximação normal; p é exploratório, páginas do mesmo veículo não são independentes. Nenhuma decisão de adoção foi aplicada ao pipeline.",
            "Hashes das entradas, fontes e PDFs invalidam caches; cada página é salva atomicamente antes da próxima. Tempos incluem abertura do PDF por página e ordem; não incluem leitura do ouro, matching, hashes, escrita de cache/relatório. Não há remoção de outliers nem inferência de tempos do detector a partir de caches antigos.",""]
    if ws:
        out += ["## Palavras: auditoria do relatório existente", "",
                "`get_text('words', sort=False)` é usado diretamente: não se afirma identidade com o contrato que desduplica caracteres, descarta texto girado e junta letras espaçadas no pdfplumber. Matching exige texto NFKC igual e centros próximos (até três pontos em x e cinco ou meia altura em y); reportam-se também multiconjunto exato e tolerância máxima das quatro bordas.",
                "| Veículo / página | Palavras plumber / MuPDF | Pares espaciais | Pares com todas as bordas ≤ 2 pt / ≤ 5 pt | τ da ordem dos pares | s plumber / MuPDF |",
                "|---|---:|---:|---:|---:|---:|"]
        for r in ws:
            c=r['comparacao']
            out.append(f"| `{r['page_id']}` | {c['n_plumber']} / {c['n_mupdf']} | {c['pares']} | {c['bbox_tol2']} / {c['bbox_tol5']} | {f(c['tau_ordem'])} | {f(r['tplumber'])} / {f(r['tmupdf'])} |")
        ca=sum(r['comparacao']['n_plumber'] for r in ws); cb=sum(r['comparacao']['n_mupdf'] for r in ws)
        hits=sum(r['comparacao']['pares'] for r in ws)
        out += ["",f"No total, {ca} palavras plumber, {cb} MuPDF, {hits} pares ({pct(hits/ca if ca else None)} do plumber); multiconjunto exatamente igual em {sum(r['comparacao']['mesmo_multiconjunto'] for r in ws)}/{len(ws)} páginas. Logo, a afirmação antiga de paridade garantida/perda nula não é sustentada por esta auditoria.",
                "| Página | Mediana |Δx0| / |Δy0| / |Δx1| / |Δy1|, pt | p95, pt | Rotação |",
                "|---|---|---|---:|"]
        for r in ws:
            c=r['comparacao'];out.append(f"| `{r['page_id']}` | {' / '.join(f(v) for v in c['bbox_mediana'])} | {' / '.join(f(v) for v in c['bbox_p95'])} | {r['rotacao']} |")
        cats=collections.Counter()
        for r in ws: cats.update(r['comparacao']['categorias'])
        out += ["",f"Categorias automáticas dos não pareados (não são diagnóstico causal de fonte): {dict(cats)}. Caracteres de spans invisíveis: {sum(r['invisiveis'] for r in ws)}; palavras MuPDF duplicadas com mesma caixa arredondada: {sum(r['duplicatas'] for r in ws)}. Invisibilidade não é inferida da transcrição; um span tipo 3/opacidade zero pode ser camada OCR. Não foi aplicada deshifenização entre linhas.",
                "Diferenças sistemáticas: métricas verticais de fonte alteram top/bottom; espaços sintetizados/tokenização e a junção de letras do extrator mudam o inventário; ligaduras são normalizadas só no matching; CIDs/substitutos dependem da codificação. A ordem nativa é do conteúdo e pode diferir entre parsers; não é ordem humana nem parâmetro de ordenação. O teste de pares não mede equivalência semântica de palavras fundidas ou partidas.",
                "Coordenadas retornadas pelo MuPDF são relativas à CropBox **não rotacionada**; page.rect é rotacionada. Para o ouro Diamond usamos a transformação explícita para MediaBox rotacionada do módulo opcional existente; para LS aplicamos rotation_matrix e escala separada x/y da imagem. Não se usa a heurística de subtrair CropBox olhando as primeiras palavras. [API oficial de coordenadas](https://pymupdf.readthedocs.io/en/latest/page.html).",""]
        ex=[(r,e) for r in ws for e in r['comparacao']['exemplos']][:12]
        out += ["| Exemplo | pdfplumber | MuPDF | Categoria automática |","|---|---|---|---|"]
        for r,e in ex:
            clean=lambda s:str(s).replace('|','/').replace('\n',' ')[:90]
            out.append(f"| `{r['page_id']}` | {clean(e['plumber'])} | {clean(e['mupdf'])} | {e['categoria']} |")
    out += ["", "## Regras sem detector", "",
            "Conservador = find_tables(lines) + agrupamento de traços/retângulos + get_image_info + vetores. As duas estratégias find_tables são executadas com `use_layout=False`, sem pymupdf_layout. Tabelas exigem pelo menos duas linhas, duas colunas e área de quatrocentos pontos quadrados. A estratégia text é apresentada isoladamente e como ablação acrescentada ao conservador, sem escolher pelo desempenho no ouro.",
            "Traços: cluster_drawings com tolerância de três pontos; pelo menos três horizontais e duas verticais distintas, sem curvas. Retângulos finos contam como traços. Fundo/borda com área acima de noventa por cento da página é excluído do agrupamento. Vetores: cluster com lados de pelo menos doze pontos, área de pelo menos cento e quarenta e quatro, e quatro curvas/diagonais; exclui os que ficam majoritariamente em tabela. Imagens raster: retângulos válidos com área mínima de dezesseis pontos quadrados. NMS elimina duplicatas da mesma classe. Não une tabelas adjacentes.",
            "Score geométrico 1 é marcador de regra aceita, sem probabilidade calibrada: os limiares de confiança LOPO não selecionam os candidatos MuPDF. Isso é uma limitação da troca de origem, não uma comparação de confiança entre detector e regras. [Estratégias e desenhos na API oficial](https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables).",""]
    if gs:
        out += ["## Qualidade das regiões — Diamond congelado", ""]
        out += tabela_det(gs,tuple(DET_NOMES))
        out += ["", "Inclui tabela/figura da revisão humana Diamond, também as figuras sem palavras excluídas do lote de ordem. Docling = detector.regioes congelado, filtrado no score da configuração LOPO de cada página. O cache anterior já tem seu piso de confiança; não se simula recall abaixo dele.", ""]
    if ls:
        digital=[r for r in ls if r['digital']];scan=[r for r in ls if not r['digital']]
        verified=[r for r in digital if r['verificada']]
        out += ["## Qualidade — Label Studio interno", "",
                f"Páginas com palavras: {len(digital)}; sem palavras: {len(scan)}. Ausência de camada textual é um marcador operacional de digitalizada/vetorizada, não prova de scanner. Páginas com menos de vinte palavras: {sum(r['sparse'] for r in ls)}. Não se usa OCR. PKCS#7 extraídos apenas para temporário em resultados: {sum(r['pkcs7'] for r in ls)} páginas.",
                f"Regiões-ouro LS sem palavras associadas, incluindo elementos gráficos: {sum(r['texto'].get('regioes_sem_palavras',0) for r in ls)}. Permanecem na régua de detecção por IoU; não se aborta nem se atribui texto fictício.",
                f"Páginas com raster cobrindo pelo menos sessenta por cento da área: {sum(r.get('raster_pagina',False) for r in ls)}; dessas, {sum(r.get('raster_pagina',False) and r['digital'] for r in ls)} ainda têm palavras. Ter algum texto (por exemplo, só um cabeçalho digital) não comprova PDF nascido digital nem dispensa OCR no corpo. O estrato 'com palavras' inclui esses casos híbridos, e o subconjunto confirmado por transcrição abaixo ajuda a explicitar esse viés.",
                "Índice do mapa é de base um, convertido por pagina−1; índice do acervo/Golden já é base zero. Escala = largura/altura em pixels do ouro dividida por page.rect em pontos. Para cada PDF local conferimos a transcrição em suas caixas e, quando existem, ambas as páginas vizinhas. A escala x/y evita arredondamento do raster; diferença de aspecto maior que três por cento é sinalizada.",
                f"Verificação positiva: {len(verified)}/{len(digital)} páginas digitais têm F1 espacial de tokens ≥ 0,5, aspecto compatível e nenhuma vizinha melhor em mais de 0,05; vizinha melhor: {sum(r['vizinha_melhor'] for r in ls)}; aspecto suspeito: {sum(r['aspecto_erro']>=.03 for r in ls)}. Não se escolhe outra página/escala pelo ouro: casos incertos permanecem declarados. Sem texto/transcrição suficiente não se pode confirmar o alinhamento pelo texto.",""]
        f1s=[r['texto']['f1'] for r in digital if r['texto']['f1'] is not None]
        out += [f"F1 espacial de transcrição: mediana {f(statistics.median(f1s) if f1s else None)}. Classe inválida/ausente: {R['ls_catalogo'].get('classe_ausente_invalida',0)}; unknown fora: {R['ls_catalogo'].get('unknown_fora',0)}. Resultados abaixo incluem todas as digitais, evitando esconder baixo alinhamento.",""]
        out += tabela_det(digital,tuple(k for k in DET_NOMES if k!='docling'))
        out += ["", "Páginas com palavras cuja confirmação por transcrição ficou inconclusiva:", "",
                "| Página | Índice zero | F1 espacial | Escala x / y, px/pt | Vizinha melhor |",
                "|---|---:|---:|---:|---|"]
        for r in digital:
            if not r['verificada']:
                out.append(f"| `{r['page_id']}` | {r['indice_zero']} | {f(r['texto']['f1'])} | {' / '.join(f(v,4) for v in r['escala_pt_px'])} | {r['vizinha_melhor']} |")
        out += ["", "Subconjunto com página/escala confirmadas por texto (seleção favorece PDFs de transcrição fácil):", ""]+tabela_det(verified,("rapido","rapido_text"))
        out += ["", "Sem camada textual: diagnóstico de regiões, fora do domínio do pipeline de palavras. Uma imagem de página inteira não é equivalente a todas as figuras/tabelas internas:",""]+tabela_det(scan,("rapido","rapido_text"))
    if gs:
        out += ["", "## Efeito na ordem — principal: palavras na saída real", "",
                "Mesmas palavras/IDs congelados do Diamond em todos os braços: muda apenas a origem dos átomos. Isso isola a detecção e não mede a mudança de tokenização do extrator; o tempo fim a fim, por sua vez, extrai as palavras de cada biblioteca ao vivo. Nenhum ID de segmentação diferente é comparado diretamente.",
                f"Configurações LOPO por página lidas do JSON do relatório original, sem nova seleção: {dict(collections.Counter(r['config'] for r in gs))}. A política permanece desligada nas páginas em que o LOPO original assim escolheu; a baseline justa recebe topo/marcas/rodapé do método com os mesmos limiares fixos, em todas as caixas de referência.",
                "XY-cut ouro pura e XY-cut ouro com margens são oráculos de segmentação (†), não pipelines disponíveis sem anotação. Precedência: marcas pela mesma regex primeiro; topo centro < sete por cento e base < dez por cento; rodapé centro > noventa e cinco por cento. Emissão: topo, corpo, marcas, rodapé. A linha justa não usa classe humana para decidir margem.",
                "Ouro de palavras = regiões na sequência humana, palavras internas por linhas geométricas. A ordem interna de tabela não foi anotada independentemente. Sucessor de palavras é inflado por pares dentro das regiões; fragmentação estrita conta qualquer interrupção por palavra de outra região ou sem ouro. Régua com menos de dois itens retorna ausência de medida.",""]
        out += tabela_ordem(gs,"palavras")
        out += ["", "| Origem de átomos | Átomos aceitos (soma) | Sem palavras (soma) |",
                "|---|---:|---:|"]
        for k in ('docling','rapido','rapido_text','nenhum'):
            out.append(f"| {k} | {sum(r['metodos'][k]['diag']['n_atomos'] for r in gs)} | {sum(r['metodos'][k]['diag']['atomos_sem_palavras'] for r in gs)} |")
        if all('puro' in r for r in gs):
            pure=[r['puro'] for r in gs]
            ref=sum(r['referencia'] for r in pure);hits=sum(r['comuns'] for r in pure)
            tt=[r['metricas']['tau'] for r in pure if r['metricas']['tau'] is not None]
            purerows=[dict(veiculo=r['veiculo'],metodos={'puro':{'palavras':r['puro']['metricas']}}) for r in gs]
            pc=bootstrap(purerows,'puro','palavras','tau')
            out += ["",f"Diagnóstico do pipeline realmente puro, extraindo words ao vivo: {hits}/{ref} palavras-ouro pareadas exatamente por texto/centro ({pct(hits/ref if ref else None)}). Nas palavras comuns, τ macro {cel(pc)} (IC por veículo, condicional ao matching/configurações). Faltantes do ouro: {ref-hits}; palavras MuPDF sem par: {sum(r['sem_par_mupdf'] for r in pure)}. Este τ em suporte comum exclui erros de tokenização e pode ser otimista; não é comparável diretamente à tabela controlada acima e não demonstra identidade fim a fim. A alteração das alturas/fragmentação das palavras também muda a geometria dos vales; detectar as mesmas tabelas não assegura a mesma ordem ao trocar o parser.",""]
            out += ["| Página: maiores perdas ao trocar também as palavras | τ com palavras congeladas | τ words MuPDF, comuns | Palavras comuns / ouro |",
                    "|---|---:|---:|---:|"]
            eleg=[r for r in gs if r['puro']['metricas']['tau'] is not None and r['metodos']['rapido']['palavras']['tau'] is not None]
            for r in sorted(eleg,key=lambda r:r['puro']['metricas']['tau']-r['metodos']['rapido']['palavras']['tau'])[:5]:
                out.append(f"| `{r['page_id']}` | {f(r['metodos']['rapido']['palavras']['tau'])} | {f(r['puro']['metricas']['tau'])} | {r['puro']['comuns']} / {r['puro']['referencia']} |")
            out += ["", "Há perdas de ordem mesmo em páginas com todas as palavras pareadas: igualdade do inventário textual não basta para preservar agrupamento de linhas e calhas. Não se recalibrou o limiar de vão pela altura nova da fonte, pois o protocolo exige congelar o LOPO.", ""]
        out += ["",f"Regiões sem palavras contadas: {sum(r['auditoria']['regioes_vazias'] for r in gs)}; páginas sem palavras: {sum(r['auditoria']['sem_palavras'] for r in gs)}. Palavras sem região-ouro: {sum(r['auditoria']['sem_ouro'] for r in gs)}. Fallback de região vazia por vizinho geométrico é somente secundário; páginas vazias não recebem nota perfeita.",
                "", "| Comparação pareada (A − B) | Métrica | Diferença [IC 95% por veículo] | p Pratt bruto | n / empates |",
                "|---|---|---:|---:|---:|"]
        tests=[]
        for a,b in (("rapido","docling"),("rapido","nenhum"),("rapido","xy_margens"),("rapido_text","rapido")):
            for regua in ('palavras','regioes','linhas'):
                for metric in ('tau','sucessor','ard'):
                    tests.append((a,b,regua,metric,teste(gs,a,b,regua,metric)))
        order=sorted(range(len(tests)),key=lambda i:tests[i][4]['p'] if tests[i][4]['p'] is not None else 1)
        adjusted={}; previous=0
        for k,i in enumerate(order):
            p=tests[i][4]['p'];previous=max(previous,min(1,(len(tests)-k)*(p or 0))); adjusted[i]=previous
        for i,(a,b,regua,metric,t) in enumerate(tests):
            label=regua+'/'+metric;scale=100 if metric=='sucessor' else 1
            out.append(f"| {a} − {b} | {label} | {f(t['delta']*scale if t['delta'] is not None else None)} [{f(t['ic'][0]*scale if t['ic'][0] is not None else None)}; {f(t['ic'][1]*scale if t['ic'][1] is not None else None)}] | {f(t['p'],5)} (Holm {f(adjusted[i],5)}) | {t['n']} / {t['empates']} |")
        out += ["", "Holm considera conjuntamente as comparações/métricas/réguas desta tabela; não corrige toda a história exploratória anterior. p sem significância não demonstra equivalência ou não inferioridade. Sucessor em pontos percentuais nesta tabela; ARD menor é melhor.",
                "", "## Estratos de colunas detectadas, sem usar ouro", ""]
        for label,rr in (("Uma coluna",[r for r in gs if r['colunas']==1]),("Multicoluna",[r for r in gs if r['colunas']>1])):
            out += [f"{label}: {len(rr)} páginas; critério fixo de calhas da reanálise justa, não anotação visual independente.",""]+tabela_ordem(rr,"palavras")+[""]
        out += ["## Réguas secundárias: mediana de ranks", "",
                "As duas tabelas abaixo preservam comparabilidade histórica. A mediana pode esconder intercalação de texto; não é o veredito principal.",""]
        for regua in ('regioes','linhas'):
            out += [regua.capitalize()+":",""]+tabela_ordem(gs,regua)+[""]
    if ts:
        out += ["## Tempo fim a fim por página", "",
                f"Threads Torch = {R['threads']}; CPU, modelo Docling local em eval/no_grad, renderização original do projeto na resolução de src/data/layout.py. Ambos os pipelines executam a mesma ordenação congelada em suas próprias palavras e regiões; tabela text é ablação adicional. Modelo é aquecido uma vez; carregamento fica separado. Abertura é por página, sem amortizar entre páginas do mesmo PDF. Cache de disco do sistema está aquecido; ordem de medição é fixa e há carga concorrente nesta máquina.",""]+tabela_tempo(ts)
        m=[r for r in ts if 'docling' in r]
        if m:
            out += ["",f"Aceleração pareada conservador: {f(sum(r['docling']['total'] for r in m)/sum(r['rapido']['total'] for r in m),1)}×. Vazão é n/soma dos tempos, não média de inversos. O tempo não vem da comparação antiga de palavras nem de um cache de GPU.",
                    "| Etapa | pdfplumber + Docling, média s | PyMuPDF conservador, média s |", "|---|---:|---:|"]
            for k,label in (("palavras","Abertura + palavras"),("render","Renderização"),("regioes","Regiões"),("ordem","Ordem")):
                a=[r['docling'][k] for r in m if k in r['docling']];b=[r['rapido'][k] for r in m if k in r['rapido']]
                out.append(f"| {label} | {f(statistics.mean(a) if a else None)} | {f(statistics.mean(b) if b else None)} |")
        model=ler(BASE/'modelo.json')
        if model:out += ["",f"Carga do Docling CPU: {f(model['carga_s'])} s (fora das latências aquecidas)."]
        out += ["", "Cauda lenta do caminho geométrico (sem descartar páginas):", "",
                "| Página | PyMuPDF total, s | Palavras, s | Regiões, s | Docling total, s |",
                "|---|---:|---:|---:|---:|"]
        for r in sorted(ts,key=lambda r:-r['rapido']['total'])[:5]:
            out.append(f"| `{r['page_id']}` | {f(r['rapido']['total'])} | {f(r['rapido']['palavras'])} | {f(r['rapido']['regioes'])} | {f(r.get('docling',{}).get('total'))} |")
        out += ["", "Remover rede não torna find_tables/clustering custo constante: páginas com muitos objetos vetoriais continuam lentas. O ganho de palavras isoladas não deve ser anunciado como aceleração fim a fim. Um orçamento de tempo para análise geométrica seria hipótese futura; não se interromperam páginas para favorecer a medição."]
        errs=[r['docling_erro'] for r in ts if 'docling_erro' in r]
        if errs:out += ["",f"Detector indisponível/falha em {len(errs)} páginas: {errs[:2]}; não se atribui tempo fictício."]
    if gs or ls:
        out += ["",f"Falhas internas de estratégias geométricas contadas: {sum(len(r.get('deteccao_erros',[])) for r in gs)} no Golden e {sum(len(r.get('erros',[])) for r in ls)} no LS. Páginas com avisos de sintaxe/reparo MuPDF: {sum(bool(r.get('avisos_pdf')) for r in gs)} no Golden e {sum(bool(r.get('avisos_pdf')) for r in ls)} no LS. Os candidatos das outras estratégias permanecem disponíveis; falha não é ausência de tabela."]
        out += ["", "## Análise de erro com exemplos", "",
                "Exemplos escolhidos deterministicamente por falha e diferença de τ, sem ajustar regras depois de vê-los. Bbox em pontos no Diamond e pixels no LS; caches conservam candidatos, pares, falsos positivos e falsos negativos.",""]
        for domain,rs in (("Diamond",gs),("LS",ls)):
            examples=sorted(rs,key=lambda r:-(r['qualidade']['rapido']['table']['fn']+r['qualidade']['rapido']['picture']['fn']))[:4]
            for r in examples:
                t=r['qualidade']['rapido']['table'];im=r['qualidade']['rapido']['picture']
                out.append(f"- {domain} `{r['page_id']}`: tabela TP/FP/FN {t['tp']}/{t['fp']}/{t['fn']}; imagem {im['tp']}/{im['fp']}/{im['fn']}; primeira caixa perdida: {next(iter(t['perdidos']+im['perdidos']),{}).get('bbox','nenhuma')}.")
        if gs:
            out += ["", "Maiores perdas/ganhos de τ de palavras ao trocar Docling por PyMuPDF:", "",
                    "| Página | τ Docling | τ PyMuPDF | Δ | Fragmentação PyMuPDF |", "|---|---:|---:|---:|---:|"]
            comparaveis=[r for r in gs if r['metodos']['rapido']['palavras']['tau'] is not None
                         and r['metodos']['docling']['palavras']['tau'] is not None]
            rr=sorted(comparaveis,key=lambda r:r['metodos']['rapido']['palavras']['tau']-r['metodos']['docling']['palavras']['tau'])
            for r in rr[:4]+rr[-4:]:
                a=r['metodos']['docling']['palavras']['tau'];b=r['metodos']['rapido']['palavras']['tau']
                out.append(f"| `{r['page_id']}` | {f(a)} | {f(b)} | {f(b-a)} | {pct(r['metodos']['rapido']['diag']['fracao_estrita'])} |")
        out += ["", "Mecanismos esperados e verificáveis nos caches: lines perde tabelas sem traços; text confunde colunas/listas alinhadas com uma tabela ampla; retângulos de fundo e títulos com moldura criam falsos positivos; imagens incorporadas podem ser fragmentos, máscara ou página inteira, enquanto uma figura humana reúne vários objetos; vetores não distinguem automaticamente rubrica, brasão, gráfico e ornamento. A caixa de um objeto PDF não é necessariamente a região semântica humana."]
        out += ["", "Inspeção visual em memória do PDF MS `executive_official_diary_48733_2024-11-05.pdf#p233`: a grande região humana reúne dados tabulares sem grade; o conservador deixa as palavras livres e o perfil passa a tratá-las como colunas de texto. Os rasters de cabeçalho/rodapé aparecem como candidatos a imagem. É um exemplo concreto em que 'não encontrou tabela' não autoriza dispensar o detector."]
    out += ["", "## Limitações e recomendação de desenho", "",
            "Amostra pequena do Golden e poucos exemplos de algumas classes; páginas de um mesmo veículo são dependentes. O Diamond e o Label Studio foram anotados corrigindo pré-anotação, com viés de ancoragem: a comparação pode favorecer caixas já propostas, e não é um teste independente de validade humana. Algoritmo original foi desenvolvido no Golden; LOPO antigo não apaga esse viés nem garante generalização por veículo.",
            "A régua principal isola a troca de átomos sobre palavras pdfplumber congeladas; não autoriza regenerar silver/Golden com get_text(words), cuja tokenização e altura diferem. Linhas internas de tabela são uma convenção geométrica, sem ouro independente de células. O LS não traz ordem humana neste experimento: é ouro de detecção, não de leitura. Figuras sem palavras entram na detecção, mas não produzem palavras para medir ordem.",
            "PDF digital não garante texto legível; também há texto invisível/OCR, fontes quebradas, CropBox não trivial e rotação. PDFs digitalizados exigem OCR e detecção visual para estrutura interna. Imagem de página inteira não substitui detecção de tabelas/imagens. Falhas e páginas/regiões sem palavras são contadas, sem assert ou descarte silencioso.",
            "PyMuPDF tem licenciamento AGPL ou comercial; avaliar compatibilidade antes de distribuir serviço ou código integrado. [Licença oficial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright). Esta análise não dá parecer jurídico. O material Data Policy permanece interno sob resultados/, sem cópia externa/publicação.",
            "Desenho recomendado: extrair palavras e objetos digitais primeiro; usar tabelas de grade e imagens incorporadas como candidatos rápidos; sinalizar texto ausente/ilegível, raster de página inteira, geometria contraditória, excesso de candidatos text ou evidência de alinhamentos sem grade para fallback ao detector (e OCR quando necessário). A regra 'não achou nada' sozinha é insuficiente: nenhuma tabela pode significar página textual correta ou falso negativo. Limiares de fallback precisam de validação independente e não foram ajustados neste estudo.",
            "Não é proposto um pipeline híbrido com número estimado: a recomendação é desenho futuro. Adotar o caminho rápido para palavras é uma decisão separada de retirar o detector de tabela/imagem; exigiria validar segmentação e referência. Não se editou qualquer arquivo preexistente, dado humano, quadro ou pipeline.",
            "", "## Reprodução e conferência", "",
            "```powershell", "venv/Scripts/python.exe -B orquestracao/analises/caminho_rapido_pymupdf.py --do-zero",
            "venv/Scripts/python.exe -B orquestracao/analises/caminho_rapido_pymupdf.py --conferir", "```", "",
            f"Controle sintético: {R.get('controles',{})}. Comparação com execução anterior sem cache: {R.get('reexecucao', 'primeira execução')}. Tempos naturalmente variam; a conferência exige identidade dos resultados de qualidade/ordem/alinhamento e reconstrói o Markdown dos resultados desta execução.",
            f"Hash do script: `{R.get('script_sha256','parcial')}`. Hashes de entradas e métricas por página em `resultados/caminho_rapido_pymupdf_cache/estado.json`; caches são internos e retomáveis. Relatório gerado integralmente pelo script.",""]
    return "\n".join(out)


def controles():
    """Controles significativos de coordenadas, matching e paginas/regioes vazias."""
    q=dict(ws=[],h=10,p=dict(dimensions=dict(width=600,height=800)))
    seq,diag=prever(q,[],o.Config('projecao_local_margens',.45,1.2,.08))
    if seq or diag['n_atomos']:
        raise ValueError("Página vazia tratada incorretamente")
    ps=[regiao('table',[0,0,100,100],'teste')]*2
    gs=[regiao('table',[0,0,100,100],'teste')]
    mt=comparar_regioes(ps,gs,'table')
    if (mt['tp'],mt['fp'],mt['fn'])!=(1,1,0):
        raise ValueError("Matching reutiliza caixa ouro")
    coord=[]
    for rot in (0,90,180,270):
        doc=pymupdf.open();pg=doc.new_page(width=600,height=800)
        pg.insert_text((100,120),'TESTE COORDENADA',fontsize=12)
        pg.set_cropbox(pymupdf.Rect(20,30,580,760));pg.set_rotation(rot)
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(doc.tobytes())) as pl:
            a=pl.pages[0].extract_words(use_text_flow=True)
            aa=[[w['text'],w['x0'],w['top'],w['x1'],w['bottom']] for w in a]
        bb=palavras(pg,'plumber')
        # pdfminer divide texto girado em caracteres: verifica o envelope,
        # separando o teste de coordenadas da tokenizacao dos parsers.
        ea=o.envelope([w[1:5] for w in aa]);eb=o.envelope([w[1:5] for w in bb])
        if max(abs(a-b) for a,b in zip(ea,eb))>4.5:
            raise ValueError(f"Transformação CropBox/rotação falhou: {rot}")
        coord.append(rot); doc.close()
    rs=[dict(id='vazia',bbox=[0,0,10,10],classe='figura')]
    aux=dict(ws=[],p=dict(bounding_boxes=rs),reg_words={'vazia':[]},gt_w=[],gt_r=['vazia'],
             gt_l=[],gold_lines=[])
    v=j.avaliar(aux,[])
    if v['palavras']['tau'] is not None or not v['diag']['regioes_sem_palavras']:
        raise ValueError("Região vazia premiada ou esquecida")
    ws=[['a',0,0,10,10],['b',0,20,10,30],['c',40,0,50,10],['d',40,20,50,30]]
    aux=dict(ws=ws,p=dict(bounding_boxes=[dict(id='A',bbox=[0,0,10,30]),dict(id='B',bbox=[40,0,50,30])]),
             reg_words={'A':[0,1],'B':[2,3]},gt_w=[0,1,2,3],gt_r=['A','B'],gt_l=[0,1,2,3],
             gold_lines=[dict(id=k,ks=[k],bbox=w[1:5]) for k,w in enumerate(ws)])
    intercalada=j.avaliar(aux,[0,2,1,3])
    if intercalada['regioes']['tau']!=1 or intercalada['palavras']['tau']>=1 or intercalada['diag']['fracao_estrita']!=1:
        raise ValueError('A regua principal mascarou intercalacao')
    return dict(pagina_vazia=True,regiao_vazia=True,matching_um_a_um=True,
                cropbox_com_rotacoes=coord,intercalacao_penalizada=True)


def assinatura_cientifica(R):
    """Exclui tempos da reproducibilidade; todos os numeros cientificos ficam."""
    ls=[]
    for row in R.get('ls',[]):
        # Contagem diagnostica adicionada sem mudar deteccao/alinhamento;
        # permite comparar com a primeira execucao que nao a armazenava.
        copia=dict(row,texto={k:v for k,v in row['texto'].items() if k!='regioes_sem_palavras'})
        copia['alternativas']=[{k:v for k,v in a.items() if k!='regioes_sem_palavras'} for a in row['alternativas']]
        ls.append(copia)
    return chave(dict(golden=R.get('golden'),ls=ls,
                 palavras=[dict(page_id=r['page_id'],comparacao=r['comparacao'],
                      invisiveis=r['invisiveis'],duplicatas=r['duplicatas']) for r in R.get('palavras',[])]))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--do-zero',action='store_true');ap.add_argument('--conferir',action='store_true')
    ap.add_argument('--sem-docling',action='store_true');ap.add_argument('--threads',type=int,default=2)
    args=ap.parse_args()
    estado=BASE/'estado.json';prev=ler(estado)
    if args.conferir:
        if not prev or not prev.get('concluido'):
            raise SystemExit('Não há execução completa para conferir')
        if digest(Path(__file__))!=prev.get('script_sha256'):
            raise SystemExit('Script mudou: executar antes de conferir')
        if {k:digest(RAIZ/k) for k in prev['hashes']}!=prev['hashes']:
            raise SystemExit('Entradas mudaram: executar antes de conferir')
        expected=relatorio(prev)
        if MD.read_text(encoding='utf-8')!=expected:
            raise SystemExit('Relatório diverge dos resultados executados')
        print('CONFERÊNCIA OK: Markdown idêntico aos resultados; assinatura',assinatura_cientifica(prev))
        return
    if args.threads<1:
        raise SystemExit('Threads precisa ser positivo')
    versoes={k:version(k) for k in ('PyMuPDF','numpy','scipy','pdfplumber','torch','transformers')}
    controles_ok=controles()
    qs,ls,cont,amostra,origem=preparar()
    caminhos=o.ENTRADAS+o.FONTES+[Path(o.__file__),Path(j.__file__),
             RAIZ/'src/data/palavras_pymupdf.py',RAIZ/'src/data/layout.py',RAIZ/'src/data/taxonomia_layout.py',
             RAIZ/'resultados/ordem_sem_bbox.json',RAIZ/'data/labelstudio/pdf_paginas.jsonl']
    caminhos += [RAIZ/f'data/diamond/{l}/anotacoes.jsonl' for l in ('diamond_piloto','diamond_treino')]
    caminhos += [RAIZ/f'data/labelstudio/conv_seed{s}/tarefas.jsonl' for s in range(1,5)]
    H={p.relative_to(RAIZ).as_posix():digest(p) for p in caminhos}
    codigo=''.join(inspect.getsource(x) for x in (detectar,sinais,nms,palavras,prever,comparar_palavras,auditar_texto,linha_rapida))
    ck=chave([H,versoes,codigo])
    R=dict(versoes=versoes,hashes=H,chave=ck,n_golden=len(qs),ls_catalogo=dict(cont),
           origem_palavras=origem,threads=args.threads,controles=controles_ok,concluido=False,
           palavras=[],golden=[],ls=[],tempo=[],script_sha256=digest(Path(__file__)))
    def salvar():
        gravar(estado,R);gravar(MD,relatorio(R))
    def salvar_palavras(rows):
        R['palavras']=list(rows);salvar()
    R['palavras']=auditar_palavras(amostra,args.do_zero,ck,salvar_palavras);salvar()
    for z,q in enumerate(qs):
        p=q['p'];path=RAIZ/'data/raw'/p['uf']/p['arquivo']
        key=chave([ck,digest(path),p['pagina'],'plumber'])
        raw=linha_rapida(p,path,'plumber',int(p['pagina']),key,args.do_zero)
        dets=dict(raw['det']);dets['docling']=[r for r in q['d']['detector']['regioes']
              if r.get('score',0)>=q['cfg'].score and r.get('rotulo') in ('table','picture')]
        quality={k:qualidade(v,q['det_ouro']) for k,v in dets.items()}
        base=j.baselines(q);met={'xy':base['xy_ouro'],'xy_margens':base['xy_ouro_geo']}
        for k,ds in (('docling',dets['docling']),('rapido',dets['rapido']),
                     ('rapido_text',dets['rapido_text']),('nenhum',[])):
            seq,diag=prever(q,ds,q['cfg']);met[k]=j.avaliar(q,seq);met[k]['diag'].update(diag)
            if k=='docling':
                oldseq,_,_=o.prever(q,q['cfg'])
                if oldseq!=seq:
                    raise ValueError('Reprodução LOPO difere da implementação original')
        # Diagnostico de saida realmente pura, com cobertura explicita. Nunca
        # atribui IDs de blocos humanos a palavras de outra segmentacao sem par.
        aux=dict(p=p,ws=raw['ws'],h=statistics.median(w[4]-w[2] for w in raw['ws']) if raw['ws'] else 10)
        seq,_=prever(aux,dets['rapido'],q['cfg'])
        pares=mapear_palavras(q['ws'],raw['ws']);para_ouro={k:i for i,k in pares}
        compartilhadas=set(para_ouro.values())
        gt=[k for k in q['gt_w'] if k in compartilhadas]
        elegiveis=set(gt);pred=[para_ouro[k] for k in seq if k in para_ouro and para_ouro[k] in elegiveis]
        puro=dict(metricas=j.metricas(pred,gt),referencia=len(q['gt_w']),comuns=len(gt),
                  sem_par_mupdf=len(raw['ws'])-len(pares))
        R['golden'].append(dict(page_id=p['page_id'],veiculo=p['uf'],qualidade=quality,
               metodos=met,config=q['cfg'].id,colunas=q['colunas'],auditoria=q['auditoria'],
               deteccao_erros=raw['erros'],digital=raw['digital'],puro=puro,avisos_pdf=raw.get('avisos_pdf','')))
        print(f"Golden {z+1}/{len(qs)} tau palavras PyMuPDF={f(met['rapido']['palavras']['tau'],4)}",flush=True)
        # Relatorio completo a cada pagina custa bootstrap; persistir estado sempre,
        # relatorio a cada cinco paginas e ao fim do dominio.
        gravar(estado,R)
        if (z+1)%5==0:gravar(MD,relatorio(R))
    salvar()
    for z,rec in enumerate(ls):
        p,m=rec['p'],rec['mapa'];path=RAIZ/m['pdf_local']
        if int(p['pagina'])!=int(m['pagina']):
            raise ValueError('Página convertida difere do mapa LS')
        key=chave([ck,digest(path),int(m['pagina'])-1,'visivel'])
        raw=linha_rapida(p,path,'visivel',int(m['pagina'])-1,key,args.do_zero)
        sx,sy=raw['escala_pt_px']
        gold=[regiao('table' if r['classe']=='table' else 'picture',r['bbox'],'ouro')
              for r in p.get('bounding_boxes',[]) if r.get('classe') in ('table','figure','chart','heading')
              and valido(r.get('bbox',[]))]
        pred={k:[dict(r,bbox=[r['bbox'][0]*sx,r['bbox'][1]*sy,r['bbox'][2]*sx,r['bbox'][3]*sy])
                 for r in ds] for k,ds in raw['det'].items()}
        R['ls'].append(dict(page_id=p['page_id'],seed=rec['seed'],qualidade={k:qualidade(v,gold) for k,v in pred.items()},
                **{k:raw[k] for k in ('digital','verificada','sparse','pkcs7','aspecto_erro','texto','vizinha_melhor',
                                      'indice_zero','escala_pt_px','rotacao','cropbox','mediabox','alternativas','erros')}))
        R['ls'][-1]['avisos_pdf']=raw.get('avisos_pdf','')
        R['ls'][-1]['raster_pagina']=raw.get('raster_pagina',False)
        if (z+1)%10==0 or z+1==len(ls):
            print(f"LS {z+1}/{len(ls)}, digitais={sum(r['digital'] for r in R['ls'])}, verificadas={sum(r['verificada'] for r in R['ls'])}",flush=True)
            salvar()
        else:gravar(estado,R)
    def salvar_tempos(rows):
        R['tempo']=list(rows);gravar(estado,R)
        if len(rows)==1 or len(rows)%5==0:
            gravar(MD,relatorio(R))
    R['tempo']=benchmark(qs,R['golden'],args.do_zero,ck,args.threads,args.sem_docling,salvar_tempos)
    if {k:digest(RAIZ/k) for k in H}!=H:
        raise ValueError('Entradas mudaram durante a execução; resultados não são congelados')
    R['concluido']=True
    if args.do_zero and prev and prev.get('concluido'):
        if assinatura_cientifica(prev)!=assinatura_cientifica(R):
            R['reexecucao']='DIVERGÊNCIA de qualidade/ordem/alinhamento: investigar antes de interpretar'
            salvar();raise SystemExit(R['reexecucao'])
        R['reexecucao']='OK: qualidade, ordem e auditorias idênticas à execução anterior; tempos medidos novamente.'
    salvar()
    print('CONCLUÍDO',MD.relative_to(RAIZ),flush=True)
    print('\n'.join(tabela_ordem(R['golden'],'palavras')))
    print('\n'.join(tabela_tempo(R['tempo'])))


if __name__=='__main__':
    main()
