"""Avalia uma unica variante HIER-1 congelada nas externas do E017.

Importa segmentar, hier1 e escores do E016 sem mudar seus parametros. Antes
de abrir externas, congela codigo/modelo e reproduz regra e E016 no ajuste.
Reusa a regua e o bootstrap oficiais; nao treina, nao usa GPU, nao abre PDFs,
anotacoes originais, parceiro ou teste cego. Cada pagina e persistida para
retomada: repetir o comando reutiliza predicoes, nunca escolhe outra variante.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e017_hier1_externas.py
  --somente-ancora  # congela e reproduz golden_v4 + RN, sem abrir externas
  --conferir       # confere fontes, caches e relatorio, sem nova inferencia
Escreve somente em resultados/e017_hier1_externas/. CPU, quatro threads,
um processo, num_workers=0. O criterio e exatamente o cartao E017 aprovado.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4",
                  OPENBLAS_NUM_THREADS="4", NUMEXPR_NUM_THREADS="4")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import argparse
import collections
import gc
import json
import math
import random
import statistics
import time
import types
from contextlib import contextmanager
from datetime import datetime, timezone

from orquestracao.analises import e016_hierarquico as hi
from orquestracao.analises.e016_hierarquico import segmentar, hier1
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e

g, h, o, c, np = hi.g, hi.h, hi.o, hi.c, hi.np
OUT = RAIZ / "resultados/e017_hier1_externas"
AJUSTE = ("golden_v4", "validacao_silver")
EXTERNAS = ("golden_v3_novo", "teste_silver")
COORTES = AJUSTE + EXTERNAS
METODOS = ("regra", "hibrido67", hi.GRAFO, "hier1")
LOCK_SHA = ASSINATURA = FONTE = FONTE16 = ESCORES = None
CONGELAMENTO = {}
FONTES_EXTERNAS = {}
PREDICOES = {}


def exigir(ok, mensagem):
    g.exigir(ok, mensagem)


def agora():
    return datetime.now(timezone.utc).isoformat()


def relativo(path):
    return Path(path).resolve().relative_to(RAIZ).as_posix()


def seguro(path):
    path = Path(path).resolve()
    exigir(path.is_relative_to(RAIZ), "Fonte fora do repositorio")
    nome = relativo(path)
    exigir(not any(x in nome.lower() for x in (
        "labelstudio", "e001_teste_cego", "data/raw/", "data/golden/", "data/diamond/")),
        "Leitura proibida: " + nome)
    return path


def ler(path, pagina=False):
    path = seguro(path)
    raw = path.read_text(encoding="utf-8")
    if pagina:
        m = o.re.search(r'"page_id"\s*:\s*("(?:[^"\\]|\\.)*")', raw)
        exigir(m is not None, "Cache sem page_id")
        o.permitido(json.loads(m.group(1)))
    return json.loads(raw)


def gravar(path, obj):
    path = Path(path).resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora do E017")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    c.substituir(tmp, path)


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if not f.tell():
            f.write(b"0")
            f.flush()
        f.seek(0)
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def vigiar():
    exigir(o.ler_lock()[0] == LOCK_SHA, "Lacre cego mudou; interrompido")
    mem = b.memoria()
    exigir(not mem or mem["ram_livre_mb"] >= 800, "RAM insuficiente; cache preservado")
    exigir(g.medir_memoria()["pico_rss_mb"] < 3072, "RSS excede 3 GiB; cache preservado")


def congelar():
    """Somente fontes de ajuste e metadados; nenhuma externa e aberta aqui."""
    global FONTE, FONTE16, ASSINATURA, CONGELAMENTO, ESCORES
    ponteiro = hi.OUT / "cache/ultima_execucao.json"
    FONTE16 = (hi.OUT / ler(ponteiro)["execucao"]).resolve()
    exigir(FONTE16.is_relative_to(hi.OUT), "Ponteiro E016 invalido")
    man16path = FONTE16 / "manifesto.json"
    man16 = ler(man16path)
    FONTE = seguro(RAIZ / man16["origem_e004"])
    exigir(FONTE.is_relative_to(g.OUT), "Origem E004 invalida")
    info = ler(FONTE / "modelo.json")
    selecao = ler(FONTE / "selecao_congelada.json")
    exigir(selecao["metodo"] == hi.GRAFO and selecao["config"] == hi.CFG == man16["config"],
           "Configuracao E004/E016 mudou")
    exigir(info["concluido"] and c.sha(seguro(FONTE / "modelo.txt")) == info["sha256"],
           "Modelo E004 incompleto ou alterado")
    exigir(b.NBOOT == 5000 and b.SEMENTE == 20261004, "Bootstrap oficial mudou")
    # Cartao E016 ganhou a conclusao depois da execucao; nao se exige seu hash
    # historico. Codigo, dados do ajuste, pesos e calibracao devem ser identicos.
    fontes = {}
    for nome, esperado in man16["fontes"].items():
        if nome.endswith(".py") or nome.startswith("resultados/unidades_sem_caixas/") or (
                nome.startswith(relativo(FONTE) + "/") and
                Path(nome).name in ("modelo.txt", "modelo.json", "selecao_congelada.json")):
            exigir(not any(co in nome for co in EXTERNAS), "Manifesto de ajuste contem externa")
            atual = c.sha(seguro(RAIZ / nome))
            exigir(atual == esperado, "Fonte difere do E016: " + nome)
            fontes[nome] = atual
    extras = [Path(__file__), ponteiro, man16path,
              RAIZ / "data/processed/splits.json",
              hi.OUT / "resumo_registro.json",
              RAIZ / "experimentos/PROTOCOLO_TESTE_CEGO.md"]
    extras += sorted((RAIZ / "experimentos/cards").glob("E017_*.md"))
    exigir(len(extras) > 6, "Cartao E017 ausente")
    for path in extras:
        fontes[relativo(path)] = c.sha(seguro(path))
    splits = ler(RAIZ / "data/processed/splits.json")
    exigir(splits["validacao"] == ["official_diary_rn"] and
           set(splits["teste"]) == {"official_diary_ce", "official_diary_ma", "official_diary_rj"},
           "Split congelado mudou")
    payload = {"experimento": "E017", "fontes": fontes, "lock_sha256": LOCK_SHA,
               "e016_sha256": fontes[relativo(Path(hi.__file__))],
               "e004_sha256": fontes[relativo(Path(g.__file__))],
               "modelo_sha256": info["sha256"], "origem_e004": relativo(FONTE),
               "origem_e016": relativo(FONTE16), "config": hi.CFG,
               "segmentacao": man16["segmentacao"], "metodos": list(METODOS),
               "ajuste": list(AJUSTE), "externas": list(EXTERNAS),
               "cpu": True, "threads": 4, "num_workers": 0, "retreino": False,
               "bootstrap": {"unidade": "veiculo", "reamostras": b.NBOOT, "semente": b.SEMENTE},
               "criterio": {"seguranca_ambas_ic_tau_inferior": -0.005,
                            "superioridade_uma_ic_quebras_superior_menor": 0,
                            "outra_media_delta_quebras_maxima": 0}}
    ASSINATURA = c.digest(payload)
    path = OUT / "congelamento.json"
    if path.exists():
        CONGELAMENTO = ler(path)
        exigir(CONGELAMENTO["assinatura"] == ASSINATURA and
               CONGELAMENTO["protocolo"] == payload, "Congelamento mudou; nao reabrir externas")
    else:
        CONGELAMENTO = {"gravado_utc": agora(), "assinatura": ASSINATURA, "protocolo": payload,
                        "externas_abertas_na_criacao": False}
        gravar(path, CONGELAMENTO)
    # A funcao de escores e o bytecode original do E016, num namespace isolado.
    # Somente caminhos de cache/escrita e estado do modelo pertencem ao E017.
    ESCORES = types.FunctionType(hi.escores.__code__, {**hi.escores.__globals__,
        "EXEC": OUT / "cache", "FONTE": FONTE, "INFO": info,
        "MODELO": None, "gravar": gravar}, "escores_e016")
    print("Congelamento conferido: " + ASSINATURA, flush=True)


def hibrido(co, p, ctx):
    if len(ctx["cs"]) > 67:
        return ctx["ordem"]
    if co == "validacao_silver":
        path = RAIZ / "resultados/e006_residual/predicoes_rn" / (e.ac.chave(p["page_id"]) + ".json")
        salvo = ler(path, pagina=True)
        exigir(salvo["pagina_sha256"] == c.digest(p), "LayoutReader RN de outra representacao")
        return salvo["ordem"]
    if co not in PREDICOES:
        path = seguro(b.OUT / "pred" / f"layoutreader_pronto__linhas__{co}.jsonl")
        rows = list(o.linhas_seguras(path))
        PREDICOES[co] = {r["page_id"]: r["ordem"] for r in rows}
        exigir(len(PREDICOES[co]) == len(rows), "LayoutReader duplicado")
        if co in EXTERNAS:
            FONTES_EXTERNAS[relativo(path)] = c.sha(path)
    exigir(p["page_id"] in PREDICOES[co], "LayoutReader ausente")
    return PREDICOES[co][p["page_id"]]


def processar(co, obj, p):
    exigir(co in COORTES, "Bancada fora do E017")
    o.permitido(p["page_id"])
    path = OUT / "cache/paginas" / co / (e.ac.chave(p["page_id"]) + ".json")
    fp = c.digest([ASSINATURA, obj, p])
    if path.exists():
        row = ler(path, pagina=True)
        exigir(row["fingerprint"] == fp, "Cache de outra pagina ou congelamento")
        for nome, sha in row["fontes_controle"].items():
            exigir(c.sha(seguro(RAIZ / nome)) == sha, "Controle alterado: " + nome)
        return row
    t0 = time.perf_counter()
    ctx, trs, q = g.preparar_pagina(obj, p)
    entrada = list(range(len(ctx["cs"])))
    random.Random(f"entrada-{p['page_id']}").shuffle(entrada)
    exigir(ctx["entrada"] == [ctx["cs"][i]["id"] for i in entrada], "Embaralhamento mudou")
    segmentos, _ = segmentar(ctx)
    probs = ESCORES(co, p, ctx)
    _, cand, _ = g.candidatos(ctx)
    internas = hier1(segmentos, ctx, cand[24], probs)
    ordens = {"regra": ctx["ordem"], "hibrido67": hibrido(co, p, ctx),
              hi.GRAFO: g.decodificar(ctx, cand[24], probs, hi.CFG),
              "hier1": [u for s in segmentos for u in internas[s["id"]]]}
    controlepath = FONTE / "inferencia" / co / (e.ac.chave(p["page_id"]) + ".json")
    antigo = ler(controlepath, pagina=True)
    exigir(antigo["page_id"] == p["page_id"], "E004 de outra pagina")
    controles = {relativo(controlepath): c.sha(controlepath)}
    resultados, corpo, hits, memo = {}, {}, {}, {}
    for nome, ordem in ordens.items():
        exigir(len(ordem) == len(ctx["cs"]) and set(ordem) == set(ctx["entrada"]),
               "Permutacao de unidades invalida")
        key = tuple(ordem)
        if key not in memo:
            res = o.avaliar_ordem(obj, p, ctx, ordem, trs, q)
            seq = [k for u in ordem for k in ctx["exp"][u]]
            memo[key] = (res, h.avaliar_corpo(q, ctx, ordem),
                         o.lm.acertos(q, seq, trs, res["metricas"]))
        resultados[nome], corpo[nome], hits[nome] = memo[key]
        exigir(all(resultados[nome]["metricas"][k] is not None and
                   math.isfinite(resultados[nome]["metricas"][k]) for k in o.METRICAS),
               "Metrica principal indefinida")
        if nome in antigo["resultados"]:
            esperado = antigo["resultados"][nome]
            exigir(ordem == esperado["ordem"], "Ordem nao reproduz E004: " + nome)
            exigir(all(abs(resultados[nome]["metricas"][k]-esperado["metricas"][k]) < 1e-11
                       for k in o.METRICAS), "Metrica nao reproduz E004: " + nome)
    if co in AJUSTE:
        p16 = FONTE16 / "paginas" / co / path.name
        r16 = ler(p16, pagina=True)
        controles[relativo(p16)] = c.sha(p16)
        exigir([s["unidades"] for s in segmentos] ==
               [s["unidades"] for s in r16["diagnostico"]["segmentos"]],
               "Segmentacao nao reproduz E016")
        for nome in METODOS:
            esperado = r16["resultados"][nome]
            exigir(ordens[nome] == esperado["ordem"] and all(
                abs(resultados[nome]["metricas"][k]-esperado["metricas"][k]) < 1e-11
                for k in o.METRICAS), "Ancora E016 nao reproduzida: " + co + "/" + nome)
    pares = {nome: {base: {tipo: {
        "reparos": sum(new and not old for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo),
        "regressoes": sum(old and not new for tr, old, new in zip(trs, hits[base], nh) if tr["tipo"] == tipo)}
        for tipo in c.TIPOS} for base in ("regra", "hibrido67", hi.GRAFO)} for nome, nh in hits.items()}
    rank = {u: i for i, u in enumerate(ordens["hibrido67"])}
    deslocamentos = [abs(i-rank[u]) for i, u in enumerate(ordens["hier1"])]
    row = {"page_id": p["page_id"], "uf": obj["uf"], "fingerprint": fp,
           "unidades": len(ctx["cs"]), "colunas": len(ctx["cortes"])+1,
           "cortes_colunas": ctx["cortes"], "segmentos": segmentos,
           "resultados": resultados, "corpo": corpo, "pares_sucessor": pares,
           "deslocamentos_vs_hibrido67": deslocamentos,
           "fontes_controle": controles, "segundos": time.perf_counter()-t0}
    gravar(path, row)
    return row


def executar(co):
    rows = []
    for obj, p in o.paginas(co):
        vigiar()
        row = processar(co, obj, p)
        rows.append(row)
        print(f"{co}: {len(rows)} paginas; {len(row['segmentos'])} segmentos", flush=True)
        gc.collect()
    exigir(rows and len({r["page_id"] for r in rows}) == len(rows), "Bancada vazia/duplicada")
    return rows


def ancoras():
    """Reexecuta os controles antes de permitir qualquer leitura externa."""
    an = o.ancora()
    dados = {co: executar(co) for co in AJUSTE}
    exigir(len(dados["golden_v4"]) == 44 and len(dados["validacao_silver"]) == 15,
           "Ajuste incompleto")
    esperado = ler(hi.OUT / "resumo_registro.json")
    medias = {}
    for co, rows in dados.items():
        for nome in METODOS:
            atual = {k: statistics.mean(r["resultados"][nome]["metricas"][k] for r in rows)
                     for k in o.METRICAS}
            ref = esperado[co + "/" + nome]
            exigir(all(abs(atual[k]-ref[z]) < 1e-11 for k, z in (
                ("tau", "tau"), ("quebras", "quebras"), ("sucessor_linhas", "sucessor"))),
                "PARE: media E016 nao reproduzida: " + co + "/" + nome)
            medias[co + "/" + nome] = atual
    validacao = {"assinatura": ASSINATURA, "regra": an, "e016": medias, "aprovada": True}
    gravar(OUT / "cache/ancoras.json", validacao)
    print("Ancoras E016 reproduzidas no golden_v4 e RN, pagina a pagina e na media.", flush=True)
    return validacao, dados


def registrar_fontes_externas():
    """Executada somente depois do congelamento e das ancoras aprovadas."""
    paths = [b.UNIDADES / "bancadas/golden_v3_novo.jsonl"]
    splits = ler(RAIZ / "data/processed/splits.json")
    for uf in splits["teste"]:
        paths += [b.UNIDADES / "linhas" / (uf+s) for s in (".jsonl", ".palavras.jsonl")]
    for co in EXTERNAS:
        paths.append(b.OUT / "pred" / f"layoutreader_pronto__linhas__{co}.jsonl")
    for path in paths:
        path = seguro(path)
        # O leitor oficial verifica o ID protegido antes da desserializacao.
        for _ in o.linhas_seguras(path):
            pass
        FONTES_EXTERNAS[relativo(path)] = c.sha(path)
    path = OUT / "cache/fontes_externas.json"
    atual = {"assinatura": ASSINATURA, "fontes": dict(FONTES_EXTERNAS)}
    if path.exists():
        exigir(ler(path) == atual, "Fontes externas mudaram; nao repetir avaliacao")
    else:
        gravar(path, atual)


def decidir(resumos):
    ds = {co: resumos[co]["hier1"]["contrastes"]["hibrido67"] for co in EXTERNAS}
    seguros = {co: ds[co]["tau"]["ic"][0] >= -.005 for co in EXTERNAS}
    superiores = {co: ds[co]["quebras"]["ic"][1] < 0 for co in EXTERNAS}
    medias = {co: ds[co]["quebras"]["media"] for co in EXTERNAS}
    outra = {EXTERNAS[0]: EXTERNAS[1], EXTERNAS[1]: EXTERNAS[0]}
    combinado = any(superiores[co] and medias[outra[co]] <= 0 for co in EXTERNAS)
    passou = all(seguros.values()) and combinado
    return {"veredito": "GO" if passou else "NÃO GO", "passou": passou,
            "seguranca_por_bancada": seguros, "superioridade_por_bancada": superiores,
            "superioridade_uma_sem_piora_media_na_outra": combinado,
            "delta_quebras_medio": medias,
            "finalistas": ["hibrido67", "regra", "hier1"] if passou else ["hibrido67", "regra"]}


def relatorio(estado):
    """Todos os numeros publicados derivam dos resultados desta execucao."""
    dados, resumos, gate = estado["dados"], estado["resumos"], estado["criterio"]
    f, ic = o.f, o.ic
    an = estado["ancoras"]
    linha_externa = lambda co: (
        f"{co}: HIER-1 {f(resumos[co]['hier1']['metricas']['quebras']['media'],6)} quebras/página, "
        f"τ {f(resumos[co]['hier1']['metricas']['tau']['media'],6)}; "
        f"Δ quebras vs híbrido {ic(resumos[co]['hier1']['contrastes']['hibrido67']['quebras'],6)}.")
    linhas = [
        f"1. Âncora da regra reproduzida: τ {f(an['regra']['tau'],6)} / {f(an['regra']['quebras'],6)} quebras/página no golden_v4.",
        f"2. E016 reproduzido: HIER-1 no golden_v4 {f(an['e016']['golden_v4/hier1']['quebras'],6)} / τ {f(an['e016']['golden_v4/hier1']['tau'],6)}; código e modelo congelados antes das externas.",
        "3. " + linha_externa(EXTERNAS[0]),
        "4. " + linha_externa(EXTERNAS[1]),
        "5. Segurança nas duas externas: " + ("PASSA" if all(gate['seguranca_por_bancada'].values()) else "FALHA") +
        "; superioridade em uma sem piora média na outra: " + ("PASSA" if gate['superioridade_uma_sem_piora_media_na_outra'] else "FALHA") + ".",
        "6. Uma variante, sem ajuste nem retreino; golden_v3_novo já foi consultado em rodadas anteriores; teste cego preservado.",
        "", "**Veredito: " + gate["veredito"] + ".** " +
        ("HIER-1 atende ao cartão e é finalista congelado do teste cego." if gate["passou"] else
         "HIER-1 permanece exploratório; finalistas do teste cego: híbrido 67 e regra."),
        "", "# E017 — HIER-1 congelado nas externas", "", "## Protocolo e congelamento", "",
        "Uma única configuração, autorizada pelo cartão E017 após o NÃO GO do E016; o portão anterior não foi alterado. "
        "Segmentação e HIER-1 são as funções importadas do E016. Escores são produzidos pela função original do E016 "
        "com o mesmo E004 e calibração; somente o namespace de caminhos de saída é isolado. "
        "K24, max-regret, limiar zero, nenhuma restrição adicional, regra entre segmentos. "
        "Sem GPU, treino ou inferência nova do LayoutReader; o híbrido usa suas predições congeladas até 67 unidades.", "",
        "SHA-256 gravados em congelamento.json antes de abrir externas:", "",
        "| Fonte | SHA-256 |", "|---|---|"]
    for key in ("e016_sha256", "e004_sha256", "modelo_sha256"):
        linhas.append(f"| {key} | `{CONGELAMENTO['protocolo'][key]}` |")
    linhas += ["", "CPU, quatro threads, um processo, num_workers=0. Caches atômicos por página/escores permitem "
        "retomada da mesma execução após queda; páginas prontas não são inferidas novamente. "
        "As ordens e métricas da regra, híbrido e grafo plano são conferidas contra os controles já existentes; "
        "no ajuste, também se conferem todos os segmentos e ordens do E016. "
        "Entrada conferida com random.Random(f'entrada-{page_id}'). Linhas e átomos ls3 congelados; "
        "cobertura integral, mesmas unidades e expansões canônicas em todos os métodos.", "",
        "Régua importada: erros_ponta_a_ponta e bancada_ordenadores via avaliar_ordem do E002; "
        "sem reimplementar τ de palavras, quebras, fidelidade de 12 ou sucessor de linhas. "
        "Quebras/1.000 palavras é a média das taxas por página da régua (denominador: palavras com referência). "
        "Médias por página, bancadas separadas. IC95 percentil pareado, bootstrap por veículo com "
        f"{b.NBOOT} reamostras e semente {b.SEMENTE}, funções oficiais. "
        "Wilcoxon Pratt bilateral sobre as médias dos Δ por veículo, apenas descritivo. "
        "Esta rodada externa segue a unidade veículo do cartão E017; o teste cego tem outro bootstrap, "
        "por PDF estratificado por UF, e não é executado aqui.", "", "## Critério E017, item a item", "",
        "Interseção de segurança e superioridade, sem compensar perda de τ com ganho de quebras.", "",
        "| Item | Valor observado | Limiar congelado | Resultado |", "|---|---:|---|---|"]
    for co in EXTERNAS:
        d = resumos[co]["hier1"]["contrastes"]["hibrido67"]
        linhas.append(f"| (1) Segurança: {co} | LI Δτ = {f(d['tau']['ic'][0],6)} | ≥ −0,005 | " +
                      ("PASSA" if gate["seguranca_por_bancada"][co] else "FALHA") + " |")
    for co in EXTERNAS:
        d = resumos[co]["hier1"]["contrastes"]["hibrido67"]["quebras"]
        linhas.append(f"| (2) Superioridade: {co} | LS Δquebras = {f(d['ic'][1],6)}; média = {f(d['media'],6)} | "
                      "LS < 0 em pelo menos uma; média ≤ 0 na outra | " +
                      ("LS < 0" if gate["superioridade_por_bancada"][co] else "LS ≥ 0") + " |")
    linhas.append("| (2) Condição conjunta de superioridade | uma LS < 0 e média da outra ≤ 0 | obrigatória | " +
                  ("PASSA" if gate["superioridade_uma_sem_piora_media_na_outra"] else "FALHA") + " |")
    linhas += ["", "Robustez: Δ por veículo, regressões graves e deslocamentos são reportados abaixo e não mudam o critério.", ""]
    registro = {}
    # Tres bancadas oficiais separadas; RN e um apendice de reproducao do ajuste.
    for co in ("golden_v4", *EXTERNAS, "validacao_silver"):
        rs, rr = dados[co], resumos[co]
        papel = "ajuste" if co == "golden_v4" else "apêndice de ajuste RN" if co == "validacao_silver" else "externa"
        linhas += [f"## {co} — {papel}", "",
            f"{len(rs)} páginas; {len({r['uf'] for r in rs})} veículos. "
            f"Cobertura mínima de palavras: {f(100*min(s['cobertura'] for s in rr.values()),1)}%.", "",
            "| Método | τ palavras | Quebras/pág | Quebras/1.000 palavras | Fidelidade 12 | Sucessor linhas |",
            "|---|---:|---:|---:|---:|---:|"]
        for nome in METODOS:
            s = rr[nome]
            linhas.append(f"| {nome} | " + " | ".join(f(s["metricas"][k]["media"],6)
                for k in ("tau", "quebras", "quebras_mil", "fid12", "sucessor_linhas")) + " |")
            registro[co+"/"+nome] = {z: s["metricas"][k]["media"] for z, k in (
                ("tau", "tau"), ("quebras", "quebras"), ("sucessor", "sucessor_linhas"))}
        linhas += ["", "### Δ contra controles, IC95 e Wilcoxon por veículo", "",
            "M/I/P = páginas melhores/iguais/piores, no sentido de cada métrica; Δ = método − base.", "",
            "| Método | Base | Métrica | Δ [IC95 veículo] | p veículo | M/I/P |",
            "|---|---|---|---:|---:|---:|"]
        for nome in ("hibrido67", hi.GRAFO, "hier1"):
            for base in ("regra", "hibrido67"):
                if nome == base:
                    continue
                for k, d in rr[nome]["contrastes"][base].items():
                    linhas.append(f"| {nome} | {base} | {k} | {ic(d,6)} | "
                        f"{f(d['wilcoxon_veiculo']['p'],6)} | {d['melhor']}/{d['igual']}/{d['pior']} |")
        linhas += ["", "### HIER-1 por veículo", "",
            "| Veículo | Páginas | Δτ vs regra | Δquebras vs regra | Δτ vs híbrido | Δquebras vs híbrido |",
            "|---|---:|---:|---:|---:|---:|"]
        for uf in sorted({r["uf"] for r in rs}):
            vals = [rr["hier1"]["contrastes"][base][k]["por_veiculo"][uf]
                    for base in ("regra", "hibrido67") for k in ("tau", "quebras")]
            linhas.append(f"| {uf} | {sum(r['uf'] == uf for r in rs)} | " +
                          " | ".join(f(v,6) for v in vals) + " |")
        graves = [(r, r["resultados"]["hier1"]["metricas"]["tau"]-
                   r["resultados"]["hibrido67"]["metricas"]["tau"]) for r in rs]
        graves = sorted(((r, d) for r, d in graves if d < -.1), key=lambda par: par[1])
        linhas += ["", "### Regressões graves do HIER-1: Δτ < −0,1 vs híbrido", "",
            f"{len(graves)} páginas. Colunas = número de cortes globais do contexto original + 1 "
            "(proxy geométrica do E004; segmentos locais não equivalem a colunas).", "",
            "| Página | Δτ | Unidades | Colunas | Segmentos |", "|---|---:|---:|---:|---:|"]
        for r, d in graves:
            linhas.append(f"| `{r['page_id']}` | {f(d,6)} | {r['unidades']} | {r['colunas']} | {len(r['segmentos'])} |")
        linhas += ["", "### Reparos e regressões de sucessores", "",
            "Contagem de arestas-ouro de linhas: errado→certo / certo→errado. Classes importadas, sem reinterpretar erros como causas.", "",
            "| Método | Base | Classe | Reparos | Regressões |", "|---|---|---|---:|---:|"]
        for nome in (hi.GRAFO, "hier1"):
            for base in ("regra", "hibrido67"):
                par = rr[nome]["pares_sucessor"][base]
                for tipo, v in par.items():
                    linhas.append(f"| {nome} | {base} | {tipo} | {v['reparos']} | {v['regressoes']} |")
                linhas.append(f"| {nome} | {base} | TOTAL | {sum(v['reparos'] for v in par.values())} | "
                              f"{sum(v['regressoes'] for v in par.values())} |")
        desloc = [d for r in rs for d in r["deslocamentos_vs_hibrido67"]]
        quant = np.percentile(desloc, [50, 90, 100]).tolist()
        linhas += ["", "### Deslocamentos do HIER-1 em relação ao híbrido", "",
            f"Deslocamento absoluto em posições de unidade, todas as unidades/páginas: "
            f"{sum(d > 0 for d in desloc)}/{len(desloc)} unidades mudam de posição; "
            f"mediana {f(quant[0],2)}, p90 {f(quant[1],2)}, máximo {f(quant[2],0)}. "
            "Diagnóstico contra a ordem do híbrido, não contra o ouro; não decide o GO.", "",
            "### Corpo sem margens — sensibilidade", "",
            "Mesma projeção automática importada do E014 em todos os métodos; não seleciona páginas nem altera o veredito.", "",
            "| Método | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |", "|---|---:|---:|---:|---:|"]
        for nome in METODOS:
            linhas.append(f"| {nome} | " + " | ".join(f(rr[nome]["corpo"][k]["media"],6)
                for k in ("tau", "quebras", "fid12", "sucessor_linhas")) + " |")
        linhas.append("")
    linhas += ["## Limitações", "",
        "Avaliação exploratória externa de uma hipótese motivada pelo ajuste do E016; não apaga seu NÃO GO. "
        "golden_v3_novo já foi consultado em rodadas anteriores e não é teste confirmatório. "
        "Uma anotação humana por página, silver ruidoso e seleção histórica dos veículos por concordância com heurística. "
        "Poucos veículos no teste silver tornam o IC discreto; RN tem um único veículo e IC degenerado. "
        "As médias são por página, não a macro-UF confirmatória do teste cego. "
        "Cobertura integral significa preservar as palavras digitais disponíveis, não comprovar ausência de falhas de OCR/extração. "
        "Segmentos geométricos podem impedir ordens humanas que reentram neles; colunas são uma proxy automática. "
        "O modelo treinado é o checkpoint já selecionado do E004, sem novas sementes ou treino. "
        "Nenhuma decisão foi tomada por p-valor, por diagnóstico de regressões ou por corpo sem margens. "
        "Nenhuma página/PDF lacrado, anotação original ou dado do parceiro foi aberto; nenhuma escrita em data/, "
        "documentação, cartão ou registro compartilhado. O teste cego permanece reservado ao orquestrador.", ""]
    exigir(all(v is not None and math.isfinite(v) for s in registro.values() for v in s.values()),
           "Resumo de registro incompleto")
    return "\n".join(linhas), registro


def conferir_fontes():
    for nome, sha in CONGELAMENTO["protocolo"]["fontes"].items():
        exigir(c.sha(seguro(RAIZ / nome)) == sha, "Fonte congelada mudou: " + nome)
    for nome, sha in FONTES_EXTERNAS.items():
        exigir(c.sha(seguro(RAIZ / nome)) == sha, "Fonte externa mudou: " + nome)
    vigiar()


def conferir():
    estado = ler(OUT / "estado.json")
    exigir(estado["completo"] and estado["assinatura"] == ASSINATURA, "Estado incompleto/divergente")
    FONTES_EXTERNAS.update(estado["fontes_externas"])
    conferir_fontes()
    exigir(set(estado["dados"]) == set(COORTES), "Bancadas inesperadas")
    for co, rows in estado["dados"].items():
        for r in rows:
            o.permitido(r["page_id"])
            path = OUT / "cache/paginas" / co / (e.ac.chave(r["page_id"])+".json")
            exigir(ler(path, pagina=True) == r, "Cache diverge do estado")
            for nome, sha in r["fontes_controle"].items():
                exigir(c.sha(seguro(RAIZ / nome)) == sha, "Controle mudou: " + nome)
    resumos = {co: h.resumir(rs, METODOS) for co, rs in estado["dados"].items()}
    exigir(resumos == estado["resumos"] and decidir(resumos) == estado["criterio"],
           "Resumo ou criterio diverge dos caches")
    md, reg = relatorio(estado)
    exigir(md == (OUT / "RELATORIO.md").read_text(encoding="utf-8"), "Relatorio divergente")
    exigir(reg == ler(OUT / "resumo_registro.json"), "Registro divergente")
    print("Conferencia concluida: hashes, caches, estatisticas, criterio, relatorio e registro coerentes; sem nova inferencia.", flush=True)


def main():
    global LOCK_SHA
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--somente-ancora", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    exigir(not (args.somente_ancora and args.conferir), "Escolha somente um modo")
    LOCK_SHA, o.PROTEGIDOS = o.ler_lock()
    o.PROTEGIDOS.update(x.rsplit("#p", 1)[0] for x in list(o.PROTEGIDOS) if "#p" in x)
    if "torch" in sys.modules:
        sys.modules["torch"].set_num_threads(4)
    with trava():
        congelar()
        if args.conferir or (OUT / "estado.json").exists():
            conferir()
            return
        an, dados = ancoras()
        if args.somente_ancora:
            return
        conferir_fontes()
        path = OUT / "cache/externas_iniciadas.json"
        if path.exists():
            exigir(ler(path)["assinatura"] == ASSINATURA, "Execucao externa de outra variante")
        else:
            gravar(path, {"assinatura": ASSINATURA, "inicio_utc": agora(), "ancoras_aprovadas": True})
        registrar_fontes_externas()
        for co in EXTERNAS:
            dados[co] = executar(co)
        conferir_fontes()
        resumos = {co: h.resumir(rs, METODOS) for co, rs in dados.items()}
        gate = decidir(resumos)
        estado = {"assinatura": ASSINATURA, "completo": True, "fim_utc": agora(),
                  "ancoras": an, "dados": dados, "resumos": resumos, "criterio": gate,
                  "fontes_externas": dict(FONTES_EXTERNAS), "memoria": g.medir_memoria()}
        md, registro = relatorio(estado)
        gravar(OUT / "RELATORIO.md", md)
        gravar(OUT / "resumo_registro.json", registro)
        gravar(OUT / "estado.json", estado)
        print(json.dumps(gate, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        falha = {"data_utc": agora(), "erro": str(exc), "assinatura": ASSINATURA,
                 "externas_iniciadas": (OUT / "cache/externas_iniciadas.json").exists()}
        gravar(OUT / "falha.json", falha)
        if not (OUT / "estado.json").exists():
            gravar(OUT / "RELATORIO.md", "1. Execução interrompida; nenhum veredito estatístico emitido.\n"
                "2. Os caches existentes foram preservados.\n3. Nenhum parâmetro foi alterado.\n"
                "4. Teste cego preservado.\n5. Motivo registrado pela execução: " + str(exc) +
                "\n6. Corrigir somente a execução, sem escolher variante pelas externas.\n\n"
                "**Veredito: INTERROMPIDO.**\n")
        raise
