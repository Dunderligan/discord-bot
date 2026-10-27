from os import getenv

from dotenv import load_dotenv


class Config:
    discord_token: str
    discord_server_id: int
    dunderligan_api_endpoint: str
    dunderligan_api_key: str
    youtube_api_key: str
    database_path: str

    def __init__(self):
        load_dotenv()
        
        self.discord_token = getenv("DISCORD_TOKEN")
        self.discord_server_id = getenv("DISCORD_SERVER_ID")
        self.dunderligan_api_endpoint = getenv("DUNDERLIGAN_API_ENDPOINT")
        self.dunderligan_api_key = getenv("DUNDERLIGAN_API_KEY")
        self.youtube_api_key = getenv("YOUTUBE_API_KEY")
        self.database_path = getenv("DATABASE_PATH")