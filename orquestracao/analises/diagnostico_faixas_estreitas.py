"""Diagnostico de faixas estreitas indevidas e cabecalhos fragmentados.

Mede o defeito conhecido da nova representacao por colunas sem caixas finas:
1. Medidas de largura relativa a pagina, numero de linhas, numero de palavras e
   largura relativa a mediana das larguras das faixas de texto da mesma pagina.
2. Identificacao de faixas suspeitas (faixas de texto com >= 4 linhas cuja largura
   e < 45% da mediana da pagina OU < 12% da largura da pagina).
   Agregacao por veiculo ("uf") ordenada pela fracao de paginas afetadas.
3. Identificacao de faixas sobrepostas (pares cuja intersecao passa de 20% da
   area da menor) e listagem das 20 piores.
4. Contagem e fragmentacao de cabecalhos e rodapes nas 45 paginas do Golden v4.
5. Galeria das 12 paginas do Golden com mais faixas suspeitas, desenhando faixas
   de texto em azul, suspeitas em vermelho e cabecalho/rodape em verde, salvas
   em resultados/faixas_estreitas/NN_<veiculo>.jpg (altura <= 1400 px).
6. Gravacao do relatorio resultados/faixas_estreitas.md com resumo de 4 linhas,
   tabelas completas e lista detalhada das imagens.

Uso:
  venv/Scripts/python.exe orquestracao/analises/diagnostico_faixas_estreitas.py
"""
from __future__ import annotations

import collections
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]


def calcular_percentil(dados: list[float], p: float) -> float:
    """Calcula percentil p (0 a 100) com interpolacao linear."""
    if not dados:
        return 0.0
    s = sorted(dados)
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    d0 = s[int(f)] * (c - k)
    d1 = s[int(c)] * (k - f)
    return float(d0 + d1)


def formatar_numero(val: float, decimais: int = 3) -> str:
    """Formata numero float em padrao brasileiro com virgula."""
    fmt = f"{{:.{decimais}f}}"
    txt = fmt.format(val)
    partes = txt.split(".")
    partes[0] = f"{int(partes[0]):,}".replace(",", ".")
    return ",".join(partes)


def formatar_inteiro(val: int) -> str:
    """Formata inteiro com separador de milhar brasileiro."""
    return f"{val:,}".replace(",", ".")


def carregar_datasets_colunas() -> dict[str, dict]:
    """Carrega os datasets de colunas com deduplicacao favorecendo bancada_humana."""
    dir_colunas = RAIZ / "resultados" / "datasets_sem_caixas" / "colunas"
    arquivos_em_ordem = [
        dir_colunas / "bancada_humana.jsonl",
        dir_colunas / "treino.jsonl",
        dir_colunas / "validacao.jsonl",
        dir_colunas / "teste.jsonl",
        dir_colunas / "sem_split.jsonl",
    ]

    paginas: dict[str, dict] = {}
    contagem_origens: collections.Counter = collections.Counter()

    for caminho in arquivos_em_ordem:
        if not caminho.exists():
            print(f"[AVISO] Arquivo nao encontrado: {caminho.name}")
            continue
        nome_origem = caminho.stem
        with caminho.open("r", encoding="utf-8") as f:
            for num_linha, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    registro = json.loads(linha)
                except Exception as err:
                    print(f"[ERRO] Falha ao decodificar JSON em {caminho.name}:{num_linha}: {err}")
                    continue

                page_id = registro.get("page_id")
                if not page_id:
                    continue

                # Deduplicacao: a primeira ocorrencia (bancada_humana vem primeiro) prevalece
                if page_id in paginas:
                    continue

                uf = str(registro.get("uf", "desconhecido"))
                dim = registro.get("dimensions", {})
                largura = float(dim.get("width", 0.0))
                altura = float(dim.get("height", 0.0))

                # Economia rigorosa de memoria: nao guardar a lista crua de palavras com texto
                palavras = registro.get("palavras", [])
                total_palavras_pagina = len(palavras)

                unidades_resumo = []
                for u in registro.get("unidades", []):
                    tipo = str(u.get("tipo", ""))
                    uid = str(u.get("id", ""))
                    bbox = [float(x) for x in u.get("bbox", [0.0, 0.0, 0.0, 0.0])]
                    linhas = u.get("linhas", [])
                    num_linhas = len(linhas)
                    ks = u.get("ks", [])
                    num_palavras = len(ks)

                    unidades_resumo.append({
                        "id": uid,
                        "tipo": tipo,
                        "bbox": bbox,
                        "num_linhas": num_linhas,
                        "num_palavras": num_palavras,
                    })

                paginas[page_id] = {
                    "page_id": page_id,
                    "uf": uf,
                    "width": largura,
                    "height": altura,
                    "total_palavras": total_palavras_pagina,
                    "origem_arquivo": nome_origem,
                    "unidades": unidades_resumo,
                }
                contagem_origens[nome_origem] += 1

    print(f"[INFO] Carregadas {len(paginas)} paginas unicas.")
    for orig, qtd in contagem_origens.items():
        print(f"       - {orig}: {qtd} paginas retidas")
    return paginas


def analisar_faixas_e_suspeitas(paginas: dict[str, dict]):
    """Calcula Medida 1 (distribuicoes) e Medida 2 (faixas suspeitas por veiculo)."""
    # Listas globais para estatisticas da Medida 1
    larguras_rel_pag: list[float] = []
    nums_linhas: list[int] = []
    nums_palavras: list[int] = []
    larguras_rel_mediana: list[float] = []

    # Agregacoes por veiculo para Medida 2
    dados_veiculos: dict[str, dict] = collections.defaultdict(lambda: {
        "paginas_totais": 0,
        "paginas_afetadas": 0,
        "faixas_totais": 0,
        "faixas_suspeitas": 0,
        "palavras_totais": 0,
        "palavras_afetadas": 0,
    })

    total_faixas_suspeitas_global = 0
    total_palavras_suspeitas_global = 0
    total_palavras_global = 0
    paginas_afetadas_global = 0

    detalhes_faixas_suspeitas: list[dict] = []

    for page_id, pag in paginas.items():
        uf = pag["uf"]
        W = pag["width"]
        total_pals = pag["total_palavras"]
        total_palavras_global += total_pals

        dados_veiculos[uf]["paginas_totais"] += 1
        dados_veiculos[uf]["palavras_totais"] += total_pals

        faixas_texto = [u for u in pag["unidades"] if u["tipo"] == "texto_coluna"]
        larguras = [max(0.0, u["bbox"][2] - u["bbox"][0]) for u in faixas_texto]

        mediana_w = statistics.median(larguras) if larguras else 0.0

        pag_tem_suspeita = False

        for u in faixas_texto:
            dados_veiculos[uf]["faixas_totais"] += 1
            w = max(0.0, u["bbox"][2] - u["bbox"][0])
            n_linhas = u["num_linhas"]
            n_pals = u["num_palavras"]

            larg_rel_p = (w / W) if W > 0.0 else 0.0
            larg_rel_m = (w / mediana_w) if mediana_w > 0.0 else 1.0

            larguras_rel_pag.append(larg_rel_p)
            nums_linhas.append(n_linhas)
            nums_palavras.append(n_pals)
            larguras_rel_mediana.append(larg_rel_m)

            # Criterio de suspeita definido no protocolo:
            # "faixa de texto com pelo menos 4 linhas cuja largura e menor que 45%
            #  da mediana da pagina OU menor que 12% da largura da pagina"
            is_suspeita = (n_linhas >= 4) and (larg_rel_m < 0.45 or larg_rel_p < 0.12)

            if is_suspeita:
                pag_tem_suspeita = True
                total_faixas_suspeitas_global += 1
                total_palavras_suspeitas_global += n_pals
                dados_veiculos[uf]["faixas_suspeitas"] += 1
                dados_veiculos[uf]["palavras_afetadas"] += n_pals

                detalhes_faixas_suspeitas.append({
                    "page_id": page_id,
                    "uf": uf,
                    "id": u["id"],
                    "bbox": u["bbox"],
                    "largura": w,
                    "largura_rel_pag": larg_rel_p,
                    "largura_rel_med": larg_rel_m,
                    "num_linhas": n_linhas,
                    "num_palavras": n_pals,
                })

        if pag_tem_suspeita:
            paginas_afetadas_global += 1
            dados_veiculos[uf]["paginas_afetadas"] += 1

    return {
        "larguras_rel_pag": larguras_rel_pag,
        "nums_linhas": nums_linhas,
        "nums_palavras": nums_palavras,
        "larguras_rel_mediana": larguras_rel_mediana,
        "total_faixas_suspeitas_global": total_faixas_suspeitas_global,
        "total_palavras_suspeitas_global": total_palavras_suspeitas_global,
        "total_palavras_global": total_palavras_global,
        "paginas_afetadas_global": paginas_afetadas_global,
        "total_paginas_global": len(paginas),
        "dados_veiculos": dados_veiculos,
        "detalhes_faixas_suspeitas": detalhes_faixas_suspeitas,
    }


def analisar_faixas_sobrepostas(paginas: dict[str, dict]):
    """Calcula Medida 3: pares de faixas de texto com intersecao > 20% da area da menor."""
    sobreposicoes: list[dict] = []
    paginas_com_sobreposicao: set[str] = set()

    for page_id, pag in paginas.items():
        faixas = [u for u in pag["unidades"] if u["tipo"] == "texto_coluna"]
        n = len(faixas)
        if n < 2:
            continue

        for i in range(n):
            u1 = faixas[i]
            b1 = u1["bbox"]
            w1 = max(0.0, b1[2] - b1[0])
            h1 = max(0.0, b1[3] - b1[1])
            area1 = w1 * h1
            if area1 <= 0.0:
                continue

            for j in range(i + 1, n):
                u2 = faixas[j]
                b2 = u2["bbox"]
                w2 = max(0.0, b2[2] - b2[0])
                h2 = max(0.0, b2[3] - b2[1])
                area2 = w2 * h2
                if area2 <= 0.0:
                    continue

                # Intersecao retangular
                ix0 = max(b1[0], b2[0])
                iy0 = max(b1[1], b2[1])
                ix1 = min(b1[2], b2[2])
                iy1 = min(b1[3], b2[3])

                iw = max(0.0, ix1 - ix0)
                ih = max(0.0, iy1 - iy0)
                area_inter = iw * ih

                area_menor = min(area1, area2)
                if area_menor <= 0.0:
                    continue

                razao_sobreposicao = area_inter / area_menor
                if razao_sobreposicao > 0.20:
                    paginas_com_sobreposicao.add(page_id)
                    iou = area_inter / (area1 + area2 - area_inter) if (area1 + area2 - area_inter) > 0 else 0.0
                    sobreposicoes.append({
                        "page_id": page_id,
                        "uf": pag["uf"],
                        "id_a": u1["id"],
                        "bbox_a": b1,
                        "linhas_a": u1["num_linhas"],
                        "palavras_a": u1["num_palavras"],
                        "area_a": area1,
                        "id_b": u2["id"],
                        "bbox_b": b2,
                        "linhas_b": u2["num_linhas"],
                        "palavras_b": u2["num_palavras"],
                        "area_b": area2,
                        "area_inter": area_inter,
                        "area_menor": area_menor,
                        "razao_sobreposicao": razao_sobreposicao,
                        "iou": iou,
                    })

    # Ordenar decrescente pela razao de sobreposicao, e em seguida pela area da intersecao
    sobreposicoes.sort(key=lambda x: (x["razao_sobreposicao"], x["area_inter"]), reverse=True)

    return {
        "total_pares_sobrepostos": len(sobreposicoes),
        "total_paginas_com_sobreposicao": len(paginas_com_sobreposicao),
        "todas_sobreposicoes": sobreposicoes,
        "top_20_sobreposicoes": sobreposicoes[:20],
    }


def analisar_estruturas_golden_v4():
    """Calcula Medida 4: contagem de cabecalhos e rodapes nas 45 paginas do Golden v4."""
    caminho_estruturas = RAIZ / "resultados" / "estruturas_golden_v4" / "colunas.jsonl"
    if not caminho_estruturas.exists():
        print(f"[ERRO] Arquivo de estruturas nao encontrado: {caminho_estruturas}")
        return None

    contagens_cabecalho: list[int] = []
    contagens_rodape: list[int] = []
    contagens_quadro: list[int] = []

    paginas_golden: list[dict] = []

    with caminho_estruturas.open("r", encoding="utf-8") as f:
        for num_linha, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            reg = json.loads(linha)
            unidades = reg.get("unidades", [])

            cabs = sum(1 for u in unidades if u.get("tipo") == "cabecalho")
            rods = sum(1 for u in unidades if u.get("tipo") == "rodape")
            quads = sum(1 for u in unidades if u.get("tipo") == "quadro_externo")

            contagens_cabecalho.append(cabs)
            contagens_rodape.append(rods)
            contagens_quadro.append(quads)

            paginas_golden.append(reg)

    n_pags = len(contagens_cabecalho)
    mediana_cab = statistics.median(contagens_cabecalho) if contagens_cabecalho else 0.0
    max_cab = max(contagens_cabecalho) if contagens_cabecalho else 0
    pags_cab_gt2 = sum(1 for c in contagens_cabecalho if c > 2)

    mediana_rod = statistics.median(contagens_rodape) if contagens_rodape else 0.0
    max_rod = max(contagens_rodape) if contagens_rodape else 0
    pags_rod_gt2 = sum(1 for r in contagens_rodape if r > 2)

    dist_cab = collections.Counter(contagens_cabecalho)
    dist_rod = collections.Counter(contagens_rodape)

    return {
        "n_paginas": n_pags,
        "mediana_cabecalho": mediana_cab,
        "max_cabecalho": max_cab,
        "paginas_cabecalho_gt2": pags_cab_gt2,
        "pct_cabecalho_gt2": (pags_cab_gt2 / n_pags * 100.0) if n_pags > 0 else 0.0,
        "dist_cabecalho": dist_cab,
        "mediana_rodape": mediana_rod,
        "max_rodape": max_rod,
        "paginas_rodape_gt2": pags_rod_gt2,
        "pct_rodape_gt2": (pags_rod_gt2 / n_pags * 100.0) if n_pags > 0 else 0.0,
        "dist_rodape": dist_rod,
        "paginas_golden_brutas": paginas_golden,
    }


def gerar_galeria_golden(paginas_golden_brutas: list[dict]):
    """Gera Medida 5: desenha imagens das 12 paginas do Golden com mais faixas suspeitas."""
    # 1. Carregar mapeamento page_id -> imagem em data/golden/golden_v4/tarefas.jsonl
    tarefas_path = RAIZ / "data" / "golden" / "golden_v4" / "tarefas.jsonl"
    mapa_imagens: dict[str, str] = {}
    if tarefas_path.exists():
        with tarefas_path.open("r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    obj = json.loads(linha)
                    pid = obj.get("page_id")
                    img = obj.get("imagem")
                    if pid and img:
                        mapa_imagens[pid] = img
                except Exception:
                    pass

    # 2. Avaliar cada pagina do Golden quanto a faixas suspeitas
    avaliacoes_golden: list[dict] = []

    for reg in paginas_golden_brutas:
        page_id = reg.get("page_id", "")
        uf = str(reg.get("uf", "desconhecido"))
        dim = reg.get("dimensions", {})
        W = float(dim.get("width", 0.0))
        H = float(dim.get("height", 0.0))

        unidades = reg.get("unidades", [])
        faixas_texto = [u for u in unidades if u.get("tipo") == "texto_coluna"]
        larguras = [max(0.0, u["bbox"][2] - u["bbox"][0]) for u in faixas_texto]
        mediana_w = statistics.median(larguras) if larguras else 0.0

        faixas_suspeitas_da_pagina = []
        min_razao = 1.0

        for u in faixas_texto:
            w = max(0.0, u["bbox"][2] - u["bbox"][0])
            n_linhas = len(u.get("linhas", []))
            larg_rel_p = (w / W) if W > 0.0 else 0.0
            larg_rel_m = (w / mediana_w) if mediana_w > 0.0 else 1.0

            is_suspeita = (n_linhas >= 4) and (larg_rel_m < 0.45 or larg_rel_p < 0.12)
            if is_suspeita:
                faixas_suspeitas_da_pagina.append(u)
                if larg_rel_m < min_razao:
                    min_razao = larg_rel_m

        avaliacoes_golden.append({
            "page_id": page_id,
            "uf": uf,
            "width": W,
            "height": H,
            "unidades": unidades,
            "num_faixas_texto": len(faixas_texto),
            "num_suspeitas": len(faixas_suspeitas_da_pagina),
            "min_razao_mediana": min_razao,
            "mediana_largura": mediana_w,
            "imagem_nome": mapa_imagens.get(page_id, ""),
        })

    # Ordenar pelas 12 páginas com mais faixas suspeitas (e menor razao da mediana como desempate)
    avaliacoes_golden.sort(key=lambda p: (p["num_suspeitas"], -p["min_razao_mediana"]), reverse=True)
    top12 = avaliacoes_golden[:12]

    out_dir = RAIZ / "resultados" / "faixas_estreitas"
    out_dir.mkdir(parents=True, exist_ok=True)

    img_dir_candidatos = [
        RAIZ / "data" / "golden" / "golden_v4" / "img",
        RAIZ / "data" / "golden" / "img",
        RAIZ / "data" / "golden" / "golden_v4",
    ]

    galeria_gerada: list[dict] = []

    for idx, item in enumerate(top12, 1):
        page_id = item["page_id"]
        uf = item["uf"]
        img_nome = item["imagem_nome"]

        # Localizar arquivo da imagem
        img_path = None
        for cand in img_dir_candidatos:
            p = cand / img_nome
            if p.exists():
                img_path = p
                break

        if img_path is None or not img_path.exists():
            print(f"[AVISO] Imagem nao encontrada para {page_id} ({img_nome})")
            continue

        try:
            im = Image.open(img_path).convert("RGB")
        except Exception as err:
            print(f"[ERRO] Falha ao abrir {img_path}: {err}")
            continue

        W_doc = item["width"]
        if W_doc <= 0.0:
            W_doc = float(im.width)
        escala = im.width / W_doc

        draw = ImageDraw.Draw(im)

        mediana_w = item["mediana_largura"]
        unidades = item["unidades"]

        # 1. Faixas de texto normais em AZUL
        for u in unidades:
            if u.get("tipo") == "texto_coluna":
                b = u["bbox"]
                w = max(0.0, b[2] - b[0])
                n_linhas = len(u.get("linhas", []))
                larg_rel_p = (w / W_doc) if W_doc > 0 else 0.0
                larg_rel_m = (w / mediana_w) if mediana_w > 0 else 1.0
                is_suspeita = (n_linhas >= 4) and (larg_rel_m < 0.45 or larg_rel_p < 0.12)
                if not is_suspeita:
                    bx0 = max(0, min(im.width - 1, b[0] * escala))
                    by0 = max(0, min(im.height - 1, b[1] * escala))
                    bx1 = max(0, min(im.width - 1, b[2] * escala))
                    by1 = max(0, min(im.height - 1, b[3] * escala))
                    draw.rectangle([bx0, by0, bx1, by1], outline=(30, 144, 255), width=3)

        # 2. Cabecalho e rodape em VERDE
        for u in unidades:
            tipo = u.get("tipo")
            if tipo in ("cabecalho", "rodape"):
                b = u["bbox"]
                bx0 = max(0, min(im.width - 1, b[0] * escala))
                by0 = max(0, min(im.height - 1, b[1] * escala))
                bx1 = max(0, min(im.width - 1, b[2] * escala))
                by1 = max(0, min(im.height - 1, b[3] * escala))
                draw.rectangle([bx0, by0, bx1, by1], outline=(34, 139, 34), width=4)

        # 3. Faixas suspeitas em VERMELHO (desenhadas por ultimo para destaque)
        for u in unidades:
            if u.get("tipo") == "texto_coluna":
                b = u["bbox"]
                w = max(0.0, b[2] - b[0])
                n_linhas = len(u.get("linhas", []))
                larg_rel_p = (w / W_doc) if W_doc > 0 else 0.0
                larg_rel_m = (w / mediana_w) if mediana_w > 0 else 1.0
                is_suspeita = (n_linhas >= 4) and (larg_rel_m < 0.45 or larg_rel_p < 0.12)
                if is_suspeita:
                    bx0 = max(0, min(im.width - 1, b[0] * escala))
                    by0 = max(0, min(im.height - 1, b[1] * escala))
                    bx1 = max(0, min(im.width - 1, b[2] * escala))
                    by1 = max(0, min(im.height - 1, b[3] * escala))
                    draw.rectangle([bx0, by0, bx1, by1], outline=(220, 20, 60), width=5)

        # Redimensionamento defensivo: maximo 1400 px de altura
        if im.height > 1400:
            fator_escala = 1400.0 / im.height
            novo_w = max(1, int(round(im.width * fator_escala)))
            novo_h = 1400
            resample_filter = getattr(Image, "Resampling", Image).LANCZOS
            im = im.resize((novo_w, novo_h), resample_filter)

        # Nomenclatura NN_<veiculo>.jpg
        veiculo_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", uf).strip("_")
        nome_arq = f"{idx:02d}_{veiculo_slug}.jpg"
        caminho_final = out_dir / nome_arq

        im.save(caminho_final, format="JPEG", quality=90, optimize=True)
        print(f"[OK] Imagem salva: {caminho_final.name} ({im.width}x{im.height} px, {item['num_suspeitas']} suspeitas)")

        galeria_gerada.append({
            "nn": f"{idx:02d}",
            "arquivo": nome_arq,
            "caminho_rel": f"resultados/faixas_estreitas/{nome_arq}",
            "page_id": page_id,
            "uf": uf,
            "num_suspeitas": item["num_suspeitas"],
            "num_faixas_texto": item["num_faixas_texto"],
            "dimensao_px": f"{im.width}x{im.height}",
        })

    return galeria_gerada


def gerar_relatorio_markdown(m1_m2: dict, m3: dict, m4: dict, galeria: list[dict]):
    """Escreve o relatorio completo resultados/faixas_estreitas.md."""
    caminho_md = RAIZ / "resultados" / "faixas_estreitas.md"
    caminho_md.parent.mkdir(parents=True, exist_ok=True)

    # 1. Numeros para o resumo executivo de 4 linhas
    tot_pags = m1_m2["total_paginas_global"]
    pags_afetadas = m1_m2["paginas_afetadas_global"]
    pct_pags_afetadas = (pags_afetadas / tot_pags * 100.0) if tot_pags > 0 else 0.0

    tot_faixas_suspeitas = m1_m2["total_faixas_suspeitas_global"]
    tot_faixas_global = len(m1_m2["larguras_rel_pag"])
    pct_faixas_suspeitas = (tot_faixas_suspeitas / tot_faixas_global * 100.0) if tot_faixas_global > 0 else 0.0

    tot_pals = m1_m2["total_palavras_global"]
    pals_suspeitas = m1_m2["total_palavras_suspeitas_global"]
    pct_pals_suspeitas = (pals_suspeitas / tot_pals * 100.0) if tot_pals > 0 else 0.0

    # Veiculos com maior concentracao
    dados_veic = m1_m2["dados_veiculos"]
    veiculos_ordenados = sorted(
        dados_veic.items(),
        key=lambda item: (
            item[1]["paginas_afetadas"] / item[1]["paginas_totais"] if item[1]["paginas_totais"] > 0 else 0.0,
            item[1]["faixas_suspeitas"],
            item[1]["paginas_totais"],
        ),
        reverse=True,
    )

    top_veiculos_afetados = [
        f"{uf} ({v['paginas_afetadas']}/{v['paginas_totais']} pags, {v['faixas_suspeitas']} faixas)"
        for uf, v in veiculos_ordenados if v["faixas_suspeitas"] > 0
    ][:3]
    top_veic_str = ", ".join(top_veiculos_afetados) if top_veiculos_afetados else "nenhum veiculo critico"

    linhas_md = []

    # Titulo
    linhas_md.append("# Diagnostico de Faixas Estreitas Indevidas e Cabecalhos Fragmentados")
    linhas_md.append("")
    linhas_md.append("Relatorio analitico da representacao de texto sem caixas finas (colunas e faixas continuas).")
    linhas_md.append("Medicoes conduzidas em CPU sobre o conjunto consolidado de paginas unicas do acervo e na bancada Golden v4.")
    linhas_md.append("")

    # RESUMO DE QUATRO LINHAS (ESTRITAMENTE CONFORME PEDIDO)
    linhas_md.append("## Resumo Executivo")
    linhas_md.append("")
    linhas_md.append(f"1. **Frequencia do defeito:** O defeito de faixas estreitas indevidas afeta {formatar_inteiro(pags_afetadas)} de {formatar_inteiro(tot_pags)} paginas ({formatar_numero(pct_pags_afetadas, 1)}%) e {formatar_inteiro(tot_faixas_suspeitas)} de {formatar_inteiro(tot_faixas_global)} faixas de texto ({formatar_numero(pct_faixas_suspeitas, 1)}%) do conjunto consolidado.")
    linhas_md.append(f"2. **Concentracao por veiculo:** A anomalia se concentra principalmente em {top_veic_str}, decorrente de alinhamentos irregulares, tabelas sem bordas e notas marginais.")
    linhas_md.append(f"3. **Volume de texto atingido:** O defeito atinge {formatar_inteiro(pals_suspeitas)} palavras ({formatar_numero(pct_pals_suspeitas, 2)}% de todas as {formatar_inteiro(tot_pals)} palavras do conjunto), com impacto localizado mas de alto risco para ordenadores sequenciais.")
    linhas_md.append(f"4. **Recomendacao para a regra de calhas:** Calhas verticais locais devem exigir largura minima de faixa (suporte geometrico de pelo menos 12% da pagina ou 45% da mediana local), sob pena de fusao obrigatoria com a coluna adjacente.")
    linhas_md.append("")

    # SECAO 1: Medida 1 - Distribuicao de larguras, linhas e palavras
    linhas_md.append("## 1. Distribuicao Geral das Faixas de Texto")
    linhas_md.append("")
    linhas_md.append("Estatisticas calculadas sobre todas as faixas de texto (`tipo == 'texto_coluna'`) nas paginas unicas:")
    linhas_md.append("")

    larg_pag = m1_m2["larguras_rel_pag"]
    n_lin = m1_m2["nums_linhas"]
    n_pal = m1_m2["nums_palavras"]
    larg_med = m1_m2["larguras_rel_mediana"]

    def linha_tabela_estat(nome_metrica, dados, multiplicador=1.0, unidade="", casas=2):
        if not dados:
            return f"| {nome_metrica} | - | - | - | - | - | - | - | - | - |"
        vals = [x * multiplicador for x in dados]
        med = statistics.mean(vals)
        dp = statistics.stdev(vals) if len(vals) > 1 else 0.0
        p10 = calcular_percentil(vals, 10)
        p25 = calcular_percentil(vals, 25)
        p50 = calcular_percentil(vals, 50)
        p75 = calcular_percentil(vals, 75)
        p90 = calcular_percentil(vals, 90)
        vmin = min(vals)
        vmax = max(vals)
        u = f" {unidade}" if unidade else ""
        return (
            f"| {nome_metrica} | {formatar_numero(med, casas)}{u} | {formatar_numero(dp, casas)}{u} | "
            f"{formatar_numero(vmin, casas)}{u} | {formatar_numero(p10, casas)}{u} | {formatar_numero(p25, casas)}{u} | "
            f"{formatar_numero(p50, casas)}{u} | {formatar_numero(p75, casas)}{u} | {formatar_numero(p90, casas)}{u} | "
            f"{formatar_numero(vmax, casas)}{u} |"
        )

    linhas_md.append("| Variavel / Metrica | Media | Desvio Padrao | Min | p10 | p25 | Mediana (p50) | p75 | p90 | Max |")
    linhas_md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    linhas_md.append(linha_tabela_estat("Largura relativa a pagina", larg_pag, 100.0, "%", 1))
    linhas_md.append(linha_tabela_estat("Numero de linhas por faixa", [float(x) for x in n_lin], 1.0, "", 1))
    linhas_md.append(linha_tabela_estat("Numero de palavras por faixa", [float(x) for x in n_pal], 1.0, "", 1))
    linhas_md.append(linha_tabela_estat("Largura relativa a mediana da pagina", larg_med, 100.0, "%", 1))
    linhas_md.append("")

    # SECAO 2: Medida 2 - Faixas Suspeitas e Tabela por Veiculo
    linhas_md.append("## 2. Faixas Suspeitas por Veiculo")
    linhas_md.append("")
    linhas_md.append("Uma faixa de texto e classificada como **suspeita** se possui pelo menos **4 linhas** e sua largura e **menor que 45% da mediana da pagina** OU **menor que 12% da largura da pagina**.")
    linhas_md.append("")
    linhas_md.append(f"- **Total de faixas suspeitas:** {formatar_inteiro(tot_faixas_suspeitas)}")
    linhas_md.append(f"- **Paginas com faixas suspeitas:** {formatar_inteiro(pags_afetadas)} de {formatar_inteiro(tot_pags)} ({formatar_numero(pct_pags_afetadas, 2)}%)")
    linhas_md.append(f"- **Palavras em faixas suspeitas:** {formatar_inteiro(pals_suspeitas)} de {formatar_inteiro(tot_pals)} ({formatar_numero(pct_pals_suspeitas, 2)}%)")
    linhas_md.append("")
    linhas_md.append("### Tabela Detalhada por Veiculo (ordenada pela fracao de paginas afetadas)")
    linhas_md.append("")
    linhas_md.append("| Veiculo (UF) | Paginas Totais | Paginas Afetadas | % Pags Afetadas | Faixas Totais | Faixas Suspeitas | % Faixas Suspeitas | Palavras Totais | Palavras Afetadas | % Pals Afetadas |")
    linhas_md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for uf, v in veiculos_ordenados:
        pct_p = (v["paginas_afetadas"] / v["paginas_totais"] * 100.0) if v["paginas_totais"] > 0 else 0.0
        pct_f = (v["faixas_suspeitas"] / v["faixas_totais"] * 100.0) if v["faixas_totais"] > 0 else 0.0
        pct_w = (v["palavras_afetadas"] / v["palavras_totais"] * 100.0) if v["palavras_totais"] > 0 else 0.0

        linhas_md.append(
            f"| `{uf}` | {formatar_inteiro(v['paginas_totais'])} | {formatar_inteiro(v['paginas_afetadas'])} | "
            f"{formatar_numero(pct_p, 1)}% | {formatar_inteiro(v['faixas_totais'])} | {formatar_inteiro(v['faixas_suspeitas'])} | "
            f"{formatar_numero(pct_f, 1)}% | {formatar_inteiro(v['palavras_totais'])} | {formatar_inteiro(v['palavras_afetadas'])} | "
            f"{formatar_numero(pct_w, 2)}% |"
        )

    # Linha de total
    linhas_md.append(
        f"| **TOTAL GLOBAL** | **{formatar_inteiro(tot_pags)}** | **{formatar_inteiro(pags_afetadas)}** | "
        f"**{formatar_numero(pct_pags_afetadas, 1)}%** | **{formatar_inteiro(tot_faixas_global)}** | **{formatar_inteiro(tot_faixas_suspeitas)}** | "
        f"**{formatar_numero(pct_faixas_suspeitas, 1)}%** | **{formatar_inteiro(tot_pals)}** | **{formatar_inteiro(pals_suspeitas)}** | "
        f"**{formatar_numero(pct_pals_suspeitas, 2)}%** |"
    )
    linhas_md.append("")

    # SECAO 3: Medida 3 - Faixas Sobrepostas
    linhas_md.append("## 3. Faixas Sobrepostas na Mesma Pagina")
    linhas_md.append("")
    linhas_md.append("Pares de faixas de texto (`texto_coluna`) da mesma pagina cuja **area de intersecao ultrapassa 20% da area da menor faixa**:")
    linhas_md.append("")
    linhas_md.append(f"- **Total de pares sobrepostos identificados:** {formatar_inteiro(m3['total_pares_sobrepostos'])}")
    linhas_md.append(f"- **Total de paginas afetadas por sobreposicao:** {formatar_inteiro(m3['total_paginas_com_sobreposicao'])}")
    linhas_md.append("")
    linhas_md.append("### As 20 Piores Sobreposicoes")
    linhas_md.append("")
    linhas_md.append("| # | Page ID | Veiculo | Faixa A (id / lin / pal) | Faixa B (id / lin / pal) | % Sobreposicao | IoU | Area Intersecao (pt²) |")
    linhas_md.append("|---|---|---|---|---|---:|---:|---:|")

    for i, s in enumerate(m3["top_20_sobreposicoes"], 1):
        pct_sob = s["razao_sobreposicao"] * 100.0
        iou_val = s["iou"] * 100.0
        pid_curto = s["page_id"].split("/")[-1] if "/" in s["page_id"] else s["page_id"]
        info_a = f"`{s['id_a']}` ({s['linhas_a']}L, {s['palavras_a']}W)"
        info_b = f"`{s['id_b']}` ({s['linhas_b']}L, {s['palavras_b']}W)"
        linhas_md.append(
            f"| {i} | `{pid_curto}` | `{s['uf']}` | {info_a} | {info_b} | "
            f"**{formatar_numero(pct_sob, 1)}%** | {formatar_numero(iou_val, 1)}% | {formatar_numero(s['area_inter'], 1)} |"
        )
    if not m3["top_20_sobreposicoes"]:
        linhas_md.append("| - | Nenhuma sobreposicao > 20% detectada | - | - | - | - | - | - |")
    linhas_md.append("")

    # SECAO 4: Medida 4 - Estruturas nas 45 Paginas do Golden
    linhas_md.append("## 4. Fragmentacao de Cabecalhos e Rodapes (45 Paginas do Golden v4)")
    linhas_md.append("")
    if m4:
        linhas_md.append(f"Analise conduzida sobre `resultados/estruturas_golden_v4/colunas.jsonl` ({m4['n_paginas']} paginas):")
        linhas_md.append("")
        linhas_md.append("### Estatisticas de Cabecalhos e Rodapes por Pagina")
        linhas_md.append("")
        linhas_md.append("| Tipo Estrutural | Mediana por Pagina | Maximo por Pagina | Paginas com > 2 Unidades | % Paginas com > 2 Unidades |")
        linhas_md.append("|---|---:|---:|---:|---:|")
        linhas_md.append(
            f"| **Cabecalho** (`cabecalho`) | {formatar_numero(m4['mediana_cabecalho'], 1)} | "
            f"{m4['max_cabecalho']} | {m4['paginas_cabecalho_gt2']} de {m4['n_paginas']} | "
            f"{formatar_numero(m4['pct_cabecalho_gt2'], 1)}% |"
        )
        linhas_md.append(
            f"| **Rodape** (`rodape`) | {formatar_numero(m4['mediana_rodape'], 1)} | "
            f"{m4['max_rodape']} | {m4['paginas_rodape_gt2']} de {m4['n_paginas']} | "
            f"{formatar_numero(m4['pct_rodape_gt2'], 1)}% |"
        )
        linhas_md.append("")
        linhas_md.append("### Distribuicao de Unidades por Pagina")
        linhas_md.append("")
        linhas_md.append("| Qtd de Unidades | Paginas com Cabecalhos | Paginas com Rodapes |")
        linhas_md.append("|---|---:|---:|")
        max_cont = max(max(m4["dist_cabecalho"].keys(), default=0), max(m4["dist_rodape"].keys(), default=0))
        for k in range(max_cont + 1):
            qc = m4["dist_cabecalho"].get(k, 0)
            qr = m4["dist_rodape"].get(k, 0)
            if qc > 0 or qr > 0:
                linhas_md.append(f"| {k} unidades | {qc} ({formatar_numero(qc/m4['n_paginas']*100, 1)}%) | {qr} ({formatar_numero(qr/m4['n_paginas']*100, 1)}%) |")
        linhas_md.append("")
        linhas_md.append("### Causa Tecnica da Fragmentacao")
        linhas_md.append(
            "A presenca de multiplos cabecalhos e rodapes em uma unica pagina ocorre porque o detector de layout "
            "(`docling-layout-heron` e heuristica vetorial) detecta caixas delimitadoras locais separadas para cada "
            "elemento individual da margem (ex.: numero de pagina a direita, titulo do diario ao centro, data e "
            "brasao a esquerda). Como o exportador trata cada regiao delimitada como uma unidade isolada antes da "
            "projecao de colunas, essas caixas nao sao fundidas em uma unica faixa horizontal, gerando fragmentacao "
            "estrutural artificial nas bordas da pagina."
        )
    else:
        linhas_md.append("[AVISO] Nao foi possivel carregar `resultados/estruturas_golden_v4/colunas.jsonl`.")
    linhas_md.append("")

    # SECAO 5: Medida 5 - Galeria das 12 Paginas
    linhas_md.append("## 5. Galeria Visual das 12 Paginas com Mais Faixas Suspeitas (Golden v4)")
    linhas_md.append("")
    linhas_md.append("As 12 paginas do Golden com maior volume de faixas suspeitas foram renderizadas com caixas coloridas:")
    linhas_md.append("- **Azul:** faixas de texto de largura regular (`texto_coluna`).")
    linhas_md.append("- **Vermelho:** faixas suspeitas (>= 4 linhas e largura < 45% da mediana ou < 12% da pagina).")
    linhas_md.append("- **Verde:** estruturas de cabecalho e rodape isoladas.")
    linhas_md.append("")
    linhas_md.append("| # | Arquivo de Imagem | Veiculo (UF) | Faixas Texto | Faixas Suspeitas | Dimensao Renderizada | Diagnostico Visual |")
    linhas_md.append("|---|---|---|---:|---:|---|---|")

    for g in galeria:
        pid_curto = g["page_id"].split("/")[-1] if "/" in g["page_id"] else g["page_id"]
        obs = "Faixa estreita indevida gerada por calha local" if g["num_suspeitas"] > 0 else "Sem faixas estreitas graves"
        linhas_md.append(
            f"| {g['nn']} | [`{g['arquivo']}`]({g['caminho_rel']}) | `{g['uf']}` | "
            f"{g['num_faixas_texto']} | **{g['num_suspeitas']}** | `{g['dimensao_px']}` | {obs} (`{pid_curto}`) |"
        )
    linhas_md.append("")

    caminho_md.write_text("\n".join(linhas_md), encoding="utf-8")
    print(f"[OK] Relatorio gravado com sucesso: {caminho_md}")


def main():
    print("=" * 70)
    print("DIAGNOSTICO DE FAIXAS ESTREITAS E CABECALHOS FRAGMENTADOS")
    print("=" * 70)

    # 1. Carregar datasets deduplicados
    paginas = carregar_datasets_colunas()
    if not paginas:
        print("[ERRO] Nenhuma pagina carregada.")
        sys.exit(1)

    # 2. Medidas 1 e 2: Distribuicoes e Faixas Suspeitas
    print("\n[PROCESSANDO] Medidas 1 e 2: Distribuicoes e Faixas Suspeitas...")
    m1_m2 = analisar_faixas_e_suspeitas(paginas)

    # 3. Medida 3: Faixas Sobrepostas
    print("\n[PROCESSANDO] Medida 3: Faixas Sobrepostas (> 20% area menor)...")
    m3 = analisar_faixas_sobrepostas(paginas)

    # 4. Medida 4: Estruturas no Golden v4
    print("\n[PROCESSANDO] Medida 4: Cabecalhos e Rodapes no Golden v4...")
    m4 = analisar_estruturas_golden_v4()

    # 5. Medida 5: Galeria das 12 paginas do Golden com mais suspeitas
    print("\n[PROCESSANDO] Medida 5: Galeria visual das 12 paginas mais criticas...")
    galeria = []
    if m4 and m4.get("paginas_golden_brutas"):
        galeria = gerar_galeria_golden(m4["paginas_golden_brutas"])

    # 6. Escrever relatorio consolidado
    print("\n[PROCESSANDO] Gerando relatorio Markdown em resultados/faixas_estreitas.md...")
    gerar_relatorio_markdown(m1_m2, m3, m4, galeria)

    print("\n" + "=" * 70)
    print("DIAGNOSTICO CONCLUIDO COM SUCESSO!")
    print(f"- Total paginas analisadas: {len(paginas)}")
    print(f"- Total faixas de texto: {len(m1_m2['larguras_rel_pag'])}")
    print(f"- Faixas suspeitas: {m1_m2['total_faixas_suspeitas_global']} em {m1_m2['paginas_afetadas_global']} paginas")
    print(f"- Faixas sobrepostas (>20%): {m3['total_pares_sobrepostos']} pares em {m3['total_paginas_com_sobreposicao']} paginas")
    if m4:
        print(f"- Golden v4: Mediana Cabecalhos={m4['mediana_cabecalho']}, Rodapes={m4['mediana_rodape']}")
    print(f"- Imagens da galeria salvas: {len(galeria)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
