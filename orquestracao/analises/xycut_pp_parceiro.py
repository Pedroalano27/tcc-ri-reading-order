"""Roda o XY-Cut++ do projeto parceiro (CEIA-Datapolicy) sobre as unidades sem caixas finas e avalia na bancada.

O algoritmo NÃO é copiado para este repositório: é importado do clone local do repositório privado
(ramo feature/wilker/xycut_pp de Benchmark-LayoutAnalysis, arquivo API/app/services/xycut_pp.py, porte em
Python do XY-Cut++, arXiv:2504.10258). Entrada na mesma ordem embaralhada do protocolo.
Uso: venv/Scripts/python.exe -B orquestracao/analises/xycut_pp_parceiro.py
"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[2]
CLONE = Path("C:/Users/pedro/dev/ceia_datapolicy/Benchmark-LayoutAnalysis_xycut_pp/API")
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(CLONE))
from app.services.xycut_pp import xycut_pp_order_page  # noqa: E402
from orquestracao.analises import bancada_ordenadores as b  # noqa: E402
from src.eval.protocolo import ordem_entrada  # noqa: E402

ROTULO = {"tabela": "table", "table": "table", "imagem": "figure", "picture": "figure",
          "cabecalho": "header", "rodape": "footer"}
PRED = RAIZ / "resultados/ordenadores_sem_caixas/pred"


def main():
    for rep in b.REPS:
        for bancada in b.BANCADAS:
            destino = PRED / f"xycut_pp_parceiro__{rep}__{bancada}.jsonl"
            with open(destino, "w", encoding="utf-8", newline="\n") as f:
                for _, p in b.paginas(bancada, rep):
                    us = p["bounding_boxes"]
                    ent = ordem_entrada({"page_id": p["page_id"], "dimensions": p["dimensions"], "bounding_boxes": us})
                    itens = [SimpleNamespace(id=us[i]["id"], bbox=list(us[i]["bbox"]),
                                             label=ROTULO.get(us[i].get("tipo"), "text")) for i in ent]
                    pagina = SimpleNamespace(items=itens, page_width=p["dimensions"]["width"],
                                             page_height=p["dimensions"]["height"])
                    ordem = [x.id for x in xycut_pp_order_page(pagina)]
                    assert sorted(ordem) == sorted(u["id"] for u in us), p["page_id"]
                    f.write(json.dumps({"page_id": p["page_id"], "ordem": ordem}, ensure_ascii=False) + "\n")
            r = subprocess.run([sys.executable, "-B", str(RAIZ / "orquestracao/analises/bancada_ordenadores.py"),
                                "--avaliar-pred", str(destino)], capture_output=True, text=True, encoding="utf-8")
            print(rep, bancada, "rc", r.returncode, (r.stdout or r.stderr).strip().splitlines()[-2:][0][:120], flush=True)


if __name__ == "__main__":
    main()
