import discord

async def empty_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    await interaction.response.defer()
    i = 0
    for c in category.channels:
        await c.delete()
        i += 1
    await category.delete()
    await interaction.followup.send(f"Finished removing {i} channels.")

#commands to remove old text channels belonging to teams

async def clear_text_channels(interaction: discord.Interaction, this_category: discord.CategoryChannel, excempt_channel: discord.TextChannel):
    await interaction.response.defer()
    if this_category != None:
        for c in this_category.text_channels:
            if c != excempt_channel:
                await c.delete()
    await interaction.followup.send(f"Finished clearing channels.")

async def clear_categoryless(interaction: discord.Interaction):
    await interaction.response.defer()
    i = 0
    for c in interaction.guild.voice_channels:
        if c.category == None:
            await c.delete()
            i += 1
    await interaction.followup.send(f"Finished removing {i} channels.")

#debug command to check order roles are being checked in
async def print_roles(interaction: discord.Interaction):
    message = ""
    for r in interaction.guild.roles:
        message += r.name + "\n"
    await interaction.response.send_message(message)