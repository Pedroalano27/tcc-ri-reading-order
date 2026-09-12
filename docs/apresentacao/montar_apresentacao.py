"""
Monta a página de apresentação para o orientador (docs/apresentacao/ordem-de-leitura.html).

Injeta no template os números de resultados/comparacao.json, do piloto de RI
(resultados/ri_japeri/resultado.json) e da curva de aprendizado
(resultados/curva_aprendizado/curva.json), e as figuras de docs/figuras/
(convertidas para JPEG e embutidas como data URI, para que o HTML funcione
sozinho, inclusive offline). Rode depois de src/eval/comparar.py e
src/eval/figuras.py sempre que os resultados mudarem.

O parágrafo da curva de aprendizado ({{CURVA_TEXTO}}) é escrito à mão em
CURVA_TEXTO abaixo, porque a leitura depende do resultado.

Uso:
    python docs/apresentacao/montar_apresentacao.py [--artefato CAMINHO]

--artefato grava também uma cópia sem <html>/<head>/<body>, no formato que a
publicação como Artifact espera.
"""
import io
import os
import sys
import json
import time
import base64
import argparse
import subprocess

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(AQUI))
RES = os.path.join(PROJ, "resultados")
FIG = os.path.join(PROJ, "docs", "figuras")
MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]

# Leitura da curva de aprendizado, escrita depois de ver o resultado. Marcadores {{...}} valem aqui.
CURVA_TEXTO = (
    "Sim, e bastante. Com 3.117 páginas extras dos mesmos veículos — 21 vezes o treino original — o τ do "
    "LayoutLM sobe de <span class=\"dado\">{{CURVA_LLM_MIN}}</span> para "
    "<span class=\"dado\">{{CURVA_LLM_MAX}}</span>, cerca de 0,03 a cada vez que o treino dobra, sem sinal de "
    "estacionar. Nas 10% piores páginas ele <strong>já passa a XY-cut</strong> (0,527 contra 0,496), e a "
    "diferença na média caiu de 0,14 para 0,05. Mas a continuidade quase não muda: o sucessor correto vai de "
    "{{CURVA_SUC_MIN}}% para {{CURVA_SUC_MAX}}%, longe dos {{SUC_XYCUT}}% da heurística. Ou seja: mais dados "
    "corrigem a ordem global, e o texto picotado vem da formulação. A BiLSTM de geometria não se mexe "
    "({{CURVA_LSTM_MIN}} para {{CURVA_LSTM_MAX}}). O maior treino levou 10 minutos na RTX 4050 — escalar dados "
    "não depende de placa nova."
)


def img(nome, largura=1500):
    im = Image.open(os.path.join(FIG, nome)).convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def v(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def ler(*partes):
    with open(os.path.join(RES, *partes), encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artefato", help="grava também a versão sem <html>/<head>/<body> neste caminho")
    a = ap.parse_args()

    comp = ler("comparacao.json")
    todas, sub = comp["todas_as_paginas"], comp["subconjunto_llm"]
    llm = sub["llm_llava_7b"]
    ri = ler("ri_japeri", "resultado.json")
    curva = ler("curva_aprendizado", "curva.json")
    lm, ls = curva["resultados"]["layoutlm"], curva["resultados"].get("lstm_geo", {})
    n_min, n_max = min(lm, key=int), max(lm, key=int)
    mrrs = list(ri["controle_pagina_inteira_mrr"].values()) + [r["mrr_trechos_frase"] for r in ri["metodos"].values()]
    commit = subprocess.run(["git", "-C", PROJ, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    hoje = time.localtime()

    campos = {
        "DADOS_JSON": json.dumps({"todas": todas, "sub": sub, "n_sub": comp["n_subconjunto_llm"]}),
        "IMG_FIG1": img("fig1_caracterizacao_por_veiculo.png"),
        "IMG_FIG2": img("fig2_problema_pagina_real.png"),
        "IMG_FIG7": img("fig7_curva_aprendizado.png"),
        "IMG_FIG8": img("fig8_ri_japeri.png"),
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
        "SUC_LAYOUTLM": f"{100 * todas['layoutlm']['sucessor']:.0f}",
        "SUC_XYCUT": f"{100 * todas['xycut']['sucessor']:.0f}",
        "RI_PAGINAS": str(ri["paginas"]),
        "RI_CONSULTAS": str(sum(ri["consultas"].values())),
        "RI_MRR_MIN": v(min(mrrs), 2),
        "RI_MRR_MAX": v(max(mrrs), 2),
        "RI_FID_PISO": v(100 * ri["metodos"]["aleatoria"]["fidelidade"], 1),
        "RI_FID_FLUXO": v(100 * ri["metodos"]["fluxo_pdf"]["fidelidade"], 1),
        "RI_FID_XYCUT": v(100 * ri["metodos"]["xycut"]["fidelidade"], 1),
        "RI_FID_LAYOUTLM": v(100 * ri["metodos"]["layoutlm"]["fidelidade"], 1),
        "CURVA_N_MAX": f"{int(n_max):,}".replace(",", "."),
        "CURVA_LLM_MIN": v(lm[n_min]["tau"]),
        "CURVA_LLM_MAX": v(lm[n_max]["tau"]),
        "CURVA_SUC_MIN": f"{100 * lm[n_min].get('sucessor', 0):.0f}",
        "CURVA_SUC_MAX": f"{100 * lm[n_max].get('sucessor', 0):.0f}",
        "CURVA_LSTM_MIN": v(ls[n_min]["tau"]) if n_min in ls else "—",
        "CURVA_LSTM_MAX": v(ls[n_max]["tau"]) if n_max in ls else "—",
    }
    campos = {"CURVA_TEXTO": CURVA_TEXTO, **campos}      # o texto da curva pode conter outros marcadores

    with open(os.path.join(AQUI, "apresentacao_template.html"), encoding="utf-8") as f:
        html = f.read()
    for chave, valor in campos.items():
        html = html.replace("{{" + chave + "}}", valor)
    if a.artefato:
        with open(a.artefato, "w", encoding="utf-8") as f:
            f.write(html)
    # Documento completo, para abrir direto no navegador (offline). Sem o charset,
    # o navegador le o UTF-8 como Latin-1 e os acentos quebram ("DiÃ¡rios").
    completo = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
                + html + '\n</body>\n</html>\n')
    saida = os.path.join(AQUI, "ordem-de-leitura.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(completo)
    restantes = html.count("{{")
    print(f"[OK] {saida} ({len(completo) / 1024:.0f} KB) | marcadores nao substituidos: {restantes}")
    if restantes:
        sys.exit(1)


if __name__ == "__main__":
    main()
