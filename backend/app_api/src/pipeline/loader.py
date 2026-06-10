from pathlib import Path
from typing import Any, Dict

import yaml

from src.pipeline.registry import COMPONENT_REGISTRY
from src.pipeline.runner import PipelineRunner


def load_pipeline_from_yaml(config_path: str | Path) -> PipelineRunner:
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Pipeline config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config: Dict[str, Any] = yaml.safe_load(file)

    steps = []

    for step_config in config.get("steps", []):
        if not step_config.get("enabled", True):
            continue

        component_key = step_config["component"]

        if component_key not in COMPONENT_REGISTRY:
            raise ValueError(f"Unknown pipeline component: {component_key}")

        component_class = COMPONENT_REGISTRY[component_key]
        params = step_config.get("params", {})
        inputs = step_config.get("input", {})
        output = step_config.get("output", {})

        # print(f"Loading component '{component_key}' for step '{step_config['id']}' with params: {params}")
        # print(f"Input mapping for step '{step_config['id']}': {inputs}")
        # print(f"Output path for step '{step_config['id']}': {output}")

        steps.append({
            "id": step_config["id"],
            "name": step_config.get("name", step_config["id"]),
            "enabled": step_config.get("enabled", True),
            "component_key": component_key,
            "component": component_class(**params),
            "params": params,
            "input": inputs,
            "output": output,
        })

    return PipelineRunner(
        pipeline_id=config["id"],
        pipeline_name=config.get("name", config["id"]),
        pipeline_version=str(config.get("version", "unknown")),
        runtime=config.get("runtime", {}),
        steps=steps,
    )