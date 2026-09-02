import discord
import toml

from discord.ext import commands
from discord import app_commands


class Config:
    id_season: str
    id_yt_channel: str
    channel_notifications: discord.TextChannel
    role_captain: discord.Role
    role_observer: discord.Role

    def __init__(self):
        pass

    def to_dict(self) -> dict:
        return {
            "id_season": self.id_season,
            "id_yt_channel": self.id_yt_channel,
            "channel_notifications": self.channel_notifications,
            "role_captain": self.role_captain,
            "role_observer": self.role_observer,
        }

    def from_dict(dict: dict):
        config = Config()
        config.id_season = dict.get('id_season', None)
        config.id_yt_channel = dict.get('id_yt_channel', None)
        config.channel_notifications = dict.get('channel_notifications', None)
        config.role_captain = dict.get('role_captain', None)
        config.role_observer = dict.get('role_observer', None)
        return config
        


def load_config() -> Config:
    with open("config.toml", '+r') as file:
        return toml.load(file)


def save_config(config: Config) -> None:
    with open("config.toml", '+w') as file:
        toml.dump(config, file)


class ConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set_captain_role", description="...")
    @app_commands.describe(role="Roll som kaptener ska bli tilldelade.")
    async def set_captain_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.send_message("Waiting for response...")


config: Config = load_config()