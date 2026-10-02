param(
    [Parameter(Mandatory = $true)]
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
$projectDirectory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$refreshScript = Join-Path $projectDirectory "refresh_data.py"
$logDirectory = Join-Path $projectDirectory "logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputLog = Join-Path $logDirectory "refresh_${timestamp}_output.log"
$errorLog = Join-Path $logDirectory "refresh_${timestamp}_error.log"

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

$outputHeader = @(
    "Scheduled refresh started: $((Get-Date).ToString('o'))"
    "Python: $PythonPath"
    "Project: $projectDirectory"
) -join [Environment]::NewLine
$standardOutput = ""
$standardError = ""

try {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $PythonPath
    $startInfo.Arguments = '"{0}"' -f $refreshScript
    $startInfo.WorkingDirectory = $projectDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "Windows could not start the refresh process."
    }

    $outputRead = $process.StandardOutput.ReadToEndAsync()
    $errorRead = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $standardOutput = $outputRead.Result
    $standardError = $errorRead.Result
    $refreshExitCode = $process.ExitCode
}
catch {
    $standardError = $_.Exception.ToString()
    $refreshExitCode = 1
}

$outputFooter = @(
    "Scheduled refresh ended: $((Get-Date).ToString('o'))"
    "Refresh process exit code: $refreshExitCode"
) -join [Environment]::NewLine
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)

[System.IO.File]::WriteAllText(
    $outputLog,
    $outputHeader + [Environment]::NewLine + $standardOutput + $outputFooter + [Environment]::NewLine,
    $utf8WithoutBom
)
[System.IO.File]::WriteAllText($errorLog, $standardError, $utf8WithoutBom)

exit $refreshExitCode
