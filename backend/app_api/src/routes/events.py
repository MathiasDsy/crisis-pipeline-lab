from fastapi import APIRouter, HTTPException

from src.repositories.event_repository import (
    list_events as list_events_from_db,
    get_event_by_id,
    list_tweets_by_event_id,
    update_event_active_status,
)

router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.get("")
def list_events(
    run_id: str | None = None,
    active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
):
    events = list_events_from_db(
        run_id=run_id,
        active=active,
        limit=limit,
        offset=offset,
    )

    return {
        "events": events,
        "count": len(events),
        "filters": {
            "run_id": run_id,
            "active": active,
        },
        "limit": limit,
        "offset": offset,
    }


@router.get("/{event_id}")
def get_event(event_id: str):
    event = get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event '{event_id}' not found",
        )

    return event


@router.get("/{event_id}/tweets")
def get_event_tweets(
    event_id: str,
    limit: int = 100,
    offset: int = 0,
):
    event = get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event '{event_id}' not found",
        )

    tweets = list_tweets_by_event_id(
        event_id=event_id,
        limit=limit,
        offset=offset,
    )

    return {
        "event_id": event_id,
        "tweets": tweets,
        "count": len(tweets),
        "limit": limit,
        "offset": offset,
    }


@router.post("/{event_id}/close")
def close_event(event_id: str):
    event = update_event_active_status(
        event_id=event_id,
        is_active=False,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event '{event_id}' not found",
        )

    return {
        "event_id": event_id,
        "status": "closed",
        "event": event,
    }


@router.post("/{event_id}/reopen")
def reopen_event(event_id: str):
    event = update_event_active_status(
        event_id=event_id,
        is_active=True,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event '{event_id}' not found",
        )

    return {
        "event_id": event_id,
        "status": "active",
        "event": event,
    }