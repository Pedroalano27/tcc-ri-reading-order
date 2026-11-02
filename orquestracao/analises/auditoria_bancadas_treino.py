"""Auditoria de sobreposição entre dados de treino e bancadas de medição.

Este script audita rigorosamente se as páginas ou documentos PDF usados para
MEDIR os ordenadores se misturam com as páginas usadas para TREINAR os modelos.

Conjuntos auditados:
  - Treino:
      * data/processed/blocos/<veiculo>.jsonl dos veículos de treino em splits.json
      * TODOS os arquivos de data/processed/blocos_extra/*.jsonl
  - Validação Silver:
      * data/processed/blocos/<veiculo>.jsonl dos veículos de validação em splits.json
  - Teste Silver:
      * data/processed/blocos/<veiculo>.jsonl dos veículos de teste em splits.json
  - Bancada Humana A:
      * data/golden/golden_v4/tarefas.jsonl (45 tarefas)
  - Bancada Humana B Nova:
      * data/golden/_avaliacao/golden_v3/tarefas.jsonl (as que não estão na Bancada A)

Saídas produzidas:
  - resultados/auditoria_bancadas_treino.md (relatório completo em Markdown)
  - resultados/auditoria_excluir_do_treino.txt (lista de page_id de treino a excluir)

Regras:
  - Apenas biblioteca padrão Python (sem dependências externas)
  - Baixo consumo de memória (processamento leve em streaming/metadados)
  - Não toca em data/labelstudio
  - Codificação UTF-8 em todas as entradas e saídas

Uso:
  venv\\Scripts\\python.exe orquestracao/analises/auditoria_bancadas_treino.py
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime
import json
import os
from pathlib import Path
import sys

# Ajuste defensivo de codificação no console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Determina raiz do projeto
RAIZ = Path(__file__).resolve().parents[2]
if not (RAIZ / "data" / "processed" / "splits.json").exists():
    cwd = Path.cwd()
    if (cwd / "data" / "processed" / "splits.json").exists():
        RAIZ = cwd


def extrair_partes_page_id(page_id: str | None, d: dict | None = None, default_uf: str = "") -> dict | None:
    """Extrai defensivamente page_id, uf, arquivo, pagina e pdf_id."""
    uf = None
    arquivo = None
    pagina = None

    if d:
        uf = d.get("uf") or d.get("veiculo") or default_uf
        arquivo = d.get("arquivo")
        pagina = d.get("pagina")

    if page_id and isinstance(page_id, str):
        if "/" in page_id:
            p_uf, resto = page_id.split("/", 1)
            if not uf:
                uf = p_uf
        else:
            resto = page_id

        if "#p" in resto:
            p_arq, p_pag = resto.rsplit("#p", 1)
            if not arquivo:
                arquivo = p_arq
            if pagina is None:
                pagina = p_pag
        else:
            if not arquivo:
                arquivo = resto
    else:
        if uf and arquivo and pagina is not None:
            page_id = f"{uf}/{arquivo}#p{pagina}"
        elif uf and arquivo:
            page_id = f"{uf}/{arquivo}"
        else:
            return None

    uf = uf or default_uf or "desconhecido"
    arquivo = arquivo or "desconhecido"
    pdf_id = f"{uf}/{arquivo}"

    return {
        "page_id": page_id,
        "uf": uf,
        "arquivo": arquivo,
        "pagina": str(pagina) if pagina is not None else "",
        "pdf_id": pdf_id,
    }


def ler_jsonl_paginas(caminho: Path, default_uf: str = "", origem: str = "") -> list[dict]:
    """Lê linhas de um JSONL de forma defensiva e em baixo consumo de memória."""
    paginas = []
    if not caminho.is_file():
        return paginas

    with open(caminho, "r", encoding="utf-8") as f:
        for num_linha, linha in enumerate(f, 1):
            linha_str = linha.strip()
            if not linha_str:
                continue
            try:
                d = json.loads(linha_str)
            except json.JSONDecodeError:
                continue

            page_id = d.get("page_id")
            reg = extrair_partes_page_id(page_id, d, default_uf=default_uf)
            if reg:
                reg["origem"] = origem or caminho.name
                reg["arquivo_fonte"] = str(caminho)
                reg["linha"] = num_linha
                paginas.append(reg)

    return paginas


def fmt_num(n: int | float) -> str:
    """Formata número com padrão brasileiro."""
    if isinstance(n, int):
        return f"{n:,}".replace(",", ".")
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_dados_splits(caminho_splits: Path) -> dict:
    """Carrega splits.json com tratamento defensivo."""
    if not caminho_splits.is_file():
        raise FileNotFoundError(f"Arquivo splits.json não encontrado em: {caminho_splits}")
    with open(caminho_splits, "r", encoding="utf-8") as f:
        return json.load(f)


def obter_papel_veiculo(uf: str, splits: dict) -> str:
    """Identifica a função metodológica do veículo segundo splits.json."""
    if uf in splits.get("treino", []):
        return "treino"
    if uf in splits.get("validacao", []):
        return "validacao"
    if uf in splits.get("teste", []):
        return "teste"
    if uf in splits.get("ufs_nao_confiaveis", []):
        return "não confiável"
    return "não listado em splits.json"


def analisar_distribuicao_veiculos(paginas: list[dict], splits: dict, veiculos_vistos_treino: set[str]) -> dict:
    """Calcula estatísticas de veículos para uma bancada humana."""
    contagem = collections.Counter(p["uf"] for p in paginas)
    total_pags = len(paginas)
    linhas = []
    total_vistos = 0
    total_nao_vistos = 0

    for uf in sorted(contagem.keys()):
        qtd = contagem[uf]
        papel = obter_papel_veiculo(uf, splits)
        visto = uf in veiculos_vistos_treino
        if visto:
            total_vistos += qtd
        else:
            total_nao_vistos += qtd

        prop = (qtd / total_pags * 100.0) if total_pags > 0 else 0.0
        linhas.append({
            "uf": uf,
            "qtd": qtd,
            "prop": prop,
            "papel": papel,
            "visto": visto
        })

    prop_vistos = (total_vistos / total_pags * 100.0) if total_pags > 0 else 0.0
    prop_nao_vistos = (total_nao_vistos / total_pags * 100.0) if total_pags > 0 else 0.0

    return {
        "linhas": linhas,
        "total_paginas": total_pags,
        "total_vistos": total_vistos,
        "prop_vistos": prop_vistos,
        "total_nao_vistos": total_nao_vistos,
        "prop_nao_vistos": prop_nao_vistos
    }


def auditar_sobreposicao_pdf(lista_treino: list[dict], lista_medicao: list[dict]) -> list[dict]:
    """Identifica sobreposição de PDFs (mesmo veículo e mesmo arquivo)."""
    treino_por_pdf = collections.defaultdict(list)
    for p in lista_treino:
        treino_por_pdf[p["pdf_id"]].append(p)

    med_por_pdf = collections.defaultdict(list)
    for p in lista_medicao:
        med_por_pdf[p["pdf_id"]].append(p)

    pdfs_compartilhados = sorted(set(treino_por_pdf.keys()) & set(med_por_pdf.keys()))

    resultados = []
    for pdf_id in pdfs_compartilhados:
        pags_treino = sorted(set(p["page_id"] for p in treino_por_pdf[pdf_id]))
        pags_med = sorted(set(p["page_id"] for p in med_por_pdf[pdf_id]))

        pags_comuns = sorted(set(pags_treino) & set(pags_med))
        pags_distintas_treino = sorted(set(pags_treino) - set(pags_med))
        pags_distintas_med = sorted(set(pags_med) - set(pags_treino))

        uf = treino_por_pdf[pdf_id][0]["uf"]
        arquivo = treino_por_pdf[pdf_id][0]["arquivo"]

        resultados.append({
            "pdf_id": pdf_id,
            "uf": uf,
            "arquivo": arquivo,
            "pags_treino": pags_treino,
            "pags_medicao": pags_med,
            "pags_comuns": pags_comuns,
            "pags_distintas_treino": pags_distintas_treino,
            "pags_distintas_medicao": pags_distintas_med,
            "tem_mesma_pagina": bool(pags_comuns),
            "tem_paginas_distintas": bool(pags_distintas_treino or pags_distintas_med)
        })

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Audita separação entre treino e bancadas de teste/humanas.")
    parser.add_argument(
        "--saida-md",
        default=str(RAIZ / "resultados" / "auditoria_bancadas_treino.md"),
        help="Caminho do relatório Markdown de saída"
    )
    parser.add_argument(
        "--saida-txt",
        default=str(RAIZ / "resultados" / "auditoria_excluir_do_treino.txt"),
        help="Caminho do arquivo TXT com page_ids de treino a excluir"
    )
    args = parser.parse_args()

    caminho_saida_md = Path(args.saida_md).resolve()
    caminho_saida_txt = Path(args.saida_txt).resolve()
    caminho_saida_md.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida_txt.parent.mkdir(parents=True, exist_ok=True)

    # 1. Carrega splits
    splits_path = RAIZ / "data" / "processed" / "splits.json"
    splits = carregar_dados_splits(splits_path)

    treino_ufs_splits = list(splits.get("treino", []))
    validacao_ufs_splits = list(splits.get("validacao", []))
    teste_ufs_splits = list(splits.get("teste", []))

    dir_blocos = RAIZ / "data" / "processed" / "blocos"
    dir_blocos_extra = RAIZ / "data" / "processed" / "blocos_extra"

    # 2. Carrega Treino Base e Treino Extra
    treino_base_paginas = []
    for uf in treino_ufs_splits:
        arq_uf = dir_blocos / f"{uf}.jsonl"
        if arq_uf.is_file():
            treino_base_paginas.extend(ler_jsonl_paginas(arq_uf, default_uf=uf, origem=f"blocos/{uf}.jsonl"))

    treino_extra_paginas = []
    if dir_blocos_extra.is_dir():
        for arq_extra in sorted(dir_blocos_extra.rglob("*.jsonl")):
            treino_extra_paginas.extend(
                ler_jsonl_paginas(arq_extra, default_uf=arq_extra.stem, origem=f"blocos_extra/{arq_extra.name}")
            )

    treino_todas_paginas = treino_base_paginas + treino_extra_paginas

    # Deduplicação e mapeamento do treino
    treino_page_id_map = {}
    for p in treino_todas_paginas:
        pid = p["page_id"]
        if pid not in treino_page_id_map:
            treino_page_id_map[pid] = p

    treino_page_ids = set(treino_page_id_map.keys())
    treino_pdfs = set(p["pdf_id"] for p in treino_todas_paginas)
    treino_ufs_distintos = set(p["uf"] for p in treino_todas_paginas)
    veiculos_vistos_treino = set(treino_ufs_splits) | treino_ufs_distintos

    # 3. Carrega Validação Silver
    val_paginas = []
    for uf in validacao_ufs_splits:
        arq_uf = dir_blocos / f"{uf}.jsonl"
        if arq_uf.is_file():
            val_paginas.extend(ler_jsonl_paginas(arq_uf, default_uf=uf, origem=f"blocos/{uf}.jsonl"))

    val_page_id_map = {p["page_id"]: p for p in val_paginas}
    val_page_ids = set(val_page_id_map.keys())
    val_pdfs = set(p["pdf_id"] for p in val_paginas)
    val_ufs = set(p["uf"] for p in val_paginas)

    # 4. Carrega Teste Silver
    teste_paginas = []
    for uf in teste_ufs_splits:
        arq_uf = dir_blocos / f"{uf}.jsonl"
        if arq_uf.is_file():
            teste_paginas.extend(ler_jsonl_paginas(arq_uf, default_uf=uf, origem=f"blocos/{uf}.jsonl"))

    teste_page_id_map = {p["page_id"]: p for p in teste_paginas}
    teste_page_ids = set(teste_page_id_map.keys())
    teste_pdfs = set(p["pdf_id"] for p in teste_paginas)
    teste_ufs = set(p["uf"] for p in teste_paginas)

    # 5. Carrega Bancada Humana A (Golden v4 - 45 tarefas)
    arq_golden_v4 = RAIZ / "data" / "golden" / "golden_v4" / "tarefas.jsonl"
    bancada_a_paginas = ler_jsonl_paginas(arq_golden_v4, origem="golden_v4")
    bancada_a_page_id_map = {p["page_id"]: p for p in bancada_a_paginas}
    bancada_a_page_ids = set(bancada_a_page_id_map.keys())
    bancada_a_pdfs = set(p["pdf_id"] for p in bancada_a_paginas)
    bancada_a_ufs = set(p["uf"] for p in bancada_a_paginas)

    # 6. Carrega Bancada Humana B (Golden v3 total - 47 tarefas; e Bancada B nova: fora do v4)
    arq_golden_v3 = RAIZ / "data" / "golden" / "_avaliacao" / "golden_v3" / "tarefas.jsonl"
    golden_v3_total_paginas = ler_jsonl_paginas(arq_golden_v3, origem="golden_v3")
    golden_v3_total_page_id_map = {p["page_id"]: p for p in golden_v3_total_paginas}
    golden_v3_total_page_ids = set(golden_v3_total_page_id_map.keys())
    golden_v3_total_pdfs = set(p["pdf_id"] for p in golden_v3_total_paginas)
    golden_v3_total_ufs = set(p["uf"] for p in golden_v3_total_paginas)

    # Bancada B nova: tarefas do golden_v3 que NÃO constam na Bancada A (golden_v4)
    bancada_b_nova_paginas = [p for p in golden_v3_total_paginas if p["page_id"] not in bancada_a_page_ids]
    bancada_b_nova_page_id_map = {p["page_id"]: p for p in bancada_b_nova_paginas}
    bancada_b_nova_page_ids = set(bancada_b_nova_page_id_map.keys())
    bancada_b_nova_pdfs = set(p["pdf_id"] for p in bancada_b_nova_paginas)
    bancada_b_nova_ufs = set(p["uf"] for p in bancada_b_nova_paginas)

    # 7. Cálculos de sobreposição de page_id
    sobrepos_val_page_id = sorted(treino_page_ids & val_page_ids)
    sobrepos_teste_page_id = sorted(treino_page_ids & teste_page_ids)
    sobrepos_bancada_a_page_id = sorted(treino_page_ids & bancada_a_page_ids)
    sobrepos_bancada_b_nova_page_id = sorted(treino_page_ids & bancada_b_nova_page_ids)
    sobrepos_golden_v3_total_page_id = sorted(treino_page_ids & golden_v3_total_page_ids)

    # 8. Cálculos de sobreposição de PDF
    sobrepos_val_pdf = auditar_sobreposicao_pdf(treino_todas_paginas, val_paginas)
    sobrepos_teste_pdf = auditar_sobreposicao_pdf(treino_todas_paginas, teste_paginas)
    sobrepos_bancada_a_pdf = auditar_sobreposicao_pdf(treino_todas_paginas, bancada_a_paginas)
    sobrepos_bancada_b_nova_pdf = auditar_sobreposicao_pdf(treino_todas_paginas, bancada_b_nova_paginas)
    sobrepos_golden_v3_total_pdf = auditar_sobreposicao_pdf(treino_todas_paginas, golden_v3_total_paginas)

    # 9. Análise de veículos das bancadas humanas
    analise_veiculos_a = analisar_distribuicao_veiculos(bancada_a_paginas, splits, veiculos_vistos_treino)
    analise_veiculos_b_nova = analisar_distribuicao_veiculos(bancada_b_nova_paginas, splits, veiculos_vistos_treino)
    analise_veiculos_b_total = analisar_distribuicao_veiculos(golden_v3_total_paginas, splits, veiculos_vistos_treino)

    # 10. Lista de exclusão para o orquestrador:
    # "toda página de treino cujo PDF aparece em alguma bancada humana"
    todos_pdfs_humanos = bancada_a_pdfs | golden_v3_total_pdfs
    paginas_treino_a_excluir = sorted(set(
        p["page_id"] for p in treino_todas_paginas if p["pdf_id"] in todos_pdfs_humanos
    ))

    # Grava arquivo TXT de exclusão
    with open(caminho_saida_txt, "w", encoding="utf-8") as f:
        for pid in paginas_treino_a_excluir:
            f.write(f"{pid}\n")

    # 11. Montagem das 4 linhas do Resumo Executivo
    # Linha 1: há page_id repetido?
    total_reps_page_id = (
        len(sobrepos_val_page_id) +
        len(sobrepos_teste_page_id) +
        len(sobrepos_bancada_a_page_id) +
        len(sobrepos_bancada_b_nova_page_id)
    )
    if total_reps_page_id == 0:
        resumo_l1 = (
            "Não há nenhum page_id repetido entre treino e os conjuntos de medição "
            "(validação silver: 0, teste silver: 0, bancada A: 0, bancada B nova: 0)."
        )
    else:
        detalhes_l1 = []
        if sobrepos_val_page_id:
            detalhes_l1.append(f"validação silver: {len(sobrepos_val_page_id)}")
        if sobrepos_teste_page_id:
            detalhes_l1.append(f"teste silver: {len(sobrepos_teste_page_id)}")
        if sobrepos_bancada_a_page_id:
            detalhes_l1.append(f"bancada A: {len(sobrepos_bancada_a_page_id)}")
        if sobrepos_bancada_b_nova_page_id:
            detalhes_l1.append(f"bancada B nova: {len(sobrepos_bancada_b_nova_page_id)}")
        resumo_l1 = (
            f"Sim, há {total_reps_page_id} ocorrência(s) de page_id repetido entre treino e medição "
            f"({', '.join(detalhes_l1)})."
        )

    # Linha 2: há PDF repetido?
    total_pdfs_repetidos = (
        len(sobrepos_val_pdf) +
        len(sobrepos_teste_pdf) +
        len(sobrepos_bancada_a_pdf) +
        len(sobrepos_bancada_b_nova_pdf)
    )
    if total_pdfs_repetidos == 0:
        resumo_l2 = (
            "Não há nenhum PDF repetido (mesmo veículo e mesmo arquivo) entre treino e os conjuntos de medição."
        )
    else:
        detalhes_l2 = []
        if sobrepos_val_pdf:
            detalhes_l2.append(f"validação: {len(sobrepos_val_pdf)} PDF(s)")
        if sobrepos_teste_pdf:
            detalhes_l2.append(f"teste: {len(sobrepos_teste_pdf)} PDF(s)")
        if sobrepos_bancada_a_pdf:
            detalhes_l2.append(f"bancada A: {len(sobrepos_bancada_a_pdf)} PDF(s)")
        if sobrepos_bancada_b_nova_pdf:
            detalhes_l2.append(f"bancada B nova: {len(sobrepos_bancada_b_nova_pdf)} PDF(s)")
        resumo_l2 = (
            f"Sim, há {total_pdfs_repetidos} caso(s) de sobreposição de PDF entre treino e medição "
            f"({', '.join(detalhes_l2)}), apresentando vazamento de template/documento intra-PDF."
        )

    # Linha 3: quantas páginas de cada bancada humana são de veículo visto no treino?
    resumo_l3 = (
        f"Bancada A (golden_v4): {analise_veiculos_a['total_vistos']} de {analise_veiculos_a['total_paginas']} "
        f"páginas ({fmt_num(analise_veiculos_a['prop_vistos'])}%) são de veículos vistos no treino "
        f"({analise_veiculos_a['total_nao_vistos']} em não vistos); "
        f"Bancada B nova (golden_v3 fora do v4): {analise_veiculos_b_nova['total_vistos']} de "
        f"{analise_veiculos_b_nova['total_paginas']} páginas ({fmt_num(analise_veiculos_b_nova['prop_vistos'])}%) "
        f"são de veículos vistos no treino ({analise_veiculos_b_nova['total_nao_vistos']} em não vistos)."
    )

    # Linha 4: o que o orquestrador deve excluir do treino para a medição ser limpa?
    resumo_l4 = (
        f"O orquestrador deve excluir exatamente {len(paginas_treino_a_excluir)} páginas do conjunto de treino "
        f"(cujos PDFs pertencem a alguma bancada humana), listadas em resultados/auditoria_excluir_do_treino.txt."
    )

    # 12. Montagem do Relatório Markdown
    agora_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append("# Auditoria de Bancadas de Avaliação vs. Treino")
    md.append("")
    md.append(f"*Data da auditoria*: {agora_iso}  ")
    md.append(f"*Ambiente*: Python {sys.version.split()[0]} no Windows | Validação estrita por biblioteca padrão  ")
    md.append(f"*Critério de exclusão*: Todo `page_id` de treino cujo PDF (`<veiculo>/<arquivo.pdf>`) aparece nas bancadas humanas.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Resumo Executivo (4 Linhas)")
    md.append("")
    md.append(f"1. **Sobreposição exata de `page_id`**: {resumo_l1}")
    md.append(f"2. **Sobreposição de PDF (mesmo documento)**: {resumo_l2}")
    md.append(f"3. **Páginas humanas em veículos vistos no treino**: {resumo_l3}")
    md.append(f"4. **Isolamento limpo para o treino**: {resumo_l4}")
    md.append("")
    md.append("---")
    md.append("")

    # Seção 1: Tabela geral
    md.append("## 1. Visão Geral dos Conjuntos")
    md.append("")
    md.append("Contagem de páginas únicas (`page_id`), documentos PDF distintos (`<veiculo>/<arquivo>`) e veículos distintos em cada partição:")
    md.append("")
    md.append("| Conjunto | Páginas (`page_id`) | PDFs Distintos | Veículos Distintos | Fontes Analisadas |")
    md.append("|---|---:|---:|---:|---|")
    md.append(
        f"| **Treino Total** (base + extra) | **{fmt_num(len(treino_page_ids))}** | "
        f"**{fmt_num(len(treino_pdfs))}** | **{fmt_num(len(treino_ufs_distintos))}** | "
        f"`data/processed/blocos/` (7 UFs) + `data/processed/blocos_extra/` |"
    )
    md.append(
        f"| └─ Treino Base | {fmt_num(len(set(p['page_id'] for p in treino_base_paginas)))} | "
        f"{fmt_num(len(set(p['pdf_id'] for p in treino_base_paginas)))} | "
        f"{fmt_num(len(set(p['uf'] for p in treino_base_paginas)))} | "
        f"`data/processed/blocos/<veiculo>.jsonl` dos 7 veículos em `splits.json` |"
    )
    md.append(
        f"| └─ Treino Extra | {fmt_num(len(set(p['page_id'] for p in treino_extra_paginas)))} | "
        f"{fmt_num(len(set(p['pdf_id'] for p in treino_extra_paginas)))} | "
        f"{fmt_num(len(set(p['uf'] for p in treino_extra_paginas)))} | "
        f"Todos os arquivos em `data/processed/blocos_extra/*.jsonl` |"
    )
    md.append(
        f"| **Validação Silver** | {fmt_num(len(val_page_ids))} | {fmt_num(len(val_pdfs))} | "
        f"{fmt_num(len(val_ufs))} | `data/processed/blocos/<veiculo>.jsonl` (RN) |"
    )
    md.append(
        f"| **Teste Silver** | {fmt_num(len(teste_page_ids))} | {fmt_num(len(teste_pdfs))} | "
        f"{fmt_num(len(teste_ufs))} | `data/processed/blocos/<veiculo>.jsonl` (CE, MA, RJ) |"
    )
    md.append(
        f"| **Bancada Humana A** (Golden v4) | {fmt_num(len(bancada_a_page_ids))} | "
        f"{fmt_num(len(bancada_a_pdfs))} | {fmt_num(len(bancada_a_ufs))} | "
        f"`data/golden/golden_v4/tarefas.jsonl` (45 tarefas) |"
    )
    md.append(
        f"| **Bancada Humana B Nova** (Golden v3 fora do v4) | {fmt_num(len(bancada_b_nova_page_ids))} | "
        f"{fmt_num(len(bancada_b_nova_pdfs))} | {fmt_num(len(bancada_b_nova_ufs))} | "
        f"`data/golden/_avaliacao/golden_v3/tarefas.jsonl` (excluídas as 20 do v4) |"
    )
    md.append(
        f"| *Referência*: Bancada Humana B Completa (Golden v3 total) | {fmt_num(len(golden_v3_total_page_ids))} | "
        f"{fmt_num(len(golden_v3_total_pdfs))} | {fmt_num(len(golden_v3_total_ufs))} | "
        f"`data/golden/_avaliacao/golden_v3/tarefas.jsonl` (47 tarefas completas) |"
    )
    md.append("")

    # Observação sobre duplicatas internas de treino se houver
    duplicatas_treino = len(treino_todas_paginas) - len(treino_page_ids)
    if duplicatas_treino > 0:
        md.append(f"> [!NOTE]\n> O conjunto de treino apresentou **{duplicatas_treino}** repetições internas de registros entre base e extra (total de {len(treino_todas_paginas)} registros para {len(treino_page_ids)} páginas únicas).")
        md.append("")

    md.append("---")
    md.append("")

    # Seção 2: Sobreposição exata de page_id
    md.append("## 2. Sobreposição Exata de `page_id` entre Treino e Medição")
    md.append("")
    md.append("Uma sobreposição exata de `page_id` significa que a exata mesma página usada para avaliar um modelo também estava presente no lote de treino.")
    md.append("")

    # 2.1 Validação
    md.append("### 2.1 Treino vs. Validação Silver")
    if sobrepos_val_page_id:
        md.append(f"⚠️ **{len(sobrepos_val_page_id)} página(s) repetida(s)**:")
        for pid in sobrepos_val_page_id:
            md.append(f"- `{pid}`")
    else:
        md.append("✅ **0 páginas repetidas**. Separação estrita garantida por veículo (`official_diary_rn`).")
    md.append("")

    # 2.2 Teste Silver
    md.append("### 2.2 Treino vs. Teste Silver")
    if sobrepos_teste_page_id:
        md.append(f"⚠️ **{len(sobrepos_teste_page_id)} página(s) repetida(s)**:")
        for pid in sobrepos_teste_page_id:
            md.append(f"- `{pid}`")
    else:
        md.append("✅ **0 páginas repetidas**. Separação estrita garantida por veículo (`official_diary_ce`, `official_diary_ma`, `official_diary_rj`).")
    md.append("")

    # 2.3 Bancada A
    md.append("### 2.3 Treino vs. Bancada Humana A (Golden v4)")
    if sobrepos_bancada_a_page_id:
        md.append(f"⚠️ **{len(sobrepos_bancada_a_page_id)} página(s) com page_id idêntico no treino**:")
        for pid in sobrepos_bancada_a_page_id:
            origens = [p["origem"] for p in treino_todas_paginas if p["page_id"] == pid]
            md.append(f"- `{pid}` (Origem no treino: {', '.join(sorted(set(origens)))})")
    else:
        md.append("✅ **0 páginas repetidas**.")
    md.append("")

    # 2.4 Bancada B Nova
    md.append("### 2.4 Treino vs. Bancada Humana B Nova (Golden v3 fora do v4)")
    if sobrepos_bancada_b_nova_page_id:
        md.append(f"⚠️ **{len(sobrepos_bancada_b_nova_page_id)} página(s) com page_id idêntico no treino**:")
        for pid in sobrepos_bancada_b_nova_page_id:
            origens = [p["origem"] for p in treino_todas_paginas if p["page_id"] == pid]
            md.append(f"- `{pid}` (Origem no treino: {', '.join(sorted(set(origens)))})")
    else:
        md.append("✅ **0 páginas repetidas**.")
    md.append("")

    # 2.5 Bancada B Total
    md.append("### 2.5 Treino vs. Bancada Humana B Total (Golden v3 completo)")
    if sobrepos_golden_v3_total_page_id:
        md.append(f"ℹ️ **{len(sobrepos_golden_v3_total_page_id)} página(s) com page_id idêntico no treino**:")
        for pid in sobrepos_golden_v3_total_page_id:
            origens = [p["origem"] for p in treino_todas_paginas if p["page_id"] == pid]
            md.append(f"- `{pid}` (Origem no treino: {', '.join(sorted(set(origens)))})")
    else:
        md.append("✅ **0 páginas repetidas**.")
    md.append("")

    md.append("---")
    md.append("")

    # Seção 3: Sobreposição de PDF
    md.append("## 3. Sobreposição de PDFs (Mesmo Veículo e Mesmo Arquivo)")
    md.append("")
    md.append("Esta análise audita o vazamento em nível de documento: casos onde o treino e a bancada de teste compartilham o mesmo arquivo PDF físico, seja na mesma página ou em páginas distintas.")
    md.append("")

    def formatar_tabela_sobreposicao_pdf(sobrepos_pdfs: list[dict], nome_medicao: str) -> list[str]:
        linhas_tabela = []
        if not sobrepos_pdfs:
            linhas_tabela.append(f"✅ **Nenhum PDF compartilhado** entre treino e {nome_medicao}.")
            return linhas_tabela

        linhas_tabela.append(f"⚠️ Foram identificados **{len(sobrepos_pdfs)} PDF(s) compartilhados** entre treino e {nome_medicao}:")
        linhas_tabela.append("")
        linhas_tabela.append("| PDF Compartilhado (`<uf>/<arquivo>`) | Páginas no Treino | Páginas na Medição | Páginas Idênticas? | Páginas Distintas do Mesmo PDF? |")
        linhas_tabela.append("|---|---|---|---|---|")
        for item in sobrepos_pdfs:
            pags_tr = ", ".join(f"#p{p.split('#p')[-1]}" if "#p" in p else p for p in item["pags_treino"])
            pags_md = ", ".join(f"#p{p.split('#p')[-1]}" if "#p" in p else p for p in item["pags_medicao"])
            mesma = "Sim" if item["tem_mesma_pagina"] else "Não"
            distinta = "Sim" if item["tem_paginas_distintas"] else "Não"
            linhas_tabela.append(f"| `{item['pdf_id']}` | `{pags_tr}` | `{pags_md}` | {mesma} | {distinta} |")
        return linhas_tabela

    md.append("### 3.1 Treino vs. Validação Silver")
    md.extend(formatar_tabela_sobreposicao_pdf(sobrepos_val_pdf, "Validação Silver"))
    md.append("")

    md.append("### 3.2 Treino vs. Teste Silver")
    md.extend(formatar_tabela_sobreposicao_pdf(sobrepos_teste_pdf, "Teste Silver"))
    md.append("")

    md.append("### 3.3 Treino vs. Bancada Humana A (Golden v4)")
    md.extend(formatar_tabela_sobreposicao_pdf(sobrepos_bancada_a_pdf, "Bancada Humana A (Golden v4)"))
    md.append("")

    md.append("### 3.4 Treino vs. Bancada Humana B Nova (Golden v3 fora do v4)")
    md.extend(formatar_tabela_sobreposicao_pdf(sobrepos_bancada_b_nova_pdf, "Bancada Humana B Nova"))
    md.append("")

    md.append("### 3.5 Treino vs. Bancada Humana B Total (Golden v3 completo)")
    md.extend(formatar_tabela_sobreposicao_pdf(sobrepos_golden_v3_total_pdf, "Bancada Humana B Total"))
    md.append("")

    md.append("---")
    md.append("")

    # Seção 4: Tabela por veículo nas bancadas humanas
    md.append("## 4. Distribuição por Veículo nas Bancadas Humanas")
    md.append("")
    md.append("Mostra a proporção de páginas originárias de veículos que faziam parte do conjunto de treino versus veículos inéditos (zero-shot de veículo/layout).")
    md.append("")

    def formatar_tabela_veiculos(analise: dict, titulo_tabela: str) -> list[str]:
        linhas = []
        linhas.append(f"#### {titulo_tabela}")
        linhas.append("")
        linhas.append("| Veículo (`uf`) | Páginas | Proporção | Papel no `splits.json` | Visto no Treino? |")
        linhas.append("|---|---:|---:|---|---|")
        for r in analise["linhas"]:
            visto_str = "**Sim**" if r["visto"] else "Não"
            linhas.append(f"| `{r['uf']}` | {r['qtd']} | {fmt_num(r['prop'])}% | {r['papel']} | {visto_str} |")
        linhas.append("|---|---:|---:|---|---|")
        linhas.append(
            f"| **TOTAL EM VEÍCULOS VISTOS NO TREINO** | **{analise['total_vistos']}** | "
            f"**{fmt_num(analise['prop_vistos'])}%** | — | **SIM** |"
        )
        linhas.append(
            f"| **TOTAL EM VEÍCULOS NÃO VISTOS NO TREINO** | **{analise['total_nao_vistos']}** | "
            f"**{fmt_num(analise['prop_nao_vistos'])}%** | — | **NÃO** |"
        )
        linhas.append(f"| **TOTAL GERAL DA BANCADA** | **{analise['total_paginas']}** | **100,0%** | — | — |")
        linhas.append("")
        return linhas

    md.extend(formatar_tabela_veiculos(analise_veiculos_a, "Bancada Humana A (Golden v4 — 45 tarefas)"))
    md.extend(formatar_tabela_veiculos(analise_veiculos_b_nova, "Bancada Humana B Nova (Golden v3 fora do v4 — 27 tarefas)"))
    md.extend(formatar_tabela_veiculos(analise_veiculos_b_total, "Referência: Bancada Humana B Total (Golden v3 completo — 47 tarefas)"))

    md.append("---")
    md.append("")

    # Seção 5: Lista de exclusão para o orquestrador
    md.append("## 5. Instruções de Isolamento para o Orquestrador")
    md.append("")
    md.append("Para que o benchmark e os testes dos ordenadores reflitam capacidades de generalização puras e sem vazamento intra-documento, recomenda-se que o orquestrador filtre o lote de treino.")
    md.append("")
    md.append(f"Arquivo gerado: [`resultados/auditoria_excluir_do_treino.txt`](resultados/auditoria_excluir_do_treino.txt)  ")
    md.append(f"Total de páginas a excluir do treino: **{len(paginas_treino_a_excluir)}**")
    md.append("")
    if paginas_treino_a_excluir:
        md.append("### Detalhamento das Páginas de Treino a Excluir:")
        md.append("")
        md.append("| `page_id` de Treino a Excluir | PDF Compartilhado com Bancada Humana | Presente em qual Bancada Humana? |")
        md.append("|---|---|---|")
        for pid in paginas_treino_a_excluir:
            p_obj = treino_page_id_map[pid]
            pdf = p_obj["pdf_id"]
            em_bancadas = []
            if pdf in bancada_a_pdfs:
                em_bancadas.append("Golden v4")
            if pdf in golden_v3_total_pdfs:
                em_bancadas.append("Golden v3")
            bancadas_str = ", ".join(em_bancadas) if em_bancadas else "Humana"
            md.append(f"| `{pid}` | `{pdf}` | {bancadas_str} |")
        md.append("")
    else:
        md.append("✅ Nenhuma página de treino precisa ser excluída.")
        md.append("")

    md_texto = "\n".join(md) + "\n"

    # Grava relatório Markdown
    with open(caminho_saida_md, "w", encoding="utf-8") as f:
        f.write(md_texto)

    # Exibe resumo no terminal
    print("=" * 72)
    print("AUDITORIA DE BANCADAS DE TREINO E MEDIÇÃO CONCLUÍDA COM SUCESSO")
    print("=" * 72)
    print(f"Relatório Markdown gravado em: {caminho_saida_md}")
    print(f"Lista de exclusão gravada em:  {caminho_saida_txt}")
    print("-" * 72)
    print("RESUMO EXECUTIVO (4 LINHAS):")
    print(f"1. {resumo_l1}")
    print(f"2. {resumo_l2}")
    print(f"3. {resumo_l3}")
    print(f"4. {resumo_l4}")
    print("=" * 72)


if __name__ == "__main__":
    main()
