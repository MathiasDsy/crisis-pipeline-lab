import os
import time
import uuid
from datetime import datetime, timezone

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "5"))


FAKE_TWEETS = [
    # SPLIT REGION
    "Smoke visible near Marjan hill in Split",
    "Something burning maybe near the road to Solin",
    "Fire trucks heading toward Klis",
    "Large plume of smoke above Žrnovnica",
    "Strong burning smell near Kaštela industrial zone",
    "Wildfire spreading fast near Omiš hills",
    "Helicopters flying over Makarska because of fire",
    "Forest fire reported near Biokovo nature park",

    # DUBROVNIK REGION
    "Huge smoke cloud visible above Dubrovnik",
    "Firefighters deployed near Cavtat",
    "Brush fire near the road to Konavle",
    "Strong smell of smoke around Lapad tonight",
    "Looks like a wildfire near Mlini",

    # ZADAR REGION
    "Smoke rising near Zadar airport",
    "Wildfire spotted close to Bibinje",
    "Fire visible from the highway near Pakoštane",
    "Canadairs flying above Zadar",
    "Big fire near the olive fields in Nin",

    # ŠIBENIK REGION
    "Forest fire near Vodice spreading quickly",
    "Smoke everywhere near Šibenik bridge",
    "Looks serious near Primošten",
    "Firefighters rushing toward Murter island",

    # RIJEKA / ISTRIA
    "Smoke visible above Rijeka port",
    "Possible wildfire near Opatija hills",
    "Fire reported close to Pula airport",
    "Something burning in Rovinj countryside",
    "Heavy smoke near Labin",

    # ZAGREB REGION
    "Huge smoke plume south of Zagreb",
    "Firefighters and police near Sesvete",
    "Building fire maybe in Novi Zagreb",
    "Strong smell of burning plastic near Trešnjevka",
    "Smoke visible from the highway near Velika Gorica",

    # SLAVONIA
    "Field burning near Osijek",
    "Wildfire reported outside Slavonski Brod",
    "Smoke visible near Vukovar farms",
    "Fire near the train tracks in Vinkovci",

    # LIKA / MOUNTAINS
    "Forest fire close to Plitvice lakes",
    "Smoke visible in the mountains near Gospić",
    "Possible wildfire spreading near Gračac",

    # ISLANDS
    "Brush fire on Hvar island",
    "Smoke visible near Supetar on Brač",
    "Wildfire maybe starting near Korčula vineyards",
    "Firefighters deployed on Pag island",

    # LOW SIGNAL / UNCERTAIN
    "Not sure but I think I saw smoke near Trogir",
    "Maybe a fire somewhere around Split hinterland",
    "Sky looks weird near Zadar tonight",
    "Can smell smoke from my balcony in Dubrovnik",

    # CLEAR NOISE
    "Beautiful sunset today in Split, amazing sky",
    "BBQ night with friends in Zagreb",
    "Fog everywhere near Rijeka this morning",
    "Crazy concert tonight in Dubrovnik",
    "Someone grilling fish near the beach",
    "Clouds over Biokovo look like smoke lol",
    "Traffic terrible near Split again",
    "The sky in Zadar is so orange tonight",
]

def build_fake_tweet(text: str) -> dict:
    return {
        "id": f"tweet_{uuid.uuid4()}",
        "text": text,
        "source": "fake_x",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "rawJson": {
            "simulated": True,
        },
    }


def send_tweet(tweet: dict) -> None:
    response = requests.post(
        f"{API_BASE_URL}/pipeline-run",
        json=tweet,
        timeout=10,
    )

    response.raise_for_status()


def main():
    print("[broker-simulator] started")
    print(f"fake tweets : {len(FAKE_TWEETS)}, interval: {INTERVAL_SECONDS} seconds")
    index = 0

    while True:
        text = FAKE_TWEETS[index % len(FAKE_TWEETS)]
        tweet = build_fake_tweet(text)

        try:
            send_tweet(tweet)
            print(f"[broker-simulator] sent {tweet['id']}")

        except Exception as exc:
            print(f"[broker-simulator] error: {exc}")

        index += 1
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()