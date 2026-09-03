import os
import json
import random

def create_mock_reading_order_data():
    """
    Gera um pre-dataset sintético (mock) que simula o formato de saída do YOLO/OCR
    e o padrão-ouro (ground truth) de ordem de leitura para Diários Oficiais.
    Esses arquivos podem ser usados para testar seu pipeline antes de carregar dados reais.
    """
    os.makedirs("data/predataset", exist_ok=True)
    
    # Simula 5 páginas de Diário Oficial de 2 colunas
    for page_id in range(1, 6):
        page_data = {
            "page_id": f"page_{page_id}",
            "dimensions": {"width": 1000, "height": 1400},
            "bounding_boxes": []
        }
        
        # Coluna 1 (X de 50 a 480)
        col1_boxes = [
            {"id": "col1_box1", "text": "RESOLUCAO NUMERO 402 DE 2026", "bbox": [50, 100, 480, 150]},
            {"id": "col1_box2", "text": "O Diretor do Instituto de Informatica da UFG, no uso de suas atribuicoes,", "bbox": [50, 170, 480, 250]},
            {"id": "col1_box3", "text": "resolve designar a banca examinadora do Trabalho de Conclusao de Curso.", "bbox": [50, 270, 480, 350]}
        ]
        
        # Coluna 2 (X de 520 a 950)
        col2_boxes = [
            {"id": "col2_box1", "text": "Art. 1 - Fica homologada a proposta de pesquisa do discente", "bbox": [520, 100, 950, 180]},
            {"id": "col2_box2", "text": "focada na comparacao de BERT e LLMs para ordem de leitura.", "bbox": [520, 200, 950, 280]},
            {"id": "col2_box3", "text": "Art. 2 - Esta portaria entra em vigor na data de sua publicacao.", "bbox": [520, 300, 950, 380]}
        ]
        
        # A ordem de leitura correta humana é Coluna 1 inteira, depois Coluna 2 inteira
        correct_order = ["col1_box1", "col1_box2", "col1_box3", "col2_box1", "col2_box2", "col2_box3"]
        
        # O YOLO pode detectar as caixas em ordem bagunçada (ex: alternando colunas)
        all_boxes = col1_boxes + col2_boxes
        random.shuffle(all_boxes)  # Bagunça a entrada para simular o YOLO cru
        
        page_data["bounding_boxes"] = all_boxes
        page_data["reading_order_ground_truth"] = correct_order
        
        # Salva o arquivo JSON da página
        with open(f"data/predataset/page_{page_id}.json", "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=4, ensure_ascii=False)
            
    print("[OK] Pré-dataset de testes criado com sucesso em: 'data/predataset/'")

def show_huggingface_instructions():
    """
    Imprime instruções de como baixar o dataset real de layout de leis (DocLayNet)
    usando a biblioteca Hugging Face Datasets.
    """
    print("\n--- COMO CARREGAR DATASETS REAIS DE LEIS (DocLayNet) NO PYTHON ---")
    print("Você pode instalar a biblioteca 'datasets' executando: pip install datasets")
    print("Depois, rode o seguinte código para carregar documentos de leis:")
    print("-" * 60)
    print("""from datasets import load_dataset

# Carrega o DocLayNet (contém leis, editais, relatórios em COCO format com bboxes)
dataset = load_dataset("docling-project/DocLayNet", split="train", streaming=True)

# Visualiza o primeiro exemplo
for sample in dataset:
    print("Categoria:", sample.get("doc_category"))
    print("Texto extraído:", sample.get("texts"))
    break
""")
    print("-" * 60)

if __name__ == "__main__":
    create_mock_reading_order_data()
    show_huggingface_instructions()
