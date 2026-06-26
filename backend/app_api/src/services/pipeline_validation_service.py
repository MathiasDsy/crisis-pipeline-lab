from src.repositories.model_repository import get_model_by_key

ALLOWED_COMPONENTS = {
    "relevance_classifier",
    "location_extractor",
    "geocoder",
    "event_matcher",
}


def validate_pipeline_runtime(pipeline: dict) -> tuple[bool, list[str]]:
    errors = []

    for component_key in pipeline["required_components_json"]:
        if component_key not in ALLOWED_COMPONENTS:
            errors.append(f"Unknown component: {component_key}")

    for model_key in pipeline["required_models_json"]:
        model = get_model_by_key(model_key)

        if model is None:
            errors.append(f"Missing model: {model_key}")
            continue

        if model["is_available"] is False:
            errors.append(f"Model not available: {model_key}")

    return len(errors) == 0, errors