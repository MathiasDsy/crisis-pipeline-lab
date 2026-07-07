import os
import time
import requests
from src.components.base import BaseComponent, ComponentOutput
from src.config import GEOCODE_API_URL, GEOCODING_ENABLED

MODEL_SERVER_URL = os.getenv("MODEL_API_URL", "http://model-server:8001")
MODEL_SERVER_TIMEOUT = float(os.getenv("MODEL_SERVER_TIMEOUT", "60"))
MODEL_SERVER_RETRIES = int(os.getenv("MODEL_SERVER_RETRIES", "2"))


def _post_model_server(path: str, payload: dict) -> dict:
    """
    POST vers le model-server avec timeout généreux + retries sur erreurs transitoires
    (timeout / connexion). Lève l'exception si tout échoue — l'appelant décide quoi en faire.
    Un modèle sur CPU peut être lent, surtout à la première inférence après un load (warmup).
    """
    last_exc: Exception | None = None
    for attempt in range(MODEL_SERVER_RETRIES + 1):
        try:
            response = requests.post(
                f"{MODEL_SERVER_URL}{path}",
                json=payload,
                timeout=MODEL_SERVER_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < MODEL_SERVER_RETRIES:
                wait = 1.0 * (attempt + 1)
                print(f"[model-server] {path} transient error (attempt {attempt + 1}): {exc} — retry in {wait}s")
                time.sleep(wait)
                continue
            raise
    raise last_exc  # pragma: no cover


class RelevanceClassifierComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")

        print(f"[relevance_classifier] text='{text[:80]}...' " if len(text) > 80 else f"[relevance_classifier] text='{text}'")

        try:
            data = _post_model_server("/predict", {"text": text})
        except Exception as exc:
            print(f"[relevance_classifier] TECHNICAL ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "is_relevant": None},
                passed=False,
                error=True,
            )

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


class LocationExtractorComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")
        threshold = params.get("threshold", 0.5)
        labels = params.get("labels", ["location", "city", "region", "country"])

        print(f"[location_extractor] text='{text[:80]}...' threshold={threshold}" if len(text) > 80 else f"[location_extractor] text='{text}' threshold={threshold}")

        try:
            data = _post_model_server(
                "/extract-locations",
                {"text": text, "labels": labels, "threshold": threshold},
            )
        except Exception as exc:
            print(f"[location_extractor] TECHNICAL ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "locations": [], "entities": []},
                passed=False,
                error=True,
            )

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


class GeocoderComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        # Geocoding disabled (e.g. Photon not in the running stack): skip cleanly
        # instead of failing. Treated as "no coordinates", not as an error.
        if not GEOCODING_ENABLED:
            print("[geocoder] geocoding disabled (GEOCODING_ENABLED=false) → skipping")
            return ComponentOutput(
                result={"lat": None, "lon": None, "skipped": True},
                passed=False,
            )

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
                timeout=float(os.getenv("GEOCODE_TIMEOUT", "15")),
            )
            response.raise_for_status()
            features = response.json().get("features", [])
        except Exception as exc:
            # Échec technique (Photon down / timeout) ≠ "pas de résultat"
            print(f"[geocoder] TECHNICAL ERROR: {exc}")
            return ComponentOutput(
                result={"error": str(exc), "lat": None, "lon": None},
                passed=False,
                error=True,
            )

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
