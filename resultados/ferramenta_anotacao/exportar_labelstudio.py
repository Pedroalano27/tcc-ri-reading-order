# -*- coding: utf-8 -*-
"""Conversor bidirecional entre o formato próprio do TCC e o formato Label Studio.

Este módulo permite converter tarefas e anotações entre:
  1. Formato Próprio (JSON simples):
     Lista de páginas com:
       - page_id: identificador da página
       - imagem: nome do arquivo ou URI da imagem
       - largura / altura: dimensões da página em pixels
       - caixas: lista de caixas [{id, bbox: [x0, y0, x1, y1], classe, texto?}]
       - ordem: lista de IDs na sequência de leitura [id_1, id_2, ...]
       - relacoes: lista opcional de relações [{de, para, tipo}]
       - flags, nota, motivo_pulo, tempo_s
  2. Formato Label Studio (JSON de anotações exportadas):
     Lista de tarefas com data, annotations e result contendo:
       - rectanglelabels / rectangle (coordenadas percentuais x, y, width, height)
       - textarea (conteúdo textual opcional)
       - relation (de -> para, direction, labels)

Pode ser executado diretamente para rodar o teste de validação de ida e volta:
    venv/Scripts/python.exe -B resultados/ferramenta_anotacao/exportar_labelstudio.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def normalizar_bbox(bbox: List[Union[int, float]]) -> List[float]:
    """Garante bbox no formato [x0, y0, x1, y1] com floats."""
    x0, y0, x1, y1 = [float(v) for v in bbox]
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def proprio_para_ls(dados_proprio: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converte do formato próprio simples para o formato de exportação do Label Studio.

    Parâmetros:
        dados_proprio: lista de páginas ou dicionário único de página no formato próprio.

    Retorna:
        Lista de tarefas no formato Label Studio importável.
    """
    if isinstance(dados_proprio, dict):
        if "tasks" in dados_proprio and isinstance(dados_proprio["tasks"], list):
            paginas = dados_proprio["tasks"]
        elif "paginas" in dados_proprio and isinstance(dados_proprio["paginas"], list):
            paginas = dados_proprio["paginas"]
        else:
            paginas = [dados_proprio]
    elif isinstance(dados_proprio, list):
        paginas = dados_proprio
    else:
        raise ValueError(f"Formato próprio inválido: esperado list ou dict, recebido {type(dados_proprio)}")

    tarefas_ls: List[Dict[str, Any]] = []

    for idx, pag in enumerate(paginas, start=1):
        page_id = str(pag.get("page_id") or f"pagina_{idx}")
        imagem = pag.get("imagem") or pag.get("image") or f"{page_id}.png"
        W = float(pag.get("largura") or pag.get("width") or 1000.0)
        H = float(pag.get("altura") or pag.get("height") or 1000.0)
        if W <= 0:
            W = 1000.0
        if H <= 0:
            H = 1000.0

        caixas = pag.get("caixas") or pag.get("bounding_boxes") or []
        ordem = [str(x) for x in (pag.get("ordem") or [])]
        relacoes = pag.get("relacoes") or []
        tempo_s = float(pag.get("tempo_s") or 0.0)
        nota = pag.get("nota") or ""
        flags = pag.get("flags") or []

        result_items: List[Dict[str, Any]] = []

        # 1. Caixas delimitadoras (rectanglelabels e textarea)
        for cx in caixas:
            cid = str(cx["id"])
            classe = str(cx.get("classe") or cx.get("label") or "texto")
            bbox = normalizar_bbox(cx["bbox"])
            x0, y0, x1, y1 = bbox
            w_px = max(x1 - x0, 0.1)
            h_px = max(y1 - y0, 0.1)

            # Conversão para porcentagem [0..100]
            pct_x = (x0 / W) * 100.0
            pct_y = (y0 / H) * 100.0
            pct_w = (w_px / W) * 100.0
            pct_h = (h_px / H) * 100.0

            item_retangulo = {
                "id": cid,
                "type": "rectanglelabels",
                "value": {
                    "x": round(pct_x, 6),
                    "y": round(pct_y, 6),
                    "width": round(pct_w, 6),
                    "height": round(pct_h, 6),
                    "rotation": 0,
                    "rectanglelabels": [classe],
                },
                "original_width": int(round(W)),
                "original_height": int(round(H)),
                "from_name": "label",
                "to_name": "image",
            }
            result_items.append(item_retangulo)

            # Texto opcional
            texto = cx.get("texto") or cx.get("text")
            if texto:
                item_texto = {
                    "id": cid,
                    "type": "textarea",
                    "value": {
                        "text": [str(texto)],
                    },
                    "from_name": "transcription",
                    "to_name": "image",
                }
                result_items.append(item_texto)

        # 2. Relações de ordem de leitura
        # Se temos uma lista de relações explícitas, usamos elas; caso contrário, geramos a cadeia da 'ordem'
        pares_rel: List[Tuple[str, str, str]] = []
        if relacoes:
            for r in relacoes:
                de = str(r.get("de") or r.get("from_id") or "")
                para = str(r.get("para") or r.get("to_id") or "")
                tipo = str(r.get("tipo") or r.get("label") or "continue")
                if de and para:
                    pares_rel.append((de, para, tipo))
        elif len(ordem) >= 2:
            for a, b in zip(ordem, ordem[1:]):
                pares_rel.append((a, b, "continue"))

        for de, para, tipo in pares_rel:
            item_rel = {
                "type": "relation",
                "from_id": de,
                "to_id": para,
                "direction": "right",
                "labels": [tipo],
            }
            result_items.append(item_rel)

        annotation = {
            "id": idx * 1000 + 1,
            "lead_time": tempo_s,
            "result": result_items,
            "was_cancelled": bool(pag.get("motivo_pulo")),
            "ground_truth": False,
        }
        if nota or flags or pag.get("motivo_pulo"):
            annotation["meta"] = {
                "nota": nota,
                "flags": flags,
                "motivo_pulo": pag.get("motivo_pulo", ""),
            }

        tarefa = {
            "id": idx,
            "data": {
                "image": imagem,
                "ocr": imagem,
                "page_id": page_id,
            },
            "annotations": [annotation],
        }
        tarefas_ls.append(tarefa)

    return tarefas_ls


def ls_para_proprio(dados_ls: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converte tarefas do formato Label Studio para o formato próprio simples.

    Parâmetros:
        dados_ls: lista de tarefas ou dicionário único de tarefa/anotação do Label Studio.

    Retorna:
        Lista de páginas no formato próprio.
    """
    if isinstance(dados_ls, dict):
        if "tasks" in dados_ls and isinstance(dados_ls["tasks"], list):
            tarefas = dados_ls["tasks"]
        elif "annotations" in dados_ls or "result" in dados_ls or "data" in dados_ls:
            tarefas = [dados_ls]
        else:
            tarefas = [dados_ls]
    elif isinstance(dados_ls, list):
        tarefas = dados_ls
    else:
        raise ValueError(f"Formato Label Studio inválido: esperado list ou dict, recebido {type(dados_ls)}")

    paginas_proprias: List[Dict[str, Any]] = []

    for t_idx, tarefa in enumerate(tarefas, start=1):
        data = tarefa.get("data") or {}
        page_id = str(data.get("page_id") or data.get("id") or tarefa.get("id") or f"ls_tarefa_{t_idx}")
        imagem = data.get("image") or data.get("ocr") or f"{page_id}.png"

        # Obter anotação válida
        annotations = tarefa.get("annotations") or []
        ann = annotations[0] if annotations else tarefa
        results = ann.get("result") or []
        tempo_s = float(ann.get("lead_time") or 0.0)

        meta = ann.get("meta") or {}
        nota = meta.get("nota") or ""
        flags = meta.get("flags") or []
        motivo_pulo = meta.get("motivo_pulo") or ""

        caixas_dict: Dict[str, Dict[str, Any]] = {}
        ligacoes: List[Dict[str, str]] = []
        W_encontrado: Optional[float] = None
        H_encontrado: Optional[float] = None

        # Processar itens do resultado
        for item in results:
            tipo = item.get("type")
            if tipo == "relation":
                de = str(item.get("from_id"))
                para = str(item.get("to_id"))
                direcao = item.get("direction", "right")
                labels = item.get("labels") or ["continue"]
                nome_rel = labels[0] if labels else "continue"
                if direcao == "left":
                    de, para = para, de
                if de and para:
                    ligacoes.append({"de": de, "para": para, "tipo": nome_rel})
                continue

            rid = str(item.get("id"))
            if not rid:
                continue

            cx = caixas_dict.setdefault(rid, {
                "id": rid,
                "classe": "texto",
                "texto": "",
                "pct": None,
                "W": None,
                "H": None,
            })

            val = item.get("value") or {}
            orig_w = item.get("original_width")
            orig_h = item.get("original_height")
            if orig_w is not None and W_encontrado is None:
                W_encontrado = float(orig_w)
            if orig_h is not None and H_encontrado is None:
                H_encontrado = float(orig_h)

            if tipo in ("rectanglelabels", "labels"):
                rotulos = val.get(tipo) or []
                if rotulos:
                    cx["classe"] = str(rotulos[0])
            elif tipo == "textarea":
                textos = val.get("text") or []
                cx["texto"] = "\n".join(str(t) for t in textos)

            if cx["pct"] is None and {"x", "y", "width", "height"} <= set(val):
                cx["pct"] = (float(val["x"]), float(val["y"]), float(val["width"]), float(val["height"]))
                cx["W"] = float(orig_w) if orig_w is not None else None
                cx["H"] = float(orig_h) if orig_h is not None else None

        W = W_encontrado or 1000.0
        H = H_encontrado or 1000.0

        # Converter porcentagens para pixels absolutos
        caixas_finais: List[Dict[str, Any]] = []
        for rid, raw_cx in caixas_dict.items():
            pct = raw_cx["pct"]
            if pct is not None:
                px, py, pw, ph = pct
                cur_W = raw_cx["W"] or W
                cur_H = raw_cx["H"] or H
                x0 = round((px / 100.0) * cur_W, 2)
                y0 = round((py / 100.0) * cur_H, 2)
                x1 = round(((px + pw) / 100.0) * cur_W, 2)
                y1 = round(((py + ph) / 100.0) * cur_H, 2)
            else:
                x0, y0, x1, y1 = 0.0, 0.0, 100.0, 100.0

            cx_obj = {
                "id": rid,
                "bbox": [x0, y0, x1, y1],
                "classe": raw_cx["classe"],
            }
            if raw_cx["texto"]:
                cx_obj["texto"] = raw_cx["texto"]
            caixas_finais.append(cx_obj)

        # Reconstruir ordem a partir das relações
        ordem: List[str] = []
        if ligacoes:
            sucessores: Dict[str, str] = {}
            entradas: Dict[str, int] = {c["id"]: 0 for c in caixas_finais}
            for lig in ligacoes:
                de, para = lig["de"], lig["para"]
                sucessores[de] = para
                entradas[para] = entradas.get(para, 0) + 1
                if de not in entradas:
                    entradas[de] = 0

            # Encontrar cabeças da cadeia (entradas == 0 que têm saída)
            cabecas = [cid for cid, count in entradas.items() if count == 0 and cid in sucessores]
            if cabecas:
                atual: Optional[str] = cabecas[0]
                visitados = set()
                while atual is not None and atual not in visitados:
                    visitados.add(atual)
                    ordem.append(atual)
                    atual = sucessores.get(atual)

        pag_obj: Dict[str, Any] = {
            "page_id": page_id,
            "imagem": imagem,
            "largura": int(round(W)),
            "altura": int(round(H)),
            "caixas": caixas_finais,
            "ordem": ordem,
            "flags": flags,
            "nota": nota,
            "tempo_s": tempo_s,
        }
        if ligacoes:
            pag_obj["relacoes"] = ligacoes
        if motivo_pulo:
            pag_obj["motivo_pulo"] = motivo_pulo

        paginas_proprias.append(pag_obj)

    return paginas_proprias


def executar_teste_ida_e_volta() -> None:
    """Executa teste sintético de ida e volta garantindo integridade das conversões."""
    print("=" * 70)
    print("TESTE DE IDA E VOLTA: Formato Próprio <-> Label Studio")
    print("=" * 70)

    # 1. Definir dados sintéticos com 3 caixas e uma relação
    W_orig, H_orig = 1200.0, 1600.0
    dados_sinteticos: List[Dict[str, Any]] = [
        {
            "page_id": "teste_sintetico_p01",
            "imagem": "pagina_teste_01.png",
            "largura": int(W_orig),
            "altura": int(H_orig),
            "caixas": [
                {
                    "id": "box-1",
                    "bbox": [100.0, 150.0, 500.0, 300.0],
                    "classe": "cabecalho",
                    "texto": "DIARIO OFICIAL DO MUNICIPIO",
                },
                {
                    "id": "box-2",
                    "bbox": [100.0, 320.0, 500.0, 800.0],
                    "classe": "texto",
                    "texto": "Artigo 1. Fica homologado o concurso publico...",
                },
                {
                    "id": "box-3",
                    "bbox": [550.0, 320.0, 1100.0, 900.0],
                    "classe": "tabela",
                    "texto": "Tabela de cargos e salarios vigentes",
                },
            ],
            # Uma relação explícita entre box-1 e box-2
            "ordem": ["box-1", "box-2"],
            "relacoes": [
                {"de": "box-1", "para": "box-2", "tipo": "continue"}
            ],
            "flags": ["revisado", "alta_qualidade"],
            "nota": "Página sintética para validação técnica da ferramenta.",
            "tempo_s": 28.4,
        }
    ]

    print("\n[1/3] Convertendo do formato próprio para Label Studio...")
    dados_ls = proprio_para_ls(dados_sinteticos)

    # Verificações na saída do Label Studio
    assert len(dados_ls) == 1, f"Esperada 1 tarefa LS, obtida {len(dados_ls)}"
    results_ls = dados_ls[0]["annotations"][0]["result"]
    retangulos_ls = [r for r in results_ls if r.get("type") == "rectanglelabels"]
    relacoes_ls = [r for r in results_ls if r.get("type") == "relation"]
    assert len(retangulos_ls) == 3, f"Esperados 3 retângulos no LS, obtidos {len(retangulos_ls)}"
    assert len(relacoes_ls) == 1, f"Esperada 1 relação no LS, obtidas {len(relacoes_ls)}"
    print(f"      OK -> {len(retangulos_ls)} caixas e {len(relacoes_ls)} relação(ões) geradas no Label Studio.")

    print("\n[2/3] Convertendo de volta de Label Studio para o formato próprio...")
    dados_volta = ls_para_proprio(dados_ls)

    # 3. Verificações de integridade estrita
    assert len(dados_volta) == 1, f"Esperada 1 página na volta, obtidas {len(dados_volta)}"
    pag_volta = dados_volta[0]
    pag_orig = dados_sinteticos[0]

    # Validar metadados básicos
    if pag_volta["page_id"] != pag_orig["page_id"]:
        raise AssertionError(f"page_id divergente: esperado {pag_orig['page_id']!r}, obtido {pag_volta['page_id']!r}")
    if pag_volta["largura"] != pag_orig["largura"] or pag_volta["altura"] != pag_orig["altura"]:
        raise AssertionError(f"Dimensões divergentes: esperado ({pag_orig['largura']}, {pag_orig['altura']}), "
                             f"obtido ({pag_volta['largura']}, {pag_volta['altura']})")
    if not math.isclose(pag_volta["tempo_s"], pag_orig["tempo_s"], abs_tol=0.1):
        raise AssertionError(f"tempo_s divergente: esperado {pag_orig['tempo_s']}, obtido {pag_volta['tempo_s']}")

    # Validar caixas
    caixas_orig_map = {c["id"]: c for c in pag_orig["caixas"]}
    caixas_volta_map = {c["id"]: c for c in pag_volta["caixas"]}

    if set(caixas_orig_map) != set(caixas_volta_map):
        raise AssertionError(f"IDs de caixas divergentes: esperados {set(caixas_orig_map)}, "
                             f"obtidos {set(caixas_volta_map)}")

    for cid, cx_o in caixas_orig_map.items():
        cx_v = caixas_volta_map[cid]
        if cx_v["classe"] != cx_o["classe"]:
            raise AssertionError(f"Classe da caixa {cid} divergiu: esperada {cx_o['classe']!r}, "
                                 f"obtida {cx_v['classe']!r}")
        if (cx_o.get("texto") or "") != (cx_v.get("texto") or ""):
            raise AssertionError(f"Texto da caixa {cid} divergiu: esperado {cx_o.get('texto')!r}, "
                                 f"obtido {cx_v.get('texto')!r}")

        # Tolerância de 0.05 px em coordenadas pós porcentagem
        for val_o, val_v in zip(cx_o["bbox"], cx_v["bbox"]):
            if not math.isclose(val_o, val_v, abs_tol=0.1):
                raise AssertionError(f"Coordenada da caixa {cid} divergiu: original {cx_o['bbox']}, "
                                     f"obtida {cx_v['bbox']} (delta > 0.1px)")

    print("      OK -> 3 caixas e todas as coordenadas/classes/textos preservados exatamente.")

    # Validar relação e ordem
    if pag_volta["ordem"] != pag_orig["ordem"]:
        raise AssertionError(f"Ordem de leitura divergiu: esperada {pag_orig['ordem']}, "
                             f"obtida {pag_volta['ordem']}")

    rel_v = pag_volta.get("relacoes", [])
    if len(rel_v) != 1 or rel_v[0]["de"] != "box-1" or rel_v[0]["para"] != "box-2":
        raise AssertionError(f"Relação recuperada divergente: esperada [('box-1' -> 'box-2')], obtida {rel_v}")

    print("      OK -> Relação 'box-1' -> 'box-2' e ordem de leitura recuperadas perfeitamente.")
    print("\n[3/3] SUCESSO: O teste de ida e volta passou em 100% das checagens sem divergências!")
    print("=" * 70)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--teste", action="store_true", help="Executa o teste de ida e volta sintético")
    parser.add_argument("--proprio-para-ls", nargs=2, metavar=("ENTRADA", "SAIDA"),
                        help="Converte arquivo JSON próprio para export do Label Studio")
    parser.add_argument("--ls-para-proprio", nargs=2, metavar=("ENTRADA", "SAIDA"),
                        help="Converte export JSON do Label Studio para formato próprio")

    args = parser.parse_args()

    if args.proprio_para_ls:
        inp, out = Path(args.proprio_para_ls[0]), Path(args.proprio_para_ls[1])
        dados = json.loads(inp.read_text(encoding="utf-8"))
        res = proprio_para_ls(dados)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Convertido com sucesso de formato próprio para Label Studio: {out}")
    elif args.ls_para_proprio:
        inp, out = Path(args.ls_para_proprio[0]), Path(args.ls_para_proprio[1])
        dados = json.loads(inp.read_text(encoding="utf-8"))
        res = ls_para_proprio(dados)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Convertido com sucesso de Label Studio para formato próprio: {out}")
    else:
        # Padrão: executa o teste de ida e volta
        executar_teste_ida_e_volta()


if __name__ == "__main__":
    main()
