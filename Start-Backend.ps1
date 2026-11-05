param([int]$Port = 15020)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) {
        throw 'Bitte zuerst die venv laut README erstellen.'
    }
    & $projectPython -m windconnect.runner --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Backend beendet: Exit-Code $LASTEXITCODE" }
} finally {
    Pop-Location
}
