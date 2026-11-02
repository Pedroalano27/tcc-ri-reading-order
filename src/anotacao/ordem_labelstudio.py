# -*- coding: utf-8 -*-
"""Anotação de ORDEM do Label Studio (projeto CEIA/Datapolicy) -> validação e formato do TCC.

A ordem é anotada no Label Studio com relações entre caixas (guia "Guia para anotação de
ordem", da Kamilla). Cada página vira UMA cadeia que passa por todas as caixas, e o nome da
relação diz o papel da ligação:

  continue     A -> B no mesmo fluxo de leitura
  skip_noise   A -> B quando A ou B é ruído (cabeçalho, rodapé, figura, propaganda)
  new_doc      A -> B quando A é a 1ª caixa de um documento
  end          A -> B quando B é a última caixa de um documento

e duas bordas marcadas na própria caixa (escolha por região, só nos extremos do documento):

  has_previous_page_start   o documento começou numa página anterior
  end_cut                   o documento continua na página seguinte
                            (o guia escreve end_continue_next_page)

A cadeia é exatamente o "sucessor" do LayoutLM do TCC: n caixas, n-1 ligações.

Comandos:
  validar     aponta, página a página, o que quebra a cadeia (ERRO), o que deixa a divisão em
              documentos inconsistente (DOC) e o que o guia deixa ambíguo (AVISO). Só lê.
  converter   grava no formato do golden do TCC (tarefas.jsonl + anotacoes.jsonl, como em
              data/golden/golden_v4/), um COCO e rótulos YOLO com as 16 classes do guia de
              layout. Página com ERRO não entra na ordem (entra marcada como inválida).

Entrada: o export JSON completo do Label Studio (lista de tarefas com "annotations"; o
JSON-MIN e o CSV não trazem as relações), uma pasta com um arquivo por anotação (como a
annotations-teste-ato/ da Kamilla) ou um arquivo desses.

Diferença para o extrair_documentos.py da Kamilla: aqui a direção da seta é respeitada. O
Label Studio grava "direction": "left" quando a seta foi invertida na tela; nesse caso a
ligação real é to_id -> from_id.

Uso:
  venv\\Scripts\\python.exe src\\anotacao\\ordem_labelstudio.py validar EXPORT [--anotador X]
  venv\\Scripts\\python.exe src\\anotacao\\ordem_labelstudio.py converter EXPORT --saida DIR
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

# 16 classes do guia de layout, na ordem de src/data/taxonomia_layout.py (LABELS_GUIA).
# Repetidas aqui para o script rodar sozinho; o import abaixo só confere que não divergiram.
GUIA = ("act", "act section", "paragraph", "signature", "heading", "id", "header", "footer",
        "table", "chart", "figure", "caption", "title", "section title",
        "sub section title", "unknown")
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
    from taxonomia_layout import GUIA as _GUIA_MODULO, GUIA_PARA_EXTRATOR
    assert tuple(_GUIA_MODULO) == GUIA, "GUIA divergiu de taxonomia_layout.py"
except ImportError:
    GUIA_PARA_EXTRATOR = None

RELACOES = {"continue", "skip_noise", "new_doc", "end"}
BORDA_INICIO = {"has_previous_page_start"}
BORDA_FIM = {"end_cut", "end_continue_next_page"}

# ruído da leitura: nunca pertence a um documento
RUIDO = {"header", "footer", "figure"}
# títulos de documento não normativo: podem ficar entre documentos (hierarquia)
HIERARQUIA = {"title", "section title", "sub section title"}
# de onde o guia diz que sai o new_doc (ato, título/subtítulo, ou o id que vem antes)
ABRE_DOCUMENTO = {"act", "id"} | HIERARQUIA

# gravidade dos problemas
ERRO, DOC, AVISO = "ERRO", "DOC", "AVISO"


# --- leitura -------------------------------------------------------------------------------

def _anotador(ann):
    """Nome legível de quem anotou, nos dois formatos de export."""
    nome = (ann.get("created_username") or "").strip()
    por = ann.get("completed_by")
    if isinstance(por, dict):
        nome = nome or por.get("email") or str(por.get("id"))
    elif por is not None and not nome:
        nome = f"usuario {por}"
    return nome or "desconhecido"


def carregar(caminho: Path):
    """Devolve a lista de anotações [(tarefa, anotacao)] do export, em qualquer formato,
    e um índice {id: result} de anotações e predições (para comparar com a origem)."""
    arquivos = ([p for p in sorted(caminho.iterdir())
                 if p.is_file() and not p.name.startswith(".")]
                if caminho.is_dir() else [caminho])
    pares, origens = [], {}
    for arq in arquivos:
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(dados, dict) and "result" in dados:        # um arquivo por anotação
            tarefa = dados.get("task") or {}
            pares.append((tarefa, dados))
            origens[("ann", dados.get("id"))] = dados.get("result") or []
        elif isinstance(dados, list):                             # export JSON completo
            for tarefa in dados:
                for pred in tarefa.get("predictions") or []:
                    if isinstance(pred, dict):
                        origens[("pred", pred.get("id"))] = pred.get("result") or []
                for ann in tarefa.get("annotations") or []:
                    origens[("ann", ann.get("id"))] = ann.get("result") or []
                    if not ann.get("was_cancelled"):
                        pares.append((tarefa, ann))
    return pares, origens


def ler_resultado(result):
    """Caixas e ligações de uma anotação. As ligações já vêm com a direção resolvida."""
    caixas, ligacoes, problemas = {}, [], []
    for item in result:
        if item.get("type") == "relation":
            a, b = item.get("from_id"), item.get("to_id")
            direcao = item.get("direction", "right")
            if direcao == "left":
                a, b = b, a
            elif direcao == "bi":
                problemas.append((ERRO, "seta_dupla", a, "seta nos dois sentidos"))
            ligacoes.append({"de": a, "para": b, "nomes": set(item.get("labels") or []),
                             "invertida": direcao == "left"})
            continue
        rid = item.get("id")
        if rid is None:
            continue
        cx = caixas.setdefault(rid, {"id": rid, "classe": None, "texto": "", "bordas": set(),
                                     "pct": None, "W": None, "H": None, "rotacao": 0})
        v = item.get("value") or {}
        tipo = item.get("type")
        if tipo in ("labels", "rectanglelabels"):
            cx["classe"] = (v.get(tipo) or [None])[0]
        elif tipo == "textarea":
            cx["texto"] = "\n".join(v.get("text") or [])
        elif tipo == "choices":
            esc = v.get("choices") or []
            cx["bordas"].update([esc] if isinstance(esc, str) else esc)
        if cx["pct"] is None and {"x", "y", "width", "height"} <= set(v):
            cx["pct"] = (v["x"], v["y"], v["width"], v["height"])
            cx["W"], cx["H"] = item.get("original_width"), item.get("original_height")
            cx["rotacao"] = v.get("rotation") or 0
    return caixas, ligacoes, problemas


# --- validação -----------------------------------------------------------------------------

def _trecho(cx, n=45):
    t = " ".join((cx.get("texto") or "").split())
    return f"{cx.get('classe')}: {t[:n]!r}" if t else f"{cx.get('classe')} (sem texto)"


def montar_ordem(caixas, ligacoes, problemas):
    """Segue a cadeia. Devolve a ordem (ou None se a cadeia não for única e completa)."""
    saida, entrada = defaultdict(list), defaultdict(list)
    for lg in ligacoes:
        if lg["de"] not in caixas or lg["para"] not in caixas:
            problemas.append((ERRO, "ligacao_para_caixa_inexistente", lg["de"],
                              f"{lg['de']} -> {lg['para']}"))
            continue
        if not lg["nomes"]:
            problemas.append((ERRO, "ligacao_sem_nome", lg["de"],
                              f"{_trecho(caixas[lg['de']])} -> {_trecho(caixas[lg['para']])}"))
        for nome in lg["nomes"] - RELACOES:
            problemas.append((ERRO, "nome_de_ligacao_desconhecido", lg["de"], nome))
        saida[lg["de"]].append(lg)
        entrada[lg["para"]].append(lg)

    for rid, lgs in saida.items():
        if len(lgs) > 1:
            problemas.append((ERRO, "duas_saidas", rid, _trecho(caixas[rid])))
    for rid, lgs in entrada.items():
        if len(lgs) > 1:
            problemas.append((ERRO, "duas_entradas", rid, _trecho(caixas[rid])))

    if len(caixas) <= 1:
        return list(caixas)
    inicios = [r for r in caixas if not entrada[r]]
    soltas = [r for r in inicios if not saida[r]]
    for r in soltas:
        problemas.append((ERRO, "caixa_solta", r, _trecho(caixas[r])))
    cabecas = [r for r in inicios if saida[r]]
    if len(cabecas) > 1:
        problemas.append((ERRO, "cadeia_partida", None,
                          f"{len(cabecas)} trechos, começando em: "
                          + " | ".join(_trecho(caixas[r], 25) for r in cabecas)))
    if not cabecas:
        problemas.append((ERRO, "laco", None, "nenhuma caixa sem entrada: a cadeia fecha em laço"))
        return None
    if any(p[0] == ERRO for p in problemas):
        return None

    ordem, atual = [], cabecas[0]
    while atual is not None:
        if atual in ordem:
            problemas.append((ERRO, "laco", atual, _trecho(caixas[atual])))
            return None
        ordem.append(atual)
        atual = saida[atual][0]["para"] if saida[atual] else None
    return ordem


def montar_documentos(caixas, ordem, nomes_de, problemas):
    """Divide a cadeia em documentos (mesma semântica do extrair_documentos.py da Kamilla)
    e aponta o que ficou incoerente. Ruído e figura não entram em documento."""
    docs, aberto = [], None
    n = len(ordem)
    for pos, rid in enumerate(ordem):
        cx = caixas[rid]
        classe, bordas = cx["classe"], cx["bordas"]
        entra = nomes_de.get((ordem[pos - 1], rid), set()) if pos else set()
        sai = nomes_de.get((rid, ordem[pos + 1]), set()) if pos < n - 1 else set()

        if classe in RUIDO:
            if bordas & (BORDA_INICIO | BORDA_FIM):
                problemas.append((AVISO, "borda_em_ruido", rid, _trecho(cx)))
            continue

        if "new_doc" in sai:
            if aberto is not None:
                problemas.append((DOC, "documento_sem_end", rid,
                                  f"o documento anterior não recebeu end antes de {_trecho(cx)}"))
            if classe not in ABRE_DOCUMENTO:
                problemas.append((AVISO, "new_doc_fora_de_titulo", rid, _trecho(cx)))
            if bordas & BORDA_INICIO:
                problemas.append((DOC, "new_doc_com_has_previous", rid, _trecho(cx)))
            aberto = {"ids": [], "comeca_antes": bool(bordas & BORDA_INICIO),
                      "continua_depois": False, "abertura": "new_doc"}
            docs.append(aberto)
        elif aberto is None and bordas & (BORDA_INICIO | BORDA_FIM):
            aberto = {"ids": [], "comeca_antes": bool(bordas & BORDA_INICIO),
                      "continua_depois": False, "abertura": "borda"}
            docs.append(aberto)
        elif aberto is not None and bordas & BORDA_INICIO:
            problemas.append((DOC, "has_previous_no_meio", rid,
                              f"{_trecho(cx)} não é a 1ª caixa do documento"))

        if aberto is None:
            if classe not in HIERARQUIA:
                problemas.append((AVISO, "fora_de_documento", rid, _trecho(cx)))
            continue

        if not aberto["ids"] and aberto["comeca_antes"] and len(docs) > 1:
            problemas.append((AVISO, "has_previous_fora_do_inicio", rid,
                              "documento que vem da página anterior não é o 1º da página"))
        aberto["ids"].append(rid)

        if "end" in entra and bordas & BORDA_FIM:
            problemas.append((DOC, "end_com_end_cut", rid,
                              f"{_trecho(cx)} termina e continua ao mesmo tempo"))
        if bordas & BORDA_FIM:
            aberto["continua_depois"] = True
            aberto["fechamento"] = "end_cut"
            aberto = None
        elif "end" in entra:
            aberto["fechamento"] = "end"
            aberto = None

    if aberto is not None:
        aberto["fechamento"] = None
        problemas.append((DOC, "documento_sem_fim", aberto["ids"][-1],
                          "documento aberto no fim da página: falta end ou end_cut"))
    for d in docs[:-1]:
        if d["continua_depois"]:
            problemas.append((AVISO, "end_cut_fora_do_fim", d["ids"][-1],
                              "documento que continua na próxima página não é o último"))
    return docs


def validar_anotacao(result):
    """Tudo o que se sabe de uma anotação: caixas, ordem, documentos e problemas."""
    caixas, ligacoes, problemas = ler_resultado(result)
    for rid, cx in caixas.items():
        if not cx["classe"]:
            problemas.append((ERRO, "caixa_sem_classe", rid, _trecho(cx)))
        elif cx["classe"] not in GUIA:
            problemas.append((AVISO, "classe_fora_do_guia", rid, cx["classe"]))
        if cx["pct"] is None:
            problemas.append((ERRO, "caixa_sem_retangulo", rid, _trecho(cx)))
        elif cx["rotacao"]:
            problemas.append((AVISO, "caixa_girada", rid, f"{cx['rotacao']} graus"))

    ordem = montar_ordem(caixas, ligacoes, problemas)
    nomes_de = {(lg["de"], lg["para"]): lg["nomes"] for lg in ligacoes}
    for lg in ligacoes:
        a, b = caixas.get(lg["de"]), caixas.get(lg["para"])
        if not a or not b:
            continue
        ruido = a["classe"] in RUIDO or b["classe"] in RUIDO
        if "skip_noise" in lg["nomes"] and not ruido:
            problemas.append((AVISO, "skip_noise_sem_ruido", lg["de"],
                              f"{_trecho(a, 25)} -> {_trecho(b, 25)}"))
        if "continue" in lg["nomes"] and ruido:
            problemas.append((AVISO, "continue_com_ruido", lg["de"],
                              f"{_trecho(a, 25)} -> {_trecho(b, 25)}"))

    docs = montar_documentos(caixas, ordem, nomes_de, problemas) if ordem else []
    return {"caixas": caixas, "ligacoes": ligacoes, "ordem": ordem, "documentos": docs,
            "problemas": problemas, "invertidas": sum(lg["invertida"] for lg in ligacoes)}


def _ordem_de(result):
    """Ordem de uma anotação ou predição de origem (None se a cadeia não fechar)."""
    caixas, ligacoes, probs = ler_resultado(result)
    return montar_ordem(caixas, ligacoes, probs)


def sucessores_iguais(ordem, origem):
    """Quantas ligações da anotação já estavam na origem (XY-cut duplicado)."""
    if not ordem or not origem:
        return None
    pares = set(zip(origem, origem[1:]))
    iguais = sum((a, b) in pares for a, b in zip(ordem, ordem[1:]))
    return iguais, max(len(ordem) - 1, 0)


# --- montagem por anotação -----------------------------------------------------------------

def _meta(tarefa, ann):
    dados = tarefa.get("data") or {}
    fonte = unquote(urlparse(dados.get("source_file") or dados.get("pdf") or "").path)
    lote_arquivo = fonte.split("/docs/", 1)[-1].lstrip("/") if fonte else ""
    pagina = dados.get("page")
    return {
        "task_id": tarefa.get("id"),
        "projeto": tarefa.get("project") or ann.get("project"),
        "anotacao_id": ann.get("id"),
        "anotador": _anotador(ann),
        "atualizada_em": ann.get("updated_at"),
        "tempo_s": ann.get("lead_time"),
        "pagina": pagina,
        "arquivo": lote_arquivo or None,
        "imagem": dados.get("ocr") or dados.get("image"),
        "page_id": f"{lote_arquivo}#p{pagina}" if lote_arquivo else f"ls{tarefa.get('id')}",
        "origem": (("ann", ann.get("parent_annotation")) if ann.get("parent_annotation")
                   else ("pred", ann.get("parent_prediction")) if ann.get("parent_prediction")
                   else None),
    }


def processar(pares, origens, anotador=None, excluir=None):
    saida = []
    for tarefa, ann in pares:
        meta = _meta(tarefa, ann)
        quem = meta["anotador"].lower()
        if anotador and anotador.lower() not in quem:
            continue
        if excluir and any(e.lower() in quem for e in excluir):
            continue
        val = validar_anotacao(ann.get("result") or [])
        comp = None
        if meta["origem"] and meta["origem"] in origens:
            comp = sucessores_iguais(val["ordem"], _ordem_de(origens[meta["origem"]]))
        saida.append({**meta, **val, "iguais_a_origem": comp})
    return saida


# --- comando validar -----------------------------------------------------------------------

def cmd_validar(args):
    pares, origens = carregar(args.export)
    paginas = processar(pares, origens, args.anotador, args.excluir)
    if not paginas:
        sys.exit(f"nenhuma anotação encontrada em {args.export}")

    por_codigo, por_anotador = Counter(), defaultdict(Counter)
    for p in sorted(paginas, key=lambda p: (p["anotador"], p["task_id"] or 0)):
        grav = Counter(g for g, *_ in p["problemas"])
        marca = "XX" if grav[ERRO] else "! " if grav[DOC] else "~ " if grav[AVISO] else "ok"
        comp = p["iguais_a_origem"]
        extra = f" · {comp[0]}/{comp[1]} ligações iguais à origem" if comp else ""
        inv = f" · {p['invertidas']} seta(s) invertida(s)" if p["invertidas"] else ""
        print(f"{marca} tarefa {p['task_id']} · {p['anotador']} · {len(p['caixas'])} caixas · "
              f"{len(p['ligacoes'])} ligações · {len(p['documentos'])} doc(s){inv}{extra}")
        for g, cod, _rid, det in sorted(p["problemas"], key=lambda x: "EDA".index(x[0][0])):
            if g == AVISO and not args.avisos:
                continue
            print(f"     {g:<5} {cod}: {det}")
        por_codigo.update((g, cod) for g, cod, *_ in p["problemas"])
        a = por_anotador[p["anotador"]]
        a["paginas"] += 1
        a["validas"] += not grav[ERRO]
        a["caixas"] += len(p["caixas"])
        a["tempo_s"] += p["tempo_s"] or 0

    print("\nresumo por anotador")
    for quem, c in sorted(por_anotador.items()):
        tempo = f" · {c['tempo_s'] / 60:.1f} min ({c['tempo_s'] / c['paginas']:.0f} s/pág.)" \
            if c["tempo_s"] else ""
        print(f"  {quem}: {c['paginas']} página(s), {c['validas']} com cadeia válida, "
              f"{c['caixas']} caixas{tempo}")
    if por_codigo:
        print("\nproblemas (gravidade, código, ocorrências)"
              + ("" if args.avisos else " — use --avisos para listar os AVISOs por página"))
        for (g, cod), k in sorted(por_codigo.items(), key=lambda x: ("EDA".index(x[0][0][0]), -x[1])):
            print(f"  {g:<5} {cod}: {k}")
    if args.json:
        rel = [{k: p[k] for k in ("task_id", "anotador", "page_id", "anotacao_id")}
               | {"problemas": [list(x) for x in p["problemas"]]} for p in paginas]
        args.json.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nrelatório em {args.json}")


# --- comando converter ---------------------------------------------------------------------

MARCA_SAIDA = "origem_labelstudio.json"


def _nome_imagem(p):
    """Nome único da imagem da página: o caminho depois de /amostras/ com '/' -> '__'
    (é como a Kamilla nomeia a pasta paginas/). Só o nome do arquivo colide: quase toda
    página se chama page_002.jpg."""
    caminho = unquote(urlparse(p["imagem"] or "").path)
    relativo = caminho.split("/amostras/", 1)[-1].lstrip("/")
    return relativo.replace("/", "__") or f"tarefa_{p['task_id']}.jpg"


def _bbox_px(cx):
    x, y, w, h = cx["pct"]
    W, H = cx["W"] or 100, cx["H"] or 100
    return [round(x / 100 * W, 1), round(y / 100 * H, 1),
            round((x + w) / 100 * W, 1), round((y + h) / 100 * H, 1)]


def cmd_converter(args):
    saida: Path = args.saida
    if (saida / "anotacoes.jsonl").exists() and not (saida / MARCA_SAIDA).exists():
        sys.exit(f"{saida} já tem anotacoes.jsonl que não veio deste conversor: "
                 "não sobrescrevo anotação humana. Escolha outra pasta.")
    pares, origens = carregar(args.export)
    paginas = processar(pares, origens, args.anotador, args.excluir)
    if not paginas:
        sys.exit(f"nenhuma anotação encontrada em {args.export}")
    saida.mkdir(parents=True, exist_ok=True)

    tarefas, anotacoes, vistas = [], [], set()
    coco = {"images": [], "annotations": [],
            "categories": [{"id": i + 1, "name": c} for i, c in enumerate(GUIA)]}
    yolo = saida / "yolo_labels"
    yolo.mkdir(exist_ok=True)
    for p in sorted(paginas, key=lambda p: (p["task_id"] or 0, p["anotador"])):
        caixas = p["caixas"]
        cx0 = next(iter(caixas.values()), None)
        W, H = (cx0["W"], cx0["H"]) if cx0 else (None, None)
        erros = [x for x in p["problemas"] if x[0] == ERRO]

        if p["page_id"] not in vistas:          # caixas: uma vez por página
            vistas.add(p["page_id"])
            blocos = []
            for rid in (p["ordem"] or list(caixas)):
                cx = caixas[rid]
                if cx["pct"] is None:
                    continue
                b = {"id": rid, "text": cx["texto"], "bbox": _bbox_px(cx), "classe": cx["classe"]}
                if GUIA_PARA_EXTRATOR:
                    b["classe_extrator"] = GUIA_PARA_EXTRATOR.get(cx["classe"])
                blocos.append(b)
            tarefas.append({"page_id": p["page_id"], "task_id": p["task_id"],
                            "projeto": p["projeto"], "arquivo": p["arquivo"],
                            "pagina": p["pagina"], "imagem": p["imagem"],
                            "dimensions": {"width": W, "height": H, "unidade": "px"},
                            "bounding_boxes": blocos})
            img_id = len(coco["images"]) + 1
            nome_img = _nome_imagem(p)
            coco["images"].append({"id": img_id, "file_name": nome_img, "width": W, "height": H,
                                   "task_id": p["task_id"], "page_id": p["page_id"]})
            linhas = []
            for b in blocos:
                if b["classe"] not in GUIA:
                    continue
                x0, y0, x1, y1 = b["bbox"]
                coco["annotations"].append({
                    "id": len(coco["annotations"]) + 1, "image_id": img_id,
                    "category_id": GUIA.index(b["classe"]) + 1,
                    "bbox": [x0, y0, round(x1 - x0, 1), round(y1 - y0, 1)],
                    "area": round((x1 - x0) * (y1 - y0), 1), "iscrowd": 0})
                x, y, w, h = caixas[b["id"]]["pct"]
                linhas.append(f"{GUIA.index(b['classe'])} {(x + w / 2) / 100:.6f} "
                              f"{(y + h / 2) / 100:.6f} {w / 100:.6f} {h / 100:.6f}")
            (yolo / f"{Path(nome_img).stem}.txt").write_text("\n".join(linhas) + "\n",
                                                             encoding="utf-8")

        nomes = {(lg["de"], lg["para"]): sorted(lg["nomes"]) for lg in p["ligacoes"]}
        anotacoes.append({
            "page_id": p["page_id"], "anotador": p["anotador"],
            "status": "invalida" if erros else "concluida",
            "ordem": p["ordem"] or [],
            "relacoes": ([[a, b, nomes.get((a, b), [])] for a, b in zip(p["ordem"], p["ordem"][1:])]
                         if p["ordem"] else []),
            "documentos": [{"ids": d["ids"], "comeca_em_pagina_anterior": d["comeca_antes"],
                            "continua_na_proxima_pagina": d["continua_depois"]}
                           for d in p["documentos"]],
            "problemas": [list(x) for x in p["problemas"]],
            "iguais_a_origem": p["iguais_a_origem"],
            "n_blocos": len(caixas), "tempo_s": p["tempo_s"],
            "task_id": p["task_id"], "anotacao_id": p["anotacao_id"],
            "salvo_em": p["atualizada_em"]})

    def gravar_jsonl(nome, linhas):
        (saida / nome).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in linhas),
                                  encoding="utf-8")
    gravar_jsonl("tarefas.jsonl", tarefas)
    gravar_jsonl("anotacoes.jsonl", anotacoes)
    (saida / "coco.json").write_text(json.dumps(coco, ensure_ascii=False), encoding="utf-8")
    (saida / "yolo_classes.txt").write_text("\n".join(GUIA) + "\n", encoding="utf-8")
    (saida / MARCA_SAIDA).write_text(json.dumps({
        "export": str(args.export), "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "anotador": args.anotador, "excluir": args.excluir,
        "paginas": len(tarefas), "anotacoes": len(anotacoes),
        "validas": sum(a["status"] == "concluida" for a in anotacoes)},
        ensure_ascii=False, indent=2), encoding="utf-8")
    validas = sum(a["status"] == "concluida" for a in anotacoes)
    print(f"{len(tarefas)} página(s), {len(anotacoes)} anotação(ões), {validas} com cadeia válida, "
          f"{len(coco['annotations'])} caixas no COCO\nsaída em {saida}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("validar", "converter"):
        s = sub.add_parser(nome)
        s.add_argument("export", type=Path, help="export JSON do Label Studio, arquivo ou pasta")
        s.add_argument("--anotador", help="só as anotações cujo autor contém este texto")
        s.add_argument("--excluir", action="append", default=[],
                       help="ignora autores que contêm este texto (pode repetir; ex.: admin)")
        if nome == "validar":
            s.add_argument("--avisos", action="store_true", help="lista também os AVISOs")
            s.add_argument("--json", type=Path, help="grava o relatório de problemas")
        else:
            s.add_argument("--saida", type=Path, required=True)
    args = ap.parse_args()
    {"validar": cmd_validar, "converter": cmd_converter}[args.cmd](args)


if __name__ == "__main__":
    main()
