"""
Bancada reproduzivel para comparar versoes do segmentador de blocos.

Compara, nas MESMAS paginas, as colecoes armazenadas v1 e B com o codigo atual
de src/data/extrator.py executado ao vivo. A amostra contem quatro paginas-problema
documentadas e mais 40 paginas sorteadas com semente fixa, balanceadas entre os
veiculos de teste e os veiculos cuja ordem de fluxo nao e confiavel.

O script nunca escreve em data/. A unica saida persistente e
resultados/avaliacao_segmentacao.json. Paginas ausentes de uma colecao contam como
rejeitadas pelo filtro; no codigo ao vivo tambem sao registradas paginas com menos
de 3 ou mais de 200 blocos, sem descartar suas metricas de segmentacao.

Uso:
    venv/Scripts/python.exe src/data/avaliar_segmentacao.py
    venv/Scripts/python.exe src/data/avaliar_segmentacao.py --n-amostra 40 --seed 42
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.data.extrator import (MAX_BLOCOS, MIN_BLOCOS, RAW, palavras_da_pagina,  # noqa: E402
                               segmentar)
from src.data.reextrair import qualidade  # noqa: E402

DIR_V1 = os.path.join(RAIZ, "data", "processed", "blocos_v1")
DIR_B = os.path.join(RAIZ, "data", "processed", "blocos")
ARQ_SPLITS = os.path.join(RAIZ, "data", "processed", "splits.json")
SAIDA = os.path.join(RAIZ, "resultados", "avaliacao_segmentacao.json")

PROBLEMAS = [
    ("official_diary_ma", "executive_official_diary_2024-01-18_22_36.pdf", 0, "entrada em negrito"),
    ("official_diary_se", "DOE-SE_2023-03-10_5100.pdf", 14, "texto justificado"),
    ("official_diary_rj", "Parte II (Poder Legislativo)_2024-02-06.pdf", 1, "tres colunas"),
    ("official_diary_ce", "do20250314p03.pdf", 45, "texto corrido fundido"),
]


def ler_colecao(pasta):
    """Indexa paginas validas de uma pasta JSONL por page_id."""
    paginas = {}
    if not os.path.isdir(pasta):
        return paginas
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".jsonl"):
            continue
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            for linha in f:
                try:
                    pagina = json.loads(linha)
                except (json.JSONDecodeError, TypeError):
                    continue
                paginas[pagina["page_id"]] = pagina
    return paginas


def id_pagina(uf, arquivo, pagina):
    return f"{uf}/{arquivo}#p{pagina}"


def amostra_balanceada(paginas, veiculos, n, seed):
    """Sorteio em rodadas: cada veiculo contribui antes de um repetir."""
    rng = random.Random(seed)
    grupos = defaultdict(list)
    for pagina in paginas.values():
        if pagina["uf"] in veiculos:
            grupos[pagina["uf"]].append(pagina)
    for grupo in grupos.values():
        grupo.sort(key=lambda p: p["page_id"])
        rng.shuffle(grupo)
    escolhidas = []
    nomes = sorted(grupos)
    rng.shuffle(nomes)
    rodada = 0
    while len(escolhidas) < n:
        adicionou = False
        for nome in nomes:
            if rodada < len(grupos[nome]):
                escolhidas.append(grupos[nome][rodada])
                adicionou = True
                if len(escolhidas) == n:
                    break
        if not adicionou:
            break
        rodada += 1
    return escolhidas


def pagina_de_blocos(modelo, blocos):
    caixas = [{"id": f"b{i}", "text": b["texto"],
               "bbox": [b["x0"], b["top"], b["x1"], b["bottom"]]}
              for i, b in enumerate(blocos)]
    return {"page_id": modelo["page_id"], "uf": modelo["uf"],
            "arquivo": modelo["arquivo"], "pagina": modelo["pagina"],
            "dimensions": modelo.get("dimensions", {}), "bounding_boxes": caixas}


def percentil(valores, p):
    if not valores:
        return None
    ordenados = sorted(valores)
    pos = (len(ordenados) - 1) * p
    baixo, alto = int(pos), min(int(pos) + 1, len(ordenados) - 1)
    frac = pos - baixo
    return ordenados[baixo] * (1 - frac) + ordenados[alto] * frac


def resumir(registros, ids_esperados, tempos=None, erros=None):
    disponiveis = [registros[i] for i in ids_esperados if i in registros]
    q = qualidade(disponiveis)
    maiores = [max((len(c["text"].split()) for c in p["bounding_boxes"]), default=0)
               for p in disponiveis]
    return {
        **q,
        "paginas_esperadas": len(ids_esperados),
        "paginas_rejeitadas_filtro": len(ids_esperados) - len(disponiveis),
        "ids_rejeitados": [i for i in ids_esperados if i not in registros],
        "maior_bloco_palavras_p50": round(percentil(maiores, 0.50), 1) if maiores else None,
        "maior_bloco_palavras_p95": round(percentil(maiores, 0.95), 1) if maiores else None,
        "maior_bloco_palavras_max": max(maiores) if maiores else None,
        "tempo_ms_pagina": round(statistics.mean(tempos), 1) if tempos else None,
        "erros": erros or {},
    }


def processar_pdf_ao_vivo(tarefa):
    """Worker de um PDF; fica no topo do modulo para funcionar no spawn do Windows."""
    import pdfplumber

    uf, arquivo, pedidos = tarefa
    saida, tempos, erros = {}, [], {}
    caminho = os.path.join(RAW, uf, *arquivo.split("/"))
    try:
        with pdfplumber.open(caminho) as pdf:
            for modelo in pedidos:
                t0 = time.perf_counter()
                try:
                    blocos = segmentar(palavras_da_pagina(pdf.pages[modelo["pagina"]]))
                    tempos.append((time.perf_counter() - t0) * 1000)
                    if MIN_BLOCOS <= len(blocos) <= MAX_BLOCOS:
                        saida[modelo["page_id"]] = pagina_de_blocos(modelo, blocos)
                    else:
                        erros[modelo["page_id"]] = f"n_blocos={len(blocos)}"
                except Exception as exc:  # lista a pagina com erro; nao perde a amostra inteira
                    erros[modelo["page_id"]] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        for modelo in pedidos:
            erros[modelo["page_id"]] = f"pdf: {type(exc).__name__}: {exc}"
    return saida, tempos, erros


def processar_ao_vivo(modelos, workers):
    saida, tempos, erros = {}, [], {}
    por_pdf = defaultdict(list)
    for modelo in modelos:
        por_pdf[(modelo["uf"], modelo["arquivo"])].append(modelo)
    tarefas = [(uf, arquivo, pedidos) for (uf, arquivo), pedidos in sorted(por_pdf.items())]
    with Pool(min(workers, len(tarefas))) as pool:
        for n, (regs, ts, errs) in enumerate(pool.imap_unordered(processar_pdf_ao_vivo, tarefas), 1):
            saida.update(regs)
            tempos.extend(ts)
            erros.update(errs)
            if n % 5 == 0 or n == len(tarefas):
                print(f"    PDFs processados: {n}/{len(tarefas)}", flush=True)
    return saida, tempos, erros


def imprimir_tabela(resumos):
    print("\nFonte                 paginas  blocos/pag  sobrepostos  1 palavra  maior p50/p95/max  rejeitadas  ms/pag")
    for nome, r in resumos.items():
        tempo = "-" if r["tempo_ms_pagina"] is None else f"{r['tempo_ms_pagina']:.1f}"
        maior = f"{r['maior_bloco_palavras_p50']:g}/{r['maior_bloco_palavras_p95']:g}/{r['maior_bloco_palavras_max']}"
        print(f"{nome:<21}{r['paginas']:>7}  {r['blocos_por_pagina']:>10.1f}  "
              f"{r['prop_blocos_sobrepostos']:>10.1%}  {r['prop_blocos_de_1_palavra']:>9.1%}  "
              f"{maior:>18}  {r['paginas_rejeitadas_filtro']:>10}  {tempo:>6}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-amostra", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=min(8, max(1, (os.cpu_count() or 4) - 2)))
    ap.add_argument("--saida", default=SAIDA)
    args = ap.parse_args()

    v1, versao_b = ler_colecao(DIR_V1), ler_colecao(DIR_B)
    if not v1:
        sys.exit(f"[ERRO] colecao v1 ausente ou vazia: {DIR_V1}")
    with open(ARQ_SPLITS, encoding="utf-8") as f:
        splits = json.load(f)
    veiculos = set(splits["teste"] + splits["ufs_nao_confiaveis"])
    sorteadas = amostra_balanceada(v1, veiculos, args.n_amostra, args.seed)

    modelos = {p["page_id"]: p for p in sorteadas}
    descricoes = {}
    for uf, arquivo, numero, descricao in PROBLEMAS:
        pid = id_pagina(uf, arquivo, numero)
        modelo = v1.get(pid) or versao_b.get(pid) or {
            "page_id": pid, "uf": uf, "arquivo": arquivo, "pagina": numero,
            "dimensions": {},
        }
        modelos[pid] = modelo
        descricoes[pid] = descricao
    modelos_lista = sorted(modelos.values(), key=lambda p: p["page_id"])
    ids = [p["page_id"] for p in modelos_lista]

    print(f"[*] amostra: {len(ids)} paginas ({len(sorteadas)} sorteadas + "
          f"{len(ids) - len(sorteadas)} problemas adicionais), seed={args.seed}", flush=True)
    atual, tempos, erros = processar_ao_vivo(modelos_lista, args.workers)
    resumos = {
        "v1_armazenada": resumir(v1, ids),
        "b_armazenada": resumir(versao_b, ids),
        "codigo_atual": resumir(atual, ids, tempos, erros),
    }
    imprimir_tabela(resumos)

    detalhe_problemas = {}
    for pid, descricao in descricoes.items():
        detalhe_problemas[pid] = {"descricao": descricao}
        for nome, fonte in (("v1_armazenada", v1), ("b_armazenada", versao_b),
                            ("codigo_atual", atual)):
            pagina = fonte.get(pid)
            detalhe_problemas[pid][nome] = (len(pagina["bounding_boxes"]) if pagina else None)
    resultado = {
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": args.seed,
        "n_amostra_sorteada": len(sorteadas),
        "page_ids": ids,
        "veiculos_na_amostra": sorted({p["uf"] for p in modelos_lista}),
        "fontes": resumos,
        "paginas_problema": detalhe_problemas,
    }
    destino = os.path.abspath(args.saida)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] -> {os.path.relpath(destino, RAIZ)}")


if __name__ == "__main__":
    main()
