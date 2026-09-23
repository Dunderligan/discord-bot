import sqlite3
from datetime import datetime

import discord


class Connection:
    connection: sqlite3.Connection


def get_team_role(team_id: str) -> discord.Role | None:
    return None


class DiscordObject:
    id: int
    type: str

DISCORD_OBJECTS = [
    DiscordObject(0, "role"),
    DiscordObject(1, "category"),
    DiscordObject(2, "text_channel"),
    DiscordObject(3, "voice_channel")
]

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

class LinkedUser:
    discord_id: int
    player_id: str
    battletag: str
    linked_at: datetime
    checked_in: bool

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