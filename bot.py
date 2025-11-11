# https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import json
import psycopg2
import requests
import datetime
import typst
import enum
import asyncio
from dotenv import load_dotenv
from discord import app_commands


class CLEARABLE_OBJECT(str, enum.Enum):
    VoiceChannels = "VOICE"
    TextChannels = "TEXT"
    Roles = "ROLES"
    All = "ALL"


CLEAR_FROM_PATH: str = "old_objects.json"  # contains the id to text-, voice channels, and roles, divided in a dictionary

load_dotenv()
token = os.getenv("TOKEN")
server_id: int = int(os.getenv("SERVER_ID"))
postgres_link = os.getenv("POSTGRES_LINK")
PERSISTENT_FOLDER: str = os.getenv("PERSISTENT_FOLDER")

db_conn = psycopg2.connect(postgres_link)
cursor = db_conn.cursor()

admin_role_id: int = int(os.getenv("ADMIN_ID"))
text_category: discord.CategoryChannel

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await tree.sync(guild=discord.Object(id=server_id))


@tree.command(
    name="remove_old_objects",
    description="Removes all old objects of a given type, that has previously been created by this bot.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(alternative="Objects to remove")
async def remove_old_objects(
    interaction: discord.Interaction, alternative: CLEARABLE_OBJECT
) -> None:
    await interaction.response.defer()
    old_objects = load_old_objects()
    if old_objects:
        if alternative in ["VOICE", "ALL"]:
            for o in old_objects["voice"]:
                voice_channel = discord.utils.find(
                    lambda v: v.id == o, interaction.guild.voice_channels
                )
                if voice_channel:
                    await voice_channel.delete()
                else:
                    print(f"Couldn't find voice channel with ID: {o}")
            old_objects["voice"] = []

        if alternative in ["TEXT", "ALL"]:
            for o in old_objects["text"]:
                text_channel = discord.utils.find(
                    lambda t: t.id == o, interaction.guild.text_channels
                )
                if text_channel:
                    await text_channel.delete()
                else:
                    print(f"Couldn't find text channel with ID: {o}")
            old_objects["text"] = []

        if alternative in ["ROLES", "ALL"]:
            for o in old_objects["roles"]:
                role = discord.utils.find(lambda r: r.id == o, interaction.guild.roles)
                if role:
                    await role.delete()
                else:
                    print(f"Couldn't find role with ID: {o}")
            old_objects["roles"] = []
        save_new_objects(old_objects)
        await interaction.followup.send(
            f"Finished removing all old {alternative} objects."
        )
    else:
        await interaction.followup.send(
            f"Did not find any objects in {CLEAR_FROM_PATH} to remove."
        )


def load_old_objects() -> dict:
    if os.path.isfile(PERSISTENT_FOLDER + CLEAR_FROM_PATH):
        with open(PERSISTENT_FOLDER + CLEAR_FROM_PATH, "r") as file:
            old_objects: dict = json.load(file)
            return old_objects
    else:
        old_objects: dict = {}
        return old_objects


@tree.command(
    name="create_new_objects",
    description="Creates a new role, text channel, and voice channel for each team in the given season.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(season="Season to get teams from.")
async def create_new_objects(interaction: discord.Interaction, season: str) -> None:
    await interaction.response.defer()
    text_category: discord.CategoryChannel = discord.utils.find(
        lambda category: category.id == int(os.getenv("TEXT_CATEGORY")),
        interaction.guild.categories,
    )
    teams = get_teams(season)
    new_objects = {"text": [], "voice": [], "roles": []}

    for t in teams:
        # creates a role
        formatted_name = format_name(t[0])
        new_role: discord.Role = await interaction.guild.create_role(name=f"{t[0]}")
        new_objects["roles"].append(new_role.id)

        # creates a text channel in assigned category
        channel_permissions: dict = get_role_permissions(interaction.guild, new_role)
        new_text_channel: discord.TextChannel = (
            await interaction.guild.create_text_channel(
                formatted_name, category=text_category, overwrites=channel_permissions
            )
        )
        new_objects["text"].append(new_text_channel.id)

        # sends embed in newly created text channel
        embed: discord.Embed = discord.Embed(title=formatted_name)
        embed.set_image(url=get_team_logo_link(t[2], 256))
        embed.description = f"Välkommen till ert lags kanal! Här kommer er direktkontakt med admins ske.\n<@&{new_role.id}>"
        await new_text_channel.send(embed=embed)

        # creates a voice channel
        voice_category = discord.utils.get(interaction.guild.categories, name=t[1])
        if not voice_category:
            voice_category = await interaction.guild.create_category(t[1])
        new_voice_channel: discord.VoiceChannel = (
            await interaction.guild.create_voice_channel(
                t[0], category=voice_category, overwrites=channel_permissions
            )
        )
        new_objects["voice"].append(new_voice_channel.id)

    save_new_objects(new_objects)
    await interaction.followup.send("Finished creating new objects.")


def save_new_objects(objects: dict) -> None:
    with open(PERSISTENT_FOLDER + CLEAR_FROM_PATH, "w") as file:
        json.dump(objects, file)


def get_teams(season: str) -> dict:
    cursor.execute(f"""SELECT 
                    r.name, 
                    d.name as division_name, 
                    r.id, 
                    r.slug 
                    FROM roster r 
                        JOIN "group" g ON g.id = r.group_id
                        JOIN division d ON d.id = g.division_id
                    WHERE season_slug = '{season}'
                    ORDER BY division_name, r.name
                    LIMIT 8""")
    teams = cursor.fetchall()
    return teams


def format_name(name: str) -> str:
    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789-"
    formatted_name = ""
    for c in name:
        char = c.lower()
        if char in allowed_characters:
            formatted_name += char
        elif char in "åäáà":
            formatted_name += "a"
        elif char == "öõ":
            formatted_name += "o"
        elif char == "'" or formatted_name[-1] == "-":
            continue
        else:
            formatted_name += "-"
    return formatted_name.lower()


def get_role_permissions(guild: discord.Guild, role: discord.Role) -> dict:
    admin_role: discord.Role = discord.utils.find(
        lambda r: r.id == admin_role_id, guild.roles
    )
    overwrites: dict[discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False, connect=False
        ),
        role: discord.PermissionOverwrite(view_channel=True, connect=True),
        admin_role: discord.PermissionOverwrite(view_channel=True, connect=True),
    }
    return overwrites


def get_team_logo_link(team: str, size: int) -> str:
    return f"https://cdn.kesomannen.com/cdn-cgi/image/format=png,fit=scale-down,width={size}/dunderligan/logos/{team}.png"


async def check_updates():
    check_for_updates: bool = True

    await asyncio.sleep(10)

    guild: discord.Guild = None
    channel: discord.TextChannel = None

    while check_for_updates:
        if not guild:
            guild = discord.utils.find(lambda s: s.id == server_id, client.guilds)
        if guild and not channel:
            channel = discord.utils.find(
                lambda c: c.name == "tabell", guild.text_channels
            )
        if guild and channel:
            cursor.execute("""
                        SELECT 
                            d.name AS "division_name"
                        FROM division d
                            JOIN "season" s ON d.season_id = s.id
                        WHERE s.slug = 'test'
                        ORDER BY d.name
                        """)
            divisions = cursor.fetchall()

            for d in divisions:
                await output_standing(channel, d[0])

        time_now: datetime.datetime = datetime.datetime.now()
        next_hour: datetime.datetime = (time_now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0
        )
        second_delay: int = (next_hour - time_now).total_seconds()

        await asyncio.sleep(second_delay)


def get_team_thumbnail(team: str) -> str:
    image_folder = f"{PERSISTENT_FOLDER}team_thumbnails/"
    image_path = f"{image_folder}{format_name(team)}.png"

    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)
    if not os.path.isfile(image_path):
        image_formats = ("image/png", "image/jpeg", "image/jpg")
        r = requests.get(get_team_logo_link(team, 64))
        if r.headers["content-type"] in image_formats:
            image = r.content
            with open(image_path, "wb") as file:
                file.write(image)
        else:
            return "placeholder-team.jpg"
    return image_path


async def output_standing(channel: discord.TextChannel, division_name: str) -> None:
    cursor.execute(f"""
                    SELECT 
                        d.name AS "division_name",
                        m.team_a_score,
                        m.team_b_score,
                        ra.name AS "roster_a_name",
                        rb.name AS "roster_b_name",
                        ra.id AS "roster_a_id",
                        rb.id AS "roster_b_id",
                        m.draws AS "draw"
                    FROM division d
                        JOIN "group" g ON g.division_id = d.id
                        JOIN "match" m ON m.group_id = g.id
                        JOIN "roster" ra ON m.roster_a_id = ra.id
                        JOIN "roster" rb ON m.roster_b_id = rb.id
                        JOIN "season" s ON d.season_id = s.id
                    WHERE s.slug = 'test'
                        AND d.name = '{division_name}'
                   """)
    matches = cursor.fetchall()

    # goes through all matches and adds relevant numbers to teams
    teams: dict[str:tuple] = {}
    for match in matches:
        points_1 = match[1]
        points_2 = match[2]
        team_1 = match[3]
        team_2 = match[4]
        id_1 = match[5]
        id_2 = match[6]
        draws = match[7]

        total_points = points_1 + points_2

        if not teams.get(team_1):
            teams[team_1] = (get_team_thumbnail(id_1), 0, 0, 0)
        if not teams.get(team_2):
            teams[team_2] = (get_team_thumbnail(id_2), 0, 0, 0)

        (logo_1, wins_1, losses_1, draws_1) = teams[team_1]
        teams[team_1] = (
            logo_1,
            wins_1 + points_1,
            losses_1 + (total_points - points_1),
            draws_1 + draws,
        )

        (logo_2, wins_2, losses_2, draws_2) = teams[team_2]
        teams[team_2] = (
            logo_2,
            wins_2 + points_2,
            losses_2 + (total_points - points_2),
            draws_2 + draws,
        )

    # sorts teams after amount of wins; highest number first
    sorted_teams = {}
    for team in sorted(teams, key=lambda t: teams.get(t)[1], reverse=True):
        sorted_teams[team] = teams[team]
    teams = None

    # formats data for typst-file
    standings = []
    for team, data in sorted_teams.items():
        (logo, wins, losses, draws) = data
        standings.append((logo, team, f"{wins}/{losses}/{draws}", f"{wins}p"))
    sorted_teams = None

    print(standings)
    # adds further data for typst
    current_time = str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"))
    season = "7"
    document_data = {
        "standings": standings,
        "division": division_name,
        "season": season,
    }
    sys_inputs = {
        "document_data": json.dumps(document_data),
        "time": json.dumps(current_time),
    }

    image_directory = "generated_images"
    if not os.path.isdir(image_directory):
        os.mkdir(image_directory)
    OUTPUT_FILE = (
        f"{image_directory}/standing-div-{division_name.replace(' ', '_')}.png"
    )

    TYPST_FILE = f"standings.typ"
    typst.compile(
        input=TYPST_FILE,
        output=OUTPUT_FILE,
        format="png",
        sys_inputs=sys_inputs,
        ppi=144.0,
        font_paths=["fonts"],
    )
    with open(OUTPUT_FILE, "rb") as image:
        await channel.send(file=discord.File(image))


def get_roster(season: int, division: int, team: str = ""):
    pass


def clear_thumbnail_cache() -> None:
    directory = "team_thumbnails"
    for thumbnail in os.listdir(directory):
        os.remove(f"{directory}/{thumbnail}")


@tree.command(
    name="print_rosters",
    description="Prints rosters for all team in division",
    guild=discord.Object(id=server_id),
)
async def print_rosters(interaction: discord.Interaction, division: int) -> None:
    await interaction.response.defer()
    cursor.execute(f"""
                    SELECT 
                        p.battletag,
                        m.rank, 
                        m.tier, 
                        m.role,
                        m.is_captain,
                        r.name AS "roster_name"
                    FROM player p
                        JOIN "member" m ON m.player_id = p.id
                        JOIN "roster" r ON r.id = m.roster_id
                        JOIN "group" g ON g.id = r.group_id
                        JOIN "division" d ON d.id = g.division_id
                        JOIN "season" s ON s.id = d.season_id
                    WHERE s.slug = 'test'
                        AND d.name = 'Division {division}'
                    """)
    players = cursor.fetchall()

    teams: dict[str:list] = {}
    for p in players:
        battletag = p[0]
        rank = p[1]
        tier = p[2]
        role = p[3]
        is_captain = p[4]
        team_name = p[5]

        if not teams.get(team_name):
            teams[team_name] = []
        teams[team_name].append((rank, tier, role, battletag, is_captain))

    roles = {"tank": 0, "damage": 1, "support": 2, "flex": 3, "coach": 4}
    for team_name, players in teams.items():
        team_players = sorted(players, key=lambda p: roles[p[2]])
        team_message = f"## **{team_name}**\n"
        for p in team_players:
            rank_emote = discord.utils.get(interaction.guild.emojis, name=p[0])
            role_emote = discord.utils.get(interaction.guild.emojis, name=p[2])
            if p[2] == "coach":
                team_message += "\n"
            team_message += f"- {role_emote} {p[2].capitalize()} - {rank_emote} {p[0].capitalize()} {p[1]} - {p[3]} {'**C**' if p[4] else ''}\n"
        await interaction.channel.send(team_message)
    await interaction.followup.send("Completed.")


########## OLD CODE vvv
"""

@tree.command(
    name='empty_category',
    description='removes all channels in category', 
    guild=discord.Object(id=server_id))
@app_commands.describe(category='Kategori att tömma')
async def empty_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    await util.empty_category(interaction, category)

#commands to remove old text channels belonging to teams
@tree.command(
        name='clear_text_channels', 
        description='Removes old text channels', 
        guild=discord.Object(id=server_id))
@app_commands.describe(this_category='Kategorin du vill rensa', excempt_channel='Kanal att låta stå kvar')
async def clear_text_channels(interaction: discord.Interaction, this_category: discord.CategoryChannel, excempt_channel: discord.TextChannel):
    await util.clear_text_channels(interaction, this_category, excempt_channel)

@tree.command(
    name='clear_categoryless',
    description='removes all channels without a category', 
    guild=discord.Object(id=server_id))
async def clear_categoryless(interaction: discord.Interaction):
    await util.clear_categoryless(interaction)

"""


async def main():
    """Runs client that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(check_updates(), client.start(token))


asyncio.run(main())
# asyncio.run(check_updates())
# client.run(token)
