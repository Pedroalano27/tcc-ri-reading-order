"""Valida em dado novo a ordem por linhas e atomos, com parametros congelados.

Importa a geometria original sem alterar fontes ou anotacoes. Converte o projeto
23 em resultados/ordem_ls/validacao_sem_bbox; extrai palavras em pontos do PDF,
confere pagina e escala pela transcricao, e usa somente CPU para o detector ls3.
A regua principal e a sequencia real de palavras, sem projecao por mediana.
Uma unica melhoria exploratoria e desenvolvida primeiro no golden_v4: usar as
linhas internas de atomos para votar nas calhas quando o perfil original falha,
preservando a atomicidade na saida. Nao seleciona parametros no Label Studio.

Uso na raiz: venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_validacao_ls.py
--do-zero ignora caches e compara os numeros com a execucao anterior.
--conferir reconstroi o relatorio a partir dos resultados e verifica igualdade.
Caches por pagina, conversao, PDFs temporarios e resultados ficam em resultados/.
Exports sao lidos incrementalmente; linhas de cache truncadas sao ignoradas.
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
import concurrent.futures
import hashlib
import json
import math
import os
import re
import statistics
import time
import unicodedata
from types import SimpleNamespace
from importlib.metadata import version
import numpy as np
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import ordem_sem_bbox_justo as j
from src.anotacao import ordem_labelstudio as ls
from src.data.extrator import palavras_da_pagina
from src.data.montar_deteccao_ls import fonte_de

BASE = RAIZ / "resultados/ordem_ls/validacao_sem_bbox"
MD = RAIZ / "resultados/ordem_sem_bbox_validacao_ls.md"
EXPORT = RAIZ / "data/labelstudio/ls_p23_seed2_order.json"
PESOS = RAIZ / "runs/detect/ls3/weights/best.pt"
CFG = o.Config("projecao_local_margens", 0.45, 1.2, 0.08)
NOMES = {"ingenua": "Ingênua nas caixas-ouro†", "xy": "XY-cut nas caixas-ouro†",
         "xy_margens": "XY-cut ouro + mesmas margens†",
         "ouro": "Sem bbox fina, átomos-ouro† (diagnóstico)",
         "ls3": "Sem bbox fina, detector ls3 CPU",
         "ouro_exp": "Exploratório: átomos-ouro + voto interno†",
         "ls3_exp": "Exploratório: ls3 + voto interno"}
REGUAS = ("palavras", "regioes")
METRICAS = ("tau", "sucessor", "ard")
# Cabecalhos dos PDFs confirmam estas duas grafias do mesmo veiculo.
# Nao se funde Teresina com PI nem Porto Alegre com RS (jornais distintos).
ALIASES_VEICULO = {"rio janeiro": "rj", "doe pa": "pa"}


def gravar(path, objeto):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporario = path.with_name(path.name + ".tmp")
    with temporario.open("w", encoding="utf-8", newline="\n") as f:
        f.write(objeto if isinstance(objeto, str) else json.dumps(objeto, ensure_ascii=False,
                                                               indent=2, allow_nan=False))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporario, path)


def carregar_json(path):
    """Cache incompleto apos queda nao impede retomar dos outros arquivos."""
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def digest(path):
    return j.digest(path)


def lista_json(path):
    """Decodifica uma tarefa por vez, sem read_text nem leitura integral do export."""
    dec = json.JSONDecoder()
    with path.open(encoding="utf-8") as f:
        buf, iniciou, acabou = "", False, False
        while not acabou:
            bloco = f.read(65536)
            buf += bloco
            while True:
                buf = buf.lstrip()
                if not iniciou:
                    if not buf:
                        break
                    if buf[0] != "[":
                        raise ValueError("Export precisa ser lista de tarefas")
                    iniciou, buf = True, buf[1:]
                    continue
                buf = buf.lstrip(" \r\n\t,")
                if buf.startswith("]"):
                    acabou = True
                    break
                if not buf:
                    break
                try:
                    tarefa, fim = dec.raw_decode(buf)
                except json.JSONDecodeError:
                    if not bloco:
                        raise ValueError("Export incompleto")
                    break
                yield tarefa
                buf = buf[fim:]
            if not bloco and not acabou:
                raise ValueError("Export sem fechamento")


def converter():
    """Usa o conversor existente, trocando apenas o carregador integral em memoria."""
    pares, origens = [], {}
    cont = collections.Counter()
    for t in lista_json(EXPORT):
        cont["tarefas_export"] += 1
        for pred in t.get("predictions") or []:
            if isinstance(pred, dict):
                origens[("pred", pred.get("id"))] = pred.get("result") or []
        for a in t.get("annotations") or []:
            if not isinstance(a, dict):
                continue
            origens[("ann", a.get("id"))] = a.get("result") or []
            if a.get("was_cancelled"):
                cont["canceladas"] += 1
            elif ls._anotador(a) == "desconhecido":
                cont["automaticas_ignoradas"] += 1
            else:
                pares.append((t, a))
    processadas = ls.processar(pares, origens, excluir=["desconhecido"])
    validas = [p for p in processadas if not any(x[0] == ls.ERRO for x in p["problemas"])]
    cont.update(humanas=len(processadas), humanas_invalidas=len(processadas)-len(validas),
                humanas_validas=len(validas))
    # Escolhe antes da conversao: caixas e ordem pertencem a mesma revisao humana.
    escolhidas = {}
    for p in validas:
        pid = p["page_id"]
        if pid not in escolhidas or (p["atualizada_em"] or "", p["anotacao_id"] or 0) > (
                escolhidas[pid]["atualizada_em"] or "", escolhidas[pid]["anotacao_id"] or 0):
            escolhidas[pid] = p
    ids = {p["anotacao_id"] for p in escolhidas.values()}
    selecionados = [(t, a) for t, a in pares if a.get("id") in ids]
    antigo = ls.carregar
    try:
        # A marca antecede a primeira anotacao derivada: queda durante conversao
        # nao faz o conversor confundi-la com uma anotacao humana protegida.
        destino = BASE / "convertido"
        if not (destino / "anotacoes.jsonl").exists():
            gravar(destino / ls.MARCA_SAIDA, {"export": str(EXPORT),
                   "criador": Path(__file__).name, "em_conversao": True})
        ls.carregar = lambda caminho: (selecionados, origens)
        ls.cmd_converter(SimpleNamespace(export=EXPORT, saida=destino,
                                         anotador=None, excluir=["desconhecido"]))
    finally:
        ls.carregar = antigo
    return dict(cont)


def particao(items, ws, H):
    return j.particao(items, ws, H, "geo")


def ordenar_exploratorio(items, ids, q, diag, depth=0):
    """Unica mudanca: no fallback, atomos votam com suas linhas, sem serem partidos."""
    if not ids:
        return []
    if depth > 60:
        return sorted(ids, key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
    h = q["h"]
    cortes = o.vales_locais(items, ids, h, CFG.vale) or o.vales(items, ids, h, CFG.vale)
    if not cortes and any(items[i]["tipo"] in ("table", "picture") for i in ids):
        sondas = []
        for i in ids:
            m = items[i]
            if m["tipo"] in ("table", "picture") and m["ks"]:
                sondas.extend({"bbox": L["bbox"]} for L in o.linhas(q["ws"], m["ks"]))
            else:
                sondas.append({"bbox": m["bbox"]})
        ii = list(range(len(sondas)))
        cortes = o.vales_locais(sondas, ii, h, CFG.vale) or o.vales(sondas, ii, h, CFG.vale)
        if cortes:
            diag["votos_internos"] += 1
    if not cortes:
        return o.xycut(ids, o.boxes(items))
    diag["max_colunas"] = max(diag["max_colunas"], len(cortes)+1)
    W = max(items[i]["bbox"][2] for i in ids)-min(items[i]["bbox"][0] for i in ids)
    largos = [i for i in ids if any(items[i]["bbox"][0] < c < items[i]["bbox"][2]
               and min(c-items[i]["bbox"][0], items[i]["bbox"][2]-c) >= .10*W for c in cortes)]
    if largos:
        largos.sort(key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
        diag["pontes"] += len(largos)
        ys = [(items[i]["bbox"][1]+items[i]["bbox"][3])/2 for i in largos]
        secs = [[] for _ in range(len(largos)+1)]
        for i in ids:
            if i not in largos:
                cy = (items[i]["bbox"][1]+items[i]["bbox"][3])/2
                secs[sum(y < cy for y in ys)].append(i)
        saida = []
        for z, sec in enumerate(secs):
            saida.extend(ordenar_exploratorio(items, sec, q, diag, depth+1))
            if z < len(largos):
                saida.append(largos[z])
        return saida
    gs = [[] for _ in range(len(cortes)+1)]
    for i in ids:
        cx = (items[i]["bbox"][0]+items[i]["bbox"][2])/2
        gs[sum(c < cx for c in cortes)].append(i)
    return [i for g in gs for i in ordenar_exploratorio(items, g, q, diag, depth+1)]


def prever(q, det, exploratorio=False):
    ats, livres = o.atomos(q["ws"], det, CFG.score)
    items = ats + o.linhas_partidas(q["ws"], livres, CFG.gap, q["h"])
    diag = {"max_colunas": 1, "pontes": 0, "votos_internos": 0,
            "n_atomos": len(ats), "atomos_sem_palavras": sum(not x["ks"] for x in ats)}
    ini, corpo, marcas, fim = particao(items, q["ws"], q["p"]["dimensions"]["height"])
    if exploratorio:
        ordem = ordenar_exploratorio(items, corpo, q, diag)
    else:
        ordem = o.ordenar_projecao(items, corpo, q["h"], CFG.vale, diag, local=True)
    chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
    ordem = sorted(ini, key=chave)+ordem+sorted(marcas, key=chave)+sorted(fim, key=chave)
    if sorted(ordem) != list(range(len(items))):
        raise ValueError("Ordenador perdeu itens")
    items = [items[i] for i in ordem]
    seq = o.fluxo(items, q["ws"])
    if sorted(seq) != list(range(len(q["ws"]))):
        raise ValueError("Ordenador perdeu ou duplicou palavras")
    return seq, items, diag


def referencia(p, a, ws):
    # Conversor emite caixas na ordem humana; entrada geometrica canonica evita
    # usar essa ordem como desempate das heuristicas.
    p = dict(p, bounding_boxes=sorted(p["bounding_boxes"], key=lambda r: (
        r["bbox"][1], r["bbox"][0], str(r["id"]))))
    kws, livres, amb = o.donos(ws, p["bounding_boxes"])
    reg_words, gold_lines, gt_l = {}, [], []
    por_l = {}
    for r, ks in zip(p["bounding_boxes"], kws):
        reg_words[r["id"]], por_l[r["id"]] = ks, []
        for z, L in enumerate(o.linhas(ws, ks)):
            lid = f"{r['id']}:l{z}"
            gold_lines.append({"id": lid, "regiao": r["id"], "ks": L["ks"], "bbox": L["bbox"]})
            por_l[r["id"]].append(lid)
    for rid in a["ordem"]:
        gt_l.extend(por_l.get(rid, []))
    por_id = {L["id"]: L for L in gold_lines}
    return {"p": p, "ws": ws, "h": statistics.median(w[4]-w[2] for w in ws) if ws else 10.,
            "gt_r": a["ordem"], "gt_l": gt_l, "gold_lines": gold_lines, "reg_words": reg_words,
            "gt_w": [k for lid in gt_l for k in por_id[lid]["ks"]],
            "auditoria": {"palavras": len(ws), "fora_ouro": len(livres), "ambiguas": amb,
                          "regioes_vazias": sum(not ks for ks in kws), "pagina_vazia": int(not ws)}}


def avaliar(q, seq, ordem=None):
    r = j.avaliar(q, seq, ordem)
    r.pop("linhas", None)  # A mediana de linhas nao e apresentada como saida real.
    return r


def baselines(q, fluxos=None):
    rs = q["p"]["bounding_boxes"]
    items = [{"id": r["id"], "bbox": r["bbox"], "ks": q["reg_words"][r["id"]]} for r in rs]
    chave = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
    saida = {}
    for nome in ("ingenua", "xy", "xy_margens"):
        if nome == "xy_margens":
            ini, corpo, marcas, fim = particao(items, q["ws"], q["p"]["dimensions"]["height"])
        else:
            ini, corpo, marcas, fim = [], list(range(len(items))), [], []
        ordem = sorted(corpo, key=chave) if nome == "ingenua" else o.xycut(corpo, o.boxes(items))
        ordem = sorted(ini, key=chave)+ordem+sorted(marcas, key=chave)+sorted(fim, key=chave)
        seq = o.fluxo([items[i] for i in ordem], q["ws"])
        livres = sorted(set(range(len(q["ws"])))-set(seq))
        seq.extend(k for L in o.linhas(q["ws"], livres) for k in L["ks"])
        if fluxos is not None:
            fluxos[nome] = seq
        saida[nome] = avaliar(q, seq, [items[i]["id"] for i in ordem])
    return saida


def ouro_det(q, golden=False):
    classes = ("tabela", "figura") if golden else ("table", "figure", "chart", "heading")
    return [{"rotulo": "table" if r["classe"] in ("table", "tabela") else "picture",
             "score": 1., "bbox": r["bbox"]} for r in q["p"]["bounding_boxes"] if r["classe"] in classes]


def desenvolver_golden():
    """Executa antes de avaliar o LS; sem grade, escolha ou ajuste no dado novo."""
    rows = []
    for q in j.preparar():
        met = {}
        for fonte, det in (("docling", q["d"]["detector"]["regioes"]), ("ouro", ouro_det(q, True))):
            for exp in (False, True):
                seq, _, diag = prever(q, det, exp)
                met[fonte+("_exp" if exp else "")] = avaliar(q, seq)
                met[fonte+("_exp" if exp else "")]["diag"].update(diag)
                if not exp and fonte == "docling":
                    antiga, _, _ = o.prever(q, CFG)
                    if antiga != seq:
                        raise ValueError("Configuracao congelada difere do script original")
        rows.append({"page_id": q["p"]["page_id"], "veiculo": q["p"]["page_id"].split("/",1)[0],
                     "colunas": j.colunas(q)["n"], "metodos": met})
    gravar(BASE / "desenvolvimento_golden.json", rows)
    return rows


def tokens(s):
    s = unicodedata.normalize("NFKD", s).lower()
    return collections.Counter(re.findall(r"[a-z0-9]+", s))


def conferir_texto(p, ws):
    """Compara tokens espacialmente associados com transcricao, sem usar ordem humana."""
    kws, livres, amb = o.donos(ws, p["bounding_boxes"])
    inter, ref, pred, n, regioes = 0, 0, 0, 0, []
    for r, ks in zip(p["bounding_boxes"], kws):
        a = tokens(r.get("text") or "")
        b = tokens(" ".join(ws[k][0] for k in ks))
        if not a:
            continue
        hit = sum((a & b).values())
        nr, npred = sum(a.values()), sum(b.values())
        inter += hit; ref += nr; pred += npred; n += 1
        regioes.append({"id": r["id"], "tokens_transcricao": nr, "tokens_pdf": npred,
                        "comuns": hit, "recall": hit/nr})
    return {"regioes_transcritas": n, "tokens_transcricao": ref, "tokens_pdf_transcritos": pred,
            "tokens_comuns": inter, "recall": inter/ref if ref else None,
            "f1": 2*inter/(ref+pred) if ref+pred else None, "por_regiao": regioes}


def pdf_util(path):
    """Extrai PKCS#7 sob resultados; PDFs normais e com zeros finais ficam intactos."""
    with path.open("rb") as f:
        inicio = f.read(1024)
    off = inicio.find(b"%PDF")
    if off in (0, -1) and not path.parent.name.upper().endswith("-MG"):
        return path, False
    raw = path.read_bytes()
    ini, fim = raw.find(b"%PDF"), raw.rfind(b"%%EOF")
    if ini < 0 or fim < ini:
        raise ValueError("Envelope sem PDF completo")
    out = BASE / "pdf_temporarios" / (digest(path)+".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".pdf.tmp")
    with tmp.open("wb") as f:
        f.write(raw[ini:fim+5])
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp,out)
    return out, True


def extrair_grupo(registros):
    """Abre cada PDF uma vez por grupo; guarda cada pagina antes de seguir."""
    import pdfplumber
    out = []
    path = RAIZ / registros[0]["mapa"]["pdf_local"]
    try:
        util, envelope = pdf_util(path)
        with pdfplumber.open(util) as pdf:
            for rec in registros:
                p = rec["p"]
                arquivo = BASE / "palavras" / (hashlib.sha256(p["page_id"].encode()).hexdigest()+".json")
                idx = int(rec["mapa"]["pagina"])-1
                if int(p["pagina"]) != int(rec["mapa"]["pagina"]):
                    raise ValueError("Pagina do export difere do mapa")
                if not 0 <= idx < len(pdf.pages):
                    out.append({"page_id": p["page_id"], "erro": "indice_fora_do_pdf"})
                    continue
                pg = pdf.pages[idx]
                W, H = float(pg.width), float(pg.height)
                sx, sy = W/p["dimensions"]["width"], H/p["dimensions"]["height"]
                pt = dict(p, dimensions={"width": W, "height": H})
                pt["bounding_boxes"] = [dict(r, bbox=[r["bbox"][0]*sx,r["bbox"][1]*sy,
                      r["bbox"][2]*sx,r["bbox"][3]*sy]) for r in p["bounding_boxes"]]
                def palavras(page):
                    return [[w["t"],w["x0"],w["top"],w["x1"],w["bottom"]]
                            for w in palavras_da_pagina(page)]
                ws = palavras(pg)
                audit = conferir_texto(pt, ws)
                # Verifica as duas interpretacoes vizinhas, apenas como auditoria.
                alternativas = []
                for ix in (idx-1, idx+1):
                    if 0 <= ix < len(pdf.pages) and audit["regioes_transcritas"]:
                        outra = pdf.pages[ix]
                        ow = palavras(outra)
                        alt = conferir_texto(pt, ow)
                        alternativas.append({"indice_zero": ix, "f1": alt["f1"]})
                        outra.close()
                audit["alternativas"] = alternativas
                audit["vizinha_melhor"] = any(x["f1"] is not None and audit["f1"] is not None
                                             and x["f1"] > audit["f1"]+.05 for x in alternativas)
                row = {"page_id": p["page_id"], "chave": rec["chave"], "p": pt, "ws": ws,
                       "pdf": rec["mapa"]["pdf_local"], "pagina_um": idx+1, "indice_zero": idx,
                       "numero_paginas_pdf": len(pdf.pages), "pkcs7": envelope,
                       "escala_px_pt": [sx, sy], "texto": audit}
                gravar(arquivo, row)
                pg.close()
                out.append(row)
    except Exception as e:
        out.append({"pdf": str(path.relative_to(RAIZ)), "erro": f"{type(e).__name__}: {e}"})
    return out


def extrair(tarefas, mapa, chave, do_zero, workers):
    prontos, grupos, erros = {}, collections.defaultdict(list), []
    for p in tarefas:
        m = mapa.get(p["task_id"])
        if not m:
            erros.append({"page_id": p["page_id"], "erro": "sem_pdf_no_mapa"})
            continue
        arq = BASE / "palavras" / (hashlib.sha256(p["page_id"].encode()).hexdigest()+".json")
        if arq.exists() and not do_zero:
            try:
                row = json.load(arq.open(encoding="utf-8"))
                if row["chave"] == chave:
                    prontos[p["page_id"]] = row
                    continue
            except (ValueError, KeyError):
                pass
        grupos[m["pdf_local"]].append({"p": p, "mapa": m, "chave": chave})
    # Named pipes do multiprocessing sao bloqueados neste Windows restrito.
    # Threads abrem documentos independentes, sem mudar a extracao.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(extrair_grupo, regs) for regs in grupos.values()]
        for fut in concurrent.futures.as_completed(futs):
            for row in fut.result():
                if "erro" in row:
                    erros.append(row)
                else:
                    prontos[row["page_id"]] = row
            print(f"[extração CPU] {len(prontos)}/{len(tarefas)} páginas; {len(erros)} falhas", flush=True)
            gravar(MD, "# Validação independente — extração em andamento\n\n"
                   f"{len(prontos)}/{len(tarefas)} páginas extraídas; {len(erros)} falhas.\n"
                   f"Palavras já gravadas nos caches: {sum(len(r['ws']) for r in prontos.values())}.\n"
                   "Configuração e melhoria exploratória congeladas; sem veredito até a avaliação.\n")
    return prontos, erros


class Detector:
    def __init__(self, threads):
        self.modelo = None
        self.threads = threads

    def detectar(self, p, split, chave, do_zero):
        arq = BASE / "detector" / (hashlib.sha256(p["page_id"].encode()).hexdigest()+".json")
        if arq.exists() and not do_zero:
            try:
                r = json.load(arq.open(encoding="utf-8"))
                if r["chave"] == chave:
                    return r
            except (ValueError, KeyError):
                pass
        img = RAIZ / "data/labelstudio/img" / split["img"]
        if not img.exists():
            return {"erro": "imagem_local_ausente"}
        if self.modelo is None:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            os.environ["YOLO_CONFIG_DIR"] = str(BASE / "ultralytics")
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["YOLO_OFFLINE"] = "true"
            import torch
            torch.set_num_threads(self.threads)
            torch.set_num_interop_threads(1)
            from ultralytics import YOLO
            from ultralytics.utils import SETTINGS
            dict.__setitem__(SETTINGS, "sync", False)
            self.modelo = YOLO(str(PESOS)).to("cpu")
        from PIL import Image
        with Image.open(img) as im:
            wpx, hpx = im.size
        sx, sy = p["dimensions"]["width"]/wpx, p["dimensions"]["height"]/hpx
        ini = time.perf_counter()
        pred = self.modelo.predict(str(img), device="cpu", imgsz=1024, conf=.25,
                                  iou=.7, max_det=300, verbose=False, save=False, save_txt=False)[0]
        rs = []
        for b in pred.boxes:
            nome = pred.names[int(b.cls.item())]
            if nome not in ("texto", "tabela", "imagem"):
                raise ValueError(f"Classe inesperada no ls3: {nome}")
            if nome == "texto":
                continue
            px = [float(v) for v in b.xyxy[0].tolist()]
            rs.append({"rotulo": "table" if nome == "tabela" else "picture",
                       "bbox": [px[0]*sx,px[1]*sy,px[2]*sx,px[3]*sy], "score": float(b.conf.item())})
        r = {"page_id": p["page_id"], "chave": chave, "regioes": rs, "device": "cpu",
             "tempo_ms": (time.perf_counter()-ini)*1000, "imagem_px": [wpx,hpx]}
        gravar(arq, r)
        return r


def estimar(rows, valores, nboot, seed):
    pares = [(r["veiculo"], v) for r,v in zip(rows,valores) if v is not None and math.isfinite(v)]
    if not pares:
        return {"n": 0, "grupos": 0, "media": None, "ic": [None,None]}
    gs = sorted({g for g,v in pares})
    somas = np.array([sum(v for gg,v in pares if gg==g) for g in gs])
    ns = np.array([sum(gg==g for gg,v in pares) for g in gs])
    sorteios = np.random.default_rng(seed).integers(0,len(gs),(nboot,len(gs)))
    medias = somas[sorteios].sum(axis=1)/ns[sorteios].sum(axis=1)
    return {"n": len(pares), "grupos": len(gs), "media": statistics.mean(v for g,v in pares),
            "ic": [float(x) for x in np.quantile(medias,[.025,.975])]}


def agregar(rows, nboot, seed):
    metodos = [m for m in NOMES if any(m in r["metodos"] for r in rows)]
    saida = {}
    for m in metodos:
        rr = [r for r in rows if m in r["metodos"]]
        s = {reg: {v: estimar(rr,[r["metodos"][m][reg][v] for r in rr],nboot,seed)
                   for v in METRICAS} for reg in REGUAS}
        s["fragmentacao"] = estimar(rr,[r["metodos"][m]["diag"]["fracao_estrita"] for r in rr],nboot,seed)
        s["paginas"] = len(rr)
        saida[m] = s
    return saida


def testes(rows, nboot, seed):
    out = []
    for metodo, base in (("ouro","xy"),("ouro","xy_margens"),("ls3","xy"),
                         ("ls3","xy_margens"),("ouro_exp","ouro"),("ls3_exp","ls3")):
        for reg in REGUAS:
            for met in METRICAS:
                pares = [r for r in rows if metodo in r["metodos"] and base in r["metodos"]
                         and r["metodos"][metodo][reg][met] is not None
                         and r["metodos"][base][reg][met] is not None]
                ds = [r["metodos"][metodo][reg][met]-r["metodos"][base][reg][met] for r in pares]
                if not ds:
                    continue
                d = np.round(ds,12)
                if np.all(d==0):
                    stat, pv = 0.,1.
                else:
                    w = wilcoxon(d, zero_method="pratt", alternative="two-sided", method="auto")
                    stat,pv = float(w.statistic),float(w.pvalue)
                # Inferencia auxiliar por veiculo: evita tratar paginas irmas como independentes.
                grupos = sorted({r["veiculo"] for r in pares})
                gd = np.array([statistics.mean(v for r,v in zip(pares,ds) if r["veiculo"]==g) for g in grupos])
                if np.all(np.round(gd,12)==0):
                    pg = 1.
                else:
                    pg = float(wilcoxon(np.round(gd,12),zero_method="pratt",method="auto").pvalue)
                out.append({"metodo": metodo, "base": base, "regua": reg, "metrica": met,
                            "delta": estimar(pares,ds,nboot,seed), "w": stat, "p_pratt": pv,
                            "p_pratt_veiculo": pg, "empates": int(sum(d==0)),
                            "ganhos": int(sum(d>0)) if met!="ard" else int(sum(d<0)),
                            "perdas": int(sum(d<0)) if met!="ard" else int(sum(d>0))})
    # Holm na familia inteira por subconjunto (inclui duas reguas e exploratorios).
    maior = 0.
    for rank,i in enumerate(sorted(range(len(out)),key=lambda i:out[i]["p_pratt"])):
        maior = max(maior,min(1.,out[i]["p_pratt"]*(len(out)-rank)))
        out[i]["p_holm"] = maior
    return out


def resumo(R):
    rows = R["paginas"]
    subsets = {"todas": rows, "uma_coluna": [r for r in rows if r["colunas"]==1],
               "multicoluna": [r for r in rows if r["colunas"]>1],
               "corrigidas_comprovadas": [r for r in rows if r["bias"]=="alterada_comprovada"],
               "diferentes_xy_recalculada": [r for r in rows if r["diferente_xy"]],
               "ls3_treino": [r for r in rows if r["split"]=="train"],
               "ls3_validacao": [r for r in rows if r["split"]=="val"],
               "ls3_teste": [r for r in rows if r["split"]=="test"],
               "ls3_fora_treino": [r for r in rows if r["split"] in ("val","test")],
               "alinhamento_confirmado": [r for r in rows if r["alinhamento_confirmado"]]}
    R["resumos"] = {k:{"n":len(rr),"veiculos":len({r["veiculo"] for r in rr}),
                       "metodos": agregar(rr,R["bootstrap"],R["semente"]),
                       "testes": testes(rr,R["bootstrap"],R["semente"])} for k,rr in subsets.items()}
    gg = R["golden"]
    R["golden_resumo"] = {k: agregar_golden(rr,R["bootstrap"],R["semente"]) for k,rr in
                          (("todas",gg),("multicoluna",[r for r in gg if r["colunas"]>1]))}


def agregar_golden(rows,nboot,seed):
    return {m: estimar(rows,[r["metodos"][m]["palavras"]["tau"] for r in rows],nboot,seed)
            for m in ("docling","docling_exp","ouro","ouro_exp")}


def f(x,n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".",",")


def cel(e,percent=False):
    esc = 100 if percent else 1
    if e["media"] is None:
        return "—"
    n = 1 if percent else 3
    return f"{f(e['media']*esc,n)}{'%' if percent else ''} [{f(e['ic'][0]*esc,n)}; {f(e['ic'][1]*esc,n)}]"


def tabela(S,regua,metodos):
    out = ["| Método | n | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) | Regiões fragmentadas ↓ |",
           "|---|---:|---:|---:|---:|---:|"]
    for m in metodos:
        if m not in S:
            continue
        s=S[m]
        out.append(f"| {NOMES[m]} | {s[regua]['tau']['n']} | {cel(s[regua]['tau'])} | {cel(s[regua]['sucessor'],True)} | {cel(s[regua]['ard'])} | {cel(s['fragmentacao'],True)} |")
    return out


def relatorio(R):
    if not R.get("concluido"):
        return ("# Validação independente — execução parcial\n\n"
                f"{len(R.get('paginas',[]))} páginas com métricas gravadas; etapa: {R.get('etapa','início')}.\n\n"
                "Sem veredito até terminar a amostra. Caches sincronizados por página permitem retomada.\n")
    S=R["resumos"]; todos=S["todas"]["metodos"]
    ta=todos["ouro"]["palavras"]["tau"]["media"]
    tx=todos["xy"]["palavras"]["tau"]["media"]
    tj=todos["xy_margens"]["palavras"]["tau"]["media"]
    teste=next(t for t in S["todas"]["testes"] if t["metodo"]=="ouro" and t["base"]=="xy_margens" and t["regua"]=="palavras" and t["metrica"]=="tau")
    ganho = teste["delta"]["ic"][0]>0 and teste["p_pratt_veiculo"]<.05
    R["veredito"] = ("O ganho se confirma apenas no diagnóstico com átomos humanos, nesta amostra enviesada."
                      if ganho else "O ganho geral não se confirma em dado novo contra a XY-cut com as mesmas margens.")
    out=["# Validação independente da ordem sem bounding box fina", "", "## Resumo em cinco linhas", "",
         f"1. **Veredito: {R['veredito']}**",
         f"2. {S['todas']['n']} páginas com cadeia válida ({todos['ouro']['palavras']['tau']['n']} com métrica de palavras), de {S['todas']['veiculos']} veículos: τ real {f(ta)} (átomos-ouro), {f(tx)} (XY-cut pura) e {f(tj)} (XY-cut com margens).",
         f"3. Contra a XY-cut justa: Δτ {cel(teste['delta'])}; Wilcoxon Pratt por página p={f(teste['p_pratt'],6)} e por veículo p={f(teste['p_pratt_veiculo'],6)}.",
         f"4. Multicoluna: {S['multicoluna']['n']} páginas; correções comprovadas da sugestão: {S['corrigidas_comprovadas']['n']}; diferentes da XY-cut recalculada (sensibilidade): {S['diferentes_xy_recalculada']['n']}.",
         f"5. Detector: {S['ls3_treino']['n']} páginas no treino, {S['ls3_validacao']['n']} na validação, {S['ls3_teste']['n']} no teste; melhoria por voto interno é exploratória e não muda o veredito do método congelado.",
         "", "## Configuração congelada e independência", "",
         f"`{CFG.id}`: abordagem={CFG.abordagem}, score={f(CFG.score,2)}, gap={f(CFG.gap,1)}, vale={f(CFG.vale,2)}. É a configuração modal do LOPO anterior; escolhas registradas: `{R['congelamento']['escolhas_lopo']}`. Não houve reajuste nem seleção com a ordem LS. O score filtra átomos; todos os outros limiares são os do código importado, em pontos PDF. Hashes de fontes/dados constam em `manifesto.json`.",
         "Páginas novas pertencem ao projeto parceiro Data Policy: uso exclusivamente interno. Independência aqui significa páginas não usadas no desenvolvimento original; não garante veículos inéditos. A melhoria foi executada no Golden antes das métricas LS. Caixas humanas de texto só entram nas baselines e na avaliação; o método usa palavras e átomos table/figure/chart/heading. A classe heading é rubrica manuscrita, não título. unknown fica fora dos átomos, mas continua na régua humana quando tem palavras.",
         f"Checagem de sobreposição com o Golden por nome de PDF e página: `{R['independencia']}`. É conferência de identidade nominal, não prova de conteúdos distintos por hash de raster.",
         "", "## Réguas, margens e inferência", "",
         "**Principal = sequência real de palavras.** Cada palavra recebe um ID próprio. Referência = regiões na ordem das relações humanas; dentro da região, `linhas()` emite topo→base/esquerda→direita. A predição é a expansão real dos itens, sem mediana. Portanto a ordenação interna não foi anotada independentemente: trata-se de uma referência geométrica derivada, não transcrição humana de leitura palavra a palavra. Tabelas também são lidas por linhas nesta régua. Sucessor de palavras é favorecido por pares internos longos; lê-se junto com fragmentação.",
         "Fragmentação estrita = fração das regiões com palavras cuja saída tem mais de um trecho; palavras sem dono interrompem trechos. Regiões vazias ficam fora desse denominador, são contadas e só na régua secundária recebem o posto da palavra geometricamente mais próxima (ou geometria numa página vazia). Páginas/réguas com menos de dois itens têm métrica ausente, não acerto perfeito. Regiões por mediana são secundárias e podem esconder intercalação.",
         "A baseline justa aplica às caixas-ouro a precedência literal: marcas quando todas as palavras casam com RE_MARCACAO; topo se centro < 7% da altura e base < 10%; rodapé se centro > 95%; saída = topo, corpo XY-cut, marcas, rodapé. Limiar, regex e desempate são idênticos ao método, preservando caixas inteiras.",
         f"Médias macro por página. IC percentil de 95%, {R['bootstrap']} reamostras de veículos inteiros, semente {R['semente']}; grupos vêm de `ls_split.json`/`fonte_de()`, nunca do nome da edição. Com configuração fixa, não há seleção a refazer no bootstrap. Wilcoxon pareado `zero_method='pratt'`; diferenças arredondadas a doze casas só para distinguir empates numéricos. Reportamos também Pratt nas médias de diferenças por veículo. P por página pode ser otimista por dependência; Holm abrange a família de comparações de cada subconjunto, e análises por estrato continuam exploratórias.",
         "Agrupamento corrige dois aliases do split, confirmados pelos cabeçalhos: `rio janeiro` e `rj` = D.O. do Município do Rio de Janeiro (tarefas 7200/7208); `doe pa` e `pa` = Diário Oficial do Estado do Pará (tarefas 7271/7191). As grafias originais e o split original do detector são preservados em cada resultado. Essa correção só define a unidade de reamostragem, sem alterar predições, limiares ou seleção de páginas.",
         "Colunas: palavras do corpo (centro entre 10% e 95% da altura, sem marcas), linhas partidas com gap=1,2; `vales_locais(..., 0,08)` e fallback `vales`. Uma coluna = nenhum corte; multicoluna = ao menos um corte. É o detector do próprio método, não rótulo humano: pode errar e não resolve layouts que mudam por faixa.",
         "", "## Tabela principal — saída real, palavras", "", "† Usa caixas humanas; diagnóstico, indisponível em produção. A linha ls3 agregada inclui treino e é descritiva; a separação seguinte é obrigatória.", ""]
    principais=("ingenua","xy","xy_margens","ouro","ls3")
    out+=tabela(todos,"palavras",principais)
    for k,nome in (("uma_coluna","Uma coluna"),("multicoluna","Multicoluna"),
                   ("ls3_treino","Detector — páginas do treino (contaminadas)"),
                   ("ls3_validacao","Detector — validação (usada na escolha do checkpoint)"),
                   ("ls3_teste","Detector — teste (fora de treino e validação)"),
                   ("ls3_fora_treino","Detector — fora do treino, incluindo validação"),
                   ("corrigidas_comprovadas","Humano mudou a sugestão — comprovado"),
                   ("diferentes_xy_recalculada","Sensibilidade — humano difere da XY-cut recalculada"),
                   ("alinhamento_confirmado","Sensibilidade — alinhamento textual confirmado")):
        out += ["", f"### {nome}", "", f"{S[k]['n']} páginas, {S[k]['veiculos']} veículos.", ""]
        out += tabela(S[k]["metodos"],"palavras",principais)
    bias=collections.Counter(r["bias"] for r in R["paginas"])
    out += ["", "## Ancoragem e sugestão ausente", "",
            f"Campo `iguais_a_origem` do conversor: {dict(bias)}. O export contém referências a parent_prediction cujas predições não vieram no arquivo. Não inventamos a origem ausente. Subconjunto comprovado exige campo presente e iguais < total. Origem ausente é desconhecida, mesmo se a ordem coincide com a XY-cut atual.",
            "A sensibilidade compara o humano à XY-cut recalculada nas caixas da revisão humana. Ela não comprova correção da proposta original: caixas podem ter sido editadas, IDs trocados e o código XY-cut pode diferir. O viés de ancoragem permanece em todos os subconjuntos; corrigir uma sugestão não equivale a anotação do zero.",
            "", "## Régua secundária — regiões por mediana", ""]
    out += tabela(todos,"regioes",principais)
    out += ["", "## Testes pareados — todas as páginas", "",
            "| Método − base | Régua | Métrica | n/grupos | Δ (IC por veículo) | ganha/empata/perde | p Pratt | p Holm | p Pratt veículo |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for t in S["todas"]["testes"]:
        if t["metodo"].endswith("_exp"):
            continue
        d=t["delta"]
        out.append(f"| {t['metodo']} − {t['base']} | {t['regua']} | {t['metrica']} | {d['n']}/{d['grupos']} | {cel(d)} | {t['ganhos']}/{t['empates']}/{t['perdas']} | {f(t['p_pratt'],6)} | {f(t['p_holm'],6)} | {f(t['p_pratt_veiculo'],6)} |")
    out += ["", "## Exploratório — uma melhoria para átomos em colunas", "",
            "Hipótese desenvolvida no Golden: caixas altas de tabelas lado a lado deixam poucos itens no perfil e impedem a detecção de uma calha. **Única mudança:** quando o perfil original não encontra cortes e há átomos, linhas internas desses átomos votam no mesmo detector de vales; as caixas continuam indivisíveis na saída. Sem novo limiar, nova grade ou ajuste LS. O restante (margens, score, ponte de 10%, recursão/fallback) permanece igual. O resultado é reportado mesmo se não melhorar; não selecionamos a versão vencedora após o LS.",
            "No desenvolvimento Golden, os votos adicionais não melhoraram a ordem real. Portanto a hipótese não teve suporte nessa bancada; mantemos o teste LS explicitamente exploratório, sem promovê-lo ao método congelado.",
            "", "| Desenvolvimento Golden | n | Docling congelado | Docling + voto | Ouro congelado | Ouro + voto |",
            "|---|---:|---:|---:|---:|---:|"]
    for k,g in R["golden_resumo"].items():
        out.append(f"| {k} | {g['docling']['n']} | {cel(g['docling'])} | {cel(g['docling_exp'])} | {cel(g['ouro'])} | {cel(g['ouro_exp'])} |")
    for k in ("todas","multicoluna","ls3_teste"):
        out += ["", f"### Validação exploratória LS: {k}", ""]
        out += tabela(S[k]["metodos"],"palavras",("ouro","ouro_exp","ls3","ls3_exp"))
        for t in S[k]["testes"]:
            if t["metodo"].endswith("_exp") and t["regua"]=="palavras" and t["metrica"]=="tau":
                out += [f"{t['metodo']} − {t['base']}: Δτ {cel(t['delta'])}; p Pratt={f(t['p_pratt'],6)}, p por veículo={f(t['p_pratt_veiculo'],6)}."]
    audits=R["auditoria"]
    out += ["", "## Auditoria de PDF, índice e escala", "",
            f"Conversão: `{R['conversao']}`. Extração: {len(R['paginas'])} páginas, {len(R['erros'])} falhas. Totais calculados: `{audits}`.",
            "Índice usado = pagina do mapa/export − 1 (mapa e export precisam coincidir). Caixas do conversor estão em pixels; x e y são convertidos separadamente para pontos usando largura/altura real do PDF. Isso preserva constantes como janelas de cem pontos do método anterior. PDF encapsulado é o trecho do primeiro %PDF ao último %%EOF sob pdf_temporarios; originais nunca são alterados.",
            "Verificação: tokens normalizados das palavras dentro das caixas vs transcrições, sem usar a ordem humana; páginas vizinhas (−1/+1) auditadas quando há texto transcrito. Alinhamento confirmado exige F1 de tokens ≥ 0,80 e nenhuma vizinha mais de 0,05 melhor. Esses limites são diagnóstico de qualidade da referência, não parâmetros de ordenação. Não trocamos índice nem ajustamos caixas para melhorar resultados. Transcrição vazia é ausência de prova, não prova de erro. A tabela de sensibilidade mostra só alinhamento confirmado.",
            "", "| tarefa | página/índice | PDF px→pt x/y | F1 tokens | vizinha melhor | regiões sem palavras |",
            "|---|---:|---:|---:|---|---:|"]
    for r in R["paginas"]:
        a=r["extracao"]
        out.append(f"| {r['task_id']} | {a['pagina_um']}/{a['indice_zero']} | {f(a['escala_px_pt'][0],5)}/{f(a['escala_px_pt'][1],5)} | {f(a['texto']['f1'])} | {'sim' if a['texto']['vizinha_melhor'] else 'não'} | {r['auditoria']['regioes_vazias']} |")
    out += ["", "## Análise de erro", "",
            "Piores diferenças na saída real contra a XY-cut justa, átomos-ouro; diagnóstico geométrico, sem causas humanas anotadas.", "",
            "| tarefa/veículo | colunas | Δτ palavras | Δτ regiões | fragmentação | átomos/vazios | pontes | intervenção exploratória |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    validas=[r for r in R["paginas"] if r["metodos"]["ouro"]["palavras"]["tau"] is not None]
    piores=sorted(validas,key=lambda r:r["metodos"]["ouro"]["palavras"]["tau"]-r["metodos"]["xy_margens"]["palavras"]["tau"])[:10]
    for r in piores:
        a,b=r["metodos"]["ouro"],r["metodos"]["xy_margens"]
        diag=a["diag"]
        dr = a["regioes"]["tau"]-b["regioes"]["tau"] if a["regioes"]["tau"] is not None else None
        out.append(f"| {r['task_id']} / {r['veiculo']} | {r['colunas']} | {f(a['palavras']['tau']-b['palavras']['tau'])} | {f(dr)} | {f(100*diag['fracao_estrita'],1) if diag['fracao_estrita'] is not None else '—'}% | {diag['n_atomos']}/{diag['atomos_sem_palavras']} | {diag['pontes']} | {r['metodos']['ouro_exp']['diag']['votos_internos']} |")
    for r in piores[:4]:
        ev=r.get("evidencia",{})
        if ev:
            out += ["", f"Tarefa {r['task_id']}: sequência humana de regiões `{ev['humana']}`; trechos reais emitidos pelo método congelado `{ev['trechos_ouro']}` (até quarenta transições; ∅ = palavra sem região). Repetições mostram intercalação, enquanto grandes permutações sem repetição mostram inversão de regiões inteiras."]
    vazias=[r['task_id'] for r in R['paginas'] if r['auditoria']['pagina_vazia']]
    out += ["", f"Páginas sem camada textual utilizável: tarefas `{vazias}`. Não são excluídas da contabilização de cadeias válidas nem recebem nota de palavras; o fallback de regiões nessas páginas é somente diagnóstico."]
    mascaradas=sum(r["metodos"]["ouro"]["diag"]["mediana_perfeita_fragmentada"] for r in R["paginas"])
    out += ["", f"Há {mascaradas} páginas em que a projeção secundária de regiões é perfeita apesar de fragmentação. Átomos com palavras de regiões diferentes podem misturar o texto; a mediana oculta isso. Falhas de texto/escala, geometria humana incompleta, tabelas com leitura interna diferente e layouts por faixas são explicações alternativas, não causalidade estabelecida.",
            "", "## Limitações e recomendação para o TCC", "",
            "A amostra concluída é seletiva: páginas sem cadeia válida são excluídas; não representa todas as tarefas do parceiro. n por estrato e número de veículos, sobretudo no teste do detector, podem ser pequenos; IC com poucos grupos é instável. Caixas-ouro são informação humana, e nenhuma avaliação com elas é ganho de produção. Figuras sem texto não entram na métrica principal de palavras; seu posicionamento só aparece na régua secundária com fallback diagnóstico. A referência interna de palavras é geométrica. Não há OCR nem avaliação de texto em raster. O bootstrap agrupa veículos, mas a normalização dos nomes não assegura independência semântica total entre edições. Não provamos veículos inéditos nem anotação sem ancoragem. Páginas de validação do detector não são teste virgem.",
            "**Recomendação:** apresentar a configuração congelada como validação externa de páginas, com régua real, baseline justa e estratos lado a lado. Não usar o τ agregado por mediana para afirmar superioridade geral. Manter a regra exploratória separada; qualquer adoção exige confirmação do Pedro e novo ouro anotado do zero, separado por veículo. Não mudar o protocolo principal do TCC com este script.",
            "", "## Reprodução e conferência", "",
            "`venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_ls.py --do-zero`",
            "`venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_ls.py --conferir`",
            "O relatório é gerado do mesmo objeto que `resultado.json`; --conferir recalcula agregados/testes e exige igualdade literal. --do-zero refaz Golden, conversão, extração e detector; havendo resultado anterior com os mesmos hashes, exige igualdade dos números (tempos são excluídos). Manifesto verifica fontes, export, mapa, split, PDFs e imagens antes/depois. Nenhum dado parceiro sai do repositório.",
            f"Conferência entre execuções: `{R.get('reproducao',{})}`. JSONs e relatório são gravados em temporário e substituídos após sincronização; caches incompletos são ignorados e a conversão mantém uma marca prévia de saída derivada. Versões do ambiente: `{R.get('versoes',{})}`.", ""]
    return "\n".join(out)


def assinatura_numerica(R):
    return hashlib.sha256(json.dumps({"resumos":R.get("resumos"),"golden":R.get("golden_resumo"),
                         "auditoria":R.get("auditoria")},sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def checar_sinteticos():
    """Bordas e mascara da mediana: controles relevantes ao protocolo novo."""
    p={"dimensions":{"width":200,"height":300},"bounding_boxes":[
       {"id":"a","bbox":[0,20,70,100],"classe":"paragraph","text":"a b"},
       {"id":"b","bbox":[90,20,160,100],"classe":"paragraph","text":"c d"},
       {"id":"v","bbox":[0,120,70,160],"classe":"figure","text":""}]}
    ws=[["a",1,21,10,30],["b",1,41,10,50],["c",91,21,100,30],["d",91,41,100,50]]
    q=referencia(p,{"ordem":["a","b","v"]},ws)
    r=avaliar(q,[0,2,1,3])
    if not (r["palavras"]["tau"]<1 and r["diag"]["fracao_estrita"]==1):
        raise ValueError("Controle de intercalacao falhou")
    qv=referencia(p,{"ordem":["a","b","v"]},[])
    seq,_,_=prever(qv,ouro_det(qv))
    rv=avaliar(qv,seq)
    if rv["palavras"]["tau"] is not None or qv["auditoria"]["regioes_vazias"]!=3:
        raise ValueError("Controle de pagina vazia falhou")
    cache=BASE/'controle_retomada.json'
    gravar(cache,{"valido":True})
    cache.write_text('{"interrompido":',encoding='utf-8')
    if carregar_json(cache) is not None:
        raise ValueError("Cache interrompido nao foi ignorado")
    gravar(cache,{"valido":True,"cache_interrompido_ignorado":True})
    if carregar_json(cache)!={"valido":True,"cache_interrompido_ignorado":True}:
        raise ValueError("Recuperacao de cache falhou")
    return 3


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero",action="store_true")
    ap.add_argument("--conferir",action="store_true")
    ap.add_argument("--bootstrap",type=int,default=2000)
    ap.add_argument("--semente",type=int,default=20261003)
    ap.add_argument("--workers",type=int,default=2)
    ap.add_argument("--threads",type=int,default=2)
    args=ap.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    out=BASE/"resultado.json"
    if args.conferir:
        R=carregar_json(out)
        if not R or not R.get('concluido'):
            raise ValueError("Sem resultado completo para conferir; retome a execucao")
        sig=assinatura_numerica(R)
        resumo(R)
        if assinatura_numerica(R)!=sig or MD.read_text(encoding="utf-8")!=relatorio(R):
            raise ValueError("Relatorio/numeros nao conferem")
        print("CONFERIDO: agregados, testes e Markdown coincidem; "+sig)
        print("\n".join(tabela(R["resumos"]["todas"]["metodos"],"palavras",("ingenua","xy","xy_margens","ouro","ls3"))))
        return
    anterior=carregar_json(out)
    anterior_original=json.load((RAIZ/"resultados/ordem_sem_bbox.json").open(encoding="utf-8"))
    escolhas=anterior_original["selecao_cv"]
    if max(escolhas,key=escolhas.get)!=CFG.id:
        raise ValueError("Config congelada nao e mais a modal do resultado original")
    R={"concluido":False,"etapa":"desenvolvimento no Golden","paginas":[],
       "bootstrap":args.bootstrap,"semente":args.semente,"sinteticos":checar_sinteticos(),
       "congelamento":{"config":CFG.id,"escolhas_lopo":escolhas,
                        "melhoria":"Voto de linhas internas de atomos apenas no fallback sem cortes"}}
    R['versoes']={n:version(n) for n in ('numpy','scipy','pdfplumber','Pillow','torch','ultralytics')}
    gravar(BASE/"congelamento.json",R["congelamento"])
    gravar(MD,relatorio(R))
    R["golden"]=desenvolver_golden()
    print("[Golden] desenvolvimento da unica regra encerrado; configuracao mantida",flush=True)
    R["conversao"]=converter()
    tarefas=j.ler_jsonl(BASE/"convertido/tarefas.jsonl")
    golden_tarefas=j.ler_jsonl(o.ENTRADAS[0])
    nomes_g={Path(p['arquivo']).name.lower() for p in golden_tarefas}
    pares_g={(Path(p['arquivo']).name.lower(),p['pagina']) for p in golden_tarefas}
    R['independencia']={'pdfs_com_nome_em_comum':len(nomes_g & {Path(p['arquivo']).name.lower() for p in tarefas}),
                       'paginas_com_identidade_em_comum':sum((Path(p['arquivo']).name.lower(),p['pagina']) in pares_g for p in tarefas)}
    anns={a["page_id"]:a for a in j.ler_jsonl(BASE/"convertido/anotacoes.jsonl") if a["status"]=="concluida"}
    mapa={m["task_id"]:m for m in j.ler_jsonl(RAIZ/"data/labelstudio/pdf_paginas.jsonl") if m.get("uso")=="ordem"}
    split=json.load((RAIZ/"data/deteccao/ls_split.json").open(encoding="utf-8"))["paginas"]
    fontes=[EXPORT,RAIZ/"data/labelstudio/pdf_paginas.jsonl",RAIZ/"data/deteccao/ls_split.json",
            Path(__file__),Path(o.__file__),Path(j.__file__),Path(ls.__file__),
            RAIZ/"src/data/extrator.py",RAIZ/"src/data/regioes.py",RAIZ/"src/eval/metrics.py",
            RAIZ/"src/data/montar_deteccao_ls.py",RAIZ/"src/eval/baselines.py",
            RAIZ/"src/data/taxonomia_layout.py",RAIZ/"resultados/ordem_sem_bbox.json"]+o.ENTRADAS
    detector_ok=(RAIZ/"runs/detect/ls3/treino_ok").exists() and PESOS.exists()
    if detector_ok:
        fontes.append(PESOS)
    for p in tarefas:
        if p["task_id"] in mapa:
            fontes.append(RAIZ/mapa[p["task_id"]]["pdf_local"])
        s=split.get(p["page_id"])
        if s:
            img=RAIZ/"data/labelstudio/img"/s["img"]
            if img.exists():
                fontes.append(img)
    H={str(p.relative_to(RAIZ)).replace("\\","/"):digest(p) for p in sorted(set(fontes)) if p.exists()}
    R["hashes"]=H
    gravar(BASE/"manifesto.json",H)
    chave=hashlib.sha256(json.dumps({'hashes':H,'versoes':R['versoes'],
                                   'threads_cpu':args.threads},sort_keys=True).encode()).hexdigest()
    R["etapa"]="extracao de palavras PDF"
    gravar(MD,relatorio(R))
    extraidas,erros=extrair(tarefas,mapa,chave,args.do_zero,args.workers)
    R["erros"]=erros
    detector=Detector(args.threads)
    for z,p in enumerate(tarefas):
        pid=p["page_id"]
        if pid not in extraidas:
            continue
        e=extraidas[pid]; a=anns[pid]
        q=referencia(e["p"],a,e["ws"])
        fluxos={"referencia":q["gt_w"]}
        met=baselines(q,fluxos)
        for exp in (False,True):
            seq,items,diag=prever(q,ouro_det(q),exp)
            m="ouro_exp" if exp else "ouro"
            met[m]=avaliar(q,seq)
            met[m]["diag"].update(diag)
            fluxos[m]=seq
        s=split.get(pid,{})
        detmeta={}
        if detector_ok and s:
            d=detector.detectar(e["p"],s,chave,args.do_zero)
            if "erro" not in d:
                detmeta={k:d[k] for k in ("device","tempo_ms","imagem_px")}
                for exp in (False,True):
                    seq,_,diag=prever(q,d["regioes"],exp)
                    m="ls3_exp" if exp else "ls3"
                    met[m]=avaliar(q,seq)
                    met[m]["diag"].update(diag)
                    fluxos[m]=seq
            else:
                R["erros"].append({"page_id":pid,**d})
        comp=a.get("iguais_a_origem")
        bias="alterada_comprovada" if comp and comp[0]<comp[1] else "igual_comprovada" if comp else "origem_ausente"
        # Diferenca em relacao a baseline atual e sensibilidade, nao origem comprovada.
        xyids=[q["p"]["bounding_boxes"][i]["id"] for i in o.xycut(list(range(len(p["bounding_boxes"]))),o.boxes(q["p"]["bounding_boxes"]))]
        aud=e["texto"]
        veiculo_origem=s.get("fonte") or fonte_de(p["arquivo"])
        dono={k:rid for rid,ks in q['reg_words'].items() for k in ks}
        trechos=[]
        for k in fluxos['ouro']:
            rid=dono.get(k,'∅')
            if not trechos or trechos[-1]!=rid:
                trechos.append(rid)
        gravar(BASE/'fluxos'/(str(p['task_id'])+'.json'),{'page_id':pid,'fluxos':fluxos,
               'palavra_para_regiao':dono,'regioes_humanas':q['gt_r']})
        r={"page_id":pid,"task_id":p["task_id"],"veiculo":ALIASES_VEICULO.get(veiculo_origem,veiculo_origem),
           "veiculo_split_original":veiculo_origem,
           "evidencia":{"humana":q['gt_r'],'trechos_ouro':trechos[:40]},
           "split":s.get("split","desconhecido"),"anotador":a["anotador"],"bias":bias,
           "iguais_a_origem":comp,"diferente_xy":a["ordem"]!=xyids,"colunas":j.colunas(q)["n"],
           "alinhamento_confirmado":aud["f1"] is not None and aud["f1"]>=.80 and not aud["vizinha_melhor"],
           "auditoria":q["auditoria"],"extracao":{k:v for k,v in e.items() if k not in ("ws","p","chave")},
           "metodos":met,"detector":detmeta}
        R["paginas"].append(r)
        gravar(BASE/"paginas"/(str(p["task_id"])+".json"),r)
        R["etapa"]="avaliacao e detector CPU"
        gravar(out,R)
        if R["paginas"]:
            medidas=[v["metodos"]["ouro"]["palavras"]["tau"] for v in R["paginas"]
                     if v["metodos"]["ouro"]["palavras"]["tau"] is not None]
            tau=statistics.mean(medidas) if medidas else None
            gravar(MD,relatorio(R)+f"\nτ real parcial (átomos-ouro) = {f(tau)}.\n")
        print(f"[avaliada {z+1}/{len(tarefas)}] tarefa {p['task_id']} | {s.get('split','?')} | palavras={len(q['ws'])}",flush=True)
    R["auditoria"]={k:sum(r["auditoria"][k] for r in R["paginas"]) for k in
                     ("palavras","fora_ouro","ambiguas","regioes_vazias","pagina_vazia")}
    R["auditoria"].update(regioes=sum(len(anns[r["page_id"]]["ordem"]) for r in R["paginas"]),
        paginas_pkcs7=sum(r["extracao"]["pkcs7"] for r in R["paginas"]),
        paginas_transcritas=sum(bool(r["extracao"]["texto"]["regioes_transcritas"]) for r in R["paginas"]),
        vizinha_melhor=sum(r["extracao"]["texto"]["vizinha_melhor"] for r in R["paginas"]),
        tokens_transcricao=sum(r["extracao"]["texto"]["tokens_transcricao"] for r in R["paginas"]),
        tokens_comuns=sum(r["extracao"]["texto"]["tokens_comuns"] for r in R["paginas"]))
    if any(digest(RAIZ/p)!=h for p,h in H.items()):
        raise ValueError("Uma entrada mudou durante a execucao")
    R["concluido"]=True
    resumo(R)
    if args.do_zero and anterior and anterior.get("concluido"):
        iguais=assinatura_numerica(anterior)==assinatura_numerica(R)
        mesmos_hashes=anterior.get('hashes')==H
        R['reproducao']={'execucao_do_zero':True,'assinatura_numerica_igual':iguais,
                        'mesmos_hashes_de_codigo_e_dados':mesmos_hashes,
                        'assinatura':assinatura_numerica(R)}
        if mesmos_hashes and not iguais:
            raise ValueError("Execucao do zero produziu numeros diferentes")
        if iguais:
            print("REPRODUZIDO DO ZERO: assinatura numerica identica",flush=True)
    texto=relatorio(R)
    gravar(out,R); gravar(MD,texto)
    if MD.read_text(encoding="utf-8")!=relatorio(R):
        raise ValueError("Markdown diverge do objeto de resultados")
    print(R["veredito"])
    print("\n".join(tabela(R["resumos"]["todas"]["metodos"],"palavras",("ingenua","xy","xy_margens","ouro","ls3"))))
    print("RESULTADO: "+str(MD))


if __name__=="__main__":
    main()
