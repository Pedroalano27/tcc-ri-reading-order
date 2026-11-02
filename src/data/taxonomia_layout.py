# -*- coding: utf-8 -*-
"""
Taxonomia de layout do PROJETO (guia de anotacao "Diarios Oficiais") e os mapeamentos entre ela,
as 9 classes do extrator atual e os rotulos crus do detector Docling.

Decisao (19/09/2026, quadro): o extrator passa a falar a taxonomia do guia, para (a) treinar no
dataset rotulado a mao do projeto (LabelStudio) e (b) ser comparavel ao projeto de pesquisa.
Ver COMUNICACAO_AGENTES.md e docs/GUIA_DIAMOND.md.

Este modulo NAO detecta nada; so define o vocabulario e as traducoes. As distincoes SEMANTICAS que
o extrator ainda nao faz (marcadas com # PRECISA LOGICA) exigem regras/ modelo:
  - act vs title      : "e ato normativo?" (DECRETO/PORTARIA/RESOLVE... vs titulo comum)
  - act section       : subtitulo/divisao interna de ato (Art., Paragrafo, CAPITULO)
  - id                : identificadores/protocolos/nº processo/campos chave-valor
  - caption           : legenda de tabela/figura/grafico
  - chart             : grafico de dados (vs figura)
  - signature vs heading : bloco de assinatura textual/digital vs rubrica MANUSCRITA
"""
from __future__ import annotations

# --- Taxonomia do guia (tabela da secao 11: label -> (atalho, funcao)) ---
# Ordem = ordem de decisao do guia (secao 10): normativo primeiro, depois recorrente, visual, id.
LABELS_GUIA = {
    "act":              ("t", "Titulo de ato normativo"),
    "act section":      ("a", "Subtitulo ou divisao interna de ato"),
    "paragraph":        ("5", "Texto corrente"),
    "signature":        ("q", "Bloco textual ou digital de assinatura"),
    "heading":          ("w", "Assinatura manuscrita ou rubrica"),
    "id":               ("0", "Identificadores, protocolos e codigos"),
    "header":           ("1", "Cabecalho geral da pagina (recorrente, topo)"),
    "footer":           ("2", "Rodape geral da pagina (recorrente, base)"),
    "table":            ("6", "Estrutura tabular"),
    "chart":            ("e", "Grafico de dados"),
    "figure":           ("7", "Imagem, fotografia, mapa ou ilustracao"),
    "caption":          ("8", "Legenda de tabela, figura ou grafico"),
    "title":            ("3", "Titulo principal de documento NAO normativo"),
    "section title":    ("4", "Titulo de secao de documento nao normativo"),
    "sub section title":("9", "Titulo de subsecao de documento nao normativo"),
    "unknown":          ("u", "Classificacao duvidosa"),
}
GUIA = tuple(LABELS_GUIA)  # 16 classes

# --- Guia -> 9 classes do extrator atual (colapso; sempre bem definido) ---
GUIA_PARA_EXTRATOR = {
    "act": "titulo", "act section": "titulo",
    "title": "titulo", "section title": "titulo", "sub section title": "titulo",
    "paragraph": "texto",
    "id": "texto",
    "table": "tabela",
    "figure": "figura", "chart": "figura",
    "caption": "texto",
    "signature": "assinatura", "heading": "assinatura",
    "header": "cabecalho", "footer": "rodape",
    "unknown": "outro",
}

# --- 9 classes do extrator -> guia (melhor esforco; 1->1 quando da, com ressalva) ---
# Onde o guia distingue mais que o extrator, escolhemos o rotulo mais provavel e marcamos a duvida.
EXTRATOR_PARA_GUIA = {
    "titulo": "title",        # PRECISA LOGICA: act se for ato normativo
    "texto": "paragraph",     # PRECISA LOGICA: id se for protocolo/campo; act section se for Art./§
    "lista": "paragraph",     # o guia NAO tem classe "lista": itens viram paragraph
    "tabela": "table",
    "assinatura": "signature",# PRECISA LOGICA: heading se for rubrica manuscrita
    "cabecalho": "header",
    "rodape": "footer",
    "figura": "figure",       # PRECISA LOGICA: chart se for grafico de dados
    "outro": "unknown",
}

# --- Docling (rotulo cru do detector) -> guia ---
# Base para o caminho "detector + regras" ja falar a taxonomia do guia sem re-treinar.
DOCLING_PARA_GUIA = {
    "title": "title", "section_header": "section title",   # PRECISA LOGICA: act se normativo
    "text": "paragraph",
    "list_item": "paragraph",                              # guia nao tem lista
    "table": "table", "document_index": "table",
    "picture": "figure",
    "caption": "caption",
    "footnote": "paragraph",
    "formula": "paragraph", "code": "paragraph",
    "page_header": "header", "page_footer": "footer",
    "key_value_region": "id",                              # campos chave-valor administrativos
    "form": "unknown", "checkbox_selected": "unknown", "checkbox_unselected": "unknown",
}

# Classes que exigem funcao semantica (o guia diz que dependem da funcao, nao so da aparencia)
PRECISA_SEMANTICA = ("act", "act section", "signature", "heading", "id")


def para_guia_do_extrator(classe_extrator: str) -> str:
    """9 classes -> guia (melhor esforco, sem contexto)."""
    return EXTRATOR_PARA_GUIA.get(classe_extrator, "unknown")


def para_extrator_do_guia(classe_guia: str) -> str:
    """guia -> 9 classes (colapso bem definido), util para medir no teste antigo."""
    return GUIA_PARA_EXTRATOR.get(classe_guia, "outro")


def para_guia_do_docling(rotulo: str) -> str:
    """rotulo cru do Docling -> guia."""
    return DOCLING_PARA_GUIA.get(rotulo, "unknown")


if __name__ == "__main__":  # sanidade: toda classe do guia tem colapso; todo mapa aponta para o guia
    assert set(GUIA_PARA_EXTRATOR) == set(GUIA), set(GUIA) ^ set(GUIA_PARA_EXTRATOR)
    assert all(v in GUIA for v in EXTRATOR_PARA_GUIA.values())
    assert all(v in GUIA for v in DOCLING_PARA_GUIA.values())
    print(f"OK: {len(GUIA)} classes do guia; mapeamentos consistentes.")
    print("guia -> extrator:", GUIA_PARA_EXTRATOR)
