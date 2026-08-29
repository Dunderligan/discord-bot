import discord
import os
import requests


current_season_id = "da4f6b34-ca5d-40f2-9810-3bf6bd103ae1"
# TODO Figure out how to get current season
api_endpoint = os.getenv("API_ENDPOINT")
api_key = os.getenv("API_KEY")


class CheckinModal(discord.ui.Modal, title="Incheckning"):
    battletag = discord.ui.TextInput(
        label='Battletag',
        placeholder='Skriv din battletag här...'
    )

    async def on_submit(self, interaction: discord.Interaction):
        checkin_response = checkin_player(interaction.user.id, str(self.battletag.value))
        await interaction.response.send_message(checkin_response, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("Oj! Ett fel uppstod. Kontakta Admin om det kvarstår.", ephemeral=True)
        print(f"Error occurred when user {interaction.user.global_name} tried checking in: {error}")


def checkin_player(discord_id: str, battletag: str) -> str:
    """
        Checks in player into website. Returns a string response to be displayed to the user.
    """
    if not validate_battletag(battletag):
        return "Failed to check in: Invalid battletag format. Battletags should be written like 'Gnome#1337'."

    headers = {
        "Authorization":f"Bearer {api_key}" 
    }
    print(headers)
    json = {
        "battletag": battletag
    }
    url = f"{api_endpoint}/checkin/{current_season_id}/{discord_id}"
    checkin_response = requests.post(url=url, json=json, headers=headers)
    print(checkin_response.status_code, checkin_response.text, checkin_response.url)

    if checkin_response.status_code == 401:
        return "Fel: API-nyckel är ogiltig. Kontakta admin."
    if checkin_response.status_code == 409:
        return "Fel: Spelare är redan incheckad. Kontakta admin."
    if checkin_response.status_code == 200:
        return "Du är nu incheckad för nästa säsong av Dunderligan!"
    return "Fel: Kunde inte hitta battletag."


def validate_battletag(battletag: str) -> bool:
    """Returns True if string is on form Name#0000, i.e. a string, #, and number of digits greater than 2 and fewer than 6."""
    try:
        split_tag = battletag.split("#")
        if len(split_tag) != 2 or len(split_tag[0]) == 0 or len(split_tag[1]) <= 2 or len(split_tag[1]) >= 7:
            return False
        int(split_tag[1])
        return True
    except ValueError:
        return False