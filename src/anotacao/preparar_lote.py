"""
Prepara um lote de paginas para a anotacao manual da ordem de leitura (Golden Dataset).

Para cada pagina escolhida grava, em data/golden/<lote>/:
  tarefas.jsonl   blocos (id, texto, bbox) e as ordens automaticas. A ferramenta de
                  anotacao NUNCA mostra essas ordens; elas servem so para a avaliacao.
  img/NNN.jpg     a pagina renderizada a partir do PDF original

Grupos de amostragem (--grupo NOME:N, pode repetir):
  silver    veiculos de TESTE, em que o fluxo do PDF foi considerado confiavel. Comparar
            a anotacao humana com esse rotulo automatico valida (ou derruba) a referencia
            usada em todos os resultados ate aqui.
  incerto   veiculos em que o fluxo do PDF NAO e confiavel. Neles nao se sabe se erra o
            fluxo ou a XY-cut; so a anotacao humana decide.
  <veiculo> um veiculo especifico, ex.: official_diary_go (Goias, fora do acervo: baixe os
            PDFs para data/raw/official_diary_go/ e use --extrair).

As paginas sao sorteadas com semente fixa, em rodizio entre veiculos e alternando
paginas de 3+, 2 e 1 coluna. Uma pagina presente em qualquer lote nunca e repetida.
Rodar de novo com o mesmo --lote ACRESCENTA paginas ao lote, sem apagar anotacoes.

Uso:
    python src/anotacao/preparar_lote.py --lote golden_v1 --grupo silver:10 --grupo incerto:20
    python src/anotacao/preparar_lote.py --lote goias --grupo official_diary_go:20 --extrair
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import random
import argparse
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import carregar_splits, iterar_paginas, DIR_BLOCOS, RAIZ_PROJETO  # noqa: E402

RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
DIR_BLOCOS_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos_golden")


def extrair_veiculo(uf, workers=4):
    """Extrai TODAS as paginas dos PDFs de data/raw/<uf> (veiculos fora do protocolo)."""
    from src.data.extrator import processar_pdf, PADROES_EXCLUIDOS
    pdfs = sorted(p for p in glob.glob(os.path.join(RAW, uf, "**", "*.pdf"), recursive=True)
                  if not any(x in p for x in PADROES_EXCLUIDOS))
    if not pdfs:
        sys.exit(f"[ERRO] nenhum PDF em {os.path.join(RAW, uf)}")
    os.makedirs(DIR_BLOCOS_GOLDEN, exist_ok=True)
    destino = os.path.join(DIR_BLOCOS_GOLDEN, f"{uf}.jsonl")
    tarefas = [(uf, p, 100000, f"golden-{uf}-{k}", True) for k, p in enumerate(pdfs)]
    n = 0
    with Pool(workers) as pool, open(destino, "w", encoding="utf-8") as f:
        for _, registros, _, _ in pool.imap_unordered(processar_pdf, tarefas):
            for r in registros:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += len(registros)
    print(f"[*] {uf}: {n} paginas extraidas de {len(pdfs)} PDFs -> {destino}")


def candidatas(ufs, min_blocos, max_blocos, excluir):
    por_uf = {}
    for uf in ufs:
        proprio = os.path.join(DIR_BLOCOS_GOLDEN, f"{uf}.jsonl")
        fonte = DIR_BLOCOS_GOLDEN if os.path.exists(proprio) else DIR_BLOCOS
        for p in iterar_paginas([uf], fonte):
            if min_blocos <= p["stats"]["n_blocos"] <= max_blocos and p["page_id"] not in excluir:
                por_uf.setdefault(uf, []).append(p)
    return por_uf


def sortear(por_uf, n, rng):
    """Rodizio entre veiculos, alternando as faixas de 3+, 2 e 1 coluna."""
    faixas = {}
    for uf, pags in sorted(por_uf.items()):
        d = {1: [], 2: [], 3: []}
        for p in sorted(pags, key=lambda p: p["page_id"]):
            d[min(3, max(1, p["stats"]["n_colunas"]))].append(p)
        for lista in d.values():
            rng.shuffle(lista)
        faixas[uf] = d
    ufs = sorted(faixas)
    rng.shuffle(ufs)
    escolhidas, vez = [], 0
    while len(escolhidas) < n and ufs:
        alvo = (3, 2, 1)[len(escolhidas) % 3]
        pego = None
        for preferir_alvo in (True, False):
            for k in range(len(ufs)):
                uf = ufs[(vez + k) % len(ufs)]
                opcoes = [alvo] if preferir_alvo else [b for b in (3, 2, 1) if faixas[uf][b]]
                if opcoes and faixas[uf][opcoes[0]]:
                    pego, vez = faixas[uf][opcoes[0]].pop(), (vez + k + 1) % len(ufs)
                    break
            if pego:
                break
        if pego is None:
            break
        escolhidas.append(pego)
    return escolhidas


def renderizar(p, destino, resolucao):
    import pdfplumber
    with pdfplumber.open(os.path.join(RAW, p["uf"], p["arquivo"])) as pdf:
        im = pdf.pages[p["pagina"]].to_image(resolution=resolucao).original.convert("RGB")
    im.save(destino, "JPEG", quality=82, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True, help="nome do lote (letras, numeros, _ ou -)")
    ap.add_argument("--grupo", action="append", required=True, help="NOME:N, ex.: silver:10 ou incerto:20")
    ap.add_argument("--min-blocos", type=int, default=6)
    ap.add_argument("--max-blocos", type=int, default=80)
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--resolucao", type=int, default=110, help="dpi da imagem da pagina")
    ap.add_argument("--extrair", action="store_true",
                    help="extrai antes os veiculos fora do protocolo (ex.: official_diary_go)")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.lote):
        sys.exit("[ERRO] nome de lote: use so letras, numeros, _ ou -")

    splits = carregar_splits()
    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    os.makedirs(os.path.join(dir_lote, "img"), exist_ok=True)
    arq = os.path.join(dir_lote, "tarefas.jsonl")
    ja_usadas, n_existentes = set(), 0
    for outro in glob.glob(os.path.join(DIR_GOLDEN, "*", "tarefas.jsonl")):
        with open(outro, encoding="utf-8") as f:
            ids = [json.loads(l)["page_id"] for l in f if l.strip()]
        ja_usadas |= set(ids)
        if os.path.exists(arq) and os.path.samefile(outro, arq):
            n_existentes = len(ids)

    rng = random.Random(f"{a.semente}-{a.lote}-{n_existentes}")
    novas = []
    for g in a.grupo:
        nome, _, qtd = g.partition(":")
        n = int(qtd or 10)
        if nome == "silver":
            ufs = splits["teste"]
        elif nome == "incerto":
            ufs = splits["ufs_nao_confiaveis"]
        else:
            ufs = [nome]
            if a.extrair:
                extrair_veiculo(nome)
        por_uf = candidatas(ufs, a.min_blocos, a.max_blocos, ja_usadas)
        escolhidas = sortear(por_uf, n, rng)
        for p in escolhidas:
            ja_usadas.add(p["page_id"])
            p["grupo"] = nome
        novas += escolhidas
        print(f"[*] grupo {nome}: {len(escolhidas)} de {n} paginas pedidas, de {len(por_uf)} veiculos "
              f"({sum(len(v) for v in por_uf.values())} candidatas com {a.min_blocos}-{a.max_blocos} blocos)")

    gravadas = 0
    with open(arq, "a", encoding="utf-8") as f:
        for k, p in enumerate(novas, n_existentes + 1):
            nome_img = f"{k:03d}.jpg"
            try:
                renderizar(p, os.path.join(dir_lote, "img", nome_img), a.resolucao)
            except Exception as e:
                print(f"  [!] pagina ignorada, nao renderizou {p['page_id']}: {e}")
                continue
            reg = {"n": k, "page_id": p["page_id"], "grupo": p["grupo"], "uf": p["uf"],
                   "arquivo": p["arquivo"], "pagina": p["pagina"], "dimensions": p["dimensions"],
                   "imagem": nome_img, "bounding_boxes": p["bounding_boxes"],
                   "ordens": p["ordens"], "stats": p["stats"]}
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            gravadas += 1
    blocos = sum(p["stats"]["n_blocos"] for p in novas)
    print(f"[OK] {gravadas} paginas novas no lote '{a.lote}' ({n_existentes + gravadas} no total, "
          f"{blocos} blocos a ordenar) -> {dir_lote}")
    print("     Para anotar: venv\\Scripts\\python.exe src\\anotacao\\servidor.py")


if __name__ == "__main__":
    main()
