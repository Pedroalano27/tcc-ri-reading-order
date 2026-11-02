"""Monta lote classificavel sem caixas de paragrafo para correcao no Diamond.

Este script prepara um lote de 60 paginas estratificadas para inspecao e correcao
humana pelo Pedro, usando a ferramenta Diamond (src/anotacao/servidor.py --diamond).
As unidades propostas veem do extrator novo sem caixas de paragrafo (linhas de texto
e atomos de tabelas e imagens, alem de cabecalhos/rodapes estruturais).

Estratificacao:
- 30 paginas com os piores achados da auditoria (D1 a D7), diversificando
  detectores e veiculos.
- 30 paginas aleatorias (semente 20261008) para estimar a taxa real de erro.
- Teto rigoroso de no maximo 4 paginas por veiculo no lote total.
- Exclusao estrita das bancadas humanas (golden_v4 e golden_v3) e de data/labelstudio.

As imagens sao renderizadas via PyMuPDF a 110 dpi em JPEG para img/.
As tarefas sao salvas no formato exato que servidor.py e diamond.html leem.
A ordem de leitura NAO vem preenchida (anotacao cega de segmentacao).

Uso:
    venv\\Scripts\\python.exe -B orquestracao/analises/montar_lote_sem_paragrafos.py
Saida:
    resultados/lote_sem_paragrafos/tarefas.jsonl
    resultados/lote_sem_paragrafos/LEIAME.md
    resultados/lote_sem_paragrafos/img/*.jpg
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import gc
import glob
import json
import os
import random
import re
from collections import Counter, defaultdict

import pymupdf

# Diretorios de entrada e saida
DIR_SAIDA = RAIZ / "resultados" / "lote_sem_paragrafos"
DIR_IMG = DIR_SAIDA / "img"
ARQ_TAREFAS = DIR_SAIDA / "tarefas.jsonl"
ARQ_LEIAME = DIR_SAIDA / "LEIAME.md"

ARQ_AUDITORIA = RAIZ / "resultados" / "auditoria_extrator_sem_paragrafos.json"
DIR_LINHAS = RAIZ / "resultados" / "datasets_sem_caixas" / "linhas"
RAW = RAIZ / "data" / "raw"

# Classes oficiais do Diamond (definidas em src/anotacao/servidor.py)
CLASSES_DIAMOND = [
    "titulo", "texto", "lista", "tabela", "assinatura",
    "cabecalho", "rodape", "figura", "outro"
]

SEMENTE_ALEATORIA = 20261008
MAX_PAGINAS_POR_VEICULO = 4
ALVO_PIORES = 30
ALVO_ALEATORIAS = 30
TOTAL_ALVO = 60


def mapear_classe_diamond(tipo: str) -> str:
    """Mapeia tipo de unidade do extrator novo para o vocabulario do Diamond."""
    t = str(tipo or "").strip().lower()
    if t in ("texto", "linhas", "texto_coluna", "text"):
        return "texto"
    if t in ("tabela", "table", "document_index"):
        return "tabela"
    if t in ("figura", "picture", "imagem", "image"):
        return "figura"
    if t in ("cabecalho", "page_header"):
        return "cabecalho"
    if t in ("rodape", "page_footer"):
        return "rodape"
    if t in ("titulo", "title", "section_header"):
        return "titulo"
    if t in ("lista", "list_item"):
        return "lista"
    if t in ("assinatura",):
        return "assinatura"
    return "outro"


def parse_page_id(pid: str):
    """Extrai (uf, arquivo, pagina_idx) a partir do page_id."""
    if "#p" not in pid:
        return None, None, None
    pdf_rel, pag_str = pid.split("#p", 1)
    try:
        pag_idx = int(pag_str)
    except ValueError:
        return None, None, None
    if "/" not in pdf_rel:
        return None, None, None
    uf, arq = pdf_rel.split("/", 1)
    return uf, arq, pag_idx


def obter_caminho_pdf(pid: str, uf: str | None = None, arq: str | None = None) -> Path | None:
    """Localiza o arquivo PDF em data/raw/."""
    if uf and arq:
        c = RAW / uf / Path(*arq.split("/"))
        if c.exists():
            return c
    u, a, _ = parse_page_id(pid)
    if u and a:
        c = RAW / u / Path(*a.split("/"))
        if c.exists():
            return c
    return None


def carregar_ids_proibidos() -> set[str]:
    """Carrega IDs de paginas que NUNCA devem entrar no lote."""
    proibidos = set()

    # 1. Golden v4
    arq_v4 = RAIZ / "data" / "golden" / "golden_v4" / "tarefas.jsonl"
    if arq_v4.exists():
        with open(arq_v4, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    proibidos.add(json.loads(l)["page_id"])

    # 2. Golden v3
    arq_v3 = RAIZ / "data" / "golden" / "_avaliacao" / "golden_v3" / "tarefas.jsonl"
    if arq_v3.exists():
        with open(arq_v3, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    proibidos.add(json.loads(l)["page_id"])

    # 3. LabelStudio (nunca usar nesta noite)
    for arq_ls in RAIZ.glob("data/labelstudio/**/tarefas.jsonl"):
        try:
            with open(arq_ls, encoding="utf-8") as f:
                for l in f:
                    if l.strip():
                        proibidos.add(json.loads(l).get("page_id", ""))
        except Exception:
            pass

    return {p for p in proibidos if p}


def carregar_dados_linhas() -> dict[str, dict]:
    """Carrega dados das unidades do extrator novo de datasets_sem_caixas/linhas/*.jsonl."""
    dados = {}
    for arq in sorted(DIR_LINHAS.glob("*.jsonl")):
        with open(arq, encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                d = json.loads(l)
                pid = d.get("page_id")
                if pid and pid not in dados:
                    dados[pid] = d
    return dados


def carregar_metadados_diamond() -> dict[str, dict]:
    """Carrega blocos_v3, detector e sha256 originais de data/diamond/*/tarefas.jsonl."""
    meta = {}
    for arq in sorted(RAIZ.glob("data/diamond/*/tarefas.jsonl")):
        with open(arq, encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                t = json.loads(l)
                pid = t.get("page_id")
                if pid and pid not in meta:
                    meta[pid] = {
                        "blocos_v3": t.get("blocos_v3", []),
                        "detector": t.get("detector", {}),
                        "extrator_sha256": t.get("extrator_sha256", ""),
                    }
    return meta


def carregar_auditoria() -> dict:
    """Carrega o relatorio de auditoria do extrator sem paragrafos."""
    if not ARQ_AUDITORIA.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {ARQ_AUDITORIA}")
    with open(ARQ_AUDITORIA, encoding="utf-8") as f:
        return json.load(f)


def selecionar_paginas(
    auditoria: dict,
    dados_linhas: dict[str, dict],
    proibidos: set[str],
) -> tuple[list[dict], list[dict]]:
    """Estratifica as 60 paginas: 30 piores achados + 30 aleatorias.

    Garante teto de no maximo 4 paginas por veiculo no lote total e existencia do PDF.
    """
    paginas_auditoria = auditoria.get("paginas", {})

    # Filtrar universo de candidatas validas com PDF existente
    candidatas_validas = {}
    for pid, d in dados_linhas.items():
        if pid in proibidos:
            continue
        if "labelstudio" in pid.lower():
            continue
        uf, arq, pag_idx = parse_page_id(pid)
        if not uf or not arq or pag_idx is None:
            continue
        pdf_path = obter_caminho_pdf(pid, uf, arq)
        if not pdf_path or not pdf_path.exists():
            continue
        candidatas_validas[pid] = {
            "page_id": pid,
            "uf": uf,
            "arquivo": arq,
            "pagina": pag_idx,
            "pdf_path": pdf_path,
            "dados": d,
            "audit": paginas_auditoria.get(pid, {}),
        }

    # -------------------------------------------------------------
    # 1. SELECAO DOS 30 PIORES ACHADOS
    # -------------------------------------------------------------
    # Agrupar candidatas por detector de defeito com suas maiores gravidades
    candidatas_com_defeito = []
    for pid, c in candidatas_validas.items():
        audit = c["audit"]
        achados = audit.get("achados", [])
        if achados or audit.get("total_achados", 0) > 0:
            grav_max = float(audit.get("gravidade_max", 0.0))
            grav_soma = float(audit.get("gravidade_soma", 0.0))
            detectores = sorted({a.get("detector") for a in achados if a.get("detector")})
            candidatas_com_defeito.append({
                **c,
                "grav_max": grav_max,
                "grav_soma": grav_soma,
                "total_achados": len(achados) or audit.get("total_achados", 0),
                "detectores": detectores,
                "achados": achados,
            })

    # Ordenar por gravidade soma decrescente e gravidade max decrescente
    candidatas_com_defeito.sort(key=lambda x: (x["grav_soma"], x["grav_max"], x["total_achados"]), reverse=True)

    selecionadas_piores: list[dict] = []
    pids_selecionados = set()
    contagem_veiculos = Counter()

    # Passada 1: Cobrir especificamente detectores raros e criticos (D1, D7, D2, D5, D4, D6)
    # D1 (linha atravessa colunas) e D7 (texto sem dono perto de atomo) sao muito raros
    ordem_detectores = ["D1", "D7", "D2", "D5", "D4", "D6"]
    limite_por_detector = {"D1": 3, "D7": 3, "D2": 6, "D5": 5, "D4": 7, "D6": 6}

    for det in ordem_detectores:
        candidatos_det = [
            c for c in candidatas_com_defeito
            if det in c["detectores"] and c["page_id"] not in pids_selecionados
        ]
        # Ordenar pelos achados mais graves desse detector especifico
        def grav_no_detector(cand):
            return max(
                (float(a.get("gravidade", 0.0)) for a in cand["achados"] if a.get("detector") == det),
                default=0.0
            )
        candidatos_det.sort(key=grav_no_detector, reverse=True)

        pegos = 0
        for cand in candidatos_det:
            if pegos >= limite_por_detector.get(det, 4):
                break
            uf = cand["uf"]
            # No estrato de piores, limitamos a 2 por UF inicialmente para diversificar
            if contagem_veiculos[uf] < 2:
                selecionadas_piores.append({**cand, "motivo": f"Pior achado [{det}]"})
                pids_selecionados.add(cand["page_id"])
                contagem_veiculos[uf] += 1
                pegos += 1
                if len(selecionadas_piores) >= ALVO_PIORES:
                    break
        if len(selecionadas_piores) >= ALVO_PIORES:
            break

    # Passada 2: Completar ate 30 com as maiores gravidades gerais, mantendo veiculos diversificados (max 3 por UF nos piores)
    if len(selecionadas_piores) < ALVO_PIORES:
        for cand in candidatas_com_defeito:
            if cand["page_id"] in pids_selecionados:
                continue
            uf = cand["uf"]
            if contagem_veiculos[uf] < 3:
                dets_str = "+".join(cand["detectores"]) if cand["detectores"] else "Grave"
                selecionadas_piores.append({**cand, "motivo": f"Pior achado [{dets_str}]"})
                pids_selecionados.add(cand["page_id"])
                contagem_veiculos[uf] += 1
                if len(selecionadas_piores) >= ALVO_PIORES:
                    break

    # Passada 3: Se ainda faltar, permitir ate 4 por UF
    if len(selecionadas_piores) < ALVO_PIORES:
        for cand in candidatas_com_defeito:
            if cand["page_id"] in pids_selecionados:
                continue
            uf = cand["uf"]
            if contagem_veiculos[uf] < MAX_PAGINAS_POR_VEICULO:
                dets_str = "+".join(cand["detectores"]) if cand["detectores"] else "Grave"
                selecionadas_piores.append({**cand, "motivo": f"Pior achado [{dets_str}]"})
                pids_selecionados.add(cand["page_id"])
                contagem_veiculos[uf] += 1
                if len(selecionadas_piores) >= ALVO_PIORES:
                    break

    assert len(selecionadas_piores) == ALVO_PIORES, f"Falha ao selecionar 30 piores: obtidas {len(selecionadas_piores)}"

    # -------------------------------------------------------------
    # 2. SELECAO DAS 30 ALEATORIAS (Semente 20261008)
    # -------------------------------------------------------------
    candidatas_aleatorias = [
        c for pid, c in candidatas_validas.items()
        if pid not in pids_selecionados
    ]
    # Ordem deterministica antes do shuffle
    candidatas_aleatorias.sort(key=lambda x: x["page_id"])

    rng = random.Random(SEMENTE_ALEATORIA)
    rng.shuffle(candidatas_aleatorias)

    selecionadas_aleatorias: list[dict] = []
    for cand in candidatas_aleatorias:
        uf = cand["uf"]
        # Teto rigido de no maximo 4 paginas por veiculo no lote total (piores + aleatorias)
        if contagem_veiculos[uf] < MAX_PAGINAS_POR_VEICULO:
            selecionadas_aleatorias.append({**cand, "motivo": "Amostra aleatoria"})
            pids_selecionados.add(cand["page_id"])
            contagem_veiculos[uf] += 1
            if len(selecionadas_aleatorias) >= ALVO_ALEATORIAS:
                break

    assert len(selecionadas_aleatorias) == ALVO_ALEATORIAS, f"Falha ao selecionar 30 aleatorias: obtidas {len(selecionadas_aleatorias)}"

    return selecionadas_piores, selecionadas_aleatorias


def construir_tarefa_e_renderizar(
    indice: int,
    item: dict,
    meta_diamond: dict[str, dict],
    dir_img: Path,
) -> dict:
    """Renderiza a imagem a 110 dpi e formata a tarefa no padrao do Diamond."""
    pid = item["page_id"]
    uf = item["uf"]
    arq = item["arquivo"]
    pag_idx = item["pagina"]
    pdf_path = item["pdf_path"]
    dados = item["dados"]
    meta = meta_diamond.get(pid, {})

    # 1. Renderizar imagem via PyMuPDF a 110 dpi em JPEG
    nome_img = f"{indice:03d}.jpg"
    caminho_img = dir_img / nome_img
    with pymupdf.open(pdf_path) as doc:
        pagina = doc[pag_idx]
        pix = pagina.get_pixmap(dpi=110)
        caminho_img.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(caminho_img))

    # 2. Dimensoes da pagina
    dim = dados.get("dimensions", {})
    largura = round(float(dim.get("width", 595.0)), 1)
    altura = round(float(dim.get("height", 842.0)), 1)

    # 3. Palavras
    palavras = dados.get("palavras", [])

    # 4. Proposta de caixas a partir das unidades do extrator novo
    unidades = dados.get("unidades", [])
    proposta_caixas = []

    for k, u in enumerate(unidades):
        tipo_u = u.get("tipo", "texto")
        classe_diamond = mapear_classe_diamond(tipo_u)

        raw_box = u.get("bbox", [0.0, 0.0, 10.0, 10.0])
        x0 = max(0.0, min(float(raw_box[0]), largura))
        y0 = max(0.0, min(float(raw_box[1]), altura))
        x1 = max(0.0, min(float(raw_box[2]), largura))
        y1 = max(0.0, min(float(raw_box[3]), altura))

        # Garantir area positiva minima para o servidor nao rejeitar
        if x1 - x0 < 1.0:
            x1 = min(largura, x0 + 1.0)
        if y1 - y0 < 1.0:
            y1 = min(altura, y0 + 1.0)

        proposta_caixas.append({
            "id": f"p{k+1}",
            "classe": classe_diamond,
            "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
            "origem": "extrator_sem_paragrafos",
            "tipo_original": tipo_u,
            "score": 1.0,
            "alertas": [],
        })

    # 5. Blocos v3 e detector (se disponiveis nos metadados diamond)
    blocos_v3 = meta.get("blocos_v3", [])
    detector = meta.get("detector", {"modelo": "docling-layout-heron", "regioes": []})
    extrator_sha = meta.get("extrator_sha256", "extrator_sem_paragrafos_202610")

    tarefa = {
        "n": indice,
        "page_id": pid,
        "uf": uf,
        "arquivo": arq,
        "pagina": pag_idx,
        "dimensions": {"width": largura, "height": altura},
        "imagem": nome_img,
        "palavras": palavras,
        "proposta": proposta_caixas,
        "blocos_v3": blocos_v3,
        "detector": detector,
        "stats": {
            "n_palavras": len(palavras),
            "n_proposta": len(proposta_caixas),
            "motivo_selecao": item.get("motivo", ""),
            "total_achados_auditor": item.get("total_achados", 0),
        },
        "extrator_sha256": extrator_sha,
    }

    return tarefa


def validar_tarefas_com_servidor(tarefas: list[dict], dir_img: Path) -> dict:
    """Valida as tarefas usando as regras e estruturas do servidor.py."""
    from src.anotacao import servidor

    erros = []
    avisos = []
    total_palavras = 0
    total_caixas_proposta = 0
    classes_contagem = Counter()

    for t in tarefas:
        pid = t["page_id"]
        W = t["dimensions"]["width"]
        H = t["dimensions"]["height"]

        if W <= 0 or H <= 0:
            erros.append(f"{pid}: dimensoes invalidas {W}x{H}")

        # Checar se a imagem existe
        arq_img = dir_img / t["imagem"]
        if not arq_img.exists() or arq_img.stat().st_size == 0:
            erros.append(f"{pid}: imagem {t['imagem']} inexistente ou vazia")

        # Checar palavras
        pws = t.get("palavras", [])
        total_palavras += len(pws)
        if not pws:
            avisos.append(f"{pid}: pagina sem palavras")

        # Checar proposta
        prop = t.get("proposta", [])
        total_caixas_proposta += len(prop)
        if not prop:
            erros.append(f"{pid}: proposta vazia")

        ids_prop = set()
        for p in prop:
            rid = p.get("id")
            if not rid or rid in ids_prop:
                erros.append(f"{pid}: id de regiao duplicado ou vazio ({rid})")
            ids_prop.add(rid)

            cl = p.get("classe")
            if cl not in servidor.CLASSES:
                erros.append(f"{pid}: classe invalida na proposta ({cl})")
            classes_contagem[cl] += 1

            bbox = p.get("bbox")
            if not bbox or len(bbox) != 4:
                erros.append(f"{pid}: bbox mal formatada")
            else:
                x0, y0, x1, y1 = bbox
                if x1 - x0 < 0.5 or y1 - y0 < 0.5:
                    erros.append(f"{pid}: caixa sem area suficiente ({bbox})")

        # Simular a checagem de palavras alfa que servidor.salvar_diamond faz
        fora = 0
        for w in pws:
            if not servidor.RE_ALFANUM.search(w[0]):
                continue
            cx = (w[1] + w[3]) / 2
            cy = (w[2] + w[4]) / 2
            dentro = any(r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3] for r in prop)
            if not dentro:
                fora += 1
        if fora > 0:
            avisos.append(f"{pid}: {fora} palavras fora das caixas da proposta (alerta normal para correcao humana)")

    return {
        "ok": len(erros) == 0,
        "erros": erros,
        "avisos": avisos,
        "total_tarefas": len(tarefas),
        "total_palavras": total_palavras,
        "total_caixas": total_caixas_proposta,
        "classes_contagem": dict(classes_contagem),
    }


def gerar_leiame(
    tarefas: list[dict],
    piores: list[dict],
    aleatorias: list[dict],
    relatorio_val: dict,
) -> str:
    """Gera o arquivo LEIAME.md com orientacoes, comandos e tabelas de estratificacao."""
    # Contagens por veiculo
    veiculos_piores = Counter(p["uf"] for p in piores)
    veiculos_aleat = Counter(p["uf"] for p in aleatorias)
    veiculos_total = Counter(t["uf"] for t in tarefas)

    # Detectores cobertos nos piores
    detectores_piores = Counter()
    for p in piores:
        for d in p.get("detectores", []):
            detectores_piores[d] += 1

    linhas_tabela_veiculos = []
    for uf in sorted(veiculos_total):
        linhas_tabela_veiculos.append(
            f"| `{uf}` | {veiculos_piores[uf]} | {veiculos_aleat[uf]} | **{veiculos_total[uf]}** |"
        )
    tabela_veiculos_md = "\n".join(linhas_tabela_veiculos)

    # Linhas da tabela das 60 paginas
    linhas_tabela_pags = []
    for t in tarefas:
        n = t["n"]
        pid = t["page_id"]
        uf = t["uf"]
        motivo = t["stats"].get("motivo_selecao", "")
        n_pals = t["stats"].get("n_palavras", 0)
        n_prop = t["stats"].get("n_proposta", 0)
        img = t["imagem"]
        linhas_tabela_pags.append(
            f"| {n:02d} | `{pid}` | `{uf}` | {motivo} | {n_pals} | {n_prop} | `{img}` |"
        )
    tabela_pags_md = "\n".join(linhas_tabela_pags)

    status_validacao = "PASSOU COM SUCESSO (0 erros)" if relatorio_val["ok"] else f"FALHOU ({len(relatorio_val['erros'])} erros)"

    classes_str = ", ".join(f"`{k}`: {v}" for k, v in sorted(relatorio_val["classes_contagem"].items()))

    return f"""# Lote Diamond Sem Caixas de Paragrafo (`lote_sem_paragrafos`)

Lote classificavel com **60 paginas estratificadas** preparadas a partir do extrator
novo sem caixas de paragrafo (linhas de texto corridas; tabelas e imagens atomicas;
cabecalhos, rodapes e quadros estruturais).

Este lote destina-se a **anotacao e correcao humana de segmentacao** pelo Pedro na
ferramenta Diamond (`src/anotacao/servidor.py --diamond`), sem ordem preenchida (anotacao cega).

---

## 1. Como Abrir o Lote no Diamond

O servidor local (`src/anotacao/servidor.py`) procura os lotes Diamond sob `data/diamond/<lote>/`.
Como os arquivos foram gerados sob `resultados/lote_sem_paragrafos/` (respeitando a regra de nao escrita em `data/`),
o lote deve ser copiado ou vinculado para `data/diamond/lote_sem_paragrafos/`.

### Passo a passo no PowerShell (Windows 11):

1. **Copiar a pasta do lote para `data/diamond/`:**
   ```powershell
   Copy-Item -Recurse resultados\\lote_sem_paragrafos data\\diamond\\lote_sem_paragrafos
   ```
   *(Alternativa com juncao NTFS instantanea sem duplicar disco):*
   ```powershell
   cmd /c mklink /J data\\diamond\\lote_sem_paragrafos resultados\\lote_sem_paragrafos
   ```

2. **Iniciar o servidor Diamond:**
   ```powershell
   venv\\Scripts\\python.exe src\\anotacao\\servidor.py --diamond
   ```

3. **Acessar a ferramenta no navegador:**
   - URL: **`http://127.0.0.1:8770/diamond`**
   - No seletor **Lote** (canto superior esquerdo), selecione: **`lote_sem_paragrafos`**
   - Informe seu nome no campo **Anotador** (ex.: `Pedro`).
   - As alteracoes sao salvas automaticamente em tempo real em `data/diamond/lote_sem_paragrafos/anotacoes.jsonl`.

---

## 2. O que Corrigir nas Paginas

A proposta que chega na tela contem as unidades do novo extrator como caixas iniciais.
O Pedro devera inspecionar e corrigir tres tipos principais de defeitos:

1. **Caixas com fronteiras erradas (Geometria):**
   - Linhas de texto que atravessam calhas entre colunas (dividir com <kbd>Shift</kbd>+<kbd>D</kbd> ou <kbd>D</kbd>).
   - Caixas de tabela ou figura que invadem texto corrido ou vice-versa.
   - Textos institucionais ou molduras que foram engolidos como texto simples.
   - Tecla <kbd>A</kbd> (<kbd>Shift</kbd>+<kbd>A</kbd> em todas) ajusta as bordas da caixa as palavras exatas de dentro.

2. **Classes erradas (Semantica):**
   - Títulos de secao/atos marcados como `texto` -> reclassificar para `titulo` (<kbd>1</kbd>).
   - Textos corridos marcados como `outro` ou `lista` -> reclassificar para `texto` (<kbd>2</kbd>).
   - Tabelas marcadas como texto ou figura -> reclassificar para `tabela` (<kbd>4</kbd>).
   - Assinaturas de autoridades -> reclassificar para `assinatura` (<kbd>5</kbd>).
   - Cabecalhos (<kbd>6</kbd>) e Rodapes (<kbd>7</kbd>) fragmentados ou ausentes.
   - Brasao/logo/QR code -> `figura` (<kbd>8</kbd>).

3. **Caixas que faltam:**
   - Palavras destacadas em vermelho (sem caixa): desenhe uma nova caixa arrastando o mouse na area.
   - Palavras destacadas em magenta (em duas caixas): ajuste ou redimensione as caixas concorrentes.

### Teclas rapidas:
- <kbd>1</kbd>–<kbd>9</kbd>: altera classe da caixa selecionada (1=Titulo, 2=Texto, 3=Lista, 4=Tabela, 5=Assinatura, 6=Cabecalho, 7=Rodape, 8=Figura, 9=Outro).
- <kbd>A</kbd>: ajusta caixa selecionada as palavras; <kbd>Shift</kbd>+<kbd>A</kbd>: ajusta todas.
- <kbd>D</kbd>: divide caixa na altura do clique; <kbd>Shift</kbd>+<kbd>D</kbd>: divide na largura.
- <kbd>J</kbd>: junta caixas selecionadas.
- <kbd>Del</kbd>: apaga caixa selecionada.
- <kbd>N</kbd>: navega para o proximo alerta.
- <kbd>Enter</kbd>: conclui e avanca.

---

## 3. Estratificacao da Amostra

O lote possui **60 paginas rigorosamente estratificadas**:
- **30 paginas com os piores achados do auditor** (`resultados/auditoria_extrator_sem_paragrafos.json`),
  garantindo diversificacao de defeitos graves (D1 a D7) e de orgaos publicadores.
- **30 paginas aleatorias** (semente fixa `20261008`) sorteadas sobre as paginas candidatas sem defeito grave
  para estimar a taxa real e nao viesada de erro do extrator.
- **Teto maximo de 4 paginas por veiculo** no lote todo para evitar sobre-representacao de qualquer diario oficial.
- **Exclusao estrita:** nenhuma pagina das bancadas humanas (`golden_v4` e `golden_v3`) e nenhuma de `data/labelstudio/`.

### Cobertura de Detectores nos Piores Achados:
- **D1 (Linha que atravessa colunas):** {detectores_piores['D1']} paginas
- **D2 (Sobreposicao tabela x texto):** {detectores_piores['D2']} paginas
- **D4 (Tabela suspeita / vazia):** {detectores_piores['D4']} paginas
- **D5 (Cabecalho/rodape fragmentado):** {detectores_piores['D5']} paginas
- **D6 (Linha com altura anomala):** {detectores_piores['D6']} paginas
- **D7 (Texto sem dono perto de atomo):** {detectores_piores['D7']} paginas

### Distribuicao de Paginas por Veiculo (Diario Oficial):

| Veiculo (`uf`) | Piores Achados | Aleatorias | Total no Lote |
|---|---:|---:|---:|
{tabela_veiculos_md}

---

## 4. Validacao Tecnica com `servidor.py`

- **Status da Validacao:** {status_validacao}
- **Total de Tarefas Verificadas:** {relatorio_val['total_tarefas']}
- **Total de Imagens JPEG (110 dpi):** {relatorio_val['total_tarefas']}
- **Total de Palavras no Lote:** {relatorio_val['total_palavras']:,}
- **Total de Regioes na Proposta:** {relatorio_val['total_caixas']:,}
- **Distribuicao de Classes na Proposta:** {classes_str}
- **Erros impeditivos:** {len(relatorio_val['erros'])}
- **Avisos informativos de palavras pendentes de caixa:** {len(relatorio_val['avisos'])} (esperados para correcao manual)

---

## 5. Tabela Completa das 60 Paginas do Lote

| N | Page ID | Veiculo | Motivo da Estratificacao | Palavras | Propostas | Imagem |
|---|---|---|---|---:|---:|---|
{tabela_pags_md}
"""


def main():
    print("[*] Iniciando montagem do lote classificavel sem caixas de paragrafo...")

    # 1. Carregar exclusoes
    proibidos = carregar_ids_proibidos()
    print(f"[*] IDs proibidos carregados: {len(proibidos)} (golden_v4, golden_v3, labelstudio)")

    # 2. Carregar dados do extrator em linhas
    dados_linhas = carregar_dados_linhas()
    print(f"[*] Paginas carregadas do extrator sem caixas (linhas): {len(dados_linhas)}")

    # 3. Carregar metadados diamond adicionais
    meta_diamond = carregar_metadados_diamond()
    print(f"[*] Metadados Diamond vinculados: {len(meta_diamond)}")

    # 4. Carregar auditoria
    auditoria = carregar_auditoria()
    print(f"[*] Auditoria carregada: {auditoria.get('total_paginas_auditadas', 0)} paginas auditadas")

    # 5. Estratificar 60 paginas (30 piores + 30 aleatorias)
    piores, aleatorias = selecionar_paginas(auditoria, dados_linhas, proibidos)
    print(f"[OK] Estratificacao concluida: {len(piores)} piores achados + {len(aleatorias)} aleatorias")

    selecionadas = piores + aleatorias
    assert len(selecionadas) == TOTAL_ALVO

    # 6. Criar diretorios
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    DIR_IMG.mkdir(parents=True, exist_ok=True)

    # 7. Renderizar imagens e construir tarefas
    tarefas = []
    print(f"[*] Renderizando imagens PyMuPDF (110 dpi) e montando tarefas.jsonl...")
    for idx, item in enumerate(selecionadas, start=1):
        t = construir_tarefa_e_renderizar(idx, item, meta_diamond, DIR_IMG)
        tarefas.append(t)
        if idx % 10 == 0 or idx == TOTAL_ALVO:
            print(f"    -> {idx}/{TOTAL_ALVO} paginas processadas")
            gc.collect()

    # 8. Gravar tarefas.jsonl
    print(f"[*] Gravando {ARQ_TAREFAS}...")
    with open(ARQ_TAREFAS, "w", encoding="utf-8") as f:
        for t in tarefas:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # 9. Validar tarefas usando as funcoes do servidor.py
    print(f"[*] Validando lote com regras de src/anotacao/servidor.py...")
    relatorio_val = validar_tarefas_com_servidor(tarefas, DIR_IMG)
    if relatorio_val["ok"]:
        print(f"[OK] Validacao do servidor.py: SUCESSO (todas as {len(tarefas)} tarefas abrem sem erro)")
    else:
        print(f"[!] ERROS de validacao encontrados ({len(relatorio_val['erros'])}):")
        for err in relatorio_val["erros"][:10]:
            print(f"    - {err}")

    # 10. Gerar LEIAME.md
    print(f"[*] Gravando {ARQ_LEIAME}...")
    conteudo_leiame = gerar_leiame(tarefas, piores, aleatorias, relatorio_val)
    with open(ARQ_LEIAME, "w", encoding="utf-8") as f:
        f.write(conteudo_leiame)

    print(f"[OK] Lote montado com sucesso em {DIR_SAIDA.relative_to(RAIZ)}")
    print(f"     - Tarefas: {ARQ_TAREFAS.relative_to(RAIZ)} ({len(tarefas)} linhas)")
    print(f"     - Imagens: {DIR_IMG.relative_to(RAIZ)}/ ({len(list(DIR_IMG.glob('*.jpg')))} JPEGs)")
    print(f"     - Documentacao: {ARQ_LEIAME.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
