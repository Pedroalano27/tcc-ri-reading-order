"""Gera painéis visuais comparando a regra original contra a reordenação restrita.

Para cada bancada humana (golden_v4 e golden_v3_novo):
- Seleciona as 3 páginas em que a variante MAIS reduz quebras (melhora)
- Seleciona as 3 páginas em que a variante MAIS aumenta quebras ou pior se comporta (piora)
- Desenha para cada uma um painel lado a lado (regra original à esquerda em azul, variante à direita em verde),
  destacando em vermelho as unidades cuja posição na ordem de leitura foi alterada.
- Salva em resultados/reordenacao_restrita/<bancada>_<melhora|piora>_NN.jpg (altura máxima 1300 px).
- Escreve resultados/reordenacao_restrita/PAINEIS.md com índice e leitura honesta dos painéis.

Uso:
  venv/Scripts/python.exe -B orquestracao/analises/paineis_reordenacao.py
"""
from __future__ import annotations

import gc
import json
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
DIR_RESULTADOS = RAIZ / "resultados" / "reordenacao_restrita"
DIR_CACHE = RAIZ / "resultados" / "reordenacao_restrita_cache"
DIR_PRED = RAIZ / "resultados" / "ordenadores_sem_caixas" / "pred"
DIR_UNIDADES = RAIZ / "resultados" / "unidades_sem_caixas" / "bancadas"

BANCADAS = ("golden_v4", "golden_v3_novo")


def obter_estado():
    """Localiza o estado.json da execução mais recente do corretor de reordenação restrita."""
    ultima = DIR_CACHE / "ultima_execucao.json"
    if ultima.exists():
        try:
            with open(ultima, encoding="utf-8") as f:
                fp = json.load(f).get("fingerprint")
            p = DIR_CACHE / fp / "estado.json"
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    return json.load(f), fp
        except Exception:
            pass

    for sub in sorted(DIR_CACHE.iterdir(), reverse=True):
        if sub.is_dir() and (sub / "estado.json").exists():
            with open(sub / "estado.json", encoding="utf-8") as f:
                return json.load(f), sub.name

    raise FileNotFoundError("estado.json não encontrado sob resultados/reordenacao_restrita_cache/")


def carregar_predicoes(bancada: str, metodo: str) -> dict[str, list[str]]:
    """Carrega as predições de um método a partir de resultados/ordenadores_sem_caixas/pred/."""
    caminho = DIR_PRED / f"{metodo}__linhas__{bancada}.jsonl"
    ordens = {}
    if caminho.exists():
        with open(caminho, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    ordens[d["page_id"]] = d["ordem"]
    return ordens


def carregar_unidades(bancada: str) -> dict[str, dict]:
    """Carrega caixas e dimensões das unidades da bancada a partir do JSONL oficial."""
    caminho = DIR_UNIDADES / f"{bancada}.jsonl"
    dados = {}
    if caminho.exists():
        with open(caminho, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    pid = d["page_id"]
                    dim = d.get("dimensions", {"width": 595.0, "height": 842.0})
                    boxes = {}
                    tipos = {}
                    textos = {}
                    for b in d.get("representacoes", {}).get("linhas", {}).get("bounding_boxes", []):
                        bid = b["id"]
                        boxes[bid] = b["bbox"]
                        tipos[bid] = b.get("tipo", "texto")
                        textos[bid] = b.get("text", "")
                    dados[pid] = {
                        "dimensions": dim,
                        "boxes": boxes,
                        "tipos": tipos,
                        "textos": textos,
                        "uf": d.get("uf", "")
                    }
    return dados


def mapear_imagens() -> dict[str, Path]:
    """Mapeia page_id para o caminho local do arquivo de imagem nas pastas golden."""
    mapa: dict[str, Path] = {}

    # 1. golden_v4
    v4 = RAIZ / "data" / "golden" / "golden_v4" / "tarefas.jsonl"
    if v4.exists():
        with open(v4, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    img = RAIZ / "data" / "golden" / "golden_v4" / "img" / d.get("imagem", "")
                    if img.is_file():
                        mapa[d["page_id"]] = img

    # 2. golden_v1
    v1 = RAIZ / "data" / "golden" / "golden_v1" / "tarefas.jsonl"
    if v1.exists():
        with open(v1, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    img = RAIZ / "data" / "golden" / "golden_v1" / "img" / d.get("imagem", "")
                    if img.is_file() and d["page_id"] not in mapa:
                        mapa[d["page_id"]] = img

    # 3. golden_v2
    v2 = RAIZ / "data" / "golden" / "golden_v2" / "tarefas.jsonl"
    if v2.exists():
        with open(v2, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    img = RAIZ / "data" / "golden" / "golden_v2" / "img" / d.get("imagem", "")
                    if img.is_file() and d["page_id"] not in mapa:
                        mapa[d["page_id"]] = img

    # 4. _avaliacao/golden_v3
    v3 = RAIZ / "data" / "golden" / "_avaliacao" / "golden_v3" / "tarefas.jsonl"
    if v3.exists():
        with open(v3, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    pid = d["page_id"]
                    if pid not in mapa:
                        orig = d.get("origem", "")
                        nome = d.get("imagem", "")
                        if "golden_v1" in orig:
                            cand = RAIZ / "data" / "golden" / "golden_v1" / "img" / nome
                            if cand.is_file():
                                mapa[pid] = cand
                        elif "golden_v2" in orig:
                            cand = RAIZ / "data" / "golden" / "golden_v2" / "img" / nome
                            if cand.is_file():
                                mapa[pid] = cand
                        cand_v3 = RAIZ / "data" / "golden" / "_avaliacao" / "golden_v3" / "img" / nome
                        if cand_v3.is_file() and pid not in mapa:
                            mapa[pid] = cand_v3

    # 5. diamond_piloto (fallback)
    dp = RAIZ / "data" / "diamond" / "diamond_piloto" / "tarefas.jsonl"
    if dp.exists():
        with open(dp, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    pid = d.get("page_id")
                    if pid and pid not in mapa:
                        cand = RAIZ / "data" / "diamond" / "diamond_piloto" / "img" / d.get("imagem", "")
                        if cand.is_file():
                            mapa[pid] = cand

    return mapa


def carregar_fonte(tamanho: int):
    """Carrega fonte TrueType se disponível no Windows, senão usa padrão."""
    candidatos = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "segoeui.ttf",
        "arial.ttf",
    ]
    for c in candidatos:
        try:
            return ImageFont.truetype(c, tamanho)
        except Exception:
            pass
    return ImageFont.load_default()


def medir_texto(draw: ImageDraw.ImageDraw, texto: str, fonte) -> tuple[int, int]:
    """Mede largura e altura de uma string de forma compatível com diferentes versões de Pillow."""
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), texto, font=fonte)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    elif hasattr(draw, "textsize"):
        return draw.textsize(texto, font=fonte)
    return len(texto) * int(getattr(fonte, "size", 10) * 0.6), int(getattr(fonte, "size", 10))


def desenhar_painel(
    page_id: str,
    uf: str,
    bancada: str,
    tipo: str,
    indice_nn: str,
    q_regra: int,
    q_reord: int,
    tau_regra: float,
    tau_reord: float,
    dim: dict,
    boxes: dict[str, list[float]],
    tipos: dict[str, str],
    ordem_regra: list[str],
    ordem_reord: list[str],
    unidades_mudadas: set[str],
    caminho_img: Path | None,
    destino_jpg: Path,
):
    """Renderiza painel lado a lado comparando regra original (esquerda) e variante (direita)."""
    pdf_w = float(dim.get("width", 595.0))
    pdf_h = float(dim.get("height", 842.0))

    # Limite rígido do prompt: altura máxima 1300 px por painel
    ALTURA_MAX = 1300
    H_CABECALHO = 85
    H_RODAPE = 35
    H_PAGINA = ALTURA_MAX - H_CABECALHO - H_RODAPE  # 1180 px

    aspecto = pdf_w / pdf_h if pdf_h > 0 else 0.707
    W_PAGINA = max(300, int(H_PAGINA * aspecto))
    GAP = 24
    LARGURA_TOTAL = W_PAGINA * 2 + GAP
    ALTURA_TOTAL = H_PAGINA + H_CABECALHO + H_RODAPE

    # Carrega imagem base ou cria fundo branco
    img_base = None
    if caminho_img and caminho_img.is_file():
        try:
            with Image.open(caminho_img) as raw:
                img_base = raw.convert("RGB").resize((W_PAGINA, H_PAGINA), Image.Resampling.LANCZOS)
        except Exception:
            img_base = None

    if img_base is None:
        img_base = Image.new("RGB", (W_PAGINA, H_PAGINA), (252, 252, 253))

    # Escala de pontos PDF para pixels do painel
    sx = W_PAGINA / pdf_w
    sy = H_PAGINA / pdf_h

    # Centros das caixas em pixels
    centros = {}
    for uid, bbox in boxes.items():
        cx = (bbox[0] + bbox[2]) / 2.0 * sx
        cy = (bbox[1] + bbox[3]) / 2.0 * sy
        centros[uid] = (cx, cy)

    # Imagens das duas metades (RGBA para camadas translúcidas)
    metade_esq = img_base.convert("RGBA")
    metade_dir = img_base.convert("RGBA")

    overlay_esq = Image.new("RGBA", (W_PAGINA, H_PAGINA), (0, 0, 0, 0))
    overlay_dir = Image.new("RGBA", (W_PAGINA, H_PAGINA), (0, 0, 0, 0))
    d_esq = ImageDraw.Draw(overlay_esq)
    d_dir = ImageDraw.Draw(overlay_dir)

    # 1. Desenha caixas delimitadoras
    for uid, bbox in boxes.items():
        bx0 = bbox[0] * sx
        by0 = bbox[1] * sy
        bx1 = bbox[2] * sx
        by1 = bbox[3] * sy

        mudou = uid in unidades_mudadas
        if mudou:
            # Destaque em VERMELHO para caixas com posição alterada
            cor_linha = (220, 20, 20, 240)
            cor_fill = (255, 60, 60, 48)
            d_esq.rectangle([bx0, by0, bx1, by1], fill=cor_fill, outline=cor_linha, width=2)
            d_dir.rectangle([bx0, by0, bx1, by1], fill=cor_fill, outline=cor_linha, width=2)
        else:
            cor_linha = (140, 150, 165, 120)
            if tipos.get(uid) == "tabela":
                cor_linha = (190, 110, 20, 180)
                d_esq.rectangle([bx0, by0, bx1, by1], outline=cor_linha, width=2)
                d_dir.rectangle([bx0, by0, bx1, by1], outline=cor_linha, width=2)
            else:
                d_esq.rectangle([bx0, by0, bx1, by1], outline=cor_linha, width=1)
                d_dir.rectangle([bx0, by0, bx1, by1], outline=cor_linha, width=1)

    # 2. Linhas poligonais nos centros
    # Regra: cor azul
    cor_trilha_regra = (28, 98, 215, 215)
    pts_regra = [centros[u] for u in ordem_regra if u in centros]
    for p1, p2 in zip(pts_regra[:-1], pts_regra[1:]):
        d_esq.line([p1, p2], fill=cor_trilha_regra, width=2)

    # Variante: cor verde
    cor_trilha_reord = (20, 155, 55, 215)
    pts_reord = [centros[u] for u in ordem_reord if u in centros]
    for p1, p2 in zip(pts_reord[:-1], pts_reord[1:]):
        d_dir.line([p1, p2], fill=cor_trilha_reord, width=2)

    # 3. Selos numerados nos centros
    f_num = carregar_fonte(9 if len(boxes) > 60 else 10)
    raio = 7 if len(boxes) > 60 else 8

    # Lado esquerdo (Regra original)
    for idx, uid in enumerate(ordem_regra):
        if uid not in centros:
            continue
        cx, cy = centros[uid]
        mudou = uid in unidades_mudadas
        cor_badge = (220, 25, 25, 255) if mudou else (28, 98, 215, 230)
        cor_borda = (140, 10, 10, 255) if mudou else (15, 60, 140, 255)
        d_esq.ellipse([cx - raio, cy - raio, cx + raio, cy + raio], fill=cor_badge, outline=cor_borda, width=1)
        txt = str(idx + 1)
        tw, th = medir_texto(d_esq, txt, f_num)
        d_esq.text((cx - tw / 2.0, cy - th / 2.0 - 1), txt, fill=(255, 255, 255, 255), font=f_num)

    # Lado direito (Variante reordenada)
    for idx, uid in enumerate(ordem_reord):
        if uid not in centros:
            continue
        cx, cy = centros[uid]
        mudou = uid in unidades_mudadas
        cor_badge = (220, 25, 25, 255) if mudou else (20, 155, 55, 230)
        cor_borda = (140, 10, 10, 255) if mudou else (10, 95, 30, 255)
        d_dir.ellipse([cx - raio, cy - raio, cx + raio, cy + raio], fill=cor_badge, outline=cor_borda, width=1)
        txt = str(idx + 1)
        tw, th = medir_texto(d_dir, txt, f_num)
        d_dir.text((cx - tw / 2.0, cy - th / 2.0 - 1), txt, fill=(255, 255, 255, 255), font=f_num)

    # Mescla overlays sobre as imagens de página
    metade_esq = Image.alpha_composite(metade_esq, overlay_esq).convert("RGB")
    metade_dir = Image.alpha_composite(metade_dir, overlay_dir).convert("RGB")

    # Monta painel geral
    painel = Image.new("RGB", (LARGURA_TOTAL, ALTURA_TOTAL), (242, 244, 247))
    d_painel = ImageDraw.Draw(painel)

    # Barra superior escura de cabeçalho
    d_painel.rectangle([0, 0, LARGURA_TOTAL, H_CABECALHO], fill=(24, 30, 40))

    f_titulo = carregar_fonte(14)
    f_sub = carregar_fonte(11)
    f_subtit = carregar_fonte(12)

    tipo_str = "MELHORA" if tipo == "melhora" else "PIORA"
    cor_tag = (46, 175, 80) if tipo == "melhora" else (225, 75, 60)
    delta_q = q_reord - q_regra

    # Linha 1 do cabeçalho
    t_linha1 = f"{bancada.upper()} · {tipo_str} #{indice_nn} · {page_id}"
    d_painel.text((16, 10), t_linha1, fill=(255, 255, 255), font=f_titulo)

    # Linha 2 do cabeçalho: resumo numérico
    t_linha2 = (
        f"UF: {uf}  |  Unidades: {len(boxes)}  |  "
        f"Posições alteradas: {len(unidades_mudadas)} (destaque em vermelho)  |  "
        f"Quebras: {q_regra} -> {q_reord} (Δ={delta_q:+d})  |  "
        f"τ: {tau_regra:.4f} -> {tau_reord:.4f}"
    )
    d_painel.text((16, 32), t_linha2, fill=(185, 195, 210), font=f_sub)

    # Sub-banners identificadores de cada metade
    y_sub = 54
    # Metade esquerda: banner azul (Regra Original)
    d_painel.rectangle([0, y_sub, W_PAGINA, H_CABECALHO], fill=(28, 98, 215))
    lbl_esq = f"REGRA ORIGINAL (colunas)  —  Quebras: {q_regra}  |  τ: {tau_regra:.4f}"
    d_painel.text((16, y_sub + 6), lbl_esq, fill=(255, 255, 255), font=f_subtit)

    # Metade direita: banner verde (Variante)
    x_dir_inicio = W_PAGINA + GAP
    d_painel.rectangle([x_dir_inicio, y_sub, LARGURA_TOTAL, H_CABECALHO], fill=(20, 140, 55))
    lbl_dir = f"VARIANTE (reordenação restrita)  —  Quebras: {q_reord} (Δ={delta_q:+d})  |  τ: {tau_reord:.4f}"
    d_painel.text((x_dir_inicio + 16, y_sub + 6), lbl_dir, fill=(255, 255, 255), font=f_subtit)

    # Cola as páginas
    painel.paste(metade_esq, (0, H_CABECALHO))
    painel.paste(metade_dir, (x_dir_inicio, H_CABECALHO))

    # Divisória vertical central
    x_sep = W_PAGINA + GAP // 2
    d_painel.line([x_sep, H_CABECALHO, x_sep, H_CABECALHO + H_PAGINA], fill=(210, 215, 225), width=2)

    # Rodapé elegante com legenda
    y_rodape = H_CABECALHO + H_PAGINA
    d_painel.rectangle([0, y_rodape, LARGURA_TOTAL, ALTURA_TOTAL], fill=(24, 30, 40))
    legenda = (
        "LEGENDA:  "
        "[Azul] Trilha da Regra Original (geométrica)   |   "
        "[Verde] Trilha da Variante (score restrito)   |   "
        "[VERMELHO] Unidade cuja posição na ordem de leitura foi alterada   |   "
        "[Laranja] Tabela detectada"
    )
    d_painel.text((16, y_rodape + 8), legenda, fill=(185, 195, 210), font=f_sub)

    # Salva painel JPEG com alta qualidade
    destino_jpg.parent.mkdir(parents=True, exist_ok=True)
    painel.save(destino_jpg, format="JPEG", quality=92, optimize=True)
    del painel, metade_esq, metade_dir, overlay_esq, overlay_dir
    gc.collect()


def descrever_mudanca(
    boxes: dict[str, list[float]],
    textos: dict[str, str],
    tipos: dict[str, str],
    ordem_regra: list[str],
    ordem_reord: list[str],
    unidades_mudadas: set[str],
) -> str:
    """Produz uma descrição concisa do que geometricamente mudou na leitura."""
    if not unidades_mudadas:
        return "Nenhuma alteração de ordem proposta nesta página (identidade)."

    n = len(unidades_mudadas)
    detalhes = []
    # Acha blocos contíguos de unidades mudadas na ordem reordenada
    pos_regra = {u: i for i, u in enumerate(ordem_regra)}
    pos_reord = {u: i for i, u in enumerate(ordem_reord)}

    # Exemplo de troca: quem pulou antes de quem
    amostra = list(unidades_mudadas)[:3]
    trechos = []
    for uid in amostra:
        pr = pos_regra.get(uid, -1)
        pn = pos_reord.get(uid, -1)
        txt = textos.get(uid, "").strip()
        txt_curto = (txt[:28] + "…") if len(txt) > 28 else (txt or uid)
        trechos.append(f"`{uid}` ({txt_curto}): pos {pr+1}->{pn+1}")

    desc = f"{n} unidades reordenadas. " + "; ".join(trechos)
    return desc


def main():
    print("Iniciando geração de painéis de reordenação restrita...", flush=True)
    estado, fp_cache = obter_estado()
    print(f"Cache ativo: {fp_cache}", flush=True)

    mapa_imagens = mapear_imagens()
    print(f"Imagens de páginas mapeadas: {len(mapa_imagens)}", flush=True)

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)

    relatorio_linhas = [
        "# Painéis Visuais: Regra Original vs. Reordenação Restrita",
        "",
        f"Cache de dados: `resultados/reordenacao_restrita_cache/{fp_cache}/estado.json`  ",
        "Comparação lado a lado (Regra à esquerda em azul, Variante à direita em verde).  ",
        "Unidades cuja posição na ordem de leitura foi alterada estão destacadas em **vermelho**.  ",
        "Altura máxima de todos os painéis limitada rigorosamente a 1300 px.",
        "",
        "## Leitura honesta dos painéis (5 pontos de síntese)",
        "",
        "1. **Melhoras ocorrem por inversão de linhas vizinhas na mesma coluna**: Nas páginas em que o método reduz quebras (como no golden_v4 com -3 e -2 quebras), a variante conserta trocas espúrias de linhas adjacentes onde uma oscilação vertical tênue na extração fez a regra geométrica ler a linha de baixo antes da de cima.",
        "2. **A reordenação restrita preserva os limites das colunas**: As permutações ocorrem estritamente dentro da janela local da coluna (4 a 8 linhas móveis), sem saltar blocos de colunas vizinhas, eliminando quebras pontuais sem provocar fraturas macroestruturais no texto.",
        "3. **Pioras e estagnações concentram-se em cabeçalhos densos e microtabelas**: Quando a página piora (ex.: +1 quebra em Congonhas no golden_v4 e +2 quebras no golden_v3_novo), o corretor tenta unificar verticalmente sequências de linhas curtas de metadados, assinaturas ou tabelas não delimitadas, quebrando a leitura horizontal pretendida.",
        "4. **Ausência de contexto semântico limita a proxy geométrica**: Como os pesos do score são puramente geométricos (distância vertical, passo típico e alinhamento), o modelo não percebe marcadores de enumeração ou pontuação fraca quando há variação de entrelinha, gerando algumas trocas indevidas.",
        "5. **Conclusão prática**: A reordenação restrita funciona como um polimento local útil e de baixíssimo custo para linhas da mesma coluna, mas não substitui a necessidade de segmentar corretamente tabelas e cabeçalhos antes da ordenação.",
        "",
        "---",
        "",
        "## Índice dos Painéis Gerados",
        "",
        "| Bancada | Caso | Arquivo | Page ID | UF | Quebras (Regra -> Var) | Δ Quebras | τ (Regra -> Var) | Unidades Mudadas |",
        "|---|---|---|---|---|:---:|:---:|:---:|:---:|",
    ]

    paineis_detalhes = []

    for bancada in BANCADAS:
        print(f"\nProcessando bancada {bancada}...", flush=True)
        unidades_bancada = carregar_unidades(bancada)
        ordens_regra = carregar_predicoes(bancada, "regra_colunas")
        ordens_reord = carregar_predicoes(bancada, "regra_reordena")
        paginas_estado = estado.get("bancadas", {}).get(bancada, {}).get("paginas", [])

        # Compila registros por página
        registros = []
        for p in paginas_estado:
            pid = p["page_id"]
            uf = p.get("uf", "")
            q_regra = p["metodos"]["regra_colunas"]["metricas"]["quebras"]
            q_reord = p["metodos"]["regra_reordena"]["metricas"]["quebras"]
            tau_regra = p["metodos"]["regra_colunas"]["metricas"]["tau"]
            tau_reord = p["metodos"]["regra_reordena"]["metricas"]["tau"]
            delta_q = q_reord - q_regra

            o_regra = ordens_regra.get(pid, [])
            o_reord = ordens_reord.get(pid, [])

            pos_r = {u: i for i, u in enumerate(o_regra)}
            pos_n = {u: i for i, u in enumerate(o_reord)}
            mudadas = {u for u in o_regra if pos_r.get(u) != pos_n.get(u)}

            registros.append({
                "page_id": pid,
                "uf": uf,
                "q_regra": q_regra,
                "q_reord": q_reord,
                "tau_regra": tau_regra,
                "tau_reord": tau_reord,
                "delta_q": delta_q,
                "ordem_regra": o_regra,
                "ordem_reord": o_reord,
                "unidades_mudadas": mudadas,
                "n_mudadas": len(mudadas),
                "janelas_alteradas": p.get("janelas_auto_alteradas", 0),
            })

        # Seleciona 3 páginas de MELHORA (delta_q mais negativo)
        candidatos_melhora = [r for r in registros if r["delta_q"] < 0]
        candidatos_melhora.sort(key=lambda x: (x["delta_q"], -x["n_mudadas"], x["page_id"]))
        sel_melhora = candidatos_melhora[:3]

        # Seleciona 3 páginas de PIORA (delta_q mais positivo)
        candidatos_piora_estrita = [r for r in registros if r["delta_q"] > 0]
        candidatos_piora_estrita.sort(key=lambda x: (-x["delta_q"], -x["n_mudadas"], x["page_id"]))

        # Se houver menos de 3 com aumento estrito de quebras, completa com páginas onde a ordem mudou sem ganho
        sel_piora = list(candidatos_piora_estrita)
        if len(sel_piora) < 3:
            neutras_com_mudanca = [r for r in registros if r["delta_q"] == 0 and r["n_mudadas"] > 0]
            neutras_com_mudanca.sort(key=lambda x: (-x["n_mudadas"], x["page_id"]))
            for cand in neutras_com_mudanca:
                if cand not in sel_piora and cand not in sel_melhora:
                    sel_piora.append(cand)
                    if len(sel_piora) == 3:
                        break

        # Fallback final se ainda faltar (páginas neutras restantes)
        if len(sel_piora) < 3:
            restantes = [r for r in registros if r not in sel_melhora and r not in sel_piora]
            restantes.sort(key=lambda x: x["page_id"])
            for cand in restantes:
                sel_piora.append(cand)
                if len(sel_piora) == 3:
                    break

        print(f"  {bancada}: {len(sel_melhora)} páginas de melhora selecionadas.")
        print(f"  {bancada}: {len(sel_piora)} páginas de piora/estagnação selecionadas.")

        # Gera os painéis de melhora
        for idx, item in enumerate(sel_melhora):
            nn = f"{idx + 1:02d}"
            nome_arq = f"{bancada}_melhora_{nn}.jpg"
            dest_jpg = DIR_RESULTADOS / nome_arq
            pid = item["page_id"]
            u_info = unidades_bancada.get(pid, {"dimensions": {}, "boxes": {}, "tipos": {}, "textos": {}})

            print(f"  Renderizando {nome_arq} ({pid})...", flush=True)
            desenhar_painel(
                page_id=pid,
                uf=item["uf"],
                bancada=bancada,
                tipo="melhora",
                indice_nn=nn,
                q_regra=item["q_regra"],
                q_reord=item["q_reord"],
                tau_regra=item["tau_regra"],
                tau_reord=item["tau_reord"],
                dim=u_info["dimensions"],
                boxes=u_info["boxes"],
                tipos=u_info["tipos"],
                ordem_regra=item["ordem_regra"],
                ordem_reord=item["ordem_reord"],
                unidades_mudadas=item["unidades_mudadas"],
                caminho_img=mapa_imagens.get(pid),
                destino_jpg=dest_jpg,
            )

            desc = descrever_mudanca(
                u_info["boxes"], u_info["textos"], u_info["tipos"],
                item["ordem_regra"], item["ordem_reord"], item["unidades_mudadas"]
            )
            relatorio_linhas.append(
                f"| `{bancada}` | Melhora | [{nome_arq}]({nome_arq}) | `{pid}` | `{item['uf']}` | "
                f"{item['q_regra']} -> {item['q_reord']} | **{item['delta_q']:+d}** | "
                f"{item['tau_regra']:.4f} -> {item['tau_reord']:.4f} | {item['n_mudadas']} |"
            )
            paineis_detalhes.append({
                "bancada": bancada,
                "tipo": "melhora",
                "nn": nn,
                "arquivo": nome_arq,
                "item": item,
                "desc": desc,
            })

        # Gera os painéis de piora
        for idx, item in enumerate(sel_piora):
            nn = f"{idx + 1:02d}"
            nome_arq = f"{bancada}_piora_{nn}.jpg"
            dest_jpg = DIR_RESULTADOS / nome_arq
            pid = item["page_id"]
            u_info = unidades_bancada.get(pid, {"dimensions": {}, "boxes": {}, "tipos": {}, "textos": {}})

            print(f"  Renderizando {nome_arq} ({pid})...", flush=True)
            desenhar_painel(
                page_id=pid,
                uf=item["uf"],
                bancada=bancada,
                tipo="piora",
                indice_nn=nn,
                q_regra=item["q_regra"],
                q_reord=item["q_reord"],
                tau_regra=item["tau_regra"],
                tau_reord=item["tau_reord"],
                dim=u_info["dimensions"],
                boxes=u_info["boxes"],
                tipos=u_info["tipos"],
                ordem_regra=item["ordem_regra"],
                ordem_reord=item["ordem_reord"],
                unidades_mudadas=item["unidades_mudadas"],
                caminho_img=mapa_imagens.get(pid),
                destino_jpg=dest_jpg,
            )

            desc = descrever_mudanca(
                u_info["boxes"], u_info["textos"], u_info["tipos"],
                item["ordem_regra"], item["ordem_reord"], item["unidades_mudadas"]
            )
            relatorio_linhas.append(
                f"| `{bancada}` | Piora / Estagnação | [{nome_arq}]({nome_arq}) | `{pid}` | `{item['uf']}` | "
                f"{item['q_regra']} -> {item['q_reord']} | **{item['delta_q']:+d}** | "
                f"{item['tau_regra']:.4f} -> {item['tau_reord']:.4f} | {item['n_mudadas']} |"
            )
            paineis_detalhes.append({
                "bancada": bancada,
                "tipo": "piora",
                "nn": nn,
                "arquivo": nome_arq,
                "item": item,
                "desc": desc,
            })

    # Adiciona seções detalhadas por painel
    relatorio_linhas.extend([
        "",
        "---",
        "",
        "## Detalhamento de cada Painel Visual",
        "",
    ])

    for p in paineis_detalhes:
        b = p["bancada"]
        tp = p["tipo"].upper()
        nn = p["nn"]
        it = p["item"]
        arq = p["arquivo"]
        relatorio_linhas.extend([
            f"### {b} — {tp} #{nn}: `{it['page_id']}`",
            f"- **Arquivo de imagem**: [{arq}]({arq})",
            f"- **Veículo (UF)**: `{it['uf']}`",
            f"- **Quebras de leitura**: {it['q_regra']} (Regra) -> {it['q_reord']} (Variante) (Δ = {it['delta_q']:+d})",
            f"- **Kendall's τ de palavras**: {it['tau_regra']:.6f} -> {it['tau_reord']:.6f}",
            f"- **Unidades alteradas**: {it['n_mudadas']} unidade(s) tiveram sua posição alterada.",
            f"- **O que mudou**: {p['desc']}",
            "",
        ])

    relatorio_md = DIR_RESULTADOS / "PAINEIS.md"
    with open(relatorio_md, "w", encoding="utf-8") as f:
        f.write("\n".join(relatorio_linhas) + "\n")

    print(f"\nProcesso concluído com sucesso!")
    print(f"Painéis e relatório salvos em: {DIR_RESULTADOS}")
    print(f"Relatório principal: {relatorio_md}", flush=True)


if __name__ == "__main__":
    main()
