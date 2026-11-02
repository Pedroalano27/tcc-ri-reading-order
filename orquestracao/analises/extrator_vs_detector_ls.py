"""Compara layout do extrator e dos detectores no teste LS, sem tocar nos dados.

O ouro e o split existentes ficam congelados. Os exports grandes sao percorridos
uma tarefa por vez; a origem vem da anotacao que reproduz as caixas convertidas.
Cada etapa guarda cache atomico em resultados/ls_teste_cache para sobreviver a
interrupcoes. Modelos usam exclusivamente CPU e arquivos locais. O relatorio e
reescrito durante a execucao, identificando cobertura parcial e treinos ausentes.

Uso, da raiz: venv/Scripts/python.exe orquestracao/analises/extrator_vs_detector_ls.py
Repetir o comando reaproveita palavras, Docling e propostas; acrescenta apenas
detectores com treino_ok. --so-relatorio recalcula metricas sem inferencia.
--autoteste verifica o emparelhamento, os mapas e o leitor incremental.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.parse import unquote, urlparse

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.dont_write_bytecode = True
# Impede acesso acidental a GPU/rede ate em componentes importados.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["YOLO_OFFLINE"] = "true"
os.environ["YOLO_AUTOINSTALL"] = "false"
os.environ["YOLO_CONFIG_DIR"] = str(RAIZ / "resultados/ls_teste_cache/ultralytics_config")

import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import linear_sum_assignment
from scipy.stats import wilcoxon
from src.data.taxonomia_layout import GUIA, GUIA_PARA_EXTRATOR, para_guia_do_extrator

CACHE = RAIZ / "resultados/ls_teste_cache"
RELATORIO = RAIZ / "resultados/extrator_vs_detector_ls_teste.md"
VERSAO = 1
CLASSES3 = ("texto", "tabela", "imagem")
ORIGENS = ("manual", "prediction", "prediction-changed", "ausente", "ambigua")
REGUAS = {"loc50": (None, .5), "loc75": (None, .75),
          "c3_50": (3, .5), "c3_75": (3, .75),
          "c9_50": (9, .5), "c9_75": (9, .75),
          "c16_50": (16, .5), "c16_75": (16, .75)}


def salvar(caminho, objeto):
    """Escrita atomica: uma queda nunca torna um cache parcial valido."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(objeto, f, ensure_ascii=False, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, caminho)


def ler(caminho):
    try:
        with caminho.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def sha(objeto):
    return hashlib.sha256(json.dumps(objeto, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def arquivo_id(caminho):
    s = caminho.stat()
    return [str(caminho.relative_to(RAIZ)), s.st_size, s.st_mtime_ns]


def codigo_id(*nomes):
    return sha([hashlib.sha256((RAIZ / n).read_bytes()).hexdigest() for n in nomes])


def assinatura_palavras(p):
    return sha([VERSAO, p["entrada_id"], codigo_id("src/data/extrator.py")])


def assinatura_docling(w):
    from src.data import layout
    return sha([VERSAO, w["assinatura"], layout.REVISAO, layout.DPI, layout.SCORE_CACHE,
                codigo_id("src/data/layout.py")])


def assinatura_extrator(w, d):
    return sha([VERSAO, w["assinatura"], d["assinatura"],
                codigo_id("src/data/regioes.py", "src/data/taxonomia_layout.py")])


def chave(p):
    return hashlib.sha256(p["page_id"].encode("utf-8")).hexdigest()[:24]


def caminho_cache(p, etapa):
    return CACHE / etapa / (chave(p) + ".json")


def jsonl(caminho):
    with caminho.open(encoding="utf-8") as f:
        for numero, linha in enumerate(f, 1):
            if linha.strip():
                try:
                    yield json.loads(linha)
                except ValueError as e:
                    raise ValueError(f"JSONL invalido: {caminho}:{numero}") from e


def tarefas_export(f):
    """Le array JSON incremental, mantendo somente uma tarefa na memoria."""
    dec, buf, pos, eof, iniciou = json.JSONDecoder(), "", 0, False, False
    while True:
        if pos:
            buf, pos = buf[pos:], 0
        if not buf.strip() and not eof:
            parte = f.read(65536)
            buf += parte
            eof = not parte
        buf = buf.lstrip()
        if not iniciou:
            if not buf or buf[0] != "[":
                raise ValueError("Export precisa ser uma lista JSON")
            buf, iniciou = buf[1:], True
        buf = buf.lstrip(" ,\t\r\n")
        if buf.startswith("]"):
            return
        try:
            obj, pos = dec.raw_decode(buf)
        except json.JSONDecodeError:
            if eof:
                raise ValueError("Export truncado ou invalido")
            parte = f.read(65536)
            buf += parte
            eof = not parte
            continue
        yield obj


def normalizar(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    # Um digito pode ser justamente o numero de pagina que distingue vizinhas.
    return re.findall(r"[a-z][a-z0-9]+|[0-9]+", t)


def mapa3(c):
    if c == "unknown":
        return None
    return {"table": "tabela", "figure": "imagem", "chart": "imagem", "heading": "imagem"}.get(c, "texto")


def classe(b, regua):
    c = b["classe"]
    if regua is None:
        return "*"
    if regua == 3:
        return c if c in CLASSES3 else mapa3(c)
    if regua == 9:
        return GUIA_PARA_EXTRATOR[c]
    return c


def caixas_export(ann, dimensoes):
    caixas = {}
    for item in ann.get("result") or []:
        if not isinstance(item, dict) or item.get("type") == "relation" or item.get("id") is None:
            continue
        c = caixas.setdefault(str(item["id"]), {})
        v = item.get("value") or {}
        tipo = item.get("type")
        if tipo in ("labels", "rectanglelabels"):
            nomes = v.get(tipo) or []
            if nomes:
                c["classe"] = nomes[0]
            c["origem_label"] = item.get("origin")
        if tipo == "textarea":
            texto = v.get("text") or []
            c["texto"] = "\n".join(texto) if isinstance(texto, list) else str(texto)
        if tipo == "rectangle":
            c["origem_retangulo"] = item.get("origin")
        if "bbox" not in c and all(k in v for k in ("x", "y", "width", "height")):
            W = item.get("original_width") or dimensoes[0]
            H = item.get("original_height") or dimensoes[1]
            x, y, w, h = (float(v[k]) for k in ("x", "y", "width", "height"))
            c["bbox"] = [x * W / 100, y * H / 100, (x+w) * W / 100, (y+h) * H / 100]
            c["rotacao"] = float(v.get("rotation") or 0)
    return caixas


def carregar_ouro():
    split = ler(RAIZ / "data/deteccao/ls_split.json")
    teste = {k: v for k, v in split["paginas"].items() if v.get("split") == "test"}
    fontes_teste = {v["fonte"] for v in teste.values()}
    assert not fontes_teste & {v["fonte"] for v in split["paginas"].values() if v["split"] != "test"}
    assert len(teste) == 317 and len(fontes_teste) == 42, "Split divergiu da tarefa"
    arquivos = [RAIZ / "data/deteccao/ls_split.json", RAIZ / "data/labelstudio/pdf_paginas.jsonl"]
    exports = []
    for seed in range(1, 5):
        arquivos.append(RAIZ / f"data/labelstudio/conv_seed{seed}/tarefas.jsonl")
        candidatos = list((RAIZ / "data/labelstudio").glob(f"ls_p*_seed{seed}.json"))
        assert len(candidatos) == 1, candidatos
        exports.append(candidatos[0])
    mapas = {p["page_id"]: p for p in jsonl(arquivos[1]) if p.get("page_id") in teste}
    insumos_paginas = []
    for pid, sp in sorted(teste.items()):
        insumos_paginas.append([arquivo_id(RAIZ / mapas[pid]["pdf_local"]),
                               arquivo_id(RAIZ / "data/deteccao/ls16/images/test" / sp["img"]),
                               *[arquivo_id(RAIZ / f"data/deteccao/ls{n}/labels/test" /
                                            (Path(sp["img"]).stem+".txt")) for n in (3, 16)]])
    assinatura = sha([VERSAO, [arquivo_id(f) for f in arquivos + exports], insumos_paginas])
    anterior = ler(CACHE / "ouro.json")
    if anterior and anterior.get("assinatura") == assinatura:
        return anterior["paginas"], anterior["auditoria"]
    convertidas, por_tarefa = {}, {}
    for seed in range(1, 5):
        for t in jsonl(RAIZ / f"data/labelstudio/conv_seed{seed}/tarefas.jsonl"):
            if t.get("page_id") in teste and teste[t["page_id"]]["seed"] == seed:
                convertidas[t["page_id"]] = t
                por_tarefa[(seed, t["task_id"])] = t
    assert set(convertidas) == set(teste) == set(mapas)
    audit = Counter()
    for seed, export in enumerate(exports, 1):
        with export.open(encoding="utf-8") as f:
            for tarefa in tarefas_export(f):
                t = por_tarefa.get((seed, tarefa.get("id")))
                if t is None:
                    continue
                W, H = t["dimensions"]["width"], t["dimensions"]["height"]
                candidatos = []
                for ann in tarefa.get("annotations") or []:
                    if not isinstance(ann, dict) or ann.get("was_cancelled"):
                        continue
                    cx = caixas_export(ann, (W, H))
                    erro = 0.
                    for b in t.get("bounding_boxes") or []:
                        a = cx.get(str(b["id"]), {})
                        erro += 10000 * (a.get("classe") != b.get("classe"))
                        erro += (sum(abs(x-y) for x, y in zip(a["bbox"], b["bbox"]))
                                 if "bbox" in a else 10000)
                        erro += 100 * (normalizar(a.get("texto", "")) != normalizar(b.get("text", "")))
                    extras = set(cx) - {str(b["id"]) for b in t.get("bounding_boxes") or []}
                    erro += 10000 * sum("bbox" in cx[k] for k in extras)
                    candidatos.append((erro, ann, cx))
                candidatos.sort(key=lambda x: x[0])
                assert candidatos, f"Sem anotacao nao cancelada: {t['page_id']}"
                melhor = candidatos[0][0]
                assert melhor <= max(1, .25 * len(t["bounding_boxes"])), (t["page_id"], melhor)
                iguais = [c for c in candidatos if abs(c[0]-melhor) < 1e-7]
                audit["paginas_multianotador"] += len(candidatos) > 1
                audit["anotacoes_equivalentes"] += len(iguais) > 1
                for b in t["bounding_boxes"]:
                    itens = [c[2][str(b["id"])] for c in iguais]
                    origens = {a.get("origem_label") or a.get("origem_retangulo") or "ausente" for a in itens}
                    b["origem"] = next(iter(origens)) if len(origens) == 1 else "ambigua"
                    b["origem_geometria"] = itens[0].get("origem_retangulo") or "ausente"
                    audit["rotacoes_ouro"] += bool(itens[0].get("rotacao"))
                    audit["origem_classe_geometria_diferente"] += (itens[0].get("origem_label") != itens[0].get("origem_retangulo"))
                t["anotacao_id"] = candidatos[0][1].get("id")
    paginas = []
    for pid, sp in sorted(teste.items()):
        t, mapa = convertidas[pid], mapas[pid]
        img = RAIZ / "data/deteccao/ls16/images/test" / sp["img"]
        with Image.open(img) as im:
            W, H = im.size
        assert (W, H) == (t["dimensions"]["width"], t["dimensions"]["height"]), pid
        ouro = []
        for b in t["bounding_boxes"]:
            if b.get("classe") not in GUIA:
                audit["classe_fora_guia"] += 1
                continue
            x0, y0, x1, y1 = b["bbox"]
            bb = [max(0, x0), max(0, y0), min(W, x1), min(H, y1)]
            if bb[2]-bb[0] < 1 or bb[3]-bb[1] < 1:
                audit["caixas_menores_1px"] += 1
                continue
            ouro.append({"id": str(b["id"]), "bbox": bb, "classe": b["classe"],
                         "texto": b.get("text") or "", "origem": b.get("origem", "ausente"),
                         "origem_geometria": b.get("origem_geometria", "ausente")})
        # Usa a geometria exata do YOLO; transcricao/origem permanecem associadas por ordem.
        for n, nomes in ((16, GUIA), (3, CLASSES3)):
            rotulo = RAIZ / f"data/deteccao/ls{n}/labels/test" / (Path(sp["img"]).stem + ".txt")
            linhas = [l.split() for l in rotulo.read_text(encoding="utf-8").splitlines() if l.strip()]
            esperado = ouro if n == 16 else [b for b in ouro if mapa3(b["classe"]) is not None]
            assert len(linhas) == len(esperado), (pid, n, len(linhas), len(esperado))
            for b, l in zip(esperado, linhas):
                cid, cx, cy, w, h = map(float, l)
                bb = [(cx-w/2)*W, (cy-h/2)*H, (cx+w/2)*W, (cy+h/2)*H]
                assert nomes[int(cid)] == (b["classe"] if n == 16 else mapa3(b["classe"])), pid
                assert max(abs(x-y) for x, y in zip(bb, b["bbox"])) < .004, (pid, b, bb)
                if n == 16:
                    b["bbox"] = bb
        assert all(b["origem"] in ORIGENS for b in ouro), pid
        p = {"page_id": pid, **sp, "pdf_local": mapa["pdf_local"], "pagina_ls": int(mapa["pagina"]),
             "width": W, "height": H, "ouro": ouro, "anotacao_id": t.get("anotacao_id")}
        p["entrada_id"] = sha([arquivo_id(RAIZ / p["pdf_local"]), arquivo_id(img),
                               p["pagina_ls"], p["width"], p["height"], ouro])
        paginas.append(p)
    salvar(CACHE / "ouro.json", {"assinatura": assinatura, "paginas": paginas, "auditoria": dict(audit)})
    return paginas, dict(audit)


def auditar_split():
    """Identifica aliases nominais com token de pagina e confere os cabecalhos."""
    split = ler(RAIZ / "data/deteccao/ls_split.json")["paginas"]
    por_canonica = defaultdict(list)
    nomes = {v["fonte"]: v["split"] for v in split.values()}
    for fonte, sp in nomes.items():
        canonica = " ".join(t for t in fonte.split() if t != "pag")
        por_canonica[canonica].append((fonte, sp))
    candidatos = []
    for canonica, grupo in por_canonica.items():
        testes = [n for n, sp in grupo if sp == "test"]
        outros = [n for n, sp in grupo if sp != "test"]
        if testes and outros:
            candidatos.append({"canonica": canonica, "testes": testes, "outros": outros})
    if not candidatos:
        return {"aliases": [], "paginas_afetadas": []}
    envolvidos = {n for c in candidatos for n in c["testes"]+c["outros"]}
    exemplos = {}
    for seed in range(1, 5):
        for t in jsonl(RAIZ / f"data/labelstudio/conv_seed{seed}/tarefas.jsonl"):
            fonte = split.get(t.get("page_id"), {}).get("fonte")
            if fonte not in envolvidos or fonte in exemplos:
                continue
            textos = [b.get("text") or "" for b in t.get("bounding_boxes") or []
                      if b.get("classe") == "header" and "oficial" in (b.get("text") or "").lower()]
            if textos:
                exemplos[fonte] = {"page_id": t["page_id"], "cabecalho": " / ".join(textos)}
    afetadas = []
    for c in candidatos:
        c["exemplos"] = {n: exemplos.get(n) for n in c["testes"]+c["outros"]}
        # Confirma por texto, sem deduzir identidade so da semelhanca do nome.
        cabecalhos = [" ".join(normalizar(e["cabecalho"])) if e else "" for e in c["exemplos"].values()]
        c["confirmado"] = (c["canonica"] == "df" and
                           all("diario oficial do distrito federal" in t for t in cabecalhos))
        c["paginas_teste"] = [pid for pid, v in split.items() if v["fonte"] in c["testes"]]
        if c["confirmado"]:
            afetadas += c["paginas_teste"]
    return {"aliases": candidatos, "paginas_afetadas": sorted(set(afetadas))}


def pdf_util(caminho):
    """Desembrulha PKCS#7 sob resultados, sem modificar o PDF de origem."""
    with caminho.open("rb") as f:
        prefixo = f.read(1024)
    if prefixo.startswith(b"%PDF"):
        return caminho, False
    dados = caminho.read_bytes()
    inicio, fim = dados.find(b"%PDF"), dados.rfind(b"%%EOF")
    if inicio < 0 or fim < inicio:
        raise ValueError("Arquivo sem trecho PDF valido")
    tmp = CACHE / "pdf_temporarios" / (sha(arquivo_id(caminho))[:24] + ".pdf")
    if not tmp.exists():
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as f:
            f.write(dados[inicio:fim+5])
    return tmp, True


def verificar_pagina(doc, p):
    """Compara 0/1-based com a transcricao; raster desempata paginas sem texto."""
    gold = Counter(normalizar(" ".join(b["texto"] for b in p["ouro"])))
    n = p["pagina_ls"]
    candidatos = sorted({i for i in (n-1, n) if 0 <= i < len(doc)})
    if not candidatos:
        raise ValueError(f"Indice LS {n} fora de PDF com {len(doc)} paginas")
    with Image.open(RAIZ / "data/deteccao/ls16/images/test" / p["img"]) as im:
        ref = np.asarray(im.convert("L").resize((96, 128)), dtype=float)
    resultados, tokens_de = [], {}
    for i in candidatos:
        pg = doc[i]
        texto = pg.get_text()
        tokens = Counter(normalizar(texto))
        tokens_de[i] = tokens
        cobertura = sum((gold & tokens).values()) / max(1, sum(gold.values()))
        pix = pg.get_pixmap(matrix=__import__("pymupdf").Matrix(.3, .3), alpha=False)
        imagem = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        arr = np.asarray(imagem.convert("L").resize((96, 128)), dtype=float)
        corr = (float(np.corrcoef(arr.ravel(), ref.ravel())[0, 1])
                if arr.std() > 1e-6 and ref.std() > 1e-6 else float(np.abs(arr-ref).mean() < 3))
        mae = float(np.abs(arr-ref).mean())
        resultados.append({"indice": i, "cobertura_texto": cobertura, "correlacao_imagem": corr,
                           "erro_imagem": mae, "n_tokens": sum(tokens.values())})
    resultados.sort(key=lambda r: (.65*r["cobertura_texto"] + .35*r["correlacao_imagem"]), reverse=True)
    escolhido = resultados[0]
    if escolhido["cobertura_texto"] < .20 and escolhido["correlacao_imagem"] < .80:
        raise ValueError(f"PDF/imagem/ouro sem correspondencia verificavel: {resultados}")
    if len(resultados) > 1:
        dif = (.65*(resultados[0]["cobertura_texto"]-resultados[1]["cobertura_texto"])
               + .35*(resultados[0]["correlacao_imagem"]-resultados[1]["correlacao_imagem"]))
        a, b = resultados[0]["indice"], resultados[1]["indice"]
        unicos_a = sum((gold & (tokens_de[a]-tokens_de[b])).values())
        unicos_b = sum((gold & (tokens_de[b]-tokens_de[a])).values())
        escolhido["tokens_discriminantes_ouro"] = unicos_a
        escolhido["tokens_discriminantes_alternativa"] = unicos_b
        evidencia_exclusiva = (unicos_a > 0 and unicos_b == 0 and
                              escolhido["correlacao_imagem"] >= .80 and
                              escolhido["correlacao_imagem"] > resultados[1]["correlacao_imagem"])
        if dif < .03 and not evidencia_exclusiva:
            raise ValueError(f"Indice ambiguo entre 0/1-based: {resultados}")
    return escolhido["indice"], {"candidatos": resultados, "paginas_pdf": len(doc),
                                 "base": 1 if escolhido["indice"] == n-1 else 0}


def extrair_palavras(p):
    """Worker sem torch: verifica pagina e congela as palavras do extrator original."""
    import pdfplumber
    import pymupdf
    from src.data.extrator import palavras_da_pagina
    entrada = assinatura_palavras(p)
    c = ler(caminho_cache(p, "palavras"))
    if c and c.get("assinatura") == entrada and not c.get("erro"):
        return p["page_id"], c, True
    inicio = time.perf_counter()
    try:
        pdf, envelope = pdf_util(RAIZ / p["pdf_local"])
        with pymupdf.open(pdf) as doc:
            indice, verificacao = verificar_pagina(doc, p)
        tempo_verificacao = (time.perf_counter()-inicio)*1000
        t = time.perf_counter()
        with pdfplumber.open(pdf) as doc:
            page = doc.pages[indice]
            ws = palavras_da_pagina(page)
            bbox = list(map(float, page.bbox))
            crop = list(map(float, page.cropbox)) if page.cropbox else bbox
            c = {"page_id": p["page_id"], "assinatura": entrada, "indice_pdf": indice,
                 "verificacao": verificacao, "envelope": envelope, "bbox_pagina": bbox,
                 "cropbox": crop, "rotacao": int(page.rotation or 0), "ws": ws,
                 "sem_texto": not any(re.search(r"[A-Za-z0-9À-ÿ]", w["t"]) for w in ws),
                 "texto_escasso": 0 < len(ws) < 5, "tempo_palavras_ms": (time.perf_counter()-t)*1000,
                 "tempo_verificacao_ms": tempo_verificacao}
        salvar(caminho_cache(p, "palavras"), c)
    except Exception as e:
        c = {"page_id": p["page_id"], "assinatura": entrada, "erro": f"{type(e).__name__}: {e}"}
        salvar(caminho_cache(p, "palavras"), c)
    return p["page_id"], c, False


def preparar_docling(p, palavras, detector):
    """Renderiza como layout.py (DPI e CropBox), depois infere em CPU."""
    import pdfplumber
    from src.data import layout
    entrada = assinatura_docling(palavras)
    c = ler(caminho_cache(p, "docling"))
    if c and c.get("assinatura") == entrada and not c.get("erro"):
        return c, True
    pdf, _ = pdf_util(RAIZ / p["pdf_local"])
    t = time.perf_counter()
    with pdfplumber.open(pdf) as doc:
        page = doc.pages[palavras["indice_pdf"]]
        if (page.rotation or 0) % 360 and tuple(page.cropbox) != tuple(page.mediabox):
            raise ValueError("Rotacao com CropBox: layout.py considera coordenadas nao confiaveis")
        pi = page.to_image(resolution=layout.DPI)
        imagem = pi.original.convert("RGB")
        bbox, escala = list(map(float, pi.bbox)), float(pi.scale)
    render_ms = (time.perf_counter()-t)*1000
    if abs(imagem.width/imagem.height - p["width"]/p["height"]) > .015:
        raise ValueError("Aspecto da imagem LS difere do recorte do PDF")
    t = time.perf_counter()
    regioes = detector([imagem], [(bbox, escala)])[0]
    c = {"page_id": p["page_id"], "assinatura": entrada, "modelo": layout.MODELO,
         "revisao": layout.REVISAO, "dispositivo": "cpu", "dpi": layout.DPI, "bbox_imagem": bbox,
         "escala": escala, "regioes": regioes, "tempo_render_ms": render_ms,
         "tempo_docling_ms": (time.perf_counter()-t)*1000}
    salvar(caminho_cache(p, "docling"), c)
    return c, False


def propor_pagina(p, w, d):
    """Reproduz preparar_diamond; converte pontos para pixels no recorte visivel."""
    from src.data.extrator import segmentar
    from src.data import layout, regioes
    assinatura = assinatura_extrator(w, d)
    c = ler(caminho_cache(p, "extrator"))
    if c and c.get("assinatura") == assinatura and not c.get("erro"):
        return c, True
    t = time.perf_counter()
    ws = w["ws"]
    blocos = segmentar(ws, layout.tabelas(d["regioes"]))
    bloco_de = {id(word): i for i, B in enumerate(blocos) for L in B["linhas"] for word in L["ws"]}
    ox, oy = w["bbox_pagina"][:2]
    palavras = [[z["t"], round(z["x0"]-ox, 2), round(z["top"]-oy, 2),
                 round(z["x1"]-ox, 2), round(z["bottom"]-oy, 2), bloco_de.get(id(z), -1)] for z in ws]
    v3 = [{"id": f"v{i}", "bbox": [round(B["x0"]-ox, 1), round(B["top"]-oy, 1),
                                   round(B["x1"]-ox, 1), round(B["bottom"]-oy, 1)],
           **({"tipo": "tabela"} if B.get("tabela") else {})} for i, B in enumerate(blocos)]
    det = [{**r, "bbox": [r["bbox"][0]-ox, r["bbox"][1]-oy, r["bbox"][2]-ox, r["bbox"][3]-oy]}
           for r in d["regioes"] if r["score"] >= regioes.SCORE_MIN]
    proposta = regioes.propor(palavras, v3, det, regras=True)
    caixas = []
    x0, y0, x1, y1 = d["bbox_imagem"]
    sx, sy = p["width"]/(x1-x0), p["height"]/(y1-y0)
    for r in proposta:
        a, b, c1, d1 = r["bbox"]
        bb = [max(0., (a+ox-x0)*sx), max(0., (b+oy-y0)*sy),
              min(float(p["width"]), (c1+ox-x0)*sx), min(float(p["height"]), (d1+oy-y0)*sy)]
        if bb[2] <= bb[0] or bb[3] <= bb[1]:
            continue
        caixas.append({"id": r["id"], "bbox": bb, "classe": para_guia_do_extrator(r["classe"]),
                       "classe_original": r["classe"], "origem": r["origem"], "score": r["score"]})
    regras_ms = (time.perf_counter()-t)*1000
    c = {"page_id": p["page_id"], "assinatura": assinatura, "caixas": caixas,
         "palavras": palavras, "blocos_v3": v3, "proposta_pontos": proposta,
         "tempo_regras_ms": regras_ms,
         "tempo_ms": w["tempo_palavras_ms"]+d["tempo_render_ms"]+d["tempo_docling_ms"]+regras_ms}
    salvar(caminho_cache(p, "extrator"), c)
    return c, False


def matriz_iou(g, p):
    if not g or not p:
        return np.zeros((len(g), len(p)))
    a, b = np.array([r["bbox"] for r in g]), np.array([r["bbox"] for r in p])
    inicio = np.maximum(a[:, None, :2], b[None, :, :2])
    fim = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.maximum(0, fim-inicio).prod(axis=2)
    area_a = np.maximum(0, a[:, 2:]-a[:, :2]).prod(axis=1)
    area_b = np.maximum(0, b[:, 2:]-b[:, :2]).prod(axis=1)
    return inter / np.maximum(1e-12, area_a[:, None]+area_b[None, :]-inter)


def emparelhar(g, p, limiar=.5, regua=None):
    """Maximiza TP primeiro, depois IoU. Cada caixa participa no maximo uma vez."""
    gs = [i for i, b in enumerate(g) if classe(b, regua) is not None]
    ps = [i for i, b in enumerate(p) if classe(b, regua) is not None]
    a, b = [g[i] for i in gs], [p[i] for i in ps]
    ious = matriz_iou(a, b)
    validos = ious >= limiar
    if regua is not None:
        validos &= np.array([[classe(x, regua) == classe(y, regua) for y in b] for x in a],
                            dtype=bool).reshape(ious.shape)
    pares = []
    if len(a) and len(b):
        ganho = validos * (1 + ious/(min(len(a), len(b))+1))
        ii, jj = linear_sum_assignment(-ganho)
        pares = [(gs[i], ps[j], float(ious[i, j])) for i, j in zip(ii, jj) if validos[i, j]]
    return [len(pares), len(b)-len(pares), len(a)-len(pares)], pares


def f1(cont):
    tp, fp, fn = np.asarray(cont).T
    den = 2*tp+fp+fn
    return np.divide(2*tp, den, out=np.zeros_like(den, dtype=float), where=den != 0)


def intervalo(contagens, B, seed=20261003):
    a = np.asarray(contagens, dtype=float)
    if not len(a):
        return None
    rng = np.random.default_rng(seed)
    ids = rng.integers(0, len(a), (B, len(a)))
    estimativas = f1(a[ids].sum(axis=1))
    return [float(x) for x in np.percentile(estimativas, [2.5, 97.5])]


def numero(v, casas=3):
    return "—" if v is None else f"{v:.{casas}f}".replace(".", ",")


def ic_texto(v, ic):
    return f"{numero(v)} [{numero(ic[0])}; {numero(ic[1])}]" if ic else numero(v)


def prever_yolo(nome, paginas, threads):
    from ultralytics import YOLO
    peso = RAIZ / f"runs/detect/{nome}/weights/best.pt"
    peso_sha = hashlib.sha256(peso.read_bytes()).hexdigest()
    assinatura_modelo = sha([VERSAO, peso_sha, "cpu", 1024, .25, .7, 300])
    pendentes = []
    for p in paginas:
        c = ler(caminho_cache(p, nome))
        assinatura = sha([assinatura_modelo, p["entrada_id"]])
        if not c or c.get("assinatura") != assinatura or c.get("erro"):
            pendentes.append((p, assinatura))
    if not pendentes:
        print(f"[{nome}] cache completo ({len(paginas)} paginas)", flush=True)
        return
    t = time.perf_counter()
    modelo = YOLO(str(peso))
    modelo.to("cpu")
    nomes = set(modelo.names.values())
    assert nomes == set(GUIA if nome == "ls16" else CLASSES3), (nome, modelo.names)
    print(f"[{nome}] CPU; carga {time.perf_counter()-t:.2f}s; {len(pendentes)} paginas novas", flush=True)
    # Aquecimento igual para todas; excluido da latencia por pagina.
    modelo.predict(Image.new("RGB", (1024, 1024), "white"), device="cpu", imgsz=1024,
                   conf=.25, iou=.7, max_det=300, verbose=False, save=False)
    for k, (p, assinatura) in enumerate(pendentes, 1):
        t = time.perf_counter()
        resultado = modelo.predict(str(RAIZ / "data/deteccao/ls16/images/test" / p["img"]),
                                   device="cpu", imgsz=1024, conf=.25, iou=.7, max_det=300,
                                   verbose=False, save=False)[0]
        tempo_ms = (time.perf_counter()-t)*1000
        caixas = [{"id": str(i), "bbox": list(map(float, bb)), "classe": modelo.names[int(cid)],
                   "score": float(score)} for i, (bb, cid, score) in enumerate(zip(
                       resultado.boxes.xyxy.tolist(), resultado.boxes.cls.tolist(), resultado.boxes.conf.tolist()))]
        salvar(caminho_cache(p, nome), {"page_id": p["page_id"], "assinatura": assinatura,
                                      "peso_sha256": peso_sha, "peso_stat": arquivo_id(peso),
                                      "entrada_id": p["entrada_id"], "caixas": caixas, "tempo_ms": tempo_ms,
                                      "dispositivo": "cpu", "imgsz": 1024, "conf": .25, "iou_nms": .7})
        if k % 10 == 0 or k == len(pendentes):
            print(f"[{nome}] {k}/{len(pendentes)}", flush=True)
    del modelo


def avaliar(paginas, auditoria, B, status):
    auditoria_split = ler(CACHE / "auditoria_split.json") or {"aliases": [], "paginas_afetadas": []}
    sistemas = {"extrator": {}}
    for nome in ("ls3", "ls16"):
        if status[nome]["incluido"]:
            sistemas[nome] = {}
    palavras = {}
    for p in paginas:
        w = ler(caminho_cache(p, "palavras"))
        if w and w.get("assinatura") == assinatura_palavras(p) and not w.get("erro"):
            palavras[p["page_id"]] = w
        for nome in sistemas:
            c = ler(caminho_cache(p, nome))
            valido = False
            if nome == "extrator" and p["page_id"] in palavras:
                d = ler(caminho_cache(p, "docling"))
                valido = bool(d and d.get("assinatura") == assinatura_docling(w) and
                              c and c.get("assinatura") == assinatura_extrator(w, d))
            elif nome != "extrator" and c:
                valido = (c.get("peso_stat") == arquivo_id(RAIZ / f"runs/detect/{nome}/weights/best.pt")
                          and c.get("entrada_id") == p["entrada_id"] and c.get("imgsz") == 1024
                          and c.get("dispositivo") == "cpu" and c.get("conf") == .25 and c.get("iou_nms") == .7)
            if valido and c and not c.get("erro") and "caixas" in c:
                sistemas[nome][p["page_id"]] = c
    metricas, resumo, origens, por_fonte, latencias, erros = {}, {}, {}, {}, {}, {}
    for nome, preds in sistemas.items():
        metricas[nome] = {}
        origens[nome] = {o: {"n": 0, "tp_loc": 0, "n3": 0, "tp3": 0} for o in ORIGENS}
        erros[nome] = {"confusoes9": Counter(), "perdidas_classe": Counter(), "fp_classe": Counter(),
                       "divisao": 0, "fusao": 0, "classe_errada3": 0, "localizacao": 0}
        for p in paginas:
            pid = p["page_id"]
            if pid not in preds:
                continue
            g, pred = p["ouro"], preds[pid]["caixas"]
            m = {}
            reguas = [k for k in REGUAS if ("c16" not in k or nome == "ls16") and ("c9" not in k or nome != "ls3")]
            for k in reguas:
                regua, limiar = REGUAS[k]
                cont, pares = emparelhar(g, pred, limiar, regua)
                m[k] = cont
                if k in ("loc50", "c3_50"):
                    achados = {x[0] for x in pares}
                    for i, caixa in enumerate(g):
                        o = origens[nome][caixa["origem"]]
                        if k == "loc50":
                            o["n"] += 1
                            o["tp_loc"] += i in achados
                        elif mapa3(caixa["classe"]) is not None:
                            o["n3"] += 1
                            o["tp3"] += i in achados
            metricas[nome][pid] = m
            _, pares = emparelhar(g, pred)
            gs, ps = {i for i, _, _ in pares}, {j for _, j, _ in pares}
            for i, j, _ in pares:
                if nome != "ls3":
                    a, b = GUIA_PARA_EXTRATOR[g[i]["classe"]], GUIA_PARA_EXTRATOR[pred[j]["classe"]]
                    if a != b:
                        erros[nome]["confusoes9"][(a, b)] += 1
                if mapa3(g[i]["classe"]) is not None and classe(g[i], 3) != classe(pred[j], 3):
                    erros[nome]["classe_errada3"] += 1
            for i in range(len(g)):
                if i not in gs:
                    erros[nome]["perdidas_classe"][g[i]["classe"]] += 1
            for j in range(len(pred)):
                if j not in ps:
                    erros[nome]["fp_classe"][pred[j]["classe"]] += 1
            # Indicios descritivos de divisao/fusao: >=2 caixas com intersecao >=50% da menor.
            a = np.array([x["bbox"] for x in g], dtype=float).reshape(-1, 4)
            b = np.array([x["bbox"] for x in pred], dtype=float).reshape(-1, 4)
            inter = np.maximum(0, np.minimum(a[:, None, 2:], b[None, :, 2:])-
                               np.maximum(a[:, None, :2], b[None, :, :2])).prod(axis=2)
            areas = np.minimum(np.maximum(0, a[:, 2:]-a[:, :2]).prod(axis=1)[:, None],
                               np.maximum(0, b[:, 2:]-b[:, :2]).prod(axis=1)[None, :])
            ov = inter/np.maximum(1e-12, areas) >= .5
            erros[nome]["divisao"] += int((ov.sum(axis=1) >= 2).sum())
            erros[nome]["fusao"] += int((ov.sum(axis=0) >= 2).sum())
        resumo[nome] = {}
        for k in next(iter(metricas[nome].values()), {}):
            conts = [m[k] for m in metricas[nome].values()]
            soma = np.array(conts).sum(axis=0).tolist()
            resumo[nome][k] = {"contagens": soma, "f1": float(f1(soma)), "ic95": intervalo(conts, B),
                               "f1_macro": float(np.mean(f1(conts)))}
        lat = np.array([x["tempo_ms"] for x in preds.values()])
        latencias[nome] = ({"n": len(lat), "media_ms": float(lat.mean()), "mediana_ms": float(np.median(lat)),
                           "p95_ms": float(np.percentile(lat, 95)), "total_s": float(lat.sum()/1000)} if len(lat) else {})
        fontes = defaultdict(list)
        for p in paginas:
            if p["page_id"] in metricas[nome]:
                fontes[p["fonte"]].append(metricas[nome][p["page_id"]]["c3_50"])
        por_fonte[nome] = {f: {"n": len(c), "f1": float(f1(np.array(c).sum(axis=0))), "ic95": intervalo(c, B)}
                            for f, c in fontes.items()}
    melhores = [n for n in ("ls3", "ls16") if len(metricas.get(n, {})) == len(paginas)]
    melhor = max(melhores, key=lambda n: resumo[n]["c3_50"]["f1"]) if melhores else None
    pareado = None
    if melhor:
        ids = sorted(set(metricas["extrator"]) & set(metricas[melhor]))
        if ids:
            e = np.array([float(f1(metricas["extrator"][i]["c3_50"])) for i in ids])
            d = np.array([float(f1(metricas[melhor][i]["c3_50"])) for i in ids])
            delta = d-e
            rng = np.random.default_rng(20261003)
            amostras = delta[rng.integers(0, len(delta), (B, len(delta)))].mean(axis=1)
            pvalor = float(wilcoxon(d, e, zero_method="wilcox", alternative="two-sided", method="approx").pvalue) if np.any(delta) else 1.
            pareado = {"detector": melhor, "n": len(ids), "delta_macro": float(delta.mean()),
                       "ic95": np.percentile(amostras, [2.5, 97.5]).tolist(), "p_wilcoxon": pvalor,
                       "ganha_detector": int((delta > 1e-12).sum()), "ganha_extrator": int((delta < -1e-12).sum()),
                       "empates": int((np.abs(delta) <= 1e-12).sum())}
    estratos = {}
    for nome in sistemas:
        estratos[nome] = {}
        for tipo in ("com_texto", "sem_texto", "texto_escasso"):
            ids = [p["page_id"] for p in paginas if p["page_id"] in palavras and p["page_id"] in metricas[nome]
                   and (palavras[p["page_id"]]["texto_escasso"] if tipo == "texto_escasso"
                        else palavras[p["page_id"]]["sem_texto"] == (tipo == "sem_texto"))]
            estratos[nome][tipo] = {"n": len(ids)}
            for k in ("loc50", "loc75", "c3_50", "c3_75"):
                conts = [metricas[nome][pid][k] for pid in ids]
                if conts:
                    estratos[nome][tipo][k] = float(f1(np.array(conts).sum(axis=0)))
    erros_json = {}
    for nome, er in erros.items():
        erros_json[nome] = {k: ([[str(a), str(b), n] for (a, b), n in v.most_common()] if k == "confusoes9"
                               else dict(v) if isinstance(v, Counter) else v) for k, v in er.items()}
    sensibilidade = {}
    for nome in sistemas:
        ids = [pid for pid in metricas[nome] if pid not in auditoria_split["paginas_afetadas"]]
        if ids and auditoria_split["paginas_afetadas"]:
            conts = [metricas[nome][pid]["c3_50"] for pid in ids]
            sensibilidade[nome] = {"n": len(ids), "f1": float(f1(np.array(conts).sum(axis=0))),
                                   "ic95": intervalo(conts, B)}
    out = {"gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"), "bootstrap": B,
           "n_paginas": len(paginas), "n_fontes": len({p["fonte"] for p in paginas}), "auditoria": auditoria,
           "auditoria_split": auditoria_split, "sensibilidade_alias": sensibilidade,
           "n_ouro": sum(len(p["ouro"]) for p in paginas), "n_ouro3": sum(mapa3(b["classe"]) is not None for p in paginas for b in p["ouro"]),
           "status_detectores": status, "cobertura": {n: len(p) for n, p in sistemas.items()},
           "resumo": resumo, "origens": origens, "por_fonte": por_fonte, "latencias": latencias,
           "pareado": pareado, "estratos": estratos, "erros": erros_json, "metricas_paginas": metricas,
           "sem_texto": sum(w["sem_texto"] for w in palavras.values()), "palavras_concluidas": len(palavras),
           "envelopes_paginas": sum(w["envelope"] for w in palavras.values()),
           "indice_base": dict(Counter(str(w["verificacao"]["base"]) for w in palavras.values())),
           "indice_confirmado_texto": sum(w["verificacao"]["candidatos"][0]["cobertura_texto"] >= .20 for w in palavras.values()),
           "falhas_pdf": {p["page_id"]: w["erro"] for p in paginas if (w := ler(caminho_cache(p, "palavras"))) and w.get("erro")}}
    out["falhas_extrator"] = ler(CACHE / "falhas_extrator.json") or {}
    salvar(CACHE / "metricas.json", out)
    escrever_relatorio(out, paginas, sistemas, palavras)
    verificar_relatorio(out)
    return out


def verificar_relatorio(r):
    """Confere numericamente a tabela escrita, com arredondamento explicitado."""
    texto = RELATORIO.read_text(encoding="utf-8")
    tabela = texto.split("## Tabela principal", 1)[1].split("| Detector |", 1)[0]
    for nome, res in r["resumo"].items():
        linha = next(l for l in tabela.splitlines() if l.startswith(f"| {nome} |"))
        col = [c.strip() for c in linha.split("|")[1:-1]]
        assert int(col[1]) == r["cobertura"][nome]
        for i, k in enumerate(("loc50", "loc75", "c3_50", "c3_75", "c9_50", "c16_50"), 2):
            if k in res:
                valor = float(col[i].split(" [", 1)[0].replace(",", "."))
                assert abs(valor-res[k]["f1"]) <= .0005000001, (nome, k, valor, res[k])
            else:
                assert col[i] == "—"
        lat = r["latencias"][nome].get("media_ms")
        if lat is not None:
            assert abs(float(col[-1].replace(",", "."))-lat) <= .05000001
    salvar(CACHE / "verificacao_relatorio.json", {"ok": True, "tabela_principal": "confere com metricas.json",
                                                "sha256_relatorio": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
                                                "cobertura": r["cobertura"]})


def escrever_relatorio(r, paginas, sistemas, palavras):
    nomes = list(sistemas)
    cobertura = r["cobertura"]
    completa = cobertura.get("extrator", 0) == r["n_paginas"]
    ausentes = [n for n, s in r["status_detectores"].items() if not s["incluido"]]
    pareado = r["pareado"]
    if pareado and completa:
        vencedor = pareado["detector"] if r["resumo"][pareado["detector"]]["c3_50"]["f1"] > r["resumo"]["extrator"]["c3_50"]["f1"] else "extrator"
        veredito = f"{vencedor} tem o maior F1 de 3 classes a IoU 0,50 no teste observado; a escolha do melhor detector é exploratória."
    else:
        vencedor = None
        veredito = "Sem detector concluído e avaliado: não há vencedor comparativo; só é possível estabelecer a linha de base do extrator."
    linhas = ["# Extrator × detectores — teste de layout do Label Studio", "", "## Resumo de cinco linhas", "",
              f"1. **Veredito:** {veredito}",
              f"2. Universo: {r['n_paginas']} páginas de {r['n_fontes']} chaves nominais de fonte no teste; {len(r['auditoria_split']['paginas_afetadas'])} página(s) com alias confirmado de fonte do treino/validação; {r['n_ouro']} caixas de ouro ({r['n_ouro3']} em 3 classes).",
              f"3. Cobertura: " + "; ".join(f"{n}: {cobertura[n]}/{r['n_paginas']}" for n in nomes) +
              f". Detectores fora: {', '.join(ausentes) or 'nenhum'}.",
              f"4. PDFs sem texto: {r['sem_texto']}, entre {r['palavras_concluidas']} páginas inspecionadas; {r['envelopes_paginas']} páginas em envelopes PKCS#7; índice verificado antes da extração.",
              "5. Uso interno do parceiro Data Policy. Ouro corrigido de pré-anotação tem viés de ancoragem; separação nominal de fontes não elimina esse viés nem resolve aliases.", "",
              f"Gerado pelo script em {r['gerado_em']}. " + ("Execução completa do extrator." if completa else "**Execução parcial: números provisórios nas páginas disponíveis.**"), "",
              "## Tabela principal", "",
              "F1 micro por caixa; IC 95% por bootstrap de páginas entre colchetes. Régua comum principal: 3 classes, IoU ≥ 0,50. Nenhum limiar foi escolhido no teste.", "",
              "| Sistema | Páginas | Localização 0,50 | Localização 0,75 | 3 classes 0,50 | 3 classes 0,75 | 9 classes 0,50 | 16 classes 0,50 | ms/página (média) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for n in nomes:
        res = r["resumo"][n]
        vals = [ic_texto(res[k]["f1"], res[k]["ic95"]) if k in res else "—" for k in ("loc50", "loc75", "c3_50", "c3_75", "c9_50", "c16_50")]
        linhas.append(f"| {n} | {cobertura[n]} | " + " | ".join(vals) + f" | {numero(r['latencias'][n].get('media_ms'), 1)} |")
    for n in ausentes:
        linhas.append(f"| {n} (fora) | 0 | — | — | — | — | — | — | — |")
    linhas += ["", "| Detector | `treino_ok` | Checkpoint | Situação nesta execução |", "|---|---|---|---|"]
    for n, s in r["status_detectores"].items():
        linhas.append(f"| {n} | {'existe' if s['treino_ok'] else 'ausente'} | {'existe' if s['checkpoint'] else 'ausente'} | {s['motivo']} |")
    if r["auditoria_split"]["aliases"]:
        linhas += ["", "**Auditoria do split: a premissa de fontes inteiramente inéditas tem uma exceção confirmada.** A tabela principal preserva todas as páginas e rótulos pedidos; não alteramos o arquivo de split."]
        for a in r["auditoria_split"]["aliases"]:
            linhas += [f"- Alias {', '.join(a['testes'])} no teste ↔ {', '.join(a['outros'])} no treino/validação: {len(a['paginas_teste'])} página(s) de teste; identidade {'confirmada por cabeçalhos' if a['confirmado'] else 'a conferir'}."]
            for fonte, ex in a["exemplos"].items():
                if ex:
                    cabecalho = " ".join(ex["cabecalho"].split())[:180]
                    linhas.append(f"  Evidência {fonte}: `{ex['page_id']}`; cabeçalho “{cabecalho}”.")
        linhas += ["", "Sensibilidade exploratória excluindo somente páginas dos aliases confirmados; não substitui o resultado principal nem redefine o conjunto oficial:", "",
                   "| Sistema | Páginas sem alias confirmado | F1 3 classes 0,50 (IC 95%) |", "|---|---:|---:|"]
        for nome, v in r["sensibilidade_alias"].items():
            linhas.append(f"| {nome} | {v['n']} | {ic_texto(v['f1'],v['ic95'])} |")
    linhas += ["", "## Protocolo e conferência do ouro", "",
               "A referência é exatamente o teste exportado para YOLO; todas as classes e coordenadas foram conferidas contra `conv_seed1..4/tarefas.jsonl`. Caixas são limitadas à imagem; o filtro existente de largura/altura menor que 1 pixel é reproduzido. O script associa cada caixa por ID à anotação não cancelada que reproduz geometria, classe e transcrição convertidas. Em empate com origens diferentes usa `ambigua`, sem escolher um anotador arbitrariamente.",
               f"Há {r['auditoria'].get('paginas_multianotador',0)} páginas com múltiplas anotações candidatas; {r['auditoria'].get('anotacoes_equivalentes',0)} com anotações equivalentes. Rotações de caixas no ouro: {r['auditoria'].get('rotacoes_ouro',0)}. Origem de rótulo e retângulo diferentes: {r['auditoria'].get('origem_classe_geometria_diferente',0)} caixas. Filtro <1px: {r['auditoria'].get('caixas_menores_1px',0)}; classes fora do guia: {r['auditoria'].get('classe_fora_guia',0)}.",
               "O índice informado pelo LS é comparado nas alternativas zero/um com as transcrições (cobertura de tokens normalizados) e com o raster da imagem. Em páginas quase idênticas, tokens exclusivos da candidata presentes no ouro, ausentes na alternativa, e raster mais parecido confirmam o índice. Índices ainda ambíguos ou PDFs sem correspondência são registrados como falha, sem avaliar outra página. A verificação textual usa o ouro somente para identificar a página; essas transcrições não entram no extrator nem nos modelos.",
               f"Base inferida entre as páginas concluídas: {r['indice_base']}; {r['indice_confirmado_texto']} confirmadas com cobertura textual ≥ 0,20. As restantes dependem da correspondência visual. Falhas técnicas de PDF/índice: {len(r['falhas_pdf'])}.",
               "O extrator reproduz palavras_da_pagina → segmentar(com tabelas Docling) → palavras/blocos_v3/detector → propor(regras=True, fundir=True). O Docling Heron usa a revisão fixada em layout.py, CPU, DPI do módulo, limiar de cache 0,30 e de proposta 0,45. Portanto esta linha de base contém um detector visual pré-treinado, além das regras. A transformação pontos→pixels respeita a origem do recorte do raster; não supõe página em (0,0).",
               f"As 9 classes são a régua histórica do extrator, colapsada por GUIA_PARA_EXTRATOR: lista do extrator vira paragraph→texto. O mapa do guia ocupa {len(set(GUIA_PARA_EXTRATOR.values()))} classes distintas, pois o guia não tem lista. As 3 classes: table→tabela; figure/chart/heading→imagem; unknown excluído; demais→texto. O mapa assinatura→signature perde a distinção de rubrica manuscrita: limitação real, sem usar o ouro para resolver. Localização sem classe inclui unknown também para ls3, que não foi treinado para detectá-lo. Na régua 3 classes removemos caixas unknown de ouro e predições; não ignoramos outra predição só por tocar um unknown.",
               "Emparelhamento bipartido um a um, maximizando primeiro o número de pares válidos e depois IoU; classe precisa coincidir na régua correspondente. TP, FP e FN são somados antes de calcular F1=2TP/(2TP+FP+FN). Página sem ouro e sem predição tem F1 por página definido como zero (sem contribuição ao micro). Não medimos mAP nem ordem de leitura nesta tarefa.",
               f"Bootstrap: {r['bootstrap']} reamostras de páginas com reposição, semente 20261003. O IC não incorpora dependência entre páginas da mesma fonte; pode ser estreito demais. Por fonte, n pequeno (ou uma única página) torna o IC instável ou degenerado.", "",
               "| Sistema / régua | TP | FP | FN | F1 micro | F1 macro por página |", "|---|---:|---:|---:|---:|---:|"]
    for n in nomes:
        for k, v in r["resumo"][n].items():
            linhas.append(f"| {n} / {k} | " + " | ".join(map(str, v["contagens"])) + f" | {numero(v['f1'])} | {numero(v['f1_macro'])} |")
    linhas += ["", "## Páginas com e sem camada de texto", "", "Sem texto = nenhuma palavra alfanumérica extraída; isso sugere digitalização, mas não prova ausência de texto visual. Página digitalizada com OCR embutido ou só cabeçalho textual e corpo digitalizado pertence ao grupo com texto. Texto escasso (<5 palavras) é também mostrado como subconjunto de com texto; não é somado de novo ao total.", "",
               "| Sistema | Estrato | Páginas | Localização 0,50 | Localização 0,75 | 3 classes 0,50 |", "|---|---|---:|---:|---:|---:|"]
    for n in nomes:
        for tipo, v in r["estratos"][n].items():
            linhas.append(f"| {n} | {tipo} | {v['n']} | {numero(v.get('loc50'))} | {numero(v.get('loc75'))} | {numero(v.get('c3_50'))} |")
    linhas += ["", "O extrator pode preservar figuras detectadas visualmente sem texto, mas descarta outras regiões sem palavras; a separação é necessária para não esconder essa dependência. O detector lê a imagem e independe da camada textual.", "", "## Ancoragem", "",
               "Origem principal = campo origin do item labels; fallback para rectangle quando labels não tem origem. A revocação usa o emparelhamento global e só depois agrupa as caixas do ouro; uma predição não pode acertar mais de uma caixa por origem.", "",
               "| Sistema | Origem | Caixas (todas) | TP localização 0,50 | Revocação localização | Caixas (3 classes) | TP com classe | Revocação 3 classes |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for n in nomes:
        for o, v in r["origens"][n].items():
            linhas.append(f"| {n} | {o} | {v['n']} | {v['tp_loc']} | {numero(v['tp_loc']/v['n'] if v['n'] else None)} | {v['n3']} | {v['tp3']} | {numero(v['tp3']/v['n3'] if v['n3'] else None)} |")
    for n in nomes:
        por = r["origens"][n]
        manual, mantida, alterada = (por[o] for o in ("manual", "prediction", "prediction-changed"))
        if manual["n"] and mantida["n"] and alterada["n"]:
            linhas += [f"\n{n}: revocação de localização em caixas mantidas−manuais = {numero(mantida['tp_loc']/mantida['n']-manual['tp_loc']/manual['n'])}; alteradas−manuais = {numero(alterada['tp_loc']/alterada['n']-manual['tp_loc']/manual['n'])}. São diferenças brutas, sem ajuste por dificuldade, fonte ou classe."]
    if not pareado:
        linhas += ["", "**Herança de viés do pré-anotador: ainda não testável entre sistemas**, pois falta detector concluído com cobertura total. As diferenças de revocação por origem do extrator são descritivas."]
    else:
        linhas += ["", "Diferenças de revocação por origem são compatíveis com herança de ancoragem, mas não a demonstram: as caixas manuais podem ser menores, mais difíceis, de classes/fontes distintas; prediction-changed pode significar só troca de classe ou texto. Sem teste desenhado do zero e sem controlar dificuldade/classe/fonte não é possível atribuir a diferença causalmente ao pré-anotador."]
    linhas += ["", "Mesmo manual é uma caixa adicionada enquanto a pré-anotação estava visível; não equivale a uma página anotada às cegas do zero. A origem é metadado do LS e não reconstrói todas as edições. Fontes inéditas evitam vazamento de layout do treino, mas preservam a mesma maneira de construir o ouro.", "",
               "## Por fonte e teste pareado", "", "Régua: F1 micro de 3 classes a IoU 0,50, IC por bootstrap das páginas da própria fonte. Uma fonte com uma página tem IC degenerado; a marca † sinaliza n<5. 'Sem comparação' significa que não há detector pronto em todas as páginas da fonte.", "",
               "| Fonte | Páginas | " + " | ".join(nomes) + " | Maior F1 observado |", "|---|---:|" + "---:|"*len(nomes) + "---|"]
    contagem_fontes = Counter(p["fonte"] for p in paginas)
    vitorias = Counter()
    for fonte, n in sorted(contagem_fontes.items()):
        vals = [r["por_fonte"][s].get(fonte) for s in nomes]
        completos = {s: v for s, v in zip(nomes, vals) if v and v["n"] == n}
        if len(completos) >= 2 and "extrator" in completos:
            maximo = max(v["f1"] for v in completos.values())
            ganha = [s for s, v in completos.items() if abs(v["f1"]-maximo) < 1e-12]
            quem = "/".join(ganha)
            vitorias[quem] += 1
        else:
            quem = "Sem comparação"
        linhas.append(f"| {fonte}{' †' if n<5 else ''} | {n} | " + " | ".join(ic_texto(v["f1"], v["ic95"]) if v else "—" for v in vals) + f" | {quem} |")
    linhas += ["", "Vitórias por fonte (descritivas, sem teste múltiplo por fonte): " + (str(dict(vitorias)) if vitorias else "não calculáveis nesta execução") + "."]
    if pareado:
        linhas += [f"Melhor detector observado: {pareado['detector']} (seleção pelo F1 micro 3 classes no próprio teste). Wilcoxon bilateral, pareado nos F1 por página: n={pareado['n']}, p={numero(pareado['p_wilcoxon'],6)}; diferença média detector−extrator={ic_texto(pareado['delta_macro'],pareado['ic95'])}. Vitórias por página: detector {pareado['ganha_detector']}, extrator {pareado['ganha_extrator']}, empates {pareado['empates']}. O IC da diferença é bootstrap pareado. Selecionar o melhor no teste pode favorecer o detector; páginas da mesma fonte são correlacionadas. Não tratar p como confirmação independente da escolha."]
    else:
        linhas += ["Teste pareado extrator × melhor detector: **não calculável**; nenhum detector concluído foi avaliado em todo o teste. O código realizará Wilcoxon e bootstrap pareado quando houver cobertura comum."]
    linhas += ["", "## Tempo por página", "", "CPU em todos os sistemas. Tempo de parede por página, sem carga/aquecimento do modelo e sem escrita de cache. Extrator inclui abertura/extração de palavras, renderização, Docling, segmentação e regras. YOLO inclui leitura da imagem, pré-processamento, inferência e pós-processamento. Verificação do índice com o ouro é preparação do experimento e fica fora. Sem excluir Docling, a comparação mede o custo real do extrator avaliado.", "",
               "| Sistema | Páginas cronometradas | Média ms | Mediana ms | p95 ms | Soma s |", "|---|---:|---:|---:|---:|---:|"]
    for n in nomes:
        t = r["latencias"][n]
        linhas.append(f"| {n} | {t.get('n',0)} | {numero(t.get('media_ms'),1)} | {numero(t.get('mediana_ms'),1)} | {numero(t.get('p95_ms'),1)} | {numero(t.get('total_s'),1)} |")
    ids = list(sistemas["extrator"])
    if ids:
        custos = []
        for pid in ids:
            p = next(p for p in paginas if p["page_id"] == pid)
            w, d, e = palavras[pid], ler(caminho_cache(p, "docling")), sistemas["extrator"][pid]
            custos.append([w["tempo_palavras_ms"], d["tempo_render_ms"], d["tempo_docling_ms"], e["tempo_regras_ms"]])
        medias = np.mean(custos, axis=0)
        linhas += [f"Componentes médios do extrator (ms): palavras {numero(medias[0],1)}; renderização {numero(medias[1],1)}; Docling {numero(medias[2],1)}; segmentação/regras {numero(medias[3],1)}."]
    linhas += ["Tempos preservados do primeiro cálculo válido de cada etapa, não do acesso ao cache. Há concorrência com treino e outras tarefas na máquina; não é um benchmark em máquina ociosa. Retomadas misturam momentos de carga distintos e não incluem os custos de inicialização.", "",
               "## Análise de erro e exemplos", "", "Os indícios de divisão/fusão são geométricos: uma caixa toca pelo menos duas da outra segmentação com interseção ≥50% da área menor. Podem incluir sobreposições legítimas e não são uma nova métrica de acerto.", "",
               "| Sistema | Ouro sem par IoU 0,50 | Predições sem par | Indícios de divisão | Indícios de fusão | Pares localizados com classe3 errada |", "|---|---:|---:|---:|---:|---:|"]
    for n in nomes:
        er = r["erros"][n]
        linhas.append(f"| {n} | {sum(er['perdidas_classe'].values())} | {sum(er['fp_classe'].values())} | {er['divisao']} | {er['fusao']} | {er['classe_errada3']} |")
        if er["perdidas_classe"]:
            top = sorted(er["perdidas_classe"].items(), key=lambda x: -x[1])[:5]
            linhas.append("\n" + n + " — classes mais perdidas: " + "; ".join(f"{c}: {k}" for c, k in top) + ".")
        if er["confusoes9"]:
            linhas.append(n + " — confusões em pares localizados (9 classes): " + "; ".join(f"{a}→{b}: {k}" for a, b, k in er["confusoes9"][:5]) + ".")
    candidatos = []
    for p in paginas:
        pid = p["page_id"]
        if pid in r["metricas_paginas"]["extrator"]:
            m = r["metricas_paginas"]["extrator"][pid]
            candidatos.append((float(f1(m["c3_50"])), p))
    candidatos.sort(key=lambda x: (x[0], x[1]["page_id"]))
    exemplos = []
    fontes = set()
    for _, p in candidatos:
        if p["fonte"] not in fontes:
            exemplos.append(p)
            fontes.add(p["fonte"])
        if len(exemplos) == 3:
            break
    linhas += ["", "Exemplos selecionados automaticamente entre os menores F1 do extrator, em fontes distintas; são casos adversos e não uma amostra representativa."]
    for p in exemplos:
        pid = p["page_id"]
        pred = sistemas["extrator"][pid]["caixas"]
        cont, pares = emparelhar(p["ouro"], pred, .5, 3)
        perdidos = [b for i, b in enumerate(p["ouro"]) if i not in {a for a, _, _ in pares} and mapa3(b["classe"]) is not None]
        exemplo = perdidos[0] if perdidos else p["ouro"][0] if p["ouro"] else None
        trecho = re.sub(r"\s+", " ", exemplo["texto"])[:140] if exemplo else ""
        detalhe = ""
        if exemplo:
            ious = matriz_iou([exemplo], pred).ravel()
            if len(ious):
                j = int(ious.argmax())
                detalhe = (f"Maior IoU desse ouro com uma predição: {numero(float(ious[j]))}, "
                           f"classe predita {pred[j]['classe']}; "
                           + ("geometria abaixo do limiar." if ious[j] < .5 else "a classe ou a disputa um a um impede o par com classe."))
            else:
                detalhe = "O extrator não produziu caixa nessa página."
        tabelas = [b for b in p["ouro"] if b["classe"] == "table"]
        figuras = [b for b in pred if b["classe"] == "figure"]
        ambiguas = int((matriz_iou(tabelas, figuras).max(axis=1) >= .5).sum()) if tabelas and figuras else 0
        if ambiguas:
            detalhe += (f" {ambiguas} tabela(s) do ouro têm IoU ≥ 0,50 com predição classificada como figura. "
                        "No pipeline, figura não recebe palavras; texto dessa área pode voltar como sobras de blocos e produzir fragmentação.")
        if not palavras[pid]["ws"]:
            detalhe += " Sem palavras, o pipeline só preserva regiões visuais de figura; as outras classes perdem suas caixas."
        pasta = CACHE / "exemplos"
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / (chave(p)+".jpg")
        with Image.open(RAIZ / "data/deteccao/ls16/images/test" / p["img"]) as im:
            im = im.convert("RGB")
            desenho = ImageDraw.Draw(im)
            for b in p["ouro"]:
                desenho.rectangle(b["bbox"], outline=(30, 170, 40), width=3)
            for b in pred:
                desenho.rectangle(b["bbox"], outline=(215, 45, 45), width=2)
            im.thumbnail((1000, 1500))
            im.save(destino, quality=85)
        linhas += [f"- **{p['fonte']}**, `{pid}`: F1 3 classes={numero(float(f1(cont)))}; TP/FP/FN={cont}; palavras={len(palavras[pid]['ws'])}. "
                   + (f"Caixa sem par com classe: `{exemplo['id']}`, {exemplo['classe']}, origem {exemplo['origem']}, trecho: “{trecho.replace('|','/')}”. " if exemplo else "")
                   + detalhe + f" [Sobreposição local](ls_teste_cache/exemplos/{destino.name}) (verde=ouro; vermelho=extrator)."]
    linhas += ["", "## Limitações e recomendação", "",
               "O ouro não é uma adjudicação independente: representa a anotação escolhida pela conversão original, mesmo onde há vários anotadores. A taxonomia semântica do guia é mais fina que a do extrator; o colapso em 3/9 classes elimina distinções importantes. Retângulos rotacionados usam o mesmo envelope axis-aligned já exportado ao YOLO. F1 depende da granularidade das caixas e do limiar IoU. Não há OCR adicional; PDFs com OCR embutido, texto ilegível ou parcial exigem análise separada. A novidade de fontes foi conferida no split dos modelos LS; não auditamos os dados de pré-treino do Docling. Fontes com poucas páginas, ancoragem, dependência intrafonte e seleção do melhor detector limitam as inferências.",
               (f"Recomendação medida: usar {vencedor} quando o objetivo é o maior F1 de layout em 3 classes nesse domínio. O outro sistema pode ser útil conforme custo/semântica; consultar os estratos e tempos antes de decidir. Para páginas sem camada de texto, priorizar um detector concluído com OCR posterior para obter texto; o presente teste de caixas não mede a qualidade desse OCR." if vencedor else
                "Recomendação provisória: o extrator já pode fornecer caixas e texto em PDFs com camada textual, com as perdas medidas acima. Para digitalizações, o desenho do detector é apropriado, mas sua vantagem ainda não foi medida nesta execução. Não substituir o extrator com base em checkpoint de treino inacabado. Reexecutar este script quando existir treino_ok; a decisão comparativa fica pendente até essa medição."),
               "Para investigar ancoragem, usar futuramente páginas anotadas do zero, sem pré-anotação visível, por mais de um anotador e com adjudicação. Isso é uma recomendação de estudo, não altera o split ou as anotações atuais.", "",
               "## Retomada e evidência", "", "```powershell",
               "venv/Scripts/python.exe orquestracao/analises/extrator_vs_detector_ls.py",
               "venv/Scripts/python.exe orquestracao/analises/extrator_vs_detector_ls.py --so-relatorio",
               "```", "",
               "Cache interno: `resultados/ls_teste_cache/` (ouro, palavras, Docling, propostas, predições YOLO, PDFs temporários, exemplos e `metricas.json`). Todas as etapas têm assinatura de entrada/modelo/código e escrita atômica. A execução não grava em data/, não usa GPU, não baixa modelos, não altera o quadro e não faz commit. Os derivados do parceiro permanecem neste repositório e não devem ser publicados."]
    if r["falhas_pdf"]:
        linhas += ["", "Falhas registradas:"] + [f"- `{pid}`: {er}" for pid, er in r["falhas_pdf"].items()]
    if r.get("falhas_extrator"):
        linhas += ["", "Falhas técnicas de preparo/inferência do extrator (não confundir com páginas sem texto):"] + [f"- `{pid}`: {er}" for pid, er in r["falhas_extrator"].items()]
    texto = "\n".join(linhas)+"\n"
    tmp = RELATORIO.with_suffix(".md.tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, RELATORIO)


def status_detectores():
    status = {}
    for n in ("ls3", "ls16"):
        ok = (RAIZ / f"runs/detect/{n}/treino_ok").is_file()
        peso = (RAIZ / f"runs/detect/{n}/weights/best.pt").is_file()
        status[n] = {"treino_ok": ok, "checkpoint": peso, "incluido": ok and peso,
                     "motivo": "concluído; incluído" if ok and peso else "fora: treino_ok ausente" if not ok else "fora: checkpoint ausente"}
    return status


def autoteste():
    b = lambda x, c="paragraph": {"bbox": x, "classe": c}
    g = [b([0,0,10,10]), b([0,0,5,10])]
    p = [b([0,0,10,10]), b([5,0,10,10])]
    # O par de IoU=1 nao pode roubar um segundo TP possivel no limiar .5.
    cont, _ = emparelhar(g, p)
    assert cont == [2,0,0], cont
    assert emparelhar(g, p, .75)[0] == [1,1,1]
    assert emparelhar([], [b([0,0,10,10])])[0] == [0,1,0]
    assert emparelhar([b([0,0,10,10])], [b([0,0,10,10], "table")], .5, 3)[0] == [0,1,1]
    assert emparelhar([b([0,0,10,10], "unknown")], [b([0,0,10,10], "unknown")], .5, 3)[0] == [0,0,0]
    assert GUIA_PARA_EXTRATOR[para_guia_do_extrator("lista")] == "texto"
    assert mapa3("heading") == "imagem" and mapa3("signature") == "texto"
    dados = '[{"id":1,"s":"' + "a"*140000 + '"},{"id":2}]'
    assert [x["id"] for x in tarefas_export(io.StringIO(dados))] == [1,2]
    assert float(f1([2,0,0])) == 1. and float(f1([0,0,0])) == 0.
    print("Autoteste OK: cardinalidade, IoU, classe, vazios, mapas e JSON incremental.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=2, help="processos CPU para extracao PDF")
    ap.add_argument("--threads", type=int, default=4, help="threads de inferencia CPU")
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--so-relatorio", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.autoteste:
        autoteste()
        return
    if a.workers < 1 or a.threads < 1 or a.bootstrap < 100:
        ap.error("workers/threads positivos; bootstrap >=100")
    os.chdir(RAIZ)
    CACHE.mkdir(parents=True, exist_ok=True)
    paginas, auditoria = carregar_ouro()
    salvar(CACHE / "auditoria_split.json", auditar_split())
    status = status_detectores()
    print(f"Ouro: {len(paginas)} paginas; {len({p['fonte'] for p in paginas})} fontes. Detectores: {status}", flush=True)
    avaliar(paginas, auditoria, a.bootstrap, status)
    if not a.so_relatorio:
        palavras, novas, ultimo_relatorio = {}, 0, 0
        try:
            executor = ProcessPoolExecutor(max_workers=a.workers)
        except PermissionError:
            # O sandbox Windows pode bloquear named pipes de multiprocessing.
            print("[CPU] Pipes de processos indisponiveis; usando threads para PDFs.", flush=True)
            executor = ThreadPoolExecutor(max_workers=a.workers)
        with executor as pool:
            futuros = [pool.submit(extrair_palavras, p) for p in paginas]
            for k, futuro in enumerate(as_completed(futuros), 1):
                pid, c, cache = futuro.result()
                palavras[pid] = c
                novas += not cache
                if c.get("erro"):
                    print(f"[PDF ERRO] {pid}: {c['erro']}", flush=True)
                if k % 10 == 0 or k == len(paginas):
                    print(f"[palavras] {k}/{len(paginas)}; novas {novas}", flush=True)
                    if novas > ultimo_relatorio:
                        avaliar(paginas, auditoria, a.bootstrap, status)
                        ultimo_relatorio = novas
        import torch
        from src.data import layout
        torch.set_num_threads(a.threads)
        torch.set_num_interop_threads(1)
        detector = None
        erros, novas_regioes, ultimo_relatorio = {}, 0, 0
        for k, p in enumerate(paginas, 1):
            w = palavras[p["page_id"]]
            if w.get("erro"):
                continue
            try:
                dc = ler(caminho_cache(p, "docling"))
                entrada = assinatura_docling(w)
                if (not dc or dc.get("assinatura") != entrada or dc.get("erro")) and detector is None:
                    t = time.perf_counter()
                    detector = layout.Detector(dispositivo="cpu", permitir_download=False)
                    detector([Image.new("RGB", (595,842), "white")], [((0,0,595,842),1.)])
                    print(f"[Docling] CPU; carga/aquecimento {time.perf_counter()-t:.2f}s", flush=True)
                d, cache_docling = preparar_docling(p, w, detector)
                _, cache_proposta = propor_pagina(p, w, d)
                novas_regioes += not (cache_docling and cache_proposta)
            except (Exception, SystemExit) as e:
                erros[p["page_id"]] = f"{type(e).__name__}: {e}"
                print(f"[extrator ERRO] {p['page_id']}: {e}", flush=True)
            if k % 10 == 0 or k == len(paginas):
                print(f"[extrator] {k}/{len(paginas)}; novas {novas_regioes}; erros {len(erros)}", flush=True)
                if novas_regioes > ultimo_relatorio:
                    avaliar(paginas, auditoria, a.bootstrap, status)
                    ultimo_relatorio = novas_regioes
        del detector
        salvar(CACHE / "falhas_extrator.json", erros)
        # Nao aguarda treino: so incorpora os ja concluidos ao chegar nesta etapa.
        status = status_detectores()
        for nome, s in status.items():
            if s["incluido"]:
                prever_yolo(nome, paginas, a.threads)
                avaliar(paginas, auditoria, a.bootstrap, status)
    resultado = avaliar(paginas, auditoria, a.bootstrap, status)
    print("\nTABELA FINAL (F1 micro; tempos medidos, sem acesso ao cache):", flush=True)
    for nome, res in resultado["resumo"].items():
        print(nome, "paginas", resultado["cobertura"][nome],
              {k: round(v["f1"],6) for k, v in res.items()}, resultado["latencias"][nome], flush=True)
    print(f"Relatorio: {RELATORIO}\nEvidencia: {CACHE / 'metricas.json'}", flush=True)
    if resultado["cobertura"]["extrator"] != len(paginas):
        raise SystemExit("Execucao incompleta: consultar falhas e retomar")


if __name__ == "__main__":
    main()
