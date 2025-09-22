#https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
import psycopg2
from dotenv import load_dotenv
from discord import app_commands

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
                   d.name as division_name
                   FROM roster r 
                   JOIN "group" g ON g.id = r.group_id
                   JOIN division d ON d.id = g.division_id 
                   WHERE season_slug = '{season}' 
                   ORDER BY division_name, r.name
                   LIMIT 3
                   """)
    teams = cursor.fetchall()

    for t in teams:
        team_role = await create_team_role(interaction.guild, t[0])
        team_text_channel = await create_text_channel(interaction.guild, t[0], team_role, text_category)
        await team_text_channel.send(f"<@&{team_role.id}> \nVälkommen till er nya kanal! Här kommer er direktkontakt med admins ske.")
        await create_voice_channel(interaction.guild, t[0], team_role, t[1])
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
    cursor.execute(f"""SELECT 
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
@app_commands.describe(category="Kategor i att tömma")
async def empty_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    await interaction.response.defer()
    i = 0
    for c in category.channels:
        await c.delete()
        i += 1
    await category.delete()
    await interaction.followup.send(f"Finished removing {i} channels.")

#commands to remove old text channels belonging to teams
@tree.command(
        name="clear_text_channels", 
        description="Removes old text channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(this_category="Kategorin du vill rensa", excempt_channel="Kanal att låta stå kvar")
async def clear_text_channels(interaction: discord.Interaction, this_category: discord.CategoryChannel, excempt_channel: discord.TextChannel):
    await interaction.response.defer()
    if this_category != None:
        for c in this_category.text_channels:
            if c != excempt_channel:
                await c.delete()
    await interaction.followup.send(f"Finished clearing channels.")

@tree.command(
    name="clear_categoryless",
    description="removes all channels without a category", 
    guild=discord.Object(id=server_id))
async def clear_categoryless(interaction: discord.Interaction):
    await interaction.response.defer()
    i = 0
    for c in interaction.guild.voice_channels:
        if c.category == None:
            await c.delete()
            i += 1
    await interaction.followup.send(f"Finished removing {i} channels.")

#debug command to check order roles are being checked in
@tree.command(
    name="print_roles",
    description="prints all roles", 
    guild=discord.Object(id=server_id))
async def print_roles(interaction: discord.Interaction):
    message = ""
    for r in interaction.guild.roles:
        message += r.name + "\n"
    await interaction.response.send_message(message)
        
client.run(token)