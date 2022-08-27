import discord
from discord import app_commands
from discord.ext import commands

class EmojiTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str):
        ctx = await commands.Context.from_interaction(interaction)
        return await commands.EmojiConverter().convert(ctx, value)