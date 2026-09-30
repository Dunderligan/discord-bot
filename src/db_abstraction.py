import sqlite3

import db


class DatabaseAbstraction:
    def __init__(self):
        self.connection = db.Connection("local.db")

    def get_team_role_id(self, season_id: str, team_id: str) -> int | None:
        type_id = self.connection.fetch_discord_object(type="role").id
        try:
            role = self.connection.fetch_created_object(type_id, season_id, team_id=team_id)
        except sqlite3.DatabaseError:
            print(f"Couldn't find role with season_id {season_id} and team_id {team_id}")
            return None
        return role.id