import requests
import datetime

BASE_URL = "https://dunderligan.se/api/"

class CheckinRequest:
    seasonID: str
    battletag: str
    discordID: str

class Roster:
    id: str
    name: str
    slug: str    

class Membership:
    rank: str
    tier: int
    role: str
    sr: int
    is_captain: bool
    registered_name: str
    roster: Roster

class Player:
    id: str
    battletag: str
    memberships: list[Membership]

class CheckinResponse:
    discordID: str
    checkedInAt: datetime.datetime
    player: Player

async def get(endpoint: str) -> dict:
    """Makes a GET request to the dunderligan.se api, and returns it as a dict."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request to {url}: {e}")
        return {}


async def post(endpoint: str, data: dict) -> dict:
    """Makes a POST request to the dunderligan.se api, and returns it as a dict."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request to {url}: {e}")
        return {}