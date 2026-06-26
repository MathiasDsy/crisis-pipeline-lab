def resolve_inputs(context: dict, input_mapping: dict) -> dict:
    """
    Résout les inputs d'un step depuis le contexte d'exécution.
    input_mapping ex: {"text": "tweet.content", "locations": "outputs.location_extractor.locations"}
    """
    resolved = {}

    for key, path in input_mapping.items():
        resolved[key] = get_path(context, path)

    return resolved


def get_path(obj: dict, path: str):
    """Accès par chemin pointé : "outputs.step_id.field" """
    parts = path.split(".")
    current = obj

    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)

    return current


def set_path(obj: dict, path: str, value) -> None:
    """Écriture par chemin pointé : "outputs.step_id" """
    parts = path.split(".")
    current = obj

    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value
