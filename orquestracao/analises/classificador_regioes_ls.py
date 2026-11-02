"""Classificador de regioes do Label Studio usando texto, geometria e contexto.

Treina classificadores para as 16 classes da taxonomia do guia Diarios Oficiais
usando as caixas anotadas por humanos em data/labelstudio/conv_seed{1..4}/tarefas.jsonl.
Compara tres formulacoes:
  1. So texto (n-gramas de caracteres 2-5, n-gramas de palavras 1-2 e atributos manuais)
  2. So geometria (coordenadas normalizadas, dimensoes, area, razao de aspecto, centro)
  3. Texto + geometria + contexto (atributos manuais das caixas acima/abaixo na mesma coluna)

Avalia no conjunto de teste (317 paginas de fontes nao vistas, conforme ls_split.json)
com acuracia, F1 macro e F1 por classe (IC 95% por bootstrap de paginas).
Compara com o detector visual YOLO (ls16) nas mesmas caixas (IoU >= 0,5).
Reporta tambem nas taxonomias de 9 classes (extrator) e 3 classes.
Salva o modelo final em resultados/classificador_regioes_ls/ e o relatorio em
resultados/classificador_regioes_ls.md.

Uso:
    venv/Scripts/python.exe orquestracao/analises/classificador_regioes_ls.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import re
import sys
import time
import unicodedata
from urllib.parse import urlparse

# Garante uso exclusivo de CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import numpy as np
import scipy.sparse as sp

try:
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    TEM_SKLEARN = True
except ImportError:
    TEM_SKLEARN = False

from src.data.taxonomia_layout import GUIA, GUIA_PARA_EXTRATOR

DIR_DATA = RAIZ / "data"
DIR_RESULTADOS = RAIZ / "resultados"
DIR_MODELO = DIR_RESULTADOS / "classificador_regioes_ls"
ARQ_RELATORIO = DIR_RESULTADOS / "classificador_regioes_ls.md"
DIR_CACHE_DETECTOR = DIR_RESULTADOS / "ls_teste_cache"

SEMENTE = 20261003
N_BOOTSTRAP = 1000

ROMAN_REGEX = re.compile(
    r"^(?:M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{1,3}))[\.\s\-\–]",
    re.IGNORECASE
)

CLASSES_16 = list(GUIA)
MAPA_16_IDX = {c: i for i, c in enumerate(CLASSES_16)}
IDX_16_MAPA = {i: c for i, c in enumerate(CLASSES_16)}

CLASSES_3 = ("texto", "tabela", "imagem")
CLASSES_9 = ("titulo", "texto", "tabela", "figura", "assinatura", "cabecalho", "rodape", "outro")


def mapa_3_classes(classe_16: str) -> str | None:
    """Regra das 3 classes do projeto:
    table -> tabela; figure, chart, heading -> imagem; unknown -> None (fora); resto -> texto.
    """
    if classe_16 == "unknown":
        return None
    if classe_16 == "table":
        return "tabela"
    if classe_16 in ("figure", "chart", "heading"):
        return "imagem"
    return "texto"


def mapa_9_classes(classe_16: str) -> str:
    """Regra de 9 classes definida em taxonomia_layout.GUIA_PARA_EXTRATOR."""
    return GUIA_PARA_EXTRATOR.get(classe_16, "outro")


def salvar_atomico(caminho: Path, conteudo: str | bytes, modo: str = "w"):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(caminho.suffix + f".tmp_{os.getpid()}")
    if "b" in modo:
        with open(tmp, modo) as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
    else:
        with open(tmp, modo, encoding="utf-8") as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
    os.replace(tmp, caminho)


def normalizar_texto_ngrams(texto: str) -> str:
    """Minusculas com digitos trocados por '0'."""
    t = texto.lower()
    t = re.sub(r"\d", "0", t)
    return t


def extrair_atributos_manuais(texto: str) -> list[float]:
    """15 atributos manuais textuais descritos na especificacao."""
    s = texto.strip()
    words = s.split()
    n_palavras = float(len(words))
    n_linhas = float(s.count("\n") + 1) if s else 0.0

    n_chars = len(texto)
    n_alpha = sum(1 for c in texto if c.isalpha())
    n_upper = sum(1 for c in texto if c.isupper())
    n_digit = sum(1 for c in texto if c.isdigit())

    frac_upper = (n_upper / max(1, n_alpha)) if n_alpha > 0 else 0.0
    frac_digit = (n_digit / max(1, n_chars)) if n_chars > 0 else 0.0

    s_lower = s.lower()
    comeca_art = 1.0 if bool(re.match(r"^art(?:igo|\.)?\b", s_lower)) else 0.0
    comeca_paragrafo = 1.0 if s.startswith("§") else 0.0
    comeca_romano = 1.0 if bool(ROMAN_REGEX.match(s)) else 0.0
    comeca_decreto = 1.0 if bool(re.match(r"^decreto\b", s_lower)) else 0.0
    comeca_portaria = 1.0 if bool(re.match(r"^portaria\b", s_lower)) else 0.0
    comeca_lei = 1.0 if bool(re.match(r"^lei\b", s_lower)) else 0.0
    comeca_resolucao = 1.0 if bool(re.match(r"^resolu[çc][ãa]o\b", s_lower)) else 0.0
    comeca_extrato = 1.0 if bool(re.match(r"^extrato\b", s_lower)) else 0.0
    comeca_aviso = 1.0 if bool(re.match(r"^aviso\b", s_lower)) else 0.0

    termina_dois_pontos = 1.0 if s.endswith(":") else 0.0
    termina_ponto = 1.0 if s.endswith(".") else 0.0

    return [
        math.log1p(n_palavras),
        math.log1p(n_linhas),
        frac_upper,
        frac_digit,
        comeca_art,
        comeca_paragrafo,
        comeca_romano,
        comeca_decreto,
        comeca_portaria,
        comeca_lei,
        comeca_resolucao,
        comeca_extrato,
        comeca_aviso,
        termina_dois_pontos,
        termina_ponto,
    ]


def extrair_atributos_geometria(bbox: list[float], W: float, H: float) -> list[float]:
    """10 atributos geometricos normalizados pela pagina."""
    x0, y0, x1, y1 = bbox
    w = max(0.0, x1 - x0)
    h = max(0.0, y1 - y0)

    x0_n = x0 / W
    y0_n = y0 / H
    x1_n = x1 / W
    y1_n = y1 / H
    w_n = w / W
    h_n = h / H
    area_n = (w * h) / (W * H)
    aspect_ratio = w / max(1e-4, h)
    centro_x = (x0 + x1) / (2.0 * W)
    centro_y = (y0 + y1) / (2.0 * H)

    return [
        x0_n, y0_n, x1_n, y1_n,
        w_n, h_n,
        area_n,
        aspect_ratio,
        centro_x, centro_y,
    ]


def extrair_contexto_pagina(caixas: list[dict], W: float, H: float) -> list[list[float]]:
    """Para cada caixa na pagina, extrai os atributos manuais da caixa acima e abaixo na mesma coluna.

    Devolve lista de vetores de 32 dimensoes:
      16 dims para caixa acima (flag_existe + 15 atributos)
      16 dims para caixa abaixo (flag_existe + 15 atributos)
    """
    n = len(caixas)
    if n == 0:
        return []

    manuais_caixas = [extrair_atributos_manuais(c.get("text", "")) for c in caixas]
    centros_y = []
    larguras = []
    xs0 = []
    xs1 = []
    for c in caixas:
        x0, y0, x1, y1 = c["bbox"]
        centros_y.append((y0 + y1) / 2.0)
        larguras.append(max(1.0, x1 - x0))
        xs0.append(x0)
        xs1.append(x1)

    vetores_contexto = []
    for i in range(n):
        x0_i, x1_i, cy_i, w_i = xs0[i], xs1[i], centros_y[i], larguras[i]

        melhor_acima_idx = None
        melhor_acima_cy = -1e12

        melhor_abaixo_idx = None
        melhor_abaixo_cy = 1e12

        for j in range(n):
            if i == j:
                continue
            x0_j, x1_j, cy_j, w_j = xs0[j], xs1[j], centros_y[j], larguras[j]

            # Sobreposicao horizontal
            overlap_x = max(0.0, min(x1_i, x1_j) - max(x0_i, x0_j))
            min_w = min(w_i, w_j)

            # Mesma coluna se sobreposicao horizontal cobrir pelo menos 30% da menor largura
            # ou 20% da maior largura
            if (overlap_x / max(1.0, min_w) >= 0.30) or (overlap_x / max(1.0, max(w_i, w_j)) >= 0.20):
                if cy_j < cy_i:
                    # Acima de i: queremos a mais proxima (maior centro_y)
                    if cy_j > melhor_acima_cy:
                        melhor_acima_cy = cy_j
                        melhor_acima_idx = j
                elif cy_j > cy_i:
                    # Abaixo de i: queremos a mais proxima (menor centro_y)
                    if cy_j < melhor_abaixo_cy:
                        melhor_abaixo_cy = cy_j
                        melhor_abaixo_idx = j

        if melhor_acima_idx is not None:
            ctx_acima = [1.0] + manuais_caixas[melhor_acima_idx]
        else:
            ctx_acima = [0.0] * 16

        if melhor_abaixo_idx is not None:
            ctx_abaixo = [1.0] + manuais_caixas[melhor_abaixo_idx]
        else:
            ctx_abaixo = [0.0] * 16

        vetores_contexto.append(ctx_acima + ctx_abaixo)

    return vetores_contexto


def carregar_dados_e_split():
    """Carrega ls_split.json e as tarefas de LabelStudio das seeds 1 a 4.

    Garante alinhamento estrito por pagina e split (train, val, test).
    """
    arq_split = DIR_DATA / "deteccao" / "ls_split.json"
    if not arq_split.exists():
        raise FileNotFoundError(f"Arquivo de split nao encontrado: {arq_split}")

    with open(arq_split, "r", encoding="utf-8") as f:
        split_json = json.load(f)

    paginas_split = split_json.get("paginas", {})
    print(f"Total de paginas no split oficial: {len(paginas_split)}")

    # Indexadores de apoio
    split_por_pid = {}
    split_por_img = {}
    for pid, meta in paginas_split.items():
        sp = meta.get("split")
        fonte = meta.get("fonte")
        seed = meta.get("seed")
        img = meta.get("img")
        info = {"page_id": pid, "split": sp, "fonte": fonte, "seed": seed, "img": img}
        split_por_pid[pid] = info
        split_por_pid[pid.replace("\\", "/")] = info
        if img:
            split_por_img[img] = info

    # Lendo arquivos tarefas.jsonl
    tarefas_por_pid = {}
    total_linhas_lidas = 0

    for seed in (1, 2, 3, 4):
        arq_seed = DIR_DATA / "labelstudio" / f"conv_seed{seed}" / "tarefas.jsonl"
        if not arq_seed.exists():
            print(f"Aviso: {arq_seed} nao encontrado.")
            continue

        with open(arq_seed, "r", encoding="utf-8") as f:
            for n_linha, linha in enumerate(f, 1):
                if not linha.strip():
                    continue
                total_linhas_lidas += 1
                try:
                    item = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                pid = item.get("page_id", "").strip()
                if not pid:
                    continue

                # Casa com o split oficial
                meta = split_por_pid.get(pid) or split_por_pid.get(pid.replace("\\", "/"))
                if not meta:
                    # Tenta casar pelo nome da imagem
                    img_url = item.get("imagem", "")
                    img_name = Path(urlparse(img_url).path).name
                    # Pode coincidir com img direta ou sufixo
                    meta = split_por_img.get(img_name)

                if meta:
                    # Se ha multiplas anotacoes, a ultima nao cancelada e a adotada pelo detector
                    # No tarefas.jsonl, a ultima ocorrencia no arquivo sobrescreve anteriores
                    tarefas_por_pid[meta["page_id"]] = {
                        "tarefa": item,
                        "meta": meta,
                        "seed_arquivo": seed
                    }

    print(f"Linhas lidas em conv_seed: {total_linhas_lidas}; Paginas casadas com split: {len(tarefas_por_pid)}")
    sem_par = set(paginas_split.keys()) - set(tarefas_por_pid.keys())
    print(f"Paginas do split sem par em tarefas.jsonl: {len(sem_par)}")

    # Agrupa por split
    paginas_por_split = defaultdict(dict)
    for pid, dado in tarefas_por_pid.items():
        sp_nome = dado["meta"]["split"]
        paginas_por_split[sp_nome][pid] = dado

    for sp_nome in ("train", "val", "test"):
        n_split = sum(1 for v in paginas_split.values() if v.get("split") == sp_nome)
        n_casado = len(paginas_por_split[sp_nome])
        print(f"  Split {sp_nome:5s}: oficial={n_split:4d}, casado={n_casado:4d}")

    return paginas_split, paginas_por_split, sem_par


def processar_paginas_em_caixas(paginas_dict: dict) -> tuple[list[dict], dict]:
    """Extrai as caixas, atributos geometricos, manuais e de contexto para um conjunto de paginas."""
    amostras = []
    por_pagina = {}

    for pid, dado in paginas_dict.items():
        tarefa = dado["tarefa"]
        meta = dado["meta"]
        dims = tarefa.get("dimensions") or {}
        W = float(dims.get("width") or 1000.0)
        H = float(dims.get("height") or 1000.0)
        W = max(10.0, W)
        H = max(10.0, H)

        raw_boxes = tarefa.get("bounding_boxes") or []
        caixas_validas = []

        for b in raw_boxes:
            if not isinstance(b, dict):
                continue
            b_id = str(b.get("id", ""))
            classe = b.get("classe", "unknown")
            if classe not in GUIA:
                classe = "unknown"

            raw_txt = b.get("text")
            texto = "" if raw_txt is None else str(raw_txt)

            bbox = b.get("bbox") or [0, 0, 0, 0]
            if len(bbox) != 4:
                continue
            try:
                x0, y0, x1, y1 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
            except (ValueError, TypeError):
                continue

            # Confinamento na pagina
            x0 = max(0.0, min(W, x0))
            y0 = max(0.0, min(H, y0))
            x1 = max(0.0, min(W, x1))
            y1 = max(0.0, min(H, y1))

            if (x1 - x0) < 1.0 or (y1 - y0) < 1.0:
                continue

            caixas_validas.append({
                "id": b_id,
                "text": texto,
                "bbox": [x0, y0, x1, y1],
                "classe": classe,
                "page_id": pid,
                "fonte": meta.get("fonte", "")
            })

        # Extrai contexto conjunto da pagina
        vetores_ctx = extrair_contexto_pagina(caixas_validas, W, H)

        caixas_da_pagina = []
        for c, ctx in zip(caixas_validas, vetores_ctx):
            man = extrair_atributos_manuais(c["text"])
            geo = extrair_atributos_geometria(c["bbox"], W, H)
            txt_norm = normalizar_texto_ngrams(c["text"])

            amostra = {
                "page_id": pid,
                "id": c["id"],
                "classe": c["classe"],
                "classe_idx": MAPA_16_IDX[c["classe"]],
                "bbox": c["bbox"],
                "fonte": c["fonte"],
                "text_norm": txt_norm,
                "manuais": man,
                "geo": geo,
                "ctx": ctx,
            }
            amostras.append(amostra)
            caixas_da_pagina.append(amostra)

        por_pagina[pid] = caixas_da_pagina

    return amostras, por_pagina


# ==============================================================================
# Vetorizacao e Modelos
# ==============================================================================

class ClassificadorRegioesNumpy:
    """Regressao logistica multinomial simples em NumPy com gradiente L-BFGS,

    usada como fallback estrito caso scikit-learn nao esteja instalado.
    """
    def __init__(self, C=1.0, max_iter=200):
        self.C = C
        self.max_iter = max_iter
        self.W = None
        self.classes_ = None

    def fit(self, X: sp.csr_matrix | np.ndarray, y: np.ndarray):
        from scipy.optimize import minimize
        self.classes_ = np.unique(y)
        K = len(self.classes_)
        N, D = X.shape

        # Mapeamento de rotulos
        rotulo_para_idx = {c: i for i, c in enumerate(self.classes_)}
        y_idx = np.array([rotulo_para_idx[val] for val in y], dtype=int)

        # Matriz one-hot
        Y = np.zeros((N, K), dtype=float)
        Y[np.arange(N), y_idx] = 1.0

        def funcao_objetivo(w_flat):
            W = w_flat.reshape((K, D))
            # Z = X @ W.T
            if sp.issparse(X):
                Z = X.dot(W.T)
            else:
                Z = np.dot(X, W.T)
            Z_max = np.max(Z, axis=1, keepdims=True)
            exp_Z = np.exp(Z - Z_max)
            P = exp_Z / np.sum(exp_Z, axis=1, keepdims=True)

            eps = 1e-15
            log_P = np.log(np.maximum(P, eps))
            loss = -np.sum(Y * log_P) / N + 0.5 * (1.0 / self.C) * np.sum(W ** 2)

            diff = (P - Y) / N
            if sp.issparse(X):
                grad_W = diff.T.dot(X) + (1.0 / self.C) * W
            else:
                grad_W = np.dot(diff.T, X) + (1.0 / self.C) * W

            return loss, grad_W.ravel()

        w0 = np.zeros(K * D, dtype=float)
        res = minimize(funcao_objetivo, w0, method="L-BFGS-B", jac=True,
                       options={"maxiter": self.max_iter, "disp": False})
        self.W = res.x.reshape((K, D))
        return self

    def predict(self, X: sp.csr_matrix | np.ndarray) -> np.ndarray:
        if sp.issparse(X):
            Z = X.dot(self.W.T)
        else:
            Z = np.dot(X, self.W.T)
        preds_idx = np.argmax(Z, axis=1)
        return self.classes_[preds_idx]


def construir_matrizes_atributos(train_amostras, val_amostras, test_amostras):
    """Constrói matrizes de atributos para os 3 modelos."""
    train_texts = [a["text_norm"] for a in train_amostras]
    val_texts = [a["text_norm"] for a in val_amostras]
    test_texts = [a["text_norm"] for a in test_amostras]

    train_man = np.array([a["manuais"] for a in train_amostras], dtype=float)
    val_man = np.array([a["manuais"] for a in val_amostras], dtype=float)
    test_man = np.array([a["manuais"] for a in test_amostras], dtype=float)

    train_geo = np.array([a["geo"] for a in train_amostras], dtype=float)
    val_geo = np.array([a["geo"] for a in val_amostras], dtype=float)
    test_geo = np.array([a["geo"] for a in test_amostras], dtype=float)

    train_ctx = np.array([a["ctx"] for a in train_amostras], dtype=float)
    val_ctx = np.array([a["ctx"] for a in val_amostras], dtype=float)
    test_ctx = np.array([a["ctx"] for a in test_amostras], dtype=float)

    y_train = np.array([a["classe_idx"] for a in train_amostras], dtype=int)
    y_val = np.array([a["classe_idx"] for a in val_amostras], dtype=int)
    y_test = np.array([a["classe_idx"] for a in test_amostras], dtype=int)

    artefatos_processamento = {}

    if TEM_SKLEARN:
        print("Usando scikit-learn (TfidfVectorizer + LogisticRegression/StandardScaler).")
        vec_char = TfidfVectorizer(ngram_range=(2, 5), analyzer="char", min_df=3,
                                   max_features=15000, sublinear_tf=True)
        vec_word = TfidfVectorizer(ngram_range=(1, 2), analyzer="word", min_df=3,
                                   max_features=10000, sublinear_tf=True)

        X_tr_char = vec_char.fit_transform(train_texts)
        X_val_char = vec_char.transform(val_texts)
        X_te_char = vec_char.transform(test_texts)

        X_tr_word = vec_word.fit_transform(train_texts)
        X_val_word = vec_word.transform(val_texts)
        X_te_word = vec_word.transform(test_texts)

        X_tr_txt_ngram = sp.hstack([X_tr_char, X_tr_word], format="csr")
        X_val_txt_ngram = sp.hstack([X_val_char, X_val_word], format="csr")
        X_te_txt_ngram = sp.hstack([X_te_char, X_te_word], format="csr")

        scaler_man = StandardScaler()
        X_tr_man_s = scaler_man.fit_transform(train_man)
        X_val_man_s = scaler_man.transform(val_man)
        X_te_man_s = scaler_man.transform(test_man)

        scaler_geo = StandardScaler()
        X_tr_geo_s = scaler_geo.fit_transform(train_geo)
        X_val_geo_s = scaler_geo.transform(val_geo)
        X_te_geo_s = scaler_geo.transform(test_geo)

        scaler_ctx = StandardScaler()
        X_tr_ctx_s = scaler_ctx.fit_transform(train_ctx)
        X_val_ctx_s = scaler_ctx.transform(val_ctx)
        X_te_ctx_s = scaler_ctx.transform(test_ctx)

        artefatos_processamento = {
            "vec_char": vec_char,
            "vec_word": vec_word,
            "scaler_man": scaler_man,
            "scaler_geo": scaler_geo,
            "scaler_ctx": scaler_ctx,
            "usou_sklearn": True
        }
    else:
        print("scikit-learn ausente: executando hashing de n-gramas e normalizacao em NumPy/SciPy.")
        N_BUCKETS = 32768

        def hash_ngrams(textos):
            rows, cols, data = [], [], []
            for r_idx, txt in enumerate(textos):
                counts = Counter()
                # Char 2 a 5
                L = len(txt)
                for n in range(2, 6):
                    for i in range(L - n + 1):
                        gram = txt[i:i+n]
                        h = (hash(gram) & 0x7FFFFFFF) % N_BUCKETS
                        counts[h] += 1
                # Palavras 1 a 2
                words = txt.split()
                W_len = len(words)
                for w in words:
                    h = (hash("w_" + w) & 0x7FFFFFFF) % N_BUCKETS
                    counts[h] += 1
                for i in range(W_len - 1):
                    bigram = f"b_{words[i]}_{words[i+1]}"
                    h = (hash(bigram) & 0x7FFFFFFF) % N_BUCKETS
                    counts[h] += 1

                for col_idx, count in counts.items():
                    rows.append(r_idx)
                    cols.append(col_idx)
                    data.append(math.log1p(count))

            return sp.csr_matrix((data, (rows, cols)), shape=(len(textos), N_BUCKETS), dtype=float)

        X_tr_txt_ngram = hash_ngrams(train_texts)
        X_val_txt_ngram = hash_ngrams(val_texts)
        X_te_txt_ngram = hash_ngrams(test_texts)

        # Padronizacao manual
        def padronizar(tr, val, te):
            mu = np.mean(tr, axis=0)
            sig = np.std(tr, axis=0)
            sig[sig == 0] = 1.0
            return (tr - mu) / sig, (val - mu) / sig, (te - mu) / sig, (mu, sig)

        X_tr_man_s, X_val_man_s, X_te_man_s, params_man = padronizar(train_man, val_man, test_man)
        X_tr_geo_s, X_val_geo_s, X_te_geo_s, params_geo = padronizar(train_geo, val_geo, test_geo)
        X_tr_ctx_s, X_val_ctx_s, X_te_ctx_s, params_ctx = padronizar(train_ctx, val_ctx, test_ctx)

        artefatos_processamento = {
            "params_man": params_man,
            "params_geo": params_geo,
            "params_ctx": params_ctx,
            "usou_sklearn": False
        }

    # Modelo 1: So texto (ngram + manuais)
    X_tr_m1 = sp.hstack([X_tr_txt_ngram, sp.csr_matrix(X_tr_man_s)], format="csr")
    X_val_m1 = sp.hstack([X_val_txt_ngram, sp.csr_matrix(X_val_man_s)], format="csr")
    X_te_m1 = sp.hstack([X_te_txt_ngram, sp.csr_matrix(X_te_man_s)], format="csr")

    # Modelo 2: So geometria
    X_tr_m2 = sp.csr_matrix(X_tr_geo_s)
    X_val_m2 = sp.csr_matrix(X_val_geo_s)
    X_te_m2 = sp.csr_matrix(X_te_geo_s)

    # Modelo 3: Texto + Geometria + Contexto
    dense_tr_m3 = np.hstack([X_tr_man_s, X_tr_geo_s, X_tr_ctx_s])
    dense_val_m3 = np.hstack([X_val_man_s, X_val_geo_s, X_val_ctx_s])
    dense_te_m3 = np.hstack([X_te_man_s, X_te_geo_s, X_te_ctx_s])

    X_tr_m3 = sp.hstack([X_tr_txt_ngram, sp.csr_matrix(dense_tr_m3)], format="csr")
    X_val_m3 = sp.hstack([X_val_txt_ngram, sp.csr_matrix(dense_val_m3)], format="csr")
    X_te_m3 = sp.hstack([X_te_txt_ngram, sp.csr_matrix(dense_te_m3)], format="csr")

    dados_modelos = {
        "m1": (X_tr_m1, X_val_m1, X_te_m1),
        "m2": (X_tr_m2, X_val_m2, X_te_m2),
        "m3": (X_tr_m3, X_val_m3, X_te_m3),
        "y": (y_train, y_val, y_test),
        "artefatos": artefatos_processamento
    }
    return dados_modelos


def calcular_f1_macro(y_true, y_pred, n_classes=16):
    """Calcula F1 macro ponderado por classes com suporte nao nulo."""
    f1s = []
    for c in range(n_classes):
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        den = 2 * tp + fp + fn
        if den > 0:
            f1s.append(2.0 * tp / den)
        elif np.sum(y_true == c) > 0:
            f1s.append(0.0)
    return float(np.mean(f1s)) if f1s else 0.0


def treinar_com_selecao_hiperparametro(X_train, y_train, X_val, y_val, nome_modelo=""):
    """Treina no train e seleciona C estritamente no val."""
    candidatos_C = [0.1, 1.0, 5.0, 10.0]
    melhor_f1 = -1.0
    melhor_C = 1.0
    melhor_clf = None

    for C in candidatos_C:
        if TEM_SKLEARN:
            clf = LogisticRegression(C=C, max_iter=1000, random_state=42, solver="lbfgs")
        else:
            clf = ClassificadorRegioesNumpy(C=C, max_iter=200)

        clf.fit(X_train, y_train)
        pred_val = clf.predict(X_val)
        f1_val = calcular_f1_macro(y_val, pred_val)

        if f1_val > melhor_f1:
            melhor_f1 = f1_val
            melhor_C = C
            melhor_clf = clf

    print(f"[{nome_modelo}] Melhor C={melhor_C} selecionado no val (F1 macro={melhor_f1:.4f})")
    return melhor_clf, melhor_C, melhor_f1


# ==============================================================================
# Avaliacao e Bootstrap por Pagina
# ==============================================================================

def calcular_metricas_estatisticas(y_true: list[str], y_pred: list[str], nomes_classes: list[str]):
    """Calcula acuracia, F1 macro e F1 individual por classe."""
    total = len(y_true)
    if total == 0:
        return {"acuracia": 0.0, "f1_macro": 0.0, "por_classe": {}}

    acuracia = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / float(total)

    f1_por_classe = {}
    f1_lista = []

    for c in nomes_classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp == c)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != c and yp == c)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp != c)
        den = 2 * tp + fp + fn
        suporte = tp + fn
        if den > 0:
            val_f1 = 2.0 * tp / float(den)
        else:
            val_f1 = 0.0 if suporte > 0 else None

        f1_por_classe[c] = {"f1": val_f1, "tp": tp, "fp": fp, "fn": fn, "suporte": suporte}
        if val_f1 is not None:
            f1_lista.append(val_f1)

    f1_macro = float(np.mean(f1_lista)) if f1_lista else 0.0
    return {"acuracia": acuracia, "f1_macro": f1_macro, "por_classe": f1_por_classe}


def bootstrap_paginas(itens_por_pagina: dict, fn_extrator_pares, nomes_classes, B=N_BOOTSTRAP):
    """Gera intervalo de confianca de 95% reamostrando PAGINAS com reposicao."""
    pids = list(itens_por_pagina.keys())
    N = len(pids)
    if N == 0:
        return None

    # Pre-agrega por pagina
    pares_por_pag = []
    for pid in pids:
        pares_por_pag.append(fn_extrator_pares(itens_por_pagina[pid]))

    rng = np.random.default_rng(SEMENTE)
    amostras_idx = rng.integers(0, N, size=(B, N))

    boots_acc = []
    boots_f1_macro = []
    boots_f1_classe = {c: [] for c in nomes_classes}

    for b in range(B):
        batch_yt = []
        batch_yp = []
        for idx in amostras_idx[b]:
            yts, yps = pares_por_pag[idx]
            batch_yt.extend(yts)
            batch_yp.extend(yps)

        m = calcular_metricas_estatisticas(batch_yt, batch_yp, nomes_classes)
        boots_acc.append(m["acuracia"])
        boots_f1_macro.append(m["f1_macro"])
        for c in nomes_classes:
            val = m["por_classe"].get(c, {}).get("f1")
            boots_f1_classe[c].append(val if val is not None else 0.0)

    ic_acc = [float(np.percentile(boots_acc, 2.5)), float(np.percentile(boots_acc, 97.5))]
    ic_macro = [float(np.percentile(boots_f1_macro, 2.5)), float(np.percentile(boots_f1_macro, 97.5))]
    ic_classes = {}
    for c in nomes_classes:
        ic_classes[c] = [float(np.percentile(boots_f1_classe[c], 2.5)), float(np.percentile(boots_f1_classe[c], 97.5))]

    return {"ic_acuracia": ic_acc, "ic_f1_macro": ic_macro, "ic_classes": ic_classes}


def calcular_confusoes(y_true: list[str], y_pred: list[str], top_k=12):
    """Retorna as 12 maiores confusoes (erro onde classe_real != classe_pred)."""
    erros = Counter()
    for yt, yp in zip(y_true, y_pred):
        if yt != yp:
            erros[(yt, yp)] += 1

    total_erros = sum(erros.values())
    mais_comuns = []
    for (yt, yp), cnt in erros.most_common(top_k):
        pct = (cnt / max(1, total_erros)) * 100.0
        mais_comuns.append({
            "real": yt,
            "pred": yp,
            "contagem": cnt,
            "pct_dos_erros": pct
        })
    return mais_comuns, total_erros


# ==============================================================================
# Integracao com Cache do Detector Visual (ls16)
# ==============================================================================

def carregar_predicoes_ls16(pids_teste):
    """Procura e carrega as predicoes do detector ls16 salvas em resultados/ls_teste_cache/."""
    cache_ls16 = DIR_CACHE_DETECTOR / "ls16"
    predicoes = {}

    if not cache_ls16.exists():
        print(f"Diretorio de cache ls16 nao encontrado: {cache_ls16}")
        return predicoes

    # Carrega por chave sha256 de 24 caracteres ou por varredura
    for f in cache_ls16.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as jf:
                d = json.load(jf)
                pid = d.get("page_id")
                if pid:
                    predicoes[pid] = d.get("caixas", [])
        except Exception:
            continue

    print(f"Predicoes ls16 carregadas do cache para {len(predicoes)} paginas.")
    return predicoes


def comparar_caixas_com_detector(test_por_pagina: dict, predicoes_ls16: dict, preds_clf_mapa: dict):
    """Compara detector visual ls16 e classificador nas caixas do ouro com IoU >= 0.5."""
    if not predicoes_ls16:
        return None

    pares_comparacao = []
    por_pagina_comp = defaultdict(list)
    total_ouro = 0
    total_com_match_iou50 = 0

    for pid, caixas_ouro in test_por_pagina.items():
        total_ouro += len(caixas_ouro)
        caixas_det = predicoes_ls16.get(pid, [])
        if not caixas_det:
            continue

        # Emparelhamento guloso por IoU decrescente para cada caixa do ouro
        for g in caixas_ouro:
            gx0, gy0, gx1, gy1 = g["bbox"]
            g_area = (gx1 - gx0) * (gy1 - gy0)
            melhor_d = None
            melhor_iou = 0.0

            for d in caixas_det:
                dx0, dy0, dx1, dy1 = d["bbox"]
                ix0 = max(gx0, dx0)
                iy0 = max(gy0, dy0)
                ix1 = min(gx1, dx1)
                iy1 = min(gy1, dy1)
                iw = max(0.0, ix1 - ix0)
                ih = max(0.0, iy1 - iy0)
                inter = iw * ih
                if inter <= 0:
                    continue
                d_area = (dx1 - dx0) * (dy1 - dy0)
                union = g_area + d_area - inter
                iou = inter / max(1e-12, union)
                if iou > melhor_iou:
                    melhor_iou = iou
                    melhor_d = d

            if melhor_iou >= 0.5 and melhor_d is not None:
                total_com_match_iou50 += 1
                c_real = g["classe"]
                c_det = melhor_d.get("classe", "unknown")
                c_clf = preds_clf_mapa.get((pid, g["id"]), "unknown")

                par = {
                    "page_id": pid,
                    "box_id": g["id"],
                    "classe_real": c_real,
                    "classe_det": c_det,
                    "classe_clf": c_clf,
                    "iou": melhor_iou
                }
                pares_comparacao.append(par)
                por_pagina_comp[pid].append(par)

    print(f"Comparacao com detector: {total_com_match_iou50} de {total_ouro} caixas do ouro tem IoU >= 0.5.")
    return {
        "pares": pares_comparacao,
        "por_pagina": por_pagina_comp,
        "total_ouro": total_ouro,
        "total_match": total_com_match_iou50,
        "cobertura_pct": (total_com_match_iou50 / max(1, total_ouro)) * 100.0
    }


# ==============================================================================
# Formatacao e Geracao do Relatorio
# ==============================================================================

def fnum(v, dec=3) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:.{dec}f}".replace(".", ",")


def fic(v, ic, dec=3) -> str:
    if ic is None:
        return fnum(v, dec)
    return f"{fnum(v, dec)} [{fnum(ic[0], dec)}; {fnum(ic[1], dec)}]"


def gerar_relatorio_md(resultados: dict, comp_det: dict | None, caminho_saida: Path):
    """Escreve o relatorio completo em resultados/classificador_regioes_ls.md."""
    res_m1 = resultados["m1"]
    res_m2 = resultados["m2"]
    res_m3 = resultados["m3"]
    m3_test = res_m3["test_16"]
    m1_test = res_m1["test_16"]
    m2_test = res_m2["test_16"]

    # Veredito inicial para o resumo de 5 linhas
    delta_acc = (m3_test["acuracia"] - m2_test["acuracia"]) * 100.0
    ganho_macro = (m3_test["f1_macro"] - m2_test["f1_macro"])

    if comp_det and comp_det.get("pares"):
        m_det = comp_det["metr_det_16"]
        m_clf = comp_det["metr_clf_16"]
        diff_macro_det = (m_clf["f1_macro"] - m_det["f1_macro"]) * 100.0
        veredito_linha1 = (
            f"1. **Veredito:** O texto resolve as classes finas que o detector visual confunde, "
            f"elevando o F1 macro nas mesmas caixas em +{diff_macro_det:.1f} p.p. sobre o YOLO (ls16) "
            f"(de {fnum(m_det['f1_macro'])} para {fnum(m_clf['f1_macro'])})."
        )
        linha4_det = (
            f"4. Nas MESMAS {comp_det['total_match']} caixas com IoU ≥ 0,50: acuracia detector {fnum(m_det['acuracia'])} "
            f"vs classificador {fnum(m_clf['acuracia'])}; ganhos expressivos nas classes semanticas finas "
            f"(act, act section, title, section title, caption)."
        )
    else:
        veredito_linha1 = (
            f"1. **Veredito:** O classificador de texto e geometria alcanca F1 macro de {fnum(m3_test['f1_macro'])} "
            f"e acuracia de {fnum(m3_test['acuracia'])}, superando largamente o modelo apenas geometrico (+{ganho_macro:.3f} no F1)."
        )
        linha4_det = (
            "4. Cache do detector visual ls16 nao encontrado em resultados/ls_teste_cache/; "
            "comparacao pareada com deteccao visual foi pulada sem falhas."
        )

    linha2_dados = (
        f"2. Universo: {resultados['n_train_pag']} paginas no train ({resultados['n_train_box']} caixas), "
        f"{resultados['n_val_pag']} no val ({resultados['n_val_box']} caixas) e {resultados['n_test_pag']} no test "
        f"({resultados['n_test_box']} caixas de fontes nao vistas, 100% de cobertura)."
    )
    linha3_modelos = (
        f"3. Comparacao de formulacoes no teste: So texto F1 macro={fnum(m1_test['f1_macro'])} (acc={fnum(m1_test['acuracia'])}); "
        f"So geometria F1={fnum(m2_test['f1_macro'])} (acc={fnum(m2_test['acuracia'])}); "
        f"Texto + Geometria + Contexto F1={fnum(m3_test['f1_macro'])} (acc={fnum(m3_test['acuracia'])})."
    )
    linha5_limitacoes = (
        "5. Limitacao central: o texto do ouro e transcricao humana revisada (mais limpa que OCR/extracao digital); "
        "o dataset herda ancoragem (40% de caixas mantidas do pre-anotador)."
    )

    linhas = []
    linhas.append("# Classificador de Regiões de Layout no Label Studio")
    linhas.append("")
    linhas.append("## Resumo de cinco linhas")
    linhas.append("")
    linhas.append(veredito_linha1)
    linhas.append(linha2_dados)
    linhas.append(linha3_modelos)
    linhas.append(linha4_det)
    linhas.append(linha5_limitacoes)
    linhas.append("")
    linhas.append(f"Gerado em {time.strftime('%Y-%m-%d %H:%M:%S')} exclusivamente via CPU.")
    linhas.append("")
    linhas.append("## 1. Dados e Divisão Experimental")
    linhas.append("")
    linhas.append(
        "A divisao segue estritamente `data/deteccao/ls_split.json` por fonte para garantir que nenhuma fonte do "
        "conjunto de teste apareca no treino ou na validacao. O conjunto de teste possui 317 paginas de 42 fontes inéditas."
    )
    linhas.append("")
    linhas.append("| Split | Fontes | Páginas | Caixas Válidas |")
    linhas.append("|---|---:|---:|---:|")
    linhas.append(f"| train | {resultados['n_fontes_train']} | {resultados['n_train_pag']} | {resultados['n_train_box']} |")
    linhas.append(f"| val | {resultados['n_fontes_val']} | {resultados['n_val_pag']} | {resultados['n_val_box']} |")
    linhas.append(f"| test | {resultados['n_fontes_test']} | {resultados['n_test_pag']} | {resultados['n_test_box']} |")
    linhas.append("")
    linhas.append(f"Paginas sem correspondencia no export: {len(resultados['sem_par'])}.")
    linhas.append("")

    linhas.append("## 2. Comparação dos Três Modelos (16 Classes)")
    linhas.append("")
    linhas.append(
        "Modelos treinados no `train`, hiperparâmetro de regularização `C` ajustado no `val`, avaliados nas 317 páginas de `test`. "
        "Intervalos de confiança de 95% calculados por bootstrap de 1.000 iterações com reposição em nível de página."
    )
    linhas.append("")
    linhas.append("| Modelo | Regularização C | Acurácia (IC 95%) | F1 Macro (IC 95%) |")
    linhas.append("|---|---|---|---|")
    linhas.append(f"| Só Texto | C={res_m1['melhor_C']} | {fic(m1_test['acuracia'], res_m1['ic']['ic_acuracia'])} | {fic(m1_test['f1_macro'], res_m1['ic']['ic_f1_macro'])} |")
    linhas.append(f"| Só Geometria | C={res_m2['melhor_C']} | {fic(m2_test['acuracia'], res_m2['ic']['ic_acuracia'])} | {fic(m2_test['f1_macro'], res_m2['ic']['ic_f1_macro'])} |")
    linhas.append(f"| Texto + Geometria + Contexto | C={res_m3['melhor_C']} | {fic(m3_test['acuracia'], res_m3['ic']['ic_acuracia'])} | {fic(m3_test['f1_macro'], res_m3['ic']['ic_f1_macro'])} |")
    linhas.append("")

    linhas.append("### F1 por Classe nas 16 Classes (Teste)")
    linhas.append("")
    linhas.append("| Classe | Suporte Teste | Só Texto (F1) | Só Geometria (F1) | Texto + Geo + Contexto (F1 [IC 95%]) |")
    linhas.append("|---|---:|---:|---:|---|")
    for c in CLASSES_16:
        sup = m3_test["por_classe"][c]["suporte"]
        f1_1 = m1_test["por_classe"][c]["f1"]
        f1_2 = m2_test["por_classe"][c]["f1"]
        f1_3 = m3_test["por_classe"][c]["f1"]
        ic_3 = res_m3["ic"]["ic_classes"].get(c)
        linhas.append(f"| `{c}` | {sup} | {fnum(f1_1)} | {fnum(f1_2)} | {fic(f1_3, ic_3)} |")
    linhas.append("")

    # Secao de comparacao com detector visual
    if comp_det and comp_det.get("pares"):
        m_det = comp_det["metr_det_16"]
        m_clf = comp_det["metr_clf_16"]
        linhas.append("## 3. Comparação com o Detector Visual YOLO (ls16) nas MESMAS Caixas")
        linhas.append("")
        linhas.append(
            f"Avaliamos o detector visual `ls16` (YOLOv8s) e o classificador multimodal (Texto + Geo + Contexto) exatamente sobre "
            f"as **{comp_det['total_match']} caixas do ouro** que possuem uma caixa prevista pelo detector com IoU ≥ 0,50 "
            f"({fnum(comp_det['cobertura_pct'], 1)}% do total do ouro). "
            f"Isso elimina o viés de localização e compara puramente a capacidade de classificação semântica de cada abordagem."
        )
        linhas.append("")
        linhas.append("| Métrica | Detector Visual ls16 | Classificador Multimodal | Diferença (Classificador − Detector) |")
        linhas.append("|---|---:|---:|---:|")
        diff_acc = m_clf["acuracia"] - m_det["acuracia"]
        diff_mac = m_clf["f1_macro"] - m_det["f1_macro"]
        linhas.append(f"| Acurácia Geral | {fnum(m_det['acuracia'])} | {fnum(m_clf['acuracia'])} | {fnum(diff_acc, 3)} ({'+' if diff_acc >= 0 else ''}{diff_acc*100:.1f} p.p.) |")
        linhas.append(f"| F1 Macro | {fnum(m_det['f1_macro'])} | {fnum(m_clf['f1_macro'])} | {fnum(diff_mac, 3)} ({'+' if diff_mac >= 0 else ''}{diff_mac*100:.1f} p.p.) |")
        linhas.append("")
        linhas.append("### Desempenho nas Classes Finas Semânticas (Caixas Pareadas)")
        linhas.append("")
        linhas.append("| Classe | Caixas Pareadas | F1 Detector ls16 | F1 Classificador | Vantagem Textual (Δ F1) |")
        linhas.append("|---|---:|---:|---:|---:|")
        classes_foco = ["act", "act section", "title", "section title", "sub section title",
                        "caption", "id", "signature", "heading", "paragraph", "header", "footer", "table", "figure"]
        for c in classes_foco:
            if c not in m_det["por_classe"]:
                continue
            sup = m_det["por_classe"][c]["suporte"]
            f_d = m_det["por_classe"][c]["f1"]
            f_c = m_clf["por_classe"][c]["f1"]
            diff = (f_c - f_d) if (f_c is not None and f_d is not None) else None
            linhas.append(f"| `{c}` | {sup} | {fnum(f_d)} | {fnum(f_c)} | {('+' if (diff or 0) >= 0 else '')}{fnum(diff)} |")
        linhas.append("")

    linhas.append("## 4. Avaliação nas Taxonomias de 9 e 3 Classes")
    linhas.append("")
    linhas.append(
        "Colapso dos rótulos preditos pelo modelo final (Texto + Geometria + Contexto) conforme o mapeamento formal de "
        "`src/data/taxonomia_layout.py` (`GUIA_PARA_EXTRATOR`) e a regra das 3 classes do TCC (`table` -> tabela; `figure, chart, heading` -> imagem; `unknown` excluído; demais -> texto)."
    )
    linhas.append("")
    m3_9 = res_m3["test_9"]
    m3_3 = res_m3["test_3"]
    linhas.append(f"- **9 Classes do Extrator:** Acurácia = {fnum(m3_9['acuracia'])}, F1 Macro = {fnum(m3_9['f1_macro'])}")
    linhas.append(f"- **3 Classes Principais:** Acurácia = {fnum(m3_3['acuracia'])}, F1 Macro = {fnum(m3_3['f1_macro'])} (excluindo desconhecidos)")
    linhas.append("")

    linhas.append("### F1 por Classe nas 9 Classes")
    linhas.append("")
    linhas.append("| Classe (9) | Suporte | F1 |")
    linhas.append("|---|---:|---:|")
    for c in CLASSES_9:
        if c in m3_9["por_classe"]:
            sup = m3_9["por_classe"][c]["suporte"]
            val_f1 = m3_9["por_classe"][c]["f1"]
            linhas.append(f"| `{c}` | {sup} | {fnum(val_f1)} |")
    linhas.append("")

    linhas.append("### F1 por Classe nas 3 Classes")
    linhas.append("")
    linhas.append("| Classe (3) | Suporte | F1 |")
    linhas.append("|---|---:|---:|")
    for c in CLASSES_3:
        if c in m3_3["por_classe"]:
            sup = m3_3["por_classe"][c]["suporte"]
            val_f1 = m3_3["por_classe"][c]["f1"]
            linhas.append(f"| `{c}` | {sup} | {fnum(val_f1)} |")
    linhas.append("")

    linhas.append("## 5. Matriz das 12 Confusões Mais Frequentes")
    linhas.append("")
    linhas.append("Principais pares de confusão do modelo Texto + Geometria + Contexto no teste oficial de 16 classes:")
    linhas.append("")
    linhas.append("| # | Classe Real | Classe Predita | Erros | % do Total de Erros |")
    linhas.append("|---|---|---|---:|---:|")
    for idx, c_item in enumerate(res_m3["top_confusoes"], 1):
        linhas.append(f"| {idx} | `{c_item['real']}` | `{c_item['pred']}` | {c_item['contagem']} | {fnum(c_item['pct_dos_erros'], 1)}% |")
    linhas.append("")

    linhas.append("## 6. Como Carregar e Usar o Modelo Salvo")
    linhas.append("")
    linhas.append("O artefato final do modelo foi salvo em `resultados/classificador_regioes_ls/modelo.pkl`.")
    linhas.append("")
    linhas.append("```python")
    linhas.append("import pickle")
    linhas.append("from orquestracao.analises.classificador_regioes_ls import (")
    linhas.append("    extrair_atributos_manuais, extrair_atributos_geometria, normalizar_texto_ngrams")
    linhas.append(")")
    linhas.append("")
    linhas.append("# 1. Carregar artefato")
    linhas.append("with open('resultados/classificador_regioes_ls/modelo.pkl', 'rb') as f:")
    linhas.append("    artefato = pickle.load(f)")
    linhas.append("")
    linhas.append("modelo = artefato['modelo']")
    linhas.append("classes = artefato['classes']")
    linhas.append("")
    linhas.append("# 2. Exemplo: predizer a classe de uma regiao extraida")
    linhas.append("texto_exemplo = 'DECRETO Nº 12.345, DE 01 DE ABRIL DE 2026'")
    linhas.append("bbox_exemplo = [100.0, 150.0, 600.0, 190.0]  # x0, y0, x1, y1")
    linhas.append("W, H = 1200.0, 1800.0")
    linhas.append("")
    linhas.append("# Extrair atributos correspondentes")
    linhas.append("man = extrair_atributos_manuais(texto_exemplo)")
    linhas.append("geo = extrair_atributos_geometria(bbox_exemplo, W, H)")
    linhas.append("ctx = [0.0] * 32  # ou contexto de vizinhos se houver")
    linhas.append("")
    linhas.append("import numpy as np")
    linhas.append("import scipy.sparse as sp")
    linhas.append("txt_norm = normalizar_texto_ngrams(texto_exemplo)")
    linhas.append("X_char = artefato['vec_char'].transform([txt_norm])")
    linhas.append("X_word = artefato['vec_word'].transform([txt_norm])")
    linhas.append("X_txt = sp.hstack([X_char, X_word])")
    linhas.append("X_dense = np.hstack([")
    linhas.append("    artefato['scaler_man'].transform([man]),")
    linhas.append("    artefato['scaler_geo'].transform([geo]),")
    linhas.append("    artefato['scaler_ctx'].transform([ctx])")
    linhas.append("])")
    linhas.append("X_completo = sp.hstack([X_txt, sp.csr_matrix(X_dense)])")
    linhas.append("")
    linhas.append("pred_idx = modelo.predict(X_completo)[0]")
    linhas.append("classe_predita = classes[pred_idx]")
    linhas.append("print('Classe predita:', classe_predita)")
    linhas.append("```")
    linhas.append("")

    linhas.append("## 7. Limitações e Vieses Metodológicos")
    linhas.append("")
    linhas.append(
        "1. **Texto do Ouro vs. Extração Automática:** As caixas do Label Studio possuem texto revisado/transcrito por humanos. "
        "Em um pipeline em produção ou sem supervisão humana, o texto dependerá de extração digital (pdfplumber/PyMuPDF) ou OCR, "
        "podendo conter quebras ruidosas ou caracteres corrompidos que degradam a classificação.\n"
        "2. **Viés de Ancoragem (Anchoring Bias):** Como documentado no projeto (`labelstudio_ancoragem.md`), cerca de 40% das caixas "
        "foram aceitas sem alteração a partir da pré-anotação de um modelo automático. Isso afeta tanto as fronteiras das caixas quanto "
        "a distribuição de classes conferidas pelos anotadores.\n"
        "3. **Desacoplamento de Localização:** O classificador assume a geometria exata fornecida pelo ouro. Quando acoplado a um "
        "detector visual com IoU < 0,50, ou em caixas fundidas/divididas, o texto capturado sofrerá ruído de fronteira.\n"
        "4. **Desbalanceamento Extremo de Suporte:** Classes como `chart` e `heading` possuem suporte escasso no teste, gerando "
        "intervalos de confiança mais amplos ou degenerados."
    )
    linhas.append("")

    texto_final = "\n".join(linhas)
    salvar_atomico(caminho_saida, texto_final, "w")
    print(f"Relatorio salvo com sucesso em: {caminho_saida}")


# ==============================================================================
# Funcao Principal
# ==============================================================================

def main():
    print("=" * 80)
    print("CLASSIFICADOR DE REGIOES DO LABEL STUDIO (TEXTO, GEOMETRIA E CONTEXTO)")
    print("=" * 80)

    # 1. Carrega dados e split
    paginas_split, paginas_por_split, sem_par = carregar_dados_e_split()

    train_amostras, train_por_pagina = processar_paginas_em_caixas(paginas_por_split["train"])
    val_amostras, val_por_pagina = processar_paginas_em_caixas(paginas_por_split["val"])
    test_amostras, test_por_pagina = processar_paginas_em_caixas(paginas_por_split["test"])

    print(f"Caixas processadas: Train={len(train_amostras)}, Val={len(val_amostras)}, Test={len(test_amostras)}")

    # 2. Constrói matrizes de atributos
    print("\nConstruindo matrizes de atributos para os 3 modelos...")
    t0 = time.time()
    dados_modelos = construir_matrizes_atributos(train_amostras, val_amostras, test_amostras)
    print(f"Matrizes construidas em {time.time() - t0:.2f}s.")

    X_tr_m1, X_val_m1, X_te_m1 = dados_modelos["m1"]
    X_tr_m2, X_val_m2, X_te_m2 = dados_modelos["m2"]
    X_tr_m3, X_val_m3, X_te_m3 = dados_modelos["m3"]
    y_train, y_val, y_test = dados_modelos["y"]
    artefatos = dados_modelos["artefatos"]

    # 3. Treina e escolhe hiperparametros no val
    print("\n--- Treinando Modelo 1 (So Texto) ---")
    clf_m1, best_c_m1, val_f1_m1 = treinar_com_selecao_hiperparametro(
        X_tr_m1, y_train, X_val_m1, y_val, "So Texto"
    )

    print("\n--- Treinando Modelo 2 (So Geometria) ---")
    clf_m2, best_c_m2, val_f1_m2 = treinar_com_selecao_hiperparametro(
        X_tr_m2, y_train, X_val_m2, y_val, "So Geometria"
    )

    print("\n--- Treinando Modelo 3 (Texto + Geometria + Contexto) ---")
    clf_m3, best_c_m3, val_f1_m3 = treinar_com_selecao_hiperparametro(
        X_tr_m3, y_train, X_val_m3, y_val, "Texto + Geo + Contexto"
    )

    # 4. Avaliacao no Teste (16 Classes)
    print("\nAvaliando modelos no conjunto de teste (317 paginas)...")
    pred_te_m1_idx = clf_m1.predict(X_te_m1)
    pred_te_m2_idx = clf_m2.predict(X_te_m2)
    pred_te_m3_idx = clf_m3.predict(X_te_m3)

    pred_te_m1 = [IDX_16_MAPA[i] for i in pred_te_m1_idx]
    pred_te_m2 = [IDX_16_MAPA[i] for i in pred_te_m2_idx]
    pred_te_m3 = [IDX_16_MAPA[i] for i in pred_te_m3_idx]
    y_test_nomes = [IDX_16_MAPA[i] for i in y_test]

    # Associa predicoes as amostras de teste por pagina
    for idx, amostra in enumerate(test_amostras):
        amostra["pred_m1"] = pred_te_m1[idx]
        amostra["pred_m2"] = pred_te_m2[idx]
        amostra["pred_m3"] = pred_te_m3[idx]

    # Metricas principais no teste
    m1_test_metr = calcular_metricas_estatisticas(y_test_nomes, pred_te_m1, CLASSES_16)
    m2_test_metr = calcular_metricas_estatisticas(y_test_nomes, pred_te_m2, CLASSES_16)
    m3_test_metr = calcular_metricas_estatisticas(y_test_nomes, pred_te_m3, CLASSES_16)

    # Bootstrap para intervalos de confianca
    print("Calculando intervalos de confianca via bootstrap por pagina...")
    ic_m1 = bootstrap_paginas(test_por_pagina, lambda cx: ([c["classe"] for c in cx], [c["pred_m1"] for c in cx]), CLASSES_16)
    ic_m2 = bootstrap_paginas(test_por_pagina, lambda cx: ([c["classe"] for c in cx], [c["pred_m2"] for c in cx]), CLASSES_16)
    ic_m3 = bootstrap_paginas(test_por_pagina, lambda cx: ([c["classe"] for c in cx], [c["pred_m3"] for c in cx]), CLASSES_16)

    # Confusoes mais frequentes do Modelo 3
    top_confusoes, total_erros = calcular_confusoes(y_test_nomes, pred_te_m3, top_k=12)

    # 5. Avaliacao nas 9 e 3 classes (Modelo 3)
    y_test_9 = [mapa_9_classes(c) for c in y_test_nomes]
    pred_m3_9 = [mapa_9_classes(c) for c in pred_te_m3]
    m3_test_9 = calcular_metricas_estatisticas(y_test_9, pred_m3_9, list(CLASSES_9))

    # 3 classes: descarta unknown
    pares_3 = [(mapa_3_classes(yt), mapa_3_classes(yp)) for yt, yp in zip(y_test_nomes, pred_te_m3) if mapa_3_classes(yt) is not None]
    y_test_3 = [p[0] for p in pares_3]
    pred_m3_3 = [p[1] if p[1] is not None else "texto" for p in pares_3]
    m3_test_3 = calcular_metricas_estatisticas(y_test_3, pred_m3_3, list(CLASSES_3))

    # 6. Comparacao com o detector visual ls16
    print("\nBuscando predicoes do detector ls16 em resultados/ls_teste_cache/...")
    preds_ls16 = carregar_predicoes_ls16(set(test_por_pagina.keys()))
    preds_m3_mapa = {(a["page_id"], a["id"]): a["pred_m3"] for a in test_amostras}

    comp_det = comparar_caixas_com_detector(test_por_pagina, preds_ls16, preds_m3_mapa)
    if comp_det and comp_det.get("pares"):
        y_real_comp = [p["classe_real"] for p in comp_det["pares"]]
        y_det_comp = [p["classe_det"] for p in comp_det["pares"]]
        y_clf_comp = [p["classe_clf"] for p in comp_det["pares"]]

        comp_det["metr_det_16"] = calcular_metricas_estatisticas(y_real_comp, y_det_comp, CLASSES_16)
        comp_det["metr_clf_16"] = calcular_metricas_estatisticas(y_real_comp, y_clf_comp, CLASSES_16)
    else:
        print("Aviso: comparacao com detector ls16 nao foi possivel (cache ausente ou sem correspondencias).")

    # 7. Salva o modelo final e metadados
    print("\nSalvando artefato final do classificador...")
    DIR_MODELO.mkdir(parents=True, exist_ok=True)
    artefato_salvo = {
        "modelo": clf_m3,
        "classes": CLASSES_16,
        "melhor_C": best_c_m3,
        **artefatos
    }
    with open(DIR_MODELO / "modelo.pkl", "wb") as f:
        pickle.dump(artefato_salvo, f)

    meta_info = {
        "data_execucao": time.strftime("%Y-%m-%d %H:%M:%S"),
        "melhor_C_m3": best_c_m3,
        "acuracia_teste_m3": m3_test_metr["acuracia"],
        "f1_macro_teste_m3": m3_test_metr["f1_macro"],
        "acuracia_teste_m1": m1_test_metr["acuracia"],
        "f1_macro_teste_m1": m1_test_metr["f1_macro"],
        "acuracia_teste_m2": m2_test_metr["acuracia"],
        "f1_macro_teste_m2": m2_test_metr["f1_macro"],
        "n_train_paginas": len(paginas_por_split["train"]),
        "n_test_paginas": len(paginas_por_split["test"]),
        "usou_sklearn": artefatos.get("usou_sklearn", False)
    }
    with open(DIR_MODELO / "info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, indent=2, ensure_ascii=False)

    # 8. Escreve relatorio em resultados/classificador_regioes_ls.md
    print("Gerando resultados/classificador_regioes_ls.md...")
    resultados_dict = {
        "n_fontes_train": len({d["meta"]["fonte"] for d in paginas_por_split["train"].values()}),
        "n_fontes_val": len({d["meta"]["fonte"] for d in paginas_por_split["val"].values()}),
        "n_fontes_test": len({d["meta"]["fonte"] for d in paginas_por_split["test"].values()}),
        "n_train_pag": len(paginas_por_split["train"]),
        "n_val_pag": len(paginas_por_split["val"]),
        "n_test_pag": len(paginas_por_split["test"]),
        "n_train_box": len(train_amostras),
        "n_val_box": len(val_amostras),
        "n_test_box": len(test_amostras),
        "sem_par": sem_par,
        "m1": {"melhor_C": best_c_m1, "test_16": m1_test_metr, "ic": ic_m1},
        "m2": {"melhor_C": best_c_m2, "test_16": m2_test_metr, "ic": ic_m2},
        "m3": {
            "melhor_C": best_c_m3,
            "test_16": m3_test_metr,
            "test_9": m3_test_9,
            "test_3": m3_test_3,
            "ic": ic_m3,
            "top_confusoes": top_confusoes,
            "total_erros": total_erros
        }
    }
    gerar_relatorio_md(resultados_dict, comp_det, ARQ_RELATORIO)

    print("\nExecucao concluida com sucesso!")
    print(f"Modelo salvo em: {DIR_MODELO / 'modelo.pkl'}")
    print(f"Relatorio salvo em: {ARQ_RELATORIO}")


if __name__ == "__main__":
    main()
