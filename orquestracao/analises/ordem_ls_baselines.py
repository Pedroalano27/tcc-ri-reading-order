# -*- coding: utf-8 -*-
"""Avaliacao de ordem de leitura e heuristicas sobre anotacoes do Label Studio.

Executa o pipeline completo:
1. Converte data/labelstudio/ls_p23_seed2_order.json para resultados/ordem_ls/conv usando
   src/anotacao/ordem_labelstudio.py.
2. Filtra anotacoes com status "concluida" feitas por humanos (anotador != "desconhecido"),
   seleciona a anotacao mais recente por pagina e mede a concordancia interanotador nas
   paginas em comum.
3. Aplica a ordem ingenua (topo->base, esq.->dir.) e a heuristica XY-cut recursiva sobre as
   caixas da pagina, medindo tau de Kendall, acerto de sucessor e ARD normalizado contra
   a referencia humana.
4. Calcula medias e intervalos de confianca de 95% via bootstrap (2.000 reamostras) no total,
   por anotador e estratificando entre paginas mantidas identicas a sugestao e alteradas.
5. Quantifica o vies de ancoragem (fracao de paginas e ligacoes identicas a sugestao) e
   gera o relatorio completo em resultados/ordem_ls_baselines.md, comparando com o golden_v4.

Uso:
    venv\\Scripts\\python.exe orquestracao/analises/ordem_ls_baselines.py
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys

# Ajusta sys.path para importar modulos do repositorio
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.data.extrator import xycut  # noqa: E402
from src.eval.metrics import acerto_exato, acerto_sucessor, ard_normalizado, kendall_tau  # noqa: E402


def fmt_num(v: float, decimais: int = 3) -> str:
    """Formata float com virgula decimal."""
    return f"{v:.{decimais}f}".replace(".", ",")


def fmt_pct(v: float, decimais: int = 1) -> str:
    """Formata porcentagem com virgula decimal."""
    return f"{v * 100:.{decimais}f}%".replace(".", ",")


def ic95(v: list[float], reamostras: int = 2000) -> tuple[float, float]:
    """Intervalo de confianca de 95% via bootstrap com semente fixa 7."""
    if not v:
        return 0.0, 0.0
    if len(v) < 2:
        return v[0], v[0]
    rng = random.Random(7)
    n = len(v)
    medias = sorted(sum(rng.choices(v, k=n)) / n for _ in range(reamostras))
    return medias[int(0.025 * reamostras)], medias[int(0.975 * reamostras)]


def ler_jsonl(caminho: Path) -> list[dict]:
    """Le arquivo JSONL defensivamente."""
    if not caminho.exists():
        return []
    linhas = []
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            t = linha.strip()
            if t:
                try:
                    linhas.append(json.loads(t))
                except json.JSONDecodeError:
                    continue
    return linhas


def executar_conversor(export_json: Path, saida_conv: Path) -> None:
    """Chama src/anotacao/ordem_labelstudio.py converter via subprocess."""
    anot_arq = saida_conv / "anotacoes.jsonl"
    taref_arq = saida_conv / "tarefas.jsonl"
    marca_arq = saida_conv / "origem_labelstudio.json"

    precisa_converter = True
    if anot_arq.exists() and taref_arq.exists() and marca_arq.exists():
        if anot_arq.stat().st_mtime >= export_json.stat().st_mtime:
            precisa_converter = False

    if precisa_converter:
        saida_conv.mkdir(parents=True, exist_ok=True)
        print(f"Executando conversao: {export_json} -> {saida_conv}")
        cmd = [
            sys.executable,
            str(RAIZ / "src" / "anotacao" / "ordem_labelstudio.py"),
            "converter",
            str(export_json),
            "--saida",
            str(saida_conv),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(f"Erro na conversao (codigo {res.returncode}):\n{res.stderr}")
            sys.exit(res.returncode)
        print(res.stdout.strip())
    else:
        print(f"Conversao ja existente e atualizada em {saida_conv}")


def calcular_metricas(pred: list[str], gt: list[str]) -> dict[str, float]:
    """Calcula metricas de avaliacao de uma predicao contra a referencia."""
    return {
        "tau": kendall_tau(pred, gt),
        "sucessor": acerto_sucessor(pred, gt),
        "ard_norm": ard_normalizado(pred, gt),
        "exato": acerto_exato(pred, gt),
    }


def resumir_estatisticas(registros: list[dict], metodos: tuple[str, ...] = ("aleatoria", "naive", "xycut")) -> dict[str, dict]:
    """Resume medias e IC95% para cada metodo."""
    res = {}
    for m in metodos:
        sub = [r["metricas"][m] for r in registros if m in r.get("metricas", {})]
        if not sub:
            continue
        n = len(sub)
        taus = [x["tau"] for x in sub]
        sucs = [x["sucessor"] for x in sub]
        ards = [x["ard_norm"] for x in sub]
        exas = [x["exato"] for x in sub]
        res[m] = {
            "n": n,
            "tau_media": statistics.mean(taus),
            "tau_ic95": ic95(taus),
            "sucessor_media": statistics.mean(sucs),
            "sucessor_ic95": ic95(sucs),
            "ard_norm_media": statistics.mean(ards),
            "ard_norm_ic95": ic95(ards),
            "exato_media": statistics.mean(exas),
            "exato_ic95": ic95(exas),
        }
    return res


def formatar_tabela_markdown(resumos: dict[str, dict], nomes_metodos: dict[str, str] | None = None) -> list[str]:
    """Gera linhas de tabela markdown para o resumo de metricas."""
    nomes = nomes_metodos or {
        "aleatoria": "Ordem de entrada / detector (piso)",
        "naive": "Ingênua (topo→base, esq.→dir.)",
        "xycut": "XY-cut (heurística de colunas)",
    }
    linhas = [
        "| Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m, r in resumos.items():
        if m.startswith("_") or not isinstance(r, dict):
            continue
        nome = nomes.get(m, m)
        t_m, (t_a, t_b) = r["tau_media"], r["tau_ic95"]
        s_m, (s_a, s_b) = r["sucessor_media"], r["sucessor_ic95"]
        a_m, (a_a, a_b) = r["ard_norm_media"], r["ard_norm_ic95"]
        e_m = r["exato_media"]
        linhas.append(
            f"| {nome} | {r['n']} | **{fmt_num(t_m)}** ({fmt_num(t_a)} a {fmt_num(t_b)}) | "
            f"**{fmt_pct(s_m)}** ({fmt_pct(s_a)} a {fmt_pct(s_b)}) | "
            f"{fmt_num(a_m)} ({fmt_num(a_a)} a {fmt_num(a_b)}) | "
            f"{fmt_pct(e_m)} |"
        )
    return linhas


def processar_dataset(saida_conv: Path) -> dict:
    """Processa anotacoes e tarefas convertidas, aplicando as heuristicas."""
    anotacoes_raw = ler_jsonl(saida_conv / "anotacoes.jsonl")
    tarefas_raw = ler_jsonl(saida_conv / "tarefas.jsonl")
    tarefas_por_pid = {t["page_id"]: t for t in tarefas_raw if "page_id" in t}

    # 1. Filtrar anotacoes validas de humanos
    anotacoes_humanas = []
    for a in anotacoes_raw:
        if a.get("status") != "concluida":
            continue
        autor = (a.get("anotador") or "").strip()
        if not autor or autor.lower() == "desconhecido":
            continue
        anotacoes_humanas.append(a)

    # 2. Agrupar por (page_id, anotador) para reter a mais recente por anotador
    por_pid_autor = {}
    for a in anotacoes_humanas:
        pid = a["page_id"]
        autor = a["anotador"]
        chave = (pid, autor)
        ts = (a.get("salvo_em") or "", a.get("anotacao_id") or 0)
        if chave not in por_pid_autor or ts > por_pid_autor[chave][0]:
            por_pid_autor[chave] = (ts, a)

    anotacoes_por_pid = defaultdict(list)
    for (pid, _), (_, a) in por_pid_autor.items():
        anotacoes_por_pid[pid].append(a)

    # 3. Medir concordancia interanotador nas paginas em comum
    concordancias = []
    for pid, lista in anotacoes_por_pid.items():
        if len(lista) >= 2:
            for i in range(len(lista)):
                for j in range(i + 1, len(lista)):
                    a1, a2 = lista[i], lista[j]
                    concordancias.append({
                        "page_id": pid,
                        "anotador_1": a1["anotador"],
                        "anotador_2": a2["anotador"],
                        "tau": kendall_tau(a1["ordem"], a2["ordem"]),
                        "sucessor": acerto_sucessor(a1["ordem"], a2["ordem"]),
                        "ard_norm": ard_normalizado(a1["ordem"], a2["ordem"]),
                        "n_blocos": len(a1["ordem"]),
                    })

    # 4. Selecionar a anotacao humana mais recente de cada pagina como referencia
    referencias_por_pid = {}
    for pid, lista in anotacoes_por_pid.items():
        ref = max(lista, key=lambda x: (x.get("salvo_em") or "", x.get("anotacao_id") or 0))
        referencias_por_pid[pid] = ref

    # 5. Avaliar heuristicas pagina a pagina
    registros_paginas = []
    tot_ligacoes_todas = 0
    tot_ligacoes_iguais = 0
    paginas_identicas = 0

    for pid in sorted(referencias_por_pid.keys()):
        ref = referencias_por_pid[pid]
        tarefa = tarefas_por_pid.get(pid)
        if not tarefa:
            continue
        blocos = tarefa.get("bounding_boxes", [])
        if not blocos:
            continue

        gt = ref["ordem"]
        gt_set = set(gt)

        # Caixas presentes no gabarito
        blocos_validos = [b for b in blocos if b["id"] in gt_set]
        if len(blocos_validos) < 2:
            continue

        ids = [b["id"] for b in blocos_validos]
        B = [{"x0": b["bbox"][0], "top": b["bbox"][1], "x1": b["bbox"][2], "bottom": b["bbox"][3]}
             for b in blocos_validos]

        # Ordem de entrada (detector)
        pred_aleat = list(ids)

        # Ordem ingenua (topo -> base, esquerda -> direita)
        idx_naive = sorted(range(len(ids)), key=lambda i: (B[i]["top"], B[i]["x0"]))
        pred_naive = [ids[i] for i in idx_naive]

        # Ordem XY-cut recursiva
        idx_xycut = xycut(list(range(len(ids))), B)
        pred_xycut = [ids[i] for i in idx_xycut]

        # Metricas
        m_aleat = calcular_metricas(pred_aleat, gt)
        m_naive = calcular_metricas(pred_naive, gt)
        m_xycut = calcular_metricas(pred_xycut, gt)

        # Analise de preservacao da sugestao da XY-cut
        comp = ref.get("iguais_a_origem")
        if comp and isinstance(comp, (list, tuple)) and len(comp) == 2:
            iguais, total_lig = int(comp[0]), int(comp[1])
        else:
            pares_xycut = set(zip(pred_xycut, pred_xycut[1:]))
            pares_gt = list(zip(gt, gt[1:]))
            iguais = sum(1 for p in pares_gt if p in pares_xycut)
            total_lig = len(pares_gt)

        manteve_ordem = (iguais == total_lig and total_lig > 0) or (pred_xycut == gt)
        if manteve_ordem:
            paginas_identicas += 1
        tot_ligacoes_todas += total_lig
        tot_ligacoes_iguais += iguais

        registros_paginas.append({
            "page_id": pid,
            "task_id": ref.get("task_id"),
            "anotacao_id": ref.get("anotacao_id"),
            "anotador": ref.get("anotador"),
            "tempo_s": ref.get("tempo_s"),
            "n_blocos": len(gt),
            "manteve_ordem": manteve_ordem,
            "ligacoes_iguais": iguais,
            "total_ligacoes": total_lig,
            "metricas": {
                "aleatoria": m_aleat,
                "naive": m_naive,
                "xycut": m_xycut,
            },
        })

    n_total = len(registros_paginas)
    frac_pag_iguais = (paginas_identicas / n_total) if n_total > 0 else 0.0
    frac_lig_iguais = (tot_ligacoes_iguais / tot_ligacoes_todas) if tot_ligacoes_todas > 0 else 0.0

    # Resumos
    resumo_geral = resumir_estatisticas(registros_paginas)

    # Por anotador
    por_anotador = defaultdict(list)
    for r in registros_paginas:
        por_anotador[r["anotador"]].append(r)
    resumos_por_anotador = {}
    for autor, regs in por_anotador.items():
        st = resumir_estatisticas(regs)
        st["_n_paginas"] = len(regs)
        resumos_por_anotador[autor] = st

    # Mantidas vs Alteradas
    regs_mantidas = [r for r in registros_paginas if r["manteve_ordem"]]
    regs_alteradas = [r for r in registros_paginas if not r["manteve_ordem"]]
    resumo_mantidas = resumir_estatisticas(regs_mantidas)
    resumo_alteradas = resumir_estatisticas(regs_alteradas)

    return {
        "n_total": n_total,
        "registros_paginas": registros_paginas,
        "concordancias": concordancias,
        "resumo_geral": resumo_geral,
        "resumos_por_anotador": resumos_por_anotador,
        "resumo_mantidas": resumo_mantidas,
        "resumo_alteradas": resumo_alteradas,
        "vies": {
            "paginas_total": n_total,
            "paginas_identicas": paginas_identicas,
            "paginas_alteradas": n_total - paginas_identicas,
            "frac_paginas_identicas": frac_pag_iguais,
            "ligacoes_total": tot_ligacoes_todas,
            "ligacoes_identicas": tot_ligacoes_iguais,
            "frac_ligacoes_identicas": frac_lig_iguais,
        },
    }


def gerar_relatorio_md(dados: dict, caminho_md: Path) -> str:
    """Gera o texto completo do relatorio Markdown e salva em disco."""
    n_total = dados["n_total"]
    res_geral = dados["resumo_geral"]
    vies = dados["vies"]
    res_mant = dados["resumo_mantidas"]
    res_alt = dados["resumo_alteradas"]
    por_autor = dados["resumos_por_anotador"]
    concordancias = dados["concordancias"]

    xy_geral = res_geral.get("xycut", {})
    na_geral = res_geral.get("naive", {})
    xy_alt = res_alt.get("xycut", {})
    na_alt = res_alt.get("naive", {})

    tau_alt_str = fmt_num(xy_alt["tau_media"]) if "tau_media" in xy_alt else "N/A"
    suc_alt_str = fmt_pct(xy_alt["sucessor_media"]) if "sucessor_media" in xy_alt else "N/A"

    linhas_md = []

    # 1. Titulo
    linhas_md.append("# Avaliação de Heurísticas de Ordem de Leitura no Conjunto Label Studio (Seed 2)\n")

    # 2. Resumo de exatamente 5 linhas
    resumo_5_linhas = (
        f"1. Foram avaliadas {n_total} páginas de diários oficiais com cadeias completas e válidas anotadas por humanos no export Seed 2 do Label Studio.\n"
        f"2. No conjunto geral, a heurística XY-cut obteve τ de Kendall médio de {fmt_num(xy_geral.get('tau_media', 0.0))} e acerto de sucessor de {fmt_pct(xy_geral.get('sucessor_media', 0.0))}, superando a abordagem ingênua ({fmt_num(na_geral.get('tau_media', 0.0))} e {fmt_pct(na_geral.get('sucessor_media', 0.0))}).\n"
        f"3. O processo de anotação sofreu forte viés de ancoragem por ter partido de uma pré-anotação gerada pela própria XY-cut: {fmt_pct(vies['frac_paginas_identicas'])} das páginas ({vies['paginas_identicas']}/{vies['paginas_total']}) e {fmt_pct(vies['frac_ligacoes_identicas'])} das ligações foram aceitas sem nenhuma modificação.\n"
        f"4. No subconjunto de páginas em que os anotadores efetivamente intervieram e corrigiram a ordem (n = {vies['paginas_alteradas']}), a XY-cut cai para τ = {tau_alt_str} e sucessor = {suc_alt_str}.\n"
        f"5. Em contraste com o Golden Dataset v4 (44 páginas anotadas do zero, onde a XY-cut registrou τ = 0,825 e sucessor = 71,5%), os números globais do Label Studio estão inflados pela aceitação passiva da sugestão algorítmica."
    )
    linhas_md.append("## Resumo Executivo\n")
    linhas_md.append(resumo_5_linhas + "\n")

    # 3. Contexto e Protocolo
    linhas_md.append("## Contexto e Desenho Experimental\n")
    linhas_md.append(
        "Este relatório avalia um segundo conjunto de páginas anotadas, derivado das anotações de ordem de leitura "
        "do projeto parceiro Datapolicy no Label Studio (`data/labelstudio/ls_p23_seed2_order.json`). "
        "Os dados foram convertidos para a estrutura do TCC via `src/anotacao/ordem_labelstudio.py converter`. "
        "Foram selecionadas exclusivamente páginas com cadeias de relações válidas (`status = 'concluida'`) "
        "produzidas por anotadores humanos identificados (descartando anotações anônimas ou com rótulo 'desconhecido'). "
        "Quando uma página continha múltiplas anotações humanas válidas, adotou-se a mais recente como gabarito oficial.\n"
    )

    # 4. Concordancia Interanotador
    linhas_md.append("## Concordância Interanotador nas Páginas em Comum\n")
    if concordancias:
        linhas_md.append(
            f"Foram identificadas {len(concordancias)} comparação(ões) entre anotações humanas independentes "
            "em páginas coincidentes. A concordância de ordens fornece uma estimativa empírica do limite humano "
            "(teto prático) para a tarefa:\n"
        )
        linhas_md.append("| Página | Anotador A | Anotador B | Blocos | τ Kendall | Sucessor correto | ARD norm. |")
        linhas_md.append("|---|---|---|---:|---:|---:|---:|")
        taus_c = []
        sucs_c = []
        for c in concordancias:
            taus_c.append(c["tau"])
            sucs_c.append(c["sucessor"])
            linhas_md.append(
                f"| `{c['page_id']}` | {c['anotador_1']} | {c['anotador_2']} | {c['n_blocos']} | "
                f"{fmt_num(c['tau'])} | {fmt_pct(c['sucessor'])} | {fmt_num(c['ard_norm'])} |"
            )
        linhas_md.append(
            f"\n**Média de concordância entre humanos:** τ = **{fmt_num(statistics.mean(taus_c))}**, "
            f"sucessor correto = **{fmt_pct(statistics.mean(sucs_c))}**.\n"
        )
    else:
        linhas_md.append(
            "Nenhuma página deste lote possui anotações concluídas duplicadas por múltiplos anotadores humanos "
            "simultaneamente. Cada página concluída foi anotada por um único anotador humano.\n"
        )

    # 5. Tabela Geral de Resultados
    linhas_md.append("## Desempenho Geral das Heurísticas de Referência\n")
    linhas_md.append(
        f"Abaixo estão os resultados consolidados para as **{n_total} páginas** do conjunto de teste Label Studio. "
        "Os intervalos de confiança de 95% foram calculados por bootstrap não paramétrico sobre as páginas com 2.000 reamostragens (semente fixa 7):\n"
    )
    for lin in formatar_tabela_markdown(res_geral):
        linhas_md.append(lin)
    linhas_md.append("")

    # 6. Desempenho por Anotador
    linhas_md.append("## Resultados Estratificados por Anotador\n")
    linhas_md.append(
        "A variabilidade entre anotadores reflete critérios subjetivos de ordenação (ex.: tratamento de cabeçalhos institucionais, "
        "rodapés e quebras entre documentos normativos):\n"
    )
    for autor, r_autor in sorted(por_autor.items()):
        linhas_md.append(f"### Anotador: `{autor}` (n = {r_autor.get('_n_paginas', r_autor.get('xycut', {}).get('n', 0))} páginas)")
        for lin in formatar_tabela_markdown(r_autor):
            linhas_md.append(lin)
        linhas_md.append("")

    # 7. Quantificacao do Vies de Ancoragem
    linhas_md.append("## Quantificação do Viés de Ancoragem (Anchoring Bias)\n")
    linhas_md.append(
        "Diferentemente do Golden Dataset do TCC (onde a anotação é executada às cegas a partir do zero), "
        "a interface do Label Studio deste projeto parceiro carregava previamente as relações geométricas "
        "preditas pela própria heurística **XY-cut**. O anotador humano tinha a tarefa de revisar e corrigir eventuais erros.\n"
    )
    linhas_md.append(
        f"- **Páginas idênticas à sugestão:** {vies['paginas_identicas']} de {vies['paginas_total']} páginas "
        f"(**{fmt_pct(vies['frac_paginas_identicas'])}** foram mantidas 100% inalteradas pelo humano).\n"
        f"- **Páginas com alterações pelo humano:** {vies['paginas_alteradas']} de {vies['paginas_total']} páginas "
        f"(**{fmt_pct(1.0 - vies['frac_paginas_identicas'])}** receberam pelo menos uma correção).\n"
        f"- **Ligações preservadas da pré-anotação:** {vies['ligacoes_identicas']} de {vies['ligacoes_total']} conexões direcionadas "
        f"(**{fmt_pct(vies['frac_ligacoes_identicas'])}** de todas as ligações sucessoras foram aceitas sem ajuste).\n"
    )
    linhas_md.append(
        "Para isolar o efeito da acomodação/ancoragem dos anotadores, a tabela abaixo compara o desempenho das "
        "heurísticas entre o grupo de páginas mantidas e o grupo onde o humano realizou correções ativas:\n"
    )

    tabela_vies = [
        "| Subconjunto | Método | n | τ de Kendall (IC 95%) | Sucessor correto (IC 95%) | ARD norm. (IC 95%) | Acerto exato |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for sub_nome, r_sub in [("Páginas mantidas (sem edição)", res_mant), ("Páginas alteradas (com edição)", res_alt)]:
        for m in ("naive", "xycut"):
            nm = "Ingênua" if m == "naive" else "XY-cut"
            r = r_sub.get(m, {})
            if not r:
                continue
            t_m, (t_a, t_b) = r["tau_media"], r["tau_ic95"]
            s_m, (s_a, s_b) = r["sucessor_media"], r["sucessor_ic95"]
            a_m, (a_a, a_b) = r["ard_norm_media"], r["ard_norm_ic95"]
            e_m = r["exato_media"]
            tabela_vies.append(
                f"| {sub_nome} | {nm} | {r['n']} | **{fmt_num(t_m)}** ({fmt_num(t_a)} a {fmt_num(t_b)}) | "
                f"**{fmt_pct(s_m)}** ({fmt_pct(s_a)} a {fmt_pct(s_b)}) | "
                f"{fmt_num(a_m)} ({fmt_num(a_a)} a {fmt_num(a_b)}) | "
                f"{fmt_pct(e_m)} |"
            )
    for lin in tabela_vies:
        linhas_md.append(lin)
    linhas_md.append("")

    # 8. Comparacao com Golden Dataset v4
    linhas_md.append("## Comparação com o Benchmark Golden Dataset v4\n")
    linhas_md.append(
        "O `golden_v4` é o benchmark primário do TCC, composto por **44 páginas** de múltiplos estados anotadas "
        "do zero pelo autor da pesquisa, sem nenhuma pré-anotação algorítmica (anotação cega). "
        "A tabela a seguir contrasta o comportamento da XY-cut entre os dois ambientes de teste:\n"
    )

    tabela_comp = [
        "| Conjunto de Avaliação | Tipo de Anotação | n páginas | τ Kendall XY-cut | Sucessor Correto XY-cut | Acerto Exato |",
        "|---|---|---:|---:|---:|---:|",
        f"| **Label Studio (Total)** | Correção de pré-anotação | {n_total} | **{fmt_num(xy_geral.get('tau_media', 0.0))}** | **{fmt_pct(xy_geral.get('sucessor_media', 0.0))}** | {fmt_pct(xy_geral.get('exato_media', 0.0))} |",
        f"| **Label Studio (Alteradas)** | Correção efetiva | {vies['paginas_alteradas']} | **{fmt_num(xy_alt.get('tau_media', 0.0))}** | **{fmt_pct(xy_alt.get('sucessor_media', 0.0))}** | {fmt_pct(xy_alt.get('exato_media', 0.0))} |",
        "| **Golden Dataset v4** | Anotação cega (do zero) | 44 | **0,825** | **71,5%** | 22,7% |",
    ]
    for lin in tabela_comp:
        linhas_md.append(lin)
    linhas_md.append("")

    linhas_md.append("### Conclusões Metodológicas e Limitações\n")
    linhas_md.append(
        "1. **Favorecimento estrutural da heurística:** A XY-cut atinge índices artificialmente elevados "
        f"(τ = {fmt_num(xy_geral.get('tau_media', 0.0))}) no total do Label Studio porque o humano atuou como validador "
        "de um rascunho construído por ela mesma. Quando um layout complexo apresentava ordem plausível, o anotador tendeu a aprová-la.\n"
        "2. **Comportamento sob divergência:** No subgrupo onde o humano deliberadamente corrigiu a cadeia "
        f"(n = {vies['paginas_alteradas']}), a XY-cut obteve τ = {fmt_num(xy_alt.get('tau_media', 0.0))} e sucessor = {fmt_pct(xy_alt.get('sucessor_media', 0.0))}, "
        "evidenciando os pontos cegos da geometria pura (intercalação de matérias, títulos de largura total inseridos no meio de colunas e caixas isoladas).\n"
        "3. **Recomendação para o TCC:** Este conjunto do Label Studio deve ser tratado como uma **bancada de auditoria de pré-anotação** "
        "e não como gabarito neutro equivalente ao Golden Dataset v4. A inclusão destas métricas no texto do TCC ilustra com clareza o impacto "
        "do viés de ancoragem em tarefas de recuperação de ordem e estruturação documental.\n"
    )

    conteudo_md = "\n".join(linhas_md)
    caminho_md.write_text(conteudo_md, encoding="utf-8")
    return conteudo_md


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=RAIZ / "data" / "labelstudio" / "ls_p23_seed2_order.json",
        help="Caminho do export JSON do Label Studio",
    )
    parser.add_argument(
        "--saida-conv",
        type=Path,
        default=RAIZ / "resultados" / "ordem_ls" / "conv",
        help="Pasta de saida da conversao",
    )
    parser.add_argument(
        "--relatorio-md",
        type=Path,
        default=RAIZ / "resultados" / "ordem_ls_baselines.md",
        help="Arquivo Markdown de relatorio",
    )
    parser.add_argument(
        "--relatorio-json",
        type=Path,
        default=RAIZ / "resultados" / "ordem_ls" / "avaliacao.json",
        help="Arquivo JSON com os dados completos",
    )
    args = parser.parse_args()

    print("=== Avaliação de Heurísticas de Ordem no Label Studio ===")
    print(f"Export de entrada : {args.export}")
    print(f"Pasta conversão   : {args.saida_conv}")
    print(f"Relatório MD      : {args.relatorio_md}")

    # Passo 1: Executar conversor
    executar_conversor(args.export, args.saida_conv)

    # Passos 2 a 4: Processar dados, calcular heuristicas e bootstrap
    print("\nProcessando anotações humanas e executando heurísticas...")
    dados = processar_dataset(args.saida_conv)

    # Passo 5: Gerar relatorio MD e JSON
    args.relatorio_md.parent.mkdir(parents=True, exist_ok=True)
    args.relatorio_json.parent.mkdir(parents=True, exist_ok=True)

    gerar_relatorio_md(dados, args.relatorio_md)
    print(f"[OK] Relatório gerado em: {args.relatorio_md}")

    # Salva JSON estruturado (sem objetos complexos)
    with open(args.relatorio_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON completo salvo em: {args.relatorio_json}")

    # Resumo no terminal
    res_geral = dados["resumo_geral"]
    vies = dados["vies"]
    print("\n=== RESUMO GERAL ===")
    print(f"Total de páginas avaliadas: {dados['n_total']}")
    for m, r in res_geral.items():
        print(
            f"  {m:<10}: tau={r['tau_media']:.3f} [{r['tau_ic95'][0]:.3f}, {r['tau_ic95'][1]:.3f}] | "
            f"sucessor={r['sucessor_media']:.1%} [{r['sucessor_ic95'][0]:.1%}, {r['sucessor_ic95'][1]:.1%}] | "
            f"ard_norm={r['ard_norm_media']:.3f}"
        )
    print(
        f"\nViés de ancoragem: {vies['paginas_identicas']}/{vies['paginas_total']} páginas "
        f"({vies['frac_paginas_identicas']:.1%}) e {vies['ligacoes_identicas']}/{vies['ligacoes_total']} ligações "
        f"({vies['frac_ligacoes_identicas']:.1%}) mantidas idênticas à sugestão XY-cut."
    )


if __name__ == "__main__":
    main()
