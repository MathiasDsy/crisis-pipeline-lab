from typing import Any

from psycopg2.extras import Json

from src.database.db import get_connection


def list_pipeline_configs(valid: bool | None = None) -> list[dict[str, Any]]:
    query = """
    SELECT
        id,
        name,
        version,
        description,
        config_json,
        required_models_json,
        required_components_json,
        original_filename,
        created_at,
        is_valid,
        validation_errors
    FROM pipeline_configs
    WHERE 1 = 1
    """

    params = []

    if valid is not None:
        query += " AND is_valid = %s"
        params.append(valid)

    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
def get_pipeline_config_by_id(
    pipeline_config_id: str,
) -> dict | None:
    query = """
    SELECT
        id,
        name,
        version,
        description,
        config_json,
        required_models_json,
        required_components_json,
        original_filename,
        created_at,
        is_valid,
        validation_errors
    FROM pipeline_configs
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (pipeline_config_id,))
            return cur.fetchone()
        
def upsert_pipeline_config(pipeline: dict[str, Any]) -> None:
    query = """
    INSERT INTO pipeline_configs (
        id,
        name,
        version,
        description,
        config_json,
        required_models_json,
        required_components_json,
        original_filename,
        config_hash,
        is_valid,
        validation_errors,
        created_at
    )
    VALUES (
        %(id)s,
        %(name)s,
        %(version)s,
        %(description)s,
        %(config_json)s,
        %(required_models_json)s,
        %(required_components_json)s,
        %(original_filename)s,
        %(config_hash)s,
        %(is_valid)s,
        %(validation_errors)s,
        %(created_at)s
    )
    ON CONFLICT (config_hash)
    DO UPDATE SET
        name = EXCLUDED.name,
        version = EXCLUDED.version,
        description = EXCLUDED.description,
        config_json = EXCLUDED.config_json,
        required_models_json = EXCLUDED.required_models_json,
        required_components_json = EXCLUDED.required_components_json,
        original_filename = EXCLUDED.original_filename,
        is_valid = EXCLUDED.is_valid,
        validation_errors = EXCLUDED.validation_errors
    """

    payload = pipeline.copy()
    payload["config_json"] = Json(payload["config_json"])
    payload["required_models_json"] = Json(payload["required_models_json"])
    payload["required_components_json"] = Json(payload["required_components_json"])
    payload["validation_errors"] = Json(payload["validation_errors"])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, payload)
        conn.commit()

def update_pipeline_validation(
    pipeline_config_id: str,
    is_valid: bool,
    errors: list[str],
) -> None:
    query = """
    UPDATE pipeline_configs
    SET
        is_valid = %s,
        validation_errors = %s
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    is_valid,
                    Json(errors),
                    pipeline_config_id,
                ),
            )
        conn.commit()

def delete_pipeline_config_by_id(pipeline_config_id: str) -> bool:
    query = """
    DELETE FROM pipeline_configs
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (pipeline_config_id,))
            deleted = cur.rowcount > 0

        conn.commit()

    return deleted