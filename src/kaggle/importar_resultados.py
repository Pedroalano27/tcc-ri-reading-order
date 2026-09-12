"""
Traz para o projeto os resultados gerados no Kaggle.

    python src/kaggle/importar_resultados.py caminho/para/resultados_kaggle.zip

  - predicoes de LLM no teste         -> resultados/            (onde comparar.py as encontra)
  - predicoes nas paginas do Golden   -> resultados/golden/<lote>/
  - latencia medida na T4             -> resultados/
  - registro das execucoes            -> acrescentado a resultados/execucoes_llm.jsonl
  - copia intacta de tudo             -> resultados/kaggle/<data-hora>/  (versionada no git:
                                         essas predicoes custam horas de GPU)
Depois roda comparar.py.
"""
from __future__ import annotations

import os
import sys
import json
import time
import zipfile
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(RAIZ, "resultados")


def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        sys.exit("uso: python src/kaggle/importar_resultados.py resultados_kaggle.zip")
    copia = os.path.join(RES, "kaggle", time.strftime("%Y-%m-%d_%H%M"))
    novos, execucoes = [], []
    with zipfile.ZipFile(sys.argv[1]) as z:
        for info in z.infolist():
            nome = info.filename.replace("\\", "/")
            if info.is_dir() or nome.startswith("/") or ".." in nome.split("/"):
                continue
            dados = z.read(info)
            destino_copia = os.path.join(copia, *nome.split("/"))
            os.makedirs(os.path.dirname(destino_copia), exist_ok=True)
            with open(destino_copia, "wb") as f:
                f.write(dados)
            partes = nome.split("/")
            if partes[0] != "resultados":
                continue
            base = partes[-1]
            if base == "execucoes_llm.jsonl":
                execucoes += [l for l in dados.decode("utf-8").splitlines() if l.strip()]
                continue
            if not (base.startswith("pred_llm_") or base.startswith("latencia_")):
                continue
            destino = os.path.join(RAIZ, *partes)       # mantem resultados/ ou resultados/golden/<lote>/
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "wb") as f:
                f.write(dados)
            novos.append(os.path.relpath(destino, RAIZ))

    if execucoes:
        reg = os.path.join(RES, "execucoes_llm.jsonl")
        existentes = set()
        if os.path.exists(reg):
            with open(reg, encoding="utf-8") as f:
                existentes = {l.strip() for l in f if l.strip()}
        with open(reg, "a", encoding="utf-8") as f:
            for l in execucoes:
                if l.strip() not in existentes:
                    f.write(l.strip() + "\n")
    print(f"[OK] {len(novos)} arquivos importados; copia completa em {os.path.relpath(copia, RAIZ)}")
    for n in novos:
        print("   ", n)
    for l in execucoes:
        e = json.loads(l)
        print(f"    execucao: {e['metodo']} | {e['particao']} | {e['paginas']} pag. | "
              f"{e['segundos_por_pagina']} s/pag. | GPU {e.get('gpu')}")
    subprocess.run([sys.executable, os.path.join(RAIZ, "src", "eval", "comparar.py")], check=False)


if __name__ == "__main__":
    main()
