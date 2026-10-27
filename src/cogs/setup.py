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

from configuration import Suite
from discord.ext import commands

import discord
from backend.sqlite_database import CreatedObject
from discord import (
    CategoryChannel,
    Guild,
    Interaction,
    Role,
    app_commands,
)
from discord.modal import get_selection_modal
from models import Division, Roster, Season


class SetupCog(commands.Cog):
    def __init__(self, suite: Suite):
        self.config = suite.config
        self.api = suite.api
        self.db = suite.db

    @app_commands.command(
        name="setup_channels",
        description="Creates roles, categories, and channels for the divisions and teams belonging to season.",
    )
    async def setup_channels(self, interaction: Interaction):
        try:
            self.seasons: list[Season] = self.api.get_seasons()
            modal: discord.ui.Modal = get_selection_modal("Säsong", (s.name for s in self.seasons), (s.id for s in self.seasons))
            await interaction.response.send_modal(modal)
            await modal.wait()
            print(modal.value)
            await self.generate_season(interaction, modal.vae)
        except Exception as e:
            print(e.with_traceback())

    async def generate_season(self, interaction: Interaction, season_id: str):
        await self.clear_old_objects(interaction.guild)
        season = next(s for s in self.seasons if s.id == season_id)
        for division in season.divisions:
            await generate_division(interaction.guild, division, season)

    async def clear_old_objects(self, guild: Guild) -> None:
        objs: list[CreatedObject] = self.db.get_created_objects()
        try:
            for created_object in objs:
                if created_object.type.type == "role":
                    role: discord.Role = guild.get_role(created_object.id)
                    if not role:
                        continue
                    await role.delete()
                elif (
                    created_object.type.type == "category"
                    or created_object.type.type == "text_channel"
                    or created_object.type.type == "voice_channel"
                ):
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
    short_div = (
        "div" + division.slug
        if division.slug.isdigit()
        else "ds"
        if division.slug == "dunderserien"
        else "???"
    )
    suffix = f"{short_div}-{season.slug[0]}{season.slug[-1]}"

    channels = [
        "spelschema",
        "tabell",
        "information",
        "spelartrupper",
        "rapportera-bans",
    ]
    for c in channels:
        await create_channel(guild, f"{c}-{suffix}", div_cat, {})

    for group in division.groups:
        for roster in group.rosters:
            pass


async def generate_team_channels(guild: Guild, roster: Roster) -> None:
    pass
