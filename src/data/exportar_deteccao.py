"""
Exporta as anotacoes do Diamond (caixas + classes) para o formato YOLO de deteccao,
pronto para fine-tunar um detector de layout (ex.: DocLayout-YOLO / ultralytics) nas
9 classes de diario oficial.

Por que existir
---------------
O extrator de hoje USA o detector Docling Heron e conserta a saida com as palavras do
PDF e regras. Isso e forte na localizacao (F1@0,5 ~0,92-0,95) mas fraco na classe
(~0,80) e cego onde o texto e so imagem (nao ha palavra no PDF). Um detector treinado
nas classes do Diamond trabalha a partir da IMAGEM: ataca a classe, enxerga texto-imagem
e deixa de depender da camada de texto do PDF.

O que faz
---------
  - Le os lotes do Diamond (ouro = anotacao humana) e, opcionalmente, do Rose (prata =
    pseudo-rotulo de VLM). Usa so as anotacoes com status "concluida".
  - Casa cada anotacao (page_id -> regioes) com a tarefa (page_id -> imagem, dimensions).
  - Escreve rotulos YOLO: "classe cx cy w h", normalizados por dimensions (pontos do PDF;
    coordenada normalizada independe da resolucao da imagem renderizada).
  - Separa uma fracao das paginas OURO para validacao; treino = resto do ouro + toda a
    prata. Paginas de prata cujo page_id ja esta no ouro sao descartadas (evita
    vazamento, porque rose_treino cobre as mesmas paginas do diamond_treino).
  - Lotes passados em --teste viram um split separado, nunca usado no treino (reserve
    aqui as paginas desenhadas do zero, sem a pre-marcacao, para a medicao honesta).

Uso
---
    venv\\Scripts\\python.exe src\\data\\exportar_deteccao.py
    venv\\Scripts\\python.exe src\\data\\exportar_deteccao.py --ouro diamond_piloto diamond_treino \\
        --prata rose_treino --frac-val 0.2 --saida data/deteccao/diamond_yolo
    venv\\Scripts\\python.exe src\\data\\exportar_deteccao.py --teste diamond_teste_zero
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import random
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.regioes import CLASSES  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond")
IDX = {c: i for i, c in enumerate(CLASSES)}


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def paginas_do_lote(lote):
    """Devolve [(page_id, imagem_abs, w, h, regioes)] das anotacoes concluidas do lote."""
    dir_lote = os.path.join(DIR_DIAMOND, lote)
    tarefas = {t["page_id"]: t for t in ler_jsonl(os.path.join(dir_lote, "tarefas.jsonl"))}
    # uma pagina pode ter varias linhas concluidas (re-anotacao): fica a ULTIMA (mais recente),
    # senao a mesma pagina seria copiada varias vezes e poderia vazar entre treino e validacao.
    ultima = {}
    for a in ler_jsonl(os.path.join(dir_lote, "anotacoes.jsonl")):
        if a.get("status") == "concluida":
            ultima[a["page_id"]] = a
    saida = []
    for page_id, a in ultima.items():
        t = tarefas.get(page_id)
        if not t:
            continue
        img = os.path.join(dir_lote, "img", t["imagem"])
        if not os.path.exists(img):
            continue
        dim = t["dimensions"]
        saida.append((page_id, img, float(dim["width"]), float(dim["height"]), a["regioes"]))
    return saida


def rotulos_yolo(regioes, w, h):
    """Converte regioes ([{classe, bbox:[x0,y0,x1,y1]}]) em linhas YOLO normalizadas."""
    linhas = []
    for r in regioes:
        if r["classe"] not in IDX:
            continue
        x0, y0, x1, y1 = r["bbox"]
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        cx, cy = (x0 + x1) / 2 / w, (y0 + y1) / 2 / h
        bw, bh = (x1 - x0) / w, (y1 - y0) / h
        if bw <= 0 or bh <= 0:
            continue
        clamp = lambda v: max(0.0, min(1.0, v))
        linhas.append(f"{IDX[r['classe']]} {clamp(cx):.6f} {clamp(cy):.6f} {clamp(bw):.6f} {clamp(bh):.6f}")
    return linhas


def escrever_split(itens, dir_saida, split):
    dir_img = os.path.join(dir_saida, "images", split)
    dir_lbl = os.path.join(dir_saida, "labels", split)
    os.makedirs(dir_img, exist_ok=True)
    os.makedirs(dir_lbl, exist_ok=True)
    n_regioes = 0
    for lote, page_id, img, w, h, regioes in itens:
        base = f"{lote}__{os.path.basename(img)}"
        shutil.copy(img, os.path.join(dir_img, base))
        linhas = rotulos_yolo(regioes, w, h)
        n_regioes += len(linhas)
        raiz_txt = os.path.splitext(base)[0] + ".txt"
        with open(os.path.join(dir_lbl, raiz_txt), "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
    return n_regioes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ouro", nargs="+", default=["diamond_piloto", "diamond_treino"],
                    help="lotes com anotacao humana")
    ap.add_argument("--prata", nargs="*", default=["rose_treino"],
                    help="lotes de pseudo-rotulo (VLM); paginas ja presentes no ouro sao descartadas")
    ap.add_argument("--teste", nargs="*", default=[],
                    help="lotes reservados so para teste (nunca entram no treino)")
    ap.add_argument("--frac-val", type=float, default=0.2, help="fracao do OURO para validacao")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--saida", default=os.path.join("data", "deteccao", "diamond_yolo"))
    a = ap.parse_args()

    dir_saida = os.path.join(RAIZ, a.saida) if not os.path.isabs(a.saida) else a.saida
    if os.path.exists(dir_saida):
        shutil.rmtree(dir_saida)

    # ouro: coleta e separa val por pagina (semeado)
    ouro = [(lote, *p) for lote in a.ouro for p in paginas_do_lote(lote)]
    ids_ouro = {p[1] for p in ouro}  # page_id
    rng = random.Random(a.seed)
    rng.shuffle(ouro)
    n_val = round(len(ouro) * a.frac_val)
    val, treino = ouro[:n_val], ouro[n_val:]

    # prata: entra so no treino, sem paginas que ja sao ouro
    prata = [(lote, *p) for lote in a.prata for p in paginas_do_lote(lote) if p[0] not in ids_ouro]
    treino = treino + prata

    # teste: lotes exclusivos
    teste = [(lote, *p) for lote in a.teste for p in paginas_do_lote(lote)]

    n_r_treino = escrever_split(treino, dir_saida, "train")
    n_r_val = escrever_split(val, dir_saida, "val")
    n_r_teste = escrever_split(teste, dir_saida, "test") if teste else 0

    data_yaml = os.path.join(dir_saida, "data.yaml")
    with open(data_yaml, "w", encoding="utf-8") as f:
        f.write(f"path: {dir_saida}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        if teste:
            f.write("test: images/test\n")
        f.write(f"nc: {len(CLASSES)}\n")
        f.write("names:\n")
        for i, c in enumerate(CLASSES):
            f.write(f"  {i}: {c}\n")

    manifesto = {
        "classes": CLASSES,
        "ouro": a.ouro, "prata": a.prata, "teste": a.teste,
        "paginas": {"treino": len(treino), "val": len(val), "teste": len(teste),
                    "ouro_no_treino": len(treino) - len(prata), "prata": len(prata)},
        "regioes": {"treino": n_r_treino, "val": n_r_val, "teste": n_r_teste},
        "frac_val": a.frac_val, "seed": a.seed,
    }
    with open(os.path.join(dir_saida, "manifesto.json"), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)

    print(f"[OK] dataset YOLO em {os.path.relpath(dir_saida, RAIZ)}")
    print(f"     treino: {len(treino)} pag ({len(treino) - len(prata)} ouro + {len(prata)} prata), "
          f"{n_r_treino} regioes")
    print(f"     val:    {len(val)} pag (ouro), {n_r_val} regioes")
    if teste:
        print(f"     teste:  {len(teste)} pag, {n_r_teste} regioes")
    print(f"     data.yaml: {os.path.relpath(data_yaml, RAIZ)}")


if __name__ == "__main__":
    main()
