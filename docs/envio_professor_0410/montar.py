"""Monta o resumo de resultados de 02 a 04/10 para o orientador.

Todo número do resumo é lido de um arquivo de resultados; nada é digitado à mão.
Uso: venv/Scripts/python.exe docs/envio_professor_0410/montar.py
Saída: figuras PNG e resumo.html nesta pasta (o PDF é impresso a partir do HTML).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
RES = RAIZ / "resultados"

CORES = {"texto": (2, 132, 199), "tabela": (217, 119, 6), "imagem": (190, 24, 93),
         "margem": (22, 163, 74), "quadro": (124, 58, 237)}
GRUPO = {"texto_coluna": "texto", "texto": "texto", None: "texto", "table": "tabela", "tabela": "tabela",
         "picture": "imagem", "imagem": "imagem", "cabecalho": "margem", "rodape": "margem",
         "quadro_externo": "quadro"}


def ler(caminho):
    return [json.loads(x) for x in Path(caminho).read_text(encoding="utf-8").splitlines() if x.strip()]


def br(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",")


def sinal(x, casas=1):
    return br(x, casas).replace("-", "−")


def pct(x, casas=1):
    return br(100 * x, casas) + "%"


def milhar(n):
    return f"{n:,}".replace(",", ".")


def fonte(tam):
    for nome in ("segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{nome}", tam)
        except OSError:
            pass
    return ImageFont.load_default()


def painel(img, dims, caixas, preencher):
    base = img.convert("RGBA")
    camada = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    sx, sy = base.width / dims["width"], base.height / dims["height"]
    for c in caixas:
        cor = CORES[GRUPO.get(c.get("tipo", c.get("classe")), "texto")]
        x0, y0, x1, y1 = c["bbox"]
        ret = [x0 * sx, y0 * sy, x1 * sx, y1 * sy]
        d.rectangle(ret, outline=cor + (255,), width=3, fill=cor + (38,) if preencher else None)
    return Image.alpha_composite(base, camada).convert("RGB")


def figura_caixas(pid, golden, diamond, estruturas, saida, altura=1150):
    g, d, e = golden[pid], diamond[pid], estruturas[pid]
    img = Image.open(RAIZ / "data/golden/golden_v4/img" / g["imagem"]).convert("RGB")
    img = img.resize((round(img.width * altura / img.height), altura), Image.LANCZOS)
    finas, novas = d["blocos_v3"], e["unidades"]
    n_texto = sum(GRUPO.get(u.get("tipo")) == "texto" for u in novas)
    titulos = (f"Hoje: caixas finas do extrator ({len(finas)} caixas)",
               f"Proposta: texto não dividido ({len(novas)} unidades, {n_texto} de texto)")
    topo, vao = 64, 30
    folha = Image.new("RGB", (img.width * 2 + vao, altura + topo), "white")
    des = ImageDraw.Draw(folha)
    for i, (caixas, cheio) in enumerate(((finas, False), (novas, True))):
        x = i * (img.width + vao)
        folha.paste(painel(img, g["dimensions"], caixas, cheio), (x, topo))
        des.text((x + 4, 14), titulos[i], fill="black", font=fonte(30))
    folha.save(saida, optimize=True)
    return len(finas), len(novas)


def figura_erros(m, saida):
    nomes = ["Ordem ingênua\n(cima para baixo)", "Caixas finas\n+ XY-cut (atual)",
             "Caixas finas\n+ XY-cut + margens", "Sem caixas finas\n(proposta)"]
    chaves = ["P0", "P1", "P1m", "P2"]
    cores = ["#9ca3af", "#0284c7", "#0284c7", "#16a34a"]
    fig, eixos = plt.subplots(1, 2, figsize=(11, 3.9), dpi=170)
    for ax, (metr, titulo, casas) in zip(eixos, (("quebras", "Quebras de leitura por página (menor é melhor)", 1),
                                                  ("tau", "τ de Kendall de palavras (maior é melhor)", 3))):
        med = [m[k][metr]["media"] for k in chaves]
        ic = [m[k][metr]["ic"] for k in chaves]
        err = [[a - lo for a, (lo, hi) in zip(med, ic)], [hi - a for a, (lo, hi) in zip(med, ic)]]
        barras = ax.bar(nomes, med, yerr=err, capsize=4, color=cores, edgecolor="none",
                        error_kw={"ecolor": "#374151", "lw": 1})
        barras[2].set_hatch("//"); barras[2].set_edgecolor("white")
        for b, v, (lo, hi) in zip(barras, med, ic):
            ax.text(b.get_x() + b.get_width() / 2, hi, " " + br(v, casas), ha="center", va="bottom", fontsize=10,
                    fontweight="bold")
        ax.set_title(titulo, fontsize=11, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelsize=8.5)
        ax.set_ylim(0.6 if metr == "tau" else 0, None)
        ax.yaxis.set_major_formatter(lambda v, _, c=(2 if metr == "tau" else 0): br(v, c))
    fig.tight_layout()
    fig.savefig(saida)
    plt.close(fig)


def main():
    erros = json.loads((RES / "erros_ponta_a_ponta.json").read_text(encoding="utf-8"))
    R = erros["resumos"]
    T, V4, V3 = R["todas"], R["v4"], R["v3_novo"]
    m, t = T["metodos"], T["testes"]
    palavras_ouro = sum(p["palavras_ouro"] for p in erros["paginas"])

    def q(p, k):
        return p["metodos"][k]["quebras"]
    placar = {b: [sum(q(p, "P2") < q(p, b) for p in erros["paginas"]),
                  sum(q(p, "P2") == q(p, b) for p in erros["paginas"]),
                  sum(q(p, "P2") > q(p, b) for p in erros["paginas"])] for b in ("P1", "P1m")}
    ganho = sorted(((q(p, "P1m") - q(p, "P2")), p["page_id"]) for p in erros["paginas"])
    top5 = sum(g for g, _ in ganho[-5:])
    saldo = sum(g for g, _ in ganho)

    golden = {p["page_id"]: p for p in ler(RAIZ / "data/golden/golden_v4/tarefas.jsonl")}
    diamond = {}
    for lote in ("diamond_piloto", "diamond_treino"):
        for p in ler(RAIZ / f"data/diamond/{lote}/tarefas.jsonl"):
            diamond[p["page_id"]] = p
    estruturas = {p["page_id"]: p for p in ler(RES / "estruturas_golden_v4/colunas.jsonl")}
    n_finas = sum(len(diamond[i]["blocos_v3"]) for i in golden)
    tipos = {}
    for i in golden:
        for u in estruturas[i]["unidades"]:
            tipos[GRUPO.get(u.get("tipo"), "texto")] = tipos.get(GRUPO.get(u.get("tipo"), "texto"), 0) + 1
    n_novas = sum(tipos.values())

    exemplos = [("official_diary_rj/Parte II (Poder Legislativo)_2024-02-06.pdf#p1", "fig_caixas_rj.png"),
                ("official_diary_pe/2023-02-02_1-Poder Executivo.pdf#p6", "fig_caixas_pe.png")]
    for pid, nome in exemplos:
        figura_caixas(pid, golden, diamond, estruturas, AQUI / nome)
    figura_erros(m, AQUI / "fig_erros.png")
    por_pagina = {p["page_id"]: p for p in erros["paginas"]}
    rj = por_pagina[exemplos[0][0]]

    lr = {}
    for r in ler(RES / "datasets_sem_caixas/avaliacao/layoutreader.jsonl"):
        lr.setdefault(r["versao"], []).append(r)
    lr = {k: (sum(x["tau"] for x in v) / len(v), sum(x["sucessor"] for x in v) / len(v), len(v)) for k, v in lr.items()}
    man = json.loads((RES / "datasets_sem_caixas/manifesto.json").read_text(encoding="utf-8"))
    val = json.loads((RES / "datasets_sem_caixas/validacao_exportacao.json").read_text(encoding="utf-8"))
    ls3 = json.loads((RES / "deteccao/ls3_map_teste.json").read_text(encoding="utf-8"))
    ls16 = json.loads((RES / "deteccao/ls16_map_teste.json").read_text(encoding="utf-8"))
    split = json.loads((RAIZ / "data/deteccao/ls_split.json").read_text(encoding="utf-8"))["caixas"]["ls3"]
    n_treino, n_teste = split["train"]["paginas"], split["test"]["paginas"]
    n_diamond = (RES / "deteccao/comparacao_detector_ls.txt").read_text(encoding="utf-8").split()[1]

    # F1 de localização do extrator: lido da tabela principal de resultados/extrator_v4.md
    f1 = {}
    for linha in (RES / "extrator_v4.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in linha.split("|")]
        if len(c) > 3 and c[1] in ("extrator", "ls3", "puro_cv", "v4_cv") and c[1] not in f1:
            f1[c[1]] = c[2].split(" ")[0]
    f1_diamond = {}
    bloco = (RES / "deteccao/comparacao_detector_ls.txt").read_text(encoding="utf-8").split("--- 3 classes")[0]
    for linha in bloco.splitlines():
        if linha.startswith("extrator"):
            f1_diamond["extrator"] = linha.split()[2].replace(".", ",")
        if linha.startswith("detector ls3"):
            f1_diamond["ls3"] = linha.split()[2].replace(".", ",")

    def linha_tab(nome, k, destaque=False):
        x = m[k]
        cls = ' class="dest"' if destaque else ""
        return (f"<tr{cls}><td>{nome}</td><td>{br(x['quebras']['media'], 1)}</td><td>{br(x['tau']['media'])}</td>"
                f"<td>{pct(x['sucessor_linhas']['media'])}</td><td>{pct(x['fid12']['media'])}</td>"
                f"<td>{x.get('piso_interno', '—') if k != 'P0' else '—'}</td></tr>")

    d1, d1m = t["P2-P1/quebras"], t["P2-P1m/quebras"]
    red1 = 1 - m["P2"]["quebras"]["media"] / m["P1"]["quebras"]["media"]
    red1m = 1 - m["P2"]["quebras"]["media"] / m["P1m"]["quebras"]["media"]
    o1 = m["P1"]["origens"]
    parte_margens = ((m["P1"]["quebras"]["media"] - m["P1m"]["quebras"]["media"])
                     / (m["P1"]["quebras"]["media"] - m["P2"]["quebras"]["media"]))
    tot1 = m["P1"]["quebras"]["total"]
    q_caixas = o1["caixa_fundida"] + o1["caixa_partida"] + o1["interno_caixa"]
    q_margens = o1["ordenacao_residual"] - m["P1m"]["origens"]["ordenacao_residual"]
    q_resto = tot1 - q_caixas - q_margens
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Ordem de leitura sem caixas finas — resultados de 02 a 04/10/2026</title>
<style>
@page {{ size: A4; margin: 14mm 15mm; }}
body {{ font: 10.6pt/1.42 "Segoe UI", Arial, sans-serif; color: #111827; max-width: 180mm; margin: 0 auto; }}
h1 {{ font-size: 17pt; margin: 0 0 2pt; }}
h2 {{ font-size: 12.5pt; margin: 14pt 0 4pt; border-bottom: 1px solid #d1d5db; padding-bottom: 2pt; break-after: avoid; }}
p {{ margin: 4pt 0; }} ul, ol {{ margin: 4pt 0; padding-left: 16pt; }} li {{ margin: 2pt 0; }}
.sub {{ color: #4b5563; font-size: 9.5pt; margin-bottom: 8pt; }}
.caixa {{ background: #f3f4f6; border-left: 3px solid #16a34a; padding: 6pt 9pt; margin: 8pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.6pt; break-inside: avoid; }}
th, td {{ border-bottom: 1px solid #e5e7eb; padding: 3pt 5pt; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ border-bottom: 1.5px solid #6b7280; font-weight: 600; }}
tr.dest td {{ font-weight: 700; background: #f0fdf4; }}
figure {{ margin: 8pt 0; break-inside: avoid; text-align: center; }} figure img {{ width: 100%; border: 1px solid #e5e7eb; }}
figure.pag img {{ width: 80%; }} figcaption {{ text-align: left; }}
figcaption {{ font-size: 9pt; color: #374151; margin-top: 2pt; }}
.leg span {{ display: inline-block; width: 9pt; height: 9pt; margin: 0 3pt 0 8pt; vertical-align: -1pt; }}
.fontes {{ font-size: 8.4pt; color: #4b5563; }}
code {{ font-size: 8.6pt; }}
</style></head><body>
<h1>Ordem de leitura sem caixas finas de texto</h1>
<div class="sub">Resultados de 02 a 04/10/2026 · Pedro Alano · TCC INF-UFG · para o Prof. Thierson Couto Rosa</div>

<div class="caixa"><b>Resumo.</b> Deixar de dividir o texto em caixas de parágrafo (só tabela e imagem viram bloco; o
texto é organizado em colunas) reduziu as quebras de leitura de {br(m['P1']['quebras']['media'], 1)} para
{br(m['P2']['quebras']['media'], 1)} por página nas {T['n']} páginas com ordem anotada. A maior parte desse ganho
({pct(parte_margens, 0)}) também aparece mantendo as caixas e apenas tratando cabeçalho e rodapé à parte
({br(m['P1m']['quebras']['media'], 1)} por página); entre essas duas alternativas a diferença ainda não é
estatisticamente clara, mas a proposta quase elimina os erros que nascem dentro das caixas
({m['P1']['piso_interno']} → {m['P2']['piso_interno']}).</div>

<h2>1. A representação</h2>
<p>Hoje o extrator divide a página em caixas finas (parágrafos, títulos, assinaturas) e o ordenador decide a sequência
das caixas. Na proposta, apenas tabelas e imagens são detectadas como blocos; o resto do texto fica inteiro e é
organizado em faixas de coluna pelas calhas verticais da página. Cabeçalho, rodapé e quadros institucionais são
separados antes de formar as colunas. Nas {len(golden)} páginas do Golden v4 isso troca {milhar(n_finas)} caixas
({br(n_finas / len(golden), 0)} por página) por {n_novas} unidades ({br(n_novas / len(golden), 0)} por página):
{tipos['texto']} faixas de texto, {tipos['tabela'] + tipos['imagem']} tabelas e imagens, {tipos['margem']} trechos de
cabeçalho ou rodapé e {tipos['quadro']} quadro institucional.</p>
<figure class="pag"><img src="fig_caixas_rj.png">
<figcaption>Diário Oficial do RJ, Poder Legislativo, 06/02/2024. Nesta página o pipeline com caixas finas entrega
{q(rj, 'P1')} quebras de leitura ({q(rj, 'P1m')} com a política de margens) e a proposta, {q(rj, 'P2')}.
<span class="leg"><span style="background:#0284c7"></span>texto<span style="background:#d97706"></span>tabela<span
style="background:#be185d"></span>imagem<span style="background:#16a34a"></span>cabeçalho e rodapé<span
style="background:#7c3aed"></span>quadro institucional</span></figcaption></figure>

<h2>2. Erros que chegam ao texto final</h2>
<p>Comparação entre pipelines totalmente automáticos (nenhum recebe caixa, classe ou ordem humana), em
{T['n']} páginas de {T['veiculos']} veículos com ordem de leitura anotada ({milhar(palavras_ouro)} palavras).
<b>Quebra de leitura</b>: ponto da saída em que a palavra seguinte não é a palavra seguinte na leitura humana.</p>
<table><tr><th>Pipeline</th><th>Quebras por página</th><th>τ de palavras</th><th>Sucessor de linhas</th>
<th>Trechos de 12 palavras intactos</th><th>Quebras dentro de uma unidade</th></tr>
{linha_tab("Ordem ingênua (cima para baixo, esquerda para direita)", "P0")}
{linha_tab("Caixas finas + XY-cut (pipeline atual)", "P1")}
{linha_tab("Caixas finas + XY-cut + política de margens", "P1m")}
{linha_tab("Sem caixas finas (proposta)", "P2", True)}
</table>
<figure><img src="fig_erros.png"><figcaption>Médias por página com intervalo de 95% (bootstrap por veículo).</figcaption></figure>
<ul>
<li><b>Contra o pipeline atual:</b> {sinal(d1['media'])} quebras por página [IC 95% {sinal(d1['ic'][0])}; {sinal(d1['ic'][1])}],
{pct(red1, 0)} a menos (Wilcoxon por veículo com correção de Holm, p = {br(d1['veiculo']['holm'], 3)}). Melhora em
{placar['P1'][0]} páginas, empata em {placar['P1'][1]} e piora em {placar['P1'][2]}.</li>
<li><b>Contra o atual com margens:</b> {sinal(d1m['media'])} quebras por página [IC 95% {sinal(d1m['ic'][0])}; {sinal(d1m['ic'][1])}],
{pct(red1m, 0)} a menos na média, mas o intervalo inclui zero (p por veículo = {br(d1m['veiculo']['p'], 2)}). A proposta
melhora em {placar['P1m'][0]} páginas, empata em {placar['P1m'][1]} e piora em {placar['P1m'][2]}: o ganho médio vem de
poucas páginas densas em que as caixas finas erram muito (as cinco maiores somam {top5} quebras a menos, para um saldo
total de {saldo}).</li>
<li><b>Erros que nenhuma reordenação conserta</b> (já estão dentro de uma caixa ou unidade):
{m['P1']['piso_interno']} no pipeline atual contra {m['P2']['piso_interno']} na proposta.</li>
<li><b>De onde vêm as quebras do pipeline atual:</b> das {milhar(tot1)} quebras, {q_caixas}
({pct(q_caixas / tot1, 0)}) são associadas às caixas ({o1['caixa_fundida']} em caixas que fundem dois trechos,
{o1['caixa_partida']} em caixas partidas e {o1['interno_caixa']} de ordem dentro da caixa); {q_margens}
({pct(q_margens / tot1, 0)}) somem só com a política de margens, isto é, eram cabeçalho ou rodapé fora do lugar; as
outras {q_resto} ({pct(q_resto / tot1, 0)}) são ordem entre caixas no corpo da página. A regra é conservadora (uma
caixa mal cortada pode gerar um erro contado como de ordem), mas a hipótese de que a maioria das quebras nasce nas
caixas não se confirmou nesta medição. O que as caixas trazem são os erros sem conserto posterior, do item acima.</li>
</ul>
<p>Separando as páginas: nas {V4['n']} usadas no desenvolvimento do método, {br(V4['metodos']['P1']['quebras']['media'], 1)}
→ {br(V4['metodos']['P1m']['quebras']['media'], 1)} → {br(V4['metodos']['P2']['quebras']['media'], 1)} quebras por
página (atual → com margens → proposta); nas {V3['n']} páginas adicionais, {br(V3['metodos']['P1']['quebras']['media'], 1)}
→ {br(V3['metodos']['P1m']['quebras']['media'], 1)} → {br(V3['metodos']['P2']['quebras']['media'], 1)}.</p>

<h2>3. Ordenador neural pronto sobre as novas unidades</h2>
<p>O LayoutReader pré-treinado, sem retreino, recebeu as unidades embaralhadas das {lr['linhas'][2]} páginas anotadas do
Golden v4: τ de palavras {br(lr['linhas'][0])} com linhas e {br(lr['colunas'][0])} com faixas de coluna. Nas mesmas
páginas a ordenação geométrica por colunas da seção 2 chega a {br(V4['metodos']['P2']['tau']['media'])}. O modelo pronto
não ajuda; para testar um ordenador aprendido é preciso treiná-lo nessa representação. A exportação já existe para
{man['paginas_unicas']} páginas ({val['integridade']['colunas']['multicolunas']} com evidência de mais de uma coluna),
mas só {man['bancada_humana']} têm ordem humana.</p>
<figure class="pag"><img src="fig_caixas_pe.png" style="width:64%">
<figcaption>Diário Oficial de PE, 02/02/2023: página com quatro colunas, anúncio e imagens isoladas como blocos.</figcaption></figure>

<h2>4. Extrator treinado no dataset anotado (Label Studio, Data Policy)</h2>
<p>Detector de layout treinado nas {milhar(n_treino)} páginas de treino (divisão por fonte; {n_teste} páginas de teste de fontes não
vistas): mAP50 de {br(ls3['mAP50'])} com 3 classes (texto, tabela, imagem) e {br(ls16['mAP50'])} com as 16 classes do
guia. F1 de localização (IoU ≥ 0,5) nas {n_teste} páginas de teste: extrator atual {f1['extrator']}; detector de 3 classes
{f1['ls3']} ({f1['puro_cv']} com limiar ajustado); extrator novo, que parte do detector e ajusta as caixas às palavras
do PDF, {f1['v4_cv']}. Ressalva: nas {n_diamond} páginas que anotei do zero com a minha convenção de caixas, o extrator atual
ainda vence ({f1_diamond['extrator']} contra {f1_diamond['ls3']}), porque as duas convenções de anotação diferem.</p>

<h2>5. Limitações</h2>
<ul>
<li>{V4['n']} das {T['n']} páginas foram usadas para desenvolver o método; nas {V3['n']} adicionais o ganho é menor.</li>
<li>A referência de palavras deriva da ordem humana das regiões, com ordem geométrica dentro de cada região; não é
uma anotação palavra a palavra.</li>
<li>A separação de colunas ainda produz faixas estreitas indevidas em algumas páginas (exemplo: MG, página 18 do
comparador) e cabeçalhos fragmentados; o quadro institucional só é reconhecido quando tem moldura vetorial no PDF.</li>
<li>A variante com margens e quadros da figura ainda não teve a ordenação medida; os números da seção 2 usam a versão
anterior do mesmo método de colunas.</li>
</ul>

<h2>6. Pontos para decidir</h2>
<ol>
<li>Método principal do TCC: a proposta sem caixas finas, ou caixas finas com política de margens (mais simples e,
por enquanto, estatisticamente equivalente)?</li>
<li>Vale anotar a ordem em mais páginas nessa representação para treinar um ordenador (LayoutLM ou LayoutReader)?</li>
<li>Convenção de caixas do extrator: a do guia do Data Policy (16 classes) ou a que usei no Golden?</li>
</ol>

<p><b>Anexo:</b> <code>comparador_golden_v4.html</code>, comparador interativo das {len(golden)} páginas em seis
representações (abre direto no navegador, sem instalar nada).</p>
<p class="fontes"><b>Arquivos de origem dos números:</b> <code>resultados/erros_ponta_a_ponta.json</code> (seção 2);
<code>resultados/estruturas_golden_v4/colunas.jsonl</code> e <code>data/diamond/*/tarefas.jsonl</code> (seção 1);
<code>resultados/datasets_sem_caixas/</code> (seção 3); <code>resultados/deteccao/ls3_map_teste.json</code>,
<code>ls16_map_teste.json</code>, <code>comparacao_detector_ls.txt</code> e <code>resultados/extrator_v4.md</code>
(seção 4). Gerado por <code>docs/envio_professor_0410/montar.py</code>.</p>
</body></html>
"""
    (AQUI / "resumo.html").write_text(html, encoding="utf-8")
    print(json.dumps({"placar": placar, "top5": top5, "saldo": saldo, "finas": n_finas, "novas": n_novas,
                      "tipos": tipos, "f1": f1, "f1_diamond": f1_diamond, "lr": lr,
                      "rj": [q(rj, k) for k in ("P1", "P1m", "P2")]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
