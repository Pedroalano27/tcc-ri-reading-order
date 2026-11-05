"""Prepara as 36 paginas do cruzado E008, sem abrir paginas do teste cego.

Embrulha o inventario, a ancora, o detector e o montador do E001. As paginas
novas usam a mesma renderizacao, extracao e representacao canonicas; apenas
o minimo de palavras muda para os 80 pedidos pelo protocolo deste lote.
Nao mede ordenacao nova, nao escreve em data/ e nao usa GPU ou Label Studio.
Caches atomicos permitem retomar o sorteio depois de queda sem ressorteio.

Da raiz: venv/Scripts/python.exe -B
orquestracao/analises/e008_montar_lote_cruzado.py [--max-minutos 20]
--conferir verifica somente os artefatos prontos, sem abrir PDFs.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import collections
import importlib.util
import json
import math
import os
import random
import re
import shutil
import subprocess
import time

from orquestracao.analises import e001_montar_teste_cego as base

OUT = RAIZ / "resultados/e008_anotacao/lote"
E001 = RAIZ / "resultados/e001_teste_cego"
HTML = RAIZ / "resultados/e008_anotacao/ferramenta/anotador.html"
SEMENTE = 20261104
UFS = tuple("official_diary_" + s for s in ("pr", "rr", "sc", "rn", "ce", "ma", "rj"))
VERSAO = "e008-lote-v1"
# Redireciona somente o modulo importado neste processo, nunca o arquivo E001.
# Os helpers originais verificam que toda escrita esta dentro desta nova OUT.
base.OUT = OUT
ler, gravar, sha, digest, exigir = base.ler, base.gravar, base.sha, base.digest, base.exigir


def caminho_seguro(p):
    """Nao enumera nem le tarefas lacradas ou dados do parceiro."""
    partes = Path(p).relative_to(RAIZ).parts
    return not any("labelstudio" in s.casefold() or "teste_cego" in s.casefold()
                   or s.casefold().startswith("e001_") or s == "ceia_datapolicy"
                   for s in partes) and not Path(p).resolve().is_relative_to(OUT)


def textos_seguros(pasta):
    for raiz, dirs, nomes in os.walk(pasta, followlinks=False):
        dirs[:] = sorted(d for d in dirs if caminho_seguro(Path(raiz) / d))
        for nome in sorted(nomes):
            p = Path(raiz) / nome
            if caminho_seguro(p) and not p.is_symlink() and p.suffix.casefold() in base.TEXTO:
                yield p


def inventario(raw):
    """Atualiza metadados do E001 usando seus regexes e cache, sem seus lotes."""
    anterior = ler(E001 / "pdfs_tocados.json")
    hashes_e001 = ler(E001 / "cache/hashes_pdfs.json")
    lacre = ler(base.LOCK)
    # O manifesto efetivo contem hashes de artefatos, nao nomes de PDFs.
    # Ler somente metadados do lacre e cache cobre escolhidos E candidatos.
    e001_nomes = {k.removeprefix("data/raw/") for k in hashes_e001}
    e001_nomes.update(lacre["pdfs_sha256"])
    excluidos = set(anterior["pdfs"]) | e001_nomes
    fontes = set()
    for raiz in ("data/golden", "data/diamond"):
        for pasta, dirs, nomes in os.walk(RAIZ / raiz, followlinks=False):
            dirs[:] = sorted(d for d in dirs if caminho_seguro(Path(pasta) / d))
            if "tarefas.jsonl" in nomes:
                fontes.add(Path(pasta) / "tarefas.jsonl")
    for pasta in (RAIZ / "data/processed").glob("blocos*"):
        fontes.update(textos_seguros(pasta) if pasta.is_dir() else [pasta])
    fontes.update(textos_seguros(RAIZ / "resultados"))
    cachepath = OUT / "cache/fontes_inventario.json"
    cache = ler(cachepath) if cachepath.exists() else ler(E001 / "cache/fontes_inventario.json")
    canon = {k.casefold(): k for k in raw}
    por_nome = collections.defaultdict(set)
    for k in raw:
        por_nome[Path(k).name.casefold()].add(k)
    fontes_sha = {}
    for i, p in enumerate(sorted(fontes)):
        st = p.stat()
        sig, nome = [st.st_size, st.st_mtime_ns], base.rel(p)
        item = cache.get(nome)
        if not item or item["assinatura"] != sig:
            refs = set()
            import codecs
            import hashlib
            h, sobra = hashlib.sha256(), ""
            with p.open("rb") as f:
                cabecalho = f.read(4)
                f.seek(0)
                # Alguns logs do PowerShell legado possuem BOM UTF-16/32.
                # Detectar pelo BOM evita perder nomes de PDFs nesse inventario.
                codificacao = ("utf-32" if cabecalho.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE))
                               else "utf-16" if cabecalho.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE))
                               else "utf-8-sig")
                dec = codecs.getincrementaldecoder(codificacao)(errors="strict")
                for bloco in iter(lambda: f.read(2**20), b""):
                    h.update(bloco)
                    texto = sobra + dec.decode(bloco)
                    candidatos = [m.group() for m in base.RX_REL.finditer(texto)]
                    candidatos += [m.group(1) for m in base.RX_JSON_PDF.finditer(texto)]
                    for s in candidatos:
                        s = base.decodificar(s)
                        inicio = re.search(r"official_diary_[a-zA-Z0-9_]+/", s, re.I)
                        if inicio:
                            k = s[inicio.start():]
                            refs.add(canon.get(k.casefold(), k))
                        elif "/" not in s:
                            refs.update(por_nome.get(s.casefold(), set()))
                    sobra = texto[-4096:]
                dec.decode(b"", final=True)
            st2 = p.stat()
            exigir(sig == [st2.st_size, st2.st_mtime_ns], f"Fonte mudou; retome: {nome}")
            item = {"assinatura": sig, "sha256": h.hexdigest(), "pdfs": sorted(refs)}
            cache[nome] = item
        excluidos.update(item["pdfs"])
        fontes_sha[nome] = {"sha256": item["sha256"], "assinatura": sig}
        if i % 1000 == 0:
            print(f"Inventario seguro: {i+1}/{len(fontes)} fontes", flush=True)
            gravar(cachepath, cache)
    gravar(cachepath, cache)
    hashes = {v["sha256"] for v in hashes_e001.values()}
    # Hash de PDF lacrado vem apenas dos metadados; nunca reabre esse PDF.
    hashes.update(lacre["pdfs_sha256"].values())
    for k in sorted(excluidos & raw.keys()):
        if "data/raw/" + k not in hashes_e001:
            hashes.add(sha(raw[k]))
    obj = {"pdfs": sorted(excluidos), "e001_pdfs": sorted(e001_nomes),
           "hashes_excluidos": sorted(hashes), "fontes": fontes_sha,
           "fontes_e001_sha256": {base.rel(p): sha(p) for p in (
               E001 / "pdfs_tocados.json", E001 / "cache/hashes_pdfs.json",
               E001 / "manifesto.json", base.LOCK)},
           "politica": "Metadados E001 + mencoes por nome em fontes locais seguras; homonimos e aliases binarios excluidos. Nenhuma tarefa/imagem E001 lida."}
    gravar(OUT / "cache/inventario.json", obj)
    return obj


class Montador(base.Montador):
    def __init__(self, e, u, m, raw, inv, limite):
        super().__init__(e, u, m, raw, inv, limite)
        self.proibidos = {s.casefold() for s in inv["pdfs"]}
        self.hashes_proibidos = set(inv["hashes_excluidos"])

    def permitir(self, k, numero=None):
        exigir(k in self.raw and k.split('/')[0] in UFS, f"Fora do universo: {k}")
        exigir(k.casefold() not in self.proibidos, f"PDF excluido: {k}")
        exigir(self.hash_pdf(self.raw[k]) not in self.hashes_proibidos, f"Alias excluido: {k}")
        if numero is not None:
            exigir(numero > 0, "Pagina zero proibida")

    def plano_e008(self):
        destino = OUT / "cache/plano.json"
        if destino.exists():
            plano = ler(destino)
            exigir(plano["receita"] == self.receita, "Receita mudou; nao misturar caches")
            return plano
        excluidos = self.proibidos
        filas = {}
        for uf in UFS:
            ks = [k for k in sorted(self.raw) if k.split('/')[0] == uf and k.casefold() not in excluidos]
            random.Random(f"{SEMENTE}-{uf}").shuffle(ks)
            filas[uf] = ks
        ordem = list(UFS)
        random.Random(SEMENTE).shuffle(ordem)
        plano = {"semente": SEMENTE, "receita": self.receita, "filas": filas,
                 "ordem_veiculos": ordem, "inventario_inicial_sha256": digest(self.inv)}
        gravar(destino, plano)
        return plano

    def pagina(self, k, numero):
        self.pausar()
        self.permitir(k, numero)
        pid = f"{k}#p{numero}"
        destino = OUT / "cache/paginas" / (base.chave(pid) + ".json")
        fp = digest([VERSAO, self.receita, self.hash_pdf(self.raw[k]), numero, 80])
        if destino.exists():
            obj = ler(destino)
            exigir(obj["fingerprint"] == fp, f"Cache divergente: {pid}")
            return obj
        with self.pdf_aberto(k) as doc:
            page = doc.pages[numero]
            try:
                ws = self.e.extrator.palavras_da_pagina(page)
                palavras = [[w["t"], w["x0"], w["top"], w["x1"], w["bottom"]] for w in ws]
                texto = " ".join(w[0] for w in palavras)
                ncid = len(re.findall(r"\(cid:[^)]*\)", texto))
                norm = re.sub(r"\(cid:[^)]*\)", "\ufffd", texto)
                taxa = (ncid + texto.count("\ufffd")) / max(1, len(re.sub(r"\s", "", norm)))
                obj = {"page_id": pid, "pdf": k, "pagina": numero, "fingerprint": fp,
                       "n_palavras": len(palavras), "fracao_ilegivel": taxa,
                       "elegivel": len(palavras) >= 80 and taxa <= .05}
                if not obj["elegivel"]:
                    gravar(destino, obj)
                    return obj
                dim = {"width": float(page.width), "height": float(page.height)}
                img = OUT / "cache/imagens" / (self.e.ac.chave(pid) + ".png")
                if not img.exists():
                    pi = page.to_image(resolution=self.e.layout.DPI)
                    exigir(max(abs(v) for v in pi.bbox[:2]) < .11 and
                           max(abs(pi.bbox[2]-page.width), abs(pi.bbox[3]-page.height)) < .11,
                           f"CropBox incompativel com P2: {pid}")
                    img.parent.mkdir(parents=True, exist_ok=True)
                    tmp = img.with_suffix(".png.tmp")
                    pi.original.convert("RGB").save(tmp, format="PNG")
                    os.replace(tmp, img)
            finally:
                page.close()
        uf, arquivo = k.split("/", 1)
        meta = {"page_id": pid, "uf": uf, "arquivo": arquivo, "pagina": numero, "dimensions": dim}
        regs, _ = self.detector(meta, self.contexto)
        dets = self.e.ls.dets({"ls3": regs}, "ls3")
        linhas, _ = self.u.representar({**meta, "palavras": palavras,
                                      "detector": {"modelo": "ls3", "regioes": dets}})
        ncol = linhas["colunas"]["n_estimado"]
        obj.update(meta, palavras=palavras, unidades=linhas["unidades"],
                   detector={"modelo": "ls3", "regioes": dets}, colunas=ncol,
                   tabela=any(r["classe"] == "tabela" and r["score"] >= .45 for r in regs),
                   estrato="3+" if ncol >= 3 else str(ncol))
        exigir(sorted(i for u in obj["unidades"] for i in u["ks"]) == list(range(len(palavras))),
               f"Cobertura canonica invalida: {pid}")
        gravar(destino, obj)
        return obj

    def triar(self, k):
        self.permitir(k)
        destino = OUT / "cache/triagem" / (base.chave(k) + ".json")
        if destino.exists():
            return ler(destino)
        import pymupdf
        with pymupdf.open(self.raw[k]) as doc:
            numeros = list(range(1, len(doc)))
        random.Random(f"{SEMENTE}-{k}-paginas").shuffle(numeros)
        paginas, tentativas = [], []
        try:
            for n in numeros[:12]:
                if any(abs(n - p["pagina"]) <= 1 for p in paginas):
                    continue
                p = self.pagina(k, n)
                tentativas.append({x: p[x] for x in ("page_id", "n_palavras", "elegivel")})
                if p["elegivel"]:
                    paginas.append({x: p[x] for x in ("page_id", "pdf", "uf", "pagina", "colunas", "estrato", "tabela", "n_palavras")})
                if len(paginas) == 2:
                    break
        finally:
            self.fechar_pdf()
        obj = {"pdf": k, "paginas": paginas, "tentativas": tentativas}
        gravar(destino, obj)
        return obj


def escolher(pool):
    """Sorteio condicionado apenas as quotas de layout, tabela, PDF e veiculo."""
    import numpy as np
    from scipy.optimize import milp, Bounds, LinearConstraint
    if any(sum(p["estrato"] == s for p in pool) < 12 for s in ("1", "2", "3+")):
        return None
    if sum(p["tabela"] for p in pool) < 12:
        return None
    n = len(pool)
    a, lo, hi = [], [], []
    for s in ("1", "2", "3+"):
        a.append([int(p["estrato"] == s) for p in pool]); lo.append(12); hi.append(12)
    a.append([int(p["tabela"]) for p in pool]); lo.append(12); hi.append(36)
    for k in sorted({p["pdf"] for p in pool}):
        a.append([int(p["pdf"] == k) for p in pool]); lo.append(0); hi.append(2)
    # Representar os sete veiculos, sem impor prevalencia ou quota igual por UF.
    for uf in UFS:
        a.append([int(p["uf"] == uf) for p in pool]); lo.append(1); hi.append(36)
    custos = [random.Random(f"{SEMENTE}-sorteio-{p['page_id']}").random() for p in pool]
    r = milp(np.array(custos), integrality=np.ones(n), bounds=Bounds(0, 1),
             constraints=LinearConstraint(np.array(a), lo, hi), options={"time_limit": 30})
    if not r.success:
        return None
    return [p for p, x in zip(pool, r.x) if x > .5]


def selecionar(m, plano):
    destino = OUT / "cache/selecao.json"
    if destino.exists():
        return ler(destino)
    pool, hashes_vistos = [], set()
    filas = plano["filas"]
    for rodada in range(max(map(len, filas.values()))):
        for uf in plano["ordem_veiculos"]:
            m.pausar()
            if rodada >= len(filas[uf]):
                continue
            k = filas[uf][rodada]
            m.permitir(k)
            h = m.hash_pdf(m.raw[k])
            if h in hashes_vistos:
                continue
            hashes_vistos.add(h)
            pool.extend(m.triar(k)["paginas"])
            c = collections.Counter(p["estrato"] for p in pool)
            print(f"Triagem E008: rodada {rodada+1}, {uf}; pool={len(pool)}, colunas={dict(c)}, tabelas={sum(p['tabela'] for p in pool)}", flush=True)
        # A regra de parada so consulta viabilidade das quotas, nunca a ordem.
        ps = escolher(pool)
        if ps is not None:
            obj = {"paginas": ps, "pool": pool, "rodadas": rodada + 1,
                   "regra": "Primeiro fim de rodada viavel; custo pseudoaleatorio fixo por pagina; MILP binario de quotas"}
            gravar(destino, obj)
            return obj
    raise ValueError("Acervo livre esgotado sem cumprir as quotas; nenhum lote final publicado")


def dividir(ps):
    """Fixa seis paginas de cada estrato em cada bloco, equilibrando tabelas."""
    import numpy as np
    from scipy.optimize import milp, Bounds, LinearConstraint
    n = len(ps)
    a, lo, hi = [], [], []
    for s in ("1", "2", "3+"):
        a.append([int(p["estrato"] == s) for p in ps]); lo.append(6); hi.append(6)
        total = sum(p["estrato"] == s and p["tabela"] for p in ps)
        a.append([int(p["estrato"] == s and p["tabela"]) for p in ps])
        lo.append(total // 2); hi.append(math.ceil(total / 2))
    total = sum(p["tabela"] for p in ps)
    a.append([int(p["tabela"]) for p in ps]); lo.append(total // 2); hi.append(math.ceil(total / 2))
    # Tambem reparte cada veiculo com diferenca de no maximo uma pagina.
    for uf in UFS:
        total = sum(p["uf"] == uf for p in ps)
        a.append([int(p["uf"] == uf) for p in ps]); lo.append(total // 2); hi.append(math.ceil(total / 2))
    custos = [random.Random(f"{SEMENTE}-bloco-{p['page_id']}").random() for p in ps]
    r = milp(np.array(custos), integrality=np.ones(n), bounds=Bounds(0, 1),
             constraints=LinearConstraint(np.array(a), lo, hi))
    exigir(r.success, "Nao foi possivel balancear os dois blocos; nao publicar")
    blocos = [[p for p, x in zip(ps, r.x) if (x > .5) == primeiro] for primeiro in (True, False)]
    for i, bloco in enumerate(blocos, 1):
        random.Random(f"{SEMENTE}-apresentacao-{i}").shuffle(bloco)
    return blocos


def exportar(m, blocos):
    from src.eval.protocolo import ordem_entrada
    from PIL import Image
    tarefas, defs = [], []
    for bi, ps in enumerate(blocos, 1):
        defs.append({"bloco": bi, "sequencia": "A→B" if bi == 1 else "B→A",
                     "sessao_1": "A" if bi == 1 else "B", "sessao_2": "B" if bi == 1 else "A",
                     "ordem_apresentacao": [p["page_id"] for p in ps]})
        for pos, meta in enumerate(ps, 1):
            m.pausar()
            m.permitir(meta["pdf"], meta["pagina"])
            p = ler(OUT / "cache/paginas" / (base.chave(meta["page_id"]) + ".json"))
            unidades = sorted(p["unidades"], key=lambda u: u["id"])
            ordem = ordem_entrada({"page_id": p["page_id"], "bounding_boxes": unidades})
            proposta = []
            for j, k in enumerate(ordem, 1):
                u = unidades[k]
                dim = p["dimensions"]
                x0, y0, x1, y1 = u["bbox"]
                # Mesmo recorte de coordenadas usado no exportador do E001.
                x0, y0 = max(0., min(x0, dim["width"]-1)), max(0., min(y0, dim["height"]-1))
                x1, y1 = min(dim["width"], max(x1, x0+1)), min(dim["height"], max(y1, y0+1))
                proposta.append({"id": f"p{j}", "classe": m.m.mapear_classe_diamond(u["tipo"]),
                                 "tipo_original": u["tipo"], "bbox": [x0, y0, x1, y1], "bbox_original": u["bbox"],
                                 "texto": u.get("text", ""), "palavras_cobertas": u["ks"],
                                 "origem": "extrator_sem_paragrafos", "score": float(u.get("score", 1.)), "alertas": []})
            n = len(tarefas) + 1
            t = {"n": n, **{k: p[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "palavras")},
                 "imagem": f"{n:03d}.jpg", "proposta": proposta, "blocos_v3": [], "detector": p["detector"],
                 "e008": {"bloco": bi, "posicao": pos, "estrato": p["estrato"], "tabela_ls3": p["tabela"]},
                 "stats": {"n_palavras": p["n_palavras"], "n_proposta": len(proposta), "estrato": p["estrato"],
                           "caixas_recortadas": sum(u["bbox"] != u["bbox_original"] for u in proposta),
                           "motivo_selecao": "Sorteio E008 condicionado a quotas, sem desempenho"},
                 "extrator_sha256": m.receita[base.rel(Path(m.e.extrator.__file__))]}
            dest = OUT / "img" / t["imagem"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                with Image.open(OUT / "cache/imagens" / (m.e.ac.chave(p["page_id"]) + ".png")) as im:
                    tmp = dest.with_suffix(".jpg.tmp")
                    im.convert("RGB").save(tmp, format="JPEG", quality=90)
                    os.replace(tmp, dest)
            tarefas.append(t)
    gravar(OUT / "tarefas.jsonl", "".join(json.dumps(t, ensure_ascii=False, allow_nan=False) + "\n" for t in tarefas))
    gravar(OUT / "blocos.json", {"semente": SEMENTE, "embaralhar_no_anotador": False,
                                 "intervalo_minimo_dias": 7, "blocos": defs})
    return tarefas


def validar(tarefas, inv, m):
    exigir(len(tarefas) == 36 and len({t["page_id"] for t in tarefas}) == 36, "Total/IDs invalidos")
    exigir(collections.Counter(t["e008"]["estrato"] for t in tarefas) == {"1": 12, "2": 12, "3+": 12}, "Estratos invalidos")
    exigir(sum(t["e008"]["tabela_ls3"] for t in tarefas) >= 12, "Menos de doze com tabela")
    pdfs = {t["page_id"].split("#p")[0] for t in tarefas}
    exigir(max(collections.Counter(t["page_id"].split("#p")[0] for t in tarefas).values()) <= 2, "Teto por PDF excedido")
    exigir(set(t["uf"] for t in tarefas) == set(UFS), "Veiculo ausente")
    sobre = {"lote_x_tocados_pdf": len({k.casefold() for k in pdfs} & {k.casefold() for k in inv["pdfs"]}),
             "lote_x_e001_pdf": len(pdfs & set(inv["e001_pdfs"])),
             "lote_x_excluidos_sha256": len({m.hash_pdf(m.raw[k]) for k in pdfs} & set(inv["hashes_excluidos"]))}
    exigir(not any(sobre.values()), f"Sobreposicao detectada: {sobre}")
    for bi in (1, 2):
        pp = [t for t in tarefas if t["e008"]["bloco"] == bi]
        exigir(len(pp) == 18 and collections.Counter(t["e008"]["estrato"] for t in pp) == {"1": 6, "2": 6, "3+": 6}, "Bloco desbalanceado")
    for t in tarefas:
        exigir(t["pagina"] > 0 and len(t["palavras"]) >= 80, "Pagina fora dos filtros")
        exigir(not any(k in t for k in ("ordem", "ordens", "referencia", "gt_w", "ordem_leitura")), "Ordem preenchida")
        exigir(sorted(i for u in t["proposta"] for i in u["palavras_cobertas"]) == list(range(len(t["palavras"]))), "Cobertura invalida")
        exigir(len({u["id"] for u in t["proposta"]}) == len(t["proposta"]), "ID de unidade repetido")
        W, H = t["dimensions"]["width"], t["dimensions"]["height"]
        exigir(all(len(w) == 5 and all(math.isfinite(v) for v in w[1:]) for w in t["palavras"]), "Palavra invalida")
        exigir(all(0 <= u["bbox"][0] < u["bbox"][2] <= W+.11 and
                    0 <= u["bbox"][1] < u["bbox"][3] <= H+.11 for u in t["proposta"]), "BBox invalida")
    return sobre


def validar_javascript(tarefas):
    """Executa o conversor original sem simular navegador ou renderizacao."""
    disponibilidade = {k: importlib.util.find_spec(k) is not None for k in ("playwright", "selenium")}
    node = shutil.which("node")
    exigir(node is not None, "Node ausente; requer validacao estatica adicional")
    fonte = HTML.read_text(encoding="utf-8")
    js = re.search(r"<script>([\s\S]*?)</script>", fonte).group(1)
    teste = r'''
const fs = require('fs'), vm = require('vm');
const dados = JSON.parse(fs.readFileSync(0, 'utf8'));
const ctx = {document:{addEventListener:()=>{}}, console, setInterval:()=>0, clearInterval:()=>{}};
vm.createContext(ctx); vm.runInContext(dados.js, ctx);
ctx.entrada = dados.tarefas;
const resultado = vm.runInContext(`(() => {
  app.modo = 'B — simplificada';
  const b = converterTarefasEntrada(entrada);
  app.modo = 'A — densa'; app.origemModoA = 'branco';
  const a = converterTarefasEntrada(entrada);
  return b.map((p,i)=>{
    const c = new Map();
    p.caixas.forEach(u=>u.palavras_cobertas.forEach(k=>c.set(k,(c.get(k)||0)+1)));
    return {page_id:p.page_id, palavras:p.palavras.length, unidades_b:p.caixas.length,
      unidades_a:a[i].caixas.length, ordem_vazia:p.ordem.length===0 && a[i].ordem.length===0,
      sem_cobertura:p.palavras.filter(w=>!c.has(w.id)).length,
      cobertura_multipla:p.palavras.filter(w=>(c.get(w.id)||0)>1).length};
  });
})()`, ctx);
process.stdout.write(JSON.stringify(resultado));
'''
    r = subprocess.run([node, "-e", teste], input=json.dumps({"js": js, "tarefas": tarefas}, ensure_ascii=False),
                       capture_output=True, text=True, encoding="utf-8", check=True)
    rows = json.loads(r.stdout)
    exigir(len(rows) == 36 and all(p["unidades_b"] > 0 and p["unidades_a"] == 0 and
                                 p["ordem_vazia"] and p["sem_cobertura"] == 0 for p in rows), "Conversor JS incompativel")
    from PIL import Image
    for t in tarefas:
        with Image.open(OUT / "img" / t["imagem"]) as im:
            im.verify()
    navegador = validar_navegador(tarefas[:2], node)
    obj = {"playwright_selenium": disponibilidade, "navegador_headless": navegador,
           "metodo": "Leitura do contrato + conversor original executado em Node/vm; JPEGs verificados com PIL",
           "html_sha256": sha(HTML), "paginas": rows,
           "limite": "Ensaio de carregamento nao valida precisao do cronometro, autosave, acoes ou exports. Cobertura geometrica nao substitui IDs canonicos."}
    gravar(OUT / "cache/validacao_anotador.json", obj)
    return obj


def validar_navegador(tarefas, node):
    """Abre o HTML original em Chrome headless usando CDP local do Node."""
    candidatos = [Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
                  Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe"]
    navegador = next((p for p in candidatos if p.exists()), None)
    if navegador is None:
        return {"executado": False, "motivo": "Chrome/Edge nao encontrados nos caminhos padrao"}
    teste = r'''
const fs = require('fs'), cp = require('child_process'), path = require('path');
const dados = JSON.parse(fs.readFileSync(0,'utf8'));
const dormir = ms => new Promise(r=>setTimeout(r,ms));
async function executar() {
  const perfil = path.join(dados.cache, 'perfil-'+Date.now());
  fs.mkdirSync(perfil,{recursive:true});
  const proc = cp.spawn(dados.bin, ['--headless=new','--disable-gpu','--no-first-run',
    '--no-default-browser-check','--disable-background-networking','--disable-sync',
    '--disable-component-update','--remote-debugging-address=127.0.0.1',
    '--remote-debugging-port=0','--user-data-dir='+perfil,dados.html],
    {windowsHide:true,stdio:['ignore','ignore','pipe']});
  let diagnostico=''; proc.stderr.on('data',b=>{diagnostico=(diagnostico+b.toString()).slice(-10000);});
  let ws, cdp;
  try {
    let porta;
    for (let i=0;i<150;i++) {
      if(proc.exitCode!==null) throw Error('Chrome encerrou ('+proc.exitCode+'): '+diagnostico);
      const p = path.join(perfil,'DevToolsActivePort');
      if (fs.existsSync(p)) { porta=fs.readFileSync(p,'utf8').split('\n')[0]; break; }
      await dormir(100);
    }
    if (!porta) throw Error('Chrome nao publicou a porta CDP');
    let alvo;
    for (let i=0;i<100;i++) {
      const abas = await (await fetch('http://127.0.0.1:'+porta+'/json/list')).json();
      alvo = abas.find(a=>a.type==='page' && a.url.startsWith(dados.html));
      if (alvo) break;
      await dormir(100);
    }
    if (!alvo) throw Error('Aba do anotador nao encontrada');
    ws = new WebSocket(alvo.webSocketDebuggerUrl);
    await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});
    let id=0; const pendentes=new Map(), erros=[];
    ws.addEventListener('message',ev=>{
      const m=JSON.parse(ev.data);
      if(m.method==='Runtime.exceptionThrown') erros.push(m.params.exceptionDetails.text);
      if(m.id && pendentes.has(m.id)) {
        const p=pendentes.get(m.id); pendentes.delete(m.id);clearTimeout(p.timer);
        m.error?p.rej(Error(JSON.stringify(m.error))):p.res(m.result);
      }
    });
    cdp=(method,params={})=>new Promise((res,rej)=>{
      const k=++id, timer=setTimeout(()=>{pendentes.delete(k);rej(Error('Timeout '+method));},7000);
      pendentes.set(k,{res,rej,timer});ws.send(JSON.stringify({id:k,method,params}));
    });
    const avaliar=async expression=>{
      const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
      if(r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
      return r.result.value;
    };
    await cdp('Runtime.enable');
    for(let i=0;i<100;i++) {
      if(await avaliar('typeof carregarArquivoTarefas === "function" && document.readyState === "complete"')) break;
      await dormir(100);
    }
    await avaliar(`app.embaralhar=false; app.modo='B — simplificada';
      app.imagensLocais=new Map(${JSON.stringify(dados.imagens)});
      fecharModalSessao(); renderizarPaletaClasses();
      carregarArquivoTarefas(${JSON.stringify(JSON.stringify(dados.tarefas))}); true`);
    const paginas=[];
    for(let i=0;i<2;i++) {
      await avaliar('mudarPagina('+i+'); true');
      const res=await avaliar(`new Promise((resolve,reject)=>{
        let tentativas=0; const conferir=()=>{
          const im=document.getElementById('imagem-pagina');
          if(im.complete && im.naturalWidth>0) resolve({
            page_id:paginaAtual().page_id, palavras:paginaAtual().palavras.length,
            unidades_b:paginaAtual().caixas.length,
            caixas_svg:document.getElementById('camada-caixas').childElementCount,
            largura_imagem:im.naturalWidth, altura_imagem:im.naturalHeight,
            tarefas:app.tarefas.length, ordem_vazia:paginaAtual().ordem.length===0});
          else if(++tentativas>100) reject(Error('Imagem nao carregou'));
          else setTimeout(conferir,50);
        }; conferir();
      })`);
      paginas.push(res);
    }
    await avaliar(`app.modo='A — densa';app.origemModoA='branco';
      renderizarPaletaClasses();carregarArquivoTarefas(${JSON.stringify(JSON.stringify(dados.tarefas))});true`);
    for(let i=0;i<2;i++) {
      await avaliar('mudarPagina('+i+');true');
      paginas[i].unidades_a=await avaliar('paginaAtual().caixas.length');
    }
    const versao=await cdp('Browser.getVersion');
    if(erros.length) throw Error(JSON.stringify(erros));
    process.stdout.write(JSON.stringify({executado:true,metodo:'Chrome headless via CDP local, HTML original',
      navegador:versao.product,paginas,erros_javascript:erros}));
  } finally {
    if(cdp) await cdp('Browser.close').catch(()=>{});
    if(ws) ws.close();
    await dormir(200);
    if(proc.exitCode===null) proc.kill();
  }
}
executar().catch(e=>{process.stderr.write(String(e.stack));process.exitCode=1;});
'''
    dados = {"bin": str(navegador), "cache": str(OUT / "cache/navegador"), "html": HTML.as_uri(),
             "tarefas": tarefas, "imagens": [[t["imagem"], (OUT / "img" / t["imagem"]).as_uri()] for t in tarefas]}
    r = subprocess.run([node, "-e", teste], input=json.dumps(dados, ensure_ascii=False),
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode != 0:
        # Falha de inicializacao do navegador nao invalida a alternativa por
        # leitura de codigo/conversor prevista na tarefa. Nunca desativa sandbox.
        return {"executado": False, "tentado": True, "binario": str(navegador),
                "erro": r.stderr, "alternativa": "Contrato e conversor original em Node/vm, nas 36 paginas"}
    obj = json.loads(r.stdout)
    exigir(len(obj["paginas"]) == 2 and all(p["tarefas"] == 2 and p["unidades_b"] > 0 and
            p["caixas_svg"] > 0 and p["unidades_a"] == 0 and p["ordem_vazia"] for p in obj["paginas"]),
           f"Carga visual incompativel: {obj}")
    return obj


def relatorio(anc, tarefas, inv, selecao, sobre, val):
    f = lambda x: base.fmt(x)
    navegador = val["navegador_headless"]
    headless = (f"Concluído no {navegador.get('navegador')}, com {len(navegador['paginas'])} páginas."
                if navegador["executado"] else "Não concluído neste ambiente: " +
                navegador.get("erro", navegador.get("motivo", "indisponível")).splitlines()[0] +
                ". Detalhes da tentativa em `cache/validacao_anotador.json`; foi usada a alternativa de validação pelo código.")
    ls = ["# E008 — Lote de anotação densa × simplificada", "",
          f"Lote pronto: **{len(tarefas)} páginas**, semente **{SEMENTE}**. Este preparo não mede as hipóteses H6–H9.", "",
          f"Âncora reproduzida com os módulos originais: τ **{f(anc['tau'])}** e **{f(anc['quebras'])}** quebras/página, em {anc['paginas']} páginas do golden_v4 (`ancora.json`).", "",
          "## Composição", "", "| Bloco | Ordem entre sessões | 1 coluna | 2 colunas | 3+ colunas | Tabela ls3 |", "|---|---|---:|---:|---:|---:|"]
    for bi in (1, 2):
        ps = [t for t in tarefas if t["e008"]["bloco"] == bi]
        c = collections.Counter(t["e008"]["estrato"] for t in ps)
        ls.append(f"| {bi} | {'A→B' if bi==1 else 'B→A'} | {c['1']} | {c['2']} | {c['3+']} | {sum(t['e008']['tabela_ls3'] for t in ps)} |")
    ls += ["", "| Veículo | PDFs | Páginas | 1 coluna | 2 colunas | 3+ colunas | Tabela ls3 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for uf in UFS:
        ps = [t for t in tarefas if t["uf"] == uf]
        c = collections.Counter(t["e008"]["estrato"] for t in ps)
        ls.append(f"| {uf} | {len({t['arquivo'] for t in ps})} | {len(ps)} | {c['1']} | {c['2']} | {c['3+']} | {sum(t['e008']['tabela_ls3'] for t in ps)} |")
    pdfs = {t['page_id'].split('#p')[0] for t in tarefas}
    ls += ["", f"Total: {len(pdfs)} PDFs; {sum(t['e008']['tabela_ls3'] for t in tarefas)} páginas com tabela; mínimo observado de {min(len(t['palavras']) for t in tarefas)} palavras. Nenhuma página zero; no máximo duas páginas, não consecutivas, por PDF.", "",
           "## Exclusão e auditoria", ""]
    ls += [f"- {k}: **{v}**." for k, v in sobre.items()]
    ls += ["", f"Inventário: {len(inv['pdfs'])} nomes excluídos; {len(inv['fontes'])} fontes locais seguras conferidas; {len(inv['e001_pdfs'])} nomes do cache/lacre E001 excluídos conservadoramente. Evidência em `cache/inventario.json`.", "",
           "O manifesto real do E001 não tem uma lista de PDFs: contém hashes de artefatos. Foram usados somente os nomes e hashes do inventário, do cache de hashes e dos metadados do lacre. Isso exclui também PDFs candidatos não escolhidos pelo E001. Nenhuma tarefa, imagem ou conteúdo de página do teste cego foi aberto. O SHA-256 do manifesto foi registrado, sem abrir os artefatos que ele referencia.", "",
           "## Sorteio e representação", "",
           f"Listas de PDFs permutadas por veículo com a semente {SEMENTE}; veículos percorridos em rodadas. Até doze páginas internas em ordem sorteada por PDF, parando em duas elegíveis não consecutivas. Filtro: pelo menos 80 palavras e no máximo 5% de glifos ilegíveis, como no E001. O primeiro fim de rodada com quotas viáveis encerra o pool: {len(selecao['pool'])} páginas candidatas após {selecao['rodadas']} rodadas. Seleção binária com custo pseudoaleatório fixo por página, quotas exatas por coluna, mínimo de tabelas, máximo por PDF e presença dos sete veículos. Não é uma amostra aleatória simples do acervo; probabilidades de inclusão não foram estimadas.", "",
           "As colunas são a estimativa automática de calhas da representação canônica, não uma classificação humana. Tabela ls3 significa detecção com score ≥ 0,45; pode incluir falsos positivos/negativos. O detector e a renderização são os mesmos do E001 (CPU, offline). As linhas e átomos vêm de `unidades_sem_caixas.representar`, sem parágrafos; todas as palavras têm um único dono pelos IDs canônicos. `proposta` é embaralhada por `ordem_entrada` com `random.Random(f\"entrada-{page_id}\")`; não há ordem humana/automática pré-preenchida.", "",
           f"Coordenadas de {sum(t['stats']['caixas_recortadas'] for t in tarefas)} propostas foram recortadas aos limites da página com a mesma regra do E001. As coordenadas anteriores ficam em `bbox_original`; palavras e IDs canônicos são preservados. A cobertura efetiva após o recorte também foi conferida pelo conversor original do anotador.", "",
           "Cada bloco tem seis páginas de cada estrato. A divisão equilibra tabelas por estrato e no total, além das contagens por veículo, com diferença máxima de uma quando o total é ímpar. A ordem de apresentação está em `blocos.json` e nas linhas do JSONL: primeiro bloco 1, depois bloco 2. Não reembaralhar na interface.", "",
           "## Uso pelo Pedro", "",
           "1. Abra `../ferramenta/anotador.html`. Confira o nome Pedro. Crie cópias temporárias dos dois blocos com o comando abaixo; o lote canônico permanece intacto.", "",
           "```powershell", '$e008 = "resultados/e008_anotacao/lote/tarefas.jsonl"',
           'Get-Content -LiteralPath $e008 -Encoding UTF8 | Select-Object -First 18 | Set-Content -Encoding UTF8 "$env:TEMP/e008_bloco_1.jsonl"',
           'Get-Content -LiteralPath $e008 -Encoding UTF8 | Select-Object -Last 18 | Set-Content -Encoding UTF8 "$env:TEMP/e008_bloco_2.jsonl"', "```", "",
           "2. **Sessão 1:** bloco 1 no modo **A — Densa**, depois bloco 2 no modo **B — Simplificada**. No A, selecione origem **em branco**: desenhar e classificar as caixas densas do zero. No B, corrigir linhas/átomos automáticos e marcar estruturas/ruído. Nos dois, anotar a ordem de leitura.",
           f"3. Configure a semente {SEMENTE} e **desmarque embaralhar**. Selecione o arquivo temporário do bloco em Abrir Tarefas e carregue a pasta `lote/img` em Pasta Imagens. A ordem já foi sorteada. O modo é global, não muda por metadado de tarefa.",
           "4. Exporte a sessão ao terminar cada bloco; identifique externamente sessão, bloco, modo e data. Exporte antes de trocar modo. **Depois de configurar cada novo modo, reimporte o JSONL original do bloco**, pois a troca de modo reconverte o estado normalizado da ferramenta e pode perder as propostas. Não continue a anotação anterior no outro modo.",
           "5. **Sessão 2, pelo menos sete dias depois (preferencialmente sete a dez):** bloco 1 no **B**, bloco 2 no **A**; mesma ordem dentro dos blocos, reimportando os dados iniciais e sem consultar o resultado da sessão 1. Use sempre A em branco e B com proposta. Exporte separadamente cada bloco. A análise principal usa só a primeira sessão de cada página; a segunda mede os efeitos cruzados/memória.",
           "6. Pause o cronômetro em interrupções e registre os pulos. Preserve os exports originais. Nenhuma anotação foi criada por este preparo.", "",
           "A escolha operacional A em branco usa uma opção existente do anotador e evita tratar linhas automáticas como caixas densas. Assim, o custo compara desenho denso do zero com correção de proposta simplificada: não isola apenas a taxonomia, e não representa uma condição densa com caixas de parágrafo pré-anotadas.", "",
           "## Validação do anotador", "",
           f"Playwright instalado: {val['playwright_selenium']['playwright']}; Selenium instalado: {val['playwright_selenium']['selenium']}. Nenhuma biblioteca foi instalada. Ensaio headless: {headless}", "",
           f"O código do leitor foi inspecionado (`carregarArquivoTarefas`, `converterTarefasEntrada`, `normalizarPalavras`, `calcularPalavrasCobertas`). Seu JavaScript original foi executado em Node/vm para **{len(val['paginas'])} páginas**, incluindo as duas primeiras: modo B carrega propostas, modo A em branco inicia sem caixas, ambos sem ordem preenchida. Todos os JPEGs foram decodificados/verificados com PIL. Nenhuma palavra ficou sem cobertura no conversor geométrico.", "",
           f"O conversor do anotador recalcula pertencimento por centro da palavra e tolerância geométrica, ignorando os IDs fornecidos: {sum(p['cobertura_multipla'] for p in val['paginas'])} palavras tiveram cobertura por mais de uma proposta. Isso é um diagnóstico da interface; os IDs canônicos da representação não têm perda/duplicação. Não demonstra H9 nem valida exportação após edição. Detalhes por página em `cache/validacao_anotador.json`.", "",
           "Quando disponível, o ensaio headless abre o HTML original, importa duas páginas, navega entre elas e confere imagens decodificadas, elementos SVG, propostas no modo B e início em branco no A, sem erros JavaScript. Não valida precisão do cronômetro, persistência do autosave, ações ou exports no navegador. Recomenda-se também o ensaio manual descrito no LEIAME, sem usar seus tempos como anotação experimental e recarregando os dados iniciais antes da sessão real.", "",
           "## Bancadas e limites", "", "| Bancada | Uso neste preparo |", "|---|---|",
           "| golden_v4 | Reprodução da âncora, sem ajuste |",
           "| golden_v3_novo | Não avaliada; já consultada em rodadas anteriores |",
           "| teste silver CE/MA/RJ | Não avaliado; PDFs identificados excluídos |", "",
           "Não há referência humana nas páginas novas. Δ contra a regra, IC95 por veículo, Wilcoxon por veículo, páginas melhor/igual/pior e reparos/regressões de sucessores não se aplicam ao preparo: serão calculados após anotação pela régua existente, mantendo as três bancadas separadas. Não há alegação de qualidade nem tempo humano novo.", "",
           "Limitações: estratos e tabelas automáticos, acervo condicionado às exclusões e ao texto digital (sem OCR), páginas quase vazias/capas excluídas, anotador único e possível memória entre sessões. A ausência de uso anterior é verificável nos artefatos locais inventariados, sem garantir ausência de consulta humana não registrada. Cartão E008 não existia em `experimentos/cards/` nesta execução; escopo extraído da tarefa e do plano. Nenhum arquivo pré-existente ou anotação humana foi alterado. Nenhuma escrita em data/, leitura de dados do parceiro, uso de GPU ou publicação.", "",
           "## Retomar ou conferir", "", "```powershell",
           "venv/Scripts/python.exe -B orquestracao/analises/e008_montar_lote_cruzado.py",
           "venv/Scripts/python.exe -B orquestracao/analises/e008_montar_lote_cruzado.py --conferir", "```", "",
           "Depois do manifesto final, a execução padrão só confere os hashes, sem ressorteio ou reextração. Todos os números deste relatório são produzidos pelo script a partir dos artefatos da execução. Hashes de PDFs, código, tarefas, imagens, blocos e relatório estão em `manifesto.json`.", ""]
    gravar(OUT / "RELATORIO.md", "\n".join(ls))


def conferir():
    manifesto = ler(OUT / "manifesto.json")
    for k, h in manifesto["artefatos_sha256"].items():
        exigir(sha(OUT / k) == h, f"Artefato divergente: {k}")
    exigir(sha(HTML) == manifesto["anotador_sha256"], "Anotador mudou desde a verificacao")
    exigir(sha(base.LOCK) == manifesto["lock_sha256"], "Lacre E001 mudou")
    print("E008: hashes conferidos; nenhuma pagina/PDF foi aberto.", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--revalidar-anotador", action="store_true")
    ap.add_argument("--max-minutos", type=float, default=0)
    args = ap.parse_args()
    exigir(args.max_minutos >= 0, "Tempo negativo")
    with base.trava():
        if args.revalidar_anotador:
            conferir()
            tarefas = [json.loads(s) for s in (OUT / "tarefas.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
            manifesto = ler(OUT / "manifesto.json")
            val = validar_javascript(tarefas)
            relatorio(ler(OUT / "ancora.json"), tarefas, ler(OUT / "cache/inventario.json"),
                      ler(OUT / "cache/selecao.json"), manifesto["sobreposicao"], val)
            for k in ("RELATORIO.md", "cache/validacao_anotador.json"):
                manifesto["artefatos_sha256"][k] = sha(OUT / k)
            manifesto["script_sha256"] = sha(Path(__file__))
            manifesto["e001_script_sha256"] = sha(Path(base.__file__))
            gravar(OUT / "manifesto.json", manifesto)
            conferir()
            return
        if args.conferir or (OUT / "manifesto.json").exists():
            conferir()
            return
        inicio = time.monotonic()
        e, b, u, m = base.importar()
        anc = base.ancora(e, b)
        raw = base.catalogo_raw()
        # Com selecao persistida, nao reabre paginas nem refaz o sorteio.
        # O inventario atualizado obrigatorio continua abaixo, antes do manifesto.
        inv = (ler(OUT / "cache/inventario.json") if (OUT / "cache/selecao.json").exists()
               and (OUT / "cache/inventario.json").exists() else inventario(raw))
        montador = Montador(e, u, m, raw, inv, inicio + args.max_minutos*60 if args.max_minutos else None)
        try:
            plano = montador.plano_e008()
            selecao = selecionar(montador, plano)
            blocos = dividir(selecao["paginas"])
            tarefas = exportar(montador, blocos)
            # Mudancas concorrentes de outras fontes nao podem contaminar a selecao.
            inv = inventario(raw)
            sobre = validar(tarefas, inv, montador)
            val = validar_javascript(tarefas)
            relatorio(anc, tarefas, inv, selecao, sobre, val)
            nomes = ["tarefas.jsonl", "blocos.json", "RELATORIO.md", "ancora.json",
                     "cache/inventario.json", "cache/selecao.json", "cache/plano.json", "cache/validacao_anotador.json"]
            artefatos = {k: sha(OUT / k) for k in nomes}
            artefatos.update({base.rel(p).removeprefix(base.rel(OUT) + "/"): sha(p) for p in sorted((OUT / "img").glob("*.jpg"))})
            manifesto = {"versao": VERSAO, "semente": SEMENTE, "sobreposicao": sobre,
                         "pdfs_sha256": {k: montador.hash_pdf(raw[k]) for k in sorted({p["pdf"] for p in selecao["paginas"]})},
                         "receita_sha256": montador.receita, "script_sha256": sha(Path(__file__)),
                         "e001_script_sha256": sha(Path(base.__file__)),
                         "anotador_sha256": sha(HTML), "lock_sha256": sha(base.LOCK),
                         "artefatos_sha256": artefatos, "paginas": len(tarefas),
                         "colunas": dict(collections.Counter(t["e008"]["estrato"] for t in tarefas)),
                         "tabelas": sum(t["e008"]["tabela_ls3"] for t in tarefas)}
            gravar(OUT / "manifesto.json", manifesto)
            conferir()
            print(json.dumps({k: manifesto[k] for k in ("paginas", "colunas", "tabelas", "sobreposicao")}, ensure_ascii=False), flush=True)
        except base.Pausa as exc:
            print(str(exc), flush=True)
        finally:
            montador.fechar_pdf()


if __name__ == "__main__":
    main()
