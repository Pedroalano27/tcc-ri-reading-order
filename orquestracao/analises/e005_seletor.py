"""Compara seletores E005 por pagina usando apenas ordens ja salvas, em CPU.

Reproduz a ancora antes de medir; importa a regua, os diagnosticos e o
bootstrap existentes. Features recebem somente geometria, texto automatico
e predicoes. LOOV conjunto e exploratorio: suas bancadas externas participam
do treino dos OUTROS folds. Uma segunda analise treina exclusivamente em
v4/RN, exclui o veiculo de destino e preserva a transferencia externa.
Nao procura hiperparametros, limiares ou sementes depois de ver resultados.
Caches atomicos por pagina/fold permitem retomar apos reinicio.

Uso da raiz: venv/Scripts/python.exe -B orquestracao/analises/e005_seletor.py
  [--autoteste] [--somente-ancora] [--max-minutos 30] [--conferir]
Escreve somente em resultados/e005_seletor/. Sem GPU, PDFs, dados do parceiro,
DataLoader, multiprocessing, alteracao de anotacoes ou avaliacao cega.
LightGBM ausente fica explicitamente indisponivel, sem substituto silencioso.
"""
from __future__ import annotations

import os
os.environ.update(CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                  NUMEXPR_NUM_THREADS="4")
import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import statistics
import time
from contextlib import contextmanager

import numpy as np
import sklearn
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from orquestracao.analises import bancada_ordenadores as b
from orquestracao.analises import erros_ponta_a_ponta as e
from orquestracao.analises import corretor_de_transicoes as c
from orquestracao.analises import e002_oraculos as o

if "torch" in sys.modules:
    sys.modules["torch"].set_num_threads(4)

OUT = RAIZ / "resultados/e005_seletor"
COORTES = o.COORTES
AJUSTE = ("golden_v4", "validacao_silver")
SEMENTES = (42, 43, 44)
MODELOS = ("arvore_rasa", "logistica", "lightgbm")
METRICAS = o.METRICAS
BASES = ("regra", "hibrido67")
FEATURES = ("n_unidades", "n_colunas_regra", "prop_margem", "prop_cabecalho",
            "prop_rodape", "n_tabelas", "n_imagens", "tem_transversal",
            "largura_media_coluna", "concordancia_regra_layoutreader")
PARAMETROS = {
    "arvore_rasa": {"max_depth": 3, "min_samples_leaf": 5},
    "logistica": {"C": 1., "max_iter": 2000, "solver": "lbfgs"},
    "lightgbm": {"n_estimators": 50, "num_leaves": 7, "max_depth": 3,
                 "min_child_samples": 10, "learning_rate": .05,
                 "reg_lambda": 1., "n_jobs": 4, "verbosity": -1,
                 "deterministic": True, "force_col_wise": True},
}
PRAZO = None
FONTES = {}


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def gravar(path, obj):
    path = path.resolve()
    exigir(path.is_relative_to(OUT.resolve()), "Escrita fora de E005")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fonte(path):
    path = path.resolve()
    exigir(path.is_relative_to(RAIZ) and "labelstudio" not in path.parts,
           "Fonte fora do escopo")
    FONTES[path.relative_to(RAIZ).as_posix()] = c.sha(path)
    return path


def vigiar():
    exigir(o.ler_lock()[0] == o.ASSINATURA_LOCK, "O lock cego mudou; reinicie")
    if PRAZO and time.monotonic() >= PRAZO:
        raise TimeoutError("Prazo atingido; caches preservados para retomada")


@contextmanager
def trava():
    path = OUT / "cache/execucao.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if not f.tell():
            f.write(b"0")
            f.flush()
        f.seek(0)
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def salvos():
    """Carrega ordens, nunca executa LayoutReader ou o grafo."""
    preds = {co: {m: {} for m in ("regra", "layoutreader_pronto")} for co in COORTES}
    for co in COORTES:
        for nome, arquivo in (("regra", "regra_colunas"),
                              ("layoutreader_pronto", "layoutreader_pronto")):
            path = b.OUT / "pred" / f"{arquivo}__linhas__{co}.jsonl"
            if path.exists():
                for r in o.linhas_seguras(fonte(path)):
                    exigir(r["page_id"] not in preds[co][nome], "Predicao duplicada")
                    preds[co][nome][r["page_id"]] = r["ordem"]
    # RN nao tem arquivo canonico da regra: reutiliza a ordem SALVA no E002.
    manifesto = RAIZ / "resultados/e002_oraculos/cache/manifesto.json"
    if manifesto.exists():
        meta = b.ler(fonte(manifesto))
        pasta = manifesto.parent / meta["assinatura"] / "validacao_silver"
        for path in sorted(pasta.glob("*.json")):
            if path.stem.endswith("_residual"):
                continue
            r = b.ler(fonte(path))
            o.permitido(r["page_id"])
            preds["validacao_silver"]["regra"].setdefault(
                r["page_id"], r["resultados"]["regra_colunas"]["ordem"])
    rel = RAIZ / "resultados/e004_grafo/RELATORIO.md"
    texto = fonte(rel).read_text(encoding="utf-8") if rel.exists() else ""
    linha = next((s for s in texto.splitlines() if "Veredito do cartão E004:" in s), "ausente").rstrip(".")
    info = {"estado": linha, "incluido": False, "metodo": None}
    metodos = ["regra", "layoutreader_pronto"]
    # A retomada solicitada por Pedro inclui o grafo CONCLUIDO mesmo se seu
    # criterio individual der NAO GO: roteamento e uma hipotese diferente.
    # Nao adota o grafo como metodo final nem muda o criterio do cartao E005.
    concluido = any("Veredito do cartão E004: "+v in linha for v in ("GO", "NÃO GO"))
    if concluido:
        raiz = RAIZ / "resultados/e004_grafo"
        pointer = b.ler(fonte(raiz / "cache/ultima_execucao.json"))
        estado = b.ler(fonte(raiz / pointer["execucao"] / "estado.json"))
        exigir(estado["completo"] and estado["escolha"]["congelado"], "E004 nao congelado")
        escolhido = estado["escolha"]["metodo"]
        for co in COORTES:
            preds[co]["grafo_e004"] = {}
            for r in estado["dados"].get(co, []):
                o.permitido(r["page_id"])
                if escolhido in r["resultados"]:
                    preds[co]["grafo_e004"][r["page_id"]] = r["resultados"][escolhido]["ordem"]
        metodos.append("grafo_e004")
        info.update(incluido=True, metodo=escolhido)
    return preds, metodos, info


def extrair_features(auto, ws, ordens, metodos):
    """Nao recebe referencia, metrica, uf ou indicador de bancada."""
    ctx = c.contexto(auto, ws)
    us, W = ctx["cs"], auto["dimensions"]["width"]
    linhas = [u for u in us if c.tipo_unidade(u) == "texto"]
    den = max(1, len(linhas))
    prop = lambda tipo: sum(ctx["margem"].get(u["id"]) == tipo for u in linhas) / den
    larguras = []
    for grupo in ctx["grupos"].values():
        if grupo:
            larguras.append((max(ctx["mapa"][u]["bbox"][2] for u in grupo) -
                              min(ctx["mapa"][u]["bbox"][0] for u in grupo)) / W)
    vals = [len(us), ctx["diag"]["max_colunas"], prop("marca")+prop("topo")+prop("rodape"),
            prop("topo"), prop("rodape"), sum(c.tipo_unidade(u) == "tabela" for u in us),
            sum(c.tipo_unidade(u) == "imagem" for u in us), int(bool(ctx["pontes"])),
            statistics.mean(larguras) if larguras else 0.]
    # Inclui FIM privado, uma decisao de sucessor por unidade.
    for a, z in itertools.combinations(metodos, 2):
        sa = dict(zip(ordens[a], ordens[a][1:]+[None]))
        sz = dict(zip(ordens[z], ordens[z][1:]+[None]))
        vals.append(sum(sa[u] == sz[u] for u in sa)/len(sa))
    exigir(np.isfinite(vals).all(), "Feature nao finita")
    return vals, ctx


def alvo(resultados, metodos):
    # A ordem fixa coloca a regra antes de qualquer metodo empatado, sem usar tau.
    return min(range(len(metodos)), key=lambda i: resultados[metodos[i]]["metricas"]["quebras"])


def preparar(preds, metodos, assinatura, antigas):
    rows, ausencias = [], {}
    for co in COORTES:
        ausencias[co] = collections.Counter()
        for obj, p in o.paginas(co):
            vigiar()
            pid = p["page_id"]
            ordens = {m: preds[co][m][pid] for m in metodos if pid in preds[co][m]}
            if "regra" not in ordens:
                ausencias[co]["regra_sem_predicao"] += 1
                continue
            fp = c.digest([assinatura, obj, p, ordens])
            path = OUT / "cache/paginas" / co / (hashlib.sha256(pid.encode("utf-8")).hexdigest()+".json")
            row = b.ler(path) if path.exists() else None
            if not row or row["fingerprint"] != fp:
                auto = c.automatico(p)
                completo = len(ordens) == len(metodos)
                if completo:
                    features, ctx = extrair_features(auto, obj["palavras"], ordens, metodos)
                else:
                    features, ctx = None, c.contexto(auto, obj["palavras"])
                exigir(ctx["ordem"] == ordens["regra"], "Regra salva divergiu da ancora")
                exigir(sorted(k for ks in ctx["exp"].values() for k in ks) ==
                       list(range(len(obj["palavras"]))), "Expansao canonica perdeu/repetiu palavras")
                resultados, seqs = {}, {}
                for nome, ordem in ordens.items():
                    b.auditar_unidades(p, obj)
                    if tuple(ordem) not in seqs:
                        med, classes, trs, _ = c.preparar_avaliacao(obj, p, {**ctx, "ordem": ordem})
                        seqs[tuple(ordem)] = {"metricas": med, "classes": classes,
                            "certos": [i for i, tr in enumerate(trs) if tr["acerto"]],
                            "tipos": [tr["tipo"] for tr in trs], "ordem": ordem}
                    resultados[nome] = seqs[tuple(ordem)]
                    anterior = antigas.get(co, {}).get(nome, {}).get(pid)
                    if anterior:
                        for k in METRICAS:
                            a, z = anterior[k], resultados[nome]["metricas"][k]
                            exigir((a is None and z is None) or
                                   (a is not None and z is not None and abs(a-z) < 1e-12),
                                   f"Metrica salva divergiu: {co}/{nome}/{pid}/{k}")
                if len(auto["bounding_boxes"]) > 67:
                    resultados["hibrido67"] = resultados["regra"]
                elif "layoutreader_pronto" in resultados:
                    resultados["hibrido67"] = resultados["layoutreader_pronto"]
                target = alvo(resultados, metodos) if completo else None
                if completo:
                    resultados["oraculo_roteamento"] = resultados[metodos[target]]
                row = {"fingerprint": fp, "page_id": pid, "uf": obj["uf"], "coorte": co,
                       "features": features, "alvo": target, "unidades": len(auto["bounding_boxes"]),
                       "resultados": resultados, "completo": completo, "cobertura_palavras": 1.}
                gravar(path, row)
            for m in metodos:
                if m not in ordens:
                    ausencias[co][m+"_sem_predicao"] += 1
            rows.append(row)
        print(f"{co}: {sum(r['coorte'] == co for r in rows)} páginas; ausências {dict(ausencias[co])}", flush=True)
    return rows, ausencias


def criar_modelo(nome, semente):
    if nome == "arvore_rasa":
        return DecisionTreeClassifier(**PARAMETROS[nome], random_state=semente)
    if nome == "logistica":
        return make_pipeline(StandardScaler(), LogisticRegression(**PARAMETROS[nome], random_state=semente))
    import lightgbm as lgb
    return lgb.LGBMClassifier(**PARAMETROS[nome], random_state=semente)


def ajustar_prever(nome, semente, treino, teste, nomes_features):
    exigir(treino and teste, "Fold sem treino/teste")
    exigir(not {r["uf"] for r in treino} & {r["uf"] for r in teste}, "Vazamento de veiculo")
    exigir(not {r["page_id"] for r in treino} & {r["page_id"] for r in teste}, "Vazamento de pagina")
    y = np.array([r["alvo"] for r in treino])
    if len(set(y)) == 1:
        return [int(y[0])]*len(teste), "Folha constante: classe "+str(int(y[0]))
    modelo = criar_modelo(nome, semente)
    modelo.fit(np.array([r["features"] for r in treino]), y)
    probs = modelo.predict_proba(np.array([r["features"] for r in teste]))
    classes = np.asarray(modelo.classes_)
    # classes_ crescente: empate probabilistico tambem prefere a regra.
    escolhas = [int(classes[i]) for i in np.argmax(probs, axis=1)]
    texto = export_text(modelo, feature_names=nomes_features, decimals=4) if nome == "arvore_rasa" else None
    return escolhas, texto


def validacao(rows, metodos, disponiveis, assinatura, nomes_features):
    completos = [r for r in rows if r["completo"]]
    folds, predicoes = [], {}
    for modo in ("cv_conjunta", "transferencia_ajuste"):
        for uf in sorted({r["uf"] for r in completos}):
            teste = [r for r in completos if r["uf"] == uf]
            treino = [r for r in completos if r["uf"] != uf and
                      (modo == "cv_conjunta" or r["coorte"] in AJUSTE)]
            if not treino:
                continue
            for nome in disponiveis:
                for seed in SEMENTES:
                    vigiar()
                    chave = c.digest([assinatura, modo, uf, nome, seed,
                                      [r["fingerprint"] for r in treino], [r["fingerprint"] for r in teste]])
                    path = OUT / "cache/folds" / (chave+".json")
                    if path.exists():
                        fold = b.ler(path)
                        exigir(fold["fingerprint"] == chave, "Cache de fold alterado")
                    else:
                        escolhas, texto = ajustar_prever(nome, seed, treino, teste, nomes_features)
                        fold = {"fingerprint": chave, "modo": modo, "uf": uf, "metodo": nome,
                                "semente": seed, "treino_n": len(treino),
                                "treino_veiculos": sorted({r["uf"] for r in treino}),
                                "teste": [[r["coorte"], r["page_id"]] for r in teste],
                                "escolhas": escolhas, "arvore": texto}
                        gravar(path, fold)
                    exigir(uf not in fold["treino_veiculos"], "Veiculo vazou no cache")
                    for r, escolha in zip(teste, fold["escolhas"]):
                        predicoes[(modo, nome, seed, r["coorte"], r["page_id"])] = metodos[escolha]
                    folds.append(fold)
            print(f"{modo}: veículo {uf}; treino {len(treino)}, teste {len(teste)}", flush=True)
    # Arvore de v4/RN para o texto, sem metricas de treino nem escolha pelo resultado.
    treino = [r for r in completos if r["coorte"] in AJUSTE]
    y = [r["alvo"] for r in treino]
    arvore = criar_modelo("arvore_rasa", SEMENTES[0])
    arvore.fit([r["features"] for r in treino], y)
    texto = export_text(arvore, feature_names=nomes_features, decimals=4)
    return predicoes, folds, texto


def materializar(rows, predicoes, modo, disponiveis, seed):
    out = []
    for row in rows:
        resultados = dict(row["resultados"])
        if row["completo"]:
            for nome in disponiveis:
                escolhido = predicoes.get((modo, nome, seed, row["coorte"], row["page_id"]))
                if escolhido is not None:
                    resultados[nome] = resultados[escolhido]
        out.append({**row, "resultados": resultados})
    return out


def resumir(rows, nomes):
    resumo = {}
    for nome in nomes:
        rs = [r for r in rows if nome in r["resultados"]]
        if not rs:
            resumo[nome] = {"n": 0, "metricas": {k: None for k in METRICAS}, "contrastes": {}}
            continue
        W = b.PESOS_CLUSTER(rs)
        metricas = {k: o.media(r["resultados"][nome]["metricas"][k] for r in rs) for k in METRICAS}
        s = {"n": len(rs), "veiculos": len({r["uf"] for r in rs}), "metricas": metricas,
             "completo": len(rs) == len(rows), "contrastes": {}, "cobertura": 1.}
        for base in BASES:
            pares = [r for r in rs if base in r["resultados"]]
            if not pares:
                continue
            pesos = W if len(pares) == len(rs) else b.PESOS_CLUSTER(pares)
            contrastes = {}
            for k in METRICAS:
                ds = [None if r["resultados"][nome]["metricas"][k] is None or
                      r["resultados"][base]["metricas"][k] is None else
                      r["resultados"][nome]["metricas"][k]-r["resultados"][base]["metricas"][k] for r in pares]
                por_uf = {uf: o.media(d for r, d in zip(pares, ds) if r["uf"] == uf)
                          for uf in sorted({r["uf"] for r in pares})}
                sinal = -1 if k in ("quebras", "quebras_mil") else 1
                contrastes[k] = {**e.media_ic(ds, pesos), "por_veiculo": por_uf,
                    "wilcoxon_veiculo": e.pratt([v for v in por_uf.values() if v is not None]),
                    "melhor": sum(d is not None and sinal*d > 1e-12 for d in ds),
                    "igual": sum(d is not None and abs(d) <= 1e-12 for d in ds),
                    "pior": sum(d is not None and sinal*d < -1e-12 for d in ds)}
            classes = {t: dict(reparos=0, regressoes=0) for t in c.TIPOS}
            for r in pares:
                novo, antes = r["resultados"][nome], r["resultados"][base]
                exigir(novo["tipos"] == antes["tipos"], "Sucessores de referencias diferentes")
                certos, base_certos = set(novo["certos"]), set(antes["certos"])
                for i in certos-base_certos:
                    classes[novo["tipos"][i]]["reparos"] += 1
                for i in base_certos-certos:
                    classes[novo["tipos"][i]]["regressoes"] += 1
            s["contrastes"][base] = {"n": len(pares), "metricas": contrastes, "classes": classes,
                "reparos": sum(v["reparos"] for v in classes.values()),
                "regressoes": sum(v["regressoes"] for v in classes.values())}
        resumo[nome] = s
    return resumo


def avaliar_criterio(resumos, nome):
    s = resumos["conjunto"][nome]
    d = s["contrastes"]["hibrido67"]["metricas"]["quebras"]
    limites = {co: resumos[co][nome]["contrastes"]["hibrido67"]["metricas"]["quebras"]["media"]
               for co in COORTES if resumos[co][nome]["n"]}
    return {"delta_negativo": d["media"] < 0, "ic95_abaixo_zero": d["ic"][1] < 0,
            "nenhuma_bancada_piora_mais_05": all(v <= .5 for v in limites.values()),
            "delta_por_bancada": limites,
            "go": d["media"] < 0 and d["ic"][1] < 0 and all(v <= .5 for v in limites.values())}


def tabela_metricas(linhas, ss, nomes):
    linhas += ["| Método | n | τ palavras | Quebras/pág | Quebras/1.000 | Fid12 | Sucessor |",
               "|---|---:|---:|---:|---:|---:|---:|"]
    for nome in nomes:
        s = ss[nome]
        m = s["metricas"]
        linhas.append(f"| {nome} | {s['n']} | "+" | ".join(o.f(m[k], 6) for k in METRICAS)+" |")
    linhas += ["", "| Método | Base | n pareado | Δ quebras [IC95 veículo] | p veículo | Melhor/igual/pior | Reparos/regressões |",
               "|---|---|---:|---:|---:|---:|---:|"]
    for nome in nomes:
        for base, cp in ss[nome]["contrastes"].items():
            d = cp["metricas"]["quebras"]
            linhas.append(f"| {nome} | {base} | {cp['n']} | {o.ic(d)} | {o.f(d['wilcoxon_veiculo']['p'], 6)} | "
                          f"{d['melhor']}/{d['igual']}/{d['pior']} | {cp['reparos']}/{cp['regressoes']} |")


def publicar(an, rows, ausencias, metodos, info, disponiveis, indisponiveis,
             predicoes, folds, arvore, manifesto):
    nomes = [*metodos, "hibrido67", *MODELOS, "oraculo_roteamento"]
    modos, registros = {}, {}
    for modo in ("cv_conjunta", "transferencia_ajuste"):
        rs = materializar(rows, predicoes, modo, disponiveis, SEMENTES[0])
        modos[modo] = {co: resumir([r for r in rs if r["coorte"] == co], nomes) for co in COORTES}
        # Mesmas observacoes das bancadas; sobreposicoes historicas explicitadas.
        modos[modo]["conjunto"] = resumir([r for r in rs if r["completo"]], nomes)
        for co, ss in modos[modo].items():
            for nome, s in ss.items():
                chave = f"{co}/{nome}" if modo == "cv_conjunta" else f"{co}/{nome}_transferencia"
                # Uma media parcial nao representa a bancada inteira no registro.
                disponivel = bool(s["n"] and s.get("completo"))
                registros[chave] = {"tau": s["metricas"]["tau"] if disponivel else None,
                    "quebras": s["metricas"]["quebras"] if disponivel else None,
                    "sucessor": s["metricas"]["sucessor_linhas"] if disponivel else None}
    primario = modos["cv_conjunta"]
    criterios = {nome: avaliar_criterio(primario, nome) for nome in disponiveis}
    aprovados = [m for m, v in criterios.items() if v["go"]]
    veredito = ("GO exploratório: "+", ".join(aprovados)) if aprovados else "NÃO GO nos seletores executados; manter o híbrido 67 congelado"
    if indisponiveis:
        veredito += "; comparação completa PENDENTE ("+", ".join(indisponiveis)+")"
    elegiveis = [r for r in rows if r["completo"]]
    pids = collections.Counter(r["page_id"] for r in elegiveis)
    l = [f"1. Âncora reproduzida: τ {o.f(an['tau'], 6)}; {o.f(an['quebras'], 6)} quebras/página.",
         f"2. CV conjunta: {len(elegiveis)} observações, {len(pids)} páginas distintas, {len({r['uf'] for r in elegiveis})} veículos; leave-one-vehicle-out.",
         "3. Veredito E005: "+veredito+".",
         "4. Métodos roteáveis: "+", ".join(metodos)+"; E004: "+info["estado"]+".",
         "5. RN: "+str(sum(r["coorte"] == "validacao_silver" and r["completo"] for r in rows))+" páginas com todos os candidatos; ausências explícitas, sem executar ordenadores.",
         "6. Golden_v3_novo já foi consultado em rodadas anteriores; análise exploratória, sem abrir ou avaliar teste cego.",
         "", "# E005 — seletor de método por página", "", "## Protocolo congelado e alcance", "",
         "Todos os números e este texto são escritos pelo script. Fontes, versões, parâmetros e hashes em `cache/manifesto.json`; resultados completos, folds, contrastes por veículo e classes em `cache/estado.json`. CPU, um processo, quatro threads, num_workers=0. Nenhum PDF, anotação original ou dado do parceiro é aberto.", "",
         "A régua é importada de `corretor_de_transicoes.preparar_avaliacao/medir`, `bancada_ordenadores` e `erros_ponta_a_ponta`. Mantêm-se linhas + átomos ls3, expansão interna canônica e todas as palavras. Quebras/1.000 usa o denominador da régua existente (palavras-ouro); não é apresentado como novo denominador de transições. Fid12 é integral. Features usam somente dados automáticos e concordância dos sucessores (incluindo FIM). A partição geométrica e os desempates usam `ordem_entrada`, random.Random(f'entrada-{page_id}'). Alvo é o menor número de quebras; empate escolhe regra, depois a ordem fixa dos candidatos, sem desempate por τ.", "",
         "A CV conjunta solicitada reúne as bancadas de desenvolvimento, com parâmetros fixados no código antes da execução. Nenhum parâmetro, limiar, semente ou checkpoint é escolhido em v3/silver. Rótulos desses conjuntos entram no treino dos outros folds nesta análise conjunta, portanto seus resultados conjuntos NÃO são transferência externa independente. A análise adicional `transferencia_ajuste` treina só em golden_v4 + RN disponível e exclui o veículo avaliado também desse treino. Nenhum fold vê qualquer página ou PDF do veículo de destino, inclusive suas ocorrências nas outras bancadas.", "",
         f"Sobreposição histórica preservada: {sum(n-1 for n in pids.values())} observações repetem page_id entre bancadas. O agregado usa as observações solicitadas (mesmo peso por observação); não são amostras independentes. Bootstrap e folds agrupam todas as ocorrências pelo mesmo veículo. Há referências humanas/silver diferentes para parte dessas páginas; isso pode produzir rótulos conflitantes.", "",
         "IC95 percentil por veículo: "+str(b.NBOOT)+" reamostras, mesma função da bancada. Wilcoxon bilateral Pratt sobre diferenças médias por veículo, descritivo; nenhuma decisão depende de p. Semente primária "+str(SEMENTES[0])+" congelada; as demais medem sensibilidade, sem selecionar semente. Critério do cartão: Δ quebras < 0 contra híbrido 67 na CV conjunta, IC95 inteiro < 0, nenhuma bancada piorando > 0,5 quebra/página. Não se acrescenta o critério geral de 10% ao cartão E005.", "",
         "E004: "+info["estado"]+". Por solicitação explícita nesta retomada, a seleção congelada do grafo concluído entra como candidato de roteamento mesmo se seu critério individual resultar NÃO GO. Isso testa seleção por página, sem mudar o critério do E005 ou adotar o grafo isoladamente. E004 pendente continua excluído, sem substituição por estimativa.", "",
         "Dependências indisponíveis: "+(json.dumps(indisponiveis, ensure_ascii=False) if indisponiveis else "nenhuma")+". Não se substitui LightGBM por outro algoritmo. Depois de disponibilizar a dependência no venv, repetir o comando refaz a comparação com a nova versão de ambiente registrada.", "",
         "Configurações fixas: `"+json.dumps(PARAMETROS, ensure_ascii=False)+"`. Sem pesos de classe, sem ajuste de limiar de probabilidade e sem busca de hiperparâmetros. StandardScaler da logística é ajustado apenas no treino de cada fold. A árvore tem profundidade máxima 3; LightGBM tem 7 folhas e 50 árvores. Classes ausentes no treino não podem ser previstas; fold de uma classe usa a constante correspondente.", "",
         "## CV conjunta — agregado exploratório", ""]
    tabela_metricas(l, primario["conjunto"], nomes)
    l += ["", "Critério por seletor: `"+json.dumps(criterios, ensure_ascii=False)+"`."]
    for co in COORTES:
        l += ["", "## "+co+" — CV conjunta", "",
              f"Total: {sum(r['coorte'] == co for r in rows)} páginas; ausências: `"+json.dumps(ausencias[co], ensure_ascii=False)+"`. Médias parciais têm o n explícito e ficam nulas no resumo de registro.", ""]
        tabela_metricas(l, primario[co], nomes)
        l += ["", "Reparos/regressões de sucessores por classe (regra; híbrido67):", "",
              "| Método | Classe | vs regra | vs híbrido67 |", "|---|---|---:|---:|"]
        for nome in [*disponiveis, "oraculo_roteamento"]:
            for tipo in c.TIPOS:
                valores = []
                for base in BASES:
                    cp = primario[co][nome]["contrastes"].get(base)
                    v = cp["classes"][tipo] if cp else None
                    valores.append(f"{v['reparos']}/{v['regressoes']}" if v else "indisponível")
                l.append(f"| {nome} | {c.ROTULOS[tipo]} | "+" | ".join(valores)+" |")
    l += ["", "## Transferência com treino restrito ao ajuste", "",
          "Cada veículo é excluído de todo o treino v4/RN. As médias por bancada mantêm seus próprios gabaritos. A CV conjunta não escolhe o modelo usado nesta tabela.", ""]
    for co in COORTES:
        l += ["", "### "+co, ""]
        tabela_metricas(l, modos["transferencia_ajuste"][co], ["hibrido67", *MODELOS, "oraculo_roteamento"])
    l += ["", "## Sensibilidade às sementes", "",
          "Média ± desvio padrão amostral das métricas agregadas entre sementes; não é IC e não escolhe o vencedor.", "",
          "| Modo | Método | Quebras/pág média ± dp | τ média ± dp |", "|---|---|---:|---:|"]
    sensibilidade = {}
    for modo in modos:
        for nome in disponiveis:
            valores = []
            for seed in SEMENTES:
                rs = materializar(elegiveis, predicoes, modo, [nome], seed)
                valores.append({k: o.media(r["resultados"][nome]["metricas"][k] for r in rs) for k in ("quebras", "tau")})
            sensibilidade[modo+"/"+nome] = valores
            cel = lambda k: o.f(statistics.mean(v[k] for v in valores), 6)+" ± "+o.f(statistics.stdev(v[k] for v in valores), 6)
            l.append(f"| {modo} | {nome} | {cel('quebras')} | {cel('tau')} |")
    l += ["", "## Árvore rasa para o TCC", "",
          "Árvore ajustada somente em v4/RN com candidatos disponíveis, semente primária. É uma descrição do modelo de implantação; suas métricas de treino não são reportadas como validação. As árvores efetivamente avaliadas fora de veículo vêm a seguir e ficam também nos caches dos folds.", "",
          "Classes: `"+json.dumps(dict(enumerate(metodos)), ensure_ascii=False)+"`.", "", "```text", arvore, "```", "",
          "Features: unidades = linhas e átomos; colunas = máximo local informado pela regra; margem = marca/cabeçalho/rodapé entre unidades de texto; transversais = pontes geométricas; largura média = extensão horizontal dos grupos de coluna normalizada pela largura da página; concordância = fração de decisões de sucessor idênticas. Todas são calculadas antes de consultar o gabarito."]
    for fold in folds:
        if fold["metodo"] == "arvore_rasa" and fold["semente"] == SEMENTES[0] and fold["modo"] == "cv_conjunta":
            l += ["", "### Árvore sem o veículo "+fold["uf"], "", "```text", fold["arvore"], "```"]
    l += ["", "## Limitações e veredito", "", veredito+".", "",
          "O limiar 67 e a própria regra já foram desenvolvidos em v4: seus controles não se tornam inéditos com LOOV. Golden_v3_novo já foi consultado em rodadas anteriores. Referência silver é ruidosa, sobretudo dentro de átomos; o oráculo apenas escolhe as ordens existentes, sem consertá-las. Seu teto usa o gabarito e é inalcançável como preditor. RN sem LayoutReader não permite alvo, features de concordância ou roteamento perfeito completos; páginas RN densas têm somente híbrido parcial igual à regra. Não se preenche a ausência escolhendo regra nas páginas leves.", "",
          "Cobertura de palavras é integral nas ordens avaliadas, conferida por IDs/expansões da régua; não mede palavras ausentes da camada digital. Reporta-se a página inteira, com diagnóstico geométrico de margens e outras classes. Não existe aqui uma referência humana independente só do corpo; o diagnóstico de classe não deve ser citado como métrica completa do corpo. IC por veículo com poucos grupos (especialmente silver) tem baixa resolução. Os testes são exploratórios e não substituem o confirmatório por PDF. Não há nova avaliação do teste cego.", "",
          "Retomada: `venv/Scripts/python.exe -B orquestracao/analises/e005_seletor.py`; verificação sem alterar saídas: mesmo comando com `--conferir`. Apenas caches cuja assinatura de código, fontes, parâmetros e versões coincide são reaproveitados.", ""]
    for nome, sha in FONTES.items():
        exigir(c.sha(RAIZ / nome) == sha, "Fonte mudou durante a execucao: "+nome)
    estado = {"ancora": an, "manifesto": manifesto, "metodos": metodos, "e004": info,
              "indisponiveis": indisponiveis, "criterios": criterios, "veredito": veredito,
              "ausencias": ausencias, "resumos": modos, "sensibilidade": sensibilidade,
              "folds": folds, "arvore_ajuste": arvore}
    gravar(OUT / "cache/estado.json", estado)
    gravar(OUT / "RELATORIO.md", "\n".join(l))
    gravar(OUT / "resumo_registro.json", registros)
    gravar(OUT / "cache/integridade.json", {
        "fontes": FONTES,
        "produtos": {str(p.relative_to(OUT)): c.sha(p) for p in
                     [OUT / "cache/estado.json", OUT / "RELATORIO.md", OUT / "resumo_registro.json"]}})
    print(veredito, flush=True)


def autoteste():
    exigir(alvo({"regra": {"metricas": {"quebras": 2}}, "lr": {"metricas": {"quebras": 2}}}, ["regra", "lr"]) == 0,
           "Empate deve escolher regra")
    ws = [["abc", 10., 10., 30., 20.], ["def", 10., 30., 30., 40.]]
    auto = {"page_id": "sintetico/a.pdf#p0", "dimensions": {"width": 100., "height": 100.},
            "bounding_boxes": [{"id": f"u{i}", "bbox": w[1:], "ks": [i], "text": w[0], "tipo": "texto"} for i, w in enumerate(ws)]}
    ordens = {"regra": ["u0", "u1"], "lr": ["u1", "u0"]}
    v, ctx = extrair_features(auto, ws, ordens, ["regra", "lr"])
    z, _ = extrair_features({**auto, "ordens": {"stream": ["veneno"]}, "gt_w": [999]}, ws, ordens, ["regra", "lr"])
    exigir(v == z and len(v) == len(FEATURES) and v[-1] == 0., "Features leem ouro ou concordancia incorreta")
    exigir(len(ctx["entrada"]) == 2, "Entrada embaralhada ausente")
    antigo = o.PROTEGIDOS
    try:
        o.PROTEGIDOS = {auto["page_id"]}
        try:
            o.permitido(auto["page_id"])
        except ValueError:
            pass
        else:
            raise ValueError("Lock cego nao bloqueou pagina sintetica")
    finally:
        o.PROTEGIDOS = antigo
    print("Autoteste: empate, features sem ouro, concordância, entrada e lock OK", flush=True)


def main():
    global PRAZO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoteste", action="store_true")
    parser.add_argument("--somente-ancora", action="store_true")
    parser.add_argument("--conferir", action="store_true")
    parser.add_argument("--max-minutos", type=float, default=0.)
    args = parser.parse_args()
    o.ASSINATURA_LOCK, o.PROTEGIDOS = o.ler_lock()
    if args.conferir:
        integridade = b.ler(OUT / "cache/integridade.json")
        for nome, sha in integridade["fontes"].items():
            exigir(c.sha(RAIZ / nome) == sha, "Fonte alterada: "+nome)
        for nome, sha in integridade["produtos"].items():
            exigir(c.sha(OUT / nome) == sha, "Produto alterado: "+nome)
        print("Integridade: fontes, relatório, estado e resumo OK", flush=True)
        return
    if args.max_minutos:
        PRAZO = time.monotonic()+60*args.max_minutos
    if args.autoteste:
        autoteste()
    with trava():
        an = o.ancora()
        if args.somente_ancora:
            return
        for p in set(b.DEP_PATHS) | {Path(__file__), Path(c.__file__), Path(o.__file__),
                                   RAIZ / "data/processed/splits.json"}:
            fonte(p)
        if o.LOCK.exists():
            fonte(o.LOCK)
        splits = b.ler(RAIZ / "data/processed/splits.json")
        for co in c.HUMANAS:
            fonte(b.UNIDADES / "bancadas" / (co+".jsonl"))
        for part in ("validacao", "teste"):
            for uf in splits[part]:
                for suf in (".jsonl", ".palavras.jsonl"):
                    fonte(b.UNIDADES / "linhas" / (uf+suf))
        preds, metodos, info = salvos()
        historico = b.ler(fonte(b.JSON))["resultados"]
        antigas = {co: {nome: {r["page_id"]: r["metricas"] for r in
                   historico.get(arquivo+"__linhas__"+co, {}).get("paginas", [])}
                   for nome, arquivo in (("regra", "regra_colunas"),
                                         ("layoutreader_pronto", "layoutreader_pronto"))}
                   for co in COORTES}
        del historico
        nomes_features = list(FEATURES)
        if len(metodos) > 2:
            nomes_features += ["concordancia_"+a+"_"+z for a, z in list(itertools.combinations(metodos, 2))[1:]]
        disponiveis, indisponiveis = list(MODELOS), {}
        versoes = {"python": sys.version, "numpy": np.__version__, "sklearn": sklearn.__version__}
        if importlib.util.find_spec("lightgbm") is None:
            disponiveis.remove("lightgbm")
            indisponiveis["lightgbm"] = "Pacote ausente no venv; pip retornou 'No matching distribution found for lightgbm'; nenhum wheel local encontrado."
            versoes["lightgbm"] = None
        else:
            import lightgbm
            versoes["lightgbm"] = lightgbm.__version__
        manifesto = {"fontes": FONTES, "lock_cego_sha256": o.ASSINATURA_LOCK, "ancora": an,
                     "features": nomes_features, "metodos": metodos, "parametros": PARAMETROS,
                     "sementes": SEMENTES, "versoes": versoes, "cpu": True, "processos": 1,
                     "num_workers": 0, "threads": 4}
        assinatura = c.digest(manifesto)
        manifesto["assinatura"] = assinatura
        gravar(OUT / "cache/manifesto.json", manifesto)
        rows, ausencias = preparar(preds, metodos, assinatura, antigas)
        predicoes, folds, arvore = validacao(rows, metodos, disponiveis, assinatura, nomes_features)
        publicar(an, rows, ausencias, metodos, info, disponiveis, indisponiveis,
                 predicoes, folds, arvore, manifesto)


if __name__ == "__main__":
    main()
