# Sobe (ou retoma depois de uma queda) tudo o que a noite precisa, sem duplicar o que ja esta rodando.
# Uso, da raiz do projeto:
#   powershell -NoProfile -ExecutionPolicy Bypass -File orquestracao\noite_0210\iniciar.ps1
# ou, no Git Bash:  bash orquestracao/noite_0210/iniciar.sh
# Tudo e retomavel: treino continua da ultima epoca, filas pulam o que tem .done, Gemini usa --retomar.
# Para parar: criar orquestracao\noite_0210\STOP e matar as arvores (taskkill /T) -- ver status.sh.
$r = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$rbash = '/' + $r.Substring(0, 1).ToLower() + $r.Substring(2).Replace('\', '/')
$bash = 'C:\Program Files\Git\usr\bin\bash.exe'
$d = 'orquestracao/noite_0210'
if (Test-Path "$r\orquestracao\noite_0210\STOP") { Remove-Item "$r\orquestracao\noite_0210\STOP"; 'removi o STOP antigo' }
$vivos = @(Get-CimInstance Win32_Process -Filter "Name='bash.exe'" | ForEach-Object { $_.CommandLine })

function Subir($nome, $padrao, $cmd) {
    if ($vivos | Where-Object { $_ -match $padrao }) { "ja rodando: $nome"; return }
    $linha = '"cd ' + $rbash + ' && ' + $cmd + ' >> ' + $d + '/saida_' + $nome + '.log 2>&1"'
    Start-Process -FilePath $bash -ArgumentList '-lc', $linha -WindowStyle Hidden
    "iniciado:   $nome"
}

Subir 'gpu'    'noite_0210/gpu\.sh|noite_detector_ls\.sh' "bash $d/gpu.sh"
# segunda parte da GPU (ajuste fino no Diamond); so entra depois que o roteiro dos detectores terminou
if (Test-Path "$r\resultados\deteccao\comparacao_detector_ls.txt") { Subir 'gpu2' 'noite_0210/gpu2\.sh' "bash $d/gpu2.sh" }
Subir 'codex'  'fila\.sh codex'                           "bash $d/fila.sh codex"
Subir 'agy'    'fila\.sh agy'                             "bash $d/fila.sh agy"
# o Gemini terminou em 03/10 04:54 (89 paginas de teste ordenadas; massa em 345/383, o resto falha sempre
# na validacao). Para rodar de novo, apague o marcador gemini_feito.
if (Test-Path "$r\orquestracao\noite_0210\gemini_feito") { 'encerrado:  gemini (marcador gemini_feito)' }
else { Subir 'gemini' 'noite_0210/gemini\.sh' "bash $d/gemini.sh" }
