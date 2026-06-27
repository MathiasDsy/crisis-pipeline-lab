import requests
from src.components.base import BaseComponent, ComponentOutput
from src.config import GEOCODE_API_URL

MODEL_SERVER_URL = "http://model-server:8001"


class RelevanceClassifierComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")

        print(f"[relevance_classifier] text='{text[:80]}...' " if len(text) > 80 else f"[relevance_classifier] text='{text}'")

        try:
            response = requests.post(
                f"{MODEL_SERVER_URL}/predict",
                json={"text": text},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            is_relevant = data.get("is_relevant", False)
            print(f"[relevance_classifier] → label={data.get('label')} is_relevant={is_relevant} confidence={data.get('confidence'):.3f}")

            return ComponentOutput(
                result={
                    "is_relevant": is_relevant,
                    "label": data.get("label"),
                    "confidence": data.get("confidence"),
                    "model_key": data.get("model_key"),
                },
                passed=is_relevant,
            )

        except Exception as exc:
            print(f"[relevance_classifier] ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "is_relevant": False},
                passed=False,
            )


class LocationExtractorComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")
        threshold = params.get("threshold", 0.5)
        labels = params.get("labels", ["location", "city", "region", "country"])

        print(f"[location_extractor] text='{text[:80]}...' threshold={threshold}" if len(text) > 80 else f"[location_extractor] text='{text}' threshold={threshold}")

        try:
            response = requests.post(
                f"{MODEL_SERVER_URL}/extract-locations",
                json={"text": text, "labels": labels, "threshold": threshold},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            entities = data.get("entities", [])
            location_names = [e["text"] for e in entities]

            print(f"[location_extractor] → {len(location_names)} location(s) found: {location_names}")

            return ComponentOutput(
                result={
                    "locations": location_names,
                    "entities": entities,
                    "model_key": data.get("model_key"),
                },
                passed=len(location_names) > 0,
            )

        except Exception as exc:
            print(f"[location_extractor] ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "locations": [], "entities": []},
                passed=False,
            )


class GeocoderComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        locations = inputs.get("locations", [])

        # Si le step précédent a passé son output complet au lieu de la liste
        if isinstance(locations, dict):
            locations = locations.get("locations", [])

        print(f"[geocoder] received locations={locations}")

        if not locations or not isinstance(locations, list):
            print(f"[geocoder] → no locations to geocode, blocking")
            return ComponentOutput(result={"lat": None, "lon": None}, passed=False)

        location_name = locations[0]
        print(f"[geocoder] querying Photon for '{location_name}'")

        try:
            response = requests.get(
                GEOCODE_API_URL,
                params={"q": location_name, "limit": 1},
                timeout=5,
            )
            response.raise_for_status()
            features = response.json().get("features", [])

            if not features:
                print(f"[geocoder] → no result from Photon for '{location_name}'")
                return ComponentOutput(result={"lat": None, "lon": None}, passed=False)

            feature = features[0]
            lon, lat = feature["geometry"]["coordinates"]
            display_name = feature.get("properties", {}).get("name")
            print(f"[geocoder] → lat={lat} lon={lon} name='{display_name}'")

            return ComponentOutput(
                result={"lat": lat, "lon": lon, "display_name": display_name},
                passed=True,
            )

        except Exception as exc:
            print(f"[geocoder] ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "lat": None, "lon": None},
                passed=False,
            )


class EventMatcherComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        geocoding = inputs.get("geocoding", {})
        lat = inputs.get("lat") or (geocoding.get("lat") if isinstance(geocoding, dict) else None)
        lon = inputs.get("lon") or (geocoding.get("lon") if isinstance(geocoding, dict) else None)
        run_id = context.get("run_id")
        tweet_text = context.get("tweet", {}).get("content", "")
        radius_km = params.get("radius_km", 5.0)

        print(f"[event_matcher] lat={lat} lon={lon} radius_km={radius_km}")

        if lat is None or lon is None:
            print(f"[event_matcher] → no coordinates, skipping")
            return ComponentOutput(result={"event_created": False, "event_id": None}, passed=True)

        from src.repositories.event_repository import (
            list_active_events_by_run_id,
            create_event,
            increment_event_tweet_count,
        )

        active_events = list_active_events_by_run_id(run_id)

        for event in active_events:
            dist = _haversine(lat, lon, event["center_lat"], event["center_lon"])
            print(f"[event_matcher] distance to event {event['id']}: {dist:.2f} km")
            if dist <= radius_km:
                increment_event_tweet_count(event["id"], tweet_text)
                print(f"[event_matcher] → matched existing event {event['id']}")
                return ComponentOutput(
                    result={"event_created": False, "event_id": str(event["id"])},
                    passed=True,
                )

        new_event = create_event(run_id=run_id, lat=lat, lon=lon, tweet_text=tweet_text)
        print(f"[event_matcher] → created new event {new_event['id']}")
        return ComponentOutput(
            result={"event_created": True, "event_id": str(new_event["id"])},
            passed=True,
        )


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))
