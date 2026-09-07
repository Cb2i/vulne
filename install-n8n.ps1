<#
.SYNOPSIS
  Installe et lance n8n via Docker sur ce poste Windows.
.DESCRIPTION
  - Verifie Docker (et tente de l'installer via winget si absent)
  - Cree le dossier d'installation
  - Genere docker-compose.yml et .env (avec mot de passe aleatoire) si absents
  - Verifie les prerequis (daemon actif, port libre)
  - Lance n8n, attend qu'il reponde, ouvre le navigateur
.PARAMETER InstallDir
  Dossier d'installation (defaut: $HOME\n8n)
.PARAMETER Port
  Port d'ecoute local (defaut: 5678)
.PARAMETER AuthUser
  Identifiant de connexion n8n (defaut: admin)
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install-n8n.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install-n8n.ps1 -InstallDir D:\n8n -Port 5680
#>

param(
    [string]$InstallDir = "$HOME\n8n",
    [int]$Port = 5678,
    [string]$AuthUser = "admin"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    ATTENTION: $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "    ERREUR: $msg" -ForegroundColor Red }

function New-RandomPassword {
    param([int]$Length = 20)
    $chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
    -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

# 1. Docker CLI present ?
Write-Step "Verification de Docker"
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Warn "Docker n'est pas installe sur ce poste."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "    Tentative d'installation via winget (necessite les droits administrateur)..."
        try {
            winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
            Write-Ok "Docker Desktop installe."
            Write-Warn "Redemarrez votre session Windows (ou la machine), demarrez Docker Desktop, puis relancez ce script."
        } catch {
            Write-Err "Echec de l'installation automatique : $($_.Exception.Message)"
            Write-Host "    Installez manuellement : https://www.docker.com/products/docker-desktop/"
        }
    } else {
        Write-Err "winget indisponible sur ce poste."
        Write-Host "    Installez Docker Desktop manuellement : https://www.docker.com/products/docker-desktop/"
    }
    exit 1
}
Write-Ok "Docker CLI present."

# 2. Daemon Docker demarre ?
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Err "Docker Desktop n'est pas demarre."
    Write-Host "    Ouvrez l'application Docker Desktop, attendez qu'elle soit prete, puis relancez ce script."
    exit 1
}
Write-Ok "Docker Desktop est demarre."

# 3. Plugin Compose present ?
docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Err "Le plugin 'docker compose' est introuvable. Mettez a jour Docker Desktop."
    exit 1
}
Write-Ok "Plugin Docker Compose present."

# 4. Port libre ?
$conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($conn) {
    Write-Err "Le port $Port est deja utilise sur ce poste."
    Write-Host "    Relancez avec -Port <autre_numero>, ou liberez le port $Port."
    exit 1
}
Write-Ok "Port $Port libre."

# 5. Dossier d'installation
Write-Step "Preparation du dossier d'installation ($InstallDir)"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}
Set-Location $InstallDir
Write-Ok "Dossier pret."

# 6. Identifiants (.env)
if (-not (Test-Path ".env")) {
    Write-Step "Generation des identifiants"
    $password = New-RandomPassword
    @"
N8N_BASIC_AUTH_USER=$AuthUser
N8N_BASIC_AUTH_PASSWORD=$password
N8N_HOST=localhost
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:$Port/
GENERIC_TIMEZONE=UTC
"@ | Out-File -Encoding utf8 .env
    Write-Ok "Fichier .env cree avec un mot de passe genere aleatoirement."
} else {
    Write-Warn ".env existe deja dans ce dossier, il n'est pas modifie."
}

# 7. docker-compose.yml
Write-Step "Ecriture de docker-compose.yml"
@"
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "${Port}:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=`${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=`${N8N_BASIC_AUTH_PASSWORD}
      - N8N_HOST=`${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=`${N8N_PROTOCOL:-http}
      - NODE_ENV=production
      - WEBHOOK_URL=`${WEBHOOK_URL:-http://localhost:$Port/}
      - GENERIC_TIMEZONE=`${GENERIC_TIMEZONE:-UTC}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
"@ | Out-File -Encoding utf8 docker-compose.yml
Write-Ok "docker-compose.yml ecrit."

# 8. Lancement
Write-Step "Lancement de n8n"
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Err "Echec du lancement. Consultez les logs avec : docker compose logs n8n"
    exit 1
}

# 9. Attente que le service reponde (jusqu'a 60s)
Write-Step "Attente du demarrage du service"
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$Port/" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode) { $ready = $true; break }
    } catch {
        if ($_.Exception.Response) { $ready = $true; break }
    }
}

if ($ready) {
    Write-Ok "n8n repond sur http://localhost:$Port"
} else {
    Write-Warn "n8n ne repond pas encore apres 60s. Verifiez : docker compose logs -f n8n"
}

# 10. Resume
Write-Step "Termine"
Write-Host ""
Write-Host "  URL       : http://localhost:$Port" -ForegroundColor White
Get-Content ".env" | Where-Object { $_ -match "N8N_BASIC_AUTH" } | ForEach-Object {
    Write-Host "  $_" -ForegroundColor White
}
Write-Host ""
Write-Host "  Dossier   : $InstallDir" -ForegroundColor Gray
Write-Host "  Arreter   : docker compose down   (depuis ce dossier)" -ForegroundColor Gray
Write-Host "  Logs      : docker compose logs -f n8n" -ForegroundColor Gray
Write-Host ""

Start-Process "http://localhost:$Port"
