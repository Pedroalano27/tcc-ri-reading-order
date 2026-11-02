"""Gera comparador visual local do Golden v4, sem alterar dados ou anotacoes.

Mostra extracao v3, Golden v4 e representacoes sem caixas de paragrafo.
Uso: venv/Scripts/python.exe src/data/comparador_golden_v4.py
"""
import base64, io, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from PIL import Image, ImageDraw
from src.data.dataset_sem_caixas_finas import representar, write
from src.data.estruturas_pagina import representar_estruturas
OUT=ROOT/'resultados/comparador_golden_v4'

def ler(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    golden=ler(ROOT/'data/golden/golden_v4/tarefas.jsonl')
    sources={}
    for lote in ('diamond_piloto','diamond_treino'):
        for p in ler(ROOT/f'data/diamond/{lote}/tarefas.jsonl'): sources[p['page_id']]=p
    datasets={v:{p['page_id']:p for p in ler(ROOT/f'resultados/datasets_sem_caixas/{v}/bancada_humana.jsonl')} for v in ('linhas','colunas')}
    pages=[]; novas={"linhas":[],"colunas":[]}
    for p in golden:
        pid=p['page_id']; d=sources[pid]
        if pid not in datasets['linhas']:
            a,b=representar(d); datasets['linhas'][pid]=a;datasets['colunas'][pid]=b
        ea,eb=representar_estruturas(d);novas['linhas'].append(ea);novas['colunas'].append(eb)
        variants={'linhas_estruturas':ea['unidades'],'colunas_estruturas':eb['unidades'],'v3':d['blocos_v3'],'v4':p['bounding_boxes'],
                  'linhas':datasets['linhas'][pid]['unidades'],'colunas':datasets['colunas'][pid]['unidades']}
        boxes={}
        for v,ns in variants.items():
            boxes[v]=[{'id':str(n.get('id',i)),'bbox':n['bbox'],'tipo':n.get('tipo',n.get('classe','texto')),
                       'text':n.get('text',''),'palavras':len(n.get('ks',[]))} for i,n in enumerate(ns)]
        imagepath=ROOT/'data/golden/golden_v4/img'/p['imagem']
        im=Image.open(imagepath).convert('RGB');im.thumbnail((1000,1500))
        buf=io.BytesIO();im.save(buf,format='JPEG',quality=85)
        pages.append({'id':pid,'imagem':'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode(),
                      'dimensions':p['dimensions'],'boxes':boxes,'colunas':datasets['colunas'][pid]['colunas']})
    for v,rows in novas.items(): write(ROOT/f'resultados/estruturas_golden_v4/{v}.jsonl',rows)
    template=(Path(__file__).with_suffix('.html')).read_text(encoding='utf-8')
    (OUT/'index.html').write_text(template.replace('__DATA__',json.dumps(pages,ensure_ascii=False).replace('</','<\/')),encoding='utf-8')
    # Exemplos estaticos de paginas com maior evidencia de multicolunas.
    examples=sorted(pages,key=lambda p:(p['colunas']['n_estimado'],len(p['boxes']['v4'])),reverse=True)[:3]
    for j,p in enumerate(examples,1):
        im=Image.open(io.BytesIO(base64.b64decode(p['imagem'].split(',')[1]))).convert('RGB')
        im.thumbnail((500,760));w,h=im.size; sheet=Image.new('RGB',(w*3,h+45),'white')
        draw=ImageDraw.Draw(sheet)
        for col,(v,title) in enumerate((('v3','Extrator v3'),('v4','Golden v4'),('colunas','Texto por colunas'))):
            layer=im.copy();ld=ImageDraw.Draw(layer);sx=w/p['dimensions']['width'];sy=h/p['dimensions']['height']
            for b in p['boxes'][v]:
                typ=b['tipo'];color='#d97706' if typ in ('table','tabela') else '#be185d' if typ in ('picture','figura','imagem') else '#0284c7'
                ld.rectangle([b['bbox'][0]*sx,b['bbox'][1]*sy,b['bbox'][2]*sx,b['bbox'][3]*sy],outline=color,width=2)
            sheet.paste(layer,(col*w,45));draw.text((col*w+12,12),title,fill='black')
        sheet.save(OUT/f'exemplo_{j}.png')
    (OUT/'manifesto.json').write_text(json.dumps({'paginas':len(pages),'variantes':['v3','v4','linhas','colunas','linhas_estruturas','colunas_estruturas'],
        'exemplos':[p['id'] for p in examples],'imagens_ausentes':0,'aviso':'Golden v4 contem 45 tarefas; avaliacao humana anterior usa 44 concluidas. v4 mostra caixas existentes, nao nova anotacao.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'paginas':len(pages),'arquivo':str(OUT/'index.html')},ensure_ascii=False))

if __name__=='__main__': main()
