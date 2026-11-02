from discord.ui import Label, Modal, Select, TextInput

from discord import Interaction, SelectOption


def get_selection_modal(name: str, labels: list[str], values: list[str]) -> Modal:
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
                                label=labels[i],
                                value=values[i],
                            )
                            for i in range(len(values))
                        ],
                        required=True
                ))
                self.add_item(self.selection)
                self.value = None
    
            async def on_submit(self, interaction: Interaction) -> None:
                self.value = self.selection.component.values[0]
                self.stop()
    
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