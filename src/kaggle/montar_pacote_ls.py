# -*- coding: utf-8 -*-
"""
Monta o pacote do Kaggle para treinar detectores de layout no dataset do Label Studio:
  dist/kaggle/ls_deteccao.zip        imagens (uma vez) + rotulos ls16 e ls3 + split por fonte
                                     + as 11 imagens do diamond_teste (para a comparacao local)
  notebooks/kaggle_detector_ls.ipynb notebook que treina varios modelos nas 2 GPUs T4 em paralelo

ATENCAO: o dataset e do projeto Data Policy. No Kaggle, suba como dataset PRIVADO.

Uso:
    venv\\Scripts\\python.exe src\\kaggle\\montar_pacote_ls.py            # zip + notebook
    venv\\Scripts\\python.exe src\\kaggle\\montar_pacote_ls.py --so-notebook
"""
import argparse
import glob
import json
import os
import sys
import zipfile
from pathlib import Path

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from taxonomia_layout import GUIA  # noqa: E402

DET = Path("data/deteccao")
ZIP = Path("dist/kaggle/ls_deteccao.zip")
NB = Path("notebooks/kaggle_detector_ls.ipynb")
CLASSES3 = ["texto", "tabela", "imagem"]


def montar_zip():
    paginas = json.loads((DET / "ls_split.json").read_text(encoding="utf-8"))["paginas"]
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    split, n = {}, 0
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_STORED) as z:
        for info in paginas.values():
            img, sp = info["img"], info["split"]
            origem = DET / "ls16" / "images" / sp / img
            if not origem.exists():
                continue
            stem = Path(img).stem
            z.write(origem, f"images/{img}")
            z.write(DET / "ls16" / "labels" / sp / f"{stem}.txt", f"labels_ls16/{stem}.txt")
            z.write(DET / "ls3" / "labels" / sp / f"{stem}.txt", f"labels_ls3/{stem}.txt")
            split[img] = sp
            n += 1
        z.writestr("split.json", json.dumps(split))
        z.writestr("classes.json", json.dumps({"ls16": list(GUIA), "ls3": CLASSES3}))
        for f in sorted(glob.glob("data/diamond/diamond_teste/img/*.jpg")):
            z.write(f, f"diamond_teste/img/{os.path.basename(f)}")
    print(f"[OK] {ZIP}: {n} paginas, {ZIP.stat().st_size / 1e9:.2f} GB")


TREINA = r'''
import sys, json, os, glob, shutil, traceback
ds, arq, imgsz, batch, horas, nome, dev = sys.argv[1:8]
os.environ["CUDA_VISIBLE_DEVICES"] = dev            # cada fila enxerga so a sua GPU
# o fork doclayout_yolo liga o wandb sozinho e usa o caminho de "project" como nome do projeto: no Kaggle
# de 03/10 os dois treinos do DocLayout cairam com "Invalid project name '/kaggle/working/runs'"
os.environ["WANDB_MODE"] = "disabled"
os.environ["WANDB_DISABLED"] = "true"
# 08/10: so as variaveis nao bastam (a validacao do nome do projeto roda antes do "disabled"): desliga o callback
# do wandb pelas SETTINGS do fork e usa um "project" relativo, sem barra
try:
    from doclayout_yolo.utils import SETTINGS
    SETTINGS.update({"wandb": False})
except Exception as e:
    print("aviso: nao consegui desligar o wandb pelas SETTINGS:", e)
os.chdir("/kaggle/working")
imgsz, batch, horas = int(imgsz), int(batch), float(horas)
RAIZ = "/kaggle/working"
data = f"{RAIZ}/ds/{ds}/data.yaml"
saida = f"{RAIZ}/saida/{nome}"
os.makedirs(saida, exist_ok=True)
try:
    kw = dict(data=data, epochs=100, patience=20, imgsz=imgsz, batch=batch, device=0, seed=42,
              project="runs", name=nome, exist_ok=True, fliplr=0.0, workers=2)
    if arq == "doclayout":                           # pesos pre-treinados em documentos (DocStructBench)
        from doclayout_yolo import YOLOv10 as Modelo
        from huggingface_hub import hf_hub_download
        pesos = hf_hub_download("juliozhao/DocLayout-YOLO-DocStructBench",
                                "doclayout_yolo_docstructbench_imgsz1024.pt")
        kw["epochs"] = int(horas)                    # o fork nao tem limite por tempo: aqui "horas" = epocas
    elif arq.startswith("rtdetr"):
        from ultralytics import RTDETR as Modelo
        pesos, kw["time"] = arq, horas
    else:
        from ultralytics import YOLO as Modelo
        pesos, kw["time"] = arq, horas
    Modelo(pesos).train(**kw)

    best = f"{RAIZ}/runs/{nome}/weights/best.pt"
    m = Modelo(best)
    r = m.val(data=data, split="test", imgsz=imgsz, batch=batch, device=0, verbose=False,
              project="runs", name=nome + "_teste", exist_ok=True)
    met = {"modelo": arq, "dataset": ds, "imgsz": imgsz, "mAP50": float(r.box.map50), "mAP50_95": float(r.box.map),
           "precisao": float(r.box.mp), "revocacao": float(r.box.mr),
           "por_classe": {m.names[int(c)]: {"AP50": float(r.box.ap50[i]), "AP50_95": float(r.box.ap[i])}
                          for i, c in enumerate(r.box.ap_class_index)}}
    json.dump(met, open(f"{saida}/metricas_teste.json", "w"), ensure_ascii=False, indent=1)

    entrada = os.path.dirname(glob.glob("/kaggle/input/**/split.json", recursive=True)[0])
    with open(f"{saida}/pred_diamond_teste.jsonl", "w") as out:
        for img in sorted(glob.glob(f"{entrada}/diamond_teste/img/*.jpg")):
            res = m.predict(img, imgsz=imgsz, conf=0.25, device=0, verbose=False)[0]
            h, w = res.orig_shape
            regs = [{"classe": res.names[int(b.cls[0])], "bbox_px": [round(float(v), 1) for v in b.xyxy[0].tolist()],
                     "score": round(float(b.conf[0]), 4)} for b in res.boxes]
            out.write(json.dumps({"imagem": os.path.basename(img), "w": w, "h": h, "regioes": regs},
                                 ensure_ascii=False) + "\n")
    shutil.copy(best, f"{saida}/best.pt")
    shutil.copy(f"{RAIZ}/runs/{nome}/results.csv", f"{saida}/results.csv")
    print("FIM_OK", nome, met["mAP50"], met["mAP50_95"])
except Exception:
    open(f"{saida}/erro.txt", "w").write(traceback.format_exc())
    traceback.print_exc()
    print("FIM_ERRO", nome)
'''

CELULAS = [
    ("md", "# Detectores de layout no dataset do Label Studio (2 × T4)\n\n"
           "Treina vários modelos nas **mesmas páginas e no mesmo split por fonte** do treino local, uma fila por GPU.\n\n"
           "**Antes de rodar:** Settings → Accelerator **GPU T4 x2**, **Internet ON**, e o dataset `ls_deteccao` "
           "(PRIVADO) adicionado em *Add input*. Depois: **Save Version → Save & Run All (Commit)** e pode fechar a aba.\n\n"
           "No fim, baixe `saida_ls.zip` na aba *Output*."),
    ("code", "!pip -q install -U ultralytics huggingface_hub 2>&1 | tail -1\n"
             "!pip -q install doclayout-yolo 2>&1 | tail -1   # se falhar, as filas pulam esse modelo\n"
             "import torch, glob, json, os\n"
             "print('torch', torch.__version__, '| GPUs:', torch.cuda.device_count())\n"
             "assert torch.cuda.device_count() >= 1, 'Ligue a GPU em Settings -> Accelerator'"),
    ("code", "# --- monta os dois datasets (ls16 e ls3) em /kaggle/working/ds, com links para as imagens ---\n"
             "achados = glob.glob('/kaggle/input/**/split.json', recursive=True)\n"
             "assert achados, 'Dataset ls_deteccao nao encontrado em /kaggle/input (Add input)'\n"
             "ENT = os.path.dirname(achados[0])\n"
             "split = json.load(open(f'{ENT}/split.json'))\n"
             "classes = json.load(open(f'{ENT}/classes.json'))\n"
             "import shutil\n"
             "for ds in ('ls16', 'ls3'):\n"
             "    raiz = f'/kaggle/working/ds/{ds}'\n"
             "    for img, sp in split.items():\n"
             "        os.makedirs(f'{raiz}/images/{sp}', exist_ok=True); os.makedirs(f'{raiz}/labels/{sp}', exist_ok=True)\n"
             "        dst = f'{raiz}/images/{sp}/{img}'\n"
             "        if not os.path.lexists(dst): os.symlink(f'{ENT}/images/{img}', dst)\n"
             "        stem = os.path.splitext(img)[0]\n"
             "        shutil.copy(f'{ENT}/labels_{ds}/{stem}.txt', f'{raiz}/labels/{sp}/{stem}.txt')\n"
             "    nomes = '\\n'.join(f'  {i}: {c}' for i, c in enumerate(classes[ds]))\n"
             "    open(f'{raiz}/data.yaml', 'w').write(f'path: {raiz}\\ntrain: images/train\\nval: images/val\\ntest: images/test\\nnames:\\n{nomes}\\n')\n"
             "from collections import Counter\n"
             "print('paginas por split:', dict(Counter(split.values())))"),
    ("code", "%%writefile /kaggle/working/treina.py" + TREINA),
    ("code", "# --- duas filas, uma por GPU. Colunas: dataset, modelo, imgsz, batch, horas (ou epocas p/ doclayout), nome ---\n"
             "FILAS = {\n"
             "  '0': [('ls16', 'yolo11m.pt', 1280, 6, 4.5, 'ls16_yolo11m_1280'),\n"
             "        ('ls16', 'rtdetr-l.pt', 1024, 4, 4.0, 'ls16_rtdetr_l_1024')],\n"
             "  '1': [('ls16', 'doclayout', 1024, 8, 45, 'ls16_doclayout_1024'),\n"
             "        ('ls3', 'yolo11m.pt', 1280, 6, 3.5, 'ls3_yolo11m_1280'),\n"
             "        ('ls3', 'doclayout', 1024, 8, 45, 'ls3_doclayout_1024')],\n"
             "}\n"
             "import subprocess, time\n"
             "if torch.cuda.device_count() < 2:      # so 1 GPU: tudo numa fila\n"
             "    FILAS = {'0': FILAS['0'] + FILAS['1']}\n"
             "os.makedirs('/kaggle/working/logs', exist_ok=True)\n"
             "procs = []\n"
             "for gpu, jobs in FILAS.items():\n"
             "    cmd = ' ; '.join(f'python /kaggle/working/treina.py {d} {m} {i} {b} {h} {n} {gpu} > /kaggle/working/logs/{n}.log 2>&1'\n"
             "                     for d, m, i, b, h, n in jobs)\n"
             "    procs.append(subprocess.Popen(cmd, shell=True))\n"
             "t0 = time.time()\n"
             "while any(p.poll() is None for p in procs):\n"
             "    time.sleep(600)\n"
             "    feitos = [os.path.basename(os.path.dirname(f)) for f in glob.glob('/kaggle/working/saida/*/metricas_teste.json')]\n"
             "    print(f'{(time.time()-t0)/3600:.1f} h | concluidos: {feitos}', flush=True)\n"
             "print('filas terminadas')"),
    ("code", "# --- resumo e pacote de saida ---\n"
             "import pandas as pd\n"
             "linhas = []\n"
             "for f in sorted(glob.glob('/kaggle/working/saida/*/metricas_teste.json')):\n"
             "    m = json.load(open(f)); linhas.append({'nome': os.path.basename(os.path.dirname(f)), 'dataset': m['dataset'],\n"
             "        'modelo': m['modelo'], 'imgsz': m['imgsz'], 'mAP50': round(m['mAP50'], 3), 'mAP50-95': round(m['mAP50_95'], 3)})\n"
             "display(pd.DataFrame(linhas))\n"
             "for f in glob.glob('/kaggle/working/saida/*/erro.txt'): print('ERRO em', f, '\\n', open(f).read()[-600:])\n"
             "shutil.copytree('/kaggle/working/logs', '/kaggle/working/saida/logs', dirs_exist_ok=True)\n"
             "shutil.make_archive('/kaggle/working/saida_ls', 'zip', '/kaggle/working/saida')\n"
             "print('Baixe /kaggle/working/saida_ls.zip na aba Output')"),
]


def montar_notebook():
    nb = nbf.v4.new_notebook()
    nb["cells"] = [nbf.v4.new_markdown_cell(t) if k == "md" else nbf.v4.new_code_cell(t) for k, t in CELULAS]
    nb["metadata"] = {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}}
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(NB))
    print(f"[OK] {NB}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-notebook", action="store_true")
    a = ap.parse_args()
    montar_notebook()
    if not a.so_notebook:
        montar_zip()
