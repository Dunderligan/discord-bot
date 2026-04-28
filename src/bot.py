# https://discordpy.readthedocs.io/en/latest/api.html
import discord
import os

import datetime
import asyncio

import youtube_integration as youtube_integration

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
try:
    token = os.getenv("TOKEN")
    server_id: int = int(os.getenv("SERVER_ID"))
    yt_token = os.getenv("YOUTUBE_API_KEY")
    yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
    yt_notification_channel_id = os.getenv("YOUTUBE_NOTIFICATION_CHANNEL_ID")
except Exception as e:
    print(f"Error loading environment variables: {e}")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

yt_integration = youtube_integration.YoutubeIntegration(yt_token)
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


@client.event
@tree.command(name="ping", description="Replies with Pong!", guild=discord.Object(id=server_id))
async def ping(interaction: discord.Interaction):
    """A simple command that replies with Pong! when the user types /ping."""
    await interaction.response.send_message("Pong!")


async def check_updates():
    """Checks for updates on YouTube channel every hour."""
    while True:
        await asyncio.sleep(3600)  # Updates every hour
        print(f"Checking for updates at {datetime.datetime.now()}")
        await yt_integration.check_for_new_videos()


async def main():
    """Runs client that checks for user-commands and server-side updates in parallell"""
    await asyncio.gather(client.start(token), check_updates())


asyncio.run(main())
