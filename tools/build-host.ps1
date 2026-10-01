$ErrorActionPreference = 'Stop'
$briefRoot = Split-Path -Parent $PSScriptRoot
$briefTools = Join-Path $briefRoot '.local-tools'
$briefCargo = Join-Path $briefTools 'cargo/bin/cargo.exe'
$briefGcc = Join-Path $briefTools 'mingw64/bin/gcc.exe'
foreach ($briefRequired in @($briefCargo, $briefGcc)) {
    if (-not (Test-Path -LiteralPath $briefRequired)) { throw "Missing local build tool: $briefRequired" }
}
$env:CARGO_HOME = Join-Path $briefTools 'cargo'
$env:RUSTUP_HOME = Join-Path $briefTools 'rustup'
$env:CARGO_TARGET_DIR = Join-Path $briefTools 'target'
$env:PATH = (Join-Path $briefTools 'mingw64/bin') + ';' + (Join-Path $briefTools 'cargo/bin') + ';' + $env:PATH
$env:CC = $briefGcc
$env:CARGO_NET_GIT_FETCH_WITH_CLI = 'true'
Push-Location (Join-Path $briefRoot 'OctoSense-App-Hub')
try {
    & $briefCargo build --release -p octosense-card-host -p octosense-app-hub
    if ($LASTEXITCODE -ne 0) { throw "Host build failed ($LASTEXITCODE)" }
} finally { Pop-Location }
