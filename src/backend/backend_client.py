from backend.database import DatabaseAbstraction
from backend.dunderligan_api import DunderliganAPI
from config import Config
from models import Player, Season


class Backend:
    def __init__(self, config: Config):
        self.database = DatabaseAbstraction(config.database_path)
        self.api = DunderliganAPI(config.dunderligan_api_endpoint, config.dunderligan_api_key)    

    def checkin_player(self, season_id: str, discord_id: int, battletag: str) -> Player:
        player: Player = self.api.checkin_player(season_id, discord_id, battletag)
        return player

    def get_tasks(self):
        return []

    def get_player_role_ids(self, season_id: str, player: Player) -> list[int]:
        print(f"Searching for role for roster ids: {[t.roster.id for t in player.memberships]}")
        return self.database.get_team_role_ids(season_id, [t.roster.id for t in player.memberships])

    def get_season(self, season_id: str) -> Season:
        return next(filter(lambda s: s.id == season_id, self.api.get_seasons()))

    def store_created_channels(self, channels: list) -> None:
        self.database.store_created_channels(channels)