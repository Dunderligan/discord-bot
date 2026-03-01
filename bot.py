# https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os

# TODO switch to https://pypi.org/project/asyncpg/
import requests
import datetime
import asyncio
import sqlite3

import db

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
try:
    token = os.getenv("TOKEN")
    server_id: int = int(os.getenv("SERVER_ID"))
    admin_role_id: int = int(os.getenv("ADMIN_ID"))
    observer_role_id: int = int(os.getenv("OBSERVER_ID"))
    captains_role_id: int = int(os.getenv("CAPTAINS_ID"))
except Exception as e:
    print(f"Error loading environment variables: {e}")
    exit(1)

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
    description="Creates channels and roles for all team in a season. Gets data from dunderligan.se API.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
async def create_new_objects(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    seasons = await request_seasons()
    if seasons is None:
        await interaction.followup.send("Failed to fetch seasons.")
        return

    season_name = "Säsong 8"

    for season in seasons:
        print(f"{season['name']}")
        if season["name"] != season_name:
            print("Not correct.")
            continue
        season_slug = season["slug"]
        season_slug = season_slug[0] + season_slug[-1]
        for division in season["divisions"]:
            print(f"{division['name']}")

            division_name = division["name"]
            division_slug = division["slug"]
            if division_slug == "dunderserien":
                division_slug = "ds"
            else:
                division_slug = "div" + division_slug[0]

            division_roles = {}
            for group in division["groups"]:
                for team in group["rosters"]:
                    team_name = team["name"]
                    team_slug = team["slug"]
                    team_role: discord.Role = await interaction.guild.create_role(
                        name=team_name
                    )
                    db_connection.execute(
                        "INSERT INTO channels (id, type, season, division, team) VALUES (?, ?, ?, ?, ?)",
                        (team_role.id, 3, season_name, division_name, team["id"]),
                    )
                    db_connection.commit()
                    division_roles[team_name] = team_role
                    print(f"Created role for team: {team_name}")

            print("Starts creating divisions permissions.")
            division_permissions = get_division_permissions(
                interaction.guild, division_roles.values()
            )

            print("Starts creating channels for division.")
            info_category: discord.CategoryChannel = await create_channel(
                interaction.guild,
                0,
                f"{season_name} - {division_name}",
                season_slug,
                division_slug,
                None,
                None,
                division_permissions,
            )
            await create_channel(
                interaction.guild,
                1,
                f"spelschema-{division_slug}-{season_slug}",
                season_slug,
                division_slug,
                None,
                info_category,
                division_permissions,
            )
            await create_channel(
                interaction.guild,
                1,
                f"tabell-{division_slug}-{season_slug}",
                season_slug,
                division_slug,
                None,
                info_category,
                division_permissions,
            )
            await create_channel(
                interaction.guild,
                1,
                f"information-{division_slug}-{season_slug}",
                season_slug,
                division_slug,
                None,
                info_category,
                division_permissions,
            )
            await create_channel(
                interaction.guild,
                1,
                f"spelartrupper-{division_slug}-{season_slug}",
                season_slug,
                division_slug,
                None,
                info_category,
                division_permissions,
            )
            await create_channel(
                interaction.guild,
                1,
                f"rapportera-bans-{division_slug}-{season_slug}",
                season_slug,
                division_slug,
                None,
                info_category,
                get_captains_permissions(interaction.guild, division_roles.values()),
            )
            text_category: discord.CategoryChannel = await create_channel(
                interaction.guild,
                0,
                f"{season_name} - {division_name} - Klubbhus",
                season_slug,
                division_slug,
                None,
                None,
                get_admin_permissions(interaction.guild),
            )
            voice_category: discord.CategoryChannel = await create_channel(
                interaction.guild,
                0,
                f"{season_name} - {division_name} - Röstkanaler",
                season_slug,
                division_slug,
                None,
                None,
                get_admin_permissions(interaction.guild),
            )

            for group in division["groups"]:
                for team in group["rosters"]:
                    team_name = team["name"]
                    team_slug = team["slug"]
                    team_id = team["id"]

                    team_role = division_roles[team_name]
                    team_permissions = get_team_permissions(
                        interaction.guild, team_role
                    )
                    text_channel = await create_channel(
                        interaction.guild,
                        1,
                        f"{team_slug}",
                        season_slug,
                        division_slug,
                        team_id,
                        text_category,
                        team_permissions,
                    )
                    await text_channel.send(f"Välkommen till klubbhuset för {team_name}!\nHär kan ni kommunicera inom laget, men det kommer också vara här som ligaledningen kan ta kontakt med er.")

                    await create_channel(
                        interaction.guild,
                        2,
                        f"{team_name}",
                        season_slug,
                        division_slug,
                        team_id,
                        voice_category,
                        team_permissions,
                    )

            print(f"Finished creating objects for division: {division['name']}")
        break
    await interaction.followup.send("Finished creating new objects.")


async def create_channel(
    guild: discord.Guild,
    type: int,
    name: str,
    season: str,
    division: str,
    team: str,
    category: discord.CategoryChannel,
    overwrites: dict,
):
    channel = None
    if type == 0:
        if overwrites is not None:
            channel = await guild.create_category(name=name, overwrites=overwrites)
        else:
            channel = await guild.create_category(name=name)
    elif type == 1:
        channel = await guild.create_text_channel(
            name=name, category=category, overwrites=overwrites
        )
    elif type == 2:
        channel = await guild.create_voice_channel(
            name=name, category=category, overwrites=overwrites
        )

    db_connection.execute(
        "INSERT INTO channels (id, type, season, division, team) VALUES (?, ?, ?, ?, ?)",
        (channel.id, type, season, division, team),
    )
    db_connection.commit()
    await asyncio.sleep(0.2)  # Sleep to avoid hitting rate limits
    return channel


@tree.command(
    name="delete_all_objects",
    description="Deletes all channels and roles previously created by the bot.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
async def delete_all_objects(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    cursor = db_connection.cursor()
    cursor.execute("SELECT id, type FROM channels")
    channels = cursor.fetchall()
    for id, type in channels:
        await asyncio.sleep(0.2)  # Sleep to avoid hitting rate limits
        channel = interaction.guild.get_channel(id)
        if channel is not None:
            await channel.delete()
            print(f"Deleted channel with id: {id}")
        else:
            role = interaction.guild.get_role(id)
            if role is not None:
                await role.delete()
                print(f"Deleted role with id: {id}")
            else:
                print(f"Could not find channel or role with id: {id}")
    db_connection.execute("DELETE FROM channels")
    db_connection.commit()
    await interaction.followup.send("Finished deleting all objects.")

async def request_seasons():
    try:
        url = os.getenv("SEASONS_URL")
        json_data = requests.get(url, timeout=10).json().get("results")
        return json_data
    except Exception as e:
        print(f"Error fetching seasons: {e}")
        return None


WRITE_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=True, connect=True, send_messages=True, read_message_history=True
)
READ_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=True, connect=True, send_messages=False, read_message_history=True
)
NO_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    view_channel=False, connect=False, send_messages=False, read_message_history=False
)
ONLY_WRITE_PERMISSIONS: discord.PermissionOverwrite = discord.PermissionOverwrite(
    connect=True, send_messages=True
)


def get_admin_permissions(guild: discord.Guild) -> dict:
    admin_role: discord.Role = discord.utils.find(
        lambda r: r.id == admin_role_id, guild.roles
    )
    overwrites: dict[discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: NO_PERMISSIONS,
        admin_role: WRITE_PERMISSIONS,
    }
    return overwrites


def get_team_permissions(guild: discord.Guild, team_role: discord.Role) -> dict:
    overwrites = get_admin_permissions(guild)
    overwrites[team_role] = READ_PERMISSIONS
    return overwrites


def get_division_permissions(guild: discord.Guild, division_roles) -> dict:
    observer_role: discord.Role = discord.utils.find(
        lambda r: r.id == observer_role_id, guild.roles
    )
    overwrites = get_admin_permissions(guild)
    overwrites[observer_role] = READ_PERMISSIONS
    for role in division_roles:
        overwrites[role] = READ_PERMISSIONS
    return overwrites

def get_captains_permissions(guild: discord.Guild, division_roles) -> dict:
    captains_role: discord.Role = discord.utils.find(
        lambda r: r.id == captains_role_id, guild.roles
    )
    overwrites = get_division_permissions(guild, division_roles)
    overwrites[captains_role] = ONLY_WRITE_PERMISSIONS
    return overwrites


@tree.command(
    name="print_rosters",
    description="Prints rosters for all team in division",
    guild=discord.Object(id=server_id),
)
async def print_rosters(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    await interaction.followup.send("Completed.")


async def check_updates():
    while True:
        await asyncio.sleep(5)
        print(f"Checking for updates at {datetime.datetime.now()}")


async def main():
    """Runs client that checks for user-commands and server-side updates in parallell"""
    # await request_seasons()

    global db_connection
    db_connection = db.get_db_connection()
    db.set_up_db()

    await asyncio.gather(client.start(token))


asyncio.run(main())
