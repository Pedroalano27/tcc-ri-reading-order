"""
LLM generativa como ordenadora de blocos, zero-shot, via Ollama (local).

A LLM recebe os blocos na MESMA ordem embaralhada do protocolo, rotulados
B1..Bn na ordem de entrada (os rotulos nao carregam informacao de ordem),
com a caixa normalizada 0-1000 e o inicio do texto. Deve devolver um JSON
com a ordem de leitura.

Mede-se tambem a CONFIABILIDADE DE FORMATO: com que frequencia a LLM devolve
uma permutacao valida (todos os ids, sem repeticao, sem inventar ids). Saidas
invalidas sao reparadas (ids faltantes vao para o fim) e sinalizadas.

Uso:
    python src/eval/llm_ordem.py --modelo llava:7b --paginas 40 --max-blocos 30
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.eval.protocolo import carregar_splits, carregar_particao, ordem_entrada, salvar_predicoes  # noqa: E402
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="llava:7b")
    ap.add_argument("--paginas", type=int, default=40)
    ap.add_argument("--max-blocos", type=int, default=30)
    a = ap.parse_args()
    import ollama

    splits = carregar_splits()
    ref = splits["referencia"]
    teste = [p for p in carregar_particao("teste") if len(p["bounding_boxes"]) <= a.max_blocos]
    por_uf = {}
    for p in teste:
        por_uf.setdefault(p["uf"], []).append(p)
    rng = random.Random(42)
    cota = math.ceil(a.paginas / max(1, len(por_uf)))
    amostra = []
    for uf in sorted(por_uf):
        amostra += rng.sample(por_uf[uf], min(cota, len(por_uf[uf])))
    amostra = amostra[: a.paginas]
    print(f"[*] {a.modelo}: {len(amostra)} paginas de teste (<= {a.max_blocos} blocos), "
          f"{len(por_uf)} UFs", flush=True)

    ollama.chat(model=a.modelo, messages=[{"role": "user", "content": "ok"}],
                options={"num_predict": 1})          # carrega o modelo na GPU (nao cronometrado)

    linhas = []
    for k, p in enumerate(amostra, 1):
        o = ordem_entrada(p)
        rotulo_para_id = {f"B{j + 1}": p["bounding_boxes"][bi]["id"] for j, bi in enumerate(o)}
        n = len(o)
        t0 = time.perf_counter()
        try:
            r = ollama.chat(model=a.modelo, format="json",
                            messages=[{"role": "system", "content": SISTEMA},
                                      {"role": "user", "content": montar_prompt(p, o)}],
                            options={"temperature": 0, "seed": 42, "num_ctx": 8192,
                                     "num_predict": 12 * n + 64})
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
        linhas.append({"page_id": p["page_id"], "ordem_pred": pred, "tempo_ms": round(dt, 1),
                       "permutacao_valida": valida, "n_rotulos_devolvidos": len(rotulos),
                       "n_unicos_validos": len(set(ids_brutos)), "n_blocos": n, "erro": erro,
                       "resposta_bruta": texto[:2000], **info})
        tau = kendall_tau(pred, p["ordens"][ref])
        print(f"  {k}/{len(amostra)} {p['uf'][15:]:<24} n={n:<3} {dt / 1000:5.1f}s "
              f"valida={'sim' if valida else 'NAO'} tau={tau:+.2f}", flush=True)

    try:    # descarrega o modelo da GPU para liberar VRAM para os proximos experimentos
        ollama.chat(model=a.modelo, messages=[{"role": "user", "content": "ok"}],
                    options={"num_predict": 1}, keep_alive=0)
    except Exception:
        pass

    caminho = salvar_predicoes("llm_" + a.modelo.replace(":", "_").replace(".", "_"), linhas)
    validas = sum(l["permutacao_valida"] for l in linhas)
    print(f"\n[OK] {len(linhas)} paginas | permutacoes validas: {validas}/{len(linhas)} | "
          f"{sum(l['tempo_ms'] for l in linhas) / len(linhas) / 1000:.1f} s/pagina -> {caminho}")


if __name__ == "__main__":
    main()
