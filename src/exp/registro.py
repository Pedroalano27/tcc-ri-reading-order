"""Registro de experimentos do TCC (sem dependencias externas).

Cada experimento tem um ID (E001, E002, ...), um cartao em experimentos/cards/<ID>.md
(hipotese, metodo, criterio de sucesso e de abandono, decidido ANTES de rodar) e zero ou
mais execucoes registradas em experimentos/registro.jsonl (uma linha por execucao, com
commit do git, hash da configuracao e dos dados, ambiente, metricas por bancada e veredito).
experimentos/REGISTRO.md e gerado a partir do jsonl (nao editar a mao).

Uso:
  python -B src/exp/registro.py novo --titulo "LM causal nas arestas" --frente ordenacao --hipotese H03
  python -B src/exp/registro.py registrar --id E001 --metricas resultados/x.json --config cfg.json \
         --dados resultados/ordem_lm/pares/MANIFESTO.json --ambiente spark --veredito inconclusivo --nota "..."
  python -B src/exp/registro.py tabela
  python -B src/exp/registro.py dados   # hashes das bancadas e conjuntos de treino (versao dos dados)

O arquivo de metricas e um JSON {"<bancada>": {"tau": .., "quebras": .., ...}, ...}.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXP = RAIZ / "experimentos"
JSONL = EXP / "registro.jsonl"
CARDS = EXP / "cards"
MODELO = EXP / "modelo_cartao.md"
VEREDITOS = ("melhorou", "piorou", "inconclusivo", "abandonado", "falhou", "controle")
# Arquivos que definem uma versao dos dados de avaliacao/treino (somente leitura).
DADOS = [
    "resultados/unidades_sem_caixas/bancadas/golden_v4.jsonl",
    "resultados/unidades_sem_caixas/bancadas/golden_v3_novo.jsonl",
    "resultados/unidades_sem_caixas/treino_noite.json",
    "resultados/unidades_sem_caixas/manifesto.json",
    "data/processed/splits.json",
    "data/golden/golden_v4/anotacoes.jsonl",
    "data/golden/golden_v4/tarefas.jsonl",
]


def sha(path: Path, n=16) -> str:
    """Hash de um arquivo; de uma pasta, hash dos caminhos relativos e conteudos (ignora img/)."""
    h = hashlib.sha256()
    arquivos = [path] if path.is_file() else sorted(
        q for q in path.rglob("*") if q.is_file() and "img" not in q.relative_to(path).parts)
    for q in arquivos:
        if q != path:
            h.update(q.relative_to(path).as_posix().encode())
        with open(q, "rb") as f:
            for bloco in iter(lambda: f.read(1 << 20), b""):
                h.update(bloco)
    return h.hexdigest()[:n]


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:
        return ""


def proximo_id() -> str:
    ns = [int(m.group(1)) for p in CARDS.glob("E*.md") if (m := re.match(r"E(\d+)", p.name))]
    return f"E{(max(ns) + 1 if ns else 1):03d}"


def novo(a):
    CARDS.mkdir(parents=True, exist_ok=True)
    eid = a.id or proximo_id()
    if list(CARDS.glob(f"{eid}_*.md")):
        sys.exit(f"cartao {eid} ja existe")
    slug = re.sub(r"[^a-z0-9]+", "_", a.titulo.lower()).strip("_")[:40]
    txt = MODELO.read_text(encoding="utf-8")
    txt = (txt.replace("{ID}", eid).replace("{TITULO}", a.titulo)
              .replace("{FRENTE}", a.frente).replace("{HIPOTESE}", a.hipotese or "-")
              .replace("{DATA}", dt.date.today().isoformat()))
    p = CARDS / f"{eid}_{slug}.md"
    p.write_text(txt, encoding="utf-8")
    print(p.relative_to(RAIZ))


def registrar(a):
    if a.veredito not in VEREDITOS:
        sys.exit(f"veredito deve ser um de {VEREDITOS}")
    if not list(CARDS.glob(f"{a.id}_*.md")):
        sys.exit(f"cartao {a.id} nao existe: crie com 'novo' antes de registrar")
    met = json.loads(Path(a.metricas).read_text(encoding="utf-8")) if a.metricas else {}
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else {}
    linha = {
        "id": a.id, "quando": dt.datetime.now().isoformat(timespec="seconds"),
        "commit": git("rev-parse", "--short", "HEAD"),
        "arvore_suja": bool(git("status", "--porcelain", "--untracked-files=no")),
        "config": cfg, "config_hash": hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16],
        "dados": {d: sha(RAIZ / d) for d in (a.dados or []) if (RAIZ / d).exists()},
        "ambiente": a.ambiente, "python": platform.python_version(), "maquina": platform.node(),
        "metricas": met, "veredito": a.veredito, "nota": a.nota or "",
        "artefatos": a.artefatos or [],
    }
    with open(JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    tabela(None)
    print(f"registrado {a.id} ({a.veredito})")


def fmt(v):
    return f"{v:.3f}".replace(".", ",") if isinstance(v, float) else str(v)


def tabela(_a):
    linhas = [json.loads(x) for x in JSONL.read_text(encoding="utf-8").splitlines() if x.strip()] \
        if JSONL.exists() else []
    titulos = {}
    for p in sorted(CARDS.glob("E*.md")):
        m = re.search(r"^# (.+)$", p.read_text(encoding="utf-8"), re.M)
        titulos[p.name.split("_")[0]] = (m.group(1) if m else p.stem, p.name)
    out = ["# Registro de experimentos", "",
           "Gerado por `src/exp/registro.py tabela` a partir de `registro.jsonl`. Não editar à mão.", "",
           "## Cartões", "", "| ID | Título | Execuções | Último veredito |", "|---|---|---:|---|"]
    for eid, (tit, nome) in titulos.items():
        ex = [l for l in linhas if l["id"] == eid]
        out.append(f"| [{eid}](cards/{nome}) | {tit} | {len(ex)} | {ex[-1]['veredito'] if ex else 'planejado'} |")
    out += ["", "## Execuções", "",
            "| ID | Quando | Commit | Ambiente | Bancada | τ | Quebras/pág | Sucessor | Veredito | Nota |",
            "|---|---|---|---|---|---:|---:|---:|---|---|"]
    for l in linhas:
        met = l["metricas"] if isinstance(l["metricas"], dict) and l["metricas"] else {"-": {}}
        for banc, m in met.items():
            m = m if isinstance(m, dict) else {}
            out.append(f"| {l['id']} | {l['quando'][:16]} | {l['commit']}{'*' if l.get('arvore_suja') else ''} | "
                       f"{l['ambiente']} | {banc} | {fmt(m.get('tau', ''))} | {fmt(m.get('quebras', ''))} | "
                       f"{fmt(m.get('sucessor', ''))} | {l['veredito']} | {l['nota'][:80]} |")
    out += ["", "`*` = árvore de trabalho com alterações não commitadas no momento da execução.", ""]
    (EXP / "REGISTRO.md").write_text("\n".join(out), encoding="utf-8")


def dados(_a):
    vistos = {}
    for d in DADOS:
        p = RAIZ / d
        vistos[d] = sha(p) if p.exists() else None
    print(json.dumps(vistos, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="acao", required=True)
    n = sub.add_parser("novo"); n.add_argument("--titulo", required=True)
    n.add_argument("--id", help="ID do plano (ex.: E006); padrao: proximo livre")
    n.add_argument("--frente", required=True, choices=("ordenacao", "anotacao", "dataset", "infra"))
    n.add_argument("--hipotese")
    r = sub.add_parser("registrar"); r.add_argument("--id", required=True)
    r.add_argument("--metricas"); r.add_argument("--config"); r.add_argument("--dados", nargs="*")
    r.add_argument("--ambiente", required=True, choices=("local", "kaggle", "spark", "api"))
    r.add_argument("--veredito", required=True); r.add_argument("--nota"); r.add_argument("--artefatos", nargs="*")
    sub.add_parser("tabela"); sub.add_parser("dados")
    a = ap.parse_args()
    {"novo": novo, "registrar": registrar, "tabela": tabela, "dados": dados}[a.acao](a)


if __name__ == "__main__":
    main()
