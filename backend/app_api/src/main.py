from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from src.modules.pipeline_lab.routes import router as pipeline_router

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

app.include_router(pipeline_router)