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

# If this script was launched by double-clicking (not from an already-open
# PowerShell prompt), the window closes instantly on error and the message
# is never seen. Catch everything and pause before exiting so it stays open.
trap {
    Write-Host ""
    Write-Host "VULNASSIST FAILED TO START:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to close this window"
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run .\scripts\install.ps1 first."
}

$FrontendDist = Join-Path $RootDir "frontend\dist"
if (-not (Test-Path $FrontendDist)) {
    Write-Warning "frontend/dist not found - the compiled UI won't be served. Run 'npm run build' in frontend/, or re-run install.ps1."
}

# Closing this window without Ctrl+C first can leave a previous VulnAssist process
# running in the background, still bound to the port -- the next start then fails
# with a cryptic Windows socket error, while your browser keeps silently talking to
# the OLD (stale) process the whole time. Detect and clear that specific case, but
# only kill a process that's clearly a previous run of this app's own Python, never
# an unrelated process that just happens to be using the port.
$existingConnections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existingConnections) {
    $ownPids = New-Object System.Collections.Generic.List[int]
    $otherPids = New-Object System.Collections.Generic.List[string]
    foreach ($conn in $existingConnections) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $procPath = $null
        if ($null -ne $proc) {
            try { $procPath = $proc.Path } catch { $procPath = $null }
        }
        if ($null -ne $proc -and $procPath -eq $VenvPython) {
            $ownPids.Add($conn.OwningProcess)
        } elseif ($null -ne $proc) {
            $otherPids.Add("$($proc.ProcessName) (PID $($conn.OwningProcess))")
        }
    }
    if ($ownPids.Count -gt 0) {
        Write-Host "Port $Port is held by a previous VulnAssist process that wasn't fully closed -- stopping it..." -ForegroundColor Yellow
        $ownPids | Select-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 1
    }
    if ($otherPids.Count -gt 0) {
        throw (
            "Port $Port is already in use by another program: $($otherPids -join ', '). " +
            "This isn't a VulnAssist process, so it wasn't stopped automatically. " +
            "Close that program, or run '.\scripts\start.ps1 -Port 8080' to use a different port."
        )
    }
}

Write-Host "Starting VulnAssist on http://${BindAddress}:${Port} ..." -ForegroundColor Cyan
Write-Host "Once you see 'Application startup complete' below, open http://localhost:$Port in your browser." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray

Push-Location $BackendDir
try {
    & $VenvPython -m uvicorn app.main:app --host $BindAddress --port $Port
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

Write-Host ""
if ($ExitCode -ne 0) {
    Write-Host "VulnAssist exited with an error (see above)." -ForegroundColor Red
} else {
    Write-Host "VulnAssist stopped." -ForegroundColor DarkGray
}
Read-Host "Press Enter to close this window"
