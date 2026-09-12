"""
Metricas de avaliacao de ordem de leitura.

Todas as funcoes recebem duas listas de identificadores de blocos:
    pred -- ordem produzida pelo metodo avaliado
    gt   -- ordem de referencia (padrao-ouro ou rotulo silver)

Metricas implementadas:

    kendall_tau      Correlacao de postos de Kendall entre as duas ordens, em [-1, 1].
                     1 = identica, 0 = sem relacao, -1 = invertida. Conta pares
                     discordantes, entao nao sofre do efeito cascata de metricas
                     posicionais (um bloco deslocado no inicio nao "contamina" o resto).

    ard              Average Relative Distance (Wang et al., 2021 - LayoutReader).
                     Media do deslocamento absoluto de cada elemento entre a posicao
                     predita e a de referencia. Elemento ausente da predicao recebe
                     penalidade n. Quanto menor, melhor; 0 = ordem perfeita.

    ard_normalizado  ARD / n, em [0, 1], para comparar paginas de tamanhos diferentes.

    bleu_pagina      BLEU (Papineni et al., 2002) do texto da pagina reconstruido na
                     ordem predita contra o texto na ordem de referencia (sacrebleu).
                     Na granularidade de BLOCO, a maior parte dos n-gramas e interna
                     aos blocos e se preserva em qualquer ordem -- o BLEU fica inflado
                     e pouco discriminativo. Reportar, mas ler junto com tau e ARD.

    acerto_exato     1.0 se a ordem predita e identica a referencia, senao 0.0.

    acerto_sucessor  Fracao dos pares consecutivos da predicao que tambem sao consecutivos
                     na referencia (o bloco certo logo em seguida). Mede a CONTINUIDADE LOCAL
                     do texto, que e o que importa para busca por trechos e RAG: um metodo
                     pode acertar a ordem global (tau alto) e ainda assim picotar o texto,
                     trocando vizinhos o tempo todo -- cada troca custa um par discordante
                     no tau, mas ate tres sucessores.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

from scipy.stats import kendalltau as _scipy_kendalltau


def _posicoes(ordem: Sequence[str]) -> Dict[str, int]:
    return {bid: i for i, bid in enumerate(ordem)}


def acerto_sucessor(pred: Sequence[str], gt: Sequence[str]) -> float:
    """Fracao dos pares consecutivos da predicao que sao consecutivos na referencia."""
    if len(gt) < 2:
        return 1.0
    prox = {a: b for a, b in zip(gt, gt[1:])}
    pares = list(zip(pred, pred[1:]))
    return sum(1 for a, b in pares if prox.get(a) == b) / max(1, len(pares))


def kendall_tau(pred: Sequence[str], gt: Sequence[str]) -> float:
    """Tau de Kendall sobre os elementos comuns as duas ordens."""
    pos_pred = _posicoes(pred)
    comuns = [b for b in gt if b in pos_pred]
    if len(comuns) < 2:
        return 1.0
    rank_gt = list(range(len(comuns)))
    rank_pred = [pos_pred[b] for b in comuns]
    tau, _ = _scipy_kendalltau(rank_gt, rank_pred)
    return float(tau)


def ard(pred: Sequence[str], gt: Sequence[str]) -> float:
    """Average Relative Distance (LayoutReader). Menor e melhor."""
    n = len(gt)
    if n == 0:
        return 0.0
    pos_pred = _posicoes(pred)
    total = 0.0
    for k, bid in enumerate(gt):
        total += abs(k - pos_pred[bid]) if bid in pos_pred else n
    return total / n


def ard_normalizado(pred: Sequence[str], gt: Sequence[str]) -> float:
    n = len(gt)
    return ard(pred, gt) / n if n else 0.0


def bleu_pagina(pred: Sequence[str], gt: Sequence[str], textos: Dict[str, str]) -> float:
    """BLEU do texto reconstruido na ordem predita contra a ordem de referencia."""
    from sacrebleu.metrics import BLEU

    hipotese = " ".join(textos.get(b, "") for b in pred)
    referencia = " ".join(textos.get(b, "") for b in gt)
    if not referencia.strip():
        return 100.0
    bleu = BLEU(effective_order=True)
    return float(bleu.sentence_score(hipotese, [referencia]).score)


def acerto_exato(pred: Sequence[str], gt: Sequence[str]) -> float:
    return 1.0 if list(pred) == list(gt) else 0.0


def avaliar(pred: Sequence[str], gt: Sequence[str], textos: Dict[str, str] | None = None) -> Dict[str, float]:
    """Calcula todas as metricas de uma pagina de uma vez."""
    r = {
        "kendall_tau": kendall_tau(pred, gt),
        "ard": ard(pred, gt),
        "ard_norm": ard_normalizado(pred, gt),
        "acerto_exato": acerto_exato(pred, gt),
        "acerto_sucessor": acerto_sucessor(pred, gt),
    }
    if textos is not None:
        r["bleu"] = bleu_pagina(pred, gt, textos)
    return r


def validar_permutacao(pred: Sequence[str], ids_validos: Sequence[str]) -> List[str]:
    """
    Repara uma ordem possivelmente invalida (ex.: saida de LLM): remove ids
    inexistentes e duplicados, e anexa ao final os ids faltantes na ordem original.
    """
    validos = set(ids_validos)
    vistos, saida = set(), []
    for b in pred:
        if b in validos and b not in vistos:
            saida.append(b)
            vistos.add(b)
    saida.extend(b for b in ids_validos if b not in vistos)
    return saida


if __name__ == "__main__":
    gt = ["a", "b", "c", "d", "e"]
    textos = {
        "a": "DECRETO N 402 DE 12 DE MARCO",
        "b": "O Prefeito Municipal no uso de suas atribuicoes legais",
        "c": "resolve nomear o servidor abaixo relacionado",
        "d": "Art 1 Fica homologada a proposta apresentada",
        "e": "Esta portaria entra em vigor na data de sua publicacao",
    }
    casos = {
        "identica": gt,
        "invertida": gt[::-1],
        "um bloco deslocado do fim para o inicio": ["e", "a", "b", "c", "d"],
        "troca de vizinhos": ["b", "a", "c", "d", "e"],
    }
    print(f"{'caso':<42}{'tau':>7}{'ARD':>7}{'ARDn':>7}{'BLEU':>8}{'exato':>7}")
    for nome, pred in casos.items():
        m = avaliar(pred, gt, textos)
        print(f"{nome:<42}{m['kendall_tau']:>7.2f}{m['ard']:>7.2f}{m['ard_norm']:>7.2f}"
              f"{m['bleu']:>8.1f}{m['acerto_exato']:>7.0f}")
