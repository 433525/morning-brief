@echo off
title 晨报卡 Morning Brief — 一键体验
echo 正在启动「晨报卡」……
echo 稍等 10-20 秒，会弹出一个窗口，那就是我们的参赛作品。
echo 关闭窗口即可结束体验。
echo.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set OCTO_HUB=C:\rustbuild\octosense-hub\x86_64-pc-windows-gnu\release\hub.exe
set OCTO_CARD_HOST=C:\rustbuild\octosense-hub\x86_64-pc-windows-gnu\release\card-host.exe
set OCTOSENSE_APP_HUB=C:\Users\Admin（无密码）\Desktop\数据文件\黑客松比赛项目\OctoSense-App-Hub
cd /d "C:\Users\Admin（无密码）\Desktop\数据文件\黑客松比赛项目"
if not exist "%OCTO_HUB%" (
  echo [错误] 找不到运行组件：%OCTO_HUB%
  echo 请先完成环境搭建，见 04_项目实操指南.md。
  pause
  exit /b 1
)
python "OctoScript-App-Design-Flow\tools\octo" run "my-entry\morning-brief\bundle" --port 8160 --timeout 120
echo.
echo 体验结束。
pause
