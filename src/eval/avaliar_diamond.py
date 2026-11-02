"""
Avalia segmentacoes em regioes contra a anotacao humana do Diamond (caixas e classes).

A comparacao e feita pelas PALAVRAS de cada regiao, e nao pelas caixas: duas caixas de tamanhos
diferentes que cobrem as mesmas palavras sao a mesma regiao. Cada palavra com letra ou digito vai
para a regiao (nao figura) menor que contem o seu centro; uma regiao e o conjunto dessas palavras.

Medidas, somadas sobre as paginas:
  F1@0,5 / F1@0,9 / F1 exata   casamento 1-1 guloso entre regioes do gabarito e do sistema, pelo
                               Jaccard das palavras (>= 0,5, >= 0,9, = 1)
  F1@0,5 com classe            o mesmo, exigindo a mesma classe
  classe certa                 % das palavras cuja regiao tem a mesma classe no sistema e no gabarito
  por classe                   revocacao das regioes do gabarito de cada classe (Jaccard >= 0,5 e mesma classe)

Sistemas:
  v3          blocos do extrator atual (so distingue tabela; o resto conta como texto)
  proposta    a pre-anotacao gravada no lote (a que o anotador viu: ATENCAO, o gabarito partiu dela)
  regioes_v2  proposta com as regras da versao 2
  regioes     src/data/regioes.py rodado agora, com todas as regras da versao 3 (candidato a segmentador v4)
  sem_<regra> regioes sem uma das regras do padrao; com_<regra> com uma regra fora do padrao (--ablacao)
  rose:<lote> anotacoes de VLM gravadas em data/diamond/<lote>/ (anotador "VLM:...")
  regioes_v3+rose:<conj> classes do Rose sobre as caixas da v3 (--rose)

Uso:
    python src/eval/avaliar_diamond.py --lote diamond_piloto --ablacao --rose rose_piloto
"""
from __future__ import annotations

import os
import re
import sys
import json
import argparse
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data import regioes as seg  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond")
DIR_RES = os.path.join(RAIZ, "resultados", "diamond")
RE_ALFANUM = re.compile(r"[0-9A-Za-zÀ-ÿ]")


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def rotular(palavras, regioes):
    """palavra (indice) -> (id da regiao, classe)."""
    saida = {}
    for k, w in enumerate(palavras):
        if not RE_ALFANUM.search(w[0]):
            continue
        cx, cy = (w[1] + w[3]) / 2, (w[2] + w[4]) / 2
        dentro = [r for r in regioes if r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3]]
        if not dentro:
            continue
        nao_figura = [r for r in dentro if r["classe"] != "figura"] or dentro
        r = min(nao_figura, key=lambda r: (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1]))
        saida[k] = (r["id"], r["classe"])
    return saida


def _grupos(rot):
    g, classe = collections.defaultdict(set), {}
    for k, (rid, c) in rot.items():
        g[rid].add(k)
        classe[rid] = c
    return [(ks, classe[rid]) for rid, ks in g.items()]


def casar(ref, pred, limiar, com_classe=False):
    """Casamento 1-1 guloso por Jaccard. Devolve os pares (i_ref, j_pred)."""
    G, P = _grupos(ref), _grupos(pred)
    pares = []
    por_palavra = collections.defaultdict(list)
    for j, (b, _) in enumerate(P):
        for k in b:
            por_palavra[k].append(j)
    for i, (a, ca) in enumerate(G):
        vistos = {j for k in a for j in por_palavra[k]}
        for j in vistos:
            b, cb = P[j]
            if com_classe and ca != cb:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= limiar:
                pares.append((jac, i, j))
    pares.sort(reverse=True)
    ui, uj, casados = set(), set(), []
    for _, i, j in pares:
        if i not in ui and j not in uj:
            ui.add(i)
            uj.add(j)
            casados.append((i, j))
    return G, P, casados


def medir_pagina(palavras, ref_regioes, pred_regioes):
    ref, pred = rotular(palavras, ref_regioes), rotular(palavras, pred_regioes)
    m = collections.Counter()
    for nome, lim, cc in (("j50", 0.5, False), ("j90", 0.9, False), ("exata", 1.0, False), ("j50_classe", 0.5, True)):
        G, P, cas = casar(ref, pred, lim, cc)
        m[nome] = len(cas)
        if nome == "j50_classe":
            for i, _ in cas:
                m["ok_" + G[i][1]] += 1
            for _, c in G:
                m["ref_" + c] += 1
    m["ref"], m["pred"] = len(_grupos(ref)), len(_grupos(pred))
    m["palavras"] = len(ref)
    m["classe_ok"] = sum(1 for k in ref if k in pred and pred[k][1] == ref[k][1])
    return m


def resumir(tot):
    f1 = lambda c: round(2 * tot[c] / max(1, tot["ref"] + tot["pred"]), 3)
    return {"regioes_gabarito": tot["ref"], "regioes_sistema": tot["pred"],
            "f1_j50": f1("j50"), "f1_j90": f1("j90"), "f1_exata": f1("exata"), "f1_j50_classe": f1("j50_classe"),
            "classe_certa_palavras": round(tot["classe_ok"] / max(1, tot["palavras"]), 3),
            "revocacao_por_classe": {c: {"n": tot["ref_" + c], "revocacao": round(tot["ok_" + c] / tot["ref_" + c], 3)}
                                     for c in seg.CLASSES if tot["ref_" + c]}}


def regioes_v3(t):
    return [{"id": b["id"], "classe": "tabela" if b.get("tipo") == "tabela" else "texto", "bbox": b["bbox"]}
            for b in t["blocos_v3"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True)
    ap.add_argument("--anotador", help="padrao: qualquer anotador humano (o que nao comeca com 'VLM:')")
    ap.add_argument("--rose", action="append", default=[], help="lote do Rose com as mesmas paginas")
    ap.add_argument("--pred", action="append", default=[],
                    help="jsonl page_id->regioes de um detector (ex.: saida do YOLO), medido como pred:<nome>")
    ap.add_argument("--pred-classe", action="append", default=[],
                    help="HIBRIDO: caixas do extrator (regioes v3) + classe do detector do jsonl, medido como hibrido:<nome>")
    ap.add_argument("--pred-classe-conj", default="todas",
                    help="quais classes o hibrido adota do detector (todas | assinatura_cabecalho | lista de classes)")
    ap.add_argument("--ablacao", action="store_true", help="avalia regioes sem cada uma das regras")
    ap.add_argument("--so-comuns", action="store_true", help="so as paginas que todos os --rose tem")
    a = ap.parse_args()

    tarefas = {t["page_id"]: t for t in ler_jsonl(os.path.join(DIR_DIAMOND, a.lote, "tarefas.jsonl"))}
    gabarito = {}
    for an in ler_jsonl(os.path.join(DIR_DIAMOND, a.lote, "anotacoes.jsonl")):
        humano = not an["anotador"].startswith("VLM:")
        if an["status"] == "concluida" and (an["anotador"] == a.anotador if a.anotador else humano):
            gabarito[an["page_id"]] = an
    if not gabarito:
        sys.exit(f"[ERRO] nenhuma pagina concluida por humano em data/diamond/{a.lote}")
    roses = {}
    for lote in a.rose:
        roses[lote] = {an["page_id"]: an for an in ler_jsonl(os.path.join(DIR_DIAMOND, lote, "anotacoes.jsonl"))
                       if an["anotador"].startswith("VLM:") and an["status"] == "concluida"}
    paginas = sorted(gabarito, key=lambda p: tarefas[p].get("n", 0))
    if a.so_comuns:
        paginas = [p for p in paginas if all(p in r for r in roses.values())]

    sistemas = {"v3": lambda t: regioes_v3(t), "proposta": lambda t: t["proposta"],
                "regioes_v2": lambda t: seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras="v2"),
                "regioes": lambda t: seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True),
                "regioes_sem_fundir": lambda t: seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True, fundir=False)}
    if a.ablacao:
        for regra in seg.REGRAS:
            padrao = regra in seg.REGRAS_PADRAO
            ativas = tuple(r for r in seg.REGRAS_PADRAO if r != regra) if padrao else seg.REGRAS_PADRAO + (regra,)
            sistemas[("sem_" if padrao else "com_") + regra] = (lambda ativas: lambda t: seg.propor(
                t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=ativas))(ativas)
    for lote, anots in roses.items():
        sistemas["rose:" + lote] = (lambda anots: lambda t: anots.get(t["page_id"], {}).get("regioes"))(anots)
    for arq in a.pred:
        nome = os.path.splitext(os.path.basename(arq))[0]
        d = {x["page_id"]: x.get("regioes") for x in ler_jsonl(arq)}
        sistemas["pred:" + nome] = (lambda d: lambda t: d.get(t["page_id"]))(d)
    for arq in a.pred_classe:
        nome = os.path.splitext(os.path.basename(arq))[0]
        d = {x["page_id"]: x.get("regioes") for x in ler_jsonl(arq)}
        sistemas["hibrido:" + nome] = (lambda d: lambda t: seg.aplicar_classes_rose(
            seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True),
            t["palavras"], d.get(t["page_id"]) or [], a.pred_classe_conj))(d)
    if roses:
        conjuntos = ["todas", "assinatura_cabecalho", "assinatura_cabecalho_titulo_rodape"]
        for lote, anots in roses.items():
            prefixo = "regioes_v3+rose" if len(roses) == 1 else f"regioes_v3+rose_{lote}"
            for conj in conjuntos:
                sistemas[f"{prefixo}:{conj}"] = (lambda anots, conj: lambda t: (
                    seg.aplicar_classes_rose(
                        seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True),
                        t["palavras"],
                        anots[t["page_id"]]["regioes"],
                        conj,
                    ) if t["page_id"] in anots and anots[t["page_id"]].get("regioes") else None
                ))(anots, conj)

    resultado = {"lote": a.lote, "paginas": len(paginas), "sistemas": {}, "por_pagina": {}}
    for nome, gerar in sistemas.items():
        tot, n = collections.Counter(), 0
        for pid in paginas:
            t = tarefas[pid]
            pred = gerar(t)
            if pred is None:
                continue
            m = medir_pagina(t["palavras"], gabarito[pid]["regioes"], pred)
            tot.update(m)
            n += 1
            resultado["por_pagina"].setdefault(pid, {})[nome] = resumir(m)["f1_j50"]
        resultado["sistemas"][nome] = {"paginas": n, **resumir(tot)}

    os.makedirs(os.path.join(DIR_RES, a.lote), exist_ok=True)
    with open(os.path.join(DIR_RES, a.lote, "avaliacao.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    linhas = [f"# Diamond `{a.lote}`: segmentacao contra a anotacao humana", "",
              f"{len(paginas)} paginas. Comparacao pelas palavras de cada regiao (docstring de "
              "`src/eval/avaliar_diamond.py`). A `proposta` e a pre-anotacao que o anotador viu: "
              "o gabarito partiu dela, entao o numero dela esta inflado.", "",
              "| Sistema | Paginas | Regioes (gabarito) | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (palavras) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for nome, s in resultado["sistemas"].items():
        linhas.append(f"| {nome} | {s['paginas']} | {s['regioes_sistema']} ({s['regioes_gabarito']}) | {s['f1_j50']:.3f} | "
                      f"{s['f1_j90']:.3f} | {s['f1_exata']:.3f} | {s['f1_j50_classe']:.3f} | "
                      f"{100 * s['classe_certa_palavras']:.1f}% |")
    linhas += ["", "## Revocacao por classe (Jaccard >= 0,5 e mesma classe)", "",
               "| Sistema | " + " | ".join(seg.CLASSES) + " |", "|---|" + "---:|" * len(seg.CLASSES)]
    for nome, s in resultado["sistemas"].items():
        rc = s["revocacao_por_classe"]
        linhas.append(f"| {nome} | " + " | ".join(f"{rc[c]['revocacao']:.2f} ({rc[c]['n']})" if c in rc else "—"
                                                   for c in seg.CLASSES) + " |")
    with open(os.path.join(DIR_RES, a.lote, "avaliacao.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))
    print(f"\n[OK] resultados/diamond/{a.lote}/avaliacao.json e .md")


if __name__ == "__main__":
    main()
