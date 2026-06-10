from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class Tweet:
    id: str
    text: str
    created_at: Optional[str] = None


@dataclass
class LocationMention:
    name: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: float = 1.0


@dataclass
class GeoPoint:
    name: str
    lat: float
    lon: float
    confidence: float = 1.0


@dataclass
class Event:
    id: str
    location: tuple[float, float]  # (lat, lon)
    tweet_ids: list[str]
    radius_km: float = 20.0


@dataclass
class ProcessResult:
    status: Literal["ignored", "uncertain", "assigned", "created"]
    tweet_id: str
    reason: str
    event_id: Optional[str] = None
    location: Optional[GeoPoint] = None