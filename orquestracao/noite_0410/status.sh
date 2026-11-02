#!/bin/bash
# Estado compacto da noite de 04/10 (para o orquestrador ler gastando pouco). So le, nao muda nada.
cd "$(dirname "$0")/../.." || exit 1
D=orquestracao/noite_0410
echo "== $(date '+%d/%m %H:%M') | GPU $(nvidia-smi --query-gpu=memory.used,utilization.gpu,temperature.gpu --format=csv,noheader 2>/dev/null)"
echo "== filas:"
for f in $D/codex/*.txt $D/agy/*.txt; do
  [ -e "$f" ] || continue
  b=${f%.txt}; e=espera
  for alvo in $(grep "^#ESPERA:" "$f" | sed 's/^#ESPERA:[[:space:]]*//' | tr -d '\r'); do [ -e "$alvo" ] || e="dep:$(basename "$alvo")"; done
  [ -f $b.rodando ] && e=RODANDO; [ -f $b.done ] && e=ok; [ -f $b.falhou ] && e=FALHOU
  printf "   %-14s %s\n" "$e" "$(basename $(dirname $f))/$(basename $f .txt)"
done
for f in $D/gpu/[0-9]*.sh; do
  [ -e "$f" ] || continue
  b=${f%.sh}; e=espera; [ -f $b.rodando ] && e=RODANDO; [ -f $b.done ] && e=ok; [ -f $b.falhou ] && e=FALHOU
  printf "   %-14s gpu/%s\n" "$e" "$(basename $b)"
done
echo "== relatorios novos: $(find resultados -maxdepth 1 -name '*.md' -newer $D/comum.txt 2>/dev/null | xargs -r -n1 basename | tr '\n' ' ')"
echo "== fila.log:"; tail -${1:-8} $D/fila.log 2>/dev/null | cut -c1-200
echo "== processos: $(powershell.exe -NoProfile -Command "\$b=@(Get-CimInstance Win32_Process -Filter \"Name='bash.exe'\" | %{ \$_.CommandLine }); \$m=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory; 'codex={0} agy={1} gpu={2} | RAM livre {3:N1} GB | commit {4:N0}%' -f @(\$b -match 'noite_0410/fila\.sh codex').Count, @(\$b -match 'noite_0410/fila\.sh agy').Count, @(\$b -match 'noite_0410/gpu\.sh').Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB), (100*\$m.CommittedBytes/\$m.CommitLimit)" 2>/dev/null | tr -d '\r')"
