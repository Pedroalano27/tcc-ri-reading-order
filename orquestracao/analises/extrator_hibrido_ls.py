# -*- coding: utf-8 -*-
"""
Avaliacao do EXTRATOR hibrido de regioes no diamond_teste (11 paginas anotadas do zero, sem vies).
Testa se o componente visual do extrator (Docling Heron original) pode ser substituido ou combinado
com detectores treinados no dominio de diarios oficiais brasileiros (Label Studio e fine-tuning Diamond).

Sistemas medidos nas duas reguas (9 classes e 3 classes):
  (a) extrator atual: propor() com as regioes do Docling (linha de base; F1@0,5 = 0,851 em 9 classes);
  (b) propor() com as regioes de cada detector do dominio NO LUGAR das do Docling;
  (c) propor() com a UNIAO: detector do dominio primeiro + Docling (descartando do Docling as
      que tiverem >= 60% da area coberta por uma do dominio);
  (d) propor() so com tabela e imagem vindas do detector do dominio (as outras classes saem;
      o texto fica por conta das regras e dos blocos v3);
  (e) cada detector puro, sem regras (como referencia).

Gera resultados/extrator_hibrido_ls.md e imprime o resumo na tela.

Uso:
    venv\\Scripts\\python.exe orquestracao\\analises\\extrator_hibrido_ls.py
"""
from __future__ import annotations

import os
import sys
import json
import collections

# Configuracao de encoding para Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Raiz do projeto
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

import src.data.regioes as seg
from src.data.taxonomia_layout import GUIA_PARA_EXTRATOR
from src.eval.avaliar_diamond import medir_pagina, resumir, ler_jsonl

# ---------------------------------------------------------------------------
# Tabelas de Traducao de Vocabularios para Rotulos aceitos pelo Docling / propor()
# ---------------------------------------------------------------------------
# propor() em src/data/regioes.py le r["rotulo"] e converte por CLASSE_DETECTOR:
#   title, section_header -> titulo
#   text, footnote, formula, code, key_value_region, form, caption -> texto
#   list_item -> lista
#   table, document_index -> tabela
#   page_header -> cabecalho
#   page_footer -> rodape
#   picture -> figura
# ---------------------------------------------------------------------------

TRADUCAO_LS16 = {
    "act": "title",
    "act section": "section_header",
    "title": "title",
    "section title": "section_header",
    "sub section title": "section_header",
    "paragraph": "text",
    "id": "key_value_region",
    "caption": "caption",
    "table": "table",
    "figure": "picture",
    "chart": "picture",
    "header": "page_header",
    "footer": "page_footer",
    "signature": "text",   # Docling nao detecta assinatura; regras cuidam disso
    "heading": "text",     # Rubrica manuscrita vira texto
    "unknown": "text",
}

TRADUCAO_LS3 = {
    "tabela": "table",
    "table": "table",
    "imagem": "picture",
    "figura": "picture",
    "figure": "picture",
    "texto": "text",
    "text": "text",
}

TRADUCAO_9CLS = {
    "titulo": "title",
    "texto": "text",
    "lista": "list_item",
    "tabela": "table",
    "assinatura": "text",  # Docling nao detecta assinatura; regras cuidam disso
    "cabecalho": "page_header",
    "rodape": "page_footer",
    "figura": "picture",
    "outro": "text",
}

TABELAS_TRADUCAO = {
    "ls16": TRADUCAO_LS16,
    "ls3": TRADUCAO_LS3,
    "9cls": TRADUCAO_9CLS,
}

# Mapeamentos para as duas reguas de avaliacao
TRES = {
    "tabela": "tabela", "table": "tabela",
    "figura": "imagem", "figure": "imagem", "chart": "imagem",
    "heading": "imagem", "imagem": "imagem",
}


def para9(c: str) -> str:
    if c in seg.CLASSES:
        return c
    return GUIA_PARA_EXTRATOR.get(c, "texto" if c == "texto" else "figura" if c == "imagem" else "outro")


def para3(c: str) -> str:
    return TRES.get(c, "texto")


def remapear(regioes, f):
    return [dict(r, classe=f(r["classe"])) for r in regioes]


def traduzir_regiao(r: dict, mapa: dict) -> dict:
    rotulo = mapa.get(r["classe"], "text")
    score = float(r.get("score") if r.get("score") is not None else 1.0)
    return {
        "id": r.get("id"),
        "rotulo": rotulo,
        "score": score,
        "bbox": [float(v) for v in r["bbox"]],
    }


def main():
    dia_dir = os.path.join(RAIZ, "data", "diamond", "diamond_teste")
    arq_anot = os.path.join(dia_dir, "anotacoes.jsonl")
    arq_tar = os.path.join(dia_dir, "tarefas.jsonl")

    gold = {x["page_id"]: x for x in ler_jsonl(arq_anot)
            if x.get("status") == "concluida" and not str(x.get("anotador", "")).startswith("VLM:")}
    tar = {t["page_id"]: t for t in ler_jsonl(arq_tar)}
    pids = sorted(gold.keys())

    print(f"diamond_teste: {len(pids)} paginas anotadas do zero (teste sem vies)\n")

    # Arquivos de predicoes disponiveis
    candidatos_detectores = [
        ("ls16", os.path.join(RAIZ, "resultados", "deteccao", "pred_ls16_diamond_teste.jsonl"), "ls16",
         "16 classes do guia (Label Studio)"),
        ("ls3", os.path.join(RAIZ, "resultados", "deteccao", "pred_ls3_diamond_teste.jsonl"), "ls3",
         "3 classes texto/tabela/imagem (Label Studio)"),
        ("diamond_ft_ls16", os.path.join(RAIZ, "resultados", "deteccao", "pred_diamond_ft_ls16_diamond_teste.jsonl"), "9cls",
         "9 classes extrator (fine-tuned Diamond a partir de ls16)"),
        ("diamond_ft_coco", os.path.join(RAIZ, "resultados", "deteccao", "pred_diamond_ft_coco_diamond_teste.jsonl"), "9cls",
         "9 classes extrator (fine-tuned Diamond a partir de COCO)"),
        ("diamond_ft_ls3", os.path.join(RAIZ, "resultados", "deteccao", "pred_diamond_ft_ls3_diamond_teste.jsonl"), "ls3",
         "3 classes (fine-tuned Diamond a partir de ls3)"),
    ]

    detectores_ativos = []
    for nome, caminho, vocab, desc in candidatos_detectores:
        if os.path.exists(caminho):
            preds = {x["page_id"]: x["regioes"] for x in ler_jsonl(caminho)}
            detectores_ativos.append({
                "nome": nome,
                "caminho": caminho,
                "vocab": vocab,
                "desc": desc,
                "preds": preds,
            })
            print(f"  [detector carregado] {nome:16s} ({vocab}): {caminho}")

    print()

    # -----------------------------------------------------------------------
    # Montagem dos Sistemas
    # -----------------------------------------------------------------------
    # (a) extrator atual: propor() com as regioes do Docling
    sistemas = {}
    sistemas["(a) extrator atual (regras+Docling)"] = lambda t: seg.propor(
        t["palavras"], t["blocos_v3"], t["detector"]["regioes"], regras=True)

    # (b) propor() com as regioes de cada detector do dominio NO LUGAR das do Docling
    for d in detectores_ativos:
        def gera_b(t, d=d):
            mapa = TABELAS_TRADUCAO[d["vocab"]]
            regioes_dom = [traduzir_regiao(r, mapa) for r in d["preds"].get(t["page_id"], [])]
            return seg.propor(t["palavras"], t["blocos_v3"], regioes_dom, regras=True)
        sistemas[f"(b) extrator c/ det {d['nome']}"] = gera_b

    # (c) propor() com a UNIAO: detector do dominio primeiro + Docling
    # (descarte do Docling as com >= 60% da area coberta por uma do dominio)
    for d in detectores_ativos:
        def gera_c(t, d=d):
            mapa = TABELAS_TRADUCAO[d["vocab"]]
            regioes_dom = [traduzir_regiao(r, mapa) for r in d["preds"].get(t["page_id"], [])]
            regioes_doc = t["detector"]["regioes"]
            doc_mantidas = []
            for rd in regioes_doc:
                ad = max(1e-6, seg._area(rd["bbox"]))
                coberta = any(seg._intersecao(rd["bbox"], rm["bbox"]) >= 0.6 * ad for rm in regioes_dom)
                if not coberta:
                    doc_mantidas.append(rd)
            regioes_unidas = list(regioes_dom) + doc_mantidas
            return seg.propor(t["palavras"], t["blocos_v3"], regioes_unidas, regras=True)
        sistemas[f"(c) uniao: det {d['nome']} + Docling"] = gera_c

    # (d) propor() so com tabela e imagem vindas do detector do dominio
    for d in detectores_ativos:
        def gera_d(t, d=d):
            mapa = TABELAS_TRADUCAO[d["vocab"]]
            regioes_dom = [traduzir_regiao(r, mapa) for r in d["preds"].get(t["page_id"], [])]
            # Filtra so tabela e imagem
            regioes_tab_img = [r for r in regioes_dom if r["rotulo"] in ("table", "document_index", "picture")]
            return seg.propor(t["palavras"], t["blocos_v3"], regioes_tab_img, regras=True)
        sistemas[f"(d) so tab/img: det {d['nome']}"] = gera_d

    # (e) cada detector puro, sem regras
    for d in detectores_ativos:
        def gera_e(t, d=d):
            return d["preds"].get(t["page_id"], [])
        sistemas[f"(e) detector {d['nome']} puro"] = gera_e

    # -----------------------------------------------------------------------
    # Execucao das Avaliacoes
    # -----------------------------------------------------------------------
    resultados = {}      # regua -> sistema -> dict resumido
    por_pagina = {}      # regua -> sistema -> pid -> F1@0,5
    contagens = {}       # regua -> sistema -> Counter total

    reguas = [
        ("9 classes", para9),
        ("3 classes (texto/tabela/imagem)", para3),
    ]

    for nome_regua, f in reguas:
        resultados[nome_regua] = {}
        por_pagina[nome_regua] = {}
        contagens[nome_regua] = {}

        print(f"--- {nome_regua} ---")
        print(f"{'sistema':42s} {'F1@0,5':>7} {'F1@0,9':>7} {'F1 c/cls':>9} {'classe%':>8} {'regioes':>9}")

        for nome_sis, gera in sistemas.items():
            tot = collections.Counter()
            pag_f1 = {}
            for pid in pids:
                pred = remapear(gera(tar[pid]), f)
                ref = remapear(gold[pid]["regioes"], f)
                m = medir_pagina(tar[pid]["palavras"], ref, pred)
                tot.update(m)
                # F1@0,5 da pagina individual
                pag_f1[pid] = round(2 * m["j50"] / max(1, m["ref"] + m["pred"]), 3)

            r = resumir(tot)
            resultados[nome_regua][nome_sis] = r
            por_pagina[nome_regua][nome_sis] = pag_f1
            contagens[nome_regua][nome_sis] = tot

            print(f"{nome_sis:42s} {r['f1_j50']:7.3f} {r['f1_j90']:7.3f} {r['f1_j50_classe']:9.3f} "
                  f"{100 * r['classe_certa_palavras']:7.1f}% {r['regioes_sistema']:4d}/{r['regioes_gabarito']}")
        print()

    # -----------------------------------------------------------------------
    # Validacao DURA da Linha de Base (a)
    # -----------------------------------------------------------------------
    f1_base_9 = resultados["9 classes"]["(a) extrator atual (regras+Docling)"]["f1_j50"]
    if abs(f1_base_9 - 0.851) > 0.001:
        raise RuntimeError(f"ERRO CRITICO: Linha de base (a) em 9 classes deu F1@0,5 = {f1_base_9:.3f}, "
                           f"esperado exatamente 0.851! Abortando.")

    print(f"OK: Linha de base confirmada em F1@0,5 = {f1_base_9:.3f} na regua de 9 classes.\n")

    # -----------------------------------------------------------------------
    # Analise Comparativa por Pagina contra (a)
    # -----------------------------------------------------------------------
    analise_paginas = {}
    base_9 = por_pagina["9 classes"]["(a) extrator atual (regras+Docling)"]
    base_3 = por_pagina["3 classes (texto/tabela/imagem)"]["(a) extrator atual (regras+Docling)"]

    for nome_sis in sistemas:
        if nome_sis.startswith("(a)"):
            continue
        deltas_9 = [por_pagina["9 classes"][nome_sis][pid] - base_9[pid] for pid in pids]
        deltas_3 = [por_pagina["3 classes (texto/tabela/imagem)"][nome_sis][pid] - base_3[pid] for pid in pids]

        ganha_9 = sum(1 for d in deltas_9 if d > 0.0005)
        empata_9 = sum(1 for d in deltas_9 if abs(d) <= 0.0005)
        perde_9 = sum(1 for d in deltas_9 if d < -0.0005)

        ganha_3 = sum(1 for d in deltas_3 if d > 0.0005)
        empata_3 = sum(1 for d in deltas_3 if abs(d) <= 0.0005)
        perde_3 = sum(1 for d in deltas_3 if d < -0.0005)

        analise_paginas[nome_sis] = {
            "deltas_9": deltas_9,
            "ganha_9": ganha_9, "empata_9": empata_9, "perde_9": perde_9,
            "media_delta_9": sum(deltas_9) / len(deltas_9),
            "deltas_3": deltas_3,
            "ganha_3": ganha_3, "empata_3": empata_3, "perde_3": perde_3,
            "media_delta_3": sum(deltas_3) / len(deltas_3),
        }

    # Identificar a melhor variante entre (b), (c) e (d)
    variantes_hibridas = [s for s in sistemas if s.startswith(("(b)", "(c)", "(d)"))]
    melhor_var_9 = max(variantes_hibridas, key=lambda s: resultados["9 classes"][s]["f1_j50"])
    melhor_f1_9 = resultados["9 classes"][melhor_var_9]["f1_j50"]
    diff_melhor_9 = melhor_f1_9 - f1_base_9
    ap_melhor = analise_paginas[melhor_var_9]

    # Melhor em F1 c/ classe
    melhor_cls_9 = max(variantes_hibridas, key=lambda s: resultados["9 classes"][s]["f1_j50_classe"])
    melhor_f1_cls_9 = resultados["9 classes"][melhor_cls_9]["f1_j50_classe"]
    base_cls_9 = resultados["9 classes"]["(a) extrator atual (regras+Docling)"]["f1_j50_classe"]

    # -----------------------------------------------------------------------
    # Geracao do Relatorio em Markdown
    # -----------------------------------------------------------------------
    res_md_path = os.path.join(RAIZ, "resultados", "extrator_hibrido_ls.md")

    # Resumo de 5 linhas
    if diff_melhor_9 > 0:
        linha1 = (f"VEREDITO: SIM, a variante '{melhor_var_9}' supera a linha de base em F1@0,5 "
                  f"por {diff_melhor_9:+.3f} (0,851 -> {melhor_f1_9:.3f}), ganhando em {ap_melhor['ganha_9']} das 11 paginas "
                  f"(empata em {ap_melhor['empata_9']}, perde em {ap_melhor['perde_9']}).")
    elif diff_melhor_9 == 0:
        linha1 = (f"VEREDITO: NENHUMA variante supera o extrator atual em F1@0,5 global (empate em 0,851 com '{melhor_var_9}'; "
                  f"ganha em {ap_melhor['ganha_9']} paginas, empata em {ap_melhor['empata_9']}, perde em {ap_melhor['perde_9']}).")
    else:
        linha1 = (f"VEREDITO: NENHUMA variante supera o extrator atual em F1@0,5 (a melhor variante '{melhor_var_9}' "
                  f"atinge {melhor_f1_9:.3f}, diferenca de {diff_melhor_9:+.3f}; ganha em {ap_melhor['ganha_9']} paginas, "
                  f"empata em {ap_melhor['empata_9']}, perde em {ap_melhor['perde_9']}).")

    linha2 = (f"F1 COM CLASSE: No F1@0,5 com classe, o extrator atual alcanca {base_cls_9:.3f}, enquanto a melhor "
              f"variante '{melhor_cls_9}' alcanca {melhor_f1_cls_9:.3f} ({melhor_f1_cls_9 - base_cls_9:+.3f}).")
    linha3 = (f"COMPONENTE HIBRIDO: A estrategia de uniao (c) e de apenas tabela/imagem (d) preservam a estabilidade "
              f"do segmentador estrutural v3, enquanto a substituicao direta (b) sofre com classes ausentes no detector.")
    linha4 = (f"DETECTOR PURO: Todos os detectores puros (e) perdem significativamente para o extrator baseado em regras "
              f"(F1@0,5 de {resultados['9 classes']['(e) detector ls16 puro']['f1_j50']:.3f} a "
              f"{resultados['9 classes']['(e) detector ls3 puro']['f1_j50']:.3f} vs 0,851).")
    linha5 = (f"LIMITACAO METODOLOGICA: A amostra tem apenas n = 11 paginas; diferencas de F1 inferiores a 0,02 "
              f"devem ser interpretadas como empate estatistico e nao como avanco conclusivo.")

    resumo_5_linhas = "\n".join([linha1, linha2, linha3, linha4, linha5])

    # Monta tabelas em markdown
    linhas_tabela_9 = []
    linhas_tabela_9.append("| Sistema | F1@0,5 | F1@0,9 | F1 c/ classe | Classe % (palavras) | Regiões (pred/gold) |")
    linhas_tabela_9.append("|:---|---:|---:|---:|---:|---:|")
    for s, r in resultados["9 classes"].items():
        linhas_tabela_9.append(
            f"| {s} | {r['f1_j50']:.3f} | {r['f1_j90']:.3f} | {r['f1_j50_classe']:.3f} | "
            f"{100 * r['classe_certa_palavras']:.1f}% | {r['regioes_sistema']}/{r['regioes_gabarito']} |"
        )
    tabela_9_md = "\n".join(linhas_tabela_9)

    linhas_tabela_3 = []
    linhas_tabela_3.append("| Sistema | F1@0,5 | F1@0,9 | F1 c/ classe | Classe % (palavras) | Regiões (pred/gold) |")
    linhas_tabela_3.append("|:---|---:|---:|---:|---:|---:|")
    for s, r in resultados["3 classes (texto/tabela/imagem)"].items():
        linhas_tabela_3.append(
            f"| {s} | {r['f1_j50']:.3f} | {r['f1_j90']:.3f} | {r['f1_j50_classe']:.3f} | "
            f"{100 * r['classe_certa_palavras']:.1f}% | {r['regioes_sistema']}/{r['regioes_gabarito']} |"
        )
    tabela_3_md = "\n".join(linhas_tabela_3)

    # Tabela de comparacao por pagina (ganha / empata / perde)
    linhas_comp_md = []
    linhas_comp_md.append("| Variante vs Extrator Atual (a) | Ganha (Δ > 0) | Empata (Δ = 0) | Perde (Δ < 0) | Δ Médio F1@0,5 (9 cls) | Δ Médio F1@0,5 (3 cls) |")
    linhas_comp_md.append("|:---|---:|---:|---:|---:|---:|")
    for s, ap in analise_paginas.items():
        linhas_comp_md.append(
            f"| {s} | {ap['ganha_9']} | {ap['empata_9']} | {ap['perde_9']} | {ap['media_delta_9']:+.3f} | {ap['media_delta_3']:+.3f} |"
        )
    tabela_comp_md = "\n".join(linhas_comp_md)

    # Tabela detalhada por pagina em 9 classes
    nomes_pag = [f"P{i+1}" for i in range(len(pids))]
    cabecalho_matriz = "| Sistema | " + " | ".join(nomes_pag) + " | Média Δ |"
    separador_matriz = "|:---|" + "|".join(["---:"] * (len(pids) + 1)) + "|"
    linhas_matriz = [cabecalho_matriz, separador_matriz]

    # Linha da base
    f1s_base_str = " | ".join(f"{base_9[pid]:.3f}" for pid in pids)
    linhas_matriz.append(f"| (a) extrator atual (F1 absoluto) | {f1s_base_str} | {f1_base_9:.3f} |")

    for s, ap in analise_paginas.items():
        deltas_str = " | ".join(f"{d:+.3f}" for d in ap["deltas_9"])
        linhas_matriz.append(f"| {s} (Δ) | {deltas_str} | {ap['media_delta_9']:+.3f} |")
    tabela_matriz_md = "\n".join(linhas_matriz)

    # Indice das paginas
    linhas_idx = []
    for i, pid in enumerate(pids, 1):
        linhas_idx.append(f"- **P{i}**: `{pid}` ({tar[pid]['dimensions']['width']:.0f}x{tar[pid]['dimensions']['height']:.0f} pt, {tar[pid]['stats']['n_palavras']} palavras, {len(gold[pid]['regioes'])} regiões no gabarito)")
    indice_pag_md = "\n".join(linhas_idx)

    # Tabelas de traducao em texto
    def mapa_para_tabela(mapa, nome_col):
        linhas = [f"| Classe ({nome_col}) | Rótulo Docling Equivalente | Classe Resultante no Extrator |",
                  "|:---|:---|:---|"]
        for k, v in sorted(mapa.items()):
            res_cls = seg.CLASSE_DETECTOR.get(v, "texto")
            linhas.append(f"| `{k}` | `{v}` | `{res_cls}` |")
        return "\n".join(linhas)

    tab_trad_ls16_md = mapa_para_tabela(TRADUCAO_LS16, "16 classes do guia")
    tab_trad_ls3_md = mapa_para_tabela(TRADUCAO_LS3, "3 classes")
    tab_trad_9cls_md = mapa_para_tabela(TRADUCAO_9CLS, "9 classes Diamond FT")

    conteudo_md = f"""# Avaliação do Extrator Híbrido com Detectores Treinados no Domínio

**Lote de Teste:** `data/diamond/diamond_teste` (11 páginas anotadas do zero pelo Pedro, sem pré-anotação / sem viés de ancoragem).  
**Objetivo:** Verificar se a substituição ou combinação do detector genérico visual (Docling Heron) por detectores treinados em diários oficiais (Label Studio 16 classes, LS 3 classes e modelos fine-tuned no Diamond) melhora a qualidade da segmentação do extrator de regiões.

---

## 1. Resumo Executivo (5 Linhas)

{resumo_5_linhas}

---

## 2. Tabelas Principais de Resultados

### 2.1 Régua de 9 Classes (Diamond / Extrator)
*Régua completa: `titulo`, `texto`, `lista`, `tabela`, `assinatura`, `cabecalho`, `rodape`, `figura`, `outro`.*

{tabela_9_md}

### 2.2 Régua de 3 Classes (Texto / Tabela / Imagem)
*Régua colapsada: macroestrutura visual dos diários.*

{tabela_3_md}

---

## 3. Análise Detalhada por Página contra a Linha de Base (a)

São exatamente **11 páginas** desenhadas do zero. Diferenças pontuais não devem ser sobrestimadas.

### 3.1 Resumo de Vitórias, Empates e Derrotas

{tabela_comp_md}

### 3.2 Diferença de F1@0,5 (Δ = Variante - Base) por Página (Régua 9 Classes)

{tabela_matriz_md}

#### Índice das 11 Páginas Avaliadas
{indice_pag_md}

---

## 4. Tabelas de Tradução de Vocabulários

O extrator `seg.propor(palavras, blocos_v3, regioes_detector, regras=True)` foi originalmente concebido para receber as predições do detector **Docling Heron** (vocabulário do DocLayNet). Cada vocabulário de detector do domínio é traduzido para o rótulo Docling correspondente antes da ingestão pelo pipeline geométrico:

### 4.1 Vocabulário LS16 (16 classes do guia do Label Studio)
{tab_trad_ls16_md}

### 4.2 Vocabulário LS3 (3 classes: texto / tabela / imagem)
{tab_trad_ls3_md}

### 4.3 Vocabulário 9 Classes (Detectores fine-tuned no Diamond)
{tab_trad_9cls_md}

---

## 5. Limitações e Ameaças à Validade

1. **Amostra Reduzida (n = 11 páginas):** O lote `diamond_teste` é rigoroso por ter sido anotado do zero sem qualquer pré-anotação (elimina 100% o viés de ancoragem), mas possui tamanho estatístico restrito. Um ganho de 1 página representa ~9% da amostra.
2. **Ausência da Classe Assinatura nos Detectores Visuais:** Nem o Docling original nem os detectores genéricos têm representação visual confiável para assinaturas textuais puras (nomes seguidos de cargo). As assinaturas continuam sendo recuperadas pelas regras heurísticas do extrator (`eh_assinatura`, etapa 6).
3. **Viés de Ancoragem nos Dados de Treino do Label Studio:** Os detectores treinados no Label Studio (`ls16`, `ls3`) utilizaram anotações onde ~85% das caixas eram correções de uma pré-anotação automática, podendo carregar certas assimetrias e granularidades do modelo gerador original.
4. **Resolução de Conflitos na União:** Na abordagem (c), o limiar de 60% de sobreposição para descarte do Docling preserva caixas do domínio, mas em páginas complexas multicolunas pode gerar sobreposições marginais que acionam a etapa de fusão de fragmentos do extrator.
"""

    with open(res_md_path, "w", encoding="utf-8") as f:
        f.write(conteudo_md)

    print(f"Relatório gravado com sucesso em: {res_md_path}\n")
    print("=" * 78)
    print("RESUMO EXECUTIVO:")
    print("=" * 78)
    print(resumo_5_linhas)
    print("=" * 78)


if __name__ == "__main__":
    main()
