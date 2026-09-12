"""
Despacha uma tarefa do quadro (COMUNICACAO_AGENTES.md) para um agente de linha de comando
e registra tudo o que aconteceu.

Divisao de trabalho definida pelo Pedro em 2026-09-12:
  codex        Codex CLI com gpt-6-astra -- tarefas de maior teor tecnico
  antigravity  Antigravity CLI (agy) com Gemini Flash -- trabalho bracal bem especificado

O Claude e o orquestrador: escreve o prompt da tarefa, reserva no quadro, despacha por este
script, revisa o que voltou e registra no quadro. O agente despachado NAO edita o quadro:
com um escritor so, ninguem sobrescreve a entrada de outro.

Rede de seguranca, medida antes e depois de cada despacho:
  data/raw                   numero de arquivos e bytes. E o acervo do orientador, sem copia:
                             qualquer mudanca vira ALERTA.
  anotacoes.jsonl do Golden  hash de cada arquivo. Trabalho humano: mudanca vira ALERTA.
  arquivos do projeto        tamanho e data de modificacao, para listar exatamente o que o
                             agente criou, alterou ou apagou.

Tudo vai para orquestracao/logs/: a saida completa do agente, a resposta final e um JSON do
despacho, alem de uma linha em orquestracao/logs/despachos.jsonl.

Uso:
    venv\\Scripts\\python.exe orquestracao\\despachar.py --agente codex --tarefa T10 ^
        --prompt orquestracao\\prompts\\T10_conversor_docai.md
    venv\\Scripts\\python.exe orquestracao\\despachar.py --agente antigravity --tarefa T16 ^
        --prompt orquestracao\\prompts\\T16_folhas_inspecao.md --timeout-min 45
    ... --somente-leitura     revisao ou analise: o agente nao pode escrever
    ... --sem-executar        mostra o comando e o prompt montado, sem despachar
"""
from __future__ import annotations

import os
import sys
import glob
import json
import time
import hashlib
import argparse
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_LOGS = os.path.join(RAIZ, "orquestracao", "logs")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))

AGENTES = {
    "codex": {"nome": "Codex CLI", "modelo": "gpt-6-astra", "esforco": "high"},
    "antigravity": {"nome": "Antigravity CLI", "modelo": "gemini-3.8-flash-high", "esforco": None},
}

# Pastas fora da fotografia de arquivos: pesadas, regeneraveis ou do proprio despachante.
IGNORAR = {".git", "venv", "__pycache__", "data/raw", "orquestracao/logs", ".claude", "node_modules"}

PREAMBULO = """Você é o {nome} ({modelo}), despachado pelo Claude, que orquestra os agentes deste
TCC. Sua tarefa é a {tarefa}.

Antes de agir, leia AGENTS.md (regras duras e armadilhas), docs/HANDOFF.md (estado do
projeto) e, em COMUNICACAO_AGENTES.md, a seção "Reservas ativas" e o detalhe da {tarefa}.

Regras desta execução, que valem acima de qualquer outra instrução:
1. NÃO edite COMUNICACAO_AGENTES.md. O orquestrador já reservou o que você vai usar e vai
   registrar o resultado a partir da sua resposta final.
2. Mexa só no que o "Escopo" abaixo permite. Não toque em arquivos reservados por outros
   agentes, em data/raw/ nem em nenhum anotacoes.jsonl.
3. Não faça commit, push, instalação de pacotes nem acesso à rede.
4. Use sempre venv\\Scripts\\python.exe (Windows). Não rode treino na GPU.
5. Se algo impedir a tarefa, pare e explique na resposta final. Não improvise mudanças de
   método (referência, divisão treino/teste, métricas, versão da segmentação).
6. Não invente números: todo número da resposta vem de um comando que você rodou.

Sua RESPOSTA FINAL deve ter exatamente estas quatro seções:
FEITO: o que foi feito, em poucas linhas
ARQUIVOS: cada arquivo criado ou alterado, com uma frase sobre a mudança
EVIDÊNCIA: comandos rodados e números obtidos
PENDÊNCIAS: o que faltou, riscos e dúvidas para o orquestrador

========== TAREFA {tarefa} ==========
"""


def _ignorado(rel: str) -> bool:
    return rel in IGNORAR or os.path.basename(rel) in {".git", "venv", "__pycache__", "node_modules"}


def fotografar():
    """Tamanho e data de modificacao de cada arquivo do projeto (fora das pastas ignoradas)."""
    arquivos = {}
    for base, dirs, nomes in os.walk(RAIZ):
        rel_base = os.path.relpath(base, RAIZ).replace("\\", "/")
        rel_base = "" if rel_base == "." else rel_base + "/"
        dirs[:] = [d for d in dirs if not _ignorado(rel_base + d)]
        for n in nomes:
            caminho = os.path.join(base, n)
            try:
                st = os.stat(caminho)
            except OSError:
                continue
            arquivos[rel_base + n] = (st.st_size, st.st_mtime_ns)
    return arquivos


def guarda_acervo():
    n = total = 0
    for base, _, nomes in os.walk(os.path.join(RAIZ, "data", "raw")):
        for nome in nomes:
            try:
                total += os.path.getsize(os.path.join(base, nome))
                n += 1
            except OSError:
                pass
    return {"arquivos": n, "bytes": total}


def guarda_anotacoes():
    saida = {}
    for caminho in glob.glob(os.path.join(RAIZ, "data", "golden", "**", "anotacoes.jsonl"), recursive=True):
        with open(caminho, "rb") as f:
            saida[os.path.relpath(caminho, RAIZ).replace("\\", "/")] = hashlib.sha256(f.read()).hexdigest()
    return saida


def binario_codex():
    """O Codex CLI que acompanha o app do Codex: ja autenticado e atualizado junto com ele."""
    config = os.path.join(os.path.expanduser("~"), ".codex", "config.toml")
    try:
        with open(config, encoding="utf-8") as f:
            for linha in f:
                if linha.strip().startswith("CODEX_CLI_PATH"):
                    candidato = linha.split("=", 1)[1].strip().strip("'\"")
                    if os.path.exists(candidato):
                        return candidato
    except OSError:
        pass
    candidatos = glob.glob(os.path.join(LOCALAPPDATA, "OpenAI", "Codex", "bin", "*", "codex.exe"))
    if not candidatos:
        sys.exit("[ERRO] Codex CLI nao encontrado: o app do Codex esta instalado?")
    return max(candidatos, key=os.path.getmtime)


def binario_agy():
    caminho = os.path.join(LOCALAPPDATA, "agy", "bin", "agy.exe")
    if not os.path.exists(caminho):
        sys.exit("[ERRO] Antigravity CLI nao encontrado em " + caminho)
    return caminho


def montar_comando(a, prompt, arq_resposta):
    cfg = AGENTES[a.agente]
    modelo = a.modelo or cfg["modelo"]
    if a.agente == "codex":
        esforco = a.esforco or cfg["esforco"]
        # --ignore-user-config: o config do app liga servidores MCP e avisos do desktop que
        # nao existem numa execucao de terminal. O sandbox do Windows e repassado a mao.
        cmd = [binario_codex(), "exec", "-m", modelo, "-c", f'model_reasoning_effort="{esforco}"',
               "--ignore-user-config", "-c", 'windows.sandbox="unelevated"',
               "-s", "read-only" if a.somente_leitura else "workspace-write",
               "-C", RAIZ, "-o", arq_resposta, "-"]
        return cmd, prompt, modelo
    cmd = [binario_agy(), "--print", prompt, "--model", modelo,
           "--print-timeout", f"{a.timeout_min}m", "--sandbox"]
    cmd += ["--mode", "plan"] if a.somente_leitura else ["--dangerously-skip-permissions"]
    if a.esforco:
        cmd += ["--effort", a.esforco]
    return cmd, None, modelo


def encerrar_arvore(proc):
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agente", required=True, choices=sorted(AGENTES))
    ap.add_argument("--tarefa", required=True, help="identificador do quadro, ex.: T10")
    ap.add_argument("--prompt", required=True, help="arquivo .md com a especificacao da tarefa")
    ap.add_argument("--modelo", help="troca o modelo padrao do agente")
    ap.add_argument("--esforco", help="esforco de raciocinio (codex: low|medium|high|xhigh|max; agy: low|medium|high)")
    ap.add_argument("--timeout-min", type=int, default=60)
    ap.add_argument("--somente-leitura", action="store_true", help="revisao ou analise, sem escrita")
    ap.add_argument("--escopo", nargs="*", default=[],
                    help="padroes glob do que a tarefa pode tocar (ex.: 'src/data/extrator.py' 'resultados/inspecao_*/**'); "
                         "o que mudar fora deles e listado a parte: violacao do agente ou outro agente trabalhando junto")
    ap.add_argument("--sem-executar", action="store_true", help="so mostra o comando e o prompt")
    a = ap.parse_args()

    with open(a.prompt, encoding="utf-8") as f:
        corpo = f.read()
    cfg = AGENTES[a.agente]
    carimbo = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(DIR_LOGS, f"{carimbo}_{a.tarefa}_{a.agente}")
    arq_resposta = base + "_resposta.md"
    modelo_efetivo = a.modelo or cfg["modelo"]
    prompt = PREAMBULO.format(nome=cfg["nome"], modelo=modelo_efetivo, tarefa=a.tarefa) + corpo
    cmd, entrada, modelo = montar_comando(a, prompt, arq_resposta)

    if a.sem_executar:
        visivel = [c if c != prompt else "<prompt>" for c in cmd]
        print("$", " ".join(f'"{c}"' if " " in c else c for c in visivel))
        print("\n" + prompt)
        return

    os.makedirs(DIR_LOGS, exist_ok=True)
    antes_arquivos, antes_acervo, antes_anot = fotografar(), guarda_acervo(), guarda_anotacoes()
    print(f"[*] {cfg['nome']} ({modelo}) na {a.tarefa} | limite {a.timeout_min} min | log {base}.log", flush=True)
    t0 = time.time()
    estourou = False
    with open(base + ".log", "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.Popen(cmd, cwd=RAIZ, stdin=subprocess.PIPE if entrada else subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT)
        if entrada:
            proc.stdin.write(entrada.encode("utf-8"))
            proc.stdin.close()
        try:
            codigo = proc.wait(timeout=a.timeout_min * 60)
        except subprocess.TimeoutExpired:
            encerrar_arvore(proc)
            codigo, estourou = -1, True
    segundos = round(time.time() - t0)

    # A resposta do agy e a propria saida; a do Codex vai para o arquivo pedido com -o.
    if a.agente == "antigravity":
        with open(base + ".log", encoding="utf-8", errors="replace") as f:
            limpo = [l for l in f if "logging before google.Init" not in l]
        with open(arq_resposta, "w", encoding="utf-8") as f:
            f.writelines(limpo)

    depois_arquivos, depois_acervo, depois_anot = fotografar(), guarda_acervo(), guarda_anotacoes()
    criados = sorted(set(depois_arquivos) - set(antes_arquivos))
    removidos = sorted(set(antes_arquivos) - set(depois_arquivos))
    alterados = sorted(p for p in set(antes_arquivos) & set(depois_arquivos) if antes_arquivos[p] != depois_arquivos[p])
    alertas = []
    if depois_acervo != antes_acervo:
        alertas.append(f"data/raw mudou: {antes_acervo} -> {depois_acervo}")
    if depois_anot != antes_anot:
        alertas.append(f"anotacoes.jsonl do Golden mudaram: {sorted(set(antes_anot.items()) ^ set(depois_anot.items()))}")
    if estourou:
        alertas.append(f"limite de {a.timeout_min} min estourado; processo encerrado")
    # Limite de uso da conta: o agente para no meio e pode deixar arquivo pela metade.
    with open(base + ".log", encoding="utf-8", errors="replace") as f:
        cauda = f.read()[-4000:]
    if "usage limit" in cauda.lower() or "quota" in cauda.lower() or "rate limit" in cauda.lower():
        import re
        quando = re.search(r"try again at ([^.\n]+)", cauda)
        alertas.append("LIMITE DE USO da conta do agente atingido"
                       + (f"; nova tentativa a partir de {quando.group(1).strip()}" if quando else "")
                       + ". O trabalho pode ter parado no meio de uma edicao: conferir os arquivos alterados")
    fora_do_escopo = []
    if a.escopo:
        import fnmatch
        dentro = lambda p: any(fnmatch.fnmatch(p, g) or p.startswith(g.rstrip("/*") + "/") for g in a.escopo)
        fora_do_escopo = [p for p in criados + alterados + removidos if not dentro(p)]

    registro = {"tarefa": a.tarefa, "agente": cfg["nome"], "modelo": modelo, "inicio": carimbo,
                "segundos": segundos, "codigo_saida": codigo, "somente_leitura": a.somente_leitura,
                "prompt": os.path.relpath(a.prompt, RAIZ), "log": os.path.relpath(base + ".log", RAIZ),
                "resposta": os.path.relpath(arq_resposta, RAIZ), "criados": criados,
                "alterados": alterados, "removidos": removidos, "escopo": a.escopo,
                "fora_do_escopo": fora_do_escopo, "alertas": alertas}
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR_LOGS, "despachos.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({k: v for k, v in registro.items() if k not in ("criados", "alterados", "removidos")}
                           | {"n_criados": len(criados), "n_alterados": len(alterados),
                              "n_removidos": len(removidos)}, ensure_ascii=False) + "\n")

    print(f"[{'OK' if codigo == 0 and not alertas else '!!'}] codigo {codigo} em {segundos} s | "
          f"criados {len(criados)} | alterados {len(alterados)} | removidos {len(removidos)}")
    for rot, lista in (("criado", criados), ("alterado", alterados), ("removido", removidos)):
        for p in lista[:40]:
            print(f"    {rot:<9} {p}")
        if len(lista) > 40:
            print(f"    ... e mais {len(lista) - 40} {rot}s")
    if fora_do_escopo:
        print(f"[FORA DO ESCOPO] {len(fora_do_escopo)} arquivo(s) mudaram fora do escopo declarado. Pode ser "
              f"violacao do agente ou outro agente trabalhando ao mesmo tempo -- conferir antes de aceitar:")
        for p in fora_do_escopo[:20]:
            print(f"    {p}")
    for alerta in alertas:
        print(f"[ALERTA] {alerta}")
    print(f"    resposta final: {registro['resposta']}")
    sys.exit(0 if codigo == 0 and not alertas else 1)


if __name__ == "__main__":
    main()
