#https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import psycopg2
import util
import datetime
import requests
from dotenv import load_dotenv
from discord import app_commands

DIVISIONS: int = 3
SEASONS: int = 7

load_dotenv()
token = os.getenv('TOKEN')
server_id = os.getenv('SERVER_ID')
postgres_link = os.getenv('POSTGRES_LINK')

db_conn = psycopg2.connect(postgres_link)
cursor = db_conn.cursor()

stop_role = "LAG_ROLLER_UNDER"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    cursor.execute(f"SELECT name FROM division")

    global DIVISIONS
    DIVISIONS = cursor.fetchall()
    await tree.sync(guild=discord.Object(id=server_id))

@tree.command(
        name="setup_teams", 
        description="Creates roles, text, and voice channels.", 
        guild=discord.Object(id=server_id))
@app_commands.describe(text_category="Kategori för textkanaler.", season="Säsong lag hämtas från.")
async def setup_teams(interaction: discord.Interaction, text_category: discord.CategoryChannel, season:str):
    await interaction.response.defer()

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
                   LIMIT 8
                   """)
    teams = cursor.fetchall()

    for t in teams:
        team_role = await create_team_role(interaction.guild, t[0])
        team_text_channel = await create_text_channel(interaction.guild, t[0], team_role, text_category)
        
        embed: discord.Embed = discord.Embed(title=t[0])
        embed.set_image(url=get_team_logo_link(t[2], 256))
        embed.description = f"Välkommen till er nya kanal! Här kommer er direktkontakt med admins ske.\n<@&{team_role.id}>"
        await team_text_channel.send(embed=embed)
        await create_voice_channel(interaction.guild, t[0], team_role, t[1])
        await create_emote(interaction, t[3], t[2])
    await interaction.followup.send("Finished setting up server.")

async def create_team_role(guild: discord.Guild, team: str) -> discord.Role:
    team_name = team
    team_role = await guild.create_role(name=f"[{team_name}]")
    return team_role

async def create_text_channel(guild: discord.Guild, team: str, team_role: discord.Role, text_category: discord.CategoryChannel) -> discord.TextChannel:
    overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            team_role: discord.PermissionOverwrite(view_channel=True),
            guild.self_role: discord.PermissionOverwrite(view_channel=True)
        }
    return await guild.create_text_channel(team, category=text_category, overwrites=overwrites)

async def create_voice_channel(guild: discord.Guild, team: str, team_role: discord.Role, division: str) -> discord.VoiceChannel:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
        team_role: discord.PermissionOverwrite(view_channel=True,connect=True),
        guild.self_role: discord.PermissionOverwrite(view_channel=True,connect=True)
    }
    category = discord.utils.get(guild.categories, name=division)
    if not category:
        category = await guild.create_category(division)
    return await guild.create_voice_channel(team, category=category, overwrites=overwrites)

async def create_emote(interaction: discord.Interaction, team: str, teamid: str):
    image = requests.get(get_team_logo_link(teamid, 128)).content
    await interaction.guild.create_custom_emoji(name = team.replace("+","_").replace("-","_"), image = image)
    
def get_team_logo_link(team: str, size: int) -> str:
    return f"https://cdn.kesomannen.com/cdn-cgi/image/format=png,fit=scale-down,width={size}/dunderligan/logos/{team}.png"
    

@tree.command(
        name="print_standing", 
        description="Prints standing for chosen division", 
        guild=discord.Object(id=server_id))
async def print_standing(interaction: discord.Interaction, season: app_commands.Range[int, 1, SEASONS+1], division: app_commands.Range[int, 1, DIVISIONS+1]):
    await interaction.response.defer()
    cursor.execute(f"""
                    SELECT 
                        d.name AS "division_name",
                        m.team_a_score,
                        m.team_b_score,
                        ra.name AS "roster_a_name",
                        rb.name AS "roster_b_name"
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

        #tables[division] = ""
        embed: discord.Embed = discord.Embed(title=f"Säsong {season} - {division}")
        teams: str = ""
        scores: str = ""
        winlossdraws: str = ""

        for team in division_scores[division]:
            score = division_scores[division][team]
            #tables[division] += f"{team}: {score} poäng | {score}W | {9-score}L\n"
            teams += f"{team}\n"
            winlossdraws += f"{score}-{9-score}-0\n"
            scores += f"{score}p\n"
            
        embed.add_field(name="Lag", value=f"{teams}", inline=True)
        embed.add_field(name="W/L/D", value=f"{winlossdraws}", inline=True)
        embed.add_field(name="Poäng", value=f"{scores}", inline=True)
        embed.timestamp = datetime.datetime.now()
        await interaction.channel.send(embed=embed)

    #for division in tables:
    #    await interaction.channel.send(f"&\n**{division}**:\n{tables[division]}")
    await interaction.followup.send("Finished!")

#command to create new text channels for the teams; currently creating team roles as well, which will be moved to its own function
@tree.command(
        name="create_channels", 
        description="Creates text channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(destination_category="ID till kategori som kanaler ska ligga under", season="säsong lag hämtas från")
async def create_text_channels(interaction: discord.Interaction, destination_category: str, season:str):
    await interaction.response.defer()
    selected_category = discord.utils.get(interaction.guild.categories, name=destination_category)
    cursor.execute(f"SELECT name FROM roster WHERE season_slug = '{season}' LIMIT 10")
    teams = cursor.fetchall()
    
    for t in teams:
        team_role = create_team_role(interaction, t[0])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            team_role: discord.PermissionOverwrite(view_channel=True),
            interaction.guild.self_role: discord.PermissionOverwrite(view_channel=True)
        }
        team_name = team_role.name

        new_channel = await interaction.guild.create_text_channel(team_name, category=selected_category, overwrites=overwrites)
        if new_channel:
            await new_channel.send(f"Välkommen till {team_name} klubbstuga! Här kommer admins kontakta er med viktig information, och här kan även ni skriva direkt till dem vid funderingar.")

    team_amount = len(teams)
    await interaction.followup.send(f"Finished creating {team_amount} channels.")

#command to remove old team roles from previous seasons
#team roles has to start with '[' to be removed, as well as lie underneath the stop_role
@tree.command(
    name="remove_team_roles",
    description="removes old team roles", 
    guild=discord.Object(id=server_id))
async def remove_team_roles(interaction: discord.Interaction):
    await interaction.response.defer()
    c = 0
    for r in interaction.guild.roles:
        if r.name == stop_role:
            break
        elif r == interaction.guild.default_role:
            continue
        elif r.name.startswith("["):
            print(f"Deleted {r.name}!")
            await r.delete()
            c += 1
    await interaction.followup.send(f"Finished removing {c} team roles.")
    
@tree.command(
        name="create_voice_channels", 
        description="Creates voice channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(season="säsong lag hämtas från")
async def create_voice_channels(interaction: discord.Interaction, season:str):
    await interaction.response.defer()
    cursor.execute(f"""
                    SELECT 
                        r.name, 
                        d.name as division_name
                    FROM roster r 
                        JOIN "group" g ON g.id = r.group_id
                        JOIN division d ON d.id = g.division_id 
                    WHERE season_slug = '{season}' 
                    ORDER BY division_name, r.name
                   """)
    teams = cursor.fetchall()

    division_categories: dict[str: discord.CategoryChannel] = {}
    for t in teams:
        team_role = discord.utils.get(interaction.guild.roles, name=f"[{t[0]}]")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
            team_role: discord.PermissionOverwrite(view_channel=True,connect=True),
            interaction.guild.self_role: discord.PermissionOverwrite(view_channel=True,connect=True)
        }
        if not division_categories.get(t[1]):
            category = discord.utils.get(interaction.guild.categories, name=t[1])
            if not category:
                category = await interaction.guild.create_category(t[1])
            division_categories[t[1]] = category
        print(t[0], division_categories[t[1]])
        await interaction.guild.create_voice_channel(t[0], category=division_categories[t[1]], overwrites=overwrites)
    await interaction.followup.send(f"Finished creating {len(teams)} voice channels.")



@tree.command(
    name="empty_category",
    description="removes all channels in category", 
    guild=discord.Object(id=server_id))
@app_commands.describe(category="Kategori att tömma")
async def empty_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    await util.empty_category(interaction, category)

#commands to remove old text channels belonging to teams
@tree.command(
        name="clear_text_channels", 
        description="Removes old text channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(this_category="Kategorin du vill rensa", excempt_channel="Kanal att låta stå kvar")
async def clear_text_channels(interaction: discord.Interaction, this_category: discord.CategoryChannel, excempt_channel: discord.TextChannel):
    await util.clear_text_channels(interaction, this_category, excempt_channel)

@tree.command(
    name="clear_categoryless",
    description="removes all channels without a category", 
    guild=discord.Object(id=server_id))
async def clear_categoryless(interaction: discord.Interaction):
    await util.clear_categoryless(interaction)

#debug command to check order roles are being checked in
@tree.command(
    name="print_roles",
    description="prints all roles", 
    guild=discord.Object(id=server_id))
async def print_roles(interaction: discord.Interaction):
    await util.print_roles(interaction)
        
client.run(token)