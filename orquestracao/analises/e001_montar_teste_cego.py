"""Monta o E001 com exclusao por PDF, estratos e lacre imutavel, so em CPU.

Importa a regua existente para reproduzir a ancora antes do inventario. Reusa
representar() e detector() do exportador sem caixas, isolando as escritas em
resultados/e001_teste_cego. Nao avalia ordenadores nas paginas novas, nao le
Label Studio, nao escreve em data/ e nao altera arquivos de outros agentes.

Da raiz: venv/Scripts/python.exe -B orquestracao/analises/e001_montar_teste_cego.py
--somente-inventario para depois do inventario; --max-minutos permite pausar.
Repetir o comando retoma caches atomicos. Depois do lacre, so verifica hashes
de arquivos e metadados: nenhuma pagina lacrada e reaberta ou reextraida.
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
import codecs
import collections
import datetime as dt
import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import time
import types
from contextlib import contextmanager

OUT = RAIZ / "resultados/e001_teste_cego"
LOCK = RAIZ / "experimentos/TESTE_CEGO.lock"
RAW = RAIZ / "data/raw"
SEMENTES = {"teste_cego": 20261102, "desenvolvimento": 20261103}
VERSAO = "e001-v1"
TEXTO = {".json", ".jsonl", ".ndjson", ".txt", ".csv", ".tsv", ".md", ".html", ".log", ".yaml", ".yml"}
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", YOLO_OFFLINE="true",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4", TOKENIZERS_PARALLELISM="false")


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def rel(p):
    return Path(p).resolve().relative_to(RAIZ).as_posix()


def ler(p):
    with Path(p).open(encoding="utf-8") as f:
        return json.load(f)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(2**20), b""):
            h.update(b)
    return h.hexdigest()


def chave(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def alocar(total, capacidades, semente, exigir_todos=True):
    """Distribui o total o mais igualmente possivel, respeitando o acervo."""
    ordem = sorted(capacidades)
    random.Random(semente).shuffle(ordem)
    exigir(sum(capacidades.values()) >= total, f"Capacidade insuficiente: {capacidades}; meta {total}")
    metas = dict.fromkeys(ordem, 0)
    for _ in range(total):
        uf = min((u for u in ordem if metas[u] < capacidades[u]), key=lambda u: metas[u])
        metas[uf] += 1
    if exigir_todos:
        exigir(all(metas.values()), f"Nao foi possivel representar todos os veiculos: {metas}")
    return metas


def gravar(p, obj):
    """Publica atomicamente somente saidas deste experimento."""
    p = Path(p).resolve()
    exigir(p.is_relative_to(OUT.resolve()), f"Saida fora do escopo: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


@contextmanager
def trava():
    """Trava de processo liberada pelo sistema inclusive depois de queda."""
    p = OUT / "cache/execucao.lock"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a+b") as f:
        f.seek(0, 2)
        if not f.tell():
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)


def importar():
    from orquestracao.analises import erros_ponta_a_ponta as e
    from orquestracao.analises import bancada_ordenadores as b
    from orquestracao.analises import unidades_sem_caixas as u
    from orquestracao.analises import montar_lote_sem_paragrafos as m
    # O importador legado define a raiz; restringir configuracoes novas ao E001.
    os.environ["YOLO_CONFIG_DIR"] = str(OUT / "cache/config")
    return e, b, u, m


def ancora(e, b):
    """Chama o ordenador e a metrica originais apenas no golden_v4."""
    fonte = b.UNIDADES / "bancadas/golden_v4.jsonl"
    deps = [Path(x.__file__) for x in (e, b, e.o, e.j, e.ls, e.ri)]
    deps += [RAIZ / s for s in ("src/eval/metrics.py", "src/eval/protocolo.py")]
    fontes = {rel(p): sha(p) for p in deps + [fonte]}
    fp = digest(fontes)
    rows = []
    for obj, p in b.paginas("golden_v4", "linhas"):
        cache = OUT / "cache/ancora" / (chave(p["page_id"]) + ".json")
        if cache.exists() and ler(cache).get("fingerprint") == fp:
            row = ler(cache)
        else:
            ordem, _ = b.prever(p, obj["palavras"], "regra_colunas")
            exp = b.expansoes(obj, p)
            seq = [k for uid in ordem for k in exp[uid]]
            med = e.medir(b.referencia(obj, p), seq, [], {}, "P0")
            row = {"fingerprint": fp, "page_id": p["page_id"],
                   **{k: med[k] for k in ("tau", "quebras", "fid12", "sucessor_linhas")}}
            gravar(cache, row)
        rows.append(row)
    res = {"paginas": len(rows), "fontes_sha256": fontes,
           "tau": statistics.mean(r["tau"] for r in rows),
           "quebras": statistics.mean(r["quebras"] for r in rows)}
    res["aprovada"] = (len(rows) == 44 and abs(res["tau"] - .985948) < .0000005
                       and abs(res["quebras"] - 6.045455) < .0000005)
    gravar(OUT / "ancora.json", res)
    exigir(res["aprovada"], f"PARE: ancora obrigatoria nao reproduzida: {res}")
    print(f"Ancora reproduzida: tau={res['tau']:.6f}; quebras={res['quebras']:.6f}", flush=True)
    return res


def arquivos_texto(base):
    """Nao atravessa o experimento atual nem pastas do parceiro."""
    proibidas = {OUT.resolve(), (RAIZ / "resultados/ceia_datapolicy").resolve(),
                 (RAIZ / "data/labelstudio").resolve()}
    for pasta, dirs, nomes in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if (Path(pasta) / d).resolve() not in proibidas
                          and "labelstudio" not in d.casefold())
        for nome in sorted(nomes):
            p = Path(pasta) / nome
            if p.suffix.casefold() in TEXTO and not p.is_symlink():
                yield p


def catalogo_raw():
    return {p.relative_to(RAW).as_posix(): p
            for p in sorted(RAW.glob("*/*")) if p.is_file() and p.suffix.casefold() == ".pdf"} | {
            p.relative_to(RAW).as_posix(): p for uf in sorted(RAW.iterdir()) if uf.is_dir()
            for p in sorted(uf.rglob("*.pdf")) if p.is_file()}


# Captura metadados sem desserializar palavras, ordens ou tensores das predicoes.
RX_REL = re.compile(r'official_diary_[a-zA-Z0-9_]+(?:/|\\\\|\\)(?:\\.|[^"\\\r\n]){1,1500}?\.pdf', re.I)
RX_JSON_PDF = re.compile(r'"((?:\\.|[^"\\\r\n]){1,1600}?\.pdf)(?:#p\d+)?"', re.I)


def decodificar(s):
    try:
        return json.loads('"' + s + '"').replace("\\", "/")
    except (ValueError, json.JSONDecodeError):
        return s.replace("\\", "/")


def inventario(raw):
    """Varre metadados em blocos, com cache e proveniencia por arquivo fonte."""
    fontes = set()
    for raiz in ("data/golden", "data/diamond"):
        fontes.update((RAIZ / raiz).rglob("tarefas.jsonl"))
    for pasta in (RAIZ / "data/processed").glob("blocos*"):
        fontes.update(arquivos_texto(pasta) if pasta.is_dir() else [pasta])
    fontes.update(arquivos_texto(RAIZ / "resultados"))
    por_nome = collections.defaultdict(set)
    canon = {k.casefold(): k for k in raw}
    for k in raw:
        por_nome[Path(k).name.casefold()].add(k)
    cachepath = OUT / "cache/fontes_inventario.json"
    cache = ler(cachepath) if cachepath.exists() else {}
    tocados, usados, desconhecidos = collections.defaultdict(set), {}, set()
    cache_alterado = False
    for i, p in enumerate(sorted(fontes)):
        st = p.stat()
        nome = rel(p)
        assinatura = [st.st_size, st.st_mtime_ns]
        ant = cache.get(nome)
        if (ant and ant["assinatura"] == assinatura
                and all('/' in k for k in ant["pdfs"])):
            item = ant
        else:
            refs, desconhecidas = set(), set()
            h, sobra = hashlib.sha256(), ""
            dec = codecs.getincrementaldecoder("utf-8")(errors="strict")
            with p.open("rb") as f:
                for bloco in iter(lambda: f.read(2**20), b""):
                    h.update(bloco)
                    texto = sobra + dec.decode(bloco)
                    candidatos = [m.group() for m in RX_REL.finditer(texto)]
                    candidatos += [m.group(1) for m in RX_JSON_PDF.finditer(texto)]
                    for s in candidatos:
                        s = decodificar(s)
                        inicio = re.search(r"official_diary_[a-zA-Z0-9_]+/", s, re.I)
                        if inicio:
                            k = s[inicio.start():]
                            refs.add(canon.get(k.casefold(), k))
                        elif "/" not in s and s.casefold() in por_nome:
                            refs.update(por_nome[s.casefold()])
                    sobra = texto[-4096:]
                dec.decode(b"", final=True)
            st2 = p.stat()
            exigir([st2.st_size, st2.st_mtime_ns] == assinatura,
                   f"Fonte mudou durante o inventario; retome: {nome}")
            item = {"assinatura": assinatura, "sha256": h.hexdigest(), "pdfs": sorted(refs)}
            cache[nome] = item
            cache_alterado = True
        usados[nome] = {"bytes": assinatura[0], "mtime_ns": assinatura[1],
                        "sha256": item["sha256"], "pdfs": len(item["pdfs"])}
        for k in item["pdfs"]:
            tocados[k].add(nome)
            if k not in raw:
                desconhecidos.add(k)
        if i % 100 == 0 and cache_alterado:
            gravar(cachepath, cache)
            cache_alterado = False
        if i % 1000 == 0:
            print(f"Inventario: {i+1}/{len(fontes)} fontes; {len(tocados)} PDFs", flush=True)
    if cache_alterado:
        gravar(cachepath, cache)
    res = {"versao": VERSAO, "pdfs": sorted(tocados), "total_pdfs": len(tocados),
           "por_uf": dict(sorted(collections.Counter(k.split('/')[0] for k in tocados).items())),
           "proveniencia": {k: sorted(v) for k, v in sorted(tocados.items())},
           "fontes": usados, "referencias_sem_pdf_atual": sorted(desconhecidos),
           "politica": "Exclusao conservadora de qualquer mencao a PDF em tarefas, blocos e listas/resultados textuais. Inclui treino, validacao, teste, bancadas e caches; nomes sem UF excluem todos os homonimos. Nao le conteudo de ordens para selecionar paginas.",
           "exclusoes_de_leitura": ["data/labelstudio/**", "resultados/ceia_datapolicy/**", "resultados/e001_teste_cego/**"]}
    gravar(OUT / "pdfs_tocados.json", res)
    return res


class Pausa(Exception):
    pass


class Montador:
    def __init__(self, e, u, m, raw, inv, limite):
        self.e, self.u, self.m, self.raw, self.inv = e, u, m, raw, inv
        self.limite = limite
        self.documento = self.documento_chave = None
        self.hashpath = OUT / "cache/hashes_pdfs.json"
        self.hashes = ler(self.hashpath) if self.hashpath.exists() else {}
        # Mesma funcao de detector, com globais isoladas; modulo original intacto.
        globais = {**u.detector.__globals__, "OUT": OUT, "MODELO": None,
                   "gravar": gravar, "rel": rel, "sha": sha,
                   "imagem_bancada": lambda *_: None, "hash_do_pdf": self.hash_pdf}
        self.detector = types.FunctionType(u.detector.__code__, globais)
        self.contexto = {"hashes": {rel(e.ls.PESOS): sha(e.ls.PESOS)}}
        deps = [Path(x.__file__) for x in (u, e.extrator, e.o, e.ls)]
        deps += [RAIZ / "src/data/dataset_sem_caixas_finas.py", e.ls.PESOS]
        self.receita = {rel(p): sha(p) for p in deps}

    def pausar(self):
        if self.limite and time.monotonic() >= self.limite:
            raise Pausa("Limite de tempo; repetir o mesmo comando para retomar.")

    def hash_pdf(self, p):
        p = Path(p)
        k, st = rel(p), p.stat()
        sig = [st.st_size, st.st_mtime_ns]
        if k not in self.hashes or self.hashes[k]["assinatura"] != sig:
            self.pausar()
            self.hashes[k] = {"assinatura": sig, "sha256": sha(p)}
            gravar(self.hashpath, self.hashes)
        return self.hashes[k]["sha256"]

    @contextmanager
    def pdf_aberto(self, k):
        """Reusa apenas o PDF corrente; nao conserva dois documentos na RAM."""
        if self.documento_chave != k:
            self.fechar_pdf()
            import pdfplumber
            self.documento = pdfplumber.open(self.raw[k])
            self.documento_chave = k
        yield self.documento

    def fechar_pdf(self):
        if self.documento is not None:
            self.documento.close()
        self.documento = self.documento_chave = None

    def plano(self):
        p = OUT / "plano.json"
        if p.exists():
            plano = ler(p)
            exigir(plano["inventario_sha256"] == digest(self.inv["pdfs"]),
                   "Inventario de PDFs mudou. Nao ressorteia automaticamente; requer revisao do orquestrador.")
            exigir(plano["receita"] == self.receita, "Receita mudou; nao misturar caches.")
            if "alocacao_capacidade" not in plano:
                exigir(not (OUT / "selecao.json").exists(), "Plano anterior ja selecionado; nao alterar quotas")
                dev = plano["grupos"]["desenvolvimento"]
                metas = alocar(45, {uf: 2*len(info["pdfs"]) for uf, info in dev.items()}, SEMENTES["desenvolvimento"])
                for uf, meta in metas.items():
                    dev[uf]["meta"] = meta
                plano["alocacao_capacidade"] = True
                gravar(p, plano)
            return plano
        splits = ler(RAIZ / "data/processed/splits.json")
        exigir(len(splits["treino"]) == 7 and splits["validacao"] == ["official_diary_rn"],
               "Divisao diferente dos sete veiculos de treino e RN")
        grupos = {"teste_cego": splits["teste"],
                  "desenvolvimento": splits["treino"] + splits["validacao"]}
        exigir(set(grupos["teste_cego"]) == {"official_diary_ce", "official_diary_ma", "official_diary_rj"},
               "Teste diferente de CE/MA/RJ")
        tocados = {s.casefold() for s in self.inv["pdfs"]}
        plano = {"versao": VERSAO, "sementes": SEMENTES, "receita": self.receita,
                 "inventario_sha256": digest(self.inv["pdfs"]), "grupos": {}}
        for grupo, ufs in grupos.items():
            extra = list(sorted(ufs))
            random.Random(SEMENTES[grupo]).shuffle(extra)
            metas = {uf: 30 if grupo == "teste_cego" else 5 + (uf in extra[:5]) for uf in ufs}
            plano["grupos"][grupo] = {}
            for uf in ufs:
                ks = [k for k in sorted(self.raw) if k.split('/')[0] == uf and k.casefold() not in tocados]
                random.Random(f"{SEMENTES[grupo]}-{uf}").shuffle(ks)
                plano["grupos"][grupo][uf] = {"meta": metas[uf], "pdfs": ks,
                    "pdfs_brutos": sum(k.split('/')[0] == uf for k in self.raw),
                    "pdfs_tocados": sum(k.split('/')[0] == uf for k in self.raw if k.casefold() in tocados)}
        dev = plano["grupos"]["desenvolvimento"]
        metas = alocar(45, {uf: 2*len(info["pdfs"]) for uf, info in dev.items()}, SEMENTES["desenvolvimento"])
        for uf, meta in metas.items():
            dev[uf]["meta"] = meta
        plano["alocacao_capacidade"] = True
        gravar(p, plano)
        return plano

    def pagina(self, k, numero):
        """Extrai palavras e linhas canonicas, sem ordenar ou medir a pagina."""
        self.pausar()
        exigir(not LOCK.exists(), "Teste ja lacrado: nenhuma pagina sera aberta.")
        pid = f"{k}#p{numero}"
        p = OUT / "cache/paginas" / (chave(pid) + ".json")
        fp = digest([self.receita, self.hash_pdf(self.raw[k]), numero])
        if p.exists():
            obj = ler(p)
            exigir(obj["fingerprint"] == fp, f"Cache de pagina incompativel: {pid}")
            return obj
        with self.pdf_aberto(k) as doc:
            page = doc.pages[numero]
            ws = self.e.extrator.palavras_da_pagina(page)
            palavras = [[w["t"], w["x0"], w["top"], w["x1"], w["bottom"]] for w in ws]
            texto = " ".join(w[0] for w in palavras)
            # Cada (cid:N) representa um caractere desconhecido. Denominador
            # conta esse glifo uma vez, nao os caracteres da notacao de erro.
            ncid = len(re.findall(r"\(cid:[^)]*\)", texto))
            normalizado = re.sub(r"\(cid:[^)]*\)", "\ufffd", texto)
            ileg = ncid + texto.count("\ufffd")
            taxa = ileg / max(1, len(re.sub(r"\s", "", normalizado)))
            obj = {"page_id": pid, "pdf": k, "pagina": numero, "fingerprint": fp,
                   "n_palavras": len(palavras), "fracao_ilegivel": taxa,
                   "elegivel": len(palavras) >= 200 and taxa <= .05}
            if not obj["elegivel"]:
                gravar(p, obj)
                page.close()
                return obj
            dim = {"width": float(page.width), "height": float(page.height)}
            img = OUT / "cache/imagens" / (self.e.ac.chave(pid) + ".png")
            if not img.exists():
                pi = page.to_image(resolution=self.e.layout.DPI)
                exigir(max(abs(v) for v in pi.bbox[:2]) < .11 and
                       max(abs(pi.bbox[2]-page.width), abs(pi.bbox[3]-page.height)) < .11,
                       f"CropBox incompatível com receita canonica: {pid}")
                img.parent.mkdir(parents=True, exist_ok=True)
                tmp = img.with_suffix(".png.tmp")
                pi.original.convert("RGB").save(tmp, format="PNG")
                os.replace(tmp, img)
            page.close()
        uf, arquivo = k.split("/", 1)
        meta = {"page_id": pid, "uf": uf, "arquivo": arquivo, "pagina": numero, "dimensions": dim}
        regs, _ = self.detector(meta, self.contexto)
        dets = self.e.ls.dets({"ls3": regs}, "ls3")
        base = {**meta, "palavras": palavras, "detector": {"modelo": "ls3", "regioes": dets}}
        linhas, _ = self.u.representar(base)
        ncol = linhas["colunas"]["n_estimado"]
        tabela = any(r["classe"] == "tabela" and r["score"] >= .45 for r in regs)
        obj.update(meta, palavras=palavras, unidades=linhas["unidades"], detector=base["detector"],
                   colunas=ncol, tabela=tabela, estrato=f"{min(3,ncol)}{'+' if ncol>=3 else ''}|{'tabela' if tabela else 'sem_tabela'}")
        gravar(p, obj)
        return obj

    def triagem_pdf(self, k, semente, exaustivo=False):
        p = OUT / "cache/triagem" / (chave(k) + ".json")
        fp = digest([self.receita, self.hash_pdf(self.raw[k]), semente])
        if p.exists() and ler(p).get("fingerprint") == fp:
            salvo = ler(p)
            if not exaustivo or salvo.get("exaustivo") or len(salvo["paginas"]) == 2:
                return salvo
        exigir(not LOCK.exists(), "Teste lacrado; nao abrir PDF.")
        import pymupdf
        with pymupdf.open(self.raw[k]) as doc:
            numeros = list(range(1, len(doc)))  # Capa excluida sem inspecao visual.
        random.Random(f"{semente}-{k}-paginas").shuffle(numeros)
        selecionadas = []
        tentativas = []
        # Limite operacional congelado antes de observar qualquer resultado.
        for n in numeros if exaustivo else numeros[:12]:
            if any(abs(n - q["pagina"]) <= 1 for q in selecionadas):
                continue
            q = self.pagina(k, n)
            tentativas.append({x: q[x] for x in ("page_id", "n_palavras", "fracao_ilegivel", "elegivel")})
            if q["elegivel"]:
                selecionadas.append({x: q[x] for x in ("page_id", "pdf", "pagina", "colunas", "tabela", "estrato", "n_palavras", "fracao_ilegivel")})
            if len(selecionadas) == 2:
                break
        obj = {"pdf": k, "fingerprint": fp, "paginas": selecionadas, "tentativas": tentativas,
               "exaustivo": exaustivo, "paginas_internas_pdf": len(numeros)}
        gravar(p, obj)
        self.fechar_pdf()
        return obj

    def selecionar(self, plano):
        p = OUT / "selecao.json"
        if p.exists():
            return ler(p)
        # Alias binario de PDF ja tocado tambem fica proibido.
        hashes_tocados = set()
        tocados = [k for k in self.inv["pdfs"] if k in self.raw]
        for i, k in enumerate(tocados):
            hashes_tocados.add(self.hash_pdf(self.raw[k]))
            if i % 200 == 0:
                print(f"Hashes de exclusao: {i+1}/{len(tocados)}", flush=True)
        selecao = {"grupos": {}, "pools": {}, "aliases_excluidos": [], "hashes_tocados": sorted(hashes_tocados),
                   "metas_efetivas": {}}
        usados_hash = set(hashes_tocados)
        for grupo, ufs in plano["grupos"].items():
            selecao["grupos"][grupo], selecao["pools"][grupo] = [], {}
            pools = {}
            for uf, info in ufs.items():
                self.pausar()
                meta = info["meta"]
                alvo_pdfs = math.ceil(meta / 2)
                pool, vistos_hash = [], set()
                # Sobreamostra PDFs, depois equilibra os estratos entre pares.
                alvo_pool = alvo_pdfs + (5 if grupo == "teste_cego" else 2)
                for k in info["pdfs"]:
                    self.pausar()
                    h = self.hash_pdf(self.raw[k])
                    if h in usados_hash or h in vistos_hash:
                        selecao["aliases_excluidos"].append(k)
                        continue
                    q = self.triagem_pdf(k, SEMENTES[grupo])
                    vistos_hash.add(h)
                    if q["paginas"]:
                        pool.append(q)
                        usados_hash.add(h)
                    print(f"Triagem {grupo}/{uf}: {len(pool)}/{alvo_pool} PDFs elegiveis", flush=True)
                    if len(pool) >= alvo_pool and sum(len(q["paginas"]) for q in pool) >= meta:
                        break
                pools[uf] = pool
            # A amostra inicial pode perder as poucas paginas com texto de um
            # PDF misto. Nos veiculos escassos de desenvolvimento, esgota a
            # busca interna antes de declarar capacidade menor que a meta.
            if grupo == "desenvolvimento":
                for uf, pool in pools.items():
                    info = ufs[uf]
                    if sum(len(q["paginas"]) for q in pool) >= info["meta"]:
                        continue
                    print(f"Varredura completa do desenvolvimento escasso: {uf}", flush=True)
                    for k in info["pdfs"]:
                        atual = next((q for q in pool if q["pdf"] == k), None)
                        if atual and len(atual["paginas"]) == 2:
                            continue
                        h = self.hash_pdf(self.raw[k])
                        if h in usados_hash and atual is None:
                            continue
                        q = self.triagem_pdf(k, SEMENTES[grupo], exaustivo=True)
                        if q["paginas"]:
                            if atual is None:
                                pool.append(q)
                            else:
                                pool[pool.index(atual)] = q
                            usados_hash.add(h)
                        if sum(len(q["paginas"]) for q in pool) >= info["meta"]:
                            break
            capacidades = {uf: sum(len(q["paginas"]) for q in pool) for uf, pool in pools.items()}
            if grupo == "desenvolvimento":
                metas = alocar(45, capacidades, SEMENTES[grupo], exigir_todos=False)
            else:
                exigir(all(c >= 30 for c in capacidades.values()), f"Teste com capacidade insuficiente: {capacidades}")
                metas = dict.fromkeys(ufs, 30)
            selecao["metas_efetivas"][grupo] = metas
            for uf, pool in pools.items():
                meta = metas[uf]
                # Sorteio de desempate ja esta na ordem do pool. Favorece
                # estratos sub-representados, sem consultar ordem ou desempenho.
                cont = collections.Counter()
                estratos = sorted({s["estrato"] for q in pool for s in q["paginas"]})
                escolhidos, paginas = [], []
                while len(paginas) < meta:
                    restantes = meta - len(paginas)
                    disponiveis = [q for q in pool if q not in escolhidos]
                    pares = [q for q in disponiveis if len(q["paginas"]) == 2]
                    candidatos = pares if restantes >= 2 and pares else disponiveis
                    def obter(q):
                        if restantes >= len(q["paginas"]):
                            return q["paginas"]
                        return [min(q["paginas"], key=lambda s: cont[s["estrato"]])]
                    def custo(q):
                        c = cont + collections.Counter(s["estrato"] for s in obter(q))
                        return sum(c[s] ** 2 for s in estratos)
                    q = min(candidatos, key=custo)
                    escolhidos.append(q)
                    novas = obter(q)
                    paginas += novas
                    cont.update(s["estrato"] for s in novas)
                selecao["grupos"][grupo] += paginas
                selecao["pools"][grupo][uf] = {
                    "pdfs_elegiveis": len(pool), "paginas": [s for q in pool for s in q["paginas"]],
                    "estratos_disponiveis": estratos}
                usados_hash.update(self.hash_pdf(self.raw[q["pdf"]]) for q in paginas)
        for grupo in selecao["grupos"]:
            random.Random(SEMENTES[grupo]).shuffle(selecao["grupos"][grupo])
        gravar(p, selecao)
        return selecao

    def exportar(self, selecao):
        from src.eval.protocolo import ordem_entrada
        from PIL import Image
        validacoes = {}
        for grupo, paginas in selecao["grupos"].items():
            tarefas = []
            for i, meta in enumerate(paginas, 1):
                self.pausar()
                q = ler(OUT / "cache/paginas" / (chave(meta["page_id"]) + ".json"))
                dim = q["dimensions"]
                unidades = sorted(q["unidades"], key=lambda x: x["id"])
                auto = {"page_id": q["page_id"], "bounding_boxes": unidades}
                proposta = []
                for j, k in enumerate(ordem_entrada(auto), 1):
                    u = unidades[k]
                    x0, y0, x1, y1 = u["bbox"]
                    x0, y0 = max(0., min(x0, dim["width"]-1)), max(0., min(y0, dim["height"]-1))
                    x1, y1 = min(dim["width"], max(x1, x0+1)), min(dim["height"], max(y1, y0+1))
                    proposta.append({"id": f"p{j}", "classe": self.m.mapear_classe_diamond(u["tipo"]),
                        "bbox": [x0, y0, x1, y1], "origem": "extrator_sem_paragrafos",
                        "tipo_original": u["tipo"], "score": float(u.get("score", 1.)), "alertas": []})
                tarefa = {"n": i, **{k: q[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "palavras")},
                    "imagem": f"{i:03d}.jpg", "proposta": proposta, "blocos_v3": [], "detector": q["detector"],
                    "stats": {"n_palavras": q["n_palavras"], "n_proposta": len(proposta),
                        "motivo_selecao": "Sorteio E001 por PDF e estrato, independente de desempenho",
                        "total_achados_auditor": 0, "estrato": q["estrato"]},
                    "extrator_sha256": self.receita[rel(Path(self.e.extrator.__file__))]}
                destino = OUT / grupo / "img" / tarefa["imagem"]
                destino.parent.mkdir(parents=True, exist_ok=True)
                if not destino.exists():
                    with Image.open(OUT / "cache/imagens" / (self.e.ac.chave(q["page_id"]) + ".png")) as img:
                        tmp = destino.with_suffix(".jpg.tmp")
                        img.convert("RGB").save(tmp, format="JPEG", quality=90)
                        os.replace(tmp, destino)
                exigir(not any(k in tarefa for k in ("ordem", "ordens", "ordem_leitura", "gt_w", "referencia")),
                       "Ordem pre-preenchida na tarefa")
                exigir(sorted(k for u in unidades for k in u["ks"]) == list(range(len(q["palavras"]))),
                       "Perda ou duplicacao de palavras na representacao")
                tarefas.append(tarefa)
            val = self.m.validar_tarefas_com_servidor(tarefas, OUT / grupo / "img")
            exigir(val["ok"], f"Tarefas incompativeis com Diamond: {val['erros']}")
            gravar(OUT / grupo / "tarefas.jsonl", "".join(json.dumps(t, ensure_ascii=False, allow_nan=False) + "\n" for t in tarefas))
            validacoes[grupo] = val
        gravar(OUT / "validacao_diamond.json", validacoes)
        return validacoes


def sobreposicao(selecao, inv, raw, montador):
    grupos = selecao["grupos"]
    exigir({k: len(v) for k, v in grupos.items()} == {"teste_cego": 90, "desenvolvimento": 45},
           "Totais diferentes de 90 e 45; nao lacrar lote incompleto")
    conjuntos = {}
    for grupo, paginas in grupos.items():
        exigir(len({p["page_id"] for p in paginas}) == len(paginas), "Pagina repetida")
        por_pdf = collections.defaultdict(list)
        for p in paginas:
            exigir(p["pagina"] > 0 and p["n_palavras"] >= 200 and p["fracao_ilegivel"] <= .05,
                   "Pagina fora dos criterios de elegibilidade")
            por_pdf[p["pdf"]].append(p["pagina"])
        for numeros in por_pdf.values():
            exigir(len(numeros) <= 2 and (len(numeros) < 2 or abs(numeros[0]-numeros[1]) > 1),
                   "Mais de duas paginas ou paginas consecutivas")
        conjuntos[grupo] = set(por_pdf)
        exigir(not ({k.casefold() for k in por_pdf} & {k.casefold() for k in inv["pdfs"]}), "PDF ja tocado no lote novo")
        exigir(not ({montador.hash_pdf(raw[k]) for k in por_pdf} & set(selecao["hashes_tocados"])),
               "Alias binario de PDF tocado no lote novo")
    exigir(not conjuntos["teste_cego"] & conjuntos["desenvolvimento"], "Sobreposicao entre lotes")
    return {"teste_cego_x_tocados_pdf": 0, "desenvolvimento_x_tocados_pdf": 0,
            "teste_cego_x_desenvolvimento_pdf": 0, "novos_x_tocados_sha256": 0}


def lacrar(selecao, montador, manifesto):
    """Cria o unico arquivo autorizado fora de resultados/, sem substituir."""
    paginas = selecao["grupos"]["teste_cego"]
    lista = sorted(p["page_id"] for p in paginas)
    pdfs = {p["pdf"]: montador.hash_pdf(montador.raw[p["pdf"]]) for p in paginas}
    obj = {"experimento": "E001", "semente": SEMENTES["teste_cego"],
           "data": dt.datetime.now(dt.timezone.utc).isoformat(), "page_id": lista,
           "pdfs_sha256": dict(sorted(pdfs.items())), "sha256_lista": digest(lista),
           "serializacao_lista": "JSON UTF-8, ensure_ascii=False, sort_keys=True, separators=(',', ':')",
           "tarefas_sha256": manifesto["artefatos_sha256"]["teste_cego/tarefas.jsonl"],
           "manifesto_sha256": sha(OUT / "manifesto.json")}
    # Primeiro persiste a copia completa; recuperacao de queda nao ressorteia.
    gravar(OUT / "lacre.json", obj)
    # Hard link e exclusivo e atomico no NTFS: queda nao deixa JSON truncado.
    # A copia ja foi fechada e sincronizada; gravar() nunca a altera in-place.
    os.link(OUT / "lacre.json", LOCK)


def conferir_lacre():
    """Verifica somente bytes/hashes e metadados; nunca abre paginas lacradas."""
    lacre = ler(LOCK)
    exigir(lacre.get("experimento") == "E001" and (OUT / "manifesto.json").exists(),
           "Ja existe lacre externo; nao abrir nenhuma pagina nem substituir a lista")
    exigir(lacre == ler(OUT / "lacre.json"), "Lacre difere da copia; nao alterar nem reabrir paginas")
    exigir(lacre["sha256_lista"] == digest(lacre["page_id"]), "Hash da lista divergente")
    exigir(lacre["manifesto_sha256"] == sha(OUT / "manifesto.json"), "Manifesto divergente")
    manifesto = ler(OUT / "manifesto.json")
    for k, h in manifesto["artefatos_sha256"].items():
        exigir(sha(OUT / k) == h, f"Artefato divergiu do lacre: {k}")
    for k, h in lacre["pdfs_sha256"].items():
        exigir(sha(RAW / k) == h, f"PDF divergiu do lacre: {k}")
    print("Lacre e hashes conferidos; nenhuma pagina foi reaberta.", flush=True)


def fmt(v, casas=6):
    return f"{v:.{casas}f}".replace(".", ",")


def relatorio(anc, inv=None, plano=None, selecao=None, manifesto=None, mensagem=""):
    l = ["# E001 — Teste cego e desenvolvimento novo", "", mensagem, "",
         "## Controle obrigatório", "",
         f"Âncora recalculada pela régua existente no golden_v4: τ {fmt(anc['tau'])}; {fmt(anc['quebras'])} quebras/página, em {anc['paginas']} páginas. Estado: {'aprovada' if anc['aprovada'] else 'REPROVADA'}. Fonte: `ancora.json`.", ""]
    if inv:
        l += [f"Inventário conservador: {inv['total_pdfs']} PDFs referenciados em {len(inv['fontes'])} arquivos; {len(inv['referencias_sem_pdf_atual'])} referências sem caminho correspondente no acervo atual. Lista e proveniência: `pdfs_tocados.json`.", ""]
    if plano:
        l += ["## Disponibilidade antes da triagem", "", "| Lote | Veículo | PDFs no acervo | Já tocados | Disponíveis por caminho | Meta de páginas |", "|---|---|---:|---:|---:|---:|"]
        for g, ufs in plano["grupos"].items():
            for uf, info in ufs.items():
                l.append(f"| {g} | {uf} | {info['pdfs_brutos']} | {info['pdfs_tocados']} | {len(info['pdfs'])} | {info['meta']} |")
    if selecao:
        l += ["", "## Contagens por veículo e estrato", "", "| Lote | Veículo | PDFs | Páginas | Colunas | Tabela detectada |", "|---|---|---:|---:|---|---|"]
        for g, ps in selecao["grupos"].items():
            ufs = plano["grupos"][g] if plano else {p['pdf'].split('/')[0] for p in ps}
            for uf in sorted(ufs):
                pp = [p for p in ps if p['pdf'].split('/')[0] == uf]
                for s in sorted({p['estrato'] for p in pp}):
                    qs = [p for p in pp if p['estrato'] == s]
                    col, tab = s.split('|')
                    l.append(f"| {g} | {uf} | {len({q['pdf'] for q in qs})} | {len(qs)} | {col} | {'sim' if tab=='tabela' else 'não'} |")
                l.append(f"| **{g}** | **{uf} — total** | **{len({q['pdf'] for q in pp})}** | **{len(pp)}** | — | — |")
        l += ["", "PDFs de linhas de estrato não são aditivos: um PDF pode contribuir para estratos diferentes.", ""]
        faltantes = [uf for uf, n in selecao["metas_efetivas"]["desenvolvimento"].items() if n == 0]
        if faltantes:
            l += ["**Limitação do acervo no desenvolvimento:** os seguintes veículos não forneceram página interna elegível mesmo após ampliar a busca para todas as páginas dos PDFs não tocados: " + ", ".join(faltantes) + ". A meta aproximada por veículo não foi atingida; as páginas foram distribuídas pelos veículos com material elegível, preservando o total e os filtros. Não houve relaxamento de qualidade nem reutilização de PDF tocado.", ""]
    if manifesto:
        l += ["## Verificação de não sobreposição", ""]
        l += [f"- {k}: **{v}**." for k, v in manifesto["sobreposicao"].items()]
        l += ["", f"Hashes do lote e imagens: `manifesto.json`. Lacre: `experimentos/TESTE_CEGO.lock`; cópia em `lacre.json`. Total: {sum(len(v) for v in selecao['grupos'].values())} tarefas.", ""]
        l += [f"Tempo da invocação que concluiu a montagem: {fmt(manifesto['tempo_s_ultima_invocacao'], 1)} s; execuções anteriores podem ter produzido caches. Não é benchmark controlado.", ""]
    l += ["## Sorteio e limites", "",
          "Sementes: teste cego 20261102; desenvolvimento 20261103. A lista ordenada de PDFs elegíveis é permutada separadamente por veículo. A página inicial (índice zero) é sempre excluída; inicialmente até doze posições por PDF são visitadas em permutação fixa, parando em duas elegíveis e não consecutivas. Se um veículo de desenvolvimento ficar abaixo da meta por escassez, a busca é ampliada para todas as páginas internas dos PDFs disponíveis sem duas páginas elegíveis. PDFs com um único candidato também podem fornecer a segunda página nessa busca. Essa ampliação não é feita no teste cego. A elegibilidade exige pelo menos 200 palavras do extrator canônico e até 5% de glifos desconhecidos; cada notação `(cid:N)` conta como um glifo, e U+FFFD também conta. O denominador é o número de caracteres sem espaços, após reduzir cada notação cid a um glifo.", "",
          "A estratificação é balanceada entre os estratos observados no pool: 1, 2 e 3+ colunas × tabela ls3 (score ≥ 0,45). O pool tenta obter cinco PDFs de reserva por UF de teste e dois por veículo de desenvolvimento; prefere pares e minimiza a soma dos quadrados das contagens de estrato, com desempate na ordem sorteada. PDFs com apenas uma página elegível também podem contribuir. As 45 páginas de desenvolvimento são distribuídas o mais igualmente possível entre os oito veículos, respeitando primeiro a capacidade de PDFs não tocados e depois a de páginas elegíveis no pool; nenhum PDF tocado é reintroduzido para completar quota. Metas efetivas e capacidade triada ficam em `selecao.json`. Estratos inexistentes no pool não podem receber quota. Isso não estima a prevalência de layouts no acervo e não garante cobrir estratos raros. A estimativa de colunas e a presença de tabela são automáticas e podem errar; ausência de estrato não prova ausência no veículo. O lote exclui capas e PDFs sem página interna elegível, limitando a representatividade. Não há OCR.", "",
          "O inventário exclui por caminho (UF/arquivo), conservadoramente, inclusive menções em resultados textuais; homônimos sem UF excluem todos os correspondentes. Hashes também excluem cópias binárias dos PDFs tocados. Fontes e PDFs ficam registrados para auditoria. Arquivos binários/comprimidos e conteúdo não identificado por nome de PDF não são interpretados; dados do parceiro, incluindo `data/labelstudio/` e `resultados/ceia_datapolicy/`, não são lidos. A ausência de uso anterior é verificável nos artefatos locais inventariados, sem garantir ausência de consulta humana não registrada.", "",
          "As propostas de segmentação usam linhas + átomos ls3 e preservam as palavras. Tarefas seguem o formato Diamond do lote_sem_paragrafos; `blocos_v3` fica vazio, pois não foram geradas caixas de parágrafo. A ordem das propostas é embaralhada com `ordem_entrada`, equivalente a `random.Random(f\"entrada-{page_id}\")`; não há ordem de leitura preenchida em nenhum lote. O detector gera pré-anotação de segmentação: ainda pode haver viés de ancoragem nessa etapa, e a correção humana é necessária.", "",
          "## Bancadas e métricas", "",
          "| Bancada | Uso neste E001 |", "|---|---|",
          "| golden_v4 | Somente reprodução da âncora obrigatória; nenhuma escolha de parâmetro |",
          "| golden_v3_novo | Não avaliada aqui; já foi consultada em rodadas anteriores |",
          "| teste silver CE/MA/RJ | Não avaliado aqui; todos os seus PDFs identificados entram na exclusão |", "",
          "Nenhum método de ordenação foi executado ou avaliado nas páginas novas. Não há Δ, IC95, Wilcoxon, páginas melhor/igual/pior, reparos ou regressões de sucessores a reportar: E001 monta dados sem referência humana nova. Essas análises pertencem à avaliação posterior do orquestrador; o teste cego é confirmatório e deve ser avaliado uma única vez após congelamento do método. CPU, um processo, sem multiprocessing, num_workers=0 quando aplicável, torch limitado a quatro threads.", "",
          "## Abrir na ferramenta — ação do Pedro", "",
          "Os comandos abaixo são instruções, não foram executados pelo montador. Pare se os nomes de lote já existirem; nunca sobreponha anotações humanas. Copie cada pasta inteira (tarefas e `img/`). No PowerShell, a partir da raiz:", "", "```powershell",
          "$destTeste = 'data/diamond/e001_teste_cego'",
          "$destDev = 'data/diamond/e001_desenvolvimento'",
          "if ((Test-Path -LiteralPath $destTeste) -or (Test-Path -LiteralPath $destDev)) { throw 'Lote já existe; não sobrescrever.' }",
          "Copy-Item -LiteralPath 'resultados/e001_teste_cego/teste_cego' -Destination $destTeste -Recurse",
          "Copy-Item -LiteralPath 'resultados/e001_teste_cego/desenvolvimento' -Destination $destDev -Recurse",
          "venv/Scripts/python.exe -B src/anotacao/servidor.py --diamond", "```", "",
          "Abra `http://127.0.0.1:8770/diamond` e selecione o lote desejado. Se a ferramenta já estiver ativa nessa porta, use a sessão existente. Confira o nome do anotador. Só Pedro anota o teste cego; agentes não devem abrir suas páginas, corrigir suas ordens ou executar métodos nelas. Os comandos de cópia só se aplicam após conclusão e lacre do lote.", "",
          "## Retomada", "", "```powershell",
          "venv/Scripts/python.exe -B orquestracao/analises/e001_montar_teste_cego.py",
          "```", "", "Antes do lacre, retoma por arquivo de inventário e por página/PDF. Depois do lacre, verifica apenas hashes de arquivos e metadados, sem reabrir páginas ou predizer ordens. Não substitui lacre nem ressorteia automaticamente.", ""]
    gravar(OUT / "RELATORIO.md", "\n".join(l))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--somente-inventario", action="store_true")
    ap.add_argument("--max-minutos", type=float, default=0)
    args = ap.parse_args()
    exigir(args.max_minutos >= 0, "Tempo deve ser positivo ou zero")
    inicio = time.monotonic()
    with trava():
        if LOCK.exists():
            conferir_lacre()
            return
        anc = {"paginas": 0, "tau": 0., "quebras": 0., "aprovada": False}
        inv = plano = selecao = montador = None
        try:
            e, b, u, m = importar()
            anc = ancora(e, b)
            raw = catalogo_raw()
            inv = inventario(raw)
            montador = Montador(e, u, m, raw, inv,
                                inicio + args.max_minutos*60 if args.max_minutos else None)
            plano = montador.plano()
            relatorio(anc, inv, plano, mensagem="Inventário concluído; montagem ainda não lacrada.")
            if args.somente_inventario:
                print("Inventario concluido; nenhum PDF novo aberto.", flush=True)
                return
            for ufs in plano["grupos"].values():
                for uf, info in ufs.items():
                    exigir(len(info["pdfs"]) >= math.ceil(info["meta"]/2),
                           f"Acervo insuficiente em {uf}: {len(info['pdfs'])} PDFs nao tocados para {info['meta']} paginas.")
            selecao = montador.selecionar(plano)
            validacoes = montador.exportar(selecao)
            # Confere mudancas concorrentes antes de lacrar: metadados apenas.
            inv = inventario(raw)
            sobre = sobreposicao(selecao, inv, raw, montador)
            artefatos = {p.relative_to(OUT).as_posix(): sha(p)
                         for g in SEMENTES for p in sorted((OUT / g).rglob('*')) if p.is_file()}
            for nome in ("pdfs_tocados.json", "ancora.json", "plano.json", "selecao.json", "validacao_diamond.json"):
                artefatos[nome] = sha(OUT / nome)
            manifesto = {"versao": VERSAO, "sementes": SEMENTES, "sobreposicao": sobre,
                         "artefatos_sha256": artefatos, "validacao_diamond": validacoes,
                         "tempo_s_ultima_invocacao": time.monotonic()-inicio}
            gravar(OUT / "manifesto.json", manifesto)
            relatorio(anc, inv, plano, selecao, manifesto,
                      "Montagem concluída; páginas lacradas para avaliação confirmatória única.")
            lacrar(selecao, montador, manifesto)
            conferir_lacre()
        except (Exception, KeyboardInterrupt) as exc:
            if not LOCK.exists():
                if (OUT / "ancora.json").exists():
                    anc = ler(OUT / "ancora.json")
                relatorio(anc, inv, plano, selecao,
                          mensagem=f"Montagem interrompida, sem lacre: {type(exc).__name__}: {exc}")
            print(f"{type(exc).__name__}: {exc}", flush=True)
            if not isinstance(exc, Pausa):
                raise
        finally:
            if montador is not None:
                montador.fechar_pdf()


if __name__ == "__main__":
    main()
