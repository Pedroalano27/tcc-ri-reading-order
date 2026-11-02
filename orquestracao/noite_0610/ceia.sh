#!/bin/bash
# Leitura dos repositorios do CEIA-Datapolicy pelo Antigravity (so leitura), um relatorio por repositorio
# e uma sintese. Clones em /c/Users/pedro/dev/ceia_datapolicy (fora do projeto). Pedido do Pedro em 06/10.
P=/c/Users/pedro/dev/tcc-ri-reading-order; D=$P/orquestracao/noite_0610; C=/c/Users/pedro/dev/ceia_datapolicy
cd $C || exit 1
log(){ echo "$(date '+%d/%m %H:%M:%S') [ceia] $*" >> $D/log.txt; }
CTX="$(cat $D/ceia_contexto.txt)"
for r in Benchmark-LayoutAnalysis_xycut_pp Benchmark-LayoutAnalysis Benchmark official-diaries-analysis pipeline-amostras-anotacao synthetic-doc-gen official-diaries-collector; do
  [ -f $D/STOP ] && exit 0
  [ -s RELATO_$r.md ] && continue
  log "lendo $r"
  agy --model gemini-3.8-flash-high --mode accept-edits --print-timeout 1500s -p="$CTX

TAREFA: leia o repositorio na pasta ./$r (so essa pasta) e escreva o relatorio em ./RELATO_$r.md (na raiz desta pasta de trabalho, fora do repositorio)." < /dev/null > $D/ceia_$r.agy.log 2>&1
  log "$r: rc=$? relato=$( [ -s RELATO_$r.md ] && wc -c < RELATO_$r.md || echo AUSENTE )"
done
log "sintese"
agy --model gemini-3.8-flash-high --mode accept-edits --print-timeout 1500s -p="$CTX

TAREFA FINAL: leia os arquivos ./RELATO_*.md desta pasta (e volte ao codigo dos repositorios quando precisar conferir um detalhe) e escreva ./SINTESE.md com: (1) as 10 coisas mais aproveitaveis para o TCC, em ordem de retorno esperado, cada uma com o arquivo de origem, o que exatamente copiar ou adaptar e quanto trabalho da; (2) o que eles ja mediram que serve de comparacao; (3) o que nao vale a pena; (4) duvidas para perguntar a equipe." < /dev/null > $D/ceia_sintese.agy.log 2>&1
mkdir -p $P/resultados/ceia_datapolicy && cp RELATO_*.md SINTESE.md $P/resultados/ceia_datapolicy/ 2>/dev/null
log "fim (copiado para resultados/ceia_datapolicy)"; touch $D/ceia_fim
