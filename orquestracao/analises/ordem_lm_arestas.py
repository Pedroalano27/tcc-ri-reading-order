"""Exporta arestas textuais e combina continuidade causal com regra congelada.

Importa candidatos, categorias e regua oficial sem chamar mains ou gravadores
antigos. Nenhum texto/referencia humana vai para o cluster. Ouro entra somente
na auditoria, na selecao em v4/RN e no oraculo explicitamente identificado.
Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/ordem_lm_arestas.py
 exportar [--contexto caminho|linha] [--palavras-contexto 48]
 decodificar --escores resultados/ordem_lm/escores/Qwen_Qwen3-8B
O segundo comando aceita cobertura parcial (fumaca) sem selecionar configuracao.
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
COORTES = ("golden_v4", "golden_v3_novo", "teste_silver", "validacao_silver")
AJUSTE = ("golden_v4", "validacao_silver")
METRICAS = ("quebras", "tau", "sucessor_linhas")
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
    with p.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+"\n")


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


def combinar(pares, escores, cfg):
    grupos = collections.defaultdict(list)
    for p, s in zip(pares, escores):
        exigir((p["id_fonte"], p["id_destino"]) == (s["id_fonte"], s["id_destino"]), "Pares/escores fora de ordem")
        exigir(math.isfinite(s["logp_media"]) and s["n_tokens"] > 0, "Escore invalido")
        grupos[p["id_fonte"]].append((p,s))
    scores, lm = {}, {}
    for u, ps in grupos.items():
        vals = [s["logp_media"] for _,s in ps]
        mx = max(vals)
        normal = mx+math.log(sum(math.exp(v-mx) for v in vals))
        scores[u], lm[u] = {}, {}
        for p,s in ps:
            v = p["id_destino"]
            lp = s["logp_media"]-normal
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
    res["acuracia_aresta_micro"] = res["arestas_certas"]/res["arestas_ouro"] if res["arestas_ouro"] else None
    res["diagnostico"] = {t: {k: sum(r["metodos"][nome]["diagnostico"][t][k] for r in rows)
                               for k in ("ouro", "acertos", "reparos", "regressoes")} for t in c.TIPOS}
    return res


def ler_escores(co, man, escdir, cfgmodelo):
    pp = BASE/"pares"/(co+".jsonl")
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


def processar(co, man, escdir, cfgmodelo, configs):
    pares, scores = ler_escores(co, man, escdir, cfgmodelo)
    rows = []
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
        for cfg in configs:
            t = time.perf_counter()
            sc, lm = combinar(ps, ss, cfg)
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
    man = b.ler(BASE/"pares/MANIFESTO.json")
    exigir(man["fontes"] == fontes(), "Fontes mudaram desde exportacao; aborte e audite")
    man["ancora"] = ancora()
    escdir = a.escores.resolve()
    cfgmodelo = b.ler(escdir/"CONFIG.json")
    dados, cobertura = {}, {}
    # Apenas desenvolvimento recebe toda a grade. Congela antes de abrir externos.
    for co in AJUSTE:
        dados[co], cobertura[co] = processar(co,man,escdir,cfgmodelo,GRADE)
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
    out = BASE/"avaliacao"/escdir.name
    if ajuste_completo:
        congelada = {"selecao":selecao,"objetivos":objetivos,"grade":GRADE,
                     "assinatura_ajuste":c.digest([cfgmodelo["config"],GRADE,
                        {co:sha(escdir/(co+".jsonl")) for co in AJUSTE},
                        {co:man["bancadas"][co]["sha256"] for co in AJUSTE}])}
        sp = out/"selecao.json"
        if sp.exists():
            exigir(b.ler(sp) == congelada, "Selecao congelada divergiu; audite antes de avaliar externos")
        else:
            gravar(sp,congelada)
    configs = [cfg for cfg in GRADE if cfg["nome"] in selecao.values()]
    for co in COORTES:
        if co not in AJUSTE:
            dados[co], cobertura[co] = processar(co,man,escdir,cfgmodelo,configs)
    nomes = list(dict.fromkeys(["regra", *selecao.values(), "oraculo"]))
    saida = {"modelo":cfgmodelo, "diretorio_escores":str(escdir), "cobertura":cobertura,
             "ajuste_completo":ajuste_completo, "completa":all(v["completa"] for v in cobertura.values()),
             "selecao":selecao, "grade":GRADE, "objetivos_ajuste":objetivos,
             "resultados": {co:{n:resumir(rows,n) for n in nomes} for co,rows in dados.items()},
             "paginas":dados, "decodificador_sha256":sha(__file__),
             "escores_sha256":{p.name:sha(p) for p in escdir.glob("*.jsonl")}}
    gravar(out/"avaliacao.json", saida)
    for co,rows in dados.items():
        if not rows:
            continue
        for dec,n in [*selecao.items(), ("oraculo","oraculo")]:
            # Mesmo fallback regra recebe contrato proprio das duas variantes.
            variante = escdir.name+"_"+(n if n != "regra" else dec+"_regra")
            dest = b.OUT/"pred"/f"lm_arestas_{variante}__linhas__{co}.jsonl"
            # indice_pred exige exatamente estas duas chaves; tempos ficam no JSON.
            jsonl(dest,[{"page_id":r["page_id"], "ordem":r["ordens"][n]} for r in rows])
    relatorio(man,saida)


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


def relatorio(man, avaliacao=None):
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
           "Combinação: w_regra × indicador de sucessor original + w_geo × prior + w_lm × log-softmax(logp médio por fonte) + w_nsp × (logit IsNext − NotNext). O corretor não tinha prior escalar por candidato; usa-se sobreposição horizontal/(1 + distância vertical em alturas). FIM tem prior zero e compete com EOS, o que pode favorecer finais curtos.",
           "Seletiva: melhor candidato precisa vencer o sucessor original tanto no LM quanto na combinação por margem estrita; move uma unidade em raio de doze posições, preserva arestas já aceitas e cobertura. Global: recalcula melhor−segunda melhor aresta viável por fonte, fixa primeiro o maior regret, impede ciclos e grau de entrada/saída maior que um; FIM privado permite vários caminhos. Costura pela primeira unidade de cada caminho na regra. Esta é uma implementação operacional de max-regret, não reprodução certificada do artigo.",
           "Grade predefinida: "+str(len(GRADE))+" configurações, descritas no JSON da avaliação. Seleção minimiza média dos deltas de quebras das duas bancadas de ajuste, com peso igual por bancada; desempata pelo maior τ. Se nenhuma configuração reduzir quebras, conserva a regra. Sem ajuste completo não há seleção. A escolha é salva em `selecao.json` antes de avaliar externos, que recebem somente as configurações escolhidas.",
           "Oráculo: teto independente por aresta = sucessores-ouro alcançáveis presentes nos candidatos, incluindo bordas internas com adjacência preservada. É um limite otimista, pois a linha inteira também precisa estar intacta; não é teto de quebras ou τ. A ordem oracular fixa arestas-ouro realizáveis com prioridade alta e aplica a mesma cobertura/costura; sua realização pode ficar abaixo do teto independente. Ouro nunca entra nos decoders automáticos.",
           "Métricas oficiais importadas: τ de palavras, quebras e sucessor de linhas. Acurácia de aresta micro = sucessores-ouro de linhas inteiras recuperados / todas as transições-ouro entre linhas; inclui bordas internas aos átomos, exclui FIM. Reporta-se também sucessor macro por página. Não há comparabilidade direta com percentuais de outro corpus/artigo.",
           "Reparos/regressões contam sucessores-ouro recuperados/perdidos, não diferenças de quebras de palavras. Diagnóstico mantém categorias das transições-ouro do corretor. IC percentil por veículo e Wilcoxon bilateral Pratt sobre diferenças médias por veículo; parâmetros de reamostragem importados da bancada. RN tem um veículo: IC degenerado e teste não informativo."]
    if avaliacao:
        A = avaliacao
        ls += ["", "## Execução pontuada", "", "Modelo: `"+A["modelo"]["config"]["modelo"]+"`; revisão: `"+str(A["modelo"]["revisao_resolvida"])+"`.",
               "Estado: "+("completo" if A["completa"] else "FUMAÇA/PARCIAL — sem conclusões nem seleção de pesos")+".",
               ("Escolhas congeladas" if A["ajuste_completo"] else "Configurações predefinidas da fumaça, sem escolha")+
               ": `"+json.dumps(A["selecao"],ensure_ascii=False)+"`.", "",
               "| Bancada | Cobertura |", "|---|---:|"]
        for co,s in A["cobertura"].items():
            ls.append(f"| {co} | {s['pontuadas']}/{s['esperadas']} |")
        rows = [r for rs in A["paginas"].values() for r in rs]
        if rows:
            tempos = [r["segundos_lm"] for r in rows]
            mems = {k:max(r["memoria_lm"].get(k,0) for r in rows) for k in {k for r in rows for k in r["memoria_lm"]}}
            ls += ["",f"Pontuação: {len(rows)} páginas; {fmt(sum(tempos))} s; média {fmt(statistics.mean(tempos))} s/página; inicialização (download/carga) {fmt(A['modelo']['segundos_carga'])} s.",
                   "Memória máxima observada (MiB): `"+json.dumps(mems,ensure_ascii=False,sort_keys=True)+"`.",
                   "O pico RSS inclui carga; tempo por página inclui tokenização e transferências, exclui carga e download. Memória CUDA é alocada/reservada pelo PyTorch."]
            if not A["completa"]:
                ls += ["", "| Página pontuada | Pares | Segundos | Pico GPU alocado (MiB) |", "|---|---:|---:|---:|"]
                for r in rows:
                    ls.append(f"| `{r['page_id']}` | {r['pares']} | {fmt(r['segundos_lm'])} | {fmt(r['memoria_lm'].get('cuda_pico_alocado_mb'))} |")
        ls += ["", "| Bancada | Método | n | Quebras/pág [IC] | τ [IC] | Sucessor linhas [IC] | Arestas certas/ouro | Reparos/regressões |",
               "|---|---|---:|---:|---:|---:|---:|---:|"]
        for co, mets in A["resultados"].items():
            for n,s in mets.items():
                if not s:
                    continue
                ms = s["metricas"]
                ls.append(f"| {co} | {n} | {s['n']} | {cel(ms['quebras'])} | {cel(ms['tau'],6)} | {cel(ms['sucessor_linhas'],6)} | {s['arestas_certas']}/{s['arestas_ouro']} ({fmt(100*s['acuracia_aresta_micro'],2)}%) | {s['reparos']}/{s['regressoes']} |")
        ls += ["", "| Bancada | Método | Δ quebras [IC veículo] | p veículo | Δ τ [IC veículo] | p veículo |", "|---|---|---:|---:|---:|---:|"]
        for co,mets in A["resultados"].items():
            for n,s in mets.items():
                if not s or n == "regra": continue
                ds = s["contrastes"]
                ls.append(f"| {co} | {n} | {cel(ds['quebras']['delta'])} | {fmt(ds['quebras']['wilcoxon_veiculo']['p'],6)} | {cel(ds['tau']['delta'],6)} | {fmt(ds['tau']['wilcoxon_veiculo']['p'],6)} |")
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
        ls += ["", "Avaliação detalhada por página, tempos, grade, seleção e contrastes em `avaliacao/"+Path(A["diretorio_escores"]).name+"/avaliacao.json`. Predições no contrato estrito `resultados/ordenadores_sem_caixas/pred/lm_arestas_<modelo>_<variante>__linhas__<bancada>.jsonl` (somente `page_id` e `ordem`, como exige `indice_pred`)."]
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
    MD.write_text("\n".join(ls),encoding="utf-8")


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
    print("Autotestes de cobertura, ciclos, regret e seletiva aprovados",flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="acao",required=True)
    ex = sub.add_parser("exportar")
    ex.add_argument("--contexto",choices=("caminho","linha"),default="caminho")
    ex.add_argument("--palavras-contexto",type=int,default=48)
    ex.add_argument("--palavras-continuacao",type=int,default=24)
    de = sub.add_parser("decodificar")
    de.add_argument("--escores",type=Path,required=True)
    sub.add_parser("autoteste")
    a = ap.parse_args()
    autoteste()
    if a.acao == "exportar":
        exigir(a.palavras_contexto > 0 and a.palavras_continuacao > 0,"Limites precisam ser positivos")
        exportar(a)
    elif a.acao == "decodificar":
        decodificar(a)


if __name__ == "__main__":
    main()
