<#
.SYNOPSIS
  Verifie que l'environnement est pret pour lancer n8n via Docker Compose.
.USAGE
  cd vers le dossier contenant docker-compose.yml, puis :
  powershell -ExecutionPolicy Bypass -File .\check-n8n.ps1
#>

$ErrorActionPreference = "SilentlyContinue"
$issues = @()
$ok = @()

function Test-Item {
    param([string]$Label, [scriptblock]$Check)
    Write-Host -NoNewline "  - $Label ... "
    try {
        $result = & $Check
        if ($result -eq $true) {
            Write-Host "OK" -ForegroundColor Green
            $script:ok += $Label
            return $true
        } else {
            Write-Host "ECHEC" -ForegroundColor Red
            $script:issues += $Label
            return $false
        }
    } catch {
        Write-Host "ECHEC ($($_.Exception.Message))" -ForegroundColor Red
        $script:issues += $Label
        return $false
    }
}

Write-Host "`n=== Verification de l'environnement n8n ===`n" -ForegroundColor Cyan

# 1. Docker CLI installe
$null = Test-Item "Docker CLI installe" {
    $null = Get-Command docker -ErrorAction Stop
    $true
}

# 2. Docker daemon demarre
$dockerRunning = Test-Item "Docker Desktop demarre (daemon accessible)" {
    docker info *> $null
    $LASTEXITCODE -eq 0
}

# 3. Plugin Docker Compose disponible
$null = Test-Item "Plugin Docker Compose disponible" {
    docker compose version *> $null
    $LASTEXITCODE -eq 0
}

# 4. docker-compose.yml present dans le dossier courant
$composeFile = Join-Path (Get-Location) "docker-compose.yml"
$composeExists = Test-Item "docker-compose.yml present dans le dossier courant" {
    Test-Path $composeFile
}

# 5. Fichier compose syntaxiquement valide (seulement si docker tourne + fichier present)
if ($dockerRunning -and $composeExists) {
    $null = Test-Item "docker-compose.yml valide (docker compose config)" {
        docker compose config *> $null
        $LASTEXITCODE -eq 0
    }
}

# 6. Fichier .env present
$envExists = Test-Item ".env present (identifiants configures)" {
    Test-Path (Join-Path (Get-Location) ".env")
}
if (-not $envExists) {
    Write-Host "    -> Copiez .env.example vers .env et definissez vos identifiants." -ForegroundColor Yellow
}

# 7. Port 5678 libre
$null = Test-Item "Port 5678 libre" {
    $conn = Get-NetTCPConnection -LocalPort 5678 -ErrorAction SilentlyContinue
    -not $conn
}

# 8. Container n8n deja present (info, pas bloquant)
$existingContainer = docker ps -a --filter "name=^n8n$" --format "{{.Names}}" 2>$null
if ($existingContainer -eq "n8n") {
    $status = docker ps -a --filter "name=^n8n$" --format "{{.Status}}" 2>$null
    Write-Host "  - Container 'n8n' existant : $status" -ForegroundColor Yellow
}

Write-Host "`n=== Resume ===" -ForegroundColor Cyan
Write-Host "OK    : $($ok.Count)" -ForegroundColor Green
Write-Host "ECHEC : $($issues.Count)" -ForegroundColor $(if ($issues.Count -gt 0) { "Red" } else { "Green" })

if ($issues.Count -eq 0) {
    Write-Host "`nTout est pret. Vous pouvez lancer : docker compose up -d`n" -ForegroundColor Green
} else {
    Write-Host "`nA corriger avant de lancer n8n :" -ForegroundColor Red
    foreach ($i in $issues) { Write-Host "  - $i" -ForegroundColor Red }
    Write-Host ""
    exit 1
}
