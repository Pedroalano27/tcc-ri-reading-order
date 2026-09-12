"""
Protocolo experimental comum a todos os metodos.

Centraliza tudo o que precisa ser IDENTICO entre os metodos comparados, para
que a comparacao seja justa:

  - quais UFs sao treino / validacao / teste (divisao POR UF, nunca por pagina:
    o mesmo veiculo repete o template por anos e um split aleatorio vazaria
    o layout do teste para o treino)
  - qual ordem e a referencia (rotulo silver)
  - a ordem de ENTRADA de cada pagina: os blocos chegam embaralhados por uma
    permutacao deterministica, simulando um detector (YOLO + OCR) que entrega
    as caixas sem ordem. Todos os metodos recebem exatamente a mesma entrada.

Cada metodo grava suas predicoes em resultados/pred_<metodo>.jsonl, uma linha
por pagina: {"page_id", "ordem_pred", "tempo_ms"}. O script src/eval/comparar.py
calcula as metricas de todos contra a mesma referencia.

Para a curva de aprendizado, montar_treino() amplia o treino com paginas extras
dos MESMOS veiculos de treino (coletadas em outra pasta), sem tocar em validacao
e teste.
"""
from __future__ import annotations

import os
import json
import random
from typing import Dict, Iterator, List, Optional

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BLOCOS = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos")
ARQ_SPLITS = os.path.join(RAIZ_PROJETO, "data", "processed", "splits.json")
DIR_RESULTADOS = os.path.join(RAIZ_PROJETO, "resultados")


def carregar_splits() -> Dict:
    with open(ARQ_SPLITS, encoding="utf-8") as f:
        return json.load(f)


def iterar_paginas(ufs: List[str], dir_blocos: Optional[str] = None) -> Iterator[Dict]:
    for uf in ufs:
        caminho = os.path.join(dir_blocos or DIR_BLOCOS, f"{uf}.jsonl")
        if not os.path.exists(caminho):
            continue
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError:
                    continue    # linha truncada por uma extracao interrompida


def carregar_particao(nome: str) -> List[Dict]:
    """nome em {'treino', 'validacao', 'teste'}"""
    return list(iterar_paginas(carregar_splits()[nome]))


def montar_treino(n_treino: Optional[int] = None, dir_extra: Optional[str] = None,
                  semente: int = 42) -> List[Dict]:
    """Treino ampliado com paginas extras dos mesmos veiculos de treino.

    As paginas do protocolo vem primeiro e as extras depois, cada grupo embaralhado
    com semente fixa. Os subconjuntos ficam aninhados: pedir 152 paginas devolve
    exatamente o treino original, e cada tamanho maior contem o anterior.
    """
    ufs = carregar_splits()["treino"]
    base = sorted(iterar_paginas(ufs), key=lambda p: p["page_id"])
    vistos = {p["page_id"] for p in base}
    extra = []
    if dir_extra:
        for p in iterar_paginas(ufs, dir_extra):
            if p["page_id"] not in vistos:
                vistos.add(p["page_id"])
                extra.append(p)
    extra.sort(key=lambda p: p["page_id"])
    rng = random.Random(semente)
    rng.shuffle(base)
    rng.shuffle(extra)
    pool = base + extra
    return pool[:n_treino] if n_treino else pool


def referencia(pagina: Dict, splits: Dict | None = None) -> List[str]:
    """Ordem de referencia (silver) da pagina, conforme definido em splits.json."""
    chave = (splits or carregar_splits())["referencia"]
    return pagina["ordens"][chave]


def ordem_entrada(pagina: Dict) -> List[int]:
    """Indices dos blocos na ordem em que chegam ao metodo (permutacao fixa por pagina)."""
    idx = list(range(len(pagina["bounding_boxes"])))
    random.Random(f"entrada-{pagina['page_id']}").shuffle(idx)
    return idx


def salvar_predicoes(metodo: str, linhas: List[Dict], dir_saida: Optional[str] = None) -> str:
    destino = dir_saida or DIR_RESULTADOS
    os.makedirs(destino, exist_ok=True)
    caminho = os.path.join(destino, f"pred_{metodo}.jsonl")
    with open(caminho, "w", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return caminho
