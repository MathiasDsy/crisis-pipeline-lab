from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.repositories.model_repository import get_model_by_key, list_models as list_models_from_db, update_model_availability
from src.repositories.model_repository import upsert_model
from src.services.model_discovery import discover_models_from_storage

router = APIRouter(
    prefix="/models",
    tags=["models"],
)


@router.get("")
def list_models(
    model_type: str | None = None,
    available: bool | None = None,
):
    models = list_models_from_db(
        model_type=model_type,
        available=available,
    )

    return {
        "models": models,
        "filters": {
            "model_type": model_type,
            "available": available,
        },
    }


@router.get("/{model_key}")
def get_model(model_key: str):
    """
    Récupère le détail d'un modèle par model_key.
    """

    model = get_model_by_key(model_key)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_key}' not found"
        )

    return model


@router.post("/discover")
def discover_models():
    discovered = discover_models_from_storage()

    valid_models = [
        model for model in discovered
        if model.get("is_valid") is True
    ]

    invalid_models = [
        model for model in discovered
        if model.get("is_valid") is False
    ]

    for model in valid_models:
        model_to_save = model.copy()
        model_to_save.pop("is_valid", None)
        upsert_model(model_to_save)

    return {
        "status": "success",
        "models_dir": "/app/storage/models",
        "discovered_count": len(discovered),
        "valid_count": len(valid_models),
        "invalid_count": len(invalid_models),
        "valid_models": valid_models,
        "invalid_models": invalid_models,
    }


@router.post("/{model_key}/check")
def check_model_availability(model_key: str):
    """
    Vérifie qu'un modèle existe vraiment sur le disque.
    """

    model = get_model_by_key(model_key)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_key}' not found"
        )

    path = Path(model["local_path"])

    is_available = path.exists()

    update_model_availability(
        model_key=model_key,
        is_available=is_available,
    )

    return {
        "model_key": model_key,
        "local_path": str(path),
        "is_available": is_available,
    }