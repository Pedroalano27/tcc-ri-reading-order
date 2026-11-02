"""
Atualiza a proposta de pre-anotacao em lotes do Diamond para paginas que ainda nao foram anotadas.

Recalcula a proposta apenas das paginas sem nenhuma anotacao (qualquer anotador, qualquer status)
em data/diamond/<lote>/anotacoes.jsonl. Sem --aplicar, apenas relata quantas paginas e regioes mudariam.

Com --aplicar:
  1. Cria copia de seguranca tarefas.jsonl.bak_<data>;
  2. Rele anotacoes.jsonl logo antes de gravar (se uma pagina foi anotada no meio, fica de fora);
  3. Grava as tarefas atualizadas via arquivo temporario + os.replace;
  4. Atualiza proposta, proposta_versao e stats de cada pagina alterada;
  5. Registra a atualizacao em data/diamond/<lote>/derivados/atualizacoes.jsonl (data, versao, paginas);
  6. Nunca toca em anotacoes.jsonl, palavras, imagem ou n.

Uso:
    python src/anotacao/atualizar_proposta.py --lote diamond_treino --versao v3
    python src/anotacao/atualizar_proposta.py --lote diamond_treino --versao v3 --rose rose_treino --classes-rose assinatura_cabecalho
    python src/anotacao/atualizar_proposta.py --lote diamond_treino --versao v3 --aplicar
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import argparse
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src.data import regioes as seg  # noqa: E402

DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond")


def ler_jsonl(caminho: str) -> list[dict]:
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def gravar_jsonl(caminho: str, registros: list[dict]) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        for reg in registros:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def atualizar_proposta(
    lote: str,
    versao: str = "v3",
    rose: str | None = None,
    classes_rose: str | None = None,
    aplicar: bool = False,
    dir_diamond: str | None = None,
) -> dict:
    base_dir = dir_diamond or DIR_DIAMOND
    dir_lote = os.path.join(base_dir, lote)
    if not os.path.isdir(dir_lote):
        raise FileNotFoundError(f"Lote nao encontrado: {dir_lote}")

    caminho_anotacoes = os.path.join(dir_lote, "anotacoes.jsonl")
    caminho_tarefas = os.path.join(dir_lote, "tarefas.jsonl")

    if not os.path.exists(caminho_tarefas):
        raise FileNotFoundError(f"Arquivo tarefas.jsonl nao encontrado em {dir_lote}")

    anotacoes = ler_jsonl(caminho_anotacoes)
    anotadas = {an["page_id"] for an in anotacoes}

    tarefas = ler_jsonl(caminho_tarefas)

    anots_rose = {}
    if rose:
        caminho_rose = os.path.join(base_dir, rose, "anotacoes.jsonl")
        if os.path.exists(caminho_rose):
            for an in ler_jsonl(caminho_rose):
                if an.get("regioes"):
                    anots_rose[an["page_id"]] = an["regioes"]

    propostas_novas = {}
    mudariam = {}
    regioes_antes_tot = 0
    regioes_depois_tot = 0

    for t in tarefas:
        pid = t["page_id"]
        if pid in anotadas:
            continue
        detector_regs = t["detector"]["regioes"] if isinstance(t.get("detector"), dict) else t.get("detector", [])
        nova_prop = seg.propor(t["palavras"], t["blocos_v3"], detector_regs, regras=versao)
        if rose and pid in anots_rose:
            conj = classes_rose or "assinatura_cabecalho"
            nova_prop = seg.aplicar_classes_rose(nova_prop, t["palavras"], anots_rose[pid], conj)

        propostas_novas[pid] = nova_prop
        antiga_prop = t.get("proposta", [])
        regioes_antes_tot += len(antiga_prop)
        regioes_depois_tot += len(nova_prop)
        if nova_prop != antiga_prop:
            mudariam[pid] = {
                "antes": len(antiga_prop),
                "depois": len(nova_prop),
            }

    elegiveis = [t for t in tarefas if t["page_id"] not in anotadas]
    resultado = {
        "lote": lote,
        "versao": versao,
        "rose": rose,
        "classes_rose": classes_rose,
        "total_tarefas": len(tarefas),
        "paginas_anotadas": len(anotadas),
        "paginas_elegiveis": len(elegiveis),
        "paginas_mudariam": len(mudariam),
        "paginas_identicas": len(elegiveis) - len(mudariam),
        "regioes_antes": regioes_antes_tot,
        "regioes_depois": regioes_depois_tot,
        "mudariam_ids": sorted(mudariam.keys()),
        "aplicado": aplicar,
    }

    print(f"=== Relato de atualizacao de proposta: {lote} ===")
    desc_versao = versao + (f" + Rose ({rose}, classes={classes_rose})" if rose else "")
    print(f"Versao da proposta: {desc_versao}")
    print(f"Total de paginas no lote: {len(tarefas)}")
    print(f"Paginas com anotacao (intocadas): {len(anotadas)}")
    print(f"Paginas sem anotacao (elegiveis): {len(elegiveis)}")
    print(f"Paginas cuja proposta mudaria: {len(mudariam)}")
    print(f"Paginas cuja proposta permaneceria identica: {len(elegiveis) - len(mudariam)}")
    diff_reg = regioes_depois_tot - regioes_antes_tot
    print(f"Regioes nas paginas elegiveis: {regioes_antes_tot} antes -> {regioes_depois_tot} depois (diferenca: {diff_reg:+d})")

    if not aplicar:
        print("\n[SIMULACAO] Modo somente leitura (--aplicar nao informado). Nenhuma alteracao gravada em disco.")
        return resultado

    # Aplicacao com seguranca
    agora = datetime.now()
    agora_str = agora.strftime("%Y%m%d_%H%M%S")
    caminho_bak = f"{caminho_tarefas}.bak_{agora_str}"
    shutil.copy2(caminho_tarefas, caminho_bak)
    print(f"\n[BACKUP] Criado: {os.path.basename(caminho_bak)}")

    # Rele anotacoes logo antes de gravar para proteger anotacoes feitas durante a execucao
    anotacoes_finais = ler_jsonl(caminho_anotacoes)
    anotadas_finais = {an["page_id"] for an in anotacoes_finais}

    paginas_alteradas = []
    tarefas_atualizadas = []
    for t in tarefas:
        pid = t["page_id"]
        # Se foi anotada no meio do caminho ou ja estava anotada, mantem intacta
        if pid in anotadas_finais:
            tarefas_atualizadas.append(t)
            continue
        if pid in propostas_novas:
            nova_prop = propostas_novas[pid]
            t["proposta"] = nova_prop
            t["proposta_versao"] = versao
            t.setdefault("stats", {})
            t["stats"]["n_proposta"] = len(nova_prop)
            t["stats"]["alertas"] = {
                a: sum(a in r.get("alertas", []) for r in nova_prop)
                for a in ("juntou_sobrepostas", "so_regras", "baixa_confianca", "atravessa_colunas")
            }
            paginas_alteradas.append(pid)
        tarefas_atualizadas.append(t)

    caminho_tmp = f"{caminho_tarefas}.tmp"
    gravar_jsonl(caminho_tmp, tarefas_atualizadas)
    os.replace(caminho_tmp, caminho_tarefas)
    print(f"[OK] tarefas.jsonl atualizado ({len(paginas_alteradas)} paginas alteradas)")

    # Registra no log de atualizacoes em derivados/
    dir_derivados = os.path.join(dir_lote, "derivados")
    os.makedirs(dir_derivados, exist_ok=True)
    caminho_atualizacoes = os.path.join(dir_derivados, "atualizacoes.jsonl")
    registro_log = {
        "data": agora.isoformat(),
        "versao": versao,
        "rose": rose,
        "classes_rose": classes_rose,
        "n_paginas_alteradas": len(paginas_alteradas),
        "paginas": paginas_alteradas,
    }
    with open(caminho_atualizacoes, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro_log, ensure_ascii=False) + "\n")
    print(f"[OK] Registro gravado em {caminho_atualizacoes}")

    resultado["paginas_efetivamente_alteradas"] = len(paginas_alteradas)
    resultado["backup"] = caminho_bak
    return resultado


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lote", required=True, help="Nome do lote em data/diamond/")
    ap.add_argument("--versao", default="v3", help="Versao das regras da proposta (padrao: v3)")
    ap.add_argument("--rose", help="Lote do Rose para aplicar classes")
    ap.add_argument("--classes-rose", default="assinatura_cabecalho", help="Conjunto de classes do Rose a aplicar")
    ap.add_argument("--aplicar", action="store_true", help="Efetiva a gravacao em tarefas.jsonl")
    ap.add_argument("--dir-diamond", help="Diretorio base alternativo do Diamond (para testes)")
    a = ap.parse_args()

    atualizar_proposta(
        lote=a.lote,
        versao=a.versao,
        rose=a.rose,
        classes_rose=a.classes_rose,
        aplicar=a.aplicar,
        dir_diamond=a.dir_diamond,
    )


if __name__ == "__main__":
    main()
