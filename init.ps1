#requires -Version 5.1
<#
.SYNOPSIS
  Provision and launch Crisis Pipeline Lab in one command (Windows equivalent of init.sh).

  1. download the 2 models (relevance + GLiNER) from HuggingFace
  2. download + import the Photon geocoder dump (OSM)
  3. build + start the whole Docker stack

  Requirements: Docker Desktop. No host-side Python/Java/zstd needed
  (everything runs inside throwaway containers).

.EXAMPLE
  .\init.ps1
.EXAMPLE
  $env:PHOTON_DUMP_URL="https://download1.graphhopper.com/public/europe/france/photon-dump-france-1.0-latest.jsonl.zst"; .\init.ps1
.EXAMPLE
  $env:HF_TOKEN="hf_xxx"; .\init.ps1   # if a model repo is private
#>
$ErrorActionPreference = "Stop"

$Root          = $PSScriptRoot
$ModelsDir     = Join-Path $Root "backend\storage\models"
$PhotonDataDir = Join-Path $Root "services\photon\data"

# Regional Photon dump (GraphHopper hosts it — nothing to self-host).
$PhotonDumpUrl = if ($env:PHOTON_DUMP_URL) { $env:PHOTON_DUMP_URL } `
                 else { "https://download1.graphhopper.com/public/europe/croatia/photon-dump-croatia-1.0-latest.jsonl.zst" }
$HfToken = if ($env:HF_TOKEN) { $env:HF_TOKEN } else { "" }

function Log($msg) { Write-Host "`n==> $msg" -ForegroundColor Blue }

# --- 0. prerequisites -------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker is required." }
docker compose version *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose v2 is required." }
$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) { New-Item -ItemType File -Path $envFile | Out-Null }

# --- 1. models --------------------------------------------------------------
Log "Downloading models (relevance + GLiNER)..."
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
docker run --rm `
  -e MODELS_DIR=/models `
  -e "HF_TOKEN=$HfToken" `
  -v "${ModelsDir}:/models" `
  -v "$(Join-Path $Root 'scripts'):/scripts:ro" `
  python:3.11-slim `
  bash -c "pip install -q --no-cache-dir huggingface_hub && python /scripts/download_models.py /scripts/models_manifest.json"
if ($LASTEXITCODE -ne 0) { throw "Model download failed." }

# --- 2. Photon dump: download + import -> servable index --------------------
$photonIndex = Join-Path $PhotonDataDir "photon_data\elasticsearch"
if (Test-Path $photonIndex) {
  Log "Photon index already present - skipping."
} else {
  Log "Provisioning Photon (download + import, one-time, a few minutes)..."
  New-Item -ItemType Directory -Force -Path $PhotonDataDir | Out-Null

  # 1) download + decompress the .jsonl.zst (throwaway alpine container)
  docker run --rm -v "${PhotonDataDir}:/data" alpine:3 sh -c `
    "apk add --no-cache curl zstd >/dev/null && curl -fL '$PhotonDumpUrl' | zstd -d -o /data/_photon_dump.jsonl"
  if ($LASTEXITCODE -ne 0) { throw "Photon dump download failed." }

  # 2) import the dump -> /data/photon_data (photon image = Java + jar)
  docker build -q -t photon-tools:local (Join-Path $Root "services\photon") | Out-Null
  docker run --rm -v "${PhotonDataDir}:/data" --entrypoint java photon-tools:local `
    -jar /app/photon.jar -import-file /data/_photon_dump.jsonl -data-dir /data
  if ($LASTEXITCODE -ne 0) { throw "Photon import failed." }

  Remove-Item -Force (Join-Path $PhotonDataDir "_photon_dump.jsonl") -ErrorAction SilentlyContinue
}

# --- 3. stack ---------------------------------------------------------------
Log "Building + starting the Docker stack..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed." }

Log "Ready."
Write-Host @"

  Frontend      -> http://localhost:5173
  pipeline-api  -> http://localhost:8000/docs
  model-server  -> http://localhost:8001/docs

  Logs  : docker compose logs -f
  Stop  : docker compose down
"@
