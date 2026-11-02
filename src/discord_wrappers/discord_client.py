from discord import CategoryChannel, Guild, Interaction, Role

from backend.backend_client import Backend
from backend.network import RejectedRequest
from config import Config
from discord_wrappers import edit_guild, send_modal
from models import Division, Player, Season

current_season_id = "da4f6b34-ca5d-40f2-9810-3bf6bd103ae1"

class DiscordHandler:
    def __init__(self, config: Config, backend: Backend):
        self.backend = backend

    async def checkin_user(self, interaction: Interaction) -> None:
        battletag: str = await send_modal.ask_for_battletag(interaction)
        
        try:
            player: Player = self.backend.checkin_player(current_season_id, interaction.user.id, battletag)
        except RejectedRequest as e:
            if e.error_code == 409:
                await interaction.followup.send("FEL: Spelare är redan incheckad. Om det är ett misstag, kontakta admin.", ephemeral=True)
            elif e.error_code == 401:
                await interaction.followup.send("FEL: API-nyckel är ogiltig. Kontakta admin.", ephemeral=True)
            elif e.error_code == 404:
                await interaction.followup.send("FEL: Battletag hittades inte. Dubbelkolla att du skrev full battletag.", ephemeral=True)
            else:
                await interaction.followup.send("FEL: Kontakta admin.", ephemeral=True)
            return
        
        role_ids: list[int] = self.backend.get_player_role_ids(player)
        if role_ids is not None and len(role_ids) > 0:
            roles: list[Role] = list(filter(lambda r: r.id in role_ids, interaction.guild.roles))
            if len(roles) > 0:
                await edit_guild.give_member_roles(roles)
            else:
                print("No roles found!")
                await interaction.followup.send(content="Failed to find roles.", ephemeral=True)
                return
        else:
            print("No role ids found!")
            await interaction.followup.send(content="Failed to find roles.", ephemeral=True)
            return

        await interaction.followup.send(content="Completed checkin.", ephemeral=True)

    async def setup(self, interaction: Interaction) -> None:
        try:
            await interaction.response.send_message("Creating channels...", ephemeral=True)
            season: Season = self.backend.get_season(current_season_id)
            await _create_category(interaction.guild, season, season.divisions[0])
            await interaction.followup.send("Successfully created channels.", ephemeral=True)
        except Exception as e:
            print(e)

    def get_tasks(self):
        return []


async def _create_category(guild: Guild, season: Season, division: Division):
    div_short_name = (
        "div" + division.slug
        if division.slug.isdigit()
        else "ds"
        if division.slug == "dunderserien"
        else "???"
    )
    suffix = f"{div_short_name}-s{season.slug[-1]}"

    category: CategoryChannel = await edit_guild.create_category_channel(guild, f"{season.name} - {division.name}", {})

    channels = [
        "spelschema",
        "tabell",
        "information",
        "spelartrupper",
        "rapportera-bans",
    ]

    for c in channels:
        await edit_guild.create_text_channel(category, f"{c}-{suffix}", {})