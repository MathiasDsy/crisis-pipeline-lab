import requests
from fastapi import HTTPException
from pydantic import BaseModel

#TODO refactor as a class ? 
class LoadModelRequest(BaseModel):
    model_key: str
    local_path: str
    loader: str

def get_models_loaded():
    try:
        response = requests.get(
            "http://model-server:8001/models/current",
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"The request sent at http://model-server:8001/models/current sent : {e}",
        )
    
def load_classifier_model(model_key, local_path, model_loader):
    req = LoadModelRequest(
        model_key=model_key,
        local_path=local_path,
        loader=model_loader,
    )

    try:
        response = requests.post(
            "http://model-server:8001/models/load/classifier",
            json=req.dict(),
        )
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e: 
        raise HTTPException(
            status_code=404,
            detail=f"Call Load Classifier Model failed : {e}",
        )
    
def load_location_model(model_key, local_path, model_loader):
    req = LoadModelRequest(
        model_key=model_key,
        local_path=local_path,
        loader=model_loader,
    )

    try:
        response = requests.post(
            "http://model-server:8001/models/load/location_extractor",
            json=req.dict(),
        )
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e: 
        raise HTTPException(
            status_code=404,
            detail=f"Call Load Location Extractor Model failed : {e}",
        )