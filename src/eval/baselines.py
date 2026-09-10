"""
Baselines nao-aprendidos, avaliados no conjunto de teste do protocolo.

  aleatoria  Confia na ordem em que o detector entregou as caixas (a permutacao
             de entrada do protocolo). E o piso: o que acontece quando ninguem
             ordena nada.
  naive      Ordena por (top, x0): de cima para baixo, da esquerda para a direita.
             E o que muitos pipelines YOLO + OCR fazem por padrao.
  xycut      Heuristica XY-cut recursiva com deteccao de colunas
             (a mesma de src/data/extrator.py), calculada so a partir das caixas.

Todos recebem apenas as bounding boxes -- nunca a ordem de fluxo do PDF.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import carregar_particao, ordem_entrada, salvar_predicoes  # noqa: E402
from src.data.extrator import xycut  # noqa: E402


def caixas(p):
    return [{"x0": c["bbox"][0], "top": c["bbox"][1], "x1": c["bbox"][2], "bottom": c["bbox"][3]}
            for c in p["bounding_boxes"]]


def main():
    teste = carregar_particao("teste")
    saidas = {"aleatoria": [], "naive": [], "xycut": []}
    for p in teste:
        ids = [c["id"] for c in p["bounding_boxes"]]
        entrada = ordem_entrada(p)

        t0 = time.perf_counter()
        pred = [ids[i] for i in entrada]
        saidas["aleatoria"].append({"page_id": p["page_id"], "ordem_pred": pred,
                                    "tempo_ms": (time.perf_counter() - t0) * 1000})

        t0 = time.perf_counter()
        B = caixas(p)
        pred = [ids[i] for i in sorted(entrada, key=lambda i: (B[i]["top"], B[i]["x0"]))]
        saidas["naive"].append({"page_id": p["page_id"], "ordem_pred": pred,
                                "tempo_ms": (time.perf_counter() - t0) * 1000})

        t0 = time.perf_counter()
        B = caixas(p)
        pred = [ids[i] for i in xycut(list(entrada), B)]
        saidas["xycut"].append({"page_id": p["page_id"], "ordem_pred": pred,
                                "tempo_ms": (time.perf_counter() - t0) * 1000})

    for metodo, linhas in saidas.items():
        caminho = salvar_predicoes(metodo, linhas)
        media = sum(l["tempo_ms"] for l in linhas) / len(linhas)
        print(f"[OK] {metodo:<10} {len(linhas)} paginas | {media:.3f} ms/pagina -> {caminho}")


if __name__ == "__main__":
    main()
