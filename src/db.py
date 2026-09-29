import sqlite3
from datetime import datetime

from dataclasses import dataclass

import discord


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


class Connection:
    connection: sqlite3.Connection

    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)
        self.create_tables()

    def create_cursor(self) -> sqlite3.Cursor:
        return self.connection.cursor()

    def create_tables(self):
        try:
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
        except Exception as e:
            print(e)

    def insert_discord_objects(self, obj_list: list[DiscordObject]) -> None:
        cursor = self.create_cursor()
        cursor.executemany(
            "INSERT INTO discord_object (id, type) VALUES (?, ?)",
            [(obj.id, obj.type) for obj in obj_list],
        )

    def insert_created_object(self, obj: CreatedObject) -> None:
        cursor = self.create_cursor()
        type_id = cursor.execute(
            "SELECT id FROM discord_object WHERE type = ?",
            (obj.type,)
        )
        cursor.execute(
            "INSERT INTO created_object (id, type_id, season_id, division_id, team_id) VALUES (?, ?, ?, ?, ?)",
            ({obj.id}, {type_id}, {obj.season_id}, {obj.division_id}, {obj.team_id}),
        )

    def insert_linked_user(self, user: LinkedUser) -> None:
        cursor = self.create_cursor()
        cursor.execute(
            "INSERT INTO linked_user (discord_id, player_id, battletag, linked_at, checked_in) VALUES (?, ?, ?, ?, ?)",
            (
                {user.discord_id},
                {user.player_id},
                {user.battletag},
                {user.linked_at},
                {user.checked_in},
            ),
        )

    def fetch_discord_object(self, type: str) -> DiscordObject:
        cursor = self.create_cursor()
        cursor.execute("SELECT id FROM discord_object WHERE type = ?", (type,))
        discord_obj = cursor.fetchone()
        if not discord_obj:
            raise sqlite3.DatabaseError
        return DISCORD_OBJECTS[discord_obj[0]]

    def fetch_created_object(self, type_id: int, season_id: str, division_id: str = "", team_id: str = ""):
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
        obj = cursor.fetchone()
        if not obj:
            raise sqlite3.DatabaseError
        type = self.fetch_discord_object(obj[1])
        return CreatedObject(obj[0], type, obj[2], obj[3], obj[4])

def get_team_role(team_id: str) -> discord.Role | None:
    return None


DISCORD_OBJECTS = [
    DiscordObject(0, "role"),
    DiscordObject(1, "category"),
    DiscordObject(2, "text_channel"),
    DiscordObject(3, "voice_channel"),
]


"""
table 1: 'Discord objects'
id: int | type: str

Constant table containing type of objects that can be created and stored in 'table 2'
Instantiated once, kept constantly
"""


"""
table 2: 'Created objects'
id: int | type: DiscordObject | season_id: str | division_id: str | team_id: str

Table containing created objects. Primary purpose is to keep track of created objects so they can be removed in the future.

When creating objects, order will probably go:
Roles -> Categories [roles are retrieved] -> Channels [roles are retrieved]
But since we keep track of season, division, and team, we can also go in any other order, although that might be more inefficient and less clear.

Admins can run a command setting up the current season; When setup they will choose if they want to clear the old season, and then they have to confirm
The setup command will take a while and might run into errors along the way. Because of that, the command should insert values into the database as soon as possible,
    but only commit changes as 'finally:'.

When objects are removed in the future, their record should also be cleared. There will be a way to clear all objects, as well as everything except the current season.
"""


"""
table 3: 'Linked users'
discord_id: int | member_id: str | battletag: str | linked_at: date | currently_checked_in: bool

Table keeping track of users that have 'linked' their discord and battletags together. The purpose is for the bot to be able to keep track of which discord user belongs to which team,
so for future functionality such as booking matches, removing information from direct messages, and simplifying contacting players. The first time a player checks in,
their new 'LinkedUser' should be added to the table. The record is then kept forever, or until the user has to switch their discord_id or battletag, in that case
an admin removes the connection using an admin command.

When checkin for a new season starts, all existing 'LinkedUsers' should have their currently_checked_in variable set to false, When they check in, it should be set to true.
The purpose is 
"""

connection = Connection("test.db")
connection.insert_discord_objects(DISCORD_OBJECTS)
print(connection.fetch_discord_object("category"))