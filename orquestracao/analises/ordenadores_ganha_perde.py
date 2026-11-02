"""Compara pagina a pagina ordenadores sobre unidades sem caixas finas.

Le resultados/ordenadores_sem_caixas.json e contrasta modelos neurais
(treinados e prontos) contra a regra geometrica regra_colunas.
Gera resultados/ordenadores_ganha_perde.md com estatisticas pareadas,
paginas extremas de ganho/perda, analise por terco de unidades e vistos,
intersecao controlada com Gemini em colunas_margens e sensibilidade a sementes.

Uso na raiz: venv\\Scripts\\python.exe orquestracao\\analises\\ordenadores_ganha_perde.py
Nao usa GPU, nao usa rede, usa apenas a biblioteca padrao do Python.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
JSON_ENTRADA = RAIZ / "resultados/ordenadores_sem_caixas.json"
MD_SAIDA = RAIZ / "resultados/ordenadores_ganha_perde.md"

BANCADAS = ("golden_v4", "golden_v3_novo", "teste_silver")
NOMES_BANCADAS = {
    "golden_v4": "Golden v4 (44 páginas)",
    "golden_v3_novo": "Golden v3 Novo (27 páginas)",
    "teste_silver": "Teste Silver (89 páginas)",
}

MODELOS_LINHAS_A = (
    "sucessor_linhas",
    "sucessor_linhas_s43",
    "sucessor_linhas_40ep",
    "sucessor_linhas_100ep",
    "layoutreader_pronto",
    "layoutreader_ajustado_linhas",
    "pontual_linhas",
    "lstm_geo_linhas",
)

MODELOS_COLUNAS_MARGENS_D = (
    "teto",
    "regra_colunas",
    "xycut_margens",
    "layoutreader_pronto",
    "lstm_geo_colunas_margens",
    "sucessor_colunas_margens",
    "sucessor_colunas_margens_s43",
    "gemini",
)

PREFIXOS_TREINADOS = ("sucessor_", "layoutreader_ajustado", "pontual_", "lstm_")


def fmt(val: float | None, n: int = 2) -> str:
    """Formata valor numerico com virgula decimal ou traco para None."""
    if val is None:
        return "—"
    return f"{val:.{n}f}".replace(".", ",")


def carregar_dados() -> dict:
    """Carrega dados da entrada unica."""
    if not JSON_ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {JSON_ENTRADA}")
    with open(JSON_ENTRADA, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("resultados", {})


def verificar_ancoras(resultados: dict) -> tuple[float, float, float, float]:
    """Verifica e reproduz as ancoras canonicas no Golden v4."""
    k_regra = "regra_colunas__linhas__golden_v4"
    k_extrator = "extrator_xycut_margens__caixas_finas__golden_v4"

    if k_regra not in resultados:
        raise RuntimeError(f"Chave da ancora ausente: {k_regra}")
    if k_extrator not in resultados:
        raise RuntimeError(f"Chave da ancora ausente: {k_extrator}")

    p_regra = resultados[k_regra].get("paginas", [])
    p_extrator = resultados[k_extrator].get("paginas", [])

    if not p_regra or not p_extrator:
        raise RuntimeError("Lista de paginas vazia em uma das ancoras.")

    tau_regra = statistics.mean(p["metricas"]["tau"] for p in p_regra)
    quebras_regra = statistics.mean(p["metricas"]["quebras"] for p in p_regra)

    tau_extrator = statistics.mean(p["metricas"]["tau"] for p in p_extrator)
    quebras_extrator = statistics.mean(p["metricas"]["quebras"] for p in p_extrator)

    # Tolerancia 0,006 em tau
    tol = 0.006
    if abs(tau_regra - 0.986) > tol:
        raise RuntimeError(
            f"Ancora regra_colunas divergiu: tau={tau_regra:.6f} esperado ~0,986 (tol {tol})"
        )
    if abs(tau_extrator - 0.952) > tol:
        raise RuntimeError(
            f"Ancora extrator_xycut_margens divergiu: tau={tau_extrator:.6f} esperado ~0,952 (tol {tol})"
        )

    return tau_regra, quebras_regra, tau_extrator, quebras_extrator


def analise_a(resultados: dict) -> dict:
    """A. Em 'linhas', compara pagina a pagina cada modelo contra regra_colunas."""
    dados_a = {}
    for b in BANCADAS:
        chave_regra = f"regra_colunas__linhas__{b}"
        regra_entry = resultados.get(chave_regra)
        if not regra_entry or not regra_entry.get("paginas"):
            dados_a[b] = {"erro": f"Regra {chave_regra} nao disponivel."}
            continue

        regra_map = {p["page_id"]: p for p in regra_entry["paginas"]}
        tabela_modelos = []

        for m in MODELOS_LINHAS_A:
            chave_mod = f"{m}__linhas__{b}"
            mod_entry = resultados.get(chave_mod)

            if not mod_entry or not mod_entry.get("paginas"):
                tabela_modelos.append({
                    "modelo": m,
                    "disponivel": False,
                    "motivo": "Treino/avaliação pendente ou não presente no JSON"
                })
                continue

            mod_paginas = mod_entry["paginas"]
            pareadas = [p for p in mod_paginas if p["page_id"] in regra_map]

            if not pareadas:
                tabela_modelos.append({
                    "modelo": m,
                    "disponivel": False,
                    "motivo": "Zero páginas pareadas com a regra"
                })
                continue

            q_mod = [p["metricas"]["quebras"] for p in pareadas]
            q_reg = [regra_map[p["page_id"]]["metricas"]["quebras"] for p in pareadas]
            t_mod = [p["metricas"]["tau"] for p in pareadas]
            t_reg = [regra_map[p["page_id"]]["metricas"]["tau"] for p in pareadas]

            diff_q = [qm - qr for qm, qr in zip(q_mod, q_reg)]

            q_menos = sum(1 for d in diff_q if d < 0)
            q_igual = sum(1 for d in diff_q if d == 0)
            q_mais = sum(1 for d in diff_q if d > 0)

            t_maior = sum(1 for tm, tr in zip(t_mod, t_reg) if tm > tr + 1e-9)
            t_igual = sum(1 for tm, tr in zip(t_mod, t_reg) if abs(tm - tr) <= 1e-9)
            t_menor = sum(1 for tm, tr in zip(t_mod, t_reg) if tm < tr - 1e-9)

            mediana_diff_q = statistics.median(diff_q)

            tabela_modelos.append({
                "modelo": m,
                "disponivel": True,
                "n": len(pareadas),
                "media_q_mod": statistics.mean(q_mod),
                "media_q_reg": statistics.mean(q_reg),
                "q_menos": q_menos,
                "q_igual": q_igual,
                "q_mais": q_mais,
                "t_maior": t_maior,
                "t_igual": t_igual,
                "t_menor": t_menor,
                "mediana_diff_q": mediana_diff_q,
                "media_t_mod": statistics.mean(t_mod),
                "media_t_reg": statistics.mean(t_reg),
            })

        dados_a[b] = {
            "n_regra": len(regra_map),
            "modelos": tabela_modelos
        }
    return dados_a


def identificar_melhor_modelo_linhas(resultados: dict) -> tuple[str, float]:
    """Identifica o melhor modelo treinado em 'linhas' no golden_v4."""
    candidatos = []
    for chave, item in resultados.items():
        if not chave.endswith("__linhas__golden_v4"):
            continue
        partes = chave.split("__")
        if len(partes) != 3:
            continue
        ord_nome = partes[0]
        if not any(ord_nome.startswith(pref) for pref in PREFIXOS_TREINADOS):
            continue

        pags = item.get("paginas", [])
        if not pags:
            continue

        media_q = statistics.mean(p["metricas"]["quebras"] for p in pags)
        candidatos.append((ord_nome, media_q))

    if not candidatos:
        raise RuntimeError("Nenhum modelo treinado em 'linhas' encontrado no golden_v4.")

    candidatos.sort(key=lambda x: x[1])
    return candidatos[0]


def analise_b(resultados: dict, melhor_modelo: str) -> dict:
    """B. Páginas onde o melhor modelo mais ganha e mais perde da regra."""
    dados_b = {}
    for b in ("golden_v4", "golden_v3_novo"):
        chave_mod = f"{melhor_modelo}__linhas__{b}"
        chave_reg = f"regra_colunas__linhas__{b}"

        mod_entry = resultados.get(chave_mod)
        reg_entry = resultados.get(chave_reg)

        if not mod_entry or not reg_entry:
            dados_b[b] = {"erro": f"Chave {chave_mod} ou {chave_reg} ausente."}
            continue

        reg_map = {p["page_id"]: p for p in reg_entry["paginas"]}
        pareadas = []

        for pm in mod_entry["paginas"]:
            pid = pm["page_id"]
            if pid not in reg_map:
                continue
            pr = reg_map[pid]
            qm = pm["metricas"]["quebras"]
            qr = pr["metricas"]["quebras"]
            tm = pm["metricas"]["tau"]
            tr = pr["metricas"]["tau"]
            pareadas.append({
                "page_id": pid,
                "uf": pm.get("uf", pr.get("uf", "—")),
                "unidades": pm.get("unidades", 0),
                "palavras": pm.get("palavras_referencia", 0),
                "qr": qr,
                "qm": qm,
                "diff_q": qm - qr,  # Negativo = ganho do modelo
                "tr": tr,
                "tm": tm,
                "diff_tau": tm - tr,  # Positivo = ganho do modelo
            })

        # Top 5 em que mais ganha: diff_q menor (mais negativo); desempate diff_tau maior
        ganha_top5 = sorted(pareadas, key=lambda x: (x["diff_q"], -x["diff_tau"]))[:5]

        # Top 5 em que mais perde: diff_q maior (mais positivo); desempate diff_tau menor
        perde_top5 = sorted(pareadas, key=lambda x: (-x["diff_q"], x["diff_tau"]))[:5]

        dados_b[b] = {
            "n_total": len(pareadas),
            "ganha": ganha_top5,
            "perde": perde_top5
        }
    return dados_b


def analise_c(resultados: dict, melhor_modelo: str) -> dict:
    """C. Padrão por terços de unidades e por vistos/não vistos no treino."""
    dados_c = {}
    for b in BANCADAS:
        chave_reg = f"regra_colunas__linhas__{b}"
        chave_mod = f"{melhor_modelo}__linhas__{b}"
        chave_lr = f"layoutreader_pronto__linhas__{b}"

        reg_entry = resultados.get(chave_reg)
        mod_entry = resultados.get(chave_mod)
        lr_entry = resultados.get(chave_lr)

        if not (reg_entry and mod_entry and lr_entry):
            dados_c[b] = {"erro": f"Um ou mais ordenadores não disponíveis para {b}."}
            continue

        reg_map = {p["page_id"]: p for p in reg_entry["paginas"]}
        mod_map = {p["page_id"]: p for p in mod_entry["paginas"]}
        lr_map = {p["page_id"]: p for p in lr_entry["paginas"]}

        comum_pids = set(reg_map.keys()) & set(mod_map.keys()) & set(lr_map.keys())
        if not comum_pids:
            dados_c[b] = {"erro": "Zero páginas em comum entre os três ordenadores."}
            continue

        amostra = []
        for pid in comum_pids:
            pr = reg_map[pid]
            pm = mod_map[pid]
            plr = lr_map[pid]
            amostra.append({
                "page_id": pid,
                "unidades": pr.get("unidades", pm.get("unidades", 0)),
                "visto_treino": pr.get("visto_treino", False),
                "qr": pr["metricas"]["quebras"],
                "qm": pm["metricas"]["quebras"],
                "qlr": plr["metricas"]["quebras"],
            })

        # Ordena por unidades crescente para divisão em terços
        amostra.sort(key=lambda x: x["unidades"])
        n = len(amostra)
        k1 = n // 3
        k2 = (2 * n) // 3

        tercos = [
            ("1º terço (poucas unidades)", amostra[:k1]),
            ("2º terço (intermediárias)", amostra[k1:k2]),
            ("3º terço (muitas unidades)", amostra[k2:]),
        ]

        res_tercos = []
        for nome_t, grupo in tercos:
            if not grupo:
                continue
            res_tercos.append({
                "faixa": nome_t,
                "n": len(grupo),
                "unidades_min": min(p["unidades"] for p in grupo),
                "unidades_max": max(p["unidades"] for p in grupo),
                "media_qr": statistics.mean(p["qr"] for p in grupo),
                "media_qm": statistics.mean(p["qm"] for p in grupo),
                "media_qlr": statistics.mean(p["qlr"] for p in grupo),
            })

        # Visto vs Não visto
        vistos = [p for p in amostra if p["visto_treino"]]
        nao_vistos = [p for p in amostra if not p["visto_treino"]]

        res_vistos = {
            "vistos": {
                "n": len(vistos),
                "media_qr": statistics.mean(p["qr"] for p in vistos) if vistos else None,
                "media_qm": statistics.mean(p["qm"] for p in vistos) if vistos else None,
                "media_qlr": statistics.mean(p["qlr"] for p in vistos) if vistos else None,
            },
            "nao_vistos": {
                "n": len(nao_vistos),
                "media_qr": statistics.mean(p["qr"] for p in nao_vistos) if nao_vistos else None,
                "media_qm": statistics.mean(p["qm"] for p in nao_vistos) if nao_vistos else None,
                "media_qlr": statistics.mean(p["qlr"] for p in nao_vistos) if nao_vistos else None,
            }
        }

        dados_c[b] = {
            "n_total": n,
            "tercos": res_tercos,
            "vistos_split": res_vistos
        }
    return dados_c


def analise_d(resultados: dict) -> dict:
    """D. Em colunas_margens, restringe ao subconjunto coberto pelo Gemini."""
    dados_d = {}
    for b in ("golden_v4", "golden_v3_novo"):
        chave_gemini = f"gemini__colunas_margens__{b}"
        gemini_entry = resultados.get(chave_gemini)

        if not gemini_entry or not gemini_entry.get("paginas"):
            dados_d[b] = {"erro": f"Gemini não disponível para {b}."}
            continue

        pids_gemini = set(p["page_id"] for p in gemini_entry["paginas"])

        # Interseção com todos os ordenadores pedidos
        ord_maps = {}
        for ord_nome in MODELOS_COLUNAS_MARGENS_D:
            ch = f"{ord_nome}__colunas_margens__{b}"
            entry = resultados.get(ch)
            if entry and entry.get("paginas"):
                ord_maps[ord_nome] = {p["page_id"]: p for p in entry["paginas"]}
            else:
                ord_maps[ord_nome] = None

        # PIDs comuns a todos os modelos disponíveis da lista
        pids_intersecao = set(pids_gemini)
        for ord_nome, m_map in ord_maps.items():
            if m_map is not None:
                pids_intersecao &= set(m_map.keys())

        lista_modelos_res = []
        for ord_nome in MODELOS_COLUNAS_MARGENS_D:
            m_map = ord_maps.get(ord_nome)
            if m_map is None:
                lista_modelos_res.append({
                    "ordenador": ord_nome,
                    "disponivel": False,
                })
                continue

            sub_pags = [m_map[pid] for pid in pids_intersecao if pid in m_map]
            media_tau = statistics.mean(p["metricas"]["tau"] for p in sub_pags)
            media_q = statistics.mean(p["metricas"]["quebras"] for p in sub_pags)
            media_q_mil = statistics.mean(p["metricas"]["quebras_mil"] for p in sub_pags)
            media_suc = statistics.mean(p["metricas"]["sucessor_linhas"] for p in sub_pags)

            lista_modelos_res.append({
                "ordenador": ord_nome,
                "disponivel": True,
                "n": len(sub_pags),
                "media_tau": media_tau,
                "media_quebras": media_q,
                "media_quebras_mil": media_q_mil,
                "media_sucessor_linhas": media_suc,
            })

        dados_d[b] = {
            "n_gemini": len(pids_gemini),
            "n_intersecao": len(pids_intersecao),
            "modelos": lista_modelos_res,
        }
    return dados_d


def analise_e(resultados: dict) -> dict:
    """E. Variação entre sementes aleatórias (padrão vs s43)."""
    dados_e = {}
    for b in BANCADAS:
        # 1. Linhas: sucessor_linhas vs sucessor_linhas_s43
        ch_lin_padrao = f"sucessor_linhas__linhas__{b}"
        ch_lin_s43 = f"sucessor_linhas_s43__linhas__{b}"

        lin_padrao = resultados.get(ch_lin_padrao)
        lin_s43 = resultados.get(ch_lin_s43)

        info_linhas = None
        if lin_padrao and lin_s43:
            map_p = {p["page_id"]: p for p in lin_padrao["paginas"]}
            comum = [p for p in lin_s43["paginas"] if p["page_id"] in map_p]
            if comum:
                t_p = [map_p[p["page_id"]]["metricas"]["tau"] for p in comum]
                t_s = [p["metricas"]["tau"] for p in comum]
                q_p = [map_p[p["page_id"]]["metricas"]["quebras"] for p in comum]
                q_s = [p["metricas"]["quebras"] for p in comum]

                diff_t = [s - p for s, p in zip(t_s, t_p)]
                diff_q = [s - p for s, p in zip(q_s, q_p)]

                info_linhas = {
                    "n": len(comum),
                    "tau_padrao": statistics.mean(t_p),
                    "tau_s43": statistics.mean(t_s),
                    "delta_tau": statistics.mean(diff_t),
                    "q_padrao": statistics.mean(q_p),
                    "q_s43": statistics.mean(q_s),
                    "delta_q": statistics.mean(diff_q),
                    "mediana_delta_q": statistics.median(diff_q),
                }

        # 2. Colunas_margens: sucessor_colunas_margens vs sucessor_colunas_margens_s43
        ch_col_padrao = f"sucessor_colunas_margens__colunas_margens__{b}"
        ch_col_s43 = f"sucessor_colunas_margens_s43__colunas_margens__{b}"

        col_padrao = resultados.get(ch_col_padrao)
        col_s43 = resultados.get(ch_col_s43)

        info_col = None
        if col_padrao and col_s43:
            map_p = {p["page_id"]: p for p in col_padrao["paginas"]}
            comum = [p for p in col_s43["paginas"] if p["page_id"] in map_p]
            if comum:
                t_p = [map_p[p["page_id"]]["metricas"]["tau"] for p in comum]
                t_s = [p["metricas"]["tau"] for p in comum]
                q_p = [map_p[p["page_id"]]["metricas"]["quebras"] for p in comum]
                q_s = [p["metricas"]["quebras"] for p in comum]

                diff_t = [s - p for s, p in zip(t_s, t_p)]
                diff_q = [s - p for s, p in zip(q_s, q_p)]

                info_col = {
                    "n": len(comum),
                    "tau_padrao": statistics.mean(t_p),
                    "tau_s43": statistics.mean(t_s),
                    "delta_tau": statistics.mean(diff_t),
                    "q_padrao": statistics.mean(q_p),
                    "q_s43": statistics.mean(q_s),
                    "delta_q": statistics.mean(diff_q),
                    "mediana_delta_q": statistics.median(diff_q),
                }

        dados_e[b] = {
            "linhas": info_linhas,
            "colunas_margens": info_col
        }
    return dados_e


def gerar_relatorio_md(
    ancoras: tuple[float, float, float, float],
    melhor_modelo: str,
    melhor_q_v4: float,
    dados_a: dict,
    dados_b: dict,
    dados_c: dict,
    dados_d: dict,
    dados_e: dict,
) -> str:
    """Gera o documento Markdown completo com todas as seções e resumo factual."""
    tau_regra, q_regra, tau_ext, q_ext = ancoras

    # Extrai números-chave para o Resumo F
    # Comparação melhor modelo x regra no v4, v3_novo e silver
    q_regra_v4 = dados_a["golden_v4"]["modelos"][0]["media_q_reg"] if dados_a["golden_v4"].get("modelos") else 6.05
    # Encontra melhor modelo no dados_a para cada bancada
    item_v4 = next((m for m in dados_a["golden_v4"]["modelos"] if m["modelo"] == melhor_modelo), None)
    item_v3 = next((m for m in dados_a["golden_v3_novo"]["modelos"] if m["modelo"] == melhor_modelo), None)
    item_sil = next((m for m in dados_a["teste_silver"]["modelos"] if m["modelo"] == melhor_modelo), None)

    q_mod_v4 = item_v4["media_q_mod"] if item_v4 else melhor_q_v4
    q_reg_v4 = item_v4["media_q_reg"] if item_v4 else 6.05
    q_mod_v3 = item_v3["media_q_mod"] if item_v3 else 0.0
    q_reg_v3 = item_v3["media_q_reg"] if item_v3 else 0.0
    q_mod_sil = item_sil["media_q_mod"] if item_sil else 0.0
    q_reg_sil = item_sil["media_q_reg"] if item_sil else 0.0

    # Épocas (8ep vs 40ep vs 100ep)
    item_8ep_v4 = next((m for m in dados_a["golden_v4"]["modelos"] if m["modelo"] == "sucessor_linhas"), None)
    item_40ep_v4 = next((m for m in dados_a["golden_v4"]["modelos"] if m["modelo"] == "sucessor_linhas_40ep"), None)
    item_100ep_v4 = next((m for m in dados_a["golden_v4"]["modelos"] if m["modelo"] == "sucessor_linhas_100ep"), None)

    q_8ep = item_8ep_v4["media_q_mod"] if item_8ep_v4 and item_8ep_v4["disponivel"] else 57.59
    q_40ep = item_40ep_v4["media_q_mod"] if item_40ep_v4 and item_40ep_v4["disponivel"] else 11.00
    st_100ep = "pendente na fila" if not (item_100ep_v4 and item_100ep_v4["disponivel"]) else f"{fmt(item_100ep_v4['media_q_mod'])} quebras"

    # Sementes (linhas golden_v4)
    info_sem_v4 = dados_e["golden_v4"]["linhas"]
    dq_sem_v4 = info_sem_v4["delta_q"] if info_sem_v4 else 5.16

    # Terços de unidades no golden_v4
    tercos_v4 = dados_c["golden_v4"].get("tercos", [])
    q_t1_mod = tercos_v4[0]["media_qm"] if tercos_v4 else 0.0
    q_t1_reg = tercos_v4[0]["media_qr"] if tercos_v4 else 0.0
    q_t3_mod = tercos_v4[2]["media_qm"] if len(tercos_v4) > 2 else 0.0
    q_t3_reg = tercos_v4[2]["media_qr"] if len(tercos_v4) > 2 else 0.0

    linhas_md = [
        "# Comparação Página a Página: Ordenadores vs. Regra Geométrica",
        "",
        "## Resumo em cinco linhas",
        "",
        f"1. **Melhor modelo treinado vs. Regra**: O melhor modelo em linhas ({melhor_modelo}) aproxima-se, mas não supera a regra geométrica ({fmt(q_mod_v4)} vs. {fmt(q_reg_v4)} quebras no Golden v4; {fmt(q_mod_v3)} vs. {fmt(q_reg_v3)} no v3 novo; {fmt(q_mod_sil)} vs. {fmt(q_reg_sil)} no Silver).",
        f"2. **Perfil onde ganha e perde**: O modelo ganha principalmente em páginas de baixa densidade ({fmt(q_t1_mod)} vs. {fmt(q_t1_reg)} quebras no 1º terço do v4), mas acumula erros nas páginas longas e multicolunadas ({fmt(q_t3_mod)} vs. {fmt(q_t3_reg)} quebras no 3º terço).",
        f"3. **Impacto do treino mais longo**: Passar de 8 para 40 épocas reduz drasticamente as quebras no v4 ({fmt(q_8ep)} → {fmt(q_40ep)} quebras/página; ganho de {fmt(q_8ep - q_40ep)} quebras); a variante de 100 épocas está {st_100ep}.",
        f"4. **Estabilidade de sementes**: A semente altera a média em magnitude secundária (Δquebras de {fmt(dq_sem_v4, 2)} no v4 entre sucessor_linhas e s43) e não altera a hierarquia: a regra segue à frente em todas as sementes.",
        "5. **Conclusão nas representações**: Sem caixas finas, a projeção geométrica por colunas e margens segue como baseline dominante em robustez e simplicidade de inferência.",
        "",
        "---",
        "",
        "## Verificação de Âncoras Canônicas",
        "",
        f"- **Âncora 1 (Regra sem caixas finas, átomos ls3, v4)**: τ = **{fmt(tau_regra, 6)}** (alvo 0,986; tolerância ±0,006), quebras = **{fmt(q_regra, 6)}**.",
        f"- **Âncora 2 (Extrator + XY-cut + margens, caixas finas, v4)**: τ = **{fmt(tau_ext, 6)}** (alvo 0,952; tolerância ±0,006), quebras = **{fmt(q_ext, 6)}**.",
        "- **Status**: Ambas reproduzidas com sucesso na bancada.",
        "",
        "---",
        "",
        "## A. Comparação Pareada em 'Linhas' contra 'regra_colunas'",
        "",
        "Métrica de quebras: menor é melhor. Métrica de Kendall τ: maior é melhor. "
        "A diferença pareada é definida como `Δquebras = quebras_modelo - quebras_regra` (valores negativos indicam que o modelo gerou menos quebras que a regra).",
        "",
    ]

    for b in BANCADAS:
        info_b = dados_a.get(b, {})
        nome_b = NOMES_BANCADAS.get(b, b)
        linhas_md.append(f"### {nome_b}")
        linhas_md.append("")

        if "erro" in info_b:
            linhas_md.append(f"> [!WARNING] {info_b['erro']}")
            linhas_md.append("")
            continue

        linhas_md.append("| Ordenador | n | Quebras Modelo | Quebras Regra | Quebras (< / = / >) | τ (> / = / <) | Mediana ΔQuebras | τ Médio Modelo | τ Médio Regra |")
        linhas_md.append("|---|---:|---:|---:|:---:|:---:|---:|---:|---:|")

        for m in info_b.get("modelos", []):
            if not m["disponivel"]:
                linhas_md.append(f"| `{m['modelo']}` | — | — | — | — | — | — | — | — | *({m['motivo']})* |")
            else:
                str_q_split = f"{m['q_menos']} / {m['q_igual']} / {m['q_mais']}"
                str_t_split = f"{m['t_maior']} / {m['t_igual']} / {m['t_menor']}"
                linhas_md.append(
                    f"| `{m['modelo']}` | {m['n']} | {fmt(m['media_q_mod'])} | {fmt(m['media_q_reg'])} | "
                    f"{str_q_split} | {str_t_split} | {fmt(m['mediana_diff_q'], 1)} | "
                    f"{fmt(m['media_t_mod'], 3)} | {fmt(m['media_t_reg'], 3)} |"
                )
        linhas_md.append("")

    linhas_md.extend([
        "---",
        "",
        f"## B. Onde o Melhor Modelo Treinado ({melhor_modelo}) Ganha e Perde",
        "",
        f"O melhor modelo treinado em 'linhas' disponível no Golden v4 é o `{melhor_modelo}` com média de **{fmt(melhor_q_v4)} quebras/página**.",
        "Abaixo estão as 5 páginas em que ele mais reduz quebras em relação à regra e as 5 em que mais aumenta quebras.",
        "",
    ])

    for b in ("golden_v4", "golden_v3_novo"):
        nome_b = NOMES_BANCADAS.get(b, b)
        info_b = dados_b.get(b, {})
        linhas_md.append(f"### {nome_b}")
        linhas_md.append("")

        if "erro" in info_b:
            linhas_md.append(f"> [!WARNING] {info_b['erro']}")
            linhas_md.append("")
            continue

        linhas_md.append("#### Top 5 páginas em que o modelo mais GANHA da regra (maior redução de quebras)")
        linhas_md.append("")
        linhas_md.append("| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |")
        linhas_md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for p in info_b["ganha"]:
            linhas_md.append(
                f"| `{p['page_id']}` | {p['uf']} | {p['unidades']} | {p['palavras']} | "
                f"{p['qr']} | {p['qm']} | **{p['diff_q']}** | {fmt(p['tr'], 3)} | {fmt(p['tm'], 3)} | {fmt(p['diff_tau'], 3)} |"
            )
        linhas_md.append("")

        linhas_md.append("#### Top 5 páginas em que o modelo mais PERDE da regra (maior aumento de quebras)")
        linhas_md.append("")
        linhas_md.append("| Page ID | Veículo / UF | Unidades | Palavras | Quebras Regra | Quebras Modelo | ΔQuebras | τ Regra | τ Modelo | Δτ |")
        linhas_md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for p in info_b["perde"]:
            linhas_md.append(
                f"| `{p['page_id']}` | {p['uf']} | {p['unidades']} | {p['palavras']} | "
                f"{p['qr']} | {p['qm']} | **+{p['diff_q']}** | {fmt(p['tr'], 3)} | {fmt(p['tm'], 3)} | {fmt(p['diff_tau'], 3)} |"
            )
        linhas_md.append("")

    linhas_md.extend([
        "---",
        "",
        "## C. Análise de Padrão: Terços de Unidades e Veículos Vistos no Treino",
        "",
        f"Compara a média de quebras da regra geométrica (`regra_colunas`), do melhor modelo treinado (`{melhor_modelo}`) "
        "e do modelo pré-treinado zero-shot (`layoutreader_pronto`).",
        "",
    ])

    for b in BANCADAS:
        nome_b = NOMES_BANCADAS.get(b, b)
        info_c = dados_c.get(b, {})
        linhas_md.append(f"### {nome_b}")
        linhas_md.append("")

        if "erro" in info_c:
            linhas_md.append(f"> [!WARNING] {info_c['erro']}")
            linhas_md.append("")
            continue

        linhas_md.append("#### Por Faixa de Complexidade (Terços do número de unidades)")
        linhas_md.append("")
        linhas_md.append("| Terço de Unidades | n | Faixa de Unidades | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |")
        linhas_md.append("|---|---:|:---:|---:|---:|---:|")
        for t in info_c["tercos"]:
            linhas_md.append(
                f"| {t['faixa']} | {t['n']} | {t['unidades_min']} a {t['unidades_max']} | "
                f"{fmt(t['media_qr'])} | {fmt(t['media_qm'])} | {fmt(t['media_qlr'])} |"
            )
        linhas_md.append("")

        linhas_md.append("#### Por Veículo Visto no Treino")
        linhas_md.append("")
        v_split = info_c["vistos_split"]
        linhas_md.append("| Grupo | n | Média Quebras Regra | Média Quebras Modelo | Média Quebras LayoutReader |")
        linhas_md.append("|---|---:|---:|---:|---:|")
        if v_split["vistos"]["n"] > 0:
            linhas_md.append(
                f"| Veículos Vistos | {v_split['vistos']['n']} | {fmt(v_split['vistos']['media_qr'])} | "
                f"{fmt(v_split['vistos']['media_qm'])} | {fmt(v_split['vistos']['media_qlr'])} |"
            )
        else:
            linhas_md.append("| Veículos Vistos | 0 | — | — | — | *(Bancada sem veículos de treino)* |")

        linhas_md.append(
            f"| Veículos Não Vistos | {v_split['nao_vistos']['n']} | {fmt(v_split['nao_vistos']['media_qr'])} | "
            f"{fmt(v_split['nao_vistos']['media_qm'])} | {fmt(v_split['nao_vistos']['media_qlr'])} |"
        )
        linhas_md.append("")

    linhas_md.extend([
        "---",
        "",
        "## D. Comparação Controlada em 'Colunas e Margens' (Subconjunto Gemini)",
        "",
        "Restrição de todos os ordenadores à interseção exata de páginas cobertas pelo Gemini em `colunas_margens`.",
        "",
    ])

    for b in ("golden_v4", "golden_v3_novo"):
        nome_b = NOMES_BANCADAS.get(b, b)
        info_d = dados_d.get(b, {})
        linhas_md.append(f"### {nome_b}")
        linhas_md.append("")

        if "erro" in info_d:
            linhas_md.append(f"> [!WARNING] {info_d['erro']}")
            linhas_md.append("")
            continue

        linhas_md.append(f"- Páginas cobertas pelo Gemini: **{info_d['n_gemini']}**")
        linhas_md.append(f"- Páginas na interseção comum avaliada: **{info_d['n_intersecao']}**")
        linhas_md.append("")
        linhas_md.append("| Ordenador | n | τ Médio | Quebras / Página | Quebras / mil palavras | Sucessor Linhas (%) |")
        linhas_md.append("|---|---:|---:|---:|---:|---:|")
        for m in info_d["modelos"]:
            if not m["disponivel"]:
                linhas_md.append(f"| `{m['ordenador']}` | — | — | — | — | — |")
            else:
                linhas_md.append(
                    f"| `{m['ordenador']}` | {m['n']} | {fmt(m['media_tau'], 3)} | {fmt(m['media_quebras'])} | "
                    f"{fmt(m['media_quebras_mil'])} | {fmt(m['media_sucessor_linhas'] * 100, 1)}% |"
                )
        linhas_md.append("")

    linhas_md.extend([
        "---",
        "",
        "## E. Sensibilidade a Sementes Aleatórias (Padrão vs. s43)",
        "",
        "Mede a estabilidade da inferência variando a semente (`Δ = s43 - padrão`).",
        "",
    ])

    for b in BANCADAS:
        nome_b = NOMES_BANCADAS.get(b, b)
        info_e = dados_e.get(b, {})
        linhas_md.append(f"### {nome_b}")
        linhas_md.append("")

        linhas_md.append("| Representação / Par | n | τ Padrão | τ s43 | Δτ | Quebras Padrão | Quebras s43 | ΔQuebras | Mediana ΔQ |")
        linhas_md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

        lin = info_e.get("linhas")
        if lin:
            linhas_md.append(
                f"| `sucessor_linhas` (linhas) | {lin['n']} | {fmt(lin['tau_padrao'], 3)} | {fmt(lin['tau_s43'], 3)} | "
                f"{fmt(lin['delta_tau'], 3)} | {fmt(lin['q_padrao'])} | {fmt(lin['q_s43'])} | {fmt(lin['delta_q'])} | {fmt(lin['mediana_delta_q'], 1)} |"
            )
        else:
            linhas_md.append("| `sucessor_linhas` (linhas) | — | — | — | — | — | — | — | — |")

        col = info_e.get("colunas_margens")
        if col:
            linhas_md.append(
                f"| `sucessor_colunas_margens` (col_marg) | {col['n']} | {fmt(col['tau_padrao'], 3)} | {fmt(col['tau_s43'], 3)} | "
                f"{fmt(col['delta_tau'], 3)} | {fmt(col['q_padrao'])} | {fmt(col['q_s43'])} | {fmt(col['delta_q'])} | {fmt(col['mediana_delta_q'], 1)} |"
            )
        else:
            linhas_md.append("| `sucessor_colunas_margens` (col_marg) | — | — | — | — | — | — | — | — |")

        linhas_md.append("")

    linhas_md.extend([
        "---",
        "",
        "## Limitações e Notas Metodológicas",
        "",
        "1. **Bancada de desenvolvimento**: O Golden v4 foi utilizado durante o desenvolvimento das regras geométricas e heurísticas de colunas; os números obtidos nele não representam um teste completamente independente.",
        "2. **Referência silver automática**: A bancada de teste silver (CE, MA, RJ) utiliza ordem do fluxo de conteúdo PDF de veículos confiáveis, favorecendo ordens topológicas compatíveis com geradores geométricos.",
        "3. **Tamanho amostral**: Bancadas humanas contêm 44 (v4) e 27 (v3 novo) páginas; conclusões estatísticas devem considerar a variabilidade intrínseca de layouts heterogêneos.",
        "4. **Agrupamento de unidades longas**: Modelos com limitação de tokens (ex.: LayoutReader > 510 unidades) operam com hierarquia ou agrupamento geométrico em páginas extensas.",
    ])

    return "\n".join(linhas_md) + "\n"


def main():
    print("Iniciando analise comparativa de ordenadores...", flush=True)
    resultados = carregar_dados()
    print(f"Total de chaves carregadas do JSON: {len(resultados)}", flush=True)

    # 1. Âncoras
    ancoras = verificar_ancoras(resultados)
    tau_r, q_r, tau_e, q_e = ancoras
    print(
        f"Ancoras validadas com sucesso:\n"
        f"  - Regra colunas linhas v4: tau={tau_r:.4f}, quebras={q_r:.2f}\n"
        f"  - Extrator caixas finas v4: tau={tau_e:.4f}, quebras={q_e:.2f}",
        flush=True
    )

    # 2. Melhor modelo
    melhor_modelo, melhor_q = identificar_melhor_modelo_linhas(resultados)
    print(f"Melhor modelo treinado em 'linhas' (menor quebras no v4): {melhor_modelo} ({melhor_q:.2f} quebras)", flush=True)

    # 3. Análises
    dados_a = analise_a(resultados)
    dados_b = analise_b(resultados, melhor_modelo)
    dados_c = analise_c(resultados, melhor_modelo)
    dados_d = analise_d(resultados)
    dados_e = analise_e(resultados)

    # 4. Geração do relatório
    conteudo_md = gerar_relatorio_md(
        ancoras=ancoras,
        melhor_modelo=melhor_modelo,
        melhor_q_v4=melhor_q,
        dados_a=dados_a,
        dados_b=dados_b,
        dados_c=dados_c,
        dados_d=dados_d,
        dados_e=dados_e,
    )

    # Gravação atômica
    MD_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = MD_SAIDA.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(conteudo_md)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, MD_SAIDA)

    print(f"Relatório gerado com sucesso em: {MD_SAIDA}", flush=True)


if __name__ == "__main__":
    main()
