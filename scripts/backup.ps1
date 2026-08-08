<#
.SYNOPSIS
    Backs up the VulnAssist SQLite database to a timestamped file.
    (If you have migrated to PostgreSQL, use pg_dump instead - this script only
    covers the default SQLite setup.)

.EXAMPLE
    PS> .\scripts\backup.ps1
    PS> .\scripts\backup.ps1 -Destination D:\Backups\VulnAssist
#>

param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$DbPath  = Join-Path $RootDir "data\vulnassist.db"

if (-not (Test-Path $DbPath)) {
    throw "No SQLite database found at $DbPath. Nothing to back up (or you are using PostgreSQL)."
}

if (-not $Destination) {
    $Destination = Join-Path $RootDir "data\backups"
}
if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $Destination "vulnassist_$Timestamp.db"

Copy-Item $DbPath $BackupFile
Write-Host "Backup created: $BackupFile" -ForegroundColor Green
