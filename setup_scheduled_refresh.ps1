param(
    [ValidatePattern("^(?:[01]\d|2[0-3]):[0-5]\d$")]
    [string]$DailyTime = "09:00",

    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$taskName = "FlowBridge Daily Refresh"
$projectDirectory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$runnerScript = Join-Path $projectDirectory "run_scheduled_refresh.ps1"

if (-not $PythonPath) {
    $PythonPath = Join-Path $projectDirectory ".venv\Scripts\python.exe"
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python was not found at '$PythonPath'. Create the project virtual environment and install requirements first."
}
if (-not (Test-Path -LiteralPath $runnerScript -PathType Leaf)) {
    throw "Scheduled refresh runner was not found at '$runnerScript'."
}

$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
& $PythonPath -c "import pandas, openpyxl, sqlite3"
if ($LASTEXITCODE -ne 0) {
    throw "Python dependency verification failed. Run: python -m pip install -r requirements.txt"
}

$windowsPowerShellPath = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
if (Test-Path -LiteralPath $windowsPowerShellPath -PathType Leaf) {
    $powerShellPath = (Resolve-Path -LiteralPath $windowsPowerShellPath).Path
}
else {
    $powerShellPath = (Get-Process -Id $PID).Path
}
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$scheduleTime = [datetime]::ParseExact(
    $DailyTime,
    "HH:mm",
    [System.Globalization.CultureInfo]::InvariantCulture
)

$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    $existingActions = @($existingTask.Actions)
    $belongsToProject = $existingActions.Count -eq 1 -and @(
        $existingActions | Where-Object {
            $_.WorkingDirectory -eq $projectDirectory -and
            $_.Arguments -like "*$runnerScript*"
        }
    ).Count -gt 0

    if (-not $belongsToProject) {
        throw "A task named '$taskName' already exists but does not belong to '$projectDirectory'. It was not changed."
    }

    Write-Host "Updating the existing FlowBridge task for this project."
}

$actionArguments = (
    '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass ' +
    '-File "{0}" -PythonPath "{1}"' -f $runnerScript, $PythonPath
)
$action = New-ScheduledTaskAction `
    -Execute $powerShellPath `
    -Argument $actionArguments `
    -WorkingDirectory $projectDirectory
$trigger = New-ScheduledTaskTrigger -Daily -At $scheduleTime
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "FlowBridge daily refresh for $projectDirectory" `
    -Force | Out-Null

$registeredTask = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "Task registered successfully."
Write-Host "Task name: $($registeredTask.TaskName)"
Write-Host "User: $currentUser"
Write-Host "Daily time: $DailyTime"
Write-Host "Next run: $($taskInfo.NextRunTime)"
Write-Host "Python: $PythonPath"
Write-Host "Working directory: $projectDirectory"
