import discord
from discord import ui
from ..network import get

# Spara databas med discordkonto id, battletag, om de är kapten, om de är incheckade, id för laget
# om ej i databas, api request till dunderligan.se för att försöka hitta spelare
# kanske bättre att spara databas med alla spelare som är anmälda, med admin kommando för att uppdatera databas med nya spelare
# om hittad, koppla discordkonto id till spelare, spara i databas, markera som incheckad

class Checkin(ui.Modal, title="Incheckning"):
    """Modal for checking in a player to the current season of Dunderligan."""

    battletag = ui.TextInput(
        label = "Battletag",
        placeholder = "Namn#1234",
        required = True
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handles the submission of the modal."""
        battletag = self.battletag.value
        if not is_battletag_valid(battletag):
            await interaction.response.send_message(
                "Ogiltig battletag. Var god ange den på formatet Namn#1234",
                ephemeral=True,
            )
            return

        discordID = interaction.user.id
        url = f"checkin/seasonID/{discordID}"

        if not is_battletag_registered(battletag):
            await interaction.response.send_message(
                "Battletagen är inte anmäld till den aktuella säsongen.", ephemeral=True
            )
            return

        if is_battletag_already_checked_in(battletag):
            if is_battletag_linked_to_user(battletag, interaction.user):
                await interaction.response.send_message(
                    "Du är redan incheckad med detta konto.", ephemeral=True
                )
                # Add roles if not already assigned
                return
            await interaction.response.send_message(
                "Ett annat Discord-konto är redan länkat till denna battletag.",
                ephemeral=True,
            )
            return

        # Check in the player, assign roles, and change nickname if captain
        await interaction.response.send_message(
            f"Du är nu incheckad: {battletag}", ephemeral=True
        )


def is_battletag_valid(battletag: str) -> bool:
    """Validates the format of the battletag, requiring it to be in the format 'X#Y', where the length of both parts is greater than 0."""
    return (
        "#" in battletag
        and len(battletag.split("#")[0]) > 0
        and len(battletag.split("#")[1]) > 0
    )


def is_battletag_registered(battletag: str) -> bool:
    """Validates that the battletag exists for the season, and is not already checked in."""
    # Implement your player validation logic here
    return True  # Placeholder for actual validation logic


def is_battletag_already_checked_in(battletag: str) -> bool:
    """Validates that the player has not already checked in."""
    # Implement your logic to check if the player has already checked in
    return False  # Placeholder for actual validation logic


def is_battletag_linked_to_user(battletag: str, user: discord.User) -> bool:
    """Assuming the player is already checked in, validates that they are using the already linked account."""
    # Implement your logic to check if the player is using the correct account
    return True  # Placeholder for actual validation logic
