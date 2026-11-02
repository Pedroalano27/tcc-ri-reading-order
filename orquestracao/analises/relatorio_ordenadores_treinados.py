"""Fecha a comparacao e audita os ordenadores sem caixas finas, so em CPU.

Le as avaliacoes existentes, pareia a cobertura do Gemini e importa a regua
de erros_ponta_a_ponta pela bancada. Nao treina, nao altera scripts existentes,
nao abre o Label Studio e nao toca em dados. Guarda diagnosticos por pagina e
logits retomaveis em resultados/ordenadores_treinados_sem_caixas/revisao_04.

Uso da raiz: venv/Scripts/python.exe -B
 orquestracao/analises/relatorio_ordenadores_treinados.py --diagnosticar
Sem a opcao, regenera o relatorio com os resultados e caches ja disponiveis.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import argparse
import bisect
import collections
import gc
import hashlib
import itertools
import json
import os
import re
import statistics as st
import time
from datetime import datetime

os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1", HF_DEACTIVATE_ASYNC_LOAD="1",
    OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
    TOKENIZERS_PARALLELISM="false")
import numpy as np
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from orquestracao.analises import treinar_sem_caixas as t
from src.models import layoutlm_sucessor as s
from src.models.layoutlm_ordem import normalizar_bbox
from src.eval import protocolo

OUT = t.OUT / "revisao_04"
MD = RAIZ / "resultados/ordenadores_treinados_sem_caixas.md"
JSON = OUT / "relatorio.json"
COLS = ("tau", "quebras", "fid12", "sucessor_linhas", "piso_interno")
DECODERS = ("gulosa", "feixe4", "cadeias050", "cadeias010", "cadeias000", "posicao")


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def salvar(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def chave(pid):
    return hashlib.sha256(pid.encode()).hexdigest()[:24]


def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def media(rows, k):
    vals = [r["metricas"][k] for r in rows if r["metricas"].get(k) is not None]
    return st.mean(vals) if vals else None


def resumo(rows, base):
    br = {p["page_id"]: p for p in base}
    tests = {}
    for k in ("tau", "quebras"):
        groups = collections.defaultdict(list)
        for p in rows:
            if p["page_id"] in br:
                a, c = p["metricas"].get(k), br[p["page_id"]]["metricas"].get(k)
                if a is not None and c is not None:
                    groups[p["uf"]].append(a-c)
        ds = {uf: st.mean(v) for uf, v in groups.items()}
        tests[k] = {**e.pratt(list(ds.values())), "veiculos": len(ds), "deltas": ds}
    return {"n": len(rows), "veiculos": len({p["uf"] for p in rows}),
            **{k: media(rows, k) for k in COLS}, "wilcoxon": tests}


def base_de(R, r):
    rep = "linhas" if r["representacao"] == "caixas_finas" else r["representacao"]
    return R["resultados"].get(f"regra_colunas__{rep}__{r['bancada']}", {}).get("paginas", [])


def tabela(txt, R, rs, subset=None, grupos=False):
    txt += ["", "| Representação | Ordenador | Grupo | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas | n | p τ / p quebras por veículo |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    saida = {}
    for r in sorted(rs, key=lambda z: (z["representacao"], z["ordenador"])):
        rows = [p for p in r["paginas"] if subset is None or p["page_id"] in subset]
        if subset is not None and {p["page_id"] for p in rows} != subset:
            continue
        for group, flag in (("todos", None), ("vistos", True), ("não vistos", False)) if grupos else (("todos", None),):
            rr = [p for p in rows if flag is None or p["visto_treino"] == flag]
            if not rr:
                continue
            z = resumo(rr, base_de(R, r))
            nome = r["ordenador"] + (" (parcial)" if not r.get("completa", True) else "")
            txt.append(f"| {r['representacao']} | {nome} | {group} | {f(z['tau'])} | {f(z['quebras'],2)} | {f(100*z['fid12'],1) if z['fid12'] is not None else '—'}% | {f(100*z['sucessor_linhas'],1) if z['sucessor_linhas'] is not None else '—'}% | {z['n']} | {f(z['wilcoxon']['tau']['p'],6)} / {f(z['wilcoxon']['quebras']['p'],6)} |")
            saida[f"{r['ordenador']}__{r['representacao']}__{group}"] = z
    return saida


def fila():
    saida = []
    for p in sorted((RAIZ / "orquestracao/noite_0410/gpu").glob("*.sh")):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"(?:^|\n)N=([^;\s]+)", text)
        states = [x for x in ("rodando", "done", "falhou") if p.with_suffix("."+x).exists()]
        log = p.with_suffix(".log")
        lg = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        err = [l.strip() for l in lg.splitlines() if "Error:" in l or "Exception:" in l]
        saida.append({"roteiro": p.name, "modelo": m.group(1) if m else None,
            "estado": ", ".join(states) or "aguarda fila", "log_bytes": log.stat().st_size if log.exists() else 0,
            "erro": err[-1] if err else "", "ultimas_linhas": lg.splitlines()[-4:], "sha256": t.sha(p)})
    return saida


def inventario(R):
    ff = fila()
    out = []
    for p in sorted(t.OUT.glob("*/treino.json")):
        if p.parent.name.startswith("fumaca"):
            continue
        info = ler(p)
        cfg = info["config"]
        nome, rep = cfg["nome"], cfg["representacao"]
        pred = []
        for bench in b.BANCADAS:
            path = t.OUT / "pred" / f"{nome}__{rep}__{bench}.jsonl"
            n = sum(1 for _ in b.jsonl(path)) if path.exists() else 0
            rr = R["resultados"].get(f"{nome}__{rep}__{bench}", {})
            pred.append({"bancada": bench, "arquivo": str(path.relative_to(RAIZ)), "n_pred": n,
                "n_avaliadas": len(rr.get("paginas", [])), "completa": rr.get("completa", False)})
        out.append({"nome": nome, "representacao": rep, "info": info,
            "checkpoints": [{"arquivo": str(x.relative_to(RAIZ)), "bytes": x.stat().st_size}
                for x in sorted(p.parent.glob("*.pt"))], "predicoes": pred,
            "rodando": any(q["modelo"] == nome and "rodando" in q["estado"] for q in ff)})
    return out, ff


def ancoras(R):
    """Reconstroi as sequencias da regra e compara com a execucao historica."""
    hist = {r["page_id"]: r for r in ler(e.JSON)["paginas"] if r["coorte"] == "v4"}
    rows = []
    for obj, p in b.paginas("golden_v4", "linhas"):
        pred, _ = b.prever(p, obj["palavras"], "regra_colunas")
        exp = b.expansoes(obj, p)
        seq = [k for uid in pred for k in exp[uid]]
        old = hist[p["page_id"]]["metodos"]
        if seq != old["P2"]["seq"]:
            raise ValueError("PARE: ancora diverge na sequencia: " + p["page_id"])
        rows.append({"page_id": p["page_id"], "P2": {k: old["P2"][k] for k in ("tau", "quebras")},
                     "P1m": {k: old["P1m"][k] for k in ("tau", "quebras")}})
    if len(rows) != 44 or len(hist) != 44:
        raise ValueError("PARE: coorte de ancora diferente")
    z = {m: {k: st.mean(x[m][k] for x in rows) for k in ("tau", "quebras")} for m in ("P2", "P1m")}
    for m, tau, quebras in (("P2", .986, 6.05), ("P1m", .952, 8.93)):
        if abs(z[m]["tau"]-tau) > .006 or abs(z[m]["quebras"]-quebras) > .0051:
            raise ValueError("PARE: ancora nao reproduzida")
    z.update(n=len(rows), sequencias_identicas=len(rows), fonte=str(e.JSON.relative_to(RAIZ)))
    return z


def ruido(p, gt):
    """Mede contradicao de pares vizinhos; nao redefine a regua de eficacia."""
    rank = {w: j for j, w in enumerate(gt)}
    us = {u["id"]: u for u in p["bounding_boxes"]}
    pairs = bad = inversoes = cruzados = fronteiras = 0
    exemplos = []
    for a, c in zip(p["ordens"]["stream"], p["ordens"]["stream"][1:]):
        if us[a]["tipo"] != "texto" or us[c]["tipo"] != "texto":
            continue
        aa, cc = ([rank[w] for w in us[x]["ks"] if w in rank] for x in (a,c))
        if not aa or not cc:
            continue
        pairs += 1
        iv = sum(bisect.bisect_left(sorted(cc), w) for w in aa)
        inversoes += iv
        cruzados += len(aa)*len(cc)
        contradiz = iv > 0
        bad += contradiz
        # Descontinuidade da fronteira e distinta de inversao entre palavras.
        fronteiras += max(aa)+1 != min(cc)
        if contradiz and len(exemplos) < 3:
            exemplos.append({"a": a, "b": c, "intervalo_a": [min(aa),max(aa)],
                             "intervalo_b": [min(cc),max(cc)], "pares_invertidos": iv})
    return {"pares_vizinhos": pairs, "pares_contraditorios": bad, "pares_palavras": cruzados,
        "pares_palavras_invertidos": inversoes, "fronteiras_nao_contiguas": fronteiras,
        "exemplos": exemplos}


def metadados():
    out = {}
    for bench in b.BANCADAS:
        rows = []
        for obj, p in b.paginas(bench, "linhas"):
            rows.append({"page_id": p["page_id"], "uf": p["uf"], "unidades": len(p["bounding_boxes"]),
                "palavras": len(obj["gt_w"]), "colunas": p["stats"].get("n_colunas"),
                "tabelas": sum(u["tipo"] == "tabela" for u in p["bounding_boxes"]),
                "imagens": sum(u["tipo"] == "imagem" for u in p["bounding_boxes"]),
                "ruido": ruido(p, obj["gt_w"])})
        out[bench] = rows
    return out


def auditar_dados(meta):
    splits = protocolo.carregar_splits()
    humanos = {p["page_id"] for bench in ("golden_v4", "golden_v3_novo") for p in meta[bench]}
    test = {p["page_id"] for p in meta["teste_silver"]}
    ids_rep, dados = {}, {}
    for rep in b.REPS:
        refs = t.indice(rep, "treino")
        val = t.indice(rep, "validacao")
        ids = {r[2] for r in refs}
        ids_rep[rep] = ids
        dados[rep] = {"treino": len(refs), "validacao": len(val), "treino_humano": len(ids & humanos),
            "treino_teste": len(ids & test), "treino_validacao": len(ids & {r[2] for r in val}),
            "ids_sha256": hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()}
    totais = collections.Counter()
    por_uf = collections.defaultdict(collections.Counter)
    geos = collections.defaultdict(list)
    unidades = fora = deg = multi = maxn = 0
    for ref in t.indice("linhas", "treino"):
        # Mantem ks para a auditoria; nao chama pagina(), que os remove.
        with open(ref[0], "rb") as fh:
            fh.seek(ref[1]); p = json.loads(fh.readline().decode("utf-8"))
        gt = range(sum(len(u["ks"]) for u in p["bounding_boxes"]))
        ru = ruido(p, gt)
        for k,v in ru.items():
            if isinstance(v,int):
                totais[k] += v; por_uf[p["uf"]][k] += v
        n = len(p["bounding_boxes"])
        multi += n > 510; maxn = max(maxn,n)
        W,H = p["dimensions"]["width"],p["dimensions"]["height"]
        for u in p["bounding_boxes"]:
            if u["tipo"] != "texto":
                continue
            unidades += 1
            bb = u["bbox"]; nb = normalizar_bbox(bb,W,H)
            fora += bb[0]<0 or bb[1]<0 or bb[2]>W or bb[3]>H
            deg += nb[0] == nb[2] or nb[1] == nb[3]
            geos["largura_norm"].append((bb[2]-bb[0])/W)
            geos["altura_norm"].append((bb[3]-bb[1])/H)
            geos["razao_largura_altura"].append((bb[2]-bb[0])/max(.01,bb[3]-bb[1]))
            geos["altura_grade1000"].append(nb[3]-nb[1])
    return {"splits": {k:splits[k] for k in ("treino","validacao","teste","referencia")},
        "particoes": dados, "mesmos_ids_todas_representacoes": all(v == ids_rep["linhas"] for v in ids_rep.values()),
        "ruido_treino_linhas": dict(totais), "ruido_por_veiculo": {k:dict(v) for k,v in por_uf.items()},
        "geometria_treino": {"linhas": unidades, "fora_pagina": fora, "degeneradas_grade1000": deg,
            "paginas_acima510": multi, "max_unidades": maxn,
            "quantis": {k: np.percentile(v,[10,50,90]).tolist() for k,v in geos.items()}}}


def validacao():
    for uf in protocolo.carregar_splits()["validacao"]:
        pp, wp = (b.UNIDADES / "linhas" / (uf+ext) for ext in (".jsonl", ".palavras.jsonl"))
        cp = b.UNIDADES / "colunas_margens" / (uf+".jsonl")
        for p,obj,c in itertools.zip_longest(b.jsonl(pp),b.jsonl(wp),b.jsonl(cp)):
            if p is None or obj is None or c is None or not p["page_id"] == obj["page_id"] == c["page_id"]:
                raise ValueError("Shards RN divergentes")
            yield {**obj,"uf":uf,"representacoes":{"colunas_margens":c}},p


def classe(a,c,p,estruturas):
    """Tipologia geometrica explicita; proxy, sem anotacao humana de transicoes."""
    margens = {"cabecalho","rodape","quadro_externo"}
    if estruturas.get(a["id"]) in margens or estruturas.get(c["id"]) in margens:
        return "margens/quadros"
    aa, cc = a["tipo"],c["tipo"]
    atomos = {"tabela","imagem"}
    if aa in atomos and cc in atomos:
        return "entre tabelas/imagens"
    if cc in atomos:
        return "entrada tabela/imagem"
    if aa in atomos:
        return "saída tabela/imagem"
    x,y,X,Y = a["bbox"]; xx,yy,XX,YY = c["bbox"]
    W,H = p["dimensions"]["width"],p["dimensions"]["height"]
    ov = (min(X,XX)-max(x,xx))/max(.001,min(X-x,XX-xx))
    if ov >= .5 and yy >= y and yy-Y <= max(4*max(Y-y,YY-yy),.04*H):
        return "linha seguinte mesma coluna"
    if xx > X-.01*W and yy < y:
        return "fim coluna → topo próxima"
    return "mudança de zona/outros"


def mapear_estruturas(obj,p):
    donor = {}
    for u in obj.get("representacoes",{}).get("colunas_margens",{}).get("bounding_boxes",[]):
        for k in u["ks"]:
            donor[k] = u["tipo"]
    return {u["id"]: collections.Counter(donor[k] for k in u["ks"] if k in donor).most_common(1)[0][0]
        for u in p["bounding_boxes"] if any(k in donor for k in u["ks"])}


def diagnostico_pagina(lp,pos,p,obj):
    o = protocolo.ordem_entrada(p)
    bs = p["bounding_boxes"]
    n = len(o)
    ids = [bs[j]["id"] for j in o]
    idx = {uid:j for j,uid in enumerate(ids)}
    ref = p["ordens"]["stream"]
    caminhos = {
        "gulosa": s.decodificar(lp,n,1), "feixe4": s.decodificar(lp,n,4),
        "cadeias050": s.decodificar_cadeias(lp,pos,n,.5),
        "cadeias010": s.decodificar_cadeias(lp,pos,n,.1),
        "cadeias000": s.decodificar_cadeias(lp,pos,n,0.),
        "posicao": sorted(range(n),key=lambda j:float(pos[j]))}
    ordens = {k:[ids[j] for j in cam] for k,cam in caminhos.items()}
    structural = mapear_estruturas(obj,p)
    mapa = {u["id"]:u for u in bs}
    geo = s.features_geo(p,o)
    counts = collections.defaultdict(collections.Counter)
    feats = collections.defaultdict(list)
    adjacency = {k:dict(zip(v,v[1:])) for k,v in ordens.items()}
    for a,c in zip(ref,ref[1:]):
        typ = classe(mapa[a],mapa[c],p,structural)
        i,j = idx[a],idx[c]
        v = counts[typ]; v["n"] += 1
        v["top1"] += int(np.argmax(lp[i+1,:n+1])) == j+1
        v["prob_ge050"] += float(np.exp(lp[i+1,j+1])) >= .5
        v["prob_ge010"] += float(np.exp(lp[i+1,j+1])) >= .1
        for k,adj in adjacency.items():
            v[k] += adj.get(a) == c
        feats[typ].append(geo[i,j].tolist())
    # Pairs de palavras consecutivas do ouro podem divergir do alvo mediano.
    dono = {w:u["id"] for u in bs for w in u["ks"]}
    word_pairs = set((dono[a],dono[c]) for a,c in zip(obj["gt_w"],obj["gt_w"][1:]) if dono[a] != dono[c])
    actual = collections.defaultdict(collections.Counter)
    for a,c in word_pairs:
        typ = classe(mapa[a],mapa[c],p,structural)
        v = actual[typ]; v["n"] += 1
        v["top1"] += int(np.argmax(lp[idx[a]+1,:n+1])) == idx[c]+1
        v["cadeias050"] += adjacency["cadeias050"].get(a) == c
    probs = np.exp(lp[1:n+1,1:n+1])
    metrics = {k:b.metricas(obj,p,order) for k,order in ordens.items()}
    return {"page_id":p["page_id"],"uf":p["uf"],"n":n,"transicoes_alvo_mediano":{k:dict(v) for k,v in counts.items()},
        "transicoes_ouro_palavras":{k:dict(v) for k,v in actual.items()},
        "features_sucessor":{k: {"n":len(v),"medias":np.mean(v,axis=0).tolist(),
            "medianas":np.median(v,axis=0).tolist()} for k,v in feats.items()},
        "linhas_top1_prob_ge050":int(np.sum(np.max(probs,axis=1)>=.5)),
        "linhas_top1_prob_ge010":int(np.sum(np.max(probs,axis=1)>=.1)),
        "metricas_decoders":metrics,"ordens":ordens,"ruido":ruido(p,obj["gt_w"])}


def diagnosticar(nome):
    """Carrega uma rede por vez; logits e metricas por pagina sobrevivem a queda."""
    ff = fila()
    if any(q["modelo"] == nome and "rodando" in q["estado"] for q in ff):
        print(f"[adiado] {nome}: roteiro ainda .rodando",flush=True)
        return
    ck = t.OUT / nome / "melhor.pt"
    if not ck.exists():
        return
    cp_sha = t.sha(ck)
    dircache = OUT / "diagnosticos" / nome / cp_sha
    info = ler(t.OUT / nome / "treino.json")
    if not info.get("concluido"):
        print(f"[adiado] {nome}: treino nao concluido",flush=True)
        return
    signature = {"checkpoint_sha256":cp_sha,"codigo_sha256":t.sha(__file__),
        "treinador_sha256":t.sha(t.__file__),"sucessor_sha256":t.sha(s.__file__),"fontes":b.fontes()}
    meta = dircache / "manifesto.json"
    if meta.exists() and ler(meta) != signature:
        raise ValueError("Fontes de diagnostico mudaram; nao reutilizar cache")
    salvar(meta,signature)
    model = cod = None
    original_out = b.OUT
    # Novas metricas vao apenas para o cache desta revisao.
    b.OUT = OUT / "regua"
    try:
        for bench in ("golden_v4","golden_v3_novo","teste_silver","validacao"):
            it = validacao() if bench == "validacao" else b.paginas(bench,"linhas")
            for i,(obj,p) in enumerate(it):
                dest = dircache / bench / (chave(p["page_id"])+".json")
                if dest.exists():
                    continue
                logits = dest.with_suffix(".npz")
                if logits.exists():
                    with np.load(logits) as arr:
                        lp,pos = arr["lp"],arr["pos"]
                else:
                    if model is None:
                        import torch
                        torch.set_num_threads(4)
                        state = torch.load(ck,map_location="cpu",weights_only=False)
                        cfg = argparse.Namespace(**{**state["config"],"device":"cpu"})
                        model,cod = t.criar_modelo(cfg)
                        model.load_state_dict(state["modelo"]); del state
                        model.eval()
                    o = protocolo.ordem_entrada(p)
                    tensors,n = s.montar_lote(cod,[p],[o],None,"cpu")
                    with torch.inference_mode():
                        score,position = model(tensors["input_ids"],tensors["bbox"],tensors["attention_mask"],
                            tensors["bloco_de"],tensors["valido"],tensors["geo"],n)
                        lp = s.log_probs(score)[0].cpu().numpy();pos = position[0].float().cpu().numpy()
                    logits.parent.mkdir(parents=True,exist_ok=True)
                    tmp = logits.with_suffix(".npz.tmp")
                    with tmp.open("wb") as handle:
                        np.savez_compressed(handle,lp=lp,pos=pos)
                    os.replace(tmp,logits)
                    del tensors,score,position
                salvar(dest,diagnostico_pagina(lp,pos,p,obj))
                if (i+1)%5 == 0:
                    print(f"[diagnostico] {nome} {bench} {i+1}",flush=True)
            # O relatorio parcial e atualizado antes da bancada seguinte.
            gerar(relendo=True)
    finally:
        b.OUT = original_out
        del model,cod
        gc.collect()
    if t.sha(ck) != cp_sha:
        raise ValueError("Checkpoint mudou durante diagnostico")


def carregar_diagnosticos():
    out = {}
    for p in sorted(t.OUT.glob("sucessor_linhas*/melhor.pt")):
        if any(q["modelo"] == p.parent.name and "rodando" in q["estado"] for q in fila()):
            continue
        d = OUT / "diagnosticos" / p.parent.name / t.sha(p)
        if not (d / "manifesto.json").exists():
            continue
        out[p.parent.name] = {bench:[ler(x) for x in sorted((d/bench).glob("*.json"))]
            for bench in (*b.BANCADAS,"validacao")}
    return out


def erros(txt,R,meta):
    learned = {x["nome"] for x in inventario(R)[0]}
    candidatos = [r for r in R["resultados"].values() if r["ordenador"] in learned and
        r["representacao"] == "linhas" and r["bancada"] == "golden_v4" and r.get("completa")]
    if not candidatos:
        txt += ["Ainda não há modelo treinado em linhas com avaliação completa."]
        return {}
    best = min(candidatos,key=lambda r:(media(r["paginas"],"quebras"),-media(r["paginas"],"tau")))
    name = best["ordenador"]
    txt += [f"Melhor treinado em linhas por menor média de quebras no v4: `{name}`. Seleção descritiva após observar o v4; não é seleção independente de teste."]
    saida = {}
    for bench in ("golden_v4","golden_v3_novo"):
        rr = R["resultados"].get(f"{name}__linhas__{bench}")
        if not rr:
            continue
        base = {p["page_id"]:p for p in base_de(R,rr)}
        mm = {p["page_id"]:p for p in meta[bench]}
        rows = [{"page_id":p["page_id"],"modelo":p["metricas"]["quebras"],
            "regra":base[p["page_id"]]["metricas"]["quebras"],
            "delta":p["metricas"]["quebras"]-base[p["page_id"]]["metricas"]["quebras"],
            **{k:mm[p["page_id"]][k] for k in ("colunas","tabelas","unidades","palavras")}} for p in rr["paginas"]]
        wins = sorted([p for p in rows if p["delta"]<0],key=lambda p:p["delta"])
        losses = sorted([p for p in rows if p["delta"]>0],key=lambda p:-p["delta"])
        ties = sum(p["delta"]==0 for p in rows)
        txt += ["",f"### {bench}","",f"Ganha em {len(wins)}, perde em {len(losses)}, empata em {ties}. Há apenas {len(wins)} ganhos estritos; não completar a lista com empates." if len(wins)<5 else f"Ganha em {len(wins)}, perde em {len(losses)}, empata em {ties}.",
            "", "| Resultado | page_id | Quebras modelo | Quebras regra | Colunas estimadas | Tabelas | Unidades |", "|---|---|---:|---:|---:|---:|---:|"]
        for label,ss in (("ganha",wins[:5]),("perde",losses[:5])):
            for p in ss:
                txt.append(f"| {label} | `{p['page_id']}` | {p['modelo']} | {p['regra']} | {p['colunas']} | {p['tabelas']} | {p['unidades']} |")
        txt += ["", "| Estrato descritivo | n | Δ quebras/página modelo − regra |", "|---|---:|---:|"]
        strata = {}
        for label,pred in (("uma coluna",lambda p:p["colunas"]==1),("multicoluna",lambda p:p["colunas"]>1),
            ("com tabela",lambda p:p["tabelas"]>0),("sem tabela",lambda p:p["tabelas"]==0),
            ("curta: até 50 unidades",lambda p:p["unidades"]<=50),("mais de 50 unidades",lambda p:p["unidades"]>50)):
            ss = [p for p in rows if pred(p)]
            strata[label] = {"n":len(ss),"delta":st.mean(p["delta"] for p in ss) if ss else None}
            txt.append(f"| {label} | {len(ss)} | {f(strata[label]['delta'],2)} |")
        txt += ["", "Estratos sobrepostos; contagem de colunas é estimativa do exportador. Associação descritiva não identifica causa; tabela detectada pode ser falso positivo."]
        saida[bench] = {"modelo":name,"ganhos":wins,"perdas":losses,"empates":ties,"estratos":strata}
    return saida


def gerar(relendo=False):
    R = ler(b.JSON)
    anc = ancoras(R) if not relendo or not (OUT/"ancoras.json").exists() else ler(OUT/"ancoras.json")
    salvar(OUT/"ancoras.json",anc)
    inv,ff = inventario(R)
    meta = ler(OUT/"metadados.json") if (OUT/"metadados.json").exists() else metadados()
    salvar(OUT/"metadados.json",meta)
    audit = ler(OUT/"auditoria_dados.json") if (OUT/"auditoria_dados.json").exists() else auditar_dados(meta)
    salvar(OUT/"auditoria_dados.json",audit)
    diag = carregar_diagnosticos()
    # Decoders exploratorios ficam em tabela propria; nao escolhem checkpoint.
    txt = ["# Ordenadores treinados nas unidades sem caixas finas", "",
        f"Gerado em {datetime.now().isoformat(timespec='seconds')} por `orquestracao/analises/relatorio_ordenadores_treinados.py`. Apenas arquivos locais; nenhuma rede, GPU ou treino nesta revisão.", ""]
    learned = {x["nome"] for x in inv}
    v4 = [r for r in R["resultados"].values() if r["bancada"]=="golden_v4"]
    get = lambda name,rep:next(r for r in v4 if r["ordenador"]==name and r["representacao"]==rep)
    lr = [r for r in v4 if r["representacao"]=="linhas" and r["ordenador"] in learned and r.get("completa")]
    if lr:
        bb = min(lr,key=lambda r:media(r["paginas"],"quebras")); rr=get("regra_colunas","linhas"); teto=get("teto","linhas")
        txt.append(f"1. Em `linhas`, a regra de colunas continua com τ {f(media(rr['paginas'],'tau'))} e {f(media(rr['paginas'],'quebras'),2)} quebras/página no v4; o melhor treinado por continuidade, {bb['ordenador']}, tem τ {f(media(bb['paginas'],'tau'))} e {f(media(bb['paginas'],'quebras'),2)}: distância de {f(media(bb['paginas'],'quebras')-media(rr['paginas'],'quebras'),2)} quebras da regra e de {f(media(bb['paginas'],'quebras')-media(teto['paginas'],'quebras'),2)} do oráculo (τ {f(media(teto['paginas'],'tau'))}, {f(media(teto['paginas'],'quebras'),2)} quebras).")
    for rep in ("colunas","colunas_margens"):
        complete = [r for r in v4 if r["representacao"]==rep and r.get("completa") and r["ordenador"] != "teto"]
        best = max(complete,key=lambda r:media(r["paginas"],"tau")); te=get("teto",rep)
        txt.append(f"{2 if rep=='colunas' else 3}. Em `{rep}`, o maior τ entre ordenadores completos no v4 é {best['ordenador']}: {f(media(best['paginas'],'tau'))}, {f(media(best['paginas'],'quebras'),2)} quebras; oráculo mediano {f(media(te['paginas'],'tau'))}, distância {f(media(te['paginas'],'tau')-media(best['paginas'],'tau'))}. Poucas quebras não bastam: a ordem interna imposta pode deslocar faixas inteiras.")
    txt += ["4. A comparação do Gemini usa também exatamente suas páginas válidas para todos os ordenadores, incluindo modelos em linhas; cobertura inválida não recebe imputação. V4, v3 novo e silver permanecem separados.",
        "5. Estes resultados sustentam a regra neste orçamento e representação; não eliminam modelos com texto ou mais dados. V4 favorece a regra por ter participado do seu desenvolvimento; silver tem piso de tabelas e os testes por veículo são exploratórios.",
        "", "## Âncoras reconstituídas antes dos números novos", "",
        f"{anc['sequencias_identicas']}/{anc['n']} sequências da regra recompostas a partir das unidades e palavras coincidem exatamente com P2 histórico. P2: τ {f(anc['P2']['tau'],6)}, {f(anc['P2']['quebras'],6)} quebras; P1m histórico: τ {f(anc['P1m']['tau'],6)}, {f(anc['P1m']['quebras'],6)} quebras. Tolerância τ 0,006 respeitada. Não foi reextraído PDF nem reinferido detector.",
        "", "## Inventário de checkpoints e avaliações", "", "| Modelo | Checkpoints | Golden v4 pred/avaliadas | V3 novo pred/avaliadas | Silver pred/avaliadas | Estado |", "|---|---|---:|---:|---:|---|"]
    for x in inv:
        cells = [f"{q['n_pred']}/{q['n_avaliadas']} {'✓' if q['completa'] else 'pendente'}" for q in x["predicoes"]]
        state = "fila em execução: não carregar" if x["rodando"] else ("treino encerrado" if x["info"].get("concluido") else "checkpoint parcial; treino interrompido/sem encerramento registrado")
        txt.append(f"| {x['nome']} | {', '.join(Path(q['arquivo']).name for q in x['checkpoints'])} | {' | '.join(cells)} | {state} |")
    txt += ["", "## Treinos: evidência dos treino.json", "", "| Modelo | Páginas / visitadas | Texto/tokens por unidade | Épocas completas/pedidas | Minutos | Melhor τ RN por unidade | Época melhor |", "|---|---:|---|---:|---:|---:|---:|"]
    for x in inv:
        z=x["info"];c=z["config"];hist=z.get("historico",[])
        best_ep=max(hist,key=lambda q:q["val_tau_unidades"])["epoca"] if hist else None
        tokens = "texto por hash + geometria" if c["modelo"]=="lstm" and "texto" in c["variante"] else ("só geometria, sem tokens" if c["modelo"]=="lstm" else "1 [UNK], sem texto")
        txt.append(f"| {x['nome']} | {z['paginas_treino']} / {z.get('paginas_visitadas',0)} | {tokens} | {z.get('epocas_completas',0)} / {c['epocas']} | {f(z.get('segundos',0)/60,2)} | {f(z.get('melhor_val_tau_unidades'),6)} | {best_ep} |")
    txt += ["", "BiLSTM com texto usa EmbeddingBag de tokens por hash; a afirmação de que todos os modelos recebem um [UNK] é falsa para essas variantes. LayoutReader usa o token 3 do seu vocabulário, equivalente ao token de caixa usado pelo adaptador; LayoutLM usa 100. τ RN acima mede unidades e escolhe checkpoint, não é τ de palavras. Os tempos são treino/validação/gravação registrados, não benchmark controlado.",
            "", "## Todas as páginas, uma bancada por tabela", "", "Médias macro por página. Gemini parcial aparece apenas descritivamente nesta tabela; comparar desempenho inferencial pelo painel pareado. Wilcoxon bilateral Pratt sobre médias das diferenças por veículo, contra a regra da mesma representação (caixas finas contra linhas), reutilizando `erros_ponta_a_ponta.pratt`. Dois p-valores: τ e quebras. Sem correção de multiplicidade; poucos veículos e empate não demonstram equivalência."]
    tables = {}
    for bench in b.BANCADAS:
        txt += ["",f"### {bench}"]
        rs=[r for r in R["resultados"].values() if r["bancada"]==bench]
        tables[bench]=tabela(txt,R,rs)
    txt += ["", "## Gemini: mesmas páginas para todos os ordenadores", "", "Cada painel fixa os IDs cobertos pelo Gemini daquela representação. Inclui outras representações para comparar pipelines de ponta a ponta nas mesmas páginas. Uma saída que não cobre todos esses IDs é excluída desse painel; nenhum valor faltante é reparado. A seleção de páginas válidas ainda pode favorecer o Gemini: falhas fazem parte do resultado operacional."]
    paired={}
    for gr in sorted([r for r in R["resultados"].values() if r["ordenador"]=="gemini"],key=lambda r:(r["bancada"],r["representacao"])):
        ids={p["page_id"] for p in gr["paginas"]}
        txt += ["",f"### {gr['bancada']}, cobertura Gemini {gr['representacao']}: {len(ids)}/{gr['esperadas']}"]
        paired[f"{gr['bancada']}__{gr['representacao']}"]=tabela(txt,R,[r for r in R["resultados"].values() if r["bancada"]==gr["bancada"]],ids)
    txt += ["", "## Bancadas humanas: veículos vistos e não vistos no treino", "", "Visto significa veículo do split supervisionado desta noite; não descreve o pré-treino de terceiros ou do detector. As páginas humanas foram excluídas do treino. V3 novo não contém páginas de veículos vistos: grupo vazio é omitido."]
    human={}
    for bench in ("golden_v4","golden_v3_novo"):
        txt += ["",f"### {bench}"]
        human[bench]=tabela(txt,R,[r for r in R["resultados"].values() if r["bancada"]==bench and (r["ordenador"] in learned or r["ordenador"]=="regra_colunas")],grupos=True)
    txt += ["", "## Silver sem páginas com tabela: sensibilidade, não novo protocolo", "", "Remove páginas com pelo menos uma unidade de tipo tabela detectada no exportado de linhas. Não usa rótulos humanos e não altera o teste original. Falsos positivos/negativos do detector podem alterar a seleção."]
    no_table={p["page_id"] for p in meta["teste_silver"] if not p["tabelas"]}
    txt += [f"Restam {len(no_table)}/{len(meta['teste_silver'])} páginas."]
    sensitivity=tabela(txt,R,[r for r in R["resultados"].values() if r["bancada"]=="teste_silver"],no_table)
    txt += ["", "| Representação | Piso interno todas | Piso interno sem tabela |", "|---|---:|---:|"]
    for rep in b.REPS:
        rr=R["resultados"][f"teto__{rep}__teste_silver"]
        txt.append(f"| {rep} | {f(media(rr['paginas'],'piso_interno'),2)} | {f(media([p for p in rr['paginas'] if p['page_id'] in no_table],'piso_interno'),2)} |")
    txt += ["", "## Revisão adversarial", "",
        "**(a) Sem texto — enfraquece a conclusão sobre o LayoutLM do TCC.** Um [UNK] por linha retira conteúdo e comprimento textual; é uma ablação geométrica, não uma reprodução do modelo anterior com texto. O BiLSTM geo_texto é exceção e deve ser lido separadamente. O modelo pode explorar embeddings de posição da entrada fixa, que não representam a ordem de leitura. Mudaria para tokens reais por linha com janelas/hierarquia explícitas e uma ablação controlada na mesma amostra.",
        "", "**(b) Dados e orçamento — enfraquece a generalização.** A amostra congelada auditada abaixo é menor que a do modelo anterior; max-minutos é limite, não tempo consumido. Há variantes interrompidas, e LayoutReader ajusta apenas as últimas quatro camadas e a cabeça. Não chamar este ensaio de comparação com o melhor treino histórico. O experimento estendido reinicializa a rede e altera o scheduler (warm-up proporcional ao total de épocas); não isola somente o efeito de continuar o treino curto.",
        "", "**(c) Mediana por unidade — ruído medido abaixo.** Definição conservadora: dois textos consecutivos na ordem mediana contradizem as palavras se existe ao menos um par cruzado invertido (max posto da primeira > min posto da segunda). Reporta também fração de pares cruzados invertidos e fronteiras descontínuas, que não são a mesma coisa. Não inclui átomo/margem entre duas linhas como par vizinho. Ruído não prova que ele explica a fragmentação; compara-se sua magnitude com os erros do modelo.",
        "", "| Conjunto linhas | Pares vizinhos | Pares contraditórios | Fração | Pares cruzados de palavras invertidos | Fronteiras não contíguas |", "|---|---:|---:|---:|---:|---:|"]
    noise={"treino":audit["ruido_treino_linhas"]}
    for bench,rows in meta.items():
        c=collections.Counter()
        for p in rows:
            c.update({k:v for k,v in p["ruido"].items() if isinstance(v,int)})
        noise[bench]=dict(c)
    valrows=[]
    for obj,p in validacao():
        valrows.append(ruido(p,obj["gt_w"]))
    vv=collections.Counter()
    for z in valrows:
        vv.update({k:v for k,v in z.items() if isinstance(v,int)})
    noise["validacao_RN"]=dict(vv)
    for name,c in noise.items():
        txt.append(f"| {name} | {c['pares_vizinhos']} | {c['pares_contraditorios']} | {f(100*c['pares_contraditorios']/max(1,c['pares_vizinhos']),3)}% | {c['pares_palavras_invertidos']}/{c['pares_palavras']} ({f(100*c['pares_palavras_invertidos']/max(1,c['pares_palavras']),4)}%) | {c['fronteiras_nao_contiguas']} |")
    txt += ["", "Ruído enfraquece a interpretação de silver como ordem humana exata, mas não invalida os valores nas bancadas humanas. Não corrigimos alvos nesta tarefa.",
        "", "**(d) Desenvolvimento no v4 — enfraquece a vantagem de generalização da regra.** A regra foi escolhida no v4 e os modelos foram selecionados por RN. V4 é bancada de desenvolvimento; v3 novo reduz esse viés por página, mas repete layouts/veículos. Não combinar os grupos nem tratar superioridade no v4 como prova em veículos novos.",
        "", "**(e) Tabelas no silver — enfraquece a leitura absoluta de quebras.** O piso interno é invariante à permutação de unidades. A sensibilidade sem tabela acima permite verificar se muda o vencedor; não atribuir o piso inteiro ao ordenador nem excluir tabelas do resultado principal.",
        "", "**(f) Vazamento e consistência — auditoria executada.**", "", "| Representação | Treino | RN | Treino ∩ humano | Treino ∩ teste | Treino ∩ RN |", "|---|---:|---:|---:|---:|---:|"]
    for rep,z in audit["particoes"].items():
        txt.append(f"| {rep} | {z['treino']} | {z['validacao']} | {z['treino_humano']} | {z['treino_teste']} | {z['treino_validacao']} |")
    txt += ["",f"IDs de treino idênticos nas três representações: {'sim' if audit['mesmos_ids_todas_representacoes'] else 'não'}. Split conferido por `treinar_sem_caixas.indice`, que falha com veículo/partição incompatível. Não foi encontrado vazamento supervisionado nesses IDs. Não certifica ausência de sobreposição no pré-treino do ls3/LayoutReader; os dados parceiros não foram abertos.",
        "", "O treinador assina os shards e o código, mas armazena só o hash dessa assinatura, sem lista completa no melhor.pt. O limite de tempo marca `concluido=True` mesmo com época parcial: significa orçamento encerrado, não convergência. A revisão usa épocas/cursor reais. Entrada embaralhada fixa por página é a exigida pelo protocolo; não é vazamento de rótulo, mas deixa o mesmo contexto arbitrário da LSTM/posição absoluta em todas as épocas. Não houve prova de robustez a outras permutações.",
        "", "As descrições antigas divergem dos comandos: roteiros 01/03/04 pedem oito épocas; o relatório antigo dizia quatro. Configs registradas de pontual/sucessor_colunas têm limites diferentes dos roteiros atuais. Descrever o treino pelo treino.json, não reconstruir flags por comentário. Há falha inicial de checkpointing no LayoutReader, seguida de tentativa concluída. Esses pontos não mudam a comparação medida, mas derrubam a alegação de reprodução exata por documentação antiga.",
        "", "O `ordenar_bancadas.py` grava tempos apenas para páginas calculadas naquela chamada; uma retomada pode apagar tempos anteriores. Não usamos isso para comparar latência. Ele e o treinador também sobrescrevem este .md com seu relatório parcial; regenerar com este script ao terminar a fila. Saídas desta revisão são isoladas, com hash do checkpoint e código. Nenhum treinador foi corrigido.",
        "", "## (g) Onde o sucessor erra", "", "Classes são proxies geométricos mutuamente exclusivos: margens/quadros pelo exportado colunas_margens; entrada/saída de átomo; mesma coluna = sobreposição horizontal ≥ 50%, descida e folga ≤ max(4 alturas, 4% da página); salto à direita e para cima; demais = zona/outros. Não há anotação independente dessas classes. Primeiro medimos o alvo mediano por unidade; depois pares de unidades atravessados por palavras consecutivas do ouro (deduplicados). Top1 bruto inclui FIM como candidato; cadeias mede o sucessor na permutação final, antes da expansão de palavras."]
    trans={}; dec={}
    for name,benches in diag.items():
        for bench,rows in benches.items():
            if not rows:
                continue
            trans[f"{name}__{bench}"]={}
            for key,label in (("transicoes_alvo_mediano","alvo mediano"),("transicoes_ouro_palavras","ouro palavras")):
                if bench not in ("golden_v4","validacao"):
                    continue
                cnt=collections.defaultdict(collections.Counter)
                for p in rows:
                    for typ,c in p[key].items():cnt[typ].update(c)
                trans[f"{name}__{bench}"][key]={k:dict(v) for k,v in cnt.items()}
                txt += ["",f"### {name}, {bench}, {label}: {len(rows)} páginas", "", "| Transição | n | Top1 bruto | Após cadeias 0,5 | Aresta correta com p ≥ 0,5 |", "|---|---:|---:|---:|---:|"]
                for typ,c in sorted(cnt.items()):
                    txt.append(f"| {typ} | {c['n']} | {f(100*c['top1']/c['n'],1)}% | {f(100*c['cadeias050']/c['n'],1)}% | {f(100*c['prob_ge050']/c['n'],1)+'%' if key=='transicoes_alvo_mediano' else '—'} |")
            txt += ["",f"### (h) {name}, {bench}: mesmo checkpoint, {len(rows)} páginas", "", "| Decodificação | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |", "|---|---:|---:|---:|---:|"]
            zz={}
            for decoder in DECODERS:
                rr=[{"metricas":p["metricas_decoders"][decoder]} for p in rows]
                z={k:media(rr,k) for k in COLS};zz[decoder]=z
                txt.append(f"| {decoder} | {f(z['tau'])} | {f(z['quebras'],2)} | {f(100*z['fid12'],1)}% | {f(100*z['sucessor_linhas'],1)}% |")
            dec[f"{name}__{bench}"]=zz
            txt += ["",f"Unidades com alguma aresta p ≥ 0,5: {sum(p['linhas_top1_prob_ge050'] for p in rows)}/{sum(p['n'] for p in rows)}; p ≥ 0,1: {sum(p['linhas_top1_prob_ge010'] for p in rows)}/{sum(p['n'] for p in rows)}."]
    if not diag:
        txt += ["", "Diagnóstico ainda pendente; execute com --diagnosticar. Nenhuma conclusão sobre limiar/treino é sustentada sem as tabelas."]
    txt += ["", "Gulosa = feixe de largura 1, feixe = largura 4, ambos nos decodificadores originais. Cadeias 0,1/0 são sensibilidades exploratórias, sem escolher limiar no teste; posição usa apenas a cabeça pontual. A matriz de probabilidades é a mesma. Melhor decodificação no ouro desta seção não é um método validado. Alterar o número de épocas muda também warm-up/scheduler; só um controle de continuação com estado preservado isolaria treino curto.",
        "", "## (i) Geometria e normalização", ""]
    geo=audit["geometria_treino"]
    txt += [f"{geo['linhas']} unidades texto de treino: {geo['fora_pagina']} caixas fora da página; {geo['degeneradas_grade1000']} degeneradas após quantização; {geo['paginas_acima510']} páginas acima de 510 unidades, máximo {geo['max_unidades']}.",
        "", "| Grandeza das linhas de treino | p10 | Mediana | p90 |", "|---|---:|---:|---:|"]
    for k,v in geo["quantis"].items():txt.append(f"| {k} | {' | '.join(f(x,5) for x in v)} |")
    txt += ["", "As caixas são convertidas de pontos para grade 0–1000 pelo normalizador original; as features do par usam pontos divididos por largura/altura, e ordem de entrada nos dois eixos. Auditamos abaixo as dez features nos alvos da validação/v4, na ordem: Δ esquerda, Δ topo, folga vertical, Δ centro x, sobreposição, Δ largura, Δ base, |folga|, alinhamento esquerdo < 2% da página, salto à direita/acima.",
        "", "| Modelo/bancada | Tipo | n | Dez medianas |", "|---|---|---:|---|"]
    for name,benches in diag.items():
        for bench in ("golden_v4","validacao"):
            cats=collections.defaultdict(list)
            for p in benches[bench]:
                for typ,z in p["features_sucessor"].items():cats[typ].append(z)
            for typ,zs in cats.items():
                # Medias por transicao agregadas exatamente; medianas de medianas
                # sao declaradas como tal para nao inventar uma mediana global.
                vals=np.median([z["medianas"] for z in zs],axis=0)
                txt.append(f"| {name}/{bench} | {typ} | {sum(z['n'] for z in zs)} | {'; '.join(f(v,4) for v in vals)} |")
    txt += ["", "A última tabela é mediana entre páginas das medianas por tipo, não mediana global de transições. A representação tem sinal vertical válido, mas alturas pequenas comprimem folga/Δy na escala da página. O indicador de alinhamento aceita 2% da largura, que pode confundir recuos e linhas curtas; não identifica coluna sozinho. Features não recebem tipo tabela/margem nem zona e não normalizam distância pela altura de linha. Isso enfraquece a adequação do desenho, sem demonstrar bug de eixo ou normalização. Mudaria para folga em alturas de linha, pertença a coluna/zona e tipo de unidade; manteria uma ablação para medir cada contribuição. Não corrigimos o treinador.",
        "", "## Erros do melhor treinado em linhas contra a regra", ""]
    error=erros(txt,R,meta)
    txt += ["", "## Fila, falhas e pendências", "", "| Roteiro | Modelo | Estado | Bytes log | Erro registrado |", "|---|---|---|---:|---|"]
    for q in ff:txt.append(f"| {q['roteiro']} | {q['modelo']} | {q['estado']} | {q['log_bytes']} | {q['erro'] or '—'} |")
    txt += ["", "Modelos/representações que não aparecem nas tabelas não foram avaliados: não extrapolar, por exemplo, pontual em colunas ou LayoutReader ajustado em colunas_margens. Nenhum modelo de linguagem novo foi chamado; apenas predições Gemini previamente autorizadas. Não iniciar treino nem inferência de checkpoint enquanto seu roteiro estiver .rodando.",
        "", "## Regeneração e fontes", "", "```powershell",
        "venv/Scripts/python.exe -B orquestracao/analises/relatorio_ordenadores_treinados.py",
        "venv/Scripts/python.exe -B orquestracao/analises/relatorio_ordenadores_treinados.py --diagnosticar",
        "```", "", "Fontes: `resultados/ordenadores_sem_caixas.json`, `resultados/erros_ponta_a_ponta.json`, `resultados/unidades_sem_caixas/`, `*/treino.json`, checkpoints/predições e marcadores/logs da fila. JSON desta revisão guarda tabelas, testes, dados por página, inventário, fila e hashes. A régua nova chama `bancada_ordenadores.metricas`, que importa `erros_ponta_a_ponta.medir/eventos`; não houve reimplementação de τ, quebras, fidelidade ou sucessor de linhas. Unidades sem palavras não afetam métricas textuais, mas afetam alvos de sucessor. Referência humana é ordem de regiões expandida geometricamente; silver é fluxo automático por palavra, nos veículos confiáveis. Sobreposição silver/humano impede somar coortes como amostra independente.", ""]
    payload={"gerado_em":datetime.now().isoformat(),"ancoras":anc,"inventario":inv,"fila":ff,
        "tabelas":tables,"gemini_pareado":paired,"humanas":human,"silver_sem_tabela":sensitivity,
        "auditoria":audit,"ruido":noise,"transicoes":trans,"decoders":dec,"erros":error,
        "fontes":{"bancada_sha256":t.sha(b.JSON),"codigo_sha256":t.sha(__file__)}}
    salvar(JSON,payload)
    tmp=MD.with_suffix(".md.revisao04.tmp")
    tmp.write_text("\n".join(txt),encoding="utf-8")
    os.replace(tmp,MD)
    print(f"[relatorio] {len(R['resultados'])} combinacoes; {MD}",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diagnosticar",action="store_true")
    a=ap.parse_args()
    gerar()
    if a.diagnosticar:
        for name in ("sucessor_linhas","sucessor_linhas_40ep"):
            diagnosticar(name)
        gerar()


if __name__ == "__main__":
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
