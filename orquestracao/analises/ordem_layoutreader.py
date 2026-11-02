"""Compara LayoutReader pronto e projecao, sem ajustar a rede no Golden.

Reutiliza palavras, linhas, atomos e grade LOPO do experimento original. A
regua principal e a sequencia real de palavras; medianas sao diagnosticos.
Tudo roda offline em CPU. Nao abre PDFs nem exports do projeto parceiro.

Uso, da raiz: venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_layoutreader.py
Recalcular: --do-zero --conferir. Testar a interface: --somente-sinteticos.
Somente dois arquivos novos: este script e resultados/ordem_layoutreader.md.
O Markdown guarda checkpoints comprimidos, atualizados a cada pagina, para
retomar sem criar JSON, logs, bytecode ou arquivos em data/ ou models/.
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
import base64
import collections
import hashlib
import json
import math
import os
import random
import re
import statistics
import time
import zlib

# Fixar antes de importar torch/transformers; nenhuma inicializacao de CUDA.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import ordem_sem_bbox_justo as justo

SAIDA = RAIZ / "resultados/ordem_layoutreader.md"
MODELO = RAIZ / "models/terceiros/layoutreader"
ORIGINAL = RAIZ / "resultados/ordem_sem_bbox.json"
MARCADOR = "ORDEM_LAYOUTREADER_CHECKPOINT_V1"
REGUAS = ("palavras", "linhas", "regioes")
METRICAS = ("tau", "sucessor", "ard")
NOMES = {
    "xy_ouro": "XY-cut regiões-ouro",
    "xy_margens": "XY-cut regiões-ouro + margens",
    "projecao": "Projeção original LOPO",
    "lr_linhas": "LayoutReader linhas/átomos",
    "lr_margens": "LayoutReader linhas/átomos + margens LOPO",
    "lr_ouro": "LayoutReader regiões-ouro†",
    "lr_ouro_margens": "LayoutReader regiões-ouro + margens†",
    "hibrido": "Híbrido: projeção agrupa, LayoutReader ordena",
}


def hashes():
    caminhos = o.ENTRADAS + o.FONTES + [Path(o.__file__), Path(justo.__file__),
        Path(__file__), ORIGINAL, MODELO / "config.json", MODELO / "model.safetensors",
        MODELO / "README.md"]
    return {p.relative_to(RAIZ).as_posix(): justo.digest(p) for p in caminhos}


def ler_cache():
    if not SAIDA.exists():
        return None
    try:
        s = SAIDA.read_text(encoding="utf-8")
        m = re.search(rf"<!-- {MARCADOR}\n([A-Za-z0-9+/=]+)\n-->", s)
        return json.loads(zlib.decompress(base64.b64decode(m.group(1))).decode("utf-8")) if m else None
    except (ValueError, AttributeError, zlib.error):
        return None


def gravar(R, texto):
    raw = json.dumps(R, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    cache = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
    with SAIDA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(texto + f"\n<!-- {MARCADOR}\n{cache}\n-->\n")
        f.flush()
        os.fsync(f.fileno())


def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def parcial(R):
    rows = R["paginas"]
    txt = ["# LayoutReader — execução parcial", "", "Sem veredito até concluir a amostra.", "",
           f"Grade reproduzida em {len(R['grade_paginas'])} páginas; variantes executadas em {len(rows)} páginas.", ""]
    if rows:
        txt += ["| Método | τ de palavras parcial |", "|---|---:|"]
        for m in NOMES:
            vals = [p["metodos"][m]["palavras"]["tau"] for p in rows]
            vals = [v for v in vals if v is not None]
            txt.append(f"| {NOMES[m]} | {f(statistics.mean(vals)) if vals else '—'} |")
    txt += ["", "Checkpoint interno no comentário final; retome com o mesmo comando sem `--do-zero`.", ""]
    return "\n".join(txt)


def permutacao(ordem, ids, contexto):
    if len(ordem) != len(ids) or len(set(ordem)) != len(ordem) or set(ordem) != set(ids):
        raise ValueError(f"Saída inválida, sem reparo pelo ouro: {contexto}")


def decodificar(logits):
    """Linhas sao posicoes de saida; colunas sao indices de caixas na entrada.

    Uma posicao recusada nunca volta a essa caixa. Uma nova concorrente pode
    deslocar uma vencedora antiga, se tiver logit maior. Empates usam indice.
    Nao usa Hungarian, soma global, ordem humana nem preenchimento de faltantes.
    Retorna diretamente os indices escolhidos, como parse_logits() oficial;
    argsort() inverteria a permutacao, erro detectado no controle sintetico.
    """
    z = np.asarray(logits, dtype=np.float64).copy()
    if z.ndim != 2 or z.shape[0] != z.shape[1] or not np.isfinite(z).all():
        raise ValueError("Logits devem ser uma matriz quadrada finita")
    n = len(z)
    for rodada in range(n * n + 1):
        postos = np.argmax(z, axis=1) if n else np.array([], dtype=int)
        repetidos = [p for p, k in collections.Counter(postos.tolist()).items() if k > 1]
        if not repetidos:
            ordem = postos.tolist()
            permutacao(ordem, list(range(n)), "decodificação")
            return ordem, {"rodadas_conflito": rodada}
        for p in repetidos:
            candidatos = np.flatnonzero(postos == p).tolist()
            vencedor = max(candidatos, key=lambda i: (z[i, p], -i))
            for i in candidatos:
                if i != vencedor:
                    z[i, p] = -np.inf
        if np.any(np.all(np.isneginf(z), axis=1)):
            raise ValueError("Decodificação esgotou as posições")
    raise RuntimeError("Decodificação excedeu o limite de recusas")


def agrupar_folha(items, ordem, h):
    """Junta vizinhos textuais alinhados; cada tabela/imagem e um grupo separado."""
    gs = []
    for i in ordem:
        b = items[i]["bbox"]
        juntar = False
        if gs and items[i].get("tipo") == "texto" and items[gs[-1][-1]].get("tipo") == "texto":
            a = items[gs[-1][-1]]["bbox"]
            wa, wb = a[2] - a[0], b[2] - b[0]
            overlap = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            juntar = (min(wa, wb) > 0 and overlap >= .7 * min(wa, wb)
                      and abs(a[0] - b[0]) <= 1.5 * h
                      and max(wa, wb) <= 2 * min(wa, wb)
                      and -.25 * h <= b[1] - a[3] <= 2.5 * h)
        if juntar:
            gs[-1].append(i)
        else:
            gs.append([i])
    return gs


def grupos_projecao(items, ids, h, vale, local=True, depth=0):
    """Mesmas calhas/pontes/faixas da projecao; preserva grupos terminais.

    A expansao inicial e identica a ordenar_projecao(). Nas folhas, so linhas
    geometricamente alinhadas sao agrupadas; atomos continuam individuais.
    """
    if not ids:
        return []
    cortes = (o.vales_locais(items, ids, h, vale) if local else o.vales(items, ids, h, vale)) if depth <= 60 else []
    if local and not cortes and depth <= 60:
        cortes = o.vales(items, ids, h, vale)
    if not cortes:
        ordem = o.xycut(ids, o.boxes(items)) if depth <= 60 else sorted(
            ids, key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
        return agrupar_folha(items, ordem, h)
    W = max(items[i]["bbox"][2] for i in ids) - min(items[i]["bbox"][0] for i in ids)
    largos = [i for i in ids if any(items[i]["bbox"][0] < c < items[i]["bbox"][2]
        and (not local or min(c-items[i]["bbox"][0], items[i]["bbox"][2]-c) >= .10*W) for c in cortes)]
    rec = lambda xs: grupos_projecao(items, xs, h, vale, local, depth+1)
    if largos:
        largos.sort(key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i))
        ys = [(items[i]["bbox"][1]+items[i]["bbox"][3])/2 for i in largos]
        secoes = [[] for _ in range(len(largos)+1)]
        grandes = set(largos)
        for i in ids:
            if i not in grandes:
                cy = (items[i]["bbox"][1]+items[i]["bbox"][3])/2
                secoes[sum(y < cy for y in ys)].append(i)
        gs = []
        for j, sec in enumerate(secoes):
            gs += rec(sec)
            if j < len(largos):
                gs.append([largos[j]])
        return gs
    cols = [[] for _ in range(len(cortes)+1)]
    for i in ids:
        cx = (items[i]["bbox"][0]+items[i]["bbox"][2])/2
        cols[sum(c < cx for c in cortes)].append(i)
    return [g for col in cols for g in rec(col)]


class Ordenador:
    def __init__(self, threads):
        import torch
        import transformers
        from transformers import LayoutLMv3ForTokenClassification
        self.torch = torch
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        t = time.perf_counter()
        self.modelo = LayoutLMv3ForTokenClassification.from_pretrained(
            str(MODELO), local_files_only=True, dtype=torch.float32).to(device="cpu", dtype=torch.float32).eval()
        self.info = {"carga_ms": 1000*(time.perf_counter()-t), "threads": threads,
            "parametros": sum(p.numel() for p in self.modelo.parameters()),
            "pesos_bytes": (MODELO / "model.safetensors").stat().st_size,
            "arquivos_bytes": sum(p.stat().st_size for p in MODELO.iterdir() if p.is_file()),
            "torch": torch.__version__, "transformers": transformers.__version__,
            "dispositivo": str(next(self.modelo.parameters()).device),
            "dtype": str(next(self.modelo.parameters()).dtype)}
        # Aquecimento nao entra na latencia de pagina.
        self.direto([{"bbox": [10, 10, 90, 20]}], [0], 100, 100, "aquecimento", {})

    def direto(self, items, ids, W, H, chave, diag):
        n = len(ids)
        if n < 2:
            return list(ids)
        if n > 510:
            raise ValueError("Chamada direta excede 510 caixas")
        if W <= 0 or H <= 0:
            raise ValueError("Dimensões inválidas")
        entrada = list(ids)
        random.Random(f"entrada-{chave}").shuffle(entrada)
        bs = []
        for i in entrada:
            b = items[i]["bbox"]
            if len(b) != 4 or not all(math.isfinite(v) for v in b):
                raise ValueError("Caixa inválida")
            norm = [max(0, min(1000, int(round(v*1000/(W if k%2 == 0 else H))))) for k,v in enumerate(b)]
            diag["coordenadas_limitadas"] = diag.get("coordenadas_limitadas", 0) + sum(
                v < 0 or v > (W if k%2 == 0 else H) for k,v in enumerate(b))
            if norm[2] < norm[0] or norm[3] < norm[1]:
                raise ValueError("Caixa com cantos invertidos")
            bs.append(norm)
        torch = self.torch
        t = time.perf_counter()
        with torch.inference_mode():
            logits = self.modelo(
                bbox=torch.tensor([[[0]*4]+bs+[[0]*4]], dtype=torch.long, device="cpu"),
                input_ids=torch.tensor([[0]+[3]*n+[2]], dtype=torch.long, device="cpu"),
                attention_mask=torch.ones((1,n+2), dtype=torch.long, device="cpu")).logits[0]
        if logits.shape[1] < n:
            raise ValueError("Número de posições do checkpoint insuficiente")
        z = logits[1:n+1, :n].float().cpu().numpy()
        diag["rede_ms"] = diag.get("rede_ms", 0.) + 1000*(time.perf_counter()-t)
        ordem, dec = decodificar(z)
        if diag.get("capturar_interface"):
            diag["interface"] = {"entrada":entrada,"indices_decodificados":ordem,
                "saida":[entrada[i] for i in ordem],
                "saida_interpretacao_invertida":[entrada[i] for i in np.argsort(ordem,kind="stable").tolist()]}
        diag["chamadas"] = diag.get("chamadas", 0)+1
        diag["max_caixas_chamada"] = max(diag.get("max_caixas_chamada", 0), n)
        diag["rodadas_conflito"] = diag.get("rodadas_conflito", 0)+dec["rodadas_conflito"]
        return [entrada[i] for i in ordem]

    def ordenar(self, items, ids, W, H, h, vale, chave, diag, depth=0):
        if len(ids) <= 510:
            return self.direto(items, ids, W, H, chave, diag)
        diag["excesso_510"] = diag.get("excesso_510", 0)+1
        gs = grupos_projecao(items, ids, h, vale)
        if len(gs) <= 510:
            reps = [{"bbox": o.envelope([items[i]["bbox"] for i in g])} for g in gs]
            go = self.direto(reps, list(range(len(gs))), W, H, chave+"-paragrafos", diag)
            diag["linhas_fundidas"] = diag.get("linhas_fundidas", 0)+len(ids)-len(gs)
            return [i for j in go for i in gs[j]]
        # Muitas caixas atomicas: hierarquia espacial, sem truncar/perder itens.
        diag["hierarquia"] = diag.get("hierarquia", 0)+1
        xs = sorted(ids, key=lambda i: ((items[i]["bbox"][0]+items[i]["bbox"][2])/2,
                                     items[i]["bbox"][1], i))
        gs = [xs[k:k+128] for k in range(0, len(xs), 128)]
        reps = [{"bbox": o.envelope([items[i]["bbox"] for i in g])} for g in gs]
        go = self.ordenar(reps, list(range(len(gs))), W, H, h, vale, chave+"-grupos", diag, depth+1)
        return [i for j in go for i in self.ordenar(items, gs[j], W, H, h, vale, chave+f"-{j}", diag, depth+1)]


def sinteticos(lr):
    z = [[6,5,0], [8,1,0], [9,7,4]]
    ordem, dec = decodificar(z)
    if ordem != [1,2,0]:
        raise ValueError("Decodificação de conflitos falhou")
    bs = [[50,100,450,120], [50,350,450,370], [550,100,950,120], [550,350,950,370]]
    items = [{"bbox": b, "tipo": "texto", "ks": [i]} for i,b in enumerate(bs)]
    testes = []
    for seed in range(6):
        d = {"capturar_interface":True}
        pred = lr.ordenar(items, list(range(4)), 1000, 1000, 20, .08, f"teste-{seed}", d)
        permutacao(pred, list(range(4)), "duas colunas")
        testes.append({"chave": seed, "ordem": pred, "correta": pred == list(range(4)),
                       "metricas": justo.metricas(pred,list(range(4))),"interface":d["interface"]})
    densos = [{"bbox":[x,100+20*y,x+400,115+20*y],"tipo":"texto","ks":[col*10+y]}
              for col,x in enumerate((50,550)) for y in range(10)]
    dense = []
    for seed in range(3):
        dg = {"capturar_interface":True}
        pred = lr.ordenar(densos,list(range(20)),1000,1000,15,.08,f"denso-{seed}",dg)
        permutacao(pred,list(range(20)),"colunas densas")
        dense.append({"chave":seed,"ordem":pred,"metricas":justo.metricas(pred,list(range(20))),
                      "interface":dg["interface"],"tau_interpretacao_invertida":justo.metricas(
                          dg["interface"]["saida_interpretacao_invertida"],list(range(20)))["tau"]})
    if any(t["metricas"]["tau"] != 1 for t in dense):
        raise ValueError("Controle de duas colunas densas não confirma a interface")
    # Duas colunas com linhas densas: exige agrupamento sem jamais enviar >510.
    muitos = [{"bbox": [x, 100+3*y, x+380, 102+3*y], "tipo": "texto", "ks": [col*260+y]}
              for col,x in enumerate((50,550)) for y in range(260)]
    d = {}
    pred = lr.ordenar(muitos, list(range(520)), 1000, 1000, 2, .08, "excesso", d)
    permutacao(pred, list(range(520)), "sintético >510")
    if d.get("max_caixas_chamada", 0) > 510:
        raise ValueError("Agrupamento >510 excedeu o limite")
    gs = grupos_projecao(muitos,list(range(520)),2,.08)
    if [i for g in gs for i in g] != list(range(520)):
        raise ValueError("Grupos geométricos >510 não preservaram as duas colunas")
    q = {"ws": [], "p": {"dimensions": {"height": 100, "width": 100}, "bounding_boxes": []},
         "d": {"detector": {"regioes": []}}, "h": 10, "gt_r": [], "gt_l": [], "gt_w": [],
         "reg_words": {}, "gold_lines": []}
    seq, _, _ = o.prever(q, o.Config("projecao_local_margens", .45, 1.2, .08))
    vazio = justo.avaliar(q, seq)
    if vazio["palavras"]["tau"] is not None or lr.ordenar([], [], 100,100,10,.08,"vazio",{}) != []:
        raise ValueError("Página vazia recebeu medida fictícia")
    q["p"]["bounding_boxes"] = [{"id": "fig", "bbox": [0,0,50,50]}]
    q["gt_r"] = ["fig"]; q["reg_words"] = {"fig": []}
    reg_vazia = justo.avaliar(q, [])
    if reg_vazia["diag"]["regioes_sem_palavras"] != ["fig"]:
        raise ValueError("Região vazia não foi contada")
    intercalacao = justo.metricas([0,2,1,3], [0,1,2,3])
    if intercalacao["tau"] == 1:
        raise ValueError("Régua de palavras ocultou intercalação")
    return {"duas_colunas": testes, "colunas_densas":dense, "conflitos": {"ordem": ordem, **dec},
            "mais_510": {"n": len(muitos), "tau": justo.metricas(pred, list(range(520)))["tau"], **d},
            "pagina_vazia": vazio["palavras"], "regiao_vazia": reg_vazia["diag"]["regioes_sem_palavras"],
            "intercalacao": intercalacao}


def preparar_items(q, c):
    ats, livres = o.atomos(q["ws"], q["d"].get("detector", {}).get("regioes", []), c.score)
    return ats + o.linhas_partidas(q["ws"], livres, c.gap, q["h"])


def prever(q, c, metodo, lr):
    """Tempo inclui preparacao, inferencia, decodificacao e expansao; nao metricas."""
    t = time.perf_counter()
    W, H = q["p"]["dimensions"]["width"], q["p"]["dimensions"]["height"]
    diag, pr = {}, None
    ouro = metodo in ("xy_ouro", "xy_margens", "lr_ouro", "lr_ouro_margens")
    if metodo == "projecao":
        seq, items, diag = o.prever(q, c)
    else:
        if ouro:
            items = [{"id": r["id"], "bbox": r["bbox"], "ks": q["reg_words"][r["id"]],
                      "tipo": r.get("classe")} for r in q["p"]["bounding_boxes"]]
        else:
            items = preparar_items(q, c)
        politica = (metodo in ("xy_margens", "lr_ouro_margens")
                    or metodo in ("lr_margens", "hibrido") and c.abordagem.endswith("margens"))
        ini, corpo, marcas, fim = justo.particao(items, q["ws"], H, "geo" if politica else None)
        diag.update(n_items=len(items), atomos_vazios=sum(not m["ks"] for m in items),
                    topo=len(ini), rodape=len(fim), marcas=len(marcas), grupos=0)
        chave_geo = lambda i: (items[i]["bbox"][1], items[i]["bbox"][0], i)
        ordens = []
        for nome, ids in zip(("topo","corpo","marcas","rodape"), (ini,corpo,marcas,fim)):
            if metodo.startswith("xy"):
                ordem = o.xycut(ids, o.boxes(items)) if nome == "corpo" else sorted(ids, key=chave_geo)
            elif metodo == "hibrido":
                gs = grupos_projecao(items, ids, q["h"], c.vale, local="local" in c.abordagem)
                # Provar que extrair os grupos nao muda a projecao original.
                if nome == "corpo":
                    dg = {"max_colunas": 1, "pontes": 0}
                    esperado = o.ordenar_projecao(items, ids, q["h"], c.vale, dg, local="local" in c.abordagem)
                    if [i for g in gs for i in g] != esperado:
                        raise ValueError("Agrupamento diverge da projeção")
                reps = [{"bbox": o.envelope([items[i]["bbox"] for i in g]), "tipo": "grupo"} for g in gs]
                go = lr.ordenar(reps, list(range(len(gs))), W,H,q["h"],c.vale,q["p"]["page_id"]+nome,diag)
                ordem = [i for j in go for i in gs[j]]
                diag["grupos"] += len(gs)
            else:
                ordem = lr.ordenar(items, ids, W,H,q["h"],c.vale,q["p"]["page_id"]+nome,diag)
            ordens += ordem
        permutacao(ordens, list(range(len(items))), metodo)
        seq = o.fluxo([items[i] for i in ordens], q["ws"])
        if ouro:
            pr = [items[i]["id"] for i in ordens]
            livres = sorted(set(range(len(q["ws"]))) - set(seq))
            seq += [k for L in o.linhas(q["ws"], livres) for k in L["ks"]]
            diag["livres_fim"] = len(livres)
    ms = 1000*(time.perf_counter()-t)
    permutacao(seq, list(range(len(q["ws"]))), metodo+" palavras")
    r = justo.avaliar(q, seq, pr)
    r["diag"].update(diag)
    r["tempo_ms"] = ms
    r["seq"] = seq
    return r


def grade_pagina(q, cs):
    resultados = {}
    for c in cs:
        seq, _, _ = o.prever(q, c)
        ranks = {k:i for i,k in enumerate(seq)}
        rs = q["p"]["bounding_boxes"]
        if all(q["reg_words"].values()):
            pr = sorted([r["id"] for r in rs], key=lambda rid: (
                statistics.median(ranks[k] for k in q["reg_words"][rid]),
                next(r["bbox"][1] for r in rs if r["id"] == rid),
                next(r["bbox"][0] for r in rs if r["id"] == rid), rid))
            metricas = justo.metricas(pr, q["gt_r"])
        else:
            metricas = justo.avaliar(q, seq)["regioes"]
        resultados[c.id] = metricas
    return resultados


def selecionar(R, cs):
    rows = R["grade_paginas"]
    ids = []
    for j in range(len(rows)):
        def key(i):
            treino = [p["metricas"][cs[i].id] for k,p in enumerate(rows) if k != j]
            return (sum(r["tau"] for r in treino if r["tau"] is not None),
                    sum(r["sucessor"] for r in treino if r["sucessor"] is not None), -i)
        ids.append(max(range(len(cs)), key=key))
    return ids


def estatisticas(rows, nboot, seed):
    grupos = sorted({p["veiculo"] for p in rows})
    gi = np.array([grupos.index(p["veiculo"]) for p in rows])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0,len(grupos),(nboot,len(grupos)))
    counts = np.stack([(draws == g).sum(axis=1) for g in range(len(grupos))], axis=1)
    pesos = counts[:,gi]
    S, B = {}, {}
    for m in NOMES:
        S[m], B[m] = {}, {}
        for regua in (*REGUAS, "fragmentacao"):
            S[m][regua], B[m][regua] = {}, {}
            for k in (("fracao","fracao_estrita") if regua == "fragmentacao" else METRICAS):
                vals = [p["metodos"][m]["diag" if regua == "fragmentacao" else regua][k] for p in rows]
                v = np.array([np.nan if a is None else a for a in vals])
                boot = justo.media_boot(np.broadcast_to(v,pesos.shape), pesos)
                fin = boot[np.isfinite(boot)]
                S[m][regua][k] = {"media": float(np.nanmean(v)) if np.isfinite(v).any() else None,
                    "ic95": np.quantile(fin,[.025,.975]).tolist() if len(fin) else [None,None],
                    "n": int(np.isfinite(v).sum())}
                B[m][regua][k] = boot
    return S, B, gi


def pratt(v):
    d = np.round(np.asarray(v), 12)
    d = d[np.isfinite(d)]
    if not len(d) or np.all(d == 0):
        return 0., 1.
    res = wilcoxon(d, zero_method="pratt", alternative="two-sided", method="approx")
    return float(res.statistic), float(res.pvalue)


def testes(rows, S, B, gi):
    ts = []
    for base in ("xy_ouro", "xy_margens", "projecao"):
        for m in NOMES:
            if m == base or m in ("xy_ouro", "xy_margens"):
                continue
            for regua in REGUAS:
                for k in METRICAS:
                    d = np.array([(p["metodos"][m][regua][k]-p["metodos"][base][regua][k])
                        if p["metodos"][m][regua][k] is not None and p["metodos"][base][regua][k] is not None
                        else np.nan for p in rows])
                    v = d[np.isfinite(d)]
                    boot = B[m][regua][k]-B[base][regua][k]
                    fin = boot[np.isfinite(boot)]
                    W,p = pratt(v)
                    gd = [float(np.nanmean(d[gi == g])) for g in sorted(set(gi)) if np.isfinite(d[gi == g]).any()]
                    _,pg = pratt(gd)
                    sinal = -1 if k == "ard" else 1
                    ts.append({"metodo": m, "base": base, "regua": regua, "metrica": k,
                        "delta": float(np.mean(v)) if len(v) else None,
                        "ic95": np.quantile(fin,[.025,.975]).tolist() if len(fin) else [None,None],
                        "ganha": int((sinal*v > 1e-12).sum()), "empata": int((np.abs(v) <= 1e-12).sum()),
                        "perde": int((sinal*v < -1e-12).sum()), "W": W, "p": p, "p_veiculo": pg})
    # Uma familia explicita: todas as comparacoes/métricas/reguas mostradas.
    ordem = sorted(range(len(ts)), key=lambda i: ts[i]["p"])
    anterior = 0.
    for j,i in enumerate(ordem):
        anterior = max(anterior, min(1., (len(ts)-j)*ts[i]["p"]))
        ts[i]["p_holm"] = anterior
    return ts


def cel(obj, pct=False):
    a = 100 if pct else 1
    n = 1 if pct else 3
    sufixo = "%" if pct else ""
    if obj["media"] is None:
        return "—"
    return f"{f(a*obj['media'],n)}{sufixo} [{f(a*obj['ic95'][0],n)}; {f(a*obj['ic95'][1],n)}]"


def tabela(S, regua, custo=None):
    txt = ["| Método | τ ↑ (IC 95%) | Sucessor ↑ (IC 95%) | ARD norm. ↓ (IC 95%) |" +
           (" Regiões fragmentadas | ms/página CPU |" if custo else ""),
           "|---|---:|---:|---:|" + ("---:|---:|" if custo else "")]
    for m in NOMES:
        r = S[m][regua]
        linha = f"| {NOMES[m]} | {cel(r['tau'])} | {cel(r['sucessor'],True)} | {cel(r['ard'])} |"
        if custo:
            linha += f" {cel(S[m]['fragmentacao']['fracao'],True)} | {f(custo[m]['media'],1)} |"
        txt.append(linha)
    return txt


def resumo_custo(rows):
    out = {}
    for m in NOMES:
        v = [p["metodos"][m]["tempo_ms"] for p in rows]
        out[m] = {"media": statistics.mean(v), "p50": float(np.median(v)), "p95": float(np.quantile(v,.95)),
                  "max": max(v), "rede_media": statistics.mean(p["metodos"][m]["diag"].get("rede_ms",0) for p in rows)}
    return out


def relatorio(R):
    rows, S, custo = R["paginas"], R["resumo"], R["custo"]
    n = len(rows)
    media = lambda m,r="palavras",k="tau": S[m][r][k]["media"]
    teste = lambda m,b,r="palavras",k="tau": next(t for t in R["testes"] if
        t["metodo"] == m and t["base"] == b and t["regua"] == r and t["metrica"] == k)
    melhor = max(("lr_linhas","lr_margens","hibrido"), key=lambda m: media(m))
    d = teste(melhor,"projecao")
    # Veredito exploratorio, com criterio transparente; nao altera o pipeline.
    if media(melhor) > media("projecao") and S[melhor]["fragmentacao"]["fracao"]["media"] <= S["projecao"]["fragmentacao"]["fracao"]["media"]:
        veredito = ("combinar os dois como candidato para validação independente" if melhor == "hibrido"
                    else "testar a troca pela variante LayoutReader com melhor saída real em ouro novo")
    else:
        veredito = "manter a projeção; nenhuma troca automática é sustentada por este experimento"
    audit = {k:sum(p["auditoria"][k] for p in rows) for k in rows[0]["auditoria"]}
    txt = ["# LayoutReader pronto no plano sem bounding box fina", "", "## Resumo em cinco linhas", "",
        f"1. Em {n} páginas de {len(R['veiculos'])} veículos, τ de palavras: projeção {f(media('projecao'))}; LayoutReader linhas/átomos {f(media('lr_linhas'))}; com margens {f(media('lr_margens'))}; híbrido {f(media('hibrido'))}.",
        f"2. A referência justa XY-cut ouro + margens chega a {f(media('xy_margens'))}; LayoutReader sobre regiões humanas chega a {f(media('lr_ouro'))}, diagnóstico com segmentação-oráculo.",
        f"3. Melhor variante sem regiões humanas: {NOMES[melhor]}; Δτ contra projeção {f(d['delta'])}, IC por veículo [{f(d['ic95'][0])}; {f(d['ic95'][1])}], Pratt por página p = {f(d['p'],6)}.",
        f"4. Custo médio CPU: projeção {f(custo['projecao']['media'],1)} ms; melhor variante {f(custo[melhor]['media'],1)} ms; pesos {f(R['modelo']['pesos_bytes']/1024**2,1)} MiB; a rede não foi afinada nestas páginas.",
        f"5. Veredito: **{veredito}**; comparar continuidade, custo e o estrato multicoluna antes de adotar.", "",
        "## Dados, preparação e comparação", "",
        f"Foram mantidas as {n} páginas concluídas de `golden_v4`, associando {audit['palavras']} palavras, {sum(p['n_regioes'] for p in rows)} regiões e {sum(p['n_linhas'] for p in rows)} linhas-ouro. Há {audit['sem_ouro']} palavras fora do ouro, {audit['ambiguas']} associações ambíguas, {audit['regioes_vazias']} regiões vazias e {audit['sem_palavras']} páginas sem palavras. O Golden já retirou {audit['visuais_retiradas']} regiões visuais sem texto; a posição delas não é avaliável aqui. Nenhuma página foi excluída nesta execução.",
        "As funções `atomos`, `linhas_partidas`, `fluxo` e a projeção vêm de `ordem_sem_bbox.py`, sem alterar esse arquivo. O carregador defensivo, a associação ao ouro e as três réguas vêm de `ordem_sem_bbox_justo.py`. Não foram abertos PDFs, exports do Label Studio nem imagens; a inferência recebe as mesmas palavras e os mesmos caches de tabela/imagem do Diamond. Nenhum detector é executado ao vivo.",
        f"Reproduzimos do zero a grade original de {len(R['grade'])} configurações: seleção LOPO por τ de regiões nas demais páginas, desempate por sucessor e índice da grade. Escolhas: `{dict(collections.Counter(p['config'] for p in rows))}`. Diferença máxima em métricas de regiões/linhas versus o JSON anterior: {f(R['reproducao']['erro_max'],12)}; configurações idênticas: {R['reproducao']['configs_iguais']}/{n}.",
        "As variantes sobre linhas herdam score/gap/vale e a presença da política desse LOPO; não há busca de parâmetros do LayoutReader. A variante direta recebe todas as linhas e átomos de uma vez, inclusive margens; a variante + margens aplica a mesma partição geométrica do LOPO e usa a rede para ordenar dentro de cada faixa. O ordenador nas regiões humanas recebe somente suas caixas, sem classes, texto ou ordem humana. † Regiões-ouro são oráculo e não estão disponíveis em produção.", "",
        "## Modelo e interface conferida", "",
        "Checkpoint local `hantian/layoutreader`, `LayoutLMv3ForTokenClassification`, treinado para posições de leitura no ReadingBank. O nome LayoutReader também designa o trabalho original; esta experiência usa especificamente a implementação LayoutLMv3 distribuída nesse checkpoint, indicada para ordenação de caixas no ecossistema MinerU. Não se executou o MinerU nem se comparou seu pipeline completo.",
        "Fonte e licença: [cartão do checkpoint](https://huggingface.co/hantian/layoutreader) e [implementação de Hantian Pang, Faster LayoutReader based on LayoutLMv3 (2024)](https://github.com/FreeOCR-AI/layoutreader). O `README.md` local declara **CC BY-NC-SA 4.0**: uso acadêmico não comercial, com atribuição e compartilhamento pela mesma licença ao distribuir adaptações. Não se publicaram pesos nem dados. Consultou-se somente documentação pública para conferir a interface; a execução usa exclusivamente a cópia local, offline, sem instalar pacotes ou baixar modelos.",
        "Caixas normalizadas para inteiros em 0..1000, pela largura/altura da página. Sequência = CLS (0), um UNK (3) por caixa, EOS (2), caixas nulas nos especiais e máscara de atenção ativa. Recortam-se linhas 1..n e colunas 0..n−1 dos logits. **Correção necessária à referência de uso do prompt: neste checkpoint, linha i representa a posição de SAÍDA i, e a coluna j representa a caixa j da ENTRADA.** A lista de escolhas após eliminar conflitos é diretamente a sequência dos índices de entrada; aplicar `argsort` nela inverte a permutação. Cada posição escolhe a caixa de maior logit; em conflito fica o maior logit naquela coluna, as perdedoras tentam a próxima opção. Não é uma atribuição de soma máxima. Entrada embaralhada com semente fixa por página/faixa, nunca a ordem humana.",
        "Essa interpretação foi conferida com a [decodificação oficial](https://github.com/FreeOCR-AI/layoutreader/blob/main/v3/helpers.py) e com a [avaliação oficial](https://github.com/FreeOCR-AI/layoutreader/blob/main/v3/eval.py), que lê `source_texts[idx]` diretamente para cada índice retornado. Uma permutação identidade ou reversa não detecta esse erro, pois coincide com sua inversa; o controle usa entradas embaralhadas não involutórias. Não se alteraram pesos nem módulos instalados para corrigir a interface.",
        f"Controles estruturais passaram: conflito, permutação completa, limite de caixas, intercalação na régua real, página vazia e região vazia. Duas colunas densas, com {len(R['sinteticos']['colunas_densas'][0]['ordem'])} linhas e {len(R['sinteticos']['colunas_densas'])} entradas embaralhadas: τ médio correto {f(statistics.mean(t['metricas']['tau'] for t in R['sinteticos']['colunas_densas']))}; interpretando indevidamente caixa→posição, {f(statistics.mean(t['tau_interpretacao_invertida'] for t in R['sinteticos']['colunas_densas']))}. Duas colunas esparsas (apenas duas linhas muito afastadas por coluna): {sum(t['correta'] for t in R['sinteticos']['duas_colunas'])}/{len(R['sinteticos']['duas_colunas'])} ordens colunais exatas, τ médio {f(statistics.mean(t['metricas']['tau'] for t in R['sinteticos']['duas_colunas']))}; a rede prefere faixas horizontais nesse arranjo ambíguo. No sintético de {R['sinteticos']['mais_510']['n']} linhas, τ = {f(R['sinteticos']['mais_510']['tau'])}, {R['sinteticos']['mais_510'].get('linhas_fundidas',0)} fusões e máximo {R['sinteticos']['mais_510'].get('max_caixas_chamada',0)} caixas por chamada. A expansão geométrica dos grupos preservou exatamente as duas colunas.",
        f"Maior entrada real de linhas/átomos: {max(p['n_items'] for p in rows)}; páginas que precisaram do fallback >510: {sum(p['metodos']['lr_linhas']['diag'].get('excesso_510',0)>0 for p in rows)}. Acima desse limite, grupos textuais vizinhos da mesma folha/coluna da projeção viram envelopes; a rede ordena envelopes e preserva sua ordem interna. Tabelas/imagens ficam individuais. Se ainda houver grupos demais, uma hierarquia espacial em lotes limita cada chamada, ordenando envelopes e depois caixas de cada lote. Isso evita truncamento, mas proíbe intercalação entre grupos e não equivale a inferência global ilimitada. O agrupamento foi testado; a hierarquia extrema não foi necessária na amostra.", "",
        "## Desenho do híbrido e política de margens", "",
        "Escolheu-se **projeção para formar grupos; LayoutReader para ordenar os grupos**. Reproduzem-se as calhas, pontes e faixas recursivas da configuração retida; cada folha usa a XY-cut existente, e apenas linhas textuais adjacentes alinhadas são agrupadas. O script confere que expandir esses grupos inicialmente reproduz exatamente a projeção. Cada tabela/imagem permanece um grupo. Envelopes vão ao modelo; a sequência interna de cada grupo fica preservada. O desenho reduz o número de caixas, protege continuidade dentro de uma coluna e deixa a rede decidir saltos globais, inclusive entre átomos lado a lado.",
        "Regra fixa de agrupamento: sobreposição horizontal ≥70% da menor largura, diferença de margem esquerda ≤1,5 alturas de linha, razão de larguras ≤2, vão vertical entre −0,25 e 2,5 alturas de linha. Estes critérios foram escolhidos para este experimento, sem varredura; não há garantia de que cada grupo seja um parágrafo semântico. Um grupo errado continua errado: a rede não consegue desintercalar duas tabelas absorvidas no mesmo átomo, nem alterar o interior de um grupo.",
        "A baseline justa XY-cut sobre regiões-ouro recebe literalmente a política anterior: primeiro detectar marcas (todas as palavras casam com `RE_MARCACAO`), depois topo se centro <7% da altura e base <10%, depois rodapé se centro >95%; saída topo → corpo → marcas → rodapé. Topo/marcas/rodapé usam (y0,x0,índice), como a projeção original. Nas variantes neurais com política, **os limiares e a precedência são os mesmos**, mas a rede substitui a ordenação interna de cada faixa; esse efeito é intencional e não deve ser atribuído à detecção de colunas. Nas duas páginas em que LOPO retém a variante sem margens, o híbrido/+margens também ficam sem essa partição; a XY-cut justa tem política fixa em todas as páginas.", "",
        "## Réguas e inferência", "",
        "**Principal: saída real de palavras**, com IDs individuais (palavras repetidas são distintas), expandida na ordem efetivamente emitida, sem mediana. Ouro = ordem humana de regiões, linhas topo→base e palavras esquerda→direita dentro de cada região, com o mesmo agrupador anterior. Palavras sem dono continuam na predição, mas ficam fora da métrica sem referência. τ, sucessor e ARD são médias macro por página. Sucessor de palavras pode ficar alto mesmo ao inverter tabelas completas; por isso se mostram também linhas e a fração de regiões cujas palavras reaparecem em mais de um trecho. A fragmentação estrita trata palavra sem dono como interrupção.",
        "**Secundárias: linhas e regiões por mediana dos ranks**, idênticas ao relatório anterior; não são sequências reais de linhas previstas quando estas cruzam uma região. Nas variantes regiões-ouro a ordem de regiões é direta, sem mediana. Regiões vazias recebem somente um diagnóstico geométrico na régua secundária; páginas/réguas com menos de dois elementos não recebem acerto perfeito fictício.",
        f"IC percentil 95%: {R['parametros']['bootstrap']} reamostras de **veículos inteiros**, semente {R['parametros']['semente']}; veículo = prefixo de `page_id` até a primeira barra. Cada sorteio inclui todas as páginas de cada veículo sorteado, conservando a média macro por página. Comparações usam os mesmos sorteios pareados. São IC **condicionais às configurações LOPO retidas**; a seleção não foi refeita dentro do bootstrap. A tarefa mantém o LOPO anterior, com possível parentesco entre páginas do mesmo veículo; não representa teste independente por veículo.",
        f"Wilcoxon bilateral pareado com `zero_method='pratt'`, aproximação normal e diferenças arredondadas a doze casas para evitar falso desempate numérico. Mostram-se W/p por página e p adicional sobre diferenças médias por veículo; Pratt por página não resolve dependência de layout. Holm abrange todas as {len(R['testes'])} comparações registradas nesta execução. Nenhum teste prova equivalência nem corrige o histórico de desenvolvimento.", "",
        "## Tabela principal — palavras na sequência de saída", "",
        *tabela(S,"palavras",custo), "", "† Informação humana indisponível em produção. Latência inclui preparação, modelo/decodificação e expansão; não inclui extração do PDF, detector nem cálculo de métricas.", "",
        "## Réguas secundárias", "", "### Linhas projetadas", "", *tabela(S,"linhas"), "",
        "### Regiões", "", *tabela(S,"regioes"), "",
        "## Estratos com o mesmo metadado do relatório anterior", "",
        "`stats.n_colunas` serve somente para estratificar e nunca entra no modelo. É estimativa geométrica, com erros conhecidos: RJ Legislativo/Manaus/Caxias visualmente complexos podem estar em uma coluna; AC/MS entram em multicoluna por campos do cabeçalho. Mantê-lo permite comparar os relatórios, mas não constitui anotação independente de colunas.", ""]
    for g in ("uma","multi"):
        e = R["estratos"][g]
        txt += [f"### {'Uma coluna' if g == 'uma' else 'Multicoluna'}: {e['n']} páginas, {e['veiculos']} veículos", "",
                *tabela(e["resumo"],"palavras"), "", "| Método | τ linhas | Sucessor linhas | ARD linhas | τ regiões | Regiões fragmentadas |", "|---|---:|---:|---:|---:|---:|"]
        for m in NOMES:
            a = e["resumo"][m]
            txt.append(f"| {NOMES[m]} | {cel(a['linhas']['tau'])} | {cel(a['linhas']['sucessor'],True)} | {cel(a['linhas']['ard'])} | {cel(a['regioes']['tau'])} | {cel(a['fragmentacao']['fracao'],True)} |")
        txt.append("")
    txt += ["## Diferenças pareadas", "", "### Palavras: contra XY-cut pura, justa e projeção", "",
        "| Variante | Referência | Métrica | Δ médio (IC por veículo) | Ganha/empata/perde | W Pratt | p página | p veículo | p Holm |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for t in R["testes"]:
        if t["regua"] != "palavras":
            continue
        txt.append(f"| {NOMES[t['metodo']]} | {NOMES[t['base']]} | {t['metrica']} | {f(t['delta'])} [{f(t['ic95'][0])}; {f(t['ic95'][1])}] | {t['ganha']}/{t['empata']}/{t['perde']} | {f(t['W'],1)} | {f(t['p'],6)} | {f(t['p_veiculo'],6)} | {f(t['p_holm'],6)} |")
    txt += ["", "### Linhas e regiões: τ e sucessor", "", "| Variante | Referência | Régua/métrica | Δ (IC por veículo) | p Pratt página | p veículo | p Holm |", "|---|---|---|---:|---:|---:|---:|"]
    for t in R["testes"]:
        if t["regua"] == "palavras" or t["metrica"] == "ard":
            continue
        txt.append(f"| {NOMES[t['metodo']]} | {NOMES[t['base']]} | {t['regua']}/{t['metrica']} | {f(t['delta'])} [{f(t['ic95'][0])}; {f(t['ic95'][1])}] | {f(t['p'],6)} | {f(t['p_veiculo'],6)} | {f(t['p_holm'],6)} |")
    txt += ["", "ARD das réguas secundárias, W e contagens de todas as comparações também constam no checkpoint interno.", "",
        "## As falhas anteriores foram corrigidas? Página a página", "",
        "Estas páginas são a união de ‘Onde o plano perde mais’ nas duas réguas do relatório anterior. Corrigida = a variante atinge simultaneamente a referência justa em τ de palavras e sucessor de linhas, sem aumentar a fragmentação; é um critério relativo, não prova de leitura perfeita.", ""]
    por_pid = {p["page_id"]:p for p in rows}
    for pid in o.NOTAS_INSPECAO:
        p = por_pid[pid]
        ms = p["metodos"]
        txt += [f"### `{pid}`", "", "| Método | τ palavras | Sucessor palavras | τ linhas | Sucessor linhas | τ regiões | Regiões fragmentadas |", "|---|---:|---:|---:|---:|---:|---:|"]
        for m in NOMES:
            a = ms[m]
            txt.append(f"| {NOMES[m]} | {f(a['palavras']['tau'])} | {f(100*a['palavras']['sucessor'],1)}% | {f(a['linhas']['tau'])} | {f(100*a['linhas']['sucessor'],1)}% | {f(a['regioes']['tau'])} | {f(100*a['diag']['fracao'],1)}% |")
        txt += ["", "Diagnóstico geométrico anterior: "+o.NOTAS_INSPECAO[pid].replace("**Inspeção:** ",""), ""]
        for m in ("lr_linhas","lr_margens","hibrido"):
            a,b = ms[m],ms["xy_margens"]
            ok = (a["palavras"]["tau"] >= b["palavras"]["tau"]-1e-12
                  and a["linhas"]["sucessor"] >= b["linhas"]["sucessor"]-1e-12
                  and a["diag"]["fracao"] <= b["diag"]["fracao"]+1e-12)
            txt.append(f"- {NOMES[m]}: **{'atinge a referência justa nos critérios' if ok else 'não corrige completamente'}**; Δτ palavras versus projeção = {f(a['palavras']['tau']-ms['projecao']['palavras']['tau'])}; regiões ainda fragmentadas: `{a['diag']['fragmentadas']}`.")
        txt += ["", "Ordem humana: `"+" → ".join(p["gt_r"])+"`. Projeção: `"+" → ".join(p["ordens_r"]["projecao"])+"`. LayoutReader direto: `"+" → ".join(p["ordens_r"]["lr_linhas"])+"`. Híbrido: `"+" → ".join(p["ordens_r"]["hibrido"])+"`.", ""]
        especiais = p["campos"]
        if especiais:
            txt += ["Campos de cabeçalho/rodapé: posição ouro → projeção / LR direto / híbrido (zero = primeira).", ""]
            for c in especiais:
                txt.append(f"- `{c['id']}` ({c['classe']}), ‘{c['texto']}’: {c['ouro']} → {c['projecao']} / {c['lr_linhas']} / {c['hibrido']}.")
            txt.append("")
    txt += ["## Regressões novas e efeito da granularidade", "",
        "As maiores regressões do LayoutReader direto contra a projeção não são somente os casos anteriormente escolhidos. A tabela abaixo é ordenada automaticamente por Δτ de palavras, sem excluir páginas com falhas. O contrafactual sobre regiões humanas troca a granularidade e as bordas conjuntamente; não identifica sozinho uma causa.", "",
        "| Página | Caixas de entrada | Grupos híbridos | τ projeção | τ LR direto | τ híbrido | τ LR regiões-ouro | Fragmentação LR direto |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    piores = sorted(rows,key=lambda p:p["metodos"]["lr_linhas"]["palavras"]["tau"]-p["metodos"]["projecao"]["palavras"]["tau"])[:6]
    for p in piores:
        a = p["metodos"]
        txt.append(f"| `{p['page_id']}` | {p['n_items']} | {a['hibrido']['diag']['grupos']} | {f(a['projecao']['palavras']['tau'])} | {f(a['lr_linhas']['palavras']['tau'])} | {f(a['hibrido']['palavras']['tau'])} | {f(a['lr_ouro']['palavras']['tau'])} | {f(100*a['lr_linhas']['diag']['fracao'],1)}% |")
    mg = next(p for p in rows if p["page_id"] == "official_diary_mg/executive_official_diary_2021-07-06.pdf#p28")
    a = mg["metodos"]
    txt += ["", f"No caso de MG acima, as {mg['n_items']} caixas cabem no limite do modelo, mas a decodificação direta exige {a['lr_linhas']['diag'].get('rodadas_conflito',0)} rodadas de conflito e o sucessor de linhas cai a {f(100*a['lr_linhas']['linhas']['sucessor'],1)}%. O híbrido reduz a entrada a {a['hibrido']['diag']['grupos']} grupos, com sucessor de linhas {f(100*a['hibrido']['linhas']['sucessor'],1)}%; sobre as {mg['n_regioes']} regiões humanas, chega a {f(100*a['lr_ouro']['linhas']['sucessor'],1)}%. Ficar abaixo de 510 evita estouro de contexto, mas não garante qualidade. Estes números sugerem sensibilidade à granularidade e a páginas densas; não justificam escolher um novo limiar de fusão retrospectivamente.", ""]
    sl = teste("hibrido","projecao","linhas","sucessor")
    multi = R["estratos"]["multi"]["resumo"]
    txt += [f"O híbrido reduz fragmentação média {f(100*S['projecao']['fragmentacao']['fracao']['media'],1)}% → {f(100*S['hibrido']['fragmentacao']['fracao']['media'],1)}% e aumenta sucessor de linhas {f(100*media('projecao','linhas','sucessor'),1)}% → {f(100*media('hibrido','linhas','sucessor'),1)}%. Contudo Δ sucessor tem IC por veículo [{f(100*sl['ic95'][0],1)}; {f(100*sl['ic95'][1],1)}] pontos percentuais, Pratt por veículo p = {f(sl['p_veiculo'],6)} e p Holm = {f(sl['p_holm'],6)}; não há evidência robusta de melhora geral. No estrato multicoluna, τ de palavras da projeção {f(multi['projecao']['palavras']['tau']['media'])} é maior que o do híbrido {f(multi['hibrido']['palavras']['tau']['media'])}.", "",
        "## Custo e limites do escopo", "",
        f"CPU em {R['modelo']['dtype']}, {R['modelo']['threads']} threads de operações e uma thread interop; torch {R['modelo']['torch']}, transformers {R['modelo']['transformers']}. {R['modelo']['parametros']} parâmetros; arquivo de pesos {R['modelo']['pesos_bytes']} bytes ({f(R['modelo']['pesos_bytes']/1024**2,1)} MiB), arquivos diretos da pasta {R['modelo']['arquivos_bytes']} bytes. Inicialização do modelo neste processo: {f(R['modelo']['carga_ms'],1)} ms, separada da inferência; o arquivo pode estar no cache do sistema operacional. Aquecimento com o controle sintético; uma medição por variante/página, sem cache de inferência nas latências abaixo. A GPU permaneceu excluída do processo.", "",
        "| Método | Média ms | Mediana ms | p95 ms | Máximo ms | Rede ms, média |", "|---|---:|---:|---:|---:|---:|"]
    for m in NOMES:
        a = custo[m]
        txt.append(f"| {NOMES[m]} | {f(a['media'],1)} | {f(a['p50'],1)} | {f(a['p95'],1)} | {f(a['max'],1)} | {f(a['rede_media'],1)} |")
    txt += ["", f"A melhor variante sem ouro custa {f(custo[melhor]['media']/custo['projecao']['media'],1)} vezes o ordenador geométrico nesta medição. Isso não é custo fim a fim: palavras e detector estão em cache. CPU/disco são compartilhados com outras tarefas, incluindo um treino ativo; faltam repetições em máquina ociosa e benchmark de extração/detecção.", "",
        "## Limitações, vieses e recomendação", "",
        "- Amostra pequena, de conveniência e com famílias de layout repetidas. Bootstrap agrupado melhora a consideração dessa dependência, mas poucos exemplos por veículo e LOPO por página impedem alegar generalização a novos diários.",
        "- **O LayoutReader não foi afinado nem treinado nestas páginas**, vantagem de validade frente à projeção cujo desenho foi desenvolvido inspecionando este ouro. Porém a preparação score/gap e a política da variante neural/híbrida vêm do LOPO desenvolvido nesta amostra; isso não transforma o pipeline inteiro em teste externo sem ajuste. Não foi auditada eventual sobreposição da pré-formação com documentos brasileiros.",
        "- As caixas humanas foram corrigidas a partir de pré-anotação automática: há viés de ancoragem na segmentação e classes. A ordem de linhas/palavras dentro das regiões é derivada geometricamente, não anotada de forma independente; tabelas não têm ouro de estrutura de células. Há favorecimento estrutural dos métodos que recebem regiões-ouro.",
        "- As medianas podem esconder texto intercalado; o veredito usa palavras reais, fragmentação e continuidade de linhas. Sucessor de palavras também é dominado por pares internos e não basta isoladamente. Imagens puras não são avaliadas; não há OCR, texto digital ausente nem teste de impacto em RI.",
        "- Um ordenador só troca caixas inteiras. Não conserta absorção de cabeçalho por tabela, duas instâncias fundidas, texto interno fora de ordem ou um grupo híbrido mal formado. O plano ainda requer átomos bem delimitados; o teste sobre regiões humanas é um diagnóstico para separar segmentação de ordenação.",
        "- Híbrido e tratamento >510 são escolhas novas de engenharia, sem treino da rede, mas precisam de validação fora desta amostra. Não foram escolhidos depois de comparar diversas configurações no teste. A inferência estatística continua exploratória e condicional à seleção anterior.", "",
        f"**Recomendação:** {veredito}. A variante de melhor τ real é {NOMES[melhor]}, mas a decisão de produção precisa considerar seus erros página a página, fragmentação e o custo acima. Congelar variantes e avaliar ouro novo de veículos separados, desenhado sem pré-anotação; manter XY-cut com a mesma política como baseline. Este relatório não modifica o pipeline nem constitui decisão metodológica final do TCC.", "",
        "## Reprodução, retomada e conferência", "", "```powershell",
        "venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_layoutreader.py --do-zero --conferir",
        "```", "",
        "Sem `--do-zero`, o script retoma checkpoints somente se hashes e parâmetros coincidirem. O próprio Markdown guarda métricas por página, sequências reais, grade, testes, tempos e hashes num comentário HTML comprimido; não são necessários arquivos auxiliares. `--conferir` relê esse objeto e exige que todo o corpo do relatório seja exatamente a renderização dele, comparando ainda tabelas impressas e, se havia execução completa anterior, métricas/sequências determinísticas (tempos variam). Os hashes das entradas/modelo/fontes são conferidos antes e depois.", "",
        f"Conferência de hashes: {R['verificacoes']['hashes_preservados']}; reprodução por página: {R['verificacoes']['reproducao']}; comparação com execução anterior: {R['verificacoes']['reexecucao']}. O relatório é escrito pelo script; todos os números derivam desta execução.", ""]
    # Separar paragrafos sem quebrar tabelas, listas ou o comando PowerShell.
    final, codigo = [], False
    for linha in txt:
        anterior = final[-1] if final else ""
        especial = lambda s:s.startswith(("#","|","- ","```")) or bool(re.match(r"^\d+\.",s))
        if linha and anterior and not codigo and not especial(linha) and not especial(anterior):
            final.append("")
        final.append(linha)
        if linha.startswith("```"):
            codigo = not codigo
    return "\n".join(final)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--somente-sinteticos", action="store_true")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--semente", type=int, default=42)
    args = ap.parse_args()
    if args.threads < 1 or args.bootstrap < 2000:
        raise ValueError("Threads positivas e pelo menos 2000 bootstraps")
    if args.somente_sinteticos:
        lr = Ordenador(args.threads)
        print(json.dumps(sinteticos(lr), ensure_ascii=False, indent=2))
        return
    H = hashes()
    params = {"threads":args.threads,"bootstrap":args.bootstrap,"semente":args.semente}
    anterior = ler_cache()
    valido = anterior and anterior.get("hashes") == H and anterior.get("parametros") == params
    R = anterior if valido and not args.do_zero else {
        "hashes":H,"parametros":params,"grade_paginas":[],"paginas":[]}
    ps, cs = justo.preparar(), o.grade()
    # Condicoes de borda sao contadas pelo carregador, sem assert para vazios.
    R["grade"] = [c.id for c in cs]
    completos = {p["page_id"] for p in R["grade_paginas"]}
    for j,q in enumerate(ps):
        pid = q["p"]["page_id"]
        if pid not in completos:
            R["grade_paginas"].append({"page_id":pid,"metricas":grade_pagina(q,cs)})
            gravar(R,parcial(R))
        print(f"[grade {j+1}/{len(ps)}] {pid}",flush=True)
    R["grade_paginas"].sort(key=lambda p:p["page_id"])
    ids = selecionar(R,cs)
    with ORIGINAL.open(encoding="utf-8") as fobj:
        antigo = json.load(fobj)
    orig = {p["page_id"]:p for p in antigo["sequencias_cv"]}
    if any(cs[i].id != orig[q["p"]["page_id"]]["config"] for q,i in zip(ps,ids)):
        raise ValueError("Configurações LOPO não reproduzem o experimento anterior")
    lr = Ordenador(args.threads)
    R["modelo"] = lr.info
    R["sinteticos"] = sinteticos(lr)
    completos = {p["page_id"] for p in R["paginas"]}
    for j,(q,i) in enumerate(zip(ps,ids)):
        pid = q["p"]["page_id"]
        if pid not in completos:
            metodos = {m:prever(q,cs[i],m,lr) for m in NOMES}
            ordens = {}
            for m,r in metodos.items():
                if m in ("xy_ouro","xy_margens","lr_ouro","lr_ouro_margens"):
                    items = q["p"]["bounding_boxes"]
                ranks = {k:v for v,k in enumerate(r["seq"])}
                bs = {a["id"]:a["bbox"] for a in q["p"]["bounding_boxes"]}
                if all(q["reg_words"].values()):
                    ordens[m] = sorted(q["gt_r"],key=lambda rid:(statistics.median(ranks[k] for k in q["reg_words"][rid]),bs[rid][1],bs[rid][0],rid))
                else:
                    ordens[m] = []
            campos = [{"id":r["id"],"classe":r.get("classe"),"texto":" ".join(r.get("text","").split())[:120],
                "ouro":q["gt_r"].index(r["id"]),**{m:ordens[m].index(r["id"]) if r["id"] in ordens[m] else None
                    for m in ("projecao","lr_linhas","hibrido")}}
                for r in q["p"]["bounding_boxes"] if r.get("classe") in ("cabecalho","rodape")]
            R["paginas"].append({"page_id":pid,"veiculo":pid.split("/",1)[0],
                "config":cs[i].id,"colunas":q["p"].get("stats",{}).get("n_colunas",1),
                "n_regioes":len(q["gt_r"]),"n_linhas":len(q["gt_l"]),
                "n_items":len(preparar_items(q,cs[i])),"auditoria":q["auditoria"],
                "metodos":metodos,"ordens_r":ordens,"gt_r":q["gt_r"],"campos":campos})
            gravar(R,parcial(R))
        print(f"[variantes {j+1}/{len(ps)}] {pid}",flush=True)
    R["paginas"].sort(key=lambda p:p["page_id"])
    rows = R["paginas"]
    erros = []
    antigos = {p["page_id"]:p for p in antigo["por_pagina"]}
    for p in rows:
        for m,ma in (("projecao","plano_cv"),("xy_ouro","xy_ouro")):
            for regua in ("regioes","linhas"):
                for k in METRICAS:
                    erros.append(abs(p["metodos"][m][regua][k]-antigos[p["page_id"]]["metodos"][ma][regua][k]))
    R["reproducao"] = {"erro_max":max(erros),"configs_iguais":len(rows)}
    if max(erros) > 1e-12:
        raise ValueError("Métricas antigas não reproduzidas")
    S,B,gi = estatisticas(rows,args.bootstrap,args.semente)
    R["resumo"],R["custo"] = S,resumo_custo(rows)
    R["testes"] = testes(rows,S,B,gi)
    R["veiculos"] = sorted({p["veiculo"] for p in rows})
    R["estratos"] = {}
    for g,teste in (("uma",lambda p:p["colunas"]==1),("multi",lambda p:p["colunas"]>1)):
        sub = [p for p in rows if teste(p)]
        a,_,_ = estatisticas(sub,args.bootstrap,args.semente)
        R["estratos"][g] = {"n":len(sub),"veiculos":len({p["veiculo"] for p in sub}),"resumo":a}
    if hashes() != H:
        raise RuntimeError("Entradas/fontes/modelo mudaram durante a execução; resultados permanecem parciais")
    reexec = "primeira execução completa"
    if anterior and anterior.get("completo") and args.do_zero:
        # Comparar somente se entradas/modelo/parametros da execucao sao iguais.
        if anterior.get("hashes")==H and anterior.get("parametros")==params:
            for a,b in zip(rows,anterior["paginas"]):
                for m in NOMES:
                    for k in (*REGUAS,"seq"):
                        if a["metodos"][m][k] != b["metodos"][m][k]:
                            raise ValueError(f"Reexecução não determinística: {a['page_id']}/{m}/{k}")
            reexec = "métricas e sequências idênticas à execução completa anterior"
        else:
            reexec = "execução anterior com fontes/parâmetros diferentes"
    R["verificacoes"] = {"hashes_preservados":True,"reproducao":True,"reexecucao":reexec}
    R["completo"] = True
    gravar(R,relatorio(R))
    salvo = ler_cache()
    texto = SAIDA.read_text(encoding="utf-8").split(f"\n<!-- {MARCADOR}",1)[0]
    if salvo is None or texto != relatorio(salvo):
        raise ValueError("Relatório difere do objeto relido")
    tabela_saida = tabela(salvo["resumo"],"palavras",salvo["custo"])
    if "\n".join(tabela_saida) not in texto:
        raise ValueError("Tabela impressa difere do relatório")
    print("\n".join(tabela_saida))
    print(f"[OK] {len(rows)} páginas; CPU; grade/relatório/hashes conferidos; {reexec}.",flush=True)


if __name__ == "__main__":
    main()
