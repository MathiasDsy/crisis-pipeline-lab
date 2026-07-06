from dataclasses import dataclass
from typing import Any


@dataclass
class ComponentOutput:
    result: Any
    passed: bool = True
    error: bool = False  # True = échec technique (timeout, connexion) ≠ résultat "négatif" légitime


class BaseComponent:
    def run(self, inputs: dict, params: dict, context: dict) -> ComponentOutput:
        raise NotImplementedError