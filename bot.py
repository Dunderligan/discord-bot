#https://discordpy.readthedocs.io/en/latest/api.html
import os
import discord
import util
import datetime
import psycopg2
import requests
import typst
import json
import enum
from dotenv import load_dotenv
from discord import app_commands

DIVISIONS: int = 3
SEASONS: int = 7

RANKS: list = ['bronze', 'silver', 'guld', 'plat', 'dia', 'master', 'gm', 'champion']

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

stop_role = 'LAG_ROLLER_UNDER'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    cursor.execute(f'SELECT name FROM division')

    global DIVISIONS
    DIVISIONS = cursor.fetchall()
    await tree.sync(guild=discord.Object(id=server_id))

@tree.command(
        name='remove_old_objects', 
        description='Removes all old objects of a given type, that has previously been created by this bot.', 
        guild=discord.Object(id=server_id))
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

# TODO make admin only
@tree.command(
        name='create_new_objects', 
        description='Creates a new role, text channel, and voice channel for each team in the given season.', 
        guild=discord.Object(id=server_id))
@app_commands.describe(season="Season to get teams from.")
async def create_new_objects(interaction: discord.Interaction, season: str) -> None:
    await interaction.response.defer()
    teams = get_teams(season)
    new_objects = {"text": [], "voice": [], "roles": []}

    for t in teams:
        formatted_name = format_name(t[0])
        new_role: discord.Role = await create_new_role(interaction.guild, formatted_name)
        new_objects["roles"].append(new_role.id)

        # TODO solve where text channels should be placed
        new_text_channel: discord.TextChannel = await create_text_channel(interaction.guild, formatted_name, new_role)
        new_objects["text"].append(new_text_channel.id)

        # TODO replace with typst image?
        embed: discord.Embed = discord.Embed(title = formatted_name)
        embed.set_image(url = get_team_logo_link(t[2], 256))
        embed.description = f"Välkommen till ert lags kanal! Här kommer er direktkontakt med admins ske.\n<@&{new_role.id}>"
        await new_text_channel.send(embed = embed)

        new_voice_channel: discord.VoiceChannel = await create_voice_channel(interaction.guild, formatted_name, new_role, t[1])
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
                    ORDER BY division_name, r.name""")
    teams = cursor.fetchall()
    return teams

def format_name(name: str) -> str:
    # TODO format name to make it discord-friendly
    return name

########## OLD CODE vvv

async def create_new_role(guild: discord.Guild, team: str) -> discord.Role:
    team_name = team
    new_role = await guild.create_role(name=f'[{team_name}]')
    return new_role

async def create_text_channel(guild: discord.Guild, team: str, new_role: discord.Role, text_category: discord.CategoryChannel) -> discord.TextChannel:
    overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            new_role: discord.PermissionOverwrite(view_channel=True),
            guild.self_role: discord.PermissionOverwrite(view_channel=True)
        }
    return await guild.create_text_channel(team, category=text_category, overwrites=overwrites)

async def create_voice_channel(guild: discord.Guild, team: str, new_role: discord.Role, division: str) -> discord.VoiceChannel:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
        new_role: discord.PermissionOverwrite(view_channel=True,connect=True),
        guild.self_role: discord.PermissionOverwrite(view_channel=True,connect=True)
    }
    category = discord.utils.get(guild.categories, name=division)
    if not category:
        category = await guild.create_category(division)
    return await guild.create_voice_channel(team, category=category, overwrites=overwrites)

async def create_emote(interaction: discord.Interaction, team: str, teamid: str):
    image = requests.get(get_team_logo_link(teamid, 128)).content
    await interaction.guild.create_custom_emoji(name = team.replace('+','_').replace('-','_'), image = image)
    
def get_team_logo_link(team: str, size: int) -> str:
    return f'https://cdn.kesomannen.com/cdn-cgi/image/format=png,fit=scale-down,width={size}/dunderligan/logos/{team}.png'
    

@tree.command(
        name='print_roster', 
        description='Prints roster for given team', 
        guild=discord.Object(id=server_id))
async def print_roster(interaction: discord.Interaction, team: str):
    await interaction.response.defer()
    roster_message: str = '
    cursor.execute(f'
                    SELECT p.name AS 'battletag', p.rank AS 'rank', p.role AS 'role'
                   FROM team
                    ')

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

    await interaction.channel.send(f'{team.capitalize()}\n')
    
    await interaction.followup.send('Finished!')


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

    division_scores: dict[str: dict[str: int]] = {}
    for match in matches:
        if not match[0] in division_scores:
            division_scores[match[0]] = {}

        if division_scores[match[0]].get(match[3]):
            division_scores[match[0]][match[3]] += match[1]
        else:
            division_scores[match[0]][match[3]] = match[1]

        if division_scores[match[0]].get(match[4]):
            division_scores[match[0]][match[4]] += match[2]
        else:
            division_scores[match[0]][match[4]] = match[2]
    
    tables: dict[str: str] = {}
    for division in division_scores:
        sorted_scores = {}
        for key in sorted(division_scores[division], key=division_scores[division].get, reverse=True):
            sorted_scores[key] = division_scores[division][key]
        division_scores[division] = sorted_scores

        #tables[division] = '
        embed: discord.Embed = discord.Embed(title=f'Säsong {season} - {division}')
        teams: str = '
        scores: str = '
        winlossdraws: str = '

        for team in division_scores[division]:
            score = division_scores[division][team]
            #tables[division] += f'{team}: {score} poäng | {score}W | {9-score}L\n'
            teams += f'{team}\n'
            winlossdraws += f'{score}-{9-score}-0\n'
            scores += f'{score}p\n'
            
        embed.add_field(name='Lag', value=f'{teams}', inline=True)
        embed.add_field(name='W/L/D', value=f'{winlossdraws}', inline=True)
        embed.add_field(name='Poäng', value=f'{scores}', inline=True)
        embed.timestamp = datetime.datetime.now()
        await interaction.channel.send(embed=embed)

    #for division in tables:
    #    await interaction.channel.send(f'&\n**{division}**:\n{tables[division]}')
    await interaction.followup.send('Finished!')

#command to create new text channels for the teams; currently creating team roles as well, which will be moved to its own function
@tree.command(
        name='create_channels', 
        description='Creates text channels', 
        guild=discord.Object(id=server_id))
@app_commands.describe(destination_category='ID till kategori som kanaler ska ligga under', season='säsong lag hämtas från')
async def create_text_channels(interaction: discord.Interaction, destination_category: str, season:str):
    await interaction.response.defer()
    selected_category = discord.utils.get(interaction.guild.categories, name=destination_category)
    cursor.execute(f'SELECT name FROM roster WHERE season_slug = '{season}' LIMIT 10')
    teams = cursor.fetchall()
    
    for t in teams:
        new_role = create_new_role(interaction, t[0])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            new_role: discord.PermissionOverwrite(view_channel=True),
            interaction.guild.self_role: discord.PermissionOverwrite(view_channel=True)
        }
        team_name = new_role.name

        new_channel = await interaction.guild.create_text_channel(team_name, category=selected_category, overwrites=overwrites)
        if new_channel:
            await new_channel.send(f'Välkommen till {team_name} klubbstuga! Här kommer admins kontakta er med viktig information, och här kan även ni skriva direkt till dem vid funderingar.')

    team_amount = len(teams)
    await interaction.followup.send(f'Finished creating {team_amount} channels.')

#command to remove old team roles from previous seasons
#team roles has to start with '[' to be removed, as well as lie underneath the stop_role
@tree.command(
    name='remove_new_roles',
    description='removes old team roles', 
    guild=discord.Object(id=server_id))
async def remove_new_roles(interaction: discord.Interaction):
    await interaction.response.defer()
    c = 0
    for r in interaction.guild.roles:
        if r.name == stop_role:
            break
        elif r == interaction.guild.default_role:
            continue
        elif r.name.startswith('['):
            print(f'Deleted {r.name}!')
            await r.delete()
            c += 1
    await interaction.followup.send(f'Finished removing {c} team roles.')
    
@tree.command(
        name='create_voice_channels', 
        description='Creates voice channels', 
        guild=discord.Object(id=server_id))
@app_commands.describe(season='säsong lag hämtas från')
async def create_voice_channels(interaction: discord.Interaction, season:str):
    await interaction.response.defer()
    cursor.execute(f'
                    SELECT 
                        r.name, 
                        d.name as division_name
                    FROM roster r 
                        JOIN 'group' g ON g.id = r.group_id
                        JOIN division d ON d.id = g.division_id 
                    WHERE season_slug = '{season}' 
                    ORDER BY division_name, r.name
                   ')
    teams = cursor.fetchall()

    division_categories: dict[str: discord.CategoryChannel] = {}
    for t in teams:
        new_role = discord.utils.get(interaction.guild.roles, name=f'[{t[0]}]')
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
            new_role: discord.PermissionOverwrite(view_channel=True,connect=True),
            interaction.guild.self_role: discord.PermissionOverwrite(view_channel=True,connect=True)
        }
        if not division_categories.get(t[1]):
            category = discord.utils.get(interaction.guild.categories, name=t[1])
            if not category:
                category = await interaction.guild.create_category(t[1])
            division_categories[t[1]] = category
        print(t[0], division_categories[t[1]])
        await interaction.guild.create_voice_channel(t[0], category=division_categories[t[1]], overwrites=overwrites)
    await interaction.followup.send(f'Finished creating {len(teams)} voice channels.')



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

#debug command to check order roles are being checked in
@tree.command(
    name='print_roles',
    description='prints all roles', 
    guild=discord.Object(id=server_id))
async def print_roles(interaction: discord.Interaction):
    await util.print_roles(interaction)
        
client.run(token)