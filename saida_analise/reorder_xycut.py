"""
reorder_xycut.py - Algoritmo XY-Cut Recursivo para Ordem de Leitura em Layout Multicoluna.

Modulo autonomo e ultraleve (somente biblioteca padrao do Python, sem dependencias externas).
Projetado especificamente para integracao como estagio de pos-processamento no pipeline
do Acessilia (A11yDevs) ou avaliacao no Dr.DocBench.

Compatibilidade:
- Nao depende de PyTorch, transformers, OpenCV ou PyMuPDF (100% livre de AGPL-3.0).
- Suporta elementos em formato dict com chave 'bbox' ([left, top, right, bottom] ou dict).
- Converte e normaliza coordenadas automaticamente (TOPLEFT).

Base teorica:
- Nagy & Seth (1984); Ha, Haralick & Phillips (1995).
- Adaptacao para documentos multicoluna e secoes horizontais com blocos largos de cabecalho/titulo.
"""

from __future__ import annotations
from typing import Any, Dict, List, Sequence, Union


def _extrair_bbox(bloco: Any) -> tuple[float, float, float, float]:
    """Extrai (x0, top, x1, bottom) de formato dict ou objeto.
    
    Garante x0 <= x1 e top <= bottom (coordenadas com origem TOPLEFT).
    """
    if isinstance(bloco, dict):
        if "bbox" in bloco:
            b = bloco["bbox"]
            if isinstance(b, (list, tuple)) and len(b) >= 4:
                x0, y0, x1, y1 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
            elif isinstance(b, dict):
                x0 = float(b.get("left", b.get("x0", 0.0)))
                y0 = float(b.get("top", b.get("y0", 0.0)))
                x1 = float(b.get("right", b.get("x1", 0.0)))
                y1 = float(b.get("bottom", b.get("y1", 0.0)))
            else:
                raise ValueError(f"Formato de bbox invalido: {b}")
        elif "left" in bloco and "top" in bloco:
            x0 = float(bloco["left"])
            y0 = float(bloco["top"])
            x1 = float(bloco.get("right", x0))
            y1 = float(bloco.get("bottom", y0))
        elif "x0" in bloco and "top" in bloco:
            x0 = float(bloco["x0"])
            y0 = float(bloco["top"])
            x1 = float(bloco.get("x1", x0))
            y1 = float(bloco.get("bottom", y0))
        else:
            raise ValueError(f"Elemento nao contem informacoes de bbox reconheciveis: {bloco}")
    else:
        # Suporte a objetos com atributos (ex.: modelos Pydantic ou dataclasses)
        if hasattr(bloco, "bbox"):
            b = getattr(bloco, "bbox")
            if isinstance(b, (list, tuple)) and len(b) >= 4:
                x0, y0, x1, y1 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
            elif hasattr(b, "left") and hasattr(b, "top"):
                x0, y0, x1, y1 = float(b.left), float(b.top), float(b.right), float(b.bottom)
            else:
                raise ValueError(f"Atributo bbox nao reconhecido em {bloco}")
        elif hasattr(bloco, "left") and hasattr(bloco, "top"):
            x0, y0 = float(bloco.left), float(bloco.top)
            x1 = float(getattr(bloco, "right", x0))
            y1 = float(getattr(bloco, "bottom", y0))
        else:
            raise ValueError(f"Objeto nao possui coordenadas de bounding box: {bloco}")

    left, right = min(x0, x1), max(x0, x1)
    top, bottom = min(y0, y1), max(y0, y1)
    return left, top, right, bottom


def _cortes_verticais(
    indices: List[int],
    caixas: List[Dict[str, float]],
    calha_min: float = 4.0,
    largura_min_frac: float = 0.12,
) -> List[List[int]]:
    """Divide os blocos em colunas separadas por calhas verticais vazias.
    
    Funde colunas anomalas excessivamente estreitas com vizinhas proximas.
    """
    ordem = sorted(indices, key=lambda i: caixas[i]["x0"])
    grupos = [[ordem[0]]]
    fim = caixas[ordem[0]]["x1"]

    for i in ordem[1:]:
        if caixas[i]["x0"] > fim + calha_min:
            grupos.append([i])
        else:
            grupos[-1].append(i)
        fim = max(fim, caixas[i]["x1"])

    def _largura(g: List[int]) -> float:
        return max(caixas[i]["x1"] for i in g) - min(caixas[i]["x0"] for i in g)

    w_total = max(caixas[i]["x1"] for i in indices) - min(caixas[i]["x0"] for i in indices)

    while len(grupos) > 1:
        k = min(range(len(grupos)), key=lambda j: _largura(grupos[j]))
        if _largura(grupos[k]) >= largura_min_frac * w_total:
            break
        if k == 0:
            j = 1
        elif k == len(grupos) - 1:
            j = k - 1
        else:
            gap_e = min(caixas[i]["x0"] for i in grupos[k]) - max(caixas[i]["x1"] for i in grupos[k - 1])
            gap_d = min(caixas[i]["x0"] for i in grupos[k + 1]) - max(caixas[i]["x1"] for i in grupos[k])
            j = k - 1 if gap_e <= gap_d else k + 1
        a, b = sorted((k, j))
        grupos[a] = grupos[a] + grupos[b]
        del grupos[b]

    return grupos


def _xycut_recursivo(
    indices: List[int],
    caixas: List[Dict[str, float]],
    prof: int = 0,
    max_prof: int = 60,
    limiar_largura_secao: float = 0.60,
) -> List[int]:
    """Execucao recursiva do XY-Cut."""
    if len(indices) <= 1 or prof > max_prof:
        return sorted(indices, key=lambda i: (caixas[i]["top"], caixas[i]["x0"]))

    grupos = _cortes_verticais(indices, caixas)
    if len(grupos) > 1:
        saida: List[int] = []
        for g in grupos:
            saida.extend(_xycut_recursivo(g, caixas, prof + 1, max_prof, limiar_largura_secao))
        return saida

    w_span = max(1e-6, max(caixas[i]["x1"] for i in indices) - min(caixas[i]["x0"] for i in indices))
    largos = [i for i in indices if (caixas[i]["x1"] - caixas[i]["x0"]) >= limiar_largura_secao * w_span]
    conj_largos = set(largos)
    estreitos = [i for i in indices if i not in conj_largos]

    if largos and estreitos:
        largos.sort(key=lambda i: caixas[i]["top"])
        centros = [(caixas[i]["top"] + caixas[i]["bottom"]) / 2.0 for i in largos]
        secoes: List[List[int]] = [[] for _ in range(len(largos) + 1)]
        for i in estreitos:
            cy = (caixas[i]["top"] + caixas[i]["bottom"]) / 2.0
            idx_sec = sum(1 for c in centros if c < cy)
            secoes[idx_sec].append(i)

        saida = []
        for k in range(len(largos) + 1):
            saida.extend(_xycut_recursivo(secoes[k], caixas, prof + 1, max_prof, limiar_largura_secao))
            if k < len(largos):
                saida.append(largos[k])
        return saida

    return sorted(indices, key=lambda i: (caixas[i]["top"], caixas[i]["x0"]))


def reorder(
    blocos: Sequence[Union[Dict[str, Any], Any]],
    inplace: bool = False,
    assign_reading_order: bool = True,
) -> List[Any]:
    """Reordena uma sequencia de blocos utilizando o algoritmo XY-Cut.
    
    Args:
        blocos: Lista de blocos/elementos. Cada bloco deve ter identificador e coordenadas:
                dict com chave 'id' e 'bbox': [left, top, right, bottom], ou similar.
        inplace: Se True, muta os dicionarios/objetos da lista original; se False, cria
                 uma nova lista contendo copias superficiais (shallow copy) dos dicionarios.
        assign_reading_order: Se True, atribui o campo/atributo `reading_order` (1..N)
                              a cada elemento retornado.
                              
    Returns:
        Lista de blocos na ordem de leitura recomendada.
    """
    if not blocos:
        return []
    if len(blocos) == 1:
        res = list(blocos) if inplace else [dict(blocos[0]) if isinstance(blocos[0], dict) else blocos[0]]
        if assign_reading_order:
            if isinstance(res[0], dict):
                res[0]["reading_order"] = 1
            elif hasattr(res[0], "reading_order"):
                setattr(res[0], "reading_order", 1)
        return res

    caixas = []
    for b in blocos:
        x0, top, x1, bottom = _extrair_bbox(b)
        caixas.append({"x0": x0, "top": top, "x1": x1, "bottom": bottom})

    indices = list(range(len(blocos)))
    ordem_indices = _xycut_recursivo(indices, caixas)

    saida = []
    for pos, idx in enumerate(ordem_indices, start=1):
        item = blocos[idx]
        if not inplace and isinstance(item, dict):
            item = dict(item)
        if assign_reading_order:
            if isinstance(item, dict):
                item["reading_order"] = pos
            elif hasattr(item, "reading_order"):
                setattr(item, "reading_order", pos)
        saida.append(item)

    return saida


def reorder_ids(blocos: Sequence[Union[Dict[str, Any], Any]]) -> List[Any]:
    """Atalho de conveniencia que devolve apenas os IDs dos blocos na nova ordem."""
    reordenados = reorder(blocos, inplace=False, assign_reading_order=False)
    ids = []
    for b in reordenados:
        if isinstance(b, dict):
            ids.append(b.get("id"))
        elif hasattr(b, "id"):
            ids.append(getattr(b, "id"))
        else:
            ids.append(b)
    return ids


# ---------------------------------------------------------------------------
# Testes unitarios e validacao
# ---------------------------------------------------------------------------

def _rodar_testes_locais():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("[*] Iniciando suite de verificacao de reorder_xycut.py...")

    # Teste 1: Pagina com duas colunas puras
    # Coluna 1 (x: 10..100): b1 (y: 10..50), b2 (y: 60..100)
    # Coluna 2 (x: 120..210): b3 (y: 10..50), b4 (y: 60..100)
    # Entrada embaralhada: b3, b2, b4, b1
    blocos_2col = [
        {"id": "b3", "bbox": [120, 10, 210, 50]},
        {"id": "b2", "bbox": [10, 60, 100, 100]},
        {"id": "b4", "bbox": [120, 60, 210, 100]},
        {"id": "b1", "bbox": [10, 10, 100, 50]},
    ]
    ordem_pred = reorder_ids(blocos_2col)
    assert ordem_pred == ["b1", "b2", "b3", "b4"], f"Falha teste 2 colunas: {ordem_pred}"
    print("  [OK] Teste 1 (duas colunas puras): passou")

    # Teste 2: Cabecalho largo que atravessa a pagina + duas colunas + rodape largo
    # Cabecalho (x: 10..210, y: 0..30)
    # Coluna 1: c1 (x: 10..100, y: 40..80)
    # Coluna 2: c2 (x: 120..210, y: 40..80)
    # Rodape (x: 10..210, y: 120..150)
    blocos_secao = [
        {"id": "c2", "bbox": [120, 40, 210, 80]},
        {"id": "rodape", "bbox": [10, 120, 210, 150]},
        {"id": "cabecalho", "bbox": [10, 0, 210, 30]},
        {"id": "c1", "bbox": [10, 40, 100, 80]},
    ]
    ordem_secao = reorder_ids(blocos_secao)
    assert ordem_secao == ["cabecalho", "c1", "c2", "rodape"], f"Falha teste cabecalho largo: {ordem_secao}"
    print("  [OK] Teste 2 (cabecalho e rodape largos): passou")

    # Teste 3: Atribuicao correta de reading_order
    res = reorder(blocos_secao, inplace=False, assign_reading_order=True)
    assert [x["reading_order"] for x in res] == [1, 2, 3, 4]
    assert [x["id"] for x in res] == ["cabecalho", "c1", "c2", "rodape"]
    print("  [OK] Teste 3 (campo reading_order sequencial 1..N): passou")

    # Teste 4: Casos limite (vazio e unico)
    assert reorder([]) == []
    assert reorder_ids([{"id": "unico", "bbox": [0, 0, 10, 10]}]) == ["unico"]
    print("  [OK] Teste 4 (casos de borda: vazio e unitario): passou")

    print("[CONCLUIDO] Todos os testes unitarios de reorder_xycut passaram com sucesso!")


if __name__ == "__main__":
    _rodar_testes_locais()
