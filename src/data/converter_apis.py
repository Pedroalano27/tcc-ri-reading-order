"""Converte os layouts locais do Azure e Google para paginas do protocolo.

Permite comparar a segmentacao comercial com o extrator C, ainda nao validado,
nas mesmas paginas, sem alterar referencia, splits ou colecoes existentes.
Nao acessa APIs: le os dois lotes Azure delimitados por NOME DO ARQUIVO e o
document (1).json do Google. O Boletim 7621 nao participa desta conversao.

Azure: cada paragrafo vira um bloco; poligonos em polegadas recebem fator 72.
Google: usa folhas de texto, substituindo cada tabela inteira por um bloco
(celulas na ordem de linhas e colunas emitida). Pais com filhos nao sao emitidos.
As paginas Google sao identificadas por cobertura de trigramas de texto contra
todas as paginas do PDF; o ranking completo fica no relatorio de auditoria.
Nao aplica filtros de quantidade de blocos, nem corrige ou recorta caixas.

Uso na raiz: venv\\Scripts\\python.exe src\\data\\converter_apis.py
Cria blocos_api_azure e blocos_api_docai em data/processed e imprime a tabela.
Arquivos existentes identicos sao preservados; divergencias impedem a gravacao.
O relatorio _comparacao_segmentacao.json guarda fontes, hashes, escalas, ranking,
estatisticas por pagina, papeis e validacoes para reproducao pelo orquestrador.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Evita criar caches fora do escopo autorizado durante os imports do projeto.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pdfplumber

from src.data.extrator import estimar_colunas, palavras_da_pagina, segmentar, xycut
from src.data.reextrair import qualidade
from src.eval.protocolo import RAIZ_PROJETO, iterar_paginas

RAIZ = Path(RAIZ_PROJETO)
RAW = RAIZ / "data/raw"
PROCESSADOS = RAIZ / "data/processed"
RJ = "official_diary_rj"
JAPERI = "official_diary_rj_japeri"
PDF_RJ = "Parte I (Poder Executivo)_2021-06-10.pdf"
BASE_JAPERI = RAW / JAPERI
GOOGLE = BASE_JAPERI / "diarios_avaliados_apis_pagas/Google Doc AI Tests/document (1).json"
AZURE = [BASE_JAPERI / "json_atos_japeri" / f"resultado_azure_lote_layout.{ext}"
         for ext in ("jsonl", "txt")]
SAIDA_AZURE = PROCESSADOS / "blocos_api_azure"
SAIDA_GOOGLE = PROCESSADOS / "blocos_api_docai"


def exigir(condicao, mensagem):
    """Falha tambem sob Python otimizado, antes de publicar dados invalidos."""
    if not condicao:
        raise ValueError(mensagem)


def proveniencia(caminho):
    return {"arquivo": caminho.relative_to(RAIZ).as_posix(),
            "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest()}


def ler_azure(caminho, ignorados):
    """Decodifica objetos multilinha, separadores e o rodape de tempo do lote."""
    texto = caminho.read_text(encoding="utf-8-sig")
    partes = re.split(r"^NOME DO ARQUIVO:[ \t]*([^\r\n]+)\r?$", texto, flags=re.M)
    exigir(len(partes) > 1 and not partes[0].strip(), f"Cabecalho invalido: {caminho}")
    for nome, corpo in zip(partes[1::2], partes[2::2]):
        nome, corpo = nome.strip(), corpo.lstrip()
        if corpo.startswith("Erro na consulta de JAPERI-5174-26-DE-JULHO-2022.pdf (429)"):
            ignorados.append({"entrada": caminho.relative_to(RAIZ).as_posix(),
                              "pdf": nome, "motivo": corpo.splitlines()[0]})
            continue
        objeto, fim = json.JSONDecoder().raw_decode(corpo)
        sobra = corpo[fim:].strip("= \t\r\n")
        exigir(not sobra or re.fullmatch(
            r"PROCESSAMENTO TOTAL CONCLU.DO EM: \d+ minuto\(s\) e [\d.]+ segundo\(s\)\.", sobra),
            f"Sobra inesperada depois de {nome}")
        yield nome, objeto["analyzeResult"]


def bloco(texto, caixa, papel=""):
    exigir(len(caixa) == 4 and all(math.isfinite(v) for v in caixa), "Caixa invalida")
    return dict(zip(("x0", "top", "x1", "bottom"), caixa), texto=texto, papel=papel)


def registro(uf, arquivo, numero, pagina_pdf, blocos, n_palavras=None):
    """Replica a permutacao de IDs e a serializacao de processar_pagina, sem filtro."""
    page_id = f"{uf}/{arquivo}#p{numero}"
    perm = list(range(len(blocos)))
    random.Random(page_id).shuffle(perm)
    ids = [f"b{k}" for k in perm]
    indices = list(range(len(blocos)))
    caixas = [{"id": ids[i], "text": b["texto"], "papel": b.get("papel", ""),
               "bbox": [round(b[k], 1) for k in ("x0", "top", "x1", "bottom")]}
              for i, b in enumerate(blocos)]
    caixas.sort(key=lambda b: int(b["id"][1:]))
    return {
        "page_id": page_id, "uf": uf, "arquivo": arquivo, "pagina": numero,
        "dimensions": {"width": round(float(pagina_pdf.width), 1),
                       "height": round(float(pagina_pdf.height), 1)},
        "bounding_boxes": caixas,
        "ordens": {
            "stream": [ids[i] for i in sorted(indices, key=lambda i: blocos[i].get("s", i))],
            "naive": [ids[i] for i in sorted(indices, key=lambda i: (blocos[i]["top"], blocos[i]["x0"]))],
            "xycut": [ids[i] for i in xycut(indices, blocos)],
        },
        "stats": {"n_blocos": len(blocos),
                  "n_palavras": (sum(len(b["texto"].split()) for b in blocos)
                                 if n_palavras is None else n_palavras),
                  "n_colunas": estimar_colunas(blocos)},
    }


def validar(registros):
    vistos = set()
    for r in registros:
        pid, caixas = r["page_id"], r["bounding_boxes"]
        exigir(pid not in vistos, f"Pagina duplicada: {pid}")
        vistos.add(pid)
        exigir(pid == f"{r['uf']}/{r['arquivo']}#p{r['pagina']}", f"Identidade invalida: {pid}")
        ids = [b["id"] for b in caixas]
        exigir(len(set(ids)) == len(ids), f"IDs duplicados: {pid}")
        exigir(set(ids) == {f"b{k}" for k in range(len(ids))}, f"IDs incompletos: {pid}")
        for nome in ("stream", "naive", "xycut"):
            exigir(Counter(r["ordens"][nome]) == Counter(ids), f"Ordem {nome} invalida: {pid}")
        w, h = r["dimensions"]["width"], r["dimensions"]["height"]
        for b in caixas:
            x0, y0, x1, y1 = b["bbox"]
            exigir(all(math.isfinite(v) for v in b["bbox"])
                   and -1 <= x0 < x1 <= w + 1 and -1 <= y0 < y1 <= h + 1,
                   f"Caixa fora da pagina ou degenerada: {pid} {b}")
        exigir(r["stats"]["n_blocos"] == len(caixas), f"Contagem invalida: {pid}")
    return {"paginas": len(registros), "blocos": sum(len(r["bounding_boxes"]) for r in registros),
            "ordens_verificadas": 3 * len(registros), "tolerancia_caixas_pt": 1,
            "erros": 0}


def converter_azure():
    registros, ignorados, documentos, escalas = [], [], [], []
    for entrada in AZURE:
        for nome, analise in ler_azure(entrada, ignorados):
            uf = RJ if nome == PDF_RJ else JAPERI
            arquivo = nome if uf == RJ else f"diarios_avaliados_apis_pagas/TEMP/{nome}"
            caminho = RAW / uf / arquivo
            grupos = {p["pageNumber"]: [] for p in analise["pages"]}
            for paragrafo in analise["paragraphs"]:
                regioes = paragrafo.get("boundingRegions", [])
                exigir(len(regioes) == 1, f"Paragrafo sem regiao unica: {nome}")
                regiao = regioes[0]
                poligono = regiao["polygon"]
                exigir(len(poligono) == 8, f"Poligono inesperado: {nome}")
                xs, ys = poligono[::2], poligono[1::2]
                grupos[regiao["pageNumber"]].append(bloco(
                    paragrafo["content"], [72 * min(xs), 72 * min(ys), 72 * max(xs), 72 * max(ys)],
                    paragrafo.get("role", "")))
            with pdfplumber.open(caminho) as pdf:
                documentos.append({**proveniencia(caminho), "entrada": entrada.relative_to(RAIZ).as_posix(),
                                   "paginas_pdf": len(pdf.pages), "paginas_api": len(grupos),
                                   "paragrafos": len(analise["paragraphs"])})
                for p in analise["pages"]:
                    exigir(p["unit"] == "inch", f"Unidade inesperada: {nome}")
                    numero = p["pageNumber"] - 1
                    pg = pdf.pages[numero]
                    w, h = float(pg.width), float(pg.height)
                    erros = [abs(w - 72 * p["width"]), abs(h - 72 * p["height"])]
                    exigir(max(erros) <= 1, f"Escala Azure diverge mais de 1 pt: {nome} {numero}")
                    r = registro(uf, arquivo, numero, pg, grupos[p["pageNumber"]])
                    registros.append(r)
                    escalas.append({"page_id": r["page_id"], "unit": p["unit"], "fator_aplicado": 72,
                                    "azure_inches": [p["width"], p["height"]], "pdf_pt": [w, h],
                                    "razao_pt_por_inch": [w / p["width"], h / p["height"]],
                                    "erro_absoluto_pt": erros})
            print(f"Azure: {nome}: {len(grupos)} paginas, {len(analise['paragraphs'])} paragrafos", flush=True)
    return registros, {"documentos": documentos, "ignorados": ignorados, "escalas": escalas}


def folhas_google(blocos, contagens):
    """Percorre em profundidade a ordem emitida; tabelas encerram a recursao externa."""
    for b in blocos:
        if "tableBlock" in b:
            contagens["tabelas"] += 1
            linhas = []
            for chave in ("headerRows", "bodyRows"):
                for linha in b["tableBlock"].get(chave, []):
                    celulas = []
                    for celula in linha["cells"]:
                        textos = [texto for _, texto, _ in folhas_google(celula.get("blocks", []), contagens)]
                        celulas.append(" ".join(textos))
                    linhas.append("\t".join(celulas))
            yield b, "\n".join(linhas), "table"
        elif "textBlock" in b:
            t = b["textBlock"]
            if t.get("blocks"):
                contagens["pais_nao_emitidos"] += 1
                yield from folhas_google(t["blocks"], contagens)
            else:
                contagens["folhas_texto_incluindo_celulas"] += 1
                if not t.get("text", "").strip():
                    contagens["folhas_sem_texto_incluindo_celulas"] += 1
                yield b, t.get("text", ""), t.get("type", "")
        else:
            raise ValueError(f"Tipo Google nao suportado: {b.keys()}")


def trigramas(texto):
    normal = "".join(c for c in unicodedata.normalize("NFKD", texto.casefold())
                     if not unicodedata.combining(c))
    palavras = re.findall(r"[a-z0-9]+", normal)
    return set(zip(palavras, palavras[1:], palavras[2:]))


def converter_google():
    documento = json.loads(GOOGLE.read_text(encoding="utf-8"))
    contagens = Counter()
    grupos = defaultdict(list)
    for b, texto, papel in folhas_google(documento["documentLayout"]["blocks"], contagens):
        span = b["pageSpan"]
        exigir(span["pageStart"] == span["pageEnd"], "Bloco Google atravessa paginas")
        exigir("normalizedVertices" in b.get("boundingBox", {}), "Bloco Google sem caixa normalizada")
        grupos[span["pageStart"]].append((b, texto, papel))
    exigir(set(grupos) == {p["pageNumber"] for p in documento["pages"]}, "Paginas Google sem blocos")
    registros, mapeamento = [], []
    with pdfplumber.open(RAW / RJ / PDF_RJ) as pdf:
        textos_pdf = []
        for n, p in enumerate(pdf.pages):
            textos_pdf.append(trigramas(p.extract_text() or ""))
            print(f"Identificacao Google: texto do PDF {n + 1}/{len(pdf.pages)}", flush=True)
        usados = set()
        for pagina_api, itens in sorted(grupos.items()):
            consulta = trigramas(" ".join(t for _, t, _ in itens))
            exigir(bool(consulta), f"Texto insuficiente no Google: {pagina_api}")
            ranking = sorted([
                {"pagina_pdf_base0": n, "trigramas_comuns": len(consulta & texto),
                 "cobertura": len(consulta & texto) / len(consulta)}
                for n, texto in enumerate(textos_pdf)
            ], key=lambda r: (-r["cobertura"], r["pagina_pdf_base0"]))
            melhor, segundo = ranking[:2]
            # Guarda de identificacao, sem funcao de filtro experimental.
            exigir(melhor["cobertura"] >= 0.5 and melhor["cobertura"] - segundo["cobertura"] >= 0.2,
                   f"Correspondencia Google ambigua: {pagina_api}: {ranking[:2]}")
            numero = melhor["pagina_pdf_base0"]
            exigir(numero not in usados, "Duas paginas Google casaram com a mesma pagina PDF")
            usados.add(numero)
            pg = pdf.pages[numero]
            blocos = []
            for b, texto, papel in itens:
                vs = b["boundingBox"]["normalizedVertices"]
                exigir(len(vs) >= 4, "Poligono Google incompleto")
                xs = [v.get("x", 0) * float(pg.width) for v in vs]
                ys = [v.get("y", 0) * float(pg.height) for v in vs]
                blocos.append(bloco(texto, [min(xs), min(ys), max(xs), max(ys)], papel))
            r = registro(RJ, PDF_RJ, numero, pg, blocos)
            registros.append(r)
            mapeamento.append({"pagina_api": pagina_api, "page_id": r["page_id"],
                               "trigramas_consulta": len(consulta), "ranking": ranking,
                               "trecho_google": " ".join(t for _, t, _ in itens)[:240]})
    return registros, {"estrutura": dict(contagens), "mapeamento": mapeamento,
                       "criterio": "Cobertura dos trigramas unicos Google no texto pdfplumber de cada pagina; "
                                   "minusculas, sem acentos, tokens [a-z0-9]+; melhor >= 0.5 e margem >= 0.2.",
                       "tabelas": "Um bloco por tabela, caixa do pai; texto das folhas das celulas, "
                                  "headerRows antes de bodyRows, sem emitir novamente as celulas.",
                       "pais": "Somente folhas: texto proprio de pais com filhos nao e emitido."}


def extrair_nosso(pedidos):
    grupos = defaultdict(list)
    for r in pedidos:
        grupos[(r["uf"], r["arquivo"])].append(r["pagina"])
    registros = []
    for (uf, arquivo), numeros in sorted(grupos.items()):
        with pdfplumber.open(RAW / uf / arquivo) as pdf:
            for n in sorted(set(numeros)):
                pg = pdf.pages[n]
                palavras = palavras_da_pagina(pg)
                registros.append(registro(uf, arquivo, n, pg, segmentar(palavras), len(palavras)))
                print(f"Extrator C (nao validado): {registros[-1]['page_id']}: "
                      f"{registros[-1]['stats']['n_blocos']} blocos", flush=True)
    return registros


def percentil(valores, p):
    """Interpolacao linear entre estatisticas de ordem, equivalente ao p95 usual."""
    v = sorted(valores)
    if not v:
        return None
    pos = (len(v) - 1) * p
    baixo, alto = math.floor(pos), math.ceil(pos)
    return v[baixo] + (v[alto] - v[baixo]) * (pos - baixo)


def resumir(fonte, amostra, registros):
    q = qualidade(registros)
    tamanhos = [len(b["text"].split()) for r in registros for b in r["bounding_boxes"]]
    n = len(tamanhos)
    return {"fonte": fonte, "amostra": amostra, "paginas": len(registros), "blocos": n,
            "blocos_por_pagina_media": statistics.mean(len(r["bounding_boxes"]) for r in registros),
            "blocos_por_pagina_mediana": statistics.median(len(r["bounding_boxes"]) for r in registros),
            "palavras_por_bloco_mediana": statistics.median(tamanhos) if n else None,
            "palavras_por_bloco_p95": percentil(tamanhos, 0.95),
            "palavras_por_bloco_maximo": max(tamanhos, default=0),
            "pct_blocos_1_palavra": 100 * sum(t == 1 for t in tamanhos) / max(1, n),
            "pct_blocos_ate_3_palavras": 100 * sum(t <= 3 for t in tamanhos) / max(1, n),
            "pct_blocos_sobrepostos": 100 * q["blocos_sobrepostos"] / max(1, n),
            "qualidade": q,
            "papeis": dict(sorted(Counter(b["papel"] for r in registros for b in r["bounding_boxes"]).items()))
                      if fonte != "Nosso C (nao validado)" else {},
            "fora_faixa_3_200": [{"page_id": r["page_id"], "n_blocos": len(r["bounding_boxes"])}
                                 for r in registros if not 3 <= len(r["bounding_boxes"]) <= 200]}


def imprimir_tabela(linhas):
    print("\n| Fonte / amostra | Paginas | Blocos | B/p media | B/p mediana | P/b mediana | P/b p95 | P/b max | % 1 palavra | % ate 3 | % sobrepostos |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    campos = ("paginas", "blocos", "blocos_por_pagina_media", "blocos_por_pagina_mediana",
              "palavras_por_bloco_mediana", "palavras_por_bloco_p95", "palavras_por_bloco_maximo",
              "pct_blocos_1_palavra", "pct_blocos_ate_3_palavras", "pct_blocos_sobrepostos")
    for r in linhas:
        valores = [str(r[k]) if isinstance(r[k], int) else f"{r[k]:.2f}".replace(".", ",") for k in campos]
        print(f"| {r['fonte']} / {r['amostra']} | " + " | ".join(valores) + " |")
        print(f"  Papeis: {json.dumps(r['papeis'], ensure_ascii=False)}; fora de 3 a 200: "
              f"{json.dumps(r['fora_faixa_3_200'], ensure_ascii=False)}")


def gravar_novos(arquivos):
    """Verifica todas as colisoes antes de criar; nunca sobrescreve um arquivo."""
    for caminho, texto in arquivos.items():
        if caminho.exists() and caminho.read_bytes() != texto.encode("utf-8"):
            raise FileExistsError(f"Saida existente divergente; nao sera alterada: {caminho}")
    for caminho, texto in arquivos.items():
        if not caminho.exists():
            caminho.parent.mkdir(parents=True, exist_ok=True)
            with caminho.open("xb") as f:
                f.write(texto.encode("utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    azure, auditoria_azure = converter_azure()
    google, auditoria_google = converter_google()
    ids_azure = {r["page_id"] for r in azure}
    ids_google = {r["page_id"] for r in google}
    exigir(ids_google == {r["page_id"] for r in azure if r["uf"] == RJ},
           "As paginas do RJ nao coincidem entre as APIs")
    nosso = extrair_nosso(azure)
    exigir({r["page_id"] for r in nosso} == ids_azure, "Amostra local diverge do Azure")
    fontes = {"Azure": azure, "Google": google, "Nosso C (nao validado)": nosso}
    validacoes = {fonte: validar(regs) for fonte, regs in fontes.items()}
    linhas = [resumir(fonte, "todas disponiveis", regs) for fonte, regs in fontes.items()]
    linhas += [resumir(fonte, "Estado RJ pareado", [r for r in regs if r["page_id"] in ids_google])
               for fonte, regs in fontes.items()]
    relatorio = {
        "fontes": [proveniencia(p) for p in [*AZURE, GOOGLE]],
        "codigo": [proveniencia(RAIZ / p) for p in
                   ("src/data/converter_apis.py", "src/data/extrator.py", "src/data/reextrair.py")],
        "versao_segmentador_local": "C, nao validada; palavras_da_pagina + segmentar ao vivo, sem filtros",
        "definicoes": {"palavras": "len(text.split()); agregacao por bloco, sem media de percentuais por pagina",
                       "p95": "Interpolacao linear na posicao (n-1)*0.95 dos tamanhos de todos os blocos",
                       "sobreposicao": "qualidade de reextrair.py: iw > 1 pt, ih > 1 pt, area/min(areas) >= 0.25",
                       "stream": "Ordem emitida pela API; nao altera a referencia do protocolo",
                       "comparabilidade": "Totais de Google e Azure cobrem amostras diferentes; usar Estado RJ pareado para tres fontes"},
        "azure": auditoria_azure, "google": auditoria_google, "validacoes": validacoes,
        "comparacao": linhas,
        "por_pagina": [{"page_id": r["page_id"], **resumir(fonte, "pagina", [r])}
                       for fonte, regs in fontes.items() for r in regs],
    }
    arquivos = {}
    for pasta, regs in ((SAIDA_AZURE, azure), (SAIDA_GOOGLE, google)):
        for uf in (RJ, JAPERI):
            selecionados = sorted((r for r in regs if r["uf"] == uf), key=lambda r: r["page_id"])
            arquivos[pasta / f"{uf}.jsonl"] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selecionados)
    arquivos[SAIDA_AZURE / "_comparacao_segmentacao.json"] = json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n"
    gravar_novos(arquivos)
    for pasta, esperados in ((SAIDA_AZURE, azure), (SAIDA_GOOGLE, google)):
        lidos = list(iterar_paginas([RJ, JAPERI], str(pasta)))
        exigir(sorted(lidos, key=lambda r: r["page_id"]) == sorted(esperados, key=lambda r: r["page_id"]),
               f"Leitura pelo protocolo diverge: {pasta}")
        print(f"Protocolo {pasta.name}: {json.dumps(validar(lidos))}")
    imprimir_tabela(linhas)
    print("\nIgnorados:", json.dumps(auditoria_azure["ignorados"], ensure_ascii=False))
    print("Maior erro de escala (pt):", max(max(e["erro_absoluto_pt"]) for e in auditoria_azure["escalas"]))
    print("Relatorio:", (SAIDA_AZURE / "_comparacao_segmentacao.json").relative_to(RAIZ).as_posix())


if __name__ == "__main__":
    main()
