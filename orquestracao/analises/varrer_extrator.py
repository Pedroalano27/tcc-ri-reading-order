# -*- coding: utf-8 -*-
"""
Varredura de configuracoes do extrator + hibridos, medida no conjunto de teste SEM VIES
(diamond_teste, desenhado do zero). Objetivo: achar o que reduz a super-segmentacao e melhora a
classe sem ancoragem.

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\varrer_extrator.py \\
        --lote diamond_teste --pred resultados/deteccao/pred_diamond_teste.jsonl

Escreve resultados/diamond/<lote>/varredura.md (ranking) e .json.
"""
import os, sys, json, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.data.regioes as seg
from src.eval.avaliar_diamond import medir_pagina, resumir, ler_jsonl

DIA = "data/diamond"


def centros(pal):
    return [seg._centro(w) for w in pal]


def gapfill(ext, pal, yolo, min_palavras=3):
    """Extrator + regioes do YOLO que cobrem palavras que NENHUMA regiao do extrator pegou."""
    cs = centros(pal)
    cobertas = set()
    for r in ext:
        b = r["bbox"]
        for k, (cx, cy) in enumerate(cs):
            if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]:
                cobertas.add(k)
    extra = []
    for yr in yolo:
        b = yr["bbox"]
        ks = [k for k, (cx, cy) in enumerate(cs)
              if b[0] <= cx <= b[2] and b[1] <= cy <= b[3] and k not in cobertas]
        if len(ks) >= min_palavras:
            extra.append(yr)
    return ext + extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", default="diamond_teste")
    ap.add_argument("--pred", default="resultados/deteccao/pred_diamond_teste.jsonl")
    a = ap.parse_args()

    gold = {x["page_id"]: x for x in ler_jsonl(f"{DIA}/{a.lote}/anotacoes.jsonl") if x["status"] == "concluida"}
    tar = {t["page_id"]: t for t in ler_jsonl(f"{DIA}/{a.lote}/tarefas.jsonl")}
    yolo = {x["page_id"]: x["regioes"] for x in ler_jsonl(a.pred)} if os.path.exists(a.pred) else {}
    if not gold:
        sys.exit(f"[ERRO] nenhuma pagina concluida em {a.lote}")

    V3 = seg.REGRAS_V3
    # (nome, funcao que gera as regioes de uma tarefa)
    def extr(regras, score=0.45):
        def f(t):
            velho = seg.SCORE_MIN
            seg.SCORE_MIN = score
            try:
                return seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=regras)
            finally:
                seg.SCORE_MIN = velho
        return f

    def hib(conj):
        def f(t):
            ext = extr(True)(t)
            return seg.aplicar_classes_rose(ext, t["palavras"], yolo.get(t["page_id"]) or [], conj)
        return f

    def hib_gap(t):
        ext = extr(True)(t)
        return gapfill(ext, t["palavras"], yolo.get(t["page_id"]) or [])

    sistemas = {}
    sistemas["extrator v3 (atual)"] = extr(True)
    sistemas["sem regras"] = extr(())
    sistemas["regras v2"] = extr("v2")
    for r in V3:
        sistemas[f"v3 sem {r}"] = extr(tuple(x for x in V3 if x != r))
    for r in V3:
        sistemas[f"so {r}"] = extr((r,))
    for sm in (0.35, 0.55, 0.65):
        sistemas[f"v3 score_min={sm}"] = extr(True, sm)
    if yolo:
        for conj in ["todas", "assinatura_cabecalho", "lista,assinatura,cabecalho,figura",
                     "tabela,figura,assinatura,cabecalho,rodape,lista"]:
            sistemas[f"hibrido classe [{conj}]"] = hib(conj)
        sistemas["hibrido gapfill (caixas)"] = hib_gap

    resultados = {}
    for nome, gen in sistemas.items():
        tot = collections.Counter()
        for pid, g in gold.items():
            pred = gen(tar[pid])
            if pred:
                tot.update(medir_pagina(tar[pid]["palavras"], g["regioes"], pred))
        resultados[nome] = resumir(tot)

    base = resultados["extrator v3 (atual)"]
    ordenado = sorted(resultados.items(), key=lambda kv: kv[1]["f1_j50_classe"], reverse=True)
    linhas = [f"# Varredura do extrator em `{a.lote}` ({len(gold)} paginas, SEM ancoragem)", "",
              "Ordenado por F1@0,5 com classe. `d` = diferenca vs extrator atual.", "",
              "| Configuracao | F1@0,5 | F1@0,9 | F1 c/ classe | d classe | Classe % | regioes |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for nome, r in ordenado:
        d = r["f1_j50_classe"] - base["f1_j50_classe"]
        marca = " **<**" if abs(d) < 1e-9 else ""
        linhas.append(f"| {nome}{marca} | {r['f1_j50']:.3f} | {r['f1_j90']:.3f} | "
                      f"**{r['f1_j50_classe']:.3f}** | {d:+.3f} | {100*r['classe_certa_palavras']:.1f}% | "
                      f"{r['regioes_sistema']}/{r['regioes_gabarito']} |")
    out_md = f"resultados/diamond/{a.lote}/varredura.md"
    out_json = f"resultados/diamond/{a.lote}/varredura.json"
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    open(out_md, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    json.dump(resultados, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[OK] {out_md}")
    for nome, r in ordenado[:6]:
        print(f"  {nome:44s} F1classe={r['f1_j50_classe']:.3f} F1@0.5={r['f1_j50']:.3f} reg={r['regioes_sistema']}")


if __name__ == "__main__":
    main()
