param([int]$Port = 8136)
$ErrorActionPreference = 'Stop'
try { Invoke-WebRequest -Uri "http://127.0.0.1:$Port/quit" -UseBasicParsing -TimeoutSec 5 | Out-Null }
catch { Write-Output "No running card-host responded on port $Port." }
