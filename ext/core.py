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
import inspect
import config

import discord
from discord import app_commands
from discord.ext import commands
from utils import views
from typing import Optional
from utils.transformers import EmojiTransformer

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lock")
    @app_commands.default_permissions(manage_emojis=True)
    @app_commands.guild_only()
    @app_commands.describe(emoji="The emoji to lock", role="The role to lock the emoji to")
    @app_commands.guilds(discord.Object(id=876848789531549786), discord.Object(id=747524774569443429))
    async def lock(self, interaction: discord.Interaction, emoji: Optional[app_commands.Transform[discord.Emoji, EmojiTransformer]], role: Optional[discord.Role]):
        """Lock an emoji, making it available only to the roles specified and the persistent roles"""
        await interaction.response.defer()
        if not emoji:
            return
            # interactive locking
        if not role:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY)) # type: ignore
        if emoji.guild != interaction.guild:
            return await interaction.followup.send('This emoji appears to be from another server')
        persistent = await self.bot.get_persistent_roles(interaction.guild)

        roles = set([*persistent, role])

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

    @commands.command(usage="<emoji>")
    @commands.max_concurrency(5, commands.BucketType.user)
    async def unlock(self, ctx, emoji: discord.Emoji = None):
        """Unlock an emoji, making it available to everyone"""
        if not emoji:
            return await self.bot.get_command('wizard unlock').__call__(ctx)

        if emoji.guild != ctx.guild:
            return await ctx.reply('This emoji appears to be from another server')

        await emoji.edit(name=emoji.name, roles=[])

        description = f'''
🔒 I have successfully unlocked the '{emoji.name}' emoji.\n
ℹ️ Now everyone will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.reply(
                description + '\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji successfully locked',
                              description=description, color=config.color)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.reply_embed(embed=embed)

    @commands.command()
    @commands.max_concurrency(5, commands.BucketType.user)
    async def unlockall(self, ctx):
        """Unlock every emoji in the server, making them available to everyone"""
        ctx.emojis = [
            emoji for emoji in ctx.guild.emojis if len(emoji.roles) > 0]
        ctx.roles = []
        if len(ctx.emojis) == 0:
            return await ctx.reply('There are no locked emojis.')
        embed = discord.Embed(title='Unlocking all emojis!',
                              description=f'You are about to unlock {len(ctx.emojis)} emojis, continue?',
                              color=discord.Color.red())
        view = views.BaseView(ctx)
        view.confirm_embed = discord.Embed(title='Emojis successfully unlocked', color=config.color,
                                           description=f'''🔓 I have successfully unlocked all of your server emojis.\n
ℹ️ Now everyone will be able to use all emojis in your server''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()

    @commands.group(usage='<role> <role>...', invoke_without_command=True)
    @commands.max_concurrency(5, commands.BucketType.user)
    async def lockall(self, ctx, roles: commands.Greedy[discord.Role] = None):
        """Lock every emoji in the server, making them available to the roles specified"""
        if roles is None:
            return await self.bot.get_command('wizard lockall').__call__(ctx)

        persistent = await self.bot.get_persistent_roles(ctx)
        ctx.roles = set(roles).union(persistent)
        embed = discord.Embed(title='Locking all emojis!', description='''Do you want to **keep** the roles in the existent setup or **overwrite** them?

If you select **keep** an emoji already locked to @role1  will be locked to @role1 + the roles that you specified in the command

if you select **overwrite** it will be locked only to the roles that you just specified.
''', color=config.color)
        view = views.LockallView(ctx)
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()

    @commands.group(usage='[<emoji> <emoji>...] , [<role> <role>...]', invoke_without_command=True)
    @commands.max_concurrency(5, commands.BucketType.user)
    # None because hardcoding :tm:
    async def multiple(self, ctx, *, args=None):
        """Locks multiple emojis to the roles specified, making them available to the that roles"""
        # Not using commands.Greedy because the parsing ambiguities ruins the overall UX
        if not args:
            return await self.bot.get_command('wizard').__call__(ctx)
        args = args.split(",")
        if len(args) == 1:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))

        emojis = args[0].split(' ')
        roles = args[1].split(' ')
        ctx.emojis = set(
            [await commands.EmojiConverter().convert(ctx, emoji.strip()) for emoji in emojis if emoji != ""])
        ctx.roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles if role != ""])
        persistent = await self.bot.get_persistent_roles(ctx)
        ctx.roles = set(ctx.roles).union(persistent)
        view = views.BaseView(ctx)
        view.confirm_embed = discord.Embed(title='Emojis successfully locked', color=config.color,
                                           description=f'''🔓 I have successfully locked {len(ctx.emojis)} emojis\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in ctx.roles])}) will be able to use the emojis''')
        view.confirm_embed.set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        await ctx.reply_embed(
            f'You are about to lock {len(ctx.emojis)} emojis to these roles : {", ".join([r.mention for r in ctx.roles])}\nContinue?',
            view=view)

        await view.wait()

    @commands.command(usage='[<emoji> <emoji>...]')
    @commands.max_concurrency(5, commands.BucketType.user)
    async def massunlock(self, ctx, *, emojis=None):
        """Unlocks the specified emojis, making them available to everyone"""
        if not emojis:
            return await self.bot.get_command('wizard unlock').__call__(ctx)
        emojis = emojis.split(" ")
        ctx.emojis = list(filter(lambda e: (len(e.roles) > 0),
                                 set([await commands.EmojiConverter().convert(ctx, emoji.strip()) for emoji in emojis if
                                      emoji != ""])))
        ctx.roles = []
        view = views.BaseView(ctx)
        view.confirm_embed = discord.Embed(title='Emojis successfully unlocked', color=config.color,
                                          description=f'''🔓 I have successfully unlocked {len(ctx.emojis)} emojis\n
ℹ️ Now everyone will be able to use the emojis''')
        view.confirm_embed.set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        await ctx.reply_embed(f'You are about to unlock {len(ctx.emojis)} emojis\nContinue?',
                              view=view)

        await view.wait()


async def setup(bot):
    await bot.add_cog(Core(bot))
