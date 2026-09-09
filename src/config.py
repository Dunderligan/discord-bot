import discord
import toml

from discord.ext import commands
from discord import app_commands


class Config:
    current_season_id: str
    monitored_yt_channel_ids: list[str]
    notification_text_channel: discord.TextChannel
    captain_role: discord.Role
    observer_role: discord.Role

    def __init__(self):
        pass

    def to_dict(self) -> dict:
        return {
            "current_season_id": self.current_season_id,
            "monitored_yt_channel_ids": self.monitored_yt_channel_ids,
            "notification_text_channel": self.notification_text_channel,
            "captain_role": self.captain_role,
            "observer_role": self.observer_role,
        }

    def from_dict(dict: dict):
        config = Config()
        config.current_season_id = dict.get('current_season_id', None)
        config.monitored_yt_channel_ids = dict.get('monitored_yt_channel_ids', [])
        config.notification_text_channel = dict.get('notification_text_channel', None)
        config.captain_role = dict.get('captain_role', None)
        config.observer_role = dict.get('observer_role', None)
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
        self.config.captain_role = role
        save_config(self.config)
        await interaction.response.send_message(f"Set captain role to <@&{role.id}>", ephemeral=True)

    @app_commands.command(name="set_notifications_channel", description="...")
    @app_commands.describe(role="Kanal som notiser ska skickas i.")
    async def set_notifications_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.config.notification_text_channel = channel
        save_config(self.config)
        await interaction.response.send_message(f"Set notifications channel to <#{channel.id}>", ephemeral=True)