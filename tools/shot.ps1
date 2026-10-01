param([string]$Name = 'ui-upgrade.png', [int]$Port = 8136)
$ErrorActionPreference = 'Stop'
$briefRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
& python (Join-Path $briefRoot '.local-tools/official-flow/tools/octo') shot $Port (Join-Path $briefRoot "my-entry/evidence/$Name")
if ($LASTEXITCODE -ne 0) { throw "Screenshot failed ($LASTEXITCODE)" }
