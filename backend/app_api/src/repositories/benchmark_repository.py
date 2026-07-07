import uuid
from datetime import datetime
from typing import Any

from psycopg2.extras import Json

from src.database.db import get_connection


def create_benchmark(
    name: str | None,
    dataset_id: str,
    classifier_model_keys: list[str],
    location_model_keys: list[str],
    total_runs: int,
) -> dict[str, Any]:
    query = """
    INSERT INTO benchmarks (
        id, name, dataset_id, classifier_model_keys, location_model_keys,
        total_runs, completed_runs, status, created_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, 0, 'running', %s)
    RETURNING *
    """
    benchmark_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    benchmark_id,
                    name,
                    dataset_id,
                    Json(classifier_model_keys),
                    Json(location_model_keys),
                    total_runs,
                    datetime.utcnow(),
                ),
            )
            benchmark = cur.fetchone()
        conn.commit()
    return benchmark


def get_benchmark_by_id(benchmark_id: str) -> dict[str, Any] | None:
    query = "SELECT * FROM benchmarks WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (benchmark_id,))
            return cur.fetchone()


def list_benchmarks() -> list[dict[str, Any]]:
    query = "SELECT * FROM benchmarks ORDER BY created_at DESC"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def count_running_benchmarks() -> int:
    query = "SELECT COUNT(*) AS count FROM benchmarks WHERE status = 'running'"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()["count"]


def fail_orphaned_benchmarks() -> int:
    """
    Mark every benchmark still flagged 'running' as 'error'.

    Like runs, benchmarks execute in-process, so a 'running' benchmark at startup
    is a leftover from a restart/crash. Reconciling it releases the concurrency
    lock shared with simulations. Returns the count.
    """
    query = """
    UPDATE benchmarks
    SET status = 'error',
        finished_at = NOW()
    WHERE status = 'running'
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            affected = cur.rowcount
        conn.commit()
    return affected


def increment_completed_runs(benchmark_id: str) -> None:
    query = """
    UPDATE benchmarks
    SET completed_runs = completed_runs + 1
    WHERE id = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (benchmark_id,))
        conn.commit()


def update_benchmark_status(benchmark_id: str, status: str) -> None:
    finished = status in ("completed", "cancelled", "error")
    query = """
    UPDATE benchmarks
    SET status = %s,
        finished_at = CASE WHEN %s THEN NOW() ELSE finished_at END
    WHERE id = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (status, finished, benchmark_id))
        conn.commit()
