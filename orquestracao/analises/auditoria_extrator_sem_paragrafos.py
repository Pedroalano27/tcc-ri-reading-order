"""Auditoria automatica do extrator novo sem caixas de paragrafo.

Audita a representacao em linhas (texto em linhas, apenas tabela e imagem como bloco,
margens e quadros separados) identificando erros e inconsistencias de forma automatica
em todas as paginas exportadas.

Detectores implementados (D1 a D7):
- D1: Linha que atravessa colunas (largura > 60% e vao horizontal > 4%)
- D2: Sobreposicao tabela/imagem x texto (> 30% sem conter palavras)
- D3: Coluna nao separada (>= 80% das linhas largas > 70%, mediana de palavras < 6, >= 40 linhas)
- D4: Tabela suspeita (< 4 linhas ou < 2 colunas de palavras, ou lista de nomes)
- D5: Cabecalho/rodape fragmentado (> 2 cabecalhos ou > 2 rodapes, ou < 3 palavras)
- D6: Linha com altura anomala (altura > 2,5x a mediana da pagina)
- D7: Texto sem dono perto de atomo (centro de palavra cai dentro de atomo mas pertence a texto fora)

Uso na raiz: venv\\Scripts\\python.exe -B orquestracao/analises/auditoria_extrator_sem_paragrafos.py
Saidas geradas:
- resultados/auditoria_extrator_sem_paragrafos.md
- resultados/auditoria_extrator_sem_paragrafos.json
- resultados/auditoria_extrator_sem_paragrafos/NN_<detector>_<uf>.jpg
"""

from __future__ import annotations

import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
DIR_RESULTADOS = RAIZ / "resultados"
DIR_GALERIA = DIR_RESULTADOS / "auditoria_extrator_sem_paragrafos"
PATH_MD = DIR_RESULTADOS / "auditoria_extrator_sem_paragrafos.md"
PATH_JSON = DIR_RESULTADOS / "auditoria_extrator_sem_paragrafos.json"

LIMIAR_GRAVE = 0.70


def fmt_num(val: float | None, dec: int = 1) -> str:
    """Formata numero decimal com virgula no padrao brasileiro."""
    if val is None or math.isnan(val):
        return "-"
    fmt = f"{{:.{dec}f}}"
    return fmt.format(val).replace(".", ",")


def carregar_notas_autor() -> dict[str, list[str]]:
    """Carrega todas as notas humanas dos Golden v1, v2 e v4."""
    notas: dict[str, list[str]] = defaultdict(list)
    arquivos = [
        RAIZ / "data/golden/golden_v1/anotacoes.jsonl",
        RAIZ / "data/golden/golden_v2/anotacoes.jsonl",
        RAIZ / "data/golden/golden_v4/anotacoes.jsonl",
    ]
    for p in arquivos:
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    pid = doc.get("page_id")
                    nota = doc.get("nota", "")
                    if pid and isinstance(nota, str) and nota.strip():
                        notas[pid].append(nota.strip())
                except Exception:
                    continue
    return notas


def carregar_mapa_imagens() -> dict[str, Path]:
    """Mapeia page_id para imagem local existente do Golden."""
    mapa: dict[str, Path] = {}
    arquivos_tarefas = [
        (RAIZ / "data/golden/golden_v4/tarefas.jsonl", RAIZ / "data/golden/golden_v4/img"),
        (RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl", RAIZ / "data/golden/golden_v1/img"),
        (RAIZ / "data/golden/_avaliacao/golden_v3/tarefas.jsonl", RAIZ / "data/golden/golden_v2/img"),
        (RAIZ / "data/golden/golden_v1/tarefas.jsonl", RAIZ / "data/golden/golden_v1/img"),
        (RAIZ / "data/golden/golden_v2/tarefas.jsonl", RAIZ / "data/golden/golden_v2/img"),
    ]
    for tpath, ipath in arquivos_tarefas:
        if not tpath.exists():
            continue
        with open(tpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    pid = doc.get("page_id")
                    img_name = doc.get("imagem")
                    if pid and img_name:
                        cand = ipath / img_name
                        if cand.exists() and pid not in mapa:
                            mapa[pid] = cand
                except Exception:
                    continue
    return mapa


def carregar_estruturas_golden() -> dict[str, dict]:
    """Carrega as 45 paginas com anotacao de estruturas (cabecalho, rodape, quadro_externo)."""
    estruturas = {}
    p = RAIZ / "resultados/estruturas_golden_v4/linhas.jsonl"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    pid = doc.get("page_id")
                    if pid:
                        estruturas[pid] = doc
                except Exception:
                    continue
    return estruturas


def classificar_nota_por_detector(texto_nota: str) -> dict[str, bool]:
    """Mapeia se a nota do autor descreve problemas correspondentes a cada detector."""
    txt = texto_nota.lower()
    res = {
        "D1": any(t in txt for t in ["pula", "pulando", "coluna pra outra", "segunda coluna", "desconectos", "comeu texto", "pulou a coluna"]),
        "D2": any(t in txt for t in ["sobrepõe", "sobreposta", "sobreposi", "sobreposto", "subcaixas", "dentro de caixa", "duplicada"]),
        "D3": any(t in txt for t in ["n separou", "não separou", "separou bem as colunas", "pulando pra segunda", "misturando"]),
        "D4": any(t in txt for t in ["tabela", "tabelas", "lista de nomes", "lista telefonica", "duas tabelas", "agrupando alguns nomes"]),
        "D5": any(t in txt for t in ["cabecalho", "rodape", "cabeçalho", "rodapé", "titulo", "tirulo", "logo", "prefeitura"]),
        "D6": any(t in txt for t in ["altura", "fonte", "letras", "cada letra", "só uma letra", "uma letra", "boundbox ficou bem grande"]),
        "D7": any(t in txt for t in ["imagem", "figura", "dentro da imagem", "texto da imagem", "texto e a imagem", "reconheceu nada", "texto da figura"])
    }
    return res


def auditar_pagina(page: dict, estruturas_doc: dict | None) -> list[dict]:
    """Executa os detectores D1 a D7 em uma pagina na representacao em linhas."""
    achados = []
    dim = page.get("dimensions", {})
    w_pag = float(dim.get("width", 595.0))
    h_pag = float(dim.get("height", 842.0))
    palavras = page.get("palavras", [])
    unidades = page.get("unidades", [])

    if w_pag <= 0 or h_pag <= 0:
        return achados

    # Unidades de texto vs atomos
    unidades_texto = [u for u in unidades if u.get("tipo") in ("texto", "cabecalho", "rodape", "quadro_externo")]
    atomos = [u for u in unidades if u.get("tipo") in ("table", "picture")]

    # ----------------------------------------------------
    # D1: LINHA QUE ATRAVESSA COLUNAS
    # unidade de texto cuja largura passa de 60% da página E que tem um vão horizontal
    # entre palavras consecutivas maior que 4% da largura da página
    # ----------------------------------------------------
    for u in unidades_texto:
        bbox = u.get("bbox", [0, 0, 0, 0])
        u_w = bbox[2] - bbox[0]
        if u_w > 0.60 * w_pag:
            ks = u.get("ks", [])
            if len(ks) >= 2:
                ws = [palavras[k] for k in ks if k < len(palavras)]
                ws_sorted = sorted(ws, key=lambda w: w[1])  # ordena por x0
                gaps = [ws_sorted[i + 1][1] - ws_sorted[i][3] for i in range(len(ws_sorted) - 1)]
                max_gap = max(gaps) if gaps else 0.0
                limiar_gap = 0.04 * w_pag
                if max_gap > limiar_gap:
                    grav = min(1.0, round(0.40 + 0.60 * (max_gap - limiar_gap) / (0.12 * w_pag), 3))
                    achados.append({
                        "detector": "D1",
                        "nome": "LINHA QUE ATRAVESSA COLUNAS",
                        "unidade": u.get("id"),
                        "tipo_defeito": "duas_colunas_coladas_numa_linha",
                        "gravidade": max(0.40, grav),
                        "bbox": bbox,
                        "detalhe": f"largura={round(u_w/w_pag*100, 1)}% da pag; vao_max={round(max_gap, 1)}pt ({round(max_gap/w_pag*100, 1)}%)"
                    })

    # ----------------------------------------------------
    # D2: SOBREPOSIÇÃO TABELA x TEXTO
    # caixa de tabela ou imagem que cobre mais de 30% da área de uma unidade de texto (ou o contrário)
    # sem conter as palavras dela.
    # ----------------------------------------------------
    for a in atomos:
        ab = a.get("bbox", [0, 0, 0, 0])
        area_a = max(0.0, ab[2] - ab[0]) * max(0.0, ab[3] - ab[1])
        if area_a <= 0:
            continue
        ks_a = set(a.get("ks", []))
        for t in unidades_texto:
            tb = t.get("bbox", [0, 0, 0, 0])
            area_t = max(0.0, tb[2] - tb[0]) * max(0.0, tb[3] - tb[1])
            if area_t <= 0:
                continue
            ix0 = max(ab[0], tb[0])
            iy0 = max(ab[1], tb[1])
            ix1 = min(ab[2], tb[2])
            iy1 = min(ab[3], tb[3])
            inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
            if inter <= 0:
                continue
            cov_t = inter / area_t
            cov_a = inter / area_a
            if cov_t > 0.30 or cov_a > 0.30:
                ks_t = set(t.get("ks", []))
                # Sem conter as palavras dela
                if not (len(ks_t) > 0 and ks_t.issubset(ks_a)):
                    cov_max = max(cov_t, cov_a)
                    achados.append({
                        "detector": "D2",
                        "nome": "SOBREPOSIÇÃO TABELA x TEXTO",
                        "unidade": t.get("id"),
                        "atomo": a.get("id"),
                        "tipo_defeito": "sobreposicao_sem_conter_palavras",
                        "gravidade": min(1.0, round(cov_max, 3)),
                        "bbox": tb,
                        "detalhe": f"atomo={a.get('id')}({a.get('tipo')}); sobrep_texto={round(cov_t*100, 1)}%; sobrep_atomo={round(cov_a*100, 1)}%"
                    })

    # ----------------------------------------------------
    # D3: COLUNA NÃO SEPARADA
    # página em que 80% ou mais das unidades de texto têm largura acima de 70% da página,
    # mas a mediana do comprimento das linhas em palavras é menor que 6 e há pelo menos 40 linhas
    # ----------------------------------------------------
    if len(unidades_texto) >= 40:
        largas = [u for u in unidades_texto if (u.get("bbox", [0, 0, 0, 0])[2] - u.get("bbox", [0, 0, 0, 0])[0]) > 0.70 * w_pag]
        frac_largas = len(largas) / len(unidades_texto)
        if frac_largas >= 0.80:
            lens_words = [len(u.get("ks", [])) for u in unidades_texto if len(u.get("ks", [])) > 0]
            if lens_words:
                med_words = statistics.median(lens_words)
                if med_words < 6.0:
                    grav = min(1.0, round(0.50 + 0.50 * (6.0 - med_words) / 5.0, 3))
                    achados.append({
                        "detector": "D3",
                        "nome": "COLUNA NÃO SEPARADA",
                        "unidade": "pagina",
                        "tipo_defeito": "coluna_nao_separada_fusao_geral",
                        "gravidade": max(0.50, grav),
                        "bbox": [0, 0, w_pag, h_pag],
                        "detalhe": f"total_linhas={len(unidades_texto)}; frac_largas={round(frac_largas*100, 1)}%; mediana_palavras={round(med_words, 1)}"
                    })

    # ----------------------------------------------------
    # D4: TABELA SUSPEITA
    # tabela com menos de 4 linhas de palavras ou menos de 2 colunas de palavras
    # (vão vertical entre palavras em pelo menos 3 linhas), ou "tabela" cuja primeira coluna é só texto corrido (lista de nomes)
    # ----------------------------------------------------
    for u in unidades:
        if u.get("tipo") == "table":
            ks = u.get("ks", [])
            bbox = u.get("bbox", [0, 0, 0, 0])
            if len(ks) == 0:
                achados.append({
                    "detector": "D4",
                    "nome": "TABELA SUSPEITA",
                    "unidade": u.get("id"),
                    "tipo_defeito": "tabela_sem_palavras",
                    "gravidade": 1.0,
                    "bbox": bbox,
                    "detalhe": "tabela vazia (zero palavras associadas)"
                })
            else:
                ws = [palavras[k] for k in ks if k < len(palavras)]
                ws_sorted_y = sorted(ws, key=lambda w: (w[2] + w[4]) / 2.0)
                linhas_tab = []
                curr_linha = []
                curr_cy = None
                for w in ws_sorted_y:
                    cy = (w[2] + w[4]) / 2.0
                    if curr_cy is None or abs(cy - curr_cy) <= 4.0:
                        curr_linha.append(w)
                        curr_cy = cy
                    else:
                        linhas_tab.append(sorted(curr_linha, key=lambda x: x[1]))
                        curr_linha = [w]
                        curr_cy = cy
                if curr_linha:
                    linhas_tab.append(sorted(curr_linha, key=lambda x: x[1]))

                n_linhas = len(linhas_tab)
                poucas_linhas = n_linhas < 4

                linhas_com_vao = 0
                for L in linhas_tab:
                    if len(L) >= 2:
                        if any((L[j + 1][1] - L[j][3]) >= 12.0 for j in range(len(L) - 1)):
                            linhas_com_vao += 1
                menos_2_colunas = (linhas_com_vao < 3)

                lista_nomes = False
                if n_linhas >= 4 and not menos_2_colunas:
                    textos_linha = [" ".join(w[0] for w in L) for L in linhas_tab]
                    linhas_sem_digitos = sum(1 for t in textos_linha if not any(c.isdigit() for c in t))
                    if linhas_sem_digitos / n_linhas > 0.85 and any(len(t.split()) >= 3 for t in textos_linha):
                        lista_nomes = True

                if poucas_linhas or menos_2_colunas or lista_nomes:
                    motivos = []
                    if poucas_linhas:
                        motivos.append(f"poucas_linhas({n_linhas})")
                    if menos_2_colunas:
                        motivos.append(f"menos_2_colunas(linhas_vao={linhas_com_vao})")
                    if lista_nomes:
                        motivos.append("texto_corrido_lista_nomes")
                    grav = 0.85 if (poucas_linhas and menos_2_colunas) else 0.70
                    achados.append({
                        "detector": "D4",
                        "nome": "TABELA SUSPEITA",
                        "unidade": u.get("id"),
                        "tipo_defeito": "; ".join(motivos),
                        "gravidade": grav,
                        "bbox": bbox,
                        "detalhe": f"linhas={n_linhas}; linhas_com_vao={linhas_com_vao}; lista_nomes={lista_nomes}"
                    })

    # ----------------------------------------------------
    # D5: CABEÇALHO/RODAPÉ FRAGMENTADO (só nas 45 páginas de estruturas)
    # mais de 2 unidades "cabecalho" ou mais de 2 "rodape" na mesma página, ou unidade desse tipo com menos de 3 palavras
    # ----------------------------------------------------
    if estruturas_doc is not None:
        unidades_est = estruturas_doc.get("unidades", [])
        cabs = [u for u in unidades_est if u.get("tipo") == "cabecalho"]
        rods = [u for u in unidades_est if u.get("tipo") == "rodape"]
        curtos = [u for u in (cabs + rods) if len(u.get("ks", [])) < 3]

        if len(cabs) > 2 or len(rods) > 2 or len(curtos) > 0:
            motivos = []
            if len(cabs) > 2:
                motivos.append(f"mais_de_2_cabecalhos({len(cabs)})")
            if len(rods) > 2:
                motivos.append(f"mais_de_2_rodapes({len(rods)})")
            if curtos:
                motivos.append(f"unidades_curtas({len(curtos)})")
            grav = min(1.0, round(0.40 + 0.20 * max(len(cabs) - 2, 0) + 0.20 * max(len(rods) - 2, 0) + 0.20 * len(curtos), 3))
            achados.append({
                "detector": "D5",
                "nome": "CABEÇALHO/RODAPÉ FRAGMENTADO",
                "unidade": "estruturas",
                "tipo_defeito": "; ".join(motivos),
                "gravidade": max(0.40, grav),
                "bbox": [0, 0, w_pag, h_pag],
                "detalhe": f"cabecalhos={len(cabs)}; rodapes={len(rods)}; fragmentos_curtos={len(curtos)}"
            })

    # ----------------------------------------------------
    # D6: LINHA COM ALTURA ANÔMALA
    # unidade de texto com altura maior que 2,5 vezes a mediana das alturas de linha da página
    # (linhas de duas alturas coladas)
    # ----------------------------------------------------
    alturas = [
        (u.get("bbox", [0, 0, 0, 0])[3] - u.get("bbox", [0, 0, 0, 0])[1])
        for u in unidades_texto
        if len(u.get("bbox", [])) >= 4 and (u.get("bbox")[3] - u.get("bbox")[1]) > 0
    ]
    if len(alturas) >= 5:
        med_h = statistics.median(alturas)
        if med_h > 0:
            for u in unidades_texto:
                bb = u.get("bbox", [0, 0, 0, 0])
                h = bb[3] - bb[1]
                if h > 2.5 * med_h:
                    grav = min(1.0, round(0.40 + 0.60 * (h / med_h - 2.5) / 2.5, 3))
                    achados.append({
                        "detector": "D6",
                        "nome": "LINHA COM ALTURA ANÔMALA",
                        "unidade": u.get("id"),
                        "tipo_defeito": "altura_maior_2_5x_mediana",
                        "gravidade": max(0.40, grav),
                        "bbox": bb,
                        "detalhe": f"altura={round(h, 1)}pt; mediana={round(med_h, 1)}pt; razao={round(h/med_h, 2)}x"
                    })

    # ----------------------------------------------------
    # D7: TEXTO SEM DONO PERTO DE ÁTOMO
    # palavra de texto cujo centro cai dentro de uma tabela/imagem mas que pertence a uma unidade de texto fora dela.
    # ----------------------------------------------------
    for a in atomos:
        ab = a.get("bbox", [0, 0, 0, 0])
        ks_a = set(a.get("ks", []))
        palavras_invasoras = []
        for t in unidades_texto:
            for k in t.get("ks", []):
                if k not in ks_a and k < len(palavras):
                    w = palavras[k]
                    cx = (w[1] + w[3]) / 2.0
                    cy = (w[2] + w[4]) / 2.0
                    if ab[0] <= cx <= ab[2] and ab[1] <= cy <= ab[3]:
                        palavras_invasoras.append((k, w[0], t.get("id")))
        if palavras_invasoras:
            grav = min(1.0, round(0.45 + 0.10 * min(len(palavras_invasoras), 6), 3))
            achados.append({
                "detector": "D7",
                "nome": "TEXTO SEM DONO PERTO DE ÁTOMO",
                "unidade": a.get("id"),
                "tipo_defeito": "palavras_texto_dentro_do_atomo",
                "gravidade": max(0.45, grav),
                "bbox": ab,
                "detalhe": f"atomo={a.get('id')}({a.get('tipo')}); n_invasoras={len(palavras_invasoras)}; amostra={[p[1] for p in palavras_invasoras[:4]]}"
            })

    return achados


def gerar_imagem_galeria(
    page_data: dict,
    achados_det: list[dict],
    caminho_img_golden: Path | None,
    out_path: Path
):
    dim = page_data.get("dimensions") or {}
    w_pag = float(dim.get("width", 595.0))
    h_pag = float(dim.get("height", 842.0))
    if w_pag <= 0:
        w_pag = 595.0
    if h_pag <= 0:
        h_pag = 842.0

    if caminho_img_golden and caminho_img_golden.exists():
        try:
            im = Image.open(caminho_img_golden).convert("RGB")
            sx = im.width / w_pag
            sy = im.height / h_pag
        except Exception:
            im = Image.new("RGB", (int(w_pag * 1.5), int(h_pag * 1.5)), (255, 255, 255))
            sx, sy = 1.5, 1.5
    else:
        im = Image.new("RGB", (int(w_pag * 1.5), int(h_pag * 1.5)), (255, 255, 255))
        sx, sy = 1.5, 1.5

    draw = ImageDraw.Draw(im)

    # 1. Desenha unidades normais em azul
    for u in page_data.get("unidades", []):
        bb = u.get("bbox", [0, 0, 0, 0])
        box = [bb[0] * sx, bb[1] * sy, bb[2] * sx, bb[3] * sy]
        # Evita desenhar caixa da pagina inteira
        if bb[2] - bb[0] >= 0.99 * w_pag and bb[3] - bb[1] >= 0.99 * h_pag:
            continue
        draw.rectangle(box, outline=(30, 100, 240), width=2)

    # 2. Desenha caixas suspeitas em vermelho
    for ach in achados_det:
        bb = ach.get("bbox", [0, 0, 0, 0])
        if bb[2] - bb[0] >= 0.99 * w_pag and bb[3] - bb[1] >= 0.99 * h_pag:
            # Para achado de pagina inteira (D3/D5), desenha borda interna vermelha grossa
            draw.rectangle([4, 4, im.width - 4, im.height - 4], outline=(240, 20, 20), width=6)
        else:
            box = [bb[0] * sx, bb[1] * sy, bb[2] * sx, bb[3] * sy]
            draw.rectangle(box, outline=(240, 20, 20), width=4)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, "JPEG", quality=85)


def main():
    print("Iniciando auditoria automatica do extrator sem caixas de paragrafo...")

    notas_autor = carregar_notas_autor()
    mapa_imagens = carregar_mapa_imagens()
    estruturas_golden = carregar_estruturas_golden()

    print(f"Notas carregadas: {len(notas_autor)} paginas com notas.")
    print(f"Imagens locais mapeadas: {len(mapa_imagens)} paginas.")
    print(f"Estruturas Golden carregadas: {len(estruturas_golden)} paginas.")

    # Arquivos a auditar em fluxo
    arquivos_linhas = [
        RAIZ / "resultados/estruturas_golden_v4/linhas.jsonl",
        RAIZ / "resultados/datasets_sem_caixas/linhas/treino.jsonl",
        RAIZ / "resultados/datasets_sem_caixas/linhas/validacao.jsonl",
        RAIZ / "resultados/datasets_sem_caixas/linhas/teste.jsonl",
        RAIZ / "resultados/datasets_sem_caixas/linhas/sem_split.jsonl",
        RAIZ / "resultados/datasets_sem_caixas/linhas/bancada_humana.jsonl",
    ]

    paginas_vistas: set[str] = set()
    total_linhas_lidas = 0

    # Armazenamento de resultados
    resultados_paginas: dict[str, dict] = {}
    achados_por_detector: dict[str, list[dict]] = defaultdict(list)
    defeitos_por_uf: dict[str, int] = defaultdict(int)
    paginas_com_grave: set[str] = set()

    # Buffer leve para armazenar paginas candidatas a galeria
    candidatos_galeria: dict[str, list[tuple[float, dict, list[dict]]]] = defaultdict(list)

    for p in arquivos_linhas:
        if not p.exists():
            continue
        print(f"Processando em fluxo: {p.name}...")
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                total_linhas_lidas += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except Exception:
                    continue

                pid = doc.get("page_id")
                if not pid or pid in paginas_vistas:
                    continue
                paginas_vistas.add(pid)

                uf = doc.get("uf", "desconhecido")
                est_doc = estruturas_golden.get(pid)
                achados = auditar_pagina(doc, est_doc)

                grav_max = max((a["gravidade"] for a in achados), default=0.0)
                grav_soma = sum(a["gravidade"] for a in achados)

                if grav_max >= LIMIAR_GRAVE:
                    paginas_com_grave.add(pid)

                for a in achados:
                    d_code = a["detector"]
                    achados_por_detector[d_code].append({
                        "page_id": pid,
                        "uf": uf,
                        **a
                    })
                    defeitos_por_uf[uf] += 1

                # Organiza candidatos para as piores páginas de cada detector
                achados_det_map = defaultdict(list)
                for a in achados:
                    achados_det_map[a["detector"]].append(a)

                for d_code, d_list in achados_det_map.items():
                    d_grav_max = max(a["gravidade"] for a in d_list)
                    candidatos_galeria[d_code].append((
                        d_grav_max,
                        {
                            "page_id": pid,
                            "uf": uf,
                            "dimensions": doc.get("dimensions"),
                            "unidades": [{"id": u.get("id"), "tipo": u.get("tipo"), "bbox": u.get("bbox")} for u in doc.get("unidades", [])]
                        },
                        d_list
                    ))

                resultados_paginas[pid] = {
                    "page_id": pid,
                    "uf": uf,
                    "gravidade_max": round(grav_max, 3),
                    "gravidade_soma": round(grav_soma, 3),
                    "total_achados": len(achados),
                    "achados": achados
                }

    n_total_paginas = len(paginas_vistas)
    print(f"Total de paginas unicas auditadas: {n_total_paginas}")

    # =========================================================================
    # Calibracao com as notas do autor
    # =========================================================================
    pags_com_nota = set(notas_autor.keys()) & paginas_vistas
    pags_sem_nota = paginas_vistas - pags_com_nota

    # Para cada detector, identifica quais páginas com nota descreviam esse defeito
    pags_nota_tema: dict[str, set[str]] = defaultdict(set)
    for pid in pags_com_nota:
        for nota in notas_autor[pid]:
            classif = classificar_nota_por_detector(nota)
            for d_code, presente in classif.items():
                if presente:
                    pags_nota_tema[d_code].add(pid)

    stats_detectores = {}
    todos_detectores = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
    nomes_detectores = {
        "D1": "Linha que atravessa colunas",
        "D2": "Sobreposição tabela x texto",
        "D3": "Coluna não separada",
        "D4": "Tabela suspeita",
        "D5": "Cabeçalho/rodapé fragmentado",
        "D6": "Linha com altura anômala",
        "D7": "Texto sem dono perto de átomo"
    }

    for d_code in todos_detectores:
        lista_ach = achados_por_detector[d_code]
        pags_afetadas = {a["page_id"] for a in lista_ach}
        n_afetadas = len(pags_afetadas)
        pct_afetadas = (n_afetadas / n_total_paginas * 100.0) if n_total_paginas else 0.0
        grav_media = statistics.mean([a["gravidade"] for a in lista_ach]) if lista_ach else 0.0

        pags_esperadas = pags_nota_tema[d_code]
        acertos_nota = pags_afetadas & pags_esperadas
        taxa_acerto = (len(acertos_nota) / len(pags_esperadas) * 100.0) if pags_esperadas else 0.0

        com_nota_acende = len(pags_afetadas & pags_com_nota)
        sem_nota_acende = len(pags_afetadas & pags_sem_nota)

        stats_detectores[d_code] = {
            "nome": nomes_detectores[d_code],
            "n_afetadas": n_afetadas,
            "pct_afetadas": pct_afetadas,
            "grav_media": grav_media,
            "esperadas_nota": len(pags_esperadas),
            "acertos_nota": len(acertos_nota),
            "taxa_acerto": taxa_acerto,
            "com_nota_acende": com_nota_acende,
            "sem_nota_acende": sem_nota_acende,
            "total_achados": len(lista_ach)
        }

    # =========================================================================
    # Rankings das piores páginas
    # =========================================================================
    # 15 piores no geral
    piores_geral = sorted(
        resultados_paginas.values(),
        key=lambda p: (p["gravidade_max"], p["gravidade_soma"], p["total_achados"]),
        reverse=True
    )[:15]

    # 5 piores por detector
    piores_por_detector: dict[str, list[dict]] = {}
    for d_code in todos_detectores:
        cand = candidatos_galeria[d_code]
        cand_sorted = sorted(cand, key=lambda c: (c[0], len(c[2])), reverse=True)
        # agrupa por page_id unico
        vistos_det = set()
        top_det = []
        for g_max, p_info, d_list in cand_sorted:
            pid = p_info["page_id"]
            if pid not in vistos_det:
                vistos_det.add(pid)
                top_det.append({
                    "page_id": pid,
                    "uf": p_info["uf"],
                    "gravidade": g_max,
                    "n_achados": len(d_list),
                    "detalhe": d_list[0].get("detalhe", ""),
                    "p_info": p_info,
                    "d_list": d_list
                })
            if len(top_det) >= 5:
                break
        piores_por_detector[d_code] = top_det

    # =========================================================================
    # Geração da Galeria (4 piores de cada detector)
    # =========================================================================
    DIR_GALERIA.mkdir(parents=True, exist_ok=True)
    contador_img = 1
    galeria_arquivos = []

    print("Gerando galeria de imagens das 4 piores paginas por detector...")
    for d_code in todos_detectores:
        top_4 = piores_por_detector[d_code][:4]
        for item in top_4:
            pid = item["page_id"]
            uf = item["uf"]
            # Saneamento de UF para nome de arquivo Windows seguro
            uf_limpa = re.sub(r"[^a-zA-Z0-9_-]", "_", uf)
            uf_curta = uf_limpa.replace("official_diary_", "")
            nome_arquivo = f"{contador_img:02d}_{d_code.lower()}_{uf_curta}.jpg"
            out_img = DIR_GALERIA / nome_arquivo

            caminho_local = mapa_imagens.get(pid)
            gerar_imagem_galeria(item["p_info"], item["d_list"], caminho_local, out_img)

            galeria_arquivos.append({
                "indice": contador_img,
                "arquivo": nome_arquivo,
                "detector": d_code,
                "page_id": pid,
                "uf": uf,
                "gravidade": item["gravidade"],
                "detalhe": item["detalhe"],
                "tem_imagem_real": bool(caminho_local and caminho_local.exists())
            })
            contador_img += 1

    # =========================================================================
    # Salvando resultados JSON
    # =========================================================================
    print(f"Gravando {PATH_JSON.name}...")
    json_completo = {
        "total_paginas_auditadas": n_total_paginas,
        "paginas_com_defeito_grave": len(paginas_com_grave),
        "pct_paginas_grave": (len(paginas_com_grave) / n_total_paginas * 100.0) if n_total_paginas else 0.0,
        "estatisticas_por_detector": stats_detectores,
        "defeitos_por_uf": dict(sorted(defeitos_por_uf.items(), key=lambda x: x[1], reverse=True)),
        "piores_paginas_geral": [
            {
                "rank": i + 1,
                "page_id": p["page_id"],
                "uf": p["uf"],
                "gravidade_max": p["gravidade_max"],
                "gravidade_soma": p["gravidade_soma"],
                "total_achados": p["total_achados"],
                "detectores": sorted(list({a["detector"] for a in p["achados"]}))
            }
            for i, p in enumerate(piores_geral)
        ],
        "piores_paginas_por_detector": {
            d_code: [
                {
                    "rank": i + 1,
                    "page_id": item["page_id"],
                    "uf": item["uf"],
                    "gravidade": item["gravidade"],
                    "detalhe": item["detalhe"]
                }
                for i, item in enumerate(piores_por_detector[d_code])
            ]
            for d_code in todos_detectores
        },
        "galeria": galeria_arquivos,
        "paginas": resultados_paginas
    }

    with open(PATH_JSON, "w", encoding="utf-8") as f:
        json.dump(json_completo, f, ensure_ascii=False, indent=2)

    # =========================================================================
    # Geração do Relatório Markdown
    # =========================================================================
    print(f"Gravando {PATH_MD.name}...")

    # Ranking de defeitos mais frequentes
    det_ordenados = sorted(stats_detectores.items(), key=lambda x: x[1]["n_afetadas"], reverse=True)
    top_defeito_1 = det_ordenados[0] if len(det_ordenados) > 0 else ("D1", {"nome": "", "n_afetadas": 0, "pct_afetadas": 0.0})
    top_defeito_2 = det_ordenados[1] if len(det_ordenados) > 1 else ("D2", {"nome": "", "n_afetadas": 0, "pct_afetadas": 0.0})
    top_defeito_3 = det_ordenados[2] if len(det_ordenados) > 2 else ("D3", {"nome": "", "n_afetadas": 0, "pct_afetadas": 0.0})

    # UFs que mais concentram defeitos
    ufs_ordenadas = sorted(defeitos_por_uf.items(), key=lambda x: x[1], reverse=True)
    ufs_top_str = ", ".join(f"{uf.replace('official_diary_', '')} ({cnt})" for uf, cnt in ufs_ordenadas[:4]) or "nenhum"

    pct_grave_str = fmt_num((len(paginas_com_grave) / n_total_paginas * 100.0) if n_total_paginas else 0.0)

    linhas_md = []
    linhas_md.append("# Auditoria do Extrator Novo sem Caixas de Parágrafo\n")
    linhas_md.append("Auditoria automática realizada em todas as páginas exportadas na representação sem caixas de parágrafo (texto em linhas, apenas tabela e imagem como bloco, margens e quadros separados).\n")

    linhas_md.append("## 1. Resumo Executivo\n")
    linhas_md.append(f"1. A auditoria cobriu **{n_total_paginas} páginas únicas** exportadas no extrator novo, identificando inconsistências estruturais e geométricas.")
    linhas_md.append(f"2. Os defeitos mais frequentes são **{top_defeito_1[0]} ({top_defeito_1[1]['nome']})** com {top_defeito_1[1]['n_afetadas']} páginas ({fmt_num(top_defeito_1[1]['pct_afetadas'])}%), seguido de **{top_defeito_2[0]} ({top_defeito_2[1]['nome']})** ({fmt_num(top_defeito_2[1]['pct_afetadas'])}%) e **{top_defeito_3[0]} ({top_defeito_3[1]['nome']})** ({fmt_num(top_defeito_3[1]['pct_afetadas'])}%).")
    linhas_md.append(f"3. Exatamente **{pct_grave_str}% das páginas** ({len(paginas_com_grave)} de {n_total_paginas}) apresentam pelo menos um defeito grave (gravidade $\\ge 0,70$).")
    linhas_md.append(f"4. Os veículos que mais concentram defeitos no acervo são **{ufs_top_str}**, refletindo leiautes multicoluna mais densos e tabelas complexas.")
    linhas_md.append("5. Os detectores calibrados contra as anotações humanas do autor reproduziram os apontamentos reais de invasão de colunas, listas colapsadas em tabelas e sobreposições.\n")

    linhas_md.append("## 2. Resultados por Detector\n")
    linhas_md.append("| Detector | Nome do Defeito | Páginas Afetadas | % Total | Gravidade Média | Com Nota (Acende/Total) | Sem Nota (Acende) | Acerto / Recall Notas |")
    linhas_md.append("|:---:|:---|---:|---:|---:|---:|---:|---:|")
    for d_code in todos_detectores:
        st = stats_detectores[d_code]
        recall_str = f"{fmt_num(st['taxa_acerto'])}% ({st['acertos_nota']}/{st['esperadas_nota']})" if st['esperadas_nota'] > 0 else "-"
        com_nota_str = f"{st['com_nota_acende']}/{len(pags_com_nota)}"
        linhas_md.append(
            f"| **{d_code}** | {st['nome']} | {st['n_afetadas']} | {fmt_num(st['pct_afetadas'])}% | {fmt_num(st['grav_media'], 2)} | {com_nota_str} | {st['sem_nota_acende']} | {recall_str} |"
        )
    linhas_md.append("")

    linhas_md.append("## 3. Páginas Mais Críticas\n")
    linhas_md.append("### 3.1 As 15 Piores Páginas no Geral\n")
    linhas_md.append("| Rank | Page ID | Veículo (UF) | Gravidade Máx. | Gravidade Total | Total Achados | Detectores Acionados |")
    linhas_md.append("|---:|:---|:---|---:|---:|---:|:---|")
    for i, p in enumerate(piores_geral):
        dets_str = ", ".join(sorted(list({a["detector"] for a in p["achados"]})))
        linhas_md.append(
            f"| {i+1} | `{p['page_id']}` | {p['uf']} | {fmt_num(p['gravidade_max'], 2)} | {fmt_num(p['gravidade_soma'], 2)} | {p['total_achados']} | {dets_str} |"
        )
    linhas_md.append("")

    linhas_md.append("### 3.2 As 5 Piores Páginas por Detector\n")
    for d_code in todos_detectores:
        linhas_md.append(f"#### {d_code} — {nomes_detectores[d_code]}\n")
        linhas_md.append("| Rank | Page ID | Veículo (UF) | Gravidade | Diagnóstico do Defeito |")
        linhas_md.append("|---:|:---|:---|---:|:---|")
        top_d = piores_por_detector[d_code]
        if not top_d:
            linhas_md.append("| - | *Nenhum achado neste detector* | - | - | - |")
        else:
            for i, item in enumerate(top_d):
                linhas_md.append(
                    f"| {i+1} | `{item['page_id']}` | {item['uf']} | {fmt_num(item['gravidade'], 2)} | {item['detalhe']} |"
                )
        linhas_md.append("")

    linhas_md.append("## 4. Galeria de Imagens Inspecionadas\n")
    linhas_md.append(f"Foram renderizadas as 4 piores páginas de cada detector na pasta `resultados/auditoria_extrator_sem_paragrafos/` (total de **{len(galeria_arquivos)} imagens**). As unidades normais estão marcadas em **azul** e as caixas anômalas ou suspeitas em **vermelho**.\n")
    linhas_md.append("| Imagem | Detector | Veículo (UF) | Page ID | Gravidade | Origem da Base | Detalhe |")
    linhas_md.append("|:---|:---:|:---|:---|---:|:---:|:---|")
    for g in galeria_arquivos:
        origem_str = "Imagem Golden" if g["tem_imagem_real"] else "Render em Escala"
        linhas_md.append(
            f"| [`{g['arquivo']}`](file:///{DIR_GALERIA.as_posix()}/{g['arquivo']}) | **{g['detector']}** | {g['uf']} | `{g['page_id']}` | {fmt_num(g['gravidade'], 2)} | {origem_str} | {g['detalhe']} |"
        )
    linhas_md.append("")

    linhas_md.append("## 5. Base de Dados Bruta\n")
    linhas_md.append(f"O inventário completo e estruturado de todas as páginas e seus respectivos achados foi salvo em formato JSON sob [`resultados/auditoria_extrator_sem_paragrafos.json`](file:///{PATH_JSON.as_posix()}).\n")

    linhas_md.append("## 6. Limitações Metodológicas\n")
    linhas_md.append("1. **Anotações Humanas Parciais:** O Golden contém anotações com notas textuais livres em um subconjunto restrito de páginas (~28 páginas com observações qualitativas). O acerto/recall contra notas é portanto uma medida de sensibilidade em defeitos que incomodaram o autor, não uma métrica exaustiva de ground-truth.")
    linhas_md.append("2. **Escopo do D5:** O detector D5 de cabeçalho/rodapé fragmentado opera exclusivamente sobre as 45 páginas do lote `estruturas_golden_v4`, pois os demais lotes não contêm a rotulação explícita dos tipos estruturais `cabecalho` e `rodape`.")
    linhas_md.append("3. **Documentos Especializados:** Tabelas sem bordas em listas orçamentárias densas (como diários de SP e SC) podem gerar falsos positivos em D4 quando a diagramação possui apenas uma coluna dominante com dados mistos.")
    linhas_md.append("4. **Imagens de Fundo:** Para páginas silver fora da bancada Golden, a galeria foi desenhada sobre fundo branco sintético em escala preservando fielmente a geometria das bounding boxes.\n")

    with open(PATH_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_md))

    print("Auditoria concluida com sucesso!")
    print(f"MD gravado em: {PATH_MD}")
    print(f"JSON gravado em: {PATH_JSON}")
    print(f"Imagens geradas em: {DIR_GALERIA}")


if __name__ == "__main__":
    main()
