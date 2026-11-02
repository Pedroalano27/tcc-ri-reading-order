"""Páginas em que o Pedro anotou reclamação de segmentação (notas do golden_v1/v2/v4), lado a lado:
à esquerda as caixas que ele viu ao reclamar, à direita as unidades sem caixas finas (colunas_margens).
Só desenha; não mede nada. Saída: resultados/reclamacoes_x_novo/NN_<veiculo>.jpg e indice.md.
Uso: venv/Scripts/python.exe -B orquestracao/analises/reclamacoes_x_novo.py
"""
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "resultados/reclamacoes_x_novo"
CORES = {"texto": (2, 132, 199), "tabela": (217, 119, 6), "imagem": (190, 24, 93),
         "margem": (22, 163, 74), "quadro": (124, 58, 237)}
GRUPO = {"table": "tabela", "tabela": "tabela", "picture": "imagem", "imagem": "imagem",
         "cabecalho": "margem", "rodape": "margem", "quadro_externo": "quadro"}


def ler(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def fonte(t):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", t)
    except OSError:
        return ImageFont.load_default()


def painel(img, dims, caixas, cheio):
    base = img.convert("RGBA")
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    sx, sy = base.width / dims["width"], base.height / dims["height"]
    for c in caixas:
        cor = CORES[GRUPO.get(c.get("tipo"), "texto")]
        x0, y0, x1, y1 = c["bbox"]
        d.rectangle([x0 * sx, y0 * sy, x1 * sx, y1 * sy], outline=cor + (255,), width=3,
                    fill=cor + (36,) if cheio else None)
    return Image.alpha_composite(base, cam).convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    notas, tarefas = {}, {}
    for lote in ("golden_v1", "golden_v2", "golden_v4"):
        for t in ler(RAIZ / f"data/golden/{lote}/tarefas.jsonl"):
            tarefas[(lote, t["page_id"])] = t
        for a in ler(RAIZ / f"data/golden/{lote}/anotacoes.jsonl"):
            if a.get("nota"):
                notas.setdefault(a["page_id"], []).append((lote, a["nota"].replace("\n", " "), a.get("flags") or []))
    novo = {}
    for b in ("golden_v4", "golden_v3_novo"):
        with open(RAIZ / f"resultados/unidades_sem_caixas/bancadas/{b}.jsonl", encoding="utf-8") as f:
            for linha in f:
                r = json.loads(linha)
                novo[r["page_id"]] = r["representacoes"]["colunas_margens"]
    indice = ["# Reclamações do Pedro × unidades sem caixas finas", ""]
    n = 0
    for pid, ns in notas.items():
        if pid not in novo:
            indice.append(f"- (sem unidades novas) `{pid}`: {ns[-1][1]}")
            continue
        lote = ns[-1][0]
        t = tarefas[(lote, pid)]
        img = Image.open(RAIZ / f"data/golden/{lote}/img" / t["imagem"]).convert("RGB")
        alt = 1300
        img = img.resize((round(img.width * alt / img.height), alt), Image.LANCZOS)
        un = novo[pid]["bounding_boxes"]
        texto = " | ".join(f"[{l[-2:]}] {x}" for l, x, _ in ns)
        linhas = textwrap.wrap(texto, 150)[:4]
        topo = 60 + 30 * len(linhas)
        folha = Image.new("RGB", (img.width * 2 + 30, alt + topo), "white")
        d = ImageDraw.Draw(folha)
        for i, l in enumerate(linhas):
            d.text((6, 4 + 30 * i), l, fill=(160, 0, 0), font=fonte(22))
        d.text((6, topo - 44), f"O que você viu ({lote}): {len(t['bounding_boxes'])} caixas", fill="black", font=fonte(28))
        d.text((img.width + 36, topo - 44), f"Sem caixas finas: {len(un)} unidades", fill="black", font=fonte(28))
        folha.paste(painel(img, t["dimensions"], t["bounding_boxes"], False), (0, topo))
        folha.paste(painel(img, novo[pid]["dimensions"], un, True), (img.width + 30, topo))
        n += 1
        nome = f"{n:02d}_{pid.split('/')[0].replace('official_diary_', '')}.jpg"
        folha.save(OUT / nome, quality=85)
        indice.append(f"- `{nome}` `{pid}`: {texto}")
    (OUT / "indice.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
    print(n, "paineis")


if __name__ == "__main__":
    main()
