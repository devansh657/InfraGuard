$BackendPort = 8000
$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$PidFile = Join-Path $RuntimeDir "backend.pid"

function Stop-ByPid {
    param([int]$ProcessId)
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        Stop-Process -Id $ProcessId -Force
        Write-Host "Stopped InfraGuard backend process $ProcessId." -ForegroundColor Green
        return $true
    }
    return $false
}

$stopped = $false

if (Test-Path $PidFile) {
    $BackendPid = Get-Content -LiteralPath $PidFile | Select-Object -First 1
    if ($BackendPid) {
        $stopped = Stop-ByPid -ProcessId ([int]$BackendPid)
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

$connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($connection) {
    $stopped = (Stop-ByPid -ProcessId ([int]$connection.OwningProcess)) -or $stopped
}

if (-not $stopped) {
    Write-Host "No InfraGuard backend process found on port $BackendPort." -ForegroundColor Yellow
}
