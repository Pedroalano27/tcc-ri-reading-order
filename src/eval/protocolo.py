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

# A pasta de blocos e o resultado de UMA segmentacao. Trocar de segmentacao (para a
# analise de sensibilidade a granularidade) e so apontar TCC_DIR_BLOCOS para outra pasta
# com os mesmos page_id -- todos os metodos, metricas e figuras seguem sem alteracao:
#     set TCC_DIR_BLOCOS=data\processed\blocos_v1  &&  python src\rodar_experimentos.py
_PADRAO_BLOCOS = os.path.join(RAIZ_PROJETO, "data", "processed", "blocos")
DIR_BLOCOS = os.path.abspath(os.path.join(RAIZ_PROJETO, os.environ.get("TCC_DIR_BLOCOS", _PADRAO_BLOCOS)))
DIR_RESULTADOS = os.path.abspath(os.path.join(RAIZ_PROJETO, os.environ.get("TCC_DIR_RESULTADOS", "resultados")))
ARQ_SPLITS = os.path.join(RAIZ_PROJETO, "data", "processed", "splits.json")


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


def arquivos_paginas_ausentes(ufs: List[str], dir_blocos: str) -> List[str]:
    """Lista JSONL esperados ausentes ou sem pagina identificavel, antes do uso.

    Reutiliza a leitura que ignora linhas vazias e JSON truncado. Nao aplica
    filtros de segmentacao: basta haver uma pagina com page_id no arquivo.
    """
    ausentes = []
    for uf in ufs:
        nome = f"{uf}.jsonl"
        if not os.path.isfile(os.path.join(dir_blocos, nome)):
            ausentes.append(nome)
            continue
        paginas = iterar_paginas([uf], dir_blocos)
        try:
            if not any(isinstance(p, dict) and p.get("page_id") for p in paginas):
                ausentes.append(nome)
        finally:
            paginas.close()
    return ausentes


def montar_treino(n_treino: Optional[int] = None, dir_extra: Optional[str] = None,
                  semente: int = 42) -> List[Dict]:
    """Treino ampliado com paginas extras dos mesmos veiculos de treino.

    As paginas do protocolo vem primeiro e as extras depois, cada grupo embaralhado
    com semente fixa. Os subconjuntos ficam aninhados: pedir 152 paginas devolve
    exatamente o treino original, e cada tamanho maior contem o anterior.
    n_treino deve ser positivo; None usa todas as paginas disponiveis.
    """
    if n_treino is not None and n_treino <= 0:
        raise ValueError(
            f"[ERRO] n_treino deve ser positivo; valor recebido: {n_treino}. "
            "None significa todas as paginas disponiveis."
        )
    ufs = carregar_splits()["treino"]
    base = sorted(iterar_paginas(ufs), key=lambda p: p["page_id"])
    if not base:
        raise RuntimeError(
            f"[ERRO] treino base vazio em {DIR_BLOCOS}. "
            "Confira TCC_DIR_BLOCOS e data/processed/splits.json."
        )
    vistos = {p["page_id"] for p in base}
    extra = []
    if dir_extra:
        dir_extra = os.path.abspath(
            dir_extra if os.path.isabs(dir_extra) else os.path.join(RAIZ_PROJETO, dir_extra)
        )
        if not os.path.isdir(dir_extra):
            raise FileNotFoundError(
                f"[ERRO] paginas extras solicitadas, mas a pasta nao existe: {dir_extra}. "
                "Reextraia data/processed/blocos_extra antes do treino ampliado."
            )
        arquivos_extra = [os.path.join(dir_extra, f"{uf}.jsonl") for uf in ufs
                          if os.path.isfile(os.path.join(dir_extra, f"{uf}.jsonl"))]
        if not arquivos_extra:
            raise FileNotFoundError(
                f"[ERRO] paginas extras solicitadas, mas {dir_extra} nao contem JSONL "
                f"dos {len(ufs)} veiculos de treino. "
                "Ausentes: " + ", ".join(f"{uf}.jsonl" for uf in ufs)
                + ". A reextracao parece incompleta."
            )
        ausentes = arquivos_paginas_ausentes(ufs, dir_extra)
        if ausentes:
            raise FileNotFoundError(
                f"[ERRO] paginas extras solicitadas, mas faltam arquivos em {dir_extra} "
                "(ausentes ou sem nenhuma pagina valida): " + ", ".join(ausentes)
                + ". A reextracao parece incompleta."
            )
        for p in iterar_paginas(ufs, dir_extra):
            if p["page_id"] not in vistos:
                vistos.add(p["page_id"])
                extra.append(p)
        if not extra:
            raise RuntimeError(
                f"[ERRO] nenhum page_id extra valido foi encontrado em {dir_extra}; "
                "a pasta esta vazia ou repete apenas o treino base."
            )
    elif n_treino is not None and n_treino > len(base):
        raise ValueError(
            f"[ERRO] foram pedidas {n_treino} paginas, mas o treino base tem {len(base)}. "
            "Informe --blocos-extra com uma pasta reextraida e nao vazia."
        )
    extra.sort(key=lambda p: p["page_id"])
    rng = random.Random(semente)
    rng.shuffle(base)
    rng.shuffle(extra)
    pool = base + extra
    if n_treino is not None and n_treino > len(pool):
        raise ValueError(
            f"[ERRO] foram pedidas {n_treino} paginas, mas ha somente {len(pool)} "
            f"({len(base)} base + {len(extra)} extras) disponiveis."
        )
    selecionadas = pool[:n_treino] if n_treino is not None else pool
    ids_base = {p["page_id"] for p in base}
    n_extra_usadas = sum(p["page_id"] not in ids_base for p in selecionadas)
    print(f"[*] treino montado: {len(selecionadas)} paginas "
          f"({len(selecionadas) - n_extra_usadas} base + {n_extra_usadas} extras; "
          f"{len(extra)} extras disponiveis)", flush=True)
    return selecionadas


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
