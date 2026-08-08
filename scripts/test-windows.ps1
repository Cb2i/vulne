<#
.SYNOPSIS
    One-shot script to pull the latest code, install, and launch VulnAssist for
    manual testing on Windows. Combines install.ps1 + start.ps1 into a single run.

.EXAMPLE
    From an already-open PowerShell prompt, inside the repo folder:
    PS> powershell -ExecutionPolicy Bypass -File .\scripts\test-windows.ps1
#>

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot

# Keep the window open on any failure so the error is actually readable,
# instead of the window flashing shut (the classic double-click symptom).
trap {
    Write-Host ""
    Write-Host "TEST RUN FAILED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to close this window"
    exit 1
}

Write-Host "=== VulnAssist - Quick test launch ===" -ForegroundColor Cyan

# 1. Pull the latest code, if this is a git checkout.
if (Test-Path (Join-Path $RootDir ".git")) {
    Write-Host "`n[1/3] Pulling latest changes..." -ForegroundColor Yellow
    Push-Location $RootDir
    try {
        git pull
    } finally {
        Pop-Location
    }
} else {
    Write-Host "`n[1/3] Not a git checkout, skipping 'git pull'." -ForegroundColor DarkGray
}

# 2. Install (safe to re-run: every step is idempotent).
Write-Host "`n[2/3] Installing / updating dependencies..." -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "install.ps1") -NoPause

# 3. Start the server.
Write-Host "`n[3/3] Starting VulnAssist..." -ForegroundColor Yellow
Write-Host "Once you see 'Application startup complete', open http://localhost:8000 in your browser." -ForegroundColor Cyan
Write-Host "Login: admin@vulnassist.internal / ChangeMe123!" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

& (Join-Path $PSScriptRoot "start.ps1")
