import editor
import interface
import responder
import surveyor

from discord import Interaction, Member, Role
from models import Player


async def checkin_user(interaction: Interaction) -> None:
    battletag: str = await surveyor.ask_for_battletag(interaction)

    player: Player = interface.checkin_player(interaction.user.id, battletag)
    roles: list[Role] = interface.get_player_roles(player)
    
    if roles is not None and len(roles) > 0:
        await editor.give_member_roles(roles)