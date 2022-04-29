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
import itertools

import config
import discord
from discord.ext import commands
from utils import views


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if len(ctx.guild.emojis) == 0:
            raise commands.BadArgument('There are no emojis in this server!')

        return True

    @commands.command(usage='<emoji>')
    @commands.guild_only()
    async def emojiinfo(self, ctx, *, emoji: discord.Emoji):
        """Get info about an emoji"""
        embed = discord.Embed(title=emoji.name)
        embed.color = config.color
        embed.set_thumbnail(url=str(emoji.url))
        embed.description = f'''
**Animated?** : {emoji.animated}
**Roles** : {", ".join([x.mention for x in emoji.roles]) or '@everyone'}
**Guild** : {emoji.guild.name} [{emoji.guild.id}]
**ID** : {emoji.id}
**Available** : {emoji.available}
**Managed by an integration?** : {emoji.managed}
**Created at** : {emoji.created_at.strftime("%m/%d/%Y, %H:%M:%S")}
**Download link** : [Click here]({str(emoji.url)})
        '''
        await ctx.reply_embed(embed=embed)

    @commands.command(aliases=["packs"])
    @commands.max_concurrency(3, commands.BucketType.user)
    async def emojis(self, ctx):
        """List all the server emojis grouped by roles"""
        ctx.packs = []
        ctx.keys = []
        def func(x): return x.roles
        for k, g in itertools.groupby(sorted(ctx.guild.emojis, key=func), func):
            ctx.packs.append(list(g))
            ctx.keys.append(k)

        ctx.embed = discord.Embed(
            title='Packs', color=config.color)
        ctx.paginator = commands.Paginator(prefix='', suffix='', linesep='')
        c = 0
        for x in ctx.packs:
            ctx.paginator.add_line('\n\n')
            ctx.paginator.add_line(
                f"> **{(', '.join([role.name for role in ctx.keys[c]])) or '@everyone'}**")
            c += 1
            ctx.paginator.add_line('\n')
            for em in x:
                ctx.paginator.add_line(f"{em} ")
        ctx.embed.description = ctx.paginator.pages[0]
        ctx.embed.set_footer(text=f'Page 1/{len(ctx.paginator.pages)}')
        view = views.PacksView(ctx)
        if len(ctx.paginator.pages) > 1:
            ctx.sent_message = await ctx.reply_embed(embed=ctx.embed, view=view)
            return await view.wait()
        else:
            ctx.sent_message = await ctx.reply_embed(embed=ctx.embed)


def setup(bot):
    bot.add_cog(Misc(bot))
