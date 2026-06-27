from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.repositories.tweet_repository import get_tweet_by_id, list_tweets_by_run_id, count_tweets_by_run_id
from src.repositories.pipeline_step_repository import get_step_execution_from_tweet_id

router = APIRouter(
    prefix="/tweets",
    tags=["tweets"],
)


class CreateTweetAnnotationRequest(BaseModel):
    expected_is_signal: bool
    expected_lat: float | None = None
    expected_lon: float | None = None
    expected_location: str | None = None
    comment: str | None = None


@router.get("")
def list_tweets(
    run_id: str | None = None,
    event_id: str | None = None,
    source: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    if run_id is not None:
        tweets = list_tweets_by_run_id(run_id, limit=limit, offset=offset)
        total = count_tweets_by_run_id(run_id)
    else:
        tweets = []
        total = 0

    return {
        "tweets": tweets,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "run_id": run_id,
            "event_id": event_id,
            "source": source,
        },
    }


@router.get("/{tweet_id}")
def get_tweet(tweet_id: str):
    tweet = get_tweet_by_id(tweet_id)

    if tweet is None:
        raise HTTPException(status_code=404, detail=f"Tweet '{tweet_id}' not found")

    return {
        "tweet_id": tweet_id,
        "tweet": tweet.get("content"),
        "event_id": tweet.get("event_id"),
        "run_id": tweet.get("run_id"),
        "source": tweet.get("source"),
        "created_at": tweet.get("created_at")
    }


@router.get("/{tweet_id}/trace")
def get_tweet_trace(tweet_id: str):

    d = get_step_execution_from_tweet_id(tweet_id)
    return d


@router.post("/{tweet_id}/annotations")
def create_tweet_annotation(
    tweet_id: str,
    request: CreateTweetAnnotationRequest,
):
    return {
        "tweet_id": tweet_id,
        "status": "annotation_created",
        "annotation": request.model_dump(),
    }


@router.get("/{tweet_id}/annotations")
def list_tweet_annotations(tweet_id: str):
    return {
        "tweet_id": tweet_id,
        "annotations": [],
    }