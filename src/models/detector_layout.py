"""
Detector de layout treinado nas 9 classes do Diamond (fine-tune de uma YOLO).

Ideia
-----
Trocar o extrator que depende das palavras do PDF por um detector que trabalha da
IMAGEM. Ataca a classe (ponto fraco, ~0,80), enxerga texto que e so imagem e deixa de
depender da camada de texto do PDF -- os tres furos do extrator de hoje.

Modelo base (leve, a pedido): YOLOv8s (~11 M par., ~10-30 ms/pagina na GPU, roda ate na
CPU). Para partir de pesos ja treinados em documentos, aponte --modelo para os pesos do
DocLayout-YOLO (pre-treinado no DocLayNet); a API e a mesma da ultralytics.

Depende de `ultralytics` (nao instalada por padrao):
    venv\\Scripts\\pip install ultralytics

Subcomandos
-----------
  treinar   fine-tune sobre o dataset gerado por src/data/exportar_deteccao.py
  prever    roda o detector nas imagens de um lote Diamond e grava as regioes previstas
            em pontos do PDF, no formato que src/eval/avaliar_diamond.py --pred consome
            (assim a saida crua do detector e medida contra o ouro, mesmo criterio da
            segmentacao atual).

Uso
---
    venv\\Scripts\\python.exe src\\models\\detector_layout.py treinar \\
        --dados data/deteccao/diamond_yolo/data.yaml --epocas 100 --imgsz 1024 --batch 16
    venv\\Scripts\\python.exe src\\models\\detector_layout.py prever \\
        --pesos runs/detect/diamond/weights/best.pt --lote diamond_treino \\
        --saida resultados/deteccao/pred_yolo_diamond_treino.jsonl
"""
from __future__ import annotations

import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.regioes import CLASSES  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond")


def _yolo(modelo):
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit("[ERRO] ultralytics nao instalada. Rode: venv\\Scripts\\pip install ultralytics")
    return YOLO(modelo)


def treinar(a):
    projeto = a.projeto if os.path.isabs(a.projeto) else os.path.join(RAIZ, a.projeto)
    ultimo = os.path.join(projeto, a.nome, "weights", "last.pt")
    if a.retomar and os.path.exists(ultimo):      # continua um treino interrompido, da ultima epoca salva
        # workers vale tambem na retomada: no Windows cada worker e um processo de ~1 GB e a validacao
        # abre o dobro deles; com 4, o treino sozinho comprometia 20 GB numa maquina de 16 GB
        _yolo(ultimo).train(resume=True, workers=a.workers)
        print(f"[OK] treino retomado e concluido. Pesos em {os.path.join(projeto, a.nome, 'weights', 'best.pt')}")
        return
    modelo = _yolo(a.modelo)
    modelo.train(data=a.dados, epochs=a.epocas, imgsz=a.imgsz, batch=a.batch,
                 device=a.dispositivo, project=projeto, name=a.nome, seed=a.seed,
                 patience=a.paciencia, exist_ok=True, fliplr=a.fliplr, workers=a.workers)
    print(f"[OK] treino concluido. Pesos em {os.path.join(projeto, a.nome, 'weights', 'best.pt')}")


def prever(a):
    from PIL import Image
    modelo = _yolo(a.pesos)
    dir_lote = os.path.join(DIR_DIAMOND, a.lote)
    tarefas = {}
    with open(os.path.join(dir_lote, "tarefas.jsonl"), encoding="utf-8") as f:
        for l in f:
            if l.strip():
                t = json.loads(l)
                tarefas[t["page_id"]] = t
    saida = a.saida if os.path.isabs(a.saida) else os.path.join(RAIZ, a.saida)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    n = 0
    with open(saida, "w", encoding="utf-8") as out:
        for pid, t in tarefas.items():
            img = os.path.join(dir_lote, "img", t["imagem"])
            if not os.path.exists(img):
                continue
            w_pt, h_pt = float(t["dimensions"]["width"]), float(t["dimensions"]["height"])
            w_px, h_px = Image.open(img).size
            sx, sy = w_pt / w_px, h_pt / h_px          # px do detector -> pontos do PDF
            res = modelo.predict(img, imgsz=a.imgsz, conf=a.conf, device=a.dispositivo, verbose=False)[0]
            regioes = []
            for i, b in enumerate(res.boxes):
                x0, y0, x1, y1 = (float(v) for v in b.xyxy[0].tolist())
                # nome da classe vem do proprio modelo (9 do Diamond, 16 do guia ou 3 do plano grosso)
                regioes.append({"id": f"d{i}", "classe": res.names[int(b.cls[0])],
                                "bbox": [round(x0 * sx, 1), round(y0 * sy, 1),
                                         round(x1 * sx, 1), round(y1 * sy, 1)],
                                "score": round(float(b.conf[0]), 4)})
            out.write(json.dumps({"page_id": pid, "regioes": regioes}, ensure_ascii=False) + "\n")
            n += 1
    print(f"[OK] {n} paginas previstas -> {os.path.relpath(saida, RAIZ)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("treinar")
    t.add_argument("--dados", default="data/deteccao/diamond_yolo/data.yaml")
    t.add_argument("--modelo", default="yolov8s.pt", help="pesos base (ou os do DocLayout-YOLO)")
    t.add_argument("--epocas", type=int, default=100)
    t.add_argument("--imgsz", type=int, default=1024)
    t.add_argument("--batch", type=int, default=16)
    t.add_argument("--paciencia", type=int, default=20)
    t.add_argument("--dispositivo", default=0, help="0 para a primeira GPU; 'cpu' para CPU")
    t.add_argument("--projeto", default="runs/detect")
    t.add_argument("--nome", default="diamond")
    t.add_argument("--seed", type=int, default=42)
    t.add_argument("--fliplr", type=float, default=0.5,
                   help="prob. de espelhar na horizontal (padrao da ultralytics; 0 para pagina de documento)")
    t.add_argument("--workers", type=int, default=8)
    t.add_argument("--retomar", action="store_true",
                   help="se existir weights/last.pt do mesmo --nome, continua dele em vez de recomecar")
    t.set_defaults(func=treinar)

    p = sub.add_parser("prever")
    p.add_argument("--pesos", required=True)
    p.add_argument("--lote", required=True, help="lote Diamond com img/ e tarefas.jsonl")
    p.add_argument("--saida", required=True, help="jsonl page_id->regioes (pontos do PDF)")
    p.add_argument("--imgsz", type=int, default=1024)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--dispositivo", default=0)
    p.set_defaults(func=prever)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
