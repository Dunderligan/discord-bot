import asyncio

from backend.backend_client import Backend
from config import Config
from discord_wrappers.bot import Bot
from discord_wrappers.discord_client import DiscordHandler


class Interface:
    def __init__(self):
        self.config: Config = Config()
        self.backend: Backend = Backend(self.config)
        self.discord: DiscordHandler = DiscordHandler(self.config, self.backend)
        self.bot: Bot = Bot(self.config.discord_token, self.config.discord_server_id, self.discord)

    def _gather_tasks(self):
        tasks = []
        tasks += self.backend.get_tasks()
        tasks += self.discord.get_tasks()
        tasks += self.bot.get_tasks()
        return tasks


async def main():
    interface: Interface = Interface()
    await asyncio.gather(*interface._gather_tasks())

asyncio.run(main())