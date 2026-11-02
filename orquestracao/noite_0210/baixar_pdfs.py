# -*- coding: utf-8 -*-
"""Baixa do S3 (publico) so os PDFs das 317 paginas de TESTE do split de deteccao e das paginas de
ordem ja anotadas por humanos no projeto 23. Grava em data/labelstudio/pdf/ e, no fim, o indice
data/labelstudio/pdf_paginas.jsonl (pagina -> PDF local). Retomavel. Teto de seguranca: 6 GB."""
import glob, json, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "data/labelstudio"
DEST = f"{BASE}/pdf"
TETO = 6e9
split = json.load(open("data/deteccao/ls_split.json", encoding="utf-8"))["paginas"]
img_teste = {v["img"]: pid for pid, v in split.items() if v["split"] == "test"}

paginas = []          # {page_key, img, pdf_url, pagina, uso}
for s in (1, 2, 3, 4):
    nome = {im["page_id"]: im["file_name"] for im in json.load(open(f"{BASE}/conv_seed{s}/coco.json", encoding="utf-8"))["images"]}
    url_img = {json.loads(l)["page_id"]: json.loads(l)["imagem"] for l in open(f"{BASE}/conv_seed{s}/tarefas.jsonl", encoding="utf-8")}
    exp = glob.glob(f"{BASE}/ls_p*_seed{s}.json")[0]
    por_ocr = {t["data"]["ocr"]: t["data"] for t in json.load(open(exp, encoding="utf-8"))}
    for pid, img in nome.items():
        if img in img_teste:
            d = por_ocr[url_img[pid]]
            paginas.append({"page_id": pid, "img": img, "pdf_url": d.get("pdf") or d.get("source_file"),
                            "pagina": d.get("page"), "uso": "teste_deteccao"})
for t in json.load(open(f"{BASE}/ls_p23_seed2_order.json", encoding="utf-8")):
    if any(a.get("completed_by") is not None and not a.get("was_cancelled") for a in t.get("annotations", [])):
        d = t["data"]
        paginas.append({"task_id": t["id"], "pdf_url": d.get("pdf") or d.get("source_file"),
                        "pagina": d.get("page"), "ocr": d.get("ocr"), "uso": "ordem"})

def local_de(url):
    caminho = urllib.parse.unquote(urllib.parse.urlparse(url).path).lstrip("/")
    return os.path.join(DEST, *caminho.split("/")[-2:])

urls = sorted({p["pdf_url"] for p in paginas if p["pdf_url"]})
print(f"{len(paginas)} paginas, {len(urls)} PDFs distintos", flush=True)
total = [0]

def baixar(url):
    dst = local_de(url)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        total[0] += os.path.getsize(dst); return "ja"
    if total[0] > TETO:
        return "TETO"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    u = urllib.parse.quote(url, safe=":/%+()=,&@!'~*$")   # o "+" tem que ir literal: %2B da 403 no S3
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(u, timeout=180) as r, open(dst + ".part", "wb") as f:
                while True:
                    bloco = r.read(1 << 20)
                    if not bloco: break
                    f.write(bloco)
            os.replace(dst + ".part", dst); total[0] += os.path.getsize(dst); return "ok"
        except Exception as e:  # noqa: BLE001
            erro = f"{type(e).__name__}: {e}"; time.sleep(3 * (tentativa + 1))
    return "ERRO " + url + " " + erro

cont = {}
with ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(baixar, urls), 1):
        k = r.split()[0]; cont[k] = cont.get(k, 0) + 1
        if r.startswith("ERRO"): print(r, flush=True)
        if i % 25 == 0: print(f"{i}/{len(urls)} {cont} {total[0]/1e9:.2f} GB", flush=True)
print(f"download: {cont} | {total[0]/1e9:.2f} GB", flush=True)

with open(f"{BASE}/pdf_paginas.jsonl.part", "w", encoding="utf-8") as f:
    for p in paginas:
        loc = local_de(p["pdf_url"]) if p["pdf_url"] else None
        p["pdf_local"] = loc.replace("\\", "/") if loc and os.path.exists(loc) else None
        f.write(json.dumps(p, ensure_ascii=False) + "\n")
os.replace(f"{BASE}/pdf_paginas.jsonl.part", f"{BASE}/pdf_paginas.jsonl")
print("FIM", sum(1 for p in paginas if p["pdf_local"]), "paginas com PDF local", flush=True)
