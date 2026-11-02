from datetime import datetime, timedelta

import discord
from discord.ext import commands

from discord_wrappers.discord_client import DiscordHandler


class Bot:
    def __init__(self, discord_token: str, discord_server_id: int, interface: DiscordHandler):
        self.discord_token = discord_token
        self.guild: discord.Guild = discord.Object(discord_server_id)
        self.interface = interface

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        self.bot: commands.Bot = commands.Bot(command_prefix=None, intents=intents)
        self.bot.setup_hook = self._setup_hook
        self._add_commands()

    async def _setup_hook(self) -> None:
        """Called once when the bot is ready."""
        await self.bot.tree.sync(guild=self.guild)
        print(f"We have logged in as {self.bot.user}")

    async def _start_bot(self) -> None:
        await self.bot.start(self.discord_token)

    def _add_commands(self):
        @self.bot.tree.command(description="Replies with Pong!", guild=self.guild)
        async def ping(interaction: discord.Interaction):
            """A simple command that replies with Pong! when the user types /ping."""
            print(f"Received ping command from {interaction.user}")
            response_time: timedelta = datetime.now().astimezone() - interaction.created_at
            await interaction.response.send_message(f"Ponged 🏓 in {round(response_time.total_seconds(), 2)} seconds")

        @self.bot.tree.command(description="Check in to the current season of Dunderligan.", guild=self.guild)
        async def checkin(interaction: discord.Interaction):
            """Asks the user for their battletag, and then tries to check them in."""
            print(f"Recieved checkin command from {interaction.user}")
            await self.interface.checkin_user(interaction)

    def get_tasks(self):
        return [self._start_bot()]