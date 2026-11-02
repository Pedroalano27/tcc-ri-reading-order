# Sobe (ou retoma depois de uma queda) as filas da fase de novembro, sem duplicar o que ja esta rodando.
# Uso, da raiz do projeto:  powershell -NoProfile -ExecutionPolicy Bypass -File orquestracao\fase_nov\iniciar.ps1
# ou, no Git Bash:          bash orquestracao/fase_nov/iniciar.sh
# Para parar: criar orquestracao\fase_nov\STOP e matar as arvores (taskkill /T) -- ver status.sh.
$r = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$rbash = '/' + $r.Substring(0, 1).ToLower() + $r.Substring(2).Replace('\', '/')
$bash = 'C:\Program Files\Git\usr\bin\bash.exe'
$d = 'orquestracao/fase_nov'
if (Test-Path "$r\orquestracao\fase_nov\STOP") { Remove-Item "$r\orquestracao\fase_nov\STOP"; 'removi o STOP antigo' }
$vivos = @(Get-CimInstance Win32_Process -Filter "Name='bash.exe'" | ForEach-Object { $_.CommandLine })

function Subir($nome, $padrao, $cmd) {
    if ($vivos | Where-Object { $_ -match $padrao }) { "ja rodando: $nome"; return }
    $linha = '"cd ' + $rbash + ' && ' + $cmd + ' >> ' + $d + '/saida_' + $nome + '.log 2>&1"'
    Start-Process -FilePath $bash -ArgumentList '-lc', $linha -WindowStyle Hidden
    "iniciado:   $nome"
}

Subir 'codex' 'fase_nov/fila\.sh codex' "DURACAO_S=86400 bash $d/fila.sh codex"
Subir 'agy'   'fase_nov/fila\.sh agy'   "DURACAO_S=86400 bash $d/fila.sh agy"
Subir 'cmd'   'fase_nov/fila\.sh cmd'   "DURACAO_S=86400 bash $d/fila.sh cmd"
