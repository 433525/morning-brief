try { Invoke-WebRequest -Uri 'http://127.0.0.1:8136/quit' -UseBasicParsing -TimeoutSec 5 | Out-Null } catch { }
Start-Sleep -Seconds 2
Get-Process -Name 'card-host','hub','node' -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*rustbuild*' } | Stop-Process -Force -ErrorAction SilentlyContinue