# -*- coding: utf-8 -*-
"""
Galeria visual comparando, nas 11 paginas do teste sem vies (diamond_teste),
a anotacao humana (ouro), o extrator de regras (regioes.py) e os dois detectores
treinados (LS-16 e LS-3), para o autor conferir a olho.

Por que existe
--------------
Para inspecionar qualitativamente os acertos e falhas de cada abordagem de
segmentacao/deteccao de layout em diarios oficiais, especialmente em blocos
complexos (tabelas, figuras, assinaturas, titulos e texto corrido multicoluna).
As 11 paginas de data/diamond/diamond_teste foram anotadas do zero pelo autor
(sem vies de ancoragem de pre-anotacao).

O que faz
---------
1. Le tarefas e anotacoes humanas de data/diamond/diamond_teste/.
2. Obtem as regioes de quatro sistemas:
   - Ouro humano: anotacoes concluidas do anotador humano;
   - Extrator: src/data/regioes.py:propor(regras=True) sobre palavras e blocos v3;
   - Detector LS-16: predicoes do modelo de 16 classes (resultados/deteccao/pred_ls16_diamond_teste.jsonl);
   - Detector LS-3: predicoes do modelo de 3 classes (resultados/deteccao/pred_ls3_diamond_teste.jsonl).
3. Mapeia as classes de todos os sistemas para a regra das 3 classes:
   - table / tabela -> tabela (roxo)
   - figure, chart, heading, figura, imagem -> imagem (cinza)
   - unknown, outro -> outro (laranja)
   - resto (classes textuais) -> texto (azul)
4. Gera uma imagem resultados/galeria_extrator_detector/pagNN.jpg por pagina com
   QUATRO paineis lado a lado (~700 px cada, largura total ~2800 px):
   contorno de 2 px sem preenchimento, com titulo e contagem de caixas em cada painel.
5. Gera resultados/galeria_extrator_detector/index.html estatico (HTML + CSS puro),
   com secao por pagina, imagem clicavel e tabela de contagens por sistema e classe.

Uso
---
    venv/Scripts/python.exe orquestracao/analises/galeria_extrator_detector.py
"""
from __future__ import annotations

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.data import regioes as seg  # noqa: E402

# Diretorios e arquivos de entrada
DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond", "diamond_teste")
ARQ_TAREFAS = os.path.join(DIR_DIAMOND, "tarefas.jsonl")
ARQ_ANOTACOES = os.path.join(DIR_DIAMOND, "anotacoes.jsonl")
DIR_IMG = os.path.join(DIR_DIAMOND, "img")

ARQ_PRED_LS3 = os.path.join(RAIZ, "resultados", "deteccao", "pred_ls3_diamond_teste.jsonl")
ARQ_PRED_LS16 = os.path.join(RAIZ, "resultados", "deteccao", "pred_ls16_diamond_teste.jsonl")

# Diretorio de saida
DIR_SAIDA = os.path.join(RAIZ, "resultados", "galeria_extrator_detector")
ARQ_HTML = os.path.join(DIR_SAIDA, "index.html")
ARQ_CONTAGENS = os.path.join(DIR_SAIDA, "contagens.json")

# Dicionario de nomes amigaveis para os veiculos dos diarios oficiais
NOMES_VEICULOS = {
    "official_diary_to": "Tocantins (TO)",
    "official_diary_pr_curitiba": "Curitiba (PR)",
    "official_diary_se": "Sergipe (SE)",
    "official_diary_RJ_duque_de_caxias": "Duque de Caxias (RJ)",
    "official_diary_MG_congonhas": "Congonhas (MG)",
    "official_diary_rr": "Roraima (RR)",
    "official_diary_ro": "Rondônia (RO)",
    "official_diary_ms": "Mato Grosso do Sul (MS)",
    "official_diary_rs_porto_alegre": "Porto Alegre (RS)",
    "official_diary_pe": "Pernambuco (PE)",
    "official_diary_pi_v2": "Piauí (PI)",
}

# Cores especificadas: texto azul, tabela roxo, imagem cinza, nao categorizado laranja
CORES_RGB = {
    "texto": (37, 99, 235),      # Azul (#2563eb)
    "tabela": (124, 58, 237),    # Roxo (#7c3aed)
    "imagem": (100, 116, 139),   # Cinza (#64748b)
    "outro": (234, 88, 12),      # Laranja (#ea580c)
}

CORES_HEX = {
    "texto": "#2563eb",
    "tabela": "#7c3aed",
    "imagem": "#64748b",
    "outro": "#ea580c",
}


def ler_jsonl(caminho: str) -> list[dict]:
    """Le arquivo JSONL de forma segura."""
    if not os.path.isfile(caminho):
        return []
    itens = []
    with open(caminho, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    itens.append(json.loads(l))
                except Exception:
                    pass
    return itens


def mapear_para_3_classes(classe: str | None) -> str:
    """
    Colapsa classes do guia (16 classes), do extrator (9 classes)
    ou do detector ls3 (3 classes) em: 'texto', 'tabela', 'imagem' ou 'outro'.

    Regra das 3 classes (especificacao):
      - table / tabela -> tabela
      - figure, chart, heading, figura, imagem -> imagem
      - unknown, outro -> outro (laranja)
      - resto -> texto
    """
    if not classe:
        return "outro"
    c = str(classe).strip().lower()

    if c in ("table", "tabela"):
        return "tabela"
    if c in ("figure", "chart", "heading", "figura", "imagem"):
        return "imagem"
    if c in ("unknown", "outro", "none", ""):
        return "outro"

    classes_texto = {
        "act", "act section", "paragraph", "signature", "id", "header",
        "footer", "caption", "title", "section title", "sub section title",
        "texto", "text", "titulo", "lista", "assinatura", "cabecalho", "rodape",
    }
    if c in classes_texto:
        return "texto"

    return "outro"


def contar_classes(regioes: list[dict]) -> dict[str, int]:
    """Conta caixas por categoria colapsada."""
    cont = {"texto": 0, "tabela": 0, "imagem": 0, "outro": 0, "total": 0}
    for r in regioes:
        cat = mapear_para_3_classes(r.get("classe", ""))
        cont[cat] += 1
        cont["total"] += 1
    return cont


def carregar_fonte(tamanho: int = 16, bold: bool = False) -> ImageFont.ImageFont:
    """Carrega fonte TrueType do sistema com fallback seguro."""
    candidatos = (
        ["arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"]
        if bold
        else ["arial.ttf", "segoeui.ttf", "calibri.ttf"]
    )
    for n in candidatos:
        try:
            return ImageFont.truetype(n, tamanho)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except Exception:
        return ImageFont.load_default()


def renderizar_painel(
    img_redim: Image.Image,
    regioes: list[dict],
    sx: float,
    sy: float,
    titulo: str,
    n_caixas: int,
    largura_painel: int = 700,
    alt_banner: int = 44,
) -> Image.Image:
    """
    Cria a imagem de um painel individual com banner de cabecalho
    e contornos de 2 px desenhados sobre a imagem redimensionada.
    """
    w_p, h_p = img_redim.size
    altura_total = h_p + alt_banner

    painel = Image.new("RGB", (largura_painel, altura_total), color="#ffffff")
    draw = ImageDraw.Draw(painel)

    # 1. Banner superior
    draw.rectangle([(0, 0), (largura_painel, alt_banner - 1)], fill="#1e293b")
    draw.line([(0, alt_banner - 1), (largura_painel, alt_banner - 1)], fill="#0f172a", width=1)

    fonte_tit = carregar_fonte(16, bold=True)
    fonte_cnt = carregar_fonte(15, bold=False)

    texto_tit = titulo
    texto_cnt = f"{n_caixas} caixa" if n_caixas == 1 else f"{n_caixas} caixas"

    draw.text((14, 11), texto_tit, fill="#ffffff", font=fonte_tit)
    draw.text((largura_painel - 14 - int(len(texto_cnt) * 8.2), 12), texto_cnt, fill="#cbd5e1", font=fonte_cnt)

    # 2. Imagem redimensionada da pagina
    painel.paste(img_redim, (0, alt_banner))

    # 3. Desenhar caixas com contorno de 2 px sem preenchimento
    draw_caixas = ImageDraw.Draw(painel)
    for r in regioes:
        bbox = r.get("bbox", [0, 0, 0, 0])
        if len(bbox) != 4:
            continue
        x0, y0, x1, y1 = bbox
        cat = mapear_para_3_classes(r.get("classe", ""))
        cor = CORES_RGB[cat]

        bx0 = max(0, min(largura_painel - 1, round(x0 * sx)))
        by0 = max(0, min(h_p - 1, round(y0 * sy))) + alt_banner
        bx1 = max(0, min(largura_painel - 1, round(x1 * sx)))
        by1 = max(0, min(h_p - 1, round(y1 * sy))) + alt_banner

        if bx1 > bx0 and by1 > by0:
            draw_caixas.rectangle([bx0, by0, bx1, by1], outline=cor, width=2)

    return painel


def criar_imagem_quatro_paineis(
    img_base: Image.Image,
    w_pt: float,
    h_pt: float,
    ouro_reg: list[dict],
    ext_reg: list[dict],
    ls16_reg: list[dict],
    ls3_reg: list[dict],
    rotulo_pagina: str,
    veiculo_nome: str,
    largura_painel: int = 700,
    alt_banner_geral: int = 48,
    alt_banner_painel: int = 44,
) -> Image.Image:
    """
    Monta a imagem combinada de 4 paineis lado a lado com banner superior geral e legenda.
    """
    w_orig, h_orig = img_base.size
    h_painel = int(round(h_orig * (largura_painel / float(w_orig))))

    # Redimensiona imagem base uma unica vez
    img_redim = img_base.convert("RGB").resize((largura_painel, h_painel), Image.Resampling.LANCZOS)

    sx = float(largura_painel) / w_pt
    sy = float(h_painel) / h_pt

    sistemas = [
        ("Ouro Humano", ouro_reg),
        ("Extrator (Regras)", ext_reg),
        ("Detector LS-16", ls16_reg),
        ("Detector LS-3", ls3_reg),
    ]

    paineis = []
    for nome_sis, regs in sistemas:
        p = renderizar_painel(
            img_redim=img_redim,
            regioes=regs,
            sx=sx,
            sy=sy,
            titulo=nome_sis,
            n_caixas=len(regs),
            largura_painel=largura_painel,
            alt_banner=alt_banner_painel,
        )
        paineis.append(p)

    largura_total = 4 * largura_painel + 3 * 2  # 3 separadores verticais de 2 px
    altura_painel_com_banner = h_painel + alt_banner_painel
    altura_total = alt_banner_geral + altura_painel_com_banner

    saida = Image.new("RGB", (largura_total, altura_total), color="#0f172a")
    draw = ImageDraw.Draw(saida)

    # 1. Faixa de cabecalho geral
    draw.rectangle([(0, 0), (largura_total, alt_banner_geral - 1)], fill="#0f172a")

    fonte_cab_tit = carregar_fonte(18, bold=True)
    fonte_leg = carregar_fonte(14, bold=False)

    texto_tit = f"{rotulo_pagina} — {veiculo_nome}"
    draw.text((18, 13), texto_tit, fill="#f8fafc", font=fonte_cab_tit)

    # Legenda colorida no topo direito
    legenda_itens = [
        ("Texto (azul)", CORES_RGB["texto"]),
        ("Tabela (roxo)", CORES_RGB["tabela"]),
        ("Imagem (cinza)", CORES_RGB["imagem"]),
        ("Outro (laranja)", CORES_RGB["outro"]),
    ]

    x_leg = largura_total - 620
    y_leg = 15
    for rotulo_cor, cor in legenda_itens:
        draw.rectangle([(x_leg, y_leg + 2), (x_leg + 14, y_leg + 14)], outline=cor, width=2)
        draw.text((x_leg + 20, y_leg), rotulo_cor, fill="#e2e8f0", font=fonte_leg)
        x_leg += 150

    draw.line([(0, alt_banner_geral - 1), (largura_total, alt_banner_geral - 1)], fill="#334155", width=2)

    # 2. Posicionar os quatro paineis lado a lado com divisor vertical
    x_offset = 0
    for i, p in enumerate(paineis):
        saida.paste(p, (x_offset, alt_banner_geral))
        x_offset += largura_painel
        if i < 3:
            draw.line(
                [(x_offset, alt_banner_geral), (x_offset, altura_total)],
                fill="#475569",
                width=2,
            )
            x_offset += 2

    return saida


def gerar_html(
    dados_paginas: list[dict],
    totais_sistemas: dict[str, dict[str, int]],
    caminho_saida: str,
) -> None:
    """Gera index.html estatico com estilo completo sem dependencias externas."""
    linhas_html = []
    linhas_html.append("<!DOCTYPE html>")
    linhas_html.append('<html lang="pt-BR">')
    linhas_html.append("<head>")
    linhas_html.append('  <meta charset="utf-8">')
    linhas_html.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    linhas_html.append("  <title>Galeria Visual: Ouro vs Extrator vs Detectores (Diamond Teste)</title>")
    linhas_html.append("  <style>")
    linhas_html.append("""
    :root {
      --bg: #0f172a;
      --card-bg: #ffffff;
      --card-border: #e2e8f0;
      --text-main: #1e293b;
      --text-muted: #64748b;
      --color-texto: #2563eb;
      --color-tabela: #7c3aed;
      --color-imagem: #64748b;
      --color-outro: #ea580c;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f8fafc;
      color: var(--text-main);
      line-height: 1.5;
      padding: 0;
    }
    header {
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      color: #ffffff;
      padding: 2.5rem 2rem 2rem;
      border-bottom: 3px solid #3b82f6;
    }
    .header-content {
      max-width: 1500px;
      margin: 0 auto;
    }
    header h1 {
      font-size: 1.85rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 0.5rem;
    }
    header p.subtitulo {
      font-size: 1.05rem;
      color: #cbd5e1;
      margin-bottom: 1.25rem;
    }
    .meta-box {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      font-size: 0.9rem;
      color: #94a3b8;
      margin-bottom: 1.5rem;
    }
    .meta-box strong { color: #f1f5f9; }
    .meta-box ul { margin-left: 1.5rem; margin-top: 0.35rem; }
    .meta-box li { margin-bottom: 0.2rem; }

    /* Barra de Legenda */
    .legenda-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      margin-top: 1rem;
    }
    .legenda-title {
      font-weight: 600;
      color: #f8fafc;
      margin-right: 0.5rem;
    }
    .legenda-item {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.9rem;
      color: #e2e8f0;
    }
    .color-pill {
      display: inline-block;
      width: 14px;
      height: 14px;
      border-radius: 3px;
      border: 2px solid;
    }

    /* Menu de Navegacao Rapida */
    .nav-bar {
      max-width: 1500px;
      margin: 1.5rem auto 0;
      padding: 0 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .nav-btn {
      display: inline-block;
      padding: 0.4rem 0.8rem;
      background-color: #ffffff;
      color: #334155;
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      transition: all 0.15s ease;
    }
    .nav-btn:hover {
      background-color: #2563eb;
      color: #ffffff;
      border-color: #2563eb;
    }

    /* Container Principal */
    main {
      max-width: 1500px;
      margin: 1.5rem auto 3rem;
      padding: 0 1.5rem;
    }

    /* Secao Consolidada */
    .resumo-card {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .resumo-card h2 {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 0.75rem;
      color: #0f172a;
    }

    /* Cartao por Pagina */
    .pagina-section {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      margin-bottom: 2.5rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      overflow: hidden;
    }
    .pagina-header {
      background-color: #f1f5f9;
      border-bottom: 1px solid #e2e8f0;
      padding: 1rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .pagina-header-tit {
      font-size: 1.15rem;
      font-weight: 700;
      color: #0f172a;
    }
    .pagina-header-sub {
      font-size: 0.85rem;
      color: #64748b;
      margin-top: 0.15rem;
    }
    .pagina-header-badge {
      display: inline-block;
      padding: 0.25rem 0.65rem;
      background: #e2e8f0;
      color: #334155;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .pagina-body {
      padding: 1.25rem 1.5rem;
    }

    /* Tabela de Contagens */
    .tabela-wrapper {
      margin-bottom: 1.25rem;
      overflow-x: auto;
    }
    table.tabela-contagens {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }
    table.tabela-contagens th,
    table.tabela-contagens td {
      padding: 0.6rem 0.85rem;
      border-bottom: 1px solid #e2e8f0;
    }
    table.tabela-contagens th {
      background-color: #f8fafc;
      font-weight: 600;
      color: #475569;
    }
    table.tabela-contagens tr:hover td {
      background-color: #f8fafc;
    }
    table.tabela-contagens td.num,
    table.tabela-contagens th.num {
      text-align: right;
    }
    table.tabela-contagens td.total,
    table.tabela-contagens th.total {
      text-align: right;
      font-weight: 700;
    }
    .dot-badge {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 5px;
    }

    /* Imagem Comparativa */
    .img-box {
      text-align: center;
      background: #090d16;
      padding: 0.75rem;
      border-radius: 8px;
    }
    .img-box a {
      display: block;
      text-decoration: none;
    }
    .img-box img {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
      display: block;
      margin: 0 auto;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
      transition: opacity 0.15s ease;
    }
    .img-box a:hover img {
      opacity: 0.95;
    }
    .img-dica {
      margin-top: 0.65rem;
      font-size: 0.85rem;
      color: #94a3b8;
    }

    footer {
      text-align: center;
      padding: 2rem;
      color: #64748b;
      font-size: 0.85rem;
      border-top: 1px solid #e2e8f0;
      background: #ffffff;
    }
    """)
    linhas_html.append("  </style>")
    linhas_html.append("</head>")
    linhas_html.append("<body>")

    # Header
    linhas_html.append("<header>")
    linhas_html.append('  <div class="header-content">')
    linhas_html.append("    <h1>Galeria Visual: Ouro Humano vs Extrator vs Detectores de Layout</h1>")
    linhas_html.append('    <p class="subtitulo">Comparação detalhada nas 11 páginas do teste sem viés (<code>data/diamond/diamond_teste</code>) para inspeção qualitativa.</p>')

    linhas_html.append('    <div class="meta-box">')
    linhas_html.append("      <strong>Metodologia e Contexto Experimental:</strong>")
    linhas_html.append("      <ul>")
    linhas_html.append("        <li><strong>Teste sem viés de ancoragem:</strong> as 11 páginas do <code>diamond_teste</code> foram anotadas do zero pelo autor (sem pré-anotação na tela), garantindo gabarito independente.</li>")
    linhas_html.append("        <li><strong>Limitações declaradas:</strong> tamanho de amostra pequeno (n = 11 páginas); o extrator depende da camada digital de texto do PDF (pdfplumber) combinada com Docling Heron, enquanto os detectores LS-16 e LS-3 operam sobre a renderização visual da imagem.</li>")
    linhas_html.append("        <li><strong>Regra das 3 classes colapsadas:</strong> Texto (azul), Tabela (roxo), Imagem/Gráfico/Rubrica (cinza) e Outro/Duvidoso (laranja). Contorno de 2 px sem preenchimento.</li>")
    linhas_html.append("      </ul>")
    linhas_html.append("    </div>")

    linhas_html.append('    <div class="legenda-bar">')
    linhas_html.append('      <span class="legenda-title">Legenda de Cores:</span>')
    linhas_html.append(f'      <div class="legenda-item"><span class="color-pill" style="border-color:{CORES_HEX["texto"]}; background:rgba(37,99,235,0.2);"></span> <strong>Texto</strong> (parágrafo, título, lista, cabeçalho, rodapé, assinatura)</div>')
    linhas_html.append(f'      <div class="legenda-item"><span class="color-pill" style="border-color:{CORES_HEX["tabela"]}; background:rgba(124,58,237,0.2);"></span> <strong>Tabela</strong> (estrutura tabular)</div>')
    linhas_html.append(f'      <div class="legenda-item"><span class="color-pill" style="border-color:{CORES_HEX["imagem"]}; background:rgba(100,116,139,0.2);"></span> <strong>Imagem</strong> (figura, gráfico, rubrica manuscrita)</div>')
    linhas_html.append(f'      <div class="legenda-item"><span class="color-pill" style="border-color:{CORES_HEX["outro"]}; background:rgba(234,88,12,0.2);"></span> <strong>Outro</strong> (classe não mapeada ou duvidosa)</div>')
    linhas_html.append("    </div>")
    linhas_html.append("  </div>")
    linhas_html.append("</header>")

    # Navegacao rapida
    linhas_html.append('<nav class="nav-bar">')
    for d in dados_paginas:
        n = d["n"]
        uf_abrev = d["uf"].replace("official_diary_", "").upper()
        linhas_html.append(f'  <a class="nav-btn" href="#pag{n:02d}">Pág {n:02d} ({uf_abrev})</a>')
    linhas_html.append("</nav>")

    linhas_html.append("<main>")

    # Resumo Geral Consolidado
    linhas_html.append('  <section class="resumo-card">')
    linhas_html.append("    <h2>Consolidado Geral (Total de Caixas nas 11 Páginas)</h2>")
    linhas_html.append('    <div class="tabela-wrapper">')
    linhas_html.append('      <table class="tabela-contagens">')
    linhas_html.append("        <thead>")
    linhas_html.append("          <tr>")
    linhas_html.append("            <th>Sistema</th>")
    linhas_html.append(f'            <th class="num"><span class="dot-badge" style="background:{CORES_HEX["texto"]};"></span>Texto</th>')
    linhas_html.append(f'            <th class="num"><span class="dot-badge" style="background:{CORES_HEX["tabela"]};"></span>Tabela</th>')
    linhas_html.append(f'            <th class="num"><span class="dot-badge" style="background:{CORES_HEX["imagem"]};"></span>Imagem</th>')
    linhas_html.append(f'            <th class="num"><span class="dot-badge" style="background:{CORES_HEX["outro"]};"></span>Outro</th>')
    linhas_html.append('            <th class="total">Total de Caixas</th>')
    linhas_html.append("          </tr>")
    linhas_html.append("        </thead>")
    linhas_html.append("        <tbody>")

    rotulos_sistemas = [
        ("ouro", "Ouro Humano (Gabarito)"),
        ("extrator", "Extrator de Regras (regioes.py)"),
        ("ls16", "Detector LS-16 (16 classes guia)"),
        ("ls3", "Detector LS-3 (3 classes plano grosso)"),
    ]
    for chave, rotulo in rotulos_sistemas:
        tot = totais_sistemas[chave]
        linhas_html.append("          <tr>")
        linhas_html.append(f"            <td><strong>{rotulo}</strong></td>")
        linhas_html.append(f'            <td class="num">{tot["texto"]}</td>')
        linhas_html.append(f'            <td class="num">{tot["tabela"]}</td>')
        linhas_html.append(f'            <td class="num">{tot["imagem"]}</td>')
        linhas_html.append(f'            <td class="num">{tot["outro"]}</td>')
        linhas_html.append(f'            <td class="total">{tot["total"]}</td>')
        linhas_html.append("          </tr>")

    linhas_html.append("        </tbody>")
    linhas_html.append("      </table>")
    linhas_html.append("    </div>")
    linhas_html.append("  </section>")

    # Seções de cada página
    for d in dados_paginas:
        n = d["n"]
        nome_arquivo_jpg = f"pag{n:02d}.jpg"
        linhas_html.append(f'  <section class="pagina-section" id="pag{n:02d}">')
        linhas_html.append('    <div class="pagina-header">')
        linhas_html.append("      <div>")
        linhas_html.append(f'        <div class="pagina-header-tit">Página {n:02d} — {d["veiculo"]}</div>')
        linhas_html.append(f'        <div class="pagina-header-sub">PDF: <code>{d["arquivo"]}</code> (pág. {d["pagina"]}) &bull; ID: <code>{d["page_id"]}</code></div>')
        linhas_html.append("      </div>")
        linhas_html.append(f'      <span class="pagina-header-badge">{d["dim_pt"]} pt &bull; {d["dim_px"]} px</span>')
        linhas_html.append("    </div>")

        linhas_html.append('    <div class="pagina-body">')
        # Tabela de contagens da pagina
        linhas_html.append('      <div class="tabela-wrapper">')
        linhas_html.append('        <table class="tabela-contagens">')
        linhas_html.append("          <thead>")
        linhas_html.append("            <tr>")
        linhas_html.append("              <th>Sistema</th>")
        linhas_html.append(f'              <th class="num"><span class="dot-badge" style="background:{CORES_HEX["texto"]};"></span>Texto</th>')
        linhas_html.append(f'              <th class="num"><span class="dot-badge" style="background:{CORES_HEX["tabela"]};"></span>Tabela</th>')
        linhas_html.append(f'              <th class="num"><span class="dot-badge" style="background:{CORES_HEX["imagem"]};"></span>Imagem</th>')
        linhas_html.append(f'              <th class="num"><span class="dot-badge" style="background:{CORES_HEX["outro"]};"></span>Outro</th>')
        linhas_html.append('              <th class="total">Total</th>')
        linhas_html.append("            </tr>")
        linhas_html.append("          </thead>")
        linhas_html.append("          <tbody>")

        for chave, rotulo in rotulos_sistemas:
            cnt = d["contagens"][chave]
            linhas_html.append("            <tr>")
            linhas_html.append(f"              <td>{rotulo}</td>")
            linhas_html.append(f'              <td class="num">{cnt["texto"]}</td>')
            linhas_html.append(f'              <td class="num">{cnt["tabela"]}</td>')
            linhas_html.append(f'              <td class="num">{cnt["imagem"]}</td>')
            linhas_html.append(f'              <td class="num">{cnt["outro"]}</td>')
            linhas_html.append(f'              <td class="total">{cnt["total"]}</td>')
            linhas_html.append("            </tr>")

        linhas_html.append("          </tbody>")
        linhas_html.append("        </table>")
        linhas_html.append("      </div>")

        # Imagem com link
        linhas_html.append('      <div class="img-box">')
        linhas_html.append(f'        <a href="{nome_arquivo_jpg}" target="_blank" title="Clique para abrir a imagem em tamanho real (2800 px de largura)">')
        linhas_html.append(f'          <img src="{nome_arquivo_jpg}" alt="Painel comparativo da página {n:02d}" loading="lazy">')
        linhas_html.append("        </a>")
        linhas_html.append(f'        <p class="img-dica">🔍 Clique na imagem para abrir em resolução máxima (4 painéis lado a lado, ~2800 px).</p>')
        linhas_html.append("      </div>")

        linhas_html.append("    </div>")
        linhas_html.append("  </section>")

    linhas_html.append("</main>")

    linhas_html.append("<footer>")
    linhas_html.append("  <p>TCC Recuperação de Informação — Detecção de Ordem de Leitura e Layout em Diários Oficiais (INF-UFG)</p>")
    linhas_html.append("  <p>Galeria gerada automaticamente por <code>orquestracao/analises/galeria_extrator_detector.py</code></p>")
    linhas_html.append("</footer>")

    linhas_html.append("</body>")
    linhas_html.append("</html>")

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_html) + "\n")


def main():
    print("[INICIO] Galeria visual: Ouro vs Extrator vs Detectores (Diamond Teste)")

    if not os.path.isfile(ARQ_TAREFAS):
        sys.exit(f"[ERRO] Arquivo de tarefas nao encontrado: {ARQ_TAREFAS}")
    if not os.path.isfile(ARQ_ANOTACOES):
        sys.exit(f"[ERRO] Arquivo de anotacoes nao encontrado: {ARQ_ANOTACOES}")

    os.makedirs(DIR_SAIDA, exist_ok=True)

    tarefas_raw = ler_jsonl(ARQ_TAREFAS)
    tarefas = {t["page_id"]: t for t in tarefas_raw}

    anotacoes_raw = ler_jsonl(ARQ_ANOTACOES)
    gabarito = {}
    for an in anotacoes_raw:
        humano = not an.get("anotador", "").startswith("VLM:")
        if an.get("status") == "concluida" and humano:
            gabarito[an["page_id"]] = an

    if not gabarito:
        sys.exit(f"[ERRO] Nenhuma anotacao humana concluida encontrada em {ARQ_ANOTACOES}")

    pred_ls3_raw = ler_jsonl(ARQ_PRED_LS3)
    pred_ls3 = {x["page_id"]: x.get("regioes", []) for x in pred_ls3_raw}

    pred_ls16_raw = ler_jsonl(ARQ_PRED_LS16)
    pred_ls16 = {x["page_id"]: x.get("regioes", []) for x in pred_ls16_raw}

    # Ordenar as paginas pelo indice 'n' da tarefa
    paginas = sorted(gabarito.keys(), key=lambda pid: tarefas[pid].get("n", 0))
    print(f"[DADOS] {len(paginas)} paginas concluidas encontradas.")

    totais_sistemas = {
        "ouro": {"texto": 0, "tabela": 0, "imagem": 0, "outro": 0, "total": 0},
        "extrator": {"texto": 0, "tabela": 0, "imagem": 0, "outro": 0, "total": 0},
        "ls16": {"texto": 0, "tabela": 0, "imagem": 0, "outro": 0, "total": 0},
        "ls3": {"texto": 0, "tabela": 0, "imagem": 0, "outro": 0, "total": 0},
    }

    dados_paginas = []

    for idx, pid in enumerate(paginas, 1):
        t = tarefas[pid]
        n = t.get("n", idx)
        uf = t.get("uf", "")
        veiculo = NOMES_VEICULOS.get(uf, uf)
        arquivo = t.get("arquivo", "")
        pagina = t.get("pagina", 0)
        img_nome = t.get("imagem", f"{n:03d}.jpg")
        caminho_img = os.path.join(DIR_IMG, img_nome)

        if not os.path.isfile(caminho_img):
            print(f"[ALERTA] Imagem nao encontrada: {caminho_img}")
            continue

        w_pt = float(t["dimensions"]["width"])
        h_pt = float(t["dimensions"]["height"])

        # 1. Regioes do Ouro Humano
        reg_ouro = gabarito[pid].get("regioes", [])

        # 2. Regioes do Extrator de Regras (reutiliza seg.propor)
        try:
            reg_ext = seg.propor(t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True)
        except Exception as e:
            print(f"[AVISO] Falha ao rodar seg.propor na pagina {pid}: {e}")
            reg_ext = []

        # 3. Regioes do Detector LS-16
        reg_ls16 = pred_ls16.get(pid, [])

        # 4. Regioes do Detector LS-3
        reg_ls3 = pred_ls3.get(pid, [])

        # Contagens
        c_ouro = contar_classes(reg_ouro)
        c_ext = contar_classes(reg_ext)
        c_ls16 = contar_classes(reg_ls16)
        c_ls3 = contar_classes(reg_ls3)

        for cat in ("texto", "tabela", "imagem", "outro", "total"):
            totais_sistemas["ouro"][cat] += c_ouro[cat]
            totais_sistemas["extrator"][cat] += c_ext[cat]
            totais_sistemas["ls16"][cat] += c_ls16[cat]
            totais_sistemas["ls3"][cat] += c_ls3[cat]

        img_base = Image.open(caminho_img)
        w_px, h_px = img_base.size

        # Gerar imagem comparativa de 4 paineis
        rotulo_pagina = f"Pág {n:02d}"
        img_quatro = criar_imagem_quatro_paineis(
            img_base=img_base,
            w_pt=w_pt,
            h_pt=h_pt,
            ouro_reg=reg_ouro,
            ext_reg=reg_ext,
            ls16_reg=reg_ls16,
            ls3_reg=reg_ls3,
            rotulo_pagina=rotulo_pagina,
            veiculo_nome=f"{veiculo} — {arquivo}",
            largura_painel=700,
        )

        nome_jpg = f"pag{n:02d}.jpg"
        caminho_jpg = os.path.join(DIR_SAIDA, nome_jpg)
        img_quatro.save(caminho_jpg, "JPEG", quality=90, optimize=True)

        print(
            f"[{idx:02d}/{len(paginas):02d}] {rotulo_pagina} ({veiculo}) -> {nome_jpg} | "
            f"Ouro: {c_ouro['total']} | Extrator: {c_ext['total']} | LS16: {c_ls16['total']} | LS3: {c_ls3['total']}"
        )

        dados_paginas.append({
            "n": n,
            "page_id": pid,
            "uf": uf,
            "veiculo": veiculo,
            "arquivo": arquivo,
            "pagina": pagina,
            "imagem": img_nome,
            "dim_pt": f"{w_pt:.1f} × {h_pt:.1f}",
            "dim_px": f"{w_px} × {h_px}",
            "contagens": {
                "ouro": c_ouro,
                "extrator": c_ext,
                "ls16": c_ls16,
                "ls3": c_ls3,
            },
        })

    # Gravar contagens JSON (resiliencia / cache)
    with open(ARQ_CONTAGENS, "w", encoding="utf-8") as f:
        json.dump(
            {
                "totais": totais_sistemas,
                "paginas": dados_paginas,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Gerar HTML
    gerar_html(dados_paginas, totais_sistemas, ARQ_HTML)
    print(f"[OK] Imagens salvas sob: {os.path.relpath(DIR_SAIDA, RAIZ)}")
    print(f"[OK] Relatorio HTML estatico salvo em: {os.path.relpath(ARQ_HTML, RAIZ)}")
    print("[CONCLUIDO] Execucao finalizada com sucesso.")


if __name__ == "__main__":
    main()
