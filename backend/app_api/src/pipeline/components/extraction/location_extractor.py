from typing import Any, Dict

from src.clients.extraction_client import ExtractionClient
from src.pipeline.base import PipelineComponent, StepOutput

_client = ExtractionClient()


class LocationExtractorComponent(PipelineComponent):
    def __init__(self, **params):
        super().__init__(**params)

    def run(
        self,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepOutput:

        text = inputs["text"]

        threshold = params.get("threshold", 0.35)
        max_locations = params.get("max_locations", 10)

        locations = extract_locations(text)

        if max_locations:
            locations = locations[:max_locations]

        print(
            f"[LocationExtractorComponent] Extracted locations from '{text}': {locations}"
        )

        return StepOutput(
            passed=len(locations) > 0,
            result={
                "locations": locations,
                "count": len(locations),
            },
            metadata={
                "threshold": threshold,
                "max_locations": max_locations,
            },
        )


def extract_locations(text: str) -> list[str]:
    return _client.extract(text)