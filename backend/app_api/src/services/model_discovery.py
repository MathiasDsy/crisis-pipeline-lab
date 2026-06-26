import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any

MODELS_DIR = Path("/app/storage/models")


def discover_models_from_storage() -> list[dict[str, Any]]:
    discovered = []

    if not MODELS_DIR.exists():
        return discovered

    for model_dir in MODELS_DIR.iterdir():
        if not model_dir.is_dir():
            continue

        metadata_path = model_dir / "metadata.json"

        if not metadata_path.exists():
            continue

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

            required_fields = [
                "model_key",
                "name",
                "model_type",
                "version",
                "entrypoint",
                "compatible_components",
            ]

            missing_fields = [
                field for field in required_fields
                if field not in metadata
            ]

            if missing_fields:
                discovered.append({
                    "model_dir": str(model_dir),
                    "is_valid": False,
                    "error": f"Missing fields: {missing_fields}",
                })
                continue

            entrypoint_path = model_dir / metadata["entrypoint"]

            discovered.append({
                "id": str(uuid.uuid4()),
                "model_key": metadata["model_key"],
                "name": metadata["name"],
                "version": metadata["version"],
                "model_type": metadata["model_type"],
                "compatible_components_key": metadata["compatible_components"],
                "local_path": str(entrypoint_path),
                "is_available": entrypoint_path.exists(),
                "metadata_json": metadata,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_valid": True,
            })

        except Exception as e:
            discovered.append({
                "model_dir": str(model_dir),
                "is_valid": False,
                "error": str(e),
            })

    return discovered