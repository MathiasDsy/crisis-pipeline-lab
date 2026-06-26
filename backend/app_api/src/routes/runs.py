from fastapi import APIRouter, HTTPException
from src.repositories.tweet_repository import count_tweets_by_run_id, list_tweets_by_run_id

from src.repositories.run_repository import (
    list_runs as list_runs_from_db,
    get_run_by_id,
    count_run_events,
    count_run_steps,
    count_run_errors,
)
from src.repositories.tweet_repository import (
    list_tweets_by_run_id,
    count_tweets_by_run_id,
)
from src.repositories.event_repository import list_events_by_run_id
from src.repositories.pipeline_step_repository import (
    list_step_executions_by_run_id,
    count_step_executions_by_run_id,
)

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)


@router.get("")
def list_runs(
    mode: str | None = None,
    status: str | None = None,
):
    runs = list_runs_from_db(mode=mode, status=status)

    return {
        "runs": runs,
        "count": len(runs),
        "filters": {
            "mode": mode,
            "status": status,
        },
    }

@router.get("/{run_id}")
def get_run(run_id: str):
    run = get_run_by_id(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )

    return run


@router.get("/{run_id}/events")
def get_run_events(
    run_id: str,
    limit: int = 100,
    offset: int = 0,
):
    if get_run_by_id(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    events = list_events_by_run_id(run_id, limit, offset)

    return {
        "run_id": run_id,
        "limit": limit,
        "offset": offset,
        "events": events,
    }

@router.get("/{run_id}/trace")
def get_run_trace(
    run_id: str,
    limit: int = 500,
    offset: int = 0,
):
    if get_run_by_id(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    trace = list_step_executions_by_run_id(run_id, limit, offset)
    total = count_step_executions_by_run_id(run_id)

    return {
        "run_id": run_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "trace": trace,
    }

@router.get("/{run_id}/summary")
def get_run_summary(run_id: str):
    run = get_run_by_id(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )

    tweets_count = count_tweets_by_run_id(run_id)
    events_count = count_run_events(run_id)
    steps_count = count_run_steps(run_id)
    errors_count = count_run_errors(run_id)

    return {
        "run_id": run_id,
        "mode": run["mode"],
        "status": run["status"],
        "tweets_processed": tweets_count,
        "events_created": events_count,
        "steps_executed": steps_count,
        "errors": errors_count,
        "started_at": run["started_at"],
        "finished_at": run["finished_at"],
    }

@router.get("/{run_id}/tweets")
def get_run_tweets(
    run_id: str,
    limit: int = 100,
    offset: int = 0,
):
    if get_run_by_id(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    tweets = list_tweets_by_run_id(run_id, limit, offset)
    total = count_tweets_by_run_id(run_id)

    return {
        "run_id": run_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "tweets": tweets,
    }