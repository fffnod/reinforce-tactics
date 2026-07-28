#Requires -Version 5.1
<#
.SYNOPSIS
  Build a FULL offline deployment package (source + packed conda env + wheels).

.DESCRIPTION
  Produces dist/reinforce-tactics-offline-YYYYMMDD-HHMM.zip containing:
    - source/     project tree (no .git / training artifacts)
    - env/        conda-pack archive of reinforce-tactics env
    - wheels/     pip wheels mirror (optional rebuild aid)
    - deploy/     install-offline scripts
    - START_HERE.txt

  Target machine: unzip, run deploy\install-offline.bat — NO network required.

.PARAMETER EnvName
  Conda env to pack. Default: reinforce-tactics

.PARAMETER OutputDir
  Output directory for the zip. Default: <repo>/dist

.PARAMETER SkipWheels
  Do not download/export pip wheels (smaller package; env archive still enough).

.PARAMETER KeepStage
  Keep staging folder under %TEMP% for debugging.

.EXAMPLE
  .\deploy\pack-offline.ps1
  .\deploy\pack-offline.ps1 -SkipWheels
#>
[CmdletBinding()]
param(
    [string]$EnvName = "reinforce-tactics",
    [string]$OutputDir = "",
    [switch]$SkipWheels,
    [switch]$KeepStage
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDir) { $OutputDir = Join-Path $RepoRoot "dist" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$pkgName = "reinforce-tactics-offline-$stamp"
$stageRoot = Join-Path $env:TEMP $pkgName
$zipPath = Join-Path $OutputDir "$pkgName.zip"

function Write-Step([string]$m) { Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "  [OK] $m" -ForegroundColor Green }

Write-Host "Repo:  $RepoRoot"
Write-Host "Env:   $EnvName"
Write-Host "Stage: $stageRoot"
Write-Host "Out:   $zipPath"

# --- Preconditions ---
Write-Step "Checking conda env '$EnvName'"
$envList = conda env list 2>&1 | Out-String
if ($envList -notmatch "(?m)^\s*$([regex]::Escape($EnvName))\s") {
    throw "Conda env '$EnvName' not found. Run deploy\install.ps1 first."
}
Write-Ok "env exists"

# --- Install conda-pack ---
Write-Step "Ensuring conda-pack is available"
$hasPack = $false
try {
    $null = & conda run -n $EnvName python -c "import conda_pack; print(conda_pack.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) { $hasPack = $true }
} catch {
    $hasPack = $false
}
if (-not $hasPack) {
    Write-Host "  Installing conda-pack into env '$EnvName' via pip ..."
    & conda run -n $EnvName --no-capture-output python -m pip install "conda-pack>=0.7.0"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  pip failed; trying conda-forge ..."
        & conda install -n $EnvName -c conda-forge conda-pack -y
        if ($LASTEXITCODE -ne 0) { throw "Failed to install conda-pack" }
    }
}
Write-Ok "conda-pack ready"

# --- Bake non-editable install so packed env is self-contained ---
Write-Step "Installing project into env as non-editable (for portable paths)"
Push-Location $RepoRoot
try {
    conda run -n $EnvName --no-capture-output python -m pip install --force-reinstall --no-deps .
    if ($LASTEXITCODE -ne 0) { throw "non-editable install failed" }
} finally {
    Pop-Location
}
Write-Ok "non-editable install done"

# --- Stage dirs ---
Write-Step "Preparing stage tree"
if (Test-Path $stageRoot) { Remove-Item -Recurse -Force $stageRoot }
$envDir = Join-Path $stageRoot "env"
$srcDir = Join-Path $stageRoot "source"
$whlDir = Join-Path $stageRoot "wheels"
$depDir = Join-Path $stageRoot "deploy"
New-Item -ItemType Directory -Force -Path $envDir, $srcDir, $whlDir, $depDir | Out-Null

# --- conda-pack ---
Write-Step "Packing conda env (1GB+; several minutes)"
$archive = Join-Path $envDir "reinforce-tactics-env.tar.gz"
# Remove old archive if any
if (Test-Path $archive) { Remove-Item -Force $archive }

# Use conda-pack CLI (package has no __main__ module)
$condaPackExe = Join-Path $env:CONDA_PREFIX "Scripts\conda-pack.exe"
# Prefer the env's own Scripts, then base
$packCandidates = @(
    (Join-Path "$env:USERPROFILE\anaconda3\envs\$EnvName\Scripts" "conda-pack.exe"),
    (Join-Path "$env:USERPROFILE\miniconda3\envs\$EnvName\Scripts" "conda-pack.exe"),
    (Join-Path "$env:LOCALAPPDATA\anaconda3\envs\$EnvName\Scripts" "conda-pack.exe"),
    (Join-Path "$env:LOCALAPPDATA\miniconda3\envs\$EnvName\Scripts" "conda-pack.exe")
)
$packExe = $null
foreach ($c in $packCandidates) {
    if (Test-Path $c) { $packExe = $c; break }
}
if (-not $packExe) {
    $which = & conda run -n $EnvName where.exe conda-pack 2>$null | Select-Object -First 1
    if ($which -and (Test-Path $which)) { $packExe = $which.Trim() }
}
if (-not $packExe) { throw "conda-pack.exe not found in env '$EnvName'" }
Write-Host "  Using: $packExe"

& $packExe -n $EnvName -o $archive --compress-level 4 --ignore-editable-packages --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Retry without --ignore-editable-packages ..." -ForegroundColor Yellow
    & $packExe -n $EnvName -o $archive --compress-level 4 --force
    if ($LASTEXITCODE -ne 0) { throw "conda_pack failed" }
}
if (-not (Test-Path $archive)) { throw "Archive not created: $archive" }
$archMb = [math]::Round((Get-Item $archive).Length / 1MB, 1)
Write-Ok "Packed env archive: $archMb MB"

# --- Restore editable install on source machine ---
Write-Step "Restoring editable install on this machine"
Push-Location $RepoRoot
try {
    conda run -n $EnvName --no-capture-output python -m pip install -e ".[gui]"
} finally {
    Pop-Location
}
Write-Ok "editable install restored"

# --- Copy source ---
Write-Step "Copying project source"
& robocopy $RepoRoot $srcDir /E /R:1 /W:1 /NFL /NDL /NJH /NJS `
    /XD .git __pycache__ .pytest_cache htmlcov .mypy_cache .ruff_cache `
       models checkpoints tensorboard logs videos replays saves dist build `
       node_modules .venv tournament_results runtime `
    /XF settings.json *.pyc .coverage | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy source failed: $LASTEXITCODE" }
Write-Ok "source copied"

# --- Wheels (optional mirror) ---
if (-not $SkipWheels) {
    Write-Step "Exporting pip wheels (offline mirror)"
    $lock = Join-Path $RepoRoot "deploy\requirements-lock.txt"
    if (Test-Path $lock) {
        conda run -n $EnvName --no-capture-output python -m pip download -r $lock -d $whlDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARN] pip download had errors; env archive is still the primary offline runtime" -ForegroundColor Yellow
        } else {
            $wc = (Get-ChildItem $whlDir -File -ErrorAction SilentlyContinue | Measure-Object).Count
            Write-Ok "wheels: $wc files"
        }
    } else {
        Write-Host "  [WARN] no requirements-lock.txt; skipping wheels" -ForegroundColor Yellow
    }
    # Also build a wheel of the project itself
    Push-Location $RepoRoot
    try {
        conda run -n $EnvName --no-capture-output python -m pip wheel . -w $whlDir --no-deps
    } catch {
        Write-Host "  [WARN] project wheel build skipped: $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  Skipping wheels (-SkipWheels)" -ForegroundColor DarkGray
}

# --- Copy deploy scripts for offline install ---
Write-Step "Copying offline install scripts"
$copyScripts = @(
    "install-offline.ps1",
    "install-offline.bat",
    "verify.ps1",
    "README.md",
    "requirements-lock.txt",
    "environment.yml"
)
foreach ($s in $copyScripts) {
    $p = Join-Path $RepoRoot "deploy\$s"
    if (Test-Path $p) {
        Copy-Item $p -Destination (Join-Path $depDir $s) -Force
    }
}
# Also place bat at package root for double-click convenience
Copy-Item (Join-Path $RepoRoot "deploy\install-offline.bat") -Destination (Join-Path $stageRoot "install-offline.bat") -Force
# Root bat must call deploy\install-offline.ps1 with correct relative path
$rootBat = @"
@echo off
setlocal
cd /d "%~dp0"
echo.
echo ============================================
echo  Reinforce Tactics - Offline install
echo ============================================
echo Package: %CD%
echo.
if not exist "env\reinforce-tactics-env.tar.gz" (
  echo [ERROR] env\reinforce-tactics-env.tar.gz missing.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\install-offline.ps1" %*
set ERR=%ERRORLEVEL%
if %ERR% neq 0 (
  echo [ERROR] failed: %ERR%
  pause
  exit /b %ERR%
)
pause
exit /b 0
"@
Set-Content -Path (Join-Path $stageRoot "install-offline.bat") -Value $rootBat -Encoding ASCII

# --- START_HERE ---
$startHere = @"
# Reinforce Tactics — 完整离线部署包

打包时间: $stamp
源环境:   conda env '$EnvName'
源仓库:   $RepoRoot

## 目标电脑要求

- Windows 10/11 x64
- 无需联网
- 无需预先安装 Anaconda（运行时已打包）
- 需要 tar（Win10 自带 tar.exe）
- 建议可用磁盘 >= 5 GB

## 安装步骤

1. 将本 zip 解压到英文路径（避免空格与中文，例如 D:\rt-offline）
2. 双击 install-offline.bat
   或 PowerShell:
     cd <解压目录>
     .\deploy\install-offline.ps1
3. 安装完成后双击 Activate-ReinforceTactics.bat
4. 运行:
     python main.py

## 目录说明

| 目录/文件 | 说明 |
|-----------|------|
| env/reinforce-tactics-env.tar.gz | conda-pack 完整 Python 环境 |
| source/ | 项目源码（安装后以可编辑方式链接） |
| wheels/ | pip 轮子镜像（备用） |
| deploy/ | 离线安装与校验脚本 |
| install-offline.bat | 一键离线安装入口 |
| runtime/ | 安装后生成，解压后的环境（可删后重装） |

## 说明

- 本包内 PyTorch 一般为 CPU 版；目标机 GPU 不会自动启用 CUDA。
- 若只需更新源码，可替换 source/ 后重新执行 install-offline.ps1。
- 详细文档见 source\docs\LOCAL_DEPLOY.md
"@
Set-Content -Path (Join-Path $stageRoot "START_HERE.txt") -Value $startHere -Encoding UTF8

# --- Zip ---
Write-Step "Compressing offline package"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

# Compress-Archive has path-length and size issues on large trees; use tar if possible
$tarZip = $zipPath
# Prefer tar to create zip (bsdtar on Windows)
Push-Location (Split-Path $stageRoot -Parent)
try {
    $stageLeaf = Split-Path $stageRoot -Leaf
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    # .zip via tar
    & tar -a -cf $zipPath $stageLeaf
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  tar zip failed, trying Compress-Archive..." -ForegroundColor Yellow
        Compress-Archive -Path $stageRoot -DestinationPath $zipPath -CompressionLevel Fastest
    }
} finally {
    Pop-Location
}

if (-not (Test-Path $zipPath)) { throw "Failed to create $zipPath" }
$zipMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Ok "Created $zipPath ($zipMb MB)"

if (-not $KeepStage) {
    Remove-Item -Recurse -Force $stageRoot
    Write-Ok "Cleaned stage"
} else {
    Write-Host "  Stage kept: $stageRoot" -ForegroundColor Yellow
}

# Manifest next to zip
$manifest = @"
name: $pkgName
created: $stamp
zip: $zipPath
size_mb: $zipMb
env: $EnvName
arch_mb: $archMb
source_machine: $env:COMPUTERNAME
"@
Set-Content -Path (Join-Path $OutputDir "$pkgName.manifest.txt") -Value $manifest -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Offline package ready" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  $zipPath"
Write-Host "  Size: $zipMb MB"
Write-Host ""
Write-Host "Copy the zip to the target PC, unzip, run install-offline.bat"
