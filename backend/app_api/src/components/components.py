import requests
from src.components.base import BaseComponent, ComponentOutput

MODEL_SERVER_URL = "http://model-server:8001"


class RelevanceClassifierComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")

        try:
            response = requests.post(
                f"{MODEL_SERVER_URL}/predict",
                json={"text": text},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            is_relevant = data.get("is_relevant", False)

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
            return ComponentOutput(
                result={"error": str(exc), "is_relevant": False},
                passed=False,
            )


class LocationExtractorComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        text = inputs.get("text", "")
        threshold = params.get("threshold", 0.5)
        labels = params.get("labels", ["location", "city", "region", "country"])

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

            return ComponentOutput(
                result={
                    "locations": location_names,
                    "entities": entities,
                    "model_key": data.get("model_key"),
                },
                passed=len(location_names) > 0,
            )

        except Exception as exc:
            return ComponentOutput(
                result={"error": str(exc), "locations": [], "entities": []},
                passed=False,
            )


class GeocoderComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        locations = inputs.get("locations", [])

        if not locations:
            return ComponentOutput(result={"lat": None, "lon": None}, passed=False)

        location_name = locations[0]

        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": location_name, "format": "json", "limit": 1},
                headers={"User-Agent": "crisis-detection-simulator/1.0"},
                timeout=5,
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                return ComponentOutput(result={"lat": None, "lon": None}, passed=False)

            return ComponentOutput(
                result={
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "display_name": results[0].get("display_name"),
                },
                passed=True,
            )

        except Exception as exc:
            return ComponentOutput(
                result={"error": str(exc), "lat": None, "lon": None},
                passed=False,
            )


class EventMatcherComponent(BaseComponent):
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        return ComponentOutput(
            result={"event_created": False, "event_id": None},
            passed=True,
        )
