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

# When Photon is not part of the running stack (e.g. the default dev profile),
# set GEOCODING_ENABLED=false so the geocoder step is skipped instead of failing
# on an unreachable Photon.
GEOCODING_ENABLED = os.getenv("GEOCODING_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")