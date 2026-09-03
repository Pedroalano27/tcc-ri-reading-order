import os
import pypdf

def extract_text_from_pdf(pdf_path):
    """
    Função de exemplo que extrai o texto bruto de um PDF usando a biblioteca pypdf.
    """
    print(f"[*] Iniciando extração de texto do arquivo: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[!] Erro: Arquivo {pdf_path} não encontrado. Retornando texto fictício (mock).")
        return "AVISO DE LICITAÇÃO. OBJETO: Aquisição de equipamentos de informática para a UFG. DATA: 15/09/2026. VALOR: R$ 150.000,00."
    
    text = ""
    try:
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text += page.extract_text() or ""
        print(f"[+] Extração concluída com sucesso! Total de {len(reader.pages)} páginas lidas.")
    except Exception as e:
        print(f"[!] Erro ao abrir PDF: {e}")
    
    return text

if __name__ == "__main__":
    # Testando a lógica de parsing
    sample_text = extract_text_from_pdf("data/raw/diario_exemplo.pdf")
    print(f"\n Trecho do texto extraído (primeiros 150 caracteres):\n{sample_text[:150]}...")
