"""Testa margens recorrentes no mesmo PDF e veto de corpo, sem treinar.

Mantem as unidades/atomos ls3 e a expansao canonica da bancada; so muda sua
ordem. PyMuPDF le texto e estilo de ate dez paginas vizinhas, sem imagens.
Importa a regua de palavras e o diagnostico das tarefas 05/06. Uma pagina
por vez, CPU, sem workers, rede ou escrita nas fontes. Caches atomicos
permitem retomar apos reinicio. Escolha somente em golden_v4 e RN.

Da raiz: venv/Scripts/python.exe -B orquestracao/analises/margens_repeticao.py
  --etapa ancoras | ajuste | tudo; --conferir reexecuta as ordens e a regua.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ.update(CUDA_VISIBLE_DEVICES='-1', HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='4',
                  MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', NUMEXPR_NUM_THREADS='4')
import argparse
import collections
import gc
import itertools
import json
import math
import re
import statistics
import time
import types
import pymupdf
from orquestracao.analises import regra_margens_v2 as m
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import erros_ponta_a_ponta as e
from src.eval.protocolo import ordem_entrada

BASE = RAIZ / 'resultados/margens_repeticao_cache'
MD = RAIZ / 'resultados/margens_por_repeticao.md'
PRED = RAIZ / 'resultados/ordenadores_sem_caixas/pred'
HUMANAS = ('golden_v4', 'golden_v3_novo')
BANCADAS = HUMANAS + ('validacao_silver', 'teste_silver')
VERSAO = 'repeticao-1'
R = {}
PRAZO = None
METODOS = ('original', 'faixas_so', 'recorrencia_final', 'veto_final',
           'combinacao_final', 'recorrencia_ancorada', 'veto_ancorada', 'combinacao_ancorada')
NOMES = {'original': 'Regra original', 'faixas_so': 'Só faixas de cabeçalho',
         'recorrencia_final': 'Só recorrência / marcas ao final',
         'veto_final': 'Só veto / marcas ao final',
         'combinacao_final': 'Combinação / marcas ao final',
         'recorrencia_ancorada': 'Só recorrência / marcas ancoradas',
         'veto_ancorada': 'Só veto / marcas ancoradas',
         'combinacao_ancorada': 'Combinação / marcas ancoradas'}


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def ler(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def gravar(path, obj):
    path = Path(path).resolve()
    exigir(path == MD or path.is_relative_to(BASE) or
           path.parent == PRED and path.name.startswith('regra_margens_rep__linhas__'),
           f'Saida fora do escopo: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def vigiar(*_):
    if PRAZO and time.monotonic() >= PRAZO:
        raise RuntimeError('Prazo atingido; repetir o comando retoma os caches.')
    mem = b.memoria()
    if mem:
        R['ram_minima_mb'] = min(R.get('ram_minima_mb', mem['ram_livre_mb']), mem['ram_livre_mb'])
        exigir(mem['ram_livre_mb'] >= 900 and mem['commit_livre_mb'] >= 1200,
               f'Parada retomavel por memoria: {mem}')


def clonar(fn, **trocas):
    return types.FunctionType(fn.__code__, {**fn.__globals__, **trocas}, fn.__name__, fn.__defaults__)


def medir(obj, p, ordem):
    return clonar(m.medir, BASE=BASE, R=R, gravar=gravar)(obj, p, ordem)


def preparar(obj, p, ctx):
    return clonar(c.preparar_avaliacao, medir=medir)(obj, p, ctx)


def paginas(nome):
    if nome in HUMANAS:
        yield from b.paginas(nome, 'linhas')
    else:
        yield from clonar(m.paginas_silver, R=R)(nome)


def diagnosticar(nome):
    clonar(m.diagnosticar, HUMANAS=(nome,), R=R, BASE=BASE, gravar=gravar,
           vigiar=vigiar, salvar=salvar, medir=medir, PREPARAR=preparar)()


MESES = r'janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro'
DIAS = r'segunda|terca|quarta|quinta|sexta|sabado|domingo'


def normalizar(texto):
    """Remove caixa, datas e digitos; numero isolado conserva um marcador."""
    texto = m.texto_normal(texto)
    if m.RE_NUM.fullmatch(texto.strip()):
        return '<numero>'
    texto = re.sub(r'\b\d{1,2}\s*(?:de\s*)?(?:' + MESES + r')\s*(?:de\s*)?\d{2,4}\b', ' ', texto)
    texto = re.sub(r'\b(?:' + DIAS + r')(?:[ -]feira)?\b', ' ', texto)
    texto = re.sub(r'\d+', ' ', texto)
    texto = re.sub(r'[^a-z]+', ' ', texto)
    texto = ' '.join(texto.split())
    return texto if len(texto.replace(' ', '')) >= 4 else ''


def fonte_nome(nome):
    return re.sub(r'^[A-Z]{6}\+', '', nome).lower().replace(' ', '')


def estilo_compativel(a, z):
    return bool(a and z and a['fonte'] == z['fonte'] and a['negrito'] == z['negrito']
                and abs(a['tamanho'] - z['tamanho']) <= max(1., .15 * max(a['tamanho'], z['tamanho'])))


def extrair(doc, idx, pdf_sig):
    """Cache por pagina nativa, sem raster, sem bytes de imagens e sem ouro."""
    cp = BASE / 'pdf' / pdf_sig / f'p{idx}.json'
    if cp.exists():
        return ler(cp)
    vigiar()
    pg = doc[idx]
    W, H = pg.mediabox.width, pg.mediabox.height
    linhas = []
    # Bboxes do texto sao relativas ao recorte; converte para a MediaBox.
    dx, dy = pg.cropbox.x0 - pg.mediabox.x0, pg.cropbox.y0 - pg.mediabox.y0
    def caixa(bb):
        return [bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy]
    for bloco in pg.get_text('dict', flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES)['blocks']:
        if bloco['type'] != 0:
            continue
        for ln in bloco['lines']:
            spans = [{'texto': s['text'], 'bbox': caixa(s['bbox']),
                      'fonte': fonte_nome(s['font']), 'tamanho': float(s['size']),
                      'negrito': bool(s['flags'] & 16)} for s in ln['spans'] if s['text'].strip()]
            if not spans:
                continue
            texto = ' '.join(s['texto'].strip() for s in spans)
            principal = max(spans, key=lambda s: len(s['texto']))
            bb = caixa(ln['bbox'])
            linhas.append({'texto': texto, 'normal': normalizar(texto), 'bbox': bb,
                           'y': (bb[1] + bb[3]) / (2 * H), 'direcao': list(ln['dir']),
                           'estilo': {k: principal[k] for k in ('fonte', 'tamanho', 'negrito')},
                           'spans': spans})
    row = {'pagina': idx, 'width': W, 'height': H, 'rotacao': pg.rotation,
           'cropbox': list(pg.cropbox), 'mediabox': list(pg.mediabox), 'linhas': linhas}
    gravar(cp, row)
    return row


def repeticao(p):
    """Seleciona ate dez vizinhas proximas do MESMO PDF, sem referencia."""
    path = RAIZ / 'data/raw' / p['uf'] / p['arquivo']
    exigir(path.is_file(), f'PDF original ausente: {path}')
    st = path.stat()
    fonte = [b.rel(path), st.st_size, st.st_mtime_ns]
    cp = BASE / 'vizinhas' / (e.ac.chave(p['page_id']) + '.json')
    sig = b.digest([VERSAO, fonte, p['pagina']])
    if cp.exists():
        row = ler(cp)
        if row['assinatura'] == sig:
            return row
    with pymupdf.open(path) as doc:
        idx = p['pagina']
        total_pdf = len(doc)
        exigir(0 <= idx < len(doc), 'Indice de pagina fora do PDF')
        vizinhas = sorted(sorted((j for j in range(max(0, idx-10), min(len(doc), idx+11)) if j != idx),
                                key=lambda j: (abs(j-idx), j))[:10])
        chave_pdf = b.digest(fonte)
        alvo = extrair(doc, idx, chave_pdf)
        indice = collections.defaultdict(list)
        for j in vizinhas:
            q = extrair(doc, j, chave_pdf)
            if q['rotacao']:
                continue
            for ln in q['linhas']:
                if ln['normal']:
                    indice[ln['normal']].append({'pagina': j, 'y': ln['y'], 'estilo': ln['estilo']})
                # Spans cobrem fragmentos lado a lado de cabecalhos compostos.
                for s in ln['spans']:
                    norm = normalizar(s['texto'])
                    if norm and norm != ln['normal']:
                        indice[norm].append({'pagina': j,
                            'y': (s['bbox'][1]+s['bbox'][3])/(2*q['height']),
                            'estilo': {k:s[k] for k in ('fonte','tamanho','negrito')}})
    row = {'assinatura': sig, 'fonte_pdf': fonte, 'pagina': idx, 'vizinhas': vizinhas,
           'total_paginas_pdf': total_pdf, 'alvo': alvo, 'indice': dict(indice)}
    gravar(cp, row)
    return row


def evidencias(p, ws, ctx, rep, par):
    """Associa estilo nativo as unidades automaticas; nunca recebe ouro."""
    W, H = (p['dimensions'][k] for k in ('width', 'height'))
    alvo = rep['alvo']
    compativel = not alvo['rotacao'] and abs(W-alvo['width']) < 2 and abs(H-alvo['height']) < 2
    infos = {}
    for u in ctx['cs']:
        uid, bb = u['id'], u['bbox']
        y = c.cy(u)/H
        ln = None
        if compativel and c.tipo_unidade(u) == 'texto':
            possiveis = [z for z in alvo['linhas'] if abs(z['y']*H-c.cy(u)) < .85*ctx['h']
                         and c.sobreposicao(u, z) > .5]
            if possiveis:
                ln = min(possiveis, key=lambda z: (abs(z['y']*H-c.cy(u)),
                         -c.sobreposicao(u, z), z['bbox'][0]))
        estilo = None
        chaves = {normalizar(u.get('text', ''))}
        if ln:
            spans = [s for s in ln['spans'] if c.sobreposicao(u, s) > .5]
            principal = max(spans or ln['spans'], key=lambda s: len(s['texto']))
            estilo = {k:principal[k] for k in ('fonte','tamanho','negrito')}
            chaves.add(ln['normal'])
            chaves.update(normalizar(s['texto']) for s in spans)
        hits = set()
        for key in chaves - {''}:
            hits.update(z['pagina'] for z in rep['indice'].get(key, [])
                        if abs(z['y']-y) <= par['tolerancia_y'] and estilo_compativel(estilo, z['estilo']))
        mesmos = sorted(j for j in hits if j % 2 == rep['pagina'] % 2)
        outros = sorted(hits-set(mesmos))
        paridade = len(mesmos) >= 2 and len(outros) < 2
        pool = [j for j in rep['vizinhas'] if not paridade or j % 2 == rep['pagina'] % 2]
        suportes = mesmos if paridade else sorted(hits)
        lateral = bb[2] < .07*W or bb[0] > .93*W or bb[3]-bb[1] > 3*max(1., bb[2]-bb[0])
        texto = m.texto_normal(u.get('text', ''))
        editorial = bool((m.RE_CAB if y < .5 else m.RE_ROD).search(texto))
        numero = bool(m.RE_NUM.fullmatch(u.get('text', '').strip()))
        recorrente = len(suportes) >= 2 and c.tipo_unidade(u) == 'texto'
        margem = ('topo' if y < .16 else 'rodape' if y > .84 else 'marca' if lateral else None)
        forte = recorrente and margem is not None and len(suportes) >= max(3, math.ceil(.6*len(pool))) and (editorial or numero or lateral)
        infos[uid] = {'estilo': estilo, 'recorrente': recorrente, 'margem_recorrente': margem,
                      'paginas_suporte': suportes, 'paridade': 'mesma' if paridade else 'ambas',
                      'forte': forte, 'lateral': lateral, 'editorial': editorial,
                      'numero': numero, 'veto_corpo': False, 'vizinho_corpo': None}
    # Uma semente de corpo deve estar fora da particao marginal original e
    # nao ter evidencia recorrente editorial. Propaga continuidade sem ouro.
    sementes = {u['id'] for u in ctx['cs'] if c.tipo_unidade(u) == 'texto'
                and u['id'] not in ctx['margem'] and not infos[u['id']]['forte']}
    for _ in range(3):
        novas = set()
        for u in ctx['cs']:
            uid = u['id']
            if c.tipo_unidade(u) != 'texto' or uid in sementes:
                continue
            viz = [z for z in ctx['cs'] if z['id'] in sementes and
                   c.sobreposicao(u,z) >= .65 and
                   min(abs(u['bbox'][0]-z['bbox'][0]), abs(u['bbox'][2]-z['bbox'][2])) <= 2*ctx['h'] and
                   .35*ctx['h'] < abs(c.cy(u)-c.cy(z)) <= par['espacamento_h']*ctx['h'] and
                   estilo_compativel(infos[uid]['estilo'], infos[z['id']]['estilo'])]
            if viz:
                infos[uid]['veto_corpo'] = True
                infos[uid]['vizinho_corpo'] = min(viz, key=lambda z:abs(c.cy(u)-c.cy(z)))['id']
                if not infos[uid]['forte']:
                    novas.add(uid)
        if not novas:
            break
        sementes.update(novas)
    # Linhas ja no corpo tambem vetam a promocao por recorrencia.
    for u in ctx['cs']:
        uid = u['id']
        if uid not in sementes or not infos[uid]['recorrente']:
            continue
        viz = [z for z in ctx['cs'] if z['id'] != uid and z['id'] in sementes and
               c.sobreposicao(u,z) >= .65 and abs(u['bbox'][0]-z['bbox'][0]) <= 2*ctx['h'] and
               .35*ctx['h'] < abs(c.cy(u)-c.cy(z)) <= par['espacamento_h']*ctx['h'] and
               estilo_compativel(infos[uid]['estilo'],infos[z['id']]['estilo'])]
        if viz:
            infos[uid]['veto_corpo'] = True
            infos[uid]['vizinho_corpo'] = viz[0]['id']
    return infos, compativel


def faixas(cs, ids, h, ent):
    """Faixas horizontais por centro, esquerda-direita, sem unir unidades."""
    grupos = []
    rank = {i:j for j,i in enumerate(ent)}
    for i in sorted(ids, key=lambda j:(c.cy(cs[j]),cs[j]['bbox'][0],rank[j])):
        if grupos and abs(c.cy(cs[i])-statistics.mean(c.cy(cs[j]) for j in grupos[-1])) <= .65*h:
            grupos[-1].append(i)
        else:
            grupos.append([i])
    return [i for g in grupos for i in sorted(g,key=lambda j:(cs[j]['bbox'][0],rank[j]))]


def prever(p, ws, rep, par, metodo, ctx=None, infos=None):
    """Contrato: somente unidades automaticas, PDF nativo e parametros fixos."""
    ctx = ctx or c.contexto(p,ws)
    if metodo == 'original':
        return ctx['ordem'], {'fallback': False}
    infos, compativel = evidencias(p,ws,ctx,rep,par) if infos is None else infos
    if len(rep['vizinhas']) < 2 or not compativel:
        return ctx['ordem'], {'fallback': True, 'motivo': 'menos_de_duas_vizinhas' if compativel else 'coordenadas_incompativeis'}
    cs = ctx['cs']
    ent = ordem_entrada(ctx['auto'])
    gs = {g:[] for g in ('topo','corpo','marca','rodape')}
    rec = metodo.startswith(('recorrencia','combinacao'))
    veto = metodo.startswith(('veto','combinacao'))
    diag = {'fallback': False, 'max_colunas':1, 'pontes':0, 'recorrentes':0,
            'vetos':0, 'fortes_contra_veto':0, 'mesma_paridade':0}
    for i in ent:
        u = cs[i]
        uid = u['id']
        inf = infos[uid]
        old = ctx['margem'].get(uid,'corpo')
        g = old
        if rec and c.tipo_unidade(u) == 'texto' and old != 'marca':
            # Altura apenas limita a zona candidata; so a repeticao decide.
            g = inf['margem_recorrente'] if inf['recorrente'] and inf['margem_recorrente'] else 'corpo'
        if veto and g in ('topo','rodape') and inf['veto_corpo']:
            if inf['forte']:
                diag['fortes_contra_veto'] += 1
            else:
                g = 'corpo'
                diag['vetos'] += 1
        # Marcas laterais geometricas exigem recorrencia; marcas sintaticas
        # originais continuam reconhecidas sem vizinhas.
        if rec and inf['recorrente'] and inf['lateral'] and g == 'corpo':
            g = 'marca'
        diag['recorrentes'] += int(inf['recorrente'])
        diag['mesma_paridade'] += int(inf['recorrente'] and inf['paridade']=='mesma')
        gs[g].append(i)
    oc = e.o.ordenar_projecao(cs,gs['corpo'],ctx['h'],e.FIXA.vale,diag,local=True)
    topo = faixas(cs,gs['topo'],ctx['h'],ent)
    fim = faixas(cs,gs['rodape'],ctx['h'],ent)
    marcas = faixas(cs,gs['marca'],ctx['h'],ent)
    if metodo.endswith('_ancorada'):
        for i in marcas:
            # Ancora na zona e coluna geometricamente mais proxima, sem
            # escolher politica pela pagina ou usar ranks humanos.
            texts = [j for j in oc if c.tipo_unidade(cs[j])=='texto']
            col = ctx['col'][cs[min(texts,key=lambda j:abs(c.cx(cs[j])-c.cx(cs[i])) )]['id']] if texts else None
            local = [j for j in oc if ctx['col'][cs[j]['id']]==col]
            abaixo = [j for j in local if c.cy(cs[j])>=c.cy(cs[i])]
            ancora = min(abaixo,key=lambda j:c.cy(cs[j])) if abaixo else (max(local,key=lambda j:c.cy(cs[j])) if local else None)
            pos = oc.index(ancora)+(not abaixo) if ancora is not None else len(oc)
            oc.insert(pos,i)
        indices = topo+oc+fim
    else:
        indices = topo+oc+marcas+fim
    exigir(sorted(indices)==list(range(len(cs))), 'Preditor perdeu/repetiu unidades')
    diag.update({g:len(ids) for g,ids in gs.items()})
    diag['papeis'] = {cs[i]['id']:g for g,ids in gs.items() for i in ids}
    return [cs[i]['id'] for i in indices], diag


def grade():
    return [{'tolerancia_y':y,'espacamento_h':gap} for y,gap in ((.008,1.8),(.014,1.8),(.008,2.2),(.014,2.2))]


def ajustar():
    if R.get('escolha'):
        print('Escolha congelada:',R['escolha']['parametros'],R['escolha']['metodo'],flush=True)
        return
    exigir(not R.get('avaliacao'), 'Nao reajustar depois da comparacao externa')
    tabela = collections.defaultdict(lambda:collections.defaultdict(list))
    ids = []
    for nome in ('golden_v4','validacao_silver'):
        for obj,p in paginas(nome):
            vigiar()
            cp = BASE/'ajuste'/(e.ac.chave(p['page_id'])+'.json')
            fp = b.digest([R['assinatura_fontes'],grade(),obj,p])
            row = ler(cp) if cp.exists() else {}
            if row.get('fingerprint') != fp:
                ctx = c.contexto(p,obj['palavras'])
                rep = repeticao(p)
                exp = b.expansoes(obj,p)
                gt, gset = obj['gt_w'],set(obj['gt_w'])
                meds = {}
                for j,par in enumerate(grade()):
                    infos = evidencias(p,obj['palavras'],ctx,rep,par)
                    for metodo in METODOS:
                        if metodo in ('original','faixas_so') and j:
                            continue
                        ordem,_ = prever(c.automatico(p),obj['palavras'],rep,par,metodo,ctx,infos)
                        seq = [k for uid in ordem for k in exp[uid]]
                        meds[f'{j}:{metodo}'] = {'tau':e.o.kendall_tau([k for k in seq if k in gset],gt),
                                               'quebras':len(e.eventos(seq,gt))}
                row = {'page_id':p['page_id'],'bancada':nome,'metricas':meds,'fingerprint':fp}
                gravar(cp,row)
            for key,med in row['metricas'].items():
                tabela[key][nome].append(med)
            ids.append(p['page_id'])
            R['progresso_ajuste'] = len(ids)
            salvar()
            print(f'Ajuste {nome}: {len(ids)} paginas acumuladas',flush=True)
            gc.collect()
    tab = {key:{n:{k:statistics.mean(r[k] for r in rows) for k in ('tau','quebras')}
                for n,rows in coortes.items()} for key,coortes in tabela.items()}
    base = tab['0:original']
    candidatos = [key for key in tab if ':combinacao_' in key]
    elegiveis = [key for key in candidatos if all(tab[key][n]['tau']>=base[n]['tau']-.002 for n in base)]
    def custo(key):
        return (sum(tab[key][n]['quebras'] for n in base), -sum(tab[key][n]['tau'] for n in base),key)
    key = min(elegiveis or candidatos,key=custo)
    j,metodo = key.split(':')
    R['escolha'] = {'parametros':grade()[int(j)],'metodo':metodo,'tabela':tab,'ids_ajuste':ids,
        'tau_admissivel':bool(elegiveis),'congelada_em':time.strftime('%Y-%m-%d %H:%M:%S'),
        'criterio':'Menor soma das medias de quebras v4+RN entre combinacoes; perda de tau <=0,002 em cada; maior tau e chave como desempate. Ablacoes usam os mesmos parametros.'}
    gravar(BASE/'escolha_congelada.json',R['escolha'])
    salvar()
    print('Escolha congelada:',R['escolha']['parametros'],metodo,flush=True)


def transicoes(nome,obj,p,ctx):
    if nome in HUMANAS:
        return ler(BASE/'diagnostico'/nome/(e.ac.chave(p['page_id'])+'.json'))['transicoes']
    _,_,trs,_ = preparar(obj,p,ctx)
    pap,_ = m.evidencia(ctx)
    for tr in trs:
        if tr['tipo']=='margem':
            tr['subtipo'] = m.subtipo(ctx,tr['a'],tr['z'],pap)
    return trs


def saldo(trs,q,seq):
    rank = {k:i for i,k in enumerate(seq)}
    ls = {L['id']:L['ks'] for L in q['gold_lines']}
    intacta = {lid:all(rank[z]==rank[a]+1 for a,z in zip(ks,ks[1:])) for lid,ks in ls.items()}
    total = {'original':0,'variante':0,'corrigidas':0,'novas':0}
    subs = {st:dict(total) for st in m.ROT}
    for tr in trs:
        ac = bool(intacta[tr['linha_a']] and intacta[tr['linha_z']] and rank[tr['palavra_z']]==rank[tr['palavra_a']]+1)
        vals = {'original':int(not tr['acerto']),'variante':int(not ac),
                'corrigidas':int(not tr['acerto'] and ac),'novas':int(tr['acerto'] and not ac)}
        for k,v in vals.items():
            total[k] += v
            if tr['tipo']=='margem':
                subs[tr['subtipo']][k] += v
    for row in [total,*subs.values()]:
        row['saldo'] = row['corrigidas']-row['novas']
        exigir(row['original']-row['variante']==row['saldo'],'Saldo inconsistente')
    return total,subs


def avaliar():
    par = R['escolha']['parametros']
    for nome in BANCADAS:
        if nome == 'golden_v3_novo':
            diagnosticar(nome)
        rows = []
        for obj,p in paginas(nome):
            vigiar()
            cp = BASE/'avaliacao'/nome/(e.ac.chave(p['page_id'])+'.json')
            fp = b.digest([R['assinatura_fontes'],par,METODOS,obj,p])
            row = ler(cp) if cp.exists() else {}
            if row.get('fingerprint') != fp:
                ctx = c.contexto(p,obj['palavras'])
                rep = repeticao(p)
                infos = evidencias(p,obj['palavras'],ctx,rep,par)
                trs = transicoes(nome,obj,p,ctx)
                meds = {}
                for metodo in METODOS:
                    ordem,diag = prever(c.automatico(p),obj['palavras'],rep,par,metodo,ctx,infos)
                    med,seq,q,_ = medir(obj,p,ordem)
                    total,subs = saldo(trs,q,seq)
                    meds[metodo] = {'metricas':med,'ordem':ordem,'diag':diag,'sucessores':total,'subtipos':subs}
                row = {'page_id':p['page_id'],'uf':p['uf'],'visto_treino':p['uf'] in R['splits']['treino'],
                       'sobrepoe_humanas':p['page_id'] in R['humanos'],'vizinhas':rep['vizinhas'],
                       'estilos_associados':sum(bool(v['estilo']) for v in infos[0].values()),
                       'unidades':len(p['bounding_boxes']),'metodos':meds,'fingerprint':fp}
                gravar(cp,row)
            rows.append(row)
            R.setdefault('avaliacao',{})[nome] = {'completa':False,'paginas':rows}
            salvar()
            print(f'Avaliacao {nome}: {len(rows)} paginas',flush=True)
            gc.collect()
        exigir(rows, f'Bancada vazia: {nome}')
        R['avaliacao'][nome]['completa'] = True
        resumir(nome)
        exportar(nome,rows)
        salvar()


def exportar(nome,rows):
    metodo = R['escolha']['metodo']
    content = ''.join(json.dumps({'page_id':r['page_id'],'ordem':r['metodos'][metodo]['ordem']},ensure_ascii=False)+'\n' for r in rows)
    path = PRED/f'regra_margens_rep__linhas__{nome}.jsonl'
    if path.exists():
        exigir(path.read_text(encoding='utf-8')==content,'Predicao anterior difere; nao sobrescrever')
    else:
        gravar(path,content)
    exigir(set(b.indice_pred(path))=={r['page_id'] for r in rows},'Contrato da bancada divergente')
    R['avaliacao'][nome]['pred_sha256'] = b.sha(path)
    # Ordens das ablacoes tambem sao reviewaveis, dentro do cache proprio.
    for met in METODOS:
        text = ''.join(json.dumps({'page_id':r['page_id'],'ordem':r['metodos'][met]['ordem']},ensure_ascii=False)+'\n' for r in rows)
        gravar(BASE/'pred'/f'{met}__linhas__{nome}.jsonl',text)


def resumir(nome):
    rows = R['avaliacao'][nome]['paginas']
    grupos = {'todos':rows}
    if nome in HUMANAS:
        grupos.update(vistos=[r for r in rows if r['visto_treino']],nao_vistos=[r for r in rows if not r['visto_treino']])
    if nome == 'teste_silver':
        grupos['sem_humanas'] = [r for r in rows if not r['sobrepoe_humanas']]
    sums = {}
    for grupo,rs in grupos.items():
        if not rs:
            continue
        sums[grupo] = {}
        for met in METODOS:
            simpl = [{'uf':r['uf'],'original':r['metodos']['original']['metricas'],
                      'variante':r['metodos'][met]['metricas']} for r in rs]
            st = m.estatisticas(simpl)
            st['sucessores'] = {k:sum(r['metodos'][met]['sucessores'][k] for r in rs) for k in rs[0]['metodos'][met]['sucessores']}
            st['subtipos'] = {s:{k:sum(r['metodos'][met]['subtipos'][s][k] for r in rs)
                                for k in rs[0]['metodos'][met]['subtipos'][s]} for s in m.ROT}
            st['fallback'] = sum(r['metodos'][met]['diag']['fallback'] for r in rs)
            sums[grupo][met] = st
    R.setdefault('resumos',{})[nome] = sums
    gravar(BASE/'estatisticas.json',R['resumos'])


def f(v,casas=3):
    return '—' if v is None else f'{v:.{casas}f}'.replace('.',',')


def cel(v,casas=3,pct=False):
    scale = 100 if pct else 1
    return f"{f(v['media']*scale,casas)} [{f(v['ic'][0]*scale,casas)}; {f(v['ic'][1]*scale,casas)}]" if v['media'] is not None else '—'


def alvo():
    met = R.get('escolha',{}).get('metodo')
    sums = R.get('resumos',{})
    if not met or not all(n in sums for n in ('golden_v4','golden_v3_novo','teste_silver')):
        return 'Ainda não concluído.',False
    a = sums['golden_v4']['todos'][met]['subtipos']['e']
    v3 = sums['golden_v3_novo']['todos'][met]['sucessores']['saldo']
    teste = sums['teste_silver']['sem_humanas'][met]['sucessores']['saldo']
    ok = a['corrigidas'] >= math.ceil(.25*a['original']) and v3>0 and teste>0
    return (f"{'Atingido' if ok else 'Não atingido'}: corpo no v4 recuperou {a['corrigidas']}/{a['original']} "
            f"({f(100*a['corrigidas']/a['original'],1)}%), com {a['novas']} novas perdas; "
            f"saldo de todos os sucessores fora do ajuste: v3={v3:+d}; teste sem bancadas humanas={teste:+d}."),ok


def relatorio():
    anc = R.get('ancoras',{})
    escolha = R.get('escolha',{})
    met = escolha.get('metodo')
    sums = R.get('resumos',{})
    topo = [f"Âncoras: {'aprovadas' if anc.get('aprovadas') else 'pendentes'}; referência e unidades preservadas.",
            f"Variante: {NOMES.get(met,'ainda em ajuste')}; parâmetros escolhidos só em v4 e RN."]
    if 'golden_v4' in sums:
        mk = sums['golden_v4']['todos'][met]['metricas']
        topo[0] += f" V4: quebras {f(mk['quebras']['original']['media'],3)} → {f(mk['quebras']['variante']['media'],3)}; τ {f(mk['tau']['original']['media'],6)} → {f(mk['tau']['variante']['media'],6)}."
    for n in ('golden_v3_novo','teste_silver'):
        if n in sums:
            grupo = 'sem_humanas' if n == 'teste_silver' else 'todos'
            st = sums[n][grupo][met]
            rot = n + (' sem sobreposição humana' if n == 'teste_silver' else '')
            topo.append(f"{rot}: n={st['n']}; Δ quebras {cel(st['metricas']['quebras']['delta'],3)}; Δ τ {cel(st['metricas']['tau']['delta'],6)}.")
        else:
            topo.append(f'{n}: execução ainda não concluída.')
    topo.append('Alvo operacional: '+alvo()[0])
    out = ['# Margens por repetição entre páginas e veto de corpo','',*['%d. %s'%(i+1,t) for i,t in enumerate(topo)],'',
           'Relatório escrito pelo script a partir dos caches. Estado: '+R.get('etapa','iniciando')+'.', '']
    if R.get('erro'):
        out += ['**Parada retomável:** '+R['erro'],'']
    if anc.get('medias'):
        out += ['## Âncoras','', '| Controle | Páginas | τ palavras | Quebras/página |', '|---|---:|---:|---:|']
        ms=anc['medias']
        out += [f"| Regra original | {anc['n']} | {f(ms['tau'],6)} | {f(ms['quebras'],6)} |",
                f"| Extrator + XY-cut + margens | {anc['n']} | {f(ms['p1m_tau'],6)} | {f(ms['p1m_quebras'],6)} |",'',
                'Regra original reexecutada e sequência inteira conferida contra P2 histórico. P1m é a sequência histórica reavaliada na referência atual. Falha da âncora interrompe a execução antes do ajuste.','']
    out += ['## Procedimento e limites','',
        'São as mesmas linhas e átomos ls3 congelados da bancada, com expansão interna canônica de `bancada_ordenadores.expansoes`. O detector não é carregado. O preditor recebe apenas texto, coordenadas, tipo automático e estilo nativo; classes humanas só entram no diagnóstico importado.', '',
        'PyMuPDF extrai linhas e spans (fonte, tamanho e negrito) da página alvo e de até dez vizinhas próximas do mesmo PDF. Remove caixa, dígitos e datas do texto; número isolado ganha um marcador. Exige o mesmo texto normalizado, posição vertical aproximada e estilo compatível em pelo menos duas vizinhas. Quando o suporte ocorre apenas na mesma paridade, compara pares com pares e ímpares com ímpares. O índice da página é zero-based; a separação de paridades é equivalente à numeração iniciada em um.', '',
        'A posição extrema (16% no topo/base) delimita candidata, e não decide sozinha no método de recorrência. Linhas recorrentes no interior ficam no corpo, exceto marca lateral. O veto exige alinhamento de coluna, espaçamento de linha e fonte/tamanho/negrito compatíveis com uma vizinha de corpo. Evidência forte que vence o veto exige recorrência em ao menos três páginas e 60% das vizinhas pertinentes, com sinal editorial, número isolado ou forma lateral. A semente de corpo deriva da partição automática original, não da referência.', '',
        'Cabeçalhos e rodapés são ordenados por faixas horizontais de centros próximos (0,65 altura de palavra), e dentro delas da esquerda para a direita. O corpo reutiliza a projeção local original, sem novas barreiras. Marcas usam duas políticas aplicadas a todas as páginas: fluxo após corpo e antes de rodapé; ou inserção pela altura na zona/coluna geometricamente mais próxima. Nunca se escolhe a política por página.', '',
        'A ablação só veto conserva a partição marginal original e testa a continuidade/estilo. A ablação só recorrência dispensa o veto. Só faixas isola a mudança de ordenação dos cabeçalhos. Linhas/átomos não são partidos. Menos de duas vizinhas ou coordenadas nativas incompatíveis conservam exatamente a regra original, inclusive nas ablações.', '',
        'Sem treino, GPU, rede, OCR, multiprocessing ou dados do projeto parceiro. Um processo e uma página com palavras por vez; no máximo quatro threads nas bibliotecas numéricas. Caches por PDF/página/ordem, escrita atômica e parada por pouca RAM. O cache nativo valida caminho, tamanho e mtime do PDF; as fontes da bancada têm SHA-256.', '',
        'golden_v4 foi usado no desenvolvimento da regra e no ajuste deste experimento. golden_v3_novo já foi consultado em rodadas anteriores: é comparação externa ao ajuste atual, não teste intocado. A silver é automática, por fluxo de palavras do PDF nos veículos confiáveis; a validação é RN e o teste CE, MA e RJ. RN exclui páginas presentes em qualquer tarefa humana, seguindo a tarefa 06. Veículos vistos seguem os sete veículos do split original, sem novo treino. Amostra humana pequena e referências humanas expandidas geometricamente dentro das regiões.', '',
        'IC 95% por bootstrap de veículos e Wilcoxon bilateral Pratt sobre diferenças médias por veículo, importados das tarefas anteriores; as médias principais ponderam páginas. Com poucos veículos de teste, os IC/p-valores têm pouca resolução. Ablações exploratórias sem correção de multiplicidade. Teste completo e teste sem qualquer página das bancadas humanas são mostrados separados.', '']
    if escolha:
        out += ['## Escolha congelada antes da comparação externa','',
            '`'+json.dumps(escolha['parametros'],ensure_ascii=False)+'`; '+NOMES[met]+'.', '',
            escolha['criterio'], '',
            f"Congelada em {escolha['congelada_em']}; restrição de τ satisfeita: {escolha['tau_admissivel']}.", '',
            'Grade de configurações: '+ '; '.join(f"{j} = tolerância vertical {f(p['tolerancia_y']*100,1)}% da altura, espaçamento {f(p['espacamento_h'],1)} alturas de palavra" for j,p in enumerate(grade()))+'.', '',
            '| Configuração | v4: τ / quebras | RN: τ / quebras |', '|---|---:|---:|']
        for key,co in escolha['tabela'].items():
            out.append('| '+key+' | '+' | '.join(f"{f(co[n]['tau'],6)} / {f(co[n]['quebras'],3)}" for n in ('golden_v4','validacao_silver'))+' |')
        out += ['']
    for nome,val in R.get('avaliacao',{}).items():
        rows=val['paginas']
        out += [f'## {nome}','',f"Cobertura: {len(rows)} páginas; {'completa' if val['completa'] else 'parcial, retomável'}.", '']
        if nome not in sums:
            continue
        out += ['| Ablação | n / veículos | τ [IC] | Quebras/página [IC] | Fidelidade de 12 (%) [IC] | Sucessor de linhas (%) [IC] |', '|---|---:|---:|---:|---:|---:|']
        for method,st in sums[nome]['todos'].items():
            mk=st['metricas']
            out.append(f"| {NOMES[method]}{' **selecionada**' if method==met else ''} | {st['n']} / {st['veiculos']} | {cel(mk['tau']['variante'],6)} | {cel(mk['quebras']['variante'],3)} | {cel(mk['fid12']['variante'],2,True)} | {cel(mk['sucessor_linhas']['variante'],2,True)} |")
        out += ['', '| Ablação contra original | Δ quebras [IC] / p veículo | Δ τ [IC] / p veículo | Δ fidelidade de 12 (p.p.) [IC] / p | Δ sucessor (p.p.) [IC] / p |', '|---|---:|---:|---:|---:|']
        for method,st in sums[nome]['todos'].items():
            if method=='original':
                continue
            out.append('| '+NOMES[method]+' | '+' | '.join(cel(st['metricas'][k]['delta'],6 if k=='tau' else 3,k in ('fid12','sucessor_linhas'))+' / '+f(st['metricas'][k]['wilcoxon']['p'],6) for k in ('quebras','tau','fid12','sucessor_linhas'))+' |')
        out += ['', '| Estrato: variante selecionada | n / veículos | τ [IC] | Quebras/página [IC] | Δ quebras [IC] / p | Fid.12 (%) [IC] | Sucessor (%) [IC] |', '|---|---:|---:|---:|---:|---:|---:|']
        for grupo,methods in sums[nome].items():
            st=methods[met]; mk=st['metricas']
            out.append(f"| {grupo} | {st['n']} / {st['veiculos']} | {cel(mk['tau']['variante'],6)} | {cel(mk['quebras']['variante'],3)} | {cel(mk['quebras']['delta'],3)} / {f(mk['quebras']['wilcoxon']['p'],6)} | {cel(mk['fid12']['variante'],2,True)} | {cel(mk['sucessor_linhas']['variante'],2,True)} |")
        if nome in HUMANAS:
            for g in ('vistos','nao_vistos'):
                if g not in sums[nome]:
                    out.append(f'| {g} | 0 / 0 | — | — | — | — | — |')
        if nome == 'teste_silver':
            out += ['', '| Ablações no teste SEM páginas humanas | n | τ | Quebras/página | Δ quebras [IC] / p veículo | Saldo de sucessores |', '|---|---:|---:|---:|---:|---:|']
            for method,st in sums[nome]['sem_humanas'].items():
                mk = st['metricas']
                out.append(f"| {NOMES[method]} | {st['n']} | {f(mk['tau']['variante']['media'],6)} | {f(mk['quebras']['variante']['media'],3)} | {cel(mk['quebras']['delta'],3)} / {f(mk['quebras']['wilcoxon']['p'],6)} | {st['sucessores']['saldo']:+d} |")
        out += ['', '| Ablação / subtipo original congelado | Perdidos original | Recuperados | Novos perdidos | Saldo | Perdidos variante |', '|---|---:|---:|---:|---:|---:|']
        for method,st in sums[nome]['todos'].items():
            if method=='original':
                continue
            for sub in ('e','d','c'):
                ss=st['subtipos'][sub]
                out.append(f"| {NOMES[method]} / {m.ROT[sub]} | {ss['original']} | {ss['corrigidas']} | {ss['novas']} | {ss['saldo']:+d} | {ss['variante']} |")
        st=sums[nome]['todos'][met]; total=st['sucessores']
        out += ['',f"Todos os tipos de sucessor: recuperados={total['corrigidas']}; novos perdidos={total['novas']}; saldo={total['saldo']:+d}.",
            f"Sem nenhuma vizinha: {sum(len(r['vizinhas'])==0 for r in rows)}; com uma só: {sum(len(r['vizinhas'])==1 for r in rows)}; com 2–4: {sum(2<=len(r['vizinhas'])<5 for r in rows)}; com 5–10: {sum(len(r['vizinhas'])>=5 for r in rows)}; fallback total: {st['fallback']}.",
            f"Estilo associado em {sum(r['estilos_associados'] for r in rows)}/{sum(r['unidades'] for r in rows)} unidades (inclui átomos, para os quais não se procura estilo).", '']
        out += ['| Estrato / subtipo: combinação selecionada | Perdidos original | Recuperados | Novos perdidos | Saldo |', '|---|---:|---:|---:|---:|']
        for grupo,methods in sums[nome].items():
            for sub in ('e','d','c'):
                ss = methods[met]['subtipos'][sub]
                out.append(f"| {grupo} / {m.ROT[sub]} | {ss['original']} | {ss['corrigidas']} | {ss['novas']} | {ss['saldo']:+d} |")
        out += ['']
        if nome in HUMANAS or nome=='teste_silver':
            grupo = 'sem_humanas' if nome == 'teste_silver' else 'todos'
            st = sums[nome][grupo][met]
            marginal = sum(s['saldo'] for s in st['subtipos'].values())
            out += [f"No estrato {grupo}, saldo em transições originalmente marginais={marginal:+d}; em todas as demais transições={st['sucessores']['saldo']-marginal:+d}. A classificação permanece congelada: novas perdas no corpo originalmente comum não são reclassificadas como margem após a intervenção.", '']
            externos = [r for r in rows if grupo != 'sem_humanas' or not r['sobrepoe_humanas']]
            piores = sorted((r for r in externos if r['metodos'][met]['metricas']['quebras']>r['metodos']['original']['metricas']['quebras']),
                            key=lambda r:(r['metodos']['original']['metricas']['quebras']-r['metodos'][met]['metricas']['quebras'],r['page_id']))[:3]
            if piores:
                out += ['Maiores regressões observadas da combinação (sem escolha posterior de política):', '']
                for r in piores:
                    a,z = r['metodos']['original'],r['metodos'][met]
                    out.append(f"- `{r['page_id']}`: quebras {a['metricas']['quebras']} → {z['metricas']['quebras']}; Δ τ {f(z['metricas']['tau']-a['metricas']['tau'],6)}; sucessores recuperados={z['sucessores']['corrigidas']}, novos perdidos={z['sucessores']['novas']}.")
                out += ['']
        if nome=='teste_silver':
            out += [f"Sobreposição com bancadas humanas: {sum(r['sobrepoe_humanas'] for r in rows)} páginas. O estrato sem_humanas é a avaliação externa mais limpa.",'']
    out += ['## O que as ablações mostram','',
            'A combinação selecionada continua a mesma da escolha v4+RN. Comparações com a ablação só veto são descritivas; ela não substitui a variante nas predições selecionadas após observar o teste.', '',
            '| Bancada / estrato | Combinação: Δ quebras [IC] | Só veto, marcas ancoradas: Δ quebras [IC] | Recorrência adicionada ao veto: Δ quebras |', '|---|---:|---:|---:|']
    for n in BANCADAS:
        if n not in sums:
            continue
        grupo = 'sem_humanas' if n == 'teste_silver' else 'todos'
        co = sums[n][grupo]
        ca = co[met]['metricas']['quebras']
        ve = co['veto_ancorada']['metricas']['quebras']
        out.append(f"| {n} / {grupo} | {cel(ca['delta'],3)} | {cel(ve['delta'],3)} | {f(ca['variante']['media']-ve['variante']['media'],3)} |")
    if all(n in sums for n in ('golden_v3_novo','teste_silver')):
        v3 = sums['golden_v3_novo']['todos']['veto_ancorada']['metricas']['quebras']
        te = sums['teste_silver']['sem_humanas']['veto_ancorada']['metricas']['quebras']
        out += ['', f"Só veto com marcas ancoradas: v3 {f(v3['original']['media'],3)} → {f(v3['variante']['media'],3)} quebras/página (p por veículo={f(v3['wilcoxon']['p'],6)}); teste sem humanas {f(te['original']['media'],3)} → {f(te['variante']['media'],3)} (p={f(te['wilcoxon']['p'],6)}). Esta ablação ajuda a separar o efeito de continuidade/estilo do efeito de exigir recorrência; o teste tem apenas os veículos do split e os IC devem acompanhar a leitura.", '']
    out += ['## Alvo e problemas que permanecem','',alvo()[0], '',
        'O alvo operacional exige recuperar pelo menos um quarto dos sucessores de corpo marginalizado do v4 e saldo positivo de todos os sucessores, separadamente no v3 e no teste sem bancadas humanas. Saldo por corpo, marca e cabeçalho também aparece acima; nenhum ganho interno substitui a comparação externa.', '',
        'O diagnóstico usa literalmente o emparelhamento e os subtipos das tarefas 05/06, congelados pela regra original. Classes de regiões só são usadas no diagnóstico v4; v3 e silver usam proxies geométricos/lexicais e não têm a mesma qualidade de classificação. Sucessores perdidos e quebras emitidas têm denominadores diferentes.', '',
        'Repetição não identifica cabeçalho exclusivo da primeira página, não distingue todo título recorrente de corpo e pode perder texto com extração nativa fragmentada. Estilo ausente impede veto; a exigência de negrito igual pode preservar uma falsa margem. Não corrige ordem interna de tabela/imagem, linha partida, OCR ausente, calhas ou títulos transversais. O fluxo silver dentro das tabelas pode divergir da expansão canônica.', '',
        'Fontes, parâmetros, resultados por página, diagnósticos e ordens das ablações: `resultados/margens_repeticao_cache/`. Predições selecionadas: `resultados/ordenadores_sem_caixas/pred/regra_margens_rep__linhas__<bancada>.jsonl`.','']
    if R.get('conferencia'):
        out += ['## Verificação','',json.dumps(R['conferencia'],ensure_ascii=False),'']
    if R.get('ram_minima_mb') is not None:
        out += [f"Menor RAM física livre observada nas verificações: {f(R['ram_minima_mb'],1)} MiB (não é medida do pico de memória do processo).", '']
    out += ['Comando: `'+ ' '.join(R.get('comando',[]))+'`','']
    return '\n'.join(out)


def salvar():
    gravar(BASE/'estado.json',R)
    gravar(MD,relatorio())


def conferir():
    exigir(R['ancoras']['aprovadas'],'Ancora nao aprovada')
    exigir(ler(BASE/'escolha_congelada.json')==R['escolha'],'Escolha alterada')
    ajuste=set(R['escolha']['ids_ajuste'])
    n=0
    for nome,val in R['avaliacao'].items():
        exigir(val['completa'],'Bancada incompleta')
        saved={r['page_id']:r for r in val['paginas']}
        ids=set()
        for obj,p in paginas(nome):
            vigiar()
            ids.add(p['page_id']); row=saved[p['page_id']]
            if nome=='golden_v3_novo' or nome=='teste_silver' and not row['sobrepoe_humanas']:
                exigir(p['page_id'] not in ajuste,'Vazamento no ajuste')
            ctx=c.contexto(p,obj['palavras']); rep=repeticao(p)
            par=R['escolha']['parametros']; infos=evidencias(p,obj['palavras'],ctx,rep,par)
            exp=b.expansoes(obj,p); q=b.referencia(obj,p); gs=set(q['gt_w'])
            for met in METODOS:
                ordem,_=prever(c.automatico(p),obj['palavras'],rep,par,met,ctx,infos)
                exigir(ordem==row['metodos'][met]['ordem'],'Ordem diverge do cache')
                seq=[k for uid in ordem for k in exp[uid]]
                med=row['metodos'][met]['metricas']
                exigir(len(e.eventos(seq,q['gt_w']))==med['quebras'],'Quebras divergem')
                exigir(e.o.kendall_tau([k for k in seq if k in gs],q['gt_w'])==med['tau'],'Tau diverge')
                if n==0 or p['page_id']==next(iter(saved)):
                    completo=e.medir(q,seq,[],{},'P0')
                    exigir(all(completo[k]==med[k] for k in m.METRICAS if k!='piso_interno'),'Regua completa diverge')
            n+=1
        exigir(ids==set(saved),'Cobertura divergente')
        pp=PRED/f'regra_margens_rep__linhas__{nome}.jsonl'
        exigir(b.sha(pp)==val['pred_sha256'],'Predicao modificada')
        antigo=R['resumos'][nome]
        resumir(nome)
        exigir(antigo==R['resumos'][nome],'Estatisticas divergentes')
    atuais = fontes()
    proprio = b.rel(Path(__file__))
    exigir({k:v for k,v in atuais.items() if k!=proprio}==
           {k:v for k,v in R['fontes'].items() if k!=proprio}, 'Fontes de dados/dependencias alteradas')
    # --conferir e a unica via para aceitar uma revisao deste script: todas
    # as ordens precisam coincidir com o resultado congelado, sem reajuste.
    if atuais != R['fontes']:
        R.setdefault('revisoes_verificadas',[]).append({'script_anterior':R['fontes'][proprio],
            'script_atual':atuais[proprio], 'ordens_preservadas':True,
            'parametros_preservados':ler(BASE/'escolha_congelada.json')==R['escolha']})
        R['fontes'] = atuais
        R['assinatura_fontes'] = b.digest(atuais)
    R['conferencia']={'paginas_reexecutadas':n,'metodos_por_pagina':len(METODOS),
                     'regua_completa_primeira_pagina_por_bancada':True,
                     'contratos_e_estatisticas':True,'fontes_preservadas':True,'device':'cpu','num_workers':0}
    salvar()
    exigir(MD.read_text(encoding='utf-8')==relatorio(),'Relatorio diverge do estado')
    print('Conferencia aprovada:',R['conferencia'],flush=True)


def fontes():
    paths=set(b.DEP_PATHS)|{Path(m.__file__),Path(c.__file__),Path(__file__),e.JSON,
        RAIZ/'data/processed/splits.json',RAIZ/'data/golden/golden_v4/tarefas.jsonl',
        RAIZ/'data/golden/_avaliacao/golden_v3/tarefas.jsonl'}
    paths.update(b.UNIDADES/'bancadas'/(n+'.jsonl') for n in HUMANAS)
    splits=ler(RAIZ/'data/processed/splits.json')
    paths.update(b.UNIDADES/'linhas'/(uf+suf) for uf in splits['teste']+splits['validacao'] for suf in ('.jsonl','.palavras.jsonl'))
    return {b.rel(p):b.sha(p) for p in sorted(paths)}


def main():
    global R,PRAZO
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--etapa',choices=('ancoras','ajuste','tudo'),default='tudo')
    ap.add_argument('--max-minutos',type=float,default=0)
    ap.add_argument('--conferir',action='store_true')
    args=ap.parse_args()
    PRAZO=time.monotonic()+args.max_minutos*60 if args.max_minutos else None
    src=fontes()
    old=ler(BASE/'estado.json') if (BASE/'estado.json').exists() else {}
    proprio = b.rel(Path(__file__))
    revisao = (old and args.conferir and old.get('escolha') and
        {k:v for k,v in old['fontes'].items() if k!=proprio}=={k:v for k,v in src.items() if k!=proprio})
    exigir(not old or old['fontes']==src or revisao,
           'Fontes/script mudaram; nao misturar execucoes. Para revisao do proprio script, use --conferir, que exige ordens e parametros preservados.')
    R=old or {'versao':VERSAO,'fontes':src,'assinatura_fontes':b.digest(src),
              'splits':ler(RAIZ/'data/processed/splits.json')}
    R['comando']=sys.argv
    R['humanos']=sorted({p['page_id'] for path in ('data/golden/golden_v4/tarefas.jsonl',
                          'data/golden/_avaliacao/golden_v3/tarefas.jsonl') for p in b.jsonl(RAIZ/path)})
    R['etapa']=args.etapa
    R.pop('erro',None)
    salvar()
    try:
        vigiar()
        # Importacoes nao carregam pesos. Se torch ja estiver importado,
        # limita suas threads; nao cria contexto CUDA.
        if 'torch' in sys.modules:
            sys.modules['torch'].set_num_threads(4)
        clonar(m.ancoras,R=R,salvar=salvar,vigiar=vigiar)()
        if args.conferir:
            conferir()
            return
        if args.etapa!='ancoras':
            diagnosticar('golden_v4')
            totais={s:sum(r['contagem_subtipos'].get(s,0) for r in R['diagnostico']['golden_v4']) for s in ('e','d','c')}
            exigir(totais=={'e':47,'d':40,'c':28},f'Diagnostico original mudou: {totais}')
            ajustar()
        if args.etapa=='tudo':
            avaliar()
            conferir()
        R['etapa']='concluída: '+args.etapa
        salvar()
    except Exception as exc:
        R['erro']=f'{type(exc).__name__}: {exc}'
        salvar()
        raise


if __name__=='__main__':
    main()
