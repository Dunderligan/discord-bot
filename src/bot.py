# https://discordpy.readthedocs.io/en/latest/api.html
import asyncio
import datetime
import os
import sys

import discord
from discord import app_commands
from dotenv import load_dotenv

import youtube_integration as yt

load_dotenv()
token = os.getenv("TOKEN")
server_id: int = int(os.getenv("SERVER_ID"))
yt_token = os.getenv("YOUTUBE_API_KEY")
yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
yt_notification_channel_id = os.getenv("YOUTUBE_NOTIFICATION_CHANNEL_ID")

if token is None or server_id is None or yt_token is None or yt_channel_id is None or yt_notification_channel_id is None:
    e = "One or more environment variables are missing. Please check your .env file."
    print(f"Error loading environment variables: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

yt_integration = yt.YoutubeIntegration(yt_token)
yt_integration.monitor_channel(yt_channel_id)


@client.event
async def on_new_videos(videos):
    """Callback function that is called when new videos are detected on the monitored YouTube channel."""
    channel = discord.utils.get(
        client.get_all_channels(), id=int(yt_notification_channel_id)
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


@client.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"We have logged in as {client.user}")
    yt_integration.add_new_video_callback(on_new_videos)
    await tree.sync(guild=discord.Object(id=server_id))


@tree.command(name="ping", description="Replies with Pong!", guild=discord.Object(id=server_id))
async def ping(interaction: discord.Interaction):
    """A simple command that replies with Pong! when the user types /ping."""
    await interaction.response.send_message("Pong!")


async def check_updates():
    """Checks for updates on YouTube channel every hour."""
    while True:
        # Calculates time until next check at 5 minutes past whole hour
        # 5 past because many videos are published at 12.00, 13.00 etc, and checking them
        # right at the hour might miss them
        time_until_next_check = datetime.datetime.now().replace(minute=5, second=0, microsecond=0) + datetime.timedelta(hours=1) - datetime.datetime.now()
        await asyncio.sleep(time_until_next_check.total_seconds())
        print(f"Checking for updates at {datetime.datetime.now()}")
        await yt.check_for_new_videos()


async def main():
    """Runs client that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(client.start(token), check_updates())


asyncio.run(main())
