"""Treina ordenadores nas unidades congeladas, em fluxo e sem alterar src/data.

Importa as redes, lotes, perdas e decodificadores do TCC. O embrulho acrescenta
CPU, checkpoint retomavel e leitura por offsets: os treinadores antigos carregam
todo o corpus, nao salvam BiLSTM e fixam CUDA no LayoutLM. Um token UNK por
unidade permite ordenar linhas sem truncar palavras/unidades. Acima de 510,
forma faixas geometricas; a rede ordena as faixas e a ordem interna e fixa.

Uso: venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas.py
 --modelo lstm --variante geo --representacao linhas --device cpu --max-minutos 8
 --nome lstm_geo --dir-saida resultados/ordenadores_treinados_sem_caixas/lstm_geo
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import argparse
import contextlib
import hashlib
import json
import math
import os
import random
import statistics
import time

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  HF_DEACTIVATE_ASYNC_LOAD="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4")
import torch
from src.eval import protocolo
from src.eval.metrics import kendall_tau
from src.models import lstm_ordem as lstm
from src.models import layoutlm_ordem as pontual
from src.models import layoutlm_sucessor as sucessor

UNIDADES = RAIZ / "resultados/unidades_sem_caixas"
OUT = RAIZ / "resultados/ordenadores_treinados_sem_caixas"
REPS = ("linhas", "colunas", "colunas_margens")


def ler(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def gravar(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def salvar_torch(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def memoria():
    if os.name != "nt":
        return {}
    import ctypes
    class Status(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (k, ctypes.c_ulonglong) for k in ("total", "free", "commit", "commit_free", "virtual", "virtual_free", "extended")]
    s = Status()
    s.length = ctypes.sizeof(s)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return {"ram_livre_mb": s.free / 2**20, "commit_livre_mb": s.commit_free / 2**20}


def indice(rep, particao, base=None, extra=None):
    """Guarda apenas caminho/offset/id; abre e fecha o shard para cada pagina."""
    splits = protocolo.carregar_splits()
    proibidas = set()
    for b in ("golden_v4", "golden_v3_novo"):
        with (UNIDADES / "bancadas" / (b + ".jsonl")).open(encoding="utf-8") as f:
            proibidas.update(json.loads(l)["page_id"] for l in f if l.strip())
    dirs = [Path(base or UNIDADES / rep)]
    if particao == "treino":
        dirs += [Path(extra or UNIDADES / (rep + "_extra"))]
    refs, vistos = [], set()
    for d in dirs:
        for uf in splits[particao]:
            path = d / (uf + ".jsonl")
            with path.open("rb") as f:
                while True:
                    off = f.tell()
                    line = f.readline()
                    if not line:
                        break
                    p = json.loads(line.decode("utf-8"))
                    pid = p["page_id"]
                    part_esperada = "treino_extra" if particao == "treino" and d == dirs[-1] else particao
                    if p["uf"] != uf or p["particao"] != part_esperada:
                        raise ValueError(f"Split/veiculo incorreto: {pid}")
                    if particao == "treino" and pid in proibidas:
                        raise ValueError(f"Bancada humana no treino: {pid}")
                    if pid not in vistos:
                        vistos.add(pid)
                        refs.append((str(path), off, pid))
    return sorted(refs, key=lambda r: r[2])


def pagina(ref):
    with open(ref[0], "rb") as f:
        f.seek(ref[1])
        p = json.loads(f.readline().decode("utf-8"))
    if p["page_id"] != ref[2]:
        raise ValueError("Offset nao corresponde ao page_id")
    # Palavras individuais ficam no shard da bancada, nunca na rede.
    p.pop("palavras", None)
    for b in p["bounding_boxes"]:
        b.pop("ks", None)
    return p


def compactar(p):
    """Agrupa apenas pagina excedente; nenhuma consulta ao ouro para formar faixas."""
    bs = p["bounding_boxes"]
    if len(bs) <= 510:
        return p, {b["id"]: [b["id"]] for b in bs}
    from orquestracao.analises import ordem_layoutreader as adaptador
    # Esse adaptador mascara CUDA ao importar; restaurar a configuracao do processo.
    # O import e preparado em criar_modelo(), antes de qualquer uso de CUDA.
    h = statistics.median(max(.1, b["bbox"][3] - b["bbox"][1]) for b in bs)
    gs = adaptador.grupos_projecao(bs, list(range(len(bs))), h, .08)
    if len(gs) > 510:
        xs = sorted(range(len(bs)), key=lambda i: (bs[i]["bbox"][0], bs[i]["bbox"][1], bs[i]["id"]))
        gs = [xs[k:k+2] for k in range(0, len(xs), 2)]
    if len(gs) > 510:
        raise ValueError("Hierarquia excede 510 faixas")
    grupos, novos = {}, []
    for j, g in enumerate(gs):
        bid = f"faixa{j}"
        grupos[bid] = [bs[i]["id"] for i in g]
        bb = [min(bs[i]["bbox"][0] for i in g), min(bs[i]["bbox"][1] for i in g),
              max(bs[i]["bbox"][2] for i in g), max(bs[i]["bbox"][3] for i in g)]
        novos.append({"id": bid, "bbox": bb, "text": " ".join(bs[i]["text"] for i in g), "tipo": "texto"})
    ordens = {}
    for key, ordem in p.get("ordens", {}).items():
        postos = {bid: j for j, bid in enumerate(ordem)}
        ordens[key] = sorted(grupos, key=lambda g: (statistics.median(postos[i] for i in grupos[g]), g))
    return {**p, "bounding_boxes": novos, "ordens": ordens}, grupos


class UmToken:
    pad, unk, cls, sep = 0, 100, 101, 102
    def pretokenizar(self, paginas):
        pass
    def codificar(self, p, ordem):
        if len(ordem) > 510:
            raise ValueError("Pagina excede o limite depois da compactacao")
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        bb = [pontual.normalizar_bbox(p["bounding_boxes"][i]["bbox"], W, H) for i in ordem]
        return [self.cls] + [self.unk]*len(ordem) + [self.sep], [[0]*4] + bb + [[1000]*4], [-1] + list(range(len(ordem))) + [-1]


def criar_modelo(a):
    torch.set_num_threads(4)
    # Importar agrupador/decoder antes de restaurar a visibilidade definida pela fila.
    visibilidade = os.environ.get("CUDA_VISIBLE_DEVICES")
    from orquestracao.analises import ordem_layoutreader
    if visibilidade is None:
        os.environ.pop("CUDA_VISIBLE_DEVICES", None)
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = visibilidade
    if a.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    torch.manual_seed(a.seed)
    if a.modelo == "lstm":
        return lstm.LSTMOrdem(a.variante).to(a.device), None
    m = memoria()
    if m.get("commit_livre_mb", 10000) < 4500:
        raise RuntimeError(f"Memoria insuficiente para rede e otimizador: {m}")
    if a.modelo == "layoutreader":
        from transformers import LayoutLMv3ForTokenClassification
        model = LayoutLMv3ForTokenClassification.from_pretrained(str(RAIZ / "models/terceiros/layoutreader"),
            local_files_only=True, disable_mmap=True, dtype=torch.float32)
        # Ultimas quatro camadas + cabeca: ajuste de encoder compativel com 6 GB.
        for p in model.parameters():
            p.requires_grad_(False)
        for layer in model.layoutlmv3.encoder.layer[-4:]:
            for p in layer.parameters():
                p.requires_grad_(True)
        for p in model.classifier.parameters():
            p.requires_grad_(True)
        if a.device == "cuda":
            # O LayoutLMv3 desta versao do transformers nao tem gradient checkpointing (falhou na GPU
            # em 05/10 02:41). So as quatro ultimas camadas treinam, entao cabe em 6 GB sem ele.
            try:
                model.gradient_checkpointing_enable()
                model.enable_input_require_grads()
            except ValueError:
                pass
        return model.to(a.device), None
    from transformers import LayoutLMModel
    # Resolver apenas o snapshot existente; from_pretrained das classes nao tem opcao offline.
    cache = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache/huggingface"))) / "hub/models--microsoft--layoutlm-base-uncased"
    revision = (cache / "refs/main").read_text(encoding="utf-8").strip()
    base = str(cache / "snapshots" / revision)
    original = LayoutLMModel.from_pretrained
    descriptor = LayoutLMModel.__dict__.get("from_pretrained")
    LayoutLMModel.from_pretrained = staticmethod(lambda *args, **kw: original(*args, **{**kw,
        "local_files_only": True, "disable_mmap": True, "dtype": torch.float32}))
    try:
        model = (sucessor.LayoutLMSucessor(base, usar_texto=True) if a.modelo == "sucessor"
                 else pontual.LayoutLMOrdem(base))
    finally:
        if descriptor is None:
            del LayoutLMModel.from_pretrained
        else:
            LayoutLMModel.from_pretrained = descriptor
    if a.device == "cuda":
        model.enc.gradient_checkpointing_enable()
    return model.to(a.device), UmToken()


def preparar_pagina(p, a):
    if a.modelo == "lstm":
        lstm.preparar([p])
        return p, {b["id"]: [b["id"]] for b in p["bounding_boxes"]}
    return compactar(p)


def lote_reader(p, ordem, device):
    n = len(ordem)
    W, H = p["dimensions"]["width"], p["dimensions"]["height"]
    bb = [pontual.normalizar_bbox(p["bounding_boxes"][i]["bbox"], W, H) for i in ordem]
    return {"input_ids": torch.tensor([[0]+[3]*n+[2]], device=device),
            "bbox": torch.tensor([[[0]*4]+bb+[[0]*4]], device=device),
            "attention_mask": torch.ones((1,n+2), dtype=torch.long, device=device)}


def amp(a):
    return torch.autocast("cuda", dtype=torch.float16) if a.device == "cuda" else contextlib.nullcontext()


def perda(model, cod, ps, a):
    ordens = [protocolo.ordem_entrada(p) for p in ps]
    ref = protocolo.carregar_splits()["referencia"]
    if a.modelo == "lstm":
        geo, ids, offs, lens, alvo, mask = lstm.montar(ps, ordens, ref)
        esc = model(geo, ids, offs, lens)
        return (((esc-alvo)**2)*mask).sum()/mask.sum()
    if a.modelo == "layoutreader":
        p, o = ps[0], ordens[0]
        n = len(o)
        # Mesmo contrato do adaptador: linhas dos logits sao postos de SAIDA,
        # colunas sao indices da entrada; nao aplicar argsort na decodificacao.
        idx = {p["bounding_boxes"][bi]["id"]: j for j, bi in enumerate(o)}
        alvo = torch.tensor([idx[bid] for bid in p["ordens"][ref]], device=a.device)
        with amp(a):
            z = model(**lote_reader(p, o, a.device)).logits[0, 1:n+1, :n]
        return torch.nn.functional.cross_entropy(z.float(), alvo)
    module = sucessor if a.modelo == "sucessor" else pontual
    tensors, N = module.montar_lote(cod, ps, ordens, ref, a.device)
    with amp(a):
        if a.modelo == "sucessor":
            s, pos = model(tensors["input_ids"], tensors["bbox"], tensors["attention_mask"],
                tensors["bloco_de"], tensors["valido"], tensors["geo"], N)
            ce, mse = sucessor.perda(s, pos, tensors, tensors["valido"])
            return ce + a.peso_posicao*mse
        esc = model(tensors["input_ids"], tensors["bbox"], tensors["attention_mask"], tensors["bloco_de"], N)
    return (((esc.float()-tensors["alvo"])**2)*tensors["mask"]).sum()/tensors["mask"].sum()


@torch.no_grad()
def prever(model, cod, p, a):
    model.eval()
    p, grupos = preparar_pagina(p, a)
    o = protocolo.ordem_entrada(p)
    if a.modelo == "lstm":
        pred = lstm.prever(model, [p])[0][0]
    elif a.modelo == "layoutreader":
        from orquestracao.analises.ordem_layoutreader import decodificar
        with amp(a):
            z = model(**lote_reader(p, o, a.device)).logits[0, 1:len(o)+1, :len(o)]
        cam, _ = decodificar(z.float().cpu().numpy())
        pred = [p["bounding_boxes"][o[j]]["id"] for j in cam]
    else:
        module = sucessor if a.modelo == "sucessor" else pontual
        t, N = module.montar_lote(cod, [p], [o], None, a.device)
        with amp(a):
            if a.modelo == "sucessor":
                s, pos = model(t["input_ids"], t["bbox"], t["attention_mask"], t["bloco_de"], t["valido"], t["geo"], N)
            else:
                esc = model(t["input_ids"], t["bbox"], t["attention_mask"], t["bloco_de"], N)
        if a.modelo == "sucessor":
            cam = sucessor.decodificar_cadeias(sucessor.log_probs(s)[0].cpu().numpy(), pos[0].float().cpu().numpy(), N, a.limiar_cadeia)
        else:
            cam = sorted(range(len(o)), key=lambda j: float(esc[0,j]))
        pred = [p["bounding_boxes"][o[j]]["id"] for j in cam]
    return [bid for g in pred for bid in grupos[g]]


def validar(model, cod, refs, a):
    ref_key = protocolo.carregar_splits()["referencia"]
    taus = []
    for r in refs:
        p = pagina(r)
        taus.append(kendall_tau(prever(model, cod, p, a), p["ordens"][ref_key]))
    return statistics.mean(taus)


def treinar(a):
    if a.modelo == "lstm" and a.device != "cpu":
        raise ValueError("BiLSTM desta tarefa roda so em CPU")
    treino = indice(a.representacao, "treino", a.blocos, a.blocos_extra)
    expected = ler(UNIDADES / "treino_noite.json")["por_representacao"][a.representacao]["paginas_unicas"]
    if len(treino) != expected:
        raise ValueError(f"Conjunto congelado divergente: {len(treino)} != {expected}")
    ids = [r[2] for r in treino]
    if a.n_treino is not None:
        if a.n_treino > expected or a.n_treino <= 0:
            raise ValueError("n-treino fora do conjunto congelado")
        random.Random(20261004).shuffle(treino)
        treino = treino[:a.n_treino]
    valid = indice(a.representacao, "validacao", a.blocos)
    # Uma pagina por micro-lote para LayoutLM: memoria independe da quantidade do corpus.
    if a.modelo != "lstm" and a.micro_batch != 1:
        raise ValueError("Usar micro-batch 1 para os transformers nesta maquina")
    a.dir_saida.mkdir(parents=True, exist_ok=True)
    config = vars(a).copy()
    config = {k: str(v) if isinstance(v, Path) else v for k,v in config.items()}
    assinatura = {k:v for k,v in config.items() if k not in ("device", "modo", "max_minutos", "max_passos")}
    assinatura["fontes"] = {p:sha(p) for p in sorted({r[0] for r in treino+valid})}
    assinatura["ids_congelados_sha256"] = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    assinatura["codigo_sha256"] = sha(__file__)
    fingerprint = hashlib.sha256(json.dumps(assinatura, sort_keys=True).encode()).hexdigest()
    ultimo, melhor = a.dir_saida / "ultimo.pt", a.dir_saida / "melhor.pt"
    info_path = a.dir_saida / "treino.json"
    if info_path.exists() and ler(info_path).get("concluido"):
        if ler(info_path)["fingerprint"] != fingerprint:
            raise ValueError("Configuracao/fontes mudaram; nao misturar checkpoint")
        print(f"[retomada] {a.nome} ja concluido", flush=True)
        return
    model, cod = criar_modelo(a)
    if a.modelo == "lstm":
        opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    elif a.modelo == "layoutreader":
        encoder = [p for p in model.layoutlmv3.parameters() if p.requires_grad]
        opt = torch.optim.AdamW([{"params": encoder, "lr": a.lr},
            {"params": model.classifier.parameters(), "lr": a.lr_cabeca}], weight_decay=.01)
    else:
        opt = torch.optim.AdamW([{"params": model.enc.parameters(), "lr": a.lr},
            {"params": [p for n,p in model.named_parameters() if not n.startswith("enc.")], "lr": a.lr_cabeca}], weight_decay=.01)
    acum = max(1, a.batch // a.micro_batch)
    total = math.ceil(len(treino)/a.batch)*a.epocas
    warm = max(1, int(.06*total))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s+1)/warm if s < warm else max(.02, (total-s)/max(1,total-warm))) if a.modelo != "lstm" else None
    scaler = torch.amp.GradScaler("cuda", enabled=a.device == "cuda")
    ep, cursor, passos, segundos, best = 0, 0, 0, 0., -2.
    historico, paginas_visitadas = [], set()
    if ultimo.exists():
        state = torch.load(ultimo, map_location="cpu", weights_only=False)
        if state["fingerprint"] != fingerprint:
            raise ValueError("Checkpoint de outra configuracao/fontes")
        model.load_state_dict(state["modelo"])
        opt.load_state_dict(state["otimizador"])
        if sched:
            sched.load_state_dict(state["scheduler"])
        scaler.load_state_dict(state["scaler"])
        torch.set_rng_state(state["torch_rng"])
        if a.device == "cuda" and state.get("cuda_rng") is not None:
            torch.cuda.set_rng_state_all(state["cuda_rng"])
        ep, cursor, passos, segundos, best = (state[k] for k in ("ep", "cursor", "passos", "segundos", "best"))
        historico, paginas_visitadas = state["historico"], set(state["paginas_visitadas"])
        del state
    inicio, ultima_gravacao = time.monotonic(), time.monotonic()
    info = {"config":config, "fingerprint":fingerprint, "paginas_treino":len(treino),
        "paginas_congeladas":expected, "paginas_validacao":len(valid), "tokens_por_unidade": None if a.modelo == "lstm" else 1,
        "treinaveis":sum(p.numel() for p in model.parameters() if p.requires_grad),
        "parametros":sum(p.numel() for p in model.parameters()), "memoria_apos_modelo":memoria()}
    def persistir(concluido=False):
        elapsed = segundos + time.monotonic()-inicio
        state = {"fingerprint":fingerprint, "config":config, "modelo":model.state_dict(),
            "otimizador":opt.state_dict(), "scheduler":sched.state_dict() if sched else None,
            "scaler":scaler.state_dict(), "torch_rng":torch.get_rng_state(),
            "cuda_rng":torch.cuda.get_rng_state_all() if a.device == "cuda" else None,
            "ep":ep,"cursor":cursor,"passos":passos,"segundos":elapsed,"best":best,
            "historico":historico,"paginas_visitadas":sorted(paginas_visitadas)}
        salvar_torch(ultimo, state)
        info.update(epocas_completas=ep, cursor=cursor, passos=passos, segundos=elapsed,
            melhor_val_tau_unidades=best, historico=historico, paginas_visitadas=len(paginas_visitadas), concluido=concluido)
        gravar(info_path, info)
        relatorio()
    def guardar_melhor():
        salvar_torch(melhor, {"modelo":model.state_dict(), "config":config,"fingerprint":fingerprint})
    persistir()
    print(f"[treino] {a.nome}: {len(treino)}/{expected} paginas; {a.device}; micro={a.micro_batch}; acum={acum}", flush=True)
    parar = False
    loss_value = None
    while ep < a.epocas and not parar:
        ordem = list(range(len(treino)))
        random.Random(a.seed+ep).shuffle(ordem)
        model.train()
        while cursor < len(ordem):
            if segundos+time.monotonic()-inicio >= a.max_minutos*60 or a.max_passos and passos >= a.max_passos:
                parar = True
                break
            tamanho = min(a.batch, len(ordem)-cursor)
            opt.zero_grad(set_to_none=True)
            for k in range(0, tamanho, a.micro_batch):
                inds = ordem[cursor+k:cursor+min(k+a.micro_batch,tamanho)]
                ps = [preparar_pagina(pagina(treino[j]), a)[0] for j in inds]
                loss = perda(model, cod, ps, a)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"Perda nao finita: {loss.item()}")
                scaler.scale(loss / math.ceil(tamanho/a.micro_batch)).backward()
                loss_value = float(loss.detach())
                paginas_visitadas.update(treino[j][2] for j in inds)
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            scaler.step(opt)
            scaler.update()
            if sched:
                sched.step()
            cursor += tamanho
            passos += 1
            if passos % 10 == 0:
                print(f"  ep={ep+1} pagina={cursor}/{len(treino)} passo={passos} loss={loss_value:.5f} s={segundos+time.monotonic()-inicio:.1f}", flush=True)
            if time.monotonic()-ultima_gravacao >= 60:
                persistir()
                ultima_gravacao = time.monotonic()
        tau = validar(model, cod, valid, a)
        historico.append({"epoca":ep+1,"cursor":cursor,"passos":passos,"val_tau_unidades":tau,"ultima_loss":loss_value})
        if tau > best:
            best = tau
            guardar_melhor()
        print(f"[val] {a.nome}: tau unidades={tau:.6f}, passos={passos}", flush=True)
        if cursor == len(ordem):
            ep += 1
            cursor = 0
        persistir()
    persistir(concluido=True)
    print(f"[OK] {a.nome}: {passos} passos, {info['segundos']:.1f}s, melhor val={best:.6f}", flush=True)


def relatorio():
    """Escreve numeros somente dos JSONs de execucao, inclusive durante o treino."""
    OUT.mkdir(parents=True, exist_ok=True)
    congelado = ler(UNIDADES / "treino_noite.json")
    txt = ["# Ordenadores treinados sobre unidades sem caixas finas", "",
        "Relatório gerado por `treinar_sem_caixas.py`; estado parcial é preservado a cada checkpoint.", "",
        f"Amostra fixa: prefixo de {congelado['limite_treino_pedido']} páginas pedidas, semente 20261004, de {congelado['elegiveis']} elegíveis; {len(congelado['puladas'])} puladas por recorte deslocado. Não foi exportada nenhuma página adicional.", ""]
    for rep, c in congelado["por_representacao"].items():
        txt.append(f"- `{rep}`: {c['base']} registros base + {c['extra']} extras = {c['paginas_unicas']} páginas únicas após deduplicação. Todos os treinos completos usam exatamente estes IDs; fumaças são subconjuntos explicitamente separados.")
    signal = ler(RAIZ / "resultados/ordenadores_sem_caixas/ancora_ok.json")
    txt += ["", "Âncoras conferidas antes do treino com `bancada_ordenadores.py --somente-ancoras`:", "",
        "| Âncora v4 | τ palavras | Quebras/página |", "|---|---:|---:|"]
    for k in ("P2", "P1m"):
        v = signal["ancoras"][k]
        txt.append(f"| {k} | {v['tau']:.6f} | {v['quebras']:.6f} |".replace(".", ","))
    txt += ["", "## Treinos executados", "", "| Modelo | Representação | Device | Páginas | Visitadas | Passos | Épocas completas | Segundos | τ validação de unidades | Concluído |", "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for path in sorted(OUT.glob("*/treino.json")):
        t = ler(path)
        c = t["config"]
        txt.append(f"| {c['nome']} | {c['representacao']} | {c['device']} | {t['paginas_treino']} | {t.get('paginas_visitadas',0)} | {t.get('passos',0)} | {t.get('epocas_completas',0)} | {t.get('segundos',0):.1f} | {t.get('melhor_val_tau_unidades',-2):.6f} | {t.get('concluido',False)} |")
    bancada = ler(RAIZ / "resultados/ordenadores_sem_caixas.json")
    txt += ["", "## Régua de palavras, por bancada", "", "As métricas abaixo vêm da bancada existente; a expansão interna é `ordem_sem_bbox.fluxo()`. Validação escolhe checkpoint por τ de unidades em RN; não usa ouro humano.", "",
        "| Modelo | Representação | Bancada | Grupo | n | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas | Δτ ao oráculo mediano | Δquebras ao oráculo |", "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for key, r in sorted(bancada["resultados"].items()):
        if not r["ordenador"].startswith(("lstm_", "sucessor_", "pontual_", "layoutreader_ajustado")):
            continue
        # Medias por pagina diretamente, sem reimplementar qualquer metrica.
        teto = bancada["resultados"].get(f"teto__{r['representacao']}__{r['bancada']}")
        for group, visto in (("todos",None),("vistos",True),("não vistos",False)):
            rows = [p for p in r["paginas"] if visto is None or p["visto_treino"] == visto]
            if not rows:
                continue
            met = {m:statistics.mean(p["metricas"][m] for p in rows) for m in ("tau","quebras","fid12","sucessor_linhas")}
            dt, dq = "—", "—"
            if teto:
                tr = [p for p in teto["paginas"] if p["page_id"] in {q['page_id'] for q in rows}]
                if len(tr) == len(rows):
                    dt = f"{statistics.mean(p['metricas']['tau'] for p in tr)-met['tau']:.6f}"
                    dq = f"{met['quebras']-statistics.mean(p['metricas']['quebras'] for p in tr):.2f}"
            txt.append(f"| {r['ordenador']} | {r['representacao']} | {r['bancada']} | {group} | {len(rows)} | {met['tau']:.6f} | {met['quebras']:.2f} | {100*met['fid12']:.2f}% | {100*met['sucessor_linhas']:.2f}% | {dt} | {dq} |")
    txt += ["", "## Veículos vistos nas bancadas humanas", ""]
    train = set(protocolo.carregar_splits()["treino"])
    for b in ("golden_v4", "golden_v3_novo"):
        rows = []
        with (UNIDADES / "bancadas" / (b+".jsonl")).open(encoding="utf-8") as f:
            for l in f:
                q = json.loads(l)
                rows.append((q["page_id"],q["uf"] in train))
        vistos = [p for p,v in rows if v]
        txt.append(f"`{b}`: {len(vistos)} vistas por veículo e {len(rows)-len(vistos)} não vistas. Nenhuma destas páginas entrou no treino.")
        txt += [""] + [f"- `{p}`" for p in vistos] + [""]
    txt += ["## Adaptações e limitações", "",
        "Os embrulhos importam as arquiteturas e perdas existentes. Leitura por offsets, micro-lotes sequenciais, sem workers, no máximo quatro threads; caches/checkpoints em resultados. BiLSTM mantém MSE/Adam 0,002 e até 40 épocas, orçamento de oito minutos por variante/representação. O prazo é conferido entre lotes; validação e gravação final podem acrescentar tempo. Entrada fixa do protocolo em treino e inferência.", "",
        "LayoutLM usa exatamente um token [UNK] por unidade, além de CLS/SEP: não há tokenização de texto nem truncamento silencioso. Sucessor mantém viés geométrico, peso de posição e decodificação em cadeias do melhor config anterior. Pontual também recebe UNK único: ablação geométrica declarada. A única página que excede 510 unidades é agrupada em faixas por geometria, com ordem interna congelada, e todas as suas unidades continuam no treino. Contagens auditadas por representação/partição estão em auditoria_tokens.json.", "",
        "LayoutReader ajusta as últimas quatro camadas e a cabeça, preservando pesos locais iniciais; o restante do encoder fica congelado para caber em 6 GB. Um token de caixa por unidade, fp16 com AMP apenas na GPU; CPU float32. Gradient checkpointing na GPU. A perda ensina diretamente a permutação retornada pelo decoder local (posto de saída → índice de entrada); não se inverte com argsort.", "",
        "Colunas têm poucas unidades e ordem interna imposta: o ordenador quase não pode consertar quebras internas. Linhas deixam mais decisões ao ordenador e aproximam o oráculo humano, mas apertam o orçamento de tokens. O teste silver discorda da expansão canônica dentro das tabelas; comparar τ e distância ao oráculo, sem interpretar todas as quebras absolutas como erro do ordenador.", "",
        "Golden v4 participou do desenvolvimento da regra de colunas; golden v3 adicional é pequeno e pode repetir veículos. Ouro humano é de regiões expandido geometricamente. Silver é automático, nos veículos confiáveis e split congelado; páginas humanas e silver podem se sobrepor e não devem ser somadas. Veículo visto refere-se ao split do TCC, não ao treinamento prévio do ls3/LayoutReader.", "",
        "## Roteiros de GPU", "",
        "Os quatro roteiros são independentes e retomáveis; treinam 873 páginas únicas, até quatro épocas e 75 minutos, batch efetivo 8/micro-batch 1; encoder lr 0,00004, cabeça 0,001, seed 42. Inferência sequencial nas três bancadas em CPU após encerrar o processo de treino; cada JSONL é incorporado com --avaliar-pred, sem alterar a expansão da bancada. Nenhum roteiro foi executado em GPU por esta tarefa.", ""]
    for path in sorted((RAIZ / "orquestracao/noite_0410/gpu").glob("[0-9]*.sh")):
        txt.append(f"- `{path.relative_to(RAIZ).as_posix()}`")
    evidence = OUT / "auditoria_tokens.json"
    if evidence.exists():
        txt += ["", "```json", json.dumps(ler(evidence), ensure_ascii=False, indent=2), "```"]
    txt += ["", "## Reprodução", "", "```powershell", "venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas.py relatorio", "```", ""]
    (RAIZ / "resultados/ordenadores_treinados_sem_caixas.md").write_text("\n".join(txt), encoding="utf-8")


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("modo", nargs="?", choices=("treinar","relatorio","auditar"), default="treinar")
    ap.add_argument("--modelo", choices=("lstm","sucessor","pontual","layoutreader"), default="lstm")
    ap.add_argument("--variante", choices=("geo","geo_texto"), default="geo")
    ap.add_argument("--representacao", choices=REPS, default="linhas")
    ap.add_argument("--device", choices=("cpu","cuda"), default="cpu")
    ap.add_argument("--nome", default="lstm_geo")
    ap.add_argument("--dir-saida", type=Path, default=OUT / "lstm_geo")
    ap.add_argument("--blocos", type=Path)
    ap.add_argument("--blocos-extra", type=Path)
    ap.add_argument("--n-treino", type=int)
    ap.add_argument("--max-minutos", type=float, default=8)
    ap.add_argument("--max-passos", type=int, default=0)
    ap.add_argument("--epocas", type=int, default=40)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--micro-batch", type=int, default=1)
    ap.add_argument("--lr", type=float, default=4e-5)
    ap.add_argument("--lr-cabeca", type=float, default=.001)
    ap.add_argument("--peso-posicao", type=float, default=.5)
    ap.add_argument("--limiar-cadeia", type=float, default=.5)
    ap.add_argument("--seed", type=int, default=42)
    return ap


def auditar():
    R = {}
    congelado = ler(UNIDADES / "treino_noite.json")
    todos = {}
    for rep in REPS:
        R[rep] = {}
        for part in ("treino","validacao","teste"):
            refs = indice(rep,part)
            ns, hier = [], []
            for r in refs:
                p = pagina(r)
                ns.append(len(p["bounding_boxes"]))
                if ns[-1] > 510:
                    q, _ = compactar(p)
                    hier.append({"page_id":p["page_id"],"unidades":ns[-1],"faixas":len(q["bounding_boxes"])})
            R[rep][part] = {"paginas":len(refs),"mediana_unidades":statistics.median(ns),"max_unidades":max(ns),
                "tokens_por_unidade":1,"fora_limite_direto":len(hier),"paginas_descartadas":0,"hierarquia":hier}
            if part == "treino":
                if len(refs) != congelado["por_representacao"][rep]["paginas_unicas"]:
                    raise ValueError("Contagem congelada divergente")
                todos[rep] = {r[2] for r in refs}
    if any(v != todos["linhas"] for v in todos.values()):
        raise ValueError("Representacoes nao compartilham o mesmo treino")
    R["mesmos_ids_treino"] = True
    gravar(OUT / "auditoria_tokens.json", R)
    print(json.dumps(R,ensure_ascii=False),flush=True)
    relatorio()


if __name__ == "__main__":
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a = parser().parse_args()
    if a.modo == "relatorio":
        relatorio()
    elif a.modo == "auditar":
        auditar()
    else:
        treinar(a)
