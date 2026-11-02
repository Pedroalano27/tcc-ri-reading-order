# -*- coding: utf-8 -*-
"""
Compara, no teste SEM vies (diamond_teste, anotado do zero), o extrator de regras com detectores
treinados no dataset do Label Studio (16 classes do guia ou 3 classes texto/tabela/imagem).

Duas reguas, porque as taxonomias diferem:
  9 classes  o ouro do Diamond como esta; predicao do guia traduzida por GUIA_PARA_EXTRATOR
             (o guia nao tem "lista": esses itens viram texto e a revocacao de lista zera)
  3 classes  ouro, extrator e detector colapsados em texto / tabela / imagem

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\avaliar_detector_ls.py \\
        --pred ls16=resultados/deteccao/pred_ls16_diamond_teste.jsonl \\
        --pred ls3=resultados/deteccao/pred_ls3_diamond_teste.jsonl
"""
import os, sys, json, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.data.regioes as seg
from src.data.taxonomia_layout import GUIA_PARA_EXTRATOR
from src.eval.avaliar_diamond import medir_pagina, resumir, ler_jsonl

DIA = "data/diamond"
# qualquer vocabulario -> 3 classes
TRES = {"tabela": "tabela", "table": "tabela",
        "figura": "imagem", "figure": "imagem", "chart": "imagem", "heading": "imagem", "imagem": "imagem"}


def para9(c):
    return c if c in seg.CLASSES else GUIA_PARA_EXTRATOR.get(c, "texto" if c == "texto" else "figura" if c == "imagem" else "outro")


def para3(c):
    return TRES.get(c, "texto")


def remapear(regioes, f):
    return [dict(r, classe=f(r["classe"])) for r in regioes]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", default="diamond_teste")
    ap.add_argument("--pred", action="append", default=[], help="nome=arquivo.jsonl (page_id -> regioes)")
    ap.add_argument("--conf", type=float, default=0.0, help="descarta predicao com score abaixo disso")
    a = ap.parse_args()

    gold = {x["page_id"]: x for x in ler_jsonl(f"{DIA}/{a.lote}/anotacoes.jsonl")
            if x["status"] == "concluida" and not x["anotador"].startswith("VLM:")}
    tar = {t["page_id"]: t for t in ler_jsonl(f"{DIA}/{a.lote}/tarefas.jsonl")}
    sistemas = {"extrator (regras+Docling)": lambda t: seg.propor(
        t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True)}
    for item in a.pred:
        nome, arq = item.split("=", 1)
        preds = {x["page_id"]: [r for r in x["regioes"] if (r.get("score") or 1) >= a.conf] for x in ler_jsonl(arq)}
        sistemas[f"detector {nome}"] = (lambda preds: lambda t: preds.get(t["page_id"], []))(preds)

    print(f"{a.lote}: {len(gold)} paginas anotadas do zero\n")
    for regua, f in (("9 classes", para9), ("3 classes (texto/tabela/imagem)", para3)):
        print(f"--- {regua} ---")
        print(f"{'sistema':28s} {'F1@0,5':>7} {'F1@0,9':>7} {'F1 c/cls':>9} {'classe%':>8} {'regioes':>9}")
        for nome, gera in sistemas.items():
            tot = collections.Counter()
            for pid, g in gold.items():
                pred = remapear(gera(tar[pid]), f)
                tot.update(medir_pagina(tar[pid]["palavras"], remapear(g["regioes"], f), pred))
            r = resumir(tot)
            print(f"{nome:28s} {r['f1_j50']:7.3f} {r['f1_j90']:7.3f} {r['f1_j50_classe']:9.3f} "
                  f"{100 * r['classe_certa_palavras']:7.1f}% {r['regioes_sistema']:4d}/{r['regioes_gabarito']}")
        print()


if __name__ == "__main__":
    main()
