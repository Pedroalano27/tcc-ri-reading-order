"""
LayoutLM para ordem de leitura formulado como PREDICAO DE SUCESSOR.

Por que trocar a formulacao
---------------------------
O modelo de src/models/layoutlm_ordem.py e PONTUAL: cada bloco recebe um escore
isolado e a ordem sai de um sort. Nada na perda olha para o par (bloco, proximo
bloco). O resultado medido no teste foi tau 0,671 com apenas 13% de sucessor
correto: a ordem global fica razoavel e o texto sai picotado, que e justamente
o que estraga a busca por trechos e o RAG.

Aqui a tarefa vira: dado o conjunto de blocos, prever para cada bloco QUAL bloco
vem imediatamente depois dele. A pagina deixa de ser um problema de regressao e
vira um caminho hamiltoniano num grafo completo de n+1 vertices (os n blocos mais
um vertice virtual INICIO/FIM).

Modelo
------
  1. LayoutLM codifica a pagina (mesmo encoder, mesma entrada embaralhada, os
     mesmos K tokens por bloco com a bounding box do bloco).
  2. Media dos estados ocultos de cada bloco -> h_i. O estado do [CLS] vira o
     vertice INICIO; um vetor aprendido vira o vertice FIM.
  3. Escore de aresta S[i][j] = <Wq h_i, Wk h_j> / sqrt(d) + vies_geometrico(i, j).
     O vies geometrico e um MLP sobre 10 features RELATIVAS do par (deslocamento,
     folga vertical, sobreposicao horizontal, mesma coluna, salto de coluna...) --
     a relacao "j vem logo depois de i" e fortemente geometrica: ou j esta logo
     abaixo de i, ou i terminou a coluna e j abre a proxima.
  4. Perda: entropia cruzada por linha (softmax sobre os candidatos a sucessor),
     somada a uma perda auxiliar de posicao (MSE, a formulacao antiga) com peso
     --peso-posicao. A auxiliar segura a ordem GLOBAL enquanto a principal cuida
     da continuidade LOCAL.
  5. Decodificacao: busca em feixe sobre a matriz de log-probabilidades, com a
     restricao de permutacao (cada bloco usado uma vez) e o custo da aresta final
     para o vertice FIM. Feixe 1 = guloso.

Ablacoes
--------
  --sem-vies-geo   remove o MLP de geometria relativa (so o produto interno)
  --peso-posicao 0 treina so com a perda de sucessor
  --feixe 1        decodificacao gulosa

Uso
---
    python src/models/layoutlm_sucessor.py treinar [--epocas 8] [--max-minutos 20]
    python src/models/layoutlm_sucessor.py avaliar [--feixe 4]

    # treino ampliado (curva de aprendizado), igual ao modelo pontual:
    python src/models/layoutlm_sucessor.py treinar --nome suc_n3235 --n-treino 3235 \
        --blocos-extra data/processed/blocos_extra --dir-saida resultados/curva_aprendizado
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

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import (carregar_splits, carregar_particao, montar_treino,  # noqa: E402
                                ordem_entrada, salvar_predicoes, DIR_RESULTADOS, RAIZ_PROJETO)
from src.eval.metrics import kendall_tau, ard_normalizado, acerto_sucessor  # noqa: E402
from src.models.layoutlm_ordem import Codificador, MODELO_BASE, DIR_MODELOS  # noqa: E402

N_FEAT_GEO = 10


def features_geo(pagina, ordem):
    """Features relativas de cada par (i, j) de blocos, na ordem de ENTRADA.

    Devolve (n, n, 10). Todas normalizadas pelas dimensoes da pagina, entao nao
    dependem do tamanho do papel. As duas ultimas sao indicadoras binarias.
    """
    W = float(pagina["dimensions"]["width"]) or 1.0
    H = float(pagina["dimensions"]["height"]) or 1.0
    cx = np.array([pagina["bounding_boxes"][b]["bbox"] for b in ordem], dtype=np.float32)
    x0, y0, x1, y1 = cx[:, 0] / W, cx[:, 1] / H, cx[:, 2] / W, cx[:, 3] / H
    larg = np.maximum(x1 - x0, 1e-6)
    n = len(ordem)
    uns = np.ones((n, n), dtype=np.float32)

    def par(v):                                # v_i constante nas linhas, v_j constante nas colunas
        return v[:, None] * uns, v[None, :] * uns

    x0i, x0j = par(x0)
    y0i, y0j = par(y0)
    x1i, x1j = par(x1)
    y1i, y1j = par(y1)
    lgi, lgj = par(larg)
    sobrep = (np.minimum(x1i, x1j) - np.maximum(x0i, x0j)) / np.minimum(lgi, lgj)
    f = np.stack([
        x0j - x0i,                       # deslocamento horizontal da borda esquerda
        y0j - y0i,                       # deslocamento vertical do topo
        y0j - y1i,                       # folga vertical: j comeca depois que i termina
        (x0j + x1j) / 2 - (x0i + x1i) / 2,   # deslocamento dos centros
        np.clip(sobrep, -2, 2),          # sobreposicao horizontal (fracao da menor largura)
        lgj - lgi,                       # diferenca de largura
        y1j - y1i,                       # deslocamento da base
        np.abs(y0j - y1i),               # magnitude da folga (simetrica)
        (np.abs(x0j - x0i) < 0.02).astype(np.float32),   # alinhados a esquerda: mesma coluna
        ((x0j > x1i - 0.01) & (y0j < y0i)).astype(np.float32),  # j abre uma coluna a direita, mais acima
    ], axis=-1).astype(np.float32)
    return f


def montar_lote(cod, paginas, ordens, ref_key, device, com_geo=True):
    """Tensores do encoder + matriz de features geometricas + alvos de sucessor/posicao."""
    seqs = [cod.codificar(p, o) for p, o in zip(paginas, ordens)]
    B = len(seqs)
    T = max(len(s[0]) for s in seqs)
    N = max(len(o) for o in ordens)
    input_ids = torch.full((B, T), cod.pad, dtype=torch.long)
    bbox = torch.zeros((B, T, 4), dtype=torch.long)
    att = torch.zeros((B, T), dtype=torch.long)
    blk = torch.full((B, T), -1, dtype=torch.long)
    valido = torch.zeros((B, N), dtype=torch.bool)
    geo = torch.zeros((B, N, N, N_FEAT_GEO))
    for i, ((a, b, c), o, p) in enumerate(zip(seqs, ordens, paginas)):
        L, n = len(a), len(o)
        input_ids[i, :L] = torch.tensor(a)
        bbox[i, :L] = torch.tensor(b)
        att[i, :L] = 1
        blk[i, :L] = torch.tensor(c)
        valido[i, :n] = True
        if com_geo:
            geo[i, :n, :n] = torch.from_numpy(features_geo(p, o))
    lote = {"input_ids": input_ids, "bbox": bbox, "attention_mask": att,
            "bloco_de": blk, "valido": valido, "geo": geo}
    if ref_key is not None:
        # alvo[i, r] = coluna correta da linha r. Linha 0 = INICIO, linha k+1 = bloco k.
        # Coluna 0 = FIM, coluna k+1 = bloco k.
        alvo = torch.full((B, N + 1), -100, dtype=torch.long)
        pos_alvo = torch.zeros((B, N))
        for i, (p, o) in enumerate(zip(paginas, ordens)):
            n = len(o)
            linha_de = {p["bounding_boxes"][bi]["id"]: k + 1 for k, bi in enumerate(o)}
            ref = p["ordens"][ref_key]
            posicao = {bid: k for k, bid in enumerate(ref)}
            alvo[i, 0] = linha_de[ref[0]]
            for k, bid in enumerate(ref):
                alvo[i, linha_de[bid]] = linha_de[ref[k + 1]] if k + 1 < len(ref) else 0
            for k, bi in enumerate(o):
                pos_alvo[i, k] = posicao[p["bounding_boxes"][bi]["id"]] / max(1, n - 1)
        lote["alvo"], lote["pos_alvo"] = alvo, pos_alvo
    return {k: v.to(device) for k, v in lote.items()}, N


class LayoutLMSucessor(nn.Module):
    def __init__(self, base=MODELO_BASE, usar_layout=True, usar_vies_geo=True, d_par=128):
        super().__init__()
        from transformers import LayoutLMModel
        self.enc = LayoutLMModel.from_pretrained(base)
        d = self.enc.config.hidden_size
        self.usar_layout = usar_layout
        self.usar_vies_geo = usar_vies_geo
        self.d_par = d_par
        self.proj_q = nn.Linear(d, d_par)
        self.proj_k = nn.Linear(d, d_par)
        self.emb_fim = nn.Parameter(torch.zeros(d))
        nn.init.normal_(self.emb_fim, std=0.02)
        self.cabeca_pos = nn.Sequential(nn.Linear(d, 256), nn.GELU(), nn.Dropout(0.1), nn.Linear(256, 1))
        if usar_vies_geo:
            self.vies_geo = nn.Sequential(nn.Linear(N_FEAT_GEO, 64), nn.GELU(), nn.Linear(64, 1))

    def representar(self, input_ids, bbox, attention_mask, bloco_de, n_blocos):
        if not self.usar_layout:
            bbox = torch.zeros_like(bbox)
        h = self.enc(input_ids=input_ids, bbox=bbox, attention_mask=attention_mask).last_hidden_state.float()
        B, T, D = h.shape
        val = (bloco_de >= 0).unsqueeze(-1).float()
        idx = bloco_de.clamp(min=0)
        soma = torch.zeros(B, n_blocos, D, device=h.device).scatter_add_(
            1, idx.unsqueeze(-1).expand(B, T, D), h * val)
        cont = torch.zeros(B, n_blocos, 1, device=h.device).scatter_add_(1, idx.unsqueeze(-1), val)
        return soma / cont.clamp(min=1.0), h[:, 0]       # blocos (B, N, D) e [CLS] (B, D)

    def forward(self, input_ids, bbox, attention_mask, bloco_de, valido, geo, n_blocos):
        hb, hcls = self.representar(input_ids, bbox, attention_mask, bloco_de, n_blocos)
        B, N, _ = hb.shape
        # linhas: [INICIO, blocos]; colunas: [FIM, blocos]
        origem = torch.cat([hcls.unsqueeze(1), hb], dim=1)                     # (B, N+1, D)
        destino = torch.cat([self.emb_fim.expand(B, 1, -1), hb], dim=1)        # (B, N+1, D)
        s = self.proj_q(origem) @ self.proj_k(destino).transpose(1, 2) / math.sqrt(self.d_par)
        if self.usar_vies_geo:
            s = s + F.pad(self.vies_geo(geo).squeeze(-1), (1, 0, 1, 0))
        # mascaras: coluna/linha de bloco invalido, aresta para si mesmo, INICIO->FIM
        col_ok = torch.cat([torch.ones(B, 1, dtype=torch.bool, device=valido.device), valido], dim=1)
        s = s.masked_fill(~col_ok.unsqueeze(1), float("-inf"))
        # a diagonal cobre tanto "bloco k -> bloco k" quanto "INICIO -> FIM" (pagina vazia)
        diag = torch.eye(N + 1, dtype=torch.bool, device=s.device)
        s = s.masked_fill(diag.unsqueeze(0), float("-inf"))
        return s, self.cabeca_pos(hb).squeeze(-1)


def log_probs(s):
    return torch.log_softmax(s.float(), dim=-1)


def decodificar(lp, n, largura=4):
    """Busca em feixe sobre a matriz de log-probabilidades. Devolve indices 0..n-1."""
    if n == 1:
        return [0]
    feixe = [(0.0, [0], np.zeros(n + 1, dtype=bool))]     # (escore, caminho comecando no INICIO, usados)
    for _ in range(n):
        cands = []
        for sc, cam, usado in feixe:
            linha = lp[cam[-1], 1:n + 1].copy()
            linha[usado[1:n + 1]] = -np.inf
            livres = int((~usado[1:n + 1]).sum())
            k = min(largura, livres)
            top = np.argpartition(-linha, k - 1)[:k] if k < n else np.arange(n)
            for t in top:
                if not np.isfinite(linha[t]):
                    continue
                u = usado.copy()
                u[int(t) + 1] = True
                cands.append((sc + float(linha[t]), cam + [int(t) + 1], u))
        if not cands:
            break
        cands.sort(key=lambda c: -c[0])
        feixe = cands[:largura]
    # a aresta final para o vertice FIM desempata caminhos que terminam em blocos diferentes
    melhor = max(feixe, key=lambda c: c[0] + float(lp[c[1][-1], 0]))
    caminho = [j - 1 for j in melhor[1][1:]]
    caminho += [j for j in range(n) if j not in set(caminho)]    # seguranca: completa a permutacao
    return caminho


def decodificar_cadeias(lp, pos, n, limiar=0.5):
    """Decodificacao hibrida: cadeias locais de sucessores, ordenadas pela cabeca de posicao.

    A predicao de sucessor acerta a continuidade LOCAL (o proximo paragrafo da coluna)
    mas erra o salto GLOBAL (qual coluna vem depois de qual), e um salto errado no meio
    do caminho arruina o tau. Aqui:

      1. as arestas i->j entram em ordem decrescente de probabilidade, enquanto
         probabilidade >= limiar, respeitando "um sucessor e um antecessor por bloco"
         e sem fechar ciclo -- o resultado e um conjunto de CADEIAS de blocos que o
         modelo tem certeza de que se seguem;
      2. as cadeias sao ordenadas pela media da posicao predita pela cabeca pontual;
      3. o que sobrar de arestas e emendado na ordem dessa media.

    Com limiar 0 nenhuma cadeia sobra e a decodificacao vira o casamento guloso puro.
    """
    if n == 1:
        return [0]
    p = np.exp(lp[1:n + 1, 1:n + 1])
    np.fill_diagonal(p, 0.0)
    pai = list(range(n))

    def raiz(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    prox, ant = [-1] * n, [-1] * n
    ordem_arestas = np.dstack(np.unravel_index(np.argsort(-p, axis=None), p.shape))[0]
    for i, j in ordem_arestas:
        i, j = int(i), int(j)
        if p[i, j] < limiar:
            break
        if prox[i] < 0 and ant[j] < 0 and raiz(i) != raiz(j):
            prox[i], ant[j] = j, i
            pai[raiz(i)] = raiz(j)

    cadeias = []
    for i in range(n):
        if ant[i] < 0:
            c, k = [i], i
            while prox[k] >= 0:
                k = prox[k]
                c.append(k)
            cadeias.append(c)
    cadeias.sort(key=lambda c: float(np.mean([pos[k] for k in c])))
    return [k for c in cadeias for k in c]


@torch.no_grad()
def prever(modelo, cod, paginas, device, batch=4, medir_tempo=False, largura=4, com_geo=True,
           modo="feixe", limiar=0.5):
    modelo.eval()
    saidas = []
    passo = 1 if medir_tempo else batch
    for b in range(0, len(paginas), passo):
        lote_p = paginas[b:b + passo]
        if medir_tempo:
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            cod.pretokenizar(lote_p)
        ordens = [ordem_entrada(p) for p in lote_p]
        lote, N = montar_lote(cod, lote_p, ordens, None, device, com_geo)
        with torch.autocast("cuda", dtype=torch.float16):
            s, posicao = modelo(lote["input_ids"], lote["bbox"], lote["attention_mask"],
                                lote["bloco_de"], lote["valido"], lote["geo"], N)
        lp = log_probs(s).cpu().numpy()
        posicao = posicao.float().cpu().numpy()
        for i, (p, o) in enumerate(zip(lote_p, ordens)):
            n = len(o)
            m = lp[i][:n + 1, :n + 1]
            cam = (decodificar_cadeias(m, posicao[i][:n], n, limiar) if modo == "cadeias"
                   else decodificar(m, n, largura))
            saidas.append([[p["bounding_boxes"][o[j]]["id"] for j in cam], None])
        if medir_tempo:
            torch.cuda.synchronize()
            saidas[-1][1] = (time.perf_counter() - t0) * 1000
    return saidas


def metricas_medias(paginas, preds, ref_key):
    pares = [(pr, p["ordens"][ref_key]) for p, (pr, _) in zip(paginas, preds)]
    return {"tau": sum(kendall_tau(a, b) for a, b in pares) / len(pares),
            "sucessor": sum(acerto_sucessor(a, b) for a, b in pares) / len(pares),
            "ard_norm": sum(ard_normalizado(a, b) for a, b in pares) / len(pares)}


def perda(s, pos, lote, valido):
    ce = F.cross_entropy(s.float().flatten(0, 1), lote["alvo"].flatten(), ignore_index=-100)
    m = valido.float()
    mse = (((pos.float() - lote["pos_alvo"]) ** 2) * m).sum() / m.sum().clamp(min=1)
    return ce, mse


def nome_modelo(args):
    if args.nome:
        return args.nome
    return "layoutlm_sucessor" + ("_sem_vies_geo" if args.sem_vies_geo else "")


def treinar(args):
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "cuda"
    splits = carregar_splits()
    ref = splits["referencia"]
    treino = (montar_treino(args.n_treino, args.blocos_extra, args.seed)
              if (args.n_treino or args.blocos_extra) else carregar_particao("treino"))
    valid = carregar_particao("validacao")
    com_geo = not args.sem_vies_geo
    print(f"[*] treino: {len(treino)} paginas | validacao: {len(valid)} | referencia: {ref} | "
          f"vies geo: {com_geo} | peso posicao: {args.peso_posicao}", flush=True)

    from transformers import AutoTokenizer
    cod = Codificador(AutoTokenizer.from_pretrained(MODELO_BASE))
    cod.pretokenizar(treino + valid)

    modelo = LayoutLMSucessor(usar_layout=not args.sem_layout, usar_vies_geo=com_geo).to(device)
    cabeca = [p for n, p in modelo.named_parameters() if not n.startswith("enc.")]
    opt = torch.optim.AdamW([{"params": modelo.enc.parameters(), "lr": args.lr},
                             {"params": cabeca, "lr": args.lr_cabeca}], weight_decay=0.01)
    micro = args.micro_batch
    acum = max(1, args.batch // micro)
    total = math.ceil(len(treino) / (micro * acum)) * args.epocas
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
    log.writerow(["epoca", "passo", "segundos", "ce", "mse", "val_tau", "val_sucessor", "val_ard_norm"])

    melhor, t0, passo, estourou, ep = -2.0, time.time(), 0, False, 0
    for ep in range(1, args.epocas + 1):
        modelo.train()
        rng = random.Random(args.seed * 100 + ep)
        idx = list(range(len(treino)))
        rng.shuffle(idx)
        soma_ce = soma_mse = 0.0
        n_loss = 0
        opt.zero_grad(set_to_none=True)
        for k, b in enumerate(range(0, len(idx), micro)):
            lote_p = [treino[i] for i in idx[b:b + micro]]
            ordens = []
            for p in lote_p:              # permutacao nova a cada epoca: aumento de dados
                o = list(range(len(p["bounding_boxes"])))
                rng.shuffle(o)
                ordens.append(o)
            lote, N = montar_lote(cod, lote_p, ordens, ref, device, com_geo)
            with torch.autocast("cuda", dtype=torch.float16):
                s, pos = modelo(lote["input_ids"], lote["bbox"], lote["attention_mask"],
                                lote["bloco_de"], lote["valido"], lote["geo"], N)
            ce, mse = perda(s, pos, lote, lote["valido"])
            scaler.scale((ce + args.peso_posicao * mse) / acum).backward()
            soma_ce += ce.item()
            soma_mse += mse.item()
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
                    log.writerow([ep, passo, round(time.time() - t0, 1),
                                  round(soma_ce / n_loss, 5), round(soma_mse / n_loss, 5), "", "", ""])
                    arq_log.flush()
                    print(f"  ep {ep} passo {passo}/{total} ce {soma_ce / n_loss:.4f} "
                          f"mse {soma_mse / n_loss:.4f} ({time.time() - t0:.0f}s)", flush=True)
                    soma_ce = soma_mse = 0.0
                    n_loss = 0
            if time.time() - t0 > args.max_minutos * 60:
                estourou = True
                break

        m = metricas_medias(valid, prever(modelo, cod, valid, device, largura=args.feixe, com_geo=com_geo,
                                          modo=args.decodificacao, limiar=args.limiar_cadeia), ref)
        log.writerow([ep, passo, round(time.time() - t0, 1), "", "",
                      round(m["tau"], 4), round(m["sucessor"], 4), round(m["ard_norm"], 4)])
        arq_log.flush()
        print(f"[val] epoca {ep}: tau {m['tau']:.4f} | sucessor {m['sucessor']:.4f} | "
              f"ARD norm {m['ard_norm']:.4f}", flush=True)
        criterio = m["sucessor"] if args.selecionar_por == "sucessor" else m["tau"]
        if criterio > melhor:
            melhor = criterio
            torch.save(modelo.state_dict(), os.path.join(DIR_MODELOS, f"{nome}.pt"))
            print(f"      novo melhor modelo salvo ({args.selecionar_por} {melhor:.4f})", flush=True)
        if estourou:
            print(f"[!] limite de {args.max_minutos} min atingido", flush=True)
            break

    arq_log.close()
    with open(os.path.join(DIR_MODELOS, f"{nome}_config.json"), "w", encoding="utf-8") as f:
        json.dump({**vars(args), "melhor_val": melhor, "paginas_treino": len(treino),
                   "paginas_validacao": len(valid), "segundos": round(time.time() - t0, 1),
                   "epocas_concluidas": ep, "passos": passo}, f, indent=2)
    print(f"[OK] treino em {time.time() - t0:.0f}s | melhor val {args.selecionar_por} {melhor:.4f}")


def avaliar(args):
    device = "cuda"
    splits = carregar_splits()
    ref = splits["referencia"]
    teste = carregar_particao("teste")
    from transformers import AutoTokenizer
    cod = Codificador(AutoTokenizer.from_pretrained(MODELO_BASE))
    nome = nome_modelo(args)
    com_geo = not args.sem_vies_geo
    modelo = LayoutLMSucessor(usar_layout=not args.sem_layout, usar_vies_geo=com_geo).to(device)
    modelo.load_state_dict(torch.load(os.path.join(DIR_MODELOS, f"{nome}.pt"), map_location=device))
    decod = dict(largura=args.feixe, com_geo=com_geo, modo=args.decodificacao, limiar=args.limiar_cadeia)
    prever(modelo, cod, teste[:4], device, medir_tempo=True, **decod)
    for p in teste:
        for c in p["bounding_boxes"]:
            c.pop("_tok", None)
    preds = prever(modelo, cod, teste, device, medir_tempo=True, **decod)
    linhas = [{"page_id": p["page_id"], "ordem_pred": pr, "tempo_ms": round(t, 3)}
              for p, (pr, t) in zip(teste, preds)]
    caminho = salvar_predicoes(args.metodo or nome, linhas, args.dir_saida)
    m = metricas_medias(teste, preds, ref)
    print(f"[OK] {nome} [{args.decodificacao}]: {len(teste)} paginas | tau {m['tau']:.4f} | sucessor {m['sucessor']:.4f} | "
          f"ARD norm {m['ard_norm']:.4f} | {sum(l['tempo_ms'] for l in linhas) / len(linhas):.1f} ms/pagina")
    print(f"     predicoes em {caminho}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["treinar", "avaliar"])
    ap.add_argument("--sem-layout", action="store_true", help="ablacao: zera as bounding boxes")
    ap.add_argument("--sem-vies-geo", action="store_true", help="ablacao: remove o MLP de geometria relativa")
    ap.add_argument("--peso-posicao", type=float, default=0.5, help="peso da perda auxiliar de posicao")
    ap.add_argument("--feixe", type=int, default=4, help="largura da busca em feixe (1 = guloso)")
    ap.add_argument("--decodificacao", choices=["feixe", "cadeias"], default="cadeias",
                    help="feixe = caminho unico; cadeias = trechos locais ordenados pela cabeca de posicao")
    ap.add_argument("--limiar-cadeia", type=float, default=0.5,
                    help="probabilidade minima para emendar dois blocos numa cadeia")
    ap.add_argument("--selecionar-por", choices=["tau", "sucessor"], default="tau",
                    help="metrica de validacao que escolhe o melhor checkpoint")
    ap.add_argument("--epocas", type=int, default=8)
    ap.add_argument("--max-minutos", type=float, default=20)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--micro-batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=4e-5)
    ap.add_argument("--lr-cabeca", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--nome", help="nome do checkpoint (padrao: layoutlm_sucessor)")
    ap.add_argument("--metodo", help="nome do arquivo de predicoes (padrao: o mesmo do checkpoint)")
    ap.add_argument("--n-treino", type=int)
    ap.add_argument("--blocos-extra")
    ap.add_argument("--dir-saida")
    a = ap.parse_args()
    treinar(a) if a.modo == "treinar" else avaliar(a)
