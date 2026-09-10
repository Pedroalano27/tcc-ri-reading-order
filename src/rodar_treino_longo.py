"""
Segunda rodada: treino LONGO do LayoutLM e da ablação sem layout.

Na primeira rodada (8 épocas, 56 s) a curva de validação do LayoutLM ainda
subia a cada época -- o modelo estava subtreinado. Aqui os dois modelos
recebem o MESMO orçamento (40 épocas, até 7 min cada), para que a ablação
seja uma comparação justa.

O script espera a fase de GPU do orquestrador (src/rodar_experimentos.py)
terminar, roda treinos e avaliações, espera o orquestrador encerrar de vez e
refaz a comparação e as figuras.

Uso:
    python src/rodar_treino_longo.py
"""
from __future__ import annotations

import os
import sys
import time
import subprocess

import psutil

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOGS = os.path.join(RAIZ, "resultados", "logs")
AMBIENTE = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
            "HF_HUB_OFFLINE": "1", "TRANSFORMERS_VERBOSITY": "error"}


def rodando(trecho):
    for p in psutil.process_iter(["cmdline"]):
        try:
            if trecho in " ".join(p.info["cmdline"] or []):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def rodar(cmd, nome):
    t0 = time.time()
    with open(os.path.join(LOGS, f"{nome}.log"), "w", encoding="utf-8") as f:
        r = subprocess.run([PY] + cmd, stdout=f, stderr=subprocess.STDOUT, cwd=RAIZ, env=AMBIENTE)
    print(f"[{time.strftime('%H:%M:%S')}] {'OK    ' if r.returncode == 0 else 'FALHOU'} "
          f"{' '.join(cmd)}  ({time.time() - t0:.0f}s, log: resultados/logs/{nome}.log)", flush=True)


def main():
    os.makedirs(LOGS, exist_ok=True)
    marco_ablacao = os.path.join(RAIZ, "resultados", "pred_layoutlm_sem_layout.jsonl")
    print(f"[{time.strftime('%H:%M:%S')}] aguardando a fase de GPU do orquestrador...", flush=True)
    while True:
        gpu_ocupada = rodando("llm_ordem.py") or rodando("layoutlm_ordem.py")
        if not gpu_ocupada and (os.path.exists(marco_ablacao) or not rodando("rodar_experimentos.py")):
            break
        time.sleep(5)

    print(f"[{time.strftime('%H:%M:%S')}] GPU livre: iniciando os treinos longos", flush=True)
    rodar(["src/models/layoutlm_ordem.py", "treinar", "--epocas", "40", "--max-minutos", "7"],
          "longo_layoutlm_treinar")
    rodar(["src/models/layoutlm_ordem.py", "avaliar"], "longo_layoutlm_avaliar")
    rodar(["src/models/layoutlm_ordem.py", "treinar", "--sem-layout", "--epocas", "40", "--max-minutos", "7"],
          "longo_sem_layout_treinar")
    rodar(["src/models/layoutlm_ordem.py", "avaliar", "--sem-layout"], "longo_sem_layout_avaliar")

    while rodando("rodar_experimentos.py"):
        time.sleep(5)
    rodar(["src/eval/comparar.py"], "longo_comparar")
    rodar(["src/eval/figuras.py"], "longo_figuras")
    print(f"[{time.strftime('%H:%M:%S')}] segunda rodada concluída", flush=True)


if __name__ == "__main__":
    main()
