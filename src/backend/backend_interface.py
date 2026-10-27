from backend.database_interface import DatabaseAbstraction
from backend.dunderligan_api import DunderliganAPI
from config import Config
from models import Player


class Backend:
    def __init__(self, config: Config):
        self.database = DatabaseAbstraction(config.database_path)
        self.api = DunderliganAPI(config.dunderligan_api_endpoint, config.dunderligan_api_key)    


    def checkin_player(self, season_id: str, discord_id: int, battletag: str) -> Player:
        player: Player = self.api.checkin_player(season_id, discord_id, battletag)
        return player

    def get_tasks(self):
        return []

    def get_player_role_ids(self, player: Player) -> list[int]:
        return []