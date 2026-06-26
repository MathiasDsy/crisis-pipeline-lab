from fastapi import APIRouter, UploadFile, File, HTTPException

from src.repositories.pipeline_repository import delete_pipeline_config_by_id, get_pipeline_config_by_id, list_pipeline_configs as list_pipeline_configs_from_db, update_pipeline_validation
from src.services.pipeline_import_service import (
    parse_pipeline_file,
    build_pipeline_record,
)
from src.repositories.pipeline_repository import upsert_pipeline_config
from src.services.pipeline_validation_service import validate_pipeline_runtime

router = APIRouter(
    prefix="/pipelines",
    tags=["pipelines"],
)


@router.get("")
def list_pipeline_configs(valid: bool | None = None):
    """
    Liste les pipeline configs importées.
    """
    pipelines = list_pipeline_configs_from_db(valid=valid)

    return {
        "pipelines": pipelines,
        "filters": {
            "valid": valid,
        },
    }

@router.get("/{pipeline_config_id}")
def get_pipeline_config(pipeline_config_id: str):
    """
    Détail d'une pipeline config.
    """

    pipeline = get_pipeline_config_by_id(
        pipeline_config_id
    )

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_config_id}' not found"
        )

    return pipeline



@router.post("/import")
async def import_pipeline_config(file: UploadFile = File(...)):
    try:
        content = await file.read()

        config = parse_pipeline_file(content)

        pipeline_record = build_pipeline_record(
            config=config,
            filename=file.filename or "unknown.yaml",
        )

        upsert_pipeline_config(pipeline_record)

        return {
            "status": "success",
            "filename": file.filename,
            "pipeline_config": pipeline_record,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/{pipeline_config_id}/validate")
def validate_pipeline_config(pipeline_config_id: str):
    pipeline = get_pipeline_config_by_id(pipeline_config_id)

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_config_id}' not found",
        )

    is_valid, errors = validate_pipeline_runtime(pipeline)

    update_pipeline_validation(
        pipeline_config_id=pipeline_config_id,
        is_valid=is_valid,
        errors=errors,
    )

    return {
        "pipeline_config_id": pipeline_config_id,
        "is_valid": is_valid,
        "errors": errors,
    }


@router.delete("/{pipeline_config_id}")
def delete_pipeline_config(pipeline_config_id: str):
    deleted = delete_pipeline_config_by_id(pipeline_config_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_config_id}' not found",
        )

    return {
        "pipeline_config_id": pipeline_config_id,
        "status": "deleted",
    }