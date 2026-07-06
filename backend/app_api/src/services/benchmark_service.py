import threading
from itertools import product

import pandas as pd
from fastapi import HTTPException

import src.logger as logger
from src.pipeline.pipeline_runner import PipelineRunner
from src.repositories.dataset_repository import get_dataset_by_id
from src.repositories.model_repository import get_model_by_key
from src.repositories.run_repository import create_pipeline_run, complete_pipeline_run
from src.repositories.tweet_repository import create_tweet
from src.repositories.benchmark_repository import (
    create_benchmark,
    increment_completed_runs,
    update_benchmark_status,
)
from src.services.simulation_service import (
    build_fixed_pipeline_config,
    ensure_models_loaded,
    ensure_no_active_run,
    finalize_run_metrics,
)

# benchmark_id -> threading.Event : set() pour annuler le benchmark en cours
_cancel_signals: dict[str, threading.Event] = {}


def request_cancel_benchmark(benchmark_id: str) -> bool:
    event = _cancel_signals.get(benchmark_id)
    if event is None:
        return False
    event.set()
    return True


def start_benchmark_service(
    dataset_id: str,
    classifier_model_keys: list[str],
    location_model_keys: list[str],
    name: str | None = None,
) -> dict:
    """Validation synchrone + création du benchmark. Retourne immédiatement l'id."""
    if not classifier_model_keys or not location_model_keys:
        raise HTTPException(status_code=400, detail="Provide at least one classifier and one location model")

    dataset = get_dataset_by_id(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    if not dataset["is_valid"]:
        raise HTTPException(status_code=400, detail="Dataset is not valid")

    # Vérifie que tous les modèles existent dans le registry
    for key in set(classifier_model_keys) | set(location_model_keys):
        if get_model_by_key(key) is None:
            raise HTTPException(status_code=404, detail=f"Model '{key}' not found in registry")

    # Verrou : pas de benchmark si un run/benchmark tourne déjà (model-server mono-état)
    ensure_no_active_run()

    df = pd.read_csv(dataset["path"])
    if "content" not in df.columns:
        raise HTTPException(status_code=400, detail="Dataset CSV must contain a 'content' column")

    combos = list(product(classifier_model_keys, location_model_keys))

    benchmark = create_benchmark(
        name=name,
        dataset_id=dataset_id,
        classifier_model_keys=classifier_model_keys,
        location_model_keys=location_model_keys,
        total_runs=len(combos),
    )

    return {
        "status": "started",
        "benchmark_id": benchmark["id"],
        "total_runs": len(combos),
        "benchmark": benchmark,
        "_internal": {"df": df, "combos": combos, "dataset_id": dataset_id},
    }


def run_benchmark_background(
    benchmark_id: str,
    df: pd.DataFrame,
    combos: list[tuple[str, str]],
    dataset_id: str,
) -> None:
    """Exécute chaque combinaison (classifier × location) en séquence."""
    cancel_event = threading.Event()
    _cancel_signals[benchmark_id] = cancel_event

    # Ordonne par classifier pour minimiser les rechargements du gros modèle
    combos = sorted(combos, key=lambda c: c[0])

    logger.info(
        f"Benchmark started — {len(combos)} combination(s)",
        context="benchmark",
        details={"benchmark_id": benchmark_id, "total_runs": len(combos)},
    )

    try:
        for classifier_key, location_key in combos:
            if cancel_event.is_set():
                logger.warning("Benchmark cancelled by user", context="benchmark", details={"benchmark_id": benchmark_id})
                update_benchmark_status(benchmark_id, "cancelled")
                return

            _run_single_combo(benchmark_id, dataset_id, df, classifier_key, location_key)
            increment_completed_runs(benchmark_id)

        update_benchmark_status(benchmark_id, "completed")
        logger.info("Benchmark completed", context="benchmark", details={"benchmark_id": benchmark_id})

    except Exception as exc:
        logger.error(f"Benchmark crashed: {exc}", context="benchmark", exc=exc, details={"benchmark_id": benchmark_id})
        update_benchmark_status(benchmark_id, "error")

    finally:
        _cancel_signals.pop(benchmark_id, None)


def _run_single_combo(
    benchmark_id: str,
    dataset_id: str,
    df: pd.DataFrame,
    classifier_key: str,
    location_key: str,
) -> None:
    snapshot = {"classifier_model_key": classifier_key, "location_model_key": location_key}

    run = create_pipeline_run(
        dataset_id=dataset_id,
        pipeline_config_id=None,
        mode="benchmark",
        status="running",
        model_snapshot=snapshot,
        benchmark_id=benchmark_id,
    )
    run_id = run["id"]

    logger.info(
        f"Benchmark run: classifier={classifier_key} location={location_key}",
        context="benchmark",
        run_id=run_id,
        details=snapshot,
    )

    try:
        ensure_models_loaded(classifier_key, location_key)

        config = build_fixed_pipeline_config(classifier_key, location_key)
        runner = PipelineRunner(pipeline_config=config)

        for _, row in df.iterrows():
            content = str(row["content"]).strip()
            if not content:
                continue

            raw_label = row.get("label")
            label: bool | None = None
            if raw_label is not None and str(raw_label).strip() != "":
                label = str(raw_label).strip().lower() in ("1", "true", "yes", "on-topic")

            tweet = create_tweet(content=content, run_id=run_id, source="dataset", label=label)
            runner.run_tweet(tweet_id=tweet["id"], run_id=run_id, text=tweet["content"])

        complete_pipeline_run(run_id=run_id, status="completed")
        finalize_run_metrics(run_id)

    except Exception as exc:
        logger.error(f"Benchmark run crashed: {exc}", context="benchmark", run_id=run_id, exc=exc)
        complete_pipeline_run(run_id=run_id, status="error")
