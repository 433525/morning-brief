@echo off
chcp 65001 >nul
title 晨报卡（改版 UI）
setlocal

set "ROOT=%~dp0"
set "BUNDLE=%ROOT%my-entry\morning-brief\bundle"
set "OCTO_DRIVER=D:\morning-brief\OctoScript-App-Design-Flow\tools\octo"
set "OCTO_HUB=D:\morning-brief\.local-tools\target\release\hub.exe"
set "OCTO_CARD_HOST=D:\morning-brief\.local-tools\target\release\card-host.exe"
set "OCTOSENSE_APP_HUB=D:\morning-brief\OctoSense-App-Hub"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

if not exist "%BUNDLE%" (
  echo 找不到改版 UI bundle：%BUNDLE%
  pause
  exit /b 1
)
if not exist "%OCTO_DRIVER%" (
  echo 找不到 Octo 启动驱动：%OCTO_DRIVER%
  pause
  exit /b 1
)
if not exist "%OCTO_HUB%" (
  echo 找不到 hub.exe：%OCTO_HUB%
  pause
  exit /b 1
)
if not exist "%OCTO_CARD_HOST%" (
  echo 找不到 card-host.exe：%OCTO_CARD_HOST%
  pause
  exit /b 1
)

powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'card-host.exe' -and $_.CommandLine -like ('*' + $env:BUNDLE + '*') } | Select-Object -First 1; if ($p) { $w=New-Object -ComObject WScript.Shell; if ($w.AppActivate([int]$p.ProcessId)) { exit 0 } }; exit 1" >nul 2>&1
if not errorlevel 1 exit /b 0

where python >nul 2>&1
if errorlevel 1 (
  echo 找不到 Python，请确认 Python 已安装并加入 PATH。
  pause
  exit /b 1
)

python -u "%OCTO_DRIVER%" run "%BUNDLE%" --port 8160 --timeout 120 --detach --app-data "%TEMP%\morning-brief-redesign-live"
if errorlevel 1 (
  echo.
  echo 启动失败，请查看上方错误信息。
  pause
  exit /b 1
)
exit /b 0

