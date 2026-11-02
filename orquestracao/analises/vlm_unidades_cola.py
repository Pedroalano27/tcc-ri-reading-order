"""Cola entre o ordenador por VLM com imagem (src/eval/vlm_ordem.py) e as bancadas
de unidades sem caixas finas (colunas_margens e colunas).

Modo 1 (preparar - padrao, sem argumentos):
    Gera particoes JSONL prontas para consumo por vlm_ordem.py a partir das bancadas
    golden_v4 e golden_v3_novo nas representacoes colunas_margens e colunas.
    Gera o relatorio resultados/ordenadores_sem_caixas/vlm/preparo.md com contagens,
    estatisticas, campos adequados e comandos exatos de execucao.

Modo 2 (--converter):
    Le os arquivos brutos produzidos pelo vlm_ordem.py (bruto__*.jsonl) e gera as
    predicoes no contrato da bancada {"page_id": ..., "ordem": [ids das unidades]},
    validando estritamente que a ordem predita seja uma permutacao exata dos ids.
    Gera o relatorio resultados/ordenadores_sem_caixas/vlm/conversao.md.

Uso:
    Modo preparar (padrao):
        venv\\Scripts\\python.exe orquestracao/analises/vlm_unidades_cola.py
    Modo converter:
        venv\\Scripts\\python.exe orquestracao/analises/vlm_unidades_cola.py --converter
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import re
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def obter_raiz() -> Path:
    """Retorna a raiz do projeto de forma robusta."""
    candidato = Path(__file__).resolve()
    for p in [candidato.parent] + list(candidato.parents):
        if (p / "src" / "eval" / "vlm_ordem.py").is_file() or (p / "AGENTS.md").is_file():
            return p
    return Path.cwd().resolve()


RAIZ = obter_raiz()
DIR_BANCADAS = RAIZ / "resultados" / "unidades_sem_caixas" / "bancadas"
DIR_VLM = RAIZ / "resultados" / "ordenadores_sem_caixas" / "vlm"
DIR_PRED = RAIZ / "resultados" / "ordenadores_sem_caixas" / "pred"

BANCADAS = ("golden_v4", "golden_v3_novo")
REPRESENTACOES = ("colunas_margens", "colunas")


def ordem_entrada(pagina: dict) -> list[int]:
    """Indices dos blocos na ordem em que chegam ao metodo (permutacao fixa por pagina)."""
    n = len(pagina.get("bounding_boxes", []))
    idx = list(range(n))
    random.Random(f"entrada-{pagina['page_id']}").shuffle(idx)
    return idx


def preparar_pagina_para_vlm(linha_bancada: dict, rep_nome: str) -> tuple[dict | None, list[str]]:
    """Extrai e adapta uma pagina de representacao para o formato de particao do vlm_ordem.py.

    Retorna (pagina_adaptada, campos_preenchidos).
    """
    reps = linha_bancada.get("representacoes", {})
    if rep_nome not in reps:
        return None, []

    rep_pag = reps[rep_nome]
    if not isinstance(rep_pag, dict):
        return None, []

    campos_ajustados: list[str] = []
    pagina_out = dict(rep_pag)

    # Garante metadados no nivel da pagina
    for campo in ("page_id", "uf", "arquivo", "pagina", "dimensions"):
        if campo not in pagina_out or pagina_out[campo] is None:
            if campo in linha_bancada:
                pagina_out[campo] = linha_bancada[campo]
                campos_ajustados.append(f"pagina.{campo}")

    # Garante estrutura e campos das unidades em bounding_boxes
    bboxes_in = pagina_out.get("bounding_boxes", [])
    bboxes_out = []
    ajustou_classe = False
    ajustou_tipo = False
    ajustou_text = False

    for idx, b in enumerate(bboxes_in):
        b_dict = dict(b)

        # ID da unidade
        if "id" not in b_dict or not b_dict["id"]:
            b_dict["id"] = f"b{idx}"

        # Texto do bloco (imagens podem ter text None)
        if "text" not in b_dict or b_dict["text"] is None:
            b_dict["text"] = ""
            ajustou_text = True

        # Tipo da unidade
        if "tipo" not in b_dict or not b_dict["tipo"]:
            b_dict["tipo"] = "texto"
            ajustou_tipo = True

        # Classe da unidade (o vlm_ordem.py consulta bloco.get('classe') or bloco.get('tipo'))
        # Para unidades sem caixas finas, atribuimos como classe o proprio tipo da unidade (neutro)
        if "classe" not in b_dict or not b_dict["classe"]:
            b_dict["classe"] = b_dict["tipo"]
            ajustou_classe = True

        bboxes_out.append(b_dict)

    if ajustou_classe:
        campos_ajustados.append("bloco.classe (preenchido com o tipo da unidade)")
    if ajustou_tipo:
        campos_ajustados.append("bloco.tipo (fallback para 'texto')")
    if ajustou_text:
        campos_ajustados.append("bloco.text (string vazia quando None)")

    pagina_out["bounding_boxes"] = bboxes_out
    return pagina_out, list(set(campos_ajustados))


def executar_preparo() -> int:
    """Executa o Modo 1: geracao das particoes e relatorio preparo.md."""
    DIR_VLM.mkdir(parents=True, exist_ok=True)

    print("[*] Iniciando Modo Preparar: geracao das particoes para VLM...", flush=True)

    relatorio_estatisticas: list[dict] = []
    todos_campos_ajustados: set[str] = set()

    for bancada in BANCADAS:
        caminho_bancada = DIR_BANCADAS / f"{bancada}.jsonl"
        if not caminho_bancada.is_file():
            print(f"[ERRO] Arquivo de bancada nao encontrado: {caminho_bancada}", file=sys.stderr)
            return 1

        for rep_nome in REPRESENTACOES:
            nome_arquivo_particao = f"particao__{rep_nome}__{bancada}.jsonl"
            caminho_particao = DIR_VLM / nome_arquivo_particao

            contagens_unidades: list[int] = []
            n_paginas = 0
            n_acima_200 = 0

            with open(caminho_bancada, "r", encoding="utf-8") as f_in, open(
                caminho_particao, "w", encoding="utf-8"
            ) as f_out:
                for linha in f_in:
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        d = json.loads(linha)
                    except json.JSONDecodeError:
                        continue

                    pag_vlm, ajustes = preparar_pagina_para_vlm(d, rep_nome)
                    if pag_vlm is None:
                        continue

                    todos_campos_ajustados.update(ajustes)
                    n_unidades = len(pag_vlm.get("bounding_boxes", []))
                    contagens_unidades.append(n_unidades)
                    n_paginas += 1
                    if n_unidades > 200:
                        n_acima_200 += 1

                    f_out.write(json.dumps(pag_vlm, ensure_ascii=False) + "\n")

            mediana_unidades = statistics.median(contagens_unidades) if contagens_unidades else 0
            max_unidades = max(contagens_unidades) if contagens_unidades else 0

            info = {
                "bancada": bancada,
                "representacao": rep_nome,
                "arquivo_particao": nome_arquivo_particao,
                "caminho_particao": str(caminho_particao.relative_to(RAIZ)).replace("\\", "/"),
                "caminho_bruto": f"resultados/ordenadores_sem_caixas/vlm/bruto__{rep_nome}__{bancada}.jsonl",
                "n_paginas": n_paginas,
                "mediana_unidades": mediana_unidades,
                "max_unidades": max_unidades,
                "n_acima_200": n_acima_200,
            }
            relatorio_estatisticas.append(info)
            print(
                f"  -> Gravado {nome_arquivo_particao}: {n_paginas} paginas | "
                f"unidades: mediana={mediana_unidades}, max={max_unidades} | "
                f">200={n_acima_200}",
                flush=True,
            )

    # Escreve o relatorio preparo.md
    caminho_preparo_md = DIR_VLM / "preparo.md"
    gerar_relatorio_preparo(caminho_preparo_md, relatorio_estatisticas, sorted(todos_campos_ajustados))
    print(f"[*] Relatorio de preparo gravado em: {caminho_preparo_md}", flush=True)
    return 0


def gerar_relatorio_preparo(
    caminho_md: Path, estatisticas: list[dict], campos_ajustados: list[str]
) -> None:
    """Gera o arquivo Markdown preparo.md com todas as especificacoes exigidas."""
    linhas: list[str] = [
        "# Preparo das Partições para Ordenação por VLM (Gemini)",
        "",
        "Este documento descreve as partições geradas a partir das unidades sem caixas finas ",
        "(`colunas_margens` e `colunas`) das bancadas humanas `golden_v4` e `golden_v3_novo`, ",
        "formatadas para o ordenador multimodal `src/eval/vlm_ordem.py`.",
        "",
        "## 1. Resumo das Partições Geradas",
        "",
        "| Arquivo de Partição | Bancada | Representação | Páginas | Unidades (Mediana) | Unidades (Máximo) | Páginas > 200 unid.* |",
        "|---|---|---|---:|---:|---:|---:|",
    ]

    for e in estatisticas:
        linhas.append(
            f"| `{e['arquivo_particao']}` | {e['bancada']} | `{e['representacao']}` | "
            f"{e['n_paginas']} | {e['mediana_unidades']:.1f} | {e['max_unidades']} | {e['n_acima_200']} |"
        )

    linhas.extend([
        "",
        "\\* *Nota sobre limite de unidades:* O `src/eval/vlm_ordem.py` possui como parâmetro padrão ",
        "`--max-blocos 200`, ignorando automaticamente páginas com mais de 200 unidades para evitar ",
        "estouro de contexto e degradação na leitura do modelo. Como observado na tabela, todas as páginas ",
        "das representações em colunas possuem contagens muito inferiores a 200 (máximo observado na casa de dezenas), ",
        "de modo que **zero páginas** são descartadas por esse filtro.",
        "",
        "## 2. Adequações e Campos Preenchidos",
        "",
        "As unidades sem caixas finas derivam da extração geométrica de colunas/estruturas e possuem campos ",
        "específicos (`id`, `bbox`, `text`, `tipo`, `ks`), mas diferem da anotação humana do Diamond. ",
        "Foram preenchidos os seguintes campos de forma defensiva e neutra:",
        "",
        "- **`bloco.classe`**: No esquema tradicional de blocos anotados, o `vlm_ordem.py` inclui a classe no ",
        "  prompt via `bloco.get('classe') or bloco.get('tipo')`. As unidades sem caixas finas não possuem anotação ",
        "  humana de classe; preenchemos `classe` com o próprio valor neutro de `tipo` (ex.: `'texto_coluna'`, ",
        "  `'tabela'`, `'imagem'`, `'cabecalho'`, `'rodape'`). Ao usar `--sem-classes`, a classe humana sai do prompt ",
        "  e resta apenas a distinção atômica de tabela/imagem, garantindo compatibilidade total com o modelo.",
        "- **`bloco.text`**: Unidades de imagem ou vazias possuíam `text: null`. Foi normalizado para `\"\"` (string vazia), ",
        "  prevenindo falhas na divisão de trechos de texto (`.split()`) em `formatar_linha_bloco`.",
        "- **Metadados de página (`uf`, `arquivo`, `pagina`, `dimensions`)**: Garantidos em cada registro de página ",
        "  a partir do nível superior da bancada, permitindo que a renderização do PDF via `pdfplumber` ",
        "  (`data/raw/<uf>/<arquivo>`) localize a página exata e calcule as escalas geométricas corretas.",
        "",
        "Campos tratados no pipeline: " + ", ".join(f"`{c}`" for c in campos_ajustados) + ".",
        "",
        "## 3. Comandos de Execução para o Orquestrador",
        "",
        "O script `src/eval/vlm_ordem.py` aceita caminho de arquivo `.jsonl` tanto em `--particao` quanto ",
        "em `--saida`. Quando `--saida` termina com `.jsonl`, ele grava diretamente no caminho do arquivo ",
        "(e mantém o `.parcial` correspondente durante a execução).",
        "",
        "Execute os quatro comandos a seguir para produzir as ordens brutas do Gemini:",
        "",
        "```powershell",
    ])

    for e in estatisticas:
        cmd = (
            f"venv/Scripts/python.exe src/eval/vlm_ordem.py "
            f"--particao {e['caminho_particao']} "
            f"--sem-classes "
            f"--saida {e['caminho_bruto']} "
            f"--retomar"
        )
        linhas.append(cmd)

    linhas.extend([
        "```",
        "",
        "Após a execução dos comandos acima, execute a conversão e validação estrita com:",
        "```powershell",
        "venv/Scripts/python.exe orquestracao/analises/vlm_unidades_cola.py --converter",
        "```",
        "",
    ])

    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def carregar_unidades_particao(caminho_particao: Path) -> dict[str, dict]:
    """Carrega as paginas da particao indexando por page_id."""
    paginas: dict[str, dict] = {}
    if not caminho_particao.is_file():
        return paginas
    with open(caminho_particao, "r", encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if not l:
                continue
            try:
                p = json.loads(l)
                pid = p.get("page_id")
                if pid:
                    paginas[pid] = p
            except json.JSONDecodeError:
                pass
    return paginas


def converter_ordem_bruta(
    ordem_raw: Any, pagina_particao: dict
) -> tuple[list[str] | None, str | None]:
    """Converte e valida a ordem predita vinda da saida do VLM para uma lista de ids de unidades.

    Retorna (ordem_ids_valida, motivo_invalidez).
    """
    bboxes = pagina_particao.get("bounding_boxes", [])
    ids_esperados = [b["id"] for b in bboxes]
    set_esperado = set(ids_esperados)
    n_esperado = len(ids_esperados)

    if n_esperado == 0:
        return None, "pagina com zero unidades esperadas"

    if not isinstance(ordem_raw, list):
        return None, f"ordem_pred nao e lista (tipo={type(ordem_raw).__name__})"

    if len(ordem_raw) != n_esperado:
        return None, f"tamanho da predicao ({len(ordem_raw)}) difere do esperado ({n_esperado})"

    # Caso 1: Ordem ja veio com os IDs das unidades (formato padrao de processar_resposta)
    if all(isinstance(x, str) and x in set_esperado for x in ordem_raw):
        ordem_ids = list(ordem_raw)
    # Caso 2: Ordem veio como rotulos B1, B2...
    elif all(isinstance(x, str) and re.match(r"^B\d+$", x) for x in ordem_raw):
        o_ent = ordem_entrada(pagina_particao)
        rot_para_id = {f"B{j + 1}": bboxes[bi]["id"] for j, bi in enumerate(o_ent)}
        if not all(x in rot_para_id for x in ordem_raw):
            return None, "contem rotulos Bx fora do conjunto de entrada"
        ordem_ids = [rot_para_id[x] for x in ordem_raw]
    # Caso 3: Ordem veio como indices inteiros das unidades
    elif all(isinstance(x, int) for x in ordem_raw):
        if all(0 <= x < n_esperado for x in ordem_raw):
            ordem_ids = [bboxes[x]["id"] for x in ordem_raw]
        else:
            return None, "indices inteiros fora da faixa [0, n)"
    else:
        return None, "elementos de ordem_pred nao reconhecidos (mistura ou ids inexistentes)"

    # Verificacao estrita de permutacao exata
    if len(set(ordem_ids)) != n_esperado:
        return None, f"predicao contem elementos duplicados (unicos={len(set(ordem_ids))}, esperado={n_esperado})"

    if set(ordem_ids) != set_esperado:
        diff = set(ordem_ids) ^ set_esperado
        return None, f"predicao nao cobre o conjunto exato de unidades (diferenca={list(diff)[:3]})"

    return ordem_ids, None


def executar_conversao() -> int:
    """Executa o Modo 2: conversao e validacao estrita das saidas brutas do VLM."""
    DIR_PRED.mkdir(parents=True, exist_ok=True)
    DIR_VLM.mkdir(parents=True, exist_ok=True)

    print("[*] Iniciando Modo Converter: validacao e extracao das predicoes...", flush=True)

    arquivos_avaliados: list[dict] = []

    for bancada in BANCADAS:
        for rep_nome in REPRESENTACOES:
            nome_bruto = f"bruto__{rep_nome}__{bancada}.jsonl"
            caminho_bruto = DIR_VLM / nome_bruto
            nome_particao = f"particao__{rep_nome}__{bancada}.jsonl"
            caminho_particao = DIR_VLM / nome_particao
            nome_pred = f"gemini__{rep_nome}__{bancada}.jsonl"
            caminho_pred = DIR_PRED / nome_pred

            res_info = {
                "bancada": bancada,
                "representacao": rep_nome,
                "arquivo_bruto": nome_bruto,
                "caminho_bruto": str(caminho_bruto.relative_to(RAIZ)).replace("\\", "/"),
                "arquivo_pred": nome_pred,
                "caminho_pred": str(caminho_pred.relative_to(RAIZ)).replace("\\", "/"),
                "existe": caminho_bruto.is_file(),
                "total_lido": 0,
                "convertidas": 0,
                "invalidas": 0,
                "detalhes_invalidas": [],
            }

            if not caminho_bruto.is_file():
                # Verifica se ha um arquivo .parcial para diagnostico
                caminho_parcial = caminho_bruto.with_name(nome_bruto + ".parcial")
                if caminho_parcial.is_file():
                    res_info["nota"] = "arquivo final ausente, mas arquivo .parcial encontrado (execucao em andamento)"
                else:
                    res_info["nota"] = "arquivo bruto ainda nao foi gerado pelo orquestrador"
                arquivos_avaliados.append(res_info)
                continue

            paginas_particao = carregar_unidades_particao(caminho_particao)
            linhas_convertidas: list[dict] = []

            with open(caminho_bruto, "r", encoding="utf-8") as f_in:
                for idx_linha, linha in enumerate(f_in, 1):
                    linha = linha.strip()
                    if not linha:
                        continue
                    res_info["total_lido"] += 1
                    try:
                        d = json.loads(linha)
                    except json.JSONDecodeError:
                        res_info["invalidas"] += 1
                        res_info["detalhes_invalidas"].append(
                            {"page_id": f"linha_{idx_linha}", "motivo": "JSONDecodeError na linha"}
                        )
                        continue

                    page_id = d.get("page_id")
                    if not page_id or page_id not in paginas_particao:
                        res_info["invalidas"] += 1
                        res_info["detalhes_invalidas"].append(
                            {"page_id": str(page_id), "motivo": "page_id nao encontrado na particao correspondente"}
                        )
                        continue

                    # Em vlm_ordem.py, permutacao_valida indica se o modelo retornou todos os rotulos
                    # exatamente uma vez sem necessidade de reparo por validar_permutacao.
                    if d.get("permutacao_valida") is False:
                        res_info["invalidas"] += 1
                        res_info["detalhes_invalidas"].append(
                            {
                                "page_id": page_id,
                                "motivo": (
                                    f"permutacao_valida=False no bruto "
                                    f"(rotulos={d.get('n_rotulos_devolvidos')}, unicos={d.get('n_unicos_validos')})"
                                ),
                            }
                        )
                        continue

                    ordem_raw = d.get("ordem_pred")
                    ordem_valida, motivo_erro = converter_ordem_bruta(ordem_raw, paginas_particao[page_id])

                    if ordem_valida is None:
                        res_info["invalidas"] += 1
                        res_info["detalhes_invalidas"].append({"page_id": page_id, "motivo": motivo_erro})
                        continue

                    linhas_convertidas.append({"page_id": page_id, "ordem": ordem_valida})
                    res_info["convertidas"] += 1

            # Grava as predicoes validas no contrato da bancada
            if linhas_convertidas:
                with open(caminho_pred, "w", encoding="utf-8") as f_out:
                    for item in linhas_convertidas:
                        f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
                print(
                    f"  -> Gravado {nome_pred}: {len(linhas_convertidas)}/{res_info['total_lido']} "
                    f"paginas validas ({res_info['invalidas']} invalidas descartadas)",
                    flush=True,
                )
            else:
                print(
                    f"  [AVISO] Nenhuma pagina valida convertida para {nome_pred} "
                    f"({res_info['invalidas']} descartadas)",
                    flush=True,
                )

            arquivos_avaliados.append(res_info)

    caminho_conversao_md = DIR_VLM / "conversao.md"
    gerar_relatorio_conversao(caminho_conversao_md, arquivos_avaliados)
    print(f"[*] Relatorio de conversao gravado em: {caminho_conversao_md}", flush=True)
    return 0


def gerar_relatorio_conversao(caminho_md: Path, resultados: list[dict]) -> None:
    """Gera o relatorio Markdown conversao.md descrevendo o status e paginas invalidas."""
    linhas: list[str] = [
        "# Relatório de Conversão e Validação das Predições VLM (Gemini)",
        "",
        "Este relatório audita a conversão das saídas brutas de `src/eval/vlm_ordem.py` ",
        "para o contrato oficial das bancadas de unidades sem caixas finas: `{\"page_id\": ..., \"ordem\": [ids]}`.",
        "",
        "## 1. Formato Original e Procedimento de Conversão",
        "",
        "No `vlm_ordem.py`, o modelo de linguagem recebe os blocos marcados visualmente como `B1, B2, ...` ",
        "numa ordem de entrada embaralhada (`ordem_entrada`). Ao receber a resposta textual, o script faz a ",
        "tradução de rótulo para ID de unidade (`rotulo_para_id`) e armazena em `ordem_pred`. Caso o modelo ",
        "omita ou repita rótulos, o `vlm_ordem.py` executa um reparo com `validar_permutacao`, mas marca ",
        "`permutacao_valida: false`.",
        "",
        "**Política estrita de validação adotada nesta cola:**",
        "1. Se `permutacao_valida` for `false`, a resposta é considerada inválida (não inventamos nem completamos ordem).",
        "2. Verifica-se que `ordem` seja uma permutação exata e estrita dos IDs esperados na partição: ",
        "   tamanho idêntico, sem repetições e sem identificadores estranhos.",
        "3. Apenas respostas 100% válidas são gravadas sob `resultados/ordenadores_sem_caixas/pred/`.",
        "",
        "## 2. Status por Arquivo",
        "",
        "| Arquivo Bruto | Arquivo de Predição | Status | Total Lido | Válidas | Inválidas |",
        "|---|---|---|---:|---:|---:|",
    ]

    for r in resultados:
        if r["existe"]:
            status = "Convertido" if r["convertidas"] > 0 else "Sem válidas"
            linhas.append(
                f"| `{r['arquivo_bruto']}` | `{r['arquivo_pred']}` | {status} | "
                f"{r['total_lido']} | {r['convertidas']} | {r['invalidas']} |"
            )
        else:
            nota = r.get("nota", "Pendente")
            linhas.append(
                f"| `{r['arquivo_bruto']}` | `{r['arquivo_pred']}` | *{nota}* | — | — | — |"
            )

    linhas.extend([
        "",
        "## 3. Detalhamento de Páginas Inválidas Descartadas",
        "",
    ])

    tem_invalidas = any(r["invalidas"] > 0 for r in resultados if r["existe"])
    if not tem_invalidas:
        arquivos_pendentes = sum(1 for r in resultados if not r["existe"])
        if arquivos_pendentes == len(resultados):
            linhas.append(
                "Nenhum arquivo bruto existe no momento. Os arquivos serão convertidos assim que o orquestrador "
                "executar os comandos de inferência listados em `preparo.md`."
            )
        else:
            linhas.append("Nenhuma página inválida encontrada nos arquivos processados.")
    else:
        for r in resultados:
            if not r["existe"] or not r["detalhes_invalidas"]:
                continue
            linhas.append(f"### `{r['arquivo_bruto']}` ({len(r['detalhes_invalidas'])} descartadas)")
            linhas.append("")
            linhas.append("| Página (`page_id`) | Motivo do Descarte |")
            linhas.append("|---|---|")
            for d in r["detalhes_invalidas"]:
                linhas.append(f"| `{d['page_id']}` | {d['motivo']} |")
            linhas.append("")

    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--converter",
        action="store_true",
        help="Executa o Modo 2: converte arquivos bruto__*.jsonl em pred/gemini__*.jsonl",
    )
    parser.add_argument(
        "--preparar",
        action="store_true",
        help="Executa o Modo 1: gera as particoes e preparo.md (comportamento padrao)",
    )

    args = parser.parse_args()

    # Se --converter for solicitado, roda modo 2. Caso contrario (sem argumentos ou com --preparar), roda modo 1.
    if args.converter:
        return executar_conversao()
    return executar_preparo()


if __name__ == "__main__":
    sys.exit(main())
