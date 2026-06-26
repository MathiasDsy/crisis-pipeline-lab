from typing import Any

from src.database.db import get_connection
from psycopg2.extras import Json

def upsert_dataset(dataset: dict):

    query = """
    INSERT INTO datasets (
        id,
        name,
        path,
        hash,
        is_valid,
        validation_errors,
        metadata_json,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s,
        %(name)s,
        %(path)s,
        %(hash)s,
        %(is_valid)s,
        %(validation_errors)s,
        %(metadata_json)s,
        %(created_at)s,
        %(updated_at)s
    )
    ON CONFLICT (hash)
    DO UPDATE SET
        name = EXCLUDED.name,
        path = EXCLUDED.path,
        is_valid = EXCLUDED.is_valid,
        validation_errors = EXCLUDED.validation_errors,
        metadata_json = EXCLUDED.metadata_json,
        updated_at = EXCLUDED.updated_at
    """

    payload = dataset.copy()

    payload["validation_errors"] = Json(
        payload["validation_errors"]
    )

    payload["metadata_json"] = Json(
        payload["metadata_json"]
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, payload)

        conn.commit()

def get_dataset_by_id(dataset_id: str) -> dict[str, Any] | None:
    query = """
    SELECT *
    FROM datasets
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (dataset_id,))
            return cur.fetchone()

def list_datasets(
    valid: bool | None = None,
) -> list[dict]:

    query = """
    SELECT *
    FROM datasets
    WHERE 1=1
    """

    params = []

    if valid is not None:
        query += " AND is_valid = %s"
        params.append(valid)

    query += """
    ORDER BY updated_at DESC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()