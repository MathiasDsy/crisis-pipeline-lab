import hashlib
import uuid
from datetime import datetime
from typing import Any

import yaml


def parse_pipeline_file(content: bytes) -> dict[str, Any]:
    raw_text = content.decode("utf-8")
    config = yaml.safe_load(raw_text)

    if not isinstance(config, dict):
        raise ValueError("Pipeline config must be a YAML object")

    return config


def validate_pipeline_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    errors = []

    for field in ["name", "version", "steps"]:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    steps = config.get("steps", [])

    if not isinstance(steps, list) or len(steps) == 0:
        errors.append("steps must be a non-empty list")

    for index, step in enumerate(steps):
        for field in ["id", "component_key", "input", "output"]:
            if field not in step:
                errors.append(f"Step {index}: missing field '{field}'")

    return len(errors) == 0, errors


def extract_required_models(config: dict[str, Any]) -> list[str]:
    models = []

    for step in config.get("steps", []):
        model_key = step.get("model_key")
        if model_key and model_key not in models:
            models.append(model_key)

    return models


def extract_required_components(config: dict[str, Any]) -> list[str]:
    components = []

    for step in config.get("steps", []):
        component_key = step.get("component_key")
        if component_key and component_key not in components:
            components.append(component_key)

    return components


def hash_config(config: dict[str, Any]) -> str:
    normalized = yaml.safe_dump(config, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_pipeline_record(
    config: dict[str, Any],
    filename: str,
) -> dict[str, Any]:
    is_valid, errors = validate_pipeline_config(config)

    return {
        "id": str(uuid.uuid4()),
        "name": config.get("name"),
        "version": str(config.get("version")),
        "description": config.get("description"),
        "config_json": config,
        "required_models_json": extract_required_models(config),
        "required_components_json": extract_required_components(config),
        "original_filename": filename,
        "config_hash": hash_config(config),
        "is_valid": is_valid,
        "validation_errors": errors,
        "created_at": datetime.utcnow(),
    }