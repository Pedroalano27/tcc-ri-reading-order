"""
Monta o conjunto de AVALIACAO do Golden numa segmentacao: tarefas + ordem de referencia.

A anotacao humana esta espalhada em lotes feitos sobre segmentacoes diferentes. Para avaliar
os metodos numa segmentacao so, junta-se:
  --projetada LOTE:ROTULO  paginas "limpas" da projecao derivados/projecao_<ROTULO>.jsonl
                           (src/anotacao/projetar_ordem.py): blocos da segmentacao atual e a ordem
                           do anotador levada para eles;
  --lote LOTE              um lote anotado diretamente na segmentacao atual (paginas concluidas;
                           as puladas entram so na contagem).

Grava em data/golden/_avaliacao/<nome>/ (fora do alcance da ferramenta de anotacao, que so lista
data/golden/*/):
  tarefas.jsonl     blocos das paginas, no formato dos lotes, com "origem"
  referencia.jsonl  uma linha por pagina: {"page_id", "status", "anotador", "ordem", "origem", "flags",
                    "nota", "tempo_s"}. E DERIVADO: regenere com este script, nunca edite a mao.
                    A anotacao humana continua so em data/golden/<lote>/anotacoes.jsonl.
  LEIAME.md

Confere que tarefas e projecoes foram geradas pelo extrator atual (sha256 de src/data/extrator.py):
referencia de uma segmentacao velha avaliaria os metodos contra blocos que eles nao recebem.

Uso:
    python src/anotacao/montar_referencia.py --nome golden_v3 --projetada golden_v1:v3 --lote golden_v2
"""
from __future__ import annotations

import os
import sys
import json
import hashlib
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import RAIZ_PROJETO  # noqa: E402

DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
EXTRATOR = os.path.join(RAIZ_PROJETO, "src", "data", "extrator.py")


def ler_jsonl(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nome", required=True, help="nome do conjunto, ex.: golden_v3")
    ap.add_argument("--projetada", action="append", default=[], metavar="LOTE:ROTULO")
    ap.add_argument("--lote", action="append", default=[])
    ap.add_argument("--anotador", help="so registros deste anotador (padrao: todos os concluidos)")
    a = ap.parse_args()
    with open(EXTRATOR, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    tarefas, referencia, contagem, problemas = [], [], Counter(), []
    vistos = set()

    def aceitar(t, r):
        if t["page_id"] in vistos:
            problemas.append(f"pagina repetida entre as fontes: {t['page_id']}")
            return
        vistos.add(t["page_id"])
        tarefas.append(t)
        referencia.append(r)

    for spec in a.projetada:
        lote, _, rotulo = spec.partition(":")
        arq = os.path.join(DIR_GOLDEN, lote, "derivados", f"projecao_{rotulo}.jsonl")
        for p in ler_jsonl(arq):
            contagem[f"{lote} ({rotulo}): {p['status']}"] += 1
            if p["status"] != "limpa":
                continue
            if p["extrator_sha256"] != sha:
                problemas.append(f"projecao feita com outro extrator: {p['page_id']} ({arq})")
                continue
            if a.anotador and p["anotador"] != a.anotador:
                continue
            original = {x["page_id"]: x for x in ler_jsonl(os.path.join(DIR_GOLDEN, lote, "anotacoes.jsonl"))
                        if x["status"] == "concluida"}.get(p["page_id"], {})
            origem = f"{lote} projetada ({rotulo})"
            aceitar({**p["tarefa"], "origem": origem},
                    {"page_id": p["page_id"], "status": "concluida", "anotador": p["anotador"],
                     "ordem": p["ordem"], "origem": origem, "flags": original.get("flags", []),
                     "nota": original.get("nota", ""), "tempo_s": original.get("tempo_s", 0.0)})

    for lote in a.lote:
        dir_lote = os.path.join(DIR_GOLDEN, lote)
        congeladas = {x["page_id"]: x for x in ler_jsonl(os.path.join(dir_lote, "derivados", "palavras_por_bloco.jsonl"))}
        por_pid = {t["page_id"]: t for t in ler_jsonl(os.path.join(dir_lote, "tarefas.jsonl"))}
        for x in ler_jsonl(os.path.join(dir_lote, "anotacoes.jsonl")):
            contagem[f"{lote}: {x['status']}"] += 1
            if x["status"] != "concluida" or (a.anotador and x["anotador"] != a.anotador):
                continue
            t = por_pid[x["page_id"]]
            if congeladas.get(x["page_id"], {}).get("extrator_sha256") != sha:
                problemas.append(f"lote gerado com outro extrator: {x['page_id']} ({lote})")
                continue
            if sorted(x["ordem"]) != sorted(c["id"] for c in t["bounding_boxes"]):
                problemas.append(f"anotacao incompleta ou com ids estranhos: {x['page_id']} ({lote})")
                continue
            aceitar({**t, "origem": lote},
                    {"page_id": x["page_id"], "status": "concluida", "anotador": x["anotador"],
                     "ordem": x["ordem"], "origem": lote, "flags": x.get("flags", []),
                     "nota": x.get("nota", ""), "tempo_s": x.get("tempo_s", 0.0)})

    for k, v in sorted(contagem.items()):
        print(f"  {k}: {v}")
    if problemas:
        print(f"[ERRO] {len(problemas)} problemas; nada foi gravado:")
        for p in problemas[:20]:
            print("   ", p)
        sys.exit(1)

    destino = os.path.join(DIR_GOLDEN, "_avaliacao", a.nome)
    os.makedirs(destino, exist_ok=True)
    for nome, linhas in (("tarefas.jsonl", tarefas), ("referencia.jsonl", referencia)):
        with open(os.path.join(destino, nome), "w", encoding="utf-8") as f:
            for l in linhas:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
    grupos = Counter(t["grupo"] for t in tarefas)
    origens = Counter(r["origem"] for r in referencia)
    blocos = sum(len(t["bounding_boxes"]) for t in tarefas)
    with open(os.path.join(destino, "LEIAME.md"), "w", encoding="utf-8") as f:
        f.write(f"""# Conjunto de avaliacao `{a.nome}` (DERIVADO — nao editar)

Gerado por `src/anotacao/montar_referencia.py` com:
`--nome {a.nome} {' '.join('--projetada ' + s for s in a.projetada)} {' '.join('--lote ' + s for s in a.lote)}`

- {len(tarefas)} paginas, {blocos} blocos; grupos: {dict(grupos)}
- origem da ordem: {dict(origens)}
- extrator: `{sha[:12]}`

`referencia.jsonl` junta a anotacao humana feita direto nesta segmentacao e a anotacao de lotes
anteriores levada para ela por projecao (so paginas em que a ordem dos blocos novos e exatamente a
do anotador). A anotacao original fica em `data/golden/<lote>/anotacoes.jsonl`.
""")
    print(f"[OK] {len(tarefas)} paginas ({blocos} blocos), grupos {dict(grupos)}, origens {dict(origens)} -> "
          f"{os.path.relpath(destino, RAIZ_PROJETO)}")


if __name__ == "__main__":
    main()
