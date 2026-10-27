import asyncio

from backend.backend_interface import Backend
from config import Config
from discord.handler import DiscordHandler
from models import Player

current_season_id = ""

class Interface:
    def __init__(self):
        self.config: Config = Config()
        self.backend: Backend = Backend(self.config)
        self.discord: DiscordHandler = DiscordHandler(self, self.config)

    def _gather_tasks(self):
        tasks = []
        tasks += self.backend.get_tasks()
        tasks += self.discord.get_tasks()
        return tasks

    def checkin_player(self, discord_id: int, battletag: str) -> Player:
        return self.backend.checkin_player(current_season_id, discord_id, battletag)
    
    def get_player_role_ids(self, player: Player) -> list[int]:
        return self.backend.get_player_role_ids(player)


async def main():
    interface: Interface = Interface()
    await asyncio.gather(*interface._gather_tasks())


asyncio.run(main())