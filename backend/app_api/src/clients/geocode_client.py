from src.config import GEOCODE_API_URL
import requests
import time

class GeocodeClient:
    BASE_URL = GEOCODE_API_URL

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "crisis-geo/0.1 (wildfire detection research; contact: you@example.com)",
            "Accept-Language": "en",
        })

    def geocode(self, query: str):
        time.sleep(1.1)  # Nominatim policy
        params = {
            "q": query,
            "limit": 1,
        }
        request = requests.Request("GET", self.BASE_URL, params=params)
        prepared = self.session.prepare_request(request)
        print(f"[GeocodeClient] full request URL: {prepared.url}")
        response = self.session.send(prepared, timeout=10)
        print(f"response status code: {response.status_code}")
        #Exemple of return of the api:
        # {
        # "type": "FeatureCollection",
        # "features": [
        #     {
        #     "type": "Feature",
        #     "properties": {
        #         "osm_type": "R",
        #         "osm_id": 11153757,
        #         "osm_key": "place",
        #         "osm_value": "city",
        #         "type": "city",
        #         "countrycode": "HR",
        #         "name": "Split",
        #         "country": "Croatie",
        #         "county": "Comitat de Split-Dalmatie",
        #         "extent": [16.3877955, 43.5322835, 16.5303557, 43.4985847]
        #     },
        #     "geometry": {
        #         "type": "Point",
        #         "coordinates": [16.4399659, 43.5116383]
        #     }
        #     }
        # ]
        # }

        response.raise_for_status()
        data = response.json()
        if data is None or len(data) == 0:
            return None

        print(f"[GeocodeClient] API request at : {self.BASE_URL} with query '{query}'")
        print(f"[GeocodeClient] API response for '{query}': {data}")
        point = data["features"][0]["geometry"]["coordinates"]

        # print(point)

        return point