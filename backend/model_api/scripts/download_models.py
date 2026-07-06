#!/usr/bin/env python3
"""
Télécharge les modèles requis par le pipeline depuis le HuggingFace Hub.

Réutilise exactement le mécanisme de la route d'import (`snapshot_download`) et
(ré)écrit le `metadata.json` de chaque modèle depuis le manifest, car c'est ce
fichier — pas le contenu du Hub — qui pilote le discovery côté pipeline-api.

Idempotent : un modèle déjà présent (poids détectés sur disque) est ignoré.

Configuration via variables d'environnement :
  MODELS_DIR  répertoire cible          (défaut: backend/storage/models)
  HF_TOKEN    token HF pour repos privés (optionnel)

Usage:
  python download_models.py [chemin/vers/models_manifest.json]
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
        print("ERREUR: huggingface_hub n'est pas installé (pip install huggingface_hub)", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    models = manifest.get("models", [])
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Répertoire modèles : {models_dir}")
    print(f"Manifest           : {manifest_path}")
    print(f"{len(models)} modèle(s) à provisionner\n")

    for entry in models:
        repo_id = entry["repo_id"]
        target = models_dir / entry["target_dir"]
        metadata = entry["metadata"]

        if _has_weights(target):
            print(f"[skip] {entry['target_dir']} — déjà présent")
        else:
            print(f"[dl]   {entry['target_dir']} <- {repo_id}")
            try:
                snapshot_download(repo_id=repo_id, local_dir=str(target), token=hf_token)
            except Exception as e:  # noqa: BLE001
                print(f"ERREUR téléchargement '{repo_id}': {e}", file=sys.stderr)
                return 1

        # metadata.json du manifest fait autorité (le discovery en dépend)
        target.mkdir(parents=True, exist_ok=True)
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"       metadata.json écrit ({metadata['model_key']})")

    print("\nModèles prêts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
