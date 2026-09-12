"""
Extrator de blocos de texto com bounding boxes a partir de PDFs digitais.

Para cada pagina, produz:
  - blocos de texto (paragrafos/trechos de coluna) com bbox [x0, top, x1, bottom]
  - tres ordens candidatas para esses blocos:

    stream  Ordem do FLUXO DE CONTEUDO do PDF -- a sequencia em que o software
            que gerou o arquivo escreveu o texto. Obtida com
            extract_words(use_text_flow=True). Em muitos geradores ela coincide
            com a ordem de leitura; em outros e arbitraria.

    naive   Ordenacao geometrica ingenua: de cima para baixo, da esquerda para
            a direita. E o que se obtem ao ordenar caixas por (top, x0) --
            baseline tipica de pipelines YOLO + OCR. Em multicoluna, intercala
            as colunas linha a linha.

    xycut   Heuristica XY-cut recursiva (Nagy & Seth, 1984; Ha et al., 1995)
            com deteccao de colunas por calhas verticais e blocos largos
            (cabecalhos, titulos) tratados como separadores de secao.

ATENCAO: o extract_words() PADRAO do pdfplumber (use_text_flow=False) ja
devolve as palavras pre-ordenadas geometricamente, e nao na ordem do arquivo.
Por isso a ordem "crua do PDF" precisa ser obtida com use_text_flow=True.

Uso:
    python src/data/extrator.py --pdfs-por-uf 20 --paginas-por-pdf 6 --workers 6
"""
from __future__ import annotations

import os
import re
import sys
import json
import glob
import time
import random
import argparse
import statistics
import warnings
from multiprocessing import Pool

warnings.filterwarnings("ignore")

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
SAIDA = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos")

RE_CID = re.compile(r"\(cid:\d+\)")

# UFs sabidamente inutilizaveis (ver docs/ACERVO.md): 86% do texto ilegivel.
UFS_EXCLUIDAS = {"official_diary_pi"}
# Arquivos auxiliares do professor que nao sao diarios limpos.
PADROES_EXCLUIDOS = ("apis_pagas", "json_atos", "bounding_boxes", "Anotado")

MIN_BLOCOS = 3
MAX_BLOCOS = 200
MAX_PROP_CID = 0.05


# ---------------------------------------------------------------------------
# Palavras -> linhas -> blocos
# ---------------------------------------------------------------------------

def palavras_da_pagina(page):
    """Palavras em ordem de fluxo do PDF, com o indice de fluxo em 's'."""
    try:
        page = page.dedupe_chars(tolerance=1)   # remove "negrito falso" (texto impresso duas vezes)
    except Exception:
        pass
    brutas = page.extract_words(use_text_flow=True, keep_blank_chars=False,
                                x_tolerance=1.5, y_tolerance=2)
    W, H = float(page.width), float(page.height)
    saida = []
    for i, w in enumerate(brutas):
        if not w.get("upright", True):          # texto rotacionado (ex.: margem vertical)
            continue
        t = w["text"].strip()
        if not t:
            continue
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        if not (0 <= cx <= W and 0 <= cy <= H):   # fora da area visivel
            continue
        saida.append({"t": t, "x0": float(w["x0"]), "x1": float(w["x1"]),
                      "top": float(w["top"]), "bottom": float(w["bottom"]), "s": i})
    return saida


def construir_linhas(ws):
    """Agrupa palavras em linhas SEM atravessar calhas entre colunas."""
    if not ws:
        return []
    larg_char = statistics.median((w["x1"] - w["x0"]) / max(1, len(w["t"])) for w in ws)
    gap_max = max(2.5, 1.8 * larg_char)
    linhas = []
    for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
        hw = w["bottom"] - w["top"]
        alvo = None
        for L in reversed(linhas[-30:]):
            ov = min(L["bottom"], w["bottom"]) - max(L["top"], w["top"])
            h = min(L["bottom"] - L["top"], hw)
            if h <= 0 or ov / h < 0.5:
                continue
            gap_dir = w["x0"] - L["x1"]
            gap_esq = L["x0"] - w["x1"]
            if -1.0 <= gap_dir <= gap_max or -1.0 <= gap_esq <= gap_max:
                alvo = L
                break
        if alvo is None:
            linhas.append({"x0": w["x0"], "x1": w["x1"], "top": w["top"],
                           "bottom": w["bottom"], "ws": [w]})
        else:
            alvo["ws"].append(w)
            alvo["x0"] = min(alvo["x0"], w["x0"])
            alvo["x1"] = max(alvo["x1"], w["x1"])
            alvo["top"] = min(alvo["top"], w["top"])
            alvo["bottom"] = max(alvo["bottom"], w["bottom"])
    return linhas


def construir_blocos(linhas):
    """Agrupa linhas verticalmente adjacentes, na mesma coluna e com fonte parecida."""
    if not linhas:
        return []
    lh = statistics.median(L["bottom"] - L["top"] for L in linhas) or 1.0
    blocos = []
    for L in sorted(linhas, key=lambda L: (L["top"], L["x0"])):
        hL = L["bottom"] - L["top"]
        alvo = None
        for B in reversed(blocos[-40:]):
            gap = L["top"] - B["bottom"]
            if gap < -0.5 * lh or gap > 0.8 * lh:
                continue
            ovx = min(B["x1"], L["x1"]) - max(B["x0"], L["x0"])
            if ovx < 0.5 * min(B["x1"] - B["x0"], L["x1"] - L["x0"]):
                continue
            if abs(hL - B["lh"]) > 0.4 * B["lh"]:      # mudanca de fonte = novo bloco
                continue
            alvo = B
            break
        if alvo is None:
            blocos.append({"x0": L["x0"], "x1": L["x1"], "top": L["top"],
                           "bottom": L["bottom"], "lh": hL, "linhas": [L]})
        else:
            alvo["linhas"].append(L)
            alvo["x0"] = min(alvo["x0"], L["x0"])
            alvo["x1"] = max(alvo["x1"], L["x1"])
            alvo["bottom"] = max(alvo["bottom"], L["bottom"])
    for B in blocos:
        partes = []
        for L in sorted(B["linhas"], key=lambda L: L["top"]):
            partes.append(" ".join(w["t"] for w in sorted(L["ws"], key=lambda w: w["x0"])))
        B["texto"] = " ".join(partes)
        B["s"] = min(w["s"] for L in B["linhas"] for w in L["ws"])
    return blocos


# ---------------------------------------------------------------------------
# Ordens candidatas
# ---------------------------------------------------------------------------

def cortes_verticais(ids, B, calha_min=4.0, largura_min_frac=0.12):
    """Divide os blocos em grupos de colunas separados por calhas verticais vazias."""
    ordem = sorted(ids, key=lambda i: B[i]["x0"])
    grupos = [[ordem[0]]]
    fim = B[ordem[0]]["x1"]
    for i in ordem[1:]:
        if B[i]["x0"] > fim + calha_min:
            grupos.append([i])
        else:
            grupos[-1].append(i)
        fim = max(fim, B[i]["x1"])

    def largura(g):
        return max(B[i]["x1"] for i in g) - min(B[i]["x0"] for i in g)

    W = max(B[i]["x1"] for i in ids) - min(B[i]["x0"] for i in ids)
    # Uma "coluna" estreita demais (ex.: numeracao de artigos na margem) nao e
    # coluna de verdade: funde com a vizinha mais proxima.
    while len(grupos) > 1:
        k = min(range(len(grupos)), key=lambda j: largura(grupos[j]))
        if largura(grupos[k]) >= largura_min_frac * W:
            break
        if k == 0:
            j = 1
        elif k == len(grupos) - 1:
            j = k - 1
        else:
            gap_e = min(B[i]["x0"] for i in grupos[k]) - max(B[i]["x1"] for i in grupos[k - 1])
            gap_d = min(B[i]["x0"] for i in grupos[k + 1]) - max(B[i]["x1"] for i in grupos[k])
            j = k - 1 if gap_e <= gap_d else k + 1
        a, b = sorted((k, j))
        grupos[a] = grupos[a] + grupos[b]
        del grupos[b]
    return grupos


def xycut(ids, B, prof=0):
    """XY-cut recursivo: colunas da esquerda para a direita; blocos largos separam secoes."""
    if len(ids) <= 1 or prof > 60:
        return sorted(ids, key=lambda i: (B[i]["top"], B[i]["x0"]))
    grupos = cortes_verticais(ids, B)
    if len(grupos) > 1:
        saida = []
        for g in grupos:
            saida += xycut(g, B, prof + 1)
        return saida
    W = max(1e-6, max(B[i]["x1"] for i in ids) - min(B[i]["x0"] for i in ids))
    largos = [i for i in ids if (B[i]["x1"] - B[i]["x0"]) >= 0.6 * W]
    conj_largos = set(largos)
    estreitos = [i for i in ids if i not in conj_largos]
    if largos and estreitos:
        largos.sort(key=lambda i: B[i]["top"])
        centros = [(B[i]["top"] + B[i]["bottom"]) / 2 for i in largos]
        secoes = [[] for _ in range(len(largos) + 1)]
        for i in estreitos:
            cy = (B[i]["top"] + B[i]["bottom"]) / 2
            secoes[sum(1 for c in centros if c < cy)].append(i)
        saida = []
        for k in range(len(largos) + 1):
            saida += xycut(secoes[k], B, prof + 1)
            if k < len(largos):
                saida.append(largos[k])
        return saida
    return sorted(ids, key=lambda i: (B[i]["top"], B[i]["x0"]))


def estimar_colunas(B):
    """Numero de colunas do corpo da pagina (ignorando blocos largos)."""
    if not B:
        return 0
    W = max(b["x1"] for b in B) - min(b["x0"] for b in B)
    estreitos = [i for i, b in enumerate(B) if (b["x1"] - b["x0"]) < 0.6 * W]
    if len(estreitos) < 2:
        return 1
    return len(cortes_verticais(estreitos, B))


# ---------------------------------------------------------------------------
# Pagina -> registro JSON
# ---------------------------------------------------------------------------

def processar_pagina(page, uf, arquivo, n_pag):
    ws = palavras_da_pagina(page)
    if len(ws) < 5:
        return None, "sem_texto"
    prop_cid = sum(1 for w in ws if RE_CID.search(w["t"])) / len(ws)
    if prop_cid > MAX_PROP_CID:
        return None, "cid"
    blocos = construir_blocos(construir_linhas(ws))
    if not (MIN_BLOCOS <= len(blocos) <= MAX_BLOCOS):
        return None, "n_blocos"

    page_id = f"{uf}/{arquivo}#p{n_pag}"
    # IDs atribuidos por permutacao aleatoria semeada: nenhum id carrega a
    # ordem de fluxo nem a geometrica (evita vazamento para a LLM, que ve os ids).
    rng = random.Random(page_id)
    perm = list(range(len(blocos)))
    rng.shuffle(perm)
    ids = [f"b{perm[k]}" for k in range(len(blocos))]

    idx = list(range(len(blocos)))
    ordem_stream = [ids[i] for i in sorted(idx, key=lambda i: blocos[i]["s"])]
    ordem_naive = [ids[i] for i in sorted(idx, key=lambda i: (blocos[i]["top"], blocos[i]["x0"]))]
    ordem_xycut = [ids[i] for i in xycut(idx, blocos)]

    caixas = [{"id": ids[i], "text": blocos[i]["texto"],
               "bbox": [round(blocos[i]["x0"], 1), round(blocos[i]["top"], 1),
                        round(blocos[i]["x1"], 1), round(blocos[i]["bottom"], 1)]}
              for i in idx]
    caixas.sort(key=lambda c: int(c["id"][1:]))

    return {
        "page_id": page_id,
        "uf": uf,
        "arquivo": arquivo,
        "pagina": n_pag,
        "dimensions": {"width": round(float(page.width), 1), "height": round(float(page.height), 1)},
        "bounding_boxes": caixas,
        "ordens": {"stream": ordem_stream, "naive": ordem_naive, "xycut": ordem_xycut},
        "stats": {"n_blocos": len(blocos), "n_palavras": len(ws),
                  "prop_cid": round(prop_cid, 4), "n_colunas": estimar_colunas(blocos)},
    }, "ok"


def processar_pdf(tarefa):
    """Worker: processa as paginas amostradas de um PDF."""
    import pdfplumber
    uf, caminho, paginas_por_pdf, semente, incluir_capa = tarefa
    arquivo = os.path.relpath(caminho, os.path.join(RAW, uf)).replace("\\", "/")
    registros, motivos = [], {}
    t0 = time.time()
    try:
        with pdfplumber.open(caminho) as pdf:
            n = len(pdf.pages)
            # pula a capa, exceto quando a coleta precisa do diario inteiro (ex.: experimento de RI)
            candidatas = list(range(n)) if (incluir_capa or n == 1) else list(range(1, n))
            rng = random.Random(semente)
            escolhidas = sorted(rng.sample(candidatas, min(paginas_por_pdf, len(candidatas))))
            for p in escolhidas:
                try:
                    reg, motivo = processar_pagina(pdf.pages[p], uf, arquivo, p)
                    motivos[motivo] = motivos.get(motivo, 0) + 1
                    if reg:
                        registros.append(reg)
                except Exception as e:
                    motivos["erro_pagina"] = motivos.get("erro_pagina", 0) + 1
    except Exception as e:
        motivos["pdf_corrompido"] = 1
    return uf, registros, motivos, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdfs-por-uf", type=int, default=20)
    ap.add_argument("--paginas-por-pdf", type=int, default=6)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ufs", nargs="*", help="restringe a estas UFs (padrao: todas)")
    ap.add_argument("--saida", default=SAIDA,
                    help="pasta dos .jsonl (padrao: data/processed/blocos). Coletas extras devem "
                         "usar outra pasta, para nao sobrescrever as paginas do protocolo")
    ap.add_argument("--incluir-capa", action="store_true",
                    help="processa tambem a primeira pagina de cada PDF (diario inteiro)")
    args = ap.parse_args()

    random.seed(args.seed)
    saida = os.path.abspath(args.saida)
    os.makedirs(saida, exist_ok=True)
    ufs = sorted(d for d in os.listdir(RAW)
                 if os.path.isdir(os.path.join(RAW, d)) and d.startswith("official_diary")
                 and d not in UFS_EXCLUIDAS)
    if args.ufs:
        ufs = [u for u in ufs if u in set(args.ufs)]

    tarefas = []
    for uf in ufs:
        pdfs = [p for p in glob.glob(os.path.join(RAW, uf, "**", "*.pdf"), recursive=True)
                if not any(x in p for x in PADROES_EXCLUIDOS)]
        pdfs.sort()
        for k, p in enumerate(random.sample(pdfs, min(args.pdfs_por_uf, len(pdfs)))):
            tarefas.append((uf, p, args.paginas_por_pdf, f"{args.seed}-{uf}-{k}", args.incluir_capa))

    print(f"[*] {len(ufs)} UFs, {len(tarefas)} PDFs, ate {args.paginas_por_pdf} paginas cada, "
          f"{args.workers} processos -> {saida}", flush=True)
    for uf in ufs:   # limpa execucoes anteriores
        alvo = os.path.join(saida, f"{uf}.jsonl")
        if os.path.exists(alvo):
            os.remove(alvo)

    t0 = time.time()
    motivos_tot, por_uf, feitos = {}, {}, 0
    with Pool(args.workers) as pool:
        for uf, registros, motivos, dt in pool.imap_unordered(processar_pdf, tarefas):
            feitos += 1
            for k, v in motivos.items():
                motivos_tot[k] = motivos_tot.get(k, 0) + v
            if registros:
                with open(os.path.join(saida, f"{uf}.jsonl"), "a", encoding="utf-8") as f:
                    for r in registros:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                por_uf[uf] = por_uf.get(uf, 0) + len(registros)
            if feitos % 25 == 0 or feitos == len(tarefas):
                print(f"  {feitos}/{len(tarefas)} PDFs | {sum(por_uf.values())} paginas uteis "
                      f"| {time.time()-t0:.0f}s", flush=True)

    print(f"\n[OK] {sum(por_uf.values())} paginas em {time.time()-t0:.0f}s -> {saida}")
    print(f"Motivos (paginas): {motivos_tot}")
    with open(os.path.join(saida, "_resumo_extracao.json"), "w", encoding="utf-8") as f:
        json.dump({"args": vars(args), "paginas_por_uf": por_uf, "motivos": motivos_tot,
                   "segundos": round(time.time() - t0, 1)}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
