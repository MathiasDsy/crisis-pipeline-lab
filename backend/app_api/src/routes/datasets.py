from datetime import datetime
import uuid
import pandas as pd
from pathlib import Path
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from src.services.dataset_discovery import discover_datasets, compute_hash
from src.repositories.dataset_repository import get_dataset_by_id, upsert_dataset
from src.repositories.dataset_repository import list_datasets as list_datasets_from_db

router = APIRouter(prefix="/datasets", tags=["datasets"])

DATASETS_DIR = Path("/app/storage/datasets")

@router.get("")
def list_datasets(
    valid: bool | None = None,
):
    datasets = list_datasets_from_db(
        valid=valid
    )

    return {
        "datasets": datasets,
        "count": len(datasets),
        "filters": {
            "valid": valid,
        },
    }


@router.get("/schema")
def get_dataset_schema():
    return {
        "format": "csv",
        "required_columns": ["content", "label"],
        "optional_columns": ["id", "created_at", "source"],
        "example": {
            "content": "Smoke visible near Split"
        }
    }



@router.post("/discover")
def discover_datasets_route():

    datasets = discover_datasets()

    for dataset in datasets:
        upsert_dataset(dataset)

    return {
        "status": "success",
        "count": len(datasets),
        "datasets": datasets,
    }


@router.post("/import")
async def import_dataset(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported",
        )

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    target_path = DATASETS_DIR / file.filename

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        df = pd.read_csv(target_path, nrows=5)

        errors = []

        if "content" not in df.columns:
            errors.append("Missing required column: content")

        if "label" not in df.columns:
            errors.append("Missing required column: label")

        file_hash = compute_hash(target_path)

        dataset = {
            "id": str(uuid.uuid4()),
            "name": target_path.stem,
            "path": str(target_path),
            "hash": file_hash,
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "metadata_json": {
                "filename": file.filename,
                "columns": list(df.columns),
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        upsert_dataset(dataset)

        return {
            "status": "success",
            "dataset": dataset,
        }

    except Exception as e:
        target_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Could not import dataset: {e}",
        )

@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: str, rows: int = 10):
    dataset = get_dataset_by_id(dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    try:
        df = pd.read_csv(dataset["path"], nrows=rows)
        return {
            "dataset_id": dataset_id,
            "rows": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "count": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read dataset: {e}")


@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: str):
    dataset = get_dataset_by_id(dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    path = Path(dataset["path"])

    if not path.exists():
        raise HTTPException(status_code=404, detail="Dataset file missing on disk")

    filename = dataset.get("metadata_json", {}).get("filename") or f"{dataset['name']}.csv"

    return FileResponse(
        path,
        media_type="text/csv",
        filename=filename,
    )


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    dataset = get_dataset_by_id(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found",
        )

    return dataset