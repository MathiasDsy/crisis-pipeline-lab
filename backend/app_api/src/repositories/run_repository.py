import uuid
from datetime import datetime
from typing import Any

from src.database.db import get_connection

from psycopg2.extras import Json

def list_runs(
    mode: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = """
    SELECT *
    FROM pipeline_runs
    WHERE 1=1
    """

    params = []

    if mode is not None:
        query += " AND mode = %s"
        params.append(mode)

    if status is not None:
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY started_at DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

def count_running_runs() -> int:
    query = "SELECT COUNT(*) AS count FROM pipeline_runs WHERE status = 'running'"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()["count"]


def find_completed_simulation_run(
    dataset_id: str,
    pipeline_config_id: str,
) -> dict[str, Any] | None:
    query = """
    SELECT *
    FROM pipeline_runs
    WHERE dataset_id = %s
      AND pipeline_config_id = %s
      AND mode = 'simulation'
      AND status = 'completed'
    ORDER BY finished_at DESC
    LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (dataset_id, pipeline_config_id))
            return cur.fetchone()


def create_pipeline_run(
    dataset_id: str | None,
    pipeline_config_id: str | None,
    mode: str,
    status: str = "running",
    model_snapshot: dict | None = None,
    benchmark_id: str | None = None,
) -> dict[str, Any]:

    run_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    query = """
    INSERT INTO pipeline_runs (
        id,
        pipeline_config_id,
        dataset_id,
        benchmark_id,
        mode,
        status,
        started_at,
        finished_at,
        model_snapshot_json
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        NULL,
        %s
    )
    RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    run_id,
                    pipeline_config_id,
                    dataset_id,
                    benchmark_id,
                    mode,
                    status,
                    started_at,
                    Json(model_snapshot) if model_snapshot else Json({}),
                ),
            )

            run = cur.fetchone()

        conn.commit()

    return run


def list_runs_by_benchmark_id(benchmark_id: str) -> list[dict[str, Any]]:
    query = """
    SELECT * FROM pipeline_runs
    WHERE benchmark_id = %s
    ORDER BY started_at ASC
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (benchmark_id,))
            return cur.fetchall()

def complete_pipeline_run(run_id: str, status: str = "completed") -> dict[str, Any]:
    query = """
    UPDATE pipeline_runs
    SET
        status = %s,
        finished_at = %s
    WHERE id = %s
    RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    status,
                    datetime.utcnow(),
                    run_id,
                ),
            )
            run = cur.fetchone()

        conn.commit()

    return run

def get_run_by_id(run_id: str) -> dict | None:
    query = """
    SELECT *
    FROM pipeline_runs
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()


def count_run_events(run_id: str) -> int:
    query = """
    SELECT COUNT(*) AS count
    FROM events
    WHERE run_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()["count"]


def count_run_steps(run_id: str) -> int:
    query = """
    SELECT COUNT(*) AS count
    FROM pipeline_step_executions
    WHERE run_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()["count"]


def count_run_errors(run_id: str) -> int:
    query = """
    SELECT COUNT(*) AS count
    FROM pipeline_step_executions
    WHERE run_id = %s
      AND status = 'error'
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()["count"]
        
def fail_orphaned_runs() -> int:
    """
    Mark every run still flagged 'running' as 'error'.

    Runs execute in-process (within the /start request), so a run left 'running'
    can only be a leftover from a process restart/crash — the executor is gone.
    Reconciling these on startup prevents a stranded run from holding the
    concurrency lock and blocking every future simulation. Returns the count.
    """
    query = """
    UPDATE pipeline_runs
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


def cancel_run(run_id: str) -> dict | None:
    query = """
    UPDATE pipeline_runs
    SET status = 'cancelled',
        finished_at = NOW()
    WHERE id = %s
      AND status = 'running'
    RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            run = cur.fetchone()

        conn.commit()

    return run