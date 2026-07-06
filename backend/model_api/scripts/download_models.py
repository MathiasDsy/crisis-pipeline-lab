#!/usr/bin/env python3
"""
Download the models required by the pipeline from the HuggingFace Hub.

Reuses the exact mechanism of the import route (`snapshot_download`) and
(re)writes each model's `metadata.json` from the manifest, since that file — not
the Hub contents — drives discovery in pipeline-api.

Idempotent: a model already present (weights detected on disk) is skipped.

Configuration via environment variables:
  MODELS_DIR  target directory          (default: backend/storage/models)
  HF_TOKEN    HF token for private repos (optional)

Usage:
  python download_models.py [path/to/models_manifest.json]
"""

import json
import os
import sys
from pathlib import Path

WEIGHT_SUFFIXES = (".safetensors", ".bin")


def _has_weights(target: Path) -> bool:
    if not target.is_dir():
        return False
    return any(
        p.suffix in WEIGHT_SUFFIXES and not p.name.endswith("training_args.bin")
        for p in target.iterdir()
        if p.is_file()
    )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "models_manifest.json"
    models_dir = Path(os.environ.get("MODELS_DIR", repo_root / "backend" / "storage" / "models"))
    hf_token = os.environ.get("HF_TOKEN") or None

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is not installed (pip install huggingface_hub)", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    models = manifest.get("models", [])
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Models directory : {models_dir}")
    print(f"Manifest         : {manifest_path}")
    print(f"{len(models)} model(s) to provision\n")

    for entry in models:
        repo_id = entry["repo_id"]
        target = models_dir / entry["target_dir"]
        metadata = entry["metadata"]

        if _has_weights(target):
            print(f"[skip] {entry['target_dir']} — already present")
        else:
            print(f"[dl]   {entry['target_dir']} <- {repo_id}")
            try:
                snapshot_download(repo_id=repo_id, local_dir=str(target), token=hf_token)
            except Exception as e:  # noqa: BLE001
                print(f"ERROR downloading '{repo_id}': {e}", file=sys.stderr)
                return 1

        # the manifest's metadata.json is the source of truth (discovery depends on it)
        target.mkdir(parents=True, exist_ok=True)
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"       metadata.json written ({metadata['model_key']})")

    print("\nModels ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
