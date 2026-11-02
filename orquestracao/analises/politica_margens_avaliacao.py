"""Mede margens na regua oficial de blocos, sem alterar o protocolo do TCC.

Usa teste silver e os Golden v3/v4, preditos ja existentes do sucessor e
ordens das baselines oficiais. Mede pos-processamento e, separadamente, XY-cut
recalculada no corpo. Nao abre PDFs, exports LS, modelos, rede ou GPU.

Unica saida: resultados/politica_margens.md. Checkpoints comprimidos no
proprio Markdown guardam ordens, metricas por pagina, hashes e testes, evitando
arquivos extras. Acrescenta um checkpoint apos cada pagina, sem apagar o
anterior. Retoma o ultimo completo, ignorando escrita truncada. No fim compacta
o arquivo, sincronizando antes de truncar. A retomada exige hashes identicos.
--do-zero ignora o checkpoint; --conferir valida hashes, metricas e a igualdade
integral do relatorio com a renderizacao do checkpoint.

Uso na raiz: venv/Scripts/python.exe -B
    orquestracao/analises/politica_margens_avaliacao.py --do-zero --testes
Testes novos e suite existente sao subprocessos unittest em CPU, com bytecode
desativado. A suite existente usa fixtures/mocks e diretorios temporarios.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import base64
import collections
import hashlib
import itertools
import json
import os
import random
import re
import subprocess
import zlib

import numpy as np
from scipy.stats import wilcoxon

from src.data.extrator import xycut
from src.eval.baselines import caixas
from src.eval.metrics import avaliar
from src.eval.politica_margens import aplicar_margens, xycut_margens, _separar, PADRAO_MARCACAO
from src.eval.protocolo import (RAIZ_PROJETO, DIR_RESULTADOS, carregar_splits,
                                iterar_paginas, ordem_entrada, referencia)

RAIZ = Path(RAIZ_PROJETO)
SAIDA = Path(DIR_RESULTADOS) / "politica_margens.md"
MARCADOR = "POLITICA_MARGENS_CHECKPOINT_V1"
METRICAS = ("kendall_tau", "acerto_sucessor", "ard_norm")
ROTULOS_METRICA = {"kendall_tau": "τ", "acerto_sucessor": "Sucessor", "ard_norm": "ARD norm."}
PADROES = dict(limiar_topo=0.07, limite_base_topo=0.10, limiar_rodape=0.95)
TOPOS = (0.05, 0.07, 0.09)
RODAPES = (0.93, 0.95, 0.97)
NOMES = {"xycut": "XY-cut", "naive": "Ingênua", "layoutlm_sucessor": "LayoutLM sucessor",
         "xycut_recalculada": "XY-cut recalculada (controle)",
         "xycut_margens": "XY-cut + margens (recorte do corpo)",
         "xycut_margens_classe": "XY-cut + margens por classe (recorte)†"}
CONJUNTOS = ("teste", "golden_v3", "golden_v4")
FONTES = [Path(__file__), RAIZ / "src/eval/politica_margens.py",
          RAIZ / "src/eval/metrics.py", RAIZ / "src/eval/baselines.py",
          RAIZ / "src/eval/protocolo.py", RAIZ / "src/data/extrator.py"]


def ler_jsonl(path):
    """Le linha a linha e falha com contexto; nao descarta dados truncados."""
    with path.open(encoding="utf-8") as f:
        for n, linha in enumerate(f, 1):
            if linha.strip():
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"JSON invalido: {path}:{n}") from exc


def unicos(regs, campo="page_id"):
    saida = {}
    for r in regs:
        if r[campo] in saida:
            raise ValueError(f"Identificador repetido: {r[campo]}")
        saida[r[campo]] = r
    return saida


def carregar():
    splits = carregar_splits()
    dir_blocos = RAIZ / "data/processed/blocos"
    entradas = [RAIZ / "data/processed/splits.json"]
    entradas += [dir_blocos / f"{uf}.jsonl" for uf in splits["teste"]]
    # Le explicitamente a segmentacao oficial, sem depender de TCC_DIR_BLOCOS.
    teste = unicos(iterar_paginas(splits["teste"], str(dir_blocos)))
    conjuntos = {"teste": {pid: (p, referencia(p, splits)) for pid, p in teste.items()}}
    auditoria = {}
    lotes = {"golden_v3": "_avaliacao/golden_v3", "golden_v4": "golden_v4"}
    todos_v4 = set()
    for nome, lote in lotes.items():
        pasta = RAIZ / "data/golden" / lote
        arq_t = pasta / "tarefas.jsonl"
        arq_a = pasta / ("referencia.jsonl" if nome == "golden_v3" else "anotacoes.jsonl")
        entradas.extend((arq_t, arq_a))
        tarefas = unicos(ler_jsonl(arq_t))
        anns = list(ler_jsonl(arq_a))
        concluidas = [a for a in anns if a.get("status") == "concluida"]
        counts = collections.Counter(a.get("anotador") for a in concluidas)
        principal = counts.most_common(1)[0][0]
        humano = unicos(a for a in concluidas if a.get("anotador") == principal)
        conjuntos[nome] = {pid: (tarefas[pid], a["ordem"]) for pid, a in humano.items()}
        auditoria[nome] = {"anotador": principal, "tarefas": len(tarefas),
                           "registros": len(anns), "concluidas": len(humano),
                           "ignoradas": len(anns) - len(humano)}
        if nome == "golden_v4":
            todos_v4 = set(tarefas)
    predicoes = {}
    for nome, paginas in conjuntos.items():
        pasta = Path(DIR_RESULTADOS) if nome == "teste" else Path(DIR_RESULTADOS) / "golden" / lotes[nome]
        predicoes[nome] = {}
        for metodo in ("xycut", "naive", "layoutlm_sucessor"):
            arq = pasta / f"pred_{metodo}.jsonl"
            if arq.exists():
                entradas.append(arq)
                regs = unicos(ler_jsonl(arq))
                predicoes[nome][metodo] = {pid: r["ordem_pred"] for pid, r in regs.items() if pid in paginas}
            elif metodo != "layoutlm_sucessor":
                predicoes[nome][metodo] = {pid: p["ordens"][metodo] for pid, (p, _) in paginas.items()}
        if len(paginas) != {"teste": 89, "golden_v3": 47, "golden_v4": 44}[nome]:
            raise ValueError(f"Contagem oficial mudou: {nome} tem {len(paginas)} paginas")
        for pid, (p, gt) in paginas.items():
            aplicar_margens(p["bounding_boxes"], gt, p["dimensions"])
            for metodo, preds in predicoes[nome].items():
                if pid in preds:
                    # Valida identidade exata: nenhuma intersecao, reparo ou projecao.
                    aplicar_margens(p["bounding_boxes"], preds[pid], p["dimensions"])
        auditoria.setdefault(nome, {})
        auditoria[nome].update(
            paginas=len(paginas), veiculos=len({pid.split("/")[0] for pid in paginas}),
            repetidas_v4=len(set(paginas) & todos_v4),
            novas_v4=len(set(paginas) - todos_v4),
            classes=dict(collections.Counter(b.get("classe", "ausente") for p, _ in paginas.values()
                                             for b in p["bounding_boxes"])),
            cobertura={m: len(v) for m, v in predicoes[nome].items()})
    # A primeira auditoria e atualizada apos conhecer o v4 completo, inclusive a pulada.
    for nome, paginas in conjuntos.items():
        auditoria[nome]["repetidas_v4"] = len(set(paginas) & todos_v4)
        auditoria[nome]["novas_v4"] = len(set(paginas) - todos_v4)
    auditoria["intersecao_teste_v3"] = len(set(conjuntos["teste"]) & set(conjuntos["golden_v3"]))
    auditoria["tarefas_v4"] = sorted(todos_v4)
    fontes = FONTES + sorted((RAIZ / "tests").glob("test_*.py"))
    return conjuntos, predicoes, auditoria, sorted(set(entradas + fontes))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for dados in iter(lambda: f.read(1024 * 1024), b""):
            h.update(dados)
    return h.hexdigest()


def hashes(paths):
    return {p.relative_to(RAIZ).as_posix(): digest(p) for p in paths}


def classificar(p, variante):
    bs = p["bounding_boxes"]
    return _separar(bs, [b["id"] for b in bs], p["dimensions"], variante=variante,
                    **PADROES, padrao_marcacao=PADRAO_MARCACAO, campo_classe="classe",
                    classe_cabecalho="cabecalho", classe_rodape="rodape")


def medir_pagina(nome, pid, p, gt, predicoes):
    ordens = {}
    for metodo, preds in predicoes.items():
        if pid not in preds:
            continue
        ordem = preds[pid]
        ordens[metodo] = ordem
        for variante in ("geometria", "classe"):
            ordens[f"{metodo}_{variante}"] = aplicar_margens(p["bounding_boxes"], ordem, p["dimensions"],
                                                          variante=variante, **PADROES)
    ids = [b["id"] for b in p["bounding_boxes"]]
    ordens["xycut_recalculada"] = [ids[i] for i in xycut(ordem_entrada(p), caixas(p))]
    ordens["xycut_margens"] = xycut_margens(p, **PADROES)
    ordens["xycut_margens_classe"] = xycut_margens(p, variante="classe", **PADROES)
    grade = []
    for topo, rodape in itertools.product(TOPOS, RODAPES):
        params = dict(limiar_topo=topo, limite_base_topo=PADROES["limite_base_topo"], limiar_rodape=rodape)
        d = {"topo": topo, "rodape": rodape, "metodos": {}}
        for metodo, preds in predicoes.items():
            if pid in preds:
                pred = aplicar_margens(p["bounding_boxes"], preds[pid], p["dimensions"], **params)
                d["metodos"][metodo] = {"ordem": pred, "metricas": avaliar(pred, gt)}
        pred = xycut_margens(p, **params)
        d["metodos"]["xycut_margens"] = {"ordem": pred, "metricas": avaliar(pred, gt)}
        grade.append(d)
    return {"page_id": pid, "conjunto": nome, "gt": gt, "n_blocos": len(ids),
            "ordens": ordens, "metricas": {m: avaliar(pr, gt) for m, pr in ordens.items()},
            "grupos": {v: classificar(p, v) for v in ("geometria", "classe")}, "grade": grade}


def ic(v, indices):
    medias = np.sort(np.asarray(v)[indices].mean(axis=1))
    n = len(medias)
    return [float(medias[int(0.025 * n)]), float(medias[int(0.975 * n)])]


def pratt(delta):
    d = np.round(delta, 12)
    if not np.any(d):
        return 1.0
    return float(wilcoxon(d, zero_method="pratt", alternative="two-sided", method="approx").pvalue)


def resumir(rows, nboot, seed):
    resumo = {}
    nomes = list(dict.fromkeys(m for r in rows for m in r["metricas"]))
    for metodo in nomes:
        rs = [r for r in rows if metodo in r["metricas"]]
        rng = random.Random(seed)
        idx = np.array([rng.choices(range(len(rs)), k=len(rs)) for _ in range(nboot)])
        resumo[metodo] = {"n": len(rs)}
        for metrica in METRICAS:
            v = [r["metricas"][metodo][metrica] for r in rs]
            resumo[metodo][metrica] = {"media": float(np.mean(v)), "ic95": ic(v, idx)}
        if metodo in ("xycut_margens", "xycut_margens_classe"):
            base = "xycut_recalculada"
        elif metodo.endswith(("_geometria", "_classe")):
            base = metodo.rsplit("_", 1)[0]
        else:
            continue
        resumo[metodo]["contra"] = base
        resumo[metodo]["diferenca"] = {}
        for metrica in METRICAS:
            d = np.array([r["metricas"][metodo][metrica] - r["metricas"][base][metrica] for r in rs])
            resumo[metodo]["diferenca"][metrica] = {
                "media": float(d.mean()), "ic95": ic(d, idx), "p_pratt": pratt(d),
                "melhora": int(np.sum(d < -1e-12) if metrica == "ard_norm" else np.sum(d > 1e-12)),
                "empata": int(np.sum(np.abs(d) <= 1e-12)),
                "piora": int(np.sum(d > 1e-12) if metrica == "ard_norm" else np.sum(d < -1e-12))}
    # Holm por conjunto, abrangendo metodos, variantes e as tres metricas.
    testes = [d for r in resumo.values() for d in r.get("diferenca", {}).values()]
    maior = 0.0
    for i, d in enumerate(sorted(testes, key=lambda d: d["p_pratt"])):
        maior = max(maior, min(1.0, (len(testes) - i) * d["p_pratt"]))
        d["p_holm"] = maior
    return resumo


def evidencia(p, r, metodo):
    """Identifica pares novos discordantes, sem inventar causa semantica."""
    base = "xycut_recalculada" if metodo.startswith("xycut_margens") else metodo.rsplit("_", 1)[0]
    variante = "classe" if metodo.endswith("classe") else "geometria"
    antes = {bid: i for i, bid in enumerate(r["ordens"][base])}
    depois = {bid: i for i, bid in enumerate(r["ordens"][metodo])}
    grupos = {bid: g for g, bids in r["grupos"][variante].items() for bid in bids}
    novos = [(a, b) for a, b in itertools.combinations(r["gt"], 2)
             if antes[a] < antes[b] and depois[a] > depois[b]]
    corrigidos = sum(antes[a] > antes[b] and depois[a] < depois[b]
                    for a, b in itertools.combinations(r["gt"], 2))
    counts = collections.Counter(bid for par in novos for bid in par if grupos[bid] != "corpo")
    if not counts:
        counts = collections.Counter(bid for par in novos for bid in par)
    bs = {b["id"]: b for b in p["bounding_boxes"]}
    descricoes = []
    for bid, n in counts.most_common(2):
        b = bs[bid]
        bbox = b["bbox"]
        altura = p["dimensions"]["height"]
        texto = " ".join((b.get("text") or "").split())[:100]
        classe = b.get("classe") or b.get("tipo") or "sem classe"
        if grupos[bid] == "topo" and classe == "titulo":
            motivo = "título tratado como cabeçalho"
        elif grupos[bid] == "rodape" and classe == "tabela":
            motivo = "caixa de tabela tratada como rodapé (não prova nota de rodapé)"
        else:
            motivo = {"topo": "ordenação/deslocamento de campo do topo", "rodape": "campo inferior levado ao fim",
                      "marcas": "marca levada antes do rodapé", "corpo": "recorte mudou ordem do corpo"}[grupos[bid]]
        descricoes.append(f"{motivo}: `{bid}` ({classe}), centro={fnum((bbox[1]+bbox[3])/2/altura,4)}, "
                          f"base={fnum(bbox[3]/altura,4)}, {n} pares; «{texto}»")
    return f"{len(novos)} pares novos discordantes, {corrigidos} corrigidos. " + "; ".join(descricoes)


def agregar(R, conjuntos):
    resumo, quedas, sensibilidade, fora_v4 = {}, {}, {}, {}
    for nome in CONJUNTOS:
        rows = [r for r in R["paginas"] if r["conjunto"] == nome]
        if not rows:
            continue
        resumo[nome] = resumir(rows, R["nboot"], R["semente"])
        novas = [r for r in rows if r["page_id"] not in set(R["auditoria"]["tarefas_v4"])]
        if novas:
            fora_v4[nome] = resumir(novas, R["nboot"], R["semente"])
        quedas[nome] = {}
        for m, s in resumo[nome].items():
            if "contra" not in s:
                continue
            base = s["contra"]
            candidatas = sorted((r for r in rows if m in r["metricas"]
                                 and r["metricas"][m]["kendall_tau"] < r["metricas"][base]["kendall_tau"] - 1e-12),
                                key=lambda r: (r["metricas"][m]["kendall_tau"] - r["metricas"][base]["kendall_tau"], r["page_id"]))
            quedas[nome][m] = [{"page_id": r["page_id"], "sem": r["metricas"][base]["kendall_tau"],
                                "com": r["metricas"][m]["kendall_tau"],
                                "causa": evidencia(conjuntos[nome][r["page_id"]][0], r, m)} for r in candidatas[:5]]
        sensibilidade[nome] = []
        for i, (topo, rodape) in enumerate(itertools.product(TOPOS, RODAPES)):
            d = {"topo": topo, "rodape": rodape, "metodos": {}}
            for m in rows[0]["grade"][i]["metodos"]:
                rs = [r for r in rows if m in r["grade"][i]["metodos"]]
                base = "xycut_recalculada" if m == "xycut_margens" else m
                d["metodos"][m] = {"n": len(rs)}
                for metrica in METRICAS:
                    v = [r["grade"][i]["metodos"][m]["metricas"][metrica] for r in rs]
                    delta = [a-r["metricas"][base][metrica] for a,r in zip(v,rs)]
                    d["metodos"][m][metrica] = float(np.mean(v))
                    d["metodos"][m][f"delta_{metrica}"] = float(np.mean(delta))
            sensibilidade[nome].append(d)
    R.update(resumo=resumo, quedas=quedas, sensibilidade=sensibilidade, resumo_fora_v4=fora_v4)


def fnum(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",")


def nome_metodo(m):
    if m in NOMES:
        return NOMES[m]
    base, variante = m.rsplit("_", 1)
    return NOMES[base] + (" + margens geométricas (pós)" if variante == "geometria" else " + margens por classe (pós)†")


def cel(s, metrica, casas=3):
    q = s[metrica]
    escala = 100 if metrica == "acerto_sucessor" else 1
    casas = 1 if escala == 100 else casas
    sufixo = "%" if escala == 100 else ""
    return f"{fnum(q['media']*escala,casas)}{sufixo} [{fnum(q['ic95'][0]*escala,casas)}; {fnum(q['ic95'][1]*escala,casas)}]"


def ptexto(p):
    """Nao transforma p pequeno em zero por arredondamento."""
    return f"{p:.2e}".replace(".", ",") if 0 < p < 0.000001 else fnum(p,6)


def renderizar(R):
    out = ["# Política de margens na régua oficial de blocos", "",
           f"Estado: **{'concluído' if R.get('completo') else 'parcial, retomável'}**.", "", "## Resumo em cinco linhas", ""]
    S = R.get("resumo", {})
    if all(n in S for n in CONJUNTOS):
        out += ["1. **Veredito: vale registrar XY-cut + margens geométricas, com recorte do corpo, como método adicional; a adoção depende do autor e não implica substituir a XY-cut.**"]
        for i, nome in enumerate(CONJUNTOS, 2):
            b, q, pos = S[nome]["xycut_recalculada"], S[nome]["xycut_margens"], S[nome]["xycut_geometria"]
            out += [f"{i}. {nome} ({q['n']} páginas): τ XY-cut {fnum(b['kendall_tau']['media'])} → recorte {fnum(q['kendall_tau']['media'])}; "
                    f"pós-processamento isolado {fnum(pos['kendall_tau']['media'])}; recorte piora τ em {q['diferenca']['kendall_tau']['piora']} páginas."]
        out += ["5. Golden_v4 foi usado no desenvolvimento; classes humanas são oráculo. Não aplicar margens indiscriminadamente aos outros ordenadores nem chamar os conjuntos completos de teste limpo."]
    else:
        out += [f"Páginas já medidas: {len(R['paginas'])}. As tabelas abaixo são parciais."]
    out += ["", "## Protocolo e operações distintas", "",
            "Médias macro por página; `src/eval/metrics.py:avaliar`, sem texto/BLEU, na régua de **blocos** de cada conjunto. "
            "Não há projeção por mediana nem régua de palavras. XY-cut e ingênua usam `pred_*.jsonl` existentes quando disponíveis; "
            "nos Golden, usam `tarefas.jsonl:ordens` quando não há arquivo. LayoutLM sucessor usa somente `pred_layoutlm_sucessor.jsonl`, "
            "sem escolher sementes/checkpoints pelo desempenho. Predições ausentes ficam ausentes, com cobertura explícita. Todos os IDs "
            "devem formar a permutação completa da segmentação correta, antes de qualquer métrica.", "",
            f"IC percentil de 95% com {R['nboot']} bootstrap de páginas, semente {R['semente']}, e os mesmos índices para com/sem/diferença. "
            "Segue a regra de índices do `comparar.py`, sem executá-lo. Wilcoxon pareado bilateral, `zero_method='pratt'`, "
            "aproximação normal; diferenças arredondadas a doze casas apenas no teste. Todos os empates dão p=1. "
            "Holm corrige conjuntamente variantes/métodos/métricas dentro de cada conjunto. ARD menor significa melhora. "
            "O IC por página solicitado não corrige dependência entre edições do mesmo veículo; os p podem ser otimistas.", "",
            f"Padrões congelados: centro do topo < {fnum(PADROES['limiar_topo']*100,1)}% da altura **e** base < "
            f"{fnum(PADROES['limite_base_topo']*100,1)}%; centro do rodapé > {fnum(PADROES['limiar_rodape']*100,1)}%. "
            "Precedência: marcas puras, topo, rodapé, corpo. Saída: topo, corpo, marcas, rodapé; margens/marcas ordenadas por "
            "(top, x0, índice original do bloco), sem tolerância de alinhamento. Marca pura: todos os tokens do texto casam com "
            f"`{PADRAO_MARCACAO}`. Texto misto não é marca. A variante classe troca somente topo/rodapé por `classe=cabecalho/rodape`, "
            "sem fallback geométrico.", "",
            "**Pós** = `aplicar_margens`: move/sorta margens e conserva a ordem relativa de todos os blocos do corpo. "
            "**Recorte** = `xycut_margens`: remove margens, recalcula XY-cut só no corpo e concatena os grupos. "
            "Esta segunda operação reproduz o desenho da reanálise. O controle XY-cut recalculada usa as mesmas caixas arredondadas "
            "e a entrada embaralhada fixa do protocolo que o recorte; a ordem armazenada pode diferir por arredondamento/desempate.", "",
            "## Tabela principal: candidato com recorte geométrico", "",
            "| Conjunto | n | τ XY-cut → +margens | Sucessor → +margens | ARD norm. → +margens | Δτ [IC 95%] | p Pratt / Holm |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for nome in CONJUNTOS:
        if nome not in S:
            continue
        b,q = S[nome]["xycut_recalculada"], S[nome]["xycut_margens"]
        d = q["diferenca"]["kendall_tau"]
        out += [f"| {nome} | {q['n']} | {fnum(b['kendall_tau']['media'])} → {fnum(q['kendall_tau']['media'])} | "
                f"{fnum(100*b['acerto_sucessor']['media'],1)}% → {fnum(100*q['acerto_sucessor']['media'],1)}% | "
                f"{fnum(b['ard_norm']['media'])} → {fnum(q['ard_norm']['media'])} | {cel(q['diferenca'],'kendall_tau')} | "
                f"{ptexto(d['p_pratt'])} / {ptexto(d['p_holm'])} |"]
    for nome in CONJUNTOS:
        if nome not in S:
            continue
        out += ["", f"## {nome}: todas as ordens e variantes", "",
                "| Método | n | τ [IC 95%] ↑ | Sucessor [IC 95%] ↑ | ARD norm. [IC 95%] ↓ |",
                "|---|---:|---:|---:|---:|"]
        for m,s in S[nome].items():
            out += [f"| {nome_metodo(m)} | {s['n']} | {cel(s,'kendall_tau')} | {cel(s,'acerto_sucessor')} | {cel(s,'ard_norm')} |"]
        rows = [r for r in R["paginas"] if r["conjunto"] == nome]
        diferentes = sum(r["ordens"]["xycut"] != r["ordens"]["xycut_recalculada"] for r in rows)
        out += ["", f"Controle recalculado difere da XY-cut oficial armazenada em {diferentes}/{len(rows)} páginas. "
                "As comparações do recorte usam o controle; as de pós-processamento usam a ordem armazenada.", "",
                "| Comparação com/sem | Métrica | Δ [IC 95%] | Melhora/empata/piora | p Pratt | p Holm |",
                "|---|---|---:|---:|---:|---:|"]
        for m,s in S[nome].items():
            for metrica,d in s.get("diferenca", {}).items():
                out += [f"| {nome_metodo(m)} × {nome_metodo(s['contra'])} | {ROTULOS_METRICA[metrica]} | "
                        f"{cel(s['diferenca'],metrica)} | {d['melhora']}/{d['empata']}/{d['piora']} | "
                        f"{ptexto(d['p_pratt'])} | {ptexto(d['p_holm'])} |"]
        out += ["", "### Cinco maiores quedas por comparação", "",
                "Ranking por Δτ; mostra até cinco quedas de **cada** método/variante para não esconder regressões do sucessor. "
                "Causas são diagnósticos verificáveis de texto, classe, geometria e pares novos discordantes; "
                "não são rótulos causais humanos nem inspeção visual de PDFs. Diferenças de ordem dentro do próprio cabeçalho "
                "também contam na régua oficial. Não se inferem notas de tabela sem evidência.", ""]
        for m, qs in R["quedas"][nome].items():
            out += [f"**{nome_metodo(m)}:**", ""]
            if not qs:
                out += ["Nenhuma queda de τ.", ""]
                continue
            out += ["| Página | τ sem → com | Δτ | Causa / evidência |", "|---|---:|---:|---|"]
            for q in qs:
                causa = q["causa"].replace("|", "\\|").replace("\n", " ")
                out += [f"| `{q['page_id']}` | {fnum(q['sem'],5)} → {fnum(q['com'],5)} | "
                        f"{fnum(q['com']-q['sem'],5)} | {causa} |"]
            out += [""]
    out += ["## Sensibilidade, sem ajuste", "",
            "Grade fixada antes da medição: topo 0,05/0,07/0,09 × rodapé 0,93/0,95/0,97; base do topo permanece 0,10. "
            "Não escolhemos o melhor ponto nem mudamos padrões. A variante por classe é insensível a esses limiares por construção. "
            "A grade está no checkpoint para todos os ordenadores e três métricas; a tabela traz τ e o recorte completo.", "",
            "| Conjunto | Topo | Rodapé | τ XY-cut pós | τ Ingênua pós | τ Sucessor pós | τ recorte | Sucessor recorte | ARD recorte |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for nome, grade in R.get("sensibilidade", {}).items():
        for g in grade:
            ms = g["metodos"]
            valores = [fnum(ms[m]["kendall_tau"]) if m in ms else "—"
                       for m in ("xycut", "naive", "layoutlm_sucessor", "xycut_margens")]
            q = ms["xycut_margens"]
            out += [f"| {nome} | {fnum(g['topo'],2)} | {fnum(g['rodape'],2)} | " + " | ".join(valores)
                    + f" | {fnum(100*q['acerto_sucessor'],1)}% | {fnum(q['ard_norm'])} |"]
        deltas = [g["metodos"]["xycut_margens"]["delta_kendall_tau"] for g in grade]
        media = S[nome]["xycut_margens"]["kendall_tau"]["media"]
        variacao = max(abs(g["metodos"]["xycut_margens"]["kendall_tau"]-media) for g in grade)
        out += ["", f"{nome}: Δτ do recorte varia de {fnum(min(deltas),5)} a {fnum(max(deltas),5)}; "
                f"maior afastamento do padrão = {fnum(variacao,5)}. "
                + ("O sinal do ganho é robusto nesta grade." if min(deltas) > 0 else "O sinal do ganho não é robusto nesta grade.")
                + " Isso não prova robustez fora destes layouts.", ""]
    if all(n in S for n in CONJUNTOS):
        out += ["**Interpretação para adoção:** conservar os padrões, sem selecionar um ponto pela grade. "
                "A estabilidade do ganho no teste é local ao limiar de topo original: apertá-lo pode deixar fora campos "
                "que quebram as colunas. O ganho médio não garante ausência de regressões em páginas. "
                "O pós-processamento isolado deve continuar opcional e identificado separadamente do recorte; "
                "no v4 ele não reproduz o ganho da reanálise.", "",
                f"No golden_v4, p Pratt do recorte geométrico = {ptexto(S['golden_v4']['xycut_margens']['diferenca']['kendall_tau']['p_pratt'])} "
                f"e p Holm = {ptexto(S['golden_v4']['xycut_margens']['diferenca']['kendall_tau']['p_holm'])}; "
                "o resultado de desenvolvimento não sustenta uma alegação geral de superioridade após todas as comparações.", ""]
    A = R["auditoria"]
    out += ["## Viés, independência e limitações", "",
            "Os limiares foram escolhidos olhando o golden_v4: ele é desenvolvimento, não teste da política. "
            "As regiões do Diamond/v4 foram anotadas corrigindo pré-anotações, com **viés de ancoragem geométrica**. "
            "A ordem humana foi anotada de forma cega; isso não elimina a ancoragem das caixas/classes. Classes humanas "
            "cabecalho/rodape são informação de oráculo (†), não um ganho de detector demonstrado. V3 e teste não têm essas "
            "classes; nessas linhas, a variante classe aplica somente a regra textual de marcas.", "",
            "| Conjunto | Páginas | Veículos | Repetidas no lote v4 | Fora do lote v4 | Classes dos blocos |",
            "|---|---:|---:|---:|---:|---|"]
    for nome in CONJUNTOS:
        a = A[nome]
        out += [f"| {nome} | {a['paginas']} | {a['veiculos']} | {a['repetidas_v4']} | {a['novas_v4']} | `{a['classes']}` |"]
    out += ["", "Diagnóstico adicional das páginas fora do lote v4 (não altera a partição oficial nem os padrões):", "",
            "| Conjunto fora do v4 | n | τ controle → recorte | Sucessor → recorte | ARD norm. → recorte | Δτ [IC 95%] |",
            "|---|---:|---:|---:|---:|---:|"]
    for nome, s in R.get("resumo_fora_v4", {}).items():
        b, q = s["xycut_recalculada"], s["xycut_margens"]
        out += [f"| {nome} | {q['n']} | {fnum(b['kendall_tau']['media'])} → {fnum(q['kendall_tau']['media'])} | "
                f"{fnum(100*b['acerto_sucessor']['media'],1)}% → {fnum(100*q['acerto_sucessor']['media'],1)}% | "
                f"{fnum(b['ard_norm']['media'])} → {fnum(q['ard_norm']['media'])} | {cel(q['diferenca'],'kendall_tau')} |"]
    out += ["", f"Teste e golden_v3 compartilham {A['intersecao_teste_v3']} páginas e não são réplicas independentes. "
            "Contamos repetição contra todas as tarefas v4, inclusive a pulada. O golden_v3 completo contém páginas do v4 e "
            "não é teste limpo; o mesmo vale para o teste silver completo. **Apenas as páginas fora do v4 são validação sem "
            "uso no ajuste original dos limiares**. Ainda assim seus resultados já foram vistos na validação anterior citada "
            "pelo autor: esta rodada não é um novo teste cego. Não houve retuning aqui. Veículos/templates já vistos, amostra "
            "pequena e de conveniência e um anotador limitam extrapolação. Para teste prospectivo limpo, congelar este módulo "
            "e anotar páginas/veículos inéditos sem sugestão de geometria/ordem.", "",
            "A referência silver vem de veículos selecionados pela concordância fluxo-PDF/XY-cut; pode favorecer XY-cut e "
            "discordar da leitura humana. V3 e v4 têm segmentações diferentes, portanto suas médias não são comparação "
            "pareada entre segmentadores. O τ pondera pares de blocos dentro de cada página; páginas com poucos blocos "
            "são especialmente sensíveis à troca de dois campos. Não avaliamos estrutura interna de tabelas, OCR, imagens "
            "sem texto, detector de classes, latência ponta a ponta ou nova inferência do LayoutLM. Não mexemos nas predições.", "",
            "## Integração proposta (diff ilustrativo; não aplicado)", "",
            "Registrar como método **adicional**, geométrico e com recorte. Este trecho deve passar pela decisão metodológica "
            "do autor antes de integrar o protocolo. Ele mostra os pontos existentes, não inventa um registro de funções que "
            "o `baselines.py` atual não possui.", "", "```diff",
            "--- a/src/eval/baselines.py", "+++ b/src/eval/baselines.py",
            "@@", "+from src.eval.politica_margens import xycut_margens",
            "@@", '-    saidas = {"aleatoria": [], "naive": [], "xycut": []}',
            '+    saidas = {"aleatoria": [], "naive": [], "xycut": [], "xycut_margens": []}',
            "@@", "+        t0 = time.perf_counter()",
            "+        pred = xycut_margens(p)",
            '+        saidas["xycut_margens"].append({"page_id": p["page_id"],',
            '+            "ordem_pred": pred, "tempo_ms": (time.perf_counter() - t0) * 1000})',
            "--- a/src/eval/comparar.py", "+++ b/src/eval/comparar.py", "@@",
            '+    "xycut_margens": "XY-cut + margens (geométricas; recorte)",  # em NOMES',
            "--- a/src/eval/figuras.py", "+++ b/src/eval/figuras.py", "@@",
            '+    "xycut_margens": "XY-cut + margens",  # em ROTULO',
            '+    "xycut_margens": "#eb6834",  # em COR, mesma família da XY-cut', "```", "",
            "## Testes, reprodução e integridade", ""]
    if not R.get("testes"):
        out += ["Testes ainda não registrados; executar com `--testes`.", ""]
    for t in R.get("testes", []):
        out += [f"`{t['comando']}`: código {t['codigo']}, {t['n']} testes, "
                f"{'OK' if t['codigo']==0 else 'FALHOU'}. Saída integral guardada no checkpoint.", ""]
    out += ["```powershell", "venv/Scripts/python.exe -B orquestracao/analises/politica_margens_avaliacao.py --do-zero --testes",
            "venv/Scripts/python.exe -B orquestracao/analises/politica_margens_avaliacao.py --conferir", "```", "",
            "O checkpoint no comentário HTML abaixo contém hashes de entradas/fontes, ordens com/sem, "
            "métricas por página, grade completa e saídas dos testes. Não há cache em data/ nem arquivos novos de predição/comparação. "
            "Durante a execução, checkpoints são acrescentados sem apagar o anterior; a retomada ignora o último se estiver truncado. "
            "Ao concluir, o relatório é compactado no mesmo arquivo, com sincronização antes de truncar o diário. "
            "A execução padrão retoma somente hashes idênticos; `--do-zero` recalcula todas as páginas.", ""]
    if R.get("reproduziu"):
        out += ["**Execução final do zero:** reproduziu exatamente ordens, métricas, quedas, grade e resumos da execução anterior. "
                "O relatório inteiro bate com a renderização do checkpoint; as métricas das ordens foram recalculadas na conferência.", ""]
    return "\n".join(out)


def ler_cache():
    if not SAIDA.exists():
        return None
    texto = SAIDA.read_text(encoding="utf-8", errors="replace")
    matches = list(re.finditer(rf"<!-- {MARCADOR}\n([A-Za-z0-9+/=]+)\n-->", texto))
    for m in reversed(matches):
        try:
            return json.loads(zlib.decompress(base64.b64decode(m[1])))
        except (ValueError, zlib.error, UnicodeError):
            continue
    if matches:
        print("[AVISO] Checkpoints danificados; sera recalculado.", flush=True)
    return None


def checkpoint(R):
    # A ordem de insercao tambem define a ordem das tabelas; preservar no JSON.
    payload = json.dumps(R, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    cache = base64.b64encode(zlib.compress(payload.encode("utf-8"), 9)).decode("ascii")
    return f"\n<!-- {MARCADOR}\n{cache}\n-->\n"


def documento(R):
    return renderizar(R) + checkpoint(R)


def gravar(R, atualizar_texto=False):
    # Um diario no proprio Markdown protege contra queda no meio da escrita.
    if not R.get("completo"):
        conteudo = documento(R) if atualizar_texto or not SAIDA.exists() else checkpoint(R)
        with SAIDA.open("a", encoding="utf-8", newline="\n") as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        return
    # Nao usar modo w: os checkpoints no fim sobrevivem a compactacao incompleta.
    with SAIDA.open("r+" if SAIDA.exists() else "w+", encoding="utf-8", newline="\n") as f:
        f.write(documento(R))
        f.flush()
        os.fsync(f.fileno())
        f.truncate()
        f.flush()
        os.fsync(f.fileno())


def executar_testes():
    comandos = [("-m", "unittest", "tests.test_politica_margens", "-v"),
                ("-m", "unittest", "discover", "-s", "tests", "-v")]
    saidas = []
    for args in comandos:
        cmd = [str(RAIZ / "venv/Scripts/python.exe"), "-B", *args]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", CUDA_VISIBLE_DEVICES="")
        r = subprocess.run(cmd, cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        saida = r.stdout + r.stderr
        n = re.search(r"Ran (\d+) tests?", saida)
        saidas.append({"comando": "venv/Scripts/python.exe -B " + " ".join(args), "codigo": r.returncode,
                       "n": int(n[1]) if n else None, "saida": saida})
        print(f"[{'OK' if r.returncode == 0 else 'FALHA'}] {' '.join(args)}: "
              f"{int(n[1]) if n else '?'} testes, codigo {r.returncode}.", flush=True)
        if r.returncode:
            print(saida, flush=True)
    return saidas


def conferir(R, conjuntos, H):
    if not R or R["hashes"] != H or not R.get("completo"):
        raise ValueError("Checkpoint incompleto ou hashes diferentes")
    for r in R["paginas"]:
        p, gt = conjuntos[r["conjunto"]][r["page_id"]]
        if gt != r["gt"]:
            raise ValueError("Referencia mudou")
        for m, ordem in r["ordens"].items():
            aplicar_margens(p["bounding_boxes"], ordem, p["dimensions"])
            if avaliar(ordem, gt) != r["metricas"][m]:
                raise ValueError(f"Metricas inconsistentes: {r['page_id']} / {m}")
        for g in r["grade"]:
            for m,d in g["metodos"].items():
                if avaliar(d["ordem"],gt) != d["metricas"]:
                    raise ValueError("Grade inconsistente")
    anterior = {k: R[k] for k in ("resumo", "quedas", "sensibilidade", "resumo_fora_v4")}
    agregar(R, conjuntos)
    if anterior != {k: R[k] for k in anterior}:
        raise ValueError("Agregacao nao reproduziu")
    if SAIDA.read_text(encoding="utf-8") != documento(R):
        raise ValueError("Relatorio diverge do checkpoint")
    print("[OK] Hashes, ordens, metricas, grade, resumos e Markdown integral conferidos.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--do-zero", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--testes", action="store_true")
    ap.add_argument("--reamostras", type=int, default=2000)
    ap.add_argument("--semente", type=int, default=7)
    args = ap.parse_args()
    if args.reamostras < 100:
        ap.error("usar pelo menos 100 reamostras")
    conjuntos, predicoes, auditoria, paths = carregar()
    H = hashes(paths)
    cache = ler_cache()
    if args.conferir:
        conferir(cache, conjuntos, H)
        return
    compativel = bool(cache and cache["hashes"] == H and cache["nboot"] == args.reamostras
                      and cache["semente"] == args.semente)
    anterior = cache if args.do_zero and compativel and cache.get("completo") else None
    R = cache if compativel and not args.do_zero else {
        "hashes": H, "nboot": args.reamostras, "semente": args.semente, "auditoria": auditoria,
        "paginas": [], "testes": [], "completo": False}
    feitos = {(r["conjunto"], r["page_id"]) for r in R["paginas"]}
    for nome in CONJUNTOS:
        for pid,(p,gt) in sorted(conjuntos[nome].items()):
            if (nome,pid) in feitos:
                continue
            R["paginas"].append(medir_pagina(nome,pid,p,gt,predicoes[nome]))
            # Publica numeros apos a primeira pagina e ao fechar cada conjunto.
            if len(R["paginas"]) == 1:
                agregar(R, conjuntos)
            gravar(R, atualizar_texto=len(R["paginas"]) == 1)
        agregar(R, conjuntos)
        gravar(R, atualizar_texto=True)
        print(f"[OK] {nome}: {len(conjuntos[nome])} paginas; relatorio atualizado.", flush=True)
    if args.testes:
        R["testes"] = executar_testes()
    R["completo"] = True
    if anterior:
        keys = ("paginas", "resumo", "quedas", "sensibilidade", "auditoria", "resumo_fora_v4")
        if any(R[k] != anterior[k] for k in keys):
            raise ValueError("Execucao do zero divergiu da anterior")
        R["reproduziu"] = True
    if hashes(paths) != H:
        raise ValueError("Entradas/fontes mudaram durante a execucao")
    gravar(R)
    conferir(R, conjuntos, H)
    # Imprime exatamente a tabela do relatorio para conferencia humana.
    t = renderizar(R).split("## Tabela principal: candidato com recorte geométrico\n\n",1)[1].split("\n\n##",1)[0]
    print(t, flush=True)
    print(f"[OK] {SAIDA.relative_to(RAIZ)}")
    if any(t["codigo"] for t in R["testes"]):
        raise SystemExit("Ha falhas na suite; ver relatorio/checkpoint.")


if __name__ == "__main__":
    main()
