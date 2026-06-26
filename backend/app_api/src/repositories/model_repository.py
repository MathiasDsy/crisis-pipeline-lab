from typing import Any

from psycopg2.extras import Json

from src.database.db import get_connection


def list_models(
    model_type: str | None = None,
    available: bool | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            model_key,
            name,
            version,
            model_type,
            compatible_components_key,
            local_path,
            is_available,
            metadata_json,
            created_at,
            updated_at
        FROM model_registry
        WHERE 1 = 1
    """

    params = {}

    if model_type is not None:
        query += " AND model_type = %(model_type)s"
        params["model_type"] = model_type

    if available is not None:
        query += " AND is_available = %(available)s"
        params["available"] = available

    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
        
def upsert_model(model: dict) -> None:
    query = """
    INSERT INTO model_registry (
        id,
        name,
        model_key,
        model_type,
        compatible_components_key,
        version,
        local_path,
        is_available,
        metadata_json,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s,
        %(name)s,
        %(model_key)s,
        %(model_type)s,
        %(compatible_components_key)s,
        %(version)s,
        %(local_path)s,
        %(is_available)s,
        %(metadata_json)s,
        %(created_at)s,
        %(updated_at)s
    )
    ON CONFLICT (model_key)
    DO UPDATE SET
        name = EXCLUDED.name,
        model_type = EXCLUDED.model_type,
        compatible_components_key = EXCLUDED.compatible_components_key,
        version = EXCLUDED.version,
        local_path = EXCLUDED.local_path,
        is_available = EXCLUDED.is_available,
        metadata_json = EXCLUDED.metadata_json,
        updated_at = EXCLUDED.updated_at
    """

    payload = model.copy()

    payload["compatible_components_key"] = Json(
        payload["compatible_components_key"]
    )

    payload["metadata_json"] = Json(
        payload["metadata_json"]
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, payload)

        conn.commit()



def get_model_by_key(model_key: str) -> dict | None:
    query = """
    SELECT *
    FROM model_registry
    WHERE model_key = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (model_key,))
            return cur.fetchone()
        
def update_model_availability(
    model_key: str,
    is_available: bool,
) -> None:
    query = """
    UPDATE model_registry
    SET
        is_available = %s,
        updated_at = NOW()
    WHERE model_key = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (is_available, model_key)
            )

        conn.commit()

