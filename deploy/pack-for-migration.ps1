#Requires -Version 5.1
<#
.SYNOPSIS
  Build a portable migration zip of this repo for copying to another PC.

.DESCRIPTION
  Creates a zip under dist/ containing source + deploy scripts + lock files,
  excluding training artifacts, caches, and local secrets.

  On the target PC:
    1. Unzip
    2. Install Miniconda/Anaconda if needed
    3. Double-click deploy\install.bat  (or run deploy\install.ps1)

.PARAMETER OutputDir
  Where to write the zip. Default: <repo>/dist

.EXAMPLE
  .\deploy\pack-for-migration.ps1
#>
[CmdletBinding()]
param(
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "dist"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$stageName = "reinforce-tactics-deploy-$stamp"
$stageRoot = Join-Path $env:TEMP $stageName
$zipPath = Join-Path $OutputDir "$stageName.zip"

if (Test-Path $stageRoot) { Remove-Item -Recurse -Force $stageRoot }
New-Item -ItemType Directory -Force -Path $stageRoot | Out-Null

Write-Host "Staging from: $RepoRoot"
Write-Host "Staging to:   $stageRoot"

# robocopy mirror-ish copy with exclusions
$excludeDirs = @(
    ".git",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    "models",
    "checkpoints",
    "tensorboard",
    "logs",
    "videos",
    "replays",
    "saves",
    "dist",
    "build",
    "*.egg-info",
    "node_modules",
    ".venv",
    "tournament_results"
)

$xdArgs = @()
foreach ($d in $excludeDirs) {
    if ($d -notlike "*.*") { $xdArgs += @("/XD", $d) }
}

# /E copy subdirs, /NFL /NDL /NJH /NJS quieter, /R:1 /W:1 retry
& robocopy $RepoRoot $stageRoot /E /R:1 /W:1 /NFL /NDL /NJH /NJS /XD .git __pycache__ .pytest_cache htmlcov .mypy_cache .ruff_cache models checkpoints tensorboard logs videos replays saves dist build node_modules .venv tournament_results docs-site\.docusaurus 2>&1 | Out-Null
# robocopy exit codes 0-7 are success-ish
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

# Drop local settings if copied
$settings = Join-Path $stageRoot "settings.json"
if (Test-Path $settings) { Remove-Item -Force $settings }

# Add a short START_HERE for the target machine
$startHere = @"
# Reinforce Tactics — 迁移包使用说明

打包时间: $stamp
来源机器仓库: $RepoRoot

## 目标电脑一键部署（Windows）

1. 安装 Miniconda 或 Anaconda（若尚未安装）
   https://docs.conda.io/en/latest/miniconda.html
2. 解压本目录到任意路径（路径尽量避免中文与空格）
3. 双击运行:  deploy\install.bat
   或在 PowerShell 中:
     cd <解压目录>
     .\deploy\install.ps1
4. 完成后:
     conda activate reinforce-tactics
     python main.py

详细文档见: docs\LOCAL_DEPLOY.md
验证脚本:   deploy\verify.ps1
"@
Set-Content -Path (Join-Path $stageRoot "START_HERE.txt") -Value $startHere -Encoding UTF8

if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Write-Host "Compressing to $zipPath ..."
Compress-Archive -Path $stageRoot -DestinationPath $zipPath -CompressionLevel Optimal

$sizeMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Remove-Item -Recurse -Force $stageRoot

Write-Host ""
Write-Host "Migration package ready:" -ForegroundColor Green
Write-Host "  $zipPath  ($sizeMb MB)"
Write-Host ""
Write-Host "Copy the zip to the other PC, unzip, run deploy\install.bat"
Write-Host "(Target PC still needs conda + network for first pip/conda downloads.)"
