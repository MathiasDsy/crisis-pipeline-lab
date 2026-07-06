#!/bin/sh
set -e

DUMP="/data/photon-dump-croatia-1.0-latest.jsonl.zst"
URL="https://download1.graphhopper.com/public/europe/croatia/photon-dump-croatia-1.0-latest.jsonl.zst"

mkdir -p /data

echo "[Photon] Checking dump..."

if [ ! -f "$DUMP" ]; then
  echo "[Photon] Downloading Croatia dump..."
  wget -O "$DUMP" "$URL"
else
  echo "[Photon] Dump already exists."
fi

echo "[Photon] Checking imported index..."

if [ ! -d "/data/photon_data" ] || [ -z "$(ls -A /data/photon_data 2>/dev/null)" ]; then
  echo "[Photon] Importing dump into Photon/OpenSearch index..."
  rm -rf /data/photon_data

  zstd --stdout -d "$DUMP" | \
    java -jar /app/photon.jar import \
      -data-dir /data \
      -import-file -

  echo "[Photon] Import done."
else
  echo "[Photon] Existing photon_data found, skipping import."
fi

echo "[Photon] Starting server..."

exec java -jar /app/photon.jar serve \
  -data-dir /data \
  -listen-ip 0.0.0.0 \
  -listen-port 2322 \
  -cors-any