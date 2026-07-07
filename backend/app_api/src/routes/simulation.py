from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from src.repositories.run_repository import cancel_run, get_run_by_id
from src.repositories.tweet_repository import list_tweets_by_run_id
from src.repositories.event_repository import list_events_by_run_id
from src.repositories.pipeline_step_repository import list_step_executions_by_run_id

from src.services.simulation_service import execute_run, request_cancel, start_simulation_service
from src.services.metrics_service import compute_run_metrics


router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
)


class StartSimulationRequest(BaseModel):
    dataset_id: str
    pipeline_config_id: str
    force_rerun: bool = False


@router.post("/start")
def start_simulation(request: StartSimulationRequest):
    """
    Start and run a simulation synchronously: loads the models, then executes the
    pipeline over the whole dataset before returning. Live progress streaming is
    deferred to v2. Returns the cached run untouched when one already exists.
    """
    result = start_simulation_service(
        dataset_id=request.dataset_id,
        pipeline_config_id=request.pipeline_config_id,
        force_rerun=request.force_rerun,
    )

    if result.get("cached"):
        return result

    summary = execute_run(result["run_id"])

    return {
        "run_id": result["run_id"],
        "run": result["run"],
        **summary,
    }


@router.get("/{run_id}")
def get_simulation(run_id: str):
    run = get_run_by_id(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )

    return {
        "run_id": run_id,
        "simulation": run,
    }

@router.get("/{run_id}/results")
def get_simulation_results(run_id: str):
    run = get_run_by_id(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )

    tweets = list_tweets_by_run_id(
        run_id=run_id,
        limit=1000,
        offset=0,
    )

    events = list_events_by_run_id(
        run_id=run_id,
        limit=1000,
        offset=0,
    )

    trace = list_step_executions_by_run_id(
        run_id=run_id,
        limit=5000,
        offset=0,
    )

    return {
        "run_id": run_id,
        "tweets": tweets,
        "events": events,
        "trace": trace,
    }


@router.get("/{run_id}/metrics")
def get_simulation_metrics(run_id: str):
    run = get_run_by_id(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )

    return compute_run_metrics(run_id)


@router.post("/{run_id}/cancel")
def cancel_simulation(run_id: str):
    # Signal au thread background s'il tourne encore en mémoire
    request_cancel(run_id)

    # Mise à jour BDD (idempotent si le thread l'a déjà fait)
    run = cancel_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=400,
            detail="Run is not running or does not exist",
        )

    return {
        "run_id": run_id,
        "status": "cancelled",
    }