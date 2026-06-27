from typing import Any
from src.database.db import get_connection
from psycopg2.extras import Json


def insert_log(
    message: str,
    level: str = "info",
    context: str = "",
    run_id: str | None = None,
    details: dict | None = None,
) -> None:
    query = """
    INSERT INTO run_logs (run_id, level, context, message, details)
    VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id, level, context, message, Json(details or {})))
        conn.commit()


def list_logs(
    run_id: str | None = None,
    level: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM run_logs WHERE 1=1"
    params: list = []

    if run_id is not None:
        query += " AND run_id = %s"
        params.append(run_id)

    if level is not None:
        query += " AND level = %s"
        params.append(level)

    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
