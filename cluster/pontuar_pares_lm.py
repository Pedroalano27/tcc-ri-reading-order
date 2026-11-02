"""Pontua continuacoes sem treino, autonomamente no cluster ou no Windows.

Somente biblioteca padrao, torch e transformers. Nao importa o repositorio.
Usa lotes com padding esquerdo e mascara apenas os tokens da continuacao.
Cada pagina e uma unidade de retomada, validada por hash do conteudo/config.
Uso: python -B pontuar_pares_lm.py --entrada pares --saida escores
     --modelo Qwen/Qwen3-8B --dtype bfloat16 --lote 8 --dispositivo cuda
--bancada golden_v4 --limite-paginas 3 executa a fumaca; --modelo falso
e exclusivamente um controle deterministico do encanamento, sem linguagem.
"""
import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def sanitizar(nome):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nome)


def ler_jsonl(path, reparar=False):
    if not path.exists():
        return
    with path.open("r+b" if reparar else "rb") as f:
        while True:
            off = f.tell()
            linha = f.readline()
            if not linha:
                break
            try:
                row = json.loads(linha)
                if not linha.endswith(b"\n"):
                    raise ValueError("Pagina incompleta")
            except (ValueError, UnicodeDecodeError):
                if reparar and not f.read(1):
                    f.seek(off)
                    f.truncate()
                    break
                raise
            yield row


def memoria():
    if os.name == "nt":
        class Mem(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
                (n, ctypes.c_size_t) for n in ("peak", "rss", "p1", "p2", "n1", "n2", "page", "peakpage")]
        m = Mem()
        m.cb = ctypes.sizeof(m)
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        ps = ctypes.windll.psapi.GetProcessMemoryInfo
        ps.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        if ps(k.GetCurrentProcess(), ctypes.byref(m), m.cb):
            return {"rss_mb": m.rss / 2**20, "pico_rss_mb": m.peak / 2**20}
    else:
        import resource
        # Linux reporta KiB; macOS reporta bytes.
        pico = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {"pico_rss_mb": pico / (2**20 if sys.platform == "darwin" else 1024)}
    return {}


class Pontuador:
    def __init__(self, a):
        self.a = a
        self.falso = a.modelo == "falso"
        self.nsp = None
        self.avisos = []
        self.torch = None
        if self.falso:
            self.revisao = "controle-deterministico-v1"
            return
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.torch = torch
        torch.set_num_threads(a.threads)
        if a.dispositivo == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA solicitada, mas indisponivel")
        self.tok = AutoTokenizer.from_pretrained(a.modelo, revision=a.revisao,
                                                 trust_remote_code=False)
        if self.tok.eos_token_id is None:
            raise ValueError("Modelo precisa de EOS para pontuar FIM")
        if self.tok.pad_token_id is None:
            self.tok.pad_token = self.tok.eos_token
        self.tok.padding_side = "left"
        self.model = AutoModelForCausalLM.from_pretrained(
            a.modelo, revision=a.revisao, torch_dtype=getattr(torch, a.dtype),
            trust_remote_code=False).to(a.dispositivo).eval()
        self.revisao = getattr(self.model.config, "_commit_hash", None)
        if a.nsp:
            from transformers import BertForNextSentencePrediction
            try:
                tok = AutoTokenizer.from_pretrained(a.nsp, trust_remote_code=False)
                model, info = BertForNextSentencePrediction.from_pretrained(
                    a.nsp, output_loading_info=True, trust_remote_code=False)
                ruins = info.get("missing_keys", []) + [str(x) for x in info.get("mismatched_keys", [])]
                if any("seq_relationship" in k for k in ruins):
                    raise ValueError("checkpoint sem cabeca NSP treinada; pesos aleatorios recusados")
                self.nsp = (tok, model.to(a.dispositivo).eval())
            except (ValueError, OSError) as exc:
                self.avisos.append("NSP ignorado: " + str(exc))
                print(self.avisos[-1], flush=True)

    def pontuar(self, pares):
        if self.falso:
            return [{"id_fonte": p["id_fonte"], "id_destino": p["id_destino"],
                     "logp_soma": -(1 + int(digest(p)[:8], 16) % 1000) / 100,
                     "logp_media": -(1 + int(digest(p)[:8], 16) % 1000) / 100,
                     "n_tokens": 1, "nsp": None} for p in pares]
        torch = self.torch
        resultado = [None] * len(pares)
        # Agrupar por contexto/tamanho reduz padding; nao promete reuso KV.
        indices = sorted(range(len(pares)), key=lambda i: (len(pares[i]["contexto"]), pares[i]["contexto"]))
        with torch.inference_mode():
            for inicio in range(0, len(indices), self.a.lote):
                ids = indices[inicio:inicio+self.a.lote]
                seqs, ncont = [], []
                for i in ids:
                    p = pares[i]
                    ctx = self.tok.encode(p["contexto"] + "\n", add_special_tokens=True)
                    cont = ([self.tok.eos_token_id] if p["id_destino"] is None else
                            self.tok.encode(" " + p["continuacao"], add_special_tokens=False))
                    if not cont or len(cont) >= self.a.max_tokens:
                        raise ValueError("Continuacao vazia ou maior que --max-tokens")
                    ctx = ctx[-(self.a.max_tokens-len(cont)):]
                    if not ctx:
                        ctx = [self.tok.eos_token_id]
                    seqs.append(ctx + cont)
                    ncont.append(len(cont))
                tam = max(map(len, seqs))
                x = torch.tensor([[self.tok.pad_token_id]*(tam-len(s))+s for s in seqs],
                                 device=self.a.dispositivo)
                mask = torch.tensor([[0]*(tam-len(s))+[1]*len(s) for s in seqs], device=x.device)
                pos = (mask.cumsum(-1)-1).clamp_min(0)
                out = self.model(input_ids=x, attention_mask=mask, position_ids=pos, use_cache=False)
                # Converte somente os logits que predizem a continuacao para float32.
                bi, ti = [], []
                for j, n in enumerate(ncont):
                    bi.extend([j]*n)
                    ti.extend(range(tam-n-1, tam-1))
                lp = out.logits[bi, ti].float().log_softmax(-1)
                alvos = x[bi, [t+1 for t in ti]]
                vals = lp.gather(1, alvos[:, None]).squeeze(1).cpu().tolist()
                cursor = 0
                nsp_vals = [None]*len(ids)
                if self.nsp:
                    ntok, nm = self.nsp
                    inp = ntok([pares[i]["contexto"] for i in ids],
                               [pares[i]["continuacao"] for i in ids],
                               padding=True, truncation=True, max_length=512, return_tensors="pt")
                    logits = nm(**{k:v.to(x.device) for k,v in inp.items()}).logits
                    # Evidencia IsNext contra NotNext, nao probabilidade calibrada.
                    nsp_vals = (logits[:, 0]-logits[:, 1]).cpu().tolist()
                for j, (i, n) in enumerate(zip(ids, ncont)):
                    soma = sum(vals[cursor:cursor+n]); cursor += n
                    if not math.isfinite(soma):
                        raise ValueError("Log-probabilidade nao finita")
                    resultado[i] = {"id_fonte": pares[i]["id_fonte"], "id_destino": pares[i]["id_destino"],
                                    "logp_soma": soma, "logp_media": soma/n,
                                    "n_tokens": n, "nsp": nsp_vals[j]}
                del out, lp, x
        return resultado


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", type=Path, required=True)
    ap.add_argument("--saida", type=Path, required=True, help="Raiz; acrescenta modelo sanitizado")
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--revisao", default="main")
    ap.add_argument("--nsp")
    ap.add_argument("--dtype", choices=("bfloat16", "float16", "float32"), default="bfloat16")
    ap.add_argument("--lote", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--dispositivo", choices=("cuda", "cpu"), default="cuda")
    ap.add_argument("--bancada")
    ap.add_argument("--limite-paginas", type=int, default=0)
    a = ap.parse_args()
    if a.lote < 1 or a.max_tokens < 2 or a.limite_paginas < 0:
        ap.error("Lote/max-tokens/limite invalidos")
    caminhos = sorted(a.entrada.glob((a.bancada or "*") + ".jsonl"))
    if not caminhos:
        ap.error("Nenhum arquivo de pares")
    saida = a.saida / sanitizar(a.modelo)
    saida.mkdir(parents=True, exist_ok=True)
    cfg = {k:v for k,v in vars(a).items() if k not in ("entrada", "saida", "bancada", "limite_paginas")}
    cfg["versao"] = "causal-continuacao-v1"
    cfg["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    cp = saida / "CONFIG.json"
    if cp.exists() and json.loads(cp.read_text(encoding="utf-8"))["config"] != cfg:
        raise ValueError("Saida ja contem outra configuracao; escolha outra --saida")
    t0 = time.perf_counter()
    pont = Pontuador(a)
    carga = time.perf_counter()-t0
    meta = {"config": cfg, "revisao_resolvida": pont.revisao, "avisos": pont.avisos,
            "nsp_ativo": pont.nsp is not None, "segundos_carga": carga,
            "memoria_carga": memoria()}
    if pont.torch:
        meta["torch"] = pont.torch.__version__
        meta["parametros"] = sum(p.numel() for p in pont.model.parameters())
        meta["gpu"] = pont.torch.cuda.get_device_name() if a.dispositivo == "cuda" else None
    if cp.exists():
        velho = json.loads(cp.read_text(encoding="utf-8"))
        if velho["revisao_resolvida"] != meta["revisao_resolvida"]:
            raise ValueError("Revisao do modelo mudou; use outra saida")
    else:
        cp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    for path in caminhos:
        dest = saida / path.name
        ja = {r["page_id"]: r for r in ler_jsonl(dest, reparar=True)}
        with dest.open("a", encoding="utf-8", newline="\n") as f:
            for k, pagina in enumerate(ler_jsonl(path)):
                if a.limite_paginas and k >= a.limite_paginas:
                    break
                sha = digest(pagina)
                pid = pagina["page_id"]
                if pid in ja:
                    if ja[pid]["pares_sha256"] != sha:
                        raise ValueError("Pares mudaram para pagina ja pontuada: " + pid)
                    continue
                if pont.torch and a.dispositivo == "cuda":
                    pont.torch.cuda.reset_peak_memory_stats()
                    pont.torch.cuda.synchronize()
                t = time.perf_counter()
                valores = pont.pontuar(pagina["pares"])
                if pont.torch and a.dispositivo == "cuda":
                    pont.torch.cuda.synchronize()
                secs = time.perf_counter()-t
                mem = memoria()
                if pont.torch and a.dispositivo == "cuda":
                    mem.update(cuda_pico_alocado_mb=pont.torch.cuda.max_memory_allocated()/2**20,
                               cuda_pico_reservado_mb=pont.torch.cuda.max_memory_reserved()/2**20)
                row = {"page_id": pid, "pares_sha256": sha, "config_sha256": digest(cfg),
                       "segundos": secs, "memoria": mem, "escores": valores}
                f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+"\n")
                f.flush(); os.fsync(f.fileno())
                ja[pid] = row
                print(json.dumps({"bancada": path.stem, "pagina": k+1, "pares": len(valores),
                                  "segundos": secs, "memoria": mem}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
