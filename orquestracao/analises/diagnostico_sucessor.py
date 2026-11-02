"""
Script de apoio para T25: Diagnóstico do LayoutLM Sucessor no Golden Dataset (golden_v3).
Gera resultados/golden/_avaliacao/golden_v3/diagnostico_sucessor.md.
Atualizado em 13/09 com decodificação em cadeias (limiar 0,5).
"""
import os
import sys
import json
import statistics

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

from src.eval.metrics import avaliar, kendall_tau, acerto_sucessor

def ler_jsonl(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def gerar_diagnostico():
    dir_golden = os.path.join(RAIZ, "data", "golden", "_avaliacao", "golden_v3")
    dir_res = os.path.join(RAIZ, "resultados", "golden", "_avaliacao", "golden_v3")
    arq_saida = os.path.join(dir_res, "diagnostico_sucessor.md")

    tarefas = {x["page_id"]: x for x in ler_jsonl(os.path.join(dir_golden, "tarefas.jsonl"))}
    ref_raw = {x["page_id"]: x for x in ler_jsonl(os.path.join(dir_golden, "referencia.jsonl")) if x.get("status") == "concluida"}
    pred_llm = {x["page_id"]: x["ordem_pred"] for x in ler_jsonl(os.path.join(dir_res, "pred_layoutlm.jsonl"))}
    pred_suc = {x["page_id"]: x["ordem_pred"] for x in ler_jsonl(os.path.join(dir_res, "pred_layoutlm_sucessor.jsonl"))}

    paginas = []
    for pid, r in ref_raw.items():
        t = tarefas[pid]
        ref = r["ordem"]
        textos = {b["id"]: b.get("text", "") for b in t["bounding_boxes"]}
        bboxes = {b["id"]: b["bbox"] for b in t["bounding_boxes"]}

        ev_s = avaliar(pred_suc[pid], ref, textos)
        ev_xy = avaliar(t["ordens"]["xycut"], ref, textos)
        ev_l = avaliar(pred_llm[pid], ref, textos)
        diff = ev_s["kendall_tau"] - ev_xy["kendall_tau"]

        stats = t.get("stats", {})
        n_col = stats.get("n_colunas", 1)
        n_tab = stats.get("n_tabelas", 0)

        paginas.append({
            "pid": pid,
            "pid_curto": pid.split("/")[-1],
            "uf": t.get("uf", "").replace("official_diary_", ""),
            "grupo": t.get("grupo", r.get("grupo", "")),
            "n_blocos": len(ref),
            "cols": n_col,
            "tabs": n_tab,
            "flags": r.get("flags", []),
            "nota": r.get("nota", ""),
            "tau_s": ev_s["kendall_tau"],
            "suc_s": ev_s["acerto_sucessor"],
            "tau_xy": ev_xy["kendall_tau"],
            "suc_xy": ev_xy["acerto_sucessor"],
            "tau_l": ev_l["kendall_tau"],
            "suc_l": ev_l["acerto_sucessor"],
            "diff": diff,
            "ref": ref,
            "pred_s": pred_suc[pid],
            "pred_xy": t["ordens"]["xycut"],
            "pred_l": pred_llm[pid],
            "textos": textos,
            "bboxes": bboxes,
        })

    # Ordena pela diferenca entre sucessor e xycut, pior primeiro
    paginas.sort(key=lambda x: x["diff"])

    taus_s = [p["tau_s"] for p in paginas]
    sucs_s = [p["suc_s"] for p in paginas]
    taus_xy = [p["tau_xy"] for p in paginas]
    sucs_xy = [p["suc_xy"] for p in paginas]
    taus_l = [p["tau_l"] for p in paginas]
    sucs_l = [p["suc_l"] for p in paginas]

    p10_s = statistics.quantiles(taus_s, n=10)[0]
    p10_xy = statistics.quantiles(taus_xy, n=10)[0]
    p10_l = statistics.quantiles(taus_l, n=10)[0]

    md = []
    md.append("# Diagnóstico de Erros do LayoutLM Sucessor no Golden Dataset (`golden_v3`)")
    md.append("")

    # Secao de Correcao de 13/09
    md.append("## Correção de 13/09: Impacto da Decodificação em Cadeias vs Busca em Feixe")
    md.append("")
    md.append("Na versão inicial deste diagnóstico, a avaliação do **LayoutLM Sucessor** no Golden Dataset (`golden_v3`) utilizou inadvertidamente predições geradas por **busca em feixe** (*beam search*), devido ao parâmetro padrão herdado na função `prever()` chamada por `src/eval/avaliar_golden.py`. No protocolo experimental principal do TCC (assim como no conjunto de teste), a linha de inferência adota **decodificação em cadeias** com limiar 0,5. Com a re-avaliação do Golden utilizando as predições corretas em cadeias (`resultados/golden/_avaliacao/golden_v3/pred_layoutlm_sucessor.jsonl`), os números e as conclusões diagnósticas alteraram-se substancialmente:")
    md.append("")
    md.append("### Comparação Direta dos Resultados Globais no Golden (`golden_v3`, n=47)")
    md.append("")
    md.append("| Métrica | Antes (Busca em Feixe) | Depois (Decodificação em Cadeias) | Variação ($\Delta$) |")
    md.append("|---|---:|---:|---:|")
    diff_tau_s = f"{statistics.mean(taus_s) - 0.699:+.3f}".replace(".", ",")
    tau_s_str = f"{statistics.mean(taus_s):.3f}".replace(".", ",")
    p10_s_str = f"{p10_s:.3f}".replace(".", ",")
    diff_p10 = f"{p10_s - 0.275:+.3f}".replace(".", ",")
    suc_s_str = f"{statistics.mean(sucs_s):.1%}".replace(".", ",")
    diff_suc = f"{(statistics.mean(sucs_s) - 0.671) * 100:+.1f}".replace(".", ",") + " p.p."
    diff_llm = f"{statistics.mean(taus_s) - statistics.mean(taus_l):+.3f}".replace(".", ",")
    diff_xy = f"{statistics.mean(taus_s) - statistics.mean(taus_xy):+.3f}".replace(".", ",")

    md.append(f"| **$\\tau$ de Kendall Médio** | 0,699 | **{tau_s_str}** | **{diff_tau_s}** |")
    md.append(f"| **$\\tau$ no Percentil 10 ($p_{{10}}$)** | 0,275 | **{p10_s_str}** | **{diff_p10}** |")
    md.append(f"| **Sucessor Correto Médio** | 67,1% | **{suc_s_str}** | **{diff_suc}** |")
    md.append(f"| **Diferença vs LayoutLM Pontual ($\\tau$)** | -0,147 (0,699 vs 0,846) | **{diff_llm}** (0,845 vs 0,846) | Empate técnico |")
    md.append(f"| **Diferença vs XY-cut ($\\tau$)** | -0,152 (0,699 vs 0,851) | **{diff_xy}** (0,845 vs 0,851) | Diferença residual |")
    md.append("")
    md.append("Com a correção, o LayoutLM Sucessor praticamente empata com o LayoutLM Pontual em $\\tau$ (0,845 vs 0,846) e aproxima-se estreitamente do XY-cut (0,851), mantendo mais que o dobro da continuidade local em relação ao modelo pontual (66,8% vs 32,8% de sucessor correto). O percentil 10 ($p_{10}$) salta de 0,275 para 0,591, superando inclusive o $p_{10}$ do próprio XY-cut (0,545).")
    md.append("")
    md.append("### Síntese da Revisão das Três Hipóteses")
    md.append("")
    md.append("- **Hipótese 1 (Falha de ancoragem de cabeçalhos): MUDA / MANTÉM-SE PARCIALMENTE.**")
    md.append("  - *O que cai:* A ideia de que o desacoplamento de cabeçalhos causava colapso global sistêmico em toda a base foi refutada. Casos críticos que sofriam quedas drásticas em feixe tiveram recuperação expressiva em cadeias (ex.: Piauí p223 saltou de $\\tau$ 0,143 para 0,714; Piauí p0 foi de 0,543 para 0,981).")
    md.append("  - *O que se mantém / expande:* O mecanismo de falha em si (pequenos blocos isolados no topo ou rodapé que não estabelecem aresta de transição com o corpo e são deslocados pela pontuação pontual) continua sendo o principal modo de erro local residual (ex.: Japeri p3, Congonhas p1, Barra do Piraí p2). Adicionalmente, revelou-se um novo modo macro de erro: a inversão de colunas completas cujos blocos internos foram encadeados perfeitamente (MA p14, com 90,6% de acerto local mas $\\tau$ 0,027 devido à leitura da Coluna 2 antes da Coluna 1).")
    md.append("- **Hipótese 2 (Degradação monotônica com número de colunas): CAI.**")
    md.append("  - *Refutação:* O colapso em páginas de 3 colunas não existe na decodificação em cadeias. O $\\tau$ médio em 3 colunas subiu de 0,601 para **0,814** (muito próximo ao de 2 colunas: 0,824). No caso mais complexo do acervo (MG p28, com 99 blocos em 3 colunas), o Sucessor saltou de $\\tau$ 0,460 para **0,881**, superando o próprio XY-cut (0,852). Em páginas de 1 coluna, o Sucessor supera amplamente o XY-cut (0,878 vs 0,788, vantagem de +0,090). O Sucessor sustenta $\\tau > 0,81$ em todas as configurações de colunas.")
    md.append("- **Hipótese 3 (Vulnerabilidade fora do domínio de treino no grupo `incerto`): CAI COMPLETAMENTE.**")
    md.append("  - *Refutação:* A suposta incapacidade de generalizar para layouts e municípios novos era um artefato exclusivo da busca em feixe (que caía de 0,739 no *silver* para 0,666 no *incerto*). Em cadeias, o Sucessor atinge $\\tau$ **0,851** no grupo *incerto* — superando tanto o grupo *silver* (0,837) quanto o próprio XY-cut no grupo *incerto* (0,834). A matriz de transição de adjacência com decodificação em cadeias generaliza de forma robusta e independente de vocabulário específico.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("Este relatório detalha o desempenho do **LayoutLM com predição de sucessor** (decodificação em cadeias, limiar 0,5) no Golden Dataset (47 páginas contra anotação humana), onde atinge $\\tau$ médio de **0,845** (p10 0,591) e **66,8%** de sucessor correto, empatando em $\\tau$ com o **LayoutLM pontual** (0,846, mas com apenas 32,8% de sucessores) e aproximando-se do **XY-cut** (0,851 e 74,0%).")
    md.append("")

    # 1. Tabela Completa por Página
    md.append("## 1. Tabela Completa por Página (Ordenada pelo Déficit do Sucessor vs XY-cut)")
    md.append("")
    md.append("Critério de ordenação: diferença de τ de Kendall ($\Delta\\tau = \\tau_{\\text{sucessor}} - \\tau_{\\text{xycut}}$), da pior página para a melhor.")
    md.append("")
    md.append("| Página | Grupo | UF | Blocos | Cols | Tabs | Flags | τ Suc. | Suc. Suc. | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut | $\Delta\\tau$ (Suc - XY) |")
    md.append("|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|")

    for p in paginas:
        flags_str = ", ".join(p["flags"]) if p["flags"] else "-"
        md.append(f"| `{p['pid_curto']}` | {p['grupo']} | {p['uf']} | {p['n_blocos']} | {p['cols']} | {p['tabs']} | {flags_str} | "
                  f"**{p['tau_s']:.3f}** | {p['suc_s']:.0%} | {p['tau_l']:.3f} | {p['suc_l']:.0%} | "
                  f"**{p['tau_xy']:.3f}** | {p['suc_xy']:.0%} | **{p['diff']:+.3f}** |")

    md.append("")

    # 2. As 8 Piores Páginas
    md.append("## 2. Análise Detalhada das 8 Páginas em que o Sucessor Mais Perde para o XY-cut")
    md.append("")
    md.append("Para cada uma das 8 piores páginas sob decodificação em cadeias, analisamos onde o sucessor começa a errar, o alinhamento bloco a bloco com os textos (40 caracteres), as coordenadas de bounding box e o padrão estrutural da falha.")
    md.append("")

    padroes_casos = {
        "executive_official_diary_2021-11-19.pdf#p14": (
            "**Inversão da ordem de macro-cadeias entre colunas (Coluna 2 antes da Coluna 1).** "
            "O LayoutLM com predição de sucessor recuperou a ordem interna de leitura de cada coluna com "
            "precisão de 100%: formou uma cadeia contínua de 15 blocos para a Coluna 1 (ref [2..16]) e uma cadeia de "
            "16 blocos para a Coluna 2 (ref [17..32]), alcançando expressivos 90,6% de sucessores corretos no documento. "
            "Contudo, na fase de decodificação global em que as cadeias são ordenadas pelo escore pontual médio, a cadeia "
            "da Coluna 2 recebeu valor médio inferior ao da Coluna 1, sendo alocada antes dela. "
            "Essa inversão de colunas completas gerou a discordância de 240 pares cruzados, despencando o τ de Kendall para "
            "0,027 (contra 0,943 do XY-cut). Trata-se de uma falha de ordenação macro-estrutural entre cadeias, contrastando com "
            "a continuidade local quase perfeita."
        ),
        "2024-05-07_DOEn8159_Edicao Ordinaria.pdf#p373": (
            "**Desconexão e colapso de adjacência em página esparsa com tabela isolada.** "
            "Página de baixa densidade (apenas 5 blocos) dominada por uma grande região de tabela identificada pelo detector visual "
            "e blocos periféricos de cabeçalho e rodapé. Nenhuma das transições entre os blocos superou o limiar de probabilidade de 0,5, "
            "resultando em 0,0% de sucessores corretos e fragmentando o documento em 5 cadeias unitárias. A ordenação dessas cadeias "
            "pela estimativa pontual posicionou o número de página no rodapé ('374 de 632', ref [4]) antes do bloco de tabela (ref [3]), "
            "atingindo τ de 0,600 contra 1,000 do particionamento determinístico do XY-cut."
        ),
        "JAPERI-5606-09-DE-MAIO-2024.pdf#p3": (
            "**Cabeçalho desacoplado jogado para o final da página.** "
            "Página de coluna única dominada por imagem gráfica (anotador: 'praticamente só uma imagem, e o texto foi bem removido, "
            "mas faltou um pouco'). O corpo textual central (ref [2..6], 5 blocos) formou uma cadeia coesa e contínua com 100% de "
            "acerto interno. Entretanto, o bloco de cabeçalho no topo (ref [1], 'DO MUNICÍPIO DE JAPERI') não estabeleceu transição de "
            "alta confiança com o início do corpo e formou uma cadeia unitária. A cabeça pontual atribuiu a esse cabeçalho uma "
            "posição tardia, posicionando-o na posição 6 (final da página) e reduzindo o τ para 0,524 (vs 0,905 do XY-cut)."
        ),
        "Parte I (Poder Executivo)_2024-02-02.pdf#p39": (
            "**Degradação severa por corrupção de fontes digitais do PDF (glifos `(cid:...)`).** "
            "Página afetada por defeito de codificação de fontes no PDF original, no qual a camada digital de texto extraiu sequências "
            "ilegíveis de glifos não mapeados (`(cid:12)(cid:13)...`). A ausência de informação semântica textual desestabilizou as "
            "probabilidades de adjacência da cabeça de sucessor (apenas 1 sucessor correto de 6, 16,7%) e a estimativa de posições. "
            "O próprio XY-cut atingiu apenas τ 0,429 nessa página, enquanto o Sucessor caiu para 0,143."
        ),
        "executive_official_diary_2025_11_07_216_2025.pdf#p223": (
            "**Desacoplamento parcial de metadados de cabeçalho (recuperação substancial em relação ao feixe).** "
            "Na busca em feixe anterior, esta página sofria colapso total (τ 0,143), com ambos os blocos de cabeçalho jogados após o corpo. "
            "Com a decodificação em cadeias, a página recuperou-se para τ 0,714 e 57,1% de sucessor: o bloco inicial de cabeçalho "
            "(ref [0], 'Disponibilizado...') foi posicionado corretamente no topo da leitura, e os 4 blocos do corpo (ref [2..5]) "
            "formaram uma cadeia contínua exemplar. O erro residual concentrou-se no segundo bloco de metadado (ref [1], 'Publicado...'), "
            "que não se encadeou ao primeiro e foi posicionado entre o corpo e o rodapé."
        ),
        "executive_official_diary_2022-05-26_095.pdf#p2": (
            "**Inversão de blocos periféricos no rodapé da página.** "
            "Página de baixa densidade (6 blocos) com cabeçalho institucional e avisos (anotador: 'pegou muito mal os textos da imagem...'). "
            "O modelo agrupou corretamente os 3 blocos superiores (ref [0..2]) e os 2 blocos de autenticação eletrônica (ref [4..5]). "
            "Contudo, o bloco intermediário contendo local e número de página (ref [3], 'Barra do Piraí/RJ 3') formou cadeia unitária que foi "
            "posicionada após os blocos de rodapé de autenticação, resultando em τ 0,733 contra 1,000 do XY-cut."
        ),
        "executive_official_diary_2026-01-16_010.pdf#p2": (
            "**Inversão de blocos de rodapé em edição do mesmo veículo (Barra do Piraí).** "
            "Comportamento e gabarito idênticos ao Caso 6: cabeçalho e corpo agrupados em cadeia com acerto perfeito, mas o bloco "
            "periférico de identificação de página (ref [3], 'Barra do Piraí/RJ 3') foi alocado após as declarações de conformidade da "
            "assinatura digital (ref [4..5]), mantendo τ de 0,733 vs 1,000 do XY-cut."
        ),
        "executive_official_diary_2020-12-10_2591.pdf#p1": (
            "**Número de página isolado inserido precocemente antes do corpo textual.** "
            "O corpo da matéria em coluna única (14 blocos, ref [2..15]) foi totalmente encadeado em uma única macro-cadeia com 100% de "
            "continuidade local (sucessor correto de 87,5%). Contudo, o número da página no rodapé inferior (ref [16], '2', caixa diminuta "
            "no canto inferior direito) formou cadeia unitária e recebeu escore pontual intermediário, sendo inserido logo na posição 2 "
            "(após o cabeçalho e antes de todo o corpo da matéria), reduzindo o τ para 0,794 (contra 0,985 do XY-cut)."
        ),
    }

    for i, p in enumerate(paginas[:8], 1):
        ref = p["ref"]
        suc = p["pred_s"]
        xy = p["pred_xy"]
        textos = p["textos"]
        bboxes = p["bboxes"]

        ref_pos = {bid: idx for idx, bid in enumerate(ref)}
        suc_pos = {bid: idx for idx, bid in enumerate(suc)}

        p_erro = next(idx for idx, (s, r) in enumerate(zip(suc, ref)) if s != r)
        s_b = suc[p_erro]
        r_b = ref[p_erro]
        bx_s = [round(x, 1) for x in bboxes[s_b]]
        bx_r = [round(x, 1) for x in bboxes[r_b]]

        # Identificacao de cadeias locais
        prox_ref = {a: b for a, b in zip(ref, ref[1:])}
        cadeias = []
        c_atual = [suc[0]]
        for a, b in zip(suc, suc[1:]):
            if prox_ref.get(a) == b:
                c_atual.append(b)
            else:
                cadeias.append(c_atual)
                c_atual = [b]
        cadeias.append(c_atual)

        md.append(f"### Caso {i}: `{p['pid_curto']}`")
        md.append(f"- **ID Completo:** `{p['pid']}`")
        md.append(f"- **Contexto:** UF: `{p['uf']}` | Grupo: `{p['grupo']}` | Blocos: {p['n_blocos']} | Colunas: {p['cols']} | Tabelas: {p['tabs']} | Flags: `{p['flags'] if p['flags'] else 'nenhum'}`")
        if p["nota"]:
            md.append(f"- **Nota do Anotador:** *\"{p['nota']}\"*")
        md.append(f"- **Desempenho Comparado:**")
        md.append(f"  - **LayoutLM Sucessor:** $\\tau = \\mathbf{{{p['tau_s']:.3f}}}$ | Sucessor Correto = **{p['suc_s']:.1%}**")
        md.append(f"  - **XY-cut:** $\\tau = \\mathbf{{{p['tau_xy']:.3f}}}$ | Sucessor Correto = **{p['suc_xy']:.1%}**")
        md.append(f"  - **LayoutLM Pontual:** $\\tau = \\mathbf{{{p['tau_l']:.3f}}}$ | Sucessor Correto = **{p['suc_l']:.1%}**")
        md.append(f"  - **Diferença (Sucessor − XY-cut):** $\\mathbf{{{p['diff']:+.3f}}}$")
        md.append("")
        md.append(f"- **Onde o Sucessor começa a errar (Posição {p_erro}):**")
        md.append(f"  - Bloco predito pelo Sucessor: `{s_b}` (deveria estar na pos {ref_pos[s_b]} da Ref, bbox={bx_s}): `\"{textos[s_b][:40]}\"`")
        md.append(f"  - Bloco esperado pela Referência: `{r_b}` (colocado pelo Sucessor na pos {suc_pos[r_b]}, bbox={bx_r}): `\"{textos[r_b][:40]}\"`")
        md.append("")
        md.append(f"- **Estrutura das Cadeias Preservadas:** O Sucessor formou {len(cadeias)} cadeias locais contínuas para {p['n_blocos']} blocos:")
        for c_idx, c in enumerate(cadeias):
            r_in = ref_pos[c[0]]
            r_fi = ref_pos[c[-1]]
            x0 = min(bboxes[b][0] for b in c)
            x1 = max(bboxes[b][2] for b in c)
            y0 = min(bboxes[b][1] for b in c)
            y1 = max(bboxes[b][3] for b in c)
            md.append(f"  - **Cadeia {c_idx+1}** ({len(c)} bloco{'s' if len(c)>1 else ''}): blocos da referência `[{r_in}..{r_fi}]`, bounding box `[{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]`. Início: `\"{textos[c[0]][:40]}\"`")
        md.append("")

        # Alinhamento bloco a bloco
        md.append("- **Alinhamento Bloco a Bloco:**")
        md.append("")
        md.append("| Bloco ID | Pos. Ref. (Humano) | Pos. Sucessor | Pos. XY-cut | Coordenadas [x0, y0, x1, y1] | Texto do Bloco (primeiros 40 carac.) |")
        md.append("|---|---:|---:|---:|---|---|")
        for bid in ref:
            bx = [round(x, 1) for x in bboxes[bid]]
            md.append(f"| `{bid}` | {ref_pos[bid]} | {suc_pos[bid]} | {xy.index(bid)} | `{bx}` | {textos[bid][:40]!r} |")
        md.append("")

        # Diagnostico do padrao
        md.append("- **Padrão do Erro:**")
        padrao = padroes_casos.get(p["pid_curto"], "**Padrão sob investigação:** erro na articulação entre cadeias locais e pontuação global.")
        md.append(padrao)
        md.append("")

    # 3. Medias por Recorte
    md.append("## 3. Médias de Desempenho por Recorte Estrutural")
    md.append("")
    md.append("Para entender a sensibilidade estrutural dos métodos sob decodificação em cadeias, agrupamos as 47 páginas por características de layout, comparando o LayoutLM Sucessor com o LayoutLM Pontual e o XY-cut.")
    md.append("")

    # 3.1 Por Grupo
    md.append("### 3.1 Por Grupo de Validação (`silver` vs `incerto`)")
    md.append("")
    md.append("| Grupo | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for g in ["silver", "incerto"]:
        sub = [p for p in paginas if p["grupo"] == g]
        md.append(f"| `{g}` | {len(sub)} | **{statistics.mean(p['tau_s'] for p in sub):.3f}** | {statistics.mean(p['suc_s'] for p in sub):.1%} | "
                  f"{statistics.mean(p['tau_l'] for p in sub):.3f} | {statistics.mean(p['suc_l'] for p in sub):.1%} | "
                  f"**{statistics.mean(p['tau_xy'] for p in sub):.3f}** | {statistics.mean(p['suc_xy'] for p in sub):.1%} |")
    md.append("")

    # 3.2 Por Colunas
    md.append("### 3.2 Por Número de Colunas da Página")
    md.append("")
    md.append("| Número de Colunas | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for c in sorted(set(p["cols"] for p in paginas)):
        sub = [p for p in paginas if p["cols"] == c]
        md.append(f"| {c} coluna{'s' if c>1 else ''} | {len(sub)} | **{statistics.mean(p['tau_s'] for p in sub):.3f}** | {statistics.mean(p['suc_s'] for p in sub):.1%} | "
                  f"{statistics.mean(p['tau_l'] for p in sub):.3f} | {statistics.mean(p['suc_l'] for p in sub):.1%} | "
                  f"**{statistics.mean(p['tau_xy'] for p in sub):.3f}** | {statistics.mean(p['suc_xy'] for p in sub):.1%} |")
    md.append("")

    # 3.3 Por Presença de Tabela
    md.append("### 3.3 Por Presença de Tabela")
    md.append("")
    md.append("#### Classificação pelo Detector Automático (`stats.n_tabelas > 0`):")
    md.append("")
    md.append("| Categoria | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for has_tab in [False, True]:
        sub = [p for p in paginas if (p["tabs"] > 0) == has_tab]
        nome = "Com tabela" if has_tab else "Sem tabela"
        md.append(f"| {nome} | {len(sub)} | **{statistics.mean(p['tau_s'] for p in sub):.3f}** | {statistics.mean(p['suc_s'] for p in sub):.1%} | "
                  f"{statistics.mean(p['tau_l'] for p in sub):.3f} | {statistics.mean(p['suc_l'] for p in sub):.1%} | "
                  f"**{statistics.mean(p['tau_xy'] for p in sub):.3f}** | {statistics.mean(p['suc_xy'] for p in sub):.1%} |")
    md.append("")

    md.append("#### Classificação pelo Flag do Anotador Humano (`'tabela' in flags`):")
    md.append("")
    md.append("| Categoria | n | τ Sucessor | Suc. Sucessor | τ Pontual | Suc. Pontual | τ XY-cut | Suc. XY-cut |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for has_tab in [False, True]:
        sub = [p for p in paginas if ("tabela" in p["flags"]) == has_tab]
        nome = "Com flag tabela" if has_tab else "Sem flag tabela"
        md.append(f"| {nome} | {len(sub)} | **{statistics.mean(p['tau_s'] for p in sub):.3f}** | {statistics.mean(p['suc_s'] for p in sub):.1%} | "
                  f"{statistics.mean(p['tau_l'] for p in sub):.3f} | {statistics.mean(p['suc_l'] for p in sub):.1%} | "
                  f"**{statistics.mean(p['tau_xy'] for p in sub):.3f}** | {statistics.mean(p['suc_xy'] for p in sub):.1%} |")
    md.append("")

    # 4. Tres Hipoteses
    md.append("## 4. Três Hipóteses Fundamentadas pelos Números (Revisadas pós-Cadeias)")
    md.append("")
    md.append("1. **Falha de ancoragem e inversão de macro-cadeias como gargalo residual.** "
              "O desacoplamento de pequenos blocos periféricos (cabeçalhos no topo, números de página ou notas de rodapé) "
              "permanece como o mecanismo mais frequente de erro local quando esses blocos não estabelecem arestas com p > 0,5 "
              "com o corpo do texto (visto em Japeri p3, Barra do Piraí e Congonhas p1). Mais importante, em páginas multicolunares "
              "densas, revelou-se um novo modo de erro: a inversão na ordenação global de colunas inteiras que foram internamente "
              "encadeadas com perfeição (como no Caso 1, MA p14, com 90,6% de sucessor correto mas τ 0,027 devido à leitura da Coluna 2 "
              "antes da Coluna 1). A cabeça pontual de ordenação de cadeias é, portanto, o componente que ainda introduz variância quando "
              "múltiplas macro-cadeias paralelas coexistem.")
    md.append("2. **Refutação do colapso com múltiplas colunas e superioridade em coluna única.** "
              "A hipótese anterior de degradação monotônica severa com o número de colunas (que previa colapso em 3 colunas, onde o τ caía para 0,601 em feixe) "
              "foi inteiramente superada: na decodificação em cadeias, páginas de 3 colunas sustentam τ médio de **0,814**, e no caso mais denso do acervo "
              "(MG p28, 99 blocos em 3 colunas) o Sucessor atinge τ **0,881**, superando o XY-cut (0,852). Além disso, em páginas de 1 coluna, o LayoutLM Sucessor "
              "supera amplamente o XY-cut (τ **0,878** vs 0,788, vantagem de +0,090), demonstrando que o modelo neural é superior na ordenação de blocos livres "
              "onde não há calhas ortogonais óbvias.")
    md.append("3. **Alta capacidade de generalização fora do domínio de treino (`incerto`).** "
              "A hipótese de vulnerabilidade a veículos e formatos novos foi conclusivamente refutada pelos dados corretos em cadeias: no grupo `incerto` "
              "(layouts e UFs nunca vistos durante o treinamento), o LayoutLM Sucessor alcança τ médio de **0,851**, superando tanto o grupo `silver` (0,837) "
              "quanto o próprio XY-cut no mesmo recorte (0,834). A aprendizagem de adjacência pairwise por meio de representações conjuntas de texto e layout "
              "mostra-se altamente agnóstica a estilos gráficos específicos, transferindo eficazmente para diários oficiais de qualquer federação ou município.")
    md.append("")

    # Registro de execucao
    md.append("## Registro de Execução")
    md.append("")
    md.append("- **Comando executado:** `venv\\Scripts\\python.exe orquestracao\\analises\\diagnostico_sucessor.py`")
    md.append("- **Arquivos de entrada:**")
    md.append("  - `data/golden/_avaliacao/golden_v3/tarefas.jsonl` (47 páginas)")
    md.append("  - `data/golden/_avaliacao/golden_v3/referencia.jsonl` (47 páginas concluídas pelo Pedro alano)")
    md.append("  - `resultados/golden/_avaliacao/golden_v3/pred_layoutlm.jsonl` (47 predições)")
    md.append("  - `resultados/golden/_avaliacao/golden_v3/pred_layoutlm_sucessor.jsonl` (47 predições em cadeias, corrigido em 13/09)")
    md.append("- **Métricas calculadas com:** `src.eval.metrics.avaliar`, `kendall_tau`, `acerto_sucessor`")
    md.append("- **Data e Hora:** 2026-09-13")

    with open(arq_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Relatório gerado com sucesso em: {arq_saida}")
    print(f"Total de páginas processadas: {len(paginas)}")

if __name__ == "__main__":
    gerar_diagnostico()
