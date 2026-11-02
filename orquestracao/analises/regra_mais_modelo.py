"""Testa intervencoes locais do LayoutLM textual na regra de colunas.

A regra fornece a ordem; somente alertas automaticos autorizam propostas.
Reusa candidatos do corretor, alertas da tarefa 08, ComTexto e decoder do
sucessor. A regua de palavras e importada, nunca reimplementada. Seleciona
duas intensidades de alerta x tres vantagens de logit em RN e golden_v4,
congela a escolha e so entao avalia golden_v3_novo e teste silver.

Uso, da raiz: venv/Scripts/python.exe -B
 orquestracao/analises/regra_mais_modelo.py
 --somente-ancoras verifica os controles sem carregar rede.
 --limite 1 prova o fluxo; nao seleciona limiar nem conclui o experimento.
 --relatorio recompila somente o relatorio a partir do estado persistido.
 --conferir audita caches, ordens, reparos e selecao sem inferir novamente.
Tudo e sequencial em CPU, com quatro threads e sem treino/workers/rede.
Escritas restritas ao relatorio pedido e resultados/regra_mais_modelo_cache.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import os
os.environ.update(CUDA_VISIBLE_DEVICES='-1', HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                  OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
                  OPENBLAS_NUM_THREADS='4', NUMEXPR_NUM_THREADS='4')
import argparse
import collections
import gc
import hashlib
import itertools
import json
import math
import statistics
import time
import traceback
from contextlib import contextmanager

from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import reordenacao_restrita as rr
from orquestracao.analises import ordenar_bancadas_texto as inferencia
b, e, texto = c.b, c.e, inferencia.texto
t = texto.t
BASE = RAIZ / 'resultados/regra_mais_modelo_cache'
MD = RAIZ / 'resultados/regra_mais_modelo_seletivo.md'
CK = RAIZ / 'resultados/ordenadores_treinados_sem_caixas/sucessor_linhas_texto_s42/melhor.pt'
COORTES = ('validacao_silver', 'golden_v4', 'golden_v3_novo', 'teste_silver')
ALERTAS = ('estrito', 'amplo')
LIMIARES = (0., 1., 3.)
GRADE = [(al, lim) for al in ALERTAS for lim in LIMIARES]
NIVEL, JANELA = 3, 12
METRICAS = ('tau', 'quebras', 'fid12', 'sucessor_linhas')
VERSAO = 'seletivo-textual-v1'


def exigir(ok, msg):
    if not ok:
        raise ValueError(msg)


def ler(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for bloco in iter(lambda: f.read(1024*1024), b''):
            h.update(bloco)
    return h.hexdigest()


def gravar(p, obj):
    p = Path(p).resolve()
    exigir(p == MD or p.is_relative_to(BASE), 'Escrita fora dos destinos autorizados')
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name + '.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as f:
        f.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False,
                                                          indent=2, allow_nan=False))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, p)


@contextmanager
def trava():
    BASE.mkdir(parents=True, exist_ok=True)
    import msvcrt
    with (BASE/'execucao.lock').open('a+b') as f:
        if f.tell() == 0:
            f.write(b'0'); f.flush()
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def nome(al, lim):
    return f'hibrido_{al}_{int(lim)}'


def paginas(co, splits):
    if co != 'validacao_silver':
        yield from b.paginas(co, 'linhas')
        return
    for uf in splits['validacao']:
        pp = b.UNIDADES/'linhas'/(uf+'.jsonl')
        wp = pp.with_name(uf+'.palavras.jsonl')
        for p, obj in itertools.zip_longest(b.jsonl(pp), b.jsonl(wp)):
            exigir(p and obj and p['page_id'] == obj['page_id'], 'Shards RN divergentes')
            exigir(p['uf'] == uf and p['particao'] == 'validacao', 'Validacao fora de RN')
            exigir(obj['referencia_palavras_tipo'] == 'fluxo_pdf_por_palavra' and
                   obj['gt_w'] == list(range(len(obj['palavras']))), 'Referencia silver mudou')
            yield {**obj, 'uf': uf}, p


def medir(obj, p, ordem):
    # Funcao sem escritas: importa a mesma medir(), eventos() e expansao canonica.
    return c.medir(obj, p, ordem)


def iniciar(a):
    splits = ler(RAIZ/'data/processed/splits.json')
    paths = set(b.DEP_PATHS + [Path(__file__), Path(c.__file__), Path(rr.__file__),
        Path(inferencia.__file__), Path(texto.__file__), Path(t.__file__),
        Path(t.sucessor.__file__), CK, CK.parent/'treino.json',
        RAIZ/'data/processed/splits.json', e.JSON])
    paths.update(b.UNIDADES/'bancadas'/(co+'.jsonl') for co in COORTES if co.startswith('golden'))
    for uf in splits['validacao'] + splits['teste']:
        paths.update([b.UNIDADES/'linhas'/(uf+'.jsonl'),
                      b.UNIDADES/'linhas'/(uf+'.palavras.jsonl')])
    fontes = {str(p.relative_to(RAIZ)): sha(p) for p in sorted(paths)}
    info = ler(CK.parent/'treino.json')
    exigir(info['codificador'] == texto.VERSAO and
           info['config']['codificador_texto'] == texto.identidade_codificador(),
           'Checkpoint e codificador textual nao correspondem')
    coortes = {co: [p['page_id'] for obj,p in paginas(co, splits)] for co in COORTES}
    exigir(len(coortes['golden_v4']) == 44 and len(coortes['golden_v3_novo']) == 27,
           'Bancadas humanas incompletas')
    exigir(not set(coortes['golden_v4']) & set(coortes['golden_v3_novo']), 'Humanas sobrepostas')
    config = {'versao': VERSAO, 'device': 'cpu', 'threads': 4, 'num_workers': 0,
              'nivel_candidatos': NIVEL, 'alertas': ALERTAS, 'limiares': LIMIARES,
              'janela_max_deslocamento': JANELA, 'limite_fumaca': a.limite,
              'selecao': 'media dos deltas de quebras RN e v4 com peso igual; desempate tau e menos mudancas'}
    fp = digest([fontes, config])
    pasta = BASE/fp
    state = pasta/'estado.json'
    if state.exists():
        R = ler(state)
    else:
        R = {'fontes': fontes, 'config': config, 'fingerprint': fp, 'splits': splits,
             'coortes': coortes, 'treino': {k: info.get(k) for k in
             ('paginas_treino', 'paginas_visitadas', 'epocas_completas', 'melhor_val_tau_unidades')},
             'ancoras': {}, 'paginas': {}, 'completas': {}, 'selecao': None,
             'estado': 'Preparando as ancoras', 'concluido': False}
    R['pasta'] = str(pasta.relative_to(RAIZ))
    gravar(BASE/'ultima_execucao.json', {'estado': str(state.relative_to(RAIZ))})
    return R


def salvar(R):
    gravar(RAIZ/R['pasta']/'estado.json', R)
    relatorio(R)


def ancoras(R):
    if R['ancoras'].get('aprovada'):
        return
    historico = ler(e.JSON)
    antigos = {r['page_id']: {m: {k: r['metodos'][m][k] for k in ('tau','quebras','seq')}
        for m in ('P2','P1m')} for r in historico['paginas'] if r['coorte'] == 'v4'}
    del historico
    rows = []
    for obj,p in paginas('golden_v4', R['splits']):
        pid = p['page_id']
        cp = RAIZ/R['pasta']/'ancoras'/(e.ac.chave(pid)+'.json')
        if cp.exists():
            row = ler(cp)
        else:
            ordem,_ = b.prever(c.automatico(p),obj['palavras'],'regra_colunas')
            med,seq,q,_ = medir(obj,p,ordem)
            det = b.UNIDADES/'cache/detector'/(e.ac.chave(pid)+'.json')
            q['ls3'] = ler(det)['regioes']
            q['d'] = {'detector': {'regioes': []}}
            p2,its,diag = e.ls.prever(q,e.FIXA,'ls3')
            mp2 = e.medir(q,p2,its,diag,'P0')
            exigir(seq == p2 == antigos[pid]['P2']['seq'], 'Sequencia P2 diverge: '+pid)
            row = {'page_id':pid, 'regra':{k:med[k] for k in ('tau','quebras')},
                   'P2':{k:mp2[k] for k in ('tau','quebras')},
                   'P1m_historico':{k:antigos[pid]['P1m'][k] for k in ('tau','quebras')},
                   'detector_sha256':sha(det)}
            gravar(cp,row)
        rows.append(row)
        R['ancoras'] = {'aprovada':False,'paginas':rows}
        salvar(R)
        print(f'[ancora] {len(rows)}/44',flush=True)
    exigir(set(antigos) == {r['page_id'] for r in rows}, 'Coorte v4 mudou')
    medias = {m:{k:statistics.mean(r[m][k] for r in rows) for k in ('tau','quebras')}
              for m in ('regra','P2','P1m_historico')}
    R['ancoras']['medias'] = medias
    for m,tau,qb in (('regra',.985948,6.045455),('P2',.985948,6.045455),
                     ('P1m_historico',.952424,8.931818)):
        exigir(abs(medias[m]['tau']-tau) <= .006 and abs(medias[m]['quebras']-qb) <= .000001,
               f'Ancora {m} nao reproduzida: {medias[m]}')
    R['ancoras']['aprovada'] = True
    R['estado'] = 'Ancoras reproduzidas; pronto para scores e intervencoes'
    salvar(R)


def alertas(ctx):
    # Somente contexto automatico. Nenhum obj, rank humano ou referencia aqui.
    restritos = {a['a']:set(a['tipos']) for a in rr.detectar_alertas(ctx)}
    amplos = {}
    for a in ctx['ordem']:
        z = ctx['regra'][a]
        nomes = set(restritos.get(a,()))
        ua,uz = ctx['mapa'][a],ctx['mapa'].get(z)
        if a in ctx['pontes'] or z in ctx['pontes'] or (uz and c.obstaculos(ctx,ua,uz)):
            nomes.add('transversal')
        for uid in (a,z):
            if uid not in ctx['margem']:
                continue
            u = ctx['mapa'][uid]
            suporte = sum(v != uid and ctx['margem'].get(v) == ctx['margem'][uid]
                and abs(c.cy(ctx['mapa'][v])-c.cy(u)) <= 3*ctx['h']
                and c.sobreposicao(u,ctx['mapa'][v]) >= .6 for v in ctx['mapa'])
            corpo_contiguo = any(v not in ctx['margem'] and ctx['col'][v] == ctx['col'][uid]
                and abs(c.cy(ctx['mapa'][v])-c.cy(u)) <= 4*ctx['h']
                and c.sobreposicao(u,ctx['mapa'][v]) >= .6 for v in ctx['mapa'] if v != uid)
            if suporte < 2 or corpo_contiguo:
                nomes.add('margem_pouco_sustentada')
        if uz and ctx['col'][a] != ctx['col'][z]:
            disputa = any(v not in (a,z) and .25*ctx['h'] < c.cy(ctx['mapa'][v])-c.cy(ua) <= 4*ctx['h']
                          for v in ctx['grupos'].get(ctx['col'][a],()))
            if disputa:
                nomes.add('disputa_colunas')
        restritos[a] = nomes
        extras = set(nomes)
        if c.confianca_regra(ctx,a) < .95:
            extras.add('baixa_continuidade')
        if uz and ctx['col'][a] != ctx['col'][z]:
            extras.add('troca_coluna')
        if a in ctx['margem'] or z in ctx['margem']:
            extras.add('margem')
        amplos[a] = extras
    return {'estrito':{a:sorted(v) for a,v in restritos.items()},
            'amplo':{a:sorted(v) for a,v in amplos.items()}}


def carregar_modelo(R):
    import torch
    from transformers import LayoutLMConfig, LayoutLMModel
    torch.set_num_threads(4)
    memoria = t.memoria()
    exigir(memoria.get('ram_livre_mb',0) >= 1200 and memoria.get('commit_livre_mb',0) >= 1800,
           f'Memoria insuficiente para inferencia em fluxo: {memoria}')
    # Meta + mmap + assign evita carregar encoder pretreinado e checkpoint em duplicata.
    ck = torch.load(CK,map_location='cpu',weights_only=False,mmap=True)
    cfg = argparse.Namespace(**{**ck['config'],'device':'cpu'})
    exigir(cfg.modelo == 'sucessor' and cfg.representacao == 'linhas','Modelo errado')
    exigir(cfg.codificador_texto == texto.identidade_codificador(),'Codificador diverge')
    config = LayoutLMConfig.from_pretrained(str(texto.snapshot_local()),local_files_only=True)
    original = LayoutLMModel.__dict__.get('from_pretrained')
    LayoutLMModel.from_pretrained = staticmethod(lambda *args,**kwargs: LayoutLMModel(config))
    try:
        with torch.device('meta'):
            model = t.sucessor.LayoutLMSucessor(str(texto.snapshot_local()),usar_texto=True)
    finally:
        if original is None:
            del LayoutLMModel.from_pretrained
        else:
            LayoutLMModel.from_pretrained = original
    model.load_state_dict(ck['modelo'],strict=True,assign=True)
    # Buffer nao persistente: nao vem no state_dict e permanece meta. Indices
    # meta em embedding CPU podem produzir valores nao inicializados, sem erro.
    model.enc.embeddings.position_ids = torch.arange(
        config.max_position_embeddings,dtype=torch.long,device='cpu').expand(1,-1)
    exigir(not any(buf.is_meta for buf in model.buffers()),'Buffer meta restante')
    del ck
    model.eval().requires_grad_(False)
    cod = texto.ComTexto()
    R['modelo_memoria'] = {'antes':memoria,'depois':t.memoria(),'carregamento':'meta/mmap/assign'}
    return model,cod,cfg


def scores_pagina(model,cod,cfg,auto):
    """Logits e ordem com os mesmos lote, ComTexto e decoder da inferencia textual."""
    import torch
    with torch.inference_mode():
        p,grupos = t.preparar_pagina(auto,cfg)
        o = c.ordem_entrada(p)
        lote,N = t.sucessor.montar_lote(cod,[p],[o],None,'cpu')
        s,pos = model(lote['input_ids'],lote['bbox'],lote['attention_mask'],
                      lote['bloco_de'],lote['valido'],lote['geo'],N)
        logits = s[0].float().cpu().numpy().copy()
        lp = t.sucessor.log_probs(s)[0].cpu().numpy()
        posto = pos[0].float().cpu().numpy()
        cam = t.sucessor.decodificar_cadeias(lp,posto,N,cfg.limiar_cadeia)
        entrada = [p['bounding_boxes'][i]['id'] for i in o]
        ordem = [uid for j in cam for uid in grupos[entrada[j]]]
    return logits,posto,entrada,grupos,ordem


def escolhas(ctx,logits,entrada,grupos):
    dono = {uid:(j+1,k,len(grupos[g])) for j,g in enumerate(entrada)
            for k,uid in enumerate(grupos[g])}
    out,cands = {},{}
    for a in ctx['ordem']:
        cands[a] = c.candidatos(ctx,a,NIVEL)
        ia,ka,na = dono[a]
        vals = {}
        if ka == na-1:
            for z in cands[a]:
                if z is None:
                    vals[z] = float(logits[ia,0])
                else:
                    iz,kz,_ = dono[z]
                    if kz == 0 and iz != ia:
                        vals[z] = float(logits[ia,iz])
        regra = ctx['regra'][a]
        if regra not in vals or not math.isfinite(vals[regra]):
            out[a] = {'z':regra,'vantagem':None,'agrupada':True}
            continue
        elegiveis = [z for z in cands[a] if z in vals and math.isfinite(vals[z])]
        best = max(elegiveis,key=lambda z:vals[z])
        out[a] = {'z':best,'vantagem':vals[best]-vals[regra],
                  'score_modelo':vals[best],'score_regra':vals[regra],'agrupada':False}
    return out,cands


def intervir(regra,propostas,alerts,limiar):
    """Move uma unidade; preserva ordem relativa das outras e arestas ja aceitas."""
    rank = {a:i for i,a in enumerate(regra)}
    candidatos = [(a,v) for a,v in propostas.items() if alerts.get(a) and
        v['vantagem'] is not None and v['vantagem'] > limiar and
        v['z'] != (regra[rank[a]+1] if rank[a]+1 < len(regra) else None)]
    candidatos.sort(key=lambda x:(-x[1]['vantagem'],rank[x[0]]))
    ordem = list(regra)
    aceitas = {}
    log = []
    for a,v in candidatos:
        z = v['z']
        ia = ordem.index(a)
        iz = ordem.index(z) if z is not None else len(ordem)-1
        if abs(iz-ia) > JANELA:
            log.append({'a':a,'z':z,'vantagem':v['vantagem'],'estado':'fora_janela'})
            continue
        nova = list(ordem)
        if z is None:
            nova.remove(a); nova.append(a)
        else:
            nova.remove(z); nova.insert(nova.index(a)+1,z)
        suces = dict(zip(nova,nova[1:]+[None]))
        if any(suces[u] != dest for u,dest in aceitas.items()):
            log.append({'a':a,'z':z,'vantagem':v['vantagem'],'estado':'conflito'})
            continue
        exigir(len(nova) == len(regra) and set(nova) == set(regra),'Movimento perdeu unidade')
        ordem = nova
        aceitas[a] = z
        log.append({'a':a,'z':z,'vantagem':v['vantagem'],'estado':'aceita'})
    antigo = dict(zip(regra,regra[1:]+[None]))
    realizado = dict(zip(ordem,ordem[1:]+[None]))
    return ordem,{'propostas':len(candidatos),'aceitas':len(aceitas),
                  'alteradas':sum(antigo[a] != realizado[a] for a in regra),
                  'fontes':len(regra),'log':log}


def acertos_linhas(q,seq,trs,met):
    # Diagnostico de reparos; a metrica continua vindo de e.medir.
    ranks = {k:i for i,k in enumerate(seq)}
    intactas = {L['id']:all(ranks[z] == ranks[a]+1 for a,z in zip(L['ks'],L['ks'][1:]))
                for L in q['gold_lines']}
    hits = [bool(intactas[tr['linha_a']] and intactas[tr['linha_z']] and
                 ranks[tr['palavra_z']] == ranks[tr['palavra_a']]+1) for tr in trs]
    exigir(not trs or abs(sum(hits)/len(trs)-met['sucessor_linhas']) < 1e-12,
           'Decomposicao de reparos diverge da regua')
    return hits


def diagnosticar(ctx,trs,propostas,cands,alerts):
    d = collections.Counter()
    tipos = {tip:collections.Counter() for tip in c.TIPOS}
    for tr in trs:
        a,z = tr['a'],tr['z']
        coberta = tr['alcancavel'] and (tr['interno'] or z in cands[a])
        for cont in (d,tipos[tr['tipo']]):
            cont['total'] += 1; cont['cobertas'] += int(coberta)
            if tr['acerto']:
                continue
            cont['erros_regra'] += 1
            if not tr['alcancavel']:
                cont['estrutural'] += 1
            elif tr['interno']:
                cont['interno'] += 1
            elif z not in cands[a]:
                cont['candidato_ausente'] += 1
            elif propostas[a]['agrupada']:
                cont['score_indisponivel_agrupamento'] += 1
            else:
                best = propostas[a]['z']
                if best == z:
                    cont['modelo_correto'] += 1
                    for al in ALERTAS:
                        cont['correto_alerta_'+al] += int(bool(alerts[al][a]))
                elif best == ctx['regra'][a]:
                    cont['mesmo_erro_regra'] += 1
                else:
                    cont['outro_erro_modelo'] += 1
    return {'total':dict(d),'tipos':{k:dict(v) for k,v in tipos.items()}}


def processar(R,co,a,rede):
    feitos = R['paginas'].setdefault(co,{})
    externos = {}
    path = CK.parent/'pred_texto'/f'sucessor_linhas_texto_s42__linhas__{co}.jsonl'
    if path.exists():
        externos = {r['page_id']:r['ordem'] for r in b.jsonl(path)}
    for i,(obj,p) in enumerate(paginas(co,R['splits'])):
        if a.limite and i >= a.limite:
            break
        if time.monotonic() >= a.prazo:
            R['estado'] = 'Pausa por prazo; execute o mesmo comando para retomar'
            salvar(R); return False
        pid = p['page_id']
        if pid in feitos:
            continue
        inicio = time.perf_counter()
        ctx = c.contexto(c.automatico(p),obj['palavras'])
        als = alertas(ctx)
        fingerprint = digest([R['fontes'],c.automatico(p)])
        cp = BASE/'scores'/(fingerprint+'.npz')
        jp = cp.with_suffix('.json')
        if cp.exists() and jp.exists():
            import numpy as np
            meta = ler(jp)
            with np.load(cp,allow_pickle=False) as f:
                logits,posto = f['logits'],f['posto']
            entrada,grupos,ordem_modelo = meta['entrada'],meta['grupos'],meta['ordem']
            score_ms = meta['score_ms']
        else:
            if not rede:
                rede.extend(carregar_modelo(R))
            before = time.perf_counter()
            logits,posto,entrada,grupos,ordem_modelo = scores_pagina(*rede,ctx['auto'])
            score_ms = 1000*(time.perf_counter()-before)
            import numpy as np
            cp.parent.mkdir(parents=True,exist_ok=True)
            with cp.with_suffix('.tmp').open('wb') as f:
                np.savez_compressed(f,logits=logits,posto=posto)
                f.flush(); os.fsync(f.fileno())
            os.replace(cp.with_suffix('.tmp'),cp)
            gravar(jp,{'page_id':pid,'entrada':entrada,'grupos':grupos,'ordem':ordem_modelo,
                       'score_ms':score_ms,'fingerprint':fingerprint})
        exigir(pid not in externos or externos[pid] == ordem_modelo,
               'Decoder diverge da inferencia textual historica: '+pid)
        props,cands = escolhas(ctx,logits,entrada,grupos)
        # A avaliacao so comeca depois de alertas, candidatos e scores automaticos.
        base,_,trs,_ = c.preparar_avaliacao(obj,p,ctx)
        med_base,seq_base,q,exp = medir(obj,p,ctx['ordem'])
        exigir(base == med_base,'Reguas da base divergentes')
        hits_base = acertos_linhas(q,seq_base,trs,base)
        row = {'page_id':pid,'uf':obj['uf'],'visto_treino':obj['uf'] in R['splits']['treino'],
               'modelos':{},'diagnostico':diagnosticar(ctx,trs,props,cands,als),
               'alertas':{al:sum(bool(v) for v in als[al].values()) for al in ALERTAS},
               'alertas_por_fonte':als,'escolhas':props,'scores':str(cp.relative_to(RAIZ)),
               'modelo_confere_historico':pid in externos,'score_ms':score_ms}
        ordens = {'regra':(ctx['ordem'],{'alteradas':0,'fontes':len(ctx['ordem'])}),
                  'modelo':(ordem_modelo,{'alteradas':sum(ctx['regra'][uid] != z for uid,z in
                    zip(ordem_modelo,ordem_modelo[1:]+[None])),'fontes':len(ctx['ordem'])})}
        for al,lim in GRADE:
            ordens[nome(al,lim)] = intervir(ctx['ordem'],props,als[al],lim)
        cache = {tuple(ctx['ordem']):(base,seq_base,hits_base)}
        for met,(ordem,diag) in ordens.items():
            if tuple(ordem) not in cache:
                med,seq,_,_ = medir(obj,p,ordem)
                cache[tuple(ordem)] = med,seq,acertos_linhas(q,seq,trs,med)
            med,seq,hits = cache[tuple(ordem)]
            row['modelos'][met] = {'metricas':med,'ordem':ordem,'diag':diag,
                'reparos':sum(not x and y for x,y in zip(hits_base,hits)),
                'regressoes':sum(x and not y for x,y in zip(hits_base,hits))}
        row['tempo_ms'] = 1000*(time.perf_counter()-inicio)
        row['memoria'] = t.memoria()
        gravar(RAIZ/R['pasta']/'paginas'/co/(e.ac.chave(pid)+'.json'),row)
        feitos[pid] = {k:v for k,v in row.items() if k not in
                      ('alertas_por_fonte','escolhas','scores')}
        # O estado agrega so ordens curtas e metricas; palavras nunca ficam no corpus.
        for m in feitos[pid]['modelos'].values():
            m.pop('ordem',None)
            m['diag'] = {k:v for k,v in m['diag'].items() if k != 'log'}
        R['estado'] = f'Processando {co}: {len(feitos)}/{len(R["coortes"][co])}'
        salvar(R)
        print(f'[pagina] {co} {len(feitos)}/{len(R["coortes"][co])} '
              f'{row["tempo_ms"]:.0f} ms; regra={base["quebras"]}',flush=True)
        del ctx,obj,p,logits,posto,row,cache,exp,seq_base,q,trs
        gc.collect()
    R['completas'][co] = set(feitos) == set(R['coortes'][co])
    salvar(R)
    return True


def selecionar(R):
    if R['selecao']:
        return
    exigir(all(R['completas'].get(co) for co in COORTES[:2]),'Ajuste incompleto')
    exigir(not any(R['paginas'].get(co) for co in COORTES[2:]),'Holdout lido antes da selecao')
    aval = []
    for al,lim in GRADE:
        m = nome(al,lim)
        dqs,dts,mudancas = [],[],[]
        for co in COORTES[:2]:
            rows = list(R['paginas'][co].values())
            dqs.append(statistics.mean(r['modelos'][m]['metricas']['quebras']-
                                       r['modelos']['regra']['metricas']['quebras'] for r in rows))
            dts.append(statistics.mean(r['modelos'][m]['metricas']['tau']-
                                       r['modelos']['regra']['metricas']['tau'] for r in rows))
            mudancas.append(sum(r['modelos'][m]['diag']['alteradas'] for r in rows))
        aval.append({'metodo':m,'alerta':al,'limiar':lim,'objetivo':statistics.mean(dqs),
                     'delta_quebras_RN_v4':dqs,'delta_tau':statistics.mean(dts),
                     'mudancas':sum(mudancas)})
    melhor = min(aval,key=lambda x:(x['objetivo'],-x['delta_tau'],x['mudancas'],
                                  x['alerta'] != 'estrito',-x['limiar']))
    R['selecao'] = {'escolhida':melhor,'grade':aval,'ajuste':list(COORTES[:2]),
                    'holdouts_ainda_nao_avaliados':True}
    gravar(RAIZ/R['pasta']/'selecao.json',R['selecao'])
    salvar(R)
    print('[selecao] '+json.dumps(melhor,ensure_ascii=False),flush=True)


def resumo(rows,met,completo):
    W = b.PESOS_CLUSTER(rows) if completo else None
    ms,ds = {},{}
    for k in METRICAS:
        v = [r['modelos'][met]['metricas'][k] for r in rows]
        vv = [x for x in v if x is not None]
        ms[k] = e.media_ic(v,W) if completo else {'media':statistics.mean(vv) if vv else None,
                                                'ic':[None,None],'n':len(vv)}
        pareadas = [r for r in rows if r['modelos'][met]['metricas'][k] is not None and
                    r['modelos']['regra']['metricas'][k] is not None]
        delta = [r['modelos'][met]['metricas'][k]-r['modelos']['regra']['metricas'][k] for r in pareadas]
        if completo and delta:
            ufs = sorted({r['uf'] for r in pareadas})
            dvs = [statistics.mean(x for r,x in zip(pareadas,delta) if r['uf'] == uf) for uf in ufs]
            ds[k] = {**e.media_ic(delta,b.PESOS_CLUSTER(pareadas)),
                     'p':e.pratt(dvs)['p'],'por_veiculo':dict(zip(ufs,dvs))}
    fontes = sum(r['modelos'][met]['diag']['fontes'] for r in rows)
    alteradas = sum(r['modelos'][met]['diag']['alteradas'] for r in rows)
    return {'n':len(rows),'veiculos':len({r['uf'] for r in rows}),'metricas':ms,'deltas':ds,
            'alteradas':alteradas,'fracao':alteradas/fontes if fontes else 0.,
            'reparos':sum(r['modelos'][met]['reparos'] for r in rows),
            'regressoes':sum(r['modelos'][met]['regressoes'] for r in rows)}


def f(x,n=3):
    return '—' if x is None else f'{x:.{n}f}'.replace('.',',')


def cel(v,n=3,pct=False):
    mul = 100 if pct else 1
    s = f(v['media']*mul if v['media'] is not None else None,n)
    if v.get('ic',[None])[0] is not None:
        s += f' [{f(v["ic"][0]*mul,n)}; {f(v["ic"][1]*mul,n)}]'
    return s+('%' if pct else '')


def relatorio(R):
    escolhido = R.get('selecao',{}).get('escolhida',{}).get('metodo') if R.get('selecao') else None
    cab = ['# Regra + LayoutLM textual: intervenção seletiva','']
    if R.get('concluido'):
        rs = {co:list(R['paginas'][co].values()) for co in COORTES}
        d = {co:statistics.mean(r['modelos'][escolhido]['metricas']['quebras']-
             r['modelos']['regra']['metricas']['quebras'] for r in rows) for co,rows in rs.items()}
        cab += [f'1. Escolha congelada em RN e golden_v4: `{escolhido}` (vantagem em logits).',
                f'2. golden_v4 (ajuste): Δ híbrido−regra {f(d["golden_v4"],2)} quebras/página.',
                f'3. golden_v3 novo: Δ {f(d["golden_v3_novo"],2)} quebras/página.',
                f'4. Teste silver CE/MA/RJ: Δ {f(d["teste_silver"],2)} quebras/página.',
                '5. '+('Há ganho médio nos dois conjuntos fora do ajuste; verificar IC e τ abaixo.'
                     if all(d[co] < 0 for co in COORTES[2:]) else
                     'O híbrido selecionado não melhora consistentemente fora do ajuste; conservar a regra.')]
    else:
        cab += [f'1. Estado: {R["estado"]}.',
                f'2. Âncoras: {"reproduzidas" if R["ancoras"].get("aprovada") else "em verificação; sem comparação nova"}.',
                f'3. Escolha: {escolhido or "pendente de completar RN e golden_v4"}.',
                '4. Resultados parciais não sustentam conclusão sobre o híbrido.',
                '5. Retomada por página e scores persistidos; não há treino nesta execução.']
    ls = cab+['','Relatório gerado exclusivamente pelo script e seus caches de execução.',
        '',f'Estado: `{R["pasta"]}/estado.json`. CPU, quatro threads, uma página por vez; pesos locais, sem rede.',
        '', '## Controles e protocolo','',
        'Regra `regra_colunas`, representação em linhas, átomos ls3 congelados. Entrada pela função original '
        '`ordem_entrada` (`random.Random(f"entrada-{page_id}")`). Expansão canônica `ordem_sem_bbox.fluxo()` '
        'e régua `erros_ponta_a_ponta.medir`; nenhum cálculo de eficácia foi substituído.',
        '', 'P2 e regra reexecutados por página contra as sequências históricas. P1m é controle histórico '
        'do pipeline extrator + XY-cut + margens; não foi reextraído. Aborta antes de números novos se τ '
        'divergir mais de 0,006 ou a média de quebras não reproduzir seis casas.',
        '', '| Controle v4 | τ palavras | Quebras/página |','|---|---:|---:|']
    for k,v in R['ancoras'].get('medias',{}).items():
        ls.append(f'| {k} | {f(v["tau"],6)} | {f(v["quebras"],6)} |')
    ls += ['', '## Intervenção e escolha','',
        'Candidatos importados de `corretor_de_transicoes.candidatos`, nível 3 já estabelecido no experimento '
        'anterior. A escolha deste nível naquele trabalho consultou as duas bancadas humanas: golden_v3 '
        'é externo ao ajuste atual, mas não ao desenvolvimento histórico dos candidatos.',
        '', 'Alerta estrito: salto/retorno/alinhamento/objeto da tarefa 08, elemento transversal, disputa '
        'entre colunas com linha próxima ainda abaixo e margem com menos de duas vizinhas alinhadas '
        'ou continuidade próxima de corpo. Amplo acrescenta continuidade geométrica baixa, toda troca '
        'de coluna e toda fronteira de margem. Margem e suporte são proxies automáticos; nenhum rótulo '
        'humano entra no alerta.',
        '', 'O candidato de maior logit só substitui o sucessor original com alerta, discordância e '
        'vantagem estritamente maior que 0, 1 ou 3. Diferença de logits equivale à diferença de '
        'log-probabilidades na mesma fonte; não é confiança calibrada. Move uma unidade para após a '
        'fonte (ou a fonte ao fim para FIN), no máximo 12 posições na ordem corrente. Preserva cobertura, '
        'unicidade, ordem relativa das demais e todas as propostas previamente aceitas. A remoção e '
        'inserção podem mudar outras duas fronteiras: medimos todas as mudanças realizadas.',
        '', 'Seleção minimiza a média, com peso igual para RN e v4, do Δ de quebras por página. Desempate: '
        'maior Δτ, menos mudanças, alerta estrito e maior limiar. A escolha é gravada antes da avaliação '
        'dos dois conjuntos externos. Sem otimização no golden_v3 novo ou no teste.',
        '', 'Logits saem do mesmo encoder, ComTexto, lote e decoder em cadeias da inferência textual. '
        'Carregamento meta/mmap/assign evita duas cópias dos pesos. Em páginas agrupadas, só a última '
        'linha de uma faixa e a primeira da outra têm score de fronteira; arestas internas sem score '
        'ficam protegidas. O modelo sozinho conserva a expansão original das faixas.',
        '', f'Treino do checkpoint (somente lido): {R["treino"].get("paginas_treino")} páginas, '
        f'{R["treino"].get("epocas_completas")} épocas; veículos vistos = os sete do split de treino. '
        'Não houve novo treino. A inferência do modelo sozinho é conferida contra os JSONLs históricos '
        'onde disponíveis; RN é inferida agora.',
        '', '## Resultados por bancada','',
        'Médias macro por página [IC 95% agrupado por veículo]. Δ = método−regra; menor quebra é melhor. '
        'Wilcoxon bilateral Pratt nas diferenças médias de cada veículo, p exploratório sem ajuste '
        'por múltiplas comparações. IC não é calculado durante uma bancada incompleta.',
        '', '| Bancada / grupo | Método | n / veículos | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |',
        '|---|---|---:|---:|---:|---:|---:|']
    contrastes = []
    for co in COORTES:
        rows = list(R['paginas'].get(co,{}).values())
        if not rows:
            continue
        grupos = [('todos',rows)]
        if co.startswith('golden'):
            grupos += [('vistos',[r for r in rows if r['visto_treino']]),
                       ('não vistos',[r for r in rows if not r['visto_treino']])]
        for g,rs in grupos:
            if not rs:
                ls.append(f'| {co} / {g} | sem páginas | 0 / 0 | — | — | — | — |')
                continue
            for m in ['regra','modelo']+([escolhido] if escolhido else []):
                s = resumo(rs,m,R['completas'].get(co,False))
                ls.append(f'| {co} / {g} | {m} | {s["n"]} / {s["veiculos"]} | '
                    + ' | '.join(cel(s['metricas'][k],2 if k != 'tau' else 6,
                                  k in ('fid12','sucessor_linhas')) for k in METRICAS)+' |')
                if m != 'regra' and s['deltas']:
                    contrastes.append((co,g,m,s))
    ls += ['', '| Bancada / grupo | Método | Δ quebras [IC veículo] | p veículo | Δ τ [IC veículo] | p veículo | Reparos / regressões de sucessores de linhas |',
           '|---|---|---:|---:|---:|---:|---:|']
    for co,g,m,s in contrastes:
        dq,dt = s['deltas']['quebras'],s['deltas']['tau']
        ls.append(f'| {co} / {g} | {m} | {cel(dq,2)} | {f(dq["p"],6)} | '
                  f'{cel(dt,6)} | {f(dt["p"],6)} | {s["reparos"]} / {s["regressoes"]} |')
    if R['selecao']:
        ls += ['',f'**Escolha congelada: `{escolhido}`**. Objetivo '
               f'{f(R["selecao"]["escolhida"]["objetivo"],6)} Δ quebras; seleção em `selecao.json`.']
    ls += ['', '## Curva de intervenção (as seis configurações)','',
        'A fração inclui o sucessor FIN de cada página: fontes cujo sucessor final mudou / número de unidades. '
        'Reparos/regressões usam as linhas-ouro inteiras intactas e são conferidos contra a métrica oficial. '
        'A grade fora do ajuste é diagnóstico, não autoriza trocar a escolha congelada.',
        '', '| Bancada | Configuração | Transições alteradas | Fração | Quebras/página | Δ quebras | τ | Reparos | Regressões |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for co in COORTES:
        rows = list(R['paginas'].get(co,{}).values())
        if not rows:
            continue
        qb = statistics.mean(r['modelos']['regra']['metricas']['quebras'] for r in rows)
        for al,lim in GRADE:
            m = nome(al,lim)
            s = resumo(rows,m,False)
            mq = s['metricas']['quebras']['media']
            ls.append(f'| {co} | {m} | {s["alteradas"]} | {f(100*s["fracao"],2)}% | '
                      f'{f(mq,2)} | {f(mq-qb,2)} | {f(s["metricas"]["tau"]["media"],6)} | '
                      f'{s["reparos"]} | {s["regressoes"]} |')
    ls += ['', '## Por que o modelo consegue ou não corrigir','',
        'Diagnóstico apenas das transições de linhas que a regra perdeu. Categorias abaixo são exclusivas: '
        'falha estrutural, transição interna, candidato ausente, score de faixa indisponível; depois, melhor candidato correto, '
        'o mesmo sucessor errado da regra, ou outro sucessor errado. Fronteira correta não garante '
        'linha inteira intacta. O recall total inclui transições internas preservadas.',
        '', '| Bancada | Recall candidatos | Erros regra | Estrutural | Interna | Ausente | Sem score | Modelo correto | Mesmo erro | Outro erro | Correto + alerta estrito / amplo |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for co in COORTES:
        rows = list(R['paginas'].get(co,{}).values())
        if not rows:
            continue
        d = collections.Counter()
        for r in rows:
            d.update(r['diagnostico']['total'])
        recall = d['cobertas']/d['total'] if d['total'] else 0
        ls.append(f'| {co} | {f(100*recall,2)}% | {d["erros_regra"]} | {d["estrutural"]} | '
                  f'{d["interno"]} | {d["candidato_ausente"]} | {d["score_indisponivel_agrupamento"]} | '
                  f'{d["modelo_correto"]} | {d["mesmo_erro_regra"]} | {d["outro_erro_modelo"]} | '
                  f'{d["correto_alerta_estrito"]} / {d["correto_alerta_amplo"]} |')
        if co == 'teste_silver' and R['completas'].get(co) and recall < .95:
            teto = (d['total']-d['estrutural'])/d['total']
            ls += ['', f'No teste silver, recall total {f(100*recall,2)}%: a meta de 95% '
                   'foi atingida no ajuste, mas não se transfere a esta referência automática. '
                   f'Mesmo todos os candidatos têm teto de cobertura de fronteiras '
                   f'{f(100*teto,2)}%, dadas {d["estrutural"]} fronteiras estruturalmente '
                   'inalcançáveis. Não ampliamos candidatos usando o teste. Parte dessa limitação '
                   'vem da discordância entre a expansão canônica e o fluxo silver dentro das '
                   'unidades; a comparação usa a mesma representação para os três métodos.', '']
    if R.get('complemento'):
        ls += ['', 'Diagnóstico das propostas da configuração escolhida: uma fronteira alcançável '
            'entre unidades identifica o alvo-ouro da fonte. FIN e fontes sem alvo único ficam como '
            'não avaliáveis. Os contadores abaixo olham a aresta proposta; reparos/regressões da '
            'régua acima incluem também os efeitos da remoção e inserção nas outras fronteiras.',
            '', '| Bancada | Propostas | Aceitas | Fora da janela | Conflito | Aceitas: regra errada → alvo certo | Aceitas: regra certa → alvo errado | Aceitas: ambos errados | Não avaliáveis | Regressões: fonte intervinda / outras |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for co,di in R['complemento'].items():
            ls.append(f'| {co} | '+ ' | '.join(str(di.get(k,0)) for k in
                ('propostas','aceitas','fora_janela','conflito','reparo_proposto',
                 'regressao_proposta','ambos_errados','nao_avaliavel'))+
                 f' | {di.get("perdas_fonte_intervinda",0)} / {di.get("perdas_outras_fontes",0)} |')
        ls += ['', 'O recall global alto inclui muitas transições fáceis já corretas. A coluna '
            '“Ausente” mostra quanto ele cai justamente nos erros da regra. “Mesmo erro” mede quando '
            'o modelo conserva o sucessor errado; a tabela de propostas mostra também quando um '
            'logit alto derruba uma decisão correta. Alertas geométricos e vantagem de score não '
            'garantem saldo positivo, e os movimentos têm efeitos nas fronteiras vizinhas. '
            '“Outras” conta sucessores de linhas perdidos cuja unidade de origem não teve proposta '
            'aceita. O critério compara somente o logit da aresta da fonte, sem garantir preservação '
            'das demais fronteiras; esse efeito é medido na saída, não vetado pelo ouro.']
    if R.get('concluido'):
        positivos = []
        for al,lim in GRADE:
            m = nome(al,lim)
            if all(statistics.mean(r['modelos'][m]['metricas']['quebras']-
                   r['modelos']['regra']['metricas']['quebras'] for r in R['paginas'][co].values()) < 0
                   for co in COORTES[2:]):
                positivos.append(m)
        ls += ['', ('Nenhuma das seis configurações reduz as quebras médias nos dois conjuntos fora do ajuste. '
                    'Nesta grade, o modelo ainda não serve como corretor seletivo consistente.' if not positivos else
                    'Configurações com Δ médio negativo nos dois conjuntos externos (análise exploratória): '
                    + ', '.join('`'+m+'`' for m in positivos)+'. A seleção permanece congelada.')]
    ls += ['', '## Cobertura, limitações e reprodução','',
        'golden_v4 participou do desenvolvimento da regra e do ajuste desta grade. golden_v3 novo tem '
        'poucas páginas e candidatos já avaliados historicamente nele; não é validação humana totalmente '
        'intocada. Referência humana é ordem de regiões expandida em palavras. Silver é fluxo automático '
        'do PDF e inclui divergências dentro das tabelas, comuns aos três métodos; as quebras absolutas '
        'não medem apenas o ordenador. Sem nova semente de treino ou recalibração dos logits.',
        '', f'Bootstrap: {b.NBOOT} reamostras de veículos, semente {b.SEMENTE}, mesma função isolada da bancada. '
        'RN tem somente um veículo: seu IC agrupado é degenerado e seu Wilcoxon não permite generalização.',
        '', '| Bancada | Páginas previstas | Medidas | Completa |','|---|---:|---:|---|']
    for co in COORTES:
        ls.append(f'| {co} | {len(R["coortes"][co])} | {len(R["paginas"].get(co,{}))} | '
                  f'{"sim" if R["completas"].get(co) else "não"} |')
    humanos = set(R['coortes']['golden_v4']+R['coortes']['golden_v3_novo'])
    ls += ['', f'Sobreposição de páginas humanas com RN: {len(humanos & set(R["coortes"]["validacao_silver"]))}; '
           f'com teste silver: {len(humanos & set(R["coortes"]["teste_silver"]))}. '
           'São bancadas separadas, não somar como observações independentes. Nenhuma página é treinada aqui.',
           '', 'Comando completo: `venv/Scripts/python.exe -B orquestracao/analises/regra_mais_modelo.py`. '
           'Repetir retoma caches por hash das fontes; `--conferir` audita sem carregar a rede. '
           'Não altera `data/`, `docs/`, o quadro ou os módulos importados. Não usa detector ao vivo, GPU ou Data Policy.',
           '', f'Último estado: {R["estado"]}.']
    if R.get('auditoria'):
        ls += ['', f'Auditoria executada: {R["auditoria"]["paginas"]} páginas e '
               f'{R["auditoria"]["ordens"]} ordens com unicidade/cobertura, limiar, alertas '
               'e propostas aceitas conferidos.']
    medidas = [r for rows in R['paginas'].values() for r in rows.values()]
    if medidas:
        ls += ['', f'Inferências com histórico idêntico: '
               f'{sum(r["modelo_confere_historico"] for r in medidas)} páginas. '
               f'Tempo mediano dos scores novos/cacheados: {f(statistics.median(r["score_ms"] for r in medidas),1)} ms; '
               f'RAM livre mínima observada entre páginas: '
               f'{f(min(r["memoria"]["ram_livre_mb"] for r in medidas),1)} MB. '
               'Esta amostragem não mede pico instantâneo de RAM.']
    if R.get('erro'):
        ls += ['', 'Falha registrada: `'+R['erro']+'`.']
    gravar(MD,'\n'.join(ls)+'\n')


def conferir(R):
    exigir(R['ancoras'].get('aprovada'),'Ancoras pendentes')
    cont = collections.Counter()
    for co,rows in R['paginas'].items():
        for pid,row in rows.items():
            full = ler(RAIZ/R['pasta']/'paginas'/co/(e.ac.chave(pid)+'.json'))
            ids = set(full['modelos']['regra']['ordem'])
            base = dict(zip(full['modelos']['regra']['ordem'],full['modelos']['regra']['ordem'][1:]+[None]))
            for m,v in full['modelos'].items():
                ordem = v['ordem']
                exigir(len(ordem) == len(ids) and set(ordem) == ids,'Cobertura invalida no cache')
                succ = dict(zip(ordem,ordem[1:]+[None]))
                exigir(v['diag']['alteradas'] == sum(base[a] != succ[a] for a in ids),'Alteradas divergem')
                exigir(v['metricas'] == row['modelos'][m]['metricas'],'Resumo diverge do cache')
                exigir(v['reparos'] == row['modelos'][m]['reparos'] and
                       v['regressoes'] == row['modelos'][m]['regressoes'],'Reparos divergentes')
                if m.startswith('hibrido'):
                    _,al,lim = m.split('_')
                    for prop in v['diag']['log']:
                        exigir(full['alertas_por_fonte'][al][prop['a']] and
                               prop['vantagem'] > float(lim) and prop['z'] != base[prop['a']],
                               'Intervencao sem alerta/discordancia/vantagem')
                        if prop['estado'] == 'aceita':
                            exigir(succ[prop['a']] == prop['z'],'Proposta aceita nao sobreviveu')
                cont['ordens'] += 1
            cont['paginas'] += 1
    if R['selecao']:
        exigir(ler(RAIZ/R['pasta']/'selecao.json') == R['selecao'],'Selecao alterada')
        exigir(R['selecao']['ajuste'] == list(COORTES[:2]) and
               R['selecao']['holdouts_ainda_nao_avaliados'],'Selecao usou holdout')
    R['auditoria'] = dict(cont)
    if R.get('concluido'):
        complementar(R)
    print('[conferido] '+json.dumps(dict(cont)),flush=True)
    salvar(R)


def complementar(R):
    """Explica propostas congeladas; nao altera grade, escolha ou metricas."""
    escolhido = R['selecao']['escolhida']['metodo']
    out = {}
    for co in COORTES:
        soma = collections.Counter()
        for obj,p in paginas(co,R['splits']):
            ctx = c.contexto(c.automatico(p),obj['palavras'])
            _,_,trs,_ = c.preparar_avaliacao(obj,p,ctx)
            esperado = collections.defaultdict(set)
            for tr in trs:
                if tr['alcancavel'] and not tr['interno']:
                    esperado[tr['a']].add(tr['z'])
            row = ler(RAIZ/R['pasta']/'paginas'/co/(e.ac.chave(p['page_id'])+'.json'))
            exigir(row['modelos']['regra']['ordem'] == ctx['ordem'],'Base da auditoria mudou')
            aceitas = {prop['a'] for prop in row['modelos'][escolhido]['diag']['log']
                       if prop['estado'] == 'aceita'}
            seq = [k for uid in row['modelos'][escolhido]['ordem'] for k in ctx['exp'][uid]]
            hits = acertos_linhas(b.referencia(obj,p),seq,trs,row['modelos'][escolhido]['metricas'])
            perdas = [tr for tr,hit in zip(trs,hits) if tr['acerto'] and not hit]
            exigir(len(perdas) == row['modelos'][escolhido]['regressoes'],
                   'Perdas da auditoria divergentes')
            soma['perdas_fonte_intervinda'] += sum(tr['a'] in aceitas for tr in perdas)
            soma['perdas_outras_fontes'] += sum(tr['a'] not in aceitas for tr in perdas)
            for prop in row['modelos'][escolhido]['diag']['log']:
                soma['propostas'] += 1
                if prop['estado'] != 'aceita':
                    soma[prop['estado']] += 1
                    continue
                soma['aceitas'] += 1
                alvos = esperado[prop['a']]
                if len(alvos) != 1:
                    soma['nao_avaliavel'] += 1
                    continue
                z = next(iter(alvos))
                if prop['z'] == z:
                    soma['reparo_proposto'] += 1
                elif ctx['regra'][prop['a']] == z:
                    soma['regressao_proposta'] += 1
                else:
                    soma['ambos_errados'] += 1
            del obj,p,ctx,row,trs
        exigir(soma['propostas'] == soma['aceitas']+soma['fora_janela']+soma['conflito'],
               'Estados de proposta nao particionados')
        exigir(soma['aceitas'] == sum(soma[k] for k in
               ('reparo_proposto','regressao_proposta','ambos_errados','nao_avaliavel')),
               'Diagnostico de propostas nao particionado')
        out[co] = dict(soma)
        print(f'[diagnostico] {co}: {dict(soma)}',flush=True)
    R['complemento'] = out
    R['auditoria_codigo_sha256'] = sha(__file__)


def autoteste():
    regra = ['a','b','c','d']
    prop = {a:{'z':z,'vantagem':2.} for a,z in [('a','c'),('b','d')]}
    ord0,_ = intervir(regra,prop,{},0.)
    exigir(ord0 == regra,'Sem alerta mudou regra')
    ord1,diag = intervir(regra,prop,{'a':['salto'],'b':['retorno']},1.)
    exigir(len(ord1) == 4 and set(ord1) == set(regra) and diag['aceitas'] > 0,'Movimento invalido')
    ord2,_ = intervir(regra,prop,{'a':['salto']},3.)
    exigir(ord2 == regra,'Limiar alto mudou regra')
    print('[autoteste] alertas, limiar e cobertura OK',flush=True)


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--limite',type=int,default=0)
    ap.add_argument('--max-minutos',type=float,default=120.)
    ap.add_argument('--somente-ancoras',action='store_true')
    ap.add_argument('--relatorio',action='store_true')
    ap.add_argument('--conferir',action='store_true')
    a = ap.parse_args()
    exigir(a.limite >= 0 and a.max_minutos > 0,'Limite ou prazo invalido')
    with trava():
        if a.relatorio or a.conferir:
            R = ler(RAIZ/ler(BASE/'ultima_execucao.json')['estado'])
            conferir(R) if a.conferir else relatorio(R)
            return
        autoteste()
        R = iniciar(a)
        salvar(R)
        rede = []
        a.prazo = time.monotonic()+60*a.max_minutos
        try:
            ancoras(R)
            if a.somente_ancoras:
                return
            for co in COORTES:
                if co == COORTES[2] and not a.limite:
                    selecionar(R)
                if not processar(R,co,a,rede):
                    return
            if not a.limite:
                R['concluido'] = all(R['completas'].values())
                R['estado'] = 'Experimento completo; escolha congelada e tres bancadas avaliadas'
            else:
                R['estado'] = 'Fumaca concluida; sem selecao nem conclusao de eficacia'
            conferir(R)
        except Exception as ex:
            R['estado'] = 'Execucao interrompida; caches preservados'
            R['erro'] = str(ex)
            salvar(R)
            traceback.print_exc()
            raise
        finally:
            rede.clear(); gc.collect()


if __name__ == '__main__':
    main()
