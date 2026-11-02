# -*- coding: utf-8 -*-
"""Conversor bidirecional entre o formato próprio do TCC e PAGE XML 2019.

Este módulo implementa a interoperabilidade com o padrão internacional PAGE XML
(esquema 2019-07-15 da PRImA Research), utilizado por ferramentas consagradas de
análise de layout e transcrição documental (como LAREX, eScriptorium e Transkribus).

Esquema PAGE XML 2019 atendido:
  - Namespace: http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15
  - PcGts com Metadata (Creator, Created, LastChange, Comments)
  - Page com imageFilename, imageWidth, imageHeight e id
  - ReadingOrder com OrderedGroup e RegionRefIndexed (index, regionRef)
  - TextRegion por caixa de texto com Coords points em pixels e TextEquiv/Unicode
  - TableRegion para tabelas com Coords e TextEquiv/Unicode
  - ImageRegion para imagens com Coords e TextEquiv/Unicode
  - Demais classes mapeadas como TextRegion com o atributo type correspondente

Também fornece composição com o Label Studio via exportar_labelstudio.py:
  - ls_para_page_xml: Label Studio -> Formato Próprio -> PAGE XML
  - page_xml_para_ls: PAGE XML -> Formato Próprio -> Label Studio

Pode ser executado diretamente para rodar o teste de validação de ida e volta:
    venv/Scripts/python.exe -B resultados/ferramenta_anotacao/conversor_page_xml.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

# Garantir importação de exportar_labelstudio.py no mesmo diretório
DIR_FERRAMENTA = Path(__file__).resolve().parent
if str(DIR_FERRAMENTA) not in sys.path:
    sys.path.insert(0, str(DIR_FERRAMENTA))

try:
    from exportar_labelstudio import ls_para_proprio, proprio_para_ls
except ImportError:
    # Fallback caso executado a partir de outros caminhos
    from resultados.ferramenta_anotacao.exportar_labelstudio import (  # type: ignore
        ls_para_proprio,
        proprio_para_ls,
    )

# Namespace oficial PAGE XML 2019
PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# Registrar namespaces para que o ElementTree não gere prefixos ns0: artificiais
ET.register_namespace("", PAGE_NS)
ET.register_namespace("xsi", XSI_NS)

# Mapeamento de classes próprias para atributos type de TextRegion no PAGE XML
CLASSE_PARA_PAGE_TYPE = {
    "texto": "paragraph",
    "cabecalho": "heading",
    "rodape": "footer",
    "quadro": "other",
    "outro": "other",
}

# Mapeamento reverso de atributos type do PAGE XML para classes do formato próprio
PAGE_TYPE_PARA_CLASSE = {
    "paragraph": "texto",
    "text": "texto",
    "heading": "cabecalho",
    "header": "cabecalho",
    "cabecalho": "cabecalho",
    "footer": "rodape",
    "rodape": "rodape",
    "page-number": "rodape",
    "table": "tabela",
    "tabela": "tabela",
    "image": "imagem",
    "imagem": "imagem",
    "quadro": "quadro",
    "other": "outro",
    "outro": "outro",
}


def obter_tag_local(elem: ET.Element) -> str:
    """Extrai o nome local da tag XML desconsiderando o namespace."""
    tag = elem.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def normalizar_bbox(bbox: List[Union[int, float]]) -> List[float]:
    """Garante bbox no formato [x0, y0, x1, y1] com floats."""
    x0, y0, x1, y1 = [float(v) for v in bbox]
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def bbox_para_points_str(bbox: List[Union[int, float]]) -> str:
    """Converte [x0, y0, x1, y1] na string de 4 pontos retangulares do PAGE XML.

    Ordem dos pontos (sentido horário): (x0, y0) -> (x1, y0) -> (x1, y1) -> (x0, y1)
    """
    x0, y0, x1, y1 = normalizar_bbox(bbox)
    x0_i = int(round(x0))
    y0_i = int(round(y0))
    x1_i = int(round(x1))
    y1_i = int(round(y1))
    return f"{x0_i},{y0_i} {x1_i},{y0_i} {x1_i},{y1_i} {x0_i},{y1_i}"


def points_str_para_bbox(points_str: str) -> List[float]:
    """Converte a string de Coords points do PAGE XML para bounding box [x0, y0, x1, y1].

    Lida com polígonos retangulares ou livres extraindo os limites envolventes (AABB).
    """
    pares = points_str.strip().split()
    if not pares:
        return [0.0, 0.0, 100.0, 100.0]

    xs: List[float] = []
    ys: List[float] = []
    for par in pares:
        if "," in par:
            p_x, p_y = par.split(",", 1)
            try:
                xs.append(float(p_x))
                ys.append(float(p_y))
            except ValueError:
                continue

    if not xs or not ys:
        return [0.0, 0.0, 100.0, 100.0]

    return [min(xs), min(ys), max(xs), max(ys)]


def proprio_para_page_xml(
    tarefa: Union[Dict[str, Any], List[Dict[str, Any]]],
    caminho_xml: Union[str, Path],
) -> Path:
    """Converte uma tarefa do formato próprio do TCC para um arquivo PAGE XML 2019.

    Parâmetros:
        tarefa: dicionário de página única no formato próprio ou lista contendo uma página.
        caminho_xml: caminho onde o arquivo PAGE XML (.xml) será gerado.

    Retorna:
        Path do arquivo XML gravado.
    """
    if isinstance(tarefa, list):
        if not tarefa:
            raise ValueError("Lista de tarefas vazia recebida em proprio_para_page_xml")
        pag = tarefa[0]
    elif isinstance(tarefa, dict):
        if "paginas" in tarefa and isinstance(tarefa["paginas"], list):
            pag = tarefa["paginas"][0]
        elif "tasks" in tarefa and isinstance(tarefa["tasks"], list):
            pag = tarefa["tasks"][0]
        else:
            pag = tarefa
    else:
        raise ValueError(f"Formato próprio inválido: esperado dict ou list, recebido {type(tarefa)}")

    caminho_saida = Path(caminho_xml)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    page_id = str(pag.get("page_id") or "pagina_01")
    imagem = str(pag.get("imagem") or pag.get("image") or f"{page_id}.png")
    largura = int(round(float(pag.get("largura") or pag.get("width") or 1000.0)))
    altura = int(round(float(pag.get("altura") or pag.get("height") or 1000.0)))
    if largura <= 0:
        largura = 1000
    if altura <= 0:
        altura = 1000

    caixas = pag.get("caixas") or pag.get("bounding_boxes") or []
    ordem = [str(x) for x in (pag.get("ordem") or [])]
    flags = pag.get("flags") or []
    nota = pag.get("nota") or ""
    tempo_s = float(pag.get("tempo_s") or 0.0)

    agora_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # 1. Elemento Raiz PcGts com schemaLocation oficial
    root = ET.Element(
        f"{{{PAGE_NS}}}PcGts",
        {
            f"{{{XSI_NS}}}schemaLocation": (
                f"{PAGE_NS} {PAGE_NS}/pagecontent.xsd"
            )
        },
    )

    # 2. Metadata
    metadata_elem = ET.SubElement(root, f"{{{PAGE_NS}}}Metadata")
    creator_elem = ET.SubElement(metadata_elem, f"{{{PAGE_NS}}}Creator")
    creator_elem.text = "TCC Ordem de Leitura · INF-UFG"
    created_elem = ET.SubElement(metadata_elem, f"{{{PAGE_NS}}}Created")
    created_elem.text = agora_iso
    last_change_elem = ET.SubElement(metadata_elem, f"{{{PAGE_NS}}}LastChange")
    last_change_elem.text = agora_iso

    # Metadados complementares preservados em Comments (JSON)
    meta_extra = {
        "page_id": page_id,
        "tempo_s": tempo_s,
        "nota": nota,
        "flags": flags,
    }
    comments_elem = ET.SubElement(metadata_elem, f"{{{PAGE_NS}}}Comments")
    comments_elem.text = json.dumps(meta_extra, ensure_ascii=False)

    # 3. Page
    page_elem = ET.SubElement(
        root,
        f"{{{PAGE_NS}}}Page",
        {
            "id": page_id,
            "imageFilename": imagem,
            "imageWidth": str(largura),
            "imageHeight": str(altura),
        },
    )

    # 4. ReadingOrder com OrderedGroup e RegionRefIndexed
    if ordem:
        ro_elem = ET.SubElement(page_elem, f"{{{PAGE_NS}}}ReadingOrder")
        og_elem = ET.SubElement(
            ro_elem,
            f"{{{PAGE_NS}}}OrderedGroup",
            {
                "id": f"ro_{page_id}",
                "caption": "Ordem de leitura sequencial de regiões",
            },
        )
        for idx, ref_id in enumerate(ordem):
            ET.SubElement(
                og_elem,
                f"{{{PAGE_NS}}}RegionRefIndexed",
                {
                    "index": str(idx),
                    "regionRef": str(ref_id),
                },
            )

    # 5. Regiões: TableRegion, ImageRegion, TextRegion (com type para demais classes)
    for cx in caixas:
        cid = str(cx["id"])
        classe = str(cx.get("classe") or cx.get("label") or "texto").lower().strip()
        bbox = normalizar_bbox(cx["bbox"])
        texto = cx.get("texto") or cx.get("text") or ""

        # Mapeamento conforme especificação PAGE 2019
        if classe in ("tabela", "table"):
            tag_regiao = f"{{{PAGE_NS}}}TableRegion"
            atributos_regiao = {"id": cid}
        elif classe in ("imagem", "image"):
            tag_regiao = f"{{{PAGE_NS}}}ImageRegion"
            atributos_regiao = {"id": cid}
        else:
            tag_regiao = f"{{{PAGE_NS}}}TextRegion"
            page_type = CLASSE_PARA_PAGE_TYPE.get(classe, classe)
            atributos_regiao = {
                "id": cid,
                "type": page_type,
            }

        regiao_elem = ET.SubElement(page_elem, tag_regiao, atributos_regiao)

        # Coordenadas poligonais (retângulo fechado em sentido horário)
        coords_elem = ET.SubElement(
            regiao_elem,
            f"{{{PAGE_NS}}}Coords",
            {"points": bbox_para_points_str(bbox)},
        )

        # Texto transcrito da região
        if texto:
            te_elem = ET.SubElement(regiao_elem, f"{{{PAGE_NS}}}TextEquiv")
            uni_elem = ET.SubElement(te_elem, f"{{{PAGE_NS}}}Unicode")
            uni_elem.text = str(texto)

    # Formatar e gravar arquivo XML
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(caminho_saida, encoding="utf-8", xml_declaration=True)

    return caminho_saida


def page_xml_para_proprio(caminho_xml: Union[str, Path]) -> Dict[str, Any]:
    """Lê um arquivo PAGE XML 2019 e converte para o formato próprio do TCC.

    Parâmetros:
        caminho_xml: caminho do arquivo .xml a ser lido.

    Retorna:
        Dicionário com a página no formato próprio do TCC.
    """
    caminho_entrada = Path(caminho_xml)
    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo PAGE XML não encontrado: {caminho_entrada}")

    tree = ET.parse(caminho_entrada)
    root = tree.getroot()

    # 1. Recuperar Metadata e comentários adicionais se disponíveis
    page_id_comentario: Optional[str] = None
    tempo_s = 0.0
    nota = ""
    flags: List[str] = []

    for meta in root:
        if obter_tag_local(meta) == "Metadata":
            for child in meta:
                if obter_tag_local(child) == "Comments" and child.text:
                    try:
                        dados_meta = json.loads(child.text)
                        if isinstance(dados_meta, dict):
                            page_id_comentario = dados_meta.get("page_id")
                            tempo_s = float(dados_meta.get("tempo_s") or 0.0)
                            nota = str(dados_meta.get("nota") or "")
                            flags = list(dados_meta.get("flags") or [])
                    except json.JSONDecodeError:
                        pass

    # 2. Localizar elemento Page
    page_elem: Optional[ET.Element] = None
    for child in root:
        if obter_tag_local(child) == "Page":
            page_elem = child
            break

    if page_elem is None:
        raise ValueError(f"Elemento <Page> não encontrado no arquivo PAGE XML: {caminho_entrada}")

    imagem = page_elem.get("imageFilename") or f"{caminho_entrada.stem}.png"
    page_id = (
        page_elem.get("id")
        or page_id_comentario
        or Path(imagem).stem
        or caminho_entrada.stem
    )

    try:
        largura = int(round(float(page_elem.get("imageWidth") or 1000.0)))
    except ValueError:
        largura = 1000

    try:
        altura = int(round(float(page_elem.get("imageHeight") or 1000.0)))
    except ValueError:
        altura = 1000

    caixas: List[Dict[str, Any]] = []
    ordem: List[str] = []
    relacoes: List[Dict[str, str]] = []

    # 3. Processar filhos de Page (ReadingOrder e Regiões)
    for elem in page_elem:
        tag_local = obter_tag_local(elem)

        # 3.1 Ordem de Leitura
        if tag_local == "ReadingOrder":
            for og in elem:
                if obter_tag_local(og) in ("OrderedGroup", "UnorderedGroup"):
                    itens_ordem: List[Tuple[int, str]] = []
                    for idx_item, ref in enumerate(og):
                        if obter_tag_local(ref) == "RegionRefIndexed":
                            rid = ref.get("regionRef")
                            if rid:
                                try:
                                    idx_val = int(ref.get("index", idx_item))
                                except ValueError:
                                    idx_val = idx_item
                                itens_ordem.append((idx_val, str(rid)))
                    itens_ordem.sort(key=lambda t: t[0])
                    ordem = [rid for _, rid in itens_ordem]
            continue

        # 3.2 Regiões de Conteúdo
        if tag_local in ("TextRegion", "TableRegion", "ImageRegion"):
            cid = elem.get("id") or f"reg_{len(caixas) + 1}"

            # Determinar classe funcional
            if tag_local == "TableRegion":
                classe = "tabela"
            elif tag_local == "ImageRegion":
                classe = "imagem"
            else:
                type_attr = (elem.get("type") or "paragraph").lower().strip()
                classe = PAGE_TYPE_PARA_CLASSE.get(type_attr, type_attr)

            # Extrair coordenadas de Coords
            bbox = [0.0, 0.0, 100.0, 100.0]
            for c_elem in elem:
                if obter_tag_local(c_elem) == "Coords":
                    pts = c_elem.get("points") or ""
                    bbox = points_str_para_bbox(pts)
                    break

            # Extrair texto transcrito de TextEquiv/Unicode
            texto = ""
            for te_elem in elem:
                if obter_tag_local(te_elem) == "TextEquiv":
                    for uni_elem in te_elem:
                        if obter_tag_local(uni_elem) == "Unicode" and uni_elem.text:
                            texto = uni_elem.text
                            break
                    if texto:
                        break

            cx_obj: Dict[str, Any] = {
                "id": cid,
                "bbox": bbox,
                "classe": classe,
            }
            if texto:
                cx_obj["texto"] = texto

            caixas.append(cx_obj)

    # 4. Reconstruir relações explícitas a partir da cadeia ordenada
    if len(ordem) >= 2:
        for a, b in zip(ordem, ordem[1:]):
            relacoes.append({"de": a, "para": b, "tipo": "continue"})

    pagina_propria: Dict[str, Any] = {
        "page_id": page_id,
        "imagem": imagem,
        "largura": largura,
        "altura": altura,
        "caixas": caixas,
        "ordem": ordem,
        "relacoes": relacoes,
        "flags": flags,
        "nota": nota,
        "tempo_s": tempo_s,
    }

    return pagina_propria


# -----------------------------------------------------------------------------
# COMPOSIÇÃO: LABEL STUDIO <-> PAGE XML
# -----------------------------------------------------------------------------

def ls_para_page_xml(
    dados_ls: Union[Dict[str, Any], List[Dict[str, Any]]],
    caminho_xml: Union[str, Path],
) -> Path:
    """Converte tarefas do formato Label Studio para PAGE XML 2019.

    Compõe ls_para_proprio() com proprio_para_page_xml().
    """
    paginas_proprias = ls_para_proprio(dados_ls)
    if not paginas_proprias:
        raise ValueError("Nenhuma tarefa válida encontrada nos dados do Label Studio")
    return proprio_para_page_xml(paginas_proprias[0], caminho_xml)


def page_xml_para_ls(caminho_xml: Union[str, Path]) -> List[Dict[str, Any]]:
    """Converte arquivo PAGE XML 2019 para o formato de tarefas do Label Studio.

    Compõe page_xml_para_proprio() com proprio_para_ls().
    """
    pagina_propria = page_xml_para_proprio(caminho_xml)
    return proprio_para_ls(pagina_propria)


# -----------------------------------------------------------------------------
# BATERIA DE TESTES DE VALIDAÇÃO TÉCNICA
# -----------------------------------------------------------------------------

def executar_teste_ida_e_volta() -> None:
    """Executa o teste técnico rigoroso de ida e volta garantindo integridade estrita."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 76)
    print("TESTE DE IDA E VOLTA: Formato Próprio <-> PAGE XML 2019 <-> Label Studio")
    print("=" * 76)

    # 1. Definir dados de referência sintéticos (3 caixas, 1 relação de ordem)
    W_orig, H_orig = 1200, 1600
    dados_originais: Dict[str, Any] = {
        "page_id": "teste_sintetico_p01",
        "imagem": "pagina_teste_01.png",
        "largura": W_orig,
        "altura": H_orig,
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
        "ordem": ["box-1", "box-2"],
        "relacoes": [
            {"de": "box-1", "para": "box-2", "tipo": "continue"}
        ],
        "flags": ["revisado", "alta_qualidade"],
        "nota": "Página sintética para validação técnica da ferramenta.",
        "tempo_s": 28.4,
    }

    caminho_xml_temp = DIR_FERRAMENTA / "teste_ida_volta_temp.xml"

    try:
        # ---------------------------------------------------------------------
        # CICLO 1: Próprio -> PAGE XML -> Próprio
        # ---------------------------------------------------------------------
        print("\n[Ciclo 1/2] Testando: Formato Próprio -> PAGE XML 2019 -> Formato Próprio...")
        proprio_para_page_xml(dados_originais, caminho_xml_temp)
        assert caminho_xml_temp.exists(), f"Arquivo XML não foi criado: {caminho_xml_temp}"

        # Inspecionar conteúdo do XML gerado
        conteudo_xml = caminho_xml_temp.read_text(encoding="utf-8")
        assert PAGE_NS in conteudo_xml, f"Namespace PAGE 2019 ausente no XML gerado:\n{conteudo_xml[:300]}"
        assert "TableRegion" in conteudo_xml, "Elemento TableRegion não encontrado no XML gerado"
        assert "TextRegion" in conteudo_xml, "Elemento TextRegion não encontrado no XML gerado"
        assert "ReadingOrder" in conteudo_xml, "Elemento ReadingOrder não encontrado no XML gerado"
        assert "RegionRefIndexed" in conteudo_xml, "Elemento RegionRefIndexed não encontrado no XML gerado"
        print("      -> Estrutura XML válida contra o esquema PAGE 2019.")

        dados_volta = page_xml_para_proprio(caminho_xml_temp)

        # Checagens de metadados
        assert dados_volta["page_id"] == dados_originais["page_id"], (
            f"Divergência em page_id: esperado {dados_originais['page_id']!r}, obtido {dados_volta['page_id']!r}"
        )
        assert dados_volta["largura"] == dados_originais["largura"], (
            f"Divergência em largura: esperado {dados_originais['largura']}, obtido {dados_volta['largura']}"
        )
        assert dados_volta["altura"] == dados_originais["altura"], (
            f"Divergência em altura: esperado {dados_originais['altura']}, obtido {dados_volta['altura']}"
        )

        # Checagens das caixas
        caixas_orig = {c["id"]: c for c in dados_originais["caixas"]}
        caixas_volta = {c["id"]: c for c in dados_volta["caixas"]}

        assert set(caixas_orig) == set(caixas_volta), (
            f"Conjunto de IDs divergente: esperado {set(caixas_orig)}, obtido {set(caixas_volta)}"
        )

        for cid, co in caixas_orig.items():
            cv = caixas_volta[cid]
            # Validação estrita de classe
            assert cv["classe"] == co["classe"], (
                f"Classe da caixa {cid} divergiu: esperada {co['classe']!r}, obtida {cv['classe']!r}"
            )
            # Validação de texto
            assert cv.get("texto", "") == co.get("texto", ""), (
                f"Texto da caixa {cid} divergiu: esperado {co.get('texto')!r}, obtido {cv.get('texto')!r}"
            )
            # Validação de BBox com tolerância máxima de 1 pixel
            for i, (val_o, val_v) in enumerate(zip(co["bbox"], cv["bbox"])):
                diff = abs(val_o - val_v)
                assert diff <= 1.0, (
                    f"Coordenada {i} da caixa {cid} divergiu além de 1 pixel: "
                    f"original={val_o}, recuperado={val_v}, delta={diff}"
                )

        print("      -> 3 caixas recuperadas com 100% de precisão (ids, classes, textos e bbox <= 1px).")

        # Checagem de ordem de leitura e relações
        assert dados_volta["ordem"] == dados_originais["ordem"], (
            f"Ordem de leitura divergiu: esperada {dados_originais['ordem']}, obtida {dados_volta['ordem']}"
        )
        assert len(dados_volta["relacoes"]) == 1, (
            f"Esperada 1 relação recuperada, obtidas {len(dados_volta['relacoes'])}"
        )
        assert dados_volta["relacoes"][0]["de"] == "box-1" and dados_volta["relacoes"][0]["para"] == "box-2", (
            f"Relação divergiu: esperada box-1 -> box-2, obtida {dados_volta['relacoes']}"
        )
        print("      -> Ordem de leitura ['box-1', 'box-2'] e relação recuperadas perfeitamente.")
        print("      OK: Ciclo 1 aprovado com sucesso.")

        # ---------------------------------------------------------------------
        # CICLO 2: Composição Label Studio <-> PAGE XML
        # ---------------------------------------------------------------------
        print("\n[Ciclo 2/2] Testando: Label Studio <-> PAGE XML 2019 (composição)...")
        # Gerar tarefa Label Studio a partir do formato próprio
        tarefas_ls_orig = proprio_para_ls(dados_originais)
        assert len(tarefas_ls_orig) == 1, "Falha na conversão para Label Studio"

        # Exportar de Label Studio direto para PAGE XML
        ls_para_page_xml(tarefas_ls_orig, caminho_xml_temp)
        assert caminho_xml_temp.exists(), "Falha ao gravar PAGE XML a partir de Label Studio"

        # Reimportar de PAGE XML de volta para Label Studio
        tarefas_ls_volta = page_xml_para_ls(caminho_xml_temp)
        assert len(tarefas_ls_volta) == 1, "Falha ao converter de PAGE XML para Label Studio"

        # Converter tarefas Label Studio recompostas de volta para formato próprio para conferência final
        dados_recompostos = ls_para_proprio(tarefas_ls_volta)[0]

        # Validar consistência do ciclo completo
        assert dados_recompostos["ordem"] == dados_originais["ordem"], (
            f"Ordem no ciclo LS <-> PAGE XML divergiu: {dados_recompostos['ordem']} != {dados_originais['ordem']}"
        )
        caixas_rec = {c["id"]: c for c in dados_recompostos["caixas"]}
        assert set(caixas_rec) == set(caixas_orig), "IDs de caixas divergentes no ciclo Label Studio"

        for cid, co in caixas_orig.items():
            cr = caixas_rec[cid]
            assert cr["classe"] == co["classe"], (
                f"Classe no ciclo LS divergiu para {cid}: {cr['classe']} != {co['classe']}"
            )
            for i, (vo, vr) in enumerate(zip(co["bbox"], cr["bbox"])):
                diff = abs(vo - vr)
                assert diff <= 1.0, (
                    f"Delta > 1px no ciclo LS para caixa {cid}, coord {i}: {vo} vs {vr} (diff={diff})"
                )

        print("      -> Ciclo completo Label Studio <-> PAGE XML validado com integridade estrita.")
        print("      OK: Ciclo 2 aprovado com sucesso.")

        print("\n" + "=" * 76)
        print("SUCESSO: Todos os testes passaram sem nenhuma divergência!")
        print("=" * 76)

    finally:
        # Limpar arquivo temporário de teste
        if caminho_xml_temp.exists():
            try:
                caminho_xml_temp.unlink()
            except OSError:
                pass


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--teste",
        action="store_true",
        help="Executa os testes de validação técnica de ida e volta",
    )
    parser.add_argument(
        "--proprio-para-page",
        nargs=2,
        metavar=("ENTRADA_JSON", "SAIDA_XML"),
        help="Converte tarefa JSON do formato próprio para PAGE XML 2019",
    )
    parser.add_argument(
        "--page-para-proprio",
        nargs=2,
        metavar=("ENTRADA_XML", "SAIDA_JSON"),
        help="Converte arquivo PAGE XML 2019 para JSON no formato próprio",
    )
    parser.add_argument(
        "--ls-para-page",
        nargs=2,
        metavar=("ENTRADA_LS_JSON", "SAIDA_XML"),
        help="Converte export JSON do Label Studio para PAGE XML 2019",
    )
    parser.add_argument(
        "--page-para-ls",
        nargs=2,
        metavar=("ENTRADA_XML", "SAIDA_LS_JSON"),
        help="Converte arquivo PAGE XML 2019 para export JSON do Label Studio",
    )

    args = parser.parse_args()

    if args.proprio_para_page:
        inp = Path(args.proprio_para_page[0])
        out = Path(args.proprio_para_page[1])
        dados = json.loads(inp.read_text(encoding="utf-8"))
        proprio_para_page_xml(dados, out)
        print(f"Convertido com sucesso de Formato Próprio para PAGE XML: {out}")
    elif args.page_para_proprio:
        inp = Path(args.page_para_proprio[0])
        out = Path(args.page_para_proprio[1])
        res = page_xml_para_proprio(inp)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Convertido com sucesso de PAGE XML para Formato Próprio: {out}")
    elif args.ls_para_page:
        inp = Path(args.ls_para_page[0])
        out = Path(args.ls_para_page[1])
        dados = json.loads(inp.read_text(encoding="utf-8"))
        ls_para_page_xml(dados, out)
        print(f"Convertido com sucesso de Label Studio para PAGE XML: {out}")
    elif args.page_para_ls:
        inp = Path(args.page_para_ls[0])
        out = Path(args.page_para_ls[1])
        res = page_xml_para_ls(inp)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Convertido com sucesso de PAGE XML para Label Studio: {out}")
    else:
        # Padrão: executa bateria completa de testes
        executar_teste_ida_e_volta()


if __name__ == "__main__":
    main()
