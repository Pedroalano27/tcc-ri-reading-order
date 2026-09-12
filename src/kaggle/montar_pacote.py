"""
Monta o pacote para rodar as LLMs numa GPU do Kaggle.

Gera em dist/kaggle/:
  tcc_ordem_leitura.zip    codigo (src/), paginas ja extraidas (data/processed), tarefas do
                           Golden Dataset (sem imagens) e as predicoes locais dos outros
                           metodos, para a comparacao sair completa la. Suba como Dataset privado.
  kaggle_llm_ordem.ipynb   o notebook, tambem salvo em notebooks/. Importe no Kaggle.

Os PDFs (19 GB) nao vao: o notebook so precisa dos blocos ja extraidos.
Passo a passo em docs/KAGGLE.md.

Uso:
    python src/kaggle/montar_pacote.py [--com-modelo]
"""
from __future__ import annotations

import os
import sys
import json
import glob
import zipfile
import argparse

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(RAIZ, "dist", "kaggle")
NOME_ZIP = "tcc_ordem_leitura.zip"

REQUISITOS = "ollama>=0.4\nsacrebleu>=2.3\n"   # torch, transformers e scipy ja vem na imagem do Kaggle

LEIAME = """Pacote do TCC (ordem de leitura em Diarios Oficiais) para o Kaggle.
Adicione este dataset ao notebook kaggle_llm_ordem.ipynb (Add Input) e rode.
Passo a passo completo: docs/KAGGLE.md no repositorio.
"""

CELULAS = [
    ("markdown", """# Ordem de leitura em Diários Oficiais: LLMs na GPU do Kaggle

Roda as LLMs do TCC nas **mesmas páginas e com o mesmo protocolo** do projeto (blocos
embaralhados, mesma referência, mesmas métricas) e mede a latência de todos os métodos
**no mesmo hardware**, para a comparação de eficiência ser justa.

**Antes de rodar**
1. *Settings* → *Accelerator*: **GPU T4 x2** · *Internet*: **On** (exige conta verificada por telefone).
2. *Add Input* → o dataset com `tcc_ordem_leitura.zip`, gerado por `src/kaggle/montar_pacote.py`.
3. Ajuste a célula de configuração logo abaixo.
4. *Save Version* → **Save & Run All (Commit)**: roda em segundo plano, por até 12 horas,
   mesmo com o navegador fechado.
5. No fim, baixe `resultados_kaggle.zip` na aba *Output* e, no projeto, rode
   `venv\\Scripts\\python.exe src\\kaggle\\importar_resultados.py resultados_kaggle.zip`."""),

    ("code", """# ===== CONFIGURACAO =====
MODELOS = ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"]  # rodam nesta ordem; o 32b ocupa as duas T4
FEW_SHOT = [0, 2]        # 0 = zero-shot; 2 = dois exemplos resolvidos (paginas de TREINO) no prompt
PARTICOES = ["teste", "golden:golden_v1"]  # teste = 95 paginas do protocolo; golden = paginas da anotacao humana
MAX_BLOCOS = 200         # 200 = todas as paginas
APAGAR_MODELO_APOS_USO = True   # libera o disco antes de baixar o proximo modelo
# Modelos com raciocinio (qwen3, deepseek-r1) rodam com o raciocinio desligado (--sem-pensar)."""),

    ("code", """import os, sys, glob, json, time, shutil, subprocess, urllib.request

achados = glob.glob("/kaggle/input/**/data/processed/splits.json", recursive=True)
assert achados, "Pacote nao encontrado: use Add Input e adicione o dataset com tcc_ordem_leitura.zip"
origem = os.path.dirname(os.path.dirname(os.path.dirname(achados[0])))
PROJ = "/kaggle/working/tcc"
if not os.path.exists(PROJ):
    shutil.copytree(origem, PROJ)
os.chdir(PROJ)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-kaggle.txt"], check=True)
print("Projeto em", PROJ)
!nvidia-smi --query-gpu=name,memory.total --format=csv"""),

    ("code", """# Instala e liga o Ollama (o mesmo servidor de LLM usado no notebook local)
!apt-get -qq update > /dev/null 2>&1; apt-get -qq install -y pciutils lshw zstd > /dev/null 2>&1
!curl -fsSL https://ollama.com/install.sh | sh > /kaggle/working/instalacao_ollama.log 2>&1; tail -n 2 /kaggle/working/instalacao_ollama.log

os.environ["OLLAMA_KEEP_ALIVE"] = "30m"
servidor = subprocess.Popen(["ollama", "serve"], stdout=open("/kaggle/working/ollama.log", "w"),
                            stderr=subprocess.STDOUT)
for _ in range(90):
    try:
        versao = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=2).read())
        print("Ollama", versao["version"], "no ar")
        break
    except Exception:
        time.sleep(1)
else:
    raise RuntimeError("O Ollama nao subiu; veja /kaggle/working/ollama.log")"""),

    ("code", """# Latencia de ingenua, XY-cut, BiLSTM e LayoutLM NESTA maquina, com o mesmo roteiro de medicao
!python src/eval/latencia_hardware.py --maquina kaggle_t4"""),

    ("code", """def rodar(cmd, mostrar=True):
    print("$", " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ultimas = []
    for linha in proc.stdout:
        if mostrar:
            print(linha, end="", flush=True)
        ultimas = (ultimas + [linha])[-2:]
    codigo = proc.wait()
    if not mostrar:
        print("".join(ultimas)[-300:])
    return codigo

RACIOCINIO = ("qwen3", "deepseek-r1", "magistral")
for modelo in MODELOS:
    t0 = time.time()
    if rodar(["ollama", "pull", modelo], mostrar=False) != 0:
        print(f"[!] falha ao baixar {modelo}; pulando")
        continue
    print(f"[download] {modelo} em {time.time() - t0:.0f} s")
    for fs in FEW_SHOT:
        for particao in PARTICOES:
            cmd = [sys.executable, "src/eval/llm_ordem.py", "--modelo", modelo, "--few-shot", str(fs),
                   "--particao", particao, "--max-blocos", str(MAX_BLOCOS), "--retomar"]
            if modelo.startswith(RACIOCINIO):
                cmd.append("--sem-pensar")
            rodar(cmd)
    if APAGAR_MODELO_APOS_USO:
        rodar(["ollama", "rm", modelo], mostrar=False)"""),

    ("code", """# Tabela completa: metodos locais (LayoutLM, XY-cut...) + as LLMs que acabaram de rodar, nas mesmas paginas
!python src/eval/comparar.py"""),

    ("code", """import zipfile
destino = "/kaggle/working/resultados_kaggle.zip"
with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
    for arq in glob.glob("resultados/**/*", recursive=True):
        nome = os.path.basename(arq)
        if os.path.isfile(arq) and nome.startswith(("pred_llm_", "latencia_", "execucoes_llm", "comparacao")):
            z.write(arq)
    if os.path.exists("/kaggle/working/ollama.log"):
        z.write("/kaggle/working/ollama.log", "logs/ollama.log")
print("Pronto:", destino, f"({os.path.getsize(destino) / 1024:.0f} KB). Baixe na aba Output.")"""),
]


def gerar_notebook():
    celulas = []
    for tipo, fonte in CELULAS:
        linhas = fonte.split("\n")
        c = {"cell_type": tipo, "metadata": {}, "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]]}
        if tipo == "code":
            c.update(execution_count=None, outputs=[])
        celulas.append(c)
    return {"cells": celulas,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--com-modelo", action="store_true",
                    help="inclui o checkpoint treinado do LayoutLM (+450 MB; so muda o tau, nao a latencia)")
    a = ap.parse_args()
    os.makedirs(DIST, exist_ok=True)

    nb = gerar_notebook()
    for destino in (os.path.join(DIST, "kaggle_llm_ordem.ipynb"), os.path.join(RAIZ, "notebooks", "kaggle_llm_ordem.ipynb")):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

    arquivos = [p for p in glob.glob(os.path.join(RAIZ, "src", "**", "*.py"), recursive=True) if "__pycache__" not in p]
    arquivos.append(os.path.join(RAIZ, "data", "processed", "splits.json"))
    arquivos += glob.glob(os.path.join(RAIZ, "data", "processed", "blocos", "*.jsonl"))
    arquivos += glob.glob(os.path.join(RAIZ, "data", "golden", "*", "tarefas.jsonl"))
    arquivos += glob.glob(os.path.join(RAIZ, "resultados", "pred_*.jsonl"))
    if a.com_modelo:
        arquivos.append(os.path.join(RAIZ, "models", "layoutlm_ordem", "layoutlm.pt"))
    faltando = [p for p in arquivos if not os.path.exists(p)]
    if faltando:
        sys.exit(f"[ERRO] arquivos ausentes: {faltando[:3]}")

    caminho_zip = os.path.join(DIST, NOME_ZIP)
    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(arquivos):
            z.write(p, os.path.relpath(p, RAIZ).replace("\\", "/"))
        z.writestr("requirements-kaggle.txt", REQUISITOS)
        z.writestr("LEIAME_KAGGLE.txt", LEIAME)
    mb = os.path.getsize(caminho_zip) / 2 ** 20
    print(f"[OK] {caminho_zip} ({mb:.1f} MB, {len(arquivos)} arquivos)")
    print(f"[OK] notebook: {os.path.join(DIST, 'kaggle_llm_ordem.ipynb')} (copia em notebooks/)")
    print("     Proximo passo: docs/KAGGLE.md")


if __name__ == "__main__":
    main()
