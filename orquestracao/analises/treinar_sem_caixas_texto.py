"""Acrescenta texto ao LayoutLM sem reescrever o treinador ou os modelos.

Importa treinar_sem_caixas e troca UmToken por ComTexto apenas no processo.
Perdas, media por unidade, split, embaralhamento e decoder sao os originais.
Tokenizador e pesos sao locais; paginas continuam sendo lidas por offsets.
Metadados e a bancada ficam isolados em resultados, sem regravar historicos.

Uso: venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas_texto.py
 treinar --modelo sucessor --representacao linhas --device cpu --n-treino 8
 --max-passos 2 --max-minutos 3 --epocas 1 --nome fumaca_texto
 --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto
Use relatorio para regenerar o Markdown sem carregar pesos.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import contextlib
import os
import statistics

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", HF_DEACTIVATE_ASYNC_LOAD="1",
                  OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4")
from orquestracao.analises import treinar_sem_caixas as t

OUT = t.OUT
RELATORIO = OUT / "treino_com_texto.md"
AVALIACAO = OUT / "bancada_texto"
ESTADO_BANCADA = AVALIACAO / "bancada.json"
VERSAO = "ComTexto-v1-prefixo-local-total510"
MAX_TOTAL, MAX_K = 510, 6
_AUDITORIA = {}
_EM_TREINO = False
_GRAVAR = t.gravar
_SALVAR_TORCH = t.salvar_torch
_PERDA = t.perda
_CRIAR_MODELO = t.criar_modelo


def saida_segura(path):
    """Recusa qualquer escrita fora de resultados, inclusive por importados."""
    path = Path(path).resolve()
    if not path.is_relative_to((RAIZ / "resultados").resolve()):
        raise ValueError(f"Saida fora de resultados: {path}")
    return path


def snapshot_local():
    """Mesmo snapshot que criar_modelo original resolve; nenhuma busca remota."""
    cache = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache/huggingface")))
    cache /= "hub/models--microsoft--layoutlm-base-uncased"
    revision = (cache / "refs/main").read_text(encoding="utf-8").strip()
    path = cache / "snapshots" / revision
    if not path.is_dir():
        raise FileNotFoundError(f"Snapshot LayoutLM local ausente: {path}")
    return path


def identidade_codificador():
    path = snapshot_local()
    arquivos = {n: t.sha(path / n) for n in
                ("vocab.txt", "tokenizer.json", "tokenizer_config.json",
                 "special_tokens_map.json", "config.json") if (path / n).exists()}
    if not any(n in arquivos for n in ("vocab.txt", "tokenizer.json")):
        raise FileNotFoundError(f"Tokenizador nao esta no snapshot local: {path}")
    return {"versao": VERSAO, "snapshot": str(path), "arquivos_sha256": arquivos,
            "wrapper_sha256": t.sha(__file__),
            "pontual_sha256": t.sha(t.pontual.__file__),
            "sucessor_sha256": t.sha(t.sucessor.__file__),
            "max_total_com_especiais": MAX_TOTAL, "max_k": MAX_K,
            "formula_k": "max(1, min(6, 510 // n))",
            "excesso": "reduz tokens excedentes; nao remove unidades"}


def k_pagina(n):
    if n <= 0:
        raise ValueError("Pagina sem unidades nao pode ser codificada")
    return max(1, min(MAX_K, MAX_TOTAL // n))


class ComTexto:
    """WordPiece por unidade; bloco_de indexa a ordem de entrada, nao o shard."""

    def __init__(self, tok=None):
        if tok is None:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(str(snapshot_local()), local_files_only=True)
        self.tok = tok
        self.pad, self.unk = tok.pad_token_id, tok.unk_token_id
        self.cls, self.sep = tok.cls_token_id, tok.sep_token_id
        if any(v is None for v in (self.pad, self.unk, self.cls, self.sep)):
            raise ValueError("Tokenizador sem PAD/UNK/CLS/SEP")

    def pretokenizar(self, paginas):
        # Codificar tokeniza somente a pagina corrente; nao guarda corpus/_tok.
        return None

    def codificar(self, p, ordem):
        n = len(ordem)
        K = k_pagina(n)
        if n > MAX_TOTAL - 2:
            raise ValueError(
                f"{p['page_id']}: {n} unidades nao cabem em {MAX_TOTAL} tokens "
                "incluindo CLS/SEP com um token por unidade. A compactacao "
                "original so trata excesso de 510; nenhuma unidade foi descartada.")
        if len(set(ordem)) != n or set(ordem) != set(range(len(p["bounding_boxes"]))):
            raise ValueError("Ordem de entrada nao e uma permutacao completa")
        W, H = p["dimensions"]["width"], p["dimensions"]["height"]
        tokens, caixas = [], []
        vazias = 0
        for bi in ordem:
            u = p["bounding_boxes"][bi]
            if "text" not in u:
                raise ValueError(f"Campo text ausente: {p['page_id']}/{u['id']}")
            texto = str(u["text"] or "").strip()
            vazias += not bool(texto)
            ids = self.tok.encode(texto, add_special_tokens=False,
                                  truncation=True, max_length=K) if texto else []
            tokens.append(list(ids[:K]) or [self.unk])
            caixas.append(t.pontual.normalizar_bbox(u["bbox"], W, H))
        # 510//n nao reserva especiais: aparar so o excesso, preservando todos
        # os indices e ao menos um token. Desempate fixo pela entrada embaralhada.
        excesso = max(0, sum(map(len, tokens)) + 2 - MAX_TOTAL)
        aparados = excesso
        while excesso:
            j = max(range(n), key=lambda i: (len(tokens[i]), i))
            if len(tokens[j]) <= 1:
                raise AssertionError("Orcamento impossivel sem perder unidade")
            tokens[j].pop()
            excesso -= 1
        ids, bb, unidade = [self.cls], [[0] * 4], [-1]
        for j, (ts, caixa) in enumerate(zip(tokens, caixas)):
            ids.extend(ts)
            bb.extend([caixa] * len(ts))
            unidade.extend([j] * len(ts))
        ids.append(self.sep)
        bb.append([1000] * 4)
        unidade.append(-1)
        if len(ids) > MAX_TOTAL or set(unidade[1:-1]) != set(range(n)):
            raise AssertionError("Limite de tokens ou cobertura de unidades violado")
        if _EM_TREINO:
            _AUDITORIA[p["page_id"]] = {
                "n": n, "k": K, "tokens_texto": len(ids) - 2,
                "mediana_tokens_reais": statistics.median(map(len, tokens)),
                "unidades_sem_texto": vazias, "tokens_aparados_especiais": aparados}
        return ids, bb, unidade


def resumo_tokens():
    rows = list(_AUDITORIA.values())
    return {"paginas_unicas_observadas_treino": len(rows),
            "k_mediano": statistics.median(r["k"] for r in rows) if rows else None,
            "fracao_paginas_k_abaixo_6": statistics.mean(r["k"] < MAX_K for r in rows) if rows else None,
            "mediana_por_pagina_tokens_reais_por_unidade":
                statistics.median(r["mediana_tokens_reais"] for r in rows) if rows else None,
            "paginas_com_ajuste_especiais": sum(r["tokens_aparados_especiais"] > 0 for r in rows),
            "por_page_id": dict(_AUDITORIA)}


def gravar(path, obj):
    path = saida_segura(path)
    if path.name == "treino.json":
        obj = {**obj, "tokens_por_unidade": resumo_tokens(),
               "codificador": VERSAO, "threads_max": 4, "num_workers": 0}
    # A inferencia original acumula tempos apenas do trecho novo. Preservar
    # diagnosticos anteriores da mesma predicao, cuja identidade ja foi conferida.
    if path.name.endswith("__tempos.json") and path.exists():
        obj = {**t.ler(path), **obj}
    _GRAVAR(path, obj)


def salvar_torch(path, obj):
    _SALVAR_TORCH(saida_segura(path), obj)


def perda(model, cod, ps, a):
    global _EM_TREINO
    antes, _EM_TREINO = _EM_TREINO, True
    try:
        return _PERDA(model, cod, ps, a)
    finally:
        _EM_TREINO = antes


def criar_modelo(a):
    # Na inferencia, a vem do checkpoint: nao basta o treino.json ser textual.
    if getattr(a, "codificador_texto", None) != identidade_codificador():
        raise ValueError("Configuracao do checkpoint nao corresponde ao codificador textual local")
    return _CRIAR_MODELO(a)


@contextlib.contextmanager
def instalar():
    """Trocas temporarias em memoria; nenhuma fonte existente e editada."""
    trocas = {"UmToken": ComTexto, "criar_modelo": criar_modelo,
              "perda": perda, "gravar": gravar,
              "salvar_torch": salvar_torch, "relatorio": relatorio}
    antigos = {k: getattr(t, k) for k in trocas}
    try:
        for k, v in trocas.items():
            setattr(t, k, v)
        yield
    finally:
        for k, v in antigos.items():
            setattr(t, k, v)


@contextlib.contextmanager
def bancada_isolada():
    """Reusa avaliar/medir/eventos com caminhos novos e fontes identificadas."""
    visibilidade = os.environ.get("CUDA_VISIBLE_DEVICES")
    from orquestracao.analises import bancada_ordenadores as b
    if visibilidade is None:
        os.environ.pop("CUDA_VISIBLE_DEVICES", None)
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = visibilidade
    antigos = b.OUT, b.JSON, b.MD, b.DEP_PATHS
    b.OUT, b.JSON, b.MD = AVALIACAO, ESTADO_BANCADA, AVALIACAO / "bancada.md"
    extras = [Path(__file__), Path(__file__).with_name("ordenar_bancadas_texto.py")]
    b.DEP_PATHS = list(antigos[3]) + extras
    b.assinatura_metricas.cache_clear()
    try:
        yield b
    finally:
        b.OUT, b.JSON, b.MD, b.DEP_PATHS = antigos
        b.assinatura_metricas.cache_clear()


def conferir_ancoras():
    # Nao confiar apenas no sinal historico: verifica as fontes atuais e as
    # sequencias P2 usando detectores ja congelados; nao carrega detector/GPU.
    with bancada_isolada() as b, b.trava():
        R = b.iniciar()
        b.conferir_ancoras(R)
        if not R["ancoras"].get("aprovada"):
            raise RuntimeError("Ancora nao reproduzida; comparacao suspensa")


def numero(v, casas=3):
    return "—" if v is None else f"{v:.{casas}f}".replace(".", ",")


def relatorio():
    """Numeros observados somente de treino.json e da bancada importada."""
    OUT.mkdir(parents=True, exist_ok=True)
    R = t.ler(ESTADO_BANCADA) if ESTADO_BANCADA.exists() else {}
    aprovada = R.get("ancoras", {}).get("aprovada", False)
    txt = ["# LayoutLM sobre linhas com texto", "",
           "Gerado por `treinar_sem_caixas_texto.py relatorio`. "
           "Fumaças são evidência de execução, não comparação de eficácia.", "",
           "`ComTexto` lê o campo `text`, preservado por `pagina()`, e usa WordPiece "
           "do snapshot local com `local_files_only=True`. Cada subpalavra recebe a "
           "mesma caixa normalizada e o índice da unidade na entrada. Sucessor e "
           "pontual já somam estados e dividem pela contagem (`scatter_add_`); perdas, "
           "geometria, alvos e decodificação originais são reutilizados.", "",
           "Orçamento teórico, calculado pelo script; não é medição do corpus. "
           "K é teto, sem preenchimento artificial para textos curtos.", "",
           "| Unidades após preparação | K máximo por unidade |",
           "|---|---:|"]
    ini, anterior = 1, k_pagina(1)
    for n in range(2, MAX_TOTAL - 1):
        atual = k_pagina(n)
        if atual != anterior:
            txt.append(f"| {ini}–{n - 1} | {anterior} |")
            ini, anterior = n, atual
    txt += [f"| {ini}–{MAX_TOTAL - 2} | {anterior} |", "",
            f"`K = max(1, min({MAX_K}, {MAX_TOTAL} // n))`; o total com CLS/SEP "
            f"é limitado a {MAX_TOTAL}. Quando o prefixo ocupa todo o orçamento, "
            "reduz-se o excesso das unidades com mais tokens, com desempate pela "
            "entrada embaralhada. Nenhuma unidade é removida. Se não couber um "
            "token por unidade, há erro explícito. A compactação original acima "
            "do seu limite é preservada; não há segmentação nova.", "",
            "## Âncoras", ""]
    if aprovada:
        txt += ["A bancada original foi chamada com saídas isoladas. P2 é "
                "reproduzido com detecções congeladas; P1m é importado do histórico, "
                "conforme o controle original. Tolerâncias são as da bancada.", "",
                "| Controle golden_v4 | Páginas | τ palavras | Quebras/página |",
                "|---|---:|---:|---:|"]
        for m in ("P2", "P1m", "regra_colunas_exportada"):
            v = R["ancoras"]["medias"][m]
            txt.append(f"| {m} | {R['ancoras']['n']} | {numero(v['tau'], 6)} | {numero(v['quebras'], 6)} |")
    else:
        txt += ["Pendente: âncoras ainda não reproduzidas nesta execução. "
                "Nenhuma conclusão nova de eficácia é permitida."]
        if R.get("bloqueio"):
            txt.append(R["bloqueio"])
    txt += ["", "## Treino e fumaça", "",
            "K mediano e fração abaixo do teto referem-se a páginas únicas "
            "realmente usadas na perda, após preparação; validação não entra. "
            "O JSON também guarda a mediana dos tokens reais por unidade.", "",
            "| Execução | Dispositivo | Selecionadas | Visitadas | Passos | Épocas | Segundos | K mediano | Fração K < 6 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    treinos = []
    for path in sorted(OUT.glob("*/treino.json")):
        info = t.ler(path)
        if info.get("codificador") != VERSAO:
            continue
        treinos.append(info)
        c, k = info["config"], info["tokens_por_unidade"]
        txt.append(f"| {c['nome']} | {c['device']} | {info['paginas_treino']} | "
                   f"{info.get('paginas_visitadas', 0)} | {info.get('passos', 0)} | "
                   f"{info.get('epocas_completas', 0)} | {numero(info.get('segundos'), 1)} | "
                   f"{numero(k['k_mediano'], 1)} | {numero(k['fracao_paginas_k_abaixo_6'])} |")
    if not treinos:
        txt += ["", "Treino de fumaça pendente; nenhuma execução comprovada."]
    txt += ["", "## Inferência e avaliação", ""]
    if aprovada:
        txt += ["Coortes separadas; grupos humanos seguem o split por veículo. "
                "Métricas importadas de `bancada_ordenadores.metricas`, que chama "
                "`erros_ponta_a_ponta.medir/eventos` e a expansão canônica.", "",
                "| Modelo | Bancada | Grupo | n | Completa | τ palavras | Quebras/página | Fidelidade 12 | Sucessor linhas |",
                "|---|---|---|---:|---|---:|---:|---:|---:|"]
        for key, r in sorted(R.get("resultados", {}).items()):
            for grupo, resumo in r["resumos"].items():
                if not resumo["n"]:
                    continue
                m = resumo["metricas"]
                media = lambda k: m[k]["media"]
                pct = lambda k: numero(100 * media(k), 2) + "%" if media(k) is not None else "—"
                txt.append(f"| {r['ordenador']} | {r['bancada']} | {grupo} | "
                           f"{resumo['n']} | {'sim' if r['completa'] else 'não'} | "
                           f"{numero(media('tau'), 6)} | {numero(media('quebras'), 2)} | "
                           f"{pct('fid12')} | {pct('sucessor_linhas')} |")
    if not R.get("resultados"):
        txt.append("Inferência de fumaça pendente; permutação e isolamento do ouro ainda não comprovados.")
    for path in sorted(OUT.glob("*/pred_fumaca_texto/*__tempos.json")):
        ds = t.ler(path)
        checks = [d for d in ds.values() if d.get("isolamento_ouro") and "metricas_fumaca" in d]
        txt.append(f"`{path.relative_to(RAIZ).as_posix()}`: {len(ds)} páginas com "
                   f"diagnóstico, {len(checks)} com repetição sem ouro e métricas originais.")
    txt += ["", "## Limitações e operação", "",
            "Não há conclusão sobre o ganho de texto antes da avaliação completa. "
            "Textos longos, inclusive tabelas, perdem o restante após o prefixo. "
            "Nas páginas densas K mínimo expõe só a primeira subpalavra da linha. "
            "O tokenizador uncased tem cobertura limitada do português. K nominal "
            "e número de tokens reais são distintos, especialmente em imagens sem texto.", "",
            "Golden v4 foi usado no desenvolvimento da regra de colunas. O golden "
            "v3 adicional é pequeno. Referência humana é de regiões expandidas; "
            "silver é fluxo automático nos veículos confiáveis. Páginas humanas "
            "são excluídas do treino, mas alguns veículos humanos podem ser vistos. "
            "As coortes podem se sobrepor ao silver e não devem ser somadas. "
            "Fumaça com n pequeno não estima eficácia, generalização ou custo em GPU.", "",
            "Leitura sequencial, sem DataLoader/workers e com até quatro threads. "
            "Checkpoint e estatísticas parciais são salvos pelo treinador original. "
            "Limite de tempo encerra seu orçamento; queda antes disso permite "
            "retomar `ultimo.pt`. Configuração inclui versão/hash do wrapper e "
            "tokenizador: não retomar checkpoints geométricos como se fossem textuais. "
            "Usar `ordenar_bancadas_texto.py` para reconstruir ComTexto; o ordenador "
            "antigo reconstrói UmToken e não serve para este checkpoint.", "",
            "`gpu_texto.sh` não é executado pela implementação. Aguarda o marcador "
            "da semente anterior solicitada e a conclusão da fila antiga, que "
            "também prevê outra semente. Isso impede disputa entre filas sem trava comum.", "",
            "## Reprodução da fumaça (CPU)", "", "```powershell",
            "venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas_texto.py treinar --modelo sucessor --representacao linhas --device cpu --n-treino 8 --max-passos 2 --max-minutos 3 --epocas 1 --nome fumaca_texto --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto",
            "venv/Scripts/python.exe -B orquestracao/analises/ordenar_bancadas_texto.py --checkpoint resultados/ordenadores_treinados_sem_caixas/fumaca_texto/melhor.pt --dir-saida resultados/ordenadores_treinados_sem_caixas/fumaca_texto/pred_fumaca_texto --limite 1 --avaliar",
            "venv/Scripts/python.exe -B orquestracao/analises/treinar_sem_caixas_texto.py relatorio",
            "```", "",
            "A inferência limitada usa uma página de cada bancada. A opção "
            "`--avaliar` registra cobertura parcial, sem apresentá-la como bancada completa.", ""]
    # O Markdown e da tarefa com texto, nunca o relatorio global antigo.
    tmp = RELATORIO.with_suffix(".md.tmp")
    with saida_segura(tmp).open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(txt))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, RELATORIO)


def treinar(a):
    if a.modelo not in ("sucessor", "pontual"):
        raise ValueError("Wrapper com texto aceita somente sucessor ou pontual")
    if not a.nome or a.nome == "lstm_geo":
        a.nome = f"{a.modelo}_{a.representacao}_texto_s{a.seed}"
    a.dir_saida = saida_segura(a.dir_saida or OUT / a.nome)
    # Esses campos entram na assinatura original e em melhor.pt/ultimo.pt.
    a.codificador_texto = identidade_codificador()
    info_path = a.dir_saida / "treino.json"
    _AUDITORIA.clear()
    if info_path.exists():
        info = t.ler(info_path)
        if info.get("codificador") != VERSAO:
            raise ValueError("Diretorio ocupado por treino sem texto; escolha outro")
        _AUDITORIA.update(info["tokens_por_unidade"].get("por_page_id", {}))
    elif any((a.dir_saida / n).exists() for n in ("melhor.pt", "ultimo.pt")):
        raise ValueError("Checkpoint sem metadados textuais; nao sobrescrever")
    relatorio()
    try:
        conferir_ancoras()
        with instalar():
            t.treinar(a)
    finally:
        relatorio()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = t.parser()
    ap.set_defaults(modelo="sucessor", nome=None, dir_saida=None)
    a = ap.parse_args()
    if a.modo == "relatorio":
        relatorio()
    elif a.modo == "auditar":
        raise ValueError("Use treino.json para auditoria textual; nao executar auditoria geometrica")
    else:
        treinar(a)


def _compactar_com_especiais(p):
    """Como t.compactar, mas o limite e 508 unidades (CLS e SEP ocupam 2 dos 510 tokens).

    Orquestrador, 08/10: a pagina com 509 unidades derrubou o treino textual as 01:15 porque a
    compactacao original so age acima de 510. Aqui, ate 508 nada muda; de 509 a 510 junta, sem
    descartar nenhuma, os pares de linhas vizinhas mais proximas (mesma ordem geometrica) ate caber.
    Acima de 510 usa a compactacao original (que gera no maximo 510 faixas; se sobrarem 509 ou 510, junta de novo).
    """
    bs = p["bounding_boxes"]
    if len(bs) <= 508:
        return p, {b["id"]: [b["id"]] for b in bs}
    if len(bs) > 510:
        p, grupos = _compactar_original(p)
        if len(p["bounding_boxes"]) <= 508:
            return p, grupos
        bs = p["bounding_boxes"]
    else:
        grupos = {b["id"]: [b["id"]] for b in bs}
    excesso = len(bs) - 508
    ordem = sorted(range(len(bs)), key=lambda i: (bs[i]["bbox"][1], bs[i]["bbox"][0], bs[i]["id"]))
    pares = sorted(range(len(ordem) - 1), key=lambda k: (
        abs(bs[ordem[k + 1]]["bbox"][1] - bs[ordem[k]]["bbox"][1]) + abs(bs[ordem[k + 1]]["bbox"][0] - bs[ordem[k]]["bbox"][0]), k))
    usados, juntar = set(), []
    for k in pares:
        a, b = ordem[k], ordem[k + 1]
        if a in usados or b in usados:
            continue
        usados.update((a, b)); juntar.append((a, b))
        if len(juntar) == excesso:
            break
    por_par = {a: b for a, b in juntar}
    consumidos = set(por_par.values())
    novos, novos_grupos = [], {}
    for i, b in enumerate(bs):
        if i in consumidos:
            continue
        membros = [i] + ([por_par[i]] if i in por_par else [])
        if len(membros) == 1:
            novos.append(b); novos_grupos[b["id"]] = list(grupos[b["id"]])
            continue
        bid = f"faixa_e{i}"
        bb = [min(bs[m]["bbox"][0] for m in membros), min(bs[m]["bbox"][1] for m in membros),
              max(bs[m]["bbox"][2] for m in membros), max(bs[m]["bbox"][3] for m in membros)]
        novos.append({"id": bid, "bbox": bb, "text": " ".join(str(bs[m].get("text") or "") for m in membros), "tipo": "texto"})
        novos_grupos[bid] = [x for m in membros for x in grupos[bs[m]["id"]]]
    ordens = {}
    for chave, ord_ in p.get("ordens", {}).items():
        postos = {}
        for j, bid in enumerate(ord_):
            postos[bid] = j
        ordens[chave] = sorted(novos_grupos, key=lambda g: (statistics.median(postos[x] for x in novos_grupos[g]), g))
    return {**p, "bounding_boxes": novos, "ordens": ordens}, novos_grupos


_compactar_original = t.compactar
t.compactar = _compactar_com_especiais


if __name__ == "__main__":
    main()
