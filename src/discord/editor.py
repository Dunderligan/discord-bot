from discord import Forbidden, Member, Role


async def give_member_roles(member: Member, roles: list[Role]) -> None:
    """Gives member roles in list, assuming bot has sufficient permissions."""
    try:
        await member.add_roles(*roles)
    except Forbidden:
        raise Forbidden(f"Bot lacking permissions to give user {member.name} roles.")


async def rename_member(member: Member, nickname: str | None = None) -> None:
    """Renames member to given nickname, assuming bot has sufficient permissions.
    If nickname is None, then the nickname will be cleared."""
    if nickname is not None:
        # trims nickname so it doesn't exceed 32 character limit
        nickname = nickname[:31]
    try:
        await member.edit(nick=nickname)
    except Forbidden:
        raise Forbidden(f"Bot lacking permissions to rename user {member.name}")
