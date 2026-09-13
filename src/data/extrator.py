"""
Extrator de blocos de texto com bounding boxes a partir de PDFs digitais.

Para cada pagina, produz:
  - blocos de texto (paragrafos/trechos de coluna) com bbox [x0, top, x1, bottom]
  - tres ordens candidatas para esses blocos:

    stream  Ordem do FLUXO DE CONTEUDO do PDF -- a sequencia em que o software
            que gerou o arquivo escreveu o texto. Obtida com
            extract_words(use_text_flow=True). Em muitos geradores ela coincide
            com a ordem de leitura; em outros e arbitraria.

    naive   Ordenacao geometrica ingenua: de cima para baixo, da esquerda para
            a direita. E o que se obtem ao ordenar caixas por (top, x0) --
            baseline tipica de pipelines YOLO + OCR. Em multicoluna, intercala
            as colunas linha a linha.

    xycut   Heuristica XY-cut recursiva (Nagy & Seth, 1984; Ha et al., 1995)
            com deteccao de colunas por calhas verticais e blocos largos
            (cabecalhos, titulos) tratados como separadores de secao.

ATENCAO: o extract_words() PADRAO do pdfplumber (use_text_flow=False) ja
devolve as palavras pre-ordenadas geometricamente, e nao na ordem do arquivo.
Por isso a ordem "crua do PDF" precisa ser obtida com use_text_flow=True.

Segmentacao (versao v3, 2026-09-12, a partir das notas do Golden v1):
  palavras -> faixas de linha de base -> linhas (cortadas nas calhas globais, nas calhas
  locais e em vaos muito grandes) -> blocos por coluna. Regioes de TABELA, dadas por um
  detector de layout sobre a imagem da pagina (src/data/layout.py), viram um bloco cada.
  Blocos sem letra nem digito (separadores) sao descartados. Sem as regioes de tabela
  (tabelas=None) a pagina e segmentada so pelas regras, e stats["layout"] fica False.

Uso:
    python src/data/extrator.py --pdfs-por-uf 20 --paginas-por-pdf 6 --workers 6
"""
from __future__ import annotations

import os
import re
import sys
import json
import glob
import time
import bisect
import random
import argparse
import statistics
import warnings
from multiprocessing import Pool

warnings.filterwarnings("ignore")

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
SAIDA = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos")

RE_CID = re.compile(r"\(cid:\d+\)")
# Palavra cortada no fim da linha: hifen COLADO na palavra e continuacao em minuscula.
RE_TRANSLINEACAO = re.compile(r"(\w{2,})-\s+([a-zà-ÿ])")
# Espaco antes de pontuacao, criado ao emendar uma entrada em negrito ("SAUDE , no uso").
RE_ESPACO_PONT = re.compile(r"\s+([,.;:!?)])")
# Letra ou digito (unicode): bloco sem nenhum e separador grafico ("*** *** ***", "-", "....").
RE_ALFANUM = re.compile(r"[^\W_]")
# Pedaco de palavra com espacamento entre letras: 1 ou 2 letras, com ponto ou dois-pontos final
# opcional ("w.", "E:"). Virgula nao entra: "alineas a, b e c" e enumeracao, nao titulo espacado.
RE_LETRAS = re.compile(r"^[^\W\d_]{1,2}[.:]?$")

# UFs sabidamente inutilizaveis (ver docs/ACERVO.md): 86% do texto ilegivel.
UFS_EXCLUIDAS = {"official_diary_pi"}
# Arquivos auxiliares do professor que nao sao diarios limpos.
PADROES_EXCLUIDOS = ("apis_pagas", "json_atos", "bounding_boxes", "Anotado")

MIN_BLOCOS = 3
MAX_BLOCOS = 200
MAX_PROP_CID = 0.05


# ---------------------------------------------------------------------------
# Palavras -> linhas -> blocos
# ---------------------------------------------------------------------------

def palavras_da_pagina(page):
    """Palavras em ordem de fluxo do PDF, com o indice de fluxo em 's'."""
    try:
        page = page.dedupe_chars(tolerance=1)   # remove "negrito falso" (texto impresso duas vezes)
    except Exception:
        pass
    brutas = page.extract_words(use_text_flow=True, keep_blank_chars=False,
                                x_tolerance=1.5, y_tolerance=2)
    W, H = float(page.width), float(page.height)
    saida = []
    for i, w in enumerate(brutas):
        if not w.get("upright", True):          # texto rotacionado (ex.: margem vertical)
            continue
        t = w["text"].strip()
        if not t:
            continue
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        if not (0 <= cx <= W and 0 <= cy <= H):   # fora da area visivel
            continue
        saida.append({"t": t, "x0": float(w["x0"]), "x1": float(w["x1"]),
                      "top": float(w["top"]), "bottom": float(w["bottom"]), "s": i})
    return _juntar_letras_espacadas(saida)


def _juntar_letras_espacadas(ws, min_pedacos=4, vao_letras=2.5, vao_palavra=1.8, frac_letra_unica=0.75):
    """"R E S O L V E:" -> "RESOLVE:"; "PA R E C E R" -> "PARECER".

    Titulo com espacamento entre letras sai do pdfplumber como uma palavra por letra (o vao
    passa do x_tolerance). Junta-se uma sequencia de pelo menos `min_pedacos` pedacos de ate
    duas letras, na mesma linha e com a mesma altura, cada um a ate `vao_letras` larguras de
    letra do anterior, desde que pelo menos `frac_letra_unica` deles sejam UMA letra so. Dentro
    da sequencia, um vao maior que `vao_palavra` vezes o vao tipico separa palavras
    ("S E M   T E M P O" -> "SEM TEMPO").

    A exigencia de letra unica e o que separa titulo espacado de texto corrido: so o tamanho
    dos pedacos colava "e se eu me" em "eseeume", "I, II e XI do" (Golden v1, AC) e siglas em
    celula de tabela ("SP RJ MG ES"). Num titulo espacado quase todo pedaco e uma letra; o
    "PA" de "PA R E C E R" e o raro par que o PDF nao separou.
    """
    if len(ws) < min_pedacos:
        return ws
    linhas = []
    for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
        for L in reversed(linhas[-8:]):
            if abs(L[0]["top"] - w["top"]) <= 1.0 and abs(L[0]["bottom"] - w["bottom"]) <= 1.0:
                L.append(w)
                break
        else:
            linhas.append([w])

    def largura_letra(w):
        return (w["x1"] - w["x0"]) / max(1, sum(ch.isalpha() for ch in w["t"]))

    fundidas, removidas = [], set()

    def fechar(seq):
        if len(seq) < min_pedacos:
            return
        unicas = sum(1 for w in seq if sum(ch.isalpha() for ch in w["t"]) == 1)
        if unicas < frac_letra_unica * len(seq):
            return
        # par de letras so vale com a mesma caixa ("PA" de "PA R E C E R"); "Sr." e abreviatura
        if any(len(L) == 2 and not (L.isupper() or L.islower())
               for L in ("".join(ch for ch in w["t"] if ch.isalpha()) for w in seq)):
            return
        vaos = [b["x0"] - a["x1"] for a, b in zip(seq, seq[1:])]
        tipico = max(0.3, statistics.median(vaos))
        grupos, atual = [], [seq[0]]
        for vao, w in zip(vaos, seq[1:]):
            if vao > vao_palavra * tipico:
                grupos.append(atual)
                atual = []
            atual.append(w)
        grupos.append(atual)
        for g in grupos:
            if len(g) < 2:
                continue
            fundidas.append({"t": "".join(w["t"] for w in g), "x0": g[0]["x0"], "x1": g[-1]["x1"],
                             "top": min(w["top"] for w in g), "bottom": max(w["bottom"] for w in g),
                             "s": min(w["s"] for w in g)})
            removidas.update(id(w) for w in g)

    for L in linhas:
        seq = []
        for w in sorted(L, key=lambda w: w["x0"]):
            cabe = RE_LETRAS.match(w["t"]) is not None
            if cabe and seq and -0.5 <= w["x0"] - seq[-1]["x1"] <= vao_letras * largura_letra(seq[-1]):
                seq.append(w)
                continue
            fechar(seq)
            seq = [w] if cabe else []
        fechar(seq)
    if not fundidas:
        return ws
    return sorted([w for w in ws if id(w) not in removidas] + fundidas, key=lambda w: w["s"])


def _faixas_de_base(ws, janela=60):
    """Palavras na mesma linha de base, agrupadas SO pela sobreposicao vertical.

    Nenhum teste horizontal aqui: uma faixa pode atravessar a pagina inteira e conter
    palavras das duas colunas. Quem separa colunas e _calhas(), logo abaixo. A faixa e
    ancorada na extensao vertical da PRIMEIRA palavra: sem a ancora a caixa cresce a
    cada palavra e acaba engolindo a linha de cima ou a de baixo.
    """
    faixas = []
    for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
        hw = w["bottom"] - w["top"]
        alvo = None
        for F in reversed(faixas[-janela:]):
            ov = min(F["a_bot"], w["bottom"]) - max(F["a_top"], w["top"])
            if ov > 0 and ov / min(F["a_bot"] - F["a_top"], hw) >= 0.5:
                alvo = F
                break
        if alvo is None:
            faixas.append({"a_top": w["top"], "a_bot": w["bottom"],
                           "top": w["top"], "bottom": w["bottom"], "ws": [w]})
        else:
            alvo["ws"].append(w)
            alvo["top"] = min(alvo["top"], w["top"])
            alvo["bottom"] = max(alvo["bottom"], w["bottom"])
    return _reatribuir_faixas(faixas, ws)


def _reatribuir_faixas(faixas, ws):
    """Segunda passada: cada palavra vai para a faixa, entre as que a sobrepoem, cujo CENTRO
    (mediana dos centros das suas palavras) esta mais perto do centro dela.

    A primeira passada processa as palavras por topo e prende cada uma a primeira faixa com
    sobreposicao suficiente. Quando as linhas de duas colunas estao deslocadas meia linha,
    uma palavra alguns decimos de ponto mais alta que as vizinhas -- "nº", por causa do "º"
    -- chega antes delas e cai na faixa da coluna ao lado. Ali ela vira linha e bloco de uma
    palavra, e a trava contra caixas que se cruzam impede o paragrafo de crescer por cima
    dela: no Golden v1 (MA), um paragrafo saiu em tres blocos mais o "nº". O centro separa
    bem os dois casos: 0,2 pt da propria linha contra ~5 pt da linha da outra coluna.
    Devolve as faixas em ordem de cima para baixo.
    """
    if len(faixas) < 2:
        return faixas
    for F in faixas:
        F["c"] = statistics.median((w["top"] + w["bottom"]) / 2 for w in F["ws"])
    ordem = sorted(faixas, key=lambda F: F["c"])
    centros = [F["c"] for F in ordem]
    novas = [[] for _ in ordem]
    for w in ws:
        hw = w["bottom"] - w["top"]
        cw = (w["top"] + w["bottom"]) / 2
        melhor, dmin = None, None
        for j in range(bisect.bisect_left(centros, cw - 2 * hw), bisect.bisect_right(centros, cw + 2 * hw)):
            F = ordem[j]
            ov = min(F["bottom"], w["bottom"]) - max(F["top"], w["top"])
            if ov <= 0 or ov / max(1e-6, min(F["a_bot"] - F["a_top"], hw)) < 0.5:
                continue
            d = abs(cw - F["c"])
            if dmin is None or d < dmin:
                melhor, dmin = j, d
        if melhor is None:                      # nao acontece: a faixa da propria palavra a sobrepoe
            melhor = min(range(len(ordem)), key=lambda j: abs(cw - ordem[j]["c"]))
        novas[melhor].append(w)
    saida = []
    for grupo in novas:
        if grupo:
            top, bot = min(w["top"] for w in grupo), max(w["bottom"] for w in grupo)
            saida.append({"a_top": top, "a_bot": bot, "top": top, "bottom": bot, "ws": grupo,
                          "c": statistics.median((w["top"] + w["bottom"]) / 2 for w in grupo)})
    return sorted(saida, key=lambda F: F["c"])


def _calhas(faixas, W, min_larg=6.0, tol=0.03, fracao=0.25):
    """Calhas verticais da pagina: faixas de x com pouquissima tinta em TODAS as linhas.

    E o unico criterio confiavel para cortar uma linha ao meio. Um limiar de distancia
    nao serve: em texto justificado o espaco entre palavras estica e chega a ficar tao
    largo quanto uma calha estreita, e a linha e picotada no meio do paragrafo. O que
    distingue os dois casos e a consistencia VERTICAL -- a calha e branca linha apos
    linha, o espaco esticado so naquela.

    O corte e RELATIVO, nao absoluto: numa pagina com muitos titulos de largura total
    a calha e cruzada por varias linhas (medido num boletim legislativo: 13 de 142) e
    um limite fixo baixo demais a perde -- mas a queda continua enorme, de ~65 linhas
    nas colunas para 13 na calha. Compara-se entao com a ocupacao TIPICA da pagina.
    """
    n_bins = int(W) + 2
    cont = [0] * n_bins
    for F in faixas:
        marcados = set()
        for w in F["ws"]:
            for b in range(max(0, int(w["x0"])), min(n_bins - 1, int(w["x1"]) + 1)):
                marcados.add(b)
        for b in marcados:
            cont[b] += 1
    ocupados = [c for c in cont if c > 0]
    tipica = statistics.median(ocupados) if ocupados else 0
    limite = max(max(1, int(tol * len(faixas))), fracao * tipica)
    calhas, ini = [], None
    for b in range(n_bins):
        if cont[b] <= limite:
            ini = b if ini is None else ini
        elif ini is not None:
            if b - ini >= min_larg:
                calhas.append((float(ini), float(b)))
            ini = None
    if ini is not None and n_bins - ini >= min_larg:
        calhas.append((float(ini), float(n_bins)))
    return calhas


def _cortes_locais(faixas, vao_max, larg_min, n_min=4, fator_espaco=1.5):
    """Vaos entre palavras vizinhas que sao CALHA LOCAL: pares (id(palavra), id(proxima)).

    A calha global (_calhas) exige que a faixa de x esteja branca na pagina inteira. Quando
    um trecho da pagina tem outro desenho de colunas -- o expediente no rodape do diario do
    RJ, duas colunas de editais em cima de uma tabela larga em Barra do Pirai, texto em duas
    colunas embaixo de uma lista em SP --, nao sobra calha global e as linhas daquele trecho
    atravessam de uma coluna para a outra (as caixas que "pulam de coluna" do Golden v1).

    Aqui o teste e local, vao a vao. Partindo do vao, sobe e desce pelas faixas enquanto
    houver uma faixa branca de pelo menos `larg_min` pontos; conta as faixas atravessadas
    que tem palavra dos DOIS lados a ate `vao_max`. Com `n_min` faixas (contando a propria) o
    vao e calha. Dois cuidados:
      - so entra vao maior que `fator_espaco` larguras de letra das palavras vizinhas. Espaco
        normal nao e calha, mesmo quando por acaso se alinha com uma calha logo abaixo (o
        titulo de largura total do expediente do RJ era cortado entre "PARTE" e "II");
      - linha que nao chega ate a faixa branca nao interrompe a subida, mas tambem nao conta:
        sem isso, uma linha longa depois de uma lista de itens curtos seria cortada.
    Espaco esticado de texto justificado nao passa: a linha de cima ou a de baixo cobre o vao.
    """
    ints = [sorted((w["x0"], w["x1"]) for w in F["ws"]) for F in faixas]

    def livre(j, lo, hi):
        """Maior trecho de (lo, hi) sem tinta na faixa j."""
        melhor, x = (lo, lo), lo
        for a, b in ints[j]:
            if b <= lo or a >= hi:
                continue
            if a - x > melhor[1] - melhor[0]:
                melhor = (x, a)
            x = max(x, b)
        if hi - x > melhor[1] - melhor[0]:
            melhor = (x, hi)
        return melhor

    def atravessa(j, lo, hi):
        return (any(b <= lo + 0.5 and lo - b <= vao_max for _, b in ints[j])
                and any(a >= hi - 0.5 and a - hi <= vao_max for a, _ in ints[j]))

    def larg_letra(w):
        return (w["x1"] - w["x0"]) / max(1, len(w["t"]))

    cortes = set()
    for k, F in enumerate(faixas):
        palavras = sorted(F["ws"], key=lambda w: w["x0"])
        for ant, w in zip(palavras, palavras[1:]):
            a, b = ant["x1"], w["x0"]
            if b - a < max(larg_min, fator_espaco * max(larg_letra(ant), larg_letra(w))):
                continue
            # Um corredor so: o segundo sentido continua do trecho branco que sobrou no primeiro.
            # Reiniciar do vao somaria corredores em posicoes diferentes acima e abaixo, e um espaco
            # esticado de texto justificado poderia ser cortado com evidencia de dois lugares. Como
            # o primeiro sentido pode estreitar o trecho para um lado que nao continua no outro,
            # tentam-se as duas ordens (subir e depois descer; descer e depois subir).
            for sentidos in ((-1, 1), (1, -1)):
                cont, lo, hi = 1, a, b
                for passo in sentidos:
                    j = k + passo
                    while 0 <= j < len(faixas) and cont < n_min:
                        nlo, nhi = livre(j, lo, hi)
                        if nhi - nlo < larg_min:
                            break
                        lo, hi = nlo, nhi
                        if atravessa(j, lo, hi):
                            cont += 1
                        j += passo
                if cont >= n_min:
                    cortes.add((id(ant), id(w)))
                    break
    return cortes


def construir_linhas(ws, devolver_calhas=False):
    """Agrupa palavras em linhas, cortando so onde ha calha ou um vao muito grande.

    Tres criterios de corte, nesta ordem de confianca:
      1. passa uma CALHA entre as duas palavras (branca em quase todas as linhas);
      1b. o vao e uma CALHA LOCAL (_cortes_locais): branca naquele trecho da pagina;
      2. o vao e grande em termos absolutos. Medido no acervo, 95% das folgas DENTRO
         de um paragrafo cabem em 1,5 largura de caractere; o corte em 8 fica muito
         acima do espaco justificado mais esticado e ainda separa os elementos de um
         cabecalho (data à esquerda, titulo ao centro, numero à direita), que a calha
         nao pega porque ficam dentro da mesma regiao branca da pagina.
    """
    if not ws:
        return ([], []) if devolver_calhas else []
    W = max(w["x1"] for w in ws) + 2
    larg_char = statistics.median((w["x1"] - w["x0"]) / max(1, len(w["t"])) for w in ws)
    vao_max = max(20.0, 8 * larg_char)
    faixas = _faixas_de_base(ws)
    calhas = _calhas(faixas, W)
    locais = _cortes_locais(faixas, vao_max, larg_min=max(3.0, 0.8 * larg_char))
    grupos = []
    for F in faixas:
        palavras = sorted(F["ws"], key=lambda w: w["x0"])
        atual = [palavras[0]]
        for ant, w in zip(palavras, palavras[1:]):
            if (w["x0"] - ant["x1"] > vao_max
                    or any(ant["x1"] <= c0 and c1 <= w["x0"] for c0, c1 in calhas)
                    or (id(ant), id(w)) in locais):
                grupos.append(atual)
                atual = []
            atual.append(w)
        grupos.append(atual)
    linhas = [{"x0": min(w["x0"] for w in g), "x1": max(w["x1"] for w in g),
               "top": min(w["top"] for w in g), "bottom": max(w["bottom"] for w in g), "ws": g}
              for g in grupos if g]
    return (linhas, calhas) if devolver_calhas else linhas


def segmentar(ws, tabelas=None):
    """Palavras -> linhas -> blocos. As calhas da pagina valem para as duas etapas.

    tabelas: caixas [x0, top, x1, bottom] em pontos, do detector de layout
    (src/data/layout.py:tabelas). Cada uma vira UM bloco com as palavras cujo centro cai
    dentro dela; o resto da pagina e segmentado pelas regras, sem as palavras da tabela
    (que antes criavam calhas falsas e derrubavam as medianas de altura de linha). No Golden
    v1, a ordem anotada nunca intercalou pedacos de uma tabela com outro texto: para quem
    le, a tabela e uma unidade. A ordem das celulas dentro dela fica fora do escopo e o
    texto do bloco sai linha a linha.

    Por fim, descarta bloco sem letra nem digito: "*** *** ***", "-", "...." sao
    separadores graficos, que o Pedro anotou como "caixinhas sem nenhuma info".
    """
    tabelas = tabelas or []
    grupos_tabela, resto = [[] for _ in tabelas], []
    for w in ws:
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        k = next((k for k, (x0, y0, x1, y1) in enumerate(tabelas)
                  if x0 <= cx <= x1 and y0 <= cy <= y1), None)
        (resto if k is None else grupos_tabela[k]).append(w)
    blocos = []
    if resto:
        linhas, calhas = construir_linhas(resto, devolver_calhas=True)
        blocos = construir_blocos(linhas, calhas)
    blocos += [_bloco_tabela(g) for g in grupos_tabela if g]
    return [B for B in blocos if RE_ALFANUM.search(B["texto"])]


def _texto_do_bloco(B):
    """Texto do bloco: linhas de cima para baixo, palavras da esquerda para a direita."""
    partes = []
    for L in sorted(B["linhas"], key=lambda L: L["top"]):
        partes.append(" ".join(w["t"] for w in sorted(L["ws"], key=lambda w: w["x0"])))
    # "Prontua- rios" -> "Prontuarios": translineacao com hifen colado na palavra. Nao pega
    # tracos soltos ("IGUATU/CE - PERIODO"), que tem espaco antes do traco. Em seguida, o
    # espaco que sobra antes da pontuacao ao emendar uma entrada em negrito ("SAUDE , no uso").
    return RE_ESPACO_PONT.sub(r"\1", RE_TRANSLINEACAO.sub(r"\1\2", " ".join(partes)))


def _bloco_tabela(ws):
    """Um bloco com todas as palavras de uma regiao de tabela, lidas linha a linha."""
    linhas = [{"x0": min(w["x0"] for w in F["ws"]), "x1": max(w["x1"] for w in F["ws"]),
               "top": min(w["top"] for w in F["ws"]), "bottom": max(w["bottom"] for w in F["ws"]),
               "ws": F["ws"]} for F in _faixas_de_base(ws)]
    B = {"x0": min(w["x0"] for w in ws), "x1": max(w["x1"] for w in ws),
         "top": min(w["top"] for w in ws), "bottom": max(w["bottom"] for w in ws),
         "lh": statistics.median(w["bottom"] - w["top"] for w in ws),
         "col": -1, "centrada": False, "tabela": True, "linhas": linhas}
    B["texto"] = _texto_do_bloco(B)
    B["s"] = min(w["s"] for w in ws)
    return B


def _regioes(calhas, W):
    """Regioes de conteudo da pagina: o complemento das calhas."""
    reg, x = [], 0.0
    for c0, c1 in sorted(calhas):
        if c0 > x:
            reg.append((x, c0))
        x = max(x, c1)
    if x < W:
        reg.append((x, W))
    return reg


def _coluna(L, regioes):
    """Indice da regiao que CONTEM a linha; -1 se ela atravessa mais de uma (titulo, cabecalho)."""
    dentro = [k for k, (a, b) in enumerate(regioes) if L["x0"] >= a - 1 and L["x1"] <= b + 1]
    return dentro[0] if len(dentro) == 1 else -1


def _caixas_cruzam(a, b):
    """Duas caixas se cruzam em pelo menos 25% da area da menor (regra de reextrair.qualidade)."""
    aa = max(1e-6, (a["x1"] - a["x0"]) * (a["bottom"] - a["top"]))
    ab = max(1e-6, (b["x1"] - b["x0"]) * (b["bottom"] - b["top"]))
    iw = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
    ih = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
    return iw > 1 and ih > 1 and (iw * ih) / min(aa, ab) >= 0.25


def construir_blocos(linhas, calhas=None):
    """Agrupa linhas em blocos -- paragrafos, itens de ato e titulos -- dentro de cada coluna.

    Uma linha entra no bloco logo acima dela quando, ao mesmo tempo:
      1. esta na mesma COLUNA (regiao entre calhas). Sem isso, um titulo de largura total
         cresce e engole linhas de outra coluna;
      2. esta verticalmente colada (folga ate 0,8 altura de linha) e tem fonte parecida;
      3. se sobrepoe horizontalmente a pelo menos metade da largura da menor das duas;
      4. as duas sao do mesmo TIPO: linha curta e centralizada (titulo, "LOTE 139/2025",
         assinatura) ou linha de texto corrido. Sem isso, um titulo centralizado entra no
         paragrafo de baixo e dezenas de atos viram um bloco so;
      5. a caixa resultante nao cruza a de outro bloco ja formado. Caixas que se cruzam
         sao a assinatura de texto embaralhado dentro do bloco.

    Como se chegou nesta regra (tarefa T03, 2026-09-12), na amostra fixa de 44 paginas de
    src/data/avaliar_segmentacao.py:

      regra                                   blocos/pag  sobrepostos  paginas rejeitadas
      margem esquerda compativel (versao C)       61,4        4,9%          0
      so as regras 1 a 3 (versao B)               41,7       10,5%          1
      regras 1 a 5 (esta)                         52,8        5,7%          1 (SE, 224 blocos)

    A versao C picota primeira linha recuada e item de lista com continuacao na margem (no
    MA, de 36 para 85 blocos); a B funde texto corrido (o CE virou 2 blocos). O criterio de
    granularidade veio de quem anota o Golden: olhando as tres versoes das paginas-problema,
    o Pedro escolheu a de 36 blocos no MA e a de 66 no RJ; esta regra da 36 e 78. Parte da
    sobreposicao que sobra e real, como carimbo de assinatura digital impresso sobre o texto.
    """
    if not linhas:
        return []
    lh = statistics.median(L["bottom"] - L["top"] for L in linhas) or 1.0
    lc = statistics.median((w["x1"] - w["x0"]) / max(1, len(w["t"]))
                           for L in linhas for w in L["ws"]) or 4.0
    W = max(L["x1"] for L in linhas) + 2
    regioes = _regioes(calhas or [], W)
    col_de = {id(L): _coluna(L, regioes) for L in linhas}
    bordas_esq, bordas_dir = {}, {}
    for L in linhas:
        bordas_esq.setdefault(col_de[id(L)], []).append(L["x0"])
        bordas_dir.setdefault(col_de[id(L)], []).append(L["x1"])
    esq = {c: sorted(v)[int(0.1 * (len(v) - 1))] for c, v in bordas_esq.items()}
    dir_ = {c: sorted(v)[int(0.9 * (len(v) - 1))] for c, v in bordas_dir.items()}

    def centrada(L):
        """Linha curta e centralizada na sua coluna: titulo, cabecalho de ato, assinatura."""
        c = col_de[id(L)]
        largura = max(1.0, dir_[c] - esq[c])
        meio = (esq[c] + dir_[c]) / 2
        return ((L["x1"] - L["x0"]) < 0.7 * largura
                and abs((L["x0"] + L["x1"]) / 2 - meio) < 0.1 * largura
                and L["x0"] > esq[c] + 3 * lc)

    blocos = []
    for L in sorted(linhas, key=lambda L: (L["top"], L["x0"])):
        hL, col, cent = L["bottom"] - L["top"], col_de[id(L)], centrada(L)
        alvo = None
        for B in reversed(blocos[-40:]):
            if B["col"] != col:
                continue
            gap = L["top"] - B["bottom"]
            if gap < -0.5 * lh or gap > 0.8 * lh:
                continue
            if abs(hL - B["lh"]) > 0.4 * B["lh"]:      # mudanca de fonte = novo bloco
                continue
            ovx = min(B["x1"], L["x1"]) - max(B["x0"], L["x0"])
            if ovx < 0.5 * min(B["x1"] - B["x0"], L["x1"] - L["x0"]):
                continue
            if cent != B["centrada"]:
                continue
            nova = {"x0": min(B["x0"], L["x0"]), "x1": max(B["x1"], L["x1"]),
                    "top": B["top"], "bottom": max(B["bottom"], L["bottom"])}
            if any(O is not B and _caixas_cruzam(nova, O) for O in blocos):
                continue
            alvo = B
            break
        if alvo is None:
            blocos.append({"x0": L["x0"], "x1": L["x1"], "top": L["top"], "bottom": L["bottom"],
                           "lh": hL, "col": col, "centrada": cent, "linhas": [L]})
        else:
            alvo["linhas"].append(L)
            alvo["x0"] = min(alvo["x0"], L["x0"])
            alvo["x1"] = max(alvo["x1"], L["x1"])
            alvo["bottom"] = max(alvo["bottom"], L["bottom"])
    for B in blocos:
        B["texto"] = _texto_do_bloco(B)
        B["s"] = min(w["s"] for L in B["linhas"] for w in L["ws"])
    return blocos


# ---------------------------------------------------------------------------
# Ordens candidatas
# ---------------------------------------------------------------------------

def cortes_verticais(ids, B, calha_min=4.0, largura_min_frac=0.12):
    """Divide os blocos em grupos de colunas separados por calhas verticais vazias."""
    ordem = sorted(ids, key=lambda i: B[i]["x0"])
    grupos = [[ordem[0]]]
    fim = B[ordem[0]]["x1"]
    for i in ordem[1:]:
        if B[i]["x0"] > fim + calha_min:
            grupos.append([i])
        else:
            grupos[-1].append(i)
        fim = max(fim, B[i]["x1"])

    def largura(g):
        return max(B[i]["x1"] for i in g) - min(B[i]["x0"] for i in g)

    W = max(B[i]["x1"] for i in ids) - min(B[i]["x0"] for i in ids)
    # Uma "coluna" estreita demais (ex.: numeracao de artigos na margem) nao e
    # coluna de verdade: funde com a vizinha mais proxima.
    while len(grupos) > 1:
        k = min(range(len(grupos)), key=lambda j: largura(grupos[j]))
        if largura(grupos[k]) >= largura_min_frac * W:
            break
        if k == 0:
            j = 1
        elif k == len(grupos) - 1:
            j = k - 1
        else:
            gap_e = min(B[i]["x0"] for i in grupos[k]) - max(B[i]["x1"] for i in grupos[k - 1])
            gap_d = min(B[i]["x0"] for i in grupos[k + 1]) - max(B[i]["x1"] for i in grupos[k])
            j = k - 1 if gap_e <= gap_d else k + 1
        a, b = sorted((k, j))
        grupos[a] = grupos[a] + grupos[b]
        del grupos[b]
    return grupos


def xycut(ids, B, prof=0):
    """XY-cut recursivo: colunas da esquerda para a direita; blocos largos separam secoes."""
    if len(ids) <= 1 or prof > 60:
        return sorted(ids, key=lambda i: (B[i]["top"], B[i]["x0"]))
    grupos = cortes_verticais(ids, B)
    if len(grupos) > 1:
        saida = []
        for g in grupos:
            saida += xycut(g, B, prof + 1)
        return saida
    W = max(1e-6, max(B[i]["x1"] for i in ids) - min(B[i]["x0"] for i in ids))
    largos = [i for i in ids if (B[i]["x1"] - B[i]["x0"]) >= 0.6 * W]
    conj_largos = set(largos)
    estreitos = [i for i in ids if i not in conj_largos]
    if largos and estreitos:
        largos.sort(key=lambda i: B[i]["top"])
        centros = [(B[i]["top"] + B[i]["bottom"]) / 2 for i in largos]
        secoes = [[] for _ in range(len(largos) + 1)]
        for i in estreitos:
            cy = (B[i]["top"] + B[i]["bottom"]) / 2
            secoes[sum(1 for c in centros if c < cy)].append(i)
        saida = []
        for k in range(len(largos) + 1):
            saida += xycut(secoes[k], B, prof + 1)
            if k < len(largos):
                saida.append(largos[k])
        return saida
    return sorted(ids, key=lambda i: (B[i]["top"], B[i]["x0"]))


def estimar_colunas(B):
    """Numero de colunas do corpo da pagina (ignorando blocos largos)."""
    if not B:
        return 0
    W = max(b["x1"] for b in B) - min(b["x0"] for b in B)
    estreitos = [i for i, b in enumerate(B) if (b["x1"] - b["x0"]) < 0.6 * W]
    if len(estreitos) < 2:
        return 1
    return len(cortes_verticais(estreitos, B))


# ---------------------------------------------------------------------------
# Pagina -> registro JSON
# ---------------------------------------------------------------------------

def processar_pagina(page, uf, arquivo, n_pag, tabelas=None, palavras=False):
    """Pagina -> registro JSON.

    tabelas: caixas de tabela da pagina (src/data/layout.py:tabelas), ou None quando nao ha
             deteccao de layout para ela; stats["layout"] registra qual foi o caso.
    palavras: inclui "_palavras" (id do bloco -> [[texto, x0, top, x1, bottom], ...]), que o
              lote do Golden grava a parte para a anotacao sobreviver a outra segmentacao.
    """
    ws = palavras_da_pagina(page)
    if len(ws) < 5:
        return None, "sem_texto"
    prop_cid = sum(1 for w in ws if RE_CID.search(w["t"])) / len(ws)
    if prop_cid > MAX_PROP_CID:
        return None, "cid"
    blocos = segmentar(ws, tabelas)
    if not (MIN_BLOCOS <= len(blocos) <= MAX_BLOCOS):
        return None, "n_blocos"

    page_id = f"{uf}/{arquivo}#p{n_pag}"
    # IDs atribuidos por permutacao aleatoria semeada: nenhum id carrega a
    # ordem de fluxo nem a geometrica (evita vazamento para a LLM, que ve os ids).
    rng = random.Random(page_id)
    perm = list(range(len(blocos)))
    rng.shuffle(perm)
    ids = [f"b{perm[k]}" for k in range(len(blocos))]

    idx = list(range(len(blocos)))
    ordem_stream = [ids[i] for i in sorted(idx, key=lambda i: blocos[i]["s"])]
    ordem_naive = [ids[i] for i in sorted(idx, key=lambda i: (blocos[i]["top"], blocos[i]["x0"]))]
    ordem_xycut = [ids[i] for i in xycut(idx, blocos)]

    caixas = []
    for i in idx:
        c = {"id": ids[i], "text": blocos[i]["texto"],
             "bbox": [round(blocos[i]["x0"], 1), round(blocos[i]["top"], 1),
                      round(blocos[i]["x1"], 1), round(blocos[i]["bottom"], 1)]}
        if blocos[i].get("tabela"):
            c["tipo"] = "tabela"
        caixas.append(c)
    caixas.sort(key=lambda c: int(c["id"][1:]))

    registro = {
        "page_id": page_id,
        "uf": uf,
        "arquivo": arquivo,
        "pagina": n_pag,
        "dimensions": {"width": round(float(page.width), 1), "height": round(float(page.height), 1)},
        "bounding_boxes": caixas,
        "ordens": {"stream": ordem_stream, "naive": ordem_naive, "xycut": ordem_xycut},
        "stats": {"n_blocos": len(blocos), "n_palavras": len(ws),
                  "prop_cid": round(prop_cid, 4), "n_colunas": estimar_colunas(blocos),
                  "n_tabelas": sum(1 for B in blocos if B.get("tabela")),
                  "layout": tabelas is not None},
    }
    if palavras:
        registro["_palavras"] = {
            ids[i]: [[w["t"], round(w["x0"], 2), round(w["top"], 2), round(w["x1"], 2), round(w["bottom"], 2)]
                     for L in sorted(blocos[i]["linhas"], key=lambda L: L["top"])
                     for w in sorted(L["ws"], key=lambda w: w["x0"])]
            for i in idx}
    return registro, "ok"


def _processar_pedidos_pdf(tarefa):
    """Worker de processar_paginas: abre um PDF e segmenta as paginas pedidas."""
    import pdfplumber
    uf, arquivo, pedidos, palavras = tarefa          # pedidos: [(n_pag, tabelas ou None)]
    page_ids = [f"{uf}/{arquivo}#p{n}" for n, _ in pedidos]
    try:
        with pdfplumber.open(os.path.join(RAW, uf, *arquivo.split("/"))) as pdf:
            saida = []
            for pid, (n_pag, tabelas) in zip(page_ids, pedidos):
                try:
                    saida.append((pid,) + processar_pagina(pdf.pages[n_pag], uf, arquivo, n_pag, tabelas, palavras))
                except Exception as e:
                    saida.append((pid, None, f"erro_pagina: {e}"))
            return saida
    except Exception as e:
        return [(pid, None, f"pdf_ilegivel: {e}") for pid in page_ids]


def processar_paginas(paginas, tabelas=None, palavras=False, workers=3):
    """Segmenta paginas avulsas: [{"uf", "arquivo", "pagina", ...}] -> {page_id: (registro, motivo)}.

    tabelas: page_id -> caixas de tabela; None segmenta tudo sem layout. Um processo por PDF."""
    por_pdf = {}
    for p in paginas:
        pid = f"{p['uf']}/{p['arquivo']}#p{p['pagina']}"
        tab = None if tabelas is None else tabelas.get(pid, [])
        por_pdf.setdefault((p["uf"], p["arquivo"]), []).append((p["pagina"], tab))
    tarefas = [(uf, arq, sorted(ps, key=lambda x: x[0]), palavras) for (uf, arq), ps in por_pdf.items()]
    resultado = {}
    with Pool(max(1, min(workers, len(tarefas)))) as pool:
        for itens in pool.imap_unordered(_processar_pedidos_pdf, tarefas):
            for pid, reg, motivo in itens:
                resultado[pid] = (reg, motivo)
    return resultado


def processar_pdf(tarefa):
    """Worker: processa as paginas amostradas de um PDF."""
    import pdfplumber
    uf, caminho, paginas_por_pdf, semente, incluir_capa = tarefa
    arquivo = os.path.relpath(caminho, os.path.join(RAW, uf)).replace("\\", "/")
    registros, motivos = [], {}
    t0 = time.time()
    try:
        with pdfplumber.open(caminho) as pdf:
            n = len(pdf.pages)
            # pula a capa, exceto quando a coleta precisa do diario inteiro (ex.: experimento de RI)
            candidatas = list(range(n)) if (incluir_capa or n == 1) else list(range(1, n))
            rng = random.Random(semente)
            escolhidas = sorted(rng.sample(candidatas, min(paginas_por_pdf, len(candidatas))))
            for p in escolhidas:
                try:
                    reg, motivo = processar_pagina(pdf.pages[p], uf, arquivo, p)
                    motivos[motivo] = motivos.get(motivo, 0) + 1
                    if reg:
                        registros.append(reg)
                except Exception as e:
                    motivos["erro_pagina"] = motivos.get("erro_pagina", 0) + 1
    except Exception as e:
        motivos["pdf_corrompido"] = 1
    return uf, registros, motivos, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdfs-por-uf", type=int, default=20)
    ap.add_argument("--paginas-por-pdf", type=int, default=6)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ufs", nargs="*", help="restringe a estas UFs (padrao: todas)")
    ap.add_argument("--saida", default=SAIDA,
                    help="pasta dos .jsonl (padrao: data/processed/blocos). Coletas extras devem "
                         "usar outra pasta, para nao sobrescrever as paginas do protocolo")
    ap.add_argument("--incluir-capa", action="store_true",
                    help="processa tambem a primeira pagina de cada PDF (diario inteiro)")
    args = ap.parse_args()

    random.seed(args.seed)
    saida = os.path.abspath(args.saida)
    os.makedirs(saida, exist_ok=True)
    ufs = sorted(d for d in os.listdir(RAW)
                 if os.path.isdir(os.path.join(RAW, d)) and d.startswith("official_diary")
                 and d not in UFS_EXCLUIDAS)
    if args.ufs:
        ufs = [u for u in ufs if u in set(args.ufs)]

    tarefas = []
    for uf in ufs:
        pdfs = [p for p in glob.glob(os.path.join(RAW, uf, "**", "*.pdf"), recursive=True)
                if not any(x in p for x in PADROES_EXCLUIDOS)]
        pdfs.sort()
        for k, p in enumerate(random.sample(pdfs, min(args.pdfs_por_uf, len(pdfs)))):
            tarefas.append((uf, p, args.paginas_por_pdf, f"{args.seed}-{uf}-{k}", args.incluir_capa))

    print(f"[*] {len(ufs)} UFs, {len(tarefas)} PDFs, ate {args.paginas_por_pdf} paginas cada, "
          f"{args.workers} processos -> {saida}", flush=True)
    for uf in ufs:   # limpa execucoes anteriores
        alvo = os.path.join(saida, f"{uf}.jsonl")
        if os.path.exists(alvo):
            os.remove(alvo)

    t0 = time.time()
    motivos_tot, por_uf, feitos = {}, {}, 0
    with Pool(args.workers) as pool:
        for uf, registros, motivos, dt in pool.imap_unordered(processar_pdf, tarefas):
            feitos += 1
            for k, v in motivos.items():
                motivos_tot[k] = motivos_tot.get(k, 0) + v
            if registros:
                with open(os.path.join(saida, f"{uf}.jsonl"), "a", encoding="utf-8") as f:
                    for r in registros:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                por_uf[uf] = por_uf.get(uf, 0) + len(registros)
            if feitos % 25 == 0 or feitos == len(tarefas):
                print(f"  {feitos}/{len(tarefas)} PDFs | {sum(por_uf.values())} paginas uteis "
                      f"| {time.time()-t0:.0f}s", flush=True)

    print(f"\n[OK] {sum(por_uf.values())} paginas em {time.time()-t0:.0f}s -> {saida}")
    print(f"Motivos (paginas): {motivos_tot}")
    with open(os.path.join(saida, "_resumo_extracao.json"), "w", encoding="utf-8") as f:
        json.dump({"args": vars(args), "paginas_por_uf": por_uf, "motivos": motivos_tot,
                   "segundos": round(time.time() - t0, 1)}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
