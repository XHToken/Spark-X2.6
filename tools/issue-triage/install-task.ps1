$ErrorActionPreference = 'Stop'
$taskName = 'Spark-X2.6 Issue Triage'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task already exists; inspect it before updating.'
}
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$ghPath = (Get-Command gh -ErrorAction Stop).Source
@{ python = $pythonPath; ghDirectory = (Split-Path $ghPath) } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.json') -Encoding UTF8
$runnerPath = Join-Path $PSScriptRoot 'run.ps1'
$arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $runnerPath + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $PSScriptRoot
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 30)
$login = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 25) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($repeat, $login) -Principal $principal -Settings $settings -Description 'Classify Spark-X2.6 issues and sync its project using the locally authenticated gh account; every 30 minutes while logged in.'
