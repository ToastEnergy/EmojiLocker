import itertools

import config
import discord
from discord.ext import commands
from utils import views


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage="<emoji>")
    @commands.guild_only()
    async def emojiinfo(self, ctx, *, emoji: discord.Emoji):
        """Get info about an emoji"""
        embed = discord.Embed(title=emoji.name)
        embed.color = config.color
        embed.set_thumbnail(url=str(emoji.url))
        embed.description = f"""
**Animated?** : {emoji.animated}
**Roles** : {", ".join([x.mention for x in emoji.roles]) or '@everyone'}
**Guild** : {emoji.guild.name} [{emoji.guild.id}]
**ID** : {emoji.id}
**Available** : {emoji.available}
**Managed by an integration?** : {emoji.managed}
**Created at** : {emoji.created_at.strftime("%m/%d/%Y, %H:%M:%S")}
**Download link** : [Click here]({str(emoji.url)})
        """
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
