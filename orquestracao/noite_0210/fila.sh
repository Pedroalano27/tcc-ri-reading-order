#!/bin/bash
# Fila de agentes da noite (versao 2, 03/10). Uso: bash orquestracao/noite_0210/fila.sh codex|agy
# Roda UMA tarefa por vez: a de menor numero entre as orquestracao/noite_0210/<fila>/NN_*.txt que ainda
# nao tem .done/.falhou e cujas dependencias (#ESPERA) ja existem. Depois de cada tarefa volta ao inicio
# da lista: tarefa de numero baixo que ficou pronta passa na frente, e tarefas novas entram sozinhas.
# Retomavel: depois de uma queda basta rodar de novo (ver iniciar.ps1). Para parar: criar noite_0210/STOP.
#
# Cabecalhos opcionais nas primeiras linhas do .txt (linhas com # nao vao para o agente):
#   #ESPERA: caminho     so roda quando esse arquivo existir (pode repetir; nao bloqueia a fila)
#   #SCRIPT: caminho.py  (agy) script que o agente deve escrever; a fila executa e devolve o erro
#   #SAIDA:  caminho.md  arquivo que precisa existir no fim
cd "$(dirname "$0")/../.." || exit 1
export PYTHONIOENCODING=utf-8
PY=venv/Scripts/python.exe
D=orquestracao/noite_0210
FILA=$1
[ "$FILA" = codex ] || [ "$FILA" = agy ] || { echo "uso: fila.sh codex|agy"; exit 2; }
INICIO=$(date +%s)
COMUM="$(cat $D/comum.txt)"
log(){ echo "$(date '+%d/%m %H:%M:%S') [$FILA] $*" >> "$D/fila.log"; }
campo(){ grep -m1 "^#$1:" "$2" | sed "s/^#$1:[[:space:]]*//" | tr -d '\r'; }
corpo(){ grep -v '^#' "$1"; }
pronta(){ local alvo
  while read -r alvo; do [ -z "$alvo" ] || [ -e "$alvo" ] || return 1
  done < <(grep "^#ESPERA:" "$1" | sed 's/^#ESPERA:[[:space:]]*//' | tr -d '\r'); return 0; }

# o historico da maquina mostra queda ao dormir: segura acordada enquanto a fila existir
$PY -c "import ctypes,time; ctypes.windll.kernel32.SetThreadExecutionState(0x80000001); time.sleep(11*3600)" &
ACORDADO=$!
trap 'kill $ACORDADO 2>/dev/null' EXIT

# os agentes nao podem gravar em data/: avisa no log se algo mudou durante a tarefa
vigia(){ local marca=$1 nome=$2 mud
  mud=$(find data/raw data/golden data/diamond data/labelstudio data/deteccao -newer "$marca" -type f 2>/dev/null \
        | grep -v "data/diamond/massa1_gemini/" | head -5 | tr '\n' ' ')
  [ -n "$mud" ] && log "ALERTA: arquivos sob data/ mudaram durante $nome: ${mud:0:400}"; }

rodar_codex(){ local f=$1 base=${1%.txt} saida rc t0 dt n
  saida=$(campo SAIDA "$f"); n=$(( $(ls "$base".t*.log 2>/dev/null | wc -l) + 1 ))
  t0=$(date +%s)
  { echo "$COMUM"; echo; corpo "$f"; } | codex exec -m gpt-6.1-sol -c 'model_reasoning_effort="xhigh"' \
      -s workspace-write -o "$base.out.md" - > "$base.t$n.log" 2>&1
  rc=$?; dt=$(( $(date +%s) - t0 ))
  if [ $rc -eq 0 ] && [ -s "$base.out.md" ]; then
    touch "$base.done"
    log "codex ok $(basename "$f") em $((dt/60)) min$( [ -n "$saida" ] && [ ! -s "$saida" ] && echo " (ATENCAO: nao gerou $saida)")"
    return; fi
  if [ $dt -lt 120 ]; then          # caiu na hora: limite de uso, rede ou login. Nao gasta a fila inteira.
    mv -f "$base.t$n.log" "$base.rapida.log"
    log "codex FALHA RAPIDA em $(basename "$f") (rc=$rc, ${dt}s): $(tail -2 "$base.rapida.log" | tr '\n' ' ' | cut -c1-180) | espero 20 min"
    sleep 1200; return; fi
  log "codex tentativa $n de $(basename "$f") falhou (rc=$rc, $((dt/60)) min)"
  [ $n -ge 2 ] && { touch "$base.falhou"; log "codex DESISTIU de $(basename "$f")"; }; }

rodar_agy(){ local f=$1 base=${1%.txt} script saida P rc rodada t0 dt
  script=$(campo SCRIPT "$f"); saida=$(campo SAIDA "$f")
  P="$COMUM

$(corpo "$f")"
  for rodada in 1 2 3 4 5; do
    [ -f "$D/STOP" ] && return
    t0=$(date +%s)
    agy --model gemini-3.8-flash-high --mode accept-edits --print-timeout 1500s -p="$P" < /dev/null > "$base.r$rodada.agy.log" 2>&1
    dt=$(( $(date +%s) - t0 ))
    if [ -z "$script" ]; then                      # tarefa so de leitura/escrita de relatorio
      [ -s "$saida" ] && { touch "$base.done"; log "agy ok $(basename "$f")"; return; }
      [ $dt -lt 20 ] && { log "agy FALHA RAPIDA em $(basename "$f") (${dt}s): $(tail -2 "$base.r$rodada.agy.log" | tr '\n' ' ' | cut -c1-180) | espero 20 min"; sleep 1200; return; }
      P="$COMUM

Voce nao criou o arquivo $saida. Crie-o agora. Tarefa original:
$(corpo "$f")"; continue
    fi
    if [ ! -f "$script" ]; then
      [ $dt -lt 20 ] && { log "agy FALHA RAPIDA em $(basename "$f") (${dt}s): $(tail -2 "$base.r$rodada.agy.log" | tr '\n' ' ' | cut -c1-180) | espero 20 min"; sleep 1200; return; }
      rc=99; echo "arquivo $script nao foi criado" > "$base.r$rodada.exec.log"
    else timeout 2700 $PY "$script" > "$base.r$rodada.exec.log" 2>&1; rc=$?; fi
    if [ $rc -eq 0 ] && [ -s "$saida" ]; then touch "$base.done"; log "agy ok $(basename "$f") na rodada $rodada"; return; fi
    log "agy rodada $rodada de $(basename "$f") falhou (rc=$rc): $(tail -1 "$base.r$rodada.exec.log" | cut -c1-140)"
    P="$COMUM

O orquestrador executou o script que voce escreveu ($PY $script) e ele FALHOU (codigo $rc) ou nao gerou $saida.
Fim da saida da execucao:
-----
$(tail -45 "$base.r$rodada.exec.log")
-----
Leia o seu script, ache a causa e CORRIJA o arquivo $script (edite-o). Voce nao pode rodar comandos; o orquestrador roda de novo.
Tarefa original:
$(corpo "$f")"
  done
  touch "$base.falhou"; log "agy DESISTIU de $(basename "$f")"; }

rm -f "$D/$FILA"/*.rodando          # marcadores mortos de uma execucao anterior
log "fila iniciada"
while [ ! -f "$D/STOP" ] && [ $(( $(date +%s) - INICIO )) -lt 39600 ]; do
  fez=0
  for f in $(ls "$D/$FILA"/*.txt 2>/dev/null | sort); do
    base=${f%.txt}; { [ -f "$base.done" ] || [ -f "$base.falhou" ]; } && continue
    pronta "$f" || continue
    log "comecando $(basename "$f")"; touch "$base.rodando"
    if [ "$FILA" = codex ]; then rodar_codex "$f"; else rodar_agy "$f"; fi
    vigia "$base.rodando" "$(basename "$f")"
    rm -f "$base.rodando"; fez=1; break
  done
  [ $fez -eq 1 ] || sleep 60
done
log "fila encerrada"
