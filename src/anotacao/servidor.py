"""
Servidor local da ferramenta de anotacao de ordem de leitura.

    venv\\Scripts\\python.exe src\\anotacao\\servidor.py        (abre http://127.0.0.1:8770)

Serve a ferramenta (ferramenta.html) e as paginas dos lotes em data/golden/, e grava
as anotacoes em data/golden/<lote>/anotacoes.jsonl: uma linha por pagina e anotador,
valendo a mais recente. Cada clique fica salvo como rascunho em segundos, entao fechar
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
RE_LOTE = re.compile(r"^[A-Za-z0-9_-]+$")
RE_IMG = re.compile(r"^[A-Za-z0-9_-]+\.(jpg|jpeg|png)$")
STATUS = {"rascunho", "concluida", "pulada"}
TRAVA = threading.Lock()


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


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
    caminho = os.path.join(DIR_GOLDEN, lote, "anotacoes.jsonl")
    with TRAVA:
        regs = [r for r in ler_jsonl(caminho)
                if not (r["page_id"] == limpo["page_id"] and r["anotador"] == anotador)]
        regs.append(limpo)
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in regs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, caminho)
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
        if u.path != "/api/anotacao":
            return self._json({"erro": "nao encontrado"}, 404)
        nome = parse_qs(u.query).get("lote", [""])[0]
        if not RE_LOTE.match(nome):
            return self._json({"erro": "lote invalido"}, 400)
        try:
            n = int(self.headers.get("Content-Length", 0))
            reg = json.loads(self.rfile.read(n).decode("utf-8"))
            return self._json({"ok": True, "anotacao": salvar(nome, reg)})
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
    a = ap.parse_args()
    if not listar_lotes():
        print("[!] Nenhum lote em data/golden/. Crie um antes, por exemplo:\n"
              "    venv\\Scripts\\python.exe src\\anotacao\\preparar_lote.py "
              "--lote golden_v1 --grupo silver:10 --grupo incerto:20")
    url = f"http://127.0.0.1:{a.porta}"
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
