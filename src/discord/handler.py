from typing import Protocol

import discord.bot as bot
import discord.editor as editor
import discord.surveyor as surveyor
from config import Config
from discord import Interaction, Role
from models import Player


class InterfaceLike(Protocol):
    def checkin_player(self, discord_id: int, battletag: str) -> Player:
        ...

    def get_player_role_ids(self, player: Player) -> list[int]:
        ...


class DiscordHandler:
    def __init__(self, interface: InterfaceLike, config: Config):
        self.bot = bot.Bot(config.discord_token, config.discord_server_id)
        self.interface = interface

    async def checkin_user(self, interaction: Interaction) -> None:
        battletag: str = await surveyor.ask_for_battletag(interaction)

        player: Player = self.interface.checkin_player(interaction.user.id, battletag)
        role_ids: list[int] = self.interface.get_player_role_ids(player)
        
        if role_ids is not None and len(role_ids) > 0:
            pass

    def get_tasks(self):
        return [self.bot._start_bot()]