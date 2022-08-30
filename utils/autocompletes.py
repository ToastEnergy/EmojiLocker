import discord
from discord import app_commands


async def emoji_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    return [app_commands.Choice(name=emoji.name, value=str(emoji.id)) for emoji in interaction.guild.emojis if emoji.name.startswith(current)][:25]
