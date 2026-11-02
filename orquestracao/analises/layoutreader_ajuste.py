"""Ajusta LayoutReader local sobre silver de linhas, sem baixar nada.

Reusa o treinador em fluxo, token de caixa unico e decoder ja conferido pela
bancada. Ajusta ultimas quatro camadas e classificador para caber em 6 GB;
GPU usa fp16 AMP e gradient checkpointing, CPU usa float32. Retoma modelo,
AdamW, scheduler, scaler, cursor e RNG. Nao altera o snapshot de terceiros.

Fumaca CPU: --device cpu --n-treino 8 --batch 4 --micro-batch 1 --max-passos 2
 --epocas 4 --max-minutos 15 --nome fumaca_layoutreader
 --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_layoutreader
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from orquestracao.analises import treinar_sem_caixas as t

if __name__ == "__main__":
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = t.parser()
    ap.set_defaults(modelo="layoutreader",representacao="linhas",epocas=4,max_minutos=75,
        nome="layoutreader_ajustado_linhas",dir_saida=t.OUT/"layoutreader_ajustado_linhas")
    a = ap.parse_args()
    if a.modelo != "layoutreader" or a.representacao != "linhas":
        raise ValueError("Este roteiro e especifico para LayoutReader/linhas")
    t.treinar(a)
