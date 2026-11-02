#!/bin/bash
# Estado compacto da noite (para o orquestrador ler gastando pouco). So le, nao muda nada.
cd "$(dirname "$0")/../.." || exit 1
D=orquestracao/noite_0210
echo "== $(date '+%d/%m %H:%M') | GPU $(nvidia-smi --query-gpu=memory.used,utilization.gpu,temperature.gpu --format=csv,noheader 2>/dev/null)"
echo "== treino: $(tail -1 orquestracao/logs/noite_detector_ls/roteiro.log 2>/dev/null | cut -c1-80)"
for m in ls3 ls16; do
  [ -f runs/detect/$m/results.csv ] && echo "   $m epoca $(tail -1 runs/detect/$m/results.csv | cut -d, -f1,8,9) $( [ -f runs/detect/$m/treino_ok ] && echo CONCLUIDO )"
done
ls resultados/deteccao/*_map_teste.json 2>/dev/null | xargs -r -n1 basename | tr '\n' ' '
[ -f resultados/deteccao/comparacao_detector_ls.txt ] && echo "| comparacao detector x extrator: PRONTA"
echo; echo "== filas:"
for f in $D/codex/*.txt $D/agy/*.txt; do
  b=${f%.txt}; e=espera
  for alvo in $(grep "^#ESPERA:" "$f" | sed 's/^#ESPERA:[[:space:]]*//' | tr -d '\r'); do [ -e "$alvo" ] || e="dep:$(basename "$alvo")"; done
  [ -f $b.rodando ] && e=RODANDO; [ -f $b.done ] && e=ok; [ -f $b.falhou ] && e=FALHOU
  printf "   %-14s %s\n" "$e" "$(basename $(dirname $f))/$(basename $f .txt)"
done
echo "== gemini: ordem teste $( [ -f resultados/pred_vlm_gemini_3_1_flash_lite.jsonl ] && echo "PRONTA ($(grep -c . resultados/pred_vlm_gemini_3_1_flash_lite.jsonl))" || echo "parcial $(grep -c . resultados/pred_vlm_gemini_3_1_flash_lite.jsonl.parcial 2>/dev/null)/89" ) | massa $(grep -c . data/diamond/massa1_gemini/anotacoes.jsonl 2>/dev/null)/383"
echo "== relatorios: $(ls -t resultados/*.md 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"
echo "== fila.log:"; tail -${1:-8} $D/fila.log 2>/dev/null | cut -c1-200
echo "== processos: $(powershell.exe -NoProfile -Command "\$b=@(Get-CimInstance Win32_Process -Filter \"Name='bash.exe'\" | %{ \$_.CommandLine }); \$p=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | %{ \$_.CommandLine }); 'gpu={0} treino={1} codex={2} agy={3} gemini={4} | RAM livre {5:N1} GB' -f @(\$b -match 'gpu\.sh|noite_detector_ls').Count, @(\$p -match 'detector_layout|ultralytics').Count, @(\$b -match 'fila\.sh codex').Count, @(\$b -match 'fila\.sh agy').Count, @(\$b -match 'gemini\.sh').Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" 2>/dev/null | tr -d '\r')"
