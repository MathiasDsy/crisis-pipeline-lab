#!/usr/bin/env bash
#
# init.sh — provisionne et lance Crisis Pipeline Lab en une commande.
#
#   1. télécharge les 2 modèles (relevance + GLiNER) depuis HuggingFace
#   2. télécharge le dump Photon (géocodeur OSM) si une URL est fournie
#   3. build + démarre toute la stack Docker (api, model-server, photon, postgres, front)
#
# Prérequis : Docker + Docker Compose. Aucune install Python côté hôte
# (le download tourne dans un conteneur jetable python:3.11-slim).
#
# Usage :
#   ./init.sh                    # download + up
#   PHOTON_DUMP_URL=https://... ./init.sh
#   HF_TOKEN=hf_xxx ./init.sh    # si un des repos modèles est privé
#
set -euo pipefail
export MSYS_NO_PATHCONV=1  # git-bash (Windows) : ne pas mangler les chemins /data des -v

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODELS_DIR="$ROOT/backend/storage/models"
PHOTON_DATA_DIR="$ROOT/services/photon/data"

# Dump Photon (géocodeur). GraphHopper publie un dump régional prêt à importer ;
# rien à héberger soi-même. Format .jsonl.zst -> importé via `photon -import-file`.
# Change la région/version ici au besoin.
PHOTON_DUMP_URL="${PHOTON_DUMP_URL:-https://download1.graphhopper.com/public/europe/croatia/photon-dump-croatia-1.0-latest.jsonl.zst}"

log() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }

# --- 0. pré-requis ----------------------------------------------------------
command -v docker >/dev/null 2>&1 || { echo "Docker est requis."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 est requis."; exit 1; }
[ -f "$ROOT/.env" ] || touch "$ROOT/.env"

# --- 1. modèles -------------------------------------------------------------
log "Téléchargement des modèles (relevance + GLiNER)…"
mkdir -p "$MODELS_DIR"
docker run --rm \
  -e MODELS_DIR=/models \
  -e HF_TOKEN="${HF_TOKEN:-}" \
  -v "$MODELS_DIR:/models" \
  -v "$ROOT/scripts:/scripts:ro" \
  python:3.11-slim \
  bash -c "pip install -q --no-cache-dir huggingface_hub && python /scripts/download_models.py /scripts/models_manifest.json"

# --- 2. dump Photon (géocodeur) : download + import -> index servable --------
if [ -d "$PHOTON_DATA_DIR/photon_data/elasticsearch" ]; then
  log "Index Photon déjà présent — skip."
else
  log "Provisioning Photon (download + import, étape unique, quelques minutes)…"
  mkdir -p "$PHOTON_DATA_DIR"
  dump="$PHOTON_DATA_DIR/_photon_dump.jsonl"

  # 1) download + décompression du .jsonl.zst (conteneur alpine jetable)
  docker run --rm -v "$PHOTON_DATA_DIR:/data" alpine:3 sh -c \
    "apk add --no-cache curl zstd >/dev/null && curl -fL '$PHOTON_DUMP_URL' | zstd -d -o /data/_photon_dump.jsonl"

  # 2) import du dump -> /data/photon_data (via l'image photon, qui a Java + le jar)
  docker build -q -t photon-tools:local "$ROOT/services/photon" >/dev/null
  docker run --rm -v "$PHOTON_DATA_DIR:/data" --entrypoint java photon-tools:local \
    -jar /app/photon.jar -import-file /data/_photon_dump.jsonl -data-dir /data

  rm -f "$dump"
fi

# --- 3. stack ---------------------------------------------------------------
log "Build + démarrage de la stack Docker…"
docker compose up -d --build

log "Prêt."
cat <<'EOF'

  Frontend      → http://localhost:5173
  pipeline-api  → http://localhost:8000/docs
  model-server  → http://localhost:8001/docs

  Logs   : docker compose logs -f
  Arrêt  : docker compose down
EOF
