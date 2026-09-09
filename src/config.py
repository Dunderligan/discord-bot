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
        return Config.from_dict(toml.load(file))


def save_config(config: Config) -> None:
    with open("config.toml", '+w') as file:
        toml.dump(config.to_dict(), file)

class ConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()

    @app_commands.command(name="set_captain_role", description="...")
    @app_commands.describe(role="Roll som kaptener ska bli tilldelade.")
    async def set_captain_role(self, interaction: discord.Interaction, role: discord.Role):
        self.config.role_captain = role
        save_config(self.config)
        await interaction.response.send_message(f"Set captain role to <@&{role.id}>", ephemeral=True)

    @app_commands.command(name="set_notifications_channel", description="...")
    @app_commands.describe(role="Kanal som notiser ska skickas i.")
    async def set_notifications_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.config.channel_notifications = channel
        save_config(self.config)
        await interaction.response.send_message(f"Set notifications channel to <#{channel.id}>", ephemeral=True)