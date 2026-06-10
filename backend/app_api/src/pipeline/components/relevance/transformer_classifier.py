from typing import Any, Dict

from src.pipeline.base import PipelineComponent, StepOutput
from src.clients.relevance_client import RelevanceClient


class RelevanceClassifierComponent(PipelineComponent):
    def __init__(self, **params):
        super().__init__(**params)
        self.client = RelevanceClient()

    def run(
        self,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepOutput:
        text = inputs["text"]

        prediction = self.client.predict(text)

        label = prediction["label"].lower()
        confidence = prediction["confidence"]

        threshold = params.get("threshold", 0.5)
        passed = label != "noise" and confidence >= threshold

        return StepOutput(
            passed=passed,
            result={
                "label": label,
                "confidence": confidence,
                "passed": passed,
                "raw_prediction": prediction,
            },
            metadata={
                "threshold": threshold,
            },
        )