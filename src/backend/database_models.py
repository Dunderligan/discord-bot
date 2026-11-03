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