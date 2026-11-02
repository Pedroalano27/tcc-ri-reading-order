"""
Mede paridade de palavras, blocos e ordens entre pdfplumber e PyMuPDF (T14).

Usa exatamente a bancada de avaliar_segmentacao.py e mais 60 paginas distintas,
balanceadas por veiculo com semente fixa. Segmenta com as MESMAS tabelas do cache
de layout existente; nunca gera layout nem escreve em data/. Mede abertura,
acesso a pagina, palavras e segmentacao; analise e IO do cache ficam fora.

Salva cada caminho de cada pagina atomicamente para retomar apos interrupcao.
O relatorio e reescrito a cada pagina concluida, sempre a partir dos resultados.
--do-zero cria uma execucao nova sem apagar nem reutilizar resultados de paginas.
Tambem executa unittest em CPU e guarda a saida completa no cache. Nao usa rede.

Uso, da raiz:
    venv/Scripts/python.exe -B orquestracao/analises/extrator_pymupdf_paridade.py
    venv/Scripts/python.exe -B orquestracao/analises/extrator_pymupdf_paridade.py --do-zero
    venv/Scripts/python.exe -B orquestracao/analises/extrator_pymupdf_paridade.py --limite 4
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.dont_write_bytecode = True
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pdfplumber
import pymupdf
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from scipy.stats import kendalltau

from src.data import avaliar_segmentacao as bancada
from src.data import extrator, layout
from src.data.palavras_pymupdf import palavras_da_pagina_pymupdf, _matriz_pdfplumber

CACHE = RAIZ / 'resultados' / 'extrator_pymupdf_cache'
RELATORIO = RAIZ / 'resultados' / 'extrator_pymupdf_paridade.md'
SEED = 20261003
SCHEMA = 1
MODULO = RAIZ / 'src' / 'data' / 'palavras_pymupdf.py'


def gravar_json(path, valor):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(valor, f, ensure_ascii=False, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def hash_json(valor):
    return hashlib.sha256(json.dumps(valor, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def assinatura_codigo(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def amostra():
    """Replica o main da bancada; as extras nao repetem nenhuma dessas paginas."""
    v1 = bancada.ler_colecao(bancada.DIR_V1)
    atual = bancada.ler_colecao(bancada.DIR_B)
    with open(bancada.ARQ_SPLITS, encoding='utf-8') as f:
        splits = json.load(f)
    veiculos = set(splits['teste'] + splits['ufs_nao_confiaveis'])
    fixas = {p['page_id']: p for p in bancada.amostra_balanceada(v1, veiculos, 40, 42)}
    for uf, arq, num, _ in bancada.PROBLEMAS:
        pid = bancada.id_pagina(uf, arq, num)
        fixas[pid] = v1.get(pid) or atual.get(pid) or {
            'page_id': pid, 'uf': uf, 'arquivo': arq, 'pagina': num}
    if len(fixas) != 44:
        raise RuntimeError(f'Bancada alterada: esperadas 44 paginas, obtidas {len(fixas)}.')
    pool = {pid: p for pid, p in atual.items() if pid not in fixas}
    extras = bancada.amostra_balanceada(pool, {p['uf'] for p in pool.values()}, 60, SEED)
    if len(extras) != 60:
        raise RuntimeError('Catalogo insuficiente para as 60 paginas extras distintas.')
    saida = []
    for grupo, paginas in (('bancada44', fixas.values()), ('extras60', extras)):
        for p in sorted(paginas, key=lambda p: p['page_id']):
            saida.append({**{k: p[k] for k in ('page_id', 'uf', 'arquivo', 'pagina')}, 'grupo': grupo})
    assert len({p['page_id'] for p in saida}) == 104
    return saida


def resolver_pdf(path, run_dir):
    """Envelopes PKCS7: recorta bytes para resultados/, nunca altera o original."""
    with path.open('rb') as f:
        inicio = f.read(1024)
        if inicio.startswith(b'%PDF'):
            return path, False
        f.seek(0)
        dados = f.read()
    a, b = dados.find(b'%PDF'), dados.rfind(b'%%EOF')
    if a < 0 or b < a:
        raise ValueError(f'Arquivo sem trecho PDF completo: {path}')
    destino = run_dir / ('envelope_' + hashlib.sha256(str(path).encode()).hexdigest()[:16] + '.pdf')
    if not destino.exists():
        destino.write_bytes(dados[a:b + len(b'%%EOF')])
    return destino, True


def iou(a, b):
    inter = max(0, min(a['x1'], b['x1']) - max(a['x0'], b['x0'])) * max(
        0, min(a['bottom'], b['bottom']) - max(a['top'], b['top']))
    aa = max(0, a['x1'] - a['x0']) * max(0, a['bottom'] - a['top'])
    ab = max(0, b['x1'] - b['x0']) * max(0, b['bottom'] - b['top'])
    return inter / (aa + ab - inter) if aa + ab > inter else 0.0


def casar(a, b, texto='t', limiar=0.7):
    """Correspondencia injetiva de cardinalidade maxima, com texto EXATO e IoU."""
    if not a or not b:
        return []
    indice = defaultdict(list)
    for j, v in enumerate(b):
        indice[v[texto]].append(j)
    rows, cols = [], []
    for i, v in enumerate(a):
        candidatos = [(iou(v, b[j]), j) for j in indice.get(v[texto], [])
                      if min(v['bottom'], b[j]['bottom']) > max(v['top'], b[j]['top'])]
        for ov, j in sorted(candidatos, reverse=True):
            if ov >= limiar:
                rows.append(i)
                cols.append(j)
    if not rows:
        return []
    grafo = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(a), len(b)))
    pares = maximum_bipartite_matching(grafo, perm_type='column')
    return [(i, int(j)) for i, j in enumerate(pares) if j >= 0]


def tau_ordens(a, b):
    """Nao transforma amostra de zero/um elemento em concordancia perfeita."""
    if len(a) < 2:
        return None
    assert len(a) == len(b) and set(a) == set(b)
    pos = {v: i for i, v in enumerate(b)}
    return float(kendalltau(range(len(a)), [pos[v] for v in a]).statistic)


def ordens(blocos):
    ids = list(range(len(blocos)))
    return {'stream': sorted(ids, key=lambda i: blocos[i]['s']),
            'naive': sorted(ids, key=lambda i: (blocos[i]['top'], blocos[i]['x0'])),
            'xycut': extrator.xycut(ids, blocos) if ids else []}


def comparar_blocos(a, b):
    pares = casar(a, b, 'texto', 0.95)
    mapa = {j: i for i, j in pares}
    comuns = set(mapa.values())
    oa, ob = ordens(a), ordens(b)
    taus, exatas = {}, {}
    for nome in oa:
        x = [i for i in oa[nome] if i in comuns]
        y = [mapa[j] for j in ob[nome] if j in mapa]
        taus[nome] = tau_ordens(x, y)
        exatas[nome] = x == y if len(x) >= 2 else None
    total = len(a) == len(b) == len(pares)
    return {'n_a': len(a), 'n_b': len(b), 'identicos': len(pares), 'mesma': total,
            'tau': taus, 'ordem_comum_igual': exatas,
            'ordem_total_igual': {k: total and bool(exatas[k]) for k in exatas}}


def compactar_blocos(blocos, ws):
    indices = {id(w): i for i, w in enumerate(ws)}
    return [{**{k: b[k] for k in ('texto', 'x0', 'x1', 'top', 'bottom', 's')},
             'tabela': bool(b.get('tabela')),
             'palavras': [indices[id(w)] for l in b['linhas'] for w in l['ws']]}
            for b in blocos]


def palavras_words(page):
    """Diagnostico do words sort=False, sem a reconstrucao de altura/tokens."""
    matriz = _matriz_pdfplumber(page)
    saida = []
    for s, w in enumerate(page.get_text('words', sort=False, clip=pymupdf.INFINITE_RECT())):
        c = pymupdf.Rect(w[:4]) * matriz
        saida.append({'t': w[4].strip(), 'x0': float(c.x0), 'x1': float(c.x1),
                      'top': float(c.y0), 'bottom': float(c.y1), 's': s})
    return extrator._juntar_letras_espacadas(saida)


def medir_caminho(item, tab, path, nome, cache_path, signature):
    if cache_path.exists():
        try:
            with cache_path.open(encoding='utf-8') as f:
                antigo = json.load(f)
            if antigo.get('signature') == signature and antigo.get('status') == 'ok':
                return antigo, True
        except (ValueError, OSError):
            pass
    t0 = time.perf_counter()
    try:
        abrir = pdfplumber.open if nome == 'pdfplumber' else pymupdf.open
        with abrir(str(path)) as doc:
            t1 = time.perf_counter()
            page = doc.pages[item['pagina']] if nome == 'pdfplumber' else doc[item['pagina']]
            t2 = time.perf_counter()
            diag = {}
            ws = (extrator.palavras_da_pagina(page) if nome == 'pdfplumber'
                  else palavras_da_pagina_pymupdf(page, diagnostico=diag))
            t3 = time.perf_counter()
            blocos = extrator.segmentar(ws, tab)
            t4 = time.perf_counter()
            reg = {'status': 'ok', 'signature': signature, 'palavras': ws,
                   'blocos': compactar_blocos(blocos, ws), 'diagnostico': diag,
                   'tempos': {'abertura': t1 - t0, 'acesso_pagina': t2 - t1,
                              'palavras': t3 - t2, 'segmentar': t4 - t3,
                              'palavras_segmentar': t4 - t2, 'total': t4 - t0}}
            if nome == 'pymupdf':
                # O diagnostico words e posterior ao cronometro do modulo.
                reg['words'] = palavras_words(page)
    except Exception as exc:
        reg = {'status': 'erro', 'signature': signature,
               'erro': f'{type(exc).__name__}: {exc}'}
    gravar_json(cache_path, reg)
    return reg, False


def diagnosticar(a, b, tab):
    wa, wb, ba, bb = a['palavras'], b['palavras'], a['blocos'], b['blocos']
    pares = casar(wa, wb)
    mapa = dict(pares)
    ia, ib = {i for i, _ in pares}, {j for _, j in pares}
    sa = sorted(ia, key=lambda i: wa[i]['s'])
    reverso = {j: i for i, j in pares}
    sb = [reverso[j] for j in sorted(ib, key=lambda j: wb[j]['s'])]
    words_pares = casar(wa, b['words'])
    words_mapa = {j: i for i, j in words_pares}
    stream_words_a = sorted(words_mapa.values(), key=lambda i: wa[i]['s'])
    stream_words_b = [words_mapa[j] for j in sorted(words_mapa, key=lambda j: b['words'][j]['s'])]
    donos_a = {w: i for i, v in enumerate(ba) for w in v['palavras']}
    donos_b = {w: j for j, v in enumerate(bb) for w in v['palavras']}
    ligacoes = Counter((donos_a[i], donos_b[j]) for i, j in pares if i in donos_a and j in donos_b)
    para_b, para_a = defaultdict(set), defaultdict(set)
    for i, j in ligacoes:
        para_b[i].add(j)
        para_a[j].add(i)
    partidos = {i: sorted(js) for i, js in para_b.items() if len(js) > 1}
    fundidos = {j: sorted(is_) for j, is_ in para_a.items() if len(is_) > 1}
    deltas = [max(abs(wa[i][k] - wb[j][k]) for k in ('x0', 'x1', 'top', 'bottom')) for i, j in pares]
    pares_blocos = casar(ba, bb, 'texto', 0.95)
    alterados_a = set(range(len(ba))) - {i for i, _ in pares_blocos}
    alterados_b = set(range(len(bb))) - {j for _, j in pares_blocos}
    exemplos = []
    candidatos = [i for i in range(len(wa)) if i not in ia and donos_a.get(i) in alterados_a]
    # Acrescenta maior desvio geometrico, mesmo com texto exatamente igual.
    candidatos += [i for i, _ in sorted(pares, key=lambda ij: max(
        abs(wa[ij[0]][k] - wb[ij[1]][k]) for k in ('x0', 'x1', 'top', 'bottom')), reverse=True)
                   if donos_a.get(i) in alterados_a]
    for i in list(dict.fromkeys(candidatos))[:2]:
        va = wa[i]
        vizinhos = sorted(enumerate(wb), key=lambda jv: abs(jv[1]['top'] - va['top'])
                          + abs(jv[1]['x0'] - va['x0']))[:2]
        exemplos.append({'pp': va, 'mu': [v for _, v in vizinhos], 'bloco_pp': donos_a.get(i)})
    extras_mu = [j for j in range(len(wb)) if j not in ib and donos_b.get(j) in alterados_b]
    for j in extras_mu[:2]:
        vm = wb[j]
        vizinhos = sorted(enumerate(wa), key=lambda iv: abs(iv[1]['top'] - vm['top'])
                          + abs(iv[1]['x0'] - vm['x0']))[:2]
        exemplos.append({'adicional_mu': vm, 'bloco_mu': donos_b.get(j),
                         'vizinhas_pp': [v for _, v in vizinhos]})
    comparacao = comparar_blocos(ba, bb)
    intervencao = None
    intervencoes_unitarias = []
    if not comparacao['mesma']:
        # Experimento controlado: apenas coordenadas dos pares mudam; t e s do
        # pdfplumber permanecem. Demonstra suficiencia, nao causalidade exclusiva.
        hibridas = [{**v, **({k: wb[mapa[i]][k] for k in ('x0', 'x1', 'top', 'bottom')}
                                if i in mapa else {})} for i, v in enumerate(wa)]
        h = extrator.segmentar(hibridas, tab)
        intervencao = comparar_blocos(ba, h)
        # Um controle mais permissivo e usado SOMENTE para a causa, sem alterar
        # as metricas principais: inclui palavras iguais cuja altura mudou muito.
        controle = dict(casar(wa, wb, limiar=0.35))
        afetadas = [i for i in controle if donos_a.get(i) in alterados_a]
        afetadas.sort(key=lambda i: max(abs(wa[i][k] - wb[controle[i]][k])
                                      for k in ('x0', 'x1', 'top', 'bottom')), reverse=True)
        for i in afetadas[:2]:
            j = controle[i]
            unitaria = [dict(v) for v in wa]
            unitaria[i].update({k: wb[j][k] for k in ('x0', 'x1', 'top', 'bottom')})
            resultado = comparar_blocos(ba, extrator.segmentar(unitaria, tab))
            intervencoes_unitarias.append({'pp': wa[i], 'mu': wb[j],
                                           'bloco_pp': donos_a.get(i), 'resultado': resultado})
    texto_blocos_igual = Counter(v['texto'] for v in ba) == Counter(v['texto'] for v in bb)
    return {**comparacao, 'palavras_a': len(wa), 'palavras_b': len(wb), 'pares_palavras': len(pares),
            'nao_casadas_a': len(wa) - len(pares), 'nao_casadas_b': len(wb) - len(pares),
            'tau_palavras_trace': tau_ordens(sa, sb), 'pares_words': len(words_pares),
            'tau_palavras_words': tau_ordens(stream_words_a, stream_words_b),
            'partidos': partidos, 'fundidos': fundidos, 'exemplos': exemplos,
            'texto_blocos_igual': texto_blocos_igual, 'intervencoes_unitarias': intervencoes_unitarias,
            'desvio_coord_p95': float(np.percentile(deltas, 95)) if deltas else None,
            'desvio_coord_max': max(deltas, default=None), 'geometria_apenas': intervencao,
            'diag_mu': b['diagnostico']}


def rodar_testes(run_dir):
    """Subprocessos offline; logs e contagens reais entram no relatorio."""
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
           'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
    resultados = []
    for nome, argumentos in (('novos', ['tests.test_palavras_pymupdf', '-v']),
                             ('suite', ['discover', '-s', 'tests', '-v'])):
        cmd = [sys.executable, '-B', '-m', 'unittest', *argumentos]
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, cwd=RAIZ, env=env, capture_output=True, encoding='utf-8', errors='replace')
        texto = proc.stdout + proc.stderr
        log = run_dir / f'testes_{nome}.txt'
        log.write_text(texto, encoding='utf-8')
        n = re.search(r'Ran (\d+) tests?', texto)
        resultados.append({'nome': nome, 'comando': subprocess.list2cmdline(cmd),
                           'n': int(n[1]) if n else None, 'exit_code': proc.returncode,
                           'segundos': time.perf_counter() - t0, 'log': str(log.relative_to(RAIZ))})
        print(f'Testes {nome}: n={resultados[-1]["n"]}, exit_code={proc.returncode}', flush=True)
    gravar_json(run_dir / 'testes.json', resultados)
    return resultados


def verificar_anterior():
    """Recalcula agregados do cache anterior, sem confiar no resumo escrito."""
    path = RAIZ / 'resultados' / 'pymupdf_palavras_cache.json'
    if not path.exists():
        return None
    with path.open(encoding='utf-8') as f:
        cache = json.load(f)
    regs = [r for r in cache.get('paginas', {}).values() if r.get('status') == 'ok' and r.get('comp')]
    if not regs:
        return None
    a = sum(r['comp']['n_p'] for r in regs)
    b = sum(r['comp']['n_m'] for r in regs)
    casados = sum(r['comp']['n_pares'] for r in regs)
    return {'n': len(regs), 'palavras_pp': a, 'palavras_mu': b, 'pares': casados,
            'frac_pp_micro': casados / a, 'frac_mu_micro': casados / b,
            'frac_pp_macro': float(np.mean([r['comp']['frac_p_em_m'] for r in regs])),
            'tempo_pp_media': float(np.mean([r['t_total_plumber'] for r in regs])),
            'tempo_mu_media': float(np.mean([r['t_total_mupdf'] for r in regs]))}


def fmt(x, n=3):
    return '—' if x is None else f'{x:.{n}f}'.replace('.', ',')


def pct(x, total):
    return fmt(100 * x / total, 2) + '%' if total else '—'


def media(valores):
    xs = [v for v in valores if v is not None]
    return float(np.mean(xs)) if xs else None


def resumo(regs):
    bons = [r for r in regs if r['status'] == 'ok']
    cs = [r['comparacao'] for r in bons]
    n = len(cs)
    a, b, identicos = (sum(c[k] for c in cs) for k in ('n_a', 'n_b', 'identicos'))
    tempos = {met: {et: media([r[met]['tempos'][et] for r in bons])
                    for et in ('abertura', 'acesso_pagina', 'palavras', 'segmentar', 'palavras_segmentar', 'total')}
              for met in ('pdfplumber', 'pymupdf')}
    return {'n': n, 'erros': len(regs) - n, 'blocos_pp': a, 'blocos_mu': b, 'identicos': identicos,
            'mesmas': sum(c['mesma'] for c in cs), 'partidos': sum(len(c['partidos']) for c in cs),
            'fundidos': sum(len(c['fundidos']) for c in cs), 'tempos': tempos,
            'tau': {k: media([c['tau'][k] for c in cs]) for k in ('stream', 'naive', 'xycut')},
            'n_tau': {k: sum(c['tau'][k] is not None for c in cs) for k in ('stream', 'naive', 'xycut')},
            'stream_total': sum(c['ordem_total_igual']['stream'] for c in cs),
            'stream_comum': sum(c['ordem_comum_igual']['stream'] is True for c in cs),
            'word_pp': sum(c['palavras_a'] for c in cs), 'word_mu': sum(c['palavras_b'] for c in cs),
            'word_pares': sum(c['pares_palavras'] for c in cs),
            'trace_tau': media([c['tau_palavras_trace'] for c in cs]),
            'words_tau': media([c['tau_palavras_words'] for c in cs]),
            'diag': dict(sum((Counter(c['diag_mu']) for c in cs), Counter()))}


def celula(texto):
    return str(texto).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def evidencia(w):
    txt = w['t'][:65]
    return celula(f'“{txt}” [{fmt(w["x0"], 2)}; {fmt(w["top"], 2)}; '
                  f'{fmt(w["x1"], 2)}; {fmt(w["bottom"], 2)}]')


def escrever_relatorio(regs, modelos, run_dir, testes, anterior, do_zero, iniciada):
    r = resumo(regs)
    n = r['n']
    completo = len(modelos) == 104 and len(regs) == len(modelos) and not r['erros']
    iguais = completo and r['mesmas'] == n and r['stream_total'] == n
    veredito = ('Paridade observada nesta amostra; adocao ainda exige revisao e decisao do autor.' if iguais else
                'NAO pode virar o padrao como substituicao transparente: blocos e/ou silver divergem.'
                if completo else 'MEDICAO PARCIAL: ainda nao ha veredito de paridade.')
    pp, mu = r['tempos']['pdfplumber']['total'], r['tempos']['pymupdf']['total']
    ganho = pp / mu if pp is not None and mu else None
    linhas = ['# T14 — Paridade do extrator opcional PyMuPDF', '',
              f'Execução: `{run_dir.relative_to(RAIZ).as_posix()}`; iniciada em {iniciada}.',
              f'CPU, {platform.platform()}, Python {platform.python_version()}, pdfplumber {pdfplumber.__version__}, '
              f'PyMuPDF {pymupdf.VersionBind}. Estado: {len(regs)}/{len(modelos)} páginas processadas, '
              f'{r["erros"]} erros. Do zero: {do_zero}.', '', '## Resumo em cinco linhas', '',
              f'1. **Veredito: {veredito}**',
              f'2. Blocos idênticos (texto exato e IoU ≥ 0,95): {r["identicos"]}/{r["blocos_pp"]} '
              f'({pct(r["identicos"], r["blocos_pp"])}); segmentação inteira igual em {r["mesmas"]}/{n} páginas.',
              f'3. Splits detectados por palavras comuns: {r["partidos"]}; fusões: {r["fundidos"]}; '
              f'τ médio stream nos blocos casados: {fmt(r["tau"]["stream"])}.',
              f'4. A referência silver inteira é preservada em {r["stream_total"]}/{n} páginas; '
              f'τ de palavras em fluxo (trace): {fmt(r["trace_tau"])}. Não regenerar a silver com este módulo '
              'quando houver qualquer divergência.',
              f'5. Ponta a ponta: pdfplumber {fmt(pp)} s/página e PyMuPDF {fmt(mu)} s/página; '
              f'aceleração {fmt(ganho, 2)}×, com layout já em cache e sem GPU.', '',
              '## Tabela principal', '',
              '| Amostra | Páginas | Blocos PP / Mu | Blocos idênticos / PP | Páginas iguais | Partidos / fundidos | '
              'τ stream | τ naive | τ xycut | PP s/pág | Mu s/pág | Ganho |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for grupo in ('bancada44', 'extras60', 'total'):
        s = r if grupo == 'total' else resumo([v for v in regs if v['grupo'] == grupo])
        tp, tm = s['tempos']['pdfplumber']['total'], s['tempos']['pymupdf']['total']
        linhas.append(f'| {grupo} | {s["n"]} | {s["blocos_pp"]} / {s["blocos_mu"]} | '
                      f'{pct(s["identicos"], s["blocos_pp"])} | {s["mesmas"]} | {s["partidos"]} / {s["fundidos"]} | '
                      f'{fmt(s["tau"]["stream"])} | {fmt(s["tau"]["naive"])} | {fmt(s["tau"]["xycut"])} | '
                      f'{fmt(tp)} | {fmt(tm)} | {fmt(tp / tm if tp and tm else None, 2)}× |')
    linhas += ['', f'Fração inversa de blocos idênticos / Mu: {pct(r["identicos"], r["blocos_mu"])}. '
               f'Médias de blocos/página: PP {fmt(r["blocos_pp"] / n if n else None, 2)}, '
               f'Mu {fmt(r["blocos_mu"] / n if n else None, 2)}. '
               '“Página igual” exige bijeção completa dos blocos com o critério acima; '
               'não exige igualdade de bytes nem dos IDs aleatórios.', '',
               '## Tempos e vazão', '', '| Etapa | PP média s/pág | Mu média s/pág |', '|---|---:|---:|']
    for et in ('abertura', 'acesso_pagina', 'palavras', 'segmentar', 'palavras_segmentar', 'total'):
        linhas.append(f'| {et} | {fmt(r["tempos"]["pdfplumber"][et], 4)} | {fmt(r["tempos"]["pymupdf"][et], 4)} |')
    linhas += ['', f'Vazão serial total: PP {fmt(1 / pp if pp else None, 2)} páginas/s; '
               f'Mu {fmt(1 / mu if mu else None, 2)} páginas/s. '
               '“total” = abertura + acesso à página + palavras + segmentar. '
               'O PDF é reaberto por página, sem cache quente de objetos entre páginas; '
               'o acesso do pdfplumber inclui a enumeração das páginas. '
               'Pareamento, análise, testes, escrita de cache e leitura de layout ficam fora. '
               'Detecção/renderização de layout não foi repetida: estas não são latências do pipeline visual completo.', '',
               '## Protocolo, identidades e ordem de fluxo', '',
               f'Bancada: 40 páginas de `blocos_v1`, seed 42, veículos `teste + ufs_nao_confiaveis`, '
               f'mais as {len(bancada.PROBLEMAS)} páginas-problema, usando as funções originais. '
               f'Extras: 60 páginas de `blocos`, sem sobreposição com a bancada, seed {SEED}, '
               'sorteio em rodadas por veículo. O manifesto guarda os identificadores, tabelas e assinaturas. '
               'Nenhuma página é descartada pelo filtro de número de blocos. '
               'São usadas apenas tabelas já disponíveis em `data/processed/layout`; '
               'a mesma lista entra nos dois caminhos, sem gerar ou modificar o cache de layout.', '',
               'Os pares são bijetivos por cardinalidade máxima em um grafo de texto EXATO e IoU. '
               'τ de blocos usa exclusivamente pares com IoU ≥ 0,95; IDs de um caminho não são comparados '
               'diretamente com IDs do outro. τ é macro por página, com exclusão de páginas com menos '
               'de dois pares. Palavras usam IoU ≥ 0,7. Splits/fusões são inferidos quando palavras casadas '
               'de um bloco pertencem a vários no outro; são evidência conservadora, não contagem exaustiva. '
               'Um split seguido de fusão pode entrar nas duas contagens.', '',
               f'Páginas com τ de blocos calculável: `{r["n_tau"]}`. '
               f'Blocos stream com ordem igual só no subconjunto: {r["stream_comum"]}/{n}; '
               f'ordem e universo completos iguais: {r["stream_total"]}/{n}. '
               'Uma correlação alta em pares sobreviventes não demonstra equivalência da referência silver.', '',
               f'Palavras PP / Mu: {r["word_pp"]} / {r["word_mu"]}; casadas: {r["word_pares"]} '
               f'({pct(r["word_pares"], r["word_pp"])} / {pct(r["word_pares"], r["word_mu"])}). '
               f'τ macro do fluxo de palavras PP × trace: {fmt(r["trace_tau"], 6)}; '
               f'PP × `words(sort=False)`: {fmt(r["words_tau"], 6)}.', '',
               '`words(sort=False)` não faz a ordenação geométrica opcional, mas deriva de TextPage, '
               'que agrupa caracteres em linhas/blocos. O módulo usa `get_texttrace()` e `seqno`, '
               'sem reagrupamento do TextPage ou espaços inventados. A sequência de desenho é uma '
               'aproximação melhor do fluxo, porém os parsers podem decodificar caracteres e Form XObjects '
               'de maneira diferente. A medida acima testa a concordância, sem prometer identidade universal. '
               '[API get_text](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text), '
               '[API get_texttrace](https://pymupdf.readthedocs.io/en/latest/functions.html#Page.get_texttrace).', '',
               '## Páginas que mudam e evidência da causa', '',
               'G = intervenção que mantém todos os textos, índices de fluxo e tokens do PP, '
               'trocando só as coordenadas das palavras casadas pelas do Mu. '
               'G diferente do PP demonstra que a geometria é suficiente para mudar blocos. '
               'Palavras não casadas podem refletir decodificação, limites dos tokens, '
               'orientação ou geometria fora da tolerância; não se atribui tudo a uma “melhoria” do parser.', '',
               '| Página (índice desde zero) | Blocos PP→Mu | Idênticos | Partidos/fundidos | '
               'Palavras sem par PP/Mu | Desvio máx. pt | Intervenção G: idênticos/PP, n blocos |',
               '|---|---:|---:|---:|---:|---:|---:|']
    mudam = [v for v in regs if v['status'] == 'ok' and not v['comparacao']['mesma']]
    for v in mudam:
        c = v['comparacao']
        g = c['geometria_apenas']
        linhas.append(f'| `{celula(v["page_id"])}` | {c["n_a"]}→{c["n_b"]} | {c["identicos"]} | '
                      f'{len(c["partidos"])}/{len(c["fundidos"])} | {c["nao_casadas_a"]}/{c["nao_casadas_b"]} | '
                      f'{fmt(c["desvio_coord_max"], 3)} | {g["identicos"]}/{g["n_a"]}, {g["n_b"]} |')
    for v in mudam:
        c = v['comparacao']
        linhas += ['', f'- `{celula(v["page_id"])}`: '
                   f'geometria isolada {"altera" if not c["geometria_apenas"]["mesma"] else "não altera"} os blocos; '
                   f'{"textos dos blocos iguais, caixas divergem" if c["texto_blocos_igual"] else "textos/partição dos blocos divergem"}; '
                   f'palavras sem correspondência {c["nao_casadas_a"]}/{c["nao_casadas_b"]}; '
                   f'aproximações do módulo `{c["diag_mu"]}`.']
        for ex in c['exemplos']:
            if 'pp' in ex:
                linhas.append(f'  - Bloco afetado PP {ex["bloco_pp"]}, palavra PP {evidencia(ex["pp"])}; '
                              'vizinhas Mu: ' + ' / '.join(evidencia(w) for w in ex['mu']) + '.')
            else:
                linhas.append(f'  - Bloco afetado Mu {ex["bloco_mu"]}: palavra sem par estrito '
                              f'{evidencia(ex["adicional_mu"])}; vizinhas PP: '
                              + ' / '.join(evidencia(w) for w in ex['vizinhas_pp']) + '.')
        for u in c['intervencoes_unitarias']:
            rr = u['resultado']
            if not rr['mesma']:
                linhas.append(f'  - Controle unitário no bloco PP {u["bloco_pp"]}: trocar só a caixa de '
                              f'{evidencia(u["pp"])} por {evidencia(u["mu"])} produz '
                              f'{rr["n_b"]} blocos, dos quais {rr["identicos"]}/{rr["n_a"]} '
                              'continuam idênticos. Texto e fluxo não foram alterados; '
                              'o par usado neste controle aceita IoU ≥ 0,35.')
    linhas += ['', '### Divergências de ordem nos blocos sobreviventes', '',
               '| Página | τ stream | τ naive | τ xycut | Pares / PP / Mu |',
               '|---|---:|---:|---:|---:|']
    for v in regs:
        if v['status'] != 'ok':
            continue
        c = v['comparacao']
        if any(c['ordem_comum_igual'][k] is False for k in ('stream', 'naive', 'xycut')):
            linhas.append(f'| `{celula(v["page_id"])}` | {fmt(c["tau"]["stream"], 6)} | '
                          f'{fmt(c["tau"]["naive"], 6)} | {fmt(c["tau"]["xycut"], 6)} | '
                          f'{c["identicos"]} / {c["n_a"]} / {c["n_b"]} |')
    linhas += ['', '## Auditoria da medição anterior', '']
    if anterior:
        linhas += [f'Leitura e recálculo de `resultados/pymupdf_palavras_cache.json`: {anterior["n"]} páginas, '
                   f'{anterior["pares"]} pares / {anterior["palavras_pp"]} palavras PP '
                   f'({pct(anterior["pares"], anterior["palavras_pp"])} micro; '
                   f'{fmt(100 * anterior["frac_pp_macro"], 2)}% macro). '
                   f'Médias totais: PP {fmt(anterior["tempo_pp_media"])} s; Mu {fmt(anterior["tempo_mu_media"])} s. '
                   'O resumo anterior afirmava 99,4% de palavras casadas, o que não corresponde ao agregado '
                   'do próprio cache. A classificação anterior chamada “acento_unicode” também incluía '
                   'textos iguais (normalização idêntica): não prova divergência de acentos. '
                   'Nem ausência de perda nem paridade dos blocos tinham sido demonstradas.']
    else:
        linhas.append('Cache anterior ausente ou sem páginas válidas; auditoria indisponível.')
    linhas += ['', '## Testes executados', '', '| Conjunto | Testes | Código de saída | Tempo s | Log |',
               '|---|---:|---:|---:|---|']
    for t in testes:
        linhas.append(f'| {t["nome"]} | {t["n"]} | {t["exit_code"]} | {fmt(t["segundos"], 2)} | `{t["log"]}` |')
    linhas += ['', 'A suíte inclui os novos testes; não somar as duas linhas. '
               'Comandos e saída completa estão nos logs e em `testes.json` da execução.', '',
               '## Limitações e compatibilidade', '',
               f'- Amostra pequena e balanceada ({n} páginas concluídas, '
               f'{len({v["uf"] for v in regs if v["status"] == "ok"})} veículos), '
               'com páginas-problema escolhidas deliberadamente. Não representa a distribuição de todo '
               'o acervo nem demonstra igualdade em PDFs inéditos. Não é avaliação humana de qualidade.',
               '- Não usa export ou anotações do Label Studio nem modifica dado humano. '
               'O viés de ancoragem de anotações feitas corrigindo pré-anotação não afeta este teste '
               'de equivalência entre parsers; continua uma limitação de avaliações humanas do projeto parceiro.',
               '- Uma rodada cronometrada por página, processo serial, abertura fresca, caches do SO '
               'não controlados e outros trabalhos na máquina. Não interpretar pequenas diferenças de tempo '
               'como significativas nem extrapolar vazão para treino/layout/OCR.',
               '- Campos emitidos: t, x0, x1, top, bottom, s. Tamanho/negrito não são emitidos pelo '
               'extrator original; altura e deduplicação são reproduzidas com descritores PDF/AFM. '
               'Fontes ambíguas/Type3 usam descender MuPDF e ficam no diagnóstico. '
               'Larguras, CMaps, ligaduras, espaços e transformações podem divergir. '
               f'Diagnósticos acumulados: `{r["diag"]}`.',
               '- Coordenadas seguem a MediaBox do pdfplumber, sem recorte pela CropBox. '
               'O caso CropBox com rotação é testado; o módulo não altera o documento. '
               'Não há OCR para texto em imagens. Envelope PKCS#7 é extraído somente em resultados/ '
               'pelo script, quando presente; arquivos normais com zeros finais abrem diretamente.',
               '- PyMuPDF/MuPDF oferecem AGPL e licença comercial. A escolha de distribuição do '
               'projeto precisa considerar a licença antes de integrar a dependência. '
               '[Licenciamento oficial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).', '',
               '## Diff proposto (não aplicado)', '',
               'Opção local por variável de ambiente; o worker ainda abre pdfplumber para manter '
               'dimensões e os demais contratos. O parsing de caracteres do pdfplumber é evitado, '
               'mas a enumeração/abertura ainda existe. Não torna o novo caminho padrão e não autoriza '
               'regenerar a silver nem lotes humanos. Revisão cruzada e decisão do Pedro continuam necessárias.', '',
               '```diff', '--- a/src/data/extrator.py', '+++ b/src/data/extrator.py', '@@',
               ' def palavras_da_pagina(page):',
               '     """Palavras em ordem de fluxo do PDF, com o indice de fluxo em \'s\'."""',
               '+    if os.environ.get("TCC_EXTRATOR_PALAVRAS", "pdfplumber") == "pymupdf":',
               '+        import pymupdf',
               '+        from src.data.palavras_pymupdf import palavras_da_pagina_pymupdf',
               '+        with pymupdf.open(page.pdf.stream.name) as pdf:',
               '+            return palavras_da_pagina_pymupdf(pdf[page.page_number - 1])',
               '     try:', '         page = page.dedupe_chars(tolerance=1)', '```', '',
               'Esse diff mínimo destina-se aos workers atuais com arquivo PDF local, não a BytesIO '
               'nem páginas recortadas via Page.crop(). O benchmark mede o módulo direto com PyMuPDF, '
               'não esse wrapper híbrido. Para remover também abertura/enumeração do pdfplumber, '
               'é preciso uma segunda alteração nos workers e nas dimensões, fora desta tarefa.', '',
               '## Reprodução e conferência automática', '',
               '`venv/Scripts/python.exe -B orquestracao/analises/extrator_pymupdf_paridade.py --do-zero`', '',
               'Sem `--do-zero`, a execução atual retoma cada caminho cujo fingerprint confere. '
               'Hashes do extrator, módulo, PDF (tamanho/mtime) e tabelas invalidam caches incompatíveis. '
               'Arquivos incompletos são ignorados. Dados intermediários completos e resumos ficam '
               'no diretório indicado acima. As contagens da tabela são conferidas contra os registros '
               'antes de cada escrita do relatório.']
    for v in regs:
        if v['status'] != 'ok':
            linhas.append(f'- ERRO `{celula(v["page_id"])}`: {celula(v.get("erro", "erro de caminho"))}.')
    texto = '\n'.join(linhas) + '\n'
    # Verificacao independente das contagens do agregado e da tabela escrita.
    assert r['identicos'] <= min(r['blocos_pp'], r['blocos_mu'])
    assert r['mesmas'] <= n and r['stream_total'] <= r['mesmas']
    assert sum(1 for v in regs if v['status'] == 'ok') == n
    tmp = RELATORIO.with_suffix('.md.tmp')
    tmp.write_text(texto, encoding='utf-8')
    os.replace(tmp, RELATORIO)
    gravar_json(run_dir / 'resumo.json', {'resumo': r, 'completo': completo, 'veredito': veredito,
                                        'do_zero': do_zero, 'testes': testes, 'auditoria_anterior': anterior})
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--do-zero', action='store_true')
    parser.add_argument('--limite', type=int, help='piloto; o padrao processa as 104 paginas')
    args = parser.parse_args()
    modelos = amostra()
    if args.limite is not None:
        if args.limite <= 0:
            parser.error('--limite deve ser positivo')
        modelos = modelos[:args.limite]
    regioes = layout.carregar_cache(ufs={p['uf'] for p in modelos})
    faltam = [p['page_id'] for p in modelos if p['page_id'] not in regioes]
    if faltam:
        raise RuntimeError('Layout nao disponivel; nao sera gerado em data/: ' + '; '.join(faltam))
    for p in modelos:
        p['tabelas'] = layout.tabelas(regioes[p['page_id']])
    CACHE.mkdir(parents=True, exist_ok=True)
    ponteiro = CACHE / 'execucao_atual.json'
    codigo = {'extrator': assinatura_codigo(RAIZ / 'src/data/extrator.py'),
              'modulo': assinatura_codigo(MODULO), 'bancada': assinatura_codigo(Path(bancada.__file__))}
    fingerprint = hash_json({'schema': SCHEMA, 'modelos': modelos, 'codigo': codigo,
                             'pp': pdfplumber.__version__, 'mu': pymupdf.VersionBind})
    run_dir = None
    if not args.do_zero and ponteiro.exists():
        try:
            with ponteiro.open(encoding='utf-8') as f:
                info = json.load(f)
            candidato = CACHE / info['diretorio']
            if info.get('fingerprint') == fingerprint and candidato.is_relative_to(CACHE) and candidato.is_dir():
                run_dir = candidato
        except (ValueError, KeyError, OSError):
            pass
    if run_dir is None:
        run_dir = CACHE / (time.strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8])
        run_dir.mkdir()
        gravar_json(ponteiro, {'fingerprint': fingerprint, 'diretorio': run_dir.name})
    iniciada = time.strftime('%Y-%m-%d %H:%M:%S')
    gravar_json(run_dir / 'manifesto.json', {'paginas': modelos, 'fingerprint': fingerprint,
                                          'script_sha256': assinatura_codigo(Path(__file__)),
                                          'codigo': codigo, 'iniciada': iniciada, 'do_zero': args.do_zero,
                                          'comando': subprocess.list2cmdline(sys.argv)})
    testes = rodar_testes(run_dir)
    anterior = verificar_anterior()
    regs = []
    escrever_relatorio(regs, modelos, run_dir, testes, anterior, args.do_zero, iniciada)
    for num, item in enumerate(modelos, 1):
        pid = item['page_id']
        path = Path(extrator.RAW) / item['uf'] / item['arquivo']
        digest = hashlib.sha256(pid.encode('utf-8')).hexdigest()[:24]
        reg = {**item, 'status': 'erro'}
        try:
            st = path.stat()
            pdfpath, envelope = resolver_pdf(path, run_dir)
            reg['envelope'] = envelope
            sig = {'schema': SCHEMA, 'pdf': [str(path), st.st_size, st.st_mtime_ns],
                   'page_id': pid, 'tab': item['tabelas'], 'codigo': codigo,
                   'versoes': [pdfplumber.__version__, pymupdf.VersionBind]}
            caminhos = ['pdfplumber', 'pymupdf'] if num % 2 else ['pymupdf', 'pdfplumber']
            reutilizados = []
            for nome in caminhos:
                resultado, reuso = medir_caminho(item, item['tabelas'], pdfpath, nome,
                                                run_dir / f'{digest}_{nome}.json', hash_json(sig))
                reg[nome] = resultado
                reutilizados.append(reuso)
            if all(reg[m]['status'] == 'ok' for m in caminhos):
                reg['comparacao'] = diagnosticar(reg['pdfplumber'], reg['pymupdf'], item['tabelas'])
                reg['status'] = 'ok'
            else:
                reg['erro'] = '; '.join(reg[m].get('erro', '') for m in caminhos if reg[m]['status'] != 'ok')
        except Exception as exc:
            reg['erro'] = f'{type(exc).__name__}: {exc}'
            reutilizados = []
        # O resumo por pagina nao duplica as listas grandes de palavras dos caches.
        pequeno = {k: v for k, v in reg.items() if k not in ('pdfplumber', 'pymupdf')}
        pequeno.update({m: {'tempos': reg[m]['tempos']} for m in ('pdfplumber', 'pymupdf')
                        if reg.get(m, {}).get('status') == 'ok'})
        gravar_json(run_dir / f'{digest}_comparacao.json', pequeno)
        regs.append(pequeno)
        r = escrever_relatorio(regs, modelos, run_dir, testes, anterior, args.do_zero, iniciada)
        if reg['status'] == 'ok':
            c = reg['comparacao']
            print(f'[{num}/{len(modelos)}] {pid}: blocos {c["n_a"]}/{c["n_b"]}, '
                  f'idênticos {c["identicos"]}, τ stream={fmt(c["tau"]["stream"], 6)}, '
                  f'cache={all(reutilizados)}', flush=True)
        else:
            print(f'[{num}/{len(modelos)}] ERRO {pid}: {reg.get("erro")}', flush=True)
    gravar_json(run_dir / 'paginas.json', regs)
    print('RESUMO_JSON=' + json.dumps(r, ensure_ascii=False, allow_nan=False), flush=True)
    print(f'RELATORIO={RELATORIO.relative_to(RAIZ)}', flush=True)
    if r['erros'] or any(t['exit_code'] != 0 for t in testes):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
