param([int]$Port = 8136, [string]$AppData = '', [switch]$Hidden, [string]$Bundle = '')
$ErrorActionPreference = 'Stop'
$briefRoot = Split-Path -Parent $PSScriptRoot
$briefTools = Join-Path $briefRoot '.local-tools'
$briefHost = Join-Path $briefTools 'target/release/card-host.exe'
$briefOcto = Join-Path $briefTools 'official-flow/tools/octo'
if (-not (Test-Path -LiteralPath $briefHost)) { throw 'Build the local host first: tools/build-host.ps1' }
if (-not (Test-Path -LiteralPath $briefOcto)) { throw 'Official tools/octo is missing; see docs/UI升级工作记录.md' }
if (-not $AppData) { $AppData = Join-Path $briefRoot '.local-state/ui-upgrade' }
if (-not $Bundle) { $Bundle = Join-Path $briefRoot 'my-entry/morning-brief/bundle' }
$env:OCTO_CARD_HOST = $briefHost
$env:OCTO_HUB = Join-Path $briefTools 'target/release/hub.exe'
$env:OCTOSENSE_APP_HUB = Join-Path $briefRoot 'OctoSense-App-Hub'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$briefArgs = @($briefOcto, 'run', $Bundle, '--port', "$Port", '--timeout', '120', '--detach', '--app-data', $AppData)
if ($Hidden) { $briefArgs += '--hidden' }
& python @briefArgs
if ($LASTEXITCODE -ne 0) { throw "card-host startup failed ($LASTEXITCODE)" }
