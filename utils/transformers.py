import discord
from discord import app_commands
from discord.ext import commands

class EmojiTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str):
        ctx = await commands.Context.from_interaction(interaction)
        return await commands.EmojiConverter().convert(ctx, value)

class RoleTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str):
        ctx = await commands.Context.from_interaction(interaction)
        return await commands.RoleConverter().convert(ctx, value)

class EmojisTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value:str):
        ctx = await commands.Context.from_interaction(interaction)
        emojis_str = value.split(",")
        res = set()
        for emoji in emojis_str:
            try:
                res.add(await commands.EmojiConverter().convert(ctx, emoji.strip()))
            except commands.BadArgument:
                pass
        return res

class RolesTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value:str):
        ctx = await commands.Context.from_interaction(interaction)
        roles_str = value.split(",")
        res = set()
        for emoji in roles_str:
            try:
                res.add(await commands.RoleConverter().convert(ctx, emoji.strip()))
            except commands.BadArgument:
                pass
        return res