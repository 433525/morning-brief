param([string]$Name)
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
Set-Location 'C:\Users\Admin（无密码）\Desktop\数据文件\黑客松比赛项目'
python 'OctoScript-App-Design-Flow\tools\octo' shot 8136 "my-entry\evidence\$Name"