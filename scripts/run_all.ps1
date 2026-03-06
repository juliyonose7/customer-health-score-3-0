Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..

python -m src.run_pipeline --skip-generate
pytest -q
