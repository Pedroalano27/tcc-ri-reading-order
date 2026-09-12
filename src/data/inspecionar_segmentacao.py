"""
Gera imagens de inspecao visual das quatro paginas-problema da segmentacao.

Por que existe:
    Para decidir qual versao da segmentacao adotar no TCC (tarefa T03), e
    necessario inspecionar visualmente como cada versao (v1, B e C) desenha os
    blocos de texto nas quatro paginas que concentram as maiores anomalias:
    entrada em negrito (MA), texto justificado (SE), tres colunas (RJ) e texto
    corrido fundido (CE).

O que faz:
    1. Obtem os blocos de texto das tres fontes:
       - v1: colecao armazenada em data/processed/blocos_v1/<veiculo>.jsonl;
       - B:  colecao armazenada em data/processed/blocos/<veiculo>.jsonl;
       - C:  codigo atual de src/data/extrator.py executado ao vivo sobre o PDF.
    2. Renderiza a pagina do PDF a 110 dpi via pdfplumber.to_image(resolution=110).
    3. Desenha o contorno de cada bloco com o codigo de cores da especificacao:
       - Vermelho: bloco com mais de 250 palavras (>250);
       - Laranja:  caixa se sobrepoe a outra (intersecao >= 25% da area da menor caixa,
                   conforme regra de src/data/reextrair.py:qualidade);
       - Cinza:    bloco de apenas uma palavra;
       - Azul:     demais blocos.
    4. Adiciona faixa informativa no topo de cada imagem com: rotulo da pagina,
       versao, numero de blocos, % de blocos sobrepostos, blocos >250 palavras
       e blocos de uma palavra.
    5. Gera painel comparativo lado a lado (<rotulo>_comparativo.png) com PIL.
    6. Salva resultados/inspecao_segmentacao/contagens.json com estatisticas consolidadas.

Uso:
    venv/Scripts/python.exe src/data/inspecionar_segmentacao.py
    venv/Scripts/python.exe src/data/inspecionar_segmentacao.py --rotulo-atual final

--rotulo-atual da nome ao painel do codigo atual (padrao C). Com outro nome, as imagens e o
JSON saem com esse sufixo, sem sobrescrever os da versao C, que ficam como evidencia.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
import pdfplumber
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.data.extrator import palavras_da_pagina, segmentar  # noqa: E402

DIR_RAW = os.path.join(RAIZ, "data", "raw")
DIR_V1 = os.path.join(RAIZ, "data", "processed", "blocos_v1")
DIR_B = os.path.join(RAIZ, "data", "processed", "blocos")
DIR_SAIDA = os.path.join(RAIZ, "resultados", "inspecao_segmentacao")
ARQ_CONTAGENS = os.path.join(DIR_SAIDA, "contagens.json")

# Codigo de cores da especificacao
COR_VERMELHO = (220, 38, 38)     # > 250 palavras
COR_LARANJA = (234, 88, 12)      # sobreposicao >= 25% da menor
COR_CINZA = (107, 114, 128)      # 1 palavra
COR_AZUL = (37, 99, 235)         # normal / demais

PAGINAS_PROBLEMA = [
    {
        "rotulo": "MA_negrito",
        "veiculo": "official_diary_ma",
        "arquivo": "executive_official_diary_2024-01-18_22_36.pdf",
        "pagina": 0,
        "descricao": "entrada em negrito",
    },
    {
        "rotulo": "SE_justificado",
        "veiculo": "official_diary_se",
        "arquivo": "DOE-SE_2023-03-10_5100.pdf",
        "pagina": 14,
        "descricao": "texto justificado",
    },
    {
        "rotulo": "RJ_tres_colunas",
        "veiculo": "official_diary_rj",
        "arquivo": "Parte II (Poder Legislativo)_2024-02-06.pdf",
        "pagina": 1,
        "descricao": "tres colunas",
    },
    {
        "rotulo": "CE_texto_corrido",
        "veiculo": "official_diary_ce",
        "arquivo": "do20250314p03.pdf",
        "pagina": 45,
        "descricao": "texto corrido",
    },
]


def carregar_fonte(tamanho: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Tenta carregar fonte TrueType do sistema operacional com fallback."""
    candidatos = (
        ["arialbd.ttf", "calibrib.ttf", "segoeuib.ttf"]
        if bold
        else ["arial.ttf", "calibri.ttf", "segoeui.ttf"]
    )
    for nome in candidatos:
        try:
            return ImageFont.truetype(nome, tamanho)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except Exception:
        return ImageFont.load_default()


def encontrar_pdf(veiculo: str, arquivo: str) -> str:
    """Localiza o arquivo PDF recursivamente sob data/raw/<veiculo>/."""
    caminho_direto = os.path.join(DIR_RAW, veiculo, arquivo)
    if os.path.isfile(caminho_direto):
        return caminho_direto
    padrao = os.path.join(DIR_RAW, veiculo, "**", arquivo)
    matches = glob.glob(padrao, recursive=True)
    if matches:
        return matches[0]
    raise FileNotFoundError(f"PDF nao encontrado: {veiculo}/{arquivo} em {DIR_RAW}")


def carregar_bloco_jsonl(pasta: str, veiculo: str, page_id: str) -> list[dict] | None:
    """Busca a linha com o page_id no arquivo JSONL do veiculo."""
    caminho = os.path.join(pasta, f"{veiculo}.jsonl")
    if not os.path.isfile(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            try:
                doc = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if doc.get("page_id") == page_id:
                caixas = []
                for b in doc.get("bounding_boxes", []):
                    caixas.append({
                        "bbox": b["bbox"],
                        "texto": b.get("text", ""),
                    })
                return caixas
    return None


def extrair_bloco_codigo_atual(pagina_pdf) -> list[dict]:
    """Segmenta a pagina do PDF ao vivo com o codigo atual de extrator.py."""
    palavras = palavras_da_pagina(pagina_pdf)
    blocos_brutos = segmentar(palavras)
    caixas = []
    for b in blocos_brutos:
        caixas.append({
            "bbox": [b["x0"], b["top"], b["x1"], b["bottom"]],
            "texto": b.get("texto", ""),
        })
    return caixas


def detectar_sobreposicoes(blocos: list[dict]) -> set[int]:
    """
    Identifica indices dos blocos que se sobrepoem a outro em pelo menos 25%
    da area da menor caixa, seguindo a funcao qualidade() de src/data/reextrair.py.
    """
    n = len(blocos)
    marcados = set()
    for i in range(n):
        ax0, ay0, ax1, ay1 = blocos[i]["bbox"]
        aa = max(1e-6, (ax1 - ax0) * (ay1 - ay0))
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = blocos[j]["bbox"]
            ab = max(1e-6, (bx1 - bx0) * (by1 - by0))
            iw = min(ax1, bx1) - max(ax0, bx0)
            ih = min(ay1, by1) - max(ay0, by0)
            if iw > 1 and ih > 1 and (iw * ih) / min(aa, ab) >= 0.25:
                marcados.add(i)
                marcados.add(j)
    return marcados


def calcular_metricas(blocos: list[dict] | None) -> dict:
    """Calcula estatisticas necessarias para a faixa e para o JSON de contagens."""
    if blocos is None:
        return {
            "n_blocos": None,
            "pct_sobrepostos": None,
            "n_sobrepostos": None,
            "n_acima_250_palavras": None,
            "n_uma_palavra": None,
            "maior_bloco_palavras": None,
            "ausente": True,
            "pagina_ausente": True,
        }

    n = len(blocos)
    sobrepostos = detectar_sobreposicoes(blocos)
    n_sob = len(sobrepostos)
    pct_sob = round(n_sob / max(1, n) * 100, 1)

    palavras_por_bloco = [len(b["texto"].split()) for b in blocos]
    n_250 = sum(1 for w in palavras_por_bloco if w > 250)
    n_1 = sum(1 for w in palavras_por_bloco if w <= 1)
    maior_bloco = max(palavras_por_bloco) if palavras_por_bloco else 0

    return {
        "n_blocos": n,
        "pct_sobrepostos": pct_sob,
        "n_sobrepostos": n_sob,
        "n_acima_250_palavras": n_250,
        "n_uma_palavra": n_1,
        "maior_bloco_palavras": maior_bloco,
        "ausente": False,
        "pagina_ausente": False,
    }


def classificar_cor(bloco: dict, idx: int, sobrepostos: set[int]) -> tuple[tuple[int, int, int], str]:
    """
    Classifica o contorno do bloco na ordem de precedencia:
    1. Vermelho: > 250 palavras
    2. Laranja:  sobreposto (>= 25% da area da menor caixa)
    3. Cinza:    1 palavra
    4. Azul:     demais
    """
    n_pal = len(bloco["texto"].split())
    if n_pal > 250:
        return COR_VERMELHO, "vermelho (>250 pal)"
    if idx in sobrepostos:
        return COR_LARANJA, "laranja (sobreposto)"
    if n_pal <= 1:
        return COR_CINZA, "cinza (1 palavra)"
    return COR_AZUL, "azul (normal)"


def criar_faixa_topo(
    largura: int,
    rotulo: str,
    versao: str,
    metricas: dict,
    banner_h: int = 95,
) -> Image.Image:
    """Cria o painel de cabecalho com as informacoes exigidas pela tarefa."""
    faixa = Image.new("RGB", (largura, banner_h), color="#f8fafc")
    draw = ImageDraw.Draw(faixa)

    # Linha inferior de separacao
    draw.line([(0, banner_h - 1), (largura, banner_h - 1)], fill="#cbd5e1", width=2)

    fonte_tit = carregar_fonte(20, bold=True)
    fonte_sub = carregar_fonte(15)
    fonte_leg = carregar_fonte(13)

    titulo = f"{rotulo}  —  Versao {versao}"
    draw.text((16, 8), titulo, fill="#0f172a", font=fonte_tit)

    if metricas["ausente"]:
        draw.text((16, 38), "pagina ausente nesta coleta", fill="#dc2626", font=fonte_sub)
        return faixa

    n_b = metricas["n_blocos"]
    n_sob = metricas["n_sobrepostos"]
    pct_sob = metricas["pct_sobrepostos"]
    n_250 = metricas["n_acima_250_palavras"]
    n_1 = metricas["n_uma_palavra"]
    maior = metricas["maior_bloco_palavras"]

    texto_stats = (
        f"Blocos: {n_b}   |   Sobrepostos: {n_sob} ({pct_sob:.1f}%)   |   "
        f">250 pal: {n_250}   |   1 palavra: {n_1}   |   Maior: {maior} pal"
    )
    draw.text((16, 38), texto_stats, fill="#334155", font=fonte_sub)

    # Legenda visual com marcadores coloridos
    x_leg = 16
    y_leg = 66
    draw.text((x_leg, y_leg), "Legenda:", fill="#64748b", font=fonte_leg)
    x_leg += 65
    itens_legenda = [
        ("Azul: normal", COR_AZUL),
        ("Laranja: sobreposto (>=25%)", COR_LARANJA),
        ("Vermelho: >250 pal", COR_VERMELHO),
        ("Cinza: 1 palavra", COR_CINZA),
    ]
    for texto, cor in itens_legenda:
        draw.rectangle([(x_leg, y_leg + 3), (x_leg + 10, y_leg + 13)], fill=cor)
        x_leg += 15
        draw.text((x_leg, y_leg), texto, fill="#475467", font=fonte_leg)
        x_leg += int(len(texto) * 7.5) + 15

    return faixa


def criar_painel_ausente(
    largura: int,
    altura: int,
    rotulo: str,
    versao: str,
    page_id: str,
    banner_h: int = 95,
) -> Image.Image:
    """Gera painel visual com aviso explicito quando a pagina nao esta na coleta."""
    total_h = altura + banner_h
    img = Image.new("RGB", (largura, total_h), color="#f8fafc")

    metricas_ausente = {"ausente": True}
    faixa = criar_faixa_topo(largura, rotulo, versao, metricas_ausente, banner_h)
    img.paste(faixa, (0, 0))

    draw = ImageDraw.Draw(img)
    fonte_aviso_tit = carregar_fonte(22, bold=True)
    fonte_aviso_det = carregar_fonte(16)

    # Cartao central de aviso
    cw, ch = min(largura - 80, 720), 220
    cx0 = (largura - cw) // 2
    cy0 = banner_h + (altura - ch) // 2
    cx1 = cx0 + cw
    cy1 = cy0 + ch

    draw.rectangle([(cx0, cy0), (cx1, cy1)], fill="#ffffff", outline="#e2e8f0", width=2)
    draw.text((cx0 + 32, cy0 + 35), "pagina ausente nesta coleta", fill="#dc2626", font=fonte_aviso_tit)
    draw.text((cx0 + 32, cy0 + 85), f"Page ID: {page_id}", fill="#334155", font=fonte_aviso_det)
    draw.text((cx0 + 32, cy0 + 125), "Pagina nao encontrada na pasta da versao ou rejeitada pelo filtro.", fill="#64748b", font=fonte_aviso_det)
    draw.text((cx0 + 32, cy0 + 160), "Nenhum bloco disponivel para inspecao visual.", fill="#94a3b8", font=fonte_aviso_det)

    return img


def desenhar_pagina_com_caixas(
    pimg_base,
    blocos: list[dict],
    rotulo: str,
    versao: str,
    metricas: dict,
    banner_h: int = 95,
) -> Image.Image:
    """Desenha contornos coloridos sobre a pagina renderizada e adiciona faixa de topo."""
    pimg = pimg_base.copy()
    sobrepostos = detectar_sobreposicoes(blocos)

    for i, b in enumerate(blocos):
        cor, _ = classificar_cor(b, i, sobrepostos)
        pimg.draw_rect(
            tuple(b["bbox"]),
            stroke=cor,
            stroke_width=2,
            fill=None,
        )

    img_pagina = pimg.annotated
    largura, altura = img_pagina.size

    img_final = Image.new("RGB", (largura, altura + banner_h), color="#ffffff")
    faixa = criar_faixa_topo(largura, rotulo, versao, metricas, banner_h)
    img_final.paste(faixa, (0, 0))
    img_final.paste(img_pagina, (0, banner_h))
    return img_final


def criar_comparativo_lado_a_lado(
    img_v1: Image.Image,
    img_b: Image.Image,
    img_c: Image.Image,
    caminho_saida: str,
    gutter: int = 16,
) -> None:
    """Junta as tres imagens lado a lado num unico arquivo PNG."""
    w1, h1 = img_v1.size
    wb, hb = img_b.size
    wc, hc = img_c.size

    largura_total = w1 + wb + wc + 2 * gutter
    altura_total = max(h1, hb, hc)

    comparativo = Image.new("RGB", (largura_total, altura_total), color="#cbd5e1")
    x = 0
    comparativo.paste(img_v1, (x, 0))
    x += w1 + gutter
    comparativo.paste(img_b, (x, 0))
    x += wb + gutter
    comparativo.paste(img_c, (x, 0))

    comparativo.save(caminho_saida, "PNG")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotulo-atual", default="C", help="nome do painel do codigo atual (padrao C)")
    rot = ap.parse_args().rotulo_atual
    t_inicio = time.perf_counter()
    os.makedirs(DIR_SAIDA, exist_ok=True)
    print("=" * 72)
    print("Inspecao Visual de Segmentacao — Tarefa T16")
    print(f"Destino das imagens: {os.path.relpath(DIR_SAIDA, RAIZ)}")
    print("=" * 72)

    contagens = {}

    for idx, item in enumerate(PAGINAS_PROBLEMA, 1):
        rotulo = item["rotulo"]
        veiculo = item["veiculo"]
        arquivo = item["arquivo"]
        pag = item["pagina"]
        page_id = f"{veiculo}/{arquivo}#p{pag}"

        print(f"\n[{idx}/4] {rotulo} ({page_id}) — {item['descricao']}")

        caminho_pdf = encontrar_pdf(veiculo, arquivo)
        with pdfplumber.open(caminho_pdf) as pdf:
            pagina_pdf = pdf.pages[pag]
            # Renderizacao a 110 dpi conforme a especificacao
            t0 = time.perf_counter()
            pimg_base = pagina_pdf.to_image(resolution=110)
            t_render = time.perf_counter() - t0
            print(f"      Renderizada a 110 dpi ({pimg_base.annotated.size[0]}x{pimg_base.annotated.size[1]}) em {t_render:.1f}s")

            # 1. Versao v1
            v1_blocos = carregar_bloco_jsonl(DIR_V1, veiculo, page_id)
            v1_metricas = calcular_metricas(v1_blocos)

            # 2. Versao B
            b_blocos = carregar_bloco_jsonl(DIR_B, veiculo, page_id)
            b_metricas = calcular_metricas(b_blocos)

            # 3. Versao C (ao vivo com extrator.py)
            c_blocos = extrair_bloco_codigo_atual(pagina_pdf)
            c_metricas = calcular_metricas(c_blocos)

        # Gerar e salvar v1
        caminho_v1 = os.path.join(DIR_SAIDA, f"{rotulo}_v1.png")
        if v1_metricas["ausente"]:
            img_v1 = criar_painel_ausente(pimg_base.annotated.width, pimg_base.annotated.height, rotulo, "v1", page_id)
        else:
            img_v1 = desenhar_pagina_com_caixas(pimg_base, v1_blocos, rotulo, "v1", v1_metricas)
        img_v1.save(caminho_v1, "PNG")
        print(f"      v1: n_blocos={v1_metricas['n_blocos']} -> {os.path.basename(caminho_v1)}")

        # Gerar e salvar B
        caminho_b = os.path.join(DIR_SAIDA, f"{rotulo}_B.png")
        if b_metricas["ausente"]:
            img_b = criar_painel_ausente(pimg_base.annotated.width, pimg_base.annotated.height, rotulo, "B", page_id)
        else:
            img_b = desenhar_pagina_com_caixas(pimg_base, b_blocos, rotulo, "B", b_metricas)
        img_b.save(caminho_b, "PNG")
        print(f"      B:  n_blocos={b_metricas['n_blocos']} (ausente={b_metricas['ausente']}) -> {os.path.basename(caminho_b)}")

        # Gerar e salvar C
        caminho_c = os.path.join(DIR_SAIDA, f"{rotulo}_{rot}.png")
        if c_metricas["ausente"]:
            img_c = criar_painel_ausente(pimg_base.annotated.width, pimg_base.annotated.height, rotulo, rot, page_id)
        else:
            img_c = desenhar_pagina_com_caixas(pimg_base, c_blocos, rotulo, rot, c_metricas)
        img_c.save(caminho_c, "PNG")
        print(f"      {rot}:  n_blocos={c_metricas['n_blocos']} -> {os.path.basename(caminho_c)}")

        # Gerar e salvar comparativo lado a lado
        caminho_comp = os.path.join(DIR_SAIDA, f"{rotulo}_comparativo.png" if rot == "C"
                                    else f"{rotulo}_comparativo_{rot}.png")
        criar_comparativo_lado_a_lado(img_v1, img_b, img_c, caminho_comp)
        print(f"      Comparativo -> {os.path.basename(caminho_comp)}")

        # Armazenar contagens estruturadas
        contagens[rotulo] = {
            "v1": {
                "n_blocos": v1_metricas["n_blocos"],
                "pct_sobrepostos": v1_metricas["pct_sobrepostos"],
                "n_acima_250_palavras": v1_metricas["n_acima_250_palavras"],
                "n_uma_palavra": v1_metricas["n_uma_palavra"],
                "maior_bloco_palavras": v1_metricas["maior_bloco_palavras"],
                "ausente": v1_metricas["ausente"],
            },
            "B": {
                "n_blocos": b_metricas["n_blocos"],
                "pct_sobrepostos": b_metricas["pct_sobrepostos"],
                "n_acima_250_palavras": b_metricas["n_acima_250_palavras"],
                "n_uma_palavra": b_metricas["n_uma_palavra"],
                "maior_bloco_palavras": b_metricas["maior_bloco_palavras"],
                "ausente": b_metricas["ausente"],
            },
            rot: {
                "n_blocos": c_metricas["n_blocos"],
                "pct_sobrepostos": c_metricas["pct_sobrepostos"],
                "n_acima_250_palavras": c_metricas["n_acima_250_palavras"],
                "n_uma_palavra": c_metricas["n_uma_palavra"],
                "maior_bloco_palavras": c_metricas["maior_bloco_palavras"],
                "ausente": c_metricas["ausente"],
            },
        }

    # Salvar contagens.json
    arq_contagens = ARQ_CONTAGENS if rot == "C" else ARQ_CONTAGENS.replace(".json", f"_{rot}.json")
    with open(arq_contagens, "w", encoding="utf-8") as f:
        json.dump(contagens, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Salvo: {os.path.relpath(arq_contagens, RAIZ)}")

    # Imprimir tabela consolidada no console
    print("\n" + "=" * 90)
    print(f"{'Rotulo':<18} {'Versao':<8} {'Blocos':<8} {'% Sobrep':<10} {'>250 pal':<10} {'1 pal':<8} {'Maior':<8} {'Ausente'}")
    print("-" * 90)
    for rotulo, versoes in contagens.items():
        for versao, m in versoes.items():
            if m["ausente"]:
                print(f"{rotulo:<18} {versao:<8} {'-':<8} {'-':<10} {'-':<10} {'-':<8} {'-':<8} {'SIM'}")
            else:
                pct_str = f"{m['pct_sobrepostos']:.1f}%"
                print(f"{rotulo:<18} {versao:<8} {m['n_blocos']:<8} {pct_str:<10} {m['n_acima_250_palavras']:<10} {m['n_uma_palavra']:<8} {m['maior_bloco_palavras']:<8} {'nao'}")
    print("=" * 90)
    tempo_total = time.perf_counter() - t_inicio
    print(f"Concluido em {tempo_total:.1f}s. 16 PNGs + 1 JSON gerados com sucesso.")


if __name__ == "__main__":
    main()
