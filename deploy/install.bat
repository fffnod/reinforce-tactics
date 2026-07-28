@echo off
setlocal
cd /d "%~dp0\.."
echo.
echo ============================================
echo  Reinforce Tactics - One-click install
echo ============================================
echo.
echo Working directory: %CD%
echo.

where conda >nul 2>&1
if errorlevel 1 (
  echo [ERROR] conda not found in PATH.
  echo Install Miniconda or Anaconda first, then reopen this window.
  echo https://docs.conda.io/en/latest/miniconda.html
  echo.
  pause
  exit /b 1
)

REM Prefer PowerShell for the real installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 (
  echo [ERROR] Install failed with exit code %ERR%
  pause
  exit /b %ERR%
)

echo.
pause
exit /b 0
