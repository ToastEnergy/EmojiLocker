"""
MIT License

Copyright (c) 2022 chickenmatty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import config
import discord
from discord import app_commands
from discord.ext import commands
from utils.views import ConfirmView
from utils.transformers import EmojiTransformer, RolesTransformer, EmojisTransformer
from utils.autocompletes import emoji_autocomplete, locked_emoji_autocomplete, roles_autocomplete, emojis_autocomplete

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lock")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.guild_only()
    @app_commands.autocomplete(emoji=emoji_autocomplete)
    @app_commands.describe(emoji="The emoji to lock", role="The role to lock the emoji to", ignore_persistent="Whether to ignore or not the persistent roles")
    async def lock(self, interaction: discord.Interaction, emoji: app_commands.Transform[discord.Emoji, EmojiTransformer], role: discord.Role, ignore_persistent: bool=False):
        """Lock an emoji, making it available only to the roles specified and the persistent roles"""
        await interaction.response.defer()
        if emoji.guild != interaction.guild:
            return await interaction.followup.send('This emoji appears to be from another server')
        if emoji.managed:
            return await interaction.followup.send('This emoji is managed by an integration')
        if not ignore_persistent:
            persistent = await self.bot.get_persistent_roles(interaction.guild)

            roles = set([*persistent, role])
        else:
            roles = [role]
        await emoji.edit(name=emoji.name, roles=roles)

        description = f'''
🔒 I have successfully locked the '{emoji.name}' emoji.\n
ℹ️ Now only the people with at least one of the roles that you specified ({', '.join([r.mention for r in roles])}) will be able to use the emoji'''

        embed = discord.Embed(title='Emoji successfully locked',
                              description=description, color=config.color)
        embed.set_footer(
            text='If you can\'t use the emoji but you have at least one of these roles try to fully restart your Discord app')
        embed.set_thumbnail(url=emoji.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unlock")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.guild_only()
    @app_commands.autocomplete(emoji=locked_emoji_autocomplete)
    @app_commands.describe(emoji="The emoji to unlock")
    async def unlock(self, interaction: discord.Interaction, emoji: app_commands.Transform[discord.Emoji, EmojiTransformer]):
        """Unlock an emoji, making it available to everyone"""
        if emoji.guild != interaction.guild:
            return await interaction.response.send_message('This emoji appears to be from another server')
        if emoji.managed:
            return await interaction.response.send_message('This emoji is managed by an integration')

        await emoji.edit(name=emoji.name, roles=[])

        description = f'''
🔒 I have successfully unlocked the '{emoji.name}' emoji.\n
ℹ️ Now everyone will be able to use the emoji'''

        embed = discord.Embed(title='Emoji successfully unlocked',
                              description=description, color=config.color)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlockall")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.guild_only()
    async def unlockall(self, interaction: discord.Interaction):
        """Unlock every emoji in the server, making them available to everyone"""
        emojis = [
            emoji for emoji in interaction.guild.emojis if len(emoji.roles) > 0] # type: ignore
        if len(emojis) == 0:
            return await interaction.response.send_message('There are no locked emojis.')
        embed = discord.Embed(title='Unlocking all emojis!',
                              description=f'You are about to unlock {len(emojis)} emojis, continue?',
                              color=discord.Color.red())
        confirm_embed = discord.Embed(title='Emojis successfully unlocked', color=config.color,
                                           description=f'''🔓 I have successfully unlocked all of your server emojis.\n
ℹ️ Now everyone will be able to use all emojis in your server''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        if not view.result:
            return await interaction.edit_original_response(content="Cancelled.", embed=None, view=None)
        for i, emoji in enumerate(emojis):
            if emoji.managed:
                continue
            await interaction.edit_original_response(content=f"{i}/{len(emojis)}", embed=None, view=None)
            await emoji.edit(name=emoji.name, roles=[])
        await interaction.edit_original_response(content=None, embed=confirm_embed)

    @app_commands.command(name="lockall")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.autocomplete(roles=roles_autocomplete)
    @app_commands.describe(roles="Comma separated list of roles to lock all of your emojis to",
                           keep="Lock the emojis to the roles that they are already locked to + the new roles",
                           ignore_persistent="Whether to ignore or not the persistent roles")
    @app_commands.guild_only()
    async def lockall(self, interaction: discord.Interaction, roles: app_commands.Transform[set[discord.Role], RolesTransformer], keep: bool=False, ignore_persistent: bool=False):
        """Lock every emoji in the server, making them available to the roles specified"""

        if not ignore_persistent:
            persistent = await self.bot.get_persistent_roles(interaction.guild)
            roles = roles.union(persistent)
        await interaction.response.send_message("Working...")
        assert interaction.guild

        for i, emoji in enumerate(interaction.guild.emojis, 1):
            if emoji.managed:
                continue
            emoji_roles = roles.union(emoji.roles) if keep else roles
            try:
                await emoji.edit(roles=emoji_roles)
                await interaction.edit_original_response(content=f"{i}/{len(interaction.guild.emojis)}")
            except:
                pass

        description = f'''
🔒 I have successfully locked all your server emojis\n
ℹ️ Now only the roles you specified will be able to use the emojis.'''

        embed = discord.Embed(title='Emojis successfully locked',
                              description=description, color=config.color)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        await interaction.edit_original_response(content=None, embed=embed)
    
    @app_commands.command(name="multiplelock")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.autocomplete(roles=roles_autocomplete, emojis=emojis_autocomplete)
    @app_commands.guild_only()
    @app_commands.describe(
                           emojis="Comma separated list of emojis to lock to the roles",
                           roles="Comma separated list of roles to lock the emojis to",
                           keep="Lock the emojis to the roles that they are already locked to + the new roles",
                           ignore_persistent="Whether to ignore or not the persistent roles")
    async def multiple(self, interaction: discord.Interaction, emojis: app_commands.Transform[set[discord.Emoji], EmojisTransformer],
    roles: app_commands.Transform[set[discord.Role], RolesTransformer],
    keep: bool=False, ignore_persistent: bool=False
    ):
        """Lock multiple emojis to multiple roles"""
        if not ignore_persistent:
            persistent = await self.bot.get_persistent_roles(interaction.guild)
            roles = roles.union(persistent)
        await interaction.response.send_message("Working...")
        assert interaction.guild

        for i, emoji in enumerate(emojis, 1):
            if emoji.managed:
                continue
            emoji_roles = roles.union(emoji.roles) if keep else roles
            try:
                await emoji.edit(roles=emoji_roles)
                await interaction.edit_original_response(content=f"{i}/{len(emojis)}")
            except:
                pass

        description = f'''
🔒 I have successfully locked your emojis\n
ℹ️ Now only the roles you specified will be able to use the emojis.'''

        embed = discord.Embed(title='Emojis successfully locked',
                              description=description, color=config.color)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        await interaction.edit_original_response(content=None, embed=embed)

        

async def setup(bot):
    await bot.add_cog(Core(bot))
