"""
LLM generativa como ordenadora de blocos, via Ollama (local ou no Kaggle).

A LLM recebe os blocos na MESMA ordem embaralhada do protocolo, rotulados
B1..Bn na ordem de entrada (os rotulos nao carregam informacao de ordem),
com a caixa normalizada 0-1000 e o inicio do texto. Deve devolver um JSON
com a ordem de leitura.

Modos:
  zero-shot   so a instrucao (padrao)
  few-shot    --few-shot K: antes da pagina, K exemplos resolvidos tirados do TREINO
              (paginas pequenas, de preferencia com mais de uma coluna), como turnos
              usuario/assistente. Nunca usa paginas de teste.

Mede-se tambem a CONFIABILIDADE DE FORMATO: com que frequencia a LLM devolve
uma permutacao valida (todos os ids, sem repeticao, sem inventar ids). Saidas
invalidas sao reparadas (ids faltantes vao para o fim) e sinalizadas.

Cada pagina e gravada assim que termina (<saida>.parcial). Com --retomar, uma
execucao interrompida (ex.: sessao do Kaggle que caiu) continua de onde parou.
Cada execucao registra modelo, GPU e tempos em execucoes_llm.jsonl.

Uso:
    python src/eval/llm_ordem.py --modelo llava:7b --paginas 20 --max-blocos 25
    python src/eval/llm_ordem.py --modelo qwen2.5:14b --few-shot 2            (teste inteiro)
    python src/eval/llm_ordem.py --modelo qwen2.5:14b --particao golden:golden_v1
"""
from __future__ import annotations

import os
import re
import sys
import json
import math
import time
import random
import argparse
import subprocess
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import (carregar_splits, carregar_particao, ordem_entrada,  # noqa: E402
                                DIR_RESULTADOS, RAIZ_PROJETO)
from src.eval.metrics import validar_permutacao, kendall_tau  # noqa: E402

SISTEMA = ("Voce e um sistema de analise de layout de documentos. Sua tarefa e determinar "
           "a ordem de leitura humana de blocos de texto de uma pagina de Diario Oficial.")

INSTRUCAO = """Os blocos abaixo foram extraidos de uma pagina e estao em ORDEM ALEATORIA.
Cada linha traz: o identificador do bloco, sua caixa [x0,y0,x1,y1] em coordenadas
normalizadas de 0 a 1000 (origem no canto superior esquerdo; y cresce para baixo)
e o inicio do texto.

Regras de leitura: cabecalhos no topo vem primeiro; em paginas com varias colunas,
le-se a coluna da esquerda inteira, de cima para baixo, e depois a proxima coluna;
titulos que atravessam a largura da pagina separam secoes; rodapes vem por ultimo.

Responda SOMENTE com um objeto JSON no formato {{"ordem": ["B3", "B1", ...]}},
contendo cada identificador exatamente uma vez.

Blocos:
{blocos}"""


def normalizar(bbox, W, H):
    x0, y0, x1, y1 = bbox
    f = lambda v, d: max(0, min(1000, int(round(1000 * v / d))))
    return f(x0, W), f(y0, H), f(x1, W), f(y1, H)


def montar_prompt(p, ordem):
    W, H = p["dimensions"]["width"], p["dimensions"]["height"]
    linhas = []
    for j, bi in enumerate(ordem):
        c = p["bounding_boxes"][bi]
        x0, y0, x1, y1 = normalizar(c["bbox"], W, H)
        trecho = " ".join(c["text"].split()[:12]).replace('"', "'")
        linhas.append(f'B{j + 1} [{x0},{y0},{x1},{y1}] "{trecho}"')
    return INSTRUCAO.format(blocos="\n".join(linhas))


def interpretar(texto):
    """Extrai a lista de rotulos da resposta, tolerando formatos imperfeitos."""
    try:
        obj = json.loads(texto)
        if isinstance(obj, dict):
            lista = obj.get("ordem") or next((v for v in obj.values() if isinstance(v, list)), [])
        elif isinstance(obj, list):
            lista = obj
        else:
            lista = []
    except Exception:
        lista = re.findall(r"B\d+", texto)
    saida = []
    for x in lista:
        m = re.search(r"\d+", str(x))
        if m:
            saida.append(f"B{int(m.group())}")
    return saida


def carregar_paginas(particao):
    """teste | golden:<lote> | caminho de um .jsonl de paginas"""
    if particao == "teste":
        return carregar_particao("teste")
    if particao.startswith("golden:"):
        caminho = os.path.join(RAIZ_PROJETO, "data", "golden", particao.split(":", 1)[1], "tarefas.jsonl")
    else:
        caminho = particao
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def escolher_exemplos(k, semente=7):
    """K paginas pequenas do TREINO para o few-shot, preferindo as de 2+ colunas."""
    treino = [p for p in carregar_particao("treino") if 6 <= len(p["bounding_boxes"]) <= 16]
    multi = [p for p in treino if p["stats"]["n_colunas"] >= 2]
    pool = sorted(multi if len(multi) >= k else treino, key=lambda p: p["page_id"])
    random.Random(semente).shuffle(pool)
    return pool[:k]


def turnos_exemplo(p, ref):
    o = ordem_entrada(p)
    rotulo = {p["bounding_boxes"][bi]["id"]: f"B{j + 1}" for j, bi in enumerate(o)}
    resposta = json.dumps({"ordem": [rotulo[i] for i in p["ordens"][ref]]})
    return [{"role": "user", "content": montar_prompt(p, o)}, {"role": "assistant", "content": resposta}]


def nome_gpu():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=10)
        return " + ".join(x.strip() for x in r.stdout.splitlines() if x.strip()) or None
    except Exception:
        return None


def versao_ollama(host):
    try:
        with urllib.request.urlopen((host or "http://127.0.0.1:11434").rstrip("/") + "/api/version", timeout=5) as r:
            return json.loads(r.read()).get("version")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", default="llava:7b")
    ap.add_argument("--particao", default="teste", help="teste | golden:<lote> | caminho de .jsonl")
    ap.add_argument("--paginas", type=int, default=0, help="amostra N paginas, equilibrando veiculos (0 = todas)")
    ap.add_argument("--max-blocos", type=int, default=200)
    ap.add_argument("--few-shot", type=int, default=0, help="quantos exemplos resolvidos do treino vao no prompt")
    ap.add_argument("--num-ctx", type=int, default=0, help="janela de contexto (0 = calcula pela maior pagina)")
    ap.add_argument("--sem-pensar", action="store_true", help="desliga o modo de raciocinio (qwen3, deepseek-r1)")
    ap.add_argument("--timeout", type=float, default=900, help="segundos maximos por pagina")
    ap.add_argument("--dir-saida", help="pasta das predicoes (padrao: resultados/ ou resultados/golden/<lote>/)")
    ap.add_argument("--retomar", action="store_true", help="continua uma execucao interrompida")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST"), help="endereco do servidor Ollama")
    a = ap.parse_args()
    import ollama

    splits = carregar_splits()
    ref = splits["referencia"]
    paginas = [p for p in carregar_paginas(a.particao) if len(p["bounding_boxes"]) <= a.max_blocos]
    if a.paginas:
        por_uf = {}
        for p in paginas:
            por_uf.setdefault(p["uf"], []).append(p)
        rng = random.Random(42)
        cota = math.ceil(a.paginas / max(1, len(por_uf)))
        amostra = []
        for uf in sorted(por_uf):
            amostra += rng.sample(por_uf[uf], min(cota, len(por_uf[uf])))
        paginas = amostra[: a.paginas]
    if not paginas:
        sys.exit("[ERRO] nenhuma pagina selecionada")

    exemplos = [m for p in escolher_exemplos(a.few_shot) for m in turnos_exemplo(p, ref)] if a.few_shot else []

    # Uma janela de contexto so para a execucao inteira: mudar num_ctx faz o Ollama recarregar o modelo.
    if a.num_ctx:
        num_ctx = a.num_ctx
    else:
        fixos = len(SISTEMA) + sum(len(m["content"]) for m in exemplos)
        maior = max((fixos + len(montar_prompt(p, ordem_entrada(p)))) / 2.8 + 12 * len(p["bounding_boxes"]) + 64
                    for p in paginas)
        num_ctx = int(min(32768, max(4096, math.ceil(maior * 1.15 / 2048) * 2048)))

    metodo = "llm_" + re.sub(r"[^A-Za-z0-9]+", "_", a.modelo).strip("_") + (f"_fs{a.few_shot}" if a.few_shot else "")
    if a.dir_saida:
        dir_saida = a.dir_saida
    elif a.particao == "teste":
        dir_saida = DIR_RESULTADOS
    elif a.particao.startswith("golden:"):
        dir_saida = os.path.join(DIR_RESULTADOS, "golden", a.particao.split(":", 1)[1])
    else:
        dir_saida = os.path.join(DIR_RESULTADOS, "outras")
    os.makedirs(dir_saida, exist_ok=True)
    final = os.path.join(dir_saida, f"pred_{metodo}.jsonl")
    parcial = final + ".parcial"

    feitas = {}
    if a.retomar and os.path.exists(parcial):
        with open(parcial, encoding="utf-8") as f:
            for l in f:
                try:
                    d = json.loads(l)
                    feitas[d["page_id"]] = d
                except (json.JSONDecodeError, KeyError):
                    pass
    elif os.path.exists(parcial):
        os.remove(parcial)

    print(f"[*] {a.modelo} | {'few-shot ' + str(a.few_shot) if a.few_shot else 'zero-shot'} | "
          f"{len(paginas)} paginas ({a.particao}, <= {a.max_blocos} blocos) | num_ctx {num_ctx} | "
          f"GPU: {nome_gpu()}" + (f" | retomando: {len(feitas)} ja feitas" if feitas else ""), flush=True)

    cliente = ollama.Client(host=a.host, timeout=a.timeout)
    opcoes = {"temperature": 0, "seed": 42, "num_ctx": num_ctx}
    extra = {"think": False} if a.sem_pensar else {}

    def conversar(mensagens, **kw):
        nonlocal extra
        try:
            return cliente.chat(model=a.modelo, messages=mensagens, **extra, **kw)
        except Exception as e:
            # cliente antigo sem o parametro think, ou modelo que nao aceita o controle de raciocinio
            if extra and (isinstance(e, TypeError) or "think" in str(e).lower()):
                extra = {}
                return cliente.chat(model=a.modelo, messages=mensagens, **kw)
            raise

    t0 = time.perf_counter()
    conversar([{"role": "user", "content": "ok"}], options={**opcoes, "num_predict": 1})   # carga, nao cronometrada
    seg_carga = time.perf_counter() - t0

    t_ini = time.perf_counter()
    with open(parcial, "a", encoding="utf-8") as saida:
        for k, p in enumerate(paginas, 1):
            if p["page_id"] in feitas:
                continue
            o = ordem_entrada(p)
            rotulo_para_id = {f"B{j + 1}": p["bounding_boxes"][bi]["id"] for j, bi in enumerate(o)}
            n = len(o)
            mensagens = [{"role": "system", "content": SISTEMA}, *exemplos,
                         {"role": "user", "content": montar_prompt(p, o)}]
            t0 = time.perf_counter()
            try:
                r = conversar(mensagens, format="json", options={**opcoes, "num_predict": 12 * n + 64})
                texto = r["message"]["content"]
                info = {"tokens_entrada": r.get("prompt_eval_count"), "tokens_saida": r.get("eval_count"),
                        "tokens_por_s": (r.get("eval_count") or 0) / max(1e-9, (r.get("eval_duration") or 0) / 1e9)}
                erro = None
            except Exception as e:
                texto, info, erro = "", {}, f"{type(e).__name__}: {e}"
            dt = (time.perf_counter() - t0) * 1000

            rotulos = interpretar(texto)
            ids_brutos = [rotulo_para_id[x] for x in rotulos if x in rotulo_para_id]
            ids_validos = [p["bounding_boxes"][bi]["id"] for bi in o]
            pred = validar_permutacao(ids_brutos, ids_validos)
            valida = (len(rotulos) == n and len(set(rotulos)) == n and all(x in rotulo_para_id for x in rotulos))
            linha = {"page_id": p["page_id"], "ordem_pred": pred, "tempo_ms": round(dt, 1),
                     "modelo": a.modelo, "few_shot": a.few_shot,
                     "permutacao_valida": valida, "n_rotulos_devolvidos": len(rotulos),
                     "n_unicos_validos": len(set(ids_brutos)), "n_blocos": n, "erro": erro,
                     "resposta_bruta": texto[:2000], **info}
            saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
            saida.flush()
            feitas[p["page_id"]] = linha
            tau = kendall_tau(pred, p["ordens"][ref])
            print(f"  {k}/{len(paginas)} {p['uf'][15:]:<24} n={n:<3} {dt / 1000:6.1f}s "
                  f"valida={'sim' if valida else 'NAO'} tau={tau:+.2f}", flush=True)

    try:    # descarrega o modelo da GPU para liberar memoria para o proximo
        cliente.chat(model=a.modelo, messages=[{"role": "user", "content": "ok"}],
                     options={"num_predict": 1}, keep_alive=0)
    except Exception:
        pass

    linhas = [feitas[p["page_id"]] for p in paginas if p["page_id"] in feitas]
    with open(final, "w", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    os.remove(parcial)

    validas = sum(l["permutacao_valida"] for l in linhas)
    media_s = sum(l["tempo_ms"] for l in linhas) / len(linhas) / 1000
    with open(os.path.join(dir_saida, "execucoes_llm.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "metodo": metodo, "modelo": a.modelo, "few_shot": a.few_shot, "particao": a.particao,
            "paginas": len(linhas), "max_blocos": a.max_blocos, "num_ctx": num_ctx, "sem_pensar": a.sem_pensar,
            "gpu": nome_gpu(), "ollama": versao_ollama(a.host), "segundos_carga_modelo": round(seg_carga, 1),
            "segundos_execucao": round(time.perf_counter() - t_ini, 1), "prop_permutacoes_validas": validas / len(linhas),
            "segundos_por_pagina": round(media_s, 2), "data": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, ensure_ascii=False) + "\n")
    print(f"\n[OK] {len(linhas)} paginas | permutacoes validas: {validas}/{len(linhas)} | "
          f"{media_s:.1f} s/pagina -> {final}")


if __name__ == "__main__":
    main()
