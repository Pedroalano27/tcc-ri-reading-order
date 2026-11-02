"""Tabela-resumo da noite de 04->05/10: ordenadores sobre unidades sem caixas finas.

Lê resultados/ordenadores_sem_caixas.json (bancada do Codex) e imprime, em Markdown, uma tabela por
representação com os três conjuntos lado a lado. Não calcula nada novo: só reorganiza o que a bancada mediu.
Uso: venv/Scripts/python.exe -B orquestracao/analises/tabela_noite_0410.py > resultados/tabela_noite_0410.md
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BANCADAS = ("golden_v4", "golden_v3_novo", "teste_silver")
ROTULO = {"golden_v4": "golden_v4 (44)", "golden_v3_novo": "golden_v3 novo (27)", "teste_silver": "teste silver (89)"}


def br(x, casas):
    return f"{x:.{casas}f}".replace(".", ",")


def media(res, chave):
    # média macro por página, como nas tabelas da bancada
    vals = [p["metricas"][chave] for p in res["paginas"]]
    return sum(vals) / len(vals)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = json.loads((RAIZ / "resultados/ordenadores_sem_caixas.json").read_text(encoding="utf-8"))["resultados"]
    por = {}
    for res in d.values():
        por.setdefault(res["representacao"], {}).setdefault(res["ordenador"], {})[res["bancada"]] = res
    print("Gerado por `orquestracao/analises/tabela_noite_0410.py` a partir de `resultados/ordenadores_sem_caixas.json`.")
    print("Cada célula: τ de palavras / quebras por página / trechos de 12 palavras intactos. `n` entre parênteses quando a cobertura é parcial.\n")
    for rep in ("caixas_finas", "linhas", "colunas_margens", "colunas"):
        if rep not in por:
            continue
        print(f"### {rep}\n")
        print("| Ordenador | " + " | ".join(ROTULO[b] for b in BANCADAS) + " |")
        print("|---|" + "---:|" * len(BANCADAS))

        def chave(item):
            res = item[1].get("golden_v4")
            return media(res, "quebras") if res else 1e9
        for nome, bs in sorted(por[rep].items(), key=chave):
            cel = []
            for b in BANCADAS:
                res = bs.get(b)
                if not res:
                    cel.append("—")
                    continue
                n = len(res["paginas"])
                parcial = "" if res.get("completa", True) else f" (n={n})"
                cel.append(f"{br(media(res, 'tau'), 3)} / {br(media(res, 'quebras'), 2)} / {br(100 * media(res, 'fid12'), 1)}%{parcial}")
            print(f"| {nome} | " + " | ".join(cel) + " |")
        print()


if __name__ == "__main__":
    main()
