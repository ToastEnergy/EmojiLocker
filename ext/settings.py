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

import asyncpg
import config
import discord
from discord.ext import commands
from discord import app_commands

@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_messages=True)
class Settings(commands.GroupCog, name="persistent-roles"):
    def __init__(self, bot):
        self.bot = bot

    def update_cache_key(self, guild, key, value):
        cache = self.bot.guilds_cache

        if not cache.get(guild):
            cache[guild] = {key: value}
        cache[guild].update({key: value})

    @app_commands.command(name="view")
    async def view_persistent_roles(self, interaction: discord.Interaction) -> None:
        """View the server settings"""
        assert interaction.guild
        data = (await self.bot.db.get_guild(interaction.guild.id)) or {}
        if not data:
            roles = 'No roles'
        else:
            roles = ', '.join(
                map(lambda r: f'<@&{r}>', data.get('roles'))) or 'No roles'  # type: ignore
        embed = discord.Embed(title='Emoji Locker\'s settings',
                              color=config.color,
                              description=f'''**Available settings**
- `roles` (the default roles that will be always included when you lock an emoji, useful for allowing emoji access to server admins)

**Current settings**
- Persistent roles : {roles}

''')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roles")
    async def roles(self, interaction: discord.Interaction):
        """Change the server's persistent roles. Persistent roles are roles applied in every emoji lock operation
        Useful to keep roles like admin always able to use emojis"""
        
        assert interaction.guild

        data = await self.bot.get_persistent_roles(interaction.guild)
        if not data:
            roles = 'There are no persistent roles for this server'
        else:
            roles = f'The persistent roles for this server are {", ".join(map(lambda r: r.mention, data))}'
        embed = discord.Embed(
            title=f'{interaction.guild.name}\'s persistent roles')
        embed.description = roles
    
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add")
    async def add(self, interaction: discord.Interaction, role: discord.Role):
        "Add a persistent role to the server"
        assert interaction.guild

        try:
            await self.bot.db.add_roles(interaction.guild.id, [role.id])
        except asyncpg.exceptions.UniqueViolationError:
            await interaction.response.send_message('One of the roles was already added.', ephemeral=True)
        await interaction.response.send_message(f'{role.mention} is now a persistent role for this server', allowed_mentions=discord.AllowedMentions().none())

    @app_commands.command(name="remove")
    async def remove(self, interaction: discord.Interaction, role: discord.Role):
        "Remove a persistent role from the server"
        assert interaction.guild

        await self.bot.db.delete_roles([role.id])
        await interaction.response.send_message(f"{role.mention} won't be a persistent role anymore", allowed_mentions=discord.AllowedMentions().none())

    @app_commands.command(name="sync")
    async def sync(self, interaction: discord.Interaction):
        """Lock emojis to newly added persistent roles"""
        assert interaction.guild
        roles = await self.bot.get_persistent_roles(interaction.guild)
        emojis = [emoji for emoji in interaction.guild.emojis if not set(roles).issubset(emoji.roles)]
        if not emojis:
            return await interaction.response.send_message('Nothing to sync.')
        await interaction.response.send_message(f'Updating {len(emojis)} emojis...')
        for i, emoji in enumerate(emojis):
            await emoji.edit(roles=set(emoji.roles).union(roles))
            try:
                await interaction.edit_original_response(content=f'{i}/{len(emojis)}')
            except:
                pass
        await interaction.edit_original_response(content=f'Updated {len(emojis)} emojis.')


async def setup(bot):
    await bot.add_cog(Settings(bot), guilds=[discord.Object(id=876848789531549786), discord.Object(id=747524774569443429)])
