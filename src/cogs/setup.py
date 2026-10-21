"""
Cog with the purpose of setting up a discord server with corresponding categories, channels, and roles,
according to the teams and divisions existing within the set season.

Currently, the structure will be as follows:
    For each division:
        An info category, with the text channels:
        <Season> - <Division> [Visible for each team playing in the division, as well as observers, hidden for @everyone]
            spelschema-<div>-<season> [read-only]
            tabell-<div>-<season> [read-only]
            information-<div>-<season> [read-only]
            spelartrupper-<div>-<season> [read-only]
            rapportera-bans-<div>-<season> [only captains can write, otherwise read-only]
            (if showmatch) [text] showmatch-<div> [hidden for @everyone, visible for Showmatch-<Div> role]
            (if showmatch) [voice] Lag 1 [hidden for @everyone, visible for Showmatch-<Div> role]
            (if showmatch) [voice] Lag 2 [hidden for @everyone, visible for Showmatch-<Div> role]

        A "clubhouse" category, with a text channel for each team in the division:
        <Season> - <Division> - Klubbhus [Hidden for @everyone]
            <team> [see and write for the teams role, hidden for others]

        A category for voice channels, with a voice channel for each team:
        <Season> - <Division> - Röstkanaler [Hidden for @everyone]
            <Team> [see, connect, and speak for teams role, hidden for others], limited to 5 members
"""

import discord
from discord import (
    CategoryChannel,
    Guild,
    Interaction,
    Role,
    app_commands,
)
from discord.ext import commands

from configuration import Suite
from db import CreatedObject
from models import Division, Roster, Season


class SetupModal(discord.ui.Modal, title="Skapa kanaler"):


    def __init__(self, callback, seasons: list[Season]):
        super().__init__()
        self.seasons = seasons
        self.callback = callback
        self.add_item(discord.ui.Label(
            text="Säsong",
            description="Välj säsong att skapa kanaler för:",
            component=discord.ui.Select(
            placeholder="Välj säsong...",
            options=[
                discord.SelectOption(
                    label=s.name,
                    value=s.id,
                )
                for s in seasons
            ],
            required=True
        )))

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(
            interaction.guild,
            filter(lambda s: s.id == self.season.values[0], self.seasons)[0],
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.followup.send(
            "Oj! Ett fel uppstod. Kontakta Admin om det kvarstår.", ephemeral=True
        )
        print(
            f"Error occurred when user {interaction.user.global_name} tried setting up channels: {error}"
        )


class SetupCog(commands.Cog):
    def __init__(
        self,
        suite: Suite
    ):
        self.config = suite.config
        self.api = suite.api
        self.db = suite.db

    @app_commands.command(
        name="setup_channels",
        description="Creates roles, categories, and channels for the divisions and teams belonging to season.",
    )
    async def setup_channels(self, interaction: Interaction):
        try:
            await interaction.response.send_modal(
                SetupModal(self.generate_season, self.api.get_seasons())
            )
        except Exception as e:
            print(e)

    async def generate_season(self, guild: Guild, season: Season):
        await self.clear_old_objects(guild)
        for division in season.divisions:
            await generate_division(guild, division, season)

    async def clear_old_objects(self, guild: Guild) -> None:
        objs: list[CreatedObject] = self.db.get_created_objects()
        try:
            for created_object in objs:
                if created_object.type.type == "role":
                    role: discord.Role = guild.get_role(created_object.id)
                    if not role:
                        continue
                    await role.delete()
                elif created_object.type.type == "category" or created_object.type.type == "text_channel" or created_object.type.type == "voice_channel":
                    channel = guild.get_channel(created_object.id)
                    if not channel:
                        continue
                    await channel.delete()
                else:
                    print("this shi cooked")
            self.db.clear_created_objects()
        except Exception as e:
            print(e)


async def create_role(guild: Guild, name: str) -> Role:
    return await guild.create_role(name=name)       


async def create_category(guild: Guild, name: str, overwrites: dict) -> CategoryChannel:
    return await guild.create_category(name=name, overwrites=overwrites)


async def create_channel(
    guild: Guild, name: str, category: CategoryChannel, overwrites: dict
):
    return await guild.create_text_channel(
        name=name, overwrites=overwrites, category=category
    )


async def generate_division(guild: Guild, division: Division, season: Season) -> None:
    div_cat = await create_category(guild, f"{season.name} - {division.name}", {})
    short_div = "div" + division.slug if division.slug.isdigit() else "ds" if division.slug == "dunderserien" else "???"
    suffix = f"{short_div}-{season.slug[0]}{season.slug[-1]}"

    channels = ["spelschema", "tabell", "information", "spelartrupper", "rapportera-bans"]
    for c in channels:
        await create_channel(guild, f"{c}-{suffix}", div_cat, {})

    for group in division.groups:
        for roster in group.rosters:
            pass


async def generate_team_channels(guild: Guild, roster: Roster) -> None:
    pass
