from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class StepOutput:
    """
    Standardized output returned by every pipeline component.

    This contract ensures that:
    - every step can be chained consistently,
    - the pipeline runner can build a full execution trace,
    - outputs can be stored/debugged/exported uniformly.

    Concepts:
    ----------
    passed:
        Indicates whether the step succeeded logically and whether
        the pipeline should continue.

        Examples:
        - relevance filter rejecting noise -> passed=False
        - geocoding ambiguity warning -> passed=True
        - extraction success -> passed=True

    result:
        Context/data forwarded to the next pipeline step.

        IMPORTANT:
        This becomes the next `context["current"]`.

        Example:
        {
            "text": "...",
            "locations": ["Split"],
            "relevance": {...}
        }

    metadata:
        Debug/inspection information not necessarily needed by
        downstream components.

        Used for:
        - UI trace visualization,
        - benchmarking,
        - diagnostics,
        - annotation support.

        Examples:
        - scores
        - candidates
        - matches
        - thresholds
        - raw model outputs

    description:
        Human-readable explanation of what happened during the step.

        Intended for:
        - frontend display,
        - debugging,
        - operational understanding.
    """

    # Whether the pipeline should continue after this step.
    passed: bool = True

    # Context passed to the next pipeline step.
    result: Dict[str, Any] = field(default_factory=dict)

    # Additional debug/trace information.
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Human-readable explanation for UI/debugging.
    description: Optional[str] = None



class PipelineComponent(ABC):
    def __init__(self, **params):
        self.params = params


    @abstractmethod
    def run(self, context: Dict[str, Any]) -> StepOutput:
        pass