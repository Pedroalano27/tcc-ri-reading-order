"""Avalia a mediana congelada do E014 com a salvaguarda predefinida no E015.

Importa inferencia, variantes, avaliacao e estatistica do E014, sem treino ou
copia de algoritmos. A salvaguarda compara as palavras expandidas das duas
ordens, sem referencia humana/silver, conforme a regua de tau do protocolo.
O limiar e estritamente zero; o tau entre unidades tambem fica como diagnostico.
Congela codigo/fontes depois do ajuste e ANTES de abrir as externas. Resultados
externos sao persistidos por pagina e reutilizados na retomada. A combinacao
exploratoria e montada dos mesmos resultados somente DEPOIS do veredito.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e015_mediana.py
  --etapa ajuste     # ancora, ajuste, diagnostico RN e congelamento
  --etapa tudo       # retoma ajuste e abre cada externa uma unica vez
  --conferir         # reconstroi resumos dos caches, sem reavaliar paginas
  --max-minutos 30   # interrupcao retomavel por pagina
Toda escrita fica em resultados/e015_mediana/. CPU, quatro threads, um processo,
sem GPU, multiprocessing, DataLoader, Label Studio ou escrita sob data/.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from orquestracao.analises import e014_cadeias as m
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
import argparse
import copy
import gc
import math
import statistics
import time
from datetime import datetime, timezone

o, c, g = m.o, m.c, m.g
OUT = RAIZ / "resultados/e015_mediana"
MED = "b_mediana"
CAND = "b_mediana_salvaguarda"
EXP = "hibrido67_mediana_salvaguarda"
CONTROLES = ("regra", "hibrido67", m.GRAFO)
NOMES = (*CONTROLES, MED, CAND)
RN = "official_diary_rn/DOE-RN_2022-12-29_Ordinaria.pdf#p40"
CRITERIOS = {
    "candidato": CAND, "salvaguarda": "tau_palavras(mediana,regra)<0 => regra",
    "tau_sem_referencia": True, "limiar": 0,
    "externas": list(o.COORTES[2:]), "margem_tau": .005,
    "delta_quebras_hibrido_maximo": 0, "ic95_superior_negativo_em": 1,
    "catastrofe_delta_tau": -.5, "hibrido_densa_acima_de": 67,
    "sem_selecao_nova": True,
}
EXEC = None
MAN = None
AJUSTE_E014 = None


def agora():
    return datetime.now(timezone.utc).isoformat()


def iniciar():
    """Verifica hashes das fontes; nao desserializa paginas externas."""
    global EXEC, MAN, AJUSTE_E014
    origem14 = m.OUT
    AJUSTE_E014 = origem14 / b.ler(origem14 / "cache/ultima_execucao.json")["execucao"]
    m.OUT = OUT
    base = m.iniciar()
    fontes = dict(base["fontes"])
    paths = [Path(__file__), origem14 / "RELATORIO.md",
             AJUSTE_E014 / "manifesto.json",
             *sorted((RAIZ / "experimentos/cards").glob("E015_*.md"))]
    for co in o.DESENV:
        paths.extend(sorted((AJUSTE_E014 / "escores" / co).glob("*.json")))
    for path in paths:
        fontes[path.relative_to(RAIZ).as_posix()] = c.sha(path)
    MAN = {"experimento": "E015", "fontes": fontes, "base_e014": base,
           "criterios": CRITERIOS, "lock_sha256": m.LOCK_SHA,
           "escores_ajuste_e014": AJUSTE_E014.relative_to(RAIZ).as_posix(),
           "tau_salvaguarda": "palavras canonicas completas; regra como ordem de comparacao; sem ouro",
           "cpu": True, "gpu": False, "treino": False, "threads": 4, "num_workers": 0}
    assinatura = c.digest(MAN)
    EXEC = OUT / "cache" / assinatura
    m.EXEC, m.ASSINATURA = EXEC, assinatura
    abertura = m.ler(OUT / "abertura_externas.json")
    m.exigir(abertura is None or abertura["assinatura"] == assinatura,
             "Externas ja abertas com outro codigo/fontes; nao iniciar outra execucao")
    return MAN


def salvaguardar(ctx, ordem):
    """Aplica literalmente tau < 0, sem acesso a referencia ou metricas de ouro."""
    regra = ctx["ordem"]
    m.exigir(len(ordem) == len(regra) and set(ordem) == set(regra), "Permutacao invalida")
    expandir = lambda seq: [k for uid in seq for k in ctx["exp"][uid]]
    tau = e.o.kendall_tau(expandir(ordem), expandir(regra))
    aciona = tau < CRITERIOS["limiar"]
    return (regra if aciona else ordem), {
        "tau_palavras_vs_regra": tau,
        "tau_unidades_vs_regra": e.o.kendall_tau(ordem, regra),
        "acionada": aciona, "fonte": "regra" if aciona else MED}


def alias(row, nome, fonte):
    """Reusa a mesma predicao/medicao; nao avalia a pagina de novo."""
    for campo in ("resultados", "corpo", "pares_sucessor"):
        row[campo][nome] = copy.deepcopy(row[campo][fonte])
    if nome not in row["solicitados"]:
        row["solicitados"].append(nome)


def avaliar(co):
    """Embrulha o E014 e guarda a ordem/decisao de salvaguarda por pagina."""
    salvos, rows = g.predicoes_salvas(co), []
    for obj, p in o.paginas(co):
        m.vigiar()
        path = EXEC / "avaliacao" / co / (e.ac.chave(p["page_id"]) + ".json")
        row = m.ler(path)
        if row is None or "salvaguarda" not in row:
            # Reusa escores ja congelados no ajuste. As externas passam pela
            # inferencia importada do E014 com o mesmo modelo do E004.
            if co in o.DESENV:
                score = AJUSTE_E014 / "escores" / co / path.name
                m.exigir(score.exists(), "E014 sem escore de ajuste")
                m.gravar(EXEC / "escores" / co / path.name, b.ler(score))
            row = m.avaliar_pagina(co, obj, p, list(CONTROLES) + [MED], salvos)
            ctx = c.contexto(p, obj["palavras"])
            gr = m.grafo_pagina(co, obj, p, ctx)
            med = m.variantes(ctx, gr)[0][MED]
            ordem, info = salvaguardar(ctx, med)
            alias(row, CAND, info["fonte"])
            row["salvaguarda"] = info
            row["ordens"] = {"regra": ctx["ordem"], MED: med, CAND: ordem}
            m.exigir(all(v["cobertura_palavras"] == 1 for v in row["resultados"].values()),
                     "Cobertura incompleta")
            m.gravar(path, row)
        rows.append(row)
        print(f"E015 {co}: {len(rows)}; salvaguarda={row['salvaguarda']['acionada']}", flush=True)
        gc.collect()
    m.gravar(EXEC / ("ordem_" + co + ".json"), [r["page_id"] for r in rows])
    return rows


def diagnosticar_rn(rows):
    """Explica a mediana por IDs e pertinencia de palavras, somente no ajuste."""
    path = EXEC / "diagnostico_rn.json"
    antigo = m.ler(path)
    if antigo:
        return antigo
    row = next(r for r in rows if r["page_id"] == RN)
    obj, p = next((obj, p) for obj, p in o.paginas("validacao_silver") if p["page_id"] == RN)
    ctx, q = c.contexto(p, obj["palavras"]), b.referencia(obj, p)
    gr = m.grafo_pagina("validacao_silver", obj, p, ctx)
    chs = m.cadeias(ctx["ordem"], gr["saida"])
    dono = {k: L["id"] for L in q["gold_lines"] for k in L["ks"]}
    unidades = {}
    for uid in ctx["ordem"]:
        lids = {dono[k] for k in ctx["exp"][uid] if k in dono}
        unidades[uid] = {"palavras": len(ctx["exp"][uid]),
                         "posto_regra": ctx["rank_regra"][uid],
                         "linhas": [lid for lid in q["gt_l"] if lid in lids],
                         "texto": ctx["mapa"][uid]["text"][:130]}
    chains = [{"unidades": ch, "postos_regra": [ctx["rank_regra"][u] for u in ch],
               "mediana": statistics.median(ctx["rank_regra"][u] for u in ch),
               "palavras": sum(unidades[u]["palavras"] for u in ch)} for ch in chs]
    d = {"page_id": RN, "salvaguarda": row["salvaguarda"], "ordens": row["ordens"],
         "cadeias": chains, "unidades": unidades,
         "metricas": {n: row["resultados"][n]["metricas"] for n in ("regra", MED, CAND)}}
    m.gravar(path, d)
    return d


def congelar(an, dados, diagnostico):
    """Persiste codigo e hashes antes de permitir qualquer leitura externa."""
    path = OUT / "congelamento.json"
    previsto = {"assinatura": c.digest(MAN), "codigo_sha256": c.sha(Path(__file__)),
                "fontes": MAN["fontes"], "criterios": CRITERIOS,
                "ancora": an, "diagnostico_rn_sha256": c.digest(diagnostico),
                "ajuste_sha256": c.digest({co: dados[co] for co in o.DESENV})}
    anterior = m.ler(path)
    if anterior:
        if {k: anterior[k] for k in previsto} == previsto:
            return anterior
        m.exigir(not (OUT / "abertura_externas.json").exists(),
                 "Congelamento mudou depois de abrir externas; proibida nova execucao")
        # Uma correcao operacional antes de abrir as externas pode exigir
        # outro hash. Preserva o congelamento anterior para auditoria.
        m.gravar(OUT / "cache" / anterior["assinatura"] / "congelamento_anterior.json", anterior)
    previsto["congelado_em_utc"] = agora()
    m.gravar(EXEC / "codigo_congelado.py", Path(__file__).read_text(encoding="utf-8"))
    m.gravar(path, previsto)
    print("CONGELADO antes das externas: " + previsto["codigo_sha256"], flush=True)
    return previsto


def resumir(dados, exploratorio=False):
    nomes = [*NOMES, *([EXP] if exploratorio else [])]
    return {co: m.resumir(rows, nomes) for co, rows in dados.items() if rows}


def catastrofes(dados):
    return {co: {nome: [{"page_id": r["page_id"],
                        "delta_tau": r["resultados"][nome]["metricas"]["tau"] -
                                     r["resultados"]["regra"]["metricas"]["tau"],
                        "salvaguarda": r["salvaguarda"]}
                       for r in rows if r["resultados"][nome]["metricas"]["tau"] -
                           r["resultados"]["regra"]["metricas"]["tau"] < -.5]
                 for nome in (MED, CAND)} for co, rows in dados.items()}


def julgar(resumos, casos):
    """Aplica o cartao ao candidato; a variante sem salvaguarda nao e finalista."""
    if not all(co in resumos for co in o.COORTES[2:]):
        return {"veredito": "PENDENTE: externas ainda não concluídas", "itens": {}}
    externos = {co: resumos[co][CAND] for co in o.COORTES[2:]}
    for r in externos.values():
        m.exigir(r["completo"] and r["contrastes"]["hibrido67"]["tau"]["n"] == r["n"],
                 "Criterio externo requer cobertura identica e hibrido completo")
    quebras = all(r["contrastes"]["hibrido67"]["quebras"]["media"] <= 0 for r in externos.values())
    ic = any(r["contrastes"]["hibrido67"]["quebras"]["ic"][1] < 0 for r in externos.values())
    tau = all(r["contrastes"]["regra"]["tau"]["media"] >= -.005 for r in externos.values())
    raw = sum(len(casos[co][MED]) for co in externos)
    guard = sum(len(casos[co][CAND]) for co in externos)
    seguro = raw == 0 or guard == 0 and quebras and ic and tau
    itens = {"1a_quebras_nao_pioram_nas_duas": quebras,
             "1b_ic95_negativo_em_ao_menos_uma": ic,
             "2_tau_dentro_da_margem_nas_duas": tau,
             "3_sem_catastrofe_ou_salvaguarda_resolve_sem_violar_1_2": seguro}
    ok = all(itens.values())
    return {"veredito": "GO" if ok else "NÃO GO", "itens": itens,
            "catastrofes_sem_salvaguarda": raw, "catastrofes_candidato": guard,
            "candidato": CAND}


def explorar(dados, veredito):
    """Combina predicoes medidas; nenhum novo ajuste ou avaliacao de pagina."""
    m.exigir(veredito["veredito"] in ("GO", "NÃO GO"), "Exploracao antes do veredito")
    out = copy.deepcopy(dados)
    for co, rows in out.items():
        for row in rows:
            fonte = CAND if row["unidades"] > 67 else "hibrido67"
            if fonte in row["resultados"]:
                alias(row, EXP, fonte)
    return out


def numero(x, n=6):
    return "indisponível" if x is None else f"{x:.{n}f}".replace(".", ",")


def intervalo(d):
    return f"{numero(d['media'])} [{numero(d['ic'][0])}; {numero(d['ic'][1])}]"


def texto_rn(d):
    f = numero
    ls = ["## RN p40 — diagnóstico no ajuste", "", f"Página `{d['page_id']}`.", "",
          f"Regra: `{d['ordens']['regra']}`; mediana: `{d['ordens'][MED]}`; "
          f"candidato: `{d['ordens'][CAND]}`.", "",
          f"τ mediana × regra sem referência: palavras {f(d['salvaguarda']['tau_palavras_vs_regra'])}; "
          f"unidades {f(d['salvaguarda']['tau_unidades_vs_regra'])}. "
          f"Salvaguarda acionada: {d['salvaguarda']['acionada']}.", "",
          "| Cadeia de unidades | Postos na regra (base zero) | Mediana | Palavras |",
          "|---|---|---:|---:|"]
    for ch in d["cadeias"]:
        ls.append(f"| `{ch['unidades']}` | {ch['postos_regra']} | {f(ch['mediana'],1)} | {ch['palavras']} |")
    ls += ["", "| Unidade | Posto regra | Palavras | IDs de linha (início … fim) |",
           "|---|---:|---:|---|"]
    for uid, z in d["unidades"].items():
        lids = z["linhas"]
        mostra = ", ".join(lids) if len(lids) <= 6 else ", ".join(lids[:3]) + " … " + ", ".join(lids[-3:])
        ls.append(f"| {uid} | {z['posto_regra']} | {z['palavras']} | {mostra} |")
    ls += ["", "A mediana pesa unidades igualmente. A cadeia que junta cabeçalho e o átomo final "
           "fica ancorada nos postos das unidades curtas do topo; ela é emitida inteira antes da outra cadeia. "
           "Assim, `b5`/`b3` passam à frente de `b6`, embora `b6` venha antes na regra. "
           "Os IDs de linha acima mostram a troca de duas grandes faixas do fluxo silver, "
           "não uma reversão literal de todas as linhas. O τ de palavras fica próximo de zero, "
           "mas positivo: a condição estrita `< 0` não detecta esta falha. "
           "Mesmo interpretar o teste nos IDs de unidade não acionaria a proteção nesta página.", "",
           "| Método | τ palavras vs referência | Quebras/pág | Sucessor linhas |", "|---|---:|---:|---:|"]
    for nome, z in d["metricas"].items():
        ls.append(f"| {nome} | {f(z['tau'])} | {f(z['quebras'])} | {f(z['sucessor_linhas'])} |")
    return ls + [""]


def tabelas(co, resumo, nomes):
    ls = [f"## {co} — {'ajuste' if co in o.DESENV else 'externa'}", "",
          "| Método | Páginas / veículos | τ palavras | Quebras/pág | Quebras/1.000 palavras (média / micro) | Fidelidade 12 | Sucessor linhas | Cobertura |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for nome in nomes:
        if nome not in resumo:
            continue
        r = resumo[nome]
        mm = {k: v["media"] for k, v in r["metricas"].items()}
        label = nome + (" (parcial)" if not r["completo"] else "")
        ls.append(f"| {label} | {r['n']} / {r['veiculos']} | {numero(mm['tau'])} | {numero(mm['quebras'])} | "
                  f"{numero(mm['quebras_mil'],3)} / {numero(r['quebras_mil_micro'],3)} | "
                  f"{numero(mm['fid12'])} | {numero(mm['sucessor_linhas'])} | {numero(100*r['cobertura'],1)}% |")
    ls += ["", "### Diferenças pareadas", "",
           "Δ = método − base; melhor/igual/pior usa o sentido de cada métrica. "
           "IC95 reamostra veículos inteiros; Wilcoxon Pratt usa uma média pareada por veículo.", "",
           "| Método | Base | Métrica | n | Δ [IC95 por veículo] | p por veículo | Melhor/igual/pior |",
           "|---|---|---|---:|---:|---:|---:|"]
    candidatos = [n for n in nomes if n not in CONTROLES or n == m.GRAFO]
    for nome in candidatos:
        if nome not in resumo:
            continue
        for base in ("regra", "hibrido67"):
            if base not in resumo[nome]["contrastes"]:
                continue
            for k, d in resumo[nome]["contrastes"][base].items():
                ls.append(f"| {nome} | {base} | {k} | {d['n']} | {intervalo(d)} | "
                          f"{numero(d['wilcoxon_veiculo']['p'])} | {d['melhor']}/{d['igual']}/{d['pior']} |")
    ls += ["", "### Diferenças por veículo", "",
           "| Método | Base | Veículo | Δ quebras/pág | Δτ |", "|---|---|---|---:|---:|"]
    for nome in candidatos:
        if nome not in resumo:
            continue
        for base in ("regra", "hibrido67"):
            if base not in resumo[nome]["contrastes"]:
                continue
            ds = resumo[nome]["contrastes"][base]
            for uf, delta in ds["quebras"]["por_veiculo"].items():
                ls.append(f"| {nome} | {base} | {uf} | {numero(delta)} | {numero(ds['tau']['por_veiculo'][uf])} |")
    ls += ["", "### Reparos e regressões de sucessores de linhas", "",
           "Contagens pareadas por classe; a variante sem salvaguarda é apenas referência.", "",
           "| Método | Base | Classe | Reparos | Regressões |", "|---|---|---|---:|---:|"]
    for nome in candidatos:
        if nome not in resumo:
            continue
        for base, classes in resumo[nome]["pares_sucessor"].items():
            for tipo, z in classes.items():
                ls.append(f"| {nome} | {base} | {tipo} | {z['reparos']} | {z['regressoes']} |")
    ls += ["", "### Corpo sem margens — diagnóstico", "",
           "Projeção pelas margens automáticas da regra, importada do E014; não substitui a referência da página inteira.", "",
           "| Método | n elegível | τ | Quebras/pág | Fidelidade 12 | Sucessor linhas |", "|---|---:|---:|---:|---:|---:|"]
    for nome in nomes:
        if nome in resumo:
            z = resumo[nome]["corpo"]
            ls.append(f"| {nome} | {z['tau']['n']} | {numero(z['tau']['media'])} | {numero(z['quebras']['media'])} | "
                      f"{numero(z['fid12']['media'])} | {numero(z['sucessor_linhas']['media'])} |")
    return ls + [""]


def relatorio(estado):
    an, rs, ver = estado["ancora"], estado["resumos"], estado["veredito"]
    acionamentos = estado["acionamentos"]
    linhas = [f"1. Âncora reproduzida: golden_v4 τ {numero(an['tau'])}; {numero(an['quebras'])} quebras/página.",
              "2. Salvaguarda fixa: τ de palavras mediana × regra < 0, sem referência; acionamentos no ajuste: " +
              "; ".join(f"{co} {len(acionamentos.get(co, []))}" for co in o.DESENV) + "."]
    for i, co in enumerate(o.COORTES[2:], 3):
        if co in rs:
            z = rs[co][CAND]
            linhas.append(f"{i}. {co}: candidato τ {numero(z['metricas']['tau']['media'])}; "
                          f"quebras {numero(z['metricas']['quebras']['media'])}; "
                          f"Δ vs híbrido {intervalo(z['contrastes']['hibrido67']['quebras'])}.")
        else:
            linhas.append(f"{i}. {co}: ainda não aberta/avaliada nesta execução.")
    linhas += ["5. Modelo, mediana e salvaguarda sem novo ajuste; código e hashes congelados antes das externas; combinação só após o veredito.",
               "6. Golden_v3_novo já foi consultado em rodadas anteriores; silver é ruidoso; resultado exploratório; teste cego preservado.", "",
               "**Veredito do candidato (b)+salvaguarda: " + ver["veredito"] + ".**", "",
               "## Protocolo e congelamento", "", f"Situação: {estado['situacao']}. "
               f"Pico RSS {numero(estado['memoria']['pico_rss_mb'],1)} MiB. "
               "CPU, quatro threads, um processo, num_workers=0, sem treino ou GPU.", "",
               "O E014 é importado para reconstruir o grafo E004 e a variante (b), medir cada ordem e resumir. "
               "Não há nova seleção. A salvaguarda usa as palavras de todas as unidades expandidas canonicamente "
               "pela bancada, com a regra como ordem de comparação; não lê a referência. "
               "O τ nos IDs de unidade é guardado apenas para diagnóstico, sem decidir o retorno. "
               "A entrada é embaralhada pelo protocolo com random.Random(f'entrada-{page_id}').", "",
               f"Estatística importada: {b.NBOOT} reamostras, semente {b.SEMENTE}; médias principais por página, "
               "taxas macro por página e micro por palavra explicitadas. RN tem apenas um veículo e IC degenerado; "
               "híbrido RN é parcial nas páginas densas, pois faltam predições LayoutReader nas leves. "
               "As comparações externas exigem o híbrido completo. Valores de p são descritivos.", ""]
    frozen = estado.get("congelamento")
    if frozen:
        linhas += [f"Congelado em {frozen['congelado_em_utc']}; SHA256 do código `{frozen['codigo_sha256']}`; "
                   f"assinatura `{frozen['assinatura']}`. Evidência em `congelamento.json`, "
                   f"`{EXEC.relative_to(OUT).as_posix()}/codigo_congelado.py` e manifesto. "
                   "Qualquer alteração de código/fontes impede retomar as externas.", ""]
    linhas += texto_rn(estado["diagnostico_rn"])
    linhas += ["## Efeito da salvaguarda no conjunto de ajuste", "",
               "| Bancada | Páginas | Acionamentos | Δτ protegido − (b) | Δ quebras protegido − (b) |",
               "|---|---:|---:|---:|---:|"]
    for co in o.DESENV:
        r = rs[co]
        linhas.append(f"| {co} | {r[MED]['n']} | {len(acionamentos[co])} | "
                      f"{numero(r[CAND]['metricas']['tau']['media']-r[MED]['metricas']['tau']['media'])} | "
                      f"{numero(r[CAND]['metricas']['quebras']['media']-r[MED]['metricas']['quebras']['media'])} |")
    linhas.append("")
    for co in o.COORTES:
        if co in rs:
            linhas += tabelas(co, rs[co], NOMES)
    linhas += ["## Acionamentos e quedas catastróficas", "",
               "| Bancada | Acionamentos |", "|---|---:|"]
    for co, ids in acionamentos.items():
        linhas.append(f"| {co} | {len(ids)} |")
    linhas.append("")
    for co, ids in acionamentos.items():
        for z in ids:
            linhas.append(f"- Salvaguarda `{co}/{z['page_id']}`: τ palavras × regra {numero(z['tau'])}.")
    linhas += ["", "Páginas externas com Δτ < −0,5 contra a regra (lista completa):", ""]
    for co in o.COORTES[2:]:
        for nome in (MED, CAND):
            if co not in estado["catastrofes"]:
                linhas.append(f"- {co}/{nome}: pendente.")
                continue
            casos = estado["catastrofes"][co][nome]
            if not casos:
                linhas.append(f"- {co}/{nome}: nenhuma.")
            for z in casos:
                linhas.append(f"- {co}/{nome}: `{z['page_id']}`; Δτ {numero(z['delta_tau'])}; "
                              f"τ palavras × regra {numero(z['salvaguarda']['tau_palavras_vs_regra'])}; "
                              f"acionou: {z['salvaguarda']['acionada']}.")
    linhas += ["", "## Critérios do cartão E015 — candidato (b)+salvaguarda", "",
               "A variante (b) sem proteção é somente referência. O veredito abaixo não usa a combinação exploratória.", ""]
    for co in o.COORTES[2:]:
        if co not in rs:
            continue
        z = rs[co][CAND]
        dq, dt = z["contrastes"]["hibrido67"]["quebras"], z["contrastes"]["regra"]["tau"]
        linhas.append(f"- {co}: Δ quebras vs híbrido {intervalo(dq)}; "
                      f"Δτ vs regra {numero(dt['media'])} (mínimo permitido −0,005000).")
    for item, ok in ver["itens"].items():
        linhas.append(f"- {item}: {'PASSA' if ok else 'FALHA'}.")
    if "catastrofes_sem_salvaguarda" in ver:
        linhas.append(f"- Critério 3: {ver['catastrofes_sem_salvaguarda']} catástrofes sem salvaguarda; "
                      f"{ver['catastrofes_candidato']} no candidato.")
    linhas += ["", "**Veredito: " + ver["veredito"] + ".**", ""]
    if ver["veredito"] == "NÃO GO":
        linhas += ["Pelo critério de abandono prévio, o grafo permanece como resultado exploratório e o "
                   "híbrido 67 permanece finalista. Não se muda o limiar após ver as externas.", ""]
    if estado.get("exploratorio"):
        linhas += ["## Exploratório posterior ao veredito — híbrido 67 com candidato nas densas", "",
                   "LayoutReader até 67 unidades; (b)+salvaguarda acima de 67. Montado exclusivamente "
                   "a partir das mesmas predições/medições já guardadas, depois de persistir o veredito. "
                   "Não é novo candidato selecionado nem reavaliação das páginas.", ""]
        for co in o.COORTES:
            if co in rs:
                linhas += tabelas(co, rs[co], ("hibrido67", EXP))
    linhas += ["## Limitações e reprodução", "",
               "As três bancadas principais são separadas; RN é ajuste adicional. Há sobreposição entre conjuntos, "
               "por isso não se somam as bancadas. Golden_v4 já orientou a regra e golden_v3_novo já foi consultado "
               "em rodadas anteriores. Silver pode ter ordem PDF errada e erro interno aos átomos. A mediana usa "
               "unidades sem ponderação por palavras; a salvaguarda não garante proximidade da referência e "
               "pode deixar passar grandes trocas quando o τ contra a regra fica positivo. O experimento reusa "
               "um único modelo/semente. IC com poucos veículos, especialmente os três do silver, tem precisão "
               "limitada. O corpo sem margens é uma projeção diagnóstica. Não houve inspeção visual de PDF nem "
               "acesso ao teste cego, ao Label Studio ou escrita sob data/.", "",
               "Comando: `venv/Scripts/python.exe -B orquestracao/analises/e015_mediana.py`. "
               "`--etapa ajuste` nunca abre externas; a execução completa retoma caches atômicos por página. "
               "`--conferir` reconstrói os resumos dos caches sem inferência ou nova medição das páginas. "
               "Abertura das externas e veredito anteriores à exploração ficam registrados em JSON.", ""]
    registro = {co+"/"+nome: {"tau": r["metricas"]["tau"]["media"],
                            "quebras": r["metricas"]["quebras"]["media"],
                            "sucessor": r["metricas"]["sucessor_linhas"]["media"]}
                for co, resumo in rs.items() for nome, r in resumo.items()}
    m.exigir(all(v is not None and math.isfinite(v) for z in registro.values() for v in z.values()),
             "Resumo registro tem numero nulo ou nao finito")
    return "\n".join(linhas), registro


def publicar(an, dados, diag, frozen, situacao, exploratorio=False):
    resumos = resumir(dados, exploratorio)
    casos = catastrofes(dados)
    ver = julgar(resumos, casos)
    estado = {"ancora": an, "manifesto": MAN, "diagnostico_rn": diag,
              "congelamento": frozen, "situacao": situacao, "resumos": resumos,
              "catastrofes": casos, "veredito": ver, "exploratorio": exploratorio,
              "memoria": g.medir_memoria(),
              "acionamentos": {co: [{"page_id": r["page_id"], "tau": r["salvaguarda"]["tau_palavras_vs_regra"]}
                                      for r in rows if r["salvaguarda"]["acionada"]]
                               for co, rows in dados.items()}}
    texto, registro = relatorio(estado)
    estado["assinatura_numeros"] = c.digest([resumos, casos, ver, registro])
    m.gravar(EXEC / "estado.json", estado)
    m.gravar(OUT / "RELATORIO.md", texto)
    m.gravar(OUT / "resumo_registro.json", registro)
    m.gravar(OUT / "cache/ultima_execucao.json", {"execucao": EXEC.relative_to(OUT).as_posix(),
                                                "assinatura_numeros": estado["assinatura_numeros"]})
    return estado


def caches():
    dados = {}
    for co in o.COORTES:
        path = EXEC / ("ordem_" + co + ".json")
        if path.exists():
            dados[co] = []
            for pid in b.ler(path):
                o.permitido(pid)
                row = b.ler(EXEC / "avaliacao" / co / (e.ac.chave(pid) + ".json"))
                m.exigir(row["page_id"] == pid, "ID de cache divergente")
                dados[co].append(row)
    return dados


def conferir():
    estado = b.ler(EXEC / "estado.json")
    # JSON normaliza tuplas importadas do E014 para listas.
    m.exigir(c.digest(estado["manifesto"]) == c.digest(MAN), "Manifesto mudou")
    dados = caches()
    if estado["exploratorio"]:
        dados = explorar(dados, b.ler(OUT / "veredito_antes_exploratorio.json")["veredito"])
    resumos = resumir(dados, estado["exploratorio"])
    casos = catastrofes(dados)
    m.exigir(c.digest(resumos) == c.digest(estado["resumos"]), "Resumo nao reproduziu")
    m.exigir(casos == estado["catastrofes"] and julgar(resumos, casos) == estado["veredito"], "Veredito mudou")
    texto, registro = relatorio(estado)
    m.exigir((OUT / "RELATORIO.md").read_text(encoding="utf-8") == texto, "Relatorio divergiu")
    m.exigir(b.ler(OUT / "resumo_registro.json") == registro, "Registro divergiu")
    for rows in dados.values():
        for r in rows:
            m.exigir(all(z["cobertura_palavras"] == 1 for z in r["resultados"].values()), "Cobertura divergiu")
            fonte = r["salvaguarda"]["fonte"]
            m.exigir(r["resultados"][CAND] == r["resultados"][fonte], "Salvaguarda divergiu")
    m.exigir(c.digest([resumos, casos, estado["veredito"], registro]) == estado["assinatura_numeros"],
             "Assinatura de numeros mudou")
    frozen = b.ler(OUT / "congelamento.json")
    m.exigir(frozen["codigo_sha256"] == c.sha(EXEC / "codigo_congelado.py") == c.sha(Path(__file__)),
             "Codigo congelado divergiu")
    abertura = m.ler(OUT / "abertura_externas.json")
    if abertura:
        m.exigir(frozen["congelado_em_utc"] <= abertura["abertas_em_utc"], "Congelamento tardio")
    print("CONFERE: fontes, lacre, codigo congelado, cobertura, caches, criterios, relatorio e registro sem nulos.", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapa", choices=("ajuste", "tudo"), default="tudo")
    ap.add_argument("--max-minutos", type=float, default=0)
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    m.LOCK_SHA, o.PROTEGIDOS = o.ler_lock()
    o.ASSINATURA_LOCK = m.LOCK_SHA
    if args.max_minutos:
        m.PRAZO = time.monotonic() + 60*args.max_minutos
    # ancora e sempre a primeira medicao; nao publica numero novo se falhar.
    an = o.ancora()
    iniciar()
    with m.trava():
        if args.conferir:
            conferir()
            return 0
        m.gravar(EXEC / "manifesto.json", MAN)
        dados, diag, frozen = {}, None, None
        try:
            for co in o.DESENV:
                dados[co] = avaliar(co)
            diag = diagnosticar_rn(dados["validacao_silver"])
            frozen = congelar(an, dados, diag)
            publicar(an, dados, diag, frozen, "Ajuste concluído; salvaguarda congelada antes das externas")
            if args.etapa == "ajuste":
                conferir()
                return 0
            m.exigir(b.ler(OUT / "congelamento.json") == frozen, "Salvaguarda mudou")
            if not (OUT / "abertura_externas.json").exists():
                m.gravar(OUT / "abertura_externas.json", {"assinatura": c.digest(MAN),
                         "codigo_sha256": c.sha(Path(__file__)), "abertas_em_utc": agora(),
                         "congelamento_sha256": c.digest(frozen),
                         "politica": "uma avaliacao por pagina; retomada somente de caches; sem ajuste"})
            for co in o.COORTES[2:]:
                m.exigir(b.ler(OUT / "congelamento.json") == frozen, "Salvaguarda mudou")
                dados[co] = avaliar(co)
                publicar(an, dados, diag, frozen, "Externa concluída com salvaguarda preservada")
            estado = publicar(an, dados, diag, frozen, "Externas completas; veredito anterior à exploração")
            path = OUT / "veredito_antes_exploratorio.json"
            anterior = m.ler(path)
            if anterior:
                m.exigir(anterior["veredito"] == estado["veredito"], "Veredito anterior mudou")
            else:
                m.gravar(path, {"veredito": estado["veredito"], "registrado_em_utc": agora(),
                               "assinatura_numeros": estado["assinatura_numeros"]})
            explorado = explorar(dados, estado["veredito"])
            publicar(an, explorado, diag, frozen, "Execução completa; exploração posterior ao veredito", True)
            conferir()
            print("VEREDITO E015: " + estado["veredito"]["veredito"], flush=True)
        except (TimeoutError, KeyboardInterrupt) as ex:
            if diag is not None and all(co in dados for co in o.DESENV):
                publicar(an, dados, diag, frozen, "PARCIAL retomável: " + str(ex))
            print("PARCIAL: " + str(ex), flush=True)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
