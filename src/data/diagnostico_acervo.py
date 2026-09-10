"""
Diagnostica a qualidade do acervo de diarios para a tarefa de ordem de leitura.

Para cada UF em data/raw/, amostra PDFs e mede:
  - integridade: o arquivo abre?
  - camada de texto: extrai palavras com coordenadas (dispensa OCR)?
  - (cid:N): fracao do texto que a fonte nao permite decodificar (texto perdido)
  - multicoluna: a pagina tem 2+ colunas, ou seja, o problema existe ali?
  - desordem: quanto a ordem crua do PDF difere da ordem de leitura humana

Uso:
    python src/data/diagnostico_acervo.py [pdfs_por_uf]
"""
import os
import re
import sys
import glob
import json
import random
import warnings

warnings.filterwarnings("ignore")
import pdfplumber

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAIZ = os.path.join(RAIZ_PROJETO, "data", "raw")
SAIDA = os.path.join(RAIZ_PROJETO, "data", "diagnostico_acervo.json")

POR_UF = int(sys.argv[1]) if len(sys.argv) > 1 else 4
RE_CID = re.compile(r"\(cid:\d+\)")
random.seed(42)


def agrupar_linhas(pagina, tol=3):
    """Agrupa palavras em linhas pela coordenada vertical."""
    linhas = []
    for p in pagina.extract_words():
        for l in linhas:
            if abs(l["top"] - p["top"]) <= tol:
                l["palavras"].append(p)
                l["x0"] = min(l["x0"], p["x0"])
                l["x1"] = max(l["x1"], p["x1"])
                break
        else:
            linhas.append({"top": p["top"], "x0": p["x0"], "x1": p["x1"], "palavras": [p]})
    for l in linhas:
        l["texto"] = " ".join(w["text"] for w in sorted(l["palavras"], key=lambda w: w["x0"]))
    return linhas


def analisar_pagina(pag):
    """Metricas de uma pagina. Retorna None se nao houver texto extraivel."""
    linhas = agrupar_linhas(pag)
    if not linhas:
        return None

    texto = " ".join(l["texto"] for l in linhas)
    prop_cid = len(RE_CID.findall(texto)) / max(1, len(texto.split()))

    largura = pag.width
    meio = largura / 2
    # Heuristica de coluna: pagina multicoluna tem maioria de linhas curtas,
    # porque nenhuma linha atravessa a pagina inteira.
    curtas = sum(1 for l in linhas if (l["x1"] - l["x0"]) < largura * 0.55)
    prop_curtas = curtas / len(linhas)

    # Ordem de leitura humana: coluna esquerda inteira, depois a direita.
    esq = sorted([l for l in linhas if (l["x0"] + l["x1"]) / 2 < meio], key=lambda l: l["top"])
    dir_ = sorted([l for l in linhas if (l["x0"] + l["x1"]) / 2 >= meio], key=lambda l: l["top"])
    correta = esq + dir_
    pos = {id(l): k for k, l in enumerate(correta)}
    fora = sum(1 for k, l in enumerate(linhas) if pos[id(l)] != k)

    return {
        "linhas": len(linhas),
        "prop_cid": prop_cid,
        "multicoluna": prop_curtas > 0.6,
        "prop_curtas": prop_curtas,
        "desordem": fora / len(linhas),
    }


def main():
    if not os.path.isdir(RAIZ):
        print(f"[!] {RAIZ} nao existe. Rode antes: python src/data/extrair_zips.py <pasta_zips>")
        return

    ufs = sorted(d for d in os.listdir(RAIZ)
                 if os.path.isdir(os.path.join(RAIZ, d)) and d.startswith("official_diary"))
    resultado = {}

    for uf in ufs:
        pdfs = glob.glob(os.path.join(RAIZ, uf, "**", "*.pdf"), recursive=True)
        if not pdfs:
            continue
        amostra = random.sample(pdfs, min(POR_UF, len(pdfs)))
        r = {"total_pdfs": len(pdfs), "abertos": 0, "corrompidos": 0,
             "sem_texto": 0, "paginas": [], "erros": []}

        for caminho in amostra:
            try:
                with pdfplumber.open(caminho) as pdf:
                    r["abertos"] += 1
                    # 2a pagina e meio do documento: a 1a costuma ser capa/expediente
                    idxs = [i for i in (1, len(pdf.pages) // 2) if i < len(pdf.pages)] or [0]
                    for i in idxs:
                        m = analisar_pagina(pdf.pages[i])
                        if m is None:
                            r["sem_texto"] += 1
                        else:
                            r["paginas"].append(m)
            except Exception as e:
                r["corrompidos"] += 1
                r["erros"].append(f"{os.path.basename(caminho)}: {type(e).__name__}")

        resultado[uf] = r
        print(f"  {uf}: {r['abertos']}/{len(amostra)} abertos, {len(r['paginas'])} paginas",
              flush=True)

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] relatorio salvo em {SAIDA}")


if __name__ == "__main__":
    main()
