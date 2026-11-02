"""Regrava resultados/unidades_sem_caixas/treino_noite.json com o que está exportado agora (treino completo)."""
import datetime, glob, json, os, shutil
R = "resultados/unidades_sem_caixas"
sp = json.load(open("data/processed/splits.json", encoding="utf-8"))
if not os.path.exists(f"{R}/treino_noite_873.json"):
    shutil.copy(f"{R}/treino_noite.json", f"{R}/treino_noite_873.json")
out = {"descricao": "Treino completo exportado na noite de 06->07/10 (o conjunto de 873 paginas da noite anterior esta em treino_noite_873.json).",
       "limite_treino_pedido": 0, "elegiveis": 3217, "gerado_em": datetime.datetime.now().isoformat(timespec="seconds"), "por_representacao": {}}
for rep in ("linhas", "colunas", "colunas_margens"):
    ids, base, extra = set(), 0, 0
    for uf in sp["treino"]:
        f = f"{R}/{rep}/{uf}.jsonl"
        if os.path.exists(f):
            for l in open(f, encoding="utf-8"):
                ids.add(json.loads(l)["page_id"]); base += 1
    for f in glob.glob(f"{R}/{rep}_extra/*.jsonl"):
        if not f.endswith(".palavras.jsonl"):
            for l in open(f, encoding="utf-8"):
                ids.add(json.loads(l)["page_id"]); extra += 1
    out["por_representacao"][rep] = {"base": base, "extra": extra, "paginas_unicas": len(ids)}
p = f"{R}/treino_puladas.jsonl"
out["puladas"] = sorted({json.loads(l)["page_id"] for l in open(p, encoding="utf-8")}) if os.path.exists(p) else []
json.dump(out, open(f"{R}/treino_noite.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v["paginas_unicas"] for k, v in out["por_representacao"].items()}, len(out["puladas"]))
