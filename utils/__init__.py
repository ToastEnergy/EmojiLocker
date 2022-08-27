import discord

async def owner_only(interaction: discord.Interaction):
    return await interaction.client.is_owner(interaction.user)