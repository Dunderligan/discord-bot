from dataclasses import dataclass
from datetime import datetime

from configuration import Configuration
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
            datetime.datetime.fromisoformat(json.get("checkedInAt")),
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
    def __init__(self, configuration: Configuration):
        self.network: Network = Network(
            configuration.api_endpoint, configuration.api_key
        )

    def checkin_player(
        self, season_id: str, discord_id: str, battletag: str
    ) -> CheckinResponse:
        return self.network.request(
            f"checkin/{season_id}/{discord_id}",
            "POST",
            {"battletag": battletag},
            CheckinResponse,
        )

    def get_seasons(self) -> list[Season]:
        response: SeasonResponse = self.request("season", "GET", None, SeasonResponse)
        return response.seasons

    def get_division(self, division_id: str) -> Division:
        response: DivisionResponse = self.request(
            f"division/{division_id}", "GET", None, DivisionResponse
        )
        return response.division
