"""Diagnostica e corrige transicoes ambiguas da regra de colunas sobre linhas.

Importa a regua de palavras de erros_ponta_a_ponta e as funcoes sem escrita
da bancada. Nao chama mains nem metricas() da bancada, pois gravariam sobre
outros experimentos. Ancoras precedem qualquer medida nova. Cada pagina,
pares de treino e checkpoint ficam no cache proprio, com hashes das fontes.
Le uma pagina por vez; treina apenas um MLP pequeno em CPU, sem DataLoader.

Executar da raiz, quando houver memoria livre:
  venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py
  ... --etapa candidatos --max-minutos 20
  ... --etapa corretor --n-treino 24 --epocas 3 --max-minutos 30
O padrao termina no diagnostico; o treino leve exige --etapa corretor.
Repetir o mesmo comando retoma paginas e o ultimo checkpoint de pagina.
--n-treino e limitado a 128: esta entrega e uma demonstracao, nao treino final.
Saidas: somente resultados/corretor_de_transicoes.md e seu _cache/**.
Nao usa GPU, rede, PDFs, Label Studio, processos filhos ou anotacao como feature.
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
import bisect
import collections
import gc
import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import time
from contextlib import contextmanager

os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from src.eval.protocolo import ordem_entrada

BASE = RAIZ / "resultados/corretor_de_transicoes_cache"
MD = RAIZ / "resultados/corretor_de_transicoes.md"
UNIDADES = RAIZ / "resultados/unidades_sem_caixas"
VERSAO = "transicoes-v2-veredito"
SEMENTE = 20261008
HUMANAS = ("golden_v4", "golden_v3_novo")
BANCADAS = HUMANAS + ("validacao_silver", "teste_silver")
TIPOS = ("mesma_coluna", "proxima_coluna", "tabela_imagem", "transversal", "margem", "outro")
ROTULOS = {"mesma_coluna": "Continuação na mesma coluna",
           "proxima_coluna": "Fim de coluna → topo da próxima",
           "tabela_imagem": "Entrada/saída de tabela ou imagem",
           "transversal": "Salto ou fronteira de elemento transversal",
           "margem": "Cabeçalho/rodapé/marca marginal", "outro": "Outro"}
METRICAS = ("tau", "quebras", "quebras_mil", "fid12", "sucessor_linhas", "piso_interno")
LIMIARES = (.5, .6, .7, .8, .9, .95, .99, 1.01)
NIVEIS = (3, 8, 16, -1)
PRAZO = None
ESTADO = None
DIR_EXEC = None


class Interromper(RuntimeError):
    """Parada retomavel por prazo, memoria ou falta de evidencia."""


def exigir(cond, mensagem):
    if not cond:
        raise ValueError(mensagem)


def ler(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def digest(obj):
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, allow_nan=False,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            h.update(buf)
    return h.hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(RAIZ).as_posix()


def destino(p):
    p = Path(p).resolve()
    exigir(p == MD.resolve() or p.is_relative_to(BASE.resolve()), f"Saida fora do escopo: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def substituir(tmp, p):
    for tentativa in range(51):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if tentativa == 50:
                raise
            time.sleep(.1)


def gravar(p, obj):
    p = destino(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    substituir(tmp, p)


def vigiar():
    if PRAZO is not None and time.monotonic() >= PRAZO:
        raise Interromper("Prazo atingido; repetir o mesmo comando retoma os caches.")
    mem = b.memoria()
    if mem and (mem["ram_livre_mb"] < 900 or mem["commit_livre_mb"] < 1200):
        raise Interromper(f"Memória insuficiente para continuar com segurança: {mem}")
    return mem


@contextmanager
def trava():
    """Lock exclusivo proprio; recupera PID morto apos reinicio do laptop."""
    p = destino(BASE / "execucao.lock")
    if p.exists():
        antigo = ler(p)
        pid, vivo = antigo["pid"], True
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            k.OpenProcess.restype = wintypes.HANDLE
            k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            k.CloseHandle.argtypes = [wintypes.HANDLE]
            h = k.OpenProcess(0x1000, False, pid)
            if h:
                codigo = wintypes.DWORD()
                exigir(k.GetExitCodeProcess(h, ctypes.byref(codigo)), "Falha ao consultar PID do lock")
                vivo = codigo.value == 259
                k.CloseHandle(h)
            else:
                vivo = ctypes.get_last_error() != 87
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                vivo = False
        exigir(not vivo, f"Outra execucao desta tarefa esta ativa no PID {pid}")
        p.unlink()
    with open(p, "x", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "criado": time.time()}, f)
    try:
        yield
    finally:
        p.unlink(missing_ok=True)


def salvar():
    if ESTADO is not None and DIR_EXEC is not None:
        ESTADO["assinatura_numeros"] = assinatura_numeros(ESTADO)
        gravar(DIR_EXEC / "estado.json", ESTADO)
        gravar(MD, relatorio(ESTADO))


def fontes(splits):
    ps = set(b.DEP_PATHS) | {Path(__file__), RAIZ / "data/processed/splits.json",
                            e.JSON, UNIDADES / "treino_noite.json"}
    ps |= {UNIDADES / "bancadas" / (c + ".jsonl") for c in HUMANAS}
    # Tarefas, inclusive as nao concluidas: so le IDs, nunca as anotacoes.
    ps |= {RAIZ / "data/golden/golden_v4/tarefas.jsonl",
           RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl"}
    for part in ("treino", "validacao", "teste"):
        for uf in splits[part]:
            pastas = ("linhas", "linhas_extra") if part == "treino" else ("linhas",)
            for pasta in pastas:
                for suf in (".jsonl", ".palavras.jsonl"):
                    p = UNIDADES / pasta / (uf + suf)
                    if pasta == "linhas_extra" and not p.exists():
                        continue
                    ps.add(p)
    for obj, p in b.paginas("golden_v4", "linhas"):
        ps.add(UNIDADES / "cache/detector" / (e.ac.chave(p["page_id"]) + ".json"))
    out = {}
    for p in sorted(ps):
        vigiar()
        exigir(p.is_file(), f"Fonte obrigatoria ausente: {p}")
        out[rel(p)] = sha(p)
    return out


def indice_shard(p):
    """Le apenas uma pagina de unidades por vez, guardando IDs e offsets."""
    out = {}
    with open(p, "rb") as f:
        while True:
            off = f.tell()
            linha = f.readline()
            if not linha:
                return out
            if not linha.strip():
                continue
            obj = json.loads(linha.decode("utf-8"))
            pid = obj["page_id"]
            exigir(pid not in out, f"Pagina duplicada no shard: {p}: {pid}")
            campos = ("page_id", "palavras", "gt_w", "referencia_palavras_tipo") if "palavras" in obj else (
                "page_id", "uf", "dimensions", "bounding_boxes", "ordens", "representacao", "referencia_palavras_tipo")
            conteudo = {k: obj[k] for k in campos if k in obj}
            out[pid] = {"offset": off, "assinatura": digest(obj), "conteudo": digest(conteudo), "uf": obj.get("uf"),
                        "particao": obj.get("particao")}


def inventario(splits, n_treino):
    humanos, ids_coortes = set(), {}
    for nome in ("data/golden/golden_v4/tarefas.jsonl", "data/golden/_avaliacao/golden_v3/tarefas.jsonl"):
        humanos.update(p["page_id"] for p in b.jsonl(RAIZ / nome))
    for c, n in zip(HUMANAS, (44, 27)):
        ids = [p["page_id"] for p in b.jsonl(UNIDADES / "bancadas" / (c + ".jsonl"))]
        exigir(len(ids) == n and len(set(ids)) == n, f"Bancada {c} incompleta/duplicada")
        ids_coortes[c] = ids
        humanos.update(ids)
    exigir(not set(ids_coortes[HUMANAS[0]]) & set(ids_coortes[HUMANAS[1]]), "Bancadas humanas sobrepostas")
    planos, excluidos, duplicatas = {}, {}, []
    for part in ("treino", "validacao", "teste"):
        regs, excl = {}, []
        for uf in splits[part]:
            for pasta in (("linhas", "linhas_extra") if part == "treino" else ("linhas",)):
                p = UNIDADES / pasta / (uf + ".jsonl")
                w = p.with_name(uf + ".palavras.jsonl")
                if not p.exists() and pasta == "linhas_extra":
                    exigir(not w.exists(), f"Shard de palavras sem unidades: {w}")
                    continue
                vigiar()
                exigir(p.exists() and w.exists(), f"Par de shards incompleto: {p}")
                ip, iw = indice_shard(p), indice_shard(w)
                exigir(set(ip) == set(iw), f"IDs de palavras/unidades divergentes: {p}")
                for pid, meta in ip.items():
                    exigir(meta["uf"] == uf and pid.split("/", 1)[0] == uf, "Veiculo divergente do shard")
                    permitido = ("treino", "treino_extra") if part == "treino" else (part,)
                    exigir(meta["particao"] in permitido, f"Particao divergente: {pid}")
                    if pid in humanos:
                        excl.append(pid)
                        continue
                    if pid in regs:
                        # Base/extra tem particao e procedencia distintas, mas
                        # precisa conter as mesmas unidades, palavras e ouro.
                        exigir(regs[pid]["conteudo"] == meta["conteudo"] and
                               regs[pid]["conteudo_palavras"] == iw[pid]["conteudo"],
                               f"Duplicata base/extra diferente: {pid}")
                        duplicatas.append(pid)
                        continue
                    regs[pid] = {**meta, "page_id": pid, "path": rel(p), "palavras_path": rel(w),
                                 "palavras_offset": iw[pid]["offset"],
                                 "assinatura_palavras": iw[pid]["assinatura"], "conteudo_palavras": iw[pid]["conteudo"]}
        planos[part] = list(regs.values())
        excluidos[part] = sorted(set(excl))
    # Amostra pequena distribuida entre veiculos; nao escolhe por eficacia.
    filas = {uf: sorted((m for m in planos["treino"] if m["uf"] == uf),
                        key=lambda m: digest([SEMENTE, m["page_id"]])) for uf in splits["treino"]}
    escolhidos = []
    for i in range(max((len(f) for f in filas.values()), default=0)):
        for uf in splits["treino"]:
            if i < len(filas[uf]):
                escolhidos.append(filas[uf][i])
        if len(escolhidos) >= n_treino:
            break
    escolhidos = escolhidos[:n_treino]
    exigir(len(escolhidos) == n_treino, "Treino elegivel menor que --n-treino")
    planos["treino"] = escolhidos
    sets = {k: {m["page_id"] for m in v} for k, v in planos.items()}
    exigir(all(not sets[a] & sets[z] for a, z in itertools.combinations(sets, 2)), "Vazamento entre splits")
    exigir(not set().union(*sets.values()) & humanos, "Pagina humana em particao silver")
    treino_pdfs = {m["page_id"].rsplit("#p", 1)[0] for m in escolhidos}
    humanos_pdfs = {pid.rsplit("#p", 1)[0] for pid in humanos}
    return {"planos": planos, "ids_coortes": ids_coortes, "excluidos": excluidos,
            "duplicatas_base_extra": sorted(set(duplicatas)), "humanos_proibidos": sorted(humanos),
            "treino_veiculos_efetivos": sorted({m["uf"] for m in escolhidos}),
            "treino_pdfs": sorted(treino_pdfs), "pdfs_compartilhados_humanas": sorted(treino_pdfs & humanos_pdfs)}


def ler_meta(m):
    def uma(nome, off):
        with open(RAIZ / nome, "rb") as f:
            f.seek(off)
            return json.loads(f.readline().decode("utf-8"))
    p = uma(m["path"], m["offset"])
    obj = uma(m["palavras_path"], m["palavras_offset"])
    exigir(p["page_id"] == obj["page_id"] == m["page_id"], "Offset trocou pagina")
    exigir(digest(p) == m["assinatura"] and digest(obj) == m["assinatura_palavras"], "Shard mudou durante a leitura")
    exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
           obj["gt_w"] == list(range(len(obj["palavras"]))), "Silver nao preserva fluxo PDF")
    return {**obj, "uf": p["uf"]}, p


def paginas(c):
    if c in HUMANAS:
        yield from b.paginas(c, "linhas")
    else:
        part = {"validacao_silver": "validacao", "teste_silver": "teste", "treino": "treino"}[c]
        for m in ESTADO["inventario"]["planos"][part]:
            yield ler_meta(m)


def automatico(p):
    return {"page_id": p["page_id"], "dimensions": dict(p["dimensions"]),
            "bounding_boxes": [{k: u[k] for k in ("id", "bbox", "ks", "text", "tipo")}
                               for u in p["bounding_boxes"]]}


def medir(obj, p, ordem):
    """Regua importada integralmente; nenhuma escrita em caches da bancada."""
    ids = b.auditar_unidades(p, obj)
    exigir(isinstance(ordem, list) and len(ordem) == len(ids) and set(ordem) == set(ids), "Ordem invalida")
    exp = b.expansoes(obj, p)
    seq = [k for uid in ordem for k in exp[uid]]
    q = b.referencia(obj, p)
    med = e.medir(q, seq, [], {}, "P0")
    res = {k: med[k] for k in METRICAS if k != "piso_interno"}
    res["piso_interno"] = sum(len(e.eventos(ks, q["gt_w"])) for ks in exp.values())
    exigir(res["piso_interno"] <= res["quebras"], "Piso excede quebras")
    return res, seq, q, exp


def ancoras():
    """Reexecuta regra/P2 congelado; P1m e controle historico explicitamente."""
    if ESTADO.get("ancoras", {}).get("aprovada"):
        return
    historico = ler(e.JSON)
    antigos = {r["page_id"]: {m: {k: r["metodos"][m][k] for k in ("tau", "quebras", "seq")}
                             for m in ("P2", "P1m")}
               for r in historico["paginas"] if r["coorte"] == "v4"}
    del historico
    rows = []
    for obj, p in paginas("golden_v4"):
        vigiar()
        pid = p["page_id"]
        cp = DIR_EXEC / "ancoras" / (e.ac.chave(pid) + ".json")
        if cp.exists():
            row = ler(cp)
        else:
            auto = automatico(p)
            ordem, _ = b.prever(auto, obj["palavras"], "regra_colunas")
            med, seq, q, _ = medir(obj, p, ordem)
            q["ls3"] = ler(UNIDADES / "cache/detector" / (e.ac.chave(pid) + ".json"))["regioes"]
            q["d"] = {"detector": {"regioes": []}}
            seq_p2, its, diag = e.ls.prever(q, e.FIXA, "ls3")
            mp2 = e.medir(q, seq_p2, its, diag, "P0")
            exigir(pid in antigos, "Pagina da ancora sem historico")
            exigir(seq == seq_p2 == antigos[pid]["P2"]["seq"], f"Sequencia da ancora diverge: {pid}")
            row = {"page_id": pid, "uf": obj["uf"],
                   "regra": {k: med[k] for k in ("tau", "quebras")},
                   "P2": {k: mp2[k] for k in ("tau", "quebras")},
                   "P1m_historico": {k: antigos[pid]["P1m"][k] for k in ("tau", "quebras")}}
            gravar(cp, row)
        rows.append(row)
        ESTADO["ancoras"] = {"aprovada": False, "paginas": rows, "concluidas": len(rows)}
        salvar()
        print(f"Ancoras: {len(rows)}/44", flush=True)
    exigir(len(rows) == 44 and {r["page_id"] for r in rows} == set(antigos), "Coorte da ancora mudou")
    medias = {m: {k: statistics.mean(r[m][k] for r in rows) for k in ("tau", "quebras")}
              for m in ("regra", "P2", "P1m_historico")}
    ESTADO["ancoras"].update(medias=medias)
    for nome, tau, qb in (("regra", .985948, 6.045455), ("P2", .985948, 6.045455),
                          ("P1m_historico", .952424, 8.931818)):
        exigir(abs(medias[nome]["tau"] - tau) <= .006 and
               abs(medias[nome]["quebras"] - qb) <= .0051, f"Ancora {nome} nao reproduzida: {medias[nome]}")
    ESTADO["ancoras"]["aprovada"] = True
    salvar()


def cx(u):
    return (u["bbox"][0] + u["bbox"][2]) / 2


def cy(u):
    return (u["bbox"][1] + u["bbox"][3]) / 2


def tipo_unidade(u):
    t = u["tipo"]
    return "tabela" if t in ("table", "tabela") else "imagem" if t in ("picture", "imagem", "figura") else "texto"


def contexto(p, ws):
    """Somente campos automaticos; jamais recebe ranks ou ordens de referencia."""
    auto = automatico(p)
    cs = auto["bounding_boxes"]
    ordem, diag = b.prever(auto, ws, "regra_colunas")
    exp = {u["id"]: e.o.fluxo([u], ws) for u in cs}
    alturas = [w[4] - w[2] for w in ws if w[4] > w[2]]
    exigir(alturas, "Pagina sem alturas de palavra positivas")
    h = statistics.median(alturas)
    ini, corpo, marcas, fim = e.j.particao(cs, ws, auto["dimensions"]["height"], "geo")
    cortes = e.o.vales_locais(cs, corpo, h, e.FIXA.vale) if corpo else []
    if not cortes and corpo:
        cortes = e.o.vales(cs, corpo, h, e.FIXA.vale)
    largura = max(u["bbox"][2] for u in cs) - min(u["bbox"][0] for u in cs)
    margem = {cs[i]["id"]: t for ids, t in ((ini, "topo"), (fim, "rodape"), (marcas, "marca")) for i in ids}
    cols = {u["id"]: bisect.bisect_right(cortes, cx(u)) for u in cs}
    pontes = {u["id"] for u in cs if any(u["bbox"][0] < c < u["bbox"][2] and
              min(c-u["bbox"][0], u["bbox"][2]-c) >= .10*largura for c in cortes)}
    mapa = {u["id"]: u for u in cs}
    grupos = {col: sorted((u["id"] for u in cs if cols[u["id"]] == col and
                          u["id"] not in pontes and u["id"] not in margem),
                         key=lambda uid: (mapa[uid]["bbox"][1], mapa[uid]["bbox"][0]))
              for col in range(len(cortes)+1)}
    pos = {uid: i / max(1, len(g)-1) for g in grupos.values() for i, uid in enumerate(g)}
    return {"auto": auto, "cs": cs, "mapa": {u["id"]: u for u in cs}, "ws": ws, "h": h,
            "ordem": ordem, "regra": dict(zip(ordem, ordem[1:] + [None])), "diag": diag,
            "exp": exp, "col": cols, "cortes": cortes, "pontes": pontes, "margem": margem,
            "grupos": grupos, "pos": pos, "rank_regra": {uid: i for i, uid in enumerate(ordem)},
            "entrada": [cs[i]["id"] for i in ordem_entrada(auto)],
            "objetos": [u for u in cs if tipo_unidade(u) != "texto" or u["id"] in pontes]}


def sobreposicao(a, z):
    ba, bz = a["bbox"], z["bbox"]
    return max(0., min(ba[2], bz[2])-max(ba[0], bz[0])) / max(1., min(ba[2]-ba[0], bz[2]-bz[0]))


def obstaculos(ctx, a, z):
    if z is None:
        return 0
    lo, hi = sorted((cy(a), cy(z)))
    x0, x1 = min(a["bbox"][0], z["bbox"][0]), max(a["bbox"][2], z["bbox"][2])
    return sum(u["id"] not in (a["id"], z["id"]) and lo < cy(u) < hi and
               u["bbox"][0] < x1 and u["bbox"][2] > x0 for u in ctx["objetos"])


def categoria(ctx, a, z, *, bbox_a=None, bbox_z=None):
    """Tipologia exclusiva, geometrica e sem classes humanas.

    Precedencia: margem, atomo, ponte, retorno entre colunas, continuacao, outro.
    Calhas sao proxies globais do corpo; nao prova causal nem anotacao humana.
    """
    if a is None or z is None:
        return "outro"
    ua, uz = ctx["mapa"][a], ctx["mapa"][z]
    if a in ctx["margem"] or z in ctx["margem"]:
        return "margem"
    if tipo_unidade(ua) != "texto" or tipo_unidade(uz) != "texto":
        return "tabela_imagem" if a != z else "outro"
    if a in ctx["pontes"] or z in ctx["pontes"] or obstaculos(ctx, ua, uz):
        return "transversal"
    aa = {"bbox": bbox_a or ua["bbox"]}
    zz = {"bbox": bbox_z or uz["bbox"]}
    ca, cz = bisect.bisect_right(ctx["cortes"], cx(aa)), bisect.bisect_right(ctx["cortes"], cx(zz))
    if cz == ca+1 and cy(zz) < cy(aa)-2*ctx["h"] and ctx["pos"].get(a, 0) >= .65 and ctx["pos"].get(z, 1) <= .35:
        return "proxima_coluna"
    if ca == cz and cy(zz) >= cy(aa)-.5*ctx["h"] and sobreposicao(aa, zz) >= .25:
        return "mesma_coluna"
    return "outro"


def confianca_regra(ctx, uid):
    """Proxy geometrico, nao probabilidade calibrada fornecida pela regra."""
    z = ctx["regra"][uid]
    if z is None:
        return .5
    a, alvo = ctx["mapa"][uid], ctx["mapa"][z]
    gap = (alvo["bbox"][1]-a["bbox"][3]) / ctx["h"]
    if categoria(ctx, uid, z) == "mesma_coluna" and -.5 <= gap <= 2.5 and sobreposicao(a, alvo) >= .75:
        return .99
    return .5


def candidatos(ctx, uid, nivel):
    """Todos os desempates partem da entrada embaralhada, sem consultar ouro."""
    a = ctx["mapa"][uid]
    ent = [z for z in ctx["entrada"] if z != uid]
    if nivel == -1:
        return ent + [None]
    out = []
    def incluir(z):
        if z != uid and z not in out:
            out.append(z)
    incluir(ctx["regra"][uid])
    abaixo = sorted((z for z in ent if ctx["col"][z] == ctx["col"][uid] and cy(ctx["mapa"][z]) > cy(a)+.25*ctx["h"]),
                    key=lambda z: (cy(ctx["mapa"][z])-cy(a), abs(cx(ctx["mapa"][z])-cx(a))))
    if abaixo:
        incluir(abaixo[0])
    proxima = sorted((z for z in ent if ctx["col"][z] == ctx["col"][uid]+1),
                     key=lambda z: (ctx["mapa"][z]["bbox"][1], ctx["mapa"][z]["bbox"][0]))
    if proxima:
        incluir(proxima[0])
    trans = sorted((z for z in ent if z in ctx["pontes"] and cy(ctx["mapa"][z]) > cy(a)),
                   key=lambda z: cy(ctx["mapa"][z])-cy(a))
    if trans:
        incluir(trans[0])
    proximos = sorted(ent, key=lambda z: math.hypot(cx(ctx["mapa"][z])-cx(a), cy(ctx["mapa"][z])-cy(a)))
    for z in proximos[:nivel]:
        incluir(z)
    if nivel > 3:
        for z in abaixo[:nivel] + proxima[:nivel]:
            incluir(z)
        # Inclui retornos ao topo, vizinhos na ordem-base e objetos proximos.
        for col in sorted(ctx["grupos"]):
            for z in ctx["grupos"][col][:nivel]:
                incluir(z)
        na_regra = sorted(ent, key=lambda z: abs(ctx["rank_regra"][z]-ctx["rank_regra"][uid]))
        for z in na_regra[:nivel]:
            incluir(z)
        for z in sorted((u["id"] for u in ctx["objetos"] if u["id"] != uid),
                        key=lambda z: abs(cy(ctx["mapa"][z])-cy(a)))[:nivel]:
            incluir(z)
    incluir(None)
    # Retira a ordem de montagem como possivel feature implicita.
    return [z for z in ent if z in out] + [None]


def preparar_avaliacao(obj, p, ctx):
    med, seq, q, exp = medir(obj, p, ctx["ordem"])
    dono = {k: uid for uid, ks in exp.items() for k in ks}
    ranks = {k: i for i, k in enumerate(seq)}
    ls = {L["id"]: L for L in q["gold_lines"]}
    intactas = {lid: all(ranks[z] == ranks[a]+1 for a, z in zip(L["ks"], L["ks"][1:])) for lid, L in ls.items()}
    trs = []
    for la, lz in zip(q["gt_l"], q["gt_l"][1:]):
        ka, kz = ls[la]["ks"][-1], ls[lz]["ks"][0]
        ua, uz = dono[ka], dono[kz]
        interno = ua == uz
        alcancavel = (ranks[kz] == ranks[ka]+1) if interno else exp[ua][-1] == ka and exp[uz][0] == kz
        bbox_a = e.o.envelope([obj["palavras"][k][1:5] for k in ls[la]["ks"]])
        bbox_z = e.o.envelope([obj["palavras"][k][1:5] for k in ls[lz]["ks"]])
        trs.append({"linha_a": la, "linha_z": lz, "palavra_a": ka, "palavra_z": kz,
                    "a": ua, "z": uz, "interno": interno, "alcancavel": alcancavel,
                    "tipo": categoria(ctx, ua, uz, bbox_a=bbox_a, bbox_z=bbox_z),
                    "acerto": intactas[la] and intactas[lz] and ranks[kz] == ranks[ka]+1})
    # A anotacao de cada transicao apenas decompoe a metrica oficial importada.
    if trs:
        exigir(abs(sum(t["acerto"] for t in trs)/len(trs) - med["sucessor_linhas"]) < 1e-12,
               "Diagnostico de linhas diverge da regua oficial")
    ev = e.eventos(seq, q["gt_w"])
    cont = {t: {"ouro": 0, "acertos": 0, "erros": 0, "quebras_palavra": 0,
                "internas": 0, "transicoes_internas": 0, "inalcancaveis": 0} for t in TIPOS}
    for t in trs:
        r = cont[t["tipo"]]
        r["ouro"] += 1
        r["acertos"] += int(t["acerto"])
        r["erros"] += int(not t["acerto"])
        r["transicoes_internas"] += int(t["interno"])
        r["inalcancaveis"] += int(not t["alcancavel"])
    for evn in ev:
        z = dono.get(evn["esperado"])
        cat = categoria(ctx, dono[evn["a"]], z)
        cont[cat]["quebras_palavra"] += 1
        cont[cat]["internas"] += int(dono[evn["a"]] == dono[evn["b"]])
    exigir(sum(r["quebras_palavra"] for r in cont.values()) == med["quebras"], "Quebras nao particionadas")
    exemplos = [{**t, "texto_a": " ".join(obj["palavras"][k][0] for k in ls[t["linha_a"]]["ks"][-6:]),
                 "texto_z": " ".join(obj["palavras"][k][0] for k in ls[t["linha_z"]]["ks"][:6])}
                for t in trs if not t["acerto"]][:12]
    return med, cont, trs, exemplos


def metadados(p):
    uf = p["uf"]
    return {"page_id": p["page_id"], "uf": uf,
            "visto_split": uf in ESTADO["splits"]["treino"],
            "visto_treino": uf in ESTADO["inventario"]["treino_veiculos_efetivos"]}


def diagnostico():
    for c in HUMANAS:
        saida = ESTADO.setdefault("diagnostico", {}).setdefault(c, {"completa": False, "paginas": []})
        rows = []
        for obj, p in paginas(c):
            vigiar()
            cp = DIR_EXEC / "diagnostico" / c / (e.ac.chave(p["page_id"])+".json")
            if cp.exists():
                row = ler(cp)
            else:
                ctx = contexto(p, obj["palavras"])
                med, cont, trs, exemplos = preparar_avaliacao(obj, p, ctx)
                row = {**metadados(p), "metricas": med, "tipos": cont, "exemplos": exemplos}
                # Auditoria integral por transicao, sem milhares de palavras juntas.
                gravar(cp, {**row, "transicoes": trs})
            row.pop("transicoes", None)
            rows.append(row)
            saida["paginas"] = rows
            salvar()
            print(f"Diagnostico {c}: {len(rows)}", flush=True)
        saida["completa"] = True
        salvar()


def medir_candidatos(c, nivel):
    rows = []
    for obj, p in paginas(c):
        vigiar()
        cp = DIR_EXEC / "candidatos" / str(nivel) / c / (e.ac.chave(p["page_id"])+".json")
        if cp.exists():
            row = ler(cp)
        else:
            ctx = contexto(p, obj["palavras"])
            _, _, trs, _ = preparar_avaliacao(obj, p, ctx)
            cont = {t: {"total": 0, "cobertos": 0, "entre_unidades": 0,
                        "cobertos_entre": 0, "internos": 0, "inalcancaveis": 0} for t in TIPOS}
            cand = {}
            for tr in trs:
                uid = tr["a"]
                if uid not in cand and not tr["interno"]:
                    cand[uid] = candidatos(ctx, uid, nivel)
                ok = tr["alcancavel"] and (tr["interno"] or tr["z"] in cand[uid])
                co = cont[tr["tipo"]]
                co["total"] += 1
                co["cobertos"] += int(ok)
                co["internos"] += int(tr["interno"])
                co["inalcancaveis"] += int(not tr["alcancavel"])
                co["entre_unidades"] += int(not tr["interno"] and tr["alcancavel"])
                co["cobertos_entre"] += int(ok and not tr["interno"])
            tamanhos = [len(v)-1 for v in cand.values()]
            row = {**metadados(p), "tipos": cont, "fontes": len(tamanhos),
                   "candidatos_soma": sum(tamanhos), "candidatos_max": max(tamanhos, default=0)}
            gravar(cp, row)
        rows.append(row)
        ESTADO.setdefault("candidatos", {}).setdefault(str(nivel), {})[c] = {"completa": False, "paginas": rows}
        salvar()
    ESTADO["candidatos"][str(nivel)][c] = {"completa": True, "paginas": rows}
    salvar()
    return rows


def recall(rows):
    total = sum(v["total"] for r in rows for v in r["tipos"].values())
    cobertos = sum(v["cobertos"] for r in rows for v in r["tipos"].values())
    return cobertos / total if total else 0.


def etapa_candidatos():
    if "nivel_candidatos" in ESTADO:
        return
    for nivel in NIVEIS:
        medidas = {c: recall(medir_candidatos(c, nivel)) for c in HUMANAS + ("validacao_silver",)}
        ESTADO["escalonamento_candidatos"] = [v for v in ESTADO.get("escalonamento_candidatos", []) if v["nivel"] != nivel]
        ESTADO["escalonamento_candidatos"].append({"nivel": nivel, "recall": medidas})
        salvar()
        if all(r >= .95 for r in medidas.values()):
            ESTADO["nivel_candidatos"] = nivel
            salvar()
            return
    raise Interromper("Recall total abaixo de 95% mesmo com todos os sucessores. O limite agora é estrutural; parar antes do corretor.")


BASE_FEATURES = ("fim", "dx_h", "dy_h", "gap_y_h", "gap_x_h", "overlap_x", "alinha_esq_h",
                 "alinha_dir_h", "largura_a_h", "largura_z_h", "altura_a_h", "altura_z_h",
                 "x_a", "y_a", "x_z", "y_z", "col_a", "col_z", "mesma_col", "pos_col_a",
                 "pos_col_z", "calha_entre", "objeto_entre", "ponte_a", "ponte_z", "margem_a",
                 "margem_z", "regra_escolheu", "confianca_regra", "dist_posto_regra")
ESTILO = ("ponto_final", "pontuacao_final", "hifen_final", "maiuscula_inicio", "lista", "n_palavras")
FEATURES = BASE_FEATURES + tuple("tipo_par_"+t for t in TIPOS) + tuple("tipo_regra_"+t for t in TIPOS) + tuple(
    prefixo+nome for prefixo in ("a_", "z_") for nome in ESTILO) + tuple(
    prefixo+t for prefixo in ("tipo_a_", "tipo_z_") for t in ("texto", "tabela", "imagem"))


def estilo(ctx, uid):
    if uid is None:
        return [0.] * len(ESTILO)
    ks = ctx["exp"][uid]
    tokens = [ctx["ws"][k][0] for k in ks]
    texto = " ".join(tokens).strip()
    inicio = next((c for c in texto if c.isalpha()), "")
    return [float(texto.endswith((".", "!", "?"))), float(texto.endswith((".", ",", ";", ":", "!", "?"))),
            float(texto.endswith(("-", "‐", "\u00ad"))), float(bool(inicio) and inicio.isupper()),
            float(bool(re.match(r"^\s*(?:[•*\-–]|\(?\d+[.)]|[IVXLCDM]+\s*[-–.)]|[a-zA-Z][.)])", texto))),
            math.log1p(len(tokens))]


def features(ctx, uid, zid):
    a = ctx["mapa"][uid]
    z = ctx["mapa"].get(zid)
    ba, bz = a["bbox"], z["bbox"] if z else [0., 0., 0., 0.]
    h = max(.1, ctx["h"])
    W, H = ctx["auto"]["dimensions"]["width"], ctx["auto"]["dimensions"]["height"]
    def norm(v):
        return max(-50., min(50., v/h))
    cat = categoria(ctx, uid, zid)
    geo = [float(z is None), norm(cx(z)-cx(a)) if z else 0., norm(cy(z)-cy(a)) if z else 0.,
           norm(bz[1]-ba[3]) if z else 0., norm(max(ba[0], bz[0])-min(ba[2], bz[2])) if z else 0.,
           sobreposicao(a, z) if z else 0., norm(bz[0]-ba[0]) if z else 0., norm(bz[2]-ba[2]) if z else 0.,
           norm(ba[2]-ba[0]), norm(bz[2]-bz[0]) if z else 0., norm(ba[3]-ba[1]), norm(bz[3]-bz[1]) if z else 0.,
           cx(a)/W, cy(a)/H, cx(z)/W if z else 0., cy(z)/H if z else 0., ctx["col"][uid]/4,
           ctx["col"].get(zid, 0)/4, float(z is not None and ctx["col"][uid] == ctx["col"][zid]),
           ctx["pos"].get(uid, .5), ctx["pos"].get(zid, .5),
           float(z is not None and any(min(cx(a), cx(z)) < c < max(cx(a), cx(z)) for c in ctx["cortes"])),
           min(10, obstaculos(ctx, a, z))/10, float(uid in ctx["pontes"]), float(zid in ctx["pontes"]),
           float(uid in ctx["margem"]), float(zid in ctx["margem"]), float(ctx["regra"][uid] == zid),
           confianca_regra(ctx, uid), (ctx["rank_regra"].get(zid, len(ctx["cs"]))-ctx["rank_regra"][uid])/max(1, len(ctx["cs"]))]
    cat_regra = categoria(ctx, uid, ctx["regra"][uid])
    vals = geo + [float(cat == t) for t in TIPOS] + [float(cat_regra == t) for t in TIPOS] + estilo(ctx, uid) + estilo(ctx, zid)
    vals += [float(tipo_unidade(u) == t) if u else 0. for u in (a, z) for t in ("texto", "tabela", "imagem")]
    exigir(len(vals) == len(FEATURES) and all(math.isfinite(v) for v in vals), "Feature invalida")
    return vals


def alvos_silver(obj, ctx):
    """Supervisao apenas depois das features: fronteiras contiguas verificaveis.

    Nao transforma mediana de unidade atravessada em ouro de sucessor.
    Exclui fonte/alvo cuja expansao canonica diverge do trecho do fluxo PDF.
    FIN participa como negativo em todas as fontes e positivo no fim real.
    """
    gt = obj["gt_w"]
    rank = {k: i for i, k in enumerate(gt)}
    dono = {k: uid for uid, ks in ctx["exp"].items() for k in ks}
    validas, causas = set(), collections.Counter()
    for uid, ks in ctx["exp"].items():
        if not ks:
            causas["sem_palavras"] += 1
            continue
        if ks != gt[rank[ks[0]]:rank[ks[-1]]+1]:
            causas["fonte_nao_contigua_ou_interna_divergente"] += 1
            continue
        validas.add(uid)
    alvos = {}
    for uid in ctx["entrada"]:
        if uid not in validas:
            continue
        ultimo = ctx["exp"][uid][-1]
        pos = rank[ultimo]
        if pos == len(gt)-1:
            alvos[uid] = None
            continue
        seguinte = gt[pos+1]
        zid = dono[seguinte]
        if zid not in validas or ctx["exp"][zid][0] != seguinte:
            causas["alvo_nao_contiguo_ou_fronteira_interna"] += 1
            continue
        alvos[uid] = zid
    return alvos, dict(causas)


def pares_treino(m, nivel):
    """JSONL de grupos, nunca corpus de palavras ou matriz quadratica em RAM."""
    pth = DIR_EXEC / "pares_treino" / (e.ac.chave(m["page_id"])+".jsonl")
    meta = pth.with_suffix(".meta.json")
    if pth.exists() and meta.exists():
        me = ler(meta)
        exigir(sha(pth) == me["sha256"], "Cache de pares alterado")
        return pth, me
    vigiar()
    obj, p = ler_meta(m)
    ctx = contexto(p, obj["palavras"])
    alvos, causas = alvos_silver(obj, ctx)
    tmp = destino(pth).with_suffix(".jsonl.tmp")
    grupos, pares, faltas = 0, 0, 0
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for uid in ctx["entrada"]:
            if uid not in alvos:
                continue
            vigiar()
            cand = candidatos(ctx, uid, nivel)
            if alvos[uid] not in cand:
                faltas += 1
                continue
            row = {"a": uid, "candidatos": cand, "y": cand.index(alvos[uid]),
                   "x": [features(ctx, uid, z) for z in cand]}
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+"\n")
            grupos += 1
            pares += len(cand)
        f.flush()
        os.fsync(f.fileno())
    substituir(tmp, pth)
    me = {**metadados(p), "grupos": grupos, "pares": pares, "alvos_fora_candidatos": faltas,
          "filtradas": causas, "nivel": nivel, "sha256": sha(pth)}
    gravar(meta, me)
    return pth, me


def normalizacao(paths):
    cp = DIR_EXEC / "normalizacao.json"
    if cp.exists():
        return ler(cp)
    np = e.np
    soma, quadrados, n = np.zeros(len(FEATURES)), np.zeros(len(FEATURES)), 0
    for pth in paths:
        vigiar()
        for g in b.jsonl(pth):
            x = np.asarray(g["x"], dtype=np.float64)
            soma += x.sum(axis=0)
            quadrados += (x*x).sum(axis=0)
            n += len(x)
    exigir(n > 0, "Nenhum par treinavel nesta amostra")
    media = soma/n
    desvio = np.sqrt(np.maximum(quadrados/n-media*media, 1e-6))
    obj = {"features": list(FEATURES), "media": media.tolist(), "desvio": desvio.tolist(), "pares": n,
           "origem": "somente treino silver"}
    gravar(cp, obj)
    return obj


def salvar_torch(torch, p, obj):
    p = destino(p)
    tmp = p.with_suffix(p.suffix+".tmp")
    with open(tmp, "wb") as f:
        torch.save(obj, f)
        f.flush()
        os.fsync(f.fileno())
    substituir(tmp, p)


def treinar(args):
    nivel = ESTADO["nivel_candidatos"]
    metas, paths = [], []
    for m in ESTADO["inventario"]["planos"]["treino"]:
        pth, meta = pares_treino(m, nivel)
        paths.append(pth)
        metas.append(meta)
        ESTADO["treino"] = {**ESTADO.get("treino", {}), "pares_paginas": metas, "pares_prontos": len(metas)}
        salvar()
    norm = normalizacao(paths)
    vigiar()
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(SEMENTE)
    device = torch.device("cpu")
    modelo = torch.nn.Sequential(torch.nn.Linear(len(FEATURES), 32), torch.nn.ReLU(), torch.nn.Linear(32, 1)).to(device)
    otimizador = torch.optim.Adam(modelo.parameters(), lr=.001)
    media = torch.tensor(norm["media"], dtype=torch.float32, device=device)
    desvio = torch.tensor(norm["desvio"], dtype=torch.float32, device=device)
    cp = DIR_EXEC / "modelo.pt"
    estado = {"epoca": 0, "pagina": 0, "perda_soma": 0., "grupos": 0, "historico": []}
    if cp.exists():
        salvo = torch.load(cp, map_location="cpu", weights_only=False)
        exigir(salvo["fingerprint"] == ESTADO["fingerprint"], "Checkpoint de outro experimento")
        modelo.load_state_dict(salvo["modelo"])
        otimizador.load_state_dict(salvo["otimizador"])
        torch.set_rng_state(salvo["rng"])
        estado = salvo["cursor"]
        del salvo
    # Recupera tambem o progresso caso o laptop caia entre salvar pesos e
    # atualizar o Markdown. O checkpoint e a fonte de verdade do cursor.
    ESTADO["treino"].update(cursor=json.loads(json.dumps(estado)), checkpoint=rel(cp),
                           parametros=sum(v.numel() for v in modelo.parameters()), device="cpu",
                           threads=4, num_workers=0, completa=estado["epoca"] == args.epocas)
    salvar()
    while estado["epoca"] < args.epocas:
        modelo.train()
        for j in range(estado["pagina"], len(paths)):
            vigiar()
            for grupo in b.jsonl(paths[j]):
                vigiar()
                x = torch.tensor(grupo["x"], dtype=torch.float32, device=device)
                y = torch.tensor([grupo["y"]], dtype=torch.long, device=device)
                otimizador.zero_grad(set_to_none=True)
                logits = modelo((x-media)/desvio).reshape(1, -1)
                perda = torch.nn.functional.cross_entropy(logits, y)
                exigir(torch.isfinite(perda).item(), "Perda nao finita")
                perda.backward()
                torch.nn.utils.clip_grad_norm_(modelo.parameters(), 2.)
                otimizador.step()
                estado["perda_soma"] += perda.item()
                estado["grupos"] += 1
            estado["pagina"] = j+1
            if estado["pagina"] == len(paths):
                exigir(estado["grupos"] > 0, "Epoca sem grupos")
                estado["historico"].append({"epoca": estado["epoca"]+1,
                    "perda": estado["perda_soma"]/estado["grupos"], "grupos": estado["grupos"]})
                estado.update(epoca=estado["epoca"]+1, pagina=0, perda_soma=0., grupos=0)
            salvar_torch(torch, cp, {"fingerprint": ESTADO["fingerprint"], "modelo": modelo.state_dict(),
                          "otimizador": otimizador.state_dict(), "rng": torch.get_rng_state(), "cursor": estado,
                          "normalizacao": norm, "device": "cpu"})
            ESTADO["treino"].update(cursor=json.loads(json.dumps(estado)), checkpoint=rel(cp), parametros=sum(v.numel() for v in modelo.parameters()),
                                    device="cpu", threads=4, num_workers=0, completa=estado["epoca"] == args.epocas)
            salvar()
            print(f"MLP CPU: epocas concluidas {estado['epoca']}, pagina {estado['pagina']}", flush=True)
        gc.collect()
    ESTADO["treino"]["checkpoint_sha256"] = sha(cp)
    salvar()
    modelo.eval()
    return torch, modelo, media, desvio


def escolhas(ctx, torch, modelo, media, desvio):
    """Inferencia por fonte: so candidatos geometricos, jamais referencias."""
    out = {}
    with torch.inference_mode():
        for uid in ctx["entrada"]:
            vigiar()
            cand = candidatos(ctx, uid, ESTADO["nivel_candidatos"])
            x = torch.tensor([features(ctx, uid, z) for z in cand], dtype=torch.float32, device="cpu")
            prob = torch.softmax(modelo((x-media)/desvio).flatten(), dim=0)
            vals = prob.tolist()
            indice = max(range(len(cand)), key=lambda k: vals[k])
            out[uid] = {"z": cand[indice], "prob": vals[indice], "n_candidatos": len(cand),
                        "prob_regra": vals[cand.index(ctx["regra"][uid])],
                        "confianca_regra": confianca_regra(ctx, uid),
                        "ambigua": confianca_regra(ctx, uid) < .95}
    return out


def decodificar(regra, escolhas_por_fonte, limiar=None):
    """Arestas sem ciclos/duplo predecessor; reata cabecas pelo posto-base.

    Hibrido conserva arestas da regra fora das propostas aceitas. Conflitos
    podem alterar outras fronteiras: a regua mede a ordem realizada, nao so
    as propostas. limiar=None e o corretor com todas as escolhas de pares.
    limiar>1 restitui exatamente a regra, inclusive unidades sem palavras.
    """
    sozinho = limiar is None
    antigo = dict(zip(regra, regra[1:]+[None]))
    rank = {uid: i for i, uid in enumerate(regra)}
    propostas = [(a, c["z"], c["prob"]) for a, c in escolhas_por_fonte.items()
                 if sozinho or c["ambigua"] and c["prob"] >= limiar and c["z"] != antigo[a]]
    propostas.sort(key=lambda t: (-t[2], rank[t[0]]))
    pai = {uid: uid for uid in regra}
    def raiz(uid):
        while pai[uid] != uid:
            pai[uid] = pai[pai[uid]]
            uid = pai[uid]
        return uid
    succ, pred, aceitas = {}, {}, set()
    conflitos, ciclos = 0, 0
    for a, z, prob in propostas:
        if z is None:
            aceitas.add(a)
            continue
        if z in pred:
            conflitos += 1
            continue
        if raiz(a) == raiz(z):
            ciclos += 1
            continue
        succ[a], pred[z] = z, a
        pai[raiz(a)] = raiz(z)
        aceitas.add(a)
    if not sozinho:
        for a, z in zip(regra, regra[1:]):
            if a in aceitas or a in succ or z in pred or raiz(a) == raiz(z):
                continue
            succ[a], pred[z] = z, a
            pai[raiz(a)] = raiz(z)
    cabecas = sorted((uid for uid in regra if uid not in pred), key=rank.__getitem__)
    ordem = []
    for uid in cabecas:
        while uid is not None:
            ordem.append(uid)
            uid = succ.get(uid)
    exigir(len(ordem) == len(regra) and set(ordem) == set(regra), "Decodificador perdeu/repetiu unidade")
    realizado = dict(zip(ordem, ordem[1:]+[None]))
    mantidas = sum(realizado[a] == z for a, z, _ in propostas)
    if not propostas and not sozinho:
        exigir(ordem == regra, "Limiar sem propostas mudou a regra")
    return ordem, {"propostas": len(propostas), "aceitas_no_grafo": len(aceitas), "mantidas_na_ordem": mantidas,
                   "conflitos": conflitos, "ciclos": ciclos, "cadeias": len(cabecas),
                   "fronteiras_alteradas": sum(realizado[a] != antigo[a] for a in regra)}


def top1(trs, ctx, scores, limiar):
    """Metricas de pares novas; sucessor de linhas oficial continua em medir()."""
    cont = {"total": 0, "regra": 0, "corretor": 0, "hibrido": 0,
            "internas": 0, "inalcancaveis": 0, "por_tipo": {t: {"total": 0, "regra": 0, "corretor": 0, "hibrido": 0} for t in TIPOS}}
    for tr in trs:
        if tr["interno"]:
            cont["internas"] += 1
            continue
        if not tr["alcancavel"]:
            cont["inalcancaveis"] += 1
            continue
        a, z = tr["a"], tr["z"]
        c = scores[a]
        ch = c["z"] if c["ambigua"] and c["prob"] >= limiar else ctx["regra"][a]
        escolhas_raw = {"regra": ctx["regra"][a], "corretor": c["z"], "hibrido": ch}
        cont["total"] += 1
        cont["por_tipo"][tr["tipo"]]["total"] += 1
        for m, pred in escolhas_raw.items():
            cont[m] += int(pred == z)
            cont["por_tipo"][tr["tipo"]][m] += int(pred == z)
    return cont


def avaliar_modelo(c, limiares, modelo_info):
    torch, modelo, media, desvio = modelo_info
    rows = []
    for obj, p in paginas(c):
        vigiar()
        cp = DIR_EXEC / "avaliacao" / c / (e.ac.chave(p["page_id"])+".json")
        if cp.exists():
            row = ler(cp)
            exigir(row["limiares"] == list(limiares), "Cache de avaliacao com outros limiares")
        else:
            ctx = contexto(p, obj["palavras"])
            mr, _, trs, _ = preparar_avaliacao(obj, p, ctx)
            scores = escolhas(ctx, torch, modelo, media, desvio)
            oc, dc = decodificar(ctx["ordem"], scores)
            mc = medir(obj, p, oc)[0]
            memo = {digest(ctx["ordem"]): mr, digest(oc): mc}
            hs = {}
            for lim in limiares:
                vigiar()
                oh, dh = decodificar(ctx["ordem"], scores, lim)
                sig = digest(oh)
                if sig not in memo:
                    memo[sig] = medir(obj, p, oh)[0]
                hs[str(lim)] = {"metricas": memo[sig], "diag": dh, "ordem": oh,
                                "top1": top1(trs, ctx, scores, lim)}
            row = {**metadados(p), "limiares": list(limiares), "regra": mr, "corretor": mc,
                   "diag_corretor": dc, "hibridos": hs, "ordem_regra": ctx["ordem"], "ordem_corretor": oc,
                   "escolhas": scores, "ambigua_total": sum(s["ambigua"] for s in scores.values()),
                   "fontes_total": len(scores)}
            gravar(cp, row)
        # Mantem apenas numeros e IDs de pagina no estado global, sem palavras/ordens.
        compacto = {k: row[k] for k in ("page_id", "uf", "visto_split", "visto_treino", "regra", "corretor",
                                        "diag_corretor", "ambigua_total", "fontes_total")}
        compacto["hibridos"] = {lim: {k: v[k] for k in ("metricas", "diag", "top1")} for lim, v in row["hibridos"].items()}
        rows.append(compacto)
        ESTADO.setdefault("avaliacao", {})[c] = {"completa": False, "paginas": rows}
        salvar()
        print(f"Avaliacao {c}: {len(rows)}", flush=True)
    ESTADO["avaliacao"][c] = {"completa": True, "paginas": rows}
    salvar()
    return rows


def escolher_limiar(rows):
    exigir(rows, "Validacao RN vazia depois da exclusao humana")
    qb = statistics.mean(r["regra"]["quebras"] for r in rows)
    tau = statistics.mean(r["regra"]["tau"] for r in rows)
    tabela = []
    for lim in LIMIARES:
        vals = [r["hibridos"][str(lim)] for r in rows]
        mq = statistics.mean(v["metricas"]["quebras"] for v in vals)
        mt = statistics.mean(v["metricas"]["tau"] for v in vals)
        propostas = sum(v["diag"]["propostas"] for v in vals)
        tabela.append({"limiar": lim, "quebras": mq, "tau": mt, "propostas": propostas,
                       "elegivel": mt >= tau-1e-9 and mq <= qb})
    elegiveis = [v for v in tabela if v["elegivel"]]
    exigir(elegiveis, "Limiar desativado nao reproduziu regra na RN")
    escolhido = min(elegiveis, key=lambda v: (v["quebras"], -v["tau"], v["propostas"], -v["limiar"]))
    ESTADO["validacao"] = {"n": len(rows), "veiculos": sorted({r["uf"] for r in rows}), "limiar": escolhido["limiar"],
                           "tabela": tabela, "regra": {"quebras": qb, "tau": tau},
                           "melhora": escolhido["quebras"] < qb, "origem": "somente RN, excluidas paginas humanas"}
    salvar()
    return escolhido["limiar"]


def exportar_predicoes(c, lim):
    """Contrato estrito da bancada; escreve so no cache desta tarefa."""
    for metodo in ("corretor_transicoes", "hibrido_transicoes"):
        pth = destino(DIR_EXEC / "pred" / f"{metodo}__linhas__{c}.jsonl")
        tmp = pth.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            for obj, p in paginas(c):
                cp = DIR_EXEC / "avaliacao" / c / (e.ac.chave(p["page_id"])+".json")
                if not cp.exists():
                    continue
                row = ler(cp)
                ordem = row["ordem_corretor"] if metodo == "corretor_transicoes" else row["hibridos"][str(lim)]["ordem"]
                f.write(json.dumps({"page_id": p["page_id"], "ordem": ordem}, ensure_ascii=False)+"\n")
            f.flush()
            os.fsync(f.fileno())
        substituir(tmp, pth)


def inferencia(rows, lim):
    out = {}
    grupos = {"todos": rows, "vistos": [r for r in rows if r["visto_treino"]],
              "nao_vistos": [r for r in rows if not r["visto_treino"]]}
    for grupo, rs in grupos.items():
        if not rs:
            out[grupo] = {"n": 0}
            continue
        W = e.pesos_cluster(rs)
        ms, testes = {}, {}
        for metodo in ("regra", "corretor", "hibrido"):
            def valores(r, k):
                return r["hibridos"][str(lim)]["metricas"][k] if metodo == "hibrido" else r[metodo][k]
            ms[metodo] = {k: e.media_ic([valores(r, k) for r in rs], W) for k in METRICAS}
        for k in METRICAS:
            paired = [r for r in rs if r["regra"][k] is not None and r["hibridos"][str(lim)]["metricas"][k] is not None]
            if not paired:
                continue
            ds = [r["hibridos"][str(lim)]["metricas"][k]-r["regra"][k] for r in paired]
            ufs = sorted({r["uf"] for r in paired})
            dv = [statistics.mean(d for r, d in zip(paired, ds) if r["uf"] == uf) for uf in ufs]
            testes[k] = {"delta": e.media_ic(ds, e.pesos_cluster(paired)),
                         "wilcoxon_pagina": e.pratt(ds), "wilcoxon_veiculo": e.pratt(dv),
                         "por_veiculo": dict(zip(ufs, dv)), "n": len(paired), "veiculos": len(ufs)}
        tops = [r["hibridos"][str(lim)]["top1"] for r in rs]
        raw = {k: sum(t[k] for t in tops) for k in ("total", "regra", "corretor", "hibrido", "internas", "inalcancaveis")}
        for metodo in ("regra", "corretor", "hibrido"):
            raw[metodo+"_macro"] = e.media_ic([t[metodo]/t["total"] if t["total"] else None for t in tops], W)
        out[grupo] = {"n": len(rs), "veiculos": len({r["uf"] for r in rs}), "metricas": ms, "testes": testes, "top1": raw,
                      "propostas": sum(r["hibridos"][str(lim)]["diag"]["propostas"] for r in rs),
                      "mantidas": sum(r["hibridos"][str(lim)]["diag"]["mantidas_na_ordem"] for r in rs),
                      "conflitos": sum(r["hibridos"][str(lim)]["diag"]["conflitos"] for r in rs),
                      "ciclos": sum(r["hibridos"][str(lim)]["diag"]["ciclos"] for r in rs),
                      "alteradas": sum(r["hibridos"][str(lim)]["diag"]["fronteiras_alteradas"] for r in rs)}
    return out


def etapa_corretor(args):
    info = treinar(args)
    rows_rn = avaliar_modelo("validacao_silver", LIMIARES, info)
    lim = escolher_limiar(rows_rn)
    # Nenhum limiar e selecionado usando bancada humana ou CE/MA/RJ.
    for c in HUMANAS + ("teste_silver",):
        avaliar_modelo(c, (lim,), info)
        exportar_predicoes(c, lim)
    # Cobertura no teste e somente descritiva, com o conjunto ja congelado.
    medir_candidatos("teste_silver", ESTADO["nivel_candidatos"])
    ESTADO["inferencia"] = {}
    for c in BANCADAS:
        rows = ESTADO["avaliacao"][c]["paginas"]
        ESTADO["inferencia"][c] = inferencia(rows, lim)
        salvar()
    ESTADO["completa"] = True
    salvar()


def f(v, casas=3):
    return "—" if v is None else format(v, f".{casas}f").replace(".", ",")


def frac(a, den):
    return "—" if not den else f(100*a/den, 2)+"%"


def cel(v, percentual=False, casas=3):
    fator = 100 if percentual else 1
    if not v or v.get("media") is None:
        return "—"
    txt = f(v["media"]*fator, casas)
    if v["ic"][0] is not None:
        txt += " ["+"; ".join(f(k*fator, casas) for k in v["ic"])+"]"
    return txt+("%" if percentual else "")


def estratos(rows, humana):
    yield "todos", rows
    if humana:
        yield "vistos", [r for r in rows if r["visto_treino"]]
        yield "não vistos", [r for r in rows if not r["visto_treino"]]


def decisao_final(R):
    """Veredito descritivo calculado, sem selecionar modelo pelo teste."""
    if not R.get("completa") or not R.get("inferencia"):
        return "Híbrido pendente; melhora ou piora ainda não foi medida."
    testes = [R["inferencia"][c]["todos"]["testes"] for c in HUMANAS + ("teste_silver",)]
    consistente = all(t["quebras"]["delta"]["media"] < 0 and
                      t["tau"]["delta"]["media"] >= 0 for t in testes)
    if not consistente:
        return ("Sem ganho consistente nas bancadas humanas e no teste silver: conservar a regra de colunas "
                "e encerrar esta demonstração sem ampliar o treino. A amostra pequena não permite excluir "
                "ganho de outra configuração do corretor.")
    sustentado = all(t["quebras"]["delta"]["ic"][1] < 0 for t in testes)
    return ("Menos quebras sem perda média de τ nas três bancadas; " +
            ("os intervalos de quebras excluem zero." if sustentado else
             "os intervalos ainda não sustentam ganho nas três bancadas; encerrar a demonstração como inconclusiva."))


def resumo_cinco(R):
    a = R.get("ancoras", {})
    l1 = "Âncoras pendentes; nenhum resultado novo foi liberado."
    if a.get("aprovada"):
        l1 = f"Âncoras aprovadas em {len(a['paginas'])} páginas: regra τ {f(a['medias']['regra']['tau'],6)}, {f(a['medias']['regra']['quebras'],6)} quebras/página."
    dg = R.get("diagnostico", {})
    ds = [r for c in HUMANAS for r in dg.get(c, {}).get("paginas", [])]
    l2 = "Diagnóstico pendente; não há contagens de transições nesta execução."
    if ds:
        co = {t: sum(r["tipos"][t]["quebras_palavra"] for r in ds) for t in TIPOS}
        pior = max(co, key=co.get)
        l2 = f"Diagnóstico {'completo' if all(dg.get(c, {}).get('completa') for c in HUMANAS) else 'parcial'}: {len(ds)} páginas; {ROTULOS[pior].lower()} reúne {co[pior]} quebras ({frac(co[pior],sum(co.values()))}); bancadas separadas abaixo."
    l3 = "Candidatos pendentes; o corretor aguarda a checagem de cobertura."
    es = R.get("escalonamento_candidatos", [])
    if es:
        ult = es[-1]
        l3 = "Candidatos: "+("todos os sucessores" if ult["nivel"] == -1 else f"nível {ult['nivel']}")+"; recall total "+", ".join(c+" "+frac(v,1) for c,v in ult["recall"].items())+"."
    treino = R.get("treino", {})
    l4 = "MLP não treinado; não há resultado do corretor."
    if treino.get("cursor"):
        l4 = f"MLP CPU: {len(R['inventario']['planos']['treino'])} páginas de treino, {treino['cursor']['epoca']} épocas concluídas; limiar RN {f(R.get('validacao',{}).get('limiar'),2)}."
    l5 = "Híbrido pendente; melhora ou piora ainda não foi medida."
    if R.get("completa") and R.get("inferencia"):
        partes = []
        for c in HUMANAS + ("teste_silver",):
            te = R["inferencia"][c]["todos"]["testes"]
            partes.append(c+f": Δ quebras {cel(te['quebras']['delta'])}, Δ τ {cel(te['tau']['delta'], casas=6)}")
        l5 = decisao_final(R)+" Δ híbrido−regra: "+"; ".join(partes)+"."
    if R.get("parada"):
        l5 = "Execução interrompida: "+R["parada"]
    return [l1, l2, l3, l4, l5]


def relatorio(R):
    lines = ["# Corretor de transições sobre linhas", ""]
    lines += [s+"  " for s in resumo_cinco(R)] + [""]
    lines += ["Relatório gerado pelo script; as medidas abaixo vêm dos caches desta execução. "
              "Resultados parciais são identificados por cobertura e não recebem uma conclusão final.", "",
              "## Protocolo e estado", "",
              "Regra congelada: `projecao_local_margens` com os parâmetros de `erros_ponta_a_ponta.FIXA`. "
              "Unidades de linhas e átomos congelados de ls3; texto vem da camada digital. "
              "Entrada pela função `ordem_entrada`, com a permutação `entrada-{page_id}`. "
              "Cada unidade é expandida por `ordem_sem_bbox.fluxo()`, como na bancada oficial.", "",
              "A régua de τ, quebras, fidelidade de trechos de palavras e sucessor de linhas é importada "
              "de `erros_ponta_a_ponta`; não foi reimplementada. `referencia`, `expansoes`, `auditar_unidades` "
              "e `prever` vêm da bancada. Não se chama sua função `metricas`, que escreveria no cache de outro experimento.", ""]
    if R.get("fingerprint"):
        lines += [f"Execução: `{R['fingerprint']}`. Estado, hashes e resultados por página em `{rel(DIR_EXEC / 'estado.json')}`.", ""]
    if R.get("config"):
        lines += ["Configuração efetiva: `"+json.dumps(R["config"], ensure_ascii=False)+"`.", ""]
    inv = R.get("inventario")
    # Inventario e cobertura novos ficam embargados ate passar a ancora.
    if inv and R.get("ancoras", {}).get("aprovada"):
        lines += ["Páginas de bancadas humanas, inclusive tarefas sem anotação concluída, são excluídas "
                  "do treino, da validação e do teste silver desta execução. As bancadas humanas continuam completas. "
                  "Esta exclusão é exigida pelo pedido; reduz a cobertura silver em relação à tabela histórica e "
                  "impede comparar diretamente suas médias com médias históricas sem pareamento.", "",
                  "| Partição silver | Páginas usadas | Páginas humanas excluídas | Veículos |", "|---|---:|---:|---:|"]
        for part in ("treino", "validacao", "teste"):
            ms = inv["planos"][part]
            lines.append(f"| {part} | {len(ms)} | {len(inv['excluidos'][part])} | {len({m['uf'] for m in ms})} |")
        lines += ["", f"Duplicatas base/extra idênticas deduplicadas: {len(inv['duplicatas_base_extra'])}. "
                  "A lista de páginas usada por cada split e as exclusões ficam no estado. "
                  "A amostra de treino é pequena e distribuída por veículo, escolhida pelo hash de IDs, sem consultar eficácia.", "",
                  "'Vistos' nas tabelas = veículos presentes na amostra de treino selecionada "
                  "(efetivamente usada quando o treino está concluído). "
                  "O estado também guarda `visto_split`, pertencimento aos veículos do split original, para distinguir "
                  "os dois conceitos quando a amostra pequena não cobre algum veículo. Não significa visto pelo detector ls3.", "",
                  "Veículos da amostra de treino: "+", ".join("`"+u+"`" for u in inv["treino_veiculos_efetivos"])+". "
                  f"PDFs compartilhados com tarefas humanas, em páginas diferentes: {len(inv['pdfs_compartilhados_humanas'])}.", ""]
    a = R.get("ancoras", {})
    lines += ["## Âncoras", "", f"Páginas rechecadas: {a.get('concluidas',0)}. Status: "+("aprovadas" if a.get("aprovada") else "pendentes ou divergentes")+".", ""]
    if a.get("medias"):
        lines += ["| Controle | τ palavras | Quebras/página |", "|---|---:|---:|"]
        for nome, v in a["medias"].items():
            lines.append(f"| {nome} | {f(v['tau'],6)} | {f(v['quebras'],6)} |")
        lines += ["", "Regra e P2 são reexecutados com detecções congeladas, sem carregar o detector. "
                  "Também se confere a igualdade das sequências com o P2 histórico. P1m é a medida histórica "
                  "de extrator + XY-cut + margens, importada de `resultados/erros_ponta_a_ponta.json`; "
                  "não é uma reextração nova. Tolerâncias, valores-alvo e verificações estão no script. "
                  "Se falhar, nenhuma tabela nova é liberada.", ""]
    if not a.get("aprovada"):
        if R.get("parada"):
            lines += ["Motivo da parada: "+R["parada"], ""]
        return "\n".join(lines)
    lines += ["## Etapa de diagnóstico", "",
              "Tipologia geométrica automática, em precedência exclusiva: margem (mesma partição da regra), "
              "tabela/imagem, elemento transversal ou obstáculo entre as linhas, retorno ao topo da próxima coluna, "
              "continuação na mesma coluna e outro. Fim/topo usam a posição relativa nas linhas de cada coluna; "
              "mudanças locais de calha podem cair em 'outro'. Não há ouro de classes/tipos nem inspeção humana "
              "que certifique estas causas. Transições dentro do mesmo átomo caem em 'outro', "
              "com marca de fronteira interna; não são entrada/saída de tabela. "
              "As caixas humanas não entram na classificação nem no modelo.", "",
              "'Acerto de linha' exige que ambas as linhas-ouro estejam intactas e consecutivas, exatamente como "
              "na régua oficial. O script confere a soma contra essa régua. Erros de sucessor-ouro e quebras "
              "emitidas são denominadores diferentes: uma ordem errada pode omitir uma transição-ouro e criar outra. "
              "A fração de quebras abaixo usa cada evento de palavra emitido, associado ao tipo da transição "
              "esperada para sua palavra de origem. Eventos dentro de linha/átomo não viram fronteiras treináveis.", ""]
    for c in HUMANAS:
        dg = R.get("diagnostico", {}).get(c)
        if not dg:
            lines += [f"{c}: pendente.", ""]
            continue
        rows = dg["paginas"]
        lines += [f"### {c} — "+("completo" if dg["completa"] else "parcial"), ""]
        for grupo, rs in estratos(rows, True):
            lines += [f"**{grupo}: {len(rs)} páginas, {len({r['uf'] for r in rs})} veículos.**", ""]
            if not rs:
                continue
            soma = {t: {k: sum(r["tipos"][t][k] for r in rs) for k in rs[0]["tipos"][t]} for t in TIPOS}
            qb = sum(v["quebras_palavra"] for v in soma.values())
            erros = sum(v["erros"] for v in soma.values())
            lines += ["| Tipo | Transições-ouro | Acertos | Erros | Erro dentro do tipo | Fração dos sucessores perdidos | Quebras emitidas | Fração das quebras | Internas à unidade |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for t, v in soma.items():
                lines.append(f"| {ROTULOS[t]} | {v['ouro']} | {v['acertos']} | {v['erros']} | {frac(v['erros'],v['ouro'])} | {frac(v['erros'],erros)} | {v['quebras_palavra']} | {frac(v['quebras_palavra'],qb)} | {v['internas']} |")
            lines += ["", "| Controle da representação | Total |", "|---|---:|"]
            lines += [f"| Transições-ouro internas à mesma unidade | {sum(v['transicoes_internas'] for v in soma.values())} |",
                      f"| Fronteiras-ouro inalcançáveis por permutação de unidades | {sum(v['inalcancaveis'] for v in soma.values())} |",
                      f"| Piso interno de quebras (função oficial) | {sum(r['metricas']['piso_interno'] for r in rs)} |", ""]
        lines += ["Exemplos de sucessores perdidos, extraídos das palavras e sem ajustar parâmetros:", "",
                  "| Página | Tipo | Origem → próxima linha-ouro |", "|---|---|---|"]
        exemplos = [(r["page_id"], x) for r in rows for x in r["exemplos"]]
        for pid, x in exemplos[:8]:
            txt = (x["texto_a"]+" → "+x["texto_z"]).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{pid}` | {ROTULOS[x['tipo']]} | {txt} |")
        lines += ["", "Todas as transições e seus IDs estão no cache de diagnóstico por página.", ""]
    lines += ["## Etapa de candidatos", "",
              "Conjunto inicial: próximo abaixo na coluna, topo da próxima coluna, próxima ponte, escolha da regra, "
              "vizinhos por distância geométrica e FIN. Ampliações predefinidas adicionam mais vizinhos, próximos abaixo, "
              "topos de colunas, vizinhos na regra e objetos; a última inclui todas as outras unidades. "
              "Desempates seguem a entrada embaralhada. Nunca se inclui um candidato porque o ouro o revelou.", "",
              "O recall total conta a fronteira de linhas-ouro que pode ser realizada: transições internas já "
              "consecutivas contam como alcançáveis sem decisão de sucessor. Fronteiras internas quebradas ou "
              "endpoints que não chegam à borda canônica da unidade contam como falha estrutural. "
              "O recall entre unidades tem somente fronteiras alcançáveis no denominador. São ambos reportados. "
              "Cobertura dos endpoints não garante que as duas linhas inteiras fiquem intactas: "
              "essa exigência adicional é medida pelo sucessor realizado da régua oficial. "
              "FIN não entra no denominador de sucessores entre linhas.", "",
              "A ampliação até atingir a meta consulta RN e as duas bancadas humanas, conforme o pedido. "
              "Portanto essas páginas também participam do desenvolvimento do conjunto de candidatos; o limiar "
              "do híbrido e os pesos continuam exclusivos da validação RN e do treino silver, respectivamente. "
              "No teste silver o conjunto já está congelado: seu recall nunca determina uma ampliação.", ""]
    for nivel, coortes in R.get("candidatos", {}).items():
        lines += ["### "+("Todos os sucessores" if nivel == "-1" else "Nível "+nivel), ""]
        for c, dados in coortes.items():
            lines += [f"**{c}: "+("completo" if dados["completa"] else "parcial")+".**", "",
                      "| Grupo | Tipo | Total | Cobertos | Recall total | Fronteiras alcançáveis entre unidades | Cobertas entre unidades | Recall entre | Falhas estruturais |",
                      "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
            for grupo, rs in estratos(dados["paginas"], c in HUMANAS):
                soma = {t: {k: sum(r["tipos"][t][k] for r in rs) for k in ("total", "cobertos", "entre_unidades", "cobertos_entre", "internos", "inalcancaveis")} for t in TIPOS}
                total = {k: sum(v[k] for v in soma.values()) for k in soma[TIPOS[0]]}
                for t, v in list(soma.items())+[("TOTAL", total)]:
                    lines.append(f"| {grupo} | {ROTULOS.get(t,t)} | {v['total']} | {v['cobertos']} | {frac(v['cobertos'],v['total'])} | {v['entre_unidades']} | {v['cobertos_entre']} | {frac(v['cobertos_entre'],v['entre_unidades'])} | {v['inalcancaveis']} |")
            den = sum(r["fontes"] for r in dados["paginas"])
            lines += ["", "Tamanho médio do conjunto por fonte entre unidades: "+
                      f(sum(r["candidatos_soma"] for r in dados["paginas"])/den if den else None)+"; máximo: "+
                      str(max((r["candidatos_max"] for r in dados["paginas"]), default=0))+". FIN excluído desses tamanhos.", ""]
    if R.get("escalonamento_candidatos"):
        lines += ["| Ampliação | Motivo observado |", "|---|---|"]
        for etapa in R["escalonamento_candidatos"]:
            falhas = [c for c,v in etapa["recall"].items() if v < .95]
            lines.append(f"| {etapa['nivel']} | "+("Recall abaixo da meta em "+", ".join(falhas)+"; acrescentar alternativas geométricas." if falhas else "Meta atingida em todas as coortes; conjunto congelado.")+" |")
        lines += [""]
    lines += ["## Etapa de corretor", "",
              "MLP de pares pequeno, com uma camada oculta. Uma decisão de fonte é um grupo de candidatos: "
              "cross-entropy sobre os escores do grupo, com probabilidades softmax. A escala das features é "
              "calculada apenas nos pares de treino. Não há embeddings, modelo remoto, GPU ou DataLoader. "
              "Features: distâncias/alturas normalizadas pela altura mediana de linha, sobreposição, alinhamento, "
              "posição na página/coluna, calha, objetos e pontes entre os dois, tipo de transição geométrica, "
              "tipo da unidade, escolha e confiança geométrica da regra, pontuação, maiúscula, hífen, tamanho e lista. "
              "A confiança da regra é um proxy heurístico; a probabilidade do MLP não tem calibração independente.", "",
              "Supervisão silver usa somente fontes e alvos cuja expansão canônica coincide com um trecho "
              "contíguo do fluxo PDF. Unidades atravessadas, conteúdo interno divergente, fontes sem texto ou "
              "sucessor fora do conjunto são contados e excluídos da loss; jamais são consertados por mediana. "
              "O terminal FIN é negativo em todos os outros grupos e positivo no fim real.", ""]
    treino = R.get("treino", {})
    if treino.get("pares_paginas"):
        metas = treino["pares_paginas"]
        causas = collections.Counter()
        for m in metas:
            causas.update(m["filtradas"])
        lines += [f"Páginas com pares prontas: {len(metas)}; decisões de fonte: {sum(m['grupos'] for m in metas)}; "
                  f"pares: {sum(m['pares'] for m in metas)}; alvos fora do conjunto: {sum(m['alvos_fora_candidatos'] for m in metas)}. "
                  "Exclusões de supervisão: `"+json.dumps(dict(causas), ensure_ascii=False)+"`.", ""]
    if treino.get("cursor"):
        lines += ["| Época concluída | Loss média por decisão de fonte | Decisões |", "|---:|---:|---:|"]
        for ep in treino["cursor"]["historico"]:
            lines.append(f"| {ep['epoca']} | {f(ep['perda'],6)} | {ep['grupos']} |")
        lines += ["", f"Parâmetros do MLP: {treino['parametros']}. Checkpoint de página: `{treino['checkpoint']}`. "
                  "Uma queda no meio de uma página refaz somente a página não confirmada. Pesos, otimizador, "
                  "RNG e cursor são salvos juntos; treino e inferência são sequenciais.", ""]
    val = R.get("validacao")
    if val:
        lines += [f"Validação: {val['n']} páginas de RN. Limiar escolhido: {f(val['limiar'],2)}. "
                  "Critério predefinido: minimizar quebras realizadas, sem reduzir τ médio de RN; "
                  "empates favorecem τ, menos intervenções e maior limiar. O limiar acima da faixa de "
                  "probabilidades desativa correções e reproduz exatamente a regra. Pesos e épocas não "
                  "são escolhidos pelas bancadas humanas.", "",
                  "| Limiar | Quebras RN | τ RN | Propostas | Elegível |", "|---:|---:|---:|---:|---|"]
        for v in val["tabela"]:
            lines.append(f"| {f(v['limiar'],2)} | {f(v['quebras'])} | {f(v['tau'],6)} | {v['propostas']} | {'sim' if v['elegivel'] else 'não'} |")
        lines += ["", "Só fronteiras ambíguas podem mudar no híbrido: continuação sobreposta, próxima e sem "
                  "obstáculos tem confiança heurística alta e fica protegida. As demais, incluindo retornos "
                  "e fronteiras de objetos/margens, são ambíguas. O classificador sozinho escolhe em todas as fontes. "
                  "A decodificação resolve duplo predecessor e ciclo por confiança e reata cadeias pelo posto "
                  "da regra; assim até 'corretor sozinho' tem a regra como informação/fallback. "
                  "O relatório separa top-1 bruto dos pares e sucessor de linhas realizado na sequência final.", ""]
        if not val["melhora"]:
            lines += ["**RN não sustenta redução de quebras pelo corretor nesta amostra.** "
                      "O limiar escolhido conserva o controle quando a intervenção não melhora RN. "
                      "Não se procura um limiar mais favorável no Golden.", ""]
    for c, dados in R.get("avaliacao", {}).items():
        if c in R.get("inferencia", {}):
            continue
        lines += [f"Avaliação {c} "+("concluída, inferência estatística pendente" if dados["completa"] else "parcial")+
                  f": {len(dados['paginas'])} páginas persistidas.", ""]
    if R.get("inferencia"):
        lines += ["### Comparação final", "",
                  "Métricas macro por página [IC agrupado por veículo]. Top-1 bruto tem o denominador "
                  "das fronteiras-ouro alcançáveis entre unidades; não inclui terminal nem decisões internas. "
                  "Sucessor de linhas realizado usa todas as transições de linhas da régua oficial.", "",
                  "| Bancada | Grupo | n | Modelo | Top-1 bruto acertos/total | Top-1 macro [IC] | Sucessor linhas realizado [IC] | τ [IC] | Quebras/página [IC] | Fidelidade [IC] |",
                  "|---|---|---:|---|---:|---:|---:|---:|---:|---:|"]
        for c, grupos in R["inferencia"].items():
            for grupo, res in grupos.items():
                if not res["n"] or c not in HUMANAS and grupo != "todos":
                    continue
                for metodo in ("regra", "corretor", "hibrido"):
                    met = res["metricas"][metodo]
                    top = res["top1"]
                    lines.append(f"| {c} | {grupo} | {res['n']} | {metodo} | {top[metodo]}/{top['total']} | {cel(top[metodo+'_macro'],True)} | {cel(met['sucessor_linhas'],True)} | {cel(met['tau'], casas=6)} | {cel(met['quebras'])} | {cel(met['fid12'],True)} |")
        lines += ["", "| Bancada | Grupo | Métrica | Δ híbrido−regra [IC] | p Wilcoxon página | p Wilcoxon veículo | Veículos |",
                  "|---|---|---|---:|---:|---:|---:|"]
        for c, grupos in R["inferencia"].items():
            for grupo, res in grupos.items():
                if not res["n"] or c not in HUMANAS and grupo != "todos":
                    continue
                for k in ("quebras", "tau", "sucessor_linhas", "fid12"):
                    te = res["testes"].get(k)
                    if te:
                        lines.append(f"| {c} | {grupo} | {k} | {cel(te['delta'], casas=6 if k == 'tau' else 3)} | {f(te['wilcoxon_pagina']['p'],6)} | {f(te['wilcoxon_veiculo']['p'],6)} | {te['veiculos']} |")
        lines += ["", "Bootstrap e Wilcoxon usam as funções do avaliador importado: percentil por veículo, "
                  f"{e.NBOOT} reamostras, semente {e.SEMENTE}; Wilcoxon bilateral Pratt, aproximação normal. "
                  "P-valores exploratórios, sem correção por multiplicidade. Páginas do mesmo veículo não "
                  "são tratadas como veículos independentes; o teste por página também fica visível como contraste. "
                  "RN tem um único veículo: seu intervalo de cluster é degenerado, não mede generalização.", "",
                  "| Bancada | Propostas | Mantidas na ordem | Conflitos | Ciclos | Fronteiras alteradas após reatar cadeias |", "|---|---:|---:|---:|---:|---:|"]
        for c, grupos in R["inferencia"].items():
            s = grupos["todos"]
            lines.append(f"| {c} | {s['propostas']} | {s['mantidas']} | {s['conflitos']} | {s['ciclos']} | {s['alteradas']} |")
        lines += ["", "| Bancada | Veredito observado |", "|---|---|"]
        for c, grupos in R["inferencia"].items():
            ts = grupos["todos"]["testes"]
            dq, dt = ts["quebras"]["delta"]["media"], ts["tau"]["delta"]["media"]
            txt = "Menos quebras em média" if dq < 0 else "Mais quebras em média" if dq > 0 else "Sem redução de quebras"
            txt += "; τ "+("sobe" if dt > 0 else "cai" if dt < 0 else "igual")+"."
            ic = ts["quebras"]["delta"]["ic"]
            if ic[0] <= 0 <= ic[1]:
                txt += " IC das quebras inclui zero: evidência inconclusiva para ganho populacional."
            lines.append(f"| {c} | {txt} |")
        if R.get("completa"):
            lines += ["", "**Decisão desta demonstração:** "+decisao_final(R), "",
                      "O limiar permanece o escolhido em RN. A avaliação final encerra esta configuração; "
                      "não se retreinam pesos nem se procura outro limiar usando resultados humanos ou de CE/MA/RJ. "
                      "O veredito considera quebras e τ juntos: melhora de pares isolados ou da validação "
                      "não demonstra melhora da sequência realizada nas bancadas finais.", ""]
    lines += ["", "## Limitações e retomada", "",
              "golden_v4 participou do desenvolvimento da regra; golden_v3_novo tem páginas adicionais e "
              "amostra pequena de conveniência. A ordem humana é de regiões expandida geometricamente, "
              "não anotação independente de todas as linhas/palavras/células. O conjunto de candidatos "
              "é desenvolvido com as humanas nesta tarefa; declare isso ao discutir generalização. "
              "Silver é referência automática de veículos escolhidos por concordância com heurística; "
              "não fornece ordem humana independente. Veículos humanos vistos e não vistos são separados. "
              "PDFs compartilhados entre treino e páginas humanas, mesmo em páginas distintas, ficam "
              "no estado para auditoria e podem reduzir a independência documental.", "",
              "O MLP foi desenhado para uma demonstração pequena; não há comparação com várias sementes "
              "nem potência estatística para declarar equivalência. Pontuação/maiúsculas são proxies "
              "baratos de estilo; não há fontes tipográficas/fontsize nos shards de palavras. "
              "Calhas são proxies globais, não segmentação humana de todas as mudanças locais. "
              "A regra fornece features e prioridade das cabeças ao decodificador: este experimento "
              "testa correção local da regra, não um ordenador neural independente.", "",
              "Ciclos e conflitos podem desfazer propostas ou mudar outras fronteiras. Ganho de top-1 "
              "bruto não garante ganho de quebras/τ; a ordem final completa é medida. Erro interno de "
              "tabela/linha/átomo permanece indivisível. FIN e unidades vazias não têm sucessor textual "
              "anotado; participam da ordem, com esse limite explícito.", "",
              "A execução mantém um processo, CPU, threads limitadas e um grupo de candidatos em RAM por vez. "
              "Hashes de fontes e configuração dão um namespace próprio; não mistura caches antigos. "
              "O script guarda pares, métricas, decisões e checkpoints antes de avançar. "
              "O controle de memória/prazo interrompe de forma retomável. Repita o mesmo comando. "
              "Fontes alteradas durante a execução invalidam a comparação.", "",
              "```powershell",
              "venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa diagnostico",
              "venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa candidatos",
              "venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --etapa corretor --n-treino 24 --epocas 3 --max-minutos 30",
              "venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --conferir",
              "venv/Scripts/python.exe -B orquestracao/analises/corretor_de_transicoes.py --autoteste", "```", "",
              "Predições JSONL no cache próprio seguem o contrato `page_id/ordem` da bancada. "
              "As métricas já foram calculadas por suas funções puras e pela régua oficial; nenhum relatório "
              "ou cache de outro experimento é escrito. Anotações, PDFs, docs e quadro de comunicação "
              "permanecem somente de leitura. Não há publicação, rede ou commit.", ""]
    if R.get("parada"):
        lines += ["Motivo da interrupção: "+R["parada"], ""]
    return "\n".join(lines)


def assinatura_numeros(R):
    return digest({k: R.get(k) for k in ("ancoras", "diagnostico", "candidatos", "escalonamento_candidatos",
                                       "nivel_candidatos", "treino", "validacao", "avaliacao", "inferencia")})


def conferir():
    exigir(ESTADO.get("assinatura_numeros") == assinatura_numeros(ESTADO), "Assinatura dos numeros diverge")
    exigir(MD.read_text(encoding="utf-8") == relatorio(ESTADO), "Markdown diverge do estado")
    exigir(fontes(ESTADO["splits"]) == ESTADO["fontes"], "Fontes alteradas")
    a = ESTADO.get("ancoras", {})
    if a.get("aprovada"):
        exigir(len(a["paginas"]) == 44, "Ancora incompleta")
        for m, vals in a["medias"].items():
            for k, v in vals.items():
                exigir(abs(statistics.mean(r[m][k] for r in a["paginas"])-v) < 1e-12, "Media da ancora diverge")
    if ESTADO.get("inferencia"):
        lim = ESTADO["validacao"]["limiar"]
        for c, s in ESTADO["inferencia"].items():
            exigir(inferencia(ESTADO["avaliacao"][c]["paginas"], lim) == s, "Inferencia estatistica nao corresponde as paginas")
    print("CONFERE: hashes, assinatura, ancoras, estatisticas por pagina e relatorio. Nenhuma escrita.", flush=True)


def autoteste():
    """Contratos criticos: permutacao, identidade, ciclos e isolamento do ouro."""
    regra = ["a", "b", "c", "d"]
    vazio = {a: {"z": z, "prob": .9, "ambigua": True} for a, z in zip(regra, regra[1:]+[None])}
    exigir(decodificar(regra, vazio, 1.01)[0] == regra, "Limiar desativado falhou")
    escolhas_ = {"a": {"z": "c", "prob": .99, "ambigua": True},
                 "b": {"z": "c", "prob": .98, "ambigua": True},
                 "c": {"z": "a", "prob": .97, "ambigua": True},
                 "d": {"z": None, "prob": .96, "ambigua": True}}
    ordem, diag = decodificar(regra, escolhas_)
    exigir(set(ordem) == set(regra) and len(ordem) == len(regra), "Ciclo/conflito corrompeu permutacao")
    exigir(diag["conflitos"] > 0 and diag["ciclos"] > 0, "Autoteste nao cobriu ciclo/conflito")
    ws, cs = [], []
    for col in range(2):
        for lin in range(4):
            ids = []
            for j in range(3):
                ids.append(len(ws))
                ws.append([f"P{len(ws)}", 30+col*300+j*25, 100+lin*20, 50+col*300+j*25, 110+lin*20])
            cs.append({"id": f"u{len(cs)}", "ks": ids, "text": "Linha.", "tipo": "texto",
                       "bbox": [30+col*300, 100+lin*20, 100+col*300, 110+lin*20]})
    p = {"page_id": "sintetico", "uf": "sintetico", "dimensions": {"width": 600, "height": 800},
         "bounding_boxes": cs, "ordens": {"stream": [u["id"] for u in cs]}}
    ctx = contexto(p, ws)
    outro = contexto({**p, "ordens": {"stream": [u["id"] for u in reversed(cs)]}, "posto_referencia": 999}, ws)
    exigir(ctx["ordem"] == outro["ordem"], "Referencia vazou no preditor")
    for uid in ctx["entrada"]:
        cand = candidatos(ctx, uid, -1)
        exigir(uid not in cand and len(cand) == len(cs) and cand.count(None) == 1, "Candidatos invalidos")
        for z in cand:
            exigir(features(ctx, uid, z) == features(outro, uid, z), "Referencia vazou em feature")
    obj = {"palavras": ws, "gt_w": list(range(len(ws)))}
    correto = medir(obj, p, [u["id"] for u in cs])[0]
    exigir(correto["quebras"] == 0 and correto["tau"] == 1., "Regua importada nao preserva ordem sintetica")
    alvos, _ = alvos_silver(obj, ctx)
    exigir(len(alvos) == len(cs) and alvos[cs[-1]["id"]] is None, "Supervisao terminal falhou")
    print("AUTOTESTE: permutacao, identidade sem correcoes, conflitos, ciclos, isolamento do ouro, features, regua e terminal: ok", flush=True)


def main():
    global ESTADO, DIR_EXEC, PRAZO
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapa", choices=("diagnostico", "candidatos", "corretor"), default="diagnostico")
    ap.add_argument("--n-treino", type=int, default=24)
    ap.add_argument("--epocas", type=int, default=3)
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()
    exigir(1 <= args.n_treino <= 128, "Use --n-treino entre 1 e 128; tarefa de demonstracao CPU")
    exigir(1 <= args.epocas <= 10 and args.max_minutos >= 0, "Epocas/prazo invalidos")
    PRAZO = time.monotonic()+args.max_minutos*60 if args.max_minutos else None
    if args.autoteste:
        autoteste()
        return
    with trava():
        if args.conferir:
            ptr = ler(BASE / "ultima_execucao.json")
            DIR_EXEC = BASE / ptr["fingerprint"]
            ESTADO = ler(DIR_EXEC / "estado.json")
            conferir()
            return
        config = {"versao": VERSAO, "semente": SEMENTE, "n_treino": args.n_treino, "epocas": args.epocas,
                  "device": "cpu", "threads_max": 4, "num_workers": 0, "meta_recall": .95,
                  "niveis_candidatos": list(NIVEIS), "limiares": list(LIMIARES), "regra": e.FIXA.id,
                  "arquitetura": [len(FEATURES), 32, 1], "features": list(FEATURES), "lr": .001}
        try:
            # O primeiro registro sai antes da leitura dos shards/fontes grandes.
            ESTADO = {"config": config, "preparando": True}
            gravar(MD, relatorio(ESTADO))
            splits = ler(RAIZ / "data/processed/splits.json")
            grupos = [set(splits[k]) for k in ("treino", "validacao", "teste")]
            exigir(all(not a & z for a,z in itertools.combinations(grupos, 2)), "Veiculo em varios splits")
            exigir(splits["validacao"] == ["official_diary_rn"] and
                   set(splits["teste"]) == {"official_diary_ce", "official_diary_ma", "official_diary_rj"} and
                   len(splits["treino"]) == 7, "Split congelado difere do protocolo solicitado")
            H = fontes(splits)
            fp = digest([config, H])
            DIR_EXEC = destino(BASE / fp / "estado.json").parent
            if (DIR_EXEC / "estado.json").exists():
                ESTADO = ler(DIR_EXEC / "estado.json")
                exigir(ESTADO["fontes"] == H and ESTADO["config"] == config, "Mistura de caches")
                exigir(ESTADO["assinatura_numeros"] == assinatura_numeros(ESTADO), "Estado foi alterado")
            else:
                ESTADO = {"fingerprint": fp, "fontes": H, "config": config, "splits": splits,
                          "inventario": inventario(splits, args.n_treino), "completa": False}
            ESTADO.pop("parada", None)
            gravar(BASE / "ultima_execucao.json", {"fingerprint": fp})
            salvar()
            ancoras()
            diagnostico()
            rs = [r for c in HUMANAS for r in ESTADO["diagnostico"][c]["paginas"]]
            if all(r["metricas"]["quebras"] == r["metricas"]["piso_interno"] for r in rs):
                raise Interromper("Todo o erro observado está dentro das unidades; correção de fronteiras não pode reduzi-lo. Parar no diagnóstico.")
            if args.etapa in ("candidatos", "corretor"):
                etapa_candidatos()
            if args.etapa == "corretor":
                etapa_corretor(args)
            exigir(fontes(splits) == H, "Fontes mudaram durante a execucao: numeros invalidos; repetir com entradas congeladas")
            salvar()
            print("Relatorio:", rel(MD), flush=True)
        except (Exception, KeyboardInterrupt) as exc:
            ESTADO["parada"] = str(exc) or "Interrupção do processo; retomar o mesmo comando."
            if DIR_EXEC is not None:
                salvar()
            else:
                gravar(MD, relatorio(ESTADO))
            if isinstance(exc, Interromper):
                print("PARADA RETOMAVEL:", ESTADO["parada"], flush=True)
                return
            raise


if __name__ == "__main__":
    main()
