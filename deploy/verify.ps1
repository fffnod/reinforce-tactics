#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke-test a Reinforce Tactics conda environment.
#>
[CmdletBinding()]
param(
    [string]$EnvName = "reinforce-tactics"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Ok([string]$msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }

$failed = 0

function Invoke-Check {
    param([string]$Name, [string[]]$PyArgs)
    Write-Host "  Testing: $Name ..." -ForegroundColor DarkGray
    & conda run -n $EnvName --no-capture-output python @PyArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Fail $Name
        $script:failed++
    } else {
        Write-Ok $Name
    }
}

# C1 imports
Invoke-Check "imports" @(
    "-c",
    "import reinforcetactics, gymnasium, torch, pygame; print('gymnasium', gymnasium.__version__); print('torch', torch.__version__, 'cuda', torch.cuda.is_available()); print('pygame', pygame.version.ver)"
)

# C2 CLI
Invoke-Check "cli_help" @("main.py", "--help")

# C3 pygame display (may fail on headless servers — warn only)
Write-Host "  Testing: pygame_display ..." -ForegroundColor DarkGray
& conda run -n $EnvName --no-capture-output python -c @"
import pygame
pygame.init()
try:
    s = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('rt-smoke')
    pygame.event.pump()
    print('pygame_display_ok', s.get_size())
except Exception as e:
    print('pygame_display_skip', type(e).__name__, e)
    raise SystemExit(2)
finally:
    pygame.quit()
"@
if ($LASTEXITCODE -eq 0) {
    Write-Ok "pygame_display"
} elseif ($LASTEXITCODE -eq 2) {
    Write-Host "  [WARN] pygame display unavailable (headless?) — GUI may not work" -ForegroundColor Yellow
} else {
    Write-Fail "pygame_display"
    $failed++
}

# Optional env step
Invoke-Check "gym_env_step" @(
    "-c",
    "from reinforcetactics.rl.gym_env import StrategyGameEnv; e=StrategyGameEnv(map_file='maps/1v1/beginner.csv', opponent='bot', render_mode=None); o,i=e.reset(); a=e.action_space.sample(); e.step(a); e.close(); print('env_ok')"
)

if ($failed -gt 0) {
    Write-Fail "$failed check(s) failed"
    exit 1
}
Write-Ok "All smoke tests passed"
exit 0
