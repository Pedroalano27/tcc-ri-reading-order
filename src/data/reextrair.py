"""
Re-extrai EXATAMENTE as mesmas paginas de uma coleta ja existente, com o codigo atual.

Por que existe: quando o extrator e corrigido, rodar `extrator.py` de novo re-amostra
as paginas (outro sorteio, outros PDFs) e o antes/depois deixa de ser comparavel. Aqui
a lista de paginas vem do proprio arquivo de entrada, entao as duas versoes cobrem o
MESMO conjunto -- e a diferenca medida e so a da segmentacao.

Isso serve a duas coisas:
  1. corrigir uma coleta sem perder o protocolo (mesmos veiculos, mesmas paginas);
  2. manter as duas versoes lado a lado para a ANALISE DE SENSIBILIDADE a granularidade:
     o ranking dos metodos sobrevive a uma segmentacao diferente?

Funciona tanto com os .jsonl de data/processed/blocos* quanto com o tarefas.jsonl de um
lote do Golden Dataset (campos extras do lote, como grupo e imagem, sao preservados).

Tambem mede a QUALIDADE da segmentacao antes e depois:
  caixas sobrepostas   duas caixas que se cruzam em area. Numa segmentacao correta isso
                       nao acontece; e a assinatura de uma linha cortada ao meio, cujas
                       metades cairam em blocos diferentes com o texto embaralhado.
  blocos de 1 palavra  fragmentacao. NAO e defeito por si so: o Google Document AI produz
                       22% deles nos mesmos diarios (o cabecalho de um diario e feito de
                       muitas regioes pequenas mesmo). Reportado para acompanhar.

As tabelas vem do cache do detector de layout (src/data/layout.py). Se alguma pagina da
entrada nao estiver no cache, o script para e diz o comando que falta, em vez de segmentar
parte das paginas sem tabela; --sem-layout segmenta tudo sem tabela, de proposito.

Uso:
    python src/data/layout.py --colecao data/processed/blocos_v1
    python src/data/reextrair.py --entrada data/processed/blocos_v1 --saida data/processed/blocos
    python src/data/reextrair.py --entrada data/processed/blocos --so-medir
    (NUNCA sobre o tarefas.jsonl de um lote do Golden com anotacao humana: os ids mudam.)
"""
from __future__ import annotations

import os
import sys
import json
import glob
import time
import shutil
import argparse
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data import extrator  # noqa: E402
from src.data.extrator import RAW, RAIZ_PROJETO  # noqa: E402


def ler_jsonl(caminho):
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError:
                    continue          # linha truncada por uma extracao interrompida


def qualidade(registros):
    """Metricas de qualidade da segmentacao de um conjunto de paginas."""
    n = sobrepostos = curtos = 0
    paginas_com_sobreposicao = 0
    for r in registros:
        cs = r["bounding_boxes"]
        n += len(cs)
        curtos += sum(1 for c in cs if len(c["text"].split()) <= 1)
        marcados = set()
        for i, a in enumerate(cs):
            ax0, ay0, ax1, ay1 = a["bbox"]
            aa = max(1e-6, (ax1 - ax0) * (ay1 - ay0))
            for j in range(i + 1, len(cs)):
                bx0, by0, bx1, by1 = cs[j]["bbox"]
                ab = max(1e-6, (bx1 - bx0) * (by1 - by0))
                iw, ih = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
                if iw > 1 and ih > 1 and (iw * ih) / min(aa, ab) >= 0.25:
                    marcados.add(i)
                    marcados.add(j)
        sobrepostos += len(marcados)
        paginas_com_sobreposicao += bool(marcados)
    return {"paginas": len(registros), "blocos": n,
            "blocos_por_pagina": round(n / max(1, len(registros)), 1),
            "blocos_sobrepostos": sobrepostos,
            "prop_blocos_sobrepostos": round(sobrepostos / max(1, n), 4),
            "paginas_com_sobreposicao": paginas_com_sobreposicao,
            "prop_paginas_com_sobreposicao": round(paginas_com_sobreposicao / max(1, len(registros)), 4),
            "blocos_de_1_palavra": curtos, "prop_blocos_de_1_palavra": round(curtos / max(1, n), 4)}


def reprocessar_pdf(tarefa):
    """Worker: reabre um PDF e refaz so as paginas pedidas, na ordem original."""
    import pdfplumber
    uf, arquivo, pedidos, tabelas, min_blocos = tarefa   # pedidos: [(n_pag, registro_antigo)]; tabelas: page_id -> caixas | None
    # O filtro de blocos do extrator e uma constante do modulo; muda-se so neste processo, para nao
    # alterar src/data/extrator.py (o sha dele amarra os lotes do Golden a segmentacao).
    extrator.MIN_BLOCOS = min_blocos
    caminho = os.path.join(RAW, uf, *arquivo.split("/"))
    saida, perdidas = [], []
    try:
        with pdfplumber.open(caminho) as pdf:
            for n_pag, antigo in pedidos:
                try:
                    tab = None if tabelas is None else tabelas.get(antigo["page_id"], [])
                    novo, motivo = extrator.processar_pagina(pdf.pages[n_pag], uf, arquivo, n_pag, tabelas=tab)
                except Exception:
                    novo, motivo = None, "erro_pagina"
                if novo is None:
                    perdidas.append((antigo["page_id"], motivo))
                    continue
                extras = {k: v for k, v in antigo.items() if k not in novo}
                saida.append({**novo, **extras})
    except Exception:
        perdidas += [(a["page_id"], "pdf_ilegivel") for _, a in pedidos]
    return uf, saida, perdidas


def agrupar(registros, tabelas=None, min_blocos=3):
    por_pdf = {}
    for r in registros:
        por_pdf.setdefault((r["uf"], r["arquivo"]), []).append((r["pagina"], r))
    tarefas = []
    for (uf, arq), ps in por_pdf.items():
        ps = sorted(ps, key=lambda x: x[0])
        tabs = None if tabelas is None else {r["page_id"]: tabelas[r["page_id"]] for _, r in ps}
        tarefas.append((uf, arq, ps, tabs, min_blocos))
    return tarefas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", required=True, help="pasta com *.jsonl ou um .jsonl especifico")
    ap.add_argument("--saida", help="pasta (ou arquivo) de destino; exige --no-lugar se for igual a entrada")
    ap.add_argument("--no-lugar", action="store_true", help="sobrescreve a entrada (guarda .bak antes)")
    ap.add_argument("--so-medir", action="store_true", help="so mede a qualidade da entrada e sai")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--layout", help="pasta do cache de layout (padrao: data/processed/layout)")
    ap.add_argument("--sem-layout", action="store_true", help="segmenta sem as tabelas do detector")
    ap.add_argument("--min-blocos", type=int, default=3,
                    help="filtro minimo de blocos por pagina (3 para ordenar; 1 para a colecao de RI)")
    a = ap.parse_args()

    entrada = os.path.abspath(a.entrada)
    arquivos = ([entrada] if entrada.endswith(".jsonl")
                else sorted(p for p in glob.glob(os.path.join(entrada, "*.jsonl"))))
    if not arquivos:
        sys.exit(f"[ERRO] nenhum .jsonl em {entrada}")

    # Um unico pool sobre TODOS os PDFs de todos os arquivos: um diario denso sozinho
    # segurava a fila inteira quando o pool era criado por arquivo.
    por_arquivo = {arq: list(ler_jsonl(arq)) for arq in arquivos}
    por_arquivo = {k: v for k, v in por_arquivo.items() if v}
    antes_total = [r for regs in por_arquivo.values() for r in regs]
    if a.so_medir:
        for arq, regs in por_arquivo.items():
            q = qualidade(regs)
            print(f"  {os.path.relpath(arq, RAIZ_PROJETO):<52} {q['paginas']:>5} pag. | sobrepostos "
                  f"{q['prop_blocos_sobrepostos']:>6.1%} | 1 palavra {q['prop_blocos_de_1_palavra']:>6.1%}", flush=True)
        print("\nQUALIDADE DA SEGMENTACAO:", json.dumps(qualidade(antes_total), ensure_ascii=False, indent=2))
        return

    de_qual_arquivo = {r["page_id"]: arq for arq, regs in por_arquivo.items() for r in regs}
    tabelas = None
    if not a.sem_layout:
        from src.data import layout
        pasta = os.path.abspath(a.layout) if a.layout else layout.DIR_LAYOUT
        cache = layout.carregar_cache(pasta)
        faltam = [r["page_id"] for r in antes_total if r["page_id"] not in cache]
        if faltam:
            sys.exit(f"[ERRO] {len(faltam)} de {len(antes_total)} paginas sem layout em {pasta} (ex.: {faltam[0]}).\n"
                     f"        Rode antes: python src/data/layout.py --colecao {a.entrada}\n"
                     f"        ou use --sem-layout para segmentar tudo sem tabelas.")
        tabelas = {r["page_id"]: layout.tabelas(cache[r["page_id"]]) for r in antes_total}
        print(f"[*] layout: {sum(len(v) for v in tabelas.values() if v)} tabelas em "
              f"{sum(1 for v in tabelas.values() if v)} de {len(antes_total)} paginas", flush=True)
        sem_imagem = [pid for pid, v in tabelas.items() if v is None]
        if sem_imagem:
            print(f"[!] {len(sem_imagem)} paginas nao renderizaram no detector e saem sem tabelas "
                  f"(stats.layout = false): {sem_imagem[:5]}", flush=True)
    tarefas = agrupar(antes_total, tabelas, a.min_blocos)
    print(f"[*] {len(antes_total)} paginas em {len(tarefas)} PDFs, {len(por_arquivo)} arquivos, "
          f"{a.workers} processos", flush=True)
    t0 = time.time()
    novos_por_arquivo, perdidas, feitos = {arq: [] for arq in por_arquivo}, [], 0
    with Pool(min(a.workers, len(tarefas))) as pool:
        for _, regs, perd in pool.imap_unordered(reprocessar_pdf, tarefas):
            for r in regs:
                novos_por_arquivo[de_qual_arquivo[r["page_id"]]].append(r)
            perdidas += perd
            feitos += 1
            if feitos % 50 == 0:
                print(f"    {feitos}/{len(tarefas)} PDFs ({time.time() - t0:.0f}s)", flush=True)

    depois_total = []
    for arq, antigos in por_arquivo.items():
        novos = novos_por_arquivo[arq]
        ordem = {r["page_id"]: i for i, r in enumerate(antigos)}
        novos.sort(key=lambda r: ordem.get(r["page_id"], 10 ** 9))
        depois_total += novos
        antes, depois = qualidade(antigos), qualidade(novos)

        if entrada.endswith(".jsonl"):
            destino = os.path.abspath(a.saida) if a.saida and not a.no_lugar else arq
        else:
            pasta = os.path.abspath(a.saida) if a.saida and not a.no_lugar else entrada
            os.makedirs(pasta, exist_ok=True)
            destino = os.path.join(pasta, os.path.basename(arq))
        if os.path.abspath(destino) == os.path.abspath(arq):
            if not a.no_lugar:
                sys.exit("[ERRO] destino igual a entrada: use --saida OUTRA_PASTA ou --no-lugar")
            shutil.copy2(arq, arq + ".bak")
        with open(destino, "w", encoding="utf-8") as f:
            for r in novos:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {os.path.relpath(arq, RAIZ_PROJETO):<52} {antes['paginas']:>5} pag. | blocos "
              f"{antes['blocos']:>6} -> {depois['blocos']:<6} | sobrepostos "
              f"{antes['prop_blocos_sobrepostos']:>6.1%} -> {depois['prop_blocos_sobrepostos']:<6.1%}", flush=True)
    if perdidas:
        print(f"  [!] {len(perdidas)} paginas nao voltaram: {perdidas[:3]}")

    print()
    if a.so_medir:
        print("QUALIDADE DA SEGMENTACAO:", json.dumps(qualidade(antes_total), ensure_ascii=False, indent=2))
        return
    antes, depois = qualidade(antes_total), qualidade(depois_total)
    print(f"{'':<34}{'antes':>12}{'depois':>12}")
    for chave, rot in (("paginas", "paginas"), ("blocos", "blocos"),
                       ("blocos_por_pagina", "blocos por pagina"),
                       ("prop_blocos_sobrepostos", "blocos sobrepostos"),
                       ("prop_paginas_com_sobreposicao", "paginas com sobreposicao"),
                       ("prop_blocos_de_1_palavra", "blocos de 1 palavra")):
        fmt = (lambda v: f"{v:.1%}") if chave.startswith("prop_") else (lambda v: f"{v:g}")
        print(f"{rot:<34}{fmt(antes[chave]):>12}{fmt(depois[chave]):>12}")
    destino_json = os.path.join(RAIZ_PROJETO, "resultados", "qualidade_segmentacao.json")
    os.makedirs(os.path.dirname(destino_json), exist_ok=True)
    with open(destino_json, "w", encoding="utf-8") as f:
        json.dump({"entrada": os.path.relpath(entrada, RAIZ_PROJETO), "antes": antes, "depois": depois,
                   "data": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] -> {os.path.relpath(destino_json, RAIZ_PROJETO)}")


if __name__ == "__main__":
    main()
