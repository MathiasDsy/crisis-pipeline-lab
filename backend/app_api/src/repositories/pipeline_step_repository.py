import uuid
from datetime import datetime
from typing import Any

from psycopg2.extras import Json

from src.database.db import get_connection

def get_step_execution_from_tweet_id(tweet_id: str) -> dict[str, Any] | None:
    query = """
    SELECT *
    FROM pipeline_step_executions
    WHERE tweet_id = %s
    ORDER BY created_at DESC, step_index DESC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tweet_id,))
            return cur.fetchall()


def create_step_execution(step: dict[str, Any]) -> dict[str, Any]:
    query = """
    INSERT INTO pipeline_step_executions (
        id,
        run_id,
        tweet_id,
        step_name,
        status,
        duration_ms,
        input_json,
        output_json,
        created_at,
        step_index
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING *
    """

    payload = {
        "id": str(uuid.uuid4()),
        "run_id": step["run_id"],
        "tweet_id": step["tweet_id"],
        "step_name": step["step_name"],
        "status": step["status"],
        "duration_ms": step["duration_ms"],
        "input_json": Json(step["input_json"]),
        "output_json": Json(step.get("output_json")),
        "created_at": datetime.utcnow(),
        "step_index": step["step_index"],
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    payload["id"],
                    payload["run_id"],
                    payload["tweet_id"],
                    payload["step_name"],
                    payload["status"],
                    payload["duration_ms"],
                    payload["input_json"],
                    payload["output_json"],
                    payload["created_at"],
                    payload["step_index"],
                ),
            )
            result = cur.fetchone()

        conn.commit()

    return result

def list_step_executions_by_run_id(
    run_id: str,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    query = """
    SELECT *
    FROM pipeline_step_executions
    WHERE run_id = %s
    ORDER BY created_at ASC, step_index ASC
    LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id, limit, offset))
            return cur.fetchall()


def count_step_executions_by_run_id(run_id: str) -> int:
    query = """
    SELECT COUNT(*) AS count
    FROM pipeline_step_executions
    WHERE run_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()["count"]