from src.clients.geocode_client import GeocodeClient
from src.pipeline.base import PipelineComponent, StepOutput
from typing import Any, Dict

_client = GeocodeClient()

class PhotonGeocoderComponent(PipelineComponent):
    def __init__(self, **params):
        super().__init__(**params)

    def run(
        self,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepOutput:
        print(f"[PhotonGeocoderComponent] Running with inputs: {inputs} and params: {params} and outputs : {context}")
        try:
            data = inputs.get("locations", [])
            geocoded = geocode_location(data["locations"][0])
            print(f"[PhotonGeocoderComponent] Geocoding result for '{data}': {geocoded}")
        except:
            print(f"[PhotonGeocoderComponent] No locations found in inputs: {inputs}")
            data = []
            geocoded = None
            return StepOutput(
                passed=False,
                result={
                    "geocoded_location": {"lon": geocoded[0], "lat": geocoded[1]} if geocoded else None,
                    "input_locations": data,
                },
                metadata={},
            )

        print(f"[PhotonGeocoderComponent] Geocoding result for '{data}': {geocoded}")
        
        return StepOutput(
            passed=geocoded is not None,
            result={
                "geocoded_location": {"lon": geocoded[0], "lat": geocoded[1]} if geocoded else None,
                "input_locations": data,
            },
            metadata={},
        )

def geocode_location(text: str) -> tuple[float, float] | None:
    return _client.geocode(text)