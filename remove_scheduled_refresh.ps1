$ErrorActionPreference = "Stop"
$taskName = "FlowBridge Daily Refresh"
$projectDirectory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$runnerScript = Join-Path $projectDirectory "run_scheduled_refresh.ps1"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if (-not $existingTask) {
    Write-Host "Task '$taskName' is not registered. Nothing was removed."
    exit 0
}

$existingActions = @($existingTask.Actions)
$belongsToProject = $existingActions.Count -eq 1 -and @(
    $existingActions | Where-Object {
        $_.WorkingDirectory -eq $projectDirectory -and
        $_.Arguments -like "*$runnerScript*"
    }
).Count -gt 0

if (-not $belongsToProject) {
    throw "Task '$taskName' does not belong to '$projectDirectory'. It was not removed."
}

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Host "Removed task '$taskName' for this FlowBridge project."
