from typing import Any, Dict

from src.pipeline.base import PipelineComponent


class KeywordNoiseFilter(PipelineComponent):
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["input"]["text"].lower()

        keywords = self.params.get("keywords", [])
        threshold = self.params.get("threshold", 1)
        positive_label = self.params.get("positive_label", "low_signal")
        negative_label = self.params.get("negative_label", "noise")

        matches = [
            keyword for keyword in keywords
            if keyword.lower() in text
        ]

        passed = len(matches) >= threshold

        return {
            "label": positive_label if passed else negative_label,
            "passed": passed,
            "matches": matches,
            "score": len(matches),
            "threshold": threshold,
        }