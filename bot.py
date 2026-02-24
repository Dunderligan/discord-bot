# https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import json

# TODO switch to https://pypi.org/project/asyncpg/
import requests
import datetime
import asyncio
import sqlite3

import db

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
token = os.getenv("TOKEN")
server_id: int = int(os.getenv("SERVER_ID"))
admin_role_id: int = int(os.getenv("ADMIN_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db_connection: sqlite3.Connection


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await tree.sync(guild=discord.Object(id=server_id))


@tree.command(
    name="create_new_objects",
    description="Creates a new role, text channel, and voice channel for each team in the given season.",
    guild=discord.Object(id=server_id)
)
@app_commands.checks.has_role(admin_role_id)
async def create_new_objects(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    season = request_seasons()

    season_name = "Säsong 8"

    for division in season["divisions"]:
        division_roles = {}

        division_name = "Division 1"
        division_name_short: str
        if division_name == "Dunderserien":
            division_name_short = "duns"
        else:
            division_name_short = division_name[0:3].lower() + "".join(division_name.split()[-1])

        division_roles = []
        for team in division["teams"]:
            print(
                f"Creating role for team: {team['name']} in division: {division['name']}"
            )
            team_role: discord.Role = await interaction.guild.create_role(name=team["name"])
            division_roles[team] = team_role
        division_permissions = get_division_permissions(interaction.guild, division_roles.values())

        info_category: discord.CategoryChannel = await create_channel(0, f"{season_name} - {division}", season_name, division, None, division_permissions)
        await create_channel(1, f"spelschema-{division_name_short}-{season_name}", season_name, division, info_category, division_permissions)
        await create_channel(1, f"tabell-{division_name_short}-{season_name}", season_name, division, info_category, division_permissions)
        await create_channel(1, f"information-{division_name_short}-{season_name}", season_name, division, info_category, division_permissions)
        await create_channel(1, f"spelartrupper-{division_name_short}-{season_name}", season_name, division, info_category, division_permissions)

        text_category: discord.CategoryChannel = await create_channel(0, f"{season_name} - {division} - Klubbhus", season_name, division, None)
        voice_category: discord.CategoryChannel = await create_channel(0, f"{season_name} - {division} - Röstkanaler", season_name, division, None)

        for team in division["teams"]:
            team_role = division_roles[team]
            team_permissions = get_team_permissions(interaction.guild, team_role)
            discord.TextChannel = await create_channel(1, f"{team}", season_name, division, text_category, team_permissions)
            discord.VoiceChannel = await create_channel(2, f"{team}", season_name, division, voice_category, team_permissions)

        print(f"Finished creating objects for division: {division['name']}")
    await interaction.followup.send("Finished creating new objects.")


async def create_channel(type: int, name: str, season: str, division: str, category: discord.CategoryChannel, overwrites: dict):
    channel = None
    if type == 0:
        channel = await category.guild.create_category(name=name, overwrites=overwrites)
    elif type == 1:
        channel = await category.guild.create_text_channel(name=name, category=category, overwrites=overwrites)
    elif type == 2:
        channel = await category.guild.create_voice_channel(name=name, category=category, overwrites=overwrites)

    db_connection.execute("INSERT INTO channels (channel_id, channel_type, season, division) VALUES (?, ?, ?, ?)", (channel.id, type, season, division))
    db_connection.commit()
    return channel


async def request_seasons():
    url = os.getenv("SEASONS_URL")
    json_data = requests.get(url).json().get("results")
    seasons = list(map(lambda s: s["slug"], json_data))
    print(seasons)


def format_name(name: str) -> str:
    return name.lower()

WRITE_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=True, connect=True, send_messages=True, read_message_history=True
)
READ_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=True, connect=True, send_messages=False, read_message_history=True
)
NO_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=False, connect=False, send_messages=False, read_message_history=False
)

def get_team_permissions(guild: discord.Guild, team_role: discord.Role) -> dict:
    admin_role: discord.Role = discord.utils.find(
        lambda r: r.id == admin_role_id, guild.roles
    )
    overwrites: dict[discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: NO_PERMISSIONS,
        team_role: WRITE_PERMISSIONS,
        admin_role: WRITE_PERMISSIONS,
    }
    return overwrites

def get_division_permissions(guild: discord.Guild, division_roles: list[discord.Role]) -> dict:
    admin_role: discord.Role = discord.utils.find(
        lambda r: r.id == admin_role_id, guild.roles
    )
    overwrites: dict[discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: NO_PERMISSIONS,
        admin_role: WRITE_PERMISSIONS,
    }
    for role in division_roles:
        overwrites[role] = READ_PERMISSIONS
    return overwrites


@tree.command(
    name="print_rosters",
    description="Prints rosters for all team in division",
    guild=discord.Object(id=server_id),
)
async def print_rosters(interaction: discord.Interaction) -> None:
    await interaction.followup.send("Completed.")


async def check_updates():
    while True:
        await asyncio.sleep(5)
        print(f"Checking for updates at {datetime.datetime.now()}")


async def main():
    """Runs client that checks for user-commands and server-side updates in parallell"""
    await request_seasons()
    
    #global db_connection
    #db_connection = db.get_db_connection()
    #db.set_up_db()

    #await asyncio.gather(check_updates(), client.start(token))

asyncio.run(main())
