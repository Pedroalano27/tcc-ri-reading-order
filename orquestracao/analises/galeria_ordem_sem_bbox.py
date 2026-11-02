"""Galeria visual do método de ordem de leitura sem bounding box fina.

Gera as 44 imagens anotadas (pag01.jpg a pag44.jpg) e a página estática index.html
em resultados/galeria_ordem_sem_bbox/, ordenadas da pior para a melhor página (tau
crescente de regiões), para inspeção qualitativa pelo autor e pelo orientador.

Reutiliza integralmente as funções e definições de orquestracao/analises/ordem_sem_bbox.py:
não há reimplementação do algoritmo de ordenação, detecção de átomos ou cortes de colunas.
Todas as funções necessárias foram importadas diretamente do script existente.

Uso (executado da raiz pelo orquestrador):
    venv\\Scripts\\python.exe orquestracao/analises/galeria_ordem_sem_bbox.py
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import html
import json
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

# Reutilização direta do trabalho de ordem_sem_bbox.py
from orquestracao.analises.ordem_sem_bbox import (
    preparar,
    Config,
    prever,
    avaliar_fluxo,
    atomos,
    linhas_partidas,
    vales,
    vales_locais,
    envelope,
    RE_MARCACAO,
    NOTAS_INSPECAO,
)

# Melhor configuração apurada no relatório (resultados/ordem_sem_bbox.md):
# Projeção local com política de margens, score 0.45, vão de linha 1.2, vale 0.08
CONFIG_MELHOR = Config("projecao_local_margens", 0.45, 1.2, 0.08)

DIR_SAIDA = RAIZ / "resultados/galeria_ordem_sem_bbox"
DIR_IMAGENS_GOLDEN = RAIZ / "data/golden/golden_v4/img"
LARGURA_ALVO = 1100
ALTURA_BANNER = 64


def obter_fonte(tamanho: int = 14, negrito: bool = False) -> ImageFont.ImageFont:
    """Tenta carregar fonte do sistema Windows com fallback gracioso para padrão."""
    candidatos = [
        "C:/Windows/Fonts/segoeuib.ttf" if negrito else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if negrito else "C:/Windows/Fonts/calibri.ttf",
    ]
    for p in candidatos:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, tamanho)
            except Exception:
                pass
    return ImageFont.load_default()


def medir_texto(draw: ImageDraw.ImageDraw, texto: str, fonte: ImageFont.ImageFont) -> tuple[int, int]:
    """Mede largura e altura do texto de forma compatível com Pillow novo e legado."""
    if hasattr(fonte, "getbbox"):
        bbox = fonte.getbbox(texto)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    return draw.textsize(texto, font=fonte)


def extrair_cortes_colunas(q: dict, cfg: Config) -> tuple[list[float], list[int], list[dict]]:
    """Obtém os cortes de coluna e itens do corpo reproduzindo fielmente a chamada do preditor."""
    ws, p, h = q["ws"], q["p"], q["h"]
    det = q["d"]["detector"]["regioes"]
    ats, livres = atomos(ws, det, cfg.score)
    items = ats + linhas_partidas(ws, livres, cfg.gap, h)
    ids = list(range(len(items)))
    corpo = []
    H = p["dimensions"]["height"]
    for i in ids:
        m = items[i]
        cy = (m["bbox"][1] + m["bbox"][3]) / 2
        if m["ks"] and all(RE_MARCACAO.match(ws[k][0]) for k in m["ks"]):
            pass
        elif cy < 0.07 * H and m["bbox"][3] < 0.10 * H:
            pass
        elif cy > 0.95 * H:
            pass
        else:
            corpo.append(i)

    cortes = vales_locais(items, corpo, h, cfg.vale) if "local" in cfg.abordagem else vales(items, corpo, h, cfg.vale)
    if "local" in cfg.abordagem and not cortes:
        cortes = vales(items, corpo, h, cfg.vale)

    return cortes, corpo, items


def formatar_numero(v: float, n: int = 3) -> str:
    return f"{v:.{n}f}".replace(".", ",")


def desenhar_pagina(
    q: dict,
    rank: int,
    total_pags: int,
    eval_res: dict,
    ordered_items: list[dict],
    cortes: list[float],
    corpo_ids: list[int],
    raw_items: list[dict],
    caminho_saida: Path,
) -> None:
    """Renderiza a imagem pagNN.jpg com todas as camadas visuais exigidas."""
    img_nome = q["p"]["imagem"]
    img_path = DIR_IMAGENS_GOLDEN / img_nome
    if not img_path.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {img_path}")

    with Image.open(img_path) as im_orig:
        im_orig = im_orig.convert("RGB")
        orig_w, orig_h = im_orig.size
        scale = LARGURA_ALVO / orig_w
        canvas_h = int(round(orig_h * scale))
        base_page = im_orig.resize((LARGURA_ALVO, canvas_h), Image.Resampling.LANCZOS)

    dim_pdf = q["p"]["dimensions"]
    w_pdf, h_pdf = dim_pdf["width"], dim_pdf["height"]
    sx = LARGURA_ALVO / w_pdf
    sy = canvas_h / h_pdf

    # Camada transparente para faixas translúcidas, caixas e trajetórias
    overlay = Image.new("RGBA", (LARGURA_ALVO, canvas_h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # 1. Faixas das colunas detectadas em cores translúcidas
    corpo_boxes = [raw_items[i]["bbox"] for i in corpo_ids] if corpo_ids else [[0, 0, w_pdf, h_pdf]]
    lo_x, y0_corpo, hi_x, y1_corpo = envelope(corpo_boxes)
    y_band_top = max(0.0, y0_corpo - 4.0) * sy
    y_band_bot = min(h_pdf, y1_corpo + 4.0) * sy

    limites_x = [max(0.0, lo_x - 4.0)] + sorted(cortes) + [min(w_pdf, hi_x + 4.0)]
    paleta_colunas = [
        (37, 99, 235, 42),   # Azul translúcido
        (234, 88, 12, 42),   # Laranja translúcido
        (22, 163, 74, 42),   # Verde translúcido
        (147, 51, 234, 42),  # Roxo translúcido
        (202, 138, 4, 42),   # Âmbar translúcido
    ]

    fonte_col = obter_fonte(12, negrito=True)
    for k in range(len(limites_x) - 1):
        x0 = limites_x[k] * sx
        x1 = limites_x[k + 1] * sx
        cor = paleta_colunas[k % len(paleta_colunas)]
        draw_ov.rectangle([x0, y_band_top, x1, y_band_bot], fill=cor)

        # Rótulo da coluna no topo da faixa
        lbl_col = f"Coluna {k + 1}"
        lw, lh = medir_texto(draw_ov, lbl_col, fonte_col)
        badge_x = x0 + 6
        badge_y = y_band_top + 4
        draw_ov.rectangle([badge_x, badge_y, badge_x + lw + 8, badge_y + lh + 4], fill=(15, 23, 42, 170))
        draw_ov.text((badge_x + 4, badge_y + 2), lbl_col, font=fonte_col, fill=(248, 250, 252, 255))

    # Linhas verticais pontilhadas/delimitadoras nos cortes
    for c in cortes:
        cx_px = c * sx
        passo = 6
        for y_dash in range(int(y_band_top), int(y_band_bot), passo * 2):
            draw_ov.line([(cx_px, y_dash), (cx_px, min(y_band_bot, y_dash + passo))], fill=(30, 41, 59, 210), width=2)

    # 2. Blocos atômicos com contorno (tabela roxo, imagem cinza)
    fonte_atomo = obter_fonte(11, negrito=True)
    n_tabelas = 0
    n_imagens = 0
    for idx_item, m in enumerate(ordered_items):
        tipo = m["tipo"]
        if tipo not in ("table", "picture"):
            continue

        b = m["bbox"]
        bx0, by0, bx1, by1 = b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy

        if tipo == "table":
            n_tabelas += 1
            cor_borda = (126, 34, 206, 255)  # Roxo
            cor_fundo = (147, 51, 234, 32)
            rotulo = f"TABELA #{idx_item + 1}"
            cor_badge = (126, 34, 206, 230)
        else:
            n_imagens += 1
            cor_borda = (71, 85, 105, 255)   # Cinza escuro/ardósia
            cor_fundo = (100, 116, 139, 32)
            rotulo = f"IMAGEM #{idx_item + 1}"
            cor_badge = (71, 85, 105, 230)

        # Retângulo do átomo com preenchimento sutil e borda viva
        draw_ov.rectangle([bx0, by0, bx1, by1], fill=cor_fundo, outline=cor_borda, width=3)

        # Badge identificador do bloco atômico
        tw, th = medir_texto(draw_ov, rotulo, fonte_atomo)
        badge_x0 = bx0 + 3
        badge_y0 = max(0, by0 - th - 6) if by0 >= th + 8 else by0 + 3
        draw_ov.rectangle([badge_x0, badge_y0, badge_x0 + tw + 8, badge_y0 + th + 4], fill=cor_badge)
        draw_ov.text((badge_x0 + 4, badge_y0 + 2), rotulo, font=fonte_atomo, fill=(255, 255, 255, 255))

    # 3. Caminho de leitura previsto como uma linha ligando o centro de cada linha de texto na ordem
    linhas_texto = [m for m in ordered_items if m["tipo"] == "texto"]
    pontos_caminho = []
    for m in linhas_texto:
        b = m["bbox"]
        cx = ((b[0] + b[2]) / 2.0) * sx
        cy = ((b[1] + b[3]) / 2.0) * sy
        pontos_caminho.append((cx, cy))

    # Desenha os segmentos do caminho de leitura
    cor_linha = (220, 38, 38, 220)  # Vermelho vivo / carmesim
    cor_ponto = (185, 28, 28, 240)
    for i in range(len(pontos_caminho) - 1):
        p_ini = pontos_caminho[i]
        p_fim = pontos_caminho[i + 1]
        draw_ov.line([p_ini, p_fim], fill=cor_linha, width=2)
        draw_ov.ellipse([p_ini[0] - 2.5, p_ini[1] - 2.5, p_ini[0] + 2.5, p_ini[1] + 2.5], fill=cor_ponto)

    if pontos_caminho:
        ult = pontos_caminho[-1]
        draw_ov.ellipse([ult[0] - 2.5, ult[1] - 2.5, ult[0] + 2.5, ult[1] + 2.5], fill=cor_ponto)

    # Marcadores com número de ordem a cada 10 linhas (1, 10, 20, 30...) e na última linha
    fonte_badge = obter_fonte(10, negrito=True)
    total_linhas = len(linhas_texto)
    for idx_linha, (cx, cy) in enumerate(pontos_caminho):
        num_ordem = idx_linha + 1
        deve_rotular = (num_ordem == 1) or (num_ordem % 10 == 0) or (num_ordem == total_linhas)
        if not deve_rotular:
            continue

        txt_num = str(num_ordem)
        nw, nh = medir_texto(draw_ov, txt_num, fonte_badge)
        raio = max(9, nw // 2 + 4)

        # Círculo ou pílula vermelha com borda branca para visibilidade contrastante
        bx0 = cx - raio
        by0 = cy - raio
        bx1 = cx + raio
        by1 = cy + raio

        draw_ov.ellipse([bx0 - 1, by0 - 1, bx1 + 1, by1 + 1], fill=(255, 255, 255, 255))
        draw_ov.ellipse([bx0, by0, bx1, by1], fill=(185, 28, 28, 255))
        draw_ov.text((cx - nw / 2, cy - nh / 2 - 1), txt_num, font=fonte_badge, fill=(255, 255, 255, 255))

    # Mescla imagem base e overlay anotado
    pagina_anotada = Image.alpha_composite(base_page.convert("RGBA"), overlay).convert("RGB")

    # 4. Título no topo com tau e sucessor da página na régua de regiões
    reg_tau = eval_res["regioes"]["tau"]
    reg_suc = eval_res["regioes"]["sucessor"]
    reg_ard = eval_res["regioes"]["ard"]
    n_colunas = len(cortes) + 1
    uf = q["p"].get("uf", "").replace("official_diary_", "").upper()
    page_id = q["p"]["page_id"]

    # Cria canvas final com o banner superior
    canvas_final = Image.new("RGB", (LARGURA_ALVO, canvas_h + ALTURA_BANNER), (15, 23, 42))
    draw_banner = ImageDraw.Draw(canvas_final)

    fonte_tit1 = obter_fonte(15, negrito=True)
    fonte_tit2 = obter_fonte(12, negrito=False)
    fonte_leg = obter_fonte(11, negrito=True)

    # Linha 1 do banner: Rank, métricas de regiões
    sufixo_rank = " (PIOR)" if rank == 1 else (" (MELHOR)" if rank == total_pags else "")
    tit_linha1 = (
        f"#{rank:02d}/{total_pags:02d}{sufixo_rank}  |  "
        f"Régua de Regiões: τ = {formatar_numero(reg_tau)}  |  "
        f"Sucessor = {formatar_numero(reg_suc * 100, 1)}%  |  "
        f"ARD = {formatar_numero(reg_ard)}"
    )
    draw_banner.text((16, 8), tit_linha1, font=fonte_tit1, fill=(248, 250, 252))

    # Linha 2 do banner: Identificação do arquivo, UF, colunas, contagem de elementos
    tit_linha2 = (
        f"Pág: {page_id}  |  UF: {uf}  |  "
        f"Colunas detectadas: {n_colunas}  |  "
        f"Linhas de texto: {total_linhas}  |  "
        f"Átomos: {n_tabelas + n_imagens} (Tabela: {n_tabelas}, Imagem: {n_imagens})"
    )
    draw_banner.text((16, 32), tit_linha2, font=fonte_tit2, fill=(148, 163, 184))

    # Legenda compacta à direita do banner
    legenda_itens = [
        ("Colunas", (59, 130, 246)),
        ("Tabela", (147, 51, 234)),
        ("Imagem", (100, 116, 139)),
        ("Caminho", (220, 38, 38)),
    ]
    x_leg = LARGURA_ALVO - 18
    for texto_leg, cor_leg in reversed(legenda_itens):
        tw, th = medir_texto(draw_banner, texto_leg, fonte_leg)
        x_leg -= tw
        draw_banner.text((x_leg, 20), texto_leg, font=fonte_leg, fill=(226, 232, 240))
        x_leg -= 14
        draw_banner.rectangle([x_leg, 22, x_leg + 10, 32], fill=cor_leg)
        x_leg -= 16

    # Linha divisória sutil
    draw_banner.line([(0, ALTURA_BANNER - 1), (LARGURA_ALVO, ALTURA_BANNER - 1)], fill=(51, 65, 85), width=1)

    # Cola a página anotada abaixo do banner
    canvas_final.paste(pagina_anotada, (0, ALTURA_BANNER))

    # Salva imagem JPEG
    canvas_final.save(caminho_saida, format="JPEG", quality=90, optimize=True)


def gerar_index_html(paginas_ordenadas: list[dict], caminho_html: Path) -> None:
    """Gera index.html estático sem dependências externas, listando da pior para a melhor."""
    media_tau_reg = sum(p["eval"]["regioes"]["tau"] for p in paginas_ordenadas) / len(paginas_ordenadas)
    media_suc_reg = sum(p["eval"]["regioes"]["sucessor"] for p in paginas_ordenadas) / len(paginas_ordenadas)
    media_tau_lin = sum(p["eval"]["linhas"]["tau"] for p in paginas_ordenadas) / len(paginas_ordenadas)
    media_suc_lin = sum(p["eval"]["linhas"]["sucessor"] for p in paginas_ordenadas) / len(paginas_ordenadas)

    pior_pag = paginas_ordenadas[0]
    melhor_pag = paginas_ordenadas[-1]

    linhas_tabela_resumo = []
    cards_html = []

    for item in paginas_ordenadas:
        rank = item["rank"]
        page_id = html.escape(item["page_id"])
        uf = html.escape(item["uf"])
        col_det = item["n_colunas_detectadas"]
        col_orig = item["n_colunas_stats"]
        tau_r = item["eval"]["regioes"]["tau"]
        suc_r = item["eval"]["regioes"]["sucessor"]
        ard_r = item["eval"]["regioes"]["ard"]
        tau_l = item["eval"]["linhas"]["tau"]
        suc_l = item["eval"]["linhas"]["sucessor"]
        img_nome = item["nome_arquivo_jpg"]
        n_linhas = item["n_linhas_texto"]
        n_tab = item["n_tabelas"]
        n_img = item["n_imagens"]
        nota_insp = item.get("nota_inspecao", "")

        # Cores para badge de tau
        if tau_r >= 0.95:
            badge_classe = "badge-otimo"
        elif tau_r >= 0.85:
            badge_classe = "badge-bom"
        elif tau_r >= 0.70:
            badge_classe = "badge-alerta"
        else:
            badge_classe = "badge-critico"

        linhas_tabela_resumo.append(
            f"<tr>"
            f"<td class='tc-center'><strong>#{rank:02d}</strong></td>"
            f"<td class='tc-center'><a href='#card-{rank:02d}'><img src='{img_nome}' class='mini-thumb' alt='Página {rank}' loading='lazy'></a></td>"
            f"<td><code>{page_id}</code></td>"
            f"<td class='tc-center'><span class='tag-uf'>{uf}</span></td>"
            f"<td class='tc-center'><strong>{col_det}</strong> <span class='txt-muted'>(orig: {col_orig})</span></td>"
            f"<td class='tc-right'><span class='badge {badge_classe}'>{formatar_numero(tau_r)}</span></td>"
            f"<td class='tc-right'>{formatar_numero(suc_r * 100, 1)}%</td>"
            f"<td class='tc-right'>{formatar_numero(ard_r)}</td>"
            f"<td class='tc-right'>{formatar_numero(tau_l)}</td>"
            f"<td class='tc-right'>{formatar_numero(suc_l * 100, 1)}%</td>"
            f"<td class='tc-center'><a href='#card-{rank:02d}' class='btn-ver'>Ver</a></td>"
            f"</tr>"
        )

        bloco_nota = ""
        if nota_insp:
            nota_escapada = html.escape(nota_insp)
            nota_escapada = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", nota_escapada)
            bloco_nota = f"<div class='nota-inspecao'><strong>Nota da Inspeção Qualitativa:</strong> {nota_escapada}</div>"

        cards_html.append(
            f"<div class='card' id='card-{rank:02d}'>"
            f"  <div class='card-header'>"
            f"    <div class='card-title-group'>"
            f"      <span class='badge-posicao'>#{rank:02d} de {len(paginas_ordenadas)}</span>"
            f"      <h3 class='card-title'><code>{page_id}</code></h3>"
            f"    </div>"
            f"    <div class='card-tags'>"
            f"      <span class='tag-uf'>UF: {uf}</span>"
            f"      <span class='tag-info'>Colunas detectadas: <strong>{col_det}</strong> (stats: {col_orig})</span>"
            f"      <span class='tag-info'>Linhas: <strong>{n_linhas}</strong></span>"
            f"      <span class='tag-info'>Tabelas: <strong>{n_tab}</strong> | Imagens: <strong>{n_img}</strong></span>"
            f"    </div>"
            f"  </div>"
            f"  <div class='card-metrics'>"
            f"    <div class='metric-box'>"
            f"      <div class='metric-label'>τ Regiões (Ouro)</div>"
            f"      <div class='metric-val {badge_classe}'>{formatar_numero(tau_r)}</div>"
            f"    </div>"
            f"    <div class='metric-box'>"
            f"      <div class='metric-label'>Sucessor Regiões</div>"
            f"      <div class='metric-val'>{formatar_numero(suc_r * 100, 1)}%</div>"
            f"    </div>"
            f"    <div class='metric-box'>"
            f"      <div class='metric-label'>ARD Regiões</div>"
            f"      <div class='metric-val'>{formatar_numero(ard_r)}</div>"
            f"    </div>"
            f"    <div class='metric-box'>"
            f"      <div class='metric-label'>τ Linhas</div>"
            f"      <div class='metric-val'>{formatar_numero(tau_l)}</div>"
            f"    </div>"
            f"    <div class='metric-box'>"
            f"      <div class='metric-label'>Sucessor Linhas</div>"
            f"      <div class='metric-val'>{formatar_numero(suc_l * 100, 1)}%</div>"
            f"    </div>"
            f"  </div>"
            f"  {bloco_nota}"
            f"  <div class='card-image-wrap'>"
            f"    <a href='{img_nome}' target='_blank' title='Clique para abrir em resolução completa (1100 px)'>"
            f"      <img src='{img_nome}' alt='Página {page_id}' class='page-img' loading='lazy'>"
            f"    </a>"
            f"    <div class='card-img-hint'>Clique na imagem para abrir o arquivo completo em nova aba (1100 px).</div>"
            f"  </div>"
            f"</div>"
        )

    corpo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Galeria Visual — Ordem de Leitura sem Bounding Box Fina</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --accent: #f97316;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{ max-width: 1280px; margin: 0 auto; }}
    header {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    h1 {{ font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 8px; }}
    .subtitle {{ color: var(--text-muted); font-size: 15px; margin-bottom: 20px; }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .stat-card {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px 18px;
    }}
    .stat-label {{ font-size: 12px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }}
    .stat-val {{ font-size: 22px; font-weight: 700; color: #fff; margin-top: 4px; }}
    .stat-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 2px; }}

    .legenda-topo {{
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px 18px;
      margin: 20px 0;
      font-size: 13px;
    }}
    .legenda-flex {{ display: flex; flex-wrap: wrap; gap: 16px; margin-top: 8px; }}
    .legenda-item {{ display: flex; align-items: center; gap: 8px; }}
    .legenda-cor {{ width: 16px; height: 16px; border-radius: 4px; display: inline-block; }}

    .section-title {{ font-size: 20px; font-weight: 700; margin: 32px 0 16px; display: flex; align-items: center; justify-content: space-between; }}
    .table-wrap {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow-x: auto;
      margin-bottom: 36px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    th, td {{ padding: 10px 14px; border-bottom: 1px solid var(--card-border); }}
    th {{ background: rgba(15, 23, 42, 0.8); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    tr:hover td {{ background: rgba(51, 65, 85, 0.3); }}
    .tc-center {{ text-align: center; }}
    .tc-right {{ text-align: right; }}
    .mini-thumb {{ width: 44px; height: 58px; object-fit: cover; border-radius: 4px; border: 1px solid var(--card-border); }}
    .mini-thumb:hover {{ transform: scale(1.4); transition: transform 0.15s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}

    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; }}
    .badge-otimo {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }}
    .badge-bom {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }}
    .badge-alerta {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }}
    .badge-critico {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
    .tag-uf {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .tag-info {{ background: rgba(30, 41, 59, 0.8); border: 1px solid var(--card-border); color: #94a3b8; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
    .txt-muted {{ color: var(--text-muted); font-size: 11px; }}
    .btn-ver {{ background: var(--primary); color: #0f172a; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 11px; }}
    .btn-ver:hover {{ opacity: 0.9; }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      margin-bottom: 32px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .card-header {{
      padding: 16px 20px;
      background: rgba(15, 23, 42, 0.8);
      border-bottom: 1px solid var(--card-border);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}
    .card-title-group {{ display: flex; align-items: center; gap: 12px; }}
    .badge-posicao {{ background: #ef4444; color: #fff; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 13px; }}
    .card:last-child .badge-posicao {{ background: #22c55e; }}
    .card-title {{ font-size: 15px; color: #fff; word-break: break-all; }}
    .card-tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}

    .card-metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      padding: 16px 20px;
      background: rgba(30, 41, 59, 0.4);
      border-bottom: 1px solid var(--card-border);
    }}
    .metric-box {{
      background: rgba(15, 23, 42, 0.5);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      text-align: center;
    }}
    .metric-label {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; margin-bottom: 4px; }}
    .metric-val {{ font-size: 18px; font-weight: 700; color: #fff; }}

    .nota-inspecao {{
      margin: 16px 20px 0;
      padding: 12px 16px;
      background: rgba(245, 158, 11, 0.1);
      border-left: 4px solid #f59e0b;
      border-radius: 4px;
      font-size: 13px;
      color: #fde68a;
      line-height: 1.6;
    }}

    .card-image-wrap {{
      padding: 20px;
      text-align: center;
      background: #090d16;
    }}
    .page-img {{
      max-width: 100%;
      height: auto;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      box-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }}
    .card-img-hint {{ font-size: 12px; color: var(--text-muted); margin-top: 8px; }}
    footer {{ text-align: center; color: var(--text-muted); font-size: 13px; margin: 40px 0 20px; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Galeria Visual — Ordem de Leitura sem Bounding Box Fina</h1>
      <p class="subtitle">
        Inspeção qualitativa das <strong>44 páginas concluídas</strong> do Golden Dataset v4.
        Método: <code>projecao_local_margens_s0.45_g1.2_v0.08</code> (melhor configuração na amostra do relatório <code>ordem_sem_bbox.md</code>).
      </p>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total de Páginas</div>
          <div class="stat-val">{len(paginas_ordenadas)}</div>
          <div class="stat-sub">100% da amostra concluída</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">τ Médio de Regiões</div>
          <div class="stat-val" style="color: #4ade80;">{formatar_numero(media_tau_reg)}</div>
          <div class="stat-sub">Sucessor médio: {formatar_numero(media_suc_reg * 100, 1)}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">τ Médio de Linhas</div>
          <div class="stat-val" style="color: #38bdf8;">{formatar_numero(media_tau_lin)}</div>
          <div class="stat-sub">Sucessor médio: {formatar_numero(media_suc_lin * 100, 1)}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Pior Página (#01)</div>
          <div class="stat-val" style="color: #f87171;">τ = {formatar_numero(pior_pag['eval']['regioes']['tau'])}</div>
          <div class="stat-sub">{html.escape(pior_pag['uf'])}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Melhor Página (#{len(paginas_ordenadas):02d})</div>
          <div class="stat-val" style="color: #4ade80;">τ = {formatar_numero(melhor_pag['eval']['regioes']['tau'])}</div>
          <div class="stat-sub">{html.escape(melhor_pag['uf'])}</div>
        </div>
      </div>

      <div class="legenda-topo">
        <strong>Guia Visual das Camadas:</strong>
        <div class="legenda-flex">
          <div class="legenda-item"><span class="legenda-cor" style="background: rgba(37,99,235,0.7);"></span> <strong>Faixas de Colunas:</strong> cores translúcidas alternadas (azul, laranja, verde...)</div>
          <div class="legenda-item"><span class="legenda-cor" style="background: #9333ea;"></span> <strong>Tabela Atômica:</strong> contorno e badge roxos</div>
          <div class="legenda-item"><span class="legenda-cor" style="background: #64748b;"></span> <strong>Imagem Atômica:</strong> contorno e badge cinzas</div>
          <div class="legenda-item"><span class="legenda-cor" style="background: #dc2626;"></span> <strong>Caminho Previsto:</strong> linha carmesim ligando o centro de cada linha de texto com número a cada 10 linhas</div>
        </div>
      </div>
    </header>

    <div class="section-title">
      <span>Tabela Resumo das Páginas (ordenadas da pior para a melhor por τ crescente)</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="tc-center">Rank</th>
            <th class="tc-center">Miniatura</th>
            <th>Identificador da Página (page_id)</th>
            <th class="tc-center">UF</th>
            <th class="tc-center">Colunas</th>
            <th class="tc-right">τ Regiões</th>
            <th class="tc-right">Sucessor Reg.</th>
            <th class="tc-right">ARD Reg.</th>
            <th class="tc-right">τ Linhas</th>
            <th class="tc-right">Sucessor Lin.</th>
            <th class="tc-center">Ação</th>
          </tr>
        </thead>
        <tbody>
          {"".join(linhas_tabela_resumo)}
        </tbody>
      </table>
    </div>

    <div class="section-title">
      <span>Galeria de Páginas Detalhadas</span>
    </div>

    {"".join(cards_html)}

    <footer>
      TCC Ordem de Leitura e Layout em Diários Oficiais Brasileiros — UFG INF
    </footer>
  </div>
</body>
</html>
"""
    caminho_html.write_text(corpo_html, encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("Iniciando geração da galeria visual: Ordem sem Bounding Box Fina")
    print(f"Configuração alvo: {CONFIG_MELHOR.id}")
    print("=" * 70)

    DIR_SAIDA.mkdir(parents=True, exist_ok=True)

    # 1. Carrega todas as anotações concluídas do golden_v4
    ps, amostra = preparar()
    assert len(ps) == 44, f"Esperadas 44 páginas, encontradas {len(ps)}"
    print(f"[1/4] {len(ps)} páginas carregadas com sucesso.")

    # 2. Executa inferência com a melhor configuração e calcula métricas
    print("[2/4] Calculando predições, métricas e detecções de colunas...")
    dados_processados = []
    for idx, q in enumerate(ps):
        seq, ordered_items, diag = prever(q, CONFIG_MELHOR)
        eval_res = avaliar_fluxo(q, seq)
        eval_res["diag"].update(diag)

        cortes, corpo_ids, raw_items = extrair_cortes_colunas(q, CONFIG_MELHOR)

        page_id = q["p"]["page_id"]
        uf = q["p"].get("uf", "").replace("official_diary_", "").upper()
        col_stats = q["p"].get("stats", {}).get("n_colunas", 1)

        linhas_texto = [m for m in ordered_items if m["tipo"] == "texto"]
        n_tab = sum(1 for m in ordered_items if m["tipo"] == "table")
        n_img = sum(1 for m in ordered_items if m["tipo"] == "picture")

        nota_insp = NOTAS_INSPECAO.get(page_id, "")

        dados_processados.append({
            "q": q,
            "page_id": page_id,
            "uf": uf,
            "eval": eval_res,
            "ordered_items": ordered_items,
            "raw_items": raw_items,
            "cortes": cortes,
            "corpo_ids": corpo_ids,
            "n_colunas_detectadas": len(cortes) + 1,
            "n_colunas_stats": col_stats,
            "n_linhas_texto": len(linhas_texto),
            "n_tabelas": n_tab,
            "n_imagens": n_img,
            "nota_inspecao": nota_insp,
        })

    # 3. Ordena da PIOR para a MELHOR (tau crescente de regiões)
    # Desempate estável: sucessor de regiões, depois page_id
    dados_processados.sort(
        key=lambda d: (
            d["eval"]["regioes"]["tau"],
            d["eval"]["regioes"]["sucessor"],
            d["page_id"],
        )
    )

    for rank_idx, item in enumerate(dados_processados):
        rank = rank_idx + 1
        item["rank"] = rank
        item["nome_arquivo_jpg"] = f"pag{rank:02d}.jpg"

    print(f"[3/4] Páginas ordenadas da pior (τ = {dados_processados[0]['eval']['regioes']['tau']:.3f}) à melhor (τ = {dados_processados[-1]['eval']['regioes']['tau']:.3f}).")

    # 4. Renderiza imagens pagNN.jpg
    print("[4/4] Renderizando imagens e index.html...")
    for item in dados_processados:
        rank = item["rank"]
        nome_jpg = item["nome_arquivo_jpg"]
        caminho_jpg = DIR_SAIDA / nome_jpg
        desenhar_pagina(
            q=item["q"],
            rank=rank,
            total_pags=len(dados_processados),
            eval_res=item["eval"],
            ordered_items=item["ordered_items"],
            cortes=item["cortes"],
            corpo_ids=item["corpo_ids"],
            raw_items=item["raw_items"],
            caminho_saida=caminho_jpg,
        )
        print(f"  [#{rank:02d}/44] {nome_jpg} (τ={item['eval']['regioes']['tau']:.3f}) -> {item['page_id']}")

    caminho_html = DIR_SAIDA / "index.html"
    gerar_index_html(dados_processados, caminho_html)
    print(f"[OK] Galeria gerada com sucesso em: {DIR_SAIDA}")
    print(f"[OK] index.html: {caminho_html}")


if __name__ == "__main__":
    main()
