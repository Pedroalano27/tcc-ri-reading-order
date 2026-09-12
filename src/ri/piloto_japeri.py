"""
Piloto de RI: a ordem de leitura muda o que a busca encontra? (Japeri, RJ)

Japeri e um dos veiculos em que o fluxo do PDF NAO e confiavel, e o acervo traz 421 atos dele
(json_atos_japeri) com o texto em ordem correta de leitura. Os atos viram a colecao de teste:
cada consulta sai de um ato, e sao relevantes as paginas que contem o conteudo da consulta.
A relevancia e decidida por sobreposicao de palavras, que independe da ordem; por isso e a
mesma para todos os metodos. So muda o texto que cada metodo de ordenacao produz.

Metodos: ordem do detector (piso), fluxo do PDF (o que um indexador comum extrai), ingenua,
XY-cut e LayoutLM (checkpoint treinado, rodado agora na GPU).

Medidas, por metodo:
  fidelidade   % de frases de 12 palavras dos atos que sobrevivem no texto da pagina
               (>= 10 das 12 palavras alinhadas)
  pagina       busca BM25 com a pagina inteira como documento. Controle: o saco de palavras
               e o mesmo em qualquer ordem, entao o resultado e identico para todos
  trechos      busca BM25 em janelas de 100 palavras (passo 50), como num RAG; a pagina vale
               o seu melhor trecho. MRR@10, Recall@1, Recall@5 por tipo de consulta:
                 frase    12 palavras seguidas do corpo do ato (as de maior IDF)
                 titulo   a primeira linha do ato (ex.: "Portaria no 0555/2024")
                 termos   os 8 termos mais raros do ato, sem ordem
  contexto     % das consultas-frase cujo 1o trecho devolvido contem a frase preservada
               (o que um RAG entregaria a LLM)

Uso:
    python src/ri/piloto_japeri.py
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import math
import argparse
import statistics
import unicodedata
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
from src.eval.protocolo import iterar_paginas, ordem_entrada, DIR_RESULTADOS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UF = "official_diary_rj_japeri"
DIR_PAGINAS = os.path.join(RAIZ, "data", "processed", "blocos_ri_japeri")
DIR_ATOS = os.path.join(RAIZ, "data", "raw", UF, "json_atos_japeri")
DIR_SAIDA = os.path.join(DIR_RESULTADOS, "ri_japeri")
JANELA, PASSO, TAM_FRASE, MIN_ALINHADAS = 100, 50, 12, 10
PARADAS = set("""a o e as os de da do das dos em no na nos nas um uma uns umas para por com sem que se
ao aos pela pelo pelas pelos ou nao sua seu suas seus este esta esse essa isto art lei""".split())
NOMES = {"aleatoria": "Ordem do detector (sem ordenar)", "fluxo_pdf": "Fluxo do PDF (extração comum)",
         "naive": "Ingênua (topo→base, esq.→dir.)", "xycut": "XY-cut (heurística de colunas)",
         "layoutlm": "LayoutLM: texto + layout 2D"}
CURTOS = {"aleatoria": "Ordem do detector", "fluxo_pdf": "Fluxo do PDF", "naive": "Ingênua",
          "xycut": "XY-cut", "layoutlm": "LayoutLM"}


def tokens(texto):
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", t)


def pct(x):
    return f"{100 * x:.1f}%".replace(".", ",")


def dec(x):
    return f"{x:.3f}".replace(".", ",")


class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        self.k1, self.b = k1, b
        self.dl = [len(d) for d in docs]
        self.media = sum(self.dl) / max(1, len(docs))
        self.inv = defaultdict(list)
        for i, d in enumerate(docs):
            for t, f in Counter(d).items():
                self.inv[t].append((i, f))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - len(ps) + 0.5) / (len(ps) + 0.5)) for t, ps in self.inv.items()}

    def escores(self, consulta):
        s = defaultdict(float)
        for t in set(consulta):
            for i, f in self.inv.get(t, ()):
                s[i] += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.media))
        return s


def indice_posicoes(toks):
    pos = defaultdict(list)
    for i, t in enumerate(toks):
        pos[t].append(i)
    return pos


def preservada(frase, texto_tok, posicoes=None):
    """A frase aparece no texto com >= MIN_ALINHADAS palavras alinhadas numa mesma posicao?"""
    posicoes = posicoes if posicoes is not None else indice_posicoes(texto_tok)
    vistos = set()
    for j, t in enumerate(frase):
        for i in posicoes.get(t, ()):
            o = i - j
            if o in vistos:
                continue
            vistos.add(o)
            if sum(1 for k, w in enumerate(frase) if 0 <= o + k < len(texto_tok) and texto_tok[o + k] == w) >= MIN_ALINHADAS:
                return True
    return False


def ordens_por_metodo(paginas, usar_layoutlm):
    ordens = {m: {} for m in ("aleatoria", "fluxo_pdf", "naive", "xycut")}
    for p in paginas:
        ids = [c["id"] for c in p["bounding_boxes"]]
        ordens["aleatoria"][p["page_id"]] = [ids[i] for i in ordem_entrada(p)]
        ordens["fluxo_pdf"][p["page_id"]] = p["ordens"]["stream"]
        ordens["naive"][p["page_id"]] = p["ordens"]["naive"]
        ordens["xycut"][p["page_id"]] = p["ordens"]["xycut"]
    if usar_layoutlm:
        import torch
        from src.models.layoutlm_ordem import LayoutLMOrdem, Codificador, prever, MODELO_BASE, DIR_MODELOS
        ckpt = os.path.join(DIR_MODELOS, "layoutlm.pt")
        if torch.cuda.is_available() and os.path.exists(ckpt):
            from transformers import AutoTokenizer
            cod = Codificador(AutoTokenizer.from_pretrained(MODELO_BASE))
            modelo = LayoutLMOrdem(MODELO_BASE).to("cuda")
            modelo.load_state_dict(torch.load(ckpt, map_location="cuda"))
            cod.pretokenizar(paginas)
            ordens["layoutlm"] = {p["page_id"]: pr for p, (pr, _) in zip(paginas, prever(modelo, cod, paginas, "cuda"))}
            del modelo
            torch.cuda.empty_cache()
        else:
            print("[!] LayoutLM ignorado (sem GPU ou sem checkpoint)")
    return ordens


def montar_consultas(atos, conj_pag, idf):
    """Consultas de tres tipos por ato; relevantes = paginas que contem o conteudo da consulta."""
    def relevantes(q, prop):
        alvo = set(q)
        return sorted(pid for pid, s in conj_pag.items() if len(alvo & s) >= prop * len(alvo))

    consultas, vistas = [], set()
    for a in atos:
        toks = tokens(a["texto"])
        titulo = tokens(a["texto"].split("\n")[0])[:20]
        candidatas = []
        if len(toks) >= 2 * TAM_FRASE:
            ini = max(len(titulo), 1)
            janelas = [toks[i:i + TAM_FRASE] for i in range(ini, len(toks) - TAM_FRASE + 1)]
            if janelas:
                candidatas.append(("frase", max(janelas, key=lambda w: sum(idf.get(t, 0) for t in w if t not in PARADAS)), 0.9))
        if len(titulo) >= 2:
            candidatas.append(("titulo", titulo, 0.9))
        termos = sorted({t for t in toks if len(t) >= 4 and t not in PARADAS and not t.isdigit()},
                        key=lambda t: (-idf.get(t, 0), t))[:8]
        if len(termos) >= 4:
            candidatas.append(("termos", termos, 0.75))
        for tipo, q, prop in candidatas:
            chave = (tipo, tuple(q))
            if chave in vistas:
                continue
            vistas.add(chave)
            rel = relevantes(q, prop)
            if rel:
                consultas.append({"tipo": tipo, "ato": a["id"], "tokens": q, "relevantes": rel})
    return consultas


def avaliar_ranking(ranking, relevantes):
    rel = set(relevantes)
    pos = next((k for k, pid in enumerate(ranking[:10], 1) if pid in rel), None)
    return {"rr": 1 / pos if pos else 0.0, "r1": 1.0 if pos == 1 else 0.0, "r5": 1.0 if pos and pos <= 5 else 0.0}


def figura(res, metodos):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.eval.figuras import estilo, salvar, virgula, COR, NEUTRO, TEXTO, TEXTO2
    cores = {**COR, "aleatoria": NEUTRO, "fluxo_pdf": TEXTO2}
    estilo()
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    ys = list(range(len(metodos)))[::-1]
    vals = [100 * res["metodos"][m]["fidelidade"] for m in metodos]
    ax.barh(ys, vals, color=[cores.get(m, NEUTRO) for m in metodos], height=0.62, zorder=3)
    for y, v in zip(ys, vals):
        ax.text(v + 0.8, y, f"{virgula(v, 1)}%", va="center", fontsize=9, color=TEXTO)
    ax.set_xlim(0, max(vals) * 1.15)
    ax.set_yticks(ys)
    ax.set_yticklabels([CURTOS[m] for m in metodos])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% das frases de 12 palavras dos atos que chegam intactas ao texto extraído")
    ax.set_title("Japeri (RJ): quanto do texto dos atos cada ordenação preserva")
    mrr = res["controle_pagina_inteira_mrr"]
    fig.text(0.01, -0.05, f"Achar a página certa não depende da ordem: MRR@10 de {virgula(min(mrr.values()), 2)} a "
             f"{virgula(max(mrr.values()), 2)} em todos os métodos (BM25, {res['paginas']} páginas).",
             fontsize=8.5, color=TEXTO2)
    salvar(fig, "fig8_ri_japeri.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sem-layoutlm", action="store_true")
    a = ap.parse_args()
    os.makedirs(DIR_SAIDA, exist_ok=True)

    paginas = list(iterar_paginas([UF], DIR_PAGINAS))
    if not paginas:
        sys.exit("[ERRO] rode antes: python src/data/extrator.py --ufs official_diary_rj_japeri --pdfs-por-uf 999 "
                 "--paginas-por-pdf 9999 --incluir-capa --saida data/processed/blocos_ri_japeri")
    atos = []
    for arq in sorted(glob.glob(os.path.join(DIR_ATOS, "*.json"))):
        tipo = os.path.basename(arq)[:-5]
        with open(arq, encoding="utf-8") as f:
            for k, x in enumerate(json.load(f)):
                atos.append({"id": f"{tipo}-{k}", "tipo": tipo, **x})
    pdfs = {p["arquivo"] for p in paginas}
    com_pdf = [x for x in atos if x.get("fonte") in pdfs]
    print(f"[*] {len(paginas)} paginas de {len(pdfs)} edicoes | {len(atos)} atos, {len(com_pdf)} com a edicao no acervo")

    textos = {p["page_id"]: {c["id"]: c["text"] for c in p["bounding_boxes"]} for p in paginas}
    conj_pag = {pid: set(tokens(" ".join(ts.values()))) for pid, ts in textos.items()}
    df = Counter(t for s in conj_pag.values() for t in s)
    idf = {t: math.log(len(conj_pag) / n) for t, n in df.items()}
    consultas = montar_consultas(com_pdf, conj_pag, idf)
    por_tipo = Counter(c["tipo"] for c in consultas)
    print(f"[*] {len(consultas)} consultas com pagina relevante: {dict(por_tipo)}")

    ordens = ordens_por_metodo(paginas, not a.sem_layoutlm)
    metodos = [m for m in ("aleatoria", "fluxo_pdf", "naive", "xycut", "layoutlm") if m in ordens]
    ids_pag = [p["page_id"] for p in paginas]

    # controle: pagina inteira como documento (o saco de palavras nao depende da ordem)
    bm_pag = BM25([tokens(" ".join(textos[pid].values())) for pid in ids_pag])
    controle = defaultdict(list)
    for c in consultas:
        s = bm_pag.escores(c["tokens"])
        ranking = [ids_pag[i] for i in sorted(s, key=lambda i: (-s[i], ids_pag[i]))]
        controle[c["tipo"]].append(avaliar_ranking(ranking, c["relevantes"])["rr"])

    res = {"paginas": len(paginas), "edicoes": len(pdfs), "atos": len(atos), "atos_com_edicao": len(com_pdf),
           "consultas": dict(por_tipo),
           "controle_pagina_inteira_mrr": {t: statistics.mean(v) for t, v in controle.items()}, "metodos": {}}
    fiel_por_metodo = {}
    for m in metodos:
        tok_pag = {pid: tokens(" ".join(textos[pid][i] for i in ordens[m][pid])) for pid in ids_pag}
        pos_pag = {pid: indice_posicoes(t) for pid, t in tok_pag.items()}
        trechos, dono = [], []
        for pid in ids_pag:
            t = tok_pag[pid]
            for ini in range(0, max(1, len(t) - JANELA + PASSO), PASSO):
                trechos.append(t[ini:ini + JANELA])
                dono.append(pid)
        bm = BM25(trechos)
        acum = defaultdict(lambda: defaultdict(list))
        fiel, contexto = [], []
        for c in consultas:
            s = bm.escores(c["tokens"])
            melhor = {}
            for i, v in s.items():
                if v > melhor.get(dono[i], (-1, None))[0]:
                    melhor[dono[i]] = (v, i)
            ranking = sorted(melhor, key=lambda pid: (-melhor[pid][0], pid))
            for k, v in avaliar_ranking(ranking, c["relevantes"]).items():
                acum[c["tipo"]][k].append(v)
            if c["tipo"] == "frase":
                fiel.append(any(preservada(c["tokens"], tok_pag[pid], pos_pag[pid]) for pid in c["relevantes"]))
                contexto.append(bool(ranking) and preservada(c["tokens"], trechos[melhor[ranking[0]][1]]))
        fiel_por_metodo[m] = fiel
        r = {"fidelidade": statistics.mean(fiel), "contexto_rag": statistics.mean(contexto), "trechos": len(trechos)}
        for tipo, d in acum.items():
            for k, v in d.items():
                r[f"{'mrr' if k == 'rr' else k}_trechos_{tipo}"] = statistics.mean(v)
        res["metodos"][m] = r
        print(f"  {m:<10} fidelidade {r['fidelidade']:.1%} | contexto RAG {r['contexto_rag']:.1%} | "
              f"MRR trechos: frase {r['mrr_trechos_frase']:.3f}, titulo {r.get('mrr_trechos_titulo', 0):.3f}, "
              f"termos {r.get('mrr_trechos_termos', 0):.3f}", flush=True)

    piso = res["metodos"]["aleatoria"]["fidelidade"]
    res["preservada_por_algum_metodo"] = statistics.mean(any(v) for v in zip(*fiel_por_metodo.values()))
    md = ["# Piloto de RI em Japeri: a ordem de leitura muda a busca?", "",
          f"{res['paginas']} páginas de {len(pdfs)} edições; {len(com_pdf)} dos {len(atos)} atos anotados têm a edição "
          "no acervo. Consultas com página relevante: " + ", ".join(f"{n} do tipo {t}" for t, n in por_tipo.items()) + ".", "",
          "**Controle (página inteira como documento):** MRR@10 = " +
          ", ".join(f"{dec(v)} ({t})" for t, v in res["controle_pagina_inteira_mrr"].items()) +
          ", idêntico para todos os métodos, porque o saco de palavras da página não depende da ordem.", "",
          f"**Frases preservadas por pelo menos um método:** {pct(res['preservada_por_algum_metodo'])}. O restante "
          "provavelmente difere entre o texto dos atos e a camada de texto do PDF (hifenização, OCR) ou atravessa páginas.", "",
          "| Método | Frases preservadas | Diferença para o piso | Contexto para RAG | MRR@10 frase | "
          "MRR@10 título | MRR@10 termos |", "|---|---:|---:|---:|---:|---:|---:|"]
    for m in metodos:
        r = res["metodos"][m]
        dif = f"{100 * (r['fidelidade'] - piso):+.1f}".replace(".", ",") + " p.p."
        md.append(f"| {NOMES[m]} | {pct(r['fidelidade'])} | {dif} | {pct(r['contexto_rag'])} | "
                  f"{dec(r['mrr_trechos_frase'])} | {dec(r.get('mrr_trechos_titulo', 0))} | "
                  f"{dec(r.get('mrr_trechos_termos', 0))} |")
    md += ["", "Frases preservadas: % das frases de 12 palavras dos atos que aparecem com ao menos 10 palavras "
           "alinhadas no texto da página produzido pelo método. Piso: blocos na ordem em que o detector os entrega. "
           "Contexto para RAG: % das consultas-frase em que o primeiro trecho devolvido contém a frase preservada. "
           "Busca por trechos: BM25 em janelas de 100 palavras (passo 50); a página vale o seu melhor trecho."]
    with open(os.path.join(DIR_SAIDA, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR_SAIDA, "resultado.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    figura(res, metodos)


if __name__ == "__main__":
    main()
