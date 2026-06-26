import pandas as pd
import requests
from fastapi import HTTPException

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

def start_simulation_service(
    dataset_id: str,
    pipeline_config_id: str,
    force_rerun: bool = False,
) -> dict:
    dataset = get_dataset_by_id(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found",
        )

    if not dataset["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Dataset is not valid",
                "validation_errors": dataset.get("validation_errors"),
            },
        )

    pipeline = get_pipeline_config_by_id(pipeline_config_id)

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline config '{pipeline_config_id}' not found",
        )

    if not pipeline["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Pipeline config is not valid",
                "validation_errors": pipeline.get("validation_errors"),
            },
        )


    # Check si ce sont les bons modèles loaded
    load_models(pipeline)

    if not force_rerun:
        cached_run = find_completed_simulation_run(
            dataset_id=dataset_id,
            pipeline_config_id=pipeline_config_id,
        )

        if cached_run is not None:
            return {
                "status": "cached",
                "cached": True,
                "run_id": cached_run["id"],
                "run": cached_run,
            }

    run = create_pipeline_run(
        dataset_id=dataset_id,
        pipeline_config_id=pipeline_config_id,
        mode="simulation",
        status="running",
    )

    df = pd.read_csv(dataset["path"])

    if "content" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="Dataset CSV must contain a 'content' column",
        )

    runner = PipelineRunner(pipeline_config=pipeline["config_json"])

    created_tweets = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing tweets"):
        content = str(row["content"]).strip()

        if not content:
            continue

        raw_label = row.get("label")
        label: bool | None = None
        if raw_label is not None and str(raw_label).strip() != "":
            label = str(raw_label).strip().lower() in ("1", "true", "yes", "on-topic")

        tweet = create_tweet(
            content=content,
            run_id=run["id"],
            source="dataset",
            label=label,
        )

        runner.run_tweet(
            tweet_id=tweet["id"],
            run_id=run["id"],
            text=tweet["content"],
        )   

        created_tweets += 1

    completed_run = complete_pipeline_run(
        run_id=run["id"],
        status="completed",
    )

    return {
        "status": "completed",
        "cached": False,
        "dataset_id": dataset_id,
        "pipeline_config_id": pipeline_config_id,
        "run_id": run["id"],
        "tweets_created": created_tweets,
        "run": completed_run,
    }

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
        if step.get("component_key") == "relevance_classifier":
            
            if model_key != classifier_data.get("model_key"):

                print("Model not loaded, loading of the classifier model")

                model_data = get_model_by_key(model_key)
                local_path = model_data["local_path"]
                model_loader = model_data["metadata_json"]["loader"]

                res = load_classifier_model(model_key, local_path, model_loader)
                
                print("Model Classifier Loaded")

        elif step.get("component_key") == "location_extractor":

            if model_key != location_data.get("model_key"):
                print("Model not loaded, loading the location model")
                model_data = get_model_by_key(model_key)
                local_path = model_data["local_path"]
                model_loader = model_data["metadata_json"]["loader"]

                res = load_location_model(model_key, local_path, model_loader)
                print("Model Location Loaded")