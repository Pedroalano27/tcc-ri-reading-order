# -*- coding: utf-8 -*-
"""
Painel visual, na MESMA pagina do golden_v4: como o extrator trabalha hoje e como fica a ideia nova.

  esquerda  HOJE: extrator com caixas finas (propor(): palavras + blocos v3 + Docling + regras). Cada
            pedaco de texto vira uma caixa com classe (titulo, texto, lista, assinatura...). E nessa
            etapa que nasce a maior parte dos erros: caixa partida, fundida ou com classe errada.
  direita   IDEIA NOVA (plano do orientador): so TABELA e IMAGEM viram caixa. O texto nao e dividido:
            fica como um fluxo de linhas (realce azul), separado em colunas (tracos verticais), e a
            ordem de leitura e o caminho vermelho que liga as linhas.

Reusa orquestracao/analises/ordem_sem_bbox.py (metodo e configuracao escolhida no relatorio) e a
deteccao de colunas da galeria; nao roda modelo nenhum (usa o detector ja guardado nos lotes Diamond).

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\comparacao_visual_fino_x_grosso.py
    venv\\Scripts\\python.exe orquestracao\\analises\\comparacao_visual_fino_x_grosso.py --todas
Saida: resultados/comparacao_fino_x_grosso/NN_<veiculo>.jpg
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
import src.data.regioes as seg  # noqa: E402
from orquestracao.analises.ordem_sem_bbox import Config, preparar, prever, avaliar_fluxo  # noqa: E402
from orquestracao.analises.galeria_ordem_sem_bbox import extrair_cortes_colunas  # noqa: E402

CFG = Config("projecao_local_margens", 0.45, 1.2, 0.08)
SAIDA = os.path.join(RAIZ, "resultados", "comparacao_fino_x_grosso")
IMG = os.path.join(RAIZ, "data", "golden", "golden_v4", "img")
COR9 = {"titulo": (220, 38, 38), "texto": (37, 99, 235), "lista": (234, 88, 12), "tabela": (147, 51, 234),
        "assinatura": (22, 163, 74), "cabecalho": (8, 145, 178), "rodape": (146, 64, 14),
        "figura": (90, 90, 90), "outro": (219, 39, 119)}
L = 820  # largura de cada painel


def fonte(tam):
    for nome in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def moldura(im, titulo, sub):
    topo = Image.new("RGB", (L, 66), (17, 24, 39))
    d = ImageDraw.Draw(topo)
    d.text((12, 8), titulo, fill=(255, 255, 255), font=fonte(22))
    d.text((12, 38), sub, fill=(203, 213, 225), font=fonte(16))
    fim = Image.new("RGB", (L, 66 + im.height), "white")
    fim.paste(topo, (0, 0)); fim.paste(im, (0, 66))
    return fim


def pagina(q, destino):
    p, d = q["p"], q["d"]
    with Image.open(os.path.join(IMG, p["imagem"])) as im0:
        base = im0.convert("RGB").resize((L, int(im0.height * L / im0.width)))
    sx, sy = L / p["dimensions"]["width"], base.height / p["dimensions"]["height"]
    px = lambda b: [b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy]

    # esquerda: caixas finas do extrator atual
    regs = seg.propor(d["palavras"], d["blocos_v3"], d["detector"]["regioes"], regras=True)
    esq = base.copy(); de = ImageDraw.Draw(esq)
    for r in regs:
        de.rectangle(px(r["bbox"]), outline=COR9.get(r["classe"], (0, 0, 0)), width=3)
    classes = sorted({r["classe"] for r in regs})

    # direita: so tabela e imagem viram caixa; o texto e um fluxo de linhas
    seq, itens, diag = prever(q, CFG)
    met = avaliar_fluxo(q, seq)
    cortes, corpo_ids, brutos = extrair_cortes_colunas(q, CFG)
    dire = base.copy().convert("RGBA")
    cam = Image.new("RGBA", dire.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(cam)
    centros = []
    for m in itens:
        b = px(m["bbox"])
        if m["tipo"] in ("table", "picture"):
            dc.rectangle(b, outline=(147, 51, 234, 255) if m["tipo"] == "table" else (90, 90, 90, 255), width=4)
        else:
            dc.rectangle(b, fill=(37, 99, 235, 46))
        centros.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
    if corpo_ids:
        y0 = min(brutos[i]["bbox"][1] for i in corpo_ids) * sy; y1 = max(brutos[i]["bbox"][3] for i in corpo_ids) * sy
        for c in cortes:
            for y in range(int(y0), int(y1), 14):
                dc.line([(c * sx, y), (c * sx, y + 8)], fill=(22, 163, 74, 255), width=3)
    dc.line(centros, fill=(220, 38, 38, 190), width=2)
    if centros:
        x, y = centros[0]; dc.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(220, 38, 38, 255))
    dire = Image.alpha_composite(dire, cam).convert("RGB")
    n_at = sum(m["tipo"] in ("table", "picture") for m in itens)

    a = moldura(esq, f"HOJE: extrator com caixas finas  ({len(regs)} caixas)",
                "cada cor e uma classe: " + ", ".join(classes))
    b = moldura(dire, f"IDEIA NOVA: so tabela e imagem viram caixa  ({n_at} caixas)",
                f"texto = fluxo de linhas (azul), {len(cortes) + 1} coluna(s), caminho de leitura em vermelho")
    tela = Image.new("RGB", (2 * L + 12, a.height + 40), (200, 200, 200))
    tela.paste(Image.new("RGB", (2 * L + 12, 40), "white"), (0, 0))
    ImageDraw.Draw(tela).text((12, 9), f"{p['page_id']}   |   tau de regioes da ideia nova nesta pagina: "
                                       f"{met['regioes']['tau']:.3f}", fill=(0, 0, 0), font=fonte(18))
    tela.paste(a, (0, 40)); tela.paste(b, (L + 12, 40))
    tela.save(destino, quality=88)
    return len(regs), n_at, len(cortes) + 1, met["regioes"]["tau"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todas", action="store_true", help="as 44 paginas (padrao: 4 escolhidas)")
    a = ap.parse_args()
    ps, _ = preparar()
    os.makedirs(SAIDA, exist_ok=True)
    if not a.todas:
        def n_atomos(q):
            return sum(r["rotulo"] in ("table", "picture") and r["score"] >= CFG.score for r in q["d"]["detector"]["regioes"])
        alvo = [q for q in ps if "Parte II (Poder Legislativo)_2024-02-06.pdf#p1" in q["p"]["page_id"]]      # 3 colunas
        alvo += [q for q in ps if "executive_official_diary_2023-03-06.pdf#p71" in q["p"]["page_id"]]       # 2 colunas, MA
        resto = [q for q in ps if q not in alvo]
        alvo += sorted(resto, key=lambda q: (-n_atomos(q), q["p"]["page_id"]))[:1]                          # mais tabelas
        alvo += [q for q in resto if "duque_de_caxias" in q["p"]["page_id"] and "p44" in q["p"]["page_id"]][:1]  # caso dificil
        ps = alvo
    for k, q in enumerate(ps, 1):
        uf = q["p"]["page_id"].split("/")[0].replace("official_diary_", "")
        destino = os.path.join(SAIDA, f"{k:02d}_{uf}.jpg")
        n, at, col, tau = pagina(q, destino)
        print(f"{os.path.relpath(destino, RAIZ)}  finas={n}  atomos={at}  colunas={col}  tau={tau:.3f}  {q['p']['page_id']}")


if __name__ == "__main__":
    main()
