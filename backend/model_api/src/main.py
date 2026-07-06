import os
from contextlib import asynccontextmanager
from typing import Any

import torch
from fastapi import APIRouter, FastAPI, HTTPException
from gliner import GLiNER
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# =====================================================
# State
# =====================================================

_state: dict[str, Any] = {
    "classifier": {
        "model_key": None,
        "tokenizer": None,
        "model": None,
        "device": None,
    },
    "gliner": {
        "model_key": None,
        "model": None,
    },
}

DEFAULT_RELEVANCE_PATH = os.getenv("RELEVANCE_MODEL_PATH", "/app/storage/models/relevance_model")
DEFAULT_GLINER_PATH = os.getenv("GLINER_MODEL_PATH", "/app/storage/models/gliner_multi-v2.1")

# =====================================================
# Loaders
# =====================================================

def _load_classifier(model_key: str, local_path: str) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(local_path, local_files_only=True)
    model.to(device)
    model.eval()

    _state["classifier"]["model_key"] = model_key
    _state["classifier"]["tokenizer"] = tokenizer
    _state["classifier"]["model"] = model
    _state["classifier"]["device"] = device


def _load_gliner(model_key: str, local_path: str) -> None:
    model = GLiNER.from_pretrained(local_path, local_files_only=True)

    _state["gliner"]["model_key"] = model_key
    _state["gliner"]["model"] = model


# =====================================================
# Startup
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # try:
    #     _load_classifier(model_key="default_classifier", local_path=DEFAULT_RELEVANCE_PATH)
    #     print(f"[startup] Classifier loaded from {DEFAULT_RELEVANCE_PATH}")
    # except Exception as e:
    #     print(f"[startup] Classifier load failed: {e}")

    # try:
    #     _load_gliner(model_key="default_gliner", local_path=DEFAULT_GLINER_PATH)
    #     print(f"[startup] GLiNER loaded from {DEFAULT_GLINER_PATH}")
    # except Exception as e:
    #     print(f"[startup] GLiNER load failed: {e}")

    print("[startup] Model API server is ready")
    yield
    print("[shutdown] Model API server is shutting down")


app = FastAPI(title="Crisis Model Server", lifespan=lifespan)

# =====================================================
# Schemas
# =====================================================

class PredictRequest(BaseModel):
    text: str

class ExtractLocationRequest(BaseModel):
    text: str
    labels: list[str] = ["location", "city", "region", "country"]
    threshold: float = 0.5

class LoadModelRequest(BaseModel):
    model_key: str
    local_path: str
    loader: str

# =====================================================
# Routers
# =====================================================

health_router = APIRouter(tags=["health"])
models_router = APIRouter(prefix="/models", tags=["models"])
inference_router = APIRouter(tags=["inference"])

# =====================================================
# Health
# =====================================================

@health_router.get("/health")
def health():
    return {
        "status": "ok",
        "classifier_loaded": _state["classifier"]["model_key"] is not None,
        "gliner_loaded": _state["gliner"]["model_key"] is not None,
    }

# =====================================================
# Models
# =====================================================

@models_router.get("/current")
def get_current_models():
    return {
        "classifier": {"model_key": _state["classifier"]["model_key"]},
        "gliner": {"model_key": _state["gliner"]["model_key"]},
    }


@models_router.post("/load/classifier")
def load_classifier(req: LoadModelRequest):
    try:
        _load_classifier(model_key=req.model_key, local_path=req.local_path)
        return {"status": "loaded", "model_key": req.model_key, "loader": req.loader}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load classifier: {e}")


@models_router.post("/load/location_extractor")
def load_location_extractor(req: LoadModelRequest):
    try:
        _load_gliner(model_key=req.model_key, local_path=req.local_path)
        return {"status": "loaded", "model_key": req.model_key, "loader": req.loader}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load GLiNER: {e}")


@models_router.post("/unload/classifier")
def unload_classifier():
    _state["classifier"] = {"model_key": None, "tokenizer": None, "model": None, "device": None}
    return {"status": "unloaded"}


@models_router.post("/unload/location_extractor")
def unload_location_extractor():
    _state["gliner"] = {"model_key": None, "model": None}
    return {"status": "unloaded"}

# =====================================================
# Inference
# =====================================================

@inference_router.post("/predict")
def predict(req: PredictRequest):
    tokenizer = _state["classifier"]["tokenizer"]
    model = _state["classifier"]["model"]
    device = _state["classifier"]["device"]
    model_key = _state["classifier"]["model_key"]

    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Classifier model not loaded")

    inputs = tokenizer(
        req.text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        pred = torch.argmax(probs, dim=1).item()
        score = probs[0][pred].item()

    label = model.config.id2label[pred]
    is_relevant = label.lower() not in ("noise", "not_relevant", "not relevant", "off-topic")

    return {
        "label": label,
        "is_relevant": is_relevant,
        "confidence": score,
        "model_key": model_key,
    }


@inference_router.post("/extract-locations")
def extract_locations(req: ExtractLocationRequest):
    model = _state["gliner"]["model"]
    model_key = _state["gliner"]["model_key"]

    if model is None:
        raise HTTPException(status_code=503, detail="GLiNER model not loaded")

    entities = model.predict_entities(req.text, req.labels, threshold=req.threshold)

    return {
        "entities": entities,
        "model_key": model_key,
    }

# =====================================================
# Register routers
# =====================================================

app.include_router(health_router)
app.include_router(models_router)
app.include_router(inference_router)
