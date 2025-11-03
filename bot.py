#https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import json
import psycopg2
import requests
import datetime
import typst
import enum
from dotenv import load_dotenv
from discord import app_commands

class CLEARABLE_OBJECT(str, enum.Enum):
    VoiceChannels = 'VOICE'
    TextChannels = 'TEXT'
    Roles = 'ROLES'
    All = 'ALL'
CLEAR_FROM_PATH: str = 'old_objects.json' # contains the id to text-, voice channels, and roles, divided in a dictionary

load_dotenv()
token = os.getenv('TOKEN')
server_id = os.getenv('SERVER_ID')
postgres_link = os.getenv('POSTGRES_LINK')

db_conn = psycopg2.connect(postgres_link)
cursor = db_conn.cursor()

admin_role_id: int = int(os.getenv('ADMIN_ID'))
text_category: discord.CategoryChannel

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=server_id))

@tree.command(
        name='remove_old_objects', 
        description='Removes all old objects of a given type, that has previously been created by this bot.', 
        guild=discord.Object(id=server_id))
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(alternative="Objects to remove")
async def remove_old_objects(interaction: discord.Interaction, alternative: CLEARABLE_OBJECT) -> None:
    await interaction.response.defer()
    old_objects = load_old_objects()
    if old_objects:
        if alternative in ['VOICE', 'ALL']:
            for o in old_objects["voice"]:
                voice_channel = discord.utils.find(lambda v: v.id == o, interaction.guild.voice_channels)
                if voice_channel:
                    await voice_channel.delete()
                else:
                    print(f"Couldn't find voice channel with ID: {o}")
            old_objects["voice"] = []

        if alternative in ['TEXT', 'ALL']:
            for o in old_objects["text"]:
                text_channel = discord.utils.find(lambda t: t.id == o, interaction.guild.text_channels)
                if text_channel:
                    await text_channel.delete()
                else:
                    print(f"Couldn't find text channel with ID: {o}")
            old_objects["text"] = []

        if alternative in ['ROLES', 'ALL']:
            for o in old_objects["roles"]:
                role = discord.utils.find(lambda r: r.id == o, interaction.guild.roles)
                if role:
                    await role.delete()
                else:
                    print(f"Couldn't find role with ID: {o}")
            old_objects["roles"] = []
        save_new_objects(old_objects)
        await interaction.followup.send(f'Finished removing all old {alternative} objects.')
    else:
        await interaction.followup.send(f'Did not find any objects in {CLEAR_FROM_PATH} to remove.')

def load_old_objects() -> dict:
    if os.path.isfile(CLEAR_FROM_PATH):
        with open(CLEAR_FROM_PATH, 'r') as file:
            old_objects: dict = json.load(file)
            return old_objects
    else:
        old_objects: dict = {}
        return old_objects

@tree.command(
        name='create_new_objects', 
        description='Creates a new role, text channel, and voice channel for each team in the given season.', 
        guild=discord.Object(id=server_id))
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(season="Season to get teams from.")
async def create_new_objects(interaction: discord.Interaction, season: str) -> None:
    await interaction.response.defer()
    text_category: discord.CategoryChannel = discord.utils.find(lambda category: category.id == int(os.getenv('TEXT_CATEGORY')), interaction.guild.categories)
    teams = get_teams(season)
    new_objects = {"text": [], "voice": [], "roles": []}

    for t in teams:
        # creates a role
        formatted_name = format_name(t[0])
        new_role: discord.Role = await interaction.guild.create_role(name=f'{t[0]}')
        new_objects["roles"].append(new_role.id)

        # creates a text channel in assigned category
        channel_permissions: dict = get_role_permissions(interaction.guild, new_role)
        new_text_channel: discord.TextChannel = await interaction.guild.create_text_channel(formatted_name, category=text_category, overwrites=channel_permissions)
        new_objects["text"].append(new_text_channel.id)

        # sends embed in newly created text channel
        embed: discord.Embed = discord.Embed(title = formatted_name)
        embed.set_image(url = get_team_logo_link(t[2], 256))
        embed.description = f"Välkommen till ert lags kanal! Här kommer er direktkontakt med admins ske.\n<@&{new_role.id}>"
        await new_text_channel.send(embed = embed)

        # creates a voice channel
        voice_category = discord.utils.get(interaction.guild.categories, name=t[1])
        if not voice_category:
            voice_category = await interaction.guild.create_category(t[1])
        new_voice_channel: discord.VoiceChannel = await interaction.guild.create_voice_channel(t[0], category=voice_category, overwrites=channel_permissions)
        new_objects["voice"].append(new_voice_channel.id)

    save_new_objects(new_objects)
    await interaction.followup.send('Finished creating new objects.')

def save_new_objects(objects: dict) -> None:
    with open(CLEAR_FROM_PATH, 'w') as file:
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
    admin_role: discord.Role = discord.utils.find(lambda r: r.id == admin_role_id, guild.roles)
    overwrites: dict[discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
        role: discord.PermissionOverwrite(view_channel=True, connect=True),
        admin_role: discord.PermissionOverwrite(view_channel=True, connect=True)
    }
    return overwrites

def get_team_logo_link(team: str, size: int) -> str:
    return f'https://cdn.kesomannen.com/cdn-cgi/image/format=png,fit=scale-down,width={size}/dunderligan/logos/{team}.png'

def get_team_thumbnail(team: str) -> str:
    image_path = f"team_thumbnails/{format_name(team)}.png"
    if not os.path.isfile(image_path):
        image_formats = ("image/png", "image/jpeg", "image/jpg")
        r = requests.get(get_team_logo_link(team, 32))
        if r.headers["content-type"] in image_formats:
            image = r.content
            with open(image_path, "wb") as file:
                file.write(image)
        else:
            return "/team_thumbnails/placeholder-team.jpg"
    return image_path

@tree.command(
        name='output_standing', 
        description='Outputs standing for division', 
        guild=discord.Object(id=server_id))
async def output_standing(interaction: discord.Interaction, division: int) -> None:
    await interaction.response.defer()
    cursor.execute(f"""
                    SELECT 
                        d.name AS "division_name",
                        m.team_a_score,
                        m.team_b_score,
                        ra.name AS "roster_a_name",
                        rb.name AS "roster_b_name",
                        ra.id AS "roster_a_id",
                        rb.id AS "roster_b_id"
                    FROM division d
                        JOIN "group" g ON g.division_id = d.id
                        JOIN "match" m ON m.group_id = g.id
                        JOIN "roster" ra ON m.roster_a_id = ra.id
                        JOIN "roster" rb ON m.roster_b_id = rb.id
                        JOIN "season" s ON d.season_id = s.id
                    WHERE s.slug = 'test'
                        AND d.name = 'Division {division}'
                   """)
    matches = cursor.fetchall()

    teams: dict[str: dict[str: int]] = {} # första int är teams, andra id
    for match in matches:
        first_team = match[3]
        second_team = match[4]
        first_points = match[1]
        second_points = match[2]

        if not teams.get(first_team):
            teams[first_team] = {"score": 0, "id": 0}
        if not teams.get(second_team):
            teams[second_team] = {"score": 0, "id": 0}

        teams[first_team]["score"] = teams[first_team]["score"] + first_points if teams.get(first_team) else first_points
        teams[second_team]["score"] = teams[second_team]["score"] + second_points if teams.get(second_team) else second_points

        teams[first_team]["id"] = match[5]
        teams[second_team]["id"] = match[6]
    
    sorted_teams = {}
    for team in sorted(teams, key = lambda t: teams.get(t)["score"], reverse = True):
        sorted_teams[team] = teams[team]

    standings = []
    for team, data in sorted_teams.items():
        (score, id) = (data["score"], data["id"])
        standings.append((get_team_thumbnail(id), team, f"{score}/{9-score}/0", f"{score}p"))
    # "standings": [(namn, x/x/x, xp)]

    current_time = str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"))
    season = "7"
    document_data = {
        "standings": standings, 
        "division": division, 
        "season": season
        }
    sys_inputs = {"document_data": json.dumps(document_data), "time": json.dumps(current_time)}

    TYPST_FILE = f"standings.typ"
    OUTPUT_FILE = f"generated_images/standing-div-{division}.png" 
    typst.compile(input = TYPST_FILE, output = OUTPUT_FILE, format = "png", sys_inputs = sys_inputs, ppi = 144.0)
    with open(OUTPUT_FILE, 'rb') as image:
        await interaction.channel.send(file = discord.File(image))

    await interaction.followup.send("Sent standings!")

async def print_rosters(interaction: discord.Interaction, division: int) -> None:
    pass

########## OLD CODE vvv
"""

@tree.command(
        name='print_roster', 
        description='Prints roster for given team', 
        guild=discord.Object(id=server_id))
async def print_roster(interaction: discord.Interaction, team: str):

@tree.command(
        name='print_standing', 
        description='Prints standing for chosen division', 
        guild=discord.Object(id=server_id))
async def print_standing(interaction: discord.Interaction, season: app_commands.Range[int, 1, SEASONS+1], division: app_commands.Range[int, 1, DIVISIONS+1]):
    await interaction.response.defer()
    cursor.execute(f'
                    SELECT 
                        d.name AS 'division_name',
                        m.team_a_score,
                        m.team_b_score,
                        ra.name AS 'roster_a_name',
                        rb.name AS 'roster_b_name'
                    FROM division d
                        JOIN 'group' g ON g.division_id = d.id
                        JOIN 'match' m ON m.group_id = g.id
                        JOIN 'roster' ra ON m.roster_a_id = ra.id
                        JOIN 'roster' rb ON m.roster_b_id = rb.id
                        JOIN 'season' s ON d.season_id = s.id
                    WHERE s.slug = 'test'
                        AND d.name = 'Division {division}'
                   ')
    matches = cursor.fetchall()

    division_teams: dict[str: dict[str: int]] = {}
    for match in matches:
        if not match[0] in division_teams:
            division_teams[match[0]] = {}

        if division_teams[match[0]].get(match[3]):
            division_teams[match[0]][match[3]] += match[1]
        else:
            division_teams[match[0]][match[3]] = match[1]

        if division_teams[match[0]].get(match[4]):
            division_teams[match[0]][match[4]] += match[2]
        else:
            division_teams[match[0]][match[4]] = match[2]
    
    tables: dict[str: str] = {}
    for division in division_teams:
        sorted_teams = {}
        for key in sorted(division_teams[division], key=division_teams[division].get, reverse=True):
            sorted_teams[key] = division_teams[division][key]
        division_teams[division] = sorted_teams

        #tables[division] = '
        embed: discord.Embed = discord.Embed(title=f'Säsong {season} - {division}')
        teams: str = '
        teams: str = '
        winlossdraws: str = '

        for team in division_teams[division]:
            score = division_teams[division][team]
            #tables[division] += f'{team}: {score} poäng | {score}W | {9-score}L\n'
            teams += f'{team}\n'
            winlossdraws += f'{score}-{9-score}-0\n'
            teams += f'{score}p\n'
            
        embed.add_field(name='Lag', value=f'{teams}', inline=True)
        embed.add_field(name='W/L/D', value=f'{winlossdraws}', inline=True)
        embed.add_field(name='Poäng', value=f'{teams}', inline=True)
        embed.timestamp = datetime.datetime.now()
        await interaction.channel.send(embed=embed)

    #for division in tables:
    #    await interaction.channel.send(f'&\n**{division}**:\n{tables[division]}')
    await interaction.followup.send('Finished!')

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
    
client.run(token)