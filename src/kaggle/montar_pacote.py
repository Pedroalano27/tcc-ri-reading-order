"""
Monta o pacote para rodar os experimentos pesados nas GPUs do Kaggle (2x T4, 16 GB cada).

Gera em dist/kaggle/:
  tcc_ordem_leitura.zip       codigo (src/), TODAS as paginas ja extraidas (protocolo, extras da
                              curva e Japeri), as tarefas e anotacoes do Golden Dataset e as
                              predicoes locais dos outros metodos. Suba como Dataset privado.
  kaggle_treino_ordem.ipynb   TREINO: as duas formulacoes do LayoutLM, a curva de aprendizado,
                              as ablacoes e a varredura do limiar de decodificacao.
  kaggle_llm_ordem.ipynb      LLMs de 7B a 32B via Ollama, no teste e nas paginas anotadas.

Os dois notebooks tambem sao copiados para notebooks/. Cada um roda sozinho por ate 12 h
com "Save & Run All (Commit)"; rode o de treino primeiro, porque o de LLM aproveita os
checkpoints que ele produz.

Os PDFs (19 GB) e as imagens do Golden nao vao: nada la precisa deles.
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
sys.path.insert(0, RAIZ)
from src.eval.protocolo import arquivos_paginas_ausentes

DIST = os.path.join(RAIZ, "dist", "kaggle")
NOME_ZIP = "tcc_ordem_leitura.zip"

REQUISITOS = "ollama>=0.4\nsacrebleu>=2.3\n"   # torch, transformers e scipy ja vem na imagem do Kaggle

LEIAME = """Pacote do TCC (ordem de leitura em Diarios Oficiais) para o Kaggle.
Adicione este dataset aos notebooks (Add Input) e rode primeiro kaggle_treino_ordem.ipynb,
depois kaggle_llm_ordem.ipynb. Passo a passo: docs/KAGGLE.md no repositorio.
"""

# Celula de preparo, identica nos dois notebooks.
PREPARO = """import os, sys, glob, json, time, shutil, subprocess, urllib.request

achados = glob.glob("/kaggle/input/**/data/processed/splits.json", recursive=True)
assert achados, "Pacote nao encontrado: use Add Input e adicione o dataset com tcc_ordem_leitura.zip"
origem = os.path.dirname(os.path.dirname(os.path.dirname(achados[0])))
PROJ = "/kaggle/working/tcc"
if not os.path.exists(PROJ):
    shutil.copytree(origem, PROJ)
os.chdir(PROJ)
os.makedirs("models/layoutlm_ordem", exist_ok=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-kaggle.txt"], check=True)

def rodar(cmd, mostrar=True, ultimas_n=3):
    if isinstance(cmd, str):
        cmd = cmd.split()
    print("$", " ".join(str(c) for c in cmd), flush=True)
    t0 = time.time()
    proc = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ultimas = []
    for linha in proc.stdout:
        if mostrar:
            print(linha, end="", flush=True)
        ultimas = (ultimas + [linha])[-ultimas_n:]
    codigo = proc.wait()
    if not mostrar:
        print("".join(ultimas).strip()[-500:])
    print(f"  [{time.time() - t0:.0f} s, codigo {codigo}]", flush=True)
    return codigo

print("Projeto em", PROJ)
!nvidia-smi --query-gpu=name,memory.total --format=csv"""

ZIPAR = """import zipfile
destino = "/kaggle/working/resultados_kaggle.zip"
with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
    for arq in glob.glob("resultados/**/*", recursive=True):
        if os.path.isfile(arq) and not arq.endswith(".pt"):
            z.write(arq)
    for arq in glob.glob("models/layoutlm_ordem/*_config.json"):
        z.write(arq)
    for arq in glob.glob("docs/figuras/*.png"):
        z.write(arq)
    for arq in glob.glob("/kaggle/working/*.log"):
        z.write(arq, "logs/" + os.path.basename(arq))
print("Pronto:", destino, f"({os.path.getsize(destino) / 2**20:.1f} MB). Baixe na aba Output.")"""

TREINO = [
    ("markdown", """# Treino na GPU do Kaggle: a formulação de sucessor e a curva de aprendizado

Roda o que é pesado demais para a RTX 4050 de 6 GB, com o **mesmo protocolo** do projeto
(mesmas páginas, mesma referência, blocos embaralhados pela mesma permutação):

1. **curva de aprendizado** das duas formulações do LayoutLM — a pontual (um escore por bloco)
   e a de **sucessor** (prevê qual bloco vem depois), em 5 tamanhos de treino;
2. **ablações** da formulação de sucessor: sem o viés geométrico, sem a perda auxiliar de
   posição, sem o layout 2D;
3. **varredura do limiar de decodificação**, que regula quanto o modelo confia nas cadeias
   locais antes de recorrer à ordem global;
4. **latência de todos os métodos no mesmo hardware**, para a comparação de eficiência ser justa;
5. **avaliação contra a anotação humana**, se o lote do Golden Dataset já estiver anotado.

**Antes de rodar**
1. *Settings* → *Accelerator*: **GPU T4 x2** · *Internet*: **On** (o LayoutLM base vem do Hugging Face).
2. *Add Input* → o dataset com `tcc_ordem_leitura.zip` (gerado por `src/kaggle/montar_pacote.py`).
3. *Save Version* → **Save & Run All (Commit)**: roda em segundo plano por até 12 h, com o navegador fechado.
4. No fim, baixe `resultados_kaggle.zip` na aba *Output* e rode no projeto
   `venv\\Scripts\\python.exe src\\kaggle\\importar_resultados.py resultados_kaggle.zip`."""),

    ("code", """# ===== CONFIGURACAO =====
TAMANHOS = [152, 400, 1000, 2000, 0]     # paginas de treino; 0 = todas as extras disponiveis (3.235)
MODELOS = ["layoutlm_sucessor", "layoutlm"]   # a formulacao nova primeiro, caso o tempo acabe
MICRO_BATCH = 12         # a T4 tem 16 GB; o batch EFETIVO continua 8 (acumulacao), so muda a velocidade
ABLACOES = True          # sem vies geometrico / sem perda de posicao / sem layout 2D
LIMIARES = [0.0, 0.3, 0.5, 0.7, 0.9]     # varredura do limiar da cadeia (so avaliacao, custa segundos)
LOTE_GOLDEN = "golden_v1"
GUARDAR_CHECKPOINT = True                # salva o melhor modelo em /kaggle/working para baixar (~450 MB)"""),

    ("code", PREPARO),

    ("code", """# Latencia de ingenua, XY-cut, BiLSTM e LayoutLM NESTA maquina, com o mesmo roteiro de medicao
rodar([sys.executable, "src/eval/latencia_hardware.py", "--maquina", "kaggle_t4"])"""),

    ("code", """# Curva de aprendizado das duas formulacoes. E a parte longa: ~1 h por modelo na T4.
rodar([sys.executable, "src/rodar_curva_aprendizado.py", "--modelos", *MODELOS, "--tamanhos", *TAMANHOS,
       "--sem-lstm", "--micro-batch", MICRO_BATCH])
print(open("resultados/curva_aprendizado/curva.json").read()[:400])"""),

    ("code", """# O maior treino que a curva de fato usou, e o checkpoint que ele deixou
N_MAIOR = json.load(open("resultados/curva_aprendizado/curva.json"))["tamanhos"][-1]
CKPT = f"curva_layoutlm_sucessor_n{N_MAIOR}"
if not os.path.exists(f"models/layoutlm_ordem/{CKPT}.pt"):
    CKPT = "layoutlm_sucessor"      # a curva nao chegou ao fim; cai para o treino padrao
print("maior treino:", N_MAIOR, "paginas | checkpoint:", CKPT)"""),

    ("code", """# Ablacoes da formulacao de sucessor, no maior treino: o que cada peca do modelo contribui
VARIANTES = [(["--sem-vies-geo"], "ablacao_suc_sem_vies_geo", "sem o MLP de geometria relativa"),
             (["--peso-posicao", "0"], "ablacao_suc_sem_posicao", "sem a perda auxiliar de posicao"),
             (["--sem-layout"], "ablacao_suc_sem_layout", "sem as bounding boxes (so texto)")]
if ABLACOES:
    for flags, nome, o_que in VARIANTES:
        print("\\n===== ablacao:", o_que, "=====", flush=True)
        base = [sys.executable, "src/models/layoutlm_sucessor.py"]
        if rodar(base + ["treinar", "--nome", nome, "--n-treino", N_MAIOR, *flags,
                         "--blocos-extra", "data/processed/blocos_extra", "--epocas", "4",
                         "--max-minutos", "60", "--micro-batch", MICRO_BATCH], mostrar=False) == 0:
            rodar(base + ["avaliar", "--nome", nome, *flags], mostrar=False)"""),

    ("code", """# Varredura do limiar: quanto o modelo deve confiar nas cadeias locais antes de recorrer
# a ordem global? Custa segundos, porque so troca a decodificacao de um modelo ja treinado.
for lim in LIMIARES:
    rodar([sys.executable, "src/models/layoutlm_sucessor.py", "avaliar", "--nome", CKPT,
           "--decodificacao", "cadeias", "--limiar-cadeia", lim,
           "--metodo", "suc_limiar_" + str(lim).replace(".", "")], mostrar=False)
rodar([sys.executable, "src/models/layoutlm_sucessor.py", "avaliar", "--nome", CKPT,
       "--decodificacao", "feixe", "--metodo", "layoutlm_sucessor_feixe"], mostrar=False)"""),

    ("code", """# Contra a anotacao humana, se o lote ja estiver anotado
if os.path.exists(f"data/golden/{LOTE_GOLDEN}/anotacoes.jsonl"):
    rodar([sys.executable, "src/eval/avaliar_golden.py", "--lote", LOTE_GOLDEN,
           "--layoutlm", "layoutlm", "--sucessor", CKPT])
else:
    print(f"Lote {LOTE_GOLDEN} ainda sem anotacoes.jsonl -- anote no projeto e refaca o pacote.")"""),

    ("code", """# Tabela final com tudo o que existe: baselines, as duas formulacoes, ablacoes e limiares
rodar([sys.executable, "src/eval/comparar.py"])
rodar([sys.executable, "src/rodar_curva_aprendizado.py", "--so-figura"], mostrar=False)"""),

    ("code", ZIPAR + """
if GUARDAR_CHECKPOINT:
    for arq in sorted(glob.glob("models/layoutlm_ordem/curva_layoutlm_sucessor_n*.pt")):
        shutil.copy(arq, "/kaggle/working/" + os.path.basename(arq))
        print("checkpoint para baixar:", os.path.basename(arq),
              f"({os.path.getsize(arq) / 2**20:.0f} MB)")"""),
]

LLM = [
    ("markdown", """# LLMs na GPU do Kaggle: ordem de leitura em Diários Oficiais

Roda as LLMs do TCC nas **mesmas páginas e com o mesmo protocolo** dos outros métodos
(blocos embaralhados, mesma referência, mesmas métricas), no teste e nas páginas anotadas
à mão, e registra a latência por página na mesma máquina.

Rode **depois** de `kaggle_treino_ordem.ipynb`: a tabela final fica completa se as predições
daquele notebook já estiverem no projeto.

**Antes de rodar**
1. *Settings* → *Accelerator*: **GPU T4 x2** · *Internet*: **On** (exige conta verificada por telefone).
2. *Add Input* → o dataset com `tcc_ordem_leitura.zip`.
3. Ajuste a célula de configuração logo abaixo.
4. *Save Version* → **Save & Run All (Commit)**: roda em segundo plano, por até 12 horas,
   mesmo com o navegador fechado.
5. No fim, baixe `resultados_kaggle.zip` na aba *Output* e, no projeto, rode
   `venv\\Scripts\\python.exe src\\kaggle\\importar_resultados.py resultados_kaggle.zip`."""),

    ("code", """# ===== CONFIGURACAO =====
MODELOS = ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"]  # rodam nesta ordem; o 32b ocupa as duas T4
FEW_SHOT = [0, 2]        # 0 = zero-shot; 2 = dois exemplos resolvidos (paginas de TREINO) no prompt
PARTICOES = ["teste", "golden:golden_v1"]  # teste = 95 paginas do protocolo; golden = anotacao humana
MAX_BLOCOS = 200         # 200 = todas as paginas
APAGAR_MODELO_APOS_USO = True   # libera o disco antes de baixar o proximo modelo
# Modelos com raciocinio (qwen3, deepseek-r1) rodam com o raciocinio desligado (--sem-pensar)."""),

    ("code", PREPARO),

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
rodar([sys.executable, "src/eval/latencia_hardware.py", "--maquina", "kaggle_t4"])"""),

    ("code", """RACIOCINIO = ("qwen3", "deepseek-r1", "magistral")
for modelo in MODELOS:
    if rodar(["ollama", "pull", modelo], mostrar=False) != 0:
        print(f"[!] falha ao baixar {modelo}; pulando")
        continue
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
rodar([sys.executable, "src/eval/comparar.py"])
if os.path.exists(f"data/golden/golden_v1/anotacoes.jsonl"):
    rodar([sys.executable, "src/eval/avaliar_golden.py", "--lote", "golden_v1"])"""),

    ("code", ZIPAR),
]

NOTEBOOKS = {"kaggle_treino_ordem.ipynb": TREINO, "kaggle_llm_ordem.ipynb": LLM}


def gerar_notebook(celulas):
    saida = []
    for tipo, fonte in celulas:
        linhas = fonte.split("\n")
        c = {"cell_type": tipo, "metadata": {}, "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]]}
        if tipo == "code":
            c.update(execution_count=None, outputs=[])
        saida.append(c)
    return {"cells": saida,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--com-modelo", action="store_true",
                    help="inclui os checkpoints ja treinados do LayoutLM (+450 MB cada)")
    a = ap.parse_args()
    with open(os.path.join(RAIZ, "data", "processed", "splits.json"), encoding="utf-8") as f:
        splits = json.load(f)
    esperados = {
        "blocos": sorted({uf for particao in ("treino", "validacao", "teste", "ufs_nao_confiaveis")
                          for uf in splits[particao]}),
        "blocos_extra": splits["treino"],
        "blocos_ri_japeri": ["official_diary_rj_japeri"],
    }
    colecoes = {
        nome: glob.glob(os.path.join(RAIZ, "data", "processed", nome, "*.jsonl"))
        for nome in esperados
    }
    vazias = [nome for nome, arquivos_colecao in colecoes.items() if not arquivos_colecao]
    ausentes = {
        nome: arquivos_paginas_ausentes(ufs, os.path.join(RAIZ, "data", "processed", nome))
        for nome, ufs in esperados.items()
    }
    if vazias or any(ausentes.values()):
        detalhe = "; ".join(
            f"data/processed/{nome}: {', '.join(faltam)}"
            for nome, faltam in ausentes.items() if faltam
        )
        motivo = (
            "colecao ausente ou vazia: "
            + ", ".join(f"data/processed/{nome}" for nome in vazias) + ". "
            if vazias else ""
        )
        sys.exit(
            "[ERRO] pacote Kaggle nao criado: " + motivo
            + "Arquivos ausentes ou sem nenhuma pagina valida: " + detalhe
            + ". A reextracao parece incompleta. Conclua a reextracao antes de empacotar."
        )

    os.makedirs(DIST, exist_ok=True)

    for nome, celulas in NOTEBOOKS.items():
        nb = gerar_notebook(celulas)
        for destino in (os.path.join(DIST, nome), os.path.join(RAIZ, "notebooks", nome)):
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(nb, f, ensure_ascii=False, indent=1)

    arquivos = [p for p in glob.glob(os.path.join(RAIZ, "src", "**", "*.py"), recursive=True)
                if "__pycache__" not in p]
    arquivos.append(os.path.join(RAIZ, "data", "processed", "splits.json"))
    for arquivos_colecao in colecoes.values():     # curva e piloto de RI rodam la tambem
        arquivos += arquivos_colecao
    arquivos += glob.glob(os.path.join(RAIZ, "data", "golden", "*", "tarefas.jsonl"))
    arquivos += glob.glob(os.path.join(RAIZ, "data", "golden", "*", "anotacoes.jsonl"))
    arquivos += glob.glob(os.path.join(RAIZ, "resultados", "pred_*.jsonl"))
    arquivos += glob.glob(os.path.join(RAIZ, "resultados", "comparacao.json"))
    if a.com_modelo:
        arquivos += glob.glob(os.path.join(RAIZ, "models", "layoutlm_ordem", "*.pt"))
    faltando = [p for p in arquivos if not os.path.exists(p)]
    if faltando:
        sys.exit(f"[ERRO] arquivos ausentes: {faltando[:3]}")

    caminho_zip = os.path.join(DIST, NOME_ZIP)
    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(arquivos):
            z.write(p, os.path.relpath(p, RAIZ).replace("\\", "/"))
        z.writestr("requirements-kaggle.txt", REQUISITOS)
        z.writestr("LEIAME_KAGGLE.txt", LEIAME)
    anotados = sum(1 for p in arquivos if p.endswith("anotacoes.jsonl"))
    print(f"[OK] {caminho_zip} ({os.path.getsize(caminho_zip) / 2**20:.1f} MB, {len(arquivos)} arquivos, "
          f"{anotados} lote(s) do Golden com anotacao)")
    for nome in NOTEBOOKS:
        print(f"[OK] notebook: {os.path.join(DIST, nome)} (copia em notebooks/)")
    print("     Proximo passo: docs/KAGGLE.md")


if __name__ == "__main__":
    main()
