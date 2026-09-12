"""
Congela, para cada pagina de um lote do Golden, as palavras que formam cada bloco.

A anotacao humana (anotacoes.jsonl) guarda a ordem dos BLOCOS pelos seus ids. Os ids so
existem para a segmentacao que gerou o lote: se o extrator mudar, os blocos mudam e a
anotacao deixa de valer. Com as palavras de cada bloco guardadas, a ordem anotada pode ser
levada para o nivel da palavra e dali projetada em qualquer outra segmentacao.

So LE o lote e os PDFs. Grava data/golden/<lote>/derivados/palavras_por_bloco.jsonl, uma
linha por pagina:
  {"page_id", "extrator_sha256", "blocos": {"b0": [[texto, x0, top, x1, bottom], ...], ...}}
com as palavras de cada bloco em ordem de leitura DENTRO do bloco (linha a linha, da
esquerda para a direita), a mesma usada para montar o texto do bloco.

Antes de gravar, confere pagina a pagina que a segmentacao atual reproduz exatamente os
blocos do lote (id, texto e caixa). Pagina que nao reproduz e recusada e listada.

Uso:
    python src/anotacao/congelar_palavras.py --lote golden_v1
"""
from __future__ import annotations

import os
import sys
import json
import random
import hashlib
import argparse
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import RAIZ_PROJETO  # noqa: E402

RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
EXTRATOR = os.path.join(RAIZ_PROJETO, "src", "data", "extrator.py")


def palavras_da_tarefa(t):
    """Refaz a segmentacao de uma pagina do lote e devolve (registro, erro)."""
    import pdfplumber
    from src.data import extrator as ex
    with pdfplumber.open(os.path.join(RAW, t["uf"], t["arquivo"])) as pdf:
        page = pdf.pages[t["pagina"]]
        reg, motivo = ex.processar_pagina(page, t["uf"], t["arquivo"], t["pagina"])
        ws = ex.palavras_da_pagina(page)
    if reg is None:
        return None, f"nao gerou blocos ({motivo})"
    if reg["bounding_boxes"] != t["bounding_boxes"]:
        return None, "blocos diferentes dos do lote"
    blocos = ex.segmentar(ws)
    # mesma permutacao semeada de processar_pagina
    rng = random.Random(t["page_id"])
    perm = list(range(len(blocos)))
    rng.shuffle(perm)
    saida = {}
    for k, B in enumerate(blocos):
        palavras = []
        for L in sorted(B["linhas"], key=lambda L: L["top"]):
            for w in sorted(L["ws"], key=lambda w: w["x0"]):
                palavras.append([w["t"], round(w["x0"], 2), round(w["top"], 2),
                                 round(w["x1"], 2), round(w["bottom"], 2)])
        saida[f"b{perm[k]}"] = palavras
    return {"page_id": t["page_id"], "blocos": saida}, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()

    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    with open(os.path.join(dir_lote, "tarefas.jsonl"), encoding="utf-8") as f:
        tarefas = [json.loads(l) for l in f if l.strip()]
    with open(EXTRATOR, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    registros, recusadas = {}, []
    with Pool(a.workers) as pool:
        for t, (reg, erro) in zip(tarefas, pool.imap(palavras_da_tarefa, tarefas)):
            if erro:
                recusadas.append((t["page_id"], erro))
            else:
                reg["extrator_sha256"] = sha
                registros[t["page_id"]] = reg
            print(f"    {len(registros) + len(recusadas)}/{len(tarefas)} {t['page_id']}"
                  + (f"  [RECUSADA: {erro}]" if erro else ""), flush=True)

    if recusadas:
        print(f"[ERRO] {len(recusadas)} paginas nao reproduzem os blocos do lote; nada foi gravado:")
        for pid, erro in recusadas:
            print(f"    {pid}: {erro}")
        sys.exit(1)

    os.makedirs(os.path.join(dir_lote, "derivados"), exist_ok=True)
    destino = os.path.join(dir_lote, "derivados", "palavras_por_bloco.jsonl")
    with open(destino, "w", encoding="utf-8") as f:
        for t in tarefas:
            f.write(json.dumps(registros[t["page_id"]], ensure_ascii=False) + "\n")
    n_pal = sum(len(p) for r in registros.values() for p in r["blocos"].values())
    print(f"[OK] {len(registros)} paginas, {n_pal} palavras, extrator {sha[:12]} -> {destino}")


if __name__ == "__main__":
    main()
