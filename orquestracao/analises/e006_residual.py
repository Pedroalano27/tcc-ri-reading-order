"""Testa correcao residual E006, importando operacoes E002 e escores E004.

O modelo congelado decide somente ganhos locais sobre o hibrido 67 salvo.
Nenhuma referencia entra na busca. A regua, os sucessores e o bootstrap sao
importados. Cada pagina, escore e passo guloso tem cache atomico retomavel.
Escolhe lambda/M somente no ajuste v4+RN; lacra codigo, fontes e parametros
antes de abrir externas. Nunca abre PDFs, teste cego ou dados do parceiro.

Uso da raiz, CPU/quatro threads/um processo:
  venv/Scripts/python.exe -B orquestracao/analises/e006_residual.py --autoteste --somente-ancora
  ... --etapa ajuste [--predicoes-rn caminho.jsonl]
  ... --etapa tudo --max-minutos 60
  ... --conferir  # somente caches, sem nova inferencia/avaliacao
--gerar-rn completa predicoes RN em CPU, somente se autorizado pelo usuario.
Todas as escritas ficam em resultados/e006_residual/.
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
import collections
import gc
import hashlib
import json
import math
import statistics
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from orquestracao.analises import e002_oraculos as o
from orquestracao.analises import e004_grafo as g
from orquestracao.analises import e014_cadeias as m
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e

c, np = g.c, g.np
OUT = RAIZ / "resultados/e006_residual"
LIMIARES = (0., .5, 1., 2., 4.)
LIMITES = (5, 20, None)
CAND = "e006_residual"
CONTROLES = ("regra", "hibrido67", "regra_reordena", "oraculo_residual")
METODOS = (*CONTROLES, CAND)
EXEC = FONTE = FONTE_ORACULO = None
MODELO = INFO = MAN = None
LOCK_SHA = None
PRAZO = None


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def agora():
    return datetime.now(timezone.utc).isoformat()


def ler(path):
    return b.ler(path) if path.exists() else None


def gravar(path, valor):
    path = path.resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora de E006")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(valor, str):
            f.write(valor)
        else:
            json.dump(valor, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, path)


def vigiar():
    if PRAZO and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; repetir retoma caches")
    exigir(o.ler_lock()[0] == LOCK_SHA, "O lacre cego mudou")
    mem, rss = b.memoria(), g.medir_memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 800 and mem["commit_livre_mb"] >= 1200,
           "Memoria insuficiente; caches preservados: " + str(mem))
    exigir(rss["pico_rss_mb"] <= 3072, "RSS excedeu 3 GiB")


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
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


def nome(lam, limite):
    return f"lambda{lam:g}_M{limite if limite is not None else 'infinito'}"


def iniciar(args):
    """Registra fontes por hash, sem desserializar referencias externas."""
    global EXEC, FONTE, FONTE_ORACULO, INFO, MAN
    FONTE = g.OUT / b.ler(g.CACHE / "ultima_execucao.json")["execucao"]
    INFO = b.ler(FONTE / "modelo.json")
    exigir(INFO["concluido"] and c.sha(FONTE / "modelo.txt") == INFO["sha256"],
           "Modelo E004 ausente/alterado")
    man_o = b.ler(o.OUT / "cache/manifesto.json")
    FONTE_ORACULO = o.OUT / "cache" / man_o["assinatura"]
    paths = {Path(__file__), Path(o.__file__), Path(g.__file__), Path(m.__file__),
             Path(c.__file__), Path(e.__file__), Path(b.__file__), Path(o.lm.__file__),
             FONTE / "modelo.txt", FONTE / "modelo.json", o.OUT / "cache/manifesto.json",
             RAIZ / "data/processed/splits.json"}
    paths.update(b.DEP_PATHS)
    paths.update((RAIZ / "experimentos/cards").glob("E006_*.md"))
    # Hashing binario nao desserializa paginas; so o leitor seguro abre registros.
    paths.update(b.UNIDADES / "bancadas" / (co + ".jsonl") for co in c.HUMANAS)
    splits = b.ler(RAIZ / "data/processed/splits.json")
    for part in ("validacao", "teste"):
        for uf in splits[part]:
            paths.update(b.UNIDADES / "linhas" / (uf + sufixo)
                         for sufixo in (".jsonl", ".palavras.jsonl"))
    for co in o.COORTES:
        for metodo in ("regra_colunas", "layoutreader_pronto", "regra_reordena"):
            p = b.OUT / "pred" / f"{metodo}__linhas__{co}.jsonl"
            if p.exists():
                paths.add(p)
    if args.predicoes_rn:
        pred = Path(args.predicoes_rn).resolve()
        exigir(pred.is_relative_to((RAIZ / "resultados").resolve()),
               "Predicoes RN devem estar em resultados/")
        paths.add(pred)
    # O complemento RN nao muda o modelo nem parametros. Se autorizado,
    # seus pesos tambem ficam identificados antes de qualquer abertura externa.
    if args.gerar_rn:
        from orquestracao.analises import ordem_layoutreader as lr
        paths.update((Path(lr.__file__), lr.MODELO / "config.json",
                      lr.MODELO / "model.safetensors"))
    fontes = {}
    for p in sorted(paths):
        exigir("labelstudio" not in p.as_posix().lower(), "Fonte proibida")
        fontes[p.relative_to(RAIZ).as_posix()] = c.sha(p)
    MAN = {"experimento": "E006", "fontes": fontes, "lock_sha256": LOCK_SHA,
           "modelo_e004": FONTE.relative_to(RAIZ).as_posix(),
           "oraculo_e002": FONTE_ORACULO.relative_to(RAIZ).as_posix(),
           "limiares": LIMIARES, "limites": LIMITES, "threads": 4,
           "processos": 1, "num_workers": 0, "cpu": True, "treino": False,
           "complementar_rn_cpu": args.gerar_rn,
           "predicoes_rn": args.predicoes_rn,
           "escores_fora_do_pool": "features E004; rank=numero de destinos reais; rank relativo=1",
           "selecao": "menor quebra media v4/RN peso igual, tau >= hibrido-0.005 na mesma media; desempate maior tau, menor M, maior lambda"}
    assinatura = c.digest(MAN)
    EXEC = OUT / "cache" / assinatura
    abertura = ler(OUT / "abertura_externas.json")
    exigir(abertura is None or abertura["assinatura"] == assinatura,
           "Externas ja abertas com outro codigo/fontes; proibida nova execucao")
    gravar(EXEC / "manifesto.json", MAN)
    gravar(OUT / "cache/ultima_execucao.json", {"execucao": EXEC.relative_to(OUT).as_posix()})


def pares(ordem):
    """Inclui FIM E004; nao ha modelo de INICIO."""
    return set(zip(ordem, ordem[1:] + [None]))


def bordas_movimento(ordem, i, tam, j):
    """So tres bordas mudam; os indices sao os de mover() do E002."""
    n = len(ordem)
    primeiro, ultimo = ordem[i], ordem[i + tam - 1]
    antes = ordem[i - 1] if i else None
    depois = ordem[i + tam] if i + tam < n else None
    def resto(k):
        return ordem[k if k < i else k + tam] if 0 <= k < n - tam else None
    a, z = resto(j - 1), resto(j)
    antigos = {(a, z), (antes, primeiro), (ultimo, depois)}
    novos = {(antes, depois), (a, primeiro), (ultimo, z)}
    antigos = {edge for edge in antigos if edge[0] is not None}
    novos = {edge for edge in novos if edge[0] is not None}
    return novos - antigos, antigos - novos


class Escores:
    """Avaliacao esparsa de pares com o modelo e Platt congelados do E004.

    Preserva EXATAMENTE os ranks/features do grafo K32+extras para suas arestas.
    Fora desse pool, usa rank terminal (relativo 1), sem marcar como extra.
    Isso e extrapolacao, explicitada no relatorio; nao troca os candidatos das
    operacoes E002, nao inventa probabilidade zero e nao treina outro modelo.
    """
    def __init__(self, co, ctx):
        self.ctx = ctx
        _, todos, self.extras = g.candidatos(ctx)
        self.canonicos = todos[32]
        self.ranks = {u: {v: i for i, v in enumerate(vs)} for u, vs in self.canonicos.items()}
        self.path = EXEC / "escores" / co / (e.ac.chave(ctx["auto"]["page_id"]) + ".json")
        self.valores = {(u, v): s for u, v, s in (ler(self.path) or {}).get("logp", [])}

    def completar(self, edges):
        global MODELO
        faltam = set(edges) - self.valores.keys()
        if not faltam:
            return
        if MODELO is None:
            import lightgbm as lgb
            MODELO = lgb.Booster(model_file=str(FONTE / "modelo.txt"))
            exigir(MODELO.feature_name() == list(g.FEATURES), "Features do modelo divergentes")
        ids = self.ctx["entrada"]
        rank_entrada = {u: i for i, u in enumerate(ids)}
        cand = {u: [] for u in ids}
        for u, v in sorted(faltam, key=lambda edge: (rank_entrada[edge[0]], rank_entrada.get(edge[1], len(ids)))):
            cand[u].append(v)
        # Um lote por fonte evita matrizes quadraticas/densas na RAM.
        for lo in range(0, len(ids), 32):
            vigiar()
            lote = {u: cand[u] if lo <= k < lo + 32 else [] for k, u in enumerate(ids)}
            if not any(lote.values()):
                continue
            X, es = g.matriz_features(self.ctx, lote, self.extras)
            rank = np.array([self.ranks[u].get(v, len(self.canonicos[u])-1) for u, v in es])
            den = np.array([max(1, len(self.canonicos[u])-1) for u, v in es])
            X[:, g.FEATURES.index("rank_candidato")] = rank
            X[:, g.FEATURES.index("rank_candidato_relativo")] = rank / den
            cal = INFO["calibracao"]
            z = MODELO.predict(X, raw_score=True, num_threads=4)
            lp = -np.logaddexp(0., -(cal["a"] * z + cal["b"]))
            exigir(np.isfinite(lp).all() and (lp <= 0).all(), "Log P invalido")
            self.valores.update(zip(es, lp.tolist()))
        gravar(self.path, {"page_id": self.ctx["auto"]["page_id"],
                          "entrada": ids, "logp": [[u, v, s] for (u, v), s in self.valores.items()],
                          "fora_pool": sum(v not in self.ranks[u] for u, v in self.valores)})

    def soma(self, ordem):
        return math.fsum(self.valores[edge] for edge in pares(ordem))


def buscar(co, ctx, inicial, cand, escores, lam, max_ops=None):
    """Trajetoria infinita; M5/M20 sao prefixos exatos da mesma busca."""
    path = EXEC / "busca" / co / e.ac.chave(ctx["auto"]["page_id"]) / (nome(lam, max_ops) + ".json")
    salvo = ler(path) or {"inicial": inicial, "ordem": inicial, "operacoes": [], "concluido": False}
    exigir(salvo["inicial"] == inicial, "Ordem inicial mudou")
    if salvo["concluido"]:
        return salvo
    ordem, historico = list(salvo["ordem"]), salvo["operacoes"]
    vistos = {c.digest(inicial)} | {op["hash_ordem"] for op in historico}
    while True:
        vigiar()
        if max_ops is not None and len(historico) >= max_ops:
            salvo = {"inicial": inicial, "ordem": ordem, "operacoes": historico, "concluido": True}
            gravar(path, salvo)
            return salvo
        ops = list(o.operacoes(ctx, ordem, cand))
        edges = pares(ordem)
        for _, i, tam, j in ops:
            novos, antigos = bordas_movimento(ordem, i, tam, j)
            edges.update(novos | antigos)
        escores.completar(edges)
        melhor, ganho = None, lam
        for k, op in enumerate(ops):
            if k % 5000 == 0:
                vigiar()
            novos, antigos = bordas_movimento(ordem, *op[1:])
            delta = math.fsum([escores.valores[edge] for edge in novos] +
                              [-escores.valores[edge] for edge in antigos])
            if delta > ganho:
                ganho, melhor = delta, op
        if melhor is None:
            salvo = {"inicial": inicial, "ordem": ordem, "operacoes": historico, "concluido": True}
            gravar(path, salvo)
            return salvo
        tipo, i, tam, j = melhor
        nova = o.mover(ordem, i, tam, j)
        exigir(abs(escores.soma(nova) - escores.soma(ordem) - ganho) < 1e-8,
               "Ganho local divergiu da soma completa de log P")
        sh = c.digest(nova)
        exigir(sh not in vistos, "Busca repetiu um estado; ganho numerico invalido")
        vistos.add(sh)
        historico.append({"tipo": tipo, "origem": i, "tamanho": tam, "destino": j,
                          "unidades": ordem[i:i+tam], "ganho_logp": ganho, "hash_ordem": sh})
        ordem = nova
        gravar(path, {"inicial": inicial, "ordem": ordem, "operacoes": historico, "concluido": False})


def prefixo(inicial, busca, limite):
    ordem = list(inicial)
    ops = busca["operacoes"][:limite]
    for op in ops:
        ordem = o.mover(ordem, op["origem"], op["tamanho"], op["destino"])
        exigir(c.digest(ordem) == op["hash_ordem"], "Prefixo nao reproduziu a busca")
    return ordem, ops


def salvos_rn(args, salvos):
    """Completa somente o insumo faltante; nunca ajusta o LayoutReader."""
    if args.predicoes_rn:
        for row in o.linhas_seguras(Path(args.predicoes_rn).resolve()):
            salvos.setdefault("layoutreader_pronto", {})[row["page_id"]] = row.get("ordem", row.get("ordem_pred"))
    lr = None
    faltantes = []
    for obj, p in o.paginas("validacao_silver"):
        pid = p["page_id"]
        if len(p["bounding_boxes"]) > 67 or pid in salvos.get("layoutreader_pronto", {}):
            continue
        path = OUT / "predicoes_rn" / (e.ac.chave(pid) + ".json")
        salvo = ler(path)
        if salvo:
            exigir(salvo["pagina_sha256"] == c.digest(p), "Predicao RN de outra representacao")
        elif args.gerar_rn:
            vigiar()
            if lr is None:
                lr = b.carregar_layoutreader()
            ordem, diag = b.prever(c.automatico(p), obj["palavras"], "layoutreader_pronto", lr)
            salvo = {"page_id": pid, "pagina_sha256": c.digest(p), "ordem": ordem,
                     "diagnostico": diag, "modelo": lr.info, "gerado_em_utc": agora()}
            gravar(path, salvo)
            print("RN CPU: predição salva " + pid, flush=True)
        else:
            faltantes.append(pid)
        if salvo:
            salvos.setdefault("layoutreader_pronto", {})[pid] = salvo["ordem"]
    del lr
    gc.collect()
    exigir(not faltantes, "Faltam predições LayoutReader RN leves: " + str(faltantes) +
           ". Informe --predicoes-rn ou, com autorização, --gerar-rn. Nenhuma externa foi aberta.")
    return salvos


def avaliar_pagina(co, obj, p, salvos, escolha=None):
    path = EXEC / "avaliacao" / co / (e.ac.chave(p["page_id"]) + ".json")
    salvo = ler(path)
    if salvo:
        exigir(salvo["pagina_sha256"] == c.digest([obj, p]), "Pagina do cache mudou")
        return salvo
    t0 = time.perf_counter()
    ctx, trs, q = g.preparar_pagina(obj, p)
    pid = p["page_id"]
    lr = salvos.get("layoutreader_pronto", {}).get(pid)
    exigir(len(ctx["cs"]) > 67 or lr is not None, "Hibrido incompleto: " + pid)
    inicial = ctx["ordem"] if len(ctx["cs"]) > 67 else lr
    ordens = {"regra": ctx["ordem"], "hibrido67": inicial}
    rr = salvos.get("regra_reordena", {}).get(pid)
    if co != "validacao_silver":
        exigir(rr is not None, "Reordenacao restrita ausente")
    if rr is not None:
        ordens["regra_reordena"] = rr
    # Teto diagnostico E002 previamente salvo, com inicio na regra (declarado).
    po = FONTE_ORACULO / co / (hashlib.sha256(pid.encode("utf-8")).hexdigest() + ".json")
    antigo = b.ler(po)
    exigir(antigo["page_id"] == pid and antigo["resultados"]["regra_colunas"]["ordem"] == ctx["ordem"],
           "Oraculo E002 pertence a outra pagina/representacao")
    ordens["oraculo_residual"] = antigo["resultados"]["oraculo_residual"]["ordem"]
    resultados, corpos, hits, por_ordem = {}, {}, {}, {}
    operacoes = {"oraculo_residual": antigo["operacoes"]}
    def medir(nm, ordem):
        exigir(len(ordem) == len(ctx["ordem"]) and set(ordem) == set(ctx["ordem"]), "Permutacao incompleta")
        chave = tuple(ordem)
        if chave not in por_ordem:
            med = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
            corpo = m.avaliar_corpo(q, ctx, ordem)
            seq = [k for u in ordem for k in ctx["exp"][u]]
            hit = o.lm.acertos(q, seq, trs, med["metricas"])
            por_ordem[chave] = med, corpo, hit
        resultados[nm], corpos[nm], hits[nm] = por_ordem[chave]
    for nm, ordem in ordens.items():
        medir(nm, ordem)
    for nm, fonte in (("regra", "regra_colunas"), ("oraculo_residual", "oraculo_residual"),
                      ("hibrido67", "hibrido67"), ("regra_reordena", "regra_reordena")):
        if nm in resultados and fonte in antigo["resultados"]:
            for k in o.METRICAS:
                exigir(abs(resultados[nm]["metricas"][k]-antigo["resultados"][fonte]["metricas"][k]) < 1e-11,
                       "Comparador divergiu do E002: " + nm + "/" + k)
    cand = o.candidatos(ctx)[32]
    escores = Escores(co, ctx)
    configs = [(lam, limite) for lam in LIMIARES for limite in LIMITES] if escolha is None else [
        (escolha["lambda"], escolha["M"])]
    for lam in dict.fromkeys(lam for lam, _ in configs):
        busca = buscar(co, ctx, inicial, cand, escores, lam, escolha["M"] if escolha else None)
        for _, limite in (cfg for cfg in configs if cfg[0] == lam):
            nm = nome(lam, limite) if escolha is None else CAND
            ordem, ops = prefixo(inicial, busca, limite)
            medir(nm, ordem)
            operacoes[nm] = ops
    reparos = {}
    for nm in resultados:
        reparos[nm] = {}
        for base in ("regra", "hibrido67", "regra_reordena"):
            if base in hits:
                reparos[nm][base] = {tipo: {
                    "reparos": sum(new and not old for tr, old, new in zip(trs, hits[base], hits[nm]) if tr["tipo"] == tipo),
                    "regressoes": sum(old and not new for tr, old, new in zip(trs, hits[base], hits[nm]) if tr["tipo"] == tipo)} for tipo in c.TIPOS}
    row = {"page_id": pid, "uf": obj["uf"], "pagina_sha256": c.digest([obj, p]),
           "unidades": len(ctx["cs"]), "palavras_ouro": len(q["gt_w"]), "resultados": resultados, "corpo": corpos,
           "pares_sucessor": reparos, "operacoes": operacoes, "segundos": time.perf_counter()-t0,
           "escores": {"pares": len(escores.valores), "fora_pool": sum(v not in escores.ranks[u] for u, v in escores.valores)}}
    gravar(path, row)
    return row


def coorte(co, args, escolha=None):
    salvos, rows = g.predicoes_salvas(co), []
    if co == "validacao_silver":
        salvos = salvos_rn(args, salvos)
    for obj, p in o.paginas(co):
        vigiar()
        row = avaliar_pagina(co, obj, p, salvos, escolha)
        rows.append(row)
        print(f"E006 {co}: {len(rows)} páginas; {row['segundos']:.2f} s", flush=True)
        gc.collect()
    gravar(EXEC / ("ordem_" + co + ".json"), [r["page_id"] for r in rows])
    return rows


def selecionar(dados):
    def media(nm, metrica):
        return statistics.mean(statistics.mean(r["resultados"][nm]["metricas"][metrica]
                                for r in dados[co]) for co in o.DESENV)
    tb = media("hibrido67", "tau")
    alternativas = []
    for lam in LIMIARES:
        for limite in LIMITES:
            nm = nome(lam, limite)
            tau, quebras = media(nm, "tau"), media(nm, "quebras")
            alternativas.append({"metodo": nm, "lambda": lam, "M": limite,
                                 "tau": tau, "quebras": quebras, "delta_tau": tau-tb,
                                 "elegivel": tau >= tb-.005-1e-12})
    elegiveis = [x for x in alternativas if x["elegivel"]]
    exigir(elegiveis, "Nenhuma configuracao atende a restricao de tau no ajuste; nao abrir externas")
    melhor = min(elegiveis, key=lambda x: (x["quebras"], -x["tau"],
                                          x["M"] if x["M"] is not None else math.inf, -x["lambda"]))
    return {**melhor, "tau_hibrido_ajuste": tb, "alternativas": alternativas}


def congelar(an, dados, escolha):
    previsto = {"assinatura": c.digest(MAN), "fontes": MAN["fontes"],
                "codigo_sha256": c.sha(Path(__file__)), "ancora": an,
                "escolha": escolha, "ajuste_sha256": c.digest(dados),
                "predicoes_rn": {p.name: c.sha(p) for p in sorted((OUT / "predicoes_rn").glob("*.json"))}}
    anterior = ler(OUT / "congelamento.json")
    if anterior:
        exigir({k: anterior[k] for k in previsto} == previsto, "Congelamento mudou; nao repetir externas")
        return anterior
    previsto["congelado_em_utc"] = agora()
    gravar(OUT / "congelamento.json", previsto)
    gravar(EXEC / "codigo_congelado.py", Path(__file__).read_text(encoding="utf-8"))
    return previsto


def alias_ajuste(dados, escolha):
    for co in o.DESENV:
        for row in dados[co]:
            for campo in ("resultados", "corpo", "pares_sucessor", "operacoes"):
                row[campo][CAND] = row[campo][escolha["metodo"]]


def resumir(rows, nomes):
    resumo = {}
    W = b.PESOS_CLUSTER(rows)
    for nm in nomes:
        rs = [r for r in rows if nm in r["resultados"]]
        if not rs:
            continue
        exigir(len(rs) == len(rows), "Media parcial de metodo proibida")
        metricas = {k: e.media_ic([r["resultados"][nm]["metricas"][k] for r in rs], W) for k in o.METRICAS}
        contrastes, pares_sucessor = {}, {}
        for base in ("regra", "hibrido67", "regra_reordena"):
            if base not in rows[0]["resultados"]:
                continue
            contrastes[base] = {}
            for k in o.METRICAS:
                ds = [r["resultados"][nm]["metricas"][k]-r["resultados"][base]["metricas"][k] for r in rs]
                por_uf = {uf: statistics.mean(d for r, d in zip(rs, ds) if r["uf"] == uf) for uf in sorted({r["uf"] for r in rs})}
                sinal = -1 if k in ("quebras", "quebras_mil") else 1
                contrastes[base][k] = {**e.media_ic(ds, W), "por_veiculo": por_uf,
                    "wilcoxon_veiculo": e.pratt(list(por_uf.values())),
                    "melhor": sum(sinal*d > 1e-12 for d in ds),
                    "igual": sum(abs(d) <= 1e-12 for d in ds), "pior": sum(sinal*d < -1e-12 for d in ds)}
            pares_sucessor[base] = {tipo: {k: sum(r["pares_sucessor"][nm][base][tipo][k] for r in rs)
                                  for k in ("reparos", "regressoes")} for tipo in c.TIPOS}
        oper = collections.Counter(op["tipo"] for r in rs for op in r["operacoes"].get(nm, []))
        resumo[nm] = {"n": len(rs), "veiculos": len({r["uf"] for r in rs}), "metricas": metricas,
                       "contrastes": contrastes, "pares_sucessor": pares_sucessor,
                       "operacoes": dict(oper), "paginas_com_operacoes": sum(bool(r["operacoes"].get(nm)) for r in rs),
                       "corpo": {k: e.media_ic([r["corpo"][nm].get(k) for r in rs], W) for k in o.METRICAS},
                       "cobertura": min(r["resultados"][nm]["cobertura_palavras"] for r in rs),
                       "quebras_mil_micro": 1000*sum(r["resultados"][nm]["metricas"]["quebras"] for r in rs)/sum(r["palavras_ouro"] for r in rs)}
    return resumo


def julgar(resumos):
    if not all(co in resumos and CAND in resumos[co] for co in o.COORTES):
        return {"veredito": "PENDENTE", "itens": {}}
    ss = {co: resumos[co][CAND] for co in o.COORTES}
    ext = o.COORTES[2:]
    item1 = all(ss[co]["contrastes"]["regra_reordena"]["quebras"]["media"] < 0
                for co in ("golden_v4", "golden_v3_novo"))
    item2a = all(ss[co]["contrastes"]["hibrido67"]["quebras"]["media"] <= 0 for co in ext)
    item2b = any(ss[co]["contrastes"]["hibrido67"]["quebras"]["ic"][1] < 0 for co in ext)
    item3 = all(ss[co]["contrastes"]["hibrido67"]["tau"]["media"] >= -.005-1e-12
                for co in ("golden_v4", *ext))
    item4 = all(3*sum(d["regressoes"] for d in ss[co]["pares_sucessor"]["hibrido67"].values()) <=
                sum(d["reparos"] for d in ss[co]["pares_sucessor"]["hibrido67"].values()) for co in ext)
    itens = {"1_menos_quebras_reordena_v4_e_v3": item1, "2a_delta_hibrido_nao_positivo_externas": item2a,
             "2b_ic95_negativo_ao_menos_uma_externa": item2b, "3_tau_margem_nas_tres": item3,
             "4_regressoes_ate_um_terco_reparos_em_cada_externa": item4}
    return {"veredito": "GO" if all(itens.values()) else "NÃO GO", "itens": itens,
            "abandono_pelo_cartao": not (item1 and item2a and item2b)}


def numero(v, n=6):
    return "indisponível" if v is None else f"{v:.{n}f}".replace(".", ",")


def intervalo(d):
    return f"{numero(d['media'])} [{numero(d['ic'][0])}; {numero(d['ic'][1])}]"


def publicar(an, dados, escolha, motivo=""):
    nomes = METODOS if escolha else CONTROLES
    resumos = {co: resumir(rows, nomes) for co, rows in dados.items() if rows}
    veredito = julgar(resumos)
    memoria = g.medir_memoria()
    estado = {"ancora": an, "escolha": escolha, "bancadas": resumos, "veredito": veredito,
              "situacao": motivo, "memoria": memoria, "manifesto": MAN}
    gravar(OUT / "metricas.json", estado)
    registro = {f"{co}/{nm}": {"tau": s["metricas"]["tau"]["media"],
                "quebras": s["metricas"]["quebras"]["media"],
                "sucessor": s["metricas"]["sucessor_linhas"]["media"]}
                for co, ss in resumos.items() for nm, s in ss.items()}
    exigir(all(math.isfinite(v) for s in registro.values() for v in s.values()), "Resumo com nulos/NaN")
    gravar(OUT / "resumo_registro.json", registro)
    ls = [f"1. Âncora golden_v4: τ {numero(an['tau'])}; {numero(an['quebras'])} quebras/página.",
          "2. Ajuste v4 + RN com peso igual; " + (f"λ={numero(escolha['lambda'], 1)}, M={escolha['M'] or '∞'} congelados." if escolha else "seleção pendente."),
          "3. " + ("; ".join(f"{co}: residual {numero(ss[CAND]['metricas']['quebras']['media'])} quebras/página" for co, ss in resumos.items() if CAND in ss) or "Somente ajuste parcial; externas fechadas."),
          "4. Veredito pelo cartão E006: " + veredito["veredito"] + ".",
          "5. CPU, sem retreino, referências fora da busca, palavras preservadas e cache por página/passo.",
          "6. golden_v3_novo já foi consultado em rodadas anteriores; teste cego não foi avaliado.", "",
          "# E006 — correção residual local", "", "Relatório integralmente gerado pelo script.", ""]
    if motivo:
        ls += ["Situação: " + motivo, ""]
    ls += ["## Método, seleção e limitações", "",
           "Ordem inicial: híbrido 67 salvo (LayoutReader até 67 unidades, regra nas demais). Operações importadas literalmente de `e002_oraculos.operacoes` e `mover`: troca vizinha; bloco de 1–4 textos até 8 posições na coluna sem atravessar margem/átomo/ponte; reinserção de margem/título antes/depois dos candidatos K32 ou nas extremidades. A restrição de barreira vale para bloco_coluna; vizinhas e reinserções conservam exatamente a definição do E002, inclusive suas exceções.", "",
           "Ganho = soma de log P das arestas criadas menos removidas, com FIM privado do E004 e sem escore de INÍCIO. Maior ganho estritamente acima de λ; empate pela enumeração E002. M limita operações, e ∞ termina em ótimo local estrito. Para o ajuste, os prefixos 5/20 da trajetória ∞ são exatamente as buscas limitadas. Não se atravessam platôs. O ouro é usado só depois de cada predição, para medição, e no oráculo diagnóstico salvo.", "",
           "Modelo LightGBM e calibração Platt OOF do E004 importados, sem retreino/recalibração. Os pares do pool K32+extras mantêm suas features e escores. Pares fora desse pool são inferidos pelo mesmo modelo/features com rank terminal e relativo 1 (extrapolação, contada nos caches). Não se lhes atribui escore zero. A cobertura não mede texto ausente da camada digital.", "",
           "Seleção: mínima média de quebras de golden_v4/RN, com peso 1/2 para cada bancada, e τ médio ≥ híbrido médio − 0,005. Desempates: maior τ, menor M, maior λ; fixados no código antes da medição. O item 3 do cartão é depois conferido separadamente nas três bancadas principais. Nenhum parâmetro é escolhido pelas externas.", "",
           "Oráculo residual é o teto local diagnóstico E002 salvo, iniciado na regra; não é um limite matemático para a busca iniciada no híbrido. RN não tinha predições LayoutReader nas páginas leves: o script exige complemento explícito e nunca substitui pela regra ou usa média parcial. Regra_reordena não existe salva para RN e é omitida nessa bancada auxiliar.", "",
           f"Estatística importada: {b.NBOOT} bootstraps por veículo, semente {b.SEMENTE}, IC95 percentil; Wilcoxon Pratt bilateral sobre os deltas médios por veículo, descritivo. Médias principais por página; as três bancadas principais são separadas e não são amostras independentes somáveis. RN tem um veículo: IC degenerado. Silver usa fluxo PDF ruidoso e pode ter átomos enormes que dominam τ. Regressões/reparos comparam sucessores-ouro intactos, inclusive no critério 4, relativamente ao híbrido; o critério é exigido em cada externa separadamente.", "",
           "Corpo é projeção diagnóstica importada do E014: exclui margens detectadas automaticamente e usa a régua oficial; não existe gabarito humano independente de corpo. Quebras/1.000 macro dividem por palavras-ouro por página; micro divide pelo total de palavras-ouro. Fidelidade de 12 é importada. O teste cego é barrado por ID/PDF antes da desserialização de cada registro.", "",
           f"Pico RSS medido pelo SO: {numero(memoria['pico_rss_mb'], 1)} MiB (limite 3072 MiB); threads 4, processos 1, num_workers 0. Manifesto e trilhas por operação ficam em `{EXEC.relative_to(RAIZ).as_posix()}`. O código é arquivado quando o ajuste completo permite congelar os parâmetros.", ""]
    if escolha:
        ls += ["## Grade do ajuste (sem externas)", "", "| λ | M | Quebras (v4/RN 1/2) | τ | Δτ híbrido | Elegível |", "|---:|---:|---:|---:|---:|---|"]
        for a in escolha["alternativas"]:
            ls += [f"| {numero(a['lambda'],1)} | {a['M'] or '∞'} | {numero(a['quebras'])} | {numero(a['tau'])} | {numero(a['delta_tau'])} | {a['elegivel']} |"]
    else:
        ls += ["## Grade parcial (não constitui seleção)", "", "| Bancada | λ | M | n | τ | Quebras/pág | Sucessor |", "|---|---:|---:|---:|---:|---:|---:|"]
        for co in o.DESENV:
            rows = dados.get(co, [])
            if not rows:
                continue
            for lam in LIMIARES:
                for limite in LIMITES:
                    nm = nome(lam, limite)
                    vals = [r["resultados"][nm]["metricas"] for r in rows]
                    ls += [f"| {co} | {numero(lam,1)} | {limite or '∞'} | {len(vals)} | " +
                           " | ".join(numero(statistics.mean(v[k] for v in vals)) for k in ("tau", "quebras", "sucessor_linhas")) + " |"]
    for co in (*o.COORTES[:1], *o.COORTES[2:], "validacao_silver"):
        if co not in resumos:
            continue
        ss = resumos[co]
        ls += ["", "## " + co, "", "| Método | n / veículos | τ palavras | Quebras/pág | Quebras/1.000 macro / micro | Fid12 | Sucessor linhas | Cobertura |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for nm, s in ss.items():
            mm = s["metricas"]
            ls += [f"| {nm} | {s['n']} / {s['veiculos']} | {numero(mm['tau']['media'])} | {numero(mm['quebras']['media'])} | {numero(mm['quebras_mil']['media'])} / {numero(s['quebras_mil_micro'])} | {numero(mm['fid12']['media'])} | {numero(mm['sucessor_linhas']['media'])} | {numero(s['cobertura']*100,1)}% |"]
        ls += ["", "### Contrastes pareados", "", "| Método | Referência | Métrica | Δ [IC95 veículo] | p veículo | Melhor/igual/pior |", "|---|---|---|---:|---:|---:|"]
        for nm, s in ss.items():
            for base, cs in s["contrastes"].items():
                if base == nm:
                    continue
                for k, d in cs.items():
                    ls += [f"| {nm} | {base} | {k} | {intervalo(d)} | {numero(d['wilcoxon_veiculo']['p'])} | {d['melhor']}/{d['igual']}/{d['pior']} |"]
        ls += ["", "### Sucessores reparados e perdidos", "", "| Método | Referência | Reparos | Regressões |", "|---|---|---:|---:|"]
        for nm, s in ss.items():
            for base, tipos in s["pares_sucessor"].items():
                ls += [f"| {nm} | {base} | {sum(x['reparos'] for x in tipos.values())} | {sum(x['regressoes'] for x in tipos.values())} |"]
        if CAND in ss:
            s = ss[CAND]
            ls += ["", f"Operações do candidato: {sum(s['operacoes'].values())}; por tipo: `{json.dumps(s['operacoes'],ensure_ascii=False)}`; páginas alteradas: {s['paginas_com_operacoes']}.", "",
                   "| Veículo | Δ quebras vs regra | Δ quebras vs híbrido | Δτ vs híbrido |", "|---|---:|---:|---:|"]
            for uf in s["contrastes"]["regra"]["quebras"]["por_veiculo"]:
                ls += [f"| {uf} | {numero(s['contrastes']['regra']['quebras']['por_veiculo'][uf])} | {numero(s['contrastes']['hibrido67']['quebras']['por_veiculo'][uf])} | {numero(s['contrastes']['hibrido67']['tau']['por_veiculo'][uf])} |"]
            ls += ["", "| Classe de sucessor | Reparos vs híbrido | Regressões vs híbrido |", "|---|---:|---:|"]
            for tipo, d in s["pares_sucessor"]["hibrido67"].items():
                ls += [f"| {c.TIPOS[tipo] if isinstance(c.TIPOS, dict) else tipo} | {d['reparos']} | {d['regressoes']} |"]
        ls += ["", "### Corpo (diagnóstico por margens automáticas)", "", "| Método | τ | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |", "|---|---:|---:|---:|---:|---:|"]
        for nm, s in ss.items():
            ls += ["| " + nm + " | " + " | ".join(numero(s["corpo"][k]["media"]) for k in o.METRICAS) + " |"]
    ls += ["", "## Veredito item a item (cartão E006)", "", "**" + veredito["veredito"] + "**.", ""]
    for item, passa in veredito["itens"].items():
        ls += [f"- {item}: {'PASSA' if passa else 'FALHA'}."]
    if veredito.get("abandono_pelo_cartao"):
        ls += ["", "Falhou (1) ou (2): aplica-se o abandono pré-registrado; híbrido 67 permanece finalista. Não foi executada nova variante após o veredito."]
    gravar(OUT / "RELATORIO.md", "\n".join(ls) + "\n")
    return estado


def autoteste():
    """Confere ganho de bordas em todos os movimentos de permutacoes pequenas."""
    import itertools
    cont = 0
    for n in range(2, 8):
        ordem = [str(i) for i in range(n)]
        scores = {(u, v): -.01*(k+1) for k, (u, v) in enumerate(
            (u, v) for u in ordem for v in [*ordem, None] if v != u)}
        for i, tam, j in itertools.product(range(n), range(1, 5), range(n)):
            if i+tam > n or j > n-tam or j == i:
                continue
            nova = o.mover(ordem, i, tam, j)
            novos, antigos = bordas_movimento(ordem, i, tam, j)
            exigir(novos == pares(nova)-pares(ordem) and antigos == pares(ordem)-pares(nova), "Delta de bordas incorreto")
            delta = math.fsum([scores[x] for x in novos] + [-scores[x] for x in antigos])
            total = math.fsum(scores[x] for x in pares(nova))-math.fsum(scores[x] for x in pares(ordem))
            exigir(abs(delta-total) < 1e-10, "Ganho incorreto")
            cont += 1
    print(f"Autoteste: {cont} movimentos, bordas/FIM e ganhos completos conferidos", flush=True)


def validar_escores():
    """Confere contra a inferencia E004 original, so no primeiro ajuste v4."""
    global MODELO
    obj, p = next(o.paginas("golden_v4"))
    ctx = c.contexto(p, obj["palavras"])
    scores = Escores("golden_v4", ctx)
    _, cand, extras = g.candidatos(ctx)
    X, edges = g.matriz_features(ctx, cand[32], extras)
    scores.completar(edges)
    if MODELO is None:
        import lightgbm as lgb
        MODELO = lgb.Booster(model_file=str(FONTE / "modelo.txt"))
    cal = INFO["calibracao"]
    original = -np.logaddexp(0., -(cal["a"]*MODELO.predict(X, raw_score=True, num_threads=4)+cal["b"]))
    diferencas = np.abs(original - np.array([scores.valores[edge] for edge in edges]))
    exigir(float(diferencas.max()) < 1e-12, "Escores canonicos nao reproduzem o E004")
    r = {"page_id": p["page_id"], "pares_conferidos": len(edges),
         "max_erro_logp": float(diferencas.max()), "aprovado": True,
         "referencia": "g.matriz_features e inferencia/calibracao E004 sem adaptacao"}
    gravar(EXEC / "validacao_escores.json", r)
    print("Escores canonicos E004 conferidos: " + str(r), flush=True)


def conferir():
    """Reconstroi relatorio dos caches, sem abrir/reavaliar paginas."""
    ponteiro = b.ler(OUT / "cache/ultima_execucao.json")
    global EXEC, MAN
    EXEC = OUT / ponteiro["execucao"]
    MAN = b.ler(EXEC / "manifesto.json")
    congelado = ler(OUT / "congelamento.json")
    estado = b.ler(OUT / "metricas.json")
    g.PICO_RSS_MB = max(g.PICO_RSS_MB, estado["memoria"]["pico_rss_mb"])
    dados = {}
    for co in o.COORTES:
        ids = ler(EXEC / ("ordem_" + co + ".json"))
        if ids:
            for pid in ids:
                o.permitido(pid)
            dados[co] = [b.ler(EXEC / "avaliacao" / co / (e.ac.chave(pid) + ".json")) for pid in ids]
    if congelado:
        alias_ajuste(dados, congelado["escolha"])
    novo = publicar(estado["ancora"], dados, congelado["escolha"] if congelado else None, estado["situacao"])
    print("Caches conferidos: " + novo["veredito"]["veredito"], flush=True)


def main():
    global LOCK_SHA, PRAZO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etapa", choices=("ajuste", "tudo"), default="tudo")
    parser.add_argument("--autoteste", action="store_true")
    parser.add_argument("--somente-ancora", action="store_true")
    parser.add_argument("--conferir", action="store_true")
    parser.add_argument("--max-minutos", type=float, default=0)
    parser.add_argument("--predicoes-rn")
    parser.add_argument("--gerar-rn", action="store_true")
    parser.add_argument("--validar-escores", action="store_true")
    args = parser.parse_args()
    LOCK_SHA, o.PROTEGIDOS = o.ler_lock()
    o.ASSINATURA_LOCK = LOCK_SHA
    if args.max_minutos:
        PRAZO = time.monotonic() + 60*args.max_minutos
    if args.autoteste:
        autoteste()
    with trava():
        if args.conferir:
            conferir()
            return
        an = o.ancora()
        if args.somente_ancora:
            return
        iniciar(args)
        if args.validar_escores:
            validar_escores()
        dados, escolha = {}, None
        try:
            for co in o.DESENV:
                dados[co] = coorte(co, args)
                publicar(an, dados, escolha)
            escolha = selecionar(dados)
            congelar(an, dados, escolha)
            alias_ajuste(dados, escolha)
            publicar(an, dados, escolha)
            print(f"Congelado: {nome(escolha['lambda'],escolha['M'])}", flush=True)
            if args.etapa == "tudo":
                abertura = ler(OUT / "abertura_externas.json")
                if abertura is None:
                    gravar(OUT / "abertura_externas.json", {"assinatura": c.digest(MAN), "aberta_em_utc": agora(), "escolha": escolha})
                for co in o.COORTES[2:]:
                    dados[co] = coorte(co, args, escolha)
                    publicar(an, dados, escolha)
            estado = publicar(an, dados, escolha)
            print("E006: " + estado["veredito"]["veredito"], flush=True)
        except (TimeoutError, KeyboardInterrupt, ValueError) as exc:
            publicar(an, dados, escolha, str(exc))
            print("Execução interrompida com caches preservados: " + str(exc), flush=True)
            raise


if __name__ == "__main__":
    main()
