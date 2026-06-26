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


app = FastAPI(
    title="Crisis Geolocation API"
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
