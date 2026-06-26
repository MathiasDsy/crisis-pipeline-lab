# src/services/dataset_discovery.py

import hashlib
import uuid

from pathlib import Path
from datetime import datetime

import pandas as pd


DATASETS_DIR = Path("/app/storage/datasets")


def compute_hash(path: Path) -> str:
    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(
            lambda: f.read(8192),
            b""
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def discover_datasets():
    datasets = []

    if not DATASETS_DIR.exists():
        return datasets

    for file_path in DATASETS_DIR.glob("*.csv"):

        try:

            df = pd.read_csv(
                file_path,
                nrows=5
            )

            errors = []

            if "content" not in df.columns:
                errors.append("Missing required column: content")

            if "label" not in df.columns:
                errors.append("Missing required column: label")

            datasets.append({
                "id": str(uuid.uuid4()),
                "name": file_path.stem,
                "path": str(file_path),
                "hash": compute_hash(file_path),
                "is_valid": len(errors) == 0,
                "validation_errors": errors,
                "metadata_json": {
                    "columns": list(df.columns)
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })

        except Exception as e:

            datasets.append({
                "id": str(uuid.uuid4()),
                "name": file_path.stem,
                "path": str(file_path),
                "hash": compute_hash(file_path),
                "is_valid": False,
                "validation_errors": [str(e)],
                "metadata_json": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })

    return datasets