# https://discordpy.readthedocs.io/en/latest/api.html
import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from checkin import CheckinModal
from config import ConfigCog, load_config
from youtube_integration import YoutubeCog

load_dotenv()
token = os.getenv("TOKEN")
api_endpoint = os.getenv("API_ENDPOINT")
server_id: int = int(os.getenv("SERVER_ID"))

if token is None or api_endpoint is None or server_id is None:
    e = "One or more environment variables are missing. Please check your .env file."
    print(f"Error loading environment variables: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot: commands.Bot = commands.Bot(command_prefix=None, intents=intents)
#client: discord.Client = discord.Client(intents=intents)
#tree = app_commands.CommandTree(client=client)

guild: discord.Guild = discord.Object(id=server_id)

config = load_config()


async def setup_hook() -> None:
    """Called once when the bot is ready."""
    await bot.add_cog(ConfigCog(bot, config))
    await bot.add_cog(YoutubeCog(bot))
    #await bot.tree.sync(guild=guild)
    await bot.tree.sync()
    print(f"We have logged in as {bot.user}")


bot.setup_hook = setup_hook


@bot.tree.command(description="Replies with Pong!", guild=guild)
async def ping(interaction: discord.Interaction):
    """A simple command that replies with Pong! when the user types /ping."""
    print(f"Received ping command from {interaction.user}")
    await interaction.response.send_message("Pong!")


@bot.tree.command(description="Checka in som spelare för denna säsong.", guild=guild)
async def checkin(interaction: discord.Interaction):
    """Command to be used by players to check in before each season, confirming they are in the discord server and linking their battletag and discord-ids."""
    print(f"Recieved checkin command from {interaction.user}")
    await interaction.response.send_modal(CheckinModal())


async def main():
    """Runs bot that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(bot.start(token))


asyncio.run(main())
