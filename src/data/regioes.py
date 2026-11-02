"""
Segmentacao por REGIOES: caixas e classes de layout a partir das palavras do PDF, do detector de
layout (Docling Heron, src/data/layout.py) e dos blocos das regras (src/data/extrator.py).

E a pre-anotacao do Diamond (src/anotacao/preparar_diamond.py) e o candidato a segmentador v4.
Mede-se contra a anotacao humana do Diamond com src/eval/avaliar_diamond.py.

Etapas de propor():
  1. regioes do detector (score >= SCORE_MIN); uma regiao com a maior parte da area dentro de outra
     ja aceita e descartada (tabelas e figuras primeiro, depois por score);
  2. cada palavra vai para a regiao que contem o seu centro (tabela primeiro, senao a menor; figura
     nunca pega palavra); a caixa e ajustada as palavras; regiao sem palavra so fica se for figura;
  3. itens de lista vizinhos na mesma coluna viram uma regiao "lista";
  4. palavras que nenhuma regiao pegou ficam com os blocos v3 a que pertencem (origem "regras");
  5. regioes que, ja ajustadas, cobrem palavras uma da outra viram uma (alerta juntou_sobrepostas);
  6. (regras=True) regras tiradas das correcoes do Pedro no diamond_piloto (13/09/2026):
     - dividir_campos: uma caixa com varios campos em MAIUSCULAS ("ACORDANTE: ...", "OBJETO: ...") ou
       varios artigos ("Art. 1o", "§ 2o") e dividida onde a linha comeca um campo e a anterior termina a frase;
     - rotulo_com_valor: rotulo sozinho ("ELEMENTO DE DESPESA:") junta com o valor na mesma linha;
     - assinatura: nome e cargo (em uma ou em duas caixas curtas empilhadas) viram uma caixa assinatura;
     - titulos_empilhados (fora do padrao; so na ablacao): titulo quebrado em duas caixas empilhadas vira um;
     - local_e_data: "Porto Alegre, 24 de fevereiro de 2023." e texto, nao titulo.
     Uma juncao so acontece se a caixa nova nao cobrir palavra de outra regiao.
  7. (fundir=True) fundir_fragmentos: junta caixas MESMA CLASSE que o extrator repartiu sem motivo
     (marcas/cabecalho/rodape espurios; sobra de bloco em texto). Calibrado no diamond_teste sem
     ancoragem: reduz a super-segmentacao sem juntar vizinhos que o ouro mantem separados.
"""
from __future__ import annotations

import collections
import re
import statistics

SCORE_MIN = 0.45
SCORE_CONFIANTE = 0.55
CLASSES = ["titulo", "texto", "lista", "tabela", "assinatura", "cabecalho", "rodape", "figura", "outro"]
CLASSE_DETECTOR = {
    "title": "titulo", "section_header": "titulo", "text": "texto", "list_item": "lista",
    "table": "tabela", "document_index": "tabela", "page_header": "cabecalho", "page_footer": "rodape",
    "picture": "figura", "caption": "texto", "footnote": "texto", "formula": "texto", "code": "texto",
    "key_value_region": "texto", "form": "texto", "checkbox_selected": "texto", "checkbox_unselected": "texto",
}
PRIORIDADE = {"tabela": 0, "figura": 1}
RE_ALFANUM = re.compile(r"[0-9A-Za-zÀ-ÿ]")
# marcas de diagramacao que vazam na camada de texto (<@...>, <#...>, contPageBreak)
RE_MARCACAO = re.compile(r"^(?:<@[^>]+>|<#[^>]+>|contPageBreak.*)$", re.I)

# linha que comeca um campo: rotulo curto com inicial maiuscula seguido de dois-pontos
RE_CAMPO = re.compile(r"^([A-ZÀ-Ý][\wÀ-ÿºª°./()\-]*(?:\s+[\wÀ-ÿºª°./()\-]+){0,5}):(\s|$)")
RE_ARTIGO = re.compile(r"^(Art\.?\s*\d|ART\.?\s*\d|§\s*\d|Par[áa]grafo\s+[úu]nico|PAR[ÁA]GRAFO\s+[ÚU]NICO)")
RE_FIM_FRASE = re.compile(r"[.;:]\s*$")
RE_ROTULO_SO = re.compile(r"^[^:]{1,60}:$")
RE_CARGO = re.compile(
    r"\b(secret(?:[áÁ]ri[oa]|ario)|subsecret(?:[áÁ]ri[oa]|ario)|president[ea]|diretor[a]?|coordenador[a]?|prefeit[oa]|"
    r"gerente|chefe|procurador[a]?|deputad[oa]|vereador[a]?|representante|assessor[a]?|superintendente|"
    r"governador[a]?|ordenador[a]?|pregoeir[oa]|tesoureir[oa]|controlador[a]?|relator[a]?|comandante|"
    r"delegad[oa]|promotor[a]?|ju[íi]z[a]?|reitor[a]?|ministr[oa]|contador[a]?|auditor[a]?|gestor[a]?|"
    r"fiscal|pregoeir[oa]|leiloeir[oa]|administrador[a]?|supervisor[a]?|conselheir[oa]|ouvidor[a]?|"
    r"corregedor[a]?|defensor[a]?|comiss[ãa]o|matr[íi]cula|mat\.)", re.I)
RE_LOCAL_DATA = re.compile(
    r"^[A-ZÀ-Ý][\wÀ-ÿ .'/-]{1,60},\s*(em\s+)?\d{1,2}\s*[º°o]?\s+de\s+[A-Za-zçÇ]+\s+de\s+\d{4}\.?$")
CONECTIVOS = {"de", "da", "do", "das", "dos", "e", "d'", "di"}
# palavras de orgao, nao de nome de pessoa ("PODER LEGISLATIVO", "SECRETARIA DE SAUDE")
INSTITUICOES = {"poder", "estado", "prefeitura", "secretaria", "municipio", "município", "governo", "camara",
                "câmara", "tribunal", "fundacao", "fundação", "instituto", "departamento", "companhia",
                "universidade", "gabinete", "mesa", "comissao", "comissão", "conselho", "diario", "diário",
                "oficial", "legislativo", "executivo", "judiciario", "judiciário", "assembleia", "procuradoria",
                "controladoria", "coordenadoria", "diretoria", "superintendencia", "superintendência", "agencia",
                "agência", "autarquia", "empresa", "ltda", "eireli", "republica", "república"}
RE_DATA = re.compile(r"\d{1,2}\s*[º°o]?\s+de\s+[A-Za-zçÇ]+\s+de\s+\d{4}")
RE_CAMPO_COM_VALOR = re.compile(r"\S:\s*\S")

# Etapa 7 (fundir_fragmentos): junta caixas MESMA CLASSE que o extrator repartiu sem motivo.
# Calibrado no diamond_teste (11 paginas do zero, sem ancoragem): so as classes/folgas abaixo
# reduzem a super-segmentacao sem destruir vizinhos legitimos. Folga = vao vertical / altura de linha.
#   - marcas/cabecalho/rodape: fragmentos quase sempre espurios -> folga generosa;
#   - texto: o ouro mantem paragrafos curtos separados de proposito, entao so junta quando um dos
#     lados veio da sobra de bloco (origem "regras") e a folga e minima.
FUNDIR_LIVRE = ({"outro", "rodape", "cabecalho"}, 2.0, False)
FUNDIR_SOBRA = ({"texto"}, 0.6, True)
FUNDIR_OV_MIN = 0.6   # sobreposicao horizontal minima (fracao da largura menor) para juntar
VAO_LISTA_MULT = 1.6  # itens de lista a ate VAO_LISTA_MULT alturas de linha viram uma lista (etapa 3)


# ---------------------------------------------------------------------------
# Geometria
# ---------------------------------------------------------------------------

def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _intersecao(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _contem(b, x, y):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def _envelope(caixas):
    return [min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas)]


def _lado_a_lado(a, b):
    """Duas caixas em colunas diferentes: sem sobreposicao horizontal e com sobreposicao vertical."""
    return (min(a[2], b[2]) - max(a[0], b[0])) <= 0 and (min(a[3], b[3]) - max(a[1], b[1])) > 0


def _centro(w):
    return (w[1] + w[3]) / 2, (w[2] + w[4]) / 2


# ---------------------------------------------------------------------------
# Proposta (etapas 1 a 5)
# ---------------------------------------------------------------------------

def _resolver_sobreposicoes(regioes, palavras):
    """Depois de ajustar as caixas as palavras, uma caixa pode cobrir o centro de palavras de outra
    (o detector marca "PROCESSO No:" como titulo dentro de uma linha de texto, e a caixa de texto
    ajustada passa por cima). A regra do Diamond e uma palavra em uma caixa so: as duas regioes
    viram uma, com a classe da que tem mais palavras, e o alerta juntou_sobrepostas. Figura fica
    de fora (pode conter texto)."""
    centro = [_centro(w) for w in palavras]

    def disputam(a, b):
        if _intersecao(a["bbox"], b["bbox"]) <= 0:
            return False
        return (any(_contem(b["bbox"], *centro[k]) for k in a["palavras"])
                or any(_contem(a["bbox"], *centro[k]) for k in b["palavras"]))

    regioes = list(regioes)
    mudou = True
    while mudou:
        mudou = False
        for i, a in enumerate(regioes):
            if a["classe"] == "figura":
                continue
            for b in regioes[i + 1:]:
                if b["classe"] == "figura" or not disputam(a, b):
                    continue
                maior, menor = (a, b) if len(a["palavras"]) >= len(b["palavras"]) else (b, a)
                maior["palavras"] = maior["palavras"] + menor["palavras"]
                maior["bbox"] = _envelope([palavras[k][1:5] for k in maior["palavras"]])
                scores = [s for s in (maior["score"], menor["score"]) if s is not None]
                maior["score"] = min(scores) if scores else None
                if maior["origem"] != menor["origem"]:
                    maior["origem"] = "detector"
                maior["juntou"] = maior.get("juntou", 0) + 1 + menor.get("juntou", 0)
                regioes.remove(menor)
                mudou = True
                break
            if mudou:
                break
    return regioes


def _altura_linha(palavras):
    hs = sorted(w[4] - w[2] for w in palavras) or [10.0]
    return hs[len(hs) // 2]


def _fundir_fragmentos(regioes, palavras):
    """Etapa 7: junta caixas MESMA CLASSE, mesma coluna e verticalmente contiguas que o extrator
    repartiu (ver FUNDIR_LIVRE/FUNDIR_SOBRA). Opera nas regioes internas (com "palavras" e "origem");
    a caixa nova e o envelope e as palavras somam. Iterativo ate estabilizar."""
    h = _altura_linha(palavras)
    rs = [dict(r) for r in regioes]
    for classes, folga_max, exige_sobra in (FUNDIR_LIVRE, FUNDIR_SOBRA):
        mudou = True
        while mudou:
            mudou = False
            rs.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
            for i, a in enumerate(rs):
                if a["classe"] not in classes:
                    continue
                for j, b in enumerate(rs):
                    if i == j or b["classe"] != a["classe"]:
                        continue
                    if exige_sobra and "regras" not in (a.get("origem"), b.get("origem")):
                        continue
                    ab, bb = a["bbox"], b["bbox"]
                    folga = (bb[1] - ab[3]) / h        # b logo abaixo de a
                    if folga < -0.6 or folga > folga_max:
                        continue
                    sobre_x = min(ab[2], bb[2]) - max(ab[0], bb[0])
                    larg_min = min(ab[2] - ab[0], bb[2] - bb[0])
                    if larg_min <= 0 or sobre_x < FUNDIR_OV_MIN * larg_min:
                        continue
                    a["bbox"] = _envelope([ab, bb])
                    a["palavras"] = a.get("palavras", []) + b.get("palavras", [])
                    a["origem"] = "detector" if "detector" in (a.get("origem"), b.get("origem")) else a.get("origem")
                    if a.get("score") is not None and b.get("score") is not None:
                        a["score"] = min(a["score"], b["score"])
                    a["regras"] = sorted(set(a.get("regras", []) + b.get("regras", []) + ["fundir_fragmentos"]))
                    rs.pop(j)
                    mudou = True
                    break
                if mudou:
                    break
    return rs


def propor(palavras, blocos_v3, detector, regras=False, fundir=True):
    """palavras: [[t, x0, top, x1, bottom, bloco]]; blocos_v3: [{"id", "bbox", "tipo"}];
    detector: [{"rotulo", "score", "bbox"}] -> lista de regioes propostas.
    regras=False reproduz a proposta do diamond_piloto; regras=True aplica a etapa 6 inteira; um
    conjunto de nomes (REGRAS) aplica so essas, para a ablacao."""
    cands = [dict(r, classe=CLASSE_DETECTOR.get(r["rotulo"], "texto")) for r in detector if r["score"] >= SCORE_MIN]
    cands.sort(key=lambda r: (PRIORIDADE.get(r["classe"], 9), -r["score"]))
    aceitas = []
    for r in cands:
        area = max(1e-6, _area(r["bbox"]))
        if any(_intersecao(r["bbox"], m["bbox"]) >= 0.6 * area for m in aceitas):
            continue
        aceitas.append({**r, "palavras": []})

    livres = []
    for k, w in enumerate(palavras):
        cx, cy = _centro(w)
        # figura nao pega palavra: o detector chama de figura cabecalho decorado com texto de verdade,
        # e o texto precisa de caixa propria (se sobrar, cai nos blocos v3 abaixo)
        dentro = [m for m in aceitas if m["classe"] != "figura" and _contem(m["bbox"], cx, cy)]
        if not dentro:
            livres.append(k)
            continue
        tab = [m for m in dentro if m["classe"] == "tabela"]
        alvo = tab[0] if tab else min(dentro, key=lambda m: _area(m["bbox"]))
        alvo["palavras"].append(k)

    regioes = []
    for m in aceitas:
        if m["palavras"]:
            caixa = _envelope([palavras[k][1:5] for k in m["palavras"]])
        elif m["classe"] == "figura":
            caixa = list(m["bbox"])
        else:
            continue
        regioes.append({"classe": m["classe"], "bbox": caixa, "origem": "detector", "rotulo": m["rotulo"],
                        "score": m["score"], "palavras": m["palavras"]})

    # itens de lista vizinhos na mesma coluna -> uma lista
    listas = sorted((r for r in regioes if r["classe"] == "lista"), key=lambda r: r["bbox"][1])
    alturas = sorted(w[4] - w[2] for w in palavras) or [10.0]
    vao_max = VAO_LISTA_MULT * alturas[len(alturas) // 2]
    fundidas = []
    for r in listas:
        alvo = None
        for f in fundidas:
            a, b = f["bbox"], r["bbox"]
            sobre_x = min(a[2], b[2]) - max(a[0], b[0])
            if sobre_x >= 0.5 * min(a[2] - a[0], b[2] - b[0]) and 0 <= b[1] - a[3] <= vao_max:
                alvo = f
                break
        if alvo is None:
            fundidas.append({**r, "palavras": list(r["palavras"]), "n_itens": 1})
        else:
            alvo["bbox"] = _envelope([alvo["bbox"], r["bbox"]])
            alvo["palavras"] += r["palavras"]
            alvo["score"] = min(alvo["score"], r["score"])
            alvo["n_itens"] += 1
    regioes = [r for r in regioes if r["classe"] != "lista"] + fundidas

    # palavras que nenhuma regiao pegou: ficam com o bloco v3 de cada uma
    por_bloco = {}
    for k in livres:
        por_bloco.setdefault(palavras[k][5], []).append(k)
    tipo_v3 = {i: b.get("tipo") for i, b in enumerate(blocos_v3)}
    for bloco, ks in sorted(por_bloco.items()):
        if bloco < 0:
            continue                      # separador descartado pelo extrator: fica sem caixa
        regioes.append({"classe": "tabela" if tipo_v3.get(bloco) == "tabela" else "texto",
                        "bbox": _envelope([palavras[k][1:5] for k in ks]), "origem": "regras",
                        "rotulo": None, "score": None, "palavras": ks})

    regioes = _resolver_sobreposicoes(regioes, palavras)
    if regras:
        if regras == "v2":
            reg_aplicar = REGRAS_V2
        elif regras == "v3" or regras is True:
            reg_aplicar = REGRAS_V3
        else:
            reg_aplicar = set(regras)
        regioes = aplicar_regras(regioes, palavras, reg_aplicar)
    if fundir:
        regioes = _fundir_fragmentos(regioes, palavras)
    regioes.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
    saida = []
    for i, r in enumerate(regioes, 1):
        alertas = []
        if r.get("juntou"):
            alertas.append("juntou_sobrepostas")
        if r["origem"] == "regras":
            alertas.append("so_regras")
        elif r["score"] is not None and r["score"] < SCORE_CONFIANTE:
            alertas.append("baixa_confianca")
        if r["classe"] not in ("tabela", "figura"):
            caixas_v3 = {palavras[k][5] for k in r["palavras"] if palavras[k][5] >= 0}
            cx = [blocos_v3[b]["bbox"] for b in caixas_v3]
            if any(_lado_a_lado(a, b) for j, a in enumerate(cx) for b in cx[j + 1:]):
                alertas.append("atravessa_colunas")
        reg = {"id": f"p{i}", "classe": r["classe"], "bbox": [round(v, 1) for v in r["bbox"]],
               "origem": r["origem"], "rotulo_detector": r["rotulo"], "score": r["score"], "alertas": alertas}
        if r.get("regras"):
            reg["regras"] = sorted(set(r["regras"]))
        saida.append(reg)
    return saida


# ---------------------------------------------------------------------------
# Etapa 6: regras das correcoes humanas
# ---------------------------------------------------------------------------

def linhas(palavras, ks):
    """Palavras de uma regiao -> linhas de cima para baixo: [{"ks", "texto", "bbox", "h"}]."""
    saida = []
    for k in sorted(ks, key=lambda k: _centro(palavras[k])[1]):
        w = palavras[k]
        cy, h = _centro(w)[1], w[4] - w[2]
        if saida and abs(cy - saida[-1]["cy"]) < 0.5 * max(h, saida[-1]["h"]):
            saida[-1]["ks"].append(k)
            saida[-1]["h"] = max(saida[-1]["h"], h)
        else:
            saida.append({"cy": cy, "h": h, "ks": [k]})
    for L in saida:
        L["ks"].sort(key=lambda k: palavras[k][1])
        L["texto"] = " ".join(palavras[k][0] for k in L["ks"])
        L["bbox"] = _envelope([palavras[k][1:5] for k in L["ks"]])
    return saida


RE_ROMANO = re.compile(r"^[IVXLC]+\s*[-–.)]?\s+")


def comeca_campo(texto):
    """Linha que abre um campo ou um artigo, como o Pedro dividiu no diamond_piloto: rotulo em
    MAIUSCULAS ("OBJETO: ...", "BASE LEGAL: ...") ou "Art. 1o". Nao abrem: rotulo com minusculas
    dentro de registro ou lista ("Mat.:", "Cargo:", "E-mail:"), item numerado com romano
    ("VIII OBJETO:") e verbo sozinho na linha ("RESOLVE:")."""
    if RE_ARTIGO.match(texto):
        return True
    m = RE_CAMPO.match(texto)
    if not m or RE_ROMANO.match(texto):
        return False
    rotulo, resto = m.group(1), texto[m.end():].strip()
    letras = [c for c in rotulo if c.isalpha()]
    if len(letras) < 2 or rotulo != rotulo.upper():
        return False
    return len(rotulo.split()) >= 2 or bool(resto)


def _parece_nome(texto):
    """2 a 7 palavras, sem digito nem dois-pontos, quase todas com inicial maiuscula."""
    if any(c.isdigit() for c in texto) or ":" in texto:
        return False
    toks = [t.strip(",.;") for t in texto.split()]
    toks = [t for t in toks if t]
    if not 2 <= len(toks) <= 7:
        return False
    uteis = [t for t in toks if t.lower() not in CONECTIVOS]
    if any(t.lower() in INSTITUICOES for t in uteis):
        return False
    return bool(uteis) and sum(t[0].isupper() for t in uteis) >= 0.8 * len(uteis) and not RE_CARGO.search(texto)


def eh_assinatura(ls):
    """Linhas de uma regiao curta: um nome e um cargo, ou 'NOME, Cargo' numa linha so."""
    if not 1 <= len(ls) <= 3 or sum(len(L["ks"]) for L in ls) > 18:
        return False
    textos = [L["texto"] for L in ls]
    # local e data, campo com valor ("Presidente: Fulano", "Tel.: (91) ...") e numero longo (processo,
    # telefone) nao sao assinatura
    if any(RE_LOCAL_DATA.match(t) or RE_DATA.search(t) or RE_CAMPO_COM_VALOR.search(t)
           or sum(c.isdigit() for c in t) >= 5 for t in textos):
        return False
    if len(ls) == 1:
        t = textos[0]
        if "," not in t:
            return False
        nome, cargo = t.split(",", 1)
        return _parece_nome(nome) and bool(RE_CARGO.search(cargo)) and nome.strip() == nome.strip().upper()
    # exatamente um nome: duas assinaturas coladas (nome, cargo, nome) ficam separadas
    return sum(_parece_nome(t) for t in textos) == 1 and any(RE_CARGO.search(t) for t in textos)


def _cobre_outra(bbox, regioes, palavras, excluir):
    for r in regioes:
        if r in excluir or r["classe"] == "figura":
            continue
        if _intersecao(bbox, r["bbox"]) > 0 and any(_contem(bbox, *_centro(palavras[k])) for k in r["palavras"]):
            return True
    return False


def _juntar(a, b, classe, regra, regioes, palavras):
    """Junta b em a se a caixa nova nao cobrir palavra de outra regiao. Devolve True se juntou."""
    ks = a["palavras"] + b["palavras"]
    caixa = _envelope([palavras[k][1:5] for k in ks])
    if _cobre_outra(caixa, regioes, palavras, (a, b)):
        return False
    scores = [s for s in (a["score"], b["score"]) if s is not None]
    a.update(palavras=ks, bbox=caixa, classe=classe, score=min(scores) if scores else None,
             origem="detector" if "detector" in (a["origem"], b["origem"]) else a["origem"],
             regras=a.get("regras", []) + b.get("regras", []) + [regra])
    regioes.remove(b)
    return True


REGRAS = ("outro_marcacao", "dividir_campos", "local_e_data", "rotulo_com_valor", "assinatura", "titulos_empilhados")
REGRAS_V2 = ("dividir_campos", "local_e_data", "rotulo_com_valor", "assinatura")
REGRAS_V3 = ("outro_marcacao", "dividir_campos", "local_e_data", "rotulo_com_valor", "assinatura")
# titulos_empilhados fica fora do padrao: na ablacao do diamond_piloto piorou os titulos (revocacao
# 0,85 -> 0,82) sem ganho no F1
REGRAS_PADRAO = REGRAS_V3


def aplicar_regras(regioes, palavras, ativas=None):
    if ativas is None or ativas is True or ativas == "v3":
        ativas = set(REGRAS_V3)
    elif ativas == "v2":
        ativas = set(REGRAS_V2)
    else:
        ativas = set(ativas)
    alt = statistics.median([w[4] - w[2] for w in palavras]) if palavras else 10.0
    regioes = list(regioes)

    # outro_marcacao: marcas de diagramacao saem da regiao e formam regiao(oes) outro por linha
    if "outro_marcacao" in ativas:
        novas = []
        for r in regioes:
            if not r.get("palavras"):
                novas.append(r)
                continue
            ks_marc = [k for k in r["palavras"] if RE_MARCACAO.match(palavras[k][0])]
            if not ks_marc:
                novas.append(r)
                continue
            ks_resto = [k for k in r["palavras"] if not RE_MARCACAO.match(palavras[k][0])]
            if ks_resto:
                # marca no meio da linha ("NOME <#E.G.B#123/> Cargo") continua dentro da caixa que
                # sobra: tirar dali deixaria a palavra em duas regioes (AP e SE, 13/09)
                resto = _envelope([palavras[k][1:5] for k in ks_resto])
                dentro = [k for k in ks_marc if _contem(resto, *_centro(palavras[k]))]
                ks_resto = sorted(ks_resto + dentro)
                ks_marc = [k for k in ks_marc if k not in dentro]
                if not ks_marc:
                    novas.append(r)
                    continue
                novas.append({
                    **r,
                    "palavras": ks_resto,
                    "bbox": _envelope([palavras[k][1:5] for k in ks_resto]),
                    "regras": r.get("regras", []) + ["outro_marcacao"],
                })
            for L in linhas(palavras, ks_marc):
                novas.append({
                    **r,
                    "classe": "outro",
                    "palavras": L["ks"],
                    "bbox": _envelope([palavras[k][1:5] for k in L["ks"]]),
                    "regras": r.get("regras", []) + ["outro_marcacao"],
                })
        regioes = novas

    # dividir_campos
    novas = []
    for r in regioes:
        if "dividir_campos" not in ativas or r["classe"] not in ("texto", "titulo") or len(r["palavras"]) < 4:
            novas.append(r)
            continue
        ls = linhas(palavras, r["palavras"])
        largura = r["bbox"][2] - r["bbox"][0]
        partes = [[ls[0]]]
        for i in range(1, len(ls)):
            ant = ls[i - 1]
            fecha = RE_FIM_FRASE.search(ant["texto"]) or (ant["bbox"][2] - ant["bbox"][0]) < 0.8 * largura
            if comeca_campo(ls[i]["texto"]) and fecha:
                partes.append([ls[i]])
            else:
                partes[-1].append(ls[i])
        if len(partes) == 1:
            novas.append(r)
            continue
        for p in partes:
            ks = [k for L in p for k in L["ks"]]
            novas.append({**r, "palavras": ks, "bbox": _envelope([palavras[k][1:5] for k in ks]),
                          "classe": "texto" if r["classe"] == "titulo" and len(p) > 1 else r["classe"],
                          "regras": r.get("regras", []) + ["dividir_campos"]})
    regioes = novas

    # local_e_data
    for r in regioes:
        if "local_e_data" in ativas and r["classe"] == "titulo":
            ls = linhas(palavras, r["palavras"])
            if len(ls) == 1 and RE_LOCAL_DATA.match(ls[0]["texto"]):
                r["classe"] = "texto"
                r["regras"] = r.get("regras", []) + ["local_e_data"]

    mudou = True
    while mudou:
        mudou = False
        ordem = sorted(regioes, key=lambda r: (r["bbox"][1], r["bbox"][0]))
        for a in ordem:
            if a not in regioes or a["classe"] not in ("texto", "titulo", "assinatura"):
                continue
            ls_a = linhas(palavras, a["palavras"])
            for b in ordem:
                if b is a or b not in regioes or b["classe"] not in ("texto", "titulo", "assinatura"):
                    continue
                A, B = a["bbox"], b["bbox"]
                sobre_y = min(A[3], B[3]) - max(A[1], B[1])
                # rotulo_com_valor: rotulo sozinho a esquerda, valor na mesma linha
                if ("rotulo_com_valor" in ativas and len(ls_a) == 1 and RE_ROTULO_SO.match(ls_a[0]["texto"]) and len(a["palavras"]) <= 6
                        and sobre_y >= 0.5 * min(A[3] - A[1], B[3] - B[1]) and 0 <= B[0] - A[2] <= 4 * alt):
                    if _juntar(a, b, "texto", "rotulo_com_valor", regioes, palavras):
                        mudou = True
                        break
                vao = B[1] - A[3]
                if not -0.2 * alt <= vao <= 1.2 * alt:
                    continue
                sobre_x = min(A[2], B[2]) - max(A[0], B[0])
                alinhadas = (sobre_x >= 0.5 * min(A[2] - A[0], B[2] - B[0])
                             or abs((A[0] + A[2]) / 2 - (B[0] + B[2]) / 2) <= 3 * alt)
                if not alinhadas:
                    continue
                ls_b = linhas(palavras, b["palavras"])
                # assinatura: nome e cargo empilhados
                if "assinatura" in ativas and len(ls_a) + len(ls_b) <= 3 and eh_assinatura(ls_a + ls_b):
                    if _juntar(a, b, "assinatura", "assinatura", regioes, palavras):
                        mudou = True
                        break
                # titulos_empilhados: mesma altura de letra, ate duas linhas cada
                if ("titulos_empilhados" in ativas and a["classe"] == b["classe"] == "titulo" and len(ls_a) <= 2 and len(ls_b) <= 2
                        and 0.8 <= ls_a[-1]["h"] / max(ls_b[0]["h"], 1e-6) <= 1.25
                        and not comeca_campo(ls_b[0]["texto"])):
                    if _juntar(a, b, "titulo", "titulos_empilhados", regioes, palavras):
                        mudou = True
                        break
            if mudou:
                break

    # assinatura numa regiao so
    for r in regioes:
        if "assinatura" in ativas and r["classe"] in ("texto", "titulo") and eh_assinatura(linhas(palavras, r["palavras"])):
            r["classe"] = "assinatura"
            r["regras"] = r.get("regras", []) + ["assinatura"]
    return regioes


# ---------------------------------------------------------------------------
# Classes do Rose (etapa opcional sobre a proposta)
# ---------------------------------------------------------------------------

CONJUNTOS_CLASSES_ROSE = {
    "todas": set(CLASSES),
    "assinatura_cabecalho": {"assinatura", "cabecalho"},
    "assinatura_cabecalho_titulo_rodape": {"assinatura", "cabecalho", "titulo", "rodape"},
}


def aplicar_classes_rose(regioes, palavras, regioes_rose, classes):
    """Para cada regiao, a classe majoritaria (por palavras) das regioes do Rose que
    cobrem as palavras dela; se estiver em classes e for diferente, adota. Nao mexe em caixa."""
    if isinstance(classes, str):
        permitidas = CONJUNTOS_CLASSES_ROSE.get(classes, {c.strip() for c in classes.split(",") if c.strip()})
    else:
        permitidas = set(classes)

    if not regioes_rose:
        return [dict(r) for r in regioes]

    centros = [_centro(w) for w in palavras]

    # Rose para cada palavra: regiao menor que contem o centro (nao figura)
    rose_classe = [None] * len(palavras)
    for k, (cx, cy) in enumerate(centros):
        dentro = [rr for rr in regioes_rose if rr["bbox"][0] <= cx <= rr["bbox"][2] and rr["bbox"][1] <= cy <= rr["bbox"][3]]
        if dentro:
            nao_fig = [rr for rr in dentro if rr.get("classe") != "figura"] or dentro
            rose_classe[k] = min(nao_fig, key=lambda rr: _area(rr["bbox"]))["classe"]

    # Palavras de cada regiao
    tem_palavras = all("palavras" in r for r in regioes)
    if tem_palavras:
        palavras_por_regiao = [list(r["palavras"]) for r in regioes]
    else:
        palavras_por_regiao = [[] for _ in regioes]
        for k, (cx, cy) in enumerate(centros):
            dentro = [i for i, r in enumerate(regioes) if r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3]]
            if dentro:
                nao_fig = [i for i in dentro if regioes[i].get("classe") != "figura"] or dentro
                palavras_por_regiao[min(nao_fig, key=lambda i: _area(regioes[i]["bbox"]))].append(k)

    saida = []
    for i, r in enumerate(regioes):
        rc = dict(r)
        if r.get("classe") == "outro":            # marca de diagramacao separada por regra fica outro
            saida.append(rc)
            continue
        ks = palavras_por_regiao[i]
        votos = collections.Counter(rose_classe[k] for k in ks if rose_classe[k] is not None)
        if votos:
            max_votos = max(votos.values())
            cands = [c for c, v in votos.items() if v == max_votos]
            classe_maj = r["classe"] if r["classe"] in cands else cands[0]
            if classe_maj in permitidas and classe_maj != r["classe"]:
                rc["classe"] = classe_maj
        saida.append(rc)
    return saida
