import discord
from discord.ext import commands

async def owner_only(interaction: discord.Interaction):
    return await interaction.client.is_owner(interaction.user)

async def guild_with_emoji_only(interaction: discord.Interaction):
    if len(interaction.guild.emojis) == 0:
        raise commands.BadArgument('There are no emojis in this server!')
    return True