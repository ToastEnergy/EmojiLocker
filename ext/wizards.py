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
import discord
import config

from discord.ext import commands
from utils import views


class Wizards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if len(ctx.guild.emojis) == 0:
            raise commands.BadArgument('There are no emojis in this server!')
        if ctx.command.name in ['packs', 'emojiinfo']:
            return True
        if not ctx.me.guild_permissions.manage_emojis:
            raise commands.BotMissingPermissions(['Manage Emojis'])
        if not ctx.author.guild_permissions.manage_emojis:
            raise commands.MissingPermissions(['Manage Emojis'])
        return True

    @commands.group(invoke_without_command=True, aliases=['select'])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def wizard(self, ctx):
        """Guided procedure to lock an emoji(s) to a role(s)"""
        ctx.embed = discord.Embed(title="Guided locking",
                                  description='Select the emojis you want to lock with the menu below, then click continue',
                                  color=config.color)
        ctx.persistent = set(await self.bot.get_persistent_roles(ctx))
        ctx.roles = set()
        ctx.emojis = set()
        view = views.MultipleSelectView(ctx)
        await ctx.reply_embed(embed=ctx.embed, view=view)
        await view.wait()

    @wizard.command(name='unlock')
    @commands.max_concurrency(1, commands.BucketType.user)
    async def unlock_wizard(self, ctx):
        """Guided procedure to unlock emojis"""
        ctx.roles = []
        ctx.emojis = set()
        ctx.locked = [
            emoji for emoji in ctx.guild.emojis if len(emoji.roles) > 0]
        if len(ctx.locked) == 0:
            raise (commands.BadArgument('There are no locked emojis!'))
        embed = discord.Embed(title='Unlocking emojis!',
                              description='Select the emojis you want to unlock with the menu below, then click '
                                          'continue', color=config.color)
        view = views.MassUnlockSelectView(ctx)
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()

    @wizard.command(name='lockall')
    @commands.max_concurrency(1, commands.BucketType.user)
    async def lockall_wizard(self, ctx):
        """Guided procedure to lock every emoji in the server"""
        embed = discord.Embed(title="Locking all emojis!",
                              description='''You are locking every emoji of the server to some roles, select them with the menu below, then click Keep or Overwrite
If you select **keep** an emoji already locked to @role1 will be locked to @role1 + the roles that you specified in the command

if you select **overwrite** it will be locked only to the roles that you just specified.
''', color=config.color)
        ctx.persistent = set(await self.bot.get_persistent_roles(ctx))
        ctx.roles = set()
        view = views.LockAllSelectView(ctx)
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()


async def setup(bot):
    await bot.add_cog(Wizards(bot))
