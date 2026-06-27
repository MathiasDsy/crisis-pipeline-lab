import uuid
from datetime import datetime
from typing import Any

from src.database.db import get_connection


def create_tweet(
    content: str,
    run_id: str,
    source: str = "dataset",
    event_id: str | None = None,
    label: bool | None = None,
) -> dict[str, Any]:
    query = """
    INSERT INTO tweets (
        id,
        content,
        event_id,
        run_id,
        source,
        label,
        created_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    str(uuid.uuid4()),
                    content,
                    event_id,
                    run_id,
                    source,
                    label,
                    datetime.utcnow(),
                ),
            )
            tweet = cur.fetchone()

        conn.commit()

    return tweet

def get_tweet_by_id(tweet_id: str) -> dict[str, Any] | None:
    query = """
    SELECT *
    FROM tweets
    WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tweet_id,))
            return cur.fetchone()


def list_tweets_by_run_id(
    run_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = """
    SELECT *
    FROM tweets
    WHERE run_id = %s
    ORDER BY created_at ASC
    LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id, limit, offset))
            return cur.fetchall()

def list_false_negatives_by_run_id(run_id: str) -> list[dict]:
    query = """
    SELECT t.*
    FROM tweets t
    WHERE t.run_id = %s
      AND t.label = true
      AND EXISTS (
          SELECT 1 FROM pipeline_step_executions pse
          WHERE pse.tweet_id = t.id
      )
      AND NOT EXISTS (
          SELECT 1 FROM pipeline_step_executions pse
          WHERE pse.tweet_id = t.id AND pse.status = 'blocked'
      )
    ORDER BY t.created_at ASC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchall()


def count_tweets_by_run_id(run_id: str) -> int:
    query = """
    SELECT COUNT(*) AS count
    FROM tweets
    WHERE run_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            result = cur.fetchone()
            return result["count"]
        
