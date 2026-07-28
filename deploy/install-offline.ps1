#Requires -Version 5.1
<#
.SYNOPSIS
  Install Reinforce Tactics from a full offline package (no network).

.DESCRIPTION
  Expects to run from an unpacked offline bundle that contains:
    - env/reinforce-tactics-env.tar.gz   (conda-pack archive)
    - source/                            (project source tree)
    - deploy/ scripts (this file may live under deploy/ or package root)

  Unpacks the Python env, runs conda-unpack, re-links the project to local
  source (editable, --no-deps), and runs offline smoke checks.

.PARAMETER Prefix
  Directory where the conda env will be extracted.
  Default: <package-root>\runtime\reinforce-tactics

.PARAMETER SkipVerify
  Skip smoke tests after install.

.EXAMPLE
  .\deploy\install-offline.ps1
  .\install-offline.ps1 -Prefix D:\rt-env
#>
[CmdletBinding()]
param(
    [string]$Prefix = "",
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$m) { Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Fail([string]$m) { Write-Host "  [FAIL] $m" -ForegroundColor Red }

# Locate package root: prefer parent of deploy/ when this script is in deploy/,
# or current directory when env/ + source/ sit next to this script.
$ScriptDir = $PSScriptRoot
if (Test-Path (Join-Path $ScriptDir "env\reinforce-tactics-env.tar.gz")) {
    $PkgRoot = $ScriptDir
} elseif (Test-Path (Join-Path (Split-Path $ScriptDir -Parent) "env\reinforce-tactics-env.tar.gz")) {
    $PkgRoot = Split-Path $ScriptDir -Parent
} elseif (Test-Path (Join-Path $ScriptDir "..\env\reinforce-tactics-env.tar.gz")) {
    $PkgRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
} else {
    # Offline zip layout: package-root/{env,source,deploy}
    $candidate = Split-Path $ScriptDir -Parent
    if (Test-Path (Join-Path $candidate "env\reinforce-tactics-env.tar.gz")) {
        $PkgRoot = $candidate
    } else {
        throw "Cannot find env\reinforce-tactics-env.tar.gz. Run this script from the offline package root or deploy\ folder."
    }
}

$EnvArchive = Join-Path $PkgRoot "env\reinforce-tactics-env.tar.gz"
$SourceDir = Join-Path $PkgRoot "source"
if (-not (Test-Path $EnvArchive)) { throw "Missing archive: $EnvArchive" }
if (-not (Test-Path $SourceDir)) { throw "Missing source dir: $SourceDir" }

if (-not $Prefix) {
    $Prefix = Join-Path $PkgRoot "runtime\reinforce-tactics"
}

Write-Host "Package root : $PkgRoot"
Write-Host "Env archive  : $EnvArchive"
Write-Host "Source       : $SourceDir"
Write-Host "Install prefix: $Prefix"

# --- Extract env ---
Write-Step "Extracting conda environment (this may take several minutes)"
if (Test-Path $Prefix) {
    Write-Host "  Removing existing prefix: $Prefix" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $Prefix
}
New-Item -ItemType Directory -Force -Path $Prefix | Out-Null

$tar = Get-Command tar -ErrorAction SilentlyContinue
if (-not $tar) {
    throw "tar not found. Windows 10+ includes tar.exe; install it or extract the .tar.gz manually to: $Prefix"
}

# tar.gz extract into prefix
& tar -xzf $EnvArchive -C $Prefix
if ($LASTEXITCODE -ne 0) { throw "tar extract failed (exit $LASTEXITCODE)" }
Write-Ok "Extracted to $Prefix"

# --- conda-unpack ---
Write-Step "Running conda-unpack (fix path prefixes)"
$unpackBat = Join-Path $Prefix "Scripts\conda-unpack.exe"
$unpackPy = Join-Path $Prefix "Scripts\conda-unpack-script.py"
$pythonExe = Join-Path $Prefix "python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "python.exe not found under $Prefix — archive may be corrupt"
}

if (Test-Path $unpackBat) {
    & $unpackBat
    if ($LASTEXITCODE -ne 0) { throw "conda-unpack failed (exit $LASTEXITCODE)" }
} elseif (Test-Path $unpackPy) {
    & $pythonExe $unpackPy
    if ($LASTEXITCODE -ne 0) { throw "conda-unpack (py) failed (exit $LASTEXITCODE)" }
} else {
    # Some packs ship conda-unpack as console script entry only
    $candidates = @(
        (Join-Path $Prefix "Scripts\conda-unpack.exe"),
        (Join-Path $Prefix "bin\conda-unpack")
    )
    $found = $false
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            & $c
            $found = $true
            break
        }
    }
    if (-not $found) {
        Write-Host "  [WARN] conda-unpack not found; paths may still work if prefixes match" -ForegroundColor Yellow
    }
}
Write-Ok "conda-unpack done"

# --- Link local source (offline-safe; no pip build isolation / network) ---
# conda-pack already bakes a non-editable copy of the package. For development we
# prefer the shipped source/ tree via a .pth file so edits take effect without
# needing setuptools build deps from the network.
Write-Step "Linking project source (offline .pth, no network)"
$sitePackages = Join-Path $Prefix "Lib\site-packages"
if (-not (Test-Path $sitePackages)) {
    throw "site-packages not found: $sitePackages"
}

# Best-effort remove baked distribution so source wins on import
& $pythonExe -m pip uninstall -y reinforcetactics 2>$null | Out-Null

$pthFile = Join-Path $sitePackages "reinforce_tactics_offline_source.pth"
# One path per line; Python site module adds it to sys.path
Set-Content -Path $pthFile -Value $SourceDir -Encoding ASCII
Write-Ok "Wrote $pthFile -> $SourceDir"

# Sanity: import must resolve under source/
$resolve = & $pythonExe -c "import reinforcetactics, os; print(os.path.abspath(os.path.dirname(reinforcetactics.__file__)))"
if ($LASTEXITCODE -ne 0) { throw "import after .pth link failed" }
Write-Host "  import path: $resolve"
$srcNorm = (Resolve-Path $SourceDir).Path
if ($resolve -notlike "$srcNorm*") {
    Write-Host "  [WARN] import path is not under source/; baked package may still be active" -ForegroundColor Yellow
} else {
    Write-Ok "Source linked: $SourceDir"
}

# --- Helper activate script ---
Write-Step "Writing activate helper"
$runtimeDir = Split-Path $Prefix -Parent
$activatePs1 = Join-Path $PkgRoot "Activate-ReinforceTactics.ps1"
$activateBat = Join-Path $PkgRoot "Activate-ReinforceTactics.bat"
$activateBody = @"
# Auto-generated — activates the offline runtime for this package
`$env:PATH = "$(Join-Path $Prefix 'Scripts');$(Join-Path $Prefix 'Library\bin');$Prefix;" + `$env:PATH
Set-Location "$SourceDir"
Write-Host "Reinforce Tactics offline env active." -ForegroundColor Green
Write-Host "Python: $Prefix\python.exe"
Write-Host "Source: $SourceDir"
Write-Host "Run: python main.py"
"@
Set-Content -Path $activatePs1 -Value $activateBody -Encoding UTF8
$batBody = @"
@echo off
set "PATH=$Prefix\Scripts;$Prefix\Library\bin;$Prefix;%PATH%"
cd /d "$SourceDir"
echo Reinforce Tactics offline env active.
echo Run: python main.py
cmd /k
"@
Set-Content -Path $activateBat -Value $batBody -Encoding ASCII
Write-Ok "Wrote $activatePs1"
Write-Ok "Wrote $activateBat"

# --- Verify ---
if (-not $SkipVerify) {
    Write-Step "Smoke tests (offline)"
    & $pythonExe -c "import reinforcetactics, gymnasium, torch, pygame; print('ok', torch.__version__, 'cuda', torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "import check failed" }
    Write-Ok "imports"

    Push-Location $SourceDir
    try {
        & $pythonExe main.py --help | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "main.py --help failed" }
        Write-Ok "cli_help"
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Offline install finished" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host @"

Next:
  1. Double-click Activate-ReinforceTactics.bat
     or:  . .\Activate-ReinforceTactics.ps1
  2. python main.py

Env prefix: $Prefix
Source:     $SourceDir
"@
