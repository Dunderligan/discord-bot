# https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import json

# TODO switch to https://pypi.org/project/asyncpg/
import requests
import datetime
import enum
import asyncio

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


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await tree.sync(guild=discord.Object(id=server_id))


"""
Skapa DB anslutning

Skapa kanal (Kategori, Division, Säsong 8, Typ, Namn)
    Skapa kanal
    Lägg till i databas

Skapa säsong i DC
    Verifiera DB
    Ladda säsong
    För varje division:
        För varje lag:
            Skapa en lagroll
        Skapa en info-kategori
        Skapa info-kanaler
        Skapa en röst-kategori
        Skapa en text-kategori
        För varje lag:
            Skapa en röstkanal för bara daem
            Skapa en textkanal för bara dem
            """


@tree.command(
    name="create_new_objects",
    description="Creates a new role, text channel, and voice channel for each team in the given season.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(season="Season to get teams from.")
async def create_new_objects(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    verify_connection()
    season = request_season()

    for division in season["divisions"]:
        standings_channel: discord.TextChannel = await interaction.guild.create_text_channel();
        info_channel: discord.TextChannel = await interaction.guild.create_text_channel();
        roster_channel: discord.TextChannel = await interaction.guild.create_text_channel();

        division_roles = []
        for team in division["teams"]:
            print(
                f"Creating role for team: {team['name']} in division: {division['name']}"
            )
            team_role: discord.Role = await interaction.guild.create_role(name=team["name"])
            division_roles.append(team_role)
            team_permissions = get_team_permissions(interaction.guild, team_role)

    await interaction.followup.send("Finished creating new objects.")


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
    global db_connection
    db_connection = dbqueries.AsyncConnection()
    await db_connection.connect_to_db(postgres_link)

    await asyncio.gather(check_updates(), client.start(token))


asyncio.run(main())
