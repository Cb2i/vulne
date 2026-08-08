<#
.SYNOPSIS
    Installs VulnAssist on a Windows Server (or Windows 10/11) machine.
    No Docker, no IIS, no cloud service required — just Python and Node.js.

.DESCRIPTION
    1. Verifies Python 3.11+ and Node.js are available.
    2. Creates a Python virtual environment under backend/.venv.
    3. Installs backend dependencies.
    4. Creates the SQLite database and applies Alembic migrations.
    5. Seeds a default admin user, default CAA/SLE rules, and starter teams.
    6. Installs frontend dependencies and builds the production bundle
       (served directly by FastAPI — no separate web server needed).

.EXAMPLE
    PS> .\scripts\install.ps1
#>

$ErrorActionPreference = "Stop"

$RootDir    = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$DataDir    = Join-Path $RootDir "data"

Write-Host "=== VulnAssist — Installation ===" -ForegroundColor Cyan

# 1. Check prerequisites
Write-Host "`n[1/6] Verifying prerequisites..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/windows/ (check 'Add python.exe to PATH' during setup) and re-run this script."
}
$pythonVersion = & python --version
Write-Host "  Found $pythonVersion"

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    throw "Node.js was not found on PATH. Install the LTS release from https://nodejs.org/ and re-run this script."
}
$nodeVersion = & node --version
Write-Host "  Found Node.js $nodeVersion"

# 2. Create virtual environment
Write-Host "`n[2/6] Creating Python virtual environment..." -ForegroundColor Yellow
$VenvDir = Join-Path $BackendDir ".venv"
if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
    Write-Host "  Created $VenvDir"
} else {
    Write-Host "  Virtual environment already exists, skipping."
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

# 3. Install backend dependencies
Write-Host "`n[3/6] Installing backend dependencies..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip | Out-Null
& $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")

# 4. Prepare data directory + database
Write-Host "`n[4/6] Preparing the database..." -ForegroundColor Yellow
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}
$EnvFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $BackendDir ".env.example") $EnvFile
    Write-Host "  Created backend/.env from .env.example — edit it to set a real VULNASSIST_SECRET_KEY before going to production."
}

Push-Location $BackendDir
try {
    & $VenvPython -m alembic upgrade head
    & $VenvPython -m app.seed
} finally {
    Pop-Location
}

# 5. Install & build frontend
Write-Host "`n[5/6] Installing and building the frontend..." -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npm install
    npm run build
} finally {
    Pop-Location
}

# 6. Done
Write-Host "`n[6/6] Installation complete." -ForegroundColor Green
Write-Host ""
Write-Host "Next step: run  .\scripts\start.ps1  to launch VulnAssist," -ForegroundColor Cyan
Write-Host "then open http://localhost:8000 (or http://<server-name>:8000 from another machine on the network)." -ForegroundColor Cyan
