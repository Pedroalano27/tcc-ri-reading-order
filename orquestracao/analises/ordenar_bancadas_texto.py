"""Reconstrui ComTexto para inferir checkpoints textuais nas mesmas bancadas.

Importa ordenar_bancadas.executar: nao copia sua inferencia, reparo de EOF ou
teste de isolamento do ouro. Desliga apenas o subprocesso de avaliacao que
escreveria historicos e chama avaliar importado com destinos novos, depois
de a rede ser liberada. --limite 1 em cada bancada prova tres paginas em CPU.

Uso: venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas_texto.py
 --checkpoint resultados/ordenadores_treinados_sem_caixas/fumaca_texto/melhor.pt
 --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto/pred_fumaca_texto
 --limite 1 --avaliar
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import argparse
import gc

from orquestracao.analises import treinar_sem_caixas_texto as texto
from orquestracao.analises import ordenar_bancadas as original


def executar(a):
    a.dir_saida = texto.saida_segura(a.dir_saida)
    # Ler apenas treino.json para validar identidade antes de carregar os pesos.
    info = texto.t.ler(a.checkpoint.parent / "treino.json")
    if (info.get("codificador") != texto.VERSAO or
            info["config"].get("codificador_texto") != texto.identidade_codificador()):
        raise ValueError("Checkpoint/tokenizador/codigo nao corresponde a ComTexto")
    cfg = info["config"]
    if cfg["modelo"] not in ("sucessor", "pontual"):
        raise ValueError("Checkpoint nao e LayoutLM textual")
    texto.relatorio()
    avaliar, a.avaliar = a.avaliar, False
    try:
        # A checagem antecede inclusive metricas_fumaca da inferencia original.
        texto.conferir_ancoras()
        with texto.instalar(), texto.bancada_isolada() as b, b.trava():
            original.executar(a)
            gc.collect()
            if avaliar:
                # Um unico processo: a rede ja foi apagada por executar().
                R = b.iniciar()
                b.conferir_ancoras(R)
                for bancada in a.bancadas:
                    path = a.dir_saida / f"{cfg['nome']}__{cfg['representacao']}__{bancada}.jsonl"
                    b.avaliar(path, estado=R)
    finally:
        a.avaliar = avaliar
        texto.relatorio()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--relatorio", action="store_true")
    ap.add_argument("--dir-saida", type=Path, default=texto.OUT / "pred_texto")
    ap.add_argument("--bancadas", nargs="+", choices=original.b.BANCADAS,
                    default=list(original.b.BANCADAS))
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--avaliar", action="store_true")
    a = ap.parse_args()
    if a.limite < 0:
        ap.error("--limite deve ser nao negativo")
    if a.relatorio:
        texto.relatorio()
    elif a.checkpoint is None:
        ap.error("Informe --checkpoint ou --relatorio")
    else:
        executar(a)


if __name__ == "__main__":
    main()
