import json

def call_llm_extractor(text_snippet):
    """
    Mock que simula a chamada de uma API de LLM (como OpenAI, Anthropic, ou Llama local via Ollama).
    Recebe um trecho de texto do diário e retorna um JSON estruturado com a licitação extraída.
    """
    print("[*] Enviando requisição para a LLM...")
    
    # Simulação de prompt interno e geração do retorno
    mock_response_json = {
        "tipo_documento": "Aviso de Licitação",
        "objeto": "Aquisição de equipamentos de informática para a UFG",
        "orgao_demandante": "Universidade Federal de Goiás",
        "data_abertura": "15/09/2026",
        "valor_estimado": 150000.00
    }
    
    return mock_response_json

if __name__ == "__main__":
    text = "AVISO DE LICITAÇÃO. OBJETO: Aquisição de equipamentos de informática para a UFG. DATA: 15/09/2026. VALOR: R$ 150.000,00."
    extracted_data = call_llm_extractor(text)
    print("\n[+] Dados extraídos estruturados pela LLM (Gabarito de Teste):")
    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))
