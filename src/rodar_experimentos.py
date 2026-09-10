"""
Orquestra a bateria completa de experimentos (depois da extracao de blocos).

  1. caracterizacao do acervo + divisao por veiculo      (CPU)
  2. baselines nao-aprendidos                             (CPU)
  3. em paralelo:
       GPU, em serie:  LayoutLM treino -> avaliacao -> [comparacao parcial]
                       -> LLM zero-shot -> ablacao sem layout -> avaliacao
       CPU, em serie:  BiLSTM texto+geo -> so geometria -> so texto
  4. comparacao final e figuras

Logs de cada etapa em resultados/logs/. Uma etapa que falha nao interrompe as
seguintes (exceto a caracterizacao, da qual todas dependem).

Uso:
    python src/rodar_experimentos.py
"""
from __future__ import annotations

import os
import sys
import time
import threading
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
DIR_LOGS = os.path.join(RAIZ, "resultados", "logs")

AMBIENTE = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
            "HF_HUB_OFFLINE": "1", "TRANSFORMERS_VERBOSITY": "error"}

INICIAIS = [["src/eval/caracterizar.py"], ["src/eval/baselines.py"]]
GPU = [
    ["src/models/layoutlm_ordem.py", "treinar", "--max-minutos", "10", "--epocas", "8"],
    ["src/models/layoutlm_ordem.py", "avaliar"],
    "PARCIAL",
    ["src/eval/llm_ordem.py", "--modelo", "llava:7b", "--paginas", "20", "--max-blocos", "25"],
    ["src/models/layoutlm_ordem.py", "treinar", "--sem-layout", "--max-minutos", "6", "--epocas", "4"],
    ["src/models/layoutlm_ordem.py", "avaliar", "--sem-layout"],
]
CPU = [["src/models/lstm_ordem.py", "--variante", v, "--threads", "4", "--max-minutos", "4"]
       for v in ("geo_texto", "geo", "texto")]
FINAIS = [["src/eval/comparar.py"], ["src/eval/figuras.py"]]

_trava = threading.Lock()


def rodar(cmd):
    nome = "_".join(os.path.basename(c).replace(".py", "") for c in cmd if not c.startswith("--"))[:60]
    nome = nome.replace(":", "_")   # ':' no Windows cria um fluxo alternativo NTFS em vez de um arquivo
    log = os.path.join(DIR_LOGS, f"{nome}.log")
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as f:
        r = subprocess.run([PY] + cmd, stdout=f, stderr=subprocess.STDOUT, cwd=RAIZ, env=AMBIENTE)
    with _trava:
        print(f"[{time.strftime('%H:%M:%S')}] {'OK    ' if r.returncode == 0 else 'FALHOU'} "
              f"{' '.join(cmd)}  ({time.time() - t0:.0f}s, log: resultados/logs/{nome}.log)", flush=True)
    return r.returncode


def main():
    os.makedirs(DIR_LOGS, exist_ok=True)
    t0 = time.time()
    for cmd in INICIAIS:
        if rodar(cmd) != 0 and "caracterizar" in cmd[0]:
            print("[!] caracterizacao falhou - abortando")
            return

    fio_cpu = threading.Thread(target=lambda: [rodar(c) for c in CPU])
    fio_cpu.start()
    for cmd in GPU:
        if cmd == "PARCIAL":
            for c in FINAIS:
                rodar(c)
            continue
        rodar(cmd)
    fio_cpu.join()

    for cmd in FINAIS:
        rodar(cmd)
    print(f"\n[FIM] bateria completa em {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
