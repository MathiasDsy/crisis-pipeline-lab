import os
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from gliner import GLiNER

MODEL_RELEVANCE_PATH = os.getenv("RELEVANCE_MODEL_PATH", "/app/data/models/relevance_model")
MODEL_GLINER_PATH = os.getenv("GLINER_MODEL_PATH", "/app/data/models/gliner_multi-v2.1")

app = FastAPI(title="Crisis Geo Dev API")

tokenizer = None
model = None
device = None
model_gliner = None

class PredictRequest(BaseModel):
    text: str

class ExtractLocationRequest(BaseModel):
    text: str

@app.on_event("startup")
def load_model():
    global tokenizer, model, device, model_gliner

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_RELEVANCE_PATH,
        local_files_only=True
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_RELEVANCE_PATH,
        local_files_only=True
    )

    model.to(device)
    model.eval()

    model_gliner = GLiNER.from_pretrained(MODEL_GLINER_PATH, local_files_only=True)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract-locations")
def extract_locations(req: ExtractLocationRequest):
    labels = ["location", "city", "region", "country"]

    entities = model_gliner.predict_entities(
        req.text,
        labels,
        threshold=0.5,
    )

    return {"entities": entities}

@app.post("/predict")
def predict(req: PredictRequest):
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

    label = model.config.id2label[pred]   # "noise" ou "low_signal"

    return {
        "label": label,
        "is_low_signal": label == "Low Signal",
        "confidence": score
    }