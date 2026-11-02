# Sobe (ou retoma depois de uma queda) as filas da noite de 04/10, sem duplicar o que ja esta rodando.
# Uso, da raiz do projeto:  powershell -NoProfile -ExecutionPolicy Bypass -File orquestracao\noite_0410\iniciar.ps1
# ou, no Git Bash:          bash orquestracao/noite_0410/iniciar.sh
# Para parar: criar orquestracao\noite_0410\STOP e matar as arvores (taskkill /T) -- ver status.sh.
$r = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$rbash = '/' + $r.Substring(0, 1).ToLower() + $r.Substring(2).Replace('\', '/')
$bash = 'C:\Program Files\Git\usr\bin\bash.exe'
$d = 'orquestracao/noite_0410'
if (Test-Path "$r\orquestracao\noite_0410\STOP") { Remove-Item "$r\orquestracao\noite_0410\STOP"; 'removi o STOP antigo' }
$vivos = @(Get-CimInstance Win32_Process -Filter "Name='bash.exe'" | ForEach-Object { $_.CommandLine })

function Subir($nome, $padrao, $cmd) {
    if ($vivos | Where-Object { $_ -match $padrao }) { "ja rodando: $nome"; return }
    $linha = '"cd ' + $rbash + ' && ' + $cmd + ' >> ' + $d + '/saida_' + $nome + '.log 2>&1"'
    Start-Process -FilePath $bash -ArgumentList '-lc', $linha -WindowStyle Hidden
    "iniciado:   $nome"
}

Subir 'codex' 'noite_0410/fila\.sh codex' "bash $d/fila.sh codex"
Subir 'agy'   'noite_0410/fila\.sh agy'   "bash $d/fila.sh agy"
Subir 'gpu'   'noite_0410/gpu\.sh'        "bash $d/gpu.sh"
