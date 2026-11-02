# -*- coding: utf-8 -*-
"""
Painel visual: como ficam as caixas, na MESMA pagina do teste do Label Studio, em quatro versoes:
ouro humano do projeto parceiro (convencao do guia), extrator atual (regras + Docling), detector de
3 classes (ls3) e detector de 16 classes (ls16).

Por que: os numeros dizem que o extrator perde no gabarito do parceiro (F1 de localizacao 0,573 x 0,780
do ls3) e ganha no gabarito do autor (0,851 x 0,765). Olhando as caixas da para ver quanto disso e
convencao (granularidade) e quanto e erro.

Le o cache de orquestracao/analises/extrator_vs_detector_ls.py (resultados/ls_teste_cache/); nao roda
modelo nenhum. As imagens sao de paginas do projeto parceiro: a saida fica em
resultados/comparacao_visual_ls/, que esta no .gitignore. NAO publicar.

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\comparacao_visual_ls.py            # escolhe 3 paginas
    venv\\Scripts\\python.exe orquestracao\\analises\\comparacao_visual_ls.py --n 6
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extrator_vs_detector_ls as base  # noqa: E402

SAIDA = base.RAIZ / "resultados/comparacao_visual_ls"
COR = {"texto": (37, 99, 235), "tabela": (147, 51, 234), "imagem": (90, 90, 90)}
TRES = {"table": "tabela", "tabela": "tabela", "figure": "imagem", "chart": "imagem", "heading": "imagem",
        "imagem": "imagem", "figura": "imagem"}


def fonte(tam):
    for nome in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def f1(tp, fp, fn):
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def painel(img, caixas, titulo, larg):
    esc = larg / img.width
    im = img.resize((larg, int(img.height * esc))).convert("RGB")
    d = ImageDraw.Draw(im)
    for c in caixas:
        x0, y0, x1, y1 = [v * esc for v in c["bbox"]]
        d.rectangle([x0, y0, x1, y1], outline=COR[TRES.get(c.get("classe"), "texto")], width=3)
    topo = Image.new("RGB", (larg, 44), (17, 24, 39))
    ImageDraw.Draw(topo).text((12, 9), f"{titulo}  ({len(caixas)} caixas)", fill=(255, 255, 255), font=fonte(22))
    fim = Image.new("RGB", (larg, 44 + im.height), "white")
    fim.paste(topo, (0, 0)); fim.paste(im, (0, 44))
    return fim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--largura", type=int, default=820, help="largura de cada painel em px")
    a = ap.parse_args()
    paginas, _ = base.carregar_ouro()
    met = json.load(open(base.CACHE / "metricas.json", encoding="utf-8"))["metricas_paginas"]
    cand = []
    for p in paginas:
        pal = base.ler(base.caminho_cache(p, "palavras"))
        if pal.get("sem_texto") or not (8 <= len(p["ouro"]) <= 45):
            continue
        fe = f1(*met["extrator"][p["page_id"]]["loc50"]); fd = f1(*met["ls3"][p["page_id"]]["loc50"])
        cand.append((fe, fd, p))
    cand.sort(key=lambda t: t[0])
    # paginas tipicas do extrator (em torno da mediana do F1 dele) e uma do quartil inferior, de fontes distintas
    alvos, fontes = [], set()
    for q in (0.50, 0.25, 0.75, 0.40, 0.60, 0.10):
        i = int(q * (len(cand) - 1))
        for j in sorted(range(len(cand)), key=lambda k: abs(k - i)):
            p = cand[j][2]
            if p["fonte"] not in fontes:
                alvos.append(cand[j]); fontes.add(p["fonte"]); break
        if len(alvos) == a.n:
            break
    SAIDA.mkdir(parents=True, exist_ok=True)
    for k, (fe, fd, p) in enumerate(alvos, 1):
        img = Image.open(base.RAIZ / "data/deteccao/ls16/images/test" / p["img"])
        sist = [("Ouro do Label Studio (convencao do guia)", p["ouro"])]
        for nome, etapa in (("Extrator atual (regras + Docling)", "extrator"), ("Detector de 3 classes", "ls3"),
                            ("Detector de 16 classes", "ls16")):
            sist.append((nome, base.ler(base.caminho_cache(p, etapa))["caixas"]))
        ps = [painel(img, c, t, a.largura) for t, c in sist]
        h = ps[0].height
        cab = Image.new("RGB", (2 * a.largura + 12, 54), (255, 255, 255))
        ImageDraw.Draw(cab).text(
            (12, 12), f"{p['fonte']}  |  F1 de localizacao nesta pagina: extrator {fe:.2f}, detector de 3 classes {fd:.2f}"
                      "  |  azul = texto, roxo = tabela, cinza = imagem", fill=(0, 0, 0), font=fonte(20))
        tela = Image.new("RGB", (2 * a.largura + 12, 54 + 2 * h + 12), (200, 200, 200))
        tela.paste(cab, (0, 0))
        for i, q in enumerate(ps):
            tela.paste(q, ((i % 2) * (a.largura + 12), 54 + (i // 2) * (h + 12)))
        destino = SAIDA / f"convencao_guia_{k:02d}.jpg"
        tela.save(destino, quality=88)
        print(f"{destino.relative_to(base.RAIZ)}  fonte={p['fonte']}  ouro={len(p['ouro'])}  "
              f"extrator={len(sist[1][1])}  ls3={len(sist[2][1])}  ls16={len(sist[3][1])}  F1 ext={fe:.2f} ls3={fd:.2f}")


if __name__ == "__main__":
    main()
