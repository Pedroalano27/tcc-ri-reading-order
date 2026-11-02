# -*- coding: utf-8 -*-
"""
Reclassificador de regiões por FEATURES (leve): em vez de regras duras, um classificador aprende a
classe de cada região a partir de features geométricas e de texto. Treina no ouro do Diamond e é
medido no teste SEM viés (diamond_teste). Ideia vinda do diagnóstico (classe é o gargalo) e do GPT.

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\reclassificador.py \\
        --treino diamond_piloto diamond_treino --teste diamond_teste
"""
import os, sys, json, re, argparse, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.data.regioes as seg

RE_MARCADOR = re.compile(r"^\s*(?:[-•*·]|\d{1,3}[.)\-]|[IVXLCivxlc]{1,4}[.)\-]|[a-zA-Z][.)])\s")
from src.eval.avaliar_diamond import rotular, medir_pagina, resumir, ler_jsonl
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline

DIA = "data/diamond"


def featurize(r, ks, pal, W, H):
    b = r["bbox"]
    txt = [pal[k][0] for k in ks]
    joined = " ".join(txt)
    letras = [c for c in joined if c.isalpha()]
    chars = [c for c in joined if not c.isspace()]
    ls = seg.linhas(pal, ks) if ks else []
    alt = [pal[k][4] - pal[k][2] for k in ks]
    larg_reg = max(1.0, b[2] - b[0])
    frac_marc = (sum(bool(RE_MARCADOR.match(L["texto"])) for L in ls) / len(ls)) if ls else 0.0
    frac_curta = (sum((L["bbox"][2] - L["bbox"][0]) < 0.6 * larg_reg for L in ls) / len(ls)) if ls else 0.0
    # features de LISTA vs TEXTO (sugestao do GPT): hanging indent, alinhamento e ritmo das linhas
    xlefts = [L["bbox"][0] for L in ls]
    if len(ls) >= 2:
        hanging = (statistics.median(xlefts[1:]) - xlefts[0]) / larg_reg   # >0: 1a linha mais a esquerda (marcador)
        left_std = statistics.pstdev(xlefts) / larg_reg
        gaps = [ls[i]["bbox"][1] - ls[i - 1]["bbox"][3] for i in range(1, len(ls))]
        mg = statistics.mean(gaps) if gaps else 0.0
        interline_cv = (statistics.pstdev(gaps) / mg) if gaps and mg > 1e-6 else 0.0
        npl = [len(L["ks"]) for L in ls]
        npl_cv = (statistics.pstdev(npl) / statistics.mean(npl)) if statistics.mean(npl) > 0 else 0.0
    else:
        hanging = left_std = interline_cv = npl_cv = 0.0
    return {
        "frac_marcador": frac_marc,
        "frac_linha_curta": frac_curta,
        "hanging_indent": hanging,
        "left_std": left_std,
        "interline_cv": interline_cv,
        "npl_cv": npl_cv,
        "pal_por_linha": len(ks) / max(1, len(ls)),
        "n_pal": len(ks),
        "n_linhas": len(ls),
        "frac_maiusc": sum(c.isupper() for c in letras) / max(1, len(letras)),
        "frac_digito": sum(c.isdigit() for c in chars) / max(1, len(chars)),
        "alt_font": (statistics.median(alt) / H) if alt else 0.0,
        "larg_rel": (b[2] - b[0]) / W,
        "alt_rel": (b[3] - b[1]) / H,
        "y_topo": b[1] / H,
        "x_centro": ((b[0] + b[2]) / 2) / W,
        "centralizado": abs(((b[0] + b[2]) / 2) / W - 0.5),
        "aspecto": (b[2] - b[0]) / max(1.0, (b[3] - b[1])),
        "area_rel": ((b[2] - b[0]) * (b[3] - b[1])) / (W * H),
        "comeca_campo": int(bool(ls) and seg.comeca_campo(ls[0]["texto"])),
        "eh_assin": int(seg.eh_assinatura(ls)) if ls else 0,
        "termina_2pontos": int(joined.strip().endswith(":")),
        "score": r.get("score") or 0.0,
        "origem_regras": int(r.get("origem") == "regras"),
        "rotulo": str(r.get("rotulo_detector")),
    }


def regioes_com_palavras(t):
    """Regiões do extrator + palavras de cada (por rotular)."""
    pal = t["palavras"]
    ext = seg.propor(pal, t["blocos_v3"], t["detector"]["regioes"], regras=True)
    rot = rotular(pal, ext)
    por = collections.defaultdict(list)
    for k, (rid, _c) in rot.items():
        por[rid].append(k)
    return ext, {r["id"]: por.get(r["id"], []) for r in ext}


def carregar(lote):
    gold = {a["page_id"]: a for a in ler_jsonl(f"{DIA}/{lote}/anotacoes.jsonl") if a["status"] == "concluida"}
    tar = {t["page_id"]: t for t in ler_jsonl(f"{DIA}/{lote}/tarefas.jsonl")}
    return {pid: tar[pid] for pid in gold}, gold


def classe_gold_por_palavra(pal, gold_regioes):
    rot = rotular(pal, gold_regioes)
    return {k: c for k, (_rid, c) in rot.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--treino", nargs="+", default=["diamond_piloto", "diamond_treino"])
    ap.add_argument("--teste", default="diamond_teste")
    ap.add_argument("--limiar", type=float, default=0.5, help="só sobrescreve a classe da regra se a confiança >= limiar")
    a = ap.parse_args()

    X, y = [], []
    for lote in a.treino:
        tar, gold = carregar(lote)
        for pid, t in tar.items():
            ext, palreg = regioes_com_palavras(t)
            wc = classe_gold_por_palavra(t["palavras"], gold[pid]["regioes"])
            for r in ext:
                ks = palreg[r["id"]]
                if not ks:
                    continue
                votos = collections.Counter(wc[k] for k in ks if k in wc)
                if not votos:
                    continue
                X.append(featurize(r, ks, t["palavras"], t["dimensions"]["width"], t["dimensions"]["height"]))
                y.append(votos.most_common(1)[0][0])
    print(f"treino: {len(X)} regiões de {len(a.treino)} lotes; classes: {dict(collections.Counter(y))}")

    clf = make_pipeline(DictVectorizer(sparse=False),
                        RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_leaf=2,
                                               class_weight="balanced", random_state=42, n_jobs=-1))
    clf.fit(X, y)

    # avaliação no teste sem viés: regras vs reclassificador (word-level e F1@0,5 com classe)
    tar, gold = carregar(a.teste)
    tot_regras, tot_reclf = collections.Counter(), collections.Counter()
    acc_regras = acc_reclf = tot_pal = 0
    conf = collections.Counter()
    for pid, t in tar.items():
        ext, palreg = regioes_com_palavras(t)
        wc = classe_gold_por_palavra(t["palavras"], gold[pid]["regioes"])
        # predição por região
        reclf = []
        classes_clf = clf.classes_
        for r in ext:
            ks = palreg[r["id"]]
            nova = dict(r)
            if ks:
                f = featurize(r, ks, t["palavras"], t["dimensions"]["width"], t["dimensions"]["height"])
                proba = clf.predict_proba([f])[0]
                j = proba.argmax()
                if proba[j] >= a.limiar:        # só sobrescreve a regra quando confiante
                    nova["classe"] = classes_clf[j]
            reclf.append(nova)
        # word-level accuracy
        for r_regras, r_reclf in zip(ext, reclf):
            ks = palreg[r_regras["id"]]
            for k in ks:
                if k not in wc:
                    continue
                tot_pal += 1
                acc_regras += (r_regras["classe"] == wc[k])
                acc_reclf += (r_reclf["classe"] == wc[k])
                if r_reclf["classe"] != wc[k]:
                    conf[(wc[k], r_reclf["classe"])] += 1
        tot_regras.update(medir_pagina(t["palavras"], gold[pid]["regioes"], ext))
        tot_reclf.update(medir_pagina(t["palavras"], gold[pid]["regioes"], reclf))

    rr, rc = resumir(tot_regras), resumir(tot_reclf)
    print(f"\nTESTE {a.teste} ({len(tar)} páginas, SEM viés):")
    print(f"  {'sistema':22s} {'F1@0.5':>7} {'F1classe':>9} {'classe_ok':>10}")
    print(f"  {'extrator (regras)':22s} {rr['f1_j50']:7.3f} {rr['f1_j50_classe']:9.3f} {100*acc_regras/max(1,tot_pal):9.1f}%")
    print(f"  {'reclassificador':22s} {rc['f1_j50']:7.3f} {rc['f1_j50_classe']:9.3f} {100*acc_reclf/max(1,tot_pal):9.1f}%")
    print("  confusões do reclf (gold->pred):", dict(conf.most_common(6)))

    # importância das features
    vec = clf.named_steps["dictvectorizer"]; rf = clf.named_steps["randomforestclassifier"]
    imp = sorted(zip(vec.get_feature_names_out(), rf.feature_importances_), key=lambda x: -x[1])[:12]
    print("  features mais importantes:", [(n, round(v, 3)) for n, v in imp])


if __name__ == "__main__":
    main()
