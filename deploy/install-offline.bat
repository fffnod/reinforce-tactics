@echo off
setlocal
cd /d "%~dp0\.."
echo.
echo ============================================
echo  Reinforce Tactics - Offline install
echo ============================================
echo.
echo Working directory: %CD%
echo.

if not exist "env\reinforce-tactics-env.tar.gz" (
  echo [ERROR] env\reinforce-tactics-env.tar.gz not found.
  echo This script must be run from an unpacked OFFLINE package root
  echo ^(folder that contains env\, source\, deploy^\).
  echo.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-offline.ps1" %*
set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 (
  echo [ERROR] Offline install failed with exit code %ERR%
  pause
  exit /b %ERR%
)
echo.
pause
exit /b 0
