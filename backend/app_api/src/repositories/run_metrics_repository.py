from typing import Any

from src.database.db import get_connection


def save_run_metrics(run_id: str, metrics: dict) -> None:
    query = """
    INSERT INTO run_metrics (
        run_id, total_tweets, labeled_tweets, tp, fp, fn, tn,
        precision, recall, f1, accuracy, computed_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (run_id)
    DO UPDATE SET
        total_tweets = EXCLUDED.total_tweets,
        labeled_tweets = EXCLUDED.labeled_tweets,
        tp = EXCLUDED.tp,
        fp = EXCLUDED.fp,
        fn = EXCLUDED.fn,
        tn = EXCLUDED.tn,
        precision = EXCLUDED.precision,
        recall = EXCLUDED.recall,
        f1 = EXCLUDED.f1,
        accuracy = EXCLUDED.accuracy,
        computed_at = NOW()
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    run_id,
                    metrics.get("total_tweets", 0),
                    metrics.get("labeled_tweets", 0),
                    metrics.get("tp", 0),
                    metrics.get("fp", 0),
                    metrics.get("fn", 0),
                    metrics.get("tn", 0),
                    metrics.get("precision", 0.0),
                    metrics.get("recall", 0.0),
                    metrics.get("f1", 0.0),
                    metrics.get("accuracy", 0.0),
                ),
            )
        conn.commit()


def get_run_metrics(run_id: str) -> dict[str, Any] | None:
    query = "SELECT * FROM run_metrics WHERE run_id = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (run_id,))
            return cur.fetchone()


_BENCHMARK_RUNS_SELECT = """
    SELECT
        r.id AS run_id,
        r.status,
        r.started_at,
        r.finished_at,
        r.model_snapshot_json,
        m.tp, m.fp, m.fn, m.tn,
        m.precision, m.recall, m.f1, m.accuracy,
        m.total_tweets, m.labeled_tweets,
        m.computed_at
    FROM pipeline_runs r
    LEFT JOIN run_metrics m ON m.run_id = r.id
    WHERE r.benchmark_id = %s
"""


def list_benchmark_runs(benchmark_id: str) -> list[dict[str, Any]]:
    """Runs d'un benchmark joints à leurs métriques, ordre chronologique (données brutes)."""
    query = _BENCHMARK_RUNS_SELECT + " ORDER BY r.started_at ASC"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (benchmark_id,))
            return cur.fetchall()


def list_benchmark_leaderboard(benchmark_id: str) -> list[dict[str, Any]]:
    """Runs d'un benchmark joints à leurs métriques, triés par F1 décroissant."""
    query = _BENCHMARK_RUNS_SELECT + " ORDER BY m.f1 DESC NULLS LAST"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (benchmark_id,))
            return cur.fetchall()
