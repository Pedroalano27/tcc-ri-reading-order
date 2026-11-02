# O que depende do Pedro antes (e durante) a fase intensiva

Lista do que só você pode fazer. Ordenada por impacto. Marque `[x]` quando resolver; eu
confiro antes de cada etapa que depende do item. Atualizado em 02/11/2026.

## Bloqueiam a fase intensiva

- [x] **1. Autorizar commit (e push) do trabalho acumulado.** Autorizado em 02/11 ("pode
  commitar e dar push"). Commitado na branch `golden-v1-e-segmentacao` e enviado ao GitHub.
  O repositório é **público**: caches regeneráveis (~3 GB), dados da Data Policy
  (`data/labelstudio/`) e predições sobre essas páginas ficam fora (ver `.gitignore`).

- [x] **2. Autorização da Data Policy para usar as anotações de ordem no TCC.** Confirmado
  pelo Pedro em 02/11: eles deixaram usar na pesquisa. São cerca de 417 páginas (129 PDFs)
  com ordem por caixa, mais as seeds novas. Regras que continuam valendo: os dados brutos e
  as predições página a página **não são publicados** (repositório público; só números
  agregados nos relatórios e no texto do TCC) e **não são enviados** a Gemini/Antigravity/Codex;
  processamento no PC e no cluster do CEIA.

- [ ] **3. Separar tempo para anotar o teste cego.** O lote `lote_sem_paragrafos` **não serve**
  (os 57 PDFs aparecem em outros conjuntos). O plano (E001) reserva **90 páginas cegas**
  (30 CE, 30 MA, 30 RJ, de PDFs nunca usados) + 45 de desenvolvimento, e 36 páginas no teste
  de anotação densa × simplificada (E008). Plano B: 60 cegas e 30 de desenvolvimento.
  Precisa ser anotação sua (gabarito humano). Eu preparo a ordem pré-preenchida e a ferramenta.

- [ ] **4. VPN do cluster ligada nos períodos de execução.** (O Pedro liga quando for começar.) Os jobs rodam sem a VPN, mas
  eu só consigo enviar, acompanhar e trazer resultados com ela conectada. Ideal: deixar o
  OpenVPN conectado e o PC ligado (na tomada, sem hibernar) nas noites de execução.

## Aceleram (não bloqueiam)

- [ ] **5. Token da API do Kaggle.** Em kaggle.com → Settings → API → *Create New Token*;
  salve o `kaggle.json` em `C:\Users\pedro\.kaggle\kaggle.json`. Com isso eu envio e baixo
  notebooks sozinho (hoje é upload manual). Confirme também que o telefone está verificado
  (necessário para GPU e Internet nos notebooks).

- [ ] **6. Chrome com o ChatGPT logado e a extensão Claude conectada** durante as sessões.
  Opcional: criar no ChatGPT um *Projeto* "TCC ordem de leitura" para eu concentrar as
  consultas lá (as perguntas e respostas também ficam salvas em `experimentos/consultas/`).

- [ ] **7. Perguntar ao orientador (Thierson):**
  - a procedência dos PDFs (de onde vieram os 8 ZIPs de 09/09: raspagem, Querido Diário,
    outro projeto?) — necessário para a seção de dados;
  - se aceita como contribuição principal "regra + correção aprendida" (em vez de um modelo
    ponta a ponta), já que é o que os dados indicam;
  - prazo de entrega do texto e da defesa, para eu fechar o cronograma.

- [ ] **8. Cota de uso das ferramentas.** Me diga se há limite que eu deva respeitar nesta
  fase (Claude, Codex, Gemini API). Por padrão: Codex só para implementação crítica,
  Antigravity para volume, Gemini API até ~US$ 5 por experimento.

- [ ] **9. Liberar o job 992/gaia do cluster quando for rodar o TCC.** Sua conta só roda
  1 job por vez; se o `gaia-sft` estiver na fila, os jobs do TCC esperam atrás dele.

## Já resolvido

- [x] Acesso SSH por chave à DGX Spark (27–28/10).
- [x] Contêiner PyTorch e Ollama no cluster.
- [x] Codex e Antigravity instalados e funcionando.
