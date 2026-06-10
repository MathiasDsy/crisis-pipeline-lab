import requests
from src.config import MODEL_RELEVANCE_SERVER_URL


class RelevanceClient:
    def __init__(self, base_url: str = MODEL_RELEVANCE_SERVER_URL):
        self.base_url = base_url.rstrip("/")

    def predict(self, text: str) -> bool:
        response = requests.post(
            f"{self.base_url}/predict",
            json={"text": text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        print(f"Relevance model response: {data}")
        return data