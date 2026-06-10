# src/modules/pipeline_lab/routes.py
from pydantic import BaseModel
from typing import Literal
from fastapi import APIRouter

from src.modules.pipeline_lab.repositories.events_repository import EventsRepository
from src.modules.pipeline_lab.repositories.tweets_repository import TweetsRepository
from src.pipeline.loader import load_pipeline_from_yaml
from src.pipeline.runner import PipelineRunner


router = APIRouter()

events_repository = EventsRepository()
tweets_repository = TweetsRepository()

pipeline_runner = load_pipeline_from_yaml("src/pipeline/configs/fire_pipeline_v1.yaml")


class StepAnnotationRequest(BaseModel):
    pipelineStepId: str
    label: Literal["correct", "incorrect", "uncertain"]


@router.get("/events")
def get_all_events():
    return events_repository.get_all_events()


@router.get("/events/{event_id}")
def get_event(event_id: str):
    return events_repository.get_event(event_id)


@router.post("/events/test")
def create_test_event():
    return events_repository.create_test_event()


@router.get("/fetch_all_tweets")
def fetch_all_tweets():
    return tweets_repository.get_all_tweets()


@router.post("/pipeline-steps/annotate")
def annotate_pipeline_step(payload: StepAnnotationRequest):
    return tweets_repository.annotate_step(
        pipeline_step_id=payload.pipelineStepId,
        label=payload.label,
        annotated_by="mathias",
    )

@router.post("/pipeline-run")
def run_pipeline_on_tweet(tweet: dict):
    print(f"[API] Received tweet {tweet['id']} for processing")
    print(f"[API] Tweet content: {tweet['text']}")
    pipeline_runner.run(tweet["text"])