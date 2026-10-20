from os import getenv
from sys import exit

from discord.ext.commands import Bot
from dotenv import load_dotenv

from cogs.config import Config, load_config
from db_abstraction import DatabaseAbstraction
from dunderligan_api import DunderliganAPI


class Configuration:
    token: str
    api_endpoint: str
    api_key: str
    server_id: int
    yt_api_key: str

    def __init__(self):
        load_dotenv()
        self.token = getenv("TOKEN")
        self.api_endpoint = getenv("API_ENDPOINT")
        self.api_key = getenv("API_KEY")
        self.server_id = int(getenv("SERVER_ID"))

        if self.token is None or self.api_endpoint is None or self.api_key is None or self.server_id is None:
            e = "One or more environment variables are missing. Please check your .env file."
            print(f"Error loading environment variables: {e}")
            exit(1)

        self.yt_api_key = getenv("YOUTUBE_API_KEY")


class Suite:
    db: DatabaseAbstraction
    api: DunderliganAPI
    config: Config
    configuration: Configuration
    bot: Bot

    def __init__(self, configuration: Configuration, bot: Bot):
        self.db = DatabaseAbstraction()
        self.api = DunderliganAPI(configuration)
        self.config = load_config
        self.configuration = configuration
        self.bot = bot