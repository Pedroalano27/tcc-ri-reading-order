"""
Monta a página de apresentação para o orientador (docs/apresentacao/ordem-de-leitura.html).

Injeta no template os números de resultados/comparacao.json e as figuras de
docs/figuras/ (convertidas para JPEG e embutidas como data URI, para que o HTML
funcione sozinho, inclusive offline). Rode depois de src/eval/comparar.py e
src/eval/figuras.py sempre que os resultados mudarem.

Uso:
    python docs/apresentacao/montar_apresentacao.py
"""
import io
import os
import json
import time
import base64
import subprocess

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(AQUI))
RES = os.path.join(PROJ, "resultados")
FIG = os.path.join(PROJ, "docs", "figuras")
MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]


def img(nome, largura=1500):
    im = Image.open(os.path.join(FIG, nome)).convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def v(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def main():
    with open(os.path.join(RES, "comparacao.json"), encoding="utf-8") as f:
        comp = json.load(f)
    todas, sub = comp["todas_as_paginas"], comp["subconjunto_llm"]
    llm = sub["llm_llava_7b"]
    commit = subprocess.run(["git", "-C", PROJ, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    hoje = time.localtime()

    campos = {
        "DADOS_JSON": json.dumps({"todas": todas, "sub": sub, "n_sub": comp["n_subconjunto_llm"]}),
        "IMG_FIG1": img("fig1_caracterizacao_por_veiculo.png"),
        "IMG_FIG2": img("fig2_problema_pagina_real.png"),
        "DATA": f"{hoje.tm_mday} {MESES[hoje.tm_mon - 1]} {hoje.tm_year}",
        "COMMIT": commit,
        "N_TESTE": str(comp["paginas_teste"]),
        "N_SUB": str(comp["n_subconjunto_llm"]),
        "TAU_XYCUT": v(todas["xycut"]["tau"]),
        "TAU_LAYOUTLM": v(todas["layoutlm"]["tau"]),
        "TAU_SEM_LAYOUT": v(todas["layoutlm_sem_layout"]["tau"]),
        "TAU_LSTM_TEXTO": v(todas["lstm_texto"]["tau"]),
        "TAU_LSTM_GEO": v(todas["lstm_geo"]["tau"]),
        "TAU_LLM": v(llm["tau"]),
        "LAT_LLM": v(llm["tempo_ms"] / 1000, 1),
        "RAZAO_LLM": f"{llm['tempo_ms'] / sub['layoutlm']['tempo_ms']:,.0f}".replace(",", "."),
    }

    with open(os.path.join(AQUI, "apresentacao_template.html"), encoding="utf-8") as f:
        html = f.read()
    for chave, valor in campos.items():
        html = html.replace("{{" + chave + "}}", valor)
    # Documento completo, para abrir direto no navegador (offline). Sem o charset,
    # o navegador le o UTF-8 como Latin-1 e os acentos quebram ("DiÃ¡rios").
    html = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
            + html + '\n</body>\n</html>\n')
    saida = os.path.join(AQUI, "ordem-de-leitura.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {saida} ({len(html) / 1024:.0f} KB) | marcadores nao substituidos: {html.count('{{')}")


if __name__ == "__main__":
    main()
