"""
Comparacao final: todos os metodos contra a mesma referencia, nas mesmas paginas.

Le resultados/pred_<metodo>.jsonl de cada metodo e produz:
  resultados/comparacao.json            numeros completos
  resultados/comparacao.md              tabelas prontas para colar no texto do TCC
  resultados/metricas_por_pagina.jsonl  base para as figuras

Alem da media, reporta o PIOR CASO (percentil 10 do tau): um metodo pode ser
bom na media e falhar catastroficamente em algumas paginas -- a mesma
preocupacao de Rodrigues et al. (SIGIR 2022) com modelos neurais de ranking.
Testes de Wilcoxon pareados verificam se as diferencas sao significativas.

LLMs novas (ex.: rodadas no Kaggle) entram sozinhas: o nome exibido vem dos
campos "modelo" e "few_shot" gravados por llm_ordem.py em cada predicao.
"""
from __future__ import annotations

import os
import sys
import json
import glob
import random
import statistics

from scipy.stats import wilcoxon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import carregar_splits, carregar_particao, DIR_RESULTADOS  # noqa: E402
from src.eval.metrics import avaliar  # noqa: E402

NOMES = {
    "aleatoria": "Ordem do detector (sem ordenar)",
    "naive": "Ingênua (topo→base, esq.→dir.)",
    "xycut": "XY-cut (heurística de colunas)",
    "lstm_texto": "BiLSTM: só texto",
    "lstm_geo": "BiLSTM: só geometria",
    "lstm_geo_texto": "BiLSTM: texto + geometria",
    "layoutlm_sem_layout": "LayoutLM sem layout (ablação)",
    "layoutlm": "LayoutLM pontual: um escore por bloco",
    "layoutlm_sucessor": "LayoutLM sucessor: prevê o próximo bloco",
    "layoutlm_sucessor_feixe": "LayoutLM sucessor (decodificação em feixe)",
    "layoutlm_sucessor_n3235": "LayoutLM sucessor (3.235 páginas de treino)",
    "llm_llava_7b": "LLM llava:7b (zero-shot)",
}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def nome_llm(d):
    fs = d.get("few_shot") or 0
    return f"LLM {d['modelo']} ({f'few-shot, {fs} exemplos' if fs else 'zero-shot'})"


def percentil(v, q):
    s = sorted(v)
    return s[min(len(s) - 1, int(q * len(s)))]


def ic95(v, reamostras=2000):
    rng = random.Random(7)
    n = len(v)
    medias = sorted(sum(rng.choices(v, k=n)) / n for _ in range(reamostras))
    return medias[int(0.025 * reamostras)], medias[int(0.975 * reamostras)]


def resumir(regs):
    t = [r["kendall_tau"] for r in regs]
    out = {
        "n": len(regs),
        "tau": statistics.mean(t), "tau_ic95": ic95(t),
        "tau_mediana": statistics.median(t), "tau_p10": percentil(t, 0.10),
        "sucessor": statistics.mean(r["acerto_sucessor"] for r in regs),
        "ard": statistics.mean(r["ard"] for r in regs),
        "ard_norm": statistics.mean(r["ard_norm"] for r in regs),
        "bleu": statistics.mean(r["bleu"] for r in regs),
        "exato": statistics.mean(r["acerto_exato"] for r in regs),
        "tempo_ms": statistics.mean(r["tempo_ms"] for r in regs),
        "tempo_ms_mediana": statistics.median(r["tempo_ms"] for r in regs),
    }
    if any("permutacao_valida" in r for r in regs):
        out["prop_permutacao_valida"] = statistics.mean(1.0 if r.get("permutacao_valida") else 0.0 for r in regs)
    return out


def tabela(titulo, resumos, nota=""):
    linhas = [f"### {titulo}", ""]
    if nota:
        linhas += [nota, ""]
    linhas += ["| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD | ARD norm. | "
               "BLEU | Acerto exato | Latencia (ms/pag.) |",
               "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for m, r in resumos.items():
        a, b = r["tau_ic95"]
        tempo = f"{r['tempo_ms']:.3f}" if r["tempo_ms"] < 1 else f"{r['tempo_ms']:,.1f}"
        linhas.append(f"| {NOMES.get(m, m)} | {r['n']} | **{r['tau']:.3f}** ({a:.3f}-{b:.3f}) | "
                      f"{r['tau_p10']:.3f} | {r['sucessor']:.1%} | {r['ard']:.2f} | {r['ard_norm']:.3f} | "
                      f"{r['bleu']:.1f} | {r['exato']:.1%} | {tempo} |")
    return "\n".join(linhas) + "\n"


def main():
    splits = carregar_splits()
    ref = splits["referencia"]
    teste = {p["page_id"]: p for p in carregar_particao("teste")}
    por_metodo = {}
    for arq in sorted(glob.glob(os.path.join(DIR_RESULTADOS, "pred_*.jsonl"))):
        metodo = os.path.basename(arq)[len("pred_"):-len(".jsonl")]
        regs = []
        with open(arq, encoding="utf-8") as f:
            for linha in f:
                d = json.loads(linha)
                if metodo not in NOMES and d.get("modelo"):
                    NOMES[metodo] = nome_llm(d)
                p = teste.get(d["page_id"])
                if p is None:
                    continue
                textos = {c["id"]: c["text"] for c in p["bounding_boxes"]}
                r = avaliar(d["ordem_pred"], p["ordens"][ref], textos)
                r.update(metodo=metodo, page_id=d["page_id"], uf=p["uf"],
                         n_colunas=p["stats"]["n_colunas"], n_blocos=p["stats"]["n_blocos"],
                         tempo_ms=float(d.get("tempo_ms") or 0.0))
                if "permutacao_valida" in d:
                    r["permutacao_valida"] = d["permutacao_valida"]
                regs.append(r)
        if regs:
            por_metodo[metodo] = regs

    ordem = [m for m in NOMES if m in por_metodo] + [m for m in por_metodo if m not in NOMES]
    completos = [m for m in ordem if len(por_metodo[m]) >= 0.9 * len(teste)]
    parciais = [m for m in ordem if m not in completos]

    res_todas = {m: resumir(por_metodo[m]) for m in completos}

    res_subconj, ids_sub = {}, set()
    if parciais:
        ids_sub = set.intersection(*[{r["page_id"] for r in por_metodo[m]} for m in parciais])
        for m in ordem:
            regs = [r for r in por_metodo[m] if r["page_id"] in ids_sub]
            if regs:
                res_subconj[m] = resumir(regs)

    por_colunas = {}
    for m in completos:
        grupos = {}
        for r in por_metodo[m]:
            g = "1 coluna" if r["n_colunas"] <= 1 else ("2 colunas" if r["n_colunas"] == 2 else "3+ colunas")
            grupos.setdefault(g, []).append(r["kendall_tau"])
        por_colunas[m] = {g: {"n": len(v), "tau": statistics.mean(v)} for g, v in sorted(grupos.items())}

    def teste_pareado(a, b, ids=None):
        ta = {r["page_id"]: r["kendall_tau"] for r in por_metodo[a]}
        tb = {r["page_id"]: r["kendall_tau"] for r in por_metodo[b]}
        comuns = sorted(set(ta) & set(tb) & (ids if ids else set(ta)))
        x, y = [ta[i] for i in comuns], [tb[i] for i in comuns]
        try:
            p = float(wilcoxon(x, y).pvalue)
        except ValueError:
            p = 1.0
        return {"a": a, "b": b, "n": len(comuns), "media_a": statistics.mean(x),
                "media_b": statistics.mean(y), "p_valor": p}

    testes = []
    ref_modelo = "layoutlm" if "layoutlm" in por_metodo else None
    if ref_modelo:
        for m in completos:
            if m != ref_modelo:
                testes.append(teste_pareado(ref_modelo, m))
        for m in parciais:
            testes.append(teste_pareado(ref_modelo, m, ids_sub))
    if "xycut" in por_metodo:
        for m in completos:
            if m.startswith("llm_"):
                testes.append(teste_pareado("xycut", m))
        for m in parciais:
            testes.append(teste_pareado("xycut", m, ids_sub))

    saida = {"referencia": ref, "paginas_teste": len(teste), "ufs_teste": splits["teste"],
             "todas_as_paginas": res_todas, "subconjunto_llm": res_subconj,
             "n_subconjunto_llm": len(ids_sub), "por_colunas": por_colunas, "testes_wilcoxon": testes,
             "nomes": {m: NOMES.get(m, m) for m in ordem}}
    with open(os.path.join(DIR_RESULTADOS, "comparacao.json"), "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR_RESULTADOS, "metricas_por_pagina.jsonl"), "w", encoding="utf-8") as f:
        for m in ordem:
            for r in por_metodo[m]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    md = ["# Resultados da comparacao", "",
          f"Referencia: ordem `{ref}` (rotulo silver). Teste: {len(teste)} paginas de "
          f"{len(splits['teste'])} veiculos nunca vistos no treino: {', '.join(splits['teste'])}.", "",
          "Setas: tau e BLEU quanto maior melhor; ARD quanto menor melhor. "
          "tau p10 = percentil 10, o desempenho nas 10% piores paginas.", ""]
    md.append(tabela("Todas as paginas de teste", res_todas))
    if res_subconj:
        nota = (f"Subconjunto de {len(ids_sub)} paginas comum aos metodos avaliados em parte do teste "
                "(a LLM llava:7b rodou so em paginas pequenas). Todos os metodos nas MESMAS paginas.")
        md.append(tabela("Subconjunto avaliado pela LLM", res_subconj, nota))
    for m in ordem:
        r = res_todas.get(m) or res_subconj.get(m) or {}
        if "prop_permutacao_valida" in r:
            md.append(f"Permutacoes validas devolvidas por {NOMES.get(m, m)}: "
                      f"**{r['prop_permutacao_valida']:.0%}** (as invalidas foram reparadas antes de medir).\n")
    md += ["### Tau medio por numero de colunas da pagina", "",
           "| Metodo | " + " | ".join(sorted({g for v in por_colunas.values() for g in v})) + " |",
           "|---|" + "---:|" * len({g for v in por_colunas.values() for g in v})]
    grupos = sorted({g for v in por_colunas.values() for g in v})
    for m, v in por_colunas.items():
        md.append(f"| {NOMES.get(m, m)} | " + " | ".join(
            f"{v[g]['tau']:.3f} (n={v[g]['n']})" if g in v else "-" for g in grupos) + " |")
    md += ["", "### Testes de Wilcoxon pareados (tau por pagina)", "",
           "| A | B | n | media A | media B | p-valor |", "|---|---|---:|---:|---:|---:|"]
    for t in testes:
        md.append(f"| {NOMES.get(t['a'], t['a'])} | {NOMES.get(t['b'], t['b'])} | {t['n']} | "
                  f"{t['media_a']:.3f} | {t['media_b']:.3f} | {t['p_valor']:.2g} |")
    with open(os.path.join(DIR_RESULTADOS, "comparacao.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
