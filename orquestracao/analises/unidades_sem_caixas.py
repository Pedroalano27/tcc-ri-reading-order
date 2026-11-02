"""Exporta unidades sem caixas finas no contrato dos ordenadores do TCC.

Reutiliza as representacoes existentes, o extrator canonico e a regua de
palavras de erros_ponta_a_ponta. A silver usa o fluxo POR PALAVRA do PDF;
supervisao humana e isolada das pastas de treino. Nada e gravado em data/.
Um processo, uma pagina por vez, detector CPU/offline, caches atomicos e
exportacao em fluxo permitem retomar depois de queda sem reabrir os PDFs.

Uso da amostra: venv/Scripts/python.exe -B
orquestracao/analises/unidades_sem_caixas.py --limite-treino 60
Restante: mesmo comando com --limite-treino 0 (zero significa completo).
--conferir audita caches, arquivos exportados e compatibilidade, sem inferir.
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
import ctypes
import gc
import hashlib
import json
import math
import os
import random
import statistics
import time

# Antes de importar bibliotecas que possam inicializar modelos/threads.
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", YOLO_OFFLINE="true",
                  YOLO_CONFIG_DIR=str(RAIZ), OMP_NUM_THREADS="4",
                  MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4")
from orquestracao.analises import erros_ponta_a_ponta as e
from src.data.dataset_sem_caixas_finas import representar
from src.data.estruturas_pagina import representar_estruturas
from src.eval.protocolo import ordem_entrada

OUT = RAIZ / "resultados/unidades_sem_caixas"
MD = RAIZ / "resultados/unidades_sem_caixas.md"
REPS = ("linhas", "colunas", "colunas_margens")
SEMENTE = 20261004
VERSAO = "unidades-v1"
MODELO = None
HASHES_PDF = {}


def exigir(cond, mensagem):
    if not cond:
        raise ValueError(mensagem)


def ler(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        for l in f:
            if l.strip():
                yield json.loads(l)


def gravar(path, obj):
    path = Path(path).resolve()
    exigir(OUT.resolve() in path.parents or path == MD.resolve(),
           f"Destino fora do escopo: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha(path):
    return e.ac.sha(path)


def digest(obj):
    return e.ac.digest(obj)


def rel(path):
    return Path(path).relative_to(RAIZ).as_posix()


def memoria():
    """Pico do processo via API Windows, sem WMI/processos auxiliares."""
    from ctypes import wintypes
    class Contadores(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (k, ctypes.c_size_t) for k in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
            "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
    class Estado(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] + [
            (k, ctypes.c_ulonglong) for k in ("ullTotalPhys", "ullAvailPhys",
            "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual",
            "ullAvailVirtual", "ullAvailExtendedVirtual")]
    c, m = Contadores(), Estado()
    c.cb, m.dwLength = ctypes.sizeof(c), ctypes.sizeof(m)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    exigir(psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb),
           "Nao foi possivel medir memoria do processo")
    exigir(kernel.GlobalMemoryStatusEx(ctypes.byref(m)), "Nao foi possivel medir RAM livre")
    return {"pico_rss_mb": c.PeakWorkingSetSize / 2**20,
            "pico_commit_mb": c.PeakPagefileUsage / 2**20,
            "rss_mb": c.WorkingSetSize / 2**20,
            "ram_livre_mb": m.ullAvailPhys / 2**20}


def indice(path):
    """Guarda apenas metadados/offsets; nunca todas as palavras ou caixas."""
    out = {}
    with open(path, "rb") as f:
        while True:
            offset = f.tell()
            l = f.readline()
            if not l:
                break
            if not l.strip():
                continue
            p = json.loads(l.decode("utf-8"))
            pid = p["page_id"]
            exigir(pid not in out, f"page_id duplicado: {path}: {pid}")
            out[pid] = {k: p[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions")}
            out[pid].update(path=rel(path), offset=offset)
    return out


def pagina(m):
    with open(RAIZ / m["path"], "rb") as f:
        f.seek(m["offset"])
        p = json.loads(f.readline().decode("utf-8"))
    exigir(p["page_id"] == m["page_id"], "A fonte mudou durante a execucao")
    return p


def montar_plano(limite):
    splits = ler(RAIZ / "data/processed/splits.json")
    grupos = [set(splits[k]) for k in ("treino", "validacao", "teste")]
    exigir(not any(a & b for i, a in enumerate(grupos) for b in grupos[i+1:]),
           "Veiculo em mais de uma particao")
    h4 = indice(RAIZ / "data/golden/golden_v4/tarefas.jsonl")
    h3 = indice(RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl")
    a4 = {a["page_id"]: a for a in jsonl(e.o.ENTRADAS[1]) if a.get("status") == "concluida"}
    a3 = {a["page_id"]: a for a in jsonl(RAIZ / "data/golden/_avaliacao/golden_v3/referencia.jsonl")
          if a.get("status") == "concluida"}
    bench = {**{pid: ("golden_v4", h4[pid], a) for pid, a in a4.items()},
             **{pid: ("golden_v3_novo", h3[pid], a) for pid, a in a3.items() if pid not in h4}}
    exigir(collections.Counter(x[0] for x in bench.values()) ==
           {"golden_v4": 44, "golden_v3_novo": 27}, "Bancadas nao correspondem a 44 + 27 paginas")
    humanos_todos = set(h4) | set(h3)
    diamond = {}
    for lote in ("diamond_piloto", "diamond_treino"):
        diamond.update({pid: m for pid, m in indice(RAIZ / f"data/diamond/{lote}/tarefas.jsonl").items()
                        if pid in h4})
    plano = []
    for coorte in ("golden_v4", "golden_v3_novo"):
        for pid in sorted(bench):
            c, m, _ = bench[pid]
            if c == coorte:
                plano.append({**m, "particao": c, "colecao": "bancadas"})
    todos, excluidos = [], []
    fontes = set()
    for colecao in ("blocos", "blocos_extra"):
        partes = ("validacao", "teste", "treino") if colecao == "blocos" else ("treino_extra",)
        for part in partes:
            ms = []
            for uf in splits["treino" if part == "treino_extra" else part]:
                path = RAIZ / "data/processed" / colecao / (uf + ".jsonl")
                exigir(path.exists(), f"Fonte obrigatoria ausente: {path}")
                fontes.add(path)
                for m in indice(path).values():
                    exigir(m["uf"] == uf, f"Veiculo errado em {path}")
                    m.update(particao=part, colecao=colecao)
                    if part.startswith("treino") and m["page_id"] in humanos_todos:
                        excluidos.append(m["page_id"])
                    else:
                        ms.append(m)
            ms.sort(key=lambda m: m["page_id"])
            if part.startswith("treino"):
                random.Random(SEMENTE).shuffle(ms)
            todos += ms
    # Preservar as duas colecoes originais. montar_treino ja deduplica entre
    # base e extra; o exportador nao pode alterar a lista de paginas extras.
    base_ids = {m["page_id"] for m in todos if m["particao"] == "treino"}
    repetidos_extra = [m["page_id"] for m in todos if m["particao"] == "treino_extra" and m["page_id"] in base_ids]
    ntreino = 0
    for m in todos:
        if m["particao"].startswith("treino"):
            if limite and ntreino >= limite:
                continue
            ntreino += 1
        plano.append(m)
    paths = fontes | {RAIZ / "data/processed/splits.json", Path(__file__), e.ls.PESOS,
        RAIZ / "data/golden/golden_v4/tarefas.jsonl", e.o.ENTRADAS[1],
        RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl",
        RAIZ / "data/golden/_avaliacao/golden_v3/referencia.jsonl"}
    paths |= {RAIZ / f"data/diamond/{l}/tarefas.jsonl" for l in ("diamond_piloto", "diamond_treino")}
    paths |= {Path(mod.__file__) for mod in (e, e.o, e.j, e.ls, e.ac, e.extrator, e.layout)}
    paths |= {RAIZ / n for n in ("src/data/dataset_sem_caixas_finas.py", "src/data/estruturas_pagina.py",
              "src/data/regioes.py", "src/eval/protocolo.py", "src/eval/politica_margens.py",
              "src/eval/baselines.py", "src/eval/metrics.py", "src/ri/piloto_japeri.py")}
    hashes = {rel(p): sha(p) for p in sorted(paths)}
    fp = digest([VERSAO, hashes])
    anteriores = {fp}
    anterior = ler(OUT / "manifesto.json") if (OUT / "manifesto.json").exists() else None
    # VERSAO identifica a receita de unidades/rotulos e deve mudar caso ela
    # mude. Ajustes de inventario, retomada e relatorio nao refazem inferencia
    # nem descartam medicoes originais com as mesmas fontes e a mesma receita.
    gerador = rel(Path(__file__))
    if anterior and anterior.get("versao") == VERSAO:
        fontes_antigas = {k: v for k, v in anterior["hashes"].items() if k != gerador}
        fontes_atuais = {k: v for k, v in hashes.items() if k != gerador}
        if fontes_antigas == fontes_atuais:
            anteriores.add(anterior["fingerprint"])
    return {"splits": splits, "bench": bench, "h4": h4, "diamond": diamond,
            "humanos_todos": humanos_todos, "plano": plano, "todos_silver": todos,
            "excluidos_treino": sorted(set(excluidos)), "duplicatas_extra": repetidos_extra,
            "hashes": hashes, "fingerprint": fp, "fingerprints_compativeis": anteriores,
            "manifesto_anterior": anterior}


def canonico(m, contexto):
    """Preferencia pelas palavras congeladas; os demais caches sao somente leitura."""
    pid = m["page_id"]
    if pid in contexto["h4"]:
        d = pagina(contexto["diamond"][pid])
        return d["palavras"], d["dimensions"], contexto["diamond"][pid]["path"], d
    cache = e.ac.CACHE / "palavras" / (e.ac.chave(pid) + ".json")
    if cache.exists():
        obj = ler(cache)
        exigir(not obj.get("erro") and obj["page_id"] == pid, f"Cache invalido: {cache}")
        # O mesmo fingerprint empregado pelo extrator que produziu o cache.
        pdf = RAIZ / "data/raw" / m["uf"] / m["arquivo"]
        hash_pdf = hash_do_pdf(pdf)
        esperado = digest([e.ac.VERSAO, hash_pdf, sha(Path(e.extrator.__file__)), m["pagina"]])
        exigir(obj.get("fingerprint") == esperado, f"Cache canonico desatualizado: {cache}")
        return obj["palavras"], obj["dimensions"], rel(cache), None
    exigir(m["particao"] != "golden_v3_novo", f"Faltam palavras congeladas do v3: {pid}")
    pdf = RAIZ / "data/raw" / m["uf"] / m["arquivo"]
    fp = digest([hash_do_pdf(pdf), sha(Path(e.extrator.__file__)), m["pagina"]])
    destino = OUT / "cache/palavras" / (e.ac.chave(pid) + ".json")
    if destino.exists():
        obj = ler(destino)
        exigir(obj["fingerprint"] == fp, f"Cache novo incompatível: {destino}")
        return obj["palavras"], obj["dimensions"], rel(destino), None
    import pdfplumber
    with pdfplumber.open(pdf) as doc:
        page = doc.pages[m["pagina"]]
        ws = e.extrator.palavras_da_pagina(page)
        exigir(all(a["s"] < b["s"] for a, b in zip(ws, ws[1:])), "Fluxo de palavras nao monotono")
        obj = {"page_id": pid, "fingerprint": fp,
               "dimensions": {"width": float(page.width), "height": float(page.height)},
               "palavras": [[w["t"], w["x0"], w["top"], w["x1"], w["bottom"]] for w in ws],
               "postos_fluxo_pdf": [w["s"] for w in ws]}
        page.close()
    gravar(destino, obj)
    return obj["palavras"], obj["dimensions"], rel(destino), None


def hash_do_pdf(path):
    k = str(path)
    if k not in HASHES_PDF:
        HASHES_PDF[k] = sha(path)
    return HASHES_PDF[k]


def imagem_bancada(m, contexto):
    pid = m["page_id"]
    if pid in contexto["h4"]:
        p = pagina(contexto["h4"][pid])
        return RAIZ / "data/golden/golden_v4/img" / p["imagem"]
    if pid in contexto["bench"]:
        p = pagina(contexto["bench"][pid][1])
        lote = "golden_v1" if str(p.get("origem", "")).startswith("golden_v1") else "golden_v2"
        return RAIZ / "data/golden" / lote / "img" / p["imagem"]
    return None


def detector(m, contexto):
    """P2: mesmos pesos, renderizacao, NMS e escala; inferencia so em CPU."""
    global MODELO
    pid = m["page_id"]
    img = imagem_bancada(m, contexto)
    peso = contexto["hashes"][rel(e.ls.PESOS)]
    caminho = OUT / "cache/detector" / (e.ac.chave(pid) + ".json")
    meta = {"peso": peso, "dimensions": m["dimensions"], "imgsz": 1024,
            "conf": .25, "iou": .7, "max_det": 300, "device": "cpu"}
    if img:
        meta["imagem"] = sha(img)
    else:
        meta.update(pdf=hash_do_pdf(RAIZ / "data/raw" / m["uf"] / m["arquivo"]),
                    pagina=m["pagina"], dpi=e.layout.DPI)
    fp = digest(meta)
    if caminho.exists():
        salvo = ler(caminho)
        exigir(salvo["fingerprint"] == fp, f"Detector em cache incompatível: {pid}")
        return salvo["regioes"], rel(caminho)
    antigo = e.BASE / "detector" / (e.ac.chave(pid) + ".json")
    if img and antigo.exists():
        salvo = ler(antigo)
        if salvo.get("fingerprint") == fp:
            gravar(caminho, {**salvo, "origem": rel(antigo)})
            return salvo["regioes"], rel(antigo)
    if img is None:
        # Renderizador canonico do P2, sem OCR ou troca de extrator.
        import pdfplumber
        img = OUT / "cache/imagens" / (e.ac.chave(pid) + ".png")
        if not img.exists():
            img.parent.mkdir(parents=True, exist_ok=True)
            with pdfplumber.open(RAIZ / "data/raw" / m["uf"] / m["arquivo"]) as doc:
                page = doc.pages[m["pagina"]]
                pi = page.to_image(resolution=e.layout.DPI)
                exigir(max(abs(v) for v in pi.bbox[:2]) < .11,
                       f"CropBox deslocada: escala P2 nao e aplicavel a {pid}")
                exigir(max(abs(pi.bbox[2]-page.width), abs(pi.bbox[3]-page.height)) < .11,
                       f"Imagem nao cobre pagina inteira: {pid}")
                tmp_img = img.with_suffix(".png.tmp")
                pi.original.convert("RGB").save(tmp_img, format="PNG")
                os.replace(tmp_img, img)
                page.close()
    if MODELO is None:
        import torch
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        from ultralytics import YOLO
        from ultralytics.utils import SETTINGS
        dict.__setitem__(SETTINGS, "sync", False)
        MODELO = YOLO(str(e.ls.PESOS)).to("cpu")
    from PIL import Image
    with Image.open(img) as im:
        wpx, hpx = im.size
    pred = MODELO.predict(str(img), device="cpu", imgsz=1024, conf=.25, iou=.7,
                          max_det=300, verbose=False, save=False, save_txt=False)[0]
    exigir(tuple(pred.orig_shape) == (hpx, wpx), "Dimensoes da imagem inconsistentes")
    sx, sy = m["dimensions"]["width"] / wpx, m["dimensions"]["height"] / hpx
    regs = []
    for b in pred.boxes:
        cls = pred.names[int(b.cls.item())]
        exigir(cls in ("texto", "tabela", "imagem"), "Peso nao e ls3")
        x0, y0, x1, y1 = map(float, b.xyxy[0].tolist())
        regs.append({"id": f"d{len(regs)}", "classe": cls, "score": float(b.conf.item()),
                     "bbox": [x0*sx, y0*sy, x1*sx, y1*sy]})
    gravar(caminho, {"fingerprint": fp, "meta": meta, "regioes": regs, "origem": "CPU"})
    return regs, "CPU"


def referencia_humana(m, ws, d, contexto):
    p = pagina(m)
    ann = contexto["bench"][m["page_id"]][2]
    q, aud = e.ac.preparar({"p": p, "gt": ann["ordem"]},
                         {"palavras": ws, "dimensions": p["dimensions"]}, [])
    exigir(q is not None, f"Referencia humana incompativel: {m['page_id']}: {aud}")
    if d is not None:
        q["d"] = d
    return q


def ancora(contexto):
    """Reexecuta preditores e medir(), sem reutilizar numeros de relatorios."""
    rows = []
    for m in contexto["plano"]:
        if m["particao"] != "golden_v4":
            continue
        destino = OUT / "cache/ancoras" / (e.ac.chave(m["page_id"]) + ".json")
        if destino.exists():
            r = ler(destino)
            exigir(r["fingerprint"] in contexto["fingerprints_compativeis"], "Ancora desatualizada")
            if r["fingerprint"] != contexto["fingerprint"]:
                r.setdefault("medicao_fingerprint", r["fingerprint"])
                r["fingerprint"] = contexto["fingerprint"]
                gravar(destino, r)
        else:
            ws, dim, _, d = canonico(m, contexto)
            exigir(dim == m["dimensions"], "Dimensoes canonicas v4 diferentes")
            q = referencia_humana(m, ws, d, contexto)
            q["ls3"], _ = detector(m, contexto)
            auto = e.automatico(q)
            resultados = {"P2": e.ls.prever(auto, e.FIXA, "ls3"),
                          "P1m": e.prever_p1(auto)["P1m"]}
            r = {"fingerprint": contexto["fingerprint"], "page_id": m["page_id"], "metodos": {}}
            for nome, (seq, itens, diag) in resultados.items():
                med = e.medir(q, seq, itens, diag, nome)
                r["metodos"][nome] = {k: med[k] for k in ("tau", "quebras", "fid12", "sucessor_linhas")}
            gravar(destino, r)
        rows.append(r)
        print(f"[ancoras {len(rows)}/44] {m['page_id']}", flush=True)
    resumo = {nome: {k: statistics.mean(r["metodos"][nome][k] for r in rows)
                     for k in ("tau", "quebras", "fid12", "sucessor_linhas")} for nome in ("P2", "P1m")}
    exigir(len(rows) == 44, "Ancora incompleta")
    ok = abs(resumo["P2"]["tau"] - .986) <= .006 and abs(resumo["P1m"]["tau"] - .952) <= .006
    # Quebras sao contagens exatas; tolerancia apenas do arredondamento publicado.
    ok = ok and abs(resumo["P2"]["quebras"] - 6.05) <= .0051 and abs(resumo["P1m"]["quebras"] - 8.93) <= .0051
    resultado = {"paginas": len(rows), "aprovada": ok, "metodos": resumo,
                 "fingerprint": contexto["fingerprint"], "paginas_medidas": rows}
    gravar(OUT / "ancoras.json", resultado)
    exigir(ok, f"PARE: ancora nao reproduzida: {resumo}")
    return resultado


def converter(m, r, ws, gt):
    """Compatibilidade de esquema; postos medianos so sao rotulos de unidades."""
    unidades = r["unidades"]
    exigir(sorted(k for u in unidades for k in u["ks"]) == list(range(len(ws))),
           f"Palavra perdida/repetida: {m['page_id']}")
    exigir(len(gt) == len(set(gt)) and set(gt) <= set(range(len(ws))), "Referencia de palavras invalida")
    postos = {k: i for i, k in enumerate(gt)}
    exigir(postos, f"Pagina sem palavras com referencia: {m['page_id']}")
    perm = list(range(len(unidades)))
    random.Random(f"ids-{m['page_id']}-{r['representacao']}").shuffle(perm)
    caixas = []
    for u, num in zip(unidades, perm):
        ranks = sorted(postos[k] for k in u["ks"] if k in postos)
        med = statistics.median(ranks) if ranks else None
        if med is None:
            cx, cy = (u["bbox"][0]+u["bbox"][2])/2, (u["bbox"][1]+u["bbox"][3])/2
            k = min(postos, key=lambda k: ((e.o.centro(ws[k])[0]-cx)**2 +
                                          (e.o.centro(ws[k])[1]-cy)**2, k))
            posto = postos[k]
        else:
            posto = med
        caixas.append({"id": f"b{num}", "text": u["text"], "bbox": u["bbox"],
                       "ks": u["ks"], "tipo": {"table": "tabela", "picture": "imagem"}.get(u["tipo"], u["tipo"]),
                       "posto_mediano_referencia": med, "posto_referencia": posto,
                       "n_palavras_referencia": len(ranks),
                       "referencia_unidade": "mediana" if ranks else "vizinho_geometrico_sem_palavras_ouro"})
    key = lambda c: (c["posto_referencia"], c["bbox"][1], c["bbox"][0], c["id"])
    ordenadas = sorted(caixas, key=key)
    com_ref = [c for c in ordenadas if c["n_palavras_referencia"]]
    ranksets = [[postos[k] for k in c["ks"] if k in postos] for c in com_ref]
    for i, (c, rs) in enumerate(zip(com_ref, ranksets)):
        prev = max(ranksets[i-1]) if i else -math.inf
        prox = min(ranksets[i+1]) if i+1 < len(ranksets) else math.inf
        ruins = sum(k < prev or k > prox for k in rs)
        c.update(n_palavras_fora_ordem_vizinha=ruins, fracao_fora_ordem_vizinha=ruins/len(rs),
                 atravessa_referencia=ruins > 0)
    for c in caixas:
        if not c["n_palavras_referencia"]:
            c.update(n_palavras_fora_ordem_vizinha=0, fracao_fora_ordem_vizinha=None,
                     atravessa_referencia=False)
    caixas.sort(key=lambda c: int(c["id"][1:]))
    p = {k: m[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions")}
    p.update(bounding_boxes=caixas, representacao="colunas_margens" if r["representacao"] == "colunas_estruturas" else r["representacao"],
             particao=m["particao"], referencia_palavras_tipo="humana_expandida" if m["colecao"] == "bancadas" else "fluxo_pdf_por_palavra",
             ordens={"stream": [c["id"] for c in ordenadas],
                     "naive": [c["id"] for c in sorted(caixas, key=lambda c: (c["bbox"][1], c["bbox"][0], c["id"]))]},
             stats={"n_blocos": len(caixas), "n_palavras": len(ws),
                    "prop_cid": sum(bool(e.extrator.RE_CID.search(w[0])) for w in ws)/max(1, len(ws)),
                    "n_colunas": r["colunas"]["n_estimado"],
                    "n_tabelas": sum(c["tipo"] == "tabela" for c in caixas), "layout": True,
                    "n_unidades_atravessam": sum(c["atravessa_referencia"] for c in caixas),
                    "n_unidades_com_referencia": len(com_ref),
                    "n_palavras_com_referencia": len(gt)},
             ordem_interna="ks devolvidos por representar/representar_estruturas")
    p["ordens"]["xycut"] = [caixas[i]["id"] for i in e.o.xycut(ordem_entrada(p), e.o.boxes(caixas))]
    auditar_pagina(p, len(ws))
    return p


def auditar_pagina(p, n):
    cs = p["bounding_boxes"]
    ids = {c["id"] for c in cs}
    exigir(len(ids) == len(cs) and len(cs) > 0, "IDs invalidos/unidades vazias")
    exigir(sorted(k for c in cs for k in c["ks"]) == list(range(n)), "Integridade das palavras falhou")
    for nome, ordem in p["ordens"].items():
        exigir(len(ordem) == len(ids) and set(ordem) == ids, f"Ordem {nome} nao e permutacao")
    for c in cs:
        exigir(len(c["bbox"]) == 4 and all(math.isfinite(v) for v in c["bbox"]), "bbox invalida")
        exigir(c["bbox"][2] >= c["bbox"][0] and c["bbox"][3] >= c["bbox"][1], "bbox invertida")
        exigir(isinstance(c["text"], str), "Texto invalido")


def cache_pagina(m):
    return OUT / "cache/paginas" / m["particao"] / (e.ac.chave(m["page_id"]) + ".json")


def processar(m, contexto):
    destino = cache_pagina(m)
    if destino.exists():
        obj = ler(destino)
        exigir(obj["fingerprint"] in contexto["fingerprints_compativeis"], f"Cache de pagina desatualizado: {destino}")
        for p in obj["representacoes"].values():
            auditar_pagina(p, len(obj["palavras"]))
        if obj["fingerprint"] != contexto["fingerprint"]:
            obj.setdefault("medicao_fingerprint", obj["fingerprint"])
            obj["fingerprint"] = contexto["fingerprint"]
            gravar(destino, obj)
        return obj, True
    mem = memoria()
    exigir(mem["ram_livre_mb"] > 350, f"RAM livre insuficiente: {mem}; retome mais tarde")
    t = time.perf_counter()
    ws, dim, fonte, d = canonico(m, contexto)
    exigir(max(abs(dim[k]-m["dimensions"][k]) for k in ("width", "height")) <= .11,
           f"Dimensoes de palavras incompativeis: {m['page_id']}")
    regs, origem_det = detector(m, contexto)
    base = {k: m[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions")}
    base.update(palavras=ws, detector={"modelo": "ls3", "regioes": e.ls.dets({"ls3": regs}, "ls3")})
    humanas = m["colecao"] == "bancadas"
    q = referencia_humana(m, ws, d, contexto) if humanas else None
    # palavras_da_pagina devolve a lista ordenada pelo indice s (use_text_flow).
    gt = q["gt_w"] if humanas else list(range(len(ws)))
    linhas, colunas = representar(base)
    _, margens = representar_estruturas(base)
    reps = {nome: converter(m, r, ws, gt) for nome, r in zip(REPS, (linhas, colunas, margens))}
    obj = {"fingerprint": contexto["fingerprint"], **{k: m[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "particao")},
           "palavras": ws, "gt_w": gt, "referencia_palavras": gt,
           "origem_palavras": fonte, "origem_detector": origem_det,
           "veiculo_visto_treino": m["uf"] in contexto["splits"]["treino"],
           "representacoes": reps, "tempo_s": time.perf_counter()-t, "memoria": memoria()}
    if humanas:
        obj.update({k: q[k] for k in ("gt_r", "gt_l", "reg_words", "gold_lines")})
    gravar(destino, obj)
    return obj, False


def percentil(xs, p):
    xs = sorted(xs)
    i = (len(xs)-1)*p
    a = int(i)
    return xs[a] + (xs[min(a+1, len(xs)-1)]-xs[a])*(i-a)


def exportar(contexto, feitos):
    """Transacao por arquivo: escreve shards sem juntar paginas em memoria."""
    destinos = collections.defaultdict(list)
    for m in feitos:
        if m["colecao"] == "bancadas":
            destinos[OUT / "bancadas" / (m["particao"] + ".jsonl")].append((m, None, False))
        else:
            for rep in REPS:
                pasta = rep + ("_extra" if m["colecao"] == "blocos_extra" else "")
                destinos[OUT / pasta / (m["uf"] + ".jsonl")].append((m, rep, False))
                destinos[OUT / pasta / (m["uf"] + ".palavras.jsonl")].append((m, rep, True))
    for destino, entradas in destinos.items():
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(destino.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            for m, rep, palavras in entradas:
                obj = ler(cache_pagina(m))
                if rep is None:
                    row = {k: v for k, v in obj.items() if k != "fingerprint"}
                elif palavras:
                    row = {k: obj[k] for k in ("page_id", "palavras", "gt_w", "origem_palavras")}
                    row["referencia_palavras_tipo"] = "fluxo_pdf_por_palavra"
                else:
                    row = obj["representacoes"][rep]
                f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        # No Windows não se troca um arquivo que outro processo está lendo (a bancada lê as bancadas e o
        # teste enquanto a exportação do treino publica): conteúdo igual não é regravado; o resto espera.
        if destino.exists() and destino.stat().st_size == tmp.stat().st_size \
                and hashlib.sha256(destino.read_bytes()).digest() == hashlib.sha256(tmp.read_bytes()).digest():
            tmp.unlink()
            continue
        for tentativa in range(90):
            try:
                os.replace(tmp, destino)
                break
            except PermissionError:
                if tentativa == 89:
                    raise
                time.sleep(2)


def verificar(contexto, feitos, final):
    humano = contexto["humanos_todos"]
    for rep in REPS:
        for extra in (False, True):
            pasta = OUT / (rep + ("_extra" if extra else ""))
            for uf in contexto["splits"]["treino"]:
                path = pasta / (uf+".jsonl")
                if path.exists():
                    for p in jsonl(path):
                        exigir(p["uf"] == uf and p["page_id"] not in humano,
                               f"Vazamento da bancada/veiculo no treino: {path}: {p['page_id']}")
            for part in ("validacao", "teste", "treino", "treino_extra"):
                if (part == "treino_extra") != extra:
                    continue
                ufs = contexto["splits"]["treino" if extra else part]
                esperado = [m["page_id"] for m in feitos if m["particao"] == part]
                real = []
                por_id = {m["page_id"]: m for m in feitos if m["particao"] == part}
                for uf in ufs:
                    path = pasta / (uf+".jsonl")
                    if path.exists():
                        for p in jsonl(path):
                            pid = p["page_id"]
                            exigir(pid in por_id, f"Pagina nao selecionada: {path}: {pid}")
                            obj = ler(cache_pagina(por_id[pid]))
                            auditar_pagina(p, len(obj["palavras"]))
                            exigir(p == obj["representacoes"][rep], f"Exportacao difere do cache: {path}: {pid}")
                            real.append(pid)
                        words_path = pasta / (uf+".palavras.jsonl")
                        words_ids = []
                        for row in jsonl(words_path):
                            pid = row["page_id"]
                            exigir(pid in por_id, f"Palavras de pagina nao selecionada: {words_path}")
                            obj = ler(cache_pagina(por_id[pid]))
                            exigir(row["palavras"] == obj["palavras"] and row["gt_w"] == obj["gt_w"],
                                   f"Palavras/referencia exportadas diferem do cache: {words_path}: {pid}")
                            words_ids.append(pid)
                        exigir(words_ids == [p["page_id"] for p in jsonl(path)],
                               f"Arquivo irmao de palavras incompleto: {words_path}")
                exigir(sorted(real) == sorted(esperado), f"page_ids exportados divergentes: {rep}/{part}")
                original = [m["page_id"] for m in contexto["todos_silver"] if m["particao"] == part]
                if final and (part in ("validacao", "teste") or len(esperado) == len(original)):
                    exigir(sorted(real) == sorted(original), f"Particao original incompleta: {part}")
    for coorte in ("golden_v4", "golden_v3_novo"):
        esperado = {m["page_id"]: m for m in feitos if m["particao"] == coorte}
        path = OUT / "bancadas" / (coorte+".jsonl")
        real = []
        if path.exists():
            for row in jsonl(path):
                pid = row["page_id"]
                exigir(pid in esperado, f"Pagina humana nao selecionada: {path}")
                obj = ler(cache_pagina(esperado[pid]))
                exigir(row == {k: v for k, v in obj.items() if k != "fingerprint"},
                       f"Bancada exportada difere do cache: {path}: {pid}")
                real.append(pid)
        exigir(sorted(real) == sorted(esperado), f"Bancada incompleta: {coorte}")
    # Importacao literal do contrato, sem inicializar outro processo pesado.
    from src.eval import protocolo
    antigo = protocolo.DIR_BLOCOS
    try:
        protocolo.DIR_BLOCOS = str(OUT / "colunas")
        n = len(protocolo.carregar_particao("validacao"))
    finally:
        protocolo.DIR_BLOCOS = antigo
    if final:
        exigir(n == sum(m["particao"] == "validacao" for m in contexto["todos_silver"]),
               "protocolo.carregar_particao nao le todas as paginas de validacao")
    return {"integridade_palavras": True, "sem_vazamento_treino": True,
            "page_ids_exportados": True, "validacao_teste_completas": final,
            "protocolo_validacao_paginas": n}


def fmt(x, n=2):
    return f"{x:.{n}f}".replace(".", ",")


def relatorio(contexto, feitos, anc, final, verificacoes, execucao):
    grupos = collections.defaultdict(lambda: {"ns": [], "unidades": 0, "com_ref": 0,
                    "atravessam": 0, "palavras": 0, "palavras_ruins": 0, "sem_ref": 0})
    tempos = collections.defaultdict(list)
    pico_rss, pico_commit = execucao["memoria"]["pico_rss_mb"], execucao["memoria"]["pico_commit_mb"]
    vistos = collections.Counter()
    for m in feitos:
        obj = ler(cache_pagina(m))
        tempos[m["particao"]].append(obj["tempo_s"])
        pico_rss = max(pico_rss, obj["memoria"]["pico_rss_mb"])
        pico_commit = max(pico_commit, obj["memoria"]["pico_commit_mb"])
        if m["colecao"] == "bancadas":
            vistos[(m["particao"], obj["veiculo_visto_treino"])] += 1
        estratos = [m["particao"]]
        if m["colecao"] == "bancadas":
            estratos.append(m["particao"] + ("_veiculos_vistos" if obj["veiculo_visto_treino"] else "_veiculos_nao_vistos"))
        for rep, p in obj["representacoes"].items():
            for estrato in estratos:
                g = grupos[(estrato, rep)]
                g["ns"].append(len(p["bounding_boxes"]))
                for c in p["bounding_boxes"]:
                    g["unidades"] += 1
                    g["com_ref"] += c["n_palavras_referencia"] > 0
                    g["sem_ref"] += c["n_palavras_referencia"] == 0
                    g["atravessam"] += c["atravessa_referencia"]
                    g["palavras"] += c["n_palavras_referencia"]
                    g["palavras_ruins"] += c["n_palavras_fora_ordem_vizinha"]
    stats = []
    for (part, rep), g in sorted(grupos.items()):
        ns = g.pop("ns")
        stats.append({"particao": part, "representacao": rep, "paginas": len(ns), **g,
                      "mediana": statistics.median(ns), "p90": percentil(ns, .9), "maximo": max(ns),
                      "paginas_acima_510": sum(n > 510 for n in ns),
                      "fracao_atravessam": g["atravessam"]/max(1, g["com_ref"]),
                      "fracao_palavras_fora": g["palavras_ruins"]/max(1, g["palavras"])})
    contagens = dict(collections.Counter(m["particao"] for m in feitos))
    universo = dict(collections.Counter(m["particao"] for m in contexto["todos_silver"]))
    amostra_t = [t for k, ts in tempos.items() if k.startswith("treino") for t in ts]
    restantes = sum(v for k, v in universo.items() if k.startswith("treino"))-len(amostra_t)
    media = statistics.mean(amostra_t) if amostra_t else None
    estado = {"versao": VERSAO, "final_amostra": final, "ancoras": anc,
              "contagens": contagens, "universo_silver": universo,
              "excluidos_treino": contexto["excluidos_treino"], "duplicatas_base_extra_preservadas": contexto["duplicatas_extra"],
              "hashes": contexto["hashes"], "fingerprint": contexto["fingerprint"],
              "estatisticas": stats, "verificacoes": verificacoes, "execucao": execucao,
              "pico_rss_mb": pico_rss, "pico_commit_mb": pico_commit,
              "tempos": {k: {"paginas": len(v), "media_s": statistics.mean(v),
                           "mediana_s": statistics.median(v), "p90_s": percentil(v, .9), "max_s": max(v)}
                         for k, v in tempos.items()},
              "paginas_unicas": len({m["page_id"] for m in feitos}),
              "historico_execucoes": sorted(rel(p) for p in (OUT / "cache/execucoes").glob("*.json")),
              "estimativa_restante": {"paginas": restantes, "media_amostra_treino_s": media,
                                    "segundos": media*restantes if media is not None else None}}
    gravar(OUT / "manifesto.json", estado)
    l = ["# Unidades sem caixas finas — exportação para os ordenadores", "",
         f"Estado: {'amostra solicitada concluída' if final else 'execução parcial, retomável'}. CPU, um processo, páginas em fluxo; sem treino de ordenador nesta tarefa.", "",
         "Âncoras reexecutadas com os preditores P2/P1m e `erros_ponta_a_ponta.medir`, antes da exportação:", "",
         "| Pipeline, golden_v4 | Páginas | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |",
         "|---|---:|---:|---:|---:|---:|"]
    for nome in ("P2", "P1m"):
        a = anc["metodos"][nome]
        l.append(f"| {nome} | {anc['paginas']} | {fmt(a['tau'],6)} | {fmt(a['quebras'],6)} | {fmt(100*a['fid12'])}% | {fmt(100*a['sucessor_linhas'])}% |")
    l += ["", "Âncoras aprovadas pela tolerância solicitada. Não se avaliou um ordenador novo aqui.", "",
          "| Partição | Representação | Páginas | Unidades | Mediana/página | p90 | Máximo | Páginas >510 | Unidades que atravessam | Palavras fora/vizinhas | Sem referência textual |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in stats:
        l.append(f"| {s['particao']} | {s['representacao']} | {s['paginas']} | {s['unidades']} | {fmt(s['mediana'],1)} | {fmt(s['p90'],1)} | {s['maximo']} | {s['paginas_acima_510']} | {s['atravessam']}/{s['com_ref']} ({fmt(100*s['fracao_atravessam'])}%) | {fmt(100*s['fracao_palavras_fora'])}% | {s['sem_ref']} |")
    l += ["", "Toda palavra disponível aparece em exatamente uma unidade em cada representação. A contagem inclui átomos sem palavras; o denominador de unidades que atravessam inclui só unidades com palavras na referência.", "",
          "O rótulo de unidade é a mediana dos postos das suas palavras na referência. A fração fora/vizinhas conta palavras cujo posto é menor que o máximo da unidade anterior ou maior que o mínimo da seguinte, na ordem de medianas, considerando apenas vizinhas com referência. Uma palavra que viola ambos conta uma vez. Qualquer fração positiva marca a unidade como atravessando; é um diagnóstico de sobreposição de intervalos, não a métrica de eficácia de palavras e não certifica erro humano. Unidades sem palavra-ouro têm mediana nula e um posto auxiliar pela palavra-ouro geometricamente mais próxima, com marca explícita; não entram no denominador.", "",
          "A silver usa **fluxo do PDF por palavra**, sem expansão dos blocos antigos: `palavras_da_pagina()` usa `use_text_flow=True`, guarda `s` e devolve palavras nesse fluxo. Os caches canônicos preservam a mesma lista; a sequência de referência é seus índices. A ordem `stream` dos blocos antigos usava o menor `s` do bloco, uma aproximação mais grossa. Não substituímos nem regeneramos a referência oficial armazenada.", "",
          "Nas bancadas, a ordem-ouro de palavras é obtida por `ordem_sem_bbox_validacao_acervo.preparar`, com as mesmas funções `donos/linhas` usadas por `erros_ponta_a_ponta`. V4 usa palavras congeladas Diamond; v3 novo usa o cache canônico existente. A ordem humana é de regiões; sua expansão interna é geométrica, não anotação independente de palavras/células.", "",
          f"Página(s) de bancada excluída(s) do inventário de treino: {len(contexto['excluidos_treino'])}. O inventário original tem {len(contexto['duplicatas_extra'])} page_id compartilhados entre base e extra, que serão preservados na exportação completa e deduplicados pelo `montar_treino()` existente. IDs no manifesto. Há {len(feitos)} registros de páginas nas partições e {estado['paginas_unicas']} page_id únicos; validação/teste preservam todas as páginas originais, inclusive sobreposições humanas, que não são amostras independentes. Bancadas e silver são reportadas separadamente.", "",
          f"Veículos de treino nas bancadas: v4 tem {vistos[('golden_v4', True)]} páginas de veículos vistos e {vistos[('golden_v4', False)]} não vistos; v3 novo tem {vistos[('golden_v3_novo', True)]} vistos e {vistos[('golden_v3_novo', False)]} não vistos. Ser visto significa pertencer ao split de treino silver; não significa que a página humana tenha entrado no treino.", "",
          "Integridade e igualdade de page_id: as partições completas validação/teste são comparadas às fontes originais. Treino amostrado é comparado à seleção determinística elegível, após exclusão obrigatória das bancadas; o treino completo será comparado a todo esse universo elegível. Nenhuma página humana nem veículo RN/CE/MA/RJ aparece nas pastas de treino.", "",
          "| Partição | Páginas cronometradas | Média s/página | Mediana | p90 | Máximo |",
          "|---|---:|---:|---:|---:|---:|"]
    for part, t in estado["tempos"].items():
        l.append(f"| {part} | {t['paginas']} | {fmt(t['media_s'],3)} | {fmt(t['mediana_s'],3)} | {fmt(t['p90_s'],3)} | {fmt(t['max_s'],3)} |")
    l += ["", f"Maior pico de memória do processo registrado na criação das páginas ou nesta invocação: RSS {fmt(pico_rss,1)} MiB; memória comprometida {fmt(pico_commit,1)} MiB (API Windows). Tempo desta invocação {fmt(execucao['tempo_s'],1)} s, incluindo âncoras, exportação e auditorias; tempos por página são os da criação original, preservados na retomada, e incluem leitura/hash/cache, renderização, detector quando necessário e três representações, excluindo âncoras e reexportações. Manifestos de invocações anteriores ficam em `cache/execucoes/`. Não é benchmark controlado; páginas humanas e parte da silver usam caches prévios.", ""]
    if media is not None:
        l += [f"Estimativa para as {restantes} páginas de treino restantes: {fmt(media*restantes/3600,2)} h, usando média de {len(amostra_t)} páginas de treino ({fmt(media,3)} s/página). Treino total elegível: {sum(v for k,v in universo.items() if k.startswith('treino'))}. Extrapolação de amostra base; extra pode ter densidade e custo de PDF diferentes. Não foi executado o treino completo.", ""]
    l += ["Formato: `<representação>/<uf>.jsonl` e `<representação>_extra/<uf>.jsonl` seguem `bounding_boxes/ordens/stats/dimensions`; palavras e referência textual ficam no irmão `<uf>.palavras.jsonl`, ignorado pelo protocolo. `ks/tipo` são extras por unidade. `bancadas/{golden_v4,golden_v3_novo}.jsonl` tem uma linha por página com palavras, `gt_w/gt_l/gold_lines/reg_words` e três páginas compatíveis sob `representacoes`. IDs das unidades recebem permutação independente da referência; a entrada dos métodos usa `ordem_entrada`, semente `entrada-{page_id}`.", "",
          "As representações são chamadas diretamente, sem copiar/reajustar sua lógica. Tabela/imagem: mesmos pesos ls3 e parâmetros P2, CPU, imgsz 1024, conf 0,25, NMS IoU 0,7, max_det 300; retenção de átomos ≥0,45. As classes finas do Docling e as classes humanas não entram nessas representações. `colunas_margens` chama `representar_estruturas`: ls3 não prevê cabeçalhos/rodapés, portanto a separação depende das bordas isoladas e da moldura/texto institucional. `ks` e texto internos são preservados como devolvidos pelas funções; não são reordenados pelo ouro.", "",
          "Limitações: v4 usado no desenvolvimento das colunas; v3 novo pequeno e de conveniência; silver automática em veículos selecionados por concordância com XY-cut; veículos humanos vistos/não vistos separados acima. Sem OCR, sem uso de dados Label Studio, sem novos pesos. Cruzamento, perda de calha e ordem interna não podem ser corrigidos pelo ordenador de unidades indivisíveis. LayoutLM admite 512 tokens, incluindo especiais: acima de 510 unidades o codificador existente pode exceder o limite mesmo com um token por unidade; abaixo disso o orçamento textual por unidade encolhe. Não silenciosamente filtre essas páginas nem anuncie compatibilidade neural completa sem tratamento próprio na tarefa dos ordenadores.", "",
          "Retomada: cada página completa é salva atomicamente; shards são publicados a cada 50 páginas e no encerramento. Caches completos sobrevivem mesmo antes da publicação. Treino base e depois extra têm embaralhamento fixo 20261004. `treino_pronto.json` só aparece quando o universo inteiro terminar.", "",
          "Comando exato, da raiz, para o orquestrador continuar a exportação:", "",
          "```powershell", "venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 0", "```", "",
          "Auditoria sem inferência:", "", "```powershell",
          "venv/Scripts/python.exe -B orquestracao/analises/unidades_sem_caixas.py --limite-treino 60 --conferir",
          'venv/Scripts/python.exe -B -c "import os; os.environ[\'TCC_DIR_BLOCOS\']=\'resultados/unidades_sem_caixas/colunas\'; from src.eval import protocolo; print(len(protocolo.carregar_particao(\'validacao\')))"',
          "```", "", "Todos os números desta página são calculados pelo script a partir dos caches; hashes e contagens detalhados em `resultados/unidades_sem_caixas/manifesto.json`."]
    gravar(MD, "\n".join(l)+"\n")
    return estado


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite-treino", type=int, default=60, help="zero exporta todo o treino")
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    exigir(args.limite_treino >= 0, "--limite-treino deve ser >=0")
    t0 = time.perf_counter()
    contexto = montar_plano(args.limite_treino)
    print("[plano]", dict(collections.Counter(m["particao"] for m in contexto["plano"])), flush=True)
    anterior = contexto["manifesto_anterior"]
    if not args.conferir and anterior and anterior["fingerprint"] != contexto["fingerprint"]:
        gravar(OUT / "cache/execucoes" / (anterior["fingerprint"]+".json"), anterior)
    if args.conferir:
        anc = ler(OUT / "ancoras.json")
        exigir(anc["aprovada"] and anc["fingerprint"] == contexto["fingerprint"], "Ancora invalida")
    else:
        try:
            anc = ancora(contexto)
        except Exception as exc:
            gravar(MD, "# Unidades sem caixas finas — interrompido nas âncoras\n\n"+str(exc)+"\n\nNenhum número novo de representação foi publicado. Consulte `ancoras.json` e caches por página.\n")
            raise
    # Incluir todos os caches prontos ANTES de publicar shards parciais. Assim
    # uma retomada nao apaga paginas prontas nem compara shards antigos a uma
    # lista que ainda nao chegou a elas no laco desta invocacao.
    feitos = []
    for m in contexto["plano"]:
        path = cache_pagina(m)
        if path.exists():
            obj = ler(path)
            exigir(obj["fingerprint"] in contexto["fingerprints_compativeis"], f"Cache incompativel: {path}")
            feitos.append(m)
    ids_feitos = {(m["particao"], m["page_id"]) for m in feitos}
    nnovas = 0
    for i, m in enumerate(contexto["plano"], 1):
        if args.conferir:
            obj = ler(cache_pagina(m))
            exigir(obj["fingerprint"] == contexto["fingerprint"], "Cache de pagina divergente")
            for p in obj["representacoes"].values():
                auditar_pagina(p, len(obj["palavras"]))
            retomada = True
        else:
            try:
                obj, retomada = processar(m, contexto)
            except ValueError as erro:
                # Página de TREINO com recorte deslocado: a escala do P2 não vale nela. Pula e registra,
                # em vez de derrubar a exportação inteira (orquestrador, 05/10). Bancadas, validação e
                # teste continuam abortando: nelas uma página a menos mudaria a medição.
                if m["particao"] not in ("treino", "treino_extra") or "CropBox deslocada" not in str(erro):
                    exportar(contexto, feitos)
                    raise
                with open(OUT / "treino_puladas.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"page_id": m["page_id"], "motivo": str(erro)}, ensure_ascii=False) + "\n")
                print(f"[{i}/{len(contexto['plano'])}] {m['particao']} {m['page_id']} PULADA: {erro}", flush=True)
                continue
            except Exception:
                exportar(contexto, feitos)
                ver = verificar(contexto, feitos, False)
                relatorio(contexto, feitos, anc, False, ver,
                          {"tempo_s": time.perf_counter()-t0, "memoria": memoria(), "paginas_novas": nnovas})
                raise
        if (m["particao"], m["page_id"]) not in ids_feitos:
            feitos.append(m)
            ids_feitos.add((m["particao"], m["page_id"]))
        nnovas += not retomada
        print(f"[{i}/{len(contexto['plano'])}] {m['particao']} {m['page_id']} "
              f"unidades={','.join(str(len(p['bounding_boxes'])) for p in obj['representacoes'].values())} "
              f"tempo={obj['tempo_s']:.2f}s {'cache' if retomada else 'nova'}", flush=True)
        publicar = ((not retomada and (nnovas == 1 or nnovas % 50 == 0))
                    or i == len(contexto["plano"]))
        if not args.conferir and publicar:
            exportar(contexto, feitos)
            ver = verificar(contexto, feitos, i == len(contexto["plano"]))
            relatorio(contexto, feitos, anc, i == len(contexto["plano"]), ver,
                      {"tempo_s": time.perf_counter()-t0, "memoria": memoria(), "paginas_novas": nnovas})
        del obj
        gc.collect()
    ver = verificar(contexto, feitos, True)
    exigir(all(sha(RAIZ / p) == h for p, h in contexto["hashes"].items()), "Fonte mudou durante a execucao")
    if args.conferir:
        print("CONFERE: integridade, hashes, page_ids, treino sem vazamento e contrato do protocolo", ver, flush=True)
        return
    completo = sum(m["colecao"] != "bancadas" for m in feitos) == len(contexto["todos_silver"])
    if completo:
        gravar(OUT / "treino_pronto.json", {"contagens": dict(collections.Counter(m["particao"] for m in feitos)),
                "representacoes": REPS, "fingerprint": contexto["fingerprint"], "verificacoes": ver})
    print("CONCLUIDO", ver, "treino_completo=", completo, flush=True)


if __name__ == "__main__":
    main()
