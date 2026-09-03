"""
Gerador do pre-dataset sintetico de ordem de leitura.

Simula a saida de um pipeline YOLO + OCR sobre paginas de Diario Oficial:
um conjunto de bounding boxes com texto e coordenadas 2D, entregue em ordem
embaralhada, acompanhado do padrao-ouro (ground truth) da ordem de leitura.

O objetivo e validar a pipeline ponta a ponta (parsing -> modelo -> metricas)
antes de carregar o DocLayNet ou o Golden Dataset real.
"""

import os
import json
import random
import argparse

# --- Configuracao de reprodutibilidade -------------------------------------
# Seed fixa: rodar duas vezes produz exatamente o mesmo dataset. Obrigatorio
# para que os numeros reportados no TCC sejam reproduziveis.
SEED = 42
NUM_PAGES = 12
OUTPUT_DIR = os.path.join("data", "predataset")

# --- Geometria da pagina ----------------------------------------------------
PAGE_WIDTH = 1000
PAGE_HEIGHT = 1400
MARGIN = 50
GUTTER = 40           # espaco horizontal entre colunas
BOTTOM_RESERVE = 120  # area inferior reservada ao rodape

HEADER_TEXTS = [
    "DIARIO OFICIAL DO ESTADO DE GOIAS - ANO 189 - EDICAO 27.842",
    "GOVERNO DO ESTADO DE GOIAS - SECRETARIA DE ESTADO DA ADMINISTRACAO",
    "SUPLEMENTO - ATOS DO PODER EXECUTIVO",
]

FOOTER_TEXTS = [
    "Documento assinado digitalmente conforme MP n. 2.200-2 de 24/08/2001.",
    "Pagina publicada em www.diariooficial.go.gov.br",
]

BODY_TEXTS = [
    "RESOLUCAO NUMERO 402, DE 12 DE MARCO DE 2026",
    "O Diretor do Instituto de Informatica da Universidade Federal de Goias, no uso de suas atribuicoes legais e regimentais,",
    "RESOLVE designar a banca examinadora do Trabalho de Conclusao de Curso do discente abaixo relacionado.",
    "Art. 1 - Fica homologada a proposta de pesquisa apresentada pelo discente ao colegiado do curso.",
    "Art. 2 - Esta portaria entra em vigor na data de sua publicacao, revogadas as disposicoes em contrario.",
    "AVISO DE LICITACAO - PREGAO ELETRONICO NUMERO 087/2026",
    "OBJETO: Aquisicao de equipamentos de informatica destinados ao parque tecnologico da autarquia.",
    "A sessao publica sera realizada em 15 de setembro de 2026, as 09h00, no portal de compras do Estado.",
    "EXTRATO DE CONTRATO - Processo Administrativo numero 202600012345678",
    "CONTRATANTE: Secretaria de Estado da Economia. CONTRATADA: empresa vencedora do certame licitatorio.",
    "VALOR GLOBAL ESTIMADO: R$ 150.000,00 (cento e cinquenta mil reais), conforme dotacao orcamentaria.",
    "PORTARIA DE NOMEACAO - O Secretario de Estado, no uso de suas atribuicoes,",
    "nomeia para o cargo de provimento em comissao os servidores constantes do anexo unico desta portaria.",
    "DESPACHO: Defiro o pedido de prorrogacao de prazo formulado pelo interessado nos autos do processo.",
    "ERRATA - Na publicacao veiculada na edicao anterior, onde se le 30 de abril, leia-se 30 de maio.",
]


def build_page(page_index, rng):
    """
    Monta uma pagina sintetica com layout variavel.

    A variacao cobre os casos que quebram heuristicas ingenuas de ordenacao:
    numero de colunas diferente, cabecalho e rodape que atravessam a largura
    inteira (e portanto nao pertencem a nenhuma coluna) e quantidade
    irregular de blocos por coluna.
    """
    n_cols = rng.choice([1, 2, 2, 3])   # 2 colunas e o caso mais comum em diarios
    has_header = rng.random() < 0.7
    has_footer = rng.random() < 0.4

    boxes = []
    reading_order = []

    y_cursor_top = MARGIN

    # Cabecalho: ocupa a largura inteira, acima de todas as colunas.
    if has_header:
        height = rng.randint(40, 70)
        box_id = "header"
        boxes.append({
            "id": box_id,
            "text": rng.choice(HEADER_TEXTS),
            "bbox": [MARGIN, y_cursor_top, PAGE_WIDTH - MARGIN, y_cursor_top + height],
        })
        reading_order.append(box_id)
        y_cursor_top += height + 30

    body_top = y_cursor_top
    col_width = (PAGE_WIDTH - 2 * MARGIN - (n_cols - 1) * GUTTER) // n_cols

    # Corpo: cada coluna e preenchida de cima para baixo. A ordem de leitura
    # correta e coluna por coluna (nao linha por linha) -- exatamente o que o
    # detector de layout erra.
    for col in range(n_cols):
        x0 = MARGIN + col * (col_width + GUTTER)
        x1 = x0 + col_width
        y = body_top
        n_blocks = rng.randint(2, 5)

        for block in range(n_blocks):
            height = rng.randint(50, 110)
            if y + height > PAGE_HEIGHT - MARGIN - BOTTOM_RESERVE:
                break
            box_id = f"col{col + 1}_box{block + 1}"
            boxes.append({
                "id": box_id,
                "text": rng.choice(BODY_TEXTS),
                "bbox": [x0, y, x1, y + height],
            })
            reading_order.append(box_id)
            y += height + rng.randint(15, 30)

    # Rodape: largura inteira, lido por ultimo.
    if has_footer:
        height = 35
        y0 = PAGE_HEIGHT - MARGIN - height
        box_id = "footer"
        boxes.append({
            "id": box_id,
            "text": rng.choice(FOOTER_TEXTS),
            "bbox": [MARGIN, y0, PAGE_WIDTH - MARGIN, y0 + height],
        })
        reading_order.append(box_id)

    # Embaralha a entrada para simular a ordem crua do detector. Repete ate
    # obter uma ordem diferente do padrao-ouro: uma pagina que ja chega
    # ordenada nao exercita nada e inflaria as metricas artificialmente.
    shuffled = list(boxes)
    for _ in range(10):
        rng.shuffle(shuffled)
        if [b["id"] for b in shuffled] != reading_order:
            break

    return {
        "page_id": f"page_{page_index}",
        "dimensions": {"width": PAGE_WIDTH, "height": PAGE_HEIGHT},
        "layout": {
            "n_columns": n_cols,
            "has_header": has_header,
            "has_footer": has_footer,
            "n_boxes": len(boxes),
        },
        "bounding_boxes": shuffled,
        "reading_order_ground_truth": reading_order,
    }


def create_mock_reading_order_data(num_pages=NUM_PAGES, seed=SEED, output_dir=OUTPUT_DIR):
    """Gera as paginas sinteticas e salva um arquivo JSON por pagina."""
    rng = random.Random(seed)
    os.makedirs(output_dir, exist_ok=True)

    # Remove paginas de execucoes anteriores para nao misturar datasets de
    # seeds diferentes no mesmo diretorio.
    for stale in os.listdir(output_dir):
        if stale.startswith("page_") and stale.endswith(".json"):
            os.remove(os.path.join(output_dir, stale))

    layouts = []
    for page_index in range(1, num_pages + 1):
        page_data = build_page(page_index, rng)
        layouts.append(page_data["layout"])

        path = os.path.join(output_dir, f"page_{page_index}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=4, ensure_ascii=False)

    print(f"[OK] {num_pages} paginas geradas em '{output_dir}' (seed={seed})")
    print("\n--- DISTRIBUICAO DOS LAYOUTS GERADOS ---")
    for n in sorted({l["n_columns"] for l in layouts}):
        count = sum(1 for l in layouts if l["n_columns"] == n)
        print(f"  {n} coluna(s): {count} pagina(s)")
    print(f"  com cabecalho: {sum(1 for l in layouts if l['has_header'])} pagina(s)")
    print(f"  com rodape:    {sum(1 for l in layouts if l['has_footer'])} pagina(s)")
    print(f"  caixas por pagina: min={min(l['n_boxes'] for l in layouts)}, "
          f"max={max(l['n_boxes'] for l in layouts)}")


def show_huggingface_instructions():
    """Instrucoes para carregar o dataset real (DocLayNet) via Hugging Face."""
    print("\n--- COMO CARREGAR DATASETS REAIS DE LEIS (DocLayNet) NO PYTHON ---")
    print("Instale a biblioteca executando: pip install datasets")
    print("Depois, rode o seguinte codigo para carregar documentos de leis:")
    print("-" * 60)
    print("""from datasets import load_dataset

# Carrega o DocLayNet (contem leis, editais, relatorios em COCO format com bboxes)
dataset = load_dataset("docling-project/DocLayNet", split="train", streaming=True)

# Visualiza o primeiro exemplo
for sample in dataset:
    print("Categoria:", sample.get("doc_category"))
    print("Texto extraido:", sample.get("texts"))
    break
""")
    print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera o pre-dataset sintetico de ordem de leitura.")
    parser.add_argument("--pages", type=int, default=NUM_PAGES, help=f"numero de paginas (padrao: {NUM_PAGES})")
    parser.add_argument("--seed", type=int, default=SEED, help=f"seed de reprodutibilidade (padrao: {SEED})")
    args = parser.parse_args()

    create_mock_reading_order_data(num_pages=args.pages, seed=args.seed)
    show_huggingface_instructions()
