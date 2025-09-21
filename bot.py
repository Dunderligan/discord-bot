#https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

load_dotenv()
token = os.getenv('TOKEN')
server_id = os.getenv('SERVER_ID')

except_channel = "kaptener"
stop_role = "LAG_ROLLER_UNDER"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=server_id))

#command to create new text channels for the teams; currently creating team roles as well, which will be moved to its own function
@tree.command(
        name="create_channels", 
        description="Creates text channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(destination_category="ID till kategori som kanaler ska ligga under")
async def create_text_channels(interaction: discord.Interaction, destination_category: str):    
    selected_category = discord.utils.get(interaction.guild.categories, name=destination_category)
    teams = ["Cool Sharks", "Missarna på Tunnelbanan", "Ocustik", "Njukas+4"]
    for t in teams:
        await interaction.guild.create_role(name=f"[{t}]")
        team_role = discord.utils.get(interaction.guild.roles, name=f"[{t}]")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
            team_role: discord.PermissionOverwrite(view_channel=True,connect=True),
            interaction.guild.self_role: discord.PermissionOverwrite(view_channel=True,connect=True)
        }

        channel_name = t
        await interaction.guild.create_text_channel(channel_name, category=selected_category, overwrites=overwrites)
    team_amount = len(teams)
    await interaction.response.send_message(f"Finished creating {team_amount} channels.")

#commands to remove old text channels belonging to teams
@tree.command(
        name="clear_channels", 
        description="Removes old text channels", 
        guild=discord.Object(id=server_id))
@app_commands.describe(this_category="Kategorin du vill rensa")
async def clear_text_channels(interaction: discord.Interaction, this_category: str):
    await interaction.response.defer()
    current_category = discord.utils.get(interaction.guild.categories, name=this_category)
    if current_category != None:
        for c in current_category.text_channels:
            if c.name != except_channel:
                await c.delete()
    await interaction.followup.send(f"Finished clearing channels.")

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