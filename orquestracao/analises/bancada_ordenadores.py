"""Mede qualquer ordenador sobre unidades sem caixas finas, sem alterar dados.

Ks define pertinencia; expande cada unidade por ordem_sem_bbox.fluxo() e
importa medir/eventos de erros_ponta_a_ponta. As ancoras P2 sao reexecutadas
em CPU com deteccoes congeladas; P1m vem do JSON historico, sem reextracao.
Paginas, predicoes e metricas persistem em fluxo; so LayoutReader e carregado.
O teto usa a ordem de referencia de unidades exportada (posto mediano): nao
e uma otimizacao combinatoria quando uma unidade atravessa a referencia.

Executar da raiz com venv/Scripts/python.exe -B e este caminho:
  --somente-ancoras
  --metodos teto ingenuo xycut xycut_margens regra_colunas
  --metodos layoutreader_pronto --max-minutos 30
  --avaliar-pred resultados/ordenadores_sem_caixas/pred/modelo__linhas__golden_v4.jsonl
  --conferir
O padrao executa os seis metodos nas tres representacoes e bancadas.
Saidas restritas a resultados/ordenadores_sem_caixas/** e seu .md/.json.
Nao usa GPU, rede, multiprocessing, treino, dados do Label Studio ou OCR.
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
import ctypes
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
import types
from contextlib import contextmanager
from functools import lru_cache

os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  HF_DEACTIVATE_ASYNC_LOAD="1",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
from orquestracao.analises import erros_ponta_a_ponta as e
from src.eval.baselines import caixas, xycut
from src.eval.politica_margens import xycut_margens
from src.eval.protocolo import ordem_entrada

UNIDADES = RAIZ / "resultados/unidades_sem_caixas"
OUT = RAIZ / "resultados/ordenadores_sem_caixas"
JSON = RAIZ / "resultados/ordenadores_sem_caixas.json"
MD = RAIZ / "resultados/ordenadores_sem_caixas.md"
REPS = ("linhas", "colunas", "colunas_margens")
BANCADAS = ("golden_v4", "golden_v3_novo", "teste_silver")
METODOS = ("teto", "ingenuo", "xycut", "xycut_margens", "regra_colunas", "layoutreader_pronto")
METRICAS = ("tau", "quebras", "quebras_mil", "fid12", "sucessor_linhas", "piso_interno")
VERSAO, SEMENTE, NBOOT = "bancada-v2-fluxo-canonico", 20261004, 5000
# Reusa as estatisticas originais em namespace isolado, sem mudar o modulo.
PESOS_CLUSTER = types.FunctionType(e.pesos_cluster.__code__,
    {**e.pesos_cluster.__globals__, "SEMENTE": SEMENTE, "NBOOT": NBOOT})
DEP_PATHS = [Path(__file__), Path(e.__file__), Path(e.o.__file__), Path(e.j.__file__),
             Path(e.ls.__file__), Path(e.ac.__file__), Path(e.ri.__file__)] + [
    RAIZ / s for s in ("src/data/regioes.py", "src/data/extrator.py",
    "src/eval/metrics.py", "src/eval/baselines.py", "src/eval/politica_margens.py",
    "src/eval/protocolo.py", "orquestracao/analises/ordem_layoutreader.py")]


def exigir(cond, msg):
    if not cond:
        raise ValueError(msg)


def ler(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def jsonl(path):
    # Fecha o shard ANTES de processar a pagina: o exportador republica
    # arquivos em paralelo. Offsets sao bytes, inclusive para texto UTF-8.
    off, i = 0, 0
    while True:
        with open(path, "rb") as f:
            f.seek(off)
            l = f.readline()
            off = f.tell()
        if not l:
            return
        i += 1
        if l.strip():
            try:
                yield json.loads(l.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"JSONL invalido {path}:{i}") from exc


def rel(path):
    path = Path(path).resolve()
    return path.relative_to(RAIZ).as_posix() if path.is_relative_to(RAIZ) else str(path)


def digest(obj):
    return e.ac.digest(obj)


def sha(path):
    return e.ac.sha(path)


def destino(path):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()) or path in (JSON, MD), f"Saida fora do escopo: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def gravar(path, obj):
    path = destino(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    # Leitores da fila no Windows podem manter o destino aberto brevemente.
    # Preserva escrita atomica; nao confunde lock transitorio com falta de RAM.
    for tentativa in range(51):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if tentativa == 50:
                raise
            time.sleep(.1)


def memoria():
    if os.name != "nt":
        return {}
    from ctypes import wintypes
    class Estado(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] + [
            (k, ctypes.c_ulonglong) for k in ("ullTotalPhys", "ullAvailPhys", "ullTotalPageFile",
            "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]
    m = Estado()
    m.dwLength = ctypes.sizeof(m)
    exigir(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)), "Falha ao medir RAM")
    return {"ram_livre_mb": m.ullAvailPhys / 2**20,
            "commit_livre_mb": m.ullAvailPageFile / 2**20}


@contextmanager
def trava():
    """Impede que inferencia e importacao externa sobrescrevam o mesmo JSON."""
    path = destino(OUT / "execucao.lock")
    if path.exists():
        anterior = ler(path)
        pid = anterior["pid"]
        vivo = True
        if os.name == "nt":
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.restype = wintypes.HANDLE
            handle = kernel.OpenProcess(0x1000, False, pid)
            if handle:
                codigo = wintypes.DWORD()
                kernel.GetExitCodeProcess(handle, ctypes.byref(codigo))
                vivo = codigo.value == 259
                kernel.CloseHandle(handle)
            else:
                vivo = ctypes.get_last_error() != 87
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                vivo = False
        exigir(not vivo, f"Bancada ja em execucao no PID {pid}; aguarde esse processo")
        path.unlink()
    with open(path, "x", encoding="utf-8") as f:
        json.dump({"pid": os.getpid()}, f)
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def referencia(obj, p):
    """Constroi o contexto do avaliador; nenhuma referencia entra no preditor."""
    ws, gt = obj["palavras"], obj["gt_w"]
    exigir(len(gt) == len(set(gt)) and gt and set(gt) <= set(range(len(ws))), "Referencia de palavras invalida")
    h = statistics.median(w[4] - w[2] for w in ws)
    q = {"ws": ws, "gt_w": gt, "h": h,
         "p": {"page_id": p["page_id"], "dimensions": p["dimensions"]}}
    if "gold_lines" in obj:
        q.update({k: obj[k] for k in ("gold_lines", "gt_l", "reg_words", "gt_r")})
    else:
        # Silver: a referencia de PALAVRAS e o fluxo PDF. Linhas geometricas
        # sao divididas em trechos contiguos desse fluxo; nunca o reordenam.
        ls = e.o.linhas_partidas(ws, list(range(len(ws))), e.FIXA.gap, h)
        dono = {k: i for i, L in enumerate(ls) for k in L["ks"]}
        grupos = [list(g) for _, g in itertools.groupby(gt, key=dono.__getitem__)]
        gl = [{"id": f"silver:l{i}", "ks": ks} for i, ks in enumerate(grupos)]
        q.update(gold_lines=gl, gt_l=[L["id"] for L in gl],
                 reg_words={"silver": gt}, gt_r=["silver"])
    return q


def paginas(bancada, rep):
    """Le somente uma pagina com palavras, nunca o corpus todo."""
    if bancada != "teste_silver":
        for obj in jsonl(UNIDADES / "bancadas" / (bancada + ".jsonl")):
            exigir(obj["particao"] == bancada, "Particao humana divergente")
            yield obj, obj["representacoes"][rep]
        return
    splits = ler(RAIZ / "data/processed/splits.json")
    for uf in splits["teste"]:
        pp = UNIDADES / rep / (uf + ".jsonl")
        wp = UNIDADES / rep / (uf + ".palavras.jsonl")
        for p, obj in itertools.zip_longest(jsonl(pp), jsonl(wp)):
            exigir(p is not None and obj is not None and p["page_id"] == obj["page_id"],
                   f"Shards de palavras/unidades divergentes: {pp}")
            exigir(p["uf"] == uf and p["particao"] == "teste", "Veiculo/split de teste divergente")
            exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra", "Silver diferente do fluxo PDF")
            exigir(obj["gt_w"] == list(range(len(obj["palavras"]))), "Silver nao preserva indices do fluxo")
            yield {**obj, "uf": uf, "particao": "teste_silver"}, p


def auditar_unidades(p, obj):
    us = p["bounding_boxes"]
    ids = [u["id"] for u in us]
    exigir(len(ids) == len(set(ids)) and ids, "IDs vazios/repetidos")
    exigir(sorted(k for u in us for k in u["ks"]) == list(range(len(obj["palavras"]))),
           f"Palavras perdidas/repetidas: {p['page_id']}")
    for u in us:
        b = u["bbox"]
        exigir(len(b) == 4 and all(math.isfinite(x) for x in b) and b[2] >= b[0] and b[3] >= b[1], "bbox invalida")
    return ids


def fontes():
    paths = DEP_PATHS + [RAIZ / "data/processed/splits.json", e.JSON]
    paths += [RAIZ / "models/terceiros/layoutreader" / n for n in ("config.json", "model.safetensors")]
    paths += [UNIDADES / "bancadas" / (b + ".jsonl") for b in BANCADAS[:2]]
    splits = ler(RAIZ / "data/processed/splits.json")
    paths += [UNIDADES / rep / (uf + suf) for rep in REPS for uf in splits["teste"]
              for suf in (".jsonl", ".palavras.jsonl")]
    return {rel(p): sha(p) for p in paths}


def iniciar():
    H = fontes()
    R = ler(JSON) if JSON.exists() else {}
    if R:
        exigir(R.get("versao") == VERSAO and R.get("fontes") == H,
               "Fontes/codigo mudaram. Preserve a saida antiga e use uma nova execucao; nao mistura caches")
    else:
        R = {"versao": VERSAO, "fontes": H, "config": {"device": "cpu", "threads_max": 4,
             "num_workers": 0, "bootstrap": NBOOT, "semente": SEMENTE,
             "wilcoxon": "bilateral por medias de veiculo; zero_method=pratt",
             "regra_colunas": e.FIXA.id, "expansao_interna": "ordem_sem_bbox.fluxo por unidade; ks e conjunto"},
             "resultados": {}, "progresso": {}, "ancoras": {}}
    return R


def salvar(R):
    gravar(JSON, R)
    gravar(MD, relatorio(R))


def conferir_ancoras(R):
    """Confere P2 e a regra com expansao canonica; ks cru fica diagnostico."""
    H = R["fontes"]
    det_paths = [UNIDADES / "cache/detector" / (e.ac.chave(obj["page_id"]) + ".json")
                 for obj, _ in paginas("golden_v4", "linhas")]
    df = {rel(p): sha(p) for p in det_paths}
    afp = digest([H, df, e.FIXA.id])
    if (R.get("ancoras", {}).get("aprovada") and R["ancoras"].get("unidades_conferidas")
            and R["ancoras"].get("fingerprint") == afp):
        return
    historico = ler(e.JSON)
    hs = {r["page_id"]: r for r in historico["paginas"] if r["coorte"] == "v4"}
    rows = []
    try:
        for obj, p in paginas("golden_v4", "linhas"):
            cache_ancora = OUT / "cache/ancoras" / afp / (e.ac.chave(p["page_id"]) + ".json")
            if cache_ancora.exists():
                salvo = ler(cache_ancora)
                exigir(salvo["page_id"] == p["page_id"], "Cache de ancora trocou pagina")
                rows.append(salvo)
                R["progresso"]["ancoras"] = {"concluidas": len(rows), "esperadas": len(hs)}
                salvar(R)
                continue
            q = referencia(obj, p)
            q["ls3"] = ler(UNIDADES / "cache/detector" / (e.ac.chave(p["page_id"]) + ".json"))["regioes"]
            q["d"] = {"detector": {"regioes": []}}
            seq, its, dg = e.ls.prever(q, e.FIXA, "ls3")
            # medir reutilizado integralmente; P0 evita apenas categorias causais.
            med = e.medir(q, seq, its, dg, "P0")
            velho = hs[p["page_id"]]["metodos"]
            exigir(seq == velho["P2"]["seq"], f"Sequencia P2 difere: {p['page_id']}")
            for k in METRICAS[:-1]:
                exigir((med[k] is None and velho["P2"][k] is None) or
                       med[k] is not None and velho["P2"][k] is not None and
                       abs(med[k] - velho["P2"][k]) < 1e-10, f"Metrica P2 difere: {p['page_id']}: {k}")
            ordem, diag = prever(p, obj["palavras"], "regra_colunas")
            novas = metricas(obj, p, ordem)
            cruas = metricas(obj, p, ordem, canonica=False)
            mapa = {u["id"]: u for u in p["bounding_boxes"]}
            itens_ord = [mapa[uid] for uid in ordem]
            seq_raw = [k for u in itens_ord for k in u["ks"]]
            seq_diag = e.o.fluxo(itens_ord, obj["palavras"])
            med_diag = e.medir(q, seq_diag, [], {}, "P0")
            exigir(seq_diag == seq, f"Expansao canonica nao coincide com P2: {p['page_id']}")
            exigir(all(novas[k] == med_diag[k] for k in METRICAS[:-1]), "Regua nao usa expansao canonica")
            detalhes = diagnosticar_internas(obj, p)
            rows.append({"page_id": p["page_id"], "uf": obj["uf"],
                         "P2": {k: med[k] for k in METRICAS[:-1]},
                         "P1m": {k: velho["P1m"][k] for k in METRICAS[:-1]},
                         "regra_colunas_exportada": novas,
                         "regra_colunas_ks_cru": cruas,
                         "expansao_canonica_diagnostico": {k: med_diag[k] for k in METRICAS[:-1]},
                         "diagnostico": {"ks_diferem_da_expansao_canonica": seq_raw != seq_diag,
                             "canonizada_identica_P2": seq_diag == seq,
                             "unidades_internas_diferentes": len(detalhes), "detalhes": detalhes},
                         "ordem_regra_colunas_exportada": ordem, "diag_regra": diag})
            gravar(cache_ancora, rows[-1])
            R["progresso"]["ancoras"] = {"concluidas": len(rows), "esperadas": len(hs)}
            # Antes de passar, o relatorio contem so progresso, sem tabelas.
            salvar(R)
            if len(rows) % 10 == 0:
                print(f"Ancoras: {len(rows)}/{len(hs)}", flush=True)
        exigir(len(rows) == 44 and {r["page_id"] for r in rows} == set(hs), "Coorte v4 diferente de 44 paginas")
        medios = {m: {k: statistics.mean(r[m][k] for r in rows) for k in ("tau", "quebras")}
                  for m in ("P2", "P1m", "regra_colunas_exportada", "regra_colunas_ks_cru", "expansao_canonica_diagnostico")}
        for m in ("regra_colunas_exportada", "regra_colunas_ks_cru"):
            medios[m]["piso_interno"] = statistics.mean(r[m]["piso_interno"] for r in rows)
        R["ancoras"] = {"aprovada": False, "unidades_conferidas": True, "fingerprint": afp,
                        "detectores_sha256": df, "n": len(rows), "medias": medios, "paginas": rows,
                        "paginas_ks_diferentes": sum(r["diagnostico"]["ks_diferem_da_expansao_canonica"] for r in rows),
                        "paginas_canonizadas_identicas_P2": sum(r["diagnostico"]["canonizada_identica_P2"] for r in rows),
                        "P2_sequencias_e_metricas_identicas_historico": True,
                        "P1m_fonte": rel(e.JSON)}
        for m, tau, qb in (("P2", .986, 6.05), ("P1m", .952, 8.93)):
            exigir(abs(medios[m]["tau"] - tau) <= .006 and abs(medios[m]["quebras"] - qb) <= .0051,
                   f"Ancora {m} nao reproduzida: {medios[m]}")
        exigir(abs(medios["regra_colunas_exportada"]["tau"]-.986) <= .006 and
               abs(medios["regra_colunas_exportada"]["quebras"]-6.05) <= .0051,
               "Regra sobre unidades exportadas nao reproduz a ancora: " +
               str(medios["regra_colunas_exportada"]) +
               ". Expansao canonica nao reproduziu P2; nao publicar tabelas.")
        R["ancoras"]["aprovada"] = True
        R.pop("bloqueio", None)
        salvar(R)
        print("Ancoras aprovadas:", medios, flush=True)
    except Exception as exc:
        R["ancoras"].update(aprovada=False, fingerprint=afp)
        R["bloqueio"] = f"PARE: {exc}"
        salvar(R)
        raise


def inventario(R):
    if "inventario" in R:
        return
    inv, todos = {}, {}
    treino = set(ler(RAIZ / "data/processed/splits.json")["treino"])
    for b in BANCADAS:
        ids, us, vistos, ufs = [], [], 0, set()
        for obj, p in paginas(b, "linhas"):
            ids.append(p["page_id"])
            ufs.add(obj["uf"])
            vistos += obj["uf"] in treino
            us.append(len(p["bounding_boxes"]))
        exigir(len(ids) == len(set(ids)), f"Paginas duplicadas na bancada {b}")
        if b != "teste_silver":
            exigir(len(ids) == {"golden_v4": 44, "golden_v3_novo": 27}[b], f"Bancada {b} incompleta")
        inv[b] = {"n": len(ids), "veiculos": len(ufs), "vistos": vistos, "nao_vistos": len(ids)-vistos,
                  "max_unidades_linhas": max(us), "paginas_linhas_acima_510": sum(n > 510 for n in us)}
        todos[b] = set(ids)
    exigir(not todos[BANCADAS[0]] & todos[BANCADAS[1]], "V3 novo inclui paginas v4")
    inv["sobreposicao_silver_humanas"] = len(todos["teste_silver"] & (todos[BANCADAS[0]] | todos[BANCADAS[1]]))
    R["inventario"] = inv


def diagnosticos_internos(R):
    if "diagnosticos_internos" in R:
        return
    saida = {}
    for rep in REPS:
        for b in BANCADAS:
            tipos, exemplos = {}, []
            paginas_diferentes = 0
            for obj, p in paginas(b, rep):
                detalhes = diagnosticar_internas(obj, p)
                paginas_diferentes += bool(detalhes)
                for d in detalhes:
                    s = tipos.setdefault(d["tipo"], {"unidades": 0, "piso_ks_cru": 0,
                        "piso_canonico": 0, "com_linhas_lado_a_lado": 0})
                    s["unidades"] += 1
                    s["piso_ks_cru"] += d["piso_ks_cru"]
                    s["piso_canonico"] += d["piso_canonico"]
                    s["com_linhas_lado_a_lado"] += bool(d["linhas_lado_a_lado"])
                    if len(exemplos) < 3 and not any(x["page_id"] == p["page_id"] for x in exemplos):
                        exemplos.append({"page_id": p["page_id"], **d})
            saida[f"{rep}__{b}"] = {"paginas_diferentes": paginas_diferentes,
                                    "tipos": tipos, "exemplos": exemplos}
    R["diagnosticos_internos"] = saida
    salvar(R)


def prever(p, ws, metodo, lr=None):
    """Somente teto consulta ordens/ranks. Os demais recebem campos automaticos."""
    cs = [{k: u[k] for k in ("id", "bbox", "ks", "text", "tipo")} for u in p["bounding_boxes"]]
    auto = {"page_id": p["page_id"], "dimensions": p["dimensions"], "bounding_boxes": cs}
    ent = ordem_entrada(auto)
    ids = [u["id"] for u in cs]
    diag = {"unidades": len(cs), "entrada": [ids[i] for i in ent]}
    t = time.perf_counter()
    if metodo == "teto":
        ordem = list(p["ordens"]["stream"])
    elif metodo == "ingenuo":
        ordem = [ids[i] for i in sorted(ent, key=lambda i: (cs[i]["bbox"][1], cs[i]["bbox"][0]))]
    elif metodo == "xycut":
        ordem = [ids[i] for i in xycut(ent, caixas(auto))]
    elif metodo == "xycut_margens":
        ordem = xycut_margens(auto)
    elif metodo == "regra_colunas":
        h = statistics.median(w[4] - w[2] for w in ws)
        ini, corpo, marcas, fim = e.j.particao(cs, ws, p["dimensions"]["height"], "geo")
        corpo_set = set(corpo)
        diag.update(max_colunas=1, pontes=0, topo=len(ini), rodape=len(fim), marcas=len(marcas))
        oc = e.o.ordenar_projecao(cs, [i for i in ent if i in corpo_set], h, e.FIXA.vale, diag, local=True)
        chave = lambda i: (cs[i]["bbox"][1], cs[i]["bbox"][0], i)
        ordem = [ids[i] for i in sorted(ini, key=chave) + oc + sorted(marcas, key=chave) + sorted(fim, key=chave)]
    elif metodo == "layoutreader_pronto":
        exigir(lr is not None, "LayoutReader nao carregado")
        # direto() do adaptador embaralha a lista canonica com entrada-page_id.
        # Evita duas permutacoes: esta chamada deve receber indices canonicos.
        ordem_i = lr.ordenar(cs, list(range(len(cs))), p["dimensions"]["width"],
                            p["dimensions"]["height"], statistics.median(w[4]-w[2] for w in ws),
                            e.FIXA.vale, p["page_id"], diag)
        ordem = [ids[i] for i in ordem_i]
    else:
        raise ValueError(f"Ordenador desconhecido: {metodo}")
    exigir(len(ordem) == len(ids) and set(ordem) == set(ids), "Predicao nao e permutacao completa")
    diag["tempo_ms"] = 1000*(time.perf_counter()-t)
    return ordem, diag


@lru_cache(maxsize=1)
def assinatura_metricas():
    return digest([sha(p) for p in DEP_PATHS])


def expansoes(obj, p, canonica=True):
    """A ordem dentro da unidade independe do ordenador; nao altera a fonte."""
    return {u["id"]: e.o.fluxo([u], obj["palavras"]) if canonica else list(u["ks"])
            for u in p["bounding_boxes"]}


def diagnosticar_internas(obj, p):
    """Localiza divergencias de ks, incluindo linhas lado a lado nas faixas."""
    ws, gt = obj["palavras"], obj["gt_w"]
    h = statistics.median(w[4]-w[2] for w in ws)
    detalhes = []
    for u in p["bounding_boxes"]:
        can = e.o.fluxo([u], ws)
        if can == u["ks"]:
            continue
        ls = e.o.linhas(ws, u["ks"])
        lado = sum(any(ws[b][1]-ws[a][3] > max(4., e.FIXA.gap*h)
                       for a, b in zip(L["ks"], L["ks"][1:])) for L in ls)
        detalhes.append({"id": u["id"], "tipo": u["tipo"], "bbox": u["bbox"],
                         "palavras": len(can), "linhas": len(ls), "linhas_lado_a_lado": lado,
                         "piso_ks_cru": len(e.eventos(u["ks"], gt)),
                         "piso_canonico": len(e.eventos(can, gt)),
                         "primeiros_ks_crus": u["ks"][:16], "primeiros_ks_canonicos": can[:16]})
    return detalhes


def metricas(obj, p, ordem, *, canonica=True):
    ids = auditar_unidades(p, obj)
    exigir(isinstance(ordem, list) and len(ordem) == len(ids) and set(ordem) == set(ids),
           f"IDs da predicao nao pertencem a esta representacao: {p['page_id']}")
    mapa = {u["id"]: u for u in p["bounding_boxes"]}
    exp = expansoes(obj, p, canonica)
    seq = [k for uid in ordem for k in exp[uid]]
    q = referencia(obj, p)
    # Cache da regua independe do ordenador/representacao: mesma sequencia e
    # referencia implicam mesmas metricas. O piso depende das unidades.
    fp = digest([VERSAO, assinatura_metricas(), q, seq])
    cache = OUT / "cache/metricas" / (fp + ".json")
    if cache.exists():
        res = ler(cache)
    else:
        med = e.medir(q, seq, [], {}, "P0")
        res = {k: med[k] for k in METRICAS[:-1]}
        gravar(cache, res)
    # Mede transicoes dentro de CADA unidade com a mesma eventos(). Inclui
    # palavra livre interposta: tambem nao pode ser reparada reordenando IDs.
    res["piso_interno"] = sum(len(e.eventos(ks, q["gt_w"])) for ks in exp.values())
    exigir(res["piso_interno"] <= res["quebras"], "Piso excedeu quebras: expansao inconsistente")
    return res


def resumo(rows, R, rep, bancada, parcial=False):
    grupos = ("todos", "vistos", "nao_vistos") if bancada != "teste_silver" else ("todos",)
    saida = {}
    rep_base = "linhas" if rep == "caixas_finas" else rep
    base = R["resultados"].get(f"regra_colunas__{rep_base}__{bancada}", {})
    base_rows = {r["page_id"]: r for r in base.get("paginas", [])}
    for g in grupos:
        rs = [r for r in rows if g == "todos" or r["visto_treino"] == (g == "vistos")]
        if not rs:
            saida[g] = {"n": 0, "veiculos": 0, "metricas": {}, "contra_regra_colunas": {}}
            continue
        W = None if parcial else PESOS_CLUSTER(rs)
        ms = {}
        for k in METRICAS:
            v = [r["metricas"][k] for r in rs]
            vv = [x for x in v if x is not None]
            ms[k] = {"media": statistics.mean(vv) if vv else None, "n": len(vv), "ic": [None, None]} if parcial else e.media_ic(v, W)
            if k in ("quebras", "piso_interno"):
                ms[k]["total"] = sum(vv)
        # Contrastes por veiculo apenas em paginas pareadas, sem imputacao.
        testes = {}
        for k in METRICAS:
            pareadas = [r for r in rs if r["page_id"] in base_rows and r["metricas"][k] is not None and
                        base_rows[r["page_id"]]["metricas"][k] is not None]
            if parcial or not pareadas or not base.get("completa"):
                continue
            ds = [r["metricas"][k] - base_rows[r["page_id"]]["metricas"][k] for r in pareadas]
            veiculos = sorted({r["uf"] for r in pareadas})
            dvs = [statistics.mean(d for r, d in zip(pareadas, ds) if r["uf"] == uf) for uf in veiculos]
            testes[k] = {"delta": e.media_ic(ds, PESOS_CLUSTER(pareadas)),
                         "wilcoxon_veiculo": e.pratt(dvs), "n_pareadas": len(pareadas),
                         "n_veiculos": len(veiculos), "medias_diferencas_por_veiculo": dict(zip(veiculos, dvs))}
        saida[g] = {"n": len(rs), "veiculos": len({r["uf"] for r in rs}),
                    "metricas": ms, "contra_regra_colunas": testes,
                    "agrupadas_510": sum(bool(r.get("diag", {}).get("excesso_510")) for r in rs),
                    "hierarquia_510": sum(bool(r.get("diag", {}).get("hierarquia")) for r in rs)}
    return saida


def identidade(path, ordenador=None, representacao=None, bancada=None):
    partes = Path(path).stem.split("__")
    if len(partes) == 3:
        ordenador = ordenador or partes[0]
        representacao = representacao or partes[1]
        bancada = bancada or partes[2]
    bancada = "teste_silver" if bancada == "teste" else bancada
    exigir(ordenador and re.fullmatch(r"[A-Za-z0-9_-]+", ordenador), "Ordenador ausente/invalido no nome ou --ordenador")
    exigir(representacao in REPS and bancada in BANCADAS, "Use nome ordenador__representacao__bancada.jsonl ou as opcoes explicitas")
    return ordenador, representacao, bancada


def indice_pred(path, reparar=False):
    """So offsets em memoria; repara ultima linha incompleta apenas da saida propria."""
    out = {}
    with open(path, "rb") as f:
        while True:
            off = f.tell()
            l = f.readline()
            if not l:
                break
            if not l.strip():
                continue
            try:
                row = json.loads(l.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                if reparar and not f.read(1):
                    with open(destino(path), "r+b") as w:
                        w.truncate(off)
                    break
                raise ValueError(f"Predicao JSONL invalida: {path} offset {off}")
            exigir(set(row) == {"page_id", "ordem"} and isinstance(row["ordem"], list), "Contrato exige somente page_id e ordem")
            exigir(row["page_id"] not in out, f"Predicao duplicada: {row['page_id']}")
            out[row["page_id"]] = off
            if reparar and not l.endswith(b"\n"):
                with open(destino(path), "ab") as w:
                    w.write(b"\n")
                    w.flush()
                    os.fsync(w.fileno())
    return out


def ler_offset(f, off):
    f.seek(off)
    return json.loads(f.readline().decode("utf-8"))


def avaliar(arquivo, ordenador=None, representacao=None, bancada=None, *, estado=None, prazo=None):
    """Avalia contrato externo; nao prediz nem reavalia outros ordenadores.

    Em uso via import, adquirir trava() para persistencia concorrente segura.
    A identidade e inferida do nome ou passada explicitamente. Ordem interna
    usa fluxo() por unidade; IDs incompativeis/duplicados sao erros.
    """
    path = Path(arquivo).resolve()
    m, rep, b = identidade(path, ordenador, representacao, bancada)
    R = estado if estado is not None else iniciar()
    conferir_ancoras(R)
    inventario(R)
    ind = indice_pred(path)
    key = f"{m}__{rep}__{b}"
    old = R["resultados"].get(key, {})
    saved = {r["page_id"]: r for r in old.get("paginas", [])}
    rows, esperados = [], set()
    treino = set(ler(RAIZ / "data/processed/splits.json")["treino"])
    final = True
    with open(path, "rb") as f:
        for obj, p in paginas(b, rep):
            pid = p["page_id"]
            esperados.add(pid)
            if pid not in ind:
                continue
            pred = ler_offset(f, ind[pid])
            fp = digest([obj, p, pred, R["fontes"], VERSAO])
            if pid in saved and saved[pid].get("fingerprint") == fp:
                row = saved[pid]
            else:
                if prazo and time.monotonic() >= prazo:
                    final = False
                    break
                med = metricas(obj, p, pred["ordem"])
                dp = OUT / "cache/diagnosticos" / key / (e.ac.chave(pid) + ".json")
                diag = ler(dp) if dp.exists() and path == OUT / "pred" / (key + ".jsonl") else {}
                if diag.get("ordem_digest") != digest(pred["ordem"]):
                    diag = {}
                row = {"page_id": pid, "uf": obj["uf"], "visto_treino": obj["uf"] in treino,
                       "palavras_referencia": len(obj["gt_w"]), "unidades": len(p["bounding_boxes"]),
                       "metricas": med, "diag": diag, "fingerprint": fp}
            rows.append(row)
            R["resultados"][key] = {"ordenador": m, "representacao": rep, "bancada": b,
                "fonte_pred": rel(path), "completa": False, "esperadas": R["inventario"][b]["n"],
                "paginas": rows, "resumos": resumo(rows, R, rep, b, parcial=True)}
            salvar(R)
            if len(rows) % 20 == 0:
                print(f"Avaliar {key}: {len(rows)}/{R['inventario'][b]['n']}", flush=True)
    if final:
        exigir(set(ind) <= esperados, f"Predicao contem paginas fora da bancada: {sorted(set(ind)-esperados)[:3]}")
    completa = final and len(rows) == R["inventario"][b]["n"]
    R["resultados"][key] = {"ordenador": m, "representacao": rep, "bancada": b,
        "fonte_pred": rel(path), "pred_sha256": sha(path), "completa": completa,
        "esperadas": R["inventario"][b]["n"], "paginas": rows,
        "resumos": resumo(rows, R, rep, b, parcial=not completa)}
    if m == "regra_colunas" and completa:
        # Recalcula so os CONTRASTES estatisticos, nunca ordens/metricas alheias.
        for v in R["resultados"].values():
            if (v["representacao"] == rep or rep == "linhas" and v["representacao"] == "caixas_finas") and v["bancada"] == b and v["completa"]:
                v["resumos"] = resumo(v["paginas"], R, v["representacao"], b)
    salvar(R)
    print(f"{key}: {len(rows)} paginas; completa={completa}", flush=True)
    return R["resultados"][key]


def gerar(R, metodo, rep, b, lr, prazo):
    key = f"{metodo}__{rep}__{b}"
    path = destino(OUT / "pred" / (key + ".jsonl"))
    ind = indice_pred(path, reparar=True) if path.exists() else {}
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for obj, p in paginas(b, rep):
            pid = p["page_id"]
            if pid in ind:
                continue
            if prazo and time.monotonic() >= prazo:
                break
            ordem, diag = prever(p, obj["palavras"], metodo, lr)
            diag["ordem_digest"] = digest(ordem)
            gravar(OUT / "cache/diagnosticos" / key / (e.ac.chave(pid) + ".json"), diag)
            f.write(json.dumps({"page_id": pid, "ordem": ordem}, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
            ind[pid] = True
            R["progresso"][key] = {"preditas": len(ind), "esperadas": R["inventario"][b]["n"]}
            salvar(R)
    avaliar(path, estado=R, prazo=prazo)


def comparar_caixas_finas(R):
    """So importa medidas P1m humanas ja salvas, preservando o protocolo."""
    if R.get("comparacao_caixas_finas_importada"):
        return
    historico = ler(e.JSON)
    treino = set(ler(RAIZ / "data/processed/splits.json")["treino"])
    for b, c in (("golden_v4", "v4"), ("golden_v3_novo", "v3_novo")):
        rows = [{"page_id": r["page_id"], "uf": r["uf"], "visto_treino": r["uf"] in treino,
                 "metricas": {k: r["metodos"]["P1m"][k] for k in METRICAS}}
                for r in historico["paginas"] if r["coorte"] == c]
        exigir(len(rows) == R["inventario"][b]["n"], "Comparacao P1m com coorte diferente")
        key = f"extrator_xycut_margens__caixas_finas__{b}"
        R["resultados"][key] = {"ordenador": "extrator_xycut_margens", "representacao": "caixas_finas",
            "bancada": b, "fonte_pred": rel(e.JSON), "completa": True, "esperadas": len(rows),
            "paginas": rows, "resumos": resumo(rows, R, "caixas_finas", b)}
    R["comparacao_caixas_finas_importada"] = True
    salvar(R)


def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def cel(v, percentual=False, n=3):
    fator = 100 if percentual else 1
    if not v or v.get("media") is None:
        return "—"
    val = f(v["media"] * fator, n)
    if v["ic"][0] is not None:
        val += " [" + "; ".join(f(x * fator, n) for x in v["ic"]) + "]"
    return val + ("%" if percentual else "")


def relatorio(R):
    ls = ["# Ordenadores sobre unidades sem caixas finas", ""]
    if not R.get("ancoras", {}).get("aprovada"):
        ls += ["## Resposta em cinco linhas", "",
               "1. Ainda não é válido escolher um ordenador: a âncora nas unidades exportadas não passou.",
               "2. Linhas: comparação suspensa até a expansão canônica reproduzir a âncora.",
               "3. Colunas e colunas_margens: comparação suspensa pelo mesmo pré-requisito.",
               "4. O piso interno abaixo quantifica um custo que nenhum ordenador de unidades elimina.",
               "5. LayoutReader não foi carregado; os adaptadores e a avaliação externa ficam implementados.", "",
               "Nenhuma tabela publicada: checagem obrigatória das âncoras.", "",
               R.get("bloqueio", "Checagem em andamento; caches preservados para retomada."), ""]
        a = R.get("ancoras", {})
        if a.get("medias"):
            mm = a["medias"]
            ls += ["## Evidência executada", "",
                   f"Nas {a['n']} páginas v4, P2 canônico reproduz τ **{f(mm['P2']['tau'],6)}**, "
                   f"**{f(mm['P2']['quebras'],6)} quebras/página**. O controle P1m importado de "
                   f"`resultados/erros_ponta_a_ponta.json` dá τ **{f(mm['P1m']['tau'],6)}** e "
                   f"**{f(mm['P1m']['quebras'],6)} quebras/página**.", "",
                   f"A mesma regra com expansão canônica dá τ **{f(mm['regra_colunas_exportada']['tau'],6)}** e "
                   f"**{f(mm['regra_colunas_exportada']['quebras'],6)} quebras/página**. "
                   f"O piso interno é **{f(mm['regra_colunas_exportada']['piso_interno'],6)} quebras/página**. "
                   "A aprovação exige tolerância 0,006 em τ e 0,0051 nas quebras, além da identidade com P2 por página.", "",
                   f"`ks` difere da expansão canônica em **{a['paginas_ks_diferentes']} páginas**. "
                   "No diagnóstico que aplica `ordem_sem_bbox.fluxo()` dentro das unidades, "
                   f"**{a['paginas_canonizadas_identicas_P2']} sequências** ficam idênticas ao P2, "
                   f"com τ **{f(mm['expansao_canonica_diagnostico']['tau'],6)}** e "
                   f"**{f(mm['expansao_canonica_diagnostico']['quebras'],6)} quebras/página**. "
                   "Isso localiza a diferença na expansão interna, e não na permutação das unidades. "
                   "A expansão é a decisão explícita da tarefa 02b; nenhum arquivo exportado foi modificado.", "",
                   "Os preditores teto, ingênuo, XY-cut, XY-cut com margens, regra de colunas e LayoutReader CPU "
                   "estão implementados; `--avaliar-pred` também exige a âncora antes de incorporar modelos. "
                   "O teto exportado usa posto mediano, não ótimo combinatório. As métricas importam "
                   "`medir()`/`eventos()`; IC usa bootstrap por veículo e o contraste usa Wilcoxon Pratt.", "",
                   "Golden v4 participou do desenvolvimento; referência humana é ordem de regiões expandida, "
                   "não ouro independente palavra a palavra. Silver é automático, por fluxo PDF, "
                   "e não foi comparado nesta execução bloqueada. Veículos vistos/não vistos são definidos "
                   "pelo split congelado. Nenhum arquivo sob data/, docs/ ou o quadro foi alterado.", "",
                   "## Reprodução", "", "```powershell",
                   "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --somente-ancoras",
                   "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --conferir", "```", "",
                   "Após corrigir as entradas, arquivar as saídas desta execução antes de repetir: "
                   "a bancada recusa misturar fontes de hashes diferentes. Os números acima são gerados "
                   "pelo script; o JSON inclui medições e diagnósticos de todas as páginas.", ""]
        ls += ["Progresso: " + json.dumps(R.get("progresso", {}), ensure_ascii=False), ""]
        return "\n".join(ls)
    ls += ["## Resposta em cinco linhas", ""]
    vals = list(R["resultados"].values())
    for rep in REPS:
        partes = []
        for b in BANCADAS:
            rs = [v for v in vals if v["representacao"] == rep and v["bancada"] == b and
                  v["completa"] and v["ordenador"] != "teto"]
            if not rs:
                partes.append(b + ": pendente")
                continue
            menor = min(v["resumos"]["todos"]["metricas"]["quebras"]["media"] for v in rs)
            melhores = [v for v in rs if abs(v["resumos"]["todos"]["metricas"]["quebras"]["media"]-menor) < 1e-12]
            nomes = "/".join(v["ordenador"] for v in melhores)
            partes.append(f"{b}: {nomes}, {f(menor,2)} quebras/página")
        ls.append(f"- **{rep}** — " + "; ".join(partes) + ".")
    custos = []
    for rep in REPS:
        for b in BANCADAS:
            v = R["resultados"].get(f"teto__{rep}__{b}")
            if v and v["completa"]:
                ms = v["resumos"]["todos"]["metricas"]
                custos.append(f"{rep}/{b}: τ {f(ms['tau']['media'])}, {f(ms['quebras']['media'],2)} quebras/página (piso {f(ms['piso_interno']['media'],2)})")
    ls += ["- **Custo da representação (teto exportado)** — " + ("; ".join(custos) if custos else "pendente") + ".",
           "- Menos erros significa menor média de quebras; empates ficam explícitos. Comparação de bancada só é conclusiva após completar os seis ordenadores. O teto mediano não garante ótimo combinatório; o piso interno canônico é irredutível.", ""]
    a = R["ancoras"]["medias"]
    ls += ["## Âncoras", "", f"P2 canônico reexecutado: τ {f(a['P2']['tau'],6)}, {f(a['P2']['quebras'],6)} quebras/página. "
           f"Extrator + XY-cut + margens importado: τ {f(a['P1m']['tau'],6)}, {f(a['P1m']['quebras'],6)}. "
           "As sequências e métricas P2 conferem por página com o histórico; P1m vem de `resultados/erros_ponta_a_ponta.json`. "
           "A configuração é `projecao_local_margens` 0,45 / 1,2 / 0,08. "
           f"A regra sobre linhas reproduz τ {f(a['regra_colunas_exportada']['tau'],6)} e "
           f"{f(a['regra_colunas_exportada']['quebras'],6)} quebras/página: "
           f"{R['ancoras']['paginas_canonizadas_identicas_P2']} sequências idênticas ao P2. "
           "Toda unidade é um conjunto de palavras; `ordem_sem_bbox.fluxo()` ordena suas palavras em todas as representações, bancadas e predições externas.", "",
           "## Diagnóstico separado: custo de `ks` cru", "",
           f"No golden_v4/linhas, regra com `ks` cru: τ **{f(a['regra_colunas_ks_cru']['tau'],6)}**, "
           f"**{f(a['regra_colunas_ks_cru']['quebras'],2)} quebras/página**, piso interno "
           f"**{f(a['regra_colunas_ks_cru']['piso_interno'],2)}**. Com expansão canônica, piso "
           f"**{f(a['regra_colunas_exportada']['piso_interno'],6)}**. "
           f"A ordem crua difere em {R['ancoras']['paginas_ks_diferentes']} páginas. "
           "Esses números crus não entram na comparação de ordenadores. Saídas bloqueadas anteriores preservadas em `resultados/ordenadores_sem_caixas/arquivo_0030/`.", ""]
    for key, d in R.get("diagnosticos_internos", {}).items():
        tipos = "; ".join(f"{t}: {s['unidades']} unidades, {s['com_linhas_lado_a_lado']} com vãos lado a lado, "
                          f"piso cru/canônico total {s['piso_ks_cru']}/{s['piso_canonico']}"
                          for t, s in d["tipos"].items()) or "nenhuma unidade difere"
        ls.append(f"- **{key}**: {d['paginas_diferentes']} páginas com divergência; {tipos}.")
    dg = R.get("diagnosticos_internos", {}).get("linhas__golden_v4", {})
    exemplos = dg.get("exemplos", [])
    if exemplos:
        ls += ["", "Três exemplos da âncora (IDs reais; demais detalhes no JSON):", ""]
        for d in exemplos:
            ls.append(f"- `{d['page_id']}`: unidade `{d['id']}` ({d['tipo']}), "
                      f"{d['palavras']} palavras, {d['linhas']} linhas, "
                      f"piso cru {d['piso_ks_cru']} → canônico {d['piso_canonico']}.")
    ls += ["", "Vão lado a lado = palavras na mesma linha geométrica separadas por mais de `max(4; 1,2 × altura mediana)`. "
           "Nas faixas, a expansão canônica pode intercalar esses trechos; isso é um custo da representação, ainda presente no piso. "
           "A tipologia e os exemplos descrevem divergências entre expansões; não certificam que toda mudança melhora a leitura.", ""]
    for b in BANCADAS:
        inv = R.get("inventario", {}).get(b)
        if not inv:
            continue
        ls += [f"## {b}", "", f"{inv['n']} páginas, {inv['veiculos']} veículos; "
               f"{inv['vistos']} páginas de veículos vistos no treino e {inv['nao_vistos']} não vistos. "
               + ("Não há páginas vistas nesta bancada; por isso não existe estimativa para esse grupo." if not inv['vistos'] else ""), "",
               "Valores macro por página [IC 95% agrupado por veículo]. Piso é média de quebras internas por página.", "",
               "| Representação | Ordenador | Veículos | n | τ palavras | Quebras/página | Quebras/mil | Fidelidade 12 | Sucessor linhas | Piso interno | p veículo (quebras) | >510 agrupadas |",
               "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for v in sorted((v for v in vals if v["bancada"] == b), key=lambda v: (v["representacao"], v["ordenador"])):
            for g, s in v["resumos"].items():
                if not s["n"]:
                    continue
                ms = s["metricas"]
                teste = s["contra_regra_colunas"].get("quebras", {})
                pv = teste.get("wilcoxon_veiculo", {}).get("p")
                nome = v["ordenador"] + (" (parcial)" if not v["completa"] else "")
                grupo = {"todos": "todos", "vistos": "vistos", "nao_vistos": "não vistos"}[g]
                ls.append(f"| {v['representacao']} | {nome} | {grupo} ({s['veiculos']}) | {s['n']} | " + " | ".join([
                    cel(ms["tau"]), cel(ms["quebras"], n=2), cel(ms["quebras_mil"], n=2),
                    cel(ms["fid12"], True, 1), cel(ms["sucessor_linhas"], True, 1),
                    cel(ms["piso_interno"], n=2), f(pv, 6), str(s["agrupadas_510"])]) + " |")
    ls += ["", "## Quando a mediana não é teto", ""]
    falhas_teto = []
    for rep in REPS:
        for b in BANCADAS:
            teto = R["resultados"].get(f"teto__{rep}__{b}", {})
            regra = R["resultados"].get(f"regra_colunas__{rep}__{b}", {})
            if not (teto.get("completa") and regra.get("completa")):
                continue
            for g, st in teto["resumos"].items():
                if not st["n"]:
                    continue
                tm, rm = st["metricas"], regra["resumos"][g]["metricas"]
                difs = []
                if tm["tau"]["media"] < rm["tau"]["media"] - 1e-12:
                    difs.append(f"τ {f(tm['tau']['media'],6)} < {f(rm['tau']['media'],6)}")
                if tm["quebras"]["media"] > rm["quebras"]["media"] + 1e-12:
                    difs.append(f"quebras {f(tm['quebras']['media'],2)} > {f(rm['quebras']['media'],2)}")
                if difs:
                    falhas_teto.append(f"- {rep}/{b}/{g}: " + "; ".join(difs) + ".")
    ls += falhas_teto or ["Nas comparações completas disponíveis, a ordem mediana não ficou abaixo da regra em τ nem em quebras médias."]
    ls += ["", "Posto mediano é um oráculo de referência, sem garantia de máximo τ ou mínimo de quebras. "
           "Onde perde para a regra, não é teto de verdade. O piso interno tem garantia: nenhuma permutação de unidades conserta essas transições.", ""]
    inv = R.get("inventario", {})
    ls += ["", "## Protocolo e limitações", "",
           f"Bootstrap percentil de 95%, {NBOOT} reamostras de veículos, semente {SEMENTE}; todas as páginas de cada veículo sorteado ficam juntas. "
           "A média é macro por página. Quebras/mil também é média das taxas por página. O JSON guarda totais, IC de todas as métricas e deltas pareados.", "",
           "Wilcoxon bilateral Pratt (`zero_method='pratt'`, aproximação normal) sobre médias das diferenças pareadas por veículo, contra regra_colunas na mesma representação e bancada. "
           "O JSON inclui os testes de τ, quebras, taxa por mil, fidelidade 12 e sucessor de linhas. P-valores exploratórios sem correção de multiplicidade; células sem base completa ficam pendentes. "
           "Com poucos veículos, especialmente no silver, a inferência tem baixa resolução.", "",
           "Golden v4 foi usado no desenvolvimento da regra de colunas e na escolha dos parâmetros; não é teste independente. "
           "Golden v3 novo usa páginas adicionais, mas pode repetir veículos/layouts do desenvolvimento. A coluna vistos refere-se ao split de treino do TCC, não ao treino prévio do detector ls3 ou do LayoutReader. "
           "O ouro humano é ordem de regiões expandida geometricamente, não anotação independente de cada palavra/linha; no v3 há projeção sobre blocos do extrator. Tabelas têm ordem interna potencialmente ambígua.", "",
           "Silver usa fluxo de conteúdo PDF, só CE/MA/RJ do split congelado. É referência automática escolhida por concordância com XY-cut por veículo, favorecendo regras geométricas. "
           "Linhas silver são trechos contíguos do fluxo, separados por linhas geométricas com gap 1,2; sucessor silver não é ouro humano. "
           f"Há {inv.get('sobreposicao_silver_humanas',0)} páginas em comum entre silver e as bancadas humanas: tabelas separadas, sem somar como observações independentes.", "",
           "Teto = `ordens.stream` da tarefa 01, derivada do posto mediano das palavras. Unidades que atravessam a referência impedem um teto combinatório exato. "
           "O piso soma `eventos(fluxo([unidade], palavras), gt_w)` dentro de cada unidade, incluindo palavras sem referência interpostas; reordenar IDs não altera esses pares. "
           "O custo do teto inclui esse piso e fronteiras da ordem mediana; não atribuir tudo ao ordenador. Unidades sem palavras participam da permutação, mas não das métricas textuais.", "",
           "Entrada determinística `random.Random(f'entrada-{page_id}')`, via protocolo; preditores automáticos recebem apenas IDs, caixas, tipos/texto e palavras. "
           "LayoutReader usa o adaptador local em CPU/float32; acima de 510 unidades, há agrupamento geométrico ou hierarquia espacial, preservando todas as unidades. "
           "A carga de pesos é sequencial (`HF_DEACTIVATE_ASYNC_LOAD=1`), com leitura direta (`disable_mmap=True`): a materialização por memória mapeada esperou no Windows, mesmo após desativar a carga assíncrona. "
           "Isso mede um híbrido nessas páginas, não inferência neural direta em todas as linhas. A coluna >510 mostra páginas efetivamente agrupadas; diagnósticos por página ficam no JSON. "
           "Um único processo, threads no máximo 4, sem workers ou abertura de PDFs. Nenhum treino/modelo de linguagem nesta tarefa. ls3 só fornece detecções em cache; seus dados parceiros não foram lidos.", "",
           "## Retomada e integração", "", "```powershell",
           "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py",
           "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --metodos layoutreader_pronto --max-minutos 30",
           "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --avaliar-pred resultados/ordenadores_sem_caixas/pred/modelo__linhas__golden_v4.jsonl",
           "venv/Scripts/python.exe -B orquestracao/analises/bancada_ordenadores.py --conferir", "```", "",
           "Contrato JSONL estrito: `{" + '"page_id": "...", "ordem": ["b0", "b1"]' + "}`. "
           "Nomes: `<ordenador>__<linhas|colunas|colunas_margens>__<golden_v4|golden_v3_novo|teste_silver>.jsonl`; "
           "`teste` é aceito como alias. Opções explícitas `--ordenador`, `--representacao`, `--bancada` aceitam nomes externos. "
           "Predições parciais têm cobertura declarada. IDs/páginas incompatíveis falham; nunca são reparados. "
           "`--avaliar-pred` atualiza só a predição recebida e o relatório, reaproveitando resultados anteriores; nenhum modelo é carregado. "
           "Predições e métricas são persistidas a cada página. Fontes e código são identificados por SHA-256; mudança de fontes é recusada. "
           "Shards de entrada são fechados após cada linha, antes do processamento. "
           "`ancora_ok.json` só é publicado quando as âncoras e as 54 combinações obrigatórias estão completas e conferidas.", ""]
    if R.get("modelo_layoutreader"):
        ls += ["LayoutReader carregado: `" + json.dumps(R["modelo_layoutreader"], ensure_ascii=False) + "`.", ""]
    if R.get("progresso"):
        ls += ["Progresso persistido: `" + json.dumps(R["progresso"], ensure_ascii=False) + "`.", ""]
    if R.get("bloqueio"):
        ls += ["Pendência da execução: " + R["bloqueio"], ""]
    return "\n".join(ls)


def conferir(R):
    exigir(R["fontes"] == fontes(), "Fontes alteradas")
    exigir(MD.read_text(encoding="utf-8") == relatorio(R), "Markdown diverge do JSON")
    a = R.get("ancoras", {})
    if a.get("medias"):
        exigir(len(a["paginas"]) == a["n"] == 44, "Ancora sem 44 paginas")
        for m, ms in a["medias"].items():
            for k, v in ms.items():
                exigir(abs(statistics.mean(r[m][k] for r in a["paginas"])-v) < 1e-10,
                       "Media de ancora nao corresponde as paginas")
        for p, h in a["detectores_sha256"].items():
            exigir(sha(RAIZ / p) == h, "Deteccao da ancora alterada")
    n = 0
    for v in R["resultados"].values():
        if "pred_sha256" in v:
            exigir(sha(RAIZ / v["fonte_pred"]) == v["pred_sha256"], "Predicao alterada")
        esperado = resumo(v["paginas"], R, v["representacao"], v["bancada"], parcial=not v["completa"])
        exigir(esperado == v["resumos"], "Resumo nao corresponde as metricas por pagina")
        n += len(v["paginas"])
    print(f"CONFERE: fontes, {a.get('n',0)} ancoras, predicoes, Markdown e resumos de {n} avaliacoes; sem reavaliar/inferir", flush=True)


def publicar_sinal(R):
    """Libera a proxima tarefa somente com todas as tabelas obrigatorias."""
    a = R.get("ancoras", {})
    if not a.get("aprovada") or R.get("bloqueio"):
        return
    obrigatorias = [f"{m}__{rep}__{b}" for m in METODOS for rep in REPS for b in BANCADAS]
    if not all(R["resultados"].get(k, {}).get("completa") for k in obrigatorias):
        return
    exigir(R["fontes"] == fontes(), "Fontes alteradas antes de publicar ancora_ok")
    for k in obrigatorias:
        v = R["resultados"][k]
        exigir(len(v["paginas"]) == R["inventario"][v["bancada"]]["n"], "Tabela obrigatoria incompleta")
        exigir(sha(RAIZ / v["fonte_pred"]) == v["pred_sha256"], "Predicao alterada antes do sinal")
        exigir(all(s["contra_regra_colunas"] for s in v["resumos"].values() if s["n"]),
               "Tabela sem contraste contra a regra")
    sinal = {"aprovada": True, "versao": VERSAO, "expansao_interna": R["config"]["expansao_interna"],
             "ancoras": a["medias"], "paginas_ancora": a["n"],
             "sequencias_identicas_P2": a["paginas_canonizadas_identicas_P2"],
             "ordenadores_avaliados": sorted({v["ordenador"] for v in R["resultados"].values() if v["completa"]}),
             "ordenadores_obrigatorios": list(METODOS), "combinacoes_obrigatorias": obrigatorias,
             "inventario": R["inventario"], "fontes_fingerprint": digest(R["fontes"]),
             "relatorio_json_sha256": sha(JSON), "relatorio_md_sha256": sha(MD)}
    gravar(OUT / "ancora_ok.json", sinal)
    print(f"ancora_ok.json publicado: {len(obrigatorias)} tabelas obrigatorias completas", flush=True)


def carregar_layoutreader():
    """Embrulha a carga local: evita storage mmap que esperou no Windows.

    Reusa integralmente o Ordenador e sua inferencia CPU/float32. A opcao
    disable_mmap le os mesmos tensores diretamente do arquivo safetensors.
    A alteracao temporaria do classmethod nao escreve na biblioteca/adaptador.
    """
    from orquestracao.analises import ordem_layoutreader as adaptador
    from transformers import LayoutLMv3ForTokenClassification as Modelo
    original = Modelo.from_pretrained
    descriptor = Modelo.__dict__.get("from_pretrained")
    def carregar(*args, **kwargs):
        return original(*args, **{**kwargs, "disable_mmap": True})
    Modelo.from_pretrained = staticmethod(carregar)
    try:
        lr = adaptador.Ordenador(4)
        lr.info.update(carregamento_assincrono=False, disable_mmap=True)
        return lr
    finally:
        if descriptor is None:
            del Modelo.from_pretrained
        else:
            Modelo.from_pretrained = descriptor


def autoteste():
    """Verifica contrato, expansao canonica e piso com palavra livre interna."""
    ws = [[str(i), i*5., 10., i*5.+4, 20., 0] for i in range(15)]
    obj = {"palavras": ws, "gt_w": list(range(15))}
    p = {"page_id": "sintetico", "dimensions": {"width": 100, "height": 100},
         "bounding_boxes": [{"id": "a", "ks": [0,2,1]+list(range(3,8)), "text": "a", "tipo": "texto", "bbox": [0,10,50,20]},
                            {"id": "b", "ks": list(range(8,15)), "text": "b", "tipo": "texto", "bbox": [0,30,50,40]}]}
    res = metricas(obj, p, ["a", "b"])
    assert res["piso_interno"] == 0 and res["quebras"] == 0
    raw = metricas(obj, p, ["a", "b"], canonica=False)
    assert raw["piso_interno"] == 3 and raw["quebras"] == 3
    original = list(p["bounding_boxes"][0]["ks"])
    p["bounding_boxes"][0]["ks"].reverse()
    assert metricas(obj, p, ["a", "b"]) == res
    p["bounding_boxes"][0]["ks"] = original
    try:
        metricas(obj, p, ["a", "a"])
    except ValueError:
        pass
    else:
        raise AssertionError("IDs duplicados aceitos")
    obj["gt_w"] = [0,2]+list(range(3,15))
    p["bounding_boxes"][0]["ks"] = list(range(8))
    res = metricas(obj, p, ["a", "b"])
    assert res["piso_interno"] == 1 and res["quebras"] == 1
    p["ordens"] = {"stream": ["b", "a"]}
    for nome in METODOS[:-1]:
        ordem, _ = prever(p, ws, nome)
        assert sorted(ordem) == ["a", "b"]
        if nome != "teto":
            p2 = {**p, "ordens": {"stream": ["a", "b"]}}
            assert prever(p2, ws, nome)[0] == ordem
    assert PESOS_CLUSTER([{"uf": "A"}, {"uf": "B"}, {"uf": "B"}]).shape == (NBOOT, 3)
    assert e.pratt([0., 0.])["p"] == 1.
    from orquestracao.analises import ordem_layoutreader as adaptador
    muitos = [{"bbox": [x, 100+3*y, x+380, 102+3*y], "tipo": "texto", "ks": [col*260+y]}
              for col, x in enumerate((50, 550)) for y in range(260)]
    gs = adaptador.grupos_projecao(muitos, list(range(520)), 2., .08)
    assert sorted(i for g in gs for i in g) == list(range(520)) and len(gs) <= 510
    print("Autoteste: expansao/piso, contrato, cinco preditores, isolamento do ouro, bootstrap e agrupamento 510 conferidos", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--avaliar-pred", type=Path)
    ap.add_argument("--ordenador")
    ap.add_argument("--representacao", choices=REPS)
    ap.add_argument("--bancada", choices=BANCADAS + ("teste",))
    ap.add_argument("--metodos", nargs="+", choices=METODOS, default=list(METODOS))
    ap.add_argument("--representacoes", nargs="+", choices=REPS, default=list(REPS))
    ap.add_argument("--bancadas", nargs="+", choices=BANCADAS, default=list(BANCADAS))
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--somente-ancoras", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()
    exigir(args.max_minutos >= 0, "max-minutos deve ser nao negativo")
    with trava():
        if args.autoteste:
            autoteste()
            return
        R = iniciar()
        if args.conferir:
            conferir(R)
            return
        prazo = time.monotonic() + args.max_minutos*60 if args.max_minutos else None
        conferir_ancoras(R)
        inventario(R)
        diagnosticos_internos(R)
        comparar_caixas_finas(R)
        if args.somente_ancoras:
            return
        if args.avaliar_pred:
            avaliar(args.avaliar_pred, args.ordenador, args.representacao, args.bancada, estado=R, prazo=prazo)
            publicar_sinal(R)
            return
        lr = None
        try:
            # Geometria antes da rede; uma instancia de modelo em CPU.
            for m in sorted(set(args.metodos), key=lambda m: (m == "layoutreader_pronto", METODOS.index(m))):
                for rep in args.representacoes:
                    for b in args.bancadas:
                        if prazo and time.monotonic() >= prazo:
                            R["bloqueio"] = "Prazo --max-minutos atingido; retome o mesmo comando."
                            salvar(R)
                            return
                        key = f"{m}__{rep}__{b}"
                        pronto = R["resultados"].get(key, {})
                        if pronto.get("completa"):
                            exigir(sha(RAIZ / pronto["fonte_pred"]) == pronto["pred_sha256"], "Predicao propria alterada")
                            continue
                        if m == "layoutreader_pronto" and lr is None:
                            mem = memoria()
                            exigir(mem.get("ram_livre_mb", 3000) >= 2500 and mem.get("commit_livre_mb", 4000) >= 3000,
                                   f"LayoutReader adiado por RAM/commit livre: {mem}; retome com placa/memoria livre")
                            from orquestracao.analises import ordem_layoutreader as adaptador
                            lr = carregar_layoutreader()
                            R["modelo_layoutreader"] = {**lr.info, "pesos_sha256": sha(adaptador.MODELO / "model.safetensors")}
                            exigir(R["modelo_layoutreader"]["dispositivo"] == "cpu", "Modelo fora da CPU")
                            salvar(R)
                        gerar(R, m, rep, b, lr, prazo)
            R.pop("bloqueio", None)
            salvar(R)
            conferir(R)
            publicar_sinal(R)
        except Exception as exc:
            R["bloqueio"] = str(exc)
            salvar(R)
            raise
        finally:
            del lr
            gc.collect()


if __name__ == "__main__":
    main()
