from discord import Interaction
from discord.ui import Label, Modal, TextInput


class TextInputModal(Modal, title="Placeholder"):
    def __init__(self, label: str, description: str, placeholder: str):
        super().__init__()
        self.input = Label(
            text=label,
            description=description,
            component=TextInput(placeholder=placeholder, required=True),
        )
        self.add_item(self.input)
        self.value = None

    async def on_submit(self, interaction: Interaction):
        self.value = self.input.component.value
        await interaction.response.send_message("Försöker checka in...", ephemeral=True)
        self.stop()

    async def on_error(self, interaction: Interaction, error: Exception):
        print(error)
        await interaction.response.send_message("Något gick fel. Kontakta admin.")
        return await super().on_error(interaction, error)


async def ask_for_battletag(interaction: Interaction) -> str:
    modal = TextInputModal(
                "Battletag",
                "Mata in din battletag på formatet Spelare#00000",
                "Spelare#00000",
            )
    await interaction.response.send_modal(modal)
    await modal.wait()
    return str(modal.value)
