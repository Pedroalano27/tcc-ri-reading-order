"""
Projeta a ordem anotada de um lote do Golden nos blocos da segmentacao ATUAL das mesmas paginas.

A anotacao humana ordena os blocos de uma segmentacao. Quando o extrator muda, os blocos mudam,
mas as palavras nao. Com derivados/palavras_por_bloco.jsonl (src/anotacao/congelar_palavras.py),
cada palavra herda a posicao do seu bloco na ordem humana e a sua posicao dentro do bloco; isso
da a SEQUENCIA HUMANA DE PALAVRAS da pagina. Cada bloco novo recebe as palavras antigas cujo
centro cai dentro de alguma palavra dele (uma palavra nova pode juntar varias antigas, como em
"R E S O L V E" -> "RESOLVE").

Uma pagina e LIMPA quando o conjunto de palavras de todo bloco novo e um trecho CONTIGUO da
sequencia humana (depois de retirar as palavras que nao entraram em bloco nenhum, como os
separadores descartados). Nesse caso a ordem projetada -- blocos novos pelo inicio do trecho --
e exatamente a leitura do anotador: juntar blocos que ele leu em sequencia (os pedacos de uma
tabela) ou dividir um bloco em pedacos seguidos (um paragrafo cortado) nao muda nada. A pagina
tem CONFLITO quando algum bloco novo nao e contiguo: um bloco antigo que atravessava colunas foi
dividido e os pedacos se intercalam, ou um bloco novo junta trechos que o anotador leu em
momentos diferentes. So o anotador resolve esses casos; a pagina volta para anotacao.

Grava data/golden/<lote>/derivados/projecao_<rotulo>.jsonl, uma linha por pagina do lote:
  {"page_id", "status": "limpa" | "conflito" | "sem_anotacao" | "sem_blocos", "anotador",
   "extrator_sha256", "tarefa": <registro da segmentacao atual, sem "_palavras">,
   "palavras_por_bloco": {...}, "ordem": [ids novos] (so se limpa),
   "blocos_em_conflito": [ids novos], "posicoes_humanas_afetadas": [posicoes 1..n da anotacao]}

Uso:
    python src/anotacao/projetar_ordem.py --lote golden_v1 --rotulo v3
"""
from __future__ import annotations

import os
import re
import sys
import json
import hashlib
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import RAIZ_PROJETO  # noqa: E402

DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
EXTRATOR = os.path.join(RAIZ_PROJETO, "src", "data", "extrator.py")
# letra ou digito: palavra sem nenhum e separador ("***", "-"), que o extrator atual descarta
RE_ALFANUM = re.compile(r"[^\W_]")


def sequencia_humana(anotacao, palavras_antigas):
    """[(cx, cy, posicao_do_bloco, texto)] na ordem de leitura do anotador, uma entrada por palavra."""
    seq = []
    for k, bid in enumerate(anotacao["ordem"]):
        for t, x0, top, x1, bottom in palavras_antigas[bid]:
            seq.append(((x0 + x1) / 2, (top + bottom) / 2, k, t))
    return seq


def casar_palavras(seq, palavras_novas, folga=0.6):
    """Cada palavra antiga vai para UMA palavra nova que contem o seu centro (com `folga` pt).

    A escolha e feita palavra antiga a palavra antiga, sobre todas as candidatas, e nao por
    ordem de visita: com palavras muito proximas, a primeira palavra nova visitada tomava o
    centro da vizinha (achado da revisao do Codex). Preferencia: contem o centro sem folga;
    mesmo texto (ou o texto antigo dentro do novo, como "R" em "RESOLVE"); menor distancia.
    Devolve (lista de palavras novas [(id_bloco, texto, x0, top, x1, bottom)], {i_antiga: j_nova})."""
    novas = [(bid, *p) for bid in sorted(palavras_novas, key=lambda b: int(b[1:])) for p in palavras_novas[bid]]
    grade = {}
    for j, (_, _, x0, top, x1, bottom) in enumerate(novas):
        for gx in range(int((x0 - folga) // 20), int((x1 + folga) // 20) + 1):
            for gy in range(int((top - folga) // 20), int((bottom + folga) // 20) + 1):
                grade.setdefault((gx, gy), []).append(j)
    atribuicao = {}
    for i, (cx, cy, _, t) in enumerate(seq):
        melhor = None
        for j in grade.get((int(cx // 20), int(cy // 20)), ()):
            _, tn, x0, top, x1, bottom = novas[j]
            if not (x0 - folga <= cx <= x1 + folga and top - folga <= cy <= bottom + folga):
                continue
            chave = (not (x0 <= cx <= x1 and top <= cy <= bottom), tn != t, t not in tn,
                     abs(cx - (x0 + x1) / 2) + abs(cy - (top + bottom) / 2), j)
            if melhor is None or chave < melhor:
                melhor = chave
        if melhor is not None:
            atribuicao[i] = melhor[-1]
    return novas, atribuicao


def projetar_pagina(anotacao, palavras_antigas, palavras_novas, folga=0.6):
    """Devolve {"status", "ordem", "blocos_em_conflito", "posicoes_humanas_afetadas", ...}.

    anotacao: registro de anotacoes.jsonl (status concluida); palavras_antigas: id antigo -> palavras;
    palavras_novas: id novo -> palavras ([texto, x0, top, x1, bottom]).

    A garantia de uma pagina "limpa" e sobre a ORDEM DOS BLOCOS: ela e a do anotador. A ordem das
    palavras DENTRO de um bloco pode mudar, e muda quando a segmentacao nova corrige uma linha
    (o "nº" que voltou para a propria linha no MA); a avaliacao e por bloco. Para ser limpa, alem
    da contiguidade, toda palavra nova precisa ter par antigo e toda palavra antiga que sumiu
    precisa ser separador (sem letra nem digito)."""
    seq = sequencia_humana(anotacao, palavras_antigas)
    novas, atribuicao = casar_palavras(seq, palavras_novas, folga)
    posicoes = {bid: set() for bid in palavras_novas}
    com_par = set(atribuicao.values())
    for i, j in atribuicao.items():
        posicoes[novas[j][0]].add(i)
    sem_par = [novas[j][1] for j in range(len(novas)) if j not in com_par and RE_ALFANUM.search(novas[j][1])]
    perdidas = [seq[i][3] for i in range(len(seq)) if i not in atribuicao and RE_ALFANUM.search(seq[i][3])]
    rank = {p: r for r, p in enumerate(sorted(atribuicao))}
    conflito, afetadas = [], set()
    for bid, conj in posicoes.items():
        if not conj:
            continue
        rs = sorted(rank[p] for p in conj)
        if rs[-1] - rs[0] + 1 != len(rs):
            conflito.append(bid)
            afetadas.update(seq[p][2] + 1 for p in conj)
    vazios = sorted((bid for bid, conj in posicoes.items() if not conj), key=lambda b: int(b[1:]))
    saida = {"blocos_em_conflito": sorted(conflito, key=lambda b: int(b[1:])),
             "posicoes_humanas_afetadas": sorted(afetadas), "palavras_novas_sem_par": sem_par,
             "palavras_anotadas_perdidas": perdidas, "blocos_sem_palavra_anotada": vazios}
    if conflito or vazios or sem_par or perdidas:
        saida["status"] = "conflito"
        saida["ordem"] = None
    else:
        saida["status"] = "limpa"
        saida["ordem"] = sorted(posicoes, key=lambda b: min(rank[p] for p in posicoes[b]))
    return saida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True)
    ap.add_argument("--rotulo", required=True, help="nome da segmentacao atual, ex.: v3")
    ap.add_argument("--anotador", help="padrao: o registro concluido de cada pagina")
    ap.add_argument("--layout", default=None, help="pasta do cache de layout (padrao: data/processed/layout)")
    ap.add_argument("--sem-layout", action="store_true", help="segmenta sem regioes de tabela")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()

    from src.data import layout as L
    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    tarefas = [json.loads(l) for l in open(os.path.join(dir_lote, "tarefas.jsonl"), encoding="utf-8") if l.strip()]
    anotacoes = {}
    for l in open(os.path.join(dir_lote, "anotacoes.jsonl"), encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            if r["status"] == "concluida" and (not a.anotador or r["anotador"] == a.anotador):
                anotacoes[r["page_id"]] = r
    antigas = {json.loads(l)["page_id"]: json.loads(l)
               for l in open(os.path.join(dir_lote, "derivados", "palavras_por_bloco.jsonl"), encoding="utf-8") if l.strip()}
    faltam_palavras = [t["page_id"] for t in tarefas if t["page_id"] in anotacoes and t["page_id"] not in antigas]
    if faltam_palavras:
        sys.exit(f"[ERRO] {len(faltam_palavras)} paginas anotadas sem palavras congeladas: {faltam_palavras[:3]}")

    tabelas = {}
    if not a.sem_layout:
        cache = L.garantir_cache(tarefas, a.layout or L.DIR_LAYOUT, workers=a.workers)
        tabelas = {t["page_id"]: L.tabelas(cache[t["page_id"]]) for t in tarefas}

    with open(EXTRATOR, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    from src.data.extrator import processar_paginas
    segmentadas = processar_paginas(tarefas, None if a.sem_layout else tabelas, palavras=True, workers=a.workers)

    destino = os.path.join(dir_lote, "derivados", f"projecao_{a.rotulo}.jsonl")
    contagem = {}
    with open(destino, "w", encoding="utf-8") as f:
        for t in tarefas:
            pid = t["page_id"]
            reg, motivo = segmentadas[pid]
            linha = {"page_id": pid, "extrator_sha256": sha, "anotador": None}
            if reg is None:
                linha.update(status="sem_blocos", motivo=motivo)
            else:
                palavras_novas = reg.pop("_palavras")
                linha.update(tarefa={**reg, **{k: t[k] for k in ("n", "grupo", "imagem") if k in t}},
                             palavras_por_bloco=palavras_novas)
                if pid not in anotacoes:
                    linha["status"] = "sem_anotacao"
                else:
                    linha["anotador"] = anotacoes[pid]["anotador"]
                    linha.update(projetar_pagina(anotacoes[pid], antigas[pid]["blocos"], palavras_novas))
            contagem[linha["status"]] = contagem.get(linha["status"], 0) + 1
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            antes = len(t["bounding_boxes"])
            depois = len(reg["bounding_boxes"]) if reg else 0
            extra = ""
            if linha["status"] == "conflito":
                extra = f" | posicoes afetadas {linha['posicoes_humanas_afetadas'][:15]}"
            print(f"  {linha['status']:<13} {antes:>3} -> {depois:<3} blocos "
                  f"({reg['stats']['n_tabelas'] if reg else 0} tabelas) {pid[:62]}{extra}")
    print(f"[OK] {contagem} -> {os.path.relpath(destino, RAIZ_PROJETO)}")


if __name__ == "__main__":
    main()
