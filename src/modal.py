from discord import Interaction, SelectOption
from discord.ui import Label, Modal, Select, TextInput


def get_selection_modal(name: str, choices: list[str], callback) -> Modal:
    class SimpleModal(Modal, title=f"Välj {name}"):
            def __init__(self):
                super().__init__()
                self.selection: Label = Label(
                    text=name,
                    description=f"Välj en {name}:",
                    component=Select(
                        placeholder=f"{name}",
                        options=[
                            SelectOption(
                                label=c.title(),
                                value=c,
                            )
                            for c in choices
                        ],
                        required=True
                ))
                self.add_item(self.selection)
    
            async def on_submit(self, interaction: Interaction) -> None:
                await callback(interaction, self.selection.component.values[0])
    
            async def on_error(self, interaction: Interaction, error: Exception) -> None:
                print(error)
    
    return SimpleModal()
    

def get_input_modal(name: str, callback) -> Modal:
    class SimpleModal(Modal, title=f"Mata in {name}"):
            def __init__(self):
                super().__init__()
                self.input = Label(
                    text=name,
                    description=f"Mata in {name}:",
                    component=TextInput(
                        placeholder=f"{name}",
                        required=True
                ))
                self.add_item(self.input)
    
            async def on_submit(self, interaction: Interaction) -> None:
                await callback(interaction, self.input.component.value)
    
            async def on_error(self, interaction: Interaction, error: Exception) -> None:
                print(error)
    
    return SimpleModal()