"""
Regioes de layout detectadas na IMAGEM da pagina: tabela, figura, cabecalho, titulo...

Modelo: Docling Heron (RT-DETRv2 treinado no DocLayNet e em outras bases; Livathinos et al.,
2025, "Advanced Layout Analysis Models for Docling", arXiv:2509.11720; licenca Apache-2.0),
com a revisao fixada abaixo. Carrega so do cache local do Hugging Face: nada e baixado sem
--permitir-download.

O segmentador (src/data/extrator.py) usa so as TABELAS: cada tabela vira um bloco. Por que
um detector e nao regras: tabela foi o problema mais anotado no Golden v1 (12 de 30 paginas;
as 4 paginas puladas eram de tabela). Tabela de diario oficial vem de todo jeito -- grade
completa, so linhas horizontais, nenhuma linha --, o find_tables() do pdfplumber so acha a
de grade, e as celulas viravam colunas de blocos. O detector achou tabela nas 12 paginas.

Cache: data/processed/layout/<uf>.jsonl, uma linha por pagina:
  {"page_id", "modelo", "revisao", "dpi", "bbox_imagem", "escala", "regioes": [{"rotulo", "score", "bbox"}]}
com bbox [x0, top, x1, bottom] em pontos, no mesmo sistema de coordenadas das palavras do
pdfplumber: ponto = pixel / escala + origem de bbox_imagem, a area da pagina que a imagem
mostra (em geral a CropBox; quando ela nao comeca em (0, 0), ignorar a origem desloca as
tabelas). Guarda toda regiao com score >= 0,3; o limiar de uso fica com quem le.

Uso:
    python src/data/layout.py --colecao data/processed/blocos_v1 data/processed/blocos_extra_v1
    python src/data/layout.py --colecao data/golden/golden_v1/tarefas.jsonl --saida /tmp/layout
"""
from __future__ import annotations

import os
import sys
import glob
import json
import time
import argparse
from multiprocessing import Pool

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(RAIZ_PROJETO, "data", "raw")
DIR_LAYOUT = os.path.join(RAIZ_PROJETO, "data", "processed", "layout")

MODELO = "docling-project/docling-layout-heron"
REVISAO = "8f39ad3c0b4c58e9c2d2c84a38465abf757272d8"
DPI = 110              # mesma resolucao das imagens do Golden, onde o detector foi conferido
SCORE_CACHE = 0.3
SCORE_TABELA = 0.5


# ---------------------------------------------------------------------------
# Detector (so no processo principal: os workers de renderizacao nao importam torch)
# ---------------------------------------------------------------------------

class Detector:
    def __init__(self, dispositivo=None, permitir_download=False):
        import torch
        from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection
        self.torch = torch
        self.dispositivo = dispositivo or ("cuda" if torch.cuda.is_available() else "cpu")
        kw = {"revision": REVISAO, "local_files_only": not permitir_download}
        try:
            self.proc = RTDetrImageProcessor.from_pretrained(MODELO, **kw)
            self.modelo = RTDetrV2ForObjectDetection.from_pretrained(MODELO, **kw).to(self.dispositivo).eval()
        except OSError as e:
            raise SystemExit(f"[ERRO] modelo {MODELO}@{REVISAO[:8]} fora do cache local do Hugging Face. "
                             f"Para baixar (~170 MB), rode de novo com --permitir-download. Detalhe: {e}")
        self.rotulos = self.modelo.config.id2label

    def __call__(self, imagens, transformacoes):
        """imagens: lista de PIL RGB; transformacoes: [(bbox, escala)] de cada imagem, como em
        pdfplumber.display.PageImage: pixel = (ponto - bbox[0:2]) * escala. A imagem mostra so a
        area de bbox (em geral a CropBox), cuja origem pode nao ser (0, 0) no sistema das palavras."""
        torch = self.torch
        ent = self.proc(images=imagens, return_tensors="pt").to(self.dispositivo)
        with torch.no_grad():
            saida = self.modelo(**ent)
        alvos = torch.tensor([[im.height, im.width] for im in imagens])
        res = self.proc.post_process_object_detection(saida, target_sizes=alvos, threshold=SCORE_CACHE)
        regioes = []
        for (bbox, escala), r in zip(transformacoes, res):
            x_ini, y_ini = bbox[0], bbox[1]
            regioes.append([{"rotulo": self.rotulos[int(l)], "score": round(float(s), 4),
                             "bbox": [round(b[0] / escala + x_ini, 1), round(b[1] / escala + y_ini, 1),
                                      round(b[2] / escala + x_ini, 1), round(b[3] / escala + y_ini, 1)]}
                            for s, l, b in zip(r["scores"].tolist(), r["labels"].tolist(), r["boxes"].tolist())])
        return regioes


def tabelas(regioes, score_min=SCORE_TABELA):
    """Caixas de tabela com score >= score_min. Duas deteccoes da mesma tabela (a menor com
    metade ou mais da area dentro da maior) ficam so com a de maior score.

    regioes None (pagina que o renderizador nao abriu, registrada no cache como falha) devolve
    None: o extrator segmenta a pagina sem tabelas e marca stats["layout"] = False."""
    if regioes is None:
        return None
    cands = sorted((r for r in regioes if r["rotulo"] == "table" and r["score"] >= score_min),
                   key=lambda r: -r["score"])
    mantidas = []
    for r in cands:
        x0, y0, x1, y1 = r["bbox"]
        area = max(1e-6, (x1 - x0) * (y1 - y0))
        repetida = False
        for m in mantidas:
            mx0, my0, mx1, my1 = m
            iw, ih = min(x1, mx1) - max(x0, mx0), min(y1, my1) - max(y0, my0)
            area_m = max(1e-6, (mx1 - mx0) * (my1 - my0))
            if iw > 0 and ih > 0 and iw * ih >= 0.5 * min(area, area_m):
                repetida = True
                break
        if not repetida:
            mantidas.append(r["bbox"])
    return mantidas


# ---------------------------------------------------------------------------
# Renderizacao (workers) e cache
# ---------------------------------------------------------------------------

def renderizar_pdf(tarefa):
    """Worker: abre um PDF e renderiza as paginas pedidas. Devolve [(page_id, img, (bbox, escala), erro)]."""
    import pdfplumber
    uf, arquivo, pedidos = tarefa                       # pedidos: [(n_pag, page_id)]
    saida = []
    try:
        with pdfplumber.open(os.path.join(RAW, uf, *arquivo.split("/"))) as pdf:
            for n_pag, pid in pedidos:
                try:
                    page = pdf.pages[n_pag]
                    # Pagina girada com CropBox diferente da MediaBox: a origem que o pdfplumber da
                    # nao bate com o recorte renderizado (revisao do Codex, erro de ~20 pt). Nenhuma
                    # das 4.112 paginas do acervo medidas em 2026-09-12 cai aqui; se cair, fica sem
                    # tabelas em vez de receber caixas deslocadas.
                    if (page.rotation or 0) % 360 and tuple(page.cropbox) != tuple(page.mediabox):
                        saida.append((pid, None, None, "rotacao_com_cropbox: coordenadas nao confiaveis"))
                        continue
                    pi = page.to_image(resolution=DPI)
                    im = pi.original.convert("RGB")
                    saida.append((pid, im, (tuple(float(v) for v in pi.bbox), float(pi.scale)), None))
                except Exception as e:
                    saida.append((pid, None, None, f"erro_render: {e}"))
    except Exception as e:
        saida += [(pid, None, None, f"pdf_ilegivel: {e}") for _, pid in pedidos]
    return saida


def paginas_de(caminhos):
    """Registros (page_id, uf, arquivo, pagina) de pastas de *.jsonl ou de arquivos .jsonl."""
    arquivos = []
    for c in caminhos:
        c = os.path.abspath(c)
        arquivos += [c] if c.endswith(".jsonl") else sorted(glob.glob(os.path.join(c, "*.jsonl")))
    vistos, paginas = set(), []
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                try:
                    r = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                if "page_id" in r and r["page_id"] not in vistos:
                    vistos.add(r["page_id"])
                    paginas.append({k: r[k] for k in ("page_id", "uf", "arquivo", "pagina")})
    return paginas


def carregar_cache(pasta=DIR_LAYOUT, ufs=None):
    """page_id -> regioes, de todos os <uf>.jsonl da pasta (ou so das ufs pedidas)."""
    cache = {}
    for arq in sorted(glob.glob(os.path.join(pasta, "*.jsonl"))):
        if ufs and os.path.basename(arq)[:-6] not in ufs:
            continue
        with open(arq, encoding="utf-8", errors="replace") as f:   # cauda com UTF-8 cortado vira JSON invalido
            for linha in f:
                if linha.strip():
                    try:
                        r = json.loads(linha)
                    except json.JSONDecodeError:
                        continue          # linha truncada por uma execucao interrompida
                    # registro sem "escala" e anterior a correcao da origem da CropBox: invalido
                    if r.get("revisao") == REVISAO and "escala" in r:
                        cache[r["page_id"]] = r["regioes"]      # None: falha de renderizacao registrada
    return cache


class GravadorCache:
    """Acrescenta registros de layout em <pasta>/<uf>.jsonl, um por pagina.

    Se a ultima linha de um arquivo ficou truncada (execucao interrompida no meio da escrita),
    encerra-a com uma quebra de linha antes do primeiro registro novo: sem isso o registro
    colaria no fragmento e os dois se perderiam na leitura. O fragmento fica no arquivo, como
    linha invalida que carregar_cache() ignora."""

    def __init__(self, pasta):
        self.pasta = pasta
        self.arquivos = {}
        os.makedirs(pasta, exist_ok=True)

    def _abrir(self, uf):
        if uf in self.arquivos:
            return
        caminho = os.path.join(self.pasta, f"{uf}.jsonl")
        precisa_quebra = False
        if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
            with open(caminho, "rb") as f:
                f.seek(-1, os.SEEK_END)
                precisa_quebra = f.read(1) != b"\n"
        self.arquivos[uf] = open(caminho, "a", encoding="utf-8")
        if precisa_quebra:
            self.arquivos[uf].write("\n")

    def __call__(self, pid, uf, regioes, transformacao):
        self._abrir(uf)
        bbox, escala = transformacao
        self.arquivos[uf].write(json.dumps({"page_id": pid, "modelo": MODELO, "revisao": REVISAO, "dpi": DPI,
                                            "bbox_imagem": [round(v, 2) for v in bbox], "escala": round(escala, 6),
                                            "regioes": regioes}, ensure_ascii=False) + "\n")
        self.arquivos[uf].flush()

    def falha(self, pid, uf, erro):
        """Registra uma pagina que nao renderizou, para nao tentar de novo a cada execucao e para
        quem le o cache saber que ela fica sem tabelas por falta de imagem, e nao por esquecimento."""
        self._abrir(uf)
        self.arquivos[uf].write(json.dumps({"page_id": pid, "modelo": MODELO, "revisao": REVISAO, "dpi": DPI,
                                            "bbox_imagem": None, "escala": None, "regioes": None,
                                            "erro": str(erro)[:300]}, ensure_ascii=False) + "\n")
        self.arquivos[uf].flush()

    def fechar(self):
        for f in self.arquivos.values():
            f.close()
        self.arquivos = {}


def garantir_cache(paginas, pasta=DIR_LAYOUT, workers=3, progresso=False):
    """Cache (page_id -> regioes) com todas as paginas pedidas: detecta as que faltam e as
    acrescenta em <pasta>/<uf>.jsonl. Pagina que nao renderiza fica registrada como falha
    (regioes None) e e avisada."""
    cache = carregar_cache(pasta)
    falhas_antigas = [p["page_id"] for p in paginas if p["page_id"] in cache and cache[p["page_id"]] is None]
    if falhas_antigas:
        print(f"[!] {len(falhas_antigas)} paginas pedidas estao no cache como falha de renderizacao e ficam "
              f"sem tabelas: {falhas_antigas[:5]}", flush=True)
    faltam = [{k: p[k] for k in ("page_id", "uf", "arquivo", "pagina")} for p in paginas
              if p["page_id"] not in cache]
    if not faltam:
        return cache
    print(f"[*] detectando layout de {len(faltam)} paginas fora do cache ({pasta})", flush=True)
    gravar = GravadorCache(pasta)
    uf_de = {p["page_id"]: p["uf"] for p in faltam}
    try:
        novos, erros = detectar_paginas(faltam, workers=workers, ao_gravar=gravar, progresso=progresso)
        for pid, erro in erros:
            gravar.falha(pid, uf_de[pid], erro)
            novos[pid] = None
    finally:
        gravar.fechar()
    if erros:
        print(f"[!] {len(erros)} paginas nao renderizaram e ficam sem tabelas (registradas no cache): "
              f"{[pid for pid, _ in erros][:5]}", flush=True)
    cache.update(novos)
    return cache


def detectar_paginas(paginas, detector=None, workers=3, lote=8, ao_gravar=None, progresso=True):
    """Renderiza e detecta. Devolve (page_id -> regioes, [(page_id, erro)]).
    ao_gravar(page_id, uf, regioes, transformacao) e chamado a cada pagina pronta (grava o cache aos poucos)."""
    detector = detector or Detector()
    por_pdf = {}
    for p in paginas:
        por_pdf.setdefault((p["uf"], p["arquivo"]), []).append((p["pagina"], p["page_id"]))
    tarefas = [(uf, arq, sorted(ps)) for (uf, arq), ps in por_pdf.items()]
    uf_de = {p["page_id"]: p["uf"] for p in paginas}
    resultado, erros, fila, t0 = {}, [], [], time.time()

    def esvaziar():
        if not fila:
            return
        regs = detector([im for _, im, _ in fila], [tr for _, _, tr in fila])
        for (pid, _, tr), rg in zip(fila, regs):
            resultado[pid] = rg
            if ao_gravar:
                ao_gravar(pid, uf_de[pid], rg, tr)
        fila.clear()

    with Pool(max(1, min(workers, len(tarefas)))) as pool:
        for k, itens in enumerate(pool.imap_unordered(renderizar_pdf, tarefas), 1):
            for pid, im, tr, erro in itens:
                if erro:
                    erros.append((pid, erro))
                    continue
                fila.append((pid, im, tr))
                if len(fila) >= lote:
                    esvaziar()
            if progresso and (k % 25 == 0 or k == len(tarefas)):
                print(f"    {k}/{len(tarefas)} PDFs | {len(resultado) + len(fila)} paginas | "
                      f"{time.time() - t0:.0f}s", flush=True)
    esvaziar()
    return resultado, erros


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--colecao", nargs="+", required=True, help="pastas de *.jsonl ou arquivos .jsonl com page_id")
    ap.add_argument("--saida", default=DIR_LAYOUT)
    ap.add_argument("--workers", type=int, default=3, help="processos de renderizacao (CPU)")
    ap.add_argument("--lote", type=int, default=8, help="imagens por passada na GPU")
    ap.add_argument("--dispositivo", help="cuda ou cpu (padrao: cuda se houver)")
    ap.add_argument("--permitir-download", action="store_true")
    a = ap.parse_args()

    saida = os.path.abspath(a.saida)
    os.makedirs(saida, exist_ok=True)
    paginas = paginas_de(a.colecao)
    feitas = carregar_cache(saida)
    faltam = [p for p in paginas if p["page_id"] not in feitas]
    print(f"[*] {len(paginas)} paginas nas colecoes; {len(paginas) - len(faltam)} ja no cache; "
          f"{len(faltam)} a detectar -> {saida}", flush=True)
    if not faltam:
        return
    detector = Detector(a.dispositivo, a.permitir_download)
    print(f"[*] {MODELO}@{REVISAO[:8]} em {detector.dispositivo}, {DPI} dpi", flush=True)
    gravar = GravadorCache(saida)
    uf_de = {p["page_id"]: p["uf"] for p in faltam}
    t0 = time.time()
    try:
        resultado, erros = detectar_paginas(faltam, detector, a.workers, a.lote, ao_gravar=gravar)
        for pid, erro in erros:
            gravar.falha(pid, uf_de[pid], erro)
    finally:
        gravar.fechar()
    n_tab = sum(len(tabelas(r)) for r in resultado.values())
    print(f"[OK] {len(resultado)} paginas em {time.time() - t0:.0f}s | {n_tab} tabelas com score >= {SCORE_TABELA}")
    if erros:
        print(f"[!] {len(erros)} paginas nao renderizaram; ficam registradas como falha e sem tabelas: {erros[:3]}")


if __name__ == "__main__":
    main()
