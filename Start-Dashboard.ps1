param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) {
        throw 'Bitte zuerst die venv laut README erstellen.'
    }
    & $projectPython -m streamlit run dashboard/app.py --server.port $Port
    if ($LASTEXITCODE -ne 0) { throw "Dashboard beendet: Exit-Code $LASTEXITCODE" }
} finally {
    Pop-Location
}
