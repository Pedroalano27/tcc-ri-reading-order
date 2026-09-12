"""
LayoutLM para deteccao de ordem de leitura, formulada como LEARNING TO RANK.

Formulacao (pontual): cada bloco recebe um escore; ordenar os blocos pelo
escore produz a ordem de leitura predita. O alvo de cada bloco e sua posicao
normalizada na ordem de referencia, rank / (n - 1), com perda MSE.

Entrada do modelo:
  - os blocos da pagina EMBARALHADOS (permutacao nova a cada epoca no treino,
    permutacao fixa do protocolo na avaliacao). Como a ordem de entrada nao
    carrega informacao, o modelo so pode acertar usando o TEXTO e a GEOMETRIA 2D.
  - cada bloco contribui com seus primeiros K tokens WordPiece, todos com a
    bounding box do bloco normalizada para 0-1000 (convencao do LayoutLM).
  - o escore do bloco sai de uma cabeca MLP sobre a media dos estados ocultos
    dos seus tokens.

Ablacao --sem-layout: zera todas as bounding boxes. O modelo ve so o texto --
isola quanto da eficacia vem da consciencia de layout.

Uso:
    python src/models/layoutlm_ordem.py treinar  [--sem-layout] [--epocas 8] [--max-minutos 16]
    python src/models/layoutlm_ordem.py avaliar  [--sem-layout]

Curva de aprendizado (treino ampliado com paginas extras dos mesmos veiculos):
    python src/models/layoutlm_ordem.py treinar --nome curva_n1000 --n-treino 1000 \
        --blocos-extra data/processed/blocos_extra --dir-saida resultados/curva_aprendizado
    python src/models/layoutlm_ordem.py avaliar --nome curva_n1000 --dir-saida resultados/curva_aprendizado
"""
from __future__ import annotations

import os
import sys
import csv
import json
import math
import time
import random
import argparse

import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import (carregar_splits, carregar_particao, montar_treino,  # noqa: E402
                                ordem_entrada, salvar_predicoes, DIR_RESULTADOS, RAIZ_PROJETO)
from src.eval.metrics import kendall_tau, ard_normalizado  # noqa: E402

MODELO_BASE = "microsoft/layoutlm-base-uncased"
DIR_MODELOS = os.path.join(RAIZ_PROJETO, "models", "layoutlm_ordem")
MAX_LEN = 512
MAX_TOK_BLOCO = 8


def normalizar_bbox(bbox, W, H):
    x0, y0, x1, y1 = bbox
    f = lambda v, d: max(0, min(1000, int(round(1000 * v / d))))
    a = [f(x0, W), f(y0, H), f(x1, W), f(y1, H)]
    a[2], a[3] = max(a[2], a[0]), max(a[3], a[1])
    return a


class Codificador:
    """Transforma uma pagina (numa dada ordem de entrada) em tensores do LayoutLM."""

    def __init__(self, tok):
        self.tok = tok
        self.cls, self.sep = tok.cls_token_id, tok.sep_token_id
        self.pad, self.unk = tok.pad_token_id, tok.unk_token_id

    def pretokenizar(self, paginas):
        textos, refs = [], []
        for p in paginas:
            for c in p["bounding_boxes"]:
                if "_tok" not in c:
                    textos.append(" ".join(c["text"].split()[:24]))
                    refs.append(c)
        for i in range(0, len(textos), 4096):
            enc = self.tok(textos[i:i + 4096], add_special_tokens=False,
                           truncation=True, max_length=MAX_TOK_BLOCO)
            for c, ids in zip(refs[i:i + 4096], enc["input_ids"]):
                c["_tok"] = ids or [self.unk]

    def codificar(self, p, ordem):
        n = len(ordem)
        K = max(1, min(MAX_TOK_BLOCO, (MAX_LEN - 2) // n))
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        ids, bb, blk = [self.cls], [[0, 0, 0, 0]], [-1]
        for j, bi in enumerate(ordem):
            c = p["bounding_boxes"][bi]
            nb = normalizar_bbox(c["bbox"], W, H)
            for t in c["_tok"][:K]:
                ids.append(t)
                bb.append(nb)
                blk.append(j)
        ids.append(self.sep)
        bb.append([1000, 1000, 1000, 1000])
        blk.append(-1)
        return ids, bb, blk


def montar_lote(cod, paginas, ordens, ref_key, device):
    seqs = [cod.codificar(p, o) for p, o in zip(paginas, ordens)]
    B, T, N = len(seqs), max(len(s[0]) for s in seqs), max(len(o) for o in ordens)
    input_ids = torch.full((B, T), cod.pad, dtype=torch.long)
    bbox = torch.zeros((B, T, 4), dtype=torch.long)
    att = torch.zeros((B, T), dtype=torch.long)
    blk = torch.full((B, T), -1, dtype=torch.long)
    for i, (a, b, c) in enumerate(seqs):
        L = len(a)
        input_ids[i, :L] = torch.tensor(a)
        bbox[i, :L] = torch.tensor(b)
        att[i, :L] = 1
        blk[i, :L] = torch.tensor(c)
    lote = {"input_ids": input_ids, "bbox": bbox, "attention_mask": att, "bloco_de": blk}
    if ref_key is not None:
        alvo, mask = torch.zeros((B, N)), torch.zeros((B, N))
        for i, (p, o) in enumerate(zip(paginas, ordens)):
            pos = {bid: k for k, bid in enumerate(p["ordens"][ref_key])}
            n = len(o)
            t = [pos[p["bounding_boxes"][bi]["id"]] / max(1, n - 1) for bi in o]
            alvo[i, :n] = torch.tensor(t)
            mask[i, :n] = 1
        lote["alvo"], lote["mask"] = alvo, mask
    return {k: v.to(device) for k, v in lote.items()}, N


class LayoutLMOrdem(nn.Module):
    def __init__(self, base, usar_layout=True):
        super().__init__()
        from transformers import LayoutLMModel
        self.enc = LayoutLMModel.from_pretrained(base)
        d = self.enc.config.hidden_size
        self.cabeca = nn.Sequential(nn.Linear(d, 256), nn.GELU(), nn.Dropout(0.1), nn.Linear(256, 1))
        self.usar_layout = usar_layout

    def forward(self, input_ids, bbox, attention_mask, bloco_de, n_blocos):
        if not self.usar_layout:
            bbox = torch.zeros_like(bbox)
        h = self.enc(input_ids=input_ids, bbox=bbox, attention_mask=attention_mask).last_hidden_state.float()
        B, T, D = h.shape
        valido = (bloco_de >= 0).unsqueeze(-1).float()
        idx = bloco_de.clamp(min=0)
        soma = torch.zeros(B, n_blocos, D, device=h.device).scatter_add_(
            1, idx.unsqueeze(-1).expand(B, T, D), h * valido)
        cont = torch.zeros(B, n_blocos, 1, device=h.device).scatter_add_(1, idx.unsqueeze(-1), valido)
        return self.cabeca(soma / cont.clamp(min=1.0)).squeeze(-1)


@torch.no_grad()
def prever(modelo, cod, paginas, device, batch=8, medir_tempo=False):
    """Retorna [(ordem_predita, tempo_ms)] usando a ordem de entrada do protocolo."""
    modelo.eval()
    saidas = []
    passo = 1 if medir_tempo else batch
    for b in range(0, len(paginas), passo):
        lote_p = paginas[b:b + passo]
        if medir_tempo:
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            cod.pretokenizar(lote_p)          # tokenizacao faz parte do custo por pagina
        ordens = [ordem_entrada(p) for p in lote_p]
        lote, N = montar_lote(cod, lote_p, ordens, None, device)
        with torch.autocast("cuda", dtype=torch.float16):
            esc = modelo(lote["input_ids"], lote["bbox"], lote["attention_mask"], lote["bloco_de"], N)
        esc = esc.float().cpu()
        for i, (p, o) in enumerate(zip(lote_p, ordens)):
            s = esc[i, :len(o)].tolist()
            pred = [p["bounding_boxes"][o[j]]["id"] for j in sorted(range(len(o)), key=lambda j: s[j])]
            saidas.append([pred, None])
        if medir_tempo:
            torch.cuda.synchronize()
            saidas[-1][1] = (time.perf_counter() - t0) * 1000
    return saidas


def metricas_medias(paginas, preds, ref_key):
    taus = [kendall_tau(pr, p["ordens"][ref_key]) for p, (pr, _) in zip(paginas, preds)]
    ards = [ard_normalizado(pr, p["ordens"][ref_key]) for p, (pr, _) in zip(paginas, preds)]
    return {"tau": sum(taus) / len(taus), "ard_norm": sum(ards) / len(ards)}


def nome_modelo(args):
    return args.nome or ("layoutlm_sem_layout" if args.sem_layout else "layoutlm")


def treinar(args):
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "cuda"
    splits = carregar_splits()
    ref = splits["referencia"]
    if args.n_treino or args.blocos_extra:
        treino = montar_treino(args.n_treino, args.blocos_extra, args.seed)
    else:
        treino = carregar_particao("treino")
    valid = carregar_particao("validacao")
    print(f"[*] treino: {len(treino)} paginas ({len(splits['treino'])} UFs) | "
          f"validacao: {len(valid)} paginas | referencia: {ref}", flush=True)

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODELO_BASE)
    cod = Codificador(tok)
    cod.pretokenizar(treino + valid)

    modelo = LayoutLMOrdem(MODELO_BASE, usar_layout=not args.sem_layout).to(device)
    opt = torch.optim.AdamW([{"params": modelo.enc.parameters(), "lr": args.lr},
                             {"params": modelo.cabeca.parameters(), "lr": args.lr_cabeca}],
                            weight_decay=0.01)
    micro = args.micro_batch
    acum = max(1, args.batch // micro)
    passos_epoca = math.ceil(len(treino) / (micro * acum))
    total = passos_epoca * args.epocas
    aquec = max(1, int(0.06 * total))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / aquec if s < aquec else max(0.02, (total - s) / max(1, total - aquec)))
    scaler = torch.amp.GradScaler("cuda")

    nome = nome_modelo(args)
    dir_saida = args.dir_saida or DIR_RESULTADOS
    os.makedirs(DIR_MODELOS, exist_ok=True)
    os.makedirs(dir_saida, exist_ok=True)
    arq_log = open(os.path.join(dir_saida, f"treino_{nome}.csv"), "w", newline="", encoding="utf-8")
    log = csv.writer(arq_log)
    log.writerow(["epoca", "passo", "segundos", "loss", "val_tau", "val_ard_norm"])

    melhor, t0, passo, estourou = -2.0, time.time(), 0, False
    for ep in range(1, args.epocas + 1):
        modelo.train()
        rng = random.Random(args.seed * 100 + ep)
        ordem_pags = list(range(len(treino)))
        rng.shuffle(ordem_pags)
        soma_loss, n_loss = 0.0, 0
        opt.zero_grad(set_to_none=True)
        for k, b in enumerate(range(0, len(ordem_pags), micro)):
            lote_p = [treino[i] for i in ordem_pags[b:b + micro]]
            ordens = []
            for p in lote_p:        # permutacao NOVA a cada epoca: aumento de dados
                o = list(range(len(p["bounding_boxes"])))
                rng.shuffle(o)
                ordens.append(o)
            lote, N = montar_lote(cod, lote_p, ordens, ref, device)
            with torch.autocast("cuda", dtype=torch.float16):
                esc = modelo(lote["input_ids"], lote["bbox"], lote["attention_mask"], lote["bloco_de"], N)
            loss = (((esc.float() - lote["alvo"]) ** 2) * lote["mask"]).sum() / lote["mask"].sum()
            scaler.scale(loss / acum).backward()
            soma_loss += loss.item()
            n_loss += 1
            if (k + 1) % acum == 0:
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
                scaler.step(opt)
                scaler.update()
                sched.step()
                opt.zero_grad(set_to_none=True)
                passo += 1
                if passo % 10 == 0:
                    log.writerow([ep, passo, round(time.time() - t0, 1), round(soma_loss / n_loss, 5), "", ""])
                    arq_log.flush()
                    print(f"  ep {ep} passo {passo}/{total} loss {soma_loss / n_loss:.4f} "
                          f"({time.time() - t0:.0f}s)", flush=True)
                    soma_loss, n_loss = 0.0, 0
            if time.time() - t0 > args.max_minutos * 60:
                estourou = True
                break

        m = metricas_medias(valid, prever(modelo, cod, valid, device), ref)
        log.writerow([ep, passo, round(time.time() - t0, 1), "", round(m["tau"], 4), round(m["ard_norm"], 4)])
        arq_log.flush()
        print(f"[val] epoca {ep}: tau {m['tau']:.4f} | ARD norm {m['ard_norm']:.4f}", flush=True)
        if m["tau"] > melhor:
            melhor = m["tau"]
            torch.save(modelo.state_dict(), os.path.join(DIR_MODELOS, f"{nome}.pt"))
            print(f"      novo melhor modelo salvo (tau {melhor:.4f})", flush=True)
        if estourou:
            print(f"[!] limite de {args.max_minutos} min atingido", flush=True)
            break

    arq_log.close()
    with open(os.path.join(DIR_MODELOS, f"{nome}_config.json"), "w", encoding="utf-8") as f:
        json.dump({**vars(args), "melhor_val_tau": melhor, "paginas_treino": len(treino),
                   "paginas_validacao": len(valid), "segundos": round(time.time() - t0, 1),
                   "epocas_concluidas": ep, "passos": passo}, f, indent=2)
    print(f"[OK] treino concluido em {time.time() - t0:.0f}s | melhor val tau {melhor:.4f}")


def avaliar(args):
    device = "cuda"
    splits = carregar_splits()
    ref = splits["referencia"]
    teste = carregar_particao("teste")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODELO_BASE)
    cod = Codificador(tok)
    nome = nome_modelo(args)
    modelo = LayoutLMOrdem(MODELO_BASE, usar_layout=not args.sem_layout).to(device)
    modelo.load_state_dict(torch.load(os.path.join(DIR_MODELOS, f"{nome}.pt"), map_location=device))
    prever(modelo, cod, teste[:4], device, medir_tempo=True)      # aquecimento da GPU
    for p in teste:
        for c in p["bounding_boxes"]:
            c.pop("_tok", None)
    preds = prever(modelo, cod, teste, device, medir_tempo=True)
    linhas = [{"page_id": p["page_id"], "ordem_pred": pr, "tempo_ms": round(t, 3)}
              for p, (pr, t) in zip(teste, preds)]
    caminho = salvar_predicoes(nome, linhas, args.dir_saida)
    m = metricas_medias(teste, preds, ref)
    print(f"[OK] {nome}: {len(teste)} paginas de teste | tau {m['tau']:.4f} | "
          f"ARD norm {m['ard_norm']:.4f} | {sum(l['tempo_ms'] for l in linhas) / len(linhas):.1f} ms/pagina")
    print(f"     predicoes em {caminho}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["treinar", "avaliar"])
    ap.add_argument("--sem-layout", action="store_true", help="ablacao: zera as bounding boxes")
    ap.add_argument("--epocas", type=int, default=8)
    ap.add_argument("--max-minutos", type=float, default=16)
    ap.add_argument("--batch", type=int, default=8, help="batch efetivo (com acumulacao)")
    ap.add_argument("--micro-batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=4e-5)
    ap.add_argument("--lr-cabeca", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--nome", help="nome do modelo e das predicoes (padrao: layoutlm ou layoutlm_sem_layout)")
    ap.add_argument("--n-treino", type=int, help="usa so as N primeiras paginas do treino ampliado")
    ap.add_argument("--blocos-extra", help="pasta com paginas extras dos veiculos de treino")
    ap.add_argument("--dir-saida", help="pasta do log de treino e das predicoes (padrao: resultados/)")
    a = ap.parse_args()
    treinar(a) if a.modo == "treinar" else avaliar(a)
