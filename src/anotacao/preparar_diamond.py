"""
Prepara um lote do DIAMOND: paginas em que o Pedro corrige as CAIXAS e as CLASSES das regioes.

O Golden anota a ordem de blocos que o extrator entrega; o Diamond anota a propria segmentacao,
para medir e treinar o extrator. Cada pagina chega com uma PROPOSTA (pre-anotacao) que o anotador
so corrige, e com alertas que apontam onde a proposta e suspeita.

Para cada pagina grava, em data/diamond/<lote>/:
  tarefas.jsonl   uma linha por pagina:
                    palavras   todas as palavras da camada de texto do PDF (extrator.palavras_da_pagina),
                               [texto, x0, top, x1, bottom, bloco v3 ou -1]
                    blocos_v3  a segmentacao atual (extrator.segmentar com as tabelas do detector)
                    detector   as regioes do Docling Heron com score >= SCORE_MIN, do cache de layout
                    proposta   as regioes propostas, com classe, origem e alertas
  img/NNN.jpg     a pagina renderizada (--resolucao dpi)

A proposta e a segmentacao por regioes de src/data/regioes.py (detector + palavras + blocos v3), com
as regras tiradas do diamond_piloto (proposta_versao "v2"); --sem-regras reproduz a do piloto ("v1").
Alertas da proposta: baixa_confianca (score < 0,55), so_regras, juntou_sobrepostas, atravessa_colunas.
A ferramenta recalcula sobreposicao, palavras sem caixa e os alertas de regra a cada edicao.

Paginas: --de-lote pega as de um lote do Golden; --colecao sorteia das colecoes de blocos (rodizio
entre veiculos, semente fixa), fora dos veiculos de TESTE (guardados para avaliar o segmentador sem
vazamento; --incluir-teste os aceita) e de qualquer pagina ja usada em lote do Golden ou do Diamond.

As anotacoes (data/diamond/<lote>/anotacoes.jsonl) sao gravadas pelo servidor
(src/anotacao/servidor.py) e NUNCA por este script. Rodar de novo com o mesmo --lote acrescenta
paginas; pagina ja presente fica como esta.

Uso:
    python src/anotacao/preparar_diamond.py --lote diamond_piloto --de-lote _avaliacao/golden_v3 --n 20 --sem-regras
    python src/anotacao/preparar_diamond.py --lote diamond_treino --colecao data/processed/blocos data/processed/blocos_extra --n 200
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import random
import hashlib
import argparse
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.extrator import RAW, RAIZ_PROJETO  # noqa: E402

DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
DIR_DIAMOND = os.path.join(RAIZ_PROJETO, "data", "diamond")
EXTRATOR = os.path.join(RAIZ_PROJETO, "src", "data", "extrator.py")

# A proposta vive em src/data/regioes.py (candidato a segmentador v4); os nomes ficam aqui para
# os testes e para quem ja importava daqui.
from src.data.regioes import (  # noqa: E402,F401
    SCORE_MIN, SCORE_CONFIANTE, CLASSES, CLASSE_DETECTOR, PRIORIDADE, RE_ALFANUM,
    _area, _intersecao, _contem, _envelope, _lado_a_lado, _resolver_sobreposicoes, propor)


# ---------------------------------------------------------------------------
# Paginas
# ---------------------------------------------------------------------------

def _processar_pdf(tarefa):
    """Worker: abre um PDF, segmenta, propoe e renderiza as paginas pedidas."""
    import pdfplumber
    from src.data.extrator import palavras_da_pagina, segmentar
    from src.data import layout
    uf, arquivo, pedidos, dir_img, resolucao, regras, em_branco = tarefa  # pedidos: [(pagina_info, regioes, nome_img)]
    saida = []
    with pdfplumber.open(os.path.join(RAW, uf, *arquivo.split("/"))) as pdf:
        for info, regioes, nome_img in pedidos:
            pid = info["page_id"]
            try:
                page = pdf.pages[info["pagina"]]
                ws = palavras_da_pagina(page)
                blocos = segmentar(ws, layout.tabelas(regioes))
                # a imagem mostra a area de page.bbox; quando ela nao comeca em (0, 0) (SP: y = 50), as
                # coordenadas gravadas passam a ser relativas a imagem, e a origem fica em origem_pagina
                ox, oy = float(page.bbox[0]), float(page.bbox[1])
                bloco_de = {}
                for i, B in enumerate(blocos):
                    for L in B["linhas"]:
                        for w in L["ws"]:
                            bloco_de[id(w)] = i
                palavras = [[w["t"], round(w["x0"] - ox, 2), round(w["top"] - oy, 2), round(w["x1"] - ox, 2),
                             round(w["bottom"] - oy, 2), bloco_de.get(id(w), -1)] for w in ws]
                blocos_v3 = [{"id": f"v{i}", "bbox": [round(B["x0"] - ox, 1), round(B["top"] - oy, 1),
                                                     round(B["x1"] - ox, 1), round(B["bottom"] - oy, 1)],
                              **({"tipo": "tabela"} if B.get("tabela") else {})} for i, B in enumerate(blocos)]
                detector = [{**r, "bbox": [round(r["bbox"][0] - ox, 1), round(r["bbox"][1] - oy, 1),
                                           round(r["bbox"][2] - ox, 1), round(r["bbox"][3] - oy, 1)]}
                            for r in (regioes or []) if r["score"] >= SCORE_MIN]
                # em branco: sem pre-marcacao, o anotador desenha do zero (gabarito nao ancorado)
                proposta = [] if em_branco else propor(palavras, blocos_v3, detector, regras=regras)
                im = page.to_image(resolution=resolucao).original.convert("RGB")
                im.save(os.path.join(dir_img, nome_img), "JPEG", quality=85, optimize=True)
                reg = {"page_id": pid, "uf": uf, "arquivo": arquivo, "pagina": info["pagina"],
                       **{k: info[k] for k in ("grupo", "origem") if k in info},
                       "dimensions": {"width": round(float(page.width), 1), "height": round(float(page.height), 1)},
                       "imagem": nome_img, "proposta_versao": "em_branco" if em_branco else ("v2" if regras else "v1"),
                       **({"origem_pagina": [ox, oy]} if (ox, oy) != (0.0, 0.0) else {}),
                       "palavras": palavras, "blocos_v3": blocos_v3,
                       "detector": detector, "proposta": proposta,
                       "stats": {"n_palavras": len(palavras), "n_blocos_v3": len(blocos),
                                 "n_proposta": len(proposta),
                                 "palavras_sem_bloco_v3": sum(1 for w in palavras if w[5] < 0),
                                 "alertas": {a: sum(a in r["alertas"] for r in proposta)
                                             for a in ("juntou_sobrepostas", "so_regras", "baixa_confianca",
                                                       "atravessa_colunas")}}}
                saida.append((pid, reg, None))
            except Exception as e:
                saida.append((pid, None, f"{type(e).__name__}: {e}"))
    return saida


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def escolher(tarefas, n, semente):
    """Rodizio entre veiculos, cada um embaralhado com semente fixa."""
    rng = random.Random(semente)
    por_uf = {}
    for t in sorted(tarefas, key=lambda t: t["page_id"]):
        por_uf.setdefault(t["uf"], []).append(t)
    for lista in por_uf.values():
        rng.shuffle(lista)
    ufs = sorted(por_uf)
    rng.shuffle(ufs)
    escolhidas = []
    while len(escolhidas) < n and any(por_uf.values()):
        for uf in ufs:
            if por_uf[uf] and len(escolhidas) < n:
                escolhidas.append(por_uf[uf].pop())
    return escolhidas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True, help="nome do lote (letras, numeros, _ ou -)")
    fonte_pags = ap.add_mutually_exclusive_group(required=True)
    fonte_pags.add_argument("--de-lote", help="lote do Golden de onde vem a lista de paginas, ex.: _avaliacao/golden_v3")
    fonte_pags.add_argument("--colecao", nargs="+", help="pastas de blocos para sortear, ex.: data/processed/blocos_extra")
    ap.add_argument("--incluir-teste", action="store_true", help="com --colecao, aceita os veiculos de teste")
    ap.add_argument("--min-palavras", type=int, default=80, help="com --colecao")
    ap.add_argument("--max-palavras", type=int, default=2500, help="com --colecao")
    ap.add_argument("--sem-regras", action="store_true", help="proposta sem as regras do piloto (v1)")
    ap.add_argument("--em-branco", action="store_true",
                    help="sem pre-marcacao: o anotador desenha do zero (gabarito NAO ancorado, para teste justo)")
    ap.add_argument("--n", type=int, default=20, help="quantas paginas novas")
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--resolucao", type=int, default=150, help="dpi da imagem (caixas finas pedem mais que os 110 do Golden)")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.lote):
        sys.exit("[ERRO] nome de lote: use so letras, numeros, _ ou -")

    usadas = {t["page_id"] for arq_lote in glob.glob(os.path.join(DIR_GOLDEN, "**", "tarefas.jsonl"), recursive=True)
              + glob.glob(os.path.join(DIR_DIAMOND, "*", "tarefas.jsonl")) for t in ler_jsonl(arq_lote)}
    if a.de_lote:
        fonte = ler_jsonl(os.path.join(DIR_GOLDEN, *a.de_lote.split("/"), "tarefas.jsonl"))
        if not fonte:
            sys.exit(f"[ERRO] sem tarefas em data/golden/{a.de_lote}")
    else:
        from src.eval.protocolo import carregar_splits
        teste = set() if a.incluir_teste else set(carregar_splits()["teste"])
        fonte, vistos = [], set()
        for pasta in a.colecao:
            for arq_col in sorted(glob.glob(os.path.join(RAIZ_PROJETO, pasta, "*.jsonl"))):
                for p in ler_jsonl(arq_col):
                    if (p["page_id"] in usadas or p["page_id"] in vistos or p["uf"] in teste
                            or not a.min_palavras <= p["stats"]["n_palavras"] <= a.max_palavras):
                        continue
                    vistos.add(p["page_id"])
                    fonte.append({"page_id": p["page_id"], "uf": p["uf"], "arquivo": p["arquivo"],
                                  "pagina": p["pagina"], "grupo": os.path.basename(pasta.rstrip("/\\"))})
        print(f"[*] {len(fonte)} paginas candidatas de {len({p['uf'] for p in fonte})} veiculos"
              f"{'' if a.incluir_teste else ' (sem os de teste: ' + ', '.join(sorted(teste)) + ')'}")
    dir_lote = os.path.join(DIR_DIAMOND, a.lote)
    dir_img = os.path.join(dir_lote, "img")
    os.makedirs(dir_img, exist_ok=True)
    arq = os.path.join(dir_lote, "tarefas.jsonl")
    existentes = ler_jsonl(arq)
    ja = {t["page_id"] for t in existentes}
    escolhidas = escolher([t for t in fonte if t["page_id"] not in ja], a.n, f"{a.semente}-{a.lote}-{len(existentes)}")
    if not escolhidas:
        sys.exit("[ERRO] nenhuma pagina nova para o lote")

    from src.data import layout
    cache = layout.carregar_cache()
    sem_cache = [t["page_id"] for t in escolhidas if t["page_id"] not in cache]
    if sem_cache:
        sys.exit(f"[ERRO] {len(sem_cache)} paginas fora do cache de layout (rode src/data/layout.py antes; "
                 f"nao detecto aqui para nao disputar a GPU): {sem_cache[:5]}")

    por_pdf = {}
    for k, t in enumerate(escolhidas):
        nome_img = f"{len(existentes) + k + 1:03d}.jpg"
        por_pdf.setdefault((t["uf"], t["arquivo"]), []).append((t, cache[t["page_id"]], nome_img))
    tarefas = [(uf, arq_pdf, ps, dir_img, a.resolucao, not a.sem_regras, a.em_branco) for (uf, arq_pdf), ps in por_pdf.items()]
    resultado = {}
    with Pool(max(1, min(a.workers, len(tarefas)))) as pool:
        for itens in pool.imap_unordered(_processar_pdf, tarefas):
            for pid, reg, erro in itens:
                resultado[pid] = (reg, erro)

    with open(EXTRATOR, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    gravadas = 0
    with open(arq, "a", encoding="utf-8") as f:
        for t in escolhidas:
            reg, erro = resultado[t["page_id"]]
            if reg is None:
                print(f"  [!] pagina ignorada ({erro}): {t['page_id']}")
                continue
            reg = {"n": len(existentes) + gravadas + 1, **reg, "extrator_sha256": sha,
                   "detector": {"modelo": layout.MODELO, "revisao": layout.REVISAO, "score_min": SCORE_MIN,
                                "regioes": reg["detector"]}}
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            gravadas += 1
            s = reg["stats"]
            print(f"  {reg['n']:03d} {t['page_id']}: {s['n_palavras']} palavras | {s['n_blocos_v3']} blocos v3 | "
                  f"{s['n_proposta']} regioes propostas | alertas {s['alertas']}")
    print(f"[OK] {gravadas} paginas novas no Diamond '{a.lote}' ({len(existentes) + gravadas} no total) -> {dir_lote}")
    print("     Para anotar: venv\\Scripts\\python.exe src\\anotacao\\servidor.py --diamond")


if __name__ == "__main__":
    main()
