$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$stateRoot = Join-Path $taskRoot 'state'
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
$taskLock = $null
try {
    $taskLock = [IO.File]::Open((Join-Path $stateRoot 'run.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
} catch [IO.IOException] {
    exit 0
}
try {
    $env:PYTHONUTF8 = '1'
    $runtimeConfig = Get-Content -LiteralPath (Join-Path $taskRoot 'runtime.json') -Raw | ConvertFrom-Json
    $env:Path = $runtimeConfig.ghDirectory + ';' + $env:Path
    & $runtimeConfig.python -u (Join-Path $taskRoot 'triage.py') --apply *> (Join-Path $stateRoot 'last-run.log')
    $taskExit = $LASTEXITCODE
    @{ at = (Get-Date).ToUniversalTime().ToString('o'); exitCode = $taskExit } |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateRoot 'run-status.json') -Encoding UTF8
    exit $taskExit
} finally {
    if ($taskLock) { $taskLock.Dispose() }
}
