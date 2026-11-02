from discord import (
    CategoryChannel,
    Forbidden,
    Guild,
    Member,
    PermissionOverwrite,
    Role,
    TextChannel,
    VoiceChannel,
)


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


async def create_text_channel(category: CategoryChannel, name: str, overwrites: dict[Role, PermissionOverwrite]) -> TextChannel:
    """Creates a text channel within the given category."""
    try:
        return await category.create_text_channel(name=name, overwrites=overwrites)
    except Forbidden:
        raise Forbidden("Bot lacking permissions to create text channel")
    except TypeError:
        raise TypeError(f"Recieved overwrites in invalid format: {overwrites}")


async def create_voice_channel(category: CategoryChannel, name: str, overwrites: dict[Role, PermissionOverwrite], user_limit: int = 0) -> VoiceChannel:
    """Creates a voice channel within the given category."""
    try:
        return await category.create_voice_channel(name=name, overwrites=overwrites, user_limit=user_limit)
    except Forbidden:
        raise Forbidden("Bot lacking permissions to create voice channel")
    except TypeError:
        raise TypeError(f"Recieved overwrites in invalid format: {overwrites}")


async def create_category_channel(guild: Guild, name: str, overwrites: dict[Role, PermissionOverwrite]) -> CategoryChannel:
    """Creates a category channel in the given guild."""
    try:
        return await guild.create_category(name=name, overwrites=overwrites)
    except Forbidden:
        raise Forbidden("Bot lacking permissions to create category")
    except TypeError:
        raise TypeError(f"Recieved overwrites in invalid format: {overwrites}")


async def create_role(guild: Guild, name: str) -> Role:
    """Creates a role in the given guild."""
    try:
        return await guild.create_role(name=name, hoist=True, mentionable=True)
    except Forbidden:
        raise Forbidden("Bot lacking permissions to create role")