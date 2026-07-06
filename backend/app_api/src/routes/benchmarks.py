from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.repositories.benchmark_repository import (
    get_benchmark_by_id,
    list_benchmarks as list_benchmarks_from_db,
    update_benchmark_status,
)
from src.repositories.run_metrics_repository import list_benchmark_leaderboard, list_benchmark_runs
from src.services.benchmark_service import (
    request_cancel_benchmark,
    run_benchmark_background,
    start_benchmark_service,
)

router = APIRouter(
    prefix="/benchmarks",
    tags=["benchmarks"],
)


class StartBenchmarkRequest(BaseModel):
    dataset_id: str
    classifier_model_keys: list[str]
    location_model_keys: list[str]
    name: str | None = None


@router.post("/start")
def start_benchmark(request: StartBenchmarkRequest, background_tasks: BackgroundTasks):
    result = start_benchmark_service(
        dataset_id=request.dataset_id,
        classifier_model_keys=request.classifier_model_keys,
        location_model_keys=request.location_model_keys,
        name=request.name,
    )

    internal = result.pop("_internal")
    background_tasks.add_task(
        run_benchmark_background,
        benchmark_id=result["benchmark_id"],
        df=internal["df"],
        combos=internal["combos"],
        dataset_id=internal["dataset_id"],
    )

    return result


@router.get("")
def list_benchmarks():
    benchmarks = list_benchmarks_from_db()
    return {"benchmarks": benchmarks, "count": len(benchmarks)}


@router.get("/{benchmark_id}")
def get_benchmark(benchmark_id: str):
    benchmark = get_benchmark_by_id(benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found")
    return benchmark


@router.get("/{benchmark_id}/runs")
def get_benchmark_runs(benchmark_id: str):
    benchmark = get_benchmark_by_id(benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found")

    runs = list_benchmark_runs(benchmark_id)

    return {
        "benchmark_id": benchmark_id,
        "status": benchmark["status"],
        "total_runs": benchmark["total_runs"],
        "completed_runs": benchmark["completed_runs"],
        "count": len(runs),
        "runs": runs,
    }


@router.get("/{benchmark_id}/leaderboard")
def get_benchmark_leaderboard(benchmark_id: str):
    benchmark = get_benchmark_by_id(benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found")

    leaderboard = list_benchmark_leaderboard(benchmark_id)

    return {
        "benchmark_id": benchmark_id,
        "status": benchmark["status"],
        "total_runs": benchmark["total_runs"],
        "completed_runs": benchmark["completed_runs"],
        "leaderboard": leaderboard,
    }


@router.post("/{benchmark_id}/cancel")
def cancel_benchmark(benchmark_id: str):
    benchmark = get_benchmark_by_id(benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found")

    request_cancel_benchmark(benchmark_id)
    update_benchmark_status(benchmark_id, "cancelled")

    return {"benchmark_id": benchmark_id, "status": "cancelled"}
