"""
Extracao opcional de palavras por PyMuPDF para o segmentador v3.

Evita o parsing de pagina do pdfminer, mantendo o contrato de palavras_da_pagina:
dicts com t, x0, x1, top, bottom e s, em pontos na MediaBox rotacionada, origem
superior esquerda. O extrator original NAO recorta pela CropBox: este modulo
tambem inclui texto fora dela quando o centro fica dentro das dimensoes da pagina.

Usa get_texttrace(), nao get_text('words'): os caracteres seguem a sequencia de
desenho (seqno), sem espacos sintetizados nem agrupamento geometrico do TextPage.
Reconstrui tokens com x_tolerance=1.5 e y_tolerance=2, desduplica caracteres a
1 ponto e aplica a mesma juncao de letras espacadas. A altura usa o /Descent do
FontDescriptor e o tamanho da fonte, como o pdfminer; fontes PDF padrao usam
as metricas AFM. Negrito e tamanho NAO sao campos do contrato do extrator: o
segmentador infere mudanca de fonte pela altura da caixa. Negrito falso e
removido por desduplicacao, inclusive texto simultaneamente preenchido/tracado.
O trace nao identifica o recurso PDF de cada fonte: a chave de desduplicacao usa
o nome sem prefixo subset. Fontes distintas com mesmo nome podem ser confundidas.

Limites: CMaps/ligaduras, largura de glifos, texto inclinado, fontes Type3,
fontes com mesmo nome e descritores conflitantes e transformacoes anisotropicas
podem divergir. Nao garante identidade da segmentacao nem da referencia silver;
rode orquestracao/analises/extrator_pymupdf_paridade.py antes de adotar.
Nao modifica a pagina, nao abre rede, nao usa modelos, GPU nem pdfplumber.

Uso (da raiz):
    import pymupdf
    from src.data.palavras_pymupdf import palavras_da_pagina_pymupdf
    from src.data.extrator import segmentar
    with pymupdf.open('diario.pdf') as pdf:
        blocos = segmentar(palavras_da_pagina_pymupdf(pdf[0]))

diagnostico={} e opcional: recebe contagens de aproximacoes de fonte/orientacao.
Licenca da dependencia PyMuPDF: AGPL ou licenca comercial da Artifex.
"""
from __future__ import annotations

import itertools
import math
import re
from collections import Counter, defaultdict

import pymupdf

from src.data.extrator import _juntar_letras_espacadas


def _nome_fonte(nome):
    return re.sub(r"^[A-Z]{6}\+", "", nome).replace(" ", "")


def _descidas(page):
    """Le metrica PDF; nao extrai nem carrega arquivos de fonte."""
    doc = page.parent
    saida = defaultdict(set)
    for fonte in page.get_fonts(full=True):
        xref, _, tipo, nome = fonte[:4]
        nome = _nome_fonte(nome)
        if tipo == "Type3":
            continue
        # Type0 pode guardar DescendantFonts em array ou em objeto indireto.
        if tipo == "Type0":
            kind, value = doc.xref_get_key(xref, "DescendantFonts")
            if kind == "xref":
                value = doc.xref_object(int(value.split()[0]))
            refs = re.findall(r"(\d+)\s+\d+\s+R", value)
            if refs:
                xref = int(refs[0])
        kind, value = doc.xref_get_key(xref, "FontDescriptor")
        if kind == "xref":
            kind, value = doc.xref_get_key(int(value.split()[0]), "Descent")
        elif kind == "dict":
            kind, value = doc.xref_get_key(xref, "FontDescriptor/Descent")
        if kind in ("int", "real"):
            saida[nome].add(-abs(float(value)) / 1000)
        elif nome in ("Symbol", "ZapfDingbats"):
            saida[nome].add(0.0)
        elif nome.startswith(("Helvetica", "Arial")):
            saida[nome].add(-0.207)
        elif nome.startswith(("Courier", "CourierNew")):
            saida[nome].add(-0.194)
        elif nome.startswith(("Times-", "TimesNewRoman,")) or nome == "TimesNewRoman":
            saida[nome].add(-0.217)
    return saida


def _matriz_pdfplumber(page):
    """PDF -> MediaBox rotacionada, incluindo a origem nao nula do pdfplumber."""
    x0, y0, x1, y1 = page.mediabox
    w, h = x1 - x0, y1 - y0
    rot = page.rotation % 360
    if rot == 0:
        saida = pymupdf.Matrix(1, 0, 0, -1, 0, h)
    if rot == 90:
        saida = pymupdf.Matrix(0, 1, 1, 0, 0, -2 * x0)
    elif rot == 180:
        saida = pymupdf.Matrix(-1, 0, 0, 1, x1 + x0, -2 * y0)
    elif rot == 270:
        saida = pymupdf.Matrix(0, -1, -1, 0, y1 + y0, w)
    # transformation_matrix perde o deslocamento de CropBox em paginas giradas
    # na versao 1.28.2. Construi a inversa sem alterar a pagina nem o documento.
    cx, cy = page.cropbox_position
    nativo_para_pdf = pymupdf.Matrix(1, 0, 0, -1, cx, y1 - cy)
    return nativo_para_pdf * saida


def _clusters(itens, campo, tolerancia=1.0):
    """Clusters encadeados, como dedupe_chars; nao usa buckets arredondados."""
    grupo, anterior = [], None
    for item in sorted(itens, key=lambda c: c[campo]):
        valor = item[campo]
        if anterior is not None and valor > anterior + tolerancia:
            yield grupo
            grupo = []
        grupo.append(item)
        anterior = valor
    if grupo:
        yield grupo


def _desduplicar(chars):
    grupos = defaultdict(list)
    for c in chars:
        grupos[(c['upright'], c['t'], c['font'], c['size'])].append(c)
    unicos = []
    for grupo in grupos.values():
        for ys in _clusters(grupo, 'top'):
            for xs in _clusters(ys, 'x0'):
                unicos.append(min(xs, key=lambda c: (c['top'], c['x0'], c['i'])))
    return sorted(unicos, key=lambda c: c['i'])


def palavras_da_pagina_pymupdf(page: pymupdf.Page, *, diagnostico=None):
    """Devolve palavras no contrato do extrator; page deve ser uma pagina PDF aberta.

    s e o ordinal da palavra antes do filtro de orientacao/centro, nao uma
    coordenada nem uma promessa de igualdade com o indice do outro parser.
    diagnostico, quando fornecido, e preenchido sem alterar o contrato de saida.
    """
    if not page.parent.is_pdf:
        raise ValueError("A pagina deve pertencer a um documento PDF.")
    diag = Counter()
    descidas = _descidas(page)
    matriz = _matriz_pdfplumber(page)
    chars = []
    rot = page.rotation % 360
    w, h = page.mediabox.width, page.mediabox.height
    if rot in (90, 270):
        w, h = h, w
    for span in sorted(page.get_texttrace(), key=lambda s: s['seqno']):
        dx, dy = span['dir']
        nome = _nome_fonte(span['font'])
        valores = descidas.get(nome, set())
        if len(valores) == 1:
            desc = next(iter(valores))
        else:
            desc = -abs(float(span['descender']))
            diag['fonte_ambigua' if valores else 'fonte_sem_descritor'] += len(span['chars'])
        size = float(span['size'])
        horizontal = abs(dy) < 1e-5 and abs(abs(dx) - 1) < 1e-5
        vertical = abs(dx) < 1e-5 and abs(abs(dy) - 1) < 1e-5
        if not (horizontal or vertical):
            diag['orientacao_aproximada'] += len(span['chars'])
        upright = (horizontal and rot in (0, 180)) or (vertical and rot in (90, 270))
        compostos = []
        for codigo, glifo, origem, bbox in span['chars']:
            texto = chr(codigo) if 0 <= codigo <= 0x10ffff else '\ufffd'
            # Ligadura: o primeiro componente tem a caixa inteira; os seguintes
            # tem glifo -1, mesma origem e largura zero. Mantem a caixa do glifo
            # inteiro para que o proximo caractere nao crie um vao artificial.
            if glifo == -1 and compostos and origem == compostos[-1][1]:
                compostos[-1][0] += texto
                diag['componentes_ligadura_unidos'] += 1
                continue
            compostos.append([texto, origem, bbox])
        for texto, origem, bbox in compostos:
            ox, oy = origem
            # Altura PDF: baseline + descent ate baseline + descent + size.
            # As larguras continuam sendo as do MuPDF, sem estimativa por texto.
            if horizontal:
                a, b = oy - dx * (1 + desc) * size, oy - dx * desc * size
                native = (bbox[0], min(a, b), bbox[2], max(a, b))
            elif vertical:
                a, b = ox + dy * (1 + desc) * size, ox + dy * desc * size
                native = (min(a, b), bbox[1], max(a, b), bbox[3])
            else:
                native = bbox
            caixa = pymupdf.Rect(native) * matriz
            valores_caixa = (*caixa, size)
            if not all(math.isfinite(v) for v in valores_caixa) or size <= 0:
                diag['caractere_nao_finito'] += 1
                continue
            chars.append({'t': texto, 'x0': float(caixa.x0), 'x1': float(caixa.x1),
                          'top': float(caixa.y0), 'bottom': float(caixa.y1), 'upright': upright,
                          'font': nome, 'size': size, 'i': len(chars)})
    antes = len(chars)
    chars = _desduplicar(chars)
    diag['caracteres_desduplicados'] = antes - len(chars)
    palavras = []
    ordinal = 0

    def fechar(atual):
        nonlocal ordinal
        if not atual:
            return
        palavra = {'t': ''.join(c['t'] for c in atual),
                   'x0': min(c['x0'] for c in atual), 'x1': max(c['x1'] for c in atual),
                   'top': min(c['top'] for c in atual), 'bottom': max(c['bottom'] for c in atual),
                   's': ordinal}
        ordinal += 1
        palavra['t'] = palavra['t'].strip().translate(str.maketrans(
            {'\ufb00': 'ff', '\ufb01': 'fi', '\ufb02': 'fl', '\ufb03': 'ffi',
             '\ufb04': 'ffl', '\ufb05': 'st', '\ufb06': 'st'}))
        cx = (palavra['x0'] + palavra['x1']) / 2
        cy = (palavra['top'] + palavra['bottom']) / 2
        if atual[0]['upright'] and palavra['t'] and 0 <= cx <= w and 0 <= cy <= h:
            palavras.append(palavra)

    for _, grupo in itertools.groupby(chars, key=lambda c: c['upright']):
        atual = []
        for c in grupo:
            if c['t'].isspace():
                fechar(atual)
                atual = []
                continue
            if atual:
                ant = atual[-1]
                if (c['x0'] < ant['x0'] or c['x0'] > ant['x1'] + 1.5
                        or abs(c['top'] - ant['top']) > 2):
                    fechar(atual)
                    atual = []
            atual.append(c)
        fechar(atual)
    if diagnostico is not None:
        diagnostico.update(diag)
    return _juntar_letras_espacadas(palavras)
