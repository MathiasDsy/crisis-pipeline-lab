#!/bin/sh
#
# Model-server entrypoint: provision the models into the storage volume, then
# hand over to the server command. download_models.py is idempotent (it skips
# models whose weights are already on disk), so this is cheap on every boot but
# does the full download once, on first start — same pattern as the Photon service.
#
set -e

export MODELS_DIR="${MODELS_DIR:-/app/storage/models}"

echo "[model-server] Provisioning models into $MODELS_DIR ..."
python /app/scripts/download_models.py /app/scripts/models_manifest.json
echo "[model-server] Models ready — starting server."

exec "$@"
