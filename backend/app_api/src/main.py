from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.admin import router as admin_router
from src.routes.datasets import router as datasets_router
from src.routes.events import router as events_router
from src.routes.models import router as models_router
from src.routes.pipelines import router as pipelines_router
from src.routes.runs import router as runs_router
from src.routes.simulation import router as simulation_router
from src.routes.tweets import router as tweet_router

import src.logger as logger


def _run_discovery() -> None:
    from src.services.dataset_discovery import discover_datasets
    from src.services.model_discovery import discover_models_from_storage
    from src.repositories.dataset_repository import upsert_dataset
    from src.repositories.model_repository import upsert_model

    try:
        datasets = discover_datasets()
        for d in datasets:
            upsert_dataset(d)
        logger.info(f"Dataset discovery: {len(datasets)} dataset(s) found", context="startup")
    except Exception as exc:
        logger.error("Dataset discovery failed", context="startup", exc=exc)

    try:
        discovered = discover_models_from_storage()
        valid = [m for m in discovered if m.get("is_valid")]
        for m in valid:
            m_to_save = m.copy()
            m_to_save.pop("is_valid", None)
            upsert_model(m_to_save)
        logger.info(f"Model discovery: {len(valid)}/{len(discovered)} model(s) valid", context="startup")
    except Exception as exc:
        logger.error("Model discovery failed", context="startup", exc=exc)

    try:
        from pathlib import Path
        from src.services.pipeline_import_service import build_pipeline_record
        from src.repositories.pipeline_repository import upsert_pipeline_config

        pipelines_dir = Path("/app/storage/pipelines")
        yaml_files = list(pipelines_dir.glob("*.yaml")) + list(pipelines_dir.glob("*.yml")) if pipelines_dir.exists() else []
        count = 0
        for yaml_path in yaml_files:
            try:
                content = yaml_path.read_bytes()
                from src.services.pipeline_import_service import parse_pipeline_file
                config = parse_pipeline_file(content)
                record = build_pipeline_record(config=config, filename=yaml_path.name)
                upsert_pipeline_config(record)
                count += 1
            except Exception as exc:
                logger.error(f"Failed to import pipeline '{yaml_path.name}'", context="startup", exc=exc)
        logger.info(f"Pipeline discovery: {count}/{len(yaml_files)} pipeline(s) imported", context="startup")
    except Exception as exc:
        logger.error("Pipeline discovery failed", context="startup", exc=exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting up — running discovery", context="startup")
    _run_discovery()
    yield
    logger.info("API shutting down", context="startup")


app = FastAPI(
    title="Crisis Geolocation API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(datasets_router)
app.include_router(events_router)
app.include_router(models_router)
app.include_router(pipelines_router)
app.include_router(runs_router)
app.include_router(simulation_router)
app.include_router(tweet_router)
