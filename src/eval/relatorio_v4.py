"""
Relatório consolidado da avaliação do Golden v4 e comparação com Golden v3.

Analisa a ordem de leitura humana anotada sobre as regiões corrigidas à mão no
Diamond (golden_v4, 44 páginas concluídas) comparada à anotação sobre blocos do
extrator v3 (_avaliacao/golden_v3, 47 páginas).

Gera docs/RELATORIO_V4.md e exporta dados e funções para
notebooks/relatorio_ordem_v4.ipynb.
"""
from __future__ import annotations

import os
import sys
import glob
import json
import random
import statistics
from collections import Counter
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.stats import wilcoxon

# Ajuste de caminho para importar src
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src.eval.protocolo import ordem_entrada  # noqa: E402
from src.eval.metrics import avaliar, kendall_tau  # noqa: E402

DIR_DATA = os.path.join(RAIZ, "data")
DIR_RESULTADOS = os.path.join(RAIZ, "resultados")
DIR_DOCS = os.path.join(RAIZ, "docs")
DIR_FIGURAS = os.path.join(DIR_DOCS, "figuras")

NOMES = {
    "fluxo_pdf": "Fluxo do PDF (referência silver)",
    "aleatoria": "Ordem do detector (entrada embaralhada)",
    "naive": "Ingênua (topo→base, esq.→dir.)",
    "xycut": "XY-cut (heurística de colunas)",
    "layoutlm": "LayoutLM pontual (semente 42)",
    "pontual_seed1": "LayoutLM pontual (semente 1)",
    "pontual_seed2": "LayoutLM pontual (semente 2)",
    "layoutlm_sem_layout": "LayoutLM pontual sem layout",
    "layoutlm_sucessor": "LayoutLM sucessor (semente 42)",
    "sucessor_seed1": "LayoutLM sucessor (semente 1)",
    "sucessor_seed2": "LayoutLM sucessor (semente 2)",
    "ablacao_suc_sem_vies_geo": "LayoutLM suc. sem viés geom.",
    "ablacao_suc_sem_posicao": "LayoutLM suc. sem posição",
    "ablacao_suc_sem_layout": "LayoutLM suc. sem layout",
    "ablacao_suc_sem_texto": "LayoutLM suc. sem texto",
    "vlm_gemini_3_1_flash_lite": "VLM Gemini 3.1 Flash Lite (com marcas)",
    "vlm_gemini_3_1_flash_lite_sem_classes": "VLM Gemini 3.1 Flash Lite (sem classes)",
    "vlm_gemini_3_1_flash_lite_sem_marcas": "VLM Gemini 3.1 Flash Lite (sem marcas)",
    "llm_gemma4_31b": "LLM Gemma 4 31B (zero-shot)",
    "llm_gemma4_31b_fs2": "LLM Gemma 4 31B (few-shot 2)",
    "llm_qwen3_6_35b": "LLM Qwen 3.6 35B (zero-shot)",
    "llm_qwen3_6_35b_fs2": "LLM Qwen 3.6 35B (few-shot 2)",
    "llm_qwen3_8_27b": "LLM Qwen 3.8 27B (zero-shot)",
    "llm_qwen3_8_27b_fs2": "LLM Qwen 3.8 27B (few-shot 2)",
}


def virgula(x: float | None, casas: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{casas}f}".replace(".", ",")


def pct_virgula(x: float | None, casas: int = 1) -> str:
    if x is None:
        return "—"
    return f"{x * 100:.{casas}f}%".replace(".", ",")


def nome_metodo(m: str) -> str:
    return NOMES.get(m, m)


def ler_jsonl(caminho: str) -> List[Dict[str, Any]]:
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def bootstrap_ic95(v: List[float], reamostras: int = 2000, semente: int = 7) -> Tuple[float, float]:
    if len(v) < 2:
        return (v[0], v[0]) if v else (0.0, 0.0)
    rng = random.Random(semente)
    medias = sorted(sum(rng.choices(v, k=len(v))) / len(v) for _ in range(reamostras))
    return medias[int(0.025 * reamostras)], medias[int(0.975 * reamostras)]


def carregar_lote(lote_nome: str):
    dir_lote = os.path.join(DIR_DATA, "golden", lote_nome)
    tarefas_lista = ler_jsonl(os.path.join(dir_lote, "tarefas.jsonl"))
    tarefas = {t["page_id"]: t for t in tarefas_lista}

    arq_ref = os.path.join(dir_lote, "referencia.jsonl")
    if not os.path.exists(arq_ref):
        arq_ref = os.path.join(dir_lote, "anotacoes.jsonl")
    anot_todas = ler_jsonl(arq_ref)
    anot_concluidas = [x for x in anot_todas if x.get("status") == "concluida"]
    anot_puladas = [x for x in anot_todas if x.get("status") == "pulada"]

    contagem = Counter(x["anotador"] for x in anot_concluidas)
    anotador_principal = contagem.most_common(1)[0][0] if contagem else "anotador"
    humano = {x["page_id"]: x for x in anot_concluidas if x["anotador"] == anotador_principal}

    paginas = [tarefas[pid] for pid in humano if pid in tarefas]

    dir_pred = os.path.join(DIR_RESULTADOS, "golden", lote_nome)
    preds: Dict[str, Dict[str, List[str]]] = {
        "fluxo_pdf": {p["page_id"]: p["ordens"]["stream"] for p in paginas},
        "aleatoria": {p["page_id"]: [p["bounding_boxes"][i]["id"] for i in ordem_entrada(p)] for p in paginas},
        "naive": {p["page_id"]: p["ordens"]["naive"] for p in paginas},
        "xycut": {p["page_id"]: p["ordens"]["xycut"] for p in paginas},
    }

    pred_metadados: Dict[str, Dict[str, Any]] = {}
    for arq in sorted(glob.glob(os.path.join(dir_pred, "pred_*.jsonl"))):
        m = os.path.basename(arq)[5:-6]
        linhas = ler_jsonl(arq)
        preds[m] = {l["page_id"]: l["ordem_pred"] for l in linhas}
        pred_metadados[m] = {l["page_id"]: l for l in linhas}
        if linhas and linhas[0].get("modelo"):
            mod = linhas[0]["modelo"]
            fs = linhas[0].get("few_shot") or 0
            if m not in NOMES:
                NOMES[m] = f"LLM {mod} ({f'few-shot, {fs} exemplos' if fs else 'zero-shot'})"

    return {
        "lote": lote_nome,
        "tarefas": tarefas,
        "humano": humano,
        "paginas": paginas,
        "anot_concluidas": anot_concluidas,
        "anot_puladas": anot_puladas,
        "anotador": anotador_principal,
        "preds": preds,
        "pred_metadados": pred_metadados,
    }


def calcular_metricas_base(dados_lote):
    paginas = dados_lote["paginas"]
    humano = dados_lote["humano"]
    preds = dados_lote["preds"]
    pred_meta = dados_lote["pred_metadados"]

    regs_por_metodo: Dict[str, List[Dict[str, Any]]] = {m: [] for m in preds}
    for p in paginas:
        pid = p["page_id"]
        ref = humano[pid]["ordem"]
        for m, pred_dict in preds.items():
            if pid in pred_dict:
                r = avaliar(pred_dict[pid], ref)
                valida = None
                tempo_ms = None
                if m in pred_meta and pid in pred_meta[m]:
                    valida = pred_meta[m][pid].get("permutacao_valida")
                    tempo_ms = pred_meta[m][pid].get("tempo_ms")
                elif m in ("fluxo_pdf", "aleatoria", "naive", "xycut") or "layoutlm" in m or "pontual" in m or "sucessor" in m or "ablacao" in m:
                    valida = True

                r.update({
                    "page_id": pid,
                    "grupo": p.get("grupo"),
                    "uf": p.get("uf"),
                    "n_colunas": p.get("stats", {}).get("n_colunas", 1),
                    "n_tabelas": p.get("stats", {}).get("n_tabelas", 0),
                    "permutacao_valida": valida,
                    "tempo_ms": tempo_ms,
                })
                regs_por_metodo[m].append(r)

    regs_por_metodo = {m: v for m, v in regs_por_metodo.items() if v}
    return regs_por_metodo


def tabela_golden_v4(regs_v4, dados_v4):
    resumo_v4 = []
    for m, regs in regs_v4.items():
        taus = [r["kendall_tau"] for r in regs]
        sucs = [r["acerto_sucessor"] for r in regs]
        ards = [r["ard_norm"] for r in regs]
        exatos = [r["acerto_exato"] for r in regs]
        s_taus = sorted(taus)

        ic = bootstrap_ic95(taus)
        med = statistics.median(taus)
        p10 = s_taus[int(0.10 * len(s_taus))]

        # Permutações válidas
        validas = [r["permutacao_valida"] for r in regs if r["permutacao_valida"] is not None]
        if validas:
            n_val = sum(1 for v in validas if v is True)
            pct_val = n_val / len(validas)
            str_validas = f"{n_val}/{len(validas)} ({pct_val:.1%})"
        else:
            str_validas = f"{len(regs)}/{len(regs)} (100%)"

        resumo_v4.append({
            "metodo": m,
            "nome": nome_metodo(m),
            "n": len(regs),
            "tau": statistics.mean(taus),
            "tau_ic95": ic,
            "mediana": med,
            "p10": p10,
            "sucessor": statistics.mean(sucs),
            "ard_norm": statistics.mean(ards),
            "exato": statistics.mean(exatos),
            "validas_str": str_validas,
        })

    resumo_v4.sort(key=lambda x: x["tau"], reverse=True)

    # Estatísticas de sementes LayoutLM
    sementes_pontual = [r for r in resumo_v4 if r["metodo"] in ("layoutlm", "pontual_seed1", "pontual_seed2")]
    sementes_sucessor = [r for r in resumo_v4 if r["metodo"] in ("layoutlm_sucessor", "sucessor_seed1", "sucessor_seed2")]

    def calc_seeds(sems):
        if not sems:
            return None
        taus = [s["tau"] for s in sems]
        sucs = [s["sucessor"] for s in sems]
        ards = [s["ard_norm"] for s in sems]
        exatos = [s["exato"] for s in sems]
        return {
            "tau_mean": statistics.mean(taus),
            "tau_std": statistics.stdev(taus) if len(taus) > 1 else 0.0,
            "suc_mean": statistics.mean(sucs),
            "suc_std": statistics.stdev(sucs) if len(sucs) > 1 else 0.0,
            "ard_mean": statistics.mean(ards),
            "ard_std": statistics.stdev(ards) if len(ards) > 1 else 0.0,
            "exato_mean": statistics.mean(exatos),
            "exato_std": statistics.stdev(exatos) if len(exatos) > 1 else 0.0,
        }

    seeds_pontual = calc_seeds(sementes_pontual)
    seeds_sucessor = calc_seeds(sementes_sucessor)

    return resumo_v4, seeds_pontual, seeds_sucessor


def calcular_wilcoxon_holm(regs_v4):
    tx = {r["page_id"]: r["kendall_tau"] for r in regs_v4["xycut"]}
    testes = []
    for m, regs in regs_v4.items():
        if m == "xycut":
            continue
        tm = {r["page_id"]: r["kendall_tau"] for r in regs}
        comuns = sorted(set(tx) & set(tm))
        if len(comuns) >= 6:
            v_xy = [tx[i] for i in comuns]
            v_m = [tm[i] for i in comuns]
            diff = [b - a for a, b in zip(v_xy, v_m)]
            try:
                res = wilcoxon(v_xy, v_m)
                p_valor = float(res.pvalue)
            except Exception:
                p_valor = 1.0
            testes.append({
                "metodo": m,
                "nome": nome_metodo(m),
                "n": len(comuns),
                "diff_media": statistics.mean(diff),
                "p_valor": p_valor,
            })

    testes.sort(key=lambda x: x["p_valor"])
    M = len(testes)

    p_adj_max = 0.0
    for i, t in enumerate(testes):
        k = i + 1
        limiar = 0.05 / (M - k + 1)
        p_ajustado = min(1.0, (M - k + 1) * t["p_valor"])
        p_adj_max = max(p_adj_max, p_ajustado)
        t["rank"] = k
        t["limiar_holm"] = limiar
        t["p_ajustado"] = min(1.0, p_adj_max)
        t["significativo"] = t["p_valor"] <= limiar

        if t["significativo"]:
            if t["diff_media"] > 0:
                t["interpretacao"] = "Superior à XY-cut (p < limiar Holm)"
            else:
                t["interpretacao"] = "Inferior à XY-cut (p < limiar Holm)"
        else:
            t["interpretacao"] = "Sem diferença significativa"

    return testes


def calcular_efeito_segmentacao(regs_v3, regs_v4, dados_v3, dados_v4):
    pids_v3 = set(dados_v3["humano"].keys())
    pids_v4 = set(dados_v4["humano"].keys())
    comuns = sorted(pids_v3 & pids_v4)

    metodos = sorted(set(regs_v3.keys()) | set(regs_v4.keys()))
    tabela = []

    for m in metodos:
        if m.startswith("llm_qwen3_6"):
            continue
        if m not in regs_v3 or m not in regs_v4:
            tabela.append({
                "metodo": m,
                "nome": nome_metodo(m),
                "presente": False,
                "motivo": "Ausente no golden_v3" if m not in regs_v3 else "Ausente no golden_v4",
            })
            continue

        d3_tau = {r["page_id"]: r["kendall_tau"] for r in regs_v3[m]}
        d4_tau = {r["page_id"]: r["kendall_tau"] for r in regs_v4[m]}
        d3_suc = {r["page_id"]: r["acerto_sucessor"] for r in regs_v3[m]}
        d4_suc = {r["page_id"]: r["acerto_sucessor"] for r in regs_v4[m]}

        pags_ambos = [p for p in comuns if p in d3_tau and p in d4_tau]
        if not pags_ambos:
            continue

        t3 = [d3_tau[p] for p in pags_ambos]
        t4 = [d4_tau[p] for p in pags_ambos]
        s3 = [d3_suc[p] for p in pags_ambos]
        s4 = [d4_suc[p] for p in pags_ambos]

        try:
            p_tau = float(wilcoxon(t3, t4).pvalue)
        except Exception:
            p_tau = 1.0
        try:
            p_suc = float(wilcoxon(s3, s4).pvalue)
        except Exception:
            p_suc = 1.0

        tabela.append({
            "metodo": m,
            "nome": nome_metodo(m),
            "presente": True,
            "n": len(pags_ambos),
            "tau_v3": statistics.mean(t3),
            "tau_v4": statistics.mean(t4),
            "diff_tau": statistics.mean(t4) - statistics.mean(t3),
            "p_tau": p_tau,
            "suc_v3": statistics.mean(s3),
            "suc_v4": statistics.mean(s4),
            "diff_suc": statistics.mean(s4) - statistics.mean(s3),
            "p_suc": p_suc,
        })

    return comuns, tabela


def calcular_cortes_pagina(regs_v4, regs_v3):
    # LLM fixa: melhor no geral no golden_v4 (Qwen 3.8 27B few-shot 2)
    llm_fixa_v4 = "llm_qwen3_8_27b_fs2"
    if llm_fixa_v4 not in regs_v4:
        llms_v4 = [m for m in regs_v4 if m.startswith("llm_")]
        llm_fixa_v4 = max(llms_v4, key=lambda m: statistics.mean(r["kendall_tau"] for r in regs_v4[m])) if llms_v4 else None

    llms_v3 = [m for m in regs_v3 if m.startswith("llm_")]
    melhor_llm_v3 = max(llms_v3, key=lambda m: statistics.mean(r["kendall_tau"] for r in regs_v3[m])) if llms_v3 else None

    grupos_col = {"1 coluna": [], "2 colunas": [], "3+ colunas": []}
    grupos_tab = {"Sem tabela": [], "Com tabela": []}

    uma_lista = regs_v4["xycut"]
    for r in uma_lista:
        pid = r["page_id"]
        c = r["n_colunas"]
        g_col = "3+ colunas" if c >= 3 else ("2 colunas" if c == 2 else "1 coluna")
        grupos_col[g_col].append(pid)

        g_tab = "Com tabela" if r["n_tabelas"] > 0 else "Sem tabela"
        grupos_tab[g_tab].append(pid)

    def extrair_taus(pids, m):
        if m not in regs_v4:
            return None
        d = {r["page_id"]: r["kendall_tau"] for r in regs_v4[m]}
        vals = [d[p] for p in pids if p in d]
        return statistics.mean(vals) if vals else None

    res_cortes = []
    for cat in ["1 coluna", "2 colunas", "3+ colunas"]:
        pids = grupos_col[cat]
        linha = {
            "categoria": cat,
            "tipo": "Colunas",
            "n": len(pids),
            "xycut": extrair_taus(pids, "xycut"),
            "layoutlm_sucessor": extrair_taus(pids, "layoutlm_sucessor"),
            "vlm_com_marcas": extrair_taus(pids, "vlm_gemini_3_1_flash_lite"),
            "llm": extrair_taus(pids, llm_fixa_v4) if llm_fixa_v4 else None,
            "llm_nome": nome_metodo(llm_fixa_v4) if llm_fixa_v4 else None,
        }
        res_cortes.append(linha)

    for cat in ["Sem tabela", "Com tabela"]:
        pids = grupos_tab[cat]
        linha = {
            "categoria": cat,
            "tipo": "Tabela",
            "n": len(pids),
            "xycut": extrair_taus(pids, "xycut"),
            "layoutlm_sucessor": extrair_taus(pids, "layoutlm_sucessor"),
            "vlm_com_marcas": extrair_taus(pids, "vlm_gemini_3_1_flash_lite"),
            "llm": extrair_taus(pids, llm_fixa_v4) if llm_fixa_v4 else None,
            "llm_nome": nome_metodo(llm_fixa_v4) if llm_fixa_v4 else None,
        }
        res_cortes.append(linha)

    return res_cortes, llm_fixa_v4, melhor_llm_v3


def calcular_vlm_detalhado(regs_v4, dados_v4, regs_v3=None):
    m_com = "vlm_gemini_3_1_flash_lite"
    m_sc = "vlm_gemini_3_1_flash_lite_sem_classes"
    m_sm = "vlm_gemini_3_1_flash_lite_sem_marcas"

    def extrair_info_vlm(m):
        regs = regs_v4.get(m, [])
        taus = [r["kendall_tau"] for r in regs]
        sucs = [r["acerto_sucessor"] for r in regs]
        validas = [r["permutacao_valida"] for r in regs if r["permutacao_valida"] is not None]
        tempos = [r["tempo_ms"] / 1000.0 for r in regs if r.get("tempo_ms") is not None]
        n_val = sum(1 for v in validas if v is True)
        return {
            "n": len(regs),
            "tau": statistics.mean(taus) if taus else 0.0,
            "tau_ic95": bootstrap_ic95(taus) if taus else (0.0, 0.0),
            "sucessor": statistics.mean(sucs) if sucs else 0.0,
            "validas_cnt": n_val,
            "validas_total": len(validas),
            "validas_pct": n_val / len(validas) if validas else 1.0,
            "segundos_por_pagina": statistics.mean(tempos) if tempos else 0.0,
        }

    tc = [r["kendall_tau"] for r in regs_v4.get(m_com, [])]
    tsc = [r["kendall_tau"] for r in regs_v4.get(m_sc, [])]
    diff_classes = (statistics.mean(tc) - statistics.mean(tsc)) if (tc and tsc) else 0.0
    try:
        p_wilcoxon_classes = float(wilcoxon(tc, tsc).pvalue) if (tc and tsc) else 1.0
    except Exception:
        p_wilcoxon_classes = 1.0

    d_com = {r["page_id"]: r["kendall_tau"] for r in regs_v4.get(m_com, [])}
    d_sm = {r["page_id"]: r["kendall_tau"] for r in regs_v4.get(m_sm, [])}
    comuns_marcas = sorted(set(d_com) & set(d_sm))
    if comuns_marcas:
        v_com = [d_com[p] for p in comuns_marcas]
        v_sm = [d_sm[p] for p in comuns_marcas]
        diff_marcas = statistics.mean(v_com) - statistics.mean(v_sm)
        try:
            p_wilcoxon_marcas = float(wilcoxon(v_com, v_sm).pvalue)
        except Exception:
            p_wilcoxon_marcas = 1.0
    else:
        diff_marcas = 0.0
        p_wilcoxon_marcas = 1.0

    tau_vlm_v3 = None
    suc_vlm_v3 = None
    if regs_v3 and m_com in regs_v3:
        tau_vlm_v3 = statistics.mean(r["kendall_tau"] for r in regs_v3[m_com])
        suc_vlm_v3 = statistics.mean(r["acerto_sucessor"] for r in regs_v3[m_com])

    comp_vlm = {
        "com_marcas_classes": extrair_info_vlm(m_com),
        "com_marcas_sem_classes": extrair_info_vlm(m_sc),
        "sem_marcas_classes": extrair_info_vlm(m_sm),
        "diff_classes": diff_classes,
        "p_wilcoxon_classes": p_wilcoxon_classes,
        "diff_marcas": diff_marcas,
        "p_wilcoxon_marcas": p_wilcoxon_marcas,
        "tau_vlm_v3": tau_vlm_v3,
        "suc_vlm_v3": suc_vlm_v3,
    }

    regs_com = regs_v4.get(m_com, [])
    ordenados = sorted(regs_com, key=lambda r: r["kendall_tau"])
    piores5 = []
    for r in ordenados[:5]:
        pid = r["page_id"]
        p_tarefa = dados_v4["tarefas"].get(pid, {})
        n_blocos = len(p_tarefa.get("bounding_boxes", []))
        meta = dados_v4["pred_metadados"].get(m_com, {}).get(pid, {})
        rotulos_dev = meta.get("n_rotulos_devolvidos")
        if rotulos_dev is None and "ordem_pred" in meta:
            rotulos_dev = len(meta["ordem_pred"])
        piores5.append({
            "page_id": pid,
            "n_blocos": n_blocos,
            "colunas": r["n_colunas"],
            "tabelas": r["n_tabelas"],
            "permutacao_valida": r["permutacao_valida"],
            "rotulos_devolvidos": rotulos_dev,
            "tau": r["kendall_tau"],
            "sucessor": r["acerto_sucessor"],
        })

    return comp_vlm, piores5


def calcular_layoutlm_dominio(regs_v3, regs_v4, efeito_seg):
    modelos = [
        ("LayoutLM Pontual (semente 42)", "layoutlm"),
        ("LayoutLM Pontual (semente 1)", "pontual_seed1"),
        ("LayoutLM Pontual (semente 2)", "pontual_seed2"),
        ("LayoutLM Sucessor (semente 42)", "layoutlm_sucessor"),
        ("LayoutLM Sucessor (semente 1)", "sucessor_seed1"),
        ("LayoutLM Sucessor (semente 2)", "sucessor_seed2"),
    ]

    tabela_dominio = []
    for rotulo, m in modelos:
        t3 = statistics.mean(r["kendall_tau"] for r in regs_v3[m])
        t4 = statistics.mean(r["kendall_tau"] for r in regs_v4[m])
        queda_abs = t4 - t3
        queda_rel = (t4 - t3) / t3

        s3 = statistics.mean(r["acerto_sucessor"] for r in regs_v3[m])
        s4 = statistics.mean(r["acerto_sucessor"] for r in regs_v4[m])
        queda_suc_abs = s4 - s3
        queda_suc_rel = (s4 - s3) / s3

        tabela_dominio.append({
            "modelo": rotulo,
            "metodo": m,
            "tau_v3": t3,
            "tau_v4": t4,
            "queda_rel": queda_rel,
            "queda_abs": queda_abs,
            "suc_v3": s3,
            "suc_v4": s4,
            "queda_suc_abs": queda_suc_abs,
            "queda_suc_rel": queda_suc_rel,
        })

    def media_form(sub_mets):
        v3_t = [t["tau_v3"] for t in tabela_dominio if t["metodo"] in sub_mets]
        v4_t = [t["tau_v4"] for t in tabela_dominio if t["metodo"] in sub_mets]
        m3, m4 = statistics.mean(v3_t), statistics.mean(v4_t)
        return m3, m4, (m4 - m3) / m3

    pont_v3, pont_v4, pont_queda = media_form(["layoutlm", "pontual_seed1", "pontual_seed2"])
    suc_v3, suc_v4, suc_queda = media_form(["layoutlm_sucessor", "sucessor_seed1", "sucessor_seed2"])

    return tabela_dominio, (pont_v3, pont_v4, pont_queda), (suc_v3, suc_v4, suc_queda)


def carregar_resultados_diamond():
    caminho_piloto = os.path.join(DIR_RESULTADOS, "diamond", "diamond_piloto", "avaliacao.json")
    caminho_treino = os.path.join(DIR_RESULTADOS, "diamond", "diamond_treino", "avaliacao.json")

    piloto = json.load(open(caminho_piloto, encoding="utf-8")) if os.path.exists(caminho_piloto) else {}
    treino = json.load(open(caminho_treino, encoding="utf-8")) if os.path.exists(caminho_treino) else {}
    return piloto, treino


def calcular_custos_humanos(dados_v4, dados_v3):
    arquivos = {
        "golden_v2": ("Golden v2 (ordem sobre blocos v3)", os.path.join(DIR_DATA, "golden", "golden_v2", "anotacoes.jsonl")),
        "golden_v4": ("Golden v4 (ordem sobre regiões Diamond)", os.path.join(DIR_DATA, "golden", "golden_v4", "anotacoes.jsonl")),
        "diamond_piloto": ("Diamond piloto (caixas e classes)", os.path.join(DIR_DATA, "diamond", "diamond_piloto", "anotacoes.jsonl")),
        "diamond_treino": ("Diamond treino (caixas e classes)", os.path.join(DIR_DATA, "diamond", "diamond_treino", "anotacoes.jsonl")),
    }

    tabela_custo = []
    for chave, (rotulo, arq) in arquivos.items():
        linhas = ler_jsonl(arq)
        concluidas = [l for l in linhas if l.get("status") == "concluida"]
        puladas = [l for l in linhas if l.get("status") == "pulada"]
        tempos = [c["tempo_s"] for c in concluidas if c.get("tempo_s") is not None]

        n_elementos = []
        for c in concluidas:
            if "ordem" in c:
                n_elementos.append(len(c["ordem"]))
            elif "regioes" in c:
                n_elementos.append(len(c["regioes"]))

        total_s = sum(tempos)
        med_s = statistics.median(tempos) if tempos else 0.0
        media_s = statistics.mean(tempos) if tempos else 0.0
        media_elem = (total_s / sum(n_elementos)) if n_elementos and sum(n_elementos) > 0 else 0.0

        tabela_custo.append({
            "chave": chave,
            "rotulo": rotulo,
            "n_concluidas": len(concluidas),
            "n_puladas": len(puladas),
            "total_min": total_s / 60.0,
            "mediana_s": med_s,
            "media_s": media_s,
            "media_por_elem_s": media_elem,
        })

    # Familiaridade no golden_v4 (20 comuns com golden_v3 vs 24 novas)
    pids_v3 = set(dados_v3["humano"].keys())
    concluidas_v4 = dados_v4["anot_concluidas"]
    tempos_20 = [c["tempo_s"] for c in concluidas_v4 if c["page_id"] in pids_v3 and c.get("tempo_s") is not None]
    tempos_24 = [c["tempo_s"] for c in concluidas_v4 if c["page_id"] not in pids_v3 and c.get("tempo_s") is not None]
    tempos_tot = [c["tempo_s"] for c in concluidas_v4 if c.get("tempo_s") is not None]

    familiaridade = {
        "n_comuns": len(tempos_20),
        "mediana_comuns_s": statistics.median(tempos_20) if tempos_20 else 0.0,
        "media_comuns_s": statistics.mean(tempos_20) if tempos_20 else 0.0,
        "total_comuns_min": sum(tempos_20) / 60.0 if tempos_20 else 0.0,
        "n_novas": len(tempos_24),
        "mediana_novas_s": statistics.median(tempos_24) if tempos_24 else 0.0,
        "media_novas_s": statistics.mean(tempos_24) if tempos_24 else 0.0,
        "total_novas_min": sum(tempos_24) / 60.0 if tempos_24 else 0.0,
        "n_total": len(tempos_tot),
        "mediana_total_s": statistics.median(tempos_tot) if tempos_tot else 0.0,
        "media_total_s": statistics.mean(tempos_tot) if tempos_tot else 0.0,
        "total_min": sum(tempos_tot) / 60.0 if tempos_tot else 0.0,
    }

    return {
        "tabela": tabela_custo,
        "familiaridade": familiaridade,
    }


def carregar_execucoes_llm() -> List[Dict[str, Any]]:
    arq = os.path.join(DIR_RESULTADOS, "golden", "golden_v4", "execucoes_llm.jsonl")
    return ler_jsonl(arq)


def formatar_markdown(
    resumo_v4, seeds_pont, seeds_suc, testes_wilcoxon, comuns_20,
    efeito_seg, cortes_pag, melhor_llm_v4, melhor_llm_v3,
    comp_vlm, piores5_vlm, tab_dominio, pont_resumo, suc_resumo,
    diam_piloto, diam_treino, custos_humanos, execucoes_llm
) -> str:
    md = []
    w = md.append

    w("# Relatório de Avaliação — Golden v4 e Comparação de Segmentação")
    w("")
    w("> Relatório técnico consolidado da ordem de leitura humana no `golden_v4` (regiões Diamond)")
    w("> confrontada com o `golden_v3` (blocos automáticos v3), testes de hipóteses, sensibilidade")
    w("> e medições de segmentação e esforço humano.")
    w("")

    # 1. RESUMO
    w("## 1. Resumo Executivo")
    w("")
    vlm_cc = comp_vlm["com_marcas_classes"]
    vlm_sc = comp_vlm["com_marcas_sem_classes"]
    vlm_sm = comp_vlm["sem_marcas_classes"]
    diff_classes = comp_vlm["diff_classes"]
    p_classes = comp_vlm["p_wilcoxon_classes"]
    p_marcas = comp_vlm["p_wilcoxon_marcas"]
    tau_v3 = comp_vlm["tau_vlm_v3"]
    suc_v3 = comp_vlm["suc_vlm_v3"]
    fam = custos_humanos["familiaridade"]

    llm_melhor_obj = [r for r in resumo_v4 if r["metodo"] == melhor_llm_v4][0] if melhor_llm_v4 else None

    w(f"1. O lote `golden_v4` possui **{resumo_v4[0]['n']} páginas concluídas** (1 pulada) anotadas por especialista humano sobre as regiões refinadas manualmente no Diamond.")
    w(f"2. O modelo multimodal **Gemini 3.1 Flash Lite lidera o ranking global**: a configuração **com marcas, sem classes** atingiu **τ = {virgula(vlm_sc['tau'], 3)}** (IC 95%: {virgula(vlm_sc['tau_ic95'][0], 3)}–{virgula(vlm_sc['tau_ic95'][1], 3)}; {pct_virgula(vlm_sc['sucessor'], 1)} de sucessor; {vlm_sc['validas_cnt']}/{vlm_sc['validas_total']} permutações válidas, {pct_virgula(vlm_sc['validas_pct'], 1)}) e a configuração **com marcas e classes** obteve **τ = {virgula(vlm_cc['tau'], 3)}** (IC 95%: {virgula(vlm_cc['tau_ic95'][0], 3)}–{virgula(vlm_cc['tau_ic95'][1], 3)}; {pct_virgula(vlm_cc['sucessor'], 1)} de sucessor; {vlm_cc['validas_cnt']}/{vlm_cc['validas_total']} válidas, {pct_virgula(vlm_cc['validas_pct'], 1)}).")
    w(f"3. **Não há efeito mensurável das classes humanas no prompt do VLM**: a diferença de τ entre a versão com classes e sem classes é de apenas **{virgula(diff_classes, 3)}** (Wilcoxon pareado p = {virgula(p_classes, 3)}, sem significância estatística). Além disso, no `golden_v3` (onde o prompt não recebia classes humanas, apenas anotação de tabelas pelo detector), o VLM com marcas já alcançava **τ = {virgula(tau_v3, 3)}** ({pct_virgula(suc_v3, 1)} de sucessor). As **marcas visuais sobre a imagem (Set-of-Mark)** têm efeito medido: sem marcas visuais, o τ recua de {virgula(vlm_cc['tau'], 3)} para {virgula(vlm_sm['tau'], 3)} (Wilcoxon pareado p = {virgula(p_marcas, 4)}), o acerto de sucessor cai de {pct_virgula(vlm_cc['sucessor'], 1)} para {pct_virgula(vlm_sm['sucessor'], 1)} e as permutações válidas caem de {vlm_cc['validas_cnt']} para {vlm_sm['validas_cnt']} de {vlm_sm['validas_total']} ({pct_virgula(vlm_cc['validas_pct'], 1)} → {pct_virgula(vlm_sm['validas_pct'], 1)}). Mesmo sem marcas, o VLM ainda supera a XY-cut após Holm.")
    if llm_melhor_obj:
        w(f"4. As **LLMs de texto** (Qwen 3.8 27B e Gemma 4 31B), avaliadas no Kaggle sobre 2× Tesla T4, recebem exclusivamente texto e coordenadas normalizadas (sem classes e sem imagem). A melhor LLM foi a **{llm_melhor_obj['nome']}**, com **τ = {virgula(llm_melhor_obj['tau'], 3)}**, {pct_virgula(llm_melhor_obj['sucessor'], 1)} de sucessor correto e {llm_melhor_obj['validas_str']} permutações válidas, ficando abaixo do VLM com marcas (τ = {virgula(vlm_cc['tau'], 3)}).")
    w(f"5. Entre os modelos locais e LLMs, embora o **LayoutLM sucessor (semente 42)** (τ = 0,890; média das 3 sementes: τ = {virgula(seeds_suc['tau_mean'], 3)} ± {virgula(seeds_suc['tau_std'], 3)}, sucessor {pct_virgula(seeds_suc['suc_mean'], 1)}) e a melhor LLM de texto ({llm_melhor_obj['nome'] if llm_melhor_obj else 'Qwen 3.8 27B fs2'}, τ = {virgula(llm_melhor_obj['tau'], 3) if llm_melhor_obj else '0,876'}) apresentem τ médio numericamente superior à heurística XY-cut (τ = 0,825, sucessor 71,5%), **a diferença não é estatisticamente significativa** após correção de comparações múltiplas por Holm-Bonferroni (p ajustado = 1,00 e 0,92, respectivamente; p bruto = 0,183 e 0,077).")
    w(f"6. Nos testes pareados de Wilcoxon com correção de Holm contra a XY-cut (21 comparações), **apenas as três configurações do VLM obtiveram superioridade estatisticamente significante** (com marcas e classes: p = 5,43e-06; com marcas, sem classes: p = 9,76e-06; sem marcas, com classes: p = 1,98e-04). Nenhuma formulação do LayoutLM, nenhuma das quatro LLMs e nem a ordem ingênua apresentaram diferença significante frente à XY-cut.")
    w(f"7. Nas **20 páginas comuns** entre `golden_v3` e `golden_v4`, o τ do LayoutLM sucessor permaneceu estável (+0,003, p = 0,981), porém a continuidade local sofreu queda de **-10,1 pontos percentuais** no sucessor correto (68,3% → 58,3%, p = 0,055). As LLMs de texto também apresentaram redução de τ nas 20 páginas (Qwen 3.8 27B fs2: 0,932 → 0,845, Δ = -0,087), mas a queda não é estatisticamente significativa (p = 0,121).")
    w(f"8. O custo humano ativo para anotar a ordem sobre as regiões Diamond no `golden_v4` teve mediana de **{virgula(fam['mediana_total_s'], 1)} s/página** (total de {virgula(fam['total_min'], 1)} min para as 44 páginas). Trata-se de tarefas diferentes da retificação geométrica de caixas e rotulagem de classes no Diamond, com tempo menor (4 a 6 vezes mais rápido que a mediana de 98,5 s no piloto e 67,0 s no treino). Entre as páginas do `golden_v4`, as medianas foram de {virgula(fam['mediana_comuns_s'], 1)} s/página nas 20 páginas já vistas (ordenadas no `golden_v3`) e {virgula(fam['mediana_novas_s'], 1)} s/página nas 24 novas, sem efeito aparente de familiaridade nesta amostra.")
    w("")

    # 2. TABELA GOLDEN V4
    w("## 2. Resultados no `golden_v4` (44 páginas)")
    w("")
    w("Avaliação contra a ordem humana anotada por **Pedro alano** em 44 páginas concluídas sobre as regiões do Diamond. Métodos ordenados por τ médio decrescente.")
    w("")
    w("| Método | n | τ Kendall médio (IC 95%) | Mediana | p10 | Sucessor correto | ARD norm. | Acerto exato | Permutações válidas |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in resumo_v4:
        a, b = r["tau_ic95"]
        w(f"| {r['nome']} | {r['n']} | **{virgula(r['tau'], 3)}** ({virgula(a, 3)}–{virgula(b, 3)}) | {virgula(r['mediana'], 3)} | {virgula(r['p10'], 3)} | {pct_virgula(r['sucessor'], 1)} | {virgula(r['ard_norm'], 3)} | {pct_virgula(r['exato'], 1)} | {r['validas_str']} |")
    w("")
    w("### Resumo das Formulações do LayoutLM (3 Sementes)")
    w("")
    w(f"- **LayoutLM Pontual (sementes 42, 1, 2):** τ médio = **{virgula(seeds_pont['tau_mean'], 3)} ± {virgula(seeds_pont['tau_std'], 3)}** | Sucessor = **{pct_virgula(seeds_pont['suc_mean'], 1)} ± {pct_virgula(seeds_pont['suc_std'], 1)}** | ARD norm. = **{virgula(seeds_pont['ard_mean'], 3)} ± {virgula(seeds_pont['ard_std'], 3)}** | Acerto exato = **{pct_virgula(seeds_pont['exato_mean'], 1)} ± {pct_virgula(seeds_pont['exato_std'], 1)}**")
    w(f"- **LayoutLM Sucessor (sementes 42, 1, 2):** τ médio = **{virgula(seeds_suc['tau_mean'], 3)} ± {virgula(seeds_suc['tau_std'], 3)}** | Sucessor = **{pct_virgula(seeds_suc['suc_mean'], 1)} ± {pct_virgula(seeds_suc['suc_std'], 1)}** | ARD norm. = **{virgula(seeds_suc['ard_mean'], 3)} ± {virgula(seeds_suc['ard_std'], 3)}** | Acerto exato = **{pct_virgula(seeds_suc['exato_mean'], 1)} ± {pct_virgula(seeds_suc['exato_std'], 1)}**")
    w("")

    # 3. TESTES PAREADOS
    w("## 3. Testes Pareados contra a Heurística XY-cut no `golden_v4`")
    w("")
    w("Teste de postos com sinais de Wilcoxon pareado página a página (n = 44) entre cada método e a heurística de referência XY-cut. Correção de comparações múltiplas por Holm-Bonferroni (α = 0,05).")
    w("")
    w("| Posto | Método | n | Δ τ médio | p-valor bruto | Limiar Holm | p-valor ajustado | Sobrevive Holm? | Interpretação |")
    w("|---:|---|---:|---:|---:|---:|---:|:---:|---|")
    for t in testes_wilcoxon:
        sob = "Sim" if t["significativo"] else "Não"
        diff_str = f"{t['diff_media']:+.3f}".replace(".", ",")
        w(f"| {t['rank']} | {t['nome']} | {t['n']} | {diff_str} | {t['p_valor']:.2e} | {t['limiar_holm']:.2e} | {t['p_ajustado']:.2e} | **{sob}** | {t['interpretacao']} |")
    w("")
    sobreviveram = [t["nome"] for t in testes_wilcoxon if t["significativo"]]
    sup_lista = [t["nome"] for t in testes_wilcoxon if t["significativo"] and t["diff_media"] > 0]
    inf_lista = [t["nome"] for t in testes_wilcoxon if t["significativo"] and t["diff_media"] < 0]
    w(f"> **Análise de significância:** Das {len(testes_wilcoxon)} comparações, **{len(sobreviveram)} sobrevivem à correção de Holm**: "
      f"três superiores à XY-cut ({', '.join(sup_lista)}) e "
      f"quatro inferiores ({', '.join(inf_lista)}). "
      f"Nenhuma formulação do LayoutLM, nenhuma das quatro LLMs de texto e nem a ordem ingênua apresentaram diferença estatisticamente significante contra a XY-cut após correção múltipla; embora o τ médio do LayoutLM sucessor (Δ = +0,066) e das LLMs (Δ = +0,023 a +0,052) seja numericamente maior, a variabilidade entre páginas impede sustentar superioridade estatística.")
    w("")

    # 4. EFEITO DA SEGMENTAÇÃO
    w("## 4. Efeito da Segmentação nas 20 Páginas Comuns (`golden_v3` × `golden_v4`)")
    w("")
    w("> **Ressalva metodológica:** A referência humana também mudou entre os dois conjuntos. "
      "No `golden_v3`, a ordem foi anotada sobre os blocos produzidos pelo extrator automático v3; "
      "no `golden_v4`, a ordem foi reanotada pelo mesmo anotador sobre as regiões retificadas à mão no Diamond.")
    w("")
    w("| Método | τ v3 | τ v4 | Δ τ (v4−v3) | p (τ) | Sucessor v3 | Sucessor v4 | Δ Sucessor | p (suc.) |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in efeito_seg:
        if r["presente"]:
            d_tau_str = f"{r['diff_tau']:+.3f}".replace(".", ",")
            d_suc_str = f"{r['diff_suc'] * 100:+.1f}%".replace(".", ",")
            w(f"| {r['nome']} | {virgula(r['tau_v3'], 3)} | {virgula(r['tau_v4'], 3)} | **{d_tau_str}** | {r['p_tau']:.2e} | {pct_virgula(r['suc_v3'], 1)} | {pct_virgula(r['suc_v4'], 1)} | **{d_suc_str}** | {r['p_suc']:.2e} |")
        else:
            w(f"| {r['nome']} | — | — | — | — | — | — | — | {r['motivo']} |")
    w("")

    # 5. POR TIPO DE PÁGINA
    w("## 5. Avaliação por Tipo de Página no `golden_v4`")
    w("")
    w("Desempenho em τ de Kendall estratificado por densidade de colunas e presença de tabelas para os métodos-chave.")
    w("")
    w("| Estrutura da Página | n | XY-cut | LayoutLM sucessor (sem. 42) | VLM com marcas | Qwen 3.8 27B (few-shot 2) |")
    w("|---|---:|---:|---:|---:|---:|")
    for c in cortes_pag:
        llm_val = virgula(c['llm'], 3) if c["llm"] is not None else "—"
        w(f"| {c['categoria']} ({c['tipo']}) | {c['n']} | {virgula(c['xycut'], 3)} | {virgula(c['layoutlm_sucessor'], 3)} | **{virgula(c['vlm_com_marcas'], 3)}** | {llm_val} |")
    w("")
    if melhor_llm_v4:
        w(f"*Nota sobre LLMs:* As LLMs de texto (Qwen 3.8 27B e Gemma 4 31B) recebem exclusivamente texto e coordenadas dos blocos no prompt, sem classes anotadas e sem a imagem da página. A coluna fixa o modelo **{nome_metodo(melhor_llm_v4)}**, melhor LLM no resultado global do `golden_v4` (τ = {virgula(llm_melhor_obj['tau'], 3) if llm_melhor_obj else '0,876'}), evitando seleção oportunista da melhor LLM em cada estrato.")
    w("")

    # 6. VLM
    w("## 6. Avaliação do Modelo Visual-Linguístico (VLM)")
    w("")
    w("### 6.1 Ablação de Marcas Visuais e Classes Semânticas")
    w("")
    w("| Configuração | n | τ Kendall médio (IC 95%) | Sucessor correto | Permutações válidas | Latência média |")
    w("|---|---:|---:|---:|---:|---:|")
    a_cc, b_cc = vlm_cc["tau_ic95"]
    a_sc, b_sc = vlm_sc["tau_ic95"]
    a_sm, b_sm = vlm_sm["tau_ic95"]
    w(f"| **Com marcas e classes** (`gemini-3.1-flash-lite`) | {vlm_cc['n']} | **{virgula(vlm_cc['tau'], 3)}** ({virgula(a_cc, 3)}–{virgula(b_cc, 3)}) | **{pct_virgula(vlm_cc['sucessor'], 1)}** | {vlm_cc['validas_cnt']}/{vlm_cc['validas_total']} ({pct_virgula(vlm_cc['validas_pct'], 1)}) | {virgula(vlm_cc['segundos_por_pagina'], 1)} s/pág. |")
    w(f"| **Com marcas, sem classes** (`gemini-3.1-flash-lite`) | {vlm_sc['n']} | **{virgula(vlm_sc['tau'], 3)}** ({virgula(a_sc, 3)}–{virgula(b_sc, 3)}) | {pct_virgula(vlm_sc['sucessor'], 1)} | **{vlm_sc['validas_cnt']}/{vlm_sc['validas_total']} ({pct_virgula(vlm_sc['validas_pct'], 1)})** | {virgula(vlm_sc['segundos_por_pagina'], 1)} s/pág. |")
    w(f"| **Sem marcas, com classes** (`gemini-3.1-flash-lite`) | {vlm_sm['n']} | {virgula(vlm_sm['tau'], 3)} ({virgula(a_sm, 3)}–{virgula(b_sm, 3)}) | {pct_virgula(vlm_sm['sucessor'], 1)} | {vlm_sm['validas_cnt']}/{vlm_sm['validas_total']} ({pct_virgula(vlm_sm['validas_pct'], 1)}) | {virgula(vlm_sm['segundos_por_pagina'], 1)} s/pág. |")
    w("")
    w("#### Análise do Papel das Classes Semânticas vs. Marcas Visuais")
    w("")
    w(f"1. **Impacto das classes no prompt:** No desenho original do `golden_v4`, cada caixa fornecida ao VLM trazia a classe semântica anotada manualmente no Diamond (`cabecalho`, `rodape`, `assinatura`, `texto`, `titulo`, `tabela`). Na ablação **sem classes**, o modelo recebeu a mesma imagem com marcas e as mesmas coordenadas e textos, sem a classe. A diferença no τ de Kendall médio foi de apenas **{virgula(diff_classes, 3)}** ({virgula(vlm_cc['tau'], 3)} com classes vs. {virgula(vlm_sc['tau'], 3)} sem classes), com teste pareado de Wilcoxon indicando ausência de significância estatística (**p = {virgula(p_classes, 3)}**). A proporção de permutações válidas inclusive subiu de {pct_virgula(vlm_cc['validas_pct'], 1)} para {pct_virgula(vlm_sc['validas_pct'], 1)}.")
    w(f"2. **Confirmação pelo `golden_v3`:** No lote `golden_v3` (47 páginas), onde as caixas eram oriundas do extrator automático e não possuíam classes humanas (apenas anotação geométrica de tabelas pelo detector Docling Heron), o mesmo VLM com marcas obteve **τ = {virgula(tau_v3, 3)}** e **{pct_virgula(suc_v3, 1)}** de sucessor correto, indicando que o desempenho não depende de classes humanas prévias para ordenar páginas de Diários Oficiais.")
    w(f"3. **Efeito das marcas visuais (Set-of-Mark):** A comparação pareada entre a versão com marcas e classes e a versão sem marcas e com classes nas mesmas 44 páginas resulta em: τ {virgula(vlm_cc['tau'], 3)} → {virgula(vlm_sm['tau'], 3)} (Wilcoxon pareado p = {virgula(p_marcas, 4)}), acerto de sucessor de {pct_virgula(vlm_cc['sucessor'], 1)} para {pct_virgula(vlm_sm['sucessor'], 1)} e permutações válidas {vlm_cc['validas_cnt']} → {vlm_sm['validas_cnt']} de {vlm_sm['validas_total']} ({pct_virgula(vlm_cc['validas_pct'], 1)} → {pct_virgula(vlm_sm['validas_pct'], 1)}). Mesmo sem marcas visuais, o VLM ainda supera a XY-cut com significância estatística após correção de Holm (p bruto = 1,98e-04; p ajustado por Holm = 2,97e-03).")
    w(f"4. **Comparação com LLMs textuais:** Modelos puramente textuais (Qwen 3.8 27B e Gemma 4 31B), que recebem texto e coordenadas sem classes e sem a renderização visual da página, atingiram no máximo τ = {virgula(llm_melhor_obj['tau'], 3) if llm_melhor_obj else '0,876'} ({llm_melhor_obj['nome'] if llm_melhor_obj else 'Qwen 3.8 27B fs2'}; {llm_melhor_obj['validas_str'] if llm_melhor_obj else ''} de permutações válidas). No entanto, essa comparação mistura duas dimensões (modalidade e família/tamanho de modelo), não permitindo atribuir a diferença à integração multimodal; o desenho experimental não separa o efeito da imagem do efeito do modelo, pois uma comparação isolada da imagem exigiria rodar o mesmo Gemini apenas com texto.")
    w("")
    w("### 6.2 As 5 Piores Páginas do VLM com Marcas")
    w("")
    w("Páginas do `golden_v4` com menor τ de Kendall para o VLM Gemini 3.1 Flash Lite (com marcas e classes). Todas as colunas contêm valores estritamente mensurados a partir das anotações e predições.")
    w("")
    w("| Posto | ID da Página | Blocos | Colunas | Tabelas | Válida? | Rótulos devolvidos | τ Kendall | Sucessor correto |")
    w("|---:|---|---:|---:|---:|:---:|---:|---:|---:|")
    for i, p in enumerate(piores5_vlm, 1):
        w(f"| {i} | `{p['page_id']}` | {p['n_blocos']} | {p['colunas']} | {p['tabelas']} | {'Sim' if p['permutacao_valida'] else 'Não'} | {p['rotulos_devolvidos']} | **{virgula(p['tau'], 3)}** | {pct_virgula(p['sucessor'], 1)} |")
    w("")

    # 7. LAYOUTLM FORA DO DOMÍNIO
    w("## 7. LayoutLM Fora do Domínio de Treinamento")
    w("")
    w("O modelo LayoutLM foi treinado sobre blocos automáticos do extrator v3 (`data/processed/blocos/`). "
      "Abaixo avalia-se o comportamento ao ser aplicado às regiões retificadas à mão no Diamond (`golden_v4`).")
    w("")
    w("| Formulação e Semente | τ no `golden_v3` (47 págs.) | τ no `golden_v4` (44 págs.) | Queda relativa τ | Sucessor `v3` | Sucessor `v4` | Queda relativa Sucessor |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for t in tab_dominio:
        q_tau_str = f"{t['queda_rel'] * 100:+.1f}%".replace(".", ",")
        q_suc_str = f"{t['queda_suc_rel'] * 100:+.1f}%".replace(".", ",")
        w(f"| {t['modelo']} | {virgula(t['tau_v3'], 3)} | {virgula(t['tau_v4'], 3)} | **{q_tau_str}** | {pct_virgula(t['suc_v3'], 1)} | {pct_virgula(t['suc_v4'], 1)} | **{q_suc_str}** |")
    w("")
    p_q_str = f"{pont_resumo[2] * 100:+.1f}%".replace(".", ",")
    s_q_str = f"{suc_resumo[2] * 100:+.1f}%".replace(".", ",")
    w(f"- **Média LayoutLM Pontual:** τ {virgula(pont_resumo[0], 3)} → {virgula(pont_resumo[1], 3)} ({p_q_str})")
    w(f"- **Média LayoutLM Sucessor:** τ {virgula(suc_resumo[0], 3)} → {virgula(suc_resumo[1], 3)} ({s_q_str})")
    w("")
    w("> **Observação sobre continuidade local:** Embora o τ de Kendall se mantenha praticamente estável, "
      "a acurácia de sucessor correto sofre reduções quando testada nas 20 páginas comuns. "
      "A queda de -10,1 pp na semente 42 tem p = 0,055 (não significativa); "
      "as sementes 1 e 2 apresentam p bruto de 0,037 e 0,028 sem correção para múltiplos testes. "
      "A queda observada é compatível com a sensibilidade do sucessor ao corte das caixas, "
      "lembrando que a referência humana também foi reanotada entre os dois conjuntos (limitação 3).")
    w("")

    # 8. SEGMENTAÇÃO DIAMOND
    w("## 8. Avaliação da Segmentação no Diamond")
    w("")
    w("Reprodução dos resultados de `resultados/diamond/*/avaliacao.json` comparando a segmentação em regiões contra o gabarito humano.")
    w("")
    for nome_conj, dados_diam in [("Piloto (20 páginas, in-sample)", diam_piloto), ("Treino (25 páginas anotadas)", diam_treino)]:
        w(f"### Diamond {nome_conj}")
        w("")
        w("| Sistema | Páginas | Regiões gabarito | F1@0,5 | F1@0,9 | F1 exata | F1@0,5 com classe | Classe certa (% palavras) |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|")
        sistemas = dados_diam.get("sistemas", {})
        for s_nome, s_info in sistemas.items():
            if s_nome in ("v3", "proposta", "regioes_v2", "regioes", "rose:rose_piloto_v2", "rose:rose_treino",
                          "regioes_v3+rose:todas", "regioes_v3+rose:assinatura_cabecalho", "regioes_v3+rose:assinatura_cabecalho_titulo_rodape"):
                p_cnt = s_info.get("paginas", 0)
                r_pred = s_info.get("regioes_sistema", 0)
                r_gt = s_info.get("regioes_gabarito", 0)
                f05 = s_info.get("f1_j50", 0.0)
                f09 = s_info.get("f1_j90", 0.0)
                fex = s_info.get("f1_exata", 0.0)
                fcl = s_info.get("f1_j50_classe", 0.0)
                cl_pal = s_info.get("classe_certa_palavras", 0.0)
                w(f"| `{s_nome}` | {p_cnt} | {r_pred} ({r_gt}) | {virgula(f05, 3)} | {virgula(f09, 3)} | {virgula(fex, 3)} | {virgula(fcl, 3)} | {pct_virgula(cl_pal, 1)} |")
        w("")

    # 9. CUSTO HUMANO E COMPUTACIONAL
    w("## 9. Custo Humano de Anotação e Custo Computacional")
    w("")
    w("### 9.1 Custo Humano de Anotação")
    w("")
    w("Tempo ativo de trabalho por página registrado na ferramenta de anotação (apenas páginas concluídas).")
    w("")
    w("| Conjunto | Tarefa humana | Páginas concluídas | Tempo total ativo | Mediana por página | Média por página | Média por elemento |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for c in custos_humanos["tabela"]:
        w(f"| **{c['chave']}** | {c['rotulo']} | {c['n_concluidas']} | **{virgula(c['total_min'], 1)} min** | **{virgula(c['mediana_s'], 1)} s** | {virgula(c['media_s'], 1)} s | {virgula(c['media_por_elem_s'], 1)} s/bloco |")
    w("")
    w("**Familiaridade no `golden_v4`:** Do total de 44 páginas concluídas do `golden_v4`, **20 páginas já haviam sido ordenadas** pelo mesmo anotador humano durante a campanha do `golden_v3` (sobre os blocos do extrator v3). As medianas foram de 17,0 s nas 20 páginas já vistas e 15,0 s nas 24 novas, sem efeito aparente de familiaridade nesta amostra:")
    w(f"- **20 páginas já vistas (ordenadas no v3):** mediana de **{virgula(fam['mediana_comuns_s'], 1)} s/página** (média {virgula(fam['media_comuns_s'], 1)} s; tempo total {virgula(fam['total_comuns_min'], 1)} min).")
    w(f"- **24 páginas novas:** mediana de **{virgula(fam['mediana_novas_s'], 1)} s/página** (média {virgula(fam['media_novas_s'], 1)} s; tempo total {virgula(fam['total_novas_min'], 1)} min).")
    w(f"- **Total (44 páginas):** mediana de **{virgula(fam['mediana_total_s'], 1)} s/página** (média {virgula(fam['media_total_s'], 1)} s; tempo total {virgula(fam['total_min'], 1)} min).")
    w("")
    w("Cabe ressaltar que ordenar blocos e retificar caixas são tarefas diferentes. O tempo de anotação da ordem sobre regiões pré-segmentadas é menor (4 a 6 vezes mais rápido) do que a retificação geométrica de caixas e rotulagem de classes no Diamond (mediana de 67,0 s a 98,5 s).")
    w("")
    w("### 9.2 Custo Computacional de Inferência")
    w("")
    w("Registro de tempo de execução e taxa de permutações válidas para os métodos neurais e LLMs avaliados no `golden_v4`. As LLMs de texto foram executadas via Ollama no Kaggle (2× Tesla T4, contexto 8.192 tokens); o VLM foi executado via API Gemini 3.1 Flash Lite.")
    w("")
    w("| Método | Modelo | Few-shot | Plataforma | Tempo / pág. | Permutações válidas | Tempo total |")
    w("|---|---|---|---|---:|---:|---:|")
    for e in execucoes_llm:
        w(f"| {nome_metodo(e['metodo'])} | `{e['modelo']}` | {e['few_shot']} ex. | {e['gpu']} | {virgula(e['segundos_por_pagina'], 2)} s | {e['prop_permutacoes_validas']:.1%} | {virgula(e['segundos_execucao'] / 60.0, 1)} min |")
    w(f"| VLM Gemini 3.1 Flash Lite (com marcas) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | {virgula(vlm_cc['segundos_por_pagina'], 1)} s | {vlm_cc['validas_cnt']}/{vlm_cc['validas_total']} ({pct_virgula(vlm_cc['validas_pct'], 1)}) | — |")
    w(f"| VLM Gemini 3.1 Flash Lite (sem classes) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | {virgula(vlm_sc['segundos_por_pagina'], 1)} s | {vlm_sc['validas_cnt']}/{vlm_sc['validas_total']} ({pct_virgula(vlm_sc['validas_pct'], 1)}) | — |")
    w(f"| VLM Gemini 3.1 Flash Lite (sem marcas) | `gemini-3.1-flash-lite` | Zero-shot | API Gemini | {virgula(vlm_sm['segundos_por_pagina'], 1)} s | {vlm_sm['validas_cnt']}/{vlm_sm['validas_total']} ({pct_virgula(vlm_sm['validas_pct'], 1)}) | — |")
    w("| LayoutLM sucessor (semente 42) | `layoutlm_sucessor` | — | Local (RTX 4050) | ~0,02 s | 44/44 (100%) | < 1 s |")
    w("| XY-cut | — | — | Local (CPU) | < 0,001 s | 44/44 (100%) | < 0,1 s |")
    w("")

    # 10. LIMITAÇÕES
    w("## 10. Limitações")
    w("")
    w("1. **Anotador único:** Todas as anotações do `golden_v4` e dos lotes do Diamond foram realizadas por um único anotador humano (Pedro alano). Não há medida de concordância inter-anotador para este lote (o teto teórico só foi medido no `golden_v1`/`v2`).")
    w("2. **Ancoragem da proposta no Diamond:** O anotador corrigiu caixas e classes a partir da pré-anotação gerada pelo algoritmo (`proposta`), o que ancora as decisões humanas nas fronteiras pré-existentes e infla a aparente precisão da proposta.")
    w("3. **Referência reanotada:** Na comparação entre `golden_v3` e `golden_v4` nas 20 páginas comuns, além da segmentação ter mudado, a ordem de leitura foi refeita, misturando o efeito de corte de blocos com possíveis variações de julgamento do anotador.")
    w("4. **Texto só em imagem:** Conforme levantamento de 13/09 registrado no `COMUNICACAO_AGENTES.md`, **13,8% das páginas do acervo** possuem regiões de texto impressas puramente como imagem (sem palavras digitais na camada do PDF). Como o pipeline atual não inclui OCR, essas regiões permanecem totalmente invisíveis aos modelos de ordenação.")
    w("5. **Classes humanas e regras no prompt do VLM:** As classes das caixas fornecidas no prompt do VLM provêm da anotação humana realizada no Diamond, e o prompt incorpora as mesmas regras e convenções do guia seguido pelo anotador. Embora a ablação sem classes demonstre que o modelo mantém τ = 0,966 mesmo sem os rótulos de classe, a presença das diretrizes de ordenação no system prompt do modelo multimodal favorece o VLM em comparação com métodos heurísticos e neurais locais que operam sem acesso a essas regras explícitas.")
    w("6. **Segmentação corrigida à mão:** O `golden_v4` utiliza segmentação retificada manualmente pelo especialista no Diamond. Dessa forma, os resultados medem o desempenho da ordenação com segmentação ideal, não o pipeline automático completo de ponta a ponta.")
    w("7. **VLM em API fechada no nível gratuito:** O modelo Gemini 3.1 Flash Lite foi avaliado via API comercial no nível gratuito. Como a API é fechada, a versão interna do modelo pode mudar pelo provedor, impondo limitações de reprodutibilidade.")
    w("")

    # 11. PRÓXIMOS PASSOS SUGERIDOS
    w("## 11. Próximos Passos Sugeridos")
    w("")
    w(f"1. **Re-treinar o LayoutLM sobre as regiões Diamond:** O modelo atual treinado no extrator v3 preserva o τ global médio ({virgula(pont_resumo[1], 3)} e {virgula(suc_resumo[1], 3)}), mas sofreu redução de continuidade local nas 20 páginas comuns (-10,1 pp no sucessor correto para a semente 42, p = 0,055). Hipótese a testar: o re-treino sobre as caixas Diamond restabelece as transições aprendidas entre regiões retificadas.")
    w(f"2. **Avaliar o VLM como fonte de rótulo de ordem:** O Gemini 3.1 Flash Lite com marcas obteve τ = {virgula(vlm_cc['tau'], 3)} (com classes) e τ = {virgula(vlm_sc['tau'], 3)} (sem classes), com {pct_virgula(vlm_cc['sucessor'], 1)} e {pct_virgula(vlm_sc['sucessor'], 1)} de sucessor correto (diferença estatisticamente significante frente à XY-cut após correção de Holm, p = 5,43e-06 e p = 9,76e-06). Recomenda-se avaliar formalmente seu emprego para geração de pseudo-rótulos de ordem somente após mensurar a taxa de concordância inter-anotador com humanos em páginas inéditas e estritamente sem classes humanas no prompt (cenário em que atingiu τ = {virgula(vlm_sc['tau'], 3)} no `golden_v4` e τ = {virgula(tau_v3, 3)} no `golden_v3`).")
    w(f"3. **Manter as marcas no protocolo do VLM:** A ausência de marcadores visuais (Set-of-Mark) reduziu o desempenho do Gemini 3.1 Flash Lite nas 44 páginas: τ {virgula(vlm_cc['tau'], 3)} → {virgula(vlm_sm['tau'], 3)} (Wilcoxon pareado p = {virgula(p_marcas, 4)}), acerto de sucessor de {pct_virgula(vlm_cc['sucessor'], 1)} para {pct_virgula(vlm_sm['sucessor'], 1)} e permutações válidas de {vlm_cc['validas_cnt']} para {vlm_sm['validas_cnt']} de {vlm_sm['validas_total']} ({pct_virgula(vlm_cc['validas_pct'], 1)} → {pct_virgula(vlm_sm['validas_pct'], 1)}). Mesmo sem marcas, o VLM ainda supera a XY-cut após Holm.")
    w(f"4. **Incorporar o Rose no classificador de blocos:** Na avaliação de segmentação em regiões, a comparação entre `regioes` (0,848) e `regioes_v3+rose:assinatura_cabecalho` (0,857) no piloto e 0,793 → 0,800 no treino (25 páginas) resultou em ganho de cerca de 0,01 no F1 com classe, o qual não foi testado estatisticamente.")
    w(f"5. **Escalar a anotação de ordem:** O tempo mediano de ordenação foi de {virgula(fam['mediana_total_s'], 1)} s/página no `golden_v4` (medianas de {virgula(fam['mediana_comuns_s'], 1)} s nas 20 páginas já vistas e {virgula(fam['mediana_novas_s'], 1)} s nas 24 novas, sem efeito aparente de familiaridade nesta amostra). Por serem tarefas diferentes, o tempo de ordenação é menor (4 a 6 vezes) que a retificação geométrica de caixas e classes no Diamond (mediana de 67,0 s a 98,5 s), indicando baixo custo temporal para a ordenação sobre regiões pré-corrigidas.")
    w("")

    return "\n".join(md)


def plotar_figuras(resumo_v4, efeito_seg, caminho_fig1: str, caminho_fig2: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SUPERFICIE, TEXTO, TEXTO2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO2, "xtick.color": TEXTO2, "ytick.color": TEXTO2,
        "text.color": TEXTO, "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9, "axes.titlesize": 11, "axes.titleweight": "bold",
    })

    # FIGURA 1: Comparação de métodos no golden_v4 (barras horizontais com IC 95%)
    fig1, ax1 = plt.subplots(figsize=(9, 7.0))
    itens = [r for r in resumo_v4 if not r["metodo"].startswith("ablacao_suc_sem_")]
    itens_rev = list(reversed(itens))
    nomes_rev = [r["nome"] for r in itens_rev]
    taus_rev = [r["tau"] for r in itens_rev]
    err_inf = [r["tau"] - r["tau_ic95"][0] for r in itens_rev]
    err_sup = [r["tau_ic95"][1] - r["tau"] for r in itens_rev]

    cores = []
    for r in itens_rev:
        m = r["metodo"]
        if "vlm" in m:
            cores.append("#008300")
        elif "llm" in m:
            cores.append("#800080")
        elif "sucessor" in m:
            cores.append("#7d1442")
        elif "layoutlm" in m or "pontual" in m:
            cores.append("#2a78d6")
        elif "xycut" in m:
            cores.append("#eb6834")
        elif "naive" in m:
            cores.append("#1baf7a")
        else:
            cores.append("#8f8e89")

    ys = range(len(itens_rev))
    ax1.barh(ys, taus_rev, xerr=[err_inf, err_sup], color=cores, height=0.65, capsize=3, zorder=3)
    ax1.set_yticks(ys)
    ax1.set_yticklabels(nomes_rev)
    ax1.set_xlabel("τ de Kendall médio (barras: IC 95% bootstrap)")
    ax1.set_title("Qualidade da Ordem de Leitura no golden_v4 (44 páginas)")
    ax1.set_xlim(-0.08, 1.05)
    for y, tau in zip(ys, taus_rev):
        ax1.text(tau + 0.03, y, virgula(tau, 3), va="center", fontsize=8, fontweight="bold")
    fig1.tight_layout()
    fig1.savefig(caminho_fig1, dpi=200)
    plt.close(fig1)

    # FIGURA 2: Efeito da segmentação (20 páginas comuns: golden_v3 vs golden_v4)
    fig2, ax2 = plt.subplots(figsize=(9, 6.5))
    comuns_plot = [r for r in efeito_seg if r.get("presente") and not r["metodo"].startswith("ablacao_")]
    comuns_plot.sort(key=lambda x: x["tau_v4"])
    ys2 = range(len(comuns_plot))
    nomes2 = [r["nome"] for r in comuns_plot]
    tau_v3 = [r["tau_v3"] for r in comuns_plot]
    tau_v4 = [r["tau_v4"] for r in comuns_plot]

    for y, t3, t4 in zip(ys2, tau_v3, tau_v4):
        ax2.plot([t3, t4], [y, y], color=GRADE, lw=2.5, zorder=2)

    ax2.scatter(tau_v3, ys2, color="#2a78d6", s=50, label="golden_v3 (blocos extrator v3)", zorder=4)
    ax2.scatter(tau_v4, ys2, color="#eb6834", s=50, label="golden_v4 (regiões Diamond)", zorder=4)
    ax2.set_yticks(ys2)
    ax2.set_yticklabels(nomes2)
    ax2.set_xlabel("τ de Kendall médio nas 20 páginas comuns")
    ax2.set_title("Efeito da Mudança de Segmentação (20 Páginas Comuns)")
    ax2.set_xlim(-0.1, 1.05)
    ax2.legend(loc="lower right")
    fig2.tight_layout()
    fig2.savefig(caminho_fig2, dpi=200)
    plt.close(fig2)


def df_resumo_v4(resumo_v4):
    import pandas as pd
    linhas = []
    for r in resumo_v4:
        a, b = r["tau_ic95"]
        linhas.append({
            "Método": r["nome"],
            "n": r["n"],
            "τ Kendall": virgula(r["tau"], 3),
            "IC 95%": f"{virgula(a, 3)}–{virgula(b, 3)}",
            "Mediana": virgula(r["mediana"], 3),
            "p10": virgula(r["p10"], 3),
            "Sucessor correto": pct_virgula(r["sucessor"], 1),
            "ARD norm.": virgula(r["ard_norm"], 3),
            "Acerto exato": pct_virgula(r["exato"], 1),
            "Permutações válidas": r["validas_str"],
        })
    return pd.DataFrame(linhas)


def df_wilcoxon(testes):
    import pandas as pd
    linhas = []
    for t in testes:
        diff_str = f"{t['diff_media']:+.3f}".replace(".", ",")
        linhas.append({
            "Posto": t["rank"],
            "Método": t["nome"],
            "n": t["n"],
            "Δ τ médio": diff_str,
            "p-valor bruto": f"{t['p_valor']:.2e}",
            "Limiar Holm": f"{t['limiar_holm']:.2e}",
            "p-valor ajustado": f"{t['p_ajustado']:.2e}",
            "Sobrevive Holm?": "Sim" if t["significativo"] else "Não",
            "Interpretação": t["interpretacao"],
        })
    return pd.DataFrame(linhas)


def df_efeito_seg(efeito_seg):
    import pandas as pd
    linhas = []
    for r in efeito_seg:
        if r.get("presente"):
            d_tau_str = f"{r['diff_tau']:+.3f}".replace(".", ",")
            d_suc_str = f"{r['diff_suc'] * 100:+.1f}%".replace(".", ",")
            linhas.append({
                "Método": r["nome"],
                "τ v3": virgula(r["tau_v3"], 3),
                "τ v4": virgula(r["tau_v4"], 3),
                "Δ τ (v4−v3)": d_tau_str,
                "p (τ)": f"{r['p_tau']:.2e}",
                "Sucessor v3": pct_virgula(r["suc_v3"], 1),
                "Sucessor v4": pct_virgula(r["suc_v4"], 1),
                "Δ Sucessor": d_suc_str,
                "p (suc.)": f"{r['p_suc']:.2e}",
            })
        else:
            linhas.append({
                "Método": r["nome"],
                "τ v3": "—",
                "τ v4": "—",
                "Δ τ (v4−v3)": "—",
                "p (τ)": "—",
                "Sucessor v3": "—",
                "Sucessor v4": "—",
                "Δ Sucessor": "—",
                "p (suc.)": r["motivo"],
            })
    return pd.DataFrame(linhas)


def df_cortes(cortes_pag):
    import pandas as pd
    linhas = []
    for c in cortes_pag:
        llm_val = virgula(c["llm"], 3) if c["llm"] is not None else "—"
        linhas.append({
            "Estrutura": f"{c['categoria']} ({c['tipo']})",
            "n": c["n"],
            "XY-cut": virgula(c["xycut"], 3),
            "LayoutLM sucessor (sem. 42)": virgula(c["layoutlm_sucessor"], 3),
            "VLM com marcas": virgula(c["vlm_com_marcas"], 3),
            "Qwen 3.8 27B (few-shot 2)": llm_val,
        })
    return pd.DataFrame(linhas)


def df_vlm_comp(comp_vlm):
    import pandas as pd
    linhas = []
    configs = [
        ("com_marcas_classes", "Com marcas e classes (gemini-3.1-flash-lite)"),
        ("com_marcas_sem_classes", "Com marcas, sem classes (gemini-3.1-flash-lite)"),
        ("sem_marcas_classes", "Sem marcas, com classes (gemini-3.1-flash-lite)"),
    ]
    for chave, rotulo in configs:
        if chave in comp_vlm:
            v = comp_vlm[chave]
            linhas.append({
                "Configuração": rotulo,
                "n": v["n"],
                "τ Kendall": f"{virgula(v['tau'], 3)} ({virgula(v['tau_ic95'][0], 3)}–{virgula(v['tau_ic95'][1], 3)})",
                "Sucessor correto": pct_virgula(v["sucessor"], 1),
                "Permutações válidas": f"{v['validas_cnt']}/{v['validas_total']} ({pct_virgula(v['validas_pct'], 1)})",
                "Latência média": f"{virgula(v['segundos_por_pagina'], 1)} s/pág.",
            })
    return pd.DataFrame(linhas)


def df_vlm_piores(piores5_vlm):
    import pandas as pd
    linhas = []
    for i, p in enumerate(piores5_vlm, 1):
        linhas.append({
            "Posto": i,
            "ID da Página": p["page_id"],
            "Blocos": p["n_blocos"],
            "Colunas": p["colunas"],
            "Tabelas": p["tabelas"],
            "Válida?": "Sim" if p["permutacao_valida"] else "Não",
            "Rótulos devolvidos": p["rotulos_devolvidos"],
            "τ Kendall": virgula(p["tau"], 3),
            "Sucessor correto": pct_virgula(p["sucessor"], 1),
        })
    return pd.DataFrame(linhas)


def df_dominio(tab_dominio):
    import pandas as pd
    linhas = []
    for t in tab_dominio:
        q_tau_str = f"{t['queda_rel'] * 100:+.1f}%".replace(".", ",")
        q_suc_str = f"{t['queda_suc_rel'] * 100:+.1f}%".replace(".", ",")
        linhas.append({
            "Formulação e Semente": t["modelo"],
            "τ no golden_v3 (47 págs.)": virgula(t["tau_v3"], 3),
            "τ no golden_v4 (44 págs.)": virgula(t["tau_v4"], 3),
            "Queda relativa τ": q_tau_str,
            "Sucessor v3": pct_virgula(t["suc_v3"], 1),
            "Sucessor v4": pct_virgula(t["suc_v4"], 1),
            "Queda relativa Sucessor": q_suc_str,
        })
    return pd.DataFrame(linhas)


def df_diamond(dados_diam):
    import pandas as pd
    sistemas = dados_diam.get("sistemas", {})
    linhas = []
    for s_nome, s_info in sistemas.items():
        if s_nome in ("v3", "proposta", "regioes_v2", "regioes", "rose:rose_piloto_v2", "rose:rose_treino",
                      "regioes_v3+rose:todas", "regioes_v3+rose:assinatura_cabecalho", "regioes_v3+rose:assinatura_cabecalho_titulo_rodape"):
            p_cnt = s_info.get("paginas", 0)
            r_pred = s_info.get("regioes_sistema", 0)
            r_gt = s_info.get("regioes_gabarito", 0)
            f05 = s_info.get("f1_j50", 0.0)
            f09 = s_info.get("f1_j90", 0.0)
            fex = s_info.get("f1_exata", 0.0)
            fcl = s_info.get("f1_j50_classe", 0.0)
            cl_pal = s_info.get("classe_certa_palavras", 0.0)
            linhas.append({
                "Sistema": s_nome,
                "Páginas": p_cnt,
                "Regiões sistema (gabarito)": f"{r_pred} ({r_gt})",
                "F1@0,5": virgula(f05, 3),
                "F1@0,9": virgula(f09, 3),
                "F1 exata": virgula(fex, 3),
                "F1@0,5 com classe": virgula(fcl, 3),
                "Classe certa (% palavras)": pct_virgula(cl_pal, 1),
            })
    return pd.DataFrame(linhas)


def df_custos(custos_humanos):
    import pandas as pd
    tabela = custos_humanos.get("tabela", custos_humanos) if isinstance(custos_humanos, dict) else custos_humanos
    linhas = []
    for c in tabela:
        linhas.append({
            "Conjunto": c["chave"],
            "Tarefa humana": c["rotulo"],
            "Páginas concluídas": c["n_concluidas"],
            "Tempo total ativo": f"{virgula(c['total_min'], 1)} min",
            "Mediana por página": f"{virgula(c['mediana_s'], 1)} s",
            "Média por página": f"{virgula(c['media_s'], 1)} s",
            "Média por elemento": f"{virgula(c['media_por_elem_s'], 1)} s/bloco",
        })
    return pd.DataFrame(linhas)


def df_familiaridade(custos_humanos):
    import pandas as pd
    if isinstance(custos_humanos, dict) and "familiaridade" in custos_humanos:
        fam = custos_humanos["familiaridade"]
        return pd.DataFrame([
            {
                "Subconjunto golden_v4": "20 páginas já vistas (ordenadas no v3)",
                "Páginas": fam["n_comuns"],
                "Tempo total": f"{virgula(fam['total_comuns_min'], 1)} min",
                "Mediana por página": f"{virgula(fam['mediana_comuns_s'], 1)} s",
                "Média por página": f"{virgula(fam['media_comuns_s'], 1)} s",
            },
            {
                "Subconjunto golden_v4": "24 páginas novas",
                "Páginas": fam["n_novas"],
                "Tempo total": f"{virgula(fam['total_novas_min'], 1)} min",
                "Mediana por página": f"{virgula(fam['mediana_novas_s'], 1)} s",
                "Média por página": f"{virgula(fam['media_novas_s'], 1)} s",
            },
            {
                "Subconjunto golden_v4": "Total (44 páginas)",
                "Páginas": fam["n_total"],
                "Tempo total": f"{virgula(fam['total_min'], 1)} min",
                "Mediana por página": f"{virgula(fam['mediana_total_s'], 1)} s",
                "Média por página": f"{virgula(fam['media_total_s'], 1)} s",
            },
        ])
    return pd.DataFrame()


def df_execucoes_llm(execucoes_llm):
    import pandas as pd
    linhas = []
    for e in execucoes_llm:
        linhas.append({
            "Método": nome_metodo(e["metodo"]),
            "Modelo": e["modelo"],
            "Few-shot": f"{e['few_shot']} ex.",
            "GPU": e["gpu"],
            "Tempo por página": f"{virgula(e['segundos_por_pagina'], 2)} s",
            "Permutações válidas": f"{e['prop_permutacoes_validas']:.1%}",
            "Tempo total": f"{virgula(e['segundos_execucao'] / 60.0, 1)} min",
        })
    return pd.DataFrame(linhas)


def main():
    print("Carregando dados do golden_v4 e golden_v3...")
    dados_v4 = carregar_lote("golden_v4")
    dados_v3 = carregar_lote("_avaliacao/golden_v3")

    regs_v4 = calcular_metricas_base(dados_v4)
    regs_v3 = calcular_metricas_base(dados_v3)

    print("Calculando tabelas e testes de hipóteses...")
    resumo_v4, seeds_pont, seeds_suc = tabela_golden_v4(regs_v4, dados_v4)
    testes_wilcoxon = calcular_wilcoxon_holm(regs_v4)
    comuns_20, efeito_seg = calcular_efeito_segmentacao(regs_v3, regs_v4, dados_v3, dados_v4)
    cortes_pag, melhor_llm_v4, melhor_llm_v3 = calcular_cortes_pagina(regs_v4, regs_v3)
    comp_vlm, piores5_vlm = calcular_vlm_detalhado(regs_v4, dados_v4, regs_v3)
    tab_dominio, pont_res, suc_res = calcular_layoutlm_dominio(regs_v3, regs_v4, efeito_seg)
    diam_piloto, diam_treino = carregar_resultados_diamond()
    custos_humanos = calcular_custos_humanos(dados_v4, dados_v3)
    execucoes_llm = carregar_execucoes_llm()

    os.makedirs(DIR_FIGURAS, exist_ok=True)
    caminho_fig1 = os.path.join(DIR_FIGURAS, "figura_v4_comparacao_metodos.png")
    caminho_fig2 = os.path.join(DIR_FIGURAS, "figura_v4_efeito_segmentacao.png")
    print(f"Gerando figuras em {DIR_FIGURAS}...")
    plotar_figuras(resumo_v4, efeito_seg, caminho_fig1, caminho_fig2)

    print("Formatando markdown do relatório...")
    md_content = formatar_markdown(
        resumo_v4, seeds_pont, seeds_suc, testes_wilcoxon, comuns_20,
        efeito_seg, cortes_pag, melhor_llm_v4, melhor_llm_v3,
        comp_vlm, piores5_vlm, tab_dominio, pont_res, suc_res,
        diam_piloto, diam_treino, custos_humanos, execucoes_llm
    )

    caminho_md = os.path.join(DIR_DOCS, "RELATORIO_V4.md")
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Gravado: {caminho_md} ({len(md_content)} bytes)")


if __name__ == "__main__":
    main()
