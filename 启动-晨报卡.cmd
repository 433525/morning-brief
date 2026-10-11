@echo off
rem ============================================================
rem   Morning Brief (chen bao ka) - clear local launcher
rem
rem   Double-click me. I locate Python, then hand over to the
rem   project's own validated launcher:  tools\launch.py
rem
rem   WHY DELEGATE: tools\launch.py is the single source of truth.
rem   It picks the NEW card-host build (the one that knows the
rem   "model" capability), wires up the AI path, and prints usage.
rem   Launching card-host directly with a hand-written path is how
rem   the card used to end up refused and blank.
rem
rem   Optional: pass a port, e.g.   启动-晨报卡.cmd --port 8170
rem ============================================================
chcp 65001 >nul
title Morning Brief Launcher
setlocal

set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo   Morning Brief launcher  -^>  tools\launch.py %*
echo.

"%PY%" "%~dp0tools\launch.py" %*
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
  echo   [launcher stopped with code %RC%] - please read the messages above.
  pause
)

endlocal
exit /b %RC%
