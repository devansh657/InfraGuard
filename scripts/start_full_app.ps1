param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$PidFile = Join-Path $RuntimeDir "backend.pid"
$HealthUrl = "http://127.0.0.1:$BackendPort/health"
$FrontendOrigin = "http://127.0.0.1:$FrontendPort"

function Test-BackendHealthy {
    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
        return $response.status -eq "healthy"
    }
    catch {
        return $false
    }
}

function Test-BackendCorsReady {
    try {
        $response = Invoke-WebRequest `
            -Uri $HealthUrl `
            -Method Options `
            -Headers @{
                "Origin" = $FrontendOrigin
                "Access-Control-Request-Method" = "GET"
            } `
            -TimeoutSec 2

        return $response.Headers["Access-Control-Allow-Origin"] -eq $FrontendOrigin
    }
    catch {
        return $false
    }
}

function Test-BackendAppReady {
    try {
        $eda = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/eda" -TimeoutSec 2
        $benchmark = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/benchmark-report" -TimeoutSec 2
        $live = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/live/status" -TimeoutSec 2
        $asset = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/eda-assets/model_comparison.png" -UseBasicParsing -TimeoutSec 2
        return ($eda.available -eq $true) -and ($benchmark.available -eq $true) -and ($live.mode -eq "sequential_dataset_replay") -and ($asset.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Get-BackendProcessId {
    $connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($connection) {
        return [int]$connection.OwningProcess
    }
    return $null
}

function Stop-ExistingBackend {
    $stopped = $false
    if (Test-Path $PidFile) {
        $pidFromFile = Get-Content -LiteralPath $PidFile | Select-Object -First 1
        if ($pidFromFile) {
            $process = Get-Process -Id $pidFromFile -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $pidFromFile -Force
                $stopped = $true
            }
        }
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    }

    $pidFromPort = Get-BackendProcessId
    if ($pidFromPort) {
        Stop-Process -Id $pidFromPort -Force
        $stopped = $true
    }

    if ($stopped) {
        Start-Sleep -Seconds 2
    }
}

function Start-Backend {
    Write-Host "Starting InfraGuard backend on port $BackendPort..." -ForegroundColor Cyan
    $backend = Start-Process `
        -WindowStyle Hidden `
        -FilePath $Python `
        -ArgumentList @("-m", "backend.run_server", "--port", "$BackendPort", "--strict-port") `
        -WorkingDirectory $ProjectRoot `
        -PassThru

    Set-Content -LiteralPath $PidFile -Value $backend.Id

    $healthy = $false
    for ($attempt = 1; $attempt -le 25; $attempt++) {
        Start-Sleep -Seconds 1
        if ((Test-BackendHealthy) -and (Test-BackendCorsReady) -and (Test-BackendAppReady)) {
            $healthy = $true
            break
        }
    }

    if (-not $healthy) {
        Write-Host "Backend did not become healthy with CORS enabled at $HealthUrl" -ForegroundColor Red
        Write-Host "Run .venv\Scripts\python.exe -m backend.run_server to inspect logs." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Backend healthy at $HealthUrl" -ForegroundColor Green
}

if (-not (Test-Path $Python)) {
    Write-Host "Missing Python environment: $Python" -ForegroundColor Red
    Write-Host "Create/install the environment first, then rerun this script." -ForegroundColor Yellow
    exit 1
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if ((Test-BackendHealthy) -and (Test-BackendCorsReady) -and (Test-BackendAppReady)) {
    Write-Host "Backend already healthy at $HealthUrl" -ForegroundColor Green
}
else {
    if (Test-BackendHealthy) {
        Write-Host "Backend is running but needs restart to load current routes/assets/settings..." -ForegroundColor Yellow
        Stop-ExistingBackend
    }
    Start-Backend
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "Opening InfraGuard AI frontend..." -ForegroundColor Green
Write-Host "Frontend URL: http://localhost:$FrontendPort" -ForegroundColor Cyan
Write-Host "API docs:     http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the frontend dev server." -ForegroundColor Yellow
Write-Host "To stop the hidden backend later, run: .\scripts\stop_backend.ps1" -ForegroundColor Yellow

Push-Location $FrontendDir
npm run dev -- --host 127.0.0.1 --port $FrontendPort
Pop-Location
