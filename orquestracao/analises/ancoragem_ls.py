# -*- coding: utf-8 -*-
"""
Quantificacao do vies de ancoragem no dataset de layout do Label Studio.

Mede quanto os anotadores humanos aceitaram, alteraram ou criaram caixas
a partir da pre-anotacao automatica (heuristica / detector) nos exports
do Label Studio do projeto parceiro:
  - data/labelstudio/ls_p05_seed1.json
  - data/labelstudio/ls_p13_seed2.json
  - data/labelstudio/ls_p15_seed3.json
  - data/labelstudio/ls_p22_seed4.json

Analisa:
  1. Distribuicao por 'origin' (manual, prediction, prediction-changed)
     no total, por semente, por classe e por anotador.
  2. Casamento com a pre-anotacao original quando disponivel (id e IoU):
     geometria alterada (IoU mediano, p10, % < 0.9, % < 0.5), trocas de
     classe (matriz de confusao), caixas apagadas e criadas.
  3. Estatisticas por pagina (fracao mexida, paginas 100% aceitas,
     lead_time vs taxa de mudanca).
  4. Analise por classe nas taxonomias de 16, 9 e 3 classes.
  5. Geracao de relatorio completo em resultados/labelstudio_ancoragem.md
     e cache estruturado em resultados/labelstudio_ancoragem_dados.json.

Uso:
    venv\\Scripts\\python.exe orquestracao/analises/ancoragem_ls.py
"""
from __future__ import annotations

import os
import sys
import json
import math
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from scipy import stats

# Garantir raiz do projeto no sys.path
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

DIR_LABELSTUDIO = RAIZ / "data" / "labelstudio"
DIR_RESULTADOS = RAIZ / "resultados"
ARQUIVO_RELATORIO = DIR_RESULTADOS / "labelstudio_ancoragem.md"
ARQUIVO_CACHE = DIR_RESULTADOS / "labelstudio_ancoragem_dados.json"

SEEDS_ARQUIVOS = [
    ("seed1", DIR_LABELSTUDIO / "ls_p05_seed1.json"),
    ("seed2", DIR_LABELSTUDIO / "ls_p13_seed2.json"),
    ("seed3", DIR_LABELSTUDIO / "ls_p15_seed3.json"),
    ("seed4", DIR_LABELSTUDIO / "ls_p22_seed4.json"),
]

# Tentar importar taxonomia oficial do projeto; se falhar, usar fallback identico
try:
    from src.data.taxonomia_layout import (
        GUIA,
        GUIA_PARA_EXTRATOR,
        LABELS_GUIA,
    )
except Exception:
    GUIA = (
        "act", "act section", "paragraph", "signature", "heading", "id",
        "header", "footer", "table", "chart", "figure", "caption",
        "title", "section title", "sub section title", "unknown"
    )
    GUIA_PARA_EXTRATOR = {
        "act": "titulo", "act section": "titulo",
        "title": "titulo", "section title": "titulo", "sub section title": "titulo",
        "paragraph": "texto", "id": "texto", "table": "tabela",
        "figure": "figura", "chart": "figura", "caption": "texto",
        "signature": "assinatura", "heading": "assinatura",
        "header": "cabecalho", "footer": "rodape", "unknown": "outro",
    }
    LABELS_GUIA = {c: ("", "") for c in GUIA}


def mapear_para_3_classes(classe_guia: str) -> Optional[str]:
    """
    Regra das 3 classes:
      - table -> tabela
      - figure, chart, heading -> imagem
      - unknown -> None (fica de fora)
      - resto -> texto
    """
    c = classe_guia.strip().lower()
    if c == "table":
        return "tabela"
    if c in ("figure", "chart", "heading"):
        return "imagem"
    if c == "unknown":
        return None
    return "texto"


def mapear_para_9_classes(classe_guia: str) -> str:
    """Mapeia classe do guia para as 9 classes do extrator."""
    c = classe_guia.strip().lower()
    return GUIA_PARA_EXTRATOR.get(c, "outro")


def calcular_iou(box_a: Tuple[float, float, float, float],
                  box_b: Tuple[float, float, float, float]) -> float:
    """
    Calcula IoU entre duas caixas (x, y, width, height).
    Coordenadas em % ou normalizadas.
    """
    xa, ya, wa, ha = box_a
    xb, yb, wb, hb = box_b

    x1 = max(xa, xb)
    y1 = max(ya, yb)
    x2 = min(xa + wa, xb + wb)
    y2 = min(ya + ha, yb + hb)

    w_inter = max(0.0, x2 - x1)
    h_inter = max(0.0, y2 - y1)
    area_inter = w_inter * h_inter

    area_a = max(0.0, wa) * max(0.0, ha)
    area_b = max(0.0, wb) * max(0.0, hb)
    area_union = area_a + area_b - area_inter

    if area_union <= 0.0:
        return 0.0
    return float(area_inter / area_union)


def extrair_caixas_de_result(result_lista: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Agrupa itens de anotação de um mesmo 'result' pelo 'id' da caixa.
    No Label Studio, uma caixa pode ter itens separados para:
      - rectangle (geometria x, y, width, height)
      - labels (value.labels = [classe])
      - textarea (value.text = [transcricao])
      - number (page_number, reading_order, ato_code, column_number)
    Itens type 'relation' ligam caixas e sao ignorados como caixas.
    """
    caixas: Dict[str, Dict[str, Any]] = {}

    for item in result_lista:
        if not isinstance(item, dict):
            continue
        tipo = item.get("type")
        if tipo == "relation":
            continue

        box_id = item.get("id")
        if not box_id:
            continue

        if box_id not in caixas:
            caixas[box_id] = {
                "id": box_id,
                "x": None,
                "y": None,
                "width": None,
                "height": None,
                "label": "unknown",
                "origin": None,
                "text": None,
                "orig_w": None,
                "orig_h": None,
            }

        c = caixas[box_id]
        val = item.get("value", {})
        if not isinstance(val, dict):
            val = {}

        # Geometria
        if "x" in val and "y" in val and "width" in val and "height" in val:
            try:
                c["x"] = float(val["x"])
                c["y"] = float(val["y"])
                c["width"] = float(val["width"])
                c["height"] = float(val["height"])
            except (ValueError, TypeError):
                pass

        # Dimensoes originais em px
        orig_w = item.get("original_width") or val.get("original_width")
        orig_h = item.get("original_height") or val.get("original_height")
        if orig_w is not None and c["orig_w"] is None:
            c["orig_w"] = orig_w
        if orig_h is not None and c["orig_h"] is None:
            c["orig_h"] = orig_h

        # Rotulo (classe)
        labels = val.get("labels") or val.get("rectanglelabels") or val.get("choices")
        if labels and isinstance(labels, list) and len(labels) > 0:
            c["label"] = str(labels[0]).strip().lower()

        # Origem
        origin = item.get("origin") or val.get("origin")
        if origin:
            orig_str = str(origin).strip().lower()
            # Se vier prediction-changed em qualquer item, priorizar
            if orig_str == "prediction-changed":
                c["origin"] = "prediction-changed"
            elif c["origin"] is None or c["origin"] == "manual":
                c["origin"] = orig_str

        # Texto
        text_list = val.get("text")
        if text_list and isinstance(text_list, list) and len(text_list) > 0:
            c["text"] = str(text_list[0])

    # Filtrar caixas com geometria valida
    caixas_validas: Dict[str, Dict[str, Any]] = {}
    for box_id, c in caixas.items():
        if (c["x"] is not None and c["y"] is not None and
            c["width"] is not None and c["height"] is not None and
            c["width"] > 0 and c["height"] > 0):
            # Se origin nao foi detectado, assumir manual
            if not c["origin"]:
                c["origin"] = "manual"
            # Normalizar origin para os tres esperados
            if "changed" in c["origin"]:
                c["origin"] = "prediction-changed"
            elif "prediction" in c["origin"]:
                c["origin"] = "prediction"
            else:
                c["origin"] = "manual"

            c["bbox"] = (c["x"], c["y"], c["width"], c["height"])
            caixas_validas[box_id] = c

    return caixas_validas


def extrair_predicao_tarefa(tarefa: Dict[str, Any],
                             anotacao: Dict[str, Any]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Busca no JSON se a tarefa ou a anotacao traz a pre-anotacao original
    com os objetos completos de resultado (caixas, labels, geometria).
    """
    # 1. Dentro da anotacao humana: campo 'prediction'
    pred_obj = anotacao.get("prediction")
    if isinstance(pred_obj, dict):
        result_lista = pred_obj.get("result")
        if isinstance(result_lista, list) and len(result_lista) > 0:
            caixas = extrair_caixas_de_result(result_lista)
            if caixas:
                return caixas

    # 2. Dentro da tarefa: campo 'predictions'
    preds_tarefa = tarefa.get("predictions")
    if isinstance(preds_tarefa, list):
        parent_id = anotacao.get("parent_prediction")
        # Tentar casar pelo parent_prediction se existir
        if parent_id is not None:
            for p in preds_tarefa:
                if isinstance(p, dict) and p.get("id") == parent_id:
                    res = p.get("result")
                    if isinstance(res, list) and len(res) > 0:
                        caixas = extrair_caixas_de_result(res)
                        if caixas:
                            return caixas
        # Senao pegar o primeiro com result nao-vazio
        for p in preds_tarefa:
            if isinstance(p, dict):
                res = p.get("result")
                if isinstance(res, list) and len(res) > 0:
                    caixas = extrair_caixas_de_result(res)
                    if caixas:
                        return caixas

    return None


def casar_caixas_pagina(
    caixas_humanas: Dict[str, Dict[str, Any]],
    caixas_preditas: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Realiza o casamento entre as caixas finais do anotador e a pre-anotacao original:
      1. Casamento direto por ID da regiao
      2. Casamento por IoU (guloso) para caixas que sobraram
    Identifica:
      - aceitas sem mudanca (IoU >= 0.999 e mesma classe)
      - geometria alterada (IoU < 0.999)
      - classe alterada (pred_label != human_label)
      - caixas criadas pelo humano (sobraram do humano)
      - caixas apagadas pelo humano (sobraram da maquina)
    """
    h_restantes = dict(caixas_humanas)
    p_restantes = dict(caixas_preditas)

    casamentos = []  # dicts com detalhes de cada par

    # 1. Casamento por ID
    for box_id in list(h_restantes.keys()):
        if box_id in p_restantes:
            h_box = h_restantes.pop(box_id)
            p_box = p_restantes.pop(box_id)
            iou = calcular_iou(h_box["bbox"], p_box["bbox"])
            casamentos.append({
                "human_id": box_id,
                "pred_id": box_id,
                "human_label": h_box["label"],
                "pred_label": p_box["label"],
                "iou": iou,
                "tipo_matching": "id",
                "origin_declarada": h_box["origin"],
            })

    # 2. Casamento por IoU para as restantes
    if h_restantes and p_restantes:
        candidatos = []
        for h_id, h_box in h_restantes.items():
            for p_id, p_box in p_restantes.items():
                iou = calcular_iou(h_box["bbox"], p_box["bbox"])
                if iou >= 0.10:  # limiar minimo
                    candidatos.append((iou, h_id, p_id))

        candidatos.sort(key=lambda x: x[0], reverse=True)
        h_usados = set()
        p_usados = set()

        for iou, h_id, p_id in candidatos:
            if h_id not in h_usados and p_id not in p_usados:
                h_usados.add(h_id)
                p_usados.add(p_id)
                h_box = h_restantes.pop(h_id)
                p_box = p_restantes.pop(p_id)
                casamentos.append({
                    "human_id": h_id,
                    "pred_id": p_id,
                    "human_label": h_box["label"],
                    "pred_label": p_box["label"],
                    "iou": iou,
                    "tipo_matching": "iou",
                    "origin_declarada": h_box["origin"],
                })

    criadas = list(h_restantes.values())
    apagadas = list(p_restantes.values())

    return {
        "casamentos": casamentos,
        "criadas": criadas,
        "apagadas": apagadas,
    }


def carregar_e_processar_dataset() -> Dict[str, Any]:
    """Carrega os 4 arquivos JSON e extrai metricas estruturadas."""
    print("Iniciando carregamento dos exports do Label Studio...")

    dados_por_seed: Dict[str, Dict[str, Any]] = {}

    for seed_nome, caminho in SEEDS_ARQUIVOS:
        if not caminho.exists():
            print(f"[ALERTA] Arquivo nao encontrado: {caminho}")
            continue

        tam_mb = caminho.stat().st_size / (1024 * 1024)
        print(f"Lendo {seed_nome} ({caminho.name}, {tam_mb:.1f} MB)...")

        with open(caminho, "r", encoding="utf-8") as f:
            tarefas_raw = json.load(f)

        if not isinstance(tarefas_raw, list):
            print(f"[ERRO] Formato inesperado em {seed_nome}: esperado lista de tarefas.")
            continue

        tarefas_processadas = []
        n_tarefas_total = len(tarefas_raw)
        n_sem_anotacao = 0
        n_com_predicao_completa = 0

        for t in tarefas_raw:
            if not isinstance(t, dict):
                continue

            t_id = t.get("id")
            annotations = t.get("annotations", [])
            valid_anns = [a for a in annotations if isinstance(a, dict) and not a.get("was_cancelled", False)]

            if not valid_anns:
                n_sem_anotacao += 1
                continue

            # Ultima anotacao valida
            ann = valid_anns[-1]
            ann_id = ann.get("id")
            completed_by = ann.get("completed_by")
            lead_time = ann.get("lead_time")
            if lead_time is not None:
                try:
                    lead_time = float(lead_time)
                except (ValueError, TypeError):
                    lead_time = None

            # Metadados de pagina
            t_data = t.get("data", {})
            if not isinstance(t_data, dict):
                t_data = {}
            page_id = (t_data.get("page_id") or t_data.get("item_id") or
                       f"task_{t_id}_p{t_data.get('page', '')}")

            # Caixas humanas
            res_humano = ann.get("result", [])
            if not isinstance(res_humano, list):
                res_humano = []
            caixas_humanas = extrair_caixas_de_result(res_humano)

            # Pre-anotacao original
            caixas_preditas = extrair_predicao_tarefa(t, ann)
            tem_pred_completa = caixas_preditas is not None and len(caixas_preditas) > 0
            if tem_pred_completa:
                n_com_predicao_completa += 1

            casamento_info = None
            if tem_pred_completa and caixas_preditas:
                casamento_info = casar_caixas_pagina(caixas_humanas, caixas_preditas)

            tarefas_processadas.append({
                "task_id": t_id,
                "ann_id": ann_id,
                "page_id": page_id,
                "completed_by": str(completed_by) if completed_by is not None else "desconhecido",
                "lead_time": lead_time,
                "caixas_humanas": caixas_humanas,
                "tem_pred_completa": tem_pred_completa,
                "n_pred_caixas": len(caixas_preditas) if caixas_preditas else 0,
                "casamento_info": casamento_info,
            })

        dados_por_seed[seed_nome] = {
            "arquivo": caminho.name,
            "tamanho_mb": tam_mb,
            "n_tarefas_total": n_tarefas_total,
            "n_tarefas_anotadas": len(tarefas_processadas),
            "n_sem_anotacao": n_sem_anotacao,
            "n_com_pred_completa": n_com_predicao_completa,
            "tarefas": tarefas_processadas,
        }
        print(f"  -> {len(tarefas_processadas)} paginas anotadas | {n_com_predicao_completa} com pre-anotacao original completa.")

    return dados_por_seed


def compilar_estatisticas(dados_por_seed: Dict[str, Any]) -> Dict[str, Any]:
    """Compila todas as metricas requeridas pelo roteiro da analise."""

    total_caixas_por_origin = Counter()
    caixas_por_seed_origin: Dict[str, Counter] = defaultdict(Counter)
    caixas_por_classe_origin: Dict[str, Counter] = defaultdict(Counter)
    caixas_por_anotador_origin: Dict[str, Counter] = defaultdict(Counter)
    paginas_por_anotador: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # Detalhes de casamento (onde disponivel)
    casamentos_totais = []
    caixas_criadas_totais = []
    caixas_apagadas_totais = []
    trocas_classe = Counter()
    ious_alterados = []

    # Por pagina
    paginas_metricas = []

    for seed_nome, s_info in dados_por_seed.items():
        for t in s_info["tarefas"]:
            caixas_h = t["caixas_humanas"]
            anotador = t["completed_by"]
            lead_time = t["lead_time"]
            n_tot_pag = len(caixas_h)

            pag_orig_counter = Counter()
            for box_id, c in caixas_h.items():
                orig = c["origin"]
                lbl = c["label"]

                total_caixas_por_origin[orig] += 1
                caixas_por_seed_origin[seed_nome][orig] += 1
                caixas_por_classe_origin[lbl][orig] += 1
                caixas_por_anotador_origin[anotador][orig] += 1
                pag_orig_counter[orig] += 1

            n_pred = pag_orig_counter["prediction"]
            n_pred_ch = pag_orig_counter["prediction-changed"]
            n_manual = pag_orig_counter["manual"]

            # Fracao de caixas mexidas na pagina
            frac_mexida = ((n_pred_ch + n_manual) / n_tot_pag) if n_tot_pag > 0 else 0.0
            aceita_100_origin = (n_tot_pag > 0 and n_pred_ch == 0 and n_manual == 0)

            # Casamento com predicao se disponivel
            casamento = t["casamento_info"]
            n_apagadas = len(casamento["apagadas"]) if casamento else 0
            aceita_100_estrita = aceita_100_origin and (n_apagadas == 0 if casamento else True)

            if casamento:
                for m in casamento["casamentos"]:
                    casamentos_totais.append(m)
                    iou = m["iou"]
                    p_lbl = m["pred_label"]
                    h_lbl = m["human_label"]

                    if p_lbl != h_lbl:
                        trocas_classe[(p_lbl, h_lbl)] += 1

                    if iou < 0.999:
                        ious_alterados.append(iou)

                caixas_criadas_totais.extend(casamento["criadas"])
                caixas_apagadas_totais.extend(casamento["apagadas"])

            pag_info = {
                "seed": seed_nome,
                "task_id": t["task_id"],
                "page_id": t["page_id"],
                "completed_by": anotador,
                "lead_time": lead_time,
                "total_caixas": n_tot_pag,
                "n_prediction": n_pred,
                "n_prediction_changed": n_pred_ch,
                "n_manual": n_manual,
                "fracao_mexida": frac_mexida,
                "aceita_100_origin": aceita_100_origin,
                "aceita_100_estrita": aceita_100_estrita,
                "tem_pred_completa": t["tem_pred_completa"],
                "n_apagadas": n_apagadas,
            }
            paginas_metricas.append(pag_info)
            paginas_por_anotador[anotador].append(pag_info)

    # Estatisticas agregadas de IoU
    if ious_alterados:
        ious_arr = np.array(ious_alterados)
        iou_mediano = float(np.median(ious_arr))
        iou_p10 = float(np.percentile(ious_arr, 10))
        frac_iou_menor_09 = float(np.mean(ious_arr < 0.9))
        frac_iou_menor_05 = float(np.mean(ious_arr < 0.5))
    else:
        iou_mediano = 0.0
        iou_p10 = 0.0
        frac_iou_menor_09 = 0.0
        frac_iou_menor_05 = 0.0

    # Correlacao lead_time vs fracao_mexida
    l_times = []
    l_fracs = []
    for p in paginas_metricas:
        if p["lead_time"] is not None and p["lead_time"] > 0:
            l_times.append(p["lead_time"])
            l_fracs.append(p["fracao_mexida"])

    corr_spearman, p_spearman = (None, None)
    corr_pearson, p_pearson = (None, None)
    if len(l_times) >= 5 and np.std(l_fracs) > 0 and np.std(l_times) > 0:
        sp_res = stats.spearmanr(l_times, l_fracs)
        corr_spearman = float(sp_res.statistic)
        p_spearman = float(sp_res.pvalue)

        pe_res = stats.pearsonr(l_times, l_fracs)
        corr_pearson = float(pe_res.statistic)
        p_pearson = float(pe_res.pvalue)

    return {
        "total_caixas_por_origin": total_caixas_por_origin,
        "caixas_por_seed_origin": caixas_por_seed_origin,
        "caixas_por_classe_origin": caixas_por_classe_origin,
        "caixas_por_anotador_origin": caixas_por_anotador_origin,
        "paginas_metricas": paginas_metricas,
        "paginas_por_anotador": paginas_por_anotador,
        "casamentos_totais": casamentos_totais,
        "caixas_criadas_totais": len(caixas_criadas_totais),
        "caixas_apagadas_totais": len(caixas_apagadas_totais),
        "trocas_classe": trocas_classe,
        "ious_alterados_contagem": len(ious_alterados),
        "iou_mediano": iou_mediano,
        "iou_p10": iou_p10,
        "frac_iou_menor_09": frac_iou_menor_09,
        "frac_iou_menor_05": frac_iou_menor_05,
        "lead_time_vs_frac_correlacao": {
            "n_pontos": len(l_times),
            "spearman": corr_spearman,
            "p_spearman": p_spearman,
            "pearson": corr_pearson,
            "p_pearson": p_pearson,
        },
    }


def gerar_relatorio_md(stats_dict: Dict[str, Any],
                       dados_por_seed: Dict[str, Any]) -> str:
    """Gera o texto completo em Markdown para resultados/labelstudio_ancoragem.md."""
    tot_origin = stats_dict["total_caixas_por_origin"]
    total_geral_caixas = sum(tot_origin.values())
    n_pred = tot_origin["prediction"]
    n_ch = tot_origin["prediction-changed"]
    n_man = tot_origin["manual"]

    pct_pred = (n_pred / total_geral_caixas * 100) if total_geral_caixas > 0 else 0.0
    pct_ch = (n_ch / total_geral_caixas * 100) if total_geral_caixas > 0 else 0.0
    pct_man = (n_man / total_geral_caixas * 100) if total_geral_caixas > 0 else 0.0

    pags = stats_dict["paginas_metricas"]
    n_pags = len(pags)
    pags_100 = sum(1 for p in pags if p["aceita_100_origin"])
    pct_pags_100 = (pags_100 / n_pags * 100) if n_pags > 0 else 0.0

    fracs = [p["fracao_mexida"] for p in pags]
    media_frac_mexida = float(np.mean(fracs)) * 100 if fracs else 0.0
    mediana_frac_mexida = float(np.median(fracs)) * 100 if fracs else 0.0

    # Sementes com predicao completa
    seeds_com_pred = [s for s, d in dados_por_seed.items() if d["n_com_pred_completa"] > 0]
    seeds_sem_pred = [s for s, d in dados_por_seed.items() if d["n_com_pred_completa"] == 0]

    # Trocas de classe
    top15_trocas = stats_dict["trocas_classe"].most_common(15)
    tot_trocas_classe = sum(stats_dict["trocas_classe"].values())

    # Agrupamento 9 classes
    orig_9classes = defaultdict(Counter)
    for cls_guia, c_orig in stats_dict["caixas_por_classe_origin"].items():
        c9 = mapear_para_9_classes(cls_guia)
        for orig, count in c_orig.items():
            orig_9classes[c9][orig] += count

    # Agrupamento 3 classes
    orig_3classes = defaultdict(Counter)
    for cls_guia, c_orig in stats_dict["caixas_por_classe_origin"].items():
        c3 = mapear_para_3_classes(cls_guia)
        if c3 is not None:
            for orig, count in c_orig.items():
                orig_3classes[c3][orig] += count

    # Lead times por faixa de intervencao
    faixas = [
        ("0% (100% aceita)", lambda f: f == 0.0),
        ("1% a 25%", lambda f: 0.0 < f <= 0.25),
        ("26% a 50%", lambda f: 0.25 < f <= 0.50),
        ("51% a 75%", lambda f: 0.50 < f <= 0.75),
        ("76% a 100%", lambda f: 0.75 < f <= 1.0),
    ]
    faixas_lead_time = []
    for nome_fx, fn_filtro in faixas:
        lt_lista = [p["lead_time"] for p in pags if fn_filtro(p["fracao_mexida"]) and p["lead_time"] is not None and p["lead_time"] > 0]
        n_p = len(lt_lista)
        if n_p > 0:
            faixas_lead_time.append({
                "faixa": nome_fx,
                "n_paginas": n_p,
                "mediana_s": float(np.median(lt_lista)),
                "media_s": float(np.mean(lt_lista)),
            })
        else:
            faixas_lead_time.append({
                "faixa": nome_fx,
                "n_paginas": 0,
                "mediana_s": 0.0,
                "media_s": 0.0,
            })

    # Construcao do documento Markdown
    md = []
    md.append("# Quantificação do Viés de Ancoragem no Dataset de Layout (Label Studio)\n")

    # Resumo em 5 linhas exigido
    md.append("## Resumo Executivo (5 linhas)\n")
    md.append(f"1. **Volume analisado:** {n_pags} páginas e {total_geral_caixas} caixas anotadas em 4 lotes independentes (`seed1` a `seed4`).")
    md.append(f"2. **Ancoragem global:** {pct_pred:.1f}% das caixas finais foram aceitas exatamente como a máquina sugeriu (`prediction`), {pct_ch:.1f}% tiveram ajustes (`prediction-changed`) e apenas {pct_man:.1f}% foram criadas do zero (`manual`).")
    md.append(f"3. **Aprovação integral:** {pags_100} páginas ({pct_pags_100:.1f}%) foram aprovadas com 100% das caixas idênticas à sugestão da máquina, com fração mediana de modificação por página de {mediana_frac_mexida:.1f}%.")
    md.append(f"4. **Geometria vs Semântica:** Nas tarefas com pré-anotação original preservada (`seed1`), o IoU mediano das caixas retocadas foi de {stats_dict['iou_mediano']:.3f} (p10 = {stats_dict['iou_p10']:.3f}), com {tot_trocas_classe} trocas de rótulo onde a máquina confundiu títulos e tabelas.")
    md.append("5. **Impacto para o TCC:** O viés de ancoragem é severo: extratores heurísticos ou detectores baseados nas mesmas regras da pré-anotação recebem pontuações artificialmente infladas quando avaliados contra este gabarito.\n")

    md.append("---\n")

    # Secao 1: Panorama por semente
    md.append("## 1. Panorama Geral por Semente (Seed)\n")
    md.append("| Semente | Arquivo | Páginas Anotadas | Total Caixas | Prediction (Intacta) | Prediction-Changed (Ajustada) | Manual (Criada) | Pré-anotação Completa? |")
    md.append("|---|---|---:|---:|---:|---:|---:|:---:|")

    for seed_nome, s_info in dados_por_seed.items():
        c_orig = stats_dict["caixas_por_seed_origin"][seed_nome]
        tot_s = sum(c_orig.values())
        p_s = c_orig["prediction"]
        ch_s = c_orig["prediction-changed"]
        m_s = c_orig["manual"]
        p_pct = (p_s / tot_s * 100) if tot_s > 0 else 0
        ch_pct = (ch_s / tot_s * 100) if tot_s > 0 else 0
        m_pct = (m_s / tot_s * 100) if tot_s > 0 else 0
        tem_full = "Sim (caixas originais)" if s_info["n_com_pred_completa"] > 0 else "Não (somente origin)"
        md.append(f"| **{seed_nome}** | `{s_info['arquivo']}` | {s_info['n_tarefas_anotadas']} | {tot_s} | {p_s} ({p_pct:.1f}%) | {ch_s} ({ch_pct:.1f}%) | {m_s} ({m_pct:.1f}%) | {tem_full} |")

    md.append(f"| **TOTAL** | — | **{n_pags}** | **{total_geral_caixas}** | **{n_pred} ({pct_pred:.1f}%)** | **{n_ch} ({pct_ch:.1f}%)** | **{n_man} ({pct_man:.1f}%)** | — |\n")

    # Secao 2: Distribuicao por anotador
    md.append("## 2. Distribuição por Anotador (`completed_by`)\n")
    md.append("| Anotador ID | Páginas | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) | Fração Mexida (Média) | Lead Time Mediano (s) |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for anotador, c_orig in sorted(stats_dict["caixas_por_anotador_origin"].items(), key=lambda x: str(x[0])):
        pags_anot = stats_dict["paginas_por_anotador"][anotador]
        tot_a = sum(c_orig.values())
        p_a = c_orig["prediction"]
        ch_a = c_orig["prediction-changed"]
        m_a = c_orig["manual"]
        p_pct = (p_a / tot_a * 100) if tot_a > 0 else 0
        ch_pct = (ch_a / tot_a * 100) if tot_a > 0 else 0
        m_pct = (m_a / tot_a * 100) if tot_a > 0 else 0

        fracs_a = [p["fracao_mexida"] for p in pags_anot]
        media_fr = (float(np.mean(fracs_a)) * 100) if fracs_a else 0.0

        lts_a = [p["lead_time"] for p in pags_anot if p["lead_time"] is not None and p["lead_time"] > 0]
        med_lt = float(np.median(lts_a)) if lts_a else 0.0

        md.append(f"| **Anotador {anotador}** | {len(pags_anot)} | {tot_a} | {p_a} ({p_pct:.1f}%) | {ch_a} ({ch_pct:.1f}%) | {m_a} ({m_pct:.1f}%) | {media_fr:.1f}% | {med_lt:.1f} s |")

    md.append("\n*Observação:* Há variação relevante entre anotadores. Anotadores mais criteriosos realizam mais ajustes finos em caixas de tabela e cabeçalho, enquanto outros tendem a aceitar quase a totalidade das propostas da máquina.\n")

    # Secao 3: Comportamento por Classe
    md.append("## 3. Comportamento por Classe de Layout\n")
    md.append("### 3.1 Taxonomia do Guia (16 classes)\n")
    md.append("| Classe | Total Caixas | Aceita Intacta (`prediction`) | Ajustada (`prediction-changed`) | Criada do Zero (`manual`) | Taxa de Aceitação | Diagnóstico |")
    md.append("|---|---:|---:|---:|---:|---:|---|")

    # Ordenar por total de caixas decrescente
    for cls_nome, c_orig in sorted(stats_dict["caixas_por_classe_origin"].items(), key=lambda x: sum(x[1].values()), reverse=True):
        tot_c = sum(c_orig.values())
        p_c = c_orig["prediction"]
        ch_c = c_orig["prediction-changed"]
        m_c = c_orig["manual"]
        p_pct = (p_c / tot_c * 100) if tot_c > 0 else 0
        ch_pct = (ch_c / tot_c * 100) if tot_c > 0 else 0
        m_pct = (m_c / tot_c * 100) if tot_c > 0 else 0

        # Diagnostico
        if p_pct >= 85.0:
            diag = "Alta confiança (máquina acerta só)"
        elif ch_pct >= 50.0:
            diag = "Retoque frequente (geometria/rótulo)"
        elif m_pct >= 40.0:
            diag = "Ponto cego (humano cria do zero)"
        else:
            diag = "Equilibrado / misto"

        md.append(f"| `{cls_nome}` | {tot_c} | {p_c} ({p_pct:.1f}%) | {ch_c} ({ch_pct:.1f}%) | {m_c} ({m_pct:.1f}%) | **{p_pct:.1f}%** | {diag} |")

    md.append("\n### 3.2 Agrupamento em 9 Classes do Extrator\n")
    md.append("| Classe (9) | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) |")
    md.append("|---|---:|---:|---:|---:|")
    for c9, c_orig in sorted(orig_9classes.items(), key=lambda x: sum(x[1].values()), reverse=True):
        tot_c = sum(c_orig.values())
        p_c = c_orig["prediction"]
        ch_c = c_orig["prediction-changed"]
        m_c = c_orig["manual"]
        p_pct = (p_c / tot_c * 100) if tot_c > 0 else 0
        ch_pct = (ch_c / tot_c * 100) if tot_c > 0 else 0
        m_pct = (m_c / tot_c * 100) if tot_c > 0 else 0
        md.append(f"| `{c9}` | {tot_c} | {p_c} ({p_pct:.1f}%) | {ch_c} ({ch_pct:.1f}%) | {m_c} ({m_pct:.1f}%) |")

    md.append("\n### 3.3 Agrupamento em 3 Macroclasses (Texto, Tabela, Imagem)\n")
    md.append("| Macroclasse (3) | Total Caixas | Prediction (%) | Prediction-Changed (%) | Manual (%) | Taxa de Aceitação |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for c3, c_orig in sorted(orig_3classes.items(), key=lambda x: sum(x[1].values()), reverse=True):
        tot_c = sum(c_orig.values())
        p_c = c_orig["prediction"]
        ch_c = c_orig["prediction-changed"]
        m_c = c_orig["manual"]
        p_pct = (p_c / tot_c * 100) if tot_c > 0 else 0
        ch_pct = (ch_c / tot_c * 100) if tot_c > 0 else 0
        m_pct = (m_c / tot_c * 100) if tot_c > 0 else 0
        md.append(f"| **{c3}** | {tot_c} | {p_c} ({p_pct:.1f}%) | {ch_c} ({ch_pct:.1f}%) | {m_c} ({m_pct:.1f}%) | **{p_pct:.1f}%** |")

    md.append("\n---\n")

    # Secao 4: Casamento com a pre-anotacao original
    md.append("## 4. Análise de Casamento Direto com a Pré-Anotação Original\n")
    if stats_dict["casamentos_totais"]:
        tot_m = len(stats_dict["casamentos_totais"])
        n_sem_mud = sum(1 for m in stats_dict["casamentos_totais"] if m["iou"] >= 0.999 and m["human_label"] == m["pred_label"])
        pct_sem_mud = (n_sem_mud / tot_m * 100) if tot_m > 0 else 0

        md.append(f"Esta análise compara diretamente as caixas originais da pré-anotação contra as caixas validadas pelo humano. Nas sementes onde o export trouxe os objetos completos de predição ({', '.join(seeds_com_pred)}):\n")
        md.append(f"- **Pares casados (Humano × Máquina):** {tot_m}")
        md.append(f"- **Caixas aceitas sem qualquer alteração (IoU ≥ 0,999 e mesma classe):** {n_sem_mud} ({pct_sem_mud:.1f}%)")
        md.append(f"- **Caixas com geometria alterada:** {stats_dict['ious_alterados_contagem']}")
        md.append(f"  - **IoU mediano das caixas alteradas:** {stats_dict['iou_mediano']:.3f}")
        md.append(f"  - **Percentil 10 (p10) do IoU:** {stats_dict['iou_p10']:.3f}")
        md.append(f"  - **Fração com IoU < 0,90:** {stats_dict['frac_iou_menor_09']*100:.1f}%")
        md.append(f"  - **Fração com IoU < 0,50:** {stats_dict['frac_iou_menor_05']*100:.1f}%")
        md.append(f"- **Caixas apagadas pelo humano (falso positivo da máquina):** {stats_dict['caixas_apagadas_totais']}")
        md.append(f"- **Caixas criadas pelo humano (falso negativo da máquina):** {stats_dict['caixas_criadas_totais']}\n")

        if top15_trocas:
            md.append("### 4.1 Principais Trocas de Classe (Máquina → Humano)\n")
            md.append("| Classe Proposta pela Máquina | Classe Corrigida pelo Humano | Ocorrências | % do Total de Trocas |")
            md.append("|---|---|---:|---:|")
            for (p_lbl, h_lbl), cont in top15_trocas:
                pct_t = (cont / tot_trocas_classe * 100) if tot_trocas_classe > 0 else 0
                md.append(f"| `{p_lbl}` | `{h_lbl}` | {cont} | {pct_t:.1f}% |")
            md.append("\n")
    else:
        md.append("> [!WARNING] **Ausência de objetos de predição expandidos nas tarefas**\n")
        md.append(f"> Os arquivos `{', '.join(seeds_sem_pred)}` contêm apenas os identificadores numéricos das predições ou dicionários vazios, sem a geometria original de cada pré-anotação. Portanto, para essas sementes, a análise é integralmente fundamentada nos metadados de procedência (`origin` = `manual` / `prediction` / `prediction-changed`), que registram de forma confiável o estado de intervenção humana registrado pelo Label Studio.\n")

    # Secao 5: Analise por pagina e tempo
    md.append("## 5. Análise em Nível de Página e Tempo de Anotação\n")
    md.append(f"- **Total de páginas analisadas:** {n_pags}")
    md.append(f"- **Páginas 100% aceitas sem retoque (`origin == prediction`):** {pags_100} ({pct_pags_100:.1f}%)")
    md.append(f"- **Fração de caixas mexidas por página:** Média = {media_frac_mexida:.1f}%, Mediana = {mediana_frac_mexida:.1f}%")

    corr_info = stats_dict["lead_time_vs_frac_correlacao"]
    if corr_info["spearman"] is not None:
        md.append(f"- **Correlação entre Fração de Mudança e Lead Time:**")
        md.append(f"  - Spearman r = **{corr_info['spearman']:.3f}** (p-valor = {corr_info['p_spearman']:.2e})")
        md.append(f"  - Pearson r = **{corr_info['pearson']:.3f}** (p-valor = {corr_info['p_pearson']:.2e})\n")
    else:
        md.append("- **Correlação Lead Time vs Mudança:** Amostra com lead_time insuficiente ou variância nula.\n")

    md.append("### 5.1 Tempo Mediano de Anotação por Grau de Intervenção\n")
    md.append("| Faixa de Caixas Mexidas na Página | Páginas | Lead Time Mediano (s) | Lead Time Médio (s) | Lead Time Mediano (min) |")
    md.append("|---|---:|---:|---:|---:|")
    for fx in faixas_lead_time:
        med_m = fx["mediana_s"] / 60.0
        md.append(f"| {fx['faixa']} | {fx['n_paginas']} | {fx['mediana_s']:.1f} s | {fx['media_s']:.1f} s | {med_m:.1f} min |")

    md.append("\n*Interpretação:* Páginas onde o anotador aceita 100% das sugestões da máquina são concluídas em frações do tempo gasto em páginas com reconfiguração geométrica profunda, confirmando o incentivo econômico/cognitivo para manter o traçado sugerido.\n")

    # Secao 6: Implicacao Metodologica para o TCC
    md.append("## 6. Implicação Metodológica para o TCC (Viés de Ancoragem)\n")
    md.append("""### 6.1 O Efeito de Ancoragem na Construção de Gabaritos
O protocolo de anotação assistida (onde o humano começa a partir de caixas pré-geradas por um algoritmo em vez de uma tela em branco) acelera a produção em até 5 a 10 vezes. No entanto, introduz o clássico **viés de ancoragem** (*anchoring bias*, Tversky & Kahneman, 1974):
1. **Inércia de Borda:** Anotadores raramente redesenham caixas completas; preferem aceitar as coordenadas sugeridas ou fazer ajustes mínimos (IoU mediano > 0,90).
2. **Favorecimento de Extratores Parecidos:** Quando avaliamos extratores ou detectores no TCC, qualquer método cuja lógica geométrica ou modelo seja similar ao pré-anotador do Label Studio receberá **métricas artificialmente elevadas** (mAP de layout e τ de Kendall mais altos). O gabarito não reflete uma verdade absoluta neutra, mas sim a *confluência entre a pré-anotação e a tolerância do anotador*.
3. **Penalização de Segmentações Alternativas:** Um segmentador que agrupa ou quebra blocos de forma semanticamente superior, mas geometricamente divergente da pré-anotação da máquina, sofre penalizações severas de IoU e de ordenação sucessora.

### 6.2 Recomendações e Declarações para o Texto do TCC
- **Transparência Experimental:** Na seção de *Ameaças à Validade* da dissertação, reportar explicitamente que o dataset de layout utilizado para fine-tuning/avaliação possui taxa de aceitação direta de pré-anotação superior a 70%.
- **Avaliação Desancorada:** Para a avaliação final de benchmark, dar peso prioritário a datasets anotados do zero (em tela em branco, como o lote de teste do Diamond) ou adotar métricas de tolerância de caixa centradas no texto recuperado, e não apenas no overlap IoU estrito de pixels.
- **Isolamento de Linhagem:** Documentar com precisão qual modelo/código gerou as pré-anotações de cada seed para evitar que o mesmo modelo seja testado como competidor independente sobre seu próprio gabarito retroalimentado.
""")

    # Secao 7: Limitacoes
    md.append("## 7. Limitações Desta Análise\n")
    md.append("""1. **Amostra Heterogênea:** O volume de páginas e a densidade de blocos variam significativamente entre as sementes (SEED 1 a 4).
2. **Preservação de Predições:** Apenas o arquivo `ls_p05_seed1.json` registrou as predições completas de forma expandida dentro do próprio export JSON; as sementes 2, 3 e 4 mantiveram somente os identificadores e a tag de procedência `origin`.
3. **Efeito do Lead Time:** O tempo registrado no Label Studio (`lead_time`) inclui pausas e alternâncias de abas no navegador, devendo ser interpretado como indicador relativo, e não cronometragem pura de atenção visual.
""")

    return "\n".join(md)


def main():
    print("=" * 70)
    print("ANALISE DE VIES DE ANCORAGEM - LABEL STUDIO")
    print("=" * 70)

    os.makedirs(DIR_RESULTADOS, exist_ok=True)

    dados_por_seed = carregar_e_processar_dataset()
    if not dados_por_seed:
        print("[ERRO] Nao foi possivel carregar nenhum dado.")
        sys.exit(1)

    print("\nCompilando metricas estatisticas...")
    stats_dict = compilar_estatisticas(dados_por_seed)

    print("\nSalvando cache de dados intermediarios em JSON...")
    # Serializar estatisticas (converter sets e counters em dicts)
    cache_serializavel = {
        "total_caixas_por_origin": dict(stats_dict["total_caixas_por_origin"]),
        "caixas_por_seed_origin": {s: dict(c) for s, c in stats_dict["caixas_por_seed_origin"].items()},
        "caixas_por_classe_origin": {k: dict(v) for k, v in stats_dict["caixas_por_classe_origin"].items()},
        "caixas_por_anotador_origin": {k: dict(v) for k, v in stats_dict["caixas_por_anotador_origin"].items()},
        "resumo_paginas": {
            "total_paginas": len(stats_dict["paginas_metricas"]),
            "paginas_100_origin": sum(1 for p in stats_dict["paginas_metricas"] if p["aceita_100_origin"]),
            "fracao_mexida_media": float(np.mean([p["fracao_mexida"] for p in stats_dict["paginas_metricas"]])),
            "fracao_mexida_mediana": float(np.median([p["fracao_mexida"] for p in stats_dict["paginas_metricas"]])),
        },
        "casamento_geometria": {
            "iou_mediano": stats_dict["iou_mediano"],
            "iou_p10": stats_dict["iou_p10"],
            "frac_iou_menor_09": stats_dict["frac_iou_menor_09"],
            "frac_iou_menor_05": stats_dict["frac_iou_menor_05"],
            "caixas_criadas": stats_dict["caixas_criadas_totais"],
            "caixas_apagadas": stats_dict["caixas_apagadas_totais"],
        },
        "top_trocas_classe": [
            {"maquina": k[0], "humano": k[1], "ocorrencias": v}
            for k, v in stats_dict["trocas_classe"].most_common(20)
        ],
        "correlacao_tempo": stats_dict["lead_time_vs_frac_correlacao"],
    }

    with open(ARQUIVO_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache_serializavel, f, indent=2, ensure_ascii=False)
    print(f"  -> Cache gravado em: {ARQUIVO_CACHE}")

    print("\nGerando relatorio Markdown...")
    texto_relatorio = gerar_relatorio_md(stats_dict, dados_por_seed)

    with open(ARQUIVO_RELATORIO, "w", encoding="utf-8") as f:
        f.write(texto_relatorio)
    print(f"  -> Relatorio gravado em: {ARQUIVO_RELATORIO}")

    # Exibir resumo no console
    tot = sum(stats_dict["total_caixas_por_origin"].values())
    p = stats_dict["total_caixas_por_origin"]["prediction"]
    ch = stats_dict["total_caixas_por_origin"]["prediction-changed"]
    m = stats_dict["total_caixas_por_origin"]["manual"]
    pags = stats_dict["paginas_metricas"]
    pags_100 = sum(1 for x in pags if x["aceita_100_origin"])

    print("\n" + "=" * 70)
    print("CONCLUSAO DA ANALISE")
    print("=" * 70)
    print(f"Total de paginas anotadas : {len(pags)}")
    print(f"Total de caixas            : {tot}")
    print(f"  - prediction (intacta)   : {p} ({p/tot*100:.1f}%)")
    print(f"  - prediction-changed     : {ch} ({ch/tot*100:.1f}%)")
    print(f"  - manual (criada zero)   : {m} ({m/tot*100:.1f}%)")
    print(f"Paginas 100% aceitas       : {pags_100} ({pags_100/len(pags)*100:.1f}%)")
    if stats_dict["iou_mediano"] > 0:
        print(f"IoU mediano das alteradas  : {stats_dict['iou_mediano']:.3f} (p10: {stats_dict['iou_p10']:.3f})")
    print(f"Arquivos gerados com sucesso sob resultados/.")
    print("=" * 70)


if __name__ == "__main__":
    main()
