"""
Avalia os metodos contra a anotacao HUMANA (Golden Dataset).

Le data/golden/<lote>/tarefas.jsonl e anotacoes.jsonl (so paginas concluidas) e mede,
contra a ordem humana. --lote tambem aceita um conjunto de avaliacao montado por
src/anotacao/montar_referencia.py (ex.: _avaliacao/golden_v3), que traz referencia.jsonl no
lugar de anotacoes.jsonl e junta paginas anotadas direto na segmentacao atual com paginas de
lotes anteriores projetadas para ela:
  fluxo do PDF   a referencia automatica (silver) usada em todos os resultados ate aqui.
                 No grupo 'silver', o tau dela contra o humano diz se os resultados
                 preliminares se sustentam.
  ingenua, XY-cut, ordem do detector (piso)
  LayoutLM       rodado agora na GPU com o(s) checkpoint(s) treinado(s)
  LLMs           resultados/golden/<lote>/pred_*.jsonl (ex.: gerados no Kaggle)

Com mais de um anotador na mesma pagina, reporta a concordancia entre anotadores
(tau de Kendall), que e o teto realista de qualquer metodo. Tambem reporta o custo
da anotacao (tempo ativo por pagina).

Grava resultados/golden/<lote>/avaliacao.md e .json.

Uso:
    python src/eval/avaliar_golden.py --lote golden_v1
    python src/eval/avaliar_golden.py --lote _avaliacao/golden_v3 --layoutlm --sucessor
    python src/eval/avaliar_golden.py --lote golden_v1 --anotador Pedro --layoutlm layoutlm curva_n2400
"""
from __future__ import annotations

import os
import sys
import glob
import json
import random
import argparse
import statistics
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import ordem_entrada, DIR_RESULTADOS, RAIZ_PROJETO  # noqa: E402
from src.eval.metrics import avaliar, kendall_tau  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
NOMES = {
    "fluxo_pdf": "Fluxo do PDF (referência silver)",
    "aleatoria": "Ordem do detector (sem ordenar)",
    "naive": "Ingênua (topo→base, esq.→dir.)",
    "xycut": "XY-cut (heurística de colunas)",
    "layoutlm": "LayoutLM pontual: um escore por bloco",
    "layoutlm_sucessor": "LayoutLM sucessor: prevê o próximo bloco",
}


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def ic95(v, reamostras=2000):
    if len(v) < 2:
        return (v[0], v[0]) if v else (0.0, 0.0)
    rng = random.Random(7)
    medias = sorted(sum(rng.choices(v, k=len(v))) / len(v) for _ in range(reamostras))
    return medias[int(0.025 * reamostras)], medias[int(0.975 * reamostras)]


def resumir(regs):
    t = [r["kendall_tau"] for r in regs]
    s = sorted(t)
    return {"n": len(t), "tau": statistics.mean(t), "tau_ic95": ic95(t), "tau_p10": s[int(0.1 * len(s))],
            "sucessor": statistics.mean(r["acerto_sucessor"] for r in regs),
            "ard_norm": statistics.mean(r["ard_norm"] for r in regs),
            "exato": statistics.mean(r["acerto_exato"] for r in regs)}


def prever_layoutlm(paginas, nome, sucessor=False):
    """Roda um checkpoint do LayoutLM nas paginas anotadas. sucessor=True usa a
    formulacao de predicao de sucessor (src/models/layoutlm_sucessor.py)."""
    import torch
    from src.models.layoutlm_ordem import Codificador, MODELO_BASE, DIR_MODELOS
    ckpt = os.path.join(DIR_MODELOS, f"{nome}.pt")
    if not torch.cuda.is_available() or not os.path.exists(ckpt):
        print(f"[!] {nome}: {'sem GPU CUDA' if os.path.exists(ckpt) else 'checkpoint nao encontrado'}; ignorado")
        return None
    from transformers import AutoTokenizer
    cod = Codificador(AutoTokenizer.from_pretrained(MODELO_BASE))
    if sucessor:
        from src.models.layoutlm_sucessor import LayoutLMSucessor, prever
        modelo = LayoutLMSucessor(usar_layout="sem_layout" not in nome,
                                  usar_vies_geo="sem_vies_geo" not in nome).to("cuda")
    else:
        from src.models.layoutlm_ordem import LayoutLMOrdem, prever
        modelo = LayoutLMOrdem(MODELO_BASE, usar_layout="sem_layout" not in nome).to("cuda")
    modelo.load_state_dict(torch.load(ckpt, map_location="cuda"))
    cod.pretokenizar(paginas)
    preds = prever(modelo, cod, paginas, "cuda")
    for p in paginas:
        for c in p["bounding_boxes"]:
            c.pop("_tok", None)
    return {p["page_id"]: pr for p, (pr, _) in zip(paginas, preds)}


def tabela(resumos):
    linhas = ["| Metodo | n | tau Kendall (IC 95%) | tau pior caso (p10) | Sucessor correto | ARD norm. | Acerto exato |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for m, r in resumos.items():
        a, b = r["tau_ic95"]
        linhas.append(f"| {NOMES.get(m, m)} | {r['n']} | **{r['tau']:.3f}** ({a:.3f}-{b:.3f}) | "
                      f"{r['tau_p10']:.3f} | {r['sucessor']:.0%} | {r['ard_norm']:.3f} | {r['exato']:.0%} |")
    return linhas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True)
    ap.add_argument("--anotador", help="anotador de referencia (padrao: quem concluiu mais paginas)")
    ap.add_argument("--layoutlm", nargs="*", default=["layoutlm"],
                    help="checkpoints PONTUAIS em models/layoutlm_ordem/")
    ap.add_argument("--sucessor", nargs="*", default=["layoutlm_sucessor"],
                    help="checkpoints da formulacao de SUCESSOR em models/layoutlm_ordem/")
    a = ap.parse_args()

    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    tarefas = {t["page_id"]: t for t in ler_jsonl(os.path.join(dir_lote, "tarefas.jsonl"))}
    # conjunto de avaliacao (montar_referencia.py) traz referencia.jsonl; lote comum, anotacoes.jsonl
    arq_ref = os.path.join(dir_lote, "referencia.jsonl")
    if not os.path.exists(arq_ref):
        arq_ref = os.path.join(dir_lote, "anotacoes.jsonl")
    anot = [x for x in ler_jsonl(arq_ref) if x["status"] == "concluida"]
    puladas = [x for x in ler_jsonl(arq_ref) if x["status"] == "pulada"]
    if not tarefas:
        sys.exit(f"[ERRO] lote '{a.lote}' nao encontrado em {DIR_GOLDEN}")
    if not anot:
        print(f"Nenhuma pagina concluida ainda no lote '{a.lote}' ({len(tarefas)} paginas). "
              "Anote na ferramenta (src/anotacao/servidor.py) e rode de novo.")
        return

    contagem = Counter(x["anotador"] for x in anot)
    principal = a.anotador or contagem.most_common(1)[0][0]
    humano = {x["page_id"]: x for x in anot if x["anotador"] == principal}
    paginas = [tarefas[pid] for pid in humano if pid in tarefas]

    preds = {"fluxo_pdf": {p["page_id"]: p["ordens"]["stream"] for p in paginas},
             "aleatoria": {p["page_id"]: [p["bounding_boxes"][i]["id"] for i in ordem_entrada(p)] for p in paginas},
             "naive": {p["page_id"]: p["ordens"]["naive"] for p in paginas},
             "xycut": {p["page_id"]: p["ordens"]["xycut"] for p in paginas}}
    dir_pred = os.path.join(DIR_RESULTADOS, "golden", a.lote)
    os.makedirs(dir_pred, exist_ok=True)
    for nome, suc in [(n, False) for n in a.layoutlm] + [(n, True) for n in a.sucessor]:
        r = prever_layoutlm(paginas, nome, sucessor=suc)
        if r:
            preds[nome] = r
            # grava as predicoes: uma avaliacao posterior (ex.: no projeto, depois de importar do
            # Kaggle) reaproveita sem precisar do checkpoint de 450 MB
            with open(os.path.join(dir_pred, f"pred_{nome}.jsonl"), "w", encoding="utf-8") as f:
                for pid, ordem in r.items():
                    f.write(json.dumps({"page_id": pid, "ordem_pred": ordem}, ensure_ascii=False) + "\n")
    for arq in sorted(glob.glob(os.path.join(dir_pred, "pred_*.jsonl"))):
        metodo = os.path.basename(arq)[5:-6]
        if metodo in preds:          # acabou de ser calculado com o checkpoint
            continue
        linhas = ler_jsonl(arq)
        if linhas and linhas[0].get("modelo"):
            fs = linhas[0].get("few_shot") or 0
            NOMES[metodo] = f"LLM {linhas[0]['modelo']} ({f'few-shot, {fs} exemplos' if fs else 'zero-shot'})"
        preds[metodo] = {l["page_id"]: l["ordem_pred"] for l in linhas}

    regs = {m: [] for m in preds}
    for p in paginas:
        ref = humano[p["page_id"]]["ordem"]
        textos = {c["id"]: c["text"] for c in p["bounding_boxes"]}
        for m, d in preds.items():
            if p["page_id"] in d:
                r = avaliar(d[p["page_id"]], ref, textos)
                r.update(page_id=p["page_id"], grupo=p["grupo"], uf=p["uf"],
                         origem=humano[p["page_id"]].get("origem", a.lote))
                regs[m].append(r)
    regs = {m: v for m, v in regs.items() if v}
    grupos = sorted({p["grupo"] for p in paginas})
    geral = {m: resumir(v) for m, v in regs.items()}
    por_grupo = {g: {m: resumir([r for r in v if r["grupo"] == g]) for m, v in regs.items()
                     if any(r["grupo"] == g for r in v)} for g in grupos}
    origens = sorted({humano[p["page_id"]].get("origem", a.lote) for p in paginas})
    por_origem = {o: {m: resumir([r for r in v if r["origem"] == o]) for m, v in regs.items()
                      if any(r["origem"] == o for r in v)} for o in origens} if len(origens) > 1 else {}

    testes = []
    try:
        from scipy.stats import wilcoxon
        tx = {r["page_id"]: r["kendall_tau"] for r in regs["xycut"]}
        for m, v in regs.items():
            if m == "xycut":
                continue
            tm = {r["page_id"]: r["kendall_tau"] for r in v}
            comuns = sorted(set(tx) & set(tm))
            if len(comuns) >= 6:
                try:
                    pv = float(wilcoxon([tx[i] for i in comuns], [tm[i] for i in comuns]).pvalue)
                except ValueError:
                    pv = 1.0
                testes.append({"a": "xycut", "b": m, "n": len(comuns), "p_valor": pv})
    except ImportError:
        pass

    concordancia = []
    por_pagina = {}
    for x in anot:
        por_pagina.setdefault(x["page_id"], []).append(x)
    for pid, xs in por_pagina.items():
        if len(xs) >= 2:
            xs = sorted(xs, key=lambda x: x["anotador"] != principal)
            for outro in xs[1:]:
                concordancia.append({"page_id": pid, "anotadores": [xs[0]["anotador"], outro["anotador"]],
                                     "tau": kendall_tau(outro["ordem"], xs[0]["ordem"])})

    tempos = [humano[p["page_id"]]["tempo_s"] for p in paginas]
    blocos = [len(p["bounding_boxes"]) for p in paginas]
    custo = {"paginas": len(paginas), "puladas": len(puladas), "minutos_total": sum(tempos) / 60,
             "segundos_por_pagina": statistics.mean(tempos), "segundos_por_bloco": sum(tempos) / max(1, sum(blocos))}

    md = [f"# Avaliação contra anotação humana: lote `{a.lote}`", "",
          f"Referência: ordem anotada por **{principal}** em {len(paginas)} de {len(tarefas)} páginas "
          f"({len(puladas)} puladas). Grupos: {', '.join(grupos)}.", "",
          "## Todas as páginas anotadas", ""] + tabela(geral)
    for g in grupos:
        md += ["", f"## Grupo `{g}`", ""] + tabela(por_grupo[g])
    for o in por_origem:
        md += ["", f"## Referência vinda de `{o}`", ""] + tabela(por_origem[o])
    if "fluxo_pdf" in geral:
        md += ["", "## A referência automática se sustenta?", ""]
        for g in grupos:
            r = por_grupo[g].get("fluxo_pdf")
            if r:
                md.append(f"- Grupo `{g}`: o fluxo do PDF concorda com o humano com tau médio **{r['tau']:.3f}** "
                          f"(pior caso p10 {r['tau_p10']:.3f}, {r['exato']:.0%} das páginas idênticas).")
    if testes:
        md += ["", "## Wilcoxon pareado contra a XY-cut", "", "| A | B | n | p-valor |", "|---|---|---:|---:|"]
        md += [f"| {NOMES.get(t['a'], t['a'])} | {NOMES.get(t['b'], t['b'])} | {t['n']} | {t['p_valor']:.2g} |"
               for t in testes]
    if concordancia:
        md += ["", "## Concordância entre anotadores", "",
               f"{len(concordancia)} páginas com dois anotadores: tau médio "
               f"**{statistics.mean(c['tau'] for c in concordancia):.3f}** "
               f"(mínimo {min(c['tau'] for c in concordancia):.3f}). É o teto realista de qualquer método."]
    md += ["", "## Custo da anotação", "",
           f"{custo['minutos_total']:.0f} min de trabalho ativo: {custo['segundos_por_pagina']:.0f} s por página, "
           f"{custo['segundos_por_bloco']:.1f} s por bloco."]

    os.makedirs(dir_pred, exist_ok=True)
    with open(os.path.join(dir_pred, "avaliacao.json"), "w", encoding="utf-8") as f:
        json.dump({"lote": a.lote, "anotador_referencia": principal, "geral": geral, "por_grupo": por_grupo,
                   "por_origem": por_origem,
                   "wilcoxon_vs_xycut": testes, "concordancia": concordancia, "custo": custo,
                   "nomes": {m: NOMES.get(m, m) for m in geral}}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(dir_pred, "avaliacao.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
