import toml
from configuration import Suite
from discord.ext import commands

import discord
from discord import app_commands
from discord.modal import get_selection_modal
from models import Season


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
    try:
        with open("config.toml", 'r') as file:
            return Config.from_dict(toml.load(file))
    except FileNotFoundError:
        print("Config file was not found.")
        return Config()



def save_config(config: Config) -> None:
    with open("config.toml", 'w') as file:
        toml.dump(config.to_dict(), file)


class ConfigCog(commands.Cog):
    def __init__(self, suite: Suite):
        self.config = load_config()
        suite.config = self.config
        self.api = suite.api

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

    class PickSeasonModal(discord.ui.Modal, title="Välj säsong"):
        def __init__(self, config: Config, seasons: list[Season]):
            super().__init__()
            self.seasons = seasons
            self.config = config
            self.season = discord.ui.Label(
                text="Säsong",
                description="Välj nuvarande säsong.",
                component=discord.ui.Select(
                    options=[
                        discord.SelectOption(label=s.name, value=s.id) for s in seasons
                    ],
                    required=True
                )
            )
            self.add_item(self.season)


        async def on_submit(self, interaction: discord.Interaction):
            print(self.season.component.values)
            self.config.current_season_id = self.season.component.values[0]
            save_config(self.config)
            await interaction.response.send_message(f"Successfully set current_season_id to {self.season.component.values[0]}", ephemeral=True)

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            await interaction.response.send_message(
                "Oj! Ett fel uppstod. Kontakta Admin om det kvarstår.", ephemeral=True
            )
            print(
                f"Error occurred when user {interaction.user.global_name} tried changing current_season_id: {error}"
            )

    @app_commands.command(name="set_current_season", description="...")
    async def set_current_season(self, interaction: discord.Interaction):
        try:
            seasons = self.api.get_seasons()
            modal: discord.ui.Modal = get_selection_modal("Säsong", (s.name for s in seasons), (s.id for s in seasons))
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.config.current_season_id = modal.value            
        except Exception as e:
            print(e)