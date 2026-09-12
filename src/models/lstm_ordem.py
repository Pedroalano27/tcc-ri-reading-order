"""
Baseline BiLSTM para ordem de leitura -- mesmo protocolo e mesma perda do LayoutLM.

Cada bloco vira um vetor de caracteristicas; uma BiLSTM de 2 camadas percorre
os blocos (na ordem EMBARALHADA de entrada) e cada saida vira um escore.
Ordenar pelo escore = ordem predita.

Variantes (isolam a contribuicao de cada fonte de informacao):
  texto       so o texto do bloco (bag-of-words com hashing) -- SEM geometria
  geo         so a geometria (8 caracteristicas da bbox) -- SEM texto
  geo_texto   ambos

Roda em CPU para deixar a GPU livre para o LayoutLM.

Uso:
    python src/models/lstm_ordem.py --variante geo_texto

Curva de aprendizado (treino ampliado com paginas extras dos mesmos veiculos):
    python src/models/lstm_ordem.py --variante geo --nome curva_lstm_geo_n1000 --n-treino 1000 \
        --blocos-extra data/processed/blocos_extra --dir-saida resultados/curva_aprendizado
"""
from __future__ import annotations

import os
import sys
import time
import zlib
import random
import argparse

import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import (carregar_splits, carregar_particao, montar_treino,  # noqa: E402
                                ordem_entrada, salvar_predicoes)
from src.eval.metrics import kendall_tau  # noqa: E402

N_BUCKETS = 1 << 18


def preparar(paginas):
    for p in paginas:
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        for c in p["bounding_boxes"]:
            ws = c["text"].lower().split()[:24]
            c["_h"] = [zlib.crc32(w.encode("utf-8")) % N_BUCKETS for w in ws] or [0]
            x0, y0, x1, y1 = c["bbox"]
            c["_g"] = [x0 / W, y0 / H, x1 / W, y1 / H, (x1 - x0) / W, (y1 - y0) / H,
                       (x0 + x1) / 2 / W, (y0 + y1) / 2 / H]


def montar(paginas, ordens, ref):
    B, N = len(paginas), max(len(o) for o in ordens)
    geo = torch.zeros(B, N, 8)
    ids, offs, lens = [], [], []
    alvo, mask = torch.zeros(B, N), torch.zeros(B, N)
    for i, (p, o) in enumerate(zip(paginas, ordens)):
        pos = {b: k for k, b in enumerate(p["ordens"][ref])} if ref else None
        for j in range(N):
            offs.append(len(ids))
            if j < len(o):
                c = p["bounding_boxes"][o[j]]
                geo[i, j] = torch.tensor(c["_g"])
                ids.extend(c["_h"])
                if pos is not None:
                    alvo[i, j] = pos[c["id"]] / max(1, len(o) - 1)
                    mask[i, j] = 1
            else:
                ids.append(0)
        lens.append(len(o))
    return geo, torch.tensor(ids), torch.tensor(offs), torch.tensor(lens), alvo, mask


class LSTMOrdem(nn.Module):
    def __init__(self, variante, dim_txt=64, hid=128):
        super().__init__()
        self.variante = variante
        d = 0
        if "texto" in variante:
            self.emb = nn.EmbeddingBag(N_BUCKETS, dim_txt, mode="mean")
            d += dim_txt
        if "geo" in variante:
            self.proj = nn.Sequential(nn.Linear(8, 64), nn.ReLU())
            d += 64
        self.lstm = nn.LSTM(d, hid, num_layers=2, batch_first=True, bidirectional=True, dropout=0.1)
        self.cabeca = nn.Sequential(nn.Linear(2 * hid, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, geo, ids, offs, lens):
        B, N, _ = geo.shape
        partes = []
        if "texto" in self.variante:
            partes.append(self.emb(ids, offs).view(B, N, -1))
        if "geo" in self.variante:
            partes.append(self.proj(geo))
        x = torch.cat(partes, -1)
        emp = nn.utils.rnn.pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(emp)
        out, _ = nn.utils.rnn.pad_packed_sequence(out, batch_first=True, total_length=N)
        return self.cabeca(out).squeeze(-1)


@torch.no_grad()
def prever(modelo, paginas, medir_tempo=False):
    modelo.eval()
    saidas = []
    for p in paginas:
        t0 = time.perf_counter()
        o = ordem_entrada(p)
        geo, ids, offs, lens, _, _ = montar([p], [o], None)
        s = modelo(geo, ids, offs, lens)[0, :len(o)].tolist()
        pred = [p["bounding_boxes"][o[j]]["id"] for j in sorted(range(len(o)), key=lambda j: s[j])]
        saidas.append((pred, (time.perf_counter() - t0) * 1000))
    return saidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variante", choices=["texto", "geo", "geo_texto"], default="geo_texto")
    ap.add_argument("--epocas", type=int, default=40)
    ap.add_argument("--max-minutos", type=float, default=5)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--n-treino", type=int, help="usa so as N primeiras paginas do treino ampliado")
    ap.add_argument("--blocos-extra", help="pasta com paginas extras dos veiculos de treino")
    ap.add_argument("--nome", help="nome das predicoes (padrao: lstm_<variante>)")
    ap.add_argument("--dir-saida", help="pasta das predicoes (padrao: resultados/)")
    a = ap.parse_args()

    torch.manual_seed(42)
    torch.set_num_threads(a.threads)
    splits = carregar_splits()
    ref = splits["referencia"]
    if a.n_treino or a.blocos_extra:
        treino = montar_treino(a.n_treino, a.blocos_extra)
    else:
        treino = carregar_particao("treino")
    valid, teste = carregar_particao("validacao"), carregar_particao("teste")
    preparar(treino + valid + teste)
    print(f"[*] treino: {len(treino)} paginas | validacao: {len(valid)} | teste: {len(teste)}", flush=True)

    modelo = LSTMOrdem(a.variante)
    opt = torch.optim.Adam(modelo.parameters(), lr=2e-3)
    rng = random.Random(42)
    melhor, melhor_estado, t0 = -2.0, None, time.time()
    for ep in range(1, a.epocas + 1):
        modelo.train()
        idx = list(range(len(treino)))
        rng.shuffle(idx)
        for b in range(0, len(idx), a.batch):
            lote = [treino[i] for i in idx[b:b + a.batch]]
            ordens = []
            for p in lote:
                o = list(range(len(p["bounding_boxes"])))
                rng.shuffle(o)
                ordens.append(o)
            geo, ids, offs, lens, alvo, mask = montar(lote, ordens, ref)
            esc = modelo(geo, ids, offs, lens)
            loss = (((esc - alvo) ** 2) * mask).sum() / mask.sum()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()
        preds = prever(modelo, valid)
        tau = sum(kendall_tau(pr, p["ordens"][ref]) for p, (pr, _) in zip(valid, preds)) / len(valid)
        if tau > melhor:
            melhor = tau
            melhor_estado = {k: v.clone() for k, v in modelo.state_dict().items()}
        print(f"  [{a.variante}] epoca {ep}: loss {loss.item():.4f} | val tau {tau:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)
        if time.time() - t0 > a.max_minutos * 60:
            break

    modelo.load_state_dict(melhor_estado)
    preds = prever(modelo, teste, medir_tempo=True)
    linhas = [{"page_id": p["page_id"], "ordem_pred": pr, "tempo_ms": round(t, 3)}
              for p, (pr, t) in zip(teste, preds)]
    nome = a.nome or f"lstm_{a.variante}"
    salvar_predicoes(nome, linhas, a.dir_saida)
    tau = sum(kendall_tau(pr, p["ordens"][ref]) for p, (pr, _) in zip(teste, preds)) / len(teste)
    print(f"[OK] {nome}: val tau {melhor:.4f} | teste tau {tau:.4f} | "
          f"{sum(l['tempo_ms'] for l in linhas) / len(linhas):.2f} ms/pagina")


if __name__ == "__main__":
    main()
