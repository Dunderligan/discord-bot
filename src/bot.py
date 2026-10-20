# https://discordpy.readthedocs.io/en/latest/api.html
import asyncio

import discord
from discord.ext import commands

from cogs.checkin import CheckinCog
from cogs.config import ConfigCog
from cogs.setup import SetupCog
from cogs.youtube_integration import YoutubeCog
from configuration import Configuration, Suite

configuration: Configuration = Configuration()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot: commands.Bot = commands.Bot(command_prefix=None, intents=intents)
guild: discord.Guild = discord.Object(id=configuration.server_id)


async def setup_hook() -> None:
    """Called once when the bot is ready."""
    suite: Suite = Suite(configuration, bot)

    cogs = [CheckinCog, SetupCog, ConfigCog, YoutubeCog]
    for c in cogs:
        await bot.add_cog(c(suite))

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
    await asyncio.gather(bot.start(configuration.token))


asyncio.run(main())
