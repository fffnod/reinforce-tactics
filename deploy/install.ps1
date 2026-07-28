#Requires -Version 5.1
<#
.SYNOPSIS
  One-click local deploy for Reinforce Tactics (Windows).

.DESCRIPTION
  Creates conda env "reinforce-tactics" (Python 3.12), installs pinned deps,
  installs this repo in editable mode with [gui], then runs smoke checks.

.PARAMETER EnvName
  Conda environment name. Default: reinforce-tactics

.PARAMETER PythonVersion
  Python version for the env. Default: 3.12

.PARAMETER SkipVerify
  Skip post-install smoke tests.

.PARAMETER UseLock
  Install from deploy/requirements-lock.txt (reproducible). Default: $true

.PARAMETER Extras
  pip extra for editable install. Default: gui  (options: gui, all, or empty for base)

.EXAMPLE
  .\deploy\install.ps1
  .\deploy\install.ps1 -Extras all
  .\deploy\install.ps1 -SkipVerify
#>
[CmdletBinding()]
param(
    [string]$EnvName = "reinforce-tactics",
    [string]$PythonVersion = "3.12",
    [switch]$SkipVerify,
    [bool]$UseLock = $true,
    [ValidateSet("gui", "all", "base", "dev")]
    [string]$Extras = "gui"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Write-Ok([string]$msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }

# Resolve repo root (parent of deploy/)
$DeployDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent $DeployDir
Set-Location $RepoRoot
Write-Host "Repo root: $RepoRoot" -ForegroundColor DarkGray

# --- Preconditions ---
Write-Step "Checking prerequisites"

$condaCmd = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCmd) {
    Write-Fail "conda not found in PATH."
    Write-Host @"

Install one of:
  - Miniconda: https://docs.conda.io/en/latest/miniconda.html
  - Anaconda:  https://www.anaconda.com/download

Then re-open PowerShell and run this script again.
"@
    exit 1
}
Write-Ok "conda: $((conda --version) 2>&1)"

# --- Create / reuse env ---
Write-Step "Ensuring conda env '$EnvName' (Python $PythonVersion)"

$envList = conda env list 2>&1 | Out-String
if ($envList -match "(?m)^\s*$([regex]::Escape($EnvName))\s") {
    Write-Warn "Env '$EnvName' already exists — will reuse and upgrade packages."
} else {
    conda create -n $EnvName "python=$PythonVersion" -y
    if ($LASTEXITCODE -ne 0) { throw "conda create failed (exit $LASTEXITCODE)" }
    Write-Ok "Created env '$EnvName'"
}

# Helper: run python/pip inside env without relying on Activate.ps1
function Invoke-Env {
    param([Parameter(Mandatory)][string[]]$Args)
    & conda run -n $EnvName --no-capture-output @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed in env '$EnvName': conda run -n $EnvName $($Args -join ' ')"
    }
}

$pyVer = (conda run -n $EnvName python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1 | Select-Object -Last 1)
Write-Ok "Python in env: $pyVer"

# --- Install deps ---
Write-Step "Installing Python packages (this may take 10-30+ minutes; torch is large)"

$lockFile = Join-Path $DeployDir "requirements-lock.txt"
if ($UseLock -and (Test-Path $lockFile)) {
    Write-Host "  Using lock file: $lockFile"
    Invoke-Env -Args @("python", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    Invoke-Env -Args @("python", "-m", "pip", "install", "-r", $lockFile)
} else {
    Write-Warn "Lock file missing or disabled — installing from pyproject extras only."
}

# Editable project install
$extraArg = switch ($Extras) {
    "base" { "." }
    "gui"  { ".[gui]" }
    "dev"  { ".[gui,dev]" }
    "all"  { ".[all]" }
}
Write-Host "  Editable install: pip install -e `"$extraArg`""
Invoke-Env -Args @("python", "-m", "pip", "install", "-e", $extraArg)
Write-Ok "Package installed (editable)"

# --- Verify ---
if (-not $SkipVerify) {
    Write-Step "Smoke tests"
    $verify = Join-Path $DeployDir "verify.ps1"
    if (Test-Path $verify) {
        & $verify -EnvName $EnvName
        if ($LASTEXITCODE -ne 0) { throw "Verification failed" }
    } else {
        Invoke-Env -Args @("python", "-c", "import reinforcetactics, gymnasium, torch, pygame; print('imports_ok', torch.__version__, 'cuda', torch.cuda.is_available())")
        Invoke-Env -Args @("python", "main.py", "--help")
        Write-Ok "Basic checks passed"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Deploy finished successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host @"

Next steps:
  1. conda activate $EnvName
  2. cd `"$RepoRoot`"
  3. python main.py              # GUI game
  4. python main.py --mode play

Docs: docs\LOCAL_DEPLOY.md
"@
