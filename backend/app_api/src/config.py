import os

MODEL_RELEVANCE_SERVER_URL = os.getenv(
    "MODEL_RELEVANCE_SERVER_URL",
    "http://model-server:8001/"
)

MODEL_EXTRACTION_SERVER_URL = os.getenv(
    "MODEL_EXTRACTION_SERVER_URL",
    "http://model-server:8001/"
)

GEOCODE_API_URL = os.getenv(
    "PHOTON_API_URL",
    "https://photon:2322/api"
)