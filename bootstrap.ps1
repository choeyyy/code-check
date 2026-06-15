# code-check bootstrap (PowerShell)
# Downloads only the setup skill so user can run /check-setup in Cursor.
# Usage: irm https://raw.githubusercontent.com/choeyyy/code-check/main/bootstrap.ps1 | iex

$ErrorActionPreference = "Stop"

$skillDir = Join-Path $env:USERPROFILE ".cursor\skills\check-setup"
$skillFile = Join-Path $skillDir "SKILL.md"
$rawUrl = "https://raw.githubusercontent.com/choeyyy/code-check/main/setup/SKILL.md"

if (-not (Test-Path (Join-Path $env:USERPROFILE ".cursor"))) {
    Write-Host "[ERROR] Cursor directory not found. Please install Cursor first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] git is required. Please install git first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $skillDir)) {
    New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
}

try {
    Invoke-WebRequest -Uri $rawUrl -OutFile $skillFile -UseBasicParsing
    Write-Host ""
    Write-Host "[ok] check-setup skill installed." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next: open Cursor, type /check-setup to install the full plugin." -ForegroundColor Yellow
    Write-Host ""
} catch {
    Write-Host "[ERROR] Failed to download setup skill: $_" -ForegroundColor Red
    exit 1
}
