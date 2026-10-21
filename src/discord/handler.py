import editor
import interface
import responder
import surveyor

from discord import Interaction, Member


async def checkin_user(interaction: Interaction) -> None:
    battletag: str = await surveyor.ask_for_battletag(interaction)
    interface.checkin_player(interaction.user.id, battletag)
    role = interface.get_checked_in_member(interaction.user.id)
    await editor.give_member_roles([role])