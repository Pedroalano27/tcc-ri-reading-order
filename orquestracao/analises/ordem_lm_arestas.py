"""Exporta arestas textuais e combina continuidade causal com regra congelada.

Importa candidatos, categorias e regua oficial sem chamar mains ou gravadores
antigos. Nenhum texto/referencia humana vai para o cluster. Ouro entra somente
na auditoria, na selecao em v4/RN e no oraculo explicitamente identificado.
Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py
 exportar [--contexto caminho|linha] [--palavras-contexto 48]
 exportar-marginal
 decodificar --escores DIR [--escores-marginal DIR] [--saida DIR]
 preparo  # escreve resultados/e003_lm/PREPARO.md a partir das execucoes
Decodificar aceita cobertura parcial (fumaca) sem selecionar configuracao.
Com escores completos, escolhe a grade apenas em v4/RN e gera o relatorio final.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse
import collections
import hashlib
import itertools
import json
import math
import statistics
import time

from orquestracao.analises import corretor_de_transicoes as c
b, e = c.b, c.e
BASE = RAIZ / "resultados/ordem_lm"
MD = RAIZ / "resultados/ordem_lm_arestas.md"
E003 = RAIZ / "resultados/e003_lm"
COORTES = ("golden_v4", "golden_v3_novo", "teste_silver", "validacao_silver")
AJUSTE = ("golden_v4", "validacao_silver")
METRICAS = ("quebras", "tau", "fid12", "sucessor_linhas")
# Doze configuracoes predefinidas. NSP ausente equivale a zero, sem cabeca aleatoria.
GRADE = [{"nome": f"seletiva_r{r}_t{t}", "decoder": "seletiva", "w_regra": r,
          "w_geo": .1, "w_lm": 1., "w_nsp": 0., "limiar": t}
         for r in (.5, 1., 2.) for t in (.5, 1.5)] + [
         {"nome": f"global_r{r}_n{n}", "decoder": "global", "w_regra": r,
          "w_geo": .1, "w_lm": 1., "w_nsp": n, "limiar": 0.}
         for r in (.5, 1., 2.) for n in (0., .2)]


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(2**20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix+".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+"\n")
    tmp.replace(p)


def verificar_lacre(man):
    """Confere somente IDs do manifesto antes de carregar qualquer pagina."""
    lock = RAIZ/"experimentos/TESTE_CEGO.lock"
    if lock.exists():
        cegas = set(b.ler(lock)["page_id"])
        ids = {pid for co in man["bancadas"].values() for pid in co["paginas_sha256"]}
        exigir(not ids.intersection(cegas), "PARE: manifesto intercepta o teste cego")


def carregar_manifesto():
    man = b.ler(BASE/"pares/MANIFESTO.json")
    verificar_lacre(man)
    exigir(man["fontes"] == fontes(), "Fontes mudaram desde exportacao; aborte e audite")
    return man


def paginas(co):
    if co != "validacao_silver":
        yield from b.paginas(co, "linhas")
        return
    splits = b.ler(RAIZ / "data/processed/splits.json")
    for uf in splits["validacao"]:
        pp = b.UNIDADES / "linhas" / (uf+".jsonl")
        wp = pp.with_name(uf+".palavras.jsonl")
        for p, obj in itertools.zip_longest(b.jsonl(pp), b.jsonl(wp)):
            exigir(p and obj and p["page_id"] == obj["page_id"], "Shards RN divergentes")
            exigir(p["uf"] == uf and p["particao"] == "validacao", "Split RN mudou")
            exigir(obj["referencia_palavras_tipo"] == "fluxo_pdf_por_palavra" and
                   obj["gt_w"] == list(range(len(obj["palavras"]))), "Referencia RN mudou")
            yield {**obj, "uf": uf}, p


def fontes():
    splits = b.ler(RAIZ / "data/processed/splits.json")
    paths = b.DEP_PATHS + [Path(c.__file__), RAIZ/"data/processed/splits.json"]
    paths += [b.UNIDADES/"bancadas"/(co+".jsonl") for co in c.HUMANAS]
    paths += [b.UNIDADES/"linhas"/(uf+suf) for part in ("teste", "validacao")
              for uf in splits[part] for suf in (".jsonl", ".palavras.jsonl")]
    return {p.relative_to(RAIZ).as_posix(): sha(p) for p in dict.fromkeys(paths)}


def ancora():
    rows = []
    historico = {r["page_id"]: r["metodos"]["P2"]["seq"]
                 for r in b.ler(e.JSON)["paginas"] if r["coorte"] == "v4"}
    for obj, p in paginas("golden_v4"):
        ordem, _ = b.prever(c.automatico(p), obj["palavras"], "regra_colunas")
        met, seq, _, _ = c.medir(obj, p, ordem)
        exigir(seq == historico[p["page_id"]], "Sequencia da ancora divergiu: "+p["page_id"])
        rows.append({"page_id": p["page_id"], "tau": met["tau"], "quebras": met["quebras"]})
    exigir(len(rows) == 44 and {r["page_id"] for r in rows} == set(historico), "Coorte v4 mudou")
    medias = {k: statistics.mean(r[k] for r in rows) for k in ("tau", "quebras")}
    exigir(abs(medias["tau"]-.985948) <= .00000051 and
           abs(medias["quebras"]-6.045455) <= .00000051,
           "PARE: ancora obrigatoria nao bate: "+str(medias))
    print("Âncora aprovada: "+str(medias), flush=True)
    return {"n": len(rows), "medias": medias, "sequencias_identicas_P2": True}


def texto(ctx, uid):
    u = ctx["mapa"][uid]
    tipo = c.tipo_unidade(u)
    if tipo != "texto":
        return "[TABELA]" if tipo == "tabela" else "[IMAGEM]"
    return " ".join(ctx["ws"][k][0] for k in ctx["exp"][uid])


def montar_pares(ctx, a):
    pares = []
    ultimas = []
    for uid in ctx["ordem"]:
        atual = texto(ctx, uid).split()
        ultimas = (ultimas+atual)[-a.palavras_contexto:] if a.contexto == "caminho" else atual[-a.palavras_contexto:]
        for z in c.candidatos(ctx, uid, 3):
            # O corretor nao oferece score geometrico por candidato: proxy explicito.
            geo = 0. if z is None else c.sobreposicao(ctx["mapa"][uid], ctx["mapa"][z]) / (
                1+abs(c.cy(ctx["mapa"][z])-c.cy(ctx["mapa"][uid]))/ctx["h"])
            pares.append({"id_fonte": uid, "id_destino": z, "contexto": " ".join(ultimas),
                          "continuacao": "[FIM]" if z is None else " ".join(texto(ctx, z).split()[:a.palavras_continuacao]),
                          "sucessor_regra": ctx["regra"][uid] == z,
                          "prior_geo": geo, "categoria": c.categoria(ctx, uid, z)})
    return pares


def exportar(a):
    t = time.perf_counter()
    an = ancora()
    manifesto = {"versao": "pares-lm-v1", "ancora": an, "fontes": fontes(), "exportador_sha256": sha(__file__),
                 "config": {"nivel": 3, "contexto": a.contexto, "palavras_contexto": a.palavras_contexto,
                            "palavras_continuacao": a.palavras_continuacao, "regra": e.FIXA.id}, "bancadas": {}}
    for co in COORTES:
        rows, stats = [], collections.Counter()
        assinaturas = {}
        for obj, p in paginas(co):
            b.auditar_unidades(p, obj)
            ctx = c.contexto(p, obj["palavras"])
            pares = montar_pares(ctx, a)
            # Auditoria do teto fica no manifesto local, nunca no arquivo do cluster.
            _, _, trs, _ = c.preparar_avaliacao(obj, p, ctx)
            cands = collections.defaultdict(set)
            for par in pares:
                cands[par["id_fonte"]].add(par["id_destino"])
            stats.update(paginas=1, fontes=len(ctx["ordem"]), pares=len(pares),
                         palavras_contexto=sum(len(v["contexto"].split()) for v in pares),
                         palavras_continuacao=sum(len(v["continuacao"].split()) for v in pares),
                         arestas_ouro=len(trs),
                         arestas_oraculo=sum(tr["alcancavel"] and (tr["interno"] or tr["z"] in cands[tr["a"]]) for tr in trs),
                         candidatos_ouro=sum(not tr["interno"] and tr["alcancavel"] for tr in trs),
                         candidatos_cobertos=sum(not tr["interno"] and tr["alcancavel"] and tr["z"] in cands[tr["a"]] for tr in trs))
            rows.append({"page_id": p["page_id"], "pares": pares})
            assinaturas[p["page_id"]] = c.digest([obj, p])
            print(f"Exportação {co}: {len(rows)} páginas, {stats['pares']} pares", flush=True)
        path = BASE/"pares"/(co+".jsonl")
        if path.exists():
            exigir(list(b.jsonl(path)) == rows, "Exportacao existente difere; nao sera sobrescrita: "+str(path))
        else:
            jsonl(path, rows)
        manifesto["bancadas"][co] = {**stats, "bytes": path.stat().st_size, "sha256": sha(path),
                                     "paginas_sha256": assinaturas}
    manifesto["segundos_exportacao"] = time.perf_counter()-t
    manifesto["memoria"] = b.memoria()
    gravar(BASE/"pares/MANIFESTO.json", manifesto)
    relatorio(manifesto)


def pares_marginais(pagina):
    """Um destino por pagina, incluindo FIM; nao deduplica por texto repetido."""
    destinos = {}
    for p in pagina["pares"]:
        z = p["id_destino"]
        if z in destinos:
            exigir(destinos[z]["continuacao"] == p["continuacao"],
                   "Mesmo destino tem continuacoes diferentes")
        else:
            destinos[z] = {"id_fonte": None, "id_destino": z,
                           "contexto": "", "continuacao": p["continuacao"]}
    return {"page_id": pagina["page_id"], "pares": list(destinos.values())}


def exportar_marginal(a):
    t = time.perf_counter()
    man = carregar_manifesto()
    an = ancora()
    manifesto = {"versao": "pares-lm-marginal-v1", "ancora": an,
                 "condicional_manifesto_sha256": sha(BASE/"pares/MANIFESTO.json"),
                 "exportador_sha256": sha(__file__), "contexto": "somente BOS",
                 "config_condicional": man["config"], "bancadas": {}}
    for co in COORTES:
        pp = BASE/"pares"/(co+".jsonl")
        exigir(sha(pp) == man["bancadas"][co]["sha256"], "Pares condicionais mudaram")
        rows = [pares_marginais(r) for r in b.jsonl(pp)]
        exigir(len(rows) == man["bancadas"][co]["paginas"], "Cobertura marginal divergente")
        exigir({r["page_id"] for r in rows} == set(man["bancadas"][co]["paginas_sha256"]),
               "IDs marginais divergentes")
        path = BASE/"pares_marginal"/(co+".jsonl")
        if path.exists():
            exigir(list(b.jsonl(path)) == rows, "Marginais existentes diferem; nao sobrescrever")
        else:
            jsonl(path, rows)
        manifesto["bancadas"][co] = {
            "paginas": len(rows), "destinos": sum(len(r["pares"]) for r in rows),
            "palavras_continuacao": sum(len(p["continuacao"].split()) for r in rows for p in r["pares"]),
            "bytes": path.stat().st_size, "sha256": sha(path), "condicional_sha256": sha(pp)}
        print("Marginal "+co+": "+json.dumps(manifesto["bancadas"][co]), flush=True)
    manifesto["segundos_exportacao"] = time.perf_counter()-t
    path = BASE/"pares_marginal/MANIFESTO.json"
    if path.exists():
        velho = b.ler(path)
        # Mudancas no relatorio/decoder nao invalidam uma exportacao identica.
        ignorar = ("segundos_exportacao", "exportador_sha256")
        exigir({k:v for k,v in velho.items() if k not in ignorar} ==
               {k:v for k,v in manifesto.items() if k not in ignorar},
               "Manifesto marginal existente difere; audite")
    else:
        gravar(path, manifesto)


def max_regret(ordem, scores):
    """Cobre todas as unidades: fixa maior diferenca melhor-segunda aresta viavel.

    FIM e privado por fonte (varios caminhos). Destino tem no maximo uma entrada;
    union-find impede ciclo. Recalcula regrets apos cada fixacao. Ao final, costura
    raizes pelo posto da PRIMEIRA unidade na regra. Nao e um otimizador exato.
    """
    rank = {u:i for i,u in enumerate(ordem)}
    pendentes = set(ordem)
    entrada, saida = {}, {}
    pai = {u:u for u in ordem}
    def raiz(u):
        while pai[u] != u:
            pai[u] = pai[pai[u]]
            u = pai[u]
        return u
    while pendentes:
        escolha = None
        for u in ordem:
            if u not in pendentes:
                continue
            viaveis = [(v,s) for v,s in scores[u].items()
                       if v is None or (v not in entrada and raiz(u) != raiz(v))]
            viaveis.sort(key=lambda it: (-it[1], rank.get(it[0], len(rank))))
            exigir(viaveis, "Fonte sem FIM")
            v, valor = viaveis[0]
            regret = valor-viaveis[1][1] if len(viaveis) > 1 else float("inf")
            chave = (regret, valor, -rank[u])
            if escolha is None or chave > escolha[0]:
                escolha = (chave, u, v)
        _, u, v = escolha
        saida[u] = v
        pendentes.remove(u)
        if v is not None:
            entrada[v] = u
            pai[raiz(u)] = raiz(v)
    resultado = []
    for u in sorted((u for u in ordem if u not in entrada), key=rank.__getitem__):
        while u is not None:
            resultado.append(u)
            u = saida[u]
    exigir(len(resultado) == len(ordem) and set(resultado) == set(ordem), "Grafo perdeu/repetiu unidade")
    return resultado


def seletiva(regra, scores, lm, limiar, janela=12):
    """Movimento local do sucessor, mesmo contrato de regra_mais_modelo.intervir.

    Exige vitoria do LM contra o sucessor ORIGINAL por margem estrita; preserva
    arestas aceitas e ordem relativa das demais unidades, raio de doze posicoes.
    """
    orig = dict(zip(regra, regra[1:]+[None]))
    rank = {u:i for i,u in enumerate(regra)}
    propostas = []
    for u in regra:
        v = max(scores[u], key=lambda v: (scores[u][v], -rank.get(v, len(regra))))
        margem_lm = lm[u][v]-lm[u][orig[u]]
        margem = scores[u][v]-scores[u][orig[u]]
        if v != orig[u] and margem_lm > limiar and margem > limiar:
            propostas.append((margem, u, v))
    propostas.sort(key=lambda it: (-it[0], rank[it[1]]))
    ordem, aceitas = list(regra), {}
    for _, u, v in propostas:
        iu = ordem.index(u)
        iv = ordem.index(v) if v is not None else len(ordem)-1
        if abs(iu-iv) > janela:
            continue
        nova = list(ordem)
        if v is None:
            nova.remove(u); nova.append(u)
        else:
            nova.remove(v); nova.insert(nova.index(u)+1, v)
        suc = dict(zip(nova, nova[1:]+[None]))
        if any(suc[a] != z for a,z in aceitas.items()):
            continue
        ordem = nova
        aceitas[u] = v
    exigir(len(ordem) == len(regra) and set(ordem) == set(regra), "Movimento perdeu unidade")
    return ordem


def validar_escore(s):
    exigir(math.isfinite(s["logp_media"]) and isinstance(s["n_tokens"], int) and s["n_tokens"] > 0,
           "Escore invalido")
    exigir(math.isfinite(s["logp_soma"]) and
           math.isclose(s["logp_media"], s["logp_soma"]/s["n_tokens"], rel_tol=1e-6, abs_tol=1e-6),
           "Soma/media do logp inconsistentes")


def combinar(pares, escores, cfg, marginais=None):
    """Subtrai somas e divide uma vez, antes do log-softmax por fonte."""
    exigir(len(pares) == len(escores), "Numero de pares/escores diverge")
    grupos = collections.defaultdict(list)
    for p, s in zip(pares, escores):
        exigir((p["id_fonte"], p["id_destino"]) == (s["id_fonte"], s["id_destino"]), "Pares/escores fora de ordem")
        validar_escore(s)
        valor = s["logp_media"]
        if marginais is not None:
            exigir(p["id_destino"] in marginais, "Destino sem marginal")
            m = marginais[p["id_destino"]]
            validar_escore(m)
            exigir(s["n_tokens"] == m["n_tokens"], "Continuacao condicional/marginal tem tokens diferentes")
            valor = (s["logp_soma"]-m["logp_soma"])/s["n_tokens"]
        grupos[p["id_fonte"]].append((p,s,valor))
    scores, lm = {}, {}
    for u, ps in grupos.items():
        vals = [v for _,_,v in ps]
        mx = max(vals)
        normal = mx+math.log(sum(math.exp(v-mx) for v in vals))
        scores[u], lm[u] = {}, {}
        for p,s,valor in ps:
            v = p["id_destino"]
            lp = valor-normal
            lm[u][v] = lp
            ns = s.get("nsp") or 0.
            exigir(math.isfinite(ns), "NSP nao finito")
            scores[u][v] = (cfg["w_regra"]*p["sucessor_regra"]+cfg["w_geo"]*p["prior_geo"]+
                            cfg["w_lm"]*lp+cfg["w_nsp"]*ns)
    return scores, lm


def acertos(q, seq, trs, med):
    ranks = {k:i for i,k in enumerate(seq)}
    intactas = {L["id"]: all(ranks[z] == ranks[a]+1 for a,z in zip(L["ks"], L["ks"][1:])) for L in q["gold_lines"]}
    hits = [bool(intactas[t["linha_a"]] and intactas[t["linha_z"]] and ranks[t["palavra_z"]] == ranks[t["palavra_a"]]+1) for t in trs]
    exigir(not hits or abs(sum(hits)/len(hits)-med["sucessor_linhas"]) < 1e-12, "Diagnostico diverge da regua")
    return hits


def avaliar(obj, p, ordem, trs, basehits):
    met, seq, q, _ = c.medir(obj, p, ordem)
    hits = acertos(q, seq, trs, met)
    diag = {tipo: {"ouro": 0, "acertos": 0, "reparos": 0, "regressoes": 0} for tipo in c.TIPOS}
    for tr, old, new in zip(trs, basehits, hits):
        d = diag[tr["tipo"]]
        d["ouro"] += 1; d["acertos"] += new
        d["reparos"] += new and not old; d["regressoes"] += old and not new
    return {"metricas": met, "diagnostico": diag, "arestas_ouro": len(hits), "arestas_certas": sum(hits),
            "reparos": sum(d["reparos"] for d in diag.values()),
            "regressoes": sum(d["regressoes"] for d in diag.values())}


def resumir(rows, nome):
    if not rows:
        return {}
    # Importa a mesma reamostragem por veiculo e Pratt da bancada.
    W = b.PESOS_CLUSTER(rows)
    res = {"n": len(rows), "veiculos": len({r["uf"] for r in rows}), "metricas": {}, "contrastes": {}}
    for k in METRICAS:
        vs = [r["metodos"][nome]["metricas"][k] for r in rows]
        ds = [v-r["metodos"]["regra"]["metricas"][k] for v,r in zip(vs, rows)]
        dvs = [statistics.mean(d for r,d in zip(rows,ds) if r["uf"] == uf) for uf in sorted({r["uf"] for r in rows})]
        res["metricas"][k] = e.media_ic(vs, W)
        res["contrastes"][k] = {"delta": e.media_ic(ds, W), "wilcoxon_veiculo": e.pratt(dvs)}
    for k in ("reparos", "regressoes", "arestas_ouro", "arestas_certas"):
        res[k] = sum(r["metodos"][nome][k] for r in rows)
    ds = [r["metodos"][nome]["metricas"]["quebras"]-r["metodos"]["regra"]["metricas"]["quebras"] for r in rows]
    res["paginas"] = {"melhoram": sum(d < 0 for d in ds), "igualam": sum(d == 0 for d in ds),
                      "pioram": sum(d > 0 for d in ds)}
    res["acuracia_aresta_micro"] = res["arestas_certas"]/res["arestas_ouro"] if res["arestas_ouro"] else None
    res["diagnostico"] = {t: {k: sum(r["metodos"][nome]["diagnostico"][t][k] for r in rows)
                               for k in ("ouro", "acertos", "reparos", "regressoes")} for t in c.TIPOS}
    return res


def ler_escores(co, man, escdir, cfgmodelo, paresdir=None):
    pp = (paresdir or BASE/"pares")/(co+".jsonl")
    exigir(sha(pp) == man["bancadas"][co]["sha256"], "Arquivo de pares mudou")
    pares = {r["page_id"]: r for r in b.jsonl(pp)}
    sp = escdir/(co+".jsonl")
    scores = {}
    if sp.exists():
        for row in b.jsonl(sp):
            pid = row["page_id"]
            exigir(pid not in scores and pid in pares, "Pagina duplicada ou estranha nos escores")
            exigir(row["pares_sha256"] == c.digest(pares[pid]), "Hash de pares nao confere")
            exigir(row["config_sha256"] == c.digest(cfgmodelo["config"]), "Configuracao de scores misturada")
            exigir(len(row["escores"]) == len(pares[pid]["pares"]), "Escores incompletos")
            scores[pid] = row
    return pares, scores


def carregar_marginal(man, cfgmodelo, escdir):
    mm = b.ler(BASE/"pares_marginal/MANIFESTO.json")
    exigir(mm["versao"] == "pares-lm-marginal-v1" and
           mm["condicional_manifesto_sha256"] == sha(BASE/"pares/MANIFESTO.json"),
           "Manifesto marginal nao corresponde ao condicional")
    cm = b.ler(escdir/"CONFIG.json")
    exigir(cm["config"]["versao"] == "causal-continuacao-v2-bos" and
           cm.get("tokenizacao", {}).get("contexto_vazio") == "somente_bos" and
           isinstance(cm["tokenizacao"]["bos_token_id"], int), "Marginal nao certifica BOS puro")
    for campo in ("modelo", "dtype", "max_tokens"):
        exigir(cm["config"][campo] == cfgmodelo["config"][campo], "Modelos marginais diferem: "+campo)
    rev, rm = cfgmodelo.get("revisao_resolvida"), cm.get("revisao_resolvida")
    if rev and rm:
        exigir(rev == rm, "Revisoes condicional/marginal diferentes")
    else:
        exigir(cm["config"]["revisao"] == cfgmodelo["config"]["revisao"], "Revisoes solicitadas diferem")
    avisos = [] if rev and rm else ["Revisão resolvida ausente em escores legados; identidade exata dos pesos não certificada."]
    for co in COORTES:
        exigir(mm["bancadas"][co]["condicional_sha256"] == man["bancadas"][co]["sha256"],
               "Marginal derivada de outros pares")
    return {"manifesto": mm, "modelo": cm, "diretorio": str(escdir), "avisos": avisos}


def processar(co, man, escdir, cfgmodelo, configs, marginal=None):
    pares, scores = ler_escores(co, man, escdir, cfgmodelo)
    rows = []
    if not scores:
        return rows, {"pontuadas": 0, "esperadas": len(pares), "completa": False}
    if marginal:
        pm, sm = ler_escores(co, marginal["manifesto"], Path(marginal["diretorio"]),
                            marginal["modelo"], BASE/"pares_marginal")
        exigir(set(scores) <= set(sm), "Marginais ausentes para paginas condicionais em "+co)
    for obj,p in paginas(co):
        pid = p["page_id"]
        if pid not in scores:
            continue
        exigir(c.digest([obj,p]) == man["bancadas"][co]["paginas_sha256"][pid], "Pagina local mudou")
        ctx = c.contexto(p, obj["palavras"])
        met, _, trs, _ = c.preparar_avaliacao(obj, p, ctx)
        _, seq, q, _ = c.medir(obj,p,ctx["ordem"])
        basehits = acertos(q, seq, trs, met)
        row = {"page_id": pid, "uf": obj["uf"], "metodos": {}, "ordens": {"regra":ctx["ordem"]},
               "tempos_ms": {"regra":0.}, "pares":len(pares[pid]["pares"]),
               "segundos_lm": scores[pid]["segundos"], "memoria_lm": scores[pid]["memoria"]}
        row["metodos"]["regra"] = avaliar(obj,p,ctx["ordem"],trs,basehits)
        ps, ss = pares[pid]["pares"], scores[pid]["escores"]
        ms = None
        if marginal:
            exigir(pm[pid] == pares_marginais(pares[pid]), "Continuacoes marginais divergentes")
            ms = {}
            for par, s in zip(pm[pid]["pares"], sm[pid]["escores"]):
                exigir(s["id_fonte"] is None and s["id_destino"] == par["id_destino"] and
                       s["id_destino"] not in ms, "Destino marginal repetido ou fora de ordem")
                ms[s["id_destino"]] = s
            row["segundos_lm_marginal"] = sm[pid]["segundos"]
            row["memoria_lm_marginal"] = sm[pid]["memoria"]
        for cfg in configs:
            t = time.perf_counter()
            sc, lm = combinar(ps, ss, cfg, ms)
            ordem = (seletiva(ctx["ordem"],sc,lm,cfg["limiar"]) if cfg["decoder"] == "seletiva"
                     else max_regret(ctx["ordem"],sc))
            nome = cfg["nome"]
            row["tempos_ms"][nome] = 1000*(time.perf_counter()-t)
            row["metodos"][nome] = avaliar(obj,p,ordem,trs,basehits)
            row["ordens"][nome] = ordem
        # Oraculo independente do LM; arestas-ouro realizaveis recebem prioridade.
        t = time.perf_counter()
        sc = {u:{z:(1. if z == ctx["regra"][u] else 0.) for z in c.candidatos(ctx,u,3)} for u in ctx["ordem"]}
        for tr in trs:
            if tr["alcancavel"] and not tr["interno"] and tr["z"] in sc[tr["a"]]:
                sc[tr["a"]][tr["z"]] = 1000000.
        ordem = max_regret(ctx["ordem"],sc)
        row["tempos_ms"]["oraculo"] = 1000*(time.perf_counter()-t)
        row["metodos"]["oraculo"] = avaliar(obj,p,ordem,trs,basehits)
        row["ordens"]["oraculo"] = ordem
        rows.append(row)
        print(f"Decodificação {co}: {len(rows)}/{len(scores)}", flush=True)
    exigir(len(rows) == len(scores), "Pagina pontuada ausente das fontes locais")
    return rows, {"pontuadas":len(rows),"esperadas":len(pares),"completa":len(rows)==len(pares)}


def decodificar(a):
    man = carregar_manifesto()
    man["ancora"] = ancora()
    escdir = a.escores.resolve()
    cfgmodelo = b.ler(escdir/"CONFIG.json")
    marginal = carregar_marginal(man, cfgmodelo, a.escores_marginal.resolve()) if a.escores_marginal else None
    modo = "contrastivo" if marginal else "condicional"
    dados, cobertura = {}, {}
    # Apenas desenvolvimento recebe toda a grade. Congela antes de abrir externos.
    for co in AJUSTE:
        dados[co], cobertura[co] = processar(co,man,escdir,cfgmodelo,GRADE,marginal)
    ajuste_completo = all(cobertura[co]["completa"] for co in AJUSTE)
    selecao = {}
    objetivos = {}
    if ajuste_completo:
        # Duas bancadas com pesos iguais, criterio primario quebras e desempate tau.
        for cfg in GRADE:
            nome = cfg["nome"]
            objetivos[nome] = [statistics.mean(statistics.mean(r["metodos"][nome]["metricas"][k]-
                                r["metodos"]["regra"]["metricas"][k] for r in dados[co]) for co in AJUSTE)
                                for k in ("quebras","tau")]
        for dec in ("seletiva","global"):
            nomes = [cfg["nome"] for cfg in GRADE if cfg["decoder"] == dec]
            melhor = min(nomes, key=lambda n:(objetivos[n][0], -objetivos[n][1], n))
            selecao[dec] = melhor if objetivos[melhor][0] < 0 else "regra"
    else:
        # Configuracoes iniciais predefinidas apenas para provar o caminho.
        selecao = {"seletiva": GRADE[0]["nome"], "global": GRADE[6]["nome"]}
    out = a.saida or (E003/"avaliacao"/escdir.name if marginal else BASE/"avaliacao"/escdir.name)
    exigir(out.resolve().is_relative_to(RAIZ/"resultados"), "Saida precisa ficar em resultados/")
    if ajuste_completo:
        assinatura = [cfgmodelo["config"],GRADE,
                      {co:sha(escdir/(co+".jsonl")) for co in AJUSTE},
                      {co:man["bancadas"][co]["sha256"] for co in AJUSTE}]
        if marginal:
            assinatura += [modo, marginal["modelo"]["config"],
                           {co:sha(Path(marginal["diretorio"])/(co+".jsonl")) for co in AJUSTE}]
        congelada = {"selecao":selecao,"objetivos":objetivos,"grade":GRADE,
                     "assinatura_ajuste":c.digest(assinatura)}
        sp = out/"selecao.json"
        if sp.exists():
            exigir(b.ler(sp) == congelada, "Selecao congelada divergiu; audite antes de avaliar externos")
        else:
            gravar(sp,congelada)
    configs = [cfg for cfg in GRADE if cfg["nome"] in selecao.values()]
    for co in COORTES:
        if co not in AJUSTE:
            dados[co], cobertura[co] = processar(co,man,escdir,cfgmodelo,configs,marginal)
    nomes = list(dict.fromkeys(["regra", *selecao.values(), "oraculo"]))
    saida = {"modelo":cfgmodelo, "diretorio_escores":str(escdir), "cobertura":cobertura,
             "escore": modo, "marginal": marginal, "ancora": man["ancora"],
             "ajuste_completo":ajuste_completo, "completa":all(v["completa"] for v in cobertura.values()),
             "selecao":selecao, "grade":GRADE, "objetivos_ajuste":objetivos,
             "resultados": {co:{n:resumir(rows,n) for n in nomes} for co,rows in dados.items()},
             "paginas":dados, "decodificador_sha256":sha(__file__),
             "escores_sha256":{p.name:sha(p) for p in escdir.glob("*.jsonl")},
             "escores_marginal_sha256":({p.name:sha(p) for p in Path(marginal["diretorio"]).glob("*.jsonl")}
                                        if marginal else {})}
    gravar(out/"avaliacao.json", saida)
    pred = out/"pred" if a.saida or marginal else b.OUT/"pred"
    for co,rows in dados.items():
        if not rows:
            continue
        for dec,n in [*selecao.items(), ("oraculo","oraculo")]:
            # Mesmo fallback regra recebe contrato proprio das duas variantes.
            variante = escdir.name+("_contrastivo" if marginal else "")+"_"+(n if n != "regra" else dec+"_regra")
            dest = pred/f"lm_arestas_{variante}__linhas__{co}.jsonl"
            # indice_pred exige exatamente estas duas chaves; tempos ficam no JSON.
            jsonl(dest,[{"page_id":r["page_id"], "ordem":r["ordens"][n]} for r in rows])
    relatorio(man,saida, out/"AVALIACAO.md" if a.saida or marginal else MD)


def fmt(x,n=3):
    return "—" if x is None else f"{x:.{n}f}".replace(".",",")


def cel(v,n=3):
    return fmt(v["media"],n)+" ["+"; ".join(fmt(x,n) for x in v["ic"])+"]"


def conclusao(A):
    if not A or not A["completa"]:
        return "A pergunta sobre ganho fora do ajuste permanece aberta até a pontuação e avaliação completas."
    leituras = []
    for dec,n in A["selecao"].items():
        if n == "regra":
            leituras.append(dec+": ajuste conservou a regra")
            continue
        contrastes = [A["resultados"][co][n]["contrastes"]["quebras"] for co in ("golden_v3_novo","teste_silver")]
        menores = all(d["delta"]["media"] < 0 for d in contrastes)
        confirmacao = all(d["delta"]["ic"][1] < 0 and d["wilcoxon_veiculo"]["p"] < .05 for d in contrastes)
        if menores and confirmacao:
            leituras.append(dec+": médias externas menores, IC excluem zero e Pratt abaixo de 0,05; evidência exploratória")
        elif menores:
            leituras.append(dec+": médias externas menores, sem confirmação conjunta pelos IC e Pratt")
        else:
            leituras.append(dec+": não reduz quebras consistentemente nas duas bancadas externas")
    return "; ".join(leituras)+"."


def relatorio(man, avaliacao=None, caminho=MD):
    ls = ["# Continuidade de linguagem nas arestas de leitura", "",
          "1. Exportação completa com linhas e átomos ls3 congelados; regra e candidatos importados.",
          "2. Âncora v4 reproduzida: τ "+fmt(man["ancora"]["medias"]["tau"],6)+
          "; "+fmt(man["ancora"]["medias"]["quebras"],6)+" quebras/página.",
          "3. "+("Escores completos; escolhas restritas a golden_v4 e validação RN." if avaliacao and avaliacao["completa"] else
                   "Pontuação integral no cluster ainda pendente; resultados parciais são apenas fumaça."),
          "4. Golden v3 novo é externo ao ajuste atual, mas já foi consultado, inclusive nos candidatos anteriores.",
          "5. "+conclusao(avaliacao), "",
          "Relatório gerado por `ordem_lm_arestas.py`. Números medidos em `resultados/ordem_lm/`; estimativas abaixo são fórmulas explícitas.", "",
          "## Exportação", "", "| Bancada | Páginas | Fontes | Pares | Bytes | MiB | Recall candidatos | Teto arestas-ouro |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for co,s in man["bancadas"].items():
        ls.append(f"| {co} | {s['paginas']} | {s['fontes']} | {s['pares']} | {s['bytes']} | {fmt(s['bytes']/2**20)} | "+
                  fmt(100*s["candidatos_cobertos"]/s["candidatos_ouro"],2)+"% | "+
                  fmt(100*s["arestas_oraculo"]/s["arestas_ouro"],2)+"% |")
    total = sum(s["pares"] for s in man["bancadas"].values())
    tamanho = sum(s["bytes"] for s in man["bancadas"].values())
    ls += ["",f"Total: {total} pares; {tamanho} bytes. Exportação: {fmt(man['segundos_exportacao'])} s.",
           "Hashes SHA-256 de arquivos, fontes e páginas em `pares/MANIFESTO.json`. Arquivos do cluster contêm somente entrada automática, sem ouro.",
           "Sobreposições silver/humanas são conservadas conforme a bancada original; bancadas não são amostras independentes somáveis.", "",
           "Contexto: últimas "+str(man["config"]["palavras_contexto"])+" palavras, modo `"+man["config"]["contexto"]+
           "`; continuação: primeiras "+str(man["config"]["palavras_continuacao"])+". Tabelas/imagens são marcadores; FIM é pontuado pelo token EOS.",
           "O contexto acompanha a regra original e não é recalculado após intervenções. Cabeçalhos e rodapés também recebem candidatos.", "",
           "## Como executar", "", "Da raiz, um processo por vez:", "", "```powershell",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py exportar",
           "venv/Scripts/python.exe -B cluster/pontuar_pares_lm.py --entrada resultados/ordem_lm/pares --saida resultados/ordem_lm/escores --modelo Qwen/Qwen3-0.6B --dtype float16 --lote 4 --dispositivo cuda --bancada golden_v4 --limite-paginas 3",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-0.6B",
           "```", "", "Cluster Linux aarch64: copiar somente `cluster/pontuar_pares_lm.py`, `cluster/requisitos_pontuar.txt` e `pares/`. O script não importa o repositório. Não enviar anotações.", "", "```bash",
           "pip install -r requisitos_pontuar.txt",
           "python -B pontuar_pares_lm.py --entrada pares --saida escores --modelo Qwen/Qwen3-8B --dtype bfloat16 --lote 8 --dispositivo cuda",
           "# Opcional: --nsp neuralmind/bert-base-portuguese-cased",
           "```", "", "NSP só entra se a cabeça estiver presente no checkpoint; cabeça inicializada aleatoriamente é recusada. Fumaça local não baixa NSP.",
           "A saída acrescenta o nome sanitizado do modelo. Ao receber `escores/<modelo>/`, executar `decodificar --escores DIR`; o mesmo código gera a avaliação completa.",
           "Retomada por página: valida hash de pares, configuração e revisão do modelo; repara somente a última linha interrompida dos escores.", "",
           "## Escore e decodificação", "",
           "Causal: soma e média do logp dos tokens da continuação, sem chat template. Tokenização explícita: contexto + quebra de linha; continuação prefixada por espaço, codificada separadamente. Sem token de raciocínio ou geração. Lotes com padding à esquerda e posições explícitas; sem reuso KV entre pares.",
           "Combinação: w_regra × indicador de sucessor original + w_geo × prior + w_lm × log-softmax(escore LM por fonte) + w_nsp × (logit IsNext − NotNext). O escore LM é o logp médio condicional ou o contraste explicitamente identificado na execução. O corretor não tinha prior escalar por candidato; usa-se sobreposição horizontal/(1 + distância vertical em alturas). FIM tem prior zero e continuação EOS, política conservada nos dois termos.",
           "Seletiva: melhor candidato precisa vencer o sucessor original tanto no LM quanto na combinação por margem estrita; move uma unidade em raio de doze posições, preserva arestas já aceitas e cobertura. Global: recalcula melhor−segunda melhor aresta viável por fonte, fixa primeiro o maior regret, impede ciclos e grau de entrada/saída maior que um; FIM privado permite vários caminhos. Costura pela primeira unidade de cada caminho na regra. Esta é uma implementação operacional de max-regret, não reprodução certificada do artigo.",
           "Grade predefinida: "+str(len(GRADE))+" configurações, descritas no JSON da avaliação. Seleção minimiza média dos deltas de quebras das duas bancadas de ajuste, com peso igual por bancada; desempata pelo maior τ. Se nenhuma configuração reduzir quebras, conserva a regra. Sem ajuste completo não há seleção. A escolha é salva em `selecao.json` antes de avaliar externos, que recebem somente as configurações escolhidas.",
           "Oráculo: teto independente por aresta = sucessores-ouro alcançáveis presentes nos candidatos, incluindo bordas internas com adjacência preservada. É um limite otimista, pois a linha inteira também precisa estar intacta; não é teto de quebras ou τ. A ordem oracular fixa arestas-ouro realizáveis com prioridade alta e aplica a mesma cobertura/costura; sua realização pode ficar abaixo do teto independente. Ouro nunca entra nos decoders automáticos.",
           "Métricas oficiais importadas: τ de palavras, quebras e sucessor de linhas. Acurácia de aresta micro = sucessores-ouro de linhas inteiras recuperados / todas as transições-ouro entre linhas; inclui bordas internas aos átomos, exclui FIM. Reporta-se também sucessor macro por página. Não há comparabilidade direta com percentuais de outro corpus/artigo.",
           "Reparos/regressões contam sucessores-ouro recuperados/perdidos, não diferenças de quebras de palavras. Diagnóstico mantém categorias das transições-ouro do corretor. IC percentil por veículo e Wilcoxon bilateral Pratt sobre diferenças médias por veículo; parâmetros de reamostragem importados da bancada. RN tem um veículo: IC degenerado e teste não informativo."]
    if avaliacao:
        A = avaliacao
        ls += ["", "## Execução pontuada", "", "Modelo: `"+A["modelo"]["config"]["modelo"]+"`; revisão: `"+str(A["modelo"]["revisao_resolvida"])+"`.",
               "Escore: **"+A["escore"]+"**. "+("Subtrai logp_soma marginal e divide pelo mesmo n_tokens antes do log-softmax por fonte. FIM também subtrai a marginal de EOS." if A["marginal"] else "Ablação original: logp_media condicional, sem subtração marginal."),
               "Estado: "+("completo" if A["completa"] else "FUMAÇA/PARCIAL — sem conclusões nem seleção de pesos")+".",
               ("Escolhas congeladas" if A["ajuste_completo"] else "Configurações predefinidas da fumaça, sem escolha")+
               ": `"+json.dumps(A["selecao"],ensure_ascii=False)+"`.", "",
               "| Bancada | Cobertura |", "|---|---:|"]
        for co,s in A["cobertura"].items():
            ls.append(f"| {co} | {s['pontuadas']}/{s['esperadas']} |")
        if A["marginal"]:
            ls += ["", "Marginais: `"+A["marginal"]["diretorio"]+"`. Contexto vazio contém somente BOS; continuação idêntica à condicional, inclusive espaço prefixado."]
            ls += A["marginal"]["avisos"]
        rows = [r for rs in A["paginas"].values() for r in rs]
        if rows:
            tempos = [r["segundos_lm"] for r in rows]
            mems = {k:max(r["memoria_lm"].get(k,0) for r in rows) for k in {k for r in rows for k in r["memoria_lm"]}}
            ls += ["",f"Pontuação: {len(rows)} páginas; {fmt(sum(tempos))} s; média {fmt(statistics.mean(tempos))} s/página; inicialização (download/carga) {fmt(A['modelo']['segundos_carga'])} s.",
                   "Memória máxima observada (MiB): `"+json.dumps(mems,ensure_ascii=False,sort_keys=True)+"`.",
                   "O pico RSS inclui carga; tempo por página inclui tokenização e transferências, exclui carga e download. Memória CUDA é alocada/reservada pelo PyTorch."]
            if A["marginal"]:
                tm = sum(r["segundos_lm_marginal"] for r in rows)
                ls += [f"Pontuação marginal adicional: {fmt(tm)} s; carga {fmt(A['marginal']['modelo']['segundos_carga'])} s. "
                       f"Soma dos tempos de pontuação dos dois termos: {fmt(sum(tempos)+tm)} s. "
                       "O custo marginal é pago uma vez por destino/página e pode ser reutilizado entre configurações."]
            if not A["completa"]:
                ls += ["", "| Página pontuada | Pares | Segundos | Pico GPU alocado (MiB) |", "|---|---:|---:|---:|"]
                for r in rows:
                    ls.append(f"| `{r['page_id']}` | {r['pares']} | {fmt(r['segundos_lm'])} | {fmt(r['memoria_lm'].get('cuda_pico_alocado_mb'))} |")
        ls += ["", "| Bancada | Método | n | Quebras/pág [IC] | τ [IC] | Fidelidade 12 [IC] | Sucessor linhas [IC] | Arestas certas/ouro | Reparos/regressões | Páginas melhor/igual/pior (quebras) |",
               "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for co, mets in A["resultados"].items():
            for n,s in mets.items():
                if not s:
                    continue
                ms = s["metricas"]
                pg = s["paginas"]
                ls.append(f"| {co} | {n} | {s['n']} | {cel(ms['quebras'])} | {cel(ms['tau'],6)} | {cel(ms['fid12'],6)} | {cel(ms['sucessor_linhas'],6)} | {s['arestas_certas']}/{s['arestas_ouro']} ({fmt(100*s['acuracia_aresta_micro'],2)}%) | {s['reparos']}/{s['regressoes']} | {pg['melhoram']}/{pg['igualam']}/{pg['pioram']} |")
        ls += ["", "| Bancada | Método | Métrica | Δ [IC95 veículo] | p Wilcoxon veículo |", "|---|---|---|---:|---:|"]
        for co,mets in A["resultados"].items():
            for n,s in mets.items():
                if not s or n == "regra": continue
                for k,ds in s["contrastes"].items():
                    ls.append(f"| {co} | {n} | {k} | {cel(ds['delta'],6)} | {fmt(ds['wilcoxon_veiculo']['p'],6)} |")
        ls += ["", "### Diagnóstico por categoria", "", "| Bancada | Método | Categoria | Certas/ouro | Reparos/regressões |", "|---|---|---|---:|---:|"]
        for co,mets in A["resultados"].items():
            for n,s in mets.items():
                if not s: continue
                for tipo,d in s["diagnostico"].items():
                    ls.append(f"| {co} | {n} | {c.ROTULOS[tipo]} | {d['acertos']}/{d['ouro']} | {d['reparos']}/{d['regressoes']} |")
        if A["objetivos_ajuste"]:
            ls += ["", "### Grade — somente ajuste", "", "| Configuração | Δ quebras médio v4/RN | Δ τ médio v4/RN |", "|---|---:|---:|"]
            for n,v in A["objetivos_ajuste"].items():
                ls.append(f"| {n} | {fmt(v[0],6)} | {fmt(v[1],6)} |")
        ls += ["", "Avaliação detalhada em `avaliacao.json` junto a este relatório quando --saida é informado; predições em `pred/`, somente `page_id` e `ordem`. Sem --saida, a ablação mantém os destinos históricos."]
        if A["completa"]:
            ls += ["", "### Leitura dos resultados", "", conclusao(A),
                   "Avaliar também os contrastes de τ: reduzir quebras não garante preservar a ordem global. Seleção e testes sem correção de multiplicidade são exploratórios; o Golden v4 já foi usado no desenvolvimento da regra, e golden_v3_novo foi consultado antes. A referência silver é o fluxo PDF, com limitações em tabelas. Os percentuais não demonstram reprodução dos resultados de outro corpus."]
    abaixo = [(co,s) for co,s in man["bancadas"].items() if s["candidatos_cobertos"]/s["candidatos_ouro"] < .95]
    if abaixo:
        ls += ["", "## Limite dos candidatos", "",
               "O nível solicitado foi mantido sem ampliar candidatos usando resultados externos. Recall abaixo de 95%: "+
               "; ".join(co+" = "+fmt(100*s["candidatos_cobertos"]/s["candidatos_ouro"],2)+"%" for co,s in abaixo)+
               ". O denominador de recall contém bordas externas alcançáveis entre unidades; o teto de arestas usa todas as transições-ouro de linhas, incluindo as internas e inalcançáveis, por isso pode ser menor."]
    ls += ["", "## Estimativa de tempo no cluster", "",
           "Planejamento, não benchmark: operações aproximadas = 2 × parâmetros × tokens processados. São incluídos contexto e continuação de cada par, pois o script usa padding e não compartilha KV. Desconsidera padding, atenção, tokenização, I/O e download; a vazão efetiva assumida deve absorver parte desses custos. A GPU de 80 GB não foi identificada/medida."]
    palavras = sum(s["palavras_contexto"]+s["palavras_continuacao"] for s in man["bancadas"].values())
    tlo, thi = palavras*1.5, palavras*2.5
    ls += [f"Tokens supostos: {fmt(tlo,0)}–{fmt(thi,0)} = {palavras} palavras × 1,5–2,5 tokens/palavra. Vazão efetiva assumida: 20–80 TFLOP/s. Faixa deliberadamente ampla, não extrapolada da RTX.", "",
           "| Modelo bf16 | Memória apenas pesos (GB decimais) | Horas estimadas |", "|---|---:|---:|"]
    for nome,p in (("Qwen/Qwen3-8B (aprox.)",8e9),("Modelo ~30B",30e9)):
        ls.append(f"| {nome} | {fmt(p*2/1e9,1)} | {fmt(2*p*tlo/80e12/3600,2)}–{fmt(2*p*thi/20e12/3600,2)} |")
    ls += ["", "Pesos de ~30B deixam memória para ativações/KV em 80 GB, mas o lote pode precisar cair. O log de cada página permite recalcular ETA real após o primeiro arquivo. Modelo, revisão, tokenizer, dtype e lote devem permanecer fixos na retomada.", "",
           "## Números que dependem dos escores integrais do cluster", "",
           "- Tempo e memória reais dos modelos grandes, tokens reais e custo total.",
           "- Configurações escolhidas apenas em v4/RN, incluindo eventual conservação da regra.",
           "- Quebras/página, τ, sucessor macro e acurácia micro de aresta nas bancadas completas.",
           "- Reparos/regressões e diagnóstico por continuação, troca de coluna, margens e demais categorias.",
           "- IC e Wilcoxon por veículo contra a regra, cobertura completa e distância ao oráculo realizado.",
           "- Evidência sobre redução de quebras fora do ajuste; nenhum resultado da fumaça responde a essa pergunta.", ""]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(ls),encoding="utf-8")


def preparo(a):
    """Gera o documento solicitado somente a partir de arquivos e verificacoes."""
    man = carregar_manifesto()
    an = ancora()
    mm = b.ler(BASE/"pares_marginal/MANIFESTO.json")
    A = {modo: b.ler(E003/modo/"avaliacao.json") for modo in ("condicional", "contrastivo")}
    ids = [{r["page_id"] for r in av["paginas"]["golden_v4"]} for av in A.values()]
    exigir(ids[0] == ids[1] and len(ids[0]) == 3, "Preparo requer fumaca nas mesmas tres paginas")
    for modo,av in A.items():
        exigir(av["escore"] == modo and not av["ajuste_completo"], "Fumaca nao pode selecionar configuracao")
        exigir(all(not av["paginas"][co] for co in COORTES if co != "golden_v4"),
               "Fumaca avaliou outra bancada")
    # Mede compatibilidade de leitura, sem reavaliar paginas ou escolher pesos.
    legado_dir = BASE/"escores/Qwen_Qwen3-8B"
    legado_cfg = b.ler(legado_dir/"CONFIG.json")
    legados, duracoes = {}, []
    for co in COORTES:
        _, ss = ler_escores(co, man, legado_dir, legado_cfg)
        legados[co] = len(ss)
        duracoes += list(ss.values())
        exigir(sha(BASE/"pares_marginal"/(co+".jsonl")) == mm["bancadas"][co]["sha256"],
               "Arquivo marginal mudou")
    cond_rows = A["condicional"]["paginas"]["golden_v4"]
    cont_rows = A["contrastivo"]["paginas"]["golden_v4"]
    B = {r["page_id"]: r for r in cont_rows}
    mudancas = {dec: sum(r["ordens"][nome] != B[r["page_id"]]["ordens"][nome] for r in cond_rows)
                for dec,nome in A["condicional"]["selecao"].items()}
    ep = cond_rows[0]["page_id"]
    ec = next(r for r in b.jsonl(Path(A["condicional"]["diretorio_escores"])/"golden_v4.jsonl") if r["page_id"] == ep)
    em = next(r for r in b.jsonl(Path(A["contrastivo"]["marginal"]["diretorio"])/"golden_v4.jsonl") if r["page_id"] == ep)
    sc = next(s for s in ec["escores"] if s["id_destino"] is not None)
    sm = next(s for s in em["escores"] if s["id_destino"] == sc["id_destino"])
    exemplo = {"page_id": ep, "id_fonte": sc["id_fonte"], "id_destino": sc["id_destino"],
               "logp_soma_condicional": sc["logp_soma"], "logp_soma_marginal": sm["logp_soma"],
               "n_tokens": sc["n_tokens"], "escore_contrastivo": (sc["logp_soma"]-sm["logp_soma"])/sc["n_tokens"]}
    auditoria = {"ancora": an, "paginas_fumaca": sorted(ids[0]), "compatibilidade_legados": legados,
                 "paginas_ordem_diferente_entre_escores": mudancas,
                 "exemplo_contraste": exemplo,
                 "script_sha256": sha(__file__), "pontuador_sha256": sha(RAIZ/"cluster/pontuar_pares_lm.py")}
    gravar(E003/"verificacao_preparo.json", auditoria)
    total_dest = sum(v["destinos"] for v in mm["bancadas"].values())
    total_bytes = sum(v["bytes"] for v in mm["bancadas"].values())
    total_pares = sum(v["pares"] for v in man["bancadas"].values())
    velho_tempo = sum(r["segundos"] for r in duracoes)
    velho_pares = sum(len(r["escores"]) for r in duracoes)
    estimativa = velho_tempo*total_dest/velho_pares
    ls = ["# E003 — preparo do escore contrastivo", "",
          "Gerado por `venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py preparo`. "
          "Todos os números medidos vêm dos JSONs indicados; a estimativa de tempo é explicitamente calculada. Nenhum comando foi executado no cluster nesta tarefa.", "",
          "## Âncora e proteção dos dados", "",
          f"Âncora reexecutada em {an['n']} páginas: τ {fmt(an['medias']['tau'],6)} e {fmt(an['medias']['quebras'],6)} quebras/página. "
          "Sequências idênticas ao P2 histórico. Os IDs do manifesto foram conferidos contra `experimentos/TESTE_CEGO.lock` antes da leitura das páginas; sem interseção. "
          "Nada foi gravado em data/; data/labelstudio/ não foi lido nem usado. A fumaça avalia somente golden_v4. "
          "golden_v3_novo já foi consultado em rodadas anteriores e continua externo ao ajuste atual.", "",
          "## Contrato e compatibilidade", "",
          "`exportar-marginal` deriva os arquivos dos pares condicionais congelados, sem gerar candidatos novos. "
          "Mantém o JSONL agrupado por página, aceito pelo job: cada linha tem page_id e pares; dentro de pares há exatamente um item por id_destino distinto naquela página, inclusive null/FIM. "
          "Cada item tem id_fonte=null, contexto vazio e a continuação original (primeiras palavras já exportadas). Destinos diferentes com texto igual continuam distintos. "
          "Manifestos locais guardam hashes; somente os JSONLs e o pontuador são necessários no cluster.", "",
          "O contexto vazio é um único BOS, sem espaço ou quebra de linha. O BOS vem do tokenizer ou, quando ausente nele, da configuração do modelo. "
          "A continuação mantém o espaço prefixado e a tokenização separada original; FIM continua sendo EOS. "
          "O BOS não entra em n_tokens. Contextos condicionais não vazios mantêm o comportamento v1.", "",
          "Com `--escores-marginal DIR`: s=(logp_soma_condicional−logp_soma_marginal)/n_tokens. "
          "A subtração precede o log-softmax por fonte e a combinação com os priors. Sem a opção, usa logp_media condicional (ablação). "
          "O decodificador confere hashes dos pares e configurações, destinos únicos, texto idêntico, modelo/dtype, revisão disponível e n_tokens igual; falta de marginal é erro, sem descartar páginas silenciosamente. "
          "A revisão resolvida ausente nos escores legados é registrada como limitação, não presumida igual. "
          "A retomada do pontuador continua por página, com flush/fsync e reparo só da última linha interrompida. O hash do script mudou: pontuações novas usam outra pasta; as antigas continuam legíveis.", "",
          "Leitura/validação dos escores legados Qwen3-8B, sem nova avaliação: "+
          "; ".join(f"{co}: {n} páginas" for co,n in legados.items())+". Evidência: `verificacao_preparo.json`.", "",
          "## Exportação marginal", "",
          "Fonte: `resultados/ordem_lm/pares_marginal/MANIFESTO.json`.", "",
          "| Bancada | Páginas | Pares condicionais | Destinos marginais | Bytes JSONL | MiB |",
          "|---|---:|---:|---:|---:|---:|"]
    for co,s in mm["bancadas"].items():
        ls.append(f"| {co} | {s['paginas']} | {man['bancadas'][co]['pares']} | {s['destinos']} | {s['bytes']} | {fmt(s['bytes']/2**20)} |")
    ls += ["", f"Total: {total_dest} itens marginais / {total_pares} condicionais; {total_bytes} bytes ({fmt(total_bytes/2**20)} MiB) em JSONL. "
           f"Manifesto local: {(BASE/'pares_marginal/MANIFESTO.json').stat().st_size} bytes. Exportação: {fmt(mm['segundos_exportacao'])} s.", "",
           "As bancadas preservam as sobreposições históricas; não devem ser somadas como amostras independentes para inferência.", "",
           "## Fumaça local executada", "",
           "Execução sequencial em CPU, quatro threads, sem multiprocessing; modelo já presente no cache, acesso à rede desabilitado. "
           "Comandos da raiz, em PowerShell:", "", "```powershell",
           '$env:HF_HUB_OFFLINE="1"', '$env:TRANSFORMERS_OFFLINE="1"',
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py autoteste",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py exportar-marginal"]
    for entrada,saida in (("resultados/ordem_lm/pares", "escores_condicional"),
                          ("resultados/ordem_lm/pares_marginal", "escores_marginal")):
        ls.append("venv/Scripts/python.exe -B cluster/pontuar_pares_lm.py --entrada "+entrada+
                  " --saida resultados/e003_lm/"+saida+
                  " --modelo Qwen/Qwen3-0.6B --revisao c1899de289a04d12100db370d81485cdf75e47ca --dtype float32 --lote 4 --threads 4 --dispositivo cpu --bancada golden_v4 --limite-paginas 3")
    cond = "resultados/e003_lm/escores_condicional/Qwen_Qwen3-0.6B"
    marg = "resultados/e003_lm/escores_marginal/Qwen_Qwen3-0.6B"
    ls += ["venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores "+cond+" --saida resultados/e003_lm/condicional",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores "+cond+" --escores-marginal "+marg+" --saida resultados/e003_lm/contrastivo",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py preparo", "```", "",
           "| Termo | Páginas | Itens pontuados | Tokens de continuação | Tempo de pontuação (s) | Carga (s) | Pico RSS (MiB) |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for modo,path in (("condicional", Path(cond)), ("marginal", Path(marg))):
        cfg = b.ler(path/"CONFIG.json")
        rs = list(b.jsonl(path/"golden_v4.jsonl"))
        ls.append(f"| {modo} | {len(rs)} | {sum(len(r['escores']) for r in rs)} | {sum(s['n_tokens'] for r in rs for s in r['escores'])} | "
                  f"{fmt(sum(r['segundos'] for r in rs))} | {fmt(cfg['segundos_carga'])} | "
                  f"{fmt(max([cfg['memoria_carga'].get('pico_rss_mb',0)]+[r['memoria'].get('pico_rss_mb',0) for r in rs]))} |")
    tok = b.ler(Path(marg)/"CONFIG.json")["tokenizacao"]
    ls += ["", f"BOS usado: {tok['bos_token_id']} ({tok['bos_origem']}); EOS: {tok['eos_token_id']}. "
           "A contagem de tokens condicional/marginal foi conferida para cada aresta na decodificação, incluindo FIM. "
           "Os autotestes exercitam deduplicação, mudança de preferência pelo contraste, divisão por n_tokens, recusa de tokens divergentes e cobertura dos decodificadores.", "",
           f"Exemplo real (primeira aresta não-FIM da primeira página): ({fmt(sc['logp_soma'],6)} − ({fmt(sm['logp_soma'],6)})) / "
           f"{sc['n_tokens']} = {fmt(exemplo['escore_contrastivo'],6)}. IDs e valores completos em `verificacao_preparo.json`.", "",
           "Páginas da fumaça:", ""]+["- `"+pid+"`" for pid in sorted(ids[0])]
    ls += ["", "As configurações são as predefinidas para fumaça; não houve escolha de parâmetros ou checkpoint. "
           "IC95 e Wilcoxon abaixo são descritivos de uma amostra mínima; não sustentam conclusão sobre H3.", "",
           "| Bancada | Condicional pontuadas/esperadas | Contrastivo pontuadas/esperadas |",
           "|---|---:|---:|"]
    for co in COORTES:
        x,y = (av["cobertura"][co] for av in A.values())
        ls.append(f"| {co} | {x['pontuadas']}/{x['esperadas']} | {y['pontuadas']}/{y['esperadas']} |")
    ls += ["", "### Golden v4 — somente fumaça", "",
           "| Escore | Decoder | Quebras/pág | τ | Fidelidade 12 | Sucessor linhas | Δ quebras [IC95 veículo] | Wilcoxon veículo p | Melhor/igual/pior | Reparos/regressões |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for modo,av in A.items():
        for dec,nome in av["selecao"].items():
            s = av["resultados"]["golden_v4"][nome]
            ms,ds,pg = s["metricas"],s["contrastes"]["quebras"],s["paginas"]
            ls.append(f"| {modo} | {dec} ({nome}) | {fmt(ms['quebras']['media'])} | {fmt(ms['tau']['media'],6)} | "
                      f"{fmt(ms['fid12']['media'],6)} | {fmt(ms['sucessor_linhas']['media'],6)} | {cel(ds['delta'])} | "
                      f"{fmt(ds['wilcoxon_veiculo']['p'],6)} | {pg['melhoram']}/{pg['igualam']}/{pg['pioram']} | {s['reparos']}/{s['regressoes']} |")
    ls += ["", "Mudanças de ordem entre condicional e contrastivo: "+
           "; ".join(f"{dec}: {n} páginas" for dec,n in mudancas.items())+". "
           "Régua importada de erros_ponta_a_ponta/bancada_ordenadores; entrada e desempates seguem entrada-{page_id}. "
           "Cobertura integral de unidades e palavras validada para cada predição. Detalhes, IC95 e Wilcoxon de todas as métricas e diagnóstico por classe estão em "
           "`condicional/AVALIACAO.md`, `contrastivo/AVALIACAO.md` e nos respectivos `avaliacao.json`.", "",
           "### Golden v3 novo e teste silver", "",
           "Arquivos marginais exportados; nenhuma página dessas bancadas foi pontuada ou avaliada nesta fumaça. "
           "Os contrastes externos, páginas melhor/igual/pior e reparos/regressões completos aguardam os escores do cluster. RN também aguarda pontuação marginal integral.", "",
           "## Comandos preparados para o cluster — NÃO executados", "",
           "Copiar apenas os JSONLs de entrada automática e os scripts, sem anotações nem o manifesto de auditoria. "
           "Estes comandos usam o alias SSH já configurado no projeto. Executar da raiz local quando autorizado:", "", "```powershell",
           'ssh dgx-spark "mkdir -p ~/tcc/ordem_lm/pares_marginal ~/tcc/repo/cluster ~/tcc/logs"',
           "scp cluster/pontuar_pares_lm.py cluster/requisitos_pontuar.txt dgx-spark:~/tcc/ordem_lm/",
           "scp cluster/job_pontuar.sh dgx-spark:~/tcc/repo/cluster/",
           "scp "+" ".join("resultados/ordem_lm/pares_marginal/"+co+".jsonl" for co in COORTES)+" dgx-spark:~/tcc/ordem_lm/pares_marginal/",
           'ssh dgx-spark "cd ~/tcc/repo && sbatch --partition=hpc-spark-45 --time=02:00:00 cluster/job_pontuar.sh Qwen/Qwen3-8B --entrada pares_marginal --saida escores_marginal"',
           "```", "",
           "O job executa em ~/tcc/ordem_lm; os argumentos extras aparecem depois dos defaults, portanto "
           "--entrada pares_marginal e --saida escores_marginal prevalecem. Mantém bf16, lote e quatro threads; "
           "usa a partição principal, PYTHONNOUSERSITE=1 e retomada por página. Reenviar o mesmo comando retoma quando a saída tem configuração/hash idênticos. "
           "Não misturar as novas marginais com as pastas condicionais existentes. O nome sanitizado do modelo é acrescentado à saída.", "",
           "Após o job, trazer os escores e decodificar localmente:", "", "```powershell",
           "New-Item -ItemType Directory -Force resultados/ordem_lm/escores_marginal | Out-Null",
           "scp -r dgx-spark:~/tcc/ordem_lm/escores_marginal/Qwen_Qwen3-8B resultados/ordem_lm/escores_marginal/",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --saida resultados/e003_lm/ablacao_8b",
           "venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B --escores-marginal resultados/ordem_lm/escores_marginal/Qwen_Qwen3-8B --saida resultados/e003_lm/contrastivo_8b",
           "```", "",
           "## Estimativa de tempo", "",
           f"Proxy calculada com os escores condicionais Qwen3-8B já existentes na {legado_cfg['gpu']}: {velho_pares} itens em {fmt(velho_tempo)} s, "
           f"ou {fmt(velho_tempo/velho_pares,6)} s/item. À mesma vazão por item, {total_dest} marginais custariam "
           f"{fmt(estimativa)} s = {fmt(estimativa/60,2)} min, mais carga/ambiente/fila. "
           f"A carga histórica registrada foi {fmt(legado_cfg['segundos_carga'])} s. Fonte: `resultados/ordem_lm/escores/Qwen_Qwen3-8B/`.", "",
           "É uma estimativa de planejamento, não uma medição marginal no cluster: BOS encurta a entrada, "
           "mas padding, distribuição de comprimentos, EOS, lote e tokenização afetam a vazão. "
           "O limite de tempo solicitado no comando deixa folga; atualizar a ETA com as primeiras páginas do job. "
           "Os tempos da fumaça em CPU/0.6B não são extrapolados para a GB10/8B.", "",
           "## O que falta para o 2×2 (depende do E004)", "",
           "| Geometria | Sem LM | Com LM contrastivo |", "|---|---|---|",
           "| Fixa (regra/priors) | mesmos candidatos e decoder, peso LM zero | mesmos candidatos e decoder, contraste 8B |",
           "| Aprendida (LightGBM, E004) | escores de arestas do E004 | mesmos escores + contraste 8B |", "",
           "- Pontuar todas as marginais com Qwen3-8B e auditar identidade dos pesos/tokenizer: "
           "a revisão resolvida dos condicionais antigos está ausente. Se não for possível certificar a revisão, registrar essa limitação ou repontuar os dois termos com revisão fixada, sem sobrescrever os escores antigos.",
           "- Aguardar o E004 definir e exportar os escores geométricos aprendidos. Congelar um mesmo conjunto de candidatos e um mesmo decoder para as quatro células; "
           "se os candidatos/continuações mudarem, pontuar as arestas novas e exportar suas marginais, mantendo o teste cego lacrado.",
           "- Congelar grade/normalização e escolher pesos somente em golden_v4 + validação RN. "
           "A fumaça 0.6B só verifica o caminho. A seleção atual do script é a grade histórica de geometria fixa; o adaptador do E004 e a comparação controlada das quatro células continuam pendentes.",
           "- Produzir as três bancadas separadas (v4, v3 novo, teste silver), com RN separada para ajuste; "
           "reportar Δ/IC95 por veículo e Wilcoxon por veículo, páginas melhor/igual/pior, reparos/regressões de sucessores, cobertura e custo, incluindo o híbrido 67 como baseline forte. "
           "A régua atual preserva todos os elementos marginais; uma análise só do corpo ainda exige uma política comum e explícita.",
           "- Tratar a comparação como exploratória: v4 já foi usado no desenvolvimento da regra, v3 novo já foi consultado e silver usa fluxo PDF ruidoso. "
           "Aplicar o critério pré-registrado do cartão E003 somente após o 2×2 completo; avaliação confirmatória do teste cego cabe ao orquestrador.", ""]
    (E003/"PREPARO.md").write_text("\n".join(ls), encoding="utf-8")
    print("Preparo escrito em "+str(E003/"PREPARO.md"), flush=True)


def autoteste():
    ordem = ["a","b","c"]
    sc = {"a":{"b":5.,"c":4.,None:-10.}, "b":{"b":-999.,"c":10.,None:-10.}, "c":{"a":10.,None:0.}}
    sc["b"].pop("b")
    out = max_regret(ordem,sc)
    exigir(sorted(out) == sorted(ordem), "Autoteste cobertura")
    # Regret evita que a tome c quando b depende dela com vantagem maior.
    sc = {"a":{"c":10.,"b":9.,None:0.},"b":{"c":9.,None:0.},"c":{None:0.}}
    exigir(max_regret(ordem,sc) == ordem, "Autoteste roubo de aresta")
    exigir(seletiva(ordem,sc,sc,100.) == ordem, "Autoteste identidade")
    exigir(seletiva(ordem,sc,sc,0.) == ["a","c","b"], "Autoteste movimento local")
    ps = [{"id_fonte": "a", "id_destino": z, "contexto": "texto", "continuacao": str(z),
           "sucessor_regra": z == "b", "prior_geo": 0.} for z in ("b", "c", None)]
    ps += [{**ps[0], "id_fonte": "c"}]
    pm = pares_marginais({"page_id": "controle", "pares": ps})
    exigir(len(pm["pares"]) == 3 and all(p["contexto"] == "" for p in pm["pares"]),
           "Autoteste deduplicacao marginal/FIM")
    ss = [{"id_fonte": p["id_fonte"], "id_destino": p["id_destino"],
           "logp_soma": v*2, "logp_media": v, "n_tokens": 2} for p,v in zip(ps, (-1.,-2.,-3.,-1.))]
    mm = {z: {"logp_soma": v*2, "logp_media": v, "n_tokens": 2} for z,v in zip(("b","c",None), (-1.,-5.,-3.))}
    cfg = {"w_regra": 0., "w_geo": 0., "w_lm": 1., "w_nsp": 0.}
    cond, _ = combinar(ps, ss, cfg)
    contr, _ = combinar(ps, ss, cfg, mm)
    exigir(max(cond["a"], key=cond["a"].get) == "b" and max(contr["a"], key=contr["a"].get) == "c",
           "Autoteste contraste nao mudou preferencia")
    exigir(math.isclose(contr["a"]["c"]-contr["a"]["b"], 3.), "Autoteste divisao por tokens")
    ruins = {**mm, "b": {**mm["b"], "n_tokens": 1, "logp_soma": -1.}}
    try:
        combinar(ps, ss, cfg, ruins)
    except ValueError:
        pass
    else:
        raise ValueError("Autoteste deveria recusar tokens marginais divergentes")
    print("Autotestes de cobertura, ciclos, regret, seletiva e contraste marginal aprovados",flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="acao",required=True)
    ex = sub.add_parser("exportar")
    ex.add_argument("--contexto",choices=("caminho","linha"),default="caminho")
    ex.add_argument("--palavras-contexto",type=int,default=48)
    ex.add_argument("--palavras-continuacao",type=int,default=24)
    sub.add_parser("exportar-marginal")
    de = sub.add_parser("decodificar")
    de.add_argument("--escores",type=Path,required=True)
    de.add_argument("--escores-marginal",type=Path,help="Diretorio do modelo com CONFIG.json e escores marginais")
    de.add_argument("--saida",type=Path,help="Isola avaliacao, relatorio e predicoes nesta pasta")
    sub.add_parser("autoteste")
    sub.add_parser("preparo")
    a = ap.parse_args()
    autoteste()
    if a.acao == "exportar":
        exigir(a.palavras_contexto > 0 and a.palavras_continuacao > 0,"Limites precisam ser positivos")
        exportar(a)
    elif a.acao == "decodificar":
        decodificar(a)
    elif a.acao == "exportar-marginal":
        exportar_marginal(a)
    elif a.acao == "preparo":
        preparo(a)


if __name__ == "__main__":
    main()
