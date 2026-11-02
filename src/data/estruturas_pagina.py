"""Isola margens e quadros institucionais antes da deteccao de colunas.

Variante experimental: detector automatico, margens geometricas e molduras
vetoriais do PDF. Nunca consulta classes ou ordens humanas.
"""
import sys, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data.dataset_sem_caixas_finas import representar, write

def dentro(w,b):
    return b[0] <= (w[1]+w[3])/2 <= b[2] and b[1] <= (w[2]+w[4])/2 <= b[3]

def candidatos(p):
    import pymupdf
    W,H=p['dimensions']['width'],p['dimensions']['height'];ws=p['palavras'];cs=[]
    path=ROOT/'data/raw'/p['uf']/p['arquivo']
    if path.exists():
        with pymupdf.open(path) as doc:
            page=doc[p['pagina']];sx=W/page.rect.width;sy=H/page.rect.height
            drawings=page.get_drawings()
            horizontais=[d['rect'] for d in drawings if d['rect'].width>.6*page.rect.width and d['rect'].height<2]
            molduras=[]
            for top in horizontais:
                for bottom in horizontais:
                    if .04*page.rect.height<bottom.y0-top.y0<.55*page.rect.height and abs(top.x0-bottom.x0)<5 and abs(top.x1-bottom.x1)<5:
                        molduras.append(('re',pymupdf.Rect(top.x0,top.y0,top.x1,bottom.y0)))
            for d in drawings+[{'items':molduras}]:
                for item in d['items']:
                    if item[0]!='re':continue
                    r=item[1];b=[r.x0*sx,r.y0*sy,r.x1*sx,r.y1*sy]
                    if b[2]-b[0]<.6*W or not .04*H<b[3]-b[1]<.55*H:continue
                    text=' '.join(w[0] for w in ws if dentro(w,b)).lower()
                    # Moldura sozinha nao autoriza retirar texto principal.
                    if ('imprensa' in text and ('publica' in text or 'agência' in text or 'agencia' in text)):
                        cs.append({'tipo':'quadro_externo','bbox':b,'evidencia':'moldura vetorial + texto institucional'})
    for r in p.get('detector',{}).get('regioes',[]):
        typ={'page_header':'cabecalho','page_footer':'rodape'}.get(r['rotulo'])
        if typ and r['score']>=.6:cs.append({'tipo':typ,'bbox':r['bbox'],'evidencia':'detector automatico'})
    # Somente linhas isoladas nas bordas; sem remover palavras.
    from orquestracao.analises import ordem_sem_bbox as o
    h=statistics.median(w[4]-w[2] for w in ws) if ws else 10
    ls=o.linhas_partidas(ws,list(range(len(ws))),1.2,h)
    for typ,selected in [('cabecalho',[l for l in ls if l['bbox'][3]<.045*H]),('rodape',[l for l in ls if l['bbox'][1]>.955*H])]:
        if not selected:continue
        b=o.envelope([l['bbox'] for l in selected]);rest=[l for l in ls if l not in selected]
        gap=min((abs(l['bbox'][1]-b[3]) if typ=='cabecalho' else abs(b[1]-l['bbox'][3]) for l in rest),default=0)
        if gap>=h:cs.append({'tipo':typ,'bbox':b,'evidencia':'borda 4,5% + intervalo de uma linha'})
    return cs

def representar_estruturas(p):
    ws=p['palavras'];taken=set();fixed=[]
    for c in candidatos(p):
        ks=[k for k,w in enumerate(ws) if k not in taken and dentro(w,c['bbox'])]
        if not ks:continue
        taken.update(ks);fixed.append(dict(c,ks=ks,id='e'+str(len(fixed)),text=' '.join(ws[k][0] for k in ks)))
    free=[k for k in range(len(ws)) if k not in taken]
    a,b=representar(dict(p,palavras=[ws[k] for k in free]))
    def remap(n):
        n['ks']=[free[k] for k in n['ks']]
        for l in n.get('linhas',[]):remap(l)
    for r in (a,b):
        for n in r['unidades']:remap(n)
        r['unidades']+=fixed;r['palavras']=ws;r['representacao']+='_estruturas'
        assert sorted(k for n in r['unidades'] for k in n['ks'])==list(range(len(ws)))
    return a,b

