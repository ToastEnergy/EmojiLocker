import discord
from discord import app_commands
from discord.ext import commands


async def emoji_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    return [app_commands.Choice(name=emoji.name, value=str(emoji.id)) for emoji in interaction.guild.emojis if emoji.name.startswith(current)][:25]

async def locked_emoji_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    return [app_commands.Choice(name=emoji.name, value=str(emoji.id)) for emoji in interaction.guild.emojis if emoji.name.startswith(current) if len(emoji.roles)>0][:25]


async def roles_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    ctx = await commands.Context.from_interaction(interaction)
    current_roles = []
    for role_str in current.split(","):
        role_str_clean = role_str.strip()
        if role_str_clean:
            try:
                resolved_role = await commands.RoleConverter().convert(ctx, role_str_clean)
                current_roles.append(resolved_role)
            except: continue
    current_roles_names = [x.name for x in current_roles]
    roles = interaction.guild.roles
    res = []
    for role in roles:
        if role in current_roles:
            continue
        choice_str = ", ".join([*current_roles_names, role.name])
        res.append(app_commands.Choice(name=choice_str, value=choice_str))
    return res[:25]

async def emojis_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    ctx = await commands.Context.from_interaction(interaction)
    current_emojis = []
    for emoji_str in current.split(","):
        emoji_str_clean = emoji_str.strip()
        if emoji_str_clean:
            try:
                resolved_emoji = await commands.EmojiConverter().convert(ctx, emoji_str_clean)
                current_emojis.append(resolved_emoji)
            except: continue
    current_emojis_names = [x.name for x in current_emojis]
    emojis = interaction.guild.emojis
    res = []
    for emoji in emojis:
        if emoji in current_emojis:
            continue
        choice_str = ", ".join([*current_emojis_names, emoji.name])
        res.append(app_commands.Choice(name=choice_str, value=choice_str))
    return res[:25]