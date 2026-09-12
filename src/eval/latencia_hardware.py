"""
Latencia por pagina de cada metodo NO HARDWARE ATUAL, com o mesmo roteiro de medicao.

Eficiencia so e comparavel na mesma maquina. Este script mede, nas paginas de teste:
  naive, xycut     em CPU, so a partir das caixas (como em baselines.py)
  BiLSTM geo       em CPU (como em lstm_ordem.py)
  LayoutLM         na GPU, batch 1, tokenizacao incluida (como em layoutlm_ordem.py)
O tempo dos modelos nao depende dos pesos treinados: sem checkpoint, usa-se a mesma
arquitetura recem-inicializada -- a conta e identica. Cada pagina e medida em varias
passadas e fica a mediana, para reduzir o ruido.

As LLMs tem a latencia medida pelo proprio llm_ordem.py, na mesma maquina.
Grava resultados/latencia_<maquina>.json.

Uso:
    python src/eval/latencia_hardware.py --maquina notebook_rtx4050
    python src/eval/latencia_hardware.py --maquina kaggle_t4
"""
from __future__ import annotations

import os
import sys
import json
import time
import platform
import argparse
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import carregar_particao, ordem_entrada, DIR_RESULTADOS  # noqa: E402
from src.eval.baselines import caixas  # noqa: E402
from src.data.extrator import xycut  # noqa: E402


def nome_cpu():
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo") as f:
            for l in f:
                if l.startswith("model name"):
                    return l.split(":", 1)[1].strip()
    return platform.processor() or platform.machine()


def resumo(tempos):
    s = sorted(tempos)
    return {"media_ms": statistics.mean(s), "mediana_ms": statistics.median(s),
            "p90_ms": s[min(len(s) - 1, int(0.9 * len(s)))], "paginas": len(s)}


def medir_cpu(fn, paginas, passadas):
    por_pagina = []
    for p in paginas:
        entrada = ordem_entrada(p)
        ts = []
        for _ in range(passadas):
            t0 = time.perf_counter()
            fn(p, entrada)
            ts.append((time.perf_counter() - t0) * 1000)
        por_pagina.append(statistics.median(ts))
    return por_pagina


def naive(p, entrada):
    B = caixas(p)
    return sorted(entrada, key=lambda i: (B[i]["top"], B[i]["x0"]))


def xy(p, entrada):
    return xycut(list(entrada), caixas(p))


def medir_lstm(paginas, passadas):
    import torch
    from src.models.lstm_ordem import LSTMOrdem, preparar, prever
    torch.set_num_threads(min(6, os.cpu_count() or 1))
    preparar(paginas)
    modelo = LSTMOrdem("geo")
    prever(modelo, paginas[:4])
    varreduras = [[t for _, t in prever(modelo, paginas, medir_tempo=True)] for _ in range(passadas)]
    return [statistics.median(ts) for ts in zip(*varreduras)]


def medir_layoutlm(paginas, passadas):
    import torch
    if not torch.cuda.is_available():
        return None, None
    from transformers import AutoTokenizer
    from src.models.layoutlm_ordem import LayoutLMOrdem, Codificador, prever, MODELO_BASE, DIR_MODELOS
    cod = Codificador(AutoTokenizer.from_pretrained(MODELO_BASE))
    modelo = LayoutLMOrdem(MODELO_BASE).to("cuda")
    ckpt = os.path.join(DIR_MODELOS, "layoutlm.pt")
    com_pesos = os.path.exists(ckpt)
    if com_pesos:
        modelo.load_state_dict(torch.load(ckpt, map_location="cuda"))
    prever(modelo, cod, paginas[:4], "cuda", medir_tempo=True)          # aquecimento
    varreduras = []
    for _ in range(passadas):
        for p in paginas:
            for c in p["bounding_boxes"]:
                c.pop("_tok", None)
        varreduras.append([t for _, t in prever(modelo, cod, paginas, "cuda", medir_tempo=True)])
    return [statistics.median(ts) for ts in zip(*varreduras)], com_pesos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maquina", required=True, help="rotulo da maquina, ex.: kaggle_t4")
    ap.add_argument("--passadas", type=int, default=3)
    a = ap.parse_args()

    teste = carregar_particao("teste")
    info = {"maquina": a.maquina, "cpu": nome_cpu(), "nucleos": os.cpu_count(), "python": platform.python_version(),
            "sistema": platform.platform(), "data": time.strftime("%Y-%m-%d %H:%M:%S"), "metodos": {}}
    info["metodos"]["naive"] = resumo(medir_cpu(naive, teste, a.passadas))
    info["metodos"]["xycut"] = resumo(medir_cpu(xy, teste, a.passadas))
    print(f"[OK] naive {info['metodos']['naive']['media_ms']:.3f} ms | xycut {info['metodos']['xycut']['media_ms']:.3f} ms",
          flush=True)
    info["metodos"]["lstm_geo"] = resumo(medir_lstm(teste, a.passadas))
    print(f"[OK] BiLSTM geo {info['metodos']['lstm_geo']['media_ms']:.2f} ms", flush=True)

    import torch
    info["torch"] = torch.__version__
    tempos, com_pesos = medir_layoutlm(teste, a.passadas)
    if tempos:
        info["gpu"] = torch.cuda.get_device_name(0)
        info["metodos"]["layoutlm"] = {**resumo(tempos), "com_pesos_treinados": com_pesos}
        print(f"[OK] LayoutLM {info['metodos']['layoutlm']['media_ms']:.2f} ms ({info['gpu']})", flush=True)
    else:
        print("[!] sem GPU CUDA: LayoutLM nao medido")

    caminho = os.path.join(DIR_RESULTADOS, f"latencia_{a.maquina}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"[OK] -> {caminho}")


if __name__ == "__main__":
    main()
