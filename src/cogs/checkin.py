import discord
from discord import app_commands
from discord.ext import commands
from requests import HTTPError

from configuration import Suite
from dunderligan_api import CheckinResponse
from modal import get_input_modal


class CheckinCog(commands.Cog):
    def __init__(self, suite: Suite):
        self.config = suite.config
        self.api = suite.api
        self.db = suite.db

    @app_commands.command(name="checkin", description="Check in as a player to the next season.")
    async def checkin(self, interaction: discord.Interaction):
        """Command to be used by players to check in before each season, confirming they are in the discord server and linking their battletag and discord-ids."""
        print(f"Recieved checkin command from {interaction.user}")
        await interaction.response.send_modal(get_input_modal("Battletag", self.checkin_player))

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

        # TODO Store response in database for linking battletags to discord
        try:
            response: CheckinResponse = self.api.checkin_player(current_season_id, discord_id, battletag)
            member = await interaction.guild.fetch_member(response.discord_id)
            if member:
                await self.role_and_name_user(interaction.guild, member, response)
            await interaction.response.send_message("Du är nu incheckad, välkommen till Dunderligan!", ephemeral=True)
        except HTTPError as e:
            print(f"Error: {interaction.user.global_name} got error code {e.response.status_code} with json {e.response.content} when trying to check in.")
            if e.response.status_code == 409:
                await interaction.response.send_message("FEL: Spelare är redan incheckad. Om det är ett misstag, kontakta admin.", ephemeral=True)
            elif e.response.status_code == 401:
                await interaction.response.send_message("FEL: API-nyckel är ogiltig. Kontakta admin.", ephemeral=True)
            elif e.response.status_code == 404:
                await interaction.response.send_message("FEL: Battletag hittades inte. Dubbel-kolla att du skrev den fulla battletagen.", ephemeral=True)
            else:
                await interaction.response.send_message("FEL: Kontakta admin.", ephemeral=True)

    async def role_and_name_user(self, guild: discord.Guild, member: discord.Member, checkin: CheckinResponse) -> None:
        memberships = (m for m in checkin.player.memberships)

        roles_to_add: list[discord.Role] = []

        for m in memberships:
            team_role_id = self.db.get_team_role_id(m.roster.id)
            if team_role_id:
                team_role = discord.utils.get(guild.roles, id=team_role_id)
                if team_role:
                    roles_to_add.append(team_role)
                else:
                    print(f"Could not find role for team {m.roster.name}")
            else:
                print(f"Database doesn't contain role for team {m.roster.name}")
                
            if m.role in ["coach", "manager"]:
                continue

            if checkin.player.battletag and m.is_captain:
                captain_role: discord.Role = discord.utils.get(
                    guild.roles, id=int(self.config.captain_role_id)
                )
                if captain_role and captain_role not in roles_to_add:
                    roles_to_add.append(captain_role)
                else:
                    if captain_role in roles_to_add:
                        print("Captain role already added to list.")
                    else:    
                        print("Couldn't find captain role.")

                nick = f"{checkin.player.battletag}"
                if len(nick) > 32:
                    nick = f"{nick[:31]}."
                try:
                    await member.edit(nick=nick)
                except discord.Forbidden:
                    print(f"Lacking permissions to rename {member.name}")
        if len(roles_to_add) == 0:
            return
        try: 
            await member.add_roles(*roles_to_add)
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
