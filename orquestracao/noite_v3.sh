#!/bin/bash
# Roteiro da noite de 12 para 13/09/2026: tudo o que roda sem o Pedro, sobre a segmentacao v3.
# Um passo por vez na GPU; cada passo grava log proprio e uma linha em status.jsonl, e uma falha
# NAO interrompe os passos seguintes. Retomavel: a curva pula o que ja esta em curva.json.
#
#   bash orquestracao/noite_v3.sh
#
# Nao faz commit, nao publica nada e nao toca em data/raw nem em anotacoes.jsonl.
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
LOGS=orquestracao/logs/noite_v3
mkdir -p "$LOGS"
STATUS="$LOGS/status.jsonl"

passo() {   # passo <nome> <comando...>
  local nome=$1; shift
  local ini=$(date '+%Y-%m-%d %H:%M:%S')
  echo "=== $ini $nome: $*" | tee -a "$LOGS/roteiro.log"
  "$@" > "$LOGS/$nome.log" 2>&1
  local cod=$?
  local fim=$(date '+%Y-%m-%d %H:%M:%S')
  echo "{\"passo\": \"$nome\", \"inicio\": \"$ini\", \"fim\": \"$fim\", \"codigo\": $cod}" >> "$STATUS"
  echo "    -> codigo $cod ($fim)" | tee -a "$LOGS/roteiro.log"
  return $cod
}

# Impede a suspensao por inatividade enquanto o roteiro roda (SetThreadExecutionState com
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED, o mesmo pedido que um tocador de video faz; nao muda
# configuracao nenhuma e acaba junto com o processo). Tampa fechada ainda suspende.
$PY -c "import ctypes, time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(14 * 3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

# 0. Espera a T05 (re-extracao das tres colecoes) terminar
while [ ! -f resultados/qualidade_segmentacao_v3_blocos_extra.json ]; do sleep 60; done
echo "=== $(date '+%H:%M') T05 concluida" | tee -a "$LOGS/roteiro.log"

# 1. Pacote do Kaggle (so para as LLMs de 27-35B, que nao cabem na 4050)
passo pacote_kaggle $PY src/kaggle/montar_pacote.py

# 2. Colecao de RI (Japeri) com filtro de 1 bloco: pagina que e so uma tabela tem texto a indexar
passo ri_japeri_reextrair $PY src/data/reextrair.py --entrada data/processed/blocos_ri_japeri_v1 \
  --saida data/processed/blocos_ri_japeri --workers 4 --min-blocos 1
cp resultados/qualidade_segmentacao.json resultados/qualidade_segmentacao_v3_blocos_ri_japeri.json

# 3. BiLSTM, tres variantes (tabela principal)
for v in geo texto geo_texto; do
  passo lstm_$v $PY src/models/lstm_ordem.py --variante $v
done

# 4. Curva de aprendizado das duas formulacoes do LayoutLM + BiLSTM geometrica
passo curva $PY src/rodar_curva_aprendizado.py --modelos layoutlm_sucessor layoutlm lstm_geo --micro-batch 4

# 5. Maiores checkpoints da curva viram os modelos padrao da v3 (os da v1 estao em
#    models/layoutlm_ordem_segmentacao_v1/)
N=$($PY -c "import json; print(json.load(open('resultados/curva_aprendizado/curva.json'))['tamanhos'][-1])")
M=models/layoutlm_ordem
for par in "curva_layoutlm_n$N:layoutlm" "curva_layoutlm_sucessor_n$N:layoutlm_sucessor"; do
  de=${par%%:*}; para=${par##*:}
  if [ -f "$M/$de.pt" ] && [ -f models/layoutlm_ordem_segmentacao_v1/$para.pt ]; then
    cp "$M/$de.pt" "$M/$para.pt"; cp "$M/${de}_config.json" "$M/${para}_config.json"
    echo "    $de -> $para" | tee -a "$LOGS/roteiro.log"
  fi
done

# 6. Predicoes das duas formulacoes no teste, varredura do limiar e busca em feixe
passo layoutlm_avaliar $PY src/models/layoutlm_ordem.py avaliar --nome layoutlm
passo sucessor_avaliar $PY src/models/layoutlm_sucessor.py avaliar --nome layoutlm_sucessor
for lim in 0.0 0.3 0.7 0.9; do
  passo sucessor_limiar_$lim $PY src/models/layoutlm_sucessor.py avaliar --nome layoutlm_sucessor \
    --decodificacao cadeias --limiar-cadeia $lim --metodo suc_limiar_${lim/./}
done
passo sucessor_feixe $PY src/models/layoutlm_sucessor.py avaliar --nome layoutlm_sucessor \
  --decodificacao feixe --metodo layoutlm_sucessor_feixe

# 7. Contra a anotacao humana (golden_v3), com os checkpoints da v3
passo golden_v3 $PY src/eval/avaliar_golden.py --lote _avaliacao/golden_v3

# 8. Tabela e figuras com o que ja existe
passo comparar $PY src/eval/comparar.py
passo curva_figura $PY src/rodar_curva_aprendizado.py --so-figura

# 9. Piloto de RI em Japeri na v3
passo ri_japeri_piloto $PY src/ri/piloto_japeri.py

# 10. Latencia na 4050
passo latencia $PY src/eval/latencia_hardware.py --maquina rtx4050_v3

# 11. Ablacoes da formulacao de sucessor no maior treino (as mais longas ficam por ultimo)
for ab in "sem_vies_geo:--sem-vies-geo" "sem_posicao:--peso-posicao 0" "sem_layout:--sem-layout"; do
  nome=ablacao_suc_${ab%%:*}; flags=${ab#*:}
  passo ${nome}_treinar $PY src/models/layoutlm_sucessor.py treinar --nome $nome --n-treino $N $flags \
    --blocos-extra data/processed/blocos_extra --epocas 4 --max-minutos 60 --micro-batch 4 \
    && passo ${nome}_avaliar $PY src/models/layoutlm_sucessor.py avaliar --nome $nome $flags
done
passo comparar_final $PY src/eval/comparar.py

# 12. Relatorio da manha, escrito pelo Antigravity (Gemini) a partir dos arquivos de resultado
passo relatorio_antigravity $PY orquestracao/despachar.py --agente antigravity --tarefa T13 \
  --prompt orquestracao/prompts/T13_relatorio_noite_v3.md --timeout-min 45 --escopo docs/RELATORIO_NOITE_V3.md

echo "=== $(date '+%Y-%m-%d %H:%M') FIM DO ROTEIRO" | tee -a "$LOGS/roteiro.log"
