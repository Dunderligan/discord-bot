import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

load_dotenv()
token = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

server_id = 1417952384809963564

bot = commands.Bot(command_prefix="$", description="Tournament host", intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
        name="create_channels",
        description="Creates text channels",
        guild=discord.Object(id=server_id)
)
async def create_text_channels(
    interaction: discord.Interaction 
):
    teams = ["Cool Sharks", "Missarna på Tunnelbanan", "Ocustik", "Njukas+4"]
    
    for t in teams:
        channel_name = t
        await interaction.guild.create_text_channel(channel_name)
    team_amount = len(teams)
    await interaction.response.send_message("Finished creating {team_amount} channels.")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=server_id))
        
client.run(token)