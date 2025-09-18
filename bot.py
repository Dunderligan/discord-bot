import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

load_dotenv()
token = os.getenv('TOKEN')
server_id = os.getenv('SERVER_ID')

except_channel = "kaptener"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)



@tree.command(name="create_channels", description="Creates text channels", guild=discord.Object(id=server_id))
@app_commands.describe(destination_category="ID till kategori som kanaler ska ligga under")
async def create_text_channels(interaction: discord.Interaction, destination_category: str):
    selected_category = discord.utils.get(interaction.guild.categories, name=destination_category)
    teams = ["Cool Sharks", "Missarna på Tunnelbanan", "Ocustik", "Njukas+4"]
    for t in teams:
        channel_name = t
        await interaction.guild.create_text_channel(channel_name, category=selected_category)
    team_amount = len(teams)
    await interaction.response.send_message(f"Finished creating {team_amount} channels.")

@tree.command(name="clear_channels", description="Removes old text channels", guild=discord.Object(id=server_id))
@app_commands.describe(this_category="Kategorin du vill rensa")
async def clear_text_channels(interaction: discord.Interaction, this_category: str):
    current_category = discord.utils.get(interaction.guild.categories, name=this_category)
    if current_category != None:
        for c in current_category.text_channels:
            if c.name != except_channel:
                await c.delete()
    await interaction.response.send_message(f"Finished clearing channels.")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=server_id))
        
client.run(token)