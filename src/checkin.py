import datetime
import os

import discord
import requests

import db

current_season_id = "da4f6b34-ca5d-40f2-9810-3bf6bd103ae1"
# TODO Figure out how to get current season
api_endpoint = os.getenv("API_ENDPOINT")
api_key = os.getenv("API_KEY")


class CheckinModal(discord.ui.Modal, title="Incheckning"):
    battletag = discord.ui.TextInput(
        label="Battletag", placeholder="Skriv din battletag här..."
    )

    async def on_submit(self, interaction: discord.Interaction):
        checkin_response = await checkin_player(
            interaction, str(self.battletag.value)
        )
        await interaction.response.send_message(checkin_response, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "Oj! Ett fel uppstod. Kontakta Admin om det kvarstår.", ephemeral=True
        )
        print(
            f"Error occurred when user {interaction.user.global_name} tried checking in: {error}"
        )


class Roster:
    id: str
    name: str
    slug: str

    def __init__(self, id: str, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug

    def from_json(json: dict):
        return Roster(json.get("id"), json.get("name"), json.get("slug"))


class Membership:
    rank: str
    tier: int
    sr: int
    is_captain: bool
    registered_name: str
    roster: Roster
    role: str

    def __init__(
        self,
        rank: str,
        tier: int,
        sr: int,
        is_captain: bool,
        registered_name: str,
        roster: Roster,
        role: str,
    ):
        self.rank = rank
        self.tier = tier
        self.sr = sr
        self.is_captain = is_captain
        self.registered_name = registered_name
        self.roster = roster
        self.role = role

    def from_json(json: dict):
        return Membership(
            json.get("rank"),
            json.get("tier"),
            json.get("sr"),
            json.get("isCaptain"),
            json.get("registeredName"),
            Roster.from_json(json.get("roster")),
            json.get("role"),
        )


class Player:
    id: str
    battletag: str
    memberships: list[Membership]

    def __init__(self, id: str, battletag: str, memberships: list[Membership]):
        self.id = id
        self.battletag = battletag
        self.memberships = memberships

    def from_json(json: dict):
        return Player(
            json.get("id"),
            json.get("battletag"),
            [Membership.from_json(m) for m in json.get("memberships")],
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


async def checkin_player(
    interaction: discord.Interaction, battletag: str
) -> str:
    """
    Checks in player into website. Returns a string response to be displayed to the user.
    """
    if not validate_battletag(battletag):
        return "Failed to check in: Invalid battletag format. Battletags should be written like 'Gnome#1337'."

    discord_id = interaction.user.id
    headers = {"Authorization": f"Bearer {api_key}"}
    json = {"battletag": battletag}
    url = f"{api_endpoint}/checkin/{current_season_id}/{discord_id}"
    # TODO Store response in database for linking battletags to discord
    # TODO If captain, give captain role
    checkin_response = requests.post(url=url, json=json, headers=headers)

    if checkin_response.status_code == 401:
        return "Fel: API-nyckel är ogiltig. Kontakta admin."
    if checkin_response.status_code == 409:
        return "Fel: Spelare är redan incheckad. Kontakta admin."
    if checkin_response.status_code == 200:
        checkin: CheckinResponse = CheckinResponse.from_json(checkin_response.json())
        member = await interaction.guild.fetch_member(checkin.discord_id)
        if member:
            await role_and_name_user(member, checkin)
        # TODO Valid checkin should not be ephemeral
        return "Du är nu incheckad för nästa säsong av Dunderligan!"
    return "Fel: Kunde inte hitta battletag."


async def role_and_name_user(member: discord.Member, checkin: CheckinResponse) -> None:
    memberships = (m for m in checkin.player.memberships)

    for m in memberships:
        team_role = db.get_team_role(m.roster.id)
        if team_role:
            try:
                await member.add_roles(team_role)
            except discord.Forbidden:
                print(f"Lacking permissions to add role {team_role.name} to {member.name}")
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
