"""
Prepara um lote de paginas para a anotacao manual da ordem de leitura (Golden Dataset).

Para cada pagina escolhida grava, em data/golden/<lote>/:
  tarefas.jsonl   blocos (id, texto, bbox) e as ordens automaticas. A ferramenta de
                  anotacao NUNCA mostra essas ordens; elas servem so para a avaliacao.
  img/NNN.jpg     a pagina renderizada a partir do PDF original
  derivados/palavras_por_bloco.jsonl
                  as palavras de cada bloco, para a anotacao poder ser projetada em outra
                  segmentacao (src/anotacao/projetar_ordem.py) se o extrator mudar de novo

Toda pagina e segmentada NA HORA com o extrator atual e as tabelas do detector de layout
(src/data/layout.py), e nao copiada de uma colecao armazenada: o lote sempre corresponde ao
codigo que vai ser avaliado.

Grupos de amostragem (--grupo NOME:N, pode repetir):
  silver    veiculos de TESTE, em que o fluxo do PDF foi considerado confiavel. Comparar
            a anotacao humana com esse rotulo automatico valida (ou derruba) a referencia
            usada em todos os resultados ate aqui.
  incerto   veiculos em que o fluxo do PDF NAO e confiavel. Neles nao se sabe se erra o
            fluxo ou a XY-cut; so a anotacao humana decide.
  <veiculo> um veiculo especifico, ex.: official_diary_go (Goias, fora do acervo: baixe os
            PDFs para data/raw/official_diary_go/ e use --extrair).

Paginas a refazer (--refazer-de LOTE:ROTULO): as paginas de outro lote que a projecao da
anotacao para a segmentacao atual marcou como conflito ou deixou sem anotacao (puladas).
Entram primeiro, com o grupo de origem.

As paginas sao sorteadas com semente fixa, em rodizio entre veiculos e alternando
paginas de 3+, 2 e 1 coluna. Uma pagina presente em qualquer lote nunca e sorteada de novo.
Rodar de novo com o mesmo --lote ACRESCENTA paginas ao lote, sem apagar anotacoes.

Uso:
    python src/anotacao/preparar_lote.py --lote golden_v2 --refazer-de golden_v1:v3 --grupo silver:12 --grupo incerto:8
    python src/anotacao/preparar_lote.py --lote goias --grupo official_diary_go:20 --extrair
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
from src.eval.protocolo import carregar_splits, iterar_paginas, DIR_BLOCOS, RAIZ_PROJETO  # noqa: E402

RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
DIR_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "golden")
DIR_BLOCOS_GOLDEN = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos_golden")
EXTRATOR = os.path.join(RAIZ_PROJETO, "src", "data", "extrator.py")


def extrair_veiculo(uf, workers=4):
    """Extrai TODAS as paginas dos PDFs de data/raw/<uf> (veiculos fora do protocolo)."""
    from src.data.extrator import processar_pdf, PADROES_EXCLUIDOS
    pdfs = sorted(p for p in glob.glob(os.path.join(RAW, uf, "**", "*.pdf"), recursive=True)
                  if not any(x in p for x in PADROES_EXCLUIDOS))
    if not pdfs:
        sys.exit(f"[ERRO] nenhum PDF em {os.path.join(RAW, uf)}")
    os.makedirs(DIR_BLOCOS_GOLDEN, exist_ok=True)
    destino = os.path.join(DIR_BLOCOS_GOLDEN, f"{uf}.jsonl")
    tarefas = [(uf, p, 100000, f"golden-{uf}-{k}", True) for k, p in enumerate(pdfs)]
    n = 0
    with Pool(workers) as pool, open(destino, "w", encoding="utf-8") as f:
        for _, registros, _, _ in pool.imap_unordered(processar_pdf, tarefas):
            for r in registros:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += len(registros)
    print(f"[*] {uf}: {n} paginas extraidas de {len(pdfs)} PDFs -> {destino}")


def candidatas(ufs, excluir):
    """Paginas das colecoes armazenadas (so a lista e o numero de colunas, para o sorteio)."""
    por_uf = {}
    for uf in ufs:
        proprio = os.path.join(DIR_BLOCOS_GOLDEN, f"{uf}.jsonl")
        fonte = DIR_BLOCOS_GOLDEN if os.path.exists(proprio) else DIR_BLOCOS
        for p in iterar_paginas([uf], fonte):
            if p["page_id"] not in excluir:
                por_uf.setdefault(uf, []).append(p)
    return por_uf


def sortear(por_uf, n, rng):
    """Rodizio entre veiculos, alternando as faixas de 3+, 2 e 1 coluna."""
    faixas = {}
    for uf, pags in sorted(por_uf.items()):
        d = {1: [], 2: [], 3: []}
        for p in sorted(pags, key=lambda p: p["page_id"]):
            d[min(3, max(1, p["stats"]["n_colunas"]))].append(p)
        for lista in d.values():
            rng.shuffle(lista)
        faixas[uf] = d
    ufs = sorted(faixas)
    rng.shuffle(ufs)
    escolhidas, vez = [], 0
    while len(escolhidas) < n and ufs:
        alvo = (3, 2, 1)[len(escolhidas) % 3]
        pego = None
        for preferir_alvo in (True, False):
            for k in range(len(ufs)):
                uf = ufs[(vez + k) % len(ufs)]
                opcoes = [alvo] if preferir_alvo else [b for b in (3, 2, 1) if faixas[uf][b]]
                if opcoes and faixas[uf][opcoes[0]]:
                    pego, vez = faixas[uf][opcoes[0]].pop(), (vez + k + 1) % len(ufs)
                    break
            if pego:
                break
        if pego is None:
            break
        escolhidas.append(pego)
    return escolhidas


def paginas_a_refazer(spec):
    """LOTE:ROTULO -> paginas que a projecao marcou como conflito ou sem anotacao."""
    lote, _, rotulo = spec.partition(":")
    arq = os.path.join(DIR_GOLDEN, lote, "derivados", f"projecao_{rotulo}.jsonl")
    if not rotulo or not os.path.exists(arq):
        sys.exit(f"[ERRO] --refazer-de {spec}: nao achei {arq} (rode src/anotacao/projetar_ordem.py antes)")
    saida, fora = [], []
    with open(arq, encoding="utf-8") as f:
        for linha in f:
            r = json.loads(linha)
            if r["status"] in ("conflito", "sem_anotacao"):
                t = r["tarefa"]
                saida.append({"page_id": r["page_id"], "uf": t["uf"], "arquivo": t["arquivo"],
                              "pagina": t["pagina"], "grupo": t.get("grupo", lote), "origem": lote,
                              "motivo_refazer": r["status"]})
            elif r["status"] == "sem_blocos":
                fora.append(r["page_id"])
    if fora:
        print(f"[*] {len(fora)} paginas de {lote} ficam de fora: a segmentacao atual as rejeita "
              f"(menos de 3 blocos ou texto ilegivel): {fora}")
    return saida


def renderizar(p, destino, resolucao):
    import pdfplumber
    with pdfplumber.open(os.path.join(RAW, p["uf"], p["arquivo"])) as pdf:
        im = pdf.pages[p["pagina"]].to_image(resolution=resolucao).original.convert("RGB")
    im.save(destino, "JPEG", quality=82, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True, help="nome do lote (letras, numeros, _ ou -)")
    ap.add_argument("--grupo", action="append", default=[], help="NOME:N, ex.: silver:10 ou incerto:20")
    ap.add_argument("--refazer-de", action="append", default=[], metavar="LOTE:ROTULO",
                    help="inclui, primeiro, as paginas de outro lote que derivados/projecao_<ROTULO>.jsonl "
                         "marcou como conflito ou sem anotacao (src/anotacao/projetar_ordem.py)")
    ap.add_argument("--min-blocos", type=int, default=6, help="na segmentacao atual")
    ap.add_argument("--max-blocos", type=int, default=80, help="na segmentacao atual")
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--resolucao", type=int, default=110, help="dpi da imagem da pagina")
    ap.add_argument("--sem-layout", action="store_true", help="segmenta sem as tabelas do detector de layout")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--extrair", action="store_true",
                    help="extrai antes os veiculos fora do protocolo (ex.: official_diary_go)")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.lote):
        sys.exit("[ERRO] nome de lote: use so letras, numeros, _ ou -")
    if not a.grupo and not a.refazer_de:
        sys.exit("[ERRO] peca paginas com --grupo e/ou --refazer-de")

    from src.data.extrator import processar_paginas
    splits = carregar_splits()
    dir_lote = os.path.join(DIR_GOLDEN, a.lote)
    os.makedirs(os.path.join(dir_lote, "img"), exist_ok=True)
    arq = os.path.join(dir_lote, "tarefas.jsonl")
    ja_usadas, no_lote, n_existentes = set(), set(), 0
    for outro in glob.glob(os.path.join(DIR_GOLDEN, "*", "tarefas.jsonl")):
        with open(outro, encoding="utf-8") as f:
            ids = [json.loads(l)["page_id"] for l in f if l.strip()]
        ja_usadas |= set(ids)
        if os.path.exists(arq) and os.path.samefile(outro, arq):
            n_existentes, no_lote = len(ids), set(ids)

    # 1. paginas a refazer: entram primeiro, na ordem do lote de origem
    refazer = []
    for spec in a.refazer_de:
        refazer += [p for p in paginas_a_refazer(spec) if p["page_id"] not in no_lote]

    # 2. sorteio por grupo. O filtro de tamanho vale sobre a segmentacao ATUAL: pela contagem
    #    armazenada ficariam de fora justamente as paginas de tabela, que a versao anterior
    #    picotava em mais de 80 blocos. Sorteia-se 3x o pedido e aceita-se na ordem do sorteio.
    rng = random.Random(f"{a.semente}-{a.lote}-{n_existentes}")
    pedidos = []
    for g in a.grupo:
        nome, _, qtd = g.partition(":")
        n = int(qtd or 10)
        if nome == "silver":
            ufs = splits["teste"]
        elif nome == "incerto":
            ufs = splits["ufs_nao_confiaveis"]
        else:
            ufs = [nome]
            if a.extrair:
                extrair_veiculo(nome)
        por_uf = candidatas(ufs, ja_usadas)
        sorteio = sortear(por_uf, 3 * n, rng)
        ja_usadas |= {p["page_id"] for p in sorteio}
        pedidos.append((nome, n, sorteio, len(por_uf), sum(len(v) for v in por_uf.values())))

    todas = refazer + [p for _, _, sorteio, _, _ in pedidos for p in sorteio]
    if not todas:
        sys.exit("[ERRO] nenhuma pagina para o lote")
    tabelas = None
    if not a.sem_layout:
        from src.data import layout
        cache = layout.garantir_cache(todas, workers=a.workers)
        tabelas = {p["page_id"]: layout.tabelas(cache[p["page_id"]]) for p in todas}
    print(f"[*] segmentando {len(todas)} paginas com o extrator atual"
          f"{' (sem layout)' if tabelas is None else ''}", flush=True)
    segmentadas = processar_paginas(todas, tabelas, palavras=True, workers=a.workers)

    novas = []
    for p in refazer:
        reg, motivo = segmentadas[p["page_id"]]
        if reg is None:
            print(f"  [!] pagina a refazer rejeitada pelo extrator ({motivo}): {p['page_id']}")
            continue
        novas.append((reg, {k: p[k] for k in ("grupo", "origem", "motivo_refazer")}))
    if refazer:
        print(f"[*] a refazer: {len(novas)} de {len(refazer)} paginas ({', '.join(a.refazer_de)})")
    for nome, n, sorteio, n_ufs, n_cand in pedidos:
        aceitas = 0
        for p in sorteio:
            if aceitas == n:
                break
            reg, _ = segmentadas[p["page_id"]]
            if reg is None or not (a.min_blocos <= reg["stats"]["n_blocos"] <= a.max_blocos):
                continue
            novas.append((reg, {"grupo": nome}))
            aceitas += 1
        print(f"[*] grupo {nome}: {aceitas} de {n} paginas pedidas, de {n_ufs} veiculos ({n_cand} candidatas; "
              f"{a.min_blocos}-{a.max_blocos} blocos na segmentacao atual)")

    with open(EXTRATOR, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    os.makedirs(os.path.join(dir_lote, "derivados"), exist_ok=True)
    gravadas, blocos = 0, 0
    with open(arq, "a", encoding="utf-8") as f_tar, \
            open(os.path.join(dir_lote, "derivados", "palavras_por_bloco.jsonl"), "a", encoding="utf-8") as f_pal:
        for reg, extras in novas:
            k = n_existentes + gravadas + 1
            nome_img = f"{k:03d}.jpg"
            try:
                renderizar(reg, os.path.join(dir_lote, "img", nome_img), a.resolucao)
            except Exception as e:
                print(f"  [!] pagina ignorada, nao renderizou {reg['page_id']}: {e}")
                continue
            palavras = reg.pop("_palavras")
            f_tar.write(json.dumps({"n": k, "page_id": reg["page_id"], **extras, "uf": reg["uf"],
                                    "arquivo": reg["arquivo"], "pagina": reg["pagina"],
                                    "dimensions": reg["dimensions"], "imagem": nome_img,
                                    "bounding_boxes": reg["bounding_boxes"], "ordens": reg["ordens"],
                                    "stats": reg["stats"]}, ensure_ascii=False) + "\n")
            f_pal.write(json.dumps({"page_id": reg["page_id"], "extrator_sha256": sha, "blocos": palavras},
                                   ensure_ascii=False) + "\n")
            gravadas += 1
            blocos += reg["stats"]["n_blocos"]
    print(f"[OK] {gravadas} paginas novas no lote '{a.lote}' ({n_existentes + gravadas} no total, "
          f"{blocos} blocos a ordenar) -> {dir_lote}")
    print("     Para anotar: venv\\Scripts\\python.exe src\\anotacao\\servidor.py")


if __name__ == "__main__":
    main()
