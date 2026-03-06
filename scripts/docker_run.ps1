Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..

# Build lightweight image (keyword-fallback sentiment available without transformers/torch)
docker build -t customer-health-score:latest .

# Run full synthetic pipeline and persist outputs in mounted workspace
docker run --rm -v ${PWD}:/app customer-health-score:latest
