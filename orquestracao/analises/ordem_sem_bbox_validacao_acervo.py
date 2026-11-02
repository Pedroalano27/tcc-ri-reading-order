"""Valida o ordenador congelado em paginas novas do acervo do TCC, somente CPU.

A ordem humana cega do golden_v3 e a ordem silver do teste sao avaliadas em
separado. A regua principal usa a sequencia REAL de palavras; a mediana dos
postos dos blocos e secundaria. A XY-cut recebe tambem a mesma politica de
margens, para nao atribuir a projecao um ganho dessa politica. Nao ajusta nada.

Uso na raiz, com o Python do projeto:
    venv\\Scripts\\python.exe -B orquestracao\\analises\\ordem_sem_bbox_validacao_acervo.py
    ... ordem_sem_bbox_validacao_acervo.py --do-zero
    ... ordem_sem_bbox_validacao_acervo.py --conferir
    ... ordem_sem_bbox_validacao_acervo.py --autoteste

Somente cria o relatorio solicitado e caches/intermediarios sob resultados/
ordem_sem_bbox_cache/. Le PDFs com pdfplumber e palavras_da_pagina; detector
local, caso necessario, e explicitamente CPU e offline. Cada pagina pronta e
persistida; JSON atomico permite retomar apos queda. --do-zero refaz extracao,
predicoes e estatisticas, sem apagar caches ou tocar em data/. --conferir
regenera o Markdown dos numeros persistidos e confere hashes e igualdade.
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
import concurrent.futures
import hashlib
import json
import math
import os
import re
import statistics
import warnings

import numpy as np
from scipy.stats import wilcoxon
from orquestracao.analises import ordem_sem_bbox as original
from src.data.extrator import palavras_da_pagina, RE_TRANSLINEACAO, RE_ESPACO_PONT
from src.data.layout import carregar_cache, Detector, MODELO, REVISAO, DPI
from src.data.regioes import linhas, RE_MARCACAO
from src.eval.baselines import caixas, xycut
from src.eval.metrics import kendall_tau, acerto_sucessor, ard_normalizado
from src.eval.protocolo import carregar_particao, referencia, ordem_entrada, DIR_BLOCOS

CACHE = RAIZ / "resultados/ordem_sem_bbox_cache"
RELATORIO = RAIZ / "resultados/ordem_sem_bbox_validacao_acervo.md"
ESTADO = CACHE / "validacao_acervo.json"
FIXA = original.Config("projecao_local_margens", 0.45, 1.2, 0.08)
SEM_MARGENS = original.Config("projecao_local", 0.45, 1.2, 0.08)
VERSAO = "acervo-v1"
METODOS = {
    "xycut": "XY-cut pura",
    "xycut_margens": "XY-cut + mesmas margens",
    "ingenua": "Ingênua",
    "fixo": "Sem bbox fina — congelado",
    "sem_margens": "Sem bbox fina sem margens (sensibilidade)",
}
CONJUNTOS = {
    "A_novas": "A — humanas novas",
    "A_repetidas": "A — humanas repetidas",
    "B_novas": "B — silver novas",
    "B_todas": "B — silver completo",
    "B_repetidas": "B — silver repetidas (diagnóstico)",
}
REGRAS = {
    "topo_centro": 0.07, "topo_base": 0.10, "rodape_centro": 0.95,
    "bootstrap": 5000, "semente": 20261003,
}

# Diagnosticos qualitativos feitos apos medir, por inspecao das figuras e dos
# identificadores/textos nos caches. Nao entram no preditor, referencia ou filtros.
INSPECAO = {
    "official_diary_ma/executive_official_diary_2021-11-19.pdf#p55":
        "Expediente e quadro de preços: calha local do quadro não detectada; rótulos de lista ficam num bloco vertical separado das descrições, e um bloco v3 une células das duas colunas. A saída intercala esses blocos, mas o silver também põe seções visualmente fora de ordem: a perda não demonstra erro humano. Tabelas lado a lado/calha ausente já apareciam em Manaus/Caxias no v4; referência v3 que fatora a lista e mistura colunas é limitação nova desta validação.",
    "official_diary_ac/executive_official_diary_2022-12-02.pdf#p419":
        "Cabeçalho/área acima da tabela: topo exato inverte campos laterais; linhas do título do relatório são interrompidas pelo campo de página/data à direita. A tabela permanece atômica. Desempate de campos do cabeçalho já aparecia em AC/MS no v4; esta instância de campo lateral no corpo é nova.",
    "official_diary_se/DOE-SE_2022-03-18_4475.pdf#p15":
        "Marcas de diagramação textFrameStart/SEGRASE mudam para antes do rodapé, embora a ordem humana v3 as tenha mantido entre blocos de conteúdo. Campo de número/página também se fragmenta. As tabelas empilhadas ficam preservadas. Margens/campos fragmentados eram conhecidos no v4; avaliar marcas como blocos ordenáveis nesta referência v3 é uma nova incompatibilidade de representação.",
    "official_diary_ma/executive_official_diary_2026-01-14.pdf#p46":
        "Cabeçalho e data/assinatura: o número da página vira átomo picture separado da data, fragmentando o bloco v3; a ordem silver data→assinatura diverge da posição visual assinatura→data. A tabela central não se intercala. Campos de cabeçalho e imagens que capturam texto já ocorriam no v4; discrepância semântica do silver limita a atribuição causal.",
    "official_diary_rj/Parte I (Poder Executivo)_2024-02-02.pdf#p34":
        "Cabeçalho sobre tabela longa: campos muito curtos com top diferentes são permutados; DIÁRIO OFICIAL é átomo picture. Corpo da tabela preservado e nenhuma região fragmentada. Mesmo motivo geométrico de cabeçalho/átomos do v4; perda pequena em palavras e grande sensibilidade regional por haver poucos blocos.",
    "official_diary_ma/executive_official_diary_2021-09-20.pdf#p26":
        "Cabeçalho: campo de data/número se reparte porque o número é picture; a margem ordena fragmentos por top e troca o campo esquerdo com o direito. Corpo é uma tabela única preservada. Calhas detectadas aqui são células da tabela, não duas colunas de leitura: viés do estratificador. Campos e dependência da delimitação de átomos são conhecidos no v4.",
    "official_diary_pi_v2/executive_official_diary_2025_11_07_216_2025.pdf#p223":
        "Rodapé: contPageBreak pertence ao mesmo bloco v3 que edição/data, mas a regra de marcas o emite separadamente antes do rodapé, quebrando a contiguidade. A mediana conserva a ordem perfeita dos blocos e esconde a interrupção. Campos de rodapé intercalados eram conhecidos em Barra do Piraí/v4; o marcador incorporado ao bloco v3 é uma incompatibilidade nova.",
    "official_diary_ma/executive_official_diary_2021-09-29.pdf#p54":
        "Cabeçalho: o átomo picture do número da página separa data/número; diferenças de top invertem os campos superiores. Tabela única permanece atômica. Calhas internas correspondem a células, não a colunas independentes de texto. Repete o erro conhecido de cabeçalho no v4, com falso multicoluna produzido pelo estratificador.",
}
SINTESE_ERROS = (
    "Os oito casos foram inspecionados nas figuras intermediárias e nas sequências/caixas do cache. "
    "Cabeçalho/rodapé, desempate por topo e dependência da delimitação dos átomos já constavam das inspeções do v4 (AC/MS, Barra do Piraí e Caxias); "
    "tabelas lado a lado e calha ausente também (Manaus/PB/Caxias). As novidades são da **régua v3/silver**: "
    "bloco que mistura células de colunas distintas, marcadores isolados/incorporados a blocos humanos, lista fatorada em rótulos e texto e fluxo silver visualmente incoerente. "
    "Não há evidência para atribuir estas oito perdas a título atravessando colunas; esse motivo foi uma hipótese de desenvolvimento (ponte/ARTIGOS no MA) e não deve ser inventado aqui. "
    "Também não confundir calhas entre células com colunas de jornal. Os casos não justificam reajustar o método após o teste."
)


def ler_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for numero, linha in enumerate(f, 1):
            if linha.strip():
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSONL inválido: {path}:{numero}") from e


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for parte in iter(lambda: f.read(1024 * 1024), b""):
            h.update(parte)
    return h.hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def chave(pid):
    return hashlib.sha256(pid.encode("utf-8")).hexdigest()[:24]


def gravar(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def carregar(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def fontes_e_amostra():
    a_dir = RAIZ / "data/golden/_avaliacao/golden_v3"
    tarefas = list(ler_jsonl(a_dir / "tarefas.jsonl"))
    refs = {r["page_id"]: r for r in ler_jsonl(a_dir / "referencia.jsonl")
            if r.get("status") == "concluida"}
    v4 = list(ler_jsonl(RAIZ / "data/golden/golden_v4/tarefas.jsonl"))
    ids_v4 = {p["page_id"] for p in v4}
    veiculos_v4 = {p["uf"] for p in v4}
    b = carregar_particao("teste")
    if Path(DIR_BLOCOS).resolve() != (RAIZ / "data/processed/blocos").resolve():
        raise ValueError("TCC_DIR_BLOCOS aponta outra segmentação; esta validação exige blocos v3 do protocolo.")
    amostra = []
    for p in tarefas:
        r = refs.get(p["page_id"])
        amostra.append({"p": p, "gt": r.get("ordem", []) if r else [], "fonte": "A",
                        "repetida": p["page_id"] in ids_v4,
                        "veiculo_visto": p["uf"] in veiculos_v4,
                        "nota_humana": r.get("nota", "") if r else "referência ausente"})
    for p in b:
        amostra.append({"p": p, "gt": referencia(p), "fonte": "B",
                        "repetida": p["page_id"] in ids_v4,
                        "veiculo_visto": p["uf"] in veiculos_v4, "nota_humana": ""})
    paths = [a_dir / n for n in ("tarefas.jsonl", "referencia.jsonl", "LEIAME.md")]
    paths += [RAIZ / "data/golden/golden_v4/tarefas.jsonl", RAIZ / "data/processed/splits.json"]
    paths += [RAIZ / f"data/processed/blocos/{uf}.jsonl" for uf in sorted({p["uf"] for p in b})]
    paths += [RAIZ / f"data/processed/layout/{uf}.jsonl" for uf in sorted({q["p"]["uf"] for q in amostra})]
    paths += [RAIZ / n for n in (
        "orquestracao/analises/ordem_sem_bbox.py", "src/data/extrator.py", "src/data/regioes.py",
        "src/data/layout.py", "src/eval/metrics.py", "src/eval/protocolo.py", "src/eval/baselines.py",
        "resultados/ordem_sem_bbox.md", "resultados/ordem_sem_bbox.json",
        "resultados/revisao_ordem_sem_bbox.md")]
    if (RAIZ / "resultados/ordem_sem_bbox_justo.md").exists():
        paths.append(RAIZ / "resultados/ordem_sem_bbox_justo.md")
    paths.append(Path(__file__).resolve())
    paths += sorted({RAIZ / "data/raw" / q["p"]["uf"] / q["p"]["arquivo"] for q in amostra})
    hashes = {p.relative_to(RAIZ).as_posix(): sha(p) for p in paths if p.exists()}
    return amostra, hashes


def extrair_pdf(tarefa):
    """Abre cada PDF uma vez e persiste cada pagina antes de passar a seguinte."""
    import pdfplumber
    pdf_path, pedidos, hash_pdf, hash_extrator, do_zero = tarefa
    saida, pendentes = [], []
    for p in pedidos:
        path = CACHE / "palavras" / (chave(p["page_id"]) + ".json")
        fp = digest([VERSAO, hash_pdf, hash_extrator, p["pagina"]])
        antigo = carregar(path) if not do_zero else None
        if antigo and antigo.get("fingerprint") == fp and not antigo.get("erro"):
            saida.append(antigo)
        else:
            pendentes.append((p, path, fp))
    if not pendentes:
        return saida
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p, path, fp in pendentes:
                r = {"page_id": p["page_id"], "fingerprint": fp, "erro": None}
                try:
                    page = pdf.pages[int(p["pagina"])]
                    ws = palavras_da_pagina(page)
                    r.update(dimensions={"width": float(page.width), "height": float(page.height)},
                             bbox=list(page.bbox), rotation=page.rotation,
                             cropbox=list(page.cropbox), mediabox=list(page.mediabox),
                             palavras=[[w["t"], w["x0"], w["top"], w["x1"], w["bottom"]] for w in ws])
                    page.close()
                except Exception as e:
                    r["erro"] = f"{type(e).__name__}: {e}"
                gravar(path, r)
                saida.append(r)
    except Exception as e:
        for p, path, fp in pendentes:
            r = {"page_id": p["page_id"], "fingerprint": fp, "erro": f"PDF ilegível: {e}"}
            gravar(path, r)
            saida.append(r)
    return saida


def obter_layout(paginas):
    """Usa o cache original sem escrever nele; faltantes vao ao cache novo, CPU."""
    cache = carregar_cache(ufs={p["uf"] for p in paginas})
    fontes = {pid: "data/processed/layout" for pid in cache}
    detector = None
    for p in paginas:
        pid = p["page_id"]
        if pid in cache and cache[pid] is not None:
            continue
        path = CACHE / "layout" / (chave(pid) + ".json")
        salvo = carregar(path)
        if salvo and salvo.get("revisao") == REVISAO and salvo.get("regioes") is not None:
            cache[pid] = salvo["regioes"]
            fontes[pid] = "resultados/ordem_sem_bbox_cache/layout"
            continue
        import pdfplumber
        if detector is None:
            detector = Detector(dispositivo="cpu", permitir_download=False)
            detector.torch.set_num_threads(2)
        try:
            with pdfplumber.open(RAIZ / "data/raw" / p["uf"] / p["arquivo"]) as pdf:
                page = pdf.pages[int(p["pagina"])]
                if page.rotation and tuple(page.cropbox) != tuple(page.mediabox):
                    raise ValueError("rotação com CropBox diferente da MediaBox")
                pi = page.to_image(resolution=DPI)
                regs = detector([pi.original.convert("RGB")], [(tuple(pi.bbox), float(pi.scale))])[0]
            salvo = {"page_id": pid, "modelo": MODELO, "revisao": REVISAO, "regioes": regs, "device": "cpu"}
        except Exception as e:
            salvo = {"page_id": pid, "revisao": REVISAO, "regioes": None, "erro": str(e)}
        gravar(path, salvo)
        cache[pid] = salvo["regioes"]
        fontes[pid] = "resultados/ordem_sem_bbox_cache/layout"
    return cache, fontes


def limpar(texto):
    return RE_ESPACO_PONT.sub(r"\1", RE_TRANSLINEACAO.sub(r"\1\2", texto))


def preparar(q, extraido, det):
    """Audita coordenadas antes da avaliacao; regioes vazias ficam contabilizadas."""
    p = q["p"]
    if extraido.get("erro"):
        return None, {"erro": extraido["erro"]}
    ws, rs = extraido["palavras"], p["bounding_boxes"]
    ids = [r["id"] for r in rs]
    if len(set(ids)) != len(ids) or len(q["gt"]) != len(ids) or set(q["gt"]) != set(ids):
        return None, {"erro": "referência não é permutação completa dos blocos desta página"}
    dif_dim = max(abs(extraido["dimensions"][k] - p["dimensions"][k]) for k in ("width", "height"))
    if dif_dim > 0.11 or any(len(r["bbox"]) != 4 or original.area(r["bbox"]) <= 0 for r in rs):
        return None, {"erro": "dimensões ou caixas incompatíveis", "erro_dimensoes_pt": dif_dim}
    kws, livres, ambiguas = original.donos(ws, rs)
    por_r = {r["id"]: ks for r, ks in zip(rs, kws)}
    por_l, por_w_l, por_w_r, gold_lines, ordem_local = {}, {}, {}, [], {}
    auditoria = {"palavras": len(ws), "blocos": len(rs), "livres": len(livres), "ambiguas": ambiguas,
                 "vazios": [r["id"] for r, ks in zip(rs, kws) if not ks],
                 "erro_dimensoes_pt": dif_dim, "texto_divergente": [], "envelope_divergente": [],
                 "tokens_similaridade": [], "erro_envelope_max_pt": 0.0}
    for r, ks in zip(rs, kws):
        ls = linhas(ws, ks) if ks else []
        por_l[r["id"]] = []
        ordem_local[r["id"]] = [k for L in ls for k in L["ks"]]
        if ks:
            env = original.envelope([ws[k][1:5] for k in ks])
            err = max(abs(a - b) for a, b in zip(env, r["bbox"]))
            auditoria["erro_envelope_max_pt"] = max(err, auditoria["erro_envelope_max_pt"])
            if err > 0.15:
                auditoria["envelope_divergente"].append(r["id"])
            atual = limpar(" ".join(ws[k][0] for k in ordem_local[r["id"]]))
            a, b = collections.Counter(atual.split()), collections.Counter(r.get("text", "").split())
            simil = sum((a & b).values()) / max(1, sum((a | b).values()))
            auditoria["tokens_similaridade"].append(simil)
            if a != b:
                auditoria["texto_divergente"].append(r["id"])
        for i, L in enumerate(ls):
            lid = f"{r['id']}:l{i}"
            por_l[r["id"]].append(lid)
            gold_lines.append({"id": lid, "regiao": r["id"], "ks": L["ks"], "bbox": L["bbox"]})
            for k in L["ks"]:
                por_w_l[k], por_w_r[k] = lid, r["id"]
    auditoria["tokens_similaridade_media"] = statistics.mean(auditoria["tokens_similaridade"]) if auditoria["tokens_similaridade"] else None
    # Excluir apenas pagina incompatível, sem reposicionar palavras ou corrigir pelo ouro.
    if ws and kws and (len(auditoria["envelope_divergente"]) > len(rs) / 2
                       and (auditoria["tokens_similaridade_media"] or 0) < 0.5):
        auditoria["erro"] = "caixas e palavras não batem: auditoria geométrica/textual falhou"
        return None, auditoria
    h = statistics.median(w[4] - w[2] for w in ws) if ws else None
    prep = {**q, "ws": ws, "h": h, "d": {"detector": {"regioes": det or []}},
            "gt_r": [rid for rid in q["gt"] if por_r[rid]],
            "gt_w": [k for rid in q["gt"] for k in ordem_local[rid]],
            "gt_l": [lid for rid in q["gt"] for lid in por_l[rid]],
            "reg_words": por_r, "ordem_local": ordem_local, "por_w_r": por_w_r, "por_w_l": por_w_l,
            "gold_lines": gold_lines, "auditoria": auditoria}
    return prep, auditoria


def colunas(q):
    """Mesmo detector de vales, sem caixas-ouro ou atomos que escondam tabelas."""
    if not q["ws"]:
        return {"n": 0, "cortes": []}
    H = q["p"]["dimensions"]["height"]
    ks = [k for k, w in enumerate(q["ws"]) if 0.10 * H <= original.centro(w)[1] <= 0.95 * H
          and not RE_MARCACAO.match(w[0])]
    items = original.linhas_partidas(q["ws"], ks, FIXA.gap, q["h"])
    ids = list(range(len(items)))
    cortes = original.vales_locais(items, ids, q["h"], FIXA.vale)
    if not cortes:
        cortes = original.vales(items, ids, q["h"], FIXA.vale)
    return {"n": len(cortes) + 1, "cortes": cortes}


def baseline(q, metodo):
    p, rs = q["p"], q["p"]["bounding_boxes"]
    B, entrada = caixas(p), ordem_entrada(p)
    ini, fim, marcas, corpo = [], [], [], []
    H = p["dimensions"]["height"]
    for i in entrada:
        b = rs[i]["bbox"]
        ks = q["reg_words"][rs[i]["id"]]
        cy = (b[1] + b[3]) / 2
        if metodo != "xycut_margens":
            corpo.append(i)
        elif ks and all(RE_MARCACAO.match(q["ws"][k][0]) for k in ks):
            marcas.append(i)
        elif cy < REGRAS["topo_centro"] * H and b[3] < REGRAS["topo_base"] * H:
            ini.append(i)
        elif cy > REGRAS["rodape_centro"] * H:
            fim.append(i)
        else:
            corpo.append(i)
    key = lambda i: (B[i]["top"], B[i]["x0"], i)
    meio = sorted(corpo, key=lambda i: (B[i]["top"], B[i]["x0"])) if metodo == "ingenua" else xycut(corpo, B)
    ordem = sorted(ini, key=key) + meio + sorted(marcas, key=key) + sorted(fim, key=key)
    pr = [rs[i]["id"] for i in ordem if q["reg_words"][rs[i]["id"]]]
    seq = [k for rid in pr for k in q["ordem_local"][rid]]
    return seq, pr


def metricas(pred, gt):
    if len(gt) < 2:
        return {"tau": None, "sucessor": None, "ard": None}
    if len(pred) != len(gt) or set(pred) != set(gt) or len(set(pred)) != len(pred):
        raise ValueError("ordem inválida na avaliação; não reparar usando a referência")
    return {"tau": kendall_tau(pred, gt), "sucessor": acerto_sucessor(pred, gt), "ard": ard_normalizado(pred, gt)}


def trechos(seq, donos, ignorar_livres=True):
    nomes = [donos[k] if k in donos else None for k in seq if k in donos or not ignorar_livres]
    return [v for i, v in enumerate(nomes) if i == 0 or v != nomes[i - 1]]


def continuidade(seq, donos, gt):
    runs = trechos(seq, donos)
    conta = collections.Counter(runs)
    n = len(gt)
    prox = {a: b for a, b in zip(gt, gt[1:])}
    succ = sum(prox.get(a) == b for a, b in zip(runs, runs[1:])) / (len(runs) - 1) if len(runs) > 1 else None
    return {"fragmentacao": sum(v > 1 for v in conta.values()) / n if n else None,
            "n_fragmentadas": sum(v > 1 for v in conta.values()), "sucessor_trechos": succ,
            "trechos": len(runs)}


def avaliar(q, seq, pr=None, diag=None):
    real = [k for k in seq if k in q["por_w_r"]]
    rank = {k: i for i, k in enumerate(seq)}
    if pr is None:
        rr = {rid: statistics.median(rank[k] for k in ks) for rid, ks in q["reg_words"].items() if ks}
        rb = {r["id"]: r["bbox"] for r in q["p"]["bounding_boxes"]}
        pr = sorted(rr, key=lambda rid: (rr[rid], rb[rid][1], rb[rid][0], rid))
    cont = continuidade(seq, q["por_w_r"], q["gt_r"])
    linhas_cont = continuidade(seq, q["por_w_l"], q["gt_l"])
    strict = collections.Counter(trechos(seq, q["por_w_r"], ignorar_livres=False))
    cont["fragmentacao_estrita"] = sum(strict[r] > 1 for r in q["gt_r"]) / len(q["gt_r"]) if q["gt_r"] else None
    return {"palavras": metricas(real, q["gt_w"]), "regioes": metricas(pr, q["gt_r"]),
            "continuidade": cont, "linhas_reais": linhas_cont, "diag": diag or {},
            "seq": seq, "ordem_regioes": pr}


def avaliar_pagina(q, extraido, det, origem_layout):
    prep, aud = preparar(q, extraido, det)
    p = q["p"]
    r = {"page_id": p["page_id"], "uf": p["uf"], "arquivo": p["arquivo"], "pagina": p["pagina"],
         "fonte": q["fonte"], "grupo": p.get("grupo", "silver"), "repetida": q["repetida"],
         "veiculo_visto": q["veiculo_visto"], "origem": p.get("origem", "protocolo"),
         "nota_humana": q["nota_humana"], "auditoria": aud, "origem_layout": origem_layout,
         "layout_falhou": det is None, "metodos": {}}
    if prep is None:
        r["status"] = "excluida_auditoria"
        return r
    if len(prep["gt_w"]) < 2 or not prep["ws"]:
        r["status"] = "sem_palavras_avaliaveis"
        return r
    r["status"] = "ok"
    r["colunas"] = colunas(prep)
    for m in ("xycut", "xycut_margens", "ingenua"):
        seq, pr = baseline(prep, m)
        r["metodos"][m] = avaliar(prep, seq, pr)
    for m, c in (("fixo", FIXA), ("sem_margens", SEM_MARGENS)):
        seq, items, diag = original.prever(prep, c)
        r["metodos"][m] = avaliar(prep, seq, diag=diag)
        if m == "fixo":
            r["items"] = items
    return r


def resumo_valores(valores, veiculos, seed):
    pares = [(v, uf) for v, uf in zip(valores, veiculos) if v is not None and math.isfinite(v)]
    if not pares:
        return {"media": None, "ic": None, "ic_paginas": None, "n": 0, "g": 0}
    por_uf = collections.defaultdict(list)
    for v, uf in pares:
        por_uf[uf].append(v)
    grupos = [por_uf[uf] for uf in sorted(por_uf)]
    g, n = len(grupos), len(pares)
    soma = np.array([sum(v) for v in grupos])
    cont = np.array([len(v) for v in grupos])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, g, size=(REGRAS["bootstrap"], g))
    boot = soma[idx].sum(axis=1) / cont[idx].sum(axis=1)
    vals = np.array([v for v, _ in pares])
    idx_p = rng.integers(0, n, size=(REGRAS["bootstrap"], n))
    bp = vals[idx_p].mean(axis=1)
    return {"media": float(vals.mean()), "ic": [float(x) for x in np.quantile(boot, [0.025, 0.975])],
            "ic_paginas": [float(x) for x in np.quantile(bp, [0.025, 0.975])], "n": n, "g": g}


def metrica_de(r, m, regua, metrica):
    return r["metodos"][m][regua][metrica]


def pratt(dif):
    # Quantizacao evita zeros numericos artificiais na comparacao de ordens identicas.
    d = np.round(np.array(dif, dtype=float), 12)
    if not len(d):
        return {"W": None, "p": None, "n": 0}
    if not np.any(d):
        return {"W": 0.0, "p": 1.0, "n": len(d)}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w, p = wilcoxon(d, zero_method="pratt", alternative="two-sided", method="auto")
    return {"W": float(w), "p": float(p), "n": len(d)}


def resumir(paginas, inferencia=True):
    rs = [r for r in paginas if r["status"] == "ok"]
    out = {"n_total": len(paginas), "n": len(rs), "veiculos": len({r["uf"] for r in rs}), "metodos": {}, "testes": []}
    ufs = [r["uf"] for r in rs]
    for m in METODOS:
        out["metodos"][m] = {}
        for regua, metrics in (("palavras", ("tau", "sucessor", "ard")), ("regioes", ("tau", "sucessor", "ard")),
                               ("continuidade", ("fragmentacao", "fragmentacao_estrita", "sucessor_trechos")),
                               ("linhas_reais", ("sucessor_trechos",))):
            out["metodos"][m][regua] = {
                met: resumo_valores([metrica_de(r, m, regua, met) for r in rs], ufs, REGRAS["semente"])
                for met in metrics}
    if inferencia:
        for regua in ("palavras", "regioes"):
            for ref in ("xycut", "xycut_margens"):
                for met in ("tau", "sucessor", "ard"):
                    pares = [(metrica_de(r, "fixo", regua, met) - metrica_de(r, ref, regua, met), r["uf"])
                             for r in rs if metrica_de(r, "fixo", regua, met) is not None and metrica_de(r, ref, regua, met) is not None]
                    d, uf = [a for a, _ in pares], [b for _, b in pares]
                    agr = collections.defaultdict(list)
                    for a, b in pares:
                        agr[b].append(a)
                    s = resumo_valores(d, uf, REGRAS["semente"])
                    orientado = np.array(d) * (-1 if met == "ard" else 1)
                    s.update(regua=regua, referencia=ref, metrica=met, pagina=pratt(d),
                             veiculo=pratt([statistics.mean(v) for _, v in sorted(agr.items())]),
                             ganha=int(sum(orientado > 1e-12)), empata=int(sum(abs(orientado) <= 1e-12)), perde=int(sum(orientado < -1e-12)))
                    out["testes"].append(s)
        # Familia exploratoria explicitamente definida: duas reguas x tres metricas x duas baselines.
        validos = sorted([t for t in out["testes"] if t["pagina"]["p"] is not None], key=lambda t: t["pagina"]["p"])
        anterior = 0.0
        for i, t in enumerate(validos):
            anterior = max(anterior, min(1.0, (len(validos) - i) * t["pagina"]["p"]))
            t["p_holm"] = anterior
    return out


def selecionar(paginas, nome):
    fonte = nome[0]
    rs = [r for r in paginas if r["fonte"] == fonte]
    if nome.endswith("novas"):
        return [r for r in rs if not r["repetida"]]
    if nome.endswith("repetidas"):
        return [r for r in rs if r["repetida"]]
    return rs


def construir_estado(paginas, hashes, amostra, concluido, autotestes):
    conjuntos = {nome: resumir(selecionar(paginas, nome), inferencia=concluido) for nome in CONJUNTOS}
    estratos = {}
    if concluido:
        for nome in ("A_novas", "A_repetidas", "B_novas", "B_todas"):
            rs = selecionar(paginas, nome)
            grupos = {}
            for r in rs:
                if r["status"] != "ok":
                    continue
                labels = ["colunas/" + ("1 coluna detectada" if r["colunas"]["n"] == 1 else "multicoluna detectada"),
                          "veiculo/" + r["uf"], "familiaridade/" + ("veículo já visto no v4" if r["veiculo_visto"] else "veículo ausente do v4")]
                if r["fonte"] == "A":
                    labels.append("grupo/" + r["grupo"])
                for label in labels:
                    grupos.setdefault(label, []).append(r)
            estratos[nome] = {k: resumir(v, inferencia=False) for k, v in sorted(grupos.items())}
    novas = [r for r in paginas if not r["repetida"] and r["status"] == "ok"]
    # Mesma pagina A/B entra uma vez: a humana tem prioridade na analise de erro.
    unica = {}
    for r in sorted(novas, key=lambda r: (r["fonte"], r["page_id"])):
        unica.setdefault(r["page_id"], r)
    piores = sorted(unica.values(), key=lambda r: (r["metodos"]["fixo"]["palavras"]["tau"] - r["metodos"]["xycut"]["palavras"]["tau"], r["page_id"]))[:8]
    ids_a = {q["p"]["page_id"] for q in amostra if q["fonte"] == "A"}
    ids_b = {q["p"]["page_id"] for q in amostra if q["fonte"] == "B"}
    associacao_sens = {}
    if concluido:
        for nome in ("A_novas", "B_novas"):
            rs = selecionar(paginas, nome)
            excluidas = [r["page_id"] for r in rs if r["auditoria"].get("envelope_divergente")]
            associacao_sens[nome] = {"paginas_retiradas": excluidas,
                                    "resumo": resumir([r for r in rs if r["page_id"] not in excluidas], inferencia=False)}
    return {"versao": VERSAO, "concluido": concluido, "hashes": hashes, "config": FIXA.id,
            "sensibilidade": SEM_MARGENS.id, "regras": REGRAS, "autotestes": autotestes,
            "esperadas": {n: len(selecionar([{"fonte": q["fonte"], "repetida": q["repetida"]} for q in amostra], n)) for n in CONJUNTOS},
            "intersecao_A_B": sorted(ids_a & ids_b), "paginas": paginas, "conjuntos": conjuntos,
            "estratos": estratos, "sensibilidade_associacao": associacao_sens,
            "inspecao": INSPECAO, "sintese_erros": SINTESE_ERROS,
            "piores": [{"fonte": r["fonte"], "page_id": r["page_id"]} for r in piores]}


def fmt(x, pct=False, nd=3):
    if x is None:
        return "—"
    return (f"{100 * x:.1f}%" if pct else f"{x:.{nd}f}").replace(".", ",")


def ic(s, pct=False, nd=3):
    if s["media"] is None:
        return "—"
    a, b = s["ic"]
    return f"{fmt(s['media'], pct, nd)} [{fmt(a, pct, nd)}; {fmt(b, pct, nd)}]"


def tabela_principal(s, regua):
    out = ["| Conjunto | n / veículos | Método | τ (IC 95% por veículo) ↑ | Sucessor (IC 95%) ↑ | ARD norm. (IC 95%) ↓ |", "|---|---:|---|---:|---:|---:|"]
    for nome, label in CONJUNTOS.items():
        res = s["conjuntos"][nome]
        if not res["n"]:
            continue
        for m, ml in METODOS.items():
            r = res["metodos"][m][regua]
            out.append(f"| {label} | {res['n']} / {res['veiculos']} | {ml} | {ic(r['tau'])} | {ic(r['sucessor'], True)} | {ic(r['ard'])} |")
    return out


def diagnostico_inicial(r):
    """Somente indicadores geometricos; a inspecao humana do agente fica separada."""
    diag = r["metodos"]["fixo"]["diag"]
    return (f"{r['colunas']['n']} colunas detectadas; {diag.get('max_colunas')} no decodificador; "
            f"{diag.get('pontes')} pontes; {diag.get('n_atomos')} átomos; "
            f"topo/fim/marcas={diag.get('margem_topo')}/{diag.get('margem_fim')}/{diag.get('marcas')}")


def renderizar(s):
    c = s["conjuntos"]
    def media(nome, m, regua="palavras", met="tau"):
        return c[nome]["metodos"][m][regua][met]["media"]
    estado = "concluído" if s["concluido"] else "PARCIAL — execução em andamento, não interpretar como resultado final"
    l = ["# Validação no acervo: ordem de leitura sem bounding box fina", "", f"Estado: **{estado}**.", ""]
    if c["A_novas"]["n"]:
        delta_a = media("A_novas", "fixo") - media("A_novas", "xycut_margens")
        delta_b = media("B_novas", "fixo") - media("B_novas", "xycut_margens") if c["B_novas"]["n"] else None
        veredito = "O ganho geral do golden_v4 não se confirma contra a XY-cut com a mesma política nas páginas humanas novas." if delta_a <= 0 else "O ganho médio de τ se confirma em páginas humanas novas, sobretudo multicoluna detectada; não se confirma superioridade geral, pois a continuidade piora e o teste pareado é inconclusivo."
        l += ["## Resumo em cinco linhas", "",
              f"1. **Veredito:** {veredito}",
              f"2. Nas {c['A_novas']['n']} humanas novas: τ de palavras {fmt(media('A_novas', 'fixo'))}, XY-cut pura {fmt(media('A_novas', 'xycut'))}, XY-cut com margens {fmt(media('A_novas', 'xycut_margens'))}; Δ justo {fmt(delta_a)}.",
              f"3. Nas {c['B_novas']['n']} silver novas: τ de palavras {fmt(media('B_novas', 'fixo'))}, XY-cut pura {fmt(media('B_novas', 'xycut'))}, com margens {fmt(media('B_novas', 'xycut_margens'))}; Δ justo {fmt(delta_b)}; a seleção silver favorece XY-cut.",
              f"4. Fragmentação do método: {fmt(media('A_novas', 'fixo', 'continuidade', 'fragmentacao'), True)} das regiões por página em A nova e {fmt(media('B_novas', 'fixo', 'continuidade', 'fragmentacao'), True)} em B nova; a mediana de regiões não mede a sequência real.",
              "5. Recomendação: manter o método como experimento congelado e reportar condições/estratos; não substituir o pipeline nem alegar generalização para veículos inéditos com esta amostra.", ""]
    l += ["## Amostra e ausência de ajuste", "",
          f"Configuração principal **`{s['config']}`**, escolhida anteriormente no golden_v4. Sensibilidade **`{s['sensibilidade']}`**: muda apenas a política de margens. Não há grade, seleção, treino ou ajuste nestes dados.", "",
          "| Conjunto | Páginas previstas | Avaliadas | Veículos avaliados |", "|---|---:|---:|---:|"]
    for nome, label in CONJUNTOS.items():
        l.append(f"| {label} | {s['esperadas'][nome]} | {c[nome]['n']} | {c[nome]['veiculos']} |")
    l += ["", "Repetição = igualdade literal de `page_id` contra **todas** as tarefas do golden_v4, incluindo a página pulada. Novidade aqui é de página, não necessariamente de veículo/template. A humana usa `referencia.jsonl` concluída e os blocos v3; a silver usa `carregar_particao('teste')` e `referencia()` do protocolo, sem trocar segmentação.", "",
          f"A e B compartilham **{len(s['intersecao_A_B'])} páginas**; não agregamos as amostras. As referências A e B podem divergir nessas páginas. B completo e B novo também não são evidências independentes.", "",
          "**Silver enviesado em favor da XY-cut:** seus veículos foram escolhidos porque o fluxo de conteúdo do PDF concordava com a heurística. Essa referência não substitui leitura humana e não autoriza declarar todo desacordo erro do método.", "",
          "A ordem humana do Golden foi anotada de forma cega, sem sugestão automática de ordenação. A geometria/segmentação dos blocos já é automática; parte da referência foi projetada de uma segmentação anterior apenas em páginas sem conflito. Portanto a independência da ordem não torna a segmentação um ouro de palavras/células.", "",
          "## Auditoria de extração e coordenadas", "",
          "Palavras são extraídas de `data/raw/<uf>/<arquivo>` na página de índice zero, com `pdfplumber` e `palavras_da_pagina()` (fluxo, deduplicação e junção de letras do extrator). O preditor recebe apenas texto/geometria e detecções table/picture: não usa fluxo como ordem, ordem humana ou caixas finas. O sistema é `[x0, top, x1, bottom]` em pontos.", "",
          "A associação é por centro, menor caixa e preferência por não figura, como no script original. Comparamos dimensões, envelopes das palavras por caixa e multiconjunto de tokens após a limpeza do extrator. Diferenças de agrupamento de linhas/translineação não são automaticamente erro de coordenadas. Nenhuma caixa é escalada ou reposicionada para melhorar resultado.", "",
          "| Conjunto | Palavras extraídas | Sem bloco | Dono ambíguo | Blocos vazios | Páginas vazias | Excluídas por auditoria/extração | Maior erro de dimensões (pt) | Envelopes divergentes (>0,15 pt) | Tokens divergentes |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for nome in ("A_novas", "A_repetidas", "B_novas", "B_todas"):
        rs = selecionar(s["paginas"], nome)
        aa = [r["auditoria"] for r in rs]
        l.append(f"| {CONJUNTOS[nome]} | {sum(a.get('palavras', 0) for a in aa)} | {sum(a.get('livres', 0) for a in aa)} | {sum(a.get('ambiguas', 0) for a in aa)} | {sum(len(a.get('vazios', [])) for a in aa)} | {sum(a.get('palavras') == 0 for a in aa)} | {sum(r['status'] != 'ok' for r in rs)} | {fmt(max((a.get('erro_dimensoes_pt', 0) for a in aa), default=0), nd=5)} | {sum(len(a.get('envelope_divergente', [])) for a in aa)} | {sum(len(a.get('texto_divergente', [])) for a in aa)} |")
    ok = [r for r in s["paginas"] if r["status"] == "ok"]
    l += ["", f"Layout disponível no cache original: {sum(r['origem_layout'] == 'data/processed/layout' for r in ok)} registros A/B; cache novo: {sum(r['origem_layout'] != 'data/processed/layout' for r in ok)}; falhas de layout: {sum(r['layout_falhou'] for r in ok)}. Valores A/B incluem a interseção, portanto não são contagem de páginas únicas.", "",
          "Regiões vazias são contadas e excluídas **da projeção de todos os métodos**, sem mediana fictícia. Página sem duas palavras avaliáveis não ganha nota perfeita: é registrada sem medida. Erros de PDF/referência/coordenadas são registrados, não tratados por assert. Átomos table/picture sem palavras permanecem na saída do método, mas não têm ordem textual avaliável.", "",
          "## Réguas e comparação justa", "",
          "**Principal — sequência real de palavras:** índices distintos mesmo para palavras iguais. Referência = blocos na ordem humana (A) ou silver (B), expandidos por `linhas()` de cima para baixo e esquerda para direita dentro de cada bloco. Comparamos diretamente a permutação de palavras emitida pelo método; não projetamos palavras/linhas por mediana. Palavras sem bloco continuam na saída, mas não têm referência e saem das métricas. Médias macro por página.", "",
          "**Continuidade:** fração de blocos com palavras que aparecem em mais de um trecho da saída. A versão principal ignora palavras sem dono como no original; a estrita também conta essas palavras como interrupção. Sucessor de trechos de linha/bloco usa a sequência real comprimindo somente repetições consecutivas do mesmo dono, preservando suas reaparições; compara pares com vizinhos da referência e penaliza intercalação. Não há mediana nessa régua.", "",
          "**Secundária — regiões:** mediana dos postos das palavras de cada bloco, com desempate por geometria e ID; baselines usam sua ordem diretamente. Regiões sem palavras não entram. A mediana pode ocultar intercalação e estes números não decidem o veredito principal.", "",
          "Todas as baselines recebem as mesmas caixas e a permutação `ordem_entrada()`. São comparadores condicionais à segmentação v3 disponível, e não uma medição ponta a ponta do custo de obtê-la. Na XY-cut com margens, a precedência e os limiares são idênticos: marcas por `RE_MARCACAO` primeiro na classificação; topo se centro < 7% e base < 10%; rodapé se centro > 95%; saída topo, corpo por XY-cut, marcas, rodapé. Faixas especiais ordenadas por `(top, x0, índice)`. As caixas de referência ficam inteiras, enquanto o método classifica fragmentos de linha/átomos: igualdade de política, não de granularidade.", "",
          "## Tabela principal — saída real de palavras", ""]
    l += tabela_principal(s, "palavras")
    if s["concluido"]:
        t = next(t for t in c["A_novas"]["testes"] if t["regua"] == "palavras" and t["metrica"] == "tau" and t["referencia"] == "xycut_margens")
        rs = selecionar(s["paginas"], "A_novas")
        ds = [r["metodos"]["fixo"]["palavras"]["tau"] - r["metodos"]["xycut_margens"]["palavras"]["tau"] for r in rs if r["status"] == "ok"]
        l += ["", f"**Interpretação do ganho humano novo:** Δ justo {ic(t, nd=5)}; Pratt por página p={fmt(t['pagina']['p'], nd=6)}, por veículo p={fmt(t['veiculo']['p'], nd=6)}. Ganha/empata/perde em {t['ganha']}/{t['empata']}/{t['perde']} páginas, mediana de Δ={fmt(statistics.median(ds), nd=5)}. O IC da média pode ser positivo enquanto o teste de postos pareados é inconclusivo: medem aspectos distintos da distribuição. Algumas melhoras grandes sustentam a média; não há vitória uniforme.", ""]
        l += ["### Sensibilidade à associação geométrica (diagnóstico posterior)", "",
              "O RJ Municipalidades `#p0` tem letras estilizadas em caixas que se sobrepõem: a preferência pela menor caixa transfere uma letra entre blocos e muda seus envelopes; dimensões da página conferem. As outras divergências de tokens são translineação/pontuação produzidas por agrupadores de linhas diferentes. Conservamos o critério original e todos esses casos nas tabelas principais. A retirada da página com envelopes divergentes abaixo é somente diagnóstico posterior, sem reajuste do método nem do filtro principal.", "",
              "| Conjunto | Páginas retiradas | n restante | τ palavras método | τ palavras XY-cut+margens | Δ |", "|---|---|---:|---:|---:|---:|"]
        for nome, ss in s["sensibilidade_associacao"].items():
            e = ss["resumo"]
            f, j = [e["metodos"][m]["palavras"]["tau"]["media"] for m in ("fixo", "xycut_margens")]
            l.append(f"| {CONJUNTOS[nome]} | {', '.join('`'+pid+'`' for pid in ss['paginas_retiradas']) or 'nenhuma'} | {e['n']} | {fmt(f)} | {fmt(j)} | {fmt(f-j, nd=5)} |")
    l += ["", "## Continuidade real", "", "| Conjunto | Método | Blocos fragmentados (IC 95%) | Fragmentação estrita | Sucessor trechos de bloco | Sucessor trechos de linha |", "|---|---|---:|---:|---:|---:|"]
    for nome in ("A_novas", "A_repetidas", "B_novas", "B_todas"):
        for m, ml in METODOS.items():
            r = c[nome]["metodos"][m]
            l.append(f"| {CONJUNTOS[nome]} | {ml} | {ic(r['continuidade']['fragmentacao'], True)} | {fmt(r['continuidade']['fragmentacao_estrita']['media'], True)} | {fmt(r['continuidade']['sucessor_trechos']['media'], True)} | {fmt(r['linhas_reais']['sucessor_trechos']['media'], True)} |")
    l += ["", "Sucessor de palavras é dominado por pares internos a blocos longos e pode permanecer alto mesmo quando dois blocos inteiros se invertem; ler junto com τ e as duas medidas de continuidade. Baselines de blocos são contíguas por construção e emitem somente palavras associadas aos blocos; a fragmentação estrita delas não avalia posicionamento de palavras sem dono. No método, essas palavras permanecem na sequência real, e a versão estrita é um diagnóstico adicional de sua cobertura.", "", "## Régua secundária — blocos por mediana", ""]
    l += tabela_principal(s, "regioes")
    if s["concluido"]:
        l += ["", "## Inferência pareada contra XY-cut", "",
              f"IC percentil 95%: {REGRAS['bootstrap']} reamostras, semente {REGRAS['semente']}. Reamostragem principal sorteia **veículos inteiros** com reposição e mantém todas suas páginas; estima a mesma média por página com denominador variável. Não refaz seleção porque a configuração está congelada. IC por páginas, solicitado inicialmente, aparece apenas como sensibilidade da diferença: ignora dependência do veículo.", "",
              "Wilcoxon bilateral pareado com `zero_method='pratt'`, `method='auto'`, diferenças quantizadas em doze casas para evitar falsos não zeros. Mostramos p por página e por médias de veículo. O primeiro não corrige a correlação intraveículo; o segundo tem pouquíssimos grupos em B. p Holm por conjunto abrange as duas réguas, três métricas e duas baselines; não corrige a história de desenvolvimento nem os estratos exploratórios. IC com um veículo degenera e não mede generalização; B tem apenas três veículos.", "",
              "| Conjunto | Régua | Comparador | Métrica | Δ método − comparador (IC veículo) | IC páginas | G/E/P | p Pratt página | p Holm | p Pratt veículo |", "|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
        for nome in ("A_novas", "A_repetidas", "B_novas", "B_todas"):
            for t in c[nome]["testes"]:
                ip = t["ic_paginas"]
                l.append(f"| {CONJUNTOS[nome]} | {t['regua']} | {METODOS[t['referencia']]} | {t['metrica']} | {ic(t, nd=5)} | [{fmt(ip[0], nd=5)}; {fmt(ip[1], nd=5)}] | {t['ganha']}/{t['empata']}/{t['perde']} | {fmt(t['pagina']['p'], nd=6)} | {fmt(t.get('p_holm'), nd=6)} | {fmt(t['veiculo']['p'], nd=6)} |")
        l += ["", "ARD negativo significa melhora. Ausência de significância não prova equivalência ou não inferioridade.", "", "## Estratos — colunas, veículo, grupo e familiaridade", "",
              "Critério fixo de colunas: palavras com centro entre 10% e 95% da altura, retirando marcas; `linhas_partidas(gap=1.2)`, `vales_locais(vale=0.08)` e fallback para `vales`. Cortes aceitos + um, até quatro colunas. Reutiliza o detector de calhas do método, aplicado às palavras antes dos átomos para não esconder calhas entre tabelas. Não lê `stats.n_colunas` nem ordem/caixas humanas. Uma coluna detectada não prova uma coluna visual; células podem criar falso corte. O máximo de colunas no decodificador também fica persistido para diagnóstico.", "",
              "Cada célula de τ abaixo traz média [IC 95% agrupado por veículo]. Estratos por veículo com um só grupo têm IC degenerado; as médias servem para descrever casos, não para inferir novos templates. Não há ajuste por estrato.", ""]
        for nome, estratos in s["estratos"].items():
            l += [f"### {CONJUNTOS[nome]}", "", "| Estrato | n / veículos | τ palavras fixo | τ XY-cut | τ XY-cut+margens | Δ justo palavras | τ regiões fixo / XY-cut+margens | Sucessor palavras fixo / justa | Fragmentação fixo |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for label, e in estratos.items():
                ms = e["metodos"]
                f, x, j = [ms[m]["palavras"] for m in ("fixo", "xycut", "xycut_margens")]
                l.append(f"| {label} | {e['n']} / {e['veiculos']} | {ic(f['tau'])} | {ic(x['tau'])} | {ic(j['tau'])} | {fmt(f['tau']['media'] - j['tau']['media'])} | {fmt(ms['fixo']['regioes']['tau']['media'])} / {fmt(ms['xycut_margens']['regioes']['tau']['media'])} | {fmt(f['sucessor']['media'], True)} / {fmt(j['sucessor']['media'], True)} | {fmt(ms['fixo']['continuidade']['fragmentacao']['media'], True)} |")
        l += ["", "## Análise das oito maiores perdas em páginas novas", "",
              "Ranking por Δ τ **da sequência real de palavras** contra XY-cut pura. Considera A/B novas; uma página compartilhada aparece uma vez, priorizando a referência humana. Abaixo há também Δ contra a XY-cut justa e τ de regiões para expor desacordo entre réguas. Motivos são diagnósticos de geometria/inspeção, não rótulos causais anotados; não houve mudança de configuração após inspeção.", "",
              "| Página / fonte | τ palavras XY-cut → método | Δ pura / justa | τ regiões XY-cut → método | Fragmentação | Motivo e relação com golden_v4 |", "|---|---:|---:|---:|---:|---|"]
        for ident in s["piores"]:
            r = next(r for r in s["paginas"] if r["fonte"] == ident["fonte"] and r["page_id"] == ident["page_id"])
            ms = r["metodos"]
            f, x, j = [ms[m]["palavras"]["tau"] for m in ("fixo", "xycut", "xycut_margens")]
            nota = s.get("inspecao", {}).get(r["page_id"], diagnostico_inicial(r) + "; inspeção causal ainda não concluída")
            l.append(f"| `{r['page_id']}` ({r['fonte']}) | {fmt(x, nd=5)} → {fmt(f, nd=5)} | {fmt(f-x, nd=5)} / {fmt(f-j, nd=5)} | {fmt(ms['xycut']['regioes']['tau'])} → {fmt(ms['fixo']['regioes']['tau'])} | {fmt(ms['fixo']['continuidade']['fragmentacao'], True)} | {nota} |")
        if s.get("sintese_erros"):
            l += ["", s["sintese_erros"]]
    l += ["", "## Limitações e recomendação para o TCC", "",
          "Amostra humana pequena e de conveniência, um anotador, poucos exemplos por veículo e possível parentesco tipográfico. Páginas novas do mesmo veículo não equivalem a teste de domínio novo. A referência silver é selecionada por concordância com XY-cut. A interseção A/B e a repetição de B no golden_v4 impedem tratar o total como uma validação independente única.", "",
          "A ordem humana cega evita ancoragem numa sugestão de **ordem**. Corrigir uma pré-anotação de **caixas/segmentação**, como no Diamond/v4, traz viés de ancoragem geométrica; isso continua pertinente ao resultado de desenvolvimento, mas não deve ser atribuído sem prova à ordem cega usada aqui. Em A, a segmentação v3 define a unidade que o humano ordenou. Projeção sem conflito conserva a ordem anotada, mas pode mudar o peso/unidade dos itens.", "",
          "A expansão dentro de cada bloco é algorítmica, não ouro humano de palavras ou células. Blocos v3 que misturam colunas podem impor uma referência interna intercalada: melhora/piora de palavras nesses blocos não decide a leitura humana correta. A régua de regiões também herda esse defeito de segmentação. Tabelas são achatadas por y/x; não avaliamos estrutura semântica de células, OCR ou imagens sem texto. Palavras fora dos blocos e regiões vazias não têm referência textual avaliável.", "",
          "As baselines preservam blocos inteiros e compartilham a expansão interna da referência, o que favorece seus pares internos; o método precisa reconstruir essa granularidade sem vê-la. τ de palavras pondera pares de palavras (peso maior para blocos longos dentro da página), enquanto τ de regiões pondera pares de blocos. Fragmentação e sucessores de trechos tornam essa diferença visível. Os números das duas réguas não são intercambiáveis.", "",
          "Não demonstramos superioridade geral, equivalência ou vantagem ponta a ponta de latência. Recomenda-se apresentar a configuração congelada como diagnóstico de generalização por página, com comparação de margens iguais, estratos e falhas; não adotar no protocolo sem decisão do autor. Para sustentar substituição, obter ordem humana em páginas/veículos realmente inéditos e uma referência de leitura interna dos blocos problemáticos, mantendo a saída real e continuidade como critérios.", "",
          "## Reprodução, retomada e integridade", "", "```powershell",
          "venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_acervo.py --do-zero",
          "venv/Scripts/python.exe -B orquestracao/analises/ordem_sem_bbox_validacao_acervo.py --conferir", "```", "",
          "Caches: `resultados/ordem_sem_bbox_cache/palavras/` (PDF/hash/página), `avaliacao_acervo/` (métricas e sequências por referência/hash), `validacao_acervo.json` (todos os números, hashes, testes e estratos), `inspecao_acervo/` (figuras intermediárias de erro). A execução padrão retoma hashes compatíveis; `--do-zero` reabre PDFs e recalcula tudo. O relatório é escrito após o primeiro lote com números e atualizado durante a execução. Não há leitura do Label Studio, rede, GPU, edição de dados, commit ou alteração do método anterior.", "",
          f"Controles sintéticos executados: {len(s['autotestes'])}; resultados: " + "; ".join(s["autotestes"]) + ".", "",
          "`--conferir` compara o Markdown inteiro com sua renderização a partir do JSON e verifica todos os hashes de entrada/fontes/PDFs. A execução normal confere hashes antes/depois. Os hashes completos e as ordens previstas estão no JSON do cache; figuras de erro têm caixas v3 azuis, átomos Docling vermelhos e calhas verdes."]
    if s.get("verificacao_do_zero"):
        l += ["", "**Conferência final:** a execução do zero reproduziu as métricas, sequências, estratos e testes da execução anterior; relatório conferido por igualdade integral com a renderização do JSON."]
    return "\n".join(l) + "\n"


def escrever_relatorio(s):
    texto = renderizar(s)
    tmp = RELATORIO.with_suffix(".md.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    os.replace(tmp, RELATORIO)


def inspecionar(s):
    """Gera figuras de diagnostico das maiores perdas, so sob o cache de resultados."""
    import pymupdf
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    a = list(ler_jsonl(RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl"))
    ps = {("A", p["page_id"]): p for p in a}
    ps.update({("B", p["page_id"]): p for p in carregar_particao("teste")})
    diretorio = CACHE / "inspecao_acervo"
    diretorio.mkdir(parents=True, exist_ok=True)
    for i, ident in enumerate(s["piores"], 1):
        r = next(r for r in s["paginas"] if r["fonte"] == ident["fonte"] and r["page_id"] == ident["page_id"])
        p = ps[(r["fonte"], r["page_id"])]
        e = carregar(CACHE / "palavras" / (chave(r["page_id"]) + ".json"))
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        with pymupdf.open(RAIZ / "data/raw" / p["uf"] / p["arquivo"]) as pdf:
            pix = pdf[int(p["pagina"])].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            im = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        fig, axes = plt.subplots(1, 2, figsize=(14, 10))
        for ax in axes:
            ax.imshow(im, extent=[0, W, H, 0])
            ax.set_xlim(0, W)
            ax.set_ylim(H, 0)
            ax.axis("off")
        for b in p["bounding_boxes"]:
            x0, y0, x1, y1 = b["bbox"]
            axes[0].add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, edgecolor="royalblue", linewidth=0.8))
            axes[0].text(x0, y0, b["id"], color="blue", fontsize=6, backgroundcolor="white")
        for j, item in enumerate(r["items"]):
            x0, y0, x1, y1 = item["bbox"]
            if item["tipo"] != "texto":
                axes[1].add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, edgecolor="red", linewidth=1.1))
                axes[1].text(x0, y0, f"{j}:{item['tipo']}", color="red", fontsize=7, backgroundcolor="white")
        for x in r["colunas"]["cortes"]:
            axes[1].axvline(x, color="limegreen", linewidth=0.8)
        axes[0].set_title("Blocos v3 usados na referência")
        axes[1].set_title("Átomos Docling e calhas detectadas")
        fig.suptitle(f"{i}. {r['page_id']}\n{diagnostico_inicial(r)}", fontsize=9)
        fig.tight_layout(rect=(0, 0, 1, 0.90))
        destino = diretorio / f"{i:02d}_{chave(r['page_id'])}.png"
        fig.savefig(destino, dpi=140)
        plt.close(fig)
        print(destino.relative_to(RAIZ).as_posix(), flush=True)


def autoteste():
    """Casos de borda e contraprova da mediana sem usar assert."""
    def exigir(cond, mensagem):
        if not cond:
            raise ValueError("Autoteste falhou: " + mensagem)
    p = {"page_id": "sintetica", "dimensions": {"width": 100, "height": 100},
         "bounding_boxes": [{"id": "a", "bbox": [0, 0, 40, 40], "text": "a"},
                            {"id": "b", "bbox": [50, 0, 90, 40], "text": "b"}]}
    q = {"p": p, "gt": ["a", "b"]}
    e = {"palavras": [], "dimensions": p["dimensions"]}
    prep, aud = preparar(q, e, [])
    exigir(prep is not None and len(aud["vazios"]) == 2, "página vazia")
    exigir(metricas([], [])["tau"] is None, "vazia não recebe nota perfeita")
    e["palavras"] = [["a", 1, 1, 3, 3]]
    prep, aud = preparar(q, e, [])
    exigir(aud["vazios"] == ["b"] and prep["gt_r"] == ["a"], "região sem palavras")
    seq = [0, 2, 1, 3]
    owners = {0: "a", 1: "a", 2: "b", 3: "b"}
    exigir(continuidade(seq, owners, ["a", "b"])["fragmentacao"] == 1, "intercalação fragmenta ambos")
    exigir(kendall_tau(["a", "b"], ["a", "b"]) == 1 and kendall_tau(seq, [0, 1, 2, 3]) < 1, "mediana perfeita esconde erro")
    exigir(pratt([0, 0, 0])["p"] == 1, "Pratt só zeros")
    a = resumo_valores([0, 0, 1], ["x", "x", "y"], 7)
    exigir(abs(a["media"] - 1 / 3) < 1e-12 and a["g"] == 2, "bootstrap preserva peso por página")
    return ["página vazia tratada", "vazia sem nota perfeita", "região vazia tratada",
            "intercalação contada", "mediana perfeita com palavras erradas", "Pratt zeros", "bootstrap por veículo"]


def imprimir(s):
    print("\nTABELA PRINCIPAL: sequência real de palavras", flush=True)
    for nome in ("A_novas", "A_repetidas", "B_novas", "B_todas"):
        e = s["conjuntos"][nome]
        print(f"{CONJUNTOS[nome]} | n={e['n']}, veículos={e['veiculos']}")
        for m, label in METODOS.items():
            r = e["metodos"][m]
            print(f"  {label}: tau={fmt(r['palavras']['tau']['media'])}; sucessor={fmt(r['palavras']['sucessor']['media'], True)}; ARDn={fmt(r['palavras']['ard']['media'])}; fragmentação={fmt(r['continuidade']['fragmentacao']['media'], True)}")
    print(f"[OK] {RELATORIO.relative_to(RAIZ).as_posix()}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--inspecionar", action="store_true", help="figuras intermediárias das oito perdas, a partir do resultado final")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    tests = autoteste()
    if args.autoteste:
        print("[OK] " + "; ".join(tests))
        return
    if args.inspecionar:
        s = carregar(ESTADO)
        if not s or not s.get("concluido"):
            raise ValueError("Resultado final ausente")
        inspecionar(s)
        return
    if args.conferir:
        s = carregar(ESTADO)
        if not s or not s.get("concluido"):
            raise ValueError("Resultado final ausente")
        for path, h in s["hashes"].items():
            if sha(RAIZ / path) != h:
                raise ValueError("Hash mudou: " + path)
        if RELATORIO.read_text(encoding="utf-8") != renderizar(s):
            raise ValueError("Relatório diverge dos números persistidos")
        imprimir(s)
        print(f"[OK] Relatório idêntico à renderização; {len(s['hashes'])} hashes conferidos.")
        return
    amostra, hashes = fontes_e_amostra()
    unico = {q["p"]["page_id"]: q["p"] for q in amostra}
    print(f"[*] {len(amostra)} referências A/B; {len(unico)} páginas únicas; CPU; configuração {FIXA.id}", flush=True)
    dets, fontes_layout = obter_layout(list(unico.values()))
    grupos = {}
    for p in unico.values():
        path = RAIZ / "data/raw" / p["uf"] / p["arquivo"]
        grupos.setdefault(path, []).append(p)
    tarefas = [(str(path), ps, hashes[path.relative_to(RAIZ).as_posix()], hashes["src/data/extrator.py"], args.do_zero)
               for path, ps in sorted(grupos.items())]
    avaliadas = []
    anterior = carregar(ESTADO)
    fontes_hash = {k: v for k, v in hashes.items() if not k.startswith("data/raw/")}
    def processar_lote(regs):
        for extraido in regs:
            pid = extraido["page_id"]
            for q in [q for q in amostra if q["p"]["page_id"] == pid]:
                fingerprint = digest([VERSAO, fontes_hash, q, extraido["fingerprint"], dets.get(pid), FIXA.id, SEM_MARGENS.id])
                cp = CACHE / "avaliacao_acervo" / (q["fonte"] + "_" + chave(pid) + ".json")
                salvo = carregar(cp) if not args.do_zero else None
                if salvo and salvo.get("fingerprint") == fingerprint:
                    r = salvo["resultado"]
                else:
                    r = avaliar_pagina(q, extraido, dets.get(pid), fontes_layout.get(pid, "ausente"))
                    gravar(cp, {"fingerprint": fingerprint, "resultado": r})
                avaliadas.append(r)
        avaliadas.sort(key=lambda r: (r["fonte"], r["page_id"]))
        parcial = construir_estado(avaliadas, hashes, amostra, False, tests)
        gravar(ESTADO, parcial)
        escrever_relatorio(parcial)
        print(f"    {len(avaliadas)}/{len(amostra)} referências medidas e persistidas", flush=True)
    # Threads nao dependem dos pipes de multiprocessing bloqueados no sandbox Windows.
    # Cada worker abre seu proprio PDF; o limite baixo preserva CPU para os outros jobs.
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 2))) as pool:
        futuros = [pool.submit(extrair_pdf, t) for t in tarefas]
        for futuro in concurrent.futures.as_completed(futuros):
            processar_lote(futuro.result())
    s = construir_estado(avaliadas, hashes, amostra, True, tests)
    if anterior and anterior.get("concluido") and anterior.get("hashes") == hashes:
        for k in ("inspecao", "sintese_erros"):
            if k in anterior:
                s[k] = anterior[k]
        if args.do_zero:
            comparar = ("paginas", "conjuntos", "estratos", "piores", "sensibilidade_associacao")
            if any(anterior[k] != s[k] for k in comparar):
                raise ValueError("Execução do zero divergiu da execução anterior")
            s["verificacao_do_zero"] = True
        elif anterior.get("verificacao_do_zero"):
            s["verificacao_do_zero"] = True
    for path, h in hashes.items():
        if sha(RAIZ / path) != h:
            raise ValueError("Entrada/fonte mudou durante a execução: " + path)
    gravar(ESTADO, s)
    escrever_relatorio(s)
    imprimir(s)


if __name__ == "__main__":
    main()
