"""
Script defining an interface towards the Dunderligan API. 
Currently keeps track of both Response-types and the specific
requests the bot will make towards the API, might be separated in the
future if there are many added response types.
"""

from dataclasses import dataclass
from datetime import datetime

from models import Division, Player, Season
from network import Network


@dataclass
class CheckinResponse:
    discord_id: str
    checked_in_at: datetime
    player: Player

    def from_json(json: dict):
        return CheckinResponse(
            json.get("discordId"),
            datetime.fromisoformat(json.get("checkedInAt")),
            Player.from_json(json.get("player")),
        )

@dataclass
class SeasonResponse:
    seasons: list[Season]

    def from_json(json: dict):
        return SeasonResponse([Season.from_json(s) for s in json.get("seasons")])

@dataclass
class DivisionResponse:
    division: Division

    def from_json(json: dict):
        return DivisionResponse(Division.from_json(json))


class DunderliganAPI:
    def __init__(self, api_endpoint: str, api_key: str):
        self.network: Network = Network(
            api_endpoint, api_key
        )

    def checkin_player(
        self, season_id: str, discord_id: str, battletag: str
    ) -> CheckinResponse:
        return self.network.post(
            f"checkin/{season_id}/{discord_id}",
            {"battletag": battletag},
            CheckinResponse,
        )

    def get_seasons(self) -> list[Season]:
        response: SeasonResponse = self.network.get("season", SeasonResponse)
        return response.seasons

    def get_division(self, division_id: str) -> Division:
        response: DivisionResponse = self.network.get(
            f"division/{division_id}", DivisionResponse
        )
        return response.division
