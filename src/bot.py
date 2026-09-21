# https://discordpy.readthedocs.io/en/latest/api.html
import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from checkin import CheckinCog
from network import Network
from config import Config, ConfigCog, load_config
from youtube_integration import YoutubeCog

load_dotenv()
token = os.getenv("TOKEN")
api_endpoint = os.getenv("API_ENDPOINT")
api_key = os.getenv("API_KEY")
server_id: int = int(os.getenv("SERVER_ID"))

if token is None or api_endpoint is None or server_id is None:
    e = "One or more environment variables are missing. Please check your .env file."
    print(f"Error loading environment variables: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot: commands.Bot = commands.Bot(command_prefix=None, intents=intents)
guild: discord.Guild = discord.Object(id=server_id)


async def setup_hook() -> None:
    """Called once when the bot is ready."""
    config: Config = load_config()
    network: Network = Network(api_endpoint, api_key)
    
    network_cogs = [CheckinCog]
    for c in network_cogs:
        await bot.add_cog(c(bot, config, network))

    other_cogs = [ConfigCog, YoutubeCog]
    for c in other_cogs:
        await bot.add_cog(c(bot, config))

    await bot.tree.sync()
    print(f"We have logged in as {bot.user}")


bot.setup_hook = setup_hook


@bot.tree.command(description="Replies with Pong!", guild=guild)
async def ping(interaction: discord.Interaction):
    """A simple command that replies with Pong! when the user types /ping."""
    print(f"Received ping command from {interaction.user}")
    await interaction.response.send_message("Pong!")


async def main():
    """Runs bot that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(bot.start(token))


asyncio.run(main())
