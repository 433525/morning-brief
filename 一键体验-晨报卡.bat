@echo off
rem ============================================================
rem   Morning Brief - one-click trial
rem   (kept for compatibility with the old file name)
rem
rem   FIXED 2026-10-11
rem   This file used to hard-code the OLD card-host build at
rem       C:\rustbuild\octosense-hub\x86_64-pc-windows-gnu\release\
rem   which predates the "model" capability. The card was then
rem   refused by the host ("unknown capability model") and the
rem   window never showed a usable UI.
rem
rem   It now delegates to tools\launch.py, which selects the host
rem   by checking the binary for the "model.complete" marker and
rem   therefore skips the stale build.
rem ============================================================
chcp 65001 >nul
title Morning Brief
setlocal

set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo   Morning Brief  -^>  tools\launch.py %*
echo.

"%PY%" "%~dp0tools\launch.py" %*
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
  echo   [stopped with code %RC%] - please read the messages above.
  pause
)

endlocal
exit /b %RC%
