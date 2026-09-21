import discord
import toml
from discord import app_commands
from discord.ext import commands


class Config:
    current_season_id: str = None
    monitored_yt_channel_ids: list[str] = None
    notification_text_channel_id: int = None
    captain_role_id: int = None
    observer_role_id: int = None

    def to_dict(self) -> dict:
        return {
            "current_season_id": self.current_season_id,
            "monitored_yt_channel_ids": self.monitored_yt_channel_ids,
            "notification_text_channel_id": self.notification_text_channel_id,
            "captain_role_id": self.captain_role_id,
            "observer_role_id": self.observer_role_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        config = cls()
        config.current_season_id = data.get('current_season_id', None)
        config.monitored_yt_channel_ids = data.get('monitored_yt_channel_ids', [])
        config.notification_text_channel_id = data.get('notification_text_channel_id', None)
        config.captain_role_id = data.get('captain_role_id', None)
        config.observer_role_id = data.get('observer_role_id', None)
        return config
        


def load_config() -> Config:
    with open("config.toml", 'r') as file:
        return Config.from_dict(toml.load(file))


def save_config(config: Config) -> None:
    with open("config.toml", 'w') as file:
        toml.dump(config.to_dict(), file)


class ConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: Config):
        self.bot = bot
        self.config = config

    @app_commands.command(name="set_captain_role", description="...")
    @app_commands.describe(role="Roll som kaptener ska bli tilldelade.")
    async def set_captain_role(self, interaction: discord.Interaction, role: discord.Role):
        self.config.captain_role_id = role.id
        save_config(self.config)
        await interaction.response.send_message(f"Set captain role to <@&{role.id}>", ephemeral=True)

    @app_commands.command(name="set_notifications_channel", description="...")
    @app_commands.describe(channel="Kanal som notiser ska skickas i.")
    async def set_notifications_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.config.notification_text_channel_id = channel.id
        save_config(self.config)
        await interaction.response.send_message(f"Set notifications channel to <#{channel.id}>", ephemeral=True)