from typing import Any, Dict
import uuid
import json
from src.pipeline.base import PipelineComponent, StepOutput
from src.utils.geo import haversine_distance
from src.modules.pipeline_lab.repositories.events_repository import EventsRepository


def find_matching_event(point: tuple, events: list, max_distance_km: float) -> Dict[str, Any] | None:
    """
    Find the nearest event to the given point within max_distance_km.
    
    Args:
        point: Tuple of (lat, lon)
        events: List of event dictionaries
        max_distance_km: Maximum distance in kilometers
        
    Returns:
        The matching event or None if no match found
    """
    if not events:
        return None
    
    best_event = None
    best_distance = max_distance_km
    
    for event in events:
        event_point = (event["center_lat"], event["center_lon"])
        distance = haversine_distance(point, event_point)
        
        if distance < best_distance:
            best_distance = distance
            best_event = event
    
    print(f"[EventMatcher] Best distance: {best_distance:.2f} km for event ID: {best_event if best_event else 'None'}")
    return best_event


class EventMatcherComponent(PipelineComponent):
    def __init__(self, **params):
        super().__init__(**params)
        self.events_repo = EventsRepository()
        self.events = self.events_repo.get_all_events()

        print(f"[EventMatcherComponent] Loaded {len(self.events)} active events") 

    def run(
        self,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepOutput:

        # print(f"[EventMatcherComponent] Processing tweet: ")
        # print(json.dumps(inputs, indent=2))
        locations = inputs.get("locations", [])
        text = inputs.get("text", "")

        max_distance_km = params.get("max_distance_km", 5.0)
        create_if_no_match = params.get("create_if_no_match", True)

        lon = inputs['locations']['geocoded_location']['lon']
        lat = inputs['locations']['geocoded_location']['lat']
        geocoded_locations = {
            "lat": lat,
            "lon": lon
        }

        if not geocoded_locations:
            return StepOutput(
                passed=False,
                result={
                    "matched": False,
                    "eventId": None,
                    "mode": "no_geocoded_location",
                },
                metadata={},
            )

        best_location = geocoded_locations
        point = (best_location["lat"], best_location["lon"])
        matched_event = find_matching_event(
            point=point,
            events=self.events,
            max_distance_km=max_distance_km,
        )
        if matched_event:
            self.events_repo.add_tweet_to_event(
                event_id=matched_event["id"],
                tweet_id=context["tweet"]["id"],
                tweet_text=context["tweet"]["text"],
            )

            return StepOutput(
                passed=True,
                result={
                    "matched": True,
                    "eventId": str(matched_event["id"]),
                    "mode": "matched_existing",
                    "locationUsed": best_location,
                },
                metadata={
                    "max_distance_km": max_distance_km,
                },
            )

        if not create_if_no_match:
            return StepOutput(
                passed=False,
                result={
                    "matched": False,
                    "eventId": None,
                    "mode": "no_match",
                    "locationUsed": best_location,
                },
                metadata={},
            )

        print(json.dumps(context, indent=2))
        new_event = self.events_repo.create_event(
            lat=best_location["lat"],
            lon=best_location["lon"],
            source_text=text,
            tweet_id=context["tweet"]["id"],
        )

        self.events.append(new_event)

        return StepOutput(
            passed=True,
            result={
                "matched": True,
                "eventId": str(new_event["id"]),
                "mode": "created",
                "locationUsed": best_location,
            },
            metadata={
                "max_distance_km": max_distance_km,
            },
        )