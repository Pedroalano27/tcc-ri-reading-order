"""Diagnostica margens e testa uma variante da regra sobre linhas, em CPU.

Importa o emparelhamento de transicoes da tarefa 05 e a regua oficial de
palavras, sem mudar seus modulos ou caches. Ancoras precedem os numeros novos.
Le uma pagina por vez; nao treina, nao carrega detector, nao consulta classes
humanas ao prever. Resultados e checkpoints ficam somente em resultados/.

Uso da raiz: venv/Scripts/python.exe -B
  orquestracao/analises/regra_margens_v2.py --etapa diagnostico
  ... --etapa tudo
Repetir o comando retoma as paginas com a mesma assinatura de fontes/entrada.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", OMP_NUM_THREADS="4",
                  MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4")
import argparse
import collections
import gc
import json
import re
import statistics
import time
import types
import unicodedata
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import erros_ponta_a_ponta as e
from src.eval.protocolo import ordem_entrada
from src.eval import politica_margens as pm

BASE = RAIZ / "resultados/margens_e_transversais_cache"
PAINEIS = RAIZ / "resultados/margens_e_transversais"
MD = RAIZ / "resultados/margens_e_transversais.md"
PRED = RAIZ / "resultados/ordenadores_sem_caixas/pred"
HUMANAS = ("golden_v4", "golden_v3_novo")
METRICAS = c.METRICAS
VERSAO_DIAG = "margens-diagnostico-2-classes-apenas-diagnostico"
VERSAO_REGRA = "margens-regra-1"
ROT = {
    "a": "Cabeçalho enviado para depois do corpo",
    "b": "Rodapé antes de parte do corpo",
    "c": "Cabeçalho multilinha/lado a lado fora de ordem",
    "d": "Marca marginal em posição errada",
    "e": "Corpo tratado como margem pelo limiar",
    "f": "Outro / evidência insuficiente",
}
R = {}
PRAZO = None


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def ler(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def hash_obj(obj):
    return b.digest(obj)


def gravar(p, obj):
    p = Path(p).resolve()
    permitido = (p == MD or p.is_relative_to(BASE) or p.is_relative_to(PAINEIS)
                 or p.parent == PRED and p.name.startswith("regra_margens_v2__linhas__"))
    exigir(permitido, f"Saída fora do escopo: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def vigiar(atualizar=True):
    if PRAZO and time.monotonic() >= PRAZO:
        raise RuntimeError("Prazo atingido; repetir o comando retoma os caches.")
    mem = b.memoria()
    if mem:
        if atualizar:
            R["memoria_minima_mb"] = min(R.get("memoria_minima_mb", mem["ram_livre_mb"]), mem["ram_livre_mb"])
        exigir(mem["ram_livre_mb"] >= 900 and mem["commit_livre_mb"] >= 1200,
               f"Parada retomável por memória: {mem}")


def fonte_assinatura():
    paths = set(b.DEP_PATHS) | {Path(c.__file__), Path(pm.__file__),
              RAIZ / "data/processed/splits.json", e.JSON,
              RAIZ / "data/golden/golden_v4/tarefas.jsonl",
              RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl"}
    out = {b.rel(p): b.sha(p) for p in sorted(paths)}
    return out


def texto_normal(t):
    return "".join(x for x in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(x) != "Mn")


RE_CAB = re.compile(r"diario|oficial|edicao|pagina|ano\s+[ivxlcdm\d]|\b(?:segunda|terca|quarta|quinta|sexta|sabado|domingo)\b|imprensa|estado\s+d|municipio\s+d|prefeitura|www\.|https?://", re.I)
RE_ROD = re.compile(r"assinad|certific|autentic|verific|digital|imprensa|documento|publicac|www\.|https?://|icp.brasil", re.I)
RE_NUM = re.compile(r"^(?:\d{1,4}|p[aá]g(?:ina)?[. :]*\d{1,4})$", re.I)


def evidencia(ctx):
    """Papeis automaticos exploratorios; nao sao classes humanas anotadas."""
    W, H = (ctx["auto"]["dimensions"][k] for k in ("width", "height"))
    pap, sinais = {}, {}
    for u in ctx["cs"]:
        uid, bb = u["id"], u["bbox"]
        t = texto_normal(u.get("text", ""))
        cy = c.cy(u) / H
        lateral = bb[2] < .07*W or bb[0] > .93*W or bb[3]-bb[1] > 3*max(1., bb[2]-bb[0])
        marca = ctx["margem"].get(uid) == "marca" or lateral or (
            bool(RE_NUM.fullmatch(u.get("text", "").strip())) and (cy < .15 or cy > .85))
        cab = cy < .10 and bool(RE_CAB.search(t)) and not (len(u['ks']) > 10 and t[:1].islower())
        rod = cy > .93 and bool(RE_ROD.search(t)) and not (len(u['ks']) > 10 and t[:1].islower())
        perto = [z for z in ctx["cs"] if z["id"] != uid and c.tipo_unidade(z) == "texto"
                 and c.sobreposicao(u, z) > .65 and abs(c.cy(z)-c.cy(u)) < 1.8*ctx["h"]]
        corpo = not (cab or rod or marca) and bool(perto) and (
            len(u["ks"]) >= 9 or t[:1].islower() or t.endswith(("-", ",", ";")))
        if marca:
            papel = "marca"
        elif cab:
            papel = "cabecalho"
        elif rod:
            papel = "rodape"
        elif corpo:
            papel = "corpo"
        elif ctx["margem"].get(uid) == "topo":
            papel = "cabecalho"
        elif ctx["margem"].get(uid) == "rodape":
            papel = "rodape"
        else:
            papel = "corpo"
        pap[uid] = papel
        sinais[uid] = {"papel": papel, "lexico_cabecalho": cab, "lexico_rodape": rod,
                       "continuidade_corpo": corpo, "margem_original": ctx["margem"].get(uid),
                       "y_relativo": cy}
    return pap, sinais


def subtipo(ctx, a, z, pap):
    """Atribui um subtipo exclusivo ao sucessor perdido, com precedencia."""
    us = [uid for uid in (a, z) if uid is not None]
    if any(pap[uid] == "corpo" and uid in ctx["margem"] for uid in us):
        return "e"
    if any(pap[uid] == "marca" for uid in us):
        return "d"
    if all(pap[uid] == "cabecalho" for uid in us) and len(us) == 2:
        return "c"
    corpos = [uid for uid in ctx["ordem"] if pap[uid] == "corpo"]
    if any(pap[uid] == "cabecalho" and any(ctx["rank_regra"][v] < ctx["rank_regra"][uid] for v in corpos)
           for uid in us):
        return "a"
    if any(pap[uid] == "rodape" and any(ctx["rank_regra"][v] > ctx["rank_regra"][uid] for v in corpos)
           for uid in us):
        return "b"
    return "f"


def medir(obj, p, ordem):
    """Reusa medir() da tarefa 05 e so persiste em nosso cache."""
    q = b.referencia(obj, p)
    exp = b.expansoes(obj, p)
    seq = [k for uid in ordem for k in exp[uid]]
    ids = b.auditar_unidades(p, obj)
    exigir(len(ordem) == len(ids) and set(ordem) == set(ids), "Predição inválida")
    chave = hash_obj([R["assinatura_fontes"], q, seq])
    cp = BASE / "metricas" / (chave + ".json")
    if cp.exists():
        med = ler(cp)
    else:
        # Cache existente da bancada pode ser lido, nunca criado/modificado.
        fp = b.digest([b.VERSAO, b.assinatura_metricas(), q, seq])
        antigo = b.OUT / "cache/metricas" / (fp + ".json")
        if antigo.exists():
            med = ler(antigo)
            med = {k: med[k] for k in METRICAS if k != "piso_interno"}
        else:
            med = e.medir(q, seq, [], {}, "P0")
            med = {k: med[k] for k in METRICAS if k != "piso_interno"}
        gravar(cp, med)
    med = {**med, "piso_interno": sum(len(e.eventos(ks, q["gt_w"])) for ks in exp.values())}
    return med, seq, q, exp


# Namespace isolado: o emparelhamento original chama nosso cache de metricas.
PREPARAR = types.FunctionType(c.preparar_avaliacao.__code__,
                             {**c.preparar_avaliacao.__globals__, "medir": medir})


def salvar():
    gravar(BASE / "estado.json", R)
    gravar(MD, relatorio())


def ancoras():
    historico = ler(e.JSON)
    antigos = {r["page_id"]: {m: {k: r["metodos"][m][k] for k in ("tau", "quebras", "seq")}
                             for m in ("P2", "P1m")}
               for r in historico["paginas"] if r["coorte"] == "v4"}
    del historico
    rows = []
    for obj, p in b.paginas("golden_v4", "linhas"):
        vigiar()
        auto = c.automatico(p)
        ordem, _ = b.prever(auto, obj["palavras"], "regra_colunas")
        exp = b.expansoes(obj, p)
        seq = [k for uid in ordem for k in exp[uid]]
        exigir(seq == antigos[p["page_id"]]["P2"]["seq"], f"Âncora divergiu: {p['page_id']}")
        gt = obj["gt_w"]
        pw = [k for k in seq if k in set(gt)]
        row = {"page_id": p["page_id"], "tau": e.o.kendall_tau(pw, gt),
               "quebras": len(e.eventos(seq, gt)),
               "p1m_tau": e.o.kendall_tau([k for k in antigos[p["page_id"]]["P1m"]["seq"] if k in set(gt)], gt),
               "p1m_quebras": len(e.eventos(antigos[p["page_id"]]["P1m"]["seq"], gt))}
        rows.append(row)
    exigir(len(rows) == len(antigos) == 44, "Coorte v4 incompleta")
    ms = {k: statistics.mean(r[k] for r in rows) for k in ("tau", "quebras", "p1m_tau", "p1m_quebras")}
    R["ancoras"] = {"aprovadas": False, "n": len(rows), "medias": ms, "paginas": rows}
    salvar()
    exigir(abs(ms["tau"]-.985948) < 5e-7 and abs(ms["quebras"]-6.045455) < 5e-7,
           f"Âncora original obrigatória não bateu: {ms}")
    exigir(abs(ms["p1m_tau"]-.952424) <= .006 and abs(ms["p1m_quebras"]-8.931818) < .0051,
           f"Âncora extrator+XY-cut+margens não bateu: {ms}")
    R["ancoras"]["aprovadas"] = True
    salvar()
    print("Âncoras aprovadas:", ms, flush=True)


def diagnosticar():
    for nome in HUMANAS:
        path_classes = RAIZ / ("data/golden/golden_v4/tarefas.jsonl" if nome == 'golden_v4'
                               else "data/golden/_avaliacao/golden_v3/tarefas.jsonl")
        classes = {p['page_id']: {u['id']: u.get('classe') for u in p['bounding_boxes']}
                   for p in b.jsonl(path_classes)}
        rows = []
        for obj, p in b.paginas(nome, "linhas"):
            vigiar()
            cp = BASE / "diagnostico" / nome / (e.ac.chave(p["page_id"]) + ".json")
            fp = hash_obj([VERSAO_DIAG, R["assinatura_fontes"], obj, p])
            cached = ler(cp) if cp.exists() else {}
            if cached.get("fingerprint") == fp:
                row = cached
            else:
                ctx = c.contexto(p, obj["palavras"])
                med, cont, trs, _ = PREPARAR(obj, p, ctx)
                pap, sinais = evidencia(ctx)
                _, seq, q, exp = medir(obj, p, ctx["ordem"])
                gl = {L["id"]: L for L in q["gold_lines"]}
                dono = {k: uid for uid, ks in exp.items() for k in ks}
                linha = {k: lid for lid, L in gl.items() for k in L["ks"]}
                def papeis_linhas(lids):
                    ps = dict(pap)
                    for lid in lids:
                        if lid is None:
                            continue
                        L = gl[lid]
                        cls = classes[p['page_id']].get(L.get('regiao'))
                        for k in L['ks']:
                            uid = dono[k]
                            if pap[uid] != 'marca' and cls:
                                ps[uid] = {'cabecalho':'cabecalho', 'rodape':'rodape'}.get(cls, 'corpo')
                    return ps
                prox = {a: z for a, z in zip(seq, seq[1:])}
                detalhes = []
                for t in trs:
                    if t['tipo'] == 'margem':
                        ps = papeis_linhas([t['linha_a'], t['linha_z']])
                        t['subtipo'] = subtipo(ctx, t['a'], t['z'], ps)
                    if t["tipo"] != "margem" or t["acerto"]:
                        continue
                    ps = papeis_linhas([t['linha_a'], t['linha_z']])
                    st = subtipo(ctx, t["a"], t["z"], ps)
                    atual = prox.get(t["palavra_a"])
                    lid_atual = linha.get(atual)
                    tex = lambda lid: " ".join(obj["palavras"][k][0] for k in gl[lid]["ks"]) if lid else "[fora da referência / fim]"
                    detalhes.append({**t, "subtipo": st,
                        "texto_a": tex(t["linha_a"]), "texto_ouro": tex(t["linha_z"]),
                        "texto_regra": tex(lid_atual), "linha_regra": lid_atual,
                        "ordem_humana": [t["linha_a"], t["linha_z"]],
                        "ordem_regra": [t["linha_a"], lid_atual],
                        "papel_a": ps[t["a"]], "papel_z": ps[t["z"]],
                        "classe_regiao_a": classes[p['page_id']].get(gl[t['linha_a']].get('regiao')),
                        "classe_regiao_z": classes[p['page_id']].get(gl[t['linha_z']].get('regiao'))})
                emit = collections.Counter()
                for ev in e.eventos(seq, q["gt_w"]):
                    a, z = dono[ev["a"]], dono.get(ev["esperado"])
                    if c.categoria(ctx, a, z) == "margem":
                        ps = papeis_linhas([linha.get(ev['a']), linha.get(ev['esperado'])])
                        emit[subtipo(ctx, a, z, ps)] += 1
                row = {"page_id": p["page_id"], "uf": p["uf"],
                    "visto_treino": p["uf"] in R["splits"]["treino"], "metricas": med,
                    "tipos": cont, "contagem_subtipos": dict(collections.Counter(t["subtipo"] for t in detalhes)),
                    "quebras_subtipos": dict(emit), "detalhes": detalhes,
                    "sinais": sinais, "ordem_regra": ctx["ordem"],
                    "fingerprint": fp, "transicoes": trs}
                exigir(len(detalhes) == cont["margem"]["erros"], "Erros de margem não particionados")
                exigir(sum(emit.values()) == cont["margem"]["quebras_palavra"], "Quebras não particionadas")
                gravar(cp, row)
            rows.append({k: row[k] for k in ("page_id", "uf", "visto_treino", "metricas", "tipos", "contagem_subtipos", "quebras_subtipos")})
            R.setdefault("diagnostico", {})[nome] = rows
            salvar()
            print(f"Diagnóstico {nome}: {len(rows)}", flush=True)
            gc.collect()


def bandas_evidencia(cs, ws, dimensoes, h, gap_h):
    """Encontra separacao por branco nas bordas, sem ler classes/referencia.

    Nas bandas extremas, uma calha horizontal maior que gap_h*altura de
    palavra separa margem de corpo. Sem calha, continuidade com linhas do
    corpo impede que o limiar original retire texto corrido.
    """
    H = dimensoes['height']
    textuais = [i for i,u in enumerate(cs) if u['ks'] and c.tipo_unidade(u) == 'texto'
                and not all(e.o.RE_MARCACAO.match(ws[k][0]) for k in u['ks'])]
    intervalos = sorted((cs[i]['bbox'][1], cs[i]['bbox'][3]) for i in textuais)
    merged = []
    for a,z in intervalos:
        if merged and a <= merged[-1][1]+.15*h:
            merged[-1][1] = max(merged[-1][1], z)
        else:
            merged.append([a,z])
    candidatos = [(z[0]-a[1], (z[0]+a[1])/2) for a,z in zip(merged,merged[1:])]
    tops = [(g,y) for g,y in candidatos if .02*H < y < .10*H and g >= gap_h*h]
    bots = [(g,y) for g,y in candidatos if .90*H < y < .99*H and g >= gap_h*h]
    top = max(tops, default=(0,None))[1]
    bot = max(bots, default=(0,None))[1]
    return top, bot


def ordenar_transversais(cs, ids, h, vale, diag, largura, ponte):
    """Barreiras globais com suporte dos dois lados; reusa regra nas secoes."""
    cortes = e.o.vales_locais(cs, ids, h, vale) or e.o.vales(cs, ids, h, vale)
    largos = [i for i in ids if cs[i]['bbox'][2]-cs[i]['bbox'][0] >= .50*largura
              and any(cs[i]['bbox'][0] < x < cs[i]['bbox'][2]
                      and min(x-cs[i]['bbox'][0], cs[i]['bbox'][2]-x) >= ponte*largura for x in cortes)]
    if not largos:
        return e.o.ordenar_projecao(cs, ids, h, vale, diag, local=True)
    largos.sort(key=lambda i:(c.cy(cs[i]),cs[i]['bbox'][0],i))
    # Pontes na mesma altura compoem uma barreira horizontal, sem partir atomos.
    grupos = []
    for i in largos:
        if grupos and abs(c.cy(cs[i])-statistics.mean(c.cy(cs[j]) for j in grupos[-1])) < .5*h:
            grupos[-1].append(i)
        else:
            grupos.append([i])
    ys = [statistics.mean(c.cy(cs[i]) for i in g) for g in grupos]
    especiais = set(largos)
    secoes = [[] for _ in range(len(grupos)+1)]
    for i in ids:
        if i not in especiais:
            secoes[sum(y < c.cy(cs[i]) for y in ys)].append(i)
    out = []
    for j, sec in enumerate(secoes):
        out.extend(e.o.ordenar_projecao(cs, sec, h, vale, diag, local=True))
        if j < len(grupos):
            out.extend(sorted(grupos[j],key=lambda i:cs[i]['bbox'][0]))
    diag['barreiras_v2'] = len(grupos)
    return out


def prever(p, ws, parametros):
    """Preditor publico: so campos automaticos e parametros congelados.

    Devolve (ordem de IDs, diagnostico), no contrato da bancada. Nao recebe
    obj, anotacoes, classes de regiao, fluxo silver ou ranks de referencia.
    """
    auto = c.automatico(p)
    cs = auto['bounding_boxes']
    ent = ordem_entrada(auto)
    H = auto['dimensions']['height']
    h = statistics.median(w[4]-w[2] for w in ws)
    ini, corpo, marcas, fim = e.j.particao(cs, ws, H, 'geo')
    if parametros.get('original'):
        return b.prever(auto, ws, 'regra_colunas')
    topo, rodape = (None,None)
    if parametros['evidencia']:
        topo, rodape = bandas_evidencia(cs, ws, auto['dimensions'], h, parametros['gap_h'])
    gs = {g:[] for g in ('topo','corpo','marcas','rodape')}
    old = {i:g for ids,g in ((ini,'topo'),(corpo,'corpo'),(marcas,'marcas'),(fim,'rodape')) for i in ids}
    for i in ent:
        u = cs[i]
        g = old[i]
        cy = c.cy(u)
        if g == 'marcas' and parametros['marcas_geo']:
            g = ('topo' if cy < .07*H and u['bbox'][3] < .10*H else 'rodape' if cy > .95*H else 'corpo')
        if parametros['evidencia'] and g != 'marcas':
            if topo is not None and cy < .12*H:
                g = 'topo' if u['bbox'][3] <= topo else 'corpo'
            elif g == 'topo':
                t = texto_normal(u['text'])
                viz = any(j != i and old[j] == 'corpo' and c.sobreposicao(u,cs[j]) >= .55
                          and 0 < c.cy(cs[j])-cy < 2*h for j in ent)
                if viz and not (cy < .035*H or RE_CAB.search(t) and not (len(u['ks'])>10 and t[:1].islower())):
                    g = 'corpo'
            if rodape is not None and cy > .88*H:
                g = 'rodape' if u['bbox'][1] >= rodape else 'corpo'
            elif g == 'rodape':
                viz = any(j != i and old[j] == 'corpo' and c.sobreposicao(u,cs[j]) >= .55
                          and 0 < cy-c.cy(cs[j]) < 2*h for j in ent)
                if viz:
                    g = 'corpo'
        gs[g].append(i)
    diag = {'max_colunas':1,'pontes':0,'barreiras_v2':0,'topo':len(gs['topo']),
            'rodape':len(gs['rodape']),'marcas':len(gs['marcas']),
            'corte_topo':topo,'corte_rodape':rodape}
    chave = lambda i:(cs[i]['bbox'][1],cs[i]['bbox'][0],ent.index(i))
    def margem(ids):
        if parametros['ordem_margens'] == 'colunas':
            return e.o.xycut(ids,e.o.boxes(cs))
        if parametros['ordem_margens'] == 'faixas':
            restantes = sorted(ids,key=chave)
            grupos = []
            for i in restantes:
                if grupos and abs(c.cy(cs[i])-statistics.mean(c.cy(cs[j]) for j in grupos[-1])) <= 1.5*h:
                    grupos[-1].append(i)
                else:
                    grupos.append([i])
            return [i for g in grupos for i in sorted(g,key=lambda j:(cs[j]['bbox'][0],ent.index(j)))]
        return sorted(ids,key=chave)
    if parametros['ponte']:
        W = max(u['bbox'][2] for u in cs)-min(u['bbox'][0] for u in cs)
        oc = ordenar_transversais(cs,gs['corpo'],h,e.FIXA.vale,diag,W,parametros['ponte'])
    else:
        oc = e.o.ordenar_projecao(cs,gs['corpo'],h,e.FIXA.vale,diag,local=True)
    indices = margem(gs['topo'])+oc+margem(gs['marcas'])+margem(gs['rodape'])
    exigir(sorted(indices) == list(range(len(cs))), 'Variante perdeu/repetiu unidade')
    return [cs[i]['id'] for i in indices], diag


def paginas_silver(nome):
    if nome == 'teste_silver':
        yield from b.paginas(nome,'linhas')
    else:
        for uf in R['splits']['validacao']:
            for p,obj in __import__('itertools').zip_longest(
                    b.jsonl(b.UNIDADES/'linhas'/(uf+'.jsonl')),
                    b.jsonl(b.UNIDADES/'linhas'/(uf+'.palavras.jsonl'))):
                exigir(p is not None and obj is not None and p['page_id']==obj['page_id'], 'Shards RN divergentes')
                exigir(p['uf']==uf and p['particao']=='validacao', 'Veiculo incorreto na validacao')
                exigir(obj['gt_w']==list(range(len(obj['palavras']))) and obj['referencia_palavras_tipo']=='fluxo_pdf_por_palavra', 'Silver nao e fluxo PDF')
                if p['page_id'] not in R['humanos']:
                    yield {**obj,'uf':uf},p


def grade():
    out = [{'nome':'original','original':True}]
    for ev,mode,mk in __import__('itertools').product((False,True),('colunas','faixas'),(False,True)):
        out.append({'nome':f"ev{int(ev)}_{mode}_marca{int(mk)}",'evidencia':ev,
                    'gap_h':1.0,'ordem_margens':mode,'marcas_geo':mk,'ponte':0})
    # Ablacoes transparentes de barreira e da exigencia de branco nas bordas.
    for gap, ponte in ((.7,0),(1.5,0),(1.,.06),(1.,.10)):
        out.append({'nome':f"ev1_colunas_marca1_gap{gap}_ponte{ponte}", 'evidencia':True,
                    'gap_h':gap,'ordem_margens':'colunas','marcas_geo':True,'ponte':ponte})
    return out


def ajustar():
    assinatura = hash_obj([VERSAO_REGRA, grade(), R['assinatura_fontes']])
    if R.get('escolha',{}).get('assinatura') == assinatura:
        print('Parâmetros já congelados:',R['escolha']['parametros'],flush=True)
        return
    exigir(not R.get('avaliacao'), 'Não reajustar depois de ver as bancadas finais')
    rows = []
    for nome in ('golden_v4','validacao_silver'):
        paginas = b.paginas(nome,'linhas') if nome=='golden_v4' else paginas_silver(nome)
        for obj,p in paginas:
            vigiar()
            cp = BASE/'ajuste'/(e.ac.chave(p['page_id'])+'.json')
            fp = hash_obj([assinatura,obj,p])
            row = ler(cp) if cp.exists() else {}
            if row.get('fingerprint') != fp:
                exp = b.expansoes(obj,p)
                gt,gset = obj['gt_w'],set(obj['gt_w'])
                meds = {}
                for par in grade():
                    ordem,_ = prever(c.automatico(p),obj['palavras'],par)
                    seq = [k for uid in ordem for k in exp[uid]]
                    meds[par['nome']] = {'tau':e.o.kendall_tau([k for k in seq if k in gset],gt),
                                         'quebras':len(e.eventos(seq,gt))}
                row = {'page_id':p['page_id'],'bancada':nome,'metricas':meds,'fingerprint':fp}
                gravar(cp,row)
            rows.append(row)
            print(f"Ajuste {nome}: {sum(r['bancada']==nome for r in rows)}",flush=True)
    tabela = {}
    for par in grade():
        tabela[par['nome']] = {nome:{k:statistics.mean(r['metricas'][par['nome']][k] for r in rows if r['bancada']==nome)
                                     for k in ('tau','quebras')} for nome in ('golden_v4','validacao_silver')}
    base = tabela['original']
    elegiveis = [p for p in grade() if all(tabela[p['nome']][n]['tau'] >= base[n]['tau']-.002
                                          for n in base)]
    # Mesma importancia para media v4 e RN; tau e estabilidade como desempate.
    vencedor = min(elegiveis,key=lambda p:(sum(tabela[p['nome']][n]['quebras'] for n in base),
                         -sum(tabela[p['nome']][n]['tau'] for n in base),p['nome']))
    R['escolha'] = {'assinatura':assinatura,'parametros':vencedor,'candidatos':tabela,
                   'ids_ajuste':[r['page_id'] for r in rows],
                   'criterio':'minimizar soma das médias de quebras v4+RN; perda de tau <=0,002 em cada coorte; maior tau e nome como desempate',
                   'congelada_em':time.strftime('%Y-%m-%d %H:%M:%S')}
    salvar()
    print('Escolha congelada:',vencedor,flush=True)


def avaliar():
    params = R['escolha']['parametros']
    for nome in HUMANAS+('validacao_silver','teste_silver'):
        rows = []
        paginas = b.paginas(nome,'linhas') if nome in HUMANAS else paginas_silver(nome)
        for obj,p in paginas:
            vigiar()
            cp = BASE/'avaliacao'/nome/(e.ac.chave(p['page_id'])+'.json')
            fp = hash_obj([VERSAO_REGRA,params,R['assinatura_fontes'],obj,p])
            row = ler(cp) if cp.exists() else {}
            if row.get('fingerprint') != fp:
                ctx = c.contexto(p,obj['palavras'])
                ordem,diag = prever(c.automatico(p),obj['palavras'],params)
                m0,_,q,_ = medir(obj,p,ctx['ordem'])
                mv,seq,_,exp = medir(obj,p,ordem)
                tipos, subtipos = {}, {}
                if nome in HUMANAS:
                    d = ler(BASE/'diagnostico'/nome/(e.ac.chave(p['page_id'])+'.json'))
                    rank = {k:i for i,k in enumerate(seq)}
                    ls = {L['id']:L['ks'] for L in q['gold_lines']}
                    intacta = {lid:all(rank[z]==rank[a]+1 for a,z in zip(ks,ks[1:])) for lid,ks in ls.items()}
                    # Classifica tambem novas perdas, usando a tipologia original congelada.
                    for t in d['transicoes']:
                        ac = bool(intacta[t['linha_a']] and intacta[t['linha_z']] and rank[t['palavra_z']]==rank[t['palavra_a']]+1)
                        tt = tipos.setdefault(t['tipo'],{'original':0,'variante':0,'corrigidas':0,'novas':0})
                        tt['original'] += not t['acerto']; tt['variante'] += not ac
                        tt['corrigidas'] += not t['acerto'] and ac; tt['novas'] += t['acerto'] and not ac
                        if t['tipo']=='margem':
                            st = t['subtipo']
                            ss = subtipos.setdefault(st,{'original':0,'variante':0,'corrigidas':0,'novas':0})
                            ss['original'] += not t['acerto']; ss['variante'] += not ac
                            ss['corrigidas'] += not t['acerto'] and ac; ss['novas'] += t['acerto'] and not ac
                row = {'page_id':p['page_id'],'uf':p['uf'],'visto_treino':p['uf'] in R['splits']['treino'],
                       'sobrepoe_humanas':p['page_id'] in R['humanos'],'ordem':ordem,
                       'original':m0,'variante':mv,'tipos':tipos,'subtipos':subtipos,'diag':diag,'fingerprint':fp}
                gravar(cp,row)
            rows.append(row)
            R.setdefault('avaliacao',{})[nome] = {'completa':False,'paginas':rows}
            if len(rows)%5==0:
                salvar()
                print(f"Avaliação {nome}: {len(rows)}",flush=True)
        R['avaliacao'][nome]['completa'] = True
        salvar()
        if nome in HUMANAS+('teste_silver',):
            path = PRED/f'regra_margens_v2__linhas__{nome}.jsonl'
            content = ''.join(json.dumps({'page_id':r['page_id'],'ordem':r['ordem']},ensure_ascii=False)+'\n' for r in rows)
            if path.exists():
                exigir(path.read_text(encoding='utf-8')==content,'Predição existente difere; não sobrescrever arquivo anterior')
            else:
                gravar(path,content)
            # Audita o contrato com a propria bancada, sem escrever estado dela.
            exigir(set(b.indice_pred(path))=={r['page_id'] for r in rows},'Contrato/IDs de predição divergentes')
            R['avaliacao'][nome]['pred_sha256'] = b.sha(path)
            salvar()


def estatisticas(rows):
    W = b.PESOS_CLUSTER(rows)
    out = {'n':len(rows),'veiculos':len({r['uf'] for r in rows}),'metricas':{}}
    for k in ('tau','quebras','fid12','sucessor_linhas'):
        ds = [r['variante'][k]-r['original'][k] if r['variante'][k] is not None and r['original'][k] is not None else None for r in rows]
        ufs = sorted({r['uf'] for r in rows})
        dvs = {uf:statistics.mean(d for r,d in zip(rows,ds) if r['uf']==uf and d is not None) for uf in ufs}
        out['metricas'][k] = {m:e.media_ic([r[m][k] for r in rows],W) for m in ('original','variante')}
        out['metricas'][k].update(delta=e.media_ic(ds,W),wilcoxon=e.pratt(list(dvs.values())),por_veiculo=dvs)
    ds = [r['variante']['quebras']-r['original']['quebras'] for r in rows]
    out['melhor_igual_pior'] = [sum(d<0 for d in ds),sum(d==0 for d in ds),sum(d>0 for d in ds)]
    return out


def resumir():
    sums = {}
    for nome,val in R.get('avaliacao',{}).items():
        if not val['completa']:
            continue
        rows = val['paginas']
        grupos = {'todos':rows}
        if nome in HUMANAS:
            grupos.update(vistos=[r for r in rows if r['visto_treino']],nao_vistos=[r for r in rows if not r['visto_treino']])
        if nome=='teste_silver':
            grupos['sem_humanas'] = [r for r in rows if not r['sobrepoe_humanas']]
        sums[nome] = {g:estatisticas(rs) for g,rs in grupos.items() if rs}
    R['resumos'] = sums
    gravar(BASE/'estatisticas.json',sums)
    salvar()


def descobrir_imagens():
    out = {}
    for pasta in ('golden_v4','_avaliacao/golden_v3','golden_v1','golden_v2'):
        path = RAIZ/'data/golden'/pasta/'tarefas.jsonl'
        for p in b.jsonl(path):
            if p['page_id'] in out:
                continue
            nome = p.get('imagem')
            if not nome:
                continue
            candidates = [path.parent/'img'/nome,path.parent/nome]
            origem = p.get('origem','')
            for lote in ('golden_v1','golden_v2'):
                if lote in origem:
                    # Nao supor que a numeracao _avaliacao e igual a do lote.
                    tarefas = RAIZ/'data/golden'/lote/'tarefas.jsonl'
                    for original in b.jsonl(tarefas):
                        if original['page_id']==p['page_id']:
                            candidates.insert(0,tarefas.parent/'img'/original['imagem'])
            candidato = next((x for x in candidates if x.exists()),None)
            if candidato:
                out[p['page_id']] = candidato
    return out


def paineis():
    """Desenha oito paginas por bancada; somente uma imagem de cada vez."""
    from PIL import Image,ImageDraw,ImageFont
    imagens = descobrir_imagens()
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',11)
    manifests = []
    for nome in HUMANAS:
        rows = sorted(R['diagnostico'][nome],key=lambda r:(-r['tipos']['margem']['erros'],-r['tipos']['margem']['quebras_palavra'],r['page_id']))[:8]
        ids = {r['page_id']:r for r in rows}
        for obj,p in b.paginas(nome,'linhas'):
            if p['page_id'] not in ids:
                continue
            vigiar()
            pid = p['page_id']
            exigir(pid in imagens,f'Imagem Golden nao encontrada: {pid}')
            cp = PAINEIS/nome/(e.ac.chave(pid)+'.png')
            with Image.open(imagens[pid]) as im:
                original = im.convert('RGB')
                original.thumbnail((1250,1800))
            sw,sh = original.size
            canvas = Image.new('RGB',(sw*2+40,sh+115),'white')
            draw = ImageDraw.Draw(canvas)
            draw.text((15,8),pid,font=font,fill='black')
            draw.text((15,30),f"{nome} | perdas de margem: {ids[pid]['tipos']['margem']['erros']} | azul: linhas; vermelho: linhas envolvidas nos erros de margem",font=small,fill='black')
            diag = ler(BASE/'diagnostico'/nome/(e.ac.chave(pid)+'.json'))
            erros = {t[k] for t in diag['detalhes'] for k in ('linha_a','linha_z')}
            q = b.referencia(obj,p)
            exp = b.expansoes(obj,p)
            seq = [k for uid in diag['ordem_regra'] for k in exp[uid]]
            ranks = {k:i for i,k in enumerate(seq)}
            ls = {L['id']:L for L in q['gold_lines']}
            regra = sorted(q['gt_l'],key=lambda lid:min(ranks[k] for k in ls[lid]['ks']))
            for painel,ordem,titulo in ((0,regra,'Regra original: postos das linhas na saida'),(1,q['gt_l'],'Referencia humana: postos das linhas')):
                xoff = 10+painel*(sw+20)
                canvas.paste(original,(xoff,75))
                draw.text((xoff,53),titulo,font=font,fill='black')
                for pos,lid in enumerate(ordem,1):
                    L=ls[lid]
                    bb=L.get('bbox') or e.o.envelope([obj['palavras'][k][1:5] for k in L['ks']])
                    x0,y0,x1,y1=bb
                    sx,sy=sw/p['dimensions']['width'],sh/p['dimensions']['height']
                    x,y=xoff+x0*sx,75+y0*sy
                    color='#b91c1c' if lid in erros else '#1465ae'
                    draw.rectangle((x,y,xoff+x1*sx,75+y1*sy),outline=color,width=1)
                    label=str(pos)
                    rect=draw.textbbox((x,y),label,font=small)
                    draw.rectangle(rect,fill='white')
                    draw.text((x,y),label,font=small,fill=color)
            cp.parent.mkdir(parents=True,exist_ok=True)
            canvas.save(cp)
            manifests.append({'bancada':nome,'page_id':pid,'imagem_origem':b.rel(imagens[pid]),
                              'painel':b.rel(cp),'perdas_margem':ids[pid]['tipos']['margem']['erros'],
                              'dimensoes':[canvas.width,canvas.height]})
            original.close(); canvas.close()
    gravar(PAINEIS/'manifesto.json',manifests)
    R['paineis'] = manifests
    salvar()


def conferir():
    """Confere consistencia de cache, contrato e ausencia de vazamento no ajuste."""
    exigir(R['ancoras']['aprovadas'],'Sem ancora')
    exigir(len(R['diagnostico']['golden_v4'])==44 and len(R['diagnostico']['golden_v3_novo'])==27,'Diagnostico incompleto')
    if R.get('resumos'):
        ajuste=set(R['escolha']['ids_ajuste'])
        v3={r['page_id'] for r in R['avaliacao']['golden_v3_novo']['paginas']}
        testelimpo={r['page_id'] for r in R['avaliacao']['teste_silver']['paginas'] if not r['sobrepoe_humanas']}
        exigir(not ajuste&v3 and not ajuste&testelimpo,'Vazamento de pagina no ajuste/teste limpo')
        for nome,val in R['avaliacao'].items():
            exigir(val['completa'],'Avaliacao parcial')
            for r in val['paginas']:
                cp=BASE/'avaliacao'/nome/(e.ac.chave(r['page_id'])+'.json')
                exigir(ler(cp)==r,'Estado diverge do cache de pagina')
                for m in ('original','variante'):
                    exigir(r[m]['piso_interno']<=r[m]['quebras'],'Piso incoerente')
            rows = val['paginas']
            for grupo,s in R['resumos'][nome].items():
                rs=[r for r in rows if grupo=='todos' or grupo=='vistos' and r['visto_treino']
                    or grupo=='nao_vistos' and not r['visto_treino']
                    or grupo=='sem_humanas' and not r['sobrepoe_humanas']]
                exigir(estatisticas(rs)==s,'Estatisticas nao reproduzem resultados por pagina')
            por_id={r['page_id']:r for r in rows}
            exigir(len(por_id)==len(rows),'Pagina de cache repetida')
            paginas=b.paginas(nome,'linhas') if nome in HUMANAS else paginas_silver(nome)
            primeiro=True
            ids_lidos=set()
            for obj,p in paginas:
                vigiar(False)
                ids_lidos.add(p['page_id'])
                row=por_id[p['page_id']]
                if nome in ('golden_v4','validacao_silver'):
                    ajuste_cp=ler(BASE/'ajuste'/(e.ac.chave(p['page_id'])+'.json'))
                    exigir(ajuste_cp['fingerprint']==hash_obj([R['escolha']['assinatura'],obj,p]),
                           'Dados do ajuste mudaram depois da escolha')
                ordem,_=prever(c.automatico(p),obj['palavras'],R['escolha']['parametros'])
                exigir(ordem==row['ordem'],'Preditor reexecutado diverge do cache')
                exp=b.expansoes(obj,p)
                original,_=b.prever(c.automatico(p),obj['palavras'],'regra_colunas')
                q=b.referencia(obj,p)
                gset=set(q['gt_w'])
                for m,ordem_m in (('original',original),('variante',ordem)):
                    seq=[k for uid in ordem_m for k in exp[uid]]
                    exigir(len(e.eventos(seq,q['gt_w']))==row[m]['quebras'],'Quebras novas nao reproduzem cache')
                    exigir(e.o.kendall_tau([k for k in seq if k in gset],q['gt_w'])==row[m]['tau'],'Tau nao reproduz cache')
                    if primeiro:
                        # Uma regua completa independente por bancada/metodo,
                        # incluindo fidelidade lexical, sem consultar nosso cache.
                        med=e.medir(q,seq,[],{},'P0')
                        exigir(all(med[k]==row[m][k] for k in METRICAS if k!='piso_interno'),'Regua completa diverge')
                primeiro=False
            exigir(set(por_id)==ids_lidos,'Cobertura do cache diverge da bancada')
        for nome in HUMANAS+('teste_silver',):
            p=PRED/f'regra_margens_v2__linhas__{nome}.jsonl'
            exigir(b.sha(p)==R['avaliacao'][nome]['pred_sha256'],'Predicao modificada')
        exigir(len(R.get('paineis',[]))==16,'Faltam paineis de oito paginas por bancada')
        R['conferencia']={'paginas_reexecutadas':sum(len(x['paginas']) for x in R['avaliacao'].values()),
                         'bancadas_regua_completa':list(R['avaliacao']),
                         'fontes_preservadas':fonte_assinatura()==R['fontes']}
        exigir(R['conferencia']['fontes_preservadas'],'Fonte anterior alterada durante a execucao')
    esperado = relatorio()
    exigir(MD.read_text(encoding='utf-8')==esperado,'Markdown nao reproduz estado')
    print('Conferência aprovada: caches, relatório, âncoras e contrato.',flush=True)


def f(v, n=3):
    return "—" if v is None else f"{v:.{n}f}".replace(".", ",")


def cel(m, percentual=False, casas=3):
    mul = 100 if percentual else 1
    a,z = m['ic']
    return f"{f(m['media']*mul,casas)} [{f(a*mul,casas)}; {f(z*mul,casas)}]"


def relatorio():
    diag = R.get("diagnostico", {})
    n = sum(len(x) for x in diag.values())
    out = ["# Margens e elementos transversais sobre linhas", "",
           f"Diagnóstico disponível: {n} páginas humanas; a atribuição de subtipos é automática e exploratória.  ",
           "Variante: em preparação; nenhuma conclusão antecipada sobre eficácia.  ",
           "Ganho fora da amostra de ajuste: ainda não medido.  ",
           "Não resolvido: ordem interna de átomos, linhas fragmentadas e causas sem evidência de margem.  ",
           "Estado: execução parcial e retomável; âncoras precedem as medidas novas.", "",
           "Este relatório é escrito pelo script, a partir dos resultados por página. Não usa GPU, treino, rede ou Label Studio.", "",
           "## Âncoras", ""]
    if R.get('resumos'):
        v4 = diag['golden_v4']
        cnt = collections.Counter()
        for row in v4:
            cnt.update(row['contagem_subtipos'])
        ganho = []
        for nome,grupo in (('golden_v3_novo','todos'),('teste_silver','sem_humanas')):
            s=R['resumos'][nome][grupo]
            ganho.append(f"{nome} ({s['n']} páginas): Δ quebras {cel(s['metricas']['quebras']['delta'])}, Δ τ {cel(s['metricas']['tau']['delta'],casas=6)}")
        out[2:7] = [
            'Margens no v4: '+ '; '.join(f"{ROT[st]} = {cnt[st]} sucessores perdidos" for st in ('c','d','e')) + '.  ',
            'Variante congelada: '+R['escolha']['parametros']['nome']+'; margens por branco/continuidade, leitura por colunas e marcas pela posição, conforme ablações abaixo.  ',
            'Fora do ajuste: '+'; '.join(ganho)+'.  ',
            'Não resolveu todas as margens/átomos: no v3, a fidelidade de 12 caiu '+f(abs(R['resumos']['golden_v3_novo']['todos']['metricas']['fid12']['delta']['media'])*100)+' ponto percentual, e marcas tiveram '+str(sum(r['subtipos'].get('d',{}).get('variante',0)-r['subtipos'].get('d',{}).get('original',0) for r in R['avaliacao']['golden_v3_novo']['paginas']))+' perdas líquidas a mais.  ',
            'Veredito: '+veredito()+'.']
    anc = R.get("ancoras", {})
    if anc:
        ms = anc["medias"]
        out += [f"Status: {'aprovadas' if anc['aprovadas'] else 'NÃO aprovadas'}; {anc['n']} páginas reexecutadas.", "",
                "| Controle | τ palavras | Quebras/página |", "|---|---:|---:|",
                f"| Regra original | {f(ms['tau'],6)} | {f(ms['quebras'],6)} |",
                f"| Extrator + XY-cut + margens | {f(ms['p1m_tau'],6)} | {f(ms['p1m_quebras'],6)} |", "",
                "A ordem da regra é reexecutada com as unidades/átomos congelados e conferida palavra por palavra contra P2 histórico. Para o controle do extrator, reavaliam-se as sequências históricas P1m na referência atual; não se reextraem PDFs nem se reinfere o detector.", ""]
    out += ["## Diagnóstico fino", "",
        "Reutiliza `contexto`, `categoria` e `preparar_avaliacao` de `corretor_de_transicoes.py`. Cada sucessor-ouro de margem perdido recebe um subtipo exclusivo: corpo erroneamente separado, marca, par de cabeçalhos, cabeçalho após corpo, rodapé antes do corpo, outro. **Somente no diagnóstico v4**, usa a classe da região nas tarefas congeladas (cabecalho/rodape/texto etc.); as classes ficam fora do preditor. No v3, que não possui esse campo, usa proxies conservadores de texto/geometria. A classificação de subtipos das duas coortes não tem a mesma qualidade de supervisão. Um mesmo deslocamento pode perder mais de um sucessor. Quebras emitidas e sucessores perdidos têm denominadores distintos.", "",
        "Cabeçalho combina faixa superior e vocabulário editorial; marca combina regex original, número isolado em borda ou forma lateral; rodapé combina faixa inferior e vocabulário de assinatura/publicação. Continuidade espacial/textual dá evidência de corpo. Os shards não guardam fonte/tamanho: não se inventa informação tipográfica.", ""]
    for nome, rows in diag.items():
        out += [f"### {nome}", "",f"Veículos do treino original: {sum(r['visto_treino'] for r in rows)} páginas vistas; {sum(not r['visto_treino'] for r in rows)} não vistas. Estratos vazios não recebem médias.",""]
        for grupo in ("todos", "vistos", "nao_vistos"):
            rs = [r for r in rows if grupo == "todos" or r["visto_treino"] == (grupo == "vistos")]
            if not rs:
                continue
            total = sum(r["tipos"]["margem"]["erros"] for r in rs)
            qb = sum(r["tipos"]["margem"]["quebras_palavra"] for r in rs)
            out += [f"**{grupo}: {len(rs)} páginas; {len(set(r['uf'] for r in rs))} veículos.**", "",
                    "| Subtipo | Sucessores perdidos | % das perdas de margem | Quebras emitidas |", "|---|---:|---:|---:|"]
            for st, rot in ROT.items():
                cnt = sum(r["contagem_subtipos"].get(st, 0) for r in rs)
                eq = sum(r["quebras_subtipos"].get(st, 0) for r in rs)
                out.append(f"| ({st}) {rot} | {cnt} | {f(100*cnt/total if total else 0,1)}% | {eq} |")
            out += [f"| Total | {total} | {f(100 if total else 0,1)}% | {qb} |", ""]
    if n:
        out += ["### Exemplos reais", "", "São mostrados até três exemplos por subtipo, priorizando páginas distintas. Texto completo de todas as ocorrências e IDs de linha ficam nos caches; falta de exemplos não é preenchida artificialmente.", ""]
        exemplos = collections.defaultdict(list)
        for nome, rows in diag.items():
            for row in rows:
                full = ler(BASE / "diagnostico" / nome / (e.ac.chave(row["page_id"])+".json"))
                for t in full["detalhes"]:
                    exemplos[t["subtipo"]].append((nome, row["page_id"], t))
        for st, rot in ROT.items():
            out += [f"**({st}) {rot}**", ""]
            xs = exemplos[st]
            escolhidos, usados = [], set()
            for x in xs:
                if x[1] not in usados:
                    escolhidos.append(x)
                    usados.add(x[1])
                if len(escolhidos) == 3:
                    break
            for x in xs:
                if len(escolhidos) == 3:
                    break
                if x not in escolhidos:
                    escolhidos.append(x)
            if not escolhidos:
                out += ["Nenhuma ocorrência atribuída a este subtipo nesta execução.", ""]
            elif len(escolhidos)<3:
                out += [f"Há somente {len(xs)} ocorrência(s) atribuída(s); não existem três exemplos para mostrar sem mudar a classificação ou inventar casos.", ""]
            for nome, pid, t in escolhidos:
                out += [f"- `{pid}` ({nome}; {t['linha_a']} → {t['linha_z']}; {'interna à unidade' if t['interno'] else 'entre unidades'}).",
                        f"  - Humana: «{t['texto_a']}» → «{t['texto_ouro']}».",
                        f"  - Regra: «{t['texto_a']}» → «{t['texto_regra']}»."]
            out.append("")
    if R.get('escolha'):
        out += ['## Variante e ajuste congelado','',
            'O preditor `prever(p, ws, parametros)` remove todos os campos humanos/silver antes de ordenar. A grade testa ordenação das margens por XY-cut (colunas) ou bandas de altura próxima; deslocamento das marcas de diagramação conforme sua posição; separação de margens pela maior faixa de branco nas bordas e continuidade com o corpo; e barreiras transversais que dividem corpo acima/abaixo. A regra original já trata pontes: a ablação transversal testa uma exigência alternativa de largura/suporte. Unidades e suas palavras internas permanecem congeladas. Nenhum exemplo do v3 ou de CE/MA/RJ seleciona parâmetros.','',
            'Parâmetros escolhidos: `'+json.dumps(R['escolha']['parametros'],ensure_ascii=False,sort_keys=True)+'`.','',
            'Critério definido antes da avaliação final: '+R['escolha']['criterio']+'. Os candidatos e os limiares foram desenhados a partir do diagnóstico v4. A consulta ao diagnóstico v3 exigida nesta tarefa não permite tratá-lo como validação cega da ideia; seus resultados não foram usados no ajuste numérico.','',
            '| Candidato | v4: τ / quebras | RN: τ / quebras |','|---|---:|---:|']
        for nome,t in R['escolha']['candidatos'].items():
            a,z=t['golden_v4'],t['validacao_silver']
            out.append(f"| {nome} | {f(a['tau'],6)} / {f(a['quebras'])} | {f(z['tau'],6)} / {f(z['quebras'])} |")
        out += ['','RN exclui páginas presentes nas tarefas humanas, inclusive a tarefa v4 ainda sem conclusão. Seus IDs de ajuste estão no estado; sete veículos de treino são lidos somente do split para estratificar. Esta regra não aprende em páginas silver de treino e não usa repetição de páginas, fonte ou tamanho de fonte.','']
    if R.get('resumos'):
        out += ['## Avaliação pareada','',
            'Médias por página, IC 95% por bootstrap de **veículos** (funções da bancada, 5.000 réplicas). Δ = variante − original. Wilcoxon bilateral Pratt aplicado a uma média de diferença por veículo; não se contam páginas de um veículo como observações independentes. RN tem apenas um veículo (IC degenerado) e CE/MA/RJ apenas três: inferência limitada. Percentuais de fidelidade e sucessor estão em pontos percentuais nos contrastes. Sem correção para múltiplas comparações.','',
            '| Bancada / estrato | n / veículos | τ original → v2 | Quebras original → v2 | Fidelidade 12 original → v2 | Sucessor linhas original → v2 | Melhor / igual / pior em quebras |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for nome,grupos in R['resumos'].items():
            for g,s in grupos.items():
                ms=s['metricas']
                pairs=[]
                for k in ('tau','quebras','fid12','sucessor_linhas'):
                    mul=100 if k in ('fid12','sucessor_linhas') else 1
                    casas=6 if k=='tau' else 3
                    pairs.append(f"{f(ms[k]['original']['media']*mul,casas)} → {f(ms[k]['variante']['media']*mul,casas)}")
                out.append(f"| {nome} / {g} | {s['n']} / {s['veiculos']} | "+' | '.join(pairs)+" | "+' / '.join(map(str,s['melhor_igual_pior']))+' |')
        out += ['','| Bancada / estrato | Métrica | Original [IC] | v2 [IC] | Δ [IC por veículo] | p Wilcoxon por veículo |',
                '|---|---|---:|---:|---:|---:|']
        for nome,grupos in R['resumos'].items():
            for g,s in grupos.items():
                for k,m in s['metricas'].items():
                    pct=k in ('fid12','sucessor_linhas')
                    casas=6 if k=='tau' else 3
                    out.append(f"| {nome} / {g} | {k} | {cel(m['original'],pct,casas)} | {cel(m['variante'],pct,casas)} | {cel(m['delta'],pct,casas)} | {f(m['wilcoxon']['p'],6)} |")
        full=R['avaliacao']['teste_silver']['paginas']
        out += ['',f"Teste silver integral: {len(full)} páginas, das quais {sum(r['sobrepoe_humanas'] for r in full)} também estão nas tarefas humanas. A tabela integral preserva o contrato da bancada histórica; **o estrato sem_humanas ({sum(not r['sobrepoe_humanas'] for r in full)} páginas) é a comparação de teste sem sobreposição com o ajuste humano**. A retirada é apenas uma análise adicional, não alteração do split nem das predições integrais. O v3 tem páginas disjuntas do v4. A referência silver pode discordar das tabelas expandidas geometricamente; seu piso absoluto de quebras é alto.",'',
                '**Conclusão observada:** '+veredito()+'.','',
                '### Diferenças médias por veículo fora do ajuste','',
                '| Bancada / estrato | Veículo | Δ τ | Δ quebras | Δ fidelidade 12 (pp) | Δ sucessor linhas (pp) |',
                '|---|---|---:|---:|---:|---:|']
        for nome,g in (('golden_v3_novo','todos'),('teste_silver','sem_humanas')):
            s=R['resumos'][nome][g]['metricas']
            for uf in sorted(s['quebras']['por_veiculo']):
                out.append(f"| {nome} / {g} | {uf} | {f(s['tau']['por_veiculo'][uf],6)} | {f(s['quebras']['por_veiculo'][uf])} | {f(100*s['fid12']['por_veiculo'][uf])} | {f(100*s['sucessor_linhas']['por_veiculo'][uf])} |")
        out += ['',
                '### Sucessores perdidos por tipo de transição','',
                'A categoria é a da regra original congelada, para não mudar o denominador depois de alterar margens. Corrigidas e novas são fronteiras-ouro completas (ambas as linhas intactas e adjacentes), não apenas acerto de pares de IDs.','',
                '| Bancada | Tipo | Original | v2 | Corrigidas | Novas perdas |','|---|---|---:|---:|---:|---:|']
        for nome in HUMANAS:
            rows=R['avaliacao'][nome]['paginas']
            for tipo,rot in c.ROTULOS.items():
                vals={k:sum(r['tipos'].get(tipo,{}).get(k,0) for r in rows) for k in ('original','variante','corrigidas','novas')}
                out.append(f"| {nome} | {rot} | "+' | '.join(str(vals[k]) for k in vals)+' |')
        out += ['','### Ganhos e perdas nos subtipos de margem','',
                '| Bancada | Subtipo | Original | v2 | Corrigidas | Novas perdas | Δ perdas |','|---|---|---:|---:|---:|---:|---:|']
        for nome in HUMANAS:
            rows=R['avaliacao'][nome]['paginas']
            for st,rot in ROT.items():
                vals={k:sum(r['subtipos'].get(st,{}).get(k,0) for r in rows) for k in ('original','variante','corrigidas','novas')}
                out.append(f"| {nome} | ({st}) {rot} | "+' | '.join(str(vals[k]) for k in vals)+f" | {vals['variante']-vals['original']} |")
        for nome in HUMANAS:
            pioram=[]
            rows=R['avaliacao'][nome]['paginas']
            for st in ROT:
                d=sum(r['subtipos'].get(st,{}).get('variante',0)-r['subtipos'].get(st,{}).get('original',0) for r in rows)
                if d>0:
                    pioram.append(f"({st}) {ROT[st]}: +{d}")
            out += ['',f"{nome}: "+('subtipos que pioraram: '+'; '.join(pioram) if pioram else 'nenhum subtipo apresentou aumento líquido de perdas; novas perdas locais podem coexistir com correções')+'.']
        out.append('')
    if R.get('avaliacao') and not R.get('resumos'):
        out += ['## Resultados intermediários','',
                '| Bancada | Páginas medidas | Estado | τ original → v2 | Quebras original → v2 |',
                '|---|---:|---|---:|---:|']
        for nome,v in R['avaliacao'].items():
            rows=v['paginas']
            if rows:
                ms={k:{m:statistics.mean(r[m][k] for r in rows) for m in ('original','variante')} for k in ('tau','quebras')}
                out.append(f"| {nome} | {len(rows)} | {'completo' if v['completa'] else 'parcial'} | {f(ms['tau']['original'],6)} → {f(ms['tau']['variante'],6)} | {f(ms['quebras']['original'])} → {f(ms['quebras']['variante'])} |")
        out += ['','Resultados parciais não recebem intervalos nem conclusão final; repetir o comando retoma páginas já persistidas.','']
    if R.get('paineis'):
        out += ['## Painéis das piores páginas','',
            'Oito páginas de cada coorte humana, escolhidas pelo número de sucessores de margem perdidos; desempate por quebras de margem e page_id. Esquerda: posto de cada linha humana na sequência da regra; direita: posto na referência humana. Linhas que participam de uma perda de margem ficam vermelhas. O número se refere à linha expandida, não ao bloco de parágrafo. Uma linha intercalada pode ter um único posto inicial: o cache conserva a sequência integral para esse caso. A imagem original é descoberta por page_id nas tarefas, sem supor igualdade de numeração entre lotes.','',
            '| Bancada | Página | Perdas de margem | Painel |','|---|---|---:|---|']
        for p in R['paineis']:
            out.append(f"| {p['bancada']} | `{p['page_id']}` | {p['perdas_margem']} | [PNG]({Path(p['painel']).relative_to('resultados').as_posix()}) |")
        out.append('')
    out += ["## Protocolo, limitações e retomada", "",
        "Margens originais: centro < 7% e base < 10% no topo; centro > 95% no rodapé; topo → corpo → marcas → rodapé. Texto em linhas; tabelas/imagens indivisíveis. Entrada `random.Random(f\"entrada-{page_id}\")`, fornecida por `ordem_entrada`. Expansão canônica de palavras por `bancada_ordenadores.expansoes`; métricas importadas de `erros_ponta_a_ponta`.", "",
        "golden_v4 participou do desenvolvimento da regra e serve ao ajuste. golden_v3_novo serve apenas à medição final. Silver usa fluxo automático do PDF e split por veículo, com RN para validação e CE/MA/RJ para teste; não é referência humana independente. Nas humanas, 'vistos' significa veículo no split original dos sete veículos de treino; esta variante não recebe treino. Não se usa a anotação como entrada do ordenador.", "",
        "A referência humana foi expandida geometricamente de regiões: não é anotação independente de todas as palavras/linhas/células. Os subtipos são diagnósticos operacionais e podem se confundir; 'outro' preserva casos sem evidência. Classes congeladas disponíveis só no v4, usadas apenas para diagnóstico. Amostras pequenas e de conveniência; seleção entre várias variantes no v4/RN favorece esses resultados. Nenhum retreino/modelo neural nesta tarefa; não se pode inferir ganho com novas sementes ou veículos independentes.", "",
        f"Menor RAM livre observada: {f(R.get('memoria_minima_mb'),1)} MB. Uma página com palavras em memória por vez; nenhum processo filho, DataLoader ou modelo carregado.", "",
        "```powershell", "venv/Scripts/python.exe -B orquestracao/analises/regra_margens_v2.py --etapa diagnostico",
        "venv/Scripts/python.exe -B orquestracao/analises/regra_margens_v2.py --etapa tudo", "```", "",
        "Cópias intermediárias e assinaturas: `resultados/margens_e_transversais_cache/estado.json`. Nenhum arquivo anterior, dado bruto, anotação, documento ou quadro de comunicação é modificado."]
    if R.get("erro"):
        out += ["", "**Parada registrada:** " + R["erro"]]
    return "\n".join(out) + "\n"


def veredito():
    if not R.get('resumos'):
        return 'avaliação ainda parcial'
    partes=[]
    for nome,grupo in (('golden_v3_novo','todos'),('teste_silver','sem_humanas')):
        s=R['resumos'][nome][grupo]['metricas']
        d=s['quebras']['delta']['media']
        tau=s['tau']['delta']['media']
        a,z=s['quebras']['delta']['ic']
        if d < 0 and tau >= 0:
            obs='menos quebras e τ maior/igual'
        elif d < 0:
            obs='menos quebras, com queda de τ'
        elif d > 0:
            obs='mais quebras'
        else:
            obs='mesma média de quebras'
        obs += '; IC das quebras '+('inclui zero' if a<=0<=z else 'exclui zero')
        partes.append(nome+': '+obs)
    return '; '.join(partes)


def main():
    global R, PRAZO
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapa", choices=("diagnostico", "ajuste", "tudo"), default="tudo")
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument('--conferir',action='store_true')
    args = ap.parse_args()
    PRAZO = time.monotonic()+args.max_minutos*60 if args.max_minutos else None
    fontes = fonte_assinatura()
    R = ler(BASE / "estado.json") if (BASE / "estado.json").exists() else {}
    if R and R.get("assinatura_fontes") != hash_obj(fontes):
        exigir(not R.get('avaliacao'),'Fontes alteradas após avaliar: não misturar execuções')
        gravar(BASE/'execucoes'/R['assinatura_fontes']/'estado.json',R)
        R={}
    R.update(fontes=fontes, assinatura_fontes=hash_obj(fontes), splits=ler(RAIZ / "data/processed/splits.json"), comando=sys.argv)
    R['script_sha256']=b.sha(Path(__file__))
    R.pop("erro", None)
    if args.conferir:
        conferir()
        salvar()
        return
    R['humanos'] = sorted({p['page_id'] for nome in ('data/golden/golden_v4/tarefas.jsonl',
                          'data/golden/_avaliacao/golden_v3/tarefas.jsonl') for p in b.jsonl(RAIZ/nome)})
    salvar()
    try:
        ancoras()
        diagnosticar()
        if args.etapa in ('ajuste','tudo'):
            ajustar()
        if args.etapa == "tudo":
            avaliar()
            resumir()
            paineis()
        R["etapa_concluida"] = args.etapa
        salvar()
        conferir()
        salvar()
    except Exception as exc:
        R["erro"] = f"{type(exc).__name__}: {exc}"
        salvar()
        raise


if __name__ == "__main__":
    main()
