from src.database.db import get_connection
from datetime import datetime

def list_events(
    run_id: str | None = None,
    active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = """
    SELECT *
    FROM events
    WHERE 1=1
    """

    params = []

    if run_id is not None:
        query += " AND run_id = %s"
        params.append(run_id)

    if active is not None:
        query += " AND is_active = %s"
        params.append(active)

    query += """
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
        
def get_event_by_id(event_id: str) -> dict | None:
    query = """
    SELECT *
    FROM events
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (event_id,))
            return cur.fetchone()


def list_tweets_by_event_id(
    event_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = """
    SELECT *
    FROM tweets
    WHERE event_id = %s
    ORDER BY created_at ASC
    LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (event_id, limit, offset))
            return cur.fetchall()


def update_event_active_status(
    event_id: str,
    is_active: bool,
) -> dict | None:
    query = """
    UPDATE events
    SET
        is_active = %s,
        finished_at = CASE
            WHEN %s = false THEN %s
            ELSE NULL
        END
    WHERE id = %s
    RETURNING *
    """

    now = datetime.utcnow()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    is_active,
                    is_active,
                    now,
                    event_id,
                ),
            )
            event = cur.fetchone()

        conn.commit()

    return event


def list_events_by_run_id(
    run_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = """
    SELECT *
    FROM events
    WHERE run_id = %s
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id, limit, offset))
            return cur.fetchall()