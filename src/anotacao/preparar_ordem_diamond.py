"""
Monta um lote de ORDEM DE LEITURA (Golden) sobre as regioes corrigidas a mao no Diamond.

Os lotes golden_v1..v3 ordenam os blocos do extrator v3, com os erros de segmentacao dele. Aqui os blocos
sao as regioes que o anotador conferiu no Diamond (caixa e classe), entao a ordem anotada e a medida dos
metodos deixam de depender dos erros do extrator. As regras de leitura estao em
docs/GUIA_ORDEM_LEITURA.md, as mesmas que o ordenador por VLM recebe (src/eval/vlm_ordem.py).

Para cada pagina CONCLUIDA por humano nos lotes do Diamond, grava em data/golden/<lote>/:
  tarefas.jsonl   no formato de sempre (bounding_boxes com id, text, bbox; ordens stream, naive, xycut;
                  stats), mais "classe" em cada bloco e "diamond" com a proveniencia
  img/NNN.jpg     a imagem da pagina, copiada do lote do Diamond

Regioes sem nenhuma palavra (brasao, foto) ficam de fora: nao ha texto a ordenar, e todos os metodos
recebem os mesmos blocos. Cada palavra entra em uma regiao so (a menor que nao e figura). Os ids sao uma
permutacao semeada pelo page_id, como no extrator: nao carregam ordem.

Rodar de novo com o mesmo --lote acrescenta as paginas novas; anotacao existente nao e tocada.

Uso:
    python src/anotacao/preparar_ordem_diamond.py --lote golden_v4 --diamond diamond_piloto diamond_treino
"""
from __future__ import annotations

import os
import re
import sys
import json
import random
import shutil
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.extrator import xycut, estimar_colunas, RAIZ_PROJETO  # noqa: E402

DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
DIR_DIAMOND = os.path.join(RAIZ_PROJETO, "data", "diamond")
RE_ALFANUM = re.compile(r"[0-9A-Za-zÀ-ÿ]")


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def blocos_da_pagina(tarefa, regioes):
    """Regioes humanas -> blocos com texto (palavras por linha) e indice de fluxo da 1a palavra."""
    palavras = tarefa["palavras"]

    def area(r):
        return (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])

    dono = {}
    for k, w in enumerate(palavras):
        cx, cy = (w[1] + w[3]) / 2, (w[2] + w[4]) / 2
        dentro = [r for r in regioes if r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3]]
        if dentro:
            nao_figura = [r for r in dentro if r["classe"] != "figura"] or dentro
            dono[k] = min(nao_figura, key=area)["id"]
    blocos = []
    for r in regioes:
        ks = [k for k, rid in dono.items() if rid == r["id"]]
        if not any(RE_ALFANUM.search(palavras[k][0]) for k in ks):
            continue
        linhas = []
        for k in sorted(ks, key=lambda k: (palavras[k][2] + palavras[k][4]) / 2):
            w = palavras[k]
            cy, h = (w[2] + w[4]) / 2, w[4] - w[2]
            if linhas and abs(cy - linhas[-1]["cy"]) < 0.5 * max(h, linhas[-1]["h"]):
                linhas[-1]["ks"].append(k)
            else:
                linhas.append({"cy": cy, "h": h, "ks": [k]})
        texto = " ".join(" ".join(palavras[k][0] for k in sorted(L["ks"], key=lambda k: palavras[k][1]))
                         for L in linhas)
        x0, y0, x1, y1 = r["bbox"]
        blocos.append({"regiao": r["id"], "classe": r["classe"], "texto": texto, "s": min(ks),
                       "x0": x0, "top": y0, "x1": x1, "bottom": y1})
    return blocos


def montar(tarefa, anotacao, lote_diamond, n, nome_img):
    blocos = blocos_da_pagina(tarefa, anotacao["regioes"])
    if len(blocos) < 2:
        return None
    rng = random.Random(tarefa["page_id"])
    perm = list(range(len(blocos)))
    rng.shuffle(perm)
    ids = [f"b{perm[k]}" for k in range(len(blocos))]
    idx = list(range(len(blocos)))
    caixas = []
    for i in idx:
        B = blocos[i]
        c = {"id": ids[i], "text": B["texto"], "bbox": [round(B["x0"], 1), round(B["top"], 1),
                                                      round(B["x1"], 1), round(B["bottom"], 1)],
             "classe": B["classe"]}
        if B["classe"] == "tabela":
            c["tipo"] = "tabela"
        caixas.append(c)
    caixas.sort(key=lambda c: int(c["id"][1:]))
    return {
        "n": n, "page_id": tarefa["page_id"], "grupo": tarefa.get("grupo") or lote_diamond,
        "origem": lote_diamond, "uf": tarefa["uf"], "arquivo": tarefa["arquivo"], "pagina": tarefa["pagina"],
        "dimensions": tarefa["dimensions"], "imagem": nome_img,
        **({"origem_pagina": tarefa["origem_pagina"]} if tarefa.get("origem_pagina") else {}),
        "bounding_boxes": caixas,
        "ordens": {"stream": [ids[i] for i in sorted(idx, key=lambda i: blocos[i]["s"])],
                   "naive": [ids[i] for i in sorted(idx, key=lambda i: (blocos[i]["top"], blocos[i]["x0"]))],
                   "xycut": [ids[i] for i in xycut(idx, blocos)]},
        "stats": {"n_blocos": len(blocos), "n_colunas": estimar_colunas(blocos),
                  "n_tabelas": sum(1 for B in blocos if B["classe"] == "tabela"), "layout": True,
                  "segmentacao": "diamond"},
        "diamond": {"lote": lote_diamond, "anotador": anotacao["anotador"], "salvo_em": anotacao["salvo_em"],
                    "regioes_sem_texto": len(anotacao["regioes"]) - len(blocos)},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True)
    ap.add_argument("--diamond", nargs="+", required=True, help="lotes do Diamond de onde vem as paginas")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.lote):
        sys.exit("[ERRO] nome de lote: use so letras, numeros, _ ou -")
    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    os.makedirs(os.path.join(dir_lote, "img"), exist_ok=True)
    arq = os.path.join(dir_lote, "tarefas.jsonl")
    existentes = ler_jsonl(arq)
    ja = {t["page_id"] for t in existentes}
    novas = []
    for lote in a.diamond:
        tarefas = {t["page_id"]: t for t in ler_jsonl(os.path.join(DIR_DIAMOND, lote, "tarefas.jsonl"))}
        humanas = [x for x in ler_jsonl(os.path.join(DIR_DIAMOND, lote, "anotacoes.jsonl"))
                   if x["status"] == "concluida" and not x["anotador"].startswith("VLM:")]
        for an in sorted(humanas, key=lambda x: tarefas[x["page_id"]].get("n", 0)):
            if an["page_id"] in ja or an["page_id"] not in tarefas:
                continue
            ja.add(an["page_id"])
            novas.append((lote, tarefas[an["page_id"]], an))
    gravadas = 0
    with open(arq, "a", encoding="utf-8") as f:
        for lote, t, an in novas:
            n = len(existentes) + gravadas + 1
            nome_img = f"{n:03d}.jpg"
            reg = montar(t, an, lote, n, nome_img)
            if reg is None:
                print(f"  [!] menos de 2 regioes com texto, fica de fora: {t['page_id']}")
                continue
            shutil.copyfile(os.path.join(DIR_DIAMOND, lote, "img", t["imagem"]), os.path.join(dir_lote, "img", nome_img))
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            gravadas += 1
    print(f"[OK] {gravadas} paginas novas em data/golden/{a.lote} ({len(existentes) + gravadas} no total)")
    print("     Para ordenar: venv\\Scripts\\python.exe src\\anotacao\\servidor.py  (lote " + a.lote + ")")


if __name__ == "__main__":
    main()
