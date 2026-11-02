"""Exporta linhas ou faixas de coluna, sem caixas de paragrafo.

Tabelas e imagens do detector automatico ficam atomicas. Texto conserva IDs
de palavras e linhas. Referencias humanas sao escritas separadamente.
Uso: venv/Scripts/python.exe src/data/dataset_sem_caixas_finas.py --avaliar
Saida experimental em resultados/datasets_sem_caixas; originais intocados.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import argparse, collections, hashlib, json, random, statistics, time
from orquestracao.analises import ordem_sem_bbox as o

OUT = ROOT / 'resultados/datasets_sem_caixas'

def zonas(items, ids, h, depth=0):
    """Divide em faixas e colunas; nunca usa rotulos de paragrafo humanos."""
    if not ids: return []
    cuts = o.vales_locais(items, ids, h, .08) if depth < 40 else []
    if not cuts and depth < 40: cuts = o.vales(items, ids, h, .08)
    if not cuts:
        return [sorted(ids, key=lambda i: (items[i]['bbox'][1], items[i]['bbox'][0]))]
    width = max(items[i]['bbox'][2] for i in ids)-min(items[i]['bbox'][0] for i in ids)
    bridges = [i for i in ids if any(items[i]['bbox'][0] < c < items[i]['bbox'][2]
        and min(c-items[i]['bbox'][0],items[i]['bbox'][2]-c)>=.1*width for c in cuts)]
    if bridges:
        bridges.sort(key=lambda i: (items[i]['bbox'][1],items[i]['bbox'][0]))
        ys=[sum(items[i]['bbox'][1::2])/2 for i in bridges]
        bands=[[] for _ in range(len(bridges)+1)]
        for i in ids:
            if i not in bridges: bands[sum(y<sum(items[i]['bbox'][1::2])/2 for y in ys)].append(i)
        out=[]
        for j,b in enumerate(bands):
            out+=zonas(items,b,h,depth+1)
            if j<len(bridges): out.append([bridges[j]])
        return out
    cols=[[] for _ in range(len(cuts)+1)]
    for i in ids: cols[sum(c<sum(items[i]['bbox'][::2])/2 for c in cuts)].append(i)
    return [g for col in cols for g in zonas(items,col,h,depth+1)]

def representar(p):
    ws=p['palavras']; h=statistics.median(w[4]-w[2] for w in ws) if ws else 10
    atoms,free=o.atomos(ws,p.get('detector',{}).get('regioes',[]),.45)
    items=atoms+o.linhas_partidas(ws,free,1.2,h)
    textids=list(range(len(atoms),len(items)))
    groups=zonas(items,textids,h)
    nodes=[]
    for i,a in enumerate(atoms): nodes.append(dict(a,id=f'a{i}'))
    for j,g in enumerate(groups):
        nodes.append({'id':f'c{j}','tipo':'texto_coluna','bbox':o.envelope([items[i]['bbox'] for i in g]),
                      'ks':[k for i in g for k in items[i]['ks']], 'linhas':[items[i] for i in g]})
    owner={i:j for j,g in enumerate(groups) for i in g}
    lines=[dict(m,id=f'l{i}',coluna=None if i<len(atoms) else f'c{owner[i]}') for i,m in enumerate(items)]
    body=[i for i in textids if .1*p['dimensions']['height']<sum(items[i]['bbox'][1::2])/2<.95*p['dimensions']['height']]
    cuts=o.vales_locais(items,body,h,.08) if body else []
    def package(ns,version):
        seen=[k for n in ns for k in n['ks']]
        assert sorted(seen)==list(range(len(ws))), 'Perda ou duplicacao de palavras'
        for n in ns: n['text']=' '.join(ws[k][0] for k in n['ks'])
        random.Random(p['page_id']+version).shuffle(ns)
        return {'page_id':p['page_id'],'uf':p.get('uf'),'dimensions':p['dimensions'],
                'representacao':version,'palavras':ws,'unidades':ns,'h_linha':h,
                'colunas':{'cortes_x':cuts,'n_estimado':len(cuts)+1,'faixas':len(groups),
                           'criterio':'calhas locais; faixas variaveis; nao anotacao humana'},
                'detector':p.get('detector',{}).get('modelo'),'score_atomos':.45}
    return package(lines,'linhas'),package(nodes,'colunas')

def write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--avaliar',action='store_true'); args=ap.parse_args()
    splits=json.loads((ROOT/'data/processed/splits.json').read_text(encoding='utf-8'))
    pages={}; sources={}
    for f in sorted((ROOT/'data/diamond').glob('*/tarefas.jsonl')):
        for p in o.ler(f):
            if 'palavras' in p and 'detector' in p:
                pages.setdefault(p['page_id'],p); sources.setdefault(p['page_id'],str(f.relative_to(ROOT)))
    gold,_=o.preparar(); refs={}
    for q in gold:
        pid=q['p']['page_id']
        pages[pid]=dict(q['d'],palavras=q['ws'])
        sources[pid]='diamond canonico associado ao golden_v4'
        refs[q['p']['page_id']]=[k for rid in q['gt_r'] for L in o.linhas(q['ws'],q['reg_words'][rid]) for k in L['ks']]
    outputs=collections.defaultdict(list); stats=collections.Counter()
    for pid,p in pages.items():
        part=next((s for s in ('treino','validacao','teste') if p.get('uf') in splits[s]),'sem_split')
        for r in representar(p):
            r['origem']=sources[pid]; r['split']=part
            outputs[(r['representacao'],part)].append(r)
            if pid in refs: outputs[(r['representacao'],'bancada_humana')].append(r)
        stats[part]+=1
    for (v,s),rows in outputs.items(): write(OUT/v/(s+'.jsonl'),rows)
    write(OUT/'referencias/bancada_humana.jsonl',[{'page_id':p,'ordem_palavras':r,'origem':'ordem humana de regioes + linhas internas derivadas'} for p,r in refs.items()])
    manifest={'paginas_unicas':len(pages),'por_split':dict(stats),'bancada_humana':len(refs),
        'fontes_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'data/diamond').glob('*/tarefas.jsonl'))},
        'aviso':'Split herdado por fonte; treino exportado nao significa rotulos humanos disponiveis. Sem OCR. Coordenadas de linhas continuam necessarias; sem caixas de paragrafo. Colunas sao faixas geometricas, nao numero uniforme em toda pagina.'}
    (OUT/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest['por_split']),len(pages),flush=True)
    if args.avaliar:
        from orquestracao.analises.ordem_layoutreader import Ordenador
        lr=Ordenador(2); rows=[]
        for v in ('linhas','colunas'):
            for p in outputs[(v,'bancada_humana')]:
                items=p['unidades']; ids=list(range(len(items))); W,H=p['dimensions']['width'],p['dimensions']['height']
                t=time.perf_counter(); diag={}
                order=lr.ordenar(items,ids,W,H,p['h_linha'],.08,p['page_id']+v,diag)
                seq=[k for i in order for k in items[i]['ks']]
                assert sorted(seq)==list(range(len(p['palavras'])))
                gt=refs[p['page_id']]; allowed=set(gt); pred=[k for k in seq if k in allowed]
                rows.append({'page_id':p['page_id'],'versao':v,'tau':o.kendall_tau(pred,gt),'sucessor':o.acerto_sucessor(pred,gt),
                             'tempo_ms':1000*(time.perf_counter()-t),'ordem_unidades':[items[i]['id'] for i in order]})
                print(v,len(rows),flush=True)
        write(OUT/'avaliacao/layoutreader.jsonl',rows)
        text='# Datasets sem caixas finas\n\nVersoes experimentais; originais preservados. Apenas tabela/imagem sao atomos. Texto representado por linhas ou faixas de coluna, nunca por paragrafo rotulado.\n\n'
        text+=f'{len(pages)} paginas unicas; {len(refs)} paginas na bancada humana. Split por fonte herdado, sem treino novo do modelo. Referencia derivada da ordem humana de regioes; nao referencia independente de palavras.\n\n'
        text+='| LayoutReader pronto em CPU | tau palavras | Sucessor palavras | ms/pagina |\n|---|---:|---:|---:|\n'
        for v in ('linhas','colunas'):
            rr=[r for r in rows if r['versao']==v]
            text+=f"| {v} | {statistics.mean(r['tau'] for r in rr):.4f} | {statistics.mean(r['sucessor'] for r in rr):.4f} | {statistics.mean(r['tempo_ms'] for r in rr):.1f} |\n"
        text+='\nResultados exploratorios sobre 44 paginas usadas no desenvolvimento. Versao colunas impoe ordem geometrica interna; modelo decide entre faixas. Nao demonstra generalizacao nem efeito de treinar LayoutLM nesta representacao.\n'
        (OUT/'RELATORIO.md').write_text(text,encoding='utf-8')

if __name__=='__main__': main()
