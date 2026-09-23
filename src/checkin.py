import datetime

import discord
from discord import app_commands
from discord.ext import commands
from network import Network
from requests import HTTPError

import db
from config import Config
from models import Player


class CheckinModal(discord.ui.Modal, title="Incheckning"):
    battletag = discord.ui.TextInput(
        label="Battletag", placeholder="Skriv din battletag här..."
    )

    def __init__(self, callback):
        self.callback = callback
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, str(self.battletag))

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.followup.send(
            "Oj! Ett fel uppstod. Kontakta Admin om det kvarstår.", ephemeral=True
        )
        print(
            f"Error occurred when user {interaction.user.global_name} tried checking in: {error}"
        )


class CheckinResponse:
    discord_id: str
    checked_in_at: datetime.datetime
    player: Player

    def __init__(
        self, discord_id: str, checked_in_at: datetime.datetime, player: Player
    ):
        self.discord_id = discord_id
        self.checked_in_at = checked_in_at
        self.player = player

    def from_json(json: dict):
        return CheckinResponse(
            json.get("discordId"),
            datetime.datetime.fromisoformat(json.get("checkedInAt")),
            Player.from_json(json.get("player")),
        )


class CheckinCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: Config, network: Network):
        self.bot = bot
        self.config = config
        self.network = network

    @app_commands.command(name="checkin", description="Check in as a player to the next season.")
    async def checkin(self, interaction: discord.Interaction):
        """Command to be used by players to check in before each season, confirming they are in the discord server and linking their battletag and discord-ids."""
        print(f"Recieved checkin command from {interaction.user}")
        await interaction.response.send_modal(CheckinModal(self.checkin_player))

    async def checkin_player(
        self, interaction: discord.Interaction, battletag: str
    ) -> None:
        """
        Checks in player into website. Returns a string response to be displayed to the user.
        """
        if not validate_battletag(battletag):
            return "Failed to check in: Invalid battletag format. Battletags should be written like 'Gnome#1337'."

        discord_id = interaction.user.id
        current_season_id = self.config.current_season_id

        json = {"battletag": battletag}
        print(json)
        # TODO Store response in database for linking battletags to discord
        # TODO If captain, give captain role
        try:
            response: CheckinResponse = self.network.request(
                f"checkin/{current_season_id}/{discord_id}",
                "POST",
                json, 
                CheckinResponse
            )
            member = await interaction.guild.fetch_member(response.discord_id)
            if member:
                await self.role_and_name_user(member, response)
            # TODO Valid checkin should not be ephemeral
            await interaction.response.send_message("Du är nu incheckad, välkommen till Dunderligan!", ephemeral=True)
        except HTTPError as e:
            print(f"Error: {interaction.user.global_name} got error code {e.response.status_code} with json {e.response.content} when trying to check in.")
            if e.response.status_code == 409:
                await interaction.response.send_message("FEL: Spelare är redan incheckad. Om det är ett misstag, kontakta admin.", ephemeral=True)
            elif e.response.status_code == 401:
                await interaction.response.send_message("FEL: API-nyckel är ogiltig. Kontakta admin.", ephemeral=True)
            else:
                await interaction.response.send_message("FEL: Kontakta admin.", ephemeral=True)

    async def role_and_name_user(self, member: discord.Member, checkin: CheckinResponse) -> None:
        memberships = (m for m in checkin.player.memberships)

        roles_to_add: list[discord.Role] = []

        for m in memberships:
            team_role = db.get_team_role(m.roster.id)
            if team_role:
                roles_to_add.append(team_role)
            else:
                print(f"Could not find role for team {m.roster.name}")
                
            if m.role in ["coach", "manager"]:
                continue

            if checkin.player.battletag and m.is_captain:
                nick = f"{checkin.player.battletag}"# ({next(m for m in checkin.player.memberships if is_player(m)).roster.name})"
                if len(nick) > 32:
                    nick = f"{nick[:31]}."
                try:
                    await member.edit(nick=nick)
                except discord.Forbidden:
                    print(f"Lacking permissions to rename {member.name}")
        if len(roles_to_add) == 0:
            return
        try: 
            await member.add_roles(roles_to_add)
        except discord.Forbidden:
            print(f"Lacking permissions to add roles to user {member.name}")
            
                

def validate_battletag(battletag: str) -> bool:
    """Returns True if string is on form Name#0000, i.e. a string, #, and number of digits greater than 2 and fewer than 6."""
    try:
        split_tag = battletag.split("#")
        if (
            len(split_tag) != 2
            or len(split_tag[0]) == 0
            or len(split_tag[1]) <= 2
            or len(split_tag[1]) >= 7
        ):
            return False
        int(split_tag[1])
        return True
    except ValueError:
        return False
