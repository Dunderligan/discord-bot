import enum
import sqlite3

import backend.sqlite_database as sqlite_database
from backend.database_models import CreatedObject


class CreatedObjects(enum.Enum):
    ROLE = "role"
    TEXT_CHANNEL = "text_channel"
    VOICE_CHANNEL = "voice_channel"
    CATEGORY = "category"


class DatabaseAbstraction:
    def __init__(self, db_path: str):
        self.connection = sqlite_database.Connection(db_path)
        self.types = {}
        self.types[CreatedObjects.ROLE] = self.connection.fetch_discord_object(type=CreatedObjects.ROLE.value)
        self.types[CreatedObjects.TEXT_CHANNEL] = self.connection.fetch_discord_object(type=CreatedObjects.TEXT_CHANNEL.value)
        self.types[CreatedObjects.VOICE_CHANNEL] = self.connection.fetch_discord_object(type=CreatedObjects.VOICE_CHANNEL.value)
        self.types[CreatedObjects.CATEGORY] = self.connection.fetch_discord_object(type=CreatedObjects.CATEGORY.value)

    def get_team_role_ids(self, season_id: str, team_ids: list[str]) -> list[int] | None:
        try:
            role_ids: list[int] = [self.connection.fetch_created_object(self.types["role"], season_id, team_id=team_id).id for team_id in team_ids]
            return role_ids
        except sqlite3.DatabaseError:
            print(f"Couldn't find roles with season_id {season_id} and team_ids {team_ids}")
            return None

    def get_created_objects(self):
        objects = self.connection.fetch_all_created_objects()
        self.connection.delete_all_created_objects()
        return objects

    def clear_created_objects(self):
        self.connection.delete_all_created_objects()

    def store_role_id(self, role_id: int, season_id: str, division_id: str, team_id: str | None) -> None:
        self.connection.insert_created_object(CreatedObject(
            role_id,
            self.types[CreatedObjects.ROLE],
            season_id,
            division_id,
            team_id  
        ))

    def store_text_channel_id(self, channel_id: int, season_id: str, division_id: str, team_id: str | None) -> None:
        self.connection.insert_created_object(CreatedObject(
            channel_id,
            self.types[CreatedObjects.TEXT_CHANNEL],
            season_id,
            division_id,
            team_id  
        ))

    def store_voice_channel_id(self, channel_id: int, season_id: str, division_id: str, team_id: str | None) -> None:
        self.connection.insert_created_object(CreatedObject(
            channel_id,
            self.types[CreatedObjects.VOICE_CHANNEL],
            season_id,
            division_id,
            team_id  
        ))

    def store_category_id(self, category_id: int, season_id: str, division_id: str) -> None:
        self.connection.insert_created_object(CreatedObject(
            category_id,
            self.types[CreatedObjects.CATEGORY],
            season_id,
            division_id,
            None  
        ))