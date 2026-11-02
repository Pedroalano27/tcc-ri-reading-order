import os
import sys
import json
import statistics

sys.path.insert(0, os.path.abspath("."))
from src.data.extrator import xycut
from src.eval.metrics import kendall_tau, acerto_sucessor, ard_normalizado, acerto_exato
from src.eval.protocolo import carregar_splits, iterar_paginas

def avaliar_lista(preds, gts):
    taus = [kendall_tau(p, g) for p, g in zip(preds, gts)]
    sucs = [acerto_sucessor(p, g) for p, g in zip(preds, gts)]
    ards = [ard_normalizado(p, g) for p, g in zip(preds, gts)]
    exatos = [acerto_exato(p, g) for p, g in zip(preds, gts)]
    s = sorted(taus)
    p10 = s[int(0.1 * len(s))]
    return {
        "n": len(taus),
        "tau": statistics.mean(taus),
        "tau_p10": p10,
        "sucessor": statistics.mean(sucs),
        "ard_norm": statistics.mean(ards),
        "exato": statistics.mean(exatos)
    }

# 1. Golden_v3 (_avaliacao/golden_v3 - anotacao humana Pedro Alano)
ref_file_v3 = "data/golden/_avaliacao/golden_v3/referencia.jsonl"
tar_file_v3 = "data/golden/_avaliacao/golden_v3/tarefas.jsonl"
tarefas_v3 = {json.loads(l)["page_id"]: json.loads(l) for l in open(tar_file_v3, encoding="utf-8") if l.strip()}
refs_v3 = [json.loads(l) for l in open(ref_file_v3, encoding="utf-8") if l.strip() and json.loads(l).get("status") == "concluida"]

preds_gv3, gts_gv3 = [], []
for r in refs_v3:
    pid = r["page_id"]
    if pid not in tarefas_v3:
        continue
    t = tarefas_v3[pid]
    ids = [c["id"] for c in t["bounding_boxes"]]
    B = [{"x0": c["bbox"][0], "top": c["bbox"][1], "x1": c["bbox"][2], "bottom": c["bbox"][3]} for c in t["bounding_boxes"]]
    pred_idx = xycut(list(range(len(ids))), B)
    preds_gv3.append([ids[i] for i in pred_idx])
    gts_gv3.append(r["ordem"])

res_gv3 = avaliar_lista(preds_gv3, gts_gv3)
print("=== 1. GOLDEN V3 (47 pags anotadas Pedro Alano) ===")
print(f"n={res_gv3['n']}, tau={res_gv3['tau']:.3f}, p10={res_gv3['tau_p10']:.3f}, suc={res_gv3['sucessor']*100:.1f}%, ardn={res_gv3['ard_norm']:.3f}, exato={res_gv3['exato']*100:.1f}%")

# 2. Golden_v4 (golden_v4 - anotacao humana Pedro Alano)
ref_file_v4 = "data/golden/golden_v4/anotacoes.jsonl"
tar_file_v4 = "data/golden/golden_v4/tarefas.jsonl"
tarefas_v4 = {json.loads(l)["page_id"]: json.loads(l) for l in open(tar_file_v4, encoding="utf-8") if l.strip()}
refs_v4 = [json.loads(l) for l in open(ref_file_v4, encoding="utf-8") if l.strip() and json.loads(l).get("status") == "concluida"]

preds_gv4, gts_gv4 = [], []
for r in refs_v4:
    pid = r["page_id"]
    if pid not in tarefas_v4:
        continue
    t = tarefas_v4[pid]
    ids = [c["id"] for c in t["bounding_boxes"]]
    B = [{"x0": c["bbox"][0], "top": c["bbox"][1], "x1": c["bbox"][2], "bottom": c["bbox"][3]} for c in t["bounding_boxes"]]
    pred_idx = xycut(list(range(len(ids))), B)
    preds_gv4.append([ids[i] for i in pred_idx])
    gts_gv4.append(r["ordem"])

res_gv4 = avaliar_lista(preds_gv4, gts_gv4)
print("=== 2. GOLDEN V4 (44 pags anotadas Pedro Alano) ===")
print(f"n={res_gv4['n']}, tau={res_gv4['tau']:.3f}, p10={res_gv4['tau_p10']:.3f}, suc={res_gv4['sucessor']*100:.1f}%, ardn={res_gv4['ard_norm']:.3f}, exato={res_gv4['exato']*100:.1f}%")

# 3. Teste v1 (95 pags - segmentacao v1 original em RESULTADOS_PRELIMINARES.md)
splits = carregar_splits()
teste_ufs = splits["teste"]
paginas_v1 = list(iterar_paginas(teste_ufs, dir_blocos="data/processed/blocos_v1"))
preds_v1, gts_v1 = [], []
for p in paginas_v1:
    ids = [c["id"] for c in p["bounding_boxes"]]
    B = [{"x0": c["bbox"][0], "top": c["bbox"][1], "x1": c["bbox"][2], "bottom": c["bbox"][3]} for c in p["bounding_boxes"]]
    pred_idx = xycut(list(range(len(ids))), B)
    preds_v1.append([ids[i] for i in pred_idx])
    gts_v1.append(p["ordens"]["stream"])

res_v1 = avaliar_lista(preds_v1, gts_v1)
print("=== 3. TESTE V1 (95 pags - RESULTADOS_PRELIMINARES.md) ===")
print(f"n={res_v1['n']}, tau={res_v1['tau']:.3f}, p10={res_v1['tau_p10']:.3f}, suc={res_v1['sucessor']*100:.1f}%, ardn={res_v1['ard_norm']:.3f}, exato={res_v1['exato']*100:.1f}%")

# 4. Teste v3 (89 pags - segmentacao v3 atual em resultados/comparacao.md)
paginas_v3 = list(iterar_paginas(teste_ufs, dir_blocos="data/processed/blocos"))
preds_v3, gts_v3 = [], []
for p in paginas_v3:
    ids = [c["id"] for c in p["bounding_boxes"]]
    B = [{"x0": c["bbox"][0], "top": c["bbox"][1], "x1": c["bbox"][2], "bottom": c["bbox"][3]} for c in p["bounding_boxes"]]
    pred_idx = xycut(list(range(len(ids))), B)
    preds_v3.append([ids[i] for i in pred_idx])
    gts_v3.append(p["ordens"]["stream"])

res_v3 = avaliar_lista(preds_v3, gts_v3)
print("=== 4. TESTE V3 (89 pags - resultados/comparacao.md) ===")
print(f"n={res_v3['n']}, tau={res_v3['tau']:.3f}, p10={res_v3['tau_p10']:.3f}, suc={res_v3['sucessor']*100:.1f}%, ardn={res_v3['ard_norm']:.3f}, exato={res_v3['exato']*100:.1f}%")
