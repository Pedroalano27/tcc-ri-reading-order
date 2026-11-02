# -*- coding: utf-8 -*-
"""
Monta os datasets YOLO de deteccao de layout a partir dos exports do Label Studio do projeto
Data Policy (seeds 1-4, ja convertidos por src/anotacao/ordem_labelstudio.py converter).

Gera duas versoes com as MESMAS paginas e o MESMO split:
  ls16  as 16 classes do guia de anotacao (src/data/taxonomia_layout.py)
  ls3   plano "sem bbox fina": texto / tabela / imagem
        (table -> tabela; figure, chart, heading[rubrica manuscrita] -> imagem;
         unknown fica de fora; todo o resto -> texto)

Split POR FONTE (municipio/estado tirado do nome do PDF): uma fonte inteira vai para treino, val
ou teste, nunca dividida -- o teste mede generalizacao para veiculo nao visto, como no protocolo
do TCC. As imagens entram por hardlink (sem duplicar ~1 GB).

Uso:
    venv\\Scripts\\python.exe src\\data\\montar_deteccao_ls.py            # monta ls16 e ls3
    venv\\Scripts\\python.exe src\\data\\montar_deteccao_ls.py --so-fontes # so lista as fontes
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomia_layout import GUIA  # noqa: E402

BASE = Path("data/labelstudio")
SAIDA = Path("data/deteccao")
CLASSES3 = ("texto", "tabela", "imagem")
PARA3 = {"table": "tabela", "figure": "imagem", "chart": "imagem", "heading": "imagem", "unknown": None}

# prefixo "ESTADO_MES_ANO" que alguns lotes poem antes da fonte ("SERGIPE_ABRIL_2026+-+se_simao_dias")
RE_PREFIXO_LOTE = re.compile(r"[a-z][a-z ]* (?:janeiro|fevereiro|marco|abril|maio|junho|julho) 2026(?: teste)? ")
# tokens de edicao/paginacao: ed1345, ednone, edx, pag146, normalpag142, p0125
RE_TOKEN_EDICAO = re.compile(r"^(?:ed(?:\d\w*|none|x)?|(?:normal|extra)?pag\d+|p\d+)$")
# palavras do tipo de edicao, que nao distinguem o veiculo ("normal df" e "df" sao a mesma fonte)
PALAVRAS_DE_EDICAO = {"normal", "extra", "extraordinario", "extraordinaria", "suplemento", "suplementar",
                      "caderno", "executivo", "estado", "teste", "edicao", "atos", "pessoal",
                      "de", "do", "da", "pdf"}


UFS = set("ac al ap am ba ce df es go ma mt ms mg pa pb pr pe pi rj rn rs ro rr sc sp se to".split())


def fonte_de(arquivo: str) -> str:
    """Nome do PDF -> chave da fonte (municipio/estado), sem data, edicao e paginacao.

    Primeiro troca TODO separador por espaco (o "_" impede \\b e fazia "df", "df a" e "df p1"
    virarem fontes diferentes, vazando o mesmo veiculo entre treino e teste)."""
    nome = arquivo.replace("\\", "/").split("/")[-1]
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    nome = " " + re.sub(r"[^a-z0-9]+", " ", nome).strip() + " "
    nome = RE_PREFIXO_LOTE.sub(" ", nome, count=1)
    tokens = [t for t in nome.split()
              if not t.isdigit() and len(t) > 1 and t not in PALAVRAS_DE_EDICAO
              and not RE_TOKEN_EDICAO.match(t)]
    if len(tokens) > 1 and tokens[0] in UFS:     # "go goiania" e "goiania" sao o mesmo veiculo
        tokens = tokens[1:]
    return " ".join(tokens) or "desconhecida"


def carregar():
    paginas, vistas, descartadas = [], set(), 0
    for s in (1, 2, 3, 4):
        d = BASE / f"conv_seed{s}"
        nome = {im["page_id"]: im["file_name"]
                for im in json.loads((d / "coco.json").read_text(encoding="utf-8"))["images"]}
        for linha in (d / "tarefas.jsonl").read_text(encoding="utf-8").splitlines():
            t = json.loads(linha)
            W, H = t["dimensions"].get("width"), t["dimensions"].get("height")
            img = nome[t["page_id"]]
            if not W or not H or W <= 0 or H <= 0 or img in vistas:   # sem dimensao ou imagem repetida
                descartadas += 1
                continue
            vistas.add(img)
            t["seed"], t["img"], t["fonte"] = s, img, fonte_de(t["arquivo"])
            paginas.append(t)
    if descartadas:
        print(f"[aviso] {descartadas} pagina(s) fora: sem dimensao valida ou imagem repetida")
    return paginas


def dividir(paginas, frac_teste, frac_val, semente):
    """Fontes embaralhadas com semente fixa; enche teste, depois val, o resto e treino."""
    por_fonte = collections.defaultdict(list)
    for p in paginas:
        por_fonte[p["fonte"]].append(p)
    fontes = sorted(por_fonte)
    random.Random(semente).shuffle(fontes)
    alvo_t, alvo_v = frac_teste * len(paginas), frac_val * len(paginas)
    split, n_t, n_v = {}, 0, 0
    for f in fontes:
        n = len(por_fonte[f])
        if n > 0.04 * len(paginas):           # fonte muito grande fica no treino
            split[f] = "train"
        elif n_t + n <= alvo_t:
            split[f], n_t = "test", n_t + n
        elif n_v + n <= alvo_v:
            split[f], n_v = "val", n_v + n
        else:
            split[f] = "train"
    faltando = {"train", "val", "test"} - set(split.values())
    if faltando:
        sys.exit(f"[ERRO] split(s) vazio(s): {sorted(faltando)}. Poucas fontes para as fracoes pedidas.")
    return split


def linha_yolo(b, W, H, cid):
    x0, y0, x1, y1 = b["bbox"]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    return f"{cid} {(x0 + x1) / 2 / W:.6f} {(y0 + y1) / 2 / H:.6f} {(x1 - x0) / W:.6f} {(y1 - y0) / H:.6f}"


def montar(nome, classes, mapa, paginas, split):
    raiz = SAIDA / nome
    if raiz.exists():
        shutil.rmtree(raiz)
    cont = collections.Counter()
    faltam = 0
    for p in paginas:
        origem = BASE / "img" / p["img"]
        if not origem.exists():
            faltam += 1
            continue
        sp = split[p["fonte"]]
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        linhas = []
        for b in p["bounding_boxes"]:
            c = mapa(b["classe"])
            if c is None:
                continue
            l = linha_yolo(b, W, H, classes.index(c))
            if l:
                linhas.append(l)
                cont[(sp, c)] += 1
        (raiz / "images" / sp).mkdir(parents=True, exist_ok=True)
        (raiz / "labels" / sp).mkdir(parents=True, exist_ok=True)
        destino = raiz / "images" / sp / p["img"]
        if not destino.exists():
            try:
                os.link(origem, destino)
            except OSError:
                shutil.copy2(origem, destino)
        (raiz / "labels" / sp / (Path(p["img"]).stem + ".txt")).write_text("\n".join(linhas) + "\n", encoding="utf-8")
        cont[(sp, "_paginas")] += 1
    nomes = "\n".join(f"  {i}: {c}" for i, c in enumerate(classes))
    (raiz / "data.yaml").write_text(
        f"path: {raiz.resolve().as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\n"
        f"names:\n{nomes}\n", encoding="utf-8")
    return cont, faltam


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--teste", type=float, default=0.15)
    ap.add_argument("--val", type=float, default=0.10)
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--so-fontes", action="store_true")
    a = ap.parse_args()

    paginas = carregar()
    split = dividir(paginas, a.teste, a.val, a.semente)
    por_fonte = collections.Counter(p["fonte"] for p in paginas)
    if a.so_fontes:
        for f, n in por_fonte.most_common():
            print(f"{n:5d}  {split[f]:5s}  {f}")
        print(f"{len(por_fonte)} fontes, {len(paginas)} paginas")
        return

    SAIDA.mkdir(parents=True, exist_ok=True)
    resumo = {}
    for nome, classes, mapa in (
            ("ls16", GUIA, lambda c: c if c in GUIA else None),
            ("ls3", CLASSES3, lambda c: PARA3.get(c, "texto") if c in GUIA else None)):
        cont, faltam = montar(nome, classes, mapa, paginas, split)
        resumo[nome] = {sp: {"paginas": cont[(sp, "_paginas")],
                             **{c: cont[(sp, c)] for c in classes}} for sp in ("train", "val", "test")}
        print(f"[{nome}] " + " | ".join(f"{sp}: {cont[(sp, '_paginas')]} pags" for sp in ("train", "val", "test"))
              + (f" | SEM IMAGEM: {faltam}" if faltam else ""))
    n_fontes = collections.Counter(split.values())
    (SAIDA / "ls_split.json").write_text(json.dumps({
        "semente": a.semente, "fontes_por_split": n_fontes,
        "paginas": {p["page_id"]: {"split": split[p["fonte"]], "fonte": p["fonte"], "seed": p["seed"],
                                   "img": p["img"]} for p in paginas},
        "caixas": resumo}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fontes: {dict(n_fontes)} | split em {SAIDA / 'ls_split.json'}")


if __name__ == "__main__":
    main()
