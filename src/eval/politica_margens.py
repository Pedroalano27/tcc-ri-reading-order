"""Aplica uma politica explicita de margens a ordens de leitura de blocos.

Cabecalhos primeiro, marcas de diagramacao antes do rodape e rodapes por ultimo
evitam que campos laterais interrompam colunas. Os padroes reproduzem a regra
de ordem_sem_bbox_justo.py: centro < 7% e base < 10% no topo, centro > 95% no
rodape. A variante por classe substitui os dois testes por cabecalho/rodape;
nao usa geometria como fallback quando a classe falta.

Uso: aplicar_margens(p['bounding_boxes'], ids, p['dimensions']) devolve uma
lista nova, preservando exatamente a ordem relativa do corpo. xycut_margens(p)
separa as margens ANTES de calcular XY-cut no corpo, como na reanalise. Estas
operacoes nao sao equivalentes: remover caixas pode mudar os cortes do corpo.
As duas funcoes recebem apenas texto, caixas e, opcionalmente, classes; nunca
consultam p['ordens'], anotacoes ou modelos. Nao ha I/O nem alteracao da entrada.

IDs devem formar uma permutacao completa, sem repeticao. Entrada invalida gera
ValueError: reparar silenciosamente poderia esconder troca de segmentacao.
Caixas e dimensoes usam a mesma unidade e coordenadas [x0, top, x1, bottom].
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Hashable

PADRAO_MARCACAO = r"^(?:<@[^>]+>|<#[^>]+>|contPageBreak.*)$"


def _separar(blocos, ordem, dimensoes, *, variante, limiar_topo,
             limite_base_topo, limiar_rodape, padrao_marcacao, campo_classe,
             classe_cabecalho, classe_rodape):
    """Valida e particiona, usando indice do bloco como desempate estavel."""
    if variante not in ("geometria", "classe"):
        raise ValueError("variante deve ser 'geometria' ou 'classe'")
    if not (0 <= limiar_topo <= limite_base_topo <= limiar_rodape <= 1):
        raise ValueError("limiares devem satisfazer 0 <= topo <= base <= rodape <= 1")
    try:
        largura, altura = float(dimensoes["width"]), float(dimensoes["height"])
        if not all(math.isfinite(v) and v > 0 for v in (largura, altura)):
            raise ValueError
        ids = [b["id"] for b in blocos]
        if len(set(ids)) != len(ids):
            raise ValueError
        if len(ordem) != len(ids) or len(set(ordem)) != len(ordem) or set(ordem) != set(ids):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("dimensoes invalidas, IDs repetidos ou ordem nao e permutacao completa") from exc
    regex = re.compile(padrao_marcacao) if padrao_marcacao is not None else None
    grupos = {k: [] for k in ("topo", "corpo", "marcas", "rodape")}
    chaves = {}
    for i, b in enumerate(blocos):
        try:
            x0, y0, x1, y1 = map(float, b["bbox"])
            if not all(math.isfinite(v) for v in (x0, y0, x1, y1)) or x1 < x0 or y1 < y0:
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"bbox invalida no bloco {b.get('id')!r}") from exc
        chaves[b["id"]] = (y0, x0, i)
        tokens = (b.get("text") or "").split()
        centro = (y0 + y1) / 2
        # Marcas tem precedencia mesmo quando aparecem nas margens.
        if regex is not None and tokens and all(regex.match(t) for t in tokens):
            grupo = "marcas"
        elif (variante == "geometria" and centro < limiar_topo * altura and y1 < limite_base_topo * altura
              or variante == "classe" and b.get(campo_classe) == classe_cabecalho):
            grupo = "topo"
        elif (variante == "geometria" and centro > limiar_rodape * altura
              or variante == "classe" and b.get(campo_classe) == classe_rodape):
            grupo = "rodape"
        else:
            grupo = "corpo"
        grupos[grupo].append(b["id"])
    corpo = set(grupos["corpo"])
    grupos["corpo"] = [bid for bid in ordem if bid in corpo]
    for grupo in ("topo", "marcas", "rodape"):
        grupos[grupo].sort(key=chaves.__getitem__)
    return grupos


def aplicar_margens(
    blocos: Sequence[Mapping], ordem: Sequence[Hashable], dimensoes: Mapping, *,
    variante: str = "geometria", limiar_topo: float = 0.07,
    limite_base_topo: float = 0.10, limiar_rodape: float = 0.95,
    padrao_marcacao: str | None = PADRAO_MARCACAO, campo_classe: str = "classe",
    classe_cabecalho: str = "cabecalho", classe_rodape: str = "rodape",
) -> list[Hashable]:
    """Devolve topo + corpo original + marcas + rodape, sem mutar entradas.

    Margens/marcas usam (top, x0, indice na lista de blocos), sem tolerancia
    vertical. Um titulo no topo pode ser falso cabecalho na variante geometrica.
    Uma caixa inteira e deslocada; tabelas e caixas com texto misto nao se partem.
    padrao_marcacao=None desativa apenas a regra de marcas.
    """
    grupos = _separar(blocos, ordem, dimensoes, variante=variante, limiar_topo=limiar_topo,
                      limite_base_topo=limite_base_topo, limiar_rodape=limiar_rodape,
                      padrao_marcacao=padrao_marcacao, campo_classe=campo_classe,
                      classe_cabecalho=classe_cabecalho, classe_rodape=classe_rodape)
    return [bid for grupo in ("topo", "corpo", "marcas", "rodape") for bid in grupos[grupo]]


def xycut_margens(
    pagina: Mapping, *, variante: str = "geometria", limiar_topo: float = 0.07,
    limite_base_topo: float = 0.10, limiar_rodape: float = 0.95,
    padrao_marcacao: str | None = PADRAO_MARCACAO, campo_classe: str = "classe",
    classe_cabecalho: str = "cabecalho", classe_rodape: str = "rodape",
) -> list[Hashable]:
    """XY-cut no corpo apos separar margens; retorna IDs como as baselines.

    Usa a entrada embaralhada fixa do protocolo. So consulta bounding_boxes,
    dimensions e page_id; a ordem silver/humana nao faz parte da entrada.
    """
    from src.data.extrator import xycut
    from src.eval.baselines import caixas
    from src.eval.protocolo import ordem_entrada

    blocos = pagina["bounding_boxes"]
    ids = [b["id"] for b in blocos]
    entrada = ordem_entrada(pagina)
    grupos = _separar(blocos, [ids[i] for i in entrada], pagina["dimensions"],
                      variante=variante, limiar_topo=limiar_topo,
                      limite_base_topo=limite_base_topo, limiar_rodape=limiar_rodape,
                      padrao_marcacao=padrao_marcacao, campo_classe=campo_classe,
                      classe_cabecalho=classe_cabecalho, classe_rodape=classe_rodape)
    corpo = set(grupos["corpo"])
    grupos["corpo"] = [ids[i] for i in xycut([i for i in entrada if ids[i] in corpo], caixas(pagina))]
    return [bid for grupo in ("topo", "corpo", "marcas", "rodape") for bid in grupos[grupo]]
