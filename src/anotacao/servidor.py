"""
Servidor local das ferramentas de anotacao.

    venv\\Scripts\\python.exe src\\anotacao\\servidor.py             (ordem de leitura, Golden)
    venv\\Scripts\\python.exe src\\anotacao\\servidor.py --diamond   (caixas e classes, Diamond)

Golden: serve ferramenta.html e os lotes de data/golden/, e grava as anotacoes em
data/golden/<lote>/anotacoes.jsonl. Diamond: serve diamond.html (em /diamond) e os lotes de
data/diamond/, e grava em data/diamond/<lote>/anotacoes.jsonl. Nos dois, uma linha por pagina e
anotador, valendo a mais recente; cada edicao fica salva como rascunho em segundos, entao fechar
o navegador nao perde trabalho. So usa a biblioteca padrao do Python.
"""
from __future__ import annotations

import os
import re
import json
import time
import argparse
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DIR_GOLDEN = os.path.join(RAIZ, "data", "golden")
DIR_DIAMOND = os.path.join(RAIZ, "data", "diamond")
RE_LOTE = re.compile(r"^[A-Za-z0-9_-]+$")
RE_IMG = re.compile(r"^[A-Za-z0-9_-]+\.(jpg|jpeg|png)$")
RE_ALFANUM = re.compile(r"[0-9A-Za-zÀ-ÿ]")
STATUS = {"rascunho", "concluida", "pulada"}
CLASSES = ["titulo", "texto", "lista", "tabela", "assinatura", "cabecalho", "rodape", "figura", "outro"]
TRAVA = threading.Lock()


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def gravar_anotacao(caminho, limpo):
    """Troca a linha da mesma pagina e anotador (ou acrescenta), gravando por arquivo temporario."""
    with TRAVA:
        regs = [r for r in ler_jsonl(caminho)
                if not (r["page_id"] == limpo["page_id"] and r["anotador"] == limpo["anotador"])]
        regs.append(limpo)
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in regs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, caminho)


def tarefas(lote):
    return ler_jsonl(os.path.join(DIR_GOLDEN, lote, "tarefas.jsonl"))


def listar_lotes():
    saida = []
    if os.path.isdir(DIR_GOLDEN):
        for nome in sorted(os.listdir(DIR_GOLDEN)):
            if RE_LOTE.match(nome) and os.path.exists(os.path.join(DIR_GOLDEN, nome, "tarefas.jsonl")):
                anot = ler_jsonl(os.path.join(DIR_GOLDEN, nome, "anotacoes.jsonl"))
                saida.append({"nome": nome, "paginas": len(tarefas(nome)),
                              "concluidas": sum(1 for a in anot if a.get("status") == "concluida")})
    return saida


def salvar(lote, reg):
    t = {x["page_id"]: x for x in tarefas(lote)}.get(reg.get("page_id"))
    if t is None:
        raise ValueError("pagina desconhecida neste lote")
    anotador = str(reg.get("anotador", "")).strip()[:40]
    if not anotador:
        raise ValueError("escreva seu nome no campo Anotador antes de anotar")
    status = reg.get("status")
    if status not in STATUS:
        raise ValueError("status invalido")
    ids = [c["id"] for c in t["bounding_boxes"]]
    ordem = [str(x) for x in reg.get("ordem", [])]
    if len(set(ordem)) != len(ordem) or not set(ordem) <= set(ids):
        raise ValueError("ordem com blocos repetidos ou desconhecidos")
    if status == "concluida" and len(ordem) != len(ids):
        raise ValueError(f"faltam {len(ids) - len(ordem)} blocos para concluir a pagina")
    limpo = {"page_id": t["page_id"], "anotador": anotador, "status": status, "ordem": ordem,
             "flags": [str(x)[:40] for x in reg.get("flags", [])][:10],
             "nota": str(reg.get("nota", ""))[:2000],
             "motivo_pulo": str(reg.get("motivo_pulo", ""))[:200],
             "tempo_s": round(float(reg.get("tempo_s") or 0), 1),
             "n_blocos": len(ids), "salvo_em": time.strftime("%Y-%m-%dT%H:%M:%S")}
    gravar_anotacao(os.path.join(DIR_GOLDEN, lote, "anotacoes.jsonl"), limpo)
    return limpo


# ---------------------------------------------------------------- Diamond

def tarefas_diamond(lote):
    return ler_jsonl(os.path.join(DIR_DIAMOND, lote, "tarefas.jsonl"))


def listar_lotes_diamond():
    saida = []
    if os.path.isdir(DIR_DIAMOND):
        for nome in sorted(os.listdir(DIR_DIAMOND)):
            if RE_LOTE.match(nome) and os.path.exists(os.path.join(DIR_DIAMOND, nome, "tarefas.jsonl")):
                anot = ler_jsonl(os.path.join(DIR_DIAMOND, nome, "anotacoes.jsonl"))
                saida.append({"nome": nome, "paginas": len(tarefas_diamond(nome)),
                              "concluidas": sum(1 for a in anot if a.get("status") == "concluida")})
    return saida


def _mudancas(regioes, proposta):
    """Quanto da proposta sobreviveu: intacta (mesma caixa, 1 pt de tolerancia, e mesma classe),
    so caixa, so classe, caixa e classe; apagadas; criadas (sem origem na proposta)."""
    prop = {p["id"]: p for p in proposta}
    c = {"proposta": len(proposta), "intactas": 0, "caixa": 0, "classe": 0, "caixa_e_classe": 0,
         "apagadas": 0, "criadas": 0}
    usados = set()
    for r in regioes:
        p = prop.get(r.get("de")) if isinstance(r.get("de"), str) else None
        if p is None or p["id"] in usados:
            c["criadas"] += 1
            continue
        usados.add(p["id"])
        mudou_caixa = max(abs(a - b) for a, b in zip(r["bbox"], p["bbox"])) > 1.0
        mudou_classe = r["classe"] != p["classe"]
        c["caixa_e_classe" if mudou_caixa and mudou_classe else "caixa" if mudou_caixa
          else "classe" if mudou_classe else "intactas"] += 1
    c["apagadas"] = len(prop) - len(usados)
    return c


def salvar_diamond(lote, reg):
    t = {x["page_id"]: x for x in tarefas_diamond(lote)}.get(reg.get("page_id"))
    if t is None:
        raise ValueError("pagina desconhecida neste lote")
    anotador = str(reg.get("anotador", "")).strip()[:40]
    if not anotador:
        raise ValueError("escreva seu nome no campo Anotador antes de anotar")
    status = reg.get("status")
    if status not in STATUS:
        raise ValueError("status invalido")
    W, H = t["dimensions"]["width"], t["dimensions"]["height"]
    regioes, ids = [], set()
    for r in reg.get("regioes", [])[:2000]:
        rid = str(r.get("id", ""))[:20]
        if not rid or rid in ids:
            raise ValueError("regiao sem id ou com id repetido")
        ids.add(rid)
        if r.get("classe") not in CLASSES:
            raise ValueError(f"classe invalida: {r.get('classe')}")
        try:
            x0, y0, x1, y1 = (float(v) for v in r["bbox"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("caixa invalida")
        x0, x1 = sorted((min(max(x0, 0), W), min(max(x1, 0), W)))
        y0, y1 = sorted((min(max(y0, 0), H), min(max(y1, 0), H)))
        if x1 - x0 < 0.5 or y1 - y0 < 0.5:
            if status == "pulada":
                continue
            raise ValueError("caixa sem area")
        de = r.get("de")
        de = str(de)[:20] if isinstance(de, str) else [str(x)[:20] for x in de][:50] if isinstance(de, list) else None
        regioes.append({"id": rid, "classe": r["classe"], "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                        "de": de})
    # palavras (com letra ou digito) cujo centro nao cai em nenhuma regiao, e em mais de uma
    # regiao que nao seja figura: o que a ferramenta impede de concluir
    fora = duplas = 0
    for w in t["palavras"]:
        if not RE_ALFANUM.search(w[0]):
            continue
        cx, cy = (w[1] + w[3]) / 2, (w[2] + w[4]) / 2
        dentro = [r for r in regioes if r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3]]
        fora += not dentro
        duplas += sum(1 for r in dentro if r["classe"] != "figura") > 1
    if status == "concluida" and (fora or duplas):
        raise ValueError(f"para concluir: {fora} palavras sem caixa e {duplas} em duas caixas")
    limpo = {"page_id": t["page_id"], "anotador": anotador, "status": status, "regioes": regioes,
             "flags": [str(x)[:40] for x in reg.get("flags", [])][:10],
             "nota": str(reg.get("nota", ""))[:2000],
             "motivo_pulo": str(reg.get("motivo_pulo", ""))[:200],
             "tempo_s": round(float(reg.get("tempo_s") or 0), 1),
             "n_regioes": len(regioes), "palavras_sem_caixa": fora, "palavras_em_duas_caixas": duplas,
             "mudancas": _mudancas(regioes, t["proposta"]),
             "extrator_sha256": t.get("extrator_sha256"), "salvo_em": time.strftime("%Y-%m-%dT%H:%M:%S")}
    gravar_anotacao(os.path.join(DIR_DIAMOND, lote, "anotacoes.jsonl"), limpo)
    return limpo


class Tratador(BaseHTTPRequestHandler):
    def _enviar(self, dados, tipo, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(dados)

    def _json(self, obj, codigo=200):
        self._enviar(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", codigo)

    def do_GET(self):
        u = urlparse(self.path)
        partes = [p for p in u.path.split("/") if p]
        try:
            if not partes or partes == ["index.html"]:
                with open(os.path.join(AQUI, "ferramenta.html"), "rb") as f:
                    return self._enviar(f.read(), "text/html; charset=utf-8")
            if partes == ["diamond"]:
                with open(os.path.join(AQUI, "diamond.html"), "rb") as f:
                    return self._enviar(f.read(), "text/html; charset=utf-8")
            if partes == ["api", "diamond", "lotes"]:
                return self._json(listar_lotes_diamond())
            if partes == ["api", "diamond", "lote"]:
                nome = parse_qs(u.query).get("nome", [""])[0]
                if not RE_LOTE.match(nome):
                    return self._json({"erro": "lote invalido"}, 400)
                anot = ler_jsonl(os.path.join(DIR_DIAMOND, nome, "anotacoes.jsonl"))
                return self._json({"tarefas": tarefas_diamond(nome), "anotacoes": anot, "classes": CLASSES})
            if len(partes) == 3 and partes[0] == "img-diamond" and RE_LOTE.match(partes[1]) and RE_IMG.match(partes[2]):
                caminho = os.path.join(DIR_DIAMOND, partes[1], "img", partes[2])
                if os.path.exists(caminho):
                    with open(caminho, "rb") as f:
                        return self._enviar(f.read(), "image/jpeg")
            if partes == ["api", "lotes"]:
                return self._json(listar_lotes())
            if partes == ["api", "lote"]:
                nome = parse_qs(u.query).get("nome", [""])[0]
                if not RE_LOTE.match(nome):
                    return self._json({"erro": "lote invalido"}, 400)
                ts = [{k: v for k, v in t.items() if k != "ordens"} for t in tarefas(nome)]
                anot = ler_jsonl(os.path.join(DIR_GOLDEN, nome, "anotacoes.jsonl"))
                return self._json({"tarefas": ts, "anotacoes": anot})
            if len(partes) == 3 and partes[0] == "img" and RE_LOTE.match(partes[1]) and RE_IMG.match(partes[2]):
                caminho = os.path.join(DIR_GOLDEN, partes[1], "img", partes[2])
                if os.path.exists(caminho):
                    with open(caminho, "rb") as f:
                        tipo = "image/png" if caminho.endswith(".png") else "image/jpeg"
                        return self._enviar(f.read(), tipo)
            self._json({"erro": "nao encontrado"}, 404)
        except Exception as e:
            self._json({"erro": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        gravar = {"/api/anotacao": salvar, "/api/diamond/anotacao": salvar_diamond}.get(u.path)
        if gravar is None:
            return self._json({"erro": "nao encontrado"}, 404)
        nome = parse_qs(u.query).get("lote", [""])[0]
        if not RE_LOTE.match(nome):
            return self._json({"erro": "lote invalido"}, 400)
        try:
            n = int(self.headers.get("Content-Length", 0))
            reg = json.loads(self.rfile.read(n).decode("utf-8"))
            return self._json({"ok": True, "anotacao": gravar(nome, reg)})
        except ValueError as e:
            return self._json({"erro": str(e)}, 400)
        except Exception as e:
            return self._json({"erro": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, fmt, *args):     # silencia o log de cada requisicao
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=8770)
    ap.add_argument("--sem-navegador", action="store_true", help="nao abre o navegador sozinho")
    ap.add_argument("--diamond", action="store_true", help="abre a ferramenta de caixas e classes (Diamond)")
    a = ap.parse_args()
    if a.diamond and not listar_lotes_diamond():
        print("[!] Nenhum lote em data/diamond/. Crie um antes, por exemplo:\n"
              "    venv\\Scripts\\python.exe src\\anotacao\\preparar_diamond.py "
              "--lote diamond_piloto --de-lote _avaliacao/golden_v3 --n 20")
    elif not a.diamond and not listar_lotes():
        print("[!] Nenhum lote em data/golden/. Crie um antes, por exemplo:\n"
              "    venv\\Scripts\\python.exe src\\anotacao\\preparar_lote.py "
              "--lote golden_v1 --grupo silver:10 --grupo incerto:20")
    url = f"http://127.0.0.1:{a.porta}" + ("/diamond" if a.diamond else "")
    servidor = ThreadingHTTPServer(("127.0.0.1", a.porta), Tratador)
    print(f"[OK] ferramenta de anotacao em {url}  (Ctrl+C encerra; as anotacoes ja ficam salvas)")
    if not a.sem_navegador:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] servidor encerrado")


if __name__ == "__main__":
    main()
