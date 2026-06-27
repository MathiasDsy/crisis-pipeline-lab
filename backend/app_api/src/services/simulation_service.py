import threading
import pandas as pd
import requests
from fastapi import HTTPException
import src.logger as logger

from src.repositories.dataset_repository import get_dataset_by_id
from src.repositories.pipeline_repository import get_pipeline_config_by_id
from src.repositories.run_repository import (
    complete_pipeline_run,
    create_pipeline_run,
    find_completed_simulation_run,
)
from src.repositories.tweet_repository import create_tweet
from src.repositories.model_repository import get_model_by_key

from tqdm import tqdm

from src.pipeline.pipeline_runner import PipelineRunner
from src.components.registry import COMPONENT_REGISTRY
from src.clients.model_server_client import get_models_loaded, load_classifier_model, load_location_model

# run_id -> threading.Event : set() pour annuler le run en cours
_cancel_signals: dict[str, threading.Event] = {}


def request_cancel(run_id: str) -> bool:
    """Signal d'annulation pour un run en cours. Retourne False si le run n'est pas actif."""
    event = _cancel_signals.get(run_id)
    if event is None:
        return False
    event.set()
    return True


def start_simulation_service(
    dataset_id: str,
    pipeline_config_id: str,
    force_rerun: bool = False,
) -> dict:
    """Validation synchrone + création du run. Retourne immédiatement le run_id."""
    dataset = get_dataset_by_id(dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    if not dataset["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Dataset is not valid", "validation_errors": dataset.get("validation_errors")},
        )

    pipeline = get_pipeline_config_by_id(pipeline_config_id)

    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline config '{pipeline_config_id}' not found")

    if not pipeline["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Pipeline config is not valid", "validation_errors": pipeline.get("validation_errors")},
        )

    load_models(pipeline)

    if not force_rerun:
        cached_run = find_completed_simulation_run(dataset_id=dataset_id, pipeline_config_id=pipeline_config_id)
        if cached_run is not None:
            return {"status": "cached", "cached": True, "run_id": cached_run["id"], "run": cached_run}

    df = pd.read_csv(dataset["path"])

    if "content" not in df.columns:
        raise HTTPException(status_code=400, detail="Dataset CSV must contain a 'content' column")

    run = create_pipeline_run(
        dataset_id=dataset_id,
        pipeline_config_id=pipeline_config_id,
        mode="simulation",
        status="running",
    )

    return {
        "status": "started",
        "cached": False,
        "run_id": run["id"],
        "run": run,
        "_internal": {"df": df, "pipeline": pipeline, "run": run},
    }


def run_simulation_background(run_id: str, df: pd.DataFrame, pipeline: dict) -> None:
    """Exécution du pipeline tweet par tweet. Appelé dans un thread background."""
    cancel_event = threading.Event()
    _cancel_signals[run_id] = cancel_event

    runner = PipelineRunner(pipeline_config=pipeline["config_json"])
    created_tweets = 0
    total = len(df)

    logger.info(f"Simulation started — {total} rows to process", context="simulation", run_id=run_id, details={"total_rows": total})

    try:
        for _, row in df.iterrows():
            if cancel_event.is_set():
                logger.warning("Simulation cancelled by user", context="simulation", run_id=run_id, details={"tweets_processed": created_tweets})
                complete_pipeline_run(run_id=run_id, status="cancelled")
                return

            content = str(row["content"]).strip()
            if not content:
                continue

            raw_label = row.get("label")
            label: bool | None = None
            if raw_label is not None and str(raw_label).strip() != "":
                label = str(raw_label).strip().lower() in ("1", "true", "yes", "on-topic")

            tweet = create_tweet(content=content, run_id=run_id, source="dataset", label=label)
            runner.run_tweet(tweet_id=tweet["id"], run_id=run_id, text=tweet["content"])
            created_tweets += 1

        logger.info(f"Simulation completed — {created_tweets}/{total} tweets processed", context="simulation", run_id=run_id, details={"tweets_processed": created_tweets, "total_rows": total})
        complete_pipeline_run(run_id=run_id, status="completed")

    except Exception as exc:
        logger.error(f"Simulation crashed: {exc}", context="simulation", run_id=run_id, exc=exc, details={"tweets_processed": created_tweets})
        complete_pipeline_run(run_id=run_id, status="error")

    finally:
        _cancel_signals.pop(run_id, None)

def load_models(pipeline: dict):
    steps = pipeline.get("config_json", None)["steps"]

    if steps is None: 
            raise HTTPException(
            status_code=404,
            detail=f"Pipeline config has no [config_json][steps] attributes, can't fetch the models details",
        )

    data_models = get_models_loaded()


    classifier_data = data_models.get("classifier")
    location_data = data_models.get("gliner")

    for step in steps:
        model_key = step.get("model_key")
        component_key = step.get("component_key")

        if component_key == "relevance_classifier":
            if not model_key:
                print(f"[load_models] step '{step.get('id')}' has no model_key, using currently loaded classifier")
                continue
            if model_key != classifier_data.get("model_key"):
                print(f"[load_models] loading classifier model '{model_key}'")
                model_data = get_model_by_key(model_key)
                if model_data is None:
                    raise HTTPException(status_code=404, detail=f"Model '{model_key}' not found in registry")
                load_classifier_model(model_key, model_data["local_path"], model_data["metadata_json"]["loader"])
                print(f"[load_models] classifier '{model_key}' loaded")

        elif component_key == "location_extractor":
            if not model_key:
                print(f"[load_models] step '{step.get('id')}' has no model_key, using currently loaded location model")
                continue
            if model_key != location_data.get("model_key"):
                print(f"[load_models] loading location model '{model_key}'")
                model_data = get_model_by_key(model_key)
                if model_data is None:
                    raise HTTPException(status_code=404, detail=f"Model '{model_key}' not found in registry")
                load_location_model(model_key, model_data["local_path"], model_data["metadata_json"]["loader"])
                print(f"[load_models] location model '{model_key}' loaded")