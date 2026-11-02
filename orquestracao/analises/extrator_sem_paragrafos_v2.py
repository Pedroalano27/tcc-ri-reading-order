"""Extrator experimental v2 sem paragrafos e comparacao retomavel em CPU.

Corrige calhas sem suporte, linhas que cruzam colunas, tabelas de uma coluna
sem grade e margens fragmentadas. Importa o extrator e a bancada existentes;
nao muda suas metricas nem fluxo(). Usa palavras e ls3 congelados, sem treino,
inferencia, GPU, rede ou leitura de data/labelstudio. Cada pagina e persistida.

Uso da raiz: venv/Scripts/python.exe -B
orquestracao/analises/extrator_sem_paragrafos_v2.py
Opcoes: --somente-ancoras, --max-paginas 2 (ensaio parcial), --sem-paineis,
--ablacao (primeira iteracao), --iteracao 2 --sem-d (segunda iteracao).
Cada componente admite --com-a/--sem-a, e analogamente b, c, d e e.
As ancoras completas precedem qualquer avaliacao nova, mesmo no ensaio.
Somente resultados/extrator_sem_paragrafos_v2.md e as pastas novas
resultados/extrator_sem_paragrafos_v2/ e resultados/unidades_sem_caixas_v2/
podem receber escritas. A referencia humana entra somente na conversao e
avaliacao; nunca nas funcoes de extracao, cortes ou selecao de parametros.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import collections
import copy
import gc
import hashlib
import json
import itertools
import math
import os
import re
import random
import statistics
import time
from contextlib import contextmanager

os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", YOLO_OFFLINE="true",
                  TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="4",
                  MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4", PYTHONDONTWRITEBYTECODE="1")
from src.data import dataset_sem_caixas_finas as ds
from src.data import estruturas_pagina as ep
from orquestracao.analises import ordem_sem_bbox as o
from orquestracao.analises import erros_ponta_a_ponta as e
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import unidades_sem_caixas as u
from orquestracao.analises import auditoria_extrator_sem_paragrafos as auditoria
from orquestracao.analises import reclamacoes_x_novo as visual

ANTIGO = RAIZ / "resultados/unidades_sem_caixas"
NOVO = RAIZ / "resultados/unidades_sem_caixas_v2"
OUT = RAIZ / "resultados/extrator_sem_paragrafos_v2"
MD = RAIZ / "resultados/extrator_sem_paragrafos_v2.md"
BANCADAS = {"golden_v4": 44, "golden_v3_novo": 27}
REPS = ("linhas", "colunas", "colunas_margens")
VERSAO = "extrator-sem-paragrafos-v2-3"
COMPONENTES = {c: True for c in "ABCDE"}
INDICE = OUT / "variantes.json"
PARAM = {"score_atomos": .45, "gap_original_h": 1.2, "vale": .08,
         "janela_h": 12, "passo_janela_h": 6, "suporte_linhas": 4,
         "persistencia_h": 4, "linhas_pareadas": 3,
         "largura_min_pagina": .12, "largura_min_mediana": .45,
         "max_cruzamento": .08, "tolerancia_x_h": .5,
         "min_faixas_colunas": 2}
IMPLEMENTACAO = [
    "A — calhas locais confirmadas por linhas dos dois lados, faixas verticais "
    "ocupadas em comum e persistência; faixas estreitas são fundidas pela "
    "remoção do corte mais fraco. Títulos e átomos transversais separam zonas.",
    "B — mantém linhas_partidas como ponto de partida e divide também no vão "
    "de uma calha local confirmada, sem cortar palavras nem unir parágrafos. "
    "Correção na segunda iteração: sem corte efetivo, conserva a linha original; "
    "o código inicial reagrupava seus fragmentos e introduzia cortes extras.",
    "C — get_drawings fornece traços verticais, retângulos e pares horizontais; "
    "find_tables confirma átomos existentes. Vetores nunca criam uma região "
    "ou uma calha sem suporte textual. Recorte/rotação incompatíveis desativam "
    "esta evidência e são registrados.",
    "D — uma tabela alinhada em uma coluna, sem grade ou confirmação nativa "
    "multicoluna, volta a linhas. Fronteiras vetoriais só estreitam um átomo "
    "confirmado; toda palavra tem posse exclusiva. Caixas geométricas ainda "
    "podem se sobrepor: posse exclusiva não garante ausência de sobreposição.",
    "E — reutiliza propostas automáticas de margens da exportação atual e "
    "funde somente fragmentos da mesma faixa horizontal e do mesmo tipo. "
    "Margens e quadros com várias linhas são divididos em linhas; só tabela "
    "e imagem permanecem como bloco na representação principal. Na segunda "
    "iteração, a fusão exige calha confirmada no corpo: sem esse suporte, "
    "conserva fragmentos de margens, pois a fusão pode impor uma ordem interna errada."
]
LIMITACOES = [
    "golden_v4 foi usado no desenvolvimento da regra e nas reclamações que "
    "motivaram estas correções; os parâmetros desta versão são fixados antes "
    "da comparação, mas a bancada não é independente do desenvolvimento.",
    "golden_v3_novo fica fora do v4, porém suas notas e a auditoria também "
    "motivaram a implementação. A amostra humana é pequena; veículos vistos "
    "e não vistos no treino são separados pelo splits.json vigente.",
    "Esta tarefa gera somente as duas bancadas humanas pedidas. Não mede "
    "teste silver nem retreina ordenadores. A referência silver do projeto é "
    "automática, do fluxo do PDF em veículos confiáveis; nenhum resultado "
    "silver novo é apresentado aqui.",
    "A ordem interna é sempre ordem_sem_bbox.fluxo(), inclusive em tabelas. "
    "O piso usa eventos() dentro de cada unidade; o teto por posto mediano "
    "da referência é diagnóstico, sem otimização combinatória.",
    "Os alertas D1–D7 são heurísticos. Na auditoria anterior, D1 e D4 não "
    "recuperaram as notas correspondentes do autor; uma queda de alertas "
    "isoladamente não demonstra melhora de leitura. D5 aqui recebe margens "
    "automáticas de ambas as versões nas mesmas páginas, e não as estruturas "
    "históricas exclusivas de parte do v4. As contagens não são o total do "
    "acervo da auditoria original.",
    "Listas com colunas de dados e tabelas sem bordas continuam ambíguas; "
    "uma grade pode faltar no PDF digital. Átomos vazios são conservados, "
    "pois podem ser tabelas/imagens rasterizadas. Não há OCR nem palavras "
    "novas para texto em imagem.",
    "A regra_colunas da bancada é preservada, inclusive sua busca de calhas. "
    "A hierarquia v2 orienta segmentação e metadados; não é uma troca oculta "
    "do ordenador. Nas faixas, a hierarquia também muda a unidade atômica."
]


def exigir(cond, msg):
    if not cond:
        raise ValueError(msg)


def ler_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsonl(p):
    with open(p, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                yield json.loads(linha)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                   allow_nan=False).encode("utf-8")).hexdigest()


def chave(pid):
    return e.ac.chave(pid)


def destino(p):
    p = Path(p).resolve()
    exigir(p == MD.resolve() or p.is_relative_to(OUT.resolve()) or
           p.is_relative_to(NOVO.resolve()), f"Escrita fora do escopo: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def gravar(p, obj):
    p = destino(p)
    temp = p.with_suffix(p.suffix + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, p)


def memoria_minima(min_mb):
    m = b.memoria()
    exigir(not m or m["ram_livre_mb"] >= min_mb,
           f"RAM insuficiente; retome depois: {m}")
    return m


@contextmanager
def trava():
    """Trava exclusiva da tarefa; reaproveita verificacao de PID da bancada."""
    antigo = b.OUT
    b.OUT = OUT
    try:
        with b.trava():
            yield
    finally:
        b.OUT = antigo


def array_json(p, nome):
    """Le elementos de um array no JSON historico sem carregar o documento."""
    dec = json.JSONDecoder()
    padrao = re.compile(r'"' + re.escape(nome) + r'"\s*:\s*\[')
    with open(p, encoding="utf-8") as f:
        buf = ""
        while True:
            bloco = f.read(65536)
            exigir(bloco, f"Array {nome} ausente: {p}")
            buf += bloco
            match = padrao.search(buf)
            if match:
                buf = buf[match.end():]
                break
            buf = buf[-1024:]
        while True:
            buf = buf.lstrip()
            if buf.startswith(","):
                buf = buf[1:].lstrip()
            if buf.startswith("]"):
                return
            try:
                obj, fim = dec.raw_decode(buf)
            except json.JSONDecodeError:
                bloco = f.read(65536)
                exigir(bloco, f"Array truncado em {p}")
                buf += bloco
                continue
            yield obj
            buf = buf[fim:]


def congelar_bancadas(run, H):
    """Copia apenas os dois JSONL humanos; nunca toca na exportacao em uso."""
    fontes = run / "antes"
    hashes = {}
    for nome in BANCADAS:
        src = ANTIGO / "bancadas" / (nome + ".jsonl")
        alvo = destino(fontes / "bancadas" / src.name)
        esperado = H[src.relative_to(RAIZ).as_posix()]
        exigir(sha(src) == esperado, "Bancada mudou antes do snapshot")
        if not alvo.exists():
            temp = alvo.with_suffix(".jsonl.tmp")
            with open(src, "rb") as f, open(temp, "wb") as g:
                for bloco in iter(lambda: f.read(65536), b""):
                    g.write(bloco)
                g.flush()
                os.fsync(g.fileno())
            exigir(sha(temp) == esperado == sha(src), "Bancada mudou durante a copia")
            os.replace(temp, alvo)
        exigir(sha(alvo) == esperado, "Snapshot divergente; preserve-o e reinicie com fontes atuais")
        hashes[nome] = esperado
        for obj in jsonl(alvo):
            src_det = ANTIGO / "cache/detector" / (chave(obj["page_id"]) + ".json")
            det_rel = src_det.relative_to(RAIZ).as_posix()
            det_hash = H[det_rel]
            frozen = destino(fontes / "cache/detector" / src_det.name)
            if not frozen.exists():
                det = ler_json(src_det)
                exigir(sha(src_det) == det_hash, "Detector mudou ao congelar")
                # Preserva bytes para o hash ser comparavel ao arquivo original.
                temp = frozen.with_suffix(".json.tmp")
                with open(src_det, "rb") as f, open(temp, "wb") as g:
                    for bloco in iter(lambda: f.read(65536), b""):
                        g.write(bloco)
                    g.flush()
                    os.fsync(g.fileno())
                exigir(sha(temp) == det_hash == sha(src_det), "Detector mudou durante a copia")
                os.replace(temp, frozen)
            exigir(sha(frozen) == det_hash, "Snapshot do detector divergente")
    return fontes, hashes


def estatisticas(rows):
    """Resume apenas escalares; nao guarda palavras de paginas em memoria."""
    return {k: statistics.mean(v) if v else None for k in
            ("tau", "quebras", "piso_interno", "fid12", "sucessor_linhas", "unidades")
            for v in [[r[k] for r in rows if r.get(k) is not None]]}


def adaptar_auditoria(obj, p):
    unidades = [{**x, "tipo": {"tabela": "table", "imagem": "picture"}.get(x["tipo"], x["tipo"])}
                for x in p["bounding_boxes"]]
    return {"page_id": obj["page_id"], "uf": obj["uf"],
            "dimensions": obj["dimensions"], "palavras": obj["palavras"],
            "unidades": unidades}


def medir_reps(obj):
    """Mesma bancada, mesmo embaralhamento e mesma regua de palavras."""
    res = {}
    est = adaptar_auditoria(obj, obj["representacoes"]["colunas_margens"])
    for rep in REPS:
        p = obj["representacoes"][rep]
        ordem, diag = b.prever(p, obj["palavras"], "regra_colunas")
        metricas = b.metricas(obj, p, ordem, canonica=True)
        teto, _ = b.prever(p, obj["palavras"], "teto")
        mt = b.metricas(obj, p, teto, canonica=True)
        res[rep] = {**metricas, "unidades": len(p["bounding_boxes"]),
                    "teto_tau": mt["tau"], "teto_quebras": mt["quebras"],
                    "ordem_regra": ordem, "diag": diag}
    doc = adaptar_auditoria(obj, obj["representacoes"]["linhas"])
    achados = auditoria.auditar_pagina(doc, est)
    return {"metricas": res, "achados": achados,
            "defeitos": sorted({a["detector"] for a in achados})}


def conferir_ancoras(R, run, fontes, min_mb):
    """Reexecuta P2 e mede P1m historico, como a bancada original."""
    R.setdefault("ancoras", {})["aprovada"] = False
    historico = {}
    for r in array_json(e.JSON, "paginas"):
        if r["coorte"] == "v4":
            historico[r["page_id"]] = {m: list(r["metodos"][m]["seq"])
                                      for m in ("P2", "P1m")}
    exigir(len(historico) == BANCADAS["golden_v4"], "Historico v4 incompleto")
    b.UNIDADES = fontes
    rows = []
    for obj, p in b.paginas("golden_v4", "linhas"):
        memoria_minima(min_mb)
        pid = obj["page_id"]
        exigir(pid in historico, f"Pagina fora da ancora: {pid}")
        detfile = fontes / "cache/detector" / (chave(pid) + ".json")
        det = ler_json(detfile)
        exigir(det.get("regioes") is not None, f"Detector congelado ausente: {pid}")
        q = b.referencia(obj, p)
        q.update(ls3=det["regioes"], d={"detector": {"regioes": []}})
        fp = digest([R["fingerprint"], obj, det, historico[pid]])
        cache = run / "ancoras" / (chave(pid) + ".json")
        if cache.exists():
            r = ler_json(cache)
            exigir(r["fingerprint"] == fp, f"Ancora em cache mudou: {pid}")
        else:
            seq, its, diag = e.ls.prever(q, e.FIXA, "ls3")
            exigir(seq == historico[pid]["P2"], f"P2 difere da sequencia historica: {pid}")
            med = e.medir(q, seq, [], {}, "P0")
            ordem, _ = b.prever(p, obj["palavras"], "regra_colunas")
            exportada = b.metricas(obj, p, ordem, canonica=True)
            exp = b.expansoes(obj, p, canonica=True)
            exigir([k for uid in ordem for k in exp[uid]] == seq,
                   f"Regra exportada difere de P2: {pid}")
            p1m = e.medir(q, historico[pid]["P1m"], [], {}, "P0")
            r = {"fingerprint": fp, "page_id": pid,
                 "P2": {k: med[k] for k in ("tau", "quebras")},
                 "P1m": {k: p1m[k] for k in ("tau", "quebras")},
                 "regra": exportada, "detector_sha256": sha(detfile)}
            gravar(cache, r)
        rows.append(r)
        R["progresso_ancoras"] = len(rows)
        salvar_estado(R, run)
        print(f"Ancora {len(rows)}/{BANCADAS['golden_v4']}: {pid}", flush=True)
        gc.collect()
    exigir(len(rows) == BANCADAS["golden_v4"] and
           {r["page_id"] for r in rows} == set(historico), "Coorte da ancora divergente")
    medias = {m: {k: statistics.mean(r[m][k] for r in rows) for k in ("tau", "quebras")}
              for m in ("regra", "P2", "P1m")}
    R["ancoras"] = {"aprovada": False, "n": len(rows), "medias": medias,
                    "P1m_origem": "sequencia historica reavaliada por medir(), sem reextracao",
                    "paginas": rows}
    exigir(abs(medias["regra"]["tau"] - .985948) <= .00000051 and
           abs(medias["regra"]["quebras"] - 6.045455) <= .00000051,
           f"PARE: ancora exata da exportacao nao reproduzida: {medias['regra']}")
    for m, tau, qb in (("P2", .986, 6.05), ("P1m", .952, 8.93)):
        exigir(abs(medias[m]["tau"] - tau) <= .006 and
               abs(medias[m]["quebras"] - qb) <= .0051,
               f"PARE: ancora {m} nao reproduzida: {medias[m]}")
    R["ancoras"]["aprovada"] = True
    R["fase"] = "antes"
    salvar_estado(R, run)


def extrair_vetores(p, pdf_hash, run, h):
    """Vetores apenas confirmam regioes e candidatos de calha com texto."""
    import pymupdf
    fp = digest([VERSAO, pdf_hash, p["pagina"], p["dimensions"], h,
                 sha(Path(__file__))])
    cache = run / "vetores" / (fp + ".json")
    if cache.exists():
        return ler_json(cache)
    W, H = p["dimensions"]["width"], p["dimensions"]["height"]
    out = {"verticais": [], "horizontais": [], "retangulos": [],
           "tabelas": [], "avisos": [], "fingerprint": fp}
    pdf = RAIZ / "data/raw" / p["uf"] / p["arquivo"]
    with pymupdf.open(pdf) as doc:
        page = doc[p["pagina"]]
        crop = page.cropbox
        if (page.rotation or abs(crop.x0) > .11 or abs(crop.y0) > .11 or
                abs(page.rect.width - W) > .11 or abs(page.rect.height - H) > .11):
            out["avisos"].append("Vetores desativados: recorte, rotacao ou dimensoes nao canonicos")
            gravar(cache, out)
            return out
        for d in page.get_drawings():
            for item in d.get("items", []):
                if item[0] == "l":
                    a, z = item[1:3]
                    x0, x1 = sorted((float(a.x), float(z.x)))
                    y0, y1 = sorted((float(a.y), float(z.y)))
                    if x1-x0 <= 2 and y1-y0 >= max(2., .5*h):
                        out["verticais"].append([x0, y0, x1, y1])
                    if y1-y0 <= 2 and x1-x0 >= .12*W:
                        out["horizontais"].append([x0, y0, x1, y1])
                elif item[0] == "re":
                    rect = item[1]
                    box = [float(v) for v in rect]
                    if rect.width >= .12*W and rect.height >= 2*h:
                        out["retangulos"].append(box)
                    if rect.width > 2 and rect.height > 2:
                        out["horizontais"].extend([[box[0], box[1], box[2], box[1]],
                                                  [box[0], box[3], box[2], box[3]]])
                        if rect.height >= max(2., .5*h):
                            out["verticais"].extend([[box[0], box[1], box[0], box[3]],
                                                    [box[2], box[1], box[2], box[3]]])
        # Pares com as mesmas extremidades; nao combina cada traco com todos.
        grupos = collections.defaultdict(list)
        for box in out["horizontais"]:
            grupos[(round(box[0]/4), round(box[2]/4))].append(box)
        for grupo in grupos.values():
            ls = sorted(grupo, key=lambda z: z[1])
            for a, z in zip(ls, ls[1:]):
                if 2*h <= z[1]-a[1] <= .6*H and min(a[2]-a[0], z[2]-z[0]) >= .12*W:
                    out["retangulos"].append([max(a[0], z[0]), a[1], min(a[2], z[2]), z[1]])
        try:
            for tabela in page.find_tables().tables:
                out["tabelas"].append({"bbox": list(map(float, tabela.bbox)),
                                       "linhas": tabela.row_count, "colunas": tabela.col_count})
        except Exception as exc:
            out["avisos"].append(f"find_tables indisponivel/falhou: {type(exc).__name__}: {exc}")
    for nome in ("verticais", "horizontais", "retangulos"):
        out[nome] = [list(t) for t in sorted(set(tuple(round(v, 3) for v in z) for z in out[nome]))]
    gravar(cache, out)
    return out


def sobrepoe_y(a, z):
    return max(0., min(a[3], z[3]) - max(a[1], z[1]))


def confirmar_atomo(a, vet, h):
    """Grade ou tabela nativa confirma um atomo; nunca cria um novo."""
    box = a["bbox"]
    W, H = box[2]-box[0], box[3]-box[1]
    if W <= 0 or H <= 0:
        return {"grade": False, "nativa_multicoluna": False, "limite": None}
    hs = [z for z in vet["horizontais"] if box[1]-h <= z[1] <= box[3]+h and
          max(0., min(z[2], box[2])-max(z[0], box[0])) >= .6*W]
    vs = [z for z in vet["verticais"] if box[0]-h <= z[0] <= box[2]+h and
          sobrepoe_y(box, z) >= .5*H]
    grade = len({round(z[1]/max(1., .5*h)) for z in hs}) >= 2 and bool(vs)
    candidatas = []
    for z in vet["retangulos"]:
        inter = o.inter(box, z)
        if inter >= .65*o.area(box) and inter >= .65*o.area(z):
            candidatas.append(z)
    nativas = [z for z in vet["tabelas"] if o.inter(box, z["bbox"]) >= .6*o.area(box)
               and o.inter(box, z["bbox"]) >= .6*o.area(z["bbox"])]
    multicoluna = any(z["colunas"] >= 2 for z in nativas)
    if nativas:
        candidatas.extend(z["bbox"] for z in nativas)
    limite = min(candidatas, key=lambda z: sum(abs(x-y) for x, y in zip(box, z)), default=None)
    return {"grade": grade, "nativa_multicoluna": multicoluna, "limite": limite}


def tabela_uma_coluna(ws, a, h):
    """Alinhamento recorrente distingue lista de lacunas isoladas entre nomes."""
    ls = o.linhas(ws, a["ks"])
    if len(ls) < 2:
        return False
    gaps = []
    sem_vao = 0
    inicios = []
    for linha in ls:
        ks = sorted(linha["ks"], key=lambda k: (ws[k][1], ws[k][3], k))
        inicios.append(min(ws[k][1] for k in ks))
        gs = [(ws[z][1]+ws[x][3])/2 for x, z in zip(ks, ks[1:])
              if ws[z][1]-ws[x][3] >= max(8., .9*h)]
        sem_vao += not gs
        gaps.extend((x, i) for x in gs for i in [len(inicios)-1])
    tol = max(4., .75*h)
    grupos = []
    for x, i in sorted(gaps):
        if grupos and abs(x-statistics.median(t[0] for t in grupos[-1])) <= tol:
            grupos[-1].append((x, i))
        else:
            grupos.append([(x, i)])
    recorrente = any(len({i for _, i in g}) >= max(3, math.ceil(.35*len(ls))) for g in grupos)
    alinhadas = sum(abs(x-statistics.median(inicios)) <= tol for x in inicios) >= .8*len(ls)
    return alinhadas and not recorrente and sem_vao >= .75*len(ls)


def atomos_v2(p, vet, h, diag):
    """Conserva NMS e resolve posse exclusiva depois de confirmar fronteiras."""
    ws = p["palavras"]
    # Reusa representar: mesmos atomos/linhas originais, sem referencia humana.
    original, _ = ds.representar(p)
    atoms = [dict(a, ks=list(a["ks"]), bbox=list(a["bbox"])) for a in original["unidades"]
             if a["tipo"] in ("table", "picture")]
    if not COMPONENTES["D"]:
        tomados = {k for a in atoms for k in a["ks"]}
        return atoms, [k for k in range(len(ws)) if k not in tomados]
    aceitos = []
    for a in atoms:
        conf = confirmar_atomo(a, vet, h)
        a["confirmacao_vetorial"] = conf
        if a["tipo"] == "table" and not conf["grade"] and not conf["nativa_multicoluna"] and tabela_uma_coluna(ws, a, h):
            diag["tabelas_rebaixadas"] += 1
            diag["rebaixadas"].append({"bbox": a["bbox"], "palavras": len(a["ks"])})
            continue
        z = conf["limite"]
        if z is not None and a["ks"]:
            estreita = [max(a["bbox"][0], z[0]), max(a["bbox"][1], z[1]),
                        min(a["bbox"][2], z[2]), min(a["bbox"][3], z[3])]
            mantidas = sum(ep.dentro(ws[k], estreita) for k in a["ks"])
            if mantidas >= .9*len(a["ks"]) and o.area(estreita) > 0:
                if estreita != a["bbox"]:
                    diag["fronteiras_confirmadas"] += 1
                    a["bbox_original"] = a["bbox"]
                    a["bbox"] = estreita
        a["ks"] = []
        aceitos.append(a)
    livres = []
    for k, w in enumerate(ws):
        cand = [a for a in aceitos if ep.dentro(w, a["bbox"])]
        if cand:
            min(cand, key=lambda a: (a["tipo"] != "table", o.area(a["bbox"]),
                                    -a.get("score", 0), a["bbox"]))["ks"].append(k)
        else:
            livres.append(k)
    return aceitos, livres


def margem_candidatas(antigo):
    """Propostas de representar_estruturas ja congeladas, nao caixas humanas."""
    return [{"tipo": z["tipo"], "bbox": list(z["bbox"])} for z in
            antigo["representacoes"]["colunas_margens"]["bounding_boxes"]
            if z["tipo"] in ("cabecalho", "rodape", "quadro_externo")]


def fundir_margens(items, ws, h, diag):
    if diag.get("max_colunas", 1) < 2:
        return items
    outros = [z for z in items if z["tipo"] not in ("cabecalho", "rodape")]
    for tipo in ("cabecalho", "rodape"):
        grupos = []
        for z in sorted((z for z in items if z["tipo"] == tipo),
                        key=lambda z: (sum(z["bbox"][1::2])/2, z["bbox"][0])):
            cy = sum(z["bbox"][1::2])/2
            alvo = None
            for g in grupos:
                centros = [sum(t["bbox"][1::2])/2 for t in g] + [cy]
                if (max(centros)-min(centros) <= .75*h and
                    all(sobrepoe_y(z["bbox"], t["bbox"]) >= .35*min(
                        z["bbox"][3]-z["bbox"][1], t["bbox"][3]-t["bbox"][1]) for t in g) and
                    len(o.linhas(ws, [k for t in g+[z] for k in t["ks"]])) == 1):
                    alvo = g
                    break
            if alvo is None:
                grupos.append([z])
            else:
                alvo.append(z)
        for g in grupos:
            ks = [k for z in g for k in z["ks"]]
            if ks:
                outros.append({"tipo": tipo, "bbox": o.envelope([ws[k][1:5] for k in ks]),
                                "ks": ks, "evidencia": "margem automatica; mesma faixa horizontal"})
            diag["fragmentos_margem_fundidos"] += max(0, len(g)-1)
    return outros


def margens_v2(ws, livres, candidatos, h, diag):
    grupos = [{**z, "ks": []} for z in candidatos]
    rest = []
    for k in livres:
        cand = [z for z in grupos if ep.dentro(ws[k], z["bbox"])]
        if cand:
            min(cand, key=lambda z: (o.area(z["bbox"]), z["tipo"], z["bbox"]))["ks"].append(k)
        else:
            rest.append(k)
    # Mesmo uma proposta de margem/quadro com varias linhas nao vira bloco
    # de texto na representacao principal. Somente table/picture sao atomos.
    linhas = []
    for z in grupos:
        if not z["ks"]:
            continue
        for linha in o.linhas_partidas(ws, z["ks"], 1.2, h):
            tipo = "texto" if z["tipo"] == "quadro_externo" else z["tipo"]
            linhas.append({**linha, "tipo": tipo, "origem_estrutura": z["tipo"]})
    return fundir_margens(linhas, ws, h, diag), rest


def suporte_calha(items, ids, x, h, W, vet):
    """Conta faixas ocupadas de ambos os lados, sem contar palavras como linhas."""
    tol = max(2., PARAM["tolerancia_x_h"]*h)
    bs = [items[i]["bbox"] for i in ids if items[i]["tipo"] == "texto"]
    bs = [z for z in bs if .08*W <= z[2]-z[0] <= .7*W]
    esq = [z for z in bs if z[2] <= x+tol]
    dire = [z for z in bs if z[0] >= x-tol]
    if not esq or not dire:
        return None
    # Bins cobrem a altura da caixa: leve diferenca de baseline nao elimina pares.
    def ocupados(zs):
        return {j for z in zs for j in range(math.floor(z[1]/h), math.ceil(z[3]/h)+1)}
    a, z = ocupados(esq), ocupados(dire)
    comuns = sorted(a & z)
    if not comuns:
        return None
    ymin, ymax = max(min(t[1] for t in esq), min(t[1] for t in dire)), min(
        max(t[3] for t in esq), max(t[3] for t in dire))
    # Centros quantizados nao duplicam fragmentos da mesma linha.
    nl = len({round((t[1]+t[3])/(2*h)) for t in esq})
    nr = len({round((t[1]+t[3])/(2*h)) for t in dire})
    pares = sum(any(abs((l[1]+l[3]-r[1]-r[3])/2) <= .8*h for r in dire) for l in esq)
    linhas_cruzadas = [t for t in bs if t[0]+tol < x < t[2]-tol]
    cruza = len(linhas_cruzadas)/max(1, len(bs))
    vetor = any(abs((t[0]+t[2])/2-x) <= tol and
                min(t[3], ymax)-max(t[1], ymin) >= 4*h for t in vet["verticais"])
    minimo = PARAM["suporte_linhas"] - int(vetor)
    # Vetor pode reduzir de quatro para tres linhas, nunca substituir o texto.
    if (min(nl, nr) < minimo or pares < PARAM["linhas_pareadas"] or
        ymax-ymin < PARAM["persistencia_h"]*h or cruza > PARAM["max_cruzamento"]):
        return None
    persistencia = max((len(list(g)) for _, g in itertools.groupby(
        enumerate(comuns), key=lambda t: t[1]-t[0])), default=0)
    if persistencia < 3:
        return None
    left_edges = [t[2] for t in esq if t[2] >= x-.18*W]
    right_edges = [t[0] for t in dire if t[0] <= x+.18*W]
    if not left_edges or not right_edges:
        return None
    largura = statistics.median(right_edges)-statistics.median(left_edges)
    if largura < 4:
        return None
    return {"x": float(x), "y0": ymin, "y1": ymax,
            "largura": largura, "limiar_gap": max(4., min(1.2*h, .5*largura)),
            "suporte_esq": nl, "suporte_dir": nr, "pares": pares,
            "persistencia_bins": persistencia, "vetor": vetor,
            "forca": min(nl, nr)*(ymax-ymin)/h + int(vetor)*4}


def filtrar_faixas(cortes, items, ids, Wpagina, diag):
    """Faixa estreita perde uma fronteira e passa a pertencer a vizinha."""
    cortes = sorted(cortes, key=lambda c: c["x"])
    lo, _, hi, _ = o.envelope([items[i]["bbox"] for i in ids])
    while cortes:
        bordas = [lo] + [c["x"] for c in cortes] + [hi]
        widths = [z-a for a, z in zip(bordas, bordas[1:])]
        med = statistics.median(widths)
        estreitas = [i for i, w in enumerate(widths) if
                     w < .12*Wpagina or w < .45*med]
        if not estreitas:
            break
        i = min(estreitas, key=widths.__getitem__)
        viz = [j for j in (i-1, i) if 0 <= j < len(cortes)]
        j = min(viz, key=lambda j: (cortes[j]["forca"], j))
        diag["faixas_estreitas_fundidas"] += 1
        cortes.pop(j)
    return cortes


def cortes_confirmados(items, ids, h, W, vet, diag):
    """Candidatos existentes, confirmados em janelas verticais locais."""
    textos = [i for i in ids if items[i]["tipo"] == "texto"]
    if len(textos) < 8:
        return []
    _, y0, _, y1 = o.envelope([items[i]["bbox"] for i in textos])
    candidatos = []
    janela = PARAM["janela_h"]*h
    y = y0
    while y <= y1:
        locais = [i for i in textos if y <= sum(items[i]["bbox"][1::2])/2 < y+janela]
        if len(locais) >= 8:
            xs = o.vales_locais(items, locais, h, .08) or o.vales(items, locais, h, .08)
            # Vao da camada de palavras continua sendo evidencia textual.
            ordenadas = sorted(locais, key=lambda i: items[i]["bbox"][1])
            for aidx, i in enumerate(ordenadas):
                aa = items[i]["bbox"]
                for j in ordenadas[aidx+1:]:
                    zz = items[j]["bbox"]
                    if zz[1] > aa[3]+h:
                        break
                    if abs(sum(aa[1::2])/2-sum(zz[1::2])/2) <= .8*h:
                        l, r = sorted((aa, zz), key=lambda z: z[0])
                        if r[0]-l[2] >= 4:
                            xs.append((l[2]+r[0])/2)
            xs += [(z[0]+z[2])/2 for z in vet["verticais"]
                   if min(z[3], y+janela)-max(z[1], y) >= 4*h]
            # Agrupa candidatos proximos antes de contar suporte.
            grupos = []
            for x in sorted(xs):
                if grupos and abs(x-statistics.median(grupos[-1])) <= max(4., .5*h):
                    grupos[-1].append(x)
                else:
                    grupos.append([x])
            for g in grupos:
                x = statistics.median(g)
                conf = suporte_calha(items, locais, x, h, W, vet)
                if conf:
                    candidatos.append(conf)
        y += PARAM["passo_janela_h"]*h
    grupos = []
    for c in sorted(candidatos, key=lambda c: c["x"]):
        if grupos and abs(c["x"]-statistics.median(t["x"] for t in grupos[-1])) <= max(4., .5*h):
            grupos[-1].append(c)
        else:
            grupos.append([c])
    cortes = []
    for g in grupos:
        # Mesma calha pode ter intervalos separados por um elemento transversal.
        melhor = max(g, key=lambda c: c["forca"])
        c = dict(melhor, x=statistics.median(t["x"] for t in g),
                 intervalos=[[t["y0"], t["y1"]] for t in g])
        cortes.append(c)
    cortes = filtrar_faixas(cortes, items, textos, W, diag)
    diag["calhas_confirmadas"] += len(cortes)
    diag["max_colunas"] = max(diag.get("max_colunas", 1), len(cortes)+1)
    return cortes


def partir_na_calha(ws, items, cortes, h, diag):
    saida = []
    for item in items:
        if item["tipo"] != "texto":
            saida.append(item)
            continue
        # O item ja e uma linha. Recalcular linhas() apenas nos seus fragmentos
        # muda as faixas de baseline sem qualquer calha confirmada.
        ks = sorted(item["ks"], key=lambda k: (ws[k][1], ws[k][2], k))
        grupos = [[]]
        for k in ks:
            if grupos[-1]:
                prev = grupos[-1][-1]
                gap = ws[k][1]-ws[prev][3]
                cy = (ws[k][2]+ws[k][4]+ws[prev][2]+ws[prev][4])/4
                if any(ws[prev][3] <= c["x"] <= ws[k][1] and
                       any(a-h <= cy <= z+h for a, z in c["intervalos"]) and
                       gap > c["limiar_gap"] for c in cortes):
                    grupos.append([])
                    diag["linhas_partidas_calha"] += 1
            grupos[-1].append(k)
        if len(grupos) == 1:
            saida.append(item)
        else:
            saida.extend({"tipo": "texto", "ks": g,
                          "bbox": o.envelope([ws[k][1:5] for k in g])} for g in grupos)
    return saida


def hierarquia(items, ids, h, W, vet, diag, depth=0, prefixo="z"):
    """Pagina -> zonas -> colunas -> linhas; atomos transversais sao barreiras."""
    if not ids:
        return []
    if not COMPONENTES["A"]:
        textos = [i for i in ids if items[i]["tipo"] == "texto"]
        grupos = ds.zonas(items, textos, h) if textos else []
        atomos = [[i] for i in ids if items[i]["tipo"] != "texto"]
        return [{"id": f"{prefixo}original{j}", "ids": g, "cortes": []}
                for j, g in enumerate(atomos + grupos)]
    if depth >= 16:
        return [{"id": prefixo, "ids": list(ids), "cortes": []}]
    cortes = cortes_confirmados(items, ids, h, W, vet, diag)
    if not cortes:
        return [{"id": prefixo, "ids": sorted(ids, key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0])),
                 "cortes": []}]
    content = o.envelope([items[i]["bbox"] for i in ids])
    largura = content[2]-content[0]
    pontes = [i for i in ids if any(items[i]["bbox"][0] < c["x"] < items[i]["bbox"][2] and
              min(c["x"]-items[i]["bbox"][0], items[i]["bbox"][2]-c["x"]) >= .1*largura
              for c in cortes) and (items[i]["tipo"] in ("table", "picture") or
              items[i]["bbox"][2]-items[i]["bbox"][0] >= .6*largura)]
    if pontes:
        pontes.sort(key=lambda i: (items[i]["bbox"][1], items[i]["bbox"][0]))
        # Barreira e uma faixa vertical, nao uma lista de centros independentes.
        bands = []
        for i in pontes:
            box = items[i]["bbox"]
            if bands and box[1] <= bands[-1]["y1"]:
                bands[-1]["ids"].append(i)
                bands[-1]["y1"] = max(bands[-1]["y1"], box[3])
            else:
                bands.append({"ids": [i], "y0": box[1], "y1": box[3]})
        diag["barreiras"] += len(bands)
        centros = [(z["y0"]+z["y1"])/2 for z in bands]
        rest = [[] for _ in range(len(bands)+1)]
        ponte_set = set(pontes)
        for i in ids:
            if i not in ponte_set:
                cy = sum(items[i]["bbox"][1::2])/2
                rest[sum(y < cy for y in centros)].append(i)
        out = []
        for j, grupo in enumerate(rest):
            out.extend(hierarquia(items, grupo, h, W, vet, diag, depth+1, f"{prefixo}s{j}"))
            if j < len(bands):
                out.append({"id": f"{prefixo}b{j}", "ids": bands[j]["ids"],
                            "barreira": True, "cortes": [c["x"] for c in cortes]})
        return out
    cols = [[] for _ in range(len(cortes)+1)]
    for i in ids:
        cx = sum(items[i]["bbox"][::2])/2
        cols[sum(c["x"] < cx for c in cortes)].append(i)
    nao_vazias = [g for g in cols if g]
    if len(nao_vazias) < PARAM["min_faixas_colunas"]:
        return [{"id": prefixo, "ids": list(ids), "cortes": []}]
    out = []
    for j, grupo in enumerate(cols):
        filhos = hierarquia(items, grupo, h, W, vet, diag, depth+1, f"{prefixo}c{j}")
        for filho in filhos:
            filho["cortes"] = sorted(set(filho.get("cortes", []) + [c["x"] for c in cortes]))
        out.extend(filhos)
    return out


def pacote(p, items, zonas, nome, h, diag):
    ws = p["palavras"]
    owner = {i: z["id"] for z in zonas for i in z["ids"]}
    if nome == "linhas":
        unidades = [dict(z, id=f"l{i}", coluna=owner.get(i)) for i, z in enumerate(items)]
    else:
        unidades = [dict(z, id=f"a{i}") for i, z in enumerate(items) if z["tipo"] != "texto"]
        for j, zona in enumerate(zonas):
            g = [i for i in zona["ids"] if items[i]["tipo"] == "texto"]
            if not g:
                continue
            unidades.append({"id": f"c{j}", "tipo": "texto_coluna",
                             "bbox": o.envelope([items[i]["bbox"] for i in g]),
                             "ks": [k for i in g for k in items[i]["ks"]],
                             "linhas": [items[i] for i in g], "zona": zona["id"]})
    for z in unidades:
        z["text"] = " ".join(ws[k][0] for k in o.fluxo([z], ws))
    exigir(sorted(k for z in unidades for k in z["ks"]) == list(range(len(ws))),
           f"Palavra sem dono/duplicada em {p['page_id']}: {nome}")
    return {"page_id": p["page_id"], "dimensions": p["dimensions"],
            "representacao": nome, "palavras": ws, "unidades": unidades, "h_linha": h,
            "colunas": {"cortes_x": sorted({x for z in zonas for x in z.get("cortes", [])}),
                        "n_estimado": diag.get("max_colunas", 1),
                        "faixas": len(zonas), "criterio": "v2: suporte textual, persistencia e zonas"},
            "hierarquia": [{"id": z["id"], "barreira": bool(z.get("barreira")),
                             "bbox": o.envelope([items[i]["bbox"] for i in z["ids"]]),
                             "cortes_x": z.get("cortes", [])} for z in zonas if z["ids"]],
            "diagnostico_v2": diag}


def representar_v2(p, estruturas, vet):
    """So campos automaticos; recebe nenhuma ordem, anotacao ou referencia."""
    ws = p["palavras"]
    h = max(.1, statistics.median(w[4]-w[2] for w in ws))
    W = p["dimensions"]["width"]
    diag = {"tabelas_rebaixadas": 0, "rebaixadas": [], "fronteiras_confirmadas": 0,
            "fragmentos_margem_fundidos": 0, "faixas_estreitas_fundidas": 0,
            "calhas_confirmadas": 0, "linhas_partidas_calha": 0, "barreiras": 0,
            "vetores_avisos": list(vet["avisos"])}
    atoms, livres = atomos_v2(p, vet, h, diag)
    # Linhas com margens fundidas; colunas sem e com isolamento de margens.
    textos = o.linhas_partidas(ws, livres, 1.2, h)
    if COMPONENTES["B"]:
        cortes = cortes_confirmados(textos, list(range(len(textos))), h, W, vet, diag)
        textos = partir_na_calha(ws, textos, cortes, h, diag)
    sem = atoms + textos
    zsem = hierarquia(sem, list(range(len(sem))), h, W, vet, diag)
    margens, rest = margens_v2(ws, livres, estruturas, h, diag) if COMPONENTES["E"] else ([], livres)
    body = o.linhas_partidas(ws, rest, 1.2, h)
    if COMPONENTES["B"]:
        cortes = cortes_confirmados(body, list(range(len(body))), h, W, vet, diag)
        body = partir_na_calha(ws, body, cortes, h, diag)
    com = atoms + body + margens
    corpo = [i for i, z in enumerate(com) if z["tipo"] not in ("cabecalho", "rodape")]
    zcom = hierarquia(com, corpo, h, W, vet, diag)
    zcom.extend({"id": f"m{i}", "ids": [i], "cortes": []} for i, z in enumerate(com)
               if z["tipo"] in ("cabecalho", "rodape"))
    # Linhas e a representacao principal. As faixas ficam so para diagnostico.
    return {"linhas": pacote(p, com, zcom, "linhas", h, diag),
            "colunas": pacote(p, sem, zsem, "colunas", h, diag),
            "colunas_margens": pacote(p, com, zcom, "colunas_estruturas", h, diag)}, diag


def converter_v2(antigo, det, vet):
    """A referencia e adicionada apenas depois da representacao automatica."""
    if not any(COMPONENTES.values()):
        obj = copy.deepcopy(antigo)
        obj["diagnostico_v2"] = {"componentes": dict(COMPONENTES), "vetores_avisos": []}
        return obj
    meta = {k: antigo[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "particao")}
    meta["colecao"] = "bancadas"
    auto = {k: meta[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions")}
    auto.update(palavras=antigo["palavras"], detector={"modelo": "ls3",
                "regioes": e.ls.dets({"ls3": det["regioes"]}, "ls3")})
    reps, diag = representar_v2(auto, margem_candidatas(antigo), vet)
    diag["componentes"] = dict(COMPONENTES)
    convertido = {nome: u.converter(meta, reps[nome], auto["palavras"], antigo["gt_w"]) for nome in REPS}
    for nome, p in convertido.items():
        p["ordem_interna"] = "ordem_sem_bbox.fluxo() por unidade; ks define pertinencia"
        p["extrator_versao"] = VERSAO
        p["hierarquia_v2"] = {"colunas": reps[nome]["colunas"], "zonas": reps[nome]["hierarquia"]}
        def assinatura_unit(z):
            tipo = {"table": "tabela", "picture": "imagem"}.get(z["tipo"], z["tipo"])
            return (tuple(sorted(z["ks"])), tuple(z["bbox"]), tipo)
        automaticas = {assinatura_unit(z): z for z in reps[nome]["unidades"]}
        for caixa in p["bounding_boxes"]:
            automatica = automaticas[assinatura_unit(caixa)]
            caixa["zona_v2"] = automatica.get("zona", automatica.get("coluna"))
            if "confirmacao_vetorial" in automatica:
                caixa["confirmacao_vetorial"] = automatica["confirmacao_vetorial"]
    obj = {k: antigo[k] for k in ("page_id", "uf", "arquivo", "pagina", "dimensions", "particao",
                                  "palavras", "gt_w", "referencia_palavras", "origem_palavras",
                                  "gt_r", "gt_l", "reg_words", "gold_lines")}
    obj.update(representacoes=convertido, veiculo_visto_treino=antigo["veiculo_visto_treino"],
               origem_detector="ls3 congelado da exportacao atual", diagnostico_v2=diag)
    for p in obj["representacoes"].values():
        b.auditar_unidades(p, obj)
    return obj


def fmt(v, n=3):
    return "—" if v is None else f"{v:.{n}f}".replace(".", ",")


def pareadas(R, bancada=None, grupo="todos"):
    return [r for r in R.get("paginas", {}).values() if "antes" in r and "depois" in r and
            (bancada is None or r["bancada"] == bancada) and
            (grupo == "todos" or r["visto_treino"] == (grupo == "vistos"))]


def resumo_pareado(rows, versao, rep):
    return estatisticas([r[versao]["metricas"][rep] for r in rows])


def conclusao(R):
    if not R.get("completa"):
        return {"estado": "pendente", "texto": "Comparação parcial: ainda não cabe decidir melhora."}
    a4, d4 = [resumo_pareado(pareadas(R, "golden_v4"), v, "linhas") for v in ("antes", "depois")]
    a3, d3 = [resumo_pareado(pareadas(R, "golden_v3_novo"), v, "linhas") for v in ("antes", "depois")]
    eps = 1e-12
    preserva4 = d4["tau"] >= a4["tau"]-eps and d4["quebras"] <= a4["quebras"]+eps
    melhora3 = (d3["tau"] >= a3["tau"]-eps and d3["quebras"] <= a3["quebras"]+eps and
                (d3["tau"] > a3["tau"]+eps or d3["quebras"] < a3["quebras"]-eps))
    piso = (d4["piso_interno"] <= a4["piso_interno"]+eps and
            d3["piso_interno"] <= a3["piso_interno"]+eps and
            (d4["piso_interno"] < a4["piso_interno"]-eps or d3["piso_interno"] < a3["piso_interno"]-eps))
    melhor = preserva4 and (melhora3 or piso)
    return {"estado": "melhor" if melhor else "nao_demonstrou_melhora", "preserva_v4": preserva4,
            "melhora_v3": melhora3, "melhora_piso": piso,
            "texto": "A v2 satisfaz o critério de melhora especificado." if melhor else
                     "A v2 não satisfaz o critério de melhora; o resultado negativo é preservado."}


def extremos(R):
    rows = pareadas(R)
    def key(r):
        a, d = [r[v]["metricas"]["linhas"] for v in ("antes", "depois")]
        return (d["quebras"]-a["quebras"], -(d["tau"]-a["tau"]), r["page_id"])
    ordenadas = sorted(rows, key=key)
    melhores = ordenadas[:3]
    ids = {r["page_id"] for r in melhores}
    piores = [r for r in reversed(ordenadas) if r["page_id"] not in ids][:3]
    return melhores, piores


def relatorio(R):
    s = ["# Extrator sem parágrafos v2", "", R.get("status", "Preparação da execução."), "",
         "## Implementação", ""]
    s.extend("- " + x for x in IMPLEMENTACAO)
    s += ["", "Configuração desta tabela: " + R.get("nome_config", "ABCDE inicial") + ".",
          "A pode ser desligado sem desligar B: nesse caso B ainda consulta calhas "
          "confirmadas para partir linhas, mas as faixas usam as zonas anteriores. "
          "C desliga toda evidência vetorial; D desliga correção de átomos; "
          "E desliga o isolamento/fusão de margens na representação nova."]
    s += ["", "Parâmetros numéricos fixos. A segunda iteração corrige B, "
          "restringe E e desliga D após o diagnóstico das bancadas; é desenvolvimento exploratório:", "",
          json.dumps(PARAM, ensure_ascii=False, sort_keys=True), "",
          "## Âncoras", ""]
    anc = R.get("ancoras", {})
    if anc.get("medias"):
        s += ["| Método | τ de palavras | Quebras/página |", "|---|---:|---:|"]
        for metodo, ms in anc["medias"].items():
            s.append(f"| {metodo} | {fmt(ms['tau'], 6)} | {fmt(ms['quebras'], 6)} |")
        s += ["", "Âncora aprovada." if anc.get("aprovada") else "Âncora não aprovada; avaliação nova interrompida.",
              "", "P2 e regra nas unidades são reexecutados; P1m é a sequência histórica "
              "reavaliada pela mesma medir(), sem refazer o extrator de caixas finas."]
    else:
        s.append(f"Conferência em andamento: {R.get('progresso_ancoras', 0)} páginas salvas.")
    if not anc.get("aprovada"):
        if R.get("erro"):
            s += ["", "Interrupção: " + R["erro"]]
        s += ["", "Nenhuma tabela nova é apresentada antes de reproduzir as âncoras."]
    else:
        s += ["", "## Comparação antes e depois", "",
              "Representação principal: linhas; faixas de coluna são diagnósticos adicionais. "
              "A tabela usa somente páginas pareadas concluídas. Médias por página, sem IC; "
              "uma execução determinística, sem treino.", "",
              "| Bancada | Grupo | Representação | n pareado | Versão | τ | Quebras/página | Piso interno/página | Unidades/página | Fidelidade de 12 | Sucessor de linhas |",
              "|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|"]
        for bancada in BANCADAS:
            for grupo in ("todos", "vistos", "nao_vistos"):
                rows = pareadas(R, bancada, grupo)
                if not rows:
                    continue
                for rep in REPS:
                    for v in ("antes", "depois"):
                        m = resumo_pareado(rows, v, rep)
                        s.append(f"| {bancada} | {grupo} | {rep} | {len(rows)} | {v} | "
                                 f"{fmt(m['tau'], 6)} | {fmt(m['quebras'], 6)} | {fmt(m['piso_interno'], 6)} | "
                                 f"{fmt(m['unidades'], 2)} | {fmt(m['fid12'], 4)} | {fmt(m['sucessor_linhas'], 4)} |")
        s += ["", "## Defeitos da auditoria", "",
              "Mesma auditar_pagina() em ambas as versões, nas mesmas páginas. "
              "D1–D4 e D6–D7 recebem unidades em linhas; D5 recebe as respectivas margens "
              "automáticas de colunas_margens. Conta páginas afetadas, não número de ocorrências.", "",
              "| Bancada | Grupo | n pareado | Detector | Antes | Depois |", "|---|---|---:|---|---:|---:|"]
        for bancada in BANCADAS:
            for grupo in ("todos", "vistos", "nao_vistos"):
                rows = pareadas(R, bancada, grupo)
                if not rows:
                    continue
                for det in ("D1", "D2", "D3", "D4", "D5", "D6", "D7"):
                    cont = [sum(det in r[v]["defeitos"] for r in rows) for v in ("antes", "depois")]
                    s.append(f"| {bancada} | {grupo} | {len(rows)} | {det} | {cont[0]} | {cont[1]} |")
        if R.get("auditoria_historica"):
            s += ["", "Conferência com auditoria_extrator_sem_paragrafos.json "
                  "na interseção de páginas disponível. O main da auditoria histórica "
                  "prioriza estruturas_golden_v4/linhas.jsonl e depois datasets_sem_caixas; "
                  "esta execução usa unidades_sem_caixas/bancadas. São exportações "
                  "diferentes, mesmo quando o page_id coincide; a coluna histórica não "
                  "substitui o antes pareado. D5 também recebe estruturas históricas "
                  "na auditoria original. A cobertura nula do v3 novo significa ausência "
                  "nessa auditoria, e não ausência de defeitos.", "",
                  "| Bancada | Páginas cobertas pelo JSON histórico | Detector | Histórico | Antes atual | Depois |",
                  "|---|---:|---|---:|---:|---:|"]
            for bc, dados in R["auditoria_historica"].items():
                for det, vals in dados["detectores"].items():
                    s.append(f"| {bc} | {dados['n']} | {det} | {vals['historico']} | "
                             f"{vals['antes']} | {vals['depois']} |")
        co = conclusao(R)
        s += ["", "## Resultado", "", co["texto"], "",
              "Critério aplicado à representação em linhas: o v4 não pode perder τ nem ganhar "
              "quebras; além disso, o v3 deve melhorar uma das duas medidas sem piorar a outra, "
              "ou o piso interno deve cair em uma bancada sem subir na outra. Faixas melhores "
              "sozinhas não declaram vitória da representação principal."]
        if co["estado"] != "pendente":
            s.append(f"Preserva v4: {'sim' if co['preserva_v4'] else 'não'}; melhora v3: {'sim' if co['melhora_v3'] else 'não'}; melhora piso: {'sim' if co['melhora_piso'] else 'não'}.")
            melhorou = sum(r["depois"]["metricas"]["linhas"]["quebras"] <
                          r["antes"]["metricas"]["linhas"]["quebras"] for r in pareadas(R))
            piorou = sum(r["depois"]["metricas"]["linhas"]["quebras"] >
                        r["antes"]["metricas"]["linhas"]["quebras"] for r in pareadas(R))
            s.append(f"Páginas com menos / mesmas / mais quebras nesta configuração: "
                     f"{melhorou} / {len(pareadas(R))-melhorou-piorou} / {piorou}. "
                     "As listas de extremos incluem empates quando faltam ganhos ou regressões.")
        s += ["", "## Páginas com maior mudança", "",
              "Ordenação por Δ de quebras em linhas, com Δ de τ como desempate. "
              "Os grupos identificam os menores e maiores deltas observados; se não houver "
              "ganho ou regressão, o sinal do delta deixa isso explícito.", "",
              "| Grupo | Bancada | page_id | Quebras antes | Depois | Δ quebras | τ antes | Depois | Δ τ |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|"]
        melhores, piores = extremos(R)
        for nome, rows in (("Menores deltas", melhores), ("Maiores deltas", piores)):
            for r in rows:
                a, d = [r[v]["metricas"]["linhas"] for v in ("antes", "depois")]
                s.append(f"| {nome} | {r['bancada']} | {r['page_id']} | {a['quebras']} | {d['quebras']} | "
                         f"{d['quebras']-a['quebras']:+d} | {fmt(a['tau'], 6)} | {fmt(d['tau'], 6)} | {fmt(d['tau']-a['tau'], 6)} |")
        avisos = [(r["page_id"], r.get("diagnostico_v2", {}).get("vetores_avisos", [])) for r in pareadas(R)]
        avisos = [(pid, xs) for pid, xs in avisos if xs]
        s += ["", "## Evidência vetorial e painéis", "",
              f"Páginas com aviso vetorial: {len(avisos)}.",
              "Os painéis finais são renderizados diretamente do PDF e da página "
              "indicados no page_id. O mapa antigo de imagens reutilizava um nome de "
              "imagem entre lotes e mostrou uma edição diferente na página do AC do "
              "v3 novo; as imagens iniciais excedentes ficam arquivadas em "
              "extrator_sem_paragrafos_v2/paineis_iniciais/ e não são evidência visual validada."]
        for pid, xs in avisos:
            s.append("- " + pid + ": " + "; ".join(xs))
        for x in R.get("paineis", []):
            s.append(f"- [{x['page_id']}]({x['arquivo']}): linhas antes e depois.")
        if not R.get("paineis"):
            s.append("Painéis ainda não gerados; a avaliação pode ser retomada.")
    if INDICE.exists():
        ix = ler_json(INDICE)
        s += ["", "## Rodadas e efeito por componente", "",
              "Inicial: todos ligados. Iteração 1: retirar um componente por vez, "
              "mantendo os outros quatro. Iteração 2, quando executada: uma combinação "
              "fixada a partir desses diagnósticos. A retirada mede efeito condicionado "
              "aos outros componentes, não efeito isolado. A seleção usa ambas as "
              "bancadas humanas; não constitui validação independente.", "",
              "| Rodada | Componentes ligados | Bancada | n | τ | Quebras/página | Piso interno | Unidades/página | Cumpre critério |",
              "|---|---|---|---:|---:|---:|---:|---:|---|"]
        for x in ix.values():
            for bancada, m in x["medias"].items():
                s.append(f"| {x['rodada']} | {x['componentes']} | {bancada} | {m['n']} | "
                         f"{fmt(m['tau'], 6)} | {fmt(m['quebras'], 6)} | "
                         f"{fmt(m['piso_interno'], 6)} | {fmt(m['unidades'], 2)} | "
                         f"{'sim' if x['conclusao']['estado'] == 'melhor' else 'não'} |")
        if R.get("completa") and "ABCDE inicial" in ix:
            inicial = ler_json(RAIZ / ix["ABCDE inicial"]["estado"])
            s += ["", "### Maiores mudanças na implementação inicial", "",
                  "Preserva os casos que motivaram a segunda iteração, inclusive as regressões.", "",
                  "| Grupo | Bancada | page_id | Quebras antes | Depois | Δ quebras | τ antes | Depois |",
                  "|---|---|---|---:|---:|---:|---:|---:|"]
            mi, pi = extremos(inicial)
            for grupo, rows in (("Melhores", mi), ("Piores", pi)):
                for r in rows:
                    a, d = [r[v]["metricas"]["linhas"] for v in ("antes", "depois")]
                    s.append(f"| {grupo} | {r['bancada']} | {r['page_id']} | {a['quebras']} | "
                             f"{d['quebras']} | {d['quebras']-a['quebras']:+d} | "
                             f"{fmt(a['tau'], 6)} | {fmt(d['tau'], 6)} |")
    if R.get("confianca"):
        s += ["", "## Incerteza pareada por veículo", "",
              "Bootstrap pareado por veículo; cada reamostra sorteia veículos com "
              "reposição e inclui todas as suas páginas, preservando a média por página. "
              "IC percentil de 95%, com semente e reamostras registradas no estado. "
              "Δ = depois − antes; em quebras/piso, negativo é melhor. "
              "Os IC são descritivos e não corrigem a seleção de componentes nas bancadas.", "",
              "| Bancada | Métrica | Δ médio | IC 95% |", "|---|---|---:|---|"]
        for bancada, d in R["confianca"]["bancadas"].items():
            for met, z in d.items():
                s.append(f"| {bancada} | {met} | {fmt(z['delta'], 6)} | "
                         f"[{fmt(z['ic95'][0], 6)}; {fmt(z['ic95'][1], 6)}] |")
        s += ["", "Ganho confiável neste diagnóstico: " +
              ("sim" if R["confianca"]["ganho_confiavel"] else "não") + ".",
              "Unidades finais completas são publicadas somente com critério de melhora "
              "cumprido e IC inteiramente favorável em quebras ou piso interno. "
              "Isso ainda exige avaliação futura em páginas independentes."]
    s += ["", "## Limitações", ""] + ["- " + x for x in LIMITACOES]
    s += ["", "## Retomada e proveniência", "",
          "Resultados e unidades são salvos por página, com hashes das fontes, do PDF, "
          "do detector e do código. Exportações finais são montadas desses caches em fluxo. "
          "As origens ficam em leitura; não há treino, multiprocessing, DataLoader ou GPU.", "",
          f"Páginas com antes salvo: {sum('antes' in r for r in R.get('paginas', {}).values())}; "
          f"com depois salvo: {sum('depois' in r for r in R.get('paginas', {}).values())}.",
          "", "Estado: " + R.get("fase", "preparacao") + ".",
          "", "Execução: venv/Scripts/python.exe -B orquestracao/analises/extrator_sem_paragrafos_v2.py"]
    if R.get("erro") and anc.get("aprovada"):
        s += ["", "Interrupção recuperável: " + R["erro"]]
    if R.get("fingerprint"):
        s += ["", "Fingerprint: " + R["fingerprint"], "", "Hashes das fontes:", ""]
        s.extend("- " + nome + ": " + val for nome, val in R["fontes"].items())
    if R.get("comando"):
        s += ["", "Comando desta configuração: `" + R["comando"] + "`."]
    if R.get("ram_minima_mb") is not None:
        s += ["", "RAM livre mínima observada: " + fmt(R["ram_minima_mb"], 1) +
              " MB; duração desta execução: " + fmt(R.get("tempo_execucao_s"), 1) + " s."]
    if R.get("exportacoes"):
        s += ["", "Unidades completas: resultados/unidades_sem_caixas_v2/bancadas/."]
    elif R.get("completa"):
        s += ["", "Sem exportação final aprovada. As unidades candidatas ficam nos "
              "caches por página; a exportação produzida pela implementação inicial "
              "foi arquivada em extrator_sem_paragrafos_v2/unidades_iniciais/."]
    return "\n".join(s) + "\n"


def catalogar(R, run):
    if not R.get("completa"):
        return
    ix = ler_json(INDICE) if INDICE.exists() else {}
    ix.pop("golden_v3_novo", None)
    nome = "".join(c for c in "ABCDE" if R.get("componentes", COMPONENTES).get(c)) or "nenhum"
    if "componentes" not in R:
        nome = "ABCDE inicial"
    elif R.get("rodada") == "Iteração 2":
        nome += " (B corrigido; E restrito)"
    ix[nome] = {"rodada": R.get("rodada", "Inicial"), "componentes": nome,
                "estado": run.relative_to(RAIZ).as_posix() + "/estado.json",
                "fingerprint": R["fingerprint"], "conclusao": conclusao(R),
                "comando": R.get("comando"),
                "medias": {bc: {**resumo_pareado(pareadas(R, bc), "depois", "linhas"),
                                 "n": len(pareadas(R, bc))} for bc in BANCADAS}}
    gravar(INDICE, ix)


def salvar_estado(R, run):
    gravar(run / "estado.json", R)
    catalogar(R, run)
    gravar(MD, relatorio(R))
    gravar(OUT / "resultado.json", R)


def medir_confianca(R):
    """IC descritivo da diferenca pareada; nao altera nenhuma metrica."""
    nboot, seed = 2000, 20261008
    out = {"semente": seed, "reamostras": nboot, "bancadas": {}}
    for bc in BANCADAS:
        rows = pareadas(R, bc)
        grupos = collections.defaultdict(list)
        for r in rows:
            grupos[r["uf"]].append(r)
        ufs = sorted(grupos)
        rng = random.Random(f"{seed}-{bc}")
        amostras = {k: [] for k in ("tau", "quebras", "piso_interno")}
        deltas = {uf: {k: [r["depois"]["metricas"]["linhas"][k] -
                           r["antes"]["metricas"]["linhas"][k] for r in grupos[uf]]
                       for k in amostras} for uf in ufs}
        for _ in range(nboot):
            sorteio = [rng.choice(ufs) for _ in ufs]
            for k in amostras:
                amostras[k].append(statistics.mean(v for uf in sorteio for v in deltas[uf][k]))
        out["bancadas"][bc] = {}
        for k, xs in amostras.items():
            xs.sort()
            out["bancadas"][bc][k] = {
                "delta": statistics.mean(v for uf in ufs for v in deltas[uf][k]),
                "ic95": [u.percentil(xs, .025), u.percentil(xs, .975)], "veiculos": len(ufs)}
    favoravel = (out["bancadas"]["golden_v3_novo"]["quebras"]["ic95"][1] < 0 or
                 any(out["bancadas"][bc]["piso_interno"]["ic95"][1] < 0 for bc in BANCADAS))
    out["ganho_confiavel"] = conclusao(R)["estado"] == "melhor" and favoravel
    return out


def conferir_auditoria_historica(R):
    dados = ler_json(RAIZ / "resultados/auditoria_extrator_sem_paragrafos.json")["paginas"]
    out = {}
    for bc in BANCADAS:
        rows = [r for r in pareadas(R, bc) if r["page_id"] in dados]
        out[bc] = {"n": len(rows), "detectores": {}}
        for det in ("D1", "D2", "D3", "D4", "D5", "D6", "D7"):
            out[bc]["detectores"][det] = {
                "historico": sum(any(x["detector"] == det for x in dados[r["page_id"]]["achados"]) for r in rows),
                **{v: sum(det in r[v]["defeitos"] for r in rows) for v in ("antes", "depois")}}
    return out


def publicar_unidades(R, run, fontes):
    """Reconstroi o esquema original, mantendo uma unica pagina em memoria."""
    inventario = {}
    for bancada, esperado in BANCADAS.items():
        alvo = destino(NOVO / "bancadas" / (bancada + ".jsonl"))
        temp = alvo.with_suffix(".jsonl.tmp")
        n = 0
        with open(temp, "w", encoding="utf-8", newline="\n") as f:
            for obj in jsonl(fontes / "bancadas" / (bancada + ".jsonl")):
                row = R["paginas"].get(obj["page_id"], {})
                if "depois" not in row:
                    continue
                novo = ler_json(run / "paginas" / (chave(obj["page_id"]) + ".json"))
                exigir(novo["fingerprint"] == row["fingerprint_v2"], "Cache mudou antes da publicacao")
                f.write(json.dumps(novo["objeto"], ensure_ascii=False, allow_nan=False) + "\n")
                n += 1
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, alvo)
        inventario[bancada] = {"paginas": n, "esperadas": esperado,
                               "completa": n == esperado, "sha256": sha(alvo)}
    gravar(NOVO / "manifesto.json", {"versao": VERSAO, "fingerprint": R["fingerprint"],
                                   "parametros": PARAM, "bancadas": inventario,
                                   "expansao": "ordem_sem_bbox.fluxo() por unidade",
                                   "aviso": "Exportacao parcial enquanto houver bancada incompleta; somente bancadas humanas"})
    return inventario


def criar_paineis(R, run, fontes):
    """Reaproveita o estilo do comparador; apenas uma imagem/PDF por vez."""
    from PIL import Image, ImageDraw
    melhores, piores = extremos(R)
    escolhidas = melhores + piores
    ids = {r["page_id"] for r in escolhidas}
    restantes = sorted((r for r in pareadas(R) if r["page_id"] not in ids),
                        key=lambda r: (-abs(len(r["depois"]["defeitos"])-len(r["antes"]["defeitos"])), r["page_id"]))
    escolhidas += restantes[:max(0, 8-len(escolhidas))]
    exigir(len(escolhidas) == 8, "Faltam paginas para os paineis")
    ids = {r["page_id"] for r in escolhidas}
    indice = {r["page_id"]: i+1 for i, r in enumerate(escolhidas)}
    paineis = {r["page_id"]: r for r in R.get("paineis", [])}
    for bancada in BANCADAS:
        for obj in jsonl(fontes / "bancadas" / (bancada + ".jsonl")):
            pid = obj["page_id"]
            if pid not in ids:
                continue
            row = R["paginas"][pid]
            nome = f"{indice[pid]:02d}_{chave(pid)}.jpg"
            alvo = destino(OUT / nome)
            fundo_hash = R["fontes"][(RAIZ / "data/raw" / obj["uf"] / obj["arquivo"]).relative_to(RAIZ).as_posix()]
            fp = digest([row["fingerprint_v2"], row["antes"], fundo_hash, sha(Path(visual.__file__))])
            previo = paineis.get(pid)
            if previo and previo["fingerprint"] == fp and alvo.exists() and sha(alvo) == previo["sha256"]:
                continue
            depois = ler_json(run / "paginas" / (chave(pid) + ".json"))["objeto"]
            # O mapa de imagens derivadas pode reutilizar um nome de outro lote.
            # Renderiza sempre o PDF/page_id efetivo, sem confiar nesse mapa.
            import pymupdf
            with pymupdf.open(RAIZ / "data/raw" / obj["uf"] / obj["arquivo"]) as pdf:
                page = pdf[obj["pagina"]]
                pix = page.get_pixmap(matrix=pymupdf.Matrix(1300/page.rect.height, 1300/page.rect.height), alpha=False)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            altura = 1300
            redimensionada = img.resize((round(img.width*altura/img.height), altura), Image.Resampling.LANCZOS)
            img.close()
            img = redimensionada
            antes_p = obj["representacoes"]["linhas"]
            depois_p = depois["representacoes"]["linhas"]
            folha = Image.new("RGB", (img.width*2+30, altura+130), "white")
            d = ImageDraw.Draw(folha)
            d.text((6, 4), pid, fill="black", font=visual.fonte(16))
            for v, p, x in (("antes", antes_p, 6), ("depois", depois_p, img.width+36)):
                met = row[v]["metricas"]["linhas"]
                d.text((x, 36), f"{v.capitalize()}: {len(p['bounding_boxes'])} unidades", fill="black", font=visual.fonte(24))
                d.text((x, 72), f"τ {fmt(met['tau'], 6)}; {met['quebras']} quebras; piso {met['piso_interno']}",
                       fill="black", font=visual.fonte(20))
                desenho = visual.painel(img, obj["dimensions"], p["bounding_boxes"], True)
                folha.paste(desenho, (x-6, 130))
                desenho.close()
            temp = alvo.with_suffix(".jpg.tmp")
            folha.save(temp, format="JPEG", quality=85)
            os.replace(temp, alvo)
            folha.close()
            img.close()
            paineis[pid] = {"page_id": pid, "arquivo": "extrator_sem_paragrafos_v2/"+nome,
                            "sha256": sha(alvo), "fingerprint": fp}
            R["paineis"] = sorted(paineis.values(), key=lambda x: indice[x["page_id"]])
            salvar_estado(R, run)
            gc.collect()
    exigir(len(R.get("paineis", [])) == 8, "Paineis incompletos")


def comparar(R, run, fontes, args):
    treino = set(ler_json(RAIZ / "data/processed/splits.json")["treino"])
    processadas = 0
    for bancada, esperado in BANCADAS.items():
        b.UNIDADES = fontes
        ids = set()
        for obj, _ in b.paginas(bancada, "linhas"):
            pid = obj["page_id"]
            exigir(pid not in ids, "Pagina duplicada na bancada")
            ids.add(pid)
            memoria_minima(args.min_ram_mb)
            visto = obj["uf"] in treino
            exigir(visto == obj["veiculo_visto_treino"], "Marcacao visto/nao visto desatualizada")
            row = R["paginas"].setdefault(pid, {"page_id": pid, "uf": obj["uf"],
                                               "bancada": bancada, "visto_treino": visto})
            if "antes" not in row:
                row["antes"] = medir_reps(obj)
                salvar_estado(R, run)
            if "depois" not in row:
                if args.max_paginas and processadas >= args.max_paginas:
                    R["fase"] = "parcial"
                    R["status"] = "Ensaio parcial encerrado; retome sem --max-paginas para completar."
                    salvar_estado(R, run)
                    return
                pdf = RAIZ / "data/raw" / obj["uf"] / obj["arquivo"]
                pdf_rel = pdf.relative_to(RAIZ).as_posix()
                pdfhash = R["fontes"][pdf_rel]
                R.setdefault("pdf_sha256", {})[pdf_rel] = pdfhash
                det = ler_json(fontes / "cache/detector" / (chave(pid) + ".json"))
                h = max(.1, statistics.median(w[4]-w[2] for w in obj["palavras"]))
                fp = digest([R["fingerprint"], obj, pdfhash, det])
                cache = run / "paginas" / (chave(pid) + ".json")
                if cache.exists():
                    salvo = ler_json(cache)
                    exigir(salvo["fingerprint"] == fp, f"Cache v2 incompativel: {pid}")
                    novo = salvo["objeto"]
                else:
                    vet = extrair_vetores(obj, pdfhash, OUT / "evidencia", h) if COMPONENTES["C"] else {
                        "verticais": [], "horizontais": [], "retangulos": [], "tabelas": [], "avisos": []}
                    novo = converter_v2(obj, det, vet)
                    gravar(cache, {"fingerprint": fp, "objeto": novo})
                # Usa a constante UNIDADES trocada, sem editar bancada_ordenadores.
                # medir_reps recebe a pagina corrente; a verificacao final le o shard.
                b.UNIDADES = NOVO
                row["depois"] = medir_reps(novo)
                row["diagnostico_v2"] = novo["diagnostico_v2"]
                row["fingerprint_v2"] = fp
                processadas += 1
                del novo
                R["fase"] = "comparacao"
                R["status"] = "Comparação em andamento; resultados parciais pareados."
                mem = memoria_minima(args.min_ram_mb)
                R["memoria_ultima_pagina"] = mem
                if mem:
                    R["ram_minima_mb"] = min(R.get("ram_minima_mb", float("inf")), mem["ram_livre_mb"])
                salvar_estado(R, run)
                print(f"v2 {len(pareadas(R))}/{sum(BANCADAS.values())}: {pid}", flush=True)
                gc.collect()
        exigir(len(ids) == esperado, f"Bancada {bancada} incompleta")
    ids4 = {r["page_id"] for r in R["paginas"].values() if r["bancada"] == "golden_v4"}
    ids3 = {r["page_id"] for r in R["paginas"].values() if r["bancada"] == "golden_v3_novo"}
    exigir(not ids4 & ids3, "V3 novo inclui pagina do v4")
    R["completa"] = len(pareadas(R)) == sum(BANCADAS.values())


def conferir_exportacao(R):
    """Compara a leitura monkeypatchada dos shards com as medidas por pagina."""
    b.UNIDADES = NOVO
    for bancada, esperado in BANCADAS.items():
        ids = set()
        for obj, p in b.paginas(bancada, "linhas"):
            b.auditar_unidades(p, obj)
            ids.add(obj["page_id"])
            row = R["paginas"][obj["page_id"]]
            ordem, _ = b.prever(p, obj["palavras"], "regra_colunas")
            met = b.metricas(obj, p, ordem)
            exigir(all(met[k] == row["depois"]["metricas"]["linhas"][k] for k in b.METRICAS),
                   "Medidas do shard publicado divergiram")
        exigir(len(ids) == esperado, "Exportacao v2 incompleta")



def executar(args):
    COMPONENTES.update({c: getattr(args, c) for c in "ABCDE"})
    nome_config = "".join(c for c in "ABCDE" if COMPONENTES[c]) or "nenhum"
    rodada = "Iteração " + str(args.iteracao) if args.iteracao else "Inicial"
    inicio = time.perf_counter()
    if "torch" in sys.modules:
        sys.modules["torch"].set_num_threads(4)
    R = {"fase": "preparacao", "status": "Execução iniciada; nenhuma métrica nova antes das âncoras.",
         "paginas": {}, "completa": False, "nome_config": nome_config, "rodada": rodada,
         "comando": "venv/Scripts/python.exe -B orquestracao/analises/extrator_sem_paragrafos_v2.py " +
                    " ".join("--sem-" + c.lower() for c in "ABCDE" if not COMPONENTES[c]) +
                    (" --iteracao " + str(args.iteracao) if args.iteracao else "")}
    run = None
    with trava():
        try:
            gravar(MD, relatorio(R))
            memoria_minima(args.min_ram_mb)
            dependencias = {Path(__file__), Path(ds.__file__), Path(ep.__file__), Path(o.__file__),
                            Path(e.__file__), Path(b.__file__), Path(u.__file__),
                            Path(auditoria.__file__), Path(visual.__file__), *b.DEP_PATHS,
                            RAIZ / "data/processed/splits.json", e.JSON,
                            RAIZ / "resultados/auditoria_extrator_sem_paragrafos.json"}
            splits = ler_json(RAIZ / "data/processed/splits.json")
            exigir(len(splits["treino"]) == 7 and splits["validacao"] == ["official_diary_rn"] and
                   set(splits["teste"]) == {"official_diary_ce", "official_diary_ma", "official_diary_rj"},
                   "Divisao por veiculo difere do protocolo pedido")
            todos = set()
            for nome, esperado in BANCADAS.items():
                entrada = ANTIGO / "bancadas" / (nome + ".jsonl")
                dependencias.add(entrada)
                ids = set()
                for obj in jsonl(entrada):
                    pid = obj["page_id"]
                    exigir(pid not in ids and pid not in todos and obj["particao"] == nome,
                           "Coortes humanas duplicadas ou particao divergente")
                    ids.add(pid)
                    for rep in REPS:
                        b.auditar_unidades(obj["representacoes"][rep], obj)
                    dependencias.add(ANTIGO / "cache/detector" / (chave(pid) + ".json"))
                    dependencias.add(RAIZ / "data/raw" / obj["uf"] / obj["arquivo"])
                exigir(len(ids) == esperado, f"Bancada {nome} incompleta")
                todos.update(ids)
            # Hash em blocos; os PDFs e JSONL nao ficam carregados em memoria.
            H = {p.relative_to(RAIZ).as_posix(): sha(p) for p in sorted(dependencias)}
            fp = digest([VERSAO, PARAM, COMPONENTES, H])
            run = OUT / "cache" / fp
            b.OUT = OUT / "avaliacao_compartilhada"
            inicial = {**R, "fingerprint": fp, "fontes": H, "parametros": PARAM,
                       "componentes": dict(COMPONENTES),
                       "config": {"device": "cpu", "threads_max": 4, "num_workers": 0, "sem_treino": True}}
            R = ler_json(run / "estado.json") if (run / "estado.json").exists() else inicial
            exigir(R["fingerprint"] == fp, "Estado de outra execucao")
            R.pop("erro", None)
            R.update(nome_config=nome_config, rodada=rodada)
            fontes, hashes = congelar_bancadas(run, H)
            R["snapshots"] = hashes
            salvar_estado(R, run)
            conferir_ancoras(R, run, fontes, args.min_ram_mb)
            if args.somente_ancoras:
                R["fase"] = "ancoras_concluidas"
                R["status"] = "Âncoras conferidas; comparação não solicitada nesta execução."
                salvar_estado(R, run)
                return
            comparar(R, run, fontes, args)
            if R["completa"]:
                R["confianca"] = medir_confianca(R)
                R["auditoria_historica"] = conferir_auditoria_historica(R)
                if R["confianca"]["ganho_confiavel"] and not args.ablacao:
                    R["exportacoes"] = publicar_unidades(R, run, fontes)
                    conferir_exportacao(R)
                R["status"] = conclusao(R)["texto"]
                R["fase"] = "avaliacao_concluida"
                salvar_estado(R, run)
                if not args.sem_paineis:
                    criar_paineis(R, run, fontes)
                    R["fase"] = "concluida"
                for fonte_rel, hash_antes in H.items():
                    exigir(sha(RAIZ / fonte_rel) == hash_antes,
                           f"Fonte mudou durante a execucao; snapshot preservado: {fonte_rel}")
            R["tempo_execucao_s"] = time.perf_counter() - inicio
            salvar_estado(R, run)
            print(R["status"], flush=True)
        except Exception as exc:
            R["erro"] = f"{type(exc).__name__}: {exc}"
            R["status"] = "Execução interrompida; caches preservados para diagnóstico e retomada."
            R["fase"] = "interrompida"
            if run is None:
                gravar(MD, relatorio(R))
            else:
                salvar_estado(R, run)
            raise


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--somente-ancoras", action="store_true")
    ap.add_argument("--max-paginas", type=int, default=0)
    ap.add_argument("--sem-paineis", action="store_true")
    ap.add_argument("--min-ram-mb", type=float, default=800)
    ap.add_argument("--ablacao", action="store_true", help="Iteracao 1: retira A, B, C, D e E, um por vez")
    ap.add_argument("--iteracao", type=int, choices=(0, 1, 2), default=0)
    for c in "ABCDE":
        grupo = ap.add_mutually_exclusive_group()
        grupo.add_argument("--com-" + c.lower(), dest=c, action="store_true")
        grupo.add_argument("--sem-" + c.lower(), dest=c, action="store_false")
        ap.set_defaults(**{c: True})
    args = ap.parse_args()
    exigir(args.max_paginas >= 0 and args.min_ram_mb >= 350, "Limites de paginas/RAM invalidos")
    # Preserva o resultado executado antes de acrescentar as opcoes de ablacao.
    for p in sorted((OUT / "cache").glob("*/estado.json")):
        antigo = ler_json(p)
        if antigo.get("completa"):
            catalogar(antigo, p.parent)
            if "nome_config" not in antigo and not (OUT / "rodada_inicial.md").exists() and MD.exists():
                gravar(OUT / "rodada_inicial.md", MD.read_text(encoding="utf-8"))
    # A implementacao inicial exportava mesmo uma candidata reprovada. Arquiva
    # seus arquivos individualmente, conferindo os dois caminhos no escopo.
    manifesto = NOVO / "manifesto.json"
    if manifesto.exists() and ler_json(manifesto).get("versao") == "extrator-sem-paragrafos-v2-1":
        for src in [NOVO / "bancadas" / (bc + ".jsonl") for bc in BANCADAS] + [manifesto]:
            if src.exists():
                exigir(src.resolve().is_relative_to(NOVO.resolve()), "Origem de arquivo fora do escopo")
                alvo = destino(OUT / "unidades_iniciais" / src.relative_to(NOVO))
                exigir(not alvo.exists(), "Arquivo inicial ja arquivado; nao sobrescrever")
                os.replace(src, alvo)
    resultado = OUT / "resultado.json"
    if resultado.exists():
        ultimo = ler_json(resultado)
        manter = {Path(p["arquivo"]).name for p in ultimo.get("paineis", [])}
        if ultimo.get("fase") == "concluida" and len(manter) == 8:
            for src in sorted(OUT.glob("*.jpg")):
                if src.name not in manter:
                    exigir(src.resolve().is_relative_to(OUT.resolve()), "Imagem fora do escopo")
                    alvo = destino(OUT / "paineis_iniciais" / src.name)
                    exigir(not alvo.exists() or sha(alvo) == sha(src), "Imagem arquivada diferente")
                    os.replace(src, alvo)
    if args.ablacao:
        for desligar in "ABCDE":
            variante = copy.copy(args)
            variante.iteracao = 1
            variante.sem_paineis = True
            for c in "ABCDE":
                setattr(variante, c, c != desligar)
            print(f"Iteração 1: desligando {desligar}", flush=True)
            executar(variante)
            gc.collect()
    else:
        executar(args)


if __name__ == "__main__":
    main()
