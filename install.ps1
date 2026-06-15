# code-check install script (PowerShell)
# Usage: open PowerShell, cd to code-check directory, run: .\install.ps1

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$PLUGIN_DIR = $PSScriptRoot
if (-not $PLUGIN_DIR) { $PLUGIN_DIR = (Get-Location).Path }

$pluginJson = Join-Path $PLUGIN_DIR ".cursor-plugin\plugin.json"
if (-not (Test-Path $pluginJson)) {
    Write-Host "[ERROR] .cursor-plugin/plugin.json not found." -ForegroundColor Red
    Write-Host "Please run this script from the code-check plugin directory." -ForegroundColor Red
    exit 1
}

$SKILLS_DIR = Join-Path $env:USERPROFILE ".cursor\skills"

$SKILL_NAMES = @(
    @{ name = "check";            desc = "Quick code review -- 3 parallel reviewers, consensus confidence, session tracking." },
    @{ name = "check-git";        desc = "Quick git branch review -- 3 parallel reviewers scoped to branch diff." },
    @{ name = "check-full";       desc = "Thorough code review -- 5 parallel reviewers, 0-100 confidence scoring, threshold filtering." },
    @{ name = "check-full-git";   desc = "Thorough git branch review -- 5 parallel reviewers, confidence scoring, threshold filtering." },
    @{ name = "check-rules";      desc = "Spec-alignment check -- verify code matches rule documents using dual-direction reviewers." },
    @{ name = "check-session";    desc = "View review session status or archive and restart." },
    @{ name = "check-summarize";  desc = "Analyze review history to extract bug patterns, hotspots, and recommended rules." }
)

if ($Uninstall) {
    Write-Host "`n=== Uninstalling code-check ===" -ForegroundColor Yellow
    foreach ($skill in $SKILL_NAMES) {
        $dir = Join-Path $SKILLS_DIR $skill.name
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Host "  Removed: $dir" -ForegroundColor Gray
        }
    }
    Write-Host "`nUninstall complete. Restart Cursor to take effect." -ForegroundColor Green
    exit 0
}

Write-Host "`n=== Installing code-check ===" -ForegroundColor Cyan
Write-Host "Plugin directory: $PLUGIN_DIR" -ForegroundColor Gray
Write-Host "Skills directory: $SKILLS_DIR" -ForegroundColor Gray

if (-not (Test-Path $SKILLS_DIR)) {
    New-Item -ItemType Directory -Path $SKILLS_DIR -Force | Out-Null
    Write-Host "  Created: $SKILLS_DIR" -ForegroundColor Gray
}

$created = 0
$skipped = 0

foreach ($skill in $SKILL_NAMES) {
    $skillDir = Join-Path $SKILLS_DIR $skill.name
    $skillFile = Join-Path $skillDir "SKILL.md"

    if (-not (Test-Path $skillDir)) {
        New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
    }

    if (Test-Path $skillFile) {
        $existing = Get-Content $skillFile -Raw
        if ($existing -match [regex]::Escape($PLUGIN_DIR)) {
            Write-Host "  [skip] $($skill.name) -- already installed with current path" -ForegroundColor Gray
            $skipped++
            continue
        }
    }

    $pluginDirForMd = $PLUGIN_DIR -replace '\\', '/'

    $content = @"
---
name: $($skill.name)
description: "$($skill.desc)"
---

Read and follow the complete orchestrator instructions at ``$pluginDirForMd/skills/$($skill.name)/SKILL.md``.

The plugin root for relative path resolution (agents/, references/) is ``$pluginDirForMd/``.
"@

    Set-Content -Path $skillFile -Value $content -Encoding UTF8
    Write-Host "  [ok] $($skill.name)" -ForegroundColor Green
    $created++
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "  Created: $created skill(s)"
Write-Host "  Skipped: $skipped skill(s) (already installed)"
Write-Host ""
Write-Host "Restart Cursor (or open a new window) to activate." -ForegroundColor Yellow
Write-Host "Then type /check in any project to start a code review." -ForegroundColor Yellow
Write-Host ""
