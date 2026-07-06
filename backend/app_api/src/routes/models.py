import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from src.repositories.model_repository import get_model_by_key, list_models as list_models_from_db, update_model_availability
from src.repositories.model_repository import upsert_model
from src.services.model_discovery import discover_models_from_storage

MODELS_DIR = Path("/app/storage/models")

# Contrat composant -> type de modèle attendu.
# Chaque entrée définit :
#   - hf_filters : les contraintes passées à HfApi.list_models pour ne remonter QUE les modèles compatibles
#   - loader     : le loader imposé côté model-server (le champ metadata.loader n'est pas laissé au choix)
COMPONENT_CONTRACTS: dict[str, dict] = {
    "relevance_classifier": {
        # HF n'accepte qu'un pipeline_tag par requête -> on lance une requête par tag et on fusionne
        "hf_pipeline_tags": ["text-classification", "zero-shot-classification"],
        "loader": "transformers",
        "label": "modèle de classification de séquence",
    },
    "location_extractor": {
        "hf_filter": "gliner",
        "loader": "gliner",
        "label": "modèle GLiNER",
    },
}


def _hf_query_variants(contract: dict) -> list[dict]:
    """Liste des jeux de kwargs à passer à list_models pour couvrir tout le contrat."""
    variants = [{"pipeline_tag": tag} for tag in contract.get("hf_pipeline_tags", [])]
    if contract.get("hf_filter"):
        variants.append({"filter": contract["hf_filter"]})
    return variants or [{}]

router = APIRouter(
    prefix="/models",
    tags=["models"],
)


@router.get("")
def list_models(
    model_type: str | None = None,
    available: bool | None = None,
):
    models = list_models_from_db(
        model_type=model_type,
        available=available,
    )

    return {
        "models": models,
        "filters": {
            "model_type": model_type,
            "available": available,
        },
    }


@router.get("/{model_key}")
def get_model(model_key: str):
    """
    Récupère le détail d'un modèle par model_key.
    """

    model = get_model_by_key(model_key)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_key}' not found"
        )

    return model


@router.post("/discover")
def discover_models():
    discovered = discover_models_from_storage()

    valid_models = [
        model for model in discovered
        if model.get("is_valid") is True
    ]

    invalid_models = [
        model for model in discovered
        if model.get("is_valid") is False
    ]

    for model in valid_models:
        model_to_save = model.copy()
        model_to_save.pop("is_valid", None)
        upsert_model(model_to_save)

    return {
        "status": "success",
        "models_dir": "/app/storage/models",
        "discovered_count": len(discovered),
        "valid_count": len(valid_models),
        "invalid_count": len(invalid_models),
        "valid_models": valid_models,
        "invalid_models": invalid_models,
    }


class HuggingFaceImportRequest(BaseModel):
    repo_id: str
    model_key: str
    component: str  # impose loader + compatible_components via COMPONENT_CONTRACTS
    version: str = "1.0.0"
    hf_token: str | None = None


@router.get("/search/huggingface")
def search_huggingface(
    component: str,
    q: str | None = None,
    limit: int = 20,
    hf_token: str | None = None,
):
    """
    Recherche des modèles HuggingFace compatibles avec un composant du pipeline.
    Le filtre HF est imposé par le contrat du composant : on ne remonte QUE
    les modèles du bon type (ex: relevance_classifier -> text-classification).
    """
    contract = COMPONENT_CONTRACTS.get(component)
    if contract is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown component '{component}'. Expected one of: {list(COMPONENT_CONTRACTS)}",
        )

    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise HTTPException(status_code=500, detail="huggingface_hub not installed")

    def _format_size(num_params: int | None) -> str | None:
        if num_params is None:
            return None
        if num_params >= 1_000_000_000:
            return f"{num_params / 1_000_000_000:.1f}B"
        if num_params >= 1_000_000:
            return f"{num_params / 1_000_000:.0f}M"
        return f"{num_params / 1_000:.0f}K"

    def _serialize(m) -> dict:
        num_params = None
        size_on_disk_mb = None
        safetensors = getattr(m, "safetensors", None)
        if safetensors is not None:
            num_params = safetensors.total
            if num_params:
                # estimation ~2 octets/paramètre (F16/BF16)
                size_on_disk_mb = round(num_params * 2 / 1_000_000, 1)
        return {
            "repo_id": m.id,
            "author": m.id.split("/")[0] if "/" in m.id else None,
            "model_name": m.id.split("/")[-1] if "/" in m.id else m.id,
            "downloads": getattr(m, "downloads", None),
            "likes": getattr(m, "likes", None),
            "tags": getattr(m, "tags", None),
            "pipeline_tag": getattr(m, "pipeline_tag", None),
            "last_modified": str(m.lastModified) if getattr(m, "lastModified", None) else None,
            "url": f"https://huggingface.co/{m.id}",
            "num_parameters": num_params,
            "size_label": _format_size(num_params),
            "size_on_disk_mb": size_on_disk_mb,
        }

    try:
        api = HfApi(token=hf_token)

        # Une requête par variante du contrat (ex: text-classification + zero-shot), puis fusion
        by_repo: dict[str, dict] = {}
        for variant in _hf_query_variants(contract):
            for m in api.list_models(
                search=q,
                limit=limit,
                sort="downloads",
                expand=["downloads", "likes", "pipeline_tag", "tags", "lastModified", "safetensors"],
                **variant,
            ):
                if m.id not in by_repo:
                    by_repo[m.id] = _serialize(m)

        models = sorted(by_repo.values(), key=lambda x: x["downloads"] or 0, reverse=True)[:limit]

        return {
            "component": component,
            "query": q,
            "count": len(models),
            "models": models,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"HuggingFace search failed: {e}")


@router.post("/import/huggingface")
def import_from_huggingface(req: HuggingFaceImportRequest):
    contract = COMPONENT_CONTRACTS.get(req.component)
    if contract is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown component '{req.component}'. Expected one of: {list(COMPONENT_CONTRACTS)}",
        )

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise HTTPException(status_code=500, detail="huggingface_hub not installed")

    target_dir = MODELS_DIR / req.model_key

    if target_dir.exists():
        raise HTTPException(status_code=409, detail=f"Model '{req.model_key}' already exists in storage")

    try:
        snapshot_download(
            repo_id=req.repo_id,
            local_dir=str(target_dir),
            token=req.hf_token,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"HuggingFace download failed: {e}")

    # loader et compatible_components sont imposés par le contrat du composant, pas par l'utilisateur
    metadata = {
        "model_key": req.model_key,
        "name": req.repo_id,
        "version": req.version,
        "model_type": req.component,
        "loader": contract["loader"],
        "entrypoint": ".",
        "compatible_components": [req.component],
        "source": "huggingface",
        "repo_id": req.repo_id,
    }

    import json
    (target_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    discovered = discover_models_from_storage()
    for model in discovered:
        if model.get("model_key") == req.model_key and model.get("is_valid"):
            m = model.copy()
            m.pop("is_valid", None)
            upsert_model(m)

    return {
        "status": "success",
        "model_key": req.model_key,
        "local_path": str(target_dir),
        "repo_id": req.repo_id,
    }


@router.post("/import/upload")
async def import_from_upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tmp_zip = MODELS_DIR / f"_tmp_{file.filename}"

    try:
        with tmp_zip.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            names = zf.namelist()

            # Cherche metadata.json à la racine ou dans un sous-dossier
            metadata_candidates = [n for n in names if n.endswith("metadata.json")]
            if not metadata_candidates:
                raise HTTPException(status_code=400, detail="No metadata.json found in zip")

            metadata_path_in_zip = sorted(metadata_candidates, key=lambda x: x.count("/"))[0]
            prefix = metadata_path_in_zip.replace("metadata.json", "")

            import json
            with zf.open(metadata_path_in_zip) as f:
                metadata = json.load(f)

            model_key = metadata.get("model_key")
            if not model_key:
                raise HTTPException(status_code=400, detail="metadata.json must contain 'model_key'")

            target_dir = MODELS_DIR / model_key
            if target_dir.exists():
                raise HTTPException(status_code=409, detail=f"Model '{model_key}' already exists in storage")

            target_dir.mkdir(parents=True)

            for member in names:
                if not member.startswith(prefix):
                    continue
                relative = member[len(prefix):]
                if not relative:
                    continue
                dest = target_dir / relative
                if member.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract zip: {e}")
    finally:
        tmp_zip.unlink(missing_ok=True)

    discovered = discover_models_from_storage()
    registered = None
    for model in discovered:
        if model.get("model_key") == model_key and model.get("is_valid"):
            m = model.copy()
            m.pop("is_valid", None)
            upsert_model(m)
            registered = m

    if registered is None:
        raise HTTPException(status_code=400, detail=f"Model extracted but metadata.json is invalid — check required fields")

    return {
        "status": "success",
        "model_key": model_key,
        "local_path": str(target_dir),
    }


@router.post("/{model_key}/check")
def check_model_availability(model_key: str):
    """
    Vérifie qu'un modèle existe vraiment sur le disque.
    """

    model = get_model_by_key(model_key)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_key}' not found"
        )

    path = Path(model["local_path"])

    is_available = path.exists()

    update_model_availability(
        model_key=model_key,
        is_available=is_available,
    )

    return {
        "model_key": model_key,
        "local_path": str(path),
        "is_available": is_available,
    }