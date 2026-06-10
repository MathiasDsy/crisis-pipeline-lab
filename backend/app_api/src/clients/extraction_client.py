import requests 
from src.config import MODEL_EXTRACTION_SERVER_URL

class ExtractionClient:
    def __init__(self, base_url: str = MODEL_EXTRACTION_SERVER_URL):
        self.base_url = base_url.rstrip("/")

    def extract(self, text: str) -> list[str]:
        response = requests.post(
            f"{self.base_url}/extract-locations",
            json={"text": text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        
        if "entities" not in data:
            return []
        
        res = []
        for entity in data["entities"]:
            res.append(entity["text"])

        return res ###TODO à changer vu que les labels qu'on a pour le moment c'est : ["location", "city", "region", "country"] et on veut peut être changer ça ? 