import sqlite3

import backend.sqlite_database as sqlite_database
from backend.sqlite_database import CreatedObject


class DatabaseAbstraction:
    def __init__(self, db_path: str):
        self.connection = sqlite_database.Connection(db_path)

    def get_team_role_ids(self, season_id: str, team_ids: list[str]) -> list[int] | None:
        type_id = self.connection.fetch_discord_object(type="role").id
        try:
            role_ids: list[int] = [self.connection.fetch_created_object(type_id, season_id, team_id=team_id).id for team_id in team_ids]
            return role_ids
        except sqlite3.DatabaseError:
            print(f"Couldn't find roles with season_id {season_id} and team_ids {team_ids}")
            return None

    def get_created_objects(self):
        return self.connection.fetch_all_created_objects()

    def clear_created_objects(self):
        self.connection.delete_all_created_objects()

    def store_created_text_channels(self, channels: list, season_id: str, division_id: str, team_id: str) -> None:
        pass