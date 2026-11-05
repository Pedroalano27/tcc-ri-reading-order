"""Treina o grafo E004 em silver e seleciona sua decodificacao sem teste cego.

Embrulha candidatos, decodificadores e diagnosticos do E002; a regua continua
corretor_de_transicoes.medir. Nao altera fontes, anotacoes ou outros caches.
Features e rotulos sao separados; veiculo e page_id nunca entram na rede.
O treino usa shards congelados de linhas, sem carregar o corpus em memoria.
LightGBM le matrizes mapeadas por Sequence e salva checkpoints de arvores.

Uso da raiz (CPU, um processo, quatro threads):
  venv/Scripts/python.exe -B orquestracao/analises/e004_grafo.py
  ... --autoteste --somente-ancora
  ... --etapa diagnostico
  ... --etapa preparar-treino  # prepara pares/matrizes mesmo sem LightGBM
  ... --max-minutos 30   # repetir retoma paginas, matrizes e arvores
  ... --conferir        # confere relatorio, resumo e caches sem reescrever
Dependencia: venv/Scripts/python.exe -B -m pip install lightgbm
Toda escrita fica em resultados/e004_grafo/, exceto este proprio script.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse
import ast
import collections
import gc
import hashlib
import importlib.util
import itertools
import json
import math
import re
import shutil
import statistics
import time
from contextlib import contextmanager

import numpy as np
import psutil
from scipy.optimize import minimize
from scipy.special import expit
from orquestracao.analises import e002_oraculos as o
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e

if "torch" in sys.modules:
    sys.modules["torch"].set_num_threads(4)

OUT = RAIZ / "resultados/e004_grafo"
CACHE = OUT / "cache"
SEMENTE = 20261102
VERSAO = "e004-1"
KS = (12, 24, 32)
LIMIARES = (0., .5, .8, .95)
DECODERS = {"guloso": o.guloso, "matching": o.matching,
            "maxregret": o.lm.max_regret}
COORTES = o.COORTES
AJUSTE = o.DESENV
EXTERNAS = COORTES[2:]
METRICAS = o.METRICAS
HIPERS = ({"num_leaves": 15, "min_data_in_leaf": 100},
          {"num_leaves": 31, "min_data_in_leaf": 100})
ARVORES = (40, 80, 120)
PRAZO = None
LOCK_SHA = None
EXEC = None
MANIFESTO = None
AMOSTRAGEM = {"semente": 7, "max_pares": 4_000_000, "rank_max": 4,
              "calibracao": "Platt OOF nao amostrado"}
PROCESSO = psutil.Process()
PICO_RSS_MB = 0.

NO = ("x", "y", "largura", "altura", "coluna", "pos_regra", "pos_coluna",
      "ponte", "margem_topo", "margem_rodape", "margem_marca", "texto", "tabela", "imagem",
      "ponto_final", "pontuacao_final", "hifen_final", "inicio_maiuscula", "numeracao",
      "log_palavras", "inicio_minuscula", "log_caracteres", "fim_coluna",
      "repeticao", "repeticao_disponivel")
PAR = ("fim", "dx_pagina", "dy_pagina", "dx_h", "dy_h", "dist_pagina", "dist_h",
       "gap_y_h", "sobreposicao_x", "alinha_esquerda_h", "mesma_coluna", "salto_coluna",
       "delta_pos_regra", "sucessor_regra", "primeira_abaixo", "rank_candidato",
       "rank_candidato_relativo", "candidato_extra")
FEATURES = tuple(p+n for p in ("i_", "j_") for n in NO) + PAR


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def destino(path):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora de E004: "+str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def gravar(path, obj):
    path = destino(path)
    tmp = path.with_suffix(path.suffix+".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, path)


def salvar_npz(path, **dados):
    path = destino(path)
    tmp = path.with_suffix(path.suffix+".tmp")
    with tmp.open("wb") as f:
        np.savez_compressed(f, **dados)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, path)


def carregar(path):
    return b.ler(path) if Path(path).exists() else None


def vigiar():
    if PRAZO is not None and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; repetir o comando retoma os caches")
    assinatura, _ = o.ler_lock()
    exigir(assinatura == LOCK_SHA, "Lock cego mudou durante a execucao")
    mem = b.memoria()
    medir_memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 800 and mem["commit_livre_mb"] >= 1200,
           "Memoria insuficiente; cache preservado: "+str(mem))
    exigir(PICO_RSS_MB <= 3072, "RSS excedeu 3 GiB; cache preservado")


def medir_memoria():
    """Pico real do SO, inclusive entre chamadas; Windows informa peak_wset."""
    global PICO_RSS_MB
    mi = PROCESSO.memory_info()
    PICO_RSS_MB = max(PICO_RSS_MB, mi.rss/2**20, getattr(mi, "peak_wset", 0)/2**20)
    return {"rss_mb": mi.rss/2**20, "pico_rss_mb": PICO_RSS_MB,
            "medicao": "psutil: RSS e peak_wset do sistema operacional",
            "limite_rss_mb": 3072, "min_ram_livre_mb": 800, "min_commit_livre_mb": 1200}


@contextmanager
def trava():
    path = destino(CACHE / "execucao.lock")
    with path.open("a+b") as f:
        if f.tell() == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def ids_somente(path):
    """Le somente identificadores para impedir vazamento, sem abrir paginas."""
    with path.open(encoding="utf-8") as f:
        for raw in f:
            if not raw.strip():
                continue
            m = re.search(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")', raw)
            exigir(m, "Registro sem page_id")
            pid = json.loads(m.group(1))
            o.permitido(pid)
            yield pid


def manifesto():
    splits = b.ler(RAIZ / "data/processed/splits.json")
    paths = set(b.DEP_PATHS) | {Path(__file__), Path(o.__file__), Path(c.__file__),
            Path(o.lm.__file__), b.UNIDADES / "treino_noite.json",
            RAIZ / "data/processed/splits.json"}
    for co in c.HUMANAS:
        paths.add(b.UNIDADES / "bancadas" / (co+".jsonl"))
    for part in ("treino", "validacao", "teste"):
        for uf in splits[part]:
            for pasta in (("linhas", "linhas_extra") if part == "treino" else ("linhas",)):
                for suf in (".jsonl", ".palavras.jsonl"):
                    path = b.UNIDADES / pasta / (uf+suf)
                    if path.exists():
                        paths.add(path)
    for co in COORTES:
        for m in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
            path = b.OUT / "pred" / f"{m}__linhas__{co}.jsonl"
            if path.exists():
                paths.add(path)
    # Hash de arquivo nao desserializa nem avalia paginas externas.
    fontes = {p.relative_to(RAIZ).as_posix(): c.sha(p) for p in sorted(paths)}
    return {"versao": VERSAO, "fontes": fontes, "lock_cego_sha256": LOCK_SHA,
            "semente": SEMENTE, "K": KS, "limiares": LIMIARES,
            "hipers": HIPERS, "arvores": ARVORES, "features": FEATURES,
            "amostragem": AMOSTRAGEM,
            "cpu": True, "threads": 4, "processos": 1, "num_workers": 0}


def reusar_preparo():
    """Reusa pares apos conserto apenas no treinador, com prova de mesmo AST.

    A primeira preparacao pode ter sido feita antes de instalar LightGBM.
    Exige snapshot que reproduza o hash do script antigo, todas as demais
    fontes identicas e AST identica das funcoes/constantes de preparacao.
    Nao reusa modelos, selecoes ou avaliacoes de outra assinatura.
    """
    if (EXEC / "inventario_treino.json").exists():
        return
    alvos = {"paginas_treino", "candidatos", "matriz_features", "preparar_treino", "matrizes",
             "salvar_npz", "gravar", "ids_somente", "NO", "PAR", "FEATURES", "KS"}
    def componentes(texto):
        out = {}
        for node in ast.parse(texto).body:
            if isinstance(node, ast.FunctionDef) and node.name in alvos:
                out[node.name] = ast.dump(node, include_attributes=False)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in alvos:
                        out[target.id] = ast.dump(node, include_attributes=False)
        exigir(set(out) == alvos, "Componente de preparo nao encontrado")
        return out
    codigo = Path(__file__).read_text(encoding="utf-8")
    novo = componentes(codigo)
    chave_script = Path(__file__).relative_to(RAIZ).as_posix()
    fontes = {k: v for k, v in MANIFESTO["fontes"].items() if k != chave_script}
    for estado_path in sorted(CACHE.glob("*/estado.json")):
        origem = estado_path.parent
        inventario = origem / "inventario_treino.json"
        snapshot = origem / "codigo_preparo.txt"
        if origem == EXEC or not inventario.exists() or not snapshot.exists():
            continue
        antigo = b.ler(estado_path)["manifesto"]
        if {k: v for k, v in antigo["fontes"].items() if k != chave_script} != fontes:
            continue
        if antigo["lock_cego_sha256"] != LOCK_SHA:
            continue
        raw = snapshot.read_bytes()
        hashes = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}
        exigir(antigo["fontes"][chave_script] in hashes, "Snapshot de preparo sem hash verificavel")
        if componentes(raw.decode("utf-8")) != novo:
            continue
        registros = b.ler(inventario)
        exigir(len(registros) == 3140, "Preparo anterior incompleto")
        for r in registros:
            o.permitido(r["page_id"])
            exigir(c.sha(origem / r["arquivo"]) == r["sha256"], "Par anterior alterado")
        for pasta in ("pares", "matrizes"):
            if (origem / pasta).exists():
                # Arquivos completos sao imutaveis; links evitam duplicar 4 GB.
                shutil.copytree(origem / pasta, destino(EXEC / pasta),
                                dirs_exist_ok=True, copy_function=os.link)
        gravar(EXEC / "inventario_treino.json", registros)
        gravar(EXEC / "origem_preparo.json", {"origem": origem.relative_to(OUT).as_posix(),
                "script_sha256": antigo["fontes"][chave_script], "componentes_ast_sha256": c.digest(novo),
                "paginas": len(registros), "motivo": "Mesmas features/rotulos; somente adaptador de treino corrigido"})
        print("Pares anteriores reaproveitados apos conferencia de fontes, AST e hashes", flush=True)
        return


def preparo_pronto():
    """Confere hashes e reutiliza o inventario sem abrir novamente o corpus."""
    registros = carregar(EXEC / "inventario_treino.json")
    if registros:
        exigir(len(registros) == 3140, "Inventario de treino incompleto")
        for r in registros:
            o.permitido(r["page_id"])
            exigir(c.sha(EXEC / r["arquivo"]) == r["sha256"], "Cache de pares mudou")
        print(f"Preparo reaproveitado: {len(registros)} paginas; features originais preservadas", flush=True)
        return registros
    return preparar_treino()


def paginas_treino():
    """Embrulha os mesmos shards base/extra usados por treinar_sem_caixas."""
    humanos = set().union(*(set(ids_somente(b.UNIDADES / "bancadas" / (co+".jsonl")))
                             for co in c.HUMANAS))
    splits = b.ler(RAIZ / "data/processed/splits.json")
    exigir(not set(splits["treino"]) & set(splits["validacao"]+splits["teste"]),
           "Veiculos de treino/validacao/teste sobrepostos")
    vistos = {}
    for pasta in ("linhas", "linhas_extra"):
        for uf in splits["treino"]:
            path = b.UNIDADES / pasta / (uf+".jsonl")
            wp = path.with_name(uf+".palavras.jsonl")
            exigir(path.exists() and wp.exists(), "Shard de treino ausente: "+str(path))
            for p, obj in itertools.zip_longest(o.linhas_seguras(path), o.linhas_seguras(wp)):
                exigir(p and obj and p["page_id"] == obj["page_id"], "Shards de treino divergentes")
                pid = p["page_id"]
                exigir(pid not in humanos and p["uf"] == uf and
                       p["particao"] == ("treino_extra" if pasta == "linhas_extra" else "treino"),
                       "Pagina humana/particao incorreta no treino")
                exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
                       obj["gt_w"] == list(range(len(obj["palavras"]))), "Silver de treino mudou")
                sig = c.digest([c.automatico(p), obj["palavras"], obj["gt_w"]])
                if pid in vistos:
                    exigir(vistos[pid] == sig, "Duplicata base/extra com conteudo diferente")
                    continue
                vistos[pid] = sig
                yield {**obj, "uf": uf}, p, sig
    esperado = b.ler(b.UNIDADES / "treino_noite.json")["por_representacao"]["linhas"]["paginas_unicas"]
    exigir(len(vistos) == esperado == 3140, f"Treino congelado divergente: {len(vistos)} / {esperado}")


def candidatos(ctx):
    """Preserva top-K E002 e adiciona topos, sem consultar ouro.

    Fim de coluna e proxy geometrica: ultimo terco (pos >= .65, como a
    categoria importada), ou fonte cuja regra sai da coluna. Os tres primeiros
    itens de cada coluna a direita e de trechos abaixo separados por 2,5 alturas
    sao adicionais, nao substituem as K vagas originais. Empates pela entrada.
    """
    base = o.candidatos(ctx)
    enriquecidos = {k: {} for k in KS}
    extras = {}
    for u in ctx["entrada"]:
        col = ctx["col"][u]
        z = ctx["regra"][u]
        terminal = ctx["pos"].get(u, 0) >= .65 or z is None or ctx["col"].get(z) != col
        novos = []
        if terminal:
            for vcol, grupo in sorted(ctx["grupos"].items()):
                if vcol > col:
                    novos.extend(grupo[:3])
                abaixo = [v for v in grupo if ctx["mapa"][v]["bbox"][1] >
                          ctx["mapa"][u]["bbox"][3]+2.5*ctx["h"]]
                if abaixo:
                    # Inicio do trecho inferior; inclui mudanca de desenho local.
                    novos.extend(abaixo[:3])
        novos = list(dict.fromkeys(v for v in novos if v != u))
        extras[u] = novos
        for k in KS:
            enriquecidos[k][u] = list(dict.fromkeys(base[k][u][:-1]+novos))+[None]
    return base, enriquecidos, extras


def matriz_features(ctx, cand, extras):
    """Features automaticas vetorizadas; nao recebe referencia nem particao."""
    ids = ctx["entrada"]
    n = len(ids)
    indice = {u: i for i, u in enumerate(ids)}
    W, H = (max(.1, ctx["auto"]["dimensions"][k]) for k in ("width", "height"))
    h = max(.1, ctx["h"])
    nodes = np.zeros((n+1, len(NO)), dtype=np.float32)
    bb = np.zeros((n+1, 4), dtype=np.float32)
    cols = np.full(n+1, -1, dtype=np.int32)
    ranks = np.full(n+1, n, dtype=np.int32)
    abaixo = np.full(n+1, n, dtype=np.int32)
    sucessor = np.full(n+1, n, dtype=np.int32)
    for i, uid in enumerate(ids):
        u = ctx["mapa"][uid]
        ba = u["bbox"]
        bb[i] = ba
        cols[i] = ctx["col"][uid]
        ranks[i] = ctx["rank_regra"][uid]
        sucessor[i] = indice.get(ctx["regra"][uid], n)
        estilo = c.estilo(ctx, uid)
        texto = u["text"].strip()
        letra = next((ch for ch in texto if ch.isalpha()), "")
        margem = ctx["margem"].get(uid)
        tipo = c.tipo_unidade(u)
        # Usa recorrencia so se ja vier no dado automatico congelado.
        repeticao = u.get("repeticao_entre_paginas")
        pos = ctx["pos"].get(uid, .5)
        nodes[i] = [(ba[0]+ba[2])/2/W, (ba[1]+ba[3])/2/H,
                    (ba[2]-ba[0])/W, (ba[3]-ba[1])/H,
                    cols[i], ranks[i]/max(1, n-1), pos, uid in ctx["pontes"],
                    margem == "topo", margem == "rodape", margem == "marca",
                    tipo == "texto", tipo == "tabela", tipo == "imagem", *estilo,
                    bool(letra) and letra.islower(), math.log1p(len(texto)),
                    pos >= .65 or ctx["regra"][uid] is None or
                    ctx["col"].get(ctx["regra"][uid]) != cols[i],
                    float(repeticao or 0), repeticao is not None]
        possiveis = [v for v in ids if v != uid and ctx["col"][v] == cols[i] and
                     c.cy(ctx["mapa"][v]) > c.cy(u)+.25*h]
        if possiveis:
            v = min(possiveis, key=lambda v: (c.cy(ctx["mapa"][v])-c.cy(u),
                                           abs(c.cx(ctx["mapa"][v])-c.cx(u))))
            abaixo[i] = indice[v]
    arestas = [(u, v) for u in ids for v in cand[u]]
    ii = np.array([indice[u] for u, _ in arestas], dtype=np.int32)
    jj = np.array([indice.get(v, n) for _, v in arestas], dtype=np.int32)
    fin = jj == n
    real = ~fin
    a, z = bb[ii], bb[jj]
    dx = ((z[:, 0]+z[:, 2])-(a[:, 0]+a[:, 2]))/2
    dy = ((z[:, 1]+z[:, 3])-(a[:, 1]+a[:, 3]))/2
    norm = lambda x: np.clip(x/h, -100, 100)*real
    inter = np.maximum(0, np.minimum(a[:, 2], z[:, 2])-np.maximum(a[:, 0], z[:, 0]))
    den = np.maximum(1., np.minimum(a[:, 2]-a[:, 0], z[:, 2]-z[:, 0]))
    rr = np.array([r for u in ids for r in range(len(cand[u]))], dtype=np.float32)
    tam = np.array([len(cand[u])-1 for u, _ in arestas], dtype=np.float32)
    es = {u: set(vs) for u, vs in extras.items()}
    par = np.column_stack([fin, dx/W*real, dy/H*real, norm(dx), norm(dy),
         np.hypot(dx/W, dy/H)*real, norm(np.hypot(dx, dy)), norm(z[:, 1]-a[:, 3]),
         inter/den*real, norm(z[:, 0]-a[:, 0]), (cols[ii] == cols[jj])*real,
         (cols[jj]-cols[ii])*real, (ranks[jj]-ranks[ii])/max(1, n-1),
         jj == sucessor[ii], (jj == abaixo[ii])*real, rr, rr/np.maximum(1, tam),
         [v in es[u] for u, v in arestas]])
    X = np.column_stack([nodes[ii], nodes[jj], par]).astype(np.float32)
    exigir(X.shape == (len(arestas), len(FEATURES)) and np.isfinite(X).all(), "Features invalidas")
    return X, arestas


def predicoes_salvas(co):
    out = {}
    for m in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
        path = b.OUT / "pred" / f"{m}__linhas__{co}.jsonl"
        if path.exists():
            rows = list(o.linhas_seguras(path))
            out[m] = {r["page_id"]: r["ordem"] for r in rows}
            exigir(len(out[m]) == len(rows), "Predicao salva duplicada")
    return out


def preparar_pagina(obj, p):
    ctx = c.contexto(p, obj["palavras"])
    _, _, trs, _ = c.preparar_avaliacao(obj, p, ctx)
    q = b.referencia(obj, p)
    return ctx, trs, q


def diagnosticar(co, obj, p, salvos):
    pid = p["page_id"]
    path = EXEC / "diagnostico" / co / (e.ac.chave(pid)+".json")
    salvo = carregar(path)
    if salvo:
        return salvo
    inicio = time.perf_counter()
    ctx, trs, q = preparar_pagina(obj, p)
    base, cand, _ = candidatos(ctx)
    resultados = {"regra": o.avaliar_ordem(obj, p, ctx, ctx["ordem"], trs, q)}
    for m in ("regra_colunas", "regra_reordena", "layoutreader_pronto"):
        ordem = salvos.get(m, {}).get(pid)
        if ordem is not None:
            if m == "regra_colunas":
                exigir(ordem == ctx["ordem"], "Regra salva divergiu da ancora")
            else:
                resultados[m] = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
    if len(ctx["cs"]) > 67:
        resultados["hibrido67"] = resultados["regra"]
    elif "layoutreader_pronto" in resultados:
        resultados["hibrido67"] = resultados["layoutreader_pronto"]
    row = {"page_id": pid, "uf": obj["uf"], "unidades": len(ctx["cs"]),
           "resultados": resultados, "recall": {}, "segundos": 0}
    for k in KS:
        row["recall"][str(k)] = {"e002": o.auditoria_candidatos(trs, base[k])["classes"],
             "extra": o.auditoria_candidatos(trs, cand[k])["classes"],
             "media_candidatos": statistics.mean(len(v)-1 for v in cand[k].values())}
    row["segundos"] = time.perf_counter()-inicio
    gravar(path, row)
    return row


def preparar_treino():
    registros = []
    for i, (obj, p, sig) in enumerate(paginas_treino(), 1):
        vigiar()
        path = EXEC / "pares" / (e.ac.chave(p["page_id"])+".npz")
        meta_path = path.with_suffix(".json")
        meta = carregar(meta_path)
        if not meta or not path.exists():
            inicio = time.perf_counter()
            ctx = c.contexto(p, obj["palavras"])
            _, cand, extras = candidatos(ctx)
            X, edges = matriz_features(ctx, cand[32], extras)
            # Exatamente a supervisao de fronteiras verificaveis do corretor.
            alvos, causas = c.alvos_silver(obj, ctx)
            valido = np.array([u in alvos for u, _ in edges])
            y = np.array([u in alvos and alvos[u] == v for u, v in edges], dtype=np.uint8)
            salvar_npz(path, X=X[valido], y=y[valido])
            meta = {"page_id": p["page_id"], "uf": p["uf"], "assinatura_pagina": sig,
                    "arquivo": path.relative_to(EXEC).as_posix(), "sha256": c.sha(path),
                    "pares": int(valido.sum()), "positivos": int(y[valido].sum()),
                    "fontes": len(alvos), "fontes_ouro_fora_candidatos":
                        sum(v not in cand[32][u] for u, v in alvos.items()),
                    "exclusoes_rotulos": causas, "segundos": time.perf_counter()-inicio}
            gravar(meta_path, meta)
        exigir(meta["assinatura_pagina"] == sig and c.sha(path) == meta["sha256"], "Cache de pares mudou")
        registros.append(meta)
        if i % 20 == 0 or i == 1:
            print(f"Features de treino: {i}/3140 paginas", flush=True)
            gravar(EXEC / "progresso_treino.json", {"concluidas": i, "pares": sum(r["pares"] for r in registros)})
    gravar(EXEC / "inventario_treino.json", registros)
    return registros


def matrizes(registros):
    """Um mmap por veiculo; montagem retoma pela ultima pagina copiada."""
    out = {}
    for uf in sorted({r["uf"] for r in registros}):
        rs = [r for r in registros if r["uf"] == uf]
        n = sum(r["pares"] for r in rs)
        xp, yp = EXEC / "matrizes" / (uf+"_X.npy"), EXEC / "matrizes" / (uf+"_y.npy")
        mp = xp.with_suffix(".json")
        estado = carregar(mp) or {"paginas": 0, "offset": 0}
        exigir(estado["paginas"] <= len(rs), "Matriz incompativel")
        for pp in (xp, yp):
            destino(pp)
        modo = "r+" if xp.exists() and yp.exists() and mp.exists() else "w+"
        if modo == "w+":
            estado = {"paginas": 0, "offset": 0}
        X = np.lib.format.open_memmap(xp, mode=modo, dtype=np.float32, shape=(n, len(FEATURES)))
        y = np.lib.format.open_memmap(yp, mode=modo, dtype=np.uint8, shape=(n,))
        for i, r in enumerate(rs):
            if i < estado["paginas"]:
                continue
            vigiar()
            lo, hi = estado["offset"], estado["offset"]+r["pares"]
            with np.load(EXEC / r["arquivo"], allow_pickle=False) as d:
                X[lo:hi], y[lo:hi] = d["X"], d["y"]
            X.flush()
            y.flush()
            estado = {"paginas": i+1, "offset": hi}
            gravar(mp, estado)
        exigir(estado["offset"] == n, "Matriz incompleta")
        del X, y
        out[uf] = {"X": xp, "y": yp, "n": n}
    return out


def parametros(hiper):
    return {"objective": "binary", "metric": "binary_logloss", "verbosity": -1,
            "device_type": "cpu", "num_threads": 4, "deterministic": True,
            "force_col_wise": True, "seed": SEMENTE, "data_random_seed": SEMENTE,
            "feature_fraction_seed": SEMENTE, "bagging_seed": SEMENTE,
            "learning_rate": .08, "max_bin": 31, "histogram_pool_size": 32,
            "bin_construct_sample_cnt": 20000,
            "feature_pre_filter": False, **hiper}


def ler_lote(path, item, dtype=None):
    """Copia somente o lote e fecha o mmap para nao acumular paginas em RSS."""
    a = np.load(path, mmap_mode="r", allow_pickle=False)
    try:
        return np.array(a[item], dtype=dtype, copy=True)
    finally:
        a._mmap.close()


def obrigatorios(X, y):
    # O rank da feature e baseado em zero: preserva literalmente rank <= 4.
    return (y == 1) | (X[:, FEATURES.index("rank_candidato")] <= AMOSTRAGEM["rank_max"])


def matrizes_amostradas(mats):
    """Mantem positivos/dificeis e sorteia exatamente o orcamento restante.

    Sorteio uniforme sem reposicao entre TODOS os negativos restantes, por
    hipergeometrica de lotes: equivale a amostrar a populacao inteira, sem
    alocar indices dela em RAM. A mesma RNG 7 e repetida na retomada.
    """
    plano_path = EXEC / "amostragem.json"
    plano = carregar(plano_path)
    lote = 16384
    if not plano:
        contagens = {}
        for uf, mat in sorted(mats.items()):
            fixos = positivos = 0
            for lo in range(0, mat["n"], lote):
                vigiar()
                sl = slice(lo, min(mat["n"], lo+lote))
                X, y = ler_lote(mat["X"], sl), ler_lote(mat["y"], sl)
                fixos += int(obrigatorios(X, y).sum())
                positivos += int(y.sum())
            contagens[uf] = {"originais": mat["n"], "obrigatorios": fixos, "positivos": positivos,
                              "restantes": mat["n"]-fixos}
        fixos = sum(z["obrigatorios"] for z in contagens.values())
        restantes = sum(z["restantes"] for z in contagens.values())
        exigir(fixos <= AMOSTRAGEM["max_pares"], "Positivos+dificeis excedem 4 milhoes; nao descartar silenciosamente")
        slots = min(restantes, AMOSTRAGEM["max_pares"]-fixos)
        plano = {**AMOSTRAGEM, "veiculos": contagens, "obrigatorios": fixos,
                 "negativos_restantes": restantes, "negativos_sorteados": slots,
                 "pares_amostrados": fixos+slots, "fracao_restantes": slots/max(1, restantes),
                 "correcao": "Sem correcao analitica: selecao de hiperparametros e Platt em OOF completo nao amostrado"}
        gravar(plano_path, plano)
    print("Amostragem: "+json.dumps(plano, ensure_ascii=False), flush=True)
    rng = np.random.default_rng(AMOSTRAGEM["semente"])
    faltam, populacao = plano["negativos_sorteados"], plano["negativos_restantes"]
    out = {}
    for uf, mat in sorted(mats.items()):
        # Indices por veiculo: poucos MB. Repetir o sorteio garante a mesma
        # sequencia RNG mesmo se alguns veiculos ja estiverem prontos.
        partes = []
        for lo in range(0, mat["n"], lote):
            vigiar()
            sl = slice(lo, min(mat["n"], lo+lote))
            X, y = ler_lote(mat["X"], sl), ler_lote(mat["y"], sl)
            manter = obrigatorios(X, y)
            candidatos = np.flatnonzero(~manter)
            m = len(candidatos)
            quantidade = int(rng.hypergeometric(faltam, populacao-faltam, m)) if m else 0
            if quantidade:
                manter[rng.choice(candidatos, size=quantidade, replace=False)] = True
            partes.append(np.flatnonzero(manter).astype(np.int32)+lo)
            faltam -= quantidade
            populacao -= m
        indices = np.concatenate(partes)
        n = len(indices)
        xp = EXEC / "matrizes_amostradas" / (uf+"_X.npy")
        yp = xp.with_name(uf+"_y.npy")
        mp = xp.with_suffix(".json")
        sig = c.digest([plano, uf, hashlib.sha256(indices.tobytes()).hexdigest()])
        estado = carregar(mp) or {"offset": 0, "assinatura": sig}
        exigir(estado["assinatura"] == sig, "Amostragem nao deterministica")
        exigir(not estado["offset"] or xp.exists() and yp.exists(), "Matriz amostrada sumiu")
        if not xp.exists() or not yp.exists():
            for path, shape, dtype in ((xp, (n, len(FEATURES)), np.float32), (yp, (n,), np.uint8)):
                a = np.lib.format.open_memmap(destino(path), mode="w+", dtype=dtype, shape=shape)
                a.flush()
                a._mmap.close()
        for lo in range(estado["offset"], n, lote):
            vigiar()
            hi = min(n, lo+lote)
            for path, fonte in ((xp, mat["X"]), (yp, mat["y"])):
                vals = ler_lote(fonte, indices[lo:hi])
                a = np.load(path, mmap_mode="r+", allow_pickle=False)
                a[lo:hi] = vals
                a.flush()
                a._mmap.close()
            estado.update(offset=hi)
            gravar(mp, estado)
        out[uf] = {"X": xp, "y": yp, "n": n}
        plano["veiculos"][uf]["amostrados"] = n
        print(f"Matriz amostrada {uf}: {n}/{mat['n']} pares", flush=True)
    exigir(faltam == populacao == 0 and sum(m["n"] for m in out.values()) == plano["pares_amostrados"],
           "Amostragem excedeu o orcamento ou perdeu pares")
    gravar(EXEC / "amostragem_resultado.json", plano)
    return out, plano


def dataset(lgb, mats, ufs):
    # API oficial Sequence: amostragem e leitura em lotes; nunca empilha corpus.
    class Mapeada(lgb.Sequence):
        batch_size = 8192
        def __init__(self, path):
            self.path = path
            a = np.load(path, mmap_mode="r", allow_pickle=False)
            self.n = len(a)
            a._mmap.close()
            self.inicio, self.bloco = -1, None
        def __len__(self):
            return self.n
        def __getitem__(self, item):
            if isinstance(item, (int, np.integer)):
                lo = int(item)//self.batch_size*self.batch_size
                if lo != self.inicio:
                    self.bloco = ler_lote(self.path, slice(lo, min(lo+self.batch_size, self.n)), np.float64)
                    self.inicio = lo
                return self.bloco[int(item)-lo]
            return ler_lote(self.path, item, np.float64)
    class DatasetEmLotes(lgb.Dataset):
        # LightGBM constroi Dataset a partir de Sequence, mas init_model tenta
        # prever diretamente sobre a lista de Sequence. Adapta somente essa
        # leitura de init_score; as arvores e a perda continuam no LightGBM.
        def _set_init_score_by_predictor(self, predictor, data, used_indices):
            if predictor is None or not isinstance(data, list):
                return super()._set_init_score_by_predictor(predictor, data, used_indices)
            exigir(used_indices is None and all(isinstance(s, lgb.Sequence) for s in data),
                   "Retomada exige sequencias completas, sem subset implicito")
            score = np.empty(sum(len(s) for s in data), dtype=np.float64)
            offset = 0
            for seq in data:
                for lo in range(0, len(seq), seq.batch_size):
                    vigiar()
                    hi = min(lo+seq.batch_size, len(seq))
                    score[offset+lo:offset+hi] = predictor.predict(seq[lo:hi], raw_score=True)
                offset += len(seq)
            self.set_init_score(score)
            return self
    sequencias = [Mapeada(mats[uf]["X"]) for uf in ufs]
    labels = np.concatenate([np.load(mats[uf]["y"], mmap_mode="r") for uf in ufs])
    return DatasetEmLotes(sequencias, label=labels, feature_name=list(FEATURES),
                          params=parametros(HIPERS[0]), free_raw_data=True)


def ajustar_modelo(lgb, ds, hiper, path, arvores):
    inicio = time.perf_counter()
    anterior = carregar(path.with_suffix(".json")) or {"segundos": 0}
    modelo = lgb.Booster(model_file=str(path)) if path.exists() else None
    feitas = modelo.current_iteration() if modelo else 0
    exigir(feitas <= arvores, "Checkpoint tem mais arvores que o alvo")
    if feitas == arvores or anterior.get("concluido"):
        return modelo
    def persistir(model, concluido=False):
        tmp = destino(path).with_suffix(".txt.tmp")
        model.save_model(str(tmp))
        c.substituir(tmp, path)
        gravar(path.with_suffix(".json"), {"arvores": model.current_iteration(), "concluido": concluido,
               "memoria": medir_memoria(),
               "segundos": anterior["segundos"]+time.perf_counter()-inicio})
        print(f"Treino {path.stem}: {model.current_iteration()}/{arvores} arvores", flush=True)
    def checkpoint(env):
        vigiar()
        if (env.iteration+1) % 20 == 0:
            persistir(env.model)
            vigiar()
    checkpoint.order = 50
    checkpoint.before_iteration = False
    vigiar()
    modelo = lgb.train(parametros(hiper), ds, num_boost_round=arvores-feitas,
                       init_model=modelo, keep_training_booster=True, callbacks=[checkpoint])
    persistir(modelo, True)
    modelo.free_dataset()
    return modelo


def loss_veiculo(modelo, mat, arvores, salvar=None):
    y = ler_lote(mat["y"], slice(None))
    total = 0.
    scores = np.empty(len(y), dtype=np.float32) if salvar is not None else None
    for lo in range(0, len(y), 65536):
        vigiar()
        hi = min(lo+65536, len(y))
        X = ler_lote(mat["X"], slice(lo, hi))
        z = modelo.predict(X, num_iteration=arvores, raw_score=True, num_threads=4)
        yy = y[lo:hi]
        total += float(np.sum(np.logaddexp(0., z)-yy*z))
        if scores is not None:
            scores[lo:hi] = z
    if salvar is not None:
        salvar_npz(salvar, z=scores, y=np.asarray(y))
    return total/max(1, len(y))


def calibrar(paths):
    """Platt em predicoes fora de veiculo; pesos iguais entre veiculos."""
    def objetivo(ab):
        vigiar()
        perda, grad = 0., np.zeros(2)
        for path in paths:
            with np.load(path, allow_pickle=False) as d:
                z, y = d["z"].astype(float), d["y"].astype(float)
            v = ab[0]*z+ab[1]
            erro = expit(v)-y
            perda += float(np.mean(np.logaddexp(0., v)-y*v))/len(paths)
            grad += np.array([np.mean(erro*z), np.mean(erro)])/len(paths)
        return perda, grad
    sol = minimize(objetivo, np.array([1., 0.]), jac=True, method="L-BFGS-B",
                   bounds=((.01, 10.), (-10., 10.)), options={"maxiter": 100, "ftol": 1e-10})
    exigir(sol.success and np.isfinite(sol.x).all(), "Calibracao nao convergiu")
    return {"a": float(sol.x[0]), "b": float(sol.x[1]), "logloss_macro": float(sol.fun),
            "tipo": "Platt OOF por veiculo; transferida ao refit completo"}


def treinar(lgb, registros):
    info_path = EXEC / "modelo.json"
    info = carregar(info_path)
    if info and info.get("concluido"):
        exigir(c.sha(EXEC / "modelo.txt") == info["sha256"], "Modelo mudou")
        return lgb.Booster(model_file=str(EXEC / "modelo.txt")), info
    completas = matrizes(registros)
    mats, amostragem = matrizes_amostradas(completas)
    ufs = sorted(mats)
    # Triplas deterministicamente agrupadas; nenhuma pagina de RN/humana aqui.
    folds = [ufs[i::3] for i in range(3)]
    resultados = []
    for hi, hiper in enumerate(HIPERS):
        por_arvores = {a: {} for a in ARVORES}
        for fi, validas in enumerate(folds):
            treino = [uf for uf in ufs if uf not in validas]
            exigir(not set(treino) & set(validas), "Veiculo nos dois lados do fold")
            path = EXEC / "modelos_cv" / f"h{hi}_fold{fi}.txt"
            resumo_path = path.with_suffix(".avaliacao.json")
            aval = carregar(resumo_path)
            if not aval:
                ds = dataset(lgb, mats, treino)
                modelo = ajustar_modelo(lgb, ds, hiper, path, max(ARVORES))
                del ds
                gc.collect()
                aval = {str(a): {uf: loss_veiculo(modelo, completas[uf], a) for uf in validas}
                        for a in ARVORES}
                gravar(resumo_path, aval)
                del modelo
                gc.collect()
            for a in ARVORES:
                por_arvores[a].update(aval[str(a)])
        for a in ARVORES:
            resultados.append({"hiper": hi, "arvores": a, "por_veiculo": por_arvores[a],
                               "logloss_macro": statistics.mean(por_arvores[a].values())})
    escolha = min(resultados, key=lambda r: (r["logloss_macro"], r["arvores"], r["hiper"]))
    gravar(EXEC / "selecao_hiperparametros.json", {"escolha": escolha, "alternativas": resultados,
           "folds_validacao": folds, "criterio": "logloss media por veiculo dentro do treino"})
    paths_oof = []
    for fi, validas in enumerate(folds):
        model = lgb.Booster(model_file=str(EXEC / "modelos_cv" / f"h{escolha['hiper']}_fold{fi}.txt"))
        for uf in validas:
            path = EXEC / "calibracao" / (uf+".npz")
            if not path.exists():
                loss_veiculo(model, completas[uf], escolha["arvores"], path)
            paths_oof.append(path)
        del model
    cal = calibrar(paths_oof)
    gravar(EXEC / "calibracao.json", cal)
    ds = dataset(lgb, mats, ufs)
    modelo = ajustar_modelo(lgb, ds, HIPERS[escolha["hiper"]], EXEC / "modelo.txt", escolha["arvores"])
    tempos = [carregar(p)["segundos"] for p in (EXEC / "modelos_cv").glob("*.json")
              if p.name.endswith(".json") and not p.name.endswith(".avaliacao.json")]
    tempos.append(carregar(EXEC / "modelo.json")["segundos"])
    info = {"concluido": True, "lightgbm": lgb.__version__, "escolha": escolha, "calibracao": cal,
            "sha256": c.sha(EXEC / "modelo.txt"), "treino_paginas": len(registros),
            "pares": sum(r["pares"] for r in registros), "positivos": sum(r["positivos"] for r in registros),
            "amostragem": amostragem, "memoria_treino": medir_memoria(),
            "features_segundos": sum(r["segundos"] for r in registros), "treino_segundos": sum(tempos),
            "importancias_gain": dict(zip(FEATURES, modelo.feature_importance(importance_type="gain").tolist()))}
    gravar(info_path, info)
    del ds
    gc.collect()
    return modelo, info


def configuracoes():
    return [{"K": k, "decoder": d, "limiar": t, "restricao_coluna": col}
            for k in KS for d in DECODERS for t in LIMIARES for col in (False, True)]


def nome_cfg(cfg):
    return (f"grafo_K{cfg['K']}_{cfg['decoder']}_t{cfg['limiar']:.2f}"+
            ("_coluna" if cfg["restricao_coluna"] else ""))


def decodificar(ctx, cand, probabilidades, cfg):
    scores = {}
    for u, vs in cand.items():
        scores[u] = {}
        for v in vs:
            prob = probabilidades[(u, v)]
            if v is not None:
                if prob < cfg["limiar"]:
                    continue
                if (cfg["restricao_coluna"] and ctx["col"][v] < ctx["col"][u] and
                        u not in ctx["margem"] and v not in ctx["margem"]):
                    continue
            scores[u][v] = prob
        exigir(None in scores[u], "FIM explicito ausente")
    return DECODERS[cfg["decoder"]](ctx["ordem"], scores)


def inferir(co, obj, p, modelo, info, cfgs, diagnostico):
    path = EXEC / "inferencia" / co / (e.ac.chave(p["page_id"])+".json")
    row = carregar(path) or {"page_id": p["page_id"], "uf": obj["uf"],
           "resultados": dict(diagnostico["resultados"]), "tempos": {}}
    pendentes = [cfg for cfg in cfgs if nome_cfg(cfg) not in row["resultados"]]
    if not pendentes:
        return row
    inicio = time.perf_counter()
    ctx, trs, q = preparar_pagina(obj, p)
    _, cand, extras = candidatos(ctx)
    X, edges = matriz_features(ctx, cand[32], extras)
    cal = info["calibracao"]
    z = modelo.predict(X, raw_score=True, num_threads=4)
    probs = dict(zip(edges, expit(cal["a"]*z+cal["b"]).tolist()))
    comum = time.perf_counter()-inicio
    por_ordem = {tuple(r["ordem"]): r for r in row["resultados"].values()}
    for cfg in pendentes:
        vigiar()
        nome = nome_cfg(cfg)
        t0 = time.perf_counter()
        ordem = decodificar(ctx, cand[cfg["K"]], probs, cfg)
        ms = time.perf_counter()-t0
        if tuple(ordem) not in por_ordem:
            por_ordem[tuple(ordem)] = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
        row["resultados"][nome] = por_ordem[tuple(ordem)]
        row["tempos"][nome] = {"comum_segundos": comum, "decoder_segundos": ms}
        gravar(path, row)
    return row


def selecionar(dados):
    cfgs = configuracoes()
    alternativas = []
    for cfg in cfgs:
        nome = nome_cfg(cfg)
        medias = {co: {m: statistics.mean(r["resultados"][nome]["metricas"][m] for r in dados[co])
                       for m in ("quebras", "tau")} for co in AJUSTE}
        alternativas.append({"config": cfg, "metodo": nome, "bancadas": medias,
               "quebras": statistics.mean(z["quebras"] for z in medias.values()),
               "tau": statistics.mean(z["tau"] for z in medias.values())})
    melhor = min(alternativas, key=lambda x: (x["quebras"], -x["tau"], x["metodo"]))
    regra = statistics.mean(statistics.mean(r["resultados"]["regra"]["metricas"]["quebras"]
                for r in dados[co]) for co in AJUSTE)
    escolha = {**melhor, "regra_ajuste": regra, "reducao_ajuste": 1-melhor["quebras"]/regra,
               "criterio": "media v4/RN com peso igual; desempate tau e nome", "congelado": True,
               "alternativas": alternativas, "manifesto": c.digest(MANIFESTO)}
    path = EXEC / "selecao_congelada.json"
    anterior = carregar(path)
    exigir(not anterior or c.digest(anterior) == c.digest(escolha), "Selecao congelada mudou")
    gravar(path, escolha)
    return escolha


def resumir(rows, nomes):
    resumo = {}
    for nome in nomes:
        rs = [r for r in rows if nome in r["resultados"]]
        if not rs:
            resumo[nome] = {"n": 0, "completo": False}
            continue
        W = b.PESOS_CLUSTER(rs)
        grupo = {"n": len(rs), "completo": len(rs) == len(rows), "metricas": {}, "contrastes": {}, "classes": {}}
        for k in METRICAS:
            grupo["metricas"][k] = e.media_ic([r["resultados"][nome]["metricas"][k] for r in rs], W)
        for base in ("regra", "hibrido67"):
            rr = [r for r in rs if base in r["resultados"]]
            testes = {}
            for k in METRICAS:
                ds = [(r["resultados"][nome]["metricas"][k]-r["resultados"][base]["metricas"][k])
                       if r["resultados"][nome]["metricas"][k] is not None and
                          r["resultados"][base]["metricas"][k] is not None else None for r in rr]
                if not rr:
                    continue
                ufs = sorted({r["uf"] for r in rr})
                por = {uf: o.media([d for r, d in zip(rr, ds) if r["uf"] == uf]) for uf in ufs}
                sinal = -1 if k in ("quebras", "quebras_mil") else 1
                testes[k] = {**e.media_ic(ds, b.PESOS_CLUSTER(rr)), "por_veiculo": por,
                     "wilcoxon_veiculo": e.pratt([d for d in por.values() if d is not None]),
                     "melhor": sum(d is not None and sinal*d > 1e-12 for d in ds),
                     "igual": sum(d is not None and abs(d) <= 1e-12 for d in ds),
                     "pior": sum(d is not None and sinal*d < -1e-12 for d in ds)}
            grupo["contrastes"][base] = {"n_pareado": len(rr), "completo": len(rr) == len(rows), "metricas": testes}
        for tipo in c.TIPOS:
            soma = collections.Counter()
            for r in rs:
                soma.update(r["resultados"][nome]["classes"][tipo])
            ds = [r["resultados"][nome]["classes"][tipo]["quebras"]-
                  r["resultados"]["regra"]["classes"][tipo]["quebras"] for r in rs]
            por = [statistics.mean(d for r, d in zip(rs, ds) if r["uf"] == uf)
                   for uf in sorted({r["uf"] for r in rs})]
            grupo["classes"][tipo] = {**soma, "quebras_pagina": soma["quebras"]/len(rs),
                    "delta": e.media_ic(ds, W), "wilcoxon_veiculo": e.pratt(por)}
        grupo["cobertura"] = min(r["resultados"][nome]["cobertura_palavras"] for r in rs)
        resumo[nome] = grupo
    return resumo


def relatorio(estado):
    an, escolha = estado["ancora"], estado.get("escolha")
    completo = estado["completo"]
    selecionado = escolha["metodo"] if escolha else "selecionado"
    regra_ajuste = escolha["regra_ajuste"] if escolha else None
    veredito = "PENDENTE — execução incompleta; não há veredito GO/NÃO GO"
    criterios = None
    if completo:
        criterios = {"ajuste_reducao_10": escolha["reducao_ajuste"] >= .10}
        for co in EXTERNAS:
            ss = estado["resumos"][co]
            criterios[co+"_hibrido"] = (ss[selecionado]["metricas"]["quebras"]["media"] <=
                                       ss["hibrido67"]["metricas"]["quebras"]["media"])
            criterios[co+"_tau"] = (ss[selecionado]["metricas"]["tau"]["media"] >=
                                    ss["regra"]["metricas"]["tau"]["media"]-.005)
        veredito = "GO" if all(criterios.values()) else "NÃO GO"
    f, ic = o.f, o.ic
    linhas = [f"1. Âncora reproduzida: τ {f(an['tau'], 6)}; {f(an['quebras'], 6)} quebras/página no golden_v4.",
              "2. Veredito do cartão E004: "+veredito+".",
              "3. "+(f"Selecionado {selecionado}; redução de {f(100*escolha['reducao_ajuste'], 2)}% no ajuste v4/RN."
                      if escolha else "Seleção ainda não realizada; externas não avaliadas."),
              "4. "+estado["situacao"],
              "5. CPU, um processo, quatro threads; cobertura integral nas ordens efetivamente medidas.",
              "6. Golden_v3_novo já foi consultado em rodadas anteriores; teste cego não aberto nem avaliado.",
              "", "# E004 — grafo de arestas aprendidas", "", "## Execução e protocolo", "",
              "Este relatório e seu resumo são produzidos pelo script. Caches atômicos, fontes e hashes em `cache/manifesto.json`; o diretório de execução é `"+estado["execucao"]+"`. Nenhum resultado ausente é substituído por estimativa.", "",
              "Régua importada: `corretor_de_transicoes.medir`, via `e002_oraculos.avaliar_ordem`, `bancada_ordenadores` e `erros_ponta_a_ponta`. τ de palavras, quebras por página/1.000 palavras-ouro (denominador da régua existente), fidelidade integral de 12 e sucessor de linhas intactas. Entrada por `ordem_entrada`, random.Random(f'entrada-{page_id}'). Átomos ls3 e expansão interna congelados; nenhuma palavra descartada.", "",
              "Candidatos conservam os K destinos do E002 e FIM privado, adicionando os três primeiros itens das colunas à direita e dos trechos abaixo para fontes do último terço da coluna ou cuja regra sai da coluna. A condição pos≥0,65 e a escala 2,5 alturas são proxies geométricas existentes, fixadas antes da medição. Extras não consomem K. Uma matriz K32+extras treina o classificador; os K menores restringem o mesmo escore e mantêm o rank de candidato do grafo máximo.", "",
              "Features: geometria normalizada pela página/altura, sobreposição, alinhamento esquerdo, primeira abaixo, colunas, posições e sucessor da regra, tipos automáticos, faixa topo/rodapé/marca, pontuação/hífen, maiúscula/minúscula, numeração, comprimentos e rank do candidato. Somente dados automáticos entram nas features. Recorrência só é usada se já vier como `repeticao_entre_paginas`; não são abertos PDFs vizinhos para calculá-la, pois poderiam conter páginas cegas.", "",
              "Supervisão importa `alvos_silver`: apenas fontes/alvos cuja expansão é trecho contíguo verificável do fluxo PDF; as demais são contadas como exclusões, sem impor sucessor por mediana. Todos os demais candidatos são negativos; fontes cujo ouro está fora do grafo mantêm todos os negativos. FIM é positivo só no fim real. Não há pesos de confiança novos: o corpus não fornece três níveis supervisionados; confiança da regra é uma proxy, não certeza do silver.", "",
              "Treino exclusivamente nos shards base+extra usados pelo exportador `treino_noite.json`, deduplicados e conferidos contra 3.140 IDs. Nunca usa RN nem páginas humanas/external/teste cego. Duas configurações (15/31 folhas; mínimo 100 exemplos/folha), checkpoints 40/80/120 árvores, learning rate 0,08, max_bin 31. Mantidos os três folds agrupados somente dentro do treino (máximo duas configurações × três folds). A logloss de seleção e a calibração Platt usam os candidatos OOF COMPLETOS, não amostrados, com peso igual por veículo. Assim a calibração corrige empiricamente a mudança de prevalência e de composição dos negativos, sem aplicar uma correção analítica uniforme que seria inadequada aos negativos difíceis preservados. Depois há refit amostrado nas 3.140 páginas. A transferência dessa calibração ao refit é uma aproximação explicitada, sem recalibrar no ouro humano/RN.", "",
              "Decisão de método autorizada nesta retomada: amostragem exclusivamente no treino, preservando todos os positivos e negativos com a feature rank_candidato ≤ 4 (rank baseado em zero, portanto cinco posições). Os demais negativos são sorteados uniformemente sem reposição, semente 7, até o limite global de quatro milhões de pares. A escolha não depende de resultados de ajuste ou externos. Matrizes originais e caches de features são preservados; novas matrizes amostradas em memmap por veículo. Avaliação e candidatos de inferência permanecem completos.", "",
              "Memória: free_raw_data=True, um Dataset construído implicitamente por chamada de treino/fold e liberado antes da avaliação; leituras em lotes fecham os mapas para evitar acumular páginas residentes. max_bin=31, amostra de construção de bins=20.000 e pool de histogramas=32 MiB. A proteção continua exigindo RAM livre ≥800 MiB e commit livre ≥1.200 MiB; há também limite de RSS de 3.072 MiB. Pico RSS medido pelo sistema operacional (peak_wset), inclusive entre chamadas do vigia.", "",
              "Decodificação reutiliza guloso, matching e max-regret do E002, com probabilidade calibrada e FIM privado. Limiar remove arestas reais abaixo de 0/0,5/0,8/0,95; FIM permanece. Para cada decodificador há variante que veta retorno para coluna anterior, exceto arestas que envolvem margem/cabeçalho. A costura de caminhos continua sendo a do E002; o veto se aplica às arestas do grafo, não garante monotonicidade da sequência costurada.", "",
              "K, decodificador, limiar e veto escolhidos pela média de quebras de golden_v4/RN com peso igual; desempate por τ e nome. O arquivo `selecao_congelada.json` precede a abertura/avaliação das externas. IC95 percentil em 5.000 bootstraps por veículo e Wilcoxon Pratt nas médias dos veículos, importados; caráter exploratório. RN tem um veículo, portanto IC degenerado e p pouco informativo. Não se somam as bancadas sobrepostas.", "",
              "Híbrido 67 e regra_reordena usam somente ordens salvas. RN não tem LayoutReader/reordena salvos; páginas densas permitem híbrido=regra, mas sua média parcial não representa RN e os contrastes indicam o n pareado. Nenhum modelo de GPU é executado para completar lacunas.", ""]
    if criterios:
        linhas += ["Critérios do cartão: "+json.dumps(criterios, ensure_ascii=False)+".", ""]
    info = estado.get("treino")
    mem = estado.get("memoria", {})
    if mem:
        linhas += [f"Pico de RSS desta execução: {f(mem['pico_rss_mb'], 2)} MiB; RSS na publicação: {f(mem['rss_mb'], 2)} MiB. Medição: {mem['medicao']}. Em retomadas, este pico cobre o processo atual; os picos de treino e checkpoints são preservados separadamente.", ""]
    if info:
        am = info["amostragem"]
        linhas += [f"Amostragem efetiva: {info['pares']} → {am['pares_amostrados']} pares; {am['obrigatorios']} obrigatórios (todos os {info['positivos']} positivos incluídos) e {am['negativos_sorteados']} de {am['negativos_restantes']} negativos restantes. Fração fixa realizada: {f(am['fracao_restantes'], 9)} (semente {am['semente']}); taxa de retenção dos obrigatórios = 1. Correção: {am['correcao']}. Pico RSS até o fim do treino: {f(info['memoria_treino']['pico_rss_mb'], 2)} MiB.", ""]
        linhas += [f"LightGBM {info['lightgbm']}; {info['treino_paginas']} páginas; {info['pares']} pares; {info['positivos']} positivos. Tempo de features {f(info['features_segundos'], 2)} s; treino CV+refit {f(info['treino_segundos'], 2)} s. Semente fixa {SEMENTE} (esta execução não estima variância entre três sementes).", "",
                   "### Importância das features (gain)", "", "| Feature | Gain |", "|---|---:|"]
        for key, val in sorted(info["importancias_gain"].items(), key=lambda kv: -kv[1]):
            linhas.append(f"| {key} | {f(val, 3)} |")
        linhas += [""]
    else:
        linhas += ["Treino e importância gain: indisponíveis; nenhum modelo LightGBM ajustado nesta execução.", ""]
    preparo = estado.get("preparo_treino")
    if preparo:
        linhas += [f"Pares preparados: {preparo['paginas']} páginas, {preparo['veiculos']} veículos, {preparo['pares']} pares e {preparo['positivos']} positivos; {preparo['fontes_ouro_fora_candidatos']} fontes válidas sem ouro no grafo. Tempo registrado de extração: {f(preparo['segundos'], 2)} s. Matrizes mapeadas/cache prontos para retomada.", "",
                   "Exclusões da supervisão silver: `"+json.dumps(preparo["exclusoes"], ensure_ascii=False)+"`.", ""]
    resumo_registro = {}
    for co in COORTES:
        resumo = estado["resumos"].get(co, {})
        linhas += [f"## {co}"+(" — ajuste" if co in AJUSTE else " — externa"), ""]
        if co not in estado["dados"]:
            linhas += ["Não avaliada: aguarda seleção congelada.", ""]
            for m in ("regra", "hibrido67", selecionado):
                resumo_registro[f"{co}/{m}"] = dict(tau=None, quebras=None, sucessor=None)
            continue
        rows = estado["dados"][co]
        linhas += [f"Páginas: {len(rows)}; veículos: {len({r['uf'] for r in rows})}.", "",
                   "| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fidelidade 12 | Sucessor linhas | Cobertura |",
                   "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for m, ss in resumo.items():
            if not ss["n"]:
                linhas.append(f"| {m} | 0 | indisponível | — | — | — | — | — |")
                continue
            mm = ss["metricas"]
            linhas.append(f"| {m}{'' if ss['completo'] else ' (parcial)'} | {ss['n']} | {f(mm['tau']['media'], 6)} | {f(mm['quebras']['media'], 6)} | {f(mm['quebras_mil']['media'])} | {f(mm['fid12']['media'], 6)} | {f(mm['sucessor_linhas']['media'], 6)} | {f(ss['cobertura']*100, 0)}% |")
        for m in ("regra", "hibrido67", selecionado):
            ss = resumo.get(m, {})
            mm = ss.get("metricas", {}) if ss.get("completo") else {}
            resumo_registro[f"{co}/{m}"] = {k: mm.get(mk, {}).get("media") for k, mk in
                                           (("tau", "tau"), ("quebras", "quebras"), ("sucessor", "sucessor_linhas"))}
        linhas += ["", "### Diferenças pareadas", "", "| Método | Base | n | Métrica | Δ [IC95 por veículo] | p veículo | Melhor/igual/pior |",
                   "|---|---|---:|---|---:|---:|---:|"]
        for m, ss in resumo.items():
            for base, contr in ss.get("contrastes", {}).items():
                for k, z in contr["metricas"].items():
                    linhas.append(f"| {m} | {base}{'' if contr['completo'] else ' (parcial)'} | {contr['n_pareado']} | {k} | {ic(z, 6)} | {f(z['wilcoxon_veiculo']['p'], 6)} | {z['melhor']}/{z['igual']}/{z['pior']} |")
        linhas += ["", "### Recall por classe, antes → depois dos extras", "",
                   "| K | Classe | E002 presentes/elegíveis | Recall E002 | Novo presentes/elegíveis | Recall novo | Erros presentes/elegíveis | Internos | Inalcançáveis |",
                   "|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
        for k in KS:
            for tipo in c.TIPOS:
                antes, depois = collections.Counter(), collections.Counter()
                for r in estado["diagnosticos"][co]:
                    antes.update(r["recall"][str(k)]["e002"][tipo])
                    depois.update(r["recall"][str(k)]["extra"][tipo])
                ratio = lambda z: z["presentes"]/z["elegiveis"] if z["elegiveis"] else None
                linhas.append(f"| {k} | {c.ROTULOS[tipo]} | {antes['presentes']}/{antes['elegiveis']} | {f(ratio(antes), 6)} | {depois['presentes']}/{depois['elegiveis']} | {f(ratio(depois), 6)} | {depois['erros_presentes']}/{depois['erros_elegiveis']} | {depois['internos']} | {depois['inalcancaveis']} |")
        linhas += ["", "### Decomposição de quebras e sucessores por classe", "",
                   "| Método | Classe | Quebras/pág | Δ regra [IC95 veículo] | p veículo | Certos/ouro | Reparos/regressões vs regra |",
                   "|---|---|---:|---:|---:|---:|---:|"]
        for m, ss in resumo.items():
            for tipo, z in ss.get("classes", {}).items():
                linhas.append(f"| {m} | {c.ROTULOS[tipo]} | {f(z['quebras_pagina'])} | {ic(z['delta'])} | {f(z['wilcoxon_veiculo']['p'], 6)} | {z['certos']}/{z['ouro']} | {z['reparos']}/{z['regressoes']} |")
        if escolha and all(selecionado in r.get("tempos", {}) for r in rows):
            tempos = [r["tempos"][selecionado] for r in rows]
            linhas += ["", "Tempo médio registrado por página: contexto/features/escore "+
                       f(statistics.mean(t["comum_segundos"] for t in tempos)*1000, 2)+
                       " ms; decoder "+f(statistics.mean(t["decoder_segundos"] for t in tempos)*1000, 2)+" ms. Exclui a régua; contexto inicial também prepara diagnóstico, portanto é limite superior do custo produtivo."]
        linhas += [""]
    if escolha:
        linhas += ["## Varredura no ajuste, sem externas", "",
                   "| K | Decoder | Limiar | Veto coluna | Quebras v4 | Quebras RN | Média | τ médio |",
                   "|---:|---|---:|---|---:|---:|---:|---:|"]
        for a in escolha["alternativas"]:
            cfg = a["config"]
            linhas.append(f"| {cfg['K']} | {cfg['decoder']} | {f(cfg['limiar'], 2)} | {cfg['restricao_coluna']} | {f(a['bancadas']['golden_v4']['quebras'])} | {f(a['bancadas']['validacao_silver']['quebras'])} | {f(a['quebras'])} | {f(a['tau'], 6)} |")
    linhas += ["", "## Limitações e retomada", "",
               "Silver tem ruído sistemático no fluxo do PDF e piso interno aos átomos; negativos difíceis não corrigem rótulos errados. Categorias do E002 são proxies automáticas, sem causalidade humana. Margens correspondem à partição automática da regra. A página inteira entra nas métricas; a decomposição mostra margens/corpo, mas não cria uma segunda referência humana independente de corpo. Não há avaliação confirmatória nem três sementes neste pedido de semente fixa. Uma execução incompleta não satisfaz o critério de abandono/sucesso.", "",
               "Retomar da raiz com `venv/Scripts/python.exe -B orquestracao/analises/e004_grafo.py`. A dependência exigida é `lightgbm` no mesmo venv. `--etapa diagnostico` executa só ajuste e não abre externas. `--max-minutos` interrompe entre páginas/lotes/20 árvores; repetir preserva o resultado concluído. `--conferir` verifica hashes dos caches, o relatório e o JSON sem alterá-los.", ""]
    return "\n".join(linhas), resumo_registro


def publicar(an, diagnosticos, dados, situacao, treino=None, escolha=None, completo=False):
    nomes = ["regra", "hibrido67", "regra_reordena", "layoutreader_pronto"]
    if escolha:
        nomes.append(escolha["metodo"])
    else:
        nomes.append("selecionado")
    estado = {"ancora": an, "diagnosticos": diagnosticos, "dados": dados,
              "memoria": medir_memoria(),
              "situacao": situacao, "treino": treino, "escolha": escolha, "completo": completo,
              "execucao": EXEC.relative_to(OUT).as_posix(), "manifesto": MANIFESTO,
              "resumos": {co: resumir(rs, nomes) for co, rs in dados.items() if rs}}
    registros = carregar(EXEC / "inventario_treino.json")
    if registros:
        exclusoes = collections.Counter()
        for r in registros:
            exclusoes.update(r["exclusoes_rotulos"])
        estado["preparo_treino"] = {"paginas": len(registros), "veiculos": len({r['uf'] for r in registros}),
            "pares": sum(r['pares'] for r in registros), "positivos": sum(r['positivos'] for r in registros),
            "fontes_ouro_fora_candidatos": sum(r['fontes_ouro_fora_candidatos'] for r in registros),
            "segundos": sum(r['segundos'] for r in registros), "exclusoes": dict(exclusoes)}
    texto, resumo = relatorio(estado)
    estado["assinatura_numeros"] = c.digest([estado["resumos"], escolha, resumo])
    gravar(EXEC / "estado.json", estado)
    gravar(OUT / "RELATORIO.md", texto)
    gravar(OUT / "resumo_registro.json", resumo)
    gravar(CACHE / "ultima_execucao.json", {"execucao": EXEC.relative_to(OUT).as_posix(),
           "assinatura_numeros": estado["assinatura_numeros"]})


def conferir():
    pointer = b.ler(CACHE / "ultima_execucao.json")
    path = OUT / pointer["execucao"]
    estado = b.ler(path / "estado.json")
    exigir(c.digest(estado["manifesto"]) == c.digest(MANIFESTO) == c.digest(manifesto()),
           "Fontes/configuracao mudaram")
    for co, rs in estado["dados"].items():
        nomes = list(estado["resumos"][co])
        exigir(c.digest(resumir(rs, nomes)) == c.digest(estado["resumos"][co]), "Resumo divergente")
        for r in rs:
            o.permitido(r["page_id"])
            for z in r["resultados"].values():
                exigir(z["cobertura_palavras"] == 1., "Cobertura divergente")
    texto, resumo = relatorio(estado)
    exigir((OUT / "RELATORIO.md").read_text(encoding="utf-8") == texto, "Relatorio divergente")
    exigir(b.ler(OUT / "resumo_registro.json") == resumo, "Registro divergente")
    exigir(c.digest([estado["resumos"], estado["escolha"], resumo]) == pointer["assinatura_numeros"],
           "Assinatura numerica divergente")
    registros = carregar(path / "inventario_treino.json")
    if registros:
        for r in registros:
            exigir(c.sha(path / r["arquivo"]) == r["sha256"], "Cache de pares divergente")
    print("CONFERE: fontes, resumos, cobertura, relatorio e registro identicos", flush=True)


def autoteste():
    global EXEC
    o.autoteste()
    p = {"page_id": "sintetico/controle.pdf#p0", "dimensions": {"width": 600, "height": 800},
         "bounding_boxes": [{"id": f"u{i}", "bbox": [20+(i//3)*250, 50+(i%3)*30,
                              220+(i//3)*250, 60+(i%3)*30], "ks": [i], "text": str(i), "tipo": "texto"}
                             for i in range(6)]}
    ws = [[str(i), *u["bbox"], 0] for i, u in enumerate(p["bounding_boxes"])]
    ctx = c.contexto(p, ws)
    antes, cand, extras = candidatos(ctx)
    X, edges = matriz_features(ctx, cand[32], extras)
    exigir(len(X) == len(edges) and X.shape[1] == len(FEATURES), "Matriz incorreta")
    exigir(sum(v is None for _, v in edges) == 6, "FIM nao e privado por fonte")
    for k in KS:
        exigir(all(set(antes[k][u]) <= set(cand[k][u]) for u in ctx["entrada"]), "Perdeu candidato E002")
    # Alterar a referencia nao pode alterar features: ela nem e recebida aqui.
    obj = {"page_id": p["page_id"], "uf": "sintetico", "palavras": ws,
           "gt_w": list(range(6)), "referencia_palavras_tipo": "fluxo_pdf_por_palavra"}
    _, trs, q = preparar_pagina(obj, p)
    probs = {(u, v): .99 if ctx["regra"][u] == v else .01 for u, v in edges}
    for cfg in configuracoes():
        ordem = decodificar(ctx, cand[cfg["K"]], probs, cfg)
        med = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
        exigir(med["cobertura_palavras"] == 1., "Decoder perdeu palavras")
    # Exerce o adaptador de retomada sem fingir um treino LightGBM. O stub
    # substitui so o recipiente Dataset; o teste confere fronteiras de lotes.
    class SequenceTeste:
        pass
    class DatasetTeste:
        def __init__(self, data, **kwargs):
            self.data = data
        def set_init_score(self, score):
            self.score = score
    class LGBTeste:
        Sequence, Dataset = SequenceTeste, DatasetTeste
    class PreditorTeste:
        def predict(self, x, raw_score):
            return x[:, 0]+2*x[:, 1]
    mats = {}
    esperados = []
    rng = np.random.default_rng(SEMENTE)
    for uf, n in (("sintetico_a", 8201), ("sintetico_b", 9)):
        X = rng.normal(size=(n, len(FEATURES))).astype(np.float32)
        xp, yp = CACHE / "autoteste" / (uf+"_X.npy"), CACHE / "autoteste" / (uf+"_y.npy")
        X[:, FEATURES.index("rank_candidato")] = np.arange(n) % 16
        ys = (np.arange(n) % 16 == 11).astype(np.uint8)
        for path, a in ((xp, X), (yp, ys)):
            with destino(path).open("wb") as f:
                np.save(f, a, allow_pickle=False)
        mats[uf] = {"X": xp, "y": yp, "n": n}
        esperados.extend(X[:, 0].astype(float)+2*X[:, 1].astype(float))
    ds = dataset(LGBTeste, mats, list(mats))
    ds._set_init_score_by_predictor(PreditorTeste(), ds.data, None)
    exigir(np.allclose(ds.score, esperados), "Retomada trocou offsets entre lotes/veiculos")
    caminhos = []
    for i in range(2):
        z = rng.normal(size=1000)
        y = (rng.random(1000) < expit(.7*z+.2)).astype(np.uint8)
        path = CACHE / "autoteste" / f"platt_{i}.npz"
        salvar_npz(path, z=z, y=y)
        caminhos.append(path)
    cal = calibrar(caminhos)
    exigir(cal["a"] > 0 and math.isfinite(cal["logloss_macro"]), "Platt invalido")
    print(f"Autoteste E004: {len(FEATURES)} features; {len(configuracoes())} configuracoes; cobertura e regua aprovadas", flush=True)
    print("Adaptador de retomada em lotes e calibracao Platt sintetica: aprovados; nao substituem treino LightGBM", flush=True)
    antigo_exec, antigo_limite = EXEC, AMOSTRAGEM["max_pares"]
    try:
        EXEC = CACHE / "autoteste/amostragem_v1"
        AMOSTRAGEM["max_pares"] = 4000
        amats, plano = matrizes_amostradas(mats)
        novos, _ = matrizes_amostradas(mats)
        exigir(sum(m["n"] for m in amats.values()) == 4000, "Orcamento amostrado incorreto")
        for uf in mats:
            y = ler_lote(mats[uf]["y"], slice(None))
            yy = ler_lote(amats[uf]["y"], slice(None))
            exigir(int(y.sum()) == int(yy.sum()), "Amostragem descartou positivo")
            exigir(c.sha(amats[uf]["X"]) == c.sha(novos[uf]["X"]), "Retomada mudou amostra")
        import lightgbm as lgb
        path = EXEC / "smoke.txt"
        # Nova pasta por execucao do autoteste; exercita efetivamente o
        # LightGBM com free_raw_data=True e checkpoint retomado de 2 para 4.
        path = path.with_stem("smoke_"+str(time.time_ns()))
        ds = dataset(lgb, amats, sorted(amats))
        model = ajustar_modelo(lgb, ds, HIPERS[0], path, 2)
        exigir(ds.free_raw_data and ds.data is None, "Dataset nao liberou dados brutos")
        del model, ds
        meta = carregar(path.with_suffix(".json"))
        meta["concluido"] = False
        gravar(path.with_suffix(".json"), meta)
        ds = dataset(lgb, amats, sorted(amats))
        model = ajustar_modelo(lgb, ds, HIPERS[0], path, 4)
        exigir(model.current_iteration() == 4 and ds.data is None, "Retomada LightGBM incorreta")
        print("Amostragem exata, positivos preservados, retomada identica e LightGBM real 2→4 arvores: OK", flush=True)
        del model, ds
    finally:
        EXEC, AMOSTRAGEM["max_pares"] = antigo_exec, antigo_limite


def main():
    global PRAZO, LOCK_SHA, EXEC, MANIFESTO
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--somente-ancora", action="store_true")
    ap.add_argument("--etapa", choices=("tudo", "diagnostico", "preparar-treino"), default="tudo")
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    LOCK_SHA, protegidos = o.ler_lock()
    o.ASSINATURA_LOCK, o.PROTEGIDOS = LOCK_SHA, protegidos
    if args.max_minutos:
        PRAZO = time.monotonic()+args.max_minutos*60
    with trava():
        # Obrigatoriamente antes de qualquer numero experimental novo.
        an = o.ancora()
        if args.autoteste:
            autoteste()
        if args.somente_ancora:
            return 0
        MANIFESTO = manifesto()
        EXEC = CACHE / c.digest(MANIFESTO)
        if args.conferir:
            conferir()
            return 0
        gravar(CACHE / "manifesto.json", MANIFESTO)
        reusar_preparo()
        diagnosticos, dados = {}, {}
        treino, escolha = None, None
        try:
            # Diagnostico somente no ajuste; nenhuma externa antes do congelamento.
            for co in AJUSTE:
                salvos = predicoes_salvas(co)
                diagnosticos[co] = []
                dados[co] = []
                for obj, p in o.paginas(co):
                    vigiar()
                    row = diagnosticar(co, obj, p, salvos)
                    diagnosticos[co].append(row)
                    dados[co].append(row)
                    print(f"Diagnostico {co}: {len(dados[co])} paginas", flush=True)
                publicar(an, diagnosticos, dados, "Diagnóstico do ajuste concluído; treino/seleção pendentes.")
            if args.etapa == "diagnostico":
                publicar(an, diagnosticos, dados, "Etapa solicitada: diagnóstico; treino e externas não executados.")
                return 0
            if args.etapa == "preparar-treino":
                registros = preparo_pronto()
                matrizes(registros)
                publicar(an, diagnosticos, dados,
                    "Dados de treino preparados e conferidos; ajuste LightGBM/seleção/externas pendentes.")
                return 0
            if importlib.util.find_spec("lightgbm") is None:
                publicar(an, diagnosticos, dados,
                    "BLOQUEADO: LightGBM ausente no venv; pip install falhou com rede do terminal indisponível. Nenhum treino, seleção ou teste externo executado.")
                return 2
            import lightgbm as lgb
            registros = preparo_pronto()
            modelo, treino = treinar(lgb, registros)
            for co in AJUSTE:
                dados[co] = []
                diags = {r["page_id"]: r for r in diagnosticos[co]}
                for obj, p in o.paginas(co):
                    vigiar()
                    dados[co].append(inferir(co, obj, p, modelo, treino, configuracoes(), diags[p["page_id"]]))
                    print(f"Varredura {co}: {len(dados[co])} paginas", flush=True)
            escolha = selecionar(dados)
            publicar(an, diagnosticos, dados, "Seleção congelada antes das externas.", treino, escolha)
            for co in EXTERNAS:
                exigir(carregar(EXEC / "selecao_congelada.json") == escolha, "Selecao nao congelada")
                salvos = predicoes_salvas(co)
                diagnosticos[co], dados[co] = [], []
                for obj, p in o.paginas(co):
                    vigiar()
                    diag = diagnosticar(co, obj, p, salvos)
                    diagnosticos[co].append(diag)
                    dados[co].append(inferir(co, obj, p, modelo, treino, [escolha["config"]], diag))
                    print(f"Externa {co}: {len(dados[co])} paginas", flush=True)
                publicar(an, diagnosticos, dados, "Externa concluída sem nova seleção.", treino, escolha)
            exigir(all(all(m in r["resultados"] for m in ("regra", "hibrido67", escolha["metodo"]))
                        for co in EXTERNAS for r in dados[co]), "Comparador externo incompleto")
            publicar(an, diagnosticos, dados, "Execução completa; seleção preservada nas externas.", treino, escolha, True)
            conferir()
        except (TimeoutError, KeyboardInterrupt) as ex:
            publicar(an, diagnosticos, dados, "PARCIAL retomável: "+str(ex), treino, escolha)
            print("Parcial preservado; repetir o comando", flush=True)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
