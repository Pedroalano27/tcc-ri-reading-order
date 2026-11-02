"""Carrega um checkpoint e prediz as tres bancadas em CPU, pagina por pagina.

Usa o contrato estrito da bancada, sem expandir unidades nem consultar ouro.
Checkpoint e shards sao identificados por hash. Cada predicao e fsync em JSONL;
retoma por page_id e remove apenas a ultima linha truncada do arquivo proprio.
--avaliar invoca bancada_ordenadores.py --avaliar-pred depois de liberar a rede.

Uso: venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas.py
 --checkpoint resultados/ordenadores_treinados_sem_caixas/lstm_geo_linhas/melhor.pt
 --avaliar
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(RAIZ))
import argparse
import gc
import json
import os
import subprocess
import time
import re
import statistics
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  HF_DEACTIVATE_ASYNC_LOAD="1", OMP_NUM_THREADS="4", MKL_NUM_THREADS="4")
import torch
from orquestracao.analises import treinar_sem_caixas as t
from orquestracao.analises import bancada_ordenadores as b


def relatorio_final():
    """Completa o relatorio com evidencias executadas e leitura dos resultados."""
    t.relatorio()
    path = RAIZ / "resultados/ordenadores_treinados_sem_caixas.md"
    texto = path.read_text(encoding="utf-8")
    linhas = []
    for l in texto.splitlines():
        if l.startswith("|"):
            l = re.sub(r"(?<=\d)\.(?=\d)", ",", l)
            l = l.replace("| Device |", "| Dispositivo |").replace("| True |", "| sim |").replace("| False |", "| não |")
        linhas.append(l)
    R = t.ler(RAIZ / "resultados/ordenadores_sem_caixas.json")
    r0 = R["resultados"]["regra_colunas__linhas__golden_v4"]
    aprendidos = [v for v in R["resultados"].values() if v["ordenador"].startswith("lstm_")
        and v["representacao"] == "linhas" and v["bancada"] == "golden_v4" and v["completa"]]
    if aprendidos:
        media = lambda r,k: statistics.mean(p["metricas"][k] for p in r["paginas"])
        linhas += ["", "## Leitura do resultado principal", "",
            "| Ordenador em linhas, v4 | τ palavras | Quebras/página |", "|---|---:|---:|"]
        for r in [r0] + sorted(aprendidos,key=lambda x:x["ordenador"]):
            linhas.append(f"| {r['ordenador']} | {media(r,'tau'):.6f} | {media(r,'quebras'):.2f} |".replace(".",","))
        if all(media(r,"quebras") > media(r0,"quebras") for r in aprendidos):
            linhas += ["", "Os BiLSTMs em linhas avaliados até aqui tiveram mais quebras de leitura que a regra de colunas. Portanto este orçamento de treino não sustenta ganho de continuidade por BiLSTM."]
    alvos = [("sucessor_linhas","linhas"),("layoutreader_ajustado_linhas","linhas"),
             ("sucessor_colunas_margens","colunas_margens"),("pontual_linhas","linhas")]
    pendentes = [f"{m}__{rep}__{bancada}" for m,rep in alvos for bancada in b.BANCADAS
        if not R["resultados"].get(f"{m}__{rep}__{bancada}",{}).get("completa")]
    linhas += ["", f"Transformers da fila: {len(pendentes)} avaliações completas ainda pendentes. A comparação com eles só pode ser concluída após a execução dos roteiros."] if pendentes else ["", "As avaliações dos Transformers da fila estão completas e constam das tabelas acima."]
    linhas += ["", "## Evidência das fumaças em CPU", "",
        "| Fumaça | Páginas selecionadas | Visitadas | Passos de otimizador | Bancadas inferidas | Isolamento do ouro |", "|---|---:|---:|---:|---:|---|"]
    for cp in sorted(t.OUT.glob("fumaca_*/treino.json")):
        info = t.ler(cp)
        ds = list((cp.parent / "pred_fumaca").glob("*__tempos.json"))
        checks = [d for p in ds for d in t.ler(p).values()]
        ok = bool(checks) and all(d.get("isolamento_ouro") and "metricas_fumaca" in d for d in checks)
        linhas.append(f"| {info['config']['nome']} | {info['paginas_treino']} | {info.get('paginas_visitadas',0)} | {info.get('passos',0)} | {len(checks)} | {'sim' if ok else 'pendente'} |")
    linhas += ["", "Fumaças usam CPU/float32, sem carregar outra rede em paralelo. Cada inferência limitada confere permutação, avalia pela função original da bancada e repete a predição sem referência de unidades. Seus valores de eficácia são controles de execução, não avaliações completas. JSONs de treino e tempos em `resultados/ordenadores_treinados_sem_caixas/fumaca_*/` preservam os números.", "",
        "O Bash desta sessão falhou antes de analisar os roteiros (`CreateFileMapping`, erro de acesso do Windows). Por isso a prova executável usa diretamente o Python do projeto com os mesmos argumentos. A sintaxe Bash precisa de conferência no terminal da fila. Nenhum pico de memória/tempo em GPU foi medido; micro-lote e congelamento de camadas são escolhas de execução a confirmar quando a fila rodar.", ""]
    path.write_text("\n".join(linhas),encoding="utf-8")


def retomar(path):
    """Repara so EOF incompleto do nosso arquivo, nunca uma predicao invalida."""
    vistos = set()
    if not path.exists():
        return vistos
    with path.open("r+b") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                f.seek(off)
                f.truncate()
                break
            q = json.loads(line.decode("utf-8"))
            if q["page_id"] in vistos:
                raise ValueError("Page_id duplicado no arquivo de predicao")
            vistos.add(q["page_id"])
    return vistos


def executar(a):
    ck = torch.load(a.checkpoint, map_location="cpu", weights_only=False)
    config = dict(ck["config"])
    config["device"] = "cpu"
    cfg = argparse.Namespace(**config)
    rep, nome = cfg.representacao, cfg.nome
    a.dir_saida.mkdir(parents=True,exist_ok=True)
    paths = [a.dir_saida / f"{nome}__{rep}__{bancada}.jsonl" for bancada in a.bancadas]
    meta = a.dir_saida / f"{nome}__{rep}__checkpoint.json"
    fingerprint = {"checkpoint_sha256":t.sha(a.checkpoint),"config":config,"fontes":b.fontes()}
    if meta.exists() and t.ler(meta) != fingerprint:
        raise ValueError("Modelo/fontes mudaram; nao misturar predicoes")
    t.gravar(meta,fingerprint)
    model, cod = t.criar_modelo(cfg)
    model.load_state_dict(ck["modelo"])
    del ck
    model.eval()
    diagnosticos = {}
    for bancada,path in zip(a.bancadas,paths):
        vistos = retomar(path)
        esperado = set()
        with path.open("a",encoding="utf-8",newline="\n") as f:
            for i, (obj,p) in enumerate(b.paginas(bancada,rep)):
                pid = p["page_id"]
                esperado.add(pid)
                if a.limite and i >= a.limite:
                    break
                if pid in vistos:
                    continue
                # So p entra no preditor; obj contem ouro/palavras e nao e passado.
                inicio = time.perf_counter()
                pred = t.prever(model,cod,p,cfg)
                ids = [u["id"] for u in p["bounding_boxes"]]
                if len(pred) != len(ids) or set(pred) != set(ids) or len(set(pred)) != len(pred):
                    raise ValueError(f"Predicao nao e permutacao: {pid}")
                f.write(json.dumps({"page_id":pid,"ordem":pred},ensure_ascii=False)+"\n")
                f.flush()
                os.fsync(f.fileno())
                diagnosticos[pid] = {"tempo_ms":1000*(time.perf_counter()-inicio),
                    "unidades":len(ids),"hierarquia":cfg.modelo != "lstm" and len(ids)>510}
                if a.limite:
                    # Fumaca real: contrato + regua existente + isolamento do ouro.
                    sem_ouro = {k:v for k,v in p.items() if k != "ordens"}
                    if t.prever(model,cod,sem_ouro,cfg) != pred:
                        raise AssertionError("Preditor depende da referencia de unidades")
                    diagnosticos[pid]["isolamento_ouro"] = True
                    diagnosticos[pid]["metricas_fumaca"] = b.metricas(obj,p,pred)
                if (i+1)%20 == 0:
                    print(f"[inferir] {nome} {rep} {bancada}: {i+1}",flush=True)
        if not a.limite and not vistos <= esperado:
            raise ValueError("Predicoes possuem pagina fora da bancada")
        print(f"[pred] {path}",flush=True)
    t.gravar(a.dir_saida/f"{nome}__{rep}__tempos.json",diagnosticos)
    del model,cod
    gc.collect()
    if a.avaliar:
        for path in paths:
            subprocess.run([sys.executable,"-B",str(RAIZ/"orquestracao/analises/bancada_ordenadores.py"),
                "--avaliar-pred",str(path)],cwd=RAIZ,check=True)
        relatorio_final()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint",type=Path)
    ap.add_argument("--relatorio",action="store_true")
    ap.add_argument("--dir-saida",type=Path,default=t.OUT/"pred")
    ap.add_argument("--bancadas",nargs="+",choices=b.BANCADAS,default=list(b.BANCADAS))
    ap.add_argument("--limite",type=int,default=0)
    ap.add_argument("--avaliar",action="store_true")
    a = ap.parse_args()
    if a.relatorio:
        relatorio_final()
    elif a.checkpoint is None:
        ap.error("Informe --checkpoint ou --relatorio")
    else:
        executar(a)


if __name__ == "__main__":
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
