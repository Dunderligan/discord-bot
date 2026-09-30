import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiscordObject:
    id: int
    type: str


@dataclass
class CreatedObject:
    """Class representing a discord object created by the discord bot.
    The types of objects that exist are defined by another table. Each CreatedObject has to have a discord id,
    season id, and type. Division and team id:s are not mandatory and should be set to NONE or -1 if missing.
    Season, division, and team id:s are meant for finding the right channel/role/category the request is looking for.
    """

    id: int
    type: DiscordObject
    season_id: str
    division_id: str
    team_id: str


@dataclass
class LinkedUser:
    discord_id: int
    player_id: str
    battletag: str
    linked_at: datetime
    checked_in: bool


# The preset list of existing discord objects
DISCORD_OBJECTS = [
    DiscordObject(0, "role"),
    DiscordObject(1, "category"),
    DiscordObject(2, "text_channel"),
    DiscordObject(3, "voice_channel"),
]


class Connection:
    connection: sqlite3.Connection

    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)
        self.create_tables()

    def create_cursor(self) -> sqlite3.Cursor:
        return self.connection.cursor()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.executescript("""
            BEGIN;
            CREATE table IF NOT EXISTS discord_object (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL
            );
                
            CREATE table IF NOT EXISTS created_object (
                id INTEGER PRIMARY KEY,
                type_id INTEGER NOT NULL,
                season_id TEXT NOT NULL,
                division_id TEXT,
                team_id TEXT
            );

            CREATE table IF NOT EXISTS linked_user (
                discord_id INTEGER PRIMARY KEY,
                player_id TEXT NOT NULL,
                battletag TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                checked_in BOOLEAN NOT NULL
            );
            COMMIT;
            """)
        self.insert_discord_objects(DISCORD_OBJECTS)

    def insert_discord_objects(self, obj_list: list[DiscordObject]) -> None:
        cursor = self.create_cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO discord_object (id, type) VALUES (?, ?)",
            [(obj.id, obj.type) for obj in obj_list],
        )
        self.connection.commit()

    def insert_created_object(self, obj: CreatedObject) -> None:
        cursor = self.create_cursor()
        cursor.execute(
            "INSERT INTO created_object (id, type_id, season_id, division_id, team_id) VALUES (?, ?, ?, ?, ?)",
            (obj.id, obj.type.id, obj.season_id, obj.division_id, obj.team_id),
        )
        self.connection.commit()

    def insert_linked_user(self, user: LinkedUser) -> None:
        cursor = self.create_cursor()
        cursor.execute(
            "INSERT INTO linked_user (discord_id, player_id, battletag, linked_at, checked_in) VALUES (?, ?, ?, ?, ?)",
            (
                user.discord_id,
                user.player_id,
                user.battletag,
                user.linked_at,
                user.checked_in,
            ),
        )
        self.connection.commit()

    def fetch_discord_object(self, type: str | None = None, type_id: int | None = None) -> DiscordObject:
        cursor = self.create_cursor()
        if type:
            cursor.execute("SELECT id FROM discord_object WHERE type = ?", (type,))
        if type_id:
            cursor.execute("SELECT id FROM discord_object WHERE id = ?", (type_id,))
        discord_obj = cursor.fetchone()
        if not discord_obj:
            raise sqlite3.DatabaseError(f"Couldn't find discord_object of type {type}")
        return DISCORD_OBJECTS[discord_obj[0]]

    def fetch_created_object(self, type_id: int, season_id: str, division_id: str | None = None, team_id: str | None = None):
        cursor = self.create_cursor()
        sql_query = "SELECT * FROM created_object WHERE type_id = ? AND season_id = ?"
        parameters = [type_id, season_id]
        if division_id:
            sql_query += " AND division_id = ?"
            parameters.append(division_id)
        if team_id:
            sql_query += " AND team_id = ?"
            parameters.append(team_id)
        cursor.execute(sql_query, parameters)
        obj = cursor.fetchall()
        if len(obj) > 1:
            raise sqlite3.DatabaseError(f"Found too many created objects with sql {sql_query}")
        elif not obj:
            raise sqlite3.DatabaseError(f"Couldn't find created object with sql {sql_query}")
        obj = obj[0]
        type = self.fetch_discord_object(type_id=obj[1])
        return CreatedObject(obj[0], type, obj[2], obj[3], obj[4])