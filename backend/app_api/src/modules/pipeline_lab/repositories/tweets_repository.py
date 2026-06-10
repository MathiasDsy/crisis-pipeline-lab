# src/modules/pipeline_lab/repositories/tweets_repository.py

import os
import psycopg2
import psycopg2.extras
from typing import Any, Dict
import json

class TweetsRepository:
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://crisis:crisis@localhost:5432/crisis_db",
        )

    def _get_connection(self):
        return psycopg2.connect(self.database_url)

    def save_pipeline_execution(self, payload: Dict[str, Any]) -> None:
        tweet = payload["tweet"]
        run = payload["run"]
        steps = payload["steps"]

        try:
            with self._get_connection() as conn:
            
                with conn.cursor() as cur:
                    # 1. Save tweet
                    cur.execute("""
                        INSERT INTO tweets (
                            id,
                            text,
                            source
                        )
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            text = EXCLUDED.text,
                            source = EXCLUDED.source;
                    """, (
                        tweet["id"],
                        tweet["text"],
                        tweet.get("source", "twitter"),
                    ))

                    # 2. Save pipeline run
                    cur.execute("""
                        INSERT INTO pipeline_runs (
                            id,
                            tweet_id,
                            pipeline_config,
                            status,
                            stopped_at,
                            final_lat,
                            final_lon,
                            raw_json
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb);
                    """, (
                        run["id"],
                        run["tweet_id"],
                        run["pipeline_config"],
                        run["status"],
                        run.get("stopped_at"),
                        run.get("final_lat"),
                        run.get("final_lon"),
                        json.dumps(run.get("raw_json", {})),
                    ))

                    # 3. Save pipeline steps
                    for index, step in enumerate(steps):
                        cur.execute("""
                            INSERT INTO pipeline_steps (
                                run_id,
                                step_id,
                                step_name,
                                status,
                                description,
                                duration_ms,
                                output,
                                step_order
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                            ON CONFLICT (run_id, step_id) DO UPDATE SET
                                step_name = EXCLUDED.step_name,
                                status = EXCLUDED.status,
                                description = EXCLUDED.description,
                                duration_ms = EXCLUDED.duration_ms,
                                output = EXCLUDED.output,
                                step_order = EXCLUDED.step_order;
                        """, (
                            run["id"],
                            step["step_id"],
                            step.get("step_name", step["step_id"]),
                            step.get("status", "success"),
                            step.get("component"),
                            int(step.get("duration_ms", 0)),
                            json.dumps({
                                "input": step.get("input"),
                                "output_path": step.get("output_path"),
                                "output": step.get("output"),
                                "error": step.get("error"),
                                "component": step.get("component"),
                            }),
                            index,
                        ))
                    conn.commit()
        except Exception:
                raise

    def count_tweets(self) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM tweets")
                return cur.fetchone()[0]

    def get_all_tweets(self):
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        t.id AS tweet_id,
                        t.event_id,
                        t.text,
                        t.created_at AS tweet_created_at,

                        pr.id AS run_id,
                        pr.pipeline_config,
                        pr.status AS run_status,
                        pr.stopped_at,
                        pr.final_lat,
                        pr.final_lon,
                        pr.raw_json,
                        pr.created_at AS run_created_at,

                        COALESCE(
                            jsonb_agg(
                                jsonb_build_object(
                                    'id', ps.step_id,
                                    'stepDbId', ps.id,
                                    'stepOrder', ps.step_order,
                                    'name', ps.step_name,
                                    'status', ps.status,
                                    'description', ps.description,
                                    'duration', ps.duration_ms,
                                    'output', ps.output,
                                    'annotation', CASE
                                        WHEN sa.id IS NULL THEN NULL
                                        ELSE jsonb_build_object(
                                            'id', sa.id,
                                            'label', sa.label,
                                            'annotatedBy', sa.annotated_by,
                                            'notes', sa.notes,
                                            'annotatedAt', sa.annotated_at
                                        )
                                    END
                                )
                                ORDER BY ps.step_order ASC, ps.created_at ASC
                            ) FILTER (WHERE ps.id IS NOT NULL),
                            '[]'::jsonb
                        ) AS trace

                    FROM tweets t
                    LEFT JOIN pipeline_runs pr
                        ON pr.tweet_id = t.id

                    LEFT JOIN pipeline_steps ps
                        ON ps.run_id = pr.id

                    LEFT JOIN step_annotations sa
                        ON sa.pipeline_step_id = ps.id

                    GROUP BY
                        t.id,
                        t.event_id,
                        t.text,
                        t.created_at,
                        pr.id,
                        pr.pipeline_config,
                        pr.status,
                        pr.stopped_at,
                        pr.final_lat,
                        pr.final_lon,
                        pr.raw_json,
                        pr.created_at

                    ORDER BY t.created_at DESC
                """)

                rows = cur.fetchall()
                return [
                    {
                        "id": row["tweet_id"],
                        "eventId": str(row["event_id"]) if row["event_id"] else None,
                        "text": row["text"],

                        "runId": str(row["run_id"]) if row["run_id"] else None,

                        "status": row["run_status"],
                        "config": row["pipeline_config"],

                        "time": row["tweet_created_at"].strftime("%H:%M"),
                        "stoppedAt": row["stopped_at"],

                        "trace": row["trace"] or [],
                        "rawJson": row["raw_json"] or {},

                        "createdAt": row["tweet_created_at"].isoformat(),
                    }
                    for row in rows 
                ]

    

    def annotate_step(self, pipeline_step_id: str, label: str, annotated_by: str = "mathias"):
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO step_annotations (
                        pipeline_step_id,
                        label,
                        annotated_by,
                        annotated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        NOW()
                    )
                    ON CONFLICT (pipeline_step_id, annotated_by)
                    DO UPDATE SET
                        label = EXCLUDED.label,
                        annotated_at = NOW()
                    RETURNING
                        id,
                        pipeline_step_id,
                        label,
                        annotated_by,
                        notes,
                        annotated_at
                """, (
                    pipeline_step_id,
                    label,
                    annotated_by,
                ))

                row = cur.fetchone()

                return {
                    "id": str(row["id"]),
                    "pipelineStepId": str(row["pipeline_step_id"]),
                    "label": row["label"],
                    "annotatedBy": row["annotated_by"],
                    "notes": row["notes"],
                    "annotatedAt": row["annotated_at"].isoformat(),
                }