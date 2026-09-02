# https://discordpy.readthedocs.io/en/latest/api.html
import asyncio
import datetime
import os
import sys

import discord
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv

import youtube_integration as yt
from checkin import CheckinModal

load_dotenv()
token = os.getenv("TOKEN")
api_endpoint = os.getenv("API_ENDPOINT")
server_id: int = int(os.getenv("SERVER_ID"))
yt_token = os.getenv("YOUTUBE_API_KEY")
yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
yt_notification_channel_id = os.getenv("YOUTUBE_NOTIFICATION_CHANNEL_ID")

if token is None or api_endpoint is None or server_id is None or yt_token is None or yt_channel_id is None or yt_notification_channel_id is None:
    e = "One or more environment variables are missing. Please check your .env file."
    print(f"Error loading environment variables: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot: commands.Bot = commands.Bot(command_prefix=None, intents=intents)
#client: discord.Client = discord.Client(intents=intents)
#tree = app_commands.CommandTree(client=client)

yt_integration = yt.YoutubeIntegration(yt_token)
yt_integration.monitor_channel(yt_channel_id)

guild: discord.Guild = discord.Object(id=server_id)


@bot.event
async def on_new_videos(videos):
    """Callback function that is called when new videos are detected on the monitored YouTube channel."""
    channel = discord.utils.get(
        bot.get_all_channels(), id=int(yt_notification_channel_id)
    )
    if channel is None:
        print(
            f"Could not find channel with ID {yt_notification_channel_id}. Please check the ID and try again."
        )
        return
    for video in videos:
        await channel.send(
            f"En ny video publicerades precis på Dunderligans kanal: **{video.title}**\n{video.url}"
        )


async def setup_hook() -> None:
    """Called once when the bot is ready."""
    await bot.tree.sync(guild=guild)
    print(f"We have logged in as {bot.user}")
    yt_integration.add_new_video_callback(on_new_videos)


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


@tasks.loop(hours=1)
async def check_for_videos() -> None:
    await yt_integration.check_for_new_videos()


async def main():
    """Runs bot that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(bot.start(token))


asyncio.run(main())
