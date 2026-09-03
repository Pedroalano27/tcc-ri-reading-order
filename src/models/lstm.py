import torch
import torch.nn as nn

class DiarioLSTM(nn.Module):
    """
    Arquitetura de rede neural recorrente (LSTM) projetada para tarefas de processamento de texto.
    Pode ser pré-treinada para prever a próxima palavra (Modelagem de Linguagem)
    e depois adaptada (fine-tuned) para classificação ou extração de entidades.
    """
    def __init__(self, vocab_size, embedding_dim, hidden_dim, output_dim, num_layers=2):
        super(DiarioLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            embedding_dim, 
            hidden_dim, 
            num_layers=num_layers, 
            batch_first=True, 
            bidirectional=True  # Bi-LSTM para capturar contexto esquerdo e direito
        )
        # Como é bidirecional, a dimensão de entrada da linear é hidden_dim * 2
        self.fc = nn.Linear(hidden_dim * 2, output_dim)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)
        predictions = self.fc(lstm_out)
        return predictions

if __name__ == "__main__":
    print("[*] Instanciando modelo LSTM de teste...")
    # Parâmetros fictícios de teste
    vocab_size = 1000  # Tamanho do vocabulário
    embedding_dim = 128
    hidden_dim = 256
    output_dim = 5     # Ex: 5 tipos de entidades jurídicas (Rótulos)
    
    model = DiarioLSTM(vocab_size, embedding_dim, hidden_dim, output_dim)
    print(model)
    
    # Criando entrada fictícia (batch_size=2, sequence_length=10)
    test_input = torch.randint(0, vocab_size, (2, 10))
    output = model(test_input)
    print(f"\n[+] Sucesso! Formato de saída do modelo (Batch, Seq_Len, Classes): {output.shape}")
