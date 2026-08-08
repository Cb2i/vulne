<#
.SYNOPSIS
    Starts the VulnAssist web application (single process: API + built frontend).

.PARAMETER Port
    TCP port to listen on. Defaults to 8000.

.PARAMETER BindAddress
    Network interface to bind to. Defaults to 0.0.0.0 (all interfaces on the internal network).

.EXAMPLE
    PS> .\scripts\start.ps1
    PS> .\scripts\start.ps1 -Port 8080
#>

param(
    [int]$Port = 8000,
    [string]$BindAddress = "0.0.0.0"
)

$ErrorActionPreference = "Stop"

$RootDir    = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run .\scripts\install.ps1 first."
}

$FrontendDist = Join-Path $RootDir "frontend\dist"
if (-not (Test-Path $FrontendDist)) {
    Write-Warning "frontend/dist not found — the compiled UI won't be served. Run 'npm run build' in frontend/, or re-run install.ps1."
}

Write-Host "Starting VulnAssist on http://${BindAddress}:${Port} ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray

Push-Location $BackendDir
try {
    & $VenvPython -m uvicorn app.main:app --host $BindAddress --port $Port
} finally {
    Pop-Location
}
